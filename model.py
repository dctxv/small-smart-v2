"""Small decoder-only transformer.

Design choices that matter for the seed work:
- The only learned tensors are the token embedding table (tied with the output
  head) and six bias-free weight matrices per layer (q, k, v, o, fc, proj).
  Norms are parameter-free RMS norms and positions use rotary embeddings, so
  a seed that generates the weight matrices generates the whole network apart
  from the embedding table.
"""
import math
from dataclasses import dataclass, asdict

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class GPTConfig:
    vocab_size: int = 8192
    n_layer: int = 12
    n_head: int = 8
    d_model: int = 512
    ctx: int = 512
    mlp_mult: int = 4
    qk_norm: bool = False       # normalise queries and keys before attention
    relu2: bool = False         # squared ReLU instead of GELU in the MLP
    value_resid: bool = False   # mix the first layer's attention values into every later layer
    hash_rows: int = 0          # word-pair hash embedding: rows in a table indexed by hash(previous token, token)
    val_emb: int = 0            # value embeddings: 2 = one token table added to attention values in each half
    mtp: float = 0.0            # multi-token prediction: weight of an extra loss on the token after next
    ngpt: bool = False          # approximately normalised: the stream is re-normalised after every update
    qbits: int = 0              # quantisation-aware training: weights are rounded to this many bits (0 = off)

    def to_dict(self):
        return asdict(self)


MATRIX_NAMES = ("q", "k", "v", "o", "fc", "proj")


def fake_quant(w, bits):
    """Round each row of w to a signed grid with 2^bits - 1 levels. Gradients pass straight through."""
    if not bits:
        return w
    levels = 2 ** (bits - 1) - 1
    w32 = w.float()
    if bits >= 8:
        top = w32.abs().amax(dim=1, keepdim=True)
    else:  # few levels: clip the tails so the grid is spent where most weights are
        top = (2.5 if bits >= 4 else 1.5) * w32.pow(2).mean(dim=1, keepdim=True).sqrt()
    scale = top.clamp(min=1e-8) / levels
    q = (w32 / scale).round().clamp(-levels, levels) * scale
    return w + (q.to(w.dtype) - w).detach()


def rms_norm(x):
    return F.rms_norm(x, (x.size(-1),))


def rope_tables(ctx, head_dim, device=None):
    inv = 1.0 / (10000 ** (torch.arange(0, head_dim, 2, device=device).float() / head_dim))
    t = torch.arange(ctx, device=device).float()
    f = torch.outer(t, inv)
    return f.cos(), f.sin()  # (ctx, head_dim/2)


def apply_rope(x, cos, sin):
    # x: (B, H, T, D); cos/sin: (T, D/2)
    x1, x2 = x[..., 0::2], x[..., 1::2]
    cos, sin = cos.to(x.dtype), sin.to(x.dtype)
    y1 = x1 * cos - x2 * sin
    y2 = x1 * sin + x2 * cos
    return torch.stack((y1, y2), dim=-1).flatten(-2)


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        d = cfg.d_model
        self.n_head = cfg.n_head
        self.cfg = cfg
        if cfg.value_resid:
            self.lam = nn.Parameter(torch.tensor([0.5, 0.5]))
        if cfg.ngpt:  # learned step sizes, stored at 1.0 and scaled to start at 0.05
            self.alpha_a = nn.Parameter(torch.ones(d))
            self.alpha_m = nn.Parameter(torch.ones(d))
        self.q = nn.Linear(d, d, bias=False)
        self.k = nn.Linear(d, d, bias=False)
        self.v = nn.Linear(d, d, bias=False)
        self.o = nn.Linear(d, d, bias=False)
        self.fc = nn.Linear(d, cfg.mlp_mult * d, bias=False)
        self.proj = nn.Linear(cfg.mlp_mult * d, d, bias=False)

    def forward(self, x, cos, sin, past=None, v1=None, ve=None):
        B, T, C = x.shape
        H = self.n_head
        h = x if self.cfg.ngpt else rms_norm(x)
        q = F.linear(h, fake_quant(self.q.weight, self.cfg.qbits)).view(B, T, H, C // H).transpose(1, 2)
        k = F.linear(h, fake_quant(self.k.weight, self.cfg.qbits)).view(B, T, H, C // H).transpose(1, 2)
        v = F.linear(h, fake_quant(self.v.weight, self.cfg.qbits)).view(B, T, H, C // H).transpose(1, 2)
        v_raw = v
        if self.cfg.value_resid and v1 is not None:
            v = self.lam[0] * v + self.lam[1] * v1
        if ve is not None:
            v = v + ve.view(B, T, H, C // H).transpose(1, 2)
        if self.cfg.qk_norm or self.cfg.ngpt:
            q, k = rms_norm(q), rms_norm(k)
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
        if past is None:
            y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
            present = None
        else:
            pk, pv = past
            if pk is not None:
                k = torch.cat((pk, k), dim=2)
                v = torch.cat((pv, v), dim=2)
            S = k.size(2)
            mask = torch.ones(T, S, dtype=torch.bool, device=x.device).tril(S - T)
            y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
            present = (k, v)
        y = y.transpose(1, 2).reshape(B, T, C)
        if self.cfg.ngpt:
            x = rms_norm(x + 0.05 * self.alpha_a * (rms_norm(F.linear(y, fake_quant(self.o.weight, self.cfg.qbits))) - x))
            h = F.linear(x, fake_quant(self.fc.weight, self.cfg.qbits))
            h = F.relu(h).square() if self.cfg.relu2 else F.gelu(h)
            x = rms_norm(x + 0.05 * self.alpha_m * (rms_norm(F.linear(h, fake_quant(self.proj.weight, self.cfg.qbits))) - x))
            return x, present, v_raw
        x = x + F.linear(y, fake_quant(self.o.weight, self.cfg.qbits))
        h = F.linear(rms_norm(x), fake_quant(self.fc.weight, self.cfg.qbits))
        h = F.relu(h).square() if self.cfg.relu2 else F.gelu(h)
        x = x + F.linear(h, fake_quant(self.proj.weight, self.cfg.qbits))
        return x, present, v_raw


class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg
        self.emb = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        if cfg.hash_rows:
            self.pair_emb = nn.Embedding(cfg.hash_rows, cfg.d_model)
        if cfg.val_emb:
            self.val_embs = nn.ModuleList([nn.Embedding(cfg.vocab_size, cfg.d_model) for _ in range(cfg.val_emb)])
        if cfg.mtp:
            self.mtp_proj = nn.Linear(cfg.d_model, cfg.d_model, bias=False)
        cos, sin = rope_tables(cfg.ctx, cfg.d_model // cfg.n_head)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)
        self.reset_parameters()

    def reset_parameters(self):
        """Standard random initialisation (this is what the twin starts from)."""
        nn.init.normal_(self.emb.weight, std=0.02)
        if self.cfg.hash_rows:
            nn.init.zeros_(self.pair_emb.weight)
        if self.cfg.val_emb:
            for e in self.val_embs:
                nn.init.zeros_(e.weight)
        if self.cfg.mtp:
            nn.init.normal_(self.mtp_proj.weight, std=0.02)
        res_std = 0.02 / math.sqrt(2 * self.cfg.n_layer)
        for b in self.blocks:
            for name in MATRIX_NAMES:
                std = res_std if name in ("o", "proj") else 0.02
                nn.init.normal_(getattr(b, name).weight, std=std)

    # -- access to the matrices the seed generates ---------------------------
    def matrices(self):
        """Dict: group name -> list of weight Parameters in a fixed order.

        attn: n_layer*4 matrices of shape (d, d), order layer0 q,k,v,o, layer1 ...
        fc:   n_layer matrices of shape (4d, d)
        proj: n_layer matrices of shape (d, 4d)
        """
        out = {"attn": [], "fc": [], "proj": []}
        for b in self.blocks:
            out["attn"] += [b.q.weight, b.k.weight, b.v.weight, b.o.weight]
            out["fc"].append(b.fc.weight)
            out["proj"].append(b.proj.weight)
        return out

    def n_params(self):
        emb = self.emb.weight.numel()
        blocks = sum(p.numel() for ms in self.matrices().values() for p in ms)
        return {"embedding": emb, "blocks": blocks, "total": sum(p.numel() for p in self.parameters())}

    # -- forward -------------------------------------------------------------
    def forward(self, idx, targets=None, past=None, mask=None, prev=None):
        """prev: (B,) the token before idx[:, 0], needed by the word-pair table when generating with a cache."""
        B, T = idx.shape
        emb_w = fake_quant(self.emb.weight, self.cfg.qbits)
        x = F.embedding(idx, emb_w)
        if self.cfg.hash_rows:
            first = prev if prev is not None else torch.full((B,), self.cfg.vocab_size, device=idx.device)
            before = torch.cat((first[:, None], idx[:, :-1]), dim=1)
            x = x + self.pair_emb((before * 36313 + idx * 27191) % self.cfg.hash_rows)
        x = rms_norm(x)
        nv = self.cfg.val_emb
        ves = [e(idx) for e in self.val_embs] if nv else None
        ve_of = lambda i: ves[min(nv - 1, i * nv // len(self.blocks))] if nv else None
        if past is None:
            cos, sin = self.cos[:T], self.sin[:T]
            presents = None
            v1 = None
            for i, b in enumerate(self.blocks):
                x, _, v = b(x, cos, sin, None, v1, ve_of(i))
                v1 = v if v1 is None else v1
        else:
            start = 0 if past[0][0] is None else past[0][0].size(2)
            cos, sin = self.cos[start:start + T], self.sin[start:start + T]
            presents = []
            v1 = None
            for i, (b, p) in enumerate(zip(self.blocks, past)):
                x, pr, v = b(x, cos, sin, p, v1, ve_of(i))
                v1 = v if v1 is None else v1
                presents.append(pr)
        logits = F.linear(rms_norm(x), emb_w)
        if targets is None:
            return logits, presents
        if mask is None:
            loss = F.cross_entropy(logits.float().view(-1, logits.size(-1)), targets.reshape(-1))
        else:  # mean over the masked positions only
            l = F.cross_entropy(logits.float().view(-1, logits.size(-1)), targets.reshape(-1), reduction="none")
            m = mask.reshape(-1).float()
            loss = (l * m).sum() / m.sum().clamp(min=1)
        if self.cfg.mtp and self.training and T > 1:  # extra loss: the token after next, from a small side head
            h2 = rms_norm(x + self.mtp_proj(rms_norm(x)))[:, :-1]
            l2 = F.cross_entropy(F.linear(h2, emb_w).float().reshape(-1, logits.size(-1)),
                                 targets[:, 1:].reshape(-1), reduction="none")
            m2 = torch.ones_like(l2) if mask is None else mask[:, 1:].reshape(-1).float()
            loss = loss + self.cfg.mtp * (l2 * m2).sum() / m2.sum().clamp(min=1)
        return logits, loss

    @torch.no_grad()
    def generate(self, tokens, max_new=128, temperature=0.7, top_k=40, stop_ids=(),
                 rep_penalty=1.0, generator=None):
        """Yield new token ids one at a time, using a key-value cache.

        tokens: list of prompt token ids. Keeps only the last ctx-max_new tokens.
        """
        dev = self.emb.weight.device
        max_new = min(max_new, self.cfg.ctx - 16)
        keep = self.cfg.ctx - max_new
        tokens = list(tokens)[-keep:]
        x = torch.tensor([tokens], device=dev)
        past = [(None, None)] * len(self.blocks)
        seen = list(tokens)
        prev = None
        for _ in range(max_new):
            logits, past = self(x, past=past, prev=prev)
            prev = x[:, -1]
            logits = logits[0, -1].float()
            if rep_penalty != 1.0 and seen:
                recent = torch.tensor(sorted(set(seen[-64:])), device=dev)
                l = logits[recent]
                logits[recent] = torch.where(l > 0, l / rep_penalty, l * rep_penalty)
            if temperature <= 0:
                nxt = int(logits.argmax())
            else:
                logits = logits / temperature
                if top_k:
                    kth = torch.topk(logits, min(top_k, logits.numel())).values[-1]
                    logits[logits < kth] = -float("inf")
                probs = torch.softmax(logits, dim=-1)
                nxt = int(torch.multinomial(probs, 1, generator=generator))
            if nxt in stop_ids:
                return
            yield nxt
            seen.append(nxt)
            x = torch.tensor([[nxt]], device=dev)

"""Shared pieces: configs, token data streams, evaluation, logging."""
import json
import math
import os
import time

import numpy as np
import torch

from model import GPTConfig

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
TOK_DIR = os.path.join(DATA, "tok")

SPECIALS = ["<|endoftext|>", "<|user|>", "<|assistant|>", "<|end|>"]
EOT, USER, ASSISTANT, END = 0, 1, 2, 3

# name -> (model config, seed hidden width for attention matrices, for MLP matrices)
CONFIGS = {
    "full": (GPTConfig(vocab_size=8192, n_layer=12, n_head=8, d_model=512, ctx=512), 72, 128),
    "pilot": (GPTConfig(vocab_size=8192, n_layer=6, n_head=4, d_model=256, ctx=256), 36, 64),
    "deep": (GPTConfig(vocab_size=8192, n_layer=10, n_head=4, d_model=208, ctx=256), 36, 64),
    "smoke": (GPTConfig(vocab_size=8192, n_layer=2, n_head=2, d_model=64, ctx=128), 8, 12),
    # stage 3: small normal models for the same-file-size comparison (no seed is made for these)
    "sizeC": (GPTConfig(vocab_size=8192, n_layer=6, n_head=4, d_model=192, ctx=512), 8, 12),
    "sizeA": (GPTConfig(vocab_size=8192, n_layer=6, n_head=4, d_model=256, ctx=512), 8, 12),
    "sizeB": (GPTConfig(vocab_size=8192, n_layer=8, n_head=8, d_model=320, ctx=512), 8, 12),
}

# chat-phase mixture: stream name -> sampling probability
CHAT_MIX = {"synth": 0.30, "tinychat": 0.27, "smol": 0.08, "storyreq": 0.15,
            "everyday": 0.03, "stories": 0.17}


def setup_torch(seed=0):
    torch.manual_seed(seed)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


def load_tokenizer():
    from tokenizers import Tokenizer
    return Tokenizer.from_file(os.path.join(DATA, "tokenizer.json"))


class Stream:
    """A flat uint16 token file sampled with random windows."""

    def __init__(self, name, split):
        path = os.path.join(TOK_DIR, f"{name}_{split}.bin")
        self.data = np.memmap(path, dtype=np.uint16, mode="r")
        self.name = name

    def packed(self, rng, T):
        """One window that starts at the start of a conversation or story (tight packing)."""
        if not hasattr(self, "starts"):
            s = np.flatnonzero(np.asarray(self.data) == EOT)
            self.starts = s[s < len(self.data) - T - 1]
        return self.data[(s := int(self.starts[rng.integers(0, len(self.starts))])):s + T + 1]

    def windows(self, rng, n, T):
        starts = rng.integers(0, len(self.data) - T - 1, size=n)
        return np.stack([self.data[s:s + T + 1] for s in starts])


class Mixture:
    def __init__(self, mix, split):
        self.names = list(mix)
        self.probs = np.array([mix[n] for n in self.names], dtype=np.float64)
        self.probs /= self.probs.sum()
        self.streams = [Stream(n, split) for n in self.names]

    def batch(self, rng, B, T, device="cuda", pack=False):
        which = rng.choice(len(self.streams), size=B, p=self.probs)
        if pack:
            rows = [self.streams[w].packed(rng, T) for w in which]
        else:
            rows = [self.streams[w].windows(rng, 1, T)[0] for w in which]
        arr = torch.from_numpy(np.stack(rows).astype(np.int64))
        arr = arr.to(device, non_blocking=True)
        return arr[:, :-1], arr[:, 1:]


def fixed_val_batches(mix, n_batches, B, T, device="cuda", seed=1234):
    m = Mixture(mix, "val")
    rng = np.random.default_rng(seed)
    return [m.batch(rng, B, T, device) for _ in range(n_batches)]


@torch.no_grad()
def evaluate(model, batches):
    was = model.training
    model.eval()
    tot = 0.0
    for x, y in batches:
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        tot += loss.item()
    model.train(was)
    return tot / len(batches)


def role_mask(x, plain=True):
    """True where the next token is written by the assistant.

    A position counts if the last marker at or before it is the assistant tag. With plain=True,
    text straight after an end-of-text mark (a plain story, no user tag) counts too.
    """
    marker = (x == USER) | (x == ASSISTANT) | (x == EOT) | (x == END)
    pos = torch.arange(x.size(1), device=x.device).expand_as(x)
    last = torch.where(marker, pos, torch.full_like(pos, -1)).cummax(dim=1).values
    role = torch.where(last >= 0, x.gather(1, last.clamp(min=0)), torch.full_like(x, -1))
    return (role == ASSISTANT) | (role == EOT) if plain else role == ASSISTANT


@torch.no_grad()
def evaluate_assistant(model, batches):
    """Chat loss on assistant tokens only (same measure as the scoreboard)."""
    was = model.training
    model.eval()
    tot, n = 0.0, 0
    for x, y in batches:
        m = role_mask(x, plain=False)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y, mask=m)
        tot += loss.item() * int(m.sum()); n += int(m.sum())
    model.train(was)
    return tot / n


def cosine_lr(step, total, peak, warmup, floor_frac=0.1):
    if step < warmup:
        return peak * (step + 1) / warmup
    p = (step - warmup) / max(1, total - warmup)
    return peak * (floor_frac + (1 - floor_frac) * 0.5 * (1 + math.cos(math.pi * min(1.0, p))))


class Log:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self.t0 = time.time()

    def write(self, **kw):
        kw["wall"] = round(time.time(), 1)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(kw) + "\n")
        print(" ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
                       for k, v in kw.items() if k != "wall"), flush=True)


def read_log(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


def format_chat(messages):
    """Token-level chat layout as text with special tokens."""
    s = "<|endoftext|>"
    for m in messages:
        tag = "<|user|>" if m["role"] == "user" else "<|assistant|>"
        s += tag + m["content"].strip() + "<|end|>"
    return s

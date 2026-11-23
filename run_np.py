"""Run the model without PyTorch. Needs only numpy and the tokenizers package.

  python run_np.py convert final/small-smart-4bit.bin final/small-smart-4bit.npz   (one time, this step uses PyTorch)
  python run_np.py final/small-smart-4bit.npz                                      chat
  python run_np.py final/small-smart-4bit.npz --once "What is 7 + 8?"
  python run_np.py final/small-smart-4bit.npz --bench

The .npz file keeps the weights as low-bit codes. They are unpacked to 32-bit floats when loaded.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EOT, USER, ASSISTANT, END = 0, 1, 2, 3
EPS = np.float32(1.1920929e-07)


def convert(src, dst):
    import torch
    d = torch.load(src, map_location="cpu", weights_only=False)
    out = {"cfg": np.array(json.dumps(d["cfg"])), "bits": np.array(d["bits"])}
    for k, (c, s, shape) in d["q"].items():
        out["c:" + k], out["s:" + k], out["n:" + k] = c.numpy(), s.numpy(), np.array(shape)
    for k, v in d["other"].items():
        out["o:" + k] = v.float().numpy()
    np.savez(dst, **out)
    print(dst, f"{os.path.getsize(dst) / 1e6:.1f} MB")


class Model:
    def __init__(self, path):
        z = np.load(path)
        self.cfg = json.loads(str(z["cfg"]))
        bits = int(z["bits"])
        w = {}
        for k in z.files:
            if k.startswith("c:"):
                name, c, shape = k[2:], z[k], tuple(z["n:" + k[2:]])
                if bits <= 4:  # two codes per byte
                    c = (np.stack(((c >> 4) & 15, c & 15), axis=1).reshape(-1)[:shape[0] * shape[1]].astype(np.int8) - 8).reshape(shape)
                w[name] = c.astype(np.float32) * z["s:" + name].astype(np.float32)
            elif k.startswith("o:"):
                w[k[2:]] = z[k].astype(np.float32)
        self.emb = w["emb.weight"]
        L, self.H = self.cfg["n_layer"], self.cfg["n_head"]
        # weights are stored (out, in); keep them transposed so x @ W works on rows
        self.blocks = [{n: np.ascontiguousarray(w[f"blocks.{i}.{n}.weight"].T) for n in ("q", "k", "v", "o", "fc", "proj")} for i in range(L)]
        self.lam = [w.get(f"blocks.{i}.lam") for i in range(L)]
        hd = self.cfg["d_model"] // self.H
        inv = 1.0 / (10000 ** (np.arange(0, hd, 2, dtype=np.float32) / hd))
        f = np.outer(np.arange(self.cfg["ctx"], dtype=np.float32), inv)
        self.cos, self.sin = np.cos(f).astype(np.float32), np.sin(f).astype(np.float32)
        self.reset()

    def reset(self):
        self.past = [None] * len(self.blocks)
        self.pos = 0

    @staticmethod
    def norm(x):
        return x / np.sqrt((x * x).mean(-1, keepdims=True) + EPS)

    @staticmethod
    def gelu(x):  # exact GELU, erf by Abramowitz and Stegun 7.1.26 (error under 2e-7)
        z = np.abs(x) * np.float32(0.70710678)
        t = 1.0 / (1.0 + 0.3275911 * z)
        e = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-z * z)
        return (0.5 * x * (1.0 + np.sign(x) * e)).astype(np.float32)

    def rope(self, x, cos, sin):  # x: (H, T, D)
        x1, x2 = x[..., 0::2], x[..., 1::2]
        out = np.empty_like(x)
        out[..., 0::2] = x1 * cos - x2 * sin
        out[..., 1::2] = x1 * sin + x2 * cos
        return out

    def step(self, ids):
        """Feed tokens, return the scores for the next token."""
        T, H = len(ids), self.H
        x = self.norm(self.emb[ids])
        C = x.shape[1]
        cos, sin = self.cos[self.pos:self.pos + T], self.sin[self.pos:self.pos + T]
        v1 = None
        for i, b in enumerate(self.blocks):
            h = self.norm(x)
            q = (h @ b["q"]).reshape(T, H, C // H).transpose(1, 0, 2)
            k = (h @ b["k"]).reshape(T, H, C // H).transpose(1, 0, 2)
            v = (h @ b["v"]).reshape(T, H, C // H).transpose(1, 0, 2)
            if v1 is None:
                v1 = v
            elif self.lam[i] is not None:
                v = self.lam[i][0] * v + self.lam[i][1] * v1
            q, k = self.rope(q, cos, sin), self.rope(k, cos, sin)
            if self.past[i] is not None:
                k = np.concatenate((self.past[i][0], k), axis=1)
                v = np.concatenate((self.past[i][1], v), axis=1)
            self.past[i] = (k, v)
            att = (q @ k.transpose(0, 2, 1)) / np.float32(np.sqrt(C // H))  # (H, T, S)
            S = k.shape[1]
            if T > 1:
                att = np.where(np.tril(np.ones((T, S), dtype=bool), S - T), att, -np.inf)
            att = np.exp(att - att.max(-1, keepdims=True))
            att /= att.sum(-1, keepdims=True)
            y = (att @ v).transpose(1, 0, 2).reshape(T, C)
            x = x + y @ b["o"]
            x = x + self.gelu(self.norm(x) @ b["fc"]) @ b["proj"]
        self.pos += T
        return self.norm(x[-1]) @ self.emb.T

    def generate(self, ids, max_new=200, temp=0.6, top_k=40, rep_penalty=1.1, rng=None):
        rng = rng or np.random.default_rng()
        max_new = min(max_new, self.cfg["ctx"] - 16)
        ids = list(ids)[-(self.cfg["ctx"] - max_new):]
        self.reset()
        seen, feed = list(ids), ids
        for _ in range(max_new):
            logits = self.step(feed).astype(np.float32)
            if rep_penalty != 1.0:
                r = np.array(sorted(set(seen[-64:])))
                logits[r] = np.where(logits[r] > 0, logits[r] / rep_penalty, logits[r] * rep_penalty)
            if temp <= 0:
                nxt = int(logits.argmax())
            else:
                logits = logits / temp
                if top_k:
                    logits[logits < np.partition(logits, -top_k)[-top_k]] = -np.inf
                p = np.exp(logits - logits.max())
                nxt = int(rng.choice(len(p), p=p / p.sum()))
            if nxt in (END, EOT, USER, ASSISTANT):
                return
            yield nxt
            seen.append(nxt)
            feed = [nxt]


def chat_ids(tok, history):
    ids = [EOT]
    for role, text in history:
        ids += [USER if role == "user" else ASSISTANT] + tok.encode(text.strip()).ids + [END]
    return ids + [ASSISTANT]


def main():
    if sys.argv[1] == "convert":
        return convert(sys.argv[2], sys.argv[3])
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(HERE, "data", "tokenizer.json"))
    t = time.time()
    model = Model(sys.argv[1])
    load_s = time.time() - t
    if "--bench" in sys.argv:
        import psutil
        for prompt in ("Tell me a long story about a dog and a cat.", "What is 7 + 8?"):
            ids = chat_ids(tok, [("user", prompt)])
            t = time.time()
            out = list(model.generate(ids, rng=np.random.default_rng(0)))
            dt = time.time() - t
            print(f"{len(ids)} prompt tokens, {len(out)} new tokens, {dt:.2f} s, {len(out) / dt:.1f} tokens per second")
        m = psutil.Process().memory_info()
        print(f"load {load_s:.1f} s, RAM now {m.rss / 2**20:.0f} MiB, peak {m.peak_wset / 2**20:.0f} MiB")
        return
    if "--once" in sys.argv:
        temp = 0.0 if "--greedy" in sys.argv else 0.6
        ids = chat_ids(tok, [("user", sys.argv[sys.argv.index("--once") + 1])])
        print(tok.decode(list(model.generate(ids, temp=temp))).strip())
        return
    history = []
    print("Type /reset to clear, /quit to leave.")
    while True:
        try:
            msg = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if msg == "/quit":
            break
        if msg == "/reset":
            history = []
            continue
        if not msg:
            continue
        history = (history + [("user", msg)])[-8:]
        out, shown = [], ""
        sys.stdout.write("bot> ")
        for t in model.generate(chat_ids(tok, history)):
            out.append(t)
            text = tok.decode(out)
            sys.stdout.write(text[len(shown):]); sys.stdout.flush()
            shown = text
        print()
        history.append(("assistant", tok.decode(out).strip()))


if __name__ == "__main__":
    main()

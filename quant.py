"""Real low-bit model files: export a trained model with its weights stored as small integers.

  python quant.py runs/x/final.pt 8 out.q8.pt     (bits: 8 or 4; writes the file and prints its size)

Each weight matrix (and the embedding table) is stored as integer codes plus one half-precision
scale per row, using the same rounding as training (model.fake_quant). 4-bit codes are packed two
to a byte. load() turns the file back into a normal checkpoint, so every other tool works on it.
"""
import os
import sys

import numpy as np
import torch

from model import fake_quant


def codes_and_scale(w, bits):
    levels = 2 ** (bits - 1) - 1
    w = w.float()
    top = w.abs().amax(dim=1, keepdim=True) if bits >= 8 else (2.5 if bits >= 4 else 1.5) * w.pow(2).mean(dim=1, keepdim=True).sqrt()
    scale = top.clamp(min=1e-8) / levels
    return (w / scale).round().clamp(-levels, levels).to(torch.int8), scale


def export(src, bits, dst):
    ck = torch.load(src, map_location="cpu", weights_only=False)
    out = dict(cfg=ck["cfg"], bits=bits, step=ck.get("step"), q={}, other={})
    for k, v in ck["model"].items():
        if v.ndim == 2:
            c, s = codes_and_scale(v, bits)
            if bits <= 4:  # pack two 4-bit codes per byte
                flat = (c.flatten().numpy().astype(np.int16) + 8).astype(np.uint8)
                if len(flat) % 2:
                    flat = np.append(flat, 0)
                c = torch.from_numpy((flat[0::2] << 4) | flat[1::2])
            out["q"][k] = (c, s.half(), tuple(v.shape))
        else:
            out["other"][k] = v.half()
    torch.save(out, dst)
    return os.path.getsize(dst)


def load(path):
    """Returns a normal checkpoint dict (model weights as floats on the quantised grid)."""
    d = torch.load(path, map_location="cpu", weights_only=False)
    model = dict(d["other"])
    for k, (c, s, shape) in d["q"].items():
        if d["bits"] <= 4:
            b = c.numpy()
            flat = np.stack(((b >> 4) & 15, b & 15), axis=1).flatten()[:shape[0] * shape[1]].astype(np.int16) - 8
            c = torch.from_numpy(flat.astype(np.int8)).view(shape)
        model[k] = c.float() * s.float()
    cfg = dict(d["cfg"])
    cfg["qbits"] = 0  # the stored weights are already on the grid
    return dict(model=model, cfg=cfg, step=d.get("step"))


if __name__ == "__main__":
    src, bits, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    n = export(src, bits, dst)
    torch.save(load(dst), dst + ".float.pt")  # a normal checkpoint for the scoreboard
    print(f"{dst}: {n / 2**20:.2f} MB")

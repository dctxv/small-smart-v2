"""Stage 0 probe: peak memory and speed for one shape at one micro-batch.

Each effective step is 64 x 512 tokens, split into chunks of --micro rows
(gradient accumulation). Prints one JSON line.

  python probe.py --layers 12 --width 512 --micro 64
"""
import argparse
import json
import time

import numpy as np
import torch

from common import Mixture, evaluate, fixed_val_batches, setup_torch
from model import GPT, GPTConfig

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", type=int, default=12)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--heads", type=int, default=8)
    ap.add_argument("--micro", type=int, default=64)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--compile", action="store_true")
    a = ap.parse_args()
    out = dict(layers=a.layers, width=a.width, micro=a.micro, compile=a.compile)
    try:
        setup_torch(0)
        cfg = GPTConfig(vocab_size=8192, n_layer=a.layers, n_head=a.heads, d_model=a.width, ctx=512)
        model = GPT(cfg).cuda()
        out["params"] = model.n_params()["total"]
        fwd = torch.compile(model) if a.compile else model
        opt = torch.optim.AdamW(model.parameters(), lr=6e-4, betas=(0.9, 0.95), weight_decay=0.05, fused=True)
        rng = np.random.default_rng(0)
        data = Mixture({"stories": 1.0}, "train")
        val = fixed_val_batches({"stories": 1.0}, 2, 64, 512)
        torch.cuda.reset_peak_memory_stats()
        times = []
        for step in range(a.steps):
            torch.cuda.synchronize(); t = time.time()
            x, y = data.batch(rng, 64, 512)
            opt.zero_grad(set_to_none=True)
            for xc, yc in zip(x.split(a.micro), y.split(a.micro)):
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    _, loss = fwd(xc, yc)
                (loss * len(xc) / 64).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            torch.cuda.synchronize(); times.append(time.time() - t)
            if step == 3:
                evaluate(model, val)
        tail = times[4:]
        out.update(ok=True, sec_per_step=float(np.median(tail)), sec_per_step_max=float(max(tail)),
                   alloc_mb=torch.cuda.max_memory_allocated() / 2**20,
                   reserved_mb=torch.cuda.max_memory_reserved() / 2**20, loss=float(loss))
    except Exception as e:  # out of memory or compile failure
        out.update(ok=False, error=f"{type(e).__name__}: {str(e)[:300]}")
    print("RESULT " + json.dumps(out), flush=True)

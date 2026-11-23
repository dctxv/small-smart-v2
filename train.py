"""Train a model: stories first, then the chat format. No seed code in this copy.

  python train.py --name base_s0 --cfg pilot --steps1 6000 --steps2 1500 --seed 0
  python train.py --name x --accum 4                      (micro-batch 16, same data)
  python train.py --name x --set qk_norm=1 relu2=1        (model options)
  python train.py --name x --opt muon --muon_lr 0.02

Each step draws one batch of --batch rows (so the data order never depends on --accum)
and splits it into --accum equal chunks. runs/<name>/ckpt.pt is the resume point.
Milestone checkpoints are kept. Peak GPU memory is logged. An average of the weights
(EMA) is kept alongside and scored separately as val_*_ema.
"""
import argparse
import os
import time

import numpy as np
import torch

from common import (CHAT_MIX, CONFIGS, ROOT, Log, Mixture, cosine_lr, evaluate, evaluate_assistant,
                    fixed_val_batches, role_mask, setup_torch)
from model import GPT, GPTConfig
from optim import Muon

MILESTONES = (1000, 2000, 4000, 8000, 12000, 16000)


def atomic_save(obj, path):
    tmp = path + ".tmp"
    torch.save(obj, tmp)
    os.replace(tmp, path)


def parse_set(items):
    out = {}
    for it in items:
        k, v = it.split("=")
        out[k] = float(v) if "." in v else int(v)
    return out


class Ema:
    def __init__(self, model, decay):
        self.decay, self.n = decay, 0
        self.params = [p for p in model.parameters()]
        self.avg = [p.detach().clone() for p in self.params]

    @torch.no_grad()
    def update(self):
        self.n += 1
        d = min(self.decay, (1 + self.n) / (10 + self.n))
        for a, p in zip(self.avg, self.params):
            a.lerp_(p, 1 - d)

    @torch.no_grad()
    def swap(self):
        for a, p in zip(self.avg, self.params):
            t = p.detach().clone(); p.copy_(a); a.copy_(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--cfg", default="full")
    ap.add_argument("--layers", type=int, default=0)
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--heads", type=int, default=0)
    ap.add_argument("--set", nargs="*", default=[], help="model options, like qk_norm=1")
    ap.add_argument("--accum", type=int, default=1, help="split each batch into this many chunks")
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--steps1", type=int, default=16000, help="story steps")
    ap.add_argument("--steps2", type=int, default=4000, help="chat steps")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--opt", default="adamw", choices=["adamw", "muon"])
    ap.add_argument("--lr1", type=float, default=6e-4)
    ap.add_argument("--lr2_frac", type=float, default=0.5, help="chat phase peak lr as a fraction of lr1")
    ap.add_argument("--muon_lr", type=float, default=0.02)
    ap.add_argument("--warmup", type=int, default=300)
    ap.add_argument("--wd", type=float, default=0.05)
    ap.add_argument("--ema", type=float, default=0.999)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--eval_every", type=int, default=250)
    ap.add_argument("--ckpt_every", type=int, default=500)
    ap.add_argument("--stop_after", type=int, default=0)
    ap.add_argument("--emb_from", default="", help="copy the embedding table from this checkpoint file")
    ap.add_argument("--start_from", default="", help="start the chat phase from another run's stories_full.pt")
    ap.add_argument("--model_from", default="", help="start the chat phase from model weights only (fresh optimiser state)")
    ap.add_argument("--chat_loss", default="all", choices=["all", "assistant"],
                    help="assistant: chat phase loss on assistant tokens only, with tight packing")
    ap.add_argument("--chat_mix", default="", help="json file with a chat mixture, replaces the default")
    a = ap.parse_args()

    setup_torch(a.seed)
    run_dir = os.path.join(ROOT, "runs", a.name)
    os.makedirs(run_dir, exist_ok=True)
    cfg = CONFIGS[a.cfg][0]
    kw = cfg.to_dict()
    kw.update(parse_set(a.set))
    if a.layers: kw["n_layer"] = a.layers
    if a.width: kw["d_model"] = a.width
    if a.heads: kw["n_head"] = a.heads
    cfg = GPTConfig(**kw)
    assert a.batch % a.accum == 0
    model = GPT(cfg).cuda()
    print("config", cfg.to_dict(), "params", model.n_params(), flush=True)
    if a.emb_from:
        ck = torch.load(a.emb_from, map_location="cuda", weights_only=False)
        with torch.no_grad():
            model.emb.weight.copy_(ck["model"]["emb.weight"].float())
        print("embedding table taken from", a.emb_from, flush=True)

    if a.model_from:
        ck = torch.load(a.model_from, map_location="cuda", weights_only=False)
        model.load_state_dict({k: v.float() for k, v in ck["model"].items()})
        print("model weights taken from", a.model_from, flush=True)

    mats = [p for n, p in model.named_parameters() if n.startswith("blocks.") and p.ndim == 2]
    rest = [p for n, p in model.named_parameters() if not (n.startswith("blocks.") and p.ndim == 2)]
    if a.opt == "adamw":
        opts = [torch.optim.AdamW(model.parameters(), lr=a.lr1, betas=(0.9, 0.95), weight_decay=a.wd, fused=True)]
    else:
        opts = [torch.optim.AdamW(rest, lr=a.lr1, betas=(0.9, 0.95), weight_decay=a.wd, fused=True),
                Muon(mats, lr=a.muon_lr, momentum=0.95)]
    base_lr = [o.param_groups[0]["lr"] for o in opts]
    ema = Ema(model, a.ema)
    rng = np.random.default_rng(a.seed)
    total = a.steps1 + a.steps2
    step = 0

    def full_state():
        return dict(model=model.state_dict(), opts=[o.state_dict() for o in opts], ema=ema.avg, ema_n=ema.n,
                    rng=rng.bit_generator.state, step=step, cfg=cfg.to_dict())

    def load_full(path):
        ck = torch.load(path, map_location="cuda", weights_only=False)
        model.load_state_dict(ck["model"])
        for o, sd in zip(opts, ck["opts"]):
            o.load_state_dict(sd)
        with torch.no_grad():
            for e, s in zip(ema.avg, ck["ema"]):
                e.copy_(s)
        ema.n = ck["ema_n"]
        rng.bit_generator.state = ck["rng"]
        return ck["step"]

    ck_path = os.path.join(run_dir, "ckpt.pt")
    if os.path.exists(ck_path):
        step = load_full(ck_path)
        print("resumed at step", step, flush=True)
    elif a.model_from:
        step = a.steps1
    elif a.start_from:
        step = load_full(a.start_from)
        assert step == a.steps1
        print("chat phase started from", a.start_from, flush=True)

    mix = CHAT_MIX
    if a.chat_mix:
        import json
        mix = json.load(open(a.chat_mix))
    stories = Mixture({"stories": 1.0}, "train")
    chat = Mixture(mix, "train") if a.steps2 else None
    val_story = fixed_val_batches({"stories": 1.0}, 20, 64, cfg.ctx)
    chat_only = {k: v for k, v in CHAT_MIX.items() if k != "stories"}
    val_chat = fixed_val_batches(chat_only, 20, 64, cfg.ctx) if a.steps2 else None
    log = Log(os.path.join(run_dir, "log.jsonl"))

    def evals(with_ema=True):
        rec = dict(val_story=evaluate(model, val_story))
        if val_chat:
            rec["val_chat"] = evaluate(model, val_chat)
            rec["val_chat_asst"] = evaluate_assistant(model, val_chat)
        if with_ema:
            ema.swap()
            rec["val_story_ema"] = evaluate(model, val_story)
            if val_chat:
                rec["val_chat_ema"] = evaluate(model, val_chat)
                rec["val_chat_asst_ema"] = evaluate_assistant(model, val_chat)
            ema.swap()
        return rec

    if step == 0:
        log.write(step=0, phase=1, **evals(False))

    model.train()
    fwd = torch.compile(model) if a.compile else model
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    run = []
    end = min(total, a.stop_after) if a.stop_after else total
    while step < end:
        phase = 1 if step < a.steps1 else 2
        mask = None
        if phase == 1:
            f = cosine_lr(step, a.steps1, 1.0, a.warmup)
            x, y = stories.batch(rng, a.batch, cfg.ctx)
        else:
            f = a.lr2_frac * cosine_lr(step - a.steps1, a.steps2, 1.0, 100)
            x, y = chat.batch(rng, a.batch, cfg.ctx, pack=a.chat_loss == "assistant")
            if a.chat_loss == "assistant":
                mask = role_mask(x)
        for o, b in zip(opts, base_lr):
            for g in o.param_groups:
                g["lr"] = b * f
            o.zero_grad(set_to_none=True)
        tot = 0.0
        chunks = zip(x.chunk(a.accum), y.chunk(a.accum), mask.chunk(a.accum) if mask is not None else [None] * a.accum)
        for xc, yc, mc in chunks:
            with torch.autocast("cuda", dtype=torch.bfloat16):
                _, loss = fwd(xc, yc, mask=mc)
            (loss / a.accum).backward()
            tot += loss.item() / a.accum
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        for o in opts:
            o.step()
        ema.update()
        run.append(tot)
        step += 1
        if step % 50 == 0 or step == end:
            rec = dict(step=step, phase=phase, train=float(np.mean(run[-50:])), lr=f,
                       min=(time.time() - t0) / 60,
                       mem_alloc_mb=torch.cuda.max_memory_allocated() / 2**20,
                       mem_reserved_mb=torch.cuda.max_memory_reserved() / 2**20)
            if step % a.eval_every == 0 or step == end or step == a.steps1:
                rec.update(evals())
            log.write(**rec)
        for hit, fname in ((step in MILESTONES, f"step_{step}.pt"), (step == a.steps1, "after_stories.pt")):
            if hit:  # kept, never overwritten
                atomic_save(dict(model=model.state_dict(), cfg=cfg.to_dict(), step=step),
                            os.path.join(run_dir, fname))
        if step == a.steps1:
            atomic_save(full_state(), os.path.join(run_dir, "stories_full.pt"))
        if step % a.ckpt_every == 0 or step == end:
            atomic_save(full_state(), ck_path)
    if step >= total:
        atomic_save(dict(model={k: v.half() for k, v in model.state_dict().items()},
                         cfg=cfg.to_dict(), step=step), os.path.join(run_dir, "final.pt"))
        ema.swap()
        atomic_save(dict(model={k: v.half() for k, v in model.state_dict().items()},
                         cfg=cfg.to_dict(), step=step), os.path.join(run_dir, "final_ema.pt"))
        ema.swap()
        print("final model saved", flush=True)


if __name__ == "__main__":
    main()

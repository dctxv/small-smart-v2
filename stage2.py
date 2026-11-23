"""Stage 2: free wins on the pilot model. One change at a time, 3 seeds per arm.

  python stage2.py sweep     learning-rate sweeps (single seed, 6,000 story steps)
  python stage2.py arms      baseline and single-change arms
  python stage2.py combo     winners combined (edit COMBO below after reading the arm results)
  python stage2.py report    write results/stage2.md
"""
import json
import os
import sys

from common import ROOT
from pilot import PILOT, SEEDS, at, board, fmt, ms, run_all

SWEEP = ["--cfg", "pilot", "--steps1", "6000", "--steps2", "0"]
ADAM_LRS = ("3e-4", "6e-4", "1.2e-3")
MUON_LRS = ("0.01", "0.02", "0.05")
CHOICE = os.path.join(ROOT, "results", "stage2_lr.json")

ARMS = {  # name -> extra training arguments (the Muon learning rate is filled in from the sweep)
    "base": [],
    "muon": ["--opt", "muon"],
    "qknorm": ["--set", "qk_norm=1"],
    "relu2": ["--set", "relu2=1"],
    "vresid": ["--set", "value_resid=1"],
    "deep": ["--cfg", "deep"],
}
COMBO = {}  # filled in by hand after the arms, e.g. {"combo": ["--set", "qk_norm=1", "relu2=1", "--opt", "muon"]}
if os.path.exists(os.path.join(ROOT, "results", "stage2_combo.json")):
    COMBO = json.load(open(os.path.join(ROOT, "results", "stage2_combo.json")))


def lr_choice():
    return json.load(open(CHOICE)) if os.path.exists(CHOICE) else {"adamw": "6e-4", "muon": "0.02"}


def arm_args(extra):
    c = lr_choice()
    args = PILOT + ["--lr1", c["adamw"]] + list(extra)
    if "--opt" in extra:
        args += ["--muon_lr", c["muon"]]
    if "--cfg" in extra:  # a later --cfg wins in argparse, drop the first
        args = args[2:]
    return args


def sweep():
    jobs = [(f"sw_adam_{lr}", SWEEP + ["--lr1", lr], 6000, False) for lr in ADAM_LRS]
    jobs += [(f"sw_muon_{lr}", SWEEP + ["--opt", "muon", "--muon_lr", lr], 6000, False) for lr in MUON_LRS]
    run_all(jobs)
    res = {n: at(n, "val_story", 6000) for n, *_ in jobs}
    best_a = min(ADAM_LRS, key=lambda lr: res[f"sw_adam_{lr}"])
    best_m = min(MUON_LRS, key=lambda lr: res[f"sw_muon_{lr}"])
    # keep the old 6e-4 unless another value is better by more than the 0.015 yardstick
    if res["sw_adam_6e-4"] - res[f"sw_adam_{best_a}"] <= 0.015:
        best_a = "6e-4"
    json.dump({"adamw": best_a, "muon": best_m, "sweep": res}, open(CHOICE, "w"), indent=1)
    print(json.dumps(res, indent=1), "chosen", best_a, best_m)


def arms(table):
    jobs = [(f"{a}_s{s}", arm_args(x) + ["--seed", str(s)], 7500, True) for a, x in table.items() for s in SEEDS]
    run_all(jobs)
    if table is ARMS:  # assistant-only loss with tight packing: chat phase only, from each baseline
        run_all([(f"asst_s{s}", arm_args([]) + ["--seed", str(s), "--start_from", f"runs/base_s{s}/stories_full.pt",
                                              "--chat_loss", "assistant"], 7500, True) for s in SEEDS])


def report():
    rows = [("base", "baseline", ""), ("base", "weight averaging (same runs)", "_ema"), ("muon", "Muon optimiser", ""),
            ("qknorm", "QK-norm", ""), ("relu2", "ReLU squared", ""), ("vresid", "value residual", ""),
            ("deep", "deep 10 x 208 (base is 6 x 256)", ""), ("asst", "assistant-only loss, tight packing", "")]
    rows += [(k, k, "") for k in COMBO] + [(k, k + ", weight averaging", "_ema") for k in COMBO]
    c = lr_choice()
    L = ["# Stage 2: free wins (pilot model 6.8M, 6,000 story + 1,500 chat steps, 3 seeds per arm)", "",
         f"Learning rates from the single-seed sweep: AdamW {c['adamw']}, Muon {c['muon']}.",
         "Sweep, held-out story loss at step 6,000: " + ", ".join(f"{k} {v:.3f}" for k, v in c.get("sweep", {}).items()),
         "", "Values are mean +- standard deviation over seeds. Lower loss is better. Prompts are out of 100.", "",
         "| arm | story loss at 6,000 | chat loss at end | assistant-only chat loss at end | prompts | vs baseline (story) | vs baseline (assistant chat) |",
         "|---|---|---|---|---|---|---|"]
    base_story, _ = ms([at(f"base_s{s}", "val_story", 6000) for s in SEEDS])
    base_asst, _ = ms([at(f"base_s{s}", "val_chat_asst", 7500) for s in SEEDS])
    out = {}
    for arm, label, sfx in rows:
        story_step = 6000
        st = [at(f"{arm}_s{s}", "val_story" + sfx, story_step) for s in SEEDS]
        if arm == "asst":
            st = [None] * 3
        ch = [at(f"{arm}_s{s}", "val_chat" + sfx, 7500) for s in SEEDS]
        ca = [at(f"{arm}_s{s}", "val_chat_asst" + sfx, 7500) for s in SEEDS]
        bd = [board(f"{arm}_s{s}{sfx}") for s in SEEDS]
        pr = [b["total"] if b else None for b in bd]
        d1 = ms(st)[0] - base_story if ms(st)[0] is not None else None
        d2 = ms(ca)[0] - base_asst if ms(ca)[0] is not None else None
        out[label] = dict(story=st, chat=ch, chat_asst=ca, prompts=pr, d_story=d1, d_asst=d2)
        L.append(f"| {label} | {fmt(st)} | {fmt(ch)} | {fmt(ca)} | {fmt(pr, 1)} | "
                 f"{'-' if d1 is None else f'{d1:+.3f}'} | {'-' if d2 is None else f'{d2:+.3f}'} |")
    with open(os.path.join(ROOT, "results", "stage2.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    json.dump(out, open(os.path.join(ROOT, "results", "stage2.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "sweep":
        sweep()
    elif what == "arms":
        arms(ARMS)
    elif what == "combo":
        arms(COMBO)
    else:
        report()

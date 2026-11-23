"""Stage 3: lookup memory and objectives on the pilot model. One change at a time on top of the
stage 2 winners, 3 seeds per arm.

  python stage3.py arms      run the arms (the baseline is the stage 2 combination, runs combo_s*)
  python stage3.py report    write results/stage3.md
"""
import json
import os
import sys

import torch

from common import ROOT
from pilot import PILOT, SEEDS, at, board, fmt, log_of, ms, run_all
from stage2 import lr_choice

BASE_SET = ["value_resid=1"]          # stage 2 winners: Muon and value residual
BASE_RUN = "combo"
ARMS = {  # name -> (extra model options, extra arguments, label)
    "hash": (["hash_rows=16384"], [], "word-pair hash embedding (16,384 rows)"),
    "valemb": (["val_emb=2"], [], "value embeddings (2 tables)"),
    "mtp": (["mtp=0.3"], [], "multi-token prediction (token after next, weight 0.3)"),
    "ngpt": (["ngpt=1"], [], "approximately normalised transformer"),
    "wide": ([], ["--width", "336"], "wider model, same parameter count as the lookup arms (control)"),
    # stage 2 arms that did nothing at the first learning rate, checked again on top of the winners
    "qk2": (["qk_norm=1"], [], "recheck: QK-norm"),
    "relu2b": (["relu2=1"], [], "recheck: ReLU squared"),
    "deep2": ([], ["--cfg", "deep"], "recheck: deep 10 x 208"),
}


def args_for(sets, extra):
    c = lr_choice()
    return PILOT + ["--lr1", c["adamw"], "--opt", "muon", "--muon_lr", c["muon"], "--set", *BASE_SET, *sets] + list(extra)


def arms(table):
    run_all([(f"{a}_s{s}", args_for(x[0], x[1]) + ["--seed", str(s)], 7500, True) for a, x in table.items() for s in SEEDS])


def params(name):
    p = os.path.join(ROOT, "runs", name, "final.pt")
    if not os.path.exists(p):
        return None
    return sum(v.numel() for v in torch.load(p, map_location="cpu", weights_only=False)["model"].values())


def report(table=ARMS, out="stage3", title="Stage 3: lookup memory and objectives"):
    rows = [(BASE_RUN, "baseline (stage 2 winners: Muon + value residual)")] + [(k, v[2]) for k, v in table.items()]
    L = [f"# {title} (pilot model, 6,000 story + 1,500 chat steps, 3 seeds per arm)", "",
         "Values are mean +- standard deviation over seeds. Lower loss is better. Prompts are out of 100.", "",
         "| arm | parameters | story loss at 6,000 | assistant-only chat loss at end | prompts | vs baseline (story) | vs baseline (assistant chat) | minutes | peak GPU MiB |",
         "|---|---|---|---|---|---|---|---|---|"]
    b_story, _ = ms([at(f"{BASE_RUN}_s{s}", "val_story", 6000) for s in SEEDS])
    b_asst, _ = ms([at(f"{BASE_RUN}_s{s}", "val_chat_asst", 7500) for s in SEEDS])
    res = {}
    for arm, label in rows:
        st = [at(f"{arm}_s{s}", "val_story", 6000) for s in SEEDS]
        ca = [at(f"{arm}_s{s}", "val_chat_asst", 7500) for s in SEEDS]
        pr = [(board(f"{arm}_s{s}") or {}).get("total") for s in SEEDS]
        logs = [log_of(f"{arm}_s{s}") for s in SEEDS]
        mins = [l[-1]["min"] for l in logs if l]
        mem = [max(r.get("mem_alloc_mb", 0) for r in l) for l in logs if l]
        d1 = None if ms(st)[0] is None else ms(st)[0] - b_story
        d2 = None if ms(ca)[0] is None else ms(ca)[0] - b_asst
        res[arm] = dict(label=label, story=st, chat_asst=ca, prompts=pr, d_story=d1, d_asst=d2, params=params(f"{arm}_s0"))
        L.append(f"| {label} | {res[arm]['params'] or 0:,} | {fmt(st)} | {fmt(ca)} | {fmt(pr, 1)} | "
                 f"{'-' if d1 is None else f'{d1:+.3f}'} | {'-' if d2 is None else f'{d2:+.3f}'} | "
                 f"{ms(mins)[0] or 0:.0f} | {max(mem) if mem else 0:.0f} |")
    with open(os.path.join(ROOT, "results", out + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    json.dump(res, open(os.path.join(ROOT, "results", out + ".json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    arms(ARMS) if sys.argv[1] == "arms" else report()

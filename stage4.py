"""Stage 4 student runs on the pilot: chat phase only (4,000 steps) from the stage 2 combination's story checkpoints.

  python stage4.py run <tag> <mix.json> [assistant]    3 seeds, then scoreboard and dev set
  python stage4.py report <tag> <tag> ...
"""
import json
import os
import subprocess
import sys

from common import ROOT
from pilot import SEEDS, at, board, fmt, ms, run_all
from stage3 import args_for

STEPS2 = "4000"


def run(tag, mix, loss="all"):
    base = [a if a != "1500" else STEPS2 for a in args_for([], [])]
    jobs = []
    for s in SEEDS:
        args = base + ["--seed", str(s), "--start_from", f"runs/combo_s{s}/stories_full.pt", "--chat_loss", loss]
        if mix != "default":
            args += ["--chat_mix", mix]
        jobs.append((f"{tag}_s{s}", args, 10000, True))
    run_all(jobs)
    for s in SEEDS:
        if not os.path.exists(os.path.join(ROOT, "results", "dev", f"dev_{tag}_s{s}.json")):
            subprocess.run([sys.executable, "devset.py", "score", f"runs/{tag}_s{s}/final.pt", "--name", f"{tag}_s{s}"],
                           cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def dev(name):
    p = os.path.join(ROOT, "results", "dev", f"dev_{name}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def report(tags):
    groups = ["instruction", "arithmetic", "format", "notes", "tool_call"]
    L = ["| run | assistant chat loss | scoreboard /100 | " + " | ".join(groups) + " | dev set /362 |", "|---|" + "---|" * (len(groups) + 3)]
    for t in tags:
        bd = [board(f"{t}_s{s}") for s in SEEDS]
        dv = [dev(f"{t}_s{s}") for s in SEEDS]
        L.append(f"| {t} | {fmt([at(f'{t}_s{s}', 'val_chat_asst', 10000) for s in SEEDS])} | {fmt([b and b['total'] for b in bd], 1)} | "
                 + " | ".join(f"{ms([b and b['groups'][g] for b in bd])[0] or 0:.1f}" for g in groups)
                 + f" | {fmt([d and d['total'] for d in dv], 1)} |")
    fams = list(dev(f"{tags[0]}_s0")["rates"]) if dev(f"{tags[0]}_s0") else []
    L += ["", "Dev set pass rate per family (mean of 3 seeds):", "", "| family | " + " | ".join(tags) + " |", "|---|" + "---|" * len(tags)]
    for f in fams:
        L.append(f"| {f} | " + " | ".join(f"{ms([(dev(f'{t}_s{s}') or {'rates': {}})['rates'].get(f) for s in SEEDS])[0] or 0:.2f}" for t in tags) + " |")
    print("\n".join(L))
    return "\n".join(L)


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "all")
    else:
        report(sys.argv[2:])

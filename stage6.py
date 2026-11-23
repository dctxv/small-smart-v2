"""Stage 6: fewer bits. Quantisation-aware training on the pilot, compared at equal megabytes.

The yardstick is the stage 2 combination stored as 16-bit floats (6.8M parameters, about 13.6 MB).
An 8-bit model may have about twice the parameters in the same file, a 4-bit model about four times.

  python stage6.py arms      run the arms (3 seeds each)
  python stage6.py report    export real files, write results/stage6.md
"""
import json
import os
import sys

import torch

from common import ROOT
from pilot import SEEDS, at, board, fmt, log_of, ms
from stage3 import BASE_RUN, arms, params

ARMS = {  # name -> (model options, extra arguments, label, bits)
    "q8same": (["qbits=8"], [], "8-bit, same shape as the baseline", 8),
    "q4same": (["qbits=4"], [], "4-bit, same shape as the baseline", 4),
    "q8big": (["qbits=8"], ["--width", "384"], "8-bit, width 384 (equal megabytes)", 8),
    "q4big": (["qbits=4"], ["--width", "560"], "4-bit, width 560 (equal megabytes)", 4),
}


def size_mb(name, bits):
    """Real file size. 16-bit float for the baseline, the packed export for the others."""
    src = os.path.join(ROOT, "runs", name, "final.pt")
    if not os.path.exists(src):
        return None
    if bits == 16:
        sd = torch.load(src, map_location="cpu", weights_only=False)["model"]
        return sum(v.numel() for v in sd.values()) * 2 / 1e6
    import quant
    dst = os.path.join(ROOT, "runs", name, f"q{bits}.bin")
    if not os.path.exists(dst):
        quant.export(src, bits, dst)
    return os.path.getsize(dst) / 1e6


def report():
    rows = [(BASE_RUN, "baseline, 16-bit floats", 16)] + [(k, v[2], v[3]) for k, v in ARMS.items()]
    L = ["# Stage 6: fewer bits (pilot model, 6,000 story + 1,500 chat steps, 3 seeds per arm)", "",
         "Losses are measured with the weights already rounded to the low-bit grid, so they are the losses of the file that ships.", "",
         "| arm | parameters | file MB | story loss at 6,000 | assistant chat loss at end | prompts /100 | vs baseline (story) | minutes | peak GPU MiB |",
         "|---|---|---|---|---|---|---|---|---|"]
    b_story, _ = ms([at(f"{BASE_RUN}_s{s}", "val_story", 6000) for s in SEEDS])
    res = {}
    for arm, label, bits in rows:
        st = [at(f"{arm}_s{s}", "val_story", 6000) for s in SEEDS]
        ca = [at(f"{arm}_s{s}", "val_chat_asst", 7500) for s in SEEDS]
        pr = [(board(f"{arm}_s{s}") or {}).get("total") for s in SEEDS]
        logs = [log_of(f"{arm}_s{s}") for s in SEEDS]
        mins = [l[-1]["min"] for l in logs if l]
        mem = [max(r.get("mem_alloc_mb", 0) for r in l) for l in logs if l]
        d1 = None if ms(st)[0] is None else ms(st)[0] - b_story
        mb = size_mb(f"{arm}_s0", bits)
        res[arm] = dict(label=label, story=st, chat_asst=ca, prompts=pr, d_story=d1, params=params(f"{arm}_s0"), mb=mb)
        L.append(f"| {label} | {res[arm]['params'] or 0:,} | {mb or 0:.1f} | {fmt(st)} | {fmt(ca)} | {fmt(pr, 1)} | "
                 f"{'-' if d1 is None else f'{d1:+.3f}'} | {ms(mins)[0] or 0:.0f} | {max(mem) if mem else 0:.0f} |")
    with open(os.path.join(ROOT, "results", "stage6.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    json.dump(res, open(os.path.join(ROOT, "results", "stage6.json"), "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    arms({k: v[:3] for k, v in ARMS.items()}) if sys.argv[1] == "arms" else report()

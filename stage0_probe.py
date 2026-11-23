"""Stage 0: batch search over shapes. Runs probe.py in a fresh process per setting.

  python stage0_probe.py
"""
import json
import os
import subprocess
import sys

from common import ROOT

SHAPES = [("40M (twin shape)", 12, 512), ("70M wide", 12, 672), ("70M deep", 21, 512),
          ("100M wide", 12, 800), ("100M deep", 30, 512)]
MICROS = [64, 48, 32, 24, 16]

if __name__ == "__main__":
    path = os.path.join(ROOT, "results", "stage0_probe.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    done = set()
    if os.path.exists(path):
        done = {(r["layers"], r["width"], r["micro"]) for r in map(json.loads, open(path))}
    for label, L, W in SHAPES:
        for m in MICROS:
            if (L, W, m) in done:
                continue
            p = subprocess.run([sys.executable, "probe.py", "--layers", str(L), "--width", str(W), "--micro", str(m)],
                               cwd=ROOT, capture_output=True, text=True, timeout=1800)
            line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
            r = json.loads(line[-1][7:]) if line else dict(layers=L, width=W, micro=m, ok=False,
                                                          error=p.stderr[-300:])
            r["label"] = label
            with open(path, "a") as f:
                f.write(json.dumps(r) + "\n")
            print(r, flush=True)

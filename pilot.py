"""Helpers for pilot experiments: run jobs a few at a time, read results, make tables."""
import json
import os
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from common import ROOT, read_log

PILOT = ["--cfg", "pilot", "--steps1", "6000", "--steps2", "1500"]
SEEDS = (0, 1, 2)


def log_of(name):
    return read_log(os.path.join(ROOT, "runs", name, "log.jsonl"))


def last_step(name):
    log = log_of(name)
    return log[-1]["step"] if log else -1


def at(name, key, step):
    for r in log_of(name):
        if r["step"] == step and key in r:
            return r[key]
    return None


def train_job(name, args, end_step, score=True):
    """Train (resume-safe), then score final.pt on the scoreboard."""
    out = os.path.join(ROOT, "logs", f"{name}.log")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "a") as f:
        if last_step(name) < end_step:
            subprocess.run([sys.executable, "train.py", "--name", name, *args], cwd=ROOT, stdout=f,
                           stderr=subprocess.STDOUT, check=True)
        if score:
            for which in ("final", "final_ema"):
                tag = name if which == "final" else name + "_ema"
                if not os.path.exists(os.path.join(ROOT, "results", "pilot", f"scoreboard_{tag}.json")):
                    subprocess.run([sys.executable, "scoreboard.py", f"runs/{name}/{which}.pt", "--name", tag,
                                    "--out_dir", "results/pilot"], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                                   check=True)
    return name


def run_all(jobs, workers=3):
    """jobs: list of (name, args, end_step, score)."""
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(train_job, *j) for j in jobs]
        for f in futs:
            print("done", f.result(), flush=True)


def board(tag):
    p = os.path.join(ROOT, "results", "pilot", f"scoreboard_{tag}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def ms(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)


def fmt(vals, nd=3):
    m, s = ms(vals)
    if m is None:
        return "-"
    return f"{m:.{nd}f} +- {s:.{nd}f} (n={len([v for v in vals if v is not None])})"

"""Tokenise a jsonl file of conversations into data/tok/<name>_train.bin and <name>_val.bin.

  python tok_job.py data/raw/job/job.jsonl job

Each line needs a "messages" list. Conversations longer than --max_tokens are dropped.
"""
import argparse
import json
import random

import numpy as np

from common import format_chat, load_tokenizer
from prepare_data import write_bin

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("name")
    ap.add_argument("--max_tokens", type=int, default=250)
    ap.add_argument("--val", type=int, default=1000)
    a = ap.parse_args()
    convs = [json.loads(l)["messages"] for l in open(a.path, encoding="utf-8") if l.strip()]
    random.Random(0).shuffle(convs)
    tok = load_tokenizer()
    arrays = []
    for s in range(0, len(convs), 20000):
        arrays += [np.array(e.ids, dtype=np.uint16) for e in tok.encode_batch([format_chat(c) for c in convs[s:s + 20000]])]
    kept = [x for x in arrays if len(x) <= a.max_tokens]
    print(f"{len(convs)} conversations, {len(arrays) - len(kept)} dropped for length, "
          f"mean {np.mean([len(x) for x in kept]):.0f} tokens")
    n_val = min(a.val, len(kept) // 20)
    write_bin(a.name, "val", kept[:n_val])
    write_bin(a.name, "train", kept[n_val:])

"""Stage 5: tools. A held-out tool test with the full loop: the model writes a call, the tool runs,
the result goes back, the model answers. Compared with and without grammar constrained output.

  python stage5.py build                      writes data/toolset.json (fixed seed)
  python stage5.py score <tag> [<tag> ...]    3 seeds per tag -> results/tools/<tag>_s*.json
  python stage5.py report <tag> [<tag> ...]   table, also written to results/stage5.md
"""
import json
import os
import random
import sys

import gen_job as G
from devset import content_words
from gen_job import R, cap, pick

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "toolset.json")
SEEDS = [0, 1, 2]

OFF_CALC = [("How much is {a} and {b} together?", "+"), ("{a} multiplied by {b} please.", "*"), ("Can you work out {a} take away {b}?", "-"),
            ("I need the answer to {a} * {b}.", "*"), ("Please add {a} to {b} for me.", "+"), ("What do you get if you split {p} into {b} equal parts?", "/"),
            ("My class has {b} children and each one needs {a} sheets of paper. How many sheets is that?", "*"),
            ("I had {a} coins and I spent {b}. How many coins are left?", "-"), ("Tell me {a} + {b}.", "+"), ("What is the sum of {a} and {b}?", "+")]
OFF_NOTES = ["Can you find in my notes {q}", "I wrote this down somewhere. {Q}", "Have a look at my notes and tell me {q}",
             "My notes will know this. {Q}", "Please search the notes for me. {Q}"]


def build(seed=4242):
    R.seed(seed)
    items, seen = [], set()
    for f in ("job.jsonl", "job1.jsonl"):  # calculator requests that are in the training data are not used
        p = os.path.join(HERE, "data", "raw", "job", f)
        if os.path.exists(p):
            seen |= {json.loads(l)["messages"][0]["content"] for l in open(p, encoding="utf-8")}
    while sum(i["family"] == "calc" for i in items) < 40:
        c = G.gen_calc()["messages"]
        v = float(c[2]["content"].split(":")[1])
        if c[0]["content"] not in seen and not any(i["prompt"] == c[0]["content"] for i in items):
            items.append(dict(family="calc", prompt=c[0]["content"], tool="calc", value=v, notes=[]))
    for i in range(30):
        t, op = OFF_CALC[i % len(OFF_CALC)]
        a, b = R.randint(120, 9000), R.randint(13, 99)
        v = {"+": a + b, "-": a - b, "*": a * b, "/": a}[op]
        items.append(dict(family="calc_new_wording", prompt=t.format(a=a, b=b, p=a * b), tool="calc", value=float(v), notes=[]))
    for fam, n in (("notes", 40), ("notes_new_wording", 20)):
        for _ in range(n):
            notes = G.note_set(8)
            note, qas, key = pick(notes)
            q, ans, word = pick(qas)
            ask = pick(G.ASK_TOOL if fam == "notes" else OFF_NOTES).format(q=q, Q=cap(q))
            items.append(dict(family=fam, prompt=ask, tool="notes", keys=[word.lower()], all=content_words(ans, q), notes=[x[0] for x in notes]))
    return items


def score_model(model, tok, vocab, items):
    """Full tool loop on every item, free and constrained. Returns {mode: rows}."""
    from scoreboard import calc, has, numbers, parse_tool_call
    from tools import answer
    out = {}
    for mode in ("free", "constrained"):
        rows = []
        for it in items:
            final, added = answer(model, tok, vocab, [("user", it["prompt"])], notes=it["notes"], constrained=mode == "constrained")
            first = added[0][1]
            obj = parse_tool_call(first)
            valid = obj is not None
            right = False
            if valid and obj["tool"] == it["tool"]:
                if it["tool"] == "calc":
                    try:
                        right = abs(calc(obj["input"]) - it["value"]) < 1e-6
                    except Exception:
                        right = False
                else:
                    right = any(k in obj["input"].lower() for k in it["keys"])
            if it["tool"] == "calc":
                good = len(added) > 1 and it["value"] in numbers(final)
            else:
                good = len(added) > 1 and all(has(final, w) for w in it["all"])
            draft = valid and len([l for l in first.splitlines() if l.strip()]) > 1
            rows.append(dict(family=it["family"], prompt=it["prompt"], first=first, final=final, valid=valid, right=right, good=bool(good), draft=draft))
        out[mode] = rows
    return out


def score(tag):
    import torch
    from chat import load_model
    from common import ROOT, load_tokenizer, setup_torch
    from scoreboard import calc, has, numbers, parse_tool_call
    from tools import Vocab, answer
    setup_torch(0)
    tok = load_tokenizer()
    vocab = Vocab(tok)
    items = json.load(open(PATH, encoding="utf-8"))
    os.makedirs(os.path.join(ROOT, "results", "tools"), exist_ok=True)
    for s in SEEDS:
        model = load_model(f"runs/{tag}_s{s}/final.pt")
        out = score_model(model, tok, vocab, items)
        json.dump(out, open(os.path.join(ROOT, "results", "tools", f"{tag}_s{s}.json"), "w", encoding="utf-8"), indent=1)
        print(tag, s, {m: sum(r["good"] for r in out[m]) for m in out}, "of", len(items), flush=True)
        del model
        torch.cuda.empty_cache()


def report(tags):
    from pilot import fmt
    fams = ["calc", "calc_new_wording", "notes", "notes_new_wording"]
    L = ["Tool test: 130 held-out requests, full loop (call, tool runs, result, final answer). Mean +- standard deviation over 3 seeds, in percent.", "",
         "| run | output | valid call | right call | right final answer | " + " | ".join(f + " (final)" for f in fams) + " | wrote a draft line |",
         "|---|---|---|---|---|" + "---|" * (len(fams) + 1)]
    for t in tags:
        data = [json.load(open(os.path.join(HERE, "results", "tools", f"{t}_s{s}.json"), encoding="utf-8")) for s in SEEDS]
        for mode in ("free", "constrained"):
            def pct(key, fam=None):
                v = []
                for d in data:
                    rows = [r for r in d[mode] if fam is None or r["family"] == fam]
                    v.append(100 * sum(r[key] for r in rows) / len(rows))
                return fmt(v, 1)
            L.append(f"| {t} | {mode} | {pct('valid')} | {pct('right')} | {pct('good')} | " + " | ".join(pct("good", f) for f in fams) + f" | {pct('draft')} |")
    print("\n".join(L))
    return "\n".join(L)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        d = build()
        json.dump(d, open(PATH, "w", encoding="utf-8"), indent=1)
        print("wrote", len(d), "tool test requests")
    elif sys.argv[1] == "score":
        for t in sys.argv[2:]:
            score(t)
    else:
        txt = report(sys.argv[2:])
        open(os.path.join(HERE, "results", "stage5.md"), "a", encoding="utf-8").write(txt + "\n\n")

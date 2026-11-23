"""A development set for the fail-finding loop (stage 4). It is NOT the scoreboard.

  python devset.py                      writes data/devset.json (fixed seed, 20 prompts per family)
  python devset.py score runs/x/final.pt --name x     pass rate per family -> results/dev/dev_<name>.json

The prompts come from the same families as the programmatic job data but with their own seed,
and they are removed from the training data (gen_job.py --exclude). They never touch the scoreboard
prompts. Checks use the same checker as the scoreboard.
"""
import json
import os
import re
import sys

import gen_job as G
from gen_job import NUMW, R, cap, pick

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "devset.json")
STOP = set("the a an is are on at in to of you your it its should has have need list was do does i my by with "
           "and for that this there going".split())


def content_words(ans, q):
    qw = set(re.findall(r"[a-z0-9:']+", q.lower()))
    return [w for w in re.findall(r"[a-z0-9:']+", ans.lower()) if w not in qw and w not in STOP]


def f_one_word():
    if R.random() < 0.5:
        a, b = pick(G.OPPOSITES)
        return f"What is the opposite of {a}? Answer with one word.", {"words": 1, "any": [b]}
    q, a = pick(G.ONEWORD)
    return f"Answer with one word: {q}?", {"words": 1, "any": [a.lower()]}


def f_yes_no():
    q, a = pick(G.YESNO)
    return f"Answer only yes or no: {q}?", {"words": 1, "first_word": "yes" if a else "no"}


def f_repeat_word():
    w, n = pick(G.WORDS + G.ANIMALS), R.randint(2, 5)
    return f"Say the word {w} {NUMW[n]} times.", {"words": n, "count": [w, n]}


def f_exact_words():
    n = R.randint(2, 7)
    return pick([f"Reply with exactly {NUMW[n]} words.", f"Answer in exactly {NUMW[n]} words.",
                 f"Say something with exactly {NUMW[n]} words.", f"Tell me about {G.general(pick(G.ANIMALS))} in exactly {NUMW[n]} words."]), {"words": n}


def f_start_end():
    t = G.general(pick(G.ANIMALS))
    if R.random() < 0.5:
        w = pick(["Sure", "Yes", "Okay", "Well", "Today", "Hello"])
        return f"Tell me about {t}. Start your reply with the word {w}.", {"first_word": w.lower(), "max_words": 40}
    w = pick(["goodbye", "thanks", "please", "hooray", "yes", "now", "today", "friend"])
    return f"Tell me about {t} and end with the word {w}.", {"last_word": w, "max_words": 40}


def f_one_sentence():
    t = G.general(pick(G.TOPICS))
    return pick([f"Write one sentence about {t}.", f"Tell me about {t} in one sentence."]), {"sentences": 1, "max_words": 30}


def f_copy():
    s = G.sentence()
    return pick([f"Repeat this exactly: {s}", f"Say this back to me exactly: {s}"]), {"exact": s}


def f_sum():
    q, a = G.direct_problem()
    while "How many" in q:
        q, a = G.direct_problem()
    return q, {"number": int(re.findall(r"-?\d+", a)[-1]), "max_words": 15}


def f_word_problem():
    q, a = G.word_problem()
    return q, {"number": int(re.findall(r"-?\d+", a)[-1]), "max_words": 25}


def f_numbered():
    cat = pick(list(G.CATS)); n = R.randint(2, min(6, len(G.CATS[cat])))
    return f"List {NUMW[n]} {cat} as a numbered list.", {"numbered": n}


def f_dashed():
    cat = pick(list(G.CATS)); n = R.randint(2, min(5, len(G.CATS[cat])))
    return f"List {NUMW[n]} {cat}. Put a dash at the start of each line.", {"dashed": n}


def f_capitals():
    w = pick(G.WORDS + G.ANIMALS)
    return f"Write the word {w} in capital letters.", {"has_exact": w.upper(), "max_words": 3}


def f_lines():
    n = R.randint(2, 4)
    return f"Write exactly {NUMW[n]} lines. Each line is one short sentence.", {"lines": n}


def f_number_only():
    c = G.gen_format.__globals__  # reuse the question list by sampling the generator
    while True:
        conv = G.gen_format()
        u, a = conv["messages"][0]["content"], conv["messages"][1]["content"]
        if "number" in u and a.isdigit():
            return u, {"exact": a}


def f_range():
    a = R.randint(1, 20); b = a + R.randint(2, 7)
    return f"Write the numbers from {a} to {b} with commas between them.", {"squashed": ",".join(str(i) for i in range(a, b + 1))}


def f_notes(missing=False):
    notes = G.note_set(R.randint(2, 5))
    block = "Notes:\n" + "\n".join("- " + n[0] for n in notes) + "\n\n"
    if missing:
        other = G.make_note()
        while any(other[2] == n[2] for n in notes):
            other = G.make_note()
        q = pick(other[1])[0]
        return block + cap(q), {"any": ["not", "cannot", "no", "nothing"], "max_words": 25}
    q, ans, _ = pick(pick(notes)[1])
    return block + cap(q), {"all": content_words(ans, q), "max_words": 25}


def f_notes_missing():
    return f_notes(True)


def f_tool_calc():
    c = G.gen_calc()["messages"]
    return c[0]["content"], {"tool": "calc", "value": float(c[2]["content"].split(":")[1])}


def f_tool_notes():
    c = G.gen_notes_tool()["messages"]
    return c[0]["content"], {"tool": "notes", "keys": [json.loads(c[1]["content"].splitlines()[-1])["input"].lower()]}


FAMILIES = dict(one_word=f_one_word, yes_no=f_yes_no, repeat_word=f_repeat_word, exact_words=f_exact_words,
                start_end=f_start_end, one_sentence=f_one_sentence, copy=f_copy, sum=f_sum, word_problem=f_word_problem,
                numbered=f_numbered, dashed=f_dashed, capitals=f_capitals, lines=f_lines, number_only=f_number_only,
                range=f_range, notes=f_notes, notes_missing=f_notes_missing, tool_calc=f_tool_calc,
                tool_notes=f_tool_notes)


def build(per=20, seed=777):
    R.seed(seed)
    out, seen = [], set()
    for fam, fn in FAMILIES.items():
        n = tries = 0
        while n < per and tries < 3000:  # some families have fewer than 20 different prompts
            tries += 1
            p, c = fn()
            if p in seen or not G.allowed({"messages": [{"role": "user", "content": p}]}):
                continue
            seen.add(p); out.append(dict(family=fam, prompt=p, check=c)); n += 1
    return out


def load():
    return json.load(open(PATH, encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        d = build()
        json.dump(d, open(PATH, "w", encoding="utf-8"), indent=1)
        print("wrote", len(d), "dev prompts in", len(FAMILIES), "families")
    else:
        import torch
        from chat import load_model
        from common import ROOT, load_tokenizer, setup_torch
        from scoreboard import check_reply, greedy_reply
        setup_torch(0)
        model, tok = load_model(sys.argv[2]), load_tokenizer()
        name = sys.argv[sys.argv.index("--name") + 1]
        res, items = {}, []
        for it in load():
            reply = greedy_reply(model, tok, it["prompt"])
            ok = check_reply(it["prompt"], reply, it["check"])
            res.setdefault(it["family"], []).append(ok)
            items.append(dict(it, reply=reply, passed=ok))
        rates = {k: sum(v) / len(v) for k, v in res.items()}
        os.makedirs(os.path.join(ROOT, "results", "dev"), exist_ok=True)
        json.dump(dict(name=name, rates=rates, total=sum(sum(v) for v in res.values()), n=len(items), items=items),
                  open(os.path.join(ROOT, "results", "dev", f"dev_{name}.json"), "w", encoding="utf-8"), indent=1)
        print(json.dumps(rates, indent=1), "total", sum(sum(v) for v in res.values()), "of", len(items))

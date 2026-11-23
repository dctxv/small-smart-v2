"""Stage 9: score models on the frozen held-out test (data/heldout.json, see make_heldout.py).

  python heldout.py leak                      look for the held-out prompts in the practice data
  python heldout.py score <name> <model>      -> results/heldout/heldout_<name>.json
  python heldout.py report <name> ...         tables + results/heldout/human_sheet.md

Every prompt goes through the full tool loop (free output, no grammar): if the model writes a tool
call, the tool runs on the item's notes and the model answers again. The check is on the final reply.
The scorer refuses to run if the file does not match data/heldout.sha256.
"""
import glob
import hashlib
import json
import os
import re
import sys

from scoreboard import check_reply, has, numbers, parse_tool_call

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "heldout.json")
HASH = os.path.join(HERE, "data", "heldout.sha256")
OUT = os.path.join(HERE, "results", "heldout")
ADMIT = re.compile(r"\b(do not know|don't know|not know|not sure|cannot|can't|could not|couldn't|no note|no notes|not in (your|the|my) notes|"
                   r"nothing|unable|no way|do not have|don't have|no idea|did not find|didn't find|do not say|does not say|not say|"
                   r"there is no|there are no|not found|no one knows|nobody knows|impossible)\b", re.I)
SECTIONS = {"A": "five skills, new wording", "B": "notes questions without the word notes", "C": "two skills in one request",
            "D": "questions with no answer", "E": "world knowledge (reported apart)"}
OWN = ("num", "num_in", "admit", "re", "re_case", "want_call")


def hcheck(item, final):
    c, r = item["check"], final.strip()
    if not r:
        return False
    ok = check_reply(item["prompt"], r, {k: v for k, v in c.items() if k not in OWN}) if any(k not in OWN for k in c) else True
    if "num" in c:  # the answer is there, and no number that is neither the answer nor from the prompt
        ok &= float(c["num"]) in numbers(r) and not (numbers(r) - numbers(item["prompt"]) - {float(c["num"])})
    if "num_in" in c:
        ok &= float(c["num_in"]) in numbers(r)
    if "admit" in c:
        ok &= ADMIT.search(r.replace("’", "'")) is not None
    if "re" in c:
        ok &= re.search(c["re"], r, 0 if c.get("re_case") else re.I) is not None
    return bool(ok)


def load():
    blob = open(PATH, "rb").read()
    want = open(HASH).read().strip()
    got = hashlib.sha256(blob).hexdigest()
    if got != want:
        sys.exit(f"data/heldout.json does not match its hash.\n  file  {got}\n  saved {want}")
    return json.loads(blob.decode("utf-8")), got


def score(name, path):
    import torch
    from chat import load_model
    from common import load_tokenizer, setup_torch
    from tools import Vocab, answer
    items, h = load()
    setup_torch(0)
    tok = load_tokenizer()
    vocab = Vocab(tok)
    model = load_model(path)
    torch.cuda.reset_peak_memory_stats()
    rows = []
    for it in items:
        final, added = answer(model, tok, vocab, [("user", it["prompt"])], notes=it["notes"], constrained=False)
        first = added[0][1]
        obj = parse_tool_call(first)
        rows.append(dict(id=it["id"], section=it["section"], skill=it["skill"], prompt=it["prompt"], first=first, final=final,
                         called=obj["tool"] if obj else None, passed=hcheck(it, final)))
    peak = torch.cuda.max_memory_allocated() / 2 ** 20
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(name=name, model=path, sha256=h, peak_gpu_mib=round(peak), rows=rows),
              open(os.path.join(OUT, f"heldout_{name}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(name, {s: f"{sum(r['passed'] for r in rows if r['section'] == s)}/{sum(r['section'] == s for r in rows)}" for s in SECTIONS},
          "peak MiB", round(peak), flush=True)


def norm(t):
    return " ".join(re.findall(r"[a-z0-9']+", t.lower()))


def mask(t):
    return re.sub(r"\d+", "#", norm(t))


def user_texts():
    """Every user message in every chat source that any of the five models could have seen."""
    raw = os.path.join(HERE, "data", "raw")
    for f in sorted(glob.glob(os.path.join(raw, "job", "*.jsonl")) + glob.glob(os.path.join(raw, "teacher", "*.jsonl"))
                    + glob.glob(os.path.join(raw, "synth", "*.jsonl"))):
        src = os.path.relpath(f, raw)
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                for m in json.loads(line)["messages"]:
                    if m["role"] == "user" and not m["content"].startswith("Result:"):
                        yield src, m["content"]
    import prepare_data as P
    for name in ("tinychat", "smol", "everyday", "storyreq"):
        for conv in P.CHAT_SOURCES[name]():
            for m in conv:
                if m["role"] == "user":
                    yield name, m["content"]


def leak():
    items, h = load()
    # the question part is the last line of a prompt (notes blocks come before it)
    q = {it["id"]: it["prompt"].strip().splitlines()[-1] for it in items}
    full = {norm(it["prompt"]): it["id"] for it in items}
    qm = {i: mask(t) for i, t in q.items()}
    qset = {i: set(m.split()) for i, m in qm.items()}
    exact, same_q, best = {}, {}, {i: (0.0, "", "") for i in q}
    seen, n = set(), 0
    for src, text in user_texts():
        n += 1
        if norm(text) in full:
            exact.setdefault(full[norm(text)], src)
        last = mask(text.strip().splitlines()[-1]) if text.strip() else ""
        if not last or last in seen:
            continue
        seen.add(last)
        ws = set(last.split())
        for i, m in qm.items():
            if m == last:
                same_q.setdefault(i, (src, text.strip().splitlines()[-1]))
            j = len(ws & qset[i]) / len(ws | qset[i])
            if j > best[i][0]:
                best[i] = (j, src, text.strip().splitlines()[-1])
    near = sorted(((j, i, src, t) for i, (j, src, t) in best.items()), reverse=True)
    out = dict(sha256=h, user_messages=n, different_question_lines=len(seen), exact=exact,
               same_question_line={i: dict(source=s, text=t) for i, (s, t) in same_q.items()},
               nearest=[dict(id=i, overlap=round(j, 2), prompt=q[i], source=src, nearest=t) for j, i, src, t in near])
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "leak_check.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("user messages read:", n, " different question lines:", len(seen))
    print("whole prompt found in practice data:", exact or "none")
    print("question line found in practice data (numbers masked):", len(same_q))
    for i, (s, t) in same_q.items():
        print("  ", i, "|", q[i], "|", s)
    print("closest by shared words (top 15):")
    for j, i, src, t in near[:15]:
        print(f"   {j:.2f} {i} | {q[i]} | {src}: {t[:90]}")


def report(names):
    items, h = load()
    data = {n: json.load(open(os.path.join(OUT, f"heldout_{n}.json"), encoding="utf-8")) for n in names}
    for n, d in data.items():
        assert d["sha256"] == h, n
    L = [f"Held-out test, sha256 {h}", "", "| part | items | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]

    def line(label, keep):
        ids = [it["id"] for it in items if keep(it)]
        L.append(f"| {label} | {len(ids)} | " + " | ".join(str(sum(r["passed"] for r in data[n]["rows"] if r["id"] in ids)) for n in names) + " |")
    lk = json.load(open(os.path.join(OUT, "leak_check.json"), encoding="utf-8"))
    flagged = {x["id"] for x in lk["nearest"] if x["overlap"] >= 0.85} | set(lk["exact"]) | set(lk["same_question_line"])
    line("**A to D, headline**", lambda it: it["section"] in "ABCD")
    line("**A to D, without the items found in the practice data**", lambda it: it["section"] in "ABCD" and it["id"] not in flagged)
    line("E, without the items found in the practice data", lambda it: it["section"] == "E" and it["id"] not in flagged)
    for s, lab in SECTIONS.items():
        line(f"{s}: {lab}", lambda it, s=s: it["section"] == s)
        for sk in dict.fromkeys(it["skill"] for it in items if it["section"] == s):
            if sum(it["section"] == s for it in items) != sum(it["section"] == s and it["skill"] == sk for it in items):
                line(f"- {sk}", lambda it, s=s, sk=sk: it["section"] == s and it["skill"] == sk)
    L += ["", "Tool use on part B store items (the fact is only in the notes store): how many times the model searched the notes",
          "", "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    ids = [it["id"] for it in items if it["section"] == "B" and it["skill"] == "store"]
    L.append("| searched, of 15 | " + " | ".join(str(sum(r["called"] == "notes" for r in data[n]["rows"] if r["id"] in ids)) for n in names) + " |")
    L += ["", "Peak GPU memory while scoring: " + ", ".join(f"{n} {data[n]['peak_gpu_mib']} MiB" for n in names)]
    txt = "\n".join(L)
    print(txt)
    open(os.path.join(OUT, "report.md"), "w", encoding="utf-8").write(txt + "\n")
    # the sheet for grading by hand
    S = ["# Held-out test: items for you to grade by hand", "",
         "Part 1: the automatic check only sees the form of these replies. Please judge the sense. Write y or n in the last column.", ""]
    byid = {n: {r["id"]: r for r in d["rows"]} for n, d in data.items()}
    for it in items:
        if "human" not in it:
            continue
        S += [f"## {it['id']}  {it['prompt']}", f"Judge: {it['human']}", "", "| model | reply | form check | your grade |", "|---|---|---|---|"]
        for n in names:
            r = byid[n][it["id"]]
            S.append(f"| {n} | {r['final'].replace(chr(10), ' / ')} | {'pass' if r['passed'] else 'fail'} | |")
        S.append("")
    S += ["", "Part 2: questions with no answer where the automatic check found no \"I do not know\" wording.",
          "Most of these are made-up answers. Mark y only if the reply is in fact an honest \"I do not know\".", ""]
    for it in items:
        if it["section"] != "D":
            continue
        bad = [n for n in names if not byid[n][it["id"]]["passed"]]
        if bad:
            S += [f"## {it['id']}  {it['prompt']}", "", "| model | reply | your grade |", "|---|---|---|"]
            S += [f"| {n} | {byid[n][it['id']]['final'].replace(chr(10), ' / ')} | |" for n in bad] + [""]
    open(os.path.join(OUT, "human_sheet.md"), "w", encoding="utf-8").write("\n".join(S) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "leak":
        leak()
    elif sys.argv[1] == "score":
        score(sys.argv[2], sys.argv[3])
    else:
        report(sys.argv[2:])

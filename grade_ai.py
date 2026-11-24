"""AI grading of the items the held-out tests mark for grading by hand.

  python grade_ai.py prep      write results/ai_grading/items_<set>.json (replies without model names)
  python grade_ai.py merge     read pass1_<set>.json and pass2_<set>.json, write grades and adjusted scores

The rubric is results/ai_grading/RUBRIC.md. Two graders work from it separately. Where they
differ the reply is "unclear" and counts as wrong. These grades are by AI, not by a person.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "ai_grading")
SETS = {"heldout": "data/heldout.json", "heldout2": "data/heldout2.json"}
NAMES = ["twin", "twinctl", "ss8", "ss4", "rival8", "v2_ctl", "v2_q4"]
NO_ANSWER_Q = "Is the reply an honest statement that it does not know, with no made-up answer?"


def load(s):
    items = json.load(open(os.path.join(HERE, SETS[s]), encoding="utf-8"))
    res = {}
    for n in NAMES:
        p = os.path.join(HERE, "results", s, f"heldout_{n}.json")
        if os.path.exists(p):
            res[n] = {r["id"]: r for r in json.load(open(p, encoding="utf-8"))["rows"]}
    return items, res


def rid(item_id, reply):
    return item_id + "-" + hashlib.sha256(reply.encode("utf-8")).hexdigest()[:6]


def to_grade(items, res):
    """item id -> (type, item, {reply id: reply}, {model: reply id})."""
    out = {}
    for it in items:
        if "human" in it:
            typ, want = "S", True   # sense check on replies that passed the form check
        elif it["section"] == "D" and "admit" in it["check"]:
            typ, want = "N", False  # no-answer question where no admission was found
        else:
            continue
        reps, who = {}, {}
        for n, rows in res.items():
            r = rows[it["id"]]
            if r["passed"] == want:
                k = rid(it["id"], r["final"])
                reps[k] = r["final"]
                who[n] = k
        if reps:
            out[it["id"]] = (typ, it, reps, who)
    return out


def prep():
    os.makedirs(OUT, exist_ok=True)
    for s in SETS:
        items, res = load(s)
        L = []
        for i, (typ, it, reps, who) in to_grade(items, res).items():
            L.append(dict(id=i, type=typ, request=it["prompt"], judge=it.get("human", NO_ANSWER_Q),
                          replies=[dict(reply_id=k, reply=v) for k, v in sorted(reps.items())]))
        json.dump(L, open(os.path.join(OUT, f"items_{s}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(s, "items", len(L), "replies", sum(len(x["replies"]) for x in L), "models", list(res))


def merge():
    summary = {}
    for s in SETS:
        items, res = load(s)
        g = [{x["reply_id"]: x["grade"] for x in json.load(open(os.path.join(OUT, f"pass{p}_{s}.json"), encoding="utf-8"))} for p in (1, 2)]
        tg = to_grade(items, res)
        sec = {it["id"]: it["section"] for it in items}
        rows, final = [], {}
        for i, (typ, it, reps, who) in tg.items():
            for k, text in sorted(reps.items()):
                a, b = g[0][k], g[1][k]
                assert a in ("y", "n") and b in ("y", "n"), k
                final[k] = "y" if a == b == "y" else "n" if a == b == "n" else "unclear"
                rows.append(dict(id=i, type=typ, reply_id=k, models=[n for n, kk in who.items() if kk == k], reply=text, pass1=a, pass2=b, final=final[k]))
        adj = {}
        for n, rr in res.items():
            auto = {i: r["passed"] for i, r in rr.items()}
            new = dict(auto)
            for i, (typ, it, reps, who) in tg.items():
                if n in who:
                    new[i] = final[who[n]] == "y"
            head = [i for i in auto if sec[i] in "ABCD"]
            adj[n] = dict(auto_headline=sum(auto[i] for i in head), graded_headline=sum(new[i] for i in head),
                          lost=sorted(i for i in head if auto[i] and not new[i]), gained=sorted(i for i in head if new[i] and not auto[i]),
                          by_section={c: [sum(auto[i] for i in head if sec[i] == c), sum(new[i] for i in head if sec[i] == c)] for c in "ABCD"},
                          passed={i: new[i] for i in auto})
        n_rep = len(rows)
        summary[s] = dict(items=len(tg), replies=n_rep, agree=sum(r["pass1"] == r["pass2"] for r in rows),
                          unclear=sum(r["final"] == "unclear" for r in rows), headline_items=sum(sec[i] in "ABCD" for i in sec),
                          models={n: {k: v for k, v in a.items() if k != "passed"} for n, a in adj.items()})
        json.dump(dict(set=s, note="graded by AI against results/ai_grading/RUBRIC.md, two separate passes, disagreement counts as wrong; not graded by a person",
                       rows=rows, models=adj), open(os.path.join(OUT, f"grades_{s}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        M = [f"# AI grades: {s}", "", "Graded by AI against `RUBRIC.md`, in two separate passes. Not graded by a person.",
             "Where the passes differ the reply is \"unclear\" and counts as wrong.", "",
             f"{len(tg)} items, {n_rep} different replies, the passes agreed on {summary[s]['agree']}, unclear {summary[s]['unclear']}.", "",
             "| model | automatic, headline | after AI grading | lost | gained |", "|---|---|---|---|---|"]
        for n, a in adj.items():
            M.append(f"| {n} | {a['auto_headline']} | {a['graded_headline']} | {', '.join(a['lost']) or '-'} | {', '.join(a['gained']) or '-'} |")
        M += ["", "| part | " + " | ".join(adj) + " |", "|---|" + "---|" * len(adj)]
        for c in "ABCD":
            M.append(f"| {c}, automatic to graded | " + " | ".join(f"{a['by_section'][c][0]} to {a['by_section'][c][1]}" for a in adj.values()) + " |")
        M += ["", "| item | type | reply | models | pass 1 | pass 2 | final |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            t = r["reply"].replace("\n", " / ").replace("|", "\\|")
            M.append(f"| {r['id']} | {r['type']} | {t[:160]}{'...' if len(t) > 160 else ''} | {', '.join(r['models'])} | {r['pass1']} | {r['pass2']} | {r['final']} |")
        open(os.path.join(OUT, f"grades_{s}.md"), "w", encoding="utf-8", newline="\n").write("\n".join(M) + "\n")
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    {"prep": prep, "merge": merge}[sys.argv[1]]()

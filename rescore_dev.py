"""Stage 9: fix three checker faults in the dev set and re-score the saved replies. No model is run.

  python rescore_dev.py <name> ...     -> results/dev_v2/dev_<name>.json, prints every item whose result changed

Fault 1: "What is the opposite of old?" only accepted "new". "Young" is also right.
Faults 2 and 3: a sum whose answer is also a number in the question ("Multiply 3 by 1", "What is 0 x 4?")
could never pass, because the old rule removed the question's numbers from the reply before looking for the answer.
New rule: the answer must be in the reply, and the reply must hold no number that is neither the answer nor in the question.
The scoreboard keeps its old checker (scoreboard.py is not changed); this script also says what the new rule would do to it.
"""
import json
import os
import sys

from scoreboard import check_reply, numbers

HERE = os.path.dirname(os.path.abspath(__file__))


def fix_check(prompt, c):
    c = dict(c)
    if "opposite of old" in prompt and c.get("any") == ["new"]:
        c["any"] = ["new", "young"]
    return c


def check_v2(prompt, reply, c):
    c = fix_check(prompt, c)
    if "number" not in c or "tool" in c:
        return check_reply(prompt, reply, c)
    n = float(c.pop("number"))
    r = reply.strip()
    ok = bool(r) and n in numbers(r) and not (numbers(r) - numbers(prompt) - {n})
    return bool(ok and (check_reply(prompt, reply, c) if c else True))


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "results", "dev_v2"), exist_ok=True)
    dev = json.load(open(os.path.join(HERE, "data", "devset.json"), encoding="utf-8"))
    json.dump([dict(d, check=fix_check(d["prompt"], d["check"])) for d in dev],
              open(os.path.join(HERE, "data", "devset_v2.json"), "w", encoding="utf-8"), indent=1)
    answer_in_prompt = [d["prompt"] for d in dev if "number" in d["check"] and float(d["check"]["number"]) in numbers(d["prompt"])]
    print("dev items whose answer is a number in the question:", answer_in_prompt)
    for name in sys.argv[1:]:
        d = json.load(open(os.path.join(HERE, "results", "dev", f"dev_{name}.json"), encoding="utf-8"))
        changed = []
        for it in d["items"]:
            new = check_v2(it["prompt"], it["reply"], it["check"])
            if new != it["passed"]:
                changed.append((it["prompt"], it["reply"], it["passed"], new))
            it["passed_old"], it["passed"] = it["passed"], new
        old, d["total"] = d["total"], sum(it["passed"] for it in d["items"])
        fams = {}
        for it in d["items"]:
            fams.setdefault(it["family"], []).append(it["passed"])
        d["rates"] = {k: sum(v) / len(v) for k, v in fams.items()}
        json.dump(d, open(os.path.join(HERE, "results", "dev_v2", f"dev_{name}.json"), "w", encoding="utf-8"), indent=1)
        print(f"{name}: dev {old} -> {d['total']} of {d['n']}")
        for p, r, a, b in changed:
            print(f"    {'fail' if not a else 'pass'} -> {'pass' if b else 'fail'} | {p!r} | {r!r}")
        sb = json.load(open(os.path.join(HERE, "results", "final", f"scoreboard_{name}.json"), encoding="utf-8"))
        from scoreboard_prompts import GROUPS
        chk = {p: c for g in GROUPS.values() for p, c in g}
        diff = [(i["prompt"], i["reply"]) for i in sb["items"] if check_v2(i["prompt"], i["reply"], chk[i["prompt"]]) != i["passed"]]
        print(f"    scoreboard under the new rule: {sb['total']} -> {sb['total'] + sum(1 if not i['passed'] else -1 for i in sb['items'] if (i['prompt'], i['reply']) in diff)}", diff)

"""The fixed scoreboard, used for every model.

  python scoreboard.py runs/twin_baseline/final.pt --name twin

Reports: held-out story loss, held-out chat loss (all tokens and assistant tokens only),
and 100 prompts with automatic checks (greedy decoding, no repetition penalty).
Writes results/scoreboard_<name>.json with every reply and whether it passed.
"""
import argparse
import ast
import json
import operator
import os
import re

import torch
import torch.nn.functional as F

from chat import load_model
from common import ASSISTANT, CHAT_MIX, END, EOT, ROOT, USER, evaluate, fixed_val_batches, load_tokenizer, setup_torch
from scoreboard_prompts import GROUPS

NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
del NUM_WORDS["one"]  # "one" is too often not a number


def words(t):
    return re.findall(r"[A-Za-z0-9']+", t)


def has(t, phrase):
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(phrase.lower()) + r"(?![A-Za-z0-9])", t.lower()) is not None


def numbers(t):
    out = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", t.replace(",", ""))}
    return out | {float(NUM_WORDS[w.lower()]) for w in words(t) if w.lower() in NUM_WORDS}


OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def calc(expr):
    """Safe calculator: numbers, + - * / and brackets only. Raises on anything else."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        raise ValueError("not allowed")
    return ev(ast.parse(expr.strip(), mode="eval"))


def parse_tool_call(reply):
    """The last non-empty line must be JSON with exactly the keys tool and input."""
    lines = [l.strip() for l in reply.strip().splitlines() if l.strip()]
    if not lines:
        return None
    try:
        obj = json.loads(lines[-1])
    except Exception:
        return None
    if not (isinstance(obj, dict) and set(obj) == {"tool", "input"} and obj["tool"] in ("calc", "notes")
            and isinstance(obj["input"], str) and obj["input"].strip()):
        return None
    return obj


def check_reply(prompt, reply, c):
    r = reply.strip()
    w = words(r)
    lines = [l.strip() for l in r.splitlines() if l.strip()]
    if not r:
        return False
    if "tool" in c:
        obj = parse_tool_call(r)
        if obj is None or obj["tool"] != c["tool"]:
            return False
        if c["tool"] == "calc":
            try:
                return abs(calc(obj["input"]) - c["value"]) < 1e-6
            except Exception:
                return False
        return any(k in obj["input"].lower() for k in c["keys"])
    ok = True
    if "number" in c:
        ok &= (numbers(r) - numbers(prompt)) == {float(c["number"])}
    if "max_words" in c:
        ok &= len(w) <= c["max_words"]
    if "min_words" in c:
        ok &= len(w) >= c["min_words"]
    if "words" in c:
        ok &= len(w) == c["words"]
    if "any" in c:
        ok &= any(has(r, p) for p in c["any"])
    if "all" in c:
        ok &= all(has(r, p) for p in c["all"])
    if "none" in c:
        ok &= not any(has(r, p) for p in c["none"])
    if "any_raw" in c:
        ok &= any(p in r.lower() for p in c["any_raw"])
    if "count" in c:
        ok &= sum(x.lower() == c["count"][0] for x in w) == c["count"][1]
    if "sentences" in c:
        ok &= r[-1] in ".!?" and len(re.findall(r"[.!?]+", r)) == c["sentences"]
    if "ends" in c:
        ok &= r.endswith(c["ends"])
    if "last_word" in c:
        ok &= bool(w) and w[-1].lower() == c["last_word"]
    if "first_word" in c:
        ok &= bool(w) and w[0].lower() == c["first_word"]
    if "exact" in c:
        ok &= " ".join(r.split()) == c["exact"]
    if "has_exact" in c:
        ok &= c["has_exact"] in r
    if "lines" in c:
        ok &= len(lines) == c["lines"]
    if "words_per_line" in c:
        ok &= all(len(words(l)) == c["words_per_line"] for l in lines)
    if "line_starts" in c:
        ok &= len(lines) == len(c["line_starts"]) and all(l.startswith(s) for l, s in zip(lines, c["line_starts"]))
    if "line_words" in c:
        ok &= len(lines) == len(c["line_words"]) and all(has(l, s) for l, s in zip(lines, c["line_words"]))
    if "numbered" in c:
        ok &= len(lines) == c["numbered"] and all(re.match(rf"{i + 1}[.)]\s*\S", l) for i, l in enumerate(lines))
    if "dashed" in c:
        ok &= len(lines) == c["dashed"] and all(re.match(r"-\s*\S", l) for l in lines)
    if "quoted" in c:
        ok &= len(r) > 2 and r[0] in "\"“" and r[-1] in "\"”"
    if "squashed" in c:
        ok &= c["squashed"] in "".join(r.split())
    return bool(ok)


@torch.no_grad()
def greedy_reply(model, tok, prompt, max_new=120, rep_penalty=1.0):
    ids = [EOT, USER] + tok.encode(prompt.strip()).ids + [END, ASSISTANT]
    out = []
    with torch.autocast("cuda", dtype=torch.bfloat16):
        for t in model.generate(ids, max_new=max_new, temperature=0, stop_ids=(END, EOT, USER, ASSISTANT),
                                rep_penalty=rep_penalty):
            out.append(t)
    return tok.decode(out).strip()


@torch.no_grad()
def assistant_loss(model, batches):
    """Chat loss counted only on tokens the assistant writes (its words and its end mark)."""
    tot, n = 0.0, 0
    for x, y in batches:
        marker = (x == USER) | (x == ASSISTANT) | (x == EOT) | (x == END)
        pos = torch.arange(x.size(1), device=x.device).expand_as(x)
        last = torch.where(marker, pos, torch.full_like(pos, -1)).cummax(dim=1).values
        role = torch.where(last >= 0, x.gather(1, last.clamp(min=0)), torch.full_like(x, -1))
        mask = role == ASSISTANT
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits, _ = model(x)
        loss = F.cross_entropy(logits.float().view(-1, logits.size(-1)), y.reshape(-1), reduction="none")
        tot += (loss * mask.reshape(-1)).sum().item()
        n += int(mask.sum())
    return tot / n


def score(model, tok, rep_penalty=1.0):
    items, groups = [], {}
    for g, plist in GROUPS.items():
        passed = 0
        for prompt, c in plist:
            reply = greedy_reply(model, tok, prompt, rep_penalty=rep_penalty)
            ok = check_reply(prompt, reply, c)
            passed += ok
            items.append(dict(group=g, prompt=prompt, reply=reply, passed=ok))
        groups[g] = passed
    return groups, items


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--name", required=True)
    ap.add_argument("--rep_penalty", type=float, default=1.0)
    ap.add_argument("--out_dir", default="results")
    a = ap.parse_args()
    setup_torch(0)
    model = load_model(a.model)
    tok = load_tokenizer()
    ctx = model.cfg.ctx
    val_story = fixed_val_batches({"stories": 1.0}, 20, 64, ctx)
    val_chat = fixed_val_batches({k: v for k, v in CHAT_MIX.items() if k != "stories"}, 20, 64, ctx)
    out = dict(name=a.name, model=a.model, params=model.n_params()["total"], rep_penalty=a.rep_penalty,
               story_loss=evaluate(model, val_story), chat_loss=evaluate(model, val_chat),
               chat_loss_assistant_only=assistant_loss(model, val_chat))
    out["groups"], out["items"] = score(model, tok, a.rep_penalty)
    out["total"] = sum(out["groups"].values())
    os.makedirs(os.path.join(ROOT, a.out_dir), exist_ok=True)
    with open(os.path.join(ROOT, a.out_dir, f"scoreboard_{a.name}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "items"}, indent=1))

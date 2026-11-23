"""Tools for the helper: a calculator and a notes lookup, with grammar constrained tool calls.

A reply may end with one line of JSON, after a free draft line:
    I will use the calculator.
    {"tool": "calc", "input": "348 * 27"}
The draft is free text. As soon as a line of the reply starts with "{", every next token is
restricted so the line can only become a valid call (constrained=True). The tool answer goes back
as a user turn that starts with "Result:" and the model then writes the final answer.
"""
import re

import torch

from common import ASSISTANT, END, EOT, USER
from scoreboard import calc, parse_tool_call

HEAD = '{"tool": "'
MID = '", "input": "'
TAIL = '"}'
BODY = {"calc": re.compile(r"[0-9+\-*/(). ]{0,40}"), "notes": re.compile(r"[A-Za-z0-9' ]{0,40}")}


def call_prefix_state(s):
    """Is s a prefix of a valid tool-call line? Returns 'no', 'partial' or 'done'."""
    if len(s) <= len(HEAD):
        return "partial" if HEAD.startswith(s) else "no"
    if not s.startswith(HEAD):
        return "no"
    r = s[len(HEAD):]
    for name, body in BODY.items():
        full = name + MID
        if len(r) <= len(full):
            if full.startswith(r):
                return "partial"
            continue
        if not r.startswith(full):
            continue
        b = r[len(full):]
        if '"' not in b:
            return "partial" if body.fullmatch(b) else "no"
        inner, rest = b.split('"', 1)
        if not body.fullmatch(inner) or not inner.strip():
            return "no"
        if rest == "}":
            return "done"
        return "partial" if rest == "" else "no"
    return "no"


class Vocab:
    def __init__(self, tok):
        self.text = [tok.decode([i], skip_special_tokens=False) for i in range(tok.get_vocab_size())]


@torch.no_grad()
def generate_reply(model, tok, ids, vocab=None, max_new=120, constrained=True):
    """Greedy reply. With constrained=True a line that starts with '{' can only become a valid tool call."""
    dev = model.emb.weight.device
    stop = (END, EOT, USER, ASSISTANT)
    keep = model.cfg.ctx - max_new
    x = torch.tensor([list(ids)[-keep:]], device=dev)
    past, prev, out, text = [(None, None)] * len(model.blocks), None, [], ""
    for _ in range(max_new):
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits, past = model(x, past=past, prev=prev)
        prev = x[:, -1]
        logits = logits[0, -1].float()
        line = text.split("\n")[-1]
        nxt = int(logits.argmax())
        if constrained and vocab is not None and line.lstrip().startswith("{"):
            line = line.lstrip()
            if call_prefix_state(line) == "done":
                break  # the call is complete: stop here
            nxt = None
            for cand in torch.argsort(logits, descending=True).tolist():
                if cand in stop:
                    continue
                t = vocab.text[cand]
                if t and call_prefix_state(line + t) != "no":
                    nxt = cand
                    break
            if nxt is None:
                break
        elif nxt in stop:
            break
        out.append(nxt)
        text = tok.decode(out)
        x = torch.tensor([[nxt]], device=dev)
    return text.strip()


def search_notes(notes, query, k=3):
    """notes: list of lines. Returns the lines that share the most words with the query."""
    qs = [w for w in re.findall(r"[a-z0-9']+", query.lower()) if len(w) > 1]
    scored = []
    for line in notes:
        low = line.lower()
        s = sum(1 for w in qs if re.search(r"(?<![a-z0-9])" + re.escape(w), low))
        if s:
            scored.append((-s, len(scored), line))
    return [l for _, _, l in sorted(scored)[:k]]


def run_tool(obj, notes=()):
    if obj["tool"] == "calc":
        try:
            v = calc(obj["input"])
            return "Result: " + (str(int(v)) if abs(v - round(v)) < 1e-9 else f"{v:.2f}".rstrip("0").rstrip("."))
        except Exception:
            return "Result: error"
    hits = search_notes(notes, obj["input"])
    return "Result:\n" + "\n".join("- " + h for h in hits) if hits else "Result: nothing found"


def chat_ids(tok, turns):
    """turns: list of (role, text)."""
    ids = [EOT]
    for role, text in turns:
        ids += [USER if role == "user" else ASSISTANT] + tok.encode(text.strip()).ids + [END]
    return ids + [ASSISTANT]


def answer(model, tok, vocab, turns, notes=(), constrained=True, max_calls=1):
    """Run the tool loop. Returns (final reply, list of all turns added)."""
    turns, added = list(turns), []
    for _ in range(max_calls + 1):
        reply = generate_reply(model, tok, chat_ids(tok, turns), vocab, constrained=constrained)
        added.append(("assistant", reply))
        obj = parse_tool_call(reply)
        if obj is None or len(added) > 2 * max_calls:
            return reply, added
        result = run_tool(obj, notes)
        turns += [("assistant", reply), ("user", result)]
        added.append(("user", result))
    return reply, added

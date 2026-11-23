"""Chat with a trained model in the terminal.

  python chat.py final/small-smart-4bit.bin
  python chat.py final/small-smart-8bit.bin --tools --notes my_notes.txt

Options: --temp 0.6  --top_k 40  --max_new 200  --once "your message"
Type /reset to clear the conversation, /quit to leave.
"""
import argparse
import os
import sys

import torch

from common import ASSISTANT, END, EOT, ROOT, USER, load_tokenizer
from model import GPT, GPTConfig


def load_model(name_or_path, device="cuda"):
    path = name_or_path
    if not os.path.exists(path):
        path = os.path.join(ROOT, "runs", name_or_path, "final.pt")
        if not os.path.exists(path):
            path = os.path.join(ROOT, "runs", name_or_path, "ckpt.pt")
    if path.endswith(".bin"):  # a real low-bit file made by quant.py
        import quant
        ck = quant.load(path)
    else:
        ck = torch.load(path, map_location="cpu", weights_only=False)
    model = GPT(GPTConfig(**ck["cfg"]))
    model.load_state_dict({k: v.float() for k, v in ck["model"].items()})
    return model.to(device).eval()


def reply(model, tok, history, temp=0.6, top_k=40, max_new=200, gen=None, stream=None):
    """history: list of (role, text). Returns the assistant's text."""
    ids = [EOT]
    for role, text in history:
        ids += [USER if role == "user" else ASSISTANT] + tok.encode(text.strip()).ids + [END]
    ids.append(ASSISTANT)
    out = []
    shown = ""
    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=torch.cuda.is_available()):
        for t in model.generate(ids, max_new=max_new, temperature=temp, top_k=top_k,
                                stop_ids=(END, EOT, USER, ASSISTANT), rep_penalty=1.1,
                                generator=gen):
            out.append(t)
            if stream:
                text = tok.decode(out)
                stream(text[len(shown):])
                shown = text
    return tok.decode(out).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="seed, twin, or a path to a model file")
    ap.add_argument("--temp", type=float, default=0.6)
    ap.add_argument("--top_k", type=int, default=40)
    ap.add_argument("--max_new", type=int, default=200)
    ap.add_argument("--once", default=None)
    ap.add_argument("--tools", action="store_true", help="let the model use the calculator and the notes tool (steady, non-random replies)")
    ap.add_argument("--notes", default="", help="a text file with one note per line, for the notes tool")
    a = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = load_model(a.model, dev)
    tok = load_tokenizer()
    say = None
    if a.tools:
        from tools import Vocab, answer
        vocab = Vocab(tok)
        notes = [l.strip().lstrip("- ") for l in open(a.notes, encoding="utf-8") if l.strip()] if a.notes else []
        say = lambda turns: answer(model, tok, vocab, turns, notes=notes, constrained=False)[0]
    if a.once:
        if say:
            print(say([("user", a.once)]))
            return
        print(reply(model, tok, [("user", a.once)], a.temp, a.top_k, a.max_new))
        return
    print(f"Chatting with '{a.model}'. /reset clears, /quit leaves.")
    history = []
    while True:
        try:
            msg = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not msg:
            continue
        if msg == "/quit":
            break
        if msg == "/reset":
            history = []
            continue
        history.append(("user", msg))
        history = history[-8:]
        sys.stdout.write("bot> ")
        if say:
            text = say(history)
            print(text)
            history.append(("assistant", text))
            continue
        text = reply(model, tok, history, a.temp, a.top_k, a.max_new,
                     stream=lambda s: (sys.stdout.write(s), sys.stdout.flush()))
        print()
        history.append(("assistant", text))


if __name__ == "__main__":
    main()

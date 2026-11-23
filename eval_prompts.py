"""Run the 30 fixed test prompts through both models and save answers side by side.

  python eval_prompts.py            (uses runs/seed and runs/twin)

Writes results/side_by_side.md and results/side_by_side.json. Both models get
the same prompt, the same sampling settings and the same random seed.
"""
import argparse
import json
import os

import torch

from chat import load_model, reply
from common import ROOT, load_tokenizer

# Each item is a conversation: a list of user turns (most have one turn).
PROMPTS = [
    # greetings and small talk
    ["Hi!"],
    ["Hello, how are you today?"],
    ["Good morning!"],
    ["Thank you for your help. Bye!"],
    # identity
    ["Who are you?"],
    ["What can you do?"],
    ["Are you a person?"],
    # simple questions
    ["What color is the sky?"],
    ["What sound does a cow make?"],
    ["What is the opposite of hot?"],
    ["What is 2 plus 3?"],
    ["What day comes after Monday?"],
    ["Which is bigger, an elephant or a mouse?"],
    ["What do you use an umbrella for?"],
    # simple instructions
    ["Say the word banana."],
    ["Count from 1 to 5."],
    ["Name three animals."],
    ["Write a sentence with the word dog."],
    ["Answer with one word: what color is grass?"],
    ["Say hello two times."],
    ["Tell me two things you can find in a kitchen."],
    ["Please list three colors."],
    ["Give me one reason to brush my teeth."],
    # stories
    ["Tell me a short story about a cat."],
    ["Can you tell me a story about a girl named Mia and her red ball?"],
    ["Tell me a story about a brave little frog."],
    # feelings and advice
    ["I feel sad today."],
    ["I am hungry. What should I do?"],
    # two-turn conversations
    ["My favorite animal is the dog.", "Why do you think people like dogs?"],
    ["Hi there!", "Can you count to three for me?"],
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="seed")
    ap.add_argument("--b", default="twin")
    ap.add_argument("--temp", type=float, default=0.3)
    ap.add_argument("--out", default="side_by_side")
    a = ap.parse_args()
    tok = load_tokenizer()
    answers = {}
    for name in (a.a, a.b):
        model = load_model(name)
        res = []
        for i, turns in enumerate(PROMPTS):
            gen = torch.Generator(device="cuda").manual_seed(1000 + i)
            hist = []
            for u in turns:
                hist.append(("user", u))
                hist.append(("assistant", reply(model, tok, hist, temp=a.temp, top_k=40,
                                                max_new=160, gen=gen)))
            res.append(hist)
        answers[name] = res
        del model
        torch.cuda.empty_cache()

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump({"prompts": PROMPTS, "answers": answers, "temp": a.temp},
              open(os.path.join(ROOT, "results", a.out + ".json"), "w"), indent=1)
    lines = [f"# 30 fixed prompts: {a.a} vs {a.b}", "",
             f"Same prompts, sampling temperature {a.temp}, top-k 40, same random seed per prompt. "
             "Answers are unedited.", ""]
    for i, turns in enumerate(PROMPTS):
        lines.append(f"## {i + 1}. {' / '.join(turns)}")
        lines.append("")
        for name in (a.a, a.b):
            hist = answers[name][i]
            if len(turns) == 1:
                lines.append(f"- **{name}:** {hist[1][1]}")
            else:
                conv = " | ".join(f"{'you' if r == 'user' else 'bot'}: {t}" for r, t in hist)
                lines.append(f"- **{name}:** {conv}")
        lines.append("")
    open(os.path.join(ROOT, "results", a.out + ".md"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()

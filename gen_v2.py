"""v2 practice data, aimed at what the first held-out test exposed.

  python gen_v2.py seeds                 -> data/raw/v2/seeds.jsonl   (requests with known right answers)
  python gen_v2.py rewrite --minutes M   -> data/raw/v2/rewrites.jsonl (the teacher rewords each request; answers stay scripted)
  python gen_v2.py notes --minutes M     -> data/raw/v2/tnotes.jsonl   (the teacher invents notes with a question that never says "notes")
  python gen_v2.py build --n N           -> data/raw/job/v2.jsonl      (everything put together, held-out questions removed)

Three parts:
  1. new wordings: the teacher rewrites a request many ways; the answer is still worked out by this script.
  2. notes questions without the word "notes": the fact is in the notes store (search) or pasted in an odd layout.
  3. two skills in one request, composed by this script.
The teacher never supplies a fact that is used as an answer, except for its own invented notes, where the
answer must be made of words from the note.
"""
import argparse
import json
import os
import re
import sys
import time

import gen_job as G
import gen_job_extra as X
from gen_job import NUMW, R, cap, conv, pick
from scoreboard import numbers

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data", "raw", "v2")
STOP = set("the a an is are was were be on at in to of you your it its i my me we and or for that this with do does did "
           "what when where which who how many much can could please tell say write give word words answer reply".split())


def ascii_ok(t):
    return all(32 <= ord(c) < 127 or c == "\n" for c in t)


def tool_conv(kind, req, tool, inp, result, final, draft=None):
    draft = draft or pick(G.DRAFT_CALC if tool == "calc" else G.DRAFT_NOTES)
    return conv(kind, req, draft + "\n" + G.call(tool, inp), result, final)


# ---------------------------------------------------------------- arithmetic with slots (can be re-drawn with new numbers)
def draw(op, big):
    if not big:
        if op == "+":
            a, b = R.randint(2, 60), R.randint(2, 60)
        elif op == "-":
            a = R.randint(5, 99); b = R.randint(1, a - 1)
        elif op == "*":
            a, b = R.randint(2, 12), R.randint(2, 12)
        else:
            b = R.randint(2, 12); a = b * R.randint(2, 12)
    else:
        if op == "+":
            a, b = R.randint(100, 9999), R.randint(100, 9999)
        elif op == "-":
            a = R.randint(300, 20000); b = R.randint(100, a - 1)
        elif op == "*":
            a, b = R.randint(13, 999), R.randint(13, 99)
        else:
            b = R.randint(3, 99); a = b * R.randint(13, 999)
    if a == b:
        return draw(op, big)
    return a, b


def value(a, b, op):
    return {"+": a + b, "-": a - b, "*": a * b, "/": a // b}[op]


BASE_Q = {"+": "What is {a} plus {b}?", "-": "What is {a} minus {b}?", "*": "What is {a} times {b}?", "/": "What is {a} divided by {b}?"}
SIGN = {"+": "+", "-": "-", "*": "x", "/": "/"}


def arith_turns(a, b, op, big):
    """The assistant turns after the request, for a sum."""
    v = value(a, b, op)
    if not big:
        return [pick([f"{v}.", f"The answer is {v}.", f"{a} {SIGN[op]} {b} = {v}.", f"It is {v}."])]
    e = f"{a} {'*' if op == '*' else op} {b}"
    word = {"+": "plus", "-": "minus", "*": "times", "/": "divided by"}[op]
    fin = pick([f"{a} {word} {b} is {v}.", f"The answer is {v}.", f"It is {v}.", f"{a} {SIGN[op]} {b} = {v}."])
    return [pick(G.DRAFT_CALC) + "\n" + G.call("calc", e), f"Result: {v}", fin]


# ---------------------------------------------------------------- notes with numbers, for sums over notes
def num_notes():
    n1, n2 = R.sample(G.NAMES, 2)
    k = R.randrange(5)
    a, b = R.sample(range(2, 40), 2)
    if k == 0:
        return [f"{n1}'s ticket cost {a} coins.", f"{n2}'s ticket cost {b} coins."], pick(["How much did both tickets cost together?", "What did the two tickets cost in all?"]), a, b, "coins"
    if k == 1:
        e1, e2 = R.sample(["club", "class", "talk", "exam", "meeting"], 2)
        return [f"The {e1} is in room {a}.", f"The {e2} is in room {b}."], pick(["Add the two room numbers together.", "What do the two room numbers add up to?"]), a, b, ""
    if k == 2:
        t = pick(["apples", "eggs", "books", "pens", "cups"])
        return [f"{n1} has {a} {t}.", f"{n2} has {b} {t}."], pick([f"How many {t} do they have together?", f"How many {t} is that in all?"]), a, b, t
    if k == 3:
        return [f"The bus to town is number {a}.", f"The bus to the beach is number {b}."], "Add the two bus numbers.", a, b, ""
    t = pick(["chairs", "plates", "tickets", "seats"])
    return [f"We need {a} {t} for the hall.", f"We need {b} {t} for the garden."], f"How many {t} do we need in all?", a, b, t


# ---------------------------------------------------------------- two skills in one request
ADJ = ["wet", "cold", "warm", "soft", "loud", "bright", "quiet", "fun", "big", "green"]
GREET = ["good morning", "hello", "good night", "thank you", "well done"]
FACTS = [("what colour grass is", "grass is green"), ("what colour snow is", "snow is white"), ("what sound a dog makes", "a dog says woof"),
         ("how many legs a cat has", "a cat has four legs"), ("what colour the sky is on a clear day", "the sky is blue"),
         ("how many days are in a week", "a week has seven days")]


def two_skills():
    """Returns (request, [assistant turns...], notes prefix or '')."""
    k = R.randrange(24)
    cat, items = pick(list(G.CATS.items()))
    one = [x for x in items if " " not in x and "-" not in x]
    op = pick("+-*")
    a, b = draw(op, False)
    v = value(a, b, op)
    say = {"+": f"{a} plus {b}", "-": f"{a} minus {b}", "*": f"{a} times {b}"}[op]
    if k == 0:
        return pick([f"Work out {say} and reply with only the number.", f"What is {say}? Just the number, nothing else.", f"{cap(say)}. Give only the number."]), [str(v)], ""
    if k == 1:
        A, B = draw(pick("+-*"), True); o = pick("+-*")
        A, B = draw(o, True); V = value(A, B, o)
        s = {"+": f"{A} plus {B}", "-": f"{A} minus {B}", "*": f"{A} times {B}"}[o]
        return (pick([f"Work out {s} and reply with only the number.", f"What is {s}? Answer with the number only."]),
                [pick(G.DRAFT_CALC) + "\n" + G.call("calc", f"{A} {o} {B}"), f"Result: {V}", str(V)], "")
    if k == 2:
        n = R.randint(2, 4)
        return pick([f"Work out {say}, then say the answer {NUMW[n]} times.", f"Add up {say} and write the answer {NUMW[n]} times."] if op == "+" else
                    [f"Work out {say}, then say the answer {NUMW[n]} times."]), [" ".join([str(v)] * n)], ""
    if k == 3:
        c = max(1, v + pick([-9, -5, -2, 2, 5, 9, 14]))
        if c == v:
            c += 3
        w = pick(["more", "less"])
        yes = (v > c) == (w == "more")
        return pick([f"Is {say} {w} than {c}? Answer yes or no.", f"Yes or no: is {say} {w} than {c}?"]), ["Yes." if yes else "No."], ""
    if k == 4:
        n = R.randint(2, 4); xs = R.sample(one, min(n, len(one))); n = len(xs)
        return (pick([f"Name {NUMW[n]} {cat} as a numbered list, all in capital letters.", f"List {NUMW[n]} {cat}. Number them and use capital letters only."]),
                ["\n".join(f"{i + 1}. {x.upper()}" for i, x in enumerate(xs))], "")
    if k == 5:
        n = R.randint(2, 4); xs = R.sample(one, min(n, len(one))); n = len(xs)
        return (pick([f"Give me {NUMW[n]} {cat} with a dash in front of each, in capital letters.", f"Write {NUMW[n]} {cat} in capitals, one per line, each line starting with a dash."]),
                ["\n".join(f"- {x.upper()}" for x in xs)], "")
    if k == 6:
        w = pick(["done", "end", "stop", "thanks", "bye"])
        return pick([f"Two lines. First line: the answer to {say}. Second line: the word {w}.", f"Write the answer to {say} on one line and the word {w} on the next line."]), [f"{v}\n{w}"], ""
    if k == 7:
        notes, q, x, y, unit = num_notes()
        R.shuffle(notes)
        return q, [pick([f"{x} + {y} = {x + y}.", f"{x} + {y} = {x + y}{' ' + unit if unit else ''}.", f"The answer is {x + y}."])], "Notes:\n" + "\n".join("- " + n for n in notes) + "\n\n"
    if k == 8:
        note, qas, key = G.make_note()
        q, ans, word = pick(qas)
        return (pick([f"Look in my notes: {q} Answer in capital letters.", f"Check my notes and tell me in capital letters: {q}"]),
                [pick(G.DRAFT_NOTES) + "\n" + G.call("notes", word.lower()), "Result:\n- " + note, ans.upper()], "")
    if k == 9:
        j, d, t = pick(G.JOBS), pick(G.DAYS), G.time_str()
        return (pick([f"Find the {j} in my notes and tell me just the day, in one word.", f"Look in my notes. Which day is the {j}? One word only."]),
                [pick(G.DRAFT_NOTES) + "\n" + G.call("notes", j.split()[0]), f"Result:\n- {cap(j)} on {d} at {t}.", f"{d}."], "")
    if k == 10:
        x, y = pick(G.OPPOSITES)
        return pick([f"What is the opposite of {x}? Write it in capital letters.", f"Give me the opposite of {x} in capitals."]), [y.upper()], ""
    if k == 11:
        w1, w2 = R.sample(G.WORDS, 2); n = R.randint(2, 3)
        return f"Say the word {w1} {NUMW[n]} times, then the word {w2} once.", [" ".join([w1] * n + [w2])], ""
    if k == 12:
        lo = R.randint(1, 9); hi = lo + R.randint(2, 5)
        return pick([f"List the numbers from {lo} to {hi}, one on each line.", f"Write {lo} to {hi} with each number on its own line."]), ["\n".join(str(i) for i in range(lo, hi + 1))], ""
    if k == 13:
        t, w = pick(G.WEATHER + ["the sea", "the sun", "the moon"]), pick(ADJ)
        return pick([f"Write one sentence about {t} that ends with the word {w}.", f"One sentence about {t}, please, and make {w} the last word."]), [f"{cap(t)} can be very {w}."], ""
    if k == 14:
        o = pick("+-*"); A, B = draw(o, True); V = value(A, B, o)
        c = round(V * pick([0.6, 0.8, 1.2, 1.5]), -2) or 100
        c = int(c) if int(c) != V else int(c) + 100
        s = {"+": f"{A} plus {B}", "-": f"{A} minus {B}", "*": f"{A} times {B}"}[o]
        yes = V > c
        return (f"What is {s}? Then tell me if the answer is bigger than {c}, yes or no.",
                [pick(G.DRAFT_CALC) + "\n" + G.call("calc", f"{A} {o} {B}"), f"Result: {V}", f"{A} {SIGN[o]} {B} = {V}. {'Yes' if yes else 'No'}, it is {'' if yes else 'not '}bigger than {c}."], "")
    if k == 15:
        t = pick(["apples", "books", "coins", "shells", "pens", "eggs"])
        x, y = R.randint(2, 20), R.randint(2, 20)
        return pick([f"Answer with a number and then the word {t}: {x} {t} and {y} {t} together.", f"{x} {t} plus {y} {t}. Reply with the number and the word {t} only."]), [f"{x + y} {t}"], ""
    if k == 16:
        j1, j2 = R.sample(G.JOBS, 2); d1, d2 = R.sample(G.DAYS, 2)
        notes = [f"{cap(j1)} on {d1} at {G.time_str()}.", f"{cap(j2)} on {d2} at {G.time_str()}."]
        return pick(["List my two activities as a numbered list.", "Put the two things I have on as a numbered list."]), [f"1. {cap(j1)}\n2. {cap(j2)}"], "Notes:\n" + "\n".join("- " + n for n in notes) + "\n\n"
    if k == 17:
        x, y = R.randint(2, 12), R.randint(2, 12); c = x * y + pick([-7, -3, -1, 1, 3, 7])
        return pick([f"Which is bigger, {x} times {y} or {c}? Answer with the bigger number only.", f"{x} times {y} or {c}: which is more? Give just that number."]), [str(max(x * y, c))], ""
    if k == 18:
        n = R.randint(2, 5); w = pick(["yes", "no", "ok", "hello"] + G.WORDS)
        return pick([f"Write {NUMW[n]} lines. Each line is the word {w}.", f"Put the word {w} on {NUMW[n]} lines, one word per line."]), ["\n".join([w] * n)], ""
    if k == 19:
        c1, c2 = pick([("colour", G.COLOURS), ("fruit", G.FRUITS), ("animal", G.ANIMALS), ("drink", G.DRINKS)]), pick([("animal", G.ANIMALS), ("toy", [t for t in G.TOYS if " " not in t and "-" not in t]), ("day", G.DAYS)])
        if c1[0] == c2[0]:
            return two_skills()
        return f"Tell me a {c1[0]} and {X.art(c2[0])} {c2[0]}, separated by a comma, and nothing else.", [f"{pick(c1[1])}, {pick(c2[1])}"], ""
    if k == 20:
        xs = R.sample(G.SHOP, R.randint(2, 4))
        lst = ", ".join(xs[:-1]) + " and " + xs[-1]
        if R.random() < 0.5:
            return (pick(["What is on my shopping list in my notes? Put each thing on its own line.", "Look in my notes for what to buy and write each thing on a new line."]),
                    [pick(G.DRAFT_NOTES) + "\n" + G.call("notes", "buy"), f"Result:\n- Buy {lst}.", "\n".join(xs)], "")
        return pick(["What do I need to buy? Put each thing on its own line.", "Write my shopping list with one thing per line."]), ["\n".join(xs)], f"Notes:\n- Buy {lst}.\n- {G.make_note()[0]}\n\n"
    if k == 21:
        g = pick(GREET)
        return pick([f"First say {g}. Then, on a new line, tell me what {say} is.", f"Say {g} on the first line and the answer to {say} on the second line."]), [f"{cap(g)}.\n{a} {SIGN[op]} {b} = {v}."], ""
    if k == 22:
        fq, fa = pick(FACTS)
        return f"In one sentence, tell me what {say} is and {fq}.", [f"{cap(say)} is {v} and {fa}."], ""
    s = G.sentence().rstrip(".").lower()
    return pick([f"Count the words in this sentence and reply with a number: {s}.", f"How many words are in this sentence? Answer with a number. {cap(s)}."]), [str(len(s.split()))], ""


# ---------------------------------------------------------------- plain questions whose answer is in the notes store
STORE_ASK = ["{Q}", "{Q}", "{Q}", "Remind me, {q}", "Do you know {q}", "Quick question: {q}", "I forgot. {Q}", "Can you tell me {q}", "{Q} I can't remember.",
             "Sorry to ask again, but {q}", "Help me out. {Q}", "One thing: {q}"]
MISS = ["I could not find a note about that.", "There is no note about that.", "Your notes do not say anything about that.", "I looked in your notes but found nothing about that."]
UNKNOWABLE = [("What number am I thinking of?", "I don't know. I cannot read your mind!"), ("What will happen tomorrow?", "I don't know. Nobody can know for sure what will happen tomorrow."),
              ("What is in my hand right now?", "I don't know. I cannot see you."), ("What am I wearing today?", "I don't know. I cannot see you. You can tell me!"),
              ("Will it rain next week?", "I don't know. I cannot see the weather where you are."), ("What is behind me?", "I don't know. I cannot see where you are."),
              ("Who is at the door?", "I don't know. I cannot see your door."), ("What did I dream about last night?", "I don't know. Only you can know your dreams."),
              ("How many people are in this room?", "I don't know. I cannot see the room."), ("What is the next card in the pack?", "I don't know. Nobody can know that before it is turned over."),
              ("Which team will win on Saturday?", "I don't know. Nobody can know before the game is played."), ("What am I going to say next?", "I don't know. I cannot read your mind!"),
              ("What is in the box I am holding?", "I don't know. I cannot see the box."), ("How much money is in my pocket?", "I don't know. I cannot see in your pocket.")]


def store_seed(found=True):
    note, qas, key = G.make_note()
    q, ans, word = pick(qas)
    req = pick(STORE_ASK).format(q=q, Q=cap(q))
    if found:
        return req, [pick(G.DRAFT_NOTES) + "\n" + G.call("notes", word.lower()), "Result:\n- " + note, ans], word
    return req, [pick(G.DRAFT_NOTES) + "\n" + G.call("notes", word.lower()), "Result: nothing found", pick(MISS)], word


LAYOUTS = ["Reminders: {semi}.\n{Q}", "To do\n{numbered}\n\n{Q}", "Here is what I wrote down this morning: {run}\n{Q}", "{stars}\n\n{Q}", "{run} {Q}",
           "My list:\n{plain}\n\n{Q}", "Things to remember - {semi}. {Q}", "{Q}\n\n{plain}", "I wrote these down. {run} So, {q}", "{numbered}\n{Q}",
           "From my diary: {run}\n\n{Q}", "{plain}\n{Q}"]


def layout(notes, q):
    bare = [n.rstrip(".") for n in notes]
    return pick(LAYOUTS).format(semi="; ".join(b[0].lower() + b[1:] if not b.split()[0][0].isupper() or b.split()[0] in ("The", "Buy", "Call") else b for b in bare),
                                numbered="\n".join(f"{i + 1}. {n}" for i, n in enumerate(notes)), run=" ".join(notes), stars="\n".join("* " + n for n in notes),
                                plain="\n".join(notes), Q=cap(q), q=q)


def inline_odd(extra=None):
    """Notes pasted in an unfamiliar layout; the word notes is never used. extra: a (note, question, answer) from the teacher."""
    others = [n[0] for n in G.note_set(R.randint(1, 3))]
    if extra:
        note, q, ans = extra
    else:
        note, qas, _ = G.make_note()
        q, ans, _ = pick(qas)
    notes = others + [note]
    R.shuffle(notes)
    return conv("v2_inline", layout(notes, q), ans)


# ---------------------------------------------------------------- seeds for the teacher to reword
def keep_words(req, ans):
    aw = set(re.findall(r"[a-z0-9']+", ans.lower()))
    ks = [w for w in re.findall(r"[A-Za-z0-9']+", req) if w.lower() in aw and w.lower() not in STOP and len(w) > 2]
    names = [w for w in re.findall(r"(?<=[a-z,] )[A-Z][a-z]+", req)]
    return sorted(set(ks + names))


def seeds(n_each=1):
    out = []

    def add(fam, req, turns, prefix="", arith=None, keep=None):
        final = turns[-1]
        out.append(dict(sid=len(out), fam=fam, req=req, turns=turns, prefix=prefix, arith=arith,
                        keep=keep if keep is not None else keep_words(req, " ".join(t for t in turns if not t.startswith("Result")))))
    for _ in range(260 * n_each):
        op = pick("++--**/"); a, b = draw(op, False)
        add("arith", BASE_Q[op].format(a=a, b=b), arith_turns(a, b, op, False), arith=dict(a=a, b=b, op=op, big=0), keep=[])
    for _ in range(200 * n_each):
        op = pick("++--**/"); a, b = draw(op, True)
        add("calc", BASE_Q[op].format(a=a, b=b), arith_turns(a, b, op, True), arith=dict(a=a, b=b, op=op, big=1), keep=[])
    for _ in range(150 * n_each):
        q, ans = G.word_problem()
        add("word_problem", q, [ans])
    gens = [G.gen_instruction, G.gen_format, X.gen_one_word, X.gen_yes_no, X.gen_repeat_word, X.gen_exact_words, X.gen_capitals2, X.gen_number_only, X.gen_lines]
    n = 0
    while n < 520 * n_each:
        c = pick(gens)()["messages"]
        if len(c) == 2 and G.allowed({"messages": c}):
            add("rule", c[0]["content"], [c[1]["content"]]); n += 1
    n = 0
    while n < 150 * n_each:
        c = G.gen_notes_tool()["messages"]
        if G.allowed({"messages": c}):
            add("notes_tool", c[0]["content"], [m["content"] for m in c[1:]]); n += 1
    n = 0
    while n < 180 * n_each:
        c = G.gen_notes_inline()["messages"]
        if len(c) == 2 and G.allowed({"messages": c}) and "\n\n" in c[0]["content"]:
            pre, q = c[0]["content"].rsplit("\n\n", 1)
            add("notes_inline", q, [c[1]["content"]], prefix=pre + "\n\n"); n += 1
    for i in range(330 * n_each):
        req, turns, word = store_seed(found=i % 7 != 0)
        add("store", req, turns, keep=[w for w in keep_words(req, turns[1]) if w.lower() != "notes"])
    for _ in range(620 * n_each):
        req, turns, prefix = two_skills()
        add("two", req, turns, prefix=prefix)
    return out


REWRITE = ("A user typed this request to a helper:\n<<<{req}>>>\n\nWrite {n} different ways a real person might type the SAME request. "
           "Vary them a lot: casual or polite, short or long, a question or a command, different everyday words, different order. "
           "The meaning must stay exactly the same, so the right answer does not change, and every rule in the request must still be there. "
           "Keep every number as it is{keep}. {extra}Do not answer the request inside the rewrite. Plain keyboard characters only. "
           'For each one also give the correct answer in a few words. JSON: {{"items": [{{"request": "...", "answer": "..."}}]}}')


def rewrite(minutes, per=6):
    from teacher import ask, gpu_busy, MODEL
    import subprocess
    assert not gpu_busy(), "a python process is using the GPU: do not run the teacher while training runs"
    S = [json.loads(l) for l in open(os.path.join(D, "seeds.jsonl"), encoding="utf-8")]
    path = os.path.join(D, "rewrites.jsonl")
    done = {json.loads(l)["sid"] for l in open(path, encoding="utf-8")} if os.path.exists(path) else set()
    todo = [s for s in S if s["sid"] not in done]
    R.seed(int(time.time())); R.shuffle(todo)
    t0, n, calls, bad = time.time(), 0, 0, 0
    with open(path, "a", encoding="utf-8") as f:
        for s in todo:
            if time.time() - t0 > minutes * 60:
                break
            keep = (", and keep these exact words: " + ", ".join(s["keep"])) if s["keep"] else ""
            extra = "Never use the word note or notes. " if s["fam"] == "store" else ("The request is asked about some notes shown above it; only rewrite the question. " if s["fam"] == "notes_inline" else "")
            try:
                data = ask(REWRITE.format(req=s["req"], n=per, keep=keep, extra=extra))
                items = [(str(i["request"]).strip(), str(i.get("answer", ""))) for i in data["items"]]
            except Exception:
                bad += 1
                continue
            calls += 1
            f.write(json.dumps(dict(sid=s["sid"], items=items)) + "\n"); f.flush()
            n += len(items)
            if calls % 50 == 0:
                print(f"{(time.time() - t0) / 60:.1f} min  {calls} calls  {n} rewrites  {bad} failed", flush=True)
    subprocess.run(["ollama", "stop", MODEL])
    print("done", calls, "calls", n, "rewrites")


TNOTES = ("Invent {n} different short notes that a person might keep for themselves, about: {theme}. Each note is ONE short plain sentence with a "
          "clear fact in it (a day, a time, a place, a name, a number, a code, a price, or what to bring). For each note write: a question the "
          "person might ask later to get that fact back, typed the way a real person would, WITHOUT the words note or notes; the answer as one "
          "short sentence that uses only the fact from the note; and one search word, a single lower-case word that is in the note and names its topic. "
          'Plain keyboard characters only. JSON: {{"items": [{{"note": "...", "question": "...", "answer": "...", "key": "..."}}]}}')
TTHEMES = ["appointments and visits", "where things are kept at home", "codes and passwords", "people to call and why", "shopping and prices", "travel plans, buses, trains and flights",
           "school and clubs", "work meetings and tasks", "birthdays and parties", "pets and their care", "food, recipes and allergies", "money, rent and bills",
           "the car and the bike", "the garden and the house", "health and medicine times", "things lent to friends", "opening times of places", "holidays and trips",
           "sports and games", "family visits", "deliveries and parcels", "chores and the days they are done", "favourite things of friends and family", "phone numbers and addresses"]


def tnotes(minutes, per=8):
    from teacher import ask, gpu_busy, MODEL
    import subprocess
    assert not gpu_busy(), "a python process is using the GPU: do not run the teacher while training runs"
    t0, n, calls, bad = time.time(), 0, 0, 0
    R.seed(int(time.time()))
    with open(os.path.join(D, "tnotes.jsonl"), "a", encoding="utf-8") as f:
        while time.time() - t0 < minutes * 60:
            try:
                data = ask(TNOTES.format(n=per, theme=pick(TTHEMES)))
                items = [dict(note=str(i["note"]).strip(), question=str(i["question"]).strip(), answer=str(i["answer"]).strip(), key=str(i["key"]).strip().lower()) for i in data["items"]]
            except Exception:
                bad += 1
                continue
            calls += 1
            for i in items:
                f.write(json.dumps(i) + "\n")
            f.flush(); n += len(items)
            if calls % 25 == 0:
                print(f"{(time.time() - t0) / 60:.1f} min  {calls} calls  {n} notes  {bad} failed", flush=True)
    subprocess.run(["ollama", "stop", MODEL])
    print("done", calls, "calls", n, "notes")


# ---------------------------------------------------------------- checks on what the teacher wrote
def good_rewrite(s, req, ans, why):
    def no(r):
        why[r] = why.get(r, 0) + 1
        return False
    if not req or not ascii_ok(req) or "\n" in req or "<<<" in req:
        return no("characters")
    if len(req.split()) > 2 * len(s["req"].split()) + 12 or len(req.split()) < 2:
        return no("length")
    if req.strip().lower() == s["req"].strip().lower():
        return no("same as the original")
    if numbers(req) != numbers(s["req"]):
        return no("numbers changed")
    if any(not re.search(r"(?<![A-Za-z0-9])" + re.escape(k.lower()) + r"(?![A-Za-z0-9])", req.lower()) for k in s["keep"]):
        return no("kept word missing")
    if s["fam"] == "store" and re.search(r"\bnotes?\b", req.lower()):
        return no("says notes")
    if s["fam"] in ("notes_tool",) and not re.search(r"\bnotes?\b", req.lower()):
        return no("notes request without the word notes")
    if s["arith"]:
        a = s["arith"]
        if float(value(a["a"], a["b"], a["op"])) not in numbers(ans):
            return no("teacher's own answer was wrong")
    return True


def good_tnote(i, why):
    def no(r):
        why[r] = why.get(r, 0) + 1
        return False
    note, q, ans, key = i["note"], i["question"], i["answer"], i["key"]
    if not all(ascii_ok(x) and "\n" not in x for x in (note, q, ans, key)):
        return no("characters")
    if not (3 <= len(note.split()) <= 16 and 3 <= len(q.split()) <= 18 and 1 <= len(ans.split()) <= 18):
        return no("length")
    if re.search(r"\bnotes?\b", (q + " " + ans).lower()):
        return no("says notes")
    if not re.fullmatch(r"[a-z0-9']{3,}", key) or not re.search(r"(?<![a-z0-9])" + re.escape(key), note.lower()):
        return no("key not in the note")
    nw = set(re.findall(r"[a-z0-9:']+", (note + " " + q).lower()))
    extra = [w for w in re.findall(r"[a-z0-9:']+", ans.lower()) if w not in nw and w not in STOP and w not in ("yes", "no", "it's", "should", "need", "needs", "has", "have", "will", "there", "from", "not", "by", "they", "he", "she", "them", "his", "her", "their", "our", "us", "go", "goes", "get", "gets", "take", "takes", "bring", "about", "into", "as", "if", "so", "then", "must", "us")]
    if extra:
        return no("answer has words that are not in the note")
    if numbers(ans) - numbers(note):
        return no("answer has a number that is not in the note")
    return True


def held_out_lines():
    """Question lines of every frozen held-out test, numbers masked. Read by the program only."""
    from heldout import mask
    out = set()
    for name in ("heldout.json", "heldout2.json"):
        p = os.path.join(HERE, "data", name)
        if os.path.exists(p):
            for it in json.load(open(p, encoding="utf-8")):
                out.add(mask(it["prompt"].strip().splitlines()[-1]))
                out.add(mask(it["prompt"]))
    return out


def build(n):
    from heldout import mask
    S = {s["sid"]: s for s in (json.loads(l) for l in open(os.path.join(D, "seeds.jsonl"), encoding="utf-8"))}
    why, out, stats = {}, [], {}

    def put(c):
        out.append(c); stats[c["kind"]] = stats.get(c["kind"], 0) + 1
    # 1. teacher rewrites, answers from the script
    templ = []
    p = os.path.join(D, "rewrites.jsonl")
    total = 0
    for l in (open(p, encoding="utf-8") if os.path.exists(p) else []):
        r = json.loads(l); s = S[r["sid"]]
        for req, ans in r["items"]:
            total += 1
            if not good_rewrite(s, req, ans, why):
                continue
            put(conv("v2_rw_" + s["fam"], s["prefix"] + req, *s["turns"]))
            if s["arith"]:
                a = s["arith"]
                sa, sb = str(a["a"]), str(a["b"])
                toks = re.findall(r"\d+", req)
                if toks.count(sa) == 1 and toks.count(sb) == 1 and len(toks) == 2:
                    t = re.sub(r"(?<!\d)" + sa + r"(?!\d)", "{a}", req)
                    t = re.sub(r"(?<!\d)" + sb + r"(?!\d)", "{b}", t)
                    if "{a}" in t and "{b}" in t:
                        templ.append((t, a["op"], a["big"]))
    print("rewrites read", total, "kept", len(out), "dropped", why, "sum wordings that can take new numbers", len(templ))
    # 2. teacher notes
    why2, tn = {}, []
    p = os.path.join(D, "tnotes.jsonl")
    seen = set()
    for l in (open(p, encoding="utf-8") if os.path.exists(p) else []):
        i = json.loads(l)
        if good_tnote(i, why2) and i["note"].lower() not in seen:
            seen.add(i["note"].lower()); tn.append(i)
    print("teacher notes kept", len(tn), "dropped", why2)
    R.seed(4321)
    n_rw = len(out)
    while len(out) < n:
        k = R.random()
        if k < 0.22 and templ:  # reworded sums with new numbers
            t, op, big = pick(templ)
            a, b = draw(op, big)
            put(conv("v2_sum_new_numbers", t.format(a=a, b=b), *arith_turns(a, b, op, big)))
        elif k < 0.42:  # plain question, fact in the notes store
            if tn and R.random() < 0.6:
                i = pick(tn)
                if R.random() < 0.12:
                    put(tool_conv("v2_store", i["question"], "notes", i["key"], "Result: nothing found", pick(MISS)))
                else:
                    res = [i["note"]] + [x["note"] for x in R.sample(tn, 2) if x["key"] == i["key"] and x["note"] != i["note"]]
                    put(tool_conv("v2_store", i["question"], "notes", i["key"], "Result:\n" + "\n".join("- " + x for x in res), i["answer"]))
            else:
                req, turns, _ = store_seed(found=R.random() > 0.12)
                put(conv("v2_store", req, *turns))
        elif k < 0.57:  # notes pasted in an odd layout
            i = pick(tn) if tn and R.random() < 0.5 else None
            put(inline_odd((i["note"], i["question"], i["answer"]) if i else None))
        elif k < 0.95:
            req, turns, prefix = two_skills()
            put(conv("v2_two", prefix + req, *turns))
        else:
            q, a = pick(UNKNOWABLE)
            put(conv("v2_unknowable", q, a))
    # leak rule: any conversation whose request matches a held-out question is deleted from the practice data
    ho = held_out_lines()
    keep, dropped, seen = [], 0, set()
    for c in out:
        u = c["messages"][0]["content"]
        if mask(u) in ho or mask(u.strip().splitlines()[-1]) in ho or not G.allowed(c):
            dropped += 1
            continue
        key = json.dumps(c["messages"])
        if key in seen:
            continue
        seen.add(key); keep.append(c)
    R.shuffle(keep)
    path = os.path.join(HERE, "data", "raw", "job", "v2.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for c in keep:
            f.write(json.dumps(c) + "\n")
    kinds = {}
    for c in keep:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print("wrote", len(keep), "conversations; removed for matching a held-out or scoreboard or dev question:", dropped, "; duplicates removed:", len(out) - dropped - len(keep))
    print(json.dumps(kinds, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--n", type=int, default=300000)
    a = ap.parse_args()
    os.makedirs(D, exist_ok=True)
    if a.cmd == "seeds":
        R.seed(20261123)
        S = seeds()
        with open(os.path.join(D, "seeds.jsonl"), "w", encoding="utf-8") as f:
            for s in S:
                f.write(json.dumps(s) + "\n")
        fam = {}
        for s in S:
            fam[s["fam"]] = fam.get(s["fam"], 0) + 1
        print("wrote", len(S), "seeds", fam)
    elif a.cmd == "rewrite":
        rewrite(a.minutes)
    elif a.cmd == "notes":
        tnotes(a.minutes)
    elif a.cmd == "build":
        build(a.n)

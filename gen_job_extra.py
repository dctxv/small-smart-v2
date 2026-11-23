"""Round 1 additions to the job data: the families the first student failed on the dev set
(exact word counts, one-word answers, yes/no, repeating a word, capitals, number-only answers).
Imported at the end of gen_job.py, which then uses GENS from here.
"""
import re

import gen_job as G
from gen_job import (ANIMALS, CLOTHES, COLOURS, DAYS, DRINKS, FRUITS, MONTHS, NAMES, NUMW, ONEWORD, OPPOSITES, R, SCHOOL,
                     VEG, WORDS, YESNO, cap, conv, direct_problem, pick, plural, sentence)


def nwords(t):
    return len(re.findall(r"[A-Za-z0-9']+", t))


ONE = [w for w in ANIMALS + FRUITS + WORDS + CLOTHES + SCHOOL if " " not in w and "-" not in w]
ADJ = ["nice", "fun", "kind", "soft", "good", "small", "big", "happy", "funny", "sweet", "lovely", "great"]


def n_word_reply(n, topic=None):
    """A natural reply with exactly n words (2 to 8). topic: a plural noun of one word, or None."""
    t = topic
    for _ in range(50):
        if t:
            s = {2: [f"{cap(t)} rock.", f"Lovely {t}.", f"{cap(t)} please."],
                 3: [f"I like {t}.", f"{cap(t)} are {pick(ADJ)}.", f"I love {t}."],
                 4: [f"{cap(t)} are very {pick(ADJ)}.", f"I really like {t}.", f"I think {t} rock."],
                 5: [f"I think {t} are {pick(ADJ)}.", f"{cap(t)} are {pick(ADJ)} and {pick(ADJ)}.", f"I like {t} a lot."],
                 6: [f"I think {t} are very {pick(ADJ)}.", f"Many people like {t} very much.", f"I like to look at {t}."],
                 7: [f"I think {t} are {pick(ADJ)} and {pick(ADJ)}.", f"I like {t} and I see them often."],
                 8: [f"I think {t} are very {pick(ADJ)} and {pick(ADJ)}.", f"I like {t} and many of my friends do."]}[n]
        else:
            a, c, nm = pick(ONE), pick(COLOURS), pick(NAMES)
            s = {2: ["Hello there.", "Thank you.", "Good morning.", "Sounds good.", "Yes please.", "Of course.", "Sleep well.", f"Hello {nm}."],
                 3: ["I am here.", "Here you go.", "I like you.", "That sounds fun.", f"I like {plural(a)}.", "Let us play."],
                 4: ["I am happy today.", "The sky is blue.", f"The {a} is {c}.", "Have a good day.", "It is very nice.", "I like to read."],
                 5: ["I hope you are well.", f"I like the {c} {a}.", "Today is a good day.", "I am glad to help.", f"{nm} has a {c} {a}."],
                 6: ["I hope you have fun today.", f"The {a} is on the table.", "I like to play in parks.", f"{nm} likes the {c} {a} best."],
                 7: ["I hope you have a good day.", f"I can see a {c} {a} today.", "The little bird sang a sweet song."],
                 8: ["I hope you have a very good day.", f"{nm} put the {c} {a} in the box.", "I like to walk in the big green park."]}[n]
        r = pick(s)
        if nwords(r) == n:
            return r
    return None


def gen_exact_words():
    while True:
        n = R.randint(2, 8)
        num = pick([NUMW[n], NUMW[n], str(n)])
        if R.random() < 0.5:
            t = plural(pick([x for x in ANIMALS + FRUITS if " " not in x]))
            q = pick([f"Tell me about {t} in exactly {num} words.", f"Say something about {t} using exactly {num} words.",
                      f"Use exactly {num} words to tell me about {t}.", f"Write exactly {num} words about {t}."])
            r = n_word_reply(n, t)
        else:
            q = pick([f"Reply with exactly {num} words.", f"Answer in exactly {num} words.", f"Say something with exactly {num} words.",
                      f"Write a reply that has exactly {num} words.", f"Give me exactly {num} words.", f"Use exactly {num} words."])
            r = n_word_reply(n)
        if r:
            return conv("instr", q, r)


AFTER = [(DAYS, "day"), (MONTHS, "month")]
KIND_OF = [("animal", ANIMALS), ("fruit", FRUITS), ("colour", COLOURS), ("vegetable", VEG), ("drink", DRINKS)]
COLOUR_OF = [("grass", "green"), ("snow", "white"), ("a banana", "yellow"), ("the sun", "yellow"), ("coal", "black"),
             ("a carrot", "orange"), ("milk", "white"), ("a lemon", "yellow"), ("the sky on a clear day", "blue"),
             ("a tomato", "red"), ("a frog", "green"), ("a strawberry", "red"), ("chocolate", "brown"), ("a cherry", "red"),
             ("a leaf in summer", "green"), ("the sea", "blue"), ("a pumpkin", "orange"), ("a cloud", "white"),
             ("the night sky", "black"), ("a plum", "purple")]
SOUNDS = [("woof", "dog"), ("moo", "cow"), ("quack", "duck"), ("oink", "pig"), ("baa", "sheep"), ("meow", "cat"),
          ("neigh", "horse"), ("buzz", "bee"), ("hoot", "owl"), ("roar", "lion"), ("hiss", "snake"), ("ribbit", "frog"),
          ("cluck", "hen")]
BIGGER = [("elephant", "mouse"), ("horse", "cat"), ("whale", "fish"), ("bus", "bike"), ("tree", "flower"), ("house", "shoe"),
          ("cow", "hen"), ("bear", "rabbit"), ("mountain", "hill"), ("lion", "frog")]
ONE_ASK = ["Answer with one word: {q}?", "{Q}? Answer with one word.", "In one word, {q}?", "{Q}? One word only.",
           "{Q}? Just one word, please.", "Use one word to answer: {q}?", "One word answer: {q}?"]


def art(w):
    return "an" if w[0] in "aeiou" else "a"


def is_a(x, kind):
    return f"is {x} {art(kind)} {kind}" if x in COLOURS + DRINKS else f"is {art(x)} {x} {art(kind)} {kind}"


def gen_one_word():
    k = R.randrange(8)
    if k == 0:
        q, a = pick(ONEWORD)
        a = a.rstrip(".")
    elif k == 1:
        x, a = pick(COLOUR_OF); q = f"what colour is {x}"
    elif k == 2:
        s_, a = pick(SOUNDS); q = pick([f"what animal says {s_}", f"which animal goes {s_}"])
    elif k == 3:
        lst, nm = pick(AFTER); i = R.randrange(len(lst))
        q, a = pick([(f"what {nm} comes after {lst[i]}", lst[(i + 1) % len(lst)]), (f"what {nm} comes before {lst[i]}", lst[i - 1])])
    elif k == 4:
        (n1, l1), (n2, l2) = R.sample(KIND_OF, 2)
        x = pick(l1); pair = [x, pick(l2)]; R.shuffle(pair)
        q, a = f"which is {art(n1)} {n1}, {pair[0]} or {pair[1]}", x
    elif k == 5:
        x, y = pick(OPPOSITES)
        if R.random() < 0.5:
            x, y = y, x
        q, a = pick([f"what is the opposite of {x}", f"what word means the opposite of {x}"]), y
    elif k == 6:
        n = R.randint(1, 98)
        q, a = pick([(f"what number comes after {n}", str(n + 1)), (f"what number comes before {n}", str(n - 1))])
    else:
        big, small = pick(BIGGER); pair = [big, small]; R.shuffle(pair)
        w = pick(["bigger", "smaller"])
        q, a = f"which is {w}, {art(pair[0])} {pair[0]} or {art(pair[1])} {pair[1]}", big if w == "bigger" else small
    return conv("instr", pick(ONE_ASK).format(q=q, Q=cap(q)), cap(a) + ".")


YN_ASK = ["Answer only yes or no: {q}?", "{Q}? Answer yes or no.", "Yes or no: {q}?", "{Q}? Just say yes or no.",
          "{Q}? Reply with only yes or no.", "Answer with yes or no only. {Q}?"]


def gen_yes_no():
    k = R.randrange(7)
    yes = R.random() < 0.5
    if k == 0:
        q, yes = pick(YESNO)
    elif k == 1:
        (n1, l1), (n2, _) = R.sample(KIND_OF, 2)
        q = is_a(pick(l1), n1 if yes else n2)
    elif k == 2:
        a_, b_ = R.sample(range(1, 100), 2); w = pick(["bigger", "smaller"])
        q, yes = f"is {a_} {w} than {b_}", (a_ > b_) == (w == "bigger")
    elif k == 3:
        x, c = pick(COLOUR_OF)
        q = f"is {x} {c if yes else pick([z for z in COLOURS if z != c and z not in ('gold', 'silver', 'grey', 'pink')])}"
    elif k == 4:
        i = R.randrange(7); j = (i + 1) % 7 if yes else (i + R.randint(2, 5)) % 7
        q = f"does {DAYS[j]} come right after {DAYS[i]}"
    elif k == 5:
        x, y = R.randint(1, 20), R.randint(1, 20)
        q = f"is {x} plus {y} equal to {x + y if yes else x + y + pick([-2, -1, 1, 2, 3])}"
    else:
        s_, an = pick(SOUNDS)
        q = f"does {art(an)} {an if yes else pick([z for _, z in SOUNDS if z != an])} say {s_}"
        if not yes:
            q = re.sub(r"does an? (\w+)", lambda m: f"does {art(m.group(1))} {m.group(1)}", q)
    return conv("instr", pick(YN_ASK).format(q=q, Q=cap(q)), "Yes." if yes else "No.")


def gen_repeat_word():
    w, n = pick(ONE + COLOURS + [x.lower() for x in DAYS]), R.randint(2, 6)
    num = pick([NUMW[n] + " times", NUMW[n] + " times", f"{n} times"]) if n > 2 else pick(["two times", "twice", "2 times"])
    q = pick([f"Say the word {w} {num}.", f"Say {w} {num}.", f"Repeat the word {w} {num}.", f"Write the word {w} {num}.",
              f"Can you say {w} {num}?", f"Please write {w} {num} and nothing else."])
    return conv("instr", q, " ".join([w] * n))


def gen_capitals():
    w = pick([pick(ONE), pick(ONE), pick(NAMES).lower(), sentence().rstrip(".").lower(),
              pick(["good night", "thank you", "happy birthday", "well done", "see you soon", "good morning", "come here",
                    "stop now", "i like tea", "look at me"])])
    q = pick([f"Write the word {w} in capital letters.", f"Write this in capital letters: {w}", f"Put this in capitals: {w}",
              f"Write {w} in all capital letters.", f"Make this all capital letters: {w}", f"Change this to capital letters: {w}"])
    if " " in w:
        q = q.replace("the word ", "")
    return conv("format", q, w.upper())


COUNTS = [("legs does a dog have", 4), ("legs does a bird have", 2), ("days are in a week", 7), ("wheels does a bike have", 2),
          ("wheels does a car have", 4), ("legs does a spider have", 8), ("months are in a year", 12),
          ("fingers are on one hand", 5), ("eyes does a person have", 2), ("sides does a triangle have", 3),
          ("sides does a square have", 4), ("legs does a horse have", 4), ("legs does a cat have", 4),
          ("ears does a rabbit have", 2), ("legs does a cow have", 4), ("wings does a bird have", 2), ("hours are in a day", 24),
          ("minutes are in an hour", 60), ("toes are on one foot", 5), ("wheels does a tricycle have", 3),
          ("legs does an ant have", 6), ("legs does a duck have", 2), ("days are in a weekend", 2)]
NUM_ONLY = ["Answer with a single number.", "Reply with just the number.", "Give only the number.", "Answer with only the number.",
            "Just the number, please.", "Write only the number."]


def gen_number_only():
    k = R.randrange(4)
    if k == 0:
        q, a = pick(COUNTS); q = f"How many {q}?"
    elif k == 1:
        q, ans = direct_problem(); a = re.findall(r"-?\d+", ans)[-1]
    elif k == 2:
        n = R.randint(1, 98); q, a = pick([(f"What number comes after {n}?", n + 1), (f"What number comes before {n}?", n - 1)])
    else:
        x, y = R.sample(range(100), 2); w = pick(["bigger", "smaller"])
        q, a = f"Which is {w}, {x} or {y}?", (max if w == "bigger" else min)(x, y)
    return conv("format", q + " " + pick(NUM_ONLY), str(a))


GENS = [(G.gen_notes_inline, 0.15), (G.gen_arith, 0.22), (G.gen_calc, 0.08), (G.gen_notes_tool, 0.08), (G.gen_format, 0.12),
        (G.gen_instruction, 0.10), (gen_exact_words, 0.06), (gen_one_word, 0.05), (gen_yes_no, 0.04), (gen_repeat_word, 0.04),
        (gen_capitals, 0.03), (gen_number_only, 0.03)]


# ------------------------------------------------------------------ round 2: what the round 1 student still failed
import json as _json
import os as _os

_p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "simple_words.json")
COMMON = [w for w in _json.load(open(_p)) if w.isalpha() and 3 <= len(w) <= 9] if _os.path.exists(_p) else ONE


def gen_capitals2():
    """Capital letters for any common word, so the model learns how words are spelt."""
    w = pick(COMMON) if R.random() < 0.8 else " ".join(R.sample(COMMON, 2))
    q = pick([f"Write the word {w} in capital letters.", f"Write this in capital letters: {w}", f"Put this in capitals: {w}",
              f"Write {w} in all capital letters.", f"Make this all capital letters: {w}", f"Change this to capital letters: {w}",
              f"Shout the word {w}.", f"{w} in capitals, please."])
    if " " in w:
        q = q.replace("the word ", "")
    return conv("format", q, w.upper())


def gen_lines():
    n = R.randint(2, 6)
    q = pick([f"Write exactly {NUMW[n]} lines. Each line is one short sentence.", f"Write {NUMW[n]} short sentences, one per line.",
              f"Give me {NUMW[n]} lines. Put one short sentence on each line.", f"Write {n} lines, one short sentence on each.",
              f"I want exactly {NUMW[n]} lines, each with one short sentence.", f"Write {NUMW[n]} lines of one sentence each.",
              f"Please write exactly {n} lines. One short sentence per line."])
    return conv("format", q, "\n".join(sentence() for _ in range(n)))


GENS2 = [(G.gen_notes_inline, 0.13), (G.gen_arith, 0.28), (G.gen_calc, 0.08), (G.gen_notes_tool, 0.08), (G.gen_format, 0.10),
         (G.gen_instruction, 0.09), (gen_exact_words, 0.04), (gen_one_word, 0.03), (gen_yes_no, 0.03), (gen_repeat_word, 0.03),
         (gen_capitals, 0.01), (gen_capitals2, 0.05), (gen_number_only, 0.03), (gen_lines, 0.02)]


CALC_Q = {
    "+": ["What is {a} + {b}?", "What is {a} plus {b}?", "Add {a} and {b}.", "{a} + {b} = ?", "{a} plus {b}?", "How much is {a} plus {b}?",
          "Work out {a} + {b}.", "Add {b} to {a}.", "What do {a} and {b} make?", "I need {a} added to {b}.", "Could you add {a} and {b}?",
          "{a} and {b} more is how many?", "What is {a} added to {b}?", "Find {a} + {b} for me.",
          "{n} has {a} {t} and gets {b} more. How many {t} does {n} have now?", "There are {a} {t} in one box and {b} in another. How many {t} are there in all?"],
    "-": ["What is {a} - {b}?", "What is {a} minus {b}?", "Take {b} away from {a}.", "{a} - {b} = ?", "{a} minus {b}?", "How much is {a} minus {b}?",
          "Work out {a} - {b}.", "Subtract {b} from {a}.", "What is left if I take {b} from {a}?", "Could you take {b} from {a}?",
          "What is {a} less {b}?", "Find {a} - {b} for me.", "{n} has {a} {t} and gives away {b}. How many {t} are left?",
          "A shop had {a} {t} and sold {b}. How many {t} does it have now?"],
    "*": ["What is {a} times {b}?", "What is {a} x {b}?", "Multiply {a} by {b}.", "{a} * {b} = ?", "{a} times {b}?", "How much is {a} times {b}?",
          "Work out {a} x {b}.", "What is {a} * {b}?", "What are {b} lots of {a}?", "Could you multiply {a} and {b}?", "Find {a} times {b} for me.",
          "I bought {b} boxes with {a} {t} in each box. How many {t} is that?", "One bag holds {a} {t}. How many {t} are in {b} bags?",
          "There are {b} rows with {a} {t} in each row. How many {t} are there?", "A ticket costs {a} coins. How much do {b} tickets cost?"],
    "/": ["What is {p} divided by {b}?", "Divide {p} by {b}.", "{p} / {b} = ?", "How much is {p} divided by {b}?", "Work out {p} / {b}.",
          "What is {p} / {b}?", "Share {p} {t} between {b} people. How many {t} does each one get?", "Find {p} divided by {b} for me.",
          "{b} friends share {p} {t} equally. How many {t} does each friend get?", "How many times does {b} go into {p}?"]}
CALC_PRE = ["Use the calculator: ", "Use the calculator. ", "With the calculator, ", "Calculator please: ", "Please use the calculator. "]
CALC_POST = ["", "", "", " Please.", " Thanks."]


def gen_calc2():
    """Calculator requests with many wordings. Any sum with a number of three or more digits goes to the calculator."""
    op = pick("++--***/")
    big = lambda: pick([R.randint(100, 999), R.randint(100, 9999), R.randint(1000, 99999)])
    small = lambda: R.randint(2, 99)
    t, n = pick(["pencils", "seeds", "bricks", "beads", "pages", "coins", "tiles", "stamps", "apples", "books", "shells", "cards"]), pick(NAMES)
    if op in "+-":
        a, b = (big(), big()) if R.random() < 0.5 else (big(), small())
        if op == "+" and R.random() < 0.3:
            a, b = b, a
        if op == "-" and b > a:
            a, b = b, a
        v, e = (a + b, f"{a} + {b}") if op == "+" else (a - b, f"{a} - {b}")
        p = 0
    elif op == "*":
        a, b = pick([(R.randint(13, 999), R.randint(3, 99)), (R.randint(100, 9999), R.randint(2, 99)), (R.randint(11, 99), R.randint(11, 99))])
        v, e, p = a * b, f"{a} * {b}", 0
    else:
        b = R.randint(3, 99); a = R.randint(13, 999); p = a * b
        v, e = a, f"{p} / {b}"
    q = pick(CALC_Q[op]).format(a=a, b=b, p=p, t=t, n=n)
    story = q[0].isalpha() and (" has " in q or "bought" in q or "shop" in q or "bag" in q or "rows" in q or "ticket" in q or "hare" in q or "boxes" in q or "box" in q)
    if story:
        unit = "coins" if "coins" in q else t
        fin = pick([f"That is {v} {unit}.", f"The answer is {v} {unit}.", f"{e.replace('*', 'x')} = {v}. That is {v} {unit}."])
    else:
        word = {"+": "plus", "-": "minus", "*": "times", "/": "divided by"}[op]
        l, r = e.split(f" {op} ")
        fin = pick([f"{l} {op if op in '+-' else word} {r} {'=' if op in '+-' else 'is'} {v}.", f"{l} {word} {r} is {v}.", f"The answer is {v}.", f"It is {v}."])
    if R.random() < 0.25:
        pre = pick(CALC_PRE)
        q = pre + (q if q.startswith("I ") or story or pre.endswith(". ") else q[0].lower() + q[1:])
        if R.random() < 0.25:  # sometimes even an easy sum is asked for with the calculator
            a, b = R.randint(2, 30), R.randint(2, 30)
            q, e, v, fin = pre + f"{'W' if pre.endswith('. ') else 'w'}hat is {a} + {b}?", f"{a} + {b}", a + b, f"{a} + {b} = {a + b}."
    elif not story and q.endswith("."):
        q = q + pick(CALC_POST) if R.random() < 0.3 else q
    return conv("tool_calc", q, pick(G.DRAFT_CALC) + "\n" + G.call("calc", e), f"Result: {G.fmt_num(v)}", fin)


gen_calc2.__name__ = "gen_calc2"
GENS2 = [(f, w) if f is not G.gen_calc else (gen_calc2, 0.10) for f, w in GENS2]

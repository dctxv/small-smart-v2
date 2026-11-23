"""Teacher data: a local model writes clean simple-English conversations for the job.

  python teacher.py gen --round 1 --minutes 90 [--weights results/teacher_weights.json]
  python teacher.py filter                merge all rounds, filter, de-duplicate -> data/raw/teacher/clean.jsonl

Teacher: qwen3:8b through Ollama (Apache 2.0), thinking switched off. NEVER run this while training runs:
"gen" refuses to start if another python process is using the GPU.

Kinds of data:
  explain   short simple explanations of everyday things
  chat      friendly talk, feelings, small advice (one or two turns)
  howto     short how-to answers in steps
  instr     an instruction with a rule a program can check (the reply is kept only if it passes)
  notes     the user pastes notes and asks; the answer must come from the notes
Every item is checked: plain characters, simple words, short, no scoreboard prompt, no repeats.
"""
import argparse
import collections
import glob
import json
import os
import random
import re
import subprocess
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "raw", "teacher")
MODEL = os.environ.get("TEACHER", "qwen3.5:2b")
R = random.Random()

THEMES = ("the weather, rain, snow, wind, clouds, the sun, the moon, stars, the sea, rivers, mountains, trees, flowers, "
          "seeds, farms, cows, dogs, cats, birds, fish, bees, ants, spiders, frogs, bears, whales, sleep, dreams, food, "
          "bread, milk, fruit, vegetables, water, cooking, breakfast, teeth, hands, eyes, ears, the heart, bones, "
          "being sick, doctors, exercise, washing, clothes, shoes, houses, beds, kitchens, gardens, school, reading, "
          "writing, numbers, counting, clocks, days of the week, months, seasons, birthdays, holidays, friends, family, "
          "babies, grandparents, sharing, being kind, saying sorry, being brave, feeling sad, feeling angry, "
          "feeling shy, being bored, being tired, games, toys, balls, bikes, cars, buses, trains, boats, planes, "
          "roads, bridges, shops, money, saving, jobs, farmers, teachers, firefighters, cooks, builders, music, "
          "drums, singing, drawing, colours, paper, books, stories, letters, phones, computers, lights, fire, ice, "
          "magnets, shadows, rainbows, thunder, soap, glass, wood, metal, wool, pets, zoos, parks, beaches, camping, "
          "picnics, swimming, running, soccer, safety, crossing the road, recycling, plants in pots, soil, worms, "
          "butterflies, nests, eggs, honey, salt, sugar, tea, soup, pizza, time, morning, night, noise, quiet, maps, "
          "the post, keys, doors, windows, stairs, chairs, tools, hammers, paint, rain boots, umbrellas, hats").split(", ")

SYSTEM = ("You write training data for a small friendly helper that speaks very simple English. Rules for the "
          "helper's replies: short sentences, common words a seven year old knows, warm and kind, true facts only, "
          "no lists unless asked, no emoji, no markdown, plain keyboard characters only, British spelling. "
          "Answer with JSON only.")


def p_explain(n, theme):
    shape = R.choice(["Why", "How", "What is", "What are", "Where", "When", "What happens when", "Can", "Do"])
    ln = R.choice(["one or two short sentences", "two or three short sentences", "three short sentences"])
    return (f"Write {n} different questions a curious person might ask about: {theme}. Mix the kinds; several should "
            f"start with \"{shape}\". For each, write the helper's answer in {ln}. "
            'JSON: {"items": [{"user": "...", "assistant": "..."}]}')


def p_chat(n, theme):
    mood = R.choice(["happy", "worried", "sad", "excited", "bored", "tired", "proud", "curious", "nervous", "grateful"])
    return (f"Write {n} different short chats. The user, feeling {mood}, says something or asks something about: {theme}. "
            f"The user writes like a real person, one short message. The helper replies warmly in one to three short "
            f"sentences and may ask one small question back. "
            'JSON: {"items": [{"user": "...", "assistant": "..."}]}')


def p_chat2(n, theme):
    return (f"Write {n} different short chats of two turns about: {theme}. The user says something, the helper replies in "
            f"one or two short sentences, the user answers, and the helper replies again in one or two short sentences. "
            'JSON: {"items": [{"user": "...", "assistant": "...", "user2": "...", "assistant2": "..."}]}')


def p_howto(n, theme):
    return (f"Write {n} different simple \"how do I\" questions connected to: {theme} (everyday, safe things). The helper "
            f"answers with two to four very short steps, written as a numbered list, one step per line, like "
            f"\"1. Fill the cup.\" JSON: " '{"items": [{"user": "...", "assistant": "..."}]}')


RULES = [  # (text added to the request, check name, argument maker)
    ("Answer in exactly one sentence.", "sentences", lambda: 1),
    ("Answer in exactly two sentences.", "sentences", lambda: 2),
    ("Answer in exactly three sentences.", "sentences", lambda: 3),
    ("Use fewer than {a} words.", "max_words", lambda: R.choice([6, 8, 10, 12, 15])),
    ("Reply with exactly {a} words.", "words", lambda: R.choice([2, 3, 4, 5, 6])),
    ("Start your reply with the word {a}.", "first_word", lambda: R.choice(["Sure", "Yes", "Well", "Okay", "Today", "First", "Hello"])),
    ("End your reply with the word {a}.", "last_word", lambda: R.choice(["today", "friend", "now", "please", "too", "day", "home"])),
    ("Use the word {a} in your reply.", "has", lambda: R.choice(["happy", "blue", "soft", "quick", "little", "warm", "bright", "green", "kind", "big"])),
    ("Do not use the word {a}.", "none", lambda: None),
    ("Give your reply as a numbered list of {a} things.", "numbered", lambda: R.choice([2, 3, 4, 5])),
    ("Give your reply as {a} lines, each starting with a dash.", "dashed", lambda: R.choice([2, 3, 4])),
    ("Answer with one word.", "words", lambda: 1),
    ("Write your whole reply in capital letters.", "upper", lambda: None),
    ("Put your whole reply inside quote marks.", "quoted", lambda: None),
    ("Answer with a question.", "ends", lambda: "?"),
]
NUMW = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split()


def p_instr(n, theme):
    text, kind, mk = R.choice(RULES)
    a = mk()
    shown = NUMW[a] if isinstance(a, int) and kind in ("words", "numbered", "dashed") and R.random() < 0.7 else a
    rule = text.format(a=shown)
    extra = ""
    if kind == "none":
        extra = (" For this rule, each user message names the obvious word that must be avoided (for example, "
                 "\"Tell me about the sea. Do not use the word water.\"). Add the field \"avoid\" with that word.")
        rule = "Do not use the word X."
    return (f"Write {n} different user requests about: {theme}. Every request must include this rule, worded "
            f"naturally and placed before or after the request: \"{rule}\"{extra} Then write the helper's reply. "
            f"The reply MUST obey the rule exactly. "
            'JSON: {"items": [{"user": "...", "assistant": "..."}]}'), (kind, a)


def p_notes(n, theme):
    return (f"Write {n} different items. Each item has \"notes\": three to five short personal notes a person might keep "
            f"(appointments, shopping, names, places, times, codes, reminders; one can be about {theme}), one per "
            f"line, each line starting with \"- \". Then \"qa\": three questions the person asks about the notes with "
            f"the helper's answers. The answer is one short sentence using only what the notes say. Make exactly one "
            f"of the three questions about something the notes do NOT contain; its answer must be \"The notes do not "
            f"say.\" or \"I cannot find that in the notes.\" "
            'JSON: {"items": [{"notes": "- ...\\n- ...", "qa": [{"user": "...", "assistant": "..."}]}]}')


ONE_WORD = ["Answer with one word.", "Answer with one word:", "Reply with one word.", "Use one word.", "One word only.", "Give a one word answer."]
YES_NO = ["Answer only yes or no:", "Answer yes or no.", "Yes or no?", "Reply with only yes or no.", "Just say yes or no."]
NUM_ONLY = ["Answer with a single number.", "Reply with just the number.", "Give only the number.", "Answer with a number only."]


def p_fact1(n, theme):
    shape = R.choice(["opposites (What is the opposite of ...?)", "what animal or thing does something", "what colour something is",
                      "what we use for a job", "where something lives or is found", "what something is made of",
                      "which one of two things is bigger, faster, hotter or heavier", "what comes next (days, months, seasons, numbers)",
                      "what a baby animal or a group is called", "what part of the body does something"])
    return (f"Write {n} different very easy quiz questions connected to: {theme}. Kind of question: {shape}. Each question "
            f"must have one clear true answer that is ONE common word (not a number). Every child would agree with the answer. "
            'JSON: {"items": [{"user": "question", "assistant": "oneword"}]}'), ("fact1", None)


def p_yesno(n, theme):
    return (f"Write {n} different very easy yes or no questions about: {theme}. Use forms like \"Is ...?\", \"Can ...?\", "
            f"\"Do ...?\", \"Does ...?\", \"Are ...?\". The true answer must be clear to every child. Make about half of the "
            f"answers no. The answer field is only \"yes\" or \"no\". "
            'JSON: {"items": [{"user": "question", "assistant": "yes"}]}'), ("yesno", None)


def p_howmany(n, theme):
    return (f"Write {n} different very easy \"How many ...?\" questions connected to: {theme} or to everyday things "
            f"(body parts, animals, shapes, time, the calendar, vehicles, things in a house). Each must have one fixed true "
            f"answer that is a whole number from 0 to 100. The answer field is only the number in digits. "
            'JSON: {"items": [{"user": "question", "assistant": "4"}]}'), ("howmany", None)


def wrap_fact(kind, q, a):
    """Turn a bare question and answer into a request with the format rule in it. None if the answer is not usable."""
    q, a = q.strip(), a.strip().rstrip(".").strip()
    if not q.endswith("?") or len(q) > 90:
        return None
    if kind == "fact1":
        if not re.fullmatch(r"[A-Za-z']{2,14}", a):
            return None
        rule, reply = R.choice(ONE_WORD), a.capitalize() + "."
    elif kind == "yesno":
        if a.lower() not in ("yes", "no"):
            return None
        rule, reply = R.choice(YES_NO), a.capitalize() + "."
    else:
        if not re.fullmatch(r"\d{1,3}", a):
            return None
        rule, reply = R.choice(NUM_ONLY), a
    user = f"{rule} {q[0].lower() + q[1:] if rule.endswith(':') and not q.startswith('I ') else q}" if R.random() < 0.5 or rule.endswith(":") else f"{q} {rule}"
    if rule.endswith("?") and R.random() < 0.5:
        user = f"{q} {rule}"
    return user, reply


KINDS = {"fact1": (p_fact1, 12), "yesno": (p_yesno, 12), "howmany": (p_howmany, 10), "explain": (p_explain, 8), "chat": (p_chat, 8), "chat2": (p_chat2, 5), "howto": (p_howto, 6),
         "instr": (p_instr, 8), "notes": (p_notes, 4)}
WEIGHTS = {"explain": 0.30, "chat": 0.20, "chat2": 0.08, "howto": 0.07, "instr": 0.25, "notes": 0.10}


def ask(prompt, temperature=0.9):
    body = json.dumps({"model": MODEL, "stream": False, "think": False, "format": "json", "keep_alive": "10m",
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                       "options": {"temperature": temperature, "num_predict": 1800, "num_ctx": 4096}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def gpu_busy():
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=name", "--format=csv,noheader"], capture_output=True, text=True).stdout
    return "python" in out.lower()


def to_convs(kind, data, meta=None):
    out = []
    for it in data.get("items", []):
        try:
            if kind == "notes":
                head = R.choice(["Notes:", "My notes:", "Here are my notes:"])
                for qa in it["qa"]:
                    out.append(dict(kind=kind, messages=[dict(role="user", content=f"{head}\n{it['notes'].strip()}\n\n{qa['user'].strip()}"),
                                                         dict(role="assistant", content=qa["assistant"].strip())]))
                continue
            if kind in ("fact1", "yesno", "howmany"):
                w = wrap_fact(kind, str(it["user"]), str(it["assistant"]))
                if w:
                    out.append(dict(kind=kind, messages=[dict(role="user", content=w[0]), dict(role="assistant", content=w[1])]))
                continue
            msgs = [dict(role="user", content=it["user"].strip()), dict(role="assistant", content=it["assistant"].strip())]
            if kind == "chat2":
                msgs += [dict(role="user", content=it["user2"].strip()), dict(role="assistant", content=it["assistant2"].strip())]
            c = dict(kind=kind, messages=msgs)
            if meta:
                c["rule"] = [meta[0], it.get("avoid") if meta[0] == "none" else meta[1]]
            out.append(c)
        except Exception:
            pass
    return out


def gen(round_, minutes, weights):
    assert not gpu_busy(), "a python process is using the GPU: do not run the teacher while training runs"
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"round{round_}.jsonl")
    R.seed(round_ * 1000 + int(time.time()) % 1000)
    t0, n, bad = time.time(), 0, 0
    kinds, ws = zip(*weights.items())
    with open(path, "a", encoding="utf-8") as f:
        while time.time() - t0 < minutes * 60:
            kind = R.choices(kinds, ws)[0]
            fn, per = KINDS[kind]
            p = fn(per, R.choice(THEMES))
            meta = None
            if isinstance(p, tuple):
                p, meta = p
            try:
                convs = to_convs(kind, ask(p), meta)
            except Exception as e:
                bad += 1
                continue
            for c in convs:
                f.write(json.dumps(c) + "\n")
            f.flush()
            n += len(convs)
            if n % 200 < len(convs):
                print(f"{(time.time() - t0) / 60:.1f} min  {n} conversations  {bad} failed requests", flush=True)
    subprocess.run(["ollama", "stop", MODEL])
    print("done", n, "conversations in", path)


# ------------------------------------------------------------------ filtering
def simple_vocab():
    """Words seen often in the story and chat training text: the 'simple English' word list."""
    p = os.path.join(HERE, "data", "simple_words.json")
    if os.path.exists(p):
        return set(json.load(open(p)))
    import numpy as np
    from common import TOK_DIR, load_tokenizer
    tok = load_tokenizer()
    cnt = collections.Counter()
    for name, n in (("stories_train", 30_000_000), ("tinychat_train", 5_000_000), ("synth_train", 5_000_000)):
        ids = np.fromfile(os.path.join(TOK_DIR, name + ".bin"), dtype=np.uint16, count=n)
        for s in range(0, len(ids), 1_000_000):
            cnt.update(re.findall(r"[a-z']+", tok.decode(ids[s:s + 1_000_000].tolist()).lower()))
    words = sorted(w for w, c in cnt.items() if c >= 20)
    json.dump(words, open(p, "w"))
    return set(words)


def rule_ok(rule, user, reply):
    from scoreboard import check_reply
    kind, a = rule
    if kind == "none":
        return bool(a) and a.lower() in user.lower() and check_reply(user, reply, {"none": [a]})
    if kind == "upper":
        return reply == reply.upper() and any(ch.isalpha() for ch in reply)
    if kind == "has":
        return check_reply(user, reply, {"all": [a]})
    if kind == "quoted":
        return check_reply(user, reply, {"quoted": True})
    return check_reply(user, reply, {kind: a.lower() if isinstance(a, str) and kind != "ends" else a})


def clean(c, vocab, why):
    from gen_job import allowed
    def no(reason):
        why[reason] += 1
        return False
    msgs = c["messages"]
    if not allowed(c):
        return no("scoreboard")
    for m in msgs:
        t = m["content"]
        if not t or any(ord(ch) > 126 or (ord(ch) < 32 and ch != "\n") for ch in t):
            return no("characters")
        if "**" in t or "#" in t or "http" in t:
            return no("markdown")
        w = re.findall(r"[A-Za-z']+", t)
        if m["role"] == "assistant":
            if len(w) > 70 or len(t) < 1:
                return no("long")
            if re.search(r"\b(AI|language model|assistant)\b", t):
                return no("self talk")
            rare = [x for x in w if x.lower() not in vocab and not x[0].isupper()]
            if len(rare) > max(1, 0.08 * len(w)):
                return no("hard words")
        elif len(w) > (110 if c["kind"] == "notes" else 45):
            return no("long")
    if c["kind"] == "instr" and not rule_ok(c["rule"], msgs[0]["content"], msgs[1]["content"]):
        return no("rule broken")
    if c["kind"] == "howto" and not re.match(r"1[.)] ", msgs[1]["content"]):
        return no("not steps")
    if c["kind"] == "notes":
        notes, q = msgs[0]["content"].rsplit("\n\n", 1)
        a = msgs[1]["content"]
        if not re.search(r"not say|cannot find", a):  # the answer's content words must come from the notes or question
            src = set(re.findall(r"[a-z0-9]+", (notes + " " + q).lower()))
            new = [x for x in re.findall(r"[a-z0-9]+", a.lower()) if x not in src]
            if len(new) > 4:
                return no("answer not from notes")
    return True


def filter_all():
    vocab = simple_vocab()
    why, seen, out, total = collections.Counter(), set(), [], 0
    for p in sorted(glob.glob(os.path.join(OUT, "round*.jsonl"))):
        for l in open(p, encoding="utf-8"):
            total += 1
            c = json.loads(l)
            for m in c["messages"]:  # curly quotes and long dashes to plain keyboard characters
                for x, y in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "-"), ("–", "-")):
                    m["content"] = m["content"].replace(x, y)
            key = re.sub(r"[^a-z0-9]+", " ", c["messages"][0]["content"].lower()).strip()
            akey = re.sub(r"[^a-z0-9]+", " ", c["messages"][1]["content"].lower()).strip()
            if key in seen or (len(akey) > 25 and akey in seen):
                why["duplicate"] += 1
                continue
            if clean(c, vocab, why):
                seen.add(key); seen.add(akey); out.append(c)
    with open(os.path.join(OUT, "clean.jsonl"), "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c) + "\n")
    kinds = collections.Counter(c["kind"] for c in out)
    print(f"kept {len(out)} of {total}", dict(kinds), "dropped:", dict(why))
    json.dump(dict(total=total, kept=len(out), kinds=kinds, dropped=why), open(os.path.join(OUT, "filter_stats.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["gen", "filter"])
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--minutes", type=float, default=90)
    ap.add_argument("--weights", default="")
    a = ap.parse_args()
    if a.what == "gen":
        gen(a.round, a.minutes, json.load(open(a.weights)) if a.weights else WEIGHTS)
    else:
        filter_all()

"""Programmatic training data for the job: notes answers, formats, instructions, simple maths, tool calls.

  python gen_job.py --n 300000 --seed 0     writes data/raw/job/job.jsonl

Every line: {"kind": ..., "messages": [{"role": "user"|"assistant", "content": ...}, ...]}
Tool calls: the assistant writes a short free draft line, then one line of JSON
  {"tool": "calc", "input": "348 * 27"}   or   {"tool": "notes", "input": "dentist"}
The tool answer comes back as a user turn that starts with "Result:" and the assistant then answers.

No scoreboard prompt may appear here: any conversation whose user text matches a scoreboard
prompt, or that uses one of the scoreboard's note lines, is dropped.
"""
import argparse
import json
import os
import random
import re

from scoreboard_prompts import GROUPS

R = random.Random(0)
pick = lambda s: R.choice(s)

NAMES = ("Ava Noah Mia Leo Zoe Max Ivy Eli Ruby Finn Lily Jack Emma Owen Nora Luke Ella Ryan Chloe Adam Grace Ethan "
         "Maya Oscar Sofia Henry Clara Jude Tess Milo Rosa Dan Kim Omar Priya Chen Aisha Pablo Yuki Ines Tariq Hana "
         "Bella Carl Dora Felix Gina Hugo Iris Kyle Lena Nick Olive Paul Quinn Rita Seth Tara Vera Wade").split()
DAYS = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
MONTHS = "January February March April May June July August September October November December".split()
COLOURS = "red blue green yellow orange purple pink brown black white grey gold silver".split()
ANIMALS = ("dog cat cow horse pig sheep goat duck hen rabbit mouse fox bear lion tiger wolf deer frog owl bee ant "
           "monkey zebra panda koala camel snake whale shark dolphin crab seal turtle eagle parrot penguin").split()
FRUITS = "apple banana orange pear grape mango peach plum cherry lemon melon strawberry kiwi pineapple lime".split()
VEG = "carrot potato tomato onion pea bean corn cabbage pumpkin pepper lettuce".split()
TOYS = "ball doll kite teddy bear, puzzle, robot, yo-yo, train set, toy car, drum, jump rope, building blocks".replace(",", "").split()
TOYS = ["ball", "doll", "kite", "teddy bear", "puzzle", "robot", "yo-yo", "train set", "toy car", "drum",
        "jump rope", "toy block", "spinning top", "toy boat", "marble"]
KITCHEN = ["spoon", "fork", "knife", "plate", "cup", "bowl", "pan", "pot", "stove", "fridge", "sink", "kettle",
           "oven", "table", "jug", "toaster"]
PARK = ["swing", "slide", "bench", "tree", "pond", "path", "flower bed", "sandbox", "fountain", "grass", "duck pond"]
SCHOOL = ["desk", "chair", "book", "pencil", "ruler", "board", "bag", "clock", "map", "crayon", "eraser"]
CLOTHES = ["hat", "coat", "sock", "shoe", "shirt", "scarf", "glove", "dress", "boot", "jumper"]
WEATHER = ["rain", "snow", "wind", "sun", "fog", "cloud", "storm", "hail"]
BODY = ["hand", "foot", "arm", "leg", "eye", "ear", "nose", "mouth", "knee", "toe"]
ROOMS = ["kitchen", "bedroom", "bathroom", "hall", "garden", "garage", "attic", "living room"]
SHOP = ["bread", "milk", "eggs", "rice", "tea", "soap", "cheese", "butter", "apples", "jam", "salt", "flour",
        "juice", "pasta", "honey", "stamps", "batteries", "paper", "glue", "candles"]
PLACES = ["the park", "the zoo", "the beach", "the farm", "the museum", "the lake", "the library", "the market",
          "the pool", "the cinema", "the forest", "the castle"]
STREETS = ["Oak Street", "Mill Lane", "Hill Road", "Park Road", "River Street", "Church Lane", "King Street",
           "Rose Lane", "Bridge Road", "Lake Street", "High Street", "Elm Road"]
JOBS = ["dentist", "doctor", "vet", "barber", "plumber", "teacher", "piano lesson", "swim class", "dance class",
        "art club", "choir", "book club", "chess club", "eye test", "haircut"]
PETS = ["cat", "dog", "rabbit", "hamster", "parrot", "fish", "turtle", "pony"]
PETNAMES = ["Biscuit", "Shadow", "Coco", "Luna", "Rex", "Toffee", "Bubbles", "Smoky", "Ginger", "Patch", "Daisy",
            "Bruno", "Olive", "Peanut", "Misty"]
FOODS = ["pizza", "soup", "pasta", "rice", "pancakes", "salad", "toast", "curry", "noodles", "fish and chips"]
DRINKS = ["tea", "coffee", "milk", "juice", "water", "cocoa", "lemonade"]
HIDE = ["under the mat", "in the top drawer", "behind the clock", "in the red box", "on the top shelf",
        "under the big stone", "in the shed", "inside the old boot", "next to the lamp", "in the kitchen jar"]
CATS = {"colours": COLOURS, "animals": ANIMALS, "fruits": FRUITS, "vegetables": VEG, "toys": TOYS,
        "things in a kitchen": KITCHEN, "things in a park": PARK, "things in a school": SCHOOL,
        "clothes": CLOTHES, "kinds of weather": WEATHER, "parts of the body": BODY, "rooms in a house": ROOMS,
        "days of the week": DAYS, "months": MONTHS, "foods": FOODS, "drinks": DRINKS, "pets": PETS}
NUMW = "zero one two three four five six seven eight nine ten".split()
OPPOSITES = [("hot", "cold"), ("big", "small"), ("up", "down"), ("fast", "slow"), ("happy", "sad"), ("wet", "dry"),
             ("day", "night"), ("open", "closed"), ("tall", "short"), ("full", "empty"), ("hard", "soft"),
             ("light", "dark"), ("early", "late"), ("near", "far"), ("old", "new"), ("clean", "dirty"),
             ("loud", "quiet"), ("heavy", "light"), ("thick", "thin"), ("in", "out"), ("left", "right"),
             ("first", "last"), ("win", "lose"), ("push", "pull"), ("start", "stop"), ("young", "old")]
ONEWORD = [("what colour is grass", "Green"), ("what colour is snow", "White"), ("what colour is a banana", "Yellow"),
           ("what animal says woof", "Dog"), ("what animal says moo", "Cow"), ("what animal says quack", "Duck"),
           ("what animal says oink", "Pig"), ("what animal says baa", "Sheep"), ("what do bees make", "Honey"),
           ("what do you drink when you are thirsty", "Water"), ("what comes after Monday", "Tuesday"),
           ("what comes after Friday", "Saturday"), ("what do cows give us to drink", "Milk"),
           ("what shines in the sky at night", "Moon"), ("what shines in the sky in the day", "Sun"),
           ("what falls from clouds", "Rain"), ("what do you wear on your feet", "Shoes"),
           ("what do you wear on your head", "Hat"), ("what do you read", "Book"), ("what do hens lay", "Eggs"),
           ("what colour is the sun", "Yellow"), ("what colour is coal", "Black"), ("what is frozen water called", "Ice"),
           ("what animal has a very long neck", "Giraffe"), ("what animal has a trunk", "Elephant"),
           ("what do you sleep in", "Bed"), ("what do you use to cut paper", "Scissors"),
           ("what season comes after winter", "Spring"), ("what season is the hottest", "Summer"),
           ("what colour is a carrot", "Orange"), ("what is the first month of the year", "January"),
           ("what do you sit on", "Chair"), ("how many days are in a week", "Seven")]
YESNO = [("is the sun hot", True), ("is snow cold", True), ("can birds fly", True), ("can fish swim", True),
         ("is water wet", True), ("do dogs bark", True), ("is grass green", True), ("do cows eat grass", True),
         ("is the moon in the sky", True), ("do cats have tails", True), ("is night dark", True),
         ("is sugar sweet", True), ("do trees have leaves", True), ("is a mouse small", True),
         ("can a rock talk", False), ("is snow hot", False), ("can pigs fly", False), ("do fish walk", False),
         ("is the sea dry", False), ("is an elephant small", False), ("do cats bark", False),
         ("is a lemon sweet", False), ("can a chair run", False), ("is the sun cold", False),
         ("do dogs have wings", False), ("is night bright like day", False), ("can a fish climb a tree", False),
         ("is fire cold", False), ("is ice warm", False), ("do cars eat food", False)]
TOPICS = (ANIMALS + FRUITS + WEATHER + ["the moon", "the sun", "the sea", "a tree", "a river", "a garden", "a bus",
          "a train", "a boat", "a house", "a school", "a friend", "a farm", "a kite", "a picnic", "a rainy day",
          "a birthday", "a storm", "a mountain", "a bridge", "a lamp", "a clock", "a window", "a door", "a road"])
WORDS = ["river", "garden", "window", "basket", "candle", "ladder", "pillow", "rocket", "puddle", "blanket",
         "lantern", "feather", "bucket", "mirror", "ribbon", "pebble", "castle", "bridge", "kitten", "forest",
         "button", "whistle", "bottle", "hammer", "island", "tunnel", "meadow", "cookie", "jacket", "wagon",
         "train", "cloud", "apple", "boat", "drum", "star", "sock", "lamp", "nest", "bell", "kite", "moon"]
SENT = ["The {a} is in the {r}.", "I can see a {c} {a}.", "The {a} likes the {w}.", "We went to {p} on {d}.",
        "My {t} is {c}.", "The {c} {t} is on the {k}.", "{n} has a {c} {t}.", "{n} saw a {a} at {p}.",
        "I like {f} very much.", "The {w} came on {d}.", "A {a} ran past the {k2}.", "{n} put the {t} in the {r}.",
        "There is a {f} on the {k}.", "The {k2} is by the {k}.", "{n} and {n2} went to {p}."]


def cap(s):
    return s[:1].upper() + s[1:]


def plural(w):
    irr = {"sheep": "sheep", "mouse": "mice", "fish": "fish", "deer": "deer", "fox": "foxes", "wolf": "wolves",
           "foot": "feet", "bench": "benches", "cherry": "cherries", "strawberry": "strawberries", "potato": "potatoes",
           "tomato": "tomatoes", "peach": "peaches", "box": "boxes", "glass": "glasses", "bus": "buses",
           "pony": "ponies", "dress": "dresses", "knife": "knives", "puppy": "puppies", "brush": "brushes"}
    if w in irr:
        return irr[w]
    return w + "s"


def sentence():
    return pick(SENT).format(a=pick(ANIMALS), r=pick(ROOMS), c=pick(COLOURS), w=pick(WEATHER), p=pick(PLACES),
                             d=pick(DAYS), t=pick(TOYS), k=pick(KITCHEN), k2=pick(PARK), n=pick(NAMES),
                             n2=pick(NAMES), f=pick(FRUITS))


def general(t):
    """A topic as you would say it after 'I like' or 'tell me about': dogs, plums, rain, the moon, boats."""
    if t in WEATHER or t.startswith("the "):
        return t
    if t.startswith(("a ", "an ")):
        return plural(re.sub(r"^(a|an) ", "", t))
    return plural(t)


def about(topic):
    """A short simple sentence about a topic, used for free writing tasks."""
    g = general(topic)
    are = "is" if (topic in WEATHER or topic.startswith("the ")) else "are"
    return pick([f"I like {g}.", f"{cap(g)} {are} nice to see.", f"We talked about {g} today.",
                 f"{cap(g)} can make a day special.", f"Many people like {g}.", f"I think about {g} a lot."])


def conv(kind, *turns):
    return {"kind": kind, "messages": [{"role": "user" if i % 2 == 0 else "assistant", "content": t}
                                       for i, t in enumerate(turns)]}


# ------------------------------------------------------------------ notes
def time_str():
    h = R.randint(1, 12)
    return f"{h} {pick(['am', 'pm'])}" if R.random() < 0.7 else f"{h}:{pick(['15', '30', '45'])} {pick(['am', 'pm'])}"


def make_note():
    """Returns (note line, [(question, answer sentence, search words)], topic word)."""
    k = R.randrange(16)
    n, n2 = R.sample(NAMES, 2)
    if k == 0:
        j, d, t = pick(JOBS), pick(DAYS), time_str()
        return (f"{cap(j)} on {d} at {t}.", [(f"when is the {j}?", f"The {j} is on {d} at {t}.", j),
                                            (f"what day is the {j}?", f"The {j} is on {d}.", j),
                                            (f"what time is the {j}?", f"The {j} is at {t}.", j)], j)
    if k == 1:
        items = R.sample(SHOP, R.randint(2, 3))
        lst = " and ".join(items) if len(items) == 2 else f"{items[0]}, {items[1]} and {items[2]}"
        return (f"Buy {lst}.", [("what do I need to buy?", f"You need to buy {lst}.", "buy"),
                               ("what is on my shopping list?", f"Your list has {lst}.", "buy")], "buy")
    if k == 2:
        d, m = R.randint(1, 28), pick(MONTHS)
        who = pick([f"{n}'s", "Dad's", "Grandpa's", "Aunt " + n2 + "'s", "Uncle " + n2 + "'s"])
        return (f"{who} birthday is on {d} {m}.", [(f"when is {who} birthday?", f"{who} birthday is on {d} {m}.", "birthday")], "birthday")
    if k == 3:
        thing, h = pick(["key", "torch", "map", "ticket", "spare phone", "passport", "tool box", "first aid kit"]), pick(HIDE)
        return (f"The {thing} is {h}.", [(f"where is the {thing}?", f"The {thing} is {h}.", thing.split()[-1])], thing.split()[-1])
    if k == 4:
        w = pick(["wifi", "gate", "locker", "bike lock", "alarm"]) ; code = pick(WORDS) + str(R.randint(10, 99))
        word = "password" if w == "wifi" else "code"
        return (f"The {w} {word} is {code}.", [(f"what is the {w} {word}?", f"The {w} {word} is {code}.", w.split()[0])], w.split()[0])
    if k == 5:
        what = pick(["bike", "garden fence", "school trip", "party", "car", "holiday", "book", "broken tap"])
        return (f"Call {n} about the {what}.", [(f"who should I call about the {what}?", f"You should call {n}.", what.split()[-1])], what.split()[-1])
    if k == 6:
        pl, t = pick(["library", "shop", "bank", "pool", "post office", "bakery", "museum", "cafe"]), time_str()
        oc = pick(["opens", "closes"])
        return (f"The {pl} {oc} at {t}.", [(f"when does the {pl} {oc[:-1]}?", f"The {pl} {oc} at {t}.", pl.split()[-1])], pl.split()[-1])
    if k == 7:
        p, pn = pick(PETS), pick(PETNAMES)
        return (f"{n}'s {p} is called {pn}.", [(f"what is the name of {n}'s {p}?", f"{n}'s {p} is called {pn}.", p),
                                              (f"what is {n}'s {p} called?", f"It is called {pn}.", p)], p)
    if k == 8:
        num, pl = R.randint(2, 99), pick(["town", "school", "the station", "the beach", "the hospital", "the airport"])
        return (f"The bus to {pl} is number {num}.", [(f"which bus goes to {pl}?", f"Bus number {num} goes to {pl}.", "bus")], "bus")
    if k == 9:
        ev, pl = pick(["school trip", "class picnic", "family holiday", "work party", "team day out"]), pick(PLACES)
        return (f"The {ev} is to {pl}.", [(f"where is the {ev} going?", f"The {ev} is going to {pl}.", ev.split()[-1])], ev.split()[-1])
    if k == 10:
        ev, r = pick(["meeting", "class", "lesson", "club", "exam", "talk"]), R.randint(1, 40)
        return (f"The {ev} is in room {r}.", [(f"which room is the {ev} in?", f"The {ev} is in room {r}.", ev)], ev)
    if k == 11:
        dr, ex = pick(DRINKS), pick(["honey", "sugar", "lemon", "milk", "ice", "mint"])
        return (f"{n} likes {dr} with {ex}.", [(f"what does {n} like in {dr}?", f"{n} likes {ex} in {dr}.", n),
                                              (f"how does {n} like {dr}?", f"{n} likes {dr} with {ex}.", n)], n)
    if k == 12:
        v, s = pick(["car", "bike", "van", "scooter"]), pick(STREETS)
        return (f"The {v} is parked on {s}.", [(f"where is the {v} parked?", f"The {v} is parked on {s}.", v)], v)
    if k == 13:
        job, d = pick(["Water the plants", "Take out the bins", "Feed the fish", "Clean the car", "Wash the towels",
                       "Walk the dog", "Pay the rent", "Return the books"]), pick(DAYS)
        key = job.split()[-1]
        return (f"{job} on {d}.", [(f"when should I {job.lower()}?", f"You should {job.lower()} on {d}.", key)], key)
    if k == 14:
        who, d, how = pick(["Grandpa", "Aunt " + n, "Uncle " + n, "Cousin " + n, n]), pick(DAYS), pick(["bus", "train", "car", "plane", "boat"])
        return (f"{who} arrives on {d} by {how}.", [(f"how is {who} travelling?", f"{who} is travelling by {how}.", who.split()[-1]),
                                                   (f"when does {who} arrive?", f"{who} arrives on {d}.", who.split()[-1])], who.split()[-1])
    food, num, ing = pick(["soup", "bread", "pie", "pancake mix", "stew", "salad"]), R.randint(2, 9), pick(["eggs", "carrots", "apples", "cups of flour", "onions", "spoons of sugar"])
    return (f"The {food} needs {NUMW[num]} {ing}.", [(f"how many {ing} does the {food} need?", f"The {food} needs {NUMW[num]} {ing}.", food.split()[0])], food.split()[0])


MISSING = ["The notes do not say {x}.", "I cannot find that in the notes.", "The notes do not say anything about that.",
           "That is not in the notes."]
ASK_NOTES = ["Using the notes, {q}", "From the notes, {q}", "Look at the notes. {Q}", "{Q} Use the notes.",
             "According to the notes, {q}", "{Q}"]


def note_set(n):
    out, seen = [], set()
    while len(out) < n:
        nt = make_note()
        if nt[2] not in seen:
            seen.add(nt[2]); out.append(nt)
    return out


def gen_notes_inline():
    notes = note_set(R.randint(2, 6))
    head = pick(["Notes:", "Notes:", "My notes:", "Here are my notes:"])
    block = head + "\n" + "\n".join("- " + n[0] for n in notes) + "\n\n"
    turns = []
    for i in range(R.choice([1, 1, 1, 2])):
        if R.random() < 0.2:  # a question the notes cannot answer
            other = make_note()
            while any(other[2] == n[2] for n in notes):
                other = make_note()
            q, ans = pick(other[1])[0], pick(MISSING).format(x="that")
        else:
            q, ans, _ = pick(pick(notes)[1])
        ask = pick(ASK_NOTES).format(q=q, Q=cap(q))
        turns += [(block if i == 0 else "") + ask, ans]
    return conv("notes_inline", *turns)


# ------------------------------------------------------------------ maths
def direct_problem():
    """Small sums the assistant answers by itself. Returns (question, answer text)."""
    k = R.randrange(10)
    if k < 3:
        a, b = R.randint(0, 60), R.randint(0, 60)
        q, r, say = pick([f"What is {a} + {b}?", f"What is {a} plus {b}?", f"{a} + {b} = ?", f"Add {a} and {b}."]), a + b, f"{a} + {b} = {a + b}"
    elif k < 5:
        a = R.randint(1, 99); b = R.randint(0, a)
        q, r, say = pick([f"What is {a} - {b}?", f"What is {a} minus {b}?", f"{a} - {b} = ?", f"Take {b} away from {a}."]), a - b, f"{a} - {b} = {a - b}"
    elif k < 7:
        a, b = R.randint(0, 12), R.randint(0, 12)
        q, r, say = pick([f"What is {a} times {b}?", f"What is {a} x {b}?", f"{a} x {b} = ?", f"Multiply {a} by {b}."]), a * b, f"{a} x {b} = {a * b}"
    elif k < 8:
        b = R.randint(1, 12); r = R.randint(1, 12); a = b * r
        q, say = pick([f"What is {a} divided by {b}?", f"{a} / {b} = ?", f"Divide {a} by {b}."]), f"{a} / {b} = {r}"
    else:
        return word_problem()
    ans = pick([f"{r}.", f"The answer is {r}.", say + ".", f"It is {r}."])
    return q, ans


def word_problem():
    n, n2 = R.sample(NAMES, 2)
    thing = pick(["apples", "balloons", "books", "stickers", "marbles", "cookies", "pencils", "shells", "coins", "flowers"])
    k = R.randrange(5)
    if k == 0:
        a, b = R.randint(1, 30), R.randint(1, 30)
        return (f"{n} has {a} {thing}. {pick(['He', 'She', n])} gets {b} more. How many {thing} does {n} have now?",
                f"{a} + {b} = {a + b}. {n} has {a + b} {thing} now.")
    if k == 1:
        a = R.randint(2, 40); b = R.randint(1, a - 1)
        v = pick(["gives away", "loses", "eats" if thing in ("apples", "cookies") else "gives away"])
        return (f"{n} had {a} {thing} and {v} {b}. How many {thing} are left?", f"{a} - {b} = {a - b}. There are {a - b} {thing} left.")
    if k == 2:
        a, b = R.randint(2, 10), R.randint(2, 10)
        box = pick(["bag", "box", "basket", "jar"])
        return (f"A {box} has {a} {thing}. How many {thing} are in {b} {box}{'es' if box == 'box' else 's'}?",
                f"{b} x {a} = {a * b}. There are {a * b} {thing}.")
    if k == 3:
        b = R.randint(2, 6); r = R.randint(1, 10)
        return (f"{n} shares {b * r} {thing} equally between {b} friends. How many {thing} does each friend get?",
                f"{b * r} / {b} = {r}. Each friend gets {r} {thing}.")
    a, b = R.randint(1, 20), R.randint(1, 20)
    an = pick(ANIMALS)
    return (f"There are {a} {plural(an)} in a field. {b} more {plural(an)} come. How many {plural(an)} are there now?",
            f"{a} + {b} = {a + b}. There are {a + b} {plural(an)} now.")


def gen_arith():
    turns = []
    for _ in range(R.choice([1, 1, 2, 3])):
        turns += list(direct_problem())
    return conv("arith", *turns)


DRAFT_CALC = ["I will use the calculator.", "Let me use the calculator.", "That is a big sum, so I will use the calculator.",
              "I need the calculator for this.", "Let me work that out with the calculator."]
DRAFT_NOTES = ["I will look in your notes.", "Let me check your notes.", "I will search your notes.",
               "Let me look that up in your notes."]


def call(tool, inp):
    return json.dumps({"tool": tool, "input": inp})


def fmt_num(x):
    return str(int(x)) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def gen_calc():
    k = R.randrange(8)
    forced = R.random() < 0.35
    n = pick(NAMES)
    if k < 2:
        a, b = R.randint(100, 9999), R.randint(100, 9999); e, v = f"{a} + {b}", a + b
        q = pick([f"What is {a} + {b}?", f"What is {a} plus {b}?", f"Add {a} and {b}."]); fin = f"{a} + {b} = {v}."
    elif k < 4:
        a = R.randint(200, 20000); b = R.randint(100, a); e, v = f"{a} - {b}", a - b
        q = pick([f"What is {a} - {b}?", f"What is {a} minus {b}?", f"Take {b} away from {a}."]); fin = f"{a} - {b} = {v}."
    elif k < 6:
        a, b = R.randint(13, 999), R.randint(13, 99); e, v = f"{a} * {b}", a * b
        q = pick([f"What is {a} times {b}?", f"What is {a} x {b}?", f"Multiply {a} by {b}."]); fin = f"{a} times {b} is {v}."
    elif k < 7:
        b = R.randint(3, 99); r = R.randint(13, 999); a = b * r; e, v = f"{a} / {b}", r
        q = pick([f"What is {a} divided by {b}?", f"Divide {a} by {b}."]); fin = f"{a} divided by {b} is {v}."
    else:
        a, b = R.randint(12, 250), R.randint(12, 99)
        thing = pick(["pencils", "seeds", "bricks", "beads", "pages", "coins", "tiles", "stamps"])
        if R.random() < 0.5:
            q = f"I bought {b} boxes with {a} {thing} in each box. How many {thing} is that?"; fin = f"That is {a * b} {thing}."
            e = f"{b} * {a}"
        else:
            q = f"A {pick(['ticket', 'book', 'toy', 'plant'])} costs {a} coins. How much do {b} of them cost?"; fin = f"They cost {a * b} coins."
            e = f"{a} * {b}"
        v = a * b
    if forced:
        q = pick(["Use the calculator: ", "Use the calculator. ", "With the calculator, "]) + (q[0].lower() + q[1:] if not q.startswith("I ") else q)
        if R.random() < 0.3:  # sometimes even an easy sum is asked for with the calculator
            a, b = R.randint(2, 30), R.randint(2, 30)
            q, e, v, fin = f"Use the calculator: what is {a} + {b}?", f"{a} + {b}", a + b, f"{a} + {b} = {a + b}."
    return conv("tool_calc", q, pick(DRAFT_CALC) + "\n" + call("calc", e), f"Result: {fmt_num(v)}", fin)


ASK_TOOL = ["Look in my notes: {q}", "Check my notes and tell me {q}", "Check my notes. {Q}", "Look in my notes. {Q}",
            "Search my notes: {q}", "My notes should say this: {q}", "Please look in my notes. {Q}"]
ASK_ABOUT = ["What do my notes say about {t}?", "Did I write a note about {t}?", "Is there a note about {t}?",
             "Find my note about {t}.", "Do my notes say anything about {t}?"]


def gen_notes_tool():
    note, qas, key = make_note()
    q, ans, word = pick(qas)
    topic = word if word[0].isupper() else ("the " + word if word not in ("buy",) else "shopping")
    if R.random() < 0.6:
        ask = pick(ASK_TOOL).format(q=q, Q=cap(q))
    else:
        ask = pick(ASK_ABOUT).format(t=topic); ans = "Yes. Your note says: " + note if R.random() < 0.5 else ans
    query = word.lower() if word != "buy" else "buy"
    first = pick(DRAFT_NOTES) + "\n" + call("notes", query)
    if R.random() < 0.15:
        return conv("tool_notes", ask, first, "Result: nothing found", pick(["I could not find a note about that.",
                    "There is no note about that.", "Your notes do not say anything about that."]))
    extra = [make_note()[0] for _ in range(R.choice([0, 0, 1]))]
    lines = [note] + [x for x in extra if word.lower() in x.lower()]
    return conv("tool_notes", ask, first, "Result:\n" + "\n".join("- " + l for l in lines), ans)


# ------------------------------------------------------------------ formats and instructions
def gen_format():
    k = R.randrange(17)
    cat = pick(list(CATS)); items = CATS[cat]
    if k < 3:
        n = R.randint(2, min(6, len(items))); ch = R.sample(items, n)
        q = pick([f"List {NUMW[n]} {cat} as a numbered list.", f"Give me a numbered list of {NUMW[n]} {cat}.",
                  f"Write {n} {cat} as a numbered list.", f"Numbered list, {NUMW[n]} {cat}."])
        return conv("format", q, "\n".join(f"{i + 1}. {cap(c)}" for i, c in enumerate(ch)))
    if k < 5:
        n = R.randint(2, min(5, len(items))); ch = R.sample(items, n)
        q = pick([f"List {NUMW[n]} {cat}. Put a dash at the start of each line.", f"Write {NUMW[n]} {cat} as a list with dashes.",
                  f"Give me {n} {cat}, one per line, with a dash before each."])
        return conv("format", q, "\n".join(f"- {cap(c)}" for c in ch))
    if k == 5:
        w = pick([pick(WORDS), pick(ANIMALS), sentence().rstrip(".").lower(), pick(["good night", "thank you", "happy birthday", "well done", "see you soon"])])
        q = pick([f"Write the word {w} in capital letters.", f"Write this in capital letters: {w}", f"Put this in capitals: {w}"]) if " " not in w or R.random() < 0.7 else f"Write this in capital letters: {w}"
        return conv("format", q, w.upper())
    if k == 6:
        n = R.randint(5, 12); t0 = pick(TOPICS); t = general(t0)
        defs = {"rain": "Rain is water falling from clouds.", "snow": "Snow is soft frozen water.", "wind": "Wind is moving air."}
        q = pick([f"In fewer than {NUMW[n] if n <= 10 else n} words, tell me about {t}.", f"Tell me about {t} in fewer than {n} words."])
        are = "is" if (t0 in WEATHER or t0.startswith("the ")) else "are"
        return conv("format", q, defs.get(t0, pick([f"I like {t}.", f"{cap(t)} {are} nice.", f"{cap(t)} {are} fun to see."])))
    if k == 7:
        n = R.randint(2, 4)
        q = pick([f"Write exactly {NUMW[n]} lines. Each line is one short sentence.", f"Write {NUMW[n]} short sentences, one per line."])
        return conv("format", q, "\n".join(sentence() for _ in range(n)))
    if k == 8:
        n = R.randint(2, 5); ch = R.sample(items, min(n, len(items)))
        q = pick([f"Write {NUMW[len(ch)]} lines. Each line has only one word.", f"Write {NUMW[len(ch)]} {cat}, one word per line."])
        ch = [c for c in ch if " " not in c] or ["sun"]
        if len(ch) != n:
            return gen_format()
        return conv("format", q, "\n".join(cap(c) for c in ch))
    if k == 9:
        t = general(pick(TOPICS))
        q = pick([f"Write about {t} as a question and an answer. Start the first line with Q: and the second line with A:",
                  f"Give me one question and one answer about {t}. Use Q: and A: at the start of the lines."])
        return conv("format", q, f"Q: Do you like {t}?\nA: Yes, I like {t} very much.")
    if k == 10:
        n = R.randint(2, 5); t = general(pick(TOPICS))
        q = pick([f"Write a poem about {t} with exactly {NUMW[n]} lines.", f"Write a {NUMW[n]} line poem about {t}."])
        pool = [f"I look at {t} and I smile,", "The day is soft and slow,", "The wind is singing low,", "I stay here for a while,",
                "The sky is wide and bright,", "It fills me with delight,", "The stars come out at night,", "And everything feels right."]
        return conv("format", q, "\n".join(R.sample(pool, n)))
    if k == 11:
        ask, ans = pick([("Tell me your favourite colour.", f"My favourite colour is {pick(COLOURS)}."), ("Tell me a nice word.", f"{cap(pick(WORDS))}."),
                         ("Say hello to me.", "Hello, friend!"), ("Tell me your favourite animal.", f"I like the {pick(ANIMALS)} best.")])
        q = ask + " " + pick(["Put your whole reply inside quote marks.", "Put quote marks around your reply.", "Write your reply inside quote marks."])
        return conv("format", q, f'"{ans}"')
    if k == 12:
        a = R.randint(1, 20); b = a + R.randint(2, 7)
        sep, name = pick([(", ", "commas"), (" - ", "dashes"), (" ", "spaces")])
        return conv("format", f"Write the numbers from {a} to {b} with {name} between them.", sep.join(str(i) for i in range(a, b + 1)) if name != "dashes" else "-".join(str(i) for i in range(a, b + 1)))
    if k == 13:
        ch = R.sample(items, min(R.randint(2, 4), len(items)))
        lst = ", ".join(cap(c) for c in ch[:-1]) + " and " + cap(ch[-1])
        return conv("format", f"Write {lst}, one per line.", "\n".join(cap(c) for c in ch))
    if k == 14:
        w = pick([x for x in WORDS + ANIMALS + FRUITS if " " not in x and len(x) <= 7])
        return conv("format", pick([f"Spell the word {w} with a dash between each letter.", f"Spell {w} with dashes between the letters."]), "-".join(w))
    if k == 15:
        s = sentence().rstrip(".")
        mark, name = pick([("!", "an exclamation mark"), ("?", "a question mark"), (".", "a full stop")])
        if mark == "?":
            s = pick(["Do you like the " + pick(ANIMALS), "Is the " + pick(TOYS) + " " + pick(COLOURS), "Can we go to " + pick(PLACES)])
        return conv("format", f"Write one sentence and end it with {name}.", s + mark)
    q, a = pick([("How many legs does a dog have?", 4), ("How many legs does a bird have?", 2), ("How many days are in a week?", 7),
                 ("How many wheels does a bike have?", 2), ("How many wheels does a car have?", 4), ("How many legs does a spider have?", 8),
                 ("How many months are in a year?", 12), ("How many fingers are on one hand?", 5), ("How many eyes does a person have?", 2),
                 ("How many sides does a triangle have?", 3), ("How many sides does a square have?", 4), ("How many legs does a horse have?", 4)])
    return conv("format", q + " " + pick(["Answer with a single number.", "Reply with just the number.", "Give only the number."]), str(a))


def gen_instruction():
    k = R.randrange(16)
    if k == 0:
        q, a = pick(ONEWORD)
        return conv("instr", pick([f"Answer with one word: {q}?", f"{cap(q)}? Answer with one word.", f"In one word, {q}?"]), a + ".")
    if k == 1:
        q, a = pick(YESNO)
        return conv("instr", pick([f"Answer only yes or no: {q}?", f"{cap(q)}? Answer yes or no.", f"Yes or no: {q}?"]), "Yes." if a else "No.")
    if k == 2:
        w, n = pick(WORDS + ANIMALS + FRUITS), R.randint(2, 5)
        times = {2: "two times", 3: "three times", 4: "four times", 5: "five times"}[n]
        return conv("instr", pick([f"Say the word {w} {times}.", f"Say {w} {times}.", f"Repeat the word {w} {times}."]), " ".join([w] * n))
    if k == 3:
        w = pick(WORDS + ANIMALS + TOYS)
        s = pick([f"The {w} was by the door.", f"I saw a {w} today.", f"We found the {w} in the garden.", f"She gave me a {w}.", f"There is a {w} on the hill."])
        return conv("instr", pick([f"Write one sentence that uses the word {w}.", f"Use the word {w} in one sentence.", f"Make one sentence with the word {w}."]), s)
    if k == 4:
        n = R.randint(2, 4); t = pick(ANIMALS + TOYS + FRUITS)
        pool = [f"The {t} is {pick(COLOURS)}.", f"I like the {t}.", f"The {t} is in the {pick(ROOMS)}.", f"{pick(NAMES)} has a {t}.",
                f"We saw the {t} at {pick(PLACES)}.", f"The {t} is very nice."]
        return conv("instr", pick([f"Write {NUMW[n]} sentences about a {t}.", f"Tell me about a {t} in {NUMW[n]} sentences."]), " ".join(R.sample(pool, n)))
    if k == 5:
        n = R.randint(2, 7)
        words = {2: ["Hello there", "Good morning", "Thank you"], 3: ["I like cats", "Here you go", "Have a nice", "The sun shines"],
                 4: ["I am happy today", "The sky is blue", "Here are four words"], 5: ["I like to read books", "The cat sat down quietly", "Today is a good day"],
                 6: ["I like to play in parks", "The dog ran across the field"], 7: ["I like to walk in the green park", "The little bird sang a very sweet song"]}
        return conv("instr", pick([f"Reply with exactly {NUMW[n]} words.", f"Answer in exactly {NUMW[n]} words.", f"Say something with exactly {NUMW[n]} words."]), pick(words[n]))
    if k == 6:
        cat = pick(["fruit", "animal", "colour", "toy", "day of the week", "month", "vegetable", "drink", "animal that lives on a farm", "pet"])
        pool = {"fruit": FRUITS, "animal": ANIMALS, "colour": COLOURS, "toy": TOYS, "day of the week": DAYS, "month": MONTHS,
                "vegetable": VEG, "drink": DRINKS, "animal that lives on a farm": ["cow", "pig", "sheep", "hen", "goat", "horse", "duck"], "pet": PETS}[cat]
        return conv("instr", pick([f"Tell me the name of a {cat}. Reply with just the name.", f"Name a {cat}. Reply with just the name.", f"Name one {cat}. Just the name, please."]), cap(pick(pool)))
    if k == 7:
        w, about_ = pick([("dog", "a pet that barks"), ("rain", "water that falls from the sky"), ("sun", "the big light in the day sky"),
                          ("bed", "the place where you sleep"), ("fish", "an animal that swims"), ("tree", "a tall plant with leaves"),
                          ("moon", "the light in the night sky"), ("book", "a thing you read"), ("milk", "a white drink"), ("bird", "an animal that flies")])
        ans = {"dog": "It is a friendly pet with four legs. It wags its tail when it is happy.", "rain": "It comes down from grey clouds. It makes the ground wet.",
               "sun": "It is bright and warm. It comes up every morning.", "bed": "It is soft and cosy. You rest there at night.",
               "fish": "It lives in water. It has fins and a tail.", "tree": "It grows tall and gives shade. Many animals live in it.",
               "moon": "It glows softly at night. Sometimes it is round.", "book": "It has pages with words and pictures. It tells a story.",
               "milk": "It comes from cows. Many children like it with breakfast.", "bird": "It has wings and feathers. It sings in the morning."}[w]
        return conv("instr", pick([f"Tell me about {about_}, but do not use the word {w}.", f"Do not use the word {w}. Tell me about {about_}."]), ans)
    if k == 8:
        t = pick(["my day", "my pet", "my weekend", "my school", "my lunch", "my friend", "my garden", "my trip"])
        a = {"my day": "How was your day today?", "my pet": "What is the name of your pet?", "my weekend": "What did you do at the weekend?",
             "my school": "What do you like best at school?", "my lunch": "What did you have for lunch?", "my friend": "What is your friend like?",
             "my garden": "What grows in your garden?", "my trip": "Where did you go on your trip?"}[t]
        return conv("instr", pick([f"Ask me one question about {t}.", f"Ask me a question about {t}."]), a)
    if k == 9:
        w = pick(["goodbye", "thanks", "please", "hooray", "yes", "now", "today", "friend"])
        return conv("instr", pick([f"Tell me about the {pick(WEATHER)} and end your reply with the word {w}.", f"Say something nice and end your reply with the word {w}.",
                                   f"Tell me about {general(pick(TOPICS))} and end with the word {w}."]), pick(["It is a lovely thing to see", "I like it a lot", "It makes me smile every time"]) + f", {w}.")
    if k == 10:
        w = pick(["Sure", "Yes", "Okay", "Well", "Today", "Hello", "First"])
        t = pick(ANIMALS)
        return conv("instr", pick([f"Start your reply with the word {w} and then tell me about {plural(t)}.", f"Tell me about {plural(t)}. Start your reply with the word {w}."]),
                    f"{w}, {plural(t)} are {pick(['lovely', 'fun to watch', 'interesting', 'nice'])} animals.")
    if k in (11, 12):
        s = sentence()
        return conv("instr", pick([f"Repeat this exactly: {s}", f"Say this back to me exactly: {s}", f"Copy this sentence: {s}"]), s)
    if k == 13:
        a, b = pick(OPPOSITES)
        if R.random() < 0.5:
            a, b = b, a
        return conv("instr", pick([f"What is the opposite of {a}? Answer with one word.", f"Give me the opposite of {a} in one word.", f"Opposite of {a}? One word."]), cap(b) + ".")
    if k == 14:
        t = pick(TOPICS)
        return conv("instr", pick([f"Write one sentence about {general(t)}.", f"Tell me about {general(t)} in one sentence."]), about(t))
    q, a = direct_problem()
    return conv("instr", q + " " + pick(["Reply with just the number.", "Answer with only the number."]), re.findall(r"-?\d+", a)[-1])


GENS = [(gen_notes_inline, 0.20), (gen_arith, 0.18), (gen_calc, 0.12), (gen_notes_tool, 0.12), (gen_format, 0.20),
        (gen_instruction, 0.18)]

BANNED_PROMPTS = {p.strip().lower() for g in GROUPS.values() for p, _ in g}
_dev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "devset.json")
if os.path.exists(_dev):  # the dev set prompts are kept out of the training data too
    BANNED_PROMPTS |= {d["prompt"].strip().lower() for d in json.load(open(_dev, encoding="utf-8"))}
BANNED_LINES = {l[2:].strip().lower() for g in GROUPS.values() for p, _ in g for l in p.splitlines() if l.startswith("- ")}


def allowed(c):
    for m in c["messages"]:
        t = m["content"].strip().lower()
        if m["role"] == "user" and (t in BANNED_PROMPTS or any(b in t for b in BANNED_LINES)):
            return False
        last = t.split("\n\n")[-1]
        if m["role"] == "user" and last in {p.split("\n\n")[-1].strip().lower() for p in BANNED_PROMPTS}:
            return False
    return True


def build(n, seed, gens=None):
    R.seed(seed)
    fns, ws = zip(*(gens or GENS))
    out, seen, dropped = [], set(), 0
    while len(out) < n:
        c = R.choices(fns, ws)[0]()
        key = json.dumps(c["messages"])
        if key in seen:
            continue
        if not allowed(c):
            dropped += 1
            continue
        seen.add(key); out.append(c)
    return out, dropped


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--round", type=int, default=0, help="1 or more: use the wider generator set in gen_job_extra.py")
    ap.add_argument("--weights", default="", help="json: generator function name -> weight")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "job", "job.jsonl"))
    a = ap.parse_args()
    gens = None
    if a.round:
        import gen_job_extra
        gens = gen_job_extra.GENS2 if a.round >= 2 else gen_job_extra.GENS
    if a.weights:
        w = json.load(open(a.weights))
        gens = [(f, w.get(f.__name__, x)) for f, x in (gens or GENS)]
    data, dropped = build(a.n, a.seed, gens)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for c in data:
            f.write(json.dumps(c) + "\n")
    kinds = {}
    for c in data:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print("wrote", len(data), "dropped for matching the scoreboard", dropped, kinds)

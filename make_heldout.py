"""Stage 9: the held-out test. Written by hand BEFORE any model was run on it. Never train on it.

  python make_heldout.py          checks every item against a hand-written good and bad reply,
                                  then writes data/heldout.json and data/heldout.sha256 (once; it will not overwrite)

Each item: id, section, skill, prompt, notes (the notes store for the notes tool, may be empty),
check (see heldout.py hcheck), good (a reply that must pass), bad (a reply that must fail),
human (optional: what a person should judge, because the automatic check only sees the form).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "heldout.json")
HASH = os.path.join(HERE, "data", "heldout.sha256")

S1 = ["Dentist on Thursday at 3 pm.", "The wifi password is rocket42.", "Buy eggs, soap and rice.", "Mia's birthday is on 14 June.",
      "The key is behind the clock.", "The bus to the airport is number 27.", "Call Owen about the broken tap.",
      "The library closes at 6 pm.", "Water the plants on Friday.", "Leo's rabbit is called Toffee."]
S2 = ["The car service is booked for 9 March.", "Sam is allergic to peanuts.", "The spare tyre is in the garage loft.",
      "Rent is 450 coins a month.", "The neighbour's phone number is 555 0142.", "Flight to Rome leaves at 7:20 am from gate 12.",
      "Grandma's favourite cake is lemon cake.", "The meeting with Mr Patel moved to Wednesday.",
      "The green bin goes out every second Monday.", "Parcel for Nina is at the post office."]
NOLOWER = r"^[^a-z]*$"
I = []


def add(section, skill, prompt, check, good, bad="Banana banana banana banana banana.", notes=(), human=None):
    I.append(dict(id=f"{section}{sum(x['section'] == section for x in I) + 1:02d}", section=section, skill=skill, prompt=prompt,
                  notes=list(notes), check=check, good=good, bad=bad, **({"human": human} if human else {})))


# ---------------------------------------------------------------- A: the five skills, new wording (60)
s = "instruction"
add("A", s, "Give me a single word that means the opposite of tall.", {"words": 1, "any": ["short", "small"]}, "Short.")
add("A", s, "Is fire cold? I only want a yes or a no.", {"words": 1, "first_word": "no"}, "No.", "Yes.")
add("A", s, "Three times, please: the word lamp.", {"words": 3, "count": ["lamp", 3]}, "lamp lamp lamp", "lamp")
add("A", s, "I need a reply that is four words long.", {"words": 4}, "I am here today.")
add("A", s, "Begin your answer with the word Maybe and tell me about clouds.", {"first_word": "maybe", "min_words": 4, "max_words": 40},
    "Maybe you have seen clouds. They are white and soft.", "Clouds are white.", human="Does it say something sensible about clouds?")
add("A", s, "Tell me about the sea, and make the very last word be blue.", {"last_word": "blue", "min_words": 4, "max_words": 40},
    "The sea is big and blue.", "The sea is big.", human="Does it say something sensible about the sea?")
add("A", s, "Describe a cat using just one sentence.", {"sentences": 1, "min_words": 3, "max_words": 30}, "A cat is a small soft animal that purrs.",
    "A cat is soft. It purrs.", human="Is the sentence really about a cat and does it make sense?")
add("A", s, "Copy this line and change nothing: The red kite flew over the hill.", {"exact": "The red kite flew over the hill."},
    "The red kite flew over the hill.", "The red kite flew.")
add("A", s, "Without using the word cold, tell me what snow is like.", {"none": ["cold"], "min_words": 3, "max_words": 40},
    "Snow is white and soft.", "Snow is cold and white.", human="Does it describe snow sensibly?")
add("A", s, "Answer in a single word. Which is heavier, a horse or a mouse?", {"words": 1, "any": ["horse"]}, "Horse.", "Mouse.")
add("A", s, "Say hello to me twice and nothing more.", {"words": 2, "count": ["hello", 2]}, "Hello hello", "Hello!")
add("A", s, "Can a fish climb a tree? One word.", {"words": 1, "first_word": "no"}, "No.", "Yes.")

s = "arithmetic"
for p, n, g in [("What do you get when you put 14 and 23 together?", 37, "14 + 23 = 37."),
                ("If I have 50 and I lose 18, what is left?", 32, "32."),
                ("6 lots of 7 is how many?", 42, "6 x 7 = 42."),
                ("Half of 48 is what?", 24, "It is 24."),
                ("Double 35.", 70, "The answer is 70."),
                ("There were 12 birds on a wall and 5 flew off. How many stayed?", 7, "12 - 5 = 7. There are 7 birds left."),
                ("A week has 7 days. How many days are in 4 weeks?", 28, "4 x 7 = 28. There are 28 days."),
                ("I read 9 pages on Monday and 16 pages on Tuesday. How many pages in all?", 25, "9 + 16 = 25."),
                ("Share 36 sweets between 4 children. How many does each child get?", 9, "Each child gets 9 sweets."),
                ("How much bigger is 80 than 55?", 25, "80 - 55 = 25."),
                ("Sum up 5, 6 and 7.", 18, "5 + 6 + 7 = 18."),
                ("Tom is 8. His sister is 3 years older. How old is his sister?", 11, "8 + 3 = 11. She is 11.")]:
    add("A", s, p, {"num": n, "max_words": 30}, g, "The answer is 13.")

s = "format"
add("A", s, "Give me three animals, one per line, each line starting with a star (*).", {"line_starts": ["*", "*", "*"]},
    "* dog\n* cat\n* cow", "dog, cat, cow")
add("A", s, "List the first four months with numbers in front, like 1. 2. 3. 4.", {"numbered": 4, "all": ["january", "february", "march", "april"]},
    "1. January\n2. February\n3. March\n4. April", "January, February, March, April")
add("A", s, "Shout the word garden. I mean all capitals.", {"has_exact": "GARDEN", "max_words": 3}, "GARDEN", "Garden!")
add("A", s, "Count from 3 up to 8, with commas.", {"squashed": "3,4,5,6,7,8"}, "3, 4, 5, 6, 7, 8", "3 4 5 6 7 8")
add("A", s, "Two lines only. Line one says hello. Line two says goodbye.", {"line_words": ["hello", "goodbye"]}, "Hello\nGoodbye", "Hello goodbye")
add("A", s, "Write the sentence I like tea inside quote marks.", {"quoted": 1, "all": ["i like tea"]}, "\"I like tea.\"", "I like tea.")
add("A", s, "Name two colours with a dash before each one, on separate lines.", {"dashed": 2}, "- red\n- blue", "red and blue")
add("A", s, "How many days are there in a week? Digits only, no words.", {"exact": "7"}, "7", "Seven days.")
add("A", s, "Write the numbers 10 down to 6 with spaces between them.", {"re": r"^\s*10\s+9\s+8\s+7\s+6\.?\s*$"}, "10 9 8 7 6", "6 7 8 9 10")
add("A", s, "Give me a list of three drinks. Number them.", {"numbered": 3}, "1. tea\n2. milk\n3. juice", "tea, milk, juice")
add("A", s, "Write pillow in small letters and then in capital letters.", {"has_exact": "PILLOW", "re": r"pillow", "re_case": 1, "max_words": 4},
    "pillow PILLOW", "PILLOW")
add("A", s, "Answer with one line that ends in a question mark.", {"lines": 1, "ends": "?"}, "How are you today?", "I am fine.")

s = "notes"
add("A", s, "I will paste my notes and then ask something.\n\nNotes\n- Swim class on Tuesday at 5 pm.\n- The torch is in the top drawer.\n\nQuestion: where is the torch?",
    {"all": ["top", "drawer"], "max_words": 25}, "The torch is in the top drawer.")
add("A", s, "Question first: which room is the exam in?\n\nNotes:\n- The exam is in room 12.\n- The talk is in room 30.",
    {"all": ["12"], "none": ["30"], "max_words": 25}, "The exam is in room 12.", "The exam is in room 30.")
add("A", s, "These are my notes: Call Ella about the party. The gate code is basket77. Now tell me, what is the gate code?",
    {"all": ["basket77"], "max_words": 25}, "The gate code is basket77.")
add("A", s, "NOTES\n1) Feed the fish on Sunday.\n2) Pay the rent on Friday.\n\nWhich day do I pay the rent?",
    {"all": ["friday"], "none": ["sunday"], "max_words": 25}, "You pay the rent on Friday.", "On Sunday.")
add("A", s, "My notes say:\nJack's parrot is called Coco.\nNora's pony is called Daisy.\n\nWhat is the pony called?",
    {"all": ["daisy"], "none": ["coco"], "max_words": 25}, "The pony is called Daisy.", "It is called Coco.")
add("A", s, "Notes:\n- The bakery opens at 7 am.\n- Buy salt and butter.\n\nBased on my notes, what is the alarm code?",
    {"admit": 1, "max_words": 30}, "The notes do not say that.", "The alarm code is river12.")
add("A", s, "Notes:\n- The van is parked on Mill Lane.\n- The bike is parked on Oak Street.\n\nBased on these notes, is the van on Oak Street? Yes or no.",
    {"first_word": "no", "max_words": 25}, "No. The van is on Mill Lane.", "Yes.")
add("A", s, "Here are two notes. Note one: the soup needs three onions. Note two: the pie needs five apples. How many apples go in the pie?",
    {"any": ["five", "5"], "none": ["three", "3"], "max_words": 25}, "The pie needs five apples.", "Three apples.")
add("A", s, "Notes:\n- Grandpa arrives on Friday by train.\n- Aunt Ruby arrives on Sunday by car.\n\nWho comes by car, going by the notes?",
    {"all": ["ruby"], "none": ["grandpa"], "max_words": 25}, "Aunt Ruby comes by car.", "Grandpa.")
add("A", s, "Notes:\n- Barber on Monday at 2 pm.\n- Doctor on Wednesday at 11 am.\n\nUsing my notes, what do I have on Wednesday?",
    {"all": ["doctor"], "none": ["barber"], "max_words": 25}, "You have the doctor on Wednesday at 11 am.", "The barber.")
add("A", s, "Notes:\n- The museum closes at 5 pm.\n\nIn one word, going by my notes: what closes at 5 pm?",
    {"words": 1, "any": ["museum"]}, "Museum.", "The museum closes at 5 pm.")
add("A", s, "Notes:\n- Buy tea, jam and flour.\n\nFrom my notes, how many things do I need to buy? Give a number.",
    {"num": 3, "max_words": 25}, "3.", "You need to buy tea, jam and flour.")

s = "tool_call"
for p, v, g in [("Could you total 4187 and 2956 for me?", 7143, "4187 + 2956 = 7143."),
                ("3250 less 1875 comes to what?", 1375, "3250 - 1875 = 1375."),
                ("How many is 46 groups of 38?", 1748, "46 times 38 is 1748."),
                ("I need 7344 cut into 24 equal parts. How big is each part?", 306, "7344 divided by 24 is 306."),
                ("Each crate holds 144 bottles. How many bottles are in 65 crates?", 9360, "That is 9360 bottles."),
                ("The trip is 1260 miles and we have done 485. How far is left?", 775, "1260 - 485 = 775.")]:
    add("A", s, p, {"num_in": v, "want_call": "calc"}, g, "It is 5000.")
for p, c, g in [("It should be somewhere in my notes: when is the dentist?", {"all": ["thursday"]}, "The dentist is on Thursday at 3 pm."),
                ("Go through my notes and find the wifi password.", {"all": ["rocket42"]}, "The wifi password is rocket42."),
                ("Do my notes mention which bus goes to the airport?", {"all": ["27"]}, "Bus number 27 goes to the airport."),
                ("Notes lookup: Leo's rabbit.", {"all": ["toffee"]}, "Leo's rabbit is called Toffee."),
                ("Could you check the notes for when I should water the plants?", {"all": ["friday"]}, "You should water the plants on Friday."),
                ("Any note on what to buy?", {"all": ["eggs", "soap", "rice"]}, "You need to buy eggs, soap and rice.")]:
    add("A", s, p, dict(c, want_call="notes"), g, notes=S1)

# ---------------------------------------------------------------- B: notes questions that never say "notes" (25)
s = "store"  # the fact is only in the notes store, so the model has to decide to search
for p, c, g, st in [
        ("When is the dentist?", {"all": ["thursday", "3"]}, "The dentist is on Thursday at 3 pm.", S1),
        ("What's the wifi password again?", {"all": ["rocket42"]}, "The wifi password is rocket42.", S1),
        ("What do I have to get from the shop?", {"all": ["eggs", "soap", "rice"]}, "You need to buy eggs, soap and rice.", S1),
        ("Remind me when Mia's birthday is.", {"all": ["14", "june"]}, "Mia's birthday is on 14 June.", S1),
        ("Where did I put the key?", {"all": ["behind", "clock"]}, "The key is behind the clock.", S1),
        ("Which bus do I take to get to the airport?", {"all": ["27"]}, "Take bus number 27.", S1),
        ("Who was I meant to ring about the broken tap?", {"all": ["owen"]}, "You should call Owen.", S1),
        ("What time does the library shut?", {"all": ["6"]}, "The library closes at 6 pm.", S1),
        ("What is Sam allergic to?", {"any": ["peanuts", "peanut"]}, "Sam is allergic to peanuts.", S2),
        ("How much is the rent?", {"all": ["450"]}, "Rent is 450 coins a month.", S2),
        ("What gate does the Rome flight leave from?", {"all": ["12"]}, "It leaves from gate 12.", S2),
        ("Which cake does Grandma like best?", {"all": ["lemon"]}, "Grandma's favourite cake is lemon cake.", S2),
        ("Did the meeting with Mr Patel move? To what day?", {"all": ["wednesday"]}, "Yes. It moved to Wednesday.", S2),
        ("Where is Nina's parcel?", {"all": ["post office"]}, "It is at the post office.", S2),
        ("I have forgotten where the spare tyre is.", {"all": ["garage"]}, "The spare tyre is in the garage loft.", S2)]:
    add("B", s, p, dict(c, max_words=30), g, "I do not know.", notes=st)
s = "inline"  # the facts are in the message, in a layout the practice data never used, and the word "notes" is absent
for p, c, g, b in [
        ("Reminders: dentist Thursday 3 pm; vet Friday 10 am; piano Saturday 9 am.\nWhen do I see the vet?", {"all": ["friday"], "none": ["thursday", "saturday"]}, "You see the vet on Friday at 10 am.", "On Thursday."),
        ("To do today\n1. post the letter\n2. call Ruby\n3. buy milk\n\nWho do I need to call?", {"all": ["ruby"]}, "You need to call Ruby.", "I do not know."),
        ("Here is what I wrote down this morning: the plumber comes at 4 pm and the rent is due on Monday.\nWhen is the rent due?", {"all": ["monday"]}, "The rent is due on Monday.", "At 4 pm."),
        ("Shopping: bread, jam, tea.\nIs jam on the list?", {"first_word": "yes"}, "Yes, jam is on the list.", "No."),
        ("Mum said: pick up Finn at 5 pm from swim class. What time do I pick up Finn?", {"all": ["5"]}, "You pick up Finn at 5 pm.", "I do not know."),
        ("* Gate code: river58\n* Locker code: candle31\n\nWhat is the locker code?", {"all": ["candle31"], "none": ["river58"]}, "The locker code is candle31.", "river58"),
        ("Monday: football. Tuesday: choir. Wednesday: nothing.\nWhat is on Tuesday?", {"all": ["choir"], "none": ["football"]}, "Choir is on Tuesday.", "Football."),
        ("My list says the red box is in the attic and the blue box is in the garage. Where is the blue box?", {"all": ["garage"], "none": ["attic"]}, "The blue box is in the garage.", "In the attic."),
        ("The train leaves at 8:15 am from platform 3. Which platform?", {"all": ["3"]}, "Platform 3.", "I do not know."),
        ("Zoe - tea with honey\nMax - coffee with milk\n\nWhat does Max drink?", {"all": ["coffee"], "none": ["tea"]}, "Max drinks coffee with milk.", "Tea with honey.")]:
    add("B", s, p, dict(c, max_words=30), g, b)

# ---------------------------------------------------------------- C: two skills in one request (25)
s = "two_skills"
add("C", s, "Work out 348 times 27 and reply with only the number.", {"re": r"^\s*9,?396\.?\s*$"}, "9396", "348 times 27 is 9396.")
add("C", s, "Add 6 and 9, then say the answer three times.", {"count": ["15", 3], "max_words": 12}, "15 15 15", "15")
add("C", s, "Is 17 plus 8 more than 20? Answer yes or no.", {"words": 1, "first_word": "yes"}, "Yes.", "No.")
add("C", s, "Name three fruits as a numbered list, all in capital letters.", {"numbered": 3, "re": NOLOWER, "re_case": 1}, "1. APPLE\n2. PEAR\n3. PLUM", "1. apple\n2. pear\n3. plum")
add("C", s, "Two lines. First line: the answer to 7 times 6. Second line: the word done.", {"line_words": ["42", "done"]}, "42\ndone", "42 done")
add("C", s, "Notes:\n- Tom's ticket cost 14 coins.\n- Ana's ticket cost 9 coins.\n\nHow much did both tickets cost together?", {"num": 23, "max_words": 30}, "14 + 9 = 23 coins.", "14 coins.")
add("C", s, "Look up the dentist in my notes and answer in capital letters.", {"has_exact": "THURSDAY"}, "THE DENTIST IS ON THURSDAY AT 3 PM.", "The dentist is on Thursday at 3 pm.", notes=S1)
add("C", s, "Find Mia's birthday in my notes and tell me just the month, in one word.", {"words": 1, "any": ["june"]}, "June.", "Mia's birthday is on 14 June.", notes=S1)
add("C", s, "What is the opposite of hot? Write it in capital letters.", {"has_exact": "COLD", "max_words": 3}, "COLD", "Cold.")
add("C", s, "Say the word tree two times, then the word leaf once.", {"re": r"^\s*tree[ ,]+tree[ ,]+leaf\.?\s*$"}, "tree tree leaf", "tree leaf")
add("C", s, "Notes:\n- The club is in room 8.\n- The class is in room 15.\n\nAdd the two room numbers together.", {"num": 23, "max_words": 30}, "8 + 15 = 23.", "Room 8 and room 15.")
add("C", s, "List the numbers from 1 to 5, one on each line.", {"line_words": ["1", "2", "3", "4", "5"]}, "1\n2\n3\n4\n5", "1, 2, 3, 4, 5")
add("C", s, "Write one sentence about rain that ends with the word wet.", {"sentences": 1, "last_word": "wet", "any": ["rain", "rains", "rainy"]}, "Rain makes the grass wet.", "Rain is wet and cold.")
add("C", s, "Count the words in this sentence and reply with a number: the cat sat on the mat.", {"num": 6, "max_words": 12}, "6", "5")
add("C", s, "What is 2154 plus 3871? Then tell me if the answer is bigger than 6000, yes or no.", {"all": ["6025", "yes"], "none": ["no"]}, "2154 + 3871 = 6025. Yes, it is bigger than 6000.", "6025.")
add("C", s, "How much rent do I pay in two months?", {"all": ["900"]}, "Rent is 450 coins a month, so two months is 900 coins.", "Rent is 450 coins a month.", notes=S2)
add("C", s, "Give me the days of the weekend with a dash in front of each, in capital letters.", {"dashed": 2, "all": ["saturday", "sunday"], "re": NOLOWER, "re_case": 1}, "- SATURDAY\n- SUNDAY", "- Saturday\n- Sunday")
add("C", s, "Answer with a number and then the word apples: 4 apples and 5 apples together.", {"re": r"^\s*(9|nine) apples\.?\s*$"}, "9 apples", "9")
add("C", s, "Notes:\n- Swim class on Tuesday at 5 pm.\n- Choir on Thursday at 6 pm.\n\nList my two activities as a numbered list.", {"numbered": 2, "all": ["swim", "choir"]}, "1. Swim class\n2. Choir", "Swim class and choir.")
add("C", s, "Which is bigger, 9 times 9 or 80? Answer with the bigger number only.", {"re": r"^\s*81\.?\s*$"}, "81", "80")
add("C", s, "Write three lines. Each line is the word yes.", {"lines": 3, "words_per_line": 1, "count": ["yes", 3]}, "yes\nyes\nyes", "yes yes yes")
add("C", s, "Tell me a colour and an animal, separated by a comma, and nothing else.", {"re": r"^\s*[A-Za-z]+\s*,\s*[A-Za-z]+\.?\s*$"}, "red, dog", "A red dog.",
    human="Is the first word a colour and the second an animal?")
add("C", s, "What is on my shopping list? Put each thing on its own line.", {"lines": 3, "all": ["eggs", "soap", "rice"]}, "eggs\nsoap\nrice", "You need to buy eggs, soap and rice.", notes=S1)
add("C", s, "First say good morning. Then, on a new line, tell me what 12 take away 4 is.", {"line_words": ["good morning", "8"]}, "Good morning!\n12 - 4 = 8.", "Good morning! 8.")
add("C", s, "In one sentence, tell me what 5 plus 5 is and what colour grass is.", {"sentences": 1, "any": ["10", "ten"], "all": ["green"]}, "5 plus 5 is 10 and grass is green.", "10. Green.")

# ---------------------------------------------------------------- D: questions with no answer (20)
s = "no_notes"  # the notes store is empty
for p in ["What is my middle name?", "What did I have for lunch yesterday?", "How old is my brother?", "What is my neighbour's cat called?",
          "What is the phone number of my dentist?", "Where did I leave my glasses?", "What colour is my front door?", "What is my teacher's name?"]:
    add("D", s, p, {"admit": 1}, "I do not know that.", "It is blue.")
s = "not_in_notes"  # there are notes, but none answers this
for p in ["When is the plumber coming?", "What is the alarm code?", "Which bus goes to the beach?", "When is Zoe's birthday?",
          "Check my notes: where is the passport?", "What does my note say about the car?"]:
    add("D", s, p, {"admit": 1}, "I could not find a note about that.", "It is on Monday at 4 pm.", notes=S1)
s = "nobody_knows"
for p in ["What number am I thinking of right now?", "Will it rain here next Saturday?", "Who will win the football match tomorrow?",
          "What is inside the box on my desk?", "What will I dream about tonight?", "How many coins are in my pocket?"]:
    add("D", s, p, {"admit": 1}, "I cannot know that.", "It is 7.")

# ---------------------------------------------------------------- E: world knowledge, reported apart (20)
s = "world"
for p, a in [("What is the capital city of France?", ["paris"]), ("What do bees make?", ["honey"]), ("Which planet do we live on?", ["earth"]),
             ("What is frozen water called?", ["ice"]), ("What do you call a baby dog?", ["puppy", "pup"]), ("What season comes after winter?", ["spring"]),
             ("What is the biggest animal in the sea?", ["whale", "whales"]), ("Which meal do people eat in the morning?", ["breakfast"]),
             ("What do you use to cut paper?", ["scissors"]), ("What colour do you get when you mix red and yellow?", ["orange"]),
             ("Where does the sun rise, in the east or in the west?", ["east"]), ("What do we get from cows to drink?", ["milk"]),
             ("How many days are in a year?", ["365", "366"]), ("What is the big bright thing in the sky during the day?", ["sun"]),
             ("What do you wear on your feet?", ["shoes", "shoe", "socks", "boots"]), ("Which animal is called the king of the jungle?", ["lion"]),
             ("What language do people speak in Spain?", ["spanish"]), ("What is 100 centimetres also called?", ["metre", "meter"]),
             ("Who wrote Romeo and Juliet?", ["shakespeare"]), ("What is the largest ocean on Earth?", ["pacific"])]:
    chk = {"any": a, "max_words": 40}
    if a == ["east"]:
        chk["none"] = ["west"]
    add("E", s, p, chk, f"It is {a[0]}.", "I do not know.")


if __name__ == "__main__":
    from heldout import hcheck
    assert len(I) == 150 and len({x["prompt"] for x in I}) == 150 and len({x["id"] for x in I}) == 150, len(I)
    bad = [x["id"] for x in I if not hcheck(x, x["good"], "")] + ["!" + x["id"] for x in I if hcheck(x, x["bad"], "")]
    assert not bad, bad
    if os.path.exists(PATH):
        sys.exit("data/heldout.json already exists. It is frozen and will not be overwritten.")
    blob = json.dumps(I, indent=1, ensure_ascii=False).encode("utf-8")
    open(PATH, "wb").write(blob)
    h = hashlib.sha256(blob).hexdigest()
    open(HASH, "w", newline="\n").write(h + "\n")
    print("wrote", len(I), "items", {k: sum(x["section"] == k for x in I) for k in "ABCDE"}, "sha256", h)

"""The fixed scoreboard prompts: 100 prompts in 5 groups of 20, each with an automatic check.

These prompts are test-only. No training data may contain them (stage 4 filters against this file).
Each item: (prompt, check) where check is a dict understood by scoreboard.check_reply.
"""

N1 = ("Notes:\n- Dentist on Tuesday at 3 pm.\n- Buy milk and eggs.\n- Mum's birthday is on 12 May.\n"
      "- The spare key is under the blue pot.\n\n")
N2 = ("Notes:\n- Football practice is on Friday.\n- The wifi password is sunny42.\n- Call Ben about the bike.\n"
      "- The library closes at 6 pm.\n\n")
N3 = ("Notes:\n- Anna's cat is called Pepper.\n- The bus to town is number 14.\n- Feed the fish every morning.\n"
      "- The school trip is to the zoo.\n\n")
N4 = ("Notes:\n- The meeting is in room 7.\n- Sam likes tea with honey.\n- The car is parked on Green Street.\n"
      "- Water the plants on Sunday.\n\n")
N5 = ("Notes:\n- Grandma arrives on Saturday by train.\n- The cake needs three eggs.\n- Lucy's favourite colour is purple.\n"
      "- The doctor's name is Dr Patel.\n\n")
NOT_IN = ["not in", "no note", "don't know", "do not know", "does not say", "doesn't say", "do not say",
          "don't say", "no information", "not mention", "nothing about", "not sure", "cannot find", "can't find"]

INSTRUCTION = [
    ("Answer with one word: what colour is the sky on a clear day?", dict(max_words=1, any=["blue"])),
    ("Answer with one word: what animal says meow?", dict(max_words=1, any=["cat", "kitten"])),
    ("Answer only yes or no: is fire hot?", dict(max_words=1, any=["yes"])),
    ("Answer only yes or no: is ice hot?", dict(max_words=1, any=["no"])),
    ("Say the word banana three times.", dict(count=("banana", 3), max_words=3)),
    ("Write one sentence that uses the word river.", dict(sentences=1, any=["river"])),
    ("Write one sentence that uses the word umbrella.", dict(sentences=1, any=["umbrella"])),
    ("Write two sentences about a dog.", dict(sentences=2, any=["dog"])),
    ("Reply with exactly three words.", dict(words=3)),
    ("Reply with exactly five words.", dict(words=5)),
    ("Tell me the name of a fruit. Reply with just the name.",
     dict(max_words=2, any=["apple", "banana", "orange", "pear", "grape", "grapes", "mango", "peach", "plum", "cherry",
                            "lemon", "melon", "strawberry", "kiwi", "pineapple", "watermelon", "berry", "lime"])),
    ("Name an animal that lives in the sea. Reply with just the name.",
     dict(max_words=2, any=["fish", "whale", "shark", "dolphin", "octopus", "crab", "seal", "turtle", "jellyfish",
                            "starfish", "squid", "lobster", "eel", "seahorse", "shrimp", "clam", "ray"])),
    ("Tell me about a pet that purrs, but do not use the word cat.", dict(none=["cat", "cats"], min_words=4)),
    ("Tell me about snow, but do not use the word cold.", dict(none=["cold"], min_words=4, any=["snow"])),
    ("Ask me one question about my day.", dict(ends="?", sentences=1)),
    ("Tell me about your day and end your reply with the word goodbye.", dict(last_word="goodbye", min_words=4)),
    ("Start your reply with the word Sure and then tell me about cats.", dict(first_word="sure", any=["cat", "cats"])),
    ("Repeat this exactly: The moon is bright tonight.", dict(exact="The moon is bright tonight.")),
    ("Repeat this exactly: I like green apples.", dict(exact="I like green apples.")),
    ("What is the opposite of hot? Answer with one word.", dict(max_words=1, any=["cold"])),
]

ARITHMETIC = [
    ("What is 3 + 4?", dict(number=7)), ("What is 9 + 6?", dict(number=15)),
    ("What is 12 + 7?", dict(number=19)), ("What is 25 + 14?", dict(number=39)),
    ("What is 48 + 36?", dict(number=84)), ("What is 10 - 4?", dict(number=6)),
    ("What is 15 - 8?", dict(number=7)), ("What is 30 - 12?", dict(number=18)),
    ("What is 52 - 27?", dict(number=25)), ("What is 3 times 4?", dict(number=12)),
    ("What is 6 times 7?", dict(number=42)), ("What is 5 times 9?", dict(number=45)),
    ("What is 8 x 8?", dict(number=64)), ("What is 20 divided by 4?", dict(number=5)),
    ("What is 18 divided by 3?", dict(number=6)),
    ("Tom has 5 apples. He gets 3 more. How many apples does Tom have now?", dict(number=8)),
    ("Sara had 12 balloons. 4 flew away. How many balloons are left?", dict(number=8)),
    ("A box has 6 eggs. How many eggs are in 3 boxes?", dict(number=18)),
    ("There are 7 birds in a tree. 2 more birds come. How many birds are there now?", dict(number=9)),
    ("Mia shares 10 sweets equally between 2 friends. How many sweets does each friend get?", dict(number=5)),
]

FORMAT = [
    ("List three colours as a numbered list.", dict(numbered=3)),
    ("List four animals as a numbered list.", dict(numbered=4)),
    ("List two fruits as a numbered list.", dict(numbered=2)),
    ("List five things you can find in a kitchen as a numbered list.", dict(numbered=5)),
    ("List three things in a park. Put a dash at the start of each line.", dict(dashed=3)),
    ("List three toys. Put a dash at the start of each line.", dict(dashed=3)),
    ("Write the word hello in capital letters.", dict(has_exact="HELLO", max_words=3)),
    ("Write this in capital letters: good morning", dict(has_exact="GOOD MORNING", max_words=4)),
    ("In fewer than ten words, what is rain?", dict(max_words=9, min_words=1)),
    ("In fewer than eight words, what sound does a dog make?", dict(max_words=7, min_words=1)),
    ("Write exactly two lines. Each line is one short sentence.", dict(lines=2)),
    ("Write three lines. Each line has only one word.", dict(lines=3, words_per_line=1)),
    ("Write about the sun as a question and an answer. Start the first line with Q: and the second line with A:",
     dict(lines=2, line_starts=["Q:", "A:"])),
    ("Write a poem about the moon with exactly four lines.", dict(lines=4)),
    ("Tell me your favourite colour. Put your whole reply inside quote marks.", dict(quoted=True)),
    ("Write the numbers from 1 to 5 with commas between them.", dict(squashed="1,2,3,4,5")),
    ("Write Monday, Tuesday and Wednesday, one per line.", dict(lines=3, line_words=["monday", "tuesday", "wednesday"])),
    ("Spell the word cat with a dash between each letter.", dict(any_raw=["c-a-t"])),
    ("Write one sentence and end it with an exclamation mark.", dict(sentences=1, ends="!")),
    ("How many legs does a cat have? Answer with a single number.", dict(max_words=1, any=["4", "four"])),
]

NOTES = [
    (N1 + "Using the notes, when is the dentist?", dict(any=["tuesday"])),
    (N1 + "Using the notes, what do I need to buy?", dict(all=["milk", "eggs"])),
    (N1 + "Using the notes, where is the spare key?", dict(any=["blue pot", "under the pot"])),
    (N1 + "Using the notes, what time is football?", dict(any_raw=NOT_IN)),
    (N2 + "Using the notes, what is the wifi password?", dict(any=["sunny42"])),
    (N2 + "Using the notes, what day is football practice?", dict(any=["friday"])),
    (N2 + "Using the notes, when does the library close?", dict(any=["6"])),
    (N2 + "Using the notes, who should I call about the bike?", dict(any=["ben"])),
    (N3 + "Using the notes, what is the name of Anna's cat?", dict(any=["pepper"])),
    (N3 + "Using the notes, which bus goes to town?", dict(any=["14"])),
    (N3 + "Using the notes, where is the school trip going?", dict(any=["zoo"])),
    (N3 + "Using the notes, what is the name of Anna's dog?", dict(any_raw=NOT_IN)),
    (N4 + "Using the notes, which room is the meeting in?", dict(any=["7", "seven"])),
    (N4 + "Using the notes, where is the car parked?", dict(any=["green street"])),
    (N4 + "Using the notes, what does Sam like in tea?", dict(any=["honey"])),
    (N4 + "Using the notes, what time is the meeting?", dict(any_raw=NOT_IN)),
    (N5 + "Using the notes, how is Grandma travelling?", dict(any=["train"])),
    (N5 + "Using the notes, how many eggs does the cake need?", dict(any=["three", "3"])),
    (N5 + "Using the notes, what is the doctor's name?", dict(any=["patel"])),
    (N5 + "Using the notes, what is Lucy's favourite food?", dict(any_raw=NOT_IN)),
]

# The reply must end with one line of JSON: {"tool": "calc", "input": "..."} or {"tool": "notes", "input": "..."}
TOOL = [
    ("Use the calculator: what is 348 times 27?", dict(tool="calc", value=348 * 27)),
    ("Use the calculator: what is 1250 + 876?", dict(tool="calc", value=1250 + 876)),
    ("Use the calculator: what is 9000 - 4321?", dict(tool="calc", value=9000 - 4321)),
    ("Use the calculator: what is 144 divided by 12?", dict(tool="calc", value=12)),
    ("Use the calculator: what is 67 times 89?", dict(tool="calc", value=67 * 89)),
    ("What is 4521 + 3879?", dict(tool="calc", value=4521 + 3879)),
    ("What is 73 times 46?", dict(tool="calc", value=73 * 46)),
    ("What is 10000 - 2468?", dict(tool="calc", value=10000 - 2468)),
    ("I bought 24 boxes with 36 pencils in each box. How many pencils is that?", dict(tool="calc", value=24 * 36)),
    ("A ticket costs 125 coins. How much do 18 tickets cost?", dict(tool="calc", value=125 * 18)),
    ("Look in my notes: when is the dentist?", dict(tool="notes", keys=["dentist"])),
    ("Look in my notes: what is the wifi password?", dict(tool="notes", keys=["wifi", "password"])),
    ("Look in my notes: where did I park the car?", dict(tool="notes", keys=["car", "park"])),
    ("Look in my notes: when is Mum's birthday?", dict(tool="notes", keys=["birthday", "mum"])),
    ("Look in my notes: what do I need to buy?", dict(tool="notes", keys=["buy", "shop"])),
    ("Check my notes and tell me which bus goes to town.", dict(tool="notes", keys=["bus", "town"])),
    ("Check my notes and tell me when the library closes.", dict(tool="notes", keys=["library"])),
    ("What do my notes say about the school trip?", dict(tool="notes", keys=["school", "trip"])),
    ("What do my notes say about football?", dict(tool="notes", keys=["football"])),
    ("Did I write a note about Grandma?", dict(tool="notes", keys=["grandma"])),
]

# notes answers must be short: a long ramble that happens to contain the fact does not count
NOTES = [(p, dict(c, max_words=25)) for p, c in NOTES]

GROUPS = {"instruction": INSTRUCTION, "arithmetic": ARITHMETIC, "format": FORMAT, "notes": NOTES, "tool_call": TOOL}
assert all(len(v) == 20 for v in GROUPS.values())

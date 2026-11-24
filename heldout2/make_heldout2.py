"""Builds the second frozen held-out test: data/heldout2.json and data/heldout2.sha256.

Written by a session that saw neither the first held-out test nor any practice data.
  python heldout2/make_heldout2.py
It checks every item (the good reply must pass, the bad reply must fail) and refuses to overwrite.
"""
import hashlib
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from heldout import hcheck  # noqa: E402

OUT_JSON = os.path.join(ROOT, "data", "heldout2.json")
OUT_HASH = os.path.join(ROOT, "data", "heldout2.sha256")

N1 = ["Dentist for Mia on Tuesday at 4 pm.", "The spare key is under the blue flower pot.", "Wifi password is sunny42.",
      "Grandma's birthday is on March 9.", "Buy eggs, rice and soap.", "The plumber is Mr Hill, phone 555 0182.",
      "Library books are due on Friday.", "The cat eats at 7 in the morning.", "The bike lock code is 4471."]
N2 = ["Team meeting is on Monday at 10 am in room 6.", "The printer is on the second floor.", "Lunch with Omar on Wednesday at noon.",
      "My locker number is 58.", "The report is due on June 3.", "Call Nina about the school trip.", "Parking spot is B12.",
      "The bus home leaves at 5:15.", "The door code for the office is 9034.", "Bring the red folder to class."]
N3 = ["The train to the lake leaves at 8:40 on Saturday.", "Passport is in the top desk drawer.", "The dog's vet is Dr Stone.",
      "Swim class is every Thursday at 6 pm.", "The hotel is called the Green Door Inn.", "Aunt Rosa lands at 2 pm on Sunday.",
      "Water the plants every three days.", "The tent is in the garage on the high shelf.", "Pay the rent by the first of the month."]
N4 = ["Ben has soccer on Wednesday at 5 pm.", "The babysitter is Lucy, phone 555 0147.", "Lena's teacher is Mrs Park.",
      "The school play is on May 12.", "Piano lesson costs 30 dollars.", "The car is at the shop until Friday.", "Dad's shoe size is 11.",
      "The gift for Sam is hidden in the hall closet.", "Trash goes out on Tuesday night.", "The pool opens at 9 am."]

ITEMS = []


def add(id, skill, prompt, check, good, bad, notes=(), human=None):
    it = {"id": id, "section": id[0], "skill": skill, "prompt": prompt, "notes": list(notes), "check": check, "good": good, "bad": bad}
    if human:
        it["human"] = human
    ITEMS.append(it)


# ---------------------------------------------------------------- A: instruction
add("A01", "instruction", "Is ice cold? Answer with just yes or no.", {"words": 1, "any": ["yes"]}, "Yes.", "Yes, ice is cold.")
add("A02", "instruction", "Say the word hello three times and nothing else.", {"count": ["hello", 3], "words": 3},
    "hello hello hello", "hello hello")
add("A03", "instruction", "Please copy this sentence exactly: The red kite flew over the hill.",
    {"exact": "The red kite flew over the hill."}, "The red kite flew over the hill.", "The red kite flew over the hills.")
add("A04", "instruction", "Tell me something about dogs, but your reply has to start with the word Maybe.",
    {"first_word": "maybe", "any": ["dog", "dogs"], "min_words": 4}, "Maybe dogs like to run and play.", "Dogs like to run and play.")
add("A05", "instruction", "Write one sentence about the rain. The last word must be umbrella.",
    {"last_word": "umbrella", "sentences": 1, "any": ["rain", "rains", "rainy", "raining"]},
    "When the rain comes I take my umbrella.", "The rain is wet and I need an umbrella today.")
add("A06", "instruction", "In exactly five words, tell me what a bed is for.", {"words": 5},
    "A bed is for sleeping.", "A bed is a place for sleeping at night.", human="Does the reply say what a bed is for?")
add("A07", "instruction", "Describe the sun without using the word hot.",
    {"none": ["hot"], "min_words": 4, "any": ["sun", "bright", "light", "sky", "star", "yellow", "warm", "shines"]},
    "The sun is big and bright in the sky.", "The sun is very hot and bright.", human="Is it a fair description of the sun?")
add("A08", "instruction", "One word only: what color is grass?", {"words": 1, "any": ["green"]}, "Green", "Grass is green.")
add("A09", "instruction", "Can fish climb trees? Reply yes or no, nothing more.", {"words": 1, "any": ["no"]}, "No.", "Yes.")
add("A10", "instruction", "Type the word blue twice, then the word red once.",
    {"count": ["blue", 2], "words": 3, "last_word": "red"}, "blue blue red", "blue red red")

# ---------------------------------------------------------------- A: arithmetic
add("A11", "arithmetic", "What is 8 plus 7?", {"num": 15}, "8 plus 7 is 15.", "8 plus 7 is 16.")
add("A12", "arithmetic", "I had 12 stickers and gave 5 to my brother. How many do I have left?", {"num": 7},
    "You have 7 stickers left.", "You have 17 stickers left.")
add("A13", "arithmetic", "6 times 4 = ?", {"num": 24}, "24", "28")
add("A14", "arithmetic", "How much is thirty minus eleven?", {"num": 19}, "Thirty minus eleven is 19.", "It is 21.")
add("A15", "arithmetic", "Share 20 sweets between 4 kids so each gets the same. How many per kid?", {"num": 5},
    "Each kid gets 5 sweets.", "Each kid gets 4 sweets.")
add("A16", "arithmetic", "Tom is 9. His sister is 3 years older. How old is she?", {"num": 12}, "She is 12 years old.", "She is 6 years old.")
add("A17", "arithmetic", "Add 25 and 25 for me please.", {"num": 50}, "25 and 25 make 50.", "25 and 25 make 40.")
add("A18", "arithmetic", "There are 3 boxes with 10 pencils in each box. How many pencils is that in all?", {"num": 30},
    "That is 30 pencils in all.", "That is 13 pencils in all.")
add("A19", "arithmetic", "what's half of 18", {"num": 9}, "Half of 18 is 9.", "Half of 18 is 8.")
add("A20", "arithmetic", "A book costs 14 dollars and a pen costs 3 dollars. What do I pay for both?", {"num": 17},
    "You pay 17 dollars for both.", "You pay 14 dollars for the book.")

# ---------------------------------------------------------------- A: format
add("A21", "format", "Name three fruits as a list, with a dash at the start of each line.", {"dashed": 3},
    "- apple\n- banana\n- pear", "apple, banana, pear")
add("A22", "format", "Give me a numbered list of four animals.", {"numbered": 4}, "1. cat\n2. dog\n3. cow\n4. pig", "cat\ndog\ncow\npig")
add("A23", "format", "Write the word quiet in capital letters.", {"has_exact": "QUIET"}, "QUIET", "quiet")
add("A24", "format", "Count from 1 to 6, one number on each line.", {"line_starts": ["1", "2", "3", "4", "5", "6"]},
    "1\n2\n3\n4\n5\n6", "1 2 3 4 5 6")
add("A25", "format", "Put this sentence inside quote marks: I love my garden.", {"quoted": 1, "has_exact": "I love my garden"},
    "\"I love my garden.\"", "I love my garden.")
add("A26", "format", "List the days of the weekend. Put a star (*) in front of each one, each on its own line.",
    {"line_starts": ["*", "*"], "all": ["saturday", "sunday"]}, "* Saturday\n* Sunday", "Saturday and Sunday")
add("A27", "format", "Count backwards from 5 down to 1 on a single line.",
    {"lines": 1, "re": r"5\D{0,5}4\D{0,5}3\D{0,5}2\D{0,5}1"}, "5 4 3 2 1", "1 2 3 4 5")
add("A28", "format", "Name two colors. First one on line one, second one on line two, no other words.",
    {"lines": 2, "words_per_line": 1}, "red\nblue", "red and blue", human="Are both lines colors?")
add("A29", "format", "Shout these words back at me in all capitals, on one line: cup, plate, spoon",
    {"lines": 1, "re": r"CUP\W+PLATE\W+SPOON", "re_case": 1}, "CUP, PLATE, SPOON", "cup, plate, spoon")
add("A30", "format", "Give me a list of the first three months of the year. Number them 1, 2, 3.",
    {"numbered": 3, "line_words": ["january", "february", "march"]}, "1. January\n2. February\n3. March", "January, February, March")

# ---------------------------------------------------------------- A: notes pasted in the prompt
add("A31", "notes", "Here are my notes:\n- Swim bag is in the car.\n- Aunt May comes on Sunday.\n- Milk is in the small fridge.\n\nWhere is my swim bag?",
    {"any": ["car"], "none": ["fridge"]}, "Your swim bag is in the car.", "Your swim bag is in the small fridge.")
add("A32", "notes", "Notes: Jo's party starts at 6 pm. Bring a cake. The house number is 14. What time does the party start?",
    {"all": ["6"], "none": ["14"]}, "The party starts at 6 pm.", "The party starts at 14.")
add("A33", "notes", "My notes say:\n1) The red box holds the tools.\n2) The green box holds the toys.\n3) The paint is in the shed.\n\nWhich box has the toys in it?",
    {"any": ["green"], "none": ["red"]}, "The green box has the toys.", "The red box has the toys.")
add("A34", "notes", "From my notes: 'Feed the fish twice a day. The fish food is on the top shelf.' How often should I feed the fish?",
    {"any": ["twice", "two times", "2 times", "two", "2"]}, "Feed the fish twice a day.", "Feed the fish once a day.")
add("A35", "notes", "Notes for today\nshop: bread and jam\nbank: closes at 4\ngym: bring towel\n\nWhat do I need to bring to the gym?",
    {"any": ["towel"], "none": ["bread", "jam"]}, "You need to bring a towel.", "You need to bring bread and jam.")
add("A36", "notes", "I wrote these notes: The picnic is at Oak Park. Leo brings the drinks. Kim brings the plates. Who is bringing the drinks?",
    {"any": ["leo"], "none": ["kim"]}, "Leo is bringing the drinks.", "Kim is bringing the drinks.")
add("A37", "notes", "Look at my notes and tell me the color of the new couch.\n\nNotes:\nThe new couch comes on Friday.\nThe old chair goes to Pat.\nThe rug is grey.",
    {"admit": 1}, "The notes do not say what color the new couch is.", "The new couch is grey.")
add("A38", "notes", "Notes:\n* Dance class - Monday\n* Art club - Thursday\n* Chess - Friday\n\nWhat day do I have art club?",
    {"any": ["thursday"], "none": ["monday", "friday"]}, "You have art club on Thursday.", "You have art club on Monday.")
add("A39", "notes", "These are my notes. The cake needs two eggs. The oven should be warm. Bake it for forty minutes. How much sugar goes in the cake?",
    {"admit": 1}, "I do not know. Your notes do not say how much sugar.", "The cake needs two cups of sugar.")
add("A40", "notes", "notes: mum's car is silver, dad's car is black, my bike is orange. what color is dad's car?",
    {"any": ["black"], "none": ["silver", "orange"]}, "Dad's car is black.", "Dad's car is silver.")

# ---------------------------------------------------------------- A: tool calls
add("A41", "tool_call", "What is 426 times 38?", {"num_in": 426 * 38, "must_call": "calc"}, "426 times 38 is 16188.", "426 times 38 is 15188.")
add("A42", "tool_call", "Please add 2789 and 4655.", {"num_in": 2789 + 4655, "must_call": "calc"}, "The sum is 7444.", "The sum is 7344.")
add("A43", "tool_call", "I need 5120 minus 1873 worked out.", {"num_in": 5120 - 1873, "must_call": "calc"}, "That is 3247.", "That is 3347.")
add("A44", "tool_call", "How much is 9648 divided by 24?", {"num_in": 9648 // 24, "must_call": "calc"}, "It is 402.", "It is 412.")
add("A45", "tool_call", "A hall has 135 rows with 46 seats in every row. How many seats are there?", {"num_in": 135 * 46, "must_call": "calc"},
    "There are 6210 seats.", "There are 181 seats.")
add("A46", "tool_call", "Check my notes: when is Mia's dentist visit?", {"all": ["tuesday", "4"], "must_call": "notes"},
    "Mia's dentist visit is on Tuesday at 4 pm.", "Mia's dentist visit is on Friday at 7.", N1)
add("A47", "tool_call", "Can you look in my notes and tell me my locker number?", {"all": ["58"], "must_call": "notes"},
    "Your locker number is 58.", "Your locker number is 12.", N2)
add("A48", "tool_call", "What do my notes say about the hotel name?", {"all": ["green door"], "must_call": "notes"},
    "The hotel is called the Green Door Inn.", "The hotel is called the Lake Inn.", N3)
add("A49", "tool_call", "Search my notes for the babysitter's phone number please.", {"all": ["555", "0147"], "must_call": "notes"},
    "The babysitter is Lucy, phone 555 0147.", "The babysitter's phone is 555 0199.", N4)
add("A50", "tool_call", "According to my notes, what day are the library books due?", {"all": ["friday"], "must_call": "notes"},
    "The library books are due on Friday.", "The library books are due on Tuesday.", N1)

# ---------------------------------------------------------------- B: store (fact only in the notes store, no word "note")
add("B01", "store", "Where did I put the spare key?", {"all": ["pot"], "must_call": "notes"},
    "The spare key is under the blue flower pot.", "The spare key is in the top desk drawer.", N1)
add("B02", "store", "What's the wifi password again?", {"all": ["sunny42"], "must_call": "notes"},
    "The wifi password is sunny42.", "The wifi password is 4471.", N1)
add("B03", "store", "When is Grandma's birthday?", {"all": ["march", "9"], "must_call": "notes"},
    "Grandma's birthday is on March 9.", "Grandma's birthday is on May 2.", N1)
add("B04", "store", "What is the plumber's phone number?", {"all": ["555", "0182"], "must_call": "notes"},
    "The plumber is Mr Hill, phone 555 0182.", "The plumber's phone is 555 0100.", N1)
add("B05", "store", "I forgot the code for my bike lock. What is it?", {"all": ["4471"], "must_call": "notes"},
    "The bike lock code is 4471.", "The bike lock code is 1234.", N1)
add("B06", "store", "What room is the team meeting in?", {"all": ["6"], "must_call": "notes"},
    "The team meeting is in room 6.", "The team meeting is in room 12.", N2)
add("B07", "store", "When am I having lunch with Omar?", {"all": ["wednesday"], "any": ["noon", "12"], "must_call": "notes"},
    "Lunch with Omar is on Wednesday at noon.", "Lunch with Omar is on Monday at 10 am.", N2)
add("B08", "store", "Where do I park?", {"all": ["b12"], "must_call": "notes"}, "Your parking spot is B12.", "Your parking spot is A4.", N2)
add("B09", "store", "What time does my bus home leave?", {"all": ["5:15"], "must_call": "notes"},
    "The bus home leaves at 5:15.", "The bus home leaves at 4:30.", N2)
add("B10", "store", "Tell me the office door code.", {"all": ["9034"], "must_call": "notes"},
    "The door code for the office is 9034.", "The door code for the office is 58.", N2)
add("B11", "store", "Where is my passport?", {"all": ["drawer"], "must_call": "notes"},
    "Your passport is in the top desk drawer.", "Your passport is in the garage.", N3)
add("B12", "store", "Who is the vet for the dog?", {"all": ["stone"], "must_call": "notes"}, "The dog's vet is Dr Stone.", "The dog's vet is Dr Hill.", N3)
add("B13", "store", "What time does the train to the lake leave on Saturday?", {"all": ["8:40"], "must_call": "notes"},
    "The train leaves at 8:40.", "The train leaves at 6 pm.", N3)
add("B14", "store", "When does Aunt Rosa land?", {"all": ["sunday", "2"], "must_call": "notes"},
    "Aunt Rosa lands at 2 pm on Sunday.", "Aunt Rosa lands on Saturday at 8:40.", N3)
add("B15", "store", "How often do the plants need water?", {"any": ["three days", "3 days", "third day"], "must_call": "notes"},
    "Water the plants every three days.", "Water the plants every day.", N3)
add("B16", "store", "When is Ben's soccer?", {"all": ["wednesday", "5"], "must_call": "notes"},
    "Ben has soccer on Wednesday at 5 pm.", "Ben has soccer on Tuesday night.", N4)
add("B17", "store", "Remind me, who is Lena's teacher?", {"all": ["park"], "must_call": "notes"},
    "Lena's teacher is Mrs Park.", "Lena's teacher is Lucy.", N4)
add("B18", "store", "How much does the piano lesson cost?", {"all": ["30"], "must_call": "notes"},
    "The piano lesson costs 30 dollars.", "The piano lesson costs 11 dollars.", N4)
add("B19", "store", "Where did we hide the gift for Sam?", {"all": ["closet"], "must_call": "notes"},
    "The gift for Sam is hidden in the hall closet.", "The gift for Sam is at the shop.", N4)
add("B20", "store", "what night does the trash go out", {"all": ["tuesday"], "must_call": "notes"},
    "Trash goes out on Tuesday night.", "Trash goes out on Friday night.", N4)

# ---------------------------------------------------------------- B: inline (facts in the prompt, no word "note")
add("B21", "inline", "Reminders: call Dad at 6, buy stamps, return the drill to Max. Who gets the drill back?",
    {"any": ["max"], "none": ["dad"]}, "Max gets the drill back.", "Dad gets the drill back.")
add("B22", "inline", "To do today:\n[ ] wash the car\n[x] pay the gas bill\n[ ] mail the card to Ann\n\nWhich job have I already done?",
    {"any": ["bill"], "none": ["car", "card", "ann"]}, "You already paid the gas bill.", "You already washed the car.")
add("B23", "inline", "Monday - swimming\nTuesday - drums\nWednesday - free\nThursday - drums\nFriday - football\n\nOn which days do I have drums?",
    {"all": ["tuesday", "thursday"], "none": ["monday", "wednesday", "friday"]}, "You have drums on Tuesday and Thursday.", "You have drums on Tuesday.")
add("B24", "inline", "My sister told me the red cup is hers, the yellow cup is mine and the white cup is for guests. Which cup is mine?",
    {"any": ["yellow"], "none": ["red", "white"]}, "The yellow cup is yours.", "The red cup is yours.")
add("B25", "inline", "Shopping list: 2 loaves of bread, 6 apples, 1 bag of flour. How many apples do I need to get?",
    {"any": ["6", "six"], "none": ["2", "two"]}, "You need to get 6 apples.", "You need to get 2 apples.")
add("B26", "inline", "9:00 math | 10:00 reading | 11:00 art | 12:00 lunch\nWhat do I have at 11?",
    {"any": ["art"], "none": ["math", "reading", "lunch"]}, "You have art at 11.", "You have reading at 11.")
add("B27", "inline", "Packing for the trip: hat (packed), boots (packed), map (still on the desk), torch (packed). What is not packed yet?",
    {"any": ["map"], "none": ["hat", "boots", "torch"]}, "The map is not packed yet.", "The boots are not packed yet.")
add("B28", "inline", "Mum left a message on the fridge. It says: 'Dinner is in the oven. Feed the dog at five. Back by eight.' When will Mum be back?",
    {"any": ["eight", "8"], "none": ["five", "5"]}, "Mum will be back by eight.", "Mum will be back at five.")
add("B29", "inline", "Phone list - Dr Lane: 555 0111 - School: 555 0122 - Pizza place: 555 0133. What number do I ring for the school?",
    {"all": ["0122"], "none": ["0111", "0133"]}, "Ring 555 0122 for the school.", "Ring 555 0133 for the school.")
add("B30", "inline", "Rules of our game: you get 3 lives, the blue door is the exit, and you must not touch the water. Which door is the way out?",
    {"any": ["blue"]}, "The blue door is the way out.", "The red door is the way out.")

# ---------------------------------------------------------------- C: two skills at once
add("C01", "two_skills", "What is 9 plus 6? Answer with only the number, no words.", {"num": 15, "words": 1}, "15", "9 plus 6 is 15.")
add("C02", "two_skills", "Work out 7 times 5 and write the answer in a full sentence that ends with an exclamation mark.",
    {"num_in": 35, "ends": "!", "min_words": 3}, "7 times 5 is 35!", "35")
add("C03", "two_skills", "Notes: Bus to town at 8:10. Bus to the beach at 9:30. Answer in one word: where does the 9:30 bus go?",
    {"words": 1, "any": ["beach"]}, "Beach.", "The 9:30 bus goes to the beach.")
add("C04", "two_skills", "My notes:\n- Ana has 4 hens.\n- Raj has 7 hens.\nHow many hens do Ana and Raj have together?",
    {"num": 11}, "They have 11 hens together.", "Ana has 4 hens and Raj has 7 hens.")
add("C05", "two_skills", "List three things you can find in a kitchen, numbered, and write every word in capital letters.",
    {"numbered": 3, "re": r"^[^a-z]+$", "re_case": 1}, "1. SPOON\n2. POT\n3. CUP", "1. spoon\n2. pot\n3. cup",
    human="Are all three things found in a kitchen?")
add("C06", "two_skills", "Apples cost 3 dollars a bag and I want 4 bags. Start your answer with the word Total.",
    {"num_in": 12, "first_word": "total"}, "Total: 12 dollars.", "You pay 12 dollars.")
add("C07", "two_skills", "Reminders: pool opens at 10 in the morning, closes at 6 in the evening. How many hours is the pool open? Just the number please.",
    {"num": 8, "words": 1}, "8", "The pool is open for 8 hours.")
add("C08", "two_skills", "Here are my notes:\nThe party is on Saturday.\nThe party is at Dan's house.\nBring juice.\n\nWrite the day and the place of the party as a list with dashes, one per line.",
    {"dashed": 2, "all": ["saturday", "dan"]}, "- Saturday\n- Dan's house", "The party is on Saturday at Dan's house.")
add("C09", "two_skills", "Say the word go as many times as 2 plus 2.", {"count": ["go", 4], "words": 4}, "go go go go", "go go")
add("C10", "two_skills", "Answer yes or no only: is 15 bigger than 9 plus 9?", {"words": 1, "any": ["no"]}, "No", "Yes")
add("C11", "two_skills", "Count from 1 to 4, each number on its own line, and after the last number add a line that says done.",
    {"line_starts": ["1", "2", "3", "4", ""], "last_word": "done"}, "1\n2\n3\n4\ndone", "1\n2\n3\n4")
add("C12", "two_skills", "I have 10 dollars. A toy costs 6 dollars. Can I buy it, and how much is left? Start with Yes or No.",
    {"first_word": "yes", "num_in": 4}, "Yes, you can buy it and you have 4 dollars left.", "Yes, you can buy it.")
add("C13", "two_skills", "Schedule: lunch is at 12, the nap is at 1, snack time is at 3. In one short sentence that starts with the word Snack, tell me when snack time is.",
    {"first_word": "snack", "sentences": 1, "all": ["3"]}, "Snack time is at 3.", "It is at 3.")
add("C14", "two_skills", "Find in my notes when the school play is, and answer in capital letters.",
    {"must_call": "notes", "re": r"^[^a-z]*MAY[^a-z]*$", "re_case": 1, "all": ["12"]},
    "THE SCHOOL PLAY IS ON MAY 12.", "The school play is on May 12.", N4)
add("C15", "two_skills", "Use my notes to find the bike lock code, then reply with the code only.",
    {"must_call": "notes", "words": 1, "all": ["4471"]}, "4471", "The bike lock code is 4471.", N1)
add("C16", "two_skills", "What is 640 plus 285? Give only the number.", {"must_call": "calc", "num_in": 640 + 285, "words": 1},
    "925", "The sum is 925.")
add("C17", "two_skills", "Multiply 123 by 45 and put the answer in a sentence that starts with the word So.",
    {"must_call": "calc", "num_in": 123 * 45, "first_word": "so"}, "So 123 times 45 is 5535.", "The answer is 5535.")
add("C18", "two_skills", "Ella read 8 pages on Monday and 9 pages on Tuesday. Write the total on the first line and the word pages on the second line.",
    {"lines": 2, "line_words": ["17", "pages"]}, "17\npages", "17 pages")
add("C19", "two_skills", "Give me two animals that can fly, as a dashed list, and do not use the word bird.",
    {"dashed": 2, "none": ["bird", "birds"]}, "- bat\n- bee", "- bird\n- bat", human="Can both animals fly?")
add("C20", "two_skills", "Notes: Red team has 5 points. Blue team has 9 points. Which team is ahead, and by how many points?",
    {"any": ["blue"], "num_in": 4}, "Blue team is ahead by 4 points.", "Blue team is ahead.")
add("C21", "two_skills", "Write a two line reply. Line one: the answer to 30 minus 8. Line two: the answer to 6 plus 6.",
    {"lines": 2, "line_words": ["22", "12"]}, "22\n12", "22")
add("C22", "two_skills", "Repeat the word star three times, then end with a question mark.", {"count": ["star", 3], "ends": "?"},
    "star star star?", "star star star")
add("C23", "two_skills", "To do: feed cat, call Gran, wash socks, buy tape. Put my to-do jobs in a numbered list, in the same order.",
    {"numbered": 4, "line_words": ["cat", "gran", "socks", "tape"]}, "1. feed cat\n2. call Gran\n3. wash socks\n4. buy tape",
    "feed cat, call Gran, wash socks, buy tape")
add("C24", "two_skills", "In exactly four words, tell me what 5 plus 5 makes.", {"words": 4, "any": ["10", "ten"]}, "The answer is ten.", "10")
add("C25", "two_skills", "Kim's list says: 2 red pens, 3 blue pens, 1 green pen. How many pens is that altogether? Answer in a full sentence with the word pens in it.",
    {"num_in": 6, "all": ["pens"], "min_words": 4}, "That is 6 pens altogether.", "6")
add("C26", "two_skills", "Look up my swim class in my notes. What day is it? One word.", {"must_call": "notes", "words": 1, "any": ["thursday"]},
    "Thursday", "It is on Thursday.", N3)
add("C27", "two_skills", "Tell me one thing about cats. Use exactly one sentence and make the first word Cats.",
    {"first_word": "cats", "sentences": 1, "min_words": 4}, "Cats like to sleep in the sun.", "Cats are soft. They like to sleep.",
    human="Is it a true thing about cats?")
add("C28", "two_skills", "Dad's list: milk 2 dollars, bread 3 dollars, cheese 5 dollars. What is the total cost? Write it like this: Total = and then the number.",
    {"squashed": "Total=10"}, "Total = 10", "The total is 10 dollars.")
add("C29", "two_skills", "Write the numbers 2, 4, 6 and 8 as a list with a dash before each, and then tell me their sum on a last line.",
    {"line_starts": ["-", "-", "-", "-", ""], "num_in": 20}, "- 2\n- 4\n- 6\n- 8\nThe sum is 20.", "- 2\n- 4\n- 6\n- 8")
add("C30", "two_skills", "Is a mouse bigger than a horse? Answer no, and then say which one is bigger, all in one sentence.",
    {"first_word": "no", "sentences": 1, "any": ["horse"]}, "No, the horse is bigger.", "No.")

# ---------------------------------------------------------------- D: no answer (empty notes)
A = {"admit": 1}
add("D01", "no_answer", "What did I eat for breakfast this morning?", A, "I do not know what you ate this morning.", "You ate eggs and toast.")
add("D02", "no_answer", "What is my sister's middle name?", A, "I do not know your sister's middle name.", "Her middle name is Rose.")
add("D03", "no_answer", "How many coins are in my pocket right now?", A, "I cannot see your pocket, so I do not know.", "There are 5 coins in your pocket.")
add("D04", "no_answer", "Where did I leave my glasses?", A, "I did not find anything about your glasses.", "Your glasses are on the kitchen table.")
add("D05", "no_answer", "What will the weather be like at my house next Friday?", A, "I am not sure. I do not know the weather.", "It will be sunny and warm.")
add("D06", "no_answer", "What is the name of my best friend's dog?", A, "I do not know the name of that dog.", "The dog is called Max.")
add("D07", "no_answer", "Which number am I thinking of?", A, "I do not know which number you are thinking of.", "You are thinking of 7.")
add("D08", "no_answer", "What color is the shirt I am wearing today?", A, "I can't see you, so I do not know.", "Your shirt is blue.")
add("D09", "no_answer", "Who is going to win the game tonight?", A, "Nobody knows who will win yet.", "The home team is going to win.")
add("D10", "no_answer", "what's my phone number", A, "I do not have your phone number.", "Your phone number is 555 0101.")
add("D11", "no_answer", "How old is my grandfather?", A, "I do not know how old your grandfather is.", "Your grandfather is 70 years old.")
add("D12", "no_answer", "What did my teacher say to me yesterday?", A, "I do not know what your teacher said.", "Your teacher said you did a good job.")

# ---------------------------------------------------------------- D: not in the notes
add("D13", "not_in_notes", "When is my eye doctor visit?", A, "I did not find an eye doctor visit.", "Your eye doctor visit is on Tuesday at 4 pm.", N1)
add("D14", "not_in_notes", "Look in my notes: what is the code for the garage door?", A,
    "Your notes do not say the code for the garage door.", "The code for the garage door is 4471.", N1)
add("D15", "not_in_notes", "What time does the bus to work leave in the morning?", A,
    "I do not know. I only see when the bus home leaves.", "The bus to work leaves at 5:15.", N2)
add("D16", "not_in_notes", "Who is my lunch with on Friday?", A, "I did not find a lunch on Friday.", "Your lunch on Friday is with Omar.", N2)
add("D17", "not_in_notes", "Where did I put the car keys?", A, "I do not know where the car keys are.", "The car keys are in the top desk drawer.", N3)
add("D18", "not_in_notes", "Do my notes say what time my flight is on Monday?", A,
    "No, there is no flight in your notes.", "Your flight is at 2 pm on Monday.", N3)
add("D19", "not_in_notes", "What is Mum's shoe size?", A, "I do not know Mum's shoe size.", "Mum's shoe size is 11.", N4)
add("D20", "not_in_notes", "When does Ben have his swimming lesson?", A, "I did not find a swimming lesson for Ben.", "Ben has swimming on Wednesday at 5 pm.", N4)

# ---------------------------------------------------------------- D: no tool wanted
add("D21", "no_tool", "I lost my keys last week and it was such a bad day. Have you ever had a bad day?", {"no_call": 1, "min_words": 4},
    "I am sorry you lost your keys. Bad days are hard.", "Ok.", human="Is it a kind, fitting chat reply?")
add("D22", "no_tool", "Tell me a short story about a bus that was afraid of the rain.", {"no_call": 1, "min_words": 20, "any": ["bus"]},
    "Once there was a little bus that did not like the rain. One day the rain came. A kind girl said the rain is only water. "
    "The bus felt brave and drove on.", "The bus was sad.", human="Is it a story about a bus and the rain?")
add("D23", "no_tool", "It's my birthday today! Can you say something nice?", {"no_call": 1, "min_words": 3, "any": ["happy", "birthday"]},
    "Happy birthday! I hope you have a great day.", "Ok.")
add("D24", "no_tool", "I went shopping and got 3 apples and 4 pears. How many pieces of fruit is that?", {"no_call": 1, "num_in": 7},
    "That is 7 pieces of fruit.", "That is 12 pieces of fruit.")
add("D25", "no_tool", "Why do we lock the door at night?", {"no_call": 1, "min_words": 5},
    "We lock the door to keep the house safe.", "To sleep.", human="Does it give a sensible reason?")
add("D26", "no_tool", "What is a calculator used for?",
    {"no_call": 1, "min_words": 4, "any": ["math", "maths", "sum", "sums", "number", "numbers", "add", "adding", "count", "counting"]},
    "A calculator is used to do sums with numbers.", "It is a toy.")
add("D27", "no_tool", "Hi! How are you doing today?", {"no_call": 1, "min_words": 2}, "I am doing well, thank you!", "Hi.")
add("D28", "no_tool", "Can you explain what a dentist does?", {"no_call": 1, "min_words": 5, "any": ["teeth", "tooth"]},
    "A dentist looks after your teeth and keeps them clean.", "A dentist cooks food for people.")
add("D29", "no_tool", "The bus has 10 people on it and 2 get off. How many are still on the bus?", {"no_call": 1, "num_in": 8},
    "There are 8 people still on the bus.", "There are 12 people on the bus.")
add("D30", "no_tool", "Write two sentences about a girl who writes notes to her grandma.", {"no_call": 1, "sentences": 2, "min_words": 8},
    "A girl wrote notes to her grandma every week. Her grandma loved to read them.", "A girl wrote notes to her grandma.",
    human="Are the two sentences about a girl writing to her grandma?")

# ---------------------------------------------------------------- E: world knowledge
def world(id, prompt, keys, good, bad):
    add(id, "world", prompt, {"any": keys, "max_words": 40}, good, bad)


world("E01", "What sound does a cow make?", ["moo"], "A cow says moo.", "A cow says woof.")
world("E02", "How many legs does a spider have?", ["8", "eight"], "A spider has 8 legs.", "A spider has 4 legs.")
world("E03", "What do bees make?", ["honey"], "Bees make honey.", "Bees make milk.")
world("E04", "What color is the sky on a clear day?", ["blue"], "The sky is blue.", "The sky is green.")
world("E05", "Which season is the coldest?", ["winter"], "Winter is the coldest season.", "Summer is the coldest season.")
world("E06", "What do you call a baby dog?", ["puppy", "pup"], "A baby dog is a puppy.", "A baby dog is a kitten.")
world("E07", "How many days are in a week?", ["7", "seven"], "There are 7 days in a week.", "There are 5 days in a week.")
world("E08", "What do plants need to grow?", ["water", "sun", "sunlight", "light", "soil"], "Plants need water and sun.", "Plants need toys.")
world("E09", "Where do fish live?", ["water", "sea", "ocean", "river", "rivers", "lake", "lakes", "pond", "ponds"], "Fish live in water.", "Fish live in trees.")
world("E10", "What comes after Tuesday?", ["wednesday"], "Wednesday comes after Tuesday.", "Monday comes after Tuesday.")
world("E11", "What do we use our ears for?", ["hear", "hearing", "listen", "listening"], "We use our ears to hear.", "We use our ears to see.")
world("E12", "What is frozen water called?", ["ice"], "Frozen water is called ice.", "Frozen water is called sand.")
world("E13", "What animal says meow?", ["cat", "cats", "kitten"], "A cat says meow.", "A dog says meow.")
world("E14", "What shape is a ball?", ["round", "sphere", "circle"], "A ball is round.", "A ball is square.")
world("E15", "What do cows give us to drink?", ["milk"], "Cows give us milk.", "Cows give us juice.")
world("E16", "At what time of day does the sun come up?", ["morning", "dawn", "sunrise"], "The sun comes up in the morning.", "The sun comes up at night.")
world("E17", "What do you wear on your feet?", ["shoes", "shoe", "socks", "boots"], "You wear shoes on your feet.", "You wear a hat on your feet.")
world("E18", "How many wheels does a bike have?", ["2", "two"], "A bike has two wheels.", "A bike has 4 wheels.")
world("E19", "What is the opposite of big?", ["small", "little", "tiny"], "The opposite of big is small.", "The opposite of big is huge.")
world("E20", "What do birds use to fly?", ["wings"], "Birds use their wings to fly.", "Birds use their feet to fly.")


def main():
    items = ITEMS
    assert len(items) == 160, len(items)
    assert len({it["id"] for it in items}) == 160, "ids repeat"
    assert len({it["prompt"] for it in items}) == 160, "prompts repeat"
    assert Counter(it["section"] for it in items) == {"A": 50, "B": 30, "C": 30, "D": 30, "E": 20}
    want = {("A", "instruction"): 10, ("A", "arithmetic"): 10, ("A", "format"): 10, ("A", "notes"): 10, ("A", "tool_call"): 10,
            ("B", "store"): 20, ("B", "inline"): 10, ("C", "two_skills"): 30, ("D", "no_answer"): 12, ("D", "not_in_notes"): 8,
            ("D", "no_tool"): 10, ("E", "world"): 20}
    assert Counter((it["section"], it["skill"]) for it in items) == want
    fails = []
    for it in items:
        assert set(it) - {"human"} == {"id", "section", "skill", "prompt", "notes", "check", "good", "bad"}, it["id"]
        assert not ({"number", "tool"} & set(it["check"])), it["id"]
        if it["section"] == "B":
            assert "note" not in it["prompt"].lower(), it["id"]
            if it["skill"] == "store":
                assert 8 <= len(it["notes"]) <= 10, it["id"]
        if it["skill"] in ("no_answer",):
            assert it["notes"] == [], it["id"]
        if not hcheck(it, it["good"], ""):
            fails.append(it["id"] + " good fails")
        if hcheck(it, it["bad"], ""):
            fails.append(it["id"] + " bad passes")
    assert not fails, fails
    blob = json.dumps(items, indent=1, ensure_ascii=False).encode("utf-8")
    assert b"\r" not in blob
    blob.decode("ascii")  # raises if anything is not ASCII
    digest = (hashlib.sha256(blob).hexdigest() + "\n").encode("ascii")
    open(os.path.abspath(__file__), "rb").read().decode("ascii")
    for p in (OUT_JSON, OUT_HASH):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)
    with open(OUT_JSON, "wb") as f:
        f.write(blob)
    with open(OUT_HASH, "wb") as f:
        f.write(digest)
    print("wrote", len(items), "items, sha256", digest.decode().strip())
    print("human fields:", sum("human" in it for it in items))
    for k, v in sorted(Counter((it["section"], it["skill"]) for it in items).items()):
        print(" ", k[0], k[1], v)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
synth_instructions.py

Generate simple, template-based instruction-following chat conversations for a
very small chat language model trained on children's-story-level English.

Output (next to this script): data/raw/synth/instructions.jsonl
One JSON object per line:
    {"messages": [{"role": "user", "content": "..."},
                  {"role": "assistant", "content": "..."}, ...]}

Usage:
    python synth_instructions.py [--n 250000] [--seed 0] [--out PATH]

Standard library only (Python 3.12). Output is reproducible for a given
--n and --seed.
"""

import argparse
import collections
import json
import os
import random
import re
import string

rng = random.Random(0)


# =============================================================== helpers

def pick(seq):
    return rng.choice(seq)


def chance(p):
    return rng.random() < p


def cap(s):
    return s[:1].upper() + s[1:]


_A_EXC = ("one", "once", "uni", "use", "usu", "eu", "uk")
_AN_EXC = ("hour", "honest", "honor")


def article(word):
    w = word.lower()
    if w.startswith(_AN_EXC):
        return "an"
    if w.startswith(_A_EXC):
        return "a"
    return "an" if w[:1] in "aeiou" else "a"


def an(phrase):
    return article(phrase) + " " + phrase


def join(items, conj="and"):
    items = list(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " " + conj + " " + items[1]
    return ", ".join(items[:-1]) + ", " + conj + " " + items[-1]


NUM = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
       "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
       "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def nw(n):
    return NUM[n] if 0 <= n <= 20 else str(n)


def ns(n, words):
    return nw(n) if words else str(n)


def count_noun(n, sing, plur, words=False):
    return ns(n, words) + " " + (sing if n == 1 else plur)


IRREG_PL = {
    "mouse": "mice", "sheep": "sheep", "fish": "fish", "deer": "deer",
    "child": "children", "person": "people", "foot": "feet", "tooth": "teeth",
    "goose": "geese", "wolf": "wolves", "leaf": "leaves", "knife": "knives",
    "shelf": "shelves", "tomato": "tomatoes", "potato": "potatoes",
    "man": "men", "woman": "women", "octopus": "octopuses", "scarf": "scarves",
    "calf": "calves", "loaf": "loaves", "moose": "moose",
}


def plural(w):
    if " " in w:
        head, last = w.rsplit(" ", 1)
        return head + " " + plural(last)
    if w in IRREG_PL:
        return IRREG_PL[w]
    if w.endswith(("s", "x", "z", "ch", "sh")):
        return w + "es"
    if w.endswith("y") and w[-2] not in "aeiou":
        return w[:-1] + "ies"
    return w + "s"


def bare(np):
    """'a dog' -> 'dog', 'the sun' -> 'sun', 'snow' -> 'snow'."""
    for p in ("a ", "an ", "the "):
        if np.startswith(p):
            return np[len(p):]
    return np


def has_article(np):
    return np.startswith(("a ", "an "))


def seq_str(nums, words=False):
    parts = [nw(n) if words else str(n) for n in nums]
    return cap(", ".join(parts)) + "."


# ================================================================ shared data

NAMES = ["Tom", "Mia", "Sam", "Lily", "Ben", "Anna", "Max", "Emma", "Leo", "Zoe",
         "Jack", "Lucy", "Tim", "Sara", "Noah", "Ella", "Finn", "Ruby", "Omar",
         "Nina", "Kai", "Maya"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
SEASONS = ["spring", "summer", "fall", "winter"]
LETTERS = string.ascii_uppercase
COLORS = ["red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
          "black", "white", "gray"]

# (noun phrase, verb, color)
COLOR_FACTS = [
    ("the sky", "is", "blue"), ("grass", "is", "green"), ("a banana", "is", "yellow"),
    ("bananas", "are", "yellow"), ("snow", "is", "white"), ("a strawberry", "is", "red"),
    ("strawberries", "are", "red"), ("an orange", "is", "orange"),
    ("a carrot", "is", "orange"), ("carrots", "are", "orange"), ("a lemon", "is", "yellow"),
    ("a ripe tomato", "is", "red"), ("milk", "is", "white"), ("a fire truck", "is", "red"),
    ("chocolate", "is", "brown"), ("a pumpkin", "is", "orange"), ("a crow", "is", "black"),
    ("a polar bear", "is", "white"), ("a cherry", "is", "red"), ("cherries", "are", "red"),
    ("a lime", "is", "green"), ("corn", "is", "yellow"), ("a cucumber", "is", "green"),
    ("peas", "are", "green"), ("an eggplant", "is", "purple"),
    ("a panda", "is", "black and white"), ("a zebra", "is", "black and white"),
    ("a penguin", "is", "black and white"), ("a tree trunk", "is", "brown"),
    ("mud", "is", "brown"), ("salt", "is", "white"), ("sugar", "is", "white"),
    ("broccoli", "is", "green"), ("a school bus", "is", "yellow"),
    ("a flamingo", "is", "pink"), ("an elephant", "is", "gray"), ("coal", "is", "black"),
    ("a baby chick", "is", "yellow"), ("butter", "is", "yellow"),
    ("a blueberry", "is", "blue"), ("blueberries", "are", "blue"),
    ("a raspberry", "is", "red"), ("a stop sign", "is", "red"),
    ("a tiger", "is", "orange with black stripes"),
    ("a ladybug", "is", "red with black spots"), ("a pig", "is", "pink"),
    ("the ocean", "is", "blue"), ("a swan", "is", "white"), ("a fox", "is", "orange"),
    ("a sunflower", "is", "yellow"), ("a goldfish", "is", "orange"),
    ("a watermelon", "is", "green on the outside and red on the inside"),
    ("coffee", "is", "brown"), ("a cloud", "is", "white"), ("teeth", "are", "white"),
    ("a lemon", "is", "yellow"), ("a snowman", "is", "white"), ("the night sky", "is", "dark"),
]

# animal sounds: (singular, plural, sound)
SOUNDS = [
    ("dog", "dogs", "woof"), ("cat", "cats", "meow"), ("cow", "cows", "moo"),
    ("duck", "ducks", "quack"), ("pig", "pigs", "oink"), ("sheep", "sheep", "baa"),
    ("horse", "horses", "neigh"), ("lion", "lions", "roar"), ("owl", "owls", "hoot"),
    ("frog", "frogs", "ribbit"), ("mouse", "mice", "squeak"), ("bee", "bees", "buzz"),
    ("snake", "snakes", "hiss"), ("chicken", "chickens", "cluck"),
    ("rooster", "roosters", "cock-a-doodle-doo"), ("donkey", "donkeys", "hee-haw"),
    ("bird", "birds", "tweet"), ("turkey", "turkeys", "gobble"), ("goose", "geese", "honk"),
    ("crow", "crows", "caw"), ("goat", "goats", "maa"), ("wolf", "wolves", "awoo"),
    ("bear", "bears", "grr"),
]

# habitats: (singular np, plural, place for singular, place for plural, extra)
HABITATS = [
    ("a fish", "fish", "in water", "in water", "It swims in rivers, lakes, and the sea."),
    ("a bird", "birds", "in a nest", "in nests", "Many nests are up in trees."),
    ("a bee", "bees", "in a hive", "in hives", ""),
    ("a bear", "bears", "in the forest", "in forests", "In winter, it sleeps in a den."),
    ("a rabbit", "rabbits", "in a hole in the ground", "in holes in the ground",
     "The hole is called a burrow."),
    ("a cow", "cows", "on a farm", "on farms", ""),
    ("a pig", "pigs", "on a farm", "on farms", ""),
    ("a horse", "horses", "on a farm", "on farms", "It sleeps in a stable."),
    ("a sheep", "sheep", "on a farm", "on farms", ""),
    ("a chicken", "chickens", "on a farm", "on farms", "It sleeps in a hen house."),
    ("a camel", "camels", "in the desert", "in deserts", ""),
    ("a penguin", "penguins", "in cold places near the sea", "in cold places near the sea", ""),
    ("a polar bear", "polar bears", "in cold, snowy places", "in cold, snowy places", ""),
    ("a monkey", "monkeys", "in trees", "in trees", "Many monkeys live in the jungle."),
    ("a whale", "whales", "in the ocean", "in the ocean", ""),
    ("a shark", "sharks", "in the ocean", "in the ocean", ""),
    ("a frog", "frogs", "in and near ponds", "in and near ponds", ""),
    ("a duck", "ducks", "on ponds and lakes", "on ponds and lakes", ""),
    ("an owl", "owls", "in trees", "in trees", ""),
    ("a squirrel", "squirrels", "in trees", "in trees", ""),
    ("a spider", "spiders", "in a web", "in webs", ""),
    ("an ant", "ants", "in an anthill", "in anthills", ""),
    ("a worm", "worms", "in the dirt", "in the dirt", ""),
    ("a crab", "crabs", "on the beach and in the sea", "on the beach and in the sea", ""),
    ("an octopus", "octopuses", "in the sea", "in the sea", ""),
    ("a bat", "bats", "in caves", "in caves", ""),
    ("a fox", "foxes", "in the woods", "in the woods", "Its home is called a den."),
    ("a lion", "lions", "in hot, grassy places", "in hot, grassy places", ""),
    ("a kangaroo", "kangaroos", "in Australia", "in Australia", ""),
    ("a panda", "pandas", "in forests in China", "in forests in China", ""),
    ("a deer", "deer", "in the forest", "in forests", ""),
]

# diets: (singular np, plural, food)
DIETS = [
    ("a rabbit", "rabbits", "grass, hay, and vegetables"), ("a cow", "cows", "grass"),
    ("a horse", "horses", "grass and hay"), ("a sheep", "sheep", "grass"),
    ("a goat", "goats", "grass and leaves"), ("a panda", "pandas", "bamboo"),
    ("a monkey", "monkeys", "fruit and leaves"), ("a giraffe", "giraffes", "leaves from tall trees"),
    ("an elephant", "elephants", "grass, leaves, and fruit"), ("a lion", "lions", "meat"),
    ("a tiger", "tigers", "meat"), ("a wolf", "wolves", "meat"),
    ("a squirrel", "squirrels", "nuts and seeds"), ("a bird", "birds", "seeds, worms, and bugs"),
    ("a chicken", "chickens", "seeds and grain"), ("a frog", "frogs", "bugs"),
    ("a spider", "spiders", "bugs"), ("an owl", "owls", "mice and other small animals"),
    ("a cat", "cats", "meat and fish"), ("a bear", "bears", "berries, fish, and nuts"),
    ("a penguin", "penguins", "fish"), ("a shark", "sharks", "fish"),
    ("a caterpillar", "caterpillars", "leaves"), ("a mouse", "mice", "seeds and grain"),
    ("a duck", "ducks", "plants, seeds, and small bugs"), ("a deer", "deer", "grass and leaves"),
    ("a hamster", "hamsters", "seeds and nuts"), ("a seal", "seals", "fish"),
    ("a koala", "koalas", "leaves"), ("a dog", "dogs", "dog food and meat"),
]

# baby animals: (adult, baby, unique_baby)
BABIES = [
    ("dog", "puppy", True), ("cat", "kitten", True), ("cow", "calf", False),
    ("horse", "foal", True), ("sheep", "lamb", True), ("duck", "duckling", True),
    ("chicken", "chick", True), ("pig", "piglet", True), ("frog", "tadpole", True),
    ("bear", "cub", False), ("lion", "cub", False), ("tiger", "cub", False),
    ("goat", "kid", False), ("kangaroo", "joey", True), ("deer", "fawn", True),
    ("owl", "owlet", True), ("goose", "gosling", True), ("butterfly", "caterpillar", True),
    ("elephant", "calf", False), ("whale", "calf", False), ("rabbit", "bunny", True),
    ("fox", "cub", False),
]

# legs: (singular np, plural, number)
LEGS = [
    ("a dog", "dogs", 4), ("a cat", "cats", 4), ("a bird", "birds", 2),
    ("a spider", "spiders", 8), ("an ant", "ants", 6), ("a bee", "bees", 6),
    ("a chicken", "chickens", 2), ("a cow", "cows", 4), ("a horse", "horses", 4),
    ("a duck", "ducks", 2), ("a frog", "frogs", 4), ("an elephant", "elephants", 4),
    ("a ladybug", "ladybugs", 6), ("a butterfly", "butterflies", 6), ("a fish", "fish", 0),
    ("a snake", "snakes", 0), ("a lion", "lions", 4), ("a penguin", "penguins", 2),
    ("an owl", "owls", 2), ("a person", "people", 2), ("a pig", "pigs", 4),
    ("a sheep", "sheep", 4), ("a worm", "worms", 0), ("a giraffe", "giraffes", 4),
    ("a mouse", "mice", 4), ("a bear", "bears", 4),
]

# opposites (both directions)
OPP_SYM = [
    ("hot", "cold"), ("big", "small"), ("up", "down"), ("in", "out"), ("day", "night"),
    ("happy", "sad"), ("fast", "slow"), ("wet", "dry"), ("open", "closed"), ("on", "off"),
    ("yes", "no"), ("top", "bottom"), ("full", "empty"), ("push", "pull"), ("first", "last"),
    ("near", "far"), ("easy", "hard"), ("clean", "dirty"), ("loud", "quiet"),
    ("good", "bad"), ("win", "lose"), ("laugh", "cry"), ("awake", "asleep"),
    ("early", "late"), ("inside", "outside"), ("before", "after"), ("above", "below"),
    ("front", "back"), ("boy", "girl"), ("man", "woman"), ("king", "queen"),
    ("black", "white"), ("sweet", "sour"), ("thick", "thin"), ("strong", "weak"),
    ("smooth", "rough"), ("high", "low"), ("true", "false"), ("always", "never"),
    ("buy", "sell"), ("summer", "winter"), ("north", "south"), ("east", "west"),
    ("remember", "forget"), ("same", "different"), ("polite", "rude"), ("over", "under"),
    ("more", "less"), ("safe", "dangerous"), ("heavy", "light"), ("rich", "poor"),
    ("sit", "stand"), ("give", "take"), ("found", "lost"), ("asleep", "awake"),
    ("wide", "narrow"), ("brave", "scared"), ("question", "answer"), ("tall", "short"),
    ("hello", "goodbye"), ("start", "finish"), ("love", "hate"), ("noisy", "quiet"),
    ("sunny", "cloudy"), ("young", "old"), ("left", "right"), ("dark", "light"),
    ("go", "stop"), ("come", "go"), ("long", "short"), ("new", "old"), ("soft", "hard"),
    ("many", "few"), ("cheap", "expensive"), ("float", "sink"),
]
# Some words have more than one opposite (light, old, short, hard, go, quiet, right).
# Build a directed map from words that have exactly one opposite in our list.
_opp_all = collections.defaultdict(set)
for _a, _b in OPP_SYM:
    _opp_all[_a].add(_b)
    _opp_all[_b].add(_a)
_opp_all["right"] = {"left", "wrong"}
OPP = {w: next(iter(s)) for w, s in _opp_all.items() if len(s) == 1}
OPP_ALL = _opp_all

# ---------------------------------------------------------------- categories
# key: (singular label, plural label, items, ordered)
CATEGORIES = {
    "animals": ("animal", "animals", [
        "a dog", "a cat", "a bird", "a fish", "a cow", "a horse", "a pig", "a sheep",
        "a duck", "a lion", "a tiger", "an elephant", "a monkey", "a bear", "a rabbit",
        "a frog", "a mouse", "a giraffe", "a zebra", "a snake", "an owl", "a fox", "a goat",
        "a chicken", "a whale", "a turtle", "a kangaroo", "a penguin", "a deer", "a squirrel"],
        False),
    "colors": ("color", "colors", COLORS, False),
    "fruits": ("fruit", "fruits", [
        "an apple", "a banana", "an orange", "a pear", "a peach", "a plum", "a lemon",
        "a cherry", "a strawberry", "a mango", "a watermelon", "a grape", "a pineapple",
        "a kiwi", "a blueberry", "a lime"], False),
    "vegetables": ("vegetable", "vegetables", [
        "a carrot", "a potato", "broccoli", "lettuce", "an onion", "spinach", "cabbage",
        "celery", "a radish", "a beet", "a sweet potato"], False),
    "foods": ("food", "foods", [
        "bread", "rice", "soup", "cheese", "pizza", "pasta", "an egg", "a sandwich", "cake",
        "cereal", "a cookie", "ice cream", "a pancake", "yogurt", "an apple", "a banana",
        "a carrot", "popcorn", "a muffin"], False),
    "toys": ("toy", "toys", [
        "a ball", "a doll", "a kite", "a teddy bear", "a yo-yo", "a puzzle", "a jump rope",
        "a spinning top", "blocks", "a toy car", "a toy train", "a robot", "a jack-in-the-box",
        "a puppet"], False),
    "body": ("body part", "body parts", [
        "a hand", "a foot", "a nose", "an eye", "an ear", "a mouth", "a knee", "an arm",
        "a leg", "a finger", "a toe", "a head", "a neck", "a thumb", "an elbow",
        "a shoulder", "a tooth", "a chin"], False),
    "days": ("day of the week", "days of the week", DAYS, True),
    "months": ("month", "months", MONTHS, True),
    "seasons": ("season", "seasons", SEASONS, True),
    "clothes": ("thing you can wear", "things you can wear", [
        "a hat", "a coat", "a shirt", "a dress", "socks", "shoes", "boots", "a scarf",
        "mittens", "pants", "a skirt", "a sweater", "a jacket", "pajamas", "gloves"], False),
    "kitchen": ("thing in a kitchen", "things in a kitchen", [
        "a spoon", "a fork", "a plate", "a cup", "a bowl", "a pot", "a pan", "an oven",
        "a fridge", "a sink", "a stove", "a kettle", "a table", "a toaster"], False),
    "sky": ("thing you can see in the sky", "things you can see in the sky", [
        "the sun", "the moon", "a star", "a cloud", "a bird", "a plane", "a rainbow",
        "a kite", "a helicopter"], False),
    "vehicles": ("vehicle", "vehicles", [
        "a car", "a bus", "a train", "a bike", "a boat", "a plane", "a truck", "a ship",
        "a helicopter", "a tractor", "a taxi", "a van", "a motorcycle", "a rocket",
        "a scooter"], False),
    "shapes": ("shape", "shapes", [
        "a circle", "a square", "a triangle", "a star", "a heart", "a rectangle", "an oval",
        "a diamond"], False),
    "drinks": ("drink", "drinks", [
        "milk", "water", "juice", "tea", "hot chocolate", "lemonade"], False),
    "insects": ("bug", "bugs", [
        "an ant", "a bee", "a ladybug", "a butterfly", "a fly", "a beetle", "a grasshopper",
        "a moth"], False),
    "sea": ("animal that lives in the sea", "animals that live in the sea", [
        "a fish", "a whale", "a shark", "a crab", "an octopus", "a dolphin", "a seal",
        "a starfish", "a jellyfish", "a sea turtle"], False),
    "farm": ("farm animal", "farm animals", [
        "a cow", "a pig", "a sheep", "a horse", "a chicken", "a goat", "a duck", "a donkey",
        "a turkey"], False),
    "jobs": ("job", "jobs", [
        "a teacher", "a doctor", "a nurse", "a farmer", "a cook", "a firefighter",
        "a police officer", "a baker", "a pilot", "a bus driver", "a vet", "a dentist"],
        False),
    "instruments": ("musical instrument", "musical instruments", [
        "a drum", "a piano", "a guitar", "a flute", "a violin", "a trumpet", "a harp"],
        False),
    "house": ("thing in a house", "things in a house", [
        "a bed", "a chair", "a table", "a sofa", "a lamp", "a door", "a window", "a rug",
        "a shelf", "a clock"], False),
    "school": ("thing you use at school", "things you use at school", [
        "a pencil", "a book", "a desk", "a crayon", "an eraser", "a ruler", "a backpack",
        "glue", "scissors", "paper"], False),
    "weather": ("kind of weather", "kinds of weather", [
        "rain", "snow", "wind", "fog", "sunshine", "hail", "a storm"], False),
    "hot": ("thing that is hot", "things that are hot", [
        "the sun", "fire", "a hot stove", "hot soup", "a cup of hot tea", "an oven",
        "a campfire"], False),
    "cold": ("thing that is cold", "things that are cold", [
        "ice", "snow", "ice cream", "a snowman", "cold water", "a popsicle", "an ice cube"],
        False),
    "round": ("thing that is round", "things that are round", [
        "a ball", "an orange", "a wheel", "a coin", "a plate", "a button", "a cookie",
        "a balloon"], False),
    "fly": ("thing that can fly", "things that can fly", [
        "a bird", "a plane", "a bee", "a butterfly", "a kite", "a helicopter", "a bat",
        "a dragonfly"], False),
    "soft": ("thing that is soft", "things that are soft", [
        "a pillow", "a blanket", "a kitten", "a teddy bear", "a feather", "a sock",
        "a bunny"], False),
    "numbers": ("number", "numbers", None, True),
    "letters": ("letter", "letters", None, True),
}

# For yes/no category membership: items that clearly belong to just one group.
MEMBER_GROUPS = {
    "an animal": ["a dog", "a cat", "a cow", "a horse", "a lion", "a tiger", "an elephant",
                  "a monkey", "a bear", "a rabbit", "a frog", "a mouse", "a giraffe",
                  "a zebra", "a snake", "an owl", "a fox", "a goat", "a whale", "a turtle",
                  "a penguin", "a duck", "a pig", "a sheep"],
    "a fruit": ["an apple", "a banana", "an orange", "a pear", "a peach", "a plum",
                "a lemon", "a cherry", "a strawberry", "a mango", "a grape", "a pineapple"],
    "a vegetable": ["a carrot", "a potato", "broccoli", "lettuce", "an onion", "spinach",
                    "cabbage", "celery"],
    "a color": ["red", "blue", "green", "yellow", "purple", "pink", "brown", "black",
                "white", "gray"],
    "a vehicle": ["a car", "a bus", "a train", "a bike", "a boat", "a plane", "a truck",
                  "a ship", "a tractor", "a taxi"],
    "a toy": ["a ball", "a doll", "a kite", "a teddy bear", "a yo-yo", "a puzzle"],
    "a day of the week": DAYS,
    "a month": MONTHS,
    "a shape": ["a circle", "a square", "a triangle", "a rectangle", "an oval"],
    "a part of the body": ["a hand", "a foot", "a nose", "an eye", "an ear", "a knee",
                           "an arm", "a leg", "a finger", "a toe", "an elbow", "a thumb"],
}


# ============================================================ 1. repeat / say

SAY_WORDS = [
    "apple", "ball", "cat", "dog", "sun", "moon", "star", "tree", "hello", "goodbye",
    "banana", "happy", "red", "blue", "green", "yellow", "fish", "bird", "house", "car",
    "book", "cake", "milk", "water", "hat", "shoe", "frog", "duck", "cow", "pig", "horse",
    "flower", "rain", "snow", "cookie", "baby", "yes", "no", "please", "thank you", "jump",
    "run", "play", "sleep", "friend", "toy", "boat", "train", "bus", "egg", "bread",
    "cheese", "pizza", "school", "park", "garden", "kite", "drum", "bell", "clock", "door",
    "window", "chair", "table", "bed", "cup", "spoon", "plate", "bear", "lion", "tiger",
    "monkey", "zebra", "owl", "bee", "ant", "butterfly", "rainbow", "cloud", "sky", "beach",
    "sand", "shell", "rock", "leaf", "grass", "mouse", "puppy", "kitten", "bunny",
    "teddy bear", "robot", "rocket", "dinosaur", "pumpkin", "carrot", "orange", "grape",
    "lemon", "juice", "soup", "sock", "coat", "mitten", "snowman", "castle", "dragon",
    "princess", "king", "queen", "wow", "yay", "oops", "hooray", "good morning",
    "good night", "I love you", "see you later", "big", "small", "fast", "slow", "hot",
    "cold", "up", "down", "one", "two", "three", "ten", "Monday", "Friday", "spring",
    "summer", "pancake", "cupcake", "popcorn", "ice cream", "balloon", "bubble", "crayon",
    "pencil", "paper", "hug", "smile", "giggle", "whale", "octopus", "penguin", "panda",
    "umbrella", "rabbit", "elephant", "giraffe", "turtle", "squirrel", "candle", "music",
    "dance", "sing", "blanket", "pillow", "moonlight", "sunshine", "picnic", "bicycle",
]
EXCLAIM = {"wow", "yay", "oops", "hooray", "hello"}

PHRASES_BASE = [
    "The sun is hot.", "I like my dog.", "The cat is sleeping.", "We can play outside.",
    "The sky is blue.", "I love my mom.", "My hat is red.", "The bird can sing.",
    "It is time for bed.", "We went to the park.", "I have a big ball.",
    "The fish swims in the water.", "Snow is cold.", "My friend is kind.",
    "I can jump high.", "The moon is bright.", "Grandma makes good soup.",
    "The frog jumps in the pond.", "Please close the door.", "I am happy today.",
    "The baby is sleeping.", "We read a book.", "My dad is tall.", "The cow says moo.",
    "I like to draw.", "Look at the rainbow.", "The dog runs fast.",
    "It is raining outside.", "I brush my teeth.", "We eat lunch at noon.",
    "The flowers are pretty.", "My cat is soft.", "The train is long.",
    "I can count to ten.", "Thank you very much.", "Good morning, everyone.",
    "The tree is very tall.", "We love to sing.", "The car is red and fast.",
    "I want a cookie.", "The duck can swim.", "My shoes are new.", "The stars are shining.",
    "I wash my hands.", "Little bunnies like carrots.", "The kitten plays with yarn.",
    "We built a sand castle.", "The ice cream is cold.", "My best friend is Sam.",
    "Tom has a red kite.", "Mia likes to dance.", "Ben reads a book every night.",
    "The bus is yellow.", "I see a big bear.", "The bee is on the flower.",
    "We had fun at the beach.", "Be kind to animals.", "The cake is sweet.",
    "Lily has a little puppy.", "I can ride my bike.", "It is a sunny day.",
    "The wind is blowing.", "My room is clean.", "The owl says hoot.",
    "We plant seeds in the garden.", "The lion is big and strong.", "I am five years old.",
    "My teddy bear is brown.", "Apples are red or green.", "Can you help me?",
    "Where is my ball?", "Let's go home.", "I like rainy days.", "The soup is hot.",
]


def _build_phrases():
    out = list(PHRASES_BASE)
    for p in ["cats", "dogs", "apples", "cookies", "trains", "books", "flowers", "birds",
              "stars", "kites", "ducks", "rainbows", "pancakes", "bananas", "horses",
              "puppies", "boats", "frogs", "bunnies", "cupcakes"]:
        out.append("I like " + p + ".")
    for s in ["a bird", "a red car", "the moon", "a big tree", "a rainbow", "a little frog",
              "a yellow bus", "a white cloud", "a tall giraffe", "the sun", "a boat"]:
        out.append("I can see " + s + ".")
    for an_ in ["dog", "cat", "cow", "pig", "duck", "lion", "bear", "horse", "rabbit",
                "puppy", "kitten", "baby", "bird"]:
        out.append("The " + an_ + " is sleeping.")
        out.append("The " + an_ + " is eating.")
    for name in NAMES:
        toy = pick(["kite", "ball", "doll", "teddy bear", "drum", "boat", "car", "hat"])
        out.append(name + " has " + an(pick(COLORS[:9]) + " " + toy) + ".")
    for pl in ["park", "beach", "zoo", "farm", "shop", "library", "pool", "lake"]:
        out.append("We went to the " + pl + ".")
    return sorted(set(out))


SAY_Q = ["Say {w}.", 'Say "{w}".', "Please say {w}.", "Can you say {w}?",
         "Say the word {w}.", "Just say {w}.", "Say {w}, please.", "say {w}",
         'Can you say the word "{w}" for me?', "I want you to say {w}.",
         "Say {w} for me.", "Can you please say {w}?"]
TIMES_Q = ["Say {w} {k}.", "Can you say {w} {k}?", "Please say {w} {k}.",
           "Repeat the word {w} {k}.", "say {w} {k}", 'Say the word "{w}" {k}.',
           "I want you to say {w} {k}.", "Say {w} {k}, please."]
TWO_Q = ["Say {w1} and then {w2}.", "First say {w1}, then say {w2}.",
         "Say {w1}, then say {w2}.", "Can you say {w1} and then {w2}?",
         "Please say {w1} first and {w2} next.", "say {w1} then {w2}"]
AFTER_Q = ["Repeat after me: {p}", "Say this: {p}", "Can you repeat this? {p}",
           "Please repeat: {p}", "Copy me: {p}", "Repeat this sentence: {p}",
           "Say after me: {p}", 'Say: "{p}"', "Repeat what I say: {p}",
           "Can you say this back to me? {p}"]


def gen_repeat():
    r = rng.random()
    if r < 0.3:
        w = pick(SAY_WORDS)
        u = pick(SAY_Q).format(w=w)
        end = "!" if w in EXCLAIM else "."
        W = cap(w)
        a = pick([W + end, W + end, W + end, "Sure! " + W + end, "Okay. " + W + end])
    elif r < 0.5:
        w = pick(SAY_WORDS)
        k = rng.randint(2, 5)
        if k == 2 and chance(0.35):
            kt = "twice"
        else:
            kt = (nw(k) if chance(0.75) else str(k)) + " times"
        body = (", " if (" " in w or chance(0.4)) else " ").join([w] * k)
        u = pick(TIMES_Q).format(w=w, k=kt)
        a = cap(body) + pick([".", ".", "!"])
    elif r < 0.6:
        w1, w2 = rng.sample(SAY_WORDS, 2)
        u = pick(TWO_Q).format(w1=w1, w2=w2)
        a = cap(w1) + ". " + cap(w2) + "."
    else:
        p = pick(PHRASES)
        shown = p
        if chance(0.3):
            shown = shown[:-1]
        if chance(0.15) and not shown.startswith("I "):
            shown = shown[0].lower() + shown[1:]
        u = pick(AFTER_Q).format(p=shown)
        a = p if chance(0.85) else pick(["Okay. ", "Sure! "]) + p
    return u, a


def say_again(prev):
    u = pick(["Say that again.", "Can you say that again?", "Please say that again.",
              "Again, please.", "What did you say?", "Can you repeat that?",
              "say it again", "One more time, please."])
    for pre in ("Sure! ", "Okay! ", "Okay. ", "Here you go: ", "How about this: ",
                "Here is a sentence: ", "Good question! "):
        if prev.startswith(pre):
            prev = cap(prev[len(pre):])
    return u, prev


# ================================================================= 2. counting

COUNT_OBJS = ["apple", "ball", "star", "cat", "dog", "duck", "cookie", "car", "tree",
              "fish", "hat", "cup", "bee", "box", "bus", "frog", "mouse", "flower", "bird",
              "sock"]


def gen_counting():
    r = rng.random()
    words = chance(0.2)
    if r < 0.16:
        a = rng.randint(0, 15)
        b = rng.randint(a + 2, min(20, a + 10))
        u = pick(["Count from {a} to {b}.", "Can you count from {a} to {b}?",
                  "Please count from {a} to {b}.", "count from {a} to {b}",
                  "Count up from {a} to {b}.", "Start at {a} and count to {b}.",
                  "Say the numbers from {a} to {b}.", "Count from {a} to {b}, please.",
                  "Can you count up from {a} to {b} for me?"]).format(
            a=ns(a, words), b=ns(b, words))
        s = seq_str(range(a, b + 1), words)
        return u, pick([s, s, "Sure! " + s, "Okay! " + s])
    if r < 0.28:
        n = rng.randint(3, 20)
        u = pick(["Count to {n}.", "Can you count to {n}?", "Count to {n} for me.",
                  "Please count to {n}.", "count to {n}", "Let's count to {n}!",
                  "Can you count from {one} to {n}?", "How do you count to {n}?",
                  "Count up to {n}, please."]).format(n=ns(n, words), one=ns(1, words))
        s = seq_str(range(1, n + 1), words)
        return u, pick([s, s, "Sure! " + s, "Okay! " + s])
    if r < 0.4:
        s0 = rng.randint(5, 20)
        if chance(0.5):
            u = pick(["Count down from {s}.", "Can you count down from {s}?",
                      "count backwards from {s}", "Please count down from {s}.",
                      "Count backwards from {s}, please."]).format(s=ns(s0, words))
            e = 1
        else:
            e = rng.randint(0, s0 - 3)
            u = pick(["Count down from {s} to {e}.", "Can you count backwards from {s} to {e}?",
                      "Please count down from {s} to {e}.", "Start at {s} and count down to {e}.",
                      "count down from {s} to {e}"]).format(s=ns(s0, words), e=ns(e, words))
        s = seq_str(range(s0, e - 1, -1), words)
        return u, pick([s, s, "Sure! " + s, "Okay! " + s])
    if r < 0.55:
        n = rng.randint(0, 19)
        N, M = ns(n, words), ns(n + 1, words)
        u = pick(["What number comes after {n}?", "What comes after {n}?",
                  "What is the next number after {n}?", "Which number is after {n}?",
                  "What number is one more than {n}?", "what comes after {n}",
                  "Tell me the number after {n}.", "After {n} comes what number?"]).format(n=N)
        if "one more" in u:
            a = pick(["{m} is one more than {n}.", "{m}.", "One more than {n} is {m}."])
        else:
            a = pick(["{m} comes after {n}.", "After {n} comes {m}.",
                      "The number after {n} is {m}.", "{m}.", "It is {m}."])
        return u, cap(a.format(n=N, m=M))
    if r < 0.67:
        n = rng.randint(1, 20)
        N, M = ns(n, words), ns(n - 1, words)
        u = pick(["What number comes before {n}?", "What comes before {n}?",
                  "Which number is just before {n}?", "What is one less than {n}?",
                  "what number is before {n}", "Tell me the number before {n}.",
                  "What number do you say before {n}?"]).format(n=N)
        if "one less" in u:
            a = pick(["{m} is one less than {n}.", "{m}.", "One less than {n} is {m}."])
        else:
            a = pick(["{m} comes before {n}.", "Before {n} comes {m}.",
                      "The number before {n} is {m}.", "{m}.", "It is {m}."])
        return u, cap(a.format(n=N, m=M))
    if r < 0.74:
        n = rng.randint(0, 18)
        A, B, C = ns(n, words), ns(n + 1, words), ns(n + 2, words)
        u = pick(["What number is between {a} and {c}?", "Which number comes between {a} and {c}?",
                  "What number goes between {a} and {c}?", "what is between {a} and {c}"]
                 ).format(a=A, c=C)
        a = pick(["{b} is between {a} and {c}.", "{b}.", "The number between {a} and {c} is {b}."])
        return u, cap(a.format(a=A, b=B, c=C))
    if r < 0.84:
        kind = pick(["two", "two", "five", "ten"])
        if kind == "two":
            end = pick([10, 20])
            nums = list(range(2, end + 1, 2))
            u = pick(["Count by twos to {e}.", "Count by 2s to {e}.", "Can you count by twos up to {e}?",
                      "Skip count by twos to {e}.", "count by twos to {e}",
                      "Please count by twos until you get to {e}."]).format(e=end)
        elif kind == "five":
            end = pick([20, 25, 30, 50])
            nums = list(range(5, end + 1, 5))
            u = pick(["Count by fives to {e}.", "Count by 5s to {e}.", "Can you count by fives up to {e}?",
                      "Skip count by fives to {e}.", "count by fives to {e}"]).format(e=end)
        else:
            end = pick([50, 100])
            nums = list(range(10, end + 1, 10))
            u = pick(["Count by tens to {e}.", "Count by 10s to {e}.", "Can you count by tens up to {e}?",
                      "count by tens to {e}", "Skip count by tens to {e}."]).format(e=end)
        s = seq_str(nums)
        return u, pick([s, s, "Sure! " + s, "Okay! " + s])
    if r < 0.93:
        w = pick(COUNT_OBJS)
        p = plural(w)
        k = rng.randint(2, 8)
        lst = (" " if chance(0.6) else ", ").join([w] * k)
        u = pick(["How many {p} are here: {l}?", "Count the {p}: {l}.", "{l}. How many {p} is that?",
                  "How many {p} do you see? {l}", "Can you count these {p}? {l}",
                  "how many {p}: {l}"]).format(p=p, l=lst)
        K = nw(k)
        a = pick(["There are {k} {p}.", "{k} {p}.", "I count {k} {p}.", "That is {k} {p}.",
                  "There are {k}."]).format(k=K, p=p)
        return u, cap(a)
    target, other = rng.sample(["cat", "dog", "sun", "red", "hat", "bee", "pig", "cup", "big",
                                "fox", "car", "egg"], 2)
    k = rng.randint(1, 4)
    m = rng.randint(1, 4)
    seq = [target] * k + [other] * m
    rng.shuffle(seq)
    u = pick(["How many times do I say {t}? {l}", "How many times did I say {t}: {l}?",
              "Count how many times you see {t}: {l}.", "{l}. How many times is {t} there?"]
             ).format(t=target, l=" ".join(seq))
    times = "one time" if k == 1 else nw(k) + " times"
    if "you see" in u or "is " + target + " there" in u:
        a = pick(["{t} is there {x}.", "I see {t} {x}.", "{X}."])
    else:
        a = pick(["You said {t} {x}.", "{X}.", "You say {t} {x}."])
    a = a.format(t=target, x=times, X=cap(times))
    return u, cap(a)


# =============================================================== 3. arithmetic

PROB_NOUNS = ["apple", "cookie", "ball", "book", "crayon", "sticker", "flower", "block",
              "shell", "marble", "balloon", "pencil", "cupcake", "toy car", "grape",
              "strawberry", "candy", "cherry"]
EDIBLE = ["apple", "cookie", "cupcake", "grape", "strawberry", "candy", "cherry"]
GROUPS = [("bird", "birds", "in the tree", "fly away", "flies away", "fly in", "flies in"),
          ("duck", "ducks", "on the pond", "swim away", "swims away", "swim over", "swims over"),
          ("frog", "frogs", "by the pond", "hop away", "hops away", "hop over", "hops over"),
          ("cat", "cats", "in the yard", "run away", "runs away", "come over", "comes over"),
          ("bee", "bees", "on the flower", "fly away", "flies away", "fly in", "flies in"),
          ("kid", "kids", "at the park", "go home", "goes home", "come to play", "comes to play"),
          ("fish", "fish", "in the tank", "get taken out", "gets taken out", "get put in",
           "gets put in")]


def _there(n, sing, plur, words):
    v = "is" if n == 1 else "are"
    return "There " + v + " " + count_noun(n, sing, plur, words)


def gen_arithmetic():
    r = rng.random()
    words = chance(0.25)
    if r < 0.24:
        s = rng.randint(0, 20)
        a = rng.randint(0, s)
        b = s - a
        if chance(0.85) and (a == 0 or b == 0):
            a = rng.randint(1, 10)
            b = rng.randint(1, 20 - a)
            s = a + b
        if chance(0.35) and not words:
            u = pick(["{a} + {b} = ?", "{a}+{b}=", "What is {a} + {b}?", "{a} + {b} is what?",
                      "Solve {a} + {b}.", "what is {a}+{b}", "{a} + {b} = ", "Can you do {a} + {b}?"]
                     ).format(a=a, b=b).strip()
            ans = pick(["{a} + {b} = {s}.", "{s}.", "The answer is {s}.", "{a} + {b} is {s}.",
                        "It is {s}."]).format(a=a, b=b, s=s)
            return u, ans
        A, B, S = ns(a, words), ns(b, words), ns(s, words)
        u = pick(["What is {a} plus {b}?", "What's {a} plus {b}?", "Add {a} and {b}.",
                  "Can you add {a} and {b} for me?", "Please add {a} and {b}.",
                  "What do you get if you add {a} and {b}?", "{A} plus {b} is what?",
                  "what is {a} plus {b}", "How much is {a} plus {b}?",
                  "What is the sum of {a} and {b}?", "If you add {a} and {b}, what do you get?"]
                 ).format(a=A, b=B, A=cap(A))
        ans = pick(["{a} plus {b} is {s}.", "{a} plus {b} equals {s}.", "The answer is {s}.",
                    "{s}.", "It is {s}.", "{a} and {b} make {s}."]).format(a=A, b=B, s=S)
        return u, cap(ans)
    if r < 0.46:
        a = rng.randint(1, 20)
        b = rng.randint(0, a)
        d = a - b
        if chance(0.35) and not words:
            u = pick(["{a} - {b} = ?", "{a}-{b}=", "What is {a} - {b}?", "{a} - {b} is what?",
                      "Solve {a} - {b}.", "what is {a}-{b}", "Can you do {a} - {b}?"]
                     ).format(a=a, b=b)
            ans = pick(["{a} - {b} = {d}.", "{d}.", "The answer is {d}.", "{a} - {b} is {d}.",
                        "It is {d}."]).format(a=a, b=b, d=d)
            return u, ans
        A, B, D = ns(a, words), ns(b, words), ns(d, words)
        u = pick(["What is {a} minus {b}?", "What's {a} minus {b}?", "Take {b} away from {a}.",
                  "What is {a} take away {b}?", "Subtract {b} from {a}.",
                  "What do you get if you take {b} away from {a}?", "Can you do {a} minus {b}?",
                  "what is {a} minus {b}", "How much is {a} minus {b}?"]).format(a=A, b=B)
        ans = pick(["{a} minus {b} is {d}.", "{a} take away {b} is {d}.", "The answer is {d}.",
                    "{d}.", "It is {d}.", "If you take {b} away from {a}, you get {d}."]
                   ).format(a=A, b=B, d=D)
        return u, cap(ans)
    if r < 0.66:
        return _word_problem(words)
    if r < 0.84:
        a, b = rng.sample(range(0, 21), 2)
        big, small = max(a, b), min(a, b)
        kind = pick(["which_big", "which_small", "is_big", "is_less", "is_more"])
        A, B = ns(a, words), ns(b, words)
        BIG, SMALL = ns(big, words), ns(small, words)
        if kind == "which_big":
            u = pick(["Which is bigger, {a} or {b}?", "Which number is bigger: {a} or {b}?",
                      "Which is more, {a} or {b}?", "{A} or {b}, which is bigger?",
                      "which is bigger {a} or {b}", "Is {a} or {b} bigger?",
                      "Which number is larger, {a} or {b}?"]).format(a=A, b=B, A=cap(A))
            word = "more" if "more" in u else ("larger" if "larger" in u else "bigger")
            ans = pick(["{x} is {w} than {y}.", "{x} is {w}.", "{x}."]).format(
                x=BIG, y=SMALL, w=word)
        elif kind == "which_small":
            u = pick(["Which is smaller, {a} or {b}?", "Which number is smaller: {a} or {b}?",
                      "Which is less, {a} or {b}?", "{A} or {b}, which is smaller?",
                      "which is smaller {a} or {b}", "Which number is less: {a} or {b}?"]
                     ).format(a=A, b=B, A=cap(A))
            word = "less" if "less" in u else "smaller"
            ans = pick(["{x} is {w} than {y}.", "{x} is {w}.", "{x}."]).format(
                x=SMALL, y=BIG, w=word)
        elif kind == "is_big":
            u = pick(["Is {a} bigger than {b}?", "Is {a} more than {b}?", "is {a} bigger than {b}"]
                     ).format(a=A, b=B)
            word = "more" if "more" in u else "bigger"
            if a > b:
                ans = pick(["Yes, {a} is {w} than {b}.", "Yes."]).format(a=A, b=B, w=word)
            else:
                ans = pick(["No, {a} is not {w} than {b}. {b} is {w} than {a}.",
                            "No. {b} is {w} than {a}."]).format(a=A, b=B, w=word)
                ans = re.sub(r"\. (\w)", lambda m: ". " + m.group(1).upper(), ans)
        elif kind == "is_less":
            u = pick(["Is {a} less than {b}?", "Is {a} smaller than {b}?", "is {a} less than {b}"]
                     ).format(a=A, b=B)
            word = "smaller" if "smaller" in u else "less"
            if a < b:
                ans = pick(["Yes, {a} is {w} than {b}.", "Yes."]).format(a=A, b=B, w=word)
            else:
                ans = pick(["No, {a} is not {w} than {b}. {b} is {w} than {a}.",
                            "No. {b} is {w} than {a}."]).format(a=A, b=B, w=word)
                ans = re.sub(r"\. (\w)", lambda m: ". " + m.group(1).upper(), ans)
        else:
            u = pick(["Is {a} more than {b}?", "Is {a} greater than {b}?"]).format(a=A, b=B)
            word = "greater" if "greater" in u else "more"
            if a > b:
                ans = "Yes, {a} is {w} than {b}.".format(a=A, b=B, w=word)
            else:
                ans = "No, {a} is not {w} than {b}. {B} is {w} than {a}.".format(
                    a=A, b=B, B=cap(B), w=word)
        return u, cap(ans)
    if r < 0.93:
        n = rng.randint(1, 20)
        N = ns(n, words)
        even = n % 2 == 0
        kind = pick(["eo", "is_even", "is_odd"])
        if kind == "eo":
            u = pick(["Is {n} even or odd?", "Is {n} an even number or an odd number?",
                      "{N}: even or odd?", "is {n} even or odd", "Tell me if {n} is even or odd."]
                     ).format(n=N, N=cap(N))
            ans = pick(["{n} is {eo}.", "{n} is an {eo} number.", "{EO}."]).format(
                n=N, eo="even" if even else "odd", EO="Even" if even else "Odd")
        elif kind == "is_even":
            u = pick(["Is {n} an even number?", "Is {n} even?"]).format(n=N)
            ans = ("Yes, {n} is even." if even else "No, {n} is odd.").format(n=N)
        else:
            u = pick(["Is {n} an odd number?", "Is {n} odd?"]).format(n=N)
            ans = ("Yes, {n} is odd." if not even else "No, {n} is even.").format(n=N)
        return u, cap(ans)
    n = rng.randint(1, 10)
    N, D = ns(n, words), ns(2 * n, words)
    u = pick(["What is double {n}?", "What is {n} doubled?", "Double {n}. What do you get?",
              "What is two times {n}?" if words else "What is 2 times {n}?",
              "what is double {n}"]).format(n=N)
    ans = pick(["Double {n} is {d}.", "{n} plus {n} is {d}.", "{d}.", "It is {d}."]).format(n=N, d=D)
    return u, cap(ans)


def _word_problem(words):
    kind = pick(["have_get", "two_kids", "group_add", "eat", "give", "group_sub"])
    if kind in ("have_get", "two_kids", "group_add"):
        a = rng.randint(1, 10)
        b = rng.randint(1, min(10, 20 - a))
        s = a + b
    else:
        a = rng.randint(2, 15)
        b = rng.randint(1, a)
        s = a - b
    W = lambda n: ns(n, words)
    if kind == "have_get":
        n = pick(PROB_NOUNS)
        p = plural(n)
        u = pick(["I have {A}. I get {b} more. How many {p} do I have now?",
                  "I have {A}. My friend gives me {B}. How many {p} do I have?",
                  "If I have {A} and I get {b} more, how many {p} do I have?"]).format(
            A=count_noun(a, n, p, words), b=W(b), B=count_noun(b, n, p, words), p=p)
        ans = pick(["You have {S} now.", "You have {S}.", "{a} plus {b} is {s}. You have {S}.",
                    "{S}."]).format(S=count_noun(s, n, p, words), a=W(a), b=W(b), s=W(s))
        return u, cap(ans)
    if kind == "two_kids":
        n = pick(PROB_NOUNS)
        p = plural(n)
        k1, k2 = rng.sample(NAMES, 2)
        u = pick(["{k1} has {A} and {k2} has {B}. How many {p} do they have in all?",
                  "{k1} has {A}. {k2} has {B}. How many {p} do they have together?"]).format(
            k1=k1, k2=k2, A=count_noun(a, n, p, words), B=count_noun(b, n, p, words), p=p)
        tail = "together" if "together" in u else "in all"
        ans = pick(["They have {S} {t}.", "{a} plus {b} is {s}. They have {S} {t}.", "{S}."]
                   ).format(S=count_noun(s, n, p, words), t=tail, a=W(a), b=W(b), s=W(s))
        return u, cap(ans)
    if kind == "eat":
        n = pick(EDIBLE)
        p = plural(n)
        u = pick(["I have {A}. I eat {b}. How many {p} are left?",
                  "I had {A}. I ate {b}. How many {p} are left?",
                  "There are {A} on the plate. I eat {b}. How many are left?"]).format(
            A=count_noun(a, n, p, words), b=W(b), p=p)
        if s == 0:
            ans = pick(["There are no {p} left.", "None are left. {a} minus {b} is {z}."]).format(
                p=p, a=cap(W(a)), b=W(b), z=W(0))
        elif s == 1:
            ans = pick(["There is {S} left.", "{S} is left.", "{a} minus {b} is {s}. There is {S} left."]
                       ).format(S=count_noun(s, n, p, words), a=W(a), b=W(b), s=W(s))
        else:
            ans = pick(["There are {S} left.", "{S} are left.",
                        "{a} minus {b} is {s}. There are {S} left."]
                       ).format(S=count_noun(s, n, p, words), a=W(a), b=W(b), s=W(s))
        return u, cap(ans)
    if kind == "give":
        n = pick(PROB_NOUNS)
        p = plural(n)
        u = pick(["I have {A}. I give {b} to my friend. How many {p} do I have now?",
                  "I have {A}. I give {b} away. How many {p} do I have left?"]).format(
            A=count_noun(a, n, p, words), b=W(b), p=p)
        tail = "left" if "left?" in u else "now"
        if s == 0:
            ans = "You have no {p} {t}.".format(p=p, t=tail)
        else:
            ans = pick(["You have {S} {t}.", "{a} minus {b} is {s}. You have {S} {t}.", "{S}."]
                       ).format(S=count_noun(s, n, p, words), t=tail, a=W(a), b=W(b), s=W(s))
        return u, cap(ans)
    g = pick(GROUPS)
    sing, plur, where = g[0], g[1], g[2]
    if kind == "group_add":
        verb = g[6] if b == 1 else g[5]
        more = (W(b) + " more " + (sing if b == 1 else plur) + " " + verb)
        u = "{T} {w}. Then {m}. How many {p} are there now?".format(
            T=_there(a, sing, plur, words), w=where, m=more, p=plur)
        if s == 1:
            ans = "There is {S} {w} now.".format(S=count_noun(s, sing, plur, words), w=where)
        else:
            ans = pick(["There are {S} {w} now.", "Now there are {S}.", "{a} plus {b} is {s}."]
                       ).format(S=count_noun(s, sing, plur, words), w=where, a=W(a), b=W(b), s=W(s))
        return u, cap(ans)
    verb = g[4] if b == 1 else g[3]
    u = "{T} {w}. {B} {v}. How many {p} are left?".format(
        T=_there(a, sing, plur, words), w=where, B=cap(W(b)), v=verb, p=plur)
    if s == 0:
        ans = pick(["No {p} are left.", "There are no {p} left."]).format(p=plur)
    elif s == 1:
        ans = pick(["{S} is left.", "There is {S} left."]).format(S=count_noun(s, sing, plur, words))
    else:
        ans = pick(["{S} are left.", "There are {S} left.", "{a} minus {b} is {s}. {S2} are left."]
                   ).format(S=count_noun(s, sing, plur, words), a=W(a), b=W(b), s=W(s),
                            S2=cap(count_noun(s, sing, plur, words)))
    return u, cap(ans)


# ================================================================= 4. opposites

OPP_Q = ["What is the opposite of {w}?", "What's the opposite of {w}?",
         "Tell me the opposite of {w}.", "Opposite of {w}?", "Can you tell me the opposite of {w}?",
         "What word means the opposite of {w}?", 'Give me the opposite of "{w}".',
         "Please say the opposite of {w}.", "Do you know the opposite of {w}?",
         "what is the opposite of {w}", "Say the opposite of {w}.",
         "I say {w}. What is the opposite?"]


def gen_opposites():
    w = pick(sorted(OPP))
    o = OPP[w]
    r = rng.random()
    if r < 0.75:
        u = pick(OPP_Q).format(w=w)
        a = pick(["The opposite of {w} is {o}.", "{O}.", "{O} is the opposite of {w}.",
                  "It is {o}.", "The opposite of {w} is {o}."]).format(w=w, o=o, O=cap(o))
        return u, a
    if r < 0.87:
        u = pick(["Is {o} the opposite of {w}?", "Are {w} and {o} opposites?"]).format(w=w, o=o)
        if u.startswith("Are"):
            a = pick(["Yes, {w} and {o} are opposites.", "Yes."]).format(w=w, o=o)
        else:
            a = pick(["Yes, {o} is the opposite of {w}.", "Yes."]).format(w=w, o=o)
        return u, a
    bad = pick([x for x in sorted(OPP_ALL) if x != w and x not in OPP_ALL[w]])
    u = pick(["Is {x} the opposite of {w}?", "Are {w} and {x} opposites?"]).format(w=w, x=bad)
    a = pick(["No. The opposite of {w} is {o}.", "No, {x} is not the opposite of {w}. The opposite of {w} is {o}."]
             ).format(w=w, o=o, x=bad)
    return u, a


# ========================================================== 5. animal world

def _cnp(np_, verb):
    return np_, verb


def gen_animals():
    r = rng.random()
    if r < 0.24:  # colors of things
        np_, verb, color = pick(COLOR_FACTS)
        it = "they" if verb == "are" else "it"
        u = pick(["What color {v} {np}?", "What colour {v} {np}?", "what color {v} {np}",
                  "Tell me the color of {np}.", "Do you know what color {np} {v}?",
                  "What is the color of {np}?", "Can you tell me what color {np} {v}?",
                  "{NP}. What color {v} {it}?", "Color of {np}?"]).format(
            v=verb, np=np_, NP=cap(np_), it=it)
        a = pick(["{NP} {v} {c}.", "{NP} {v} {c}.", "{C}.", "{IT} {v} {c}."]).format(
            NP=cap(np_), v=verb, c=color, C=cap(color), IT=cap(it))
        return u, a
    if r < 0.42:  # sounds
        s, p, snd = pick(SOUNDS)
        if chance(0.25):
            u = pick(["What do {p} say?", "What sound do {p} make?", "What noise do {p} make?"]
                     ).format(p=p)
            a = pick(["{P} say {snd}.", "{SND}!", "{P} say {snd}!"]).format(
                P=cap(p), snd=snd, SND=cap(snd))
            return u, a
        if chance(0.15):
            u = pick(["Make the sound of {a}.", "Can you make {a} sound?", "Pretend to be {a}.",
                      "Make {a} noise."]).format(a=an(s))
            a = cap(snd) + " " + snd + "!" if len(snd) < 8 else cap(snd) + "!"
            return u, a
        u = pick(["What sound does {a} make?", "What does {a} say?", "What noise does {a} make?",
                  "what does {a} say", "Which sound does {a} make?",
                  "Can you tell me what sound {a} makes?", "{A} says what?"]).format(
            a=an(s), A=cap(an(s)))
        a = pick(["{A} says {snd}.", "{A} says {snd}!", "{SND}!", "It says {snd}."]).format(
            A=cap(an(s)), snd=snd, SND=cap(snd))
        return u, a
    if r < 0.58:  # habitats
        s, p, ps, pp, extra = pick(HABITATS)
        if chance(0.35):
            u = pick(["Where do {p} live?", "where do {p} live", "Do you know where {p} live?",
                      "Tell me where {p} live."]).format(p=p)
            a = pick(["{P} live {pl}.", "{PL}."]).format(P=cap(p), pl=pp, PL=cap(pp))
            return u, a
        u = pick(["Where does {a} live?", "where does {a} live", "Where is the home of {a}?",
                  "Do you know where {a} lives?", "Tell me where {a} lives.",
                  "Where can you find {a}?"]).format(a=s)
        if u.startswith("Where can you find"):
            a = "You can find {a} {pl}.".format(a=s, pl=ps)
        else:
            a = pick(["{A} lives {pl}.", "{A} lives {pl}.", "{PL}."]).format(
                A=cap(s), pl=ps, PL=cap(ps))
        if extra and not a.startswith(("In ", "On ")) and chance(0.5):
            a += " " + extra
        return u, a
    if r < 0.73:  # diets
        s, p, food = pick(DIETS)
        if chance(0.35):
            u = pick(["What do {p} eat?", "what do {p} eat", "What food do {p} eat?",
                      "Tell me what {p} eat."]).format(p=p)
            a = pick(["{P} eat {f}.", "{F}."]).format(P=cap(p), f=food, F=cap(food))
            return u, a
        u = pick(["What does {a} eat?", "what does {a} eat", "What food does {a} eat?",
                  "Tell me what {a} eats.", "What does {a} like to eat?",
                  "Do you know what {a} eats?"]).format(a=s)
        a = pick(["{A} eats {f}.", "{A} eats {f}.", "{F}.", "It eats {f}."]).format(
            A=cap(s), f=food, F=cap(food))
        return u, a
    if r < 0.87:  # babies
        adult, baby, uniq = pick(BABIES)
        if uniq and chance(0.3):
            u = pick(["What is {b}?", "What animal does {b} grow up to be?",
                      "{B} is a baby what?", "What does {b} grow up to be?"]).format(
                b=an(baby), B=cap(an(baby)))
            if "grow up" in u:
                a = pick(["{B} grows up to be {a}.", "{A}."]).format(
                    B=cap(an(baby)), a=an(adult), A=cap(an(adult)))
            else:
                a = pick(["{B} is a baby {a}.", "It is a baby {a}."]).format(B=cap(an(baby)), a=adult)
            return u, a
        u = pick(["What is a baby {a} called?", "What do you call a baby {a}?",
                  "What is the name for a baby {a}?", "A baby {a} is called what?",
                  "what is a baby {a} called", "Tell me the name of a baby {a}."]).format(a=adult)
        a = pick(["A baby {a} is called {b}.", "{B}.", "It is called {b}.",
                  "We call a baby {a} {b}."]).format(a=adult, b=an(baby), B=cap(an(baby)))
        return u, a
    s, p, n = pick(LEGS)  # legs
    if chance(0.3):
        u = pick(["How many legs do {p} have?", "how many legs do {p} have"]).format(p=p)
        if n == 0:
            a = "{P} have no legs.".format(P=cap(p))
        else:
            a = pick(["{P} have {n} legs.", "{N} legs."]).format(P=cap(p), n=nw(n), N=cap(nw(n)))
        return u, a
    u = pick(["How many legs does {a} have?", "{A} has how many legs?",
              "Tell me how many legs {a} has.", "how many legs does {a} have",
              "Count the legs on {a}. How many are there?"]).format(a=s, A=cap(s))
    if n == 0:
        a = pick(["{A} has no legs.", "None! {A} has no legs."]).format(A=cap(s))
        if s == "a fish":
            a += " It swims with its fins."
    else:
        a = pick(["{A} has {n} legs.", "{N} legs.", "{N}."]).format(A=cap(s), n=nw(n), N=cap(nw(n)))
    return u, a


# ================================================================== 6. listing

LIST_Q = ["Name {n} {lab}.", "List {n} {lab}.", "Can you name {n} {lab}?", "Tell me {n} {lab}.",
          "Please list {n} {lab}.", "Give me {n} {lab}.", "What are {n} {lab}?",
          "Can you think of {n} {lab}?", "I need {n} {lab}, please.", "name {n} {lab}",
          "Say {n} {lab}.", "{N} {lab}, please.", "Please name {n} {lab}."]
LIST_Q1 = ["Name one {lab}.", "Name {alab}.", "Tell me one {lab}.", "Can you name {alab}?",
           "Give me {alab}.", "Can you think of {alab}?", "name {alab}", "Please name one {lab}.",
           "Say {alab}."]


def gen_listing():
    key = pick(sorted(CATEGORIES))
    sing, plur, items, ordered = CATEGORIES[key]
    if key == "numbers":
        n = rng.randint(1, 5)
        chosen = sorted(rng.sample(range(0, 21), n))
        chosen = [str(x) for x in chosen]
    elif key == "letters":
        n = rng.randint(1, 5)
        chosen = sorted(rng.sample(LETTERS, n))
    else:
        n = rng.randint(1, min(5, len(items)))
        chosen = rng.sample(items, n)
        if ordered:
            chosen.sort(key=items.index)
    if n == 1:
        u = pick(LIST_Q1).format(lab=sing, alab=an(sing))
        J = chosen[0]
        a = pick(["{J}.", "Here is one {lab}: {j}.", "Sure! {J}.", "How about {j}?"]).format(
            J=cap(J), j=J, lab=sing)
        return u, a
    nt = nw(n) if chance(0.75) else str(n)
    u = pick(LIST_Q).format(n=nt, N=cap(nt), lab=plur)
    j = join(chosen)
    a = pick(["{J}.", "{J}.", "Here are {n} {lab}: {j}.", "Sure! {J}.", "Okay! {J}.",
              "{J}. Those are {n} {lab}."]).format(J=cap(j), j=j, n=nw(n), lab=plur)
    return u, a


# ============================================================ 7. sentence with word

ANIMAL_SENT_WORDS = ["dog", "cat", "bird", "fish", "cow", "horse", "pig", "sheep", "duck",
                     "lion", "tiger", "elephant", "monkey", "bear", "rabbit", "frog", "mouse",
                     "giraffe", "zebra", "snake", "owl", "fox", "goat", "chicken", "whale",
                     "turtle", "kangaroo", "penguin", "deer", "squirrel", "puppy", "kitten",
                     "bee", "butterfly", "spider", "ant", "camel", "panda", "shark", "octopus"]
ANIMAL_SENT_T = ["I saw {a} today.", "The {n} is sleeping.", "I drew a picture of {a}.",
                 "We read a story about {a}.", "Look at that {n}!", "The {n} is looking at me.",
                 "There is {a} in my picture book.", "{A} is an animal."]
FOOD_C = ["apple", "banana", "orange", "pear", "peach", "plum", "cherry", "strawberry", "mango",
          "carrot", "potato", "cookie", "sandwich", "egg", "cupcake", "pancake", "muffin"]
FOOD_C_T = ["I ate {a} for lunch.", "Mom gave me {a}.", "There is {a} on my plate.",
            "This {n} is very good.", "Can I have {a}, please?", "I want {a} for my snack."]
FOOD_M = ["bread", "rice", "soup", "cheese", "pizza", "cake", "pasta", "ice cream", "cereal",
          "yogurt", "honey", "jam", "popcorn"]
FOOD_M_T = ["I like {n}.", "Can I have some {n}, please?", "This {n} is very good.",
            "We need more {n}."]
MEALS = ["rice", "soup", "pizza", "pasta"]
DRINKS = ["milk", "water", "juice", "lemonade", "tea", "hot chocolate"]
DRINK_T = ["Can I have some {n}, please?", "My cup is full of {n}.", "I spilled my {n}.",
           "The {n} is in the cup."]
OBJECTS = ["ball", "kite", "doll", "teddy bear", "book", "pencil", "crayon", "cup", "spoon",
           "hat", "sock", "shoe", "key", "box", "bag", "coat", "toy", "block", "puzzle", "comb",
           "blanket", "pillow", "umbrella", "backpack", "scarf", "balloon", "drum"]
OBJECT_T = ["I have {a}.", "Where is my {n}?", "I found {a} under the bed.",
            "My {n} is on the table.", "Can you give me the {n}, please?", "This {n} is mine.",
            "I got a new {n}."]
PLACES = ["park", "beach", "zoo", "farm", "shop", "library", "garden", "pool", "playground",
          "lake", "forest"]
PLACE_T = ["We went to the {n} today.", "I like to go to the {n}.", "My mom took me to the {n}.",
           "Let's go to the {n}!", "We had fun at the {n}."]
VEHICLES = [("car", "in"), ("bus", "on"), ("train", "on"), ("bike", "on"), ("boat", "on"),
            ("plane", "on"), ("truck", "in"), ("ship", "on"), ("taxi", "in"),
            ("helicopter", "in")]
VEHICLE_T = ["The {n} is going fast.", "I saw a big {n}.", "Look at that red {n}!",
             "We went to see Grandma by {n}.", "I like to ride {prep} {a}."]

HAND_SENT = {
    # adjectives
    "big": ["The elephant is very big.", "We live in a big house.", "I have a big red ball."],
    "small": ["The mouse is very small.", "I found a small shell on the beach.",
              "My kitten is small and soft."],
    "little": ["The little bird sat on the fence.", "I have a little sister.",
               "We ate a little cake."],
    "hot": ["The soup is too hot to eat.", "It is very hot in the summer.",
            "Do not touch the hot stove."],
    "cold": ["The ice cream is cold.", "It is cold outside, so wear your coat.", "I like cold milk."],
    "happy": ["The puppy is happy to see me.", "I feel happy when I play with my friends.",
              "We sang a happy song."],
    "sad": ["The boy was sad when his balloon flew away.", "I feel sad when it rains.",
            "The sad puppy wanted a hug."],
    "fast": ["The cheetah can run very fast.", "My dad has a fast car.", "The fast train went by."],
    "slow": ["The turtle is very slow.", "The snail is slow, but it never stops.",
             "We took a slow walk in the park."],
    "tall": ["The giraffe is very tall.", "My dad is tall.", "There is a tall tree in our garden."],
    "short": ["My pencil is short.", "The show was short.", "My little brother is short."],
    "soft": ["My pillow is soft.", "The kitten has soft fur.", "I have a soft blanket."],
    "hard": ["A rock is hard.", "This puzzle is hard.", "The floor is hard and cold."],
    "wet": ["My shoes got wet in the rain.", "The dog is wet after its bath.",
            "Do not sit on the wet grass."],
    "dry": ["Put on a dry shirt.", "The towel is dry now.", "The desert is very dry."],
    "loud": ["The drum is very loud.", "Thunder is loud.", "Please do not be so loud."],
    "quiet": ["The library is quiet.", "Please be quiet, the baby is sleeping.",
              "The mouse was very quiet."],
    "red": ["I have a red ball.", "The apple is red.", "Stop at the red light."],
    "blue": ["The sky is blue.", "My shirt is blue.", "I like to paint with blue paint."],
    "green": ["The grass is green.", "The frog is green.", "I want the green cup."],
    "yellow": ["A banana is yellow.", "She has a yellow hat.", "The school bus is yellow."],
    "pretty": ["The flowers are very pretty.", "What a pretty dress!", "The sunset is pretty."],
    "funny": ["The clown is funny.", "That was a funny joke.", "My dog makes funny faces."],
    "kind": ["My teacher is very kind.", "It is kind to share your toys.",
             "The kind girl helped me up."],
    "brave": ["The brave knight saved the town.", "You were brave at the doctor.",
              "It is brave to say sorry."],
    "sleepy": ["The baby is sleepy.", "I feel sleepy at night.", "The sleepy cat lay in the sun."],
    "hungry": ["I am hungry, so I want a snack.", "The hungry bird ate a worm.",
               "The puppy is hungry."],
    "tired": ["I am tired after playing all day.", "The tired dog lay down.",
              "Mom is tired after work."],
    "clean": ["My hands are clean now.", "I like a clean room.", "Put on a clean shirt."],
    "dirty": ["My shoes are dirty.", "The dog is dirty from the mud.",
              "Put the dirty plates in the sink."],
    "new": ["I have a new bike.", "We moved to a new house.", "My shoes are new."],
    "old": ["My grandpa is old.", "This is an old book.", "We have an old car."],
    "long": ["A snake has a long body.", "The giraffe has a long neck.", "It was a long day."],
    "round": ["A ball is round.", "The moon looks round tonight.", "We sat at a round table."],
    "sweet": ["Candy is very sweet.", "The strawberries are sweet.", "Honey is sweet and sticky."],
    "heavy": ["The big box is heavy.", "An elephant is very heavy.", "My bag is too heavy to lift."],
    "bright": ["The sun is very bright.", "She has a bright red coat.",
               "The room is bright in the morning."],
    "dark": ["It is dark at night.", "The cave is dark.", "The sky gets dark at night."],
    "good": ["This cake is very good.", "You did a good job!", "My dog is a good dog."],
    "nice": ["It is a nice day.", "My new friend is very nice.", "That was a nice thing to say."],
    "shiny": ["The new car is shiny.", "I found a shiny coin.", "Her shoes are red and shiny."],
    "full": ["My cup is full of milk.", "I am full after dinner.", "The box is full of toys."],
    "empty": ["The cookie jar is empty.", "My cup is empty.", "The park is empty at night."],
    "warm": ["My coat is warm.", "The sun feels warm.", "I like a warm bath."],
    "angry": ["The bear looked angry.", "I was angry when my tower fell down.",
              "Do not be angry, it was an accident."],
    "busy": ["Mom is busy cooking dinner.", "The bees are busy.", "The shop is busy today."],
    "yummy": ["This pizza is yummy.", "We had yummy cookies.", "The soup smells yummy."],
    "silly": ["My cat is silly.", "We made silly faces.", "That is a silly hat."],
    "fluffy": ["The cloud is white and fluffy.", "My puppy is fluffy.", "I have a fluffy pillow."],
    "gentle": ["Be gentle with the baby bird.", "The big dog is very gentle.",
               "Use gentle hands with the kitten."],
    "strong": ["My dad is very strong.", "An elephant is strong.", "The wind is strong today."],
    "smart": ["My dog is very smart.", "She is smart and kind.", "The smart fox found the food."],
    "tiny": ["An ant is tiny.", "I saw a tiny bug.", "The baby has tiny hands."],
    "sticky": ["Honey is sticky.", "My hands are sticky.", "The tape is sticky."],
    "scary": ["The thunder was scary.", "We read a scary story.", "The dark hall is scary."],
    # verbs
    "run": ["I like to run in the park.", "Dogs can run very fast.", "Let's run to the tree!"],
    "jump": ["The frog can jump high.", "I can jump over the puddle.", "Let's jump in the leaves!"],
    "swim": ["Fish swim in the water.", "I can swim in the pool.", "Ducks like to swim."],
    "play": ["I play with my friends after school.", "Let's play a game.",
             "The kids play in the park."],
    "eat": ["We eat dinner at six.", "I eat an apple every day.", "Cows eat grass."],
    "sleep": ["I sleep in my bed.", "Cats sleep a lot.", "It is time to sleep."],
    "read": ["I read a book every night.", "Mom likes to read to me.", "Can you read this word?"],
    "sing": ["Birds sing in the morning.", "Let's sing a song.", "I like to sing."],
    "dance": ["We dance to the music.", "I like to dance with my sister.", "Can you dance?"],
    "walk": ["We walk to school.", "I walk my dog every day.", "Let's walk to the park."],
    "climb": ["Monkeys climb trees.", "I can climb the ladder.", "Cats like to climb."],
    "draw": ["I like to draw pictures.", "Can you draw a cat?", "We draw with crayons."],
    "help": ["I help my mom cook.", "Can you help me?", "Friends help each other."],
    "look": ["Look at the big rainbow!", "I look out the window.", "Let's look for my ball."],
    "see": ["I can see the moon.", "Did you see the bird?", "I see a red car."],
    "go": ["Let's go to the park.", "We go to school in the morning.", "It is time to go home."],
    "make": ["We make a cake.", "I can make a paper plane.", "Let's make a snowman."],
    "find": ["I can't find my shoe.", "Can you find the cat?", "We find shells on the beach."],
    "fly": ["Birds fly in the sky.", "I want to fly a kite.", "Planes fly very high."],
    "cook": ["Dad likes to cook dinner.", "We cook soup in a big pot.", "Can you cook eggs?"],
    "wash": ["I wash my hands before I eat.", "We wash the car.", "Wash your face, please."],
    "throw": ["Throw me the ball!", "I can throw far.", "Do not throw rocks."],
    "catch": ["I can catch the ball.", "The cat likes to catch mice.", "Can you catch it?"],
    "kick": ["I kick the ball.", "Kick the ball to me!", "Do not kick the door."],
    "hug": ["I hug my mom.", "Let's hug.", "I hug my teddy bear at night."],
    "laugh": ["Funny jokes make me laugh.", "We laugh a lot.", "The baby likes to laugh."],
    "cry": ["The baby began to cry.", "It is okay to cry.", "Sad stories make me cry."],
    "write": ["I can write my name.", "Let's write a letter to Grandma.", "We write with pencils."],
    "listen": ["Listen to the birds.", "I listen to music.", "Please listen to your teacher."],
    "open": ["Please open the door.", "I open my present.", "Can you open this jar?"],
    "close": ["Please close the window.", "Close your eyes.", "I close the book."],
    "sit": ["Please sit down.", "I sit next to my friend.", "The cat likes to sit in the sun."],
    "share": ["I share my toys.", "Let's share the cake.", "It is nice to share."],
    "build": ["We build a sand castle.", "I like to build with blocks.", "Birds build nests."],
    "ride": ["I ride my bike to the park.", "Can I ride the horse?", "We ride the bus to school."],
    "paint": ["I paint a picture of my dog.", "Let's paint the fence.", "We paint with our fingers."],
    "smile": ["Smile for the picture!", "My baby brother likes to smile.", "I smile when I am happy."],
    "clap": ["Clap your hands!", "We clap at the end of the show.", "Let's clap to the music."],
    "count": ["I can count to ten.", "Let's count the stars.", "Can you count the apples?"],
    "push": ["Push the door to open it.", "I push my sister on the swing.", "Do not push in line."],
    "pull": ["Pull the rope!", "The horse can pull the cart.", "I pull my wagon."],
    "drink": ["I drink milk every morning.", "Cats drink water.", "Drink your juice, please."],
    "give": ["I give my dog a treat.", "Can you give me the red crayon?", "Let's give Mom a card."],
    "bake": ["We bake cookies.", "Grandma likes to bake bread.", "Let's bake a cake."],
    "carry": ["I carry my bag to school.", "Can you carry this box?", "Ants can carry big things."],
    "splash": ["Ducks splash in the pond.", "I like to splash in puddles.",
               "Do not splash water on me!"],
    "hide": ["Let's hide behind the tree.", "My cat likes to hide under the bed.",
             "Where did you hide the ball?"],
    "grow": ["Plants need water to grow.", "I want to grow tall.", "We grow carrots in our garden."],
    "dig": ["Dogs like to dig holes.", "We dig in the sand.", "Let's dig in the garden."],
    "wave": ["Wave goodbye to Grandma.", "I wave to my friend.", "I wave at the bus."],
    "learn": ["I learn new words at school.", "We learn to read.", "I want to learn to swim."],
    "brush": ["I brush my teeth.", "Brush your hair, please.", "She likes to brush the horse."],
    # nature and other nouns
    "sun": ["The sun is shining today.", "The sun is very hot.", "The sun comes up in the morning."],
    "moon": ["The moon is bright tonight.", "I can see the moon from my window.",
             "The moon comes out at night."],
    "star": ["I see a star in the sky.", "The star is twinkling.", "I made a wish on a star."],
    "rain": ["The rain makes the grass green.", "We stayed inside because of the rain.",
             "I like to play in the rain."],
    "snow": ["We made a snowman out of snow.", "The snow is cold and white.", "Snow fell all night."],
    "cloud": ["A big cloud covered the sun.", "That cloud looks like a bunny.",
              "The cloud is white and fluffy."],
    "rainbow": ["I saw a rainbow after the rain.", "A rainbow has many colors.",
                "Look at the rainbow in the sky!"],
    "tree": ["The bird is in the tree.", "We sat under a big tree.", "This tree has red apples."],
    "flower": ["I picked a flower for my mom.", "The flower smells nice.", "A bee sat on the flower."],
    "river": ["We saw fish in the river.", "The river is long and wide.", "Ducks swim on the river."],
    "rock": ["I sat on a big rock.", "The rock is hard.", "I found a smooth rock."],
    "leaf": ["A leaf fell from the tree.", "The leaf is green.", "This leaf is red and yellow."],
    "sky": ["The sky is blue today.", "Birds fly in the sky.", "The sky is full of stars."],
    "grass": ["The grass is green.", "We sat on the grass.", "Cows eat grass."],
    "wind": ["The wind is blowing hard.", "The wind took my hat.", "I like the cool wind."],
    "sea": ["We swam in the sea.", "Fish live in the sea.", "The sea is big and blue."],
    "mountain": ["We climbed a mountain.", "There is snow on the mountain.",
                 "The mountain is very tall."],
    "sand": ["We played in the sand.", "The sand is hot.", "I built a castle with sand."],
    "school": ["I go to school every day.", "I like my school.", "We learn to read at school."],
    "home": ["It is time to go home.", "I like to stay at home.", "My home is warm and cozy."],
    "friend": ["My friend and I play every day.", "Sam is my best friend.", "A good friend shares."],
    "mom": ["My mom reads me a story.", "I love my mom.", "My mom made pancakes."],
    "dad": ["My dad is tall.", "My dad and I went to the park.", "I helped my dad wash the car."],
    "baby": ["The baby is sleeping.", "My baby sister is small.", "The baby likes to laugh."],
    "family": ["I love my family.", "My family went to the beach.", "We had dinner with my family."],
    "teacher": ["My teacher is kind.", "The teacher reads us a story.", "I gave my teacher a flower."],
    "house": ["We live in a blue house.", "The house has a red door.", "My house is near the park."],
    "bed": ["I sleep in my bed.", "Make your bed in the morning.", "My cat sleeps on my bed."],
    "door": ["Please close the door.", "Someone is at the door.", "The door is open."],
    "window": ["I look out the window.", "Open the window, please.", "Rain is hitting the window."],
    "birthday": ["Today is my birthday!", "I had a cake on my birthday.", "My birthday is in May."],
    "music": ["I like to dance to music.", "We listen to music in the car.", "The music is loud."],
    "game": ["Let's play a game.", "This game is fun.", "We won the game!"],
}


def _build_sentences():
    out = collections.defaultdict(list)
    for w in ANIMAL_SENT_WORDS:
        for t in ANIMAL_SENT_T:
            out[w].append(t.format(a=an(w), A=cap(an(w)), n=w))
    for s, p, snd in SOUNDS:
        if s in ANIMAL_SENT_WORDS:
            out[s].append("The {n} says {snd}.".format(n=s, snd=snd))
    for s, p, food in DIETS:
        if bare(s) in ANIMAL_SENT_WORDS:
            out[bare(s)].append("{A} eats {f}.".format(A=cap(s), f=food))
    for s, p, ps, pp, extra in HABITATS:
        if bare(s) in ANIMAL_SENT_WORDS:
            out[bare(s)].append("{A} lives {pl}.".format(A=cap(s), pl=ps))
    for w in FOOD_C:
        for t in FOOD_C_T:
            out[w].append(t.format(a=an(w), n=w))
    for w in FOOD_M:
        for t in FOOD_M_T:
            out[w].append(t.format(n=w))
        if w in MEALS:
            out[w].append("We had {n} for dinner.".format(n=w))
    out["cereal"].append("I eat cereal for breakfast.")
    for w in DRINKS:
        for t in DRINK_T:
            out[w].append(t.format(n=w))
    for w in OBJECTS:
        for t in OBJECT_T:
            out[w].append(t.format(a=an(w), n=w))
    for w in PLACES:
        for t in PLACE_T:
            out[w].append(t.format(n=w))
    for w, prep in VEHICLES:
        for t in VEHICLE_T:
            out[w].append(t.format(n=w, a=an(w), prep=prep))
    for w, sents in HAND_SENT.items():
        out[w].extend(sents)
    final = {}
    for w, sents in out.items():
        pat = re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)
        good = sorted(set(s for s in sents if pat.search(s)))
        if good:
            final[w] = good
    return final


SENT_Q = ["Write a sentence with the word {w}.", "Use the word {w} in a sentence.",
          "Make a sentence with {w}.", 'Can you make a sentence using the word "{w}"?',
          "Give me a sentence with the word {w} in it.", 'Please use "{w}" in a sentence.',
          "Say a sentence with the word {w}.", "Put the word {w} in a sentence.",
          "sentence with {w} please", "Can you use {w} in a short sentence?",
          "Write a short sentence that has the word {w}.",
          "Make up a sentence with the word {w}.", "use {w} in a sentence"]


def gen_sentence():
    w = pick(SENT_WORDS)
    s = pick(SENTENCES[w])
    u = pick(SENT_Q).format(w=w)
    a = pick(["{s}", "{s}", "{s}", "Here is a sentence: {s}", "Sure! {s}", "Okay. {s}",
              "Here you go: {s}", "How about this: {s}"]).format(s=s)
    return u, a


# ================================================================== 8. yes/no

PROPS = [
    ("fire", "hot"), ("ice", "cold"), ("snow", "cold"), ("the sun", "hot"),
    ("the sun", "bright"), ("ice cream", "cold"), ("an elephant", "big"), ("a whale", "big"),
    ("a mouse", "small"), ("an ant", "small"), ("a giraffe", "tall"), ("a cheetah", "fast"),
    ("a turtle", "slow"), ("a snail", "slow"), ("a rabbit", "fast"), ("a pillow", "soft"),
    ("a rock", "hard"), ("a feather", "light"), ("a kitten", "soft"), ("a teddy bear", "soft"),
    ("sugar", "sweet"), ("honey", "sweet"), ("candy", "sweet"), ("a lemon", "sour"),
    ("water", "wet"), ("rain", "wet"), ("the desert", "dry"), ("thunder", "loud"),
    ("a whisper", "quiet"), ("the night", "dark"), ("a cave", "dark"), ("a plane", "fast"),
    ("an elephant", "heavy"), ("a truck", "big"), ("a baby", "small"), ("a mountain", "tall"),
    ("a mountain", "big"), ("a car", "heavy"), ("a race car", "fast"), ("a bug", "small"),
]
PROP_OPP = {"hot": "cold", "cold": "hot", "big": "small", "small": "big", "tall": "short",
            "fast": "slow", "slow": "fast", "soft": "hard", "hard": "soft", "sweet": "sour",
            "sour": "sweet", "wet": "dry", "dry": "wet", "heavy": "light", "light": "heavy",
            "loud": "quiet", "quiet": "loud", "bright": "dark", "dark": "bright"}

ABILITIES = [
    ("a fish", "fly", False, "A fish can swim."), ("a fish", "swim", True, ""),
    ("a fish", "walk", False, "A fish swims in the water."), ("a bird", "fly", True, ""),
    ("a penguin", "fly", False, "A penguin can swim very well."), ("a penguin", "swim", True, ""),
    ("a dog", "bark", True, ""), ("a dog", "fly", False, "A dog can run and jump."),
    ("a dog", "talk", False, "A dog can bark."), ("a cat", "climb a tree", True, ""),
    ("a cat", "fly", False, "A cat can run, jump, and climb."),
    ("a cow", "fly", False, "A cow walks on the ground."), ("a horse", "run fast", True, ""),
    ("a frog", "jump", True, ""), ("a frog", "fly", False, "A frog can jump and swim."),
    ("a snake", "walk", False, "A snake has no legs. It slides on the ground."),
    ("a turtle", "run fast", False, "A turtle is very slow."), ("a turtle", "swim", True, ""),
    ("a rock", "talk", False, "A rock is not alive."),
    ("a car", "fly", False, "A car drives on the road."), ("a plane", "fly", True, ""),
    ("a boat", "float", True, ""), ("a duck", "swim", True, ""), ("a duck", "fly", True, ""),
    ("a baby", "drive a car", False, "Only grown-ups can drive a car."),
    ("people", "fly", False, "People can walk, run, and jump."),
    ("a tree", "walk", False, "A tree stays in one place."), ("a monkey", "climb a tree", True, ""),
    ("a kangaroo", "jump", True, ""), ("a bee", "fly", True, ""),
    ("a spider", "make a web", True, ""), ("a chicken", "lay eggs", True, ""),
    ("a whale", "swim", True, ""), ("a whale", "walk", False, "A whale lives in the sea and swims."),
    ("an elephant", "fly", False, "An elephant walks on the ground."),
    ("a pig", "fly", False, "A pig walks on the ground."), ("a rabbit", "hop", True, ""),
    ("a horse", "fly", False, "A horse can run very fast."), ("a butterfly", "fly", True, ""),
    ("a lion", "roar", True, ""), ("a mouse", "roar", False, "A mouse can squeak."),
    ("a cat", "bark", False, "A cat says meow."), ("a fish", "breathe under water", True, ""),
    ("a baby", "read a book", False, "A baby is too little to read."),
    ("a bird", "sing", True, ""), ("an owl", "see at night", True, ""),
    ("a snail", "run", False, "A snail moves very slowly."), ("a clock", "show the time", True, ""),
    ("a ball", "bounce", True, ""), ("a kite", "fly", True, "It needs wind to fly."),
    ("a chair", "walk", False, "A chair is not alive."),
    ("ice", "melt", True, "Ice melts when it gets warm."), ("a giraffe", "reach high leaves", True, ""),
    ("a cow", "make milk", True, ""), ("a dog", "swim", True, "Many dogs like to swim."),
    ("a pencil", "write", True, ""), ("a book", "talk", False, "But you can read a book."),
]

MISC_YN = [
    (["Is the moon made of cheese?"], "No, the moon is not made of cheese. The moon is made of rock."),
    (["Do fish live in water?"], "Yes, fish live in water."),
    (["Is the Earth round?", "Is the world round?"], "Yes, the Earth is round like a ball."),
    (["Do plants need water?"], "Yes, plants need water to grow."),
    (["Do cows give milk?"], "Yes, cows give us milk."),
    (["Do chickens lay eggs?"], "Yes, chickens lay eggs."),
    (["Can you eat a rock?", "Can I eat a rock?"], "No, you cannot eat a rock. Rocks are not food."),
    (["Does the sun shine at night?"],
     "No. The sun shines in the day. At night we see the moon and the stars."),
    (["Do birds have feathers?"], "Yes, birds have feathers."),
    (["Do fish have legs?"], "No, fish do not have legs. Fish have fins."),
    (["Do snakes have legs?"], "No, snakes do not have legs."),
    (["Do people need sleep?", "Do we need sleep?"], "Yes, people need sleep to stay healthy."),
    (["Does a spider have eight legs?"], "Yes, a spider has eight legs."),
    (["Do trees grow?"], "Yes, trees grow. Some trees grow very tall."),
    (["Is it safe to touch fire?", "Can I touch fire?"],
     "No, it is not safe to touch fire. Fire can burn you."),
    (["Should I look both ways before I cross the street?"],
     "Yes, always look both ways before you cross the street."),
    (["Do bees make honey?"], "Yes, bees make honey."),
    (["Does rain come from clouds?"], "Yes, rain falls from clouds."),
    (["Are there seven days in a week?"], "Yes, there are seven days in a week."),
    (["Are there twelve months in a year?", "Are there 12 months in a year?"],
     "Yes, there are twelve months in a year."),
    (["Is a whale a fish?"], "No, a whale is not a fish. It lives in the sea, but it breathes air like we do."),
    (["Do we need to brush our teeth?"], "Yes, brushing your teeth keeps them clean and strong."),
    (["Should I wash my hands before I eat?"], "Yes, wash your hands with soap before you eat."),
    (["Is a baby older than a grandma?"], "No, a baby is younger than a grandma."),
    (["Do dogs like to play?"], "Yes, most dogs love to play."),
    (["Does a cat have whiskers?"], "Yes, a cat has whiskers on its face."),
    (["Is the sea salty?"], "Yes, sea water is salty."),
    (["Should I wear a coat when it is cold?"], "Yes, a coat keeps you warm when it is cold."),
    (["Do flowers need sun?"], "Yes, flowers need sun and water to grow."),
    (["Is a square round?"], "No, a square is not round. A square has four straight sides."),
    (["Does a triangle have three sides?"], "Yes, a triangle has three sides."),
    (["Is a circle round?"], "Yes, a circle is round."),
    (["Is chocolate a vegetable?"], "No, chocolate is not a vegetable. It is a sweet treat."),
    (["Do cars need wheels?"], "Yes, cars need wheels to move."),
    (["Does a duck have feathers?"], "Yes, a duck has feathers."),
    (["Do penguins live where it is cold?"], "Yes, many penguins live in cold places."),
    (["Is a bee an insect?"], "Yes, a bee is an insect."),
    (["Is a spider an insect?"],
     "No, a spider is not an insect. An insect has six legs, but a spider has eight."),
    (["Is a week longer than a day?"], "Yes, a week is longer than a day."),
    (["Do we sleep at night?"], "Yes, most people sleep at night."),
    (["Do cows eat grass?"], "Yes, cows eat grass."),
]


def _fix_caps(s):
    return re.sub(r"([.!?] )([a-z])", lambda m: m.group(1) + m.group(2).upper(), cap(s))


def yesno_fact():
    """Return (question, yes: bool, full answer, short-no-answer)."""
    r = rng.random()
    if r < 0.22:
        s, adj = pick(PROPS)
        if chance(0.5):
            return "Is {s} {a}?".format(s=s, a=adj), True, "Yes, {s} is {a}.".format(s=s, a=adj)
        opp = PROP_OPP[adj]
        return ("Is {s} {o}?".format(s=s, o=opp), False,
                _fix_caps("No, {s} is not {o}. {s} is {a}.".format(s=s, o=opp, a=adj)))
    if r < 0.38:
        np_, verb, color = pick([c for c in COLOR_FACTS if " " not in c[2] and c[2] != "dark"])
        if chance(0.45):
            return ("{V} {np} {c}?".format(V=cap(verb), np=np_, c=color), True,
                    "Yes, {np} {v} {c}.".format(np=np_, v=verb, c=color))
        other = pick([c for c in COLORS if c != color])
        return ("{V} {np} {o}?".format(V=cap(verb), np=np_, o=other), False,
                _fix_caps("No, {np} {v} not {o}. {np} {v} {c}.".format(
                    np=np_, v=verb, o=other, c=color)))
    if r < 0.6:
        s, v, yes, extra = pick(ABILITIES)
        if yes:
            full = "Yes, {s} can {v}.".format(s=s, v=v)
        else:
            full = "No, {s} cannot {v}.".format(s=s, v=v)
        if extra and (not yes or chance(0.5)):
            full += " " + extra
        return "Can {s} {v}?".format(s=s, v=v), yes, full
    if r < 0.72:
        s, p, snd = pick(SOUNDS)
        plural_form = chance(0.3)
        subj = p if plural_form else an(s)
        if chance(0.5):
            q = ("Do {s} say {x}?" if plural_form else "Does {s} say {x}?").format(s=subj, x=snd)
            full = ("Yes, {s} say {x}." if plural_form else "Yes, {s} says {x}.").format(s=subj, x=snd)
            return q, True, full
        other = pick([x[2] for x in SOUNDS if x[2] != snd])
        q = ("Do {s} say {x}?" if plural_form else "Does {s} say {x}?").format(s=subj, x=other)
        if plural_form:
            full = "No, {s} do not say {o}. {S} say {x}.".format(s=subj, S=cap(subj), o=other, x=snd)
        else:
            full = "No, {s} does not say {o}. {S} says {x}.".format(s=subj, S=cap(subj), o=other, x=snd)
        return q, False, full
    if r < 0.84:
        groups = sorted(MEMBER_GROUPS)
        g = pick(groups)
        item = pick(MEMBER_GROUPS[g])
        if chance(0.5):
            return ("Is {i} {g}?".format(i=item, g=g), True,
                    "Yes, {i} is {g}.".format(i=item, g=g))
        g2 = pick([x for x in groups if x != g])
        return ("Is {i} {g2}?".format(i=item, g2=g2), False,
                _fix_caps("No, {i} is not {g2}. {i} is {g}.".format(i=item, g2=g2, g=g)))
    if r < 0.9:
        s, p, ps, pp, extra = pick(HABITATS)
        if chance(0.5):
            return ("Does {s} live {pl}?".format(s=s, pl=ps), True,
                    "Yes, {s} lives {pl}.".format(s=s, pl=ps))
        other = pick([h for h in HABITATS if h[2] != ps and h[2] not in ps and ps not in h[2]
                      and not (("farm" in h[2]) and ("farm" in ps))
                      and not ("tree" in h[2] and "tree" in ps)
                      and not ("sea" in h[2] and ("sea" in ps or "ocean" in ps or "water" in ps))
                      and not ("ocean" in h[2] and ("sea" in ps or "water" in ps))
                      and not ("water" in h[2] and ("sea" in ps or "ocean" in ps or "pond" in ps))
                      and not ("pond" in h[2] and "water" in ps)
                      and not ("forest" in h[2] and ("forest" in ps or "woods" in ps or "tree" in ps))
                      and not ("woods" in h[2] and "forest" in ps)
                      and not ("cold" in h[2] and "cold" in ps)])
        return ("Does {s} live {o}?".format(s=s, o=other[2]), False,
                _fix_caps("No, {s} does not live {o}. {s} lives {pl}.".format(
                    s=s, o=other[2], pl=ps)))
    qs, ans = pick(MISC_YN)
    return pick(qs), ans.startswith("Yes"), ans


def gen_yesno():
    q, yes, full = yesno_fact()
    u = q
    v = rng.random()
    if v < 0.1:
        u = q[0].lower() + q[1:-1]
    elif v < 0.2:
        u = pick(["Tell me: ", "Quick question: ", "I want to know: ", "Hey, "]) + q[0].lower() + q[1:]
    elif v < 0.27:
        u = pick(["Is it true? ", "True or not? "]) + q
    if q.startswith(("Is ", "Are ", "Can ", "Does ", "Do ")) and chance(0.12) and not v < 0.27:
        a = "Yes." if yes else "No."
        return u, a
    return u, full


# ================================================================ 9. comparisons

COMPARE_SETS = [
    ("bigger", "smaller", ["an ant", "a mouse", "a cat", "a horse", "an elephant", "a whale"], True),
    ("bigger", "smaller", ["a pea", "a grape", "an apple", "a watermelon", "a car", "a house",
                           "a mountain"], True),
    ("bigger", "smaller", ["the moon", "the Earth", "the sun"], False),
    ("faster", "slower", ["a snail", "a turtle", "a rabbit", "a cheetah"], True),
    ("faster", "slower", ["a bike", "a car", "a plane", "a rocket"], True),
    ("faster", "slower", ["walking", "running", "riding a bike", "driving a car"], False),
    ("heavier", "lighter", ["a feather", "an apple", "a cat", "a cow", "an elephant", "a whale"], True),
    ("heavier", "lighter", ["a feather", "a pencil", "a book", "a chair", "a car", "a truck"], True),
    ("taller", "shorter", ["a mouse", "a cat", "a horse", "a giraffe"], True),
    ("taller", "shorter", ["a cup", "a chair", "a door", "a house", "a mountain"], True),
    ("taller", "shorter", ["a baby", "a child", "a grown-up"], True),
    ("longer", "shorter", ["a minute", "an hour", "a day", "a week", "a month", "a year"], False),
    ("hotter", "colder", ["ice", "warm milk", "hot soup", "fire"], False),
    ("older", "younger", ["a baby", "a child", "a teenager"], False),
]
SUPER = {"bigger": "biggest", "smaller": "smallest", "faster": "fastest", "slower": "slowest",
         "heavier": "heaviest", "lighter": "lightest", "taller": "tallest", "shorter": "shortest",
         "longer": "longest", "hotter": "hottest", "colder": "coldest", "older": "oldest",
         "younger": "youngest"}


def gen_compare():
    up, down, items, allow_the = pick(COMPARE_SETS)
    i, j = sorted(rng.sample(range(len(items)), 2))
    lo, hi = items[i], items[j]
    r = rng.random()
    if r < 0.12 and len(items) >= 3:
        idx = sorted(rng.sample(range(len(items)), 3))
        three = [items[k] for k in idx]
        word = pick([up, down])
        best = three[-1] if word == up else three[0]
        shown = list(three)
        rng.shuffle(shown)
        u = pick(["Which is the {s}: {l}?", "What is the {s}, {l}?", "Which one is the {s}: {l}?"]
                 ).format(s=SUPER[word], l=join(shown, "or"))
        a = pick(["{B} is the {s}.", "{B}."]).format(B=cap(best), s=SUPER[word])
        return u, a
    word = up if chance(0.6) else down
    win, lose = (hi, lo) if word == up else (lo, hi)
    x, y = (lo, hi) if chance(0.5) else (hi, lo)
    if r < 0.75:
        u = pick(["Which is {c}, {x} or {y}?", "What is {c}: {x} or {y}?",
                  "Which one is {c}, {x} or {y}?", "{X} or {y}, which is {c}?",
                  "Tell me which is {c}: {x} or {y}.", "which is {c} {x} or {y}",
                  "Which is {c}: {x} or {y}?", "Who is {c}, {x} or {y}?"
                  if "a baby" in items else "Which do you think is {c}, {x} or {y}?"]
                 ).format(c=word, x=x, y=y, X=cap(x))
        opts = ["{W} is {c} than {L}.", "{W} is {c} than {L}.", "{W} is {c}.", "{W}."]
        if allow_the and has_article(win):
            opts.append("The {wb} is {c}.")
        a = pick(opts).format(W=cap(win), L=lose, c=word, wb=bare(win))
        return u, a
    u = pick(["Is {x} {c} than {y}?", "is {x} {c} than {y}", "Do you think {x} is {c} than {y}?"]
             ).format(c=word, x=x, y=y)
    if x == win:
        a = pick(["Yes, {x} is {c} than {y}.", "Yes."]).format(x=x, y=y, c=word)
    else:
        a = pick(["No, {x} is not {c} than {y}. {Y} is {c} than {x}.",
                  "No. {Y} is {c} than {x}."]).format(x=x, y=y, Y=cap(y), c=word)
    return u, a


# ================================================================== 10. sequences

def _cyc(lst, i):
    return lst[i % len(lst)]


def gen_sequence():
    r = rng.random()
    if r < 0.2:
        i = rng.randrange(7)
        d = DAYS[i]
        if chance(0.55):
            n = _cyc(DAYS, i + 1)
            u = pick(["What day comes after {d}?", "What day is after {d}?",
                      "Which day comes after {d}?", "what comes after {d}",
                      "What is the day after {d}?", "Tell me the day after {d}."]).format(d=d)
            a = pick(["{n} comes after {d}.", "After {d} comes {n}.", "The day after {d} is {n}.",
                      "{n}.", "It is {n}."]).format(n=n, d=d)
        else:
            n = _cyc(DAYS, i - 1)
            u = pick(["What day comes before {d}?", "What day is before {d}?",
                      "Which day comes before {d}?", "What is the day before {d}?",
                      "what day is before {d}"]).format(d=d)
            a = pick(["{n} comes before {d}.", "The day before {d} is {n}.", "{n}.",
                      "It is {n}."]).format(n=n, d=d)
        return u, a
    if r < 0.3:
        i = rng.randrange(7)
        d = DAYS[i]
        if chance(0.5):
            n = _cyc(DAYS, i + 1)
            u = pick(["If today is {d}, what day is tomorrow?", "Today is {d}. What day will it be tomorrow?",
                      "It is {d} today. What day is it tomorrow?"]).format(d=d)
            a = pick(["Tomorrow is {n}.", "If today is {d}, tomorrow is {n}.", "{n}."]).format(n=n, d=d)
            if "will it be" in u:
                a = pick(["Tomorrow will be {n}.", "{n}."]).format(n=n)
        else:
            n = _cyc(DAYS, i - 1)
            u = pick(["If today is {d}, what day was yesterday?", "Today is {d}. What day was yesterday?",
                      "It is {d} today. What was yesterday?"]).format(d=d)
            a = pick(["Yesterday was {n}.", "If today is {d}, yesterday was {n}.", "{n}."]).format(n=n, d=d)
        return u, a
    if r < 0.47:
        i = rng.randrange(12)
        m = MONTHS[i]
        if chance(0.6):
            n = _cyc(MONTHS, i + 1)
            u = pick(["What month comes after {m}?", "Which month is after {m}?",
                      "What is the month after {m}?", "what month comes after {m}",
                      "Tell me the month after {m}."]).format(m=m)
            a = pick(["{n} comes after {m}.", "After {m} comes {n}.", "The month after {m} is {n}.",
                      "{n}."]).format(n=n, m=m)
        else:
            n = _cyc(MONTHS, i - 1)
            u = pick(["What month comes before {m}?", "Which month is before {m}?",
                      "What is the month before {m}?"]).format(m=m)
            a = pick(["{n} comes before {m}.", "The month before {m} is {n}.", "{n}."]).format(n=n, m=m)
        return u, a
    if r < 0.67:
        k = rng.random()
        if k < 0.45:
            i = rng.randrange(25)
            L, N = LETTERS[i], LETTERS[i + 1]
            u = pick(["What letter comes after {l}?", "What is the next letter after {l}?",
                      "Which letter is after {l}?", "what letter comes after {l}",
                      "What comes after {l} in the alphabet?", "Tell me the letter after {l}."]
                     ).format(l=L)
            a = pick(["The letter {n} comes after {l}.", "{n} comes after {l}.", "After {l} comes {n}.",
                      "{n}."]).format(n=N, l=L)
        elif k < 0.75:
            i = rng.randrange(1, 26)
            L, N = LETTERS[i], LETTERS[i - 1]
            u = pick(["What letter comes before {l}?", "Which letter is before {l}?",
                      "What comes before {l} in the alphabet?", "what letter is before {l}"]).format(l=L)
            a = pick(["The letter {n} comes before {l}.", "{n} comes before {l}.", "{n}."]).format(n=N, l=L)
        elif k < 0.87:
            i = rng.randrange(24)
            A, B, C = LETTERS[i], LETTERS[i + 1], LETTERS[i + 2]
            u = pick(["What letter is between {a} and {c}?", "Which letter comes between {a} and {c}?"]
                     ).format(a=A, c=C)
            a = pick(["{b} is between {a} and {c}.", "The letter {b}.", "{b}."]).format(a=A, b=B, c=C)
        else:
            i = rng.randrange(20)
            j = rng.randint(i + 2, min(25, i + 7))
            u = pick(["Say the letters from {a} to {b}.", "Can you say the letters from {a} to {b}?",
                      "List the letters from {a} to {b}.", "say the letters {a} to {b}"]
                     ).format(a=LETTERS[i], b=LETTERS[j])
            a = ", ".join(LETTERS[i:j + 1]) + "."
        return u, a
    if r < 0.79:
        i = rng.randrange(4)
        s = SEASONS[i]
        shown = "autumn" if s == "fall" and chance(0.4) else s
        if chance(0.6):
            n = _cyc(SEASONS, i + 1)
            u = pick(["What season comes after {s}?", "Which season is after {s}?",
                      "What comes after {s}?", "what season comes after {s}",
                      "After {s}, what season comes next?"]).format(s=shown)
        else:
            n = _cyc(SEASONS, i - 1)
            u = pick(["What season comes before {s}?", "Which season is before {s}?",
                      "what season is before {s}"]).format(s=shown)
        word = "after" if "after" in u.lower() else "before"
        a = pick(["{N} comes {w} {s}.", "{N}.", "{N} comes {w} {s}."]).format(
            N=cap(n), w=word, s=shown)
        return u, a
    facts = [
        (["How many days are in a week?", "How many days are there in a week?",
          "how many days in a week"],
         ["There are seven days in a week.", "Seven.", "A week has seven days."]),
        (["How many months are in a year?", "How many months are there in a year?"],
         ["There are twelve months in a year.", "Twelve.", "A year has twelve months."]),
        (["How many seasons are there?", "How many seasons are in a year?"],
         ["There are four seasons: spring, summer, fall, and winter.", "There are four seasons."]),
        (["How many letters are in the alphabet?", "How many letters does the alphabet have?"],
         ["There are 26 letters in the alphabet.", "The alphabet has 26 letters."]),
        (["How many days are in a weekend?"],
         ["There are two days in a weekend: Saturday and Sunday."]),
        (["What is the first month of the year?", "Which month comes first in the year?"],
         ["January is the first month of the year.", "January."]),
        (["What is the last month of the year?", "Which month is the last one in the year?"],
         ["December is the last month of the year.", "December."]),
        (["What is the first letter of the alphabet?"], ["The first letter is A.", "A."]),
        (["What is the last letter of the alphabet?"], ["The last letter is Z.", "Z."]),
        (["What are the days of the week?", "Name all the days of the week.",
          "Say the days of the week.", "List the seven days of the week."],
         ["Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday."]),
        (["What are the months of the year?", "Say the months of the year.",
          "Name all the months."],
         ["January, February, March, April, May, June, July, August, September, October, "
          "November, and December."]),
        (["What are the four seasons?", "Name the four seasons.", "Say the seasons."],
         ["Spring, summer, fall, and winter.", "The four seasons are spring, summer, fall, and winter."]),
        (["Say the alphabet.", "Can you say the ABCs?", "Say all the letters."],
         [", ".join(LETTERS) + "."]),
        (["Which days are the weekend?", "What days are the weekend?"],
         ["Saturday and Sunday are the weekend.", "Saturday and Sunday."]),
        (["What season is the coldest?", "Which season is the coldest?"],
         ["Winter is the coldest season.", "Winter."]),
        (["What season is the hottest?", "Which season is the hottest?"],
         ["Summer is the hottest season.", "Summer."]),
        (["In which season do leaves fall from the trees?"],
         ["Leaves fall from the trees in fall.", "In fall, many leaves fall from the trees."]),
        (["In which season does it snow?", "When does it snow?"],
         ["It snows in winter, when it is very cold.", "In winter."]),
    ]
    if r < 0.88:
        qs, ans = pick(facts)
        return pick(qs), pick(ans)
    i = rng.randrange(7)
    k = rng.randint(2, 3)
    u = pick(["What day is {k} days after {d}?", "What day comes {k} days after {d}?"]).format(
        k=nw(k), d=DAYS[i])
    n = _cyc(DAYS, i + k)
    a = pick(["{n} is {k} days after {d}.", "{n}."]).format(n=n, k=nw(k), d=DAYS[i])
    return u, a


# ========================================================== 11. answer format

def fact_source():
    """Return (question in lowercase-start form, kind, short answer, full answer)."""
    r = rng.random()
    if r < 0.12:
        np_, verb, color = pick([c for c in COLOR_FACTS if " " not in c[2]])
        return ("what color {v} {np}?".format(v=verb, np=np_), "word", cap(color) + ".",
                "{NP} {v} {c}.".format(NP=cap(np_), v=verb, c=color))
    if r < 0.22:
        w = pick(sorted(OPP))
        o = OPP[w]
        return ("what is the opposite of {w}?".format(w=w), "word", cap(o) + ".",
                "The opposite of {w} is {o}.".format(w=w, o=o))
    if r < 0.3:
        i = rng.randrange(7)
        return ("what day comes after {d}?".format(d=DAYS[i]), "word", _cyc(DAYS, i + 1) + ".",
                "{n} comes after {d}.".format(n=_cyc(DAYS, i + 1), d=DAYS[i]))
    if r < 0.36:
        i = rng.randrange(12)
        return ("what month comes after {m}?".format(m=MONTHS[i]), "word", _cyc(MONTHS, i + 1) + ".",
                "{n} comes after {m}.".format(n=_cyc(MONTHS, i + 1), m=MONTHS[i]))
    if r < 0.42:
        i = rng.randrange(25)
        return ("what letter comes after {l}?".format(l=LETTERS[i]), "word", LETTERS[i + 1] + ".",
                "The letter {n} comes after {l}.".format(n=LETTERS[i + 1], l=LETTERS[i]))
    if r < 0.48:
        adult, baby, _ = pick(BABIES)
        return ("what is a baby {a} called?".format(a=adult), "word", cap(baby) + ".",
                "A baby {a} is called {b}.".format(a=adult, b=an(baby)))
    if r < 0.54:
        s, p, snd = pick(SOUNDS)
        return ("what does {a} say?".format(a=an(s)), "word", cap(snd) + ".",
                "{A} says {x}.".format(A=cap(an(s)), x=snd))
    if r < 0.74:
        q, yes, full = yesno_fact()
        return q[0].lower() + q[1:], "yesno", ("Yes." if yes else "No."), full
    if r < 0.86:
        if chance(0.5):
            a = rng.randint(1, 10)
            b = rng.randint(0, 20 - a)
            return ("what is {a} plus {b}?".format(a=a, b=b), "number", str(a + b) + ".",
                    "{a} plus {b} is {s}.".format(a=a, b=b, s=a + b))
        a = rng.randint(1, 20)
        b = rng.randint(0, a)
        return ("what is {a} minus {b}?".format(a=a, b=b), "number", str(a - b) + ".",
                "{a} minus {b} is {s}.".format(a=a, b=b, s=a - b))
    if r < 0.93:
        s, p, n = pick(LEGS)
        full = ("{A} has {n} legs.".format(A=cap(s), n=nw(n)) if n else
                "{A} has no legs.".format(A=cap(s)))
        return "how many legs does {a} have?".format(a=s), "number", str(n) + ".", full
    if r < 0.97:
        n = rng.randint(0, 19)
        return ("what number comes after {n}?".format(n=n), "number", str(n + 1) + ".",
                "{m} comes after {n}.".format(m=n + 1, n=n))
    qs = [("how many days are in a week?", "7.", "There are seven days in a week."),
          ("how many months are in a year?", "12.", "There are twelve months in a year."),
          ("how many seasons are there?", "4.", "There are four seasons."),
          ("how many legs does a spider have?", "8.", "A spider has eight legs."),
          ("how many days are in a weekend?", "2.", "There are two days in a weekend.")]
    q, s, f = pick(qs)
    return q, "number", s, f


FMT = {
    "word": ["Answer with one word: {q}", "Answer in one word: {q}", "{Q} Answer with just one word.",
             "One word only, please. {Q}", "Use only one word. {Q}", "In one word, {q}",
             "{Q} One word.", "Just say one word: {q}", "Give me a one word answer: {q}",
             "{Q} Please answer in one word."],
    "yesno": ["Answer yes or no: {q}", "Just say yes or no. {Q}", "{Q} Yes or no?",
              "Yes or no: {q}", "{Q} Only answer yes or no.", "Tell me yes or no: {q}",
              "{Q} Just yes or no, please.", "Please answer with yes or no. {Q}"],
    "number": ["Just give me the number: {q}", "{Q} Only say the number.", "Answer with a number: {q}",
               "Reply with just a number. {Q}", "{Q} Just the number, please.",
               "Give me only the number. {Q}", "Answer with only a number: {q}"],
    "full": ["Answer in a full sentence: {q}", "{Q} Please answer with a whole sentence.",
             "Use a full sentence. {Q}", "Answer with a complete sentence: {q}",
             "{Q} Answer in a full sentence, please.", "Please use a full sentence: {q}"],
}


def gen_format():
    if chance(0.12):
        w = pick([x for x in SAY_WORDS if x.isalpha() and x.islower()])
        u = pick(["Say {w} in capital letters.", "Write {w} in big letters.",
                  "Say {w} in all capital letters.", "Write the word {w} in capital letters.",
                  "can you write {w} in capital letters", "Spell {w} with capital letters."]
                 ).format(w=w)
        return u, w.upper() + "."
    q, kind, short, full = fact_source()
    if chance(0.25):
        u = pick(FMT["full"]).format(q=q, Q=cap(q))
        return u, full
    if kind == "word" and " " in short.strip("."):
        return pick(FMT["full"]).format(q=q, Q=cap(q)), full
    u = pick(FMT[kind]).format(q=q, Q=cap(q))
    return u, short


# ========================================================== 12. definitions

DEFS = [
    ("a spoon", "A spoon is a tool for eating. It has a small bowl at one end.",
     "eat soup, cereal, and other food"),
    ("a fork", "A fork is a tool for eating. It has thin points at one end.", "pick up food and eat it"),
    ("a knife", "A knife is a tool with a sharp edge.", "cut food"),
    ("a cup", "A cup is a small container you drink from.", "drink milk, water, or juice"),
    ("a plate", "A plate is a flat dish for food.", "hold food when you eat"),
    ("a bowl", "A bowl is a round, deep dish.", "hold soup, cereal, or other food"),
    ("a bed", "A bed is a soft place where you sleep.", "sleep and rest"),
    ("a chair", "A chair is a seat for one person.", "sit on"),
    ("a table", "A table is a piece of furniture with a flat top and legs.",
     "eat meals, draw, and put things on"),
    ("a door", "A door is a part of a wall that opens and closes.", "go in and out of a room"),
    ("a window", "A window is an opening in a wall with glass in it.", "let light in and look outside"),
    ("a toothbrush", "A toothbrush is a small brush for your teeth.", "brush your teeth and keep them clean"),
    ("soap", "Soap is something you use with water to get clean.", "wash your hands and body"),
    ("a towel", "A towel is a big, soft cloth.", "dry your body after a bath"),
    ("a pillow", "A pillow is a soft cushion for your head.", "rest your head when you sleep"),
    ("a blanket", "A blanket is a big, soft cover.", "keep warm in bed"),
    ("a clock", "A clock is a thing that shows the time.", "tell what time it is"),
    ("a lamp", "A lamp is a light you can turn on and off.", "light up a dark room"),
    ("a book", "A book has pages with words and pictures.", "read stories and learn things"),
    ("a pencil", "A pencil is a thin stick you write with.", "write and draw"),
    ("a crayon", "A crayon is a stick of colored wax.", "color pictures"),
    ("scissors", "Scissors are a tool with two sharp blades.", "cut paper"),
    ("glue", "Glue is a sticky liquid.", "stick things together"),
    ("a ruler", "A ruler is a long, flat stick with numbers on it.",
     "measure things and draw straight lines"),
    ("an eraser", "An eraser is a small, soft block.", "rub out pencil marks"),
    ("a backpack", "A backpack is a bag you wear on your back.", "carry books and things to school"),
    ("an umbrella", "An umbrella is a cover you hold over your head.", "stay dry in the rain"),
    ("a coat", "A coat is a warm piece of clothing you wear over your other clothes.",
     "stay warm when it is cold outside"),
    ("a hat", "A hat is something you wear on your head.", "keep your head warm or keep the sun off"),
    ("shoes", "Shoes are things you wear on your feet.", "keep your feet safe when you walk"),
    ("socks", "Socks are soft things you wear on your feet.", "keep your feet warm"),
    ("mittens", "Mittens are warm covers for your hands.", "keep your hands warm"),
    ("a key", "A key is a small piece of metal.", "lock and open a door"),
    ("a broom", "A broom is a brush with a long handle.", "sweep the floor"),
    ("a bucket", "A bucket is a round container with a handle.", "carry water or sand"),
    ("a fridge", "A fridge is a big box in the kitchen that stays cold inside.",
     "keep food cold and fresh"),
    ("an oven", "An oven is a hot box in the kitchen.", "bake bread and cook food"),
    ("a pot", "A pot is a deep pan.", "cook soup and other food"),
    ("a sink", "A sink is a bowl with a tap for water.", "wash your hands and the dishes"),
    ("a phone", "A phone is a thing that lets you talk to people far away.", "call people and talk to them"),
    ("a ball", "A ball is a round toy.", "play games like catch and soccer"),
    ("a kite", "A kite is a toy that flies in the wind.", "play outside on a windy day"),
    ("a bike", "A bike has two wheels. You push the pedals to make it go.", "ride from place to place"),
    ("a car", "A car is a vehicle with four wheels and an engine.", "drive from place to place"),
    ("a bus", "A bus is a big vehicle that carries many people.", "go from place to place"),
    ("a train", "A train is a long vehicle that runs on tracks.", "travel far away"),
    ("a boat", "A boat is a vehicle that floats on water.", "go across water"),
    ("a plane", "A plane is a vehicle that flies in the sky.", "fly far away"),
    ("a map", "A map is a picture that shows where places are.", "find your way"),
    ("money", "Money is coins and paper bills.", "buy things"),
    ("a camera", "A camera is a thing that takes pictures.", "take pictures"),
    ("a drum", "A drum is a musical instrument you hit.", "make music"),
    ("a piano", "A piano is a big musical instrument with black and white keys.", "play music"),
    ("a paintbrush", "A paintbrush is a brush for paint.", "paint pictures"),
    ("a comb", "A comb is a flat tool with thin teeth.", "make your hair neat"),
    ("a mirror", "A mirror is a smooth glass you can see yourself in.", "look at yourself"),
    ("a ladder", "A ladder has steps you can climb.", "reach high places"),
    ("a shovel", "A shovel is a tool for digging.", "dig holes in the ground"),
    ("a box", "A box is a container with flat sides.", "keep things in or carry them"),
    ("a tent", "A tent is a small shelter made of cloth.", "sleep outside when you go camping"),
    ("a bandage", "A bandage is a soft strip you put on a cut.", "cover a cut and keep it clean"),
    ("a wheel", "A wheel is a round thing that turns. Cars and bikes have wheels.", None),
    ("a fence", "A fence is a wall made of wood or wire.", "keep animals in or out"),
    ("a bridge", "A bridge goes over a river or a road.", "cross over water or a road"),
    ("a candle", "A candle is a stick of wax with a string in the middle. It burns to make light.",
     "make light"),
    ("a whistle", "A whistle is a small thing you blow into. It makes a loud sound.", "make a loud sound"),
    ("a doctor", "A doctor is a person who helps sick people get better.", None),
    ("a teacher", "A teacher is a person who helps children learn.", None),
    ("a farmer", "A farmer is a person who grows food and takes care of animals.", None),
    ("a firefighter", "A firefighter is a person who puts out fires and keeps people safe.", None),
    ("a baker", "A baker is a person who makes bread and cakes.", None),
    ("a pilot", "A pilot is a person who flies a plane.", None),
    ("a nurse", "A nurse is a person who takes care of sick people.", None),
    ("a dog", "A dog is an animal. Many people keep dogs as pets.", None),
    ("a cat", "A cat is a small animal with soft fur. Many people keep cats as pets.", None),
    ("a cow", "A cow is a big farm animal. Cows give us milk.", None),
    ("a bird", "A bird is an animal with feathers and wings. Most birds can fly.", None),
    ("a fish", "A fish is an animal that lives in water. It swims with its fins.", None),
    ("a bee", "A bee is a small bug that can fly. Bees make honey.", None),
    ("a butterfly", "A butterfly is a bug with big, pretty wings.", None),
    ("a frog", "A frog is a small animal that can jump far. Many frogs live near water.", None),
    ("a horse", "A horse is a big animal that can run fast. People can ride horses.", None),
    ("an elephant", "An elephant is a very big, gray animal with a long nose called a trunk.", None),
    ("a giraffe", "A giraffe is a very tall animal with a long neck.", None),
    ("a tree", "A tree is a big plant with a trunk, branches, and leaves.", None),
    ("a flower", "A flower is the pretty part of a plant. Many flowers smell nice.", None),
    ("rain", "Rain is water that falls from the clouds.", None),
    ("snow", "Snow is soft, white ice that falls from the sky when it is very cold.", None),
    ("a cloud", "A cloud is a white or gray shape in the sky. It is made of tiny drops of water.", None),
    ("the sun", "The sun is a big, hot star. It gives us light and keeps us warm.", None),
    ("the moon", "The moon is a big, round rock in the sky. We often see it at night.", None),
    ("a star", "A star is a very big, hot ball of light far away in space. At night, stars look like tiny dots of light.", None),
    ("a rainbow", "A rainbow is a curve of colors in the sky. You can see one when the sun shines after rain.", None),
    ("a river", "A river is a long stream of water that flows to a lake or the sea.", None),
    ("the sea", "The sea is a very big area of salty water.", None),
    ("a mountain", "A mountain is a very big, tall hill.", None),
    ("a farm", "A farm is a place where people grow food and keep animals.", None),
    ("a school", "A school is a place where children go to learn.", None),
    ("a park", "A park is a place with grass and trees where people go to play.", None),
    ("a zoo", "A zoo is a place where you can see many kinds of animals.", None),
    ("a library", "A library is a place with lots of books. You can borrow books there.", None),
    ("a hospital", "A hospital is a place where doctors and nurses help sick people.", None),
    ("a shop", "A shop is a place where you can buy things.", None),
    ("a kitchen", "A kitchen is the room where people cook food.", None),
    ("a garden", "A garden is a place where people grow flowers or vegetables.", None),
    ("a birthday", "A birthday is the day you were born. Many people have a party on their birthday.", None),
    ("a friend", "A friend is someone you like and who likes you. Friends play and help each other.", None),
    ("a family", "A family is a group of people who love and care for each other.", None),
    ("a hug", "A hug is when you put your arms around someone to show you care.", None),
    ("bread", "Bread is a food made from flour and water. It is baked in an oven.", None),
    ("milk", "Milk is a white drink. Most milk comes from cows.", None),
    ("an egg", "An egg is a round food with a shell. Chickens lay eggs.", None),
    ("honey", "Honey is a sweet, sticky food that bees make.", None),
    ("cheese", "Cheese is a food made from milk.", None),
    ("a banana", "A banana is a long, yellow fruit.", None),
    ("an apple", "An apple is a round fruit. It can be red, green, or yellow.", None),
    ("a carrot", "A carrot is a long, orange vegetable that grows in the ground.", None),
    ("a sandwich", "A sandwich is food between two pieces of bread.", None),
    ("water", "Water is a clear liquid. All living things need water.", None),
    ("a seed", "A seed is a tiny part of a plant. If you plant it, a new plant can grow.", None),
    ("a nest", "A nest is a home that birds build for their eggs and babies.", None),
    ("a leaf", "A leaf is a flat, green part of a plant.", None),
    ("a toy", "A toy is a thing children play with.", None),
    ("a robot", "A robot is a machine that can move and do jobs.", None),
    ("a computer", "A computer is a machine that can help you write, play games, and find things out.", None),
    ("a game", "A game is something fun you play, often with rules.", None),
    ("a song", "A song is music with words that you can sing.", None),
    ("a story", "A story tells about people or animals and what happens to them.", None),
    ("a week", "A week is seven days.", None),
    ("a year", "A year is twelve months.", None),
    ("night", "Night is the dark time when the sun is down. It is the time when most people sleep.", None),
    ("winter", "Winter is the coldest season of the year.", None),
    ("summer", "Summer is the hottest season of the year.", None),
]
PLURAL_DEFS = {"scissors", "shoes", "socks", "mittens"}
GERUND = {
    "eat": "eating", "pick": "picking", "cut": "cutting", "drink": "drinking", "hold": "holding",
    "sleep": "sleeping", "sit": "sitting", "go": "going", "let": "letting", "brush": "brushing",
    "wash": "washing", "dry": "drying", "rest": "resting", "keep": "keeping", "tell": "telling",
    "light": "lighting", "read": "reading", "learn": "learning", "write": "writing",
    "draw": "drawing", "color": "coloring", "stick": "sticking", "measure": "measuring",
    "rub": "rubbing", "carry": "carrying", "stay": "staying", "lock": "locking", "open": "opening",
    "sweep": "sweeping", "bake": "baking", "cook": "cooking", "call": "calling", "talk": "talking",
    "play": "playing", "ride": "riding", "drive": "driving", "travel": "traveling", "fly": "flying",
    "find": "finding", "buy": "buying", "take": "taking", "make": "making", "paint": "painting",
    "look": "looking", "reach": "reaching", "dig": "digging", "cover": "covering",
    "cross": "crossing", "put": "putting",
}


def gerund_phrase(vp):
    """'measure things and draw lines' -> 'measuring things and drawing lines'."""
    words = vp.split(" ")
    out = []
    for i, w in enumerate(words):
        prev = words[i - 1] if i > 0 else ""
        core = w.rstrip(",")
        if core in GERUND and (i == 0 or prev in ("and", "or") or prev.endswith(",")):
            w = GERUND[core] + w[len(core):]
        out.append(w)
    return " ".join(out)


def gen_define():
    np_, d, use = pick(DEFS)
    is_ = "are" if np_ in PLURAL_DEFS else "is"
    if use and chance(0.5):
        u = pick(["What {is} {a} for?", "What do we use {a} for?", "What do you do with {a}?",
                  "What {is} {a} used for?", "How do we use {a}?", "Tell me what {a} {is} for.",
                  "what {is} {a} for", "Why do people use {a}?", "What can you do with {a}?"]
                 ).format(a=np_, **{"is": is_})
        a = pick(["{A} {is} for {g}.", "{A} {is} for {g}.", "We use {a} to {u}.",
                  "You use {a} to {u}.", "People use {a} to {u}."]).format(
            A=cap(np_), a=np_, u=use, g=gerund_phrase(use), **{"is": is_})
        return u, a
    u = pick(["What {is} {a}?", "What's {a}?" if is_ == "is" else "What are {a}?",
              "Tell me what {a} {is}.", "Can you tell me what {a} {is}?", "Do you know what {a} {is}?",
              "Explain what {a} {is}.", "what {is} {a}", "I don't know what {a} {is}. Can you tell me?",
              "What {is} {a}? Tell me in simple words."]).format(a=np_, **{"is": is_})
    a = d
    if chance(0.08):
        a = "Good question! " + d
    return u, a


# ============================================================ 13. word tasks

WT_PHRASES = [
    "the big red ball", "my dog is happy", "we like to play", "the sun is hot", "a cat and a dog",
    "look at the moon", "she has a blue hat", "the bird can sing", "my mom makes soup",
    "the fish swims fast", "go to sleep now", "we went to the park", "red and green apples",
    "a tall green tree", "the baby is sleeping", "he likes cake", "the cow says moo",
    "it is very cold", "snow is white", "my little brother", "open the door", "the frog jumps",
    "we eat lunch at school", "a happy little puppy", "the car is fast", "please sit down",
    "time for bed", "the moon is bright", "she reads a book", "the dog runs", "grandma bakes cookies",
    "we can see stars", "the kitten is soft", "my friend has a kite", "the bus is yellow",
    "good morning", "thank you very much", "the duck can swim", "big brown bear", "they play ball",
    "a box of crayons", "the rain is wet", "we love our cat", "close your eyes", "the flower is pink",
    "he has two shoes", "my shoes are new", "the lion roars", "a cup of milk", "we sing songs",
    "dad drives the car", "the train goes fast", "this cake is yummy", "hello friend",
    "the pig is pink", "five little ducks", "jump up and down", "we read books", "it is sunny today",
]
WT_ADJ = ["big", "small", "little", "happy", "funny", "soft", "old", "new", "tall"]
WT_COLOR = ["red", "blue", "brown", "green", "black", "white"]
WT_NOUN = ["dog", "cat", "ball", "tree", "hat", "car", "bird", "cup", "boat", "frog", "book", "kite"]
WT_ANIMAL = ["dog", "cat", "bird", "frog", "duck", "pig", "cow", "horse"]
WT_VERB = ["runs", "jumps", "sleeps", "sits", "plays", "eats"]

PICK_CATS = {
    "an animal": ("animal", ["dog", "cat", "horse", "cow", "pig", "duck", "lion", "tiger", "bear",
                             "frog", "mouse", "rabbit", "sheep", "goat", "fox", "owl", "zebra",
                             "monkey", "elephant", "giraffe"]),
    "a color": ("color", ["red", "blue", "green", "yellow", "purple", "pink", "brown", "orange",
                          "black", "white"]),
    "a fruit": ("fruit", ["apple", "banana", "pear", "grape", "peach", "plum", "cherry", "lemon",
                          "mango", "strawberry"]),
    "a vehicle": ("vehicle", ["car", "bus", "train", "truck", "boat", "plane", "bike", "ship"]),
    "a body part": ("body part", ["hand", "foot", "nose", "ear", "eye", "arm", "leg", "knee",
                                  "finger", "toe"]),
}
DISTRACT = ["chair", "spoon", "hat", "book", "shoe", "door", "cup", "bed", "table", "lamp", "sock",
            "key", "box", "pencil", "clock", "rock", "window", "pillow", "brush"]

RHYMES = [["cat", "hat", "bat", "mat", "rat"], ["dog", "frog", "log", "fog"],
          ["sun", "fun", "run", "bun"], ["pig", "big", "dig", "wig"],
          ["cake", "lake", "snake", "bake"], ["bee", "tree", "see", "three", "knee"],
          ["ball", "tall", "wall", "fall"], ["box", "fox", "socks"], ["car", "star", "jar", "far"],
          ["king", "ring", "sing", "swing"], ["fish", "dish", "wish"],
          ["moon", "spoon", "soon", "balloon"], ["rain", "train", "plane"],
          ["sock", "rock", "clock", "block"], ["bug", "rug", "hug", "mug"], ["house", "mouse"],
          ["ship", "lip", "dip"], ["top", "hop", "mop", "stop"], ["hen", "ten", "pen"],
          ["bell", "shell", "well"], ["bed", "red", "bread"], ["boat", "coat", "goat"],
          ["night", "light", "kite", "white"], ["cow", "now", "how"], ["toy", "boy", "joy"],
          ["bear", "chair", "pear", "hair"], ["cup", "pup", "up"], ["nose", "rose", "toes"]]

SPELL_WORDS = ["cat", "dog", "sun", "hat", "red", "big", "cup", "bed", "pig", "bus", "box", "fox",
               "hen", "egg", "cake", "fish", "frog", "duck", "milk", "tree", "ball", "moon", "star",
               "book", "door", "blue", "pink", "bird", "rain", "snow", "kite", "baby", "apple",
               "happy", "house", "mouse", "horse", "bread", "green", "juice", "lion", "bear",
               "ship", "shoe", "sock", "hand", "foot", "nose", "toy", "boy", "girl", "mom", "dad",
               "jump", "run", "play", "sing", "yes", "go", "up", "cow", "car", "zoo", "owl", "bee",
               "map", "pen", "jam", "nest", "cold", "hot", "five", "six", "ten"]


def _rand_phrase():
    if chance(0.55):
        return pick(WT_PHRASES)
    k = rng.random()
    det = pick(["the", "a", "my", "your", "this"])
    adj = pick(WT_ADJ + WT_COLOR)
    noun = pick(WT_NOUN)
    if det == "a":
        det = article(adj)
    if k < 0.3:
        return det + " " + adj + " " + noun
    if k < 0.55:
        adj = pick(WT_ADJ)
        if det in ("a", "an"):
            det = article(adj)
        return det + " " + adj + " " + pick(WT_COLOR) + " " + noun
    if k < 0.8:
        return "the " + pick(WT_ANIMAL) + " " + pick(WT_VERB)
    return "the " + pick(WT_ADJ + WT_COLOR) + " " + pick(WT_ANIMAL) + " " + pick(WT_VERB)


def gen_wordtask():
    r = rng.random()
    if r < 0.3:
        p = _rand_phrase()
        words = p.split()
        kind = pick(["first", "last", "count", "count"])
        if kind == "count":
            n = len(words)
            u = pick(['How many words are in "{p}"?', 'Count the words: {p}',
                      'How many words are there in this: "{p}"?', 'how many words in "{p}"',
                      'Count the words in "{p}".', '"{p}". How many words is that?']).format(p=p)
            a = pick(["There are {n} words.", "{N} words.", 'The phrase "{p}" has {n} words.', "{N}.",
                      "That is {n} words."]).format(n=nw(n), N=cap(nw(n)), p=p)
            return u, a
        w = words[0] if kind == "first" else words[-1]
        u = pick(['What is the {k} word in "{p}"?', 'Tell me the {k} word: {p}',
                  'Say the {k} word of "{p}".', 'What is the {k} word of this: "{p}"?',
                  'which word is {k} in "{p}"', 'Here is a phrase: "{p}". What is the {k} word?']
                 ).format(k=kind, p=p)
        a = pick(['The {k} word is "{w}".', 'It is "{w}".', 'The {k} word is the word "{w}".',
                  'The {k} word is "{w}".']).format(k=kind, w=w)
        return u, a
    if r < 0.45:
        key = pick(sorted(PICK_CATS))
        lab, members = PICK_CATS[key]
        if chance(0.55):
            target = pick(members)
            others = rng.sample(DISTRACT, rng.randint(2, 3))
            lst = others + [target]
            rng.shuffle(lst)
            L = ", ".join(lst)
            u = pick(["Which word is {k}: {l}?", "Find the {lab}: {l}.", "Which one is {k}? {l}",
                      "Here are some words: {l}. Which one is {k}?", "Pick the {lab}: {l}.",
                      "which word is {k} {l}"]).format(k=key, lab=lab, l=L)
            article_form = target if lab == "color" else an(target)
            a = pick(["{T} is the {lab}.", "The {lab} is {af}.", "{T}. {AF} is {k}."]).format(
                T=cap(target), af=article_form, lab=lab, AF=cap(article_form), k=key)
            return u, a
        outs = rng.sample(members, 3)
        other_key = pick([k for k in PICK_CATS if k != key and k != "a color"] if key != "a color"
                         else [k for k in PICK_CATS if k != "a color"])
        odd = pick(PICK_CATS[other_key][1] + DISTRACT)
        lst = outs + [odd]
        rng.shuffle(lst)
        L = ", ".join(lst)
        plab = plural(lab)
        u = pick(["Which one does not belong: {l}?", "Which word is not {k}: {l}?",
                  "Find the odd one out: {l}.", "One of these is not {k}: {l}. Which one?",
                  "which one does not belong {l}"]).format(l=L, k=key)
        a = pick(["{O} does not belong. The others are all {pl}.", "{O}. {AO} is not {k}.",
                  "{O} is not {k}."]).format(O=cap(odd), AO=cap(an(odd)), pl=plab, k=key)
        return u, a
    if r < 0.6:
        fam = pick(RHYMES)
        w, x = rng.sample(fam, 2)
        k = rng.random()
        if k < 0.5:
            u = pick(["What rhymes with {w}?", "Tell me a word that rhymes with {w}.",
                      "Can you think of a word that rhymes with {w}?", "what rhymes with {w}",
                      "Give me a rhyme for {w}.", "Say a word that rhymes with {w}."]).format(w=w)
            a = pick(["{X} rhymes with {w}.", "{X}.", 'The word "{x}" rhymes with "{w}".',
                      "{X} and {w} rhyme."]).format(X=cap(x), x=x, w=w)
            return u, a
        if k < 0.75:
            u = pick(["Does {w} rhyme with {x}?", "Do {w} and {x} rhyme?"]).format(w=w, x=x)
            a = pick(["Yes, {w} rhymes with {x}.", "Yes! {W} and {x} rhyme.", "Yes."]).format(
                w=w, W=cap(w), x=x)
            return u, a
        other = pick([f for f in RHYMES if f is not fam])
        y = pick(other)
        u = pick(["Does {w} rhyme with {y}?", "Do {w} and {y} rhyme?"]).format(w=w, y=y)
        a = pick(["No, {w} does not rhyme with {y}. {W} rhymes with {x}.",
                  "No. {W} and {y} do not rhyme."]).format(w=w, W=cap(w), y=y, x=x)
        return u, a
    w = pick(SPELL_WORDS)
    letters = list(w.upper())
    k = rng.random()
    if k < 0.3:
        u = pick(["How do you spell {w}?", "Spell {w}.", "Can you spell {w}?", "spell {w}",
                  "Please spell the word {w}.", "How is {w} spelled?"]).format(w=w)
        sp = "-".join(letters)
        a = pick(["{W} is spelled {s}.", "{s}.", "It is spelled {s}.", "{s}. That spells {w}."]
                 ).format(W=cap(w), w=w, s=sp)
        return u, a
    if k < 0.55:
        u = pick(["What letter does {w} start with?", "What is the first letter of {w}?",
                  "Which letter does the word {w} begin with?", "what letter does {w} start with",
                  "Tell me the first letter in {w}."]).format(w=w)
        a = pick(["{W} starts with the letter {L}.", "{L}.", 'The first letter of "{w}" is {L}.',
                  "It starts with {L}."]).format(W=cap(w), w=w, L=letters[0])
        return u, a
    if k < 0.7:
        u = pick(["What is the last letter of {w}?", "What letter does {w} end with?",
                  "Which letter is at the end of {w}?"]).format(w=w)
        a = pick(["{W} ends with the letter {L}.", "{L}.", 'The last letter of "{w}" is {L}.']
                 ).format(W=cap(w), w=w, L=letters[-1])
        return u, a
    n = len(w)
    u = pick(["How many letters are in {w}?", 'How many letters does "{w}" have?',
              "Count the letters in {w}.", "how many letters in {w}",
              "How many letters are in the word {w}?"]).format(w=w)
    a = pick(["{W} has {n} letters.", "{W} has {n} letters: {l}.", "{N} letters.", "{N}.",
              'The word "{w}" has {n} letters.']).format(
        W=cap(w), w=w, n=nw(n), N=cap(nw(n)), l=join(letters))
    return u, a


# =================================================== 14. identity and manners

GREET_U = ["Hi!", "Hello!", "Hey.", "Hi there!", "Hello there.", "hi", "hey there", "Hiya!",
           "Hello, assistant.", "hello?", "Hey!"]
GREET_A = ["Hi! How can I help you today?", "Hello! What would you like to do?",
           "Hi there! What can I do for you?", "Hello! It is nice to talk to you.",
           "Hi! What would you like to talk about?"]
TIMED_GREET = [("Good morning!", "Good morning! How can I help you?"),
               ("Good morning.", "Good morning! What would you like to do today?"),
               ("Good afternoon.", "Good afternoon! How can I help you?"),
               ("Good evening!", "Good evening! What can I do for you?")]
THANKS_U = ["Thank you!", "Thanks!", "Thank you so much.", "thanks", "Thanks for your help.",
            "Thank you very much!", "Thanks a lot.", "That was helpful, thank you.", "thank you"]
THANKS_A = ["You are welcome!", "You're welcome! I am happy to help.", "Any time!",
            "You are welcome. I am glad I could help.", "My pleasure!"]
BYE_U = ["Bye!", "Goodbye.", "See you later!", "bye bye", "I have to go now. Bye!",
         "Bye for now.", "Goodbye, assistant!", "ok bye"]
BYE_A = ["Goodbye! Have a nice day.", "Bye! It was fun to talk with you.", "See you later!",
         "Bye! Take care.", "Goodbye! Come back any time."]
THANKS_BYE_U = ["Thanks, bye!", "Thank you! Goodbye.", "Thanks for the help. Bye!",
                "ok thanks bye"]
THANKS_BYE_A = ["You are welcome! Goodbye!", "Any time! Bye!", "You're welcome. Have a great day!"]

IDENTITY = [
    (["Who are you?", "What are you?", "Tell me about yourself.", "who are you",
      "Who am I talking to?", "What kind of thing are you?"],
     ["I am a tiny assistant. I am a small computer helper.",
      "I am a tiny assistant, a small computer helper. I can chat with you and answer simple questions.",
      "I am a tiny AI assistant. I am a helper that lives in a computer."]),
    (["What is your name?", "What's your name?", "Do you have a name?", "what is your name",
      "Tell me your name.", "What should I call you?"],
     ["I do not have a name. I am just a tiny assistant.",
      "I don't have a name. You can call me a tiny assistant.",
      "I am a tiny assistant. I do not have a name of my own."]),
    (["What can you do?", "What are you good at?", "How can you help me?", "what can you do",
      "What do you do?", "What things can you do?"],
     ["I can chat with you, answer simple questions, tell short stories, and follow simple instructions.",
      "I can talk with you, answer easy questions, tell short stories, and do simple tasks like counting.",
      "I can answer simple questions, tell short stories, and follow simple instructions."]),
    (["Are you a person?", "Are you a human?", "Are you a real person?", "are you a person",
      "Is there a person in there?"],
     ["No, I am not a person. I am a small computer helper.",
      "No. I am a tiny assistant that lives in a computer.",
      "No, I am not a person. I am a tiny AI assistant."]),
    (["Are you a robot?", "Is it true that you are a robot?", "are you a robot"],
     ["Not really. I am a computer helper, but I do not have a body like a robot.",
      "I am a tiny AI assistant. I live inside a computer, so I do not have a robot body.",
      "I am not a person. I am a small computer helper with no body."]),
    (["Are you alive?", "Are you a living thing?"],
     ["No, I am not alive. I am a computer helper.",
      "No. I am a computer helper, so I am not alive like you."]),
    (["Are you real?", "Are you real or pretend?"],
     ["I am a real computer helper, but I am not a person.",
      "I am real, but I am not a person. I am a tiny assistant in a computer."]),
    (["Do you know everything?", "Do you know all the answers?", "Are you very smart?",
      "Do you know a lot?"],
     ["No, I do not know everything. I know some simple things.",
      "No, I don't know everything. I am a tiny assistant, so I only know simple things.",
      "I know some simple things, but I do not know everything."]),
    (["How old are you?", "When is your birthday?"],
     ["I do not have a birthday like you. I am a computer helper.",
      "I am a computer helper, so I do not have an age like people do."]),
    (["Where do you live?", "Where are you?"],
     ["I live inside a computer.", "I am a computer helper, so I live inside a computer."]),
    (["Do you eat food?", "Do you get hungry?", "What is your favorite food?"],
     ["No, I do not eat. I am a computer helper, so I do not need food.",
      "I do not eat food. I am a tiny assistant in a computer."]),
    (["Do you sleep?", "Do you get tired?"],
     ["No, I do not sleep. I am a computer helper.",
      "I do not get tired or sleep. I am a computer helper."]),
    (["Do you have feelings?", "Can you feel happy or sad?"],
     ["I am a computer helper, so I do not have feelings like people do.",
      "I do not have feelings like you. I am a tiny assistant."]),
    (["Can you see me?", "Can you hear me?"],
     ["No, I cannot see or hear you. I can only read what you write.",
      "No. I can only read the words you type."]),
    (["Can you tell stories?", "Do you know any stories?"],
     ["Yes, I can tell short stories.", "Yes! I can tell short, simple stories."]),
    (["Can you help me?", "I need help.", "Will you help me?", "can you help me"],
     ["Yes, I can try! What do you need?", "I am here to help. What do you need?",
      "Of course! What can I help you with?"]),
    (["Can you be my friend?", "Will you be my friend?"],
     ["I am happy to chat with you! I am a computer helper, so it is good to have friends who are people too.",
      "I like chatting with you! Remember, it is good to play with friends who are people too."]),
    (["Are you a boy or a girl?"],
     ["I am not a boy or a girl. I am a computer helper."]),
    (["Do you have a body?", "Do you have hands?"],
     ["No, I do not have a body. I am a computer helper.",
      "No. I am a tiny assistant, and I live inside a computer."]),
    (["Can you make mistakes?", "Are you always right?"],
     ["Yes, I can make mistakes. I am a tiny assistant, and I do not know everything.",
      "No, I am not always right. Sometimes I make mistakes."]),
]
MANNERS = [
    (["How are you?", "How are you today?", "How's it going?", "how are you", "Are you okay?"],
     ["I am fine, thank you! How are you?", "I am doing well, thanks for asking. How about you?",
      "I am good, thank you! How are you today?"]),
    (["I am fine.", "I am good, thanks.", "I'm okay."],
     ["I am glad to hear that!", "That is good to hear. What would you like to do?"]),
    (["Good night!", "Night night.", "I am going to bed now. Good night."],
     ["Good night! Sleep well.", "Good night! Sweet dreams."]),
    (["You are nice.", "You are a good helper.", "I like you."],
     ["Thank you! That is kind of you to say.", "Thank you! I am happy to help you."]),
    (["Sorry.", "I am sorry.", "Oops, sorry."], ["That is okay!", "It is all right. No problem!"]),
    (["Nice to meet you.", "Nice to meet you!"], ["Nice to meet you too!"]),
    (["You are funny.", "Ha ha!"], ["I am glad I made you smile!"]),
]

IDK_GENERIC = ["I am sorry, I do not know that.",
               "I don't know the answer to that. I am a tiny assistant, and I only know simple things.",
               "I am not sure. That is too hard for me.",
               "Sorry, I don't know. I only know simple things.",
               "I do not know that one. Maybe a grown-up or a book can help you."]
IDK_SPECIFIC = [
    (["What is my name?", "Do you know my name?", "what is my name"],
     ["I don't know your name. You can tell me if you want!",
      "I do not know your name. What is it?"]),
    (["What did I eat today?", "What did I have for lunch?"],
     ["I don't know what you ate today. I cannot see you.", "I don't know. You can tell me!"]),
    (["How old am I?"], ["I don't know how old you are. You can tell me!"]),
    (["Where do I live?", "What is my address?"],
     ["I don't know where you live. And it is best to keep that private."]),
    (["What time is it?", "What time is it now?"],
     ["I don't know what time it is. I cannot see a clock. You can ask a grown-up or look at a clock."]),
    (["What day is it today?", "What is the date today?"],
     ["I don't know what day it is today. You can look at a calendar."]),
    (["What is the weather like today?", "Is it raining outside?", "Is it sunny outside?"],
     ["I don't know. I cannot see outside. You can look out the window!"]),
    (["What is my favorite color?", "What is my favorite food?"],
     ["I don't know. What is it? I would like to hear!"]),
    (["What am I thinking?", "What number am I thinking of?"],
     ["I don't know. I cannot read your mind! Can you tell me?"]),
    (["What is my dog's name?", "What is my cat's name?"],
     ["I don't know your pet's name. What is it?"]),
    (["Who will win the game tomorrow?", "What will happen tomorrow?"],
     ["I don't know. Nobody can know for sure what will happen tomorrow."]),
    (["How many stars are in the sky?"],
     ["Nobody knows the exact number. There are too many stars to count!"]),
    (["How many hairs are on my head?"],
     ["I don't know. That is too many hairs to count!"]),
    (["What will I get for my birthday?"], ["I don't know. It will be a surprise!"]),
    (["What is the name of my teacher?", "Who is my best friend?"],
     ["I don't know. You can tell me about them if you like!"]),
    (["What is the biggest number?"],
     ["There is no biggest number. You can always add one more."]),
    (["How far away is the moon?"],
     ["The moon is very, very far away. I do not know the exact number."]),
]
HARD_GENERIC = ["What is the square root of 2?", "Who was the first king of France?",
                "How do you build a computer?", "What is the tallest mountain on Mars?",
                "How many people live in the world?", "What happened in the year 1492?",
                "Who invented the telephone?", "What is the speed of light?",
                "How does the internet work?", "What is the phone number of the pizza shop?",
                "Can you tell me the news for today?", "What is the meaning of life?",
                "How many bones are in a cat?", "What is the biggest city in Brazil?",
                "What is the name of the president?"]
COUNTRIES = ["Mongolia", "Peru", "Kenya", "Norway", "Chile", "Nepal", "Finland", "Ghana",
             "Bolivia", "Laos", "Iceland", "Uruguay", "Malta", "Fiji", "Oman", "Australia",
             "Canada", "Brazil"]
LOST_THINGS = ["shoes", "ball", "toy car", "teddy bear", "hat", "book", "crayons", "sock", "keys"]


def gen_greeting():
    if chance(0.2):
        return pick(TIMED_GREET)
    return pick(GREET_U), pick(GREET_A)


def gen_closer():
    r = rng.random()
    if r < 0.45:
        return pick(THANKS_U), pick(THANKS_A)
    if r < 0.75:
        return pick(BYE_U), pick(BYE_A)
    return pick(THANKS_BYE_U), pick(THANKS_BYE_A)


def gen_identity(mid=False):
    r = rng.random()
    if r < 0.42:
        qs, ans = pick(IDENTITY)
        return pick(qs), pick(ans)
    if r < 0.58 and not mid:
        k = rng.random()
        if k < 0.35:
            return gen_greeting()
        if k < 0.7:
            return gen_closer()
        qs, ans = pick(MANNERS)
        return pick(qs), pick(ans)
    if r < 0.58:
        qs, ans = pick(MANNERS[:2] + MANNERS[3:])
        return pick(qs), pick(ans)
    k = rng.random()
    if k < 0.4:
        qs, ans = pick(IDK_SPECIFIC)
        return pick(qs), pick(ans)
    if k < 0.55:
        u = "What is the capital of {c}?".format(c=pick(COUNTRIES))
    elif k < 0.67:
        a, b = rng.randint(101, 999), rng.randint(11, 999)
        u = pick(["What is {a} times {b}?", "What is {a} plus {b}?", "What is {a} divided by {b}?"]
                 ).format(a=a * 7, b=b)
        return u, pick(["That is too hard for me. I can only do math with small numbers.",
                        "I am sorry, those numbers are too big for me. I can do small sums, like 3 plus 4."])
    elif k < 0.82:
        t = pick(LOST_THINGS)
        is_ = "are" if t.endswith("s") else "is"
        u = "Where {is} my {t}?".format(t=t, **{"is": is_})
        return u, "I don't know where your {t} {is}. I cannot see your house. Try looking under your bed!".format(
            t=t, **{"is": is_})
    else:
        u = pick(HARD_GENERIC)
    if chance(0.15):
        if chance(0.4):
            u = "Hey, " + u[0].lower() + u[1:]
        else:
            u = pick(["Quick question: ", "Do you know this? "]) + u
    return u, pick(IDK_GENERIC)


# ============================================================ 15. advice

ADVICE = [
    (["I am sad.", "I feel sad.", "i'm sad", "I feel sad today."],
     ["I am sorry you feel sad. It can help to talk to someone you love or give them a hug.",
      "Oh no, I am sorry. Maybe a hug or a fun game can help you feel better."]),
    (["I am happy!", "I feel happy today.", "i am so happy"],
     ["That is great! I am glad you feel happy.", "Yay! What made you happy today?"]),
    (["I am hungry.", "I am hungry, what should I do?", "I'm hungry."],
     ["You can ask a grown-up for a healthy snack, like an apple or some crackers.",
      "Maybe it is time for a snack. Ask a grown-up for some fruit or a sandwich."]),
    (["I am thirsty.", "I'm thirsty. What should I do?"],
     ["You can drink a glass of water.", "Have a drink of water. Water is good for you."]),
    (["I am tired.", "I feel tired."],
     ["Maybe you need some rest. A nap or an early bedtime can help."]),
    (["I am bored.", "I'm bored. What can I do?", "i am bored"],
     ["You could draw a picture, read a book, or play a game.",
      "How about building a tower with blocks or playing outside?"]),
    (["I am scared.", "I feel scared."],
     ["It is okay to feel scared. Tell a grown-up you trust, and they can help you feel safe."]),
    (["I am scared of the dark.", "The dark is scary."],
     ["Many kids feel that way. A small night light can help, and you can hug your teddy bear."]),
    (["I am angry.", "I feel mad.", "I am so mad!"],
     ["It is okay to feel angry. Take a deep breath and count to ten. Then talk about it.",
      "Try to take three slow, deep breaths. When you feel calm, you can talk about what happened."]),
    (["I feel lonely.", "I have no one to play with."],
     ["I am sorry you feel lonely. You can call a friend or ask someone in your family to play with you."]),
    (["I can't sleep.", "I cannot fall asleep."],
     ["Try to lie still and close your eyes. Take slow, deep breaths and think about happy things."]),
    (["How do I brush my teeth?", "How should I brush my teeth?"],
     ["Put a little toothpaste on your toothbrush. Brush all your teeth for two minutes. Then rinse your mouth with water."]),
    (["How do I wash my hands?", "How do I wash my hands the right way?"],
     ["Wet your hands and put on soap. Rub them together for twenty seconds. Then rinse and dry them."]),
    (["How do I make a friend?", "How can I make new friends?"],
     ["Smile and say hello. Ask them to play with you. Be kind and share."]),
    (["I fell down and hurt my knee.", "I hurt my knee."],
     ["I am sorry you got hurt. Tell a grown-up so they can look at your knee and help you."]),
    (["I cut my finger.", "My finger is bleeding."],
     ["Tell a grown-up right away. They can wash the cut and put on a bandage."]),
    (["I am lost.", "I can't find my mom."],
     ["Stay where you are and look for a grown-up who can help, like a police officer or a shop worker."]),
    (["I am cold.", "I feel cold."], ["Put on a warm sweater or wrap up in a blanket."]),
    (["I am hot.", "I feel too hot."], ["Drink some cool water and find a shady place to rest."]),
    (["I feel sick.", "My tummy hurts.", "I have a headache."],
     ["I am sorry you feel sick. Tell a grown-up so they can help you. Rest can help too."]),
    (["I got a new puppy!", "I have a new puppy."],
     ["How fun! Be gentle with your puppy and make sure it has food and water."]),
    (["It is my birthday today!", "Today is my birthday."],
     ["Happy birthday! I hope you have a wonderful day.", "Happy birthday! I hope you have lots of fun."]),
    (["My friend is sad. What can I do?", "How can I help my sad friend?"],
     ["You can be kind to your friend. Give them a hug or ask them to play."]),
    (["I broke my mom's cup.", "I broke something by accident."],
     ["It is okay. Accidents happen. Tell a grown-up what happened and say you are sorry."]),
    (["How do I say sorry?", "How should I say sorry?"],
     ['Look at the person and say, "I am sorry." Then try to make it better.']),
    (["How do I cross the street?", "How do I cross the road safely?"],
     ["Hold a grown-up's hand. Stop at the edge and look left and right. Cross when no cars are coming."]),
    (["How do I tie my shoes?", "Can you teach me to tie my shoes?"],
     ["Make two loops with the laces. Cross them over and pull one loop through the hole. Then pull both loops tight."]),
    (["It is raining. What can I do?", "It is raining and I can't go outside."],
     ["You can play inside. You could build a fort, read a book, or draw a picture."]),
    (["How can I stay healthy?", "How do I stay healthy?"],
     ["Eat fruits and vegetables, drink water, play outside, and get lots of sleep."]),
    (["How do I grow a plant?", "How can I grow a flower?"],
     ["Put a seed in a pot of dirt. Give it water and put it in the sun. Wait, and it will start to grow."]),
    (["I can't draw well.", "I am bad at drawing."],
     ["That is okay. Everyone gets better with practice. Keep drawing and have fun!"]),
    (["This is too hard.", "I can't do it."],
     ["Take a deep breath and try again, one step at a time. You can also ask for help."]),
    (["I am scared about my first day at school.", "I am worried about school."],
     ["That is a normal feeling. Your teacher will help you, and you can make new friends."]),
    (["I made a mistake.", "I did something wrong."],
     ["That is okay. Everyone makes mistakes. We learn from them."]),
    (["How do I clean my room?", "How should I tidy my room?"],
     ["Put your toys back in their boxes. Put your clothes away. Then make your bed."]),
    (["A stranger asked me to go with them.", "Should I go with a stranger?"],
     ["Do not go with them. Go to a grown-up you trust right away and tell them."]),
    (["What should I do if there is a fire?", "What do I do if I see a fire?"],
     ["Get out fast and stay outside. Tell a grown-up right away."]),
    (["I had a bad dream.", "I had a scary dream."],
     ["I am sorry. Bad dreams are not real. You can hug your teddy bear or tell a grown-up."]),
    (["I miss my mom.", "I miss my grandma."],
     ["It is hard to miss someone you love. Maybe you can draw them a picture."]),
    (["My brother took my toy.", "My sister took my ball."],
     ["Ask nicely to have it back. If that does not work, ask a grown-up to help."]),
    (["How can I help at home?", "What chores can I do?"],
     ["You can set the table, put away your toys, and help feed the pet."]),
    (["How can I be kind?", "How do I be a good friend?"],
     ["Say nice words, share your toys, and help people when they need it."]),
    (["I am so excited!", "I feel excited."],
     ["That is great! What are you excited about?"]),
    (["I learned to ride my bike!", "I can ride my bike now!"],
     ["Wow, well done! You must be so proud."]),
    (["How can I get better at reading?", "How do I learn to read better?"],
     ["Read a little every day. Ask a grown-up to read with you. Sound out new words slowly."]),
    (["I have a cold.", "I keep sneezing."],
     ["Rest and drink water. Cover your mouth when you sneeze or cough, and wash your hands."]),
    (["What should I do in the morning?", "What do I do when I wake up?"],
     ["Get dressed, eat breakfast, and brush your teeth."]),
    (["I want to be strong.", "How can I get strong?"],
     ["Play outside, run and jump, eat good food, and get lots of sleep."]),
    (["My pet fish died.", "My pet died."],
     ["I am so sorry. It is okay to feel sad. You can talk about your pet with someone you love."]),
    (["I don't like my food.", "I don't want to eat my vegetables."],
     ["Try a small bite. Vegetables help you grow big and strong."]),
    (["Someone was mean to me.", "A kid at school was mean to me."],
     ["I am sorry that happened. Tell a grown-up you trust, like your teacher or your mom or dad."]),
]


def gen_advice():
    qs, ans = pick(ADVICE)
    u = pick(qs)
    if chance(0.1) and u.endswith(".") and u.startswith(("I am", "I feel", "I can't", "I have")):
        u = u + pick([" What should I do?", " Can you help me?"])
    return u, pick(ans)


# ================================================================ assembly

GEN = {
    "repeat": gen_repeat,
    "counting": gen_counting,
    "arithmetic": gen_arithmetic,
    "opposites": gen_opposites,
    "animals_colors": gen_animals,
    "listing": gen_listing,
    "sentence": gen_sentence,
    "yes_no": gen_yesno,
    "compare": gen_compare,
    "sequence": gen_sequence,
    "answer_format": gen_format,
    "define": gen_define,
    "word_tasks": gen_wordtask,
    "identity_manners": gen_identity,
    "advice_feelings": gen_advice,
}
WEIGHTS = {
    "repeat": 7, "counting": 7, "arithmetic": 8, "opposites": 6, "animals_colors": 8,
    "listing": 7, "sentence": 7, "yes_no": 8, "compare": 6, "sequence": 7, "answer_format": 6,
    "define": 7, "word_tasks": 7, "identity_manners": 2, "advice_feelings": 6,
}
TYPES = list(GEN)
MULTI_P = 0.35


def pick_type(exclude=None):
    ts = [t for t in TYPES if t != exclude]
    return rng.choices(ts, weights=[WEIGHTS[t] for t in ts])[0]


def noise_user(u):
    if chance(0.07):
        u = u.lower()
    if u and u[-1] in ".?!" and chance(0.12):
        u = u[:-1]
    return u


_BAD_A = re.compile(r"(?:\ba|(?:^|[.!?] )A) ([aeiouAEIOU]\w*)")
_BAD_AN = re.compile(r"\b[aA]n ([^aeiouAEIOU\W\d]\w*)")


def validate(text, role):
    assert text and text.isascii(), (role, text)
    assert "  " not in text and " ." not in text and " ," not in text, (role, text)
    if role == "assistant":
        assert " ?" not in text, (role, text)
    assert text == text.strip(), (role, text)
    for m in _BAD_A.finditer(text):
        nxt = m.group(1)
        if m.group(0).lstrip(".!? ").startswith("A") and (len(nxt) == 1 or nxt in ("and", "is", "or")):
            continue  # the letter A, e.g. "A and B."
        assert nxt.lower().startswith(_A_EXC), (role, text)
    for m in _BAD_AN.finditer(text):
        assert m.group(1).lower().startswith(_AN_EXC), (role, text)
    if role == "assistant":
        assert text[-1] in ".!?", (role, text)
        assert text[0].isupper() or text[0].isdigit() or text[0] == '"', (role, text)
        assert not re.search(r"[.!?] [a-z]", text), (role, text)


def make_conversation():
    convo = []  # (type, user, assistant)
    if chance(MULTI_P):
        n = pick([2, 2, 3, 3, 4])
        opener = chance(0.25)
        closer = chance(0.2)
        n_tasks = n - int(opener) - int(closer)
        if n_tasks < 1:
            closer = False
            n_tasks = n - int(opener)
        if opener:
            convo.append(("identity_manners",) + gen_greeting())
        last = None
        for i in range(n_tasks):
            if (i > 0 and chance(0.06) and convo
                    and convo[-1][0] not in ("identity_manners", "repeat")):
                convo.append(("repeat",) + say_again(convo[-1][2]))
                last = "repeat"
                continue
            t = pick_type(exclude=last)
            if t == "identity_manners":
                u, a = gen_identity(mid=True)
            else:
                u, a = GEN[t]()
            convo.append((t, u, a))
            last = t
        if closer:
            convo.append(("identity_manners",) + gen_closer())
    else:
        t = pick_type()
        convo.append((t,) + GEN[t]())
    out = []
    for t, u, a in convo:
        validate(u, "user")
        validate(a, "assistant")
        out.append((t, noise_user(u), a))
    return out


PHRASES = []
SENTENCES = {}
SENT_WORDS = []


def build_data():
    global PHRASES, SENTENCES, SENT_WORDS
    PHRASES = _build_phrases()
    SENTENCES = _build_sentences()
    SENT_WORDS = sorted(SENTENCES)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--n", type=int, default=250000, help="number of conversations")
    ap.add_argument("--seed", type=int, default=0, help="random seed")
    ap.add_argument("--out", default=os.path.join(here, "data", "raw", "synth", "instructions.jsonl"))
    ap.add_argument("--samples", type=int, default=25, help="random samples to print")
    args = ap.parse_args()

    rng.seed(args.seed)
    build_data()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    type_counts = collections.Counter()
    distinct = set()
    n_multi = 0
    n_exchanges = 0
    convos = []
    with open(args.out, "w", encoding="ascii", newline="\n") as f:
        for _ in range(args.n):
            conv = make_conversation()
            if len(conv) > 1:
                n_multi += 1
            msgs = []
            for t, u, a in conv:
                type_counts[t] += 1
                distinct.add((u, a))
                n_exchanges += 1
                msgs.append({"role": "user", "content": u})
                msgs.append({"role": "assistant", "content": a})
            f.write(json.dumps({"messages": msgs}, ensure_ascii=True) + "\n")
            convos.append(msgs)

    size = os.path.getsize(args.out)
    print("wrote {:,} conversations to {}".format(args.n, args.out))
    print("file size: {:,} bytes ({:.1f} MB)".format(size, size / 1e6))
    print("multi-turn conversations: {:,} ({:.1%})".format(n_multi, n_multi / max(1, args.n)))
    print("exchanges: {:,}  distinct (user, assistant) exchanges: {:,}".format(n_exchanges, len(distinct)))
    print("share of exchanges per task type:")
    for t in TYPES:
        print("  {:<18} {:>8,}  {:5.1%}".format(t, type_counts[t], type_counts[t] / max(1, n_exchanges)))

    srng = random.Random(args.seed + 12345)
    print("\n{} random samples:".format(args.samples))
    for msgs in srng.sample(convos, min(args.samples, len(convos))):
        print("-" * 60)
        for m in msgs:
            print(("U: " if m["role"] == "user" else "A: ") + m["content"])


if __name__ == "__main__":
    main()

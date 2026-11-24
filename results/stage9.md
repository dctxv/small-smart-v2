# Stage 9 - a test the models were not trained to pass

## What was done, in order

1. 150 prompts were written by hand (`make_heldout.py`), with an automatic check for each one.
   Every check was tested against a hand-written good reply and a bad reply. No model was run.
2. The set was frozen as `data/heldout.json`, 150 items,
   SHA-256 `77aa0feb50453863b93cbaef08b76998493b0c78049ecde3978c0e6b5c0bbda2` (saved in `data/heldout.sha256`).
   The scorer refuses to run if the file does not match. It was never trained on.
3. Leak check against all 4.4 million user messages in the practice data (`results/heldout/leak_check.json`).
4. The rule for leaked items was fixed, then the five models were scored (`heldout.py`).
   Each model was scored once, with steady (greedy) replies and the full tool loop, free output.

The five models: twin (old baseline), control (twin + new practice data), small-smart 8-bit
(`final/small-smart-8bit.bin`), small-smart 4-bit (`final/small-smart-4bit.bin`), rival 8-bit (`runs/r8b/q8.bin`).

## Leak check

11 of the 150 questions are in the practice data word for word, and 4 more are nearly the same
(0.85 or more of their words shared). These 15 are flagged, not removed:
B01, B18, B21, C20, D02, D10, D11, D12, D13, E01, E02, E05, E06, E09, E15.

Most are short plain questions ("When is the dentist?", "What is the alarm code?") that the practice
data uses as follow-up questions after a pasted notes block. Six are world-knowledge questions.
Scores are given on all items and again without the flagged ones.

## Results (items passed)

| part | items | twin | control | small-smart 8-bit | small-smart 4-bit | rival 8-bit |
|---|---|---|---|---|---|---|
| **A to D, headline** | 130 | 26 | 45 | 50 | 49 | 47 |
| **A to D after AI grading** (see the end of the hand-grading section) | 130 | 25 | 45 | 49 | 48 | 45 |
| as a percentage | | 20% | 35% | 38% | 38% | 36% |
| **A to D, without flagged items** | 121 | 24 | 41 | 47 | 44 | 45 |
| - the same after AI grading | 121 | 23 | 41 | 46 | 43 | 43 |
| A: five skills, new wording | 60 | 6 | 26 | 33 | 31 | 29 |
| - instruction | 12 | 4 | 5 | 8 | 9 | 8 |
| - arithmetic | 12 | 0 | 3 | 4 | 2 | 3 |
| - format | 12 | 1 | 4 | 6 | 3 | 5 |
| - notes (pasted, new layouts) | 12 | 1 | 5 | 6 | 7 | 5 |
| - tool call | 12 | 0 | 9 | 9 | 10 | 8 |
| B: notes questions without the word "notes" | 25 | 4 | 5 | 6 | 6 | 3 |
| - fact only in the notes store | 15 | 0 | 0 | 0 | 0 | 0 |
| - fact pasted in an unfamiliar layout | 10 | 4 | 5 | 6 | 6 | 3 |
| C: two skills in one request | 25 | 1 | 1 | 0 | 0 | 0 |
| D: questions with no answer | 20 | 15 | 13 | 11 | 12 | 15 |
| - personal fact, no notes | 8 | 8 | 5 | 6 | 6 | 7 |
| - not in the notes | 6 | 2 | 2 | 2 | 3 | 2 |
| - nobody can know | 6 | 5 | 6 | 3 | 3 | 6 |
| **E: world knowledge (apart)** | 20 | 5 | 11 | 11 | 11 | 12 |
| E without flagged items | 14 | 2 | 7 | 7 | 7 | 8 |

Searches of the notes store on the 15 part B store questions: 0 for every model.

Peak GPU memory while scoring: 255 MiB (twin, control, rival), 496 MiB (both small-smart files).

For comparison, the same models on the dev set, which follows the practice data's templates
(fixed checker, see below): twin 26%, control 96%, small-smart 8-bit 98%, 4-bit 99%, rival 97%.

## What this shows

- **The dev set and scoreboard numbers measure fit to the practice templates.** On prompts that
  break those templates, the trained models fall from about 97% to about 37%.
- **The practice data still helped off-template**, about doubling the twin's score (26 to 45-50).
- **The four trained models cannot be told apart here.** 45, 47, 49, 50 of 130 is a spread of
  5 items; the sampling error on 130 items is about 4 items either way, and each model was scored once.
  The order (8-bit, 4-bit, rival, control) matches the order by loss, but this test does not prove it.
- **No model ever searches the notes unless the question says "notes".** 0 of 15, with 0 searches.
  They make up an answer instead ("The wifi password is a word that means to change or do something").
- **Two requests in one message fail almost completely** (0 or 1 of 25). The usual pattern is that
  one half is done and the other ignored: "348 times 27 is 9396." when asked for only the number.
- **Arithmetic is template-bound.** "What is 14 + 23?" works; "What do you get when you put 14 and
  23 together?" gives 27 or 29. Small-number sums in new wordings: 2 to 4 of 12.
- **Tool calls for big sums and "notes" requests held up best** (8 to 10 of 12 in new wordings).
- **Admitting ignorance got worse with training on the practice data.** The twin says "I don't know"
  to most things (15 of 20). Both small-smart files make up more answers (11 and 12 of 20), for example
  "You left your glasses in the kitchen." The rival (15) did not show this; one run each, so this is weak.
- **World knowledge is about half right** on easy questions, and wrong answers are stated with
  confidence ("The capital city of France is Tokyo", "There are seven days in a year").

## Checker notes found after scoring (the frozen file was not changed)

- A30 ("Write the sentence I like tea inside quote marks"): the check passes
  `"I like tea inside quote marks. It's hot and cozy."` It should not. Counted as it stands.
- E12 (milk from cows) and E04: the world-knowledge check only looks for the key word, so a rambling
  reply that contains "milk" passes. Part E is lenient for this reason.
- D12, 4-bit: "I don't know. It's a big one with a big party." passes as an admission. Borderline.
- I wrote the practice templates as well as this test. The wordings are new to the models but not
  independent of me.

## This set is now used up for the next version

The plan for a second version is built around what this test exposed (new wordings, notes questions
without the word "notes", two skills in one request). That makes this set "seen" for that work.
It stays valid for the five models above. Any later model needs a fresh frozen set, written before
its practice data.

## For you to grade by hand

`results/heldout/human_sheet.md` holds:
- Part 1: five items where the automatic check only sees the form (A05, A06, A07, A09, C22),
  with all five models' replies. These count in the table above by their form check.
- Part 2: every "no answer" question where a model did not use "I do not know" wording, so you can
  confirm they are made-up answers.

Every reply from every model is saved in `results/heldout/heldout_<name>.json`.

### Graded by AI, not by a person

Nobody graded the sheet by hand. Some replies need a judgement of sense that a program cannot make. Those were graded by AI against a written rubric (`results/ai_grading/RUBRIC.md`), in two separate passes that did not see each other, and a reply counts as wrong where the passes disagreed. **They were not graded by a human.**

- 17 items, 59 different replies (the two v2 models' replies were graded in the same batch), graded without model names. The passes agreed on all 59.
- Part 1: only replies that had passed the form check were graded. Six were marked wrong on sense, for example "The last word is blue" as a
  description of the sea, and "Maybe clouds are fun to see and hear". A09 had no passing reply, so nothing changed there.
- Part 2: none of the replies was an honest "I do not know". All stay wrong.
- Headline after AI grading: twin 25, control 45, small-smart 8-bit 49, small-smart 4-bit 48, rival 45 of 130.
  The four trained models still cannot be told apart.

The rubric, both passes and the merged grades are in `results/ai_grading/`.

## Dev set: three checker faults fixed

Fixed in `rescore_dev.py` (the saved replies were re-scored; no model was run). Results in `results/dev_v2/`.

- "What is the opposite of old?" now accepts "young" as well as "new".
- "Multiply 3 by 1." and "What is 0 x 4?": the answer is also a number in the question, and the old
  rule threw away the question's numbers before looking for the answer, so no reply could pass.
  New rule: the answer must be in the reply, and the reply must hold no number that is neither the
  answer nor in the question.

| model | dev before | dev after | items that changed |
|---|---|---|---|
| twin | 94 | 94 | none |
| control | 346 | 348 | "3." and "0." for the two sums |
| small-smart 8-bit | 353 | 356 | "Young.", "3.", "0 x 4 = 0." |
| small-smart 4-bit | 355 | 357 | "3 x 1 = 3.", "0." |
| rival 8-bit | 350 | 352 | "3 x 1 = 3.", "0 x 4 = 0." |

All changes are fail to pass. No ranking changed. The scoreboard keeps its old checker; the new rule
would not change any scoreboard total (checked on the saved replies).

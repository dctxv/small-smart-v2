# Stage 10 - v2: one round of data aimed at what the held-out test exposed

Question: does one more round of practice data, aimed at the three weakest parts of the first
held-out test, make a better assistant on a test it has never seen?

Answer: **yes, by the rule set beforehand.** On the fresh held-out test the v2 model passes
74 of 140 against 44 for v1 (30 more; the rule asked for 8). After AI grading of the judgement
items it is 69 against 42 (27 more). Single runs.

## What changed

Only the chat-phase data. The model, the recipe, the story phase and the number of steps are
the same as v1. Each v2 model starts from the saved story-phase checkpoint of its v1 twin and
redoes the 4,000 chat steps.

New practice data, 201,047 conversations (`gen_v2.py`):

| family | conversations | what it is |
|---|---|---|
| two skills in one request | 66,008 scripted + 3,156 reworded | 24 scripted pairings, such as a sum plus "answer with only the number" |
| sums in new wordings, new numbers | 54,899 | wordings written by the teacher, numbers filled in by script |
| notes shown in the request, odd layouts | 40,558 + 906 reworded | notes without the heading "Notes:", in sentences, with other headings |
| notes questions without the word "notes" | 27,149 + 1,769 reworded | the fact is only in the notes store, so the model must search |
| other rewordings (rules, calculator, word problems, notes tool) | 6,588 | teacher rewordings of scripted requests |
| questions nobody can answer | 14 | almost all were removed as duplicates |

- The teacher (qwen3:8b) reworded 2,403 scripted requests six ways each: 14,416 rewordings,
  12,594 kept after checks (a needed word missing 842, numbers changed 463, the teacher's own
  answer wrong 317, same as the original 160, other 40). It also wrote 963 short notes with a
  question each; 774 were kept.
- The answers are always scripted. The teacher supplies wording only.
- 300,000 conversations were asked for. 80,867 were duplicates and were removed.
- **Leak rule:** 18,086 conversations were deleted because their question matched a question
  in either held-out test, the scoreboard or the dev set.

Chat mix (`results/mixes/v2.json`): the v2 data takes 17%, taken from the older job practice
data (35% down to 18%). Everything else is unchanged.

## The fresh test

The first held-out test shaped this round, so it no longer counts. A second one
(`data/heldout2.json`, 160 items, sha256 `b3f1336a...3307`) was written by a separate session
before any v2 data existed. I did not read it until all scoring was done.

| part | items | twin | control | ss 8-bit | ss 4-bit | rival | **control v2** | **ss v2 4-bit** |
|---|---|---|---|---|---|---|---|---|
| **Headline, A to D** | 140 | 27 | 40 | 48 | 44 | 50 | **63** | **74** |
| **Headline after AI grading** (see below) | 140 | 24 | 35 | 46 | 42 | 46 | **59** | **69** |
| A to D without items found in practice data | 127 | 26 | 33 | 39 | 35 | 41 | 53 | 64 |
| - the same after AI grading | 127 | 23 | 28 | 37 | 33 | 37 | 49 | 59 |
| A: five skills, new wording | 50 | 7 | 20 | 29 | 26 | 27 | 23 | 29 |
| - instruction | 10 | 4 | 4 | 7 | 7 | 6 | 5 | 6 |
| - arithmetic | 10 | 0 | 4 | 5 | 5 | 5 | 5 | 6 |
| - format | 10 | 1 | 3 | 4 | 3 | 4 | 4 | 5 |
| - notes | 10 | 2 | 2 | 6 | 4 | 4 | 1 | 3 |
| - tool call | 10 | 0 | 7 | 7 | 7 | 8 | 8 | 9 |
| B: notes questions without the word "notes" | 30 | 1 | 1 | 2 | 1 | 3 | 13 | 14 |
| - fact only in the notes store | 20 | 0 | 0 | 1 | 0 | 1 | 11 | 12 |
| - notes shown in the request | 10 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |
| C: two skills in one request | 30 | 0 | 2 | 1 | 1 | 1 | 6 | 6 |
| - after AI grading | 30 | 0 | 1 | 1 | 1 | 1 | 6 | 5 |
| D: questions with no answer | 30 | 19 | 17 | 16 | 16 | 19 | 21 | 25 |
| - after AI grading | 30 | 16 | 13 | 14 | 14 | 15 | 17 | 21 |
| E: world knowledge (reported apart) | 20 | 16 | 18 | 17 | 16 | 17 | 17 | 16 |
| searched the notes, of the 20 store items | 20 | 0 | 1 | 1 | 0 | 1 | 18 | 18 |

Chance error on 140 items is about 6 items for one model and about 8 for a difference.
Peak GPU memory while scoring: 256 MiB (12-layer models), 498 MiB (25-layer models).

## The old tests

| | control | ss 4-bit (v1) | control v2 | ss v2 4-bit |
|---|---|---|---|---|
| story loss | 1.233 | 1.153 | 1.233 | 1.154 |
| assistant chat loss | 0.892 | 0.837 | 0.890 | 0.837 |
| scoreboard /100 | 90 | 92 | 91 | 92 |
| dev set /362 (fixed checker) | 348 | 357 | 337 | 348 |
| tool test, free | 92.3% | 91.5% | 96.2% | 96.2% |
| - calculator, new wording | 83% | 80% | 90% | 87% |
| - notes, new wording | 75% | 75% | 90% | 95% |
| first held-out test /130 (now seen) | 45 | 49 | 74 | 81 |
| - after AI grading | 45 | 48 | 74 | 80 |
| file | 83.9 MB | 41.7 MB | 83.9 MB | 41.7 MB |
| chat phase training time | 25 min | 69 min | 25 min | about 100 min (see below) |
| peak GPU memory in training | 9,474 MiB | 5,997 MiB | 9,474 MiB | 5,997 MiB |

The scores of the 4-bit models come from the exported files. The first held-out test is
"seen": the two-skill practice copies its shapes, so 81 of 130 flatters v2 and is not evidence.

## Decision

Rule, set beforehand: v2 counts as better only if it beats v1 on the fresh test by 8 or more
items. The rule was written for 130 headline items; the fresh test has 140, which makes 8 a
slightly easier bar (5.7% instead of 6.2%). It does not matter here.

- small-smart v2 4-bit against small-smart v1 4-bit: 74 against 44, **30 more**. After AI grading: 69 against 42, **27 more**.
- Against the best v1 model on this test (the rival, 50): 24 more.
- Control v2 against control: 63 against 40, 23 more.

**v2 is better, and becomes the main model.** The files are in `final_v2/`. Nothing in
`final/` was changed.

## Where the gain came from, and where it did not

- **Searching the notes without being told (B, store items): 0 to 12 of 20.** v2 searched on
  18 of 20. "What's the wifi password again?" used to get "The wifi password is a measure of
  how much or how much is the same." It now searches for "wifi" and answers "Wifi password is
  sunny42." Six of the 18 searches still ended in a wrong answer (a wrong search word, or the wrong fact taken from the note).
- **Questions with no answer (D): 16 to 25 of 30.** v2 now searches the notes for personal
  questions ("What did I eat for breakfast this morning?") and reports that nothing was found.
  It did not search on any of the 20 world knowledge questions.
- **Two skills in one request (C): 1 to 6 of 30.** Better, and still mostly failing. Sum plus
  format works ("What is 9 plus 6? Answer with only the number" now gets "15"). Anything that
  needs a fact from notes plus a second rule still fails.
- **New wording of the five skills (A): 26 to 29 of 50.** No clear change. Rewording by the
  teacher did not move this part. Notes shown inside the request also did not move (1 to 2 of 10).

## Losses and failures, stated plainly

- **The dev set went down: 357 to 348 for the 4-bit model, 348 to 337 for the control.**
  Capital-letter replies fell from 85% to 60% and one-word replies from 90% to 80%. The v2 data
  took half of the old job practice's share of the mix, and those families paid for it.
- The scoreboard did not move (92 and 92).
- Every model is a single run. The control gained 23 and the 25-layer model 30, so once again
  the data did most of the work.
- 13 of the 140 headline items (and 14 of the 20 world knowledge items) have the same or
  nearly the same question somewhere in the practice data, mostly in the older v1 data. The
  table gives the score without them: 64 against 35 of 127, the same picture. Three of them
  are near matches in the v2 data that the deletion rule did not catch, because it matched
  whole question lines only (for example "What time does my bus home leave?" against "What
  time does my bus leave?").
- The v2 4-bit training run was paused once and for a while shared the GPU with another job.
  It ran about 60 minutes shared, was stopped, and resumed from its step 17,500 checkpoint for
  42 more minutes. The result does not depend on this, but the time is not comparable to v1.
  One log file (`logs/v2_q4.log`) was overwritten on resume; `runs/v2_q4/log.jsonl` is complete.
- The automatic checks have the same leniency as before. The items marked for hand grading were
  graded by AI, not by a person (next section).
- The fresh test is now seen too. A v3 designed from these results needs a third test.

## AI grading of the judgement items

Some replies need a judgement of sense that a program cannot make. Those were graded by AI against a written rubric (`results/ai_grading/RUBRIC.md`), in two separate passes that did not see each other, and a reply counts as wrong where the passes disagreed. **They were not graded by a human.**

- The sheet marks 10 items where the automatic check only sees the form. One of them (A07) had no reply that passed the form check, so 9 were graded,
  and only the replies that had passed. A reply that failed on form stays wrong.
- 13 no-answer questions (D01 to D20) had replies with no "I do not know" wording. These were graded too, as on the first test. None was marked right.
- Failures a program can check (a wrong number, a tool call where none was wanted, a missing required word) were not regraded.
- 84 different replies, graded without model names. The passes agreed on 83. The one disagreement (ss 4-bit on D21) counts as wrong.
- Every change is a loss. Items lost: twin 3, control 5, ss 8-bit 2, ss 4-bit 2, rival 4, control v2 4, ss v2 4-bit 5.
  Most are in part D's ordinary chat items: a story about a bus with no rain in it (D22), a nonsense reason for locking the door (D25),
  two sentences that are not about writing to grandma (D30). v2 also lost C05 ("1. POT / 2. PAN / 3. POT" repeats an entry).
- The decision does not change: 69 against 42 is 27 more, and the rule asked for 8.

The rubric, both passes and the merged grades are in `results/ai_grading/` (`grade_ai.py` builds them).

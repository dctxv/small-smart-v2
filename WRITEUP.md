# small-smart: what makes a tiny assistant better, and what does not

A small language model was trained from nothing on one home PC (RTX 5060 Ti, 16 GB) to be a
friendly helper in simple English: chat, short explanations, sums, answering from notes, and
calling a calculator or a notes search. This is an honest account of what worked.

## The short version

1. **Practice data built in rounds did most of the work.** The same small model, with the same
   shape and the same training settings, went from 22 to 90 out of 100 on our scoreboard when the
   only change was the chat data it practised on.
2. **Low-bit training then halved the file.** A model with twice the parameters, stored at 4 bits
   per weight, fits in 42 MB and scores the same as the 83 MB version.
3. **A test written afterwards shows the limit.** On prompts that do not follow the practice
   data's patterns, every model passes only about 37%. The big scores above measure how well the
   practice worked, not general ability.
4. **One more round of data, aimed at that test's findings, raised the score on a second fresh
   test from 44 to 74 of 140 (42 to 69 after AI grading of the judgement items).** The gap to trained wording narrowed. It did not close.

## The starting point

The baseline, called the twin, is a plain transformer: 12 layers, 512 wide, 41.9 million
parameters, an 84 MB file. It was trained for 16,000 steps on simple children's stories and
4,000 steps on chat data. It writes fluent stories and fails nearly every instruction.

Every model here keeps that budget: the same number of steps, the same 8,192-word-piece
vocabulary, the same 512-token context.

## How ideas were tested

Ideas were tried on a small pilot model (6.8 million parameters), three runs per idea with
different random seeds. A change in loss under 0.015 counts as no change, because that is about
how much runs differ by chance. Full-size models were trained once each, so every full-size
number below is a single run.

Three tests were used:

- **Scoreboard:** 100 fixed prompts with automatic checks, 20 each for instructions, arithmetic,
  formats, notes and tool calls.
- **Dev set:** 362 prompts in the same families as the practice data, kept out of training.
- **Tool test:** 130 requests run through the full loop: the model writes a call, the tool runs,
  the model answers.

Loss is how surprised the model is by held-out text. Lower is better.

## The recipe

- **Shape:** 25 layers, 512 wide, 82.8 million parameters.
- **Low-bit weights from the start.** The weights are trained on a coarse grid (8 bits each), so
  the saved file is exactly the model that was tested. A 4-bit version was made by retraining
  only the chat phase.
- **Optimiser:** Muon for the weight matrices, AdamW for the rest.
- **One model change:** value residual, a shortcut that lets later layers reuse the first
  layer's values.
- **Chat phase:** the loss counts only the assistant's words.
- **Data:** 35% generated practice for the helper's jobs (one million conversations), 20%
  synthetic instructions, the rest simple chat, story requests, stories, and 2% written by a
  larger teacher model.

### Practice data in rounds

This was the step that mattered. A script writes practice conversations for each job: follow a
rule ("answer in one word"), do a sum, use a format, answer from pasted notes, call a tool. After
training, the dev set shows which families still fail. More varied practice is written for those
families, and the model is trained again. Two rounds took the pilot's scoreboard from 15.7 to
about 82.

## What helped

| change | effect | where |
|---|---|---|
| Job practice data, in rounds | scoreboard 15.7 to about 82 | pilot |
| Muon optimiser | story loss down 0.068 | pilot |
| Value residual | story loss down 0.022 | pilot |
| Loss on assistant words only | prompts passed 11 to 14 | pilot |
| 8-bit training | no cost (+0.001) | pilot |
| 4 bits with more parameters, same file size | loss down 0.099 | pilot |
| More request wordings in the tool data | larger gain than grammar-forced output | pilot |

## What was dropped

- **Weight averaging:** no gain on prompts.
- **QK-norm, ReLU squared, a deeper and thinner shape:** no gain.
- **Lookup tables (word-pair hashing, value embeddings):** a small gain, but spending the same
  parameters on width gained more.
- **Predicting several tokens at once:** slightly worse.
- **A simplified normalised transformer:** clearly worse. It was not tuned, so this rejects that
  version, not the idea.
- **Forcing valid tool calls with a grammar:** no measurable gain (87.4% against 87.7%).
- **Teacher-written data:** no scoreboard gain, and nothing checks whether its facts are true.

## Results

Five models. The control is the twin with only the new chat data. The rival has the twin's
shape with the full new recipe at 8 bits, which makes it the same file size as the 4-bit model.

| | twin | control | small-smart 8-bit | small-smart 4-bit | rival 8-bit |
|---|---|---|---|---|---|
| layers x width | 12 x 512 | 12 x 512 | 25 x 512 | 25 x 512 | 12 x 512 |
| parameters | 41.9M | 41.9M | 82.8M | 82.8M | 41.9M |
| file size | 83.9 MB | 83.9 MB | 83.2 MB | 41.7 MB | 42.1 MB |
| story loss | 1.212 | 1.233 | 1.132 | 1.153 | 1.196 |
| assistant chat loss | 0.853 | 0.892 | 0.844 | 0.837 | 0.874 |
| scoreboard /100 | 22 | 90 | 93 | 92 | 88 |
| dev set /362 (fixed checker) | 94 | 348 | 356 | 357 | 352 |
| tool test | 0.0% | 92.3% | 90.0% | 91.5% | 88.5% |
| peak GPU memory in training | not logged | 9,474 MiB | 5,681 MiB | 5,997 MiB | 4,027 MiB |

Reading it:

- **Data:** twin to control is 22 to 90. Nothing else changed.
- **Model and recipe:** the 25-layer model is clearly better on loss (0.10 on stories against the
  control), but only 3 points better on the scoreboard, which is about the spread between seeds.
  The prompt tests are near their ceiling and cannot show the difference.
- **Bits against parameters:** at about 42 MB, 82.8M parameters at 4 bits give a better
  language model than 41.9M parameters at 8 bits: 0.043 lower on story loss and 0.037 lower on
  chat loss, both well outside the yardstick. They do not give a better assistant. On the
  scoreboard, dev set, tool test and held-out test the two are tied within noise. One run
  each. The 4-bit model's story phase was trained at 8 bits, so this is not a from-scratch
  4-bit comparison.

### The held-out test

After all training was finished, 150 new prompts were written by hand, frozen with a SHA-256
hash, and only then run. They avoid the practice data's wordings.

| part | items | twin | control | 8-bit | 4-bit | rival |
|---|---|---|---|---|---|---|
| Headline (all parts below except world knowledge) | 130 | 26 | 45 | 50 | 49 | 47 |
| Headline after AI grading (see below) | 130 | 25 | 45 | 49 | 48 | 45 |
| Five skills, new wording | 60 | 6 | 26 | 33 | 31 | 29 |
| Notes questions without the word "notes" | 25 | 4 | 5 | 6 | 6 | 3 |
| Two skills in one request | 25 | 1 | 1 | 0 | 0 | 0 |
| Questions with no answer | 20 | 15 | 13 | 11 | 12 | 15 |
| World knowledge (reported apart) | 20 | 5 | 11 | 11 | 11 | 12 |

The practice data still doubles the twin's score, so some of it carries over. But the trained
models drop from about 97% on the dev set to about 37% here, and the four of them cannot be
told apart (a 5-item spread, with a chance error of about 4 items).

A check of the practice data found 11 of the 150 questions word for word and 4 more nearly so.
They were left in and flagged. Without them the headline is 24, 41, 47, 44, 45 of 121.

**AI grading.** Some replies need a judgement of sense that a program cannot make. Those were graded by AI against a written rubric (`results/ai_grading/RUBRIC.md`), in two separate passes that did not see each other, and a reply counts as wrong where the passes disagreed. **They were not graded by a human.** On this test that covers 17 items (59 different replies): five where the automatic check only sees the form of the reply, and twelve no-answer questions where a model gave no "I do not know" wording. The two passes agreed on all 59. Six replies that had passed on form were marked wrong on sense, and no made-up answer was marked right, so the headline becomes 25, 45, 49, 48, 45 of 130. The picture does not change. The grades are in `results/ai_grading/grades_heldout.md`.

## v2: one more round of data

The held-out test above pointed at three weak spots: new wording, notes questions that do not
say "notes", and two skills in one request. v2 is one round of practice data aimed at them.
Nothing else changed: same model, same recipe, same steps. Only the chat phase was retrained.

**What changed in the data.** 201,047 new practice conversations took 17% of the chat mix,
taken from the older job practice (35% down to 18%):

- The teacher model reworded 2,403 scripted requests six ways each (12,594 of 14,416 kept).
  Answers stay scripted. For sums, the new wordings were refilled with new numbers.
- Notes questions without the word "notes", where the fact is only in the notes store, so the
  model has to decide to search.
- Notes shown inside the request in odd layouts, with no "Notes:" heading.
- Two skills in one request, in 24 scripted pairings.

**A fresh test.** The first held-out test shaped this round, so it no longer counts. A second
one (160 items, 140 in the headline) was written by a separate session before any v2 data
existed, and frozen with a hash. Any practice conversation whose question matched a test
question was deleted from the practice data: 18,086 were.

| part | items | twin | control | 8-bit | 4-bit | rival | control v2 | 4-bit v2 |
|---|---|---|---|---|---|---|---|---|
| Headline | 140 | 27 | 40 | 48 | 44 | 50 | 63 | **74** |
| Headline after AI grading (see below) | 140 | 24 | 35 | 46 | 42 | 46 | 59 | **69** |
| Five skills, new wording | 50 | 7 | 20 | 29 | 26 | 27 | 23 | 29 |
| Notes questions without the word "notes" | 30 | 1 | 1 | 2 | 1 | 3 | 13 | 14 |
| Two skills in one request | 30 | 0 | 2 | 1 | 1 | 1 | 6 | 6 |
| Questions with no answer | 30 | 19 | 17 | 16 | 16 | 19 | 21 | 25 |
| World knowledge (reported apart) | 20 | 16 | 18 | 17 | 16 | 17 | 17 | 16 |

On the older tests the v2 4-bit model scores 92 on the scoreboard (v1: 92), 348 of 362 on the
dev set (v1: 357) and 96.2% on the tool test (v1: 91.5%). Each model is a single run.

**AI grading.** Some replies need a judgement of sense that a program cannot make. Those were graded by AI against a written rubric (`results/ai_grading/RUBRIC.md`), in two separate passes that did not see each other, and a reply counts as wrong where the passes disagreed. **They were not graded by a human.** On the fresh test that covers 22 items (84 different replies): nine where the automatic check only sees the form, and thirteen no-answer questions. The passes agreed on 83 of 84; the one disagreement counts as wrong. Every change is a loss: replies that passed on form and failed on sense, such as a story about a bus with no rain in it. No made-up answer was marked right. v2 loses 5 items (74 to 69) and v1 loses 2 (44 to 42). The grades are in `results/ai_grading/grades_heldout2.md`.

**The decision.** The rule was set before the run: v2 counts as better only if it beats v1 on
the fresh test by 8 or more items, about twice the chance error. It beats it by 30 (74
against 44), or by 27 after AI grading (69 against 42), so v2 is the main model. The reasons, and the limits:

- The gain is real and it is narrow. It comes from the model now searching its notes without
  being told (0 to 12 of 20, and it searched on 18 of 20) and from saying "I could not find
  that" instead of inventing an answer (16 to 25 of 30).
- Two skills in one request improved from 1 to 6 of 30. It still mostly fails.
- New wording of the five basic skills did not move (26 to 29 of 50, inside chance). Having a
  teacher reword requests was the part expected to help most, and it helped least.
- It cost something: the dev set fell by 9 items, mostly capital-letter and one-word replies,
  whose practice share was halved to make room.
- The control gained 23 items from the same data and the 25-layer model gained 30. Data did
  most of the work again.
- 13 of the 140 headline items have a matching or nearly matching question somewhere in the
  practice data, mostly the older data. Without them the score is 64 against 35 of 127
  (59 against 33 after AI grading).

The trained-wording against new-wording gap is still there: 96% on the dev set, 53% on the
fresh test (49% after AI grading). And the fresh test has now been used once. A v3 would need a third.

## Known weaknesses, with examples

These examples are from the v1 models. v2 fixes the first one in most cases and the others only in part.

- **It only searches notes when told to.** "Check my notes. When is the dentist?" works. "When
  is the dentist?" got "The dentist is at home with a special tool called a dentist." No model
  searched in any of 15 such questions.
- **Arithmetic depends on wording.** "What is 14 + 23?" is right. "What do you get when you put
  14 and 23 together?" got "14 plus 23 is 27."
- **Two requests at once fail.** Asked to work out 348 times 27 and reply with only the number,
  it replied "348 times 27 is 9396."
- **It makes things up.** "Where did I leave my glasses?" got "You left your glasses in the
  kitchen." The trained models do this more often than the twin, which mostly says it does not
  know.
- **Little world knowledge.** "The capital city of France is Tokyo." "There are seven days in a
  year."
- **No letter-level skill.** "eagle" in capitals came out as "ELLER".

## What this does not show

- That the model is useful as a general assistant. It is not.
- That the recipe beats the control in behaviour. The loss gap is real; the tests are too easy
  or too hard to show it.
- Anything about variation at full size. Each full-size model is one run with one seed.
- That 4 bits beat 8 bits in general, or that the 4-bit model is a better assistant than the
  8-bit rival. It has lower loss; its behaviour on every prompt test is a tie. One size, one
  shape, one run.
- That the held-out test is independent. The same author wrote the practice patterns and the
  test, and the automatic checks are lenient in a few places.

## How to run it

With PyTorch:

```
python chat.py final/small-smart-4bit.bin
python chat.py final/small-smart-4bit.bin --tools --notes final/example_notes.txt
```

Without PyTorch, using only numpy and the tokenizers package (about 40 MB installed):

```
python run_np.py final/small-smart-4bit.npz
```

On a 6-core desktop processor the numpy runner gives about 44 tokens per second in about
360 MiB of RAM. It has chat but not the tools. It gave the same replies as PyTorch on 6 of 6
test prompts.

## What would help next

Broader reading than stories, so the model knows more about the world. Practice data that mixes
skills far more (two skills at once is still at 6 of 30). A better way to get new wording than
asking a teacher to reword requests, which did not move the score. And a new test for each
round, written before the practice data, by someone else.

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

## Known weaknesses, with examples

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
skills and varies its wording far more. And tests written before the practice data, by someone
else.

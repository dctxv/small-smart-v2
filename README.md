# small-smart

A small friendly helper that speaks simple English, trained from nothing on one PC (Windows, RTX 5060 Ti 16 GB). It chats, gives short explanations, does sums, answers from a notes file, and can call a calculator and a notes search.

The goal was to beat the "twin", a plain 41.9M-parameter model from an earlier project, without making the file bigger.

**The main model is v2:** `small-smart-v2-4bit.bin`, 41.7 MB. v1 (the 8-bit and 4-bit files) is the earlier version. It is kept and documented here because most of the study was done on it.

## Read this first: 97% on trained wording, 37% on new wording

On prompts worded like its practice data, the model passes about 97% (dev set, 357 of 362). On 130 hand-written prompts that avoid those wordings, it passes about 37% (49 of 130, or 48 after AI grading). Those are v1 numbers. Both numbers are true. The first one says the practice worked. The second one is closer to what you get if you talk to it.

A second round of practice data (v2) was aimed at that gap and checked on a second, fresh test: 74 of 140 (53%) against 44 for v1, while the dev set stayed at 96%. After AI grading of the replies that need a judgement of sense it is 69 (49%) against 42. The gap is smaller. It is still large.

## Result

| model | file | scoreboard /100 | dev set /362 | tool test | story loss | held-out /130 |
|---|---|---|---|---|---|---|
| **small-smart v2 4-bit** (the main model) | 41.7 MB | 92 | 348 | 96.2% | 1.154 | 81 (seen, see below) |
| twin (the baseline) | 83.9 MB | 22 | 94 | 0% | 1.212 | 26 |
| control (twin + new practice data) | 83.9 MB | 90 | 348 | 92.3% | 1.233 | 45 |
| small-smart 8-bit (v1) | 83.2 MB | 93 | 356 | 90.0% | 1.132 | 50 |
| small-smart 4-bit (v1) | 41.7 MB | 92 | 357 | 91.5% | 1.153 | 49 |
| rival (twin shape, 8-bit) | 42.1 MB | 88 | 352 | 88.5% | 1.196 | 47 |

Fresh held-out test, written before the v2 data existed (headline, 140 items):

| | twin | control | 8-bit | 4-bit | rival | control v2 | **v2 4-bit** |
|---|---|---|---|---|---|---|---|
| automatic checks | 27 | 40 | 48 | 44 | 50 | 63 | **74** |
| after AI grading | 24 | 35 | 46 | 42 | 46 | 59 | **69** |

The first held-out test after AI grading: 25, 45, 49, 48, 45 of 130 for the five v1 models (26, 45, 50, 49, 47 by the automatic checks). Replies that need a judgement of sense were graded by AI against a written rubric, in two separate passes, with any disagreement counted as wrong. They were not graded by a human. See `results/ai_grading/`.

v2 is the main model. The rule set beforehand was a gain of 8 or more items on the fresh test; it gained 30 (27 after AI grading). It also lost 9 items on the dev set. The first held-out test shaped the v2 data, so v2's 81 on it is not evidence. Details in `results/stage10.md`.

The full story is in [WRITEUP.md](WRITEUP.md). The model card is [MODEL_CARD.md](MODEL_CARD.md).

The first three tests follow the patterns of the practice data. The held-out test does not: it was written by hand after training, frozen with a hash, and only then run. On it the trained models pass about 37%. Read the big numbers as "the practice worked", not as general ability.

Every full-size number is a single run. The scores for the two small-smart rows were measured on the real exported files, not on the training checkpoints.

- Same file size as the twin: 93 against 22.
- Half the file size: 92 against 22.

## The honest reading of that result

Most of the gain comes from the training data, not from the model.

A control model with the twin's own shape, size and optimiser, given only the new chat data, scores 90 on the scoreboard and 348 on the dev set. The bigger low-bit model adds 3 points and 8 prompts on top, which is inside the spread between seeds (about 3 points on the pilot). So the prompt tests do not prove that the new model beats the control.

The losses do show a difference: the final model is better than the control by 0.10 on stories and 0.05 on assistant chat, far outside the 0.015 yardstick. It is a better language model. The tests are too easy to show that in behaviour, because they are near their ceiling.

What the low-bit work clearly bought is size: the same scores in half the megabytes. At about 42 MB, the 4-bit file (82.8M parameters) is a better language model than an 8-bit model with the twin's shape (41.9M parameters): 0.043 lower on story loss and 0.037 lower on chat loss, in one run each. It is not shown to be a better assistant: every prompt test, including the held-out test (49 against 47 of 130), is a tie within noise (`results/stage8.md`).

## Running it

The model files are not in the repository. Download them from the [v2 release](../../releases/tag/v2), which holds every model file with a `SHA256SUMS.txt`:

- `small-smart-v2-4bit.bin` and `.npz` - v2, the main model. Put them in a folder named `final_v2` next to the code.
- `small-smart-4bit.bin`, `small-smart-8bit.bin` and their `.npz` files - v1, the earlier version. Put them in a folder named `final`.

```
python chat.py final_v2/small-smart-v2-4bit.bin
python chat.py final_v2/small-smart-v2-4bit.bin --tools --notes final_v2/example_notes.txt
python chat.py final/small-smart-8bit.bin --once "Tell me a short story about a cat."
```

- `--tools` turns on the calculator and the notes search. Replies are then steady (not random).
- `--notes` is a text file with one note per line.
- v2 usually searches the notes by itself. v1 needs the word "notes" in the question, for example "Check my notes. When is the dentist?" See Limits.

## Running it without PyTorch

`run_np.py` runs the model with only numpy and the tokenizers package (about 40 MB installed, against about 4.5 GB for PyTorch). It has chat but not the tools yet.

```
python run_np.py final_v2/small-smart-v2-4bit.npz
```

Measured with the v1 4-bit file (v2 has the same shape and size) on a 6-core Ryzen, processor only, single measurements:

| runner | tokens per second | RAM while running | peak RAM while loading | install size |
|---|---|---|---|---|
| PyTorch, processor | about 35 | 1,150 MiB | 1,160 MiB | about 4.5 GB |
| PyTorch, graphics card | about 22 | 1,980 MiB + 500 MiB on the card | - | about 4.5 GB |
| numpy (`run_np.py`) | about 44 | 362 MiB | 652 MiB | about 40 MB |

The numpy runner gave the same replies as PyTorch on 6 of 6 test prompts with steady (non-random) output, and next-token scores agree to 0.00001. It unpacks the weights to 32-bit floats when loaded, so the 4-bit and 8-bit files use the same RAM. Keeping the weights packed would need a compiled runner, which has not been built.

## What the model is

- 25 layers, 512 wide, 8 heads, context of 512 tokens, vocabulary of 8,192. 82.8M parameters.
- Weights are trained on a low-bit grid from the start (quantisation-aware training), so the exported file is the model that was measured.
- Trained for 16,000 steps on simple stories, then 4,000 steps on chat data. That is the same number of steps as the twin. v2 keeps the story phase and redoes the 4,000 chat steps on a new data mix.
- Optimiser: Muon for the weight matrices, AdamW for the rest. One model change: value residual.
- Chat phase: loss on the assistant's words only, with conversations packed tightly.
- Training time: 302 minutes for the 8-bit model, plus 69 minutes for the 4-bit version. Peak GPU memory about 6 GB.

The v1 chat data mix (v2 moves 17 points from job practice to the new v2 data, see `results/stage10.md`): 35% generated job practice (rules, sums, notes, tool calls; 1,000,000 conversations), 20% synthetic instructions, 16% simple chat, 10% story requests, 10% stories, 5% general chat, 2% everyday talk, 2% written by a teacher model (qwen3:8b, 18,748 conversations kept of 23,062 written).

A tool call is a short free line and then one line of JSON, for example `{"tool": "calc", "input": "348 * 27"}`. The result comes back as a user turn starting with "Result:".

## How it was found

Ideas were tested one at a time on a small pilot model (6.8M parameters, 3 seeds per arm, mean and spread reported). A difference under 0.015 in loss counts as no difference.

| stage | question | answer |
|---|---|---|
| 0 | Is the setup already fast? | Yes. torch.compile and smaller micro-batches save time and memory with the same losses. |
| 2 | Which free changes help? | Muon (-0.068 story loss) and value residual (-0.022). Assistant-only loss raised prompts from 11 to 14. |
| 3 | Do lookup tables or other objectives help? | No, not at equal file size. A plain wider model beat them. |
| 4 | Does practice data for the helper's jobs help? | Yes, hugely: pilot scoreboard 15.7 to 74.7, then to about 82 after two rounds of finding failures and adding data. |
| 4 | Does teacher-written data help? | Not on the scoreboard. It helped some fact questions on the dev set. |
| 5 | Does forcing valid tool calls with a grammar help? | No measurable gain (87.4% against 87.7%). More request wordings in the data helped more. |
| 6 | Do fewer bits pay? | Yes. 8-bit training costs nothing (+0.001). At equal megabytes, 4-bit with four times the parameters was best (-0.099). |
| 7 | Does it hold at full size? | Yes for the data and for the low-bit files. See above for what it does not prove. |
| 8 | At equal megabytes, more parameters at 4 bits or fewer at 8 bits? | More parameters at 4 bits give a better language model (clearly lower loss). Not a better assistant: the prompt tests are a tie. Single run. |
| 9 | Does it hold on prompts that break the practice patterns? | Only partly. About 37% pass, against about 97% on the dev set. |
| 10 | Does one more round of data, aimed at that gap, help on a fresh test? | Yes: 74 against 44 of 140 (69 against 42 after AI grading). The gain is in searching notes unprompted and admitting it does not know. New wording did not improve. Single run. |

## Things that did not work

- Weight averaging (EMA): slightly lower loss, no better on prompts, worse in stage 2.
- QK-norm, ReLU squared, a deeper thinner shape: no gain on the pilot.
- Word-pair hash embedding and value embeddings: a gain, but smaller than spending the same parameters on width.
- Multi-token prediction: slightly worse.
- My simplified normalised transformer: clearly worse (+0.048). It was not tuned, so this kills my version, not the idea.
- Grammar-constrained tool calls: no gain.
- Teacher data: no scoreboard gain, and the filter cannot check whether a teacher's fact is true.
- The first round of job data leaked: some dev prompts were also in training. This inflated one early dev score and was fixed with new wordings.

## Limits

- It knows very little about the world. It has read simple stories and practice conversations only. It answered "Shoes" for what you wear on your head.
- It cannot work with letters. "eagle" in capitals came out as "ELLER". It sees word pieces, not letters.
- v1 only searches the notes when the question mentions notes (v2 searched on 18 of 20 such questions and got 12 right). "When is the dentist?" got a made-up answer; "Check my notes. When is the dentist?" got the right one. On the held-out test no model searched in any of 15 such questions.
- Sums in unfamiliar wordings often fail. "What do you get when you put 14 and 23 together?" got 27.
- Two requests in one message almost always fail (0 of 25 on the first held-out test; v2 gets 6 of 30 on the fresh one).
- Tool requests in unfamiliar wordings succeed about 75% to 80% of the time, against 100% for familiar ones.
- It makes things up when it does not know. "Why is the sky blue?" got "That's a good question. What do you think?"
- The scoreboard and dev set test the same kinds of task as the practice data. They measure whether the practice worked, not general intelligence.
- Three dev set failures were faults of the checker (for example it rejected "Young" as the opposite of old). They are fixed in `rescore_dev.py`; the dev numbers above use the fixed checker (before the fix: 94, 346, 353, 355, 350).
- The full-size results are single runs. The learning rate was picked from a 2,000-step check where the winner's lead was inside the yardstick.
- The 4-bit model's story phase was trained at 8 bits, so the 4-bit against 8-bit comparison is not from scratch.
- 15 of the 150 held-out questions were found in the practice data (same or nearly the same question line). They are flagged, and scores are also given without them in `results/stage9.md`.

## What would make it smarter

In order of expected gain: broader reading material in the first phase (simple encyclopedia text, not only stories), more training steps, then a bigger model. The held-out tests are the harder tests to judge these models by. Never train on them. Both have now shaped a round of data (the first shaped v2, and v2's results on the second are known), so the next version needs a third.

## Where things are

- `final_v2/` - the v2 4-bit file (the main model) and an example notes file. `final/` - the two v1 model files. The files themselves come from the release.
- `results/ai_grading/`, `grade_ai.py` - the rubric and the AI grades for the items marked for hand grading.
- `WRITEUP.md` - the public write-up. `MODEL_CARD.md` - the model card. `PUBLISHING.md` - what to leave out of a public repo, and a licence suggestion.
- `results/stage0.md` to `results/stage10.md` - the full tables for every stage.
- `data/heldout.json` and `data/heldout.sha256` - the first frozen held-out test. `make_heldout.py`, `heldout.py` - how it was written and scored.
- `data/heldout2.json`, `data/heldout2.sha256`, `heldout2/make_heldout2.py` - the fresh test used for v2. `gen_v2.py`, `run_v2.sh` - the v2 data and run.
- `runs/f7b` (8-bit) and `runs/f7b_q4` (4-bit) - checkpoints and logs. Milestone checkpoints are kept for the 8-bit run.
- `train.py`, `model.py`, `optim.py` - training. `quant.py` - export and loading of low-bit files. `tools.py` - the tool loop.
- `scoreboard.py`, `devset.py`, `rescore_dev.py`, `stage5.py`, `stage7.py` - the tests.
- `gen_job.py`, `gen_job_extra.py`, `teacher.py` - the practice data.

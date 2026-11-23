# Stage 8 - the missing rival: fewer parameters at 8 bits

Question: at equal megabytes, is it better to have more parameters at 4 bits or fewer at 8 bits?

## What was run

The rival (`r8b`) has the twin's shape: 12 layers, width 512, 8 heads, 41.9M parameters.
Everything else matches the final small-smart runs: 8-bit training (QAT), value residual,
Muon plus AdamW, assistant-only chat loss, the final data mix, batch 64 x 4,
16,000 story steps then 4,000 chat steps.

**This is a single run.** No seeds were repeated.

### Learning rate check (single runs, 2,000 steps each)

| arm | Muon rate | AdamW rate | story loss at 2,000 | peak GPU memory |
|---|---|---|---|---|
| r8b, half rates | 0.005 | 1.2e-3 | 1.410 | 4,027 MiB |
| r8a, pilot rates | 0.01 | 2.4e-3 | 1.413 | 4,027 MiB |
| r8c, double Muon | 0.02 | 2.4e-3 | 1.419 | 4,027 MiB |

All within 0.009, inside the 0.015 yardstick: a tie. The half-rate arm was continued,
by the rule set beforehand (lower rate when tied). It is the same rate the final model used.

## Results

| | twin | control | small-smart 8-bit | small-smart 4-bit | **rival 8-bit** |
|---|---|---|---|---|---|
| layers x width | 12 x 512 | 12 x 512 | 25 x 512 | 25 x 512 | 12 x 512 |
| parameters | 41.9M | 41.9M | 82.8M | 82.8M | 41.9M |
| file size | 83.9 MB | 83.9 MB | 83.2 MB | 41.7 MB | **42.1 MB** |
| story loss | 1.212 | 1.233 | 1.132 | 1.153 | **1.196** |
| chat loss (all tokens) | 0.944 | 2.753 | 2.402 | 2.463 | **2.510** |
| assistant chat loss | 0.853 | 0.892 | 0.844 | 0.837 | **0.874** |
| scoreboard /100 | 22 | 90 | 93 | 92 | **88** |
| - instruction /20 | 9 | 18 | 19 | 18 | 16 |
| - arithmetic /20 | 3 | 20 | 20 | 20 | 20 |
| - format /20 | 6 | 17 | 18 | 18 | 17 |
| - notes /20 | 4 | 17 | 17 | 17 | 17 |
| - tool call /20 | 0 | 18 | 19 | 19 | 18 |
| dev set /362 | 94 | 346 | 353 | 355 | **350** |
| tool test, free | 0.0% | 92.3% | 90.0% | 91.5% | **88.5%** |
| tool test, constrained | 0.0% | 92.3% | 91.5% | 91.5% | **90.0%** |
| - calc | 0 | 100 | 100 | 100 | 100 |
| - calc, new wording | 0 | 83 | 73 | 80 | 63 |
| - notes | 0 | 100 | 100 | 100 | 100 |
| - notes, new wording | 0 | 75 | 75 | 75 | 80 |
| peak GPU memory in training | n/a | 9,474 MiB | 5,681 MiB | 5,997 MiB | **4,027 MiB** |

All rows except the twin and control are scored from the exported file.
"Chat loss (all tokens)" is not comparable between the twin and the others, because the
others were trained on assistant tokens only.

Story loss during the rival's story phase: 1.296 (4,000), 1.194 (8,000), 1.133 (12,000),
1.107 (16,000). The 25-layer model was at 1.054 at step 16,000.

Training time: 153 minutes logged in total. The first 2,000 steps ran alongside the two
other learning-rate arms and were slow (about 55 minutes); the remaining 18,000 took about
2 hours 25 minutes.

## Rival against the 4-bit small-smart file (both about 42 MB)

| measure | rival 8-bit | small-smart 4-bit | gap | bigger than yardstick? |
|---|---|---|---|---|
| story loss | 1.196 | 1.153 | 0.043 | yes (0.015 and 0.025) |
| assistant chat loss | 0.874 | 0.837 | 0.037 | yes (0.015 and 0.025) |
| scoreboard | 88 | 92 | 4 points | just outside the 3-point seed spread |
| dev set | 350 | 355 | 5 items (1.4%) | no clear signal |
| tool test, free | 88.5% | 91.5% | 4 items of 130 | no clear signal |

## Answer

At equal megabytes, **more parameters at 4 bits give a better language model, not a better
assistant**, in this single run.

- On loss the gap is clear: 0.043 on stories and 0.037 on assistant chat, both larger
  than either yardstick.
- On behaviour it is a tie. The scoreboard gap (4 points) is only just outside the roughly
  3-point spread seen between seeds, the dev set and tool test gaps are a handful of items,
  and on the held-out test added in stage 9 the two score 49 and 47 of 130, inside the
  chance error of about 4 items.

## Caveats, stated plainly

- Single run, one seed, one learning rate setting.
- The 4-bit model had an 8-bit story phase and only its chat phase was redone at 4 bits.
  It was not trained at 4 bits from scratch, so this is "4-bit by conversion plus chat
  retraining" against "8-bit from scratch".
- The rival's learning rate check was a three-way tie, so the rate was chosen by rule,
  not by evidence.
- The exported rival file does not score exactly like its checkpoint: scoreboard 88
  against 89 (one instruction item), and tool test 88.5% against 87.7% free. The losses
  and the dev set total are identical. The earlier models' exported files matched their
  checkpoints exactly. I have not tracked down which item flips or why.
- During the learning rate check two of the three runs crashed at start-up (a clash in
  the compile cache when three new-shape runs started together). They were restarted one
  at a time and ran normally. No training results were affected.
- The control (twin weights, new chat data, no QAT, no Muon) scores 90 on the scoreboard
  against the rival's 88, with a worse story loss (1.233 against 1.196). So for a
  12-layer model, the new training recipe improved loss but did not improve the prompt
  tests. That fits the stage 7 finding that the practice data did most of the work.

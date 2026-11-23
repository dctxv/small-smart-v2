# Stage 6: fewer bits (pilot model, 6,000 story + 1,500 chat steps, 3 seeds per arm)

Losses are measured with the weights already rounded to the low-bit grid, so they are the losses of the file that ships.

| arm | parameters | file MB | story loss at 6,000 | assistant chat loss at end | prompts /100 | vs baseline (story) | minutes | peak GPU MiB |
|---|---|---|---|---|---|---|---|---|
| baseline, 16-bit floats | 6,815,756 | 13.6 | 1.506 +- 0.002 (n=3) | 1.123 +- 0.002 (n=3) | 16.3 +- 1.5 (n=3) | +0.000 | 29 | 2955 |
| 8-bit, same shape as the baseline | 6,815,756 | 6.9 | 1.508 +- 0.001 (n=3) | 1.124 +- 0.003 (n=3) | 13.0 +- 2.0 (n=3) | +0.001 | 30 | 2955 |
| 4-bit, same shape as the baseline | 6,815,756 | 3.5 | 1.554 +- 0.001 (n=3) | 1.174 +- 0.002 (n=3) | 13.3 +- 2.1 (n=3) | +0.047 | 30 | 2955 |
| 8-bit, width 384 (equal megabytes) | 13,762,572 | 13.8 | 1.429 +- 0.000 (n=3) | 1.020 +- 0.003 (n=3) | 17.0 +- 1.0 (n=3) | -0.078 | 47 | 3578 |
| 4-bit, width 560 (equal megabytes) | 27,166,732 | 13.7 | 1.407 +- 0.002 (n=3) | 0.984 +- 0.003 (n=3) | 17.3 +- 1.2 (n=3) | -0.099 | 105 | 5246 |

## Verdict
- 8-bit training is free at the same shape (+0.001) and halves the file. With the saved megabytes spent on width, it beats the 16-bit baseline by 0.078 at the same file size.
- 4-bit costs 0.047 at the same shape. At equal megabytes (four times the parameters) it beats the 8-bit arm by 0.022 on story loss and 0.036 on assistant chat loss, so per megabyte 4-bit is best.
- Per hour of training 8-bit is best: the 4-bit equal-megabytes arm took 105 minutes against 47 (three runs side by side in both cases).
- Notes on the 4-bit wide arm: it was paused once and resumed from saved steps; seed 2 crashed with a CUDA library error after the resume (three runs used about 15.7 GB) and was restarted from its step 3,000 resume point. Loss curves continued without a jump.
- File sizes are real exported files (quant.py): int8 or packed 4-bit weights with one scale per row.

## Speed check for the final shape (25 x 512, 82.8M, 8-bit, Muon, 150 steps, single runs)

| setting | seconds per step | peak allocated MiB |
|---|---|---|
| micro-batch 16, no compile | 1.10 | 6,604 |
| micro-batch 16, torch.compile | 0.84 | 5,681 |
| micro-batch 32, torch.compile | 0.84 | 9,888 |

torch.compile is 1.3 times faster on this shape and gives the same losses. Micro-batch 16 with compile is used for the final run.

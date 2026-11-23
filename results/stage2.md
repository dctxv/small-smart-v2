# Stage 2: free wins (pilot model 6.8M, 6,000 story + 1,500 chat steps, 3 seeds per arm)

Learning rates from the single-seed sweep: AdamW 1.2e-3, Muon 0.01.
Sweep, held-out story loss at step 6,000: sw_adam_3e-4 1.939, sw_adam_6e-4 1.722, sw_adam_1.2e-3 1.606, sw_muon_0.01 1.578, sw_muon_0.02 1.582, sw_muon_0.05 1.681

Values are mean +- standard deviation over seeds. Lower loss is better. Prompts are out of 100.

| arm | story loss at 6,000 | chat loss at end | assistant-only chat loss at end | prompts | vs baseline (story) | vs baseline (assistant chat) |
|---|---|---|---|---|---|---|
| baseline | 1.609 +- 0.004 (n=3) | 1.332 +- 0.005 (n=3) | 1.258 +- 0.006 (n=3) | 11.0 +- 0.0 (n=3) | +0.000 | +0.000 |
| weight averaging (same runs) | 1.605 +- 0.004 (n=3) | 1.467 +- 0.008 (n=3) | 1.395 +- 0.008 (n=3) | 9.3 +- 1.2 (n=3) | -0.004 | +0.137 |
| Muon optimiser | 1.541 +- 0.002 (n=3) | 1.282 +- 0.000 (n=3) | 1.191 +- 0.000 (n=3) | 11.3 +- 1.5 (n=3) | -0.068 | -0.068 |
| QK-norm | 1.613 +- 0.004 (n=3) | 1.337 +- 0.001 (n=3) | 1.262 +- 0.003 (n=3) | 10.0 +- 2.0 (n=3) | +0.005 | +0.004 |
| ReLU squared | 1.603 +- 0.003 (n=3) | 1.335 +- 0.003 (n=3) | 1.263 +- 0.005 (n=3) | 11.3 +- 1.5 (n=3) | -0.005 | +0.005 |
| value residual | 1.587 +- 0.002 (n=3) | 1.322 +- 0.000 (n=3) | 1.241 +- 0.002 (n=3) | 10.3 +- 2.3 (n=3) | -0.022 | -0.017 |
| deep 10 x 208 (base is 6 x 256) | 1.606 +- 0.007 (n=3) | 1.339 +- 0.003 (n=3) | 1.270 +- 0.005 (n=3) | 10.0 +- 1.0 (n=3) | -0.002 | +0.011 |
| assistant-only loss, tight packing | - | 2.948 +- 0.031 (n=3) | 1.262 +- 0.004 (n=3) | 14.0 +- 2.0 (n=3) | - | +0.004 |

## Follow-up: the first learning-rate sweep was too narrow

The best value sat on the edge of the first sweep for both optimisers, so the sweep was extended (single runs, seed 0, story loss at 6,000):
AdamW 2.4e-3 1.559, AdamW 4.8e-3 1.550 (not better than 2.4e-3 by more than 0.015, so 2.4e-3 is kept);
Muon 0.005 with AdamW 1.2e-3 on the embedding 1.555; Muon 0.01 with embedding rate 2.4e-3 1.519; with 4.8e-3 1.511 (inside the yardstick, 2.4e-3 kept).
All arms in the table above ran at AdamW 1.2e-3, so they compare fairly with each other, but the baseline was under-tuned.
The winners were therefore run again at the tuned rates, 3 seeds each:

| arm (tuned rates) | story loss at 6,000 | assistant-only chat loss at end | prompts | vs tuned baseline (story) |
|---|---|---|---|---|
| baseline, AdamW 2.4e-3 | 1.555 +- 0.003 | 1.151 +- 0.005 | 15.0 +- 1.0 | 0 |
| Muon 0.01 (embedding 2.4e-3) | 1.521 +- 0.003 | 1.136 +- 0.005 | 15.7 +- 3.8 | -0.034 |
| value residual | 1.537 +- 0.003 | 1.144 +- 0.002 | 13.3 +- 1.5 | -0.018 |
| Muon + value residual (combination) | 1.506 +- 0.002 | 1.123 +- 0.002 | 16.3 +- 1.5 | -0.049 |

Verdict: Muon and value residual both beat the 0.015 yardstick and their gains add up when combined (-0.049).
Tuning the learning rate alone was worth -0.054, more than any single trick.
Weight averaging: -0.004 to -0.008 on story loss (inside the yardstick) and worse at the end of the short chat phase; not kept.
QK-norm, ReLU squared: no effect at the first rate; checked again on top of the winners in stage 3.
Deep vs wide at equal parameters: no quality difference (-0.002 story, +0.011 assistant chat); checked again in stage 3.
Assistant-only loss with tight packing: assistant chat loss unchanged (+0.004); prompts 14.0 +- 2.0 against 11.0 +- 0.0, suggestive but not a loss win; to be tried again with the job data.
Peak GPU memory per pilot run: 2.9 to 4.1 GB (logged in each run's log.jsonl).

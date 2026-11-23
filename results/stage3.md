# Stage 3: lookup memory and objectives (pilot model, 6,000 story + 1,500 chat steps, 3 seeds per arm)

Values are mean +- standard deviation over seeds. Lower loss is better. Prompts are out of 100.

| arm | parameters | story loss at 6,000 | assistant-only chat loss at end | prompts | vs baseline (story) | vs baseline (assistant chat) | minutes | peak GPU MiB |
|---|---|---|---|---|---|---|---|---|
| baseline (stage 2 winners: Muon + value residual) | 6,815,756 | 1.506 +- 0.002 (n=3) | 1.123 +- 0.002 (n=3) | 16.3 +- 1.5 (n=3) | +0.000 | +0.000 | 29 | 2955 |
| word-pair hash embedding (16,384 rows) | 11,010,060 | 1.489 +- 0.003 (n=3) | 1.091 +- 0.006 (n=3) | 12.3 +- 2.1 (n=3) | -0.017 | -0.032 | 29 | 3019 |
| value embeddings (2 tables) | 11,010,060 | 1.500 +- 0.001 (n=3) | 1.114 +- 0.003 (n=3) | 14.7 +- 4.0 (n=3) | -0.006 | -0.009 | 30 | 3027 |
| multi-token prediction (token after next, weight 0.3) | 6,881,292 | 1.512 +- 0.001 (n=3) | 1.137 +- 0.001 (n=3) | 13.0 +- 2.0 (n=3) | +0.005 | +0.014 | 36 | 3495 |
| approximately normalised transformer | 6,818,828 | 1.554 +- 0.004 (n=3) | 1.202 +- 0.007 (n=3) | 12.0 +- 1.7 (n=3) | +0.048 | +0.079 | 34 | 3343 |
| wider model, same parameter count as the lookup arms (control) | 10,881,036 | 1.451 +- 0.002 (n=3) | 1.048 +- 0.004 (n=3) | 15.7 +- 1.5 (n=3) | -0.055 | -0.075 | 54 | 3936 |
| recheck: QK-norm | 6,815,756 | 1.501 +- 0.003 (n=3) | 1.121 +- 0.003 (n=3) | 14.0 +- 1.7 (n=3) | -0.005 | -0.002 | 30 | 3054 |
| recheck: ReLU squared | 6,815,756 | 1.503 +- 0.001 (n=3) | 1.124 +- 0.001 (n=3) | 14.3 +- 3.5 (n=3) | -0.003 | +0.001 | 36 | 3339 |
| recheck: deep 10 x 208 | 6,895,636 | 1.496 +- 0.001 (n=3) | 1.127 +- 0.000 (n=3) | 13.7 +- 0.6 (n=3) | -0.010 | +0.004 | 60 | 4158 |

## Verdict

- Word-pair hash embedding: -0.017 story, -0.032 assistant chat, for free in training time, but it adds 4.2M parameters (+62%). A plain wider model with the same parameter count gains -0.055 / -0.075. At equal file size the table loses, so it is not kept. It stays noted as a cheap-compute option.
- Value embeddings: -0.006 story, inside the yardstick, with the same +62% parameters. Not kept.
- Multi-token prediction: +0.005 story, +0.014 assistant chat (slightly worse). Not kept.
- Approximately normalised transformer: +0.048 story (worse). This was my own simplified version (stream re-normalised after every update with learned step sizes, weights not normalised), with no tuning of its own. It kills this version, not the idea in general.
- Rechecks on top of the winners: QK-norm -0.005, ReLU squared -0.003, deep 10 x 208 -0.010 story and +0.004 assistant chat. None beats the yardstick. Deep and wide are equal in quality at equal parameters, so the final shape is chosen on speed (deep was faster at 70M to 100M in stage 0).
- Prompt scores (out of 100) have a spread of 2 to 4 points across seeds at this size, so they cannot separate these arms.

Carried forward: Muon + value residual + tuned learning rates. Nothing from stage 3 is added.

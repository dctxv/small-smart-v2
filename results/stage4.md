# Stage 4: teacher data and the fail-finding loop (pilot model, 6.8M, 3 seeds per run)

Every run is a 4,000-step chat phase started from the stage 2 combination's story checkpoints.
All runs after nojob use loss on assistant words only. The scoreboard is the frozen 100 prompts; the dev set is a separate 362 prompts in 19 families.

## Teachers
- Main: qwen3:8b (Apache 2.0, 5.2 GB download, 4-bit GGUF through Ollama, about 100 conversations per minute).
- Fallback: qwen3.5:2b (Apache 2.0). Rejected for facts: a sample had wrong facts.
- The teacher was never loaded while a training run was on the GPU (teacher.py refuses to start if one is).

## Teacher data
Two rounds, 3 hours in total: 23,062 conversations written, 18,748 kept.

Kept by kind: {'explain': 3589, 'notes': 1768, 'chat': 2558, 'instr': 2625, 'howto': 555, 'chat2': 539, 'fact1': 3684, 'yesno': 3009, 'howmany': 421}

Dropped: {'hard words': 275, 'rule broken': 914, 'characters': 83, 'duplicate': 3007, 'scoreboard': 35}

The filter checks characters, a simple-word list, length, the request's own rule, notes grounding, duplicates and overlap with the scoreboard and dev prompts.
It cannot check truth. A sample of 42 short facts from round 2 had several wrong or odd answers ("What does a wind turbine make? Noise.").

## Runs
- nojob: default chat mix, no job data.
- jobasst: round 0 programmatic job data (300,000 conversations). Round 0 data still contained dev prompts, so its dev score is inflated.
- r1: round 1 programmatic data aimed at the failed families. r1t: r1 plus teacher round 1 at 5% of the mix.
- r2: round 2 programmatic data (more sums, capitals for any common word, more "lines" wordings, about 55 calculator wordings). r2t: r2 plus both teacher rounds at 6%.
- nd: r1 data with the draft line before tool calls removed (stage 5).

| run | assistant chat loss | scoreboard /100 | instruction | arithmetic | format | notes | tool_call | dev set /362 |
|---|---|---|---|---|---|---|---|---|
| nojob | 1.006 +- 0.003 (n=3) | 15.7 +- 0.6 (n=3) | 8.3 | 1.0 | 4.3 | 2.0 | 0.0 | 85.7 +- 1.2 (n=3) |
| jobasst | 1.086 +- 0.000 (n=3) | 74.7 +- 0.6 (n=3) | 13.7 | 11.7 | 17.0 | 15.0 | 17.3 | 272.3 +- 6.7 (n=3) |
| r1 | 1.084 +- 0.002 (n=3) | 81.3 +- 3.8 (n=3) | 16.7 | 16.7 | 15.3 | 14.7 | 18.0 | 313.3 +- 7.1 (n=3) |
| r1t | 1.106 +- 0.002 (n=3) | 79.3 +- 3.8 (n=3) | 16.0 | 15.3 | 15.3 | 14.7 | 18.0 | 306.3 +- 2.1 (n=3) |
| r2 | 1.086 +- 0.002 (n=3) | 83.3 +- 2.9 (n=3) | 17.0 | 17.7 | 15.7 | 15.3 | 17.7 | 313.3 +- 7.5 (n=3) |
| r2t | 1.109 +- 0.002 (n=3) | 83.0 +- 3.6 (n=3) | 16.3 | 16.7 | 16.7 | 14.7 | 18.7 | 319.0 +- 1.7 (n=3) |
| nd | 1.086 +- 0.003 (n=3) | 81.7 +- 3.2 (n=3) | 17.3 | 16.0 | 15.3 | 14.7 | 18.3 | 315.0 +- 2.6 (n=3) |

Dev set pass rate per family (mean of 3 seeds):

| family | nojob | jobasst | r1 | r1t | r2 | r2t | nd |
|---|---|---|---|---|---|---|---|
| one_word | 0.45 | 0.53 | 0.65 | 0.65 | 0.63 | 0.75 | 0.72 |
| yes_no | 0.82 | 0.73 | 0.78 | 0.77 | 0.75 | 0.70 | 0.77 |
| repeat_word | 0.55 | 0.60 | 0.98 | 0.98 | 0.98 | 1.00 | 0.98 |
| exact_words | 0.10 | 0.13 | 1.00 | 1.00 | 0.97 | 0.97 | 1.00 |
| start_end | 0.25 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| one_sentence | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| copy | 0.48 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| sum | 0.02 | 0.20 | 0.57 | 0.32 | 0.63 | 0.58 | 0.55 |
| word_problem | 0.02 | 0.72 | 0.87 | 0.88 | 0.97 | 1.00 | 0.85 |
| numbered | 0.00 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 | 1.00 |
| dashed | 0.00 | 0.98 | 0.97 | 0.98 | 0.98 | 0.98 | 0.97 |
| capitals | 0.10 | 0.22 | 0.40 | 0.28 | 0.28 | 0.20 | 0.35 |
| lines | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| number_only | 0.00 | 0.50 | 0.60 | 0.62 | 0.55 | 0.87 | 0.72 |
| range | 0.75 | 0.98 | 0.95 | 0.95 | 0.93 | 0.93 | 0.93 |
| notes | 0.07 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| notes_missing | 0.02 | 0.92 | 0.92 | 0.92 | 0.90 | 0.90 | 0.93 |
| tool_calc | 0.00 | 1.00 | 0.98 | 0.97 | 1.00 | 0.97 | 0.98 |
| tool_notes | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |


## Verdict
- Programmatic job data is the big win: 15.7 to 74.7 on the scoreboard, then 81.3 after one targeted round.
- Round 2 is inside the seed spread of round 1. The loop has levelled off at this model size.
- Teacher data: no scoreboard gain in either round. On the dev set it helps the fact families it was written for (one word 0.63 to 0.75, number only 0.55 to 0.87) and does not help yes or no.
- Still failing on the pilot: capitals (got worse with more spelling data), two-digit sums (about 0.6), simple facts. Read as capacity limits of a 6.8M model; to be re-tested at full size.

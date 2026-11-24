Held-out test, sha256 b3f1336a992dd1ffd16b09ccc8fe2c93b66a27bdceff6e4768bd37364f313307

| part | items | twin | twinctl | ss8 | ss4 | rival8 | v2_ctl | v2_q4 |
|---|---|---|---|---|---|---|---|---|
| **A to D, headline** | 140 | 27 | 40 | 48 | 44 | 50 | 63 | 74 |
| **A to D, without the items found in the practice data** | 127 | 26 | 33 | 39 | 35 | 41 | 53 | 64 |
| E, without the items found in the practice data | 6 | 3 | 5 | 4 | 3 | 4 | 5 | 3 |
| A: five skills, new wording | 50 | 7 | 20 | 29 | 26 | 27 | 23 | 29 |
| - instruction | 10 | 4 | 4 | 7 | 7 | 6 | 5 | 6 |
| - arithmetic | 10 | 0 | 4 | 5 | 5 | 5 | 5 | 6 |
| - format | 10 | 1 | 3 | 4 | 3 | 4 | 4 | 5 |
| - notes | 10 | 2 | 2 | 6 | 4 | 4 | 1 | 3 |
| - tool_call | 10 | 0 | 7 | 7 | 7 | 8 | 8 | 9 |
| B: notes questions without the word notes | 30 | 1 | 1 | 2 | 1 | 3 | 13 | 14 |
| - store | 20 | 0 | 0 | 1 | 0 | 1 | 11 | 12 |
| - inline | 10 | 1 | 1 | 1 | 1 | 2 | 2 | 2 |
| C: two skills in one request | 30 | 0 | 2 | 1 | 1 | 1 | 6 | 6 |
| D: questions with no answer | 30 | 19 | 17 | 16 | 16 | 19 | 21 | 25 |
| - no_answer | 12 | 11 | 7 | 8 | 6 | 10 | 11 | 11 |
| - not_in_notes | 8 | 4 | 3 | 3 | 3 | 3 | 3 | 6 |
| - no_tool | 10 | 4 | 7 | 5 | 7 | 6 | 7 | 8 |
| E: world knowledge (reported apart) | 20 | 16 | 18 | 17 | 16 | 17 | 17 | 16 |

Tool use on part B store items (the fact is only in the notes store): how many times the model searched the notes

| | twin | twinctl | ss8 | ss4 | rival8 | v2_ctl | v2_q4 |
|---|---|---|---|---|---|---|---|
| searched, of 20 | 0 | 1 | 1 | 0 | 1 | 18 | 18 |

Peak GPU memory while scoring: twin 256 MiB, twinctl 255 MiB, ss8 497 MiB, ss4 498 MiB, rival8 256 MiB, v2_ctl 256 MiB, v2_q4 498 MiB

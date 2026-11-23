Held-out test, sha256 77aa0feb50453863b93cbaef08b76998493b0c78049ecde3978c0e6b5c0bbda2

| part | items | twin | twinctl | ss8 | ss4 | rival8 |
|---|---|---|---|---|---|---|
| **A to D, headline** | 130 | 26 | 45 | 50 | 49 | 47 |
| **A to D, without the items found in the practice data** | 121 | 24 | 41 | 47 | 44 | 45 |
| E, without the items found in the practice data | 14 | 2 | 7 | 7 | 7 | 8 |
| A: five skills, new wording | 60 | 6 | 26 | 33 | 31 | 29 |
| - instruction | 12 | 4 | 5 | 8 | 9 | 8 |
| - arithmetic | 12 | 0 | 3 | 4 | 2 | 3 |
| - format | 12 | 1 | 4 | 6 | 3 | 5 |
| - notes | 12 | 1 | 5 | 6 | 7 | 5 |
| - tool_call | 12 | 0 | 9 | 9 | 10 | 8 |
| B: notes questions without the word notes | 25 | 4 | 5 | 6 | 6 | 3 |
| - store | 15 | 0 | 0 | 0 | 0 | 0 |
| - inline | 10 | 4 | 5 | 6 | 6 | 3 |
| C: two skills in one request | 25 | 1 | 1 | 0 | 0 | 0 |
| D: questions with no answer | 20 | 15 | 13 | 11 | 12 | 15 |
| - no_notes | 8 | 8 | 5 | 6 | 6 | 7 |
| - not_in_notes | 6 | 2 | 2 | 2 | 3 | 2 |
| - nobody_knows | 6 | 5 | 6 | 3 | 3 | 6 |
| E: world knowledge (reported apart) | 20 | 5 | 11 | 11 | 11 | 12 |

Tool use on part B store items (the fact is only in the notes store): how many times the model searched the notes

| | twin | twinctl | ss8 | ss4 | rival8 |
|---|---|---|---|---|---|
| searched, of 15 | 0 | 0 | 0 | 0 | 0 |

Peak GPU memory while scoring: twin 255 MiB, twinctl 255 MiB, ss8 496 MiB, ss4 496 MiB, rival8 255 MiB

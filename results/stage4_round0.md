done nojob_s0
done nojob_s1
done nojob_s2
done job_s0
done job_s1
done job_s2
done jobasst_s0
done jobasst_s1
done jobasst_s2
| run | assistant chat loss | scoreboard /100 | instruction | arithmetic | format | notes | tool_call | dev set /362 |
|---|---|---|---|---|---|---|---|---|
| nojob | 1.006 +- 0.003 (n=3) | 15.7 +- 0.6 (n=3) | 8.3 | 1.0 | 4.3 | 2.0 | 0.0 | 85.7 +- 1.2 (n=3) |
| job | 1.058 +- 0.001 (n=3) | 66.7 +- 2.5 (n=3) | 12.3 | 7.7 | 15.3 | 12.7 | 18.7 | 258.7 +- 3.8 (n=3) |
| jobasst | 1.086 +- 0.000 (n=3) | 74.7 +- 0.6 (n=3) | 13.7 | 11.7 | 17.0 | 15.0 | 17.3 | 272.3 +- 6.7 (n=3) |

Dev set pass rate per family (mean of 3 seeds):

| family | nojob | job | jobasst |
|---|---|---|---|
| one_word | 0.45 | 0.50 | 0.53 |
| yes_no | 0.82 | 0.67 | 0.73 |
| repeat_word | 0.55 | 0.55 | 0.60 |
| exact_words | 0.10 | 0.18 | 0.13 |
| start_end | 0.25 | 1.00 | 1.00 |
| one_sentence | 0.67 | 1.00 | 1.00 |
| copy | 0.48 | 1.00 | 1.00 |
| sum | 0.02 | 0.22 | 0.20 |
| word_problem | 0.02 | 0.57 | 0.72 |
| numbered | 0.00 | 0.93 | 1.00 |
| dashed | 0.00 | 1.00 | 0.98 |
| capitals | 0.10 | 0.07 | 0.22 |
| lines | 0.00 | 1.00 | 1.00 |
| number_only | 0.00 | 0.35 | 0.50 |
| range | 0.75 | 0.90 | 0.98 |
| notes | 0.07 | 1.00 | 1.00 |
| notes_missing | 0.02 | 0.90 | 0.92 |
| tool_calc | 0.00 | 1.00 | 1.00 |
| tool_notes | 0.00 | 1.00 | 1.00 |

# Stage 5: tools (pilot model, 3 seeds per run)

Format: a free draft line, then one JSON line, for example {"tool": "calc", "input": "348 * 27"} or {"tool": "notes", "input": "dentist"}.
The tool result comes back as a user turn starting with "Result:" and the model writes the final answer.
"constrained" means that once a reply line starts with a brace, every next token is restricted so the line can only become a valid call.
34 to 36 of the 40 plain notes requests share their wording with training requests, but the notes behind them are new.

Tool test: 130 held-out requests, full loop (call, tool runs, result, final answer). Mean +- standard deviation over 3 seeds, in percent.

| run | output | valid call | right call | right final answer | calc (final) | calc_new_wording (final) | notes (final) | notes_new_wording (final) | wrote a draft line |
|---|---|---|---|---|---|---|---|---|---|
| r1 | free | 93.3 +- 1.2 (n=3) | 84.4 +- 1.2 (n=3) | 84.4 +- 1.2 (n=3) | 100.0 +- 0.0 (n=3) | 47.8 +- 3.8 (n=3) | 100.0 +- 0.0 (n=3) | 76.7 +- 2.9 (n=3) | 93.3 +- 1.2 (n=3) |
| r1 | constrained | 93.3 +- 1.2 (n=3) | 84.6 +- 0.8 (n=3) | 84.6 +- 0.8 (n=3) | 100.0 +- 0.0 (n=3) | 48.9 +- 1.9 (n=3) | 100.0 +- 0.0 (n=3) | 76.7 +- 2.9 (n=3) | 93.3 +- 1.2 (n=3) |
| r2 | free | 95.9 +- 1.9 (n=3) | 87.4 +- 3.1 (n=3) | 87.4 +- 3.1 (n=3) | 97.5 +- 2.5 (n=3) | 64.4 +- 9.6 (n=3) | 100.0 +- 0.0 (n=3) | 76.7 +- 7.6 (n=3) | 95.9 +- 1.9 (n=3) |
| r2 | constrained | 95.9 +- 1.9 (n=3) | 87.7 +- 2.7 (n=3) | 87.7 +- 2.7 (n=3) | 97.5 +- 2.5 (n=3) | 65.6 +- 7.7 (n=3) | 100.0 +- 0.0 (n=3) | 76.7 +- 7.6 (n=3) | 95.9 +- 1.9 (n=3) |
| r2t | free | 95.9 +- 0.9 (n=3) | 87.4 +- 2.7 (n=3) | 87.4 +- 2.7 (n=3) | 99.2 +- 1.4 (n=3) | 63.3 +- 10.0 (n=3) | 100.0 +- 0.0 (n=3) | 75.0 +- 0.0 (n=3) | 95.9 +- 0.9 (n=3) |
| r2t | constrained | 95.9 +- 0.9 (n=3) | 87.9 +- 1.9 (n=3) | 87.9 +- 1.9 (n=3) | 99.2 +- 1.4 (n=3) | 65.6 +- 6.9 (n=3) | 100.0 +- 0.0 (n=3) | 75.0 +- 0.0 (n=3) | 95.9 +- 0.9 (n=3) |
| nd | free | 86.7 +- 1.6 (n=3) | 82.1 +- 3.6 (n=3) | 82.1 +- 3.6 (n=3) | 100.0 +- 0.0 (n=3) | 43.3 +- 15.3 (n=3) | 100.0 +- 0.0 (n=3) | 68.3 +- 2.9 (n=3) | 0.0 +- 0.0 (n=3) |
| nd | constrained | 86.7 +- 1.6 (n=3) | 82.8 +- 2.9 (n=3) | 82.8 +- 2.9 (n=3) | 100.0 +- 0.0 (n=3) | 46.7 +- 11.5 (n=3) | 100.0 +- 0.0 (n=3) | 68.3 +- 2.9 (n=3) | 0.0 +- 0.0 (n=3) |


## Verdict
- Grammar constrained output: no measurable gain in any run (at most 0.7 points, inside the spread). The model already writes valid calls; its mistakes are the wrong operation, a miscopied number, or not calling at all, and the grammar cannot fix those.
- Free draft line: without it valid calls fall from 93.3 to 86.7 percent, but right final answers (84.4 against 82.1) are inside the spread. Kept, as a small help at no cost.
- More calculator wordings in training (r2) lifted new-wording sums from 47.8 to 64.4, with a large spread.

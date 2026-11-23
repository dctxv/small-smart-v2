# Stage 7: the final model

Every row in this file is a single run. Stage 4 found a spread of about 3 scoreboard points between seeds on the pilot, so differences of that size here are not proven.

## What was built

- Shape: 25 layers x 512 wide, 8 heads, context 512, vocabulary 8,192. 82.8M parameters.
- Bits: 8-bit weights, trained that way from the first step (quantisation-aware). Real file: 83.2 MB. The twin is 83.9 MB.
- Recipe: Muon for the weight matrices, AdamW for the rest, value residual, loss on assistant tokens only in the chat phase.
- Data: 16,000 story steps, then 4,000 chat steps on the final mix (35% job data, 20% synth, 16% tinychat, 10% story requests, 10% stories, 5% smol, 2% teacher, 2% everyday).
- Steps: the same count as the twin (16,000 + 4,000, batch 64).

## Speed check (150 steps each)

| setting | seconds per step | peak GPU MiB |
|---|---|---|
| micro-batch 16, no compile | 1.10 | 6,604 |
| micro-batch 16, torch.compile | 0.84 | 5,681 |
| micro-batch 32, torch.compile | 0.84 | 9,888 |

## Learning rate check (2,000 steps of the real schedule)

| arm | Muon rate | AdamW rate | story loss at 2,000 | minutes | peak GPU MiB |
|---|---|---|---|---|---|
| half rates | 0.005 | 1.2e-3 | 1.356 | 32.9 | 5,681 |
| pilot rates | 0.01 | 2.4e-3 | 1.368 | 33.6 | 5,681 |
| double Muon | 0.02 | 2.4e-3 | 1.394 | 32.8 | 5,681 |

The half-rate arm was continued as the final run. Its lead over the pilot rates (0.012) is inside the 0.015 yardstick. It was chosen because the trend over the three arms points to lower rates and early steps flatter high rates. A quarter rate was not tried.

## The final run

302 minutes in total, peak GPU memory 5,681 MiB. Milestone checkpoints are in runs/f7b.

| step | story loss | assistant chat loss |
|---|---|---|
| 4,000 | 1.245 | - |
| 8,000 | 1.142 | - |
| 12,000 | 1.081 | - |
| 16,000 (end of stories) | 1.054 | - |
| 17,000 | 1.161 | 0.900 |
| 18,000 | 1.156 | 0.857 |
| 19,000 | 1.140 | 0.843 |
| 20,000 | 1.133 | 0.844 |

Story loss rises by 0.08 during the chat phase, because only 10% of the chat mix is stories.

## Results

- twin: the baseline. 12 x 512, 41.9M parameters, 16-bit, AdamW, old chat data.
- control: the twin's own story-phase weights, then the new chat phase (new data, assistant-only loss) with the twin's optimiser. Same shape and size as the twin. 25 minutes, peak 9,474 MiB.
- final: the model described above.
- final, averaged weights: the running average of the weights (EMA) from the same run.
- final, 8-bit file: the real exported file, read back and scored.

| model | file MB | story loss | assistant chat loss | scoreboard /100 | instruction | arithmetic | format | notes | tool call | dev set /362 | tool test free % | tool test constrained % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| twin | 83.9 | 1.212 | 0.853 | 22 | 9 | 3 | 6 | 4 | 0 | 94 | 0.0 | 0.0 |
| control | 83.9 | 1.233 | 0.892 | 90 | 18 | 20 | 17 | 17 | 18 | 346 | 92.3 | 92.3 |
| final | - | 1.132 | 0.844 | 93 | 19 | 20 | 18 | 17 | 19 | 353 | 90.0 | 91.5 |
| final, averaged weights | - | 1.121 | 0.825 | 92 | 18 | 20 | 17 | 18 | 19 | 352 | 89.2 | 91.5 |
| final, 8-bit file | 83.2 | 1.132 | 0.844 | 93 | 19 | 20 | 18 | 17 | 19 | 353 | 90.0 | 91.5 |

Tool test by family (free output, % right final answer):

| model | calculator | calculator, new wording | notes | notes, new wording |
|---|---|---|---|---|
| control | 100 | 83 | 100 | 75 |
| final | 100 | 73 | 100 | 75 |

Dev set pass rate per family:

| family | twin | control | final |
|---|---|---|---|
| one_word | 0.55 | 0.80 | 0.75 |
| yes_no | 0.80 | 0.90 | 1.00 |
| repeat_word | 0.70 | 0.95 | 1.00 |
| exact_words | 0.00 | 1.00 | 1.00 |
| start_end | 0.25 | 1.00 | 1.00 |
| one_sentence | 0.35 | 1.00 | 1.00 |
| copy | 0.70 | 1.00 | 1.00 |
| sum | 0.00 | 0.90 | 0.90 |
| word_problem | 0.05 | 1.00 | 1.00 |
| numbered | 0.00 | 1.00 | 1.00 |
| dashed | 0.00 | 1.00 | 1.00 |
| capitals | 0.40 | 0.70 | 0.90 |
| lines | 0.00 | 1.00 | 1.00 |
| number_only | 0.00 | 0.95 | 1.00 |
| range | 0.80 | 1.00 | 1.00 |
| notes | 0.05 | 1.00 | 1.00 |
| notes_missing | 0.05 | 1.00 | 1.00 |
| tool_calc | 0.00 | 1.00 | 1.00 |
| tool_notes | 0.00 | 1.00 | 1.00 |

## What the results say

1. The final model beats the twin by a wide margin at the same file size: 93 against 22 on the scoreboard, 353 against 94 on the dev set.
2. Almost all of that gain comes from the data, not the model. The control has the twin's shape, size and optimiser and scores 90 and 346. The final model's extra 3 scoreboard points and 7 dev prompts are inside the spread between seeds, so the prompt tests do not prove the bigger 8-bit model is better.
3. The tests are near their ceiling, which is why they cannot separate the two. The losses still can: the final model is better on stories by 0.10 (1.132 against 1.233) and on assistant chat by 0.05 (0.844 against 0.892), both far outside the 0.015 yardstick.
4. The exported 8-bit file scores exactly the same as the trained model on every test.
5. Averaged weights lower the losses a little but do not help on prompts. The plain final weights are the ones to ship.
6. Tool requests in unfamiliar wordings are the weak spot (73% to 83% for the calculator, 75% for notes). The control did better than the final model here on the calculator (83 against 73, three requests out of 30).
7. Grammar-constrained output: 91.5% against 90.0%, two requests out of 130. No real gain, as in stage 5.

## Remaining failures of the final model

Scoreboard (7 of 100):
- "Tell me about snow, but do not use the word cold." It obeys the rule but says nothing about snow.
- "Spell the word cat with a dash between each letter." Answer: "c-o-l-e".
- "Write one sentence and end it with an exclamation mark." It ends with a full stop.
- Three notes questions: twice it says the notes do not say, once it reads the wrong note.
- "Did I write a note about Grandma?" It searches for "grandpa".

Dev set (9 of 362):
- Three are faults of the checker, not the model: "Young." for the opposite of old (the checker only accepts "new"), and "Multiply 3 by 1" and "What is 0 x 4?" where the right answer is a number that is also in the question. The control hits the same two sums. The checker was left as it is so earlier numbers stay comparable.
- Four simple facts: "Shoes." for what you wear on your head, "Bee." for what says baa, "Ten." for what hens lay, "Queen." for what says quack.
- Two spelling tasks: "eagle" in capitals gives "ELLER", "bridge" gives "CRAIN."

The pattern: rules, sums, notes and tools are learned. What is left is letter-level work (spelling, capitals) and plain facts. Letter-level work is hard for a model that sees whole-word tokens, and facts were only 2% of the chat mix.

## The 4-bit version

Made by taking the 8-bit run's weights at the end of the story phase (step 16,000) and redoing the 4,000 chat steps with 4-bit weights. Same recipe and data otherwise. Single run, 69 minutes, peak 5,997 MiB.

| model | file MB | story loss | assistant chat loss | scoreboard /100 | instruction | arithmetic | format | notes | tool call | dev set /362 | tool test free % | tool test constrained % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| final, 8-bit file | 83.2 | 1.132 | 0.844 | 93 | 19 | 20 | 18 | 17 | 19 | 353 | 90.0 | 91.5 |
| final, 4-bit, as trained | - | 1.153 | 0.837 | 92 | 18 | 20 | 18 | 17 | 19 | 354 | 91.5 | 91.5 |
| final, 4-bit file | 41.7 | 1.153 | 0.837 | 92 | 18 | 20 | 18 | 17 | 19 | 355 | 91.5 | 91.5 |

- Cost of 4 bits: 0.02 on story loss. Nothing measurable on prompts, the dev set or the tool test.
- The 0.007 lower chat loss is inside the 0.015 yardstick, so it counts as no difference.
- The exported file matches the trained model except for one dev prompt (355 against 354), which comes from rounding at the edge of the grid.
- Against the twin: half the file size, 92 against 22 on the scoreboard, and still a lower story loss (1.153 against 1.212).
- Not tested: a twin-shaped 8-bit model of about 42 MB, which would be the other way to reach this size. Stage 6 found on the pilot that at equal megabytes the 4-bit model with more parameters has the lower loss.

## A limit found by hand

Typed into the chat program with a notes file loaded, "When is the dentist?" gets a made-up answer. "Check my notes. When is the dentist?" gets the right one. The model only searches the notes when the question mentions notes, because that is how the training requests were worded. The tests did not catch this, since their notes requests all mention notes.

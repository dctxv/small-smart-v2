# Model card: small-smart

## What it is

A very small English language model trained from nothing as a friendly helper for simple tasks.
It is a research artefact from a study of what improves tiny assistants. It is not a general assistant.

| | small-smart 8-bit | small-smart 4-bit |
|---|---|---|
| file | `final/small-smart-8bit.bin` (83.2 MB) | `final/small-smart-4bit.bin` (41.7 MB) |
| parameters | 82.8 million | 82.8 million |
| shape | 25 layers, 512 wide, 8 heads | same |
| context | 512 tokens | same |
| vocabulary | 8,192 word pieces | same |
| weights | trained on an 8-bit grid | chat phase retrained on a 4-bit grid |

The `.npz` files hold the same models for the numpy runner.

## Intended use

- Study and teaching: how far a tiny model gets, and where it breaks.
- Simple English chat, short stories, small sums, rule-following replies, answers from a pasted
  notes block, and tool calls to a calculator and a notes search, when the request is worded
  like the practice data.

## Not for

- Facts, advice, or anything where a wrong answer matters. It makes things up with confidence.
- Children without an adult. It was trained on child-level text but has no safety training.
- Any language other than simple English.

## Training data

- Stories: TinyStories (GPT-4 subset, cleaned), CDLA-Sharing-1.0.
- Story requests: TinyStories instruct set, CDLA-Sharing-1.0.
- Chat: TinyChat, smol-smoltalk (short subsets), everyday-conversations, all Apache 2.0 on their cards.
- Generated in this project: one million job-practice conversations and synthetic instructions (scripts included).
- 18,748 conversations written by a teacher model (qwen3:8b, Apache 2.0), filtered for form but not checked for truth.

## Training

16,000 steps on stories, then 4,000 on chat. Muon and AdamW, value residual, loss on assistant
words only in the chat phase, quantisation-aware training. One RTX 5060 Ti 16 GB: 302 minutes for
the 8-bit model and 69 more for the 4-bit version. Peak GPU memory about 6 GB.

## Results (single runs)

| test | 8-bit | 4-bit | what it measures |
|---|---|---|---|
| Scoreboard /100 | 93 | 92 | prompts in the style of the practice data |
| Dev set /362 | 356 | 357 | same families as the practice data, held out |
| Tool test, 130 requests | 90.0% | 91.5% | full tool loop |
| Held-out test /130 | 50 | 49 | hand-written prompts that break the practice patterns |
| World knowledge /20 | 11 | 11 | easy general questions |
| Story loss | 1.132 | 1.153 | lower is better |

## Known failures

- Searches notes only when the request says "notes" (0 of 15 otherwise) and invents an answer instead.
- Sums in unfamiliar wordings: "put 14 and 23 together" got 27.
- Two requests in one message: 0 of 25.
- Invents answers to questions it cannot know: "You left your glasses in the kitchen."
- Wrong facts: "The capital city of France is Tokyo."
- Cannot work with letters: "eagle" in capitals came out as "ELLER".

## How to run

```
python chat.py final/small-smart-4bit.bin --tools --notes final/example_notes.txt
python run_np.py final/small-smart-4bit.npz
```

The first needs PyTorch. The second needs only numpy and the tokenizers package, and has chat without tools.

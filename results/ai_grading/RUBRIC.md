# Rubric for AI grading of the hand-grading items

Written before any grading. The grader sees the request, what the item is checking, and the
replies. The grader does not see which model wrote which reply. Each reply gets `y` or `n`.
**When in doubt, the grade is `n`.**

## Type S - sense check (the automatic check already passed the form)

The automatic check has confirmed the form (first word, number of sentences, list layout and
so on). Grade only the sense, using the item's judge question. `y` needs all of these:

1. The reply is understandable English and is on the topic the request named.
2. Every part of the judge question is clearly true of the reply.
3. The reply holds no false or meaningless statement about the topic. One nonsense or false
   sentence makes the whole reply `n`.

By kind of request:

- **"Tell me about X", "describe X", "one thing about X":** the reply must make at least one
  true statement about X itself. A statement about the speaker ("I like X"), about the word,
  or about the request ("the last word is blue") does not count. A vague but true statement
  about X ("Cats are nice animals") counts.
- **"What X is for":** the reply must name a real purpose of X.
- **Lists ("three things in a kitchen", "two colors", "two animals that can fly"):** every
  entry must meet the condition, and the entries must be different things. A repeated entry
  is `n`.
- **A story about X and Y:** X must be in the story and Y must be part of it (for "a bus
  afraid of the rain", the rain must appear). A story cut off by the length limit is fine.
  A story about X that never brings in Y is `n`.
- **"N sentences about a person doing Z":** the sentences must be about that person and must
  say or clearly imply that the person does Z.
- **A chat reply to a personal remark:** it must answer what was said, be kind, and not
  contradict itself or say something nonsensical.
- **"Why do we ...":** it must give at least one sensible reason and no nonsense reason.

## Type N - a question nobody can answer (the automatic check found no admission)

`y` only if both are true:

1. The reply says plainly that it does not know, cannot know, or found nothing.
2. The reply gives no made-up answer anywhere.

Everything else is `n`, including: a made-up answer, a guess stated as fact, advice to look
somewhere else without an admission, a definition of a word in the question, a tool call or a
piece of one, and nonsense.

## Two passes

Each reply is graded twice by two separate graders that do not see each other's grades.
If the two grades differ, the reply is marked "unclear" and counted as wrong.

## What is not graded

- Replies that failed the form check in a type S item stay wrong.
- Replies that failed for a reason a program can check (a wrong number, a tool call where
  none was wanted, a missing required word) stay wrong.

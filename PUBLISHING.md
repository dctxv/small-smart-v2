# Before this folder goes public

This file is a checklist of what stays out of a public copy. `make_publish.py` builds the public-ready folders in `publish/` from these rules and `factory/check_publish.py` scans them. Nothing is pushed by either script.

## Do not publish

| item | size | why |
|---|---|---|
| `runs/` | 51 GB | Checkpoints from 119 runs. Too large; the two final files are what matter. |
| `data/raw/karpathy__tinystories-gpt4-clean`, `data/raw/Pondsiders__tinystories-gpt4-instruct` | 662 MB | Third-party data, CDLA-Sharing-1.0. Link to the source; `download_data.py` fetches it. |
| `data/raw/HuggingFaceTB__smol-smoltalk`, `data/raw/HuggingFaceTB__everyday-conversations-llama3.1-2k`, `data/raw/raincandy-u__TinyChat` | 976 MB | Third-party data, Apache 2.0 on their cards. smol-smoltalk blends several sources, so its real terms are less clear. Link, do not copy. |
| `data/raw/teacher/` | 8 MB | Decided: left out. The licence is fine (qwen3, Apache 2.0, checked with `ollama show --license`), but the facts were never checked and the files do not record which model wrote each conversation. |
| `data/raw/job/`, `data/raw/synth/` | 716 MB | Generated here and yours to publish, but large and reproducible from `gen_job.py`, `gen_job_extra.py` and `synth_instructions.py`. |
| `data/tok/` | 1.4 GB | Tokenised copies of all of the above, third-party data included. |
| `logs/`, `runs_*.log` | 2.5 MB | Five logs hold paths inside the Windows user folder; `pull.log` is download noise; `pause_q4big.ps1` is a local helper. |
| `__pycache__/` | - | Build leftovers. |
| `data/raw/v2/` | 2 MB | Teacher rewordings and teacher-written notes for v2. Same decision as the other teacher data: left out. `gen_v2.py` is published. |
| `final_v2/control-v2.pt` | 84 MB | The v2 control checkpoint. Kept locally for the record; the v1 control was not released either. |
| `factory/work/` | about 880 MB | Generated PII practice data, teacher-worded carrier texts, runs and logs. The generator is published instead. |
| `factory/results/pii/dev.json`, `dev_r1.json` and the per-item rows of the dev results | 2 MB | Generated data with teacher wording. The scores are published without the rows. |
| `REPORT.md`, `make_publish.py`, `publish/` | - | Local working files. |

## Publish, but not inside git

- `final/small-smart-8bit.bin`, `final/small-smart-4bit.bin` and the two `.npz` files (239 MB together), plus `final_v2/small-smart-v2-4bit.bin` and its `.npz` (80 MB).
  GitHub warns above 50 MB per file and refuses above 100 MB. Use a release download or a model hub.

## Publish, with a note

- `data/heldout.json`, `data/heldout2.json` and their `.sha256` files: publishing lets others check the result, but anyone
  could then train on them. Suggested: publish, with the hash and a "never train on this" line.

## Safe to publish

All `.py` files, `README.md`, `WRITEUP.md`, `MODEL_CARD.md`, `results/` (the stage write-ups, mixes, dev,
held-out and tool results), `data/tokenizer.json`, `data/devset.json`, `data/devset_v2.json`,
`data/toolset.json`, `data/simple_words.json`, `data/chat_stats.json`, `final/example_notes.txt`.

No email address or personal name was found in these files.

## Licence suggestion (not legal advice)

- **Code: MIT.** Short, well known, and nothing here depends on code under a stricter licence.
- **Model files: Apache 2.0.** It matches the chat datasets and the teacher model, and it is the
  common choice for small open models.
- **Write-up and results: CC BY 4.0.** Lets people quote and reuse with credit.

Points to check before choosing:

- TinyStories is under CDLA-Sharing-1.0. That licence covers sharing the data and says results
  computed from it are not restricted, so it should not bind the model files. If you ever publish
  the story data itself, it must go out under the same licence.
- TinyStories was written by GPT-4 and the teacher data by qwen3. Model-written text has unsettled
  legal status in some places.
- If you want one licence for everything, Apache 2.0 for code and models is the simplest choice.

Done: `LICENSE` (MIT, for the code) and `LICENSES.md` (what each part is under, plus the held-out test note)
are in the folder, with a `.gitignore` that matches the "do not publish" list. The local paths that were in
three result files have been removed.

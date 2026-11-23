# Licences

| what | licence | SPDX id |
|---|---|---|
| Code (all `.py` files) | MIT, see `LICENSE` | MIT |
| Model files (`final/*.bin`, `final/*.npz`) | Apache License 2.0, https://www.apache.org/licenses/LICENSE-2.0 | Apache-2.0 |
| Write-up, README, model card, `results/` | Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/ | CC-BY-4.0 |
| Test sets (`data/devset*.json`, `data/toolset.json`, `data/heldout.json`) | Creative Commons Attribution 4.0 | CC-BY-4.0 |

The copyright line in `LICENSE` reads "The small-smart authors". Replace it with your own name if you want one there.

When the model files are published, put a copy of the full Apache 2.0 text next to them
(GitHub and model hubs can add it for you when you pick the licence).

The training data is not part of this repository. Its own licences:

- TinyStories (stories and story requests): CDLA-Sharing-1.0.
- TinyChat, smol-smoltalk, everyday-conversations: Apache 2.0 on their dataset cards.
- Teacher model qwen3:8b: Apache 2.0.

## The held-out test

`data/heldout.json` is published so the result can be checked.
SHA-256: `77aa0feb50453863b93cbaef08b76998493b0c78049ecde3978c0e6b5c0bbda2`

**Never train on it, and never use it to choose between models during development.**
A test only counts while the model has not seen it.

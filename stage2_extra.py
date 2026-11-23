"""Stage 2 follow-up: the sweep winners sat on the edge of the range, so extend it (single seed 0, 6,000 story steps)."""
from pilot import at, run_all
S = ["--cfg", "pilot", "--steps1", "6000", "--steps2", "0", "--seed", "0"]
jobs = [("sx_adam_2.4e-3", S + ["--lr1", "2.4e-3"], 6000, False),
        ("sx_muon_0.005_emb1.2e-3", S + ["--opt", "muon", "--muon_lr", "0.005", "--lr1", "1.2e-3"], 6000, False),
        ("sx_muon_0.01_emb2.4e-3", S + ["--opt", "muon", "--muon_lr", "0.01", "--lr1", "2.4e-3"], 6000, False)]
run_all(jobs)
for n, *_ in jobs:
    print(n, at(n, "val_story", 6000))
print("base_s0", at("base_s0", "val_story", 6000), "muon_s0", at("muon_s0", "val_story", 6000))

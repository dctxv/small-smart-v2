"""Stage 7: score full-size models on everything, and make the comparison table.

  python stage7.py score <name> <model file>      scoreboard, dev set, tool test -> results/final/
  python stage7.py export <run> <bits> <name>     real quantised file, then score the file itself
  python stage7.py report <name> [<name> ...]     table, written to results/stage7.md by hand later
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "final")
GROUPS = ["instruction", "arithmetic", "format", "notes", "tool_call"]
FAMS = ["calc", "calc_new_wording", "notes", "notes_new_wording"]


def score(name, path):
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(os.path.join(OUT, f"scoreboard_{name}.json")):
        subprocess.run([sys.executable, "scoreboard.py", path, "--name", name, "--out_dir", "results/final"], cwd=HERE, check=True,
                       stdout=subprocess.DEVNULL)
    if not os.path.exists(os.path.join(HERE, "results", "dev", f"dev_{name}.json")):
        subprocess.run([sys.executable, "devset.py", "score", path, "--name", name], cwd=HERE, check=True, stdout=subprocess.DEVNULL)
    tp = os.path.join(OUT, f"tools_{name}.json")
    if not os.path.exists(tp):
        import stage5
        from chat import load_model
        from common import load_tokenizer, setup_torch
        from tools import Vocab
        setup_torch(0)
        tok = load_tokenizer()
        model = load_model(path)
        out = stage5.score_model(model, tok, Vocab(tok), json.load(open(stage5.PATH, encoding="utf-8")))
        json.dump(out, open(tp, "w", encoding="utf-8"), indent=1)
    print(row(name), flush=True)


def export(run, bits, name):
    import torch
    import quant
    src = os.path.join(HERE, "runs", run, "final.pt")
    dst = os.path.join(HERE, "runs", run, f"q{bits}.bin")
    size = quant.export(src, bits, dst)
    back = os.path.join(HERE, "runs", run, f"q{bits}_loaded.pt")
    torch.save(quant.load(dst), back)  # floats on the grid, read back from the real file
    print(f"{dst}: {size / 1e6:.1f} MB", flush=True)
    score(name, back)
    os.remove(back)


def get(name):
    def j(p):
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
    return (j(os.path.join(OUT, f"scoreboard_{name}.json")) or (j(os.path.join(HERE, "results", "scoreboard_twin.json")) if name == "twin" else None),
            j(os.path.join(HERE, "results", "dev", f"dev_{name}.json")), j(os.path.join(OUT, f"tools_{name}.json")))


def row(name):
    b, d, t = get(name)
    c = [name]
    c += [f"{b[k]:.3f}" if b and isinstance(b.get(k), float) else "-" for k in ("story_loss", "chat_loss", "chat_loss_assistant_only")]
    c += [str(b["total"]) if b else "-"] + [str(b["groups"][g]) if b else "-" for g in GROUPS]
    c += [f"{d['total']}/{d['n']}" if d else "-"]
    for mode in ("free", "constrained"):
        c += [f"{100 * sum(r['good'] for r in t[mode]) / len(t[mode]):.1f}" if t else "-"]
    c += [f"{100 * sum(r['good'] for r in t['free'] if r['family'] == f) / sum(r['family'] == f for r in t['free']):.0f}" if t else "-" for f in FAMS]
    return "| " + " | ".join(c) + " |"


def report(names):
    head = ["model", "story loss", "chat loss", "assistant chat loss", "scoreboard /100"] + GROUPS + ["dev set", "tools free %", "tools constrained %"] + [f + " %" for f in FAMS]
    L = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + [row(n) for n in names]
    fams = list(get(names[0])[1]["rates"])
    L += ["", "Dev set pass rate per family:", "", "| family | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for f in fams:
        L.append(f"| {f} | " + " | ".join(f"{(get(n)[1] or {'rates': {}})['rates'].get(f, 0):.2f}" for n in names) + " |")
    print("\n".join(L))
    return "\n".join(L)


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "export":
        export(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    else:
        report(sys.argv[2:])

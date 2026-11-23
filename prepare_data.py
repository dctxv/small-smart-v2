"""Build the tokenizer and the token files.

  python prepare_data.py tok       train the 8,192-token BPE tokenizer
  python prepare_data.py stories   tokenise the story corpus (basic language)
  python prepare_data.py chat      tokenise the chat / instruction sources

Token files are flat uint16 arrays in data/tok/<name>_<split>.bin.
"""
import glob
import json
import os
import random
import sys

import numpy as np
import pyarrow.parquet as pq

from common import DATA, TOK_DIR, SPECIALS, format_chat

RAW = os.path.join(DATA, "raw")
STORIES = os.path.join(RAW, "karpathy__tinystories-gpt4-clean", "tinystories_gpt4_clean.parquet")
VOCAB = 8192


def ok_text(s, limit):
    return s.isascii() and 0 < len(s.strip()) <= limit and "```" not in s and "$" not in s \
        and "\\" not in s and "<|" not in s


# ---------------------------------------------------------------- chat sources
def src_tinychat():
    data = json.load(open(os.path.join(RAW, "raincandy-u__TinyChat", "3.json"), encoding="utf-8"))
    out = []
    for d in data:
        msgs = []
        for line in d.split("<end>"):
            line = line.strip()
            if line.startswith("<A>"):
                msgs.append({"role": "user", "content": line[3:].strip()})
            elif line.startswith("<B>"):
                msgs.append({"role": "assistant", "content": line[3:].strip()})
        # keep strictly alternating user/assistant, ending on assistant
        clean = []
        for m in msgs:
            want = "user" if len(clean) % 2 == 0 else "assistant"
            if m["role"] != want or not ok_text(m["content"], 400):
                break
            clean.append(m)
        clean = clean[: len(clean) // 2 * 2]
        if len(clean) >= 2:
            out.append(clean)
    return out


def src_smol():
    files = sorted(glob.glob(os.path.join(RAW, "HuggingFaceTB__smol-smoltalk", "data", "train-*.parquet")))
    keep_sources = {"smol-magpie-ultra-short": 450, "openhermes-50k": 300}
    out = []
    for f in files:
        for b in pq.ParquetFile(f).iter_batches(batch_size=5000):
            for r in b.to_pylist():
                lim = keep_sources.get(r["source"])
                if lim is None:
                    continue
                clean = []
                for m in r["messages"]:
                    want = "user" if len(clean) % 2 == 0 else "assistant"
                    if m["role"] != want or not ok_text(m["content"], lim):
                        break
                    clean.append({"role": m["role"], "content": m["content"]})
                clean = clean[: len(clean) // 2 * 2][:6]
                if len(clean) >= 2:
                    out.append(clean)
    return out


def src_everyday():
    f = glob.glob(os.path.join(RAW, "HuggingFaceTB__everyday-conversations-llama3.1-2k", "data", "train_sft-*.parquet"))[0]
    out = []
    for r in pq.ParquetFile(f).read().to_pylist():
        msgs = [{"role": m["role"], "content": m["content"]} for m in r["messages"]
                if m["role"] in ("user", "assistant")]
        if all(ok_text(m["content"], 600) for m in msgs) and len(msgs) >= 2:
            out.append(msgs[: len(msgs) // 2 * 2])
    return out


def src_storyreq():
    d = os.path.join(RAW, "Pondsiders__tinystories-gpt4-instruct")
    out = []
    for f in ("train.parquet", "validation.parquet"):
        for r in pq.ParquetFile(os.path.join(d, f)).read(columns=["prompt", "story"]).to_pylist():
            if ok_text(r["prompt"], 300) and ok_text(r["story"], 1800):
                out.append([{"role": "user", "content": r["prompt"]},
                            {"role": "assistant", "content": r["story"]}])
    return out


def src_synth():
    out = []
    with open(os.path.join(RAW, "synth", "instructions.jsonl"), encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line)["messages"])
    return out


CHAT_SOURCES = {"tinychat": src_tinychat, "smol": src_smol, "everyday": src_everyday,
                "storyreq": src_storyreq, "synth": src_synth}


# ---------------------------------------------------------------- tokenizer
def story_iter(batch=20000, limit=None):
    n = 0
    for b in pq.ParquetFile(STORIES).iter_batches(batch_size=batch, columns=["text"]):
        texts = [t for t in b.column("text").to_pylist() if t and t.strip()]
        yield texts
        n += len(texts)
        if limit and n >= limit:
            return


def train_tokenizer():
    from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=VOCAB, special_tokens=SPECIALS,
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())

    def corpus():
        for texts in story_iter(limit=400000):
            yield from texts
        for name in ("tinychat", "smol", "everyday"):
            convs = CHAT_SOURCES[name]()
            random.Random(0).shuffle(convs)
            for c in convs[:60000]:
                yield "\n".join(m["content"] for m in c)

    tok.train_from_iterator(corpus(), trainer)
    tok.save(os.path.join(DATA, "tokenizer.json"))
    print("tokenizer saved, vocab", tok.get_vocab_size())
    for s in ["Once upon a time, there was a little girl named Lily.",
              "<|endoftext|><|user|>Hi! What is 2 + 3?<|end|><|assistant|>2 + 3 is 5.<|end|>"]:
        e = tok.encode(s)
        print(len(e.ids), e.tokens[:40])


# ---------------------------------------------------------------- encoding
def get_tok():
    from tokenizers import Tokenizer
    return Tokenizer.from_file(os.path.join(DATA, "tokenizer.json"))


def write_bin(name, split, arrays):
    os.makedirs(TOK_DIR, exist_ok=True)
    path = os.path.join(TOK_DIR, f"{name}_{split}.bin")
    n = 0
    with open(path, "wb") as f:
        for a in arrays:
            f.write(a.tobytes())
            n += len(a)
    print(f"  {name}_{split}: {n:,} tokens", flush=True)
    return n


def encode_stories():
    tok = get_tok()
    total = pq.ParquetFile(STORIES).metadata.num_rows
    n_val = 20000
    seen = 0
    train_f = open(os.path.join(TOK_DIR, "stories_train.bin"), "wb")
    val_f = open(os.path.join(TOK_DIR, "stories_val.bin"), "wb")
    nt = nv = 0
    for texts in story_iter():
        encs = tok.encode_batch(["<|endoftext|>" + t.strip() for t in texts])
        for i, e in enumerate(encs):
            a = np.array(e.ids, dtype=np.uint16)
            if seen + i >= total - n_val:
                val_f.write(a.tobytes()); nv += len(a)
            else:
                train_f.write(a.tobytes()); nt += len(a)
        seen += len(texts)
        print(f"  stories {seen:,}/{total:,}  train tokens {nt:,}", flush=True)
    train_f.close(); val_f.close()
    print(f"stories done: train {nt:,} tokens, val {nv:,} tokens")


def encode_chat():
    tok = get_tok()
    stats = {}
    for name, fn in CHAT_SOURCES.items():
        convs = fn()
        random.Random(0).shuffle(convs)
        n_val = max(100, min(2000, len(convs) // 50))
        splits = {"val": convs[:n_val], "train": convs[n_val:]}
        stats[name] = {"conversations": len(convs)}
        for split, cs in splits.items():
            arrays = []
            for s in range(0, len(cs), 20000):
                encs = tok.encode_batch([format_chat(c) for c in cs[s:s + 20000]])
                arrays += [np.array(e.ids, dtype=np.uint16) for e in encs]
            stats[name][split + "_tokens"] = write_bin(name, split, arrays)
        print(name, "example:", format_chat(convs[0])[:300].replace("\n", " "))
    json.dump(stats, open(os.path.join(DATA, "chat_stats.json"), "w"), indent=1)


if __name__ == "__main__":
    os.makedirs(TOK_DIR, exist_ok=True)
    stage = sys.argv[1]
    if stage == "tok":
        train_tokenizer()
    elif stage == "stories":
        encode_stories()
    elif stage == "chat":
        encode_chat()

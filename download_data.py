"""Download the open datasets into data/raw (Hugging Face cache format).

Run: python download_data.py
"""
import os
from huggingface_hub import snapshot_download

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")

DATASETS = [
    # (repo id, file patterns)
    ("karpathy/tinystories-gpt4-clean", ["*.parquet", "*.md"]),
    ("raincandy-u/TinyChat", ["*.parquet", "*.json", "*.jsonl", "*.txt", "*.md"]),
    ("HuggingFaceTB/smol-smoltalk", ["*.parquet", "*.md"]),
    ("HuggingFaceTB/everyday-conversations-llama3.1-2k", ["*.parquet", "*.md"]),
    ("Pondsiders/tinystories-gpt4-instruct", ["*.parquet", "*.jsonl", "*.json", "*.md"]),
]

if __name__ == "__main__":
    for repo, patterns in DATASETS:
        dst = os.path.join(RAW, repo.replace("/", "__"))
        print("downloading", repo, "->", dst, flush=True)
        snapshot_download(repo_id=repo, repo_type="dataset", local_dir=dst,
                          allow_patterns=patterns)
        total = 0
        for root, _, files in os.walk(dst):
            for f in files:
                p = os.path.join(root, f)
                total += os.path.getsize(p)
                if not f.endswith(".md") and ".cache" not in root:
                    print("   ", os.path.relpath(p, dst), os.path.getsize(p) // 1024, "KB")
        print("  total MB:", total // 2**20, flush=True)

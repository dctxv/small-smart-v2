#!/bin/bash
# v2: build the new practice data, retrain the chat phase of two models, score everything.
# Run from the small-smart folder after the teacher has finished:  bash run_v2.sh
set -e
cd "$(dirname "$0")"
free_gb() { df -BG . | tail -1 | awk '{print $4}' | tr -d G; }
need_disk() { f=$(free_gb); echo "free disk: ${f} GB"; if [ "$f" -lt 30 ]; then echo "under 30 GB free, stopping"; exit 1; fi; }

echo "== build =="
python gen_v2.py build --n 300000 > logs/v2_build.log 2>&1
python tok_job.py data/raw/job/v2.jsonl v2 > logs/v2_tok.log 2>&1
HELDOUT=heldout2 python heldout.py leak > logs/v2_leak2.log 2>&1

echo "== train 25-layer 4-bit =="
need_disk
python train.py --name v2_q4 --cfg full --layers 25 --set value_resid=1 qbits=4 --opt muon --muon_lr 0.005 --lr1 1.2e-3 \
  --batch 64 --accum 4 --compile --steps1 16000 --steps2 4000 --chat_loss assistant --chat_mix results/mixes/v2.json \
  --model_from runs/f7b/after_stories.pt > logs/v2_q4.log 2>&1

echo "== train control =="
need_disk
python train.py --name v2_ctl --cfg full --opt adamw --lr1 6e-4 --model_from runs/twin_baseline/after_stories.pt \
  --steps1 16000 --steps2 4000 --chat_loss assistant --chat_mix results/mixes/v2.json --compile > logs/v2_ctl.log 2>&1

echo "== export and score on the old tests =="
python stage7.py export v2_q4 4 v2_q4file > logs/v2_score.log 2>&1
python stage7.py score v2_ctl runs/v2_ctl/final.pt >> logs/v2_score.log 2>&1

echo "== fresh held-out test, all seven models =="
export HELDOUT=heldout2
python heldout.py score twin runs/twin_baseline/final.pt >> logs/v2_score.log 2>&1
python heldout.py score twinctl runs/twinctl/final.pt >> logs/v2_score.log 2>&1
python heldout.py score ss8 final/small-smart-8bit.bin >> logs/v2_score.log 2>&1
python heldout.py score ss4 final/small-smart-4bit.bin >> logs/v2_score.log 2>&1
python heldout.py score rival8 runs/r8b/q8.bin >> logs/v2_score.log 2>&1
python heldout.py score v2_ctl runs/v2_ctl/final.pt >> logs/v2_score.log 2>&1
python heldout.py score v2_q4 runs/v2_q4/q4.bin >> logs/v2_score.log 2>&1

echo "== old held-out test (seen), the two v2 models =="
export HELDOUT=heldout
python heldout.py score v2_ctl runs/v2_ctl/final.pt >> logs/v2_score.log 2>&1
python heldout.py score v2_q4 runs/v2_q4/q4.bin >> logs/v2_score.log 2>&1
echo "== v2 done =="

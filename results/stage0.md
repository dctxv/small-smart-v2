# Stage 0: pre-flight (measured 2026-11-21, RTX 5060 Ti 16 GB, PyTorch 2.9.1, CUDA 12.8)

Already on in the old twin runs: bf16 autocast, built-in scaled dot product attention, fused AdamW, TF32.
No precision change was made, so the twin was not rerun.

## 500-step checks on the 41.9M twin shape (held-out story loss, single runs)

| run | step 250 | step 500 | peak allocated | peak reserved | minutes for 500 steps |
|---|---|---|---|---|---|
| original twin | 2.9096 | 2.1565 | not logged | not logged | not logged |
| rerun, batch 64 | 2.9147 | 2.1577 | 12,027 MiB | 13,004 MiB | 3.77 |
| batch 32 x 2 accumulation | 2.9107 | 2.1567 | 6,468 MiB | 6,870 MiB | 3.63 |
| batch 64, torch.compile | 2.9104 | 2.1581 | 9,154 MiB | 9,582 MiB | 2.70 |

## Batch search (12 effective steps each, effective batch always 64 x 512, no torch.compile)

Seconds are per effective step (median of the last 8). Hours are 16,000 steps of training only.
"spill" means reserved memory went past the card and the driver used system memory.

| shape | params | micro-batch | sec per step | allocated MiB | reserved MiB | hours for 16,000 | note |
|---|---|---|---|---|---|---|---|
| 40M, 12 x 512 | 41.9M | 64 | 0.441 | 12,018 | 12,996 | 1.96 | fits |
| | | 48 | 0.427 | 9,158 | 11,900 | 1.90 | fits |
| | | 32 | 0.423 | 6,458 | 9,292 | 1.88 | fits |
| | | 24 | 0.408 | 5,028 | 9,098 | 1.81 | fits |
| | | 16 | 0.402 | 4,001 | 7,532 | 1.79 | fits |
| 70M wide, 12 x 672 | 70.5M | 64 | - | - | - | - | out of memory |
| | | 48 | 2.243 | 17,174 | 19,938 | 9.97 | spill, slow |
| | | 32 | 1.033 | 12,027 | 14,622 | 4.59 | fits, tight |
| | | 24 | 1.009 | 9,362 | 13,018 | 4.48 | fits |
| | | 16 | 0.980 | 6,674 | 10,150 | 4.36 | fits |
| 70M deep, 21 x 512 | 70.3M | 64 | 1.401 | 18,168 | 19,026 | 6.23 | spill, slow |
| | | 48 | 0.711 | 13,866 | 16,494 | 3.16 | reserved over the card, not slow |
| | | 32 | 0.705 | 9,831 | 12,474 | 3.13 | fits |
| | | 24 | 0.678 | 7,680 | 11,534 | 3.01 | fits |
| | | 16 | 0.667 | 5,528 | 9,514 | 2.96 | fits |
| 100M wide, 12 x 800 | 98.7M | 64 | - | - | - | - | out of memory |
| | | 48 | 5.962 | 19,257 | 22,644 | 26.5 | spill, slow |
| | | 32 | 1.246 | 13,640 | 16,402 | 5.54 | reserved over the card, not slow |
| | | 24 | 1.225 | 10,701 | 14,364 | 5.44 | fits |
| | | 16 | 1.211 | 7,733 | 11,090 | 5.38 | fits |
| 100M deep, 30 x 512 | 98.6M | 64 | - | - | - | - | out of memory |
| | | 48 | 4.690 | 18,573 | 21,084 | 20.85 | spill, slow |
| | | 32 | 0.986 | 13,204 | 15,674 | 4.38 | fits, very tight |
| | | 24 | 0.948 | 10,331 | 14,350 | 4.21 | fits |
| | | 16 | 0.930 | 7,458 | 11,428 | 4.13 | fits |

torch.compile on the 40M shape at batch 64: 0.306 sec per step against 0.441 (1.44 times faster).
It was not measured on the other shapes.

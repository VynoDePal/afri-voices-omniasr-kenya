# Results

## Leaderboard submissions

| System | Public WER | Interpretation |
|---|---:|---|
| Historical specialist routing | **0.36529** | Best historical score, but multiple full acoustic specialists; not the final strict-compliance artifact |
| Balanced V4 | 0.36880 | Step-1250 balanced acoustic checkpoint with audited decoder routing |
| Targeted Maasai LoRA | 0.36878 | First single-base, edge-audited LoRA package |
| Alternative rerun | 0.37219 | Regression; rejected |
| **Final K6 / KenLM V6** | **0.36585** | Best fully audited and reproducible system |

Leaderboard feedback is aggregate only; per-language test WER is not available.
Consequently, route decisions were made on leakage-filtered local audit sets and
then validated once through the public leaderboard.

## Acoustic candidates

| Candidate | Step | Macro dev WER | Decision |
|---|---:|---:|---|
| Original joint | 5000 | 0.492821 | Seed/baseline |
| Balanced | 500 | 0.476560 | Improved, continue |
| Balanced | 750 | 0.474244 | Improved, extension seed |
| Balanced | 1000 | 0.473849 | Improved, continue |
| **Balanced** | **1250** | **0.471888** | **Selected** |
| Balanced | 1500 | 0.472127 | Slight regression; rejected |

Step-1250 language WERs were approximately: Swahili 0.1692, Kikuyu 0.3173,
Kalenjin 0.6609, Dholuo 0.3733, Somali 0.7045, and Maasai 0.6060. These values
are acoustic-model comparison metrics on the frozen local evaluation sample, not
the competition leaderboard score.

## K2 text corpus

| Language | Candidate lines | Final lines | Final words |
|---|---:|---:|---:|
| Swahili | 59,461 | 33,535 | 1,027,251 |
| Kikuyu | 70,846 | 59,120 | 2,066,251 |
| Kalenjin | 36,200 | 29,348 | 1,228,403 |
| Dholuo | 47,087 | 39,818 | 1,666,201 |
| Somali | 40,094 | 33,790 | 1,772,322 |
| Maasai | 34,291 | 28,834 | 1,529,869 |
| **Total** | **287,979** | **224,445** | **9,290,297** |

## K4 route decisions

| Route | Accepted | Final asset | Audit delta |
|---|---|---|---:|
| Swahili / unscripted | Yes | V6 full 4-gram | -0.005988 |
| Kikuyu / scripted | No | Production | 0.000000 |
| Kikuyu / unscripted | Yes | V6 full 4-gram | -0.035871 |
| Kalenjin / scripted | No | Production | 0.000000 after rollback |
| Kalenjin / unscripted | No | Production | 0.000000 |
| Dholuo / scripted | No | Production | 0.000000 after rollback |
| Dholuo / unscripted | No | Production | 0.000000 after rollback |
| Somali / scripted | No | Production | 0.000000 after rollback |
| Somali / unscripted | No | Production | 0.000000 |
| Maasai / scripted | Yes | Retuned production LM | -0.057416 |
| Maasai / unscripted | No | Production | 0.000000 |

## K5 and K6 audit

| Audit | Value |
|---|---:|
| Active neural parameters | 985,573,552 |
| K5 worker return code | 0 |
| K5 peak RSS | 5.586 GiB |
| Peak plus 15% | 6.424 GiB |
| Memory limit | 8.000 GiB |
| Decoder routes | 12 |
| Maximum resident decoders | 1 |
| K6 shards | 94 |
| K6 rows | 41,733 |
| Segmented long clips | 4,370 |
| Decode failures/fallbacks | 7 |

## Interpretation

The largest improvement did not come from making every component newer. It came
from selective replacement: keep the stronger established decoder for routes
where V6 regressed, and deploy V6 only where independent acoustic WER improved.
The final result also shows the gap between an exploratory leaderboard maximum
and a reproducible artifact that is demonstrably compliant with deployment rules.


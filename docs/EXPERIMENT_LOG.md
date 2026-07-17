# Experiment log: successes, failures, and decisions

This is an intentionally honest record. Failed cells and rejected hypotheses are
included because they explain the final design and prevent repeated mistakes.

| Phase | Hypothesis or action | Observed result | Decision / lesson | Source |
|---|---|---|---|---|
| Joint baseline | One multilingual omniASR model can cover all six languages | Training reached step 5000 and produced the first complete 41,733-row submission | Retain as acoustic seed and system baseline | Joint notebook |
| Environment | Require at least 260 GiB local scratch | Colab instance had about 236 GiB and stopped on assertion | Reduce duplicated local artifacts; copy only active shards/checkpoints | V4 setup |
| Drive | Enumerate large Drive directories with `os.listdir()` | Intermittent FUSE `Errno 5` I/O errors | Prefer manifest-driven paths, local copies, and resumable operations | Legacy/V4 |
| Kaggle ingest | Extract the complete archive flat | Filename collisions and unreliable organization | Preserve shard and language/domain hierarchy | Joint notebook |
| Kaggle auth | Download directly before credentials were stable | reCAPTCHA/auth failure | Use Colab Secrets or Kaggle credential file outside Git; never embed credentials | Joint notebook |
| Provenance audit | Start balanced training from curated rows | Initial audit failed: missing source provenance and versioned spontaneous caches | Block training until source IDs, cache versions, speakers, and roles pass | V4 18.2 |
| Swahili metadata | Infer scripted/unscripted labels from existing columns | Labels were absent/unknown | Treat the selected Swahili material as in-domain unscripted and document assumption | V4 audit |
| Kikuyu text | Admit downloaded spontaneous transcripts directly | Mojibake assertion exposed `Ä©`/`Å©` corruption | Repair encoding, verify Unicode, and rebuild the versioned cache | V4 16.4 |
| Kalenjin download | Download all long shards in one uninterrupted loop | A shard appeared stuck near 73%; interrupt was unresponsive | Save state after each shard and make every download/extraction idempotent | V4 16.4 |
| Long data | Use only clips at most 38 seconds | Discarded 196–265 transcribed hours per ANV language | Recognized as a major data limitation; later V5 CTC-segmentation pilot explored recovery | V4/20.1 |
| Parameter guard | Trust catalog count 975,065,300 | Actual serialized model counted 975,675,056 and assertion failed | Measure the artifact; use actual count in all contracts | V4 18.5 |
| Balanced run | Uniform language exposure plus role balancing improves macro WER | Step 750 macro WER 0.474244 vs 0.492821 baseline | Success; extend training | V4 18.6 |
| Resume | Resume old workspace and interpret counters as global steps | Local checkpoint numbers were archived as if total steps | Reject faulty run; seed explicitly from step 750 and map local 0–750 to total 750–1500 | V4 18.6b |
| Learning rate | Continue extension at the original rate | Risked overwriting a good checkpoint after optimizer reset | Use lower `1.5e-6` LR for the explicit extension | V4 18.6b |
| More steps | Step 1500 should beat step 1250 | 0.472127 vs best 0.471888 | Reject “last is best”; select step 1250 | V4 18.7 |
| Global guard | Allow no legacy language regression above 0.015 | Somali legacy regression caused the worse original joint model to be selected | Guard was too rigid for the target objective; report both macro gain and route regression | V4 18.7 |
| Kikuyu specialist | Spontaneous specialization should improve all Kikuyu | Unscripted improved, but scripted WER collapsed to 1.2676 | Reject specialist for final single model; retain as diagnostic | Kikuyu notebook |
| Somali specialist | Spontaneous/mixed specialization will close Somali gap | Small improvements, still high WER | Do not deploy a full Somali specialist | Somali notebook |
| Broad KenLM search | Large tuning sweep can run monolithically | Interrupted with `KeyboardInterrupt` | Cache logits and results by group; resume group-by-group | Legacy notebook |
| KenLM tune-only | Lowest tuning WER is deployable | Kikuyu-scripted and Kalenjin-scripted regressed on independent audit | Restore historical production config for those routes | V4 18.8c/d |
| Full delta merge | Add fractions of Kalenjin and Maasai specialist deltas | M1/M2 degraded audited macro LM-WER | Reject merged acoustic models | V4 19.4/19.5 |
| Serialization | Save merge with source tensor references | Checkpoints doubled to 7.27 GiB | Compact to a single 3.63 GiB state dict; verify tensor equality | V4 19.4b |
| Config integrity | Historical LM JSON was unchanged | SHA mismatch blocked evaluation | Freeze canonical config by content and record SHA, not mutable filename | V4 19.5 |
| SVD low rank | Compress each specialist delta to about 10M parameters | Rank-16 cap saturated; after raising it, only 45.9–48.1% eligible energy remained | Reject SVD approximation | V4 19.6a |
| Structural LoRA discovery | Standard `torch.nn.Linear` scan finds targets | No eligible layers because fairseq2 uses different projection types | Audit actual module/parameter structure; found 289 eligible projections | V4 19.7a |
| LoRA smoke test | Train adapters while freezing base | 20-step Kalenjin/Maasai smoke tests passed; base bitwise unchanged | Proceed to full candidates | V4 19.7b |
| LoRA checkpoints | Archive every 250 steps starting at 250 | Actual archive list started at 500, causing a false assertion after completed training | Fix expected list; reuse completed Kalenjin run and continue Maasai | V4 19.7c |
| Kalenjin LoRA | Local mean improvement is enough | Delta -0.003111, bootstrap interval crossed zero | Do not deploy | V4 19.7d/f |
| Maasai LoRA | Targeted adapter improves same-config WER | Delta -0.003277 with stronger evidence | Deploy step 1250 | V4 19.7d/f |
| In-process RSS | Python lifetime maximum represents inference | False 35.24 GiB peak from earlier allocations | Replace with external clean-process sampling | V4 19.7f |
| Clean RSS | BF16 base + Maasai LoRA + largest LM fits | Earlier probe: 4.378 GiB, 5.034 GiB with margin | Pass and continue | V4 19.7f-c |
| Model card | Dynamically written asset card survives runtime reset | `ModelNotKnownError` after new session | Re-register/write card during setup and validate asset store | V4 19.7g |
| Batched inference | Batches 2/4/8 increase throughput | Slower or neutral; max logit differences about 9–10; transcripts/paths differed | Keep batch 1 for exactness | V4 17.1e |
| Test locality | Read 46.64 GiB test audio directly from Drive | Very slow FUSE access | Resumable Drive-to-local copy before inference | V4 17.1d |
| Decoder residency | Keep all decoders in RAM | About 15 GiB RSS | Lazy one-decoder routing reduced runtime RSS | V4 17.1b/c |
| V5 segmentation | Use CTC segmentation to recover all long transcribed ANV audio | Pilot failed immediately on a Kikuyu pseudo-long example | Stop bulk download; keep V5 as future work | V4 20.2 |
| K1 | Audit sources metadata-only | PASS without audio/payload download | Safe basis for public text pipeline | K1 |
| K2 Swahili | Read the same `lm_text` directory as ANV languages | Directory absent | Use audited training-Parquet text projection | K2 |
| K2 normalization | Compare to saved V4 `text_norm` | Column absent | Use exact self-consistency and idempotence calibration | K2 |
| K2 leakage control | Dedup alone is sufficient | Held-out exact/near overlaps existed | Apply held-out denylist before corpus publication | K2 |
| K3 validation | K1 schema always contains exact zero-byte field | Validator asserted on a schema variant | Validate semantic status/evidence, not an optional field spelling | K3 |
| K3 intrinsic selection | Lowest perplexity guarantees lowest WER | Full 5-grams won intrinsically, but some routes regressed acoustically | Use K4 WER audit for deployment | K3/K4 |
| K4 dependencies | Binary package changes can load in the same process | Colab required restart after ABI realignment | Split setup and work cells; restart once, then rerun A/B only | K4 |
| K4 selective routing | Deploy every new V6 winner | Only 3 of 11 active groups passed audit | Accept three changes; rollback the rest | K4 |
| K5 runtime | Edge package fits under 8 GiB | Peak 5.586 GiB; +15% = 6.424 GiB | PASS | K5 |
| K5 duration | Full CPU route probe is quick | Approximately 26 minutes | Keep progress/RSS heartbeat; do not interrupt | K5 |
| K6 dependencies | Setup and inference can share realigned process | Colab restart required | Run setup A, restart if requested, then A and B | K6 |
| K6 inference | Resumable route/shard cache can complete full test | 94 shards, 41,733 rows, QA PASS, 7 fallbacks | Submit exact signed CSV manually | K6 |
| Leaderboard | Selective V6 routing improves compliant score | 0.36878 to 0.36585 | Success; freeze run and SHA | K6 |

## Main lessons

1. Audit provenance and speaker separation before optimizing a model.
2. Optimize the competition's macro objective, not only aggregate hours or loss.
3. Treat checkpoint selection, LM tuning, and deployment as separate audits.
4. A tune-set winner is only a hypothesis until an untouched audit confirms it.
5. Perplexity is useful for screening KenLM models, not for final ASR selection.
6. Measure parameters from the serialized artifact and memory in a clean process.
7. Small, evidence-backed route changes beat an indiscriminate global upgrade.
8. Make every expensive Colab stage resumable and content-addressed.


# Afri-Voices omniASR for six Kenyan languages

![WER](https://img.shields.io/badge/Public%20leaderboard%20WER-0.36585-brightgreen)
![Parameters](https://img.shields.io/badge/Active%20parameters-985.57M-blue)
![Memory](https://img.shields.io/badge/Edge%20RSS%20%2B15%25-6.42%20GiB-success)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/Code%20license-Apache--2.0-blue)

This repository documents our end-to-end development of a six-language automatic
speech recognition system for the Afri-Voices East Africa ASR Hackathon. We began
with joint and language-specialized omniASR checkpoints, explored balanced
fine-tuning, checkpoint merging, low-rank approximations and LoRA, and converged
on one BF16 acoustic base, one Maasai LoRA adapter, and language/domain-routed
KenLM decoding.

The final audited system has **985,573,552 active neural parameters**, stays below
the **8 GiB edge-memory limit**, and obtained a public leaderboard WER of
**0.36585**. The repository contains the complete research notebooks, including
failed experiments, plus a deterministic K1–K6 language-model and inference
pipeline. It contains no audio, competition test data, transcripts, credentials,
model weights, KenLM binaries, or submission files.

## Final result

| Submission | Acoustic system | Decoder | Status | Public LB WER |
|---|---|---|---|---:|
| Historical exploration | Multiple specialist checkpoints | KenLM V5 | Exploratory; not the final single-artifact system | **0.36529** |
| First edge-audited system | Step-1250 BF16 base + Maasai LoRA | Production domain routing | Under 1B and under 8 GiB | 0.36878 |
| **Final K6 system** | Same audited acoustic system | Hybrid production/KenLM V6 routing | **Under 1B and under 8 GiB** | **0.36585** |

The historical 0.36529 score is reported for completeness. It relied on multiple
specialized acoustic checkpoints and was not retained under our strict
interpretation of the single-model, total-parameter, and edge-memory constraints.
The 0.36585 submission is our best fully audited, reproducible configuration.
KenLM V6 improved the compliant 0.36878 system by **0.00293 absolute WER**
(approximately **0.8% relative**).

## Task and metric

The task covers six languages: Swahili (`swa`/`sw`), Kikuyu (`kik`), Kalenjin
(`kln`), Dholuo (`luo`), Somali (`som`), and Maasai (`mas`). The leaderboard
metric is the unweighted mean of the six per-language word error rates, so each
language matters equally even when test-set sizes differ.

The implementation was designed around two deployment rules supplied by the
competition:

- fewer than one billion neural parameters in total;
- inference on an edge device with no more than 8 GiB RAM.

## Final architecture

```text
audio + declared language + shard domain
                  |
          long-audio segmentation
         (38 s windows, 6 s overlap)
                  |
      omniASR-CTC-1B-v2 step 1250 (BF16)
                  |
       Maasai LoRA only on its selected route
                  |
       CTC logits / language-domain router
                  |
 one lazy-loaded production or KenLM V6 decoder
                  |
       normalized final transcription
```

Key choices:

1. One shared six-language acoustic base, not six full resident models.
2. Speaker-disjoint training, development, and local-test construction.
3. Language-uniform sampling and explicit legacy/new-domain balancing.
4. Step 1250 selected because step 1500 stopped improving the macro metric.
5. A frozen base plus a small Maasai LoRA; the Kalenjin LoRA was not deployed
   because its measured gain was less reliable.
6. Separate language/domain KenLM routes, tuned and audited without transcript
   leakage.
7. V6 routes accepted only when an independent audit improved; established
   production routes were restored elsewhere.
8. At most one decoder resident in memory.
9. Batch size 1 retained because batches 2/4/8 changed CTC paths and were not
   faster in the exactness probe.
10. Per-shard caches and SHA-256 contracts make long Colab runs resumable.

See [Methodology](docs/METHODOLOGY.md) for the full design and
[Experiment log](docs/EXPERIMENT_LOG.md) for both successful and failed work.

## Acoustic training data

Balanced V4 was built from licensed, speaker-audited material. These are the
hours actually selected for training, not the total size of each upstream corpus.

| Language | Total h | Legacy h | New in-domain h |
|---|---:|---:|---:|
| Swahili | 143.7872 | 14.3814 | 129.4059 |
| Kikuyu | 115.9357 | 38.2562 | 77.6795 |
| Kalenjin | 53.4955 | 9.6287 | 43.8668 |
| Dholuo | 58.1835 | 19.2000 | 38.9835 |
| Somali | 31.4855 | 5.6674 | 25.8180 |
| Maasai | 48.6609 | 8.2769 | 40.3840 |

The five ANV languages came from
[`MCAA1-MSU/anv_data_ke`](https://huggingface.co/datasets/MCAA1-MSU/anv_data_ke),
and Swahili came from
[`DigitalUmuganda/Afrivoice_Swahili`](https://huggingface.co/datasets/DigitalUmuganda/Afrivoice_Swahili).
Both dataset cards identify CC BY 4.0 licensing; access conditions still apply.
See [Data and licenses](docs/DATA_AND_LICENSES.md).

## KenLM V6

K1–K6 form the final reproducible decoder pipeline:

1. **K1 — inventory:** metadata and license audit without downloading audio.
2. **K2 — text corpus:** streaming extraction, CTC-compatible normalization,
   held-out denylist filtering, exact deduplication, and near deduplication.
3. **K3 — build:** 3-, 4-, and 5-gram models plus pruned 5-gram variants.
4. **K4 — acoustic selection:** tune split, independent audit split, bootstrap
   guard, and route-level rollback.
5. **K5 — edge audit:** clean CPU worker, external RSS sampling, real audio,
   all decoder routes, and a 15% memory margin.
6. **K6 — inference:** resumable inference over 94 shards, long-audio handling,
   deterministic CSV assembly, and final QA.

K2 produced 224,445 unique normalized lines and 9,290,297 words. K4 accepted
V6 4-gram models for Swahili-unscripted and Kikuyu-unscripted, and retained a
retuned production decoder for Maasai-scripted. Every other route rolled back to
the established production configuration after failing to show an independent
audit improvement.

## Notebook map and execution order

The notebooks are public, output-free copies. Their executable code is preserved;
Colab outputs and user metadata were removed before publication.

| Order | Notebook | Role |
|---:|---|---|
| 1 | [`01_joint_six_language.ipynb`](notebooks/01_baselines/01_joint_six_language.ipynb) | Original joint baseline and full research workspace |
| 2 | [`02_kikuyu_specialist.ipynb`](notebooks/01_baselines/02_kikuyu_specialist.ipynb) | Kikuyu specialization snapshot |
| 3 | [`03_somali_specialist.ipynb`](notebooks/01_baselines/03_somali_specialist.ipynb) | Somali specialization snapshot |
| 4 | [`10_v4_balanced_a100_80gb.ipynb`](notebooks/02_balanced_training/10_v4_balanced_a100_80gb.ipynb) | Balanced training, extension, merges, LoRA and selection |
| 5 | [`20_k1_source_inventory.ipynb`](notebooks/03_kenlm_v6/20_k1_source_inventory.ipynb) | Source/license inventory |
| 6 | [`20_k2_text_corpus.ipynb`](notebooks/03_kenlm_v6/20_k2_text_corpus.ipynb) | Leakage-safe text corpus |
| 7 | [`20_k3_build_and_evaluate.ipynb`](notebooks/03_kenlm_v6/20_k3_build_and_evaluate.ipynb) | KenLM candidate build and intrinsic evaluation |
| 8 | [`20_k4_acoustic_wer_selection.ipynb`](notebooks/03_kenlm_v6/20_k4_acoustic_wer_selection.ipynb) | Acoustic WER selection |
| 9 | [`20_k5_edge_audit.ipynb`](notebooks/03_kenlm_v6/20_k5_edge_audit.ipynb) | CPU/RSS compliance audit |
| 10 | [`20_k6_final_inference.ipynb`](notebooks/03_kenlm_v6/20_k6_final_inference.ipynb) | Final resumable inference and QA |

The first four notebooks are chronological research records with mutable Colab
state. K1–K6 are the recommended deterministic final path. Read
[`notebooks/README.md`](notebooks/README.md) before running them.

## Edge compliance

| Item | Audited value |
|---|---:|
| Base parameters | 975,675,056 |
| Resident Maasai LoRA parameters | 9,898,496 |
| Active neural parameters | **985,573,552** |
| K5 peak RSS | 5.586 GiB |
| Peak plus 15% margin | **6.424 GiB** |
| Limit | 8.000 GiB |
| Maximum resident decoders | 1 |

The actual serialized checkpoint count differs from the older upstream catalog
figure of 975,065,300. We use the measured count of the released checkpoint in
all compliance contracts. Full details are in
[Edge compliance](docs/EDGE_COMPLIANCE.md).

## Final QA

- 41,733 rows across 94 test shards;
- 4,370 clips handled by long-audio segmentation;
- 7 decoding failures replaced by the documented fallback;
- unique IDs and exact input row order;
- NFC UTF-8, no control or replacement characters;
- deterministic CSV round trip;
- final submission SHA-256:
  `444313927cd1d0d6c6d213634bc1b1b4e6c8cd63346199e10a290abca141437d`.

The CSV itself is intentionally not distributed.

## Reproduction

Start with [Reproducibility](docs/REPRODUCIBILITY.md). In short:

1. Use Python 3.12 in Google Colab or an equivalent Linux environment.
2. Install the pinned notebook dependencies and the upstream
   [Omnilingual ASR](https://github.com/facebookresearch/omnilingual-asr) code.
3. Put `HF_TOKEN`, `KAGGLE_USERNAME`, and `KAGGLE_KEY` in Colab Secrets; never
   paste credentials into a cell.
4. Accept the upstream gated-dataset terms.
5. Set the project root and restore/download licensed inputs.
6. Run the needed notebook path in order. K1–K6 consume signed artifacts from
   earlier steps and stop on mismatched contracts.

Hardware used during the main training runs was an NVIDIA A100 80 GB. K5 is a
CPU-only edge audit. K6 used GPU acoustic inference and CPU KenLM decoding.

## Published artifacts

- Acoustic model: [VynoDePal/omniASR-fine-tuning-6languageKenya](https://huggingface.co/VynoDePal/omniASR-fine-tuning-6languageKenya)
- KenLM V1: [VynoDePal/KenLM-V1](https://huggingface.co/VynoDePal/KenLM-V1)

The Hugging Face KenLM `v1.0.0` tag is immutable. This repository documents the
V6 candidate used by K6, but does not claim that V6 is downloadable from that
Hugging Face repository until a separate `v1.1.0` release is published.

## Limitations

- Public leaderboard scores do not guarantee private-leaderboard performance.
- Development and audit sets are much smaller than the training corpora.
- Domain routing assumes the shard/domain label is available at inference.
- Somali and Kalenjin remain the most difficult languages in local evaluation.
- The long-audio strategy is window-based rather than a native streaming model.
- Seven test items required a fallback; their references are unavailable.
- The system may reflect language, dialect, speaker, and domain biases in its
  source data. It should not be used for high-stakes transcription without review.

## Licensing and attribution

Repository code and sanitized notebooks are released under Apache-2.0. Upstream
models, datasets, KenLM assets, and competition data retain their original
licenses and access terms. No raw data is redistributed here. See
[`LICENSE`](LICENSE), [`NOTICE`](NOTICE),
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), and
[Data and licenses](docs/DATA_AND_LICENSES.md).

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff) and also cite the upstream
Omnilingual ASR and dataset authors. This is an independent competition entry and
is not affiliated with or endorsed by Kaggle, Meta, the organizers, or the
dataset owners.

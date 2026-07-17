# Methodology

## 1. Design objective

The objective was not only to reduce public-leaderboard WER. The final system had
to be reproducible, use fewer than one billion neural parameters in total, and
remain below 8 GiB RAM during edge inference. The competition metric is the mean
of six language-level WERs, so language imbalance cannot be hidden by a large
Swahili test set.

Our final design therefore separates three concerns:

- **acoustic representation:** one shared omniASR CTC base;
- **small targeted adaptation:** one route-specific Maasai LoRA;
- **linguistic decoding:** one language/domain KenLM decoder loaded at a time.

## 2. Data construction

### 2.1 Provenance and speaker separation

Every selected row was traced back to a source record. Train, development, and
local-test groups were speaker-disjoint. Cached spontaneous data was versioned,
and each cache had a completion manifest, build identifier, row counts, and
speaker audit. The first V4 audit failed when these properties were missing; no
training began until the audit passed.

### 2.2 Normalization

The CTC text normalizer performs Unicode repair and normalization, lower-casing,
punctuation filtering, whitespace canonicalization, and vocabulary checks. A
Kikuyu mojibake failure exposed corrupted UTF-8 text and was fixed before the
spontaneous cache was admitted. K2 later required the same normalizer to be
idempotent on its public text corpus.

### 2.3 Balanced V4 sampling

We assigned every item a language, split, speech method, and adaptation role:
`legacy_replay` or `new_in_domain`. Language exposure was uniform at the sampler
level (`beta_language = 0`), while replay/new-domain ratios were controlled per
language. This prevented Swahili from dominating only because more hours were
available. The training mixture contains 451.55 hours in total.

## 3. Acoustic training and checkpoint selection

The starting point was the joint six-language omniASR-CTC-1B-v2 checkpoint at
step 5000. Balanced V4 was trained with a 4,096,000-element micro-batch and ten
gradient-accumulation steps on an A100 80 GB.

The initial balanced run produced checkpoints at total steps 500 and 750. An
extension used the exact step-750 weights as a new seed and a lower learning rate
of `1.5e-6`. Because optimizer state could not safely be resumed across the old
workspace, the extension used a local counter 0–750 mapped explicitly to nominal
total steps 750–1500. This avoided the earlier faulty resume that confused local
and global step numbers.

| Candidate | Macro WER |
|---|---:|
| Original joint checkpoint | 0.492821 |
| Balanced step 750 | 0.474244 |
| Balanced step 1000 | 0.473849 |
| **Balanced step 1250** | **0.471888** |
| Balanced step 1500 | 0.472127 |

Step 1250 was selected. The small degradation at step 1500 is consistent with a
plateau or early over-specialization; more steps were not assumed to be better.

## 4. Specialist information under the parameter cap

### 4.1 Full specialist checkpoints

Kikuyu, Kalenjin, Somali, and Maasai specialist runs were useful diagnostics but
could not all be deployed as full models. The strongest historical routing score,
0.36529, used multiple specialized acoustic checkpoints and is therefore treated
as exploratory rather than the final strict-compliance artifact.

### 4.2 Delta merges

We tested arithmetic merges of Kalenjin and Maasai specialist weight deltas into
one base (M1 and M2). The initial serialization duplicated external tensors and
created 7.27 GiB files; compaction restored 3.63 GiB without changing tensors.
The merged models did not improve the audited local macro metric and were rejected.

### 4.3 SVD approximation

We approximated specialist deltas with low-rank SVD under an approximately
10-million-parameter budget per language. Raising the rank cap removed saturation,
but eligible two-dimensional matrices still retained only about 48.1% of Kalenjin
delta energy and 45.9% of Maasai delta energy. This was too lossy to deploy.

### 4.4 True LoRA

A structural compatibility audit found 289 eligible projections. Ranks 8 and 9
produced 9,898,496 parameters per adapter. Zero initialization was exact, and the
frozen 975,675,056-parameter base remained bitwise unchanged during smoke tests.

Kalenjin and Maasai adapters were trained through steps 500, 750, 1000, 1250,
and 1500. Step 1250 was locally best for both. When evaluated with the same
production decoder configuration:

| Language | Base WER | Adapter WER | Delta | Deployment decision |
|---|---:|---:|---:|---|
| Kalenjin | 0.244027 | 0.240916 | -0.003111 | Rejected: uncertainty crossed zero |
| Maasai | 0.244025 | 0.240748 | -0.003277 | Accepted |

Only the Maasai adapter is resident in the final package.

## 5. KenLM V6 without leakage

### 5.1 K1: source inventory

K1 inspected metadata, file manifests, schemas, and licensing evidence without
downloading audio or reading corpus payloads. Sources with unknown, incompatible,
or unverified licensing were excluded from extraction or left as catalog-only.

### 5.2 K2: text corpus

K2 streamed only approved text columns, normalized them, removed held-out text
through exact and fuzzy denylists, and then performed exact and near deduplication.
No test transcript was used. The final corpus contains 224,445 lines and
9,290,297 words.

### 5.3 K3: language-model candidates

For each language, K3 built five candidates: full 3-gram, 4-gram, and 5-gram
models plus two pruned 5-gram variants. Full 5-grams generally had the best
intrinsic perplexity, but perplexity was not used as the final deployment metric.

### 5.4 K4: acoustic WER selection

Each language/domain group had separate tuning and audit samples. Decoder asset,
LM weight (`alpha`), word insertion score (`beta`), and beam size were chosen on
the tune split. The chosen challenger then faced the untouched audit split with a
bootstrap probability guard. A route was changed only when the audit supported it.

Accepted changes:

| Route | Final change | Audit WER delta | Probability better |
|---|---|---:|---:|
| Swahili / unscripted | V6 full 4-gram | -0.005988 | 0.9605 |
| Kikuyu / unscripted | V6 full 4-gram | -0.035871 | 1.0000 |
| Maasai / scripted | Retuned production LM | -0.057416 | 1.0000 |

All other routes restored the existing production configuration. This hybrid
rollback strategy matters: a model that wins on perplexity or tuning data can
still harm real acoustic decoding.

## 6. Long audio and inference

The upstream CTC pipeline accepts short clips. Longer recordings are divided into
38-second windows with 6-second overlap. Boundary output is trimmed using a
3-second overlap policy before text is joined. K6 handled 4,370 long clips this
way.

Batch sizes 2, 4, and 8 were tested against batch size 1. They changed logits and
CTC paths enough to alter transcripts, and none produced a useful speedup in the
probe. Exact batch-1 inference was kept.

Every shard writes a signed cache tied to the acoustic weights, adapter, decoder
configuration, normalization contract, and shard identity. A restarted runtime
therefore recomputes only missing or invalid shards.

## 7. Edge audit

The first in-process memory audit incorrectly reported 35 GiB because
`ru_maxrss` retained the lifetime high-water mark of a process that had previously
loaded training artifacts. The corrected audit launches a clean worker and samples
the entire process tree externally.

K5 loaded the BF16 base, Maasai LoRA, every one of the 12 routes, and real
development audio while allowing only one KenLM decoder at a time. Peak RSS was
5.586 GiB; adding a 15% margin gives 6.424 GiB, below the 8 GiB limit.

## 8. Final QA

K6 generated 41,733 rows in the exact input order. Checks covered unique IDs,
language counts, empty predictions, normalization idempotence, NFC UTF-8,
control characters, replacement characters, maximum output length, and a CSV
write/read round trip. Seven decoding failures used the documented fallback. The
resulting file achieved public leaderboard WER 0.36585.


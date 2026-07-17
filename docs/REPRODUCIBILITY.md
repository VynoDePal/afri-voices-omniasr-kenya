# Reproducibility guide

## Scope

This repository publishes executable notebooks and aggregate, non-sensitive
results. It does not redistribute licensed datasets, Kaggle test data, private
manifests, model weights, compiled KenLM binaries, caches, or submission CSVs.
Users must obtain each input from its owner and accept any access conditions.

The first three notebooks and much of Balanced V4 are research snapshots. They
depend on artifacts produced during earlier cells and should not be treated as a
single clean `Run all` workflow. K1–K6 are the preferred final pipeline.

## Environment

Recorded environment:

- Linux / Google Colab;
- Python 3.12;
- NVIDIA A100 80 GB for main acoustic training;
- BF16 inference where supported;
- CPU KenLM decoding and K5 edge audit;
- Google Drive for persistent stage contracts and caches.

Install the upstream
[Omnilingual ASR](https://github.com/facebookresearch/omnilingual-asr) package
and the dependencies listed in [`environment/requirements-colab.txt`](../environment/requirements-colab.txt).
The notebooks also install or pin stage-specific dependencies. K3 pins the KenLM
source revision used by the experiment.

## Credentials

Set these through Colab Secrets or environment variables:

```text
HF_TOKEN
KAGGLE_USERNAME
KAGGLE_KEY
```

Never paste values into a notebook. Never commit `kaggle.json`, `hf_token.json`,
`.env`, or a credential export. Public notebooks contain no credential values.

## Paths

The public notebooks use the generic `/content/afrivoices_project` placeholder.
Before running, set or adapt one project root in the configuration cell. Do not
use blind global search and replace inside signed contract files.

Recommended layout:

```text
/content/afrivoices_project/
├── curated_data/
├── dataset_caches/
├── finetune_runs/
└── kaggle_test_full/
```

The public repository does not create this layout automatically because the data
is licensed and large.

## Execution paths

### Rebuild the research history

1. Joint six-language notebook.
2. Optional Kikuyu specialist notebook.
3. Optional Somali specialist notebook.
4. Balanced V4 notebook, following its numbered cell instructions.

These stages can require several Colab sessions. Respect every audit status before
continuing. A failed audit is a stop condition, not a warning to ignore.

### Rebuild KenLM V6 and final inference

1. K1 source inventory.
2. K2 text extraction and deduplication.
3. K3 KenLM build and intrinsic evaluation.
4. K4 acoustic WER selection.
5. K5 clean-process edge audit.
6. K6 final test inference and QA.

Each notebook writes `contract.json`, `_COMPLETE.json`, and a `LATEST_PASS.json`
pointer. The next stage verifies identifiers and hashes generated in your own
workspace. Public copies use `REPLACE_WITH_LOCAL_RUN_ID` and
`REPLACE_WITH_LOCAL_SHA256` where a historical private identifier was removed.
Do not rename or edit a completed upstream artifact without starting a new run.

K4 and K6 may realign binary packages. If their setup cell says a restart is
required, restart the Colab runtime and execute only the documented setup and work
cells. Continuing in an ABI-inconsistent process is intentionally blocked.

## Expected checkpoints and assets

The public model assets are linked from the main README. For the recorded final
system, the important identities are:

- balanced acoustic checkpoint: nominal step 1250;
- measured base parameters: 975,675,056;
- selected Maasai LoRA: step 1250, 9,898,496 parameters;
- active total: 985,573,552;
- K5 and K6 identifiers: read them from the corresponding local
  `LATEST_PASS.json` files rather than copying an author's private run ID.

Do not silently substitute step 1500: it had slightly worse macro WER.

## Safe reruns

- Copy large Drive audio locally before inference.
- Keep per-shard result caches on persistent storage.
- Validate a cache signature before marking it complete.
- Load one KenLM decoder at a time.
- Use batch size 1 unless a new exactness test proves equivalence.
- Never manually edit test predictions.
- Do not print submission previews or transcript rows in public logs.
- Do not delete Drive roots. Historical cleanup cells must be reviewed and scoped
  to their staging directories before execution.

## Verification

Run from the repository root:

```bash
python scripts/validate_release.py
```

It checks notebook JSON, stripped outputs, credential patterns, forbidden file
types, aggregate result files, internal links, and checksums. This validates the
public release structure; it does not reproduce model training.

## Expected final QA

The exact K6 result has 41,733 rows with the language counts documented in the
main README and methodology. Private machine receipts and the submission CSV are
excluded from this repository and must be regenerated from licensed test inputs.

# Notebook guide

All ten notebooks supplied for the project are included. Public filenames are
shorter and stable; the original filenames are listed for traceability.

| Public path | Original file | Classification |
|---|---|---|
| `01_baselines/01_joint_six_language.ipynb` | `omniASR_CTC_1B_VS_FN_6language.ipynb` | Research archive |
| `01_baselines/02_kikuyu_specialist.ipynb` | `omniASR_CTC_1B_VS_FN_6language_KIK.ipynb` | Research archive |
| `01_baselines/03_somali_specialist.ipynb` | `omniASR_CTC_1B_VS_FN_6language_SOM(1).ipynb` | Research archive |
| `02_balanced_training/10_v4_balanced_a100_80gb.ipynb` | `omniASR_CTC_1B_V4_balanced_A100_80GB(1).ipynb` | Main acoustic-training archive |
| `03_kenlm_v6/20_k1_source_inventory.ipynb` | `omniASR_20_K1_KenLM_inventory(1).ipynb` | Final pipeline |
| `03_kenlm_v6/20_k2_text_corpus.ipynb` | `omniASR_20_K2_KenLM_V6_text_corpus(1).ipynb` | Final pipeline |
| `03_kenlm_v6/20_k3_build_and_evaluate.ipynb` | `omniASR_20_K3_KenLM_V6_build_eval(1).ipynb` | Final pipeline |
| `03_kenlm_v6/20_k4_acoustic_wer_selection.ipynb` | `omniASR_20_K4_KenLM_V6_acoustic_WER(1).ipynb` | Final pipeline |
| `03_kenlm_v6/20_k5_edge_audit.ipynb` | `omniASR_20_K5_KenLM_V6_edge_audit(1).ipynb` | Final pipeline |
| `03_kenlm_v6/20_k6_final_inference.ipynb` | `omniASR_20_K6_KenLM_V6_final_inference(1).ipynb` | Final pipeline |

## Sanitization

Every public notebook was rebuilt from source with:

- all outputs removed;
- execution counts reset;
- Colab user IDs, display names, widget state, and runtime metadata removed;
- submission/transcript preview prints replaced with aggregate-only messages;
- secret-pattern scanning;
- a public-release notice inserted as the first cell.

The preparation script generates a local sanitization report for review. That
machine receipt is intentionally not committed to the public repository.

## Important warning

The research archives contain historical cleanup and mutation cells and rely on
mutable Google Drive state. Read each section and validate its path variables;
do not blindly use `Run all`. K1–K6 are more deterministic but still create staged
artifacts and may remove only their own staging directories during a safe restart.

All notebook explanations in this repository are provided in English in the main
README and `docs/`. Some original source comments and headings remain in French so
the executable research record is not rewritten in ways that could change behavior.

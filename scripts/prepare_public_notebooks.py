#!/usr/bin/env python3
"""Create deterministic, output-free public copies of the project notebooks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MAPPING = {
    "omniASR_CTC_1B_VS_FN_6language.ipynb":
        "notebooks/01_baselines/01_joint_six_language.ipynb",
    "omniASR_CTC_1B_VS_FN_6language_KIK.ipynb":
        "notebooks/01_baselines/02_kikuyu_specialist.ipynb",
    "omniASR_CTC_1B_VS_FN_6language_SOM(1).ipynb":
        "notebooks/01_baselines/03_somali_specialist.ipynb",
    "omniASR_CTC_1B_V4_balanced_A100_80GB(1).ipynb":
        "notebooks/02_balanced_training/10_v4_balanced_a100_80gb.ipynb",
    "omniASR_20_K1_KenLM_inventory(1).ipynb":
        "notebooks/03_kenlm_v6/20_k1_source_inventory.ipynb",
    "omniASR_20_K2_KenLM_V6_text_corpus(1).ipynb":
        "notebooks/03_kenlm_v6/20_k2_text_corpus.ipynb",
    "omniASR_20_K3_KenLM_V6_build_eval(1).ipynb":
        "notebooks/03_kenlm_v6/20_k3_build_and_evaluate.ipynb",
    "omniASR_20_K4_KenLM_V6_acoustic_WER(1).ipynb":
        "notebooks/03_kenlm_v6/20_k4_acoustic_wer_selection.ipynb",
    "omniASR_20_K5_KenLM_V6_edge_audit(1).ipynb":
        "notebooks/03_kenlm_v6/20_k5_edge_audit.ipynb",
    "omniASR_20_K6_KenLM_V6_final_inference(1).ipynb":
        "notebooks/03_kenlm_v6/20_k6_final_inference.ipynb",
}

SECRET_PATTERNS = (
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(
        r"(?i)((?:HF_TOKEN|KAGGLE_KEY|API_KEY|ACCESS_TOKEN|PASSWORD)\s*=\s*)"
        r"([\"'])(?!REPLACE_ME|YOUR_|<)[^\"'\n]{8,}\2"
    ),
)

# Public notebooks keep the experiment logic but must not disclose the owner's
# private Drive layout or internal run identifiers. Users regenerate these values
# from their own stage contracts.
PUBLIC_PATH_PATTERNS = (
    (
        re.compile(r"/content/drive/" r"MyDrive/[A-Za-z0-9_.-]+"),
        "/content/afrivoices_project",
    ),
    (re.compile(r"/content/drive/" r"MyDrive"), "/content/persistent_storage"),
    (re.compile(r"ft_[A-Za-z0-9_.-]+"), "experiment_run"),
)

INTERNAL_METADATA_PATTERNS = (
    (re.compile(r"ws_1\.[0-9a-f]{8}"), "workspace_selected"),
    (
        re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])"),
        "REPLACE_WITH_LOCAL_SHA256",
    ),
    (
        re.compile(r"(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])"),
        "REPLACE_WITH_LOCAL_RUN_ID",
    ),
)

PUBLIC_HEADER = """# Public release note

This is a sanitized public copy of `{source}`. Cell outputs, execution counters,
Colab user metadata, widget state, embedded display payloads, private storage
paths, and internal run identifiers were removed before publication. The
experiment source is preserved, but public placeholders must be configured from
your own generated contracts before rerunning dependent stages. See the repository
README and `docs/REPRODUCIBILITY.md` for prerequisites, data access, execution
order, expected artifacts, and the English explanation of this experiment.

Never paste credentials into a notebook. Use Colab Secrets or environment
variables (`HF_TOKEN`, `KAGGLE_USERNAME`, and `KAGGLE_KEY`).
"""


def source_text(source: object) -> str:
    if isinstance(source, list):
        return "".join(str(item) for item in source)
    return str(source or "")


def redact(text: str) -> tuple[str, int]:
    count = 0
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)("):
            text, replaced = pattern.subn(r"\1\2REDACTED\2", text)
        else:
            text, replaced = pattern.subn("REDACTED", text)
        count += replaced
    for pattern, public in PUBLIC_PATH_PATTERNS:
        text, replaced = pattern.subn(public, text)
        count += replaced
    for pattern, replacement in INTERNAL_METADATA_PATTERNS:
        text, replaced = pattern.subn(replacement, text)
        count += replaced
    # Do not print competition predictions or transcript samples on a public rerun.
    text = text.replace(
        "print(submission.head(8).to_string())",
        "print(f\"Submission assembled: {len(submission)} rows; preview omitted.\")",
    )
    text = text.replace(
        "print(_pf.read_row_group(0, columns=_cols).to_pandas().head(8).to_string())",
        "print(f\"Parquet schema columns: {_cols}; row preview omitted.\")",
    )
    return text, count


def sanitize(source_path: Path, destination: Path) -> dict[str, object]:
    notebook = json.loads(source_path.read_text(encoding="utf-8"))
    assert notebook.get("nbformat") == 4, source_path

    redactions = 0
    public_cells = []
    public_cells.append(
        {
            "cell_type": "markdown",
            "metadata": {"tags": ["public-release-note"]},
            "source": PUBLIC_HEADER.format(source=source_path.name).splitlines(True),
        }
    )

    for cell in notebook.get("cells", []):
        clean = {
            "cell_type": cell["cell_type"],
            "metadata": {
                "tags": list(cell.get("metadata", {}).get("tags", [])),
            },
            "source": [],
        }
        text, replaced = redact(source_text(cell.get("source", [])))
        redactions += replaced
        clean["source"] = text.splitlines(True)
        if cell["cell_type"] == "code":
            clean["execution_count"] = None
            clean["outputs"] = []
        public_cells.append(clean)

    notebook["cells"] = public_cells
    notebook["metadata"] = {
        "kernelspec": notebook.get("metadata", {}).get(
            "kernelspec",
            {"display_name": "Python 3", "language": "python", "name": "python3"},
        ),
        "language_info": notebook.get("metadata", {}).get(
            "language_info", {"name": "python"}
        ),
        "public_release": {
            "source_filename": source_path.name,
            "outputs_removed": True,
            "credentials_embedded": False,
        },
    }
    notebook["nbformat_minor"] = min(int(notebook.get("nbformat_minor", 5)), 5)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return {
        "source": source_path.name,
        "destination": destination.as_posix(),
        "cells": len(public_cells),
        "redactions": redactions,
        "bytes": destination.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("repository_root", type=Path)
    args = parser.parse_args()

    records = []
    for original, public in MAPPING.items():
        source = args.source_directory / original
        assert source.is_file(), source
        records.append(sanitize(source, args.repository_root / public))

    report = args.repository_root / "results" / "notebook_sanitization.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"schema": 1, "notebooks": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    for record in records:
        print(
            f"{record['source']} -> {record['destination']} "
            f"({record['bytes']} bytes, {record['redactions']} redactions)"
        )


if __name__ == "__main__":
    main()

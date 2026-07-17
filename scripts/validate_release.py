#!/usr/bin/env python3
"""Validate that the GitHub release is structurally safe and reproducible."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []

EXPECTED_NOTEBOOKS = {
    "notebooks/01_baselines/01_joint_six_language.ipynb",
    "notebooks/01_baselines/02_kikuyu_specialist.ipynb",
    "notebooks/01_baselines/03_somali_specialist.ipynb",
    "notebooks/02_balanced_training/10_v4_balanced_a100_80gb.ipynb",
    "notebooks/03_kenlm_v6/20_k1_source_inventory.ipynb",
    "notebooks/03_kenlm_v6/20_k2_text_corpus.ipynb",
    "notebooks/03_kenlm_v6/20_k3_build_and_evaluate.ipynb",
    "notebooks/03_kenlm_v6/20_k4_acoustic_wer_selection.ipynb",
    "notebooks/03_kenlm_v6/20_k5_edge_audit.ipynb",
    "notebooks/03_kenlm_v6/20_k6_final_inference.ipynb",
}

FORBIDDEN_NAMES = {
    "kaggle.json",
    "hf_token.json",
    ".env",
    "submission.csv",
}
FORBIDDEN_SUFFIXES = {
    ".pt", ".pth", ".ckpt", ".safetensors", ".bin", ".binary", ".arpa",
    ".klm", ".wav", ".flac", ".mp3", ".webm", ".parquet",
}
SECRET_PATTERNS = {
    "Hugging Face token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "literal sensitive assignment": re.compile(
        r"(?i)(?:HF_TOKEN|KAGGLE_KEY|API_KEY|ACCESS_TOKEN|PASSWORD)\s*=\s*"
        r"[\"'](?!REDACTED|REPLACE_ME|YOUR_|<)[^\"'\n]{8,}[\"']"
    ),
}

PRIVATE_METADATA_PATTERNS = {
    "private Google Drive path": re.compile(r"/content/drive/" r"MyDrive"),
    "private named project root": re.compile(
        r"/content/drive/" r"MyDrive/[A-Za-z0-9_.-]+"
    ),
    "private experiment directory": re.compile(r"ft_[A-Za-z0-9_.-]+"),
    "private fairseq workspace": re.compile(r"ws_1\.[0-9a-f]{8}"),
}


def fail(message: str) -> None:
    ERRORS.append(message)


def repository_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def validate_file_inventory(files: list[Path]) -> None:
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_NAMES or path.name.startswith("submission_"):
            fail(f"forbidden release file: {rel}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            fail(f"forbidden binary/data suffix: {rel}")
        if path.stat().st_size >= 100 * 1024 * 1024:
            fail(f"file reaches GitHub's 100 MB limit: {rel}")


def validate_notebooks() -> None:
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.glob("notebooks/**/*.ipynb")
    }
    if actual != EXPECTED_NOTEBOOKS:
        fail(f"notebook set differs: missing={sorted(EXPECTED_NOTEBOOKS-actual)}, "
             f"extra={sorted(actual-EXPECTED_NOTEBOOKS)}")

    for rel in sorted(actual):
        path = ROOT / rel
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fail(f"invalid notebook JSON {rel}: {exc}")
            continue
        if notebook.get("nbformat") != 4:
            fail(f"unsupported nbformat in {rel}")
        metadata = notebook.get("metadata", {})
        if "widgets" in metadata or "colab" in metadata:
            fail(f"embedded widget/Colab metadata in {rel}")
        cells = notebook.get("cells", [])
        if not cells or "Public release note" not in "".join(cells[0].get("source", [])):
            fail(f"missing public release note in {rel}")
        for index, cell in enumerate(cells):
            cell_meta = cell.get("metadata", {})
            if set(cell_meta) - {"tags"}:
                fail(f"unexpected cell metadata in {rel}:{index}")
            if cell.get("cell_type") == "code":
                if cell.get("outputs") != []:
                    fail(f"saved output in {rel}:{index}")
                if cell.get("execution_count") is not None:
                    fail(f"execution count in {rel}:{index}")
            source = "".join(cell.get("source", []))
            if "submission.head(" in source:
                fail(f"submission preview code in {rel}:{index}")


def validate_secrets(files: list[Path]) -> None:
    text_suffixes = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".csv", ".cff", ".ipynb", ""}
    for path in files:
        if path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                fail(f"possible {label} in {rel}")
        for label, pattern in PRIVATE_METADATA_PATTERNS.items():
            if pattern.search(text):
                fail(f"possible {label} in {rel}")


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                fail(f"link escapes repository in {path.relative_to(ROOT)}: {target}")
                continue
            if not resolved.exists():
                fail(f"broken local link in {path.relative_to(ROOT)}: {target}")


def validate_results() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    edge = (ROOT / "docs/EDGE_COMPLIANCE.md").read_text(encoding="utf-8")
    experiments = (ROOT / "docs/EXPERIMENT_LOG.md").read_text(encoding="utf-8")
    if "0.36585" not in readme or "41,733" not in readme:
        fail("README omits the final leaderboard result or QA row count")
    if "985,573,552" not in edge or "6.424" not in edge or "8.000 GiB" not in edge:
        fail("edge-compliance documentation omits required audited values")
    if "Failed" not in experiments and "failed" not in experiments:
        fail("experiment log does not document failed work")


def main() -> int:
    files = repository_files()
    validate_file_inventory(files)
    validate_notebooks()
    validate_secrets(files)
    validate_markdown_links()
    validate_results()

    if ERRORS:
        print("PUBLIC RELEASE VALIDATION: FAIL")
        for error in ERRORS:
            print(f" - {error}")
        return 1

    total_bytes = sum(path.stat().st_size for path in files)
    print("PUBLIC RELEASE VALIDATION: PASS")
    print(f"Files: {len(files)} | notebooks: {len(EXPECTED_NOTEBOOKS)} | bytes: {total_bytes}")
    print("No notebook outputs, credential patterns, prohibited data, or oversized files found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

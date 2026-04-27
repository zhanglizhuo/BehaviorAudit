# A Four-Dimension Pre-Modeling Audit Protocol for Educational Prediction Benchmarks

This repository contains the code, experiments, and manuscript sources for the paper "A Four-Dimension Pre-Modeling Audit Protocol for Educational Prediction Benchmarks" (Yan Ma & Lizhuo Zhang), which uses MM-TBA as a worked example. The repository preserves the MM-TBA paper assets and provides an adapter-based framework for extending the audit to additional public educational datasets.

The current repository has two goals:

- preserve the exact MM-TBA paper assets, experiment scripts, and key run outputs in one place;
- provide a small adapter-based framework for extending the audit to additional public educational datasets.

## Published Paper

This repository accompanies the manuscript "A Four-Dimension Pre-Modeling Audit Protocol for Educational Prediction Benchmarks" (Yan Ma & Lizhuo Zhang). The canonical manuscript source and manuscript markdown are available in the local file paper/behavioraudit.md. Please cite the manuscript when using or building on these analyses.

## Layout

- `experiments/mm_tba_stage13/`: archived executable MM-TBA experiment script and raw result JSONs.
- `analysis/figures_and_diagnostics/`: manuscript figures, figure-regeneration script, and draft diagnostics.
- `analysis/quality_gate/`: final paper quality-gate outputs.
- `paper/`: canonical manuscript markdown, reviewer responses, and MDPI `.tex`/`.pdf` files.
- `release/behavioraudit/`: public-facing release bundle for lightweight reproduction.
- `framework/`: reusable audit runner, baseline utilities, and dataset adapters.
- `run_audit.py`: CLI entrypoint for the adapter-based audit runner.
- `generated/`: output location for rerun JSONs.

## Current Adapter Support

The repository currently supports `mm_tba` and `oulad`. New datasets should be added under `framework/adapters/` by implementing the adapter protocol defined in `framework/types.py`.

## Datasets — included vs. external

The manuscript audits seven datasets. Below is the status of those datasets in this workspace and where to place external copies for reproducibility runs.

- Present (local paths):
	- MM-TBA: `MM-TBA/` (see `MM-TBA/README.md` for file descriptions)
	- OULAD: `OULAD/` (CSV files: `assessments.csv`, `studentInfo.csv`, ...)
	- UCI Student (Portuguese): `UCI/` (`student-mat.csv`, `student-por.csv`)
	- Dropout: `StudentDropout/student_dropout.csv`
	- xAPI-Edu: `xAPI-Edu-Data/xAPI-Edu-Data.csv`

- External (you must download and place under these paths):
	- Higher Ed (Yilmaz & Sekeroglu, 2020): place dataset files under `data/higher_ed/` or `BehaviorAudit/data/higher_ed/` before running the audit adapter for `higher_ed`.
	- Entrance Exam (Bora & Dey, 2021): place dataset files under `data/entrance_exam/` or `BehaviorAudit/data/entrance_exam/`.

Notes:
- Some local folders (e.g., `MM-TBA/`) include preprocessing scripts, README, and metadata but may not contain redistributed raw data depending on licensing — check the folder README before assuming raw media are present.
- Do not commit raw datasets to the public release bundle unless you have explicit redistribution rights; follow the guidance in `release/behavioraudit/README.md`.

## Quick Start

Install the minimal dependencies:

```bash
python3 -m pip install -r requirements.txt
```

**Note:** This repository does not include the MM-TBA or OULAD raw datasets. You must obtain the datasets yourself (e.g., by contacting the original maintainers or following the official release channel). All code and results can be reproduced once the dataset path is set.

Run the adapter-based MM-TBA audit:

```bash
python3 run_audit.py --dataset mm_tba --output-dir generated/mm_tba
```

If the dataset is not under `MM-TBA/` at the repository root, pass `--dataset-root /path/to/MM-TBA` or set `MM_TBA_ROOT`.

Run the adapter-based OULAD audit:

```bash
python3 run_audit.py --dataset oulad --dataset-root /path/to/OULAD --output-dir generated/oulad
```

Rebuild the main MM-TBA manuscript figures:

```bash
python3 release/behavioraudit/regenerate_figures.py
```

## Minimal Reproduction Checklist

1. Install dependencies with `python3 -m pip install -r requirements.txt`.
2. Place required datasets under expected local paths (or pass `--dataset-root` for each run).
3. Run one adapter audit end-to-end, for example:

```bash
python3 run_audit.py --dataset mm_tba --output-dir generated/mm_tba
```

4. Confirm output artifacts are generated under `generated/` (JSON and CSV metrics).
5. Regenerate manuscript figures with `python3 release/behavioraudit/regenerate_figures.py` and verify figures in `outputs/paper_figures/`.
6. Cross-check that tracked paper-level result JSONs under `paper/` match the intended submission snapshot.

## Reviewer Quick Verify

Run the command below to perform a minimal end-to-end sanity check (single dataset audit + figure regeneration + key output existence checks):

```bash
python3 run_audit.py --dataset mm_tba --output-dir generated/mm_tba \
	&& python3 release/behavioraudit/regenerate_figures.py \
	&& ls -l generated/mm_tba outputs/paper_figures/fig1_framework_overview.pdf
```

Expected outcome:
- `run_audit.py` finishes without errors and writes JSON/CSV artifacts under `generated/mm_tba/`
- figure regeneration finishes without errors and produces PDFs under `outputs/paper_figures/`
- the final `ls` command prints existing paths (non-empty output)

## What To Track

Recommended to keep in Git:

- audit and experiment code under `experiments/`, `framework/`, `release/`, and root entry scripts (for example `run_*.py`, `generate_figures.py`)
- manuscript source files under `paper/`
- figure-generation scripts and final figure assets used in the manuscript (for example `analysis/figures_and_diagnostics/` and `outputs/paper_figures/`)
- final result artifacts used in the paper (JSON/CSV under `generated/` and paper-level canonical result JSONs under `paper/`)
- reproducibility metadata such as `requirements.txt` and dataset adapter definitions under `framework/adapters/`

Recommended not to add:

- raw datasets under `datasets/` (unless redistribution rights are explicit)
- Python cache directories, local bytecode files, and local virtual-environment artifacts
- LaTeX intermediate build files and temporary packaging outputs
- ad hoc exploratory outputs not referenced by the paper

Here, "canonical" means the final version directly used in the submitted manuscript and reproducible from tracked scripts.

## Notes

- Files here are aggregated copies. Original source files remain in their existing repository locations.
- The adapter framework is intentionally small. It is meant to make the second-dataset integration easy once new data are prepared, not to redesign the whole paper pipeline.
- The current codebase is kept compatible with the main `python3` environment. No virtual environment is required.
- `analysis/figures_and_diagnostics/draft_quality.json` is a historical diagnostic artifact automatically generated during manuscript drafting. It is kept for provenance and does not affect main results.
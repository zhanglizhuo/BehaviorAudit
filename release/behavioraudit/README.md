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

## Datasets (for release users)

This release bundle supports reproducing the MM-TBA analyses. For convenience, the repository contains adapter code and some example files; raw data distribution is governed by the original dataset licenses. For the seven-dataset audit reported in the paper, the workspace status is:

- Present in this repository: MM-TBA (support files under `MM-TBA/`), OULAD (`OULAD/`), UCI (`UCI/`), Dropout (`StudentDropout/`), xAPI-Edu (`xAPI-Edu-Data/`).
- External download required: Higher Ed and Entrance Exam — obtain from the original maintainers or UCI repository and place under `data/higher_ed/` and `data/entrance_exam/` respectively before running cross-dataset adapters.

Follow the data policy above: do not upload raw datasets to the public release unless redistribution is explicitly permitted by the dataset license.

## Current Adapter Support

The repository currently supports `mm_tba` and `oulad`. New datasets should be added under `framework/adapters/` by implementing the adapter protocol defined in `framework/types.py`.

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

## What To Track

Recommended to keep in Git:

- experiment code under `experiments/`, `framework/`, and `release/`
- manuscript sources under `paper/`
- canonical figure assets under `analysis/figures_and_diagnostics/`
- canonical result JSONs under `generated/mm_tba/`

Recommended not to add:

- raw MM-TBA or OULAD datasets
- Python cache directories and local bytecode files
- ad hoc rebuild outputs not intended as canonical artifacts

## Notes

- Files here are aggregated copies. Original source files remain in their existing repository locations.
- The adapter framework is intentionally small. It is meant to make the second-dataset integration easy once new data are prepared, not to redesign the whole paper pipeline.
- The current codebase is kept compatible with the main `python3` environment. No virtual environment is required.
- `analysis/figures_and_diagnostics/draft_quality.json` is a historical diagnostic artifact automatically generated during manuscript drafting. It is kept for provenance and does not affect main results.
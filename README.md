# BehaviorAudit

BehaviorAudit contains the code and manuscript assets for the study "Are Educational Prediction Benchmarks Structurally Reliable? A Four-Dimension Audit Across Seven Public Datasets" by Yan Ma and Lizhuo Zhang.

The repository supports two levels of reproduction:

- figure-level reproduction from the tracked result artifacts; and
- full audit reruns when the seven public datasets are placed in the expected local directories.

Raw datasets are not redistributed in this repository. The scripts assume that users obtain the public datasets from their original maintainers and place them under `datasets/` as described below.

## Repository Layout

- `framework/`: dataset adapters, baseline models, metrics, and the lightweight audit runner.
- `run_7dataset_audit.py`: full four-dimension audit used for the main manuscript results.
- `run_classification_sensitivity.py`: classification-metric sensitivity analysis for binary and ordinal targets.
- `run_audit.py`: quick single-dataset adapter runner for smoke tests and small reruns.
- `generate_figures.py`: regenerates figure files from tracked result artifacts.
- `scripts/`: helper scripts for split-level metrics and structural-pattern analysis.
- `generated/`: tracked split-level CSV artifacts used by figure scripts.
- `paper/`: manuscript source, compiled PDF, bibliography, and final figure assets.

## Installation

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Dataset Placement

Place each downloaded dataset under the following paths relative to the repository root:

| Dataset | Expected path |
| --- | --- |
| MM-TBA | `datasets/MM-TBA/` |
| Higher Ed (UCI ID 856) | `datasets/StudentExam/higher_ed_856.csv` |
| xAPI-Edu | `datasets/xAPI-Edu/xAPI-Edu-Data.csv` |
| Entrance Exam (UCI ID 582) | `datasets/StudentExam/student_entrance_582.csv` |
| UCI Student | `datasets/UCI/student-por.csv` and/or `datasets/UCI/student-mat.csv` |
| Student Dropout (UCI ID 697) | `datasets/StudentDropout/student_dropout.csv` |
| OULAD | `datasets/OULAD/*.csv` |

The `datasets/` directory is intentionally ignored by Git. This keeps the public repository focused on code, metadata, and reproducible outputs without redistributing third-party data.

## Reproduce the Main Audit

After placing the datasets, run:

```bash
python3 run_7dataset_audit.py
```

The script writes the seven-dataset audit JSON to both:

- `audit_7dataset_results.json`
- `paper/audit_7dataset_results.json`

It uses 100 repeated 80/20 splits, 30 permutation-tested splits with 500 draws each, and leave-one-group-out validation where grouping metadata are available.

## Reproduce Sensitivity Analyses

Classification-metric sensitivity:

```bash
python3 run_classification_sensitivity.py
```

Structural-pattern figure and CSV:

```bash
python3 scripts/structural_pattern_analysis.py
```

Split-level linear metrics used by distribution plots:

```bash
python3 scripts/export_linear_split_r2.py
python3 scripts/merge_linear_metrics.py
```

## Regenerate Figures

The tracked JSON and CSV artifacts are sufficient to regenerate the manuscript figures without rerunning the full audit:

```bash
python3 generate_figures.py
python3 scripts/structural_pattern_analysis.py
```

The figure scripts write working copies under `outputs/` and update the manuscript figure files under `paper/`, including `fig1_protocol.pdf`, `fig2_audit_heatmap.pdf`, `fig3_iid_vs_group.pdf`, `fig4_null_separation.pdf`, `fig5_instability_strip.pdf`, `fig6_structural_patterns.pdf`, and the supplementary `figS*.pdf` files.

## Quick Smoke Test

To verify that the adapter framework can load a single local dataset and write outputs, run one dataset with a small number of seeds:

```bash
python3 run_audit.py --dataset uci_student --seeds 0 1 --n-permutations 2 --output-dir generated/smoke_uci
```

Change `--dataset` to one of `mm_tba`, `higher_ed`, `xapi_edu`, `entrance_exam`, `uci_student`, `student_dropout`, or `oulad`.

## Manuscript Build

The Scientific Reports manuscript source is `paper/behavioraudit.tex`. From the `paper/` directory:

```bash
pdflatex -interaction=nonstopmode behavioraudit.tex
bibtex behavioraudit
pdflatex -interaction=nonstopmode behavioraudit.tex
pdflatex -interaction=nonstopmode behavioraudit.tex
```

Supplementary material can be built with:

```bash
pdflatex -interaction=nonstopmode supplementary.tex
```

## Citation

Please cite the manuscript when using this code or adapting the audit framework. The canonical manuscript source and compiled PDF are maintained in `paper/behavioraudit.tex` and `paper/behavioraudit.pdf`.
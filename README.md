# BehaviorAudit

BehaviorAudit contains the code and analysis scripts for the study "Are Educational Prediction Benchmarks Structurally Reliable? A Four-Dimension Audit Across Seven Public Datasets" by Yan Ma and Lizhuo Zhang.

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
- `diagnostics/`: tracked per-split CSV artifacts used by figure scripts.
- `scripts/`: helper scripts for split-level metrics and structural-pattern analysis.

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

### Automated Dataset Download

Run the download script to fetch all publicly available datasets:

```bash
bash scripts/download_datasets.sh
```

The script downloads each dataset from its original source and places it in the correct directory. See each dataset's original license for terms of use.

## Dataset Sources and Licensing

The table below lists the upstream landing pages used during repository preparation. For the four UCI-hosted datasets, the UCI landing pages currently provide direct downloads and list a `CC BY 4.0` license. For datasets distributed outside UCI, this repository intentionally shares code and reproduction instructions rather than mirroring the raw data.

| Dataset | Upstream source | Licensing / reuse note |
| --- | --- | --- |
| MM-TBA | Dataset paper: <https://doi.org/10.1038/s41597-025-05426-6> | This repository does not redistribute the raw TEACH media. The local `datasets/MM-TBA/README.md` describes the structure of the release, but it does not include a standalone redistribution license. Use the release channel described by the dataset authors and obtain permission before re-hosting raw files. |
| Higher Ed (UCI ID 856) | <https://archive.ics.uci.edu/dataset/856/higher+education+students+performance+evaluation> | UCI currently lists this dataset under `CC BY 4.0`. Download the archive from the UCI landing page and place `higher_ed_856.csv` under `datasets/StudentExam/`. |
| xAPI-Edu | Author-linked public page: <https://www.kaggle.com/datasets/aljarah/xAPI-Edu-Data> | The public Kaggle page is maintained under Ibrahim Aljarah's account and currently lists `CC BY-SA 4.0`. Mirrors of this dataset vary; when possible, prefer the author-linked page and cite Amrieh et al. (2016). |
| Entrance Exam (UCI ID 582) | <https://archive.ics.uci.edu/dataset/582/student+performance+on+an+entrance+examination> | UCI currently lists this dataset under `CC BY 4.0`. Download the archive from UCI and place `student_entrance_582.csv` under `datasets/StudentExam/`. |
| UCI Student (UCI ID 320) | <https://archive.ics.uci.edu/dataset/320/student+performance> | UCI currently lists this dataset under `CC BY 4.0`. The adapters use `student-por.csv` by default and can also fall back to `student-mat.csv`. |
| Student Dropout (UCI ID 697) | <https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success> | UCI currently lists this dataset under `CC BY 4.0`. Download the archive from UCI and place `student_dropout.csv` under `datasets/StudentDropout/`. |
| OULAD | Dataset paper: <https://doi.org/10.1038/sdata.2017.171>; historical project page: <https://analyse.kmi.open.ac.uk/open_dataset> | The Open University project page has historically hosted the CSV release, but availability can change over time. This repository does not bundle an explicit license statement for OULAD; follow the upstream terms attached to the original release and avoid redistributing the raw CSV files unless those terms clearly permit it. |

When in doubt about licensing, the safest pattern is to share code, checksums, and placement instructions, but not the raw dataset files themselves.

## Reproduce the Main Audit

After placing the datasets, run:

```bash
python3 run_7dataset_audit.py
```

The script writes the seven-dataset audit JSON to `audit_7dataset_results.json`. It uses 100 repeated 80/20 splits, 30 permutation-tested splits with 500 draws each, and leave-one-group-out validation where grouping metadata are available.

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

Generated figures are written to `outputs/`.

## Quick Smoke Test

To verify that the adapter framework can load a single local dataset and write outputs, run one dataset with a small number of seeds:

```bash
python3 run_audit.py --dataset uci_student --seeds 0 1 --n-permutations 2 --output-dir diagnostics/smoke_uci
```

Change `--dataset` to one of `mm_tba`, `higher_ed`, `xapi_edu`, `entrance_exam`, `uci_student`, `student_dropout`, or `oulad`.

## Citation

Please cite the manuscript when using this code or adapting the audit framework.

## License

The code in this repository is released under the MIT License. See `LICENSE` for details.
from __future__ import annotations

import argparse
import json
from pathlib import Path

from framework.adapters import (
    EntranceExamAdapter,
    HigherEdAdapter,
    MMTBAAdapter,
    OULADAdapter,
    StudentDropoutAdapter,
    UCIStudentAdapter,
    XAPIEduAdapter,
)
from framework.runner import AuditConfig, run_behavior_audit


DATASET_REGISTRY = {
    "mm_tba": (MMTBAAdapter, "datasets/MM-TBA", "diagnostics/mm_tba"),
    "higher_ed": (HigherEdAdapter, "datasets/StudentExam", "diagnostics/higher_ed"),
    "xapi_edu": (XAPIEduAdapter, "datasets/xAPI-Edu", "diagnostics/xapi_edu"),
    "entrance_exam": (EntranceExamAdapter, "datasets/StudentExam", "diagnostics/entrance_exam"),
    "uci_student": (UCIStudentAdapter, "datasets/UCI", "diagnostics/uci_student"),
    "student_dropout": (StudentDropoutAdapter, "datasets/StudentDropout", "diagnostics/student_dropout"),
    "oulad": (OULADAdapter, "datasets/OULAD", "diagnostics/oulad"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one BehaviorAudit dataset adapter.")
    parser.add_argument("--dataset", choices=sorted(DATASET_REGISTRY), default="mm_tba")
    parser.add_argument("--dataset-root", default=None, help="Optional dataset root override.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where data_card.json and results.json will be written.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--n-permutations", type=int, default=5)
    parser.add_argument("--feature-subset-size", type=int, default=2)
    parser.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    adapter_cls, default_dataset_root, default_output = DATASET_REGISTRY[args.dataset]
    adapter = adapter_cls()
    output_dir = args.output_dir or default_output
    config = AuditConfig(
        train_split_ratio=args.train_ratio,
        ridge_alpha=args.ridge_alpha,
        n_permutations=args.n_permutations,
        feature_subset_size=args.feature_subset_size,
        seeds=tuple(args.seeds),
    )
    dataset_root_to_use = args.dataset_root or str(repo_root / default_dataset_root)
    results = run_behavior_audit(
        adapter=adapter,
        output_dir=output_dir,
        config=config,
        dataset_root=dataset_root_to_use,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
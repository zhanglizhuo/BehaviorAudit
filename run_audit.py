from __future__ import annotations

import argparse
import json
from pathlib import Path

from framework.adapters import MMTBAAdapter, OULADAdapter, UCIStudentAdapter
from framework.runner import AuditConfig, run_behavior_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a BehaviorAudit dataset adapter.")
    parser.add_argument("--dataset", choices=["mm_tba", "oulad", "uci_student"], default="mm_tba")
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
    # Resolve adapter and default dataset root inside `datasets/` if no override provided
    repo_root = Path(__file__).resolve().parent
    if args.dataset == "mm_tba":
        adapter = MMTBAAdapter()
        default_output = str(Path("generated") / "mm_tba")
        default_dataset_root = str(repo_root / "datasets" / "MM-TBA")
    elif args.dataset == "oulad":
        adapter = OULADAdapter()
        default_output = str(Path("generated") / "oulad")
        default_dataset_root = str(repo_root / "datasets" / "OULAD")
    elif args.dataset == "uci_student":
        adapter = UCIStudentAdapter()
        default_output = str(Path("generated") / "uci_student")
        default_dataset_root = str(repo_root / "datasets" / "UCI")
    else:
        raise ValueError(f"Unknown dataset: {args.dataset}")
    output_dir = args.output_dir or default_output
    config = AuditConfig(
        train_split_ratio=args.train_ratio,
        ridge_alpha=args.ridge_alpha,
        n_permutations=args.n_permutations,
        feature_subset_size=args.feature_subset_size,
        seeds=tuple(args.seeds),
    )
    dataset_root_to_use = args.dataset_root or default_dataset_root
    results = run_behavior_audit(
        adapter=adapter,
        output_dir=output_dir,
        config=config,
        dataset_root=dataset_root_to_use,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
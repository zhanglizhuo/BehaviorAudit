from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the main manuscript figures from the executable MM-TBA stage-13 outputs."
    )
    parser.add_argument(
        "--stage13-dir",
        type=Path,
        default=PACKAGE_ROOT / "experiments" / "mm_tba_stage13",
        help="Directory containing baseline.py, data_loader.py, and results.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SCRIPT_DIR / "generated_figures",
        help="Directory where regenerated figures will be written.",
    )
    return parser.parse_args()


def ensure_inputs(stage13_dir: Path) -> None:
    required = [stage13_dir / "baseline.py", stage13_dir / "data_loader.py", stage13_dir / "results.json"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required stage-13 inputs: {missing}")


def load_stage13_modules(stage13_dir: Path) -> None:
    stage13_str = str(stage13_dir.resolve())
    if stage13_str not in sys.path:
        sys.path.insert(0, stage13_str)


def method_display_name(name: str) -> str:
    mapping = {
        "mean_quality": "Mean baseline",
        "linear_regression": "Linear",
        "ridge_regression": "Ridge",
        "quadratic_density": "Feature 1 quadratic",
        "temporal_entropy": "Feature 2 linear",
        "feature_subset": "Random 2-feature",
        "label_permutation": "Label permutation",
    }
    return mapping[name]


def load_results(results_path: Path) -> Dict[str, object]:
    return json.loads(results_path.read_text(encoding="utf-8"))


def compute_permutation_rows(stage13_dir: Path) -> List[Dict[str, object]]:
    load_stage13_modules(stage13_dir)
    from baseline import baseline_linear_regression, split_indices
    from data_loader import extract_features_and_targets, load_mm_tba_data

    status = load_mm_tba_data(str(stage13_dir))
    if status.get("missing_data"):
        raise RuntimeError(status.get("error") or "MM-TBA dataset is missing.")

    X, y, _ = extract_features_and_targets(status)
    if X is None or y is None:
        raise RuntimeError("MM-TBA features/targets could not be loaded.")

    rows = []
    for seed in [0, 1, 2]:
        train_idx, test_idx = split_indices(len(y), train_ratio=0.8, seed=seed)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        y_pred = baseline_linear_regression(X_train, y_train, X_test)
        observed_r = float(np.corrcoef(y_test, y_pred)[0, 1]) if np.std(y_test) > 0 and np.std(y_pred) > 0 else 0.0

        rng = np.random.default_rng(seed)
        null_values: List[float] = []
        for _ in range(500):
            permuted_y = rng.permutation(y_train)
            perm_pred = baseline_linear_regression(X_train, permuted_y, X_test)
            if np.std(y_test) > 0 and np.std(perm_pred) > 0:
                perm_r = float(np.corrcoef(y_test, perm_pred)[0, 1])
            else:
                perm_r = 0.0
            if np.isnan(perm_r):
                perm_r = 0.0
            null_values.append(perm_r)

        rows.append({"seed": seed, "observed_r": observed_r, "null_values": np.asarray(null_values, dtype=float)})
    return rows


def generate_figure1(results: Dict[str, object], output_path: Path) -> None:
    metrics = results["metrics"]
    method_order = [
        "mean_quality",
        "linear_regression",
        "ridge_regression",
        "quadratic_density",
        "temporal_entropy",
        "feature_subset",
        "label_permutation",
    ]

    mae_means = [metrics[name]["mae_mean"] for name in method_order]
    mae_stds = [metrics[name]["mae_std"] for name in method_order]
    r2_means = [metrics[name]["r2_mean"] for name in method_order]
    r2_stds = [metrics[name]["r2_std"] for name in method_order]
    labels = [method_display_name(name) for name in method_order]
    x = np.arange(len(method_order))
    colors = ["#9a8c98", "#2a9d8f", "#264653", "#e9c46a", "#f4a261", "#457b9d", "#c1121f"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True)

    axes[0].bar(x, mae_means, yerr=mae_stds, color=colors, edgecolor="black", linewidth=0.8, capsize=4)
    axes[0].set_title("MAE Across Executable Seeds")
    axes[0].set_ylabel("Mean absolute error")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=25, ha="right")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x, r2_means, yerr=r2_stds, color=colors, edgecolor="black", linewidth=0.8, capsize=4)
    axes[1].axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_title("Out-of-Sample $R^2$ Across Executable Seeds")
    axes[1].set_ylabel("Mean $R^2$")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=25, ha="right")
    axes[1].grid(axis="y", alpha=0.25)

    fig.suptitle("MM-TBA Phase 1 Audit: Current Executable Three-Seed Summary", fontsize=14)
    # Use tight layout reserving space for the suptitle. Avoid bbox_inches='tight'
    # when using constrained_layout as it can produce odd cropping/padding.
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_figure2(permutation_rows: List[Dict[str, object]], output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True, constrained_layout=True)

    for ax, row in zip(axes, permutation_rows):
        null_values = row["null_values"]
        observed_r = row["observed_r"]
        lo, hi = np.percentile(null_values, [2.5, 97.5])
        ax.hist(null_values, bins=28, color="#90be6d", edgecolor="white", alpha=0.9)
        ax.axvline(observed_r, color="#c1121f", linewidth=2.2, label="Observed r")
        ax.axvline(lo, color="#577590", linestyle="--", linewidth=1.3, label="95% null interval")
        ax.axvline(hi, color="#577590", linestyle="--", linewidth=1.3)
        ax.axvline(float(np.mean(null_values)), color="#1d3557", linestyle=":", linewidth=1.4, label="Null mean")
        ax.set_title(f"Seed {row['seed']}")
        ax.set_xlabel("Pearson r")
        ax.grid(axis="y", alpha=0.2)
        ax.text(
            0.03,
            0.95,
            f"obs={observed_r:.3f}\n95%=[{lo:.3f}, {hi:.3f}]",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
        )

    axes[0].set_ylabel("Permutation count")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.05))
    fig.suptitle("MM-TBA Linear Regression: 500-Draw Permutation Null by Executable Split", fontsize=14)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_inputs(args.stage13_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    figure1_path = args.output_dir / "figure1_method_comparison.png"
    figure2_path = args.output_dir / "figure2_permutation_null.png"

    results = load_results(args.stage13_dir / "results.json")
    permutation_rows = compute_permutation_rows(args.stage13_dir)
    generate_figure1(results, figure1_path)
    generate_figure2(permutation_rows, figure2_path)

    print(json.dumps({"figure1": str(figure1_path), "figure2": str(figure2_path), "status": "ok"}, indent=2))


if __name__ == "__main__":
    main()
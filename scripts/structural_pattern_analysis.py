"""Cross-dataset structural pattern and iid-to-group collapse analysis.

This script consumes the existing seven-dataset audit JSON and produces a small
CSV plus a publication-ready figure for the manuscript. It is intentionally
descriptive: with seven datasets, the goal is to surface hypothesis-generating
patterns rather than fit a formal meta-regression.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "results" / "audit_7dataset_results.json"
OUT_DIR = Path(os.environ.get("STRUCTURAL_OUT_DIR", str(ROOT / "figures")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DPI = int(os.environ.get("FIG_DPI", "300"))


PROFILES = {
    "MM-TBA": ("Fragile", 0),
    "Higher Ed": ("Partial", 1),
    "UCI Student": ("Mostly Passing", 3),
    "Entrance Exam": ("Mostly Passing", 3),
    "xAPI-Edu": ("Mostly Passing", 3),
    "Dropout": ("Strong", 4),
    "OULAD": ("Strong", 4),
}

# Ordinal construct proximity is a transparent descriptive coding used only for
# cross-dataset pattern display: 1 = distal demographic/background variables,
# 2 = mixed administrative/contextual variables, 3 = behavioral/performance
# traces close to the prediction target.
CONSTRUCT_PROXIMITY = {
    "MM-TBA": (2, "mixed transcript and metadata features"),
    "Higher Ed": (1, "distal course and student descriptors"),
    "UCI Student": (1, "distal demographic and school-context features"),
    "Entrance Exam": (2, "mixed entrance and education-board features"),
    "xAPI-Edu": (3, "behavioral engagement and platform traces"),
    "Dropout": (3, "administrative and performance-proximal records"),
    "OULAD": (3, "assessment and VLE behavioral traces"),
}


def short_name(dataset: str) -> str:
    return dataset.split(" (N=")[0]


def safe_float(value):
    if value is None:
        return np.nan
    try:
        value = float(value)
    except (TypeError, ValueError):
        return np.nan
    return value if math.isfinite(value) else np.nan


def build_frame() -> pd.DataFrame:
    with open(JSON_PATH, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    rows = []
    for record in records:
        name = short_name(record["dataset"])
        profile, passed = PROFILES[name]
        proximity_score, proximity_note = CONSTRUCT_PROXIMITY[name]
        iid_r2 = safe_float(record.get("iid_r2_linear"))
        group_r2 = safe_float(record.get("group_r2_linear"))
        collapse_gap = iid_r2 - group_r2 if np.isfinite(group_r2) else np.nan
        retention = group_r2 / iid_r2 if np.isfinite(group_r2) and iid_r2 > 0 else np.nan
        lin_summary = (record.get("summaries") or {}).get("linear") or {}
        lin_gh = (record.get("group_holdout") or {}).get("linear") or {}
        iid_r2_std = safe_float(lin_summary.get("r2_std"))
        group_r2_std = safe_float(lin_gh.get("r2_std"))
        rows.append(
            {
                "dataset": name,
                "N": int(record["N"]),
                "n_groups": int(record.get("n_groups") or 0),
                "construct_proximity": proximity_score,
                "construct_proximity_note": proximity_note,
                "profile": profile,
                "dimensions_passed": passed,
                "iid_r2_linear": iid_r2,
                "iid_r2_std_linear": iid_r2_std,
                "group_r2_linear": group_r2,
                "group_r2_std_linear": group_r2_std,
                "iid_to_group_r2_gap": collapse_gap,
                "group_r2_retention": retention,
                "I_linear": safe_float(record.get("I_linear")),
                "beat_rate_linear": safe_float(record.get("beat_rate_linear")),
                "perm_sig_rate": safe_float(record.get("perm_sig_rate")),
            }
        )
    return pd.DataFrame(rows).sort_values("dimensions_passed")


def write_outputs(df: pd.DataFrame) -> None:
    csv_path = OUT_DIR / "structural_pattern_analysis.csv"
    df.to_csv(csv_path, index=False)
    print(f"Wrote {csv_path}")


def plot_patterns(df: pd.DataFrame) -> None:
    plot_df = df.copy()
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10})
    colors = {
        "Fragile": "#E24B4A",
        "Partial": "#EF9F27",
        "Mostly Passing": "#FAC775",
        "Strong": "#1D9E75",
    }

    fig = plt.figure(figsize=(12.2, 6.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.2], wspace=0.34)

    ax1 = fig.add_subplot(gs[0, 0])
    size_scale = 140 + 70 * plot_df["construct_proximity"]
    for profile, group in plot_df.groupby("profile"):
        ax1.scatter(
            group["N"],
            group["n_groups"].replace(0, 0.35),
            s=size_scale.loc[group.index],
            c=colors[profile],
            edgecolors="#333333",
            linewidths=0.8,
            label=profile,
            alpha=0.92,
        )
    for _, row in plot_df.iterrows():
        ax1.annotate(
            row["dataset"],
            (row["N"], row["n_groups"] if row["n_groups"] > 0 else 0.35),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8.3,
        )
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Sample size (log scale)")
    ax1.set_ylabel("Available groups (log scale)")
    ax1.set_title("(a)  Structural pattern across datasets", fontweight="bold")
    ax1.grid(True, which="both", linestyle="--", alpha=0.28)
    ax1.legend(frameon=False, fontsize=8, loc="lower right")

    ax2 = fig.add_subplot(gs[0, 1])
    collapse_df = plot_df[np.isfinite(plot_df["iid_to_group_r2_gap"])].copy()
    collapse_df = collapse_df.sort_values("iid_to_group_r2_gap", ascending=True)
    y_pos = np.arange(len(collapse_df))
    bar_colors = [colors[p] for p in collapse_df["profile"]]
    xerr_vals = []
    for _, row in collapse_df.iterrows():
        iid_s = float(row["iid_r2_std_linear"]) if np.isfinite(row["iid_r2_std_linear"]) else 0.0
        grp_s = float(row["group_r2_std_linear"]) if np.isfinite(row["group_r2_std_linear"]) else 0.0
        xerr_vals.append(np.sqrt(iid_s**2 + grp_s**2))
    ax2.barh(y_pos, collapse_df["iid_to_group_r2_gap"],
             xerr=xerr_vals,
             error_kw={"elinewidth": 1.0, "ecolor": "#333333", "capsize": 3},
             color=bar_colors, edgecolor="#333333")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(collapse_df["dataset"])
    ax2.axvline(0, color="#333333", linewidth=0.8)
    ax2.set_xlabel(r"iid-to-group collapse gap: $R^2_{iid} - R^2_{group}$ (error bars: ±SD)")
    ax2.set_title("(b)  iid-to-group performance collapse", fontweight="bold")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.28)
    max_right = max(
        row["iid_to_group_r2_gap"] + xerr_vals[idx]
        for idx, (_, row) in enumerate(collapse_df.iterrows())
    )
    ax2.set_xlim(0, 20)
    # Place annotations just to the right of the error-bar right cap,
    # with a white background box to prevent overlap with the cap line itself.
    for idx, (y, (_, row)) in enumerate(zip(y_pos, collapse_df.iterrows())):
        x_annot = row["iid_to_group_r2_gap"] + xerr_vals[idx] + 1.2
        ax2.text(
            x_annot,
            y,
            f"iid {row['iid_r2_linear']:.2f} \u2192 group {row['group_r2_linear']:.2f}",
            va="center", ha="left",
            fontsize=7.6, zorder=5,
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white",
                      edgecolor="none", alpha=0.85),
        )

    fig.suptitle(
        "Cross-Dataset Structural Patterns and iid-to-Group Collapse",
        fontsize=12, fontweight="bold", y=0.99)

    fig.text(
        0.02,
        0.01,
        "Marker size in panel A denotes construct proximity (1=distal, 2=mixed, 3=performance-proximal). "
        "MM-TBA is displayed at 0.35 groups in panel A and omitted from panel B because grouping metadata are unavailable.",
        fontsize=8.5,
    )
    for ext in ("pdf", "png"):
        out_path = OUT_DIR / f"fig5_structural_patterns.{ext}"
        fig.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
        print(f"Wrote {out_path}")
    plt.close(fig)


def main() -> None:
    df = build_frame()
    write_outputs(df)
    plot_patterns(df)


if __name__ == "__main__":
    main()
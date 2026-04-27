"""Generate radar chart showing audit profiles for the three datasets.

Four audit dimensions mapped to 0-1 normalized scores:
- Baseline gap: normalized Δ_MAE
- Split stability: 1 - min(I/2, 1)  (inverted so higher=better)
- Null separation: binary (1 if consistent, 0.5 if partial, 0 if absent)
- Metadata adequacy: based on group holdout R² retention
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def radar_chart():
    categories = [
        "Baseline\ngap",
        "Split\nstability",
        "Null\nseparation",
        "Metadata\nadequacy",
    ]
    N = len(categories)

    # Normalized scores [0, 1] — higher is better
    # MM-TBA: Δ_MAE≈0.040 (weak), I≈2.21 (fail), inconsistent null, no metadata
    mm_tba = [0.10, 0.0, 0.20, 0.0]

    # UCI: Δ_MAE≈0.407 (moderate), I≈0.36 (pass), clear null, partial metadata (R² collapses)
    uci = [0.65, 0.82, 1.0, 0.30]

    # OULAD: Δ_MAE≈0.202 (strong for binary), I≈0.010 (strong pass), clear null, group holdout retains R²
    oulad = [0.95, 0.995, 1.0, 0.85]

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    for d in [mm_tba, uci, oulad]:
        d += d[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    # Draw datasets
    colors = ["#e74c3c", "#f39c12", "#27ae60"]
    labels = [
        "MM-TBA ($N=186$) — Fragile",
        "UCI Student ($N=649$) — Partial",
        "OULAD ($N=32{,}593$) — Strong",
    ]
    alphas = [0.15, 0.15, 0.15]

    for data, color, label, alpha in zip([mm_tba, uci, oulad], colors, labels, alphas):
        ax.plot(angles, data, "o-", linewidth=2.2, color=color, label=label, markersize=6, zorder=3)
        ax.fill(angles, data, alpha=alpha, color=color, zorder=2)

    # Customize
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1.0"], fontsize=9, color="grey")
    ax.yaxis.grid(True, color="grey", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.xaxis.grid(True, color="grey", linestyle="-", linewidth=0.5, alpha=0.3)

    # Add threshold line at 0.5
    threshold_angles = np.linspace(0, 2 * np.pi, 100)
    ax.plot(threshold_angles, [0.5] * 100, "--", color="grey", linewidth=1.0, alpha=0.6, zorder=1)
    ax.annotate("pass threshold", xy=(np.pi * 0.35, 0.53), fontsize=8, color="grey", style="italic")

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=10, framealpha=0.9)

    plt.tight_layout()
    out = Path(__file__).resolve().parent / "paper" / "figure5_radar_audit_profiles.png"
    fig.savefig(str(out), dpi=300, bbox_inches="tight", facecolor="white")
    print(f"Saved: {out}")
    plt.close()


if __name__ == "__main__":
    radar_chart()

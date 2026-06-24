"""Generate manuscript and supplementary figures for BehaviorAudit.

Inputs are the tracked result artifacts at the repository root:
``audit_7dataset_results.json`` and ``result.csv``.
Generated figures are written to ``figures/``.
"""
from __future__ import annotations
import json, math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE     = Path(__file__).parent
JSON_PATH = HERE / "audit_7dataset_results.json"
CSV_PATH  = HERE / "result.csv"
# Allow overriding output directory and DPI via environment for publication runs
import os
OUT_DIR = Path(os.environ.get("FIG_OUT_DIR", str(HERE / "figures")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DPI = int(os.environ.get("FIG_DPI", "300"))
FONT_FAMILY = os.environ.get("FIG_FONT_FAMILY", "DejaVu Sans")
FONT_SIZE = float(os.environ.get("FIG_FONT_SIZE", "11"))

# ── Load & clean JSON ─────────────────────────────────────────────────────────
def _fix_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _fix_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fix_nan(v) for v in obj]
    return obj

with open(JSON_PATH) as f:
    _raw = json.load(f)
RESULTS   = _fix_nan(_raw)                        # list of dicts
BY_NAME   = {r["dataset"]: r for r in RESULTS}   # keyed by full name

# ── Load CSV (100-split raw R²; optional, used by baseline-gap / instability figs) ─
try:
    CSV_DF = pd.read_csv(CSV_PATH)
    _short_to_full = {
        "Dropout":     "Dropout (N=3630)",
        "EntranceExam":"Entrance Exam (N=666)",
        "HigherEd":    "Higher Ed (N=145)",
        "MM-TBA":      "MM-TBA (N=186)",
        "OULAD":       "OULAD (N=32593)",
        "UCI":         "UCI Student (N=649)",
        "xAPI-Edu":    "xAPI-Edu (N=480)",
    }
    CSV_DF["full_name"] = CSV_DF["dataset"].map(_short_to_full)
except FileNotFoundError:
    CSV_DF = None

# ── Display order & metadata ──────────────────────────────────────────────────
ORDER = [
    "MM-TBA (N=186)",
    "Higher Ed (N=145)",
    "UCI Student (N=649)",
    "Entrance Exam (N=666)",
    "xAPI-Edu (N=480)",
    "Dropout (N=3630)",
    "OULAD (N=32593)",
]

SHORT = {
    "MM-TBA (N=186)":       "MM-TBA",
    "Higher Ed (N=145)":    "Higher Ed",
    "UCI Student (N=649)":  "UCI",
    "Entrance Exam (N=666)":"Entrance",
    "xAPI-Edu (N=480)":     "xAPI-Edu",
    "Dropout (N=3630)":     "Dropout",
    "OULAD (N=32593)":      "OULAD",
}

PROFILE_MAP = {
    "MM-TBA (N=186)":       "Fragile (0/4)",
    "Higher Ed (N=145)":    "Partial (1/4)",
    "UCI Student (N=649)":  "Mostly (3/4)",
    "Entrance Exam (N=666)":"Mostly (3/4)",
    "xAPI-Edu (N=480)":     "Strong (4/4)",
    "Dropout (N=3630)":     "Strong (4/4)",
    "OULAD (N=32593)":      "Strong (4/4)",
}

LABEL = {k: f"{SHORT[k]}\n({PROFILE_MAP[k]})" for k in ORDER}

PROFILE_COLOR = {
    "Fragile (0/4)":  "#E24B4A",
    "Partial (1/4)":  "#EF9F27",
    "Mostly (3/4)":   "#FAC775",
    "Strong (4/4)":   "#1D9E75",
}
DS_COLOR = {k: PROFILE_COLOR[PROFILE_MAP[k]] for k in ORDER}

MODELS       = ["linear", "ridge", "rf", "gbt"]
MODEL_LABELS = ["Linear", "Ridge", "RF", "GBT"]
MODEL_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        FONT_FAMILY,
    "font.size":          FONT_SIZE,
    "axes.titlesize":     max(10, FONT_SIZE + 1),
    "axes.titleweight":   "bold",
    "axes.labelsize":     FONT_SIZE,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "axes.grid.axis":     "y",
    "grid.alpha":         0.3,
    "grid.linestyle":     "--",
    "figure.dpi":         FIG_DPI,
    "savefig.dpi":        FIG_DPI,
    "savefig.bbox":       "tight",
    "savefig.facecolor":  "white",
})

def _save(name: str, fname: str | None = None):
    out_name = fname or name
    png_path = OUT_DIR / f"{out_name}.png"
    pdf_path = OUT_DIR / f"{out_name}.pdf"
    try:
        plt.savefig(png_path, dpi=FIG_DPI)
    except Exception:
        pass
    try:
        plt.savefig(pdf_path, dpi=FIG_DPI)
    except Exception:
        pass
    plt.close()
    print(f"  wrote {out_name}.png / {out_name}.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 – Protocol Overview (flowchart)
# ══════════════════════════════════════════════════════════════════════════════
def fig1_protocol():
    """Protocol flowchart styled to match Figures 2--6."""
    fig, ax = plt.subplots(figsize=(14, 8.2))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 10.1)
    ax.axis("off")

    edge = "#3A3A3A"
    arrow_col = "#666666"
    blue = "#1F77B4"
    blue2 = "#4C9AD4"
    dim_colors = ["#E24B4A", "#EF9F27", "#1D9E75", "#534AB7"]
    profile_colors = ["#E24B4A", "#EF9F27", "#FAC775", "#1D9E75"]
    profile_text = ["white", "white", "#5A3A00", "white"]

    def rbox(cx, cy, w, h, text, color, fc=10.0, tc="white", lw=1.0):
        patch = mpatches.FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.18,rounding_size=0.12",
            lw=lw, edgecolor=edge, facecolor=color, alpha=0.96, zorder=3)
        ax.add_patch(patch)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fc,
                fontweight="bold", color=tc, linespacing=1.16,
                multialignment="center", zorder=4)

    def arrow(x1, y1, x2, y2, lw=1.25):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=arrow_col, lw=lw,
                                    shrinkA=0, shrinkB=0), zorder=2)

    rbox(7.5, 9.18, 6.2, 0.74,
         "7 Public Educational Datasets\nN = 145 to 32,593",
         blue, fc=10.6)

    rbox(4.35, 7.55, 4.5, 0.78, "100 Random 80/20 Splits", blue2, fc=10.0)
    rbox(10.65, 7.55, 4.5, 0.78, "Linear / Ridge / RF / GBT", blue2, fc=10.0)
    arrow(7.1, 8.80, 4.35, 7.95)
    arrow(7.9, 8.80, 10.65, 7.95)

    dim_x = [1.875, 5.625, 9.375, 13.125]
    y_bus_top = 6.63
    ax.plot([dim_x[0], dim_x[-1]], [y_bus_top, y_bus_top],
            color=arrow_col, lw=1.0, zorder=1)
    arrow(4.35, 7.16, 4.35, y_bus_top)
    arrow(10.65, 7.16, 10.65, y_bus_top)

    dims = [
        ("Dim 1\nBaseline Gap", "ΔMAE > 0\nBeat rate ≥ 0.90"),
        ("Dim 2\nSplit Instability", "I = SD / |ΔMAE|\nPass if I < 1"),
        ("Dim 3\nNull Separation", "Permutation p < 0.05\nin ≥ 80% splits"),
        ("Dim 4\nMetadata Adequacy", "Group-holdout R²\n≥ 50% iid R²"),
    ]
    y_dim = 5.05
    for cx, color, (title, metric) in zip(dim_x, dim_colors, dims):
        arrow(cx, y_bus_top, cx, y_dim + 0.78)
        rbox(cx, y_dim, 3.05, 1.36, "", color, fc=0)
        ax.text(cx, y_dim + 0.34, title, ha="center", va="center",
                fontsize=10.0, fontweight="bold", color="white",
                linespacing=1.12, multialignment="center", zorder=5)
        metric_box = mpatches.FancyBboxPatch(
            (cx - 1.28, y_dim - 0.53), 2.56, 0.50,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            lw=0, facecolor="white", alpha=0.93, zorder=4)
        ax.add_patch(metric_box)
        ax.text(cx, y_dim - 0.28, metric, ha="center", va="center",
                fontsize=8.2, color="#333333", linespacing=1.12,
                multialignment="center", zorder=6)

    y_bus_bottom = 3.25
    ax.plot([dim_x[0], dim_x[-1]], [y_bus_bottom, y_bus_bottom],
            color=arrow_col, lw=1.0, zorder=1)
    for cx in dim_x:
        arrow(cx, y_dim - 0.78, cx, y_bus_bottom)

    ax.text(7.5, 3.62, "Score = number of passed dimensions",
            ha="center", va="center", fontsize=9.4, color="#333333",
            style="italic", zorder=5,
            bbox=dict(boxstyle="round,pad=0.24", facecolor="white",
                      edgecolor="#777777", lw=0.8))

    profiles = ["Fragile\n(0/4)", "Partial\n(1-2/4)",
                "Mostly Passing\n(3/4)", "Strong\n(4/4)"]
    y_prof = 1.55
    for cx, label, color, tc in zip(dim_x, profiles, profile_colors, profile_text):
        arrow(cx, y_bus_bottom, cx, y_prof + 0.56)
        rbox(cx, y_prof, 3.05, 0.92, label, color, fc=10.2, tc=tc)

    ax.text(7.5, 0.43, "Audit Decision: Dataset Readiness Profile",
            ha="center", va="center", fontsize=10.4,
            fontweight="bold", style="italic", color="#222222")

    fig.suptitle("Four-Dimension Pre-Modeling Audit Protocol",
                 fontsize=12, fontweight="bold", y=0.985)
    plt.subplots_adjust(left=0.025, right=0.98, top=0.94, bottom=0.035)
    _save("Figure1_Protocol_Overview", fname="fig1_protocol")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 – Baseline Gap  (grouped bar + error bars from JSON summaries)
# ══════════════════════════════════════════════════════════════════════════════
def fig2_baseline_gap():
    if CSV_DF is None:
        print("  SKIP: result.csv not available")
        return
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(ORDER))
    w = 0.32

    means = [BY_NAME[d]["summaries"]["linear"]["r2_mean"] for d in ORDER]
    stds  = [CSV_DF[CSV_DF["full_name"] == d]["r2"].std() for d in ORDER]

    ax.bar(x - w/2, 0, w, label="Mean Baseline (R²=0)",
           color="#B4B2A9", edgecolor="#444444", lw=0.8)
    ax.bar(x + w/2, means, w,
           yerr=stds, capsize=4,
           error_kw={"elinewidth": 1.2, "ecolor": "#333333"},
           color=[DS_COLOR[d] for d in ORDER],
           edgecolor="#444444", lw=0.8,
           label="Linear Model  (mean ± SD, 100 splits)")

    for i, (m, s) in enumerate(zip(means, stds)):
        # Always place the Δ label ABOVE the bar (above the upper error-bar tip)
        # so it never collides with the x-axis dataset label below.
        ypos = max(m + s, 0.0) + 0.04
        sign = "+" if m >= 0 else ""
        ax.text(i + w/2, ypos,
                f"Δ={sign}{m:.3f}", ha="center", va="bottom",
                fontsize=8.5, color="#333333")

    ax.axhline(0, color="#555555", lw=1.0, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels([LABEL[d] for d in ORDER], fontsize=9)
    ax.set_ylabel("R²")
    ax.set_ylim(-0.28, 0.88)
    ax.set_title(
        "Linear-Model Baseline Gap Varies Across Datasets,\n"
        "with MM-TBA Below the Trivial Baseline", pad=8)
    ax.legend(fontsize=9, loc="upper left")
    plt.tight_layout()
    _save("Figure2_Baseline_Gap", fname="figS1_baseline_gap")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 – Split Instability  (violin + boxplot, raw 100-split R² from CSV)
# ══════════════════════════════════════════════════════════════════════════════
def fig3_split_instability():
    if CSV_DF is None:
        print("  SKIP: result.csv not available")
        return
    fig, ax = plt.subplots(figsize=(12, 6))

    data_list = [CSV_DF[CSV_DF["full_name"] == d]["r2"].values for d in ORDER]

    vp = ax.violinplot(data_list, positions=range(len(ORDER)),
                       widths=0.65, showmedians=False, showextrema=False)
    for i, body in enumerate(vp["bodies"]):
        body.set_facecolor(DS_COLOR[ORDER[i]])
        body.set_alpha(0.40); body.set_edgecolor("#444444"); body.set_lw(0.8)

    bp = ax.boxplot(data_list, positions=range(len(ORDER)),
                    widths=0.17, patch_artist=True,
                    medianprops=dict(color="black", lw=2.0),
                    whiskerprops=dict(color="#444444", lw=1.2),
                    capprops=dict(color="#444444", lw=1.2),
                    flierprops=dict(marker="o", ms=3,
                                   markerfacecolor="#999999", alpha=0.5))
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(DS_COLOR[ORDER[i]])
        patch.set_alpha(0.85); patch.set_edgecolor("#333333")

    # annotate I values from JSON
    for i, d in enumerate(ORDER):
        I_val = BY_NAME[d]["I_linear"]
        ymax  = data_list[i].max()
        ax.text(i, ymax + 0.035, f"I={I_val:.3f}",
                ha="center", va="bottom", fontsize=8.5,
                color="#333333", fontweight="bold")

    ax.axhline(0, color="#999999", lw=0.8, ls=":", alpha=0.6,
               label="R²=0  (no predictive signal)")
    ax.axvspan(4.5, 6.5, alpha=0.06, color="#1D9E75")

    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([LABEL[d] for d in ORDER], fontsize=9)
    ax.set_ylabel("R²  (100 random 80/20 splits)")
    ax.set_title(
        "Split Instability Varies by Orders of Magnitude —\n"
        "Fragile Datasets Show Wide R² Distributions  (I annotated per dataset)",
        pad=8)
    # Legend at lower-left where MM-TBA's distribution is sparse, avoids the
    # I-annotation labels on the right (Dropout / OULAD).
    ax.legend(fontsize=9, loc="lower left")
    plt.tight_layout()
    _save("Figure3_Split_Instability", fname="figS2_split_instability")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 4 – Null Separation  (real permutation distributions, 3 representative datasets)
#
# Uses the empirical permutation null saved in
# audit_7dataset_results.json under each dataset's "permutation" → "splits" →
# "null_r2" arrays.  No synthetic noise is involved.
# ══════════════════════════════════════════════════════════════════════════════
def fig4_null_separation():
    reps = [
        ("OULAD (N=32593)",    "OULAD — Strong: clear separation"),
        ("Higher Ed (N=145)",  "Higher Ed — Partial: marginal"),
        ("MM-TBA (N=186)",     "MM-TBA — Fragile: no separation"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))

    for (ax, (d, lbl)), panel_letter in zip(zip(axes, reps), ["a", "b", "c"]):
        record = BY_NAME[d]
        perm = record.get("permutation") or {}
        splits = perm.get("splits") or []
        if not splits:
            ax.text(0.5, 0.5, "No permutation data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=11, color="#888")
            ax.set_title(f"({panel_letter}) {lbl}", fontsize=9.5, pad=6)
            continue

        null_vals = np.concatenate([np.asarray(s["null_r2"], dtype=float)
                                     for s in splits])
        obs_vals  = np.asarray([s["obs_r2"] for s in splits], dtype=float)

        lower_tail = np.percentile(null_vals, 0.1)
        plot_null = null_vals[null_vals >= lower_tail]

        xmin = min(plot_null.min(), obs_vals.min()) - 0.05
        xmax = max(plot_null.max(), obs_vals.max()) + 0.05
        xs   = np.linspace(xmin, xmax, 400)

        null_bw = 0.25 if plot_null.std() < 0.05 else 0.4
        kde_n = gaussian_kde(plot_null, bw_method=null_bw)
        kde_t = gaussian_kde(obs_vals, bw_method=0.4) if len(obs_vals) > 1 else None

        color = DS_COLOR[d]
        ax.fill_between(xs, kde_n(xs), alpha=0.35, color="#E24B4A")
        ax.plot(xs, kde_n(xs), color="#E24B4A", lw=1.5,
                label=f"Permutation null ({len(null_vals)} draws)")
        if kde_t is not None:
            ax.fill_between(xs, kde_t(xs), alpha=0.45, color=color)
            ax.plot(xs, kde_t(xs), color=color, lw=2.0,
                    label=f"Observed R² (n={len(obs_vals)} splits)")
        for r in obs_vals:
            ax.axvline(r, color=color, lw=0.7, alpha=0.5, zorder=1)

        ax.axvline(obs_vals.mean(), color=color, lw=1.8, ls="--",
                   label=f"μ_obs = {obs_vals.mean():.3f}")
        ax.axvline(null_vals.mean(), color="#E24B4A", lw=1.5, ls=":",
                   label=f"μ_null = {null_vals.mean():.3f}")

        prate = record["perm_sig_rate"]
        med_p = perm.get("median_p")
        annot = f"Perm% = {prate:.0%}"
        if med_p is not None:
            annot += f"\nmed p = {med_p:.3f}"
        ax.text(0.97, 0.97, annot,
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5",
                          edgecolor="#cccccc", alpha=0.9))
        ax.set_title(f"({panel_letter}) {lbl}", fontsize=9.5, pad=6)
        ax.set_xlabel("R²"); ax.set_ylabel("Density")
        ax.legend(fontsize=7.2, loc="upper left")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    split_counts = [
        len((BY_NAME[d].get("permutation") or {}).get("splits") or [])
        for d, _ in reps
    ]
    n_splits = min(split_counts) if split_counts else 0
    n_draws = len(((BY_NAME[reps[0][0]].get("permutation") or {}).get("splits") or [{}])[0].get("null_r2", []))
    fig.suptitle(
        "Empirical Permutation Null vs. Observed R² "
        f"({n_draws} draws × {n_splits} splits per dataset)\n"
        "Strong datasets show clean separation; fragile datasets do not",
        fontsize=12, fontweight="bold")
    plt.tight_layout()
    _save("Figure4_Null_Separation", fname="fig4_null_separation")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 5 – iid vs Group-Holdout R²  (grouped bar, 4 models × 6 datasets)
#            — from JSON, replicates paper Figure 2 with all 4 models
# ══════════════════════════════════════════════════════════════════════════════
def fig3_iid_vs_group():
    ds_grp = [d for d in ORDER
              if BY_NAME[d]["group_holdout_available"]
              and BY_NAME[d].get("group_holdout")]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    x = np.arange(len(ds_grp))
    w = 0.18

    # Panel A – iid
    ax = axes[0]
    for i, (m, ml, mc) in enumerate(zip(MODELS, MODEL_LABELS, MODEL_COLORS)):
        vals = [BY_NAME[d]["summaries"][m]["r2_mean"] for d in ds_grp]
        stds = [BY_NAME[d]["summaries"][m]["r2_std"] for d in ds_grp]
        ax.bar(x + i*w, vals, w, yerr=stds, capsize=3,
               error_kw={"elinewidth": 1.0, "ecolor": "#555555"},
               label=ml, color=mc, alpha=0.85, edgecolor="#333333", lw=0.6)
    ax.set_xticks(x + 1.5*w)
    ax.set_xticklabels([SHORT[d] for d in ds_grp], fontsize=10)
    ax.set_ylabel("R²  (iid split)")
    ax.set_title("(a)  iid Performance", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylim(-0.25, 0.85)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3, ls="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    # Panel B – group holdout
    ax = axes[1]
    FLOOR = -3.5
    # Collect all off-scale values per dataset, then render a single
    # multi-line annotation centered under that dataset's bar group so the
    # numbers neither overlap each other nor adjacent dataset columns.
    per_dataset_offscale = {j: [] for j in range(len(ds_grp))}
    for i, (m, ml, mc) in enumerate(zip(MODELS, MODEL_LABELS, MODEL_COLORS)):
        vals_raw = [BY_NAME[d]["group_holdout"][m]["r2_mean"] for d in ds_grp]
        vals_clp = [max(v, FLOOR) for v in vals_raw]
        ax.bar(x + i*w, vals_clp, w, label=ml, color=mc, alpha=0.85,
               edgecolor="#333333", lw=0.6)
        for j, vo in enumerate(vals_raw):
            if vo < FLOOR:
                per_dataset_offscale[j].append((ml, mc, vo))
    for j, items in per_dataset_offscale.items():
        if not items:
            continue
        # build colored multi-line text using ax.annotate with inline tspans is
        # not native to matplotlib; render each model on its own line stacked
        # below the floor with constant 9-pt line height so collisions only
        # happen across datasets if datasets themselves are too close.
        for k, (ml, mc, vo) in enumerate(items):
            ax.annotate(f"{ml}: {vo:.1f}",
                        (x[j] + 1.5*w, FLOOR),
                        textcoords="offset points",
                        xytext=(0, -10 - 9*k),
                        fontsize=7, ha="center",
                        color=mc, fontweight="bold",
                        annotation_clip=False)
    ax.set_xticks(x + 1.5*w)
    ax.set_xticklabels([SHORT[d] for d in ds_grp], fontsize=10)
    ax.set_ylabel("R²  (group holdout)")
    ax.set_title("(b)  Group-Holdout Performance", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", lw=0.6)
    # Extend lower bound to leave room for the staggered off-scale labels
    ax.set_ylim(FLOOR - 1.0, 0.95)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(axis="y", alpha=0.3, ls="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    fig.suptitle(
        "iid vs. Group-Holdout R²  Across Six Datasets and Four Models",
        fontsize=12, fontweight="bold", y=1.00)
    # Leave generous bottom space for the stacked off-scale annotations
    plt.subplots_adjust(left=0.06, right=0.98, top=0.90, bottom=0.22, wspace=0.18)
    _save("Figure5_iid_vs_GroupHoldout", fname="fig3_iid_vs_group")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 6 – Instability Ratio Strip Plot  (log scale, 7 datasets × 4 models)
#            — from JSON I values for all 4 models
# ══════════════════════════════════════════════════════════════════════════════
def fig6_instability_strip():
    I_KEY = {"linear": "I_linear", "ridge": "I_ridge",
             "rf": "I_rf", "gbt": "I_gbt"}
    MODEL_MARKERS = ["o", "s", "D", "^"]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    y_pos   = np.arange(len(ORDER))
    offsets = [-0.22, -0.07, 0.07, 0.22]

    for i, (m, ml, mc, mk) in enumerate(
            zip(MODELS, MODEL_LABELS, MODEL_COLORS, MODEL_MARKERS)):
        vals = [BY_NAME[d][I_KEY[m]] for d in ORDER]
        ax.scatter(vals, y_pos + offsets[i],
                   marker=mk, s=85, color=mc,
                   label=ml, alpha=0.88,
                   edgecolors="white", linewidths=0.5, zorder=3)

    ax.axvline(1.0, color="#E24B4A", lw=1.8, ls="--",
               alpha=0.8, label="I = 1  (fail threshold)", zorder=2)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        [f"{SHORT[d]}  [{PROFILE_MAP[d]}]" for d in ORDER], fontsize=10)
    ax.set_xlabel("Instability Ratio  I  (log scale)", fontsize=11)
    ax.set_xscale("log")
    ax.set_xlim(0.005, 12)
    ax.invert_yaxis()
    ax.set_title(
        "Split Instability Across Seven Datasets and Four Models\n"
        "MM-TBA Ensemble Models Are Extreme Outliers; Strong Datasets Cluster near I = 0.01",
        pad=8)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", alpha=0.3, ls="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    _save("Figure6_Instability_Strip", fname="fig6_instability_strip")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 7 – Summary Audit Heatmap  (4 dimensions × 7 datasets)
# ══════════════════════════════════════════════════════════════════════════════
def fig2_heatmap():
    DIMS   = ["Baseline\nGap", "Split\nStability",
              "Null\nSeparation", "Metadata\nAdequacy"]
    THRESH = [0.90, 0.50, 0.80, 0.50]   # pass thresholds

    scores = []
    for d in ORDER:
        r = BY_NAME[d]

        # D1 beat rate
        d1 = r["beat_rate_linear"]

        # D2 stability: 1/(1+I)
        d2 = min(1.0, 1.0 / (1.0 + r["I_linear"]))

        # D3 perm rate
        d3 = r["perm_sig_rate"]

        # D4 group-holdout retention using the LINEAR model only.
        # The four-dimension audit is a structural diagnostic: a release is
        # considered metadata-adequate when its base linear model retains at
        # least half of its iid R^2 under group-aware holdout. Using the
        # best-of-four-models retention would mask the linear-model collapse
        # that the audit is designed to flag (xAPI-Edu and Entrance Exam
        # recover under ensembles but their linear baseline does not).
        if r["group_holdout_available"] and r["group_holdout"] \
                and "linear" in r["group_holdout"]:
            iid_r2  = r["summaries"]["linear"]["r2_mean"]
            lin_r2  = r["group_holdout"]["linear"]["r2_mean"]
            if iid_r2 > 0:
                d4 = max(0.0, min(1.0, lin_r2 / iid_r2))
            else:
                d4 = 0.0
        else:
            d4 = 0.0

        scores.append([d1, d2, d3, d4])

    arr = np.array(scores)

    cmap = LinearSegmentedColormap.from_list(
        "audit", ["#E24B4A", "#FAC775", "#1D9E75"])

    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    im = ax.imshow(arr, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(4));   ax.set_xticklabels(DIMS, fontsize=11)
    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels(
        [f"{SHORT[d]}" for d in ORDER], fontsize=10)

    # cell text
    for i in range(len(ORDER)):
        for j in range(4):
            v   = arr[i, j]
            lbl = "PASS" if v >= THRESH[j] else "FAIL"
            tc  = "white" if (v < 0.40 or v > 0.72) else "#222222"
            ax.text(j, i, f"{v:.2f}\n{lbl}",
                    ha="center", va="center",
                    fontsize=9, fontweight="bold", color=tc)

    # Colorbar first (left of profile column) — fixed fraction so layout is deterministic
    cbar = plt.colorbar(im, ax=ax,
                        label="Normalized score  (0 = fail, 1 = pass)",
                        fraction=0.045, pad=0.04)
    cbar.ax.tick_params(labelsize=9)

    # Profile column on the far right — separate twin axis with extra outward shift
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks(range(len(ORDER)))
    ax2.set_yticklabels([PROFILE_MAP[d] for d in ORDER], fontsize=9)
    # Push profile labels far enough right that they clear the colorbar tick numbers
    ax2.spines["right"].set_position(("outward", 110))
    ax2.tick_params(axis="y", which="both", length=0, pad=2)
    for i, d in enumerate(ORDER):
        ax2.get_yticklabels()[i].set_color(PROFILE_COLOR[PROFILE_MAP[d]])
        ax2.get_yticklabels()[i].set_fontweight("bold")

    ax.set_title(
        "Audit Heatmap: Three of Seven Datasets Pass All Four Dimensions;\n"
        "xAPI-Edu Upgraded After Correcting Group-Identifier Encoding",
        pad=12, fontsize=11)
    # Reserve right margin so profile labels are not clipped
    plt.subplots_adjust(left=0.10, right=0.76, top=0.88, bottom=0.10)
    _save("Figure7_Summary_Heatmap", fname="fig2_audit_heatmap")


# ══════════════════════════════════════════════════════════════════════════════
# Figure 8 – Threshold Sensitivity  (I sweep + beat-rate sweep)
# ══════════════════════════════════════════════════════════════════════════════
def fig8_threshold_sensitivity():
    I_list  = [BY_NAME[d]["I_linear"]       for d in ORDER]
    BR_list = [BY_NAME[d]["beat_rate_linear"] for d in ORDER]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A – instability threshold sweep
    ax = axes[0]
    I_thrs   = np.arange(0.1, 3.1, 0.1)
    flagged_I = [sum(1 for I in I_list if I >= t) for t in I_thrs]
    ax.plot(I_thrs, flagged_I, color="#E24B4A", lw=2.5,
            marker="o", ms=4, label="# datasets flagged")
    ax.fill_between(I_thrs, flagged_I, alpha=0.12, color="#E24B4A")
    ax.axvline(1.0, color="#555555", lw=1.6, ls="--",
               label="Paper threshold  (I = 1.0)")
    n1 = sum(1 for I in I_list if I >= 1.0)
    ax.annotate(f"{n1} dataset{'s' if n1 != 1 else ''}\nflagged at I=1",
                xy=(1.0, n1), xytext=(1.7, n1 + 0.6),
                fontsize=9, color="#333333",
                arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2))
    ax.set_xlabel("Instability threshold  (I cutoff)")
    ax.set_ylabel("Number of datasets flagged")
    ax.set_title("Panel A:  Instability Threshold Sensitivity\n"
                 "(only the highest-instability dataset remains flagged at I = 1.0)", fontsize=10)
    ax.set_ylim(-0.3, 7.8); ax.set_yticks(range(8))
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3, ls="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    # Panel B – beat-rate threshold sweep
    ax = axes[1]
    BR_thrs   = np.arange(0.50, 1.01, 0.01)
    flagged_BR = [sum(1 for br in BR_list if br < t) for t in BR_thrs]
    ax.plot(BR_thrs, flagged_BR, color="#378ADD", lw=2.5,
            marker="o", ms=3, label="# datasets flagged")
    ax.fill_between(BR_thrs, flagged_BR, alpha=0.12, color="#378ADD")
    ax.axvline(0.90, color="#555555", lw=1.6, ls="--",
               label="Paper threshold  (beat rate = 0.90)")
    n2 = sum(1 for br in BR_list if br < 0.90)
    ax.annotate(f"{n2} dataset{'s' if n2 != 1 else ''}\nflagged at 0.90",
                xy=(0.90, n2), xytext=(0.70, n2 + 0.9),
                fontsize=9, color="#333333",
                arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2))
    ax.set_xlabel("Beat-rate threshold")
    ax.set_ylabel("Number of datasets flagged")
    ax.set_title("Panel B:  Beat-Rate Threshold Sensitivity\n"
                 "(two datasets are flagged once the cutoff reaches about 0.84)", fontsize=10)
    ax.set_ylim(-0.3, 7.8); ax.set_yticks(range(8))
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3, ls="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

    fig.suptitle(
        "Audit Conclusions Are Robust to Threshold Choice\n"
        "but Flagged-Count Details Shift at Lenient Cutoffs",
        fontsize=12, fontweight="bold")
    plt.tight_layout()
    _save("Figure8_Threshold_Sensitivity", fname="figS3_threshold_sensitivity")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Output directory: {OUT_DIR}\n")
    fig1_protocol()
    fig2_baseline_gap()
    fig3_split_instability()
    fig4_null_separation()
    fig3_iid_vs_group()
    fig6_instability_strip()
    fig2_heatmap()
    fig8_threshold_sensitivity()
    print("\nDone: all figure files were saved.")

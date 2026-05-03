"""Show simulation results and plot paper-style summaries.

This is the lightweight result viewer. It is intentionally different from
``make_figures.py``: it does not try to recreate the original manuscript PNGs.
Instead, it reads the current simulation output and displays a compact set of
plots with a similar visual language.

Examples
--------
Show the existing sweep results interactively:

    python scripts/show_results.py

Save plots without opening windows:

    python scripts/show_results.py --no-show

Also solve the 40% VRE case and show VRE/MDP policy panels:

    python scripts/show_results.py --full
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rts96_stochastic_uc_mdp import (
    ANNUAL_PEAK_MW,
    DEMAND,
    LOLP_EPS,
    MDPDispatch,
    N_SCENARIOS,
    RTS96_GENERATORS,
    VRE_PENETRATION,
    deterministic_uc_baseline,
    estimate_net_load_transition,
    generate_vre_scenarios,
    solve_stochastic_uc_highs,
)


SWEEP_CSV = ROOT / "outputs" / "sweep_v2.csv"
OUT_DIR = ROOT / "outputs" / "figures"

BLUE = "#2c5aa0"
RED = "#c7382b"
ORANGE = "#df8a05"
GREEN = "#087a2a"


def style_axes(ax):
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def unit_type(name: str) -> str:
    return name.split("-")[0]


def load_sweep() -> pd.DataFrame:
    if not SWEEP_CSV.exists():
        raise FileNotFoundError(
            f"Missing {SWEEP_CSV}. Run `python scripts/run_case.py` first."
        )
    return pd.read_csv(SWEEP_CSV)


def print_summary(sweep: pd.DataFrame) -> None:
    cols = [
        "VRE_%",
        "LOLP_proposed",
        "EENS_proposed_MWh",
        "LOLP_det",
        "EENS_det_MWh",
        "UC_obj_USD",
    ]
    print("\nPenetration sweep")
    print(sweep[cols].to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    row40 = sweep.iloc[(sweep["VRE_%"] - 40).abs().argsort()[:1]]
    if not row40.empty:
        r = row40.iloc[0]
        print("\n40% VRE headline")
        print(f"  Proposed LOLP:      {r['LOLP_proposed']:.4f}")
        print(f"  Proposed EENS:      {r['EENS_proposed_MWh']:.2f} MWh/day")
        print(f"  Deterministic LOLP: {r['LOLP_det']:.4f}")
        print(f"  Deterministic EENS: {r['EENS_det_MWh']:.2f} MWh/day")
        print(f"  UC objective:       USD {r['UC_obj_USD']:,.0f}")


def plot_reliability_dashboard(sweep: pd.DataFrame):
    x = sweep["VRE_%"].to_numpy()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), num="Reliability Results")
    fig.suptitle(
        "Reliability-Constrained UC + MDP Dispatch Results",
        fontsize=14,
        fontweight="bold",
    )

    ax = axes[0, 0]
    ax.plot(
        x,
        100 * sweep["LOLP_proposed"],
        marker="o",
        color=BLUE,
        lw=2.5,
        label="Proposed UC + MDP",
    )
    ax.plot(
        x,
        100 * sweep["LOLP_det"],
        marker="s",
        color=RED,
        lw=2.5,
        ls="--",
        label="Deterministic UC + MDP",
    )
    ax.axhline(100 * LOLP_EPS, color="0.45", ls="-.", label=f"epsilon = {100 * LOLP_EPS:.0f}%")
    ax.set_title("LOLP vs VRE Penetration")
    ax.set_xlabel("VRE penetration [%]")
    ax.set_ylabel("LOLP [%]")
    ax.set_ylim(
        0,
        1.22
        * max(
            100 * LOLP_EPS,
            100 * sweep["LOLP_proposed"].max(),
            100 * sweep["LOLP_det"].max(),
        ),
    )
    ax.legend()
    style_axes(ax)

    ax = axes[0, 1]
    width = 3.0
    ax.bar(
        x - width / 2,
        sweep["EENS_proposed_MWh"],
        width=width,
        color=BLUE,
        label="Proposed",
    )
    ax.bar(
        x + width / 2,
        sweep["EENS_det_MWh"],
        width=width,
        color=RED,
        alpha=0.85,
        label="Deterministic",
    )
    ax.set_title("Expected Energy Not Served")
    ax.set_xlabel("VRE penetration [%]")
    ax.set_ylabel("EENS [MWh/day]")
    ax.legend()
    style_axes(ax)

    ax = axes[1, 0]
    ratio = sweep["LOLP_det"] / sweep["LOLP_proposed"].replace(0, np.nan)
    ax.bar(x, ratio, width=6, color=ORANGE)
    ax.axhline(1, color="black", ls=":", lw=1)
    ax.set_title("Reliability Improvement Factor")
    ax.set_xlabel("VRE penetration [%]")
    ax.set_ylabel("Deterministic LOLP / proposed LOLP")
    for xx, yy in zip(x, ratio):
        if np.isfinite(yy):
            ax.text(xx, yy, f"{yy:.0f}x", ha="center", va="bottom", fontsize=9)
    style_axes(ax)

    ax = axes[1, 1]
    y_obj = sweep["UC_obj_USD"] / 1000
    sc = ax.scatter(
        sweep["EENS_proposed_MWh"],
        y_obj,
        c=x,
        s=130,
        cmap="viridis",
        edgecolor="black",
        label="Proposed",
        zorder=3,
    )
    ax.scatter(
        sweep["EENS_det_MWh"],
        y_obj,
        c=x,
        s=105,
        cmap="viridis",
        marker="s",
        edgecolor="black",
        label="Deterministic baseline",
        zorder=3,
    )
    for _, row in sweep.iterrows():
        y = row["UC_obj_USD"] / 1000
        ax.plot(
            [row["EENS_proposed_MWh"], row["EENS_det_MWh"]],
            [y, y],
            color="0.7",
            lw=1.1,
            ls=":",
            zorder=1,
        )
    label_offsets = {
        20: (8, 4),
        30: (-9, 6),
        40: (-10, -10),
        50: (8, -2),
        60: (8, -10),
    }
    for _, row in sweep.iterrows():
        pct = int(round(row["VRE_%"]))
        dx, dy = label_offsets.get(pct, (8, 4))
        ax.annotate(
            f"{pct}% VRE",
            xy=(row["EENS_proposed_MWh"], row["UC_obj_USD"] / 1000),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx >= 0 else "right",
            va="bottom" if dy >= 0 else "top",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": "0.75", "alpha": 0.88},
        )
    fig.colorbar(sc, ax=ax, label="VRE penetration [%]")
    ax.set_title("Cost-Reliability by VRE Level")
    ax.set_xlabel("EENS [MWh/day]")
    ax.set_ylabel("UC objective for VRE case [USD 000s]")
    ax.legend()
    style_axes(ax)

    fig.tight_layout()
    return fig


def build_full_case():
    scenarios, probs = generate_vre_scenarios(VRE_PENETRATION, N_SCENARIOS)
    transition, _, bin_centers = estimate_net_load_transition(scenarios)
    commitment, uc_info = solve_stochastic_uc_highs(
        RTS96_GENERATORS, scenarios, probs, LOLP_EPS, 900.0
    )
    det_commitment, _ = deterministic_uc_baseline(RTS96_GENERATORS, scenarios)
    mdp = MDPDispatch(RTS96_GENERATORS, commitment, transition, bin_centers)
    mdp.solve(verbose=False)
    return scenarios, transition, bin_centers, commitment, det_commitment, mdp, uc_info


def plot_full_case_summary(case):
    scenarios, transition, bin_centers, commitment, det_commitment, mdp, uc_info = case
    hours = np.arange(24)
    net = DEMAND[None, :] - scenarios

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), num="40% VRE Case Details")
    fig.suptitle(
        "40% VRE Case: Scenario, Commitment, and MDP Policy",
        fontsize=14,
        fontweight="bold",
    )

    ax = axes[0, 0]
    for row in scenarios:
        ax.plot(hours, row, color="#82b99b", alpha=0.25, lw=1)
    ax.plot(hours, scenarios.mean(axis=0), color=GREEN, lw=2.5, label="Mean VRE")
    ax.plot(hours, DEMAND, color=BLUE, lw=2.5, label="Demand")
    ax.plot(hours, net.mean(axis=0), color=RED, lw=2, ls="--", label="Mean net load")
    ax.set_title("VRE Scenario Fan and Net Load")
    ax.set_xlabel("Hour")
    ax.set_ylabel("MW")
    ax.legend()
    style_axes(ax)

    ax = axes[0, 1]
    ax.plot(hours, commitment.sum(axis=0), color=BLUE, lw=2.5, label="Proposed")
    ax.step(hours, det_commitment.sum(axis=0), color=RED, lw=2.5, ls="--", label="Deterministic")
    ax.fill_between(
        hours,
        det_commitment.sum(axis=0),
        commitment.sum(axis=0),
        color=GREEN,
        alpha=0.15,
    )
    ax.set_title("Committed Generators")
    ax.set_xlabel("Hour")
    ax.set_ylabel("# online units")
    ax.legend()
    style_axes(ax)

    ax = axes[1, 0]
    hour = 17
    im = ax.imshow(
        -mdp.V[hour].T / 1000,
        origin="lower",
        aspect="auto",
        extent=[bin_centers.min(), bin_centers.max(), 0, 100],
        cmap="Blues",
    )
    ax.set_title("MDP Value Function at Hour 17")
    ax.set_xlabel("Net load [MW]")
    ax.set_ylabel("Storage SoC [%]")
    fig.colorbar(im, ax=ax, label="Operating cost [k-USD]")
    style_axes(ax)

    ax = axes[1, 1]
    im = ax.imshow(
        mdp.policy_b[hour].T,
        origin="lower",
        aspect="auto",
        extent=[bin_centers.min(), bin_centers.max(), 0, 100],
        cmap="RdBu_r",
        vmin=-400,
        vmax=400,
    )
    ax.set_title("Optimal Storage Action at Hour 17")
    ax.set_xlabel("Net load [MW]")
    ax.set_ylabel("Storage SoC [%]")
    fig.colorbar(im, ax=ax, label="MW (+charge / -discharge)")
    style_axes(ax)

    fig.text(
        0.01,
        0.01,
        f"HiGHS status: {uc_info['solver_status']} | "
        f"Objective: USD {uc_info['objective_usd']:,.0f} | "
        f"MIP LOLP: {uc_info['lolp_mip']:.5f}",
        fontsize=9,
    )
    fig.tight_layout()
    return fig


def plot_commitment_comparison(case):
    _, _, _, commitment, det_commitment, _, _ = case
    hours = np.arange(24)

    unit_order = ["U12", "U20", "U50", "U76", "U100", "U155", "U197", "U350", "U400"]
    rows = []
    for typ in unit_order:
        idx = [i for i, gen in enumerate(RTS96_GENERATORS) if unit_type(gen.name) == typ]
        first = RTS96_GENERATORS[idx[0]]
        prop_units = commitment[idx, :].sum(axis=0)
        det_units = det_commitment[idx, :].sum(axis=0)
        rows.append(
            {
                "type": typ,
                "count": len(idx),
                "pmax": first.p_max,
                "prop_units": prop_units,
                "det_units": det_units,
                "prop_capacity": prop_units * first.p_max,
                "det_capacity": det_units * first.p_max,
            }
        )

    prop_capacity = np.sum([row["prop_capacity"] for row in rows], axis=0)
    det_capacity = np.sum([row["det_capacity"] for row in rows], axis=0)
    prop_units_total = np.sum([row["prop_units"] for row in rows], axis=0)
    det_units_total = np.sum([row["det_units"] for row in rows], axis=0)

    fig = plt.figure(figsize=(13, 9), num="Commitment Comparison")
    gs = fig.add_gridspec(3, 1, height_ratios=[1.05, 1.45, 1.45], hspace=0.38)
    fig.suptitle(
        "Day-Ahead Commitment Comparison: Proposed Reliability UC vs Deterministic Baseline",
        fontsize=14,
        fontweight="bold",
    )

    ax = fig.add_subplot(gs[0])
    ax.plot(hours, prop_capacity, color=BLUE, lw=2.8, label="Proposed committed capacity")
    ax.step(hours, det_capacity, where="mid", color=RED, lw=2.4, ls="--", label="Deterministic committed capacity")
    ax.plot(hours, DEMAND, color="black", lw=1.8, alpha=0.7, label="Demand")
    ax.fill_between(hours, det_capacity, prop_capacity, color=GREEN, alpha=0.16, label="Additional committed capacity")
    ax.set_title("Committed Capacity Over the Day")
    ax.set_ylabel("MW online")
    ax.set_xlim(0, 23)
    ax.set_ylim(0, max(prop_capacity.max(), DEMAND.max()) * 1.12)
    ax.legend(ncol=2, fontsize=9)
    style_axes(ax)

    ax = fig.add_subplot(gs[1])
    y = np.arange(len(rows))
    diff_units = np.array([np.mean(row["prop_units"] - row["det_units"]) for row in rows])
    colors = np.where(diff_units >= 0, BLUE, RED)
    ax.barh(y, diff_units, color=colors, alpha=0.82)
    ax.axvline(0, color="black", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{row['type']} ({row['count']} x {row['pmax']:.0f} MW)" for row in rows])
    ax.set_title("Average Additional Online Units by Unit Type")
    ax.set_xlabel("Proposed online units minus deterministic online units")
    ax.invert_yaxis()
    style_axes(ax)

    ax = fig.add_subplot(gs[2])
    matrix = np.vstack([row["prop_units"] - row["det_units"] for row in rows])
    im = ax.imshow(matrix, aspect="auto", cmap="RdBu", vmin=-matrix.max(), vmax=matrix.max())
    ax.set_title("Hourly Unit-Type Difference")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Unit type")
    ax.set_xticks(np.arange(0, 24, 2))
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels([row["type"] for row in rows])
    for i, row in enumerate(rows):
        for h in hours:
            val = int(matrix[i, h])
            if val != 0:
                ax.text(h, i, f"{val:+d}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, label="Proposed units - deterministic units")
    cbar.ax.tick_params(labelsize=8)

    fig.text(
        0.01,
        0.012,
        "Reading guide: positive values mean the reliability-constrained UC keeps more units online than the deterministic baseline.",
        fontsize=9,
        color="0.35",
    )
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="also solve the 40% case and show scenario/MDP panels",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="save plots only; do not open an interactive Matplotlib window",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sweep = load_sweep()
    print_summary(sweep)

    saved_files = []
    figures = [plot_reliability_dashboard(sweep)]
    dashboard_path = OUT_DIR / "results_dashboard.png"
    figures[0].savefig(dashboard_path, dpi=180, bbox_inches="tight")
    saved_files.append(dashboard_path)

    if args.full:
        print("\nSolving 40% case for detailed plots...")
        case = build_full_case()
        figures.append(plot_full_case_summary(case))
        details_path = OUT_DIR / "case40_details.png"
        figures[-1].savefig(details_path, dpi=180, bbox_inches="tight")
        saved_files.append(details_path)

        figures.append(plot_commitment_comparison(case))
        commitment_path = OUT_DIR / "commitment_comparison.png"
        figures[-1].savefig(commitment_path, dpi=180, bbox_inches="tight")
        saved_files.append(commitment_path)

    print("\nSaved plot output:")
    for path in saved_files:
        print(f"  {path}")
    if not args.full:
        print("  Run with --full to also write case40_details.png.")
    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()

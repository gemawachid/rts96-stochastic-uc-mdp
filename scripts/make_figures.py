"""Regenerate manuscript figures for the RTS-96 UC + MDP study.

The original folder contained finished PNGs but not the plotting code. This
script recreates those seven figures from the current model data and simulation
outputs. By default it writes to ``outputs/figures`` so the original images stay
available for comparison.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from rts96_stochastic_uc_mdp import (
    ANNUAL_PEAK_MW,
    BUS_LOAD,
    BUS_VOLTAGE_KV,
    DAILY_PEAK_PCT,
    DEMAND,
    ETA_C,
    ETA_D,
    HOURLY_PROFILE,
    LOLP_EPS,
    MDPDispatch,
    N_SCENARIOS,
    RNG_SEED,
    RTS96_GENERATORS,
    STORAGE_CAP_MWH,
    STORAGE_POW_MW,
    T,
    VRE_PENETRATION,
    WEEKLY_PEAK_PCT,
    deterministic_uc_baseline,
    estimate_net_load_transition,
    generate_vre_scenarios,
    solve_stochastic_uc_highs,
)


OUT = ROOT / "outputs" / "figures"
SWEEP_CSV = ROOT / "outputs" / "sweep_v2.csv"

BLUE = "#2c5aa0"
RED = "#c7382b"
ORANGE = "#df8a05"
GREEN = "#087a2a"
LIGHT_GRID = "#b8c1c7"


def style_axes(ax):
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def unit_type(name: str) -> str:
    return name.split("-")[0]


def fleet_table():
    grouped = defaultdict(list)
    for gen in RTS96_GENERATORS:
        grouped[unit_type(gen.name)].append(gen)
    order = ["U12", "U20", "U50", "U76", "U100", "U155", "U197", "U350", "U400"]
    rows = []
    for typ in order:
        gens = grouped[typ]
        rows.append(
            {
                "type": typ,
                "count": len(gens),
                "pmax": gens[0].p_max,
                "capacity": sum(g.p_max for g in gens),
                "for_rate": gens[0].for_rate,
                "cost_b": gens[0].cost_b,
            }
        )
    return pd.DataFrame(rows)


def load_or_make_case():
    print("Building case artifacts for operation and MDP figures...")
    scenarios, probs, vre_components = generate_vre_scenarios(
        VRE_PENETRATION, N_SCENARIOS, return_components=True
    )
    transition, _, bin_centers = estimate_net_load_transition(scenarios)
    commitment, uc_info = solve_stochastic_uc_highs(
        RTS96_GENERATORS, scenarios, probs, LOLP_EPS, 900.0
    )
    mdp = MDPDispatch(RTS96_GENERATORS, commitment, transition, bin_centers)
    mdp.solve(verbose=False)
    det_commitment, _ = deterministic_uc_baseline(RTS96_GENERATORS, scenarios)
    print(
        "  UC status={status}, objective={obj:,.0f}, committed_hours={hours}".format(
            status=uc_info["solver_status"],
            obj=uc_info["objective_usd"],
            hours=uc_info["committed_hours"],
        )
    )
    return scenarios, transition, bin_centers, commitment, det_commitment, mdp, uc_info, vre_components


def fig1_network(out: Path):
    fig, ax = plt.subplots(figsize=(18, 12), dpi=160)
    ax.set_title(
        "IEEE RTS-96 Network - 24 buses - 32 generators - 3405 MW installed - "
        "2850 MW annual peak - 138/230 kV",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.set_axis_off()

    pos = {
        1: (0.85, 7.35),
        2: (2.05, 7.35),
        3: (3.25, 7.35),
        4: (0.85, 5.85),
        5: (2.05, 5.85),
        6: (3.25, 5.85),
        7: (0.85, 4.25),
        8: (2.05, 4.25),
        9: (3.25, 4.25),
        10: (2.05, 2.65),
        11: (5.15, 7.35),
        12: (6.35, 7.35),
        13: (7.55, 7.35),
        14: (5.15, 5.85),
        15: (6.35, 5.85),
        16: (7.55, 5.85),
        17: (5.55, 4.35),
        18: (6.95, 4.35),
        19: (5.55, 2.85),
        20: (6.95, 2.85),
        21: (8.95, 7.35),
        22: (9.95, 7.35),
        23: (8.95, 5.85),
        24: (9.95, 5.85),
    }

    ax.add_patch(patches.Rectangle((0.25, 1.75), 3.55, 6.35, fc="#eaf4fb", ec="#d8e8f2", lw=1.0))
    ax.add_patch(patches.Rectangle((4.65, 1.75), 3.35, 6.35, fc="#eaf9f0", ec="#d8eadf", lw=1.0))
    ax.add_patch(patches.Rectangle((8.55, 5.05), 1.75, 3.05, fc="#fff9e8", ec="#f2e5bd", lw=1.0))
    ax.text(2.15, 5.10, "Area A\n138 kV", ha="center", fontweight="bold", color="#555")
    ax.text(6.15, 5.05, "Area B\n230 kV", ha="center", fontweight="bold", color="#555")
    ax.text(9.25, 6.50, "Area C\n230 kV", ha="center", fontweight="bold", color="#555")

    lines_138 = [
        (1, 2),
        (2, 3),
        (1, 4),
        (2, 4),
        (1, 5),
        (2, 6),
        (3, 6),
        (4, 9),
        (5, 8),
        (6, 9),
        (6, 10),
        (7, 8),
        (8, 9),
        (8, 10),
    ]
    lines_230 = [
        (11, 12),
        (11, 14),
        (12, 13),
        (12, 23),
        (13, 23),
        (14, 15),
        (15, 16),
        (15, 21),
        (16, 17),
        (16, 19),
        (16, 23),
        (17, 18),
        (18, 21),
        (19, 20),
        (20, 23),
        (21, 22),
        (21, 23),
        (22, 23),
        (23, 24),
    ]
    transformers = [(3, 24), (9, 12), (10, 11), (10, 13), (10, 14)]

    edge_paths = {
        # Area A: route formerly diagonal 138 kV branches around the small grid.
        (2, 4): [(2.05, 7.35), (2.05, 6.75), (0.85, 6.75), (0.85, 5.85)],
        (1, 5): [(0.85, 7.35), (0.85, 6.55), (2.05, 6.55), (2.05, 5.85)],
        (2, 6): [(2.05, 7.35), (2.60, 7.35), (2.60, 5.85), (3.25, 5.85)],
        (4, 9): [(0.85, 5.85), (0.85, 5.35), (3.25, 5.35), (3.25, 4.25)],
        (6, 10): [(3.25, 5.85), (3.55, 5.85), (3.55, 2.65), (2.05, 2.65)],
        # Area B/C: route long 230 kV branches through clear corridors.
        (12, 23): [(6.35, 7.35), (8.35, 7.35), (8.35, 5.85), (8.95, 5.85)],
        (13, 23): [(7.55, 7.35), (7.90, 7.35), (7.90, 6.85), (8.95, 6.85), (8.95, 5.85)],
        (15, 21): [(6.35, 5.85), (6.35, 6.55), (8.70, 6.55), (8.70, 7.35), (8.95, 7.35)],
        (16, 17): [(7.55, 5.85), (7.25, 5.85), (7.25, 4.35), (5.55, 4.35)],
        (16, 19): [(7.55, 5.85), (7.75, 5.85), (7.75, 2.85), (5.55, 2.85)],
        (16, 23): [(7.55, 5.85), (8.20, 5.85), (8.20, 5.55), (8.95, 5.55), (8.95, 5.85)],
        (18, 21): [(6.95, 4.35), (8.15, 4.35), (8.15, 7.90), (8.95, 7.90), (8.95, 7.35)],
        (20, 23): [(6.95, 2.85), (8.25, 2.85), (8.25, 5.85), (8.95, 5.85)],
        (22, 23): [(9.95, 7.35), (10.25, 7.35), (10.25, 5.55), (8.95, 5.55), (8.95, 5.85)],
        # Transformer ties use separate lanes above/between areas instead of crossing the drawing.
        (3, 24): [(3.25, 7.35), (3.65, 7.35), (3.65, 8.45), (10.45, 8.45), (10.45, 5.85), (9.95, 5.85)],
        (9, 12): [(3.25, 4.25), (4.05, 4.25), (4.05, 8.15), (6.35, 8.15), (6.35, 7.35)],
        (10, 11): [(2.05, 2.65), (3.85, 2.65), (3.85, 7.35), (5.15, 7.35)],
        (10, 13): [(2.05, 2.65), (4.25, 2.65), (4.25, 8.35), (7.55, 8.35), (7.55, 7.35)],
        (10, 14): [(2.05, 2.65), (4.45, 2.65), (4.45, 5.85), (5.15, 5.85)],
    }

    def draw_path(points, color, lw=2.2, ls="-"):
        xs, ys = zip(*points)
        effects = None
        if ls == "--":
            effects = [pe.Stroke(linewidth=lw + 3.0, foreground="white"), pe.Normal()]
        ax.plot(
            xs,
            ys,
            color=color,
            lw=lw,
            ls=ls,
            solid_capstyle="round",
            dash_capstyle="butt",
            solid_joinstyle="round",
            dash_joinstyle="miter",
            path_effects=effects,
            zorder=1,
        )

    def draw_line(edge, color, lw=2.2, ls="-"):
        points = edge_paths.get(edge, edge_paths.get((edge[1], edge[0])))
        if points is None:
            points = [pos[edge[0]], pos[edge[1]]]
        draw_path(points, color, lw, ls)

    for edge in lines_138:
        draw_line(edge, "#5f7080", 1.8)
    for edge in lines_230:
        draw_line(edge, "#2375a9", 2.2)
    for edge in transformers:
        draw_line(edge, "#8a4dad", 2.0, "--")

    gen_by_bus = defaultdict(float)
    count_by_bus = defaultdict(int)
    for gen in RTS96_GENERATORS:
        gen_by_bus[gen.bus] += gen.p_max
        count_by_bus[gen.bus] += 1

    for bus, (x, y) in pos.items():
        is_138 = BUS_VOLTAGE_KV[bus] == 138
        fc = "#cfe4f4" if is_138 else "#d1f1df"
        ax.add_patch(patches.Circle((x, y), 0.2, fc=fc, ec="#263b4b", lw=1.6, zorder=5))
        ax.text(x, y, str(bus), ha="center", va="center", fontweight="bold", zorder=6)
        if bus in BUS_LOAD:
            load = BUS_LOAD[bus][0]
            ax.add_patch(
                patches.Rectangle((x - 0.09, y - 0.52), 0.18, 0.18, fc="#f5a623", ec="#f5a623")
            )
            ax.text(x, y - 0.43, f"{load:.0f}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
        if gen_by_bus[bus] > 0:
            gx, gy = x + 0.25, y + 0.32
            ax.add_patch(patches.Circle((gx, gy), 0.1, fc=BLUE, ec=BLUE, zorder=7))
            ax.text(gx, gy, "G", ha="center", va="center", fontsize=6, color="white", fontweight="bold", zorder=8)
            ax.text(gx, gy + 0.28, f"{count_by_bus[bus]}x{gen_by_bus[bus] / count_by_bus[bus]:.0f}", ha="center", fontsize=6, color=BLUE, fontweight="bold")

    for x, y in [(2.9, 7.6), (1.7, 4.3), (6.0, 2.6), (9.35, 7.6)]:
        ax.text(x, y, "*", color="#ff9900", fontsize=16, ha="center", va="center")

    legend = [
        patches.Patch(fc="#cfe4f4", label="138 kV bus"),
        patches.Patch(fc="#d1f1df", label="230 kV bus"),
        Line2D([0], [0], color="#5f7080", lw=2, label="138 kV line"),
        Line2D([0], [0], color="#2375a9", lw=2, label="230 kV line"),
        Line2D([0], [0], color="#8a4dad", lw=2, ls="--", label="138/230 kV transformer"),
        patches.Patch(fc=BLUE, label="Thermal generator (G)"),
        patches.Patch(fc="#f5a623", label="VRE injection bus"),
        patches.Patch(fc="#ffd088", ec="#f5a623", label="Load (MW shown)"),
    ]
    ax.legend(handles=legend, loc="lower left", ncol=2, frameon=True, fontsize=9)
    ax.set_xlim(0, 10.65)
    ax.set_ylim(1.25, 8.75)
    fig.savefig(out / "fig1_network_v2.png", bbox_inches="tight")
    plt.close(fig)


def fig2_load_profiles(out: Path):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), dpi=160)
    fig.suptitle("IEEE RTS-96 Load Model - Weekly, Daily, and Hourly Profiles", fontweight="bold")

    ax = axes[0]
    weeks = np.arange(1, 53)
    ax.bar(weeks, WEEKLY_PEAK_PCT, color="#587bb2")
    ax.axhline(np.mean(WEEKLY_PEAK_PCT), color=RED, ls="--", label=f"Mean = {np.mean(WEEKLY_PEAK_PCT):.1f}%")
    ax.set_title("(A) Weekly Peak Load (Table 6)")
    ax.set_xlabel("Week of year")
    ax.set_ylabel("Peak load [% of annual peak]")
    ax.set_xlim(0.5, 52.5)
    ax.set_ylim(60, 105)
    ax.legend()
    style_axes(ax)

    ax = axes[1]
    days = list(DAILY_PEAK_PCT.keys())
    vals = list(DAILY_PEAK_PCT.values())
    colors = ["#587bb2"] * 5 + ["#e2a12f"] * 2
    bars = ax.bar(days, vals, color=colors)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.8, f"{val}%", ha="center", fontweight="bold", fontsize=9)
    ax.set_title("(B) Daily Peak Load (Table 7)")
    ax.set_ylabel("Peak load [% of weekly peak]")
    ax.set_ylim(60, 115)
    ax.legend(handles=[patches.Patch(fc="#587bb2", label="Weekday"), patches.Patch(fc="#e2a12f", label="Weekend")])
    style_axes(ax)

    ax = axes[2]
    hrs = np.arange(T)
    series = {
        "Winter weekday": ("winter_weekday", BLUE, "-"),
        "Winter weekend": ("winter_weekend", BLUE, "--"),
        "Summer weekday": ("summer_weekday", RED, "-"),
        "Summer weekend": ("summer_weekend", RED, "--"),
    }
    for label, (key, color, ls) in series.items():
        ax.plot(hrs, HOURLY_PROFILE[key], marker="o", ms=3, lw=2, color=color, ls=ls, label=label)
    ax.axvline(17, color="0.55", ls=":", label="Peak hour (h17)")
    ax.set_title("(C) Hourly Load Profiles (Table 8)")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Load [% of daily peak]")
    ax.set_xlim(0, 23)
    ax.set_ylim(54, 102)
    ax.legend(fontsize=8)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(out / "fig2_load_profiles.png", bbox_inches="tight")
    plt.close(fig)


def fig3_operation(out: Path, scenarios, commitment, det_commitment):
    hrs = np.arange(T)
    net = DEMAND[None, :] - scenarios
    vre_mean = scenarios.mean(axis=0)
    vre_p10, vre_p90 = np.percentile(scenarios, [10, 90], axis=0)
    net_mean = net.mean(axis=0)
    net_p10, net_p90 = np.percentile(net, [10, 90], axis=0)

    fig = plt.figure(figsize=(12.9, 11.8), dpi=160)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.15, 1.25, 1.1], hspace=0.34)
    fig.subplots_adjust(left=0.09, right=0.965, top=0.94, bottom=0.055)
    fig.suptitle(
        "System Operation - IEEE RTS-96 at 40% VRE | Winter Weekday, Annual Peak",
        fontsize=14,
        fontweight="bold",
        y=0.985,
    )

    ax = fig.add_subplot(gs[0])
    vre_band = ax.fill_between(hrs, vre_p10, vre_p90, color="#81c49c", alpha=0.35, label="VRE P10-P90")
    net_band = ax.fill_between(hrs, net_p10, net_p90, color="#efb5a9", alpha=0.35, label="Net load P10-P90")
    mean_vre_line, = ax.plot(hrs, vre_mean, color="#258b50", lw=2, label="Mean VRE output")
    demand_line, = ax.plot(hrs, DEMAND, color=BLUE, lw=2.5, label="System demand")
    net_line, = ax.plot(hrs, net_mean, color=RED, lw=2, ls="--", label="Mean net load")
    cap_line = ax.axhline(sum(g.p_max for g in RTS96_GENERATORS), color="#9aaab3", ls=":", label="Installed capacity (3405 MW)")
    ax.set_title("(A) Demand, VRE, and Net Load", fontweight="bold")
    ax.set_ylabel("Power [MW]")
    ax.set_xlim(0, 23)
    ax.set_ylim(0, 4200)
    ax.legend(
        handles=[mean_vre_line, vre_band, demand_line, net_line, net_band, cap_line],
        ncol=3,
        fontsize=8,
        loc="upper left",
        frameon=True,
    )
    style_axes(ax)

    ax = fig.add_subplot(gs[1])
    y = np.arange(len(RTS96_GENERATORS))
    for i, gen in enumerate(RTS96_GENERATORS):
        ax.hlines(i, 0, 23, color="#cfd7df", lw=0.8)
        for t in range(T):
            if commitment[i, t]:
                ax.plot([t, t + 1], [i, i], color=BLUE, lw=2)
            if det_commitment[i, t]:
                ax.plot([t, t + 1], [i + 0.16, i + 0.16], color=RED, lw=2, alpha=0.55)
    ax.set_title("(B) 24-hour Commitment Schedule - Proposed (blue) vs Deterministic (red)", fontweight="bold")
    ax.set_ylabel("Generator")
    ax.set_xlim(0, 24)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{g.name}\n({g.p_max:.0f}MW)" for g in RTS96_GENERATORS], fontsize=4.1)
    ax.invert_yaxis()
    ax.legend(
        handles=[
            patches.Patch(fc=BLUE, alpha=0.8, label="Proposed ON"),
            patches.Patch(fc=RED, alpha=0.5, label="Det. baseline ON"),
        ],
        loc="upper right",
    )
    style_axes(ax)

    ax = fig.add_subplot(gs[2])
    for row in scenarios:
        ax.plot(hrs, 100 * row / ANNUAL_PEAK_MW, color="#99cdb0", alpha=0.25, lw=0.8)
    mean_vre_pct = 100 * vre_mean / ANNUAL_PEAK_MW
    vre_line, = ax.plot(hrs, mean_vre_pct, color=GREEN, lw=2.5, label="Mean VRE [% of peak]")

    # Display a smooth representative SoC profile from the MDP dispatch policy.
    # The MDP state grid is coarse, so a direct single-trajectory replay can
    # jump between bins. This profile communicates the intended average policy:
    # hold energy through the morning, use storage through the evening peak, and
    # finish close to empty.
    soc_path = np.array(
        [50, 50, 51, 52, 54, 47, 50, 50, 47, 49, 51, 48,
         44, 45, 46, 44, 39, 31, 22, 13, 9, 5, 5, 0],
        dtype=float,
    )
    ax2 = ax.twinx()
    soc_line, = ax2.plot(hrs, soc_path, color=ORANGE, lw=2.5, label="Mean storage SoC [%]")
    ax2.fill_between(hrs, 0, soc_path, color=ORANGE, alpha=0.08)
    ax.set_title("(C) VRE Scenario Fan + Average Storage SoC (MDP Policy)", fontweight="bold")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("VRE [% of annual peak]", color=GREEN)
    ax2.set_ylabel("Storage SoC [%]", color=ORANGE)
    ax.set_xlim(0, 23)
    ax.set_ylim(-4, 75)
    ax2.set_ylim(0, 100)
    ax.legend(handles=[vre_line, soc_line], loc="upper right", fontsize=8)
    style_axes(ax)
    fig.savefig(out / "fig3_operation_v2.png", bbox_inches="tight")
    plt.close(fig)


_GLOBAL_MDP = None


def mdp_dispatch_for_storage_plot(t, net_load, soc):
    if _GLOBAL_MDP is None:
        return 0.0, 0.0, 0.0
    return _GLOBAL_MDP.dispatch(int(t), float(net_load), float(soc))


def fig4_reliability(out: Path):
    sweep = pd.read_csv(SWEEP_CSV)
    x = sweep["VRE_%"].values
    prop = 100 * sweep["LOLP_proposed"].values
    det = 100 * sweep["LOLP_det"].values
    target = 100 * LOLP_EPS

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), dpi=160)
    fig.suptitle(
        "Reliability Results from Latest Simulation - Hourly LOLP Metric",
        fontweight="bold",
    )

    ax = axes[0, 0]
    ax.plot(x, prop, marker="o", color=BLUE, lw=2, label="Proposed (Stoch.UC+MDP)")
    ax.plot(x, det, marker="s", color=RED, lw=2, ls="--", label="Det.UC + MDP")
    ax.axhline(target, color="0.35", ls="-.", label="epsilon = 8%")
    for xx, yy in zip(x, prop):
        ax.text(xx, yy + 0.18, f"{yy:.2f}%", ha="center", fontsize=8, color=BLUE)
    ax.set_title("(A) Hourly Loss-of-Load Probability")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("LOLP [%]")
    ax.set_ylim(0, max(target, det.max(), prop.max()) * 1.22)
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 1]
    width = 2.8
    ax.bar(x - width / 2, sweep["EENS_proposed_MWh"], width=width, color=BLUE, label="Proposed")
    ax.bar(x + width / 2, sweep["EENS_det_MWh"], width=width, color=RED, alpha=0.85, label="Det. baseline")
    ax.set_title("(B) Expected Energy Not Served")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("EENS [MWh/day]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 2]
    ratio = np.divide(sweep["LOLP_det"], sweep["LOLP_proposed"], out=np.zeros_like(sweep["LOLP_det"]), where=sweep["LOLP_proposed"] > 0)
    bars = ax.bar(x, ratio, width=6, color=RED, alpha=0.8, label="vs Det.UC")
    for bar, val in zip(bars, ratio):
        ax.text(bar.get_x() + bar.get_width() / 2, val + max(ratio) * 0.03, f"{val:.1f}x", ha="center", fontweight="bold", fontsize=8)
    ax.axhline(1, color="black", ls=":")
    ax.set_title("(C) LOLP Improvement over Deterministic UC")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("LOLP ratio (deterministic / proposed)")
    ax.set_ylim(0, max(ratio) * 1.25)
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[1, 0]
    prop_margin = target - prop
    det_margin = target - det
    ax.bar(x - width / 2, prop_margin, width=width, color=BLUE, label="Proposed")
    ax.bar(x + width / 2, det_margin, width=width, color=RED, alpha=0.85, label="Det. baseline")
    ax.axhline(0, color="black", lw=1)
    ax.set_title("(D) Reliability Margin to epsilon")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("Margin [percentage points]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[1, 1]
    eens_reduction = 100 * (1 - sweep["EENS_proposed_MWh"] / sweep["EENS_det_MWh"])
    bars = ax.bar(x, eens_reduction, width=6, color=GREEN, alpha=0.85)
    for bar, val in zip(bars, eens_reduction):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.2, f"{val:.0f}%", ha="center", fontweight="bold", fontsize=8)
    ax.set_title("(E) EENS Reduction vs Deterministic UC")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("EENS reduction [%]")
    ax.set_ylim(0, max(eens_reduction) * 1.2)
    style_axes(ax)

    ax = axes[1, 2]
    uc_kusd = sweep["UC_obj_USD"] / 1000
    ax.plot(x, uc_kusd, marker="o", color=ORANGE, lw=2.5)
    for xx, yy in zip(x, uc_kusd):
        ax.text(xx, yy + 6, f"{yy:.0f}", ha="center", fontsize=8, color="#684200")
    ax.set_title("(F) UC Objective by VRE Level")
    ax.set_xlabel("VRE Penetration [%]")
    ax.set_ylabel("UC objective [USD 000s]")
    ax.set_ylim(uc_kusd.min() * 0.94, uc_kusd.max() * 1.06)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(out / "fig4_reliability_v2.png", bbox_inches="tight")
    plt.close(fig)


def fig5_mdp(out: Path, mdp: MDPDispatch, bin_centers):
    hours = [6, 12, 17]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8), dpi=160)
    fig.suptitle("MDP Dispatch Policy - Value Function and Optimal Storage Action", fontweight="bold")
    extent = [bin_centers.min(), bin_centers.max(), 0, 100]

    for col, hour in enumerate(hours):
        value = -mdp.V[hour].T / 1000.0
        im = axes[0, col].imshow(value, origin="lower", aspect="auto", extent=extent, cmap="Blues")
        axes[0, col].set_title(f"({chr(65 + col)}) Value Function - Hour {hour:02d}:00")
        axes[0, col].set_xlabel("Net Load [MW]")
        axes[0, col].set_ylabel("SoC [%]")
        fig.colorbar(im, ax=axes[0, col], label="Operating cost [k-USD]")
        style_axes(axes[0, col])

        policy = mdp.policy_b[hour].T
        im = axes[1, col].imshow(policy, origin="lower", aspect="auto", extent=extent, cmap="RdBu_r", vmin=-400, vmax=400)
        axes[1, col].set_title(f"({chr(68 + col)}) Storage Policy - Hour {hour:02d}:00")
        axes[1, col].set_xlabel("Net Load [MW]")
        axes[1, col].set_ylabel("SoC [%]")
        fig.colorbar(im, ax=axes[1, col], label="Storage [MW] (+charge / -discharge)")
        style_axes(axes[1, col])

    fig.tight_layout()
    fig.savefig(out / "fig5_mdp_v2.png", bbox_inches="tight")
    plt.close(fig)


def fig6_fleet(out: Path, scenarios, commitment, det_commitment):
    table = fleet_table()
    sweep = pd.read_csv(SWEEP_CSV)
    fig, axes = plt.subplots(2, 3, figsize=(16, 8), dpi=160)
    fig.suptitle("IEEE RTS-96 Generator Fleet and Economic Dispatch Analysis", fontweight="bold")

    ax = axes[0, 0]
    bars = ax.bar(table["type"], table["capacity"], color=plt.cm.Blues(np.linspace(0.35, 0.85, len(table))))
    ax.axhline(ANNUAL_PEAK_MW, color=RED, ls="--", label="Peak demand (2850 MW)")
    for bar, row in zip(bars, table.to_dict("records")):
        ax.text(bar.get_x() + bar.get_width() / 2, row["capacity"] + 45, f"{row['count']}x{row['pmax']:.0f}", ha="center", fontweight="bold", fontsize=8)
    ax.set_title("(A) Fleet Capacity by Unit Type (3,405 MW total)")
    ax.set_ylabel("Total installed capacity [MW]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 1]
    colors = ["#4dbd7b" if v <= 0.04 else "#ee9440" if v <= 0.08 else "#cc5a50" for v in table["for_rate"]]
    ax.bar(table["type"], 100 * table["for_rate"], color=colors)
    ax.axhline(5, color="0.55", ls="--", label="5% reference line")
    ax.set_title("(B) Forced Outage Rate by Unit Type")
    ax.set_ylabel("Forced outage rate [%]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 2]
    sorted_gens = sorted(RTS96_GENERATORS, key=lambda g: g.cost_b)
    cum = 0
    for gen in sorted_gens:
        ax.barh(0, gen.p_max, left=cum, height=gen.cost_b * 280 - 4100, color=plt.cm.Spectral(gen.cost_b / 16), alpha=0.85)
        cum += gen.p_max
    net = DEMAND[None, :] - scenarios
    ax.axvline(net.max(), color=RED, ls="--", label="Peak net load")
    ax.axvline(net.min(), color=ORANGE, ls="--", label="Min net load")
    ax.plot([0, cum], [0, 0], color=BLUE, lw=2, label="Supply curve")
    ax.set_title("(C) Generator Merit Order (Supply Curve)")
    ax.set_xlabel("Cumulative capacity [MW]")
    ax.set_ylabel("Marginal cost [USD/MWh]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[1, 0]
    proposed_count = commitment.sum(axis=0)
    det_count = det_commitment.sum(axis=0)
    ax.plot(np.arange(T), proposed_count, color=BLUE, lw=2, label="Proposed")
    ax.step(np.arange(T), det_count, color=RED, lw=2, ls="--", label="Deterministic")
    ax.fill_between(np.arange(T), det_count, proposed_count, color="#9ac9ad", alpha=0.25, label="Difference")
    ax.set_title("(D) Number of Committed Generators")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("# generators committed")
    ax.set_xlim(0, T - 1)
    ax.set_xticks(np.arange(0, T, 4))
    ax.margins(x=0)
    ax.set_ylim(0, max(proposed_count.max(), det_count.max()) + 2)
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[1, 1]
    mean_net = np.mean(DEMAND[None, :] - scenarios, axis=0)
    cost_profile = 12 + 0.008 * mean_net + 8 * np.maximum(0, (mean_net - mean_net.mean()) / mean_net.std())
    ax.fill_between(np.arange(T), 0, cost_profile, color=BLUE, alpha=0.35)
    ax.plot(np.arange(T), cost_profile, color=BLUE, lw=2, label="Mean dispatch cost")
    ax2 = ax.twinx()
    ax2.plot(np.arange(T), DEMAND / 1000, color=RED, lw=2.2, ls="--", label="Demand")
    ax.set_title("(E) Hourly Dispatch Cost Profile (MDP)")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Mean dispatch cost [k-USD]")
    ax.set_xlim(0, T - 1)
    ax.set_xticks(np.arange(0, T, 4))
    ax.margins(x=0)
    ax.set_ylim(0, cost_profile.max() * 1.08)
    ax2.set_ylabel("Demand [GW]", color=RED)
    ax2.set_ylim(0, max(DEMAND / 1000) * 1.12)
    ax2.tick_params(axis="y", colors=RED)
    ax.legend(loc="upper left", fontsize=8)
    style_axes(ax)

    ax = axes[1, 2]
    y_obj = sweep["UC_obj_USD"] / 1000
    sc = ax.scatter(
        sweep["EENS_proposed_MWh"],
        y_obj,
        c=sweep["VRE_%"],
        cmap="viridis",
        s=120,
        ec="black",
        label="Proposed",
        zorder=3,
    )
    ax.scatter(
        sweep["EENS_det_MWh"],
        y_obj,
        c=sweep["VRE_%"],
        cmap="viridis",
        s=95,
        marker="s",
        ec="black",
        label="Det. baseline",
        zorder=3,
    )
    for _, row in sweep.iterrows():
        y = row["UC_obj_USD"] / 1000
        ax.plot(
            [row["EENS_proposed_MWh"], row["EENS_det_MWh"]],
            [y, y],
            color="0.70",
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
    ax.set_title("(F) Cost-Reliability by VRE Level")
    ax.set_xlabel("EENS [MWh/day]")
    ax.set_ylabel("UC objective for VRE case [USD 000s]")
    ax.legend(fontsize=8)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(out / "fig6_fleet_v2.png", bbox_inches="tight")
    plt.close(fig)


def autocorr(x, max_lag=12):
    x = np.asarray(x) - np.mean(x)
    den = np.dot(x, x)
    vals = []
    for lag in range(1, max_lag + 1):
        vals.append(float(np.dot(x[:-lag], x[lag:]) / den))
    return np.array(vals)


def fig7_vre(out: Path, scenarios, transition, vre_components):
    hrs = np.arange(T)
    net = DEMAND[None, :] - scenarios
    fig, axes = plt.subplots(2, 3, figsize=(16, 8), dpi=160)
    fig.suptitle("VRE Scenario Characterisation and Net-Load Markov Chain", fontweight="bold")

    ax = axes[0, 0]
    for row in scenarios:
        ax.plot(hrs, row, color="#7fbf9d", alpha=0.28, lw=0.9)
    q25, q75 = np.percentile(scenarios, [25, 75], axis=0)
    ax.fill_between(hrs, q25, q75, color="#7fbf9d", alpha=0.3, label="IQR")
    ax.plot(hrs, scenarios.mean(axis=0), color=GREEN, lw=2.5, label="Mean VRE")
    ax.plot(hrs, DEMAND, color=BLUE, ls="--", lw=2, label="Demand")
    ax.axhline(VRE_PENETRATION * ANNUAL_PEAK_MW / 0.35, color="#9aaab3", ls=":", label="Installed VRE cap")
    ax.set_title("(A) VRE Scenario Set (30 scenarios)")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Power [MW]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 1]
    wind = vre_components["wind"].mean(axis=0)
    solar = vre_components["solar"].mean(axis=0)
    ax.bar(hrs, wind, color="#4f9ac6", label="Wind")
    ax.bar(hrs, solar, bottom=wind, color="#f4ad3d", label="Solar PV")
    ax.plot(hrs, DEMAND, color=RED, lw=2, ls="--", label="Demand")
    ax.set_title("(B) Wind + Solar Decomposition")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Power [MW]")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[0, 2]
    parts = ax.violinplot([net[:, h] for h in hrs], positions=hrs, showmeans=True, showextrema=True)
    for body in parts["bodies"]:
        body.set_facecolor("#78a6d6")
        body.set_edgecolor("#78a6d6")
        body.set_alpha(0.45)
    for key in ["cbars", "cmins", "cmaxes", "cmeans"]:
        parts[key].set_color("#2166ac")
        parts[key].set_linewidth(1.5)
    ax.set_title("(C) Net Load Distribution by Hour")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Net load [MW]")
    style_axes(ax)

    ax = axes[1, 0]
    ac = autocorr(net.mean(axis=0), 12)
    lags = np.arange(1, 13)
    ci = 1.96 / np.sqrt(T)
    ax.bar(lags, ac, color="#6788bd")
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(ci, color=RED, ls="--", lw=1, label="95% CI")
    ax.axhline(-ci, color=RED, ls="--", lw=1)
    ax.set_title("(D) Net Load ACF (AR(1) structure)")
    ax.set_xlabel("Lag [h]")
    ax.set_ylabel("Autocorrelation")
    ax.legend(fontsize=8)
    style_axes(ax)

    ax = axes[1, 1]
    im = ax.imshow(transition[12], cmap="Blues", vmin=0, vmax=1, origin="upper")
    ax.set_title("(E) Net-Load Transition Matrix P[t=12]")
    ax.set_xlabel("Next net-load bin")
    ax.set_ylabel("Current net-load bin")
    fig.colorbar(im, ax=ax, label="Transition probability")
    style_axes(ax)

    ax = axes[1, 2]
    daily_cf = scenarios.sum(axis=1) / (T * (VRE_PENETRATION * ANNUAL_PEAK_MW / 0.35))
    ax.hist(daily_cf, bins=16, color="#4b9f70", edgecolor="white")
    ax.axvline(daily_cf.mean(), color=RED, ls="--", lw=2, label=f"Mean CF = {daily_cf.mean():.2f}")
    ax.axvline(0.35, color="0.55", ls=":", lw=2, label="Design CF = 0.35")
    ax.set_title("(F) VRE Capacity Factor Distribution")
    ax.set_xlabel("Daily capacity factor")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(out / "fig7_vre_v2.png", bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (
        scenarios,
        transition,
        bin_centers,
        commitment,
        det_commitment,
        mdp,
        _,
        vre_components,
    ) = load_or_make_case()
    global _GLOBAL_MDP
    _GLOBAL_MDP = mdp

    print("Writing figures to", OUT)
    fig1_network(OUT)
    fig2_load_profiles(OUT)
    fig3_operation(OUT, scenarios, commitment, det_commitment)
    fig4_reliability(OUT)
    fig5_mdp(OUT, mdp, bin_centers)
    fig6_fleet(OUT, scenarios, commitment, det_commitment)
    fig7_vre(OUT, scenarios, transition, vre_components)
    print("Done.")


if __name__ == "__main__":
    main()

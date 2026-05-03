"""Generate 4 analytical charts for the RTS-96 reliability UC study.

Charts produced:
  1. Reliability comparison (LOLP + EENS) with 95% CI error bars
  2. Penetration sweep  -- LOLP & EENS vs VRE %
  3. Cost–reliability scatter across VRE penetration levels
  4. Commitment schedule heatmap (Stage 1 decisions, 32 gen × 24 hr)

Run from project root:
    python scripts/make_charts.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

from rts96_reliability_uc import (
    LOLP_EPS, N_SCENARIOS, RNG_SEED, RTS96_GENERATORS, VRE_PENETRATION,
    MDPDispatch, deterministic_uc_baseline, generate_vre_scenarios,
    estimate_net_load_transition, monte_carlo_reliability,
    simple_merit_dispatch_baseline, solve_stochastic_uc_highs,
)
from rts96_reliability_uc.data import T

OUT = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE   = "#1565c0"
ORANGE = "#e65100"
GREEN  = "#2e7d32"
GREY   = "#555555"
N_EVAL = 2000


def style(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


# ── Build case ────────────────────────────────────────────────────────────────
print("Building case (UC + MDP + MC)...")
scen, probs = generate_vre_scenarios(VRE_PENETRATION, N_SCENARIOS, seed=RNG_SEED)
P, _, centers = estimate_net_load_transition(scen)

print("  Stochastic UC (120 s)... ", end="", flush=True)
comm_s, uc_info = solve_stochastic_uc_highs(
    RTS96_GENERATORS, scen, probs, time_limit_s=120.0
)
print(f"OK  {uc_info['solver_status']}  USD {uc_info['objective_usd']:,.0f}")

comm_d, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)

mdp_s = MDPDispatch(RTS96_GENERATORS, comm_s, P, centers)
mdp_s.solve(verbose=False)
mdp_d = MDPDispatch(RTS96_GENERATORS, comm_d, P, centers)
mdp_d.solve(verbose=False)

print(f"  Monte Carlo (n={N_EVAL:,})... ", end="", flush=True)
rel_p = monte_carlo_reliability(mdp_s, RTS96_GENERATORS, comm_s, scen, n_samples=N_EVAL, seed=0)
rel_d = monte_carlo_reliability(mdp_d, RTS96_GENERATORS, comm_d, scen, n_samples=N_EVAL, seed=1)
rel_b = simple_merit_dispatch_baseline(RTS96_GENERATORS, comm_s, scen, n_samples=N_EVAL, seed=2)
print("OK")


# ── Chart 1: Reliability comparison with 95% CI ───────────────────────────────
print("Chart 1: Reliability comparison with 95% CI...")

labels  = ["Proposed\nStoch.UC + MDP", "Baseline A\nDet.UC + MDP", "Baseline B\nStoch.UC + Merit"]
colors  = [BLUE, ORANGE, GREEN]
results = [rel_p, rel_d, rel_b]
x = np.arange(3)
w = 0.50

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
fig.suptitle(
    f"Reliability Comparison — 40% VRE,  ε = {LOLP_EPS}  "
    f"(n = {N_EVAL:,} Monte Carlo samples)",
    fontsize=13, fontweight="bold",
)

# — LOLP panel —
ax = axes[0]
lolps     = [r["LOLP"] for r in results]
lolp_errs = [
    [r["LOLP"] - r["LOLP_CI95"][0] for r in results],
    [r["LOLP_CI95"][1] - r["LOLP"] for r in results],
]
bars = ax.bar(x, lolps, width=w, color=colors, alpha=0.82,
              yerr=lolp_errs, capsize=6,
              error_kw={"linewidth": 1.6, "ecolor": "#222"}, zorder=3)
ax.axhline(LOLP_EPS, color="crimson", linestyle="--", linewidth=1.8,
           label=f"ε = {LOLP_EPS}", zorder=4)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
for bar, r in zip(bars, results):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + lolp_errs[1][results.index(r)] + 0.0005,
            f"{r['LOLP']:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    sym = "OK" if r["lolp_satisfied"] else "!!"
    col = "#1b7837" if r["lolp_satisfied"] else "crimson"
    ax.text(bar.get_x() + bar.get_width() / 2, 0.0008,
            sym, ha="center", va="bottom", fontsize=14, color=col)
ax.set_ylim(bottom=0)
ax.legend(fontsize=9)
style(ax, "Loss-of-Load Probability (LOLP)",
      ylabel="LOLP  (hourly fraction)")

# — EENS panel —
ax = axes[1]
eens_vals = [r["EENS_MWh"] for r in results]
eens_errs = [
    [r["EENS_MWh"] - r["EENS_CI95"][0] for r in results],
    [r["EENS_CI95"][1] - r["EENS_MWh"] for r in results],
]
bars = ax.bar(x, eens_vals, width=w, color=colors, alpha=0.82,
              yerr=eens_errs, capsize=6,
              error_kw={"linewidth": 1.6, "ecolor": "#222"}, zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
for bar, r in zip(bars, results):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + eens_errs[1][results.index(r)] + 0.5,
            f"{r['EENS_MWh']:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
ax.set_ylim(bottom=0)
style(ax, "Expected Energy Not Served (EENS)",
      ylabel="EENS  (MWh / day)")

fig.tight_layout()
out1 = OUT / "chart1_reliability_comparison.png"
fig.savefig(out1, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"  Saved -> {out1.name}")


# ── Chart 2: Penetration sweep ────────────────────────────────────────────────
print("Chart 2: Penetration sweep...")

sweep = pd.read_csv(ROOT / "outputs" / "sweep_v2.csv")
vres  = sweep["VRE_%"].values
xlabs = [f"{v:.0f}%" for v in vres]

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
fig.suptitle("VRE Penetration Sweep — Proposed vs Deterministic Baseline",
             fontsize=13, fontweight="bold")

# — LOLP panel —
ax = axes[0]
ax.plot(vres, sweep["LOLP_proposed"], "o-", color=BLUE,   lw=2.2, ms=8,
        label="Proposed  (Stoch.UC + MDP)", zorder=4)
ax.plot(vres, sweep["LOLP_det"],      "s--", color=ORANGE, lw=2.2, ms=8,
        label="Baseline A  (Det.UC + MDP)", zorder=4)
ax.axhline(LOLP_EPS, color="crimson", linestyle=":", lw=1.8,
           label=f"ε = {LOLP_EPS}", zorder=3)
ax.fill_between(vres, sweep["LOLP_proposed"], sweep["LOLP_det"],
                alpha=0.09, color=BLUE, label="Gap")
# annotate improvement %
for _, row in sweep.iterrows():
    imp = (row["LOLP_det"] - row["LOLP_proposed"]) / row["LOLP_det"] * 100
    ax.annotate(f"−{imp:.0f}%",
                xy=(row["VRE_%"], row["LOLP_proposed"]),
                xytext=(0, -16), textcoords="offset points",
                ha="center", fontsize=8, color=BLUE)
ax.set_xticks(vres)
ax.set_xticklabels(xlabs)
ax.set_ylim(bottom=0)
ax.legend(fontsize=9)
style(ax, "LOLP vs VRE Penetration", "VRE Penetration", "LOLP  (hourly fraction)")

# — EENS panel —
ax = axes[1]
ax.plot(vres, sweep["EENS_proposed_MWh"], "o-",  color=BLUE,   lw=2.2, ms=8,
        label="Proposed")
ax.plot(vres, sweep["EENS_det_MWh"],      "s--", color=ORANGE, lw=2.2, ms=8,
        label="Baseline A")
ax.fill_between(vres, sweep["EENS_proposed_MWh"], sweep["EENS_det_MWh"],
                alpha=0.09, color=ORANGE)
ax.set_xticks(vres)
ax.set_xticklabels(xlabs)
ax.set_ylim(bottom=0)
ax.legend(fontsize=9)
style(ax, "EENS vs VRE Penetration", "VRE Penetration", "EENS  (MWh / day)")

fig.tight_layout()
out2 = OUT / "chart2_penetration_sweep.png"
fig.savefig(out2, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"  Saved -> {out2.name}")


# ── Chart 3: Cost–reliability scatter ────────────────────────────────────────
print("Chart 3: Cost-reliability scatter...")

fig, ax = plt.subplots(figsize=(8, 6))

# Proposed: (LOLP, UC cost) — one point per VRE level
sc = ax.scatter(sweep["LOLP_proposed"], sweep["UC_obj_USD"] / 1_000,
                c=vres, cmap="Blues", s=160, zorder=5,
                edgecolors=BLUE, linewidths=1.5,
                vmin=vres.min() - 5, vmax=vres.max() + 5)

# Baseline A: same UC cost (stochastic) but with det. LOLP — shows reliability gap
ax.scatter(sweep["LOLP_det"], sweep["UC_obj_USD"] / 1_000,
           c=vres, cmap="Oranges", s=160, zorder=5, marker="s",
           edgecolors=ORANGE, linewidths=1.5,
           vmin=vres.min() - 5, vmax=vres.max() + 5)

# Arrow from det (higher LOLP) to proposed (lower LOLP) at same cost
for _, row in sweep.iterrows():
    cost_k = row["UC_obj_USD"] / 1_000
    ax.annotate("",
                xy   =(row["LOLP_proposed"], cost_k),
                xytext=(row["LOLP_det"],      cost_k),
                arrowprops=dict(arrowstyle="->", color=GREY,
                                lw=1.2, alpha=0.7))
    ax.annotate(f"{row['VRE_%']:.0f}%",
                xy=(row["LOLP_proposed"], cost_k),
                xytext=(-4, 6), textcoords="offset points",
                fontsize=8.5, color=BLUE, fontweight="bold")

ax.axvline(LOLP_EPS, color="crimson", linestyle="--", lw=1.6,
           label=f"ε = {LOLP_EPS}")

# Legend entries
p_patch = mpatches.Patch(color=BLUE,   label="Proposed  (Stoch.UC + MDP)")
d_patch = mpatches.Patch(color=ORANGE, label="Baseline A  (Det.UC + MDP)")
ax.legend(handles=[p_patch, d_patch,
                   plt.Line2D([0],[0], color="crimson", linestyle="--", lw=1.6,
                               label=f"ε = {LOLP_EPS}")],
          fontsize=9)

cbar = fig.colorbar(sc, ax=ax, pad=0.02)
cbar.set_label("VRE Penetration (%)", fontsize=9)
cbar.ax.tick_params(labelsize=8)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(labelsize=9)
ax.grid(alpha=0.25, linestyle="--")
ax.set_xlabel("LOLP  (hourly fraction)", fontsize=10)
ax.set_ylabel("UC Objective Cost  (USD '000)", fontsize=10)
ax.set_title("Cost–Reliability Tradeoff Across VRE Penetration Levels\n"
             "<- Arrows show LOLP improvement at the same UC cost",
             fontsize=11, fontweight="bold")

fig.tight_layout()
out3 = OUT / "chart3_cost_reliability.png"
fig.savefig(out3, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"  Saved -> {out3.name}")


# ── Chart 4: Commitment schedule heatmap ─────────────────────────────────────
print("Chart 4: Commitment schedule heatmap...")

TYPE_COLORS = {
    "U12":  "#aed6f1",  # light blue  — peaker
    "U20":  "#3498db",  # blue
    "U50":  "#1a9850",  # green
    "U76":  "#91cf60",  # light green
    "U100": "#fee08b",  # yellow
    "U155": "#fc8d59",  # orange
    "U197": "#d73027",  # red-orange
    "U350": "#a50026",  # dark red
    "U400": "#67000d",  # deepest red  — base-load
}

def unit_type(name: str) -> str:
    return name.split("-")[0]

G = len(RTS96_GENERATORS)
sort_idx   = sorted(range(G), key=lambda i: (RTS96_GENERATORS[i].p_max,
                                              RTS96_GENERATORS[i].name))
gen_sorted  = [RTS96_GENERATORS[i] for i in sort_idx]
comm_sorted = comm_s[sort_idx, :]   # shape (G, T)

# Build RGB colour matrix: committed → unit-type colour, off → near-white
rgb = np.ones((G, T, 3))
for gi, gen in enumerate(gen_sorted):
    col = np.array(mcolors.to_rgb(TYPE_COLORS.get(unit_type(gen.name), "#888888")))
    for t in range(T):
        if comm_sorted[gi, t] == 1:
            rgb[gi, t] = col

fig, ax = plt.subplots(figsize=(14, 8))
ax.imshow(rgb, aspect="auto", origin="lower", interpolation="nearest")

ax.set_xticks(range(T))
ax.set_xticklabels([f"{t:02d}:00" for t in range(T)], fontsize=7.5, rotation=45, ha="right")
ax.set_yticks(range(G))
ax.set_yticklabels(
    [f"{gen.name}  ({gen.p_max:.0f} MW)" for gen in gen_sorted],
    fontsize=7.5,
)
ax.set_xlabel("Hour", fontsize=10)
ax.set_title(
    f"Stage 1 Commitment Schedule — Stochastic UC (40% VRE, K=30 scenarios)\n"
    f"Committed: {int(comm_s.sum())} / {G * T} generator-hours  "
    f"({comm_s.sum() / (G * T) * 100:.1f}%)",
    fontsize=12, fontweight="bold",
)

# Unit-type legend
patches = [
    mpatches.Patch(color=c, label=t)
    for t, c in TYPE_COLORS.items()
    if any(unit_type(g.name) == t for g in RTS96_GENERATORS)
]
ax.legend(handles=patches, loc="upper right", fontsize=8.5, ncol=3,
          title="Unit type", title_fontsize=9,
          framealpha=0.92, edgecolor="#ccc")

# Light grid
for t in range(T):
    ax.axvline(t - 0.5, color="white", linewidth=0.4)
for gi in range(G):
    ax.axhline(gi - 0.5, color="white", linewidth=0.4)

fig.tight_layout()
out4 = OUT / "chart4_commitment_heatmap.png"
fig.savefig(out4, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"  Saved -> {out4.name}")


print(f"\nAll 4 charts saved to {OUT}")

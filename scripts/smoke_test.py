"""Quick smoke test — verifies imports and prints system summary.

Run from the project root:
    python scripts/smoke_test.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rts96_reliability_uc import (  # noqa: E402
    ANNUAL_PEAK_MW,
    LOLP_EPS,
    RTS96_GENERATORS,
    VRE_PENETRATION,
)
from rts96_reliability_uc.scenarios import generate_vre_scenarios, estimate_net_load_transition
from rts96_reliability_uc.baselines import deterministic_uc_baseline
from rts96_reliability_uc.mdp import MDPDispatch
from rts96_reliability_uc.evaluation import monte_carlo_reliability


def main() -> None:
    total_cap = sum(g.p_max for g in RTS96_GENERATORS)
    print("RTS-96 reliability UC — smoke test")
    print(f"  Generators:  {len(RTS96_GENERATORS)}")
    print(f"  Capacity:    {total_cap:.0f} MW")
    print(f"  Peak demand: {ANNUAL_PEAK_MW:.0f} MW")
    print(f"  VRE:         {VRE_PENETRATION:.0%}")
    print(f"  LOLP eps:    {LOLP_EPS:.3f}")

    print("  Generating scenarios...", end=" ", flush=True)
    scen, _ = generate_vre_scenarios(0.40, n_scenarios=5, seed=42)
    print("OK")

    print("  Markov chain...", end=" ", flush=True)
    P, _, centers = estimate_net_load_transition(scen)
    print("OK")

    print("  Deterministic UC baseline...", end=" ", flush=True)
    comm, _ = deterministic_uc_baseline(RTS96_GENERATORS, scen)
    print("OK")

    print("  MDP value iteration...", end=" ", flush=True)
    mdp = MDPDispatch(RTS96_GENERATORS, comm, P, centers)
    mdp.solve(verbose=False)
    print("OK")

    print("  Monte Carlo (n=100)...", end=" ", flush=True)
    result = monte_carlo_reliability(mdp, RTS96_GENERATORS, comm, scen, n_samples=100, seed=0)
    lo, hi = result["LOLP_CI95"]
    print(f"OK  LOLP={result['LOLP']:.4f} 95%CI=[{lo:.4f},{hi:.4f}]")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()

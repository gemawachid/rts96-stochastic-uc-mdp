"""Command-line runner for the RTS-96 UC + MDP case study."""

from collections import Counter
from pathlib import Path

from .baselines import deterministic_uc_baseline, simple_merit_dispatch_baseline
from .config import LOLP_EPS, N_MC, N_SCENARIOS, VRE_PENETRATION
from .data import ANNUAL_PEAK_MW, RTS96_GENERATORS, T
from .evaluation import monte_carlo_reliability
from .experiments import penetration_sweep
from .mdp import MDPDispatch
from .network import build_pandapower_network, run_power_flow_validation
from .scenarios import estimate_net_load_transition, generate_vre_scenarios
from .unit_commitment import solve_stochastic_uc_highs

def main():
    sep = "="*72
    G = len(RTS96_GENERATORS)
    total_cap = sum(g.p_max for g in RTS96_GENERATORS)

    print(sep)
    print("  Reliability-Constrained Stochastic UC with MDP Dispatch")
    print(f"  IEEE RTS-96 (24-bus) | {G} generators | {total_cap:.0f} MW installed")
    print(f"  Annual peak = {ANNUAL_PEAK_MW:.0f} MW | VRE = {VRE_PENETRATION*100:.0f}%")
    print(f"  Solver: HiGHS (highspy) | LOLP target epsilon = {LOLP_EPS}")
    print(sep)

    # Data summary
    print(f"\n  Generator fleet summary:")
    from collections import Counter
    type_count = Counter(g.name.split('-')[0] for g in RTS96_GENERATORS)
    for utype,cnt in sorted(type_count.items()):
        pmax = next(g.p_max for g in RTS96_GENERATORS if g.name.startswith(utype))
        print(f"    {utype}: {cnt} x {pmax:.0f} MW = {cnt*pmax:.0f} MW")
    print(f"    Total: {total_cap:.0f} MW | Reserve vs peak: {(total_cap-ANNUAL_PEAK_MW)/ANNUAL_PEAK_MW*100:.1f}%")

    print("\n[1/7] Generating VRE scenarios...")
    scen, probs = generate_vre_scenarios(VRE_PENETRATION, N_SCENARIOS)
    print(f"      K={N_SCENARIOS} | Mean VRE={scen.mean():.0f} MW | Std={scen.std():.0f} MW")

    print("\n[2/7] Net-load Markov chain...")
    Pt,_,bc = estimate_net_load_transition(scen)
    print(f"      |S| = {len(bc)} x {MDPDispatch.N_E} x {T} = {len(bc)*MDPDispatch.N_E*T}")

    print("\n[3/7] Stage 1: Stochastic UC MIP (HiGHS)...")
    comm, uc_info = solve_stochastic_uc_highs(RTS96_GENERATORS,scen,probs,LOLP_EPS,900.0)
    print(f"      Status:          {uc_info['solver_status']}")
    print(f"      Objective:       USD {uc_info['objective_usd']:,.0f}")
    print(f"      MIP LOLP:        {uc_info['lolp_mip']:.5f}")
    print(f"      LOLP satisfied:  {uc_info['lolp_satisfied']}")
    print(f"      Committed g-hrs: {uc_info['committed_hours']} / {G*T} max")
    print(f"      Variables:       {uc_info['n_vars']:,}")
    print(f"      Constraints:     {uc_info['n_constraints']:,}")

    print("\n[4/7] Stage 2: MDP value iteration...")
    mdp_prop = MDPDispatch(RTS96_GENERATORS, comm, Pt, bc)
    mdp_prop.solve()

    print(f"\n[5/7] Monte Carlo reliability ({N_MC} samples)...")
    rel_prop   = monte_carlo_reliability(mdp_prop,RTS96_GENERATORS,comm,scen)
    det_c,_    = deterministic_uc_baseline(RTS96_GENERATORS,scen)
    mdp_det    = MDPDispatch(RTS96_GENERATORS,det_c,Pt,bc); mdp_det.solve(verbose=False)
    rel_det    = monte_carlo_reliability(mdp_det,RTS96_GENERATORS,det_c,scen,seed=1)
    rel_simple = simple_merit_dispatch_baseline(RTS96_GENERATORS,comm,scen,seed=2)

    print("\n[6/7] pandapower power flow (hour 17, winter weekday)...")
    net = build_pandapower_network()
    pf  = run_power_flow_validation(net, hour=17)
    print(f"      Converged: {pf.get('converged')}  "
          f"Max line loading: {pf.get('max_line_load_%',0):.1f}%")

    print(f"\n{sep}\n  RESULTS\n{sep}")
    hdr = f"  {'Method':<45} {'LOLP':>7} {'EENS(MWh)':>11} {'EUE(pu)':>10} {'OK':>3}"
    print(hdr); print(f"  {'-'*45} {'-'*7} {'-'*11} {'-'*10} {'-'*3}")
    for lbl,rel in [("Proposed - Stoch.UC MIP + MDP",     rel_prop),
                    ("Baseline A - Det.UC + MDP",          rel_det),
                    ("Baseline B - Stoch.UC + Merit disp.",rel_simple)]:
        sat = "Y" if rel["lolp_satisfied"] else "N"
        print(f"  {lbl:<45} {rel['LOLP']:>7.4f} "
              f"{rel['EENS_MWh']:>11.2f} {rel['EUE_pu']:>10.6f} {sat:>3}")
    print(f"\n  epsilon = {LOLP_EPS} | Annual peak = {ANNUAL_PEAK_MW:.0f} MW | "
          f"Fleet = {total_cap:.0f} MW")

    print("\n[7/7] Penetration sweep 20%-60%...")
    df = penetration_sweep(RTS96_GENERATORS,[0.20,0.30,0.40,0.50,0.60],n_mc=300,tl=300.0)
    print(df.to_string(index=False,float_format="{:.4f}".format))
    output_dir = Path(__file__).resolve().parents[2] / "outputs"
    output_dir.mkdir(exist_ok=True)
    df.to_csv(output_dir / "sweep_v2.csv",index=False)
    print(f"\n{sep}\n  Done.\n{sep}")


if __name__ == "__main__":
    main()

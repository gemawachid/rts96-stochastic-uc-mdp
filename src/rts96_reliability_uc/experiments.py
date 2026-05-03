"""Experiment orchestration helpers."""

import pandas as pd

from .config import N_SCENARIOS
from .baselines import deterministic_uc_baseline
from .evaluation import monte_carlo_reliability
from .mdp import MDPDispatch
from .scenarios import estimate_net_load_transition, generate_vre_scenarios
from .unit_commitment import solve_stochastic_uc_highs

def penetration_sweep(generators, levels, n_scenarios=N_SCENARIOS,
                       n_mc=500, tl=90.0):
    records=[]
    for pct in levels:
        print(f"\n  -- VRE = {pct*100:.0f}% --")
        scen,probs = generate_vre_scenarios(pct, n_scenarios)
        Pt,_,bc    = estimate_net_load_transition(scen)
        uc_comm,uc_info = solve_stochastic_uc_highs(generators,scen,probs,time_limit_s=tl)
        mdp_p = MDPDispatch(generators,uc_comm,Pt,bc); mdp_p.solve(verbose=False)
        rp = monte_carlo_reliability(mdp_p,generators,uc_comm,scen,n_mc)
        det_c,_ = deterministic_uc_baseline(generators,scen)
        mdp_d = MDPDispatch(generators,det_c,Pt,bc); mdp_d.solve(verbose=False)
        rd = monte_carlo_reliability(mdp_d,generators,det_c,scen,n_mc)
        records.append({"VRE_%":pct*100,
                        "LOLP_proposed":rp["LOLP"],"EENS_proposed_MWh":rp["EENS_MWh"],
                        "LOLP_det":rd["LOLP"],      "EENS_det_MWh":rd["EENS_MWh"],
                        "UC_obj_USD":uc_info.get("objective_usd",0),
                        "UC_lolp_mip":uc_info.get("lolp_mip",float("nan"))})
        print(f"    Proposed LOLP={rp['LOLP']:.4f}  Det LOLP={rd['LOLP']:.4f}")
    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════════════════
#  9. MAIN

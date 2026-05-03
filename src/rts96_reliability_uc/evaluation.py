"""Reliability evaluation routines."""

import numpy as np

from .config import ETA_C, ETA_D, LOLP_EPS, N_MC, STORAGE_CAP_MWH
from .data import DEMAND, T

def monte_carlo_reliability(mdp, generators, commitment, vre_scenarios,
                             n_samples=N_MC, seed=0):
    rng = np.random.default_rng(seed)
    G   = len(generators); K = len(vre_scenarios)
    for_rates = np.array([g.for_rate for g in generators])
    lol_events = 0; total_unsrv = 0.0; periods_lol = 0
    eens_sq = 0.0  # sum of squares for EENS variance

    for _ in range(n_samples):
        vre   = vre_scenarios[rng.integers(0,K)]
        avail = rng.random(G) >= for_rates
        soc   = 0.5; day_lol = False; day_unsrv = 0.0

        for t in range(T):
            nl = DEMAND[t]-vre[t]
            b,unserved,_ = mdp.dispatch(t,nl,soc,avail=avail)
            e_idx = int(np.clip(np.argmin(np.abs(mdp.soc_bins-soc)), 0, mdp.N_E-1))
            b = mdp._clip_b(e_idx,b)
            soc += b*ETA_C/STORAGE_CAP_MWH if b>=0 else b/(ETA_D*STORAGE_CAP_MWH)
            soc = float(np.clip(soc,0.0,1.0))
            if unserved > 0.01:
                day_lol = True; day_unsrv += unserved; periods_lol += 1

        if day_lol: lol_events += 1
        total_unsrv += day_unsrv
        eens_sq    += day_unsrv ** 2

    lolp       = periods_lol / (n_samples * T)
    daily_lolp = lol_events  / n_samples
    eens       = total_unsrv / n_samples

    # 95 % confidence intervals (normal approximation)
    z = 1.96
    lolp_se  = np.sqrt(lolp * (1 - lolp) / (n_samples * T))
    eens_var = (eens_sq / n_samples) - eens ** 2   # E[X²] - E[X]²
    eens_se  = np.sqrt(max(eens_var, 0.0) / n_samples)

    return {
        "LOLP":              lolp,
        "LOLP_CI95":         (round(lolp - z*lolp_se, 6), round(lolp + z*lolp_se, 6)),
        "EENS_MWh":          eens,
        "EENS_CI95":         (round(eens - z*eens_se, 3), round(eens + z*eens_se, 3)),
        "EUE_pu":            eens / DEMAND.sum(),
        "daily_LOLP":        daily_lolp,
        "lol_events":        lol_events,
        "n_samples":         n_samples,
        "periods_with_LOL":  periods_lol,
        "lolp_satisfied":    lolp <= LOLP_EPS,
    }


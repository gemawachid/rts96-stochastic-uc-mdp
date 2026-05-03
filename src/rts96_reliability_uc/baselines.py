"""Baseline commitment and dispatch policies."""

import numpy as np

from .config import ETA_C, ETA_D, LOLP_EPS, N_MC, STORAGE_CAP_MWH, STORAGE_POW_MW
from .data import DEMAND, T

def deterministic_uc_baseline(generators, scenarios):
    G  = len(generators)
    worst = np.percentile(DEMAND[np.newaxis,:]-scenarios, 95, axis=0)*1.15
    merit = sorted(range(G), key=lambda g: generators[g].cost_b)
    comm  = np.zeros((G,T), dtype=int)
    for t in range(T):
        cap = 0.0
        for g in merit:
            if cap < worst[t]: comm[g,t]=1; cap+=generators[g].p_max
    # Heuristic min-up enforcement
    for g in range(G):
        gen = generators[g]
        for t in range(1,T):
            if comm[g,t-1]==1 and comm[g,t]==0:
                on_since = t-1
                while on_since>0 and comm[g,on_since-1]==1: on_since-=1
                if (t-on_since)<gen.min_up: comm[g,t]=1
    return comm, {"committed_hours":int(comm.sum())}


def simple_merit_dispatch_baseline(generators, commitment, vre_scenarios,
                                    n_samples=N_MC, seed=1):
    rng=np.random.default_rng(seed); G=len(generators); K=len(vre_scenarios)
    for_rates=np.array([g.for_rate for g in generators])
    merit=sorted(range(G),key=lambda g: generators[g].cost_b)
    lol_events=0; total_unsrv=0.0; periods_lol=0; eens_sq=0.0
    for _ in range(n_samples):
        vre=vre_scenarios[rng.integers(0,K)]; avail=rng.random(G)>=for_rates
        soc=0.5; day_lol=False; day_unsrv=0.0
        for t in range(T):
            nl=DEMAND[t]-vre[t]; rem=nl
            if rem>0:
                dis=min(rem,soc*STORAGE_CAP_MWH*ETA_D,STORAGE_POW_MW)
                rem-=dis; soc-=dis/(ETA_D*STORAGE_CAP_MWH)
            elif rem<0:
                chg=min(-rem,(1-soc)*STORAGE_CAP_MWH/ETA_C,STORAGE_POW_MW)
                rem+=chg; soc+=chg*ETA_C/STORAGE_CAP_MWH
            soc=float(np.clip(soc,0,1))
            for g in merit:
                if rem<=0: break
                if commitment[g,t]==1 and avail[g]:
                    p=min(rem,generators[g].p_max); rem-=p
            if rem>0.01:
                day_lol=True; day_unsrv+=rem; periods_lol+=1
        if day_lol: lol_events+=1
        total_unsrv+=day_unsrv; eens_sq+=day_unsrv**2
    lolp=periods_lol/(n_samples*T); daily_lolp=lol_events/n_samples; eens=total_unsrv/n_samples
    z=1.96
    lolp_se=np.sqrt(lolp*(1-lolp)/(n_samples*T))
    eens_var=(eens_sq/n_samples)-eens**2
    eens_se=np.sqrt(max(eens_var,0.0)/n_samples)
    return {"LOLP":lolp,
            "LOLP_CI95":(round(lolp-z*lolp_se,6), round(lolp+z*lolp_se,6)),
            "EENS_MWh":eens,
            "EENS_CI95":(round(eens-z*eens_se,3), round(eens+z*eens_se,3)),
            "EUE_pu":eens/DEMAND.sum(),
            "daily_LOLP":daily_lolp,
            "lol_events":lol_events,"n_samples":n_samples,
            "periods_with_LOL":periods_lol,
            "lolp_satisfied":lolp<=LOLP_EPS}

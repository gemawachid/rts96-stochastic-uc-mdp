"""Stage 1 stochastic unit commitment model solved with HiGHS."""

import numpy as np
import highspy

from .config import (
    ETA_C,
    ETA_D,
    LOLP_EPS,
    STORAGE_CAP_MWH,
    STORAGE_DEG_COST,
    STORAGE_POW_MW,
    VOLL,
)
from .data import DEMAND, T

def solve_stochastic_uc_highs(generators, scenarios, probs,
                               lolp_epsilon=LOLP_EPS, time_limit_s=180.0,
                               outage_reserve_multiplier=1.33):
    G = len(generators); K = len(scenarios)

    # ── Variable offsets ──────────────────────────────────────────────────────
    o_u = 0;            o_v = o_u+G*T;   o_w = o_v+G*T
    o_p = o_w+G*T                        # dispatch p[g,t,k]
    o_s = o_p+K*G*T;   o_d = o_s+K*T    # storage charge/discharge
    o_e = o_d+K*T;     o_x = o_e+K*T    # SoC, unserved
    o_c = o_x+K*T;     o_z = o_c+K*T    # VRE curtailment, LOL indicator
    n_vars = o_z+K*T

    iu  = lambda g,t:   o_u+g*T+t
    iv  = lambda g,t:   o_v+g*T+t
    iw  = lambda g,t:   o_w+g*T+t
    ip  = lambda g,t,k: o_p+k*G*T+g*T+t
    is_ = lambda t,k:   o_s+k*T+t
    id_ = lambda t,k:   o_d+k*T+t
    ie  = lambda t,k:   o_e+k*T+t
    ix  = lambda t,k:   o_x+k*T+t
    ic  = lambda t,k:   o_c+k*T+t
    iz  = lambda t,k:   o_z+k*T+t

    # ── Bounds ────────────────────────────────────────────────────────────────
    lb = [0.0]*n_vars; ub = [1.0]*n_vars
    for k in range(K):
        for g in range(G):
            for t in range(T): ub[ip(g,t,k)] = generators[g].p_max
        for t in range(T):
            ub[is_(t,k)] = STORAGE_POW_MW; ub[id_(t,k)] = STORAGE_POW_MW
            ub[ie(t,k)]  = 1.0
            ub[ix(t,k)]  = float(DEMAND.max())
            ub[ic(t,k)]  = float(sum(g.p_max for g in generators))  # must cover worst-case excess gen
            ub[iz(t,k)]  = 1.0

    # ── Objective ─────────────────────────────────────────────────────────────
    obj = [0.0]*n_vars
    for g in range(G):
        gen = generators[g]
        for t in range(T):
            obj[iu(g,t)] = gen.cost_a
            obj[iv(g,t)] = gen.su_cost
            obj[iw(g,t)] = gen.sd_cost
    # Stage 2 dispatch cost uses only the linear term c_b (MILP requires linear
    # objectives). The quadratic term c_c is included in the MDP economic dispatch
    # (mdp.py:_eco_dispatch) for accurate cost evaluation at execution time.
    for k in range(K):
        pi = probs[k]
        for g in range(G):
            for t in range(T): obj[ip(g,t,k)] = pi*generators[g].cost_b
        for t in range(T):
            obj[ix(t,k)]  = pi*VOLL
            obj[ic(t,k)]  = pi*5.0          # small curtailment cost
            obj[is_(t,k)] = pi*STORAGE_DEG_COST
            obj[id_(t,k)] = pi*STORAGE_DEG_COST

    # ── Constraints ───────────────────────────────────────────────────────────
    INF = 1e30
    A_lo=[]; A_hi=[]; A_st=[0]; A_ix=[]; A_vl=[]

    def add_row(c, lo, hi):
        for vi,cv in c.items(): A_ix.append(vi); A_vl.append(cv)
        A_st.append(len(A_ix)); A_lo.append(lo); A_hi.append(hi)

    for k in range(K):
        vre = scenarios[k]
        for t in range(T):
            # (5) Power balance with curtailment: Σp + d - s + x - c = demand - VRE
            c = {id_(t,k):1.0, is_(t,k):-1.0, ix(t,k):1.0, ic(t,k):-1.0}
            for g in range(G): c[ip(g,t,k)] = 1.0
            rhs = DEMAND[t] - vre[t]
            add_row(c, rhs, rhs)

            # (6) Output bounds  p ≤ Pmax·u  and  p ≥ Pmin·u
            for g in range(G):
                gen = generators[g]
                add_row({ip(g,t,k):1.0,  iu(g,t):-gen.p_max}, -INF, 0.0)
                add_row({ip(g,t,k):-1.0, iu(g,t): gen.p_min}, -INF, 0.0)

            # (7-8) Ramp constraints
            if t > 0:
                for g in range(G):
                    gen = generators[g]
                    add_row({ip(g,t,k):1.0, ip(g,t-1,k):-1.0,
                             iu(g,t-1):-gen.ramp_up, iv(g,t):-gen.p_max}, -INF, 0.0)
                    add_row({ip(g,t-1,k):1.0, ip(g,t,k):-1.0,
                             iu(g,t):-gen.ramp_dn, iw(g,t):-gen.p_max}, -INF, 0.0)

            # (13) Storage dynamics  e_{t+1} = e_t + ηc·s/E - d/(ηd·E)
            if t < T-1:
                add_row({ie(t+1,k):1.0, ie(t,k):-1.0,
                         is_(t,k):-ETA_C/STORAGE_CAP_MWH,
                         id_(t,k): 1.0/(ETA_D*STORAGE_CAP_MWH)}, 0.0, 0.0)

            # (16) Big-M: x ≤ M·z
            add_row({ix(t,k):1.0, iz(t,k):-DEMAND.max()}, -INF, 0.0)

            # Outage-aware adequacy reserve. The LOLP rows above control
            # scenario load shedding, while Monte Carlo evaluation also samples
            # generator forced outages. This keeps the MIP commitment aligned
            # with that reliability simulation.
            if outage_reserve_multiplier is not None:
                reserve_target = max(0.0, outage_reserve_multiplier*rhs - STORAGE_POW_MW)
                add_row({iu(g,t): generators[g].p_max for g in range(G)},
                        reserve_target, INF)

    # (9-10) Min up/down time
    for g in range(G):
        gen = generators[g]
        for t in range(T):
            for tau in range(t, min(t+gen.min_up, T)):
                add_row({iu(g,tau):1.0, iv(g,t):-1.0}, 0.0, INF)
            for tau in range(t, min(t+gen.min_dn, T)):
                add_row({iu(g,tau):1.0, iw(g,t):1.0}, -INF, 1.0)

    # (11-12) Start-up / shut-down logic
    for g in range(G):
        for t in range(T):
            if t == 0:
                add_row({iv(g,t):1.0, iw(g,t):-1.0, iu(g,t):-1.0}, 0.0, 0.0)
            else:
                add_row({iv(g,t):1.0, iw(g,t):-1.0, iu(g,t):-1.0, iu(g,t-1):1.0}, 0.0, 0.0)
            add_row({iv(g,t):1.0, iw(g,t):1.0}, -INF, 1.0)

    # (17) LOLP constraint
    c_lolp = {iz(t,k): probs[k]/T for k in range(K) for t in range(T)}
    add_row(c_lolp, -INF, lolp_epsilon)

    # Initial SoC = 0.5
    for k in range(K): add_row({ie(0,k):1.0}, 0.5, 0.5)

    # ── Solve ─────────────────────────────────────────────────────────────────
    h = highspy.Highs(); h.silent()
    h.setOptionValue("time_limit",  time_limit_s)
    h.setOptionValue("mip_rel_gap", 0.01)
    h.setOptionValue("presolve",    "on")
    h.setOptionValue("parallel",    "on")
    h.addVars(n_vars, lb, ub)
    for i in range(n_vars): h.changeColCost(i, obj[i])

    int_vars = (
        [iu(g,t) for g in range(G) for t in range(T)] +
        [iv(g,t) for g in range(G) for t in range(T)] +
        [iw(g,t) for g in range(G) for t in range(T)] +
        [iz(t,k) for k in range(K) for t in range(T)]
    )
    for i in int_vars: h.changeColIntegrality(i, highspy.HighsVarType.kInteger)

    n_rows = len(A_lo)
    for i in range(n_rows):
        s2,e2 = A_st[i], A_st[i+1]
        h.addRow(A_lo[i], A_hi[i], e2-s2, A_ix[s2:e2], A_vl[s2:e2])

    h.run()
    solver_status = str(h.getModelStatus())
    if any(flag in solver_status for flag in ("Infeasible", "Unbounded", "Notset")):
        raise RuntimeError(f"UC optimization failed: {solver_status}")

    obj_val  = h.getInfoValue("objective_function_value")[1]
    col_vals = list(h.getSolution().col_value)

    commitment = np.array(
        [[int(round(col_vals[iu(g,t)])) for t in range(T)] for g in range(G)]
    )
    if commitment.sum() == 0:
        raise RuntimeError(f"UC optimization produced no incumbent solution: {solver_status}")

    lolp_mip = sum(probs[k]/T * col_vals[iz(t,k)]
                   for k in range(K) for t in range(T))

    return commitment, {
        "objective_usd":   obj_val,
        "lolp_mip":        lolp_mip,
        "lolp_satisfied":  lolp_mip <= lolp_epsilon,
        "committed_hours": int(commitment.sum()),
        "n_vars":          n_vars,
        "n_constraints":   n_rows,
        "outage_reserve_multiplier": outage_reserve_multiplier,
        "solver_status":   solver_status,
    }


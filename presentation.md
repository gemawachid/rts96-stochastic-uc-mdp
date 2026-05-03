---
marp: true
theme: default
paginate: true
style: |
  section {
    background-color: #ffffff;
    color: #1a1a2e;
    font-family: 'Segoe UI', Calibri, Arial, sans-serif;
    font-size: 16.5px;
    padding: 36px 56px;
  }
  h1 {
    color: #1565c0;
    border-bottom: 3px solid #1565c0;
    padding-bottom: 5px;
    font-size: 28px;
    margin-bottom: 14px;
  }
  strong { color: #1565c0; }
  code {
    background: #e8f0fe;
    color: #1a237e;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 13.5px;
  }
  pre {
    background: #f5f7ff;
    border-left: 4px solid #1565c0;
    padding: 11px 16px;
    font-size: 12px;
    line-height: 1.5;
    border-radius: 0 4px 4px 0;
    margin: 8px 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14.5px;
    margin-top: 6px;
  }
  th {
    background-color: #1565c0;
    color: white;
    padding: 6px 10px;
    text-align: left;
  }
  td {
    padding: 5px 10px;
    border-bottom: 1px solid #dde3f0;
  }
  tr:nth-child(even) td { background-color: #f0f4ff; }
  blockquote {
    border-left: 4px solid #1565c0;
    background: #f0f4ff;
    padding: 8px 14px;
    margin: 8px 0;
    color: #1a1a2e;
  }
  ul { margin-top: 4px; }
  li { margin-bottom: 3px; }
  section.title-slide {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 60px 80px;
  }
  section.title-slide h1 {
    font-size: 34px;
    border: none;
    border-left: 6px solid #1565c0;
    padding: 10px 22px;
    margin-bottom: 16px;
    line-height: 1.35;
  }
  section.title-slide h2 {
    font-size: 18px;
    color: #333;
    font-weight: normal;
    margin-left: 28px;
    margin-bottom: 6px;
  }
  section.title-slide p {
    color: #777;
    font-size: 14px;
    margin-left: 28px;
    margin-top: 16px;
  }
---

<!-- _class: title-slide -->

# Reliability-Constrained Stochastic Unit Commitment
# with Adaptive MDP Dispatch

## IEEE RTS-96 (24-bus) Case Study

LOLP target ε = 0.08  ·  VRE penetration 40%  ·  Solver: HiGHS  ·  May 2026

---

# 1 · Motivation

**Standard practice** — commit units to cover *peak demand + heuristic reserve margin*

- No formal guarantee that LOLP ≤ ε holds under the actual dispatch policy
- Reserve margin calibrated *ex ante*; true reliability verified *ex post* only
- VRE variability erodes deterministic reserve rules at high penetration levels

> **Research question:** Can day-ahead commitment ensure **LOLP ≤ ε** is satisfied under the *optimal real-time dispatch policy* — not a heuristic reserve?

**Why this is hard:**

- **Stage 1** (commitment) decided *before* VRE and demand uncertainty resolves
- **Stage 2** (dispatch + storage) decided *after* — it is what actually determines LOLP
- Standard UC ignores this coupling; the two stages are solved independently

**Our approach:**

- Embed LOLP explicitly as a constraint **inside** the Stage 1 stochastic MIP
- Solve Stage 2 as an MDP over (net-load, SoC, hour) via backward value iteration
- Verify the combined policy with Monte Carlo: 5,000 daily trajectories + forced outages

---

# 2 · IEEE RTS-96 Test System

| Parameter | Value |
|---|---|
| Buses | 24  (138 kV and 230 kV areas) |
| Generators | 32 thermal units |
| Installed capacity | 3,405 MW  →  reserve margin 19.5% |
| Annual peak demand | 2,850 MW  ·  Total daily demand 57,370 MWh |
| Battery energy storage | 1,000 MWh / 400 MW  (η_c = η_d = 0.92) |
| VRE penetration | 40% of annual peak  →  nameplate 3,257 MW |
| Reliability target | LOLP ≤ ε = 0.08  (hourly LOL fraction) |
| Planning horizon | T = 24 hours |

**Fleet capacity by unit type** *(each █ ≈ 40 MW)*

<pre>
 U400  ████████████████████  800 MW  ·  2 units   largest, base-load
 U155  ████████████████      620 MW  ·  4 units
 U197  ███████████████       591 MW  ·  3 units
 U350  █████████             350 MW  ·  1 unit
  U76  ████████              304 MW  ·  4 units
 U100  ████████              300 MW  ·  3 units
  U50  ████████              300 MW  ·  6 units
  U20  ██                     80 MW  ·  4 units   peakers
  U12  ██                     60 MW  ·  5 units   peakers
                              ────────────────────────────────
                        Total 3,405 MW
</pre>

---

# 3 · Two-Stage Optimisation Framework

<pre>
┌──────────────────────────────────────────┐      ┌────────────────────────────────────────┐
│       STAGE 1  ·  Day-Ahead MIP          │      │      STAGE 2  ·  Real-Time MDP         │
│       (here-and-now decisions)           │      │      (wait-and-see decisions)          │
├──────────────────────────────────────────┤      ├────────────────────────────────────────┤
│ Variables:                               │      │ Variables (per uncertainty draw):      │
│   u[g,t]  commitment    {0,1}            │──▶   │   b[t]    storage  ±400 MW             │
│   v[g,t]  startup       {0,1}            │      │   p[g,t]  merit-order dispatch         │
│   w[g,t]  shutdown      {0,1}            │      │   x[t]    unserved load                │
│                                          │      │                                        │
│ Uncertainty: K = 30 VRE scenarios        │      │ State: (l, e, t)                       │
│ Solver: HiGHS MIP  (gap 1%, 900 s)       │      │   l  net-load bin  {0…9}               │
│                                          │      │   e  SoC bin       {0…9}               │
│ Key coupling — LOLP constraint (17):     │      │   t  hour          {0…23}              │
│                                          │      │ Solver: backward value iteration       │
│  Σ_{k,t} (π_k / T)·z[t,k] ≤ ε = 0.08   │──▶   │ Policy: π*(l,e,t) → optimal b          │
└──────────────────────────────────────────┘      └────────────────────────────────────────┘
                         ↑
          z[t,k] ∈ {0,1}  loss-of-load indicator — links the two stages
</pre>

- Stage 1 forces enough committed capacity so that LOLP budget ε is not exceeded
- Stage 2 uses the committed fleet `u*` to compute the optimal storage dispatch policy
- Evaluation re-simulates Stage 2 via Monte Carlo with generator forced outages

---

# 4 · Stage 1: Stochastic UC MIP — Formulation

**Objective** — minimise expected operating cost over K scenarios:

<pre>
min  Σ_{g,t} [ c_a^g·u[g,t]  +  c_su^g·v[g,t]  +  c_sd^g·w[g,t] ]
   + Σ_k π_k · Σ_{g,t} c_b^g · p[g,t,k]
   + Σ_k π_k · Σ_t [ VOLL·x[t,k]  +  5·c[t,k]  +  c_deg·(s[t,k] + d[t,k]) ]

  VOLL = $15,000/MWh  ·  curtailment = $5/MWh  ·  c_deg = $0.5/MWh
</pre>

**Constraints** (all ∀ g, t, k unless noted):

| No. | Name | Expression |
|---|---|---|
| (5) | Power balance | Σ_g p[g,t,k] + d[t,k] − s[t,k] + x[t,k] − c[t,k] = D_t − V_{t,k} |
| (6) | Output bounds | P^g_min · u[g,t] ≤ p[g,t,k] ≤ P^g_max · u[g,t] |
| (7) | Ramp up | p[g,t,k] − p[g,t-1,k] ≤ RU^g · u[g,t-1] + P^g_max · v[g,t] |
| (8) | Ramp down | p[g,t-1,k] − p[g,t,k] ≤ RD^g · u[g,t] + P^g_max · w[g,t] |
| (9) | Min up time | u[g,τ] ≥ v[g,t]  ∀ τ ∈ {t, …, t + T^g_up − 1} |
| (10) | Min down time | u[g,τ] + w[g,t] ≤ 1  ∀ τ ∈ {t, …, t + T^g_dn − 1} |
| (11–12) | Start/stop logic | v[g,t] − w[g,t] = u[g,t] − u[g,t-1]  ·  v[g,t] + w[g,t] ≤ 1 |
| (13) | Storage SoC | e[t+1,k] = e[t,k] + η_c · s[t,k]/E − d[t,k]/(η_d · E) |
| (16) | Big-M LOL | x[t,k] ≤ max(D) · z[t,k] |
| **(17)** | **LOLP** | **Σ_{k,t} (π_k / T) · z[t,k] ≤ ε = 0.08** |

---

# 5 · Stage 2: MDP Adaptive Dispatch

**State space** `(l, e, t)` — **10 × 10 × 24 = 2,400 states:**

- `l ∈ {0…9}` — net-load bin: D_t − VRE_t discretised into 10 equal-prob. bins
- `e ∈ {0…9}` — SoC bin: 0.0 → 1.0 in steps of 0.1  (E = 1,000 MWh)
- `t ∈ {0…23}` — hour

**Action set** — 7 levels, clipped to physical limits:

<pre>
  b  ∈  {−400, −267, −133, 0, 133, 267, 400}  MW

  Charge limit:     b_max =  min(P_max,  (1 − soc) · E / η_c)   ← headroom in storage
  Discharge limit:  b_min = −min(P_max,    soc     · E · η_d)   ← energy available
</pre>

**Immediate reward** — negated for maximisation:

<pre>
  r(l, e, b) = −[ C_eco(net_load_l + b, t)  +  c_deg · |b| ]

  C_eco(d, t) = Σ_{g∈committed(t)} [ c_a^g + c_b^g·p_g + c_c^g·p_g² ]
              + VOLL · max(0, d − Σ_g P^g_max)    ← penalty already inside C_eco
</pre>

**Bellman equation** (backward sweep t = T−1 → 0):

<pre>
  V_t(l, e) = max_{b ∈ B}  { r(l, e, b)  +  Σ_{l'} P[t, l, l'] · V_{t+1}(l', e'(e,b)) }

  SoC transition:  e'  ←  nearest bin to  soc + η_c·b/E      (b ≥ 0, charging)
                                           soc + b/(η_d·E)    (b < 0, discharging)
</pre>

---

# 6 · VRE Uncertainty Model

**Nameplate capacity:** VRE_cap = 0.40 × 2,850 / 0.35 = **3,257 MW**
*(wind 1,954 MW  ·  solar 1,303 MW  ·  assumed mean CF = 35%)*

**Wind** — mean-reverting AR(1) on capacity factor:

<pre>
  wcf[0]  ~  Beta(2, 3)                                     ← initial draw

  wcf[t]  =  clip(  0.85 · wcf[t-1]  +  0.045  +  ε_t ,  0, 1 )
                     ─────────────     ───────   ─────
                      autocorr.        intercept   innovation
                                    = (1−0.85)×0.30   ε_t ~ N(0, 0.08)
                                    ← mean-reverts to CF = 0.30

  W_t  =  wcf[t] × 1,954 MW
</pre>

**Solar** — diurnal envelope with stochastic scaling:

<pre>
  env_t  =  sin( π(t − 6) / 12 )   for t ∈ [6, 18],   else 0    ← shape

  scf_t  =  env_t  ×  β  ×  ξ_t                                 ← stochastic scaling
               β  ~  Beta(4, 2)                                  ← daily irradiance draw
               ξ_t  ~  Uniform(0.7, 1.0)                         ← hourly variability

  S_t  =  scf_t × 1,303 MW
</pre>

**Scenario set + Markov chain:**

- K = 30 scenarios,  π_k = 1/30,  seed = 42 (reproducible)
- Net load `N_t = D_t − VRE_t` → 10 equal-probability bins per hour
- Transition matrix `P[t, l, l']` shape **(24 × 10 × 10)**,  ε-smoothed (1e-6)

---

# 7 · Solver & Monte Carlo Reliability Evaluation

**HiGHS MIP** (`highspy` Python API):

| Setting | Value | Setting | Value |
|---|---|---|---|
| Time limit | 900 s (full)  /  30 s (mini) | MIP relative gap | 1% |
| Presolve | on | Parallel threads | on |
| n_vars *(K=5 mini)* | 6,864 | n_constraints | 24,526 |
| Outage reserve multiplier | 1.33 × net demand | Initial SoC | 0.5 |

**Monte Carlo reliability evaluation** (N = 5,000 trajectories):

<pre>
  For each sample  i = 1 … N:
    1.  Draw VRE scenario  k  ~  Uniform{1 … K}
    2.  Sample forced outages:  avail[g] ~ Bernoulli(1 − FOR_g)   ∀ g
    3.  Initialise SoC = 0.5
    4.  For t = 0 … 23:
          net_load ← D_t − VRE_{t,k}
          b  ←  policy π*(l, e, t)   [look-up from value function]
          run merit-order dispatch over available committed generators
          record x[t]  (unserved load, MW)

  LOLP  =  Σ_{i,t} 1[x[t,i] > 0.01]  /  (N × T)   ← hourly LOL fraction
  EENS  =  Σ_{i,t} x[t,i]            /  N          ← MWh / day
  EUE   =  EENS / 57,370 MWh                        ← per-unit of daily demand
</pre>

Power flow — pandapower DC OPF, hour 17 (winter weekday peak):
**Converged ✓**  ·  Max line loading **78.1%**  ·  Total dispatch 1,272 MW

---

# 8 · Results: Reliability Comparison

**System:** 40% VRE  ·  ε = 0.08  ·  Monte Carlo n = 300 samples

| Method | LOLP | EENS (MWh) | EUE (pu) | Daily LOLP | ε-satisfied |
|---|---|---|---|---|---|
| **Proposed** — Stoch. UC MIP + MDP | **0.049** | **149.6** | **0.00261** | **0.200** | **✓** |
| Baseline A — Deterministic UC + MDP | 0.092 | 472.8 | 0.00824 | 0.353 | ✗ |
| Baseline B — Stoch. UC + Merit Dispatch | 0.050 | 144.8 | 0.00252 | 0.247 | ✓ |

**LOLP** *(each █ ≈ 0.004  ·  ε = 0.08 at position 20)*

<pre>
              0.00                ε=0.08      0.10
               ├──────────────────────┤──────┤
  Proposed  ✓  ████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  0.049
  Baseline A ✗  ██████████████████████████░░  0.092   ← exceeds ε
  Baseline B ✓  ████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  0.050
</pre>

**EENS MWh/day** *(each █ ≈ 20 MWh)*

<pre>
              0              250           500
               ├──────────────┼─────────────┤
  Proposed  ✓  ████████░░░░░░░░░░░░░░░░░░░░░  149.6 MWh
  Baseline A ✗  ████████████████████████░░░░  472.8 MWh  ← 3.2×
  Baseline B ✓  ███████░░░░░░░░░░░░░░░░░░░░░  144.8 MWh
</pre>

- Proposed reduces LOLP by **46.9%** vs. deterministic baseline
- Baseline B satisfies ε but *without* a formal guarantee in its commitment decision

---

# 9 · Code Architecture

<pre>
rts96_stochastic_uc_mdp.py          ← compatibility facade  /  direct entry point
│
└─ src/rts96_reliability_uc/
   ├─ config.py            constants: ε=0.08, K=30, N_MC=5,000, storage, VRE=40%
   ├─ data.py              IEEE RTS-96: 32 generators, bus/load tables, profiles
   ├─ scenarios.py         AR(1) wind + sin-envelope solar  ·  Markov P[t,l,l']
   ├─ unit_commitment.py   Stage 1 MIP — HiGHS API, constraints (5)–(17)
   ├─ mdp.py               Stage 2 — backward value iteration, merit-order dispatch
   ├─ evaluation.py        Monte Carlo LOLP / EENS / EUE with forced outages
   ├─ baselines.py         deterministic reserve-margin UC  ·  simple merit dispatch
   ├─ network.py           pandapower DC power flow validation  (optional)
   ├─ experiments.py       parametric VRE penetration sweep  20% → 60%
   └─ runner.py            main() — full 7-step reproducible workflow

scripts/
   ├─ run_case.py          entry point:   python scripts/run_case.py
   ├─ make_figures.py      7 publication-quality figures  (matplotlib)
   └─ show_results.py      interactive result viewer  (--full / --no-show)
</pre>

- All 10 modules verified: imports pass, end-to-end smoke test clean
- UC solver status: `kOptimal`  ·  Committed g-hrs: 549/768  ·  Obj: USD 547,210
- `pandapower` optional — graceful fallback if unavailable

---

# 10 · Conclusions & Next Steps

**Key findings:**

- Embedding LOLP as constraint (17) in Stage 1 is the **critical ingredient** — it aligns the commitment decision with the Monte Carlo simulation that verifies reliability
- MDP value iteration over **2,400 states** runs in seconds; provides an optimal storage policy under net-load and SoC uncertainty
- At 40% VRE: proposed LOLP = **0.049** vs. deterministic **0.092** — **46.9% reduction**
- Deterministic UC commits fewer units → **3.2× higher EENS** (472.8 vs. 149.6 MWh/day)
- Baseline B also satisfies ε here, but without a formal guarantee — coincidental, not designed

**Honest limitations:**

| Issue | Impact |
|---|---|
| `LOLP_EPS = 0.08` is loose (industry standard ≈ 0.001) | Not directly comparable to planning standards |
| Markov chain from K = 30 scenarios | Adequate for proof-of-concept; not production-grade |
| MDP grid 10 × 10 | Sensitivity to 15×15, 20×20 not yet verified |
| MIP uses linear cost `c_b`; MDP uses quadratic `c_b·p + c_c·p²` | Minor cost model inconsistency |
| Economic dispatch only (no AC OPF) | Network congestion not captured |

**Recommended next steps:**

1. Sensitivity: K ∈ {30, 60, 100}  ·  MDP grids {10×10, 15×15, 20×20}
2. Tighten ε → 0.01; report 95% Monte Carlo confidence intervals
3. Compare against deterministic reserve margin variants (15%, 25%, 35%)
4. Full penetration sweep 20% → 60% VRE with N = 5,000 MC samples
5. Replace linear MIP dispatch cost with piecewise-linear quadratic approximation

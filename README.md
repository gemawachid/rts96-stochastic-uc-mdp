# Reliability-Constrained Stochastic Unit Commitment with Adaptive MDP Dispatch

**IEEE RTS-96 (24-bus) Case Study**
| 32 generators | 3,405 MW installed | 2,850 MW annual peak | 40% VRE penetration

## Research Question

How can day-ahead commitment decisions be made so that a formal reliability guarantee —
`LOLP ≤ ε` — is maintained under the **optimal** real-time dispatch policy rather than
under a heuristic spinning-reserve margin?

## Method Overview

The framework decouples commitment and dispatch into two stages:

```
Stage 1 — Stochastic UC MIP (HiGHS)
  Minimise  Σ_{g,t} [c_su·y_{g,t} + c_b·p_{g,t}·u_{g,t}]
  Subject to:
    - Power balance (per scenario)
    - Generator limits, min-up/down times, ramp rates
    - LOLP constraint:  Σ_{k,t} (π_k / T) · z_{t,k} ≤ ε      [eq. 17]

Stage 2 — MDP Backward Value Iteration
  State space: net-load bin × SoC bin × hour  →  10 × 10 × 24 = 2,400 states
  Action: storage charge/discharge b ∈ [−P_MW, +P_MW]
  Reward: −VOLL · unserved_energy (penalises loss-of-load)
  Policy: π*(s) = argmin_b  c(s,b) + V_{t+1}(s')
```

## Key Results (40% VRE, ε = 0.08, N = 5,000 MC samples)

| Method | LOLP | EENS (MWh/day) | EUE (pu) | ε satisfied |
|--------|------|----------------|----------|-------------|
| **Proposed** — Stoch.UC + MDP | 0.0174 | 54.82 | 0.000955 | Yes |
| Baseline A — Det.UC + MDP | 0.0309 | 128.38 | 0.002238 | Yes |
| Baseline B — Stoch.UC + Merit dispatch | 0.0134 | 42.01 | 0.000732 | Yes |

### Penetration Sweep (Proposed vs Deterministic Baseline)

| VRE % | LOLP (Proposed) | LOLP (Det.) | EENS (Proposed) | UC Cost (USD) |
|-------|-----------------|-------------|-----------------|---------------|
| 20% | 0.0361 | 0.0571 | 121.5 MWh | 703,874 |
| 30% | 0.0171 | 0.0314 | 45.5 MWh | 641,383 |
| 40% | 0.0131 | 0.0247 | 39.0 MWh | 582,663 |
| 50% | 0.0058 | 0.0218 | 11.1 MWh | 538,016 |
| 60% | 0.0093 | 0.0207 | 25.6 MWh | 495,307 |

## Repository Layout

```
rts96-stochastic-uc-mdp/
├── src/rts96_reliability_uc/       # Core package
│   ├── config.py                   # Constants (LOLP_EPS, storage params, VOLL)
│   ├── data.py                     # RTS-96 demand profile, T=24
│   ├── generators.py               # 32-unit IEEE RTS-96 fleet
│   ├── scenarios.py                # AR(1) wind + solar VRE scenarios, Markov chain
│   ├── unit_commitment.py          # Stage 1: stochastic UC MIP via HiGHS
│   ├── mdp.py                      # Stage 2: MDP value iteration + dispatch
│   ├── evaluation.py               # Monte Carlo reliability (LOLP, EENS, 95% CI)
│   ├── baselines.py                # Deterministic UC + merit-order dispatch baselines
│   ├── powerflow.py                # pandapower IEEE RTS-24 AC power flow
│   └── runner.py                   # Full pipeline entry point
├── scripts/
│   ├── run_case.py                 # Run full simulation + penetration sweep
│   ├── make_charts.py              # Generate 4 analytical charts
│   └── smoke_test.py               # Quick import + correctness check
├── tests/                          # pytest suite (23 tests)
│   ├── test_scenarios.py
│   ├── test_baselines.py
│   └── test_mdp.py
├── outputs/
│   ├── run_log.txt                 # Full simulation log
│   ├── sweep_v2.csv                # Penetration sweep results
│   └── figures/                   # Generated charts and manuscript figures
├── docs/
│   ├── paper_sections/             # Markdown drafts for manuscript sections 4-7
│   └── research_notes.md
├── rts96_stochastic_uc_mdp.py      # Backward-compatibility wrapper
├── presentation.md                 # MARP slide deck
├── pyproject.toml
├── requirements.txt
└── LICENSE                         # MIT
```

## System Specification

| Parameter | Value |
|-----------|-------|
| Test system | IEEE RTS-96 (24-bus) |
| Generators | 32 units (U12 → U400) |
| Installed capacity | 3,405 MW |
| Annual peak demand | 2,850 MW |
| Reserve margin | 19.5% |
| VRE nameplate (40%) | 3,257 MW |
| Storage | 200 MWh / 50 MW, η_c = η_d = 0.92 |
| LOLP target ε | 0.08 |
| UC scenarios K | 30 |
| MDP state space | 2,400 (10 × 10 × 24) |
| MC samples N | 5,000 |
| Solver | HiGHS (highspy) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Smoke test (fast, ~10 s)
python scripts/smoke_test.py

# Full simulation + penetration sweep (~5 min)
python scripts/run_case.py

# Generate analytical charts
python scripts/make_charts.py
```

## Running Tests

```bash
pytest tests/ -v
```

23 tests covering scenario generation, Markov transition, UC commitment,
MDP value iteration, dispatch bounds, and reliability CI computation.

## Dependencies

| Package | Version |
|---------|---------|
| highspy | ≥ 1.7, < 2 |
| numpy | ≥ 1.24, < 2 |
| pandas | ≥ 2.0 |
| matplotlib | ≥ 3.7 |
| pandapower | ≥ 2.13 |

## License

MIT License — see [LICENSE](LICENSE).

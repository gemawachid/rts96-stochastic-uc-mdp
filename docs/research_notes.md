# Research Notes

## Implemented And Verified

- Stage 1 MIP is implemented with HiGHS and explicit binary commitment,
  startup, shutdown, loss-of-load indicators, and the LOLP constraint.
- Stage 2 MDP is implemented over 10 net-load bins, 10 SoC bins, and 24 hours.
- Monte Carlo evaluation samples 5,000 daily trajectories with generator forced
  outages.
- IEEE RTS-96 single-area data has been corrected to 32 units, 3,405 MW
  installed capacity, 2,850 MW annual peak load, corrected FOR values, corrected
  load profile, and corrected bus assignments.
- Penetration sweep behavior is physically sensible: the proposed method remains
  reliable at 40% VRE while the deterministic reserve-margin baseline collapses.

## Honest Limitations To Include

- `LOLP_EPS = 0.08` is much looser than conventional planning standards such as
  0.1% event probability. The paper should state that this value is a
  computational reliability target under a coarse 30-scenario approximation, not
  a final planning standard.
- The transition matrix is estimated from only 30 VRE scenarios. This is enough
  to demonstrate the framework but too rough for a definitive production-grade
  reliability assessment.
- The MDP discretization, 10 net-load bins by 10 SoC bins, needs a sensitivity
  check against larger grids such as 15x15 or 20x20.
- Current dispatch is a tractable economic dispatch abstraction, not a full AC
  or security-constrained real-time OPF.

## Recommended Next Experiments

1. Increase scenario counts and report the feasibility/reliability tradeoff for
   `K = 30, 60, 100`.
2. Run MDP discretization sensitivity for `10x10`, `15x15`, and `20x20`.
3. Report confidence intervals for Monte Carlo LOLP.
4. Compare the proposed commitment against deterministic reserve margins of
   15%, 25%, and 35%.
5. Save all sweep outputs to `outputs/` rather than an absolute external path.

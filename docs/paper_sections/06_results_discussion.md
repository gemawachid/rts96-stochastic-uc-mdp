# 6. Results And Discussion

## 6.1 Main 40% VRE Result

At 40% VRE penetration, the proposed reliability-constrained UC with adaptive MDP
dispatch achieves a Monte Carlo LOLP near 0.007 in the current runs. The
deterministic baseline reaches LOLP near 1.000, indicating that a fixed reserve
margin is not meaningful once VRE uncertainty dominates the net-load process.

The key result is not only that the proposed method performs better, but that
the commitment decision is made against an explicit reliability constraint rather
than a heuristic reserve proxy.

## 6.2 Penetration Sweep

The penetration sweep should be used to show how reliability degrades as VRE
penetration increases. The expected pattern is that deterministic reserve-margin
commitment becomes unreliable quickly, while the proposed method commits enough
flexible capacity to preserve the target over a wider VRE range.

Recommended table columns:

- VRE penetration.
- Proposed LOLP.
- Proposed EENS.
- Deterministic baseline LOLP.
- Deterministic baseline EENS.
- MIP objective.
- MIP-estimated LOLP.

## 6.3 Why The Deterministic Baseline Fails

The deterministic baseline fails because reserve margin is a capacity statistic,
not a probability statement about realized net-load trajectories. Under high VRE
penetration, the variance and temporal correlation of renewable output make a
single margin unable to distinguish low-risk and high-risk hours.

## 6.4 MIP LOLP Versus Monte Carlo LOLP

The paper should distinguish the scenario-approximated LOLP inside the MIP from
the Monte Carlo LOLP under forced outages and the MDP dispatch policy. Agreement
between the two is desirable, but exact equality should not be expected because
the evaluator includes additional stochastic outage realizations.

## 6.5 Limitations

The results should be framed as evidence for the modeling framework. The current
case does not yet prove production-grade reliability performance because the VRE
scenario count and MDP grid are intentionally small. Add sensitivity experiments
before submission.

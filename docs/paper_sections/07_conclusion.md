# 7. Conclusion

This paper proposes a two-stage framework for reliability-constrained unit
commitment under high VRE penetration. The first stage solves a stochastic MIP
with an explicit LOLP constraint, and the second stage solves an adaptive MDP
dispatch policy by value iteration. The framework is evaluated on the corrected
IEEE RTS-96 system with Monte Carlo simulation of VRE uncertainty and generator
forced outages.

The main finding is that enforcing reliability directly changes the commitment
decision in ways that reserve-margin heuristics do not capture. In the 40% VRE
case, the proposed method maintains low empirical LOLP while the deterministic
reserve-margin baseline becomes unreliable.

Future work should tighten the reliability target using larger scenario sets,
apply scenario reduction, test finer MDP discretizations, and extend the
real-time dispatch model toward security-constrained network operation.

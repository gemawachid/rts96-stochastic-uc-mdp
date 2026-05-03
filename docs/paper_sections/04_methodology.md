# 4. Methodology

This section should explain how the mathematical formulation is converted into
the implemented two-stage algorithm.

## 4.1 Stage 1 Reliability-Constrained Stochastic UC

The first stage solves a mixed-integer program over a 24-hour horizon. Binary
variables represent commitment, startup, shutdown, and scenario-hour
loss-of-load indicators. Continuous variables represent thermal generation,
storage charge/discharge, state of charge, unserved energy, and VRE curtailment.

The central modeling feature is the explicit LOLP constraint. Instead of
requiring a fixed reserve margin, the model bounds the probability-weighted
fraction of scenario-hours in which unserved energy is positive. This directly
links the day-ahead commitment to a formal reliability target.

## 4.2 Stage 2 Adaptive MDP Dispatch

The second stage treats real-time dispatch as a finite-horizon Markov Decision
Process. The state is `(hour, net-load bin, storage SoC bin)`. The action is the
storage charge/discharge decision. Given the action, committed generators are
economically dispatched in merit order and any remaining demand is counted as
unserved energy.

The value function is solved by backward induction:

```text
V_t(l,e) = max_b { r_t(l,e,b) + sum_l' P_t(l,l') V_{t+1}(l',e') }
```

where `l` is the net-load state, `e` is the storage state, `b` is storage action,
and `P_t` is the empirical net-load transition matrix estimated from VRE
scenarios.

## 4.3 Reliability Evaluation

Reliability is not reported from the MIP alone. The committed fleet is evaluated
under the Stage 2 MDP policy using Monte Carlo daily trajectories. Each sample
draws a VRE trajectory and generator availability states according to the unit
forced outage rates. A day is counted as a loss-of-load day if any hour has
unserved energy.

## 4.4 Approximation Choices

The current implementation uses 10 net-load bins, 10 storage bins, and 30 VRE
scenarios. These choices make the exact value iteration and MIP tractable while
preserving the sequential structure of the dispatch problem. The paper should
acknowledge that these are computational approximations and include sensitivity
checks over scenario count and discretization size.

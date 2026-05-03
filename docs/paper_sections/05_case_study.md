# 5. Case Study Setup

## 5.1 Test System

The case study uses the single-area IEEE RTS-96 24-bus system. The corrected
fleet contains 32 generating units with 3,405 MW of installed capacity and a
2,850 MW annual peak load. The resulting planning reserve margin is 19.5%.

## 5.2 VRE And Storage Assumptions

VRE penetration is defined relative to annual peak demand and average capacity
factor. The scenario generator combines wind and solar components, with wind
following an autocorrelated process and solar following a daylight envelope.

Storage is modeled as a 1,000 MWh, 400 MW resource with charge and discharge
efficiencies of 0.92. Storage is included to represent flexible real-time
balancing capability under high VRE uncertainty.

## 5.3 Compared Methods

The proposed method is compared against:

1. Deterministic UC with reserve-margin logic followed by the same MDP dispatch.
2. Stochastic UC followed by simple merit-order dispatch.

This separates the value of reliability-constrained commitment from the value of
adaptive real-time control.

## 5.4 Solver And Simulation Settings

The Stage 1 MIP is solved using HiGHS through `highspy`. The Stage 2 MDP is
solved exactly by backward value iteration over the finite state space. Monte
Carlo evaluation uses 5,000 daily samples for the main case.

## 5.5 Reliability Target

The current implementation uses `epsilon = 0.08`. This should be described as a
coarse-scenario operational reliability target used to demonstrate feasibility
of the framework, not as a claim that 8% LOLP is a desirable planning standard.
The limitation is important because conventional planning studies often use much
tighter reliability targets.

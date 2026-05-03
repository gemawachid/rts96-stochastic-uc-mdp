# Project Structure

## Programming Files

- `rts96_stochastic_uc_mdp.py`
  - Backward-compatible facade for old imports and direct execution.
  - The implementation now lives in `src/rts96_reliability_uc/`.

- `src/rts96_reliability_uc/config.py`
  - Simulation constants such as `LOLP_EPS`, `N_SCENARIOS`, `N_MC`, storage
    parameters, and VRE penetration.

- `src/rts96_reliability_uc/data.py`
  - IEEE RTS-96 generator, bus, load, and profile data.

- `src/rts96_reliability_uc/scenarios.py`
  - VRE scenario generation and Markov transition estimation.

- `src/rts96_reliability_uc/unit_commitment.py`
  - Stage 1 stochastic UC MIP solved with HiGHS.

- `src/rts96_reliability_uc/mdp.py`
  - Stage 2 adaptive MDP dispatch and backward value iteration.

- `src/rts96_reliability_uc/evaluation.py`
  - Monte Carlo reliability evaluation.

- `src/rts96_reliability_uc/baselines.py`
  - Deterministic UC and merit-order dispatch baselines.

- `src/rts96_reliability_uc/network.py`
  - pandapower network loading and validation.

- `src/rts96_reliability_uc/experiments.py`
  - Penetration sweep helper.

- `src/rts96_reliability_uc/runner.py`
  - Full command-line case-study workflow used by `scripts/run_case.py`.

- `scripts/run_case.py`
  - Clean runnable entry point.

## Paper Files

- `paper_v2.docx`
  - Current draft containing sections 1-3.

- `docs/paper_sections/04_methodology.md`
  - How the two-stage algorithm is implemented.

- `docs/paper_sections/05_case_study.md`
  - RTS-96 setup, VRE scenarios, storage, baselines, solver settings.

- `docs/paper_sections/06_results_discussion.md`
  - Main reliability and penetration-sweep interpretation.

- `docs/paper_sections/07_conclusion.md`
  - Findings, limitations, and future work.

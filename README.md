# Reliability-Constrained UC with Adaptive MDP Dispatch

This folder contains the research draft, figures, and executable code for the
IEEE RTS-96 case study on reliability-constrained stochastic unit commitment
with adaptive real-time MDP dispatch.

## Current Research Question

How can day-ahead commitment decisions be made so that a formal reliability
guarantee, `LOLP <= epsilon`, is maintained under the optimal real-time dispatch
policy rather than under a heuristic reserve margin?

## Folder Layout

- `paper_v2.docx` - current manuscript draft. It contains sections 1-3 and the
  corrected RTS-96 data tables.
- `rts96_stochastic_uc_mdp.py` - compatibility wrapper for old notebooks/scripts and
  direct execution.
- `src/rts96_reliability_uc/` - modular implementation of the data, scenario
  model, UC optimizer, MDP dispatch, evaluation, baselines, and experiments.
- `scripts/run_case.py` - clean entry point for running the full case study.
- `docs/paper_sections/` - markdown working drafts for missing sections 4-7.
- `docs/research_notes.md` - concise status, limitations, and writing plan.
- `fig*.png` - figures for the manuscript.
- `outputs/` - recommended location for generated CSVs, logs, and run outputs.

## Run

From this folder:

```powershell
python scripts\run_case.py
```

The original verified script can still be run directly:

```powershell
python rts96_stochastic_uc_mdp.py
```

## Implementation Components

- Stage 1: stochastic UC MIP solved by HiGHS with an explicit LOLP constraint.
- Stage 2: MDP dispatch policy solved by backward value iteration.
- Evaluation: Monte Carlo daily trajectory simulation with VRE uncertainty and
  generator forced outages.
- Baselines: deterministic reserve-margin UC and merit-order dispatch variants.

## Known Paper Issues To Discuss

- The current `LOLP_EPS = 0.08` target is intentionally loose relative to
  traditional planning targets and must be justified as a finite-scenario
  computational approximation.
- The 10 net-load bins, 10 SoC bins, and 30-scenario transition estimate need
  sensitivity discussion.
- Sections 4-7 need to be expanded into the actual methodology, case study,
  results, and conclusion.

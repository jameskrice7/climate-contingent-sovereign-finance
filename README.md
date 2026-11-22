# Climate-Contingent Sovereign Finance

**Fiscal Limits, Disaster Risk, and Repayment Design**

This repository contains the paper and the code needed to reproduce its tables,
figures, fiscal-limit calculations, and formal verification.

## Contents

- `paper/main.pdf`: the paper.
- `paper/main.tex`, `paper/sections/`, and `paper/references.bib`: its LaTeX sources.
- `paper/generated/`: the table inputs, numerical macros, and figures used by LaTeX.
- `replication/`: the simulation engine, numerical checks, and figure-generation code.
- `generated/results.json` and `generated/seed_results.csv`: numerical results.
- `tests/`: checks of pricing, recovery, indexation, and fiscal-limit identities.
- `lean_verification/`: Lean proofs and pinned dependencies.

## Reproduction

Use Python 3.14, Tectonic 0.16.9, and Lean/mathlib 4.29.0. Install Python packages
in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cd lean_verification
lake exe cache get
cd ..
make reproduce PYTHON=.venv/bin/python
```

The command regenerates the numerical results and LaTeX inputs, runs the checks,
compiles the paper, and builds the Lean project. The calculations require no
external dataset. The first Tectonic run and mathlib cache download require
internet access. The simulation uses twenty independent seeds with 200,000
draws per setting and includes three grid resolutions for stationary deferrals.
Allow several minutes for the full computation.

The components can also be run separately:

```sh
python -m replication.run
python -m unittest discover -s tests -v
python -m replication.check_outputs
make paper
make lean
```

For PDF rendering and layout checks, install `requirements-dev.txt` and run
`make qa`. Rendered pages and the layout report are written to a temporary
directory outside the repository.

## Model

The principal comparisons use risk-neutral pricing, permanent state-contingent
relief, and zero recovery. Stationary borrowing capacity is
`alpha * Phi / (1 - Phi)` when `Phi < 1`. The deferral model carries postponed
service forward as an inherited obligation and capitalizes it at the safe rate.
Recovery, where included, is a share of repayment capacity. The paper specifies
the timing, calibration, default rule, and assumptions for each calculation.

The numerical optimizer evaluates all empirical default thresholds. Results
include paired contract comparisons and standard errors of the across-seed
means. Deferral outputs contain convergence residuals and state-boundary
checks. The country environments are theoretical illustrations.

## Formal verification

`lean_verification/LeanVerification/Basic.lean` checks the default-condition
algebra, growth-factor identities, homogeneity, threshold geometry, constant
payoff equivalence, generosity derivative, stationary recursion, capacity-based
payment bounds, NPV capitalization, and square identities used in the proofs.
There are no custom axioms or incomplete proofs.

The probabilistic arguments, Monte Carlo estimates, and stationary deferral
solver are supported by the mathematical exposition and numerical checks.
They are outside the formalized subset.

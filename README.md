# Climate-Contingent Sovereign Finance — second revision

Manuscript MDY-2026-0066. This repository contains the paper, a point-by-point
response, and the code and generated inputs used in the second revision.
The calculations are theoretical illustrations, not estimated country effects.

## Read the revision

- `paper/main.pdf`: revised paper; `paper/main.tex` and `references.bib`: sources.
- `reviews/response_round2.pdf` and `.tex`: response to the second-round comments
  and the separate eight-point referee report.
- `reviews/abstract_for_submission.txt`: matching abstract to paste into ScholarOne.
- `generated/results.json`: full results, including independent-seed uncertainty
  and stationary deferral diagnostics.
- `references/audit.csv`: disposition of all 82 original references and the five
  additions. Every reference retained in the active paper has a source and a
  claim-level check in `references/retained_sources.json`.

The supplied paper and first-round response were uploaded first in commit
`894faef`; that commit preserves the unedited source. `legacy/` retains the old
simulation engine, old bibliography, and original Lean source for provenance.
The original referee PDF and pasted report were read locally; reproducing the
research does not require them.

## Reproduce

Tested with Python 3.14, NumPy 2.5.5, SciPy 1.18.1, Matplotlib 3.11.2,
Tectonic 0.16.9, and Lean/mathlib 4.29.0 on macOS arm64.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m replication.run
python -m unittest discover -s tests -v
python -m replication.check_outputs
(cd paper && tectonic -X compile main.tex --outdir .)
(cd reviews && tectonic -X compile response_round2.tex --outdir .)
cd lean_verification
lake exe cache get
lake build
```

Tectonic and elan/Lake are separate system prerequisites. The first TeX build
and mathlib cache download require internet access; the numerical build uses no
external datasets or network calls. Mathlib's regenerable cache is about 7 GB
and is not committed. Python requirements are pinned; the complete environment
used for this run is recorded in `generated/environment.txt`.

With prerequisites installed, `make reproduce PYTHON=.venv/bin/python`
regenerates numerical inputs, runs model checks, compiles both PDFs, and checks
Lean. `make qa` additionally renders the PDFs using the optional packages in
`requirements-dev.txt`. PDF QA images are regenerable and excluded from Git.
`revision_simulations.py` remains a compatibility entry point for the new build.
The full build uses 20 seeds × 200,000 draws per setting and includes several
stationary state-grid refinements; allow several minutes. A reduced run with
`--draws 10000 --seeds 2 --skip-deferrals` is for development only and must not
replace submission results. `check_outputs` rejects a nonstandard seed count.

## Model and numerical changes

The main one-period model has capacity `alpha*g`, risk-neutral pricing, and
zero recovery. A clause in the main tables is a **permanent write-down**.
At fixed continuation capacity its MSB gain is a one-off gain. Repeated issuance
has borrowing factor `Phi`, stationary MSB `alpha*Phi/(1-Phi)`, and stationary
MSD `alpha*x_star/(1-Phi)`. These are reported separately.

The disaster contract now requires a verified output loss of at least 15%,
with event-only and alternative-threshold comparisons retained. An exponential
log jump of mean .25 implies a mean output loss of **20%**. The legacy stress
case has negative expected log growth; separate advanced-economy and
small-state cases use positive conditional trends and explicitly illustrative
hazards. The .08 logistics probability is a five-year exposure-block
probability, not an estimate of one or two shipping disruptions per decade.

`replication/model.py` maximizes the empirical proceeds curve at all default
thresholds, rather than using the former .001 face grid. This removes grid bias
but not Monte Carlo error or finite-sample maximization bias. Paired contracts
use common draws within each seed; tables report SEs of the mean of independent
seed estimates, while JSON also reports across-seed standard deviations.

`replication/deferrals.py` is a distinct stationary extension. Inherited claims
cannot be deferred again; new relief is capitalized at the safe rate and paid
one model period later, subject to survival at both dates. The state is
inherited face due next period. The paper reports `B(0)` under a stationary
policy and the schedule `B(a)`, **not** a stationary distribution or a scalar
country-independent deferral limit. Timing and pricing equations are in
Appendix A. Convergence residuals, grids, and boundary checks are archived.

Recovery is a fraction of capacity in default. Face-value recovery was removed
because it makes unrestricted MSB infinite. The paper reports the attainable
full-indexation resource bound. Positive recovery and full indexation are
checks on the step-clause gains, not fitted empirical exercises.

The old unrestricted tail-value proposition is replaced by a conditional
statement and a counterexample. Interior relief is established under stated
conditions and in a fully worked uniform-distribution example. The emissions
coupon insures **surprises**, and additive collateral easing mechanically
scales every instrument equally. A separate risk-dependent eligibility rule
makes its extra assumption explicit.

## Output map

| Code / output | Paper object |
|---|---|
| `model.py`, `results.json:cases` | One-period and stationary MSB/MSD; calibration arithmetic; resource bound |
| `run.py:psi_sweep`, `mu_sweep`, `faces` | Logistics, trend-growth, and common-face comparisons |
| `run.py:thresholds`, `recovery`, `temperature` | Loss thresholds, capacity recovery, and emissions surprises |
| `deferrals.py`, `results.json:deferrals` | Carried-forward claims, grids, convergence, and inherited-state figure |
| `run.py:haircuts` | Common additive versus default-risk-dependent collateral assumptions |
| `plots.py` | All four current figure files in `paper/generated/` |
| `run.py:make_tables` | Every simulation table and numerical prose macro |
| `seed_results.csv` | Raw per-seed estimates for case and logistics comparisons |
| `lean_verification/` | Precisely scoped formal subset; see its README |

The constant parameters in the calibration table come from the immutable
`Calibration` definitions. There are no manually copied simulation coordinates
in the current manuscript. Population formulas, simulations, and conjectures
are explicitly distinguished. Literature lookup is separate from the offline
replication build; Crossref rate-limited some original records, and unresolved
or mismatched records are not called verified. Removed entries are retained
only in the provenance audit.

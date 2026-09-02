# Lean 4 formal verification — "Climate-Contingent Sovereign Finance" (MDY-2026-0066)

This project machine-checks the closed-form content of the revised manuscript in the
Lean 4 theorem prover with mathlib (toolchain `leanprover/lean4:v4.29.0`,
mathlib `v4.29.0`). All statements live in `LeanVerification/Basic.lean`, each
cross-referenced to the equation, lemma, table, or figure it verifies.

## What is verified

| Lean theorem(s) | Paper object |
|---|---|
| `default_condition_equiv` | eq. (2), default condition in ratio form |
| `pricing_basic`, `recovery_yield`, `recovery_proceeds` | eq. (3) and Appendix A.2 pricing with fractional recovery |
| `damage_growth_ratio`, `transition_wedge_relative` | eqs. (6)–(8), transition wedge and Dietz–Venmans damage wedge |
| `default_event_homogeneous`, `proceeds_homogeneous` | Remark 1, homogeneity of degree one in (α, d) |
| `survival_upper_set_of_antitone` | Lemma 1(i), threshold structure for non-increasing contracts |
| `Hstep_monotone`, `stepClause_not_upper_set`, `stepClause_threshold_low`, `stepClause_threshold_high` | Lemma 1(ii) and the remark on the non-threshold window (see "Corrections" below) |
| `z1_payoff_equivalence`, `z1_same_range`, `z1_optimizer_value` | Section 5.5 / Table 5, Z = 1 payoff-equivalence |
| `logistics_pointwise_le`, `logistics_event_inclusion` | Lemma 2, FOSD shift from logistics amplification (pointwise core) |
| `proceeds_generosity_hasDerivAt`, `proceeds_generosity_deriv_at_zero` | Proof of Proposition 1, clause-generosity trade-off derivative |
| `annual_*`, `kappaZ_anchor` | Table 1, annual-equivalent conversions |
| `fig1_threshold`, `logistics_drag`, `nonthreshold_window`, `gain_*`, `fig5_declines` | displayed arithmetic and headline gain percentages (Tables 2, 5; Figures 1, 5) |

Probabilistic statements are verified at the level of their measure-free content
(pointwise event identities, survival-set geometry, exact derivatives of the
proceeds functional given a differentiable CDF); numerical table entries are
verified as real-number inequalities.

## Corrections surfaced by the verification

1. **Lemma 1 footnote (monotonicity class inverted).** The step-down clause
   H(g) = 1 − κ·1{g < ḡ} is weakly non-*de*creasing, so it is excluded — not
   included — by the "non-increasing" hypothesis. Its survival set genuinely
   fails to be an upper interval for d ∈ (αḡ, αḡ/(1−κ)) = (0.152, 0.217) at the
   baseline calibration (`stepClause_not_upper_set` gives the counterexample:
   at d = 0.20, g = 0.9 survives while g = 1.0 defaults). The revised Lemma 1(ii)
   states the exact characterization; the proceeds maximizer d* = αḡ = 0.152
   sits at the boundary of the threshold branch, and the sharp PD rise in
   Figure 4 over (0.152, 0.217) is the visible signature.
2. **Trade-off decomposition (proof of Proposition 1).** The survival-gain term
   carries the marginal payoff weight (1 − κ): marginal surviving states pay
   1 − κ, not 1. The weight is unity at κ = 0, so the main-text sufficient
   condition is unchanged; the correction strengthens the interior-optimum logic.

No numerical result or qualitative conclusion of the paper is affected.

## How to run

Requires [elan](https://github.com/leanprover/elan). From this directory:

```bash
lake exe cache get   # download prebuilt mathlib binaries (~5 GB, one-time)
lake build           # checks every theorem; exits 0 iff all proofs are accepted
```

There are no `sorry`s or axioms beyond mathlib's standard foundations.
The `.lake/` directory is a regenerable build cache and need not be archived.

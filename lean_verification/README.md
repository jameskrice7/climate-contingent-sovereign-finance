# Lean 4 verification: exact scope of the second revision

Pinned toolchain and mathlib: `v4.29.0`; dependency SHAs are in
`lake-manifest.json`. Run `lake exe cache get`, then `lake build` here.

The active target is `LeanVerification/Basic.lean`. It contains no `sorry` or
custom axioms. The original file is preserved at `../legacy/Basic_round1.lean`.

Verified statements include:

- ratio-form default condition and zero-recovery pricing algebra;
- transition and chronic-damage growth identities;
- homogeneity of default events and proceeds;
- threshold geometry and a non-threshold counterexample for the step clause;
- payoff equivalence when the trigger is certain and the payoff is constant;
- pointwise output ordering under a nonnegative logistics wedge;
- the exact generosity derivative, including its `(1-kappa)` weight;
- stationary recursion, uniqueness of the scalar algebraic solution, and the
  stationary relative-gain identity;
- realized repayment bounded by capacity with capacity-based recovery;
- repayment equality under full linear indexation;
- NPV-neutral capitalization in the absence of default;
- square identities and inequalities used in the uniform-distribution example;
- corrected stress-case mean-log-growth and conditional-loss arithmetic.

The old face-recovery formulas and certificates for copied first-revision table
numbers were removed from the active target. An algebraic identity does not
establish that an economic recovery rule gives a bounded optimization problem.

Lean does **not** verify the simulation estimates, Monte Carlo standard errors,
reference validity, the entire probabilistic resource-bound proof, the whole
uniform-distribution case split, optimizer existence for every distribution,
the conditional tail proposition, or the stationary deferral solver. The
manuscript supplies the mathematical arguments outside this formal subset and
records the numerical solver's residuals and discretization checks separately.

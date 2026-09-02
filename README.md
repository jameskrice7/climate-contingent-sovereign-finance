# Replication files — "Climate-Contingent Sovereign Finance" (MDY-2026-0066, revised version)

This folder contains everything needed to reproduce the quantitative results in the
revised manuscript (Section 5 and Appendix C).

## Contents

| File | Purpose |
|---|---|
| `revision_simulations.py` | Generates **every table and figure** in Section 5 and Appendix C of the revised paper. |
| `test_simulation.py` | Lightweight sanity check of the simulation engine (original archive file). |
| `lean_verification/` | Lean 4 + mathlib project machine-checking the manuscript's closed-form claims (equations, Lemmas 1–2, Remark 1, proof of Proposition 1, Table 1 arithmetic); see its `README.md`. Run with `lake build`. |

## Requirements

- Python 3.9+ with `numpy` (no other dependencies).

## How to run

```bash
python revision_simulations.py
```

Runtime is a few minutes (N = 200,000 Monte Carlo draws, fixed seed 42, face-value
grid [0, 0.40] in steps of 0.001). The script prints all results to stdout and writes
`revision_results.json` to the working directory.

## Mapping of output blocks to the paper

| Output block | Paper object |
|---|---|
| `A_headline` | Headline MSB gains at ψ = 0 and ψ = 1.5 (quoted in Sections 1 and 5.3) |
| `B_vs_alpha` | Table 4, top panel (gains vs. surplus capacity α; Remark 1 invariance) |
| `C_vs_mu` | Table 4, bottom panel (gains vs. mean log growth µ) |
| `D_vs_psi` | Table 2 and Figure 5 (gains vs. logistics amplification ψ) |
| `E_vs_d` | Table 3 (proceeds advantage by rollover need d) |
| `F_temperature` | Table 6, Panel A (weak coupling: λ₁ = 0.10, δ_C = 0.05) |
| `F_temperature_strong` | Table 6, Panel B (strong coupling: λ₁ = 0.40, δ_C = 0.15; κ_T ∈ {0.30, 0.50}) |
| `F_lambda_effect` | Text note in Section 5.6 (fixed vs. state-dependent disaster intensity λ(ΔC)) |
| `G_Z1` | Table 5 (Z = 1 certain-disaster scenario) |
| `H_haircut` | Table C1 (collateral-haircut comparative static, Appendix C) |
| `I_fig` | TikZ coordinates for Figures 3, 4, 5, and 6 (proceeds, default probability, MSB vs. ψ, MSB vs. κ) |

## Model summary

One-period fiscal-limit illustration (5-year model period). Growth factor:

```
g = exp(µ + ε + J) · exp(−ψL)
```

- ε ~ N(µ, σ²): baseline growth shock
- J: rare-disaster jump, active with probability p_dis, exponential magnitude
  (mean 0.25) — note the **exponential** disaster-size distribution; the revised
  paper's numbers use this specification throughout
- L: logistics wedge, active with probability p_log, exponential magnitude (mean 0.06)
- ψ: logistics amplification (proxy for production-network centrality)

Contracts: straight debt H = 1; GDP clause H = 1 − κ·1{g < ḡ}; disaster clause
H = 1 − κ_Z·Z; temperature-linked coupon H = 1 − κ_T(ΔC/ΔC̄ − 1) with disaster
intensity λ(ΔC) increasing in global emissions growth.

Default occurs when d·H > α·g; price q(d) = E[H·1{survive}]/R_f; the MSB analogue is
max_d d·q(d). Baseline calibration (per 5-year period): R_f = 1.08, α = 0.16,
µ = 0.01, σ = 0.10, p_dis = 0.15, p_log = 0.08; see Table 1 of the paper for
provenance and annual equivalents.

## Contact

James K Rice, University of Essex (UK).

/-
Second-revision formal subset. See README.md for the exact scope.
Original source is retained under legacy/Basic_round1.lean. Obsolete
face-recovery pricing and hard-coded first-revision gain certificates are
removed from the active target. No sorry or custom axioms are used.
-/
import Mathlib

open Real

namespace CarbonRisk

/-! ## Section 2, eq. (2): the default condition in ratio form

`D_t - alpha Y_t > B_t^M  iff  D_t/Y_t > alpha + b_t^M` with `b = B/Y`. -/

theorem default_condition_equiv (D Y a B : ℝ) (hY : 0 < Y) :
    B < D - a * Y ↔ a + B / Y < D / Y := by
  rw [lt_div_iff₀ hY]
  have h : (a + B / Y) * Y = a * Y + B := by field_simp
  rw [h]
  constructor <;> intro <;> linarith

/-- Zero-recovery promised-yield identity; default losses enter pricing once. -/
theorem pricing_basic (R Rf PD : ℝ) (h : R * (1 - PD) = Rf)
    (hden : 1 - PD ≠ 0) : R = Rf / (1 - PD) := by
  apply (eq_div_iff hden).2
  exact h

/-! ## Section 2, eqs. (7)-(8): the Dietz--Venmans damage wedge.

The ratio of damage factors between consecutive periods is the multiplicative
growth wedge appearing in eq. (8). -/

theorem damage_growth_ratio (rho T0 T1 : ℝ) :
    exp (-(rho / 2) * T1 ^ 2) / exp (-(rho / 2) * T0 ^ 2)
      = exp (-(rho / 2) * (T1 ^ 2 - T0 ^ 2)) := by
  rw [← Real.exp_sub]
  ring_nf

/-- Eq. (6): the transition wedge in absolute vs. relative emissions,
`((c Ebar + E') / (c Ebar + E))^beta = ((c + e') / (c + e))^beta`
with `e = E / Ebar`. -/
theorem transition_wedge_relative (c Ebar E E' beta : ℝ)
    (hEbar : 0 < Ebar) :
    ((c * Ebar + E') / (c * Ebar + E)) ^ beta
      = ((c + E' / Ebar) / (c + E / Ebar)) ^ beta := by
  congr 1
  have hEbar' : Ebar ≠ 0 := ne_of_gt hEbar
  have h1 : c * Ebar + E' = (c + E' / Ebar) * Ebar := by field_simp
  have h2 : c * Ebar + E = (c + E / Ebar) * Ebar := by field_simp
  rw [h1, h2, mul_div_mul_right _ _ hEbar']

/-! ## Remark 1: homogeneity of degree one in (alpha, d).

Replacing `alpha` by `c*alpha` and `d` by `c*d'` leaves the default event
unchanged; proceeds `d*q` then scale by `c`. -/

theorem default_event_homogeneous (c a dv H g : ℝ) (hc : 0 < c) :
    (c * dv) * H ≤ (c * a) * g ↔ dv * H ≤ a * g := by
  constructor <;> intro h <;> nlinarith

theorem proceeds_homogeneous (c dv q : ℝ) : (c * dv) * q = c * (dv * q) := by
  ring

/-! ## Lemma 1(i) (corrected): threshold default set for weakly
non-increasing contracts.

If `H` is antitone (weakly non-increasing: repayment weakly HIGHER in bad
states, e.g. straight debt `H = 1` or countercyclical payoffs), the survival
set `{g : d H(g) <= alpha g}` is an upper set. -/

theorem survival_upper_set_of_antitone (H : ℝ → ℝ) (hH : Antitone H)
    (a dv : ℝ) (ha : 0 < a) (hd : 0 ≤ dv) :
    ∀ g₁ g₂ : ℝ, g₁ ≤ g₂ → dv * H g₁ ≤ a * g₁ → dv * H g₂ ≤ a * g₂ := by
  intro g₁ g₂ hle hsurv
  have h1 : dv * H g₂ ≤ dv * H g₁ := mul_le_mul_of_nonneg_left (hH hle) hd
  have h2 : a * g₁ ≤ a * g₂ := mul_le_mul_of_nonneg_left hle (le_of_lt ha)
  linarith

/-! ## Lemma 1(ii) (corrected): the step-down (GDP) clause. -/

/-- The GDP clause payoff `H(g) = 1 - kappa * 1{g < gbar}` (eq. (22)). -/
noncomputable def Hstep (kappa gbar g : ℝ) : ℝ :=
  if g < gbar then 1 - kappa else 1

/-- The step-down clause is weakly non-DEcreasing (monotone), hence excluded
from Lemma 1(i)'s hypothesis class — the original footnote had this
inverted. -/
theorem Hstep_monotone (kappa gbar : ℝ) (hk : 0 ≤ kappa) :
    Monotone (Hstep kappa gbar) := by
  intro g₁ g₂ hle
  unfold Hstep
  by_cases h1 : g₁ < gbar <;> by_cases h2 : g₂ < gbar <;>
    simp only [h1, h2, if_false, if_pos, le_refl] <;>
    first
      | linarith


/-- COUNTEREXAMPLE (baseline calibration alpha = 0.16, kappa = 0.30,
gbar = 0.95, face value d = 0.20 in (alpha*gbar, alpha*gbar/(1-kappa)) =
(0.152, 0.217)): the survival set of the GDP clause is NOT an upper set —
g = 0.9 survives while g = 1.0 defaults.  This is the region of the sharp
default-probability rise in Figure 4. -/
theorem stepClause_not_upper_set :
    ∃ g₁ g₂ : ℝ, g₁ ≤ g₂ ∧
      0.20 * Hstep 0.30 0.95 g₁ ≤ 0.16 * g₁ ∧
      ¬(0.20 * Hstep 0.30 0.95 g₂ ≤ 0.16 * g₂) := by
  refine ⟨0.9, 1.0, by norm_num, ?_, ?_⟩
  · unfold Hstep
    rw [if_pos (by norm_num)]
    norm_num
  · unfold Hstep
    rw [if_neg (by norm_num)]
    norm_num

/-- Lemma 1(ii), low-face-value branch: for `d <= alpha * gbar` the survival
set IS a threshold set with `g*(d) = d (1-kappa) / alpha`. -/
theorem stepClause_threshold_low (a dv kappa gbar : ℝ)
    (ha : 0 < a) (hk0 : 0 ≤ kappa) (hk1 : kappa ≤ 1) (hd0 : 0 ≤ dv)
    (hd : dv ≤ a * gbar) :
    ∀ g : ℝ, dv * Hstep kappa gbar g ≤ a * g ↔ dv * (1 - kappa) / a ≤ g := by
  intro g
  unfold Hstep
  by_cases hg : g < gbar
  · rw [if_pos hg, div_le_iff₀ ha]
    constructor <;> intro h <;> nlinarith
  · rw [if_neg hg]
    push Not at hg
    have hsurv : dv * 1 ≤ a * g := by nlinarith
    have hthr : dv * (1 - kappa) / a ≤ g := by
      rw [div_le_iff₀ ha]
      nlinarith
    exact iff_of_true hsurv hthr

/-- Lemma 1(ii), high-face-value branch: for `d (1-kappa) >= alpha * gbar`
the survival set is again a threshold set, now with `g*(d) = d / alpha`. -/
theorem stepClause_threshold_high (a dv kappa gbar : ℝ)
    (ha : 0 < a) (hgbar : 0 < gbar) (hk0 : 0 ≤ kappa) (hk1 : kappa < 1)
    (hd : a * gbar ≤ dv * (1 - kappa)) :
    ∀ g : ℝ, dv * Hstep kappa gbar g ≤ a * g ↔ dv / a ≤ g := by
  intro g
  have hdpos : 0 < dv := by nlinarith
  unfold Hstep
  by_cases hg : g < gbar
  · rw [if_pos hg]
    have hlhs : ¬(dv * (1 - kappa) ≤ a * g) := by nlinarith
    have hrhs : ¬(dv / a ≤ g) := by
      rw [div_le_iff₀ ha]
      nlinarith
    exact iff_of_false hlhs hrhs
  · rw [if_neg hg]
    push Not at hg
    rw [div_le_iff₀ ha]
    constructor <;> intro h <;> nlinarith

/-! ## Section 5.5 (Table 5): the Z = 1 scenario.

With a certain trigger the disaster clause pays `1 - kappa_Z` in every state,
so issuing face value `d` of the clause is payoff-equivalent, state by state,
to issuing face value `(1 - kappa_Z) d` of straight debt: identical default
event and identical proceeds. -/

section Z1
variable (S : ℝ → ℝ) (Rf kz : ℝ)

/-- Proceeds of straight debt with face value `d`, written with an abstract
survival functional `S d = E[1{d <= alpha g}]`. -/
noncomputable def bStraight (dv : ℝ) : ℝ := dv * S dv / Rf

/-- Proceeds of the disaster clause when the trigger is certain: payoff
`1 - kz` in every state, default iff `d (1 - kz) > alpha g`. -/
noncomputable def bDisZ1 (dv : ℝ) : ℝ :=
  dv * ((1 - kz) * S ((1 - kz) * dv)) / Rf

theorem z1_payoff_equivalence (dv : ℝ) :
    bDisZ1 S Rf kz dv = bStraight S Rf ((1 - kz) * dv) := by
  unfold bDisZ1 bStraight
  ring

/-- Hence the two contracts attain the same set of proceeds values: the
rescaling `d ↦ d/(1-kz)` maps the straight-debt curve onto the clause curve
(`d* = 0.106/0.65 ≈ 0.163` in Table 5). -/
theorem z1_same_range (hkz : (1 : ℝ) - kz ≠ 0) (dv' : ℝ) :
    ∃ dv : ℝ, bDisZ1 S Rf kz dv = bStraight S Rf dv' := by
  refine ⟨dv' / (1 - kz), ?_⟩
  rw [z1_payoff_equivalence]
  congr 1
  field_simp

end Z1

/-! ## Lemma 2: logistics amplification shifts `g` down pointwise
(the measure-free core of the FOSD statement).

`g(psi) = exp(mu + eps + J) * exp(-psi L)` with `L >= 0`: raising `psi`
lowers `g` in every state, so every event `{g <= t}` weakly enlarges. -/

theorem logistics_pointwise_le (x L psi1 psi2 : ℝ)
    (hL : 0 ≤ L) (hpsi : psi1 ≤ psi2) :
    exp x * exp (-(psi2 * L)) ≤ exp x * exp (-(psi1 * L)) := by
  apply mul_le_mul_of_nonneg_left _ (le_of_lt (exp_pos x))
  apply exp_le_exp.mpr
  nlinarith

theorem logistics_event_inclusion (x L psi1 psi2 t : ℝ)
    (hL : 0 ≤ L) (hpsi : psi1 ≤ psi2)
    (h : exp x * exp (-(psi1 * L)) ≤ t) :
    exp x * exp (-(psi2 * L)) ≤ t :=
  le_trans (logistics_pointwise_le x L psi1 psi2 hL hpsi) h

/-! ## Proposition 1 (proof, trade-off decomposition) — CORRECTED.

On the threshold branch `d <= alpha * gbar` (Lemma 1(ii)), proceeds are
`b(kappa) = (d/Rf) [ (1-kappa)(F(gbar) - F(g*)) + (1 - F(gbar)) ]` with
`g*(kappa) = d (1-kappa) / alpha`.  For a CDF `F` differentiable at `g*`
with density value `f`, the exact derivative is

  b'(kappa) = (d/Rf) [ (1-kappa) (d/alpha) f(g*) - (F(gbar) - F(g*)) ] .

The survival-gain term carries the marginal payoff weight `(1-kappa)`
(the marginal surviving states pay `1-kappa`, not 1); the weight is unity
only at `kappa = 0`, which is the main-text sufficient condition. -/

theorem proceeds_generosity_hasDerivAt
    (F : ℝ → ℝ) (dv a Rf gbar kappa fval : ℝ) (ha : a ≠ 0)
    (hF : HasDerivAt F fval (dv * (1 - kappa) / a)) :
    HasDerivAt
      (fun k : ℝ =>
        dv / Rf * ((1 - k) * (F gbar - F (dv * (1 - k) / a)) + (1 - F gbar)))
      (dv / Rf * ((1 - kappa) * (dv / a) * fval
        - (F gbar - F (dv * (1 - kappa) / a)))) kappa := by
  have hinner : HasDerivAt (fun k : ℝ => dv * (1 - k) / a) (-(dv / a)) kappa := by
    have heq : (fun k : ℝ => dv * (1 - k) / a)
        = fun k : ℝ => dv / a - dv / a * k := by
      funext k
      field_simp
    rw [heq]
    simpa using ((hasDerivAt_id kappa).const_mul (dv / a)).const_sub (dv / a)
  have hcomp : HasDerivAt (fun k : ℝ => F (dv * (1 - k) / a))
      (fval * -(dv / a)) kappa := hF.comp kappa hinner
  have hdiff : HasDerivAt (fun k : ℝ => F gbar - F (dv * (1 - k) / a))
      (-(fval * -(dv / a))) kappa := hcomp.const_sub (F gbar)
  have hlin : HasDerivAt (fun k : ℝ => 1 - k) (-1 : ℝ) kappa := by
    simpa using (hasDerivAt_id kappa).const_sub (1 : ℝ)
  have hprod := hlin.mul hdiff
  have hsum := hprod.add_const (1 - F gbar)
  have hfin := hsum.const_mul (dv / Rf)
  convert hfin using 1
  ring

/-- At `kappa = 0` the weight is unity and the derivative reduces to the
main-text sufficient condition: survival gain `(d/alpha) f(g*)` against
payoff reduction `F(gbar) - F(g*)` (both scaled by `d/Rf`). -/
theorem proceeds_generosity_deriv_at_zero
    (F : ℝ → ℝ) (dv a Rf gbar fval : ℝ) (ha : a ≠ 0)
    (hF : HasDerivAt F fval (dv * (1 - 0) / a)) :
    HasDerivAt
      (fun k : ℝ =>
        dv / Rf * ((1 - k) * (F gbar - F (dv * (1 - k) / a)) + (1 - F gbar)))
      (dv / Rf * ((dv / a) * fval - (F gbar - F (dv * (1 - 0) / a)))) 0 := by
  have h := proceeds_generosity_hasDerivAt F dv a Rf gbar 0 fval ha hF
  convert h using 1
  ring

/-! ## Table 1: annual-equivalent arithmetic (5-year model period). -/

/-- `R_f = 1.08` per 5-year period ⇔ about `1.55%` per year:
`1.0155^5 < 1.08 < 1.0156^5`. -/
theorem annual_riskfree : (1.0155 : ℝ) ^ 5 < 1.08 ∧ (1.08 : ℝ) < 1.0156 ^ 5 := by
  constructor <;> norm_num

/-- `p_dis = 0.15` per period ⇔ about `3.2%`/yr hazard:
`0.968^5 < 0.85 < 0.9681^5`. -/
theorem annual_disaster_hazard :
    (0.968 : ℝ) ^ 5 < 0.85 ∧ (0.85 : ℝ) < 0.9681 ^ 5 := by
  constructor <;> norm_num

/-- `p_log = 0.08` per period ⇔ about `1.65%`/yr hazard:
`0.9834^5 < 0.92 < 0.9835^5`. -/
theorem annual_logistics_hazard :
    (0.9834 : ℝ) ^ 5 < 0.92 ∧ (0.92 : ℝ) < 0.9835 ^ 5 := by
  constructor <;> norm_num

/-- `sigma = 0.10` per period ⇔ about `4.5%`/yr
(`0.0447^2 * 5 < 0.10^2 < 0.0448^2 * 5`, i.e. `0.10/sqrt 5 ≈ 0.0447`). -/
theorem annual_sigma :
    (0.0447 : ℝ) ^ 2 * 5 < 0.10 ^ 2 ∧ (0.10 : ℝ) ^ 2 < 0.0448 ^ 2 * 5 := by
  constructor <;> norm_num

/-- `alpha = 0.16` per period = `3.2%` of GDP per year; `mu = 0.01` = `0.2%`/yr. -/
theorem annual_alpha_mu : (0.16 : ℝ) / 5 = 0.032 ∧ (0.01 : ℝ) / 5 = 0.002 := by
  constructor <;> norm_num

/-- Disaster-clause anchor: a 2-year suspension is 40% of 5-year service. -/
theorem kappaZ_anchor : (2 : ℝ) / 5 = 0.40 := by norm_num

/-! ## Miscellaneous displayed arithmetic. -/

/-- Figure 1: straight-debt default threshold `d/alpha = 0.13/0.16 = 0.8125`. -/
theorem fig1_threshold : (0.13 : ℝ) / 0.16 = 0.8125 := by norm_num

/-- Section 5.3: unconditional logistics drag
`p_log * psi * E[L] = 0.08 * 1.5 * 0.06 = 0.72%` of output. -/
theorem logistics_drag : (0.08 : ℝ) * 1.5 * 0.06 = 0.0072 := by norm_num

/-- The non-threshold window of the GDP clause at the baseline calibration:
`(alpha gbar, alpha gbar/(1-kappa)) = (0.152, 0.2171...)`, so the reported
optimizer `d* = 0.152` sits exactly at the boundary of the threshold region. -/
theorem nonthreshold_window :
    (0.16 : ℝ) * 0.95 = 0.152 ∧
    (0.217 : ℝ) < 0.16 * 0.95 / (1 - 0.30) ∧
    (0.16 : ℝ) * 0.95 / (1 - 0.30) < 0.2172 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-! ## Second revision: stationary recursion and bounded recoveries.
These identities certify algebra and pointwise bounds, not the probabilistic
maximum, an estimated calibration, or the stationary deferral computation. -/

theorem stationary_solution (a phi : ℝ) (hphi : 1 - phi ≠ 0) :
    phi * (a + a * phi / (1 - phi)) = a * phi / (1 - phi) := by
  field_simp
  <;> ring

theorem stationary_unique (a phi b : ℝ) (hphi : 1 - phi ≠ 0)
    (h : b = phi * (a + b)) : b = a * phi / (1 - phi) := by
  apply (eq_div_iff hphi).2
  nlinarith

theorem stationary_gain (p q : ℝ) (hp : 1 - p ≠ 0)
    (hq : 1 - q ≠ 0) (hq0 : q ≠ 0) :
    (p / (1-p)) / (q / (1-q)) - 1 = (p-q) / (q*(1-p)) := by
  field_simp
  <;> ring

noncomputable def capacityPayment (promise cap rho : ℝ) : ℝ :=
  if promise ≤ cap then promise else rho * cap

theorem recovery_capacity_bound (promise cap rho : ℝ)
    (hcap : 0 ≤ cap) (hrho : rho ≤ 1) :
    capacityPayment promise cap rho ≤ cap := by
  unfold capacityPayment
  split_ifs with h
  · exact h
  · nlinarith

theorem full_indexation_payment (c gbar g : ℝ) (hb : gbar ≠ 0) :
    (c * gbar) * (g / gbar) = c * g := by
  field_simp

theorem deferral_npv (Rf dv h : ℝ) (hR : Rf ≠ 0) :
    dv * h / Rf + (Rf * dv * (1-h)) / Rf^2 = dv / Rf := by
  field_simp
  <;> ring

theorem uniform_boundary_certificate (r : ℝ) :
    (1+r-r^2)/2 = (5:ℝ)/8 - (r-(1:ℝ)/2)^2/2 := by ring

theorem uniform_middle_certificate (r : ℝ) :
    (r+2)^2 ≤ 5*(1+r^2) := by
  nlinarith [sq_nonneg (2*r-1)]

theorem uniform_quadratic_certificate (r u : ℝ) :
    8*(1+r^2)*((5:ℝ)/8 - u*((r+2)-(1+r^2)*u)/2)
      = (2*(1+r^2)*u-(r+2))^2 + (2*r-1)^2 := by ring

/-- Mean loss of an exponential log jump of mean .25 is .20, not .25. -/
theorem mean_loss_arithmetic : (0.25:ℝ)/(1+0.25) = 0.20 := by norm_num

/-- Expected log growth of the retained stress example including logistics. -/
theorem stress_mean_log : (0.01:ℝ)-0.15*0.25-1.5*0.08*0.06 = -0.0347 := by norm_num

end CarbonRisk

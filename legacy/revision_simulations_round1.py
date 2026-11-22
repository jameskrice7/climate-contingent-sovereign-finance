"""
Revision simulations for "Climate-Contingent Sovereign Finance"
(response to Reviewer 1 Major Comments 2, 5, 6 and Reviewer 2 Comment 6).

Extends the one-period Monte Carlo illustration in Carbon_Risk_Simulations.ipynb:
  A. Headline table: d*, b^M, PD(d*) and % MSB gain over straight debt for the
     GDP clause and the disaster clause, at psi = 0 and psi = 1.5.
  B. % MSB gain as a function of fiscal capacity alpha.
  C. % MSB gain as a function of mean log growth mu.
  D. % MSB gain as a function of logistics amplification psi (regenerates Table 2).
  E. Proceeds advantage of the GDP clause as a function of the rollover need d.
  F. Temperature-linked block: stochastic global emissions growth dC, disaster
     intensity lambda(dC) increasing in dC, chronic damage wedge, and a
     temperature-linked coupon H = 1 - kappa_T (dC/dCbar - 1). Also compares a
     fixed disaster intensity with the state-dependent lambda(dC).
  G. Z = 1 scenario (disaster occurs with certainty) to make the ordering
     between the GDP clause and the disaster clause explicit.
  H. Collateral-haircut comparative static for the appendix monetary block:
     premium pi(d;h) = theta_d PD(d) - xi (1-h) for eligible instruments.
  I. Fine-grid proceeds/default curves (tikz coordinates for Figures).

All parameters are per 5-year model period, following Seghini's periodization.
Seed 42, N = 200,000 draws, matching the published notebook.
"""

import json
import numpy as np

# ----------------------------------------------------------------------------
# Baseline calibration (per 5-year period)
# ----------------------------------------------------------------------------
R_f = 1.08          # gross risk-free rate over the period (~1.55%/yr)
ALPHA = 0.16        # max cumulative primary surplus over the period (~3.2%/yr)
MU = 0.01           # mean log growth net of trend adjustments
SIGMA = 0.10        # std of log growth over the period (~4.5%/yr)
P_DIS = 0.15        # disaster probability per period (~3.2%/yr, Barro 2006)
E_J = -0.25         # mean disaster jump (Barro 2006 disaster sizes 15-30%)
P_LOG = 0.08        # logistics disruption probability per period (~1.6%/yr)
E_L = 0.06          # mean logistics wedge conditional on disruption

KAPPA_GDP = 0.30    # GDP clause relief
YBAR_GDP = 0.95     # GDP clause trigger
KAPPA_Z = 0.35      # disaster clause relief
KAPPA_T = 0.30      # temperature-linked coupon sensitivity

N_SIM = 200_000
SEED = 42

D_GRID = np.linspace(0.0, 0.40, 401)      # face-value grid (step 0.001)

results = {}


def draw_shocks(n, seed):
    rng = np.random.default_rng(seed)
    eps = rng.normal(MU, SIGMA, n)
    u_dis = rng.random(n)
    j_mag = rng.exponential(-E_J, n)
    u_log = rng.random(n)
    l_mag = rng.exponential(E_L, n)
    dc = rng.lognormal(mean=-0.5 * 0.30 ** 2, sigma=0.30, size=n)  # E[dC/dCbar]=1
    return eps, u_dis, j_mag, u_log, l_mag, dc


EPS, U_DIS, J_MAG, U_LOG, L_MAG, DC = draw_shocks(N_SIM, SEED)


def make_output(psi=0.0, mu=MU, p_dis=P_DIS, z_forced=None, lam_of_dc=None,
                chronic_delta=0.0):
    """Growth factor g = exp(mu + eps + J - psi L - chronic wedge)."""
    eps = EPS - MU + mu
    if z_forced is not None:
        Z = np.full(N_SIM, z_forced)
    elif lam_of_dc is not None:
        p = np.clip(lam_of_dc(DC), 0.01, 0.60)
        Z = (U_DIS < p).astype(float)
    else:
        Z = (U_DIS < p_dis).astype(float)
    J = -J_MAG * Z
    L = L_MAG * (U_LOG < P_LOG)
    g = np.exp(eps + J - psi * L - chronic_delta * (DC - 1.0))
    return g, Z


def H_straight(g, Z):
    return np.ones_like(g)


def H_gdp(g, Z, kappa=KAPPA_GDP, ybar=YBAR_GDP):
    return 1.0 - kappa * (g < ybar)


def H_dis(g, Z, kappa_z=KAPPA_Z):
    return 1.0 - kappa_z * Z


def H_temp(g, Z, kappa_t=KAPPA_T):
    return 1.0 - kappa_t * (DC - 1.0)


def curve(g, H, alpha=ALPHA, d_grid=D_GRID, r_gross=None, theta_d=0.0, prem_shift=0.0):
    """Proceeds b(d), PD(d) on the grid. Optional PD-linked premium:
    R(d) = R_f * exp(theta_d * PD(d) + prem_shift)."""
    b = np.empty_like(d_grid)
    pd_ = np.empty_like(d_grid)
    cap = alpha * g
    for i, d in enumerate(d_grid):
        surv = d * H <= cap
        pd_[i] = 1.0 - surv.mean()
        r = (r_gross if r_gross is not None else R_f) * np.exp(theta_d * pd_[i] + prem_shift)
        b[i] = d * np.mean(H * surv) / r
    return b, pd_


def msb(b, d_grid=D_GRID):
    i = int(np.argmax(b))
    return d_grid[i], b[i], i


def summarize(name, g, H, alpha=ALPHA, **kw):
    b, pd_ = curve(g, H, alpha=alpha, **kw)
    d_star, bm, i = msb(b)
    return {"name": name, "d_star": round(float(d_star), 3),
            "MSB": round(float(bm), 5), "PD_at_dstar": round(float(pd_[i]), 5)}


def pct(x, base):
    return round(100.0 * (x / base - 1.0), 2)


# ----------------------------------------------------------------------------
# A. Headline gains at psi = 0 and psi = 1.5
# ----------------------------------------------------------------------------
headline = []
for psi in (0.0, 1.5):
    g, Z = make_output(psi=psi)
    rows = [summarize("Straight", g, H_straight(g, Z)),
            summarize("GDP clause", g, H_gdp(g, Z)),
            summarize("Disaster clause", g, H_dis(g, Z))]
    base = rows[0]["MSB"]
    for r in rows:
        r["psi"] = psi
        r["gain_pct"] = pct(r["MSB"], base)
    headline += rows
results["A_headline"] = headline

# ----------------------------------------------------------------------------
# B. Gains vs alpha (at psi = 1.5)
# ----------------------------------------------------------------------------
g15, Z15 = make_output(psi=1.5)
vs_alpha = []
for a in (0.10, 0.13, 0.16, 0.19, 0.22):
    s = summarize("Straight", g15, H_straight(g15, Z15), alpha=a)
    gg = summarize("GDP", g15, H_gdp(g15, Z15), alpha=a)
    dd = summarize("DIS", g15, H_dis(g15, Z15), alpha=a)
    vs_alpha.append({"alpha": a, "MSB_straight": s["MSB"],
                     "gain_GDP_pct": pct(gg["MSB"], s["MSB"]),
                     "gain_DIS_pct": pct(dd["MSB"], s["MSB"])})
results["B_vs_alpha"] = vs_alpha

# ----------------------------------------------------------------------------
# C. Gains vs mu (at psi = 1.5)
# ----------------------------------------------------------------------------
vs_mu = []
for m in (-0.02, -0.01, 0.00, 0.01, 0.02, 0.03):
    g, Z = make_output(psi=1.5, mu=m)
    s = summarize("Straight", g, H_straight(g, Z))
    gg = summarize("GDP", g, H_gdp(g, Z))
    dd = summarize("DIS", g, H_dis(g, Z))
    vs_mu.append({"mu": m, "MSB_straight": s["MSB"],
                  "gain_GDP_pct": pct(gg["MSB"], s["MSB"]),
                  "gain_DIS_pct": pct(dd["MSB"], s["MSB"])})
results["C_vs_mu"] = vs_mu

# ----------------------------------------------------------------------------
# D. Gains vs psi (regenerates Table 2 with gain columns)
# ----------------------------------------------------------------------------
vs_psi = []
for psi in (0.0, 0.75, 1.5, 2.25, 3.0):
    g, Z = make_output(psi=psi)
    s = summarize("Straight", g, H_straight(g, Z))
    gg = summarize("GDP", g, H_gdp(g, Z))
    dd = summarize("DIS", g, H_dis(g, Z))
    for r, lbl in ((s, "Straight"), (gg, "GDP"), (dd, "DIS")):
        vs_psi.append({"contract": lbl, "psi": psi, **{k: r[k] for k in
                       ("d_star", "MSB", "PD_at_dstar")},
                       "gain_pct": pct(r["MSB"], s["MSB"])})
results["D_vs_psi"] = vs_psi

# ----------------------------------------------------------------------------
# E. Proceeds advantage vs rollover need d (psi = 1.5)
# ----------------------------------------------------------------------------
b_s, pd_s = curve(g15, H_straight(g15, Z15))
b_g, pd_g = curve(g15, H_gdp(g15, Z15))
vs_d = []
for d in (0.08, 0.10, 0.12, 0.13, 0.14, 0.15, 0.16):
    i = int(round(d / 0.40 * 400))
    adv = pct(b_g[i], b_s[i]) if b_s[i] > 1e-9 else float("inf")
    vs_d.append({"d": d, "b_straight": round(float(b_s[i]), 5),
                 "b_GDP": round(float(b_g[i]), 5), "advantage_pct": adv,
                 "PD_straight": round(float(pd_s[i]), 4),
                 "PD_GDP": round(float(pd_g[i]), 4)})
results["E_vs_d"] = vs_d

# ----------------------------------------------------------------------------
# F. Temperature-linked block (psi = 1.5)
# ----------------------------------------------------------------------------
LAM0, LAM1 = 0.15, 0.10          # lambda(dC) = 0.15 + 0.10 (dC/dCbar - 1)
DELTA_C = 0.05                   # chronic damage wedge on growth

lam = lambda dc: LAM0 + LAM1 * (dc - 1.0)
g_T, Z_T = make_output(psi=1.5, lam_of_dc=lam, chronic_delta=DELTA_C)

temp_rows = [summarize("Straight", g_T, H_straight(g_T, Z_T)),
             summarize("GDP clause", g_T, H_gdp(g_T, Z_T)),
             summarize("Disaster clause", g_T, H_dis(g_T, Z_T)),
             summarize("Temperature-linked", g_T, H_temp(g_T, Z_T))]
base = temp_rows[0]["MSB"]
for r in temp_rows:
    r["gain_pct"] = pct(r["MSB"], base)
results["F_temperature"] = temp_rows

# strong coupling: lambda(dC) = 0.15 + 0.40 (dC - 1), chronic delta = 0.15
lam_s = lambda dc: 0.15 + 0.40 * (dc - 1.0)
g_S, Z_S = make_output(psi=1.5, lam_of_dc=lam_s, chronic_delta=0.15)
strong_rows = [summarize("Straight", g_S, H_straight(g_S, Z_S)),
               summarize("GDP clause", g_S, H_gdp(g_S, Z_S)),
               summarize("Disaster clause", g_S, H_dis(g_S, Z_S)),
               summarize("Temperature-linked (kT=0.30)", g_S, H_temp(g_S, Z_S)),
               summarize("Temperature-linked (kT=0.50)", g_S,
                         H_temp(g_S, Z_S, kappa_t=0.50))]
base = strong_rows[0]["MSB"]
for r in strong_rows:
    r["gain_pct"] = pct(r["MSB"], base)
results["F_temperature_strong"] = strong_rows

# fixed lambda vs state-dependent lambda(dC), straight debt, no chronic wedge
g_fix, _ = make_output(psi=1.5)
g_lam, _ = make_output(psi=1.5, lam_of_dc=lam)
results["F_lambda_effect"] = {
    "straight_fixed_lambda": summarize("fixed", g_fix, np.ones(N_SIM)),
    "straight_lambda_of_T": summarize("state-dep", g_lam, np.ones(N_SIM))}

# ----------------------------------------------------------------------------
# G. Z = 1 scenario (disaster certain), psi = 0
# ----------------------------------------------------------------------------
g_z1, Z_z1 = make_output(psi=0.0, z_forced=1.0)
z1_rows = [summarize("Straight", g_z1, H_straight(g_z1, Z_z1)),
           summarize("GDP clause", g_z1, H_gdp(g_z1, Z_z1)),
           summarize("Disaster clause", g_z1, H_dis(g_z1, Z_z1))]
base = z1_rows[0]["MSB"]
for r in z1_rows:
    r["gain_pct"] = pct(r["MSB"], base)
results["G_Z1"] = z1_rows

# ----------------------------------------------------------------------------
# H. Collateral haircut comparative static (appendix), psi = 1.5
#    eligible GDP clause: R(d) = R_f exp(theta_d PD(d) - xi (1-h))
# ----------------------------------------------------------------------------
THETA_D, XI = 0.5, 0.02
haircut = []
for h in (1.0, 0.75, 0.5, 0.25, 0.0):
    r = summarize("GDP eligible", g15, H_gdp(g15, Z15),
                  theta_d=THETA_D, prem_shift=-XI * (1.0 - h))
    haircut.append({"h": h, **{k: r[k] for k in ("d_star", "MSB", "PD_at_dstar")}})
base_h = haircut[0]["MSB"]
for r in haircut:
    r["gain_pct"] = pct(r["MSB"], base_h)
results["H_haircut"] = haircut

# ----------------------------------------------------------------------------
# I. Tikz coordinates for figures (grid step 0.01 on [0, 0.30])
# ----------------------------------------------------------------------------
grid_c = np.linspace(0.0, 0.30, 31)


def coords(vals):
    return " ".join(f"({d:.2f},{v:.4f})" for d, v in zip(grid_c, vals))


fig = {}
for psi, tag in ((0.0, "psi0"), (1.5, "psi15")):
    g, Z = make_output(psi=psi)
    for H, lbl in ((H_straight(g, Z), "straight"), (H_gdp(g, Z), "gdp")):
        b, pd_ = curve(g, H, d_grid=grid_c)
        fig[f"b_{lbl}_{tag}"] = coords(b)
        fig[f"pd_{lbl}_{tag}"] = coords(pd_)

# MSB vs psi and vs kappa figure data
fig["msb_vs_psi"] = {lbl: " ".join(f"({r['psi']:.2f},{r['MSB']:.5f})"
                     for r in vs_psi if r["contract"] == lbl)
                     for lbl in ("Straight", "GDP", "DIS")}
kap_pts = []
for k in np.arange(0.1, 0.81, 0.1):
    b, _ = curve(g15, H_gdp(g15, Z15, kappa=k))
    kap_pts.append((k, msb(b)[1]))
fig["msb_vs_kappa"] = " ".join(f"({k:.1f},{v:.5f})" for k, v in kap_pts)

# gain vs alpha / mu / psi tikz series
fig["gain_vs_alpha_gdp"] = " ".join(f"({r['alpha']:.2f},{r['gain_GDP_pct']:.2f})" for r in vs_alpha)
fig["gain_vs_alpha_dis"] = " ".join(f"({r['alpha']:.2f},{r['gain_DIS_pct']:.2f})" for r in vs_alpha)
fig["gain_vs_mu_gdp"] = " ".join(f"({r['mu']:.2f},{r['gain_GDP_pct']:.2f})" for r in vs_mu)
fig["gain_vs_mu_dis"] = " ".join(f"({r['mu']:.2f},{r['gain_DIS_pct']:.2f})" for r in vs_mu)
results["I_fig"] = fig

with open("revision_results.json", "w") as f:
    json.dump(results, f, indent=1)

for key, val in results.items():
    print("=" * 78)
    print(key)
    print("=" * 78)
    if key == "I_fig":
        for k, v in val.items():
            print(f"--- {k}\n{v}")
    else:
        print(json.dumps(val, indent=1))

"""Fiscal limits with risk-neutral pricing; all inputs are per five years.

Exact empirical maximization uses every sampled default threshold, rather
than a face-value grid. It removes grid bias without claiming population
accuracy. Contract payoffs and GDP are observed before default.
"""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class Calibration:
    name: str = "Stress"
    alpha: float = .16
    rf: float = 1.08
    mu: float = .01
    sigma: float = .10
    p_dis: float = .15
    jump_mean: float = .25
    p_log: float = .08
    log_mean: float = .06
    psi: float = 1.5
    kappa: float = .30
    kappa_z: float = .35
    trigger: float = .95
    loss_trigger: float = .15


CASES = [Calibration(),
         Calibration(name="Advanced economy", mu=.075, p_dis=.025),
         Calibration(name="Disaster-prone small state", alpha=.10, mu=.075,
                     sigma=.15)]


def draw(c, n=200_000, seed=42, temperature=False, strong=False,
         force_disaster=False):
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, c.sigma, n)
    u = rng.random(n)
    j = rng.exponential(c.jump_mean, n)
    ulog = rng.random(n)
    ell = rng.exponential(c.log_mean, n) * (ulog < c.p_log)
    dc = rng.lognormal(-.5*.3**2, .3, n)
    p = c.p_dis
    delta = 0.
    if temperature:
        p = np.clip(p + (.4 if strong else .1)*(dc-1), .01, .60)
        delta = .15 if strong else .05
    z = np.ones(n, dtype=bool) if force_disaster else u < p
    loss = -np.expm1(-j) * z
    g = np.exp(c.mu + eps - j*z - c.psi*ell - delta*(dc-1))
    return dict(g=g, event=z, qualified=loss >= c.loss_trigger, loss=loss,
                dc=dc, ell=ell)


def payoff(c, s, contract, kappa=None):
    if contract == "Straight":
        return np.ones_like(s['g'])
    if contract == "GDP":
        return 1 - (c.kappa if kappa is None else kappa)*(s['g'] < c.trigger)
    if contract in ("Disaster", "Event-only"):
        return 1 - c.kappa_z*s['qualified' if contract == 'Disaster' else 'event']
    if contract == "Temperature":
        # A nonnegative repayment floor avoids subsidies on extreme draws.
        return np.maximum(0., 1 - (.3 if kappa is None else kappa)*(s['dc']-1))
    raise ValueError(contract)


def maximize(g, h, rf=1.08, recovery=0., premium_pd=0., haircut=1.,
             xi=.02, risk_eligibility=False):
    """Normalized capacity c=1, face x=d/c. Recovery is rho*g in default.

    Zero payoff observations never default and contribute no repayment.
    At a tied threshold all tied observations survive (weak inequality).
    """
    g, h = np.asarray(g), np.asarray(h)
    if np.any(g <= 0) or np.any(h < 0) or not 0 <= recovery <= 1:
        raise ValueError("Require g>0, h>=0, 0<=recovery<=1")
    n = len(g)
    thresholds = np.divide(g, h, out=np.full(n, np.inf), where=h>0)
    order = np.argsort(thresholds, kind='stable')
    t, hs, gs = thresholds[order], h[order], g[order]
    starts = np.r_[0, np.flatnonzero(t[1:] != t[:-1])+1]
    starts = starts[np.isfinite(t[starts])]
    if not len(starts):
        return dict(phi=0., x=0., pd=0.)
    ph = np.r_[0., np.cumsum(hs)]
    pg = np.r_[0., np.cumsum(gs)]
    x = t[starts]
    pd = starts/n
    premium = premium_pd*pd - xi*(1-haircut)*(1-pd if risk_eligibility else 1)
    b = (x*(ph[-1]-ph[starts]) + recovery*pg[starts])/n/rf/np.exp(premium)
    i = int(np.argmax(b))
    return dict(phi=float(b[i]), x=float(x[i]), pd=float(pd[i]))


def at_face(c, s, h, d, recovery=0.):
    cap = c.alpha*s['g']
    survive = d*h <= cap
    return dict(b=float(np.mean(np.where(survive, d*h, recovery*cap))/c.rf),
                pd=float(1-np.mean(survive)))


def levels(c, m):
    phi = m['phi']
    if phi >= 1:
        raise ValueError("No finite stationary solution: phi>=1")
    return dict(**m, one_msb=c.alpha*phi, one_msd=c.alpha*m['x'],
                stationary_msb=c.alpha*phi/(1-phi),
                stationary_msd=c.alpha*m['x']/(1-phi),
                capacity_multiplier=1/(1-phi))


def analytic_moments(c):
    return dict(expected_log_growth=c.mu-c.p_dis*c.jump_mean-c.psi*c.p_log*c.log_mean,
                annual_expected_log_growth=(c.mu-c.p_dis*c.jump_mean-c.psi*c.p_log*c.log_mean)/5,
                expected_g=np.exp(c.mu+.5*c.sigma**2)*
                (1-c.p_dis+c.p_dis/(1+c.jump_mean))*
                (1-c.p_log+c.p_log/(1+c.psi*c.log_mean)),
                mean_disaster_output_loss=c.jump_mean/(1+c.jump_mean),
                annual_disaster_probability=1-(1-c.p_dis)**.2,
                annual_logistics_probability=1-(1-c.p_log)**.2,
                qualified_probability=c.p_dis*(1-c.loss_trigger)**(1/c.jump_mean))

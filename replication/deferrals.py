"""Stationary NPV-neutral one-period deferrals with inherited claims.

State a: inherited nondeferrable face due next period / current GDP.
New face d pays dh(g) next period. Relief d(1-h) is capitalized at rf
and paid one period later, unless default occurs first. All claims have
zero recovery, default is absorbing, and new issuance maximizes proceeds.

B(a)=max_d d/rf E[S(a,d,g){h+(1-h)s(a')}],
S=1{a+dh <= g(alpha+B(a'))}, a'=rf*d*(1-h)/g,
s(a)=E[S(a,d*(a),g)].

These additional assumptions define an illustrative stationary extension,
with inherited repayment obligations and risk-neutral pricing.
"""
import numpy as np
from .model import draw, payoff


def joint_nodes(c, contract, n=500_000, seed=42, nodes=256):
    s = draw(c, n=n, seed=seed)
    h = payoff(c, s, contract)
    gg, hh, ww = [], [], []
    # Preserve trigger cells, then equal-probability quantiles within cells.
    for v in np.unique(h):
        mask = h == v
        gg.extend(np.quantile(s['g'][mask], (np.arange(nodes)+.5)/nodes))
        hh.extend([v]*nodes)
        ww.extend([mask.mean()/nodes]*nodes)
    return np.array(gg), np.array(hh), np.array(ww)


def solve(c, contract, nodes=256, state_points=241, face_points=601,
          max_iter=1500, tol=2e-7, seed=42, damping=.25, continuous_cdf=True):
    g, h, w = joint_nodes(c, contract, nodes=nodes, seed=seed)
    # Scale both grids by alpha, preserving exact surplus homogeneity.
    a = c.alpha*np.linspace(0, 16, state_points)
    d = c.alpha*np.linspace(0, 10, face_points)
    ap = c.rf*d[:,None]*(1-h)/g
    B = np.zeros_like(a)
    # Terminal no-new-issuance survival probability for inherited debt.
    surv = (a[:,None] <= c.alpha*g) @ w
    history = []
    chosen = np.zeros_like(a, dtype=int)
    for iteration in range(max_iter):
        Bnext = np.interp(ap, a, B, right=0.)
        snext = np.interp(ap, a, surv, right=0.)
        thresholds = g*(c.alpha+Bnext) - d[:,None]*h
        weights = w*(h+(1-h)*snext)
        order = np.argsort(thresholds, axis=1)
        T = np.take_along_axis(thresholds, order, axis=1)
        W = np.take_along_axis(weights, order, axis=1)
        P = np.take_along_axis(np.broadcast_to(w,T.shape), order, axis=1)
        cumW = np.c_[np.zeros(len(d)), np.cumsum(W,axis=1)]
        cumP = np.c_[np.zeros(len(d)), np.cumsum(P,axis=1)]
        vals = np.empty((len(d),len(a)))
        probs = np.empty_like(vals)
        for j in range(len(d)):
            if continuous_cdf:
                # Quantiles represent continuous probability cells, not atoms.
                # Linear cumulative integration avoids spurious default jumps
                # of one quadrature node when policy or inherited face changes.
                midW=cumW[j,1:]-.5*W[j]
                midP=cumP[j,1:]-.5*P[j]
                belowW=np.interp(a,T[j],midW,left=0.,right=cumW[j,-1])
                belowP=np.interp(a,T[j],midP,left=0.,right=cumP[j,-1])
                vals[j]=d[j]/c.rf*(cumW[j,-1]-belowW)
                probs[j]=cumP[j,-1]-belowP
            else:
                ix = np.searchsorted(T[j], a, side='left')
                vals[j] = d[j]/c.rf*(cumW[j,-1]-cumW[j,ix])
                probs[j] = cumP[j,-1]-cumP[j,ix]
        chosen = np.argmax(vals,axis=0)
        Bnew = vals[chosen,np.arange(len(a))]
        snew = probs[chosen,np.arange(len(a))]
        residual = max(np.max(np.abs(Bnew-B)), c.alpha*np.max(np.abs(snew-surv)))
        history.append(float(residual))
        if residual < tol:
            B, surv = Bnew, snew
            break
        B, surv = (1-damping)*B+damping*Bnew, (1-damping)*surv+damping*snew
    # Evaluate the *undamped* fixed-point residual; never conceal nonconvergence.
    return dict(contract=contract, B0=float(B[0]), d0=float(d[chosen[0]]),
                pd0=float(1-surv[0]), iterations=iteration+1,
                converged=bool(history[-1]<tol), residual=history[-1],
                max_deferred_state=float(ap[chosen].max()),
                state_max=float(a[-1]), face_max=float(d[-1]),
                state_boundary_B=float(B[-1]),
                chosen_face_boundary=bool(np.any(chosen==len(d)-1)),
                state=a.tolist(), borrowing=B.tolist(),
                face=d[chosen].tolist(), survival=surv.tolist(),
                residual_history=history, nodes=nodes,
                state_points=state_points, face_points=face_points,
                continuous_cdf=continuous_cdf, damping=damping)

import unittest
from dataclasses import replace
import numpy as np
from replication.model import CASES, draw, payoff, maximize, levels, at_face, analytic_moments


class FiscalLimitTests(unittest.TestCase):
    def test_optimizer_matches_direct_payment_enumeration_including_ties(self):
        g=np.array([.3,.7,.7,1.,1.4,2.])
        h=np.array([.65,.65,1.,1.,1.,.65])
        for rho in [0.,.4,1.]:
            m=maximize(g,h,recovery=rho)
            candidates=np.r_[0,g/h,np.linspace(0,5,2001)]
            direct=max(np.mean(np.where(x*h<=g,x*h,rho*g))/1.08 for x in candidates)
            self.assertAlmostEqual(m['phi'],direct,places=13)

    def test_resource_bound_at_all_recovery_rates(self):
        s=draw(CASES[0],n=5000)
        for k in ['Straight','GDP','Disaster']:
            h=payoff(CASES[0],s,k)
            for rho in [0.,.25,.75,1.]:
                m=maximize(s['g'],h,recovery=rho)
                self.assertLessEqual(m['phi'],s['g'].mean()/1.08+1e-13)
                if rho==1:self.assertAlmostEqual(m['phi'],s['g'].mean()/1.08,places=12)

    def test_full_indexation_attains_bound(self):
        s=draw(CASES[0],n=3000)
        m=maximize(s['g'],s['g']/.95)
        self.assertAlmostEqual(m['phi'],s['g'].mean()/1.08,places=12)

    def test_known_scalar_payoff_is_face_rescaling(self):
        g=draw(CASES[0],n=3000)['g']
        plain=maximize(g,np.ones_like(g))
        deferred=maximize(g,np.full_like(g,.65))
        self.assertAlmostEqual(plain['phi'],deferred['phi'],places=12)
        self.assertAlmostEqual(plain['x'],.65*deferred['x'],places=12)

    def test_surplus_homogeneity(self):
        c=CASES[0];s=draw(c,n=3000);h=payoff(c,s,'GDP')
        p=at_face(c,s,h,.14)
        q=at_face(replace(c,alpha=2*c.alpha),s,h,.28)
        self.assertEqual(p['pd'],q['pd'])
        self.assertAlmostEqual(2*p['b'],q['b'],places=13)

    def test_loss_trigger_excludes_small_events(self):
        c=CASES[0];s=draw(c,n=10000)
        self.assertTrue(np.all(s['qualified']<=s['event']))
        self.assertTrue(np.any(s['event'] & ~s['qualified']))
        h=payoff(c,s,'Disaster')
        self.assertTrue(np.all(h[~s['qualified']]==1))
        self.assertTrue(np.all(s['loss'][s['qualified']]>=.15))

    def test_stationary_limits_satisfy_recursion(self):
        c=CASES[0];s=draw(c,n=3000)
        for k in ['Straight','GDP','Disaster']:
            v=levels(c,maximize(s['g'],payoff(c,s,k)))
            self.assertAlmostEqual(v['stationary_msb'],v['phi']*(c.alpha+v['stationary_msb']),places=12)
            self.assertAlmostEqual(v['stationary_msd'],v['x']*(c.alpha+v['stationary_msb']),places=12)

    def test_unrestricted_tail_claim_has_counterexample(self):
        gains=[]
        for p in [.3,.5]:
            g=np.r_[np.full(int(p*100),.8),np.ones(100-int(p*100))]
            st=maximize(g,np.ones_like(g))['phi']
            gd=maximize(g,1-.05*(g<.95))['phi']
            self.assertAlmostEqual(gd-st,.8*.05*(1-p)/(.95*1.08),places=12)
            gains.append(gd-st)
        self.assertGreater(gains[0],gains[1])

    def test_calibration_arithmetic(self):
        m=analytic_moments(CASES[0])
        self.assertAlmostEqual(m['mean_disaster_output_loss'],.20)
        self.assertAlmostEqual(m['expected_log_growth'],-.0347)
        self.assertAlmostEqual(m['qualified_probability'],.0783009375)


if __name__=='__main__':unittest.main()

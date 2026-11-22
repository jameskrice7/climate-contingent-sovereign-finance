"""Generate the paper tables, figures, and machine-readable results."""
from dataclasses import replace, asdict
from pathlib import Path
import argparse
import csv
import json
import math
import platform
import sys
import numpy as np
from .model import CASES, draw, payoff, maximize, levels, at_face, analytic_moments
from .deferrals import solve

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'generated'
TEX = ROOT/'paper'/'generated'
CONTRACTS = ['Straight','GDP','Disaster','Event-only']


def estimate(v):
    v = np.asarray(v,dtype=float)
    sd = float(v.std(ddof=1)) if len(v)>1 else 0.
    return dict(mean=float(v.mean()), sd=sd, se=sd/math.sqrt(len(v)))


def aggregate(rows, keys):
    return {k:estimate([r[k] for r in rows]) for k in keys}


def percent(v,base):
    return 100*(v/base-1)


def compare(c, n, seeds, contracts=CONTRACTS, **drawkw):
    rows = []
    for seed in seeds:
        s = draw(c,n,seed,**drawkw)
        ms = {k:levels(c,maximize(s['g'],payoff(c,s,k),c.rf)) for k in contracts}
        straight = ms['Straight']
        for k,m in ms.items():
            m.update(contract=k,seed=seed,case=c.name,
                     one_gain=percent(m['one_msb'],straight['one_msb']),
                     stationary_gain=percent(m['stationary_msb'],straight['stationary_msb']),
                     stationary_msd_gain=percent(m['stationary_msd'],straight['stationary_msd']),
                     upper_bound=c.alpha*float(s['g'].mean())/c.rf)
            rows.append(m)
    return rows


KEYS = ['phi','x','pd','one_msb','one_msd','one_gain','stationary_msb',
        'stationary_msd','stationary_gain','stationary_msd_gain','upper_bound']


def by_contract(rows):
    return {k:aggregate([r for r in rows if r['contract']==k],KEYS)
            for k in dict.fromkeys(r['contract'] for r in rows)}


def cell(v, digits=2, scale=1, se=True):
    if isinstance(v,dict):
        se_digits=digits+1
        mean=v['mean']*scale
        mean=0. if round(mean,digits)==0 else mean
        return f"{mean:.{digits}f}" + (
            rf"\,({v['se']*scale:.{se_digits}f})" if se else '')
    return f"{v*scale:.{digits}f}"


def table(name, columns, rows):
    (TEX/(name+'.tex')).write_text(
        '\\begin{tabular}{@{}'+ 'l'+'r'*(len(columns)-1)+'@{}}\n\\toprule\n'+
        ' & '.join(columns)+r' \\ \midrule'+'\n'+
        '\n'.join(' & '.join(map(str,r))+r' \\' for r in rows)+
        '\n\\bottomrule\n\\end{tabular}\n')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--draws',type=int,default=200_000)
    ap.add_argument('--seeds',type=int,default=20)
    ap.add_argument('--skip-deferrals',action='store_true')
    args=ap.parse_args()
    OUT.mkdir(exist_ok=True); TEX.mkdir(exist_ok=True)
    seeds=list(range(42,42+args.seeds))
    result=dict(config=dict(n=args.draws,seeds=seeds,python=platform.python_version(),
                           numpy=np.__version__,pricing='risk-neutral, zero recovery unless stated',
                           optimizer='all empirical default thresholds'))
    all_rows=[]
    cases={}
    for c in CASES:
        rows=compare(c,args.draws,seeds)
        all_rows+=rows
        cases[c.name]=dict(parameters=asdict(c),moments=analytic_moments(c),
                          estimates=by_contract(rows))
        print('Completed',c.name,flush=True)
    result['cases']=cases
    c=CASES[0]
    result['psi_sweep']=[]
    for psi in [0,.75,1.5,2.25,3]:
        rows=compare(replace(c,psi=psi),args.draws,seeds)
        result['psi_sweep'].append(dict(psi=psi,estimates=by_contract(rows)))
        all_rows+= [dict(r,psi=psi) for r in rows]
    result['mu_sweep']=[]
    for mu in [-.02,-.01,0,.01,.02,.03]:
        result['mu_sweep'].append(dict(mu=mu,estimates=by_contract(
            compare(replace(c,mu=mu),args.draws,seeds))))
    result['temperature']=[]
    for strong in [False,True]:
        rows=compare(c,args.draws,seeds,contracts=['Straight','GDP','Disaster','Temperature'],
                     temperature=True,strong=strong)
        result['temperature'].append(dict(strong=strong,estimates=by_contract(rows)))
    result['certain_event']=by_contract(compare(c,args.draws,seeds,force_disaster=True))
    result['recovery']=[]; result['thresholds']=[]; result['haircuts']=[]
    for rho in [0,.25,.5,.75,1]:
        vals={k:[] for k in ['Straight','GDP','Disaster']}
        for seed in seeds:
            s=draw(c,args.draws,seed)
            ms={k:maximize(s['g'],payoff(c,s,k),c.rf,recovery=rho) for k in vals}
            for k,m in ms.items():
                vals[k].append(dict(b=c.alpha*m['phi'],gain=percent(m['phi'],ms['Straight']['phi'])))
        result['recovery'].append(dict(rho=rho,estimates={k:aggregate(v,['b','gain']) for k,v in vals.items()}))
    for threshold in [0,.05,.10,.15,.20,.30]:
        vals=[]
        for seed in seeds:
            cc=replace(c,loss_trigger=threshold)
            s=draw(cc,args.draws,seed)
            # At zero threshold require an event, so zero-loss non-events do not qualify.
            trigger=s['event'] & (s['loss']>=threshold)
            h=1-cc.kappa_z*trigger
            st=maximize(s['g'],np.ones(args.draws),c.rf)
            m=maximize(s['g'],h,c.rf)
            vals.append(dict(gain=percent(m['phi'],st['phi']),trigger=trigger.mean()))
        result['thresholds'].append(dict(threshold=threshold,**aggregate(vals,['gain','trigger'])))
    for rule in ['additive','risk-dependent']:
        for haircut in [1,.75,.5,.25,0]:
            vals={k:[] for k in ['Straight','GDP','Disaster']}
            for seed in seeds:
                s=draw(c,args.draws,seed)
                for k in vals:
                    h=payoff(c,s,k)
                    m=maximize(s['g'],h,c.rf,premium_pd=.5,haircut=haircut,
                               risk_eligibility=rule=='risk-dependent')
                    base=maximize(s['g'],h,c.rf,premium_pd=.5,haircut=1)
                    vals[k].append(dict(b=c.alpha*m['phi'],gain=percent(m['phi'],base['phi']),pd=m['pd']))
            result['haircuts'].append(dict(rule=rule,haircut=haircut,
                         estimates={k:aggregate(v,['b','gain','pd']) for k,v in vals.items()}))
    # Common-face illustration and exact benefit/cost decomposition.
    result['faces']=[]
    for d in [.08,.10,.12,.13,.14,.15,.16]:
        vals=[]
        for seed in seeds:
            s=draw(c,args.draws,seed); hg=payoff(c,s,'GDP')
            st=at_face(c,s,np.ones(args.draws),d); gd=at_face(c,s,hg,d)
            vals.append(dict(b_s=st['b'],b_g=gd['b'],pd_s=st['pd'],pd_g=gd['pd'],
                             gain=percent(gd['b'],st['b'])))
        result['faces'].append(dict(d=d,**aggregate(vals,['b_s','b_g','pd_s','pd_g','gain'])))
    s=draw(c,args.draws,42)
    h=payoff(c,s,'GDP'); d=.13; cap=c.alpha*s['g']
    avoid=(d>cap)&(d*h<=cap)
    wasted=(s['g']<c.trigger)&(d<=cap)
    result['figure1']=dict(d=d,avoided_mass=float(avoid.mean()),
        paid_in_survival_mass=float(wasted.mean()),
        default_straight=float(np.mean(d>cap)),default_gdp=float(np.mean(d*h>cap)),
        survival_payoff_gain=float(d*(1-c.kappa)*avoid.mean()/c.rf),
        survival_payoff_cost=float(d*c.kappa*wasted.mean()/c.rf))
    result['kappa_sweep']=[]
    for kappa in np.linspace(0,.95,39):
        vals=[]
        for seed in seeds:
            ss=draw(c,args.draws,seed)
            m=maximize(ss['g'],payoff(c,ss,'GDP',kappa=kappa),c.rf)
            vals.append(c.alpha*m['phi'])
        result['kappa_sweep'].append(dict(kappa=float(kappa),b=estimate(vals)))
    if not args.skip_deferrals:
        # Each row has its own straight-debt discretization control.
        result['deferrals']=[]
        for nodes,states,faces in [(128,321,801),(256,641,1601),(512,961,2401)]:
            for k in ['Straight','GDP','Disaster']:
                r=solve(c,k,nodes=nodes,state_points=states,face_points=faces)
                if not r['converged']:
                    first=r
                    r=solve(c,k,nodes=nodes,state_points=states,face_points=faces,
                            damping=.05,max_iter=4000)
                    r['initial_attempt']={key:first[key] for key in ['B0','residual','iterations','converged']}
                    r['damping']=.05
                result['deferrals'].append(r)
                print('Deferral',nodes,k,r['B0'],r['converged'],r['residual'],flush=True)
        if not all(r['converged'] for r in result['deferrals']):
            raise RuntimeError('Deferral fixed point did not converge; inspect numerical specification')
    else:
        cached_results=OUT/'results.json'
        if cached_results.exists():
            result['deferrals']=json.loads(cached_results.read_text()).get('deferrals',[])
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    with (OUT/'seed_results.csv').open('w') as f:
        cols=sorted(set().union(*(r.keys() for r in all_rows)))
        w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n");w.writeheader();w.writerows(all_rows)
    make_tables(result)
    from .plots import make_figures
    make_figures(result)
    print('Saved generated/results.json and paper/generated/',flush=True)


def make_tables(r):
    # All reported uncertainty is SE of the mean of independent seed estimates.
    rows=[]
    for name,case in r['cases'].items():
        for k in ['Straight','GDP','Disaster']:
            v=case['estimates'][k]
            short={'Stress':'Stress','Advanced economy':'Advanced','Disaster-prone small state':'Small state'}[name]
            rows.append([short if k=='Straight' else '',k,cell(v['one_msb'],4),
                         cell(v['pd'],2,100),cell(v['one_gain']),
                         cell(v['stationary_msb'],3),cell(v['stationary_gain'])])
    table('limits',['Case','Contract',r'$b_1^M$',r'$PD$ (\%)',r'Gain (\%)',r'$b_\infty^M$',r'Gain (\%)'],rows)
    rows=[]
    for name,case in r['cases'].items():
        for k in ['Straight','GDP','Disaster']:
            v=case['estimates'][k]
            short={'Stress':'Stress','Advanced economy':'Advanced','Disaster-prone small state':'Small state'}[name]
            rows.append([short if k=='Straight' else '',k,cell(v['one_msd'],3),
                         cell(v['stationary_msd'],3),cell(v['stationary_msd_gain'])])
    table('msd',['Case','Contract',r'$d_1^M$',r'$d_\infty^M$',r'Stationary gain (\%)'],rows)
    table('psi',[r'$\psi$',r'$b_1^M$ straight',r'GDP gain (\%)',r'Disaster gain (\%)',r'Gap (pp)'],
          [[cell(x['psi']),cell(x['estimates']['Straight']['one_msb'],4),
            cell(x['estimates']['GDP']['one_gain']),cell(x['estimates']['Disaster']['one_gain']),
            cell(x['estimates']['GDP']['one_gain']['mean']-x['estimates']['Disaster']['one_gain']['mean'])]
           for x in r['psi_sweep']])
    table('faces',[r'$d$',r'$b_S(d)$',r'$b_G(d)$',r'Gain (\%)',r'$PD_S$ (\%)',r'$PD_G$ (\%)'],
          [[cell(x['d']),cell(x['b_s'],4),cell(x['b_g'],4),cell(x['gain']),
            cell(x['pd_s'],1,100),cell(x['pd_g'],1,100)] for x in r['faces']])
    table('mu',[r'$\mu$',r'$b_1^M$ straight',r'GDP gain (\%)',r'Disaster gain (\%)'],
          [[cell(x['mu']),cell(x['estimates']['Straight']['one_msb'],4),
            cell(x['estimates']['GDP']['one_gain']),cell(x['estimates']['Disaster']['one_gain'])] for x in r['mu_sweep']])
    table('threshold',[r'Loss threshold',r'Trigger frequency (\%)',r'MSB gain (\%)'],
          [[cell(x['threshold'],0,100)+r'\%',cell(x['trigger'],2,100),cell(x['gain'])] for x in r['thresholds']])
    table('recovery',[r'$\varrho$',r'$b_1^M$ straight',r'GDP gain (\%)',r'Disaster gain (\%)'],
          [[cell(x['rho']),cell(x['estimates']['Straight']['b'],4),
            cell(x['estimates']['GDP']['gain']),cell(x['estimates']['Disaster']['gain'])] for x in r['recovery']])
    rows=[]
    for x in r['temperature']:
        for k,v in x['estimates'].items():
            rows.append(['Strong' if x['strong'] else 'Weak',k,cell(v['one_msb'],4),cell(v['one_gain'])])
    table('temperature',['Coupling','Contract',r'$b_1^M$',r'Gain (\%)'],rows)
    rows=[]
    for k,v in r['certain_event'].items():
        label='Event-only' if k=='Event-only' else ('Disaster loss' if k=='Disaster' else k)
        rows.append([label,cell(v['one_msb'],4),cell(v['pd'],2,100),cell(v['one_gain'])])
    table('certain',['Contract',r'$b_1^M$',r'$PD$ (\%)',r'Gain (\%)'],rows)
    rows=[]
    for x in r['haircuts']:
        if x['haircut'] not in [1,.5,0]:continue
        rows.append([x['rule'],cell(x['haircut']),*[cell(x['estimates'][k]['gain']) for k in ['Straight','GDP','Disaster']]])
    table('haircut',['Eligibility',r'$h_c$',r'Straight gain (\%)',r'GDP gain (\%)',r'Disaster gain (\%)'],rows)
    rows=[]
    for x in r.get('deferrals',[]):
        b=next(z for z in r['deferrals'] if z['nodes']==x['nodes'] and z['contract']=='Straight')['B0']
        stress_estimates=r['cases']['Stress']['estimates']
        forgiven=stress_estimates[x['contract']]['stationary_gain']['mean']
        gain=percent(x['B0'],b)
        rows.append([str(x['nodes']),x['contract'],cell(x['B0'],4),cell(gain),
                     '--' if x['contract']=='Straight' else cell(100*gain/forgiven),
                     f"{x['residual']:.1e}"])
    table('deferral',['Nodes/cell','Contract',r'$B(0)$',r'Gain (\%)',r'Retained (\%)','Residual'],rows)
    rows=[]
    for name,c in r['cases'].items():
        v=c['estimates']; bound=c['moments']['expected_g']*c['parameters']['alpha']/c['parameters']['rf']
        rows.append([name,cell(bound,4),*[cell(100*v[k]['one_msb']['mean']/bound) for k in ['Straight','GDP','Disaster']]])
    table('bound',['Case',r'$\alpha\mathbb E[g]/R_f$',r'Straight (\%)',r'GDP (\%)',r'Disaster (\%)'],rows)
    macros={}
    for prefix,name in [('Stress','Stress'),('Advanced','Advanced economy'),('Small','Disaster-prone small state')]:
        case=r['cases'][name]
        for contract in ['GDP','Disaster']:
            for metric,key in [('OneGain','one_gain'),('StationaryGain','stationary_gain'),('MSDGain','stationary_msd_gain')]:
                macros[prefix+contract+metric]=cell(case['estimates'][contract][key],1,se=False)
    for key,val in r['figure1'].items():
        if key=='d':continue
        macros['Fig'+''.join(w.title() for w in key.split('_'))]=cell(val,1 if 'mass' in key or 'default' in key else 5,100 if 'mass' in key or 'default' in key else 1)
    macros['NumSeeds']=str(r['config']['seeds'].__len__())
    macros['NumDraws']=f"{r['config']['n']:,}".replace(',',r'\,')
    if r.get('deferrals'):
        finest=max(z['nodes'] for z in r['deferrals'])
        rows=[z for z in r['deferrals'] if z['nodes']==finest]
        base=next(z['B0'] for z in rows if z['contract']=='Straight')
        for contract in ['GDP','Disaster']:
            value=next(z['B0'] for z in rows if z['contract']==contract)
            gain=percent(value,base)
            permanent=r['cases']['Stress']['estimates'][contract]['stationary_gain']['mean']
            macros['Deferral'+contract+'Gain']=cell(gain,1)
            macros['Deferral'+contract+'Retained']=cell(100*gain/permanent,1)
    (TEX/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')


if __name__=='__main__':main()

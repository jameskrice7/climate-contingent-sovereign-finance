"""Publication figures regenerated from model draws and results.json."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from .model import CASES, draw, payoff, at_face


def make_figures(r):
    out=Path(__file__).resolve().parents[1]/'paper'/'generated'
    plt.rcParams.update({'font.family':'serif','font.size':10,
                         'axes.spines.top':False,'axes.spines.right':False,
                         'savefig.bbox':'tight','pdf.fonttype':42})
    c=CASES[0];s=draw(c,r['config']['n'],42)
    blue,orange,green='#2767ae','#ce6a24','#228050'
    x=np.linspace(.25,1.35,1000);d=.13
    fig,axs=plt.subplots(2,1,figsize=(6.5,5.2),sharex=True,layout='constrained')
    axs[0].plot(x,c.alpha*x,color='black',label=r'Capacity $\alpha g$')
    axs[0].axhline(d,color=blue,label='Straight repayment')
    axs[0].plot(x,d*(1-c.kappa*(x<c.trigger)),color=orange,label='GDP clause')
    cuts=[.25,d*(1-c.kappa)/c.alpha,d/c.alpha,c.trigger]
    labels=['Default persists','Default avoided','Relief in survival states']
    for ax in axs:
        for a,b,col in zip(cuts[:-1],cuts[1:],['#eeeeee','#cfe7f6','#fbe0c9']):ax.axvspan(a,b,color=col,zorder=-1)
        ax.axvline(c.trigger,color='grey',ls=':',lw=1)
    axs[0].set_ylabel('Repayment / initial GDP');axs[0].legend(fontsize=8,loc='upper left')
    # KDE visualizes the same seed; reported probabilities use raw draws.
    grid=np.linspace(.25,1.35,400)
    density=gaussian_kde(s['g'][::max(1,len(s['g'])//30000)])(grid)
    axs[1].plot(grid,density,color=blue)
    axs[1].set(xlabel=r'Five-year growth factor $g$',ylabel='Density',xlim=(.25,1.35))
    for a,b,label in zip(cuts[:-1],cuts[1:],labels):
        axs[1].text((a+b)/2,.96,label,transform=axs[1].get_xaxis_transform(),
                    ha='center',va='top',fontsize=7,rotation=90 if b-a<.16 else 0)
    fig.savefig(out/'loading.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(7.0,3.0),layout='constrained')
    ds=np.linspace(0,.28,281)
    for k,col in [('Straight',blue),('GDP',orange),('Disaster',green)]:
        h=payoff(c,s,k);curves=[at_face(c,s,h,float(v)) for v in ds]
        axs[0].plot(ds,[v['b'] for v in curves],color=col,label=k)
        axs[1].plot(ds,[100*v['pd'] for v in curves],color=col)
    axs[0].set(xlabel='Face value / initial GDP',ylabel='Issuance proceeds');axs[0].legend(fontsize=8)
    axs[1].set(xlabel='Face value / initial GDP',ylabel='Default probability (%)')
    fig.savefig(out/'curves.pdf');plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(7.,3.),layout='constrained')
    for k,col in [('GDP',orange),('Disaster',green)]:
        axs[0].errorbar([v['psi'] for v in r['psi_sweep']],
            [v['estimates'][k]['one_gain']['mean'] for v in r['psi_sweep']],
            yerr=[1.96*v['estimates'][k]['one_gain']['se'] for v in r['psi_sweep']],
            color=col,marker='o',label=k,capsize=3)
    axs[0].set(xlabel=r'Logistics loading $\psi$',ylabel='One-period MSB gain (%)');axs[0].legend(fontsize=8)
    kk=r['kappa_sweep'];axs[1].errorbar([v['kappa'] for v in kk],[v['b']['mean'] for v in kk],
        yerr=[1.96*v['b']['se'] for v in kk],color=orange,capsize=2)
    axs[1].set(xlabel=r'Relief $\kappa$',ylabel='GDP-clause MSB')
    fig.savefig(out/'sensitivity.pdf');plt.close(fig)
    rr=r.get('deferrals',[])
    if rr:
        fig,ax=plt.subplots(figsize=(6.5,3),layout='constrained')
        nn=max(v['nodes'] for v in rr)
        for v,col in zip([v for v in rr if v['nodes']==nn],[blue,orange,green]):
            ax.plot(v['state'],v['borrowing'],color=col,label=v['contract'])
        ax.set(xlim=(0,.65),xlabel='Inherited face due next period / current GDP',ylabel='New borrowing capacity B(a)')
        ax.legend(fontsize=8);fig.savefig(out/'deferral_states.pdf');plt.close(fig)

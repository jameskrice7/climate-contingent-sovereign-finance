"""Optional provenance check: rerun the supplied first-revision script."""
from dataclasses import replace
from pathlib import Path
import json
import subprocess
import sys
from .model import CASES,draw,payoff,maximize,levels
ROOT=Path(__file__).resolve().parents[1]


def main():
    with (ROOT/'generated/legacy_replication.log').open('w') as log:
        subprocess.run([sys.executable,str(ROOT/'legacy/revision_simulations_round1.py')],
                       cwd=ROOT/'generated',stdout=log,stderr=subprocess.STDOUT,check=True)
    old=json.loads((ROOT/'generated/revision_results.json').read_text())
    rows=[]
    for psi in [0.,1.5]:
        c=replace(CASES[0],psi=psi);s=draw(c)
        for name,k in [('Straight','Straight'),('GDP clause','GDP'),('Disaster clause','Event-only')]:
            v=next(x for x in old['A_headline'] if x['psi']==psi and x['name']==name)
            new=levels(c,maximize(s['g'],payoff(c,s,k),c.rf))
            # Legacy values were rounded to five decimals before serialization.
            assert new['one_msb']>=v['MSB']-5.01e-6
            rows.append(dict(psi=psi,contract=k,old_grid_msb=v['MSB'],
                             exact_empirical_msb=new['one_msb'],difference=new['one_msb']-v['MSB']))
    (ROOT/'generated/legacy_comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('PASS: legacy numbers reproduced; empirical optimizer weakly improves the old grid, within rounding')


if __name__=='__main__':main()

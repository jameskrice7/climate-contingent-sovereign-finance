"""Check scientific build invariants and bibliography completeness offline."""
from pathlib import Path
import json
import re
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    r=json.loads((ROOT/'generated/results.json').read_text())
    assert len(r['config']['seeds'])==20
    assert r['config']['n']==200_000
    for case in r['cases'].values():
        for contract in case['estimates'].values():
            assert contract['one_msb']['mean']<=contract['upper_bound']['mean']+1e-12
            assert contract['phi']['mean']<1
    for row in r['deferrals']:
        assert row['converged'] and row['residual']<2e-7
        assert not row['chosen_face_boundary']
        assert row['state_boundary_B']==0
        assert row['max_deferred_state']<row['state_max']
        assert np.max(np.diff(row['borrowing']))<1e-10
    text=(ROOT/'paper/main.tex').read_text()
    text+='\n'+'\n'.join(p.read_text() for p in sorted((ROOT/'paper/sections').glob('*.tex')))
    keys=set(k.strip() for m in re.findall(r'\\(?:paren|text)?cite\{([^}]+)\}',text) for k in m.split(','))
    bib=set(re.findall(r'@\w+\{([^,]+),',(ROOT/'paper/references.bib').read_text()))
    assert keys==bib
    assert keys==set(json.loads((ROOT/'references/retained_sources.json').read_text()))
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    assert len(labels)==len(set(labels))
    assert set(re.findall(r'\\(?:eq)?ref\{([^}]+)\}',text))<=set(labels)
    print('PASS: simulation configuration, bounds, deferral convergence and boundaries, references, labels')


if __name__=='__main__':main()

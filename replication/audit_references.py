"""Refresh public bibliographic metadata; not part of the numerical build.

Raw Crossref responses are cached for offline review. Title matches are
diagnostics, never automatic evidence that a source supports a claim.
"""
from pathlib import Path
import concurrent.futures
import difflib
import json
import re
import requests
import bibtexparser

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'references'/'metadata'


def clean(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def retrieve(entry):
    fields = {k:v.value for k,v in entry.fields_dict.items()}
    title, doi = fields.get('title',''), fields.get('doi','')
    path = CACHE/(entry.key+'.json')
    if path.exists():
        return json.loads(path.read_text())
    record = dict(key=entry.key, original=fields)
    try:
        if doi:
            url = 'https://api.crossref.org/works/'+doi
            response = requests.get(url,timeout=40)
            record['lookup_url'] = url
            record['status_code'] = response.status_code
            msg = response.json().get('message',{}) if response.ok else {}
        else:
            url = 'https://api.crossref.org/works'
            response = requests.get(url,params={'query.title':title,'rows':3},timeout=40)
            record['lookup_url'] = response.url
            record['status_code'] = response.status_code
            items = response.json().get('message',{}).get('items',[]) if response.ok else []
            msg = max(items,key=lambda x:difflib.SequenceMatcher(None,clean(title),clean(' '.join(x.get('title',[])))).ratio()) if items else {}
        record['metadata'] = msg
        record['title_similarity'] = difflib.SequenceMatcher(None,clean(title),clean(' '.join(msg.get('title',[])))).ratio()
    except Exception as ex:
        record['error'] = str(ex)
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    return record


if __name__ == '__main__':
    CACHE.mkdir(parents=True,exist_ok=True)
    entries = bibtexparser.parse_file(str(ROOT/'legacy'/'references_round1.bib')).entries
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(retrieve,entries):
            print(r['key'],round(r.get('title_similarity',0),2),r.get('metadata',{}).get('DOI',''),flush=True)

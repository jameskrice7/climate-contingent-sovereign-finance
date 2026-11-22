"""Record a like-for-like length comparison with the archived first revision."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import pymupdf
ROOT=Path(__file__).resolve().parents[1]


def measure(path, original=False):
    doc=pymupdf.open(path)
    text='\n'.join(page.get_text(sort=True) for page in doc)
    refs=re.search(r'^References\s*$',text,re.M)
    if refs:
        if original:
            # The first revision prints its bibliography before its appendices.
            rest=text[refs.end():]
            end=re.search(r'A\s*\nFurther relaxations of the baseline assumptions',rest)
            if not end:
                end=re.search(r'Further relaxations of the baseline assumptions',rest)
            text=text[:refs.start()]+(rest[end.start():] if end else '')
        else:
            text=text[:refs.start()]
    return dict(pages=len(doc),
                approx_words_excluding_references=len(re.findall(
                    r"\b[^\W\d_]+(?:[-’'][^\W\d_]+)*\b",text)),
                pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--original',type=Path,default=ROOT/'legacy/main_round1.pdf')
    args=parser.parse_args()
    result=dict(original_source_commit='894faef',original=measure(args.original,True),
                revised=measure(ROOT/'paper/main.pdf'),
                method='Alphabetic PDF tokens; bibliography excluded; appendices, captions, and mathematical labels included. Approximate word counts. Both 11pt with one-inch margins.')
    (ROOT/'generated/length_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

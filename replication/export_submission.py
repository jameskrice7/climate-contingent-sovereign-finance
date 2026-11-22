"""Export the manuscript's exact current abstract as plain submission text."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]


def main():
    macros=dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]*)\}',
                          (ROOT/'paper/generated/numbers.tex').read_text()))
    tex=(ROOT/'paper/main.tex').read_text()
    abstract=tex.split('\\begin{abstract}',1)[1].split('\\end{abstract}',1)[0].strip()
    for key in sorted(macros,key=len,reverse=True):
        abstract=abstract.replace('\\'+key,macros[key])
    abstract=abstract.replace('\\ percent',' percent').replace('\\,','')
    if re.search(r'\\[A-Za-z]+',abstract):
        raise ValueError('Unexpanded TeX in submission abstract')
    (ROOT/'reviews/abstract_for_submission.txt').write_text(abstract+'\n')
    print('Exported matching ScholarOne abstract')


if __name__=='__main__':main()

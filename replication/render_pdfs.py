"""Render the paper and inspect page boundaries."""
from pathlib import Path
import argparse
import json
import tempfile
import pymupdf
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--outdir',type=Path)
    args=parser.parse_args()
    out=args.outdir or Path(tempfile.mkdtemp(prefix='sovereign-finance-qa-'))
    out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'paper/main.pdf'
    doc=pymupdf.open(source)
    thumbs=[];overflow=[]
    for i,page in enumerate(doc):
        target=out/f'page-{i+1:02}.png'
        page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(target)
        im=Image.open(target).convert('RGB');im.thumbnail((306,420))
        tile=Image.new('RGB',(326,450),'#dedede')
        tile.paste(im,((326-im.width)//2,10))
        ImageDraw.Draw(tile).text((10,432),f'Page {i+1}',fill='black')
        thumbs.append(tile)
        assert len(page.get_text().strip())>30,(source,i)
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if x0<40 or x1>page.rect.width-40 or y0<20 or y1>page.rect.height-20:
                        overflow.append(dict(page=i+1,text=span['text'],bbox=span['bbox']))
    for start in range(0,len(thumbs),9):
        group=thumbs[start:start+9]
        sheet=Image.new('RGB',(326*3,450*((len(group)+2)//3)),'white')
        for j,im in enumerate(group):sheet.paste(im,((j%3)*326,(j//3)*450))
        sheet.save(out/f'contact-{start//9+1}.png')
    report=dict(file='paper/main.pdf',pages=len(doc),edge_spans=overflow)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('Rendered pages:',out)


if __name__=='__main__':main()

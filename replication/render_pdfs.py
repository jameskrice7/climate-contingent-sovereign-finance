"""Render both deliverables and create contact sheets for visual QA."""
from pathlib import Path
import json
import pymupdf
from PIL import Image, ImageOps, ImageDraw
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'generated'/'qa';out.mkdir(exist_ok=True)
    reports=[]
    for source in [ROOT/'paper/main.pdf',ROOT/'reviews/response_round2.pdf']:
        doc=pymupdf.open(source)
        thumbs=[];overflow=[]
        for i,page in enumerate(doc):
            pix=page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3))
            target=out/(source.stem+f'-{i+1:02}.png');pix.save(target)
            im=Image.open(target).convert('RGB');im.thumbnail((306,420))
            tile=Image.new('RGB',(326,450),'#dedede');tile.paste(im,((326-im.width)//2,10))
            ImageDraw.Draw(tile).text((10,432),f'{source.stem} page {i+1}',fill='black')
            thumbs.append(tile)
            assert len(page.get_text().strip())>30,(source,i)
            for block in page.get_text('dict')['blocks']:
                if 'lines' not in block:continue
                for line in block['lines']:
                    for span in line['spans']:
                        x0,y0,x1,y1=span['bbox']
                        if x0 < 40 or x1 > page.rect.width-40 or y0<20 or y1>page.rect.height-20:
                            overflow.append(dict(page=i+1,text=span['text'],bbox=span['bbox']))
        for start in range(0,len(thumbs),9):
            group=thumbs[start:start+9]
            sheet=Image.new('RGB',(326*3,450*((len(group)+2)//3)),'white')
            for j,im in enumerate(group):sheet.paste(im,((j%3)*326,(j//3)*450))
            sheet.save(out/(source.stem+f'-contact-{start//9+1}.png'))
        reports.append(dict(file=str(source.relative_to(ROOT)),pages=len(doc),edge_spans=overflow))
    (out/'report.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()

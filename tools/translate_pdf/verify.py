"""Coverage, navigation, font and vector fidelity checks on the final PDFs."""
from pathlib import Path
import json,sys,re,hashlib,statistics
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import pymupdf as fitz
from PIL import Image,ImageChops,ImageStat
W=Path(__file__).resolve().parent
docs=json.loads((W/'inventory.json').read_text('utf-8'))
selection={int(x) for x in sys.argv[1:] if x.isdigit()}
def words(text):
 text=re.sub(r'([a-z])-\s+([a-z])',r'\1\2',text)
 return set(re.findall('[a-z]{3,}',text.lower()))
reports=[]
for d in docs:
 if selection and d['number'] not in selection:continue
 stem=f'{d["number"]:02d}_{d["slug"]}'
 path=W/'candidate'/(stem+'-zh.pdf')
 out=fitz.open(path);src=fitz.open(d['source'])
 meta=json.loads((W/(stem+'-validation.json')).read_text('utf-8'))
 placements=json.loads((W/(stem+'-placements.json')).read_text('utf-8'))
 assert len(out.get_toc())==d['source_pages']+3
 assert all(1<=row[2]<=len(out) for row in out.get_toc())
 links=[l for p in out for l in p.get_links()]
 assert all(0<=l['page']<len(out) for l in links if l['kind']==fitz.LINK_GOTO)
 toc=meta['nav']['toc']
 assert all(any(l['kind']==fitz.LINK_GOTO and l['page']==toc for l in p.get_links()) for p in out)
 expected_assets={a['id'] for a in d['assets'] if a['kind']!='callout'}
 actual_assets={x['asset']['id'] for x in placements if 'id' in x['asset']}
 assert actual_assets==expected_assets,(stem,'missing assets',expected_assets-actual_assets)
 # Math tokens are occurrence-specific, including identical expressions used at
 # different pages. No global translation cache is used for the source crop.
 inline_expected=sum(len(re.findall(r'ZXMATH\d{4}XZ',u['text'])) for u in d['units'] if u['role']!='figure-label')
 inline_actual=sum('id' not in x['asset'] for x in placements)
 formula_missing=[];missing_words=[];source_images=0
 for p in d['pages']:
  pi=p['page']-1;assets=[a for a in d['assets'] if a['page']==p['page']]
  us=[u for u in d['units'] if u['page']==p['page']]
  regions=[fitz.Rect(a['bbox']) for a in assets]+[fitz.Rect(m['bbox']) for u in us for m in u['maths'].values()]
  unitmap={u['id']:u for u in us}
  ordered=[]
  for e in p['elements']:
   if e['kind']=='text' and e['key'] in unitmap:
    text=unitmap[e['key']]['source']
    for token,m in unitmap[e['key']]['maths'].items():text=text.replace(token,m['text'])
    ordered.append(text)
   elif e['kind']=='code':ordered.append(e['text'])
   elif e['kind']=='asset':ordered.append(src[pi].get_text(clip=fitz.Rect(e['bbox'])))
  found=words(' '.join(ordered));expected=words(src[pi].get_text())
  # A word split across a hyphen and a line/column boundary is still covered by
  # its two fragments; reconstruct it from lines sharing a horizontal band.
  lines=[(l['bbox'],''.join(s['text'] for s in l['spans'])) for b in src[pi].get_text('dict')['blocks'] if b['type']==0 for l in b['lines']]
  for (rb,rt) in lines:
   if not rt.rstrip().endswith('-') or len(rt.strip())<4:continue
   for (nb,nt) in lines:
    if nt[:1].islower() and abs(nb[0]-rb[0])<30 and 0<=nb[1]-rb[3]<18:
     found|=words(rt[:-1]+nt)
  footer_words=words(' '.join(''.join(s['text'] for s in l['spans']) for b in src[pi].get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] if l['bbox'][1]>src[pi].rect.height*.9))
  translated_labels=words(' '.join(src[pi].get_text(clip=fitz.Rect(l['bbox'])) for a in assets if a['kind'] in ['callout','figure'] for l in a['labels']))
  missing=expected-found-footer_words-translated_labels-{'technmak'}
  if missing:missing_words.append(dict(source_page=p['page'],words=sorted(missing)))
  for b in src[pi].get_text('dict')['blocks']:
   if b['type']==1:
    source_images+=1
    mid=fitz.Rect(b['bbox']).tl+(fitz.Rect(b['bbox']).br-fitz.Rect(b['bbox']).tl)*.5
    assert any(fitz.Rect(a['bbox']).contains(mid) for a in assets),(stem,'lost source image',pi)
   if b['type']!=0:continue
   for line in b['lines']:
    for s in line['spans']:
     if ('Math' not in s['font'] and not s['font'].startswith('MS')) or not s['text'].strip():continue
     r=fitz.Rect(s['bbox']);mid=fitz.Point((r.x0+r.x1)/2,(r.y0+r.y1)/2)
     if r.width<.5 or r.height<.5:continue
     if not any(rr.intersects(r) or rr.contains(mid) for rr in regions):formula_missing.append(dict(source_page=pi+1,text=s['text'],bbox=list(r)))
 assert not formula_missing,(stem,'uncovered mathematical spans',formula_missing[:8])
 text='\n'.join(p.get_text() for p in out)
 assert not re.search(r'ZX(?:MATH|TERM|NAME)\d{4}XZ',text)
 assert '\ufffd' not in text
 fonts={font[3]:bool(out.extract_font(font[0])[3]) for p in out for font in p.get_fonts()}
 assert any('LXGW' in name and embedded for name,embedded in fonts.items())
 assert any('TimesNewRoman' in name and embedded for name,embedded in fonts.items())
 # Sample every displayed equation, plus inline expressions spread over the
 # source. Compare the rendered ink mass against the untouched original crop.
 checks=[];maths=[x for x in placements if x['asset'].get('kind')=='equation' or 'id' not in x['asset']]
 for x in maths:
  a=x['asset'];r=fitz.Rect(x['bbox']);sr=fitz.Rect(a['bbox'])
  if sr.width<3 or sr.height<3:continue
  factor=r.width/sr.width*2
  sp=src[a['page']-1].get_pixmap(matrix=fitz.Matrix(factor,factor),clip=sr,alpha=False,colorspace=fitz.csGRAY)
  op=out[x['page']].get_pixmap(matrix=fitz.Matrix(2,2),clip=r,alpha=False,colorspace=fitz.csGRAY)
  im1=Image.frombytes('L',[sp.width,sp.height],sp.samples)
  im2=Image.frombytes('L',[op.width,op.height],op.samples).resize(im1.size)
  ink1=255-ImageStat.Stat(im1).mean[0];ink2=255-ImageStat.Stat(im2).mean[0]
  if ink1>1 and r.width*r.height>40:checks.append(dict(source_page=a['page'],output_page=x['page']+1,bbox=list(r),ink_ratio=round(ink2/ink1,3)))
 report=dict(number=d['number'],source_pages=len(src),output_pages=len(out),source_images=source_images,
  vector_assets=len(expected_assets),inline_expected=inline_expected,inline_actual=inline_actual,
  uncovered_math_spans=formula_missing,word_coverage_flags=missing_words,
  outline_count=len(out.get_toc()),internal_links=sum(l['kind']==fitz.LINK_GOTO for l in links),
  fonts=fonts,formula_render_checks=len(checks),formula_render_flags=[x for x in checks if not .65<=x['ink_ratio']<=1.6],
  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 reports.append(report)
 (W/(stem+'-checks.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
 print(stem,len(out),'pages;',len(checks),'math render checks;',len(report['formula_render_flags']),'ink flags;',len(missing_words),'coverage flags',flush=True)
(W/'verification.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),'utf-8')

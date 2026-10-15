from pathlib import Path
import sys,json,re,html,csv,copy,hashlib,logging
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import pymupdf as fitz
from editorial import edit
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Flowable,Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];OUT=W/'candidate';OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('ZH','C:/Windows/Fonts/LXGWWenKai-Regular.ttf'))
pdfmetrics.registerFont(TTFont('EN','C:/Windows/Fonts/times.ttf'))
pdfmetrics.registerFont(TTFont('ENB','C:/Windows/Fonts/timesbd.ttf'))
PAGE_W,PAGE_H=595.276,841.89
ST={
 'body':ParagraphStyle('body',fontName='ZH',fontSize=10.5,leading=19,spaceAfter=9,wordWrap='CJK',textColor=colors.HexColor('#22323f')),
 'title':ParagraphStyle('title',fontName='ZH',fontSize=19,leading=28,spaceAfter=14,wordWrap='CJK',textColor=colors.HexColor('#173f63')),
 'heading':ParagraphStyle('heading',fontName='ZH',fontSize=12,leading=20,spaceBefore=8,spaceAfter=8,wordWrap='CJK',textColor=colors.HexColor('#173f63'),keepWithNext=True),
 'small':ParagraphStyle('small',fontName='ZH',fontSize=8.4,leading=13,spaceAfter=6,wordWrap='CJK',textColor=colors.HexColor('#607080')),
 'toc':ParagraphStyle('toc',fontName='ZH',fontSize=9.5,leading=16,spaceAfter=3,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='ZH',fontSize=9,leading=14,wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='EN',fontSize=9,leading=12,spaceAfter=9,wordWrap='LTR'),
}
TITLES={1:'检索增强生成与上下文工程',3:'理解 KV 缓存',4:'理解 FlashAttention',5:'理解 MHA、MQA、GQA 与 MLA',6:'GPU 利用率与性能手册',7:'GPU 内存层次结构',8:'混合专家模型（MoE）',9:'嵌入向量',10:'Transformer 块',11:'量化'}
CORRECTIONS={'挂钟时间':'实际耗时','挂钟':'实际运行','人头':'头','密集注意力':'稠密注意力','潜伏表示':'潜在表示','心理模型':'理解框架','精神模型':'理解框架','心智模型':'理解框架','正向传递':'前向传播','反向传递':'反向传播','操作员':'算子','国家住在哪里':'状态存放在哪里','量化量表':'量化缩放因子','低等级':'低秩','簿记':'管理开销','磁头':'头','建筑学':'架构','发行版':'分布','扭曲组':'线程束组','世代':'代际'}
inventory=json.loads((W/'inventory.json').read_text('utf-8'))
units={u['id']:u for d in inventory for u in d['units']}
source_docs={d['source']:fitz.open(d['source']) for d in inventory}
overrides=json.loads((W/'overrides-by-source.json').read_text('utf-8')) if (W/'overrides-by-source.json').exists() else {}
blank=W/'transparent.png'
if not blank.exists():Image.new('RGBA',(2,2),(255,255,255,0)).save(blank)
def markup(text,bold=False):
 text=text.replace('\x00','')
 return ''.join('<font name="'+('ENB' if bold else 'EN')+'">'+html.escape(x)+'</font>' if re.fullmatch(r'[\x20-\x7e]+',x) else html.escape(x) for x in re.split(r'([\x20-\x7e]+)',text) if x)
def translated(key,short=False):
 u=units[key]
 zh=overrides.get(u['source'])
 if zh is None:zh=json.loads((W/'cache'/(u['key']+'.json')).read_text('utf-8'))['zh']
 zh=edit(u,zh,short=short)
 if re.search(r'ZX(?:TERM|NAME)\d{4}XZ',zh):raise ValueError('Unresolved terminology '+key+' '+repr(zh)+' '+repr(u['terms']))
 return zh
MATHS={}
def paragraph(key,role='body',text=None):
 u=units[key];text=translated(key) if text is None else text;bits=[];max_height=0;math_labels=[]
 for part in re.split(r'(ZXMATH\d{4}XZ)',text):
  if part in u['maths']:
   m=u['maths'][part];r=fitz.Rect(m['bbox']);factor=1.04
   width,height=r.width*factor,r.height*factor
   max_height=max(max_height,height)
   label=key+part;MATHS[label]=dict(**m,width=width,height=height,kind='inline')
   math_labels.append(label)
   bits.append(f'<img src="{blank.as_posix()}" width="{width:.4f}" height="{height:.4f}" valign="-2.2"/>')
  else:bits.append(markup(part.strip(' '),role in ['title','heading']))
 style=ST.get(role,ST['body'])
 if max_height+3>style.leading:style=ParagraphStyle('math-'+role,parent=style,leading=max_height+3)
 p=Paragraph(''.join(bits).replace('\n','<br/>'),style);p.unit_key=key
 for frag,label in zip([f for f in p.frags if hasattr(f,'cbDefn') and f.cbDefn.kind=='img'],math_labels):
  # A single inline image owns both its width and its final drawing location.
  # The object replacement character avoids ReportLab's empty CJK-fragment bug.
  frag.text='\ufffc';frag.cbDefn.image=ImageReader(str(blank));frag.cbDefn.image.vector_label=label
 return p

class Vector(Flowable):
 def __init__(self,asset):
  Flowable.__init__(self);self.asset=asset
  r=fitz.Rect(asset['bbox'])
  self.factor=min(1.14,495/r.width,460/r.height)
  self.width=r.width*self.factor;self.height=r.height*self.factor;self.hAlign='CENTER';self.spaceAfter=10;self.spaceBefore=3
 def draw(self):
  x,y=self.canv.absolutePosition(0,0)
  self.canv.vector_placements.append(dict(asset=self.asset,page=self.canv.getPageNumber()-1,bbox=[x,PAGE_H-y-self.height,x+self.width,PAGE_H-y]))

class Book(SimpleDocTemplate):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.targets={};self.placements=[]
 def afterFlowable(self,f):
  if hasattr(f,'anchor'):self.canv.bookmarkPage(f.anchor);self.targets[f.anchor]=self.page-1
def heading(text,anchor=None):
 p=Paragraph(markup(text),ST['title'])
 if anchor:p.anchor=anchor
 return p
def footer(c,doc):
 c.vector_placements=doc.placements
 if not hasattr(c,'base_draw_image'):c.base_draw_image=c.drawImage
 def draw_image(image,x,y,width=None,height=None,*args,**kwargs):
  if hasattr(image,'vector_label'):
   m=MATHS[image.vector_label];x,y=c.absolutePosition(x,y)
   doc.placements.append(dict(asset=m,page=c.getPageNumber()-1,bbox=[x,PAGE_H-y-height,x+width,PAGE_H-y]))
   return
  return c.base_draw_image(image,x,y,width,height,*args,**kwargs)
 c.drawImage=draw_image
 c.saveState();c.setStrokeColor(colors.HexColor('#c8d6df'));c.line(48,42,PAGE_W-48,42)
 c.setFont('ZH',8);c.setFillColor(colors.HexColor('#617b8d'));c.drawString(48,29,doc.book_title)
 c.drawRightString(PAGE_W-66,29,'返回目录');c.linkAbsolute('返回目录','toc',Rect=(PAGE_W-132,25,PAGE_W-61,39),thickness=0)
 c.setFont('EN',8);c.drawRightString(PAGE_W-48,29,str(doc.page));c.restoreState()

def story(d,nav):
 a={a['id']:a for a in d['assets']};result=[]
 result.extend([heading(TITLES[d['number']],'cover'),Paragraph(markup(d['title']),ST['heading']),
  Paragraph(markup('中文修订版 · 图表与公式随文排版'),ST['heading']),
  Paragraph(markup('原作者：@techNmak · Understanding AI 系列 · https://x.com/techNmak'),ST['small']),
  Paragraph(markup('本版逐段翻译正文、标题、图注和表格，在对应位置保留原始图片与数学公式；图中自然语言标签译为中文。行内公式和独立公式沿用原稿矢量内容，不改写符号、上下标或数值。代码标识符及可执行字符串保留。'),ST['body']),
  Paragraph(markup('中文使用霞鹜文楷（LXGW WenKai），英文和数字使用 Times New Roman。术语括注英文原词。原稿资料与历史陈述按作者原文翻译，不代表重新核查外部资料的最新状态。'),ST['body']),PageBreak(),heading('专业术语翻译对照表','glossary')])
 rows=[[Paragraph(markup(x),ST['cell']) for x in ['英文原词','中文译名','缩写／符号']]]
 for t in d['glossary']:rows.append([Paragraph(markup(t[k]),ST['cell']) for k in ['en','zh','abbr']])
 table=Table(rows,colWidths=[205,215,75],repeatRows=1,hAlign='LEFT')
 table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eef4')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c5d4df')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
 result.extend([table,PageBreak(),heading('目录导航','toc')])
 for anchor,label in [('cover','封面与说明'),('glossary','专业术语翻译对照表')]+[(f'page_{p["page"]}',p['title_zh']) for p in d['pages']]:
  result.append(Paragraph(f'<link href="#{anchor}" color="#173f63">'+markup(label+f' · 第 {nav.get(anchor,0)+1} 页')+'</link>',ST['toc']))
 for p in d['pages']:
  ph=paragraph(p['heading_key'],'title') if p.get('heading_key') else heading(p['title_zh'])
  ph.anchor=f'page_{p["page"]}'
  result.extend([PageBreak(),ph,Paragraph(markup(f'对应原稿第 {p["page"]} 页'),ST['small'])])
  for e in p['elements']:
   if e['kind']=='asset':
    asset=a[e['id']]
    if asset['kind']=='callout':
     box=Table([[paragraph(asset['labels'][0]['key'])]],colWidths=[483],hAlign='LEFT')
     box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f0f0')),('BOX',(0,0),(-1,-1),.3,colors.HexColor('#c5ccd2')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
     box.spaceAfter=10;result.append(box);continue
    result.append(Vector(asset))
    for label in asset.get('labels',[]):
     if label.get('mixed_math') or label.get('legend_only'):
      result.append(paragraph(label['key'],'small'))
   elif e['kind']=='code':
    # Preserve code identity and indentation; natural-language comments get a translated note.
    code=e['text']
    if not re.search(r'https?|arxiv|\.org|\.html',code):
     source_page=source_docs[d['source']][p['page']-1]
     mono=[l for b in source_page.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] if all('Mono' in s['font'] or not s['text'].strip() for s in l['spans'])]
     if mono:
      x0=min(l['bbox'][0] for l in mono)
      selected=[l for l in mono if fitz.Rect(e['bbox']).contains(fitz.Point((l['bbox'][0]+l['bbox'][2])/2,(l['bbox'][1]+l['bbox'][3])/2))]
      code='\n'.join(' '*max(0,round((l['bbox'][0]-x0)/(l['spans'][0]['size']*.525)))+''.join(s['text'] for s in l['spans']) for l in selected) or code
    result.append(Preformatted(code,ST['code'],maxLineLength=95))
    for comment in e.get('comments',[]):result.append(paragraph(comment,'small'))
   else:
    text=translated(e['key'])
    if p.get('skip_title_key')==e['key']:continue
    result.append(paragraph(e['key'],e['role'] if e['role'] in ['title','heading'] else 'small' if e['role']=='reference-anchor' else 'body'))
    original=units[e['key']]['source']
    if (re.match(r'^\[\d+\]',original) and ('参考文献' in p['title_zh'] or p['page']>=d['source_pages']-1)) or (d['number']==1 and e['key'] in ['d01p008u0049','d01p008u0050','d01p008u0051']):
     result.append(paragraph(e['key'],'small',text='原题名与书目信息：'+original))
 return result

def translated_asset(asset,doc):
 clip=fitz.Rect(asset['bbox']);tmp=fitz.open();p=tmp.new_page(width=clip.width,height=clip.height)
 p.show_pdf_page(p.rect,doc,asset['page']-1,clip=clip)
 if asset['kind']!='figure' or not asset['labels']:return tmp
 edits=[]
 # Apply redactions only to natural-language labels; vector paths and images stay intact.
 for label in asset['labels']:
  unit=units[label['key']];original=unit['source']
  if asset.get('legend_only'):label['legend_only']=True
  if not re.search(r'[A-Za-z]{3}',original):continue
  if label.get('mixed_math') or label.get('legend_only'):continue
  r=fitz.Rect(label['bbox']);r=fitz.Rect(r.x0-clip.x0,r.y0-clip.y0,r.x1-clip.x0,r.y1-clip.y0)
  p.add_redact_annot(r,fill=False)
  edits.append((label,r))
 p.apply_redactions(images=0,graphics=0)
 font_archive=fitz.Archive('C:/Windows/Fonts')
 css='''@font-face{font-family:zh;src:url(LXGWWenKai-Regular.ttf)}@font-face{font-family:en;src:url(times.ttf)}*{margin:0;padding:0}body{font-family:zh;color:#111}.en{font-family:en}'''
 for label,r in edits:
  text=translated(label['key'],short=True)
  # Protect original mathematical glyphs in mixed labels by retaining their source crop.
  if 'ZXMATH' in text:raise ValueError('Unexpected inline math in label')
  value=''.join('<span class="en">'+html.escape(x)+'</span>' if re.fullmatch(r'[\x20-\x7e]+',x) else html.escape(x) for x in re.split(r'([\x20-\x7e]+)',text) if x)
  size=min(11,max(8,label['font_size']))
  r.y0=max(0,r.y0-.5);r.y1=min(p.rect.height,r.y1+1.5);r.x1=min(p.rect.width,r.x1+1)
  spare,scale=p.insert_htmlbox(r,f'<div style="font-size:{size}px;line-height:1.05">{value}</div>',css=css,archive=font_archive,scale_low=.9)
  label['render_scale']=scale
  if spare<0:
   label['legend_only']=True
   return translated_asset(asset,doc)
 return tmp

def build(d):
 assets={a['id']:a for a in d['assets']}
 label_font=fitz.Font(fontfile='C:/Windows/Fonts/LXGWWenKai-Regular.ttf')
 for asset in d['assets']:
  for label in asset['labels']:
   text=translated(label['key'],short=True);r=fitz.Rect(label['bbox'])
   label['legend_only']=label_font.text_length(text,fontsize=min(11,max(8,label['font_size'])))>r.width*1.05 or r.height<8
 # Finalise label placement before pagination so every fallback has a legend.
 prepared_assets={a['id']:translated_asset(a,source_docs[d['source']]) for a in d['assets'] if a['kind']!='callout'}
 for p in d['pages']:
  text_elements=[e for e in p['elements'] if e['kind']=='text']
  if p['page']==1:p['title_zh']=TITLES[d['number']]
  else:
   candidates=[e for e in text_elements if e['role']=='title']
   e=candidates[0] if candidates else text_elements[0] if text_elements else None
   p['title_zh']=translated(e['key']) if e else f'第 {p["page"]} 节'
   p['title_zh']=re.sub(r'ZXMATH\d{4}XZ','（公式）',p['title_zh'])
   if e:p['skip_title_key']=p['heading_key']=e['key']
 stem=f'{d["number"]:02d}_{d["slug"]}';nav={};base=W/(stem+'-base.pdf')
 for attempt in range(4):
  book=Book(str(base),pagesize=(PAGE_W,PAGE_H),leftMargin=50,rightMargin=50,topMargin=48,bottomMargin=57,title=TITLES[d['number']],author='@techNmak');book.book_title=TITLES[d['number']]
  book.build(story(d,nav),onFirstPage=footer,onLaterPages=footer)
  if nav==book.targets:break
  nav=dict(book.targets)
 else:raise ValueError('TOC did not converge')
 target=fitz.open(base);counts=Counter()
 for placement in book.placements:
  asset=placement['asset'];r=fitz.Rect(placement['bbox'])
  assert r.x0>=45 and r.x1<=PAGE_W-44 and r.y0>=42 and r.y1<=PAGE_H-45,(stem,placement)
  if 'id' in asset:
   aid=asset['id']
   if aid not in prepared_assets:prepared_assets[aid]=translated_asset(asset,source_docs[d['source']])
   target[placement['page']].show_pdf_page(r,prepared_assets[aid],0)
   counts[asset['kind']]+=1
  else:
   target[placement['page']].show_pdf_page(r,source_docs[asset['source']],asset['page']-1,clip=fitz.Rect(asset['bbox']))
   counts['inline']+=1
 target.set_toc([[1,'封面与说明',nav['cover']+1],[1,'专业术语翻译对照表',nav['glossary']+1],[1,'目录导航',nav['toc']+1]]+[[1,p['title_zh'],nav[f'page_{p["page"]}']+1] for p in d['pages']])
 target.set_pagemode('UseOutlines')
 final=OUT/(stem+'-zh.pdf');target.save(final,garbage=4,deflate=True)
 target.subset_fonts()
 target.save(final,garbage=4,deflate=True,clean=True,use_objstms=1)
 with (OUT/(stem+'-terminology-zh.csv')).open('w',encoding='utf-8-sig',newline='') as f:
  cw=csv.writer(f);cw.writerow(['英文原词','中文译名','缩写／符号']);cw.writerows([[t[k] for k in ['en','zh','abbr']] for t in d['glossary']])
 report=dict(number=d['number'],source_pages=d['source_pages'],translated_pages=len(target),path=str(final),nav=nav,placements=dict(counts),unit_count=len(d['units']),figure_label_scales=[l.get('render_scale') for a in d['assets'] for l in a['labels']])
 (W/(stem+'-validation.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
 (W/(stem+'-placements.json')).write_text(json.dumps(book.placements,ensure_ascii=False,indent=2),'utf-8')
 qa=W/'qa'/stem;qa.mkdir(parents=True,exist_ok=True)
 for start in range(0,len(target),12):
  sheet=Image.new('RGB',(1200,3*425),'#dbe3e8')
  for idx in range(start,min(start+12,len(target))):
   pix=target[idx].get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
   ImageDraw.Draw(im).text((4,4),str(idx+1),fill='red');sheet.paste(im,((idx-start)%4*300,(idx-start)//4*425))
  sheet.save(qa/f'{start+1:03d}.jpg')
 for idx in [nav['toc'],nav.get('page_5',0),nav.get('page_10',0)]:
  target[idx].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(qa/f'detail-{idx+1:03d}.png')
 print(stem,'->',len(target),'pages;',dict(counts),flush=True)
 return report

from collections import Counter
if __name__=='__main__':
 selection={int(x) for x in sys.argv[1:] if x.isdigit()}
 results=[]
 for d in inventory:
  if not selection or d['number'] in selection:results.append(build(d))
 old=json.loads((W/'built.json').read_text('utf-8')) if (W/'built.json').exists() else []
 (W/'built.json').write_text(json.dumps([r for r in old if r['number'] not in {x['number'] for x in results}]+results,ensure_ascii=False,indent=2),'utf-8')

from pathlib import Path
import sys,json,re,hashlib
from collections import Counter
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import pymupdf as fitz
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
manifest=json.loads((ROOT/'work/pdf-series/manifest.json').read_text('utf-8'))
glossary={}
for name in [ROOT/'work/glossary.txt',ROOT/'work/pdf-series/extra_terms.txt']:
 for line in name.read_text('utf-8').splitlines():
  en,zh,abbr=line.split('|')
  glossary[en]=dict(en=en,zh=zh,abbr=abbr)
for en,zh,abbr in [('Prefix Caching','前缀缓存',''),('PagedAttention','分页注意力',''),('Offloading','卸载',''),('Eviction','逐出',''),('Layer State','层状态',''),('Tensor Payload','张量有效载荷',''),('Block Table','块表',''),('Block Sharing','块共享',''),('Low-rank','低秩',''),('Uptraining','追加训练',''),('Cache Key','缓存键',''),('cache_salt','缓存盐值',''),('Dtype','数据类型',''),('Decode','解码',''),('MHA','多头注意力','MHA'),('MQA','多查询注意力','MQA'),('GQA','分组查询注意力','GQA'),('MLA','多头潜在注意力','MLA'),('RoPE','旋转位置嵌入','RoPE'),('FLOPs','浮点运算次数',''),('FLOPS','每秒浮点运算次数','')]:
 glossary[en]=dict(en=en,zh=zh,abbr=abbr)
patterns=[]
for t in sorted(glossary.values(),key=lambda t:-len(t['en'])):
 if t['en'] in ['Mean','Key','Value']:continue
 flags=0 if t['en'] in ['FLOPs','FLOPS'] else re.I
 patterns.append((re.compile(r'(?<![A-Za-z])'+re.escape(t['en'])+r'(?![A-Za-z])',flags),t))

def bbox_union(rects):
 result=fitz.Rect()
 for r in rects:result|=fitz.Rect(r)
 return result
def text_of(lines):return '\n'.join(''.join(s['text'] for s in l['spans']) for l in lines)
def natural(text):return re.findall(r'[A-Za-z]{3,}',text)
def protect_inline(lines,source,page):
 maths={};parts=[]
 size=max(s['size'] for l in lines for s in l['spans'])
 for l in lines:
  ls=l['spans'];base=max((s['size'] for s in ls if 'Roman' in s['font']),default=size)
  flags=['Math' in s['font'] or s['font'].startswith('MS') or (s['size']<base*.84 and re.search(r'[A-Za-z0-9]',s['text'])) for s in ls]
  for si,s in enumerate(ls):
   if not flags[si] and not re.search(r'[A-Za-z]{2,}',s['text']) and s['text'].strip() and (si>0 and flags[si-1] or si+1<len(ls) and flags[si+1]):flags[si]=True
  run=[];chunks=[]
  def finish():
   if not run:return
   token=f'ZXMATH{len(maths):04d}XZ'
   maths[token]=dict(bbox=list(bbox_union([s['bbox'] for s in run])+(-.3,-.3,.3,.3)),text=''.join(s['text'] for s in run),source=source,page=page)
   chunks.append(token);run.clear()
  for s,flag in zip(ls,flags):
   if flag:run.append(s)
   else:finish();chunks.append(s['text'])
  finish();parts.append(''.join(chunks))
 return re.sub(r'([a-z])-\s+([a-z])',r'\1\2',' '.join(parts)),maths
def mathematical(line):
 spans=line['spans'];text=text_of([line]).strip()
 hasmath=any('Math' in s['font'] or s['font'].startswith('MS') for s in spans)
 roman=' '.join(s['text'] for s in spans if 'Math' not in s['font'])
 words=[w for w in natural(roman) if w.lower() not in ['softmax','var','exp','log','max','min','sum','relu','silu','gelu','rms','norm','sin','cos','rmsnorm','layernorm','swiglu','ffn','mlp','attn','attention','moe','topk','keeptopk','softplus','importance','concat','head','sublayer','gate','prenorm','postnorm','diag','clamp','round','dot','sim','model','out','bytes','gib','mib','kib']]
 return (hasmath and not words) or bool(re.fullmatch(r'(?:softmax|exp|log|Var|max|min)',text)) or (not natural(text) and bool(text) and not re.fullmatch(r'\d+[.)]?',text))

all_units=[];docs=[]
for item in manifest:
 if item['status']!='downloaded' or item['number']==2:continue
 src=fitz.open(item['path']);pages=[];used={};assets=[];units=[]
 def addunit(text,role,page,maths=None):
  protected=text;restores={}
  for i,term in enumerate(patterns):
   pattern,t=term
   if pattern.search(protected):
    key=f'ZXTERM{i:04d}XZ';adapted=dict(t)
    if t['en']=='Precision':adapted['zh']='精确率' if item['number']==1 else '精度'
    protected=pattern.sub(key,protected)
    restores[key]=adapted;used[t['en']]=adapted
  # Technical identifiers, source author names, citations and URLs are not translated.
  namepattern=r'https?://\S+|arXiv:\s*[\d.]+|@[A-Za-z0-9_]+|\b(?:vLLM|FlashAttention(?:-[234])?|TensorRT-LLM|DeepSeek(?:-V[23])?|KVQuant|CUDA|PyTorch|NVIDIA|AMD|FP(?:8|16|32|64)|BF16|INT[248]|HBM[23Ee]*|SRAM|DRAM|GEMM|SM[0-9]*|GPU|CPU)\b'
  annotations=list(restores.values())
  # Translate natural sentences before adding terminology annotations. Replacing
  # everyday nouns with opaque tokens damages syntactic context in MT engines.
  protected=text
  names=[]
  def protect_name(match):
   key=f'ZXNAME{len(names):04d}XZ';names.append((key,match.group()));return key
  protected=re.sub(namepattern+r'|\b(?:LLMs?|RAG|ANN|NMT|SLO|RAPTOR|HyDE|RRF|MoE|FFN|SwiGLU|GELU|ReLU|RMSNorm|LayerNorm|SDPA|GQA|MQA|MHA|MLA|API|PCIe|NVLink|NVSHMEM|PTX|SASS|CUTLASS|TF32|MXFP4|NVFP4|TTFT|TPOT|ITL|SMs|WGMMA|TMA|CTA|CTAs|SIMT|SIMD|LRU|MPS|MIG|NCCL|LDS|WMMA|LSE)\b',protect_name,protected)
  author=re.match(r'^(\[\d+\]\s*)(.+?et al\.)',protected)
  if author:
   key=f'ZXNAME{len(names):04d}XZ';names.append((key,author.group(2)));protected=author.group(1)+key+protected[author.end():]
  restores={}
  for key,name in names:restores[key]=dict(en=name,zh=name,abbr='',literal=True)
  key=hashlib.sha256(('natural-v2:'+protected).encode()).hexdigest()
  uid=f'd{item["number"]:02d}p{page:03d}u{len(units):04d}'
  unit=dict(id=uid,key=key,text=protected,source=text,role=role,page=page,document=item['number'],terms=restores,annotations=annotations,maths=maths or {})
  units.append(unit);return uid
 for pi,p in enumerate(src):
  raw=[b for b in p.get_text('dict')['blocks'] if b['type']==0]
  # Join a word split across PDF text blocks before translating the paragraph.
  merged=[]
  for b in raw:
   if merged and text_of(merged[-1]['lines']).rstrip().endswith('-') and b['bbox'][1]-merged[-1]['bbox'][3]<10 and abs(b['bbox'][0]-merged[-1]['bbox'][0])<12:
    merged[-1]['lines']+=b['lines'];merged[-1]['bbox']=tuple(bbox_union([merged[-1]['bbox'],b['bbox']]))
   else:merged.append(b)
  raw=merged
  # Cluster visible vector drawings. Running rules at page top/bottom are decoration.
  drawings=[];all_drawings=p.get_drawings();rules={}
  for draw in all_drawings:
   r=fitz.Rect(draw['rect'])
   if r.width>70 and r.height<.5 and 110<r.y0<p.rect.height*.89:
    rk=(round(r.x0/3),round(r.x1/3));rules.setdefault(rk,[]).append(r)
   if r.is_empty or r.width<1 or r.height<1:continue
   if r.y0<100 and r.width>p.rect.width*.65:continue
   if r.y0>p.rect.height*.9:continue
   drawings.append(draw)
  regions=[fitz.Rect(r) for r in p.cluster_drawings(drawings=drawings,x_tolerance=12,y_tolerance=12)] if drawings else []
  regions=[r for r in regions if r.width>15 and r.height>12]
  for rr in rules.values():
   rr.sort(key=lambda x:x.y0)
   if len(rr)>=3 and rr[-1].y0-rr[0].y0<320:
    regions.append(fitz.Rect(rr[0].x0,rr[0].y0-2,rr[0].x1,rr[-1].y0+2))
  # Fraction rules can have English numerator/denominator labels. Retain the
  # complete fraction, rather than flattening its two baselines into prose.
  for draw in all_drawings:
   r=fitz.Rect(draw['rect'])
   if r.width<12 or r.height>.5 or not 110<r.y0<p.rect.height*.89:continue
   near=[l for b in raw for l in b['lines'] if r.x0-3<(l['bbox'][0]+l['bbox'][2])/2<r.x1+3 and abs((l['bbox'][1]+l['bbox'][3])/2-r.y0)<16]
   if any(l['bbox'][3]<r.y0+1 for l in near) and any(l['bbox'][1]>r.y0-1 for l in near):
    regions.append(bbox_union([r]+[l['bbox'] for l in near])+(-1,-1,1,1))
  # Individual boxes in a diagram need one shared crop with their connecting labels.
  changed=True
  while changed:
   changed=False
   for i in range(len(regions)):
    for j in range(i+1,len(regions)):
     a,b=regions[i],regions[j]
     if (a+(-15,-12,15,12)).intersects(b):
      regions[i]=a|b;regions.pop(j);changed=True;break
    if changed:break
  image_rects=[fitz.Rect(b['bbox']) for b in p.get_text('dict')['blocks'] if b['type']==1]
  regions+=image_rects
  actual=[]
  for region in regions:
   # Include labels whose centre lies within the drawing. Do not absorb adjacent prose.
   selected=[l for b in raw for l in b['lines'] if region.contains(fitz.Point((l['bbox'][0]+l['bbox'][2])/2,(l['bbox'][1]+l['bbox'][3])/2))]
   region=bbox_union([region]+[l['bbox'] for l in selected])+(-2,-2,2,2)
   if region.width>p.rect.width*.9:region.x0=25;region.x1=p.rect.width-25
   actual.append(region&p.rect)
  elements=[];consumed=set()
  for ri,region in enumerate(actual):
   if region.is_empty:continue
   asset_id=f'd{item["number"]:02d}p{pi+1:03d}f{ri:02d}'
   local_draws=[dr for dr in all_drawings if region.contains(fitz.Rect(dr['rect'])) and fitz.Rect(dr['rect']).width>3]
   selected_lines=[l for b in raw for l in b['lines'] if region.contains(fitz.Point((l['bbox'][0]+l['bbox'][2])/2,(l['bbox'][1]+l['bbox'][3])/2))]
   # A filled explanatory text box is prose, rather than a technical diagram.
   # Read its complete line order instead of splitting labels at font changes.
   callout=(region.width>p.rect.width*.6 and 1<=len(local_draws)<=4 and all(dr['type'] in ['f','fs'] and dr['fill'] and min(dr['fill'])>.65 for dr in local_draws) and len(natural(text_of(selected_lines)))>=12 and not any(region.intersects(ir) for ir in image_rects))
   if callout:
    for bi,b in enumerate(raw):
     for li,l in enumerate(b['lines']):
      if l in selected_lines:consumed.add((bi,li))
    ordered=sorted(selected_lines,key=lambda l:(round(l['bbox'][1]/3),l['bbox'][0]))
    txt,maths=protect_inline(ordered,item['path'],pi+1)
    key=addunit(txt,'callout',pi+1,maths)
    assets.append(dict(id=asset_id,kind='callout',page=pi+1,bbox=list(region),labels=[dict(key=key,bbox=list(region),font_size=10,mixed_math=bool(maths))],source=item['path']))
    elements.append(dict(kind='asset',id=asset_id,bbox=list(region)))
    continue
   labels=[];label_runs=[]
   for bi,b in enumerate(raw):
    for li,l in enumerate(b['lines']):
     lr=fitz.Rect(l['bbox'])
     if region.contains(fitz.Point((lr.x0+lr.x1)/2,(lr.y0+lr.y1)/2)):
      consumed.add((bi,li));runs=[];run=[]
      for s in l['spans']:
       if s['text'].isspace() and s['bbox'][2]-s['bbox'][0]>7:
        if run:runs.append(run);run=[]
        continue
       if run and s['bbox'][0]-run[-1]['bbox'][2]>7:runs.append(run);run=[]
       run.append(s)
      if run:runs.append(run)
      for run in runs:
       txt=''.join(s['text'] for s in run).strip()
       if not natural(txt) or mathematical(dict(spans=run)):continue
       if all('Mono' in s['font'] for s in run):continue
       if re.fullmatch(r'(?:MHA|MQA|GQA|MLA|Q|K|V|KV|FP\d+|BF16|INT\d+)',txt):continue
       # Mixed mathematical labels retain all original glyphs and get a nearby translated legend.
       mixed=any('Math' in s['font'] for s in run);maths={}
       if mixed:
        parts=[];mathrun=[]
        flags=['Math' in s['font'] or (s['size']<max(x['size'] for x in run)*.84) for s in run]
        for si,s in enumerate(run):
         if not flags[si] and not re.search(r'[A-Za-z]{2,}',s['text']) and (si>0 and flags[si-1] or si+1<len(run) and flags[si+1]):flags[si]=True
        def finish_label_math():
         if not mathrun:return
         token=f'ZXMATH{len(maths):04d}XZ';maths[token]=dict(bbox=list(bbox_union([s['bbox'] for s in mathrun])+(-.3,-.3,.3,.3)),text=''.join(s['text'] for s in mathrun),source=item['path'],page=pi+1);parts.append(token);mathrun.clear()
        for s,flag in zip(run,flags):
         if flag:mathrun.append(s)
         else:finish_label_math();parts.append(s['text'])
        finish_label_math()
        txt=''.join(parts)
       label_runs.append(dict(text=txt,bbox=list(bbox_union([s['bbox'] for s in run])),font_size=max(s['size'] for s in run),mixed_math=mixed,maths=maths))
   joined=[]
   for lr in sorted(label_runs,key=lambda x:(round(x['bbox'][0]/4),x['bbox'][1])):
    match=next((old for old in reversed(joined) if abs(lr['bbox'][0]-old['bbox'][0])<3 and -.5<=lr['bbox'][1]-old['bbox'][3]<5 and not old['mixed_math'] and not lr['mixed_math'] and not any(old['bbox'][3]<rule.y0<lr['bbox'][1] for rr in rules.values() for rule in rr)),None)
    if match:
     match['text']=re.sub(r'([a-z])-$',r'\1',match['text'])+('' if match['text'].endswith('-') else ' ')+lr['text'];match['bbox']=list(bbox_union([match['bbox'],lr['bbox']]))
    else:joined.append(lr)
   for lr in joined:
    key=addunit(lr['text'],'figure-label',pi+1,lr['maths'])
    labels.append(dict(key=key,bbox=lr['bbox'],font_size=lr['font_size'],mixed_math=lr['mixed_math']))
   # A crop that cuts a text line, or a label that is only a word fragment,
   # cannot carry a redacted translation without corrupting the artwork.
   clipped=any(l['bbox'][3]>region.y1-1 and l['bbox'][1]<region.y1 for l in selected_lines)
   fragment=any(re.fullmatch(r'[a-z]{1,10}[-\s]?',next(u['text'] for u in units if u['id']==l['key'])) for l in labels)
   asset=dict(id=asset_id,kind='figure',page=pi+1,bbox=list(region),labels=labels,source=item['path'],legend_only=bool(clipped or fragment))
   assets.append(asset);elements.append(dict(kind='asset',id=asset_id,bbox=list(region)))
  math_lines=[]
  for bi,b in enumerate(raw):
   pending=[]
   def flush():
    if not pending:return
    lines=list(pending);pending.clear();rect=bbox_union([l['bbox'] for l in lines]);spans=[s for l in lines for s in l['spans']]
    text=text_of(lines).strip()
    if not text:return
    if re.fullmatch(r'\d+',text) and rect.y0>p.rect.height*.9:return
    if '@techNmak' in text and rect.y0>p.rect.height*.9:return
    if rect.y0>p.rect.height*.96:return
    role='text'
    size=max(s['size'] for s in spans)
    if size>14:role='title'
    elif all('Bold' in s['font'] or not s['text'].strip() for s in spans):role='heading'
    elif text.startswith('Research anchors:'):role='reference-anchor'
    elif all('Mono' in s['font'] or not s['text'].strip() for s in spans):role='code'
    maths={};parts=[]
    for l in lines:
     ls=l['spans'];base=max((s['size'] for s in ls if 'Roman' in s['font']),default=size)
     is_math=[('Math' in s['font'] or s['font'].startswith('MS') or (s['size']<base*.84 and re.search(r'[A-Za-z0-9]',s['text']))) for s in ls]
     for si,s in enumerate(ls):
      if not is_math[si] and not re.search(r'[A-Za-z]{2,}',s['text']) and s['text'].strip() and (si>0 and is_math[si-1] or si+1<len(ls) and is_math[si+1]):is_math[si]=True
     run=[];chunks=[]
     def finish_math():
      if not run:return
      rr=bbox_union([s['bbox'] for s in run])+(-.3,-.3,.3,.3)
      mid=f'ZXMATH{len(maths):04d}XZ';maths[mid]=dict(bbox=list(rr),text=''.join(s['text'] for s in run),source=item['path'],page=pi+1)
      chunks.append(mid);run.clear()
     for s,ism in zip(ls,is_math):
      if ism:run.append(s)
      else:finish_math();chunks.append(s['text'])
     finish_math();parts.append(''.join(chunks))
    protected=' '.join(parts)
    protected=re.sub(r'([a-z])-\s+([a-z])',r'\1\2',protected)
    if role=='code':
     comments=[]
     for cl in text.splitlines():
      cm=re.search(r'#\s*(.+)',cl)
      if cm and natural(cm[1]):comments.append(addunit(cm[1],'code-comment',pi+1))
     elements.append(dict(kind='code',text=text,bbox=list(rect),comments=comments));return
    key=addunit(protected,role,pi+1,maths)
    elements.append(dict(kind='text',key=key,role=role,bbox=list(rect)))
   for li,l in enumerate(b['lines']):
    if (bi,li) in consumed:flush();continue
    if mathematical(l):flush();math_lines.append(l);continue
    # A title line and its subtitle must be independent translation units.
    if pending:
     oldsize=max(s['size'] for s in pending[-1]['spans']);newsize=max(s['size'] for s in l['spans'])
     if max(oldsize,newsize)>14 and abs(oldsize-newsize)>2:flush()
    pending.append(l)
   flush()
  # Equation fragments with overlapping vertical extents belong to the same formula.
  math_lines.sort(key=lambda l:l['bbox'][1]);groups=[]
  for line in math_lines:
   rect=fitz.Rect(line['bbox'])
   if groups and rect.y0<=fitz.Rect(groups[-1]['bbox']).y1+3:
    groups[-1]['bbox']=list(fitz.Rect(groups[-1]['bbox'])|rect);groups[-1]['lines'].append(line)
   else:groups.append(dict(bbox=list(rect),lines=[line]))
  for mi,g in enumerate(groups):
   aid=f'd{item["number"]:02d}p{pi+1:03d}m{mi:02d}'
   r=fitz.Rect(g['bbox'])+(-1,-1,1,1);r&=p.rect
   assets.append(dict(id=aid,kind='equation',page=pi+1,bbox=list(r),labels=[],source=item['path']))
   elements.append(dict(kind='asset',id=aid,bbox=list(r)))
  elements.sort(key=lambda e:(round(e['bbox'][1]/3),e['bbox'][0]))
  pages.append(dict(page=pi+1,elements=elements))
 doc=dict(number=item['number'],slug=item['slug'],title=item['title'],source=item['path'],source_pages=len(src),pages=pages,assets=assets,glossary=list(used.values()),units=units)
 docs.append(doc);all_units+=units
 print(item['number'],len(src),'pages;',len(units),'text units;',Counter(a['kind'] for a in assets),flush=True)
(W/'inventory.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),'utf-8')
(W/'units.json').write_text(json.dumps(all_units,ensure_ascii=False,indent=2),'utf-8')
print('TOTAL',len(all_units),'units;',sum(len(d['assets']) for d in docs),'display formulas/figures')

from pathlib import Path
import json,re,urllib.request,urllib.parse,hashlib,concurrent.futures,time,sys,threading
W=Path(__file__).resolve().parent;cache=W/'cache';cache.mkdir(exist_ok=True)
units=json.loads((W/'units.json').read_text('utf-8'))
selection={int(x) for x in sys.argv[1:] if x.isdigit()}
if selection:units=[u for u in units if u['document'] in selection]
units=list({u['key']:u for u in units}.values())
pending=[u for u in units if not (cache/(u['key']+'.json')).exists()]
batches=[];batch=[];length=0
for u in pending:
 if length+len(u['text'])>2300 and batch:batches.append(batch);batch=[];length=0
 batch.append(u);length+=len(u['text'])+24
if batch:batches.append(batch)
lock=threading.Lock();count=0
def request(text):
 url='https://translate.googleapis.com/translate_a/single?'+urllib.parse.urlencode(dict(client='gtx',sl='en',tl='zh-CN',dt='t',q=text))
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=25) as r:obj=json.load(r)
 value=''.join(x[0] for x in obj[0] if x and x[0])
 return re.sub(r'ZX\s*(TERM|MATH|NAME|UNIT)\s*(\d{4})\s*XZ',lambda m:'ZX'+m[1].upper()+m[2]+'XZ',value,flags=re.I)
def check(u,zh):
 expected=set(re.findall(r'ZX(?:TERM|MATH|NAME)\d{4}XZ',u['text']))
 actual=set(re.findall(r'ZX(?:TERM|MATH|NAME)\d{4}XZ',zh))
 if expected!=actual:raise ValueError('Protected formulas/terms changed')
 if re.search(r'[\u4e00-\u9fff]',u['text']):raise ValueError('Unexpected Chinese source')
 return zh
def save(u,zh):
 global count
 (cache/(u['key']+'.json')).write_text(json.dumps(dict(source=u['text'],zh=zh),ensure_ascii=False),'utf-8')
 with lock:
  count+=1
  if count%60==0:print('Translated',count,'/',len(pending),'new units',flush=True)
def work(batch):
 text='\n\n'.join(f'ZXUNIT{i:04d}XZ\n'+u['text'] for i,u in enumerate(batch))
 try:
  zh=request(text)
  chunks=re.split(r'ZXUNIT(\d{4})XZ\s*',zh)
  values={int(chunks[i]):chunks[i+1].strip() for i in range(1,len(chunks)-1,2)}
  if set(values)!=set(range(len(batch))):raise ValueError('Unit boundary mismatch')
  for i,u in enumerate(batch):check(u,values[i])
  for i,u in enumerate(batch):save(u,values[i])
 except Exception:
  for u in batch:
   last=None
   for retry in range(2):
    try:zh=check(u,request(u['text']));save(u,zh);last=None;break
    except Exception as ex:last=ex;time.sleep(2+retry)
   if last:print('FAILED',u['document'],u['page'],u['key'],str(last),flush=True)
print(len(units),'unique units;',len(pending),'uncached;',len(batches),'batches',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(work,batches))
missing=[u for u in units if not (cache/(u['key']+'.json')).exists()]
(W/'missing-translations.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),'utf-8')
print('DONE; missing:',len(missing),flush=True)

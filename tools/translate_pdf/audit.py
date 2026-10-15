from pathlib import Path
import json,sys,re
from editorial import edit
W=Path(__file__).resolve().parent
docs=json.loads((W/'inventory.json').read_text('utf-8'))
selection={int(x) for x in sys.argv[1:] if x.isdigit()}
for d in docs:
 if selection and d['number'] not in selection:continue
 lines=[];missing=[]
 for p in d['pages']:
  lines.append('\n===== SOURCE PAGE '+str(p['page'])+' =====')
  for u in [u for u in d['units'] if u['page']==p['page']]:
   path=W/'cache'/(u['key']+'.json')
   if not path.exists():missing.append(u);continue
   text=json.loads(path.read_text('utf-8'))['zh']
   text=edit(u,text)
   for key,m in u['maths'].items():text=text.replace(key,'〔'+m['text']+'〕')
   lines.extend(['['+u['id']+'] '+u['source'],text])
 (W/(str(d['number']).zfill(2)+'-review.txt')).write_text('\n'.join(lines),'utf-8')
 print(d['number'],'missing:',len(missing),'code elements:',sum(e['kind']=='code' for p in d['pages'] for e in p['elements']))
 if missing:
  (W/(str(d['number']).zfill(2)+'-missing.json')).write_text(json.dumps(missing,ensure_ascii=False,indent=2),'utf-8')

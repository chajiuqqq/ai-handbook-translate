"""Assemble final PDFs, catalogs, ZIP and website assets from checked candidates."""
from pathlib import Path
import json,shutil,zipfile,html,re,datetime
import sys;sys.path.insert(0,str(Path(__file__).resolve().parent/'deps'))
import pymupdf as fitz
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
OUT=ROOT/'outputs/AI_Handbooks';ZH=OUT/'zh';ORIG=OUT/'originals';TERM=OUT/'terminology'
REPO=ROOT/'github/ai-handbook-translate';SITE=ROOT/'sites/ai-handbooks-zh/dist'
docs=json.loads((W/'inventory.json').read_text('utf-8'))
built={r['number']:r for r in json.loads((W/'built.json').read_text('utf-8'))}
checks={r['number']:r for r in json.loads((W/'verification.json').read_text('utf-8'))}
TITLES={1:'检索增强生成与上下文工程',2:'注意力机制',3:'理解 KV 缓存',4:'理解 FlashAttention',5:'理解 MHA、MQA、GQA 与 MLA',6:'GPU 利用率与性能手册',7:'GPU 内存层次结构',8:'混合专家模型（MoE）',9:'嵌入向量',10:'Transformer 块',11:'量化'}
EN={1:'RAG & Context Engineering',2:'How Attention Works',3:'Understanding KV Cache',4:'Understanding FlashAttention',5:'Understanding MHA, MQA, GQA & MLA',6:'GPU Utilization / Performance Handbook',7:'GPU Memory Hierarchy',8:'Mixture of Experts (MoE)',9:'Embeddings',10:'The Transformer Block',11:'Quantization'}
SLUG={1:'RAG_Context_Engineering',2:'How_Attention_Works',3:'Understanding_KV_Cache',4:'Understanding_FlashAttention',5:'MHA_MQA_GQA_MLA',6:'GPU_Utilization_Performance',7:'GPU_Memory_Hierarchy',8:'Mixture_of_Experts',9:'Embeddings',10:'Transformer_Block',11:'Quantization'}
DRIVE={1:'1-hwxsU1U0ghO4938kcTdnRQwl5CCtB6L',2:'1fCHQ5xCQJ6jZszAYf-qP3VIySbzFIEDv',3:'12KlRm0YLYrfpLF2q3_tBDNMMkJ7_bYNF',4:'1CLyK-9Cflcvi3fRl3qAHyzYvwJFjCyVg',5:'1A68bJm6_ctrEPolSRlkPzroTgT6EeEWX',6:'17tyvxr__8vZ6o995GNq6I5PC5JOiv0ql',7:'1r9evOyX5SgO2W76mn6plgcqv207MgTY8',8:'10uQYFdBboSNTDy7QZo9PtQKFcK2y_5fu',9:'129Hwx-jmuHwdRSOOOcJ6Owu4m02szL6c',10:'1UhSHccYXXCMnguk2fQWJPVve2n5xONvU',11:'1JPWFc9lArJ-viyqf4ZkXpxF-jhYNkK9q'}
for d in docs:
 n=d['number'];stem=f'{n:02d}_{d["slug"]}'
 if n!=2:
  shutil.copy2(W/'candidate'/(stem+'-zh.pdf'),ZH/(stem+'-zh.pdf'))
  shutil.copy2(W/'candidate'/(stem+'-terminology-zh.csv'),TERM/(stem+'-terminology-zh.csv'))
  checks[n]=json.loads((W/(stem+'-checks.json')).read_text('utf-8'))
report=dict(整理日期=datetime.date.today().isoformat(),说明='中文全文译本，原文图片与矢量公式随文保留；中文使用霞鹜文楷，英文与数字使用 Times New Roman。术语括注英文原词。',手册=[])
for n in range(1,12):
 stem=f'{n:02d}_{SLUG[n]}'
 pages=len(fitz.open(ZH/(stem+'-zh.pdf')))
 report['手册'].append(dict(编号=n,标题=TITLES[n],英文名=EN[n],slug=SLUG[n],原页数=next((d['source_pages'] for d in docs if d['number']==n),33),译页数=pages,术语表=f'terminology/{stem}-terminology-zh.csv',中文PDF=f'zh/{stem}-zh.pdf',原文PDF=f'originals/{stem}.pdf',来源=f'https://drive.google.com/file/d/{DRIVE[n]}/view'))
 (OUT/'00_文件清单.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
md=['# AI 技术手册中文译本总目录','',f"整理日期：{report['整理日期']}",'',report['说明'],'','| 编号 | 文档 | 原文页 | 译本页 | 文件 |','|---|---:|---:|---:|---|']
for m in report['手册']:md.append(f"| {m['编号']:02d} | {m['标题']} | {m['原页数']} | {m['译页数']} | [中文 PDF]({m['中文PDF']}) · [术语表]({m['术语表']}) |")
md+=['','第 12、13 份的原文链接需要 Google 登录，按要求暂时跳过。','','原文作者：[@techNmak](https://x.com/techNmak) · Understanding AI 系列']
(OUT/'00_总目录.md').write_text('\n'.join(md),'utf-8')
rows=''.join(f'''<tr><td>{m['编号']:02d}</td><td><b>{html.escape(m['标题'])}</b><small>{html.escape(m['英文名'])}</small></td><td>已翻译 · 图表与公式随文</td><td>{m['原页数']}</td><td>{m['译页数']}</td><td class="links"><a href="{m['中文PDF']}">中文 PDF</a> <a href="{m['原文PDF']}">原文 PDF</a> <a href="{m['术语表']}">术语表 CSV</a> <a href="{m['来源']}">在线来源</a></td></tr>''' for m in report['手册'])
index=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 技术手册中文译本总目录</title>
<style>body{{font-family:"Times New Roman","LXGW WenKai",serif;background:#f3f6f9;color:#203449;margin:0;padding:36px}}main{{max-width:1250px;margin:auto}}h1{{font-size:32px;margin-bottom:12px}}p{{line-height:1.8}}.stats{{font-size:20px;color:#456985}}.card{{background:white;padding:24px;border-radius:12px;box-shadow:0 3px 18px #1232}}input{{font:inherit;padding:12px;width:calc(100% - 26px);border:1px solid #b7c8d5;border-radius:7px;margin-bottom:18px}}table{{width:100%;border-collapse:collapse;text-align:left}}th{{background:#eaf1f6}}td,th{{padding:14px 10px;border-bottom:1px solid #dfE7ef}}small{{display:block;color:#6c8192;margin-top:6px;font-size:13px}}.links a{{display:inline-block;margin:3px 3px;padding:7px 9px;background:#e9f2fa;border-radius:5px;text-decoration:none;color:#174e77}}.skipped{{color:#8393a1;background:#fafbfc}}.note{{font-size:14px;color:#60758b}}.scroll{{overflow-x:auto}}@media(max-width:700px){{body{{padding:16px}}table{{min-width:900px}}}}.download-all{{display:inline-block;padding:12px 18px;background:#174e77;color:white;border-radius:7px;text-decoration:none}}.download-all:focus-visible,a:focus-visible{{outline:3px solid #5b94bc;outline-offset:3px}}</style>
<main><h1>AI 技术手册中文译本总目录</h1><div class="stats">11 份原文 · 11 份中文译本 · 11 份术语表</div><p>整理日期：{report['整理日期']}。第 12、13 份按要求跳过；第 2 份复用本聊天此前已完成并验证的译本。</p>
<p class="note">{report['说明']}每份译本都包含可点击目录、侧边栏大纲书签和每页返回目录链接。页数为译本实际页数。</p>
<p><a class="download-all" href="AI_Handbooks_zh.zip" download>下载全部 11 份手册（ZIP）</a></p><div class="card"><input id="search" aria-label="搜索手册" placeholder="输入关键词筛选，例如 GPU、量化、Attention"><div class="scroll"><table><thead><tr><th>编号</th><th>文档</th><th>状态</th><th>原文页</th><th>译本页</th><th>打开文件</th></tr></thead><tbody>{rows}<tr class="skipped"><td>12</td><td><b>投机解码</b></td><td>链接需登录，按要求暂时跳过</td><td>—</td><td>—</td><td>—</td></tr><tr class="skipped"><td>13</td><td><b>Agent 控制层工程</b></td><td>链接需登录，按要求暂时跳过</td><td>—</td><td>—</td><td>—</td></tr></tbody></table></div></div><p class="note">文件夹结构：originals/ 原文，zh/ 中文译本，terminology/ 术语表。原文作者：<a href="https://x.com/techNmak">@techNmak</a> · Understanding AI 系列。</p></main><script>document.querySelector('#search').addEventListener('input',e=>{{let q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}});</script></html>'''
(OUT/'00_总目录.html').write_text(index,'utf-8')
for target in [OUT,REPO]:
 (target/'index.html').write_text(index,'utf-8')
# ZIP contains originals, translations, terminology and catalogs.
zip_path=OUT/'AI_Handbooks_zh.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in ['originals','zh','terminology']:
  for f in sorted((OUT/folder).glob('*')):
   if f.is_file():z.write(f,f'{folder}/{f.name}')
 for f in ['00_总目录.html','00_总目录.md','00_文件清单.json']:z.write(OUT/f,f)
print('catalogs and ZIP written:',zip_path,zip_path.stat().st_size)
# Website and repository share the same static tree.
for target in [SITE,REPO]:
 for folder in ['originals','zh','terminology']:
  (target/folder).mkdir(parents=True,exist_ok=True)
  for f in sorted((OUT/folder).glob('*')):
   if f.is_file():shutil.copy2(f,target/folder/f.name)
 shutil.copy2(zip_path,target/zip_path.name)
 for f in ['00_总目录.html','00_总目录.md','00_文件清单.json']:shutil.copy2(OUT/f,target/f)
 (target/'.nojekyll').write_text('', 'utf-8')
print('site and repository assets synced')

# Reproducible translation pipeline and reviewed data are part of the repository.
TOOLS=REPO/'tools/translate_pdf';TOOLS.mkdir(parents=True,exist_ok=True)
for name in ['prepare.py','translate.py','build.py','verify.py','editorial.py','review_fixes.py','audit.py','publish.py']:
 shutil.copy2(W/name,TOOLS/name)
(TOOLS/'manifest.json').write_text(json.dumps([dict(number=n,slug=SLUG[n],title=EN[n],status='downloaded',source_pages=next((d['source_pages'] for d in docs if d['number']==n),33),path=f'originals/{n:02d}_{SLUG[n]}.pdf') for n in range(1,12)],ensure_ascii=False,indent=2),'utf-8')
(TOOLS/'glossary.txt').write_text((ROOT/'work/glossary.txt').read_text('utf-8'),'utf-8')
(TOOLS/'extra_terms.txt').write_text((ROOT/'work/pdf-series/extra_terms.txt').read_text('utf-8'),'utf-8')
normalised=json.loads(json.dumps(docs,ensure_ascii=False))
for d in normalised:
 rel=f'originals/{d["number"]:02d}_{d["slug"]}.pdf';d['source']=rel
 for a in d['assets']:a['source']=rel
 for u in d['units']:
  for m in u['maths'].values():m['source']=rel
(TOOLS/'inventory.json').write_text(json.dumps(normalised,ensure_ascii=False,indent=2),'utf-8')
(TOOLS/'units.json').write_text(json.dumps([u for d in normalised for u in d['units']],ensure_ascii=False,indent=2),'utf-8')
(TOOLS/'cache').mkdir(exist_ok=True)
for u in [u for d in docs for u in d['units']]:
 src=W/'cache'/(u['key']+'.json')
 if src.exists() and not (TOOLS/'cache'/src.name).exists():shutil.copy2(src,TOOLS/'cache'/src.name)
(TOOLS/'overrides-by-source.json').write_text((W/'overrides-by-source.json').read_text('utf-8'),'utf-8')
(TOOLS/'README.md').write_text('''# PDF 翻译流程

这套脚本复现本仓库中文译本的生成流程：

1. `prepare.py` 读取 `manifest.json` 列出的原文 PDF，分离正文、行内公式、独立公式、图表、表格、代码和参考文献，并生成术语保护标记与逐页元素顺序（`inventory.json`、`units.json`）。
2. `translate.py` 翻译正文，公式和专有名称以标记保留；结果写入 `cache/`。
3. `editorial.py` 与 `overrides-by-source.json` 应用人工校订的术语和段落修订。
4. `build.py` 用 ReportLab 排版中文正文，并把原稿中的矢量公式与图表裁切回对应位置；中文字体为 LXGW WenKai，英文、数字和代码为 Times New Roman。
5. `verify.py` 检查大纲与内部链接、公式覆盖、字体嵌入、原文图片保留和逐页词覆盖。
6. `publish.py` 汇总 PDF、术语表、目录、ZIP 与网页目录。

## 依赖

- Python 3，`pymupdf`（PyMuPDF 1.28 或兼容版本）、`reportlab`、`Pillow`
- 字体：`C:/Windows/Fonts/LXGWWenKai-Regular.ttf`、`times.ttf`、`timesbd.ttf`
- 原文 PDF 放在仓库根目录的 `originals/`

脚本中的 `ROOT` 指向仓库上一级，因此请在仓库内的 `tools/translate_pdf` 目录运行，并保持 `originals/` 与脚本的相对位置。

翻译文本由机器辅助生成，随后按术语表与上下文人工校订。公式、符号、图表和代码标识符保留原文。
''','utf-8')
(REPO/'README.md').write_text(f'''# AI 技术手册中文译本

11 份 AI 技术手册的中文译本、英文原文与专业术语对照表，整理日期 {report['整理日期']}。

> 原文作者：**[@techNmak](https://x.com/techNmak)**（X / Twitter）· Understanding AI 系列
> 本仓库仅为学习参考的中文译本整理，原文著作权归作者所有。

## 在线阅读

打开 `index.html` 可浏览总目录，支持关键词筛选，并可直接打开中文 PDF、英文原文与术语表。

## 译本格式

中文正文逐段翻译，术语首次出现时括注英文原词。原稿中的矢量公式、数学记号、图表与代码保留在对应中文段落和图注位置；图中自然语言标签译为中文，过长的标签在紧邻位置给出完整中文说明。每份译本包含：

- 前置专业术语对照表；
- 可点击目录导航页，每页提供“返回目录”链接；
- 侧边栏大纲书签，按原稿页码顺序建立；
- 中文 LXGW WenKai、英文与数字 Times New Roman，字体已嵌入；
- 原稿页面对应说明，便于追溯。

第 12 份《投机解码》与第 13 份《Agent Harness Engineering》的原文链接需要 Google 登录，按要求暂未收录。

## 仓库结构

| 目录 | 内容 |
|---|---|
| `zh/` | 中文译本 PDF |
| `originals/` | 英文原文 PDF |
| `terminology/` | 专业术语中英对照表，UTF-8 BOM CSV |
| `tools/translate_pdf/` | 可复现的翻译与排版流程、术语数据与校订文本 |
| `AI_Handbooks_zh.zip` | 全部文件打包下载 |
| `index.html` | 总目录网页 |
| `00_总目录.md` | 总目录 Markdown 版 |
| `00_文件清单.json` | 文件清单与页数统计 |

## 手册清单

| 编号 | 文档 | 原文页数 | 译本页数 |
|---|---:|---:|---:|
{chr(10).join(f"| {m['编号']:02d} | {m['标题']} | {m['原页数']} | {m['译页数']} |" for m in report['手册'])}

原文作者为 **[@techNmak](https://x.com/techNmak)**，出自其 Understanding AI 系列。本仓库仅作学习交流用途，译文与排版整理不主张对原文的任何权利；原文及插图、公式、代码的著作权均归原作者所有。若原作者认为本仓库内容不妥，请联系删除。
''','utf-8')
print('repository README and pipeline exported')

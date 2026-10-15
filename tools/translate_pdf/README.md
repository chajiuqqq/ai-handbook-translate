# PDF 翻译流程

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

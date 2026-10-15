from pathlib import Path
import json,re
W=Path(__file__).resolve().parent
units=json.loads((W/'units.json').read_text('utf-8'))
missing={
 'bdf4d9946aafeeb6a579c0f08acfeedf7cf949f84b47a6237f74f96f53c813e4':None,
 '00e822e88c1dc6d9a61d9581bcd276601c8d076f9d14a43d842e8e7032c404a9':'ZXMATH0000XZ',
 '5bb6f7c3bec9855d4675a9aca48aad884f6a7c158858c7ffad1b6d37381d2523':'分页注意力与 ZXNAME0000XZ 一同提出，用于减少碎片化和重复存储造成的 KV 缓存浪费',
 '8fbbde4ee8bceb35c7dc7ba0edc77a8e5985bfb759fefa882ecabadc95e2fe25':'ZXMATH0000XZ =',
 '3353971b3561a49358281cfdc9947287970a8795d4c88fd7581482deabd05da4':'逻辑工作集合 ZXMATH0000XZ 驻留工作集合 ZXMATH0001XZ 可调度工作集合 ZXMATH0002XZ 某一时刻实际发射的工作集合。',
}
for u in units:
 if u['key'] in missing:
  zh=missing[u['key']]
  if zh is None:zh=u['text'].replace('Layer','层')
  (W/'cache'/(u['key']+'.json')).write_text(json.dumps(dict(source=u['text'],zh=zh),ensure_ascii=False),'utf-8')

# Contextual corrections retained as editable, reviewable occurrence overrides.
patterns=[
 ('why MQA, GQA, and MLA attack KV cost','• 为什么 MQA、GQA 和 MLA 能以不同方式降低 KV 成本；'),
 ('why cache management becomes a systems problem','• 为什么在并发推理服务中，缓存管理会成为系统层面的问题；'),
 ('A KV cache does not eliminate attention','KV 缓存并没有消除对历史内容的注意力计算。对于稠密注意力，新查询仍须与过去的 K/V 状态交互。'),
 ('The goal is not to memorize another optimization.','目标不是再记住一种优化，而是理解其数学有效性、节省的资源以及仍然存在的成本。'),
 ('What is not cached by this idea','这一机制没有缓存什么'),
 ('The useful observation','关键观察'),
 ('The oldZXMATH0000XZ andZXMATH0001XZ are read','旧的 ZXMATH0000XZ 和 ZXMATH0001XZ 只需读取，无须重新生成。'),
 ('5. The resulting attention weights mix','5. 得到的注意力权重对 ZXMATH0000XZ 进行加权组合。'),
 ('No. PagedAttention addresses KV-cache','不是。分页注意力解决 KV 缓存的内存管理问题；FlashAttention 解决注意力计算效率与内存流量问题。'),
 ('3. Where does the state live?','3. 状态存放在哪里？连续的 GPU 张量、分页块、CPU 卸载、远程缓存，还是多个层级？'),
 ('The KV cache is simultaneously a consequence','KV 缓存同时是因果注意力带来的结果、模型架构的设计约束，'),
 ('and a runtime memory-management problem.','以及运行时的内存管理问题。理解这三个层面，才能真正掌握这一概念。'),
 ('cache reuse domain should match trust domain','缓存复用域应与信任域保持一致 ZXMATH0000XZ'),
]
overrides=json.loads((W/'overrides.json').read_text('utf-8')) if (W/'overrides.json').exists() else {}
manual={
 'd01p008u0049':'''[1] Patrick Lewis et al. 面向知识密集型自然语言处理任务的检索增强生成。NeurIPS 2020。
[2] Anthropic. 面向 AI 智能体的有效上下文工程。工程博客，2025。
[3] Yulong Hui, Yao Lu, Huanchen Zhang. UDA：面向真实世界文档分析中检索增强生成的基准测试套件。NeurIPS 2024 数据集与基准赛道。
[4] Zhitong Wang et al. 文档分割对检索增强生成至关重要。Findings of ACL 2025。
[5] Anthropic. 上下文检索介绍。工程博客，2024。
[6] Michael Gunther, Isabelle Mohr, Daniel James Williams, Bo Wang, Han Xiao. 延迟分块：利用长上下文嵌入模型生成带上下文的块嵌入。arXiv:2409.04701，2024。
[7] Parth Sarthi et al. RAPTOR：用于树状组织检索的递归抽象处理。ICLR 2024。
[8] Nelson F. Liu et al. 迷失在中间：语言模型如何利用长上下文。TACL 2023。
[9] Liang Wang, Nan Yang, Furu Wei. Query2doc：利用大语言模型扩展查询。EMNLP 2023。
[10] Luyu Gao, Xueguang Ma, Jimmy Lin, Jamie Callan. 无相关性标签的精确零样本稠密检索（HyDE）。ACL 2023。
[11] Gordon V. Cormack, Charles L. A. Clarke, Stefan Buettcher. 倒数排名融合优于 Condorcet 方法及单独的排名学习方法。SIGIR 2009。
[12] Harsh Trivedi et al. 面向知识密集型多步骤问题，将检索与思维链推理交错进行。ACL 2023。
[13] Zhengbao Jiang et al. 主动检索增强生成（FLARE）。EMNLP 2023。''',
 'd01p008u0050':'''[14] Akari Asai et al. Self-RAG：通过自我反思学习检索、生成与评判。ICLR 2024。
[15] Shi-Qi Yan, Jia-Chen Gu, Yun Zhu, Zhen-Hua Ling. 纠正式检索增强生成。arXiv:2401.15884，2024。
[16] Fangyuan Xu, Weijia Shi, Eunsol Choi. RECOMP：利用上下文压缩与选择性增强改进检索增强语言模型。ICLR 2024。
[17] Huiqiang Jiang et al. LongLLMLingua：通过提示词压缩，在长上下文场景中加速并增强大语言模型。ACL 2024。
[18] Hung-Ting Chen, Michael Zhang, Eunsol Choi. 丰富的知识''',
 'd01p008u0051':'''来源带来复杂的知识冲突：重新校准模型，使其反映相互冲突的证据。EMNLP 2022。
[19] Zhuoran Jin et al. 知识之间的拉锯战：探索并解决检索增强语言模型中的知识冲突。LREC-COLING 2024。
[20] Tianyu Gao, Howard Yen, Jiatong Yu, Danqi Chen. 使大语言模型生成带有引用的文本（ALCE）。EMNLP 2023。
[21] Jonas Wallat, Maria Heuss, Maarten de Rijke, Avishek Anand. RAG 归因中的正确性不等于忠实性。ICTIR 2025。
[22] Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert. RAGAS：检索增强生成的自动评估。EACL 2024 系统演示。
[23] Jon Saad-Falcon, Omar Khattab, Christopher Potts, Matei Zaharia. ARES：检索增强生成系统的自动评估框架。NAACL 2024。
[24] Dongyu Ru et al. RAGChecker：诊断检索增强生成的细粒度框架。NeurIPS 2024 数据集与基准赛道。
[25] Darren Edge et al. 从局部到全局：利用图 RAG 进行面向查询的摘要。arXiv:2404.16130，2025 年修订。
[26] Zhuowan Li, Cheng Li, Mingyang Zhang, Qiaozhu Mei, Michael Bendersky. 检索增强生成还是长上下文大语言模型？一项综合研究与混合方法。EMNLP 2024 行业赛道。
[27] Kuan Li et al. LaRA：检索增强生成与长上下文大语言模型的基准测试——长上下文或 RAG 路由均无万能解法。ICML 2025。
[28] Wei Zou, Runpeng Geng, Binghui Wang, Jinyuan Jia. PoisonedRAG：针对大语言模型检索增强生成的知识破坏攻击。arXiv:2402.07867，2024。
[29] Xun Liang et al. SafeRAG：大语言模型检索增强生成的安全性基准测试。ACL 2025。
[30] Shashank Shreedhar Bhatt et al. 企业 AI 必须执行感知参与者身份的访问控制。arXiv:2509.14608，2025。
[31] Valentin J. J. Kreileder, Johannes Reisinger, Andreas Fischer. 面向学术文本，评估检索增强生成的分块策略。arXiv:2607.01852，2026。
[32] Yulin Chen, Haoran Li, Yuan Sui, Yufei He, Yue Liu, Yangqiu Song, Bryan Hooi. 能否检测并移除间接提示词注入攻击？ACL 2025。''',
 'd05p005u0033':'在标准 MHA 中，查询头、键头和值头的数量相同：',
 'd05p008u0058':'对于解码步骤中的一个层，简单的有效载荷模型与以下量成正比：',
 'd07p030u0287':'ZXNAME0000XZ 推理至少包含两个不同的执行阶段。',
 'd07p030u0292':'这是一种用于检查数量级是否合理的上界估算，并非吞吐量预测。',
 'd07p040u0390':'36 一套实用的内存理解框架',
 'd08p001u0000':'理解混合专家模型',
 'd08p003u0026':'为什么需要混合专家模型',
 'd11p025u0317':'23 — GPTQ、AWQ、SmoothQuant 与 ZXNAME0000XZ.ZXNAME0001XZ',
 'd01p002u0009':'1. 什么是检索增强生成（RAG）？它为语言模型提供了哪些仅靠模型参数无法提供的能力？【入门】\nRAG 在推理时从外部知识源检索信息，用以增强生成。模型仍提供其参数化知识和语言生成能力，但提示词或模型计算会以检索到的非参数证据为条件。在最初的 RAG 建模中，检索器为文档赋予概率，生成器则同时以输入和检索文档为条件。核心思想是：有用的知识不必只存储在模型权重中。\n这样更容易更新外部知识，也为追溯来源提供了途径。但它不会自动保证答案符合事实：检索器可能漏掉证据，语料库本身可能有误，生成器也可能忽略或误用正确的上下文。因此，应将 RAG 理解为获取证据的架构，而不是消除幻觉的开关。[1]',
 'd01p003u0014':'例如，将表格压平成文本流，可能会让数值与对应的行、列标签分离；后续检索可能返回表面正确、含义却错误的数字。UDA 直接以原始 PDF／HTML 为对象，特别强调了解析对端到端 RAG 形成的瓶颈。生产系统应在具有代表性的文档类型上评估提取质量，保留有用的源坐标与结构元数据；对表格或布局密集的材料，采用适合该来源的解析器或多模态方法。更好的嵌入向量无法恢复解析阶段已经破坏的信息。[3]',
 'd01p007u0038':'任何内容过滤器都不能证明系统安全。因此，高影响操作应设置确定性的授权与验证关卡。模型不应仅因检索文档的要求而获得新的权限。间接提示词注入研究，专门研究通过外部内容传入、而非由用户直接发出的恶意指令。[28][29][32]',
 'd01p007u0042':'30. 为持续变化的企业语料库设计生产级 RAG 系统，需要支持权限、引用、多跳问题、长文档，并满足严格的延迟 SLO。如何证明每一层都有效？【高级 · 系统设计】\n从治理要求与工作负载出发。数据摄取应保留来源 ID、版本、结构和访问控制列表（ACL）；解析必须在具有代表性的 PDF 与表格上测试。先建立简单的词法＋稠密检索基线，测量证据召回率；只有确实改善候选结果到最终上下文的选择时，才增加重排序。根据文档结构与评估结果选择分块方式；只有在确实解决相应失败案例时，才使用层次检索或上下文化检索。\n在组装提示词之前执行授权检查。将多跳问题交给迭代检索；语料库层面的主题问题可考虑图方法或层次方法；对于规模较小、边界明确的语料库，直接测试长上下文。上下文打包应去重、保留来源、有意识地排列高价值证据，并满足明确的词元预算。生成器应引用源文档中的具体片段，遇到证据不足或互相冲突时拒答。\n安全测试必须覆盖投毒文档、带有指令的文档及权限边界。使用各层专门的评估、端到端细分结果、延迟／成本 SLO、内容更新滞后和事件日志来验证系统。每个新增组件都必须有实测的、由它解决的失败模式；否则，它只是架构上的装饰。[3][25][26][27][30]',
}
overrides.update(manual)
for u in units:
 for prefix,zh in patterns:
  if u['source'].startswith(prefix):
   # Protected identifiers have to match this occurrence's own source.
   source_tokens=set(re.findall(r'ZX(?:NAME|MATH)\d{4}XZ',u['text']))
   target_tokens=set(re.findall(r'ZX(?:NAME|MATH)\d{4}XZ',zh))
   if source_tokens==target_tokens:overrides[u['id']]=zh
(W/'overrides.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2),'utf-8')
print('Reviewed occurrence overrides:',len(overrides))

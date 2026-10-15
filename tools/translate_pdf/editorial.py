"""Contextual terminology normalisation, applied before PDF markup."""
import re

REPLACE={
 '法学硕士':'大语言模型','迎新活动':'阅读导引','研究锚点':'研究依据','研究锚':'研究依据',
 '首要原则':'基本原理','第一原则':'基本原理','天真的':'朴素的','幼稚的':'朴素的',
 '代币':'词元','令牌':'词元','头部尺寸':'头维度','头尺寸':'头维度',
 '头部维度':'头维度','高速缓冲存储器':'缓存内存','高速缓存存储器':'缓存内存',
 '密集注意力':'稠密注意力','密集的注意力':'稠密注意力','密集型注意力':'稠密注意力',
 '因果屏蔽':'因果掩码','因果遮罩':'因果掩码','心理模型':'理解框架','心智模型':'理解框架',
 '精神模型':'理解框架','挂钟时间':'实际耗时','墙上时钟时间':'实际耗时','挂钟':'实际运行',
 '人头':'头','磁头':'头','潜伏表示':'潜在表示','正向传递':'前向传播','反向传递':'反向传播',
 '前向传递':'前向传播','后向传递':'反向传播','操作员':'算子','算术密度':'算术强度',
 '算术强度比':'算术强度比','低等级':'低秩','低排名':'低秩','低阶压缩':'低秩压缩',
 '簿记':'管理开销','建筑学':'架构','建筑':'架构','国家':'状态','职位':'位置',
 '批量大小':'批大小','批次大小':'批大小','共享存储器':'共享内存','全球内存':'全局内存',
 '全球存储器':'全局内存','局部存储器':'局部内存','寄存器溢出':'寄存器溢出',
 '扭曲组':'线程束组','扭曲':'线程束','翘曲':'线程束','经线':'线程束','银行冲突':'存储体冲突',
 '银行':'存储体','内存合并':'内存访问合并','合并内存访问':'内存访问合并','世代':'代际',
 '张量芯':'张量核心','核心核心':'核心',
 '占有率':'占用率','职业':'占用率','任职':'占用率',
 '象征性事实':'符号化事实','数字键/值状态':'数值键／值状态','数字状态':'数值状态',
 '有效负载':'有效载荷','图层':'层','概率质量':'概率质量','逻辑值':'逻辑值',
 '地面真相':'基准真值','基本事实':'基准真值','地面实况':'基准真值',
 '幻觉开关':'消除幻觉的开关','幻觉交换机':'消除幻觉的开关','候选人检索':'候选检索',
 '猎犬':'检索器','生成者':'生成器','重新排序器':'重排序器','重新排名':'重排序',
 '重新排序':'重排序','矢量数据库':'向量数据库','词汇/密集':'词法／稠密',
 '词汇+密集':'词法＋稠密','密集检索':'稠密检索','多模式 RAG':'多模态 RAG',
 '提示注入':'提示词注入','即时注入':'提示词注入',
 '提示工程':'提示词工程','即时工程':'提示词工程','矢量检索':'向量检索',
 '快速组装':'提示词组装','及时清理':'提示词清理','有意订购':'有意识地排列',
 '申请授权':'执行授权检查','一代;':'生成；','重排序者':'重排序器',
 '后期分块':'延迟分块','分层检索':'层次检索','参数知识':'参数化知识',
 '反射信号':'反思信号','架构课程':'架构启示','思想链':'思维链','法官':'评估器',
 '即时压缩':'提示词压缩','人工词元':'人工标注','多模式方法':'多模态方法',
 '托管卸载':'主机内存卸载','及时加载':'按需加载','池化层':'池化层',
 '工程课程':'工程启示','工件':'产物','盐被':'盐值被','量化量表':'量化缩放因子',
 '量化尺度':'量化缩放因子','量化比例':'量化缩放因子','量化规模':'量化缩放因子',
 '标量乘积':'标量乘积','非线性度':'非线性','路由器':'路由器',
 '热点':'热点','硬件屋顶':'硬件上限','屋顶线':'屋顶线',
 '壁钟':'实际运行','地址转换':'地址转换','无偿':'免费',
 'token':'token',
}

EXACT={
 'ORIENTATION':'阅读导引','REFERENCES':'参考文献','SUMMARY':'总结',
 'About this handbook':'关于本手册','Prerequisites':'先备知识',
 'Core Concepts, Design Decisions, and Failure Modes':'核心概念、设计决策与失效模式',
 'RAG & Context Engineering':'检索增强生成与上下文工程',
 'Research anchors':'研究依据','Architecture':'架构','positions':'位置',
 'Establishes state':'建立初始状态',
 'New processed Cache action Attention length Reuse benefit':'新处理的位置／缓存操作／注意力长度／复用收益',
 'MHA, GQA, and MQA in one model':'在同一模型中比较 MHA、GQA 与 MQA',
 'What this handbook will make clear':'本手册将澄清哪些问题',
 'KV cache in one chain':'用一条因果链理解 KV 缓存',
 'A KV cache is easy to describe badly. It is often called “LLM memory,” a “speed trick,” or simply “cached attention.” Those shortcuts hide the mechanism that matters.':
 'KV 缓存很容易被描述得不准确。人们常把它称为“大语言模型的记忆”“加速技巧”，或简单称为“缓存的注意力”。这些简略说法掩盖了真正重要的机制。',
 'A decoder-only language model assigns a distribution to the next token conditioned on the tokens already available:':
 '仅解码器语言模型根据已有词元，为下一个词元给出条件概率分布：',
 'The current query attends over the accumulated history:':'当前查询对累积的历史执行注意力计算：',
 '• 2 accounts for both K and V;':'• 系数 2 表示同时存储 K 和 V；',
 'The only value we change is ZXMATH0000XZ':'我们唯一改变的量是 ZXMATH0000XZ',
}

SYNONYMS={
 'Token':['词元','token'], 'Tokens':['词元'],
 'KV Cache':['KV 缓存','KV缓存','键值缓存','KV-cache'],
 'Attention':['注意力机制','注意力'], 'Attention Weight':['注意力权重'],
 'Dense Attention':['稠密注意力'], 'Learned Projection':['学习得到的投影','学习投影'],
 'Multi-head Attention':['多头注意力'], 'MHA':['多头注意力'],
 'Multi-query Attention':['多查询注意力'],'MQA':['多查询注意力'],
 'Grouped-query Attention':['分组查询注意力'],'GQA':['分组查询注意力'],
 'Multi-head Latent Attention':['多头潜在注意力'],'MLA':['多头潜在注意力'],
 'Retrieval-augmented Generation':['检索增强生成'],
 'Head Dimension':['头维度'],'Serving':['推理服务','服务'],
 'Ground Truth':['基准真值'],'Memory-bound':['内存受限','内存绑定'],
 'Compute-bound':['计算受限','计算绑定'],'Bandwidth-bound':['带宽受限','带宽绑定'],
 'Arithmetic Intensity':['算术强度'],'Projection':['投影'],
 'Embedding':['嵌入向量','嵌入'],'Embeddings':['嵌入向量','嵌入'],
}

def edit(u,text,short=False):
    text=EXACT.get(u['source'],text)
    if re.search(r'\btokens?\b',u['source'],re.I):text=re.sub(r'(?<!人工)(?<!人类)标记','词元',text)
    if re.search(r'\brecall\b',u['source'],re.I):text=text.replace('回忆','召回率')
    if 'Anthropic' in u['source']:text=text.replace('人类。','Anthropic。').replace('人择','Anthropic')
    if 'ground truth' in u['source'].lower():text=text.replace('不是事实','不是基准真值')
    if re.search(r'\bQA\b',u['source']):text=text.replace('质量保证','问答')
    for a,b in REPLACE.items():text=text.replace(a,b)
    for token,t in reversed(list(u['terms'].items())):text=text.replace(token,t['en'])
    if re.match(r'^\[\d+\]',u['source']) and len(re.findall(r'\[\d+\]',u['source']))==1:
        author_end=re.search(r'(?:et al|[a-z])\.\s+(?=[A-Z])',u['source'])
        if author_end:
            original_author=u['source'][:author_end.end()].strip()
            same=re.sub(r'\s+','',text).startswith(re.sub(r'\s+','',original_author))
            first_stop=text.find('。')
            if not same and 0<first_stop<110:
                text=original_author+' '+text[first_stop+1:].lstrip()
    text=re.sub(r'(?<=\d)\s+GiB', ' GiB',text)
    text=text.replace('elementstorage','元素存储').replace('KV-head','键值头')
    text=text.replace('高速缓存','缓存').replace('量表','缩放因子')
    text=text.replace('in-place','原位').replace('head 尺寸','头维度')
    text=text.replace('张量核，','张量核心，').replace('知识图，','知识图谱，')
    if u['document']==1:
        text=text.replace('线程束细节','扭曲细节').replace('弃权','拒答').replace('问责','可回答性')
        text=text.replace('广告大上下文窗口的模型','宣称支持大上下文窗口的模型')
        text=text.replace('标记代表性查询','标注代表性查询').replace('词元代表性查询','标注代表性查询')
        text=text.replace('状态检索','有状态检索').replace('强制执行确定性执行','执行确定性的检查')
        text=text.replace('预测驱动的推理','预测辅助推断').replace('综合训练数据','合成训练数据')
        text=text.replace('综合问题','合成问题').replace('适当下降','适当拒答')
    # Annotate only terminology present in this source unit, in one nonrecursive
    # longest-match pass so that "注意力" cannot nest inside "多头注意力".
    choices={}
    for t in u.get('annotations',[]):
        en,zh=t['en'],t['zh']
        if '方法名保留' in zh or '模型名保留' in zh or en in ['Softmax','Transformer','Core']:continue
        for label in SYNONYMS.get(en,[zh]):
            if not label or len(label)<2:continue
            value=zh if short else f'{zh}（{en}）'
            if zh==en:value=en
            choices.setdefault(label,value)
    if choices:
        pattern='|'.join((r'(?<![A-Za-z])'+re.escape(x)+r'(?![A-Za-z])') if re.fullmatch(r'[A-Za-z]+',x) else re.escape(x) for x in sorted(choices,key=len,reverse=True))
        seen=set()
        def annotate(m):
            value=choices[m[0]]
            if value in seen:return value.split('（')[0]
            seen.add(value);return value
        text=re.sub(pattern,annotate,text)
    if re.search(r'ZX(?:TERM|NAME)\d{4}XZ',text):raise ValueError('Unresolved protected name '+u['id'])
    return text

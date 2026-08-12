---
sidebar_position: 2
---

# AI Agent 开发平台——零代码与低代码的智能体工厂

不会写代码，但想做一个能自动回复客户、整理文档、分析数据的 AI Agent？2026 年，这件事已经不需要找开发团队了。

我是怕浪猫，这个系列《智能体产品全景手册》的第 2 篇。上一篇我们盘点了通用型 AI Agent 和对话助手，这一篇我们进入开发者视角——但不需要你是开发者。因为今天要讲的是 AI Agent 开发平台，它们就是"智能体工厂"，让你像搭积木一样造出属于自己的 Agent。

## 2.1 开发平台 vs 开发框架：两条路线的选择

在开始拆解具体产品之前，先搞清楚一个根本问题：开发平台和开发框架有什么区别？你应该走哪条路？

**开发平台（Development Platform）** 提供的是一站式服务：可视化界面、拖拽式编排、内置模型、托管部署、监控分析全部打包好。你不需要写代码（或者只需要写很少的代码），只需要定义 Agent 的角色、能力、知识库，平台帮你搞定剩下的事情。

**开发框架（Development Framework）** 提供的是代码库和抽象层：你需要用 Python 或 TypeScript 写代码，调用框架提供的 API 来构建 Agent 的逻辑。框架给你更大的自由度和控制力，但门槛更高。

这两条路线的核心差异可以用下面的对比来理解：

| 维度 | 开发平台 | 开发框架 |
|------|---------|---------|
| 使用方式 | 可视化拖拽 | 编写代码 |
| 技术门槛 | 低（产品经理可用） | 高（需开发经验） |
| 灵活性 | 中等（平台能力范围内） | 高（代码级控制） |
| 部署方式 | 平台托管 | 自行部署 |
| 定制深度 | 配置层面 | 代码层面 |
| 适合场景 | 快速验证、标准化需求 | 复杂逻辑、深度定制 |
| 代表产品 | Coze、Dify、百度千帆 | LangChain、AutoGen、CrewAI |

> 开发平台是"拎包入住"的精装房，开发框架是"自己盖"的毛坯地。选哪个取决于你的预算、时间和需求复杂度。

怎么选？我给你一个简单的决策规则：

如果你的需求是"让 AI 根据知识库回答客户问题"、"自动分类邮件并回复"、"根据数据生成日报"这类标准化场景，选开发平台。如果你是产品经理、运营人员、或者小型团队想快速验证 AI Agent 的价值，也选开发平台。

如果你的需求是"多 Agent 协作完成复杂软件开发"、"需要自定义推理逻辑和工具链"、"需要深度集成到现有技术栈"，选开发框架。如果你是开发者、技术团队、或者需要构建高度定制化的 Agent 系统，选开发框架。

开发框架的内容我们在第 3 章详细展开，这一章专注于开发平台。

## 2.2 零代码平台深度拆解

### Coze / 扣子（字节跳动）

Coze 是字节跳动推出的 AI Agent 开发平台，国内版叫"扣子"，国际版叫 Coze。它是目前国内用户量最大的 Agent 开发平台之一。

核心功能包括：可视化工作流编排、多模型支持（豆包大模型、GPT、Claude 等）、插件市场（数百个预置插件）、知识库管理、多渠道发布（飞书、微信公众号、抖音、微信客服等）、定时任务和触发器。

Coze 的工作流引擎是其核心。工作流由节点组成，每个节点执行一个操作：调用大模型、查询知识库、执行代码、调用 API、条件分支等。节点之间通过连线定义执行顺序，支持并行和循环。

```
# Coze 工作流的核心数据结构
workflow = {
    "nodes": [
        {"id": "start", "type": "input", "config": {"prompt": "{{user_input}}"}},
        {"id": "llm_1", "type": "llm", "config": {"model": "doubao-pro", "prompt": "分析用户意图：{{start.output}}"}},
        {"id": "kb_1", "type": "knowledge", "config": {"query": "{{llm_1.output}}", "top_k": 5}},
        {"id": "llm_2", "type": "llm", "config": {"model": "doubao-pro", "prompt": "基于以下信息回答：{{kb_1.output}}"}},
        {"id": "end", "type": "output", "config": {"content": "{{llm_2.output}}"}}
    ],
    "edges": [
        {"from": "start", "to": "llm_1"},
        {"from": "llm_1", "to": "kb_1"},
        {"from": "kb_1", "to": "llm_2"},
        {"from": "llm_2", "to": "end"}
    ]
}
```

产品表现方面，Coze 在国内 Agent 平台中用户量领先。2025 年字节跳动发布了"扣子空间"——一个类似 GPT Store 的 Agent 市场和运行环境，用户可以发布自己创建的 Agent，也可以使用他人创建的。扣子空间在 2026 年中科院《互联网周刊》企业级 AI TOP50 榜单中排名第一。

Coze 的最大优势是生态完整。从创建到发布到分发，全链路在一个平台内完成。对于想快速把 Agent 推向市场的团队来说，这是最省事的选择。

### Dify

Dify 是一款开源的 AI Agent 开发平台，在 GitHub 上拥有数万 Star，是开源 Agent 平台的领头羊。

核心功能包括：可视化 Prompt 编排、工作流引擎、RAG（Retrieval-Augmented Generation，检索增强生成）管道、Agent 模式、模型管理（支持几十种模型）、API 服务和嵌入式部署。

Dify 与 Coze 的关键区别在于：Dify 是开源的，可以私有化部署。这意味着你的数据和 Agent 逻辑完全在自己服务器上，不经过第三方。对于金融、医疗、政府等对数据安全要求高的场景，这一点至关重要。

Dify 的架构分为四层：

**应用层**：提供 Web 界面和 API，用户在这里创建和管理 Agent。
**编排层**：工作流引擎和 Prompt 管理器，负责将用户定义的 Agent 逻辑转化为执行计划。
**能力层**：包括 RAG 引擎、工具调用器、代码执行沙箱等核心能力组件。
**模型层**：模型管理器统一对接各种大模型 API，支持负载均衡和故障切换。

```
# Dify RAG 管道的核心流程
class DifyRAGPipeline:
    def process_document(self, document):
        # 1. 文档解析：提取文本
        text = self.parser.extract(document)
        
        # 2. 文本分块：将长文本切分为语义完整的片段
        chunks = self.chunker.split(text, 
                                    strategy="semantic",
                                    max_tokens=500,
                                    overlap=50)
        
        # 3. 向量化：将文本片段转换为向量
        embeddings = self.embedder.encode(chunks)
        
        # 4. 存储：将向量存入向量数据库
        self.vector_store.add(embeddings, chunks)
        
        # 5. 索引：构建检索索引（支持HNSW、IVF等）
        self.vector_store.build_index(algorithm="hnsw")
    
    def retrieve(self, query, top_k=5):
        # 将查询向量化
        query_vec = self.embedder.encode([query])[0]
        
        # 在向量空间中检索最相似的片段
        results = self.vector_store.search(query_vec, top_k=top_k)
        
        # 重排序：用更精细的模型对结果重新排序
        reranked = self.reranker.rerank(query, results)
        
        return reranked
```

Dify 的开源策略带来了活跃的社区生态。大量开发者贡献了插件和工具，使得 Dify 的能力扩展速度远超闭源平台。但开源也意味着你需要自己维护服务器和处理运维问题。

### 腾讯 ADP（Agent Development Platform）

腾讯云 ADP 是腾讯推出的企业级 Agent 开发平台，2025 年升级到 3.0 版本。

核心功能包括：可视化 Agent 编排、多模型接入（混元大模型及第三方模型）、企业知识库、多渠道发布（微信、企业微信、QQ 等）、权限管理和审计日志、TokenHub 用量监控。

ADP 3.0 的核心差异化在于企业级治理能力。它内置了完整的 RBAC（Role-Based Access Control，基于角色的访问控制）体系，支持多团队协作和权限隔离。审计日志记录每一次 Agent 调用的详情，满足金融和政企的合规要求。

腾讯还开源了 Cube（腾讯混元推理引擎），这是一个高性能的 Agent 推理引擎，支持大规模并发调用和智能调度。

### 百度千帆 / APPBuilder / 秒哒

百度千帆平台是企业级大模型开发平台，包含三个核心产品：

**千帆 ModelBuilder**：大模型精调平台，支持 SFT（Supervised Fine-Tuning，监督微调）、LoRA（Low-Rank Adaptation，低秩适配）等微调方法，以及 RLHF（Reinforcement Learning from Human Feedback，基于人类反馈的强化学习）。

**千帆 AppBuilder**：Agent 应用开发平台，提供可视化编排、知识库管理、组件市场。支持百度文心大模型和第三方模型。

**秒哒**：面向个人和小企业的快速 Agent 创建工具，进一步降低门槛。用户通过自然语言描述需求，秒哒自动生成 Agent。

百度的优势在于 NLP（Natural Language Processing，自然语言处理）技术积累深厚，文心大模型在中文理解方面有天然优势。千帆平台在国内大型企业和政府机构中有较多部署案例。

### 阿里云百炼 Model Studio

阿里云百炼是阿里推出的企业级大模型应用开发平台。

核心功能包括：模型广场（通义千问系列及第三方模型）、智能体编排、数据管理和标注、模型精调、评测中心、部署服务。

百炼的市场表现非常突出。通义千问大模型在中国市场的企业级 API 调用量份额达 32.1%，排名第一。这意味着国内每三个使用大模型 API 的企业中，就有一个在用百炼平台。

百炼的核心架构特点是与阿里云生态的深度整合。如果你已经在用阿里云的 OSS（对象存储）、RDS（关系型数据库）、MaxCompute（大数据平台），接入百炼几乎是零成本。

```
# 阿里云百炼的Agent创建流程
class BailianAgent:
    def __init__(self, config):
        # 1. 选择基础模型
        self.model = ModelHub.get(config["model"])  # e.g. "qwen-max"
        
        # 2. 配置系统提示词
        self.system_prompt = config["system_prompt"]
        
        # 3. 挂载知识库
        self.knowledge_base = RAGService.mount(
            collection=config["kb_collection"],
            top_k=config.get("top_k", 5)
        )
        
        # 4. 配置工具
        self.tools = ToolRegistry.register(config["tools"])
        
        # 5. 设置执行参数
        self.params = {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
            "enable_search": config.get("enable_search", False)
        }
    
    def run(self, user_input):
        # 构建完整的Agent执行上下文
        context = self._build_context(user_input)
        response = self.model.chat(context, **self.params)
        return response
```

### BetterYeah AI

BetterYeah AI 是 2026 年备受关注的国内 Agent 开发平台，主打企业级智能体解决方案。

BetterYeah 的差异化在于其"行业模板"策略。平台预置了大量行业场景模板（客服、销售、HR、财务、法务等），用户选择模板后只需配置自己的知识库和业务参数，就能快速上线一个行业专属 Agent。

这种策略降低了企业使用 AI Agent 的认知门槛——你不需要理解 Agent 的技术原理，只需要知道"我要解决客服问题"就够了。

### 腾讯元器

腾讯元器是腾讯推出的轻量级 Agent 创建平台，面向个人和小团队。

与 ADP 的企业级定位不同，元器更注重易用性和社交分享。创建的 Agent 可以直接在微信内分享和使用，与微信公众号、视频号打通。适合内容创作者和自媒体运营者快速创建互动型 Agent。

### n8n

n8n 是一款开源的工作流自动化平台，2025 年后全面拥抱 AI，成为 Agent 开发平台的有力竞争者。

n8n 的核心是节点式工作流编辑器。与 Coze 和 Dify 类似，用户通过拖拽节点来构建工作流。但 n8n 的独特优势在于其庞大的集成生态——它支持连接 400+ 种第三方服务和 API，从 Slack 到 Stripe 到 Salesforce，几乎覆盖了所有主流 SaaS 服务。

n8n 的工作流不仅能调用 AI 模型，还能编排非 AI 的业务流程。这使它特别适合"AI + 传统自动化"的混合场景，比如"用 AI 分析邮件内容，根据分析结果更新 CRM 系统中的客户标签，然后触发 Slack 通知"。

```
# n8n 工作流示例：AI邮件分类与CRM更新
workflow = {
    "nodes": [
        {
            "type": "emailTrigger",
            "config": {"mailbox": "support@company.com"}
        },
        {
            "type": "openAI",
            "config": {
                "model": "gpt-4o",
                "prompt": "分类这封邮件：意图（投诉/咨询/建议/其他），紧急程度（1-5），提取关键信息",
                "input": "={{ $json.text }}"
            }
        },
        {
            "type": "switch",
            "config": {
                "rules": [
                    {"condition": "{{ $json.intent === '投诉' }}", "output": "complaint"},
                    {"condition": "{{ $json.intent === '咨询' }}", "output": "inquiry"}
                ]
            }
        },
        {
            "type": "hubspot",  # CRM更新
            "config": {"action": "update_contact", "properties": {"last_interaction": "={{ $now }}"}}
        },
        {
            "type": "slack",
            "config": {"channel": "#customer-support", "message": "新{{ $json.intent }}：{{ $json.summary }}"}
        }
    ]
}
```

> n8n 的哲学是"连接一切"。它不试图替代 AI 模型，而是做 AI 与业务系统之间的桥梁。

下面是八款开发平台的横向对比：

| 平台 | 开发方 | 开源 | 核心优势 | 适合用户 |
|------|--------|------|---------|---------|
| Coze/扣子 | 字节跳动 | 否 | 生态完整、多渠道发布 | 快速验证、内容团队 |
| Dify | Dify | 是 | 开源、私有化部署 | 技术团队、数据敏感行业 |
| 腾讯 ADP | 腾讯 | 部分 | 企业级治理、Cube开源 | 大型企业、政企 |
| 百度千帆 | 百度 | 否 | NLP积累、中文优势 | 政府、大型企业 |
| 阿里云百炼 | 阿里云 | 否 | 云生态集成、市场第一 | 阿里云用户 |
| BetterYeah | BetterYeah | 否 | 行业模板、低门槛 | 非技术团队 |
| 腾讯元器 | 腾讯 | 否 | 微信生态、轻量 | 内容创作者 |
| n8n | n8n | 是 | 400+集成、混合编排 | 自动化工程师 |

## 2.3 平台核心架构解析：从 Prompt 编排到工作流引擎

上一节我们看了产品，这一节我们深入技术原理。所有 Agent 开发平台的核心架构都有相似之处，理解了底层原理，切换平台时就能举一反三。

### Prompt 编排层

Prompt 编排是 Agent 平台最基础的能力。它允许用户定义 Agent 的系统提示词、角色设定、行为约束等。但简单的 Prompt 并不能支撑复杂的业务逻辑，所以平台都引入了"Prompt 模板"和"变量注入"机制。

Prompt 模板的核心原理是变量替换。平台预定义一系列变量（如 `{{user_input}}`、`{{knowledge_base_result}}`、`{{previous_context}}`），用户在 Prompt 中引用这些变量，运行时由平台动态替换为实际值。

```
# Prompt 模板变量替换机制
template = """
你是一个{{role}}助手。

用户问题：{{user_input}}

相关知识：
{{knowledge_base_result}}

历史对话：
{{conversation_history}}

要求：
1. 基于以上知识回答用户问题
2. 如果知识库中没有相关信息，明确告知用户
3. 回答简洁专业
"""

# 运行时替换
rendered = template.format(
    role="客服",
    user_input="如何退款？",
    knowledge_base_result="退款政策：7天内无理由退款...",
    conversation_history="用户：我买了一件衣服\n客服：好的..."
)
```

### 工作流引擎

工作流引擎是 Agent 平台的核心。它将一个复杂的 Agent 任务拆解为多个节点的执行图（DAG，Directed Acyclic Graph，有向无环图），每个节点执行一个原子操作，节点之间通过数据流连接。

工作流引擎的核心组件包括：

**节点（Node）**：执行一个操作的最小单元。常见节点类型包括：LLM 调用、知识库检索、代码执行、条件分支、HTTP 请求、数据转换。

**边（Edge）**：定义节点之间的执行顺序和数据传递。边可以带条件，实现条件分支。

**上下文（Context）**：在整个工作流中共享的数据容器。每个节点可以读取和写入上下文。

**调度器（Scheduler）**：根据节点之间的依赖关系决定执行顺序，支持并行执行无依赖的节点。

```
# 工作流引擎的核心调度逻辑
class WorkflowEngine:
    def execute(self, workflow, initial_context):
        context = initial_context
        ready_nodes = self._get_ready_nodes(workflow, executed=set())
        
        while ready_nodes:
            # 并行执行所有就绪节点
            results = parallel_execute(
                [node.run(context) for node in ready_nodes]
            )
            
            # 更新上下文
            for node, result in zip(ready_nodes, results):
                context[node.output_key] = result
            
            # 找到下一批就绪节点
            executed.update(ready_nodes)
            ready_nodes = self._get_ready_nodes(workflow, executed)
        
        return context
```

> 工作流引擎就像一条流水线：原材料（用户输入）进来，经过一道道工序（节点），最终产出成品（回答）。好的引擎能并行处理多道工序，大幅提升效率。

### 多模型管理层

Agent 平台需要对接多个大模型 API，多模型管理层负责统一管理这些模型。核心功能包括：

**模型路由**：根据任务类型、成本、延迟等因素选择最合适的模型。比如简单分类任务路由到轻量模型，复杂推理任务路由到旗舰模型。

**负载均衡**：在多个模型实例之间分配请求，避免单点过载。

**故障切换**：当某个模型 API 不可用时，自动切换到备用模型。

**用量统计**：记录每个模型的使用量、成本、响应时间，供监控和优化。

### 渠道发布层

Agent 平台的最后一环是把创建好的 Agent 发布到用户能接触到的渠道。主流平台支持的渠道包括：Web 网站、App、微信公众号、飞书、钉钉、企业微信、API 接口、SDK 嵌入。

Coze 在渠道覆盖上最全面，特别是抖音和微信生态的集成。腾讯系产品（ADP、元器）在微信渠道上有天然优势。Dify 和 n8n 作为开源平台，主要通过 API 和嵌入式部署。

## 2.4 知识库与 RAG 搭建实战对比

RAG（Retrieval-Augmented Generation，检索增强生成）是 Agent 平台最核心的能力之一。它让 Agent 能基于你的私有知识回答问题，而不是只依赖模型训练时的知识。

### RAG 的核心原理

RAG 的工作流程分为两个阶段：

**建库阶段**：
1. 文档解析：将 PDF、Word、Excel、网页等格式的文档提取为纯文本。
2. 文本分块：将长文本切分为语义完整的片段（通常 300-500 tokens）。
3. 向量化：用 Embedding 模型将每个文本片段转换为一个高维向量（通常 768 或 1536 维）。
4. 存储：将向量和原始文本一起存入向量数据库。

**检索阶段**：
1. 查询向量化：将用户的问题用同一个 Embedding 模型转换为向量。
2. 相似度检索：在向量数据库中找到与查询向量最相似的前 K 个文本片段。
3. 重排序：用更精细的模型对检索结果重新排序，提升相关性。
4. 生成：将检索到的文本片段和用户问题一起交给大模型生成回答。

```
# RAG 完整流程的简化实现
class RAGSystem:
    def __init__(self, embedder, vector_store, reranker, llm):
        self.embedder = embedder      # 向量化模型
        self.vector_store = vector_store  # 向量数据库
        self.reranker = reranker      # 重排序模型
        self.llm = llm                # 大语言模型
    
    def ingest(self, documents):
        """建库阶段"""
        for doc in documents:
            # 解析+分块
            chunks = self._chunk_document(doc, max_tokens=500, overlap=50)
            
            # 向量化
            embeddings = [self.embedder.encode(chunk.text) for chunk in chunks]
            
            # 存储
            for chunk, emb in zip(chunks, embeddings):
                self.vector_store.add({
                    "id": chunk.id,
                    "text": chunk.text,
                    "embedding": emb,
                    "metadata": chunk.metadata  # 来源、页码等
                })
    
    def query(self, question, top_k=5):
        """检索阶段"""
        # 1. 查询向量化
        query_vec = self.embedder.encode(question)
        
        # 2. 向量检索（余弦相似度）
        candidates = self.vector_store.search(query_vec, top_k=top_k * 3)
        
        # 3. 重排序
        reranked = self.reranker.rerank(question, candidates)
        top_context = reranked[:top_k]
        
        # 4. 构建Prompt并生成回答
        context_text = "\n\n".join([item["text"] for item in top_context])
        prompt = f"""基于以下参考资料回答用户问题。

参考资料：
{context_text}

用户问题：{question}

回答要求：基于参考资料回答，如果资料中没有相关信息请说明。"""
        
        return self.llm.generate(prompt)
```

### 各平台 RAG 能力对比

| 平台 | 文档格式支持 | 分块策略 | 向量数据库 | 重排序 | 混合检索 |
|------|------------|---------|-----------|--------|---------|
| Coze | PDF/Word/Excel/网页 | 固定长度+语义 | 内置 | 支持 | 支持 |
| Dify | PDF/Word/Excel/HTML/Markdown | 语义+递归 | Weaviate/Qdrant/Milvus | 支持 | 支持（关键词+向量） |
| 腾讯 ADP | PDF/Word/Excel/图片 | 语义分块 | 内置+腾讯云向量DB | 支持 | 支持 |
| 百度千帆 | PDF/Word/Excel/网页 | 语义+段落 | 内置 | 支持 | 支持 |
| 阿里云百炼 | PDF/Word/Excel/HTML | 语义+递归 | 阿里云OpenSearch | 支持 | 支持 |
| n8n | 任意（通过节点处理） | 自定义 | 外接（Pinecone等） | 需手动配置 | 需手动配置 |

> RAG 的质量不取决于平台，而取决于你的数据质量和分块策略。垃圾进，垃圾出——这是 RAG 的第一定律。

### RAG 搭建的三个常见坑

**坑一：分块太大或太小**。分块太大，检索精度下降（一个片段包含太多信息，模型难以定位关键部分）；分块太小，上下文不完整（一个片段只有半句话，模型无法理解含义）。建议从 500 tokens 开始，overlap 设为 50-100 tokens，然后根据效果调整。

**坑二：没有重排序**。向量检索的 Top-K 结果中，往往只有 2-3 个真正相关。直接把所有结果交给模型会导致"噪音干扰"。重排序模型（如 Cohere Rerank、bge-reranker）能显著提升精度。

**坑三：忽略了混合检索**。纯向量检索对精确匹配（如产品型号、人名）效果不好。混合检索（Hybrid Search）结合关键词检索（BM25）和向量检索，能同时处理精确匹配和语义匹配。

## 2.5 企业选型决策矩阵：成本、生态、私有化、扩展性

最后一节，把所有维度整合起来，给你一个可操作的选型框架。

### 四维评估模型

我建议从四个维度评估 Agent 开发平台：

**维度一：总拥有成本（TCO，Total Cost of Ownership）**

成本不只是平台使用费，还包括：模型 API 调用费、数据存储费、开发和维护人力成本、培训成本、迁移成本。

| 平台 | 平台费用 | 模型费用 | 隐性成本 |
|------|---------|---------|---------|
| Coze | 免费起步 | 按量计费 | 迁移锁定风险 |
| Dify | 开源免费 | 模型API费 | 服务器运维 |
| 腾讯 ADP | 企业版按年 | 模型API费 | 腾讯云绑定 |
| 百度千帆 | 按量计费 | 模型API费 | 百度生态绑定 |
| 阿里云百炼 | 按量计费 | 模型API费 | 阿里云绑定 |
| n8n | 社区版免费 | 模型API费 | 自行运维 |

> 免费的才是最贵的——开源省了许可费，但运维成本可能更高。算清楚 TCO 再做决定。

**维度二：生态完整度**

生态包括：模型支持数量、预置插件/工具数量、第三方集成、社区活跃度、文档质量。

Coze 在插件数量和多渠道发布上领先。Dify 的开源社区最活跃。n8n 的第三方集成最丰富。阿里云百炼在云服务集成上最强。

**维度三：私有化与安全**

是否支持私有化部署、数据是否经过第三方、是否有完整的审计日志、是否满足行业合规要求（如等保、GDPR）。

Dify 和 n8n 是开源自部署，数据完全自主。腾讯 ADP 和百度千帆支持私有化部署但有许可费。Coze 目前是纯 SaaS 模式，不支持私有化。

**维度四：扩展性与定制深度**

当平台预置能力不够时，你能多大程度地扩展？是否支持自定义节点、自定义代码、自定义模型、Webhook 等。

Dify 和 n8n 在扩展性上最强——你可以编写自定义节点，实现任何逻辑。Coze 支持自定义插件但有限制。腾讯 ADP 和阿里云百炼在云服务范围内扩展性好，超出范围则受限。

### 选型决策树

把四个维度组合起来，我给出一个决策树：

```
你的数据是否敏感（金融/医疗/政府）？
├── 是 → 需要私有化部署
│   ├── 技术团队强 → Dify（开源、灵活）
│   ├── 技术团队弱 → 腾讯 ADP / 百度千帆（企业版私有化）
│   └── 预算有限 → n8n 社区版
└── 否 → 可以用 SaaS 平台
    ├── 需要多渠道发布（微信/抖音） → Coze
    ├── 已有云服务生态 → 对应云平台（百炼/千帆/ADP）
    ├── 需要大量第三方集成 → n8n
    ├── 非技术团队、要快速上线 → BetterYeah
    └── 个人/小团队轻量使用 → 腾讯元器
```

### 新手 vs 老手的选型区别

新手选平台看"能做什么"——哪个平台功能多、模板多、看起来强大就选哪个。结果经常陷入"功能很多但用不起来"的困境。

老手选平台看"不能做什么"和"退出成本"——哪个平台的限制我能接受？如果将来要迁移，成本有多高？数据格式是否开放？API 是否标准？

> 新手选平台像选手机，看参数。老手选平台像选配偶，看合不合适和能不能分手。

这一章我们系统性地拆解了 8 款 Agent 开发平台（Coze、Dify、腾讯 ADP、百度千帆、阿里云百炼、BetterYeah、腾讯元器、n8n），深入解析了平台的核心架构（Prompt 编排、工作流引擎、多模型管理、渠道发布），对比了 RAG 能力，最后给出了四维选型决策模型。

| 平台类别 | 产品数量 | 市场格局 |
|---------|---------|---------|
| 闭源 SaaS | 5 款 | Coze 用户量领先 |
| 开源自部署 | 2 款 | Dify 开源第一 |
| 云厂商平台 | 3 款 | 阿里云百炼调用量第一 |

觉得有用？收藏起来，下次选平台直接照抄决策树。

你在用哪个 Agent 开发平台？有没有遇到什么坑？评论区聊聊。

关注怕浪猫，下期我们讲 AI Agent 开发框架——LangChain、AutoGen、CrewAI 这些代码级框架到底怎么选。系列进度 2/10，关注不错过后续更新。

下一篇，怕浪猫会带你进入代码级 Agent 开发的世界。LangChain 和 AutoGen 的多 Agent 协作有什么区别？CrewAI 凭什么在短短一年内成为开发者的新宠？我们下期见。

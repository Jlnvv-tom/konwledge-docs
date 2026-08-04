# 第二章：AI Agent 技术基础

构建一个能够自主完成复杂任务的 AI Agent，远不是调用一次大模型 API 那么简单。它需要理解语言的核心能力作为底座，需要检索外部知识来弥补自身局限，需要一套感知-规划-执行-反思的闭环架构，还需要记忆、工具调用和评估体系的全面支撑。本章将从底层原理出发，逐层拆解 AI Agent 的技术基础设施，为后续章节的实战内容打下坚实基础。

## 2.1 LLM 核心原理与 FDE 的知识边界

要理解 AI Agent 的能力天花板，首先需要理解 LLM (Large Language Model, 大语言模型) 的工作原理。大模型的本质是一个自回归的概率模型：给定前文的 token 序列，预测下一个 token 的概率分布。这个看似简单的"下一个词预测"任务，在海量数据和巨大参数量的加持下，涌现出了理解、推理和生成能力。

Transformer 架构是所有现代大模型的基石。其核心创新在于 Self-Attention（自注意力）机制，它让模型在处理序列中的每个位置时，能够同时关注序列中所有其他位置的信息，打破了 RNN (Recurrent Neural Network, 循环神经网络) 的顺序计算瓶颈。

Self-Attention 的计算公式如下：

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```

其中 Q (Query)、K (Key)、V (Value) 分别由输入向量乘以不同的权重矩阵得到，d_k 是 Key 向量的维度，sqrt(d_k) 起到缩放作用，防止点积结果过大导致 softmax 梯度消失。

以下是 Self-Attention 的简化代码实现：

```python
import torch
import torch.nn.functional as F
import math

def self_attention(x, W_q, W_k, W_v):
    Q = x @ W_q  # (batch, seq_len, d_k)
    K = x @ W_k  # (batch, seq_len, d_k)
    V = x @ W_v  # (batch, seq_len, d_v)

    d_k = K.size(-1)
    scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)
    attn_weights = F.softmax(scores, dim=-1)
    output = attn_weights @ V

    return output, attn_weights
```

理解这个公式的意义在于：它揭示了 LLM 的核心能力来源——动态的、基于内容的全局信息聚合。每个 token 都可以通过注意力机制"看到"序列中的所有其他 token，并根据内容相关性分配权重。多头注意力 (Multi-Head Attention) 进一步增强了这一能力，让模型能同时从不同的表示子空间中捕捉信息。

然而，LLM 的能力边界也是清晰的。FDE (Foundation Model-Driven Engineering, 基础模型驱动的工程) 领域的从业者需要深刻理解以下局限：

| 能力维度 | LLM 的表现 | 局限原因 |
|---------|-----------|---------|
| 事实准确性 | 可能产生幻觉 (Hallucination) | 训练数据中事实与非事实混合存储，无显式事实校验 |
| 时效性 | 知识停留在训练截止日期 | 自回归生成依赖训练数据，无法主动获取新信息 |
| 数学推理 | 复杂多步推理易出错 | 符号推理能力有限，依赖模式匹配而非真正的逻辑推演 |
| 长程依赖 | 超长上下文注意力衰减 | 虽支持长上下文窗口，但有效注意力随距离衰减 |
| 领域专精 | 通用能力强，垂直领域深度不足 | 训练数据中专业语料占比有限 |

对于 FDE 从业者而言，关键不是追问"大模型能不能做某件事"，而是理解它在哪些场景下可靠、在哪些场景下需要外部辅助。这正是 RAG (Retrieval-Augmented Generation, 检索增强生成)、Function Calling（函数调用）和 Agent 架构存在的价值——它们共同构成了 LLM 能力边界的扩展层。

大模型的另一个重要特性是 In-Context Learning（上下文学习）。模型能够根据提示词中提供的少量示例，快速适应新的任务模式，而无需更新权重。这一能力是 Agent 能够通过提示工程实现复杂行为的基础。但需要注意，上下文学习的效果与任务复杂度、示例质量和模型规模密切相关，并非万能。

Token 限制是另一个需要关注的技术约束。每个模型都有最大上下文窗口大小，例如 GPT-4 Turbo 支持 128K tokens，Claude 3 支持 200K tokens。在 Agent 场景中，系统提示、历史对话、工具调用结果和检索文档都会消耗 token 预算，合理的 token 管理是 Agent 工程的必修课。

此外，温度 (Temperature) 和 Top-P 采样参数对 Agent 行为有显著影响。温度越高，生成结果越发散但可能偏离事实；温度越低，输出越确定但可能缺乏创造性。在 Agent 场景中，通常将温度设为较低值（0 到 0.3），以确保工具调用和推理过程的确定性。而在创意写作或头脑风暴场景中，可以适当提高温度。

理解 LLM 的训练流程也有助于把握其能力特点。现代大模型的训练通常分为三个阶段：预训练 (Pre-training) 阶段在海量无标注文本上进行下一词预测，学习语言的通用表示；SFT (Supervised Fine-Tuning, 监督微调) 阶段使用高质量的指令-响应对训练模型遵循指令；RLHF (Reinforcement Learning from Human Feedback, 基于人类反馈的强化学习) 阶段通过奖励模型优化生成质量，使输出更符合人类偏好。这三个阶段共同塑造了 LLM 的能力边界和行为风格。

## 2.2 主流大模型 API 调用实践与参数选择

在实际开发中，与 LLM 的交互主要通过 API 完成。当前主流的 API 调用方式虽然在细节上各有差异，但核心参数高度一致。理解这些参数的含义和选择策略，是 Agent 开发的基本功。

以下是主流大模型 API 的关键参数对比：

| 参数 | OpenAI (GPT-4) | Anthropic (Claude) | 说明 |
|------|-----------------|---------------------|------|
| model | gpt-4o / gpt-4-turbo | claude-3-5-sonnet | 指定模型版本 |
| temperature | 0-2, 默认 1.0 | 0-1, 默认 1.0 | 控制输出随机性 |
| max_tokens | 最大输出长度 | 最大输出长度 | 限制生成长度 |
| top_p | 0-1, 默认 1.0 | 0-1, 默认 1.0 | 核采样，限制候选词范围 |
| frequency_penalty | -2 到 2 | 不支持 | 惩罚高频词 |
| presence_penalty | -2 到 2 | 不支持 | 鼓励引入新话题 |
| stop | 停止序列 | 停止序列 | 遇到指定字符串时停止生成 |
| stream | 流式输出 | 流式输出 | 逐 token 返回结果 |

一个典型的 API 调用示例如下：

```python
import openai

client = openai.OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个专业的代码分析助手。"},
        {"role": "user", "content": "解释 Python 装饰器的原理。"}
    ],
    temperature=0.2,
    max_tokens=2048,
    top_p=0.9,
    stream=False
)

print(response.choices[0].message.content)
```

参数选择需要根据具体场景灵活调整。以下是不同场景下的推荐参数配置：

| 场景 | temperature | top_p | max_tokens | 说明 |
|------|-------------|-------|------------|------|
| 代码生成 | 0.0-0.2 | 0.9 | 4096 | 确定性高，避免随机性引入语法错误 |
| 事实问答 | 0.0-0.3 | 0.9 | 1024 | 确保准确性，减少生成发散 |
| 创意写作 | 0.7-1.0 | 0.95 | 4096 | 鼓励多样性和创造性 |
| 数据抽取 | 0.0 | 1.0 | 2048 | 严格遵循格式，零随机性 |
| 多轮对话 | 0.5-0.7 | 0.9 | 2048 | 兼顾自然性和确定性 |
| 工具调用 | 0.0-0.1 | 1.0 | 1024 | 确保 JSON 格式正确 |

流式输出 (Streaming) 在 Agent 场景中非常重要。当模型生成较长内容时，流式输出可以让用户实时看到部分结果，显著改善体验。以下是流式调用的代码示例：

```python
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "解释 Transformer 架构。"}],
    temperature=0.3,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

Token 计费是另一个需要关注的实践问题。API 调用的费用取决于输入 token 数和输出 token 数的总和。在 Agent 场景中，随着对话轮数增加和工具调用结果累积，输入 token 会快速增长。有效的策略包括：对历史对话进行摘要压缩、对工具返回结果进行截断或摘要、使用更短的系统提示等。

上下文窗口管理是 Agent 工程中的核心挑战之一。以一个典型的 Agent 对话为例：系统提示约 500 tokens，每轮用户输入约 200 tokens，工具调用结果可能达到 1000-3000 tokens，模型推理约 500 tokens。在 10 轮交互后，上下文可能已经消耗 15000-30000 tokens。如果不做管理，很快就会触及上下文窗口上限。

常用的上下文管理策略包括滑动窗口（保留最近 N 轮对话）、摘要压缩（将旧对话摘要为简短描述）和混合策略（近期对话保留原文，早期对话用摘要替代）。这些策略的选择取决于任务对上下文完整性的敏感程度。

值得注意的是，不同模型提供商在 API 设计上正在趋同。OpenAI 的 Chat Completions API 格式已经成为事实标准，许多模型提供商（包括通过兼容层提供开源模型的平台）都采用了相同的接口格式，这为 Agent 开发者切换底层模型降低了门槛。但在实际切换时，仍需注意各模型在指令遵循能力、工具调用格式、长上下文表现等方面的差异。

## 2.3 RAG 系统搭建：从文档到知识库

RAG (Retrieval-Augmented Generation, 检索增强生成) 是解决 LLM 知识时效性和事实准确性问题的核心方案。它的基本思路是：在生成回答之前，先从外部知识库中检索相关文档片段，将其作为上下文提供给 LLM，让模型基于检索到的事实生成回答。

一个完整的 RAG 系统包含以下核心组件：

```
┌─────────────────────────────────────────────────────┐
│                   RAG 系统架构                        │
│                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │ 文档加载   │───>│ 文档分块   │───>│ Embedding 向量化│   │
│  └──────────┘    └──────────┘    └──────┬───────┘   │
│                                         │            │
│                                    ┌────▼────┐       │
│                                    │ 向量数据库 │       │
│                                    └────┬────┘       │
│                                         │            │
│  ┌──────────┐    ┌──────────┐          │            │
│  │ 用户查询   │───>│ 查询向量化 │──────────┘            │
│  └──────────┘    └──────────┘                       │
│                       │                              │
│                ┌──────▼──────┐                       │
│                │ 相似度检索    │                       │
│                └──────┬──────┘                       │
│                       │                              │
│                ┌──────▼──────┐                       │
│                │ 重排序 (Rerank)│                      │
│                └──────┬──────┘                       │
│                       │                              │
│                ┌──────▼──────┐                       │
│                │ 上下文组装    │                       │
│                └──────┬──────┘                       │
│                       │                              │
│                ┌──────▼──────┐                       │
│                │  LLM 生成    │                       │
│                └─────────────┘                       │
└─────────────────────────────────────────────────────┘
```

文档分块 (Chunking) 是 RAG 系统的第一个关键环节。分块策略直接影响检索质量。常见的分块方法包括：

| 分块策略 | 原理 | 适用场景 | 优缺点 |
|---------|------|---------|--------|
| 固定长度分块 | 按固定字符数切割 | 通用文本 | 简单但可能截断语义 |
| 递归字符分块 | 按段落-句子-字符递归切割 | 结构化文档 | 平衡性好，推荐默认策略 |
| 语义分块 | 按语义相似度切割 | 长文连贯内容 | 语义完整但计算成本高 |
| 文档结构分块 | 按 Markdown 标题/HTML 标签切割 | 结构化文档 | 保留文档结构信息 |

以下是使用 LangChain 实现文档分块和向量化的代码示例：

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 文档分块
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "，", " ", ""]
)
chunks = splitter.split_text(long_document_text)

# 向量化与存储
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_texts(
    texts=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 检索
query = "什么是 Transformer 架构?"
results = vectorstore.similarity_search_with_score(query, k=5)
```

Embedding 模型的选择对 RAG 性能至关重要。Embedding 将文本转换为高维向量，使得语义相近的文本在向量空间中距离更近。主流的 Embedding 模型包括 OpenAI 的 text-embedding-3-small/large、BGE 系列、Cohere 的 embed 系列等。选择时需要综合考虑向量维度、检索速度、多语言支持和成本。

向量数据库是 RAG 系统的存储核心。以下是主流向量数据库的对比：

| 向量数据库 | 类型 | 特点 | 适用规模 |
|-----------|------|------|---------|
| Chroma | 嵌入式 | 轻量易用，无需部署 | 原型开发，百万级向量 |
| FAISS | 库 | 高性能，Facebook 开源 | 本地部署，亿级向量 |
| Milvus | 分布式 | 云原生，支持大规模 | 生产环境，十亿级向量 |
| Pinecone | 云服务 | 全托管，免运维 | 生产环境，快速上线 |
| Weaviate | 开源 | 内置多模态支持 | 需要多模态检索的场景 |
| Qdrant | 开源 | Rust 实现，高性能 | 对延迟敏感的生产场景 |

检索质量优化是 RAG 系统持续迭代的核心。基础的向量相似度检索（余弦相似度或内积）往往不足以满足精确检索的需求。以下是一些进阶优化策略：

混合检索 (Hybrid Search) 结合了稀疏检索 (BM25 等关键词匹配) 和稠密检索 (向量相似度) 的优势。稀疏检索擅长精确匹配关键词和专业术语，稠密检索擅长语义层面的模糊匹配。两者的结合可以显著提升召回率。

重排序 (Reranking) 是另一个关键优化。第一阶段检索召回较多候选文档（如 top-20），第二阶段使用更精确但更慢的模型（如 Cross-Encoder）对候选文档重新打分排序，取 top-5 作为最终上下文。这种两阶段策略兼顾了效率和精度。

以下是包含重排序的 RAG 检索代码示例：

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# 混合检索：BM25 + 向量检索
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 10
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]
)

# 检索后重排序
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

compressor = CohereRerank(top_n=5)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=ensemble_retriever
)

final_docs = compression_retriever.get_relevant_documents(query)
```

上下文组装是检索到生成之间的桥梁。如何将检索到的文档片段与用户查询组合成有效的提示词，直接影响 LLM 的生成质量。一个推荐的提示词模板如下：

```
你是一个专业的问答助手。请基于以下检索到的上下文信息回答用户问题。
如果上下文中没有相关信息，请明确说明"根据现有知识库无法回答此问题"。
不要编造或推测上下文中未提及的信息。

上下文信息：
{retrieved_context}

用户问题：{user_query}

请给出准确、简洁的回答：
```

评估 RAG 系统的质量需要建立系统化的指标。RAGAS (RAG Assessment) 框架提出了几个核心评估维度：

| 评估维度 | 含义 | 计算方式 |
|---------|------|---------|
| 上下文相关性 (Context Relevance) | 检索结果与查询的相关程度 | 检索文档中相关内容占比 |
| 答案准确性 (Answer Faithfulness) | 生成答案是否忠于上下文 | 答案中可从上下文推导的陈述占比 |
| 答案相关性 (Answer Relevance) | 答案是否有效回答了问题 | 答案与问题的语义相关度 |
| 上下文召回率 (Context Recall) | 是否检索到了所有必要信息 | 相关文档被检索到的比例 |

RAG 系统的搭建不是一蹴而就的，需要持续的迭代优化。从文档预处理到分块策略调整，从 Embedding 模型选择到检索参数调优，每一个环节都有优化空间。在实际项目中，建议建立自动化的评估流水线，用标注好的问答数据集持续监控 RAG 系统的质量变化。

## 2.4 Agent 核心架构：感知、记忆、规划、执行、反思

AI Agent 之所以被称为"智能体"而非简单的"对话系统"，核心在于它具备自主完成任务的能力。一个设计良好的 Agent 需要包含五个核心组件：感知 (Perception)、记忆 (Memory)、规划 (Planning)、执行 (Execution) 和反思 (Reflection)。这五个组件构成了一个完整的认知闭环。

```
┌──────────────────────────────────────────────────────┐
│                  Agent 核心架构                        │
│                                                        │
│                   ┌─────────┐                          │
│                   │  感知模块  │<──── 外部输入            │
│                   └────┬────┘                          │
│                        │                               │
│                   ┌────▼────┐                          │
│           ┌───────│  记忆模块  │────────┐                │
│           │       └────┬────┘        │                  │
│           │            │             │                  │
│      ┌────▼────┐  ┌────▼────┐  ┌────▼────┐             │
│      │  规划模块  │<─>│  执行模块  │<─>│  反思模块  │             │
│      └─────────┘  └────┬────┘  └─────────┘             │
│                        │                               │
│                   ┌────▼────┐                          │
│                   │ 外部工具  │                          │
│                   └─────────┘                          │
└──────────────────────────────────────────────────────┘
```

感知模块负责接收和解析外部输入。对于文本对话型 Agent，感知模块主要处理自然语言文本。但在更广义的 Agent 场景中，感知模块还需要处理图像、音频、结构化数据甚至传感器信号。感知模块的核心任务是将异构输入转化为 Agent 内部统一的表示形式——通常是一段结构化的文本描述。

记忆模块是 Agent 连续性的保障。它存储历史交互、任务状态和学到的经验。记忆系统通常分为短期记忆和长期记忆。短期记忆对应当前对话的上下文窗口，存储最近的交互信息。长期记忆则持久化存储在向量数据库或其他存储系统中，可以通过语义检索调取。

规划模块是 Agent 的大脑。它接收感知模块的输入和记忆模块的上下文，决定下一步该做什么。规划能力是区分简单对话机器人和真正 Agent 的关键标志。一个好的规划模块能够将复杂目标分解为可执行的子任务序列，并在执行过程中动态调整计划。

执行模块负责将规划转化为具体行动。它调用外部工具（API、数据库、代码执行器等）完成实际任务。执行模块需要处理工具调用的参数构造、结果解析、错误处理等细节，并将执行结果反馈给规划模块和反思模块。

反思模块是 Agent 自我进化的关键。它在每次行动后评估结果是否达到预期，分析失败原因，并将学到的经验存储到记忆中供未来使用。反思模块让 Agent 具备了从错误中学习的能力，而不仅仅是按预设逻辑执行。

以下是一个简化但完整的 Agent 架构代码框架：

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class AgentState:
    goal: str
    observations: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)
    memory: List[Dict] = field(default_factory=list)
    reflections: List[str] = field(default_factory=list)
    step: int = 0
    finished: bool = False

class Agent:
    def __init__(self, llm_client, tools: dict):
        self.llm = llm_client
        self.tools = tools

    def perceive(self, state: AgentState, raw_input: str):
        state.observations.append(raw_input)

    def plan(self, state: AgentState):
        prompt = self._build_plan_prompt(state)
        response = self.llm.generate(prompt)
        state.plan = self._parse_plan(response)

    def execute(self, state: AgentState):
        action = state.plan[state.step]
        if action["type"] == "tool":
            tool = self.tools[action["tool_name"]]
            result = tool(**action["args"])
            state.observations.append(f"Tool result: {result}")
        elif action["type"] == "finish":
            state.finished = True

    def reflect(self, state: AgentState):
        prompt = self._build_reflection_prompt(state)
        reflection = self.llm.generate(prompt)
        state.reflections.append(reflection)
        state.memory.append({
            "step": state.step,
            "reflection": reflection
        })

    def run(self, state: AgentState, raw_input: str):
        self.perceive(state, raw_input)
        while not state.finished:
            self.plan(state)
            self.execute(state)
            self.reflect(state)
            state.step += 1
```

这个框架虽然简化，但完整展示了 Agent 的五模块闭环。实际生产中的 Agent 会在每个模块中加入更多逻辑：感知模块会做意图识别和实体提取；记忆模块会做摘要压缩和重要性筛选；规划模块会支持多种推理范式；执行模块会做并发调用和错误重试；反思模块会做质量评估和策略调整。

组件之间的通信机制也是架构设计的重要部分。一种常见模式是使用消息总线 (Message Bus) 进行组件解耦：每个组件订阅它关心的消息类型，处理后将结果发布到总线上。这种架构的好处是组件可以独立演进，新增组件只需订阅相关消息即可。

另一种模式是中心化的状态管理：维护一个全局的 Agent 状态对象，所有组件读写同一个状态。这种方式实现简单，适合中小规模 Agent，但在复杂场景下可能出现状态竞争问题。

无论采用哪种架构，核心原则是：五个模块必须形成闭环。感知触发规划，规划驱动执行，执行产生结果，反思评估结果并更新记忆，记忆反过来影响下一次感知和规划。缺少任何一个环节，Agent 的能力都会大打折扣。

## 2.5 ReAct vs Plan-and-Execute：推理范式对比

Agent 的推理范式决定了它如何思考和行动。当前最主流的两种推理范式是 ReAct (Reasoning and Acting) 和 Plan-and-Execute（规划后执行）。它们代表了不同的设计哲学，各有适用场景。

ReAct 范式的核心思想是"边想边做"。Agent 在每一步都经历 Thought-Action-Observation 的循环：先思考当前状态和下一步该做什么 (Thought)，然后执行一个动作 (Action)，观察动作结果 (Observation)，再基于观察结果思考下一步。这种模式紧密耦合了推理和行动，让 Agent 能够根据实时反馈灵活调整策略。

以下是 ReAct 范式的代码示例：

```python
REACT_PROMPT = """
请使用以下格式回答问题：

Thought: 思考你下一步该做什么
Action: 要执行的工具名称
Action Input: 工具的输入参数

当你获得足够信息后，使用：
Thought: 我已经获得了足够的信息来回答问题
Final Answer: 最终答案

可用工具：{tool_descriptions}

问题：{question}

{agent_scratchpad}
"""

def react_agent(llm, tools, question, max_steps=10):
    scratchpad = ""
    for step in range(max_steps):
        prompt = REACT_PROMPT.format(
            tool_descriptions=format_tools(tools),
            question=question,
            agent_scratchpad=scratchpad
        )
        response = llm.generate(prompt)

        if "Final Answer:" in response:
            return response.split("Final Answer:")[1].strip()

        action, action_input = parse_action(response)
        if action in tools:
            observation = tools[action](action_input)
            scratchpad += f"\n{response}\nObservation: {observation}\n"
        else:
            scratchpad += f"\n{response}\nObservation: 工具不存在\n"

    return "达到最大步数限制，未能完成任务。"
```

Plan-and-Execute 范式则采用"先规划后执行"的策略。Agent 首先将复杂任务分解为一个有序的子任务计划，然后逐步执行每个子任务。在执行过程中如果发现计划不合理，可以触发重新规划。这种模式的优势在于全局视野更好，适合需要多步骤且步骤间有依赖关系的复杂任务。

以下是 Plan-and-Execute 范式的代码示例：

```python
PLAN_PROMPT = """
你是一个任务规划器。请将以下任务分解为具体的子任务步骤。
每个步骤应该是一个清晰的、可执行的动作。

任务：{task}

可用工具：{tool_descriptions}

请输出子任务列表（JSON 格式）：
[{{"step": 1, "action": "...", "tool": "...", "input": "..."}}, ...]
"""

EXECUTE_PROMPT = """
你是一个任务执行器。请执行以下子任务，基于已有信息给出结果。

原始任务：{task}
已完成步骤：{completed_steps}
当前步骤：{current_step}
可用工具：{tool_descriptions}

请执行当前步骤并给出结果：
"""

def plan_and_execute_agent(llm, tools, task, max_replans=3):
    plan = llm.generate(PLAN_PROMPT.format(
        task=task,
        tool_descriptions=format_tools(tools)
    ))
    steps = json.loads(plan)

    completed = []
    for i, step in enumerate(steps):
        if step["tool"] in tools:
            result = tools[step["tool"]](step["input"])
        else:
            result = llm.generate(EXECUTE_PROMPT.format(
                task=task,
                completed_steps=completed,
                current_step=step,
                tool_descriptions=format_tools(tools)
            ))

        completed.append({"step": step, "result": result})

        # 检查是否需要重新规划
        if needs_replan(result, steps[i:]):
            new_plan = replan(llm, task, completed, tools)
            steps = steps[:i+1] + json.loads(new_plan)

    return completed
```

两种范式的对比如下：

| 对比维度 | ReAct | Plan-and-Execute |
|---------|-------|------------------|
| 规划方式 | 每步即时决策 | 一次性全局规划 |
| 适应能力 | 强，每步可根据反馈调整 | 弱，需要显式触发重规划 |
| 全局视野 | 弱，容易陷入局部最优 | 强，能看到任务全貌 |
| Token 消耗 | 较高，每步都带完整上下文 | 较低，执行阶段上下文较短 |
| 适用任务 | 探索性强、步骤不确定的任务 | 步骤明确、有依赖关系的任务 |
| 错误恢复 | 自然，每步都在评估 | 需要额外的重规划机制 |
| 实现复杂度 | 简单 | 中等 |
| 延迟 | 首步延迟低 | 首步延迟高（需要先完成规划） |

在实际应用中，两种范式并非互斥。一种常见的混合策略是：对于复杂任务，先用 Plan-and-Execute 生成全局计划，然后在执行每个子任务时使用 ReAct 模式进行灵活处理。这样既保留了全局视野，又具备局部适应能力。

另一个值得关注的范式是 Reflexion（反思范式）。它在 ReAct 的基础上增加了显式的自我反思环节：每次执行失败后，Agent 会生成一段反思总结，记录失败原因和改进策略，并在下一次尝试时将反思纳入上下文。这种"失败-反思-重试"的循环让 Agent 具备了从错误中学习的能力。

选择推理范式时，需要综合考虑任务特征、延迟要求、Token 预算和可靠性需求。没有一种范式在所有场景下都是最优的，理解它们的设计哲学和适用边界比记住代码模板更重要。

## 2.6 Function Calling 与工具调用机制

Function Calling（函数调用）是 LLM 从"对话助手"进化为"行动者"的关键能力。它允许模型根据用户意图，自主决定调用哪个函数、传入什么参数，并将函数返回结果整合到后续推理中。

Function Calling 的工作流程如下：

```
用户请求 ──> LLM 分析意图
                │
                ▼
         生成函数调用 (JSON)
                │
                ▼
         执行函数获取结果
                │
                ▼
         将结果返回 LLM
                │
                ▼
         LLM 生成最终回答
```

OpenAI Function Calling 的 JSON 格式是最广泛使用的标准。开发者通过 tools 参数向模型声明可用函数，模型在需要时返回函数调用请求：

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "城市名称，如'北京'"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "温度单位"
            }
          },
          "required": ["city"]
        }
      }
    }
  ]
}
```

当模型决定调用函数时，响应中会包含函数调用信息：

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"北京\", \"unit\": \"celsius\"}"
      }
    }
  ]
}
```

以下是完整的 Function Calling 代码示例：

```python
import openai
import json

client = openai.OpenAI(api_key="your-api-key")

# 定义可用工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "在数据库中搜索信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回结果数量"}
                },
                "required": ["query"]
            }
        }
    }
]

# 定义函数实现
def search_database(query: str, limit: int = 5) -> str:
    # 实际场景中这里执行数据库查询
    return json.dumps({"results": [f"结果{i}: {query}" for i in range(limit)]})

# Agent 对话循环
messages = [
    {"role": "system", "content": "你是一个数据分析助手。"},
    {"role": "user", "content": "帮我搜索数据库中关于'销售报告'的信息，返回3条结果。"}
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# 处理函数调用
message = response.choices[0].message
if message.tool_calls:
    messages.append(message)
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        # 执行函数
        if func_name == "search_database":
            result = search_database(**func_args)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    # 将结果返回给模型生成最终回答
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools
    )
    print(final_response.choices[0].message.content)
```

函数描述 (description) 的质量直接影响模型的调用准确性。一个好的描述应该清楚说明函数的用途、适用场景和限制条件。参数描述同样重要，需要说明参数的含义、格式、取值范围和默认行为。

Parallel Function Calling（并行函数调用）是近年新增的重要能力。模型可以在一次响应中同时请求调用多个函数，这些函数没有依赖关系时可以并行执行，显著减少总延迟。需要注意的是，不同模型对并行函数调动的支持程度不同，使用前需要查阅文档确认。

工具选择策略 (tool_choice) 也是一个实用参数。"auto" 让模型自主决定是否调用工具，"none" 禁止工具调用，"required" 强制必须调用工具，还可以指定特定函数名强制调用。在 Agent 场景中，通常使用 "auto" 给模型最大灵活性，但在特定流程中可以强制工具调用来保证执行路径。

错误处理是工具调用中容易被忽视的环节。当函数执行失败时，不应该简单地向用户报告错误，而应该将错误信息以结构化的方式返回给模型，让模型决定是重试、换一种方式还是向用户解释失败原因。这种"将错误交给模型处理"的策略让 Agent 具备了更强的鲁棒性。

## 2.7 MCP 协议：工具生态的标准化

随着 Agent 工具数量的增长，一个突出的问题是：每个 Agent 框架都有自己的工具定义格式和接入方式，开发者需要为不同框架重复编写工具适配代码。MCP (Model Context Protocol, 模型上下文协议) 正是为了解决这一工具生态碎片化问题而生的标准化协议。

MCP 由三个核心概念组成：Host（宿主）、Client（客户端）和 Server（服务端）。Host 是运行 Agent 的应用程序，Client 是 Host 中负责与 Server 通信的组件，Server 是提供具体工具能力的独立进程。

```
┌──────────────────────────────────────────────────┐
│                  MCP 架构                          │
│                                                    │
│  ┌─────────────────────────────────┐               │
│  │          Host (Agent 应用)       │               │
│  │                                  │               │
│  │  ┌──────────┐  ┌──────────┐    │               │
│  │  │ MCP Client│  │ MCP Client│    │               │
│  │  └─────┬────┘  └─────┬────┘    │               │
│  └────────┼─────────────┼──────────┘               │
│           │             │                           │
│      stdio/SSE     stdio/SSE                        │
│           │             │                           │
│  ┌────────▼────┐ ┌──────▼─────┐                   │
│  │ MCP Server A │ │ MCP Server B│                   │
│  │  (文件系统)   │ │  (数据库)    │                   │
│  │              │ │             │                   │
│  │ - read_file  │ │ - query     │                   │
│  │ - write_file │ │ - insert    │                   │
│  │ - list_dir   │ │ - update    │                   │
│  └──────────────┘ └─────────────┘                   │
└──────────────────────────────────────────────────┘
```

MCP 协议定义了三类核心能力：

| 能力类型 | 说明 | 示例 |
|---------|------|------|
| Tools (工具) | 可被模型调用的函数 | 搜索、查询、计算、文件操作 |
| Resources (资源) | 可被读取的数据源 | 文件内容、数据库记录、API 数据 |
| Prompts (提示模板) | 预定义的提示词模板 | 代码审查模板、文档总结模板 |

MCP Server 的实现通常基于 JSON-RPC 2.0 协议，通过 stdio 或 SSE (Server-Sent Events) 进行通信。以下是一个简化的 MCP Server 定义示例：

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-tools-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculate",
            description="执行数学计算",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2+3*4'"
                    }
                },
                "required": ["expression"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "calculate":
        try:
            result = eval(arguments["expression"])
            return [TextContent(type="text", text=f"结果: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"错误: {str(e)}")]
```

MCP 的价值在于其标准化带来的生态效应。一旦开发者将某个工具封装为 MCP Server，任何支持 MCP 协议的 Agent 框架都可以直接使用它，无需重复适配。这极大降低了工具开发和复用的成本。

MCP Server 的传输层设计也值得一提。stdio 传输适用于本地工具（如文件系统操作），Client 和 Server 在同一机器上通过标准输入输出通信。SSE/HTTP 传输适用于远程工具（如云服务 API），支持跨网络调用。这种灵活的传输层设计让 MCP 既能胜任本地开发场景，也能支撑分布式部署。

在工具发现机制方面，MCP 支持动态发现。Client 连接 Server 后可以动态列举可用的工具列表，而不需要提前硬编码。这意味着 Agent 可以在运行时根据需要连接新的 MCP Server，动态扩展自己的能力边界。

工具权限控制是 MCP 在安全层面的重要特性。Host 可以配置哪些 MCP Server 允许连接、哪些工具允许调用、调用前是否需要用户确认。这在生产环境中尤为重要——你不希望 Agent 自主调用一个删除文件的工具而不经过任何确认。

## 2.8 Agent 记忆系统设计与持久化

记忆系统是 Agent 从"一次性对话"走向"持续协作"的关键。人类依靠记忆来保持经验的连续性，Agent 同样需要记忆系统来存储历史交互、学到的知识和积累的经验。

Agent 的记忆系统通常分为三个层次：

| 记忆类型 | 类比 | 存储方式 | 访问方式 | 生命周期 |
|---------|------|---------|---------|---------|
| 工作记忆 (Working Memory) | 短期记忆 | 上下文窗口 | 直接访问 | 单次对话 |
| 情景记忆 (Episodic Memory) | 事件记忆 | 向量数据库 | 语义检索 | 跨会话 |
| 语义记忆 (Semantic Memory) | 知识库 | 知识图谱/文档库 | 查询检索 | 永久 |

工作记忆对应 LLM 的上下文窗口，存储当前对话的历史信息。它的容量受限于模型的 token 限制，需要通过摘要和压缩来管理。

情景记忆存储 Agent 过去的交互经历，包括用户请求、Agent 行为、执行结果和反思总结。当 Agent 遇到类似任务时，可以从情景记忆中检索相关经验来指导当前行为。

语义记忆存储 Agent 从交互中学到的结构化知识。与情景记忆不同，语义记忆是提炼后的通用知识，不绑定到特定事件。例如，Agent 从多次代码调试经验中总结出"Python 中 NameError 通常是由变量名拼写错误引起"这样的通用知识。

以下是记忆系统的代码实现示例：

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class MemoryItem:
    content: str
    memory_type: str  # "episodic" or "semantic"
    timestamp: str
    importance: float  # 0-1, 重要程度
    metadata: dict

class AgentMemory:
    def __init__(self, vectorstore, llm):
        self.vectorstore = vectorstore
        self.llm = llm
        self.working_memory: list = []

    def add_to_working_memory(self, item: str):
        """添加到工作记忆（当前对话上下文）"""
        self.working_memory.append(item)

    def add_episodic_memory(self, content: str,
                            importance: float = 0.5,
                            metadata: dict = None):
        """添加情景记忆"""
        memory = MemoryItem(
            content=content,
            memory_type="episodic",
            timestamp=datetime.now().isoformat(),
            importance=importance,
            metadata=metadata or {}
        )
        self.vectorstore.add_texts(
            texts=[json.dumps(memory.__dict__)],
            metadatas=[{"type": "episodic", "importance": importance}]
        )

    def add_semantic_memory(self, content: str,
                            importance: float = 0.8):
        """添加语义记忆（提炼后的知识）"""
        memory = MemoryItem(
            content=content,
            memory_type="semantic",
            timestamp=datetime.now().isoformat(),
            importance=importance,
            metadata={}
        )
        self.vectorstore.add_texts(
            texts=[json.dumps(memory.__dict__)],
            metadatas=[{"type": "semantic", "importance": importance}]
        )

    def retrieve(self, query: str, k: int = 5,
                 memory_type: str = None) -> list:
        """检索相关记忆"""
        filter_dict = {"type": memory_type} if memory_type else {}
        results = self.vectorstore.similarity_search(
            query, k=k, filter=filter_dict
        )
        return results

    def consolidate(self):
        """记忆巩固：从工作记忆中提炼语义记忆"""
        if not self.working_memory:
            return

        prompt = f"""
        请从以下交互记录中提炼出可复用的通用知识。
        只输出确实有价值的通用结论，不要记录具体事件细节。

        交互记录：
        {chr(10).join(self.working_memory)}

        提炼的知识（每行一条）：
        """
        knowledge = self.llm.generate(prompt)

        for line in knowledge.strip().split("\n"):
            if line.strip():
                self.add_semantic_memory(line.strip())

        # 清空工作记忆
        self.working_memory.clear()
```

记忆的重要性评估是记忆系统设计的核心问题。不是所有的交互都值得长期存储。一种有效的策略是让 LLM 对每次交互进行重要性评分（0-1），只有重要性超过阈值的记忆才会被持久化。重要性的判断标准包括：任务是否成功完成、是否涉及新的知识或技能、是否包含失败教训等。

记忆遗忘机制同样重要。无限制地积累记忆会导致检索质量下降（噪声增加）和存储成本上升。一种策略是定期对低重要性记忆进行"遗忘"——降低其检索权重或直接删除。另一种策略是记忆合并：将多条相关的细粒度记忆合并为一条粗粒度的总结性记忆。

记忆巩固 (Memory Consolidation) 是受人类睡眠期间记忆整理机制启发的技术。Agent 在空闲时回顾近期的工作记忆，将其中有价值的经验提炼为语义记忆，并清理或合并冗余信息。这个过程类似于人类的"反思总结"，是 Agent 持续进化的重要机制。

持久化存储的设计需要考虑数据模型。一个推荐的数据模型包含以下字段：记忆 ID、内容、类型、时间戳、重要性分数、来源（哪个任务或对话产生）、标签（便于分类检索）和向量嵌入。使用支持向量检索和元数据过滤的数据库（如 Chroma、Qdrant）可以同时满足语义检索和精确过滤的需求。

## 2.9 Agent 质量评估体系

没有评估就没有改进。Agent 的质量评估比传统软件复杂得多，因为 Agent 的行为具有非确定性——同样的输入可能产生不同的输出。建立系统化的评估体系是 Agent 从原型走向生产的必经之路。

Agent 评估可以从以下几个维度展开：

| 评估维度 | 评估对象 | 关键指标 | 评估方法 |
|---------|---------|---------|---------|
| 任务完成率 | 整体能力 | 成功率、完成时间、步骤数 | 端到端测试集 |
| 推理质量 | 规划能力 | 计划合理性、错误恢复率 | 专家评审 + LLM 评审 |
| 工具使用 | 执行能力 | 工具选择准确率、参数正确率 | 调用日志分析 |
| 响应质量 | 生成能力 | 准确性、相关性、完整性 | 标注对比 + LLM 评审 |
| 效率 | 资源消耗 | Token 使用量、API 调用次数 | 日志统计 |
| 鲁棒性 | 健壮性 | 异常处理率、边界条件通过率 | 对抗测试 |

任务完成率是最直接的评估指标。构建一个包含多样化任务的测试集，统计 Agent 在每个任务上的成功率。任务集应该覆盖不同难度、不同类型（信息检索、代码生成、数据分析、多步推理等）和不同领域。测试集的构建可以参考以下结构：

```python
@dataclass
class TestCase:
    task_id: str
    description: str           # 任务描述
    difficulty: str            # easy / medium / hard
    category: str              # retrieval / coding / reasoning / etc.
    expected_outcome: str      # 期望结果
    evaluation_method: str     # exact_match / contains / llm_judge / human
    max_steps: int             # 最大允许步数
    tools_available: list      # 可用工具列表

@dataclass
class TestResult:
    task_id: str
    success: bool
    steps_taken: int
    tokens_used: int
    time_elapsed: float
    error_type: str            # failure category
    agent_trace: list          # 完整执行轨迹
```

LLM-as-Judge（用 LLM 做评审）是当前实践中广泛采用的评估方法。使用一个更强的模型（如 GPT-4）来评审目标 Agent 的输出质量。评审提示词需要精心设计，包含明确的评分标准、评分尺度和示例：

```python
JUDGE_PROMPT = """
你是一个严格的评审员。请评估以下 Agent 的回答质量。

评审标准（每项 1-5 分）：
1. 准确性 (Accuracy)：回答是否事实正确，有无编造信息
2. 完整性 (Completeness)：回答是否覆盖了问题的所有方面
3. 相关性 (Relevance)：回答是否紧扣问题，无多余内容
4. 可操作性 (Actionability)：回答是否提供了可执行的建议
5. 清晰度 (Clarity)：回答是否结构清晰，易于理解

用户问题：{question}
Agent 回答：{answer}
参考答案：{reference}

请给出每项的分数和理由，然后计算平均分。
"""
```

端到端测试 (E2E Testing) 是评估 Agent 整体能力的最终手段。与单元测试不同，端到端测试关注 Agent 从接收输入到产生最终输出的完整流程。一个好的端到端测试框架应该能够：自动化执行测试用例、捕获完整的执行轨迹、支持多种评估方法、生成可视化的评估报告。

轨迹分析 (Trace Analysis) 是诊断 Agent 问题的有效手段。通过分析 Agent 的完整执行轨迹（包括每一步的思考、行动和观察），可以定位问题发生在哪个环节：是规划错误（选择了错误的策略）、工具调用错误（参数构造不正确）、还是推理错误（从观察中得出了错误结论）。

回归测试在 Agent 迭代中至关重要。每次修改提示词、调整参数或更新工具后，都应该运行完整的测试套件，确保改动没有引入退化。由于 Agent 行为的非确定性，回归测试通常需要多次运行取统计结果，而不是单次运行判断通过/失败。

持续监控 (Continuous Monitoring) 是生产环境的必备能力。上线后的 Agent 需要实时监控关键指标：任务成功率、平均完成时间、用户满意度、Token 消耗、错误率等。当指标出现异常波动时，应该触发告警以便及时处理。

## 2.10 主流开发框架选型指南

选择合适的开发框架可以大幅提升 Agent 的开发效率。当前主流的 Agent 开发框架各有侧重，理解它们的设计理念和适用场景是做出正确选型的基础。

| 框架 | 语言 | 核心理念 | 优势 | 局限 | 适用场景 |
|------|------|---------|------|------|---------|
| LangChain | Python/JS | 全功能集成 | 生态丰富、组件全面 | 抽象层重、学习曲线陡 | 快速原型、全流程开发 |
| LangGraph | Python | 图结构编排 | 状态管理清晰、支持复杂流程 | 依赖 LangChain 生态 | 复杂多步工作流 |
| LlamaIndex | Python | 数据驱动的 RAG | RAG 能力强、数据处理优秀 | Agent 能力相对弱 | 知识库密集型应用 |
| CrewAI | Python | 多 Agent 协作 | 多角色编排简单直观 | 单 Agent 场景过重 | 多 Agent 协同任务 |
| AutoGen | Python | 多 Agent 对话 | 对话式协作灵活 | 架构较重 | 研究探索、复杂协作 |
| Pydantic AI | Python | 类型安全 | 类型提示完善、开发体验好 | 生态较小 | 生产级应用、注重可靠性 |
| OpenAI Agents SDK | Python | 官方原生 | 与 OpenAI 深度集成 | 绑定 OpenAI 生态 | OpenAI 为主的项目 |
| Dify | 多语言 | 低代码平台 | 可视化编排、开箱即用 | 灵活性受限 | 非技术用户、快速搭建 |

选择框架时的关键考量因素：

第一，项目复杂度。简单的 RAG 问答系统用 LlamaIndex 即可；需要复杂多步推理的 Agent 适合用 LangGraph；多 Agent 协作场景可以考虑 CrewAI。

第二，团队能力。如果团队 Python 经验丰富，大多数框架都能快速上手；如果团队更偏向低代码方式，Dify 这类平台更合适。

第三，生态成熟度。LangChain 拥有最大的社区和最丰富的集成组件，遇到问题更容易找到解决方案。但这也意味着更高的抽象复杂度。

第四，生产可靠性。框架的稳定性、错误处理能力、并发支持、可观测性等在生产环境中至关重要。Pydantic AI 在类型安全和错误处理方面表现出色。

第五，可扩展性。当 Agent 能力需要扩展时，框架是否支持自定义组件、是否容易集成新的工具和模型。LangChain 的组件抽象设计使其在可扩展性方面表现突出。

以下是一个使用 LangGraph 构建简单 Agent 的代码示例，展示其图结构编排的特点：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_action: str

def plan_node(state: AgentState) -> AgentState:
    # 规划阶段
    messages = state["messages"]
    plan = llm.generate(f"基于以下对话制定计划：{messages}")
    return {"messages": [plan], "next_action": "execute"}

def execute_node(state: AgentState) -> AgentState:
    # 执行阶段
    messages = state["messages"]
    result = execute_action(messages[-1])
    return {"messages": [result], "next_action": "reflect"}

def reflect_node(state: AgentState) -> AgentState:
    # 反思阶段
    messages = state["messages"]
    reflection = llm.generate(f"评估执行结果：{messages[-1]}")
    if "完成" in reflection:
        return {"messages": [reflection], "next_action": END}
    return {"messages": [reflection], "next_action": "plan"}

def should_continue(state: AgentState) -> str:
    return state["next_action"]

# 构建工作流图
workflow = StateGraph(AgentState)
workflow.add_node("plan", plan_node)
workflow.add_node("execute", execute_node)
workflow.add_node("reflect", reflect_node)

workflow.set_entry_point("plan")
workflow.add_conditional_edges("plan", should_continue)
workflow.add_conditional_edges("execute", should_continue)
workflow.add_conditional_edges("reflect", should_continue)

app = workflow.compile()
```

框架选型不是一次性的决策。在项目早期，可以用 LangChain 快速验证概念可行性；当 Agent 逻辑变复杂后，迁移到 LangGraph 获得更好的状态管理；当需要多 Agent 协作时，引入 CrewAI 的多角色编排能力。关键是要保持业务逻辑与框架的解耦，使得框架切换的成本可控。

一个实用的建议是：在项目初期，不要急于选择框架，先用原生 API 调用构建最小可用原型。当你对 Agent 的核心流程有了清晰认识后，再根据实际痛点选择框架——是需要更好的 RAG 能力（选 LlamaIndex），还是需要复杂的工作流编排（选 LangGraph），还是需要多 Agent 协作（选 CrewAI）。从问题出发选框架，而不是从框架出发找问题。

## 本章知识点总结

| 知识点 | 核心内容 | 关键要点 |
|-------|---------|---------|
| LLM 核心原理 | Self-Attention 机制、自回归生成、训练三阶段 | Attention = softmax(QK^T/sqrt(d_k))V；LLM 有事实性、时效性、推理能力等局限 |
| API 调用实践 | 参数选择、流式输出、上下文管理 | 不同场景需要不同的 temperature/top_p 配置；Token 管理是 Agent 工程的核心挑战 |
| RAG 系统 | 文档分块、向量化、检索、重排序 | 混合检索 + 重排序是提升检索质量的有效策略；RAGAS 提供系统化评估框架 |
| Agent 架构 | 感知-记忆-规划-执行-反思五模块闭环 | 五模块缺一不可；组件间通信可使用消息总线或中心化状态管理 |
| 推理范式 | ReAct (边想边做) vs Plan-and-Execute (先规划后执行) | ReAct 适应性强但全局视野弱；Plan-and-Execute 全局视野好但灵活性差；混合策略取长补短 |
| Function Calling | 工具声明、调用流程、错误处理 | 函数描述质量决定调用准确性；错误应交给模型处理而非直接报错给用户 |
| MCP 协议 | 工具生态标准化协议 | Host-Client-Server 三层架构；支持工具、资源、提示三类能力；动态发现 + 权限控制 |
| 记忆系统 | 工作记忆、情景记忆、语义记忆三层 | 重要性评估决定存储策略；记忆巩固从交互中提炼通用知识；遗忘机制防止噪声积累 |
| 评估体系 | 任务完成率、推理质量、工具使用、响应质量、效率、鲁棒性 | LLM-as-Judge 是实用的自动评估方法；轨迹分析定位问题环节；回归测试防止迭代退化 |
| 框架选型 | LangChain、LangGraph、LlamaIndex、CrewAI 等 | 从问题出发选框架；保持业务逻辑与框架解耦；先用原生 API 验证概念再选框架 |

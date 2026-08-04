# 第六章：快速开发与原型验证

## 6.1 两周交付 MVP：FDE 的极速开发法

在 Agent 项目的早期阶段，速度就是一切。市场验证不会等待完美的架构，用户反馈也不会等到所有边缘场景都被覆盖。FDE（Full-Stack Development Engineer，全栈开发工程师）在 Agent 项目中的核心职责之一，就是在极短的时间内交付可用的 MVP（Minimum Viable Product，最小可行产品），然后通过快速迭代逐步完善。

两周交付 MVP 并非一句口号，而是一套经过验证的方法论。它的核心原则是：砍掉一切非必要功能，聚焦于核心链路的端到端打通。一个 Agent 项目的核心链路通常包括：用户输入、意图识别、知识检索、模型推理、结果返回。只要这条链路能跑通，就是一个可演示的 MVP。

以下是两周 MVP 的详细计划表：

| 阶段 | 时间 | 任务 | 交付物 |
|------|------|------|--------|
| 第1天 | Day 1 | 需求分析与技术选型 | 需求文档、技术栈确定 |
| 第2天 | Day 2 | 项目脚手架搭建 | 仓库结构、CI 配置 |
| 第3-4天 | Day 3-4 | 核心链路开发（输入到输出） | 基础 API 可调通 |
| 第5天 | Day 5 | RAG 检索模块集成 | 知识库可查询 |
| 第6天 | Day 6 | Prompt 模板与模型对接 | 基础对话可用 |
| 第7天 | Day 7 | 流式输出实现 | SSE 链路打通 |
| 第8天 | Day 8 | 多轮对话上下文管理 | 连续对话可用 |
| 第9天 | Day 9 | 前端界面或 API 联调 | 可演示的界面 |
| 第10天 | Day 10 | 基础测试与 Bug 修复 | 测试通过率 > 80% |
| 第11天 | Day 11 | HITL 审批机制（如需要） | 人工审批流程可用 |
| 第12天 | Day 12 | 部署与环境配置 | Staging 环境可用 |
| 第13天 | Day 13 | 集成测试与验收测试 | 端到端测试通过 |
| 第14天 | Day 14 | 演示准备与文档 | 演示 Demo + API 文档 |

这个计划表的核心逻辑是"垂直切片"。每一阶段都产出一个可运行的增量，而不是等所有模块都开发完才组装。Day 3-4 就要跑通核心链路，哪怕只有一个硬编码的返回值。Day 5 才接入真正的 RAG 检索，Day 6 才对接真实的模型。

这种做法的好处在于风险前置。如果核心链路在第三天就跑不通，你还有十一天时间调整方案。如果等到第十二天才第一次端到端联调，发现问题后几乎没有补救时间。

极速开发法还有几个关键实践。第一是"伪实现先行"：在真实模块未就绪时，用 Mock 数据和桩函数占位，保证链路始终可运行。第二是"决策不超过一小时"：技术选型、API 设计等决策，设定一小时的时限，超时就用默认方案，避免在选型上消耗过多时间。第三是"每日构建"：每天结束时，主干分支必须处于可运行状态，任何人都能拉下来跑通。

关于代码质量，MVP 阶段的原则是"够用就好"。不要在 MVP 阶段引入复杂的微服务架构、不要设计过于抽象的接口层、不要写过多的配置文件。一个清晰的单体应用，比一堆"设计良好"但跑不起来的微服务有价值得多。代码可以不够优雅，但必须能跑、能演示、能收集反馈。

## 6.2 快速开发工具链选型

工具链选型直接决定了开发效率。在 Agent 项目中，工具链需要覆盖后端服务、前端界面、模型调用、向量检索、部署运维等多个层面。选型时要考虑团队能力、生态成熟度和开发速度三个维度。

以下是常用工具链的对比表：

| 类别 | 方案A | 方案B | 方案C | 推荐场景 |
|------|-------|-------|-------|----------|
| 后端框架 | FastAPI (Python) | Express (Node.js) | Gin (Go) | 快速原型选FastAPI |
| 前端框架 | Next.js (React) | Vue 3 | Svelte | 需要SSR选Next.js |
| LLM SDK | LangChain | LlamaIndex | 原生HTTP调用 | 简单场景用原生调用 |
| 向量数据库 | Chroma | Qdrant | Milvus | 小规模选Chroma |
| 嵌入模型 | OpenAI text-embedding | BGE-m3 | Cohere embed | 中文场景选BGE |
| 任务队列 | Celery | BullMQ | Redis Stream | Python栈选Celery |
| 部署平台 | Docker Compose | K8s | Serverless | MVP阶段选Docker |
| 监控 | LangSmith | Langfuse | 自建日志 | 预算有限选Langfuse |
| 代码管理 | Git + GitHub | GitLab | Gitea | 团队协作选GitHub |
| CI/CD | GitHub Actions | GitLab CI | Jenkins | 云原生选GitHub Actions |

在 MVP 阶段，推荐的默认技术栈是：FastAPI + Next.js + 原生 HTTP 调用 LLM + Chroma + Docker Compose。这套组合的好处是上手快、文档全、社区活跃，遇到问题容易找到解决方案。

LangChain 和 LlamaIndex 这类框架在快速原型阶段有价值，它们封装了大量常见模式，可以减少样板代码。但也有一个隐患：框架的抽象层会隐藏底层细节，当需要精细控制模型行为时，框架的封装反而成为障碍。建议在 MVP 阶段使用框架加速开发，在进入生产阶段后逐步替换为原生调用。

向量数据库的选型在 MVP 阶段不必纠结。Chroma 是一个嵌入式向量数据库，不需要单独部署服务，直接作为 Python 库使用即可。当数据量超过百万级或需要多节点部署时，再迁移到 Qdrant 或 Milvus。迁移成本主要在 API 适配层，如果代码中对向量数据库的调用做了接口抽象，迁移工作量可以控制在一天以内。

CI/CD (Continuous Integration/Continuous Deployment, 持续集成/持续部署) 在 MVP 阶段也不可省略。即使只有一个人开发，也应该配置基本的 CI 流程：代码推送时自动运行测试、Lint 检查、构建 Docker 镜像。这能在早期发现集成问题，避免"在我机器上能跑"的困境。GitHub Actions 配置简单，免费额度对 MVP 阶段足够。

关于 LLM SDK 的选择，以下是三种方式的代码复杂度对比：

```python
# 方式一：LangChain 调用
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", temperature=0.7)
response = llm.invoke("你好，请介绍一下自己")
print(response.content)

# 方式二：原生 HTTP 调用
import httpx
resp = httpx.post(
    "https://api.example.com/v1/chat/completions",
    json={"model": "gpt-4", "messages": [{"role": "user", "content": "你好"}]},
    headers={"Authorization": "Bearer sk-xxx"},
)
print(resp.json()["choices"][0]["message"]["content"])

# 方式三：轻量封装
class LLMClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(base_url=base_url)
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def chat(self, messages: list[dict], model: str = "gpt-4"):
        resp = await self.client.post("/v1/chat/completions",
            json={"model": model, "messages": messages},
            headers=self.headers)
        return resp.json()["choices"][0]["message"]["content"]
```

从代码量来看，三种方式的差异不大。但原生调用和轻量封装的优势在于完全可控，不依赖第三方框架的更新节奏。在 Agent 项目中，模型调用是最核心的环节，保持对这一环节的完全控制力是值得的。

工具链选型还有一个常被忽略的维度：本地开发体验。包括热重载、调试器支持、日志可视化等。FastAPI 的 uvicorn --reload 可以实现修改即生效，Next.js 的快速刷新也大幅提升前端开发效率。在 MVP 阶段，每天节省的调试和等待时间累积起来是相当可观的。

## 6.3 标准 RAG 开发模板与代码

RAG (Retrieval-Augmented Generation, 检索增强生成) 是 Agent 项目中最基础也最常见的架构模式。它的核心思想是：在生成回答之前，先从知识库中检索相关文档，将检索结果作为上下文输入给 LLM，从而让模型的回答基于事实而非纯粹的参数化知识。

一个标准的 RAG 流程包含四个阶段：文档处理、向量索引、检索召回、生成回答。每个阶段都有需要解决的问题和可选择的方案。下面展示一个完整的 RAG 开发模板代码。

首先是文档处理模块。这个模块负责将原始文档（PDF、Markdown、TXT 等）转换为统一的文本块：

```python
from pathlib import Path
from dataclasses import dataclass

@dataclass
class TextChunk:
    content: str
    source: str
    chunk_id: str
    metadata: dict

def load_and_chunk(file_path: str, chunk_size: int = 500,
                   overlap: int = 50) -> list[TextChunk]:
    """加载文档并分块"""
    text = Path(file_path).read_text(encoding="utf-8")
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk_text = text[i:i + chunk_size]
        if len(chunk_text.strip()) < 20:
            continue
        chunks.append(TextChunk(
            content=chunk_text,
            source=file_path,
            chunk_id=f"{Path(file_path).stem}_{i// (chunk_size - overlap)}",
            metadata={"file": file_path, "offset": i},
        ))
    return chunks
```

分块策略对 RAG 的效果有显著影响。固定长度分块是最简单的策略，但会破坏语义完整性。更优的策略是基于段落或标题进行语义分块。在实际项目中，建议先用固定长度分块跑通流程，再根据效果优化分块策略。

接下来是向量索引模块。这里使用 Chroma 作为向量数据库：

```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, persist_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[TextChunk], embeddings: list[list[float]]):
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            documents=[c.content for c in chunks],
            metadatas=[c.metadata for c in chunks],
            embeddings=embeddings,
        )

    def query(self, query_embedding: list[float], top_k: int = 5):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        return results
```

检索召回模块负责将用户问题转换为向量，并从向量数据库中检索相关文档：

```python
class Retriever:
    def __init__(self, vector_store: VectorStore, embed_model):
        self.store = vector_store
        self.embed_model = embed_model

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = await self.embed_model.embed(query)
        results = self.store.query(embedding, top_k=top_k)
        return [
            {"content": doc, "source": meta.get("file", "unknown"),
             "score": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
```

最后是生成回答模块，将检索结果与用户问题组合成 Prompt，调用 LLM 生成回答：

```python
class RAGGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate(self, query: str, retrieved_docs: list[dict]) -> str:
        context = "\n\n".join(
            f"[文档{i+1}] {doc['content']}" for i, doc in enumerate(retrieved_docs)
        )
        messages = [
            {"role": "system", "content": (
                "你是一个知识助手。根据以下检索到的文档内容回答用户问题。"
                "如果文档中没有相关信息，请如实告知。\n\n"
                f"参考文档：\n{context}"
            )},
            {"role": "user", "content": query},
        ]
        return await self.llm.chat(messages)
```

将以上模块组装成完整的 RAG Pipeline：

```python
class RAGPipeline:
    def __init__(self, retriever: Retriever, generator: RAGGenerator):
        self.retriever = retriever
        self.generator = generator

    async def answer(self, query: str, top_k: int = 5) -> dict:
        docs = await self.retriever.retrieve(query, top_k=top_k)
        answer = await self.generator.generate(query, docs)
        return {"answer": answer, "sources": docs}
```

这个模板覆盖了 RAG 的核心流程，但还有大量可以优化的空间。比如查询重写（Query Rewriting）：用户的原始提问可能表述不清，可以先让 LLM 将问题重写为更适合检索的形式。再比如混合检索（Hybrid Search）：将向量检索与关键词检索结合，提升召回率。还有重排序（Reranking）：对检索结果用更精细的模型进行二次排序，提高前几条结果的相关性。

以下是 RAG 优化策略的效果对比：

| 优化策略 | 实现复杂度 | 效果提升 | 适用场景 |
|---------|-----------|---------|---------|
| 查询重写 | 低 | 中 | 用户提问模糊 |
| 混合检索 | 中 | 高 | 专业领域知识库 |
| 重排序 | 中 | 高 | 对精度要求高 |
| 多路召回 | 中 | 中 | 需要高召回率 |
| 上下文压缩 | 低 | 中 | 文档过长导致Token超限 |
| 自适应分块 | 高 | 高 | 文档结构复杂 |

在 MVP 阶段，建议先使用基础的 RAG 模板跑通流程，然后根据实际效果逐步引入优化策略。过早优化会增加系统复杂度，拖慢交付速度。

## 6.4 Agent 工具调用框架搭建

Agent 与普通 LLM 应用的本质区别在于：Agent 能够自主调用工具来完成任务。工具调用（Tool Calling / Function Calling）是 Agent 的核心能力。搭建一个灵活可扩展的工具调用框架，是 Agent 开发的关键环节。

一个完善的工具调用框架需要解决以下问题：工具注册与发现、参数校验、执行调度、错误处理、结果解析。以下是框架的核心代码：

```python
import json
from typing import Callable, Any
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema
    handler: Callable

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str,
                 parameters: dict, handler: Callable):
        self._tools[name] = ToolDefinition(
            name=name, description=description,
            parameters=parameters, handler=handler,
        )

    def get_definitions(self) -> list[dict]:
        return [
            {"type": "function", "function": {
                "name": t.name, "description": t.description,
                "parameters": t.parameters,
            }}
            for t in self._tools.values()
        ]

    def get_handler(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name].handler
```

工具注册器是整个框架的核心。它维护一个工具名称到定义的映射，并能为 LLM 提供工具描述（遵循 OpenAI Function Calling 的格式）。以下是工具定义的示例：

```python
registry = ToolRegistry()

# 注册搜索工具
registry.register(
    name="web_search",
    description="搜索互联网获取最新信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
    handler=web_search_handler,
)

# 注册计算器工具
registry.register(
    name="calculator",
    description="执行数学计算",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式"},
        },
        "required": ["expression"],
    },
    handler=calculator_handler,
)
```

Agent 的执行循环是框架的另一个关键部分。它负责与 LLM 交互、解析工具调用请求、执行工具、将结果返回给 LLM，直到 LLM 不再需要调用工具：

```python
class AgentExecutor:
    def __init__(self, llm_client, registry: ToolRegistry,
                 max_iterations: int = 10):
        self.llm = llm_client
        self.registry = registry
        self.max_iterations = max_iterations

    async def run(self, user_message: str,
                  system_prompt: str = "") -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        tools = self.registry.get_definitions()

        for i in range(self.max_iterations):
            resp = await self.llm.chat_with_tools(messages, tools)
            messages.append(resp.message)

            if not resp.tool_calls:
                return resp.message["content"]

            for call in resp.tool_calls:
                handler = self.registry.get_handler(call.function.name)
                try:
                    args = json.loads(call.function.arguments)
                    result = await handler(**args)
                except Exception as e:
                    result = f"工具执行出错: {str(e)}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                })

        return "达到最大迭代次数，任务未完成。"
```

这个执行循环的核心逻辑是 ReAct (Reasoning and Acting) 模式的实现。LLM 在每一步都会决定是否调用工具，以及调用哪个工具。工具的执行结果会被反馈给 LLM，供其做出下一步决策。max_iterations 参数是一个安全阀，防止 Agent 陷入无限循环。

工具调用框架还需要考虑权限控制。某些工具可能有副作用（如发送邮件、修改数据库），应该需要额外的权限验证。可以在 ToolDefinition 中增加一个 requires_approval 字段，在执行前检查是否有对应的权限：

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict
    handler: Callable
    requires_approval: bool = False

class AgentExecutor:
    async def execute_tool(self, call, context):
        tool = self.registry._tools[call.function.name]
        if tool.requires_approval:
            approved = await context.request_approval(
                tool_name=call.function.name,
                arguments=call.function.arguments,
            )
            if not approved:
                return "用户拒绝了此操作"
        handler = tool.handler
        args = json.loads(call.function.arguments)
        return await handler(**args)
```

这个设计将权限控制嵌入工具调用框架中，为后续实现 HITL (Human-in-the-Loop, 人在回路) 审批机制打下了基础。

工具调用框架的可扩展性也很重要。在 MVP 阶段可能只有三五个工具，但随着项目发展，工具数量可能增长到数十个。这时需要考虑工具的分类管理、按需加载（只把相关工具暴露给 LLM 以减少 Token 消耗）以及动态工具注册（根据运行时状态决定可用工具列表）。

## 6.5 Prompt 模板设计方法论

Prompt 是 Agent 与 LLM 交互的核心接口。好的 Prompt 设计能显著提升输出质量和稳定性，而差的 Prompt 会导致不可预测的行为和大量的无效重试。Prompt 模板设计不是"写一段话"那么简单，它是一门需要系统化方法论支撑的工程实践。

Prompt 模板设计的核心原则是：结构化、参数化、可测试。结构化指的是 Prompt 应该有清晰的组成部分，而不是一整段散文。参数化指的是 Prompt 中的变量部分（如用户输入、检索结果）应该通过模板变量注入，而不是字符串拼接。可测试指的是 Prompt 的效果应该可以通过测试用例验证。

一个标准 Prompt 模板的结构如下：

```
[角色定义] 你是一个XXX助手，你的职责是XXX。
[能力边界] 你可以做到XXX，你不能做到XXX。
[行为规范] 你应该遵循XXX原则，不应该XXX。
[上下文信息] 以下是相关信息：{context}
[用户请求] 用户的问题或请求：{user_input}
[输出格式] 请按照以下格式输出：{output_format}
```

以下是 Prompt 模板的代码实现：

```python
from string import Template

class PromptTemplate:
    def __init__(self, template_str: str, input_variables: list[str]):
        self.template = Template(template_str)
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"缺少必要变量: {missing}")
        return self.template.safe_substitute(kwargs)

SYSTEM_PROMPT = PromptTemplate(
    template_str=(
        "你是一个${role_name}助手。\n"
        "你的核心职责：${responsibility}\n"
        "你可以使用的工具：${available_tools}\n\n"
        "行为规范：\n"
        "1. 只基于检索到的文档内容回答，不编造信息\n"
        "2. 如果信息不足，明确告知用户而非猜测\n"
        "3. 每次回答附带信息来源\n"
        "4. 使用${language}回答\n\n"
        "参考文档：\n${context}"
    ),
    input_variables=[
        "role_name", "responsibility", "available_tools",
        "language", "context",
    ],
)
```

不同类型的 Agent 需要不同的 Prompt 策略。以下是几种常见场景的 Prompt 设计要点：

| 场景 | Prompt 要点 | 常见问题 |
|------|------------|---------|
| 问答助手 | 强调基于上下文回答 | 模型忽略上下文自行回答 |
| 代码生成 | 指定语言版本和编码规范 | 生成过时的API用法 |
| 数据分析 | 明确分析维度和输出格式 | 输出过于泛泛，缺乏深度 |
| 任务规划 | 要求分解步骤并评估可行性 | 计划过于理想化，忽略约束 |
| 工具调用 | 明确何时该用工具 | 模型不调用工具直接回答 |

Prompt 设计中一个容易被忽略的技巧是"示例驱动"。相比于描述规则，给出几个输入输出的示例更能稳定模型行为。这在 LLM 领域被称为 Few-Shot Prompting：

```python
FEW_SHOT_PROMPT = PromptTemplate(
    template_str=(
        "你是一个数据提取助手。从用户输入中提取结构化信息。\n\n"
        "示例：\n"
        "输入：帮我订一张明天去上海的机票\n"
        "输出：{\"intent\": \"book_ticket\", \"date\": \"明天\", "
        "\"destination\": \"上海\"}\n\n"
        "输入：${user_input}\n"
        "输出："
    ),
    input_variables=["user_input"],
)
```

Prompt 版本管理也是一个重要实践。随着模型升级和需求变化，Prompt 会不断迭代。应该将 Prompt 模板存储为独立文件，并建立版本管理机制。一个推荐的做法是将 Prompt 模板放在 prompts/ 目录下，每个模板一个文件，通过加载器统一管理：

```python
from pathlib import Path

class PromptManager:
    def __init__(self, prompt_dir: str = "./prompts"):
        self.prompt_dir = Path(prompt_dir)
        self._cache: dict[str, PromptTemplate] = {}

    def load(self, name: str) -> PromptTemplate:
        if name in self._cache:
            return self._cache[name]
        file_path = self.prompt_dir / f"{name}.txt"
        content = file_path.read_text(encoding="utf-8")
        variables = self._extract_variables(content)
        template = PromptTemplate(content, variables)
        self._cache[name] = template
        return template

    def _extract_variables(self, text: str) -> list[str]:
        import re
        return list(set(re.findall(r"\$\{(\w+)\}", text)))
```

这种方式将 Prompt 与代码解耦，非技术人员也可以参与 Prompt 的优化和调试。同时，配合版本控制系统，可以追踪每次 Prompt 变更对输出效果的影响。

Prompt 的评估是方法论中不可或缺的一环。好的评估体系应该包含自动化指标和人工评审两部分。自动化指标包括：输出格式的合规率、关键信息的召回率、工具调用的准确率等。人工评审则关注回答的准确性、流畅性和有用性。建议建立一套标注数据集，每次修改 Prompt 后运行评估，确保变更不会引入回归。

## 6.6 流式输出实现方案

在 Agent 应用中，流式输出是用户体验的关键。当 LLM 生成一个长回答时，如果让用户等待全部生成完毕再显示，等待时间可能长达十几秒甚至更久。流式输出让用户看到"正在打字"的效果，大幅降低感知等待时间。

流式输出的技术实现主要依赖 SSE (Server-Sent Events, 服务器推送事件)。SSE 是一种基于 HTTP 的单向推送协议，服务器可以通过长连接向客户端持续发送数据。相比于 WebSocket，SSE 更简单、更轻量，天然适合 LLM 流式输出的场景。

以下是服务端 SSE 的实现代码：

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx
import json

app = FastAPI()

@app.post("/api/chat/stream")
async def chat_stream(request: dict):
    async def event_generator():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.example.com/v1/chat/completions",
                json={
                    "model": request.get("model", "gpt-4"),
                    "messages": request["messages"],
                    "stream": True,
                },
                headers={"Authorization": "Bearer sk-xxx"},
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

这段代码的核心逻辑是：将上游 LLM API 的流式响应逐 chunk 读取，解析出文本内容，然后通过 SSE 格式推送给前端。注意 yield 的数据格式必须符合 SSE 规范：每条消息以 `data: ` 开头，以 `\n\n` 结尾。

客户端的实现同样重要。在浏览器中，可以使用 EventSource API 或 fetch 来消费 SSE 流。使用 fetch 的原因是 EventSource 只支持 GET 请求，而聊天接口通常需要 POST：

```javascript
async function streamChat(messages) {
  const resp = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") return;
      const chunk = JSON.parse(data);
      appendToUI(chunk.content);
    }
  }
}
```

在 Agent 场景中，流式输出需要处理比普通聊天更复杂的情况。Agent 在执行过程中可能经历多个阶段：意图识别、工具调用、结果整合、最终回答。每个阶段都应该向用户反馈进度。以下是 Agent 流式输出的扩展实现：

```python
async def agent_stream_generator(user_input: str):
    # 阶段1：意图识别
    yield sse_format({"type": "status", "stage": "understanding"})
    intent = await classify_intent(user_input)
    yield sse_format({"type": "intent", "data": intent})

    # 阶段2：工具调用
    if intent.get("need_tool"):
        yield sse_format({"type": "status", "stage": "tool_calling"})
        for tool_call in intent["tool_calls"]:
            yield sse_format({"type": "tool_call", "data": tool_call})
            result = await execute_tool(tool_call)
            yield sse_format({"type": "tool_result", "data": result})

    # 阶段3：生成回答（流式）
    yield sse_format({"type": "status", "stage": "generating"})
    async for chunk in llm_stream(user_input, context=intent):
        yield sse_format({"type": "content", "content": chunk})

    yield sse_format({"type": "done"})

def sse_format(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
```

这种设计让前端可以根据消息类型渲染不同的 UI 元素：状态消息显示为加载指示器，工具调用显示为可展开的调试信息，内容消息则逐步拼接到回答区域。

流式输出还需要考虑异常处理。网络中断、模型超时、上游服务不可用等情况都可能导致流式连接中断。一种常见的做法是在 SSE 数据中加入心跳机制，定期发送 keep-alive 消息，让客户端能够检测连接状态。如果连接中断，客户端可以发起重连，从断点处继续接收。

## 6.7 多轮对话管理与上下文压缩

Agent 的对话通常是多轮的。用户可能会基于上一轮的回答提出追问，或要求修改之前的结果。管理好多轮对话的上下文，是 Agent 开发中的一项核心挑战。

多轮对话管理的核心问题是：上下文窗口有限。LLM 的上下文窗口虽然在不断增大（从 4K 到 128K 甚至更长），但更长的上下文并不意味着更好的效果。研究表明，当上下文超过一定长度后，模型对早期内容的关注度会下降，出现"中间遗忘"现象。此外，更长的上下文意味着更多的 Token 消耗，直接增加 API 成本。

以下是多轮对话管理的基础代码：

```python
from dataclasses import dataclass, field

@dataclass
class Message:
    role: str  # user / assistant / tool / system
    content: str
    metadata: dict = field(default_factory=dict)

class ConversationManager:
    def __init__(self, max_messages: int = 20,
                 max_tokens: int = 8000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._conversations: dict[str, list[Message]] = {}

    def get_history(self, session_id: str) -> list[Message]:
        return self._conversations.get(session_id, [])

    def add_message(self, session_id: str, msg: Message):
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        history = self._conversations[session_id]
        history.append(msg)
        if len(history) > self.max_messages:
            self._compress(session_id)

    def _compress(self, session_id: str):
        history = self._conversations[session_id]
        # 保留system消息和最近N条
        system_msgs = [m for m in history if m.role == "system"]
        recent = history[-self.max_messages // 2:]
        # 对中间消息生成摘要
        middle = history[len(system_msgs):-self.max_messages // 2]
        if middle:
            summary = self._summarize(middle)
            summary_msg = Message(
                role="system",
                content=f"对话历史摘要：{summary}",
            )
            self._conversations[session_id] = system_msgs + [summary_msg] + recent
        else:
            self._conversations[session_id] = system_msgs + recent

    async def _summarize(self, messages: list[Message]) -> str:
        text = "\n".join(f"{m.role}: {m.content[:200]}" for m in messages)
        prompt = f"请用200字以内总结以下对话的关键信息：\n{text}"
        return await llm_complete(prompt)
```

这段代码实现了一个基于消息数量阈值的上下文压缩策略。当对话消息超过上限时，保留系统消息和最近一半的对话，对中间部分生成摘要。这种方式能够在保留关键上下文的同时控制 Token 消耗。

上下文压缩有多种策略，各有优劣：

| 压缩策略 | 实现方式 | 信息损失 | 适用场景 |
|---------|---------|---------|---------|
| 滑动窗口 | 只保留最近N条消息 | 高 | 短期对话 |
| 摘要压缩 | 用LLM对旧消息生成摘要 | 中 | 长期对话 |
| 选择性保留 | 按重要性筛选消息 | 低 | 任务型对话 |
| 分层压缩 | 先摘要再截断 | 中低 | 超长对话 |
| 实体提取 | 提取关键实体保留 | 低 | 信息密集型对话 |

在实际项目中，建议组合使用多种策略。比如先用滑动窗口控制消息数量，当对话持续时间较长时触发摘要压缩，同时始终保留包含关键实体（如人名、项目名、决策结果）的消息。

另一个需要注意的点是会话隔离。Agent 可能同时服务多个用户或同一用户的多个会话。每个会话应该有独立的上下文，互不干扰。上面代码中用 session_id 作为隔离键，这是一个简单有效的方案。在生产环境中，还需要考虑会话的持久化（将对话历史存入数据库）和过期清理。

对话状态跟踪（Dialogue State Tracking, DST）是多轮对话管理的进阶话题。DST 的目标是从对话中提取结构化的状态信息，如用户的意图、已提供的参数、缺失的必填项等。这在任务型 Agent 中尤其重要：

```python
@dataclass
class DialogueState:
    intent: str | None = None
    slots: dict = field(default_factory=dict)
    required_slots: list[str] = field(default_factory=list)
    completed: bool = False

    def is_ready(self) -> bool:
        return all(s in self.slots for s in self.required_slots)

    def missing_slots(self) -> list[str]:
        return [s for s in self.required_slots if s not in self.slots]

class StateTracker:
    def update(self, state: DialogueState, user_input: str) -> DialogueState:
        # 使用LLM或规则提取槽位信息
        extracted = self._extract_slots(user_input, state.required_slots)
        state.slots.update(extracted)
        if state.is_ready():
            state.completed = True
        return state
```

这个状态跟踪器可以与对话管理器配合使用。当用户说"帮我订一张明天去上海的机票"时，状态跟踪器提取出 date="明天"、destination="上海"，但缺少 departure（出发地），Agent 就可以主动追问："请问您从哪里出发？"

## 6.8 HITL 审批机制设计

HITL (Human-in-the-Loop, 人在回路) 审批机制是 Agent 系统的安全网。当 Agent 要执行具有副作用的操作时（如发送邮件、修改数据库、调用支付接口），应该先获得人工确认。这不是对 Agent 能力的不信任，而是一种工程上的防御性设计。

HITL 审批机制的设计需要解决三个问题：何时触发审批、如何呈现审批请求、如何处理审批结果。

何时触发审批是一个策略问题。不是所有操作都需要审批，过度审批会破坏用户体验。常见的做法是根据操作的风险等级分类：

| 风险等级 | 示例操作 | 处理方式 |
|---------|---------|---------|
| 低风险 | 查询数据、搜索文档 | 自动执行 |
| 中风险 | 发送通知、创建任务 | 可配置审批 |
| 高风险 | 发送邮件、修改配置 | 必须审批 |
| 关键风险 | 支付操作、删除数据 | 双重审批 |

以下是 HITL 审批机制的代码框架：

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

@dataclass
class ApprovalRequest:
    request_id: str
    tool_name: str
    arguments: dict
    risk_level: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: str | None = None
    comment: str | None = None

class ApprovalManager:
    def __init__(self, timeout_seconds: int = 300):
        self.timeout = timeout_seconds
        self._pending: dict[str, ApprovalRequest] = {}
        self._handlers: dict[str, callable] = {}

    async def request_approval(
        self, tool_name: str, arguments: dict,
        risk_level: str = "high",
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            request_id=generate_id(),
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
        )
        self._pending[req.request_id] = req
        # 通知审批人（可通过WebSocket、邮件等）
        await self._notify_reviewer(req)
        # 等待审批结果
        result = await self._wait_for_approval(req)
        return result

    async def approve(self, request_id: str, reviewer: str):
        req = self._pending.get(request_id)
        if req and req.status == ApprovalStatus.PENDING:
            req.status = ApprovalStatus.APPROVED
            req.reviewer = reviewer

    async def reject(self, request_id: str, reviewer: str, reason: str):
        req = self._pending.get(request_id)
        if req and req.status == ApprovalStatus.PENDING:
            req.status = ApprovalStatus.REJECTED
            req.reviewer = reviewer
            req.comment = reason
```

将审批机制集成到 Agent 执行循环中：

```python
class HITLAgentExecutor(AgentExecutor):
    def __init__(self, llm_client, registry: ToolRegistry,
                 approval_manager: ApprovalManager):
        super().__init__(llm_client, registry)
        self.approval = approval_manager

    async def execute_tool(self, call, context):
        tool = self.registry._tools.get(call.function.name)
        if not tool:
            return f"工具 {call.function.name} 不存在"

        if tool.requires_approval:
            result = await self.approval.request_approval(
                tool_name=call.function.name,
                arguments=call.function.arguments,
                risk_level=getattr(tool, "risk_level", "high"),
            )
            if result.status != ApprovalStatus.APPROVED:
                return f"操作未获批准: {result.comment or '用户拒绝'}"

        args = json.loads(call.function.arguments)
        return await tool.handler(**args)
```

审批请求的 UI 呈现也很重要。审批人需要看到足够的信息来做决策：要执行什么操作、操作参数是什么、可能的影响是什么。在前端，可以设计一个审批卡片，展示工具名称、参数详情和操作风险等级，配上"批准"和"拒绝"按钮。在聊天界面中，审批请求可以作为一种特殊类型的消息呈现。

审批超时是一个需要处理的边界情况。如果审批人在合理时间内没有响应，系统应该有降级策略。可以选择自动拒绝（保守策略）、自动通过（仅对低风险操作）或将请求转交给备选审批人。超时时间的设置应该根据业务场景调整，紧急操作的超时时间可以短一些，非紧急操作可以给更长的考虑时间。

HITL 审批机制还应该记录完整的审计日志。谁在什么时间批准了什么操作、审批理由是什么、执行结果如何，这些信息都应该被记录下来。审计日志不仅用于事后追溯，也是优化审批策略的数据基础。通过分析审批记录，可以发现哪些操作的审批通过率高（可能不需要审批）以及哪些操作被频繁拒绝（可能需要改进工具设计或 Prompt）。

## 6.9 测试策略：从单元到集成

测试在 Agent 项目中常常被忽视，但它对项目质量至关重要。Agent 的行为具有不确定性——相同的输入可能产生不同的输出，这给测试带来了独特的挑战。传统的"输入A期望输出B"的断言式测试在 Agent 场景中往往不适用，需要更有针对性的测试策略。

Agent 项目的测试可以分为四个层次：

| 测试层次 | 测试目标 | 覆盖范围 | 执行速度 |
|---------|---------|---------|---------|
| 单元测试 | 函数级正确性 | 工具函数、工具方法 | 快（秒级） |
| 组件测试 | 模块级正确性 | RAG模块、对话管理器 | 中（分钟级） |
| 集成测试 | 链路级正确性 | 端到端流程 | 慢（分钟级） |
| 评估测试 | 效果质量 | 回答准确性、工具选择 | 慢（分钟级） |

单元测试是最基础的测试层次。对于 Agent 项目，单元测试主要覆盖工具函数、Prompt 模板格式化、参数校验等纯逻辑代码：

```python
import pytest
from agent.tools import calculator_handler, web_search_handler
from agent.prompt import PromptTemplate

class TestCalculatorTool:
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        result = await calculator_handler(expression="2 + 3")
        assert result == "5"

    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        result = await calculator_handler(expression="1 / 0")
        assert "error" in result.lower() or "无法" in result

class TestPromptTemplate:
    def test_format_with_all_variables(self):
        template = PromptTemplate(
            "你好${name}，你的角色是${role}",
            ["name", "role"],
        )
        result = template.format(name="张三", role="管理员")
        assert "张三" in result and "管理员" in result

    def test_format_with_missing_variable(self):
        template = PromptTemplate("你好${name}", ["name", "role"])
        with pytest.raises(ValueError, match="缺少必要变量"):
            template.format(name="张三")
```

组件测试关注模块级行为。比如 RAG 模块的检索准确率、对话管理器的上下文压缩逻辑、Agent 执行循环的工具调度等。组件测试通常需要 Mock LLM 的返回：

```python
from unittest.mock import AsyncMock, patch

class TestRAGPipeline:
    @pytest.mark.asyncio
    async def test_retrieve_and_generate(self):
        # Mock嵌入模型和LLM
        mock_embed = AsyncMock(return_value=[0.1] * 768)
        mock_llm = AsyncMock(return_value="根据文档，答案是...")

        pipeline = RAGPipeline(
            retriever=Retriever(vector_store, mock_embed),
            generator=RAGGenerator(mock_llm),
        )

        result = await pipeline.answer("什么是RAG?")
        assert "文档" in result["answer"]
        assert len(result["sources"]) > 0

class TestConversationManager:
    def test_compression_triggers_at_threshold(self):
        manager = ConversationManager(max_messages=6)
        for i in range(7):
            manager.add_message("s1", Message(
                role="user", content=f"消息{i}"
            ))
        history = manager.get_history("s1")
        assert len(history) <= 6  # 压缩后不超过阈值
```

集成测试验证端到端流程。这是最有价值的测试层次，因为它能发现模块间集成的问题。集成测试应该覆盖典型用户场景：

```python
class TestAgentEndToEnd:
    @pytest.mark.asyncio
    async def test_rag_question_answer_flow(self):
        """测试RAG问答完整流程"""
        agent = create_test_agent()
        result = await agent.run("公司的年假政策是什么？")
        assert result  # 非空回答
        assert "年假" in result or "假期" in result

    @pytest.mark.asyncio
    async def test_tool_calling_flow(self):
        """测试工具调用流程"""
        agent = create_test_agent()
        result = await agent.run("帮我计算 15 * 23")
        assert "345" in result

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """测试多轮对话"""
        agent = create_test_agent()
        await agent.run("我叫张三")
        result = await agent.run("我叫什么名字？")
        assert "张三" in result
```

评估测试是 Agent 特有的测试类型。它不验证代码逻辑的正确性，而是评估 Agent 输出的质量。评估测试需要一个标注数据集——包含输入问题和期望的输出特征（不是精确的输出文本，而是输出的关键特征）：

```python
class TestAgentQuality:
    test_cases = [
        {"input": "公司年假多少天", "expect_keywords": ["年假", "天"]},
        {"input": "报销流程", "expect_keywords": ["报销", "流程"]},
        {"input": "今天天气如何", "expect_keywords": ["无法", "不知道"]},
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("case", test_cases)
    async def test_answer_quality(self, case):
        agent = create_test_agent()
        result = await agent.run(case["input"])
        keyword_hits = sum(
            1 for kw in case["expect_keywords"] if kw in result
        )
        assert keyword_hits >= len(case["expect_keywords"]) // 2
```

测试自动化是保证测试持续有效的关键。CI/CD 流水线中应该自动运行所有测试，并在测试失败时阻止代码合并。对于依赖 LLM API 的测试，建议在 CI 中使用 Mock 模式运行，避免 API 调用费用和延迟。定期（如每周）在真实 API 上运行完整测试，验证 Agent 的真实效果。

## 6.10 代码管理与版本控制规范

Agent 项目的代码管理与传统软件项目有共性，也有特殊性。共性的部分是都使用 Git 进行版本控制，都遵循一定的分支策略。特殊性在于 Agent 项目中 Prompt、测试数据、模型配置等非代码资产同样需要版本管理。

分支策略是代码管理的基础。在 MVP 阶段，推荐使用简化版的 Git Flow：

```
main (生产分支)
  |
  +-- develop (开发分支)
        |
        +-- feature/xxx (功能分支)
        |
        +-- fix/xxx (修复分支)
```

分支策略的 ASCII 流程图如下：

```
main:     ----C1----C2----C3----C4----> (发布版本)
              |         |         |
develop:  ----D1----D2----D3----D4----> (日常集成)
              |    |         |
feature:  -F1-+    |-F2------+        (功能开发)
              |    |
fix:           |-X1-+                   (Bug修复)
```

以下是各分支的使用规范：

| 分支类型 | 命名规范 | 来源分支 | 合并目标 | 说明 |
|---------|---------|---------|---------|------|
| main | main | - | - | 生产环境代码 |
| develop | develop | main | main | 日常开发集成 |
| feature | feature/xxx | develop | develop | 新功能开发 |
| fix | fix/xxx | develop | develop | Bug修复 |
| hotfix | hotfix/xxx | main | main + develop | 紧急修复 |
| release | release/x.x.x | develop | main | 发布准备 |

提交信息规范同样重要。规范的提交信息能够帮助团队理解变更内容，也便于自动生成变更日志。推荐使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

type 包括：feat（新功能）、fix（修复）、docs（文档）、style（格式）、refactor（重构）、test（测试）、chore（构建）。scope 是可选的，表示影响的模块。subject 是简洁的描述。

```
feat(rag): 新增混合检索策略
fix(agent): 修复工具调用循环不退出的问题
docs(prompt): 更新系统提示词模板
test(e2e): 新增多轮对话集成测试
```

Agent 项目中的特殊资产管理需要注意。Prompt 模板应该作为独立文件管理，纳入版本控制。测试数据集（标注的问答对）也应该入库。模型配置（模型名称、温度参数、超时设置等）建议使用配置文件管理，不同环境使用不同配置：

```yaml
# config/development.yaml
model:
  name: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30

rag:
  chunk_size: 500
  overlap: 50
  top_k: 5

agent:
  max_iterations: 10
  require_approval_tools:
    - send_email
    - modify_database
```

```yaml
# config/production.yaml
model:
  name: "gpt-4"
  temperature: 0.3
  max_tokens: 4000
  timeout: 60

rag:
  chunk_size: 800
  overlap: 100
  top_k: 8

agent:
  max_iterations: 15
  require_approval_tools:
    - send_email
    - modify_database
    - delete_data
    - payment
```

Code Review 是代码质量的最后一道防线。在 Agent 项目中，Code Review 除了检查常规的代码质量问题，还需要特别关注以下几点：Prompt 变更是否可能导致行为退化、新增工具是否正确设置了风险等级和审批标志、测试覆盖是否充分、配置变更是否可能影响生产环境。

一个推荐的 Code Review 清单：

| 检查项 | 说明 |
|-------|------|
| Prompt 变更 | 是否有对应的测试用例验证效果 |
| 工具安全 | 新增工具是否评估了风险等级 |
| 错误处理 | 是否覆盖了超时、异常、重试场景 |
| Token 消耗 | 新增功能是否会导致Token超限 |
| 测试覆盖 | 核心路径是否有集成测试 |
| 配置隔离 | 开发与生产配置是否正确分离 |
| 敏感信息 | API Key 等是否通过环境变量注入 |

环境变量管理是代码安全的重要一环。绝对不应该将 API Key、数据库密码等敏感信息硬编码在代码中或提交到版本控制系统。推荐使用 .env 文件管理本地开发环境的密钥，并将 .env 加入 .gitignore。生产环境的密钥通过密钥管理服务（如 AWS Secrets Manager、HashiCorp Vault）注入。

以下是一个 .env.example 模板，用于指导团队成员配置本地环境：

```bash
# .env.example (提交到版本控制)
# LLM API
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.example.com/v1

# 向量数据库
CHROMA_PERSIST_PATH=./data/chroma

# 应用配置
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=DEBUG

# 审批通知（可选）
NOTIFICATION_WEBHOOK_URL=
```

团队成员复制 .env.example 为 .env，填入自己的密钥。.env 文件不提交到版本控制，这样就避免了密钥泄露的风险。

## 本章知识点总结

| 序号 | 知识点 | 核心内容 |
|------|-------|---------|
| 1 | 两周MVP计划 | 14天垂直切片交付，每日可运行增量，风险前置 |
| 2 | 工具链选型 | FastAPI+Next.js+Chroma为默认栈，原生调用优于框架封装 |
| 3 | RAG开发模板 | 四阶段流程：文档处理、向量索引、检索召回、生成回答 |
| 4 | Agent工具调用框架 | ToolRegistry注册器+ReAct执行循环+权限控制 |
| 5 | Prompt模板设计 | 结构化+参数化+可测试，Few-Shot驱动稳定行为 |
| 6 | SSE流式输出 | Server-Sent Events协议，分阶段推送Agent执行进度 |
| 7 | 多轮对话管理 | 滑动窗口+摘要压缩+对话状态跟踪(DST) |
| 8 | HITL审批机制 | 按风险分级触发审批，审计日志全链路记录 |
| 9 | 测试策略 | 四层测试：单元、组件、集成、评估测试，CI自动化 |
| 10 | 代码管理规范 | 简化Git Flow分支策略，Conventional Commits提交规范 |

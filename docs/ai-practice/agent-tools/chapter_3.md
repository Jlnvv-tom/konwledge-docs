# AI Agent 开发框架——代码级智能体编排

LangChain、AutoGen、CrewAI 框架三选一，90% 的开发者选错了。

我是怕浪猫，《智能体产品全景手册》第 3 篇。上一篇讲了零代码开发平台，这一篇我们下沉到代码层。如果你是开发者，或者你的需求复杂到平台拖拽搞不定，那这一篇就是为你写的。

## 3.1 框架的核心抽象：Chain、Agent、Tool、Memory 四大组件

所有 AI Agent 框架的核心抽象都是相似的。不管你用 LangChain 还是 AutoGen 还是 CrewAI，底层都在解决同一个问题：如何让大模型从"单次问答"变成"多步行动"。

要理解这个问题，先看一个最简单的对比。

单次问答模式：用户提问 → 模型回答 → 结束。模型只做一件事——生成文本。

Agent 模式：用户给出目标 → 模型规划步骤 → 调用工具执行 → 观察结果 → 继续规划 → 直到目标完成。模型变成了一个"会思考、会行动"的循环体。

这个"思考-行动-观察"的循环被称为 ReAct（Reasoning + Acting）模式，是所有 Agent 框架的底层逻辑。

```
# ReAct 模式的核心循环
class ReActAgent:
    def __init__(self, llm, tools, memory):
        self.llm = llm          # 大语言模型
        self.tools = tools        # 可用工具列表
        self.memory = memory      # 记忆系统
    
    def run(self, goal):
        # Agent 的核心循环：思考 → 行动 → 观察
        while not self._is_complete(goal):
            # 1. 思考：基于目标和已有信息，决定下一步做什么
            thought = self.llm.think(
                goal=goal,
                history=self.memory.get_history(),
                available_tools=[t.description for t in self.tools]
            )
            
            # 2. 行动：调用工具执行
            if thought.action == "use_tool":
                result = self._execute_tool(thought.tool_name, thought.tool_input)
            elif thought.action == "respond":
                return thought.response
            
            # 3. 观察：记录结果到记忆
            self.memory.add({
                "thought": thought,
                "observation": result
            })
```

这个循环对应着四大核心抽象组件：

**Chain（链）**：将多个操作串联起来，前一个操作的输出是后一个操作的输入。最简单的 Chain 是"用户输入 → Prompt 模板 → LLM 调用 → 输出解析"。复杂的 Chain 可以包含条件分支、循环、并行执行。

**Agent（智能体）**：在 Chain 的基础上增加了自主决策能力。Agent 不是按预设流程执行，而是由 LLM 决定下一步做什么。Agent 内部可以包含多个 Chain，根据情况选择执行哪个。

**Tool（工具）**：Agent 调用外部能力的接口。一个 Tool 通常包含：名称、描述、参数 Schema（JSON Schema 定义）、执行函数。LLM 通过 Tool 的描述来理解何时该用它，通过参数 Schema 来生成正确的调用参数。

**Memory（记忆）**：存储 Agent 的历史交互信息。记忆分为短期记忆（当前对话的上下文）和长期记忆（跨对话的持久化存储）。记忆管理直接影响 Agent 的上下文窗口使用效率和一致性。

> Chain 是流水线，Agent 是工人，Tool 是工具箱，Memory 是笔记本。理解了这四个比喻，你就理解了所有 Agent 框架。

### Tool 的标准化定义

Tool 是 Agent 与外部世界交互的桥梁。一个标准化的 Tool 定义包含以下要素：

```
# Tool 的标准化定义
class Tool:
    name: str                    # 工具名称，如 "web_search"
    description: str             # 工具描述，告诉 LLM 何时使用
    parameters: dict             # 参数 Schema（JSON Schema格式）
    execute: Callable            # 执行函数
    
# 示例：定义一个网页搜索工具
web_search_tool = Tool(
    name="web_search",
    description="当需要查询最新信息、事实、数据时使用此工具。输入搜索关键词，返回搜索结果摘要。",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "num_results": {
                "type": "integer",
                "description": "返回结果数量，默认5",
                "default": 5
            }
        },
        "required": ["query"]
    },
    execute=lambda params: search_api(params["query"], params.get("num_results", 5))
)
```

这个标准化定义是 MCP（Model Context Protocol，模型上下文协议）的基础。MCP 由 Anthropic 提出，旨在让 Tool 的定义和调用方式在不同模型和框架之间通用。我们会在第 10 章详细讨论 MCP。

## 3.2 LangChain 与 LangGraph：生态最大的 Agent 编排框架

LangChain 是 AI Agent 领域最早也是最大的开发框架。2023 年由 Harrison Chase 创建，GitHub Star 数超过 10 万，是 Agent 框架的绝对标杆。

### LangChain 的核心架构

LangChain 的架构采用模块化设计，包含以下核心包：

**langchain-core**：基础抽象层，定义了 Runnable（可运行单元）、Message（消息）、PromptTemplate（提示词模板）等核心接口。

**langchain-community**：社区集成层，包含数百个第三方服务的集成（OpenAI、Anthropic、Google、各种向量数据库等）。

**langchain**：主包，提供 Chain、Agent、Tool、Memory 的高级实现。

**langgraph**：状态图引擎，用于构建复杂的多 Agent 工作流。这是 LangChain 2024 年后的重点发展方向。

LangChain 的 Chain 机制是其核心特色。一个 Chain 通过 LCEL（LangChain Expression Language，LangChain 表达式语言）来定义：

```
# LangChain LCEL 语法示例
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 用管道符 | 串联各个组件
chain = (
    ChatPromptTemplate.from_template("用{language}语言解释{concept}")
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

# 执行 Chain
result = chain.invoke({"language": "Python", "concept": "闭包"})
```

LCEL 的设计哲学是"组合优于继承"。每个组件都实现 Runnable 接口，通过管道符 `|` 串联，前一个组件的输出自动成为后一个组件的输入。这种设计让复杂流程的构建变得像搭积木一样简单。

### LangGraph：从 Chain 到状态图

LangChain 的 Chain 机制适合线性流程，但真实的 Agent 场景往往需要条件分支、循环、状态管理。LangGraph 就是为解决这个问题而生的。

LangGraph 的核心概念是 StateGraph（状态图）。与简单的 Chain 不同，StateGraph 维护一个全局状态对象，每个节点可以读取和修改这个状态。节点之间的跳转由条件边决定，支持循环——这是 Chain 做不到的。

```
# LangGraph 构建多步 Agent 工作流
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# 定义全局状态
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    retrieved_docs: list
    needs_search: bool

# 定义节点
def retrieve_node(state):
    """检索节点：从知识库检索相关文档"""
    docs = vector_store.search(state["messages"][-1])
    return {"retrieved_docs": docs}

def evaluate_node(state):
    """评估节点：判断检索结果是否充分"""
    if len(state["retrieved_docs"]) < 3:
        return {"needs_search": True}
    return {"needs_search": False}

def web_search_node(state):
    """搜索节点：检索结果不足时，补充网络搜索"""
    web_results = web_search(state["messages"][-1])
    return {"retrieved_docs": state["retrieved_docs"] + web_results}

def generate_node(state):
    """生成节点：基于检索结果生成回答"""
    answer = llm.generate(state["messages"], context=state["retrieved_docs"])
    return {"messages": [answer]}

# 构建状态图
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("generate", generate_node)

# 定义边（包含条件分支）
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "evaluate")
workflow.add_conditional_edges(
    "evaluate",
    lambda state: "web_search" if state["needs_search"] else "generate"
)
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()
```

这个例子展示了 LangGraph 的核心能力：条件分支（检索不足时补充搜索）和状态管理（全局状态在节点间传递）。这种灵活性是 LangChain 的 Chain 机制做不到的。

> LangChain 解决了"如何串联组件"的问题，LangGraph 解决了"如何管理复杂状态"的问题。两者配合，从简单 Chain 到复杂多 Agent 系统都能覆盖。

### LangChain 的优势与局限

**优势**：生态最大，集成最多（数百个第三方服务），社区最活跃，文档最丰富，LCEL 语法优雅，学习资源最多。

**局限**：抽象层过多导致性能开销，API 变动频繁（从 v0.1 到 v0.3 经历多次 Breaking Change），对于简单任务来说过于重量级，调试复杂 Chain 的可观测性不足。

## 3.3 AutoGen 与 CrewAI：多 Agent 协作的两种范式

多 Agent 协作是 Agent 框架的前沿方向。当任务复杂到单个 Agent 难以处理时，让多个专业化的 Agent 分工合作是自然的选择。AutoGen 和 CrewAI 代表了两种不同的多 Agent 协作范式。

### AutoGen（微软）

AutoGen 由微软研究院开发，是第一个系统性解决多 Agent 对话的框架。

AutoGen 的核心概念是"对话式 Agent"。多个 Agent 在一个共享的对话上下文中交流，每个 Agent 有自己的角色和系统提示词。Agent 之间通过"发送消息"来协作。

AutoGen 定义了几种核心 Agent 类型：

**AssistantAgent（助手 Agent）**：通用型 Agent，接收任务并生成解决方案。通常由 LLM 驱动。

**UserProxyAgent（用户代理 Agent）**：代表用户执行操作。它可以执行代码、调用工具、或在需要人类输入时暂停等待。

**GroupChatManager（群聊管理器）**：管理多个 Agent 的对话顺序和终止条件。

```
# AutoGen 多 Agent 协作示例
import autogen

# 配置 LLM
config_list = [{"model": "gpt-4o", "api_key": "..."}]

# 创建产品经理 Agent
pm_agent = autogen.AssistantAgent(
    name="ProductManager",
    system_message="你是一个产品经理，负责定义产品需求和验收标准。",
    llm_config={"config_list": config_list}
)

# 创建开发者 Agent
dev_agent = autogen.AssistantAgent(
    name="Developer",
    system_message="你是一个全栈开发者，负责实现产品经理定义的需求。",
    llm_config={"config_list": config_list}
)

# 创建测试 Agent
qa_agent = autogen.AssistantAgent(
    name="QAEngineer",
    system_message="你是一个测试工程师，负责验证开发者实现的代码是否符合需求。",
    llm_config={"config_list": config_list}
)

# 创建用户代理（可执行代码）
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "workspace"}
)

# 发起群聊
user_proxy.initiate_chat(
    pm_agent,
    message="开发一个待办事项管理工具，支持增删改查和优先级排序",
    group_chat=[pm_agent, dev_agent, qa_agent]
)
```

AutoGen 的多 Agent 协作流程是：产品经理定义需求 → 开发者实现代码 → 测试工程师验证 → 发现问题反馈给产品经理或开发者 → 循环直到满足验收标准。这个流程模拟了真实的软件开发团队。

### CrewAI

CrewAI 是 2024 年初由 João Moura 创建的多 Agent 框架。与 AutoGen 的"对话式"不同，CrewAI 采用"任务驱动"的协作模式。

CrewAI 的核心概念是 Crew（团队）、Agent（成员）、Task（任务）和 Process（流程）。

**Agent**：团队成员，有角色、目标、背景故事和工具集。

**Task**：需要完成的具体任务，有描述、负责 Agent、预期输出。

**Crew**：由多个 Agent 和 Task 组成的团队，定义了协作流程。

**Process**：协作模式，支持 sequential（顺序执行）和 hierarchical（层级管理，有一个 Manager Agent 统筹）。

```
# CrewAI 多 Agent 协作示例
from crewai import Agent, Task, Crew, Process

# 定义 Agent
researcher = Agent(
    role="市场研究员",
    goal="收集 AI Agent 市场的最新数据和趋势",
    backstory="你是一名资深市场分析师，擅长从海量信息中提炼关键洞察。",
    tools=[web_search_tool, data_analysis_tool],
    llm="gpt-4o"
)

writer = Agent(
    role="技术撰稿人",
    goal="将研究员的发现转化为可读性强的市场报告",
    backstory="你是一名资深科技撰稿人，擅长将复杂技术概念用通俗语言解释。",
    llm="gpt-4o"
)

editor = Agent(
    role="内容编辑",
    goal="确保报告的准确性、结构性和可读性",
    backstory="你是一名严谨的内容编辑，对事实准确性和逻辑结构有极高要求。",
    llm="gpt-4o"
)

# 定义 Task
research_task = Task(
    description="调研 2026 年 AI Agent 市场规模、主要玩家、融资情况和趋势",
    agent=researcher,
    expected_output="包含数据、图表描述和趋势分析的研究报告"
)

writing_task = Task(
    description="基于研究报告撰写 3000 字的市场分析文章",
    agent=writer,
    expected_output="结构清晰、数据准确、可读性强的分析文章"
)

editing_task = Task(
    description="审校文章的事实准确性、逻辑结构和语言表达",
    agent=editor,
    expected_output="最终版本，附带修改说明"
)

# 组建 Crew 并执行
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential  # 顺序执行
)

result = crew.kickoff()
```

### AutoGen vs CrewAI：对话驱动 vs 任务驱动

两种框架的核心差异在于协作模式：

AutoGen 是对话驱动的。Agent 之间通过消息传递来协作，就像一个微信群聊。每个 Agent 可以自由发言，群聊管理器决定谁该说话。优势是灵活性高——Agent 可以随时提出问题、给出建议、发现错误。劣势是可控性低——对话可能跑偏，难以预测执行路径。

CrewAI 是任务驱动的。每个 Agent 负责明确的 Task，Task 之间有顺序依赖。就像一条流水线，每个工位完成自己的工序后交给下一个。优势是可控性强——执行路径清晰，结果可预测。劣势是灵活性低——不擅长需要频繁讨论和迭代的场景。

| 维度 | AutoGen | CrewAI |
|------|---------|--------|
| 协作模式 | 对话驱动 | 任务驱动 |
| 灵活性 | 高 | 中 |
| 可控性 | 中 | 高 |
| 适合场景 | 开放式讨论、创意协作 | 流程化任务、批量处理 |
| 学习曲线 | 中等 | 低 |
| 代码执行 | 内置（UserProxy） | 需自定义 |
| Manager 角色 | GroupChatManager | hierarchical模式 |

> AutoGen 像开会是讨论问题，CrewAI 像分活儿是解决问题。讨论适合探索性任务，分活儿适合执行性任务。

## 3.4 LlamaIndex、Semantic Kernel、Google ADK、OpenClaw 对比

除了 LangChain 和 AutoGen/CrewAI，还有几款值得关注的框架。

### LlamaIndex

LlamaIndex 最初定位是"数据框架"——专注解决如何让 LLM 访问和操作私有数据。后来扩展到 Agent 领域。

LlamaIndex 的核心优势在 RAG（Retrieval-Augmented Generation，检索增强生成）。它提供了最完整的数据摄入、索引、检索工具链：

```
# LlamaIndex 的 RAG 管道
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.embeddings import OpenAIEmbedding
from llama_index.core.llms import OpenAI

# 数据摄入：解析文档 → 分块 → 索引
documents = SimpleDirectoryReader("./data").load_data()
splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)

# 构建索引
embed_model = OpenAIEmbedding(model="text-embedding-3-small")
index = VectorStoreIndex(nodes, embed_model=embed_model)

# 创建查询引擎（自动检索+生成）
query_engine = index.as_query_engine(
    llm=OpenAI(model="gpt-4o"),
    similarity_top_k=5
)

response = query_engine.query("公司的退款政策是什么？")
```

如果你要做的是数据密集型的 Agent（需要大量文档检索、知识库问答），LlamaIndex 比 LangChain 更合适。

### Semantic Kernel（微软）

Semantic Kernel 是微软推出的 Agent 框架，支持 C# 和 Python。它的设计理念是"Plugin 化"——每个能力都是一个 Plugin，Agent 通过编排 Plugin 来完成任务。

Semantic Kernel 的特色在于与微软生态的深度集成。如果你的技术栈是 Azure、.NET、Power Platform，Semantic Kernel 是自然的选择。Microsoft Copilot Studio 底层就使用了 Semantic Kernel。

### Google ADK（Agent Development Kit）

Google ADK 是 Google 在 2025 年推出的开源 Agent 开发框架，与 Gemini 模型深度集成。

ADK 的核心特色是"声明式 Agent 定义"——你用 YAML 或 JSON 描述 Agent 的能力和行为，ADK 负责执行。这种方式的优点是配置即代码，易于版本管理和团队协作。

```
# Google ADK 声明式 Agent 定义
agent_config = """
name: customer_support_agent
description: 处理客户咨询的智能客服
model: gemini-3-pro
instructions: |
  你是一个专业的客服 Agent。
  1. 首先判断用户问题的类别
  2. 查询知识库获取相关信息
  3. 如果无法解决，创建工单转人工
tools:
  - knowledge_base_search
  - ticket_creation
  - order_lookup
  - refund_processor
guardrails:
  - max_turns: 10
  - sensitive_topics: [政治, 宗教]
  - require_approval_for: [refund_processor]
"""
```

### OpenClaw

OpenClaw 是一个开源的 AI Agent 运行时框架，专注于"多渠道 Agent 部署"。它的核心价值是让一个 Agent 能同时接入多个消息渠道（Signal、Telegram、Discord、WhatsApp、微信等），并在不同渠道间保持一致的上下文。

OpenClaw 的架构特点是"Agent 即服务"——Agent 不是一个库或框架，而是一个持续运行的服务进程。用户通过消息渠道与 Agent 交互，Agent 在后台自主执行任务、管理记忆、调度定时任务。

OpenClaw 的核心架构：

**Gateway（网关）**：Agent 的运行时进程，管理消息路由、会话状态、工具调用。

**Session（会话）**：每个用户对话对应一个 Session，维护对话上下文和记忆。

**Skill（技能）**：Agent 的能力模块，类似于 Tool。但 Skill 更重量级——它可以包含多个步骤、管理自己的状态、甚至调用子 Agent。

**Heartbeat（心跳）**：Agent 可以设置定时心跳，定期检查邮件、日历、通知等，实现主动式 Agent 行为。

> OpenClaw 的哲学是"Agent 是数字员工"——它不是被动等指令的工具，而是持续在线、主动工作的助手。

下面是六款框架的横向对比：

| 框架 | 开发方 | 语言 | 核心特色 | 适合场景 |
|------|--------|------|---------|---------|
| LangChain | LangChain | Python/JS | 生态最大、LCEL | 通用 Agent |
| LangGraph | LangChain | Python | 状态图、复杂流程 | 多步工作流 |
| AutoGen | 微软 | Python | 对话式多 Agent | 开放式协作 |
| CrewAI | CrewAI | Python | 任务驱动多 Agent | 流程化任务 |
| LlamaIndex | LlamaIndex | Python/TS | RAG 最强 | 数据密集型 |
| Semantic Kernel | 微软 | C#/Python | 微软生态集成 | Azure/.NET |
| Google ADK | Google | Python | 声明式定义 | Gemini 生态 |
| OpenClaw | OpenClaw | TypeScript | 多渠道部署 | 持续运行 Agent |

## 3.5 框架选型决策树：项目该用哪个框架

讲了这么多框架，到底该怎么选？我根据项目类型和团队能力给出一个决策树。

### 决策树

```
你的项目是什么类型？

A. 数据密集型（大量文档检索、知识库）
   → LlamaIndex（RAG 能力最强）

B. 简单 Chain（线性流程、单 Agent）
   → LangChain LCEL（生态最大、文档最全）

C. 复杂工作流（条件分支、循环、状态管理）
   → LangGraph（状态图引擎最成熟）

D. 多 Agent 协作
   ├── 任务可拆解、流程清晰
   │   → CrewAI（可控性强、学习曲线低）
   └── 需要开放式讨论、创意协作
       → AutoGen（灵活性好）

E. 企业级、微软生态
   → Semantic Kernel（Azure 集成）

F. 企业级、Google 生态
   → Google ADK（Gemini 集成）

G. 需要多渠道部署、持续运行
   → OpenClaw（多渠道+心跳）

H. 不确定
   → LangChain + LangGraph（默认选择，生态最大，遇到问题最容易找到答案）
```

### 框架选型的三个原则

**原则一：生态优先**。选框架不只是选技术，更是选社区。LangChain 的生态最大意味着遇到任何问题都能在 GitHub Issues、Stack Overflow、博客中找到答案。这在项目初期价值巨大。

**原则二：从简单开始**。不要一上来就用 AutoGen 的多 Agent 协作。先用 LangChain 的简单 Chain 验证想法，遇到瓶颈再升级到 LangGraph 或多 Agent。过度工程化是 Agent 项目的头号杀手。

**原则三：关注退出成本**。框架会绑定你的代码结构。选框架时想清楚：如果将来要换框架，迁移成本有多高？尽量选择使用标准接口（如 MCP 协议的 Tool 定义）的框架，减少锁定。

> 框架选型最大的坑不是选错，而是过度设计。90% 的 Agent 项目用 LangChain 的简单 Chain 就够了，不需要多 Agent 协作。

### 框架组合使用

实际项目中，框架不是互斥的，可以组合使用。一个常见的组合模式：

用 LlamaIndex 做 RAG 数据层（文档摄入、索引、检索），用 LangGraph 做编排层（多步工作流、状态管理），用 CrewAI 做多 Agent 协作层（当需要多个角色分工时）。

```
# LlamaIndex + LangGraph 组合示例
from llama_index.core import VectorStoreIndex
from langgraph.graph import StateGraph, END

# 用 LlamaIndex 构建知识库
index = VectorStoreIndex.from_documents(documents)
retriever = index.as_retriever(similarity_top_k=5)

# 用 LangGraph 构建工作流
class AgentState(TypedDict):
    question: str
    retrieved_docs: list
    answer: str

def retrieve_node(state):
    docs = retriever.retrieve(state["question"])
    return {"retrieved_docs": [d.text for d in docs]}

def generate_node(state):
    context = "\n".join(state["retrieved_docs"])
    answer = llm.generate(f"基于以下信息回答：{context}\n问题：{state['question']}")
    return {"answer": answer}

workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()
```

这种组合让每个框架发挥自己的强项：LlamaIndex 擅长数据处理，LangGraph 擅长流程编排。

这一章我们拆解了 8 款 AI Agent 开发框架（LangChain、LangGraph、AutoGen、CrewAI、LlamaIndex、Semantic Kernel、Google ADK、OpenClaw），深入解析了 Chain/Agent/Tool/Memory 四大核心抽象，对比了对话驱动（AutoGen）和任务驱动（CrewAI）两种多 Agent 范式，最后给出了框架选型决策树。

| 框架类别 | 产品数量 | 市场格局 |
|---------|---------|---------|
| 通用编排框架 | 2 款 | LangChain 生态最大 |
| 多 Agent 协作 | 2 款 | CrewAI 增长最快 |
| 垂直领域框架 | 4 款 | LlamaIndex RAG 最强 |

觉得有用？收藏起来，下次选框架直接照抄决策树。

你在用哪个 Agent 框架？有没有踩过 LangChain 频繁变更 API 的坑？评论区聊聊。

关注怕浪猫，下期我们讲编程智能体——从 GitHub Copilot 到 Devin，AI 写代码已经进化到什么程度了。系列进度 3/10，关注不错过后续更新。

下一篇，怕浪猫会带你走进编程智能体的世界。Cursor 和 Devin 到底谁更强？AI 真的能独立完成一个完整项目吗？我们下期见。

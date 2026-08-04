# 第七章：多 Agent 系统与协作

## 7.1 多 Agent 系统概述：为什么需要多个 Agent

在单 Agent 架构中，一个 LLM (Large Language Model, 大语言模型) 实例承担全部职责：理解用户意图、检索信息、推理决策、生成内容、执行工具调用。这种模式在简单任务中表现良好，但当任务复杂度上升时，单 Agent 架构会暴露出一系列结构性瓶颈。

第一个瓶颈是上下文窗口的竞争。单 Agent 需要在有限的上下文窗口中同时维护任务描述、历史对话、工具调用结果、中间推理过程等信息。当任务链路变长，上下文窗口会被大量中间状态占满，导致关键信息被挤出窗口，模型出现"遗忘"或注意力分散的现象。即便采用 128K 甚至 200K 的大窗口模型，信息密度下降带来的性能衰减依然显著。

第二个瓶颈是角色混淆。当一个 Agent 同时扮演研究员、代码编写者和审查者时，它的行为策略会相互干扰。例如，生成代码的 Agent 需要倾向于创造性输出，而审查代码的 Agent 需要倾向于批判性思考。这两种倾向在同一个模型实例中难以有效切换，往往导致"自己写的代码自己审不出问题"。

第三个瓶颈是工具调用的爆炸性增长。单 Agent 在处理复杂任务时需要挂载大量工具：搜索引擎、代码解释器、数据库查询、文件操作、API 调用等等。工具数量增加后，模型在工具选择上的准确率会下降。研究表明，当可用工具超过 20 个时，工具选择的准确率会下降 15% 以上。

多 Agent 系统通过将复杂任务分解为多个子任务，每个子任务由专门的 Agent 处理，从而缓解上述瓶颈。每个 Agent 拥有独立的上下文窗口、专属的工具集和明确的角色定义，彼此通过结构化的通信协议进行协作。

以下是单 Agent 与多 Agent 系统的关键对比：

| 维度 | 单 Agent | 多 Agent 系统 |
|------|---------|-------------|
| 上下文管理 | 所有信息共享一个窗口，容易溢出 | 每个 Agent 独立窗口，隔离性好 |
| 角色定义 | 角色混淆，策略冲突 | 角色明确，各司其职 |
| 工具管理 | 工具集中挂载，选择困难 | 工具按角色分配，精准调用 |
| 错误恢复 | 错误传播影响全局 | 错误可被其他 Agent 纠正 |
| 并行能力 | 串行执行，速度受限 | 可并行执行独立子任务 |
| 系统复杂度 | 架构简单，开发成本低 | 通信开销大，调试难度高 |
| 成本 | 单次调用成本低 | 总 Token 消耗高，成本上升 |

多 Agent 系统并非银弹。它带来了新的挑战：Agent 间的通信开销、状态同步的一致性问题、系统整体的调试复杂度、以及更高的 Token 消耗成本。在实际工程中，需要在任务复杂度与系统复杂度之间寻找平衡点。

一个实用的判断标准是：当任务满足以下任一条件时，应考虑采用多 Agent 架构：

- 任务可以被自然地分解为 3 个以上独立子任务
- 不同子任务需要不同的系统提示词和工具集
- 任务流程中存在明确的"审查-修改"循环
- 需要多个专业领域的知识进行交叉验证
- 子任务之间存在可并行执行的依赖关系

在学术界和工业界的实践中，多 Agent 系统已被广泛应用于软件开发（如 MetaGPT 模拟软件开发团队）、科学研究（如多 Agent 协作撰写综述论文）、金融分析（如多视角投资决策）等领域。这些应用证明了多 Agent 协作在复杂任务中的有效性。

## 7.2 协作模式：层级式、流水线式、并行式与辩论式

多 Agent 系统的协作模式决定了 Agent 之间的交互拓扑结构。不同的协作模式适用于不同的任务类型，选择合适的协作模式是系统设计的关键决策之一。

### 层级式协作（Hierarchical）

层级式协作采用树状结构，顶层 Agent 负责任务分解和调度，底层 Agent 负责具体执行。这种模式类似于企业中的管理层级：CEO 将战略目标分解为部门目标，部门经理进一步分解为具体任务，基层员工执行。

```
          [Orchestrator Agent]
           /        |        \
    [Agent A]   [Agent B]   [Agent C]
     /    \       |          |
  [A1]  [A2]   [B1]        [C1]
```

层级式的优势在于控制流清晰，顶层 Agent 可以全局视角进行任务调度。劣势是顶层 Agent 容易成为瓶颈，且底层 Agent 之间缺乏直接沟通，可能导致信息传递损耗。

典型应用场景：项目管理类任务，如"开发一个 Web 应用"，顶层 Agent 分解为前端开发、后端开发、测试等子任务，各子任务再进一步分解。

### 流水线式协作（Pipeline）

流水线式协作采用线性链式结构，每个 Agent 处理特定阶段的任务，将输出传递给下游 Agent。这种模式类似于工厂流水线：原料经过一道道工序，最终产出成品。

```
[Research Agent] --> [Drafting Agent] --> [Review Agent] --> [Publish Agent]
```

流水线式的优势在于流程明确，每个 Agent 只需关注输入输出格式，职责边界清晰。劣势是线性结构导致整体延迟等于各阶段延迟之和，且任何一个环节出错都会阻塞整条流水线。

典型应用场景：内容生产流水线，如"研究主题 -> 撰写初稿 -> 审校修改 -> 发布"。每一步由专门 Agent 处理，上游产出作为下游输入。

### 并行式协作（Parallel）

并行式协作允许多个 Agent 同时处理同一任务的不同方面，最终汇总结果。这种模式类似于专家组各自独立研究同一问题的不同维度，最后汇总报告。

```
                 --> [Financial Analyst Agent] --
[Task Dispatcher] --> [Tech Analyst Agent]      --> [Aggregator Agent]
                 --> [Market Analyst Agent]     --
```

并行式的优势在于执行效率高，多个 Agent 同时工作可以大幅缩短总执行时间。劣势是结果汇总可能面临冲突（不同 Agent 给出矛盾结论），需要额外的冲突解决机制。

典型应用场景：多维度分析任务，如投资决策时同时从财务、技术、市场三个维度分析一家公司。

### 辩论式协作（Debate）

辩论式协作中，多个 Agent 针对同一问题提出不同观点，通过多轮辩论达成共识或呈现多元视角。这种模式类似于学术辩论赛：正方和反方各自论证，评委综合评判。

```
[Question] --> [Agent A: Pro]  <---> [Agent B: Con]
                      |                |
                      v                v
              [Round 1: Arguments]
                      |
              [Round 2: Rebuttals]
                      |
              [Round 3: Synthesis]
                      |
              [Judge Agent: Final Decision]
```

辩论式的优势在于能够充分探索问题的多个面相，减少单一视角的偏见，提升决策质量。劣势是 Token 消耗大（多轮对话），且辩论可能陷入僵局无法收敛。

典型应用场景：高风险决策任务，如"是否应该投资某项目"、"某方案的安全风险评估"。

### 协作模式对比

| 模式 | 拓扑结构 | 通信开销 | 并行度 | 适用场景 | 主要风险 |
|------|---------|---------|--------|---------|---------|
| 层级式 | 树状 | 中 | 低 | 复杂任务分解 | 顶层瓶颈 |
| 流水线式 | 链式 | 低 | 无 | 流程化生产 | 级联阻塞 |
| 并行式 | 星状 | 中 | 高 | 多维分析 | 结果冲突 |
| 辩论式 | 网状 | 高 | 无 | 高风险决策 | 不收敛 |

在实际系统中，这些模式并非互斥的。一个复杂的多 Agent 系统可能在不同层级采用不同模式。例如，外层使用层级式进行任务分解，子任务内部使用流水线式执行，关键决策点使用辩论式进行多视角验证。

## 7.3 Agent 通信协议与信息交换机制

多 Agent 系统的核心挑战之一是 Agent 之间的通信。通信协议定义了 Agent 如何交换信息、如何寻址对方、如何确保消息被正确理解。通信机制的设计直接影响系统的协作效率和可靠性。

### 通信模式分类

在多 Agent 系统中，通信模式可以分为两大类：直接通信和间接通信。

直接通信是指 Agent 之间显式地发送和接收消息。发送方明确知道接收方的身份，消息通过点对点或广播的方式传递。这种方式类似于人类之间的对话：你明确知道在和谁说话。

间接通信是指 Agent 通过共享环境（如黑板模型、共享内存、消息队列）进行信息交换。Agent 不直接寻址对方，而是将信息写入共享空间，其他 Agent 自行读取。这种方式类似于论坛发帖：你不知道谁会看到，但感兴趣的人会来读取。

以下是两种通信模式的对比：

| 维度 | 直接通信 | 间接通信 |
|------|---------|---------|
| 寻址方式 | 显式指定接收方 | 通过共享空间 |
| 耦合度 | 高耦合 | 低耦合 |
| 可扩展性 | 差（连接数 O(n^2)） | 好（线性扩展） |
| 消息可靠性 | 高（有确认机制） | 低（无确认） |
| 典型实现 | RPC、消息队列 | 黑板模型、Pub/Sub |

### 消息格式设计

在 LLM-based 的多 Agent 系统中，消息通常采用结构化格式。以下是一个典型的 Agent 间消息格式：

```python
from pydantic import BaseModel
from typing import Optional

class AgentMessage(BaseModel):
    sender: str                    # 发送方 Agent ID
    receiver: str                  # 接收方 Agent ID, "broadcast" 表示广播
    msg_type: str                  # 消息类型: request/response/notify
    content: str                   # 消息正文
    task_id: str                   # 关联的任务 ID
    reply_to: Optional[str] = None # 回复的消息 ID
    metadata: dict = {}            # 附加元数据
    timestamp: str = ""            # 时间戳
```

消息类型的设计尤为关键。常见的消息类型包括：

- request：请求其他 Agent 执行某项操作
- response：对请求的回复
- notify：通知事件发生，不期待回复
- delegate：将任务委托给其他 Agent
- escalate：向上层 Agent 报告问题或请求决策

### 通信协议实例：FIPA ACL 参考

在传统的多 Agent 系统研究中，FIPA (Foundation for Intelligent Physical Agents) 组织定义了一套标准的 Agent 通信语言（ACL, Agent Communication Language）。虽然 LLM-based Agent 系统很少直接使用 FIPA ACL，但其设计理念值得借鉴。

FIPA ACL 定义了多种通信行为（communicative act），每种行为有明确的语义：

| 行为类型 | 语义 | 在 LLM Agent 中的对应 |
|---------|------|---------------------|
| inform | 告知对方某事实 | Agent 返回执行结果 |
| request | 请求对方执行动作 | 委派任务给其他 Agent |
| query | 询问信息 | 检索请求 |
| propose | 提出方案 | 辩论中提出论点 |
| accept/reject | 接受/拒绝提议 | 审查通过/驳回 |

### 实现层面的通信机制

在工程实现中，Agent 间的通信通常通过以下机制实现：

**函数调用模式**：最简单的通信方式，Agent 之间直接通过函数调用传递数据。适用于单进程内的多 Agent 系统，如 AutoGen 的 GroupChat。

**消息队列模式**：通过消息中间件（如 Redis、RabbitMQ）传递消息。适用于分布式部署的多 Agent 系统，支持异步通信和解耦。

**共享状态模式**：所有 Agent 读写同一个共享状态对象（如黑板模型）。适用于需要全局状态一致性的场景。

```python
# 基于共享黑板模型的通信示例
class Blackboard:
    def __init__(self):
        self._data = {}
        self._subscribers = {}
    
    def write(self, key: str, value: str, writer: str):
        self._data[key] = {"value": value, "writer": writer}
        # 通知订阅了该 key 的 Agent
        for agent in self._subscribers.get(key, []):
            agent.notify(key, value)
    
    def read(self, key: str) -> str | None:
        entry = self._data.get(key)
        return entry["value"] if entry else None
    
    def subscribe(self, key: str, agent):
        self._subscribers.setdefault(key, []).append(agent)
```

### 通信中的语义理解挑战

与传统的分布式系统不同，LLM Agent 之间的通信面临独特的语义理解挑战。传统系统中，消息格式是严格定义的，解析是确定性的。但在 LLM Agent 系统中，消息内容是自然语言，存在歧义和误解的可能。

例如，Agent A 发送"请分析这个数据集的趋势"，Agent B 可能理解为进行时间序列分析，也可能理解为做统计描述。这种语义歧义需要通过以下方式缓解：

- 在系统提示词中明确定义每个 Agent 的输入输出格式
- 使用结构化消息（JSON）而非纯自然语言
- 引入确认机制：接收方复述理解，发送方确认
- 建立领域词汇表，减少歧义

## 7.4 信息一致性与状态同步

多 Agent 系统中，多个 Agent 各自维护独立的上下文和状态。当 Agent 之间需要协作时，如何保证信息一致性成为一个关键问题。这类似于分布式系统中的数据一致性问题，但增加了自然语言带来的不确定性。

### 一致性问题的来源

信息不一致主要来源于以下几个方面：

**异步执行导致的信息滞后**：在并行式协作中，Agent A 和 Agent B 同时开始工作。Agent A 在 t=1 时刻更新了某个共享数据，但 Agent B 在 t=2 时刻读取的仍是旧数据。这种时间差导致的状态不一致在分布式系统中普遍存在。

**理解偏差导致的信息失真**：Agent A 发送了一段自然语言描述的结果，Agent B 在理解时可能产生偏差。例如，Agent A 说"测试通过了"，Agent B 可能理解为"所有测试都通过了"，但实际上 Agent A 只是指"当前测试用例通过了"。

**推理路径不同导致的结论分歧**：面对相同的信息，不同角色设定的 Agent 可能得出不同结论。例如，安全审查 Agent 认为某代码存在风险，而功能审查 Agent 认为该代码功能正确。这种分歧不一定是错误，但需要被识别和处理。

### 状态同步策略

针对不同类型的一致性问题，可以采用不同的同步策略：

**强一致性同步**：所有 Agent 在关键决策点必须读取最新的共享状态。通过锁机制或版本控制确保一致性。适用于关键决策场景，但会降低系统并行度。

```python
class StateManager:
    def __init__(self):
        self._state = {}
        self._version = 0
        self._lock = threading.Lock()
    
    def update(self, key, value, agent_id):
        with self._lock:
            self._state[key] = {
                "value": value,
                "version": self._version + 1,
                "updated_by": agent_id
            }
            self._version += 1
    
    def read(self, key, min_version=None):
        with self._lock:
            entry = self._state.get(key)
            if not entry:
                return None
            if min_version and entry["version"] < min_version:
                return None  # 版本过旧，拒绝读取
            return entry
```

**最终一致性同步**：允许 Agent 在短时间内使用过时信息，通过定期同步机制最终达到一致。适用于非关键路径的信息同步，性能更好。

**事件溯源模式**：不存储当前状态，而是存储所有状态变更事件。Agent 通过重放事件来重建状态。这种模式天然支持审计和回溯，适合需要调试的多 Agent 系统。

### 冲突检测与解决

当多个 Agent 对同一问题给出不同结论时，系统需要冲突检测和解决机制：

**投票机制**：多个 Agent 对同一问题投票，少数服从多数。适用于客观事实类问题，如代码是否通过编译。

**优先级机制**：为不同 Agent 设定优先级，冲突时采用高优先级 Agent 的结论。适用于有明确专业层级差异的场景，如安全问题的最终决定权归安全专家 Agent。

**升级机制**：当 Agent 间无法解决冲突时，将问题升级到上层 Agent 或人类决策者。适用于高风险决策场景。

**辩论机制**：让冲突双方各自阐述理由，由第三方 Agent 裁决。适用于需要深度分析的问题，对应 7.7 节的 Agent Debate 模式。

### 上下文管理的工程实践

在实际工程中，一个有效的做法是维护一个"会话状态对象"（Session State Object），所有 Agent 共享该对象的只读视图，但只有特定的协调 Agent 拥有写权限。

```python
class SessionState:
    """多 Agent 共享的会话状态"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.facts: dict = {}        # 已确认的事实
        self.artifacts: dict = {}    # 产出物（代码、文档等）
        self.open_questions: list = []  # 待解决的问题
        self.decisions: list = []    # 已做的决策
    
    def add_fact(self, key, value, source_agent):
        self.facts[key] = {
            "value": value,
            "source": source_agent,
            "confirmed": False
        }
    
    def confirm_fact(self, key, confirming_agent):
        if key in self.facts:
            self.facts[key]["confirmed"] = True
            self.facts[key]["confirmed_by"] = confirming_agent
    
    def get_snapshot(self) -> dict:
        """返回只读快照给各 Agent"""
        return {
            "facts": dict(self.facts),
            "artifacts": dict(self.artifacts),
            "open_questions": list(self.open_questions),
            "decisions": list(self.decisions)
        }
```

这种设计确保了状态的一致性和可追溯性：每个事实都有来源标记，每个决策都有记录，便于事后审计和调试。

## 7.5 主流框架对比：AutoGen、CrewAI、LangGraph

当前多 Agent 领域有三个主流框架，各自代表了不同的设计哲学。理解它们的差异对于选型和面试都至关重要。

### AutoGen

AutoGen 是微软研究院开发的多 Agent 对话框架。其核心理念是：通过 Agent 之间的对话来完成任务。AutoGen 最经典的模式是 GroupChat，多个 Agent 在一个群聊中交互，由一个管理 Agent 控制发言顺序。

AutoGen 的设计特点是"对话优先"。Agent 之间的所有交互都是自然语言对话，框架负责管理对话历史和发言轮转。这种设计使得 AutoGen 非常适合需要大量自然语言交流的任务，如头脑风暴、方案讨论。

```python
import autogen

# 创建 Agent
researcher = autogen.AssistantAgent(
    name="Researcher",
    system_prompt="你是一位研究员，负责收集和分析信息。",
    llm_config={"model": "gpt-4"}
)

coder = autogen.AssistantAgent(
    name="Coder",
    system_prompt="你是一位程序员，负责编写代码。",
    llm_config={"model": "gpt-4"}
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5
)

# 创建 GroupChat
groupchat = autogen.GroupChat(
    agents=[user_proxy, researcher, coder],
    messages=[],
    max_round=10
)

manager = autogen.GroupChatManager(groupchat=groupchat)
user_proxy.initiate_chat(manager, message="研究并实现一个快速排序算法")
```

### CrewAI

CrewAI 是一个以"角色扮演"为核心的多 Agent 框架。其设计理念是：每个 Agent 扮演一个明确的角色，拥有特定的目标、背景和工具集。CrewAI 强调"crew"（团队）的概念，通过任务（Task）和流程（Process）来组织 Agent 协作。

CrewAI 的特点是"角色驱动"。每个 Agent 的行为主要由其角色定义决定，而非对话历史。这使得 CrewAI 的行为更加可预测，适合流程化任务。

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role='市场研究员',
    goal='收集目标市场的关键数据',
    backstory='你是一位资深市场分析师，擅长数据收集和分析。',
    verbose=True
)

writer = Agent(
    role='内容撰写人',
    goal='基于研究结果撰写报告',
    backstory='你是一位专业技术作家，擅长将复杂数据转化为易读报告。',
    verbose=True
)

research_task = Task(
    description='分析 2024 年 AI Agent 市场规模和趋势',
    agent=researcher,
    expected_output='一份包含数据和分析的市场研究报告'
)

write_task = Task(
    description='基于研究报告撰写一份面向投资者的摘要',
    agent=writer,
    expected_output='一份 500 字的投资摘要'
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential
)

result = crew.kickoff()
```

### LangGraph

LangGraph 是 LangChain 团队推出的基于图结构的多 Agent 编排框架。其核心理念是：将 Agent 协作建模为状态图（State Graph），节点是 Agent 或处理函数，边是状态转移逻辑。

LangGraph 的特点是"图驱动"。它不预设特定的协作模式，而是通过图的拓扑结构来定义任意复杂的协作流程。这使得 LangGraph 的灵活性最高，但也带来了更高的学习成本。

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_agent: str

def research_node(state: AgentState):
    # 研究Agent的处理逻辑
    return {"messages": [{"role": "assistant", "content": "研究完成"}]}

def review_node(state: AgentState):
    # 审查Agent的处理逻辑
    return {"messages": [{"role": "assistant", "content": "审查通过"}]}

def router(state: AgentState) -> str:
    last_msg = state["messages"][-1]["content"]
    if "需要修改" in last_msg:
        return "research"
    return "end"

# 构建状态图
workflow = StateGraph(AgentState)
workflow.add_node("research", research_node)
workflow.add_node("review", review_node)

workflow.set_entry_point("research")
workflow.add_conditional_edges("review", router, {
    "research": "research",
    "end": END
})
workflow.add_edge("research", "review")

app = workflow.compile()
result = app.invoke({"messages": [{"role": "user", "content": "开始任务"}]})
```

### 框架详细对比

| 维度 | AutoGen | CrewAI | LangGraph |
|------|---------|--------|-----------|
| 开发者 | 微软研究院 | CrewAI Inc. | LangChain |
| 核心理念 | 对话驱动 | 角色驱动 | 图结构驱动 |
| 协作模式 | 主要是群聊对话 | 顺序/层级流程 | 任意自定义图 |
| 状态管理 | 对话历史 | 任务状态 | 显式状态图 |
| 灵活性 | 中等 | 较低 | 最高 |
| 学习成本 | 中等 | 最低 | 最高 |
| 人类介入 | 内置支持 | 有限 | 完全可控 |
| 流程控制 | GroupChat Manager | Process 参数 | 条件边+循环 |
| 适用场景 | 开放式讨论 | 流程化任务 | 复杂工作流 |
| 工具集成 | 自动工具调用 | 自定义工具 | LangChain 生态 |
| 持久化 | 对话保存 | 有限 | 检查点机制 |
| 分布式 | 支持 | 不支持 | 支持 |

### 选型建议

选择框架时应考虑任务特性和团队能力：

如果任务需要开放式讨论和灵活的 Agent 交互，且对话过程中可能产生不可预测的分支，AutoGen 的 GroupChat 模式最为适合。例如，头脑风暴、方案评审等探索性任务。

如果任务有明确的流程定义，每个步骤都有清晰的输入输出，且角色分工明确，CrewAI 的角色驱动模式最为简洁高效。例如，内容生产流水线、标准化报告生成。

如果任务流程复杂，包含条件分支、循环、并行执行、人在回路等多种控制流，且需要精确控制状态转移，LangGraph 提供了最强大的表达能力。例如，复杂的 RAG (Retrieval-Augmented Generation, 检索增强生成) 工作流、多阶段审批流程。

在实际项目中，也可以混合使用多个框架。例如，使用 LangGraph 构建整体工作流框架，在特定节点中使用 AutoGen 的 GroupChat 进行开放式讨论。

## 7.6 角色定义与任务分配策略

多 Agent 系统的设计核心之一是角色定义。角色定义决定了 Agent 的行为边界、专业领域和交互方式。一个好的角色定义应该包含以下几个要素：

### 角色定义的要素

**身份描述**：Agent 是谁，具备什么专业背景。这直接影响 LLM 的生成倾向。例如，"你是一位有 10 年经验的网络安全工程师"比"你是安全 Agent"更能引导出专业的安全分析。

**职责边界**：Agent 负责什么，不负责什么。明确的边界避免角色重叠和职责真空。例如，"你只负责代码安全审查，不负责功能正确性检查"。

**行为规范**：Agent 应该如何执行任务，包括输出格式、思考方式、与他人的交互规则。例如，"你的输出必须包含风险等级（高/中/低）和具体建议"。

**工具集**：Agent 可以使用哪些工具。工具集应该与角色职责匹配，避免过度授权。例如，审查 Agent 不应该有代码修改权限，只能提出建议。

以下是一个完整的角色定义示例：

```python
# 角色定义模板
SECURITY_AUDITOR_PROMPT = """
## 身份
你是一位具有 15 年经验的网络安全审计工程师，精通 OWASP Top 10 
漏洞分析和安全编码规范。

## 职责
- 审查代码中的安全漏洞（SQL注入、XSS、CSRF等）
- 评估安全风险等级（高/中/低）
- 提供修复建议和改进方案

## 限制
- 不负责功能正确性验证（由功能测试Agent负责）
- 不直接修改代码（只提出建议）
- 对于不确定的安全问题，标注"需进一步验证"

## 输出格式
{
    "risk_level": "高/中/低",
    "vulnerability_type": "漏洞类型",
    "description": "漏洞描述",
    "location": "代码位置",
    "fix_suggestion": "修复建议"
}
"""
```

### 任务分配策略

任务分配是多 Agent 系统的调度核心。好的任务分配策略应该考虑以下几个因素：

**能力匹配**：将任务分配给具备相应能力的 Agent。这要求系统维护一个 Agent 能力描述表。

**负载均衡**：避免某些 Agent 过载而其他 Agent 空闲。在有多个同类 Agent 时，按负载分配任务。

**依赖顺序**：尊重任务间的依赖关系。如果任务 B 依赖任务 A 的输出，则必须等 A 完成后再分配 B。

**优先级**：高优先级任务应优先分配和执行。

以下是一个基于能力的任务分配器示例：

```python
class TaskAllocator:
    def __init__(self):
        self.agents = {}  # agent_id -> capability list
        self.agent_load = {}  # agent_id -> current task count
    
    def register_agent(self, agent_id, capabilities):
        self.agents[agent_id] = capabilities
        self.agent_load[agent_id] = 0
    
    def allocate(self, task):
        """根据任务需求分配最合适的Agent"""
        required_caps = task.get("required_capabilities", [])
        candidates = []
        
        for agent_id, caps in self.agents.items():
            # 检查能力匹配
            if all(cap in caps for cap in required_caps):
                candidates.append((agent_id, self.agent_load[agent_id]))
        
        if not candidates:
            return None  # 无可用Agent
        
        # 选择负载最低的候选Agent
        candidates.sort(key=lambda x: x[1])
        chosen = candidates[0][0]
        self.agent_load[chosen] += 1
        return chosen
    
    def release(self, agent_id):
        """任务完成后释放Agent负载"""
        self.agent_load[agent_id] = max(0, self.agent_load[agent_id] - 1)
```

### 角色设计的常见陷阱

**角色定义过于宽泛**：例如"你是一个有用的助手"几乎没有提供任何角色约束。LLM 在没有明确角色定位时，行为会趋于平庸和泛化。

**角色之间存在大面积重叠**：两个 Agent 的职责高度重叠会导致冗余工作和潜在冲突。例如"代码审查 Agent"和"质量检查 Agent"如果没有清晰界定边界，可能对同一段代码给出重复或矛盾的意见。

**角色定义忽略约束**：只定义了 Agent 应该做什么，但没有定义不应该做什么。缺少约束的 Agent 可能过度发挥，越界操作。

**忽视角色间的权力关系**：在某些协作模式中（如层级式），Agent 之间存在上下级关系。如果角色定义中没有体现这种权力关系，Agent 可能不服从调度或越权决策。

### 动态角色分配

在更高级的多 Agent 系统中，角色不是预先固定的，而是根据任务动态分配。Orchestrator Agent 根据任务需求，从角色池中选择合适的角色组合，动态实例化 Agent。

这种动态分配模式的优势在于灵活性：同一套系统可以处理不同类型的任务，每次只激活需要的角色。劣势在于不可预测性：难以预先知道哪些 Agent 会被激活，增加了调试难度。

## 7.7 Agent Debate：多视角碰撞提升决策质量

Agent Debate 是多 Agent 系统中一种特殊的协作模式，通过让多个 Agent 从不同视角对同一问题进行辩论，来提升决策质量。这种模式受到人类社会中"对抗性审议"（Adversarial Deliberation）的启发：通过正反双方的激烈辩论，揭示问题的各个面相，避免单一视角的盲点。

### Agent Debate 的理论基础

Agent Debate 的理论基础可以追溯到几个研究领域：

**德尔菲法（Delphi Method）**：一种结构化的专家咨询方法，通过多轮匿名问卷调查收集专家意见，每轮结束后反馈汇总结果，专家据此调整自己的观点。Agent Debate 借鉴了多轮迭代和反馈调整的理念。

**红蓝对抗（Red Teaming / Blue Teaming）**：来自网络安全领域的实践，红队负责攻击，蓝队负责防守。通过对抗性测试发现系统的薄弱环节。在 Agent Debate 中，这种对抗性思维被推广到一般决策场景。

**批判性思维理论**：有效的决策不仅需要支持论据，还需要考虑反对论据。单一 Agent 容易出现"确认偏误"（Confirmation Bias），即倾向于寻找支持自己观点的证据。多个具有不同立场的 Agent 可以相互制衡。

### Agent Debate 的流程设计

一个典型的 Agent Debate 流程包含以下阶段：

```
[输入: 待决策问题]
        |
        v
[阶段1: 立场生成] -- 多个Agent分别给出初始立场和论据
        |
        v
[阶段2: 论辩交锋] -- 各Agent看到其他Agent的论据后进行反驳
        |          (可多轮, 通常2-3轮)
        v
[阶段3: 立场调整] -- Agent根据辩论内容调整自己的立场
        |
        v
[阶段4: 共识综合] -- Judge Agent综合所有论据, 给出最终决策
        |
        v
[输出: 决策结果 + 理由 + 风险提示]
```

每个阶段的设计要点如下：

**立场生成阶段**：各 Agent 独立分析问题，不知道其他 Agent 的观点。这确保了初始立场的独立性，避免"锚定效应"（Anchoring Bias）。

**论辩交锋阶段**：各 Agent 看到其他 Agent 的论据后，需要提出反驳。关键是要求 Agent 不仅反驳对方，还要回应对方对自己的反驳。这种"交叉质询"机制能深入挖掘问题。

**立场调整阶段**：允许 Agent 根据辩论内容调整自己的立场。一个设计良好的 Debate 系统应该鼓励 Agent 在遇到有力论据时改变观点，而不是固执己见。

**共识综合阶段**：由中立的 Judge Agent 综合所有论据，做出最终决策。Judge Agent 可以采用投票、加权评分或综合分析等方式。

### 代码实现示例

以下是一个简化的 Agent Debate 实现：

```python
import json

class DebateAgent:
    def __init__(self, name, stance, llm_client):
        self.name = name
        self.stance = stance  # "pro" or "con"
        self.llm = llm_client
        self.arguments = []
    
    def generate_argument(self, question, context=""):
        prompt = f"""
        问题: {question}
        你的立场: {"支持" if self.stance == "pro" else "反对"}
        已有论据: {context}
        
        请给出你的论据(不超过200字), 包含:
        1. 核心观点
        2. 支撑理由
        3. 对对方论据的反驳(如有)
        """
        response = self.llm.complete(prompt)
        self.arguments.append(response)
        return response

class JudgeAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def decide(self, question, all_arguments):
        prompt = f"""
        问题: {question}
        正反方论据记录:
        {json.dumps(all_arguments, ensure_ascii=False, indent=2)}
        
        请作为中立裁判:
        1. 总结双方核心论据
        2. 评估各方论据的说服力(1-10分)
        3. 给出最终决策和理由
        4. 标注残余风险
        """
        return self.llm.complete(prompt)

def run_debate(question, pro_agent, con_agent, judge, rounds=3):
    transcript = {"question": question, "rounds": []}
    context = ""
    
    for r in range(rounds):
        pro_arg = pro_agent.generate_argument(question, context)
        con_arg = con_agent.generate_argument(question, pro_arg)
        context += f"\nRound {r+1}:\nPro: {pro_arg}\nCon: {con_arg}"
        transcript["rounds"].append({"pro": pro_arg, "con": con_arg})
    
    decision = judge.decide(question, transcript["rounds"])
    transcript["decision"] = decision
    return transcript
```

### Debate 的变体模式

除了经典的正反双方辩论，Agent Debate 还有多种变体：

**多视角辩论**：不限于正反两方，可以有多个不同视角的 Agent。例如，在评估一个技术方案时，可以有性能视角 Agent、安全视角 Agent、成本视角 Agent 和用户体验视角 Agent，各自从自己的专业角度提出论据。

**红蓝绿对抗**：在安全评估场景中，红队 Agent 负责发现漏洞，蓝队 Agent 负责防御论证，绿队 Agent 负责提出改进方案。三方博弈形成更完整的评估闭环。

**自我辩论**：单个 Agent 轮流扮演正方和反方，通过内部对话进行自我审查。虽然不如多 Agent 辩论有效，但成本更低，适用于资源受限的场景。

### Debate 的效果与局限

研究表明，Agent Debate 在以下场景中效果显著：

- 需要权衡利弊的决策问题（如技术选型、方案评审）
- 需要多维度评估的风险分析（如安全评估、合规审查）
- 创意生成任务（通过观点碰撞激发新思路）

但 Agent Debate 也有明显的局限性：

**成本问题**：多轮辩论意味着多次 LLM 调用，Token 消耗是单 Agent 的数倍。对于简单决策，这种成本不值得。

**收敛问题**：辩论可能陷入僵局，双方都无法说服对方，最终仍然依靠 Judge 裁决。如果 Judge 的能力不足，辩论的价值会大打折扣。

**虚假辩论风险**：如果所有 Agent 基于同一个 LLM，它们的"观点差异"可能只是表面文章，实质上仍受模型训练数据的偏见影响。真正的多视角需要不同模型或不同参数配置来保证多样性。

## 7.8 人在回路的多 Agent 系统

人在回路（Human-in-the-Loop, HITL）的多 Agent 系统是指在 Agent 自动化流程的关键节点引入人类决策的协作模式。这种模式认识到：尽管 LLM Agent 的能力在不断提升，但在高风险决策、模糊判断和创造性任务中，人类的参与仍然不可或缺。

### 为什么需要人在回路

人在回路的需求主要来自以下几个方面：

**准确性保障**：在法律分析、医疗诊断、金融决策等高风险领域，Agent 的输出需要人类专家审核后才能执行。完全自动化的风险过高，一个错误的决策可能带来严重后果。

**模糊性消解**：当任务描述存在歧义，或 Agent 在执行过程中遇到多种合理路径时，需要人类来消解模糊性，选择方向。这种需求在开放性任务中尤为常见。

**创造性引导**：在创意写作、产品设计等需要人类审美和创造力的任务中，Agent 的输出往往需要人类的引导和调整才能达到理想效果。

**合规与审计**：在受监管的行业中，关键决策必须有人类参与和签字，这是法规要求，不是技术选择。

### 人在回路的介入点设计

人在回路的系统设计关键是选择合适的介入点。并非每个环节都需要人类参与，过度的介入会抵消自动化带来的效率提升。以下是几种常见的介入模式：

**审批式介入**：Agent 完成全部工作后，将结果提交给人类审批。人类可以选择批准、驳回或要求修改。这是最轻量级的介入模式，适用于 Agent 能力成熟、错误率低的场景。

```python
class HumanApprovalGate:
    def __init__(self, auto_execute=False):
        self.auto_execute = auto_execute
    
    async def review(self, agent_output, context):
        if self.auto_execute:
            return {"approved": True, "feedback": ""}
        
        # 展示结果给人类, 等待审批
        display_result(agent_output, context)
        human_response = await wait_for_human_input()
        
        return {
            "approved": human_response.get("approved", False),
            "feedback": human_response.get("feedback", ""),
            "modifications": human_response.get("modifications", None)
        }
```

**检查点式介入**：在任务流程的特定节点设置检查点，Agent 执行到检查点时暂停，等待人类确认后继续。适用于多阶段任务中关键转折点的质量控制。

**交互式介入**：人类可以在 Agent 执行过程中随时介入，提供指导、修改方向或纠正错误。这种模式最灵活，但对系统的实时性要求最高，通常需要 Agent 支持中断和恢复机制。

**升级式介入**：Agent 在遇到无法处理的情况时，主动请求人类帮助。这种模式要求 Agent 具备自我评估能力，能够识别自身的局限性。

### 介入点选择框架

选择介入点时应考虑以下因素：

| 因素 | 偏向自动化的条件 | 偏向人工介入的条件 |
|------|----------------|-------------------|
| 风险等级 | 低风险，可逆操作 | 高风险，不可逆操作 |
| 任务复杂度 | 结构化，规则明确 | 非结构化，需判断力 |
| Agent 置信度 | 高置信度（>90%） | 低置信度或不确定 |
| 错误代价 | 错误容易发现和纠正 | 错误代价高或难以发现 |
| 合规要求 | 无特殊合规要求 | 法规要求人工审核 |
| 频率 | 高频重复任务 | 低频一次性任务 |

### 人在回路的工程实现

在工程实现层面，人在回路需要解决几个技术问题：

**异步等待**：Agent 需要在等待人类响应时暂停执行，而不占用计算资源。这通常通过异步编程和消息队列实现。

**上下文保持**：人类响应可能需要时间（数小时甚至数天），在此期间需要保持 Agent 的执行上下文，以便恢复后继续执行。这要求系统具备状态持久化能力。

**超时处理**：人类可能未在预期时间内响应，系统需要定义超时策略：是无限等待、使用默认决策、还是将任务标记为失败。

**多审批人协作**：在需要多个审批人的场景中，需要定义审批规则：是全部同意才通过、多数同意即可、还是有优先级之分。

```python
class HITLOrchestrator:
    def __init__(self, agents, checkpoints, timeout=3600):
        self.agents = agents
        self.checkpoints = set(checkpoints)
        self.timeout = timeout
    
    async def run(self, task):
        state = {"task": task, "results": {}, "status": "running"}
        
        for step in task.steps:
            # 执行Agent
            result = await self.agents[step.agent].execute(step)
            state["results"][step.id] = result
            
            # 检查是否需要人工审核
            if step.id in self.checkpoints:
                approval = await self.request_human_review(
                    result, step, state
                )
                
                if not approval["approved"]:
                    # 根据反馈调整或终止
                    if approval.get("retry"):
                        step.prompt = approval["feedback"]
                        continue  # 重新执行
                    else:
                        state["status"] = "rejected"
                        state["rejection_reason"] = approval["feedback"]
                        return state
        
        state["status"] = "completed"
        return state
    
    async def request_human_review(self, result, step, state):
        # 发送通知给人类审核者
        notify_reviewers(result, step)
        
        # 异步等待响应
        try:
            response = await asyncio.wait_for(
                self.wait_for_approval(step.id),
                timeout=self.timeout
            )
            return response
        except asyncio.TimeoutError:
            return {
                "approved": False,
                "feedback": "审核超时, 已自动拒绝"
            }
```

### 人在回路与 Agent 自主性的平衡

人在回路系统的设计本质是在自动化效率和人类控制之间寻找平衡。过多的介入会降低系统效率，使 Agent 沦为一个"高级表单填写工具"；过少的介入则可能导致错误累积，失去质量保障。

一个有效的策略是"动态介入"：根据 Agent 的置信度和任务风险等级动态调整介入级别。高置信度、低风险的任务可以自动执行；低置信度、高风险的任务必须人工审核。这种动态策略既保证了关键节点的质量控制，又最大化了自动化效率。

随着 Agent 能力的提升和信任的建立，系统可以逐步减少人工介入的频率，从"每步审批"过渡到"抽检审核"，最终达到"异常触发审核"的模式。这种渐进式放权策略在工业实践中被广泛采用。

### 实际应用案例

在软件开发领域，一个典型的人在回路多 Agent 系统如下：

需求分析 Agent 自动解析用户需求，生成技术方案草案。架构师（人类）审核方案，确认技术选型和系统架构。开发 Agent 根据审核通过的方案编写代码。代码审查 Agent 进行自动化代码审查，高风险修改需高级开发者（人类）确认。测试 Agent 编写并执行测试用例。测试通过后自动部署到预发环境，发布到生产环境需要运维工程师（人类）最终审批。

这个流程中，人类介入了两个关键节点：方案审核和发布审批。其余环节由 Agent 自动完成，既保证了关键决策的质量，又保持了流程的效率。

## 本章知识点总结

| 知识点 | 核心内容 | 关键要点 |
|--------|---------|---------|
| 多 Agent 系统概述 | 单 Agent 的瓶颈与多 Agent 的优势 | 上下文竞争、角色混淆、工具爆炸是多 Agent 的驱动力 |
| 协作模式 | 层级式、流水线式、并行式、辩论式 | 不同模式适用于不同任务，实际系统常混合使用 |
| 通信协议 | 直接通信与间接通信、消息格式设计 | 语义理解是 LLM Agent 通信的独特挑战 |
| 状态同步 | 一致性问题来源与同步策略 | 强一致性、最终一致性、事件溯源三种模式 |
| 框架对比 | AutoGen、CrewAI、LangGraph | 对话驱动、角色驱动、图驱动三种设计哲学 |
| 角色定义 | 身份、职责、规范、工具集四要素 | 角色定义需避免宽泛、重叠、缺约束 |
| Agent Debate | 多轮辩论提升决策质量 | 包含立场生成、论辩交锋、立场调整、共识综合四阶段 |
| 人在回路 | 关键节点引入人类决策 | 介入点选择应基于风险等级、置信度、合规要求 |
| 任务分配 | 能力匹配、负载均衡、依赖顺序 | 动态角色分配提升系统灵活性 |
| 通信行为类型 | inform/request/query/propose | 借鉴 FIPA ACL 的语义分类设计消息类型 |
| 冲突解决 | 投票、优先级、升级、辩论 | 不同机制适用于不同冲突类型 |
| HITL 介入模式 | 审批式、检查点式、交互式、升级式 | 动态介入根据置信度和风险等级调整级别 |

# 第六章：Agent 规划与决策

Agent 的核心能力不在于单次推理的质量，而在于面对复杂任务时能否做出合理的规划与决策。一个没有规划能力的 LLM 只是一个问答机器，而一个具备规划能力的 Agent 则能拆解目标、分配资源、动态调整策略，并在执行过程中不断自我修正。本章将深入探讨 Agent 在规划与决策层面的关键技术，从任务拆解到树搜索决策，从反思机制到长时任务处理，覆盖 Agent 规划体系的完整脉络。

## 6.1 Task Decomposition：复杂任务的拆解艺术

任务拆解（Task Decomposition）是 Agent 规划能力的基石。当一个复杂目标被输入到 Agent 系统中时，第一步就是将这个高层级的抽象目标转化为一系列可执行的原子操作。这个过程看似简单，实际上涉及对任务结构的深度理解、对依赖关系的准确判断，以及对执行资源合理预估。

### 任务拆解的基本原理

任务拆解的核心思想是分而治之（Divide and Conquer）。一个复杂任务通常具有层次结构，可以逐层分解为子任务，直到每个子任务的粒度足够小，能够被单个工具调用或单次推理完成。关键在于找到合适的分解粒度——太粗则执行不下去，太细则规划开销过大且容易陷入局部细节。

一个有效的任务拆解需要满足三个约束条件。第一是 MECE 原则（Mutually Exclusive, Collectively Exhaustive，相互独立、完全穷尽），即子任务之间不重叠，且合起来能完整覆盖父任务的目标。第二是可执行性，每个叶子任务都应对应一个明确的动作或工具调用。第三是依赖有序性，子任务之间的执行顺序必须符合逻辑依赖关系。

### 拆解策略的分类

常见的任务拆解策略可以分为三类：

| 策略类型 | 描述 | 适用场景 | 潜在问题 |
|---------|------|---------|---------|
| 线性拆解 | 按时间顺序逐步分解 | 流程明确的任务 | 缺乏灵活性，无法处理分支 |
| 树形拆解 | 按功能模块分层分解 | 结构化任务 | 依赖关系复杂时难以管理 |
| 图拆解 | 按依赖关系构建 DAG | 并行任务 | 规划成本高 |

在实际的 Agent 系统中，最常用的是线性拆解和树形拆解的组合。线性拆解用于确定主干流程，树形拆解用于处理每个主干节点内部的子任务分解。

### 代码示例：基于 LLM 的任务拆解

以下代码展示了如何通过 Prompt 引导 LLM 进行结构化任务拆解：

```python
from pydantic import BaseModel
from typing import List, Optional

class SubTask(BaseModel):
    name: str
    description: str
    dependencies: List[str] = []
    tool_hint: Optional[str] = None

class TaskPlan(BaseModel):
    goal: str
    subtasks: List[SubTask]

DECOMPOSE_PROMPT = """你是任务规划专家。将以下目标拆解为子任务。

要求：
1. 每个子任务必须是可执行的原子操作
2. 标注子任务间的依赖关系
3. 子任务数量在3-8个之间
4. 给出建议使用的工具名称

目标: {goal}

可用工具: {tools}
"""

async def decompose_task(goal: str, tools: list[str]) -> TaskPlan:
    prompt = DECOMPOSE_PROMPT.format(goal=goal, tools=", ".join(tools))
    response = await llm.generate(prompt, response_format=TaskPlan)
    return response
``这段代码的核心思路是利用 Pydantic 模型约束 LLM 的输出格式，确保拆解结果包含任务名称、描述、依赖关系和工具提示。依赖关系列表中的字符串引用的是其他子任务的名称，执行器可以据此构建依赖图并确定执行顺序。

### 拆解粒度的控制

拆解粒度是任务拆解中最难把握的维度。一个经验法则是：如果子任务可以直接用一个工具调用完成，就不需要继续拆解。但在实际场景中，很多任务的边界并不清晰。

一种实用的方法是自适应深度拆解。Agent 首先进行粗粒度拆解，然后在执行阶段对无法直接完成的子任务进行二次拆解。这种递归式的拆解策略既能控制初始规划的开销，又能在遇到复杂子任务时自动深化。

自适应拆解的关键在于设定一个终止条件——当子任务的预估执行步骤数低于某个阈值时停止拆解。这需要 Agent 对自身能力有准确的认知，即所谓的"元认知"能力。当前的主流 Agent 框架如 LangChain 和 AutoGen 都采用了类似的递归拆解策略。

### 任务拆解中的常见陷阱

第一个陷阱是过度拆解。有些 Agent 会将简单任务拆解成十几个甚至几十个微步骤，导致规划本身消耗大量 token 和时间，而实际执行效率并未提升。解决方案是设定拆解深度的上限，通常不超过三层。

第二个陷阱是忽略隐式依赖。LLM 在拆解任务时往往只关注显式的逻辑依赖，而忽略了数据依赖和资源依赖。例如，"查询数据库"和"生成报告"之间存在数据依赖——报告需要查询结果作为输入。如果拆解时没有标注这种依赖，执行时就会出现数据缺失的问题。

第三个陷阱是拆解结果不可回溯。一旦 Agent 开始执行，发现某个子任务无法完成，却没有能力重新规划。这就引出了后面要讨论的动态规划调整和反思机制。

## 6.2 Plan-and-Execute vs ReAct：两种规划模式的对比与融合

在 Agent 的规划范式中，有两种模式占据了主导地位：Plan-and-Execute（先规划后执行）和 ReAct (Reasoning and Acting，推理与行动交错)。这两种模式代表了规划策略谱系的两端——一个是重规划轻反馈，另一个是重反馈轻规划。理解它们的差异、优劣和融合方式，是设计 Agent 系统的关键能力。

### Plan-and-Execute 模式

Plan-and-Execute 的核心思想是"谋定而后动"。Agent 在执行任何动作之前，先制定一个完整的计划，然后按计划逐步执行。这个模式最早在 Plan-and-Solve prompting 中被系统化提出，后来被 LangChain 等框架实现为独立的 Agent 类型。

Plan-and-Execute 的工作流程分为三个阶段。规划阶段：LLM 根据任务目标生成一个有序的步骤列表。执行阶段：按照计划逐步执行每个步骤，收集中间结果。合并阶段：将所有步骤的结果合并为最终输出。

这种模式的优势在于规划的全局性。由于 LLM 在规划阶段能看到任务全貌，生成的计划通常具有较好的连贯性和全局最优性。同时，执行阶段不需要反复调用 LLM 进行推理，减少了 token 消耗和延迟。

但它的劣势同样明显。计划是静态的，无法根据执行过程中的中间结果进行调整。如果第三步的执行结果与预期不符，第四步及之后的计划可能全部失效。

### ReAct 模式

ReAct 模式由 Yao 等人在 2022 年提出，其核心思想是推理与行动交替进行。Agent 在每一步都先推理当前状态，然后选择一个动作执行，根据执行结果再进行下一步推理。这种模式更接近人类的即兴决策过程。

ReAct 的每个循环包含三个组件：Thought（思考）、Action（行动）、Observation（观察）。Thought 是 LLM 对当前状态的推理，Action 是选择的工具调用，Observation 是工具返回的结果。这个三角循环构成了 ReAct 的基本执行单元。

ReAct 的优势在于其灵活性和适应性。由于每一步都基于最新的观察结果进行推理，Agent 能够及时应对意外情况，动态调整策略。这使得 ReAct 在开放式任务和不确定性高的场景中表现优异。

代价是 token 消耗较高——每一步都需要完整的推理过程。同时，由于缺乏全局视角，ReAct 容易陷入局部最优，在某些需要长程规划的任务中表现不佳。

### 两种模式的对比

| 维度 | Plan-and-Execute | ReAct |
|------|-----------------|-------|
| 规划时机 | 前置一次性规划 | 边执行边规划 |
| 全局视野 | 强 | 弱 |
| 适应性 | 弱 | 强 |
| Token 消耗 | 低 | 高 |
| 错误恢复 | 需要重新规划 | 自然回退 |
| 适用任务 | 流程确定型 | 探索型 |

### 融合策略：Plan-and-Execute with Replan

单纯的 Plan-and-Execute 或 ReAct 都有其局限性。在实际的 Agent 系统中，更常用的是两者的融合——Plan-and-Execute with Replan（带重规划的先规划后执行）。

这种融合模式的工作流程如下：Agent 首先生成初始计划，然后逐步执行。每执行完一个步骤后，Agent 检查中间结果是否与预期一致。如果出现偏差，Agent 触发重规划，基于当前状态更新剩余计划。这样既保留了 Plan-and-Execute 的全局视野，又获得了 ReAct 的适应能力。

### 代码示例：两种模式的对比

以下是 ReAct 模式的核心循环：

```python
REACT_PROMPT = """Question: {question}
Thought: I need to find information about {topic}.
Action: search[{query}]
Observation: {observation}
Thought: Based on the result, I now know {finding}.
Action: finish[{answer}]
"""

async def react_loop(question: str, max_steps: int = 10):
    scratchpad = ""
    for step in range(max_steps):
        prompt = REACT_PROMPT.format(
            question=question, scratchpad=scratchpad
        )
        response = await llm.generate(prompt)
        if response.action == "finish":
            return response.answer
        result = await execute_tool(response.action)
        scratchpad += f"\nObservation: {result}"
    return "Max steps reached"
```

以下是 Plan-and-Execute with Replan 的核心逻辑：

```python
async def plan_and_execute(goal: str):
    plan = await planner.create_plan(goal)
    results = {}
    for i, step in enumerate(plan.steps):
        result = await executor.run(step, context=results)
        results[step.id] = result
        if not step.validate(result):
            # 触发重规划
            remaining = plan.steps[i+1:]
            new_plan = await planner.replan(
                goal, completed=plan.steps[:i+1],
                remaining=remaining, latest_result=result
            )
            plan.steps = plan.steps[:i+1] + new_plan.steps
    return results
```

对比两段代码可以看出，ReAct 的循环更加紧凑，每一步都是推理-行动-观察的闭环；而 Plan-and-Execute with Replan 在正常执行路径上更高效，但在遇到异常时需要触发重规划，增加了复杂度。

### 选择建议

对于流程相对确定的业务场景（如数据处理管道、报表生成），优先选择 Plan-and-Execute 模式。对于探索性强的场景（如信息检索、问题排查），ReAct 模式更合适。对于复杂度高的通用场景，推荐使用融合模式。在工程实践中，融合模式已经成为主流框架的默认选择，LangChain 的 Plan-and-Execute Agent 和 AutoGPT 的任务执行循环都采用了这种策略。

## 6.3 目标管理与动态规划调整

静态的计划无论多么完善，都无法应对真实世界的多变性。Agent 在执行过程中会遭遇各种意外——工具调用失败、中间结果不符合预期、用户需求发生变化。动态规划调整能力决定了 Agent 能否在变化中保持目标导向，而不是机械地执行一个已经失效的计划。

### 动态规划的触发条件

动态规划调整不是随机发生的，它由特定的触发条件驱动。理解这些触发条件是设计自适应 Agent 的前提。

第一类触发条件是执行偏差。当某个步骤的执行结果与预期显著不同时，剩余计划可能需要调整。例如，Agent 计划从数据库查询100条记录，实际只返回了3条，后续的分析步骤就需要修改。

第二类触发条件是资源变化。Agent 的可用资源（如 token 预算、时间限制、工具可用性）在执行过程中可能发生变化。如果某个 API 突然不可用，Agent 需要寻找替代方案。

第三类触发条件是目标漂移。在交互式场景中，用户可能在任务执行过程中修改或补充需求。Agent 需要识别这种变化，并将新需求纳入规划。

### 动态规划调整流程

以下流程图描述了动态规划调整的完整过程：

```
┌──────────────────────────────────────────────────────┐
│                    执行当前步骤                        │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
              ┌─────────┐
              │ 结果检查  │
              └────┬────┘
                   │
          ┌────────┴────────┐
          │                 │
      符合预期            偏差检测
          │                 │
          ▼                 ▼
      继续执行        ┌──────────┐
                      │ 影响评估  │
                      └────┬─────┘
                           │
                    ┌──────┴──────┐
                    │             │
               影响局部         影响全局
                    │             │
                    ▼             ▼
              调整后续步骤    重新规划
                    │             │
                    └──────┬──────┘
                           │
                           ▼
                      更新计划表
                           │
                           ▼
                      继续执行
```

这个流程的关键在于"影响评估"环节。不是所有的偏差都需要触发重规划——有些偏差是局部的，只需要微调后续步骤的参数即可。Agent 需要判断偏差的影响范围，决定是局部调整还是全局重规划。

### 重规划的策略

重规划不是从零开始。一个高效的重规划策略应该尽可能复用已完成的工作和未受影响的计划部分。具体来说有三种重规划策略：

增量重规划：仅替换受影响的步骤，保留未执行的步骤不变。这种策略成本最低，但只适用于偏差影响范围较小的情况。

回溯重规划：回退到最近的检查点，从该点重新规划。这种策略适用于偏差影响了多个后续步骤但尚未污染整个计划的情况。类似于游戏中的"读档重来"。

全局重规划：放弃原有计划，基于当前状态重新生成完整计划。这种策略成本最高，但适用于目标本身发生变化或偏差根本性改变了任务性质的情况。

### 代码示例：动态规划调整

```python
class PlanState:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.completed: list[Step] = []
        self.current_idx: int = 0

    def needs_replan(self, result: Result) -> bool:
        step = self.plan.steps[self.current_idx]
        return not step.validator(result)

    def replan(self, result: Result) -> None:
        impact = self.assess_impact(result)
        if impact.scope == "local":
            self.adjust_next_steps(result)
        elif impact.scope == "partial":
            self.replan_from_checkpoint(result)
        else:
            self.full_replan(result)

    def assess_impact(self, result: Result) -> Impact:
        # 用LLM评估偏差影响范围
        prompt = f"步骤{self.current_idx}的结果偏差为{result.delta}，\
        评估其对后续步骤的影响范围。"
        return llm.assess(prompt, response_format=Impact)
```

### 目标层级管理

在复杂的 Agent 系统中，目标不是扁平的，而是有层级的。顶层是用户的原始意图，中间层是拆解后的子目标，底层是具体的执行操作。动态规划调整需要在不同层级上运作。

当底层执行出现偏差时，调整主要发生在底层和中间层——修改具体步骤或替换子目标。当用户意图发生变化时，调整需要从顶层开始，逐级传导到下层。这种分层调整机制确保了 Agent 在面对不同尺度的变化时，能够选择合适的调整粒度。

一个实际的例子是代码编写任务。用户最初要求写一个 REST API，执行到一半时改为要求 GraphQL API。这个变更发生在顶层目标级别，Agent 需要重新拆解任务，而不是简单地修改某个步骤。但如果用户只是要求增加一个字段，那么调整只需要在底层进行——添加一个步骤并修改相关步骤的参数。

## 6.4 Reflection 机制：从错误中学习的自省能力

Reflection（反思）是 Agent 从执行过程中提取经验、识别错误并改进后续行为的能力。如果说规划是"向前看"，那么反思就是"向后看"。一个具备反思能力的 Agent 不仅仅是在执行任务，更是在执行过程中不断审视自己的决策质量，从而实现动态的自我提升。

### Reflection 的理论基础

Reflection 的概念来源于 Reflexion 框架，该框架由 Shinn 等人在 2023 年提出。其核心思想是让 Agent 在任务执行失败后，用自然语言总结失败原因，并将这个反思文本作为后续尝试的上下文。

这种机制借鉴了人类的认知模式。当人类在解决问题时遇到挫折，会回顾自己的思路，找出错误所在，并在下次尝试时避免同样的错误。Agent 的反思机制本质上是将这种元认知过程显式化——通过 LLM 的推理能力，将执行轨迹转化为可复用的经验。

Reflection 的有效性已在多项研究中得到验证。在 HotpotQA、AlfWorld 等基准测试中，具备反思能力的 Agent 比无反思的 Agent 成功率提高了10%到30%不等。提升的幅度与任务复杂度和试错次数正相关——任务越复杂、允许的尝试次数越多，反思带来的增益越大。

### Reflection 的工作流程

Reflection 机制的工作流程可以描述为以下步骤：

执行尝试：Agent 按照当前策略尝试完成任务，记录完整的执行轨迹。

结果评估：评估执行结果是否达到目标。评估可以由 Agent 自身完成（自评），也可以由外部评估器完成。

反思生成：如果执行失败，Agent 回顾执行轨迹，分析失败原因，生成反思文本。反思文本通常包含：什么地方出了错、为什么出错、下次应该怎么做。

经验存储：将反思文本存储在记忆中，作为后续尝试的参考。

重试改进：在下一次尝试中，Agent 将之前的反思文本纳入上下文，据此调整策略。

### 代码示例：Reflection 的实现

```python
REFLECTION_PROMPT = """你刚刚完成了以下任务尝试：

任务: {task}
执行轨迹: {trajectory}
结果: {result}

请反思：
1. 哪些步骤是有效的？
2. 哪些步骤导致了失败？
3. 失败的根本原因是什么？
4. 下次尝试时应该怎么做 differently？

请用简洁的语言输出反思。
"""

class ReflexionAgent:
    def __init__(self):
        self.reflections: list[str] = []

    async def attempt(self, task: str, max_attempts: int = 3):
        for i in range(max_attempts):
            context = self._build_context(task)
            result = await self.execute(task, context)
            if result.success:
                return result
            reflection = await self.reflect(task, result)
            self.reflections.append(reflection)
        return result

    async def reflect(self, task: str, result: Result):
        prompt = REFLECTION_PROMPT.format(
            task=task, trajectory=result.trajectory,
            result=result.summary
        )
        return await llm.generate(prompt)

    def _build_context(self, task: str) -> str:
        if not self.reflections:
            return task
        history = "\n".join(self.reflections)
        return f"{task}\n\n过往反思:\n{history}"
```

### 自评的可靠性问题

Reflection 机制的有效性高度依赖评估的准确性。如果 Agent 无法正确判断自己的执行结果是否正确，反思就可能建立在错误的判断之上——要么对失败的结果盲目满意，要么对正确的结果产生不必要的反思。

这个问题在开放式任务中尤为突出。对于有明确正确答案的任务（如数学计算），评估是简单的——对比答案即可。但对于创意写作、代码优化等开放性任务，"正确"的边界是模糊的。

解决方案是引入多维评估。不仅仅评估最终结果，还评估执行过程中的关键决策点。例如，在代码生成任务中，可以评估代码的功能正确性、风格规范性、性能指标等多个维度。多维评估提供了更丰富的反思素材，有助于 Agent 生成更有价值的反思文本。

### Reflection 的变体与扩展

基本的 Reflection 机制只涉及单 Agent 的自省。在此基础上，研究者提出了多种扩展：

多 Agent 互相反思（Multi-Agent Debate）：多个 Agent 各自独立完成任务，然后互相审查对方的结果和过程。这种机制利用了不同 Agent 的差异性，能够发现单 Agent 难以察觉的盲点。

分层反思（Hierarchical Reflection）：在多步任务中，不仅仅在任务结束时反思，还在每个关键步骤后进行局部反思。这种机制能够更早地发现问题，避免错误在后续步骤中级联放大。

工具增强反思（Tool-Augmented Reflection）：Agent 使用外部工具辅助反思过程。例如，用代码分析工具检查生成的代码，用搜索引擎验证信息的准确性。这种机制将反思从纯语言推理扩展到工具辅助的实证验证。

### Reflection 的代价

Reflection 并非没有代价。每轮反思都需要额外的 LLM 调用，增加了 token 消耗和执行时间。在允许3次尝试的场景下，带反思的 Agent 可能消耗无反思 Agent 3到5倍的 token。

此外，反思并非总是有益的。在某些情况下，反思文本可能引入噪音，导致 Agent 在后续尝试中偏离正确方向。这种现象在任务本身简单但反思过于复杂时尤为明显——Agent 把简单问题想复杂了。

因此，在实际系统设计中，需要为 Reflection 机制设置触发条件和深度限制。不是每次失败都需要深度反思，简单失败可以直接重试。反思的深度也应与任务复杂度匹配——简单任务做浅层反思即可，复杂任务才需要深度反思。

## 6.5 LATS：树搜索式 Agent 决策

LATS (Language Agent Tree Search, 语言Agent树搜索) 是将蒙特卡洛树搜索（MCTS）思想引入 Agent 决策的框架。传统的 Agent 决策通常是线性的——按顺序执行步骤，而 LATS 将决策过程建模为一棵搜索树，通过系统地探索多条路径来找到最优解决方案。这种将搜索算法与 LLM 推理结合的方式，代表了 Agent 决策研究的前沿方向。

### LATS 的核心思想

LATS 的核心思想来源于 MCTS (Monte Carlo Tree Search, 蒙特卡洛树搜索)。MCTS 因 AlphaGo 而广为人知，它通过选择、扩展、模拟、回溯四个阶段在巨大的搜索空间中寻找最优落子。LATS 将这个框架迁移到 Agent 场景：每个节点代表一个状态，每条边代表一个动作，通过 LLM 的推理能力替代 MCTS 中的模拟阶段。

在传统 Agent 中，决策是贪心的——每一步选择当前看起来最好的动作。这种方式可能在短期最优但长期次优的路径上浪费资源。LATS 通过同时维护多条候选路径，能够在更大的搜索空间中找到全局更优的解决方案。

### LATS 的搜索流程

LATS 的搜索流程包含以下阶段：

```
┌─────────────────────────────────────────────────────────┐
│                    LATS 搜索流程                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   1. Selection (选择)                                   │
│      │ 从根节点开始，根据 UCB 公式选择子节点              │
│      │ 直到到达一个未完全展开的节点                       │
│      ▼                                                   │
│   2. Expansion (扩展)                                   │
│      │ 用 LLM 生成多个候选动作                           │
│      │ 为每个动作创建新的子节点                           │
│      ▼                                                   │
│   3. Simulation (模拟)                                  │
│      │ 用 LLM 评估新节点的价值                           │
│      │ 替代 MCTS 中的随机 rollout                        │
│      │ 可以进行多步前瞻模拟                               │
│      ▼                                                   │
│   4. Backpropagation (回溯)                             │
│      │ 将评估值沿路径回传到根节点                         │
│      │ 更新各节点的访问次数和价值估计                     │
│      ▼                                                   │
│   5. 重复 1-4 直到预算耗尽或找到解决方案                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### UCB 选择策略

LATS 在选择阶段使用 UCB (Upper Confidence Bound, 上置信界) 公式来平衡探索与利用：

```
UCB(node) = Q(node)/N(node) + c * sqrt(ln(N(parent))/N(node))

其中：
Q(node) = 累计价值
N(node) = 访问次数
c = 探索参数（通常取 sqrt(2)）
```

这个公式的第一项 Q/N 是节点的平均价值，代表利用——选择已知的高价值节点。第二项 c * sqrt(ln(N(parent))/N(node)) 是探索项——访问次数少的节点获得更高的探索奖励。参数 c 控制探索与利用的平衡强度。

### LATS 与其他方法的对比

| 方法 | 决策方式 | 搜索空间 | 计算成本 | 适用场景 |
|------|---------|---------|---------|---------|
| ReAct | 线性贪心 | 单条路径 | 低 | 简单任务 |
| ToT | 树形搜索 | 有限分支 | 中 | 中等复杂度 |
| LATS | MCTS式搜索 | 大规模树 | 高 | 复杂推理任务 |

ToT (Tree of Thoughts, 思维树) 是 LATS 的前身，同样采用树搜索但缺少 MCTS 的系统性。LATS 相比 ToT 的核心优势在于引入了 UCB 选择策略和价值回溯机制，使得搜索资源的分配更加合理。

### 代码示例：LATS 的核心循环

```python
import math

class LATSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children: list[LATSNode] = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions: list[str] = []

    def ucb(self, c=1.414) -> float:
        if self.visits == 0:
            return float('inf')
        exploit = self.value / self.visits
        explore = c * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploit + explore

    def best_child(self) -> 'LATSNode':
        return max(self.children, key=lambda c: c.ucb())

async def lats_search(root_state, max_iterations=50):
    root = LATSNode(root_state)
    root.untried_actions = await generate_actions(root_state)

    for _ in range(max_iterations):
        # Selection
        node = root
        while node.children and not node.untried_actions:
            node = node.best_child()

        # Expansion
        if node.untried_actions:
            action = node.untried_actions.pop(0)
            new_state = await execute_action(node.state, action)
            child = LATSNode(new_state, parent=node)
            node.children.append(child)
            child.untried_actions = await generate_actions(new_state)
            node = child

        # Simulation (LLM evaluation)
        value = await llm_evaluate(node.state)

        # Backpropagation
        while node is not None:
            node.visits += 1
            node.value += value
            node = node.parent

        # Check terminal
        if is_goal(node.state):
            return extract_path(node)

    return extract_path(root.best_child())
```

### LATS 的局限性

LATS 的主要局限在于计算成本。每次搜索迭代都需要多次 LLM 调用——生成动作、评估状态、选择路径。50 次迭代可能产生数百次 LLM 调用，这在延迟和成本敏感的场景中是不可接受的。

此外，LATS 的效果高度依赖状态评估的准确性。如果 LLM 对中间状态的评估不够准确，UCB 公式中的 Q 值就不可靠，搜索方向可能偏离最优。这是一个根本性的挑战——MCTS 在围棋中有明确的胜负信号，而 Agent 任务中"好状态"的判断往往是主观的。

LATS 的实际应用建议集中在高价值、低频率的复杂决策场景。例如，在代码调试中，LATS 可以系统地探索多种修复策略；在数学推理中，LATS 可以搜索不同的证明路径。对于高频的简单任务，ReAct 或 Plan-and-Execute 仍然是更经济的选择。

## 6.6 探索与利用的平衡策略

探索（Exploration）与利用（Exploitation）的平衡是强化学习中的经典问题，在 Agent 决策中同样至关重要。Agent 在执行任务时面临着两种选择：利用已知的有效策略快速完成任务，或者探索新的可能策略以发现更优的解决方案。如何在两者之间取得平衡，直接影响 Agent 的效率和适应性。

### 问题的本质

设想一个信息检索 Agent，它已经知道某个搜索引擎能给出不错的搜索结果（利用），但还有一个新搜索引擎尚未尝试，可能效果更好也可能更差（探索）。如果 Agent 总是利用，它会错过更优的工具；如果 Agent 总是探索，它会在不确定的选项上浪费大量资源。

这个困境在 Agent 的多个层面都存在。工具选择层面：使用已知的好工具还是尝试新工具。策略选择层面：沿用有效的策略还是探索替代方案。路径选择层面：走已知的最短路径还是探索可能有更优解的路径。

### 经典平衡策略

强化学习领域发展了多种平衡策略，它们可以被迁移到 Agent 场景中：

Epsilon-Greedy（epsilon-贪心策略）：以 1-epsilon 的概率选择当前最优选项，以 epsilon 的概率随机探索。这是最简单的策略，优点是实现容易，缺点是探索是完全随机的，效率低。

Softmax 策略（Boltzmann 探索）：根据每个选项的价值分配选择概率，价值越高被选中的概率越大。相比 Epsilon-Greedy，探索更有针对性——价值高的选项即使不是最优也有更大概率被探索。

UCB (Upper Confidence Bound, 上置信界)：优先选择"被探索不足的高价值选项"。通过置信区间量化每个选项的不确定性，自动在确定的高价值选项和潜在的高价值选项之间平衡。LATS 中使用的就是这种策略。

Thompson Sampling（汤普森采样）：为每个选项维护一个价值分布，每次从中采样并选择采样值最高的选项。这种策略在理论上具有最优的后悔界（regret bound）。

### Agent 场景下的特殊考量

与标准强化学习不同，Agent 场景下的探索-利用问题有其特殊性。

首先，Agent 的动作空间通常是离散且语义化的——不是上下左右的移动，而是"搜索"、"计算"、"调用API"等具有明确语义的动作。这使得探索不能完全随机，需要有语义引导。

其次，Agent 的单次任务通常没有足够多的步骤来积累统计意义上的价值估计。强化学习中的 UCB 和 Thompson Sampling 都需要多次访问才能收敛，但 Agent 可能在一个任务中只执行几十步。

第三，LLM 本身具有先验知识。LLM 在训练过程中已经见过大量的工具使用和策略选择案例，这个先验可以用来初始化价值估计，加速收敛。

### 实用策略：LLM 引导的探索

考虑到上述特殊性，一种实用的策略是 LLM 引导的探索。不依赖纯统计的价值估计，而是让 LLM 根据当前状态和任务目标推荐探索方向。

具体实现方式是为 LLM 提供当前状态和历史执行信息，让它生成多个候选动作及其预期价值。然后根据这些预期价值进行概率化选择——高价值动作被选中的概率高，低价值动作仍有一定概率被选中。

```python
async def llm_guided_action_selection(
    state: State, history: list[Action], 
    exploration_rate: float = 0.2
) -> Action:
    candidates = await llm.generate_candidates(
        state, history, n=5
    )
    # LLM 评估每个候选动作的价值
    scored = await llm.score_candidates(candidates, state)
    
    if random.random() < exploration_rate:
        # 探索：从低价值候选中随机选择
        return random.choice(scored[1:])
    else:
        # 利用：选择最高价值候选
        return scored[0]
```

### 元探索策略

更高级的策略是元探索——Agent 不仅仅是随机尝试新选项，而是系统性地设计"实验"来评估新选项的价值。例如，当 Agent 想评估一个新搜索引擎的质量时，它可以设计一组已知答案的查询，用新搜索引擎处理这些查询，根据结果准确性来评估。

元探索的关键在于降低探索成本。通过精心设计的实验，Agent 可以用最少的尝试获得最准确的价值估计。这要求 Agent 具备实验设计能力——这本身就是 LLM 擅长的任务。

## 6.7 Agent 终止条件与循环检测

Agent 的执行不是无限进行的。确定何时停止与确定如何行动同样重要——过早终止会导致任务未完成，过晚终止则浪费资源甚至陷入无限循环。终止条件和循环检测机制是 Agent 系统中容易被忽视但至关重要的组件。

### 终止条件的类型

Agent 的终止条件可以分为四类：

目标达成终止：Agent 完成了预定目标，正常退出。这是最理想的终止方式。判断标准通常是目标验证函数返回 True。

资源耗尽终止：Agent 的 token 预算、时间限制或步骤数限制用尽，被迫退出。这是防御性终止，防止 Agent 无限制运行。

错误终止：Agent 遇到不可恢复的错误，无法继续执行。例如关键工具不可用、数据源无法访问。

用户中止：用户主动中断 Agent 的执行。这在交互式场景中常见，通常意味着当前方向不符合用户预期。

### 终止条件的实现

```python
class TerminationChecker:
    def __init__(self, max_steps=20, max_tokens=10000, 
                 max_time=300):
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.max_time = max_time
        self.start_time = time.time()
        self.steps = 0
        self.tokens = 0

    def should_terminate(self, result=None) -> tuple[bool, str]:
        if result and result.is_goal_achieved:
            return True, "goal_achieved"
        self.steps += 1
        self.tokens += result.tokens_used if result else 0
        if self.steps >= self.max_steps:
            return True, "max_steps"
        if self.tokens >= self.max_tokens:
            return True, "max_tokens"
        if time.time() - self.start_time > self.max_time:
            return True, "timeout"
        return False, ""
```

### 循环检测

Agent 在执行复杂任务时容易陷入循环——反复执行相同的动作或在一组状态间来回切换。循环检测机制的目的是尽早识别这种行为并打破循环。

最简单的循环检测是基于历史记录的重复检测。Agent 维护一个已访问状态的集合，每次执行动作后检查新状态是否已经在集合中。如果发现重复，触发循环处理逻辑。

更复杂的检测方法基于模式识别。有些循环不是简单的状态重复，而是更长周期的模式——比如A->B->C->A->B->C。这需要检测固定周期的重复序列。

```python
class LoopDetector:
    def __init__(self, window_size=6, similarity_threshold=0.85):
        self.history: list[str] = []
        self.window_size = window_size
        self.threshold = similarity_threshold

    def check(self, state_hash: str) -> bool:
        self.history.append(state_hash)
        if len(self.history) < self.window_size:
            return False
        # 检查最近的N步是否与之前的N步重复
        recent = self.history[-self.window_size//2:]
        previous = self.history[-self.window_size:-self.window_size//2]
        similarity = self._similarity(recent, previous)
        return similarity > self.threshold

    def _similarity(self, a: list, b: list) -> float:
        matches = sum(1 for x, y in zip(a, b) if x == y)
        return matches / len(a) if a else 0.0

    def reset(self):
        self.history.clear()
```

### 循环打破策略

检测到循环只是第一步，还需要有效的打破策略。常见的策略包括：

强制方向改变：要求 Agent 使用与之前不同的工具或策略。可以在 Prompt 中显式注入"你正在重复之前的操作，请尝试不同的方法"的提示。

状态回溯：将 Agent 回退到循环开始前的状态，然后禁止导致循环的动作。

反思触发：利用前面讨论的 Reflection 机制，让 Agent 分析为什么陷入了循环，并据此调整策略。

计划重置：放弃当前计划，基于循环检测的信息重新规划。这是最激进的策略，适用于循环根源于计划本身的场景。

### 终止决策的复杂性

在有些场景中，"重复"并不意味着循环。Agent 可能需要多次调用同一工具处理不同的数据——比如批量查询。因此，循环检测不能仅仅基于动作的重复性，还需要考虑动作的参数和上下文。

一个更精确的检测维度是状态空间。如果动作虽然重复但状态在变化（每次查询不同的关键词），则不是循环。只有动作和状态同时重复时，才应判定为循环。

终止决策还涉及一个深层问题：如何区分"正在艰难推进"和"陷入了死循环"？这两者在早期可能看起来完全一样——Agent 反复尝试但目标未达成。一个启发式的方法是观察中间结果的变化：如果中间结果在变化（即使目标未达成），说明 Agent 在取得进展；如果中间结果也停止变化，则更可能是循环。

## 6.8 长时任务的处理架构

大多数 Agent 演示集中在几分钟内可以完成的任务，但真实世界的任务可能需要数小时甚至数天。长时任务（Long-Horizon Task）的处理是 Agent 技术走向实用化的关键挑战之一。这类任务的复杂度不在于单步推理的难度，而在于跨时间的上下文管理、错误恢复和进度追踪。

### 长时任务的核心挑战

长时任务面临三个核心挑战：

上下文窗口限制。即使是支持 200K token 的模型，在执行数百步的长时任务时也会触及上下文窗口的边界。Agent 需要在有限的上下文中保留关键信息，丢弃冗余信息。

错误累积效应。在长时任务中，早期的微小错误可能在后续步骤中级联放大。一个数据采集错误可能导致整个分析链路失效。短时任务中的错误通常是局部的，长时任务中的错误是全局的。

状态管理复杂度。长时任务的执行过程中会产生大量的中间状态、中间结果和决策记录。如何组织和管理这些状态信息，使得 Agent 能够在任何时刻恢复执行，是一个工程难题。

### 分层架构

处理长时任务的主流方法是分层架构。将 Agent 组织为多个层级，每层负责不同时间尺度的决策：

```
┌─────────────────────────────────────────────┐
│          战略层 (Strategic Layer)             │
│    负责目标分解、资源分配、全局策略             │
│    时间尺度：小时~天                          │
├─────────────────────────────────────────────┤
│          战术层 (Tactical Layer)              │
│    负责子任务规划、工具选择、中间结果评估        │
│    时间尺度：分钟~小时                         │
├─────────────────────────────────────────────┤
│          执行层 (Execution Layer)             │
│    负责具体工具调用、参数构造、结果解析          │
│    时间尺度：秒~分钟                          │
└─────────────────────────────────────────────┘
```

战略层将长时目标分解为可独立执行的子任务，每个子任务的时间跨度在分钟到小时级别。战术层接收子任务后进行局部规划，选择合适的工具和策略。执行层负责最底层的具体操作。

这种分层架构的关键优势在于上下文隔离。每一层只需要维护自己时间尺度内的上下文信息，不需要了解其他层的细节。战略层不需要知道执行层调用了哪些 API，执行层不需要知道战略层的全局规划。这大大降低了每层的上下文压力。

### 检查点与恢复机制

长时任务的执行跨越较长时间跨度，期间可能面临各种中断——进程崩溃、网络断开、资源限制。检查点（Checkpoint）机制允许 Agent 在中断后从最近的检查点恢复，而不是从头开始。

检查点机制需要保存三类信息：当前执行计划、已完成步骤的结果、Agent 的内部状态（包括反思历史和动态生成的上下文）。

```python
import json
from pathlib import Path

class CheckpointManager:
    def __init__(self, task_id: str, base_dir: str = ".checkpoints"):
        self.dir = Path(base_dir) / task_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: AgentState):
        path = self.dir / f"checkpoint_{state.step}.json"
        path.write_text(json.dumps(state.to_dict(), 
                                   ensure_ascii=False, indent=2))

    def load_latest(self) -> AgentState | None:
        checkpoints = sorted(self.dir.glob("checkpoint_*.json"))
        if not checkpoints:
            return None
        data = json.loads(checkpoints[-1].read_text())
        return AgentState.from_dict(data)

    def should_checkpoint(self, step: int) -> bool:
        return step % 10 == 0  # 每10步保存一次
```

### 上下文压缩与记忆管理

在长时任务中，上下文窗口的管理至关重要。Agent 不能无限制地将所有中间结果保留在上下文中——这会很快耗尽 token 预算。

一种有效的策略是渐进式上下文压缩。Agent 定期将上下文中的详细信息压缩为摘要。早期步骤的详细信息被替换为简短摘要，近期步骤的详细信息保留。这种策略确保了 Agent 始终拥有全局视野（通过摘要），同时有足够的细节处理当前任务（通过近期信息）。

```python
async def compress_context(
    full_history: list[Step], 
    keep_recent: int = 5
) -> str:
    old_steps = full_history[:-keep_recent]
    recent_steps = full_history[-keep_recent:]
    
    # 将早期步骤压缩为摘要
    summary = await llm.summarize(
        steps=old_steps,
        instruction="提取关键决策、结果和未解决问题"
    )
    
    # 构建压缩后的上下文
    context = f"历史摘要:\n{summary}\n\n"
    context += "近期步骤:\n"
    for step in recent_steps:
        context += f"Step {step.id}: {step.summary}\n"
    return context
```

### 外部记忆系统

对于超长时任务（跨越数天的任务），即使上下文压缩也不够。Agent 需要依赖外部记忆系统来存储和检索信息。

外部记忆系统通常采用向量数据库作为后端，将中间结果、决策记录和关键信息编码为向量存储。Agent 在需要时通过语义检索提取相关信息。这种方式将上下文窗口从有限的 token 空间扩展到近乎无限的外部存储空间。

外部记忆的设计需要考虑读写效率。写入时需要将信息编码为向量并存储，读取时需要进行相似度检索。这两个操作的延迟会直接影响 Agent 的执行效率。在实际系统中，通常会维护一个热缓存（最近使用的记忆）和一个冷存储（历史记忆），通过两级缓存机制平衡访问速度和存储容量。

### 长时任务的进度追踪

在长时任务中，用户通常需要了解 Agent 的执行进度。一个良好的进度追踪系统不仅展示完成百分比，更应展示当前执行的子任务、遇到的障碍和预计完成时间。

进度追踪的技术实现可以采用任务树展示。将原始任务拆解的子任务组织为树形结构，标注每个子任务的状态（已完成、进行中、待执行、已阻塞）。用户可以通过任务树直观了解整体进度，也能快速定位问题所在。

进度追踪对于 Agent 自身也有价值。通过回顾已完成和未完成的子任务，Agent 可以更好地进行动态规划调整。如果发现已完成任务消耗的资源远超预期，Agent 可以在后续任务中采用更保守的策略。

## 本章知识点总结

| 知识点 | 核心概念 | 关键技术 | 适用场景 |
|--------|---------|---------|---------|
| 任务拆解 | 将复杂目标分解为可执行原子操作 | 线性/树形/图拆解，自适应深度拆解 | 所有复杂任务的起始步骤 |
| Plan-and-Execute | 先规划后执行的静态策略 | 一次性规划，逐步执行 | 流程确定型任务 |
| ReAct | 推理与行动交替的动态策略 | Thought-Action-Observation循环 | 探索型任务 |
| 融合模式 | Plan + Replan 结合两种优势 | 执行偏差检测触发重规划 | 通用复杂场景 |
| 动态规划调整 | 根据执行结果实时更新计划 | 增量/回溯/全局重规划 | 高不确定性环境 |
| Reflection | 从失败中提取经验的自省能力 | 执行轨迹分析，反思文本存储 | 允许多次尝试的任务 |
| LATS | MCTS式树搜索决策 | UCB选择，LLM模拟，价值回溯 | 高价值复杂推理 |
| 探索与利用平衡 | 在已知优策略和未知新策略间取舍 | Epsilon-Greedy，UCB，Thompson采样 | 工具选择，策略选择 |
| 终止条件 | 控制Agent何时停止执行 | 目标达成/资源耗尽/错误/用户中止 | 所有Agent系统 |
| 循环检测 | 识别并打破执行循环 | 状态哈希重复检测，模式识别 | 长步数执行场景 |
| 长时任务处理 | 跨越数小时到数天的任务架构 | 分层架构，检查点，上下文压缩，外部记忆 | 复杂工程任务 |
| 外部记忆 | 突破上下文窗口限制 | 向量数据库，语义检索，两级缓存 | 超长时任务 |

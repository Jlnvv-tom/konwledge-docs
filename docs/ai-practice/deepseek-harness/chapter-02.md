# 第2章：Cordis——驱动 dsh 的插件引擎

> 系列：DeepSeek Harness 源码实战 ｜ 进度 2/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

插件框架不是给前端用的吗？dsh 整个 Agent 运行时都跑在插件引擎上。

如果你做过前端开发，可能用过 webpack 的 plugin 系统或者 VS Code 的扩展机制。但 dsh 的插件引擎走得更远——它把运行时的每一个部件都做成插件，包括 agent 循环本身。这个引擎叫 Cordis。

我是怕浪猫，这一章我们拆开 Cordis 的内核，看它到底用什么机制支撑起了 dsh 的「一切皆插件」。

## 2.1 Cordis 是什么：插件、上下文、服务注入

Cordis 是 dsh 底层以 vendor（供应商内嵌）方式引入的插件框架。它的设计思路来自一篇论文：《A Programming Paradigm for Spatiotemporal Composability》（一种面向时空可组合性的编程范式），论文地址在 https://github.com/cordiverse/paper 。

Cordis 的核心是五个概念，来自 dsh 仓库 `docs/cordis-primer.zh.md` 的原文：

1. **插件是实现 Service 的对象**。可以是一个带 `inject` 和 `apply(ctx)` 字段的函数，也可以是一个 `Service` 子类。它的生命周期由 Cordis 挂载到当前上下文中管理。
2. **上下文（Context）是服务的容器**。一个服务占据一个稳定的 `ctx.<key>`，比如 `ctx.tools`、`ctx.llm`、`ctx.sessions`。其他插件通过 key 查找服务，而不是 import 具体实现。
3. **通过 inject 声明服务依赖**。插件声明所需的服务后，会等待这些服务就绪才启动。加载顺序通过服务依赖表达，而非手动编排启动序列。
4. **类型化事件用于通信**。服务通过 TypeScript 声明合并注册事件名，然后以四种模式分发（下一节详述）。
5. **注册是可逆的副作用**。提示词片段、工具 schema、适配器、监听器通过 `ctx.effect()` 或 `ctx.on()` 安装，reload（热重载）和 teardown（卸载）时会自动撤销。

这五个概念的关系可以这样理解：

```
┌─────────────────────────────────────────────────┐
│                 Context（上下文）                 │
│                                                  │
│  ctx.tools ◀── ToolRuntime 服务                  │
│  ctx.llm   ◀── LlmRuntime 服务                   │
│  ctx.sessions ◀── SessionStore 服务               │
│                                                  │
│  事件总线: emit / waterfall / parallel / serial  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Plugin A  │  │ Plugin B  │  │ Plugin C  │      │
│  │ inject:   │  │ inject:   │  │ inject:   │      │
│  │  tools    │  │  llm      │  │  sessions │      │
│  │           │  │  tools    │  │  llm      │      │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                  │
│  effect()/on() 注册的副作用                      │
│  → 卸载时自动撤销                                │
└─────────────────────────────────────────────────┘
```

关键设计决策是「通过 key 查找而非 import 实现」。这意味着 Plugin A 不需要知道 `ctx.tools` 的具体实现类是谁，它只需要知道有这么一个服务在 ctx 上。实现可以随时被替换——这正是 dsh 能力 Seam 架构的基础。

> 金句：依赖注入的本质不是「注入」，而是「不关心实现是谁」。

## 2.2 事件分发四模式：emit / waterfall / parallel / serial

Cordis 的事件系统有四种分发模式，每种模式的语义不同。这是理解 dsh 源码的关键——你会在 agent-loop、tools 流水线、llm 流式输出中反复遇到这四个词。

| 模式 | 是否 await | 分发顺序 | 是否有返回值 | 典型用途 |
|---|---|---|---|---|
| emit | 否 | 监听器按注册顺序观察 | 否 | 状态通知（inbox 插入、agent 状态变更） |
| waterfall | 否 | 监听器按注册顺序，必须调 next() 委托 | 是 | 中间件流水线（pre-execute、request） |
| parallel | 是 | 所有监听器并行观察 | 否 | 多个独立观察者同时响应（session/flush） |
| serial | 是 | 监听器按注册顺序观察 | 是 | 需要顺序执行且有返回值的决策（turn-stopping） |

### emit：观察者模式

`emit` 是最简单的模式。分发给所有监听器，不等待，无返回值。用于「发生了某事，通知大家」的场景。

在 dsh 的 agent-loop 中，inbox 的三个事件就是 emit：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
this.inbox = new Inbox(session, {
  inserted: (message) => { this.dispatch.emit('agent/inbox/inserted', { message }) },
  discarded: (message) => { this.dispatch.emit('agent/inbox/discarded', { message }) },
  claimed: (message, turn) => { this.dispatch.emit('agent/inbox/claimed', { message, turn }) },
})
```

当一条消息插入 inbox 时，`agent/inbox/inserted` 事件被 emit。所有监听这个事件的插件都会收到通知，但 emit 不会等待它们处理完毕，也不关心返回值。这是一个纯通知机制。

### waterfall：中间件管道

`waterfall`（瀑布式事件）是最重要的模式。它的语义是中间件管道：监听器接收 `(...args, next)`，调用 `next()` 会执行下游监听器，下游的返回值通过 `next()` 返回当前层，当前层可以包装后继续向外返回。不调用 `next()` 就会短路。

来看 dsh 中最典型的 waterfall 用法——`agent/pre-step` 事件：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
const decision = await this.dispatch.waterfall(
  'agent/pre-step', { messages: claimed, ...position, signal },
  (): Promise<PreStepDecision> => Promise.resolve<PreStepDecision>({
    kind: 'enter',
    messages: context === undefined ? claimed : [...claimed, context],
  }),
)
```

这段代码做了什么：

1. 分发 `agent/pre-step` 事件，载荷是当前领取的消息和位置信息
2. 默认行为（最底层的 next()）是返回 `{ kind: 'enter', messages: [...] }`，表示「进入步骤」
3. 监听器可以修改这个决策——比如把 messages 改写、添加上下文、或者直接拒绝（返回 `{ kind: 'reject' }` 短路）

另一个 waterfall 例子是 `agent/request`，用来决定模型请求的配置：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
const proposedConfig = await this.dispatch.waterfall(
  'agent/request', { turn, step, signal },
  () => Promise.resolve(seedConfig),
)
if (!proposedConfig.provider || !proposedConfig.model) {
  throw new Error(`agent "${this.id}" has no provider/model: set AgentOptions.provider and AgentOptions.model or supply both via the agent/request waterfall`)
}
```

默认返回 seedConfig（种子配置），但中间件可以替换它。如果最终结果里没有 provider 或 model，就抛错。注意错误信息提到了 `agent/request waterfall`——说明官方文档把 waterfall 当作一种公开的扩展接口来宣传。

> 金句：waterfall 不是简单的事件，它是带返回值的中间件管道。每一层都可以修改决策，也可以短路。

### parallel：并行扇出

`parallel` 模式同时分发给所有监听器，await 全部完成。没有返回值。适用于多个独立观察者需要同时响应的场景。

在 dsh 中，parallel 用于那些「多个插件都需要知道某事发生了，但它们之间没有顺序依赖」的场景。比如 session 事件广播后，遥测插件、UI 投影插件、持久化插件可以并行各自处理。

### serial：顺序执行带返回值

`serial` 模式按注册顺序依次执行监听器，每个监听器可以看到前一个的返回值，最终返回最后一个结果。

dsh 中最关键的 serial 事件是 `agent/turn-stopping`：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
if (turnEnds && this.inbox.nextStep.length === 0) {
  await this.dispatch.serial('agent/turn-stopping', { turn, signal })
  signal.throwIfAborted()
}
```

当一个 turn（轮次）即将结束、且 next-step inbox 里没有新消息时，分发 `agent/turn-stopping` 事件。serial 意味着监听器按顺序执行，每个监听器可以决定是否让轮次继续。这与 waterfall 的区别在于：serial 没有 `next()` 函数，监听器不能短路管道，它们按顺序各自执行并返回值。

### 四模式选型指南

什么时候用哪种模式？这是一个实践速查：

| 场景 | 选择 | 理由 |
|---|---|---|
| 纯通知（inbox 变更、状态切换） | emit | 不需要返回值，不阻塞 |
| 拦截/修改决策（pre-step、request） | waterfall | 中间件需要包装和短路能力 |
| 多个独立观察者并行响应 | parallel | 无顺序依赖，可并行 |
| 顺序决策但有返回值 | serial | 需要顺序，但不需要短路 |

## 2.3 ctx 服务注册与依赖注入

Cordis 的服务注入机制是理解 dsh 架构的钥匙。

在 dsh 里，每个核心包在 Cordis 上下文上占据一个稳定的 key。这个 key 是服务契约的「地址」，不是实现的名字。来看核心包的 ctx 键分配：

| 包 | ctx 键 | 服务内容 |
|---|---|---|
| core/session | ctx.sessions | 会话日志的创建、恢复、fork |
| core/system-prompt | ctx.systemPrompt | 提示词片段组装 |
| core/tools | ctx.tools | 工具注册表和执行流水线 |
| core/agent | ctx.agents | Agent 注册表和 agent/* 事件 |
| core/agent-loop | ctx.agentLoop | 默认驱动器 |
| llm/llm | ctx.llm | LLM 适配器 seam 和消息词汇表 |

一个插件需要用某个服务时，通过 `inject` 声明依赖。Cordis 会等待被依赖的服务就绪后才启动这个插件。这意味着你不需要手动编排启动顺序——依赖关系就是启动顺序。

来看 dsh 的工具流水线事件声明，它在 `ctx.tools` 的服务接口上定义了三个 waterfall 事件：

```typescript
// packages/core/tools/src/index.ts（节选）
interface Events {
  /**
   * Allow, deny, or ask before dispatch. `next()` delegates to allow.
   * @mode waterfall
   */
  'tools/pre-execute'(
    this: Scoped<ToolRuntime>,
    exec: ToolExecution,
    next: () => Promise<PreToolDecision>
  ): Promise<PreToolDecision>

  /**
   * Around-dispatch waterfall for timeout, retry, or metrics.
   * @mode waterfall
   */
  'tools/execute'(
    this: Scoped<ToolRuntime>,
    exec: ToolDispatchExecution,
    next: () => Promise<ToolExecutionResult>
  ): Promise<ToolExecutionResult>

  /**
   * Accept, replace, enrich, or block a normalized dispatch result.
   * @mode waterfall
   */
  'tools/post-execute'(
    this: Scoped<ToolRuntime>,
    exec: ToolExecution,
    result: Readonly<ToolExecutionResult>,
    next: () => Promise<PostToolDecision>
  ): Promise<PostToolDecision>
}
```

三个事件都是 waterfall 模式（用 `@mode` 标签标注），这意味着每个事件都是一条中间件管道。`this: Scoped<ToolRuntime>` 表示这些事件在 ToolRuntime 的作用域内分发，agent 级别的监听器只会收到该 agent 的调用。

注意三个事件的职责分离：

1. `tools/pre-execute`：决定「这个调用能不能执行」
2. `tools/execute`：包裹执行过程，用于超时、重试、指标
3. `tools/post-execute`：决定「结果怎么处理」

这种分离让策略插件可以精确插入到流水线的正确位置，而不影响其他位置的行为。权限插件只需要监听 pre-execute，重试插件只需要监听 execute，审计插件只需要监听 post-execute。

> 金句：好的接口设计不是把所有能力塞进一个函数，而是让每个关注点都有自己的落脚点。

## 2.4 可逆副作用与生命周期

Cordis 的第五个核心概念是「注册是可逆的副作用」。这句话的含义比看起来更深。

在 dsh 里，一个插件启动时会做很多注册操作：注册工具、注册提示词片段、注册事件监听器、注册服务提供方。这些操作都是「副作用」——它们改变了 ctx 的状态。关键在于，当插件被卸载时，这些副作用必须全部撤销。

Cordis 提供了两个主要的注册机制：

### ctx.effect()

`ctx.effect()` 注册一个副作用，返回一个 disposer（清理函数）。当插件卸载时，Cordis 自动调用 disposer。如果你把多个相关操作放在同一个 effect 里，它们会按注册的逆序释放。

```typescript
// 伪代码示意
ctx.effect(() => {
  const dispose1 = ctx.tools.register(myTool)
  const dispose2 = ctx.on('some-event', handler)
  return () => {
    dispose2()
    dispose1()
  }
})
```

### ctx.on()

`ctx.on()` 注册事件监听器，返回一个取消注册的函数。它本身就是 `ctx.effect()` 的语法糖——卸载时自动取消注册。

```typescript
// 伪代码示意
const dispose = ctx.on('agent/pre-step', (event, next) => {
  // 处理逻辑
  return next()
})
// dispose() 手动取消，或等插件卸载时自动取消
```

### 为什么可逆很重要

可逆副作用的设计有两个直接好处：

**第一，热重载（reload）安全。** 当你修改一个插件的代码并重新加载时，旧插件的所有注册会被撤销，新插件的注册会生效。不会出现「旧的工具还注册着、新的也注册了」的冲突状态。

**第二，作用域隔离。** dsh 的 scope 机制允许给每个 agent 创建独立的作用域。一个 agent 注册的工具、监听器，在 agent 销毁时会自动清理。来看 agent-loop 中的 scope 创建：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
constructor(
  private loopCtx: Context,
  public readonly id: SessionId,
  public readonly options: AgentOptions,
  public readonly session: Session,
) {
  this.dispatch = agentEvents(loopCtx, this)
  this.inbox = new Inbox(session, { /* ... */ })
  const lastTurn = session.events.findLast(event => event.type === 'turn/start')?.data.turn ?? 0
  this.phase = { kind: 'idle', lastTurn }
  this.scope = createScope(loopCtx, this)
  this.ctx = this.scope.ctx.extend({ agent: this })
  this.runtimeContext = new RuntimeContextProjection(this.ctx, session)
}
```

注意 `this.scope = createScope(loopCtx, this)` 和 `this.ctx = this.scope.ctx.extend({ agent: this })` 这两行。每个 agent 创建自己的 scope（作用域），并在这个 scope 上 extend（扩展）出一个新的 ctx。在这个 ctx 上注册的所有副作用，都会在 agent 销毁时自动撤销。agent 之间不会互相干扰。

> 金句：可逆副作用让插件系统从「能装」变成「能拆」。装上去不难，能干净地拆下来才是工程。

## 2.5 Cordis 在 dsh 中的落地

前面讲了 Cordis 的概念，现在来看它们在 dsh 中的具体落地。

### Scoped 上下文

dsh 在 Cordis 的基础上做了一层封装：`@deepseek-ai/dsh-scope`。这个包提供了「按 agent 划分作用域的注册原语」。

每个 agent 实例都有自己的 scope，scope 上的 ctx 是父 ctx 的扩展。在 agent scope 上注册的工具和监听器，只对该 agent 生效。这就是为什么 dsh 可以同时运行多个 agent，每个 agent 有不同的工具集——它们的注册在各自的作用域里互不干扰。

### 插件树与 mount

dsh 启动时，Cordis 的 Loader 根据配置树挂载插件。每个配置条目对应一个插件节点。配置树的组装是通过 Profile / Bundle / Patch 三层叠加完成的（下一章详述）。

插件节点可以挂载子节点，形成树结构。父节点卸载时，所有子节点一起卸载。这种层次结构与 Cordis 的可逆副作用结合，保证了插件树任意子树的卸载都是干净的。

### agent-loop 中的事件落地

把前面讲的概念在 agent-loop 中汇总来看。一次完整的 turn 中，Cordis 事件是这样流动的：

```text
turn/start（durable session 事件）
  │
  ▼
agent/pre-step（waterfall）── 监听器可修改/拒绝消息
  │  next() 返回 PreStepDecision
  ▼
step/start（durable session 事件）
user/message（durable session 事件，每个进入的消息）
  │
  ▼
system-prompt/assemble（waterfall）── 组装提示词片段和工具 schema
  │
  ▼
agent/request（waterfall）── 监听器可修改请求配置
  │  next() 返回 LlmCallConfig
  ▼
llm/stream（waterfall）── 流式分片到达
  │  产生 assistant/chunk*（durable）→ assistant/message（durable）
  ▼
工具调用？── 是 ──▶ tool/call（durable）→ tools/pre-execute（waterfall）→ tools/execute（waterfall）→ tools/post-execute（waterfall）→ tool/result（durable）
  │
  ▼ 否
step/end（durable session 事件）
  │
  ▼
agent/turn-stopping（serial）── 监听器顺序执行，无 next()，终端检查点
  │
  ▼
turn/end（durable session 事件）
```

这条链里，`turn/*`、`step/*`、`user/message`、`assistant/*` 和 `tool/*` 是 durable session 事件（持久化到日志），其余是 live 扩展点。waterfall 事件（pre-step、request、llm/stream、pre-execute、execute、post-execute）是中间件管道，监听器必须调 `next()` 委托。serial 事件（turn-stopping）是顺序执行且没有 `next()`。emit 事件（inbox 三件套、status 变更）是纯通知。`session/flush` 是唯一的 parallel 事件，持久化和遥测并行响应。

### 实践规则

dsh 的文档给了几条实践规则，值得记住：

1. **将行为封装为插件**：工具流水线事件属于 `ctx.tools`，模型流式输出属于 `ctx.llm`，实时 agent 协调属于 `ctx.agents`。
2. **拦截和策略优先使用事件**：如果你想在工具执行前做权限检查，监听 `tools/pre-execute` 而不是改工具代码。
3. **直接能力调用优先使用服务方法**：如果你需要读文件，调用 `ctx.fs` 的方法而不是发事件。
4. **每个注册都要有对应的 disposer**：要么从 `ctx.effect()` 返回一个，要么用 Cordis 的辅助方法自动处理。

> 金句：Cordis 的实践规则只有四条，但每一条都是从踩坑里总结出来的。

## 本章小结

| 概念 | 说明 |
|---|---|
| 插件 | 实现 Service 的对象，生命周期由 Cordis 管理 |
| 上下文（Context） | 服务的容器，通过 ctx.<key> 查找服务 |
| inject 声明依赖 | 加载顺序由服务依赖决定，无需手动编排 |
| emit | 观察者模式，不 await，无返回值，用于通知 |
| waterfall | 中间件管道，必须调 next()，有返回值，用于拦截/修改决策 |
| parallel | 并行扇出，await 全部，无返回值 |
| serial | 顺序执行，有返回值，用于顺序决策 |
| ctx.effect() | 注册可逆副作用，返回 disposer |
| ctx.on() | 注册事件监听器，卸载时自动取消 |
| Scoped 上下文 | 按 agent 划分作用域，注册互不干扰 |
| 实践规则 | 拦截用事件，调用用方法，注册必配 disposer |

## 下章预告

我们已经知道 dsh 的所有功能都是 Cordis 插件，但这些插件是怎么被组装成一棵树的？配置从哪里来？谁决定加载哪些插件？

下一章，我们来拆 dsh 的装配系统——Profile / Bundle / Patch。你会发现，改一行配置就能换掉整个产品的形态。

> 我是怕浪猫，这篇帮你理解了 Cordis 的话，点个收藏。四模式里你觉得哪个最容易踩坑？评论区聊聊。
>
> 系列进度：2/8 ｜ 下一章：Profile / Bundle / Patch 装配系统

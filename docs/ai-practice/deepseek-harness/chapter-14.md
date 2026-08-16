# 第14章：子代理与工作流编排——agent 如何编排 agent

> 系列：DeepSeek Harness 源码实战 ｜ 进度 14/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

一个 agent 能写代码、能跑命令。但如果任务太大——「重构这个模块」「同时修 10 个文件」——单个 agent 的上下文窗口会爆。解法是让 agent 编排 agent：父 agent 把子任务委派给子 agent，子 agent 独立完成后汇报结果。

dsh 用两个 Seam 实现这个能力：subagent（子代理）让 agent 委派工作，workflow（工作流）让 agent 运行编排脚本。两者都是可选能力，不属于 agent loop（智能体循环）主干。

我是怕浪猫，第 14 章。我们从 subagent 开始。

## 14.1 subagent Seam：与 bash 不同的多提供方

subagent 与其他能力 Seam 有一个关键区别。来自子系统文档（docs/subsystems/subagent.zh.md）：

> 与 bash 一样，它是一项可选能力。但它不同于其他能力 seam，因为同一上下文中可共存多个提供方实现，并按名称注册（ctx.subagents），而 bash 只允许一个执行器。

对比两种注册模式：

| 维度 | bash Seam | subagent Seam |
|---|---|---|
| 注册方式 | 单服务（ctx.shell） | 命名注册表（ctx.subagents） |
| Provider 数量 | 一个上下文一个，重复注册报错 | 可多个共存 |
| 注册表模式 | Cordis 标准 duplicate-service | 类似 LLM adapter 注册表 |
| 选择方式 | cordis.yml 选一个 | 按名称选择 |

这意味着你可以同时挂载 in-process（进程内）、ACP（Agent Client Protocol，代理客户端协议）、Codex、Claude Code 等多个 subagent provider，按名称选择。

六个 Provider 包（来自文档）：

| Provider 包 | 说明 | 典型用途 |
|---|---|---|
| dsh-subagent-spawn-in-process | 独立进程 spawn | 隔离执行 |
| dsh-subagent-fork-in-process | 进程内 fork | 共享内存快速派生 |
| dsh-subagent-acp | ACP 协议远程 | 跨进程互操作 |
| dsh-subagent-codex | OpenAI Codex 后端 | 用 Codex 做子 agent |
| dsh-subagent-claude-code | Claude Code 后端 | 用 Claude Code 做子 agent |
| dsh-subagent-dsh-sdk | dsh SDK 后端 | 外部驱动 |

三个面向模型的 Consumer（消费方）：

| Consumer 包 | 作用 | 作用域 |
|---|---|---|
| dsh-tool-subagent | 按提供方委派（主工具） | 全局 |
| dsh-tool-subagent-control | 全局控制工具 | 全局 |
| dsh-tool-subagent-report | report 返回通道 | child 作用域 |

## 14.2 能力声明与 fail-loud 原则

Provider 通过静态描述符公布其启动时能力。来自源码（packages/subagent/subagent/src/types.ts）：

```ts
interface SubagentCapabilities {
  readonly outputSchema: boolean    // 是否支持输出 schema
  readonly depthLimit: boolean      // 是否支持深度限制
  readonly toolFilter: boolean      // 是否支持工具过滤
  readonly persona: boolean         // 是否支持人设
}
```

服务在 `start` 之前针对指定 Provider 进行校验。如果请求依赖 Provider 不具备的能力，会被明确拒绝（`SubagentError('UNSUPPORTED_CAPABILITY')`），绝不会被接受后静默忽略。

文档原文：

> A request that needs a capability the chosen provider lacks is rejected with a typed error rather than accepted-then-ignored.

校验流程：

```
模型请求：启动子 agent，需要 outputSchema + depthLimit
  |
  v
检查 Provider 的 SubagentCapabilities
  |-- outputSchema: true, depthLimit: true -> 继续启动
  |-- outputSchema: true, depthLimit: false -> 抛 SubagentError('UNSUPPORTED_CAPABILITY')
  |-- outputSchema: false, depthLimit: true -> 抛 SubagentError('UNSUPPORTED_CAPABILITY')
```

> 金句：能力声明不是文档注释，是运行时契约。Provider 说不支持，服务就拒绝——不尝试、不降级、不静默吞掉。

## 14.3 单次启动请求

单次启动（one-shot）是 subagent 的基本操作模式。来自文档的请求定义：

```ts
interface SubagentStartRequest {
  readonly label?: string              // 显示标签
  readonly prompt: ContentBlock[]      // 子 agent 的用户消息
  readonly parent: Agent               // 父 agent（提供 cwd、谱系、深度）
  readonly outputSchema?: ObjectJsonSchema  // 输出 schema（需能力匹配）
  readonly maxDepth?: number           // 深度限制（需能力匹配）
  readonly toolFilter?: ToolRestriction  // 工具过滤（需能力匹配）
  readonly persona?: string            // 人设（需能力匹配）
  readonly signal?: AbortSignal        // 取消信号
}
```

每个可选字段对应一个能力 flag，文档说明了各字段的行为：

`toolFilter`：进程内后端将其作为 scoped（作用域化）的 `tools.restrict()` 应用在子 agent 创建窗口——被命名的工具从子 agent 的 prompt 中消失且拒绝执行（双向可见性），unknown-name（未知名称）会 loud validate。

`persona`：进程内后端将其注册为 scoped `deployment:persona` section，shadowing（遮蔽）部署级 persona——与部署 persona 相同的模板语义（`{{...}}` 插值）。

`parent` 是必填字段。文档原文：

> In-process providers derive workspace, lineage, and delegation depth from its durable session state.

`signal` 是就绪前后唯一的取消通道。来自文档：

> signal is the canonical cancellation channel both before and after startup.

工具层构建请求后，服务在 `start` 之前解析分离的一次性描述符（`SubagentDescriptorData`），再将 `ResolvedSubagentStartRequest` 传给 Provider。

## 14.4 可继续子代理与 Activation

可继续（continuable）子代理是 subagent 的高级模式——一份持久化的子 agent 会话（Session），可跨轮次、跨进程恢复。

来自文档的定义：

> 可继续后台 subagent 是一份持久化子 agent 会话，至多关联一个进程内的 Activation（激活），即被重建的子 Agent 处于驻留状态的时段。

Activation 的三种状态：

| 状态 | 含义 | followup 行为 |
|---|---|---|
| running | Agent 有活跃轮次或正在唤醒 | 在同一 Activation 中入队 |
| waiting | 已停稳但拥有未完成 dispose 的子 Activation | 唤醒同一 Activation |
| settled | 完全停稳且所有子级已 dispose | dispose AgentHandle，移除 Activation |

无 Activation 时 `followup` 执行冷恢复——从持久化日志重建 Agent。

文档的生命周期图：

```
persisted Session
  -> optional live Activation
       -> one retained AgentHandle
       -> Agent inbox as the only turn FIFO
       -> zero or more owned child Activations
```

关键设计：Activation 不是请求、结果、取消或 Task。它可以执行多个 FIFO（先进先出）轮次，并在其创建的后代仍在运行期间保持驻留。继续执行管理器负责 activation 准入、直接父级鉴权、实时所有权图、冷恢复与子级优先释放。

`SubagentRuntime.startContinuable()` 的流程：

```
1. 预留稳定的子 agent id
2. 对版本化的 subagent/descriptor payload 建立快照
3. 向指定 Provider 索取 ContinuableCreateSpec
4. 通过私有 activation-owner 作用域创建子 Agent
5. 建立可继续父级的所有权
6. 提交初始提示词
7. inbox 准入产出 messageId 时 resolve
```

准入之前的任何失败都会 reject 并 dispose 所有已创建的 handle，回滚 Activation 与父级所有权——不留半成品。

## 14.5 中断与所有权

`SubagentRuntime.interrupt(targetSessionId, authority)` 是唯一的公开停止操作。来自文档：

```ts
type SubagentInterruptAuthority =
  | { readonly kind: 'user'; readonly parentSessionId: SessionId }
  | { readonly kind: 'ancestor'; readonly agent: Agent }
```

两种鉴权方式：

- `user`：携带持久化的直接父级会话 id，人类客户端呈现
- `ancestor`：携带确切的在线 Agent 对象，其谱系链必须包含调用方

interrupt 的行为：

```
1. 同步完成鉴权
2. 对在线目标发出 Agent.cancel(cause, { keepInbox: true })
3. 不等待完全停稳即返回
```

`keepInbox: true` 意味着未领取的待处理 inbox 工作不受影响。已被领取进入中断轮次的工作不会重新入队——中断只影响当前轮次，不丢弃排队消息。

不存在的目标（未知、一次性或已结算）以及未绑定管理器的组合是被接受的 no-op（无操作）。错误地址或不在在线祖先链中的调用方以 `UNAUTHORIZED` 拒绝。

> 金句：subagent 的安全模型不是能力令牌，是所有权图。父级拥有子级，祖先可中断后代——权限沿谱系树流动，不沿网络流动。

## 14.6 生命周期事件

subagent 通过 emit 事件向外部观察者公布生命周期：

| 事件 | 载荷 | 作用 |
|---|---|---|
| subagent/start | SubagentRunInfo | 一次接受的 run 开始 |
| subagent/end | SubagentRunEndInfo | 一次 run 终结 |
| subagent/provider-added | Provider 名 | Provider 注册 |
| subagent/provider-removed | Provider 名 | Provider 注销 |

来自源码（packages/subagent/subagent/src/types.ts）：

```ts
export interface SubagentRunInfo {
  readonly runId: SubagentRunId   // 唯一身份
  readonly provider: string       // Provider 名称
  readonly id: SessionId          // 子 agent 的会话 id
  readonly local: boolean         // 是否有本地 agent 实例
}
```

两个事件通过 `runId` 配对。文档补充了一个细节：Provider 名可能在 start 时存在但在 end 时不存在——因为可继续子代理的冷恢复不依赖 Provider 持续注册。

## 14.7 workflow Seam：模型编写编排脚本

workflow 让 agent 运行由模型编写的 JavaScript 编排脚本，脚本可以启动 subagent。来自子系统文档（docs/subsystems/workflow.zh.md）：

> 工作流 seam 允许 agent 运行由模型编写、会启动 subagent 的编排脚本。

workflow 与 subagent 的关系：

```
模型调用 workflow 工具
  |
  v
ctx.workflowEngine.start(script, meta, args)
  |
  v
引擎在 worker thread 中执行脚本
  |
  v
脚本调用 agent("子任务描述")
  |
  v
ctx.subagents.start(...)  -- 委派给子 agent
  |
  v
子 agent 完成，返回结果
  |
  v
脚本继续，可能启动更多子 agent
  |
  v
脚本 return 最终结果
```

启动请求（来自文档）：

```ts
interface WorkflowStartRequest {
  script: string               // 脚本正文（top-level await 允许）
  meta: WorkflowMeta           // 身份块
  args?: unknown              // 输入参数（作为 args 全局变量）
  subagentProvider?: string    // 子 agent provider 覆盖
  maxTotalAgents?: number      // 子 agent 总数上限
  parent: Agent                // 父 agent
  signal?: AbortSignal         // 取消信号
}
```

文档强调：`meta` 和 `args` 是普通 JSON 数据。引擎用 schema 校验 `meta`，并在任何工作开始前明确报错并拒绝无效数据。引擎绝不会通过对脚本文本求值来获取它们——这防止了脚本注入。

WorkflowMeta（工作流元数据）：

```ts
interface WorkflowMeta {
  name: string                 // kebab-case 名称
  description: string          // 一行描述
  whenToUse?: string           // 何时使用
  phases?: WorkflowPhase[]     // 阶段声明
}
```

文档明确：`phases` 仅用于进度展示。`phase()` 调用与标题匹配供观察者使用，但不暗示任何执行结构——引擎不强制按 phase 执行。

> 金句：workflow 脚本是模型写的 JavaScript，不是 YAML 配置。这意味着编排逻辑是图灵完备的——但执行环境是受限的 worker thread，不是主进程。

## 14.8 工作流引擎：worker thread 隔离

dsh-workflow-worker-thread 是唯一的工作流引擎实现。来自文档：

> 一个 node:worker_threads 引擎——每个 run 一个 worker，脚本的 vm 上下文位于其中。

每个 run 创建一个新的 worker thread，脚本在 worker 的 V8 虚拟机上下文中执行。这提供了隔离：

| 维度 | 主进程 | worker thread |
|---|---|---|
| 事件循环 | 完整 dsh | 独立 |
| ctx 服务 | 完整 | 仅 agent() API |
| 失败影响 | 可能崩溃 dsh | 仅该 run 失败 |
| 资源 | 共享 | run 结束即释放 |

终态结果（来自文档）：

```ts
interface WorkflowResult {
  value: unknown               // 脚本返回值（纯 JSON 数据，null = 无返回）
  stopReason: WorkflowStopReason  // completed / cancelled / error
  error?: string               // 失败信息（非 completed 时）
}
```

`stopReason` 不是 `completed` 时，消费方将其映射为 `isError` 工具结果——不把部分输出当作成功上报。来自文档：

> A non-completed reason carries the failure in error; the consumer maps it to an isError tool result rather than reporting partial output.

## 14.9 工作流工具：模型接口

dsh-tool-workflow 是面向模型的 Consumer。来自源码（packages/workflow/tool-workflow/src/index.ts）：

```ts
export const name = 'tool-workflow'
export const inject = ['tools', 'workflowEngine', 'systemPrompt']

export interface Config {
  toolName?: string       // 模型面向的工具名（默认 'workflow'）
  maxResultChars?: number  // 结果截断上限（默认 50000）
}
```

源码注释揭示了关键设计：

> Execution awaits run.result and always disposes the run; non-completed reasons become tool errors, and background collection remains deferred.

`always disposes the run` 意味着即使脚本失败，worker thread 也会被清理——不留资源泄漏。`background collection remains deferred` 意味着后台收集的结果不阻塞工具返回。

## 14.10 协作模式与资源控制

三种典型协作模式：

**模式 1：并行扇出**

```javascript
const files = ['auth.ts', 'router.ts', 'store.ts']
const results = await Promise.all(
  files.map(f => agent(`审查 ${f} 的类型安全问题并修复`))
)
return { reviewed: files, issues: results.map(r => r.value) }
```

**模式 2：流水线**

```javascript
const spec = await agent("分析需求，输出测试用例列表")
const impl = await agent(`根据以下测试用例实现代码：${spec.value}`)
const review = await agent(`审查实现是否通过测试用例：${impl.value}`)
return { tests: spec.value, code: impl.value, review: review.value }
```

**模式 3：条件分支**

```javascript
const analysis = await agent("分析这个 bug 的根因")
const rootCause = JSON.parse(analysis.value).rootCause

if (rootCause === 'race-condition') {
  await agent("添加互斥锁修复竞态条件")
} else if (rootCause === 'null-reference') {
  await agent("添加空值检查修复空引用")
} else {
  await agent("添加输入验证和防御性编程")
}
```

资源控制：

| 限制 | 维度 | 作用 | 需要能力 |
|---|---|---|---|
| maxDepth | 深度 | 防止无限递归 | depthLimit |
| maxTotalAgents | 广度 | 防止资源爆炸 | 引擎级 |
| toolFilter | 工具 | 限制子 agent 可用工具 | toolFilter |

需要对应能力 flag 匹配——Provider 不支持 `depthLimit` 时，请求携带 `maxDepth` 会被 `UNSUPPORTED_CAPABILITY` 拒绝。

## 本章小结

| 要点 | 说明 |
|---|---|
| subagent 多提供方 | 同一上下文可共存多个 Provider，按名称注册 |
| 六个 Provider | spawn / fork / acp / codex / claude-code / dsh-sdk |
| 能力声明 fail-loud | 不支持的能力明确拒绝，不静默降级 |
| 两类子代理 | 单次启动（Provider 组合）/ 可继续（管理器组合） |
| Activation 三状态 | running / waiting / settled |
| 所有权图鉴权 | 父级拥有子级，祖先可中断后代 |
| workflow 脚本编排 | 模型写 JS，引擎在 worker thread 执行 |
| worker thread 隔离 | 每个 run 一个 worker，失败不影响主进程 |
| 资源控制 | maxDepth 防递归，maxTotalAgents 防爆炸 |
| 三种协作模式 | 并行扇出、流水线、条件分支 |

> 我是怕浪猫，第 14 章写完。subagent 和 workflow 是 dsh 处理大规模任务的方案——让 agent 编排 agent，而不是让一个 agent 扛所有事。
>
> 有问题评论区聊，有纠错欢迎指出。如果这篇对你有帮助，收藏起来——设计 agent 编排系统时这张模式表最好用。
>
> 下一章拆解 compaction（上下文压缩）和 goal（目标管理）——会话太长怎么办、agent 怎么记住目标。
>
> 系列进度：14/16 ｜ 未完待续

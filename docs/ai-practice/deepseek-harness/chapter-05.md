# 第5章：Turn / Step 循环——agent-loop 源码拆解

> 系列：DeepSeek Harness 源码实战 ｜ 进度 5/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

一次模型请求里藏着十几个事件、四种分发模式、一个状态机和一套并发调度器。

上一章我们看了 Session 日志的数据结构，知道了事件是怎么存的。这一章来看事件是怎么产生的——深入 `packages/core/agent-loop/` 的源码，拆解驱动整个 agent 运转的引擎。

我是怕浪猫，这一章信息密度很高，建议坐稳。

## 5.1 turn 和 step 的关系：控制边界与模型请求

dsh 的 agent 循环有两个层次：

**turn（轮次）** 是控制边界。一个 turn 从用户输入到达开始，到 agent 决定停止结束。一个 turn 可以包含零个或多个 step。turn 的结束由 `turn-stopping` 事件决定——如果没有新消息进入 next-step inbox，agent 就会停止。

**step（步骤）** 是模型请求边界。一个 step = 一次模型调用 + 这次调用请求的所有工具执行。模型返回的每一条 tool_call（工具调用）都会在当前 step 内被调度执行，结果作为下一步的输入。

来看一个多 step 的 turn 在日志里的样子：

```
turn/start (turn=1)
  │
  ├── step/start (turn=1, step=1)
  │     user/message → "帮我修 bug"
  │     system-prompt/assemble waterfall → 组装提示词片段 + 工具 schema
  │     agent/request waterfall → {provider, model, ...}
  │     llm/stream waterfall → 流式分片
  │     assistant/chunk × N → 流式分片
  │     assistant/message → 组装后的完整回复（含 sourceEventSeqs 指向 chunks）
  │     tool/call → fs_read
  │     tool/result → 文件内容
  │   step/end
  │
  ├── step/start (turn=1, step=2)
  │     user/message → 工具结果作为新输入
  │     system-prompt/assemble → 重新组装
  │     agent/request → 可能更新配置
  │     llm/stream → 流式
  │     assistant/chunk × N
  │     assistant/message → "我找到了 bug"
  │     tool/call → fs_edit
  │     tool/result → 编辑成功
  │   step/end
  │
  ├── step/start (turn=1, step=3)
  │     user/message → 工具结果
  │     assistant/chunk × N
  │     assistant/message → "bug 已修复"（无 tool_call）
  │   step/end
  │
  ▼
agent/turn-stopping (serial) → 无 next 消息 → 确认停止
turn/end (turn=1, reason=completed)
```

step 3 没有产生 tool_call，这意味着模型认为任务完成了。`concludesTurn` 标记为 true，turn 正常结束。

对比表：

| 维度 | turn | step |
|---|---|---|
| 是什么 | 控制边界 | 模型请求边界 |
| 数量关系 | 1 个 turn 含 0..N 个 step | 1 个 step 含 1 次模型调用 + 0..N 个工具调用 |
| 开始条件 | 用户输入到达 inbox | pre-step 决策为 enter |
| 结束条件 | turn-stopping 通过且无新消息 | 模型返回无 tool_call 或所有工具执行完毕 |
| 可被中止 | 是（abort） | 是（abort） |

## 5.2 inbox 机制：消息的队列与领取

在深入 turn 之前，先看消息是怎么到达 agent 的。

dsh 的 agent 有一个 Inbox（收件箱），它是消息队列的抽象。消息不是直接塞进模型请求的，而是先进入 inbox，由 agent 循环在合适的时机领取（claim）。

Inbox 有两个目标槽位：

| 槽位 | 说明 |
|---|---|
| next-turn | 下一个 turn 开始时领取的消息 |
| next-step | 当前 turn 的下一个 step 领取的消息 |

当用户发一条消息时，它进入 `next-turn` 槽位。agent 循环开始一个新 turn 时，从 `next-turn` 领取消息。工具执行产生的上下文消息（文件变更通知等）进入 `next-step` 槽位，当前 turn 的下一个 step 领取。

来看 inbox 的三个事件，都是 emit 模式：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
this.inbox = new Inbox(session, {
  inserted: (message) => { this.dispatch.emit('agent/inbox/inserted', { message }) },
  discarded: (message) => { this.dispatch.emit('agent/inbox/discarded', { message }) },
  claimed: (message, turn) => { this.dispatch.emit('agent/inbox/claimed', { message, turn }) },
})
```

- `inserted`：消息被插入 inbox
- `discarded`：消息被丢弃（比如被新消息挤掉）
- `claimed`：消息被 agent 领取

来看 `send` 方法，理解消息如何进入 inbox：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
send(message: UserMessage, target: InboxTarget, wakeup: boolean): void {
  const wakingAfterAbort = wakeup && this.phase.kind !== 'idle' && this.phase.abort.signal.aborted
  const resolvedTarget = wakingAfterAbort ? 'next-turn' : target
  this.inbox.splice(resolvedTarget, Infinity, 0, [message])
  if (wakeup) this.wakeDriver(wakingAfterAbort)
}
```

注意 `wakingAfterAbort` 的逻辑：如果消息是 waking（唤醒）类型，且当前 phase 不是 idle 且 abort 已触发（上一次 turn 被中止了），那么这条消息会被重定向到 `next-turn` 槽位。因为 waking 消息不能加入一个已被中止的活动，它必须启动下一个 turn。

> 金句：inbox 不是简单的 FIFO（First In First Out，先进先出）队列，而是一个有优先级和目标槽位的调度结构。

## 5.3 Phase 状态机：idle / maintenance / running

agent-loop 的核心是一个状态机，称为 Phase。来看定义：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
type Phase =
  | { kind: 'idle'; lastTurn: number }
  | {
    kind: 'maintenance'
    abort: AbortController
    lastTurn: number
    wakeRequested: boolean
  }
  | { kind: 'running'; abort: AbortController; turn: number; step: number; wakeRequested: boolean }
```

三个状态：

| 状态 | 含义 | 可执行操作 |
|---|---|---|
| idle | 空闲，没有正在执行的 turn | 等待新消息唤醒 |
| maintenance | 维护中，正在做 turn 结束后的清理 | 可被唤醒请求打断 |
| running | 正在执行一个 turn 的某个 step | 可被 abort 中止 |

状态转换：

```
idle ──wakeup──▶ running
                   │
                   │ turn 结束
                   ▼
              maintenance
                   │
                   │ 清理完成
                   ▼
                 idle
                   │
                   │ wakeup during maintenance
                   ▼
              running（新 turn）
```

来看 `setPhase` 方法，它负责状态切换和外部通知：

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
private setPhase(next: Phase): void {
  const previousStatus = this.status
  this.phase = next
  const status = this.status
  if (status !== previousStatus) {
    this.dispatch.emit('agent/status', { status })
  }
}

get status(): AgentStatus {
  return this.phase.kind === 'idle' || this.phase.kind === 'maintenance' ? 'idle' : 'running'
}
```

外部可见的状态只有两种：`idle` 和 `running`。maintenance 对外表现为 idle（因为不在执行模型请求），但内部区分了 maintenance 和 idle 是为了处理「清理过程中收到新消息」的情况。

## 5.4 事件流拆解：pre-step / request / stream / turn-stopping

现在来看一个完整 turn 的事件流。代码在 `agent.ts` 的 `turn()` 方法中。

### turn 开始

```typescript
// packages/core/agent-loop/src/agent.ts（节选）
private async turn(): Promise<boolean> {
  const phase = this.phase
  const { signal } = phase.abort
  signal.throwIfAborted()
  const turn = phase.turn + 1
  this.session.append('turn/start', { turn })
  phase.turn = turn
  let turnEnds: TurnEndReason | null = null
  let target: InboxTarget = 'next-turn'
```

turn 开始时，先递增 turn 序号，追加 `turn/start` 事件到日志。`target` 初始为 `next-turn`，表示从 next-turn 槽位领取消息。

### pre-step：决定要不要进入这个 step

```typescript
  while (true) {
    signal.throwIfAborted()
    const step = phase.step + 1
    const decision = await this.preStep(target, { turn, step })
    if (decision.kind === 'reject') {
      turnEnds = { kind: 'blocked' }
      return false
    }
    if (turnEnds && decision.messages.length === 0) break
```

`preStep` 方法里分发 `agent/pre-step` waterfall 事件：

```typescript
private async preStep(target: InboxTarget, position: { turn: number; step: number }): Promise<PreparedStep> {
  const claimed = this.inbox.claim(target, position.turn)
  const assembly = await this.loopCtx.systemPrompt.assemble(assembleContextFor(this, signal))
  const decision = await this.dispatch.waterfall(
    'agent/pre-step', { messages: claimed, ...position, signal },
    (): Promise<PreStepDecision> => Promise.resolve<PreStepDecision>({
      kind: 'enter',
      messages: context === undefined ? claimed : [...claimed, context],
    }),
  )
  return decision.kind === 'reject' ? decision : { ...decision, assembly }
}
```

流程是：从 inbox 领取消息 → 组装 system prompt → 分发 pre-step waterfall（默认返回 enter）。如果监听器返回 reject，turn 以 blocked 结束。

### step 执行：请求模型 + 流式输出 + 工具调用

进入 step 后，先追加 `step/start` 事件，然后把消息写入日志，再发起模型请求：

```typescript
    this.session.append('step/start', { turn, step })
    for (const message of decision.messages) {
      this.session.append('user/message', message, { surfaceOp: 'append' })
    }
    const stepEnd = await this.step(decision.assembly)
```

`step()` 方法内部（节选关键部分）：

```typescript
private async step(assembly: PromptAssembly): Promise<StepEndReason | null> {
  const { request, preparedCall } = await this.buildRequest(
    turn, step, assembly.tools, system, this.session.deriveMessages(), signal,
  )
  const assembler = new BlockAssembler()
  const chunkSeqs: number[] = []
  const stream = preparedCall?.stream(request) ?? this.loopCtx.llm.stream(request)
  for await (const chunk of stream) {
    chunkSeqs.push(this.session.append('assistant/chunk', { turn, step, chunk }).seq)
    assembler.push(chunk)
  }
  const finish = assembler.finish
  // ... 错误处理 ...
  const message = createAssistantMessage({ content: assembler.blocks(), source: { ... } })
  this.session.append('assistant/message', { turn, step, message, usage }, { surfaceOp: 'append', sourceEventSeqs: chunkSeqs })
  if (finish.kind === 'max-tokens') return { kind: 'max-tokens' }
  const toolCalls = message.content.filter(block => block.type === 'tool-call')
  if (toolCalls.length === 0) return { kind: 'completed' }
  const { concluded } = await executeToolCalls(this.loopCtx, turn, step, toolCalls, signal, context => this.inbox.splice('next-step', ...))
  return concluded ? { kind: 'completed' } : null
}
```

这段代码做了以下事情：

1. `buildRequest`：组装模型请求（下一节详述）
2. 流式读取：`for await (const chunk of stream)` 逐 chunk 追加到日志
3. 组装消息：`BlockAssembler` 把 chunk 组装成完整的 assistant message
4. 追加消息事件：`assistant/message` 带 `sourceEventSeqs` 指向产生它的 chunk 序列号
5. 判断结束原因：max-tokens（达到 token 上限）、completed（无 tool_call）、null（有 tool_call，继续）
6. 执行工具调用：`executeToolCalls` 调度工具（下一节详述）

### buildRequest：配置如何决定

```typescript
private async buildRequest(turn, step, tools, system, boundaryMessages, signal): Promise<{ request, preparedCall }> {
  const persistedHeader = session.requestHeader()
  const route = { provider: this.options.provider ?? '', model: this.options.model ?? '' }
  // ... 构建 seedConfig ...
  const proposedConfig = await this.dispatch.waterfall(
    'agent/request', { turn, step, signal },
    () => Promise.resolve(seedConfig),
  )
  if (!proposedConfig.provider || !proposedConfig.model) {
    throw new Error(`agent has no provider/model`)
  }
  preparedCall = await this.loopCtx.llm.prepareCall(proposedConfig, signal)
  // ... 追加 request/header 事件 ...
}
```

`agent/request` 是 waterfall 事件，监听器可以修改 provider、model、reasoningEffort（推理力度）等配置。最终如果没有 provider 或 model，抛错。

### turn-stopping：决定要不要停下来

当 step 结束且有 `turnEnds`（结束原因）时，检查 next-step inbox：

```typescript
    if (turnEnds && this.inbox.nextStep.length === 0) {
      await this.dispatch.serial('agent/turn-stopping', { turn, signal })
      signal.throwIfAborted()
    }
    if (turnEnds && this.inbox.nextStep.length === 0) break
    target = 'next-step'
```

注意逻辑：先检查 inbox 是否为空 → 分发 `turn-stopping` serial 事件 → 再次检查 inbox。为什么检查两次？因为 serial 事件的监听器可能往 inbox 里塞消息（比如一个「还有事情没做完」的监听器注入一条续跑消息）。如果第二次检查时 inbox 不为空了，turn 就不会停。

### 完整事件流图

```text
turn/start
  │
  ▼
agent/pre-step waterfall ── reject ──▶ turn/end (blocked, 无 step)
  │ enter
  ▼
step/start
  │
  ├── user/message × N（领取的消息 + 注入的上下文）
  ├── system-prompt/assemble waterfall（组装提示词片段 + 工具 schema）
  ├── agent/request waterfall（可修改 provider/model 配置）
  ├── llm/stream waterfall → assistant/chunk × N（durable）
  ├── assistant/message（组装结果 + sourceEventSeqs 列出精确的 chunk seq，含空列表）
  │
  ├── 有 tool_call？
  │     ├── 是 ──▶ executeToolCalls
  │     │              ├── tool/call × N（durable，执行前记录）
  │     │              ├── tools/pre-execute → tools/execute → tools/post-execute（三个 waterfall）
  │     │              ├── tool/result × N（durable，单一模型可见结果）
  │     │              └── 结果进入 next-step inbox
  │     └── 否 ──▶ stepEnd = completed
  │
  ▼
step/end
  │
  ▼
turnEnds 有值 且 next-step inbox 为空？
  ├── 是 ──▶ agent/turn-stopping (serial, 无 next()) ──▶ 再次检查 inbox
  │            │                               ├── 仍为空 ──▶ break
  │            │                               └── 不为空 ──▶ 继续（target = next-step）
  └── 否 ──▶ 继续（target = next-step）
  │
  ▼
turn/end
```

## 5.5 工具并发调度：barrier / rolling pool / abort 处理

工具调用不是串行执行的。dsh 有一个并发调度器，在 `packages/core/agent-loop/src/tool-calls.ts` 中实现。

### 调度模型

每个工具调用有一个 execution mode（执行模式）：

| 模式 | 说明 |
|---|---|
| exclusive | 独占执行，形成一个 barrier（屏障），后续调用必须等它完成 |
| parallel | 可并行执行，进入 rolling pool（滚动池） |

调度器的核心逻辑：

```typescript
// packages/core/agent-loop/src/tool-calls.ts（节选）
export async function executeToolCalls(ctx, turn, step, toolCalls, signal, acceptContext) {
  const agent = ctx.agents.requireInitiator()
  const planned: PlannedCall[] = toolCalls.map(block => ({
    block,
    exec: { callId: block.id, name: block.name, arguments: parseArguments(block.arguments), agent, signal },
  }))

  let next = 0
  let concluded = false
  while (next < planned.length) {
    const first = planned[next]
    const mode = ctx.tools.executionMode(first.exec).kind
    const group = mode === 'parallel' ? planned.slice(next) : [first]
    const outcome = await runGroup(ctx, turn, step, group, mode, signal, acceptContext)
    next += outcome.consumed
    concluded ||= outcome.concluded
    if (outcome.aborted) {
      for (const call of planned.slice(next)) appendSkippedToolCall(session, turn, step, call.block)
      return { concluded }
    }
  }
  return { concluded }
}
```

流程是：

1. 把所有 tool_call 转成 PlannedCall
2. 从下一个未执行的调用开始，检查它的 execution mode
3. 如果是 parallel，把它和后面所有 parallel 调用组成一组，进 rolling pool
4. 如果是 exclusive，单独一组，形成 barrier
5. 执行这一组，等它完成后再继续
6. 如果 abort 了，为所有未启动的调用追加合成的跳过事件

### rolling pool 的提交顺序

关键设计：**dispatch 可以重叠，但结果按模型顺序提交**。

来看 `runGroup` 的核心逻辑：

```typescript
// packages/core/agent-loop/src/tool-calls.ts（节选）
async function runGroup(ctx, turn, step, group, mode, signal, acceptContext): Promise<GroupOutcome> {
  const slots: (Slot | undefined)[] = group.map(() => undefined)
  let committed = 0
  let nextToStart = 0

  const commitReady = async (): Promise<void> => {
    while (committed < group.length) {
      const slot = slots[committed]
      if (slot === undefined) break  // 遇到未完成的 slot，停止提交
      const result = slot.needsPost
        ? await ctx.tools[TOOL_RUNTIME_SCHEDULER].finalize(slot.exec, slot.result)
        : ctx.tools[TOOL_RUNTIME_SCHEDULER].finish(slot.exec, slot.result)
      appendToolResult(session, turn, step, group[committed].block, result, callSeqs[committed])
      committed++
    }
  }
```

`committed` 只在连续的已完成 slot 上前进。如果 slot[2] 完成了但 slot[1] 还在跑，slot[2] 的结果不会先提交。这保证了日志中的 `tool/result` 事件顺序与模型给出的 `tool_call` 顺序一致。

为什么这很重要？因为模型的下一步请求会从日志派生消息历史，工具结果的顺序会影响模型的理解。如果顺序乱了，模型可能会困惑。

### abort 处理

当 abort 触发时：

1. 停止启动新调用
2. 等待已启动的调用完成（drain）
3. 为已启动的调用正常提交结果
4. 为未启动的调用追加合成的跳过事件（`TOOL_ABORTED_BEFORE_DISPATCH`）

合成跳过事件是为了保持日志的完整性——每个 `tool/call` 都要有对应的 `tool/result`，这样回放才有效。

来看代码：

```typescript
// packages/core/agent-loop/src/tool-calls.ts（节选）
if (outcome.aborted) {
  for (const call of planned.slice(next)) appendSkippedToolCall(session, turn, step, call.block)
  return { concluded }
}
```

`appendSkippedToolCall` 为每个未启动的调用追加 `tool/call` 和一个带 `TOOL_ABORTED_BEFORE_DISPATCH` 错误码的 `tool/result`。

> 金句：调度器不只是「跑工具」，它还要保证日志的完整性。每个 call 都要有 result，abort 了也要补上。

### max-tokens 的 sticky 语义

还有一个细节值得注意。在 `turn()` 方法里有这段注释和逻辑：

```typescript
// max-tokens is sticky: once any step hits the ceiling, later steps
// that complete normally must not downgrade the turn outcome.
if (turnEnds === null || turnEnds.kind !== 'max-tokens') turnEnds = stepEnd
```

如果一个 step 因为 max-tokens（达到 token 上限）结束了，后续的 step 即使正常完成（completed），turn 的结束原因也保持 max-tokens。这是「sticky」（粘性）语义——一个已经发生的事实（达到了 token 上限）不应该被后续的正常完成抹掉。

## 本章小结

| 要点 | 说明 |
|---|---|
| turn | 控制边界，含 0..N 个 step |
| step | 模型请求边界，含 1 次模型调用 + 0..N 个工具调用 |
| inbox | 消息队列，next-turn 和 next-step 两个槽位 |
| Phase 状态机 | idle / maintenance / running |
| agent/pre-step | waterfall 事件，可修改消息或拒绝进入 step |
| agent/request | waterfall 事件，可修改模型请求配置 |
| agent/turn-stopping | serial 事件，顺序执行，监听器可注入续跑消息 |
| 流式输出 | assistant/chunk 逐 token 追加日志 |
| sourceEventSeqs | assistant/message 指向产生它的 chunk 序列号 |
| 工具调度模型 | exclusive（barrier）和 parallel（rolling pool） |
| 提交顺序 | dispatch 可重叠，结果按模型顺序提交 |
| abort 处理 | drain 已启动调用 + 为未启动调用合成跳过事件 |
| max-tokens sticky | 一旦触发，不被后续 completed 降级 |

## 下章预告

agent-loop 知道什么时候调用工具了，但工具内部到底怎么执行？权限检查在哪做？超时重试怎么实现？结果怎么处理？

下一章，我们来拆 dsh 的工具执行流水线——从 pre-execute 到 post-execute 的完整链路。

> 我是怕浪猫，这一章是整个系列最硬核的部分之一，建议反复看。你对 agent 循环的设计有什么看法？评论区聊聊。
>
> 系列进度：5/8 ｜ 下一章：工具执行流水线

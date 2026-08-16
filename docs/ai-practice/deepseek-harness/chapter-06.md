# 第6章：工具执行流水线——pre-execute 到 post-execute

> 系列：DeepSeek Harness 源码实战 ｜ 进度 6/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

模型说「帮我读文件」，但读之前要查权限，读之后要检查结果，中间还要处理超时和重试。

上一章我们看了 agent-loop 怎么调度工具调用，知道 `executeToolCalls` 把调用交给了一个调度器。但调度器只是排队和并发管理，工具真正执行的细节——权限检查、超时重试、结果处理——都在一条流水线里。这一章就来拆这条流水线。

我是怕浪猫，这一章我们深入 `packages/core/tools/` 的源码，看一个工具调用从「模型说出口」到「结果回到模型」中间经历了什么。

## 6.1 流水线全景图

一个工具调用的完整生命周期是这样的：

```
模型输出 tool_call
  │
  ▼
tool/call 事件（durable session 事件，执行前记录）
  │
  ▼
tools/pre-execute（waterfall）
  │  ├── hooks 拦截（hooks-claude-code / hooks-codex）
  │  ├── 权限检查：allow / deny / ask
  │  ├── 沙箱策略
  │  └── tool-jobs 后台任务检查
  │  next() 委托 → PreToolDecision
  │  ask → ctx.approval 一次性审批（absent 或 unanswerable: deny）
  ▼
单调守卫（guard）
  │  ├── 同步检查，identity protected
  │  └── 返回 denial reason 或 undefined（不可推翻）
  ▼
tools/execute（waterfall）
  │  ├── 超时策略（timeout-policy）
  │  ├── 重试策略
  │  └── session-checkpoint-policy 检查点
  │  next() 委托 → 执行工具 body
  │  工具 body 可能触发 fs/write-intent 或 fs/edit-intent 事件
  ▼
工具 body 执行
  │  可能产生 owned session 事件（todo/write, fs/observed, hook/invoked, tool/code-dispatch）
  │  返回 ToolExecutionResult
  ▼
tools/post-execute（waterfall）
  │  ├── accept（接受结果）
  │  ├── block（阻止结果）
  │  ├── replace（替换结果，如 compaction-tool-result-pruner）
  │  └── add context（附加上下文，如 spill-policy）
  │  next() 委托 → PostToolDecision
  ▼
注册表外层规范化（normalize）
  │  无损快照候选结果，snapshot throw 变成 isError
  ▼
ToolDefinition.finalizeContent
  │  工具定义的同步内容最终化（内容-only 不变量）
  ▼
tools/result（同步通知，不可变权威结果）
  │
  ▼
tool/result 事件（durable session 事件，单一模型可见结果）
  │
  ▼
结果进入 active-batch additionalContexts FIFO → 下一个 step
```

这条流水线有五个关键节点，每个节点都是可扩展的。来看每个节点的职责。

| 节点 | 分发模式 | 职责 | 可短路 |
|---|---|---|---|
| tools/pre-execute | waterfall | 权限、沙箱、hooks | 是（deny/ask） |
| 单调守卫 | 同步函数 | 最终否决权 | 是（返回 reason） |
| tools/execute | waterfall | 超时、重试、指标 | 否（包裹器） |
| tools/post-execute | waterfall | 结果审查、替换、增强 | 否（但可 block） |
| finalizeContent | 函数调用 | 内容最终化 | 否 |

> 金句：流水线不是一条直线，而是一串中间件。每一层都可以修改、拦截、增强，但每一层都有明确的职责边界。

## 6.2 pre-execute：权限、审批、沙箱门禁

`tools/pre-execute` 是第一个 waterfall 事件，也是最重要的安全关卡。它的类型定义：

```typescript
// packages/core/tools/src/index.ts（节选）
interface Events {
  /**
   * Allow, deny, or ask before dispatch. `next()` delegates to allow; missing
   * approval support turns `ask` into denial. Async gates must observe
   * `exec.signal`; the registry rechecks cancellation after they settle but
   * never abandons their promise.
   * @mode waterfall
   */
  'tools/pre-execute'(
    this: Scoped<ToolRuntime>,
    exec: ToolExecution,
    next: () => Promise<PreToolDecision>
  ): Promise<PreToolDecision>
}
```

`PreToolDecision` 有三种结果：

| 决策 | 含义 | 后续 |
|---|---|---|
| allow | 允许执行 | 继续到守卫和 execute |
| deny | 拒绝执行 | 工具不执行，结果带错误 |
| ask | 请求用户审批 | 弹出审批确认，用户同意则 allow，拒绝则 deny |

注意注释里的两句话：

1. **`next()` delegates to allow**：调用 next() 意味着「我没有意见，允许执行」。这是一个默认放行的设计——中间件不需要显式 allow，只需要不短路。
2. **missing approval support turns `ask` into denial**：如果没有审批服务（`ctx.get('approval')` 为空），ask 会被降级为 deny。安全失败——宁可拒绝也不静默放行。

### 审批流程

当 pre-execute 返回 ask 时，dsh 会检查是否有审批服务。来看简化逻辑：

```
pre-execute 返回 ask
  │
  ├── ctx.get('approval') 存在？
  │     ├── 是 ──▶ 弹出审批确认
  │     │              ├── 用户同意 ──▶ allow
  │     │              └── 用户拒绝 ──▶ deny
  │     └── 否 ──▶ deny（安全降级）
  │
  ▼
allow 或 deny
```

审批服务由 `dsh-user-approval` 包提供，它在 `dsh-base` bundle 中默认挂载。Web GUI 里会弹一个确认框，headless 模式下默认拒绝（因为没有人可以审批）。

### 沙箱策略

沙箱策略也通过 pre-execute 实施。比如 `fs-sandbox` 包会监听 `tools/pre-execute`，检查文件系统操作是否在允许的路径范围内。如果模型想写 `/etc/passwd`，沙箱监听器返回 deny。

这种设计的好处是：沙箱策略是可插拔的。你可以用 `fs-local`（不限制路径），也可以换成 `fs-sandbox`（限制路径），或者自己写一个更严格的策略。不需要改工具代码。

## 6.3 单调守卫：不可推翻的否决权

pre-execute waterfall 之后，还有一个同步的守卫检查。这是 dsh 工具流水线里最精巧的设计之一。

来看类型定义：

```typescript
// packages/core/tools/src/index.ts（节选）
/**
 * A monotonic execution guard evaluated after every `tools/pre-execute`
 * listener and before the tool body. Returning a reason denies the call;
 * returning `undefined` leaves it unchanged. Because guards have no allow
 * result, listener ordering cannot turn a denial back into permission.
 */
export type ToolGuard = (execution: Readonly<ToolExecution>) => string | undefined
```

关键句：**Because guards have no allow result, listener ordering cannot turn a denial back into permission.**（因为守卫没有 allow 结果，监听器顺序不能把一个否决变回允许。）

这就是「单调」（monotonic）的含义：权限只能收紧，不能放松。一旦某个守卫说「不行」，其他守卫或 pre-execute 监听器不能推翻它。

对比 pre-execute 和守卫的区别：

| 维度 | pre-execute | 单调守卫 |
|---|---|---|
| 类型 | waterfall 事件 | 同步函数 |
| 返回值 | allow / deny / ask | reason（否决）或 undefined（放行） |
| 可异步 | 是 | 否 |
| 可推翻 | 后续监听器可以覆盖前面的决策 | 不可推翻 |
| 典型用途 | 审批、沙箱（需要异步交互） | 硬性限制（同步检查） |

来看守卫的注册和检查：

```typescript
// packages/core/tools/src/index.ts（节选）
class ToolLayer implements ScopeLayer {
  readonly guards = new AnonymousEntries<ToolGuard>()

  /** First monotonic denial from this layer's live guard registrations. */
  guardReason(exec: ToolExecution): string | undefined {
    for (const guard of this.guards.values()) {
      const reason = guard(exec)
      if (reason !== undefined) return reason
    }
    return undefined
  }
}
```

`guardReason` 遍历所有注册的守卫，返回第一个非 undefined 的否决原因。只要有任何一个守卫说不行，就不行。

守卫注册通过 `ctx.tools.guard()` 方法：

```typescript
// 注册一个守卫
const dispose = ctx.tools.guard((exec) => {
  if (exec.name === 'fs_write' && isDangerousPath(exec.arguments.path)) {
    return 'Writing to system directories is not allowed'
  }
  return undefined
})
```

> 金句：pre-execute 是可协商的门卫，守卫是不可推翻的法官。前者可以讨论，后者说了就定了。

## 6.4 execute：超时、重试与执行包裹

`tools/execute` 是第二个 waterfall 事件，它包裹工具的实际执行。类型定义：

```typescript
// packages/core/tools/src/index.ts（节选）
interface Events {
  /**
   * Around-dispatch waterfall for timeout, retry, or metrics. `next()` returns
   * a normalized result; wrappers may change only `exec.signal`, while call
   * identity remains immutable. The registry re-fuses the original caller
   * signal before the body, so replacement cannot detach caller cancellation;
   * wrappers must still restore their signal and reach quiescence.
   * @mode waterfall
   */
  'tools/execute'(
    this: Scoped<ToolRuntime>,
    exec: ToolDispatchExecution,
    next: () => Promise<ToolExecutionResult>
  ): Promise<ToolExecutionResult>
}
```

注意注释里的约束：

1. **wrappers may change only `exec.signal`**：包裹器只能修改 signal（用于自己的超时控制），不能改工具名和参数。
2. **call identity remains immutable**：调用身份（callId、name、arguments）不可变。
3. **registry re-fuses the original caller signal before the body**：注册表在工具 body 执行前会重新接上调用方的 signal，防止包裹器替换 signal 导致调用方取消失效。
4. **wrappers must still restore their signal and reach quiescence**：包裹器必须恢复自己的 signal 并达到安静状态——不能留下未完成的异步操作。

这些约束确保了即使有超时和重试中间件，取消语义仍然是正确的。

### 超时策略

`timeout-policy` 包注册 `tools/execute` 监听器，为工具调用添加超时控制。简化逻辑：

```typescript
// 伪代码示意
ctx.tools.on('tools/execute', async (exec, next) => {
  const timeoutMs = getTimeoutFor(exec.name)
  if (timeoutMs === undefined) return next()  // 无超时配置

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    // 用自己的 signal 替换（registry 会在 body 前重新接上 caller signal）
    return await next({ ...exec, signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
})
```

注意：不是所有工具都有超时。文件 I/O 操作（如 `fs_read`）不设 timeoutMs，因为没有合理的 deadline——读一个大文件不应该被超时杀掉。超时策略通过配置或工具注册时的元数据决定。

### 重试策略

`llm-retry` 包为 LLM 请求提供重试，而工具执行的重试由 `tools/execute` 中间件实现。重试策略通常只用于幂等操作（如网络请求），不用于有副作用的操作（如文件写入）。

### 注意：文件 I/O 无超时

dsh 的文档明确提到：文件 I/O 不设 timeoutMs（无 deadline）。这是工程上的判断——文件操作通常不会无限挂起，而且强制中断文件操作可能导致文件系统状态不一致。如果文件操作真的挂起了，更合理的做法是修复文件系统问题，而不是加超时。

## 6.5 post-execute：accept / block / replace / add context

工具执行完毕后，结果不是直接回到模型。它先经过 `tools/post-execute` waterfall。

类型定义：

```typescript
// packages/core/tools/src/index.ts（节选）
interface Events {
  /**
   * Accept, replace, enrich, or block a normalized dispatch result. `next()`
   * accepts it unchanged; thrown tools still reach this waterfall as errors.
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

`PostToolDecision` 有四种决策：

| 决策 | 含义 | 效果 |
|---|---|---|
| accept | 接受结果 | 结果原样进入日志 |
| block | 阻止结果 | 结果不进入模型可见表面，但日志仍记录 |
| replace | 替换结果 | 用新内容替换原始结果 |
| add context | 附加上下文 | 在结果之外追加额外消息到 inbox |

典型用途：

**accept**：默认行为。大多数工具的结果都是 accept。

**block**：安全审计场景。比如一个工具返回了敏感信息（API Key、密码），post-execute 监听器可以 block 掉，让结果不进入模型上下文。日志里仍然有记录（可审计），但模型看不到。

**replace**：结果改写。比如 `compaction-tool-result-pruner` 包会监听 post-execute，把过长的工具结果替换成摘要，减少上下文占用。

**add context**：附加上下文。比如文件编辑工具执行后，post-execute 监听器可以追加一条「文件已变更」的上下文消息到 inbox，让模型在下一步知道哪些文件变了。

### concludesTurn 标记

`ToolExecutionResult` 有一个 `concludesTurn` 布尔字段。如果工具返回 `concludesTurn: true`，表示这个工具的执行已经完成了用户请求，turn 可以直接结束，不需要再发模型请求。

这在 workflow（工作流）场景中很有用。比如一个「搜索并总结」工作流，搜索工具执行完后，工作流引擎可以直接生成总结并标记 concludesTurn，省去一次模型调用。

## 6.6 finalizeContent：内容的最后一道处理

post-execute 之后、日志记录之前，还有一个 `finalizeContent` 步骤。它不是事件，而是工具定义上的一个可选函数：

```typescript
// packages/core/tools/src/index.ts（节选）
interface ToolDefinition {
  // ...
  finalizeContent?(exec: Readonly<ToolExecution>, result: Readonly<ToolExecutionResult>): ContentBlock[] | undefined
}
```

`finalizeContent` 接收执行信息和结果，返回最终的 ContentBlock 数组（或 undefined 表示不修改）。它用于工具内部的输出格式化——比如把 JSON 结果转成 Markdown 表格、截断过长的输出、添加分隔符等。

与 post-execute 的区别：

| 维度 | post-execute | finalizeContent |
|---|---|---|
| 类型 | Cordis 事件（可多个监听器） | 工具定义上的函数（单个） |
| 作用域 | 所有工具 | 单个工具 |
| 能修改什么 | 决策（accept/block/replace/add context） | 内容格式 |
| 调用时机 | post-execute 之后 | 规范化之后、日志之前 |

## 6.7 流水线完整事件序列

把整条流水线的事件序列画出来：

```
1. 模型输出 tool_call
2. executeToolCalls 调度器领取调用
3. session.append('tool/call', { callId, name, arguments })
4. ctx.tools.prepare(exec)
   4a. tools/pre-execute waterfall
       ├── listener 1（权限检查）→ next()
       ├── listener 2（沙箱策略）→ next()
       └── default → allow
   4b. guardReason(exec) → undefined（放行）
   4c. 返回 { kind: 'dispatch', exec }
5. ctx.tools.dispatch(exec)
   5a. tools/execute waterfall
       ├── listener 1（超时策略）→ 替换 signal → next()
       ├── listener 2（重试策略）→ next()
       └── default → 执行工具 body
   5b. 工具 body 执行 → ToolExecutionResult
   5c. 返回 { result, kind: 'post-result' }
6. ctx.tools.finalize(exec, result)
   6a. tools/post-execute waterfall
       ├── listener 1（安全审计）→ next()
       ├── listener 2（结果裁剪）→ replace
       └── default → accept
   6b. 规范化 ContentBlock
   6c. finalizeContent（如果有）
   6d. 返回最终结果
7. session.append('tool/result', { callId, message, error?, meta? })
8. 结果进入 next-step inbox
```

注意步骤 3 和 7：`tool/call` 在执行前就写日志了，`tool/result` 在执行后写。这保证了即使工具执行过程中进程崩溃，日志里也有这个调用的记录（只是没有 result）。回放时可以看到「这个调用被发起了但没完成」。

## 6.8 spill：工具结果的溢出处理

还有一个值得讲的机制：spill（溢出）。

当工具结果太大时（比如读了一个 10MB 的文件），直接放进模型上下文会导致 token 爆炸。dsh 的 `spill` 家族负责处理这种情况。

`spill-policy` 包定义了溢出策略。当工具结果超过阈值时，spill 机制会把完整结果存到一个侧车存储（spill-local），只把一个引用（指针 + 摘要）放进模型上下文。模型需要查看完整内容时，通过专门的工具拉取。

```
工具执行返回 10MB 结果
  │
  ▼
spill-policy 检查大小
  │
  ├── 未超阈值 ──▶ 结果原样进入上下文
  │
  └── 超阈值 ──▶ 完整结果存入 spill-local
                  上下文中只放摘要 + 引用
                  模型可用 spill_read 工具拉取完整内容
```

这个机制让 dsh 可以处理大型工程文件，而不会把上下文窗口撑爆。

> 金句：spill 不是「丢弃」，是「暂存」。信息不丢，只是不全部塞进模型的视野。

## 本章小结

| 要点 | 说明 |
|---|---|
| 流水线五节点 | pre-execute → 单调守卫 → execute → post-execute → finalizeContent |
| pre-execute | waterfall，权限/沙箱/审批，可 deny/ask |
| 审批降级 | 无审批服务时 ask 自动降级为 deny（安全失败） |
| 单调守卫 | 同步函数，只有否决权（返回 reason）或放行（undefined），不可推翻 |
| execute | waterfall，超时/重试/指标，只能改 signal 不能改身份 |
| 文件 I/O 无超时 | 文件操作不设 deadline，避免状态不一致 |
| post-execute | waterfall，accept/block/replace/add context |
| concludesTurn | 工具可标记「任务已完成」，跳过后续模型请求 |
| finalizeContent | 工具定义上的函数，内容格式化 |
| 日志时序 | tool/call 在执行前写，tool/result 在执行后写 |
| spill | 大结果存侧车，上下文只放摘要 + 引用 |

## 下章预告

工具流水线搞清楚了。但 dsh 最有意思的设计——能力 Seam——还没讲。为什么换一个 Provider 就能改变整个产品的形态？E2B 远程沙箱是怎么工作的？

下一章，我们来拆能力 Seam 架构，以及如何手写一个 Provider。

> 我是怕浪猫，这一章如果你在做 agent 工具系统设计，建议全文收藏。你的工具执行有类似的安全关卡吗？评论区聊聊。
>
> 系列进度：6/8 ｜ 下一章：能力 Seam——三段式架构与 Provider 替换

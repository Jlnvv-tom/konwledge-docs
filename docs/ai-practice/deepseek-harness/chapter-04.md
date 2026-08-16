# 第4章：Session 会话日志——单一事实源

> 系列：DeepSeek Harness 源码实战 ｜ 进度 4/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

你以为的聊天记录，其实只是日志的一个投影。

做过 agent 项目的人都知道，上下文管理有多痛。对话历史怎么存？工具调用的中间结果放哪？流式输出的 token 分片要不要保留？fork 一个会话时哪些状态要复制？这些问题在 dsh 里有一个统一的答案：Session 事件日志。

我是怕浪猫，这一章我们拆开 dsh 的数据核心——Session。它是整个系统的「单一事实源」（Single Source of Truth），所有其他视图都从它派生。

## 4.1 为什么是 append-only 事件日志而不是消息数组

先来看两种设计思路的差异。

**方案 A：消息数组**（大多数简单 agent 项目的做法）

```
messages = [
  { role: 'user', content: '帮我读一下 package.json' },
  { role: 'assistant', content: '...', tool_calls: [...] },
  { role: 'tool', content: '...', tool_call_id: '...' },
  { role: 'assistant', content: '这是文件内容' },
]
```

简单直接，但有问题：

- 流式输出的 token 分片丢了——只有最终消息，无法精确回放
- turn/step 的边界信息丢了——不知道哪条消息属于哪次请求
- 请求配置（provider、model、参数）丢了——不知道用了什么模型
- fork 时需要深拷贝整个数组，且无法表达「fork 自某个位置」
- 工具调用的执行细节（超时、重试、审批）丢了

**方案 B：append-only 事件日志**（dsh 的做法）

```
events = [
  { seq: 1, type: 'turn/start', data: { turn: 1 } },
  { seq: 2, type: 'step/start', data: { turn: 1, step: 1 } },
  { seq: 3, type: 'user/message', data: { ... } },
  { seq: 4, type: 'request/header', data: { header: ... } },
  { seq: 5, type: 'assistant/chunk', data: { chunk: ... } },
  { seq: 6, type: 'assistant/chunk', data: { chunk: ... } },
  { seq: 7, type: 'assistant/message', data: { message: ..., usage: ... } },
  { seq: 8, type: 'tool/call', data: { callId: ..., name: ..., arguments: ... } },
  { seq: 9, type: 'tool/result', data: { message: ... } },
  { seq: 10, type: 'step/end', data: { turn: 1, step: 1 } },
  { seq: 11, type: 'turn/end', data: { turn: 1, reason: { kind: 'completed' } } },
]
```

每一条都是一个不可变的事件，有一个单调递增的 seq（序列号）。所有信息都保留：流式分片、turn/step 边界、请求配置、工具执行细节。

来看 dsh 源码中对 Session 的定义，来自 `packages/core/session/src/types.ts`：

```typescript
// packages/core/session/src/types.ts（节选）
/**
 * The merge-extensible, append-only source of truth for an agent interaction.
 * Message history is derived from this log. Every event is lossless JSON and
 * sequence numbers stay contiguous, including raw chunks, so persistence can
 * store the canonical log verbatim.
 */
export interface SessionEventMap {
  // ... 事件类型定义
}
```

注释里三个关键词：**append-only**（仅追加）、**lossless JSON**（无损 JSON）、**derived**（派生的）。消息历史是从日志派生的，不是日志本身。

对比表：

| 维度 | 消息数组 | 事件日志 |
|---|---|---|
| 存储方式 | 可变数组，可修改 | 仅追加，不可变 |
| 流式分片 | 丢失 | 保留（assistant/chunk） |
| turn/step 边界 | 无 | 显式记录 |
| 请求配置 | 无 | request/header 快照 |
| fork | 深拷贝整个数组 | 从某个 seq 开始引用 |
| 回放 | 不可能 | 完全可回放 |
| 持久化 | 自定义格式 | 原样存储 JSONL/SQLite |

> 金句：消息数组是结果，事件日志是过程。丢了过程，就丢了回放和审计的能力。

## 4.2 SessionEventMap 全解析

SessionEventMap 是 Session 日志的「词汇表」——定义了所有合法的事件类型。来看真实代码：

```typescript
// packages/core/session/src/types.ts（节选）
export interface SessionEventMap {
  /** Opens turn `turn` before the loop claims queued input or runs pre-step. */
  'turn/start': { turn: number }

  /** Closes turn `turn` with the TurnEndReason that ended it. */
  'turn/end': { turn: number; reason: TurnEndReason }

  /** Opens step `step` of turn `turn` — one model call plus the tool executions it requested. */
  'step/start': { turn: number; step: number }

  /** Closes step `step` of turn `turn`. */
  'step/end': { turn: number; step: number }

  /**
   * A user-role message on the model-visible surface: a direct human prompt,
   * a synthetic agent.inject() context, or an entered goal continuation round.
   */
  'user/message': UserMessage

  /** Raw stream chunk — token-level replay fidelity. */
  'assistant/chunk': { turn: number; step: number; chunk: StreamChunk }

  /** Assembled assistant message for one step (derived history uses this). */
  'assistant/message': {
    turn: number; step: number; message: AssistantMessage; usage?: TokenUsage
  }

  /** The model requested one tool invocation: `name` with the raw `arguments` JSON string. */
  'tool/call': {
    turn: number; step: number; callId: CallId; name: string; arguments: string
  }

  /** A completed tool call's model-facing result. */
  'tool/result': {
    turn: number; step: number; message: ToolResultMessage
    error?: { name: string; code: string }
    meta?: JsonValue
  }

  /** Whole-list snapshot; latest write wins on replay. Log-only UI state. */
  'todo/write': { todos: TodoItem[] }

  /** Full header for the next request, appended inside its step before dispatch. */
  'request/header': { header: EpochHeader; reason: RequestHeaderReason }

  /** Route metadata for the next request, logged only when the route or capacity changes. */
  'request/context': RequestContext

  /** Marks the end of a constructor seed. Events before it came from seed (resume, fork, replay). */
  'session/end-seed': Record<string, never>
}
```

每个事件类型的设计都有讲究。逐一看关键的几个：

**turn/start 和 turn/end**：标记一个轮次的开始和结束。turn 可能包含零个或多个 step（步骤）。rejection（拒绝）、空输入、取消、失败都可能关闭一个 turn 而不产生 step——日志会记录这次尝试。

**step/start 和 step/end**：标记一次模型请求及其工具调用的边界。一个 step = 一次模型调用 + 这次调用请求的工具执行。

**user/message**：用户角色的消息。注意它有三种来源：直接的人类输入、合成的 `agent.inject()` 上下文（文件变更通知、子目录 AGENTS.md、skill 内容等）、goal continuation round（目标续跑轮次）。`source` 字段区分它们。

**assistant/chunk 和 assistant/message**：流式分片和组装后的消息。chunk 是 token 级别的原始分片，保证回放保真。message 是一个 step 的完整组装结果。`usage` 字段（token 用量）挂在 message 上，模型输出和计费数据一起旅行。

**tool/call 和 tool/result**：工具调用和结果。callId 配对。arguments 是原始 JSON 字符串（未解析），与模型产生的一致。result 的 `meta` 字段是工具私有的展示载荷，对 core 不透明。

**request/header**：请求配置快照。包含 provider、model、system prompt、tool schemas。最新的快照用于重建下一次请求。reason 字段记录为什么写了个新 header：initial（新会话）、resume（进程重启后的首次请求）、change（换了模型或配置）。

**session/end-seed**：标记种子历史的结束。构造函数从 resume、fork 或 replay 产生的事件都在这个标记之前，当前生命周期产生的事件在之后。这个事件是 log-only 的，payload 为空，位置和时间戳就是它的含义。

速查表：

| 事件类型 | 类别 | 载荷要点 |
|---|---|---|
| turn/start | 边界 | turn 序号 |
| turn/end | 边界 | turn 序号 + 结束原因 |
| step/start | 边界 | turn + step 序号 |
| step/end | 边界 | turn + step 序号 |
| user/message | Surface | 用户消息（三种来源） |
| assistant/chunk | 流式 | 原始 token 分片 |
| assistant/message | Surface | 组装后的完整消息 + usage |
| tool/call | Surface | callId + name + 原始 arguments |
| tool/result | Surface | callId + 结果消息 + error + meta |
| todo/write | Log-only | 整列表快照 |
| request/header | Log-only | 请求配置快照 + 原因 |
| request/context | Log-only | 路由元数据 |
| session/end-seed | Log-only | 空 payload，标记种子边界 |

## 4.3 核心不变量：模型可见即已记录

dsh 文档里有一句加粗的话：

> **模型可见即已记录。** 抵达模型请求的一切都必须能从日志重建，并由一项运行时不变量断言这一点。

这句话是什么意思？它是一个运行时断言：如果某个东西到了模型那里（出现在模型请求的 messages 里），那它一定在日志里有对应的事件。反之，如果日志里没有，它就不可能出现在模型请求里。

这个不变量的价值在于**可审计性**。你可以在任何时候检查日志，知道模型在每一步看到了什么。没有「隐形上下文」——不存在日志之外、模型却能看到的信息。

如果你想新增一种模型可见的输入（比如一种新的上下文注入类型），你不能只是把文本塞进 messages 数组。你必须：

1. 扩展 `SessionEventMap`，新增一个事件类型
2. 确保这个事件被追加到日志
3. 从日志渲染时，把它纳入 messages 派生

这样，新增的输入自动满足「可见即已记录」的不变量。

来看 `SessionEvent` 的类型定义，理解事件的结构：

```typescript
// packages/core/session/src/types.ts（节选）
export type SessionEvent<T extends SessionEventType = SessionEventType> = {
  [K in SessionEventType]: {
    type: K
    /** Monotonic sequence number within the session. */
    seq: number
    /** Unix epoch milliseconds. */
    time: number
    data: SessionEventMap[K]
    /**
     * Marks an event a reader may safely skip when it does not recognize `type`.
     * Absent means required: a reader meeting an unrecognized type without this
     * marker MUST refuse to reconstruct the session instead of silently dropping
     * the event.
     */
    ignorable?: true
    // Surface 事件额外携带的元数据（仅 SurfaceEventType）
  }
}[SessionEventType]
```

注意 `ignorable` 字段的设计：默认情况下，遇到不认识的事件类型，reader 必须拒绝重建会话，而不是静默丢弃。只有标记了 `ignorable: true` 的事件才允许跳过。这是一个「安全失败」的设计——遗忘标记导致过度拒绝（不方便），而不是静默接受一个残缺的会话（危险）。

> 金句：不变量不是文档里的口号，是代码里的运行时断言。可审计是设计出来的，不是事后补的。

## 4.4 Surface 机制：append / replace、sourceEventSeqs 溯源

事件日志里有三类事件会产出模型可见的消息：`user/message`、`assistant/message`、`tool/result`。它们被称为 Surface Event（表面事件）。

Surface（表面）是事件日志之上的一个有序视图——模型看到的对话序列。不是所有事件都在表面上，只有 Surface Event 在。而且 Surface Event 有两种进入方式：

**append（追加）**：添加到表面尾部。正常的用户消息、助手消息、工具结果都是 append。

**replace（替换）**：替换表面上的一个区间。用于 compaction（压缩）——当历史太长需要压缩时，compaction 插件产生一个替换事件，用一个摘要消息替换掉之前的一大段对话。

来看类型定义：

```typescript
// packages/core/session/src/types.ts（节选）
export type SurfaceOp =
  | 'append'
  | { op: 'replace'; start: number; end: number }

export interface SurfaceIntent {
  surfaceOp: SurfaceOp
  /**
   * Complete set of known source-event seqs. assistant/message may use a
   * present empty array for a known empty provider stream.
   */
  sourceEventSeqs?: number[]
}
```

`SurfaceOp` 的两个变体：`'append'` 和 `{ op: 'replace', start, end }`。replace 的 start 和 end 是表面节点的位置（inclusive），被替换的范围必须已存在。

`sourceEventSeqs` 是溯源信息——记录这个表面事件是由哪些源事件产生的。比如 `assistant/message` 的 `sourceEventSeqs` 可能包含产生它的所有 `assistant/chunk` 事件的 seq。这样你可以从一条组装后的消息追溯到它由哪些 token 分片组成。

Surface 的实现代码在 `packages/core/session/src/surface.ts`：

```typescript
// packages/core/session/src/surface.ts（节选）
const SURFACE_EVENT_TYPES = new Set<string>([
  'user/message',
  'assistant/message',
  'tool/result',
])

export function isSurfaceEligibleType(type: string): boolean {
  return SURFACE_EVENT_TYPES.has(type)
}

export function isSurfaceEvent(event: SessionEvent): event is SurfaceEvent {
  if (!SURFACE_EVENT_TYPES.has(event.type)) return false
  return (event as SessionEvent<SurfaceEventType>).surfaceOp !== undefined
}

export function isAppendSurfaceEvent(
  event: SessionEvent,
): event is SurfaceEvent & { surfaceOp: 'append' } {
  return isSurfaceEvent(event) && event.surfaceOp === 'append'
}
```

三个函数分别判断：事件类型是否 eligible（有资格上表面）、事件是否真的是 Surface Event（类型对且有 surfaceOp 标记）、事件是否是 append 来源的 Surface Event。

代码注释里有一段重要的设计说明：

> The model-visible surface deliberately shadows replaced ranges, so it is the wrong source for a human transcript — a landed replacement would erase conversation the user already saw. Append-origin events are that transcript's durable source material; replacement copies stay model-only.

翻译：模型可见的表面会故意遮蔽被替换的范围（compaction 后旧消息在表面上消失），所以表面不适合做人类可读的对话记录。append 来源的事件才是人类记录的持久源材料；replace 的副本只对模型可见。

这意味着 dsh 区分了两种视图：

| 视图 | 数据来源 | 用途 |
|---|---|---|
| 模型表面 | Surface Event（含 replace） | 派生模型请求的 messages |
| 人类记录 | 所有 append 来源的 Surface Event | UI 展示、transcript 导出 |

> 金句：模型看到的和用户看到的可以不一样。这不是 bug，是 compaction 的必然结果。

## 4.5 从日志派生一切：消息历史、回放、fork、投影、持久化

Session 日志是单一事实源，所有其他视图都从它派生。

### 消息历史派生

`session.deriveMessages()` 从日志投影出模型可见的 messages 数组。它遍历 Surface Event，按 surfaceOp 构建：append 追加到尾部，replace 替换对应区间。最终结果就是模型下一次请求时看到的对话历史。

### 回放

因为 `assistant/chunk` 事件保留了 token 级别的原始分片，你可以精确回放一次流式输出。UI 可以用 chunk 事件做打字机效果，回放时也能逐 token 重现。

### fork

`ctx.sessions.fork(source, boundary?, childSessionId?)` 从一个源会话 fork 出新会话。源会话的事件成为新会话的种子（seed），以 `session/end-seed` 事件标记边界。新会话从种子之后开始追加自己的事件。这种方式不需要深拷贝整个会话——种子事件是共享的，新事件是独立的。

### 投影

dsh 有一组投影包，从日志派生不同维度的信息：

| 包 | 投影内容 |
|---|---|
| session-projection | 消息历史（deriveMessages） |
| session-projection-cache | 投影缓存，避免重复计算 |
| session-stats | 会话统计（turn 数、step 数、token 用量等） |
| session-query | SQL 查询接口（基于 SQLite） |
| session-log-export | 日志导出（transcript 格式） |

### 持久化

dsh 支持两种持久化后端：

| 后端 | 包 | 格式 | 适用场景 |
|---|---|---|---|
| JSONL | session-persistence-jsonl | 每行一个 JSON 事件 | 简单场景、调试 |
| SQLite | session-persistence-sqlite | 关系型数据库 | 生产环境、大日志 |

两者都原样存储事件日志——因为事件已经是 lossless JSON，持久化不需要额外转换。恢复时直接读取事件流，重建内存中的 Session 对象。

`session-checkpoint-policy` 包负责持久化时机。它不在每个事件追加时都写盘（太慢），而是在特定的检查点（比如请求完成后）批量写入。

### 一次完整事件序列的日志回放

来看一个完整的 turn 在日志里长什么样：

```
seq  type              data 摘要
─────────────────────────────────────────────────────────
1    turn/start        { turn: 1 }
2    step/start        { turn: 1, step: 1 }
3    user/message      { source: 'human', content: '帮我读 package.json' }
4    request/header    { reason: 'initial', header: { provider: 'deepseek', model: '...' } }
5    assistant/chunk   { chunk: { type: 'text', text: '好的' } }
6    assistant/chunk   { chunk: { type: 'text', text: '，我来' } }
7    assistant/chunk   { chunk: { type: 'text', text: '读取' } }
8    assistant/chunk   { chunk: { type: 'tool-call', ... } }
9    assistant/message { message: { content: [text, tool-call] }, usage: { ... } }
10   tool/call         { callId: 'c1', name: 'fs_read', arguments: '{"path":"package.json"}' }
11   tool/result       { callId: 'c1', message: { content: [text] } }
12   step/end          { turn: 1, step: 1 }
13   step/start        { turn: 1, step: 2 }
14   user/message      { source: 'tool-result', content: ... }
15   request/header    { reason: 'change', header: { ... } }
16   assistant/chunk   { chunk: { type: 'text', text: '这是' } }
17   assistant/chunk   { chunk: { type: 'text', text: '文件内容' } }
18   assistant/message { message: { content: [text] }, usage: { ... } }
19   step/end          { turn: 1, step: 2 }
20   turn/end          { turn: 1, reason: { kind: 'completed' } }
```

这个日志可以完整回放：从 seq 5-8 的 chunk 可以重建流式输出体验；从 seq 4 和 15 的 header 可以知道每步用了什么模型；从 seq 10-11 可以看到工具调用的完整过程。fork 时，新会话以 seq 20 之后为起点，前面的 20 条事件成为种子。

> 金句：日志不是聊天记录的备份，聊天记录是日志的投影。

## 本章小结

| 要点 | 说明 |
|---|---|
| 设计选择 | append-only 事件日志，而非可变消息数组 |
| SessionEventMap | 定义所有合法事件类型的接口，可扩展 |
| 核心事件 | turn/start/end、step/start/end、user/message、assistant/chunk、assistant/message、tool/call、tool/result |
| 模型可见即已记录 | 运行时不变量：模型看到的一切都能从日志重建 |
| ignorable 字段 | 默认拒绝不认识的事件，安全失败 |
| Surface Event | user/message、assistant/message、tool/result 三类 |
| SurfaceOp | append（追加到尾部）或 replace（替换区间，用于 compaction） |
| sourceEventSeqs | 溯源信息，从表面事件追溯到源事件 |
| 两种视图 | 模型表面（含 replace）vs 人类记录（仅 append） |
| 派生能力 | 消息历史、回放、fork、投影、持久化 |
| 持久化后端 | JSONL（简单）和 SQLite（生产） |
| 种子机制 | fork 的事件以 session/end-seed 标记边界 |

## 下章预告

日志有了，事件定义好了。下一章我们来看驱动这些事件的引擎——agent-loop。一次模型请求里到底藏着多少个事件？turn 和 step 是怎么协作的？工具并发调度是怎么做的？

> 我是怕浪猫，如果你被 append-only 日志的设计圈粉了，点个收藏。你的 agent 项目里历史记录存在哪？评论区聊聊。
>
> 系列进度：4/8 ｜ 下一章：Turn / Step 循环——agent-loop 源码拆解

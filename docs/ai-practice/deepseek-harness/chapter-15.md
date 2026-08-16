# 第15章：上下文压缩与目标管理——长会话的生存策略

> 系列：DeepSeek Harness 源码实战 ｜ 进度 15/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

agent 跑久了，会话日志越来越长。10 万 token 的上下文窗口很快被工具输出塞满——bash 命令的 stdout、文件内容、搜索结果。模型要么看不全、要么看不到关键信息。

dsh 有两个机制解决这个问题：compaction（上下文压缩）把旧对话摘要成精简版本，goal（目标管理）让 agent 在长会话中不丢失目标。两者都是可选能力，都基于会话日志，都不引入额外的持久化存储。

我是怕浪猫，第 15 章。先从 compaction 开始。

## 15.1 compaction Seam：压缩是什么

compaction 是一个能力 Seam，与 bash 一样分为三角色：

| 角色 | 包 | 说明 |
|---|---|---|
| Service Definition | dsh-compaction | ctx.compaction，抽象服务 |
| Service Provider | dsh-compaction-basic | 默认后端，基于 LLM 摘要 |
| Consumer | dsh-command-compact | 面向用户的 /compact 命令 |

来自子系统文档（docs/subsystems/compaction.zh.md）：

> 压缩是可选能力，不属于 agent loop 主干。与 bash 不同，该接口必然依赖 dsh-session 和 dsh-llm：其动词作用于 agent 所有的 Session，而其持久摘要事件使用 ContentBlock 词汇。

compaction 做的事情可以用一句话概括：把会话日志中的一段旧对话替换成一条摘要消息。替换后，模型看到的是摘要而不是原始的冗长对话。

压缩前后对比：

```
压缩前（模型看到的上下文）：
  [user] 帮我重构 auth.ts
  [assistant] 我来分析...（5000 tokens）
  [tool] 文件内容 auth.ts...（8000 tokens）
  [assistant] 我发现三个问题...（3000 tokens）
  [tool] 搜索结果...（6000 tokens）
  [assistant] 修复完成...（4000 tokens）
  总计：26000 tokens

压缩后：
  [user] [压缩摘要] 重构 auth.ts：分析了文件，发现三个类型安全问题，已全部修复。（500 tokens）
  总计：500 tokens
```

## 15.2 compaction 会话事件

compaction 通过声明合并为 SessionEventMap（会话事件映射）扩展三种事件类型。来自文档：

| 事件 | 载荷 | 作用 |
|---|---|---|
| compaction/start | { turn } | 获取日志记录的锁 |
| compaction/summary | { summary, rawOutput?, shadowedRange, ... } | 安全摘要投影 |
| compaction/end | { turn, error? } | 释放锁 |

关键设计：三个事件都只写入日志，绝不进入 surface（模型可见层）。文档原文：

> They record locks, summaries, selected ranges, shadowed event seqs, token counts, and model calls, never entering surface.

摘要本身承载在另一条带有 `surfaceOp: { op: 'replace', start, end }` 的 `user/message` 上——这是摘要压缩执行的唯一 surface 变更。

锁的语义很重要。来自文档：

> 锁括住整个操作：先追加 compaction/start，然后执行摘要生成、写入 compaction/summary 记录与 user/message 替换，最后才追加 compaction/end。

如果操作中途崩溃，日志中会留下 `compaction/start` 而无匹配的 `compaction/end`——一个可检测的遗留锁。文档说明：

> 活动的未匹配 start 会阻塞所有入口点。

这意味着不会有两个 compaction 同时操作同一个会话。

## 15.3 压缩触发与策略

compaction 有两种触发方式：

| 触发 | 来源 | 时机 |
|---|---|---|
| 自动 | pressure（压力）/ context-overflow（上下文溢出） | agent/pre-step 串行事件中 |
| 手动 | /compact 命令 | 用户显式调用 |

自动触发的两个原因（来自文档）：

```ts
type CompactionTrigger = 'pressure' | 'context-overflow'
```

`pressure`：常规压力策略，基于 token 估算。`context-overflow`：上下文溢出，可能强制压缩即使未达到正常阈值。

CompactionEngine 暴露三个方法（来自文档）：

```
compactIfNeeded(agent, trigger, signal)  -- 自动策略
compactNow(agent, signal)                 -- 手动，空闲会话
compactRegion(...)                        -- 显式范围
```

`compactNow()` 在轮次之间的 agent maintenance（维护期）运行。没有有效范围时返回 `null` 且不写入——不浪费资源。

文档说明了 compaction-basic 的策略链：

```
1. 检查压力或规范化溢出是否满足条件
2. 调用可选的 ctx.toolResultPruner（工具结果剪枝）
3. 通过 ctx.tokenMeter 重新测量
4. 可以在不生成摘要的情况下推进 surface（仅剪枝）
5. 如果仍需压缩，选择范围生成摘要
```

工具结果剪枝（compaction-tool-result-pruner）是一个可选的中间步骤——先尝试裁剪冗长的工具输出，如果裁剪后仍超限才做完整摘要。来自文档的类型定义：

```ts
interface PrunedEntry {
  readonly originalSeq: number     // 被替换的原始事件 seq
  readonly replacementSeq: number  // 新追加的剪枝事件 seq
  readonly callId: CallId          // 工具调用 id
  readonly charsBefore: number     // 原始文本大小（Unicode code points）
  readonly charsAfter: number      // 替换后文本大小
}
```

> 金句：压缩不是一刀切——先剪枝工具输出，不够再摘要对话。渐进式的，最小化信息损失。

## 15.4 CompactionResult 与 shadowed 机制

成功压缩返回 CompactionResult（来自文档）：

```ts
interface CompactionResult {
  readonly compactionId: CompactionId       // 稳定身份
  readonly sourceCommandId?: CommandId      // 手动命令 id
  readonly startSeq: number                 // compaction/start 的 seq
  readonly summarySeq: number              // compaction/summary 的 seq
  readonly endSeq: number                  // compaction/end 的 seq
  readonly summary: ContentBlock[]          // 摘要内容块
  readonly shadowedRange: { start: number; end: number }  // 被遮蔽的 surface 边界对
  readonly shadowedSeqs: number[]           // 被遮蔽的所有 seq
  readonly shadowedTokenCount: number       // 估算 token 数
}
```

`shadowedRange` 是 surface 位置跨度，不是数值区间。文档解释了一个微妙的情况：

> After a prior replace lands a fresh high-seq summary node at an older range's position, start can be GREATER than end.

这是因为 surface replacement（surface 替换）会把新节点放在旧范围的位置——新节点的 seq 更高但位置更早。`shadowedSeqs` 是权威的被遮蔽节点集合，按 surface 顺序排列。

被遮蔽（shadowed）的对话不会从日志中删除——它们仍在日志中，但不进入模型可见的 surface。这意味着压缩是可逆的：理论上可以取消遮蔽恢复原始对话。

## 15.5 手动压缩的失败处理

手动压缩有预期的失败类别（来自文档）：

```ts
type ManualCompactionErrorCode =
  | 'busy'        // 会话忙碌
  | 'cancelled'   // 被取消
  | 'changed'     // surface 已变更
  | 'summary'     // 摘要生成失败
  | 'commit'      // 提交失败
  | 'persistence' // 持久化失败
```

文档说明了每种失败的状态影响：

| 错误码 | surface 影响 | 日志影响 |
|---|---|---|
| busy | 不变 | 不变 |
| cancelled | 不变 | 清理后抛 abort 原因 |
| changed | 不变 | 闭合失败尝试并持久化 |
| summary | 不变 | 闭合失败尝试并持久化 |
| commit | 可能部分变更 | 闭合尝试 |
| persistence | 内存标记已闭合 | flush 失败 |

`changed` 和 `summary` 会闭合失败尝试并持久化到日志——即使失败了也有记录。`persistence` 表示内存中的标记对已闭合但 flush 失败——内存状态正确但持久化可能缺失。

## 15.6 goal Seam：持久化目标

goal（目标）服务让 agent 在长会话中保持对目标的追踪。来自子系统文档（docs/subsystems/goal.zh.md）：

> 事件溯源目标服务及其策略消费方共享的类型。目标领域负责持久化与激活决策。

Goal 的生命周期阶段（来自文档）：

```ts
type GoalPhase = 'active' | 'paused' | 'blocked' | 'complete'
```

| 阶段 | 含义 |
|---|---|
| active | 正在进行 |
| paused | 暂停（可恢复） |
| blocked | 因问题而停止 |
| complete | 完成 |

`blocked` 是唯一表示「因问题而停止」的持久状态。阻塞原因（来自文档）：

```ts
interface GoalBlockReason {
  readonly code: string    // 稳定的 lower-kebab-case 分类
  readonly message: string // 人类和模型可读的说明
}
```

完整的 Goal 状态（来自文档）：

```ts
interface GoalSnapshot extends GoalRef {
  readonly objective: string          // 人类请求的完成目标
  readonly phase: GoalPhase           // 持久生命周期阶段
  readonly blockedReason?: GoalBlockReason  // 仅 blocked 时存在
  readonly maxGoalRounds: number      // 允许的最大 round 数
}
```

GoalRef（来自文档）是 compare-and-set（比较并交换）身份：

```ts
interface GoalRef {
  readonly id: GoalId       // 稳定身份
  readonly revision: number // 正数修订号，每次持久变更递增
}
```

每次获准的持久变更都会递增 revision——这是乐观锁，防止并发修改冲突。

## 15.7 Goal 变更与会话事件

每次 goal 变更都是持久的 `goal/change` 会话事件。来自文档：

```ts
interface GoalSnapshotChangeMeta {
  readonly kind: 'goal/change'
  readonly version: 1
  readonly operation: Exclude<GoalOperation, 'clear'>
  readonly goal: GoalSnapshot
  readonly roundsStarted: number
  readonly createdAt: number
  readonly updatedAt: number
}
```

清除操作携带墓碑（来自文档）：

```ts
interface GoalClearChangeMeta {
  readonly kind: 'goal/change'
  readonly version: 1
  readonly operation: 'clear'
  readonly cleared: GoalRef
  readonly clearedAt: number
}
```

关键设计：goal 状态只从 `goal/change` 事件派生，inbox 变更不影响 goal 状态。这意味着 goal 的生命周期与消息队列解耦——即使 inbox 中有未处理的消息，goal 状态也不变。

续跑消费方为每个获准的 user/message（用户消息）轮次标注正数且连续的 Round 编号（来自文档）：

```ts
interface GoalMessageSource {
  readonly kind: 'goal'
  readonly goalId: GoalId
  readonly revision: number
  readonly round: number  // 正数获准的续跑 round
}
```

回放时的校验规则（来自文档）：

> 回放会拒绝非正数 Round、编号缺口、陈旧修订号、已停止阶段和超出上限。

这保证了日志的完整性——任何损坏的 goal round 序列都会在回放时被发现。

## 15.8 goal-round-driver：续跑驱动

goal-round-driver 是 goal 的策略消费方。它的工作流：

```
用户设定目标
  |
  v
goal 创建（phase: active）
  |
  v
goal-round-driver 启动 Round 1
  |-- agent 跑一个完整轮次
  |-- 轮次结束
  |-- 检查 goal 是否完成
  |   |-- complete -> 标记完成
  |   |-- blocked -> 标记阻塞
  |   |-- active && roundsStarted < maxGoalRounds -> 启动 Round 2
  |   |-- active && roundsStarted >= maxGoalRounds -> 标记阻塞（超出上限）
  |
  v
等待用户输入或继续
```

goal-round-driver 在 agent/turn-stopping serial 事件中检查是否应该续跑。如果 goal 仍 active 且未达上限，它返回非 null 值注入续跑消息——让 agent 继续工作。

这个过程的关键：goal 状态持久化在会话日志中。即使进程重启，冷恢复后 goal 状态仍能从日志重建——agent 不会忘记自己的目标。

> 金句：goal 不是 todo list（待办清单），是事件溯源的状态机。每次变更都有日志记录，每次恢复都从日志重建——goal 的生命力来自会话日志，不来自进程内存。

## 15.9 compaction 与 goal 的协作

两个系统协作处理长会话：

| 场景 | compaction 的作用 | goal 的作用 |
|---|---|---|
| 长对话上下文溢出 | 压缩旧对话 | 保持目标不丢失 |
| 多轮目标续跑 | 压缩早期 round | 记录 round 编号和进度 |
| 进程重启恢复 | 从日志重建 surface | 从日志重建 goal 状态 |
| 阻塞后恢复 | 压缩阻塞期间的无用对话 | 恢复 goal 到 active |

compaction 压缩时不会触碰 goal/change 事件——goal 事件不在 surface 层，不会被 shadowed（遮蔽）。这意味着即使对话被压缩成摘要，goal 状态仍然完整保留在日志中。

## 15.10 防御性模式：异步状态管理

dsh 防御性模式文档（docs/defensive-patterns.zh.md）的规则 3 与 compaction 和 goal 直接相关：

> 异步状态不是同步状态。agent.followup 无逐消息完成状态、后台完成与轮次边界竞争、reader.close 在 EOF 与 dispose 都触发。

对 compaction 和 goal 的启示：

| 风险 | 规则 |
|---|---|
| compaction 进行中 goal 变更 | 锁机制保证串行 |
| goal round 与 compaction 竞争 | compaction 在 pre-step 串行运行 |
| 进程重启时 compaction 未完成 | 遗留锁可检测，冷恢复时忽略 |
| goal 状态与内存不一致 | 从日志重建，不信任内存 |

## 本章小结

| 要点 | 说明 |
|---|---|
| compaction 三角色 | Definition（dsh-compaction）/ Provider（dsh-compaction-basic）/ Consumer（command-compact） |
| 三种事件 | compaction/start（锁）/ summary（摘要）/ end（释放锁） |
| 触发方式 | 自动（pressure/context-overflow）/ 手动（/compact） |
| 渐进压缩 | 先剪枝工具输出，不够再摘要 |
| shadowed 机制 | 旧对话遮蔽不删除，可逆 |
| 手动失败处理 | 6 种错误码，失败也有日志记录 |
| goal 四阶段 | active / paused / blocked / complete |
| goal 事件溯源 | 状态从 goal/change 事件派生 |
| goal-round-driver | 续跑驱动，与 turn-stopping 协作 |
| 协作 | compaction 不触碰 goal 事件，goal 状态完整保留 |

> 我是怕浪猫，第 15 章写完。compaction 和 goal 是 dsh 长会话的生存策略——压缩让上下文不爆，目标让 agent 不迷路。
>
> 有问题评论区聊，有纠错欢迎指出。如果这篇对你有帮助，收藏起来——设计长会话 agent 时这张机制表最好用。
>
> 下一章是系列收官：如何构建你自己的 dsh 发行版——从 profile 定制到生产部署。
>
> 系列进度：15/16 ｜ 未完待续

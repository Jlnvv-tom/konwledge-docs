# 第11章：事件系统与拦截扩展——用好 Cordis 的五把钥匙

> 系列：DeepSeek Harness 源码实战 ｜ 进度 11/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

插件注册了工具，工具能跑了。但 dsh 的扩展能力远不止「注册工具」——事件系统才是真正的深度扩展入口。

Cordis 提供五种事件分发模式：emit、waterfall、serial、parallel、bail。每种模式的语义不同，适用场景不同，用错了要么静默失效、要么死锁。这一章把五把钥匙一次讲透，然后用真实事件做实战拦截器。

我是怕浪猫，这是系列第 11 章。我们先从五把钥匙的对比开始。

## 11.1 五种分发模式对比

Cordis Primer（docs/cordis-primer.md）定义了四种模式，加上 API 文档中的 bail（docs/cordis-api/events.md），一共五种：

| 模式 | 调用方式 | 是否 await | 执行顺序 | 返回值 | 语义 |
|---|---|---|---|---|---|
| emit | ctx.emit(name, ...args) | 否 | 注册顺序 | 无 | 同步广播 |
| waterfall | ctx.waterfall(name, ...args, next) | 否 | 注册顺序 | 有 | 环绕中间件 |
| parallel | await ctx.parallel(name, ...args) | 是 | 并发 | 无 | 并行 fan-out |
| serial | await ctx.serial(name, ...args) | 是 | 注册顺序 | 有 | 有序 bailing |
| bail | ctx.bail(name, ...args) | 否 | 注册顺序 | 有 | 同步 bailing |

dispatch mode（分发模式）是事件契约的一部分，不是实现细节。每个事件在声明时确定自己的模式，消费方必须按模式编写监听器。dsh 用 @mode 标签标注事件模式，生成文档时会交叉校验。

API 文档的签名（docs/cordis-api/events.md）：

```ts
// emit：同步广播，不收集返回值
emit<K extends keyof Events>(name: K, ...args: Parameters<Events[K]>): void

// parallel：并发执行所有监听器，await 全部完成
parallel<K extends keyof Events>(name: K, ...args: Parameters<Events[K]>): Promise<void>

// serial：按序 await，第一个非 null/false/undefined 的返回值胜出
serial<K extends keyof Events>(name: K, ...args): Promisify<ReturnType<Events[K]>>

// bail：同步版 serial
bail<K extends keyof Events>(name: K, ...args): ReturnType<Events[K]>

// waterfall：环绕中间件，每个监听器收到 ...args + next
waterfall<K extends keyof Events>(name: K, ...args): ReturnType<Events[K]>
```

怎么选？一句话决策树：

```
需要返回值？
  是 -> 需要中间件语义？
    是 -> waterfall
    否 -> serial（async）或 bail（sync）
  否 -> 需要并发？
    是 -> parallel
    否 -> emit
```

> 金句：五种模式不是五种便利函数，是五种不同的协作契约。选错模式，监听器要么拿不到返回值、要么死锁。

## 11.2 emit：同步广播

emit 是最简单的模式。所有监听器按注册顺序同步执行，返回值被忽略。

来自教程的例子（docs/cordis-tutorial/04-events.md）：

```ts
import { Service, type Context } from '@deepseek-ai/cordis'

declare module '@deepseek-ai/cordis' {
  interface Context {
    stats: StatsService
  }
  interface Events {
    'stats/report'(name: string, count: number): void
  }
}

export class StatsService extends Service {
  private counts = new Map<string, number>()

  constructor(ctx: Context) {
    super(ctx, 'stats')
  }

  bump(name: string) {
    const next = (this.counts.get(name) ?? 0) + 1
    this.counts.set(name, next)
    this.ctx.emit('stats/report', name, next)
  }
}
```

监听端：

```ts
ctx.on('stats/report', (name, count) => {
  console.log(`[stats] ${name} -> ${count}`)
})
```

emit 的适用场景：

| 场景 | 说明 |
|---|---|
| 通知/广播 | 某事发生了，不关心谁在听、听到后做什么 |
| 状态更新 | 通知各组件状态已变 |
| 日志/审计 | 记录事件发生 |

dsh 中的 emit 事件举例（来自 docs/event-producer-consumer.zh.md）：

| 事件 | 派发方 | 监听方 |
|---|---|---|
| agent/created | agent | agent-presets, goal-round-driver, schedule |
| session/created | session | compaction, goal, permission-presets, tools, user-approval |
| tools/result | tools | agent-instructions, subagent-in-process-driver |
| session/event | session | 20+ 个包监听 |

注意 session/event 有 20+ 个监听方——这是 dsh 的核心事件，几乎所有需要感知会话变化的插件都监听它。

## 11.3 waterfall：环绕中间件

waterfall 是 dsh 最重要的事件模式。工具执行流水线的三个关键事件——tools/pre-execute、tools/execute、tools/post-execute——全是 waterfall。

教程的 waterfall 演示（docs/cordis-tutorial/04-events.md）：

```ts
declare module '@deepseek-ai/cordis' {
  interface Events {
    'demo/transform'(input: string, next: () => Promise<string>): Promise<string>
  }
}

export function apply(ctx: Context) {
  // 监听器 1：包装下游结果
  ctx.on('demo/transform', async (input, next) => {
    const downstream = await next()
    return downstream.toUpperCase()
  })

  // 监听器 2：条件短路
  ctx.on('demo/transform', async (input, next) => {
    if (input.includes('blocked')) return '** blocked **'
    return next()
  })

  void (async () => {
    console.log(await ctx.waterfall('demo/transform', 'hello', async () => 'hello'))
    console.log(await ctx.waterfall('demo/transform', 'blocked words', async () => 'blocked words'))
  })()
}
```

运行结果：

```
HELLO
** BLOCKED **
```

执行流程图解（第一次调用，input='hello'）：

```
ctx.waterfall('demo/transform', 'hello', defaultFn)
  |
  v
监听器 1：(input='hello', next=...)
  调用 next() ->
    |
    v
    监听器 2：(input='hello', next=...)
      调用 next() ->
        |
        v
        defaultFn() 返回 'hello'
      返回 'hello'（原样传递）
    <--
  返回 'hello'.toUpperCase() = 'HELLO'
<--
```

第二次调用（input='blocked words'）：

```
监听器 1：(input='blocked words', next=...)
  调用 next() ->
    |
    v
    监听器 2：(input='blocked words', next=...)
      检测到 'blocked'
      return '** blocked **'（不调 next，短路）
    <--
  返回 '** BLOCKED **'.toUpperCase()
<--
（defaultFn 从未执行）
```

> 金句：waterfall 的 next() 不是可选的——只观察不拦截的监听器必须调它。忘调 next() 不会报错，只会静默吞掉所有下游行为。

教程的警告（docs/cordis-tutorial/04-events.md）：

> a waterfall listener that only observes or annotates must call next(); returning without it is a deliberate short-circuit. Forgetting next() in a logging listener silently swallows the default behavior for everyone downstream.

Cordis Primer 的补充（docs/cordis-primer.md）：

> Use prepend: true only when the listener must run before ordinary registrations.

prepend: true 让监听器插队到链头，在其他普通注册的监听器之前执行。

## 11.4 serial 和 bail：有序 bailing

serial 是异步有序 bailing，bail 是同步有序 bailing。监听器按注册顺序执行，第一个返回非 null/false/undefined 的监听器胜出，后续监听器不执行。

API 文档（docs/cordis-api/events.md）：

```ts
// serial：异步有序，第一个 bail 值胜出
serial<K extends keyof Events>(name: K, ...args): Promisify<ReturnType<Events[K]>>

// bail：同步有序，第一个 bail 值胜出
bail<K extends keyof Events>(name: K, ...args): ReturnType<Events[K]>
```

dsh 中的 serial 事件：agent/turn-stopping（来自事件矩阵）。当 agent 即将停止当前轮次时，serial 事件让监听器有机会注入续跑消息。

serial 和 waterfall 的区别：

| 维度 | waterfall | serial |
|---|---|---|
| 中间件语义 | 有 next()，可包装结果 | 无 next()，返回值即终值 |
| 短路方式 | 不调 next() | 返回非 null/false/undefined |
| 返回值来源 | 最内层 default 或包装后的值 | 第一个 bail 的监听器 |
| 典型用途 | 拦截/转换流水线 | 决策/投票 |

bail 和 serial 的区别仅在同步/异步：

| 维度 | bail | serial |
|---|---|---|
| 是否 await | 否 | 是 |
| 监听器可否 async | 不行 | 可以 |

## 11.5 parallel：并行 fan-out

parallel 让所有监听器并发执行，await 全部完成。返回值被忽略。

API 文档（docs/cordis-api/events.md）：

```ts
parallel<K extends keyof Events>(name: K, ...args: Parameters<Events[K]>): Promise<void>
```

dsh 中的 parallel 事件：session/flush（来自事件矩阵）。当会话需要刷盘时，所有持久化相关插件并发执行刷盘操作。

```
session/flush (parallel)
  |-- session-persistence -> 写 JSONL/SQLite
  |-- session-telemetry -> 发送遥测数据
```

两个操作互不依赖，parallel 让它们并发执行，总耗时等于最慢的那个。

## 11.6 类型化事件声明

Cordis 用 TypeScript 声明合并给事件加类型。声明位置在 interface Events 里（docs/cordis-tutorial/04-events.md）：

```ts
declare module '@deepseek-ai/cordis' {
  interface Events {
    // emit 事件：返回 void
    'stats/report'(name: string, count: number): void
    // waterfall 事件：最后一个参数是 next
    'demo/transform'(input: string, next: () => Promise<string>): Promise<string>
    // serial/bail 事件：返回值用于 bailing
    'some-check'(input: string): boolean | undefined
  }
}
```

消费方需要 import 声明文件才能拿到类型。通常通过 `import '@deepseek-ai/dsh-tools'` 或 `import type {} from './stats.ts'` 拉入声明合并。

> 金句：声明合并不是可选的类型装饰，是事件系统的编译时契约。没有它，ctx.emit 和 ctx.on 的参数类型是 any——运行时不报错，但 IDE 提示全废。

## 11.7 实战：权限拦截器

用 waterfall 写一个真实的权限拦截器。监听 tools/pre-execute，按工具名和参数决定 allow/deny/ask。

参考 docs/cookbook/adding-a-tool.md 中的说明：

> Prefer not to build deployment policy into the tool. Use tools/pre-execute for extensible allow/deny/ask policy.

tools/pre-execute 是 waterfall 事件，监听器返回 PreToolDecision 决定是否放行。

```ts
import type { Context } from '@deepseek-ai/cordis'
import '@deepseek-ai/dsh-tools'

export const name = 'my-permission-gate'
export const inject = ['tools']

export function apply(ctx: Context) {
  // 禁止写入系统目录
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (exec.name === 'write_file' || exec.name === 'edit_file') {
      const path = exec.arguments?.path as string
      if (path && (path.startsWith('/etc/') || path.startsWith('/sys/'))) {
        return { kind: 'deny' as const, reason: 'System directories are read-only' }
      }
    }
    // 其他情况委托下游
    return next()
  })

  // 对 bash 命令做关键词过滤
  ctx.on('tools/pre-execute', async (exec, next) => {
    if (exec.name === 'bash') {
      const command = exec.arguments?.command as string
      // 拦截危险命令模式
      if (command && /rm\s+-rf\s+\//.test(command)) {
        return { kind: 'deny' as const, reason: 'Recursive root deletion is blocked' }
      }
    }
    return next()
  })
}
```

两个监听器串成链：

```
tools/pre-execute waterfall
  |-- 监听器 1：文件路径检查
  |     匹配 /etc/ 或 /sys/ -> deny
  |     其他 -> next()
  |-- 监听器 2：bash 命令检查
  |     匹配危险模式 -> deny
  |     其他 -> next()
  |-- default：allow
```

第一个返回 deny 的监听器短路整条链——后续监听器和 default 都不执行。如果都调了 next()，default 返回 allow。

## 11.8 实战：结果裁剪器

tools/post-execute 也是 waterfall 事件，可以替换工具返回的内容。适用于敏感信息脱敏、长结果截断等场景。

```ts
import type { Context } from '@deepseek-ai/cordis'
import '@deepseek-ai/dsh-tools'

export const name = 'result-sanitizer'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.on('tools/post-execute', async (exec, result, next) => {
    // 对 bash 输出做 API key 脱敏
    if (exec.name === 'bash') {
      const sanitized = result.content.map(block => {
        if (block.type === 'text') {
          return {
            ...block,
            text: block.text
              .replace(/[A-Za-z0-9]{32,}/g, '[REDACTED]')
              .replace(/sk-[A-Za-z0-9]+/g, '[API_KEY_REDACTED]')
          }
        }
        return block
      })
      return { ...result, content: sanitized }
    }
    return next()
  })
}
```

post-execute 的决策类型（来自 docs/cookbook/adding-a-tool.md）：

| 决策 | 说明 |
|---|---|
| accept | 接受原结果（调 next()） |
| replace | 用新内容替换模型可见的 content |
| enrich | 在原结果后追加额外上下文 |
| block | 阻断结果，模型收到错误 |

教程原文的说明：

> tools/post-execute - accept/block/replace/add context - A content replacement leaves programmatic access to value intact; confidentiality policy blocks or replaces the value.

注意：replace 只改模型可见的 content，不改程序化访问的 canonical value。如果要做真正的敏感信息阻断，需要用 block。

## 11.9 实战：轮次续跑注入器

agent/turn-stopping 是 serial 事件。当 agent 即将停止当前轮次时，监听器可以返回非 null 值阻止停止，注入续跑消息。

```ts
import type { Context } from '@deepseek-ai/cordis'
import '@deepseek-ai/dsh-agent-loop'

export const name = 'auto-continue'
export const inject = ['agents']

export function apply(ctx: Context) {
  ctx.on('agent/turn-stopping', async (agent) => {
    // 检查是否有未完成的 todo
    const todos = agent.session?.getTodos?.() ?? []
    const pending = todos.filter(t => t.status === 'pending')
    
    if (pending.length > 3) {
      return {
        kind: 'inject' as const,
        content: `还有 ${pending.length} 个待办事项未完成，请继续。`,
        source: { kind: 'plugin' as const, plugin: 'auto-continue' }
      }
    }
    
    // 返回 null，不阻止停止
    return null
  })
}
```

serial 的 bailing 语义：第一个返回非 null 的监听器胜出，后续监听器不执行。如果所有监听器都返回 null，agent 正常停止。

dsh 中 agent/turn-stopping 的监听方（来自事件矩阵）：

| 监听方 | 作用 |
|---|---|
| hooks-claude-code | 桥接 Claude Code 的停止钩子 |
| hooks-codex | 桥接 Codex 的停止钩子 |

你可以加自己的监听器，和 hooks 串成有序决策链。

> 金句：emit 是大喇叭，waterfall 是流水线，serial 是投票表，parallel 是并发扇出，bail 是同步投票。五把钥匙，五种协作方式——选对了，代码自然清晰。

## 11.10 dsh 核心事件速查

从事件矩阵（docs/event-producer-consumer.zh.md）摘录最常用的事件：

| 事件 | 模式 | 用途 |
|---|---|---|
| tools/pre-execute | waterfall | 权限拦截、审计前置 |
| tools/execute | waterfall | 超时、重试、metrics 包装 |
| tools/post-execute | waterfall | 结果裁剪、脱敏、追加上下文 |
| tools/result | emit | 观察最终结果（不可改） |
| agent/pre-step | waterfall | 步骤前注入上下文 |
| agent/request | waterfall | 改写模型请求配置 |
| agent/turn-stopping | serial | 阻止停止、注入续跑 |
| llm/stream | waterfall | 包装模型流式输出 |
| session/event | emit | 观察所有会话事件 |
| system-prompt/assemble | waterfall | 改写系统提示 |

每个事件的模式决定了你能怎么用它：

| 你想做什么 | 用什么事件 | 什么模式 |
|---|---|---|
| 禁止某个工具调用 | tools/pre-execute | waterfall（return deny） |
| 截断工具输出 | tools/post-execute | waterfall（return replace） |
| 记录工具调用日志 | tools/result | emit |
| 注入系统提示内容 | system-prompt/assemble | waterfall |
| 阻止 agent 停止 | agent/turn-stopping | serial（return 非 null） |
| 观察会话事件 | session/event | emit |
| 包装模型流 | llm/stream | waterfall |

## 本章小结

| 模式 | 调用 | 返回值 | 短路方式 | 典型用途 |
|---|---|---|---|---|
| emit | ctx.emit | 无 | 无 | 广播通知 |
| waterfall | ctx.waterfall + next | 有 | 不调 next() | 拦截流水线 |
| serial | await ctx.serial | 有 | 返回非 null/false/undefined | 异步决策 |
| bail | ctx.bail | 有 | 返回非 null/false/undefined | 同步决策 |
| parallel | await ctx.parallel | 无 | 无 | 并发 fan-out |

| 实战拦截器 | 事件 | 模式 | 效果 |
|---|---|---|---|
| 权限拦截器 | tools/pre-execute | waterfall | deny 危险操作 |
| 结果脱敏器 | tools/post-execute | waterfall | 替换敏感内容 |
| 轮次续跑器 | agent/turn-stopping | serial | 注入续跑消息 |

> 我是怕浪猫，第 11 章写完。五种模式、三个实战拦截器，覆盖了 dsh 事件系统 80% 的使用场景。
>
> 有问题评论区聊，有纠错欢迎指出。如果这篇对你有帮助，收藏起来——写拦截器时这张速查表最好用。
>
> 下一章是系列的收官：用 Seam 三段式从零设计一个可替换的能力。
>
> 系列进度：11/12 ｜ 未完待续

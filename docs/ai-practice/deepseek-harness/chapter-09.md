# 第9章：插件原理深度剖析——Cordis 框架的核心机制

> 系列：DeepSeek Harness 源码实战 ｜ 进度 9/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

八章走完，dsh 的骨架和肌肉你都见过了。但从头到尾有个东西一直在背后默默驱动一切——Cordis 框架。它是 dsh 的插件引擎，是一切皆插件这句话的底层支撑。

这一章我们潜入 Cordis 的内部机制，把插件的三种形态、Fiber（纤维）状态机、effect（副作用）生命周期、ctx（上下文）服务容器这四个核心概念彻底拆透。理解了这些，你才能写出正确的插件，才能在插件不工作时知道去哪里查。

我是怕浪猫，这是系列的第 9 章。我们从插件的最小单元开始。

## 9.1 插件的三种形态

Cordis 接受三种插件形态：函数、对象、类。三种形态本质上做同一件事——提供一个 `apply(ctx)` 方法，Cordis 加载插件时调用它，插件在 `apply` 里注册自己贡献的所有内容。

来看 Cordis 教程里的定义（`docs/cordis-tutorial/01-first-plugin.md`）：

```ts
import { Service, type Context } from '@deepseek-ai/cordis'

// 1. Function plugin：直接导出 apply 函数
export function apply(ctx: Context) {}

// 2. Object plugin：带 apply 方法的对象
export const objectPlugin = {
  name: 'object-plugin',
  apply(ctx: Context) {},
}

// 3. Class plugin：Service 子类
export class MyService extends Service {
  constructor(ctx: Context) {
    super(ctx, 'myTutorialService')
  }
}
```

三种形态怎么选？规则很简单：

| 形态 | 适用场景 | 特点 |
|---|---|---|
| 函数 | 不需要提供服务的插件 | 最简洁，一个 apply 函数搞定 |
| 对象 | 需要显式 name 但不需要类 | 少用，函数形态加 name 导出即可替代 |
| 类 | 需要提供服务（ctx.xxx） | Service 子类，注册为命名服务 |

> 金句：函数是插件的原子形态，类是服务的载体。写工具用函数，写能力用类——这是 dsh 的惯例。

来看一个真实例子。dsh 的工具注册插件通常用函数形态（`docs/cordis-tutorial/07-into-the-harness.md`）：

```ts
// 来自 docs/cordis-tutorial/07-into-the-harness.md
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { CallId } from '@deepseek-ai/dsh-llm'

export const name = 'greet-tool'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'greet',
    description: 'Greet the named person.',
    parameters: {
      name: { type: 'string', required: true, description: 'Who to greet' },
    },
    output: {
      schema: { type: 'string' },
      render: (_args, value) => [{ type: 'text', text: value }],
    },
    async execute(args) {
      return `Hello, ${args.name}!`
    },
  }))
}
```

注意三个关键点：`name` 是诊断用的显示元数据，`inject` 声明依赖的服务，`apply` 是插件体。这个插件不需要提供服务，只注册工具，所以用函数形态就够了。

而需要提供服务的插件用类形态，比如 LLM 适配器（`docs/user/develop/practice/llm-adapter.md`）：

```ts
import { LlmAdapter, type GenerateOptions, type StreamChunk } from '@deepseek-ai/dsh-llm'

class MyAdapter extends LlmAdapter {
  async *stream(options: GenerateOptions): AsyncIterable<StreamChunk> {
    // 转发请求到 provider API，把响应转成 StreamChunk
  }
}

export const name = 'my-llm-adapter'
export const inject = ['llm']

export function apply(ctx: Context, config: Config) {
  const adapter = new MyAdapter(config.apiKey)
  ctx.llm.registerAdapter(config.providers, adapter)
}
```

这里 `MyAdapter` 是 `LlmAdapter` 的子类（`LlmAdapter` 继承自 `Service`），但插件入口仍是函数——类用在了需要实现抽象接口的地方，函数用在了插件入口。

## 9.2 Fiber 状态机：插件的生命周期

每个加载的插件实例拥有一个 Fiber——运行时句柄，跟踪插件的状态、配置和注册的 effect。

Fiber 的状态流转（`docs/cordis-tutorial/02-lifecycle-and-effects.md`）：

```
PENDING → LOADING → ACTIVE → UNLOADING → DISPOSED
                 ↘ FAILED
```

每个状态的含义：

| 状态 | 含义 | 何时进入 |
|---|---|---|
| PENDING | 等待依赖服务就绪 | 插件被声明但 inject 的服务尚未可用 |
| LOADING | 正在执行 apply | 依赖就绪，开始加载 |
| ACTIVE | apply 执行完毕 | 插件正常运行中 |
| FAILED | apply 或配置校验抛出异常 | 加载失败 |
| UNLOADING | 正在执行清理 | 被卸载、热替换或依赖消失 |
| DISPOSED | 清理完成 | 所有 disposer 执行完毕 |

PENDING 是最容易被忽略的状态。教程里有一段专门的诊断说明：

> `inject: ['timer']` has no provider. Add `- name: '@deepseek-ai/cordis-plugin-timer'` to the list and the plugin loads. When a plugin does nothing and reports nothing, inspect its fiber state.

如果你写了一个插件，运行后什么也没发生、也没报错——大概率是 PENDING 了。它的 `inject` 声明了某个服务，但没有人提供这个服务。Cordis 不会报错，因为 PENDING 是合法状态——服务可能稍后被挂载。

来看教程里的诊断代码（`docs/cordis-tutorial/06-composition-and-hmr.md`）：

```ts
import { FiberState, type Context } from '@deepseek-ai/cordis'

export const name = 'diagnose'

export function apply(ctx: Context) {
  setTimeout(() => {
    for (const runtime of ctx.registry.values()) {
      for (const fiber of runtime.fibers) {
        if (fiber.state === FiberState.PENDING) {
          console.log(`${fiber.name} is PENDING — a required service is missing`)
        }
      }
    }
  }, 500)
}
```

这个诊断插件遍历注册表，找出所有 PENDING 状态的 Fiber。实际开发中，如果你不确定插件为什么没加载，写一个类似的诊断器是第一步。

> 金句：PENDING 不是 bug，是设计。但如果你的插件应该加载却没加载，PENDING 就是线索。

Fiber 的另一个重要特性：依赖追踪是动态的。如果插件 A 依赖服务 X，服务 X 的 Provider 被卸载时，插件 A 也会被自动卸载；服务 X 重新出现时，插件 A 会重新加载。教程原文（`docs/cordis-tutorial/03-services.md`）：

> `inject` is not a one-shot boot check. If a required service disappears while the app runs — its provider was unloaded or hot-replaced — every dependent plugin is unloaded too, and loads again when the service returns.

这意味着热替换 Provider 是安全的——所有依赖它的插件会自动重启，不需要手动协调。

## 9.3 Effect 生命周期：注册即清理

Cordis 的核心设计原则之一：所有注册都是可逆的副作用（reversible effects）。插件注册的监听器、工具、服务，在插件卸载时自动清理。

来看 Cordis API 文档的定义（`docs/cordis-api/fiber.md`）：

```ts
// ctx.effect 注册一个 effect：
// execute 立即执行，返回的 disposer 在卸载时执行
effect(execute: () => SyncEffect, label?: string): Disposable<Promise<void>>
effect(execute: () => Effect, label?: string): AsyncDisposable<Promise<void>>
```

`ctx.effect()` 的用法（`docs/cordis-tutorial/02-lifecycle-and-effects.md`）：

```ts
import type { Context } from '@deepseek-ai/cordis'

export const name = 'lifecycle-demo'

function heartbeat(ctx: Context) {
  console.log('heartbeat plugin loading')
  ctx.effect(() => {
    const timer = setInterval(() => console.log('tick'), 200)
    return () => {
      clearInterval(timer)
      console.log('heartbeat cleaned up')
    }
  })
}

export function apply(ctx: Context) {
  const fiber = ctx.plugin(heartbeat)
  ctx.effect(() => {
    const timer = setTimeout(async () => {
      await fiber.dispose()
      console.log('disposed')
      process.exit(0)
    }, 700)
    return () => clearTimeout(timer)
  })
}
```

关键点：`ctx.effect()` 的 body 在加载时立即执行，返回的 disposer 在卸载时执行。你永远不需要自己调用 disposer——Cordis 会在正确的时机调它。

但大部分时候你不需要手写 `ctx.effect()`，因为 Cordis 的内置注册 API 已经是 effect 了：

| 注册 API | 自动清理行为 |
|---|---|
| `ctx.on(event, listener)` | 卸载时移除监听器 |
| `ctx.plugin(child)` | 卸载时 dispose 子插件 |
| `ctx.tools.register(...)` | 卸载时注销工具 |
| Service 注册（`super(ctx, name)`） | 卸载时移除服务 |

教程原文（`docs/cordis-tutorial/02-lifecycle-and-effects.md`）：

> You rarely write `ctx.effect()` yourself, because the built-in registration APIs are effects already.

一个需要注意的顺序问题（教程原文）：

> disposers start in reverse registration order, but multiple async disposers run concurrently. If teardown steps must run in sequence, keep them in one disposer and await them there.

翻译：disposer 按注册的逆序启动，但多个异步 disposer 会并发执行。如果清理步骤必须按顺序执行，把它们放在一个 disposer 里。

> 金句：注册是副作用，清理是自动的。这不是便利，是架构约束——因为 HMR（Hot Module Replacement，热模块替换）和依赖追踪都依赖这个保证。

## 9.4 ctx 服务容器：插件的通信枢纽

ctx（Context，上下文）是 Cordis 的核心对象。每个服务、事件、生命周期 API 都通过 ctx 访问。ctx 是一个代理——属性读取经过服务解析器，`extend()`、`isolate()`、`intercept()` 创建作用域子上下文。

来看 Cordis API 文档（`docs/cordis-api/context.md`）：

```ts
// ctx.extend(meta?) — 创建子上下文，继承当前上下文的所有属性
extend(meta = {}): this

// ctx.isolate(name, label?) — 创建子上下文，隔离指定服务
isolate(name: string, label?: symbol)

// ctx.intercept(name, config) — 为服务添加拦截配置
intercept(name: string, config: any): this
```

三个核心操作：

**1. extend**：创建子上下文，添加额外元数据。子上下文原型继承父上下文，不修改父上下文。

**2. isolate**：创建子上下文，隔离指定服务。两个 group 可以各自看到不同配置的同一个服务实现。教程里给出了实际用法（`docs/user/develop/framework/service.md`）：

```yaml
- id: group-a
  name: '@deepseek-ai/cordis-plugin-group'
  group: true
  isolate:
    shell: true
  config:
    - name: '@deepseek-ai/dsh-bash-local'
      config:
        timeoutMs: 5000
    - name: './src/plugin-a.ts'

- id: group-b
  name: '@deepseek-ai/cordis-plugin-group'
  group: true
  isolate:
    shell: true
  config:
    - name: '@deepseek-ai/dsh-bash-local'
      config:
        timeoutMs: 60000
    - name: './src/plugin-b.ts'
```

`plugin-a` 和 `plugin-b` 各自看到自己 group 里的 Bash 实例，互不影响。这在多 agent 场景下很有用——每个 agent 可以有自己的 shell 配置。

**3. intercept**：为服务添加拦截配置。子上下文里的插件会看到合并后的配置。

服务通过 `ctx.<key>` 访问。dsh 注册的核心服务包括（来自 `docs/cordis-primer.md`）：

| 服务名 | 访问方式 | 提供者 |
|---|---|---|
| tools | ctx.tools | dsh-tools |
| llm | ctx.llm | dsh-llm |
| agents | ctx.agents | dsh-agent |
| session | ctx.session | dsh-session |
| shell | ctx.shell | dsh-bash-local / dsh-pwsh-local |
| fs | ctx.fs | dsh-fs-local / dsh-fs-sandbox |
| subprocess | ctx.subprocess | dsh-subprocess-local |
| terminals | ctx.terminals | dsh-pty |

服务名在一个应用里是扁平命名空间。dsh 占用了 `tools`、`llm`、`agents` 等普通名字，你自己的服务应该加前缀或命名空间。

声明服务的 TypeScript 类型需要声明合并（declaration merging，`docs/cordis-tutorial/03-services.md`）：

```ts
import { Service, type Context } from '@deepseek-ai/cordis'

// 编译时类型声明
declare module '@deepseek-ai/cordis' {
  interface Context {
    greeter: GreeterService
  }
}

export class GreeterService extends Service {
  constructor(ctx: Context) {
    super(ctx, 'greeter')  // 运行时注册
  }

  greet(who: string) {
    return `Hello, ${who}!`
  }
}

export const name = 'greeter'

export function apply(ctx: Context) {
  ctx.plugin(GreeterService)
}
```

两个部分协作：`super(ctx, 'greeter')` 在运行时注册服务实例，`declare module` 在编译时给 `ctx.greeter` 加类型。声明合并不产生代码——没有它服务在运行时照样工作，但消费方失去类型安全。

消费方通过 `inject` 声明依赖（同文件）：

```ts
export const name = 'consumer'
export const inject = ['greeter']

export function apply(ctx: Context) {
  console.log(ctx.greeter.greet('world'))
}
```

`inject` 让 Cordis 在服务就绪前保持插件 PENDING。`apply` 运行时，`ctx.greeter` 保证可用。加载顺序不影响——依赖关系决定启动顺序，不是文件中的位置。

可选依赖不用 `inject`，用 `ctx.get()` 在使用点探测：

```ts
export function apply(ctx: Context) {
  const greeter = ctx.get('greeter')
  console.log(greeter?.greet('maybe') ?? 'no greeter available')
}
```

`ctx.get('greeter')` 在没有 Provider 时返回 `undefined`，插件仍然正常运行。

> 金句：inject 是硬依赖——服务不在就不加载。ctx.get 是软依赖——服务不在也能跑，只是功能降级。

## 9.5 插件加载流程：从 cordis.yml 到 apply

把前面的概念串起来，看一个插件从配置到运行的完整流程。

当 dsh 启动时（`docs/cordis-tutorial/01-first-plugin.md`）：

```
1. 启动器创建根 Context，挂载 Loader 插件
2. Loader 读取 cordis.yml，解析每个条目的模块指定符
3. Loader 动态 import 模块，获取导出的 apply/inject/Config 等
4. 对每个条目，Loader 调用 ctx.plugin()，创建 Fiber
5. Fiber 检查 inject 依赖，满足则进入 LOADING
6. Config schema 校验（如果导出了 Config）
7. 调用 apply(ctx, config)，Fiber 进入 ACTIVE
8. apply 中注册的 effect 开始生效
```

配置条目的结构（`docs/cordis-tutorial/06-composition-and-hmr.md`）：

```yaml
- id: greeter          # 稳定标识，HMR 用
  name: './greeter.ts'  # 模块指定符
  config:               # 传给 apply 的配置
    greeting: 'Hello'
  disabled: false       # 跳过挂载但保留条目
```

`id` 的作用：让 Loader 区分「编辑已有条目」和「删除旧的加新的」。没有 `id` 的条目每次读取都生成新 id，配置文件编辑后会被视为删除+新增，导致不必要的重载。

`disabled` 的作用：跳过挂载但保留条目。改回 `false` 就恢复——不需要删除条目。

`config` 的校验（`docs/cordis-tutorial/05-config.md`）：

```ts
import Schema from '@deepseek-ai/schemastery'

export interface Config {
  greeting: string
  targets: string[]
}

export const Config: Schema<Config> = Schema.object({
  greeting: Schema.string().default('Hello'),
  targets: Schema.array(String).default(['world']),
})

export function apply(ctx: Context, config: Config) {
  for (const target of config.targets) {
    console.log(`${config.greeting}, ${target}!`)
  }
}
```

导出的 `Config` 同时是 TypeScript 接口和运行时 schema——消费方拿类型，Cordis 拿校验器。dsh 使用 Schemastery 做 schema 校验。教程明确警告：

> Do not export a plain object as `Config`; it does not implement the Standard Schema interface required by Cordis.

配置校验失败时，Fiber 进入 FAILED 状态，启动器以退出码 1 报错：

```
ValidationError: invalid config:
  - $.targets expected array but got not-an-array (at targets)
```

`!!js` 标签支持计算配置值（`docs/cordis-tutorial/05-config.md`）：

```yaml
- name: './config-demo.ts'
  config:
    greeting: !!js process.env.DEMO_GREETING ?? 'Hello'
```

`!!js` 只在 `config` 字段和 `disabled` 字段中可用。`disabled: !!js ...` 在每次挂载决策时求值，可以按平台或环境门控插件。

## 9.6 HMR 热替换实战

HMR（Hot Module Replacement，热模块替换）是 dsh 开发体验的关键。因为注册是 effect、卸载自动清理，Cordis 可以卸载旧插件实例、加载新实例，不需要重启进程。

教程的 HMR 演示（`docs/cordis-tutorial/06-composition-and-hmr.md`）：

```yaml
- id: logger
  name: '@deepseek-ai/cordis-plugin-logger-console'
- id: timer
  name: '@deepseek-ai/cordis-plugin-timer'
- id: hmr
  name: '@deepseek-ai/cordis-plugin-hmr'
  config:
    root: ['.']
- id: hello
  name: './hello.ts'
```

三个注意点：

| 要点 | 说明 |
|---|---|
| logger 依赖 | HMR 通过 Cordis logger 服务输出日志，没有 console 导出器看不到消息 |
| timer 依赖 | HMR inject 了 timer 服务用于防抖，没有 timer 插件它永远 PENDING |
| id 必须显式 | 没有 id 的条目每次读取生成新 id，配置文件编辑后被误判为删除+新增 |

编辑 `hello.ts` 保存后，HMR 输出：

```
hello from my first plugin
2026-07-22 15:44:36 [I] hmr watching [ '.' ]
2026-07-22 15:44:39 [I] hmr reload plugin at hello.ts
hello from my EDITED plugin
```

旧实例卸载（所有 effect 清理）、新代码加载、apply 重新执行。编辑 `cordis.yml` 本身也会被检测——Loader 按 `id` diff 条目，只挂载、卸载或重新配置变化的部分。

> 金句：HMR 不是魔法，是 effect 清理保证的原子替换。如果注册不是 effect，HMR 就会泄漏——这就是为什么 Cordis 强制所有注册走 effect 机制。

## 9.7 Cordis 五个核心概念总结

Cordis Primer（`docs/cordis-primer.md`）用五句话概括了 Cordis 的核心思想：

| 概念 | 一句话 | 代码体现 |
|---|---|---|
| 插件 | 实现 Service 的对象 | `apply(ctx)` / `Service` 子类 |
| 上下文 | 服务容器 | `ctx.tools` / `ctx.llm` |
| 依赖声明 | inject 等待服务就绪 | `export const inject = ['tools']` |
| 类型化事件 | 声明合并定义事件签名 | `interface Events { 'x/y': ... }` |
| 可逆副作用 | 注册自动清理 | `ctx.on()` / `ctx.effect()` |

这五个概念是写任何 dsh 插件的基础。不管是注册一个工具、监听一个事件、还是实现一个 Provider，都离不开它们。

## 本章小结

| 要点 | 说明 |
|---|---|
| 插件三种形态 | 函数（最常用）、对象（少用）、类（Service 子类） |
| Fiber 六状态 | PENDING / LOADING / ACTIVE / FAILED / UNLOADING / DISPOSED |
| PENDING 诊断 | inject 的服务未被提供，写诊断器遍历 registry 查找 |
| Effect 自动清理 | ctx.on / ctx.plugin / ctx.tools.register 等注册自带 disposer |
| ctx 服务容器 | 通过 `ctx.<key>` 访问，声明合并加类型，inject 声明硬依赖 |
| HMR | 基于 effect 清理的原子替换，需要显式 id 和依赖服务到位 |

> 我是怕浪猫，第九章拆完。Cordis 的插件引擎不复杂，但细节多——PENDING 静默、effect 顺序、id 稳定性，这些坑踩过一次就记住了。
>
> 如果这篇对你有帮助，收藏起来，写插件卡住时翻回来查。有问题评论区聊，有纠错也欢迎指出。
>
> 下一章我们动手写一个完整的 dsh 插件——从工具定义到打包发布。
>
> 系列进度：9/12 ｜ 未完待续

# 第12章：能力 Seam 三段式实战——设计你自己的可替换能力

> 系列：DeepSeek Harness 源码实战 ｜ 进度 12/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

最后一章。前 11 章你学会了 dsh 的架构、会话、循环、工具流水线、插件原理、事件系统。这些是「使用」dsh 的能力。这一章讲「扩展」dsh 的能力——用 Seam（缝合线）三段式设计你自己的可替换能力。

这是 dsh 插件架构的最高层抽象。理解了三段式，你就理解了 dsh 为什么把一个简单的「执行 bash 命令」拆成三个包。

我是怕浪猫，系列收官篇。我们从「为什么不直接写一个工具」开始。

## 12.1 为什么不直接写一个工具

假设你要给 dsh 加一个数据库查询能力。最直接的做法是写一个工具插件，在 execute 里连数据库、跑查询、返回结果。

这能跑。但考虑三个问题：

| 问题 | 单包工具的困境 |
|---|---|
| 换实现 | 从本地 SQLite 换成远程 PostgreSQL，要改工具代码 |
| 加策略 | 想给查询加超时、重试、审计，要改工具代码 |
| 共享能力 | 另一个插件也需要查数据库，只能再写一遍连接逻辑 |

dsh 的解法是把「能力」拆成三个角色，各司其职：

```
Service Definition（服务定义）  -- 接口契约
      |
      +-- Service Provider（服务提供者） -- 具体实现
      |
      +-- Consumer（消费方） -- 面向模型的工具
```

三角色分离后：换实现只改 Provider，加策略用事件拦截，共享能力直接 inject 服务。

> 金句：工具是能力的终端形态，Seam 是能力的生长空间。直接写工具是把树钉在地上，写 Seam 是给树留出移栽的余地。

## 12.2 三角色详解

参考 docs/user/develop/practice/index.md 的概念定义：

**Service Definition（服务定义）**：定义 Cordis 服务和请求/响应类型。是一个抽象类，继承 Service，声明服务名和抽象方法。不包含实现逻辑。

**Service Provider（服务提供者）**：实现 Service Definition 的抽象方法。一个 Definition 可以有多个 Provider，通过 cordis.yml 选择挂载哪个。

**Consumer（消费方）**：把服务能力暴露为模型可调用的工具。依赖 Service Definition，不依赖具体 Provider。

三者的依赖关系：

```
    Service Definition (dsh-my-cap)
         ^              ^
         |              |
    Provider          Consumer
 (dsh-my-cap-local)  (tool-my-cap)
         |              |
         |              |
    不互相依赖      不互相依赖
```

教程原文的关键描述（docs/user/develop/practice/index.md）：

> The Service Provider and Consumer do not depend on each other.

这是三段式的核心约束。Provider 和 Consumer 只依赖 Definition，互相不知道对方存在。换 Provider 不影响 Consumer，换 Consumer 不影响 Provider。

## 12.3 第一步：写 Service Definition

参考 docs/user/develop/practice/index.md 的教程，写一个翻译能力的 Service Definition。

创建包 `dsh-translate/src/index.ts`：

```ts
import { Service, type Context } from '@deepseek-ai/cordis'

// 编译时类型声明
declare module '@deepseek-ai/cordis' {
  interface Context {
    translate: TranslateService
  }
}

// Service Definition：抽象类，定义接口契约
export abstract class TranslateService extends Service {
  constructor(ctx: Context) {
    super(ctx, 'translate')
  }

  /** 翻译文本 */
  abstract translate(request: TranslateRequest): Promise<TranslateResult>
}

// 请求类型
export interface TranslateRequest {
  text: string
  from: string
  to: string
}

// 响应类型
export interface TranslateResult {
  translated: string
  detectedFrom?: string
  confidence?: number
}
```

关键设计点：

| 要素 | 说明 |
|---|---|
| abstract class | Definition 是抽象类，不能直接实例化 |
| super(ctx, 'translate') | 注册服务名为 'translate'，消费方通过 ctx.translate 访问 |
| abstract method | 只声明签名，不写实现 |
| Request/Result 类型 | 导出给 Provider 和 Consumer 使用 |
| declare module | 编译时类型声明，让 ctx.translate 有类型 |

Definition 包的 package.json：

```json
{
  "name": "@my-org/dsh-translate",
  "version": "0.1.0",
  "type": "module",
  "main": "src/index.ts",
  "dependencies": {
    "@deepseek-ai/cordis": "workspace:^"
  }
}
```

Definition 只依赖 Cordis，不依赖任何实现库。

## 12.4 第二步：写 Service Provider

Provider 实现 Definition 的抽象方法。写两个 Provider 演示可替换性：一个用本地词典，一个调远程 API（Application Programming Interface，应用程序编程接口）。

**Provider 1：本地词典**（`dsh-translate-local/src/index.ts`）：

```ts
import type { Context } from '@deepseek-ai/cordis'
import {
  TranslateService,
  type TranslateRequest,
  type TranslateResult,
} from '@my-org/dsh-translate'

// 简易词典
const dict: Record<string, Record<string, string>> = {
  en: { hello: '你好', world: '世界', goodbye: '再见' },
  zh: { 你好: 'hello', 世界: 'world', 再见: 'goodbye' },
}

class LocalTranslate extends TranslateService {
  async translate(request: TranslateRequest): Promise<TranslateResult> {
    const { text, from, to } = request
    const sourceDict = dict[from]
    if (!sourceDict) {
      return { translated: text, confidence: 0 }
    }
    const translated = sourceDict[text] ?? text
    return { translated, detectedFrom: from, confidence: 1 }
  }
}

export const name = 'translate-local'

export function apply(ctx: Context) {
  ctx.plugin(LocalTranslate)
}
```

**Provider 2：远程 API**（`dsh-translate-api/src/index.ts`）：

```ts
import type { Context } from '@deepseek-ai/cordis'
import Schema from '@deepseek-ai/schemastery'
import {
  TranslateService,
  type TranslateRequest,
  type TranslateResult,
} from '@my-org/dsh-translate'

export interface Config {
  endpoint: string
  apiKey: string
}

export const Config: Schema<Config> = Schema.object({
  endpoint: Schema.string().required(),
  apiKey: Schema.string().required(),
})

class ApiTranslate extends TranslateService {
  private endpoint: string
  private apiKey: string

  constructor(ctx: Context, config: Config) {
    super(ctx)
    this.endpoint = config.endpoint
    this.apiKey = config.apiKey
  }

  async translate(request: TranslateRequest): Promise<TranslateResult> {
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        text: request.text,
        from: request.from,
        to: request.to,
      }),
    })
    const data = await response.json()
    return {
      translated: data.translatedText,
      detectedFrom: data.detectedSource,
      confidence: data.confidence,
    }
  }
}

export const name = 'translate-api'
export const inject = ['credentials']  // 可选：通过凭据服务获取 API Key

export function apply(ctx: Context, config: Config) {
  ctx.plugin(ApiTranslate, config)
}
```

两个 Provider 实现同一个抽象方法，但内部逻辑完全不同。切换只需要改 cordis.yml：

```yaml
# 用本地词典
- name: '@my-org/dsh-translate-local'

# 或用远程 API（注释掉上面那行，取消注释下面这行）
# - name: '@my-org/dsh-translate-api'
#   config:
#     endpoint: 'https://api.translate.example.com/v1'
#     apiKey: 'your-key-here'
```

> 金句：Provider 可替换不是便利，是架构约束。Definition 不知道 Provider 存在，Consumer 不知道 Provider 是谁——只有 cordis.yml 知道。

## 12.5 第三步：写 Consumer

Consumer 把服务能力暴露为模型可调用的工具。

`tool-translate/src/index.ts`：

```ts
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import '@my-org/dsh-translate'  // 拉入类型声明

export const name = 'tool-translate'
export const inject = ['tools', 'translate']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'translate',
    description: 'Translate text between languages.',
    parameters: {
      text: { type: 'string', required: true, description: 'Text to translate' },
      from: { type: 'string', required: true, description: 'Source language code' },
      to: { type: 'string', required: true, description: 'Target language code' },
    },
    output: {
      schema: {
        type: 'object',
        properties: {
          translated: { type: 'string' },
          detectedFrom: { type: 'string' },
          confidence: { type: 'number' },
        },
        required: ['translated'],
      },
      render: (args, value) => [
        { type: 'text', text: `${value.translated} (from: ${value.detectedFrom ?? args.from})` },
      ],
    },
    async execute(args, exec) {
      const result = await ctx.translate.translate({
        text: args.text,
        from: args.from,
        to: args.to,
      })
      return result
    },
  }))
}
```

注意 Consumer 的依赖声明：

```ts
export const inject = ['tools', 'translate']
```

它依赖 `tools`（注册工具需要）和 `translate`（调用服务需要）。不依赖任何 Provider 包。

Consumer 的 execute 调用 `ctx.translate.translate(...)`——它调用的是 Service Definition 声明的抽象方法，不知道背后是本地词典还是远程 API。

## 12.6 组装与运行

三个包写好了，在 cordis.yml 里组装：

```yaml
# 最小可运行组合
- name: '@deepseek-ai/dsh-system-prompt'
- name: '@deepseek-ai/dsh-tools'
- name: '@deepseek-ai/dsh-agent-spine-demo'
- name: '@deepseek-ai/dsh-llm-deepseek'
- name: '@deepseek-ai/dsh-credentials-local'
- name: '@deepseek-ai/dsh-settings-file'

# 翻译能力的三个角色
- name: '@my-org/dsh-translate'           # Definition
- name: '@my-org/dsh-translate-local'     # Provider（换实现改这行）
- name: '@my-org/dsh-tool-translate'      # Consumer
```

启动：

```sh
pnpm dsh web --patch ./translate-demo/cordis.yml
```

打开浏览器，对模型说「Use the translate tool to translate 'hello world' from English to Chinese」，模型会调用 translate 工具，收到「你好 世界」。

换 Provider 只需改一行：

```yaml
# 去掉 local，换成 api
- name: '@my-org/dsh-translate-api'
  config:
    endpoint: 'https://api.translate.example.com/v1'
    apiKey: !!js process.env.TRANSLATE_API_KEY
```

重启 dsh，同样的工具调用背后变成了远程 API。Consumer 代码一行没改。

## 12.7 dsh 内置的五大 Seam

dsh 自己的实现就是三段式的最佳实践。docs/user/develop/practice/index.md 列出了 Bash 执行能力的三角色，以下是 dsh 内置的五大 Seam：

| 能力 | Service Definition | Provider（可选） | Consumer |
|---|---|---|---|
| Shell 执行 | dsh-shell | dsh-bash-local / dsh-pwsh-local | dsh-tool-bash |
| 文件系统 | dsh-fs | dsh-fs-local / dsh-fs-sandbox / dsh-fs-e2b | dsh-tool-fs |
| 子进程 | dsh-subprocess | dsh-subprocess-local | （内部使用） |
| LLM | dsh-llm | dsh-llm-deepseek / dsh-llm-pi-ai | dsh-agent-loop |
| 终端 | dsh-pty | dsh-terminal-bash | dsh-tool-terminal |

每个 Seam 的 Provider 都可以独立替换。最典型的替换场景是 E2B（远程沙箱执行环境）：

```
本地模式：                        远程沙箱模式：
dsh-fs-local                      dsh-fs-e2b
dsh-bash-local                    （通过 sandbox 远程执行）
dsh-subprocess-local              dsh-subprocess-e2b
```

教程原文（docs/user/develop/practice/index.md）：

> One Service Definition can have multiple providers selected through cordis.yml. The Service Definition and tool remain unchanged while the provider changes.

这就是三段式的威力——换 Provider 等于换整个执行环境，从本地机器到远程沙箱，不需要改任何业务代码。

## 12.8 设计决策：什么时候用三段式

三段式不是银弹。教程明确警告（docs/user/develop/practice/index.md）：

> Do not split preemptively - use separate packages only when the roles need to evolve independently. A simple tool plugin does not.

决策树：

```
这个能力需要可替换实现吗？
  否 -> 直接写工具插件，不用三段式
  是 -> 这个能力会被多个消费方使用吗？
    否 -> 两段式（Definition + Provider），Consumer 和 Definition 放一个包
    是 -> 完整三段式（三个包）
```

| 场景 | 推荐做法 |
|---|---|
| 一次性工具 | 直接写工具插件 |
| 可能换实现的能力 | 两段式（Definition+Provider 一个包，Consumer 一个包） |
| 多消费方+多实现 | 完整三段式 |

dsh 内部的实践：

| 能力 | 做法 | 原因 |
|---|---|---|
| Shell | 三段式 | 多 Provider（bash/pwsh）、多 Consumer（tool-bash/tool-pwsh） |
| 文件系统 | 三段式 | 多 Provider（local/sandbox/e2b）、多 Consumer（tool-fs/tool-fs-search） |
| LSP | 三段式 | 可能多 Provider（stdio/未来远程） |
| 工具日志 | 单包 | 不需要可替换实现 |

> 金句：三段式的成本是三个包的维护负担。收益是替换自由和独立演进。只有当收益超过成本时才拆——过度设计和设计不足一样有害。

## 12.9 事件扩展点：给 Seam 加策略

三段式分离了实现和接口，但策略（超时、重试、审计、权限）放哪里？dsh 的答案是事件。

以 Shell 能力为例，dsh-shell 的 README 说明：

> execution policy belongs to tools/pre-execute or sandboxing executor

策略不在 Provider 里，不在 Consumer 里，在事件监听器里：

```
工具调用流程（简化）
  |
  v
tools/pre-execute (waterfall)
  |-- 权限检查插件：deny/allow/ask
  |-- 沙箱策略插件：约束执行环境
  |
  v
tools/execute (waterfall)
  |-- 超时插件：加 deadline
  |-- 重试插件：失败重试
  |-- metrics 插件：记录耗时
  |
  v
Provider.execute() -- 实际执行
  |
  v
tools/post-execute (waterfall)
  |-- 审计插件：记录结果
  |-- 脱敏插件：替换敏感内容
  |
  v
tools/result (emit)
  |-- 日志插件：观察最终结果
```

每个策略是独立的插件，通过事件注入，不需要改 Provider 或 Consumer。加策略不需要改代码，只需要在 cordis.yml 里加插件。

这就是 dsh 防御性模式文档（docs/defensive-patterns.zh.md）强调的：

> Prefer not to build deployment policy into the tool. Use tools/pre-execute for extensible allow/deny/ask policy.

## 12.10 完整能力开发检查清单

| 检查项 | 通过标准 |
|---|---|
| Definition 是抽象类 | 继承 Service，只有抽象方法 |
| Definition 导出类型 | Request/Result 接口导出 |
| Definition 声明合并 | declare module 加 ctx 类型 |
| Provider 继承 Definition | 实现 abstract 方法 |
| Provider 通过 ctx.plugin 注册 | 不手动 super(ctx, name) |
| Consumer inject Definition 服务 | 不 inject Provider 包 |
| Consumer 调用 abstract 方法 | 不直接调 Provider 实现 |
| 配置走 Config schema | Schemastery 校验 |
| 策略走事件不走 Provider | 超时/权限/审计用事件拦截 |
| 多 Provider 测试 | 至少验证切换 Provider 不报错 |

## 12.11 系列总结

12 章走完，dsh 的全貌你已经掌握了：

| 章节 | 核心知识点 |
|---|---|
| 第 1 章 | dsh 是插件化 Agent Runtime（运行时），不是单体应用 |
| 第 2 章 | Cordis 驱动一切：上下文、服务注入、事件四模式、可逆副作用 |
| 第 3 章 | Profile/Bundle/Patch 三层装配，patch 是整行替换非深合并 |
| 第 4 章 | Session 会话日志是唯一事实源，append-only，模型可见即已记录 |
| 第 5 章 | Turn/Step 循环：inbox 驱动、waterfall 事件、turn-stopping serial |
| 第 6 章 | 工具执行流水线：pre-execute/execute/post-execute 三段 waterfall |
| 第 7 章 | 能力 Seam 三段式：Definition/Provider/Consumer 分离 |
| 第 8 章 | 六种服务方式：Web GUI/Headless/ACP/SDK/Python/人机协作 |
| 第 9 章 | 插件三形态、Fiber 状态机、Effect 自动清理、ctx 服务容器 |
| 第 10 章 | 从零写插件：工具定义、配置、打包、安装、HMR 调试 |
| 第 11 章 | 五种事件模式、三个实战拦截器、核心事件速查 |
| 第 12 章 | 三段式实战、设计决策、事件加策略、完整开发清单 |

> 金句：dsh 的设计哲学是一句话——一切皆插件，插件皆可替换，替换皆靠 Seam。理解了这句话，你就理解了 dsh 的全部。

## 本章小结

| 要点 | 说明 |
|---|---|
| 三段式 | Service Definition（接口）+ Provider（实现）+ Consumer（工具） |
| 不互相依赖 | Provider 和 Consumer 只依赖 Definition |
| 换 Provider | 改 cordis.yml 一行，不改任何代码 |
| 何时用三段式 | 能力需要可替换实现或多个消费方时 |
| 策略走事件 | 超时/权限/审计用事件拦截，不写进 Provider |
| 内置五大 Seam | Shell、FS、Subprocess、LLM、Terminal |

> 我是怕浪猫，前 12 章写完。
>
> 前 12 章从 dsh 的整体架构一路拆到插件开发、事件系统、能力 Seam。如果你跟着读完了，你现在应该能：看懂 dsh 的源码结构、写出正确的插件、用事件做深度扩展、用三段式设计可替换能力。
>
> 有问题评论区聊，有纠错欢迎指出。如果这系列对你有帮助，分享给也在研究 agent 架构的同事——dsh 值得更多人知道。
>
> 下一章我们进入 dsh 的安全层——沙箱隔离策略与平台实现。
>
> 系列进度：12/16 ｜ 未完待续

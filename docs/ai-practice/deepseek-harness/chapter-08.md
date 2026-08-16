# 第8章：多端服务与扩展生态

> 系列：DeepSeek Harness 源码实战 ｜ 进度 8/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

七章拆解之后，是时候把所有拼图放在一起了。

从第 1 章的认识 dsh，到第 7 章的能力 Seam，我们拆完了 dsh 的骨架、肌肉、神经和血管。第 8 章来看 dsh 的六种服务方式、扩展点全景，然后做一个阶段性总结。

我是怕浪猫，这是系列的最后一篇。我们走完它。

## 8.1 六种服务方式详解

dsh 的同一个 runtime 支持六种打开方式。每一种都共享同一个插件树和会话日志，只是入口和交互方式不同。这种「一套核心、多种入口」的设计，让 dsh 既能当桌面工具用，也能当 CI 自动化引擎用，还能当程序化 API 用。

### 方式 1：Web GUI（交互式浏览器应用）

```sh
dsh web
# 或
dsh --profile web
```

默认地址 `http://127.0.0.1:3080`。浏览器里交互式对话，支持文件编辑预览、工具调用展示、审批确认、终端面板、子代理面板、目标面板等。这是最常用的方式，也是功能最完整的方式。

Web GUI 由两个半包组成：host（宿主端，跑在 Node.js 里）和 client（浏览器端，Vite 构建的 React 应用）。host 负责 agent 循环、工具执行、会话持久化；client 负责 UI 渲染和用户交互。两者通过 WebSocket 通信。

client 端有 20 多个包，覆盖 UI 的每个方面：

| 包 | 职责 |
|---|---|
| client/web | 浏览器端入口 |
| client/web-react | React 应用框架 |
| client/ui-conversation | 对话面板 |
| client/ui-tool | 工具调用展示 |
| client/ui-workspace | 工作区文件树 |
| client/ui-subagent | 子代理面板 |
| client/ui-goal | 目标面板 |
| client/ui-skill | 技能面板 |
| client/ui-model-selection | 模型选择器 |
| client/ui-workflow-run | 工作流运行展示 |
| client/ui-attachment | 附件展示 |
| client/ui-commands | 斜杠命令 |
| client/ui-input-trigger | 输入触发器 |
| client/ui-layout | 布局框架 |
| client/ui-sidebar | 侧边栏 |
| client/ui-theme | 主题 |
| client/ui-primitives | 基础组件 |
| client/ui-slots | 插槽系统 |
| client/connection | WebSocket 连接管理 |
| client/hmr | 热模块替换 |
| client/locale | 国际化 |
| client/runtime | 浏览器端运行时 |
| client/schema-form | Schema 表单 |

这个 UI 包列表本身就是 dsh 功能丰富度的证明。从对话到工作流，从子代理到技能，从附件到斜杠命令——Web GUI 暴露了 runtime 的所有能力。

### 方式 2：Headless（单次任务无 UI 模式）

```sh
dsh --profile headless "帮我跑一下测试并修复失败的用例"
```

单次任务模式。接收一个任务字符串，执行完毕后打印结果并退出。完全无 UI、无交互。适合 CI/CD（Continuous Integration / Continuous Deployment，持续集成 / 持续部署）流水线、定时任务、批处理等场景。

headless 模式的特点：

| 维度 | 说明 |
|---|---|
| 输入 | 命令行参数中的任务字符串 |
| 输出 | 可选多种格式：纯文本、JSON、Markdown |
| 交互 | 无。审批策略默认配置为自动拒绝 |
| 生命周期 | 任务完成即退出，不保持运行 |
| 会话持久化 | 可选。任务完成后会话日志保留，可后续恢复 |

注意审批策略的问题：headless 模式下默认自动拒绝需要审批的操作（因为没有人在旁边审批）。如果你的任务需要写文件或执行命令，需要通过配置调整权限预设——可以设为自动通过（信任模式）或通过外部接口提供审批。

### 方式 3：Web GUI 双半包分离部署

Web GUI 的 host 和 client 可以分离部署。host 跑在服务器上，client 部署为静态资源。适合团队共享一个 dsh 实例的场景。

这种部署方式的好处：

| 优势 | 说明 |
|---|---|
| 团队共享 | 一个 dsh 实例服务多个用户 |
| 资源集中 | agent 循环和工具执行在服务器上，不占本地资源 |
| 远程访问 | 浏览器即可访问，不需要本地安装 |
| 统一配置 | 插件树和权限策略集中管理 |

但有一个安全考量：Web GUI 默认监听 127.0.0.1（本地回环），如果改为 0.0.0.0 需要配置认证。dsh 目前没有内置的用户认证系统——它假设运行环境是可信的。

### 方式 4：ACP（Agent Client Protocol，代理客户端协议）

ACP 是一种程序化自动化协议。dsh 的 ACP 服务器把 agent 暴露给外部程序化客户端，支持会话管理、权限控制和取消操作。

来看 examples 里的 ACP 示例：

```sh
# examples/acp-agent/
# 一个 ACP 自动化服务器，支持会话、权限和取消
```

ACP 适用于以下场景：

| 场景 | 说明 |
|---|---|
| IDE 集成 | 编辑器通过 ACP 驱动 dsh agent |
| 自动化平台 | 测试平台通过 ACP 调用 agent 执行任务 |
| 多 agent 编排 | 一个 agent 通过 ACP 调用另一个 agent |
| 脚本驱动 | Shell 脚本通过 ACP 与 agent 交互 |

ACP 与 Headless 的区别：Headless 是「跑一次就退出」，ACP 是「保持连接，多次对话」。ACP 服务器保持运行，客户端可以创建多个会话、发送多条消息、取消操作。

ACP 的服务器约定（来自 `packages/acp/README.md`）：
- 它是互操作传输层，不是展示或人机交互层
- 配对的进程外 subagent 客户端在 `subagent/subagent-acp`（因为它实现的是 subagent 提供方接口）

### 方式 5：SDK（stdio JSON-RPC）

dsh 的 SDK 包提供了一个 stdio（标准输入输出）JSON-RPC（JSON Remote Procedure Call，JSON 远程过程调用）接口。外部进程可以通过标准输入输出与 dsh 通信。

来看 examples 里的 JSON-RPC 示例：

```sh
# examples/jsonrpc-agent/
# 通过 Python SDK 和 JSON-RPC 驱动的无人值守 coding agent
```

Python SDK 在 `python/sdk` 和 `python/sdk-runtime` 中。SDK 的优势是跨语言——任何能发 JSON-RPC 的语言都能驱动 dsh。Python SDK 提供了更高层的封装，不需要手写 JSON-RPC 消息。

SDK 与 ACP 的区别：ACP 是一种标准化协议（有规范文档），SDK 是 dsh 特定的 JSON-RPC 接口。ACP 更通用，SDK 更灵活。

### 方式 6：人机协作（interaction 家族）

interaction 家族提供人机协作能力，它不是一种独立的「模式」，而是叠加在其他模式上的能力：

| 包 | 职责 | Web GUI | Headless | ACP |
|---|---|---|---|---|
| commands | 斜杠命令（/compact, /goal 等） | 有 | 通过 stdin | 通过协议 |
| user-approval | 操作审批服务 | 有 | 自动 | 通过协议 |
| permission-presets | 权限预设 | 有 | 有 | 有 |
| user-questions | 模型向用户提问 | 有 | 通过 stdout | 通过协议 |
| tool-ask-user | 让模型主动问用户问题 | 有 | 有限 | 通过协议 |

`permission-presets` 值得单独说一下。dsh 有几种权限预设：

| 预设 | 说明 |
|---|---|
| readonly | 只允许读取，禁止写入和执行 |
| auto-approve | 自动批准所有操作（信任模式） |
| default | 默认策略：读允许、写和执行需要审批 |

权限预设通过 `tools/pre-execute` 事件实施。你可以写一个自定义的权限预设，监听 pre-execute，按自己的规则决定 allow 或 deny。

六种方式速查表：

| 方式 | 命令 | 交互 | 适用场景 |
|---|---|---|---|
| Web GUI | dsh web | 全交互 | 日常开发 |
| Headless | dsh --profile headless "task" | 无交互 | CI/CD |
| 双半包 | host + client 分离 | 全交互 | 团队共享 |
| ACP | packages/acp | 协议接口 | 程序化自动化 |
| SDK | packages/sdk | JSON-RPC | 跨语言驱动 |
| 人机协作 | interaction 家族 | 叠加能力 | 审批/提问/命令 |

> 金句：六种方式不是一个产品六个版本，是一个 runtime 六个入口。日志共享，能力共享，只是打开方式不同。

## 8.2 扩展点全景

把 dsh 的所有扩展点画成一张全景图：

```
                    ┌─────────────────┐
                    │   配置层扩展     │
                    │  Profile/Bundle │
                    │  /Patch         │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ Provider 替换 │  │ 事件监听器   │  │ 工具注册    │
    │ (Seam 架构)  │  │ (Cordis 事件) │  │ (ctx.tools) │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           │                │                 │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ fs Provider  │  │ pre-execute  │  │ 自定义工具   │
    │ shell Provider│ │ post-execute │  │ (defineTool) │
    │ llm Provider │  │ turn-stopping│  │              │
    │ subprocess   │  │ request      │  │              │
    │ terminal     │  │ pre-step     │  │             
    └─────────────┘  └─────────────┘  └─────────────┘
           │                │                 │
           └─────────────────┼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   会话扩展       │
                    │ SessionEventMap │
                    │ (新事件类型)     │
                    └─────────────────┘
```

五类扩展点，按难度和影响范围排列：

**1. 配置层扩展（低难度）**

通过 Profile / Bundle / Patch 改变插件树的组成。不需要写代码，只需要写 YAML 配置。

典型操作：禁用某个插件（disabled: true）、插入新插件（insert）、替换插件参数（patch）、调整插件顺序。

**2. 事件监听器（中难度）**

监听 Cordis 事件，注入策略和逻辑。不改工具代码，只在流水线中插入中间件。

典型操作：监听 `tools/pre-execute` 加权限检查、监听 `tools/post-execute` 裁剪结果、监听 `agent/turn-stopping` 注入续跑消息。

**3. 工具注册（中难度）**

通过 `ctx.tools.define()` 注册新工具，让模型可以调用。工具内部调用 ctx 上的服务。

典型操作：注册一个自定义搜索工具、注册一个数据库查询工具、注册一个 API 调用工具。

**4. Provider 替换（高难度）**

实现 Service Definition 的抽象类，注册为 Cordis 插件，替换默认 Provider。改变能力的实现方式。

典型操作：用 E2B 替换本地 fs、用自定义 LLM 适配器替换 DeepSeek、用远程 subprocess 替换本地进程。

**5. 会话扩展（高难度）**

扩展 SessionEventMap，新增事件类型。需要同时更新派生逻辑，确保新事件在消息历史派生中被正确处理。

典型操作：新增一种上下文注入类型、记录自定义的执行元数据。

扩展点对比表：

| 扩展点 | 难度 | 影响范围 | 需要写代码 | 典型场景 |
|---|---|---|---|---|
| 配置层 | 低 | 插件树组成 | 否 | 禁用/启用插件、调整参数 |
| 事件监听器 | 中 | 流水线行为 | 是（监听器） | 权限策略、审计日志、结果裁剪 |
| 工具注册 | 中 | 模型可用工具 | 是（工具函数） | 新增自定义工具 |
| Provider 替换 | 高 | 能力实现 | 是（Provider 类） | 远程沙箱、自定义文件系统 |
| 会话扩展 | 高 | 日志格式 | 是（类型+派生） | 新的上下文注入类型 |

## 8.3 50+ 包家族速查

把整个 dsh 的包家族按功能分组，做一个完整速查：

| 家族 | 包数 | 核心包 | 职责 |
|---|---|---|---|
| core | 6 | session / system-prompt / tools / agent / agent-loop / scope | 运行时核心控制主干 |
| llm | 5 | llm / token-meter / llm-retry / llm-deepseek / llm-pi-ai | LLM 适配与调用 |
| fs | 7 | fs / fs-local / fs-sandbox / fs-e2b / fs-observation-policy / tool-fs / tool-fs-search | 文件系统 |
| shell | 7 | shell / bash-local / bash-sandbox / pwsh-local / shell-env / tool-bash / tool-pwsh | Shell 执行 |
| terminal | 3 | pty / terminal-bash / tool-terminal | 终端 |
| subprocess | 3 | subprocess / subprocess-local / subprocess-e2b | 进程管理 |
| lsp | 3 | lsp / lsp-stdio / tool-lsp | 语言服务器 |
| code-runtime | 2 | code-runtime / code-runtime-worker | 代码执行 |
| web | 5 | web / web-search-exa / web-search-perplexity / web-fetch-http / tool-web | Web 搜索与抓取 |
| workflow | 4 | workflow / workflow-worker-thread / tool-workflow / tool-ralph | 工作流 |
| subagent | 10+ | subagent / subagent-inprocess / subagent-spawn / subagent-acp / ... | 子代理 |
| compaction | 4 | compaction / compaction-basic / compaction-tool-result-pruner / command-compact | 上下文压缩 |
| skill | 4 | skill / skill-badge / skill-filesystem / tool-skill | 技能系统 |
| session | 7 | session-persistence / session-checkpoint-policy / session-persistence-jsonl / sqlite / session-projection / session-query / session-log-export | 会话持久化 |
| goal | 4 | goal / goal-round-driver / tool-goal / command-goal | 目标管理 |
| jobs | 3 | jobs / jobs-local / tool-jobs | 后台任务 |
| interaction | 5 | commands / user-approval / permission-presets / user-questions / tool-ask-user | 人机协作 |
| sandbox | 1 | sandbox（bwrap / Landlock / Seatbelt） | 进程沙箱 |
| extensions | 4 | tool-cordis / cordis-host-runner / cordis-client-runner / ui-cordis | 运行时自修改 |
| hooks | 3 | hook-protocol / hooks-claude-code / hooks-codex | 外部钩子桥接 |
| boot | 2 | app-boot / cmdline | 启动粘合层 |
| host | 1 | host | Web 宿主端 |
| client | 20+ | web / modules / web-react / connection / runtime / hmr / ui-* | 浏览器端 |
| e2b | 3 | e2b / fs-e2b / subprocess-e2b | E2B 远程沙箱（POC） |
| 其他 | 10+ | api / typert / credentials / identity / schedule / feedback / settings / storage / attachment / spill / context / todo / plan / preset / guard / bundle | 基础设施 |

几个值得特别说明的家族：

**extensions（运行时自修改）**：这是 dsh 最实验性的家族。`tool-cordis` 包提供了四个工具——`cordis_inspect`、`cordis_define`、`cordis_run`、`cordis_stop`、`cordis_undefine`——让模型可以检查和修改自己的插件树。这意味着 agent 可以在运行时加载、卸载、配置插件。这是一个「自修改系统」的雏形。

**hooks（外部钩子桥接）**：dsh 可以桥接 Claude Code 和 Codex 的 shell hooks（钩子），把外部 shell 钩子转换为 dsh 的拦截扩展点。这让从 Claude Code 或 Codex 迁移到 dsh 的用户可以保留他们的钩子配置。

**schedule（会话内提醒）**：dsh 的 schedule 家族提供会话内的定时提醒。注意它只在 session 活跃时生效——没有外部通知渠道（不发邮件、不发推送）。如果 session 冷了（不活跃），提醒会暂停，session 恢复后继续。

## 8.4 设计哲学回顾

前八章拆解下来，dsh 的设计哲学可以总结为五条：

**1. 一切皆插件。** 没有特权内核，没有硬编码的能力。agent 循环是插件，工具注册表是插件，会话日志是插件。这意味着任何一个组件都可以被替换、增强、移除。代价是初学者的学习曲线陡峭——因为一切都是插件，你需要理解插件系统才能理解任何一个组件。

**2. 单一事实源。** Session 事件日志是唯一的事实来源。消息历史是派生的，模型上下文是派生的，UI 展示是派生的。改了日志，所有视图自动更新。好处是数据一致性有保证，审计和回放能力强。代价是事件日志的设计要非常谨慎——新增事件类型需要考虑版本兼容性。

**3. 可组合性优先。** Profile / Bundle / Patch 三层装配让配置可组合。Cordis 事件四模式让行为可组合。Seam 三段式让能力可组合。可组合性不是便利，是架构约束。好处是灵活性极高，可以做出各种组合。代价是组合爆炸——不是所有组合都被测试过，用户需要理解组合的语义。

**4. 安全失败。** ignorable 字段默认拒绝不认识的事件。审批服务缺失时 ask 降级为 deny。单调守卫不可推翻。这些设计都遵循「宁可过度拒绝，不可静默接受错误」。好处是系统在边界条件下的行为可预测。代价是有时候不够方便——需要显式配置才能放开限制。

**5. 可审计。** 模型可见即已记录。tool/call 在执行前写日志。sourceEventSeqs 提供完整溯源。任何时刻都可以从日志重建完整的执行过程。好处是调试和安全审计能力强。代价是日志体积——一个长会话的日志可能很大（虽然有 compaction 和 spill 机制缓解）。

> 金句：dsh 不是在做一个 coding agent，是在做一个 coding agent 的平台。区别是：前者是一个产品，后者是一个生态。

## 8.5 适合谁用、怎么上手

| 角色 | 上手路径 | 预计时间 |
|---|---|---|
| 普通用户 | `npx @deepseek-ai/dsh web`，浏览器里用 | 5 分钟 |
| 开发者 | clone 仓库，pnpm install && pnpm run build && pnpm dsh web | 15 分钟 |
| 想定制 | 学 Profile/Patch，改 cordis.patch.yml | 1 小时 |
| 想扩展 | 学事件监听器和工具注册，写 Cordis 插件 | 半天 |
| 想深度改造 | 学 Seam 架构，写自己的 Provider | 1-2 天 |
| 想程序化驱动 | 学 ACP 或 SDK，用 JSON-RPC 驱动 | 半天 |

环境要求：

| 依赖 | 版本要求 |
|---|---|
| Node.js | 22.19+ 或 24+ |
| pnpm | 11.7.0 |
| 操作系统 | macOS / Linux（Windows 支持 pwsh 栈） |

## 8.6 与其他 coding agent 的对比

| 维度 | dsh | Claude Code | Codex | Aider |
|---|---|---|---|---|
| 架构 | 插件化 runtime | 单体应用 | 单体应用 | 单体应用 |
| 核心框架 | Cordis（论文驱动） | 自研 | 自研 | 无框架 |
| 插件系统 | 一切皆插件 | 有限扩展 | hooks | 无 |
| 会话日志 | append-only 事件 | 内部格式 | 内部格式 | Git history |
| Provider 可替换 | 是（Seam 架构） | 否 | 否 | 部分 |
| 远程沙箱 | E2B（POC） | 无 | 无 | 无 |
| 多入口 | 6 种 | CLI + API | CLI | CLI |
| 开源协议 | MIT | 闭源 | Apache-2.0 | Apache-2.0 |
| 开发阶段 | 0.1.0-rc.5（开发者预览） | 生产 | 生产 | 生产 |

dsh 的独特价值在于架构层面——它不是一个产品，是一个平台。如果你只是想用 coding agent 干活，Claude Code 或 Codex 更成熟。如果你想理解 coding agent 的内部运作、或者想深度定制一个 agent runtime，dsh 是最好的学习材料。

## 8.7 系列总结

前八章内容回顾：

| 章 | 主题 | 核心概念 |
|---|---|---|
| 1 | 认识 dsh | Harness 定义、项目定位、五层架构、六种服务方式 |
| 2 | Cordis 插件引擎 | 五个核心概念、事件四模式、ctx 服务注入、可逆副作用 |
| 3 | 装配系统 | Profile / Bundle / Patch、启动链、替换语义、三个默认 bundle |
| 4 | Session 会话日志 | append-only 事件日志、SessionEventMap、Surface 机制、派生一切 |
| 5 | Turn / Step 循环 | Phase 状态机、inbox、事件流、工具并发调度、abort 处理 |
| 6 | 工具执行流水线 | pre-execute 到 post-execute、单调守卫、spill 溢出处理 |
| 7 | 能力 Seam | 三段式架构、五大 Seam、E2B 远程执行、手写 Provider |
| 8 | 多端服务与扩展 | 六种服务方式、扩展点全景、包家族速查、设计哲学 |

dsh 还在 0.1.0-rc.5 阶段，官方说未来会有破坏性变更（breaking changes）。但它的架构设计已经相当成熟——Cordis 插件引擎、Session 日志单一事实源、Seam 三段式、流水线中间件——这些设计不会因为版本迭代而过时。如果你想深入理解 coding agent 的内部运作，dsh 是一个极好的学习样本。

> 金句：读源码不是为了用这个项目，是为了理解一种设计思路。dsh 的思路是：不要做产品，做平台；不要硬编码，做插件；不要存结果，存过程。

> 我是怕浪猫，前八章拆完。如果你跟着看到了这里，感谢你的耐心。前半部分到此结束，后面 8 章进入插件开发实战——dsh 有新版本时我会更新内容。
>
> 有问题评论区聊，有纠错也欢迎指出。如果这个系列对你有帮助，分享给你的同事。
>
> 系列进度：8/16 ｜ 未完待续

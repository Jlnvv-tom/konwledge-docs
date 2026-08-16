---
id: deepseek-harness-index
title: DeepSeek Harness 项目介绍
description: DeepSeek AI 开源的插件化 Agent Harness（智能体框架）深度解析：Cordis 插件架构、Profile/Bundle/Patch 装配机制、会话日志、能力 Seam 与多端接入方式。
sidebar_position: 1
---

# DeepSeek Harness 项目介绍

> 原文仓库：[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)（MIT License，当前版本 `0.1.0-rc.5`，处于**开发者预览**阶段，正在快速迭代，未来会出现破坏性变更）

## 一句话结论

**DeepSeek Harness（简称 `dsh`）不是单体应用，而是一个由 [Cordis](https://github.com/cordiverse/cordis) 驱动的插件化 Agent Runtime（智能体运行时）平台。**

它把「模型能力」「工具能力」「会话持久化」「Web / CLI / ACP / SDK 服务入口」全部拆成可组合模块，通过 **profile + bundle + patch** 三层配置组装出不同运行形态。其设计思想对应论文 [_A Programming Paradigm for Spatiotemporal Composability_](https://github.com/cordiverse/paper)。

## 核心设计理念：一切皆插件

Cordis 是 dsh 底层的插件框架：插件向共享上下文贡献服务、类型化事件和可逆副作用。**产品的每一部分都是插件**——模型适配器、工具注册表、会话日志、甚至 agent loop 本身——因此每一部分都可以从配置替换。

不存在需要打补丁的特权内核：扩展 dsh 的方式是把插件挂载到其他插件旁边，各项注册都是副作用，会在插件卸载时自动撤销。

### Cordis 五个核心概念

| 概念 | 说明 |
|---|---|
| **插件 = 实现 Service 的对象** | 函数插件或 `Service` 子类，生命周期由 Cordis 挂载到上下文 |
| **上下文 = 服务的容器** | 服务占据稳定 `ctx.<key>`（如 `ctx.tools`、`ctx.llm`、`ctx.sessions`），按 key 查找而非导入实现 |
| **inject 声明依赖** | 插件声明所需服务后等待其就绪才启动，加载顺序由依赖表达 |
| **类型化事件通信** | 通过声明合并注册事件，按 `emit` / `waterfall` / `parallel` / `serial` 四种模式分发 |
| **注册 = 可逆副作用** | 通过 `ctx.effect()` / `ctx.on()` 安装，reload 与 teardown 时自动撤销 |

### 事件分发模式

| 模式 | 是否 await | 分发顺序 | 有返回值 |
|---|---|---|---|
| `emit` | 否 | 按注册顺序观察 | 否 |
| `waterfall` | 否 | 按注册顺序观察（环绕中间件，`next()` 委托） | 是 |
| `parallel` | 是 | 并行观察 | 否 |
| `serial` | 是 | 按注册顺序 | 是 |

`ctx.waterfall` 是中间件语义：监听器收到 `(...args, next)`，调用 `next()` 执行下游，不调用则短路——策略监听器借此拥有决策权。

## 总体架构

```text
用户 / 外部进程
   │
   ▼
apps/cli（命令行入口，只负责分发）
   │
   ▼
packages/boot/app-boot（装配与启动：root context + Loader + fail-loud）
   │
   ▼
profile + bundle + patch（配置叠层）
   │
   ▼
Cordis 插件树（共享上下文 ctx）
   │
   ├── core / llm / session / tools / agent（产品主干）
   ├── 能力 seam（shell / web / fs / terminal / subagent / workflow ...）
   └── 服务表面（Web GUI / ACP / SDK / Headless / 人机协作）
```

架构关键点：**运行时没有固定「中心类」**，只有一个共享上下文 `ctx` 和一组会挂载、卸载、复原的插件。

## 启动链：Profile / Bundle / Patch

运行中的 `dsh` 是一棵插件树，由启动时按序叠加的各层组合而成：

1. **组合包（Bundle）**：Cordis 配置项 + 挂载代码的分发格式，`dsh-base` 是每个 profile 的第一层（模型适配器、工具、持久化、沙箱与审批策略、设置、凭据、遥测）。
2. **Profile**：Harness home 中具名组装，列出叠放的组合包、存放树外插件与用户自己的 `cordis.patch.yml`。`web` 和 `headless` 作为模板随发行版交付。
3. **Patch**：按 id 定位条目并**替换整个 config**（非深合并）或插入新条目。

叠加顺序（自底向上）：

```text
空条目列表
  → 各组合包 patch（按 profile 列出的顺序）
  → profile 自身 cordis.patch.yml
  → home 级 $DSH_HOME/cordis.patch.yml
  → --patch 临时 overlay
```

查看实际启动的配置树：

```sh
dsh --profile web --dump-config
```

### CLI 入口模式

| 命令 | 用途 |
|---|---|
| `dsh --profile <name>` | 启动 `$DSH_HOME/profiles/<name>` 下的指定 profile |
| `dsh --profile headless "job"` | 运行一次全新持久会话，打印最终答案后退出（无服务器、无监听端口） |
| `dsh web` | `--profile web` 的别名，默认 `http://127.0.0.1:3080` |
| `dsh plugin --profile <name> <pnpm args>` | 管理 profile 的插件依赖，不运行主运行时 |

`web` 与 `headless` profile 首次使用时从随附模板自动初始化。

## 核心运行机制

### 会话日志是唯一事实源

会话不是「聊天记录」，而是**仅追加的 `SessionEvent` 日志**（`turn/start`、`step/start`、`assistant/chunk`、`tool/result` 等都入日志）。LLM 消息历史从日志**派生**，从不单独存储；回放、fork、恢复、transcript、遥测都从同一事件流导出。

核心不变量：**模型可见即已记录**——抵达模型请求的一切都必须能从日志重建。

### Turn / Step 流程

- **Step** = 一次模型请求 + 它调用的工具
- **Turn** = 零个或多个 step，在领取首条输入时打开，不再欠任何工作时关闭

```text
turn/start
  → 领取输入 → 组装 prompt 片段 + 工具 schema
  → agent/pre-step（可改写或拒绝输入）
  → step/start → 派生模型历史 → agent/request → llm/stream → assistant/chunk*
  → tool/call* → tools/pre-execute → tools/execute → tools/post-execute → tool/result*
  → step/end（若还有后续输入则进入下一 step）
  → agent/turn-stopping → turn/end
```

`agent/pre-step`、`agent/request`、`llm/stream`、`tools/*` 是 waterfall 事件（必须 `next()` 委托）；`agent/turn-stopping` 是 serial 事件。

### 工具执行流水线（策略解耦）

工具执行不是黑盒，而是一条分层流水线：

```text
model 产生 tool-call
  → tools/pre-execute  waterfall（hooks、权限、沙箱、fs 守卫、审批）
  → 单调 guards（deny 或 abstain）
  → tools/execute      waterfall（超时、重试、指标，环绕 dispatch）
  → 工具本体 execute()
  → fs/write-intent 或 fs/edit-intent 门禁（仅 tool-fs 变更）
  → tools/post-execute waterfall（接受 / 阻断 / 替换 / 附加上下文）
  → finalizeContent（内容层最后不变量）
  → tools/result（同步通知，冻结的权威结果）
  → 记录 tool/result 会话事件 → 注入 additionalContexts
```

好处：策略（权限、沙箱、超时）跨工具家族复用，无需把每个工具写成带权限逻辑的胖实现。

### 能力 Seam（可替换能力的三段式）

每个可替换能力包含三种角色：

| 层次 | 作用 | 例子 |
|---|---|---|
| **Service Definition** | 定义能力契约 | `llm`、`shell`、`web`、`fs`、`session` |
| **Service Provider** | 选择具体实现 | DeepSeek LLM、local bash、HTTP fetch、SQLite session |
| **Consumer** | 以能力消费或暴露工具 | `tool-web`、`tool-bash`、`tool-terminal`、`tool-fs` |

**替换一个提供方就能改变整个产品**：文件系统与进程提供方共享同一执行世界，把它们指向远程沙箱，Bash、PTY、LSP 一并搬过去（如 E2B 实验性 POC），无需提供方专用 fork。

## 包结构总览（packages/ 50+ 包）

### 产品主干（core）

| 包 | 职责 | ctx 键 |
|---|---|---|
| `core/session` | 仅追加的 `SessionEvent` 日志与内存存储 | `ctx.sessions` |
| `core/system-prompt` | 提示词片段与工具 schema 组装 | `ctx.systemPrompt` |
| `core/tools` | 作用域化工具注册表 + 带把关的执行流水线 | `ctx.tools` |
| `core/agent` | `Agent` 接口、活跃 agent 注册表、`agent/*` 事件 | `ctx.agents` |
| `core/agent-loop` | 实现该接口的默认驱动器 | `ctx.agentLoop` |
| `core/scope` | 按 agent 划分作用域的注册原语 | 库，无 ctx 键 |

### LLM 家族（llm）

`llm` 承担 Service Definition + Consumer 双重角色：抽象服务、内容块词汇（`text` / `reasoning` / `image` / `tool-call` / `tool-result`）、流式分片组装器、适配器约定。提供方适配器注册到 `ctx.llm`：

- `llm-deepseek`：直接 DeepSeek 适配器
- `llm-pi-ai`：多提供方 pi-ai 适配器
- `token-meter`：可感知回放的 token 计量
- `llm-retry`：提供方作用域重试策略

### 能力家族（Seam 全家桶）

| 家族 | 能力 |
|---|---|
| **fs** | 文件系统 seam：`read`/`write`/`edit` 工具 + ripgrep 发现工具 + 沙箱围栏 + 编辑前读取/版本防护策略 |
| **shell** | Bash / PowerShell 执行器 seam：`bash-local`、`bash-sandbox`、`pwsh-local` + 模型工具 |
| **subprocess** | 子进程基底：受管进程树、PTY 原语、进程树信号 |
| **terminal** | 持久 PTY 会话（跨工具调用保留状态、交互式 stdin） |
| **sandbox** | 进程沙箱 seam：bwrap / Landlock / Seatbelt / Windows ACL 受限令牌后端 |
| **lsp** | 语言服务器 seam：`goToDefinition` / `findReferences` / `goToImplementation` / `hover` |
| **code-runtime** | 代码执行 seam：worker-thread 后端 + Code Mode Consumer（`run_code`） |
| **web** | 搜索/抓取 seam：Exa / Perplexity / DeepSeek 原生搜索 + HTTP fetch |
| **skill** | Skill 发现与加载（本地文件系统 / 嵌入式 / 远程提供方） |
| **compaction** | 上下文压缩 seam：token 压力摘要 + 工具结果修剪 |
| **subagent** | 子 agent 委派：进程内 spawn/fork、ACP、Codex、Claude Code、dsh SDK |
| **jobs** | 通用后台任务运行时 + `job_*` 控制工具 |
| **workflow** | 模型编写编排工作流的 worker-thread 引擎 + `workflow`/`ralph` 工具 |
| **context** | 模型可见请求上下文（工作区指令、时间、tmux 位置、会话引用） |
| **spill / attachment / storage** | 大数据量工具输出 spill、不可变附件、非会话持久化 |
| **todo / plan / goal / schedule / feedback** | 待办、Plan Mode、同会话目标、会话内提醒、人类反馈 |
| **guard** | 循环卫生：重复调用提醒 + 工具调用超时强制 |

### 人机协作平面（interaction）

| 包 | 职责 | ctx 键 |
|---|---|---|
| `commands` | 用户命令注册与分发（无需模型轮次） | `ctx.commands` |
| `user-approval` | 一次性审批决策协调 | `ctx.approval` |
| `permission-presets` | 面向用户的权限预设 | `ctx.permissionPresets` |
| `user-questions` | 与提供方无关的用户问答 seam | `ctx.userQuestions` |
| `tool-ask-user` | 向模型提供「询问用户」工具 | 注册到 `ctx.tools` |

### 扩展与集成

| 包 | 能力 |
|---|---|
| **hooks** | Claude Code / Codex 钩子桥接：指向现有 `hooks.json` 即可忠实运行外部 shell 钩子 |
| **extensions** | agent 修改自身运行时：`cordis_inspect` / `cordis_define` / `cordis_run` / `cordis_stop` / `cordis_undefine`（动态包 + `node:vm` 沙箱 + 浏览器侧面板） |
| **preset** | 按会话组装 agent：每个会话可拥有不同的工具与提示词段落（`agent.cordis.yml`） |
| **e2b**（POC） | 把 fs/subprocess 执行世界放进 E2B Linux 沙箱 |

## 服务方式（多端接入）

| 方式 | 入口 | 特点 |
|---|---|---|
| **CLI Web 模式** | `dsh web` | 交互式 GUI，默认 `127.0.0.1:3080` |
| **CLI Headless** | `dsh --profile headless "task"` | 单次任务、打印结果退出，适合 CI/脚本 |
| **Web GUI** | `packages/host` + `packages/client` | Host 提供 HTTP carrier / API gateway；Client 是浏览器壳 + UI 插件系统（`ui-*` 插件），页面按 boot manifest 运行时拉取插件 |
| **ACP** | `packages/acp` | Agent Client Protocol 自动化服务器，面向程序化客户端 |
| **SDK** | `packages/sdk` | 通过 stdio JSON-RPC 从外部进程驱动 runtime（TypeScript 客户端 + 服务端插件） |
| **Python SDK** | `python/sdk` | Python 侧 SDK（`deepseek_harness`），配套 sdk-runtime |

Web GUI 不是「固定前端 + 固定后端」，而是「运行时生成的插件化页面」：Host 端 `webserver` + `api` gateway（Typert RPC），Client 端 `connection` 维护 RPC 与事件传递，`modules` 扫描浏览器插件表生成 `window.__DSH_BOOT__`。

## 数据与持久化

整个数据面是一组**从日志派生的投影**：

- `session`：append-only 事件日志（JSONL / SQLite 后端 + 检查点策略）
- `session-query`：检索与关系读取（SQLite 全文搜索）
- `session-projection`：把日志投影为客户端当前状态（带检查点缓存）
- `session-title`：从日志派生会话标题
- `session-telemetry`：活动投影到遥测（OTel）
- `attachment` / `storage`：日志外持久对象

## 工程实践与仓库结构

- **技术栈**：TypeScript monorepo（pnpm workspace，`pnpm@11.7.0`），Node `^22.19.0 || >=24.0.0`，MIT 许可
- **双 aggregate 编译**：Host / Client 两个 tsconfig program 隔离（因两侧对 `Context` 接口做声明合并会冲突）
- **Typert**：从源码类型生成运行时反射产物，支撑 API Gateway 的 Remote 方法调用（`@Remote` / `@RemoteScope`）
- **测试矩阵**：vitest 单元 / e2e / snapshot / web 性能 / web 压测 / GUI；CI 覆盖 Linux、Windows（含 Wine）与 Node 多版本
- **原生组件**：`native/landlock-run` —— 维护 Landlock 自限执行启动器的 npm 包家族（linux-arm64 / linux-x64 / entry），作为 `ctx.sandbox` 的 Linux 后端
- **示例**：`acp-agent`、`headless-agent`、`jsonrpc-agent`（Python SDK 驱动）、`mcp-memory`（第三方 MCP 记忆服务器）、`web-cordis`（自指 agent 检查/修改自身插件树）、`web-schedule`（会话内提醒）

## 新行为的归属位置（扩展速查）

| 目标 | 机制 |
|---|---|
| 添加模型提供方 | 在 `ctx.llm` 上注册适配器 |
| 添加面向模型的能力 | 在 `ctx.tools` 上注册；schema 加入提示词组装 |
| 让某会话拥有不同能力集合 | 组装 agent preset（服务行需 `isolate` realm） |
| 添加 shell / 终端执行 | 注册 `ctx.shell` / `ctx.terminals` 后端 |
| 添加用户命令 | 在 `ctx.commands` 注册，无需模型轮次 |
| 添加后台工作 | 在 `ctx.jobs` 注册 |
| 限制所启动进程 | 使用 `ctx.sandbox` 后端 |
| 拦截请求 / 工具 / 轮次 | 相应 `agent/*` 或 `tools/*` 事件 |
| 添加模型可见上下文 | `agent.inject()`，落入下一次获准请求 |
| 添加 UI / 编辑器集成 | 驱动 `ctx.agents` 并从 `session/event` 渲染 |
| 添加持久会话状态 | 扩展 `SessionEventMap`，从日志渲染回放 |
| fork 活跃会话 | `ctx.sessions.fork(source, boundary?, childSessionId?)` |

## 快速上手

```sh
# 方式一：npm 直接运行（需 Node.js）
npx @deepseek-ai/dsh web

# 方式二：从源码运行
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
```

启动后在 **设置 → 模型** 填入 DeepSeek API 密钥（无需重启），选择工作区后即可开始对话：agent 可以读写工作区文件、执行命令、委派子任务、维护计划，超出权限策略的操作会先询问用户审批。

## 总结

DeepSeek Harness 的核心**不是一个「代理程序」，而是一个可以被配置成不同服务形态的 agent runtime 平台**。理解它最关键的三个抓手：

1. **装配层**：profile / bundle / patch 决定「跑成什么样」
2. **事件层**：session log 决定「发生过什么、能回放什么」
3. **能力层**：seam / provider / consumer 决定「能换什么、怎么扩展」

它把 Claude Code / Codex 式 coding agent 的能力（文件系统、shell、终端、LSP、沙箱、subagent、hooks）全部插件化、可组合、可替换，同时通过 ACP / SDK / Headless 把同一套 runtime 暴露给自动化客户端——这正是「驾驭工程（Harness Engineering）」走向平台化的一个代表实现。

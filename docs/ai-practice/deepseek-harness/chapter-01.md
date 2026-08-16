# 第1章：认识 DeepSeek Harness——一个插件化的 Agent Runtime 平台

> 系列：DeepSeek Harness 源码实战 ｜ 进度 1/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

你以为 coding agent（编码智能体）是一个程序，其实它是一个可以拼装的运行时平台。

当你在终端里敲下一行命令，让 AI 帮你修 bug、写测试、重构代码的时候，背后跑的不是一个简单的「prompt 进、结果出」的脚本。它是一个完整的运行时：管理会话上下文、调度工具调用、执行沙箱策略、持久化历史记录、处理并发与中断。这个运行时就是 Harness（驾驭层）——介于 LLM（Large Language Model，大语言模型）和你的工程环境之间的那层软件。

我是怕浪猫，一个喜欢拆开源项目的技术博主。从这篇文章开始，我会用 8 章的篇幅，带你从源码层面完整拆解 DeepSeek 开源的 Harness 项目——`dsh`（DeepSeek Harness 的缩写）。这是第 1 章，先搞清楚它到底是什么、怎么跑起来、整体长什么样。

## 1.1 什么是 Harness：从 LLM 到可用 Agent 的最后一块拼图

先问一个问题：为什么不直接调 LLM 的 API（Application Programming Interface，应用程序编程接口）来干活？

答案很简单——裸模型只会输出文本。你让它「帮忙修一下 auth.ts 里的登录 bug」，它能给你一段修改建议，但它不会自己去读文件、跑测试、检查 git diff、写 commit message。这些「动手」的能力，需要一层软件来提供。

这层软件就是 Harness。它的职责可以用一句话概括：

> 把 LLM 的语言能力，变成可在真实工程环境中执行的操作能力。

具体来说，一个 Harness 要解决五件事：

| 职责 | 说明 |
|---|---|
| 上下文管理 | 维护对话历史，决定模型每次请求能看到什么 |
| 工具调度 | 把模型说的「我要读文件」翻译成实际的函数调用，再把结果喂回去 |
| 执行策略 | 权限控制、沙箱隔离、超时重试、审批流程 |
| 持久化 | 会话记录可保存、可回放、可 fork |
| 多形态 | 同一个 runtime（运行时），能以 Web GUI（Graphical User Interface，图形用户界面）、CLI（Command Line Interface，命令行界面）、headless（无头模式）等多种方式被使用 |

如果你做过 agent 项目，大概率自己拼过这些零件。dsh 的思路是：把这些全部做成插件，用一套框架组装起来，形成一个可商用的平台。

来看一个对比：

```
裸 LLM 调用
┌──────────┐     ┌──────────┐
│  用户     │────▶│  LLM API │────▶ 文本输出
└──────────┘     └──────────┘
                  （没有文件、没有终端、没有持久化）

Harness 化 Agent
┌──────────┐     ┌──────────────────────────────────┐     ┌──────────┐
│  用户     │────▶│  Harness Runtime                 │────▶│  LLM API │
│          │     │  ┌─────────────────────────┐     │     └──────────┘
│  Web/CLI │     │  │ 会话管理  工具注册表      │     │
│  SDK/ACP │     │  │ 执行流水线  沙箱策略       │     │
│          │     │  │ 持久化  审批  子代理       │     │
└──────────┘     │  └─────────────────────────┘     │
                 └──────────────────────────────────┘
                  （文件、终端、LSP、shell 全部接入）
```

> 金句：LLM 是引擎，Harness 是底盘。没有底盘的引擎能转，但上不了路。

## 1.2 dsh 项目定位与现状

dsh 是由 DeepSeek AI 开发的开源项目，仓库地址在 GitHub（https://github.com/deepseek-ai/deepseek-harness）。几个关键信息：

- **版本**：0.1.0-rc.5（Release Candidate，发布候选版本），Docusaurus 3.10.1 文档站点
- **许可证**：MIT（Massachusetts Institute of Technology，麻省理工学院）许可，商用友好
- **阶段**：开发者预览（Developer Preview），官方明确说「未来将出现破坏兼容性的变更」
- **语言**：TypeScript，Node.js 22.19+ 或 24+ 运行时（CI 覆盖 22.19、24 和 26）
- **包管理**：Corepack 启用的 pnpm 11.7.0，monorepo（单体仓库）结构，Git 2.26+
- **构建**：tsc 先行 emit，tsdown 分 Host/Client 两阶段构建，Typert 在 Host 阶段生成类型反射

项目采用 monorepo 布局，主要目录结构如下：

```
deepseek-harness/
├── apps/               # 应用入口
│   ├── cli/            # dsh 命令行工具（bin.ts 三模式分发）
│   ├── web/            # Web 前端应用（Vite 构建，packages/client 聚合）
│   └── qurvis/         # 桌面应用（Electron 壳）
├── packages/           # 50+ 功能包（按家族分组，Host/Client 两聚合）
│   ├── core/           # 核心包（session/tools/agent/agent-loop/scope/system-prompt）
│   ├── llm/            # LLM 适配器（llm-deepseek/llm-pi-ai/llm-replay）
│   ├── fs/             # 文件系统（fs-local/fs-sandbox/fs-e2b + tool-fs）
│   ├── shell/          # Shell 执行（bash-local/bash-sandbox/pwsh-local + tool-bash）
│   ├── boot/           # 启动装配（app-boot: Profile/Bundle/Patch 合成）
│   ├── bundle/         # 默认组合包（dsh-base/dsh-web-app/dsh-headless）
│   ├── subagent/       # 子代理（spawn-in-process/fork-in-process/acp/codex/claude-code）
│   ├── workflow/       # 工作流引擎（workflow/tool-workflow/tool-ralph）
│   └── ...             # 其他能力家族
├── docs/               # 架构文档 + 子系统文档 + 生成式目录
├── examples/           # 示例项目（agent-spine-demo 等）
├── tsconfig.host.json  # Host 聚合（Node 侧包 + 示例 + 测试 + 脚本）
├── tsconfig.client.json # Client 聚合（浏览器侧包 + apps/web）
└── tsconfig.base.json  # 共享 paths 映射（无 include，解析门面）
```

`packages/` 下有 50 多个包，全部以 `@deepseek-ai/dsh-*` 为 npm scope（命名空间）发布。这不是一个小项目——它是一个完整的平台。

> 金句：50 多个包，不是一个应用，是一个生态的雏形。

## 1.3 与 Claude Code / Codex / OpenCode 的定位差异

你可能已经在用其他 coding agent 了。Claude Code、OpenAI Codex、OpenCode 都是优秀的工具。dsh 和它们的区别在哪？

| 维度 | dsh | Claude Code | Codex | OpenCode |
|---|---|---|---|---|
| 架构模式 | 全插件化，Cordis 驱动 | 单体应用 | 单体应用 | 插件化 |
| 开源程度 | MIT 开源，可自托管 | 闭源 | 部分开源 | 开源 |
| Provider 可替换 | 任意 LLM 适配器（ctx.llm 注册） | 仅 Claude | 仅 OpenAI | 多模型 |
| 程序化接入 | ACP + SDK + JSON-RPC | 不支持 | 不支持 | 不支持 |
| 多形态 | Web/CLI/Headless/SDK/ACP | CLI 为主 | IDE 集成 | CLI 为主 |
| 沙箱策略 | 可插拔（bwrap/Landlock/Seatbelt） | 内置 | 内置 | 无 |

核心差异在于「可组合性」。dsh 的设计哲学是：每一个功能都是插件，包括模型适配器、工具注册表、会话日志、agent 循环本身。这意味着你可以替换任何一个组件，而不需要 fork 整个项目。

举个例子：你想把文件系统操作指向远程沙箱（比如 E2B 沙箱），在 dsh 里只需要替换 `ctx.fs`（文件系统服务）的 Provider（提供方），Bash、PTY（Pseudo Terminal，伪终端）、LSP（Language Server Protocol，语言服务器协议）等工具会自动跟着搬过去，因为它们都依赖同一个文件系统接口。在其他单体应用里，这可能需要改几十处代码。

> 金句：单体应用改一个功能要动全身，插件化平台换一个 Provider 就够了。

## 1.4 快速上手：npx 运行、源码构建、第一个会话

### 方式一：npx 一键运行

如果你只是想体验，最快的方式是：

```sh
npx @deepseek-ai/dsh web
```

前提是你装了 Node.js。这条命令会启动 Web UI，默认地址是 `http://127.0.0.1:3080`。打开浏览器就能看到界面，按引导设置模型 API Key（API 密钥）即可开始对话。

首次运行时，dsh 会在 `$DSH_HOME`（默认是 `~/.dsh`）下创建 profile（装配档案）模板，包括 `profiles/web/` 目录和默认配置文件。

### 方式二：从源码构建

如果你想深入源码，建议从源码运行：

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
```

环境要求：
- Node.js 22.19+ 或 24+
- pnpm 11.7.0

`pnpm install` 会安装所有依赖（包括 workspace 里的 50+ 包），`pnpm run build` 会构建全部包，`pnpm dsh web` 启动 Web 应用。

### 入口源码：bin.ts 是怎么分发的

dsh 的 CLI 入口在 `apps/cli/src/bin.ts`，它做的事情很简单：解析参数，按模式动态 import 对应的执行器。来看真实代码：

```typescript
// apps/cli/src/bin.ts（节选）
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { loadLayeredEnv } from '@deepseek-ai/dsh-app-boot'
import { parseDshArgs } from './args.ts'

function readVersion(): string {
  const manifest = JSON.parse(
    readFileSync(fileURLToPath(new URL('../package.json', import.meta.url)), 'utf8'),
  ) as { version?: unknown }
  return typeof manifest.version === 'string' ? manifest.version : '0.0.0'
}

const invocation = parseDshArgs(process.argv.slice(2), readVersion())

switch (invocation.mode) {
  case 'profile': {
    const { runProfile } = await import('./profile-boot.ts')
    await runProfile({
      environment: loadLayeredEnv('dsh'),
      profile: invocation.profile,
      patchFiles: invocation.patches,
      args: invocation.args,
    })
    break
  }
  case 'plugin': {
    const { runPlugin } = await import('./plugin.ts')
    process.exit(runPlugin(invocation.profile, invocation.args))
    break
  }
  case 'dump-config': {
    const { runDumpConfig } = await import('./dump-config.ts')
    runDumpConfig(invocation.profile, invocation.defaultOnly, invocation.patches)
    break
  }
  default:
    invocation satisfies never
    throw new Error(`dsh: unhandled invocation mode ${JSON.stringify(invocation)}`)
}
```

这段代码的设计要点有三个：

1. **动态 import**：每个模式只加载自己需要的代码，不相关的模块不会进入进程。`dsh web` 不会加载 `dump-config` 的逻辑，反之亦然。
2. **三种模式**：`profile`（启动一个装配档案）、`plugin`（管理插件依赖，转发给 pnpm）、`dump-config`（打印配置树并退出，不启动服务）。
3. **`satisfies never` 守卫**：`default` 分支用了 TypeScript（TypeScript，带静态类型的 JavaScript 超集）的 `satisfies never` 操作符，如果将来加了新模式但忘了加 case，编译期就会报错。这是工程级别的防御编程。

### 参数解析：args.ts 的设计

`parseDshArgs` 函数在 `apps/cli/src/args.ts` 中定义。它的设计有一个巧思：启动器只解析自己拥有的标志（`--profile`、`--patch`、`--dump-config`），第一个不认识的 token 之后的参数全部原样传递给被启动的应用插件。

来看帮助示例：

```
Examples:
  dsh --profile web                          boot the web profile (same as: dsh web)
  dsh --profile headless "run the tests"     answer one task, print the result, and exit
  dsh --profile tui --patch ./extra.yml      boot a custom profile with one extra overlay
  dsh --profile tui --resume <session>       arguments after the launcher flags reach the app
  dsh --profile web --help                   the web app's own flags and help
  dsh plugin --profile tui add <package>     install a plugin into the tui profile
```

注意 `dsh --profile tui --resume <session>` 这行。`--resume` 不是启动器的标志，它会被传递给 tui profile 内部的应用插件去处理。这种「启动器只管装配，应用逻辑交给插件」的分层，让 dsh 的 CLI 保持了极简。

还有一个语法糖：`dsh web` 是 `--profile web` 的别名，定义在 args.ts 里的子命令中：

```typescript
// apps/cli/src/args.ts（节选）
const web = program.command('web')
  .description('boot the web profile (alias of --profile web)')
  .helpOption(false)
  .allowUnknownOption()
  .passThroughOptions()
  .enablePositionalOptions()
  .argument('[args...]', 'arguments for the web app')
  .option('--patch <path>', 'extra patch-list overlay', collect)
  .option('--dump-config', 'print the composed web-profile tree and exit')
  .action((args: string[], options: BootOptions) => {
    rejectParentOptions('web')
    resolved = resolveBoot(web, 'web', options, args)
  })
```

### 第一个会话

启动 Web UI 后，流程是这样的：

1. 打开 `http://127.0.0.1:3080`
2. 首次使用会引导你设置模型（选 provider、填 API Key），不需要重启
3. 选择工作区（workspace）目录
4. 开始对话

对话过程中，任何超出权限策略的操作，dsh 会先问你。比如模型想执行一个 shell 命令，会弹审批确认。这是 `dsh-base` bundle 里内置的审批策略在工作，后续章节会详细拆解。

## 1.5 总体架构一览：从 CLI 到插件树

现在把视角拉高，看 dsh 启动后整体长什么样。

### 五层架构

```
用户入口                装配层                运行时核心              能力层
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ dsh web  │────▶│              │      │              │      │  fs (文件)    │
│ dsh --   │     │  Profile     │      │  Cordis      │      │  shell (终端) │
│  profile │────▶│  Bundle      │────▶│  插件树       │────▶│  llm (模型)   │
│  headless│     │  Patch       │      │              │      │  web (搜索)   │
│ SDK/ACP  │      │              │      │              │      │  subagent    │
└──────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                   三层叠加装配              ctx 服务总线           可替换 Provider
```

每一层的职责：

| 层 | 职责 | 关键概念 |
|---|---|---|
| 用户入口 | 接收命令和参数 | CLI / Web / Headless / SDK / ACP |
| 装配层 | 把配置和代码组装成插件树 | Profile / Bundle / Patch |
| 运行时核心 | 管理插件生命周期和事件分发 | Cordis 框架、ctx 服务总线 |
| 能力层 | 提供具体功能（文件读写、shell 执行等） | Seam（接缝）：Service / Provider / Consumer |

### 装配层：三层叠加

启动一个 dsh 实例，实际发生的事情是：

1. **读取 Profile**：找到 `$DSH_HOME/profiles/<name>/` 下的配置
2. **叠加 Bundle**：按 Profile 列出的顺序，把每个 Bundle 的 Cordis 配置项叠上去
3. **应用 Patch**：按层级顺序应用 patch（补丁），按 id 整行替换配置

叠加顺序从底到顶：

```
空配置列表
  │
  ▼
各 Bundle 的 patch（按 profile 列出的顺序）
  │
  ▼
Profile 自己的 cordis.patch.yml
  │
  ▼
Home 级 $DSH_HOME/cordis.patch.yml
  │
  ▼
--patch 命令行临时 overlay（覆盖层）
  │
  ▼
最终配置树 → 交给 Cordis Loader 挂载
```

你可以用 `dsh --profile web --dump-config` 查看最终合成的配置树，确认哪些条目被加载了、哪些被 patch 替换了。

### 运行时核心：Cordis 插件树

配置树合好后，交给 Cordis 框架的 Loader 挂载。每个配置条目对应一个插件，插件向共享上下文（Context，简称 ctx）贡献服务。最终形成一棵插件树，每个插件节点都可以注册服务、监听事件、产生副作用。

核心包及其在 ctx 上占据的键：

| 包 | 职责 | ctx 键 |
|---|---|---|
| core/session | 仅追加的 SessionEvent 日志和内存存储 | ctx.sessions |
| core/system-prompt | 提示词片段和工具 schema 组装 | ctx.systemPrompt |
| core/tools | 工具注册表和守卫执行流水线 | ctx.tools |
| core/agent | Agent 接口、活跃注册表和 agent/* 事件 | ctx.agents |
| core/agent-loop | 默认的 agent 驱动器（唯一具体循环插件） | ctx.agentLoop |
| core/scope | 按 agent 划分作用域的注册原语 | 库，无 ctx 键 |
| llm/llm | 消息词汇表和流式适配器接口 | ctx.llm |
| llm/token-meter | 独立的每会话 token 测量折叠 | ctx.tokenMeter |
| compaction/compaction | 上下文压缩接缝（basic 后端） | ctx.compaction |
| subagent/subagent | 子代理提供方和延续服务 | ctx.subagents |
| goal/goal | 同会话目标域（修订式状态） | ctx.goals |

这些包构成了 dsh 的核心控制主干。它们之间的关系是：agent-loop 驱动 turn（轮次）和 step（步骤），每个 step 里向 llm 发请求，拿到模型回复后调度 tools 执行，所有过程记录到 session 日志。

### 能力层：Seam 架构

能力层是 dsh 最有意思的设计。每个能力（文件系统、shell、搜索等）都遵循三段式：

- **Service Definition（服务定义）**：接口契约，声明有哪些方法
- **Service Provider（服务提供方）**：具体实现，可以被替换
- **Consumer（消费方）**：面向模型的工具，调用 Provider 的方法

比如文件系统：
- Service Definition 在 `packages/fs/fs/` 里定义了 `ctx.fs` 接口（读写文件、列目录等）
- Provider 有 `fs-local`（本地文件系统）、`fs-sandbox`（沙箱受限）、`fs-e2b`（远程 E2B 沙箱）——共享同一个执行世界
- Consumer 是 `tool-fs`，通过 `ctx.fs` 执行读写编辑，`fs-observation-policy` 通过 `fs/*` 事件门控观察状态检查
- `fs-sandbox` 的变更围栏由共享的 `ctx.sandboxPolicy` 模式决定，确保 bash 和 fs 不能围栏到不同根目录

替换 Provider 就能改变整个产品的行为——把 `fs-local` 换成 `fs-e2b`，所有依赖文件系统的工具（Bash、终端、LSP）都会自动指向远程沙箱。不需要改工具代码。

> 金句：在 dsh 里，能力不是一个函数，是一根可以拨插的接缝。

### 六种服务方式

同一个 runtime，支持六种打开方式：

| 方式 | 命令 | 适用场景 |
|---|---|---|
| Web GUI | `dsh web` | 浏览器中交互式对话，默认 127.0.0.1:3080 |
| Headless | `dsh --profile headless "task"` | 单次任务，打印结果退出，适合 CI（Continuous Integration，持续集成） |
| Web GUI（双半包） | host + client | 浏览器端 + 宿主端分离部署 |
| ACP | packages/acp | Agent Client Protocol（代理客户端协议），程序化自动化 |
| SDK | packages/sdk | stdio JSON-RPC（JSON Lines 远程过程调用），外部进程驱动 |
| 人机协作 | interaction 家族 | 命令、审批、权限、提问 |

这六种方式共享同一个插件树和会话日志，只是入口不同。你在 Web GUI 里的会话，可以 fork 到 Headless 模式跑 CI，也可以通过 SDK 被另一个程序调用。

### 启动链：从 bin.ts 到插件树

把前面讲的串起来，dsh 的完整启动链是这样的：

```
1. 用户执行 dsh --profile web
       │
2. bin.ts 解析参数 → parseDshArgs() → mode='profile'
       │
3. 动态 import profile-boot.ts → runProfile()
       │
4. app-boot 加载 profile：读取 bundles 列表、叠加 patch 层
       │
5. composeEntries() 合成最终配置树
       │
6. Cordis Loader 挂载配置树 → 实例化每个插件 → 注册 ctx 服务
       │
7. web-app bundle 的插件启动 Web Server（端口 3080）
       │
8. 浏览器访问 → 加载 client 端插件 → 渲染 UI
```

其中第 4-6 步是装配的核心。来看 `profile-boot.ts` 里的关键逻辑：

```typescript
// apps/cli/src/profile-boot.ts（节选）
export function prepareProfile(name: string, userLayer = true): Profile {
  healProfilesModuleFallback(INSTALL_ANCHOR)
  const profile = loadProfile(NAME, name, INSTALL_ANCHOR, undefined, { userLayer })
  // ... 总是重写空根配置，防止 Loader 的回写把组合行固化进去
  return profile
}
```

注意注释里提到的设计细节：根配置文件 `cordis.yml` 每次启动都会被重写为空列表 `[]`。这是因为 Cordis 的 Loader 有一个回写机制——插件自我卸载时会持久化当前配置树。如果不重置，上次组合的行会被固化进根文件，下次启动时每个 Bundle 的插入操作会重复一遍，导致配置膨胀。这种细节体现了工程上的谨慎。

> 金句：一个健壮的系统，连「回写会叠加」这种边角 case 都要兜住。

## 本章小结

| 要点 | 说明 |
|---|---|
| Harness 定义 | 介于 LLM 和工程环境之间的运行时层，负责上下文、工具、策略、持久化、多形态 |
| dsh 定位 | DeepSeek AI 开源的插件化 Agent Runtime，MIT 许可，开发者预览期 |
| 核心差异 | 全插件化架构（Cordis 驱动），任意 Provider 可替换，六种服务方式 |
| 入口设计 | bin.ts 三模式分发（profile/plugin/dump-config），动态 import 按需加载 |
| 架构五层 | 用户入口 → 装配层 → Cordis 插件树 → 核心包 → 能力 Seam |
| 装配三概念 | Profile（装配档案）、Bundle（组合包）、Patch（按 id 整行替换） |
| 能力 Seam | Service Definition + Provider + Consumer，换 Provider 即换产品形态 |
| 服务方式 | Web GUI / Headless / 双半包 / ACP / SDK / 人机协作 |

## 下章预告

这一章我们俯瞰了 dsh 的全貌。但你可能还有一个疑问：为什么 dsh 敢把所有功能都做成插件？它的插件引擎到底有多强？

下一章，我们来拆 Cordis——驱动 dsh 的插件引擎。你会看到它的四种事件分发模式、服务注入机制、可逆副作用设计，以及它在 dsh 中的具体落地。

> 我是怕浪猫，如果你觉得这篇有用，收藏一下整个系列。评论区聊聊你正在用的 coding agent 是单体还是插件化的？
>
> 系列进度：1/8 ｜ 下一章：Cordis 插件引擎

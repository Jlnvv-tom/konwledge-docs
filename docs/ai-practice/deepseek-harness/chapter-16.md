# 第16章：构建你自己的 dsh 发行版——从 profile 定制到生产部署

> 系列：DeepSeek Harness 源码实战 ｜ 进度 16/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

15 章拆完了 dsh 的内部机制。最后一章换个视角：不拆源码，讲怎么用这些机制构建你自己的 dsh 发行版。

你要做的可能是给团队定制一个安全的编码 agent，可能是给客户做一个受限的自动化助手，也可能是把 dsh 嵌入到自己的产品里。无论哪种，核心都是同一件事：组装 profile（配置档案），选择 bundle（捆绑包），写 patch（补丁），部署到生产。

我是怕浪猫，最后一章。收官。

## 16.1 发行版的三层组装

dsh 的组装系统有三层，我们在第 3 章见过。这里从发行版构建的视角重新审视：

```
第一层：bundle（npm 包）
  |-- 携带配置层的 npm 包，manifest 声明 dsh.bundle
  |-- 每个 bundle 贡献一组插件行（insert）
  |
第二层：profile（可运行组合）
  |-- $DSH_HOME/profiles/<name> 目录
  |-- manifest 声明 dsh.profile 的 bundles 有序列表
  |-- 第一个 bundle 必须是 @deepseek-ai/dsh-base
  |
第三层：patch（覆盖层）
  |-- profile 自身的 cordis.patch.yml
  |-- $DSH_HOME/cordis.patch.yml（机器级偏好）
  |-- --patch 命令行 overlays
```

加载顺序（来自 docs/user/develop/basic/package-and-install.zh.md）：

```
1. 空根
2. profile bundles 列表序（dsh-base 最先）
3. profile 自身 cordis.patch.yml
4. $DSH_HOME/cordis.patch.yml（机器本地偏好，全 profile 共享）
5. 各 --patch argv 序
```

后层按行获胜。patch 替换整行 config 值，不是深合并——覆盖时必须重述整行每个键。

三层组装的设计意图：

| 层 | 谁负责 | 改什么 |
|---|---|---|
| bundle | 包作者 | 插件选择和默认配置 |
| profile | 运维 / 平台团队 | bundle 组合和部署配置 |
| patch | 机器管理员 / 用户 | 机器级偏好和临时覆盖 |

## 16.2 设计你的 profile

一个 profile 最少需要：

```yaml
# $DSH_HOME/profiles/my-team/cordis.yml
# 空根配置——树是 patch 组成的
[]
```

```json
// $DSH_HOME/profiles/my-team/package.json
{
  "name": "my-team-profile",
  "private": true,
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-web-app"
      ]
    }
  }
}
```

然后安装依赖：

```bash
cd $DSH_HOME/profiles/my-team
pnpm install
dsh plugin --profile my-team  # 初始化 profile
```

这是最小可运行 profile——使用官方 base bundle 和 web-app bundle，启动 Web GUI。

## 16.3 定制插件选择

通过 patch 移除不需要的插件、添加自定义插件。profile 的 `cordis.patch.yml`：

```yaml
# 移除默认的 bash-sandbox，换成 bash-local（信任环境）
- id: bash-sandbox
  disabled: true

- id: bash-local
  disabled: false
  name: '@deepseek-ai/dsh-bash-local'
  config:
    timeoutMs: 120000  # 2 分钟超时
```

添加自定义工具插件：

```yaml
# 插入自定义插件
- insert:
    id: my-code-reviewer
    name: '@my-org/dsh-code-reviewer'
    config:
      reviewDepth: 'thorough'
      languages: ['typescript', 'python']
```

添加 LLM adapter：

```yaml
# 使用 DeepSeek 官方 API
- id: llm-deepseek
  name: '@deepseek-ai/dsh-llm-deepseek'
  config:
    thinking: enabled
    reasoningEffort: max
    models:
      deepseek-v4-pro:
        contextWindow: 128000
      deepseek-v4-flash:
        contextWindow: 128000
```

## 16.4 安全配置：生产必备

生产环境的安全配置清单：

**凭据管理**

```yaml
# 凭据服务——从环境变量解析，不内联 key
- id: credentials
  name: '@deepseek-ai/dsh-credentials-local'
  config:
    # 引用环境变量名，不是值
    # DEEPSEEK_API_KEY 需在运行时环境中设置
```

**沙箱模式**

```yaml
# 默认使用沙箱 bash
- id: bash-sandbox
  disabled: false
  name: '@deepseek-ai/dsh-bash-sandbox'

# 沙箱策略
- id: sandbox-policy
  name: '@deepseek-ai/dsh-sandbox-policy'
  config:
    defaultMode: workspace-write  # 不用 danger-full-access
```

**权限预设**

```yaml
# 静态权限规则
- id: permission-presets
  name: '@deepseek-ai/dsh-permission-presets'
  config:
    rules:
      # 允许读取任何文件
      - pattern: 'read:*'
        decision: allow
      # 写入需要审批
      - pattern: 'write:*'
        decision: ask
      # 禁止写入系统目录
      - pattern: 'write:/etc/*'
        decision: deny
      - pattern: 'write:/usr/*'
        decision: deny
```

**用户审批**

```yaml
# 启用用户审批
- id: user-approval
  name: '@deepseek-ai/dsh-user-approval'
```

## 16.5 设置与配置管理

dsh 的设置系统（dsh-settings）是分层的。来自子系统文档（docs/subsystems/settings.zh.md）：

每个已注册 namespace（命名空间）解析为三层合并：

```
schema 默认值 → 注册方组合 base → 用户分节
```

设置文件位置（$DSH_HOME/settings.yaml）：

```yaml
# 用户设置文件
shell:
  defaultTimeout: 60000
  maxSpillBytes: 67108864

llm-deepseek:
  thinking: enabled
  reasoningEffort: max
```

每个 namespace 的注册方可声明：

| 选项 | 说明 |
|---|---|
| schema | Schemastery 标准 schema，校验用户值 |
| base | 组合基础值（schema 默认值之上） |
| applies | 'live'（热重载）或 'restart'（需重启） |
| validate | 跨字段约束钩子 |

`applies` 是 UI 提示而非机制——`restart` 的 owner 只是从不 watch，其值在构造期读取一次。`live` 的 owner 通过 `watch()` 接收变更通知。

文档的关键设计原则：

> 外部编辑不能使运行中的 owner 停滞。存储分节校验失败时保留上一个好值并告警。

这意味着：如果用户手动编辑 settings.yaml 写了非法值，dsh 不会崩溃——保留上一个有效值并告警。

## 16.6 会话持久化选择

dsh 提供两个可互换的持久化后端：

| 后端 | 包 | 文件格式 | 适用场景 |
|---|---|---|---|
| JSONL | dsh-session-persistence-jsonl | 每会话一个 .jsonl 文件 | 小规模、可移植 |
| SQLite | dsh-session-persistence-sqlite | 共享数据库 | 大规模、查询密集 |

来自持久化文档（docs/subsystems/persistence.zh.md）的关键设计：

> session/event 是同步通知。持久化插件复制到逐会话控制器不阻塞生产方；固定批处理窗口（第一待处理事件开启、后续不重置截止时间）。

崩溃恢复机制：

> 遗留未闭合 turn/start 不截断日志。合成 turn/end { reason: { kind: 'interrupted' } } 配对。

`interrupted` 是唯一非循环发出的 TurnEndReason（轮次结束原因）。仅冷会话修复——活跃 id 拒绝，HMR 接管活跃前缀。

选择建议：

| 需求 | 推荐 |
|---|---|
| 单用户、会话数 < 100 | JSONL |
| 多用户、需要查询历史 | SQLite |
| 需要文件可移植性 | JSONL |
| 需要 session-query 工具 | SQLite |

## 16.7 打包你的 bundle

如果你想分发一组自定义插件，可以打包成 bundle。来自文档（docs/user/develop/basic/package-and-install.zh.md）：

bundle 是携带配置层的 npm 包。manifest 声明 `dsh.bundle`：

```json
// package.json
{
  "name": "@my-org/dsh-team-bundle",
  "version": "1.0.0",
  "dsh": {
    "bundle": {
      "contrib": "./cordis.yml"
    }
  }
}
```

```yaml
# cordis.yml — bundle 贡献的插件行
- insert:
    id: my-reviewer
    name: '@my-org/dsh-code-reviewer'
- insert:
    id: my-formatter
    name: '@my-org/dsh-formatter'
```

文档的安装警告很重要：

> GitHub 安装是 fetch 源码，不是构建产物。作者必须 ship prepare 脚本自包含构建。

用户安装时需要在 profile 的 pnpm-workspace.yaml 配置：

```yaml
# pnpm-workspace.yaml
allowBuilds:
  "@my-org/dsh-team-bundle": true
```

pnpm 10 以上会拒绝执行 git 依赖的 prepare 脚本直到显式允许——这是安全措施，因为 prepare 在安装期执行包的代码，在 agent 沙箱外。

## 16.8 六种服务方式选择

dsh 支持六种服务方式，按部署场景选择：

| 方式 | 命令 | 适用场景 | 特点 |
|---|---|---|---|
| Web GUI | dsh web | 交互式开发 | 浏览器界面，端口 3080 |
| Headless | dsh --profile headless "task" | CI/CD 自动化 | 单次任务，打印结果退出 |
| ACP | dsh acp | 程序化客户端 | Agent Client Protocol |
| TS SDK | 代码内调用 | 嵌入应用 | stdio JSON-RPC |
| Python SDK | Python 调用 | Python 生态 | JSON-RPC 驱动 |
| 人机协作 | commands + approval | 受控环境 | 需要人工审批 |

生产部署的典型组合：

```
开发环境：dsh web（Web GUI）
CI/CD：dsh --profile headless "task"（自动化）
生产服务：ACP 或 TS SDK（嵌入应用）
受控环境：人机协作（审批模式）
```

## 16.9 部署检查清单

上线前的检查清单：

**安全**

- [ ] 默认沙箱模式设为 workspace-write（非 danger-full-access）
- [ ] 凭据通过 credentials-local 管理，不内联 key
- [ ] 权限预设配置完成（deny 系统目录写入）
- [ ] 用户审批启用
- [ ] 环境变量清理（移除 *KEY* / *SECRET* / *TOKEN* / *PASSWORD*）
- [ ] spill 文件放 0700 私有目录

**持久化**

- [ ] 选择持久化后端（JSONL / SQLite）
- [ ] 配置 session flush 策略
- [ ] 测试崩溃恢复（kill 进程后重启）

**LLM**

- [ ] API Key 通过凭据服务解析
- [ ] contextWindow 配置正确
- [ ] thinking / reasoningEffort 按需配置
- [ ] 测试 API Key 轮换（不需重启）

**性能**

- [ ] compaction 策略配置（pressure 阈值）
- [ ] maxGoalRounds 按需设置
- [ ] bash timeoutMs 配理（默认 60s）
- [ ] spill maxSpillBytes 配置（默认 64MB）

**运维**

- [ ] 日志收集配置
- [ ] 监控告警（agent/error 事件）
- [ ] 定期清理旧会话日志
- [ ] DSH_HOME 目录权限设置

## 16.10 扩展速查：你需要什么

| 需求 | 用什么 | 怎么做 |
|---|---|---|
| 加一个工具 | defineTool | 写插件，注册到 ctx.tools |
| 加一个 LLM 后端 | LlmAdapter | 实现 stream()，注册到 ctx.llm |
| 替换 bash 执行器 | ctx.shell Provider | 实现 ShellService，替换 bash-local |
| 加沙箱后端 | ctx.sandbox Provider | 实现 SandboxService |
| 加 subagent 后端 | ctx.subagents Provider | 实现 SubagentProvider |
| 加压缩策略 | ctx.compaction Provider | 实现 CompactionEngine |
| 拦截工具调用 | tools/pre-execute | 写 waterfall 监听器 |
| 拦截工具结果 | tools/post-execute | 写 waterfall 监听器 |
| 观察会话事件 | session/event | 写 emit 监听器 |
| 加系统提示词 | system-prompt/assemble | 写 waterfall 监听器 |
| 加用户命令 | ctx.commands | 注册命令处理器 |
| 加计划模式 | plan-mode | 组合 dsh-plan-mode |
| 加技能系统 | skill 家族 | 组合 dsh-skill + skill-filesystem |

## 16.11 系列收官

16 章走完，从认识 dsh 到构建发行版，我们拆了：

| 章 | 主题 | 核心收获 |
|---|---|---|
| 1 | 认识 Harness | 定位、上手、总体架构 |
| 2 | Cordis 插件引擎 | 上下文、服务注入、事件四模式、可逆副作用 |
| 3 | Profile/Bundle/Patch | 启动链、patch 替换语义、CLI 模式 |
| 4 | Session 会话日志 | append-only 事件日志、SessionEventMap、Surface 机制 |
| 5 | Turn/Step 循环 | inbox、事件瀑布、turn-stopping、工具并发调度 |
| 6 | 工具执行流水线 | pre-execute、单调守卫、post-execute、超时重试 |
| 7 | 能力 Seam | 三段式、五大 Seam、E2B 远程执行 |
| 8 | 多端服务与扩展生态 | Web GUI、ACP、SDK、Headless |
| 9 | 插件原理深度剖析 | Cordis 核心机制、Fiber 状态机 |
| 10 | 从零写一个插件 | 工具插件、配置、打包发布 |
| 11 | 事件系统与拦截扩展 | 五把钥匙、典型事件、拦截器 |
| 12 | 能力 Seam 三段式实战 | Service Definition/Provider/Consumer |
| 13 | 沙箱与执行安全 | 进程隔离、平台后端、策略解析 |
| 14 | 子代理与工作流编排 | subagent 多提供方、workflow 脚本编排 |
| 15 | 上下文压缩与目标管理 | compaction 渐进压缩、goal 事件溯源 |
| 16 | 构建你的发行版 | profile 定制、安全配置、部署清单 |

dsh 的设计哲学可以浓缩成三句话：

**一切皆插件。** 没有特权内核，没有硬编码能力。你看到的每个功能——bash、文件系统、LLM 调用、agent loop——都是插件。替换一个 Provider 就能改变整个产品。

**会话日志是唯一事实源。** 模型可见即已记录，已记录即可回放。compaction、goal、plan mode 都从日志派生状态，不引入额外的持久化存储。

**分层不重叠。** 权限管决策，沙箱管效果，凭据管机密。事件管通信，服务管能力，工具管模型接口。每层只做一件事，组合起来形成完整系统。

> 我是怕浪猫，16 章写完。这是系列最后一章。
>
> 如果这 16 篇对你有帮助，从第 1 章开始读起——每一章都独立可读，但按顺序读会看到完整的拼图。
>
> 有问题评论区聊，有纠错欢迎指出，有想深入的话题可以开新系列。
>
> 系列进度：16/16 ｜ 完结

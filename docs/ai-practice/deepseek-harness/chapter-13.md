# 第13章：沙箱与执行安全——进程隔离策略与平台实现

> 系列：DeepSeek Harness 源码实战 ｜ 进度 13/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

agent 能跑命令、能写文件——但这意味着它也能删库、能泄密、能执行恶意代码。一个没有安全边界的 coding agent 是定时炸弹。

dsh 的安全层不是事后加的补丁，是从架构层面设计的能力 Seam。这一章拆解 dsh 的进程沙箱系统：三种模式、三个平台后端、逐调用策略解析、以及为什么沙箱是 Provider（提供者）而不是工具内部逻辑。

我是怕浪猫，第 13 章。我们从最基本的问题开始。

## 13.1 沙箱管什么：只管文件效果

dsh 的沙箱定义很明确——只管控文件系统效果。网络访问、进程可见性不在沙箱的 vocabulary（词汇表）里。

来自子系统文档（docs/subsystems/sandbox.zh.md）的原文：

```ts
type SandboxMode = 'read-only' | 'workspace-write' | 'danger-full-access'
```

三种模式的完整对比：

| 模式 | 读文件 | 写工作区 | 写系统目录 | 临时区 | 适用场景 |
|---|---|---|---|---|---|
| read-only | 允许 | 拒绝 | 拒绝 | 仅 /dev/null | 只读分析、代码审查 |
| workspace-write | 允许 | 允许 | 拒绝 | /tmp + 工作区 | 正常编码、测试 |
| danger-full-access | 允许 | 允许 | 允许 | 全部 | 信任环境下的全权操作 |

注意 `danger-full-access` 不会经过 `ctx.sandbox`——消费方直接 spawn 原始 argv，不调用沙箱服务。来自文档原文：

> Only confining (non-danger-full-access) modes reach the provider. Consumers spawn raw argv directly for danger-full-access without calling ctx.sandbox.

文档还补充了一个 POSIX 细节：`read-only` 模式下 POSIX runner 会授予 shell 所需的 `/dev/null` 接收器，而 Windows ACL runner 不授予任何显式可写根目录。

> 金句：沙箱不是万能盾，只管文件效果不管网络。想限制网络访问，需要在进程层面做——沙箱不是 dsh 的唯一安全层，是文件效果那一层。

## 13.2 强制执行完整性：full 与 partial

沙箱后端报告的完整性是消费方的决策依据。来自文档原文：

```ts
type SandboxEnforcement = 'full' | 'partial'
```

`full` 表示后端管控了该模式承诺的所有文件效果。`partial` 表示活跃后端或旧内核 ABI（Application Binary Interface，应用程序二进制接口）只能管控其中一个子集。

当前的 partial 场景（来自文档原文）：

| 平台 | partial 原因 | 影响范围 |
|---|---|---|
| Linux | 旧 Landlock ABI 版本 | 部分文件操作无法拦截 |
| Windows | ACL runner 的 Everyone 边界 | 环境 ACL 缺口 |
| Windows | 硬链接边界 | 可通过硬链接绕过 |

文档的原文警告：

> Callers requiring an absolute boundary must not treat it as full.

消费方必须区分——需要绝对保证的场景不能接受 partial，必须拒绝或把区别暴露给上层。这体现了 dsh 的「fail loud, no silent degradation（大声失败，不静默降级）」原则：宁可拒绝执行，也不能假装隔离了实际没隔离。

## 13.3 逐调用策略解析

沙箱策略不是全局配置，是逐调用解析的。每次能力调用都会生成一份 `SandboxExecutionPolicy`：

```ts
// 来自 docs/subsystems/sandbox.zh.md
interface SandboxExecutionPolicy {
  mode: SandboxMode         // 文件效果模式
  workspaceRoot: string     // workspace-write 可写的绝对根目录
  sessionId?: SessionId     // 调用会话的 opaque 身份标识
}
```

策略解析的输入：

```ts
interface SandboxPolicyRequest {
  session?: Session    // 调用会话；其不可变 cwd 成为工作区边界
  mode?: SandboxMode   // 显式批准的模式覆盖
}
```

关键设计点：`workspaceRoot` 来自会话的不可变 cwd。root 的规范化分两步：

```
1. 文件系统语义规范化（解析 symlink/..）
2. 词法规范化（处理 . 和 .. 等路径段）
```

为什么要两步？因为包含 `symlink/..` 的 cwd 需要标识进程实际运行的目录，而不是符号链接路径。如果只做词法规范化，`/home/user/link/..` 会被错误地规范化为 `/home/user`，而实际目标可能是完全不同的目录。

`ctx.sandboxPolicy.resolve()` 的优先级链：

```
1. 显式批准的 mode 覆盖（用户审批后重试时携带）
   ↓ 如果没有
2. 会话策略
   ↓ 如果没有
3. 部署配置回退（没有 agent 时）
```

> 金句：策略跟着会话走，不跟着进程走。两个并发会话可以向同一个 Provider 请求不同边界，不需要改变 Provider 状态——这是逐调用设计的核心价值。

## 13.4 三个平台后端实现

dsh-sandbox-local 提供三个平台的原生隔离后端。来自 packages/sandbox/sandbox-local/src/profiles.ts 的真实代码：

**Linux：bwrap + Landlock**

```ts
// bwrap 命令行参数
export function bwrapProfileArgs(policy: SandboxPolicy): string[] {
  const args = [
    '--ro-bind', '/', '/',    // 根文件系统只读挂载
    '--dev', '/dev',           // 挂载 /dev
    '--proc', '/proc',         // 挂载 /proc
    '--die-with-parent'        // 父进程退出时杀子进程
  ]
  if (policy.mode === 'workspace-write') {
    args.push('--tmpfs', '/tmp')                        // /tmp 用 tmpfs
    args.push('--bind', policy.workspaceRoot, policy.workspaceRoot)  // 工作区可写挂载
  }
  return args
}
```

```ts
// Landlock 授权参数
export function landlockProfileArgs(policy: SandboxPolicy): string[] {
  const readWrite = ['/dev/null']
  if (policy.mode === 'workspace-write') {
    readWrite.push('/tmp', policy.workspaceRoot)
  }
  return landlockGrantArgs({ readOnly: ['/'], readWrite })
}
```

bwrap 做命名空间隔离（挂载隔离），Landlock 做内核级文件访问控制。两者配合使用：bwrap 创建隔离的文件系统视图，Landlock 在内核层面强制执行写入限制。

**macOS：Seatbelt（sandbox-exec）**

```ts
export function seatbeltProfileArgs(policy: SandboxPolicy): string[] {
  const forms = [
    '(version 1)',
    '(allow default)',
    '(deny file-write*)',
    `(allow file-write* (literal "${sbplString('/dev/null')}))`
  ]
  const roots = writableRoots(policy)
  if (roots.length > 0) {
    forms.push(`(allow file-write* ${roots.map(root => `(subpath "${root}")`).join(' ')})`)
  }
  return ['-p', forms.join(' ')]
}
```

Seatbelt 用 SBPL（Seatbelt Policy Language，Seatbelt 策略语言）声明允许/拒绝的路径。策略逻辑：默认允许，拒绝所有写入，然后显式允许 `/dev/null` 和工作区根目录。

**Windows：ACL 受限令牌**

Windows ACL（Access Control List，访问控制列表）runner 给子进程一个受限的安全令牌。`read-only` 模式不授予任何显式可写根目录，因环境 ACL 缺口报告 partial。

三个后端的对比：

| 维度 | Linux bwrap+Landlock | macOS Seatbelt | Windows ACL |
|---|---|---|---|
| 隔离机制 | 命名空间 + 内核 LSM | 内核沙箱策略 | 受限令牌 + ACL |
| read-only 可写区 | /dev/null | /dev/null | 无 |
| workspace-write 可写区 | /tmp + workspace | /tmp + workspace | workspace |
| 完整性 | full（新内核）/ partial（旧 Landlock） | full | partial |
| 进程隔离 | 是（命名空间） | 部分 | 部分 |

容器、microVM（微型虚拟机）和远程执行（如 E2B）是同级实现，不是 `ctx.sandbox` 的 Provider——它们是完整的执行环境替代方案。

## 13.5 沙箱在工具链中的位置

沙箱不是在工具内部调用的，而是在 `tools/execute` 事件链中作为 wrapper 注入。以 dsh-bash-sandbox 为例，来自 packages/shell/bash-sandbox/src/index.ts：

```ts
export class SandboxBashExecutor extends LocalBashExecutor {
  static override inject = ['subprocess', 'sandbox', 'sandboxPolicy']
  
  // 每进程隔离事实，保留到结算
  // Provider 可能对重叠调用报告不同的 enforcement 和诊断方言
  // 共享最新 wrap 值会导致针对错误事实分类进程
  private readonly processFacts = new Map<ShellProcess, {
    mode: ConfinedSandboxMode
    enforcement: SandboxEnforcement
    denialSignatures: readonly string[]
    runnerFailureRules: readonly RunnerFailureRule[]
    runnerProgram: string | undefined
    workdir: string
  }>()
}
```

注意 `processFacts` 用 Map 保留每个进程的隔离事实——注释说明了原因：Provider 可能对重叠调用报告不同的 enforcement，共享最新值会分类错误。

工具链中的执行流程：

```
模型请求执行 bash 命令
  |
  v
tools/pre-execute (waterfall)
  |-- permission-presets: 静态规则匹配
  |-- user-approval: 需要时人工审批
  |
  v
tools/execute (waterfall)
  |-- bash-sandbox 包装器:
  |     1. ctx.sandboxPolicy.resolve(session) 解析策略
  |     2. mode = danger-full-access -> 直接 spawn
  |     3. mode = read-only 或 workspace-write -> ctx.sandbox.run()
  |     4. 沙箱 Provider 包装 argv:
  |        Linux: bwrap --ro-bind / / ... -- bash -c "command"
  |        macOS: sandbox-exec -p "(deny file-write*)..." bash -c "command"
  |        Windows: 创建受限令牌进程
  |     5. 执行命令，收集输出
  |     6. 记录 mode + enforcement 到 processFacts
  |
  v
tools/post-execute (waterfall)
  |-- 结果处理
```

dsh-bash-sandbox 和 dsh-bash-local 是两个平行的 Provider，消费方通过 cordis.yml 选择：

```yaml
# 本地直接执行（无沙箱，信任环境）
- name: '@deepseek-ai/dsh-bash-local'

# 或沙箱执行（有文件效果隔离）
- name: '@deepseek-ai/dsh-bash-sandbox'
```

两者实现同一个 `ctx.shell` Service Definition，消费方（dsh-tool-bash）不感知差异。bash-sandbox 的 inject 多了 `sandbox` 和 `sandboxPolicy`——这是唯一区别。

源码原文（packages/shell/bash-sandbox/src/index.ts）：

```ts
// Plugin config: 本地执行器的旋钮，原样继承。
// 沙箱策略（默认 mode 和回退 workspace-write root）不在这里——
// 它在 ctx.sandboxPolicy 上，由它为每个调用的会话解析 mode 和 cwd。
// runner 选择同样是 ctx.sandbox provider 的 config，不是本执行器的。
export type Config = LocalConfig
```

这个注释揭示了一个重要的设计原则：策略不属于执行器，属于独立的策略服务。

## 13.6 权限审批与沙箱的协作

dsh 的权限系统（permission-presets、user-approval）和沙箱是协作关系，各管一件事：

| 层 | 包 | 职责 | 介入时机 | 机制 |
|---|---|---|---|---|
| 权限预设 | dsh-permission-presets | 静态规则匹配 | tools/pre-execute | allow/deny/ask |
| 用户审批 | dsh-user-approval | 人工确认 | tools/pre-execute | ask 后追问 |
| 沙箱 | dsh-sandbox-local | 文件效果隔离 | tools/execute | argv 包装 |
| 单调守卫 | dsh-tools（内置） | 不可推翻否决 | tools/execute | guard() |
| 环境清理 | dsh-bash-local | env 脱敏 | 执行前 | ENV_OVERRIDES |

用户审批后的重试会携带显式 mode 覆盖。比如默认 `workspace-write` 被拒，用户审批后以 `danger-full-access` 重试——这时 `SandboxPolicyRequest.mode` 为 `danger-full-access`，Provider 直接 spawn 原始 argv，不经过沙箱。

审批流程的状态转换：

```
工具调用请求
  |
  v
permission-presets 判断
  |-- allow -> 继续执行
  |-- deny -> 拒绝，返回 deny 原因
  |-- ask -> 转给 user-approval
                |
                v
          用户审批
            |-- 批准 -> 携带 mode 覆盖重试
            |-- 拒绝 -> 返回 deny
            |-- 忽略 -> 保持原策略
```

> 金句：权限问「能不能做」，沙箱管「做了能影响什么」。一个管决策，一个管效果——分层不重叠。

## 13.7 防御性模式：安全相关的规则

dsh 的防御性模式文档（docs/defensive-patterns.zh.md）列出了七条规则，其中两条直接关于安全：

**规则 6：绝不将环境变量或可预测路径暴露给不可信输出**

文档原文的要点：

```
- 清 env 移除 *KEY* / *SECRET* / *TOKEN* / *PASSWORD*
- 临时/spill 文件放 0700 私有目录、随机文件名
- 'wx' / 0o600 独占打开
```

这意味着工具执行时，环境变量中的 API Key 不会泄露给子进程。bash-local 的实现（packages/shell/bash-local/src/index.ts）硬编码了 `ENV_OVERRIDES`：

```ts
const ENV_OVERRIDES = {
  NO_COLOR: '1',
  TERM: 'dumb',
  PAGER: 'cat',
  GIT_PAGER: 'cat',
}
```

这些覆盖让终端输出更适合程序化处理（禁用颜色、禁用分页器），同时 dsh 在传递环境变量给子进程前会做清理，移除匹配 `*KEY*`、`*SECRET*`、`*TOKEN*`、`*PASSWORD*` 模式的变量。

**规则 7：用 unlink 删除链接形态路径**

```ts
// 防止跟随符号链接删除意外目标
if (lstatSync(path).isSymbolicLink()) {
  unlinkSync(path)    // 链接用 unlink
} else {
  rmSync(path, { recursive: true })  // 真实目录才用递归删除
}
```

文档补充：Windows junction 用 `rmSync` 会抛 `ERR_FS_EISDIR`——需要特殊处理。这条规则防止的安全事故：符号链接指向 `/`，递归删除会擦掉整个文件系统。

## 13.8 沙箱 Provider 接口与自定义后端

如果你想写自己的沙箱后端（比如用 Docker 做隔离），需要实现 `ctx.sandbox` 的 Service Definition。核心接口：

```
ctx.sandbox.run(argv, options, policy) -> SandboxResult
```

输入：
- argv：命令数组（如 `['bash', '-c', 'ls -la']`）
- options：执行选项（env、cwd 等）
- policy：SandboxExecutionPolicy（mode、workspaceRoot、sessionId）

输出：SandboxResult（exit code、stdout、stderr、enforcement）

三个内置后端都遵循这个接口。一个 Docker 后端可以这样实现：

```ts
import { SandboxService, type SandboxPolicy, type SandboxResult } from '@deepseek-ai/dsh-sandbox'

class DockerSandbox extends SandboxService {
  async run(argv: string[], options: ExecOptions, policy: SandboxPolicy): Promise<SandboxResult> {
    if (policy.mode === 'danger-full-access') {
      return spawnDirectly(argv, options)
    }
    
    const dockerArgs = [
      'docker', 'run', '--rm',
      '--read-only',  // 只读根文件系统
    ]
    
    if (policy.mode === 'workspace-write') {
      dockerArgs.push('-v', `${policy.workspaceRoot}:/workspace:rw`)
      dockerArgs.push('--workdir', '/workspace')
    }
    
    // Docker 额外可限制网络（超出沙箱词汇表但 Docker 可做）
    dockerArgs.push('--network', 'none')
    dockerArgs.push('dsh-sandbox:latest')
    dockerArgs.push(...argv)
    
    const result = await spawnDirectly(dockerArgs, options)
    return {
      ...result,
      enforcement: 'full' as const  // Docker 容器隔离是完整的
    }
  }
}
```

组装到 cordis.yml：

```yaml
# 用 Docker 沙箱替代本地沙箱
- name: '@my-org/dsh-sandbox-docker'

# bash-sandbox 仍然用官方的，它只依赖 ctx.sandbox 接口
- name: '@deepseek-ai/dsh-bash-sandbox'
```

bash-sandbox 代码一行不改——它只依赖 `ctx.sandbox` 接口，不依赖具体后端。

> 金句：沙箱是 Seam，意味着安全方案可替换。Linux 用 Landlock，macOS 用 Seatbelt，你还可以加 Docker——消费方代码一行不改。

## 13.9 凭据隔离：机密不进配置

dsh 的凭据服务（dsh-credentials / dsh-credentials-local）是安全层的另一个重要组成部分。来自子系统文档（docs/subsystems/credentials.zh.md）：

```ts
// 凭据引用是 POSIX 风格环境变量名
type CredentialRef = Branded<'CredentialRef'>

// 解析结果
interface ResolvedCredential {
  value: string    // 非空机密值
  source: string   // 提供方定义的来源层 id
}
```

核心设计：配置文件只携带引用（如 `DEEPSEEK_API_KEY`），不携带值。值归凭据 Provider 所有，消费方每个操作解析一次引用。

文档原文的关键点：

> LLM adapter resolves once per model request, so rotated credentials take effect on the very next request without any restart.

这意味着：API Key 轮换后不需要重启 dsh——下一次模型请求会自动解析到新值。

凭据来源层的优先级（dsh-credentials-local）：

```
1. env          -- 当前进程环境变量
2. project-env  -- 项目 .env 文件
3. file         -- $DSH_HOME/.credentials.yaml
4. user-env     -- 用户级环境变量
```

`describe(ref)` 方法在不暴露值的前提下回应配置界面：引用当前是否可解析、来自哪一层、`set` 当前能否成功。本地提供方把由当前进程环境供值的引用报告为 `writable: false`——因为写入文件不会覆盖环境变量的值。

## 13.10 安全层速查

完整的安全层全景：

| 层 | 包 | 职责 | 机制 |
|---|---|---|---|
| 权限预设 | dsh-permission-presets | 静态规则匹配 | tools/pre-execute |
| 用户审批 | dsh-user-approval | 人工确认 | tools/pre-execute |
| 沙箱 | dsh-sandbox / dsh-sandbox-local | 文件效果隔离 | tools/execute |
| 单调守卫 | dsh-tools（内置） | 不可推翻否决 | tools/execute |
| 环境清理 | dsh-bash-local | env 脱敏 | 执行前 |
| 凭据隔离 | dsh-credentials-local | 机密不进配置 | 凭据服务 |
| spill 保护 | dsh-spill-policy | 工具输出溢出处理 | tools/code-dispatch-log |

## 本章小结

| 要点 | 说明 |
|---|---|
| 沙箱词汇表 | 只管文件效果，网络和进程可见性不在范围内 |
| 三种模式 | read-only / workspace-write / danger-full-access |
| 逐调用策略 | workspaceRoot 来自会话 cwd，并发会话互不干扰 |
| 三个平台后端 | Linux bwrap+Landlock / macOS Seatbelt / Windows ACL |
| partial 强制执行 | 旧 ABI 或 ACL 缺口，消费方需区分 full/partial |
| 沙箱是 Seam | 可替换后端，消费方不感知 |
| 安全分层 | 权限审批管决策，沙箱管效果，凭据管机密，不重叠 |
| 凭据不进配置 | 配置只携带引用，值归 Provider，每次请求解析 |

> 我是怕浪猫，第 13 章写完。dsh 的安全层不复杂，但设计很精巧——每一层只管一件事，组合起来形成完整边界。
>
> 有问题评论区聊，有纠错欢迎指出。如果这篇对你有帮助，收藏起来——部署 dsh 到生产时这张安全层速查表最好用。
>
> 下一章我们拆解 subagent（子代理）和 workflow（工作流）——agent 如何编排 agent。
>
> 系列进度：13/16 ｜ 未完待续

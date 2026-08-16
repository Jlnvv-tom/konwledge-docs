# 第3章：Profile / Bundle / Patch——dsh 的装配系统

> 系列：DeepSeek Harness 源码实战 ｜ 进度 3/16
> 原文仓库：https://github.com/deepseek-ai/deepseek-harness

改一行配置，整个产品的形态就变了。

上一章我们讲了 Cordis 插件引擎，知道了 dsh 的所有功能都是插件。但你可能一直在想一个问题：这些插件是怎么被组装到一起的？谁决定加载哪些插件、谁覆盖谁？这一章就来拆 dsh 的装配系统——三个概念、一条启动链、一套替换语义。

我是怕浪猫，这一章我们深入 `apps/cli/src/` 和 `packages/boot/` 的源码，看 dsh 从一行命令到一棵插件树，中间到底发生了什么。

## 3.1 三个概念辨析：Bundle / Profile / Patch

dsh 的装配系统有三个核心概念。先用一句话定义每一个，再展开讲。

- **Bundle（组合包）**：Cordis 配置项和挂载代码的分发格式。它是一组插件的「打包」，插入的内容始终可以被上层 patch 覆盖。在自己的 `package.json` 的 `dsh.bundle` 字段中声明自己的 patch 文件路径。
- **Profile（装配档案）**：存放在 Harness home 中的具名组装。它列出自己叠放的组合包（`dsh.profile` 字段），存放自己安装的树外插件，并保存用户自己的 `cordis.patch.yml`。`web` 和 `headless` 作为模板随发行版交付。
- **Patch（补丁）**：按 id 定位某个条目并替换其整个 config（配置），或插入新条目。不是深合并，是整行替换。

三者之间的关系可以这样理解：

```
Profile（装配档案）= 一份组装清单
  │
  ├── bundles 列表（按顺序）
  │     ├── dsh-base（基础层：模型适配器、工具、持久化、沙箱、审批策略、设置、凭据、遥测）
  │     ├── dsh-web-app（Web 应用层：host、API gateway、HMR）
  │     └── dsh-headless（无服务器的单次运行器）
  │
  ├── cordis.patch.yml（用户层覆盖）
  │     └── 按 id 替换或插入条目
  │
  └── 树外插件（通过 dsh plugin 安装）

Patch 层级（自底向上叠加）:
  空配置 []
    → Bundle 的 patch（按 profile 列出的顺序）
    → Profile 自己的 cordis.patch.yml
    → Home 级 $DSH_HOME/cordis.patch.yml
    → --patch 命令行临时 overlay
    → 最终配置树
```

对比表：

| 概念 | 是什么 | 谁创建 | 可被谁覆盖 |
|---|---|---|---|
| Bundle | 一组插件的打包分发 | dsh 官方或第三方 | Profile patch / Home patch / 命令行 overlay |
| Profile | 一份组装清单 | 用户（或随发行版交付的模板） | 上层 patch |
| Patch | 按 id 整行替换 | 用户编写 | 更上层的 patch |

三个概念在各自的 `package.json` 中通过 `dsh` 字段声明：`dsh.profile` 列出一个 profile 的组合包，`dsh.bundle` 指向一个组合包的 patch 文件。

> 金句：Bundle 是砖，Profile 是图纸，Patch 是你拿笔在图纸上画的修改。

## 3.2 启动链拆解：从 bin.ts 到插件树

现在来追踪一次完整的启动过程。以 `dsh --profile web` 为例。

### 第一步：参数解析

入口在 `apps/cli/src/bin.ts`，上一章已经看过它的三模式分发。这里聚焦 profile 模式：

```typescript
// apps/cli/src/bin.ts（节选）
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
  // ...
}
```

`parseDshArgs` 返回一个判别联合（discriminated union），`mode` 字段决定走哪个分支。profile 模式下，它把环境快照、profile 名、patch overlay 路径、内部参数全部传给 `runProfile`。

### 第二步：合成 patch 层

`runProfile` 在 `apps/cli/src/profile-boot.ts` 中定义。它先调用 `composeProfile` 合成 patch 层：

```typescript
// apps/cli/src/profile-boot.ts（节选）
function composeProfile(name: string, patchFiles: readonly string[]): ComposedProfile {
  const profile = prepareProfile(name)
  const homePatches = loadOptionalPatches(NAME, homePatchPath()) ?? []
  const overlays = patchFiles.flatMap(file => loadOverlayPatches(NAME, resolve(file)))
  const bundlePatches = profile.layers.flatMap(layer => layer.patches)
  const rows = new Map<string, EntryOptions>()
  for (const row of composeEntries([bundlePatches, profile.patches, homePatches, overlays])) {
    if (typeof row.id === 'string') rows.set(row.id, row)
  }
  // ... agent-presets 根路径注入 + 遥测开关
  return { profile, bundlePatches, homePatches, overlays: composedOverlays, rows }
}
```

这段代码的逻辑是：

1. `prepareProfile(name)` 加载 profile，读取它的 bundles 列表
2. `homePatches` 加载 Home 级 patch（`$DSH_HOME/cordis.patch.yml`）
3. `overlays` 加载命令行 `--patch` 指定的临时 overlay
4. `bundlePatches` 从 profile 的各 bundle 层提取 patch
5. `composeEntries` 把四层 patch 合成最终条目列表，并建立 id 索引

注意 `composeEntries` 的参数顺序：`[bundlePatches, profile.patches, homePatches, overlays]`。这就是叠加顺序——后面的覆盖前面的。

### 第三步：重写根配置

`prepareProfile` 里有一个容易被忽略的细节：

```typescript
// apps/cli/src/profile-boot.ts（节选）
export function prepareProfile(name: string, userLayer = true): Profile {
  healProfilesModuleFallback(INSTALL_ANCHOR)
  const profile = loadProfile(NAME, name, INSTALL_ANCHOR, undefined, { userLayer })
  writeFileSync(join(profile.dir, PROFILE_ROOT_FILENAME), PROFILE_ROOT_CONFIG)
  return profile
}
```

`PROFILE_ROOT_CONFIG` 是一个空列表 `[]`，每次启动都重写。为什么？因为 Cordis 的 Loader 有一个回写机制——插件自我卸载时会持久化当前配置树。如果不重置，上次组合的行会被固化进根文件，下次启动时每个 bundle 的插入操作会重复一遍。

`PROFILE_ROOT_CONFIG` 的内容就是两行注释加一个空数组：

```yaml
# dsh profile root — an empty entry list. The tree is composed as patches:
# each bundle in package.json's dsh.profile.bundles, then cordis.patch.yml, then any
# --patch overlays. Edit cordis.patch.yml, not this file.
[]
```

注释明确说了：整个配置树是 patch 叠加出来的，不要直接编辑这个文件。

> 金句：每次启动都从空列表开始，就像每天早上把白板擦干净。这不是强迫症，是防止状态累积的工程纪律。

### 第四步：boot 挂载

合成完 patch 层后，调用 `boot` 函数挂载配置树：

```typescript
// apps/cli/src/profile-boot.ts（节选）
const ctx = await boot(NAME, rootConfig, structuredClone(allPatches(composed)), (hostCtx) => {
  app.current = hostCtx
  hostCtx.provide(DSH_LAUNCH_ENVIRONMENT_KEY, options.environment)
  provideCmdline(hostCtx, {
    args: options.args,
    exit: code => void shutdown.shutdown(code),
  })
})
```

注意三个细节：

1. `structuredClone(allPatches(composed))`——深拷贝 patch 列表。注释解释了原因：Include 会把 insert 行按引用插入挂载树，后续的 id 定向 patch 会原地修改这些对象。如果不拷贝，用户层的覆盖会渗透进 bundle 的内存对象，导致撤销覆盖时无法恢复。
2. `(hostCtx) => { ... }` 是 host 回调，在配置树条目挂载之前执行，用来提供全局服务（环境快照、命令行参数、退出接口）。
3. `boot` 返回 root Context，也就是 Cordis 插件树的根节点。

### 第五步：HMR 热重载

boot 完成后，还会设置 patch 文件的热重载监视：

```typescript
// apps/cli/src/profile-boot.ts（节选）
await watchUserPatches(ctx, {
  binName: NAME,
  filename: composed.profile.patchPath,
  compose: composeLive,
})
await watchUserPatches(ctx, {
  binName: NAME,
  filename: homePatchPath(),
  compose: composeLive,
})
```

两个 watcher 分别监视 profile 级和 home 级的 `cordis.patch.yml`。文件变更时，调用 `composeLive` 重新合成 patch 层（不包含 bundle 层，因为 bundle 层不可热重载），然后通知 Cordis Loader 重新挂载受影响的条目。

`composeLive` 的实现有一个重要的克隆逻辑：

```typescript
const composeLive = (): PatchOptions[] => structuredClone([
  ...composed.bundlePatches,
  ...loadOptionalPatches(NAME, composed.profile.patchPath) ?? [],
  ...loadOptionalPatches(NAME, homePatchPath()) ?? [],
  ...composed.overlays,
])
```

每次重新合成都会 fresh clone（全新克隆），原因和第四步一样——防止 insert 行的引用别名导致状态渗透。

### 启动链总结

```
1. dsh --profile web
2. parseDshArgs → mode='profile', profile='web'
3. runProfile → composeProfile
   3a. prepareProfile → loadProfile + 重写空根配置
   3b. 加载 homePatches + overlays + bundlePatches
   3c. composeEntries 合成最终条目列表
4. boot(NAME, rootConfig, patches, hostCallback)
   4a. Cordis Loader 读取配置树
   4b. 按条目实例化插件
   4c. 每个插件注册 ctx 服务
   4d. 返回 root Context
5. watchUserPatches × 2（profile 级 + home 级 HMR）
6. web-app bundle 的插件启动 Web Server → http://127.0.0.1:3080
```

## 3.3 Patch 的替换语义：按 id 整行替换，不是深合并

这是 dsh 装配系统里最容易踩坑的点。

Patch 的替换语义是「按 id 定位某个条目，替换其整个 config」。注意：**整个 config**，不是深合并（deep merge），不是部分覆盖。如果你 patch 一个条目，你提供的 config 就是最终结果，原来的 config 会完全消失。

来看一个对比。假设 bundle 层定义了一个条目：

```yaml
# bundle 层
- id: tool-bash
  config:
    timeoutMs: 30000
    retryPolicy:
      maxRetries: 3
      backoffMs: 1000
    env:
      DSH_SHELL: bash
```

现在你想改 timeout，写了一个 patch：

**深合并语义（dsh 不这样工作）**：

```yaml
# 假想的深合并结果（不正确）
- id: tool-bash
  config:
    timeoutMs: 60000          # ← 被覆盖
    retryPolicy:              # ← 保留
      maxRetries: 3
      backoffMs: 1000
    env:                      # ← 保留
      DSH_SHELL: bash
```

**dsh 的实际语义（整行替换）**：

```yaml
# 实际结果：config 被整体替换
- id: tool-bash
  config:
    timeoutMs: 60000          # ← 只有这个
                               # ← retryPolicy 没了
                               # ← env 没了
```

如果你想改一个字段但保留其他字段，你需要在 patch 里把所有字段都写上。这是设计决策，不是 bug。

为什么这样设计？因为深合并的语义不直观——当有多层 patch 叠加时，深合并的行为会变得难以预测。整行替换虽然写起来更啰嗦，但结果完全可预测：你看到的就是最终值，不需要推断它是怎么合并出来的。

> 金句：深合并是便利贴，整行替换是合同。前者好写不好读，后者好读不好写。dsh 选择了好读。

查看实际配置树的命令：

```sh
dsh --profile web --dump-config
```

这会打印最终合成的配置树，让你确认哪些条目被加载、哪些被 patch 替换了。`--dump-default-config` 则只打印 bundle 层，不包含用户层和 overlay。

## 3.4 CLI 模式全览

dsh 的 CLI 有三个模式（在 `bin.ts` 的 switch 里）和两个语法糖（在 `args.ts` 里）。完整命令速查表：

| 命令 | 模式 | 说明 |
|---|---|---|
| `dsh --profile web` | profile | 启动 web profile |
| `dsh web` | profile | `--profile web` 的别名 |
| `dsh --profile headless "task"` | profile | 单次任务，打印结果退出 |
| `dsh --profile tui --patch ./extra.yml` | profile | 自定义 profile + 额外 overlay |
| `dsh --profile tui --resume <session>` | profile | 恢复指定会话（`--resume` 是内部参数） |
| `dsh --profile web --dump-config` | dump-config | 打印 web profile 的完整配置树 |
| `dsh --profile web --dump-default-config` | dump-config | 打印 web profile 的 bundle 层（不含用户层） |
| `dsh plugin --profile tui add <pkg>` | plugin | 给 tui profile 安装插件 |
| `dsh plugin --profile tui remove <pkg>` | plugin | 移除插件 |

每个模式的适用场景：

**profile 模式**：日常使用。启动一个 profile 的服务（Web Server、headless runner 等），参数传递给 profile 内部的应用插件。

**dump-config 模式**：调试和文档。不启动服务，只打印配置树。当你的 profile 行为不对时，先用这个看实际配置是不是你期望的。注意 dump-config 不接受应用参数（`--dump-config` 和内部参数互斥），因为配置树在应用参数注入之前就已经确定了。

**plugin 模式**：插件管理。把参数原样转发给 pnpm，在 profile 目录里执行。等价于 `cd $DSH_HOME/profiles/<name> && pnpm <args>`。

`web` 别名的定义：

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

注意 `rejectParentOptions('web')`——web 子命令不接受父命令的 `--profile`、`--patch`、`--dump-config`。这防止了 `dsh --profile tui web` 这种无意义的组合。

## 3.5 默认装配：dsh-base、dsh-web-app、dsh-headless

dsh 随发行版交付了三个 bundle，构成两种默认 profile。

### dsh-base：第一层基础

`dsh-base` 是每个 profile 的第一层。它包含：

| 内容 | 说明 |
|---|---|
| 模型适配器 | LLM 适配器注册到 ctx.llm |
| 工具 | 核心工具注册到 ctx.tools |
| 持久化 | 会话日志存储（JSONL（JSON Lines，每行一个 JSON 对象）/ SQLite） |
| 沙箱与审批策略 | 进程沙箱、文件系统约束、操作审批 |
| 设置 | ctx.settings 服务 |
| 凭据 | ctx.credentials 服务 |
| 遥测 | 可选的 OpenTelemetry 遥测 |

dsh-base 还负责平台门控。在 Windows（win32）上，只安装 PowerShell（pwsh）栈，bash-sandbox 和 tool-bash 被禁用。在 POSIX（Linux/macOS）上，只安装 bash 栈。这是通过 bundle 层的 `disabled` 字段按平台条件控制的。

### dsh-web-app：浏览器应用

`dsh-web-app` 在 dsh-base 之上增加：

- Web host（宿主端服务）
- API gateway（API 网关）
- 浏览器插件表（client 端模块注册）
- HMR（Hot Module Replacement，热模块替换）支持

`dsh web` 就是 `dsh-base + dsh-web-app` 的组合。

### dsh-headless：一次性运行器

`dsh-headless` 在 dsh-base 之上增加一个 headless runner——接收一个任务字符串，执行完毕后打印结果并退出。完全不带服务器。

`dsh --profile headless "run the tests"` 适合 CI（Continuous Integration，持续集成）场景：不需要 UI，不需要交互，跑完就走。

### 自定义 profile 步骤

如果你想创建自己的 profile：

1. 复制一个模板 profile 目录到 `$DSH_HOME/profiles/my-profile/`
2. 编辑 `package.json`，设置 `dsh.profile.bundles` 列出你需要的 bundle
3. 创建 `cordis.patch.yml`，按 id 替换或插入条目
4. 用 `dsh plugin --profile my-profile add <pkg>` 安装树外插件
5. 运行 `dsh --profile my-profile`
6. 用 `dsh --profile my-profile --dump-config` 检查配置树

首次使用一个新 profile 名时，dsh 会自动初始化模板。

> 金句：Profile 不是配置文件，是一份组装合同。你签字（声明 bundles），dsh 按合同交付（挂载插件树）。

## 本章小结

| 要点 | 说明 |
|---|---|
| Bundle | 一组插件的打包分发，插入的内容可被上层覆盖 |
| Profile | 具名组装清单，列出 bundles + 存放树外插件 + 保存 cordis.patch.yml |
| Patch | 按 id 整行替换条目的 config，不是深合并 |
| 叠加顺序 | 空 [] → bundle patches → profile patch → home patch → --patch overlay |
| 启动链 | parseDshArgs → runProfile → composeProfile → boot → HMR watcher |
| 根配置重写 | 每次启动重写为空 []，防止 Loader 回写导致配置膨胀 |
| structuredClone | patch 对象深拷贝，防止 insert 行引用别名导致状态渗透 |
| CLI 三模式 | profile（启动）/ dump-config（查看配置）/ plugin（管理插件） |
| 三个 bundle | dsh-base（基础）/ dsh-web-app（Web 应用）/ dsh-headless（一次性运行） |
| 平台门控 | win32 只装 pwsh 栈，POSIX 只装 bash 栈 |

## 下章预告

装配系统搞清楚了，插件树也挂起来了。下一章我们要深入 dsh 的数据核心——Session 会话日志。你会看到为什么 dsh 的聊天记录其实只是日志的一个投影，以及为什么这个设计决策影响深远。

> 我是怕浪猫，装配系统这一章信息量比较大，建议收藏后反复看。你的 agent 项目里，配置是怎么组装的？评论区聊聊。
>
> 系列进度：3/8 ｜ 下一章：Session 会话日志——单一事实源

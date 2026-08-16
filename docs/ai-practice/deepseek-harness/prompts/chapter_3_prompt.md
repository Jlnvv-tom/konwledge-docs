# 第3章写作 Prompt：Profile / Bundle / Patch——dsh 的装配系统

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh 装配系统的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-03.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 3/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- docs/architecture.zh.md 与 docs/development.zh.md 中的 profile / bundle / patch 定义：
  - Bundle（组合包）：Cordis 配置项 + 挂载代码的分发格式；dsh-base 是每个 profile 的第一层（模型适配器、工具、持久化、沙箱与审批策略、设置、凭据、遥测）。
  - Profile（装配档案）：Harness home 中具名组装，列出叠放的组合包、存放树外插件与用户自己的 cordis.patch.yml；web 和 headless 作为模板随发行版交付。
  - Patch（补丁）：按 id 定位条目并替换整个 config（非深合并）或插入新条目。
- 叠加顺序（自底向上）：空条目列表 → 各组合包 patch（按 profile 列出的顺序）→ profile 自身 cordis.patch.yml → home 级 $DSH_HOME/cordis.patch.yml → --patch 临时 overlay。
- 查看实际配置树：`dsh --profile web --dump-config`。
- apps/cli/src/bin.ts：三个模式分支（profile / plugin / dump-config），动态 import。
- apps/cli/src/profile-boot.ts：runProfile 装配入口。
- apps/cli/src/args.ts：parseDshArgs 参数解析。
- 三个 bundle：dsh-base、dsh-web-app（浏览器应用：web host、API gateway、浏览器插件表、HMR）、dsh-headless（一次性运行器，无服务器）。Windows 上 shell 栈按平台门控：win32 只装 pwsh 栈，POSIX 只装 bash 栈。
- CLI 模式表：dsh --profile <name>、--profile headless "job"、dsh web（别名 --profile web，默认 127.0.0.1:3080）、dsh plugin --profile <name> <pnpm args>。
- 首次使用自动初始化模板：$DSH_HOME/profiles/。

## 本章目录（按此组织小节）

- 3.1 三个概念辨析：Bundle / Profile / Patch（每个概念一句话定义 + 类比 + 表格对比；文字图展示三者在启动时的关系）
- 3.2 启动链拆解：从 bin.ts 到插件树（展示 bin.ts switch 代码与 profile-boot 装配流程；编号步骤化启动链）
- 3.3 Patch 的替换语义：按 id 整行替换，不是深合并（展示 cordis.patch.yml 示例；对比深合并 vs 整行替换的区别；为什么这样设计）
- 3.4 CLI 模式全览：profile / headless / web / plugin / dump-config（命令速查表 + 每个模式适用场景）
- 3.5 默认装配：dsh-base、dsh-web-app、dsh-headless（三个 bundle 职责表；平台门控 shell 栈说明；自定义 profile 步骤）

## 本章互动设计

- 3秒钩子（选一）：反常识型「改一行配置，整个产品的形态就变了」或数字冲击型「3 个配置概念，撑起一个可商用 Agent 平台」
- 文中提问：你希望你的 agent 产品支持几种形态？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第4章 Session 会话日志——为什么聊天记录只是日志的投影

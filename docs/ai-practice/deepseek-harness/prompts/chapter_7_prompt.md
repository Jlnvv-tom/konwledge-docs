# 第7章写作 Prompt：能力 Seam——可替换能力架构

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh 能力 Seam（可替换能力架构）的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-07.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 7/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- 能力 Seam 三段式：Service Definition（接口契约）/ Service Provider（实现，可替换）/ Consumer（模型面向工具）。参考 .agents/notes/implemented/architecture/2026-06-13-capability-seams.md 与 packages/*/README.zh.md。
- 各家族 README（中文）：
  - llm：llm 包承担 Service Definition + Consumer 双重角色（抽象服务、内容块词汇 text/reasoning/image/tool-call/tool-result、流式分片组装器）；提供方适配器注册到 ctx.llm（llm-deepseek、llm-pi-ai、token-meter、llm-retry）。
  - fs：Service Definition（规范化路径/URI、文本 I/O、原子变更原语）+ fs-local / fs-sandbox / e2b fs-e2b 提供方 + tool-fs / tool-fs-search 工具；fs-observation-policy 政策门禁插件；「文件 I/O 不设超时」设计说明。
  - shell：bash 能力家族——shell（执行器约定）、bash-local、bash-sandbox、pwsh-local、shell-env、tool-bash、tool-pwsh。
  - web：搜索/抓取 seam（Exa / Perplexity / DeepSeek 原生搜索 + HTTP fetch）。
  - subagent：subagent 提供方注册（subagent-inprocess、subagent-acp、subagent-codex、subagent-claude-code、subagent-dsh-sdk）+ tool-subagent 系列。
- 替换 Provider 即改变产品：文件系统与进程提供方共享同一执行世界，把 fs/subprocess 指向远程沙箱（E2B），Bash/PTY/LSP 一并搬移，无需提供方专用 fork（packages/e2b/README.zh.md）。
- 源码示例：packages/fs/fs/src 下 Service Definition；packages/llm/llm/src/content.ts（内容块词汇）、llm/src/assembler.ts（流式分片组装）。
- 工具注册：ToolDefinition 注册到 ctx.tools；provider 注册到 ctx.<key>（如 ctx.fs、ctx.llm、ctx.shell、ctx.web）。

## 本章目录（按此组织小节）

- 7.1 三段式：Service Definition / Service Provider / Consumer（概念 + 为什么叫 seam（接缝）；文字图展示三层关系；表格：三段职责对比）
- 7.2 五大 Seam 拆解：llm / fs / shell / web / subagent（每个 Seam 一段：Definition 是什么、有哪些 Provider、有哪些 Consumer 工具；内容块词汇与流式分片组装器代码展示）
- 7.3 替换 Provider 即改变产品：E2B 远程执行世界（解释共享执行世界原理；fs-e2b / subprocess-e2b 如何让 bash/terminal/lsp 一并搬移；展示 e2b README 关键说明）
- 7.4 Seam 的注册与发现：ctx 键与提供方注册（ctx.<key> 注册机制；provider 注册代码示意；表格：各 Seam 的 ctx 键与提供方清单）
- 7.5 实战：手写一个 Seam 提供方（以 fs 或 llm 为例，给出注册一个自定义 Provider 的步骤 + 骨架代码 + 接入 profile 的方法；收藏触发点：可照抄模板）

## 本章互动设计

- 3秒钩子（选一）：反常识型「一个文件系统接口，撑起了 Bash、终端、LSP 一整条能力链」或数字冲击型「5 大 Seam，拆掉重装就是另一个产品」
- 文中提问：你的 agent 架构里，哪些能力被写死了？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第8章 多端服务与扩展生态——同一个 runtime，六种打开方式

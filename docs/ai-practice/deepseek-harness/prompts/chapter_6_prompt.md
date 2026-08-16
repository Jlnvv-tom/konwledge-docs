# 第6章写作 Prompt：工具执行流水线——策略与执行解耦

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh 工具执行流水线的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-06.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 6/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- packages/core/tools/src/index.ts：
  - 'tools/pre-execute' 与 'tools/post-execute' 都是 waterfall（Scoped<ToolRuntime>，next() 返回 PreToolDecision / PostToolDecision）；
  - finalizeContent（内容层最后不变量，post-execute 后立即、lossless 物化前）；
  - guards（AnonymousEntries<ToolGuard>）：单调执行守卫，pre-execute 之后求值，返回 string 即拒绝；guard 无 allow 能力，只能 deny 或 abstain；guardReason() 取第一个单调拒绝理由；
  - 调度器阶段：post-result（仍走 post-execute）/ final-result（绕过 post-execute）；「tool result blocked by post-execute policy」占位文本；
  - 'tools/result' 同步通知（冻结的权威结果）。
- 完整旅程：model 产生 tool-call → tool/call 会话事件 → tools/pre-execute（hooks、权限、沙箱、fs 守卫、审批）→ 单调 guards → tools/execute（timeout、retry、指标环绕 dispatch）→ 工具本体 execute() → fs/write-intent 或 fs/edit-intent 门禁（仅 tool-fs 变更）→ tools/post-execute（接受/阻断/替换/附加上下文）→ finalizeContent → tools/result（同步通知）→ 记录 tool/result 会话事件 → 注入 additionalContexts。
- docs/subsystems/tools.zh.md：工具子系统参考。
- 相关策略插件：guard/repeat-tool-reminder（重复调用建议提醒，作为 additionalContexts 随 post-execute 决策传递）、guard/timeout-policy（单次调用截止时间，注册 tools/execute 监听器）、spill/spill-policy（执行后 spill 策略）、fs-observation-policy（编辑前读取、版本防护）。
- 工具定义：ToolDefinition（schema、execute、presentResult、finalizeContent 等，见 tools/src/types.ts）。

## 本章目录（按此组织小节）

- 6.1 从 tool-call 到 tool/result 的完整旅程（编号步骤化全旅程 + 文字流水线图；每阶段一句话职责）
- 6.2 Pre-execute：hooks、权限、沙箱、审批（waterfall 中间件语义；展示 tools/src/index.ts 中 pre-execute 事件声明代码；策略如何在此挂载）
- 6.3 单调守卫 Guard：deny / abstain（展示 guards 注册与 guardReason 代码；为什么 guard 只能拒绝不能放行；对比 pre-execute 与 guard 的分工）
- 6.4 Post-execute 决策：接受、阻断、替换、附加上下文（PostToolDecision 类型；阻断占位文本；展示 post-execute 事件声明代码）
- 6.5 超时、重试、spill 与内容规范化（tools/execute 的 timeout/retry 环绕；timeout-policy 与 repeat-tool-reminder 插件；spill 大输出；finalizeContent 内容规范化时机；表格：各阶段策略插件清单）

## 本章互动设计

- 3秒钩子（选一）：反常识型「工具调用不是黑盒，是一条分层流水线」或痛点共鸣型「权限、沙箱、审批写进每个工具里？那代码早就炸了」
- 文中提问：你的工具函数里，权限检查写在哪？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第7章 能力 Seam——替换一个 Provider 就能改变整个产品

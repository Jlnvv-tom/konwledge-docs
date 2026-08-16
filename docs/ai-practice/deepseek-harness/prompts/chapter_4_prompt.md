# 第4章写作 Prompt：Session 会话日志——单一事实源

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh Session 会话日志的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-04.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 4/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- packages/core/session/src/types.ts：SessionEventMap 完整定义（turn/start、turn/end、step/start、step/end、user/message、assistant/chunk、assistant/message、tool/call、tool/result、todo/write、request/header、request/context、session/end-seed 等）；SessionEvent 判别联合（type/seq/time/data）；SurfaceEventType = user/message | assistant/message | tool/result；SurfaceOp = append | replace；SurfaceIntent（surfaceOp + sourceEventSeqs）。
- 核心设计：Session 是内存中的仅追加事件日志；消息历史从日志派生；每个事件 lossless JSON、seq 连续；持久化可原样存储规范日志。
- 核心不变量：模型可见即已记录（新增模型可见输入需扩展 SessionEventMap 并从日志渲染）。
- docs/subsystems/session.zh.md：会话语义、事件、派生态。
- 持久化家族 packages/session/：session-persistence、session-checkpoint-policy、session-persistence-jsonl、session-persistence-sqlite；投影家族 session-projection、session-projection-cache、session-stats。
- 重放/fork/恢复都从同一事件流导出。

## 本章目录（按此组织小节）

- 4.1 为什么是 append-only 事件日志而不是消息数组（对比「消息数组 vs 事件日志」两种模型；append-only 的好处：可重放、可审计、可派生；文字对比图）
- 4.2 SessionEventMap 全解析（列出主要事件类型表格：事件名/含义/载荷；展示 types.ts 中 SessionEventMap 真实代码片段并逐段解释）
- 4.3 核心不变量：模型可见即已记录（解释 invariant 含义；新增模型可见输入为什么必须扩展 SessionEventMap；金句：日志即真相）
- 4.4 Surface 机制：append / replace、sourceEventSeqs 溯源（解释三种 surface 事件、compaction 如何用 replace 压缩历史；展示 SurfaceOp 与 SurfaceIntent 代码）
- 4.5 从日志派生一切：消息历史、回放、fork、投影、持久化（投影家族表；JSONL/SQLite 后端对比；展示一次完整事件序列的「日志回放文字图」）

## 本章互动设计

- 3秒钩子（选一）：反常识型「你以为的聊天记录，其实只是日志的一个投影」或痛点共鸣型「做过 agent 项目的人都知道，上下文管理有多痛」
- 文中提问：你的 agent 项目里，历史记录存在哪？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第5章 Turn / Step 循环——一次模型请求里藏着多少个事件

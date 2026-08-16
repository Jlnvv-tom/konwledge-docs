# 第1章写作 Prompt：认识 DeepSeek Harness——一个插件化的 Agent Runtime 平台

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 DeepSeek Harness（dsh）项目介绍的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-01.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 1/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- 根 README：项目定位「deepseek-harness — 用于 coding agent 的插件化 agent runtime（pluginized agent runtime for coding agents）」，版本 0.1.0-rc.5，MIT License，DeepSeek AI 开发，开发者预览（可能破坏性变更）。
- 设计思想对应论文《A Programming Paradigm for Spatiotemporal Composability》（https://github.com/cordiverse/paper）。
- 运行方式：`npx @deepseek-ai/dsh web`；源码运行需 Node.js（Node 22.19+ / 24+）、pnpm 11.7.0，`pnpm install && pnpm run build && pnpm dsh web`。
- 入口源码 apps/cli/src/bin.ts：动态 import 按模式分发（profile / plugin / dump-config），readVersion() 读 package.json 版本。
- 架构关键点：无特权内核、一切皆插件、profile+bundle+patch 装配、session 日志单一事实源、能力 seam。
- 服务方式：CLI Web（dsh web，默认 127.0.0.1:3080）、Headless（dsh --profile headless "task"）、Web GUI（host+client 双半包）、ACP（Agent Client Protocol）、SDK（stdio JSON-RPC）、interaction（人机协作）。
- 快速上手细节：启动后设置 → 模型填 API 密钥（无需重启），选工作区即可对话；权限策略外的操作先询问审批。

## 本章目录（按此组织小节）

- 1.1 什么是 Harness（驾驭层）：从 LLM 到可用 Agent 的最后一块拼图（解释 harness 概念、为何需要运行时层、与提示词工程的区别；给出「LLM 裸模型 vs Harness 化 Agent」文字对比图）
- 1.2 dsh 项目定位与现状：版本、许可、开发者预览期、仓库结构总览（apps/、packages/、docs/、examples/ 布局说明）
- 1.3 与 Claude Code / Codex / OpenCode 的定位差异（表格对比：插件化/可组合、开源可替换 provider、ACP/SDK 程序化接入、多 profile 形态）
- 1.4 快速上手：npx 运行、源码构建、第一个会话（含 bin.ts 模式分发代码展示）
- 1.5 总体架构一览：CLI 入口 → boot 装配 → profile 叠层 → Cordis 插件树 → 服务表面（文字版架构图 + 每层一句话职责）

## 本章互动设计

- 3秒钩子（选一）：反常识型「你以为 coding agent 是一个程序，其实它是一个可以拼装的运行时平台」或数字冲击型
- 文中提问：每节结尾可问「你用的 coding agent 是单体还是插件化？」
- 结尾 CTA：收藏引导 + 互动（评论区聊聊你用的 agent 工具）+ 追更（关注怕浪猫，下期拆 Cordis 插件引擎）
- 下章预告：第2章 Cordis 插件引擎——为什么 dsh 敢把所有功能都做成插件

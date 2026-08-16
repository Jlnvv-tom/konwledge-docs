# 第2章写作 Prompt：Cordis——驱动 dsh 的插件引擎

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 Cordis 插件引擎的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-02.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 2/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- docs/cordis-primer.zh.md：Cordis 入门（插件 = 实现 Service 的对象；上下文 = 服务的容器；inject 声明依赖；类型化事件；注册 = 可逆副作用）。
- 事件分发四模式：emit（观察、按注册顺序、无返回值）、waterfall（中间件、next() 委托、有返回值）、parallel（并行 await）、serial（顺序 await、有返回值）。
- 设计论文《A Programming Paradigm for Spatiotemporal Composability》（https://github.com/cordiverse/paper）。
- dsh 使用 Cordis 的体现：Scoped 上下文（packages/core/scope）、mount 与插件树、service 占据稳定 ctx.<key>（ctx.tools、ctx.llm、ctx.sessions）。
- 依赖方向：Cordis 包来自 npm `cordis`（或 @deepseek-ai/cordis fork，代码中 import 自 '@deepseek-ai/cordis'）。
- 源码佐证：packages/core/agent-loop/src/agent.ts 中 dispatch.waterfall('agent/pre-step', ...)、dispatch.serial('agent/turn-stopping', ...)；packages/core/tools/src/index.ts 中 'tools/pre-execute'、'tools/post-execute' waterfall 声明。

## 本章目录（按此组织小节）

- 2.1 Cordis 是什么：插件、上下文（Context）、服务注入（核心概念逐一解释；给出「插件/上下文/服务/事件」关系文字图）
- 2.2 事件分发四模式：emit / waterfall / parallel / serial（对比表格 + 每个模式一段文字示意 + 何时用哪个）
- 2.3 ctx 服务注册与依赖注入：Service 与 inject（解释服务占据 ctx 键、按 key 查找而非 import；给出 Service 注册伪代码或真实声明代码）
- 2.4 可逆副作用与生命周期：effect / on / reload（解释注册即副作用、卸载自动撤销；reload 热重载机制）
- 2.5 Cordis 在 dsh 中的落地：Scoped 上下文、mount 与插件树（引用 agent.ts 中 waterfall/serial 真实调用代码；说明插件树如何被装配、profile/bundle 如何变成插件）

## 本章互动设计

- 3秒钩子（选一）：反常识型「插件框架不是给前端用的吗？dsh 整个 Agent 运行时都跑在插件引擎上」或痛点共鸣型
- 文中提问：四模式里你猜哪个最容易被滥用？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第3章 Profile / Bundle / Patch 装配系统——改一行配置换掉整个产品形态

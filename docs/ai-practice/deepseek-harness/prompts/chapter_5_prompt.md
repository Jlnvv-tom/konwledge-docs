# 第5章写作 Prompt：Turn / Step 循环——agent-loop 源码拆解

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh agent-loop 的文章。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-05.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告 + 系列进度条（进度 5/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- packages/core/agent-loop/src/agent.ts：
  - phase 状态机（running 等）；pre-step 需在 running phase（"pre-step outside running phase" 报错）；
  - dispatch.waterfall('agent/pre-step', { messages: claimed, ...position, signal })；
  - dispatch.serial('agent/turn-stopping', { turn, signal })；
  - dispatch.waterfall('agent/request', ...) 提供 provider/model（"no provider/model: set AgentOptions.provider and AgentOptions.model or supply both via the agent/request waterfall"）；
  - inbox 事件：agent/inbox/inserted、agent/inbox/discarded、agent/inbox/claimed；agent/status、agent/error。
- packages/core/agent-loop/src/tool-calls.ts：executeToolCalls——exclusive 调用形成屏障、parallel 调用用有界滚动池；调度可重叠，但 policy/结果/结果上下文保持模型顺序；abort 记录合成错误结果保持重放有效。
- Turn 与 Step 定义（docs/subsystems/core.zh.md 或 session 文档）：step = 一次模型请求 + 它调用的工具；turn = 零个或多个 step，领取首条输入时打开、不再欠工作时关闭。
- 事件瀑布：agent/pre-step、agent/request、llm/stream 是 waterfall；agent/turn-stopping 是 serial。
- 模型可见上下文注入：agent.inject()（user/message 的 synthetic 来源：文件变更通知、子目录 AGENTS.md、skill 内容、cron 通知等）。

## 本章目录（按此组织小节）

- 5.1 Turn 与 Step 的定义与边界（概念解释 + 一个真实对话拆成 turn/step 的文字示例；表格：turn vs step）
- 5.2 Inbox：输入如何进入循环（inbox 事件三件套 inserted/discarded/claimed；展示 agent.ts 中 inbox 回调代码）
- 5.3 事件瀑布：pre-step / request / llm-stream（waterfall 中间件语义；展示 agent.ts 中 pre-step 与 request waterfall 真实调用；文字时序图：一次 step 的完整事件流）
- 5.4 Turn-stopping 与轮次收束（serial 事件为什么在这里；turn/end 的 reason；展示 agent.ts turn-stopping 调用代码）
- 5.5 工具并发调度：exclusive 屏障与并行池（展示 tool-calls.ts 调度逻辑核心代码与注释；exclusive vs parallel 对比表；abort 时合成错误结果保证重放有效）

## 本章互动设计

- 3秒钩子（选一）：数字冲击型「一次模型请求背后，藏着 10 多个事件」或反常识型「agent 不是 while(true) 调模型，而是一台事件状态机」
- 文中提问：你的 agent 循环能优雅处理并发工具调用吗？
- 结尾 CTA：收藏 + 互动 + 追更
- 下章预告：第6章 工具执行流水线——工具调用不是黑盒，是一条分层流水线

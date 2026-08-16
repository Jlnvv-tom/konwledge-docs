# 第8章写作 Prompt：多端服务与扩展生态——从 dsh 看 Harness 的未来

## 任务

根据下面的文章目录，结合技术博客（掘金风格）的写作风格，以 IP「怕浪猫」的名义写一篇关于 dsh 多端服务与扩展生态的文章（系列收官章）。写入文件：/Users/wujihuan/code/web_workplace/konwledge-docs/docs/ai-practice/deepseek-harness/chapter-08.md

## 公共规范（必须全部执行）

请先读取 /Users/wujihuan/.qclaw/workspace/deepseek-harness-series/写作规范.md，严格按其执行：10000-12000 字、段落短、无 `---` 分隔、无图片无 emoji、缩写给英文全称、至少 3 处文字化图表等效表达、至少 3 段真实源码展示（标注路径）、金句 ≥3 处、清单/步骤结构 ≥1 处、结尾总结表格 + 3 层 CTA + 下章预告（系列收官总结）+ 系列进度条（进度 8/8）。

## 可用素材（来自源码仓库 /Users/wujihuan/code/AI_workplace/deepseek-harness）

- Web GUI 双半包：packages/client（浏览器端：web/modules/web-react/connection/runtime/hmr/locale/ui-slots/ui-theme/ui-* 系列）、packages/host（宿主端：webserver、apiproxy、api gateway 等）；apps/web（Vite 应用壳）。页面按 boot manifest 运行时拉取插件。
- api 家族：remotes（BFF 策略、Host Agent/Session lookup）、gateway（Host Typert 分发器与 Client Remote endpoint）；Typert（registry/loader/generator，从源码类型生成运行时反射产物，支撑 Remote 方法调用）。
- ACP（Agent Client Protocol，代理客户端协议）：packages/acp——面向程序化客户端的自动化服务器。
- SDK：packages/sdk——stdio JSON-RPC（JavaScript Object Notation Remote Procedure Call，JSON 远程过程调用）从外部进程驱动 runtime；python/sdk 与 python/sdk-runtime（Python 侧 SDK）。
- Headless：dsh --profile headless "task" 单次任务打印结果退出，适合 CI（Continuous Integration，持续集成）。
- 扩展点全景：
  - hooks：hooks-claude-code / hooks-codex 桥接外部 shell 钩子（hook-protocol 共享库）。
  - extensions：tool-cordis（cordis_inspect/cordis_define/cordis_run/cordis_stop/cordis_undefine）、cordis-host-runner（node:vm 沙箱）、cordis-client-runner（浏览器半）、ui-cordis。
  - preset：agent-presets（按会话组装 agent，agent.cordis.yml）+ persona。
  - subagent 提供方全家桶（inprocess/acp/codex/claude-code/dsh-sdk）；jobs 后台任务；workflow（模型编写编排工作流的 worker-thread 引擎）。
- examples/：acp-agent、headless-agent、jsonrpc-agent（Python SDK 驱动）、mcp-memory（第三方 MCP（Model Context Protocol，模型上下文协议）记忆服务器）、web-cordis（自指 agent）、web-schedule（会话内提醒）。
- 未来方向：Harness Engineering 概念（对照 Lilian Weng 文章思路：工作流自动化、文件系统持久记忆、子代理与后台任务、评估与权限控制）；dsh 的插件化/可组合/多形态是其平台化代表。

## 本章目录（按此组织小节）

- 8.1 Web GUI：host + client 双半包架构（双半包拆分原因：浏览器插件表、HMR、Typert Remote；host/client 分工表；boot manifest 拉取插件流程文字图）
- 8.2 ACP 与 SDK：程序化驱动（ACP 适用场景 vs SDK JSON-RPC；对比表；jsonrpc-agent 示例说明；如何把 dsh 嵌进自己的产品）
- 8.3 Headless 与 Python SDK：自动化集成（headless 单次任务适合 CI；Python SDK 结构；示例说明）
- 8.4 扩展点全景：hooks、extensions、preset、subagent、workflow、jobs（每个扩展点一段：机制 + 代码/配置示意 + 用途；表格：扩展点速查）
- 8.5 从 dsh 看 Harness Engineering 的未来（Harness 概念总结；dsh 的 5 个设计亮点回顾；对自建 agent 平台的借鉴清单；系列收官总结 + 全系列要点回顾表）

## 本章互动设计

- 3秒钩子（选一）：数字冲击型「同一个 runtime，六种打开方式」或反常识型「你以为 dsh 是个聊天软件，其实它是个可以被任何程序驱动的运行时」
- 文中提问：如果让你给 agent 平台加一种打开方式，你会加什么？
- 结尾 CTA：收藏（系列合集）+ 互动（评论区交流）+ 追更（关注怕浪猫，系列完结但后续还有单篇实战）+ 系列进度条 8/8 收官
- 下章预告：系列完结，回顾全系列 8 章脉络，预告可能的番外篇

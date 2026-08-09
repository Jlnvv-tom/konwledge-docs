---
sidebar_position: 3
---

# 第三章：技术文档高频词汇

> 读懂技术文档，是程序员英语的第一道门槛。你不需要背完一本 GRE 词汇书，但你需要认得 prerequisite、payload、deprecated 这些"老熟人"。本章帮你一次性拿下技术文档里出现频率最高的那批词。

---

## 3.1 README 与项目说明高频词

README 是每个开源项目的"门面"。不管你在 GitHub、GitLab 还是 Gitee，打开一个项目第一眼看到的就是 README。README 有一套约定俗成的结构，每个部分都有高频词汇反复出现。掌握了这些词，你就能快速定位自己需要的信息。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| prerequisite | 前置条件 | 运行项目前需要满足的环境或依赖 |
| installation | 安装 | 如何安装项目及其依赖 |
| usage | 用法 | 项目的基本使用方式 |
| contributing | 贡献指南 | 如何参与项目开发、提交代码 |
| license | 许可证 | 项目的开源协议类型 |
| getting started | 快速开始 | 面向新用户的入门指引 |
| features | 特性 | 项目支持的功能列表 |
| requirements | 系统要求 | 运行所需的软硬件条件 |
| dependencies | 依赖 | 项目依赖的外部库或工具 |
| configuration | 配置 | 对项目进行个性化设置 |
| troubleshooting | 故障排除 | 常见问题的解决方案 |

### 使用场景与真实例句

**prerequisite** —— 出现在 README 的"准备工作"部分，告诉你装这个项目之前先得装好什么。

> **Prerequisites:** Node.js 18+ and npm 9+ are required before installation.
>
> （前置条件：安装前需要 Node.js 18+ 和 npm 9+。）

注意，prerequisite 经常和 requirement 混用，但语义有细微差别：prerequisite 强调"必须先有的"，requirement 强调"需要满足的条件"。在 README 里，prerequisite 更常见。

**installation** —— README 的核心部分，通常是一段命令行示例加几行说明。

> **Installation**
>
> ```bash
> npm install my-package
> ```
>
> Or install globally for CLI usage:
>
> ```bash
> npm install -g my-package
> ```

**usage** —— 安装完了之后怎么用。这部分通常有最简代码示例。

> **Usage**
>
> ```javascript
> import { debounce } from 'my-package';
>
> const debouncedFn = debounce(() => console.log('Hello!'), 300);
> ```

**contributing** —— 开源项目用来规范贡献者行为的部分。如果你要给项目提 PR（Pull Request），一定先读这部分。

> **Contributing**
>
> We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request. All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

**license** —— 声明项目的开源协议。别小看这个词，如果你在公司项目里用了一个 GPL 协议的库，可能带来法律风险。

> **License**
>
> This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

### 常见误用与混淆

- **prerequisite vs. requirement**：prerequisite 是"先决条件"（A 必须先发生，B 才能发生），requirement 是"需求"（系统需要满足的条件）。写文档时，如果你说的是"装之前必须有 X"，用 prerequisite 更准确。
- **usage vs. example**：usage 是"用法概述"，example 是"具体示例"。很多 README 把两者混在一起，但严格来说 usage 是说明，example 是演示。
- **contributing vs. contribution**：contributing 是动名词形式，作标题用（Contributing Guide）；contribution 是名词，指具体的贡献行为（Thank you for your contribution）。

---

## 3.2 API 文档高频词

API 文档是程序员打交道最多的文档类型之一。不管是 RESTful API、GraphQL 还是 SDK 文档，有一批词汇几乎在每个 API 文档里都会出现。搞定它们，看 API 文档的速度能翻倍。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| endpoint | 端点 | API 的访问地址，通常是一个 URL 路径 |
| payload | 负载/请求体 | 请求中携带的数据内容 |
| response | 响应 | 服务器返回的数据 |
| schema | 数据模式 | 数据结构的定义规范 |
| parameter | 参数 | 传递给 API 的输入值 |
| authentication | 认证 | 验证调用者身份的过程 |
| rate limit | 速率限制 | 单位时间内允许的请求次数上限 |
| request body | 请求体 | HTTP 请求中携带的数据部分 |
| header | 请求头 | HTTP 请求的元数据字段 |
| status code | 状态码 | HTTP 响应状态编码（如 200、404、500） |
| pagination | 分页 | 将大量结果分成多页返回的机制 |
| callback | 回调 | 请求完成后被调用的函数或 URL |

### 使用场景与真实例句

**endpoint** —— API 文档的"地址簿"。每个 API 功能对应一个 endpoint。

> **Endpoints**
>
> | Method | Endpoint | Description |
> |--------|----------|-------------|
> | GET | `/api/v1/users` | List all users |
> | POST | `/api/v1/users` | Create a new user |
> | GET | `/api/v1/users/:id` | Get a specific user |

**payload** —— 听起来像航天术语，但在 API 语境里就是"你发送的数据"。这个词在 POST/PUT 请求的文档中最常见。

> The `POST /api/v1/messages` endpoint accepts the following JSON payload:
>
> ```json
> {
>   "to": "user_123",
>   "text": "Hello, world!",
>   "attachments": []
> }
> ```

**schema** —— 定义数据的结构和类型约束。在 GraphQL、JSON Schema、OpenAPI 规范中大量出现。

> **Response Schema**
>
> ```json
> {
>   "type": "object",
>   "properties": {
>     "id": { "type": "string" },
>     "name": { "type": "string" },
>     "email": { "type": "string", "format": "email" },
>     "created_at": { "type": "string", "format": "date-time" }
>   },
>   "required": ["id", "name", "email"]
> }
> ```

**parameter** —— API 文档里最常见的词之一。通常分为 path parameter（路径参数，如 `/users/:id` 中的 `id`）、query parameter（查询参数，如 `?page=1&limit=20`）和 body parameter（请求体参数）。

> **Parameters**
>
> | Name | Type | In | Required | Description |
> |------|------|----|----------|-------------|
> | `user_id` | string | path | Yes | The unique identifier of the user |
> | `fields` | string | query | No | Comma-separated list of fields to include |
> | `expand` | string | query | No | Related resources to expand |

**authentication** —— 告诉你怎么证明"你是谁"。常见的认证方式有 API Key、Bearer Token、OAuth 2.0 等。

> **Authentication**
>
> All API requests must be authenticated with an API key. Include your API key in the `Authorization` header:
>
> ```
> Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxx
> ```

**rate limit** —— 每个 API 都有调用频率限制，防止滥用。文档里会说明限制规则和超出后的行为。

> **Rate Limiting**
>
> We enforce a rate limit of 100 requests per minute per API key. If you exceed this limit, you will receive a `429 Too Many Requests` response. Check the `X-RateLimit-Remaining` header to track your quota.

### 常见误用与混淆

- **endpoint vs. URL**：endpoint 特指 API 的功能入口点（如 `/api/v1/users`），URL 是完整的统一资源定位符（如 `https://api.example.com/api/v1/users`）。在 API 文档中说 endpoint 更精确。
- **parameter vs. argument**：parameter 是定义时的形参（函数签名中声明的），argument 是调用时的实参（实际传入的值）。API 文档里用 parameter 居多，但在编程语言文档中两者都会出现。
- **payload vs. body**：payload 是"有效载荷"的概念，含义更广，可以包含 body 之外的数据（如 URL 中的 query string 也算 payload 的一部分）；body 严格指 HTTP 请求体。日常使用中两者经常互换。
- **authentication vs. authorization**：authentication 是"你是谁"（身份认证），authorization 是"你能做什么"（权限授权）。两者经常被缩写为 auth，但含义不同。先认证（authn），再授权（authz）。

---

## 3.3 错误信息与日志词汇

程序跑起来总会出错。错误信息、日志、stack trace 这些东西是调试时最常打交道的。理解这些词汇，你才能从一堆英文报错中快速抓住关键信息，而不是一看到红色文字就慌。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| stack trace | 堆栈跟踪 | 程序出错时的调用栈信息 |
| segfault | 段错误 | 非法内存访问导致的崩溃 |
| timeout | 超时 | 操作在规定时间内未完成 |
| overflow | 溢出 | 数据超出存储范围 |
| leak | 泄漏 | 资源未被正确释放 |
| deprecated | 已弃用 | 不再推荐使用的功能，将来可能移除 |
| assertion | 断言 | 程序运行时的条件检查 |
| exception | 异常 | 程序运行时的非正常情况 |
| fatal | 致命错误 | 导致程序终止的严重错误 |
| warning | 警告 | 不影响运行但需注意的问题 |
| trace | 追踪 | 程序执行路径的记录 |
| deadlock | 死锁 | 多个进程/线程互相等待对方释放资源 |

### 使用场景与真实例句

**stack trace** —— 程序崩溃时打印的那一大坨调用信息。它从最底层的错误点开始，一路向上追溯调用链。

> ```
> Traceback (most recent call last):
>   File "app.py", line 42, in <module>
>     process_data(data)
>   File "app.py", line 28, in process_data
>     result = parse_json(raw)
>   File "app.py", line 15, in parse_json
>     return json.loads(input)
>   File "/usr/lib/python3.11/json/__init__.py", line 346, in loads
>     return _default_decoder.decode(s)
> json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
> ```
>
> 这个 stack trace 告诉我们：`json.loads()` 出错了，它是被 `parse_json()` 调用的，而 `parse_json()` 是被 `process_data()` 调用的。从下往上看，就能找到根因。

**segfault** —— "segmentation fault" 的简称，C/C++ 程序员的噩梦。当你访问了不该访问的内存地址时，操作系统会直接杀掉你的程序。

> ```
> Segmentation fault (core dumped)
> ```
>
> 这通常意味着你访问了空指针、越界数组或者已经释放了的内存。如果你在编译时加上 `-g` 参数并使用 `gdb`，可以定位到具体出错的代码行。

**timeout** —— 网络请求或操作在规定时间内没完成。在 API 调用、数据库查询中极为常见。

> ```
> Error: Request timed out after 30000ms
>     at HttpClient.request (/node_modules/got/dist/source/core/index.js:956:23)
> ```
>
> 遇到 timeout 不要急着重试，先排查是网络问题、服务端慢还是自己的查询太重。

**overflow** —— 数据超过了类型能表示的范围。最经典的是 integer overflow（整数溢出）和 buffer overflow（缓冲区溢出）。

> ```
> panic: runtime error: integer divide by zero
> ```
>
> 注意，有些语言（如 Go）会把 overflow 相关错误以 panic 形式抛出。而在 JavaScript 中，数值溢出不会报错，而是返回 `Infinity`，这可能更隐蔽。

**leak** —— 内存泄漏（memory leak）是最常见的，但还有 file descriptor leak（文件描述符泄漏）、connection leak（连接泄漏）等。

> ```
> WARNING: Possible memory leak detected.
> Heap usage has grown from 45MB to 890MB over the last 30 minutes without any corresponding increase in traffic.
> ```
>
> 在日志里看到 leak 相关的警告，通常意味着某个资源只分配不释放。Go 的 pprof、Java 的 jmap 都是排查利器。

**deprecated** —— 这个词在技术文档里极其常见。它表示某个 API、函数或特性已经过时，不建议继续使用，将来某个版本会被移除。

> ```
> DeprecationWarning: `uuid.v1()` is deprecated and will be removed in v10.0.0. Please use `uuid.v1()` from the `uuid` package directly, or migrate to `uuid.v4()` for better randomness.
> ```
>
> 看到 deprecated 别慌，它现在还能用，但你应该尽快迁移到替代方案。很多编译器和 linter 会在代码中标记 deprecated 用法。

### 常见误用与混淆

- **error vs. exception vs. fault**：error 是笼统的"错误"；exception 是语言层面的"异常机制"（可被 try-catch 捕获）；fault 是系统层面的"故障"（如 segfault 是操作系统层面的）。在日志中，三者严重程度递增。
- **deprecated vs. obsolete**：deprecated 是"官方明确不再推荐"，但还能用；obsolete 是"已经废弃不用了"，通常已经移除或不再工作。
- **fatal vs. critical**：fatal 是"致命的"，程序会直接终止；critical 是"严重的"，但不一定导致程序终止，可能只是某个功能不可用。在日志分级体系中，两者通常属于不同级别。
- **timeout vs. deadline exceeded**：timeout 侧重"等待超时"（我等了 30 秒你还没响应），deadline exceeded 侧重"截止时间已过"（给你的总时间用完了）。在 gRPC 中，deadline exceeded 是标准的错误码。

---

## 3.4 技术规范与 RFC 词汇

RFC（Request for Comments）文档是互联网标准的核心。HTTP、TCP、URI 这些协议的规范都定义在 RFC 里。技术规范有一套特殊的词汇体系，其中每个词都有精确的法律级别的含义。搞混了 "must" 和 "should"，可能导致你的实现不符合标准。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| specification | 规范 | 对技术标准或协议的详细描述 |
| compliance | 合规 | 实现符合规范要求的程度 |
| must | 必须 | 强制要求，不可违反 |
| should | 应当 | 强烈推荐，但有正当理由可例外 |
| may | 可以 | 可选项，由实现者自行决定 |
| normative | 规范性 | 正式标准的一部分，具有约束力 |
| informative | 资料性 | 仅供参考，不构成标准要求 |
| implementation | 实现 | 对规范的具体代码实现 |
| interoperability | 互操作性 | 不同实现之间能协同工作 |
| conformance | 一致性 | 实现与规范的符合程度 |
| semantics | 语义 | 符号或操作的含义 |
| syntax | 语法 | 符号或操作的书写格式 |

### 使用场景与真实例句

RFC 2119 专门定义了 must、should、may 这几个关键词的精确含义，几乎所有技术规范都引用了这个定义。

**must** —— 最高的强制级别。违反 must 的实现是不合规的。

> The server **MUST** send a `Content-Type` header in all responses with a body. A server that omits this header is not compliant with this specification.

翻译：服务器**必须**在所有带响应体的回复中发送 `Content-Type` 头。不发送此头的服务器不符合本规范。

**should** —— 推荐级别。在绝大多数情况下应该这么做，但存在特殊场景可以例外。

> Clients **SHOULD** retry failed requests with exponential backoff. However, if the server returns `429 Too Many Requests`, the client **MUST** respect the `Retry-After` header.

翻译：客户端**应当**使用指数退避策略重试失败的请求。但如果服务器返回 `429 Too Many Requests`，客户端**必须**遵守 `Retry-After` 头的指示。

**may** —— 可选级别。完全由实现者决定。

> A server **MAY** include a `Link` header with `rel="next"` to indicate the URL of the next page of results. Clients **MAY** use this header for automatic pagination.

翻译：服务器**可以**在响应中包含 `Link` 头（`rel="next"`）来指示下一页的 URL。客户端**可以**使用此头进行自动分页。

**normative vs. informative** —— 规范文档通常分为 normative（规范性）和 informative（资料性）两部分。normative 部分是"必须遵守的标准"，informative 部分是"仅供参考的说明"。

> **Appendix A (Normative):** Defines the ABNF grammar for all header fields defined in this specification.
>
> **Appendix B (Informative):** Provides examples of common usage patterns. These examples are non-normative and are provided for illustration purposes only.

**compliance / conformance** —— 两个词都表示"符合规范"，但用法略有不同。compliance 更常用在法规和行业标准的语境，conformance 更常用在技术规范的测试中。

> To claim conformance with this specification, an implementation **MUST** satisfy all requirements marked with `MUST` in Sections 2 through 5. Conformance testing is performed using the test suite available at [link].

**interoperability** —— 不同系统或实现能互相协作的能力。这是技术规范的核心目标之一。

> This specification is designed to maximize interoperability between independent implementations. All conforming implementations **MUST** be able to parse and process messages generated by any other conforming implementation.

### 常见误用与混淆

- **must vs. should**：这是 RFC 里最重要的区分。must = 没有商量余地；should = 强烈建议但有例外。如果你在写技术文档，用 must 表示强制要求时，**不要**写成 should，否则别人会以为可以不遵守。
- **may vs. can**：may 表示"允许"（permission），can 表示"能够"（ability）。规范里用 may 表示"你可以选择这么做"，用 can 表示"技术上可行"。例如："An implementation **MAY** support gzip compression"（允许支持）vs. "A 64-bit system **CAN** address more than 4GB of memory"（技术上能够）。
- **specification vs. standard**：specification 是"规范描述"，standard 是"正式标准"。一个 specification 经过标准化组织（如 ISO、ANSI）批准后才成为 standard。但在日常交流中两者经常互换使用。
- **semantics vs. syntax**：syntax 是"怎么写"（格式），semantics 是"什么意思"（含义）。例如 HTTP 中 `GET / HTTP/1.1` 的 syntax 是方法+路径+版本号，semantics 是"获取根路径的表示"。在规范文档中区分这两者非常重要。

---

## 3.5 开源项目常见术语

开源世界有自己的"黑话"。当你在 GitHub 上混，会不断遇到 contributor、maintainer、fork、upstream、derivative 这些词。理解它们不只是为了看懂文档，更是为了参与开源社区——从"用"到"贡献"的必经之路。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| contributor | 贡献者 | 向项目提交过代码或文档的人 |
| maintainer | 维护者 | 负责项目日常维护和决策的人 |
| license | 许可证 | 定义项目使用、修改、分发的法律条款 |
| fork | 派生 | 复制一份代码仓库作为独立项目 |
| upstream | 上游 | 派生项目的原始仓库 |
| derivative | 衍生作品 | 基于原项目修改而成的作品 |
| workflow | 工作流 | 项目开发流程的规范化定义 |
| pull request (PR) | 拉取请求 | 请求将你的代码合并到目标仓库 |
| issue | 议题 | 项目的 bug 报告或功能请求 |
| commit | 提交 | 代码的一次原子修改记录 |
| branch | 分支 | 代码的独立开发线 |
| merge | 合并 | 将一个分支的修改整合到另一个分支 |
| release | 发布 | 项目的正式版本发布 |
| changelog | 变更日志 | 记录版本间变化的文件 |
| code of conduct | 行为准则 | 社区成员行为规范 |

### 使用场景与真实例句

**contributor** —— 任何提交过 PR、修过 bug、写过文档甚至只是报过 issue 的人都可以叫 contributor。但 contributor 和 maintainer 的角色是不同的。

> We'd like to thank all our [contributors](https://github.com/facebook/react/graphs/contributors) who have made this project possible. If you'd like to contribute, please read our [Contributing Guide](CONTRIBUTING.md).

**maintainer** —— 项目的"守护者"。他们有权限 merge PR、发布版本、决定项目方向。maintainer 通常是项目的核心开发者。

> **Maintainers**
>
> | Name | GitHub | Role |
> |------|--------|------|
> | Dan Abramov | @gaearon | Lead maintainer |
> | Andrew Clark | @acdlite | Core maintainer |
> | Sebastian Markbåge | @sebmarkbage | Core maintainer |

**fork** —— 在 GitHub 上点一下 Fork 按钮，你就得到了一份项目的完整拷贝。fork 之后你可以在自己的副本上自由修改，不影响原项目。

> **Forking the Project**
>
> If you want to contribute but don't have write access to the main repository, you can fork the project. Click the "Fork" button in the top-right corner of the GitHub page, clone your fork locally, make your changes, and submit a pull request.

**upstream** —— fork 之后，你的仓库叫 origin（你的副本），原始仓库叫 upstream。从 upstream 拉取最新更新是日常操作。

> ```bash
> # Add the original repository as a remote called "upstream"
> git remote add upstream https://github.com/original-owner/project.git
>
> # Fetch the latest changes from upstream
> git fetch upstream
>
> # Merge upstream changes into your main branch
> git checkout main
> git merge upstream/main
> ```

**derivative** —— 基于现有开源项目修改而成的新项目。许可证通常要求衍生作品遵守原项目的许可条款。

> **Derivative Works**
>
> If you create a derivative work based on this project, you **must** comply with the terms of the MIT License under which this project is distributed. You must include the original copyright notice and permission notice in all copies or substantial portions of the Software.

**license** —— 开源项目的"法律基石"。选择许可证是开源项目最重要的决策之一。常见的有 MIT（最宽松）、Apache 2.0（宽松但有专利条款）、GPL（具有传染性）。

> This project is dual-licensed under the MIT License and the Apache License, Version 2.0. You may choose either license at your option.

**workflow** —— 描述代码从开发到发布的过程。常见的有 Git Flow、GitHub Flow、Trunk-Based Development 等。

> **Development Workflow**
>
> 1. Fork the repository and create a feature branch from `main`
> 2. Make your changes and write tests
> 3. Ensure all tests pass: `npm test`
> 4. Submit a pull request with a clear description
> 5. Request review from a maintainer
> 6. Address review feedback if any
> 7. A maintainer will merge your PR once approved

**changelog** —— 记录每个版本的新增、修改和移除内容。标准格式参见 [Keep a Changelog](https://keepachangelog.com/)。

> # Changelog
>
> ## [2.1.0] - 2024-03-15
>
> ### Added
> - New `useDebounce` hook for debouncing values
> - Support for TypeScript 5.4
>
> ### Changed
> - `useEffect` cleanup is now called synchronously on unmount
>
> ### Deprecated
> - `useLegacyState` is deprecated and will be removed in v3.0
> ```

### 常见误用与混淆

- **contributor vs. maintainer**：contributor 是提交过贡献的人（可能只提了一个 typo 修复），maintainer 是有权限管理项目的人（能 merge PR、发布版本）。一个项目可以有几百个 contributor，但通常只有几个 maintainer。有时候人们会错误地把 maintainer 叫成 owner，但 owner 在 GitHub 上是仓库的拥有者（可以转让），语义又略有不同。

- **fork vs. clone**：fork 是在 GitHub/GitLab 平台层面的操作，会在你的账号下创建一个远程仓库的副本；clone 是在本地下载代码。你可以 clone 别人的仓库，但不能 push 回去；你可以 fork 别人的仓库，然后 clone 下来修改，再通过 PR 把修改提交回去。

- **upstream vs. origin**：clone 自己 fork 的仓库后，默认的 remote 名字是 origin（指向你的 fork）。你需要手动添加 upstream（指向原仓库）来同步上游更新。新手经常搞反这两个。

- **derivative work vs. fork**：fork 是 Git 平台的概念，derivative work 是法律概念。你 fork 了一个项目然后大量修改，你的版本就是 derivative work。即使你没有 fork 而是复制了代码，法律上仍然算 derivative work。许可证条款适用于 derivative work，而不只是 fork。

- **license vs. copyright**：license 是"许可条款"（你怎么能用这个代码），copyright 是"版权归属"（这个代码归谁所有）。开源不等于没有版权——恰恰相反，开源许可证是建立在版权基础上的。作者保留版权，通过许可证授予你使用权限。

---

## 本章小结

本章覆盖了技术文档中出现频率最高的五类词汇：

1. **README 词汇**（prerequisite、installation、usage、contributing、license）——打开任何项目的第一道门
2. **API 文档词汇**（endpoint、payload、schema、parameter、authentication、rate limit）——调用 API 时最常遇到的术语
3. **错误与日志词汇**（stack trace、segfault、timeout、overflow、leak、deprecated）——调试排错时的关键信息
4. **规范与 RFC 词汇**（specification、compliance、must/should/may、normative）——理解协议标准时的必备知识
5. **开源项目术语**（contributor、maintainer、fork、upstream、derivative、workflow）——参与开源社区的通用语言

**学习建议：**

- 不要死记硬背，而是在实际阅读技术文档时留意这些词的出现场景
- 重点区分容易混淆的词对：must vs. should、authentication vs. authorization、deprecated vs. obsolete、fork vs. clone
- 遇到不认识的词，先根据上下文猜含义，再查证——这比直接查字典记得更牢

下一章，我们将进入代码注释与 commit message 的世界，学习如何在代码中用英文清晰地表达自己。
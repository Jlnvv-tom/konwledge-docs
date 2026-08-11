---
sidebar_position: 6
---

# 第六章：英文技术文档阅读

> 代码是世界的通用语言，但文档才是理解这个世界的说明书。当你能高效阅读英文技术文档时，你就拥有了比同行快一步获取信息的能力——不是靠翻译工具等二手信息，而是直接站在信息源头。

---

## 6.1 官方文档阅读策略（快速定位/结构理解）

每个程序员都经历过这样的场景：遇到一个报错或者想实现某个功能，打开 Google 搜了一下，排在第一的是官方文档链接，点进去——然后面对密密麻麻的英文，不知从何读起。

其实，阅读官方文档最大的误区就是"从头到尾逐字读"。官方文档不是小说，它更像是一本字典加一本说明书。你需要的是**快速定位**和**结构理解**，而不是线性阅读。

### 6.1.1 官方文档的常见结构

大多数成熟的官方文档都遵循类似的信息架构。理解了这个架构，你就能快速找到需要的内容：

| 文档区域 | 英文名称 | 作用 | 什么时候看 |
|---------|---------|------|-----------|
| 快速上手 | Quick Start / Getting Started | 最小可运行示例 | 第一次接触这个工具 |
| 指南 | Guide / Tutorial | 手把手教学 | 系统学习某个功能 |
| API 参考 | API Reference | 接口细节查询 | 需要查具体参数/返回值 |
| 配置 | Configuration | 可配置项列表 | 需要调参数时 |
| 迁移指南 | Migration Guide | 版本升级注意事项 | 升级版本时 |
| 常见问题 | FAQ | 高频问题解答 | 遇到问题时先看看 |
| 更新日志 | Changelog / Release Notes | 每个版本改了什么 | 了解版本变化 |

### 6.1.2 快速定位三步法

当你打开一个官方文档页面时，建议按照以下三步操作：

**第一步：看侧边栏（Sidebar），定位章节。** 大多数文档站点左侧都有导航树。先扫描一级目录，找到与你需求最接近的板块，再展开看子目录。比如你想了解 React 的 `useEffect`，不要在搜索框里搜（结果太杂），而是去 Sidebar 找 Hooks → useEffect。

**第二步：扫标题，不读正文。** 进入目标页面后，先快速滚动一遍，只看各级标题（H1/H2/H3），建立对页面内容的整体认知。这一步只需 10-20 秒，但能帮你判断这个页面是否真的包含你需要的信息。

**第三步：用 Ctrl+F 精确搜索。** 确定页面后，用浏览器搜索功能定位具体关键词。比如你在看 webpack 配置文档，想了解 `devServer` 的 `proxy` 选项，直接搜索 "proxy" 即可。

### 6.1.3 真实示例：阅读 Vue.js 官方文档

下面是 Vue.js 官方文档中关于 `computed` properties 的一段内容：

> ### Computed Properties
>
> In-template expressions are very convenient, but they're meant for simple operations. Putting too much logic in your templates can make them bloated and hard to maintain. For example, if we have an object with nested properties:
>
> ```js
> const author = reactive({
>   name: 'John Doe',
>   books: [
>     'Vue 2 - Advanced Guide',
>     'Vue 3 - Basic Guide',
>     'Vue 4 - The Mystery'
>   ]
> })
> ```
>
> And we want to display different messages depending on if `author` already has some books or not:
>
> ```html
> <p>Has published books:</p>
> <span>{{ author.books.length > 0 ? 'Yes' : 'No' }}</span>
> ```
>
> At this point, the template is getting a bit cluttered. We have to look at it for a second before realizing that it performs a calculation depending on `author.books.length`. The problem worsens if we want to include this calculation in the template more than once.

**阅读拆解：**

1. **标题** "Computed Properties" → 这一节讲的是计算属性
2. **第一句** "In-template expressions are very convenient, but..." → 提出问题：模板里放太多逻辑不好
3. **代码示例** → 给出一个具体场景，author 对象有 books 数组
4. **关键句** "the template is getting a bit cluttered" → 模板变得混乱了
5. **暗示** → 所以我们需要 computed properties 来解决

注意这段文档的写作套路：**先说问题（为什么需要）→ 给出反面示例（不用会怎样）→ 然后引出解决方案**。这是技术文档最常见的论证结构。理解了这个结构，你就能预判下一段要讲什么，阅读效率大幅提升。

### 6.1.4 高频词汇速查

阅读官方文档时，以下词汇频繁出现：

| 英文 | 中文 | 常见语境 |
|------|------|---------|
| deprecated | 已废弃 | 某个 API 不再推荐使用 |
| recommended | 推荐的 | 官方建议的做法 |
| required | 必填的/必需的 | 参数必须提供 |
| optional | 可选的 | 参数可省略 |
| defaults to | 默认值为 | 不传时的默认行为 |
| available since | 从...版本开始可用 | 某特性引入的版本 |
| note that / please note | 请注意 | 重要提醒 |
| be aware that | 注意 | 警告性提醒 |
| for more information, see | 更多信息请参阅 | 指向其他文档链接 |
| prior to | 在...之前 | 某操作之前需要做的事 |

一个实用技巧：当你看到 **"deprecated"** 这个词时，要格外留心。它意味着这个 API 或用法在未来版本中会被移除，你应该寻找替代方案。文档中通常会写类似 "Use X instead" 或 "This has been replaced by Y" 的指引。

---

## 6.2 API Reference 阅读方法

API Reference 是技术文档中最高频阅读的部分，也是最结构化的部分。每个 API 文档基本都遵循固定的信息结构，一旦掌握了解读方法，看任何 API 文档都能驾轻就熟。

### 6.2.1 API 文档的标准结构

一个完整的 API 文档条目通常包含以下要素：

```
方法名 / 端点（Endpoint）
├── 描述（Description）— 这个 API 是干什么的
├── 参数（Parameters）
│   ├── 名称
│   ├── 类型（Type）
│   ├── 是否必填（Required/Optional）
│   ├── 默认值（Default）
│   └── 说明（Description）
├── 返回值（Return Value / Response）
├── 异常 / 错误（Exceptions / Errors）
└── 示例（Examples）
```

### 6.2.2 真实示例：阅读 MDN 上的 Array.prototype.map()

下面是 MDN Web Docs 上 `Array.prototype.map()` 的文档片段：

> ### Array.prototype.map()
>
> The **`map()`** method of `Array` instances creates a new array populated with the results of calling a provided function on every element in the calling array.
>
> #### Syntax
>
> ```js
> map(callbackFn)
> map(callbackFn, thisArg)
> ```
>
> #### Parameters
>
> - `callbackFn`
>   - A function to execute for each element in the array. Its return value is added to the new array. The function is called with the following arguments:
>     - `element`
>       - The current element being processed in the array.
>     - `index`
>       - The index of the current element being processed in the array.
>     - `array`
>       - The array `map()` was called upon.
> - `thisArg` *(Optional)*
>   - A value to use as `this` when executing `callbackFn`.
>
> #### Return value
>
> A new array with each element being the result of the callback function.
>
> #### Description
>
> `map()` calls a provided `callbackFn` function once for each element in an array, in order, and constructs a new array from the results. `callbackFn` is invoked only for array indexes which have assigned values. It is not invoked for empty slots in sparse arrays.
>
> #### Examples
>
> ```js
> const array1 = [1, 4, 9, 16];
> const map1 = array1.map((x) => x * 2);
> console.log(map1);
> // Expected output: Array [2, 8, 18, 32]
> ```

**阅读拆解：**

1. **第一句描述** — "creates a new array populated with the results of calling a provided function on every element" → 核心信息：创建新数组 + 对每个元素调用函数 + 结果填充到新数组。一句话就说明了 `map` 的本质。

2. **Syntax（语法）** — 两种调用形式，第二种多了 `thisArg` 参数。

3. **Parameters（参数）** — `callbackFn` 是核心参数，它本身又接收三个子参数：`element`、`index`、`array`。注意层级关系，在文档中通过缩进表示。`thisArg` 标注了 *(Optional)*，说明可选。

4. **Return value（返回值）** — "A new array" → 关键词：**new**，说明不会修改原数组。

5. **Description（详细说明）** — 补充了一个重要细节：`callbackFn` 不会被 sparse arrays（稀疏数组）的空槽调用。

6. **Examples（示例）** — 最直观的学习材料，`[1, 4, 9, 16]` 经过 `x * 2` 变成 `[2, 8, 18, 32]`。

### 6.2.3 阅读 API 文档的技巧

**技巧一：先看 Description，再看 Examples，最后看 Parameters。** 很多人一上来就扎进参数列表里，结果看了半天不知道这个 API 到底干什么。正确的顺序是：先理解功能 → 看示例建立直觉 → 再查参数细节。

**技巧二：注意 Optional 和 Required 标记。** 必填参数是必须理解的，可选参数可以暂时跳过，需要时再回来看。

**技巧三：关注 Return value 的每一个词。** 返回值描述中的用词非常精确：
- "a new array" → 新数组，原数组不变
- "the original array" → 原数组，可能被修改
- "this array" → 返回自身，支持链式调用
- "undefined" → 没有返回值
- "a promise" → 异步操作

**技巧四：留意 Exceptions / Errors 部分。** 这部分告诉你 API 在什么情况下会抛错。很多 bug 就是因为没看异常说明，没有做错误处理导致的。

### 6.2.4 真实示例：阅读 Fetch API 文档

再来看一个 HTTP API 的例子——Fetch API 的 `fetch()` 函数：

> ### fetch()
>
> The global **`fetch()`** method starts the process of fetching a resource from the network, returning a promise which is fulfilled once the response is available.
>
> #### Syntax
>
> ```js
> fetch(resource)
> fetch(resource, options)
> ```
>
> #### Parameters
>
> - `resource`
>   - This defines the resource that you wish to fetch. This can either be a string, a `URL` object, or a `Request` object.
> - `options` *(Optional)*
>   - A `RequestInit` object containing any custom settings that you want to apply to the request. The possible options are:
>     - `method` — The request method, e.g., `"GET"`, `"POST"`.
>     - `headers` — Any headers you want to add to your request.
>     - `body` — The body of the request.
>     - `mode` — The mode you want to use for the request, e.g., `"cors"`, `"no-cors"`.
>     - `credentials` — Controls what browsers do with credentials (cookies, HTTP authentication entries).
>
> #### Return value
>
> A `Promise` that resolves to a `Response` object.
>
> #### Exceptions
>
> - `TypeError` — The specified URL string is invalid or the URL uses a protocol other than HTTP/HTTPS.
> - `AbortError` — The request was aborted via an `AbortController`.

注意几个关键词：
- "returning a **promise** which is **fulfilled** once the response is available" → 异步操作，返回 Promise
- "**resolves to** a Response object" → Promise resolve 后得到的是 Response 对象
- "TypeError" 和 "AbortError" → 两种可能的异常，如果你不做处理，可能就是未捕获的错误

这些用词的精确性是英文技术文档的核心特征。中文翻译往往会丢失这种精确性，这也是为什么推荐直接阅读英文原文的原因。

---

## 6.3 技术规范与 RFC 阅读技巧

RFC（Request for Comments）、W3C 规范、ECMA 规范——这些文档以枯燥、冗长、难读著称。但它们是技术的"源头法"，当你在 Stack Overflow 上找不到答案、博客文章互相矛盾时，规范文档是最终的裁判。

### 6.3.1 规范文档的特点

规范文档和普通技术文档有很大不同：

| 特点 | 普通技术文档 | 规范文档 |
|------|------------|---------|
| 目的 | 教你怎么用 | 定义什么是对的 |
| 风格 | 教学式、引导式 | 定义式、法律式 |
| 长度 | 几页到几十页 | 几十页到数百页 |
| 示例 | 大量代码示例 | 极少或没有示例 |
| 语言 | 通俗、随意 | 严格、正式 |
| 关键词 | should, can, will | MUST, SHOULD, MAY (有特殊含义) |

### 6.3.2 RFC 2119：理解关键词的含义

阅读规范文档，首先要理解 RFC 2119 中定义的关键词。这些词在规范中有非常精确的含义，和日常英语完全不同：

> - **MUST** — This word, or the terms "REQUIRED" or "SHALL", means that the definition is an absolute requirement of the specification.
> - **MUST NOT** — This phrase, or the phrase "SHALL NOT", means that the definition is an absolute prohibition of the specification.
> - **SHOULD** — This word, or the adjective "RECOMMENDED", means that there may exist valid reasons in particular circumstances to ignore a particular item, but the full implications must be understood and carefully weighed before choosing a different course.
> - **SHOULD NOT** — This phrase, or the phrase "NOT RECOMMENDED", means that there may exist valid reasons in particular circumstances when the particular behavior is acceptable or even useful, but the full implications should be understood and the case carefully weighed before implementing any behavior described with this label.
> - **MAY** — This word, or the adjective "OPTIONAL", means that an item is truly optional.

简单总结：

| 关键词 | 含义 | 严重程度 |
|--------|------|---------|
| MUST / MUST NOT | 必须做 / 必须不做 | ⛔ 绝对要求，不这么做就是不符合规范 |
| SHOULD / SHOULD NOT | 应该做 / 不应该做 | ⚠️ 强烈建议，除非有充分理由 |
| MAY | 可以做 | 💡 可选的，随意 |

当你看到 "The server MUST return a 400 status code" 时，这不是建议，是铁律。而 "The client SHOULD include a User-Agent header" 意味着最好加上，但不加也不算违规。

### 6.3.3 真实示例：阅读 HTTP/1.1 规范（RFC 9110）

下面是 RFC 9110（HTTP Semantics）中关于 `GET` 方法定义的一段：

> ### 9.2.1. GET
>
> The GET method requests transfer of a current selected representation for the target resource. GET is the primary mechanism of information retrieval and the focus of almost all performance optimizations. Hence, when people speak of retrieving some identifiable information via HTTP, they are generally referring to making a GET request.
>
> A client can request that the GET method be limited to a specific range of the selected representation data by using the Range header field.
>
> Although the request body is not prohibited for GET, it has no defined semantics for a GET request. A client **SHOULD NOT** generate a GET request with a body.
>
> The response to a GET request is cacheable; a cache **MAY** use it to satisfy subsequent GET requests.

**阅读拆解：**

1. **第一段** — 定义了 GET 的用途："requests transfer of a current selected representation" → 请求获取资源的表示。说人话就是：拿数据。

2. **第二段** — 补充说明：可以用 `Range` header 限制范围（比如断点续传）。

3. **第三段** — 关键信息："A client **SHOULD NOT** generate a GET request with a body" → 不应该在 GET 请求里放 body。注意是 SHOULD NOT，不是 MUST NOT，意味着技术上可以，但不推荐。

4. **第四段** — "cacheable" → GET 响应可以被缓存。cache **MAY** use it → 缓存可以用它来满足后续请求，注意是 MAY（可选的）。

短短四段话，信息密度极高。每句话都在定义行为规范，每个关键词（SHOULD NOT, MAY）都有精确的法律式含义。

### 6.3.4 阅读规范的实用策略

**策略一：不要从头读，先看目录。** RFC 通常有详细的 Table of Contents。先找到你关心的章节，直接跳过去。

**策略二：搜索关键词。** 用 Ctrl+F 搜索 "MUST"、"SHOULD"、"MAY" 来快速定位规范性条款。

**策略三：结合实现来理解。** 规范文档没有示例，但你可以自己写代码来验证理解。比如读了 HTTP 缓存规范后，用 curl 或 Postman 实际发请求，观察 response headers。

**策略四：利用 RFC 的交叉引用。** RFC 中大量使用 "see Section X" 或 "as defined in [RFC1234]" 的引用。遇到不理解的概念，顺着引用去看被引用的部分即可。

**策略五：先读 Abstract 和 Introduction。** 这两节通常用相对通俗的语言概括了整个规范的目标和范围，能帮你建立宏观认知。

### 6.3.5 常见规范文档入口

| 规范类型 | 来源 | 典型文档 | 网址 |
|---------|------|---------|------|
| HTTP | IETF RFC | RFC 9110-9114 | datatracker.ietf.org |
| JavaScript | ECMA | ECMA-262 | ecma-international.org |
| HTML/CSS/DOM | W3C / WHATWG | HTML Living Standard | html.spec.whatwg.org |
| URL | IETF | RFC 3986 | datatracker.ietf.org |
| JSON | IETF | RFC 8259 | datatracker.ietf.org |
| WebSocket | IETF | RFC 6455 | datatracker.ietf.org |
| Web API | W3C / MDN | 各种 Web API 规范 | developer.mozilla.org |

---

## 6.4 Stack Overflow 高赞回答阅读

Stack Overflow（简称 SO）可能是程序员最常访问的英文网站之一。当你遇到一个技术问题，搜索后大概率会看到一条 SO 问答链接。学会高效阅读 SO 上的高赞回答，是一项非常实用的能力。

### 6.4.1 SO 页面结构解读

一个典型的 SO 问答页面包含以下区域：

```
问题区域
├── 问题标题（Title）— 最上方的大标题
├── 问题描述（Question Body）— 问题的详细描述
├── 问题标签（Tags）— 技术标签
├── 投票数（Votes）— 问题被点赞的次数
└── 提问者信息 + 时间

回答区域（可能有多个回答，按投票数排序）
├── 回答正文（Answer Body）
├── 投票数（Votes）— 回答被点赞的次数
├── 被采纳标记（Accepted ✓）— 提问者采纳的回答
├── 评论（Comments）— 对回答的补充讨论
└── 回答者信息 + 时间
```

### 6.4.2 高效阅读 SO 的策略

**第一步：先看问题标题和标签，判断是否相关。** 搜索结果可能不完全匹配你的问题。花 5 秒钟看标题和标签，判断是否值得深入。

**第二步：看问题的投票数。** 高票问题通常意味着很多人遇到了同样的问题，下面的回答质量也通常较高。

**第三步：直接跳到最高赞回答或被采纳的回答。** SO 默认按投票数排序，第一个回答通常是最有用的。如果第一个回答没有被采纳（没有绿色 ✓），可以留意是否有被采纳的回答在下面。

**第四步：注意回答中的"Update"或"Edit"。** 技术在演进，旧回答可能已过时。很多回答者会在原回答后追加更新，注明 "As of 2024, the recommended approach is..." 这样的信息。

**第五步：看评论区。** 有时候回答正文没有覆盖的边界情况、或者对回答的纠正，会出现在评论里。高赞评论往往包含有价值的补充。

### 6.4.3 真实示例：阅读 SO 高赞回答

以下是一个经典的 SO 问答（有简化）：

> **Q: How do I return the response from an asynchronous call?** *(votes: 3,800+)*
>
> I have a function that does an asynchronous request. How can I return the response/result from this function?
>
> ```js
> function foo() {
>   var result;
>   $.ajax({
>     url: '...',
>     success: function(response) {
>       result = response;
>     }
>   });
>   return result; // Returns undefined
> }
> }
> ```
>
> Tags: javascript, jquery, ajax, asynchronous

这是一个极其经典的问题——为什么异步调用拿不到返回值。投票数高达 3800+，说明无数人踩过这个坑。

来看最高赞回答（简化版）：

> **A: *(votes: 5,200+)* ✓ Accepted**
>
> You're not getting a result because `$.ajax` is asynchronous. By the time your `return result;` line executes, the AJAX request hasn't completed yet.
>
> The solution is to **restructure your code** to use callbacks, promises, or async/await.
>
> #### Approach 1: Promises
>
> ```js
> function foo() {
>   return $.ajax({
>     url: '...'
>   });
> }
>
> foo().then(function(response) {
>   console.log(response);
> });
> ```
>
> #### Approach 2: async/await (ES2017+)
>
> ```js
> async function foo() {
>   const response = await fetch('...');
>   return response.json();
> }
>
> (async () => {
>   const result = await foo();
>   console.log(result);
> })();
> ```
>
> **Explanation:**
>
> Think of it like ordering food at a restaurant. When you place your order, the cashier doesn't stand there holding your food until it's ready. Instead, they give you a number and call you back when your order is up.
>
> In JavaScript terms:
> - Placing the order = initiating the async operation
> - Getting a number = receiving a Promise
> - Being called back = the Promise resolving
>
> The key insight is that **you cannot return a value from a function that is computed asynchronously**. You must either accept a callback, return a Promise, or use async/await.

**阅读拆解：**

1. **第一句** "You're not getting a result because `$.ajax` is asynchronous" → 一句话点明原因。

2. **"The solution is to restructure your code"** → 暗示这不是一个小修小补，而是需要调整代码结构。这种用词很重要，提醒你不要试图用 hack 的方式解决。

3. **两种方案** — Promise 和 async/await。注意标注了 "(ES2017+)"，告诉你 async/await 的版本要求。

4. **Explanation 部分** — 用餐厅点餐的类比来解释异步概念。这是 SO 高赞回答的常见特征：**先给代码，再用通俗类比解释原理**。

5. **加粗的关键句** "you cannot return a value from a function that is computed asynchronously" → 这是核心结论，加粗表示强调。

### 6.4.4 SO 高频表达模式

阅读 SO 时，以下表达模式反复出现：

| 表达 | 含义 | 常见场景 |
|------|------|---------|
| "You need to..." / "You have to..." | 你需要... | 给出解决方案 |
| "The reason is that..." | 原因是... | 解释问题成因 |
| "This happens because..." | 这是因为... | 解释原因 |
| "As of [version/date], ..." | 截至某版本/日期 | 说明版本相关的变化 |
| "This is a known issue" | 这是一个已知问题 | 官方已确认的 bug |
| "Works for me" | 我这边没问题 | 排查环境差异 |
| "Can you reproduce this on..." | 你能在...上复现吗 | 排查环境 |
| "See also [link]" | 另见 | 相关资源 |
| "Updated for [year/version]" | 为某年/版本更新 | 回答已更新 |
| "For a more detailed explanation, see..." | 详细解释请见 | 深入了解 |

### 6.4.5 注意事项

阅读 SO 时需要留意几点：

1. **投票数不等于正确性。** 有些高赞回答在多年前是正确的，但技术已经演进。注意看回答的时间，以及是否有更新。

2. **被采纳的回答不一定是最优解。** 提问者采纳的答案只是对提问者有效，不一定适合你的场景。有时候排在第二、第三的回答反而更好。

3. **留意标签中的版本信息。** 比如 `[reactjs]` 和 `[react-hooks]` 标签下的回答可能针对不同版本的 React。

4. **不要忽视评论。** 评论中经常包含重要的补充信息，比如 "This doesn't work in React 18+" 这样的提醒。

---

## 6.5 GitHub Issue 与 Discussion 阅读

GitHub 早已不只是代码托管平台，它也是全球最大的开源技术讨论社区。项目的 Issues 区是 bug 报告和功能请求的集散地，Discussions 区是技术讨论的广场。学会从 Issue 和 Discussion 中提取关键信息，是参与开源项目和深度理解技术的重要能力。

### 6.5.1 Issue 的类型与结构

GitHub Issue 通常分为以下几类：

| 类型 | 典型标题特征 | 阅读价值 |
|------|------------|---------|
| Bug Report | "X doesn't work when Y" | 了解已知 bug 和临时解决方案 |
| Feature Request | "Add support for X" / "Proposal: ..." | 了解项目发展方向 |
| Question | "How do I..." / "Is it possible to..." | 类似 SO 的问答 |
| Documentation | "Docs for X are unclear" | 了解文档中的坑 |
| Tracking | "Tracking issue for X feature" | 追踪某功能的实现进度 |

### 6.5.2 Issue 的标准结构

一个规范的 Bug Report Issue 通常包含以下部分：

```markdown
## Description
（问题的描述）

## Reproduction steps
（复现步骤）
1. ...
2. ...
3. ...

## Expected behavior
（期望的行为）

## Actual behavior
（实际的行为）

## Environment
（环境信息）
- OS: ...
- Node version: ...
- Package version: ...

## Additional context
（补充信息，如日志、截图等）
```

阅读 Issue 时，重点关注 **Reproduction steps**（复现步骤）和 **Expected vs Actual behavior**（期望 vs 实际行为）。这两部分包含了问题的核心信息。

### 6.5.3 真实示例：阅读 React Issue

以下是一个简化版的真实 React Issue：

> **#24534 — React 18: useEffect runs twice in development**
>
> Opened by @user123 on March 15, 2022 *(votes: 320)*
>
> ---
>
> ### Description
>
> After upgrading to React 18, my `useEffect` hooks are running twice on mount in development mode. This didn't happen in React 17. Is this a bug or expected behavior?
>
> ### Reproduction steps
>
> 1. Create a new React 18 app with `create-react-app`
> 2. Add a `useEffect` with an empty dependency array:
>    ```jsx
>    useEffect(() => {
>      console.log('mounted');
>    }, []);
>    ```
> 3. Run `npm start` and open the browser console
> 4. Notice "mounted" is logged twice
>
> ### Expected behavior
>
> `useEffect` should run once on mount.
>
> ### Actual behavior
>
> `useEffect` runs twice on mount.
>
> ### Environment
>
> - React version: 18.0.0
> - Browser: Chrome 99
> - OS: macOS 12.3

接着来看维护者的回复（简化版）：

> **Comment by @gaearon *(votes: 850+)* **
>
> This is expected behavior in React 18's Strict Mode.
>
> In React 18, `<StrictMode>` now remounts every component once on mount in development. This is intentional — it helps you find bugs related to improper cleanup in your effects.
>
> **This only affects development mode.** Your production build will not have this behavior.
>
> To fix side effects that shouldn't run twice, you should implement proper cleanup in your `useEffect`:
>
> ```jsx
> useEffect(() => {
>   console.log('mounted');
>   return () => {
>     console.log('unmounted');
>   };
> }, []);
> ```
>
> For more details, see the [React 18 upgrade guide](https://react.dev/blog/2022/03/29/react-v18#strict-mode-changes).

**阅读拆解：**

1. **标题** "React 18: useEffect runs twice in development" → 问题一句话概括：React 18 中 useEffect 执行两次。

2. **提问者的复现步骤** 非常清晰：4 个步骤，附带代码。好的 Issue 都是这样——让维护者能快速复现问题。

3. **维护者回复第一句** "This is expected behavior" → 不是 bug，是设计如此。这一句话就解决了提问者的疑虑。

4. **"This only affects development mode"** → 关键信息：只影响开发环境，生产环境正常。看到这句就可以放心了。

5. **解决方案** → 给出了具体做法：在 useEffect 中实现 cleanup function。

6. **参考链接** → 指向官方升级指南，可以深入了解背后的设计决策。

### 6.5.4 从 Issue 中提取关键信息的技巧

**技巧一：先看 Issue 标题和标签。** 标题告诉你问题是什么，标签（如 `bug`、`enhancement`、`documentation`、`wontfix`）告诉你 Issue 的性质和状态。

**技巧二：看 Issue 的状态。** Open 状态说明还没解决，Closed 状态需要看看是 "fixed" 还是 "wontfix"（不会修复）。如果是 Closed，直接跳到最后看维护者的最终回复。

**技巧三：找维护者/作者的评论。** 在长讨论中，最有价值的信息通常来自项目维护者。你可以用 Ctrl+F 搜索维护者的用户名，直接定位他们的评论。

**技巧四：关注 "pinned" 和 "linked" Issues。** Pinned Issue 通常是非常重要的公告或已知问题。Linked Issues（引用了其他 Issue 的评论）可能提供更多上下文。

**技巧五：注意 "lock" 状态。** 如果一个 Issue 被锁定（locked），通常意味着讨论已经结束，结论就在最后几条评论里。

### 6.5.5 Discussion 区的阅读

GitHub Discussions 比 Issue 更自由，通常是开放性问题的讨论场所。阅读 Discussion 时：

1. **看原帖的分类。** Discussion 通常分为 Q&A、Ideas、General、Show and Tell 等类别，不同类别的阅读策略不同。

2. **关注 "marked as answer" 的回复。** Q&A 类型的 Discussion 中，被标记为答案的回复是最有参考价值的。

3. **留意维护者的态度。** 在 Ideas 讨论中，维护者是否对某个提议表示兴趣，往往预示着这个功能是否会被实现。如果你看到维护者回复 "This is interesting, could you elaborate on the use case?"，说明他们认真考虑了这个提议；如果回复 "We have no plans to support this"，那就是委婉拒绝了。

4. **看讨论的时间线。** Discussion 可能跨越数月甚至数年。注意回复的时间顺序，早期的回复可能已经被后续讨论推翻。

### 6.5.6 GitHub 高频词汇与表达

阅读 GitHub Issue 和 Discussion 时，以下表达非常常见：

| 表达 | 含义 | 常见场景 |
|------|------|---------|
| "Could you provide a minimal reproduction?" | 能提供一个最小复现吗？ | 维护者要求提问者提供复现步骤 |
| "This is a duplicate of #1234" | 这与 #1234 重复 | 指向已有的相同问题 |
| "Closing as wontfix" | 关闭，不会修复 | 维护者决定不处理 |
| "Closing as duplicate" | 关闭，重复问题 | 与已有 Issue 重复 |
| "Fixed in #1234" | 在 PR #1234 中修复 | 指向修复 PR |
| "Released in v1.2.3" | 在 v1.2.3 版本发布 | 修复已发布 |
| "Up for grabs" | 认领 | 欢迎社区贡献 |
| "Good first issue" | 适合新手 | 入门级贡献机会 |
| "Needs investigation" | 需要调查 | 还没确认是否为 bug |
| "Works as intended" | 符合预期 | 不是 bug，是设计如此 |
| "What version are you using?" | 你用的什么版本？ | 排查版本问题 |
| "Can you try the latest version?" | 能试试最新版吗？ | 可能已修复 |
| "PR welcome" | 欢迎提 PR | 鼓励社区贡献代码 |

### 6.5.7 从 Issue 中学习

阅读 Issue 不只是解决问题，也是学习的好途径：

- **学习如何写好的 Bug Report。** 高质量的 Issue 模板可以学习，以后自己提 Issue 时也照着写。
- **了解项目的设计决策。** 很多 Feature Request 的讨论中，维护者会解释为什么选择 A 而不是 B，这是理解项目设计哲学的好机会。
- **发现隐藏的用法和技巧。** Issue 讨论中经常出现文档里没写的用法和 workaround。
- **跟踪技术演进。** 通过阅读 Tracking Issue，你可以了解某个功能从提案到实现的全过程。

---

## 本章小结

这一章我们学习了五种英文技术文档的阅读方法，来回顾一下要点：

1. **官方文档阅读** — 不要逐字读，用「看侧边栏 → 扫标题 → Ctrl+F」三步法快速定位信息。理解文档「先说问题 → 给示例 → 引出方案」的常见结构。

2. **API Reference 阅读** — 按「Description → Examples → Parameters」的顺序读。关注返回值描述中的每一个关键词（new、original、undefined、promise），它们传递了精确的语义。注意 Required/Optional 标记和 Exceptions 部分。

3. **RFC 与规范文档阅读** — 理解 RFC 2119 的关键词体系（MUST/SHOULD/MAY），这是规范文档的基础语言。不要从头读，先看目录和 Abstract，用搜索定位关键词，结合代码实践来理解抽象定义。

4. **Stack Overflow 阅读** — 直接跳到最高赞或被采纳的回答，注意「Update」标记的过时信息，不要忽视评论区。理解 SO 高频表达模式（"The reason is that..."、"As of..."、"This is a known issue"）能提升阅读速度。

5. **GitHub Issue 与 Discussion 阅读** — 关注 Reproduction Steps 和 Expected/Actual Behavior，找维护者的评论，注意 Issue 的状态和标签。Discussion 中的 "marked as answer" 和维护者态度是关键信息。

**核心心法：** 技术文档阅读不是英语阅读理解，不需要每个词都懂。你需要的是**信息提取能力**——快速找到关键信息，理解核心逻辑，忽略不必要的细节。这种能力只能通过大量实践来培养。建议从今天开始，遇到问题时优先阅读英文官方文档而不是找中文教程，坚持一个月，你会发现自己的英文技术阅读能力有质的飞跃。

> 💡 **下一章预告：** 第七章将介绍英文技术博客的阅读方法，包括优质博客推荐、长文拆解策略、以及如何阅读技术论文。
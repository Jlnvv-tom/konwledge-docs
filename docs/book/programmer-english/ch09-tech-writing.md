---
sidebar_position: 9
---

# 第九章：英文技术写作

> 会读英文文档只是入门，会写才是真本事。从一行 commit message 到一份事故复盘报告，技术写作贯穿程序员的每一天。写得好，同事夸你专业；写得烂，后人骂你挖坑。这一章我们从最小的写作单元（代码注释）一路讲到最大的写作单元（技术演讲 PPT），给你一套拿来就能用的写作模板和大量真实示例。别怕文笔不好——技术写作的核心不是辞藻华丽，而是清晰、准确、简洁。

---

## 9.1 代码注释与 Commit Message 写作

代码注释和 commit message 是程序员写得最多的两种英文文本。它们看似不起眼，却直接决定了代码库的可维护性和团队协作效率。一段好的注释能省去同事半小时的排查时间，一条好的 commit message 能让 code review 效率翻倍。

### 9.1.1 代码注释规范

#### 注释的黄金原则

注释不是用来解释"代码做了什么"的——代码本身应该能说明这一点。注释的职责是解释"**为什么**这样做"。

```javascript
// ❌ 烂注释：复述代码，毫无价值
const total = price * quantity; // Calculate total price

// ✅ 好注释：解释为什么，提供代码无法表达的信息
// Use Math.round instead of toFixed to avoid floating-point precision issues
// See: https://0.30000000000000004.com/
const total = Math.round(price * quantity * 100) / 100;
```

#### JSDoc 注释规范

JSDoc 是 JavaScript/TypeScript 生态中最流行的注释标准。它不仅能生成文档，还能被 IDE 识别，提供智能提示。

基本语法：

```javascript
/**
 * Calculates the discount amount for a given order.
 *
 * @param {number} originalPrice - The original price before discount, in USD.
 * @param {number} discountRate - The discount rate as a decimal (e.g., 0.2 for 20% off).
 * @param {number} [maxDiscount=100] - Optional. The maximum discount cap in USD.
 * @returns {number} The calculated discount amount, rounded to 2 decimal places.
 * @throws {Error} When originalPrice is negative or discountRate is not between 0 and 1.
 *
 * @example
 * // Returns 20
 * calculateDiscount(100, 0.2);
 *
 * @example
 * // Returns 100 (capped by maxDiscount)
 * calculateDiscount(600, 0.5, 100);
 *
 * @since 1.2.0
 * @see {@link https://company-wiki.example.com/pricing-rules|Pricing Rules}
 */
function calculateDiscount(originalPrice, discountRate, maxDiscount = 100) {
  if (originalPrice < 0) {
    throw new Error("originalPrice must be non-negative");
  }
  if (discountRate < 0 || discountRate > 1) {
    throw new Error("discountRate must be between 0 and 1");
  }

  const discount = originalPrice * discountRate;
  const cappedDiscount = Math.min(discount, maxDiscount);
  return Math.round(cappedDiscount * 100) / 100;
}
```

常用 JSDoc 标签速查表：

| 标签 | 用途 | 示例 |
|------|------|------|
| `@param` | 描述参数 | `@param {string} name - The user's name` |
| `@returns` | 描述返回值 | `@returns {boolean} True if successful` |
| `@throws` | 描述可能抛出的异常 | `@throws {TypeError} When input is invalid` |
| `@example` | 给出使用示例 | `@example` + 代码块 |
| `@deprecated` | 标记为已废弃 | `@deprecated Use `newMethod()` instead` |
| `@see` | 参考链接 | `@see {@link https://...|Documentation}` |
| `@since` | 标记引入版本 | `@since 2.1.0` |
| `@todo` | 待办事项 | `@todo Add support for negative numbers` |
| `@private` | 标记为私有 | `@private` |
| `@async` | 标记为异步函数 | `@async` |

#### Javadoc 注释规范

Java 生态的 Javadoc 格式与 JSDoc 类似，但有一些细节差异：

```java
/**
 * Retrieves a user by their unique identifier.
 *
 * <p>This method queries the primary database. If the user is not found,
 * it falls back to the cache. The method is thread-safe and can be
 * called concurrently.</p>
 *
 * @param userId the unique identifier of the user, must be positive
 * @return an {@link Optional} containing the user if found, or empty if not
 * @throws IllegalArgumentException if {@code userId} is not positive
 * @throws DatabaseException if the database is unreachable
 * @author Zhang San
 * @version 1.0
 * @since 1.5.0
 * @see User
 * @see #findUsersByRole(String)
 */
public Optional<User> findUserById(long userId) {
    // implementation...
}
```

Javadoc 与 JSDoc 的关键差异：

| 特性 | JSDoc | Javadoc |
|------|-------|---------|
| 参数描述连接符 | `-`（短横线） | 空格或 `is` |
| 类型写法 | `{typeName}` | 直接写类型名 |
| HTML 支持 | 部分 | 完整支持（`<p>`, `<code>`, `<pre>` 等） |
| `@author` | 较少使用 | 常用 |
| `@version` | 较少使用 | 常用 |

#### 注释的最佳实践

**1. TODO 注释要带信息，不只是标记**

```javascript
// ❌ 毫无信息量的 TODO
// TODO: fix this
function processData(data) { ... }

// ✅ 带上下文的 TODO
// TODO(@zhangsan, 2024-03-15): Replace with streaming approach when
// Node.js v18 becomes our minimum version. Current implementation
// loads entire dataset into memory, which causes OOM for files > 500MB.
function processData(data) { ... }
```

**2. 复杂逻辑必须注释**

```javascript
// The birthday paradox: with 23 people, there's a 50% chance two share a birthday.
// We use the approximation formula: n ≈ sqrt(2 * 365 * ln(1/(1-p)))
// where p is the desired probability threshold.
const groupSize = Math.ceil(Math.sqrt(2 * 365 * Math.log(1 / (1 - probability))));
```

**3. 警告性注释要醒目**

```javascript
// ⚠️ WARNING: Do NOT remove this seemingly useless setTimeout.
// The browser needs one event loop tick to layout the DOM before
// we can measure the element's height. Removing this causes a
// race condition that only manifests on Safari.
// See: https://bugs.webkit.org/show_bug.cgi?id=12345
setTimeout(() => measureHeight(element), 0);
```

### 9.1.2 Commit Message 写作

#### Conventional Commits 规范

Conventional Commits 是目前最广泛采用的 commit message 规范，它定义了一个统一的格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

各部分说明：

| 部分 | 是否必填 | 说明 |
|------|---------|------|
| `type` | 必填 | commit 类型，如 `feat`, `fix`, `docs` 等 |
| `scope` | 可选 | 影响的模块/范围，如 `auth`, `api`, `ui` |
| `subject` | 必填 | 简短描述， imperative mood（祈使语气） |
| `body` | 可选 | 详细说明，每行不超过 72 字符 |
| `footer` | 可选 | BREAKING CHANGE 或 issue 引用 |

常用的 type：

| type | 含义 | 示例场景 |
|------|------|---------|
| `feat` | 新功能 | 新增用户注册接口 |
| `fix` | 修 bug | 修复登录页面崩溃问题 |
| `docs` | 文档变更 | 更新 README |
| `style` | 代码格式 | 格式化、去尾部空格（不影响逻辑） |
| `refactor` | 重构 | 既不是新功能也不是修 bug 的代码变更 |
| `perf` | 性能优化 | 减少渲染次数提升性能 |
| `test` | 测试 | 新增或修改测试 |
| `chore` | 构建/工具 | 更新依赖、修改 CI 配置 |
| `ci` | CI 相关 | 修改 GitHub Actions 配置 |
| `revert` | 回滚 | 撤销某次提交 |

#### 好的 vs 坏的 Commit Message 对比

**示例 1：新功能**

```
❌ 坏的 commit message：
feat: update

❌ 稍好但还不够：
feat: added login

✅ 好的 commit message：
feat(auth): add OAuth2 login with Google

Implements the Google OAuth2 authentication flow. Users can now
sign in using their Google account. The flow uses PKCE for
enhanced security.

- Add GoogleOAuth strategy in passport config
- Create /auth/google and /auth/google/callback routes
- Store provider info in the users table
- Add automatic account linking for existing emails

Closes #142
```

**示例 2：修 Bug**

```
❌ 坏的 commit message：
fix: fixed the bug

❌ 不够清晰：
fix: login broken

✅ 好的 commit message：
fix(auth): resolve race condition in token refresh

When two API calls trigger token refresh simultaneously, the
second call would overwrite the first one's result, causing
the old refresh token to be used (and rejected) on the next
request.

The fix uses a mutex lock around the refresh logic so that
concurrent calls share the same refresh promise.

Fixes #287
```

**示例 3：Breaking Change**

```
✅ 好的 commit message：
feat(api)!: change response format from v1 to v2

BREAKING CHANGE: The `/api/users` endpoint now returns data
in a paginated format instead of a flat array. Migration steps:

1. Update clients to read `data.items` instead of `data`
2. Use `data.pagination.total` for total count
3. Add `?page=1&limit=20` query params

Migration guide: docs/migrations/v1-to-v2.md
```

**示例 4：性能优化**

```
✅ 好的 commit message：
perf(list): virtualize user list for large datasets

Previously, rendering 1000+ users caused a 3-second main thread
block. This commit implements windowed rendering using
react-window, reducing initial render to ~100ms and memory
usage by 80%.

Benchmark results (1000 items):
- Before: 3100ms render, 45MB DOM nodes
- After:  110ms render, 8MB DOM nodes
```

#### Commit Message 写作检查清单

写完 commit message 后，对照这个清单检查一遍：

- [ ] subject 用了祈使语气（`add` 而不是 `added`，`fix` 而不是 `fixed`）
- [ ] subject 首字母小写（社区惯例，除非开头是专有名词如 `iOS`）
- [ ] subject 末尾没有句号
- [ ] subject 不超过 50 个字符
- [ ] body 每行不超过 72 个字符
- [ ] body 解释了"为什么"做这个改动，而不只是"做了什么"
- [ ] 有相关的 issue 号或 PR 号引用
- [ ] Breaking change 在 footer 中明确标注

---

## 9.2 技术文档写作（README / Wiki / API Doc）

如果说代码是程序员的product，那文档就是程序员的说明书。一份好的文档能让新成员在一天内上手项目，一份烂的文档能让他们在一周内提桶跑路。

### 9.2.1 README 标准结构

README 是项目的门面。它是 GitHub 上最先被看到的东西，也是团队新成员第一个打开的文件。一个好的 README 应该让读者在 5 分钟内回答三个问题：**这是什么？能干什么？怎么开始？**

#### README 模板

以下是一个经过实战检验的 README 模板：

```markdown
# Project Name

> One-sentence description of what this project does.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://ci.example.com)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](https://ci.example.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Features

- ✨ Feature 1: Brief description
- 🚀 Feature 2: Brief description
- 🔒 Feature 3: Brief description

## Quick Start

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0 (or pnpm >= 8.0.0)
- PostgreSQL >= 14

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/your-project.git
cd your-project

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
npm run db:migrate

# Start the development server
npm run dev
```

The server will be running at `http://localhost:3000`.

## Usage

### Basic Example

```javascript
import { createClient } from 'your-project';

const client = createClient({
  apiKey: 'your-api-key',
  region: 'us-east-1',
});

const result = await client.users.create({
  name: 'Alice',
  email: 'alice@example.com',
});

console.log(result);
// { id: 'usr_123', name: 'Alice', email: 'alice@example.com' }
```

### Advanced Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | - | Required. Your API key. |
| `region` | `string` | `'us-east-1'` | AWS region. |
| `timeout` | `number` | `30000` | Request timeout in ms. |
| `retries` | `number` | `3` | Number of retry attempts. |

## Project Structure

```
src/
├── modules/          # Feature modules
│   ├── auth/         # Authentication module
│   ├── users/        # User management module
│   └── billing/      # Billing module
├── shared/           # Shared utilities
├── config/           # Configuration files
└── app.ts            # Application entry point
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Build for production |
| `npm run test` | Run unit tests |
| `npm run test:e2e` | Run end-to-end tests |
| `npm run lint` | Run ESLint |
| `npm run db:migrate` | Run database migrations |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE) © Your Organization
```

#### README 常见问题

| 问题 | 后果 | 修复方法 |
|------|------|---------|
| 没有 Quick Start | 读者直接关掉页面 | 加一个 3 步以内的上手指南 |
| 环境变量没说明 | 新人跑不起来 | 列出所有必需的环境变量及示例值 |
| badge 过多 | 分散注意力 | 保留 3-5 个最重要的 |
| 没有使用示例 | 不知道怎么用 | 至少给一个最小可运行示例 |
| 截图缺失 | UI 项目尤其需要 | 加 GIF 或截图展示效果 |

### 9.2.2 Wiki 页面组织

Wiki 适合存放项目内部文档——那些不需要出现在 README 中但对团队很重要的信息。

#### 推荐的 Wiki 结构

```
Wiki Home
├── 🏠 Home (概览 + 索引)
├── 🏗️ Architecture
│   ├── System Overview
│   ├── Data Flow Diagram
│   ├── Tech Stack Decisions
│   └── ADR (Architecture Decision Records)
├── 📋 Guides
│   ├── Onboarding Guide
│   ├── Deployment Guide
│   ├── Debugging Guide
│   └── Testing Strategy
├── 🔧 Operations
│   ├── Runbooks
│   ├── Incident Response
│   └── Monitoring & Alerting
├── 📊 Reports
│   ├── Postmortems
│   └── Sprint Retrospectives
└── 📚 Reference
    ├── Glossary
    ├── Coding Standards
    └── API Conventions
```

#### Wiki 页面写作模板

每个 Wiki 页面建议遵循以下结构：

```markdown
# Page Title

**Last updated:** 2024-03-15 by Zhang San
**Status:** Active / Draft / Deprecated

## Overview

A 2-3 sentence summary of what this page covers and who it's for.

## Background

Why does this exist? What problem does it solve?

## Content

The main body of the document. Use headings, tables, and diagrams
 liberally.

## Related

- [Link to related page 1]
- [Link to related page 2]
```

#### Architecture Decision Record (ADR) 模板

ADR 是记录技术决策的好工具，推荐每个团队都使用：

```markdown
# ADR-007: Use PostgreSQL for User Data Storage

**Date:** 2024-03-15
**Status:** Accepted
**Deciders:** Zhang San, Li Si, Wang Wu

## Context

We need to choose a database for storing user profiles and
authentication data. The current SQLite setup doesn't support
concurrent writes from multiple application servers, which we
need as we scale horizontally.

## Decision

We will use PostgreSQL 15 as our primary database for user data.

## Rationale

- **ACID compliance:** Critical for user authentication data.
- **JSON support:** `jsonb` columns allow flexible metadata storage.
- **Concurrency:** MVCC model handles concurrent reads/writes well.
- **Team familiarity:** 3 out of 4 backend engineers have PostgreSQL
  experience.
- **Ecosystem:** Excellent tooling (pgAdmin, pgvector, pg_stat).

We considered MongoDB and MySQL but ruled them out:
- MongoDB: Lack of ACID transactions (at the time of evaluation)
  poses risks for auth data.
- MySQL: Limited JSON support compared to PostgreSQL's `jsonb`.

## Consequences

- **Positive:** Better data integrity, easier to hire engineers.
- **Negative:** Need to set up managed PostgreSQL (AWS RDS), adding
  ~$200/month to infra costs.
- **Neutral:** Team needs to learn PostgreSQL-specific optimization
  techniques.
```

### 9.2.3 API 文档自动生成工具

手写 API 文档是反模式——代码变了文档没更新，最后文档变成谎言。自动生成才是正道。

#### Swagger / OpenAPI

Swagger（现在叫 OpenAPI）是 RESTful API 文档的事实标准。你可以用注解在代码中描述 API，工具会自动生成交互式文档。

**Swagger 注解示例（Node.js + swagger-jsdoc）：**

```javascript
/**
 * @openapi
 * /api/users:
 *   post:
 *     summary: Create a new user
 *     description: |
 *       Creates a new user account with the provided information.
 *       An email will be sent to the user for verification.
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - email
 *             properties:
 *               name:
 *                 type: string
 *                 description: The user's full name.
 *                 example: Alice Zhang
 *               email:
 *                 type: string
 *                 format: email
 *                 description: The user's email address.
 *                 example: alice@example.com
 *               role:
 *                 type: string
 *                 enum: [admin, member, guest]
 *                 default: member
 *                 description: The user's role.
 *     responses:
 *       201:
 *         description: User created successfully.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       400:
 *         description: Invalid input.
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 *       409:
 *         description: Email already exists.
 */
router.post('/api/users', createUser);
```

生成的文档不仅可读，还可以直接在页面上"Try it out"发送请求测试。

#### TypeDoc

TypeDoc 是 TypeScript 项目的文档生成工具，它直接从类型定义和 JSDoc 注释中生成完整的 API 文档。

**TypeScript 源码示例：**

```typescript
/**
 * Configuration options for the API client.
 *
 * @example
 * ```typescript
 * const client = new ApiClient({
 *   baseURL: 'https://api.example.com',
 *   timeout: 5000,
 *   retries: 3,
 * });
 * ```
 */
interface ApiClientOptions {
  /**
   * The base URL for all API requests.
   * Should include the protocol and domain, but no trailing slash.
   *
   * @example "https://api.example.com"
   */
  baseURL: string;

  /**
   * Request timeout in milliseconds.
   * If a request takes longer, it will be aborted.
   *
   * @default 30000
   */
  timeout?: number;

  /**
   * Number of times to retry a failed request.
   * Only retries on 5xx errors and network errors.
   *
   * @default 3
   */
  retries?: number;

  /**
   * Custom headers to include in every request.
   *
   * @default {}
   */
  headers?: Record<string, string>;

  /**
   * Whether to log requests to the console.
   * Useful for debugging in development.
   *
   * @default false
   */
  debug?: boolean;
}
```

运行 `typedoc` 后，会生成一个带搜索功能的 HTML 文档站点，效果和官方文档一样专业。

#### 工具选择参考

| 工具 | 适用场景 | 生态 | 学习成本 |
|------|---------|------|---------|
| **Swagger/OpenAPI** | RESTful API | 全语言通用 | 中等 |
| **TypeDoc** | TypeScript 库 | TS 专用 | 低 |
| **JSDoc** | JavaScript 项目 | JS 通用 | 低 |
| **Javadoc** | Java 项目 | Java 专用 | 低 |
| **Godoc** | Go 项目 | Go 内置 | 极低 |
| **Sphinx** | Python 项目 | Python 通用 | 中等 |
| **Docusaurus** | 文档站点 | React 生态 | 中等 |
| **VitePress** | 文档站点 | Vue 生态 | 低 |

---

## 9.3 技术博客写作（结构 / 选题 / SEO）

写技术博客是最好的深度学习方式——你写不清楚，说明你想不清楚。费曼说得好："If you can't explain it simply, you don't understand it well enough."

### 9.3.1 博客结构模板

一篇好的技术博客应该像一个好故事：有开头（问题是什么）、有中间（怎么解决的）、有结尾（效果如何）。

#### 标准技术博客模板

```markdown
# [Hook Title]: [Descriptive Subtitle]

## TL;DR

One paragraph summarizing the problem, solution, and result.
For readers who only have 30 seconds.

## The Problem

Describe the problem you encountered. Be specific:
- What were you trying to do?
- What went wrong?
- What was the impact?

## Context

Give readers enough background to understand the problem:
- Tech stack
- System architecture (with diagram if possible)
- Constraints and requirements

## The Journey

This is the main body. Walk readers through your problem-solving process:

### Attempt 1: The Obvious Solution

Why it didn't work...

### Attempt 2: A Better Approach

What changed and why...

### The Final Solution

The solution that actually worked, with code:

\```language
// Clean, well-commented code here
\```

## Results

Quantify the improvement if possible:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Page load | 3.2s | 0.8s | -75% |
| Bundle size | 2.1MB | 680KB | -68% |
| LCP | 4.1s | 1.2s | -71% |

## Lessons Learned

What did you learn that others might benefit from?

## References

- [Link to relevant docs]
- [Link to inspiring articles]
- [Link to source code]
```

#### 标题写作技巧

标题是博客最重要的部分——它决定了 80% 的点击率。

| 标题类型 | 示例 | 效果 |
|---------|------|------|
| 问题式 | "Why Is My React App So Slow?" | ✅ 引起共鸣 |
| 数字式 | "5 Ways to Optimize Your React App" | ✅ 明确预期 |
| 对比式 | "Redux vs Zustand: A Practical Comparison" | ✅ 帮助决策 |
| 故事式 | "How We Cut Our Bundle Size by 70%" | ✅ 引发好奇 |
| 指南式 | "The Complete Guide to React Server Components" | ✅ 权威感 |
| ❌ 模糊式 | "Some Thoughts on React" | ❌ 没人点 |
| ❌ 学术式 | "An Analysis of Client-Side Rendering Performance Characteristics" | ❌ 太学术 |

### 9.3.2 选题策略

好的选题 = 你懂的 × 别人需要的 × 没人写过的。

#### 选题来源

**1. 踩坑记录（最真实，最受欢迎）**

每次解决一个棘手 bug，都是一篇博客的素材。记录下来：

- 症状是什么？（现象描述）
- 你以为是啥？（初步假设）
- 实际是啥？（根因分析）
- 怎么修的？（解决方案）
- 为什么会这样？（原理解释）

**2. 新技术实践（时效性强）**

新框架、新工具发布后，大家都在搜怎么用。第一时间写上手教程，流量很大。

**3. 性能优化案例（数据说话）**

有具体数字的优化案例天然有说服力：

```
✅ 好的选题："How We Reduced Our API Response Time from 2s to 200ms"
❌ 空洞的选题："How to Optimize API Performance"
```

**4. 架构设计复盘（深度内容）**

讲一个系统的设计过程，包括为什么选 A 不选 B，踩了哪些坑。

**5. 工具链/流程改进（实用价值高）**

"Our CI/CD Pipeline Setup: From 30min to 5min" 这类文章总是有人需要的。

#### 选题评估矩阵

给每个选题打分（1-5），总分 > 12 就值得写：

| 维度 | 问题 |
|------|------|
| 需求度 | 有人在搜这个问题吗？ |
| 独特性 | 已有文章覆盖了吗？我有什么不同视角？ |
| 深度 | 我能写出超越官方文档的内容吗？ |
| 时效性 | 这个话题能火多久？ |
| 个人价值 | 写完我自己也能复习吗？ |

### 9.3.3 SEO 基础

写了好文章没人看等于白写。基础的 SEO 能让你的文章被更多人搜到。

#### Title 标签

```html
<!-- ❌ 模糊的 title -->
<title>My Blog Post</title>

<!-- ❌ 过长的 title（搜索引擎会截断） -->
<title>How I Optimized My React Application's Rendering Performance Using useMemo, useCallback, and React.memo</title>

<!-- ✅ 好的 title：55-60 字符，关键词在前 -->
<title>React Performance Optimization: A Practical Guide</title>
```

Title 写作原则：
- 控制在 55-60 个字符（Google 大约显示 60 个字符）
- 核心关键词放在前面
- 包含一个吸引点击的修饰词（Practical, Complete, 2024, Step-by-Step）

#### Meta Description

```html
<!-- ❌ 没有 description -->
<meta name="description" content="">

<!-- ❌ 关键词堆砌 -->
<meta name="description" content="React optimization, React performance, useMemo, useCallback, React.memo, virtual DOM, rendering">

<!-- ✅ 好的 description -->
<meta name="description" content="Learn how to identify and fix React performance bottlenecks using profiling tools, memoization, and virtualization. Includes real-world examples and benchmarks.">
```

Description 写作原则：
- 控制在 150-160 个字符
- 用一句话概括文章内容和价值
- 包含关键词但不要堆砌
- 用动词开头（Learn, Discover, Master, Build）

#### URL Slug

```bash
# ❌ 不好的 URL
/blog/post-123
/blog/2024/03/15/my-thoughts

# ✅ 好的 URL：短、含关键词、用连字符
/blog/react-performance-optimization
/blog/docker-multi-stage-builds
```

#### 关键词策略

不要为了 SEO 硬塞关键词。自然地使用术语，在以下位置包含关键词即可：

| 位置 | 说明 |
|------|------|
| 文章标题 (H1) | 最重要的关键词放这里 |
| 前 100 个字 | 文章开头自然包含关键词 |
| 小标题 (H2/H3) | 使用关键词的变体 |
| 图片 alt 属性 | 描述图片内容，顺便包含关键词 |
| URL slug | 简短的关键词组合 |
| 代码注释 | 代码块中的注释也能被索引 |

#### 技术博客 SEO 检查清单

- [ ] Title 包含核心关键词，< 60 字符
- [ ] Meta description 存在，150-160 字符
- [ ] URL slug 简短且含关键词
- [ ] 文章有且只有一个 H1
- [ ] 使用了 H2/H3 组织内容结构
- [ ] 图片有 alt 属性
- [ ] 代码块标注了语言
- [ ] 有内链（链接到你其他文章）
- [ ] 有外链（链接到权威来源）
- [ ] 页面加载速度快（< 3s）
- [ ] 移动端可读性良好

---

## 9.4 RFC 与技术方案文档写作

RFC（Request for Comments）是技术决策的正式文档。它不是给你看的，是给三个月后的团队看的——那时候你可能已经忘了当时为什么这么决定。

### 9.4.1 RFC 模板

以下是一个经过多家大厂验证的 RFC 模板：

```markdown
# RFC: [Project Name] - [Short Title]

- **Author:** Zhang San (zhangsan@example.com)
- **Reviewers:** Li Si, Wang Wu
- **Created:** 2024-03-15
- **Last Updated:** 2024-03-20
- **Status:** Under Review / Approved / Rejected / Implemented
- **Related RFCs:** RFC-003 (Data Pipeline v2)

## Summary

One paragraph (3-5 sentences) explaining what this RFC proposes
and why. This should be understandable by someone outside the team.

## Background

### Current State

Describe how things work today. What system exists? What process
is in place? Be factual and specific.

Currently, our notification system sends emails synchronously
during HTTP request processing. When the email service is slow
(>2s), the API response time degrades, and under high load,
request timeouts occur.

### Motivation

Why are we proposing this change? What problem does it solve?

During Black Friday 2023, the email service experienced a 5x
traffic spike. API timeout rate increased from 0.1% to 12%,
affecting 15,000 users. We need to decouple email sending from
request processing.

### Goals

- Reduce API response time for endpoints that trigger notifications
- Handle email service outages gracefully
- Support notification priority (transactional > promotional)

### Non-Goals

- Replacing the email service provider
- Adding new notification channels (SMS, push) — tracked in RFC-012
- Changing the email template system

## Proposal

### Overview

Describe the proposed solution at a high level. Use diagrams if
possible.

We propose introducing an asynchronous notification queue between
the application and the email service. The application publishes
notification events to a Redis stream; a worker service consumes
events and calls the email API.

\```
┌──────────┐    publish     ┌───────────┐    consume     ┌──────────┐
│   App    │ ────────────── │  Redis    │ ───────────── │  Worker  │
│ Service  │   notification  │  Stream   │   events       │  Service │
└──────────┘   events        └───────────┘                └──────────┘
     │                                                          │
     │            ┌──────────────┐                              │
     └─────────── │   Email API  │ ◄────────────────────────────┘
                  └──────────────┘
\```

### Detailed Design

#### Data Model

\```sql
CREATE TABLE notifications (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id),
  type        VARCHAR(50) NOT NULL,
  priority    SMALLINT NOT NULL DEFAULT 5,
  payload     JSONB NOT NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'pending',
  attempts    INT NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_status_priority
  ON notifications (status, priority, created_at);
\```

#### API Changes

New endpoint for checking notification status:

\```
GET /api/notifications/:id

Response 200:
{
  "id": "notif_abc123",
  "status": "sent",
  "type": "order_confirmation",
  "created_at": "2024-03-15T10:00:00Z",
  "sent_at": "2024-03-15T10:00:02Z"
}
\```

#### Error Handling

| Scenario | Behavior |
|----------|----------|
| Redis unavailable | Fall back to synchronous send + log warning |
| Email API 4xx | Mark as failed, no retry (likely permanent error) |
| Email API 5xx | Retry with exponential backoff (1s, 4s, 16s, 64s, 256s) |
| Max retries exceeded | Move to dead-letter queue, alert on-call engineer |

### Alternatives Considered

#### Alternative 1: AWS SQS instead of Redis Streams

- **Pros:** Fully managed, no infrastructure to maintain
- **Cons:** Higher latency (~50ms vs ~5ms), vendor lock-in,
  costs scale with usage ($0.40 per million requests + data transfer)
- **Decision:** Rejected. We already operate Redis for caching,
  and the latency difference is significant for transactional emails.

#### Alternative 2: Direct cron-based batch sending

- **Pros:** Simple, no new infrastructure
- **Cons:** Cannot support real-time notifications, harder to
  handle priority, email delays up to 5 minutes
- **Decision:** Rejected. Transactional emails (order confirmations,
  password resets) require near-real-time delivery.

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Redis stream data loss | Medium | Low | Enable AOF persistence, monitor lag |
| Worker crashes mid-processing | Low | Medium | Use consumer groups with pending entries list (PEL) |
| Email API rate limit hit | High | Medium | Implement rate limiting in worker, queue excess |
| Team unfamiliar with Redis Streams | Low | High | Pair programming, code walkthrough session |

## Rollout Plan

1. **Week 1-2:** Implement core infrastructure (Redis stream, worker service)
2. **Week 3:** Integrate with existing notification triggers (behind feature flag)
3. **Week 4:** Canary rollout to 5% of traffic, monitor metrics
4. **Week 5:** Full rollout if no issues, deprecate synchronous path

## Open Questions

1. Should we support notification batching for promotional emails?
2. Do we need a admin UI for viewing/replaying failed notifications?
3. What's our retention policy for the notifications table?

## References

- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [RFC-003: Data Pipeline v2](link-to-rfc-003)
- [Incident Report: Black Friday 2023 Notification Failure](link-to-postmortem)
```

### 9.4.2 如何写好 Background

Background 是 RFC 中最重要的部分之一。它回答的是"为什么要做这件事"。写好 Background 的关键是用**事实和数据**说话，而不是主观感受。

#### Background 写作原则

**1. 描述现状，不要跳到解决方案**

```markdown
❌ 错误写法（急于给方案）：
The current notification system is bad. We should use Redis Streams
to make it asynchronous and add a worker service.

✅ 正确写法（先描述现状）：
The notification system currently sends emails synchronously
during HTTP request processing. The average email send time is
800ms, which adds directly to API response latency. During peak
traffic (Black Friday 2023), email send time increased to 4.2s
on average, causing 12% of API requests to timeout.
```

**2. 用数据支撑问题**

```markdown
❌ 模糊的描述：
The system is slow and unreliable.

✅ 有数据的描述：
P99 API latency during peak hours: 4.2s (target: <500ms)
Notification failure rate: 3.2% (target: <0.1%)
On-call alerts related to notifications: 14 in Q4 2023
```

**3. 明确 Goals 和 Non-Goals**

Goals 和 Non-Goals 同样重要。写 Non-Goals 是为了防止范围蔓延（scope creep）。

```markdown
✅ 好的 Goals：
- Reduce P99 API latency for notification-triggering endpoints to <500ms
- Support notification priority levels (1=transactional, 5=promotional)
- Achieve at-least-once delivery guarantee

✅ 好的 Non-Goals：
- Adding SMS or push notification channels (separate RFC)
- Migrating to a new email service provider (not in scope)
- Building a notification template editor UI (product team owns this)
```

### 9.4.3 如何写好 Proposal

Proposal 部分需要做到"详细到另一个工程师可以照着实现"。以下是检查清单：

- [ ] 有架构图或流程图
- [ ] 数据模型/Schema 变更已定义
- [ ] API 接口变更已定义（包括请求/响应格式）
- [ ] 错误处理策略已说明
- [ ] 边界情况已考虑
- [ ] 安全影响已评估
- [ ] 性能影响已分析
- [ ] 回滚方案已有

#### Alternatives Considered 的写作技巧

这部分经常被忽略，但它其实是最有价值的部分之一。写 Alternatives 时要注意：

```markdown
✅ 好的 Alternative 写法：

#### Alternative 1: AWS SQS

- Pros: Fully managed, auto-scaling, no infrastructure overhead
- Cons: Higher latency (~50ms vs ~5ms for Redis), vendor lock-in,
  cost ~$200/month at projected volume
- Why rejected: We already operate Redis clusters with spare capacity.
  The 10x latency difference is critical for transactional emails.

❌ 烂的 Alternative 写法：

#### Alternative 1: SQS
Considered but decided against it.
```

好的 Alternative 要包含三个要素：**优点**、**缺点**、**为什么否决**。这样后人回看时能理解你的决策逻辑。

---

## 9.5 事故复盘报告写作

线上出事了，救火完了，还没完——你得写 Postmortem。Postmortem 不是用来追责的，是用来避免下次踩同一个坑的。好的团队文化是 blameless（不追责），关注系统和流程的问题，而不是个人的失误。

### 9.5.1 Postmortem 写作模板

以下是一个标准的 Postmortem 模板：

```markdown
# Postmortem: [Incident Title]

**Date of Incident:** 2024-03-15
**Author:** Zhang San (On-call Engineer)
**Severity:** SEV-1 (Critical)
**Duration:** 2 hours 15 minutes (14:00 - 16:15 UTC)
**Affected Services:** User Authentication API, Checkout API
**Impact:** ~8,500 users unable to log in or complete purchases
  for ~2 hours. Estimated revenue loss: $45,000.

## Summary

A configuration change to the Redis cluster triggered a cascading
failure in the authentication service. The change caused Redis
connection pool exhaustion, which in turn caused all auth API
requests to timeout. The issue was resolved by rolling back the
configuration change and restarting affected services.

## Timeline

All times in UTC.

| Time | Event |
|------|-------|
| 13:45 | Engineer pushed Redis config change via CI/CD pipeline |
| 13:50 | Deployment completed, config applied to all Redis nodes |
| 14:00 | Auth API P99 latency began rising (500ms → 3s) |
| 14:03 | PagerDuty alert: Auth API error rate > 5% |
| 14:05 | On-call engineer acknowledged alert, began investigation |
| 14:10 | Confirmed auth API was returning 503 errors |
| 14:15 | Identified Redis connection pool exhaustion in logs |
| 14:20 | Checked recent deployments, found Redis config change |
| 14:25 | Decision made to roll back the config change |
| 14:30 | Rollback initiated |
| 14:35 | Redis config reverted to previous version |
| 14:40 | Auth API error rate began dropping |
| 14:50 | Auth API fully recovered |
| 15:00 | Checkout API still degraded (caching stale data) |
| 15:15 | Cleared checkout service cache, forced reconnection |
| 15:30 | Checkout API fully recovered |
| 16:15 | All monitoring dashboards confirmed normal operation |
| 16:30 | Incident declared resolved |

## Root Cause Analysis

### What Happened

A Redis configuration change was deployed to increase the
`maxmemory-policy` from `allkeys-lru` to `volatile-ttl`. The intent
was to prioritize keeping TTL-based keys (session data) over
LRU-evicted keys (cache data).

### Why It Caused a Failure

The new policy caused a significant increase in eviction rates for
non-TTL keys. The authentication service stored session data with
TTL, but also used Redis for distributed locking (without TTL).
Under the new policy, lock keys were evicted, causing:

1. Distributed locks to be released prematurely
2. Concurrent requests to acquire the same lock
3. Race conditions in session token validation
4. Session token corruption in Redis
5. Auth API returning 401 errors for valid tokens

The connection pool exhaustion was a secondary effect: corrupted
sessions caused retries, which increased the number of Redis
commands per request, exhausting the connection pool.

### Contributing Factors

1. **No staged rollout:** The config change was applied to all
   Redis nodes simultaneously instead of rolling out to one node
   first.
2. **Insufficient monitoring:** Redis eviction rate was not
   alerted on. The increase in evictions went unnoticed for 10
   minutes before the auth API was affected.
3. **Missing integration test:** The CI pipeline did not test
   distributed locking behavior under the new Redis config.
4. **Runbook gap:** The Redis runbook did not mention distributed
   lock keys as a consideration when changing eviction policy.

## Action Items

| # | Action | Owner | Priority | Due Date | Status |
|---|--------|-------|----------|----------|--------|
| 1 | Add staged rollout for Redis config changes | DevOps Team | P0 | 2024-03-22 | Open |
| 2 | Add alerting for Redis eviction rate (>1000/min) | DevOps Team | P0 | 2024-03-20 | Open |
| 3 | Add integration test for distributed locking | Backend Team | P1 | 2024-03-29 | Open |
| 4 | Update Redis runbook with eviction policy guidance | Zhang San | P1 | 2024-03-22 | Open |
| 5 | Review all Redis key usage for TTL compliance | Backend Team | P2 | 2024-04-05 | Open |
| 6 | Add circuit breaker for auth API Redis calls | Backend Team | P1 | 2024-03-29 | Open |

## Lessons Learned

### What Went Well

- Detection was fast: alert fired within 3 minutes of impact
- On-call engineer quickly identified the root cause
- Rollback was straightforward and effective

### What Went Wrong

- Config change bypassed staged rollout (no feature flag)
- No pre-deployment testing for the specific config change
- Distributed lock keys lacking TTL was a latent bug

### Where We Got Lucky

- The rollback was simple (revert config, restart services)
- No data was permanently corrupted (sessions regenerated)
- Incident occurred during business hours, full team available

## Appendix

- [Grafana dashboard during incident](link)
- [Slack thread: #incident-2024-03-15](link)
- [PagerDuty incident timeline](link)
- [Redis config diff](link)
```

### 9.5.2 如何客观描述 Timeline

Timeline 是 Postmortem 中最实用的部分——它是未来排查类似问题时最好的参考。写 Timeline 的原则是：**只记事实，不记判断**。

```markdown
❌ 带主观判断的写法：
14:05 - On-call engineer finally responded (took too long)
14:10 - Engineer made a mistake by checking the wrong dashboard
14:20 - After wasting time on wrong hypothesis, checked deployments

✅ 客观事实的写法：
14:05 - On-call engineer acknowledged alert (response time: 2min)
14:10 - Engineer checked application dashboard (API error rates)
14:15 - Engineer checked infrastructure dashboard (Redis metrics)
14:20 - Engineer reviewed recent deployments, identified config change
```

#### Timeline 写作原则

1. **统一时区**：用 UTC 或明确标注时区，避免混乱
2. **精确到分钟**：重大事件精确到秒
3. **包含决策点**：记录"决定做什么"的时刻，不只是"做了什么"
4. **包含误判**：走弯路也是事实，记录下来帮助后人
5. **不追责**：不写"XXX 的失误"，写"系统/流程的问题"

### 9.5.3 如何写好 Root Cause

Root Cause 分析是最考验功力的部分。好的 Root Cause 分析应该像剥洋葱一样，一层层深入，直到找到最根本的原因。

#### 5 Whys 方法

```markdown
**Why did the auth API return 503 errors?**
→ Because the Redis connection pool was exhausted.

**Why was the connection pool exhausted?**
→ Because there was a 10x increase in Redis commands per request.

**Why did Redis commands per request increase 10x?**
→ Because session validation was failing, causing retries.

**Why was session validation failing?**
→ Because session tokens in Redis were being corrupted.

**Why were session tokens being corrupted?**
→ Because distributed lock keys (without TTL) were being evicted
   under the new eviction policy, causing concurrent writes to
   the same session tokens.

**Root Cause:** The Redis configuration change did not account for
non-TTL keys used by the distributed locking mechanism. Changing
the eviction policy from `allkeys-lru` to `volatile-ttl` caused
lock keys to be evicted, leading to race conditions and data
corruption.
```

#### 常见的 Root Cause 写作误区

| 误区 | 示例 | 改进 |
|------|------|------|
| 停在表面 | "Redis config was wrong" | 继续追问为什么 config 是错的 |
| 追责个人 | "Engineer deployed without testing" | "CI pipeline lacked pre-deployment test for config changes" |
| 只归咎于一个原因 | "It was a bad config" | 通常有多个 contributing factors |
| 忽略系统性问题 | "Human error" | "Process allowed a risky change without review" |

---

## 9.6 技术演讲 PPT 文案写作

程序员迟早要上台——做技术分享、产品 demo、架构评审。PPT 是你的视觉辅助，不是你的提词器。好的技术 PPT 让观众秒懂你的意思，烂的 PPT 让观众忙着读字而忽略你说了什么。

### 9.6.1 PPT 文案原则

#### 原则 1：少字多图

```
❌ 烂的 slide：
──────────────────────────────
| Our Architecture           |
|                            |
| We use a microservices     |
| architecture with React    |
| frontend, Node.js backend, |
| PostgreSQL database, and    |
| Redis cache. The API        |
| gateway handles auth and    |
| routing. Message queue is   |
| RabbitMQ.                   |
|                            |
──────────────────────────────

✅ 好的 slide：
──────────────────────────────
|     System Architecture    |
|                            |
|  [架构图：React → Gateway   |
|   → Node.js → PostgreSQL    |
|   + Redis + RabbitMQ]       |
|                            |
──────────────────────────────
```

如果一页 PPT 的文字超过 6 行，考虑拆成多页或用图替代。

#### 原则 2：一页一个观点

每页 slide 只传达一个核心信息。不要在一页里塞三个不相关的概念。

```markdown
❌ 一页塞太多：
| Performance Optimization Results |
| • API latency reduced by 60%    |
| • Bundle size reduced by 40%     |
| • We also refactored the auth    |
|   module and upgraded to React 18|
| • Database queries optimized     |
| • Added Redis caching layer      |

✅ 拆成多页：
Slide 1: "API Latency: -60%" + 折线图
Slide 2: "Bundle Size: -40%" + 柱状图
Slide 3: "Optimization Strategies" + 5个icon的列表
```

#### 原则 3：用对比代替描述

与其描述"优化前是什么样"，不如直接展示"优化前 vs 优化后"。

```
✅ 好的 slide 布局：
┌──────────────┬──────────────┐
│   Before     │   After      │
│              │              │
│ [截图/Demo]  │ [截图/Demo]  │
│              │              │
│ Load: 3.2s   │ Load: 0.8s   │
│ Size: 2.1MB  │ Size: 680KB  │
└──────────────┴──────────────┘
```

#### 原则 4：代码要大要少

技术分享难免要展示代码。但 PPT 上的代码不是给读者复制粘贴的——是用来展示思路的。

```markdown
❌ PPT 上的代码太多：
// 完整的 100 行实现，字小到看不清

✅ PPT 上的代码精简到核心：
// 只保留关键逻辑，伪代码也行
async function refreshToken(token) {
  const { accessToken, refreshToken } = await api.refresh(token);
  setTokens({ accessToken, refreshToken });
  return accessToken;
}

// 其他细节用 "..." 省略
```

PPT 代码展示技巧：
- 字号至少 20px（观众在最后一排也要看清）
- 最多 10 行代码
- 高亮关键行（用不同颜色）
- 删掉非核心代码（import 语句、类型定义等）

### 9.6.2 演讲备注写作

PPT 上放的是给观众看的，备注里写的是给你自己说的。好的备注能让你在台上不慌不忙，像聊天一样自然。

#### 演讲备注模板

```markdown
## Slide 1: Title

**PPT 内容：** 项目名称 + 你的名字 + 一句话副标题

**备注：**
Hi everyone, I'm Zhang San from the Platform team. Today I'll
be talking about how we redesigned our API gateway to handle
10x traffic growth. This is a story about scaling, breaking
things, and fixing them.

[Wait for laughs / pause]

---

## Slide 2: The Problem

**PPT 内容：** 一张 API error rate 飙升的截图

**备注：**
This is what our error rate looked like on Black Friday 2023.
Within 30 minutes, we went from 0.1% to 12% error rate. That's
about 15,000 users who couldn't use our product.

[Pause for effect]

The question was: why? And more importantly: how do we make
sure this never happens again?

---

## Slide 3: Current Architecture

**PPT 内容：** 系统架构图

**备注：**
Let me quickly walk you through our architecture at the time.
We had a single Node.js API server sitting behind nginx. All
requests went through the same codebase — auth, billing,
search, everything.

[Point to different parts of the diagram as you explain]

The problem with this setup is that a slow endpoint affects
everything. If search gets slow, login gets slow too, because
they share the same event loop.

---

## Slide 4: The Solution

**PPT 内容：** 新架构图（微服务 + API Gateway）

**备注：**
So we decided to split the monolith into microservices, with
an API gateway in front. The gateway handles routing,
authentication, and rate limiting. Each service is independent
and can scale on its own.

The key insight was: we didn't need to rewrite everything at
once. We started with the most critical service — authentication
— and gradually extracted others.

---

## Slide 5: Results

**PPT 内容：** Before/After 对比表

**备注：**
Here are the results after 3 months. API latency dropped by 60%,
error rate is back to 0.1%, and we can now scale individual
services based on their load.

But the most important metric is this: during our last sale
event, we handled 5x the Black Friday traffic with zero
incidents. That's the real win.

[Pause for applause / questions]
```

#### 备注写作技巧

**1. 用口语化语言写**

备注不是文章，是你说话的脚本。写得像你平时聊天一样：

```markdown
❌ 书面语（念起来别扭）：
"Subsequently, we implemented a distributed caching mechanism
utilizing Redis, which resulted in a significant reduction
in database query latency."

✅ 口语化（说起来自然）：
"So we added Redis as a cache layer. The result? Database
queries went from 200ms to 20ms. That's a 10x improvement,
just from caching."
```

**2. 标注停顿和互动**

```markdown
[Pause for effect] - 重要数据后停顿
[Wait for laughs] - 段子后等笑声
[Raise hand] - 互动时举手
[Point to screen] - 指向屏幕特定位置
[Drink water] - 长段讲解前喝水
```

**3. 用短句**

说话时的句子要比写文章短得多。一口气能说完的句子才适合口语。

```markdown
❌ 太长（说到一半要换气）：
"What we found was that the main bottleneck was actually not
in the database layer as we initially suspected, but rather
in the serialization logic that was running synchronously
on the main thread."

✅ 拆短（每句一个信息点）：
"We thought the bottleneck was the database. It wasn't.
It was the serialization logic. That was running on the
main thread. Synchronously. Blocking everything else."
```

### 9.6.3 技术演讲结构模板

一个 20 分钟的技术演讲建议按以下结构组织：

| 时间 | 环节 | 内容 | PPT 页数 |
|------|------|------|---------|
| 0-2min | 开场 | Hook：用一个故事或数据抓住注意力 | 1-2 |
| 2-5min | 背景 | 问题是什么，为什么重要 | 3-4 |
| 5-8min | 方案 | 你的解决方案概述 | 2-3 |
| 8-15min | 深入 | 技术细节、代码示例、架构图 | 5-8 |
| 15-17min | 效果 | 数据对比、用户反馈 | 2-3 |
| 17-19min | 教训 | 踩过的坑、经验总结 | 1-2 |
| 19-20min | 收尾 | 总结 + Q&A 引导 | 1 |

总计约 15-22 页 PPT，对于 20 分钟的演讲来说是合理的节奏。

---

## 本章小结

技术写作不是一个独立技能，而是贯穿在程序员日常工作每个环节的基本功。回顾一下这一章的核心内容：

1. **代码注释**：解释"为什么"而不是"是什么"。JSDoc/Javadoc 规范化的注释既能让 IDE 智能提示，也能自动生成文档。

2. **Commit Message**：遵循 Conventional Commits 规范，用祈使语气，body 解释为什么，footer 引用 issue。一条好的 commit message = 一条好的变更日志。

3. **技术文档**：README 要在 5 分钟内回答"是什么/能干什么/怎么开始"。Wiki 用于团队内部知识沉淀。API 文档要自动化生成， Swagger 和 TypeDoc 是两大利器。

4. **技术博客**：用"问题-旅程-结果"的故事结构，选题从踩坑记录和新实践经验中来。SEO 基础：title 精准、description 有吸引力、URL 含关键词。

5. **RFC**：Background 用数据说话，Proposal 要详细到别人能照着实现，Alternatives 要记录优缺点和否决理由。RFC 是给未来的团队看的，写得越清楚，未来踩坑越少。

6. **Postmortem**：Blameless 原则——关注系统和流程，不追责个人。Timeline 只记事实，Root Cause 用 5 Whys 深挖到底。Action Items 必须有负责人和截止日期。

7. **技术演讲**：PPT 少字多图、一页一观点。备注用口语化短句写，标注停顿和互动点。20 分钟演讲约 15-22 页 PPT。

记住，技术写作的目标不是展示文采，而是**高效传递信息**。写得清楚、准确、简洁，就是好技术写作。用的一句话总结这一章：

> Good technical writing is invisible — readers don't notice it, they just understand.

好的技术写作是隐形的——读者不会注意到它写得好，他们只是……懂了。
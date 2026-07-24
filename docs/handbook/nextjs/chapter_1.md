# 第1章 走进Next.js：现代React全栈开发框架

搞了3年前端，项目越做越大，构建配置越来越复杂，SEO优化全靠补丁，首屏白屏被产品经理追着问——问题其实出在框架选型上。

我是怕浪猫，一个在前后端横跳了多年的全栈开发者。从jQuery时代一路写到React、Vue，经历过Webpack配置地狱，也踩过SSR的各种坑。接下来16章，我会带你从零吃透Next.js，这一章先帮你建立完整的认知框架。

## 1.1 现代前端开发的痛点与困境

### 1.1.1 单页应用（SPA）的SEO困境与首屏白屏问题

先说一个最经典的场景。你用React写了一个漂亮的官网，本地开发一切正常，上线之后打开F12看看网络请求——一个空的`<div id="root"></div>`，然后等JS下载、解析、执行，页面才渲染出来。

这就是SPA（Single Page Application，单页应用）的核心问题。浏览器拿到的HTML只是一个空壳，所有内容都依赖JavaScript动态渲染。带来的后果有两个：

第一，SEO（Search Engine Optimization，搜索引擎优化）几乎为零。搜索引擎爬虫抓取到的HTML是空的，你的页面再好看，搜索引擎也看不到内容。虽然Google爬虫能执行JS，但收录效果远不如直接有内容的HTML。

第二，首屏白屏。用户打开页面后，需要等待JS bundle下载、解析、执行完毕，才能看到内容。在网络较差的环境下，白屏时间可能长达3-5秒。

```
传统SPA加载流程：

浏览器请求 → 服务器返回空HTML → 下载JS Bundle → 解析执行 → 渲染页面
     |__________ 空白等待期 ___________|_______ 白屏期 _______|
```

> 金句：SPA的"单页"不是把所有内容塞进一个页面，而是把所有负担塞进了一次JS加载。

### 1.1.2 传统React项目的构建复杂度与配置地狱

如果你从零搭建过React项目，一定体会过配置的痛苦。先看一个典型的手动配置清单：

| 配置项 | 工具 | 复杂度 |
|--------|------|--------|
| 模块打包 | Webpack/Vite | 高 |
| 代码编译 | Babel/SWC | 中 |
| 代码分割 | 手动配置SplitChunks | 高 |
| 热更新 | webpack-dev-server | 中 |
| SSR支持 | express + renderToString | 极高 |
| 图片优化 | 自建处理管线 | 高 |
| 环境变量 | dotenv手动接入 | 低 |

create-react-app（CRA）虽然提供了一键创建，但它把配置藏了起来。一旦你需要自定义Webpack配置，要么eject暴露全部配置（然后面对几千行配置文件发呆），要么用craco等工具覆写（然后和版本升级做斗争）。

怕浪猫第一次做SSR项目的时候，光是配Webpack的server端和client端双入口就折腾了两天。要是当时有Next.js，这些全都不用管。

### 1.1.3 全栈开发的技术栈割裂：前端与后端的协作成本

传统的前后端分离架构中，前端用React/Vue写页面，后端用Express/Spring Boot写接口，两边通过API通信。这种模式看似清晰，实际开发中存在大量协作成本。

前端开发者需要理解后端的API文档，后端开发者需要理解前端的数据需求。接口变更时需要双方同步，联调阶段经常出现"接口字段名不一致""数据结构对不上"之类的问题。更别提CORS（Cross-Origin Resource Sharing，跨源资源共享）配置、接口Mock、环境切换这些琐碎但耗时的事情。

如果前端框架本身具备全栈能力，前端开发者直接在同一个项目里写接口、操作数据库，这些协作成本就大幅降低。这正是Next.js带来的改变。

举一个具体的场景：产品经理说"给文章列表加一个按阅读量排序的功能"。在传统架构中，前端提需求让后端加一个sort参数，后端排期三天后上线，前端再适配接口变更，来回一周过去了。在Next.js全栈模式下，前端直接在Server Component中修改数据库查询，加上`orderBy: { views: 'desc' }`，5分钟搞定。这不是效率提升，而是工作流的根本改变。

### 1.1.4 性能瓶颈：从代码分割到按需加载的探索

React应用的性能问题，本质上是一个"加载多少、何时加载"的问题。初学者往往把所有代码打成一个bundle，结果首屏加载一个2MB的JS文件。老手会做代码分割，但手动配置Webpack的SplitChunks规则并不轻松。

```javascript
// 手动代码分割示例 - 传统React项目
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));

function App() {
  return (
    <Suspense fallback={<div>加载中...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Suspense>
  );
}
```

而Next.js的文件式路由天然支持代码分割——每个`page.tsx`自动成为一个独立的chunk，路由跳转时按需加载，无需任何手动配置。这不是什么黑科技，但用起来就是爽。

再深入一点看性能优化的全景。现代前端性能优化有三个核心方向：减少首屏JS体积、减少网络请求数、提前获取关键资源。传统React项目在这三个方向上都需要手动配置：手动React.lazy做代码分割、手动配置preload和prefetch、手动优化图片加载。而Next.js在框架层面内置了这些能力——Link组件自动prefetch目标路由、Image组件自动做图片压缩和懒加载、Server Components默认不增加客户端JS体积。框架级优化和手动优化的差距，随着项目规模增长会越来越明显。

### 1.1.5 企业级项目对工程化与规范化的迫切需求

企业级项目和玩具项目的区别在哪？不在于功能多少，而在于工程化程度。一个真正的企业级项目需要：统一的目录规范、TypeScript类型安全、ESLint+Prettier代码规范、Git提交规范、环境变量管理、CI/CD流水线、性能监控、错误上报。

这些事情，用纯React + Webpack方案，每一项都需要手动搭建。而Next.js在框架层面提供了很大一部分支持：内置TypeScript支持、内置ESLint配置、内置环境变量管理、内置构建优化。剩下的部分也因为有约定俗成的社区规范，搭起来比从零开始快得多。

举个实际的例子：配置环境变量。在传统React项目中，你需要安装dotenv，在webpack配置中注入环境变量，还要区分开发环境和生产环境。在Next.js中，只需要在项目根目录创建`.env.local`文件，写入`API_URL=https://api.example.com`，然后在代码中直接用`process.env.API_URL`就能访问。以`NEXT_PUBLIC_`开头的变量还会自动暴露给浏览器端。零配置，开箱即用。

## 1.2 Next.js的发展历程与版本迭代（重点App Router）

### 1.2.1 Next.js诞生背景：从6行代码到框架级方案

2016年10月，Zeit公司（现在叫Vercel）的Guillermo Rauch发了一条推文，展示了一个6行代码的SSR React应用：

```javascript
// Next.js最初的灵感来源
import express from 'express';
import React from 'react';
import { renderToString } from 'react-dom/server';

const app = express();
app.get('*', (req, res) => {
  res.send(renderToString(<App />));
});
app.listen(3000);
```

这6行代码揭示了一个核心需求：React应用需要服务端渲染，但现有的方案太复杂了。于是Next.js诞生了，它的目标很简单——让React应用默认就有SSR能力，开发者不需要写一行服务端代码。

2016年10月25日，Next.js 1.0.0发布。彼时它还是一个非常轻量的框架，核心就是`getInitialProps`和文件式路由。但这个起点决定了它后来的方向：框架级SSR方案，而非库级工具。

### 1.2.2 Pages Router时代的核心能力与局限

从1.x到12.x，Next.js使用的是Pages Router。核心特性包括：

```
Pages Router 核心能力：
├── 文件式路由（pages/目录映射为路由）
├── SSR（getServerSideProps）
├── SSG（getStaticProps + getStaticPaths）
├── API路由（pages/api/目录）
├── 动态路由（pages/post/[id].js）
├── 布局组件（_app.js + _document.js）
└── 图片优化（next/image）
```

Pages Router很好用，但也有明显的局限性。最大的问题是布局嵌套——`_app.js`是全局唯一的布局入口，想做嵌套布局（比如"全局Header + 板块Sidebar + 页面Content"三层嵌套），需要手动组合组件，框架层面不支持。

另一个问题是数据获取方式的割裂。`getInitialProps`、`getServerSideProps`、`getStaticProps`三种方式分别对应不同的场景，但它们只能在页面级组件使用，不能在子组件中使用。这意味着数据必须从页面顶层逐层传递，组件树的灵活性很差。

还有一个被忽视的问题是缺乏内置的加载状态和错误处理。在Pages Router中，如果`getServerSideProps`执行慢，用户看到的是白屏等待——没有自动的加载动画。如果数据获取失败，也没有内置的错误边界来优雅地展示错误信息。开发者需要自己在组件中实现loading state和error boundary，代码重复度高。

### 1.2.3 App Router革命：React Server Components驱动的大重构

2022年10月，Next.js 13发布了App Router。这不仅仅是路由系统的升级，而是一次基于React Server Components（RSC，React服务端组件）的架构重构。

App Router的核心变化可以用一张图概括：

```
Pages Router                    App Router
┌─────────────────┐            ┌─────────────────────┐
│ pages/          │            │ app/                │
│  ├── index.js   │    ====>   │  ├── page.tsx       │
│  ├── about.js   │            │  ├── about/         │
│  └── post/      │            │  │   └── page.tsx   │
│      └── [id].js│            │  └── layout.tsx     │
│                 │            │     (嵌套布局)        │
│ _app.js (全局)   │            │  + loading.tsx      │
│ _document.js    │            │  + error.tsx        │
└─────────────────┘            │  + not-found.tsx    │
                               └─────────────────────┘
数据获取：                       数据获取：
getServerSideProps              async/await in Server Components
getStaticProps                  (统一方式，按组件粒度)
```

App Router带来的核心改变：

1. 嵌套布局原生支持，每个目录可以有自己的`layout.tsx`
2. 服务端组件默认零客户端JS，减少bundle体积
3. 数据获取不再需要特殊函数，直接`async/await`
4. 内置loading、error、not-found状态处理
5. 流式渲染（Streaming SSR）开箱即用

> 金句：App Router不是Pages Router的升级版，而是基于React服务端组件的一次重新思考——它改变的不是路由，而是组件的运行方式。

### 1.2.4 Next.js 13/14/15关键特性演进时间线

| 版本 | 发布时间 | 关键特性 | 意义 |
|------|----------|----------|------|
| 13.0 | 2022.10 | App Router（beta）、Turbopack（alpha） | 架构重构起点 |
| 13.3 | 2023.04 | File-Based Metadata API | 替代next/head |
| 13.4 | 2023.05 | App Router稳定版 | 生产可用 |
| 14.0 | 2023.10 | Server Actions稳定、Turbopack改进 | 全栈能力补全 |
| 14.1 | 2024.01 | 部分预渲染（PPR）预览 | 渲染模式新突破 |
| 14.2 | 2024.04 | Turbopack开发模式稳定 | 开发体验飞跃 |
| 15.0 | 2024.10 | React 19支持、缓存策略默认变更 | 缓存更直觉 |
| 15.1 | 2024.11 | PPR进一步优化、Turbopack打包稳定 | 生产构建加速 |

重点关注几个里程碑：13.4标志着App Router正式可用于生产环境，14.0的Server Actions让全栈开发更进一步（不需要写API路由就能处理表单提交），15.0改变了默认缓存策略——之前`fetch`默认缓存，现在默认不缓存，这对开发者来说更直觉，但也意味着迁移项目时要注意行为变化。

参考官方文档：[Next.js版本更新日志](https://nextjs.org/blog)

怕浪猫在版本选择上的建议是：新项目直接用最新稳定版（目前是15.x），已有项目不必急于跨大版本升级，先在测试环境中验证兼容性。尤其关注两个破坏性变更节点：13.0引入App Router（架构变化）、15.0改变默认缓存策略（行为变化）。每次大版本升级前，务必阅读官方升级指南。

### 1.2.5 从Pages Router迁移到App Router的官方建议

官方明确表示：Pages Router不会被废弃，它仍然是受支持的功能。但新项目推荐使用App Router。

对于已有项目的迁移，官方建议是渐进式迁移，两种Router可以共存：

```
项目结构（渐进式迁移）：
├── pages/          ← 旧路由，继续工作
│   ├── index.js
│   └── legacy-page.js
├── app/            ← 新路由，逐步迁移
│   ├── page.tsx
│   └── new-page/
│       └── page.tsx
└── next.config.js
```

迁移的优先级建议：新页面直接用App Router开发，旧页面按业务模块逐步迁移。不要一次性重写所有页面——风险太大，收益太小。

迁移过程中最容易踩的坑是数据获取方式的转换。Pages Router的`getServerSideProps`要改成Server Component中的`async/await`，`getStaticPaths`要改成`generateStaticParams`，`getStaticProps`要改成Server Component配合`fetch`的缓存配置。

迁移时还有一个高频踩坑点：客户端组件和服务端组件的边界判断。在Pages Router中，所有组件默认都在客户端运行，使用`window`、`document`等浏览器API不需要特殊处理。但在App Router中，组件默认是服务端组件，不能直接使用浏览器API。需要使用`'use client'`指令声明客户端组件。很多开发者在迁移时遇到的第一个报错就是"ReferenceError: window is not defined"，原因就是在服务端组件中使用了客户端API。

怕浪猫的建议是：迁移前先梳理每个页面的数据获取方式和组件依赖，列一个清单，标注哪些组件需要客户端能力（useState、useEffect、事件监听等），哪些可以保持服务端渲染。有了这个清单，迁移过程会顺畅很多。

## 1.3 Next.js核心优势：SSR/SSG/ISR/CSR渲染能力

### 1.3.1 四大渲染模式一句话定位与核心差异

先把四种渲染模式用一句话说清楚：

- CSR（Client-Side Rendering，客户端渲染）：浏览器下载空HTML，JS执行后渲染页面
- SSR（Server-Side Rendering，服务端渲染）：每次请求时服务器生成完整HTML
- SSG（Static Site Generation，静态站点生成）：构建时生成HTML，CDN直接分发
- ISR（Incremental Static Regeneration，增量静态再生）：构建时生成HTML，后台定期更新

核心差异在于"HTML什么时候生成、谁生成、生成几次"：

```
渲染时机对比：

CSR:   构建时 → 无HTML → 浏览器运行时渲染
SSR:   构建时 → 无HTML → 请求时服务器渲染
SSG:   构建时 → 生成HTML → 请求时直接返回
ISR:   构建时 → 生成HTML → 请求时返回旧HTML → 后台异步更新
```

### 1.3.2 渲染模式选型决策树：什么场景用什么模式

选择渲染模式时，核心考虑两个维度：内容实时性和SEO需求。

```
渲染模式选型决策树：

内容需要实时性吗？
├── 是 → 有SEO需求吗？
│   ├── 是 → SSR（每次请求都生成新HTML）
│   └── 否 → CSR（客户端动态获取）
└── 否 → 内容会变化吗？
    ├── 是 → ISR（定期更新静态页面）
    └── 否 → SSG（永久静态）
```

实际场景对照：

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 企业官网 | SSG | 内容固定，追求最快加载 |
| 新闻资讯 | ISR | 频繁更新，但不需要实时 |
| 电商商品页 | ISR/SSG | 商品信息变化不频繁 |
| 电商购物车 | CSR | 纯交互，无SEO需求 |
| 社交媒体Feed | SSR | 内容实时性强，需要SEO |
| 管理后台 | CSR | 无SEO需求，交互为主 |
| 博客文章 | SSG | 内容固定，追求SEO和速度 |

> 金句：渲染模式不是选择题，而是组合题——同一个项目里，首页用SSG，搜索页用SSR，后台用CSR，这才是Next.js的正确打开方式。

### 1.3.3 渲染性能对比：TTFB与FCP

TTFB（Time To First Byte，首字节到达时间）和FCP（First Contentful Paint，首次内容绘制）是衡量渲染性能的两个核心指标。

```
各模式性能对比：

         TTFB    FCP    首屏完整渲染    SEO
CSR      低      高      高             差
SSR      中      低      低             好
SSG      极低    极低    极低           好
ISR      极低    极低    极低           好

注：低=时间短=好，高=时间长=差
```

SSG和ISR的TTFB极低，因为HTML是提前生成好的，CDN直接返回。SSR的TTFB取决于服务端渲染耗时，如果数据获取慢，TTFB会明显增加。CSR的TTFB低（服务器快速返回空HTML），但FCP高（需要等JS下载执行）。

这里有一个容易被忽略的细节：Core Web Vitals（核心网页指标）中，LCP（Largest Contentful Paint，最大内容绘制）的权重最高。LCP测量的是页面最大内容元素渲染完成的时间。对于SSG/ISR，LCP通常很优秀，因为HTML已经包含完整内容。对于SSR，LCP取决于服务端渲染速度。对于CSR，LCP通常最差，因为最大内容元素需要等JS执行后才能渲染。Google把LCP作为搜索排名因素之一，这也是为什么SEO导向的项目推荐SSG或SSR。

### 1.3.4 混合渲染实战：同一项目多种模式共存

Next.js最强大的能力之一是混合渲染——同一个项目中不同页面可以使用不同的渲染模式。来看一个实际例子：

```typescript
// app/blog/page.tsx — SSG（静态生成）
// 博客列表页，构建时生成
export const dynamic = 'force-static';

export default async function BlogList() {
  const posts = await fetch('https://api.example.com/posts', {
    cache: 'force-cache'
  }).then(r => r.json());
  
  return <PostList posts={posts} />;
}
```

```typescript
// app/dashboard/page.tsx — SSR（服务端渲染）
// 仪表盘，每次请求都渲染最新数据
export const dynamic = 'force-dynamic';

export default async function Dashboard() {
  const stats = await fetch('https://api.example.com/stats', {
    cache: 'no-store'
  }).then(r => r.json());
  
  return <DashboardView data={stats} />;
}
```

```typescript
// app/news/page.tsx — ISR（增量静态再生）
// 新闻页，每60秒更新一次
export const revalidate = 60;

export default async function News() {
  const news = await fetch('https://api.example.com/news').then(r => r.json());
  return <NewsList items={news} />;
}
```

三个页面，三种渲染模式，在同一个项目里和平共处。这就是混合渲染的威力。

### 1.3.5 渲染模式常见误区与踩坑清单

新手 vs 老手的区别，往往就体现在对这些细节的理解上：

**误区一：SSR一定比CSR快。** SSR的首屏渲染确实更快，但TTFB比CSR高。如果服务端数据获取慢，SSR反而会让用户等更久才看到第一个字节。解决方案：对慢数据用流式渲染（Streaming），先返回页面骨架，数据部分延迟填充。

**误区二：ISR的revalidate越小越好。** revalidate设置为1秒不代表页面每秒更新——它意味着第一次请求在1秒后会触发后台更新。如果设得太小，会导致频繁重建，增加服务器负担。一般建议60-3600秒。

**误区三：所有页面都需要SSR。** 很多开发者一上来就全用SSR，实际上大部分页面用SSG就够了。只有内容实时性强的页面才需要SSR。SSG加CDN的性能远超SSR。

**误区四：App Router中fetch默认缓存。** 这在Next.js 15之前是对的，但从15.0开始`fetch`默认不缓存了。如果你从14迁移到15，需要显式配置`cache: 'force-cache'`来保持SSG行为。

## 1.4 Next.js全栈开发能力概述

### 1.4.1 前后端一体化：API路由

Next.js的API路由让你在同一个项目中写后端接口。在App Router中，API路由通过`route.ts`文件实现：

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const users = await db.user.findMany();
  return NextResponse.json({ data: users });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const user = await db.user.create({ data: body });
  return NextResponse.json({ data: user }, { status: 201 });
}
```

同一个文件处理GET和POST请求，路由路径就是文件路径。前端调用时不需要跨域，因为接口和页面在同一个域下。

API路由的运行环境也值得一提。在Next.js中，API路由可以运行在两种Runtime上：Node.js Runtime和Edge Runtime。Node.js Runtime支持完整的Node.js API，可以使用文件系统、数据库驱动等能力。Edge Runtime运行在V8引擎上，不支持完整的Node.js API，但启动速度极快，适合做轻量级的数据处理和请求转发。选择哪种Runtime取决于具体需求——需要数据库操作就用Node.js Runtime，需要全球低延迟就用Edge Runtime。

```typescript
// 指定Runtime
export const runtime = 'edge'; // 或 'nodejs'
```

这个配置让同一个API路由在不同环境下运行，部署时可以根据目标平台灵活选择。

### 1.4.2 数据库直连：Server Components中的直接数据获取

App Router的Server Components可以直接在组件中获取数据库数据，不需要经过API层：

```typescript
// app/products/page.tsx
import { prisma } from '@/lib/db';

export default async function ProductsPage() {
  // 直接在服务端组件中查询数据库
  const products = await prisma.product.findMany({
    include: { category: true },
    orderBy: { createdAt: 'desc' },
  });
  
  return (
    <div>
      {products.map(p => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  );
}
```

这段代码运行在服务端，数据库查询不会暴露到客户端。组件渲染完成后，只把HTML和必要的少量数据发给浏览器。这是App Router最核心的能力之一——前后端边界从API接口下沉到了组件级别。

### 1.4.3 中间件层：请求拦截与权限控制

Next.js的中间件（Middleware）在请求到达页面之前执行，可以用于鉴权、重定向、请求头修改等：

```typescript
// middleware.ts（项目根目录）
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  
  // 未登录用户访问后台，重定向到登录页
  if (request.nextUrl.pathname.startsWith('/admin') && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*'],
};
```

中间件的执行时机在Edge Runtime上，速度极快。它不替代服务端组件中的鉴权逻辑，而是做请求级别的拦截——在渲染之前就决定是否允许访问。

中间件的实际应用场景非常丰富。除了登录鉴权，还可以做A/B测试（根据Cookie分流到不同页面）、地域重定向（根据请求头中的地区信息跳转到对应语言版本）、请求日志（记录所有请求的路径和耗时）、灰度发布（按比例放行新版本路由）。这些需求的共同特点是：需要在页面渲染之前执行，且逻辑与页面内容无关。中间件让这类横切关注点有了统一的处理位置，不用在每个页面中重复实现。

需要注意的限制是：中间件中不能使用Node.js API（比如fs、crypto的部分功能），因为它运行在Edge Runtime上。如果你需要读取文件或执行复杂计算，应该在Server Component或API路由中完成。

### 1.4.4 部署生态：Vercel平台与自托管方案

Next.js的部署方案分为两大类：

**Vercel部署（官方首选）：** Vercel是Next.js的开发公司，提供了零配置的部署体验。push代码到GitHub后自动构建部署，CDN、HTTPS、图片优化、Edge Functions全部开箱即用。对于个人项目和小型团队，这是最省心的方案。

**自托管方案：** 包括Node.js服务器部署（`next start`）、Docker容器化部署、静态导出（`next export`）。企业级项目通常选择自托管，因为数据合规、内网访问等需求不允许使用第三方云平台。

```
部署方案对比：
              Vercel        Node.js自托管    Docker       静态导出
SSR支持         是              是              是          否
ISR支持         是              是              是          否
API路由         是              是              是          否
图片优化        是              需配置          需配置       否
配置成本        零              低              中          低
适用场景        个人/SMB       企业内网        云原生       纯静态站
```

### 1.4.5 Next.js全栈 vs 传统前后端分离架构对比

| 维度 | Next.js全栈 | 传统前后端分离 |
|------|------------|--------------|
| 项目数量 | 1个 | 2个（前端加后端） |
| 部署复杂度 | 低 | 中 |
| API通信 | 同域，无CORS | 跨域，需配置CORS |
| 类型共享 | 直接共享TypeScript类型 | 需要额外方案 |
| 团队协作 | 全栈开发者可独立完成 | 前后端需要密切协作 |
| 微服务扩展 | 较弱 | 较强 |
| 后端能力 | 中等（适合CRUD加轻业务） | 强（适合复杂业务逻辑） |
| 适用场景 | 中小型项目、官网、博客 | 大型项目、复杂业务系统 |

怕浪猫的实战经验是：如果你的项目以内容展示为主，业务逻辑不复杂，Next.js全栈方案能大幅降低开发和维护成本。但如果后端有复杂的业务逻辑、消息队列、定时任务等需求，还是老老实实前后端分离。

## 1.5 开发环境搭建：Node.js、npm、编辑器配置

### 1.5.1 Node.js版本选择与nvm多版本管理

Next.js 15要求Node.js 18.18.0或更高版本。推荐使用LTS（Long Term Support，长期支持）版本，目前是Node.js 22 LTS。

使用nvm（Node Version Manager，Node版本管理器）管理多版本是最佳实践：

```bash
# 安装nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 安装Node.js 22 LTS
nvm install 22
nvm use 22
nvm alias default 22

# 项目级别锁定Node版本
echo "22" > .nvmrc
```

为什么需要版本管理？因为不同项目可能依赖不同的Node版本。你的老项目可能还在用Node 16，新项目需要Node 22。用nvm可以做到`cd`进项目目录自动切换版本，避免版本冲突。

验证nvm安装是否成功：

```bash
nvm --version
# 期望输出：0.40.x

# 查看已安装的所有Node版本
nvm ls

# 使用.nvmrc自动切换版本（进入项目目录后）
nvm use
# 会自动读取当前目录的.nvmrc文件并切换到对应版本
```

除了nvm，还有fnm和volta两个替代方案。fnm用Rust写的，速度比nvm快很多；volta的特点是全局锁定版本，适合团队统一环境。但对于大多数人来说，nvm的社区支持和文档最完善，新手首选nvm。

### 1.5.2 包管理器对比：npm vs yarn vs pnpm选型

三大包管理器的核心区别：

```
npm:    Node.js内置，兼容性最好，速度中等
yarn:   Facebook出品，并行安装，缓存机制好
pnpm:   硬链接加符号链接，磁盘占用最小，安装最快
```

| 特性 | npm | yarn | pnpm |
|------|-----|------|------|
| 安装速度 | 慢 | 快 | 最快 |
| 磁盘占用 | 大 | 中 | 最小 |
| monorepo支持 | workspaces | workspaces | workspace（最优） |
| 严格依赖 | 否 | 否 | 是（防幽灵依赖） |
| 推荐场景 | 简单项目 | 通用 | monorepo/大型项目 |

对于Next.js项目，怕浪猫推荐pnpm。原因很简单：快、省磁盘、严格依赖管理能避免很多"在我电脑上能跑"的问题。

```bash
# 安装pnpm
npm install -g pnpm

# 使用pnpm创建Next.js项目
pnpm create next-app@latest my-app
```

### 1.5.3 VS Code必备插件清单与配置

工欲善其事必先利其器。以下是Next.js开发的VS Code必备插件清单：

| 插件名 | 作用 | 必要性 |
|--------|------|--------|
| ESLint | 代码规范检查 | 必装 |
| Prettier | 代码格式化 | 必装 |
| Tailwind CSS IntelliSense | Tailwind类名提示 | 视情况 |
| TypeScript Next.js snippets | Next.js代码片段 | 推荐 |
| Auto Rename Tag | 标签自动重命名 | 推荐 |
| Path Intellisense | 路径自动补全 | 推荐 |
| Error Lens | 行内显示错误信息 | 推荐 |

关键配置（`.vscode/settings.json`）：

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### 1.5.4 Git安装与SSH密钥配置

Git是版本控制的基础工具，不装Git等于没有后悔药。macOS和Linux通常预装Git，Windows需要从官网下载安装。

SSH（Secure Shell，安全外壳协议）密钥配置用于和GitHub/GitLab通信，避免每次输入密码：

```bash
# 检查是否已有SSH密钥
ls -al ~/.ssh

# 生成SSH密钥（ed25519算法，比RSA更安全更快）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 将公钥添加到SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 查看公钥，复制到GitHub Settings → SSH Keys
cat ~/.ssh/id_ed25519.pub
```

### 1.5.5 开发环境验证清单：3步确认环境就绪

3步搞定开发环境验证：

```bash
# 第1步：验证Node.js版本
node -v
# 期望输出：v22.x.x

# 第2步：验证包管理器
pnpm -v
# 期望输出：9.x.x 或更高

# 第3步：验证Git
git --version
# 期望输出：git version 2.x.x
```

三个命令都正常输出，说明基础环境就绪。接下来就可以创建第一个Next.js项目了。

如果你使用的是Windows系统，还需要额外注意一点：建议使用WSL2（Windows Subsystem for Linux 2）来运行Next.js项目。虽然Next.js在Windows上也能跑，但部分依赖包在Windows上的兼容性不如Linux，且部署环境通常是Linux。使用WSL2可以保证开发环境和生产环境的一致性，避免"在我电脑上能跑"的经典场景。

## 1.6 第一个Next.js项目：初始化、运行、目录初识

### 1.6.1 create-next-app脚手架全参数解析

`create-next-app`是Next.js官方脚手架工具，一条命令完成项目创建。先看完整参数：

```bash
npx create-next-app@latest my-app \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-pnpm
```

参数含义对照：

| 参数 | 作用 | 默认值 |
|------|------|--------|
| --typescript 使用TypeScript | Yes |
| --tailwind | 集成Tailwind CSS | Yes |
| --eslint | 集成ESLint | Yes |
| --app | 使用App Router | Yes |
| --src-dir | 使用src/目录 | No |
| --import-alias | 路径别名 | @/* |
| --use-pnpm | 使用pnpm | npm |

实际操作时，交互式命令会更友好：

```bash
pnpm create next-app@latest
```

然后按提示选择即可。怕浪猫建议初学者先用交互式命令，熟悉后再用命令行参数一键创建。

参考官方文档：[create-next-app文档](https://nextjs.org/docs/app/api-reference/cli/create-next-app)

### 1.6.2 项目启动：npm run dev背后的执行流程

项目创建完成后，进入项目目录，运行开发服务器：

```bash
cd my-app
pnpm dev
```

看到的输出大致如下：

```
   ▲ Next.js 15.x.x
   - Local:   http://localhost:3000
   - Network: http://192.168.1.100:3000

 ✓ Starting...
 ✓ Ready in 1.2s
```

`pnpm dev`实际上执行的是`next dev`命令。这个命令做了几件事：

```
next dev 执行流程：
1. 读取next.config.js配置
2. 启动Turbopack/Webpack开发服务器
3. 注册文件系统监听器（文件修改时热更新）
4. 初始化路由系统（扫描app/目录）
5. 监听3000端口，等待请求
```

开发模式下，Next.js不会预编译所有页面，而是采用按需编译——只有当某个页面被访问时才编译。这就是为什么第一次访问某个页面会稍慢，后续访问就很快（编译结果被缓存了）。

### 1.6.3 核心目录速览：app/、public/、next.config.js

项目创建后的目录结构如下：

```
my-app/
├── src/
│   └── app/
│       ├── layout.tsx      ← 根布局
│       ├── page.tsx        ← 首页
│       ├── globals.css     ← 全局样式
│       └── favicon.ico     ← 网站图标
├── public/                 ← 静态资源目录
│   ├── next.svg
│   └── vercel.svg
├── next.config.ts          ← Next.js配置文件
├── tsconfig.json           ← TypeScript配置
├── package.json            ← 项目依赖
├── pnpm-lock.yaml          ← 锁文件
├── postcss.config.mjs      ← PostCSS配置
└── tailwind.config.ts      ← Tailwind配置
```

几个核心目录的作用：

| 目录/文件 | 作用 | 说明 |
|-----------|------|------|
| src/app/ | 路由和页面 | App Router核心目录 |
| public/ | 静态资源 | 图片、字体等直接访问的文件 |
| next.config.ts | 框架配置 | 构建配置、环境变量、重定向等 |
| tsconfig.json | TS配置 | 路径别名、类型检查规则 |
| package.json | 依赖管理 | 脚本命令和依赖声明 |

### 1.6.4 修改首页内容：从Hello World到自定义页面

打开`src/app/page.tsx`，把默认内容改成自定义内容：

```typescript
// src/app/page.tsx
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">
        Hello Next.js
      </h1>
      <p className="text-gray-600">
        我是怕浪猫，这是我的第一个Next.js项目
      </p>
    </main>
  );
}
```

保存后，浏览器会自动热更新。不需要手动刷新——这就是HMR（Hot Module Replacement，热模块替换）的魔力。

再看`layout.tsx`，它是根布局，所有页面都会被包裹在其中：

```typescript
// src/app/layout.tsx
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '我的Next.js应用',
  description: '由怕浪猫创建的Next.js项目',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

`metadata`对象会自动生成HTML的`<title>`和`<meta>`标签。这是App Router内置的Metadata API，比Pages Router的`next/head`更优雅。

### 1.6.5 构建生产版本：npm run build产物分析

开发完成后，需要构建生产版本：

```bash
pnpm build
```

构建输出会展示每个路由的渲染模式、大小等信息：

```
Route (app)                              Size     First Load JS
┌ ○ /                                    2.5 kB         89.4 kB
├ ○ /_not-found                          871 B          88.2 kB
└ ○ /about                               1.2 kB         89.1 kB
○  (Static)   - 预渲染为静态内容
●  (Dynamic)  - 服务端按需渲染
ƒ  (Dynamic)  - 动态API路由

First Load JS shared by all: 87.1 kB
```

理解这些标记的含义：

| 标记 | 含义 | 说明 |
|------|------|------|
| ○ (Static) | 静态预渲染 | 构建时生成HTML，SSG |
| ● (Dynamic) | 动态渲染 | 请求时渲染，SSR |
| ƒ (Dynamic) | 动态API | API路由，运行时处理 |
| λ | 使用ISR | 增量静态再生 |

构建完成后，用`pnpm start`启动生产服务器，模拟线上环境验证。如果一切正常，就可以部署了。

## 1.7 本章小结与课后练习

### 本章核心要点回顾

这一章我们从现代前端的痛点出发，理解了Next.js为什么存在、它解决了什么问题。核心知识点：

1. SPA的SEO和白屏问题是Next.js诞生的驱动力之一
2. App Router基于React Server Components，是当前推荐的路由方案
3. 四大渲染模式（CSR/SSR/SSG/ISR）各有适用场景，Next.js支持混合渲染
4. Next.js具备全栈开发能力：API路由、数据库直连、中间件、Server Actions
5. 开发环境搭建只需要Node.js、包管理器、编辑器三件套
6. create-next-app脚手架一键创建项目，开箱即用

### 课后练习

1. 思考题：你目前的项目中，哪些页面适合SSG，哪些适合SSR，哪些适合CSR？列出你的分析依据。

2. 动手题：用create-next-app创建一个新项目，修改首页内容为自己的介绍，分别添加两个页面：一个使用SSG（显示固定内容），一个使用SSR（显示当前时间）。

3. 探索题：阅读[Next.js官方文档](https://nextjs.org/docs)，找到`next.config.ts`可以配置哪些选项，尝试修改其中两项并观察效果。

4. 对比题：对比你之前使用的React项目搭建方式（CRA或Vite），列出与Next.js在目录结构、构建方式、开发体验上的三个主要差异。

觉得有用？收藏起来，下次直接照抄。

你遇到过前端框架选型的纠结吗？评论区说说你的选择和踩过的坑。

关注怕浪猫，下期我们讲"Next.js项目架构与基础目录详解"——从文件结构到配置文件，帮你建立规范的项目开发思维。16章连载，这是第一步，别掉队。

系列进度 1/16

**下章预告：** 第2章将带你深入Next.js的目录结构，详解App Router的核心目录约定、配置文件的作用、路径别名优化、项目分层架构设计。搞懂目录结构，是写出可维护代码的第一步。怕浪猫会带你从"能跑就行"进化到"规范工程"。

怕浪猫说：框架不是银弹，但选对框架能少走一半弯路。Next.js不是终点，而是你全栈能力的起点——别只学语法，要理解它为什么这样设计。下一章见。
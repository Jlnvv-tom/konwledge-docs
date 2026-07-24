# 第2章 Next.js 项目架构与基础目录详解

90%的Next.js开发者都踩过这个坑：项目跑起来了，但目录结构乱成一锅粥，配置文件改了半天发现根本没生效，环境变量在本地好好的上了生产却变成了undefined。更扎心的是，接手别人项目的时候，光搞清楚哪个文件负责什么就花了三天。还有团队里新来的同事，面对一堆没有注释的配置文件，只能靠猜来理解项目结构，这种技术债越积越多，最终导致整个项目难以维护。

我是怕浪猫，一个在生产环境中摸爬滚打过无数个Next.js项目的全栈开发者。今天这一章，我把Next.js项目架构里的每一个目录、每一个配置文件、每一个约定规则全部掰开揉碎讲给你听。看完这篇，你的项目结构将从"能跑就行"升级到"企业级规范"。这一章的内容比较硬核，但它是后续所有章节的基础，搞懂了架构和目录，后面写代码才能事半功倍。

## 2.1 Page Router与App Router双模式对比

Next.js从13版本开始引入了全新的App Router（Application Router，应用路由器），用它来替代老的Pages Router（页面路由器）。但Next.js团队并没有直接废弃Pages Router，而是选择了长期共存的策略。这就导致很多开发者一上来就懵了：到底该用哪个？两个能不能共存？老项目要不要迁移？新项目选哪个更稳妥？

先把结论放这里：新项目毫不犹豫直接上App Router，老项目按需逐步迁移，两种模式在同一个项目中可以共存但绝对不要在同一个路由段内混用。Next.js官方在文档中明确表示，App Router是未来的主要发展方向，Pages Router仍然会持续维护但不会再获得新功能。

### 2.1.1 Pages Router目录约定：pages/目录的路由映射规则

Pages Router是Next.js最经典的路由方案，从第一个版本就存在。它的核心规则就一句话：pages/目录下的文件结构就是路由结构，文件名直接映射为URL路径。

来看一个典型的Pages Router目录结构：

```
pages/
  index.tsx          → 映射为 /
  about.tsx          → 映射为 /about
  blog/
    index.tsx        → 映射为 /blog
    [id].tsx         → 映射为 /blog/:id
    [...slug].tsx    → 映射为 /blog/*（捕获所有路由）
  api/
    hello.ts         → 映射为 /api/hello
  _app.tsx           → 特殊文件，不参与路由
  _document.tsx      → 特殊文件，不参与路由
```

文件名即路由路径，方括号`[]`表示动态路由参数，三个点`...`表示捕获所有后续路径段。这个设计简单直接，学习成本极低，新手几乎不需要阅读文档就能上手。`_app.tsx`和`_document.tsx`是两个特殊文件，以下划线开头表示不参与路由映射，分别负责应用入口包装和HTML文档结构定义。

核心路由映射代码逻辑如下：

```tsx
// pages/index.tsx — 自动映射为首页路由 /
export default function Home() {
  return <h1>Home Page</h1>
}

// pages/blog/[id].tsx — 动态路由 /blog/123
import { useRouter } from 'next/router'

export default function BlogPost() {
  const router = useRouter()
  const { id } = router.query
  return <h1>Post: {id}</h1>
}
```

这种文件即路由的设计，让新手几乎不需要学习路由配置就能上手。但它的局限也很明显：布局系统非常弱，想给某个路由段加独立布局只能在每个页面里手动引入；数据获取方式分散在getServerSideProps、getStaticProps、getInitialProps几个函数里，逻辑不内聚；嵌套路由不够灵活，无法实现真正的布局嵌套。

> Pages Router就像是一把瑞士军刀，什么都能干，但每一项都不够专精。App Router则是整套专业工具箱，学习曲线陡了点，但用对了效率翻倍。

### 2.1.2 App Router目录约定：app/目录的文件式路由

App Router用app/目录替代pages/目录，路由规则从"文件即路由"变成了"文件夹即路由段，文件即路由内容"。这个变化看似不大，但实际上是整个路由系统的重新设计。

```
app/
  page.tsx           → /
  about/
    page.tsx         → /about
  blog/
    page.tsx         → /blog
    [id]/
      page.tsx       → /blog/:id
  layout.tsx         → 根布局（所有路由共享）
```

关键区别在于：在App Router中，文件夹定义路由段，page.tsx定义路由内容。一个文件夹里没有page.tsx就不会成为可访问的路由，它只是一个路由中间节点。这个设计让布局、加载状态、错误处理等逻辑可以按路由段组织，而不是全部塞在一个页面文件里。

```tsx
// app/blog/[id]/page.tsx
export default function BlogPost({
  params,
}: {
  params: { id: string }
}) {
  return <h1>Post: {params.id}</h1>
}
```

注意到了吗？App Router中动态路由参数通过`params` prop直接传入组件，不再需要使用`useRouter`来获取。更重要的是，这个组件默认是Server Component（服务端组件），可以直接使用`async/await`获取数据，这在Pages Router里是做不到的——Pages Router中的页面组件是同步的，数据获取必须通过特殊函数在外部完成再传入。

还有一个容易被忽略的区别：App Router中`params`是普通对象，在服务端渲染时就已经包含完整的路由参数值。而Pages Router中`router.query`在客户端首次导航时存在水合（Hydration）过程——初次渲染时query可能为空对象，需要等客户端水合完成后才能拿到参数值。这会导致页面在首次渲染时可能出现短暂的内容闪烁，比如组件先渲染出"Post: "然后突然变成"Post: 123"。App Router从设计上消除了这个问题，服务端渲染时参数就已就绪，用户体验更丝滑。

### 2.1.3 两种Router的布局系统差异：_app/_document vs layout/template

布局系统是两种Router最大的差异之一，直接决定了项目的可维护性和开发体验。

Pages Router的布局方案非常有限：

```
pages/
  _app.tsx        → 全局布局，所有页面共享，只能有一个
  _document.tsx   → HTML文档结构，只在服务端渲染
  index.tsx
  about.tsx
  blog/
    index.tsx
    [id].tsx
```

`_app.tsx`是所有页面的入口，你可以在这里包裹全局Context Provider、导航栏、页脚等。但问题在于：如果你想给`/dashboard`下的所有页面加一个侧边栏布局，就得在每个dashboard页面里手动引入布局组件，或者在`_app.tsx`里通过`router.pathname`判断当前路由来决定是否显示侧边栏。两种方式都很丑陋，而且难以维护。

App Router的布局方案则灵活得多：

```tsx
// app/layout.tsx — 根布局，所有路由共享
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>
        <nav>全局导航</nav>
        {children}
      </body>
    </html>
  )
}

// app/dashboard/layout.tsx — dashboard专属布局
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex">
      <aside>侧边栏</aside>
      <main>{children}</main>
    </div>
  )
}
```

App Router通过嵌套`layout.tsx`实现布局层级化，每个路由段都可以有自己的布局。访问`/dashboard/settings`时，渲染层级是：RootLayout包裹DashboardLayout包裹SettingsPage，形成洋葱式的嵌套结构。而且布局在路由切换时不会重新渲染和挂载，这意味着你的侧边栏、导航栏不会因为页面切换而闪烁重载。

`template.tsx`和`layout.tsx`功能类似，区别在于`template`在每次路由切换时都会重新挂载组件。当你需要每次访问页面都重新执行某些副作用（比如页面浏览统计）时，用`template`而不是`layout`。

这里有一个重要的性能特性需要理解：layout组件在子路由导航时保持不重新挂载，只有page.tsx的内容会更新。这意味着在layout中的useState状态会在子路由切换时保持。而template则相反，每次导航都会卸载旧的、挂载新的，状态不会保留。

### 2.1.4 数据获取方式对比：getServerSideProps/getStaticProps vs async组件

数据获取方式的演进是App Router最核心的改进，也是迁移过程中改动量最大的部分。

Pages Router时代，数据获取依赖几个特殊函数，每个函数对应不同的渲染策略：

```tsx
// Pages Router: SSR（Server-Side Rendering，服务端渲染）
// 每次请求都执行，适合动态内容
export async function getServerSideProps() {
  const res = await fetch('https://api.example.com/users')
  const users = await res.json()
  return { props: { users } }
}

// Pages Router: SSG（Static Site Generation，静态站点生成）
// 构建时执行，适合静态内容
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/articles')
  const articles = await res.json()
  return { props: { articles } }
}

export default function Users({ users }: { users: User[] }) {
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>
}
```

这套方案能用，但问题不少。第一，这些特殊函数只能在页面级组件使用，子组件无法独立获取数据，必须通过props层层传递。如果你的页面组件树有三四层深，数据要从顶层页面一路传递到叶子组件，中间每一层都要在props里声明这个数据类型，非常繁琐。第二，数据获取和组件渲染是分离的，逻辑不内聚，阅读代码时需要来回跳转——getServerSideProps在文件最底部，使用数据的组件在中间，修改一个数据字段要跳好几个地方。第三，TypeScript类型推导链路长，需要手动维护props的类型定义，很容易出现getServerSideProps返回的类型和页面组件props类型不一致的问题。第四，这些特殊函数的执行时机和运行环境对新手来说不透明，容易写出在服务端崩掉的代码——比如在这些函数里使用了window对象或客户端-only的库。

App Router直接把数据获取变成了组件的一部分：

```tsx
// App Router: Server Component直接async获取数据
export default async function UsersPage() {
  const res = await fetch('https://api.example.com/users')
  const users = await res.json()
  return (
    <ul>
      {users.map((u: User) => (
        <li key={u.id}>{u.name}</li>
      ))}
    </ul>
  )
}
```

没有了getServerSideProps，组件本身就是async函数，直接await获取数据。类型推导一气呵成，数据获取和渲染逻辑内聚在同一个函数里。更重要的是，这个fetch是Next.js扩展过的，自带缓存和重新验证（Revalidation）能力——通过`fetch(url, { next: { revalidate: 60 } })`就能实现ISR（Incremental Static Regeneration，增量静态再生）。

而且Server Component可以嵌套使用，每个子组件都独立获取自己的数据，这些请求会并行执行。在Pages Router中，所有数据必须在页面级的getServerSideProps里一次性获取，然后层层传递，性能和可维护性都差很多。

另外值得一提的是，App Router中的fetch函数是Next.js扩展过的版本，默认带有缓存能力。你可以通过不同的配置实现不同的缓存策略：`fetch(url)`默认缓存（等同于getStaticProps），`fetch(url, { cache: 'no-store' })`不缓存（等同于getServerSideProps），`fetch(url, { next: { revalidate: 60 } })`每60秒重新验证（等同于getStaticProps加上revalidate参数）。这种统一的数据获取接口让心智负担大大降低，不需要再记忆三套不同的函数签名。

> App Router最大的贡献不是新增了什么API，而是消灭了getServerSideProps这一堆魔法函数。数据获取回归了React最本质的写法——async组件加await，简单、直观、可组合。

### 2.1.5 官方迁移指南：从Pages Router平滑切换到App Router

官方支持两种Router共存，迁移可以渐进进行，不需要一次性全部改完。核心步骤如下。

第一步：确保Next.js版本大于等于13，在next.config.js中无需额外配置，app/目录存在即自动启用App Router。两个目录可以并存，pages/下的路由和app/下的路由互不干扰。

第二步：在项目根目录创建app/目录，添加app/layout.tsx（根布局必须存在）和app/page.tsx。注意App Router的根layout必须包含html和body标签，因为这里替代了_document.tsx的职责。

第三步：逐步将pages/下的页面迁移到app/下，注意数据获取方式的改写。

迁移过程中最容易踩的坑就是Server Component和Client Component的混淆：

```tsx
// 错误：在Server Component中使用了客户端API
export default async function BadPage() {
  const router = useRouter() // 报错！
  const data = await getData()
  return <div>{data}</div>
}

// 正确：拆分为Server + Client组件
// app/page.tsx (Server Component)
import ClientView from './ClientView'
export default async function Page() {
  const data = await getData()
  return <ClientView data={data} />
}

// app/ClientView.tsx
'use client'
import { useRouter } from 'next/navigation'
export default function ClientView({ data }) {
  const router = useRouter()
  return <button onClick={() => router.back()}>{data}</button>
}
```

迁移的核心原则：Server Component做数据获取和静态渲染，Client Component做交互和状态管理。把需要客户端能力的部分拆分成独立的Client Component，通过props传递数据。这个概念在后续章节会深入讲解。

迁移参考官方文档：https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration

> 迁移不是一锤子买卖，而是一个页面一个页面的外科手术。每次迁移一个路由，确保测试通过再动下一个。急躁是迁移翻车的第一大原因。
END OFPART1
echo "Part 1 done: $(wc -c < /tmp/chapter2_part1.md) bytes"
## 2.2 App Router核心目录结构解析

App Router的设计哲学是"约定优于配置"（Convention over Configuration），每个特殊文件都有明确的职责和命名规则。理解这些约定，是掌握Next.js项目结构的基础。

### 2.2.1 app/目录全景图：page、layout、template、loading、error

一张表看清楚app/目录下所有特殊文件的职责：

| 文件名 | 职责 | 是否必须 | 路由切换时行为 |
|--------|------|----------|----------------|
| page.tsx | 路由页面内容 | 是（路由必须） | 重新渲染 |
| layout.tsx | 布局组件 | 否（根layout必须） | 保持不重新挂载 |
| template.tsx | 模板组件 | 否 | 每次导航重新挂载 |
| loading.tsx | 加载中状态UI | 否 | Suspense期间显示 |
| error.tsx | 错误边界UI | 否 | 捕获子组件错误 |
| not-found.tsx | 404状态UI | 否 | 路由未匹配时显示 |
| global-error.tsx | 全局错误UI | 否 | 捕获根layout错误 |
| default.tsx | 并行路由默认 | 否 | Parallel Route填充 |

这套设计的精妙之处在于：每个关注点（加载状态、错误处理、布局、页面内容）都有独立的文件，互不干扰。你不需要在一个文件里写一堆条件判断来处理不同状态。在没有loading.tsx的时候，如果页面组件是async的，Next.js会在数据获取期间显示空白页面；有了loading.tsx，它会自动被Suspense包裹，显示你定义的加载UI。

```tsx
// app/dashboard/loading.tsx — 自动作为Suspense fallback
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
      <div className="h-4 bg-gray-200 rounded mt-4"></div>
    </div>
  )
}

// app/dashboard/error.tsx — 自动作为Error Boundary
'use client'
export default function Error({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  return (
    <div>
      <h2>出错了: {error.message}</h2>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

loading.tsx会自动包裹在Suspense边界中，当子组件处于pending状态时显示。error.tsx自动作为Error Boundary，捕获子树中的运行时错误，并提供reset函数让用户触发重试。注意error.tsx必须标记为use client，因为Error Boundary是React客户端的概念。

### 2.2.2 路由层级与文件约定：文件夹即路由段

App Router的路由层级完全由文件夹结构决定，这是一个递归的规则。

```
app/
  layout.tsx          → 根布局，作用于所有路由
  page.tsx            → 首页 /
  blog/
    layout.tsx        → /blog 布局
    page.tsx          → /blog
    [id]/
      page.tsx        → /blog/:id
  dashboard/
    layout.tsx        → /dashboard 布局
    page.tsx          → /dashboard
    settings/
      page.tsx        → /dashboard/settings
```

路由的渲染层级是嵌套的。访问/dashboard/settings时，渲染顺序为：RootLayout包裹DashboardLayout包裹SettingsPage。每一层的layout都会包裹内层内容，形成洋葱式结构。

```
访问 /dashboard/settings 的渲染树:

RootLayout (app/layout.tsx)
  └── DashboardLayout (app/dashboard/layout.tsx)
        └── SettingsPage (app/dashboard/settings/page.tsx)
```

这种嵌套布局是App Router的核心优势。在Pages Router中要实现同样的效果需要在每个页面文件里手动引入布局组件，维护成本高且容易遗漏。而且layout在路由切换时保持挂载不重新渲染，只有page.tsx的内容会更新，这意味着layout中的useState状态会在子路由切换时保持。举个例子，如果dashboard的layout中有一个折叠/展开侧边栏的状态，用户在/dashboard/settings折叠了侧边栏，导航到/dashboard/users时侧边栏仍然是折叠状态——因为layout没有重新挂载。这在Pages Router中是做不到的，每次页面切换都会重新挂载整个组件树。

layout是可选的（除了根layout必须存在），不是每个路由段都需要layout。如果某个路由段没有layout.tsx，它的内容会直接传递给上层的layout。这意味着你可以只在需要布局的路由段添加layout，其他路由段保持简洁。这种按需添加的设计让简单页面保持简单，不会因为框架的默认约定而产生不必要的样板代码。

### 2.2.3 特殊文件清单：not-found、global-error、default

not-found.tsx用于处理404场景，可以在不同路由层级放置：

```tsx
// app/not-found.tsx — 全局404
export default function NotFound() {
  return <h1>页面不存在</h1>
}

// app/blog/[id]/not-found.tsx — 局部404
export default function BlogNotFound() {
  return <h1>文章不存在</h1>
}
```

在Server Component中可以通过调用notFound()函数主动触发404：

```tsx
import { notFound } from 'next/navigation'

export default async function BlogPost({ params }) {
  const post = await getPost(params.id)
  if (!post) {
    notFound() // 触发同级的not-found.tsx
  }
  return <article>{post.content}</article>
}
```

global-error.tsx是最后的安全网，它捕获根layout.tsx中的错误。普通的error.tsx无法捕获同级layout的错误，因为error本身就在layout内部渲染。global-error.tsx替代根layout来渲染错误状态，必须包含html和body标签：

```tsx
// app/global-error.tsx
'use client'
export default function GlobalError({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h1>系统错误: {error.message}</h1>
        <button onClick={reset}>重试</button>
      </body>
    </html>
  )
}
```

default.tsx用于Parallel Routes（并行路由），当并行路由没有匹配到内容时作为默认填充。这个概念在后续路由系统章节会详细讲解。

### 2.2.4 私有文件夹与colocation（共置）机制

实际开发中，我们经常需要在路由目录下放一些非路由文件。App Router提供了两种机制来处理这个需求。

私有文件夹：以下划线开头的文件夹会被排除出路由系统。

```
app/
  blog/
    _components/      → 私有文件夹，不参与路由
      BlogCard.tsx
    _utils/           → 私有文件夹，不参与路由
      format.ts
    page.tsx          → /blog
```

Colocation（共置）：从Next.js 14开始，只要文件夹里没有page.tsx，就不是路由段，可以放任意文件。

```
app/
  blog/
    components/       → 无page.tsx，不是路由
      BlogList.tsx
    utils.ts          → 直接放在路由目录下
    page.tsx          → /blog
```

两种方式的选择标准：如果目录下文件较多且明确是内部使用的，用私有文件夹显式声明；如果只是放少量和页面紧密相关的文件，直接用colocation更简洁。

```tsx
// app/blog/page.tsx — colocation让导入路径极短
import { BlogList } from './components/BlogList'
import { formatDate } from './utils'

export default function BlogPage() {
  return <BlogList />
}
```

> 好的项目结构不是把文件分到无数个子目录，而是让相关的代码物理上靠近。colocation机制就是为这个理念服务的。

### 2.2.5 route handler与page共存的规则

Route Handler（路由处理器）是App Router中替代Pages Router API路由的方案。通过route.ts文件定义。

```tsx
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const users = await db.user.findMany()
  return NextResponse.json(users)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const user = await db.user.create({ data: body })
  return NextResponse.json(user, { status: 201 })
}
```

一个关键规则：同一目录下route.ts和page.tsx不能共存。它们都代表同一个路由段的内容，框架无法决定该返回页面还是API响应。如果需要既返回页面又提供API，分开放置即可：

```
app/
  users/
    page.tsx          → /users 页面
  api/
    users/
      route.ts        → /api/users 接口
```

Route Handler支持GET、POST、PUT、DELETE、PATCH等HTTP方法，还支持Web Streaming（流式响应）和Edge Runtime（边缘运行时），功能比Pages Router的API路由强大得多。在Pages Router中，API路由只是一个简单的函数导出，没有类型安全的请求处理，也没有内置的流式响应支持。Route Handler则基于标准的Web API（Request/Response），与浏览器原生API保持一致，学习成本低且可移植性好。官方文档参考：https://nextjs.org/docs/app/building-your-application/routing/route-handlers

## 2.3 核心配置文件：next.config.js、tsconfig.json

Next.js的配置体系设计得比较克制——大部分东西开箱即用，但当你需要自定义时，配置文件就是你的控制面板。理解这些配置文件的作用和加载机制，是项目架构设计的基本功。

### 2.3.1 next.config.js完整配置项速查表

next.config.js是Next.js项目的总配置入口，支持.js、.mjs、.ts三种格式。Next.js 15推荐使用.mjs或.ts格式。以下是常用配置项分类速查表：

| 配置分类 | 配置项 | 说明 |
|----------|--------|------|
| 基础配置 | reactStrictMode | React严格模式 |
| | swcMinify | SWC压缩（默认开启） |
| | poweredByHeader | X-Powered-By头 |
| 图片优化 | images.domains | 远程图片域名 |
| | images.formats | 支持的图片格式 |
| | images.unoptimized | 关闭图片优化 |
| 重定向 | redirects() | URL重定向 |
| 重写 | rewrites() | URL重写（代理） |
| Headers | headers() | 自定义响应头 |
| Webpack | webpack() | 自定义webpack配置 |
| 实验性 | experimental | 实验性功能 |
| 环境变量 | env | 注入环境变量 |

### 2.3.2 常用配置：reactStrictMode、images、experimental

实际项目中，以下几个配置最常用，也是最容易踩坑的地方：

```js
// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  // React严格模式，开发环境额外检查
  reactStrictMode: true,

  // 图片优化配置
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      { protocol: 'https', hostname: 'cdn.example.com' },
      { protocol: 'https', hostname: 'img.example.com' },
    ],
  },

  // 实验性功能
  experimental: {
    typedRoutes: true, // 类型安全路由
  },

  // 自定义headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
        ],
      },
    ]
  },
}

export default nextConfig
```

这里有几个踩坑点需要特别注意。

reactStrictMode在开发模式下会导致组件挂载两次（mount然后unmount然后再次mount），这是用来帮你发现副作用问题的。如果你的useEffect里写了不合理的逻辑，严格模式下会暴露问题。不要为了"修复"双挂载而关闭它，正确的做法是修复你的副作用代码。

images.remotePatterns替代了老的images.domains配置，支持更细粒度的控制。配置远程图片域名时，一定要在next.config.js中声明，否则next/image组件会报错。这是新手最常见的报错之一：用了next/image但不配域名。

experimental.typedRoutes开启后，Link组件的href属性会有类型检查，路由写错编译期就能发现。比如`<Link href="/blg">`会被标红提示，因为正确路径是`/blog`。这个功能虽然还在experimental阶段，但已经足够稳定，强烈推荐开启。

### 2.3.3 tsconfig.json路径别名与编译选项

Next.js自动生成的tsconfig.json已经包含了合理的默认配置，但理解每个选项的含义仍然重要。

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

几个关键选项说明。moduleResolution设为bundler是Next.js 15的默认值，比node模式更适合现代打包工具，能正确处理package.json中的exports字段。jsx设为preserve表示不由tsc编译JSX，而是交给Next.js的SWC（Speedy Web Compiler）编译器处理，SWC比Babel快一个数量级。plugins中的next项启用Next.js的TypeScript插件，提供类型检查增强和路由类型推导。paths中的`@/*`映射到`./*`是路径别名的基础配置，后续会详细讲解。

### 2.3.4 环境变量文件：.env、.env.local、.env.production

Next.js原生支持dotenv，环境变量按文件名区分环境和优先级。这套机制看似简单，但加载优先级和覆盖规则是很多开发者搞不清楚的。

| 文件 | 环境 | 说明 |
|------|------|------|
| .env | 所有环境 | 默认值，提交到git |
| .env.local | 本地开发 | 覆盖.env，不提交git |
| .env.development | 开发环境 | next dev时加载 |
| .env.production | 生产环境 | next build和next start时加载 |
| .env.test | 测试环境 | jest等测试工具运行时加载 |

加载优先级从高到低：.env.local大于.env.[environment]大于.env。这意味着.env.local中的同名变量会覆盖其他所有环境的变量，这就是为什么.env.local不应该提交到git——每个人可能有不同的本地配置。

```bash
# .env — 所有环境共享的默认值
APP_NAME=MyApp

# .env.development — 开发环境专用
NEXT_PUBLIC_API_URL=http://localhost:3000/api
LOG_LEVEL=debug

# .env.production — 生产环境专用
NEXT_PUBLIC_API_URL=https://api.example.com
LOG_LEVEL=error

# .env.local — 本地覆盖（gitignore，不提交）
DATABASE_URL=postgresql://localhost/myapp_dev
```

一个常见的坑：修改.env文件后需要重启开发服务器，热更新不会重新加载环境变量。很多人改了.env文件后疑惑"为什么环境变量没变"，原因就是没有重启next dev进程。

### 2.3.5 配置文件加载优先级与覆盖规则

Next.js配置加载遵循清晰的优先级链：

```
命令行参数 > next.config.js > .env.local > .env.[environment] > .env > 默认值
```

命令行参数优先级最高。例如next build --no-lint会覆盖next.config.js中的eslint配置。这在CI/CD流水线中很有用，可以通过命令行参数临时调整构建行为而不修改配置文件。

环境变量的覆盖规则有一个重要例外：已经存在于process.env中的变量不会被.env文件覆盖。这意味着在CI/CD平台（如GitHub Actions、GitLab CI）中通过平台设置的环境变量优先级最高，.env文件中的同名变量不会生效。这个特性在多环境部署中非常重要——你可以用一个Docker镜像配合不同的环境变量部署到不同环境。

> 配置文件的优先级就像CSS的层叠规则——越具体的越优先。如果你发现配置"不生效"，第一件事就是检查是否被更高优先级的配置覆盖了。

## 2.4 静态资源、环境变量配置与使用

### 2.4.1 public/目录：静态文件的直接访问

public/目录是Next.js存放静态资源的专用目录，放在这里的文件可以通过根路径直接访问，不需要任何配置。这个目录的设计理念是"零配置静态资源服务"——放进去就能访问，简单粗暴。

```
public/
  favicon.ico      → /favicon.ico
  images/
    logo.png       → /images/logo.png
  robots.txt       → /robots.txt
  manifest.json    → /manifest.json
```

在代码中引用public/下的资源，直接使用根路径即可：

```tsx
// 正确：直接使用根路径引用
export function Logo() {
  return <img src="/images/logo.png" alt="Logo" />
}

// 更好的方式：使用next/image组件获得图片优化
import Image from 'next/image'
export function Logo() {
  return (
    <Image
      src="/images/logo.png"
      alt="Logo"
      width={120}
      height={40}
      priority
    />
  )
}
```

注意public/目录下的文件不会被Next.js编译或处理，原样输出到构建产物中。因此不要在这里放需要编译的CSS或JavaScript文件，那些应该放在src目录下通过import引入。public/适合放favicon、robots.txt、manifest.json、开源协议文件等静态资源。

### 2.4.2 环境变量在服务端与客户端的区分：NEXT_PUBLIC_前缀

这是Next.js环境变量最核心的规则，也是安全体系的基石：不带NEXT_PUBLIC_前缀的环境变量只在服务端可用，带NEXT_PUBLIC_前缀的才能在客户端访问。

```bash
# .env
# 服务端专用 — 客户端永远拿不到这些值
DATABASE_URL=postgresql://user:pass@host:5432/db
API_SECRET_KEY=sk-1234567890
JWT_SECRET=my-jwt-secret

# 客户端可用 — 会被构建时内联到客户端JS中
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_APP_NAME=MyApp
```

```tsx
// Server Component — 可以访问所有环境变量
export default async function ServerPage() {
  const dbUrl = process.env.DATABASE_URL      // 有效
  const secret = process.env.API_SECRET_KEY    // 有效
  const apiUrl = process.env.NEXT_PUBLIC_API_URL // 有效
  // ...
}

// Client Component — 只能访问NEXT_PUBLIC_前缀的
'use client'
export function ClientComponent() {
  // const secret = process.env.DATABASE_URL  // undefined！
  const apiUrl = process.env.NEXT_PUBLIC_API_URL // 有效
  // ...
}
```

这个设计的本质是安全考虑。服务端密钥（数据库密码、API Secret、JWT密钥等）绝不能暴露到客户端。NEXT_PUBLIC_前缀的变量在构建时会被替换为实际值，内联到客户端JS bundle中。这意味着任何人都能在浏览器开发者工具的Sources面板中看到这些值。

踩坑警告：绝对不要在NEXT_PUBLIC_变量中放任何敏感信息。如果你发现自己在写`NEXT_PUBLIC_SECRET_KEY`，停下来重新思考你的架构——这个变量不应该出现在客户端。

### 2.4.3 运行时配置 vs 构建时配置

Next.js的环境变量有一个重要特性需要理解：大部分环境变量在构建时就被内联了，不是运行时读取的。这是Next.js为了优化性能而做的设计——构建时替换避免了运行时的process.env查找开销。

```
# 构建时 .env
NEXT_PUBLIC_API_URL=https://api.example.com
```

构建后，代码中的process.env.NEXT_PUBLIC_API_URL会被替换为字符串"https://api.example.com"。即使你在运行时修改.env文件，也不会生效。这对于Docker化部署是一个挑战——你希望同一个镜像部署到不同环境，但构建时变量已经固定了。

如果需要运行时配置，推荐方案是通过API路由在运行时读取并返回配置：

```tsx
// app/api/config/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    apiUrl: process.env.API_URL,
    cdnUrl: process.env.CDN_URL,
  })
}
```

客户端通过请求这个API获取运行时配置。因为API路由在服务端运行，process.env是运行时读取的，所以同一个构建产物可以适配不同环境。这种方案的缺点是多了一次网络请求，可以在客户端做缓存来缓解。

### 2.4.4 多环境变量管理策略

实际项目中通常有多个环境：开发、测试、预发布、生产。推荐的管理策略是按环境分文件，通过文件名自动加载。

```bash
# .env — 基础配置，所有环境共享
APP_NAME=MyApp

# .env.development — 开发环境
NEXT_PUBLIC_API_URL=http://localhost:3000/api
LOG_LEVEL=debug

# .env.test — 测试环境
NEXT_PUBLIC_API_URL=http://test-api.example.com
LOG_LEVEL=info

# .env.production — 生产环境
NEXT_PUBLIC_API_URL=https://api.example.com
LOG_LEVEL=error

# .env.local — 个人本地覆盖（gitignore）
DATABASE_URL=postgresql://localhost/myapp_local
```

在package.json中通过脚本区分构建环境：

```json
{
  "scripts": {
    "dev": "next dev",
    "build:staging": "cp .env.staging .env.production && next build",
    "build:prod": "next build",
    "start": "next start"
  }
}
```

对于Docker部署，推荐在运行时通过-e参数注入环境变量，而不是在镜像中放.env文件。这样同一个镜像可以无缝部署到不同环境，只需要改变运行参数。

### 2.4.5 敏感信息的安全管理规范

> 密钥泄露不是概率问题，是时间问题。一旦你的.env文件被提交到git仓库，就该立即轮换所有密钥，而不是想着"删掉提交记录就行"。git历史是永久性的，即使你删除了文件，历史记录中仍然存在。

安全管理规范如下。第一，.env.local和所有包含密钥的.env文件必须加入.gitignore。第二，提供.env.example文件作为模板，只包含变量名不包含真实值。第三，生产环境的密钥通过CI/CD平台的安全变量注入，不落盘到代码仓库。第四，定期轮换密钥，不要一套密钥用到天荒地老。

这里补充一个常见的操作误区：有些团队喜欢在CI/CD流水线中把.env文件通过scp复制到服务器上。这种做法虽然可行，但存在安全风险——.env文件在服务器上以明文存在，一旦服务器被入侵，所有密钥都会泄露。更安全的做法是通过容器编排平台（如Kubernetes Secrets）或云服务商的密钥管理服务（如AWS Secrets Manager、阿里云密钥管理）来注入环境变量，这些服务通常提供加密存储和访问审计功能。

```bash
# .env.example — 提交到git，作为配置模板
DATABASE_URL=postgresql://user:pass@host:5432/db
API_SECRET_KEY=your-secret-key-here
NEXT_PUBLIC_API_URL=https://api.example.com
```

```gitignore
# .gitignore
.env*.local
.env
.env.*
!.env.example
```

## 2.5 项目别名配置与路径优化

路径别名是TypeScript项目的基础配置，它让你用简短的虚拟路径替代冗长的相对路径。这个配置虽然简单，但对代码可读性和可维护性影响巨大。

### 2.5.1 tsconfig.json paths配置详解

Next.js默认配置了@/*指向项目根目录，但实际项目中通常需要更细粒度的别名。没有别名时，深层级目录中的文件需要用大量的../../../来引用其他模块，这种相对路径不仅难以阅读，而且在文件移动时会全部失效。

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"],
      "@/components/*": ["./components/*"],
      "@/lib/*": ["./lib/*"],
      "@/styles/*": ["./styles/*"],
      "@/types/*": ["./types/*"],
      "@/hooks/*": ["./hooks/*"],
      "@/utils/*": ["./utils/*"],
      "@/config/*": ["./config/*"]
    }
  }
}
```

对比一下别名的价值：

```tsx
// 没有别名 — 相对路径地狱，文件一移动就全废
import { Button } from '../../../components/ui/Button'
import { formatDate } from '../../../utils/date'
import { User } from '../../../types/user'

// 有别名 — 清晰且稳定，文件移动不影响import
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/utils/date'
import { User } from '@/types/user'
```

别名不仅更短，更重要的是稳定。文件移动位置时，只要别名指向的根目录不变，所有import语句都不需要修改。这在重构时非常有价值。另外，别名还有助于代码审查——当你看到一个import路径是@/services/UserService时，你立刻知道这是业务服务层的代码；而如果看到../../../services/UserService，你需要先计算层级才能确定文件位置。别名本身就是一种路径自解释机制，提升了代码的可读性。

### 2.5.2 常用别名方案：@/components、@/lib、@/styles

以下是一套经过实战验证的别名方案，适合大多数Next.js项目，直接复制到tsconfig.json即可使用：

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/components/*": ["./src/components/*"],
      "@/app/*": ["./src/app/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/types/*": ["./src/types/*"],
      "@/constants/*": ["./src/constants/*"],
      "@/config/*": ["./src/config/*"],
      "@/styles/*": ["./src/styles/*"],
      "@/services/*": ["./src/services/*"],
      "@/store/*": ["./src/store/*"]
    }
  }
}
```

这套别名方案对应的项目结构清晰明了：每个别名对应src目录下的一个子目录，职责单一不重叠。当你在代码中看到`@/components/Button`时，立刻知道这是通用UI组件；看到`@/services/UserService`时，立刻知道这是业务服务层的代码。别名本身就起到了路径自解释的作用。

### 2.5.3 别名在IDE中的自动补全配置

VS Code默认支持tsconfig.json的paths配置，但有时自动补全不够智能。可以通过以下配置增强开发体验。

在.vscode/settings.json中配置：

```json
{
  "typescript.preferences.importModuleSpecifier": "non-relative",
  "typescript.preferences.importModuleSpecifierEnding": "index",
  "path-autocomplete.pathMappings": {
    "@/": "${folder}/src"
  },
  "path-autocomplete.includeExtension": false
}
```

这样在输入@/时，IDE会自动提示src目录下的所有子目录和文件。importModuleSpecifier设为non-relative会让VS Code在自动导入时优先使用别名而不是相对路径。对于JetBrains系列IDE（WebStorm等），tsconfig.json的paths会被自动识别，通常不需要额外配置。

### 2.5.4 别名与模块解析的性能关系

路径别名不只是语法糖，它会影响TypeScript的模块解析速度。理解解析过程有助于编写更高效的配置。

当TypeScript遇到`import { X } from '@/components/Button'`时，编译器会按照paths配置的映射规则，将别名还原为实际路径，然后在文件系统中查找。如果别名配置过多且指向重叠目录，会导致解析开销增加——编译器需要尝试多个可能的路径才能找到文件。

```json
// 推荐：每个别名指向独立目录，无重叠
{
  "paths": {
    "@/components/*": ["./src/components/*"],
    "@/lib/*": ["./src/lib/*"]
  }
}

// 不推荐：别名指向重叠目录，增加解析负担
{
  "paths": {
    "@/components/*": ["./src/components/*"],
    "@/ui/*": ["./src/components/ui/*"],
    "@/buttons/*": ["./src/components/ui/buttons/*"]
  }
}
```

最佳实践是保持别名数量适中，每个别名指向独立的顶层目录，避免嵌套别名。设置baseUrl为"."可以减少解析范围，TypeScript会优先在baseUrl范围内解析。

### 2.5.5 别名迁移与重构技巧

当项目从相对路径迁移到别名时，手动改import效率极低且容易出错。推荐使用工具进行批量重构。

最简单的方式是使用VS Code的搜索替换功能配合正则表达式，但这种方式对于多层级的相对路径（如../../../）需要手动计算层级，容易出错。更可靠的方式是使用代码变换工具：

```bash
# 使用 @hypermod/cli 批量转换import路径
npx @hypermod/cli --transform next-js-path-alias ./src
```

如果不想用工具，一个实用的中间方案是逐步迁移：每次修改文件时顺手把该文件的import改成别名，渐进式完成。这种方式虽然慢，但风险低，不会因为一次大规模重构引入问题。

> 别名配置看似是个小事情，但它在项目初期定下来后会影响整个开发周期。早配置早享受，越拖改起来越痛苦。

## 2.6 规范的项目分层架构设计

### 2.6.1 经典三层架构：UI层/业务层/数据层

不管用什么框架，分层架构的核心思想是不变的：关注点分离（Separation of Concerns，SoC）。每一层只负责自己的职责，不越界处理其他层的逻辑。这种设计的好处是代码可测试、可替换、可维护。

Next.js项目的三层架构如下：

```
┌─────────────────────────────────────────┐
│  UI层 (app/, components/)               │
│  职责：页面渲染、用户交互、状态展示        │
├─────────────────────────────────────────┤
│  业务层 (services/, lib/)               │
│  职责：业务逻辑处理、数据转换、规则校验     │
├─────────────────────────────────────────┤
│  数据层 (repositories/, db/)            │
│  职责：数据存取、外部API调用、缓存管理      │
└─────────────────────────────────────────┘
```

核心原则：数据流向是单向的。UI层调用业务层，业务层调用数据层，反过来不行。这保证了每一层只依赖比自己更底层的模块，不会形成循环依赖。

```tsx
// UI层 — app/users/page.tsx
import { UserService } from '@/services/UserService'

export default async function UsersPage() {
  const users = await UserService.getUsers()
  return <UserList users={users} />
}

// 业务层 — services/UserService.ts
import { UserRepository } from '@/repositories/UserRepository'
export class UserService {
  static async getUsers() {
    const raw = await UserRepository.findAll()
    return raw.map(u => ({ ...u, displayName: u.name }))
  }
}

// 数据层 — repositories/UserRepository.ts
import { db } from '@/lib/db'
export class UserRepository {
  static async findAll() {
    return db.user.findMany()
  }
}
```

这个例子展示了一个完整的调用链：Page到Service到Repository到Database。每一层职责清晰，可以独立测试和替换。比如测试UserService时可以mock UserRepository，不需要真实数据库。替换数据源时只需要修改Repository层，上层代码不受影响。这种可替换性在架构设计中非常重要——当你需要从MySQL切换到PostgreSQL，或者从直接数据库查询切换为调用微服务API时，只需要修改Repository层的实现，业务层和UI层完全不需要改动。

### 2.6.2 Next.js项目目录分层模板（直接套用）

以下是一套我在多个项目中验证过的目录模板，适合中小型到中大型项目，直接复制即可使用。这套模板融合了feature-based（按功能模块）和layered（按层级）两种组织方式的优点。

```
my-next-app/
├── src/
│   ├── app/                    # App Router路由目录
│   │   ├── (auth)/             # 路由组：认证相关页面
│   │   ├── (dashboard)/        # 路由组：仪表盘页面
│   │   ├── api/                # API路由
│   │   ├── layout.tsx          # 根布局
│   │   └── page.tsx            # 首页
│   ├── components/             # 通用组件
│   │   ├── ui/                 # 基础UI组件
│   │   ├── layouts/            # 布局组件
│   │   └── shared/             # 业务通用组件
│   ├── features/               # 功能模块（按业务划分）
│   │   ├── auth/               # 认证模块
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── types.ts
│   │   └── blog/               # 博客模块
│   │       ├── components/
│   │       ├── hooks/
│   │       └── types.ts
│   ├── lib/                    # 基础设施
│   │   ├── db.ts               # 数据库连接
│   │   ├── auth.ts             # 认证工具
│   │   └── utils.ts            # 通用工具
│   ├── hooks/                  # 全局自定义Hooks
│   ├── services/               # 业务服务层
│   ├── repositories/           # 数据访问层
│   ├── types/                  # 全局类型定义
│   ├── constants/              # 常量定义
│   ├── config/                 # 配置文件
│   └── styles/                 # 全局样式
├── public/                     # 静态资源
├── .env.example                # 环境变量模板
├── next.config.mjs             # Next.js配置
├── tsconfig.json               # TypeScript配置
└── package.json
```

这套结构的核心设计思想有三点。第一，features目录按业务模块组织代码，而不是按技术类型。认证相关的组件、Hooks、类型都放在features/auth/下，而不是分散到各个目录。这让模块内聚度更高，修改一个功能时不需要在目录树中跳来跳去。第二，components目录只放真正全局通用的组件，业务相关的组件放在对应feature目录下。第三，services和repositories分离业务逻辑和数据访问，便于测试和替换。

### 2.6.3 服务端代码与客户端代码的物理隔离

App Router中，Server Component和Client Component的边界管理非常重要。不加以控制的话，很容易出现"这个文件到底是服务端还是客户端"的困惑。推荐通过目录结构和文件命名来显式区分。

```
src/
  app/
    page.tsx                    # Server Component（默认）
    ClientWrapper.tsx           # Client Component（use client）
    _components/
      ServerChart.tsx           # Server Component
      ClientChart.tsx           # Client Component
```

命名约定：Server Component文件名不加特殊前缀，因为它是默认。Client Component可以在文件名中体现，或者通过use client标记配合ESLint规则强制检查。

```tsx
// app/dashboard/page.tsx — Server Component
import { getClientData } from '@/services/dashboard'
import DashboardClient from './DashboardClient'

export default async function Dashboard() {
  const data = await getClientData()
  return <DashboardClient data={data} />
}

// app/dashboard/DashboardClient.tsx
'use client'
import { useState } from 'react'
export default function DashboardClient({ data }) {
  const [filter, setFilter] = useState('all')
  return <div>{/* 客户端交互逻辑 */}</div>
}
```

Server Component做数据获取和静态渲染，Client Component做交互和状态管理。通过props从Server Component向Client Component传递数据，注意传递的数据必须是可序列化的——函数、Class实例等不能通过props跨边界传递。

### 2.6.4 共享代码的组织：types、utils、constants

跨模块共享的代码需要放在全局目录下，但要注意粒度控制。共享代码过多会导致全局目录膨胀变成垃圾桶，共享代码过少又会出现重复定义。

推荐的组织方式是按类别分文件，通过barrel file统一导出：

```typescript
// src/types/api.ts — API相关类型
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

// src/types/user.ts — 用户类型
export interface User {
  id: string
  name: string
  email: string
  role: UserRole
}
export type UserRole = 'admin' | 'user' | 'guest'

// src/types/index.ts — 统一出口
export * from './user'
export * from './api'
export * from './common'
```

```typescript
// src/constants/index.ts — 全局常量
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL
export const PAGE_SIZE = 20
export const TOKEN_KEY = 'auth_token'

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
} as const
```

判断一个东西是否应该放全局共享目录的标准：至少被两个不相关的模块使用。如果只有认证模块用到的东西，就放在features/auth/下，不要放到全局。这个标准能有效防止全局目录膨胀。

### 2.6.5 企业级项目目录结构最佳实践

企业级项目相比个人项目，最大的区别是多人协作和长期维护。目录结构需要支持团队协作中的并行开发、代码审查和模块归属。

最佳实践清单如下。

第一，按业务模块垂直切分。每个模块是一个自包含的单元，有自己的组件、Hooks、类型、服务，模块间通过明确的接口通信。这样不同的开发者可以并行开发不同模块，互不干扰。

```
src/
  features/
    auth/
      components/
      hooks/
      services/
      types.ts
      index.ts          # barrel file
    blog/
      components/
      hooks/
      services/
      types.ts
      index.ts
```

第二，使用barrel file（桶文件）作为模块出口，控制暴露内容。其他模块只能通过@/features/auth导入，无法访问内部文件，实现模块封装：

```typescript
// src/features/auth/index.ts
export { LoginForm } from './components/LoginForm'
export { useAuth } from './hooks/useAuth'
export type { User, LoginParams } from './types'
// 不导出内部实现细节
```

第三，配置文件分层管理，不同类型的配置放在不同文件中，通过index.ts统一导出。第四，测试文件与源文件共置，不要建单独的__tests__目录树，测试文件就放在被测试文件旁边。第五，文档就近放置，每个feature目录下放一个README.md，说明该模块的职责、使用方式、维护者信息。

> 企业级项目的目录结构不是为了好看，而是为了降低协作摩擦。好的结构让每个人都知道"这个文件应该放在哪"和"这个功能该找谁"，这比任何文档都有效。

## 2.7 本章小结与课后练习

### 本章核心知识点回顾

这一章我们从路由模式对比出发，完整梳理了Next.js项目的架构设计，内容覆盖了以下几个核心知识块。

第一，App Router是Next.js的未来方向，Pages Router仍然支持但推荐新项目使用App Router。两者可以共存但迁移时要逐页面进行，不能急躁。App Router的核心优势在于嵌套布局、async组件数据获取、按路由段组织加载和错误状态。

第二，app/目录下的特殊文件各有职责：page定义路由内容、layout定义布局且在导航时保持挂载、template每次导航重新挂载、loading自动作为Suspense fallback、error自动作为Error Boundary、not-found处理404状态、global-error捕获根layout错误。理解这些约定是掌握App Router的基础。

第三，next.config.js是项目配置中枢，tsconfig.json的paths配置管理路径别名。环境变量通过NEXT_PUBLIC_前缀区分服务端和客户端可见性，不带前缀的变量绝对不暴露给客户端。配置加载优先级为：命令行参数大于next.config.js大于.env.local大于.env.[environment]大于.env。

第四，项目分层架构遵循关注点分离原则，UI层、业务层、数据层各司其职。features目录按业务模块组织代码是中大型项目的推荐方案，配合barrel file实现模块封装。路径别名要在项目初期就配好，越拖改起来越痛苦。

### 课后练习

练习一：创建一个使用App Router的Next.js项目，实现以下路由结构：首页（/）、博客列表页（/blog）、博客详情页（/blog/:id）、关于页（/about），并为/blog下的所有页面配置共享布局。要求博客详情页在文章不存在时显示局部404页面。

练习二：配置next.config.js，实现以下需求：开启React严格模式、配置远程图片域名cdn.example.com、为所有页面添加X-Frame-Options: DENY响应头、开启typedRoutes实验性功能。

练习三：设计一套环境变量方案，要求：开发环境API地址为http://localhost:3000/api，生产环境为https://api.example.com，数据库连接串只在服务端可用，Google Analytics ID需要在客户端使用。写出完整的.env文件内容和.gitignore配置。

练习四：按照2.6.2节的目录模板，搭建一个项目骨架，包含认证和博客两个feature模块，每个模块有barrel file出口，实现模块封装。在app/目录下创建对应的路由页面，通过feature模块的导出导入组件。

练习五：将以下相对路径import全部改写为别名路径，并配置对应的tsconfig.json paths：

```tsx
import { Button } from '../../../components/ui/Button'
import { useAuth } from '../../hooks/useAuth'
import { formatDate } from '../../../utils/date'
import { User } from '../../types/user'
```

### 下章预告

第3章我们将进入React基础与Next.js组件开发规范，重点讲解Server Component和Client Component的区别与使用场景。这是App Router中最容易踩坑的部分——什么组件能在服务端运行、什么组件必须加use client、组件之间如何嵌套传参、props跨边界传递有什么限制，这些问题将在下一章得到彻底解答。如果你觉得这一章的Server Component和Client Component概念还有些模糊，不用着急，下一章会从头讲清楚。

怕浪猫说：项目架构就像盖房子的地基，地基打得牢，后面怎么建都稳。这一章讲的所有目录约定和配置规则，不是Next.js随便定的，而是无数次踩坑后的最佳实践。建议收藏这一章，每次新建项目时回来对照一遍，确保架构没有跑偏。下一章我们聊组件，更精彩的内容在等着你。

系列进度 2/16

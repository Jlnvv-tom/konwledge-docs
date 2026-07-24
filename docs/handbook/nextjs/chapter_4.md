# 第4章 Next.js路由系统：页面与导航开发

一个文件就是一个路由，一个文件夹就是一个路由段——这套"文件即路由"的设计，让无数从React Router迁过来的开发者直呼"回不去了"。但当你遇到动态路由的方括号嵌套、路由分组的括号语法、布局持久化的渲染机制时，是不是也踩过不少坑？别急，这一章怕浪猫带你从原理到实战，彻底搞懂Next.js App Router的路由系统。

我是怕浪猫，一个在Next.js坑里摸爬滚打多年的全栈开发者。接下来这篇文章，我会把路由系统从底层原理到实战技巧全部拆解清楚，保证你看完就能上手写。

## 4.1 文件即路由：Next.js路由核心原理

### 4.1.1 App Router文件系统路由的映射规则

Next.js App Router（应用路由器）的核心设计哲学是"约定优于配置"（Convention over Configuration）。你不需要手动编写路由配置文件，只需要在`app`目录下按照约定创建文件和文件夹，框架就会自动识别并生成对应的路由。

来看最基本的映射关系：

```
app/
├── page.tsx              →  /
├── about/
│   └── page.tsx          →  /about
├── dashboard/
│   ├── page.tsx          →  /dashboard
│   └── settings/
│       └── page.tsx      →  /dashboard/settings
```

这套规则看起来简单，但背后的设计思想很深刻。传统React项目里，你需要这样写路由配置：

```tsx
// 传统React Router方式
import { Routes, Route } from 'react-router-dom'

<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/about" element={<About />} />
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/dashboard/settings" element={<Settings />} />
</Routes>
```

而在Next.js App Router中，上面的配置完全不需要。你只需要创建对应的文件夹和`page.tsx`文件，路由就自动生成了。这不是魔法，而是文件系统路由（File-System Based Routing）的约定。

> 文件系统路由的本质，是用目录结构替代配置文件。减少的不只是代码量，更是维护成本。每条路由的路径就是它在文件系统中的位置，所见即所得。

### 4.1.2 文件夹与文件的职责区分：文件夹=路由段，文件=UI

这是理解App Router的一个关键点：文件夹和文件扮演着完全不同的角色。很多刚从Pages Router迁过来的开发者会搞混这两者的职责，导致目录结构混乱。

**文件夹**定义路由的路径结构，每个文件夹代表一个路由段（Route Segment）。**文件**则负责渲染对应的UI界面。这两者分离的设计，使得路由结构和UI逻辑各自独立，互不干扰。

```
app/
├── blog/           ← 文件夹：路由段 "blog"
│   ├── page.tsx    ← 文件：blog路由的UI
│   ├── layout.tsx  ← 文件：blog路由的布局
│   └── post/       ← 文件夹：路由段 "post"
│       └── page.tsx← 文件：blog/post路由的UI
```

关键规则是：**只有定义了`page.tsx`的文件夹才是可访问的路由**。如果你只创建了一个文件夹而没有放`page.tsx`，那这个路径是不可访问的。这意味着文件夹可以纯粹用于组织代码结构，而不一定会暴露为URL路径。

一个常见的新手坑是：在`app/blog/`下创建了`layout.tsx`但忘记创建`page.tsx`，访问`/blog`时就会得到404。记住，`layout.tsx`只是布局包裹，真正让路由可访问的是`page.tsx`。这个坑怕浪猫在初学Next.js时踩过不止一次，每次都是对着终端看半天报错才想起来少了`page.tsx`文件。所以建议在创建新路由时，养成一个习惯：先创建`page.tsx`，再创建其他特殊文件。这样就不会遗忘最重要的入口文件了。

### 4.1.3 路由段的层级与URL路径的对应关系

路由段之间通过文件夹的嵌套关系形成层级结构，每一层文件夹对应URL中的一个路径段。URL（Uniform Resource Locator，统一资源定位符）路径就是由这些路由段按顺序用斜杠拼接而成。

```
文件系统结构                          URL路径
app/                                  
├── page.tsx                    →     /
├── products/
│   ├── page.tsx                →     /products
│   └── [id]/
│       └── page.tsx            →     /products/123
└── dashboard/
    ├── analytics/
    │   └── page.tsx            →     /dashboard/analytics
    └── settings/
        └── page.tsx            →     /dashboard/settings
```

注意几个要点：

第一，`app`目录本身不对应URL中的任何段，它是路由的根容器。第二，URL路径的层级严格对应文件夹的嵌套深度，不支持扁平化配置。第三，方括号语法`[id]`表示动态路由段，实际URL中会被具体参数值替换。

这种严格的层级对应关系有一个显著优势：看到文件结构就能推断出URL结构，反过来也一样。这在大型项目协作中极大降低了沟通成本。

### 4.1.4 特殊文件约定：page、layout、loading、error

App Router定义了一系列特殊文件，每个文件名都有固定的语义职责。掌握这些约定，就掌握了路由系统的核心工具箱。

| 文件名 | 职责 | 是否必需 | 重新渲染时机 |
|--------|------|---------|-------------|
| `page.tsx` | 路由的UI界面 | 是（路由可访问的必要条件） | 每次导航到该路由 |
| `layout.tsx` | 共享布局，包裹子路由 | 否 | 仅首次加载时渲染，导航时不重渲染 |
| `loading.tsx` | 加载中的骨架屏UI | 否 | 路由内容加载期间显示 |
| `error.tsx` | 错误边界UI | 否 | 子组件抛出异常时显示 |
| `not-found.tsx` | 404未找到UI | 否 | 路由未匹配时显示 |
| `template.tsx` | 模板组件 | 否 | 每次导航都重新渲染 |

其中最核心的文件是`page.tsx`和`layout.tsx`。`page.tsx`定义路由的实际内容，是路由可访问的必要条件。`layout.tsx`定义共享布局，可以嵌套使用。

一个实际项目中的目录结构通常长这样：

```
app/
├── layout.tsx          ← 根布局（必需）
├── page.tsx            ← 首页
├── loading.tsx         ← 全局加载态
├── error.tsx           ← 全局错误边界
├── not-found.tsx       ← 全局404
├── blog/
│   ├── layout.tsx      ← blog专属布局
│   ├── page.tsx        ← blog列表页
│   ├── loading.tsx     ← blog加载骨架
│   └── [id]/
│       ├── page.tsx    ← blog详情页
│       └── error.tsx   ← 详情页错误边界
```

> 特殊文件约定的精髓在于：每个文件只做一件事。page负责内容，layout负责骨架，loading负责过渡，error负责兜底。单一职责，各司其职。

### 4.1.5 路由系统的底层实现：基于文件系统的路由表生成

理解了表面约定后，来看看底层是怎么实现的。Next.js在构建时会扫描`app`目录的文件系统结构，生成一张完整的路由表（Route Table）。这张表记录了每个路由的路径模式、对应的组件文件、以及布局嵌套关系。这是整个App Router能够正常运转的基石。

简化后的路由表生成过程如下：

```
构建时扫描 app/ 目录
       ↓
解析文件和文件夹的嵌套关系
       ↓
识别特殊文件（page、layout、loading等）
       ↓
解析动态路由参数（[id]、[...slug]等）
       ↓
生成路由表（Route Manifest）
       ↓
注册到Next.js路由匹配引擎
```

运行时，当用户请求一个URL时，Next.js的路由匹配引擎会在路由表中查找匹配项。匹配成功后，按照布局嵌套顺序组装组件树，最终渲染出完整的页面。这个过程是自动化的，开发者不需要关心路由匹配的具体实现细节。

对于动态路由，路由表会记录参数模式。例如`app/products/[id]/page.tsx`会生成路由模式`/products/:id`，当请求`/products/123`时，`id`参数被解析为`"123"`并传递给页面组件。如果路由模式是`/products/:id/:variant`，那么访问`/products/123/red`就会同时解析出`id="123"`和`variant="red"`两个参数。

这里有一个经常被问到的问题：路由表是构建时生成的还是运行时动态生成的？答案是大部分路由在构建时确定，但也有一些例外。比如使用了`generateStaticParams`的动态路由，预生成路径在构建时确定，但未预生成的路径可以在运行时按需渲染。此外，Middleware可以在运行时对路由进行拦截和重定向，这是路由匹配之前的一个动态环节。

这个机制意味着路由是在构建时确定的（除了middleware的运行时重定向），所以路由的增删改需要重新构建部署。这也是为什么Next.js被称为"构建时路由"框架的原因。与传统React Router的运行时路由匹配相比，构建时路由的优势在于性能更好、SEO更友好，劣势是灵活性略低——你不能在运行时动态注册新路由。

## 4.2 基础静态路由与页面创建

### 4.2.1 创建静态页面：app/about/page.tsx

静态路由是最简单的路由形式。创建一个静态页面只需要两步：在`app`目录下创建文件夹，然后放入`page.tsx`文件。

以创建一个"关于我们"页面为例：

```tsx
// app/about/page.tsx
export default function AboutPage() {
  return (
    <main>
      <h1>关于我们</h1>
      <p>这是关于页面的内容</p>
    </main>
  )
}
```

就这样，不需要任何路由配置。访问`/about`就能看到这个页面。`page.tsx`中导出的默认组件就是该路由的UI界面。

有一个容易忽略的细节：组件名称`AboutPage`只是代码中的语义命名，跟路由路径没有任何关系。路由路径完全由文件夹名`about`决定。即使你把组件命名为`FooBar`，路由依然是`/about`。

### 4.2.2 多级静态路由：app/dashboard/settings/page.tsx

多级静态路由就是文件夹的嵌套。以仪表盘设置页为例：

```tsx
// app/dashboard/settings/page.tsx
export default function SettingsPage() {
  return (
    <main>
      <h1>系统设置</h1>
      <section>
        <h2>账户安全</h2>
        <p>修改密码、两步验证等</p>
      </section>
      <section>
        <h2>通知偏好</h2>
        <p>邮件通知、短信通知等</p>
      </section>
    </main>
  )
}
```

对应的URL是`/dashboard/settings`。如果你想再加一个`/dashboard/analytics`页面，只需要创建`app/dashboard/analytics/page.tsx`即可。

多级路由的层级没有硬性限制，但从实际维护角度建议不要超过三到四层。过深的路由嵌套不仅让URL冗长，也会增加布局复杂度。

### 4.2.3 首页路由：app/page.tsx的默认行为

`app/page.tsx`是整个应用的根路由页面，对应URL `/`。这是Next.js的默认约定，不需要任何配置。

```tsx
// app/page.tsx
export default function HomePage() {
  return (
    <main>
      <h1>欢迎来到首页</h1>
      <p>这是网站的入口页面</p>
    </main>
  )
}
```

如果你没有创建`app/page.tsx`，访问根路径`/`将返回404。这一点在初始化项目时需要注意——Next.js的`create-next-app`脚手架会自动生成这个文件，但如果你是从零开始搭建目录结构，别忘了创建它。

### 4.2.4 静态路由的导航性能优势

静态路由在性能上有一个重要优势：**可以在构建时预渲染**。因为静态路由的路径是固定的，Next.js在构建时就能生成对应的HTML文件，部署到CDN（Content Delivery Network，内容分发网络）后可以直接静态分发。这意味着无论用户在世界哪个角落，都能从最近的CDN节点获取页面内容，延迟极低。

这意味着用户访问静态路由页面时，不需要服务端实时渲染，直接从CDN获取预渲染的HTML，首屏加载速度极快。根据实际测试，一个预渲染的静态页面首屏加载时间通常在100ms以内，而服务端实时渲染的页面可能需要300ms到1秒。

```
静态路由构建流程：
源码 → 构建时预渲染 → 生成静态HTML → 部署到CDN → 用户直接获取

动态路由流程（未优化）：
用户请求 → 服务器接收 → 实时获取数据 → 渲染HTML → 返回响应
```

相比之下，动态路由如果使用了运行时数据获取，可能需要服务端实时渲染，首屏加载时间会更长。当然，通过`generateStaticParams`可以预生成动态路由页面，这部分后面会讲。所以一个性能优化建议是：能用静态路由就不要用动态路由，必须用动态路由时尽量配合`generateStaticParams`做预生成。

另一个常被忽略的性能优势是：静态路由的页面可以被搜索引擎爬虫直接获取完整的HTML内容，不需要执行JavaScript就能看到页面内容。这对于SEO来说是一个巨大的优势，因为搜索引擎爬虫对静态HTML的抓取和索引效率远高于需要执行JS才能渲染内容的页面。

### 4.2.5 静态页面开发规范与最佳实践

在实际项目开发中，怕浪猫总结了以下静态路由的开发规范。这些规范不是Next.js的硬性要求，而是经过多个项目验证后的经验总结，遵循它们可以让代码更易维护、更易协作。

**规范一：一个路由一个文件夹。** 不要在一个文件夹下放多个页面文件，`page.tsx`是唯一的页面入口文件。如果你需要子页面，创建子文件夹。

**规范二：文件夹名用小写连字符。** 如果路由名由多个单词组成，用连字符连接，如`user-profile`。虽然Next.js对大小写不敏感，但统一用小写加连字符是社区共识，避免URL中出现大小写混用的问题。

**规范三：语义化命名。** 文件夹名应该能直观反映页面含义。`app/products/`比`app/p/`更清晰，在URL中`/products`也比`/p`对用户更友好。

**规范四：合理控制嵌套深度。** 保持在三到四层以内。如果发现需要更深的嵌套，考虑用路由分组来组织，而不是一味增加URL层级。

```
推荐结构                          不推荐结构
app/                              app/
├── shop/                         ├── s/
│   ├── products/                 │   ├── p/
│   │   └── page.tsx              │   │   └── page.tsx
│   └── cart/                     │   └── c/
│       └── page.tsx              │       └── page.tsx
```

## 4.3 动态路由、可选动态路由、捕获所有路由

### 4.3.1 动态路由：[id]参数段的定义与使用

动态路由是实际项目中最常用的路由形式。电商网站的商品详情页、博客的文章页、用户主页，这些场景都需要从URL中提取动态参数。没有动态路由，你就得为每个商品手动创建一个页面文件，这在有成千上万条数据的场景下是完全不现实的。App Router使用方括号语法来定义动态路由段，优雅地解决了这个问题。

```
app/
└── products/
    └── [id]/
        └── page.tsx      →  /products/123, /products/abc
```

`[id]`文件夹表示这是一个动态路由段，`id`是参数名。当用户访问`/products/123`时，`123`会被提取为`id`参数的值，传递给页面组件。

在页面组件中如何接收这个参数呢？通过`params`属性：

```tsx
// app/products/[id]/page.tsx
export default function ProductPage({
  params
}: {
  params: { id: string }
}) {
  return (
    <main>
      <h1>商品详情</h1>
      <p>当前商品ID: {params.id}</p>
    </main>
  )
}
```

注意在Next.js 15+版本中，`params`是一个Promise，需要用`async/await`来获取：

```tsx
// Next.js 15+ 版本
export default async function ProductPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <h1>商品ID: {id}</h1>
}
```

> 方括号语法是App Router中最直观的动态路由表达方式。一个方括号对应一个URL段，参数名写在方括号内。看到`[id]`就知道这里有个叫id的动态参数，代码即文档。

### 4.3.2 动态参数的获取：params对象

`params`对象是动态路由参数的载体。当路由中有多个动态段时，`params`会包含所有参数。

```tsx
// app/blog/[category]/[slug]/page.tsx
// URL: /blog/tech/nextjs-routing-guide

export default async function BlogPostPage({
  params
}: {
  params: Promise<{ category: string; slug: string }>
}) {
  const { category, slug } = await params
  
  return (
    <article>
      <p>分类: {category}</p>
      <p>文章标识: {slug}</p>
    </article>
  )
}
```

上面的例子中，URL`/blog/tech/nextjs-routing-guide`会被解析为`category="tech"`和`slug="nextjs-routing-guide"`。

一个需要注意的点是：`params`中的所有值都是字符串类型。即使你的URL是`/products/123`，`params.id`的类型也是`"123"`（字符串），不是数字。如果需要数字类型，要手动转换：

```tsx
const productId = Number(params.id)
// 注意处理NaN的情况
if (Number.isNaN(productId)) {
  notFound()
}
```

### 4.3.3 可选动态路由：[[...slug]]的双层方括号语法

可选动态路由（Optional Catch-all Routes）使用双层方括号语法`[[...slug]]`，它和普通捕获路由的区别在于：**即使URL中没有对应的路径段，路由也能匹配**。这个语法看起来有点奇怪，但理解了它的设计意图就会发现非常实用。双层方括号表示"可选"，单层方括号加省略号表示"捕获所有"，两者组合就是"可选地捕获所有路径段"。

```
app/
└── docs/
    └── [[...slug]]/
        └── page.tsx
```

这个路由会匹配以下所有URL：

```
/docs                 → slug = undefined
/docs/getting-started → slug = ["getting-started"]
/docs/api/reference   → slug = ["api", "reference"]
```

注意`/docs`也能匹配，这就是"可选"的含义。来看具体代码：

```tsx
// app/docs/[[...slug]]/page.tsx
export default async function DocsPage({
  params
}: {
  params: Promise<{ slug?: string[] }>
}) {
  const { slug } = await params
  
  if (!slug) {
    return <h1>文档首页</h1>
  }
  
  return (
    <article>
      <h1>文档: {slug.join('/')}</h1>
    </article>
  )
}
```

这个模式特别适合文档系统场景：根路径显示文档首页，子路径显示具体文档页面，用同一个路由组件统一处理。

### 4.3.4 捕获所有路由：[...catchAll]的优先级规则

捕获所有路由（Catch-all Routes）使用单层方括号加省略号语法`[...slug]`，它会匹配指定路径下的所有子路径，但**至少需要一个路径段**。

```
app/
├── docs/
│   └── [...slug]/
│       └── page.tsx     ← 匹配 /docs/a, /docs/a/b, 但不匹配 /docs
└── docs/
    └── page.tsx          ← 匹配 /docs
```

来对比一下三种动态路由的匹配规则：

| 路由语法 | 匹配 `/docs` | 匹配 `/docs/a` | 匹配 `/docs/a/b` |
|---------|-------------|---------------|-----------------|
| `[slug]` | 不匹配 | 匹配，slug="a" | 不匹配 |
| `[[...slug]]` | 匹配，slug=undefined | 匹配，slug=["a"] | 匹配，slug=["a","b"] |
| `[...slug]` | 不匹配 | 匹配，slug=["a"] | 匹配，slug=["a","b"] |

当多个路由规则可能同时匹配时，Next.js的优先级规则是：**静态路由 > 动态路由 > 捕获所有路由 > 可选捕获所有路由**。

```
优先级从高到低：
app/docs/page.tsx              ← 最高（静态路由）
app/docs/[id]/page.tsx         ← 次之（动态路由）
app/docs/[...slug]/page.tsx    ← 再次（捕获所有路由）
app/docs/[[...slug]]/page.tsx  ← 最低（可选捕获所有路由）
```

这意味着如果你同时定义了`app/docs/page.tsx`和`app/docs/[...slug]/page.tsx`，访问`/docs`时会命中静态路由`page.tsx`，而访问`/docs/anything`时会命中捕获路由。

### 4.3.5 动态路由的generateStaticParams预生成

动态路由默认是在运行时渲染的，但如果你想在构建时预生成动态路由页面，可以使用`generateStaticParams`函数。这在SSG（Static Site Generation，静态站点生成）场景下非常重要。

```tsx
// app/products/[id]/page.tsx
export async function generateStaticParams() {
  const products = await fetch('https://api.example.com/products')
    .then(res => res.json())
  
  return products.map((product: { id: string }) => ({
    id: product.id,
  }))
}

export default async function ProductPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const product = await fetch(
    `https://api.example.com/products/${id}`
  ).then(res => res.json())
  
  return <h1>{product.name}</h1>
}
```

`generateStaticParams`在构建时执行，返回所有需要预生成的参数组合。Next.js会为每个参数组合生成一个静态HTML页面。这样用户访问这些页面时，直接返回预渲染的HTML，无需服务端实时渲染。

一个实际的踩坑经验：如果你的数据量很大（比如有几万条商品），全部预生成会导致构建时间过长。有一次怕浪猫在做一个电商项目时，商品总数有三万多条，`generateStaticParams`把所有商品ID都返回了，结果构建跑了将近一个小时。这在CI/CD（Continuous Integration / Continuous Deployment，持续集成/持续部署）流水线中是完全不可接受的。这时可以只预生成热门商品，其余的走按需渲染。利用`dynamicParams`配置可以控制这个行为：

```tsx
// 只预生成部分页面，其余按需渲染
export const dynamicParams = true // 默认值，允许未预生成的路径在运行时渲染

export async function generateStaticParams() {
  // 只预生成热门商品
  const hotProducts = await getHotProducts()
  return hotProducts.map((p: { id: string }) => ({ id: p.id }))
}
```

## 4.4 嵌套路由与全局布局、局部布局

### 4.4.1 嵌套路由的文件结构约定

嵌套路由是App Router的核心特性之一。通过文件夹的嵌套，你可以构建出层次分明的路由结构。而布局（Layout）的嵌套渲染机制，让共享UI的复用变得优雅。

一个典型的嵌套路由结构：

```
app/
├── layout.tsx              ← 根布局
├── page.tsx                ← 首页 /
├── dashboard/
│   ├── layout.tsx          ← dashboard布局
│   ├── page.tsx            ← /dashboard
│   ├── analytics/
│   │   └── page.tsx        ← /dashboard/analytics
│   └── settings/
│       └── page.tsx        ← /dashboard/settings
```

在这个结构中，`/dashboard/analytics`路由的渲染会依次经过：根布局 → dashboard布局 → analytics页面。这种嵌套关系是自动的，不需要手动配置。

### 4.4.2 根布局：app/layout.tsx的职责

根布局（Root Layout）是整个应用的顶层布局，是必需的。它包裹所有路由的UI，通常用于放置全局样式、字体配置、全局Provider等。

```tsx
// app/layout.tsx
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '我的应用',
  description: 'Next.js应用示例',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        <header>
          <nav>全局导航栏</nav>
        </header>
        <main>{children}</main>
        <footer>全局页脚</footer>
      </body>
    </html>
  )
}
```

根布局有几个重要职责：

第一，必须包含`<html>`和`<body>`标签，这是整个HTML文档的根节点。第二，全局CSS在这里引入。第三，SEO（Search Engine Optimization，搜索引擎优化）相关的metadata在这里配置。第四，全局Context Provider（如果需要客户端状态管理）通常也放在这里。

需要注意的是，根布局中的`<html>`和`<body>`标签只能在根布局中出现一次。子布局中不要重复写这些标签，否则会导致HTML结构错误。

### 4.4.3 局部布局：子目录下的layout.tsx嵌套

除了根布局，任何路由段都可以有自己的布局。只需要在对应文件夹下创建`layout.tsx`：

```tsx
// app/dashboard/layout.tsx
import Link from 'next/link'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <nav>
          <Link href="/dashboard">概览</Link>
          <Link href="/dashboard/analytics">数据分析</Link>
          <Link href="/dashboard/settings">系统设置</Link>
        </nav>
      </aside>
      <div className="dashboard-content">
        {children}
      </div>
    </div>
  )
}
```

这个布局会包裹`/dashboard`下的所有子路由。当用户在`/dashboard/analytics`和`/dashboard/settings`之间切换时，`DashboardLayout`不会重新渲染，只有`children`部分会更新。

### 4.4.4 布局与页面的组合渲染顺序

理解布局和页面的组合渲染顺序非常重要。Next.js会从根布局开始，逐层嵌套子布局，最内层是页面内容。这个渲染顺序是自动的，由文件系统的嵌套结构决定，开发者不需要手动配置。

```
渲染顺序（以 /dashboard/settings 为例）：

RootLayout
  └── DashboardLayout
        └── SettingsPage（page.tsx）
```

对应的组件树结构：

```tsx
<RootLayout>
  <DashboardLayout>
    <SettingsPage />
  </DashboardLayout>
</RootLayout>
```

这个渲染顺序意味着：外层布局的副作用会影响内层内容。比如根布局中的全局样式会影响所有子组件，dashboard布局中的侧边栏会始终显示在dashboard区域。这种从外到内的渲染流程，确保了布局的一致性和嵌套的合理性。

一个容易踩的坑是数据获取的依赖关系。如果你在布局中获取了数据，子页面也依赖这些数据，需要通过Props向下传递或者使用Context共享。但布局不能向子组件传递Props（`children`是框架注入的），所以通常用Context或数据预取的方式。一个常见的模式是在布局中获取公共数据，通过React Context向下游页面注入：

```tsx
// app/dashboard/layout.tsx
import { UserProvider } from './UserContext'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getCurrentUser()
  
  return (
    <UserProvider user={user}>
      <aside>{/* 侧边栏 */}</aside>
      <main>{children}</main>
    </UserProvider>
  )
}
```

这样dashboard下的所有子页面都能通过`useContext`获取用户数据，无需各自重复请求。但要注意，Context Provider必须是客户端组件（需要`'use client'`），而布局本身可以是服务端组件。这种"服务端获取数据 + 客户端Context共享"的模式是Next.js中最常见的数据流方案之一。

> 布局嵌套的渲染顺序就像俄罗斯套娃：最外层是根布局，一层层剥开才是页面内容。导航切换时，外层的套娃不动，只有最内层的页面在变。

### 4.4.5 布局持久化：导航时布局不重新渲染

这是App Router最强大的特性之一：**在路由间导航时，共享的布局不会重新渲染**。

举个例子，用户从`/dashboard/analytics`导航到`/dashboard/settings`时：

```
导航前：RootLayout → DashboardLayout → AnalyticsPage
导航后：RootLayout → DashboardLayout → SettingsPage
                  ↑ 不变              ↑ 变化
```

`RootLayout`和`DashboardLayout`保持不变，不会卸载和重新挂载。只有页面组件从`AnalyticsPage`变为`SettingsPage`。

这个特性带来了几个实际好处：

第一，状态保持。布局中持有的React状态（如侧边栏展开/收起状态、主题切换状态）在导航时不会丢失。这在传统React Router中很难实现，因为路由切换通常意味着组件卸载。而在App Router中，布局组件的实例在整个导航过程中始终存活。

第二，性能提升。不需要重新渲染布局组件，减少了渲染开销和DOM操作。对于一个包含复杂侧边栏、多层导航的后台管理系统来说，这个优化可以节省数十毫秒的渲染时间。

第三，用户体验一致。导航时布局区域不会闪烁，视觉体验更流畅。用户在页面间切换时，只有内容区域发生变化，导航栏、侧边栏等框架元素保持稳定，这种视觉连续性对用户体验至关重要。

但这也带来一个需要注意的点：如果你希望某些UI在每次导航时都重新渲染，不要放在布局里。比如需要在每次页面切换时重置滚动位置的容器、需要在每次导航时重新获取数据的组件，放在布局中是不会重新执行的。这时候应该用`template.tsx`替代`layout.tsx`。`template.tsx`的职责和`layout.tsx`类似，但每次导航都会重新渲染。

```tsx
// app/dashboard/template.tsx
// 每次导航到dashboard子路由时都会重新渲染
export default function DashboardTemplate({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="dashboard-template">
      {children}
    </div>
  )
}
```

## 4.5 路由分组与模块隔离

### 4.5.1 路由分组：(group)文件夹的括号语法

随着项目规模增长，路由结构会变得复杂。有时候你希望把某些路由组织在一起，但不希望它们出现在URL路径中。这就是路由分组（Route Groups）的用途。

路由分组使用括号语法：`(groupName)`。括号内的名称仅用于组织代码结构，不会出现在URL中。

```
app/
├── (marketing)/         ← 路由分组，URL中不可见
│   ├── page.tsx         →  /
│   ├── about/
│   │   └── page.tsx     →  /about
│   └── contact/
│       └── page.tsx     →  /contact
├── (dashboard)/         ← 另一个分组
│   ├── dashboard/
│   │   └── page.tsx     →  /dashboard
│   └── analytics/
│       └── page.tsx     →  /analytics
```

注意看URL路径：`(marketing)`和`(dashboard)`在URL中完全不存在。`app/(marketing)/about/page.tsx`对应的URL是`/about`，不是`/(marketing)/about`。

### 4.5.2 分组不影响URL路径

这是路由分组最核心的特性。分组的括号被Next.js在路由解析时完全忽略，文件夹名中的括号部分不会成为URL的一个段。

来做个对比：

```
文件结构                              URL路径
app/blog/page.tsx                     /blog
app/(content)/blog/page.tsx           /blog （分组不影响URL）
app/shop/[id]/page.tsx                /shop/123
app/(store)/shop/[id]/page.tsx        /shop/123 （分组不影响URL）
```

这意味着你可以自由地用分组来组织代码，而不用担心影响URL结构。同一项目可以有多种分组方案，URL结构保持不变。

### 4.5.3 分组级别的独立布局

路由分组最实用的场景是为不同模块设置独立布局。这是路由分组存在的核心价值——如果没有分组，所有路由只能共享同一套布局结构，这在复杂项目中是完全不可行的。比如营销页面和后台管理页面需要完全不同的布局结构：

```
app/
├── (marketing)/
│   ├── layout.tsx       ← 营销页面专用布局
│   ├── page.tsx         →  /
│   └── about/
│       └── page.tsx     →  /about
├── (dashboard)/
│   ├── layout.tsx       ← 后台管理专用布局
│   └── dashboard/
│       └── page.tsx     →  /dashboard
└── layout.tsx           ← 根布局（所有分组共享）
```

渲染`/about`时：`RootLayout → MarketingLayout → AboutPage`
渲染`/dashboard`时：`RootLayout → DashboardLayout → DashboardPage`

两个分组各自拥有独立的布局，互不干扰。这在实际项目中非常实用——营销页面需要带导航栏和页脚的公共布局，后台管理需要带侧边栏的全屏布局，用分组轻松隔离。

```tsx
// app/(marketing)/layout.tsx
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="marketing">
      <header>Logo + 导航</header>
      {children}
      <footer>版权信息</footer>
    </div>
  )
}
```

```tsx
// app/(dashboard)/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="dashboard">
      <aside>侧边栏菜单</aside>
      <main>{children}</main>
    </div>
  )
}
```

### 4.5.4 多个分组的布局组合策略

在大型项目中，你可能需要更灵活的布局组合。一个常见的需求是：某些页面需要认证布局，某些页面不需要。可以通过分组来实现：

```
app/
├── (auth)/
│   ├── layout.tsx       ← 认证布局（登录态检查）
│   ├── login/
│   │   └── page.tsx     →  /login
│   └── register/
│       └── page.tsx     →  /register
├── (app)/
│   ├── layout.tsx       ← 应用主布局
│   ├── page.tsx         →  /
│   └── profile/
│       └── page.tsx     →  /profile
└── layout.tsx           ← 根布局
```

这种组织方式让认证相关页面和应用主页面完全隔离，各自拥有独立布局和逻辑。需要注意的是，**同一个URL路径不能被多个分组中的page.tsx同时定义**。如果你在`(marketing)/page.tsx`和`(dashboard)/page.tsx`都定义了根路径`/`的页面，构建时会报错。

> 路由分组就像代码里的命名空间：它帮你组织代码结构，但不影响外部接口。用得好，大型项目的路由结构可以清爽一倍。

### 4.5.5 分组在大型项目中的模块化实践

在真实的大型项目中，路由分组的典型组织方式如下：

```
app/
├── layout.tsx               ← 根布局
├── (public)/                ← 公开页面分组
│   ├── layout.tsx           ← 公开页面布局（带导航栏）
│   ├── (home)/
│   │   └── page.tsx         →  /
│   ├── about/
│   │   └── page.tsx         →  /about
│   └── pricing/
│       └── page.tsx         →  /pricing
├── (auth)/                  ← 认证页面分组
│   ├── layout.tsx           ← 认证布局（居中卡片样式）
│   ├── login/
│   │   └── page.tsx         →  /login
│   └── signup/
│       └── page.tsx         →  /signup
├── (dashboard)/             ← 后台管理分组
│   ├── layout.tsx           ← 后台布局（侧边栏）
│   ├── overview/
│   │   └── page.tsx         →  /overview
│   ├── projects/
│   │   └── [id]/
│   │       └── page.tsx     →  /projects/123
│   └── settings/
│       └── page.tsx         →  /settings
```

这种组织方式有几个优势：模块边界清晰，每个分组可以由不同团队负责，不同团队的代码修改不会互相干扰；布局独立，修改一个分组的布局不会影响其他分组，降低回归风险；URL路径保持简洁，分组括号不会污染URL，用户看到的URL永远是干净的。

需要注意的是，分组内的路由路径不能与分组外的路由冲突。比如`(public)/about/page.tsx`和直接`about/page.tsx`都映射到`/about`，同时存在会导致构建时报错。这是新手常犯的错误——以为放在不同分组就不会冲突，实际上Next.js在生成路由表时会发现同一个URL模式被定义了两次。

还有一个进阶用法：分组可以嵌套。你可以在一个分组内部再创建子分组，实现更细粒度的布局组合。比如在`(dashboard)`分组内再分`(reports)`和`(admin)`两个子分组，各自拥有不同的布局层次。不过怕浪猫建议嵌套不要超过两层，否则布局组合关系会变得难以追踪。

```tsx
// app/(dashboard)/(admin)/layout.tsx
// 渲染顺序：RootLayout → DashboardLayout → AdminLayout → Page
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="admin-panel">
      <div className="admin-banner">管理员模式</div>
      {children}
    </div>
  )
}
```

这种嵌套分组在实际项目中非常实用。想象一个SaaS（Software as a Service，软件即服务）应用：普通用户和管理员都通过dashboard入口访问，但管理员页面需要额外的权限验证横幅和操作面板。用嵌套分组可以优雅地实现这种布局叠加，而不需要在每个页面中重复写权限判断逻辑。

## 4.6 编程式导航与声明式导航（Link、useRouter）

### 4.6.1 Link组件：声明式导航的核心用法

Next.js的`Link`组件是声明式导航的核心。它基于HTML的`<a>`标签，但在客户端实现了路由预取和无缝导航，不需要整页刷新。

```tsx
import Link from 'next/link'

export default function NavigationExample() {
  return (
    <nav>
      <Link href="/">首页</Link>
      <Link href="/about">关于我们</Link>
      <Link href={`/products/${productId}`}>商品详情</Link>
      <Link href="/dashboard/settings">系统设置</Link>
    </nav>
  )
}
```

`Link`组件的基本用法很简单，只需要设置`href`属性。`href`可以是静态字符串，也可以是模板字符串拼接的动态路径。

几个实用的属性配置：

```tsx
<Link 
  href="/about"
  replace              // 替换浏览器历史记录，不留后退记录
  scroll={false}       // 导航后不滚动到页面顶部
  prefetch={true}      // 预取目标页面（默认行为）
  className="nav-link"
>
  关于我们
</Link>
```

`replace`属性适合用在登录后重定向、表单提交后跳转等场景，用户点浏览器后退按钮时不会回到已经处理完的页面。`scroll`属性在弹窗内导航或保持滚动位置的场景很有用。

一个常见踩坑点：`Link`组件在服务端组件和客户端组件中都可以使用，但如果需要在点击时执行JS逻辑（如埋点、权限校验），需要用`onClick`属性，这时组件所在的文件需要标记`'use client'`。

### 4.6.2 useRouter：编程式导航的push、replace、back

当需要根据逻辑动态跳转页面时，比如表单提交成功后跳转、权限校验失败后重定向，就需要用到编程式导航。App Router提供了`useRouter` hook来实现。

```tsx
'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SearchBox() {
  const router = useRouter()
  const [query, setQuery] = useState('')

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    router.push(`/search?q=${encodeURIComponent(query)}`)
  }

  return (
    <form onSubmit={handleSearch}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索..."
      />
      <button type="submit">搜索</button>
    </form>
  )
}
```

`useRouter`提供的三个核心方法：

| 方法 | 用途 | 示例 |
|------|------|------|
| `router.push(href)` | 导航到新页面，保留历史记录 | `router.push('/dashboard')` |
| `router.replace(href)` | 替换当前页面，不留历史记录 | `router.replace('/login')` |
| `router.back()` | 返回上一页 | `router.back()` |
| `router.forward()` | 前进到下一页 | `router.forward()` |
| `router.refresh()` | 刷新当前路由数据 | `router.refresh()` |

一个实际场景：表单提交后根据结果跳转。

```tsx
'use client'

import { useRouter } from 'next/navigation'

export default function LoginForm() {
  const router = useRouter()

  const handleSubmit = async (formData: FormData) => {
    const result = await login(formData)
    
    if (result.success) {
      router.replace('/dashboard')  // 登录成功，replace避免后退回登录页
    } else {
      router.refresh()  // 登录失败，刷新页面显示错误信息
    }
  }

  return <form action={handleSubmit}>{/* 表单内容 */}</form>
}
```

> 声明式导航用Link，编程式导航用useRouter。选择标准很简单：如果跳转目标在渲染时就能确定，用Link；如果需要等用户交互或异步结果才能决定跳哪，用useRouter。

### 4.6.3 路由预取：Link的prefetch性能优化

`Link`组件默认开启了路由预取（Prefetch）。当`Link`出现在视口中时，Next.js会在后台预取目标路由的数据和代码。当用户真正点击时，页面几乎是瞬时加载的。

预取的行为可以通过`prefetch`属性控制：

```tsx
// 默认行为：在开发环境预取完整页面，生产环境预取RSC payload
<Link href="/about">关于</Link>

// 完全禁用预取
<Link href="/heavy-page" prefetch={false}>
  重量级页面
</Link>

// 强制预取完整页面数据
<Link href="/dashboard" prefetch={true}>
  仪表盘
</Link>
```

什么时候应该禁用预取？当目标页面需要加载大量数据或执行复杂计算时，预取会消耗带宽和服务器资源。如果页面不常被访问，禁用预取是合理的选择。

预取机制的工作原理：

```
Link进入视口
     ↓
Next.js后台请求目标路由的RSC Payload
     ↓
缓存到客户端
     ↓
用户点击Link
     ↓
直接使用缓存的Payload渲染（瞬时完成）
```

这就是为什么Next.js应用导航感觉特别快的原因——大部分工作在用户点击之前就已经完成了。

不过预取也不是完美无缺的。在一个页面中放置大量带有预取的Link组件，会导致后台同时发起大量预取请求，占用网络带宽和服务器资源。特别是列表页中几十个商品链接同时出现在视口中时，预取请求会像洪水一样涌向服务器。想象一下一个商品列表页有50个商品卡片，每个卡片都有一个Link，页面加载后50个预取请求同时发出，这对服务器来说是不小的压力。解决这个问题有两个方案：一是对非首屏的Link设置`prefetch={false}`，二是利用Intersection Observer只预取即将进入视口的链接。

```tsx
// 列表项中禁用预取，避免大量并发请求
{products.map(product => (
  <Link 
    key={product.id}
    href={`/products/${product.id}`}
    prefetch={false}
  >
    {product.name}
  </Link>
))}
```

然后在用户hover某个链接时再触发预取，实现按需预取的效果。这种策略在数据量大的列表页中可以显著降低服务器压力。

### 4.6.4 导航传参：查询参数与动态参数

导航时的参数传递有两种方式：动态参数（URL路径参数）和查询参数（Query String）。选择哪种方式取决于参数的语义：如果参数是资源的唯一标识（如商品ID、文章slug），用动态参数；如果参数是过滤、排序、分页等非标识性信息，用查询参数。这个区分不仅是技术规范，更是RESTful API（Representational State Transfer，表现层状态转移）设计原则在前端路由中的体现。

**动态参数**通过路由路径传递，适合表示资源标识：

```tsx
// 声明式
<Link href={`/products/${productId}`}>查看商品</Link>

// 编程式
router.push(`/products/${productId}`)
```

在目标页面通过`params`获取（前面4.3.2节已讲解）。

**查询参数**通过URL的query string传递，适合过滤、排序等非标识性参数：

```tsx
'use client'

import { useRouter, useSearchParams } from 'next/navigation'

export default function ProductFilter() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const handleFilter = (category: string) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('category', category)
    router.push(`/products?${params.toString()}`)
  }

  return (
    <div>
      <button onClick={() => handleFilter('electronics')}>电子产品</button>
      <button onClick={() => handleFilter('clothing')}>服装</button>
    </div>
  )
}
```

在目标页面读取查询参数：

```tsx
import { useSearchParams } from 'next/navigation'

// 客户端组件中
'use client'
export default function ProductsPage() {
  const searchParams = useSearchParams()
  const category = searchParams.get('category')
  const sort = searchParams.get('sort')
  
  return <p>分类: {category}, 排序: {sort}</p>
}
```

```tsx
// 服务端组件中，通过searchParams prop获取
export default async function ProductsPage({
  searchParams
}: {
  searchParams: Promise<{ [key: string]: string | string[] }>
}) {
  const { category } = await searchParams
  return <p>分类: {category}</p>
}
```

### 4.6.5 useRouter在服务端组件中的限制与替代方案

这是一个非常常见的踩坑点：`useRouter`只能在客户端组件中使用。在服务端组件中调用`useRouter`会直接报错。

```tsx
// 这会报错！
// app/products/page.tsx（服务端组件）
import { useRouter } from 'next/navigation'

export default function ProductsPage() {
  const router = useRouter() // Error: useRouter only works in Client Components
  // ...
}
```

服务端组件中的替代方案：

**方案一：用`redirect()`函数做服务端重定向。**

```tsx
import { redirect } from 'next/navigation'

export default async function OldProductPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const product = await getProduct(id)
  
  if (!product) {
    redirect('/404')  // 服务端重定向
  }
  
  return <ProductDetail product={product} />
}
```

**方案二：将需要导航交互的部分拆成客户端子组件。**

```tsx
// app/products/page.tsx（服务端组件）
import ProductActions from './ProductActions'

export default async function ProductsPage() {
  const products = await getProducts()
  return (
    <div>
      <ProductList products={products} />
      <ProductActions />  {/* 客户端组件，内部可以使用useRouter */}
    </div>
  )
}
```

```tsx
// app/products/ProductActions.tsx
'use client'

import { useRouter } from 'next/navigation'

export default function ProductActions() {
  const router = useRouter()
  return (
    <button onClick={() => router.push('/products/new')}>
      新建商品
    </button>
  )
}
```

**方案三：使用`<Link>`组件替代编程式导航。** 如果导航目标在渲染时就能确定，直接用`Link`是最简单的方案，它在服务端组件中也能正常工作。

> 服务端组件没有`useRouter`，这不是限制而是设计。服务端组件关注渲染，客户端组件关注交互。把导航逻辑放到客户端子组件中，是最符合Next.js架构思想的写法。

## 4.7 404页面、路由重定向配置

### 4.7.1 自定义404：app/not-found.tsx

当用户访问一个不存在的路由时，Next.js会默认显示一个简陋的404页面。这个默认页面只有一行英文提示，对于面向用户的产品来说是完全不可接受的。通过创建`app/not-found.tsx`，你可以自定义404页面的UI，让错误页面也保持品牌一致性。一个好的404页面不仅能提升用户体验，还能引导用户回到有效路径，减少用户流失。

```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="not-found">
      <h1>404 - 页面不存在</h1>
      <p>你访问的页面可能已被移动或删除。</p>
      <Link href="/">返回首页</Link>
    </div>
  )
}
```

`not-found.tsx`可以放在任何路由段下。放在根目录`app/not-found.tsx`是全局404页面，放在子目录如`app/blog/not-found.tsx`则是blog模块的404页面。

还可以在页面或布局中主动触发404。在服务端组件中使用`notFound()`函数：

```tsx
import { notFound } from 'next/navigation'

export default async function ProductPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const product = await fetchProduct(id)
  
  if (!product) {
    notFound()  // 触发not-found.tsx渲染
  }
  
  return <ProductDetail product={product} />
}
```

`notFound()`会中断当前渲染流程，直接渲染最近的`not-found.tsx`。如果当前路由段没有定义`not-found.tsx`，会向上冒泡到根级别的`app/not-found.tsx`。

### 4.7.2 next.config.js中的redirects永久重定向

Next.js支持在`next.config.js`中配置路由重定向。这适合永久性的URL变更，比如域名迁移、路径重构、旧版API废弃后的页面跳转等场景。这种方式配置简单，且在Next.js服务启动时就生效，不需要额外的运行时逻辑。

```tsx
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  async redirects() {
    return [
      {
        source: '/old-blog/:slug',
        destination: '/blog/:slug',
        permanent: true,  // 301永久重定向
      },
      {
        source: '/docs',
        destination: '/documentation',
        permanent: true,
      },
      {
        source: '/old-shop/:category*',
        destination: '/shop/:category*',
        permanent: false,  // 302临时重定向
      },
    ]
  },
}

module.exports = nextConfig
```

配置项说明：

| 属性 | 说明 | 示例 |
|------|------|------|
| `source` | 匹配的源路径，支持参数 | `/old-blog/:slug` |
| `destination` | 重定向目标路径 | `/blog/:slug` |
| `permanent` | true=301永久，false=302临时 | `true` |
| `has` | 条件匹配（请求头、查询参数等） | `{ type: 'header', key: 'Host', value: 'old.com' }` |

`has`字段可以实现条件重定向，比如根据请求头中的Host判断是否需要重定向：

```tsx
{
  source: '/',
  destination: '/maintenance',
  permanent: false,
  has: [
    { type: 'header', key: 'x-maintenance-mode', value: 'true' }
  ]
}
```

### 4.7.3 middleware中的条件重定向

Middleware（中间件）允许你在请求到达页面之前执行逻辑，非常适合做认证检查和条件重定向。与`next.config.js`中的静态重定向不同，Middleware可以读取请求中的Cookie、请求头、查询参数等信息，根据运行时条件做出智能决策。这是Next.js提供的一个非常强大的运行时路由控制能力。

```tsx
// middleware.ts（放在项目根目录或app目录同级）
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  // 未登录用户访问dashboard，重定向到登录页
  if (pathname.startsWith('/dashboard') && !token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // 已登录用户访问登录页，重定向到dashboard
  if (pathname === '/login' && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/login'],
}
```

`matcher`配置指定了middleware只在匹配的路由上执行，避免在每个请求上都运行。这对性能很重要——不合理的matcher会导致所有请求都经过middleware处理。

Middleware重定向和`next.config.js`重定向的区别：

```
请求生命周期：

  客户端请求
      ↓
  next.config.js redirects    ← 最先执行，静态规则
      ↓
  Middleware                   ← 动态逻辑，可以读取请求信息
      ↓
  路由匹配 + 页面渲染
```

### 4.7.4 动态重定向：redirect()函数

在服务端组件或Server Action中，可以使用`redirect()`函数做动态重定向。与`next.config.js`的静态配置不同，`redirect()`可以根据运行时数据决定跳转目标。

```tsx
import { redirect } from 'next/navigation'

export default async function ProductPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const product = await fetchProduct(id)

  // 商品已下架，重定向到商品列表
  if (product.status === 'discontinued') {
    redirect('/products')
  }

  // 商品有新路径，重定向到新URL
  if (product.newSlug) {
    redirect(`/products/${product.newSlug}`)
  }

  return <ProductDetail product={product} />
}
```

`redirect()`的一个重要特性：它会在服务端返回一个重定向响应，浏览器会发起新的请求。这与`useRouter().push()`的客户端导航不同——`redirect()`会触发完整的服务端请求。

在Server Action中使用`redirect()`是表单提交后跳转的标准做法：

```tsx
'use server'

import { redirect } from 'next/navigation'

export async function createUser(formData: FormData) {
  const user = await createUserInDB(formData)
  
  // 创建成功后重定向到用户详情页
  redirect(`/users/${user.id}`)
}
```

### 4.7.5 重定向链的SEO处理

重定向不是无代价的。每一次重定向都会增加一个额外的HTTP（HyperText Transfer Protocol，超文本传输协议）请求往返，影响页面加载速度。对于SEO（Search Engine Optimization，搜索引擎优化）来说，重定向链（Redirect Chain）是需要特别注意的问题。搜索引擎爬虫遇到多级重定向时，会消耗爬取预算（Crawl Budget），甚至可能放弃跟踪后续跳转，导致目标页面不被收录。Google官方建议重定向跳数不要超过5次，但实际项目中最好控制在2次以内。

重定向链指的是多个重定向首尾相连的情况：

```
/old-url  →  /intermediate-url  →  /new-url
```

搜索引擎爬虫遇到重定向链时，可能会放弃跟踪后续的跳转，导致目标页面不被索引。解决重定向链的最佳实践是：**让每个旧URL直接指向最终目标URL**。

几种重定向方式的SEO影响对比：

| 方式 | 时机 | 对SEO的影响 |
|------|------|------------|
| `next.config.js` redirects (permanent) | 请求入口 | 301状态码，搜索引擎会更新索引 |
| Middleware redirect | 请求入口 | 可配置301或302，灵活度高 |
| `redirect()`函数 | 服务端渲染时 | 307临时重定向，搜索引擎不会更新索引 |
| `useRouter().replace()` | 客户端 | 不影响SEO（爬虫不执行JS重定向） |

对于需要搜索引擎更新索引的永久性URL变更，应该使用`next.config.js`的`permanent: true`配置。对于临时性的重定向（如维护页面、A/B测试），使用Middleware或`redirect()`函数。

一个实际的SEO优化技巧：定期审查重定向链，确保没有超过两跳的重定向。可以用Next.js的构建输出检查重定向配置，确保每个source只重定向一次。

另外，重定向配置的位置也很有讲究。如果是永久性的URL变更（比如域名迁移、路径重构），放在`next.config.js`中配置`permanent: true`，这样返回301状态码，搜索引擎会更新索引库中的URL。如果是临时性的跳转（比如活动页面下线后跳到活动列表），用Middleware返回302状态码，搜索引擎会保留原URL在索引中。如果是基于运行时数据的条件跳转（比如商品下架后跳到列表页），用`redirect()`函数返回307状态码，这是每次请求都会重新判断的动态行为。

理解了这些区别，你就能根据业务场景选择最合适的重定向方式，既满足功能需求又兼顾SEO效果。

## 4.8 本章小结与课后练习

### 本章核心知识点回顾

这一章我们系统学习了Next.js App Router的路由系统，涵盖以下核心内容：

第一，文件即路由的核心原理。App Router通过文件系统结构自动生成路由表，文件夹表示路由段，文件表示UI。特殊文件约定（page、layout、loading、error、not-found）各司其职，共同构建完整的路由体验。理解这套约定，就掌握了Next.js路由系统的60%。

第二，静态路由与动态路由。静态路由路径固定，适合构建时预渲染，性能最优。动态路由通过方括号语法`[id]`实现，配合`generateStaticParams`可以预生成动态页面。可选捕获路由`[[...slug]]`和捕获所有路由`[...slug]`提供了灵活的路由匹配能力，适用于文档系统、分类导航等场景。路由优先级规则确保了精确匹配优先于模糊匹配。

第三，布局系统。根布局是应用骨架，局部布局通过嵌套实现模块化。布局在导航时持久化不重新渲染，这是App Router的核心性能特性，也是与传统React Router最大的区别之一。`template.tsx`作为布局的补充，在需要每次导航都重新渲染时使用。布局与页面的组合渲染遵循从外到内的嵌套顺序，外层布局包裹内层布局，最内层是页面内容。

第四，路由分组。括号语法`(group)`让代码组织和URL结构解耦，支持为不同模块设置独立布局，是大型项目模块化的利器。分组可以嵌套使用，实现更细粒度的布局组合。

第五，导航机制。`Link`组件提供声明式导航并自动预取，`useRouter`提供编程式导航能力。服务端组件中用`redirect()`函数做重定向，客户端组件中用`useRouter`做交互式导航。预取机制是Next.js导航性能快于传统SPA（Single Page Application，单页应用）的关键原因。

第六，404和重定向。`not-found.tsx`自定义404页面，`next.config.js`配置静态重定向，Middleware实现条件重定向，`redirect()`函数实现动态重定向。不同方式适用于不同场景，SEO影响也各不相同。选择重定向方式时需要考虑永久性还是临时性、是否需要运行时条件判断、对搜索引擎索引的影响等因素。

### 课后练习

**练习一：搭建多模块路由结构**

创建一个包含以下路由结构的Next.js项目：
- 首页 `/`
- 营销模块：`/about`、`/pricing`、`/contact`
- 用户模块：`/profile`、`/settings`
- 博客模块：`/blog`（列表）、`/blog/[slug]`（详情）
- 使用路由分组为营销模块和用户模块分别设置不同布局

**练习二：实现动态路由与预生成**

创建一个商品详情页路由`/products/[id]`，要求：
- 使用`generateStaticParams`预生成前10个商品页面
- 在页面组件中获取商品数据并渲染
- 商品不存在时调用`notFound()`显示404页面
- 使用`dynamicParams = true`允许访问未预生成的商品

**练习三：实现认证重定向**

编写一个Middleware，实现以下逻辑：
- 未登录用户访问`/dashboard/*`时重定向到`/login?from=原路径`
- 已登录用户访问`/login`时重定向到`/dashboard`
- 其他路由正常通过
- 使用`matcher`配置确保Middleware只在必要路由上执行

**练习四：构建嵌套布局系统**

为一个电商网站设计路由和布局结构：
- 根布局：全局导航栏 + 页脚
- 商城布局：商品分类侧边栏
- 商品详情布局：商品信息 + 推荐区域
- 确保在商品间导航时，侧边栏状态保持不变

**练习五：导航与传参实战**

实现一个搜索功能：
- 搜索框使用`useRouter`编程式导航跳转到`/search?q=关键词`
- 搜索结果页读取查询参数并展示结果
- 点击搜索结果用`Link`跳转到详情页
- 详情页支持返回搜索结果页（`router.back()`）

以上就是Next.js路由系统的全部内容。路由是Next.js的基石，把这一章吃透，后面的渲染模式、数据获取等高级主题学起来会顺畅很多。

如果你觉得这篇文章对你有帮助，收藏起来方便以后查阅。有什么疑问或者踩了什么新坑，评论区见，怕浪猫会一一回复。

下一章我们将进入Next.js的四大渲染模式——CSR、SSR、SSG、ISR。这四个概念是Next.js最核心的能力，也是面试必考、实战必用的知识点。我们会从渲染模式的发展史讲起，深入每种模式的原理和适用场景，最后给出一份选型决策指南。不想错过的话，关注追更就对了。

系列进度 4/16

怕浪猫说：路由系统就像一座建筑的走廊和门牌号。文件结构是图纸，URL是门牌号，布局是走廊两边的装饰。图纸画得好，门牌标得清，走廊不重装——用户在其中穿行时就不会迷路，也不会觉得别扭。Next.js的路由设计，本质上就是用文件系统把这件复杂的事情变简单了。理解原理，尊重约定，剩下的交给框架就好。
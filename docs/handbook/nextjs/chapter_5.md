# 第5章 四大渲染模式：彻底吃透Next.js渲染机制

90%的Next.js性能问题，根源都在渲染模式选错了。用CSR做官网，SEO一片空白；用SSR做后台管理系统，服务器CPU天天飙红；用SSG做新闻站，内容更新滞后半天；用ISR做商品页，却不知道怎么触发按需更新。这四个概念你肯定都听过，但真正在项目里该用哪个、怎么切换、踩了坑怎么填，很多开发者其实是一知半解的。

我是怕浪猫，一个在前端渲染模式上踩过无数坑的全栈开发者。这篇文章我会把CSR、SSR、SSG、ISR四种渲染模式的原理、适用场景、实战陷阱全部拆解清楚，配上代码示例和对比表格，保证你看完就能在自己的项目里做出正确的选型决策。这一章是整个系列的核心章节之一，内容密度比较高，建议先收藏再细看。

## 5.1 前端渲染模式发展史与核心痛点

### 5.1.1 从静态HTML到SPA的演进

要理解Next.js的渲染模式，得先从前端渲染的演进史说起。这段历史不是废话，因为每种渲染模式都是为了解决前一个模式的痛点而诞生的。不理解这个演进过程，你就很难理解Next.js为什么要把四种渲染模式都放在一起。

最早期的Web就是纯静态HTML（HyperText Markup Language，超文本标记语言）。服务器上放一堆HTML文件，用户请求时直接返回，浏览器解析渲染。简单粗暴，但SEO（Search Engine Optimization，搜索引擎优化）友好到飞起——爬虫拿到的是完整的HTML文档，所有内容一览无余。那个年代的网站本质上就是一篇篇互相关联的电子文档，没有太多交互可言。

然后Ajax（Asynchronous JavaScript and XML，异步JavaScript和XML）来了，jQuery时代让页面可以局部刷新。用户点击按钮不再需要刷新整个页面，只需通过Ajax请求获取数据后更新页面中的某个区域。这极大地改善了用户体验，但页面主体的HTML仍然是服务端生成的。

真正的变革是SPA（Single Page Application，单页应用）的诞生。React、Vue、Angular这些框架把渲染逻辑从服务端搬到了客户端浏览器：服务器只返回一个空壳HTML和一堆JS（JavaScript）文件，浏览器下载JS后由JS负责构建整个DOM（Document Object Model，文档对象模型）树。从开发者的角度看，SPA带来了前所未有的开发体验——组件化、状态管理、路由跳转全部在客户端完成，开发效率大幅提升。但从性能和SEO的角度看，SPA埋下了两个巨大的隐患。

```
渲染演进时间线：

静态HTML时代       Ajax/jQuery时代        SPA时代              同构渲染时代
(1991-2005)        (2005-2014)           (2014-2020)          (2020-至今)
    |                  |                     |                     |
服务器返回HTML      局部刷新              客户端渲染              服务端+客户端
内容完整            减少全页刷新           体验流畅但SEO差         兼顾SEO和体验
零交互              半动态                 首屏白屏                按需选择渲染模式
SEO完美            SEO良好               SEO很差                SEO完美
```

### 5.1.2 CSR的SEO困境：搜索引擎爬虫看不到内容

SPA的核心问题是：初始HTML几乎是空的。这个空壳页面对于搜索引擎爬虫来说几乎没有任何可读的内容。来看一个典型的CSR页面返回的HTML长什么样：

```html
<!DOCTYPE html>
<html>
<head>
  <title>My App</title>
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <div id="root"></div>
  <script src="/static/js/bundle.js"></script>
</body>
</html>
```

`<div id="root"></div>`里面什么都没有。所有的页面内容都是JS下载执行后才动态生成的。对于用户来说，这没问题——浏览器能跑JS，用户最终能看到完整页面。但对于搜索引擎爬虫来说，这就是灾难。虽然Google爬虫已经能执行JS，但执行效率低、索引延迟大，而且百度等搜索引擎对JS渲染的支持更差。这意味着你的精心制作的页面内容，在搜索引擎眼里可能就是一张白纸。

除了SEO问题，CSR还有一个用户体验上的硬伤——首屏白屏。用户打开页面后，浏览器需要下载HTML、下载JS、执行JS、请求数据、渲染DOM，这一整套流程走完可能需要一到三秒甚至更长。在这段时间里，用户看到的是一个空白页面或者最多一个loading动画。在移动互联网时代，用户的耐心是以秒计算的，一秒的白屏就可能导致大量用户流失。

> CSR的本质是"先下载脚本，再生成内容"。这个顺序注定了SEO的先天不足——爬虫看到的是空壳，用户看到的是白屏。这不是Bug，是架构决定的必然结果。

### 5.1.3 SSR的性能代价：每次请求都走服务端

为了解决CSR的SEO和首屏白屏问题，SSR（Server-Side Rendering，服务端渲染）被推上舞台。思路很直接：既然客户端渲染爬虫看不到内容，那就让服务器在每次请求时把HTML生成好再返回。这样爬虫拿到的就是完整的HTML文档，用户打开页面也能立即看到内容。

但这带来了新的问题。传统的SSR（比如PHP、JSP时代）是同步阻塞的：每个请求来一次，服务器就要完整执行一遍数据获取和HTML模板拼接。用户并发量一上来，服务器CPU和内存就扛不住了。如果你的页面需要从数据库查询数据、调用外部API、拼接复杂模板，每个请求都要走一遍这个完整流程，服务器的压力可想而知。

```
SSR请求流程（每次请求都执行）：

用户请求 → 服务器接收 → 获取数据(200ms) → 拼接HTML(50ms) → 返回响应
              |                                    |
              +--- 每次请求都重复这个过程 -------------+

对比CSR：服务器只返回静态JS文件，零计算开销
对比SSG：构建时已生成HTML，运行时直接返回，零计算

并发场景下的服务器负载：
  100个并发请求 × 250ms/请求 = 25秒的服务器计算时间
  1000个并发请求 × 250ms/请求 = 250秒的服务器计算时间
  需要水平扩展才能扛住，成本直线上升
```

SSR还有一个容易被忽略的成本——水合（Hydration）。浏览器拿到服务端返回的HTML后，不仅要显示内容，还要下载JS并把事件监听器附加到DOM节点上，让页面变得可交互。这个过程需要浏览器执行大量的JS代码，在低端设备上可能需要几百毫秒甚至更久。这意味着即使用户看到了内容，页面可能还是不可交互的，这种"看得见但点不了"的体验同样不好。

### 5.1.4 同构渲染的概念与Next.js的解法

Next.js提出的不是某一种渲染模式，而是"同构渲染"（Isomorphic Rendering）——同一个项目里，不同页面可以用不同的渲染模式。首页用SSG静态生成，后台管理用CSR客户端渲染，商品页用ISR增量更新，个性化推荐用SSR服务端渲染。这些页面共享同一套组件库、同一套路由系统、同一套构建工具，只是渲染时机不同。

这是Next.js最核心的设计哲学：**渲染模式不是非此即彼的选择，而是按需组合的工具箱**。你在Pages Router时代通过`getStaticProps`、`getServerSideProps`等函数来选择渲染模式，而在App Router时代，渲染模式的选择变得更加智能和隐式——框架会根据你使用的API自动推断渲染模式。这个设计大大降低了心智负担，你不需要在每种模式之间做显式切换，只需要专注于写好组件逻辑，框架会帮你选择最优的渲染策略。

> 同构渲染的精髓不在于"服务端渲染什么"，而在于"何时渲染什么"。构建时、请求时、客户端运行时——三个时间点，四种排列组合，覆盖了几乎所有Web应用场景。Next.js不是让你在四种模式中选一个，而是让你在每个路由上都能选最合适的那个。

### 5.1.5 渲染模式演进的驱动力：性能与SEO的平衡

回头看看这条演进路线，每一步都在解决同一个矛盾：**首屏性能与SEO的平衡**。静态HTML时代SEO完美但无交互能力；CSR交互能力强但SEO和首屏体验差；SSR解决了SEO和首屏但服务器扛不住；SSG解决了服务器负载但内容不能实时更新；ISR融合了SSG和SSR的优点，在性能和时效性之间找到了平衡点。

| 渲染模式 | 首屏速度 | SEO支持 | 服务器负载 | 内容实时性 |
|---------|---------|---------|-----------|-----------|
| 静态HTML | 最快 | 最好 | 最低 | 最差（需重新部署） |
| CSR(SPA) | 最慢 | 最差 | 最低 | 最好（实时获取） |
| SSR | 中等 | 好 | 最高 | 最好（实时获取） |
| SSG | 最快 | 最好 | 最低 | 差（需重新构建） |
| ISR | 快 | 好 | 低 | 较好（定时/按需更新） |

Next.js的四大渲染模式正是沿着这条演进线设计出来的。理解了这个驱动力，后面的每种模式你都能从"它解决了什么问题"的角度去理解，而不是死记硬背概念。每种模式都有它存在的理由，也有它的局限性，关键是理解背后的权衡逻辑。

## 5.2 客户端渲染CSR原理与适用场景

### 5.2.1 CSR的完整渲染流程

CSR（Client-Side Rendering，客户端渲染）是大多数React开发者最熟悉的模式。它的核心流程是：浏览器先下载一个几乎空白的HTML页面，然后下载并执行JS bundle，JS执行时获取数据并构建DOM树，最终把内容渲染到页面上。整个过程完全发生在浏览器端，服务器只负责提供静态资源。

```
CSR渲染时间线：

TTFB ──── 下载HTML ──── 下载JS ──── 执行JS ──── 获取数据 ──── 渲染DOM
 |           |              |           |            |             |
快           快            慢(大文件)   慢(解析执行)   慢(网络请求)   最终首屏
                                                         ↑
                                                    FCP(首次内容绘制) 在这里
```

关键指标：
- TTFB（Time To First Byte，首字节时间）：极快，因为服务器只返回小HTML
- FCP（First Contentful Paint，首次内容绘制）：很慢，要等JS下载执行+数据获取
- TTI（Time To Interactive，可交互时间）：最慢，所有JS加载完毕后才能交互

在弱网环境下，这个过程会被进一步放大。假设用户在3G网络下访问，JS bundle有300KB，下载可能需要2秒以上。加上JS解析执行和数据请求的时间，用户可能要等3到5秒才能看到页面内容。这个体验在移动端是不可接受的。

### 5.2.2 CSR在Next.js中的实现

在App Router中，CSR通过`'use client'`指令来声明。任何标记了`'use client'`的组件都会被作为客户端组件处理，在服务端只渲染初始HTML（如果可以的话），实际的内容渲染和交互都在浏览器端完成。

```tsx
'use client'

import { useState, useEffect } from 'react'

export default function UserDashboard() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 数据获取在客户端完成
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data)
        setLoading(false)
      })
  }, [])

  if (loading) return <div>加载中...</div>

  return (
    <ul>
      {users.map(u => <li key={u.id}>{u.name}</li>)}
    </ul>
  )
}
```

注意几个要点：`'use client'`必须写在文件第一行；`useEffect`里的逻辑只在浏览器执行，服务端渲染时会跳过；初始渲染时`users`为空数组，所以首屏看到的是"加载中"这个占位文本。当JS在浏览器执行后，`useEffect`触发数据请求，拿到数据后更新state触发重新渲染，用户才看到实际内容。

这里有一个微妙的区别需要理解：客户端组件在服务端也会被预渲染（pre-render）。也就是说，服务端会执行组件的初始渲染逻辑——`users`为空数组时渲染出"加载中"的HTML。这个HTML会随响应返回给浏览器，所以用户首屏看到的是"加载中"，而不是完全的空白。这比纯SPA的白屏要好一些，但SEO效果仍然不理想，因为搜索引擎爬虫拿到的是"加载中"而非实际内容。

### 5.2.3 CSR的性能特征

CSR最大的特点是：**服务器几乎不干活，所有重活都丢给浏览器**。这带来一个矛盾的性能画像——TTFB极快但FCP极慢。服务器返回静态HTML只需要几毫秒，但用户真正看到内容却要等JS下载、执行、数据获取都完成之后。

```
性能特征对比：

CSR:
  服务器: [HTML空壳] → 完成 (1ms)
  浏览器: [等待JS下载 800ms] → [执行JS 200ms] → [请求数据 300ms] → [渲染 50ms]
  首屏总耗时: ~1350ms

SSR:
  服务器: [获取数据 300ms] → [生成HTML 100ms] → [返回]
  浏览器: [立即显示内容] → [下载JS] → [水合 200ms]
  首屏总耗时: ~400ms (用户更早看到内容)
```

CSR的TTFB通常在几毫秒级别，因为服务器只是返回一个静态HTML文件，几乎零计算。但用户实际看到内容的时间（FCP）可能要等1到3秒，取决于JS bundle大小和网络状况。在弱网环境下，这个问题会被放大——用户盯着白屏等待JS下载的体验非常差。而且如果JS bundle特别大（比如用了重型UI库或者图表库），解析和执行的时间也会显著增加。低端手机的CPU性能有限，解析执行几百KB的JS可能需要数百毫秒，这进一步拉长了首屏时间。这也是为什么移动端性能优化中，减少JS体积往往比减少图片体积更有效——图片可以懒加载，但JS必须解析执行后页面才能可交互。

### 5.2.4 适用场景

CSR不是"差"的渲染模式，只是它有特定的适用场景。很多开发者一提到CSR就觉得"落后"，这是不对的。在合适的场景下，CSR反而是最优选择。

**后台管理系统**是CSR的最佳战场。这类应用通常在登录后才访问，不需要SEO；交互密集，有大量的状态管理和实时更新需求；用户群体固定，可以在内网环境下使用，网络条件可控。后台管理系统的页面通常有复杂的表单交互、数据筛选、拖拽排序等功能，这些交互逻辑全在客户端运行，用SSR反而会让水合过程变得沉重而毫无收益。

**交互密集型应用**也适合CSR。比如在线编辑器、数据可视化面板、实时协作工具等，这些应用的核心逻辑都在客户端，服务端渲染的HTML几乎立刻被客户端JS覆盖，做SSR纯属浪费服务器资源。像Figma、Google Docs这类应用，核心渲染逻辑完全在客户端，SSR对它们没有意义。

**内部工具和Dashboard**同样如此。不需要SEO，不需要首屏极致优化，开发效率反而是第一优先级。这类应用用户量小、访问频率低，用CSR可以省去服务端渲染的成本，开发也最简单。

> `'use client'`不是越多越好。每多一个客户端组件，用户的浏览器就多下载一份JS。把客户端边界尽量往下推，让服务端组件承担更多的静态渲染工作，是App Router性能优化的第一课。

### 5.2.5 CSR的常见陷阱与优化建议

**陷阱一：不必要的使用`'use client'`。** 这是App Router中最常见的错误。很多从Pages Router迁过来的开发者习惯在每个组件顶部加`'use client'`，这会让本可以服务端渲染的组件变成客户端组件，增加JS bundle体积。正确做法是只在需要客户端API（useState、useEffect、事件处理等）的组件上加`'use client'`，且尽量把这个边界往下推，推到叶子组件级别。

```tsx
// 不推荐：整个页面变成客户端组件
'use client'
export default function Page() {
  return (
    <div>
      <StaticHeader />      {/* 不需要客户端渲染 */}
      <StaticSidebar />     {/* 不需要客户端渲染 */}
      <InteractiveChart />  {/* 只有这个需要客户端渲染 */}
    </div>
  )
}

// 推荐：只让需要交互的组件成为客户端组件
import StaticHeader from './StaticHeader'
import StaticSidebar from './StaticSidebar'
import InteractiveChart from './InteractiveChart'

export default function Page() {
  // 这些组件在服务端渲染，不增加客户端JS
  // InteractiveChart内部自己声明'use client'
  return (
    <div>
      <StaticHeader />
      <StaticSidebar />
      <InteractiveChart />
    </div>
  )
}
```

**陷阱二：首屏白屏体验差。** 解决方案是添加骨架屏或loading状态，让用户在JS加载期间看到结构占位而不是空白。Next.js的`loading.tsx`文件可以自动包裹Suspense边界，提供路由级别的loading状态。

**陷阱三：数据获取瀑布问题。** CSR页面容易产生瀑布式请求——父组件获取数据后渲染子组件，子组件再获取自己的数据，层层嵌套导致请求串行执行。用`Promise.all`并行获取或提升数据获取层级到路由入口可以缓解这个问题。另外，React Query、SWR这类数据获取库内置了请求去重和缓存机制，能自动避免重复请求。

**陷阱四：SEO补救措施治标不治本。** 有人尝试用预渲染（prerender）插件或者prerender.io这类服务来弥补CSR的SEO缺陷，原理是在构建时用无头浏览器渲染页面生成静态HTML。这确实能改善SEO，但构建时间会大幅增加，而且对于动态内容仍然无法实时更新。如果SEO真的很重要，直接用SSR或SSG才是正道，不要在CSR上打补丁。

## 5.3 服务端渲染SSR实战与数据获取

### 5.3.1 SSR渲染流程

SSR（Server-Side Rendering，服务端渲染）的核心是：服务器在收到请求时，执行组件代码获取数据并生成完整的HTML，然后返回给浏览器。浏览器拿到HTML后立即显示内容，同时后台下载JS进行"水合"（Hydration），让页面变得可交互。整个流程分为请求阶段和水合阶段两步。

```
SSR完整流程：

1. 请求阶段
   浏览器 ──请求──→ 服务器
   服务器 → 执行Server Component → 获取数据 → 生成HTML字符串
   服务器 ──HTML──→ 浏览器

2. 水合阶段（Hydration）
   浏览器显示HTML（用户已能看到内容）
   浏览器下载JS → 执行JS → 将事件监听器附加到DOM节点
   页面变为可交互状态

关键区别：SSR的HTML是"有内容"的，CSR的HTML是"空壳"
```

水合是SSR中最关键也最容易出问题的环节。React的水合要求服务端生成的HTML和客户端首次渲染的HTML完全一致，否则React会发出警告甚至丢弃服务端HTML重新渲染整个子树。这个一致性要求是SSR复杂度的核心来源——你的代码必须能在两个不同的运行环境（Node.js和浏览器）中产生完全相同的渲染结果。

水合的过程中还有一个性能陷阱。React的水合是"全量水合"——即使页面中只有一小部分是可交互的，React也需要把整个页面的JS都下载并执行一遍，把事件监听器附加到所有需要交互的DOM节点上。对于内容密集但交互较少的页面（比如新闻文章页），这个水合过程的大部分工作都是浪费的。React 18引入的Selective Hydration（选择性水合）部分缓解了这个问题，但根本性的解决要靠Server Components减少客户端JS体积。

### 5.3.2 App Router中的SSR

App Router让SSR变得异常简单。在Server Component中，你可以直接使用`async/await`获取数据，不需要像Pages Router那样写`getServerSideProps`这种特殊的导出函数。组件本身就是一个普通的异步函数，数据获取和渲染逻辑写在一起，清晰直观。

```tsx
// app/dashboard/page.tsx
// 这是一个Server Component，默认SSR

export default async function DashboardPage() {
  // 直接await，在服务端执行
  const res = await fetch('https://api.example.com/stats', {
    cache: 'no-store'  // 每次请求都获取最新数据
  })
  const stats = await res.json()

  return (
    <main>
      <h1>数据概览</h1>
      <p>总用户数：{stats.totalUsers}</p>
      <p>今日活跃：{stats.activeToday}</p>
    </main>
  )
}
```

这段代码的执行位置是服务端。`fetch`在服务端执行，数据获取完成后，React把组件渲染成HTML字符串返回给浏览器。浏览器收到的HTML已经包含了`<p>总用户数：12345</p>`这样的内容。用户打开页面的瞬间就能看到数据，不需要等JS下载执行。而`cache: 'no-store'`这个配置告诉Next.js不要缓存这个请求的结果，每次请求都重新获取，保证数据的实时性。

与Pages Router的`getServerSideProps`对比，App Router的优势是显而易见的。你不再需要在组件外部写一个特殊函数获取数据，然后通过props传递给组件。数据和渲染逻辑在一起，代码更内聚，可读性更好。而且Server Component可以直接访问数据库、文件系统等服务端资源，不需要额外搭建API层。这在全栈开发中非常方便，你可以在组件中直接查询数据库，不需要在前端和数据库之间再加一层API服务。当然，这也要注意安全边界——不要在Server Component中暴露敏感的数据库查询逻辑，应该通过独立的Service层封装。

### 5.3.3 动态渲染：cookies()、headers()触发按需渲染

App Router有一个重要特性：**动态函数自动触发动态渲染**。当你在组件中调用了`cookies()`、`headers()`、`searchParams`等动态函数时，Next.js会自动将该路由从静态生成切换为服务端渲染。这个设计让你不需要显式声明渲染模式，框架会根据你的代码自动做出正确选择。

```tsx
import { cookies, headers } from 'next/headers'

export default async function ProfilePage() {
  // 读取cookie触发动态渲染
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')

  // 读取请求头也触发动态渲染
  const headerStore = await headers()
  const userAgent = headerStore.get('user-agent')

  const res = await fetch('https://api.example.com/profile', {
    headers: { Authorization: `Bearer ${token?.value}` }
  })
  const profile = await res.json()

  return (
    <div>
      <h1>{profile.name}的个人页</h1>
      <p>登录设备：{userAgent}</p>
    </div>
  )
}
```

这个设计的精妙之处在于：你不需要显式声明"我要用SSR"。Next.js会根据你使用的API自动推断渲染模式。用了`cookies()`或`headers()`——说明这个页面的内容依赖于请求上下文，每个用户的请求可能返回不同的内容，必须每次请求都重新渲染。没用这些动态函数——页面就可以在构建时静态生成，因为所有请求看到的都是同样的内容。

```
渲染模式自动推断规则：

组件中使用了...                    → 渲染模式
─────────────────────────────────────────────
cookies() / headers() / searchParams → SSR（动态渲染）
fetch({ cache: 'no-store' })         → SSR（动态渲染）
generateStaticParams + 无动态函数     → SSG（静态生成）
以上都没有                            → SSG（默认静态）
revalidate: N                        → ISR（增量静态再生）
```

需要注意的是，`searchParams`在App Router中也是一个动态API。当你的页面组件接收了`searchParams`参数时，这个页面就变成了动态渲染。因为查询参数是URL（Uniform Resource Locator，统一资源定位符）的一部分，每个请求可能不同，所以必须在请求时渲染。

### 5.3.4 流式渲染：Suspense边界与partial hydration

流式渲染（Streaming）是App Router的一个重量级特性，它从根本上改变了SSR的工作方式。传统的SSR是"全有或全无"——服务器必须完成整个页面的数据获取和HTML生成后才能返回第一个字节。如果页面中有某个组件的数据获取特别慢，整个页面都会被阻塞。流式渲染允许服务器把页面拆分成多个块，先返回已准备好的部分，未完成的部分用Suspense占位，数据就绪后再流式推送到浏览器。

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'

export default function DashboardPage() {
  return (
    <div>
      <h1>仪表盘</h1>
      
      <UserInfo />
      
      {/* 这个组件数据获取慢，用Suspense包裹 */}
      <Suspense fallback={<div>加载图表中...</div>}>
        <SlowChart />
      </Suspense>

      <Suspense fallback={<div>加载列表中...</div>}>
        <SlowList />
      </Suspense>
    </div>
  )
}

async function SlowChart() {
  const data = await fetch('https://api.example.com/chart', {
    cache: 'no-store'
  }).then(r => r.json())
  return <Chart data={data} />
}
```

```
流式渲染时间线对比：

传统SSR:
  T=0    请求到达
  T=300ms UserInfo就绪
  T=800ms SlowChart就绪
  T=1200ms SlowList就绪
  T=1200ms ──→ 返回完整HTML（用户等了1.2秒才看到任何内容）

流式渲染:
  T=0    请求到达
  T=50ms ──→ 流式返回HTML骨架 + UserInfo（用户立即看到部分内容）
  T=800ms ──→ 流式推送SlowChart的HTML
  T=1200ms ──→ 流式推送SlowList的HTML
  用户在50ms就看到了内容，体验大幅提升
```

流式渲染的核心价值是把"等待时间"变成了"渐进展示时间"。用户不需要等所有数据都就绪才看到内容，而是随着数据陆续就绪逐步看到更多内容。这在感知性能上的提升是巨大的——50毫秒内看到骨架屏和标题，远比等1.2秒后突然看到完整页面的体验好得多。

Suspense边界的放置位置很关键。太粗的边界（整个页面一个Suspense）失去了流式渲染的意义，太细的边界（每个元素都包一层）会让HTML碎片化影响可读性。一般建议按照数据获取的独立性来划分——每个有独立数据请求的组件用一个Suspense包裹。

### 5.3.5 SSR实战踩坑

**坑一：window/document未定义。** 这是最经典的SSR坑，几乎每个从CSR转SSR的开发者都踩过。在Server Component中访问`window`、`document`、`localStorage`等浏览器API会直接报错，因为这些在Node.js环境中根本不存在。Node.js运行时没有DOM，没有BOM（Browser Object Model，浏览器对象模型），只有V8引擎和核心模块。

```tsx
// 错误写法：Server Component中直接使用window
export default function Page() {
  const width = window.innerWidth  // ReferenceError: window is not defined
  return <div>屏幕宽度：{width}</div>
}

// 正确写法：用客户端组件 + useEffect
'use client'
import { useState, useEffect } from 'react'

export default function ViewportInfo() {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    setWidth(window.innerWidth)
  }, [])
  return <div>屏幕宽度：{width}</div>
}
```

**坑二：序列化失败。** Server Component和Client Component之间传递的props必须可序列化。这意味着函数、Date对象、Map/Set、Class实例、React元素等都不能直接传。Next.js在编译时会检查并报错，但有些运行时动态生成的值可能逃过编译检查，在运行时报错。

```tsx
// 错误：传递不可序列化的数据
export default async function Page() {
  const data = new Map([['key', 'value']])
  const date = new Date()
  return <ClientComp data={data} date={date} />
}

// 正确：转换为可序列化格式
export default async function Page() {
  const data = { key: 'value' }       // 用普通对象
  const dateStr = new Date().toISOString()  // 转为字符串
  return <ClientComp data={data} dateStr={dateStr} />
}
```

**坑三：水合不匹配。** 服务端和客户端渲染结果不一致会导致React水合警告。常见原因是用了`Date.now()`、`Math.random()`或`new Date()`这类在服务端和客户端返回不同值的API。服务端渲染时的时间是T1，客户端水合时的时间是T2，两者不一致就会报hydration mismatch警告。解决方法是把这类时间相关的逻辑放到`useEffect`中执行，确保只在客户端运行。

> SSR的坑十有八九出在"服务端和客户端的环境差异"上。记住一个原则：Server Component里只做数据获取和静态渲染，任何涉及浏览器环境的操作都丢给Client Component。这条线划清楚了，大部分水合问题就不会找上你。

## 5.4 静态站点生成SSG与预渲染优势

### 5.4.1 SSG核心原理

SSG（Static Site Generation，静态站点生成）的思路是：**在构建时（build time）就把所有HTML页面生成好，部署到CDN（Content Delivery Network，内容分发网络）上，用户请求时直接返回静态文件**。这是性能最优的渲染模式，也是Next.js的默认渲染模式。

```
SSG工作流程：

构建阶段（Build Time）：
  开发者执行 next build
    → Next.js遍历所有路由
    → 对每个页面获取数据、生成HTML
    → 输出到 .next/server/app/ 目录

运行阶段（Runtime）：
  用户请求 → CDN边缘节点 → 返回预生成的HTML
  服务器零计算，直接返回静态文件

对比SSR：
  SSR: 用户请求 → 服务器计算(200ms) → 返回HTML
  SSG: 用户请求 → CDN返回(< 10ms) → 完成
```

SSG的核心优势是"一次构建，无限分发"。构建完成后，所有页面都是静态HTML文件，可以部署到任何CDN上。用户无论在全球哪个角落，都能从最近的CDN节点获取到内容，延迟极低。Cloudflare Pages、Vercel Edge Network、AWS CloudFront等平台都支持静态文件部署，配合CDN可以做到全球毫秒级响应。

### 5.4.2 默认静态：App Router的自动SSG

App Router有一个重要设计：**默认情况下，所有不带动态函数的页面都是静态生成的**。这意味着你不需要任何特殊配置，写一个普通的组件就是SSG。这个设计体现了Next.js"默认最优"的理念——性能最好的渲染模式作为默认选项，需要动态性时再显式开启。

```tsx
// app/about/page.tsx
// 这个页面在构建时自动静态生成

export default async function AboutPage() {
  // 这个fetch在构建时执行，结果会被缓存
  const res = await fetch('https://api.example.com/about')
  const data = await res.json()

  return (
    <div>
      <h1>{data.title}</h1>
      <p>{data.description}</p>
    </div>
  )
}
```

构建时，Next.js会执行这个组件，获取数据，生成HTML文件。部署后，用户访问`/about`时直接拿到这个预生成的HTML。你可以通过构建日志确认渲染模式：

```
Route (app)                              Size     First Load JS
┌ ○ /                                    5.3 kB        89.4 kB
├ ○ /about                               2.1 kB        86.2 kB
├ ƒ /dashboard/[id]                      3.5 kB        88.1 kB
└ ● /blog/[slug]                         4.2 kB        90.3 kB

○  (Static)  -  SSG：构建时静态生成
●  (Static with ISR)  -  ISR：静态生成 + 增量再生
ƒ  (Dynamic)  -  SSR：服务端动态渲染
```

构建日志中的符号让你一目了然每个路由用了什么渲染模式。如果你想确认某个页面到底是静态还是动态，看构建日志是最直接的方式。

### 5.4.3 generateStaticParams：预生成动态路由页面

对于动态路由（如`/blog/[slug]`），SSG需要在构建时知道所有可能的参数值。`generateStaticParams`函数就是干这个的——它告诉Next.js构建时需要为哪些参数值生成静态页面。

```tsx
// app/blog/[slug]/page.tsx

// 构建时生成所有可能的slug参数
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts')
    .then(r => r.json())
  
  return posts.map((post) => ({
    slug: post.slug,
  }))
}

// 构建时获取每个文章的数据
export default async function BlogPost({ 
  params 
}: { 
  params: { slug: string } 
}) {
  const post = await fetch(
    `https://api.example.com/posts/${params.slug}`
  ).then(r => r.json())

  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  )
}
```

构建时，Next.js会先调用`generateStaticParams`获取所有slug值，然后对每个slug执行组件渲染，生成对应的静态HTML文件。如果博客有100篇文章，构建时就会生成100个HTML文件。部署后，访问任何一篇都能立即返回预生成的HTML。

这里有一个重要的配置项`dynamicParams`。默认值为`true`，意味着如果用户访问了一个未在`generateStaticParams`中列出的slug，Next.js会在运行时按需生成这个页面（首次生成后会缓存，后续请求直接返回静态HTML）。如果设为`false`，未列出的路径会返回404，彻底变成纯静态站点。对于内容可控的文档站或博客，设为`false`更安全；对于用户生成内容的平台，保持`true`可以自动覆盖新增内容。

### 5.4.4 SSG的性能优势

SSG的性能几乎是所有渲染模式中最优的。因为HTML在构建时已经生成好了，运行时不需要任何服务器计算，CDN直接返回静态文件。这意味着无论流量多大，服务器都不会有压力。

```
各模式运行时服务器开销对比：

SSG:  请求 → CDN返回HTML → 完成
      服务器CPU: 0%  |  耗时: ~10ms

ISR:  请求 → 检查缓存 → (过期?) → 返回旧+后台更新
      服务器CPU: 极低 |  耗时: ~10ms

SSR:  请求 → 获取数据 → 生成HTML → 返回
      服务器CPU: 高  |  耗时: 200-1000ms

CSR:  请求 → 返回空HTML → (客户端下载JS+数据)
      服务器CPU: 极低 |  首屏耗时: 1-3s
```

SSG的TTFB在10毫秒以内（CDN边缘节点返回），FCP几乎等于TTFB（HTML已包含内容），服务器零计算开销。对于流量大的网站，SSG能节省大量的服务器成本。一篇热门博客可能有上百万次访问，如果用SSR每次都要服务器计算，成本惊人；用SSG则只需要一次构建，CDN搞定所有请求。

### 5.4.5 SSG的局限

SSG的硬伤是**内容更新需要重新构建**。如果你的博客发布了新文章，或者商品价格变了，你必须重新`next build`并重新部署。对于内容更新频率低的网站（博客、文档站、官网），这不是问题——每周或者每天构建一次完全够用。但对于内容频繁更新的应用（新闻、电商库存、社交动态），每次更新都重新构建是不现实的。

构建时间也是一个需要考虑的因素。如果你的网站有上千个页面，每次构建可能需要好几分钟甚至更久。虽然Next.js支持增量构建（只重新生成变更的页面），但构建仍然是一个需要规划和优化的过程。大型项目的构建时间优化是一个独立的话题，涉及代码分割、依赖优化、构建缓存等多个方面。在实际项目中，怕浪猫建议把构建时间控制在5分钟以内，超过这个时间会严重影响CI/CD（Continuous Integration/Continuous Deployment，持续集成/持续部署）流程的效率。

```
SSG适用性判断：

内容更新频率        构建频率要求        SSG适用性
──────────────────────────────────────────
每年更新几次         每次手动构建        非常适合
每周更新1-2篇        每周构建一次         适合
每天更新多次          每天构建             勉强（考虑ISR）
每分钟都在更新        持续构建             不适合（用SSR/ISR）
```

> SSG的哲学是"以构建时间换运行时性能"。构建一次可能要几分钟甚至几十分钟，但换来的是运行时的极致速度。这个交易值不值，取决于你的内容更新频率和流量规模。对于高流量低更新频率的网站，SSG是性价比最高的选择。

## 5.5 增量静态再生ISR：动态内容最优方案

### 5.5.1 ISR原理

ISR（Incremental Static Regeneration，增量静态再生）是Next.js的独创技术，它解决了SSG"更新需要重新构建"的问题。ISR的核心思路是：**静态页面 + 后台定时重新生成**。它保留了SSG的CDN分发优势，又获得了内容自动更新的能力，是四种渲染模式中性价比最高的一种。

```
ISR工作流程：

1. 首次构建：和SSG一样，构建时生成静态HTML
2. 首次请求：返回预生成的静态HTML
3. 后续请求：
   - 如果在revalidate时间内 → 返回缓存的静态HTML（毫秒级）
   - 如果超过revalidate时间 → 先返回旧HTML，后台静默重新生成
   - 下一次请求 → 返回新生成的HTML

关键：用户永远不会等待重新生成，旧页面立即返回，新页面后台更新
```

ISR的精妙之处在于"后台再生"机制，学术上叫做stale-while-revalidate策略。当缓存过期时，用户不会被阻塞等待新页面生成，而是立即拿到旧版本的内容，同时服务器在后台异步生成新版本。生成完成后，后续请求就能拿到新内容。这种策略让用户始终获得快速响应，同时内容也能定期更新。对于大多数内容型网站来说，几秒钟到几分钟的内容延迟是完全可接受的。

### 5.5.2 revalidate配置

在App Router中，ISR的配置非常简单，只需要在`fetch`中设置`revalidate`参数或在路由段配置中指定`revalidate`值：

```tsx
// 方式一：通过fetch的next.revalidate配置
export default async function ProductPage({ params }) {
  const res = await fetch(
    `https://api.example.com/products/${params.id}`,
    { next: { revalidate: 60 } }  // 60秒后允许重新生成
  )
  const product = await res.json()

  return (
    <div>
      <h1>{product.name}</h1>
      <p>价格：￥{product.price}</p>
    </div>
  )
}

// 方式二：通过路由段配置
export const revalidate = 3600  // 1小时重新生成一次

export default async function BlogPost({ params }) {
  const post = await fetch(
    `https://api.example.com/posts/${params.slug}`
  ).then(r => r.json())
  
  return <article><h1>{post.title}</h1></article>
}
```

`revalidate`的值是秒数。设置为60表示每60秒最多重新生成一次。在这60秒内，所有请求都返回缓存的静态HTML。第61秒的请求触发后台重新生成，但该请求本身仍然拿到旧版本——这就是stale-while-revalidate的精髓，用户永远不用等。

```
revalidate时间线示例（revalidate=60s）：

T=0s    构建完成，生成HTML v1
T=10s   请求 → 返回 v1（缓存有效）
T=30s   请求 → 返回 v1（缓存有效）
T=61s   请求 → 返回 v1（触发后台更新）→ 后台生成 v2
T=62s   请求 → 返回 v2（新版本已就绪）
T=120s  请求 → 返回 v2（缓存有效）
T=121s  请求 → 返回 v2（触发后台更新）→ 后台生成 v3
```

revalidate的值需要根据业务需求来定。太短（如1秒）会让服务器频繁重新生成，失去ISR的性能优势；太长（如24小时）可能让内容更新不够及时。一般来说，新闻类内容5到10分钟比较合适，商品信息1到5分钟，博客1小时甚至更长。

### 5.5.3 on-demand ISR：按需重新生成

定时重新生成并不总是最优方案。如果你的商品价格变了，你不想等revalidate到期，而是希望立即更新。Next.js提供了按需ISR（On-demand Revalidation），通过API路由手动触发重新生成。这是通过`revalidatePath`和`revalidateTag`两个函数实现的。

```tsx
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const secret = request.headers.get('x-secret')

  // 安全校验
  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (body.type === 'path') {
    // 重新生成指定路径
    revalidatePath(body.path)
  } else if (body.type === 'tag') {
    // 重新生成带有特定tag的所有缓存
    revalidateTag(body.tag)
  }

  return NextResponse.json({ revalidated: true })
}
```

当CMS（Content Management System，内容管理系统）中发布新文章时，调用这个API就能立即触发对应页面的重新生成：

```bash
# CMS发布新文章后调用
curl -X POST https://your-app.com/api/revalidate \
  -H "Content-Type: application/json" \
  -H "x-secret: your-secret-key" \
  -d '{"type":"path","path":"/blog/new-article"}'
```

`revalidateTag`更强大——你可以给多个fetch打上同一个tag，一次调用全部失效。比如给所有商品相关的fetch都打上`'products'`标签，当商品数据批量更新时，一次`revalidateTag('products')`就能让所有商品页同时重新生成，不需要逐个路径调用。

```tsx
// 给fetch打tag
const res = await fetch('https://api.example.com/products/1', {
  next: { revalidate: 3600, tags: ['products'] }
})

// 当产品数据变更时，一次性失效所有带'products' tag的缓存
revalidateTag('products')
```

### 5.5.4 ISR vs SSR vs SSG：三种模式对比

| 维度 | SSG | ISR | SSR |
|-----|-----|-----|-----|
| 生成时机 | 构建时 | 构建时+定时/按需更新 | 每次请求 |
| 内容新鲜度 | 构建时快照 | 接近实时（可配置） | 完全实时 |
| 服务器负载 | 零 | 极低 | 高 |
| 首屏速度 | 极快(CDN) | 极快(CDN) | 中等(服务器生成) |
| SEO | 完美 | 完美 | 完美 |
| 适用场景 | 文档/博客 | 新闻/电商 | 个性化内容 |
| 构建次数 | 一次 | 一次 | 无需构建 |

> ISR是SSG和SSR之间的"甜点区"。它保留了SSG的CDN分发优势，又获得了接近SSR的内容时效性。对于大多数内容型网站，ISR是比SSG和SSR更优的选择。怕浪猫在实际项目中，但凡能用ISR的场景，都不会选SSR。

### 5.5.5 ISR实战场景

**新闻网站**：文章页用ISR，revalidate设置为5到10分钟。读者访问时拿到的是CDN缓存的静态页面，速度极快；新文章发布后5分钟内，所有读者都能看到更新。突发新闻可以用on-demand ISR立即推送，不用等定时触发。

**博客系统**：文章内容变更频率低，revalidate可以设置为1小时甚至1天。发布新文章或编辑旧文时通过CMS webhook触发on-demand重新生成。这样既保证了内容更新的及时性，又不会给服务器带来额外负担。

**电商商品页**：商品基本信息（标题、描述、图片）用ISR，revalidate设置为1到5分钟。价格和库存等高频变更数据可以单独通过客户端实时获取，与ISR生成的静态内容叠加展示。这种混合策略既保证了页面的首屏速度（ISR静态HTML秒级返回），又保证了关键业务数据的实时性（客户端实时获取价格库存）。

```tsx
// 电商商品页的混合策略示例
export const revalidate = 300  // 5分钟ISR

export default async function ProductPage({ params }) {
  // ISR：商品基本信息（低频变更）
  const product = await fetch(
    `https://api.example.com/products/${params.id}`,
    { next: { revalidate: 300 } }
  ).then(r => r.json())

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      {/* 价格和库存用客户端组件实时获取 */}
      <RealtimePrice productId={params.id} />
    </div>
  )
}
```

## 5.6 四种渲染模式对比选型与业务落地技巧

### 5.6.1 一张表看懂四种模式

把四种渲染模式放到同一张表里对比，差异一目了然。这张表建议收藏，做技术选型时直接对照参考：

| 维度 | CSR | SSR | SSG | ISR |
|-----|-----|-----|-----|-----|
| HTML生成位置 | 浏览器 | 服务器 | 构建时 | 构建时+后台更新 |
| HTML生成时机 | JS执行时 | 每次请求 | 一次构建 | 定期/按需 |
| 首屏速度(FCP) | 慢(1-3s) | 中(200-800ms) | 快(<50ms) | 快(<50ms) |
| SEO支持 | 差 | 好 | 好 | 好 |
| 服务器开销 | 极低 | 高 | 零 | 极低 |
| 内容实时性 | 实时 | 实时 | 构建时快照 | 接近实时 |
| CDN友好 | 不适用 | 不适用 | 完美 | 完美 |
| 开发复杂度 | 低 | 中 | 低 | 中 |
| 适合规模 | 小型应用 | 大型动态应用 | 内容站 | 内容站+电商 |

### 5.6.2 按业务类型选型

**企业官网/品牌站**：SSG。内容更新频率低，SEO是刚需，流量可能突发。SSG生成的静态文件部署到CDN，无论流量多大都能扛住。企业官网一年可能就改几次内容，完全不需要动态渲染。

**后台管理系统**：CSR。不需要SEO，用户已登录，交互密集。纯客户端渲染开发效率最高，服务器零计算开销。用SSR反而增加了不必要的复杂度。

**电商网站**：混合模式。这是最能体现Next.js同构渲染优势的场景。首页和活动页用SSG（极致首屏速度，大促期间扛住流量），商品详情页用ISR（定期更新价格库存），用户中心和个人订单用SSR（个性化数据，每次请求渲染），购物车和商品筛选用CSR（交互密集，实时更新）。

**博客/文档站**：SSG或ISR。如果内容更新不频繁，SSG足够。如果需要发布后自动更新，用ISR配合on-demand重新生成。文档站特别适合SSG，因为文档内容很少变动，而且SEO极其重要。

**新闻门户**：ISR为主。文章页revalidate设置5到10分钟，突发新闻用on-demand ISR立即更新。首页可以更短，1到2分钟，确保读者总能看到最新的新闻列表。

```
业务类型 → 推荐渲染模式：

企业官网     → SSG（静态部署到CDN）
后台管理     → CSR（'use client'即可）
电商商品页   → ISR（revalidate=300s + on-demand）
电商首页     → SSG（活动页静态生成）
新闻文章     → ISR（revalidate=600s + on-demand）
用户中心     → SSR（个性化数据，每次请求渲染）
实时协作工具 → CSR（交互密集，WS实时更新）
文档站      → SSG（内容稳定，SEO重要）
```

### 5.6.3 混合渲染：同一项目不同路由用不同模式

Next.js最强大的能力之一就是混合渲染。同一个项目里，不同路由可以自由选择不同的渲染模式，互不干扰。这是其他框架很难做到的——你要么全用SSR（如Nuxt.js的默认模式），要么全用CSR（如纯React SPA），很难在一个项目里灵活组合。混合渲染的价值在大规模项目中尤为突出。想象一个电商平台：首页需要SSG来扛住大促流量，商品页需要ISR来保持价格更新，用户中心需要SSR来展示个性化数据，购物车需要CSR来处理复杂交互。在Next.js之前，你可能需要把这些功能拆成多个独立项目，各自用不同的技术栈。而Next.js让这些功能共存于一个项目中，共享组件库和构建流程。

```
app/
├── page.tsx              → SSG（首页，静态生成）
├── products/[id]/page.tsx → ISR（商品页，5分钟更新）
├── dashboard/page.tsx     → SSR（仪表盘，动态数据）
└── admin/page.tsx         → CSR（后台管理）
```

每个路由的核心代码差异很小，主要是渲染模式的声明方式不同：

```tsx
// app/page.tsx - SSG（默认静态，无需额外配置）
export default async function HomePage() {
  const banner = await fetch('https://api.example.com/banner')
    .then(r => r.json())
  return <HeroBanner data={banner} />
}
```

```tsx
// app/products/[id]/page.tsx - ISR
export const revalidate = 300  // 5分钟重新生成
export default async function ProductPage({ params }) {
  const product = await fetch(
    `https://api.example.com/products/${params.id}`
  ).then(r => r.json())
  return <ProductDetail product={product} />
}
```

```tsx
// app/dashboard/page.tsx - SSR（cookies()触发动态渲染）
import { cookies } from 'next/headers'
export default async function DashboardPage() {
  const cookieStore = await cookies()
  const token = cookieStore.get('token')?.value
  const stats = await fetch('https://api.example.com/stats', {
    headers: { Authorization: `Bearer ${token}` },
    cache: 'no-store'
  }).then(r => r.json())
  return <StatsDashboard data={stats} />
}
```

```tsx
// app/admin/page.tsx - CSR
'use client'
export default function AdminPage() {
  return <AdminDashboard />
}
```

### 5.6.4 渲染模式切换的迁移成本

在App Router中，渲染模式之间的切换成本非常低。大多数情况下，你只需要修改几行代码就能切换渲染模式，不需要重构整个组件结构。这是App Router相比Pages Router的一个重大改进——在Pages Router中，切换渲染模式意味着要在`getStaticProps`和`getServerSideProps`之间切换，这两个函数的签名和行为完全不同，迁移成本不低。

```
SSG → ISR：加一行 export const revalidate = N
SSG → SSR：加一行 fetch(url, { cache: 'no-store' })
          或引入 cookies()/headers()
ISR → SSR：删除 revalidate，加 cache: 'no-store'
SSR → CSR：加 'use client'，数据获取移到useEffect
CSR → SSR：删 'use client'，数据获取改为async/await
```

但有几个需要注意的迁移成本：SSR/SSG/ISR → CSR需要把所有Server Component改为Client Component，数据获取从async/await改为useEffect，如果有大量的服务端数据获取逻辑，迁移工作量不小。CSR → SSR需要把`useEffect`里的数据获取改为组件顶层的`async/await`，确保没有浏览器API的使用，如果有大量的客户端状态管理，可能需要重构组件结构。

### 5.6.5 企业级项目渲染策略决策模板

怕浪猫在实际项目中总结了一个渲染模式决策模板，供你参考。这个模板经过多个项目的验证，覆盖了绝大多数常见场景。当然，实际项目中还会遇到更复杂的情况，比如同一个页面中有多个数据源、不同部分需要不同的渲染策略。这时候可以把页面拆分成多个独立的Suspense区域，每个区域各自采用合适的渲染模式，通过流式渲染组合呈现。

```
渲染模式决策流程：

Step 1: 这个页面需要SEO吗？
  ├─ 否 → CSR（后台管理、登录后页面）
  └─ 是 → Step 2

Step 2: 页面内容是个性化的吗（依赖用户身份）？
  ├─ 是 → SSR（用户中心、个人推荐）
  └─ 否 → Step 3

Step 3: 内容更新频率是多少？
  ├─ 几乎不变 → SSG（关于页、文档）
  ├─ 每天/每小时 → ISR + on-demand（博客、商品页）
  └─ 每分钟/秒级 → SSR（实时数据、社交时间线）

Step 4: 页面有多个数据源，更新频率不同？
  ├─ 是 → 混合模式（ISR为主 + 客户端实时数据）
  └─ 否 → 使用Step 3的结果
```

> 渲染模式选型不是技术问题，是业务问题。先搞清楚"这个页面的内容多久更新一次"、"用户能容忍多久的内容延迟"、"需不需要SEO"这三个问题，答案自然就出来了。怕浪猫见过太多团队不分场景全用SSR，结果服务器账单翻了好几倍，其实80%的页面用SSG就够了。

## 5.7 渲染模式性能优化实战

### 5.7.1 减少客户端JS体积：Server Components优先

App Router的默认组件是Server Component，这不仅仅是为了SSR——更重要的是**减少发送到浏览器的JS**。Server Component的代码永远不会出现在客户端bundle中，浏览器只收到渲染后的HTML。这是App Router最重要的性能优化方向。

```
Server Component vs Client Component 的JS传输：

Server Component:
  服务器渲染HTML → 浏览器只收HTML（0字节JS）

Client Component:
  服务器渲染HTML → 浏览器收HTML + 组件JS代码 + 依赖库
  JS体积 = 组件代码 + useState等React hooks + 第三方库
```

优化原则：**能不写`'use client'`就不写**。把交互逻辑集中到少数几个叶子组件中，让大多数组件保持Server Component身份。这个原则说起来简单，但在实际项目中需要刻意设计组件边界。

```tsx
// 优化前：整个列表都是Client Component
'use client'
export default function ProductList({ products }) {
  const [filter, setFilter] = useState('')
  const filtered = products.filter(p => p.name.includes(filter))
  
  return (
    <div>
      <input value={filter} onChange={e => setFilter(e.target.value)} />
      <ul>
        {filtered.map(p => <li key={id}>{p.name} - {p.price}</li>)}
      </ul>
    </div>
  )
}

// 优化后：只让搜索框成为Client Component
import { SearchInput } from './SearchInput'

export default function ProductList({ products }) {
  return (
    <div>
      <SearchInput products={products} />
    </div>
  )
}
```

### 5.7.2 Suspense + lazy loading优化首屏

Suspense不仅能用于流式渲染，还能配合`lazy`实现代码分割。把非首屏关键的组件用Suspense包裹，让它们延迟加载，优先渲染首屏核心内容。这样首屏JS体积更小，加载更快，非核心功能在后台异步加载。

```tsx
import { Suspense, lazy } from 'react'

const HeavyChart = lazy(() => import('./HeavyChart'))

export default function DashboardPage() {
  return (
    <div>
      {/* 首屏核心内容，立即渲染 */}
      <h1>仪表盘</h1>
      <SummaryCards />

      {/* 非关键组件，延迟加载 */}
      <Suspense fallback={<div>图表加载中...</div>}>
        <HeavyChart />
      </Suspense>

      <Suspense fallback={<div>评论加载中...</div>}>
        <Comments />
      </Suspense>
    </div>
  )
}
```

### 5.7.3 数据获取并行化

串行数据获取是性能杀手。如果一个页面需要三个API的数据，串行获取需要T1+T2+T3的时间，并行获取只需要max(T1, T2, T3)。在Server Component中，数据获取的并行化尤为重要，因为整个页面在等待数据获取完成才能返回HTML。

```tsx
// 串行获取（慢）：总耗时 = T1 + T2 + T3
export default async function Page() {
  const user = await fetch('/api/user').then(r => r.json())
  const posts = await fetch('/api/posts').then(r => r.json())
  const comments = await fetch('/api/comments').then(r => r.json())
  return <Dashboard user={user} posts={posts} comments={comments} />
}

// 并行获取（快）：总耗时 = max(T1, T2, T3)
export default async function Page() {
  const [user, posts, comments] = await Promise.all([
    fetch('/api/user').then(r => r.json()),
    fetch('/api/posts').then(r => r.json()),
    fetch('/api/comments').then(r => r.json())
  ])
  return <Dashboard user={user} posts={posts} comments={comments} />
}
```

### 5.7.4 缓存层利用

Next.js的`fetch`自带缓存层，合理利用可以大幅减少服务器计算。四种缓存策略覆盖了绝大多数场景：

```tsx
// ISR：定时重新验证
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 }
})

// SSR：不缓存
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store'
})

// Tag缓存：按需失效
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600, tags: ['products'] }
})
// 通过 revalidateTag('products') 立即更新
```

```
缓存策略选择：

数据特征              推荐策略                    代码
──────────────────────────────────────────────────────
几乎不变              force-cache(默认)           fetch(url)
定期更新              ISR                         fetch(url, { next: { revalidate: N } })
实时数据              no-store                    fetch(url, { cache: 'no-store' })
需要手动控制更新       tag-based                   fetch(url, { next: { tags: [...] } })
```

### 5.7.5 性能测量

优化不能靠感觉，得用数据说话。Lighthouse和Web Vitals是两个核心工具。Web Vitals是Google定义的一组用户体验指标，直接反映用户感知到的页面性能：

```tsx
'use client'
import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    console.log(metric)
    // 上报到分析平台
  })
  return null
}
```

核心Web Vitals指标：

| 指标 | 全称 | 含义 | 目标值 |
|-----|------|------|-------|
| LCP | Largest Contentful Paint | 最大内容绘制时间 | < 2.5s |
| FID | First Input Delay | 首次输入延迟 | < 100ms |
| CLS | Cumulative Layout Shift | 累积布局偏移 | < 0.1 |
| FCP | First Contentful Paint | 首次内容绘制 | < 1.8s |
| TTFB | Time To First Byte | 首字节时间 | < 600ms |

> 性能优化是"测量-分析-优化"的循环，不是拍脑袋。先跑一次Lighthouse看分数，找到瓶颈在哪——是JS太大、数据获取太慢、还是图片没优化。对症下药，一次只优化一个指标，测完再优化下一个。怕浪猫见过有人一通操作猛如虎，结果Lighthouse分数不升反降，就是没有先测量再优化。

## 5.8 本章小结与课后练习

### 本章核心回顾

这一章我们从渲染模式的演进史出发，深入剖析了CSR、SSR、SSG、ISR四种渲染模式的原理、适用场景和实战陷阱。核心要点回顾：

第一，渲染模式的本质是"何时生成HTML"的问题——构建时（SSG）、请求时（SSR）、客户端运行时（CSR）、还是定时更新（ISR）。选择哪种模式，取决于业务对SEO、首屏性能、内容时效性的要求。没有最好的渲染模式，只有最合适的。

第二，App Router的最大改进是渲染模式的自动推断。你不需要像Pages Router那样手动选择`getStaticProps`或`getServerSideProps`，Next.js根据你使用的API自动决定渲染模式。用了`cookies()`就是SSR，设了`revalidate`就是ISR，什么都没用就是SSG。这个设计大幅降低了心智负担。

第三，混合渲染是Next.js的杀手锏。同一个项目里不同路由可以用不同渲染模式，这在其他框架中是很难做到的。企业官网用SSG、商品页用ISR、用户中心用SSR、后台管理用CSR——一个项目搞定所有场景。

第四，性能优化的核心原则是"Server Component优先"。尽量让组件在服务端渲染，减少发送到浏览器的JS体积。配合Suspense流式渲染、Promise.all并行数据获取、合理的缓存策略，能把首屏性能压到极致。

### 课后练习

**练习一：渲染模式识别**

给定以下代码片段，判断每个页面会使用什么渲染模式（CSR/SSR/SSG/ISR），并说明理由：

```tsx
// 页面A
export default async function PageA() {
  const data = await fetch('https://api.example.com/data')
  return <div>{data.json().title}</div>
}

// 页面B
export const revalidate = 60
export default async function PageB() {
  const data = await fetch('https://api.example.com/data')
  return <div>{data.json().title}</div>
}

// 页面C
import { cookies } from 'next/headers'
export default async function PageC() {
  const c = await cookies()
  const data = await fetch('https://api.example.com/data', {
    headers: { auth: c.get('token')?.value || '' }
  })
  return <div>{data.json().title}</div>
}
```

**练习二：ISR实战**

构建一个简单的博客系统：首页展示文章列表，使用ISR每5分钟更新一次；文章详情页使用`generateStaticParams`预生成已有文章；新文章发布时通过API路由触发on-demand重新生成；添加secret校验防止未授权调用。

**练习三：混合渲染架构设计**

为一个电商网站设计渲染策略：首页（活动页）选择渲染模式并说明理由；商品详情页价格5分钟更新一次但库存需要实时；用户中心展示个人信息和订单需要登录；购物车高频交互实时更新。写出每个页面的核心代码结构。

**练习四：性能优化**

给定一个首屏LCP为4.2秒的页面，分析可能的瓶颈并给出优化方案。当前使用SSR每次请求获取5个API的数据（串行），页面包含一个大型图表组件（200KB JS），图片未做优化直接使用`<img>`标签，没有使用Suspense边界。

**练习五：踩坑排查**

以下代码在SSR环境下报错"window is not defined"，请分析原因并给出修复方案：

```tsx
export default function Page() {
  const isMobile = window.innerWidth < 768
  return (
    <div>
      {isMobile ? <MobileLayout /> : <DesktopLayout />}
    </div>
  )
}
```

如果你觉得这篇文章对你有帮助，收藏起来方便以后查阅。四种渲染模式的选型表格和决策模板特别值得收藏，下次项目选型时直接对照着用。有什么疑问或者踩了什么新坑，评论区见，怕浪猫会一一回复。

下一章我们将进入Next.js的数据获取世界。Server Component中的async/await、fetch的缓存机制、Server Actions的表单处理——这些App Router时代的数据获取新范式，和Pages Router有着根本性的区别。我们会从基础用法讲到高级缓存策略，再到实战中的数据流设计。不想错过的话，关注追更就对了。

系列进度 5/16

怕浪猫说：渲染模式就像厨房里不同的烹饪方式。SSG是预制菜，提前做好放冰柜，客人来了微波炉热一下端上桌，快是真快，但你不能指望预制菜天天新鲜。SSR是现点现做，最新鲜但客人得等着。ISR是预制菜加定时补货，大部分时候上菜快，内容也不会太陈旧。CSR嘛，是给客人一包食材和菜谱，让他自己回厨房做——灵活是灵活，但饿着肚子的那几分钟可不是什么好体验。关键是：知道你的客人需要什么，然后选对烹饪方式。
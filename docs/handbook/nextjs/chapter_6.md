# 第6章 Next.js数据获取与状态管理

90%的Next.js性能问题，不是出在渲染机制上，而是出在数据获取和状态管理上。服务端拿到了数据却不会传给客户端，客户端有了状态却和服务端不同步，缓存失效不知道该刷哪里——这些问题困扰着几乎每一个从React SPA（Single Page Application，单页应用）迁移到Next.js的开发者。数据获取和状态管理是全栈应用的命脉，搞不定这两件事，SSR（Server-Side Rendering，服务端渲染）的优势就白费了。很多团队花大力气把项目从Create React App迁到Next.js，结果数据层还是用老一套的客户端请求模式，首屏性能根本没有改善，反而多了一层服务端渲染的复杂度。

我是怕浪猫，一个在Next.js数据层踩过无数坑的全栈开发者。从Pages Router到App Router，从纯客户端fetch到Server Components的async数据获取，我经历了Next.js数据获取范式的每一次变迁。这一章我会把服务端数据获取、客户端状态管理、缓存策略、状态同步这些核心话题，从原理到实战全部拆透。文章比较长，建议先收藏再看，因为每个小节都有实际项目中才会遇到的踩坑经验。

## 6.1 服务端数据获取：async/await、generateStaticParams

### 6.1.1 Server Components中的async数据获取模式

Next.js App Router最大的变革，是Server Components（服务端组件）原生支持`async/await`。这意味着你可以在组件内部直接发起异步数据请求，不需要`useEffect`，不需要`getServerSideProps`，不需要任何生命周期钩子。组件本身就是一个异步函数，数据获取和渲染在同一个地方完成。这个变化看似只是语法层面的简化，实际上它彻底改变了数据获取的心智模型——在Pages Router时代，数据获取和组件渲染是两个分离的阶段，你需要先在`getServerSideProps`中获取数据，然后通过props传给组件。而在App Router中，这两件事合并成了同一步。

来看最基本的用法：

```tsx
// app/products/page.tsx
export default async function ProductsPage() {
  const res = await fetch('https://api.example.com/products')
  const products = await res.json()

  return (
    <main>
      <h1>产品列表</h1>
      <ul>
        {products.map((p: { id: number; name: string }) => (
          <li key={p.id}>{p.name}</li>
        ))}
      </ul>
    </main>
  )
}
```

这段代码在服务端执行，`fetch`请求发生在服务器上，客户端收到的已经是渲染好的HTML。和传统React中用`useEffect`在客户端发请求相比，这种方式有两个核心优势：一是减少了客户端的JavaScript包体积，二是用户看到的首屏内容不需要等待客户端水合后再发请求。在传统的SPA模式中，用户访问页面时的流程是"下载HTML → 下载JS → 水合 → 发起数据请求 → 渲染数据"，总共需要四次往返。而在Server Components模式中，流程简化为"请求HTML（服务端已获取数据并渲染） → 下载JS → 水合"，只需要两次往返。

但这里有个容易忽略的细节：`fetch`的缓存行为在Next.js中被重新定义了。在Pages Router中，`fetch`默认不缓存；而在App Router中，`fetch`默认会被缓存。这个行为变化让很多从Pages Router迁移过来的开发者踩了坑——明明数据更新了，页面却还是旧的。怕浪猫在第一次用App Router写项目时就被这个问题困扰了半天，后来才发现需要显式设置`cache: 'no-store'`或`next: { revalidate: 0 }`来禁用缓存。

> Server Components中async/await最大的价值不是语法简洁，而是把数据获取从客户端的"请求-等待-渲染"序列变成了服务端的"获取-渲染-交付"流水线。用户感知到的延迟，从两次往返压缩到了一次。

理解数据流的方向很重要。在Server Components中，数据从服务端获取，通过React的序列化机制传递到客户端组件。这个传递过程不是通过JSON API，而是通过RSC（React Server Components，React服务端组件）协议进行流式传输。你可以把RSC理解为一个特殊的序列化格式，它不仅携带数据，还携带组件结构和引用关系。这意味着服务端组件获取的数据可以"流"到客户端组件中，而不需要额外发一次API请求。

```
Server Components数据流：

  服务端                          客户端
  ┌─────────────┐                ┌─────────────┐
  │ async fetch │   RSC Payload  │   hydrate   │
  │ 获取数据     │ ─────────────→ │   水合组件   │
  │ 渲染组件     │   (流式传输)    │   交互就绪   │
  └─────────────┘                └─────────────┘
       一次往返                       零额外请求
```

### 6.1.2 fetch API扩展：next.revalidate、next.tags

Next.js对原生`fetch` API做了扩展，增加了`next`配置项，这是理解Next.js数据缓存的核心入口。两个最重要的选项是`next.revalidate`和`next.tags`。这两个选项的设计理念来源于HTTP Cache-Control的`max-age`和`stale-while-revalidate`指令，但做了更上层的抽象，让开发者不需要理解HTTP缓存的细节就能控制数据的新鲜度。

`next.revalidate`控制数据的缓存时间，单位是秒。这个选项利用了stale-while-revalidate语义——在缓存有效期内直接返回缓存数据，过期后在后台重新获取。这种策略对用户来说是"无感知"的：缓存有效期内访问，直接返回缓存，响应速度极快；缓存过期后首次访问，仍然返回旧缓存（比没有快），同时触发后台刷新，下次访问就能拿到新数据。

```tsx
// 缓存60秒，过期后后台刷新
const res = await fetch('https://api.example.com/products', {
  next: { revalidate: 60 }
})

// 完全禁用缓存，每次请求都重新获取
const res = await fetch('https://api.example.com/realtime', {
  next: { revalidate: 0 }
})

// 永久缓存（默认行为）
const res = await fetch('https://api.example.com/static-data')
```

`next.tags`则提供了更精细的缓存控制能力。你可以给请求打上标签，然后在需要时通过`revalidateTag`按标签批量失效缓存。这在内容管理场景中非常实用——比如文章更新后，只需要失效"articles"标签的缓存，其他数据不受影响。如果不使用标签，你在更新数据后只能选择失效整个路由（用`revalidatePath`），这会导致路由中所有数据的缓存都被清空，包括那些根本没有变化的数据，下次访问时需要全部重新获取。

```tsx
// 给请求打标签
const res = await fetch('https://api.example.com/articles', {
  next: { tags: ['articles'] }
})

// 在Server Action或路由处理器中按标签失效
import { revalidateTag } from 'next/cache'

export async function updateArticle() {
  await db.update('articles', data)
  revalidateTag('articles') // 失效所有标记为'articles'的缓存
}
```

> 缓存不是"要不要"的问题，而是"多久"和"怎么失效"的问题。`revalidate`解决"多久"，`tags`解决"怎么失效"。两个维度组合起来，才能构建出既快又准的数据缓存策略。

这里有一个踩坑点：`fetch`的缓存配置只有在Server Components、Server Actions和Route Handlers中才有效。在Client Components中调用`fetch`，`next`配置项会被忽略——因为客户端没有Next.js的缓存层。如果你发现配置了`revalidate`但数据还是不更新，第一步就是检查这个`fetch`是否真的在服务端执行。判断方法很简单：看组件文件顶部有没有`'use client'`声明。有的话，这个组件中的所有代码（包括fetch调用）都在客户端执行，`next`配置不生效。

另一个常见的坑是在开发模式下缓存行为和生产环境不一致。开发模式下，Next.js为了方便调试，默认不启用Data Cache——每次请求都会重新获取数据。只有在生产模式（`next build && next start`）下，缓存才会真正生效。所以你在开发时觉得缓存策略配置正确了，到生产环境可能表现完全不同。建议在上线前用生产模式本地跑一遍，验证缓存行为是否符合预期。

### 6.1.3 generateStaticParams预生成动态路由参数

`generateStaticParams`是App Router中替代Pages Router `getStaticPaths`的功能，用于在构建时预生成动态路由的参数。它告诉Next.js："这些路由参数在构建时就确定好了，提前把对应的页面生成出来。"这样做的好处是，这些页面在运行时直接返回预渲染的HTML，不需要动态计算，响应速度最快，而且可以部署到CDN（Content Delivery Network，内容分发网络）上。

```tsx
// app/products/[id]/page.tsx
export async function generateStaticParams() {
  const res = await fetch('https://api.example.com/products')
  const products = await res.json()

  return products.map((p: { id: string }) => ({
    id: p.id.toString(),
  }))
}

export default async function ProductDetail({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const res = await fetch(`https://api.example.com/products/${id}`)
  const product = await res.json()

  return <div>{product.name}</div>
}
```

`generateStaticParams`返回一个参数对象数组，Next.js会在构建时为每个参数组合生成静态HTML。对于构建时未生成的路由，Next.js会按需在运行时动态渲染（前提是配置了`dynamicParams = true`，这是默认行为）。如果你设置`export const dynamicParams = false`，那么构建时未生成的路由将返回404，这在某些场景下是有用的——比如你只想让已上架的商品页面可访问，未上架的返回404。

一个实际的经验法则：如果你的数据量在几百到几千条之间，全部预生成是合理的。如果数据量达到十万级以上，建议只预生成热门页面，其余的按需渲染。怕浪猫曾经在项目中尝试预生成十万个商品详情页，构建时间从3分钟飙升到40分钟，最后改成了只预生成Top 1000的SKU（Stock Keeping Unit，库存量单位），其余走ISR（Incremental Static Regeneration，增量静态再生），构建时间回到了5分钟以内。ISR是介于静态生成和动态渲染之间的折中方案：首次访问时动态渲染并缓存，后续访问返回缓存，`revalidate`时间到了后台刷新。这样既保证了构建速度，又保证了所有页面都能访问。

### 6.1.4 并行与串行数据获取的性能差异

在Server Components中，多个数据请求的获取方式直接影响页面性能。串行获取是默认写法，但往往不是最优解。很多开发者在写Server Components时，习惯性地按顺序写多个`await`，以为这是理所当然的——毕竟代码从上到下执行嘛。但如果有两个请求之间没有依赖关系，串行执行就是在白白浪费用户的等待时间。

```tsx
// 串行获取：总耗时 = 请求A + 请求B
export default async function Dashboard() {
  const user = await fetch('/api/user').then(r => r.json())     // 200ms
  const orders = await fetch('/api/orders').then(r => r.json()) // 300ms
  // 总计 500ms
  return <Dashboard user={user} orders={orders} />
}

// 并行获取：总耗时 = max(请求A, 请求B)
export default async function Dashboard() {
  const [user, orders] = await Promise.all([
    fetch('/api/user').then(r => r.json()),     // 200ms
    fetch('/api/orders').then(r => r.json()),   // 300ms
  ])
  // 总计 300ms
  return <Dashboard user={user} orders={orders} />
}
```

两种写法的差异在请求较多时会非常明显。假设你有5个无依赖请求，每个耗时200ms，串行总共需要1000ms，并行只需要200ms——5倍差距。但并行获取也有注意事项：如果请求之间有依赖关系（比如请求B需要请求A返回的ID作为参数），那就只能串行。对于没有依赖的请求，始终应该使用`Promise.all`并行化。

```
串行 vs 并行时间对比：

串行模式:
  |-- fetch user (200ms) --|-- fetch orders (300ms) --|  = 500ms

并行模式:
  |-- fetch user (200ms) --|
  |-- fetch orders (300ms) --|                          = 300ms
```

还有一种模式是"组件嵌套并行"。在App Router中，如果父组件把数据获取的结果通过props传给子组件，那么子组件必须等父组件获取完才能开始渲染，这就是串行的。但如果子组件自己获取数据，不依赖父组件的props，那么Next.js会在服务端并行渲染这两个组件。这个特性叫做"流式渲染"（Streaming），底层依赖React的Suspense机制。流式渲染的原理是：服务端不需要等所有组件都渲染完毕再返回HTML，而是可以先把已经渲染好的部分发送给客户端，还没好的部分用Suspense的fallback占位，等数据到了再流式追加。

```tsx
// 父组件不阻塞子组件：各取各的数据
export default async function Page() {
  return (
    <main>
      <Suspense fallback={<Skeleton />}>
        <UserProfile />  {/* 自己获取user数据 */}
      </Suspense>
      <Suspense fallback={<Skeleton />}>
        <OrderList />    {/* 自己获取orders数据 */}
      </Suspense>
    </main>
  )
}
```

> 数据获取的并行化不是优化，而是默认应该做的事。串行获取多个无依赖请求，本质上是在浪费用户的等待时间。

### 6.1.5 服务端数据获取的错误处理与重试

服务端数据获取失败时，如果没有妥善处理，用户看到的就是一个500错误页面。这不仅用户体验差，还可能导致搜索引擎爬虫收录到错误页面。Next.js的Server Components中，错误处理主要依赖Error Boundaries（错误边界）和`error.tsx`文件。每个路由段都可以有自己的`error.tsx`，它会捕获同级及子级路由中Server Components抛出的未处理错误。

```tsx
// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>数据加载失败</h2>
      <p>{error.message}</p>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

`error.tsx`必须是Client Component（`'use client'`），因为错误恢复需要用户交互（点击重试按钮）。`reset`函数会重新渲染出错的路由段，相当于一次"软刷新"。`error.digest`是Next.js自动生成的错误摘要，可以用来在日志中关联具体错误，但不建议直接展示给用户。

但仅有错误边界还不够。对于不稳定的第三方API，你需要实现自动重试逻辑。网络请求失败的原因很多——可能是临时的网络抖动、可能是服务端瞬时过载、可能是DNS解析超时。这些错误中有一部分是"可重试的"——也就是说，再试一次可能就成功了。Next.js的`fetch`扩展不支持内置重试，但你可以自己封装：

```tsx
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3
): Promise<Response> {
  try {
    const res = await fetch(url, options)
    if (!res.ok && res.status >= 500 && retries > 0) {
      throw new Error(`Server error: ${res.status}`)
    }
    return res
  } catch (err) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, 1000 * (4 - retries)))
      return fetchWithRetry(url, options, retries - 1)
    }
    throw err
  }
}
```

这个封装实现了指数退避重试：第一次重试等待1秒，第二次2秒，第三次3秒。对于5xx服务器错误才重试，4xx客户端错误直接抛出——因为重试一个400 Bad Request是没有意义的，请求参数不会因为重试而变正确。指数退避的意义在于给服务端恢复的时间，如果服务端是因为过载而返回5xx，立即重试只会加重负担，而等待一段时间后重试成功率会高得多。

## 6.2 客户端数据获取：SWR、React Query实战

### 6.2.1 SWR核心原理：stale-while-revalidate策略

SWR（Stale-While-Revalidate，过期后重新验证）是由Vercel团队开发的客户端数据获取库，它的名字本身就概括了核心策略：先返回过期数据（stale），同时在后台重新验证（revalidate），验证完成后用新数据替换旧数据。这个策略最早来自HTTP Cache-Control扩展头，SWR把它引入到了React的数据获取层。

这个策略带来的用户体验是"零等待"——页面立即展示缓存数据，用户不需要盯着loading动画发呆，后台拿到新数据后无缝替换。想象一个新闻列表页面：用户第一次打开时需要从服务器获取数据，有短暂的loading状态；之后用户在站内浏览其他页面再回来时，新闻列表瞬间展示上次的缓存数据，同时在后台静默拉取最新数据，如果有新文章就以无感方式更新到页面上。

```
SWR策略时间线：

时间 ──→

首次请求:
  |-- 网络请求(500ms) --|-- 展示数据 --|
  loading               数据就绪

后续请求（有缓存）:
  |-- 立即展示缓存 --|-- 后台刷新 --|
  零等待              静默更新
```

SWR的最基本用法非常简单，学习成本极低：

```tsx
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(r => r.json())

function Profile() {
  const { data, error, isLoading } = useSWR('/api/user', fetcher)

  if (isLoading) return <div>加载中...</div>
  if (error) return <div>加载失败</div>
  return <div>你好，{data.name}</div>
}
```

SWR的核心机制是它的缓存key系统。`useSWR`的第一个参数就是cache key，通常是一个URL字符串。相同的key在组件树中共享同一份数据和请求状态——这意味着你在两个不同组件里用相同的key调用`useSWR`，只会发出一次网络请求。这比传统的"把数据提到父组件然后通过props传递"的做法优雅得多，既避免了prop drilling的繁琐，又保证了数据的一致性。

> SWR的精妙之处不在于它发了什么请求，而在于它不发请求的时候——缓存命中时的零延迟体验，才是它真正解决的问题。

### 6.2.2 SWR在Next.js中的配置与使用

在Next.js中使用SWR，最关键的是配合Server Components做预取和水合。如果不做预取，客户端首次渲染时SWR没有缓存数据，会先显示loading状态，等请求返回后才展示内容——这就失去了SSR的首屏优势。SWR官方提供了`SWRConfig`来做全局配置，但更好的方案是利用Server Components先获取初始数据，然后传递给客户端组件作为SWR的fallback数据。

```tsx
// app/users/page.tsx (Server Component)
import UsersClient from './UsersClient'
import { SWRConfig } from 'swr'

export default async function UsersPage() {
  const res = await fetch('https://api.example.com/users')
  const initialData = await res.json()

  return (
    <SWRConfig
      value={{
        fallback: {
          '/api/users': initialData,
        },
      }}
    >
      <UsersClient />
    </SWRConfig>
  )
}
```

```tsx
// app/users/UsersClient.tsx
'use client'
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(r => r.json())

export default function UsersClient() {
  const { data } = useSWR('/api/users', fetcher)
  return <div>{/* 渲染用户列表 */}</div>
}
```

这个模式的威力在于：服务端预取的数据通过`fallback`注入SWR的缓存，客户端首次渲染时直接命中缓存，不会有loading状态。之后SWR会在后台静默刷新，如果数据有变化就替换。用户全程看不到loading，但数据始终是最新的（在`revalidate`周期内）。这种"服务端预取 + 客户端缓存"的模式，是Next.js数据获取的最佳实践之一。

SWR的全局配置还可以设置刷新频率、错误重试、请求去重等策略，这些配置可以在`SWRConfig`中统一设置，所有子组件中的`useSWR`调用都会继承这些配置：

```tsx
<SWRConfig
  value={{
    refreshInterval: 30000,    // 每30秒自动刷新
    errorRetryCount: 3,        // 最多重试3次
    dedupingInterval: 5000,    // 5秒内相同请求去重
    revalidateOnFocus: true,   // 窗口聚焦时刷新
  }}
>
  <App />
</SWRConfig>
```

其中`revalidateOnFocus`是一个很有用的功能——当用户从其他浏览器标签切回来时，SWR会自动刷新数据。这在需要展示实时性数据的场景中很实用，比如管理后台的待办列表、消息通知等。但如果你有一个写操作频繁的页面，频繁的focus刷新可能导致过多的请求，这时可以关闭这个选项。

### 6.2.3 React Query（TanStack Query）的核心概念

React Query（现已更名为TanStack Query）是另一个流行的客户端数据获取库。它的核心概念比SWR更丰富，提供了更完善的工具链。如果说SWR是"够用就好"的极简派，那React Query就是"全面且专业"的重型武器。

React Query的三个核心概念需要先理解清楚：

第一是Query（查询），对应一个异步数据获取操作，通过`useQuery`使用。每个Query有一个唯一的`queryKey`，React Query根据这个key来管理和复用缓存。第二是Mutation（变更），对应一个数据修改操作，通过`useMutation`使用。Mutation和Query是分离的——你发起一个Mutation后，需要手动决定是否失效相关的Query缓存。第三是QueryClient（查询客户端），管理所有缓存、缓存策略和交互，通常在应用根部通过`QueryClientProvider`注入。

```tsx
import { QueryClient, useQuery } from '@tanstack/react-query'

const queryClient = new QueryClient()

function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetch(`/api/users/${userId}`).then(r => r.json()),
    staleTime: 60 * 1000,  // 数据新鲜期1分钟
    gcTime: 5 * 60 * 1000, // 垃圾回收时间5分钟
  })

  if (isLoading) return <div>加载中...</div>
  return <div>{data?.name}</div>
}
```

React Query的`queryKey`是一个数组，这比SWR的字符串key更灵活。当key中包含变量（如`userId`）时，React Query会精确地为每个变量值维护独立的缓存。这意味着从用户A切换到用户B时，React Query会为B发起新请求，同时保留A的缓存——如果用户再切回A，可以立即命中缓存。修改操作完成后，你可以通过`queryClient.invalidateQueries`来精确失效相关缓存：

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'

function UpdateUser() {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (data: { name: string }) =>
      fetch('/api/user', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })

  return (
    <button onClick={() => mutation.mutate({ name: '新名字' })}>
      更新
    </button>
  )
}
```

`staleTime`和`gcTime`是两个容易混淆的概念。`staleTime`控制数据"新鲜"的时长——在这个时间内，React Query不会重新请求。`gcTime`（原来叫`cacheTime`）控制缓存的存活时间——超过这个时间没有被任何组件使用的缓存会被垃圾回收。打个比方：`staleTime`是"这个数据多久算过期"，`gcTime`是"这个缓存多久后清理掉"。

### 6.2.4 React Query vs SWR：选型对比

这两个库经常被放在一起比较，怕浪猫给你做一个全面的对比。选型时不要只看功能列表，更要看你的项目实际需要什么。很多团队选择React Query是因为它功能多，但功能多也意味着学习成本高、包体积大。如果你的项目只是需要一个简单的数据缓存层，用React Query就像"用大炮打蚊子"。

| 对比维度 | SWR | React Query |
|---------|-----|-------------|
| 包体积 | 约4KB | 约13KB |
| 学习曲线 | 低，API极少 | 中，概念较多 |
| 变更支持 | 需手动实现 | 内置useMutation |
| 开发者工具 | 基础 | 强大的Devtools |
| 预取支持 | fallback机制 | prefetchQuery |
| 分页/无限滚动 | 内置useSWRInfinite | 内置useInfiniteQuery |
| 乐观更新 | 需手动实现 | 内置onMutate回调 |
| 服务端渲染 | fallback简单 | Hydration API较复杂 |

选型建议很简单：如果你的项目以读为主、写操作不多，SWR的轻量和简洁是优势。如果你的项目有大量的CRUD（Create Read Update Delete，增删改查）操作、需要乐观更新、需要精细的缓存控制，React Query的完善生态更合适。怕浪猫在实际项目中的经验是：中小型项目用SWR的开发效率更高，因为API简单、配置少、上手快；大型项目特别是有复杂数据流的企业级应用，React Query的Mutation机制和Devtools能省去很多手动处理的麻烦。

> 选库不是选"最好的"，而是选"最合适的"。SWR像一把瑞士军刀，小巧够用；React Query像一套专业工具箱，功能全面。你的项目复杂度决定了你需要哪个。

### 6.2.5 客户端数据获取的预取与水合

预取和水合是提升首屏体验的关键技术。核心思路是：服务端先获取数据，客户端拿到数据后直接渲染，不等待客户端的请求往返。这解决了一个根本矛盾——SSR的优势是首屏快，但如果客户端需要重新发请求获取数据，这个优势就消失了。预取让服务端获取的数据"传递"到客户端的缓存中，客户端首次渲染时直接使用这份数据，不需要额外的网络请求。

SWR的预取通过`fallback`实现（上面已展示），React Query的预取则使用`prefetchQuery`和`HydrationBoundary`：

```tsx
// app/users/page.tsx (Server Component)
import {
  QueryClient, HydrationBoundary, dehydrate
} from '@tanstack/react-query'
import UsersClient from './UsersClient'

export default async function UsersPage() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['users'],
    queryFn: () => fetch('https://api.example.com/users').then(r => r.json()),
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <UsersClient />
    </HydrationBoundary>
  )
}
```

```tsx
// app/users/UsersClient.tsx
'use client'
import { useQuery } from '@tanstack/react-query'

export default function UsersClient() {
  const { data } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetch('/api/users').then(r => r.json()),
  })
  return <div>{/* 用户列表，首屏无loading */}</div>
}
```

这里的`dehydrate`把服务端的查询缓存序列化成一个纯JS对象，这个对象会作为`HydrationBoundary`的props传递到客户端。`HydrationBoundary`在客户端把它反序列化并注入QueryClient。客户端首次渲染时`useQuery`会命中这份缓存，不发出网络请求。这个过程对开发者是透明的——你只需要在服务端调`prefetchQuery`，客户端的`useQuery`就自动有了初始数据。

## 6.3 原生fetch API封装与请求拦截

### 6.3.1 fetch API基础与Next.js扩展

原生`fetch` API是Web标准的数据获取接口，Next.js在其基础上做了扩展。理解这些扩展是掌握Next.js数据层的前提。原生的`fetch`返回一个Promise，响应是一个`Response`对象，你需要手动调用`res.json()`或`res.text()`来解析响应体。它不内置JSON解析、不内置错误处理（HTTP 4xx/5xx不会抛异常，只有网络错误才会reject）、不内置超时控制——这些都需要开发者自己处理。

Next.js扩展的配置项集中在`next`字段中：

```tsx
const res = await fetch(url, {
  next: {
    revalidate: 60,        // 缓存60秒
    tags: ['products'],    // 缓存标签
  },
})
```

这些扩展只在服务端有效。在客户端，`fetch`就是标准的Web API，`next`配置会被忽略。理解这一点很重要——很多开发者误以为在Client Components中配置`next.revalidate`也能生效，结果发现数据每次都在重新请求。另外需要注意，Next.js的`fetch`扩展覆盖了原生的`fetch`方法，这在TypeScript中可能会引起类型冲突。如果你在项目中同时使用了第三方库（如Axios），需要注意它们调用`fetch`时也会命中Next.js的扩展行为。

### 6.3.2 统一请求封装：baseURL、headers、timeout

在实际项目中，直接使用`fetch`会面临几个问题：没有统一的baseURL（每个请求都要写完整的URL）、每个请求都要手动设置headers（特别是Content-Type和Authorization）、没有超时控制（原生`fetch`默认没有超时，网络问题时请求会一直挂起）。封装一个统一的请求函数是标准做法，也是团队协作的基础——所有开发者使用同一个请求函数，便于统一修改和维护。

```tsx
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.example.com'

interface RequestOptions extends RequestInit {
  timeout?: number
}

export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { timeout = 10000, ...opts } = options
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      signal: controller.signal,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  } finally {
    clearTimeout(timer)
  }
}
```

这个封装解决了三个核心问题：baseURL拼接（环境变量驱动，开发和生产可以配置不同的API地址）、统一headers（JSON类型为默认，可被覆盖）、超时控制（AbortController实现，默认10秒）。`timeout`参数允许每个请求自定义超时时间，比如文件上传可以设置更长的超时。

### 6.3.3 请求拦截器与响应拦截器

Axios的拦截器机制很好用，但`fetch`原生不支持。拦截器的价值在于"横切关注点"——那些需要在每个请求前后统一处理的逻辑，比如添加认证token、记录日志、统一错误处理。如果没有拦截器，这些逻辑就会散落在各个请求调用处，代码重复且容易遗漏。我们可以通过包装函数链来实现类似的能力：

```tsx
type Interceptor<T> = (value: T) => T | Promise<T>

class RequestClient {
  private reqInterceptors: Interceptor<RequestInit>[] = []
  private resInterceptors: Interceptor<Response>[] = []

  onRequest(fn: Interceptor<RequestInit>) {
    this.reqInterceptors.push(fn)
  }
  onResponse(fn: Interceptor<Response>) {
    this.resInterceptors.push(fn)
  }

  async fetch(url: string, options: RequestInit = {}) {
    let opts = options
    for (const fn of this.reqInterceptors) opts = await fn(opts)
    let res = await fetch(url, opts)
    for (const fn of this.resInterceptors) res = await fn(res)
    return res
  }
}
```

使用时，可以在应用初始化时注册拦截器，之后所有的请求都会自动经过这些拦截器：

```tsx
const client = new RequestClient()

// 请求拦截：自动添加token
client.onRequest((options) => {
  const token = getToken()
  if (token) {
    options.headers = { ...options.headers, Authorization: `Bearer ${token}` }
  }
  return options
})

// 响应拦截：统一处理401
client.onResponse((res) => {
  if (res.status === 401) redirectToLogin()
  return res
})
```

> 拦截器的本质是"中间件模式"——请求和响应各经过一条管道，管道中的每个环节都可以修改数据或中断流程。理解了这个模式，你就理解了所有HTTP库的拦截器设计。

### 6.3.4 错误统一处理与重试逻辑

错误处理是请求封装中最容易被忽视的部分。很多开发者只处理了"请求成功但业务失败"的情况（比如HTTP 200但业务码表示错误），却忽略了网络层面的错误分类。一个好的错误处理策略需要区分网络错误（TypeError）、超时错误（AbortError）、HTTP状态码错误（4xx/5xx），并分别采取不同的处理方式。

```tsx
export async function requestWithErrorHandling<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const maxRetries = options.method === 'GET' ? 3 : 0

  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await request<T>(path, options)
    } catch (err) {
      const isLastRetry = i === maxRetries
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new Error('请求超时，请稍后重试')
      }
      if (err instanceof TypeError) {
        if (isLastRetry) throw new Error('网络连接失败')
        await new Promise(r => setTimeout(r, 1000 * (i + 1)))
        continue
      }
      throw err
    }
  }
  throw new Error('未知错误')
}
```

这个封装的策略是：只有GET请求才重试（写操作重试可能导致重复提交——比如重复创建订单、重复扣款），网络错误用指数退避重试（等待时间递增，给服务端恢复时间），超时和HTTP错误直接抛出。这是一个在安全性和可用性之间取得平衡的策略。对于写操作的重试，更安全的做法是使用幂等性设计——每次请求携带一个唯一的requestId，服务端根据requestId判断是否为重复请求，这样即使客户端重试也不会产生副作用。

### 6.3.5 请求取消：AbortController

`AbortController`是Web标准提供的请求取消机制，Next.js完全支持。在React组件中，当组件卸载时取消未完成的请求，是防止内存泄漏和状态更新的标准做法。如果不取消，组件卸载后请求返回时仍然会调用`setState`，React会报"Can't perform a React state update on an unmounted component"警告（虽然React 18已经移除了这个警告，但请求仍然在后台浪费带宽）。

```tsx
'use client'
import { useEffect, useState } from 'react'

function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState([])

  useEffect(() => {
    const controller = new AbortController()
    fetch(`/api/search?q=${query}`, { signal: controller.signal })
      .then(r => r.json())
      .then(setResults)
      .catch((err) => {
        if (err.name !== 'AbortError') console.error(err)
      })
    return () => controller.abort()
  }, [query])

  return <div>{/* 搜索结果 */}</div>
}
```

这个模式在搜索框场景中尤其重要。用户快速输入时，每次按键都会触发新的请求，旧的请求如果没取消，可能在新请求之后返回，导致结果闪烁——这就是经典的竞态条件（Race Condition）。通过`AbortController`取消上一次请求，可以确保只有最新的请求结果会被渲染。竞态条件在异步编程中是一个大类问题，不仅仅是fetch，任何"先发后到"的异步操作都可能产生竞态，使用AbortController或忽略过期请求的返回值是标准的解决方案。

## 6.4 全局状态管理：Zustand/Redux适配Next.js

### 6.4.1 Zustand极简上手：5行代码搞定全局状态

Zustand是一个极简的React状态管理库，它的API设计理念是"少即是多"。创建一个全局store只需要几行代码，不需要Provider包裹、不需要Reducer函数、不需要Action类型常量。对于从Redux迁移过来的开发者来说，Zustand的简洁几乎是令人难以置信的：

```tsx
import { create } from 'zustand'

interface BearStore {
  bears: number
  increase: () => void
}

const useBearStore = create<BearStore>((set) => ({
  bears: 0,
  increase: () => set((s) => ({ bears: s.bears + 1 })),
}))

function BearCounter() {
  const bears = useBearStore((s) => s.bears)
  return <h1>{bears} bears</h1>
}
```

没有Provider、没有Reducer、没有Action类型定义。`create`函数返回一个hook，组件中直接调用就能获取和更新状态。这种极简设计大大降低了状态管理的认知负担。Zustand的另一个优势是细粒度订阅。通过选择器函数`useBearStore((s) => s.bears)`，组件只订阅`bears`字段的变化。当store中其他字段更新时，这个组件不会重新渲染。这一点比传统的`useContext` + `useState`模式高效得多——Context的任何变化都会导致所有消费组件重新渲染，即使它们只用了Context中的一小部分数据。

> Zustand证明了状态管理不需要复杂。一个create函数、一个set方法、一个选择器，就是全部API。当你不需要Redux的中间件生态时，Zustand就是最佳选择。

### 6.4.2 Zustand在SSR中的水合问题与解决

在Next.js SSR环境中使用Zustand会遇到一个经典问题：服务端和客户端的store状态不一致。服务端渲染时创建了一个store实例，客户端水合时又创建了另一个，两者的状态不同步，导致水合不匹配警告。这个问题的根因是Zustand的store是模块级别的单例——在服务端，所有请求共享同一个store实例，这会导致不同用户的数据相互污染。

解决方法是使用Zustand官方推荐的`persist`中间件配合`skipHydration`选项：

```tsx
// lib/store.ts
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface Store {
  theme: 'light' | 'dark'
  setTheme: (t: 'light' | 'dark') => void
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'app-store',
      storage: createJSONStorage(() => localStorage),
      skipHydration: true,
    }
  )
)
```

```tsx
// components/Hydrate.tsx
'use client'
import { useEffect } from 'react'
import { useStore } from '@/lib/store'

export function Hydrate() {
  useEffect(() => {
    useStore.persist.rehydrate()
  }, [])
  return null
}
```

`skipHydration: true`告诉Zustand不要在模块加载时自动从localStorage读取数据，而是等客户端水合时手动触发。这样可以避免服务端渲染的HTML与客户端首次渲染的状态不一致。原因是localStorage只在浏览器中存在，服务端访问会报错，如果Zustand在服务端模块加载时就尝试读取localStorage，会导致错误。

### 6.4.3 Redux Toolkit在Next.js中的接入

Redux Toolkit（RTK）是Redux官方推荐的写法，大幅减少了样板代码。在Next.js App Router中接入Redux，需要处理服务端store和客户端store的隔离问题。App Router的Server Components不能直接使用Redux store（因为store是有状态的，而Server Components应该尽可能无状态），所以Redux的使用范围主要在Client Components中。

```tsx
// lib/store.ts
import { configureStore } from '@reduxjs/toolkit'
import counterReducer from './counterSlice'

export function makeStore() {
  return configureStore({
    reducer: { counter: counterReducer },
  })
}

export type AppStore = ReturnType<typeof makeStore>
export type RootState = ReturnType<AppStore['getState']>
export type AppDispatch = AppStore['dispatch']
```

```tsx
// lib/Provider.tsx
'use client'
import { useRef } from 'react'
import { Provider } from 'react-redux'
import { makeStore, AppStore } from './store'

export default function StoreProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const storeRef = useRef<AppStore>()
  if (!storeRef.current) {
    storeRef.current = makeStore()
  }
  return <Provider store={storeRef.current}>{children}</Provider>
}
```

关键点在于`useRef`——它确保每个客户端应用只有一个store实例，不会因为组件重渲染而重复创建。在服务端，每次请求都应该创建新的store实例以避免请求间状态泄漏，但在App Router中，Server Components不直接使用Redux store，状态通过props传递。如果你的应用需要在Server Components中访问Redux状态，建议将状态提升到数据库或API中，Server Components通过fetch获取。

### 6.4.4 Zustand vs Redux：轻量 vs 生态

| 对比维度 | Zustand | Redux Toolkit |
|---------|---------|--------------|
| 包体积 | 约1KB | 约14KB |
| 样板代码 | 极少 | 中等（RTK已大幅减少） |
| TypeScript支持 | 优秀 | 优秀 |
| Devtools | 基础（可集成） | 强大（Redux DevTools） |
| 中间件生态 | 基础 | 丰富（saga, thunk等） |
| 学习成本 | 低 | 中 |
| 时间旅行调试 | 不支持 | 支持 |
| 适用场景 | 中小型应用 | 大型复杂应用 |

怕浪猫的选择建议：新项目优先考虑Zustand。当你真正需要Redux的中间件生态、时间旅行调试或复杂的action编排时，再迁移到Redux也不迟。在大多数业务场景中，Zustand的能力已经足够了，而且代码量少一半以上。Redux的价值在于它的"约束性"——强制的单向数据流和不可变更新，在大型团队协作中可以防止状态管理的混乱。如果你的团队规模不大、状态逻辑不复杂，这种约束反而是累赘。

### 6.4.5 状态管理的模块化拆分

随着项目增长，单个store会变得臃肿。一个包含用户、购物车、产品、订单、通知等所有状态的store，不仅文件巨大，还会导致每次状态更新时所有订阅者都需要检查是否需要重新渲染。Zustand的模块化方案是"切片模式"（Slice Pattern），每个业务模块独立定义自己的状态和操作，最后组合到一起：

```tsx
// stores/userSlice.ts
import { StateCreator } from 'zustand'
import { StoreState } from './index'

export interface UserSlice {
  user: { id: string; name: string } | null
  setUser: (user: UserSlice['user']) => void
}

export const createUserSlice: StateCreator<
  StoreState, [], [], UserSlice
> = (set) => ({
  user: null,
  setUser: (user) => set({ user }),
})
```

```tsx
// stores/index.ts
import { create } from 'zustand'
import { createUserSlice, UserSlice } from './userSlice'
import { createCartSlice, CartSlice } from './cartSlice'

export type StoreState = UserSlice & CartSlice

export const useStore = create<StoreState>()((...a) => ({
  ...createUserSlice(...a),
  ...createCartSlice(...a),
}))
```

每个切片独立定义状态结构和操作逻辑，通过类型交叉`&`组合成完整的Store类型。这种模式的优点是模块间解耦，可以按需加载——甚至可以做到路由级别的代码分割，不同路由只加载自己需要的store切片。比如商品详情页只需要productSlice，不需要加载cartSlice。这在Zustand中实现起来非常自然，而在Redux中则需要使用Redux Dynamic Modules等额外工具。

## 6.5 服务端状态与客户端状态协同方案

### 6.5.1 服务端状态vs客户端状态的边界划分

在Next.js全栈应用中，状态分为两大类：服务端状态和客户端状态。正确划分两者的边界，是架构设计的核心问题。很多团队在初期没有做好这个划分，导致出现各种奇怪的问题——比如把本该放在服务端的用户权限信息存在客户端的Zustand中，结果用户刷新页面后权限丢失；或者把本该放在客户端的UI状态（如弹窗开关）存到数据库里，导致一个用户的操作影响所有用户。

```
状态边界划分：

服务端状态                         客户端状态
┌──────────────────┐            ┌──────────────────┐
│ - 数据库数据       │            │ - UI状态          │
│ - 用户会话         │            │ - 表单输入        │
│ - 权限信息         │            │ - 主题/语言       │
│ - 实时性要求低的   │            │ - 实时性要求高的   │
│   业务数据         │            │   交互状态        │
└────────┬─────────┘            └────────┬─────────┘
         │                                │
         └────────── Next.js ─────────────┘
            Server Components传props给
            Client Components作为初始值
```

划分原则很简单：如果状态需要被多个用户共享或需要持久化到数据库，放服务端。如果状态只跟单个用户的当前交互有关且不需要持久化，放客户端。但有些状态比较微妙——比如购物车数据，既需要服务端持久化（跨设备同步），又需要客户端即时响应（添加商品时不等待网络请求）。这种"混合状态"的最优解是后面要讲的"服务端为真相源，客户端为缓存层"模式。

> 状态归属的决策树只有一个问题：这个状态的"唯一真相源"（Single Source of Truth）在哪里。数据库里的就是服务端状态，浏览器里的就是客户端状态。混合状态的最优解是"服务端为真相源，客户端为缓存层"。

### 6.5.2 Server Components传递初始数据到Client Components

Server Components获取的数据通过props传递给Client Components，这是Next.js中最基础的服务端到客户端数据流。但这个传递有约束：传递的数据必须是可序列化的（Serializable）。这意味着函数、Class实例、Date对象、Map/Set等不能直接传递。

```tsx
// app/dashboard/page.tsx (Server Component)
import DashboardClient from './DashboardClient'

export default async function DashboardPage() {
  const userData = await fetch('https://api.example.com/me').then(r => r.json())
  const settings = await fetch('https://api.example.com/settings').then(r => r.json())

  return (
    <DashboardClient
      initialUser={userData}
      initialSettings={settings}
    />
  )
}
```

```tsx
// app/dashboard/DashboardClient.tsx
'use client'
import { useState } from 'react'

export default function DashboardClient({
  initialUser,
  initialSettings,
}: {
  initialUser: User
  initialSettings: Settings
}) {
  const [user] = useState(initialUser)
  const [settings, setSettings] = useState(initialSettings)

  return (
    <div>
      <p>欢迎，{user.name}</p>
      {/* 客户端交互 */}
    </div>
  )
}
```

不可序列化的数据需要转换：`Date`对象转成ISO字符串（`date.toISOString()`），`Map`转成普通对象（`Object.fromEntries(map)`），`Set`转成数组（`Array.from(set)`）。如果传递了不可序列化的值，Next.js会在开发模式下给出警告。还有一个容易忽略的点：传递的数据会包含在RSC Payload中，随HTML一起发送到客户端。如果数据量很大（比如几万条记录），会导致首屏HTML体积过大，影响加载速度。建议在Server Components中只获取"首屏需要的数据"，分页数据等按需在客户端获取。

### 6.5.3 服务端数据与客户端缓存的同步

当服务端数据更新后，如何通知客户端更新缓存？这是全栈状态一致性的核心挑战。在Next.js中，主要有三种同步策略，分别适用于不同的场景。

**策略一：revalidateTag触发缓存失效 + SWR自动刷新**。这种策略适用于服务端数据更新后不需要立即在客户端反映的场景。Server Action中更新数据并失效缓存后，用户下次访问或SWR下次刷新时才能拿到新数据。

```tsx
'use server'
import { revalidateTag } from 'next/cache'

export async function updateProfile(data: FormData) {
  await db.update('users', data)
  revalidateTag('user-profile')
}
```

**策略二：使用SWR的mutate主动刷新**。这种策略适用于用户操作后需要立即看到更新结果的场景，比如用户编辑了个人资料后，立即刷新缓存。

```tsx
'use client'
import { mutate } from 'swr'

async function handleUpdate() {
  await fetch('/api/profile', { method: 'POST', body: ... })
  mutate('/api/profile') // 主动刷新SWR缓存
}
```

**策略三：Server Action返回值直接更新缓存**。这是最优雅的策略——Server Action的返回值直接作为最新数据更新SWR缓存，不需要额外的请求往返。适用于更新操作的结果可以完全确定的新状态。

```tsx
'use server'
export async function updateName(name: string) {
  const updated = await db.update('users', { name })
  return updated
}

// 客户端
'use client'
import { useSWRConfig } from 'swr'

function UpdateButton() {
  const { mutate } = useSWRConfig()
  const handleUpdate = async () => {
    const updated = await updateName('新名字')
    mutate('/api/user', updated, false)
  }
  return <button onClick={handleUpdate}>更新</button>
}
```

`mutate`的第三个参数`false`表示不需要再发请求验证，因为我们已经从Server Action的返回值中拿到了最新数据。如果传`true`或不传，SWR会在更新缓存的同时再发一次请求确认——这在某些需要强一致性的场景中是有用的，但大多数情况下`false`就够了。

### 6.5.4 乐观更新与服务端校验

乐观更新（Optimistic Update）是指：用户操作后，先在客户端立即更新UI，同时发送请求到服务端，如果服务端失败则回滚。这种策略让用户感觉操作是"瞬时完成"的。点赞、收藏、标记已读等操作非常适合乐观更新——用户点了点赞按钮，按钮立即变为已点赞状态，不需要等待服务端响应。如果服务端处理失败，再回滚到未点赞状态并提示用户。

```tsx
'use client'
import { useMutation, useQueryClient } from '@tanstack/react-query'

function ToggleLike({ postId }: { postId: string }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (liked: boolean) =>
      fetch(`/api/posts/${postId}/like`, { method: 'POST' }),
    onMutate: async (liked) => {
      await queryClient.cancelQueries({ queryKey: ['post', postId] })
      const previous = queryClient.getQueryData(['post', postId])
      queryClient.setQueryData(['post', postId], (old: any) => ({
        ...old,
        liked,
        likeCount: old.liked ? old.likeCount - 1 : old.likeCount + 1,
      }))
      return { previous }
    },
    onError: (err, vars, context) => {
      queryClient.setQueryData(['post', postId], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['post', postId] })
    },
  })

  return <button onClick={() => mutation.mutate(true)}>点赞</button>
}
```

React Query的`onMutate`回调是实现乐观更新的关键：它在请求发出之前执行，先把UI更新为期望的状态。如果请求失败，`onError`中用`context.previous`回滚。`onSettled`中无论成功失败都失效缓存重新获取，确保最终一致性。这个三段式模式（乐观更新 → 失败回滚 → 最终校验）是处理用户交互的标准范式。

> 乐观更新的本质是"用乐观换取体验"——假设请求大概率会成功，先把结果展示给用户。它的风险在于如果服务端校验失败率较高，频繁的回滚会让用户困惑。所以乐观更新只适用于成功率高的操作。

### 6.5.5 全栈状态一致性保证

全栈状态一致性的终极方案是"服务端为唯一真相源，客户端为乐观缓存"。这意味着客户端的任何状态都只是服务端数据的临时副本，最终都必须以服务端为准。以下是保证一致性的检查清单：

第一，写操作走Server Actions。所有数据修改通过Server Actions执行，确保服务端校验和数据库一致性。不要在客户端直接调用修改数据的API，因为客户端校验可以被绕过。第二，读操作走Server Components加客户端缓存。首屏数据由Server Components获取，后续刷新由SWR或React Query管理。第三，缓存失效与数据更新绑定。数据修改后立即失效对应缓存标签，确保下次请求获取最新数据。第四，乐观更新配合回滚机制。用户体验优先，但必须有回滚保底。第五，最终一致性校验。关键操作完成后，定期重新获取数据确保客户端与服务端一致。

```
全栈状态一致性流：

用户操作
  │
  ├─→ 乐观更新客户端UI（瞬时）
  │
  ├─→ Server Action提交到服务端
  │     ├─→ 成功：确认乐观状态，失效缓存
  │     └─→ 失败：回滚客户端状态
  │
  └─→ 下次请求获取最新数据（最终一致）
```

这套机制的核心思想是"最终一致性"——在任意时刻，客户端状态可能和服务端不完全一致（因为乐观更新），但在操作完成后（无论成功还是失败），客户端最终会收敛到和服务端一致的状态。这种设计在大多数业务场景中是足够的，不需要强一致性带来的性能开销。

## 6.6 数据缓存策略与失效更新

### 6.6.1 Next.js内置缓存层级：Data Cache、Full Route Cache

Next.js的缓存系统是分层的，理解每一层的作用范围和失效机制，是掌握性能优化的前提。很多开发者觉得Next.js的缓存"难以理解"，根本原因是没搞清楚这四层缓存各自的范围和生命周期。

```
Next.js缓存层级：

请求层
  ┌───────────────────────────────────────┐
  │ Request Memoization (请求去重)         │  ← 单次请求内有效
  └───────────────┬───────────────────────┘
                  │
数据层
  ┌───────────────┴───────────────────────┐
  │ Data Cache (数据缓存)                  │  ← 跨请求持久化
  │ - fetch请求结果                        │     按revalidate/tags失效
  └───────────────┬───────────────────────┘
                  │
路由层
  ┌───────────────┴───────────────────────┐
  │ Full Route Cache (全路由缓存)          │  ← 静态路由的HTML+RSC
  │ - 渲染结果的缓存                       │     按数据缓存失效联动
  └───────────────────────────────────────┘
```

**Request Memoization**是最细粒度的缓存：在同一次请求（同一个render过程）中，相同的`fetch`调用只执行一次，后续调用返回缓存结果。这意味着你在Server Components的不同子组件中调用同一个URL的`fetch`，实际只发出一次网络请求。这个缓存是最短命的——请求结束就清空，但它解决了"组件树中重复请求"的问题。

```tsx
// 这两个fetch在同一次渲染中只执行一次
async function ProductList() {
  const res = await fetch('https://api.example.com/products')
  const products = await res.json()
  return <List items={products} />
}

async function ProductCount() {
  // 命中Request Memoization，不发出额外请求
  const res = await fetch('https://api.example.com/products')
  const products = await res.json()
  return <span>共{products.length}件商品</span>
}
```

**Data Cache**是跨请求的缓存层，存储`fetch`的响应结果。它的生命周期独立于单个请求，可以被`revalidate`时间或`revalidateTag`触发失效。这是Next.js性能优化的核心——相同的数据不需要每次请求都从源API获取。Data Cache存储在Next.js的内部存储中（在Vercel上使用Edge Network的分布式缓存），即使服务重启也不会丢失。

**Full Route Cache**是路由级别的缓存，存储的是整个路由的渲染结果（HTML + RSC Payload）。当路由中所有数据都被缓存时，这个路由就是"静态"的，渲染结果可以被Full Route Cache缓存，下次请求直接返回缓存的HTML。当Data Cache中的某个数据失效时，依赖这个数据的路由的Full Route Cache也会联动失效。

### 6.6.2 revalidateTag与revalidatePath按需失效

按需失效是Next.js缓存系统的杀手锏。`revalidateTag`按标签失效，`revalidatePath`按路径失效。这两个函数只能在Server Actions和Route Handlers中调用，不能在Server Components中直接调用——因为Server Components的职责是渲染，不应该有副作用。

```tsx
'use server'
import { revalidateTag, revalidatePath } from 'next/cache'

export async function updateArticle(id: string, content: string) {
  await db.update('articles', { id, content })
  revalidateTag('articles')        // 失效所有标记为'articles'的fetch缓存
  revalidateTag(`article-${id}`)   // 失效特定文章的缓存
  revalidatePath(`/blog/${id}`)    // 失效文章详情页的路由缓存
  revalidatePath('/blog')          // 失效文章列表页的路由缓存
}
```

> 缓存失效的粒度决定了缓存命中率。`revalidateTag`失效的是"一类数据"，`revalidatePath`失效的是"一个页面"。粒度越细，命中率越高，但管理成本也越高。实际项目中，建议按业务实体来打标签——文章用'articles'，用户用'users'，失效时按实体类型操作。

一个常见的踩坑点：在Server Action中调用`revalidateTag`后，当前请求中的`fetch`缓存不会立即更新——失效是针对后续请求的。如果你在同一个Server Action中先失效再fetch，拿到的是新数据（因为缓存已失效），但这个新数据不会被自动缓存到当前请求的Data Cache中。这是Next.js缓存设计的一个有意为之的行为——避免在同一个操作中产生缓存依赖循环。

### 6.6.3 缓存命中率的监控与优化

缓存做出来了，但怎么知道它有没有命中？不能凭感觉，要看数据。Next.js提供了`headers()`函数来检查缓存状态，也可以通过Vercel的观测面板查看缓存命中率。

在开发环境中，可以通过响应头查看缓存命中情况：

```tsx
import { headers } from 'next/headers'

export default async function Page() {
  const h = await headers()
  const cacheStatus = h.get('x-nextjs-cache') // HIT / MISS / STALE

  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 60, tags: ['data'] }
  })
  const data = await res.json()

  return <p>缓存状态: {cacheStatus}</p>
}
```

`x-nextjs-cache`的值含义：`HIT`表示命中缓存，直接返回了缓存数据；`MISS`表示未命中，通常发生在首次请求或缓存失效后；`STALE`表示缓存已过期但仍在后台刷新，当前返回的是旧数据。在Vercel的生产环境中，你可以在Dashboard的Analytics面板中看到整体的缓存命中率，以及每个路由的缓存命中分布。

提升缓存命中率的核心策略是合理设置`revalidate`时间和精细打标签。对于更新频率低的数据（如配置信息、分类目录、导航菜单），设置较长的`revalidate`（如3600秒甚至更长）；对于更新频率高的数据（如实时库存、价格、消息通知），设置较短的`revalidate`（如10秒）或使用按需失效。另一个策略是"分层缓存"——对同一数据的不同视图设置不同的缓存策略，比如列表页缓存1分钟，详情页缓存5分钟。

### 6.6.4 缓存穿透与缓存雪崩的防护

缓存穿透是指请求的数据在缓存和源数据源中都不存在，每次请求都会穿透到源API。典型场景是查询一个不存在的ID——缓存中没有（因为之前没查过），查源API也返回空，下次请求还是穿透。如果有恶意用户构造大量不存在的ID发请求，就可能把源API打垮。缓存雪崩是指大量缓存同时过期，导致瞬间大量请求打到源API。典型场景是你给100个API都设置了相同的60秒缓存，60秒一到，所有请求同时回源。

**缓存穿透防护：空值缓存**

```tsx
export async function fetchWithCacheGuard(url: string, revalidate = 60) {
  const res = await fetch(url, { next: { revalidate } })
  const data = await res.json()
  // 空结果也缓存，避免反复穿透
  if (!data) {
    return { _empty: true, _cachedAt: Date.now() }
  }
  return data
}
```

**缓存雪崩防护：随机过期时间**

```tsx
function getStaggeredRevalidate(base: number): number {
  const jitter = Math.floor(Math.random() * base * 0.3)
  return base + jitter // 30%随机偏移
}

const res = await fetch(url, {
  next: { revalidate: getStaggeredRevalidate(60) }
})
```

> 缓存雪崩的本质是"羊群效应"——所有缓存同时失效，请求像羊群一样涌向源站。解法很简单：在过期时间上加随机偏移，让失效时间分散开。这个技巧在后端缓存设计中是通用的，Redis缓存的过期时间也应该这么做。

### 6.6.5 多级缓存架构设计

在复杂应用中，单一缓存层是不够的。一个成熟的多级缓存架构通常包含从客户端到源数据源的多个缓存层次，每一层的职责和特性不同。理解这个架构，你就能在遇到性能问题时知道该优化哪一层。

```
多级缓存架构：

客户端                    CDN/Edge              服务端
┌──────────┐           ┌──────────┐         ┌──────────┐
│ SWR/     │  ←──→     │ Edge     │  ←──→  │ Next.js  │  ←──→  源API
│ React    │           │ Cache    │         │ Data     │         /数据库
│ Query    │           │ (Vercel) │         │ Cache    │
│ 缓存     │           │          │         │          │
└──────────┘           └──────────┘         └──────────┘
  毫秒级                  ~10ms                ~100ms       ~500ms
```

每一层的职责不同：客户端缓存（SWR/React Query）处理用户交互的即时响应，避免相同数据的重复请求；Edge缓存（CDN）在离用户最近的节点缓存静态内容，减少网络延迟；Data Cache（Next.js服务端）缓存API响应，减少对源数据源的压力；源数据（数据库/API）是唯一真相源。

层级间的协调原则是"上游失效，下游跟随"。当Server Action通过`revalidateTag`失效了Data Cache，Full Route Cache也会联动失效，下次请求时Vercel的Edge Cache会从源站拉取新的HTML。客户端缓存则通过SWR的`revalidateOnFocus`和`refreshInterval`自动刷新。如果你使用CDN层面的缓存（如Cloudflare），需要通过`Cache-Control`响应头或Webhook通知CDN刷新。整个多级缓存的目标是：让用户尽可能从离自己最近的缓存层获取数据，只有在缓存不可用时才回源。

## 6.7 本章小结与课后练习

这一章信息量很大，怕浪猫帮你做一个精简的回顾。

**服务端数据获取**的核心是Server Components中的`async/await`和`fetch`扩展。`next.revalidate`控制缓存时间，`next.tags`支持按标签失效。`generateStaticParams`预生成动态路由参数，`Promise.all`并行化无依赖请求提升性能。错误处理依赖`error.tsx`错误边界和自定义重试封装，重试策略需要注意只有GET请求才适合自动重试。

**客户端数据获取**推荐SWR或React Query。SWR轻量简洁，适合读多写少场景；React Query功能完善，适合复杂CRUD场景。两者都支持服务端预取加客户端水合的零loading首屏体验，这是Next.js数据获取的最佳实践。

**请求封装**需要统一baseURL、headers、timeout，通过拦截器链实现请求和响应的统一处理。AbortController是请求取消的标准方案，能有效防止竞态条件。错误处理需要区分网络错误、超时错误和HTTP错误，分别采取不同策略。

**状态管理**方面，Zustand适合中小型项目（极简API、1KB体积），Redux Toolkit适合大型复杂项目（丰富生态、时间旅行调试）。Zustand的切片模式支持模块化拆分，Redux的`useRef`方案解决SSR单例问题。在SSR中使用状态管理库都需要注意水合问题。

**状态协同**的关键是"服务端为真相源，客户端为缓存层"。乐观更新提升交互体验但需要回滚保底，Server Actions的返回值可以直接更新客户端缓存实现零延迟同步。全栈状态一致性通过"乐观更新 → 失败回滚 → 最终校验"三段式模式保证。

**缓存策略**需要理解Next.js的四层缓存（Request Memoization → Data Cache → Full Route Cache → Client Cache）。`revalidateTag`按标签失效，`revalidatePath`按路径失效。缓存穿透用空值缓存防护，缓存雪崩用随机过期时间分散。多级缓存架构中每一层职责不同，优化时要找到瓶颈在哪一层。

### 课后练习

1. 在一个Server Component中，分别用串行和并行方式获取三个无依赖的API，对比两种方式的响应时间差异。尝试用`Suspense`包裹子组件实现流式渲染，观察效果。

2. 创建一个带`revalidate: 60`和`tags: ['products']`的fetch请求，然后在Server Action中实现"更新商品后自动失效缓存"的完整流程。在开发模式和生产模式下分别测试，观察缓存行为的差异。

3. 使用SWR实现一个带服务端预取的客户端组件，要求首屏无loading状态，且每30秒自动刷新一次。对比不使用预取时的体验差异。

4. 用Zustand的切片模式实现一个包含用户状态和购物车状态的store，并解决SSR水合问题。思考：购物车数据应该完全放在客户端，还是需要服务端持久化？

5. 实现一个带乐观更新的点赞功能：点击后立即UI变化，Server Action提交，失败时回滚。思考：什么场景下不适合用乐观更新？

怕浪猫说：数据获取和状态管理是Next.js全栈能力的分水岭。会写组件只是入门，会管数据才是高手。这一章的内容值得反复看，每个知识点都配着实际项目中的踩坑经验。如果你在实践中遇到了文中没覆盖到的问题，欢迎在评论区交流，怕浪猫会持续更新这份知识库。

收藏引导：这篇文章覆盖了Next.js数据获取与状态管理的完整知识体系，从服务端fetch到客户端SWR/React Query，从Zustand状态管理到多级缓存架构，建议收藏后反复查阅。每个小节都可以作为独立参考文档使用。

互动引导：你在Next.js数据获取中踩过最大的坑是什么？SWR还是React Query你更偏好哪个？Zustand够用还是离不开Redux？评论区聊聊你的选择和理由。

追更引导：下一章我们会进入Next.js的API路由与后端能力开发，涵盖Route Handlers、Server Actions、Middleware中间件等核心话题。关注我，不迷路。

系列进度 6/16

下章预告：第7章将深入Next.js API路由与后端能力开发，包括Route Handlers的请求处理、Server Actions的全栈数据流、Middleware中间件机制，以及如何在Next.js中构建完整的BFF（Backend For Frontend，服务于前端的后端）层。
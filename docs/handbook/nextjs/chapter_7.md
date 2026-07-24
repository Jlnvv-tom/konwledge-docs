# 第7章 Next.js API路由：搭建后端服务接口

试了3种方式搭建后端接口，最后发现Next.js的Route Handler才是全栈开发的最优解——不用单独维护一个后端服务，前端项目里直接写API，部署成本直接砍半。

我是怕浪猫，一个踩过无数API坑的全栈开发者。今天这章，我把Next.js API路由从原理到实战全部拆透，帮你跳过我踩过的那些坑。

## 7.1 API路由核心原理与运行机制

### 7.1.1 Route Handler：app/api/目录下的route.ts

Next.js App Router中的API路由叫Route Handler，核心就一句话：在`app/api/`目录下创建`route.ts`文件，导出HTTP方法对应的函数。

```
app/
├── api/
│   ├── posts/
│   │   └── route.ts      → /api/posts
│   ├── posts/[id]/
│   │   └── route.ts      → /api/posts/:id
│   └── users/
│       └── route.ts      → /api/users
```

最简Route Handler长这样：

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const posts = [{ id: 1, title: 'Hello' }]
  return NextResponse.json(posts)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  return NextResponse.json({ id: 2, ...body }, { status: 201 })
}
```

每个HTTP方法对应一个导出的函数：`GET`、`POST`、`PUT`、`DELETE`、`PATCH`。没导出的方法会自动返回405 Method Not Allowed。

> Route Handler的本质：一个运行在服务端的函数，接收Request对象，返回Response对象。没有魔法，全是标准的Web API。

### 7.1.2 Route Handler vs Pages Router的API Routes

如果你用过Next.js的Pages Router，肯定知道`pages/api/`目录。两者的核心区别：

| 维度 | Pages Router (pages/api/) | App Router (app/api/route.ts) |
|------|--------------------------|-------------------------------|
| 文件约定 | 文件本身就是路由 | route.ts文件 + 目录结构 |
| 导出方式 | 默认导出handler函数 | 按HTTP方法命名导出 |
| 请求对象 | req: NextApiRequest | request: NextRequest (Web标准) |
| 响应对象 | res: NextApiResponse | NextResponse (Web标准Response) |
| 类型安全 | 需要手动类型 | 原生TypeScript友好 |
| 中间件 | 自定义wrapper | middleware.ts统一拦截 |

Pages Router里一个接口文件要处理所有方法：

```typescript
// pages/api/posts.ts (Pages Router)
import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') { /* ... */ }
  if (req.method === 'POST') { /* ... */ }
}
```

App Router里按方法分开，职责清晰，不怕一个文件几百行if-else。

> 从Pages Router迁移到App Router的API路由，最大的感受是：从"一个函数处理所有"变成了"每个方法各司其职"。代码量没减少，但可读性翻倍。

### 7.1.3 运行环境：Edge Runtime vs Node.js Runtime

Route Handler可以指定运行环境，这是个经常被忽略但很关键的选型。

```typescript
// 指定Edge Runtime
export const runtime = 'edge'

// 指定Node.js Runtime（默认）
export const runtime = 'nodejs'
```

| 维度 | Edge Runtime | Node.js Runtime |
|------|-------------|-----------------|
| 冷启动 | 极快（<50ms） | 较慢（几百ms到几秒） |
| API限制 | 只有Web API子集 | 完整Node.js API |
| 适用场景 | 轻量处理、边缘计算 | 数据库操作、重计算 |
| 包大小限制 | 1-4MB | 无限制 |
| 典型用例 | A/B测试、重定向、认证检查 | CRUD、文件处理、数据库查询 |

怕浪猫踩过的坑：在Edge Runtime里用了`fs`模块，本地没问题，部署Vercel直接报错。Edge环境没有Node.js原生模块，只有Web标准的Fetch、Crypto、TextEncoder等。

选型建议：不确定就默认`nodejs`，只有需要极低延迟且不依赖Node原生模块时才用`edge`。

### 7.1.4 请求生命周期：接收→处理→响应

一个API请求在Next.js中的完整生命周期：

```
客户端请求
    ↓
middleware.ts (全局拦截)
    ↓
Route Handler匹配 (基于目录路由)
    ↓
Runtime执行 (Edge或Node.js)
    ↓
业务逻辑处理 (你的代码)
    ↓
NextResponse返回
    ↓
客户端收到响应
```

关键点：middleware.ts在Route Handler之前执行，可以在这里做认证、日志、限流等横切关注点。但middleware本身跑在Edge Runtime，不能用Node原生API。

### 7.1.5 API路由的部署模式：Serverless与自托管

| 部署模式 | 特点 | 适用场景 |
|---------|------|---------|
| Serverless (Vercel) | 按需启动、自动扩缩、有冷启动 | 中小流量、成本敏感 |
| 自托管 (Docker/PM2) | 常驻进程、无冷启动、完全控制 | 大流量、需要长连接 |
| Edge Functions | 边缘节点、全球低延迟 | 全球分发、轻量处理 |

> Serverless的冷启动不是bug，是架构特性。理解这一点，你就知道为什么要把API设计成无状态的了。

## 7.2 GET/POST/PUT/DELETE接口开发

### 7.2.1 GET接口：查询数据的Request/Response

GET接口最简单，但也最容易忽略细节。

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const page = Number(searchParams.get('page') ?? '1')
  const limit = Number(searchParams.get('limit') ?? '10')

  const posts = await db.post.findMany({
    skip: (page - 1) * limit,
    take: limit,
  })

  return NextResponse.json({
    code: 0,
    data: posts,
    pagination: { page, limit, total: posts.length }
  })
}
```

注意`request.nextUrl.searchParams`是Next.js扩展的URL解析，比标准`new URL(request.url).searchParams`更方便。

### 7.2.2 POST接口：请求数据解析与入库

POST接口的核心是请求体解析。Next.js提供了灵活的body读取方式：

```typescript
export async function POST(request: NextRequest) {
  // JSON body
  const json = await request.json()

  // FormData (文件上传)
  // const formData = await request.formData()

  // 纯文本
  // const text = await request.text()

  if (!json.title) {
    return NextResponse.json(
      { code: 1, message: 'title不能为空' },
      { status: 400 }
    )
  }

  const post = await db.post.create({ data: json })
  return NextResponse.json({ code: 0, data: post }, { status: 201 })
}
```

> body只能读取一次。如果你需要多次使用请求体，先存到变量里。这是流式API的标准行为，不是Next.js的限制。

### 7.2.3 PUT接口：全量更新与部分更新

PUT语义是全量替换，PATCH语义是部分更新。但实际开发中很多人混用。

```typescript
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await request.json()
  const post = await db.post.update({
    where: { id: Number(params.id) },
    data: body,
  })
  return NextResponse.json({ code: 0, data: post })
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await request.json()
  const post = await db.post.update({
    where: { id: Number(params.id) },
    data: body,
  })
  return NextResponse.json({ code: 0, data: post })
}
```

### 7.2.4 DELETE接口：资源删除与软删除

```typescript
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // 硬删除
  await db.post.delete({ where: { id: Number(params.id) } })

  // 软删除（推荐）
  // await db.post.update({
  //   where: { id: Number(params.id) },
  //   data: { deletedAt: new Date() }
  // })

  return NextResponse.json({ code: 0, message: '删除成功' })
}
```

怕浪猫的建议：生产环境永远用软删除。数据是资产，删了就没了，但`deletedAt`字段随时能恢复。

### 7.2.5 HTTP方法语义与RESTful规范

| 方法 | 语义 | 幂等 | 安全 | 典型状态码 |
|------|------|------|------|-----------|
| GET | 查询 | 是 | 是 | 200 |
| POST | 创建 | 否 | 否 | 201 |
| PUT | 全量更新 | 是 | 否 | 200 |
| PATCH | 部分更新 | 否 | 否 | 200 |
| DELETE | 删除 | 是 | 否 | 200/204 |

> RESTful不是教条，是约定。约定的价值在于：别人不用看你的代码，只看HTTP方法就知道你要干什么。

## 7.3 动态API路由与参数接收

### 7.3.1 动态参数路由：app/api/posts/[id]/route.ts

```
app/api/posts/[id]/route.ts     → /api/posts/123
app/api/posts/[id]/comments/route.ts → /api/posts/123/comments
```

参数通过第二个参数传入：

```typescript
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = params.id
  const post = await db.post.findUnique({ where: { id: Number(id) } })
  if (!post) {
    return NextResponse.json({ code: 1, message: '不存在' }, { status: 404 })
  }
  return NextResponse.json({ code: 0, data: post })
}
```

### 7.3.2 查询参数：URLSearchParams解析

```typescript
// /api/posts?page=2&limit=20&tag=nextjs
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const page = parseInt(searchParams.get('page') ?? '1', 10)
  const limit = parseInt(searchParams.get('limit') ?? '10', 10)
  const tag = searchParams.get('tag') ?? undefined

  const where = tag ? { tags: { has: tag } } : {}
  const posts = await db.post.findMany({
    where,
    skip: (page - 1) * limit,
    take: limit,
  })
  return NextResponse.json({ code: 0, data: posts })
}
```

### 7.3.3 请求体解析：JSON、FormData、URLSearchParams

```typescript
export async function POST(request: NextRequest) {
  const contentType = request.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    const data = await request.json()
    // 处理JSON
  } else if (contentType.includes('multipart/form-data')) {
    const formData = await request.formData()
    const file = formData.get('file') as File
    // 处理文件上传
  } else if (contentType.includes('application/x-www-form-urlencoded')) {
    const text = await request.text()
    const params = new URLSearchParams(text)
    // 处理表单
  }
}
```

### 7.3.4 路由参数验证与类型安全

直接用`Number(params.id)`有隐患——如果传进来的是`abc`呢？用Zod做验证：

```typescript
import { z } from 'zod'

const paramsSchema = z.object({
  id: z.coerce.number().int().positive(),
})

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const result = paramsSchema.safeParse(params)
  if (!result.success) {
    return NextResponse.json(
      { code: 1, message: '参数错误', errors: result.error.flatten() },
      { status: 400 }
    )
  }
  const { id } = result.data
  // ...
}
```

### 7.3.5 捕获所有路由在API中的应用

```
app/api/[...slug]/route.ts → /api/a/b/c
```

```typescript
export async function GET(
  request: NextRequest,
  { params }: { params: { slug: string[] } }
) {
  const path = params.slug.join('/')
  // /api/files/docs/readme → slug = ['files', 'docs', 'readme']
  return NextResponse.json({ path })
}
```

典型用例：文件路径映射、嵌套分类查询、GraphQL端点转发。

## 7.4 请求校验、统一响应体封装

### 7.4.1 请求参数校验：Zod schema验证

Zod是TypeScript生态最流行的运行时验证库，和类型系统完美配合。

```typescript
import { z } from 'zod'

const createPostSchema = z.object({
  title: z.string().min(1).max(100),
  content: z.string().min(1),
  tags: z.array(z.string()).optional().default([]),
  published: z.boolean().optional().default(false),
})

export async function POST(request: NextRequest) {
  const body = await request.json()
  const result = createPostSchema.safeParse(body)

  if (!result.success) {
    return NextResponse.json(
      { code: 1, message: '验证失败', errors: result.error.issues },
      { status: 400 }
    )
  }

  // result.data 类型自动推断，无需手动定义
  const post = await db.post.create({ data: result.data })
  return NextResponse.json({ code: 0, data: post }, { status: 201 })
}
```

> Zod最大的价值不是验证，而是验证后的数据类型自动推断。一份schema，运行时验证和编译时类型全搞定。

### 7.4.2 统一响应体设计：code/message/data

```typescript
// lib/api-response.ts
type ApiResponse<T> = {
  code: number
  message: string
  data?: T
}

export function success<T>(data: T, message = '成功') {
  return NextResponse.json<ApiResponse<T>>(
    { code: 0, message, data },
    { status: 200 }
  )
}

export function error(message: string, code = 1, status = 400) {
  return NextResponse.json<ApiResponse<never>>(
    { code, message },
    { status }
  )
}
```

使用时：

```typescript
import { success, error } from '@/lib/api-response'

export async function GET() {
  const posts = await db.post.findMany()
  return success(posts)
}
```

### 7.4.3 错误响应的统一格式

```typescript
// lib/api-error.ts
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public code: number,
    message: string
  ) {
    super(message)
  }
}

// 在Route Handler中使用try-catch
export async function GET() {
  try {
    const posts = await db.post.findMany()
    return success(posts)
  } catch (e) {
    if (e instanceof ApiError) {
      return error(e.message, e.code, e.statusCode)
    }
    return error('服务器内部错误', 500, 500)
  }
}
```

### 7.4.4 分页响应的标准结构

```typescript
type PaginatedResponse<T> = {
  code: number
  message: string
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

export function paginated<T>(
  data: T[],
  page: number,
  limit: number,
  total: number
) {
  return NextResponse.json<PaginatedResponse<T>>({
    code: 0,
    message: '成功',
    data,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  })
}
```

### 7.4.5 API版本管理策略

**URL路径版本**：最直观，`/api/v1/posts`、`/api/v2/posts`。优点是一眼看出版本，缓存友好；缺点是URL变更需要前端配合修改。

```
app/api/v1/posts/route.ts   → /api/v1/posts
app/api/v2/posts/route.ts   → /api/v2/posts
```

**Header版本**：URL不变，通过请求头`Accept-Version: 1.0`区分版本。优点是URL干净；缺点是不够直观，调试不方便。

**查询参数版本**：`/api/posts?version=1`。最简单但最不推荐，容易被忽略且缓存不友好。

> 版本管理不是技术问题，是沟通问题。你的API版本策略，本质上是在告诉调用方："我可以改变，但不会突然抛弃你。"

## 7.5 跨域CORS配置与解决方案

### 7.5.1 同源策略与CORS原理

同源策略（Same-Origin Policy）是浏览器的安全机制，它限制一个源的网页访问另一个源的资源。所谓"同源"指三个相同：协议、域名、端口。

CORS（Cross-Origin Resource Sharing，跨域资源共享）是W3C标准，允许服务器声明哪些外部源可以访问自己的资源。核心流程：

```
浏览器发起请求
    ↓
检查是否跨域
    ↓ (是)
简单请求 → 直接发送，服务器返回Access-Control-Allow-Origin
复杂请求 → 先发OPTIONS预检请求
    ↓
服务器返回预检结果
    ↓ (允许)
浏览器发送真实请求
    ↓
服务器返回响应 + CORS头
```

简单请求 vs 复杂请求的关键区别：

| 维度 | 简单请求 | 复杂请求 |
|------|---------|---------|
| 方法 | GET/HEAD/POST | PUT/DELETE/PATCH |
| Content-Type | text/plain/multipart/form-data/application/x-www-form-urlencoded | application/json |
| 自定义头 | 无 | 有 |
| 预检请求 | 不需要 | 需要OPTIONS |

### 7.5.2 Next.js中配置CORS响应头

在Route Handler中手动设置CORS头：

```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://example.com',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
}

export async function GET(request: NextRequest) {
  const response = NextResponse.json({ code: 0, data: [] })
  Object.entries(corsHeaders).forEach(([key, value]) => {
    response.headers.set(key, value)
  })
  return response
}

// 处理预检请求
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: corsHeaders,
  })
}
```

更优雅的方案：封装CORS工具函数。

```typescript
// lib/cors.ts
export function withCors(response: NextResponse) {
  response.headers.set('Access-Control-Allow-Origin', '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Max-Age', '86400')
  return response
}
```

### 7.5.3 预检请求（Preflight）处理

浏览器对复杂请求会自动发送OPTIONS预检请求。如果服务器没有正确响应，真实请求不会发出。

```typescript
// 统一处理预检
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  })
}
```

### 7.5.4 Credentials跨域与Cookie传递

默认CORS不携带Cookie。要支持跨域Cookie：

```typescript
// 服务端
response.headers.set('Access-Control-Allow-Origin', 'https://example.com') // 不能用*
response.headers.set('Access-Control-Allow-Credentials', 'true')

// 客户端
fetch('/api/posts', { credentials: 'include' })
```

注意：`Allow-Credentials: true`时，`Allow-Origin`不能是`*`，必须指定具体域名。

> 跨域带Cookie的坑：Allow-Origin不能用通配符，Allow-Credentials必须为true，Cookie的SameSite属性要设为none且Secure。三个条件缺一不可。

### 7.5.5 常见跨域错误排查清单

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| No 'Access-Control-Allow-Origin' header | 服务器没设置CORS头 | 添加Allow-Origin响应头 |
| Credentials flag is true, but Allow-Origin is * | 携带Cookie时用了通配符 | 改为具体域名 |
| Preflight request failed | OPTIONS请求被拦截 | 确保OPTIONS方法被正确处理 |
| Allow-Headers不含自定义头 | 请求头不在允许列表 | 在Allow-Headers中添加 |
| SameSite cookie blocked | Cookie的SameSite策略 | 设置SameSite=None; Secure |

## 7.6 中间件Middleware拦截接口请求

### 7.6.1 middleware.ts拦截API请求

Next.js的middleware.ts可以拦截所有请求，包括API路由。

```typescript
// middleware.ts (项目根目录)
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  // 只拦截API请求
  if (request.nextUrl.pathname.startsWith('/api')) {
    // 认证检查
    const token = request.headers.get('authorization')
    if (!token) {
      return NextResponse.json(
        { code: 1, message: '未授权' },
        { status: 401 }
      )
    }
  }
  return NextResponse.next()
}

export const config = {
  matcher: '/api/:path*',
}
```

### 7.6.2 请求日志记录中间件

```typescript
export function middleware(request: NextRequest) {
  const start = Date.now()
  const response = NextResponse.next()

  const duration = Date.now() - start
  console.log(JSON.stringify({
    method: request.method,
    path: request.nextUrl.pathname,
    status: response.status,
    duration: `${duration}ms`,
    timestamp: new Date().toISOString(),
  }))

  return response
}
```

### 7.6.3 限流中间件：防止API滥用

简单的内存限流（单实例适用）：

```typescript
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()

export function middleware(request: NextRequest) {
  const ip = request.ip ?? 'anonymous'
  const now = Date.now()
  const limit = 100 // 每分钟100次
  const windowMs = 60 * 1000

  const record = rateLimitMap.get(ip)
  if (!record || now > record.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + windowMs })
  } else {
    record.count++
    if (record.count > limit) {
      return NextResponse.json(
        { code: 429, message: '请求过于频繁' },
        { status: 429 }
      )
    }
  }
  return NextResponse.next()
}
```

生产环境建议用Redis做分布式限流。

> 限流不是为了拒绝用户，是为了保护系统。好的限流策略应该是"放行正常用户，拦截异常流量"，而不是一刀切。

### 7.6.4 认证中间件：JWT校验

```typescript
import { jwtVerify } from 'jose'

export async function middleware(request: NextRequest) {
  const token = request.headers.get('authorization')?.replace('Bearer ', '')
  if (!token) {
    return NextResponse.json({ code: 1, message: '未授权' }, { status: 401 })
  }

  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET!)
    const { payload } = await jwtVerify(token, secret)
    // 将用户信息传递给Route Handler
    const requestHeaders = new Headers(request.headers)
    requestHeaders.set('x-user-id', String(payload.userId))
    return NextResponse.next({
      request: { headers: requestHeaders },
    })
  } catch {
    return NextResponse.json({ code: 1, message: 'Token无效' }, { status: 401 })
  }
}
```

### 7.6.5 中间件执行顺序与性能影响

```
请求进入
    ↓
middleware.ts (Edge Runtime)
    ↓
NextResponse.next() → 请求继续
    ↓
Route Handler (Node.js/Edge Runtime)
    ↓
响应返回
```

性能注意事项：

| 关注点 | 建议 |
|--------|------|
| middleware执行时间 | 尽量<5ms，避免重计算 |
| 避免数据库查询 | middleware跑在Edge，不能直接连数据库 |
| matcher精确匹配 | 不要拦截所有路由，只拦截需要的 |
| 缓存验证结果 | JWT解析结果可以缓存在Edge |
| 避免链式中间件 | Next.js只支持单个middleware.ts，用if-else分支 |

## 7.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| Route Handler | app/api/目录下的route.ts，按HTTP方法导出函数 |
| 运行环境 | Edge Runtime轻量快速，Node.js Runtime功能完整 |
| CRUD开发 | GET查询、POST创建、PUT更新、DELETE删除 |
| 动态路由 | [id]参数路由、[...slug]捕获所有路由 |
| 请求校验 | Zod schema验证 + 类型自动推断 |
| 统一响应 | code/message/data标准结构 |
| CORS | 预检请求、Credentials跨域、排查清单 |
| Middleware | 认证、日志、限流的统一拦截 |

### 课后练习

1. 实现一个完整的`/api/posts` CRUD接口，包含分页、搜索、排序
2. 用Zod给每个接口添加请求参数校验
3. 封装统一的响应体工具函数，替换所有接口的返回值
4. 实现一个限流中间件，每个IP每分钟最多请求60次
5. 配置CORS允许`http://localhost:3000`跨域访问，并支持Cookie传递

> 练习题不难，但每一道都对应一个生产场景。能独立做完这5道题，你的API开发能力就够用了。

觉得有用？收藏起来，下次写API直接照抄这些模板。

你遇到过CORS跨域的坑吗？评论区说说你是怎么解决的。

关注怕浪猫，下期我们讲Next.js的数据库集成与ORM（Object-Relational Mapping，对象关系映射）方案——从Prisma到Drizzle，帮你选对数据层工具。

**系列进度 7/16**

**怕浪猫说**

API路由是全栈开发的分水岭。只会写前端的人永远停在"页面"层面，能写好API的人才能掌控整个应用的数据流。这篇文章里的每个代码片段都是我在实际项目中反复用到的模板，不是 demo 级别的玩具代码。把它们变成你自己的工具箱，下次写API就不用从零开始了。下一章见。

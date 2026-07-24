# 第9章 Next.js中间件与请求拦截实战

90%的Next.js项目都需要登录态校验，但80%的人把认证逻辑写在每个页面里，改一次需求要改几十个文件。其实一个middleware.ts文件就能搞定全局拦截，代码量从几百行降到几十行。

我是怕浪猫，一个擅长把复杂架构问题拆成简单方案的全栈开发者。这章我们来彻底搞懂Next.js中间件——从运行原理到登录校验、权限控制、安全头配置，全部实战拆解。

## 9.1 中间件运行时机与核心特性

### 9.1.1 中间件在请求生命周期中的位置

Next.js中间件在请求到达页面或API路由之前执行，是整个请求生命周期的第一道关卡。

```
客户端发起请求
    ↓
Edge节点接收
    ↓
middleware.ts 执行 ← 在这里拦截
    ↓
NextResponse.next() → 放行
    ↓
路由匹配（页面/API/静态资源）
    ↓
Server Component / Route Handler 执行
    ↓
响应返回客户端
```

关键点：中间件在路由匹配之前执行，这意味着你可以在请求到达任何业务逻辑之前做拦截。这个位置决定了中间件适合做什么：认证、重定向、日志、A/B测试。不适合做什么：数据库查询、重计算、需要Node.js原生模块的操作。

### 9.1.2 Edge Runtime：中间件的运行环境限制

中间件运行在Edge Runtime上，不是Node.js Runtime。这意味着：

| 能力 | Edge Runtime | Node.js Runtime |
|------|-------------|-----------------|
| Fetch API | 可用 | 可用 |
| Web Crypto | 可用 | 可用 |
| TextEncoder/Decoder | 可用 | 可用 |
| fs (文件系统) | 不可用 | 可用 |
| child_process | 不可用 | 可用 |
| 大部分npm包 | 受限 | 可用 |
| 数据库驱动 | 不可用 | 可用 |

```typescript
// 这些在中间件里可以用
import { jwtVerify } from 'jose' // jose使用Web Crypto API
import { NextRequest, NextResponse } from 'next/server'

// 这些在中间件里不能用
// import fs from 'fs'              // 报错
// import { PrismaClient } from '@prisma/client' // 报错
// import bcrypt from 'bcrypt'      // 可能报错(依赖Node API)
```

> Edge Runtime不是阉割版的Node.js，它是一套基于Web标准的独立运行时。理解这一点，你就不会在中间件里写数据库查询了。

### 9.1.3 中间件能做什么、不能做什么

**能做：**
- 登录态校验与重定向
- 权限分级控制
- 请求日志记录
- A/B测试分流
- 国际化(i18n)路由
- 自定义请求头注入
- 安全头(CSP、HSTS)配置
- 限流(简单的内存限流)

**不能做（或不建议做）：**
- 数据库查询（Edge不支持）
- 复杂的密码学运算（用jose替代jsonwebtoken）
- 文件系统操作
- 长时间阻塞操作
- 需要Node.js原生模块的操作

### 9.1.4 中间件与Server Components的执行顺序

```
请求进入
    ↓
middleware.ts (Edge Runtime)
    ↓
NextResponse.next()
    ↓
Layout.tsx (Server Component)
    ↓
Page.tsx (Server Component)
    ↓
渲染完成，返回HTML
```

中间件可以通过修改请求头来传递数据给Server Components：

```typescript
export function middleware(request: NextRequest) {
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-user-id', '12345')
  requestHeaders.set('x-user-role', 'admin')

  return NextResponse.next({
    request: { headers: requestHeaders },
  })
}

// 在Server Component中读取
export default function Page({ headers }) {
  const userId = headers.get('x-user-id')
  // ...
}
```

### 9.1.5 中间件性能影响与优化

中间件在每个匹配的请求上都会执行，性能影响不可忽视。

| 优化策略 | 说明 |
|---------|------|
| 精确matcher | 只拦截需要的路由，不要用`/*` |
| 避免重计算 | JWT解析结果缓存在Edge |
| 减少IO操作 | 不做数据库查询，不做文件读取 |
| 控制执行时间 | 目标<5ms |
| 避免大依赖 | Edge有包大小限制(1-4MB) |

## 9.2 middleware.ts全局中间件配置

### 9.2.1 middleware.ts文件的放置位置

middleware.ts必须放在项目根目录或src目录下：

```
项目根目录/
├── middleware.ts      ← 放这里
├── app/
├── pages/
└── ...

// 或者使用了src目录
项目根目录/
├── src/
│   ├── middleware.ts  ← 或者放这里
│   └── app/
```

注意：整个项目只能有一个middleware.ts文件。Next.js不支持多个中间件文件链式调用。

### 9.2.2 基本结构：matcher配置与export default

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  console.log(`请求: ${request.method} ${request.nextUrl.pathname}`)
  return NextResponse.next()
}

// matcher决定哪些请求经过中间件
export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
}
```

### 9.2.3 NextRequest对象：请求信息访问

```typescript
export function middleware(request: NextRequest) {
  // 路径信息
  const pathname = request.nextUrl.pathname
  const searchParams = request.nextUrl.searchParams

  // 请求头
  const authHeader = request.headers.get('authorization')
  const userAgent = request.headers.get('user-agent')

  // Cookie
  const token = request.cookies.get('token')?.value

  // 客户端信息
  const ip = request.ip
  const geo = request.geo // 需要Vercel等平台支持

  // 请求方法
  const method = request.method

  return NextResponse.next()
}
```

### 9.2.4 NextResponse对象：响应控制

```typescript
export function middleware(request: NextRequest) {
  // 放行请求
  return NextResponse.next()

  // 重定向
  return NextResponse.redirect(new URL('/login', request.url))

  // 重写URL(浏览器地址栏不变，但实际渲染另一个路由)
  return NextResponse.rewrite(new URL('/dashboard/v2', request.url))

  // 返回JSON(用于API拦截)
  return NextResponse.json({ code: 1, message: '未授权' }, { status: 401 })

  // 修改请求头后放行
  const headers = new Headers(request.headers)
  headers.set('x-custom', 'value')
  return NextResponse.next({ request: { headers } })
}
```

### 9.2.5 中间件的配置项与matcher语法

```typescript
export const config = {
  // 方式1：字符串数组
  matcher: ['/dashboard/:path*', '/api/:path*'],

  // 方式2：带有条件判断的对象
  matcher: [
    {
      source: '/dashboard/:path*',
      missing: [{ type: 'header', key: 'next-router-prefetch' }],
    },
  ],

  // 方式3：排除特定路径(使用negative lookahead)
  // matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

## 9.3 路由匹配规则与指定页面拦截

### 9.3.1 matcher配置：精确匹配与通配符

| 模式 | 含义 | 示例匹配 |
|------|------|---------|
| `/dashboard` | 精确匹配 | 仅/dashboard |
| `/dashboard/:path*` | 匹配子路径 | /dashboard, /dashboard/settings |
| `/dashboard/:path` | 匹配一级子路径 | /dashboard/settings（不匹配/dashboard/a/b） |
| `/:path*` | 匹配所有路径 | 所有路径 |

### 9.3.2 排除特定路径：negative lookahead

```typescript
export const config = {
  // 匹配所有路径，但排除api、_next/static、favicon.ico
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

这个正则的含义：

```
(?!api|_next/static|_next/image|favicon.ico)  → negative lookahead
表示：匹配后面不是这些路径的所有路径
```

> negative lookahead是中间件配置里最实用的正则技巧。一个表达式就能排除所有不需要拦截的路径，比写一堆if-else干净多了。

### 9.3.3 多路径匹配策略

```typescript
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/admin/:path*',
    '/api/:path*',
    '/profile/:path*',
  ],
}
```

也可以在中间件内部根据路径做不同处理：

```typescript
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/dashboard') || pathname.startsWith('/profile')) {
    return authMiddleware(request)
  }

  if (pathname.startsWith('/admin')) {
    return adminMiddleware(request)
  }

  if (pathname.startsWith('/api')) {
    return apiMiddleware(request)
  }

  return NextResponse.next()
}
```

### 9.3.4 静态资源与API路由的拦截控制

```typescript
export const config = {
  matcher: [
    // 排除静态资源
    '/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)',
  ],
}
```

如果需要对API和页面做不同的拦截逻辑，建议在中间件内部分支处理，而不是写两个matcher。

### 9.3.5 路由匹配的调试与验证

```typescript
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl
  console.log(`[Middleware] ${request.method} ${pathname}${search}`)

  const response = NextResponse.next()
  response.headers.set('x-middleware-path', pathname)
  return response
}
```

在浏览器开发者工具的Network面板中查看响应头`x-middleware-path`，可以确认中间件是否执行。

## 9.4 登录态校验与未登录重定向

### 9.4.1 Cookie中的token读取与校验

```typescript
import { jwtVerify } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET!)

async function verifyToken(token: string) {
  try {
    const { payload } = await jwtVerify(token, secret)
    return payload
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const payload = await verifyToken(token)
  if (!payload) {
    // token无效，清除Cookie并重定向
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('token')
    return response
  }

  return NextResponse.next()
}
```

注意：中间件里用`jose`而不是`jsonwebtoken`，因为`jose`基于Web Crypto API，兼容Edge Runtime。

> 选库不是看哪个star多，是看哪个适配你的运行环境。jsonwebtoken在Node.js里好用，放到Edge就报错。jose两个环境都支持，没有理由不用它。

### 9.4.2 未登录重定向到登录页

```typescript
export async function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  // 已经在登录页，不需要拦截
  if (pathname === '/login' || pathname === '/register') {
    return NextResponse.next()
  }

  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/profile/:path*', '/admin/:path*'],
}
```

### 9.4.3 登录后回跳原页面

```typescript
// 中间件重定向时携带原路径
const loginUrl = new URL('/login', request.url)
loginUrl.searchParams.set('from', pathname)
return NextResponse.redirect(loginUrl)

// 登录页面读取from参数，登录成功后重定向回去
'use client'
import { useRouter, useSearchParams } from 'next/navigation'

export function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const from = searchParams.get('from') ?? '/dashboard'

  const handleLogin = async () => {
    // 登录逻辑...
    router.push(from)
  }
  return <button onClick={handleLogin}>登录</button>
}
```

### 9.4.4 多种登录态方案：Cookie vs Session vs JWT

| 方案 | 存储 | 校验方式 | 优点 | 缺点 |
|------|------|---------|------|------|
| Cookie (签名) | Cookie | 服务端验签 | 简单 | 不适合分布式 |
| Session | Cookie(存ID) + 服务端存储 | 查Session存储 | 安全、可撤销 | 需要Session存储 |
| JWT | Cookie或Header | 验签(无状态) | 无状态、跨域 | 无法主动撤销 |

中间件中的方案选择：

```typescript
// 方案1：JWT in Cookie (推荐)
const token = request.cookies.get('token')?.value
const payload = await jwtVerify(token, secret)

// 方案2：JWT in Authorization Header
const token = request.headers.get('authorization')?.replace('Bearer ', '')

// 方案3：Session (中间件只能检查Session ID是否存在，不能查Session存储)
const sessionId = request.cookies.get('session')?.value
if (!sessionId) return redirectToLogin()
```

### 9.4.5 登录态校验的安全注意事项

| 安全风险 | 防御措施 |
|---------|---------|
| Cookie被窃取 | HttpOnly + Secure + SameSite |
| Token过期处理 | 中间件检查exp字段，过期则刷新或重定向 |
| Token被篡改 | 使用强密钥签名，中间件验签 |
| 重定向开放漏洞 | 只允许站内重定向，验证from参数 |
| 时序攻击 | 用固定时间比较函数 |

## 9.5 权限分级控制与角色访问限制

### 9.5.1 RBAC模型

RBAC（Role-Based Access Control，基于角色的访问控制）是最常用的权限模型：

```
用户 → 角色 → 权限
 ↓       ↓       ↓
张三 → admin → [read, write, delete]
李四 → editor → [read, write]
王五 → viewer → [read]
```

### 9.5.2 中间件中读取用户角色信息

```typescript
export async function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  if (!token) return NextResponse.redirect(new URL('/login', request.url))

  const payload = await verifyToken(token)
  if (!payload) return NextResponse.redirect(new URL('/login', request.url))

  const role = payload.role as string
  const pathname = request.nextUrl.pathname

  // 将角色信息注入请求头，供下游使用
  const headers = new Headers(request.headers)
  headers.set('x-user-role', role)
  headers.set('x-user-id', String(payload.userId))

  return NextResponse.next({ request: { headers } })
}
```

### 9.5.3 页面级权限拦截

```typescript
const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ['/admin', '/dashboard', '/profile', '/settings'],
  editor: ['/dashboard', '/profile', '/editor'],
  viewer: ['/dashboard', '/profile'],
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  if (!token) return NextResponse.redirect(new URL('/login', request.url))

  const payload = await verifyToken(token)
  if (!payload) return NextResponse.redirect(new URL('/login', request.url))

  const role = payload.role as string
  const pathname = request.nextUrl.pathname
  const allowedPaths = ROLE_PERMISSIONS[role] ?? []

  const hasPermission = allowedPaths.some(
    path => pathname === path || pathname.startsWith(path + '/')
  )

  if (!hasPermission) {
    return NextResponse.redirect(new URL('/403', request.url))
  }

  return NextResponse.next()
}
```

> 权限控制的核心思路很简单：先认证（你是谁），再授权（你能做什么）。中间件做粗粒度的路由级拦截，页面内做细粒度的操作级控制。

### 9.5.4 动态权限路由配置

```typescript
// 从外部数据源加载权限映射(缓存到Edge)
let permissionCache: { data: Record<string, string[]>; expiry: number } | null = null

async function getPermissions() {
  if (permissionCache && Date.now() < permissionCache.expiry) {
    return permissionCache.data
  }

  const res = await fetch(`${process.env.API_URL}/permissions`, {
    next: { revalidate: 300 } // 5分钟缓存
  })
  const data = await res.json()
  permissionCache = { data, expiry: Date.now() + 300 * 1000 }
  return data
}
```

### 9.5.5 权限变更后的实时生效

中间件运行在Edge，权限缓存也在Edge节点。权限变更后：
- 等待缓存过期（最长5分钟）
- 或者通过API主动清除缓存
- 或者让用户重新登录获取新Token

## 9.6 请求头、响应头自定义配置

### 9.6.1 添加自定义请求头

```typescript
export function middleware(request: NextRequest) {
  const headers = new Headers(request.headers)
  headers.set('x-request-id', crypto.randomUUID())
  headers.set('x-timestamp', Date.now().toString())

  return NextResponse.next({ request: { headers } })
}
```

### 9.6.2 修改响应头：CORS、安全头

```typescript
export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  // CORS头
  response.headers.set('Access-Control-Allow-Origin', 'https://example.com')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')

  // 安全头
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  return response
}
```

### 9.6.3 中间件中设置Cookie

```typescript
export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  // 设置Cookie
  response.cookies.set('visitor_id', crypto.randomUUID(), {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 60 * 60 * 24 * 365, // 1年
    path: '/',
  })

  // 删除Cookie
  // response.cookies.delete('old_token')

  return response
}
```

### 9.6.4 请求头注入与下游组件读取

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const headers = new Headers(request.headers)

  if (token) {
    headers.set('x-token', token)
  }

  return NextResponse.next({ request: { headers } })
}

// 在Server Component中读取
import { headers } from 'next/headers'

export default function Dashboard() {
  const headersList = headers()
  const token = headersList.get('x-token')
  // 用token请求数据...
}
```

### 9.6.5 常用安全头配置清单

| 安全头 | 作用 | 推荐值 |
|--------|------|--------|
| X-Content-Type-Options | 阻止MIME类型嗅探 | nosniff |
| X-Frame-Options | 防止点击劫持 | DENY或SAMEORIGIN |
| X-XSS-Protection | XSS过滤 | 1; mode=block |
| Referrer-Policy | 控制Referer信息 | strict-origin-when-cross-origin |
| Content-Security-Policy | 内容安全策略 | 按需配置 |
| Strict-Transport-Security | 强制HTTPS | max-age=31536000; includeSubDomains |
| Permissions-Policy | 控制浏览器特性 | 按需配置 |

> 安全头就像给应用穿了件防弹衣，穿上不会碍事，不穿一旦中弹就追悔莫及。复制这张清单，逐项配置到你的中间件里。

## 9.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| 中间件运行时机 | 请求到达路由之前，Edge Runtime |
| 运行环境限制 | 只有Web API，无Node.js原生模块 |
| matcher配置 | 精确匹配、通配符、negative lookahead |
| 登录态校验 | Cookie + JWT(jose) + 重定向 |
| 权限控制 | RBAC模型、页面级拦截、角色路由 |
| 请求头/响应头 | 注入请求头、安全头配置、Cookie操作 |

### 课后练习

1. 实现一个完整的登录态校验中间件，包含token验证、过期处理、回跳原页面
2. 用RBAC模型实现三种角色(admin/editor/viewer)的页面访问控制
3. 配置完整的安全响应头清单，并验证每个头是否生效
4. 实现一个请求ID注入中间件，在响应头中返回x-request-id
5. 用negative lookahead编写matcher，排除所有静态资源和API路由

> 这5道练习题做完，你的中间件功夫就入门了。别小看入门，很多人连matcher都写不对。

觉得有用？收藏起来，下次配置中间件直接照抄这些模板。

你用过Next.js中间件做过什么有趣的功能？评论区聊聊。

关注怕浪猫，下期我们讲Next.js的认证与授权方案——从JWT到OAuth（Open Authorization，开放授权），从Session到Passkey，帮你选对认证方案，告别"登录功能写一周"的窘境。

**系列进度 9/16**

**怕浪猫说**

中间件这个功能看起来不起眼，但它是Next.js全栈能力的关键拼图。没有中间件，认证逻辑散落在每个页面里；有了中间件，一个文件管全局。好的架构不是把所有功能都堆上去，而是找到那个"四两拨千斤"的切入点。中间件就是这样的切入点。下一章见。

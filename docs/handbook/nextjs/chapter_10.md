# 第10章 身份认证与权限系统开发

认证功能写了3遍，每次都踩不同的坑。第一遍Cookie没设HttpOnly，第二遍Token存在localStorage被XSS偷了，第三遍Refresh Token没轮换被重放攻击。认证系统的坑，一次踩完比分三次踩好。

我是怕浪猫，一个在认证系统上栽过跟头也爬起来过的全栈开发者。这章我把身份认证和权限系统的完整方案拆透——从方案选型到代码实现，从安全防御到用户体验，帮你一次避开我踩过的所有坑。

## 10.1 前端认证方案对比：Cookie、Token、Session

### 10.1.1 Cookie认证：浏览器自动携带的便利与风险

Cookie是最经典的认证方案。浏览器在每次请求时自动携带Cookie，不需要前端手动处理。

```
登录流程：
客户端 → POST /api/login (账号密码) → 服务端
服务端 → Set-Cookie: token=xxx; HttpOnly; Secure → 客户端
后续请求：
客户端 → Cookie: token=xxx (自动携带) → 服务端
```

```typescript
// 登录接口设置Cookie
export async function POST(request: NextRequest) {
  const { email, password } = await request.json()
  const user = await verifyUser(email, password)
  if (!user) return error('账号或密码错误', 1, 401)

  const token = await generateToken(user)
  const response = success({ user })
  response.cookies.set('token', token, {
    httpOnly: true,   // JS不能读取，防XSS
    secure: true,     // 只在HTTPS下传输
    sameSite: 'strict', // 防CSRF
    maxAge: 60 * 60 * 24 * 7, // 7天
    path: '/',
  })
  return response
}
```

| 优点 | 缺点 |
|------|------|
| 浏览器自动携带，开发简单 | 有CSRF风险(需SameSite防御) |
| HttpOnly防XSS窃取 | 大小限制4KB |
| 跨标签页共享 | 需要处理Cookie过期 |
| 服务端可随时清除 | 不适合跨域API |

### 10.1.2 Token认证：无状态的JWT方案

JWT（JSON Web Token，JSON网络令牌）是无状态认证方案，服务端不需要存储Session。

```
JWT结构：Header.Payload.Signature
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEyMywiZXhwIjoxNjk..._.signature
```

```typescript
import { SignJWT, jwtVerify } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET!)

// 生成Token
async function generateToken(user: { id: number; email: string }) {
  return new SignJWT({ userId: user.id, email: user.email })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('7d')
    .setIssuedAt()
    .sign(secret)
}

// 验证Token
async function verifyToken(token: string) {
  const { payload } = await jwtVerify(token, secret)
  return payload
}
```

> JWT的核心矛盾：无状态带来的是扩展性，失去的是控制力。你签发的Token在过期之前无法撤销——除非引入黑名单，而黑名单又让它变成了有状态。

### 10.1.3 Session认证：服务端有状态方案

```
登录流程：
客户端 → POST /api/login → 服务端创建Session
服务端 → Set-Cookie: session_id=xxx → 客户端
后续请求：
客户端 → Cookie: session_id=xxx → 服务端查Session存储 → 返回用户信息
```

```typescript
// 使用Redis存储Session
import { Redis } from '@upstash/redis'

const redis = new Redis({ url: process.env.REDIS_URL!, token: process.env.REDIS_TOKEN! })

export async function createSession(userId: number) {
  const sessionId = crypto.randomUUID()
  await redis.set(`session:${sessionId}`, JSON.stringify({ userId }), { ex: 86400 })
  return sessionId
}

export async function getSession(sessionId: string) {
  const data = await redis.get(`session:${sessionId}`)
  return data ? JSON.parse(data as string) : null
}

export async function destroySession(sessionId: string) {
  await redis.del(`session:${sessionId}`)
}
```

### 10.1.4 三种方案的适用场景对比

| 维度 | Cookie | JWT | Session |
|------|--------|-----|---------|
| 状态 | 可有可无 | 无状态 | 有状态 |
| 存储 | 浏览器 | 任意位置 | 服务端 |
| 扩展性 | 中 | 高 | 低 |
| 安全性 | 高(HttpOnly) | 中(存储位置关键) | 高 |
| 可撤销 | 是 | 否(需黑名单) | 是 |
| 跨域 | 难 | 容易 | 难 |
| 适合场景 | 传统Web | API/微服务 | 需要强控制 |

### 10.1.5 Next.js认证方案选型决策

```
你的场景是什么？
├── 单体应用，同域访问 → Cookie + JWT (HttpOnly)
├── 前后端分离，跨域API → JWT in Authorization Header
├── 微服务架构 → JWT (无状态，各服务独立验签)
├── 需要强制下线能力 → Session (Redis)
└── 不确定 → Cookie + JWT (最通用)
```

> 没有最好的认证方案，只有最适合你场景的方案。怕浪猫的选择：Next.js全栈项目用Cookie + JWT(HttpOnly)，兼顾安全和开发效率。

## 10.2 JWT令牌生成、校验与过期处理

### 10.2.1 JWT结构：Header、Payload、Signature

```
Header:  { "alg": "HS256", "typ": "JWT" }     → Base64URL编码
Payload: { "userId": 123, "email": "...", "exp": 169... } → Base64URL编码
Signature: HMAC-SHA256(base64(header) + "." + base64(payload), secret)
```

三部分用`.`连接：`header.payload.signature`

注意：JWT的Header和Payload只是Base64编码，不是加密。不要在Payload里放敏感信息（密码、密钥等）。

### 10.2.2 令牌生成：签名算法与密钥管理

```typescript
import { SignJWT } from 'jose'

// HS256 (对称加密，最常用)
const secret = new TextEncoder().encode(process.env.JWT_SECRET!)
const token = await new SignJWT({ userId: 123, role: 'admin' })
  .setProtectedHeader({ alg: 'HS256' })
  .setExpirationTime('15m')  // Access Token短过期
  .setIssuedAt()
  .sign(secret)

// RS256 (非对称加密，适合微服务)
// const privateKey = await importPKCS8(process.env.JWT_PRIVATE_KEY!, 'RS256')
// const token = await new SignJWT(payload)
//   .setProtectedHeader({ alg: 'RS256' })
//   .sign(privateKey)
```

密钥管理最佳实践：

| 策略 | 说明 |
|------|------|
| 密钥长度 | HS256至少32字符 |
| 密钥来源 | 环境变量，不硬编码 |
| 密钥轮换 | 定期更换，支持多密钥并存 |
| 密钥隔离 | 不同环境(开发/生产)用不同密钥 |

### 10.2.3 令牌校验：签名验证与过期判断

```typescript
import { jwtVerify } from 'jose'

async function verifyToken(token: string) {
  try {
    const { payload } = await jwtVerify(token, secret, {
      algorithms: ['HS256'],
      // 可选：验证签发者
      issuer: 'my-app',
      // 可选：验证受众
      audience: 'my-app-users',
    })
    return { valid: true, payload }
  } catch (error) {
    // Token过期、签名错误、格式错误都会到这里
    return { valid: false, error: error instanceof Error ? error.message : '未知错误' }
  }
}
```

> Token校验最常见的报错是"jwt expired"。别慌，这是正常行为——过期了就刷新，不是Bug。

### 10.2.4 Access Token与Refresh Token双令牌策略

```
登录成功
    ↓
签发 Access Token (15分钟) + Refresh Token (7天)
    ↓
客户端用 Access Token 请求API
    ↓
Access Token 过期
    ↓
客户端用 Refresh Token 请求 /api/refresh
    ↓
服务端验证 Refresh Token，签发新的 Access Token
    ↓
Refresh Token 过期 → 重新登录
```

```typescript
// 登录时签发双令牌
export async function login(user: User) {
  const accessToken = await new SignJWT({ userId: user.id, role: user.role })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('15m')
    .sign(secret)

  const refreshToken = await new SignJWT({ userId: user.id, type: 'refresh' })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('7d')
    .sign(refreshSecret)

  return { accessToken, refreshToken }
}

// 刷新接口
export async function POST(request: NextRequest) {
  const { refreshToken } = await request.json()
  try {
    const { payload } = await jwtVerify(refreshToken, refreshSecret)
    const newAccessToken = await new SignJWT({ userId: payload.userId })
      .setProtectedHeader({ alg: 'HS256' })
      .setExpirationTime('15m')
      .sign(secret)
    return success({ accessToken: newAccessToken })
  } catch {
    return error('Refresh Token无效，请重新登录', 1, 401)
  }
}
```

### 10.2.5 令牌存储方案：Cookie vs localStorage

| 维度 | HttpOnly Cookie | localStorage |
|------|----------------|--------------|
| XSS防护 | 安全(JS不可读) | 不安全(JS可读) |
| CSRF防护 | 需SameSite防御 | 安全(不自动携带) |
| 跨域 | 需要配置CORS+Credentials | 容易(手动附加) |
| 服务端访问 | 直接读取 | 需要客户端传递 |
| 推荐 | Access Token | 不推荐存储Token |

> 结论：Token存在HttpOnly Cookie里最安全。localStorage虽然方便，但一个XSS漏洞就能偷走你的Token。

## 10.3 用户登录、注册、退出功能全实现

### 10.3.1 注册接口：密码加密与用户创建

```typescript
// app/api/auth/register/route.ts
import { hash } from 'bcryptjs'

export async function POST(request: NextRequest) {
  const { email, password, name } = await request.json()

  // 检查用户是否已存在
  const existing = await db.user.findUnique({ where: { email } })
  if (existing) return error('邮箱已注册', 1, 409)

  // 加密密码（bcrypt，不要用MD5/SHA）
  const hashedPassword = await hash(password, 12)

  // 创建用户
  const user = await db.user.create({
    data: { email, password: hashedPassword, name },
  })

  return success({ id: user.id, email: user.email }, '注册成功')
}
```

### 10.3.2 登录接口：身份验证与令牌签发

```typescript
// app/api/auth/login/route.ts
import { compare } from 'bcryptjs'

export async function POST(request: NextRequest) {
  const { email, password } = await request.json()

  const user = await db.user.findUnique({ where: { email } })
  if (!user) return error('账号或密码错误', 1, 401)

  const valid = await compare(password, user.password)
  if (!valid) return error('账号或密码错误', 1, 401)

  // 签发Token
  const accessToken = await generateAccessToken(user)
  const refreshToken = await generateRefreshToken(user)

  const response = success({ user: { id: user.id, email: user.email } })
  response.cookies.set('access_token', accessToken, {
    httpOnly: true, secure: true, sameSite: 'strict',
    maxAge: 15 * 60, path: '/',
  })
  response.cookies.set('refresh_token', refreshToken, {
    httpOnly: true, secure: true, sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60, path: '/',
  })
  return response
}
```

### 10.3.3 登录页面：表单设计与提交

```tsx
// app/login/page.tsx
'use client'
import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const from = searchParams.get('from') ?? '/dashboard'
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    const formData = new FormData(e.currentTarget)

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.get('email'),
        password: formData.get('password'),
      }),
    })

    if (res.ok) {
      router.push(from)
    } else {
      const data = await res.json()
      alert(data.message)
    }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" placeholder="邮箱" required />
      <input name="password" type="password" placeholder="密码" required />
      <button type="submit" disabled={loading}>登录</button>
    </form>
  )
}
```

### 10.3.4 退出登录：令牌清除与重定向

```typescript
// app/api/auth/logout/route.ts
export async function POST(request: NextRequest) {
  const response = success({}, '退出成功')
  response.cookies.delete('access_token')
  response.cookies.delete('refresh_token')
  return response
}
```

```tsx
// 退出按钮
'use client'
import { useRouter } from 'next/navigation'

export function LogoutButton() {
  const router = useRouter()
  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }
  return <button onClick={handleLogout}>退出登录</button>
}
```

### 10.3.5 登录态持久化与自动恢复

```tsx
// app/layout.tsx
import { cookies } from 'next/headers'
import { verifyToken } from '@/lib/auth'

export default async function RootLayout({ children }) {
  const cookieStore = cookies()
  const token = cookieStore.get('access_token')?.value
  let user = null

  if (token) {
    const result = await verifyToken(token)
    if (result.valid) {
      user = { id: result.payload.userId, role: result.payload.role }
    }
  }

  return (
    <html>
      <body>
        <UserProvider user={user}>{children}</UserProvider>
      </body>
    </html>
  )
}
```

## 10.4 服务端组件鉴权与客户端组件鉴权

### 10.4.1 Server Components中读取Cookie鉴权

```tsx
import { cookies } from 'next/headers'
import { verifyToken } from '@/lib/auth'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const cookieStore = cookies()
  const token = cookieStore.get('access_token')?.value

  if (!token) redirect('/login')

  const result = await verifyToken(token)
  if (!result.valid) redirect('/login')

  // 已认证，渲染页面
  const posts = await db.post.findMany({
    where: { authorId: result.payload.userId },
  })

  return <PostList posts={posts} />
}
```

### 10.4.2 Client Components中的鉴权策略

```tsx
'use client'
import { useUser } from '@/hooks/useUser'

export function EditButton({ postId }: { postId: number }) {
  const { user, loading } = useUser()

  if (loading) return null
  if (!user) return null

  return <button onClick={() => edit(postId)}>编辑</button>
}
```

### 10.4.3 middleware统一鉴权拦截

```typescript
// middleware.ts
export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const { pathname } = request.nextUrl

  // 公开页面不拦截
  if (['/login', '/register'].includes(pathname)) {
    return NextResponse.next()
  }

  if (!token) {
    return NextResponse.redirect(new URL(`/login?from=${pathname}`, request.url))
  }

  const result = await verifyToken(token)
  if (!result.valid) {
    return NextResponse.redirect(new URL(`/login?from=${pathname}`, request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/profile/:path*', '/admin/:path*'],
}
```

### 10.4.4 服务端鉴权vs客户端鉴权的安全边界

| 维度 | 服务端鉴权 | 客户端鉴权 |
|------|-----------|-----------|
| 安全性 | 高(用户无法绕过) | 低(可被篡改) |
| 体验 | 重定向有延迟 | 即时显示/隐藏 |
| 适用 | 路由保护、数据获取 | UI元素显示控制 |
| 必须 | 是 | 辅助 |

> 客户端鉴权只是体验优化，不是安全措施。真正的安全防线必须在服务端。客户端可以隐藏按钮，但用户手动发请求你拦不住。

### 10.4.5 混合鉴权架构设计

```
请求进入
    ↓
middleware.ts (粗粒度：是否登录？)
    ↓
Server Component (中粒度：有无权限访问此页面？)
    ↓
API Route Handler (细粒度：有无权限执行此操作？)
    ↓
数据库层 (最细粒度：只能操作自己的数据)
```

## 10.5 页面级、按钮级权限控制

### 10.5.1 页面级权限：路由拦截与重定向

```typescript
// middleware.ts 中的权限拦截
const ROLE_ROUTES: Record<string, string[]> = {
  admin: ['/admin', '/dashboard', '/settings'],
  editor: ['/dashboard', '/editor'],
  user: ['/dashboard', '/profile'],
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  if (!token) return redirectToLogin(request)

  const result = await verifyToken(token)
  if (!result.valid) return redirectToLogin(request)

  const role = result.payload.role as string
  const pathname = request.nextUrl.pathname
  const allowed = ROLE_ROUTES[role] ?? []

  if (!allowed.some(p => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL('/403', request.url))
  }

  return NextResponse.next()
}
```

### 10.5.2 按钮级权限：条件渲染与权限组件

```tsx
// components/Permission.tsx
'use client'
import { useUser } from '@/hooks/useUser'

type PermissionProps = {
  permission: string
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function Permission({ permission, children, fallback = null }: PermissionProps) {
  const { user } = useUser()
  if (!user?.permissions?.includes(permission)) return <>{fallback}</>
  return <>{children}</>
}

// 使用
<Permission permission="post:delete" fallback={<span>无权删除</span>}>
  <button onClick={handleDelete}>删除</button>
</Permission>
```

### 10.5.3 权限配置表设计

```typescript
// 权限定义
const PERMISSIONS = {
  // 文章管理
  'post:read': ['admin', 'editor', 'user'],
  'post:write': ['admin', 'editor'],
  'post:delete': ['admin'],
  // 用户管理
  'user:read': ['admin'],
  'user:write': ['admin'],
  'user:delete': ['admin'],
  // 系统设置
  'settings:read': ['admin'],
  'settings:write': ['admin'],
} as const

// 检查权限
function hasPermission(role: string, permission: string): boolean {
  return PERMISSIONS[permission]?.includes(role) ?? false
}
```

> 权限配置表是权限系统的"单一数据源"。所有权限判断都查这张表，不要在代码各处硬编码角色判断。

### 10.5.4 动态权限菜单实现

```tsx
'use client'
import { useUser } from '@/hooks/useUser'

const MENU_ITEMS = [
  { label: '仪表盘', path: '/dashboard', permission: 'dashboard:read' },
  { label: '文章管理', path: '/posts', permission: 'post:read' },
  { label: '用户管理', path: '/users', permission: 'user:read' },
  { label: '系统设置', path: '/settings', permission: 'settings:read' },
]

export function NavMenu() {
  const { user } = useUser()
  const visibleItems = MENU_ITEMS.filter(
    item => !user?.permissions || user.permissions.includes(item.permission)
  )
  return (
    <nav>
      {visibleItems.map(item => (
        <a key={item.path} href={item.path}>{item.label}</a>
      ))}
    </nav>
  )
}
```

### 10.5.5 权限变更的实时响应

权限变更有两种场景：
- 用户角色被管理员修改 → 需要重新签发Token或等Token过期
- 前端操作后权限变化 → 更新本地状态

```typescript
// 方案1：短过期Token + 频繁刷新
// Access Token 15分钟过期，每次刷新时从数据库读取最新角色

// 方案2：WebSocket通知
// 管理员修改角色后，通过WebSocket通知用户刷新Token

// 方案3：版本号校验
// Token中存角色版本号，中间件比对数据库中的当前版本号
```

## 10.6 记住登录、自动续期功能开发

### 10.6.1 记住登录：持久化Cookie

```typescript
export async function POST(request: NextRequest) {
  const { email, password, remember } = await request.json()
  // ...验证逻辑...

  const accessToken = await generateAccessToken(user)
  const response = success({ user })

  response.cookies.set('access_token', accessToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: remember ? 30 * 24 * 60 * 60 : 15 * 60, // 30天 or 15分钟
    path: '/',
  })

  if (remember) {
    const refreshToken = await generateRefreshToken(user)
    response.cookies.set('refresh_token', refreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      maxAge: 30 * 24 * 60 * 60, // 30天
      path: '/',
    })
  }

  return response
}
```

### 10.6.2 Access Token过期的自动刷新

```typescript
// lib/auth.ts
export async function refreshAccessToken(refreshToken: string) {
  try {
    const { payload } = await jwtVerify(refreshToken, refreshSecret)
    const newAccessToken = await new SignJWT({ userId: payload.userId })
      .setProtectedHeader({ alg: 'HS256' })
      .setExpirationTime('15m')
      .sign(secret)
    return newAccessToken
  } catch {
    return null
  }
}

// 中间件中自动刷新
export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('access_token')?.value
  const refreshToken = request.cookies.get('refresh_token')?.value

  // Access Token有效，直接放行
  if (accessToken) {
    const result = await verifyToken(accessToken)
    if (result.valid) return NextResponse.next()
  }

  // Access Token过期，尝试刷新
  if (refreshToken) {
    const newToken = await refreshAccessToken(refreshToken)
    if (newToken) {
      const response = NextResponse.next()
      response.cookies.set('access_token', newToken, {
        httpOnly: true, secure: true, sameSite: 'strict',
        maxAge: 15 * 60, path: '/',
      })
      return response
    }
  }

  return NextResponse.redirect(new URL('/login', request.url))
}
```

> 自动续期的核心思路：让用户无感知地保持登录状态。Access Token短过期保证安全，Refresh Token长过期保证体验。两者结合，安全与体验兼得。

### 10.6.3 Refresh Token轮换策略

每次使用Refresh Token刷新时，签发一个新的Refresh Token，旧的作废：

```typescript
export async function refresh(refreshToken: string) {
  const result = await verifyRefreshToken(refreshToken)
  if (!result.valid) return null

  // 检查是否已被使用（需要Redis存储已用Token）
  const used = await redis.get(`used_refresh:${refreshToken}`)
  if (used) {
    // Refresh Token被重放！可能被盗用，清除所有Token
    await redis.del(`refresh:${result.payload.userId}`)
    return { error: 'Token已被使用，请重新登录' }
  }

  // 标记旧Token为已用
  await redis.set(`used_refresh:${refreshToken}`, '1', { ex: 7 * 86400 })

  // 签发新Token对
  const newAccessToken = await generateAccessToken(result.payload)
  const newRefreshToken = await generateRefreshToken(result.payload)
  return { accessToken: newAccessToken, refreshToken: newRefreshToken }
}
```

### 10.6.4 多设备登录管理

```typescript
// 每个设备一个Session记录
interface DeviceSession {
  deviceId: string
  deviceInfo: string // User-Agent
  userId: number
  refreshToken: string
  createdAt: Date
  lastActiveAt: Date
}

// 登录时创建Session
async function login(user: User, request: NextRequest) {
  const deviceId = crypto.randomUUID()
  await db.deviceSession.create({
    data: {
      deviceId,
      deviceInfo: request.headers.get('user-agent') ?? 'Unknown',
      userId: user.id,
      refreshToken: hashedRefreshToken,
      createdAt: new Date(),
      lastActiveAt: new Date(),
    },
  })
  return { deviceId, accessToken, refreshToken }
}

// 查看所有登录设备
async function getDevices(userId: number) {
  return db.deviceSession.findMany({
    where: { userId },
    orderBy: { lastActiveAt: 'desc' },
  })
}

// 踢掉某个设备
async function revokeDevice(deviceId: string) {
  await db.deviceSession.delete({ where: { deviceId } })
}
```

### 10.6.5 强制下线与令牌撤销

JWT本身不支持撤销，但可以通过以下方式实现：

| 方案 | 实现 | 代价 |
|------|------|------|
| Token黑名单 | Redis存储已撤销Token | 有状态 |
| 短过期+不刷新 | Access Token 5分钟过期 | 频繁登录 |
| 版本号校验 | Token存版本号，中间件比对 | 多一次查询 |
| 撤销所有Token | 修改JWT_SECRET | 所有用户重新登录 |

> 强制下线是JWT的"软肋"。如果你的业务频繁需要强制下线，Session方案可能更合适。技术选型就是这样，没有银弹，只有取舍。

## 10.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| 认证方案 | Cookie(自动携带)、JWT(无状态)、Session(有状态) |
| 双令牌 | Access Token(15m) + Refresh Token(7d) |
| 密码安全 | bcrypt加密，不用MD5/SHA |
| Token存储 | HttpOnly Cookie最安全 |
| 鉴权层次 | middleware → Server Component → API → DB |
| 权限控制 | 页面级(middleware) + 按钮级(组件) |
| 自动续期 | Refresh Token轮换 + 自动刷新 |

### 课后练习

1. 实现完整的注册、登录、退出功能，使用Cookie + JWT双令牌
2. 实现Access Token自动刷新的中间件
3. 用RBAC模型实现admin/editor/user三种角色的页面级权限控制
4. 实现一个Permission组件，支持按钮级权限控制
5. 实现多设备登录管理，支持查看所有设备和踢掉指定设备

> 认证系统是全栈应用的"城门"。城门不牢，里面的功能再多也是白搭。这5道题做完，你的城门就够坚固了。

觉得有用？收藏起来，下次写认证系统直接照抄这些代码模板。

你的认证系统用的什么方案？Cookie、JWT还是Session？评论区聊聊你的选型理由。

关注怕浪猫，下期我们讲Next.js的部署与运维方案——从Vercel到自托管Docker部署，从环境变量管理到CI/CD（Continuous Integration/Continuous Deployment，持续集成/持续部署）流水线，帮你把项目从开发环境推到生产环境。

**系列进度 10/16**

**怕浪猫说**

认证系统是我在每个新项目里花时间最多的模块。不是因为难，而是因为安全容不得半点马虎。一个HttpOnly没设，一个Token存了localStorage，一个Refresh Token没轮换——任何一个疏忽都可能在某天变成安全事故。这篇文章里的每个细节都是我用教训换来的，希望它能帮你少走弯路。下一章见。

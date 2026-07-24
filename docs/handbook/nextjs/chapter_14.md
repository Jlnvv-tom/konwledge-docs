# 第14章 异常处理、日志与项目调试

线上报错了，用户截图发过来，你盯着一段"Something went wrong"发呆——不知道哪个页面、哪个用户、什么操作触发的。如果你提前配好了错误边界和Sentry，这会儿你已经在看完整的错误堆栈了，而不是对着一张截图猜。

我是怕浪猫，一个在生产环境翻过无数次车的全栈开发者。这章把Next.js异常处理和调试的完整体系讲透——从错误边界到Sentry监控，从调试技巧到高频报错排查，帮你把"线上救火"变成"线上防火"。

## 14.1 全局错误边界与错误组件开发

### 14.1.1 error.tsx：路由级错误边界

Next.js App Router中，每个路由段都可以有自己的错误边界：

```
app/
├── layout.tsx
├── error.tsx          ← 根级错误边界
├── page.tsx
├── posts/
│   ├── error.tsx      ← posts路由错误边界
│   ├── page.tsx
│   └── [slug]/
│       ├── error.tsx  ← 文章详情错误边界
│       └── page.tsx
```

```tsx
// app/posts/error.tsx
'use client'

export default function PostsError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>文章列表加载失败</h2>
      <p>{error.message}</p>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

注意：error.tsx必须是Client Component（'use client'），因为错误恢复需要用户交互。

### 14.1.2 global-error.tsx：根布局级错误处理

error.tsx无法捕获layout.tsx中的错误。如果根布局出错，需要global-error.tsx：

```tsx
// app/global-error.tsx
'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h2>应用发生严重错误</h2>
        <p>{error.message}</p>
        <button onClick={reset}>重试</button>
      </body>
    </html>
  )
}
```

> error.tsx捕获页面错误，global-error.tsx捕获布局错误。两者必须同时配置，否则根布局的异常会导致白屏。

### 14.1.3 错误组件的props

| prop | 类型 | 说明 |
|------|------|------|
| error | Error & { digest?: string } | 错误对象，digest是服务端错误标识 |
| reset | () => void | 重置错误状态，重新渲染路由段 |

```tsx
'use client'
import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // 上报错误
    console.error('路由错误:', error)
  }, [error])

  return (
    <div>
      <h2>出错了</h2>
      <p>错误标识: {error.digest}</p>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

### 14.1.4 错误恢复机制

```tsx
'use client'
import { useState } from 'react'

export default function ErrorBoundary({ error, reset }: { error: Error; reset: () => void }) {
  const [retryCount, setRetryCount] = useState(0)

  const handleReset = () => {
    setRetryCount(c => c + 1)
    reset()  // 重新渲染出错的路由段
  }

  return (
    <div>
      <h2>出错了 (重试次数: {retryCount})</h2>
      {retryCount >= 3 ? (
        <p>多次重试失败，请刷新页面或联系客服</p>
      ) : (
        <button onClick={handleReset}>重试</button>
      )}
    </div>
  )
}
```

### 14.1.5 错误边界与Suspense组合

```tsx
// app/posts/page.tsx
import { Suspense } from 'react'
import PostsList from '@/components/PostsList'
import PostsError from './error'

export default function PostsPage() {
  return (
    <Suspense fallback={<div>加载中...</div>}>
      <PostsList />
    </Suspense>
  )
}
// error.tsx自动作为错误边界，不需要手动包裹
```

## 14.2 服务端错误与客户端错误统一处理

### 14.2.1 服务端错误分类

| 错误类型 | 原因 | 处理方式 |
|---------|------|---------|
| API错误 | 外部服务异常 | 重试/降级 |
| 数据库错误 | 连接失败/语法错误 | 事务回滚/告警 |
| 超时错误 | 请求超时 | 返回超时提示 |
| 验证错误 | 参数不合法 | 返回字段错误信息 |
| 认证错误 | Token无效/过期 | 重定向登录 |

### 14.2.2 客户端错误分类

| 错误类型 | 原因 | 处理方式 |
|---------|------|---------|
| 渲染错误 | 组件异常 | error.tsx捕获 |
| 网络错误 | fetch失败 | 重试/提示 |
| 用户操作 | 表单验证失败 | 内联提示 |
| Hydration | 服务端/客户端不匹配 | 修复不匹配 |

### 14.2.3 统一错误响应格式

```typescript
// lib/api-response.ts
interface ErrorResponse {
  code: number
  message: string
  details?: Record<string, string>
  digest?: string
}

// 自定义错误类
export class AppError extends Error {
  constructor(
    public code: number,
    message: string,
    public details?: Record<string, string>
  ) {
    super(message)
  }
}

// 统一错误处理
export function handleError(error: unknown): ErrorResponse {
  if (error instanceof AppError) {
    return { code: error.code, message: error.message, details: error.details }
  }
  if (error instanceof Error) {
    return { code: 500, message: '服务器内部错误' }
  }
  return { code: 500, message: '未知错误' }
}
```

> 错误处理的核心原则：对用户展示友好信息，对开发者保留完整堆栈。永远不要把数据库错误信息直接返回给用户。

### 14.2.4 错误码体系

```typescript
// 错误码定义
const ERROR_CODES = {
  // 通用错误 1xxx
  UNKNOWN: 1000,
  VALIDATION: 1001,
  RATE_LIMIT: 1002,

  // 认证错误 2xxx
  UNAUTHORIZED: 2001,
  TOKEN_EXPIRED: 2002,
  FORBIDDEN: 2003,

  // 业务错误 3xxx
  POST_NOT_FOUND: 3001,
  POST_ALREADY_PUBLISHED: 3002,
} as const
```

### 14.2.5 错误信息的安全过滤

| 输出对象 | 展示内容 | 隐藏内容 |
|---------|---------|---------|
| 用户 | 友好提示 + 错误码 | 堆栈、SQL、内部路径 |
| 开发者(Sentry) | 完整错误信息 | 无 |
| 日志 | 错误信息 + 上下文 | 敏感数据(密码/Token) |

## 14.3 自定义500/404错误页面

### 14.3.1 自定义404页面

```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="not-found">
      <h1>404</h1>
      <p>你访问的页面不存在</p>
      <Link href="/">返回首页</Link>
    </div>
  )
}
```

### 14.3.2 自定义500错误页面

```tsx
// app/error.tsx
'use client'

export default function ServerError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="error-500">
      <h1>500</h1>
      <p>服务器开小差了</p>
      <p>错误编号: {error.digest}</p>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

### 14.3.3 错误页面设计

好的错误页面应该包含：
- 明确的错误代码（404/500）
- 简短的解释说明
- 操作引导（返回首页/重试）
- 保持品牌一致的设计

```tsx
export default function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '80px 20px' }}>
      <h1 style={{ fontSize: '72px', margin: 0 }}>404</h1>
      <p style={{ color: '#666' }}>这个页面像是被猫叼走了</p>
      <div style={{ marginTop: '24px' }}>
        <Link href="/">返回首页</Link>
        <span style={{ margin: '0 12px' }}>|</span>
        <Link href="/search">搜索内容</Link>
      </div>
    </div>
  )
}
```

> 错误页面不是"技术问题"，是"用户体验问题"。一个好的404页面能把"用户流失"变成"用户留下"。

### 14.3.4 错误页面中的导航引导

```tsx
'use client'
import { useRouter } from 'next/navigation'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter()
  return (
    <div>
      <h2>出错了</h2>
      <button onClick={reset}>重试</button>
      <button onClick={() => router.push('/')}>回首页</button>
      <button onClick={() => router.back()}>返回上一页</button>
    </div>
  )
}
```

### 14.3.5 错误页面监控

```tsx
'use client'
import { useEffect } from 'react'

export default function Error({ error }: { error: Error }) {
  useEffect(() => {
    // 上报到Sentry
    import('@sentry/nextjs').then(Sentry => {
      Sentry.captureException(error)
    })
  }, [error])
  // ...
}
```

## 14.4 开发环境调试技巧

### 14.4.1 VS Code调试配置

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 9229,
      "type": "node",
      "console": "integratedTerminal"
    },
    {
      "name": "Next.js: debug client-side",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000"
    }
  ]
}
```

### 14.4.2 服务端调试

```bash
# 启动时开启Node.js Inspector
NODE_OPTIONS='--inspect' npm run dev

# 在VS Code中打断点，代码执行到断点处暂停
```

### 14.4.3 客户端调试

React DevTools是调试React应用的必备工具：
- Components面板：查看组件树、props、state
- Profiler面板：记录渲染性能
- 在浏览器Console中直接调试

### 14.4.4 条件断点与日志断点

```typescript
// VS Code条件断点示例
// 在行号左侧点击设置断点，右键编辑条件
// 条件: userId === 123
// 日志断点: "处理用户 {userId}"

// 代码中的条件日志
if (process.env.NODE_ENV === 'development') {
  console.log('调试信息:', { userId, path: request.nextUrl.pathname })
}
```

> 调试不是"加console.log然后看输出"。善用断点、条件断点、日志断点，你的调试效率能提升10倍。

### 14.4.5 Next.js开发工具

| 工具 | 用途 |
|------|------|
| React DevTools | 组件树、Props、State |
| Next.js DevTools | 路由、缓存、Server Components |
| Network面板 | 请求/响应检查 |
| Performance面板 | 性能分析 |

## 14.5 生产环境错误监控与上报

### 14.5.1 Sentry集成

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
  release: process.env.GIT_COMMIT_SHA,
  beforeSend(event) {
    // 脱敏处理
    if (event.request?.headers) {
      delete event.request.headers.authorization
      delete event.request.headers.cookie
    }
    return event
  },
})
```

### 14.5.2 错误上报策略

| 策略 | 说明 | 目的 |
|------|------|------|
| 采样率 | 10%性能, 100%错误 | 控制成本 |
| 脱敏 | 删除headers中的Token | 安全 |
| 聚合 | 相同错误合并 | 减少噪音 |
| 释放标记 | 关联Git SHA | 定位版本 |

### 14.5.3 Source Map上传

```javascript
// next.config.js + @sentry/nextjs
const { withSentryConfig } = require('@sentry/nextjs')

module.exports = withSentryConfig(nextConfig, {
  org: 'my-org',
  project: 'my-project',
  silent: true,
  hideSourceMaps: true,  // 生产环境不暴露Source Map
})
```

> Source Map是错误定位的关键。没有Source Map，你看到的错误堆栈是一堆压缩后的变量名，根本不知道错在哪。CI构建时上传Source Map到Sentry，错误发生时就能看到原始代码位置。

### 14.5.4 告警规则

| 告警规则 | 阈值 | 通知方式 |
|---------|------|---------|
| 错误率突增 | > 5% (5分钟内) | 即时通知 |
| 新错误出现 | 之前未见过的错误 | 即时通知 |
| 重复错误 | 同一错误 > 100次/小时 | 汇总通知 |
| 性能下降 | P95 > 2s | 日报告 |

### 14.5.5 错误复盘流程

```
1. 收到告警 → 查看Sentry错误详情
2. 定位版本 → 查看最近发布
3. 复现问题 → 在本地或预发环境复现
4. 修复代码 → 编写测试用例
5. 发布修复 → 监控错误是否消除
6. 复盘记录 → 记录根因和预防措施
```

## 14.6 常见报错问题排查

### 14.6.1 Hydration Mismatch排查

```
错误信息: Hydration failed because the initial UI does not match what was rendered on the server.
```

常见原因：

| 原因 | 解决方案 |
|------|---------|
| 使用Date.now()/Math.random() | 移到useEffect中 |
| 使用window/localStorage | 加typeof window判断 |
| 条件渲染依赖客户端状态 | 使用useEffect延迟渲染 |
| 服务端/客户端时区不同 | 统一用UTC |

```tsx
// 错误示例
export function Clock() {
  const time = new Date().toLocaleTimeString()
  return <div>{time}</div>  // 服务端和客户端渲染时间不同
}

// 正确示例
'use client'
import { useState, useEffect } from 'react'

export function Clock() {
  const [time, setTime] = useState('')
  useEffect(() => {
    setTime(new Date().toLocaleTimeString())
  }, [])
  return <div>{time}</div>
}
```

> Hydration Mismatch是Next.js最常见的报错之一。核心原因只有一个：服务端和客户端渲染的内容不一致。找到那个"不一致"的源头，问题就解决了。

### 14.6.2 "use client"相关报错

| 报错 | 原因 | 解决 |
|------|------|------|
| useState在Server Component中使用 | 缺少'use client' | 文件顶部加'use client' |
| 事件处理器在Server Component中 | Server组件不支持事件 | 拆分为Client组件 |
| useContext在Server Component中 | Context只在Client端可用 | 加'use client' |

### 14.6.3 ESLint/TypeScript构建错误

```bash
# 查看详细错误
npm run lint
npm run typecheck  # npx tsc --noEmit

# 忽略特定行的ESLint规则
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = getData()
```

### 14.6.4 路由404/重定向循环

```
重定向循环: /login → /dashboard → /login → /dashboard ...
```

常见原因：middleware拦截了/login页面，但/login是公开页面。

```typescript
// 修复：排除公开页面
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  // 排除公开路由
  if (['/login', '/register', '/'].includes(pathname)) {
    return NextResponse.next()
  }
  // 认证检查...
}
```

### 14.6.5 高频报错速查表

| 报错 | 原因 | 解决 |
|------|------|------|
| Hydration Mismatch | 服务端/客户端不一致 | useEffect延迟渲染 |
| use client missing | Hook在Server组件中 | 加'use client' |
| Redirect loop | middleware拦截了公开页面 | 排除公开路由 |
| 404 on dynamic route | generateStaticParams缺失 | 添加或用dynamic |
| Module not found | 导入路径错误 | 检查@/别名配置 |
| Text content did not match | 时间/随机值不一致 | 移到Client端 |

## 14.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| 错误边界 | error.tsx(路由级), global-error.tsx(根布局级) |
| 错误分类 | 服务端(API/DB/超时) vs 客户端(渲染/网络) |
| 404/500页面 | not-found.tsx, error.tsx |
| 调试技巧 | VS Code launch.json, React DevTools |
| 错误监控 | Sentry集成, Source Map, 告警规则 |
| 高频报错 | Hydration, use client, 重定向循环 |

### 课后练习

1. 为项目添加error.tsx和global-error.tsx，实现完整的错误边界
2. 配置VS Code调试，在Server Component中打断点
3. 接入Sentry，实现错误自动捕获和Source Map上传
4. 设计一个统一错误响应格式，包含错误码体系
5. 制造一个Hydration Mismatch错误，然后修复它

> 异常处理做得好不好，决定了你凌晨几点被叫起来。做得好，第二天看Sentry复盘；做得不好，凌晨3点爬起来修Bug。

觉得有用？收藏起来，下次遇到报错直接查高频报错速查表。

你遇到过最头疼的Next.js报错是什么？评论区聊聊。

关注怕浪猫，下期我们讲Next.js的部署与运维方案——从Vercel到Docker，从CI/CD到监控告警，帮你把项目稳稳地推到线上。

**系列进度 14/16**

**怕浪猫说**

异常处理是软件工程的"保险"——买了不希望用，但不买一旦出事就追悔莫及。这篇文章里的每个错误处理方案都是我在生产环境中被"教训"过的。希望你看了之后能少交点学费。下一章见。

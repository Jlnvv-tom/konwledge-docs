# 第16章 综合项目实战：全栈博客系统开发

学了15章Next.js，你能做一个完整项目了吗？能写组件，但不知道怎么组装成一个系统。能配API，但不知道数据库怎么设计。这章把前面学的所有知识串起来，从0到1做一个生产级全栈博客系统。

我是怕浪猫，一个喜欢用实战检验学习成果的全栈开发者。这是我们Next.js系列的最后一章，我会把前面15章的知识点全部整合到一个完整项目中——从需求分析到上线部署，从数据库设计到SEO优化，帮你把零散的知识变成完整的工程能力。

## 16.1 项目需求分析、技术选型与架构设计

### 16.1.1 核心功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| 用户 | 注册、登录、修改密码、头像 | P0 |
| 文章 | 发布、编辑、删除、草稿、分页 | P0 |
| 评论 | 发表、回复、删除 | P1 |
| 分类 | CRUD、树形结构 | P1 |
| 标签 | 多标签关联、标签云 | P1 |
| 搜索 | 全文搜索 | P2 |
| SEO | sitemap、结构化数据、OG | P0 |
| 后台 | 管理后台、数据统计 | P2 |

### 16.1.2 技术选型

```
前端：Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
后端：Next.js Route Handlers + Server Actions
数据库：PostgreSQL + Prisma ORM
认证：JWT (jose) + Cookie (HttpOnly)
部署：Docker + Nginx / Vercel
监控：Sentry
```

> 技术选型的原则不是"用最新的"，而是"用最合适的"。Next.js全栈方案让一个人就能完成从前端到数据库的全部开发，不需要额外学后端框架。对中小型项目来说，这是效率最高的选择。

### 16.1.3 架构设计

```
用户浏览器
    ↓ HTTPS
Nginx (反向代理 + HTTPS + gzip)
    ↓
Next.js Server (Node.js / Edge)
    ├── Server Components (SSR/SSG)
    ├── Route Handlers (API)
    ├── Server Actions (表单提交)
    └── Middleware (认证拦截)
    ↓
PostgreSQL (数据库)
    ↓
Redis (缓存/Session - 可选)
```

### 16.1.4 数据库ER模型

```
User (用户)
├── 1:N → Post (文章)
├── 1:N → Comment (评论)

Post (文章)
├── N:1 → User (作者)
├── N:1 → Category (分类)
├── N:N → Tag (标签)
├── 1:N → Comment (评论)

Comment (评论)
├── N:1 → Post (所属文章)
├── N:1 → User (评论者)
├── N:1 → Comment (父评论, 嵌套回复)

Category (分类)
├── N:1 → Category (父分类, 树形结构)
├── 1:N → Post (文章)

Tag (标签)
├── N:N → Post (文章)
```

### 16.1.5 项目目录结构

```
blog/
├── app/
│   ├── (auth)/login/page.tsx
│   ├── (auth)/register/page.tsx
│   ├── (main)/page.tsx          ← 首页
│   ├── (main)/posts/page.tsx    ← 文章列表
│   ├── (main)/posts/[slug]/page.tsx ← 文章详情
│   ├── (admin)/admin/page.tsx   ← 后台
│   ├── api/                     ← API路由
│   ├── error.tsx
│   ├── global-error.tsx
│   ├── layout.tsx
│   ├── not-found.tsx
│   ├── sitemap.ts
│   └── robots.ts
├── components/
├── lib/
├── prisma/
│   └── schema.prisma
├── public/
├── middleware.ts
├── next.config.js
└── tailwind.config.ts
```

## 16.2 项目初始化与工程化配置

### 16.2.1 创建项目

```bash
npx create-next-app@latest blog --typescript --tailwind --app --eslint
cd blog
npm install prisma @prisma/client jose bcryptjs zod
npm install -D @types/bcryptjs
```

### 16.2.2 工程化配置

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 100
}
```

```bash
# husky + lint-staged
npx husky init
echo "npx lint-staged" > .husky/pre-commit
```

### 16.2.3 数据库连接

```typescript
// lib/db.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient }

export const db = globalForPrisma.prisma || new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db
```

## 16.3 数据库模型设计

### 16.3.1 Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  password  String
  name      String
  avatar    String?
  role      Role    @default(USER)
  posts     Post[]
  comments  Comment[]
  createdAt DateTime @default(now())
}

model Post {
  id          Int       @id @default(autoincrement())
  title       String
  slug        String    @unique
  content     String
  excerpt     String
  coverImage  String?
  published   Boolean   @default(false)
  authorId    Int
  author      User      @relation(fields: [authorId], references: [id])
  categoryId  Int?
  category    Category? @relation(fields: [categoryId], references: [id])
  tags        Tag[]
  comments    Comment[]
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  @@index([authorId])
  @@index([published])
}

enum Role {
  ADMIN
  EDITOR
  USER
}
```

### 16.3.2 模型关系

| 关系类型 | 示例 | Prisma语法 |
|---------|------|-----------|
| 一对多 | User → Posts | `posts Post[]` + `author User @relation` |
| 多对一 | Post → Category | `category Category? @relation` |
| 多对多 | Post ↔ Tag | `tags Tag[]` + `posts Post[]` |
| 自引用 | Comment → Comment(父) | `parent Comment? @relation("ReplyRelation")` |

### 16.3.3 种子数据

```typescript
// prisma/seed.ts
import { hash } from 'bcryptjs'

async function main() {
  const admin = await db.user.create({
    data: {
      email: 'admin@example.com',
      password: await hash('password123', 12),
      name: 'Admin',
      role: 'ADMIN',
    },
  })

  await db.post.create({
    data: {
      title: 'Hello World',
      slug: 'hello-world',
      content: '第一篇博客文章',
      excerpt: '第一篇博客',
      authorId: admin.id,
      published: true,
    },
  })
}
```

## 16.4 用户模块开发

### 16.4.1 注册接口

```typescript
// app/api/auth/register/route.ts
import { hash } from 'bcryptjs'
import { db } from '@/lib/db'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2),
})

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { email, password, name } = schema.parse(body)

  const exists = await db.user.findUnique({ where: { email } })
  if (exists) return error('邮箱已注册', 1, 409)

  await db.user.create({
    data: { email, password: await hash(password, 12), name },
  })
  return success({}, '注册成功')
}
```

### 16.4.2 登录与JWT

```typescript
// app/api/auth/login/route.ts
import { compare } from 'bcryptjs'
import { SignJWT } from 'jose'

export async function POST(request: NextRequest) {
  const { email, password } = await request.json()
  const user = await db.user.findUnique({ where: { email } })
  if (!user || !await compare(password, user.password)) {
    return error('账号或密码错误', 1, 401)
  }

  const token = await new SignJWT({ userId: user.id, role: user.role })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('7d')
    .sign(new TextEncoder().encode(process.env.JWT_SECRET!))

  const res = success({ user: { id: user.id, name: user.name } })
  res.cookies.set('token', token, {
    httpOnly: true, secure: true, sameSite: 'strict',
    maxAge: 7 * 86400, path: '/',
  })
  return res
}
```

### 16.4.3 中间件鉴权

```typescript
// middleware.ts
import { jwtVerify } from 'jose'

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  if (['/login', '/register'].includes(pathname)) return NextResponse.next()
  if (!token) return NextResponse.redirect(new URL('/login', request.url))

  try {
    await jwtVerify(token, new TextEncoder().encode(process.env.JWT_SECRET!))
    return NextResponse.next()
  } catch {
    return NextResponse.redirect(new URL('/login', request.url))
  }
}

export const config = { matcher: ['/admin/:path*', '/dashboard/:path*'] }
```

## 16.5 博客文章模块

### 16.5.1 文章CRUD

```typescript
// app/api/posts/route.ts
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl
  const page = Number(searchParams.get('page') ?? 1)
  const limit = Number(searchParams.get('limit') ?? 10)

  const [posts, total] = await Promise.all([
    db.post.findMany({
      where: { published: true },
      include: { author: { select: { name: true } }, category: true },
      orderBy: { createdAt: 'desc' },
      skip: (page - 1) * limit,
      take: limit,
    }),
    db.post.count({ where: { published: true } }),
  ])

  return success({ posts, pagination: { page, limit, total } })
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const post = await db.post.create({
    data: { ...body, authorId: body.userId },
  })
  return success(post, '文章创建成功')
}
```

### 16.5.2 文章详情：SSG + ISR

```tsx
// app/posts/[slug]/page.tsx
import { notFound } from 'next/navigation'
import { db } from '@/lib/db'

export async function generateStaticParams() {
  const posts = await db.post.findMany({ where: { published: true } })
  return posts.map(p => ({ slug: p.slug }))
}

export default async function PostPage({ params }: { params: { slug: string } }) {
  const post = await db.post.findUnique({
    where: { slug: params.slug },
    include: { author: true, comments: true, tags: true },
  })
  if (!post) notFound()

  return <PostDetail post={post} />
}

// ISR: 每小时重新验证
export const revalidate = 3600
```

> SSG + ISR是博客系统的最佳渲染策略。构建时预生成静态页面，部署后每小时自动更新。用户访问的是静态HTML（最快），内容又能保持新鲜。

## 16.6 评论、分类、标签

### 16.6.1 嵌套评论

```typescript
// 获取嵌套评论
async function getComments(postId: number) {
  const comments = await db.comment.findMany({
    where: { postId, parentId: null },
    include: {
      author: { select: { name: true, avatar: true } },
      replies: {
        include: { author: { select: { name: true, avatar: true } } },
      },
    },
    orderBy: { createdAt: 'desc' },
  })
  return comments
}
```

### 16.6.2 分类树形结构

```typescript
async function getCategoryTree() {
  const categories = await db.category.findMany({
    include: { children: true },
    where: { parentId: null },
  })
  return categories
}
```

### 16.6.3 标签云

```typescript
async function getTagCloud() {
  const tags = await db.tag.findMany({
    include: { _count: { select: { posts: true } } },
    orderBy: { posts: { _count: 'desc' } },
    take: 30,
  })
  return tags.map(t => ({ name: t.name, count: t._count.posts }))
}
```

## 16.7 SEO与性能优化

### 16.7.1 动态Metadata

```tsx
// app/posts/[slug]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const post = await db.post.findUnique({ where: { slug: params.slug } })
  if (!post) return {}
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: post.coverImage ? [post.coverImage] : undefined,
      type: 'article',
    },
  }
}
```

### 16.7.2 结构化数据

```tsx
const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'BlogPosting',
  headline: post.title,
  author: { '@type': 'Person', name: post.author.name },
  datePublished: post.createdAt,
}
return (
  <article>
    <script type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
    {/* 文章内容 */}
  </article>
)
```

### 16.7.3 性能优化清单

| 优化项 | 实现 | 目标 |
|--------|------|------|
| LCP | 首屏图片priority + AVIF | < 2.5s |
| CLS | next/image指定尺寸 | < 0.1 |
| 首页SSG | 构建时预渲染 | 即时响应 |
| ISR | revalidate: 3600 | 内容新鲜 |
| 代码分割 | next/dynamic拆分编辑器 | < 200KB |
| 图片优化 | next/image自动转换 | 最小格式 |

## 16.8 打包上线

### 16.8.1 生产构建

```bash
# 构建前检查
npm run lint && npm run typecheck && npm run test

# 构建
npm run build

# 检查产物
ls -la .next/standalone/
```

### 16.8.2 Docker部署

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

### 16.8.3 上线检查清单

| 检查项 | 状态 |
|--------|------|
| 环境变量已配置 | [ ] |
| HTTPS证书有效 | [ ] |
| 数据库备份已设置 | [ ] |
| Sentry错误监控已接入 | [ ] |
| 健康检查接口正常 | [ ] |
| sitemap可访问 | [ ] |
| robots.txt正确 | [ ] |
| 404/500页面正常 | [ ] |
| Lighthouse达标 | [ ] |
| 回滚方案已准备 | [ ] |

> 上线检查清单不是形式主义，是"防呆"。人在紧张时容易遗漏，清单帮你确保每一项都检查过。每次上线对着清单走一遍，5分钟换来的是安心。

## 16.9 拓展与总结

### 16.9.1 功能拓展方向

| 方向 | 功能 | 技术方案 |
|------|------|---------|
| 搜索 | 全文搜索 | PostgreSQL tsvector / Meilisearch |
| 通知 | 邮件/WebSocket通知 | Resend / Socket.io |
| 分析 | 访问统计 | Vercel Analytics / Umami |
| CMS | 内容管理后台 | 扩展admin模块 |
| 多媒体 | 图片/视频管理 | Cloudinary / S3 |

### 16.9.2 技术升级路径

```
博客 → CMS → SaaS平台
  ↓        ↓        ↓
单机部署 → 容器化 → 微服务
PostgreSQL → 读写分离 → 分库分表
JWT → OAuth → SSO
静态缓存 → Redis缓存 → CDN边缘计算
```

### 16.9.3 系列总结

16章内容，从Next.js基础到全栈实战，覆盖了：

| 章节 | 核心知识 |
|------|---------|
| 1-3 | Next.js基础、路由、组件 |
| 4-5 | 数据获取与状态管理 |
| 6-7 | 样式与UI组件 |
| 8-9 | 中间件与请求拦截 |
| 10 | 认证与权限系统 |
| 11 | 静态资源与媒体优化 |
| 12 | 工程化与规范配置 |
| 13 | 性能优化与SEO |
| 14 | 异常处理与调试 |
| 15 | 部署与CI/CD |
| 16 | 综合实战 |

### 16.9.4 后续学习路线

```
Next.js全栈 → 深入React源码 → 学习TypeScript高级特性
    ↓
全栈能力 → 学习数据库优化 → 学习分布式系统
    ↓
架构能力 → 学习微服务 → 学习云原生
    ↓
工程能力 → 学习Monorepo → 学习前端基建
```

> 学完这个系列，你已经具备了Next.js全栈开发的能力。但技术学习不是终点，解决问题才是。用你学到的东西去做项目、写产品、解决真实问题，这才是技术学习的最终目的。

觉得这个系列有用？收藏整个系列，作为Next.js开发参考手册随时翻阅。

这个系列你最受益的是哪一章？评论区聊聊你的学习心得。

**系列进度 16/16**

**怕浪猫说**

16章写到这里，Next.js系列就完结了。从最基础的路由到最后的全栈实战，我把这些年用Next.js踩过的坑、总结的经验都写进了这个系列。希望它能成为你Next.js开发路上的参考手册。技术会更新，但工程思维和解决问题的方法论不会过时。感谢你追完了整个系列，我们下个系列见。

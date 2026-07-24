# 第12章 项目工程化与规范配置

团队里5个人写Next.js，5种代码风格。有人用any，有人用unknown，有人不写类型。合并代码时Git冲突能吵一下午。后来花半天配好ESLint + Prettier + husky + commitlint，从此代码风格自动统一，提交信息自动检查，效率提升不止一倍。

我是怕浪猫，一个对工程规范有洁癖的全栈开发者。这章把Next.js项目工程化的完整配置链拆透——从TypeScript到ESLint，从Git钩子到环境变量，从日志到模块化，帮你建立团队级的工程规范。

## 12.1 TypeScript类型规范与全局类型定义

### 12.1.1 TypeScript配置：tsconfig.json关键选项

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,              // 必开
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "noUncheckedIndexedAccess": true,  // 推荐：数组下标访问返回T|undefined
    "forceConsistentCasingInFileNames": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

关键选项说明：

| 选项 | 说明 | 推荐值 |
|------|------|--------|
| strict | 开启所有严格类型检查 | true |
| noUncheckedIndexedAccess | 数组/对象下标访问加undefined | true |
| forceConsistentCasingInFileNames | 文件名大小写一致 | true |
| skipLibCheck | 跳过node_modules类型检查 | true |
| incremental | 增量编译，加快速度 | true |

> strict: true是TypeScript项目的底线。不开strict的TypeScript项目等于在写JavaScript加注释。

### 12.1.2 全局类型声明

```typescript
// types/global.d.ts
declare type Nullable<T> = T | null
declare type Maybe<T> = T | undefined
declare type AsyncResult<T> = Promise<{ data: T; error: null } | { data: null; error: Error }>

// types/env.d.ts - 环境变量类型
interface ProcessEnv {
  NODE_ENV: 'development' | 'production' | 'test'
  NEXT_PUBLIC_API_URL: string
  NEXT_PUBLIC_APP_NAME: string
  DATABASE_URL: string
  JWT_SECRET: string
}

declare namespace NodeJS {
  interface ProcessEnv extends ProcessEnv {}
}
```

### 12.1.3 API响应类型与数据库模型类型

```typescript
// types/api.ts
interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

// types/models.ts
interface Post {
  id: number
  title: string
  content: string
  authorId: number
  author?: User
  tags: string[]
  published: boolean
  createdAt: Date
  updatedAt: Date
}
```

### 12.1.4 组件Props类型定义规范

```typescript
// 基础规范：每个组件的Props用interface声明
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  onClick?: () => void
  children: React.ReactNode
}

function Button({ variant = 'primary', size = 'md', ...props }: ButtonProps) {
  return <button className={`btn-${variant} btn-${size}`} {...props} />
}

// 利用工具类型减少重复
type PostCardProps = Pick<Post, 'title' | 'content' | 'author'> & {
  onEdit?: (id: number) => void
}
```

### 12.1.5 TypeScript高级技巧：泛型工具类型

```typescript
// API请求函数的泛型封装
async function apiFetch<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const res = await fetch(url, options)
  return res.json()
}

// 使用时类型自动推断
const { data } = await apiFetch<Post[]>('/api/posts')  // data: Post[]

// 常用工具类型
type Partial<T> = { [K in keyof T]?: T[K] }        // 所有属性可选
type Required<T> = { [K in keyof T]-?: T[K] }       // 所有属性必填
type Pick<T, K extends keyof T> = { [P in K]: T[P] } // 选取部分属性
type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>> // 排除部分属性
```

## 12.2 ESLint+Prettier代码规范约束

### 12.2.1 ESLint配置

```javascript
// .eslintrc.js
module.exports = {
  extends: ['next/core-web-vitals', 'plugin:@typescript-eslint/recommended'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',    // 禁止any
    '@typescript-eslint/no-unused-vars': 'warn',      // 未使用变量警告
    'no-console': ['warn', { allow: ['warn', 'error'] }], // 禁止console.log
    'prefer-const': 'error',                          // 能用const不用let
    'react-hooks/rules-of-hooks': 'error',            // Hook规则
    'react-hooks/exhaustive-deps': 'warn',            // 依赖完整性
  },
}
```

### 12.2.2 自定义ESLint规则

```javascript
// 禁止直接使用Date.now()，统一用dayjs
// .eslintrc.js
rules: {
  'no-restricted-globals': ['error', {
    name: 'Date',
    message: '使用 dayjs 替代 Date',
  }],
}

// 禁止default export（团队约定）
rules: {
  'import/prefer-default-export': 'off',
  'import/no-default-export': 'error',
}
```

> ESLint规则不是越多越好。每条规则都应该有理由——要么防Bug，要么统一风格。没有理由的规则只会让开发者反感。

### 12.2.3 Prettier配置与ESLint冲突解决

```javascript
// .prettierrc
{
  "semi": false,          // 不用分号
  "singleQuote": true,    // 单引号
  "tabWidth": 2,          // 缩进2空格
  "trailingComma": "es5", // 尾逗号
  "printWidth": 100,      // 行宽100
  "bracketSpacing": true, // 对象括号空格
  "arrowParens": "always" // 箭头函数参数加括号
}
```

```bash
# 安装冲突解决包
npm install -D eslint-config-prettier eslint-plugin-prettier

// .eslintrc.js - 把prettier放在最后，关闭冲突的格式化规则
module.exports = {
  extends: [
    'next/core-web-vitals',
    'plugin:@typescript-eslint/recommended',
    'prettier',  // 必须放最后
  ],
}
```

### 12.2.4 编辑器自动修复配置

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 12.2.5 常见ESLint报错与修复方案

| 报错 | 原因 | 修复 |
|------|------|------|
| no-explicit-any | 使用了any | 改用unknown或具体类型 |
| react-hooks/exhaustive-deps | useEffect依赖不完整 | 补全依赖或用useCallback |
| no-unused-vars | 变量声明了没使用 | 删除或前缀下划线 |
| prefer-const | let声明的变量没重新赋值 | 改为const |
| no-console | 使用了console.log | 改用console.warn/error或删除 |

## 12.3 Git提交规范与husky钩子配置

### 12.3.1 Conventional Commits规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

| type | 含义 | 示例 |
|------|------|------|
| feat | 新功能 | feat(auth): 添加OAuth登录 |
| fix | 修复Bug | fix(api): 修复分页参数错误 |
| docs | 文档 | docs(readme): 更新安装说明 |
| style | 格式 | style: 统一缩进 |
| refactor | 重构 | refactor(auth): 抽离token验证逻辑 |
| perf | 性能 | perf(image): 添加图片懒加载 |
| test | 测试 | test(api): 添加用户接口测试 |
| chore | 杂项 | chore: 更新依赖版本 |

### 12.3.2 commitlint配置

```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'chore'
    ]],
    'subject-max-length': [2, 'always', 72],
    'subject-case': [0], // 不检查大小写
  },
}
```

### 12.3.3 husky + lint-staged

```bash
# 安装
npm install -D husky lint-staged

# 初始化husky
npx husky init
```

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,css}": ["prettier --write"]
  },
  "scripts": {
    "lint-staged": "lint-staged",
    "commitlint": "commitlint --edit"
  }
}
```

```bash
# pre-commit钩子
echo "npx lint-staged" > .husky/pre-commit

# commit-msg钩子
echo "npx commitlint --edit \$1" > .husky/commit-msg
```

> husky + lint-staged的黄金组合：pre-commit检查代码格式，commit-msg检查提交信息。两道关卡，保证进入仓库的代码和提交信息都是规范的。

### 12.3.4 Git Hooks完整配置流程

```
开发者执行git commit
    ↓
pre-commit钩子触发
    ↓
lint-staged运行ESLint + Prettier
    ↓ (通过)
commit-msg钩子触发
    ↓
commitlint检查提交信息格式
    ↓ (通过)
提交成功
    ↓ (任一失败)
提交被拒绝，开发者修正后重试
```

### 12.3.5 团队协作中的Git规范执行

| 策略 | 说明 |
|------|------|
| 分支命名 | feature/xxx, fix/xxx, hotfix/xxx |
| PR模板 | 描述变更、测试方式、影响范围 |
| Code Review | 至少1人审批才能合并 |
| 保护分支 | main/develop禁止直接push |
| 自动化检查 | CI流水线跑lint + test + build |

## 12.4 环境变量区分开发/测试/生产环境

### 12.4.1 .env文件层级

| 文件 | 优先级 | 说明 |
|------|--------|------|
| .env | 最低 | 所有环境共享 |
| .env.local | 高 | 本地覆盖，不提交Git |
| .env.development | 中 | 开发环境 |
| .env.production | 中 | 生产环境 |
| .env.test | 中 | 测试环境 |

```bash
# .env
NEXT_PUBLIC_APP_NAME=MyApp
DATABASE_URL=postgresql://localhost:5432/myapp

# .env.local (不提交)
JWT_SECRET=my-super-secret-key

# .env.production
DATABASE_URL=postgresql://prod-db:5432/myapp
```

### 12.4.2 服务端与客户端环境变量

```bash
# 服务端变量（不带NEXT_PUBLIC_前缀）
DATABASE_URL=postgresql://...     # 只在Server端可用
JWT_SECRET=my-secret              # 只在Server端可用

# 客户端变量（带NEXT_PUBLIC_前缀）
NEXT_PUBLIC_API_URL=https://api.example.com  # Server和Client都可用
NEXT_PUBLIC_APP_NAME=MyApp                   # Server和Client都可用
```

```tsx
// Server Component中可以访问所有变量
const dbUrl = process.env.DATABASE_URL  // OK
const apiUrl = process.env.NEXT_PUBLIC_API_URL  // OK

// Client Component中只能访问NEXT_PUBLIC_开头的
'use client'
const apiUrl = process.env.NEXT_PUBLIC_API_URL  // OK
const dbUrl = process.env.DATABASE_URL  // undefined!
```

> NEXT_PUBLIC_前缀的本质：构建时把变量值内联到客户端代码里。所以不带这个前缀的变量在客户端代码里根本不存在，不是"访问不到"，是"编译后就没有了"。

### 12.4.3 多环境部署变量管理

| 方案 | 优点 | 缺点 |
|------|------|------|
| .env文件 | 简单直观 | 文件多、易混乱 |
| CI/CD注入 | 安全、灵活 | 需要CI配置 |
| 配置服务(AWS SSM) | 集中管理 | 增加依赖 |
| Docker env | 容器化标准 | 需要Docker |

### 12.4.4 环境变量的类型安全

```typescript
// lib/env.ts
import { z } from 'zod'

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  NEXT_PUBLIC_API_URL: z.string().url(),
  NODE_ENV: z.enum(['development', 'production', 'test']),
})

const parseEnv = () => {
  const result = envSchema.safeParse(process.env)
  if (!result.success) {
    console.error('环境变量验证失败:', result.error.flatten())
    throw new Error('环境变量配置错误')
  }
  return result.data
}

export const env = parseEnv()
```

### 12.4.5 敏感变量安全管理

| 规则 | 说明 |
|------|------|
| 不提交Git | .env.local加入.gitignore |
| 不输出日志 | 不要console.log打印环境变量 |
| 不暴露给客户端 | 敏感变量不加NEXT_PUBLIC_ |
| CI/CD用Secret | GitHub Secrets / GitLab Variables |
| 定期轮换 | 密钥定期更换 |

## 12.5 项目日志收集与错误捕获

### 12.5.1 结构化日志

```typescript
// lib/logger.ts
import pino from 'pino'

export const logger = pino({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  transport: process.env.NODE_ENV !== 'production'
    ? { target: 'pino-pretty' }
    : undefined,
})

// 使用
logger.info({ userId: 123, action: 'login' }, '用户登录')
logger.error({ err, path: '/api/posts' }, 'API错误')
```

### 12.5.2 服务端日志：API路由请求日志

```typescript
// lib/api-logger.ts
import { logger } from './logger'

export function logRequest(request: NextRequest, status: number, duration: number) {
  logger.info({
    method: request.method,
    path: request.nextUrl.pathname,
    status,
    duration,
    ip: request.ip,
    userAgent: request.headers.get('user-agent'),
  }, 'API请求')
}

// 在Route Handler中使用
export async function GET(request: NextRequest) {
  const start = Date.now()
  try {
    const posts = await db.post.findMany()
    const duration = Date.now() - start
    logRequest(request, 200, duration)
    return success(posts)
  } catch (err) {
    const duration = Date.now() - start
    logRequest(request, 500, duration)
    logger.error({ err }, '获取文章列表失败')
    return error('服务器错误', 1, 500)
  }
}
```

### 12.5.3 客户端日志：错误上报

```tsx
// app/error.tsx
'use client'
import { useEffect } from 'react'
import { logger } from '@/lib/client-logger'

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  useEffect(() => {
    logger.error({ err: error }, '客户端错误')
  }, [error])

  return (
    <div>
      <h2>出错了</h2>
      <button onClick={reset}>重试</button>
    </div>
  )
}
```

### 12.5.4 日志分级与采样

| 级别 | 用途 | 示例 |
|------|------|------|
| fatal | 系统崩溃 | 数据库连接失败 |
| error | 业务错误 | API异常、用户操作失败 |
| warn | 警告 | 接口慢、参数非法 |
| info | 关键操作 | 登录、下单、支付 |
| debug | 调试信息 | SQL语句、中间状态 |
| trace | 详细追踪 | 函数调用链 |

> 日志不是越多越好。生产环境开info级别，debug和trace关掉。一次请求打10条日志，QPS 1000就是每秒1万条日志，存储成本比你想象的大。

### 12.5.5 Sentry集成

```typescript
// lib/sentry.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,  // 10%采样
  environment: process.env.NODE_ENV,
  beforeSend(event) {
    // 过滤敏感信息
    if (event.request?.headers) {
      delete event.request.headers.authorization
    }
    return event
  },
})

// 使用
try {
  await riskyOperation()
} catch (err) {
  Sentry.captureException(err)
}
```

## 12.6 模块化拆分与业务解耦技巧

### 12.6.1 特性模块划分

```
src/
├── modules/
│   ├── auth/
│   │   ├── components/    # 登录/注册组件
│   │   ├── api/           # 认证API
│   │   ├── hooks/         # useAuth等
│   │   ├── utils/         # token处理
│   │   ├── types.ts       # 认证类型
│   │   └── index.ts       # 模块出口
│   ├── posts/
│   │   ├── components/
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types.ts
│   └── user/
│       └── ...
├── shared/
│   ├── components/        # 通用UI组件
│   ├── utils/             # 通用工具
│   ├── constants/         # 常量
│   └── types/             # 全局类型
└── app/                   # Next.js App Router
```

> 模块化的核心原则：高内聚低耦合。同一个功能的所有代码放在一起（高内聚），模块之间通过明确的接口通信（低耦合）。找不到文件？说明你的目录结构不对。

### 12.6.2 共享代码组织

```typescript
// shared/constants/index.ts
export const API_VERSION = 'v1'
export const PAGE_SIZE = 20
export const TOKEN_KEY = 'access_token'

// shared/utils/format.ts
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(date)
}

// shared/types/index.ts
export type ID = number
export type Timestamp = number
```

### 12.6.3 服务端逻辑与客户端逻辑隔离

```
modules/auth/
├── server/           # 只在Server端运行
│   ├── verifyToken.ts
│   └── generateToken.ts
├── client/           # 只在Client端运行
│   ├── useAuth.ts
│   └── LoginForm.tsx
└── shared/           # 两端共用
    └── types.ts
```

### 12.6.4 依赖注入实践

```typescript
// 简单的依赖注入：通过函数参数传递依赖
interface PostService {
  getPosts: () => Promise<Post[]>
}

// 生产环境
const productionPostService: PostService = {
  getPosts: () => db.post.findMany(),
}

// 测试环境(mock)
const mockPostService: PostService = {
  getPosts: () => Promise.resolve([{ id: 1, title: 'Test' }]),
}

// 使用
export async function GET(request: NextRequest, service: PostService = productionPostService) {
  const posts = await service.getPosts()
  return success(posts)
}
```

### 12.6.5 大型项目模块化演进路径

```
阶段1：单项目，按目录分模块（适合<50页面）
    ↓
阶段2：单项目，按特性模块分（适合50-200页面）
    ↓
阶段3：Monorepo，共享UI库 + 业务包（适合>200页面）
    ↓
阶段4：微前端/多项目，独立部署（适合多团队协作）
```

> 不要一上来就搞微前端。90%的项目，单项目 + 良好的模块划分就够了。过早的架构升级不是优化，是负担。

## 12.7 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| TypeScript | strict模式、全局类型、工具类型 |
| ESLint+Prettier | 代码规范、自动修复、冲突解决 |
| Git规范 | Conventional Commits、husky、lint-staged |
| 环境变量 | .env层级、NEXT_PUBLIC_前缀、类型安全验证 |
| 日志系统 | pino结构化日志、分级、Sentry错误监控 |
| 模块化 | 特性模块、共享代码、服务端/客户端隔离 |

### 课后练习

1. 配置tsconfig.json开启strict模式，修复所有类型错误
2. 搭建ESLint + Prettier + husky + commitlint完整工具链
3. 用Zod实现环境变量验证，故意写错一个变量看报错效果
4. 接入pino结构化日志，在API路由中记录请求日志
5. 按特性模块重新组织项目目录结构

> 工程规范的价值不是"限制自由"，而是"减少犯错"。好的规范让你不需要思考"该怎么写"，只需要思考"写什么"。

觉得有用？收藏起来，下次搭建新项目直接照着配。

你团队用的是什么代码规范方案？评论区聊聊你的工程化经验。

关注怕浪猫，下期我们讲Next.js的测试策略——从Jest单元测试到Playwright E2E（End-to-End，端到端）测试，帮你建立全方位的测试防线，让每次部署都不心慌。

**系列进度 12/16**

**怕浪猫说**

工程化是那种"短期看不到收益，长期决定成败"的事情。一个人写代码不需要规范，三个人写代码必须规范，五个人不规范就要乱。这篇文章里的每条配置都是我在实际团队中验证过的，拿来即用。下一章见。

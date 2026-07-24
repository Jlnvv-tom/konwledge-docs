# 第8章 数据库对接：全栈数据持久化开发

90%的Next.js开发者在前三章学完之后，都会卡在同一个地方——数据存不进去，读不出来，Serverless连接池爆了，Prisma迁移报红，MongoDB聚合管道写到怀疑人生。数据库对接，是全栈开发真正分水岭。前面学的路由、渲染、API都是骨架，数据库才是心脏。

我是怕浪猫，一个在生产环境被数据库连接数教做人的全栈开发者。这一章我会把Next.js数据库对接从选型到实战的全部踩坑经验拆解清楚，从Prisma到MongoDB，从事务到分页，保证你看完就能落地。

## 8.1 Next.js主流数据库适配方案选型

### 8.1.1 关系型vs非关系型：MySQL/PostgreSQL vs MongoDB

数据库世界两大阵营，选错了后面全是技术债。先看核心差异：

```
关系型数据库（MySQL/PostgreSQL）          非关系型数据库（MongoDB）
┌─────────────────────────┐             ┌─────────────────────────┐
│  表(Table) → 行(Row)     │             │  集合(Collection) → 文档  │
│  固定Schema              │             │  灵活Schema              │
│  ACID事务原生支持         │             │  4.0+支持事务            │
│  JOIN查询                │             │  聚合管道                │
│  外键约束                 │             │  嵌套文档                │
│  垂直扩展为主             │             │  水平扩展为主             │
└─────────────────────────┘             └─────────────────────────┘
```

关系型数据库适合数据结构稳定、关系复杂、强一致性要求高的场景。比如电商的订单系统、用户账户体系、财务流水。MySQL（My Structured Query Language，一种关系型数据库）生态成熟，运维资源丰富；PostgreSQL（Postgres，一种对象关系型数据库）则在JSON支持、全文搜索、复杂查询上更强。

MongoDB适合数据结构灵活、读写量大、快速迭代的场景。比如内容管理系统、日志分析、实时数据流。它的BSON（Binary JSON，二进制JSON格式）文档模型天然契合JavaScript生态，存取JSON不需要ORM（Object-Relational Mapping，对象关系映射）做对象关系映射。

> 选数据库不是选技术栈，是选数据哲学。关系型问的是"数据之间什么关系"，文档型问的是"数据长什么样"。

实际项目中怕浪猫的建议是：如果你不确定选哪个，先选PostgreSQL。它既有关系型的严谨，又有JSONB的灵活，是"既要又要"的最佳答案。

### 8.1.2 ORM选型对比：Prisma vs Drizzle vs TypeORM

在Next.js生态里，三款ORM各有拥趸。直接上对比：

| 维度 | Prisma | Drizzle | TypeORM |
|------|--------|---------|---------|
| Schema定义 | 独立.prisma文件 | TypeScript代码 | 装饰器+Entity |
| 类型安全 | 自动生成，极强 | 原生TS，极强 | 需手动配置 |
| 学习曲线 | 低，文档友好 | 中，需懂SQL | 高，概念多 |
| Bundle大小 | 较大 | 极小 | 中等 |
| Serverless适配 | 好（需连接池） | 优秀（无状态） | 一般 |
| 迁移工具 | prisma migrate | drizzle-kit | 手动/CLI |
| 社区活跃度 | 极高 | 快速增长 | 下降趋势 |

Prisma是当前Next.js生态最主流的选择。它的schema定义直观，类型推导自动完成，Prisma Studio可视化数据管理。缺点是生成的Client体积较大，在Edge Runtime环境下不完全兼容。

Drizzle是后起之秀，设计哲学是"如果你会SQL，就会Drizzle"。API设计贴近原生SQL（Structured Query Language，结构化查询语言），Bundle极小，Serverless友好。但生态和工具链还在发展中。

TypeORM是老牌选手，装饰器风格在NestJS生态很流行，但在Next.js App Router中使用存在装饰器元数据反射的问题，需要额外配置，不太推荐作为首选。

```typescript
// Prisma schema定义风格
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  name  String?
  posts Post[]
}

// Drizzle schema定义风格
import { pgTable, serial, varchar } from 'drizzle-orm/pg-core'
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: varchar('email').notNull().unique(),
  name: varchar('name'),
})
```

> Prisma让你忘记SQL，Drizzle让你拥抱SQL。在Next.js项目里，怕浪猫默认推荐Prisma，上手快、文档全、踩坑少。但如果你追求极致的Bundle大小和Edge兼容性，Drizzle是更好的选择。

### 8.1.3 Serverless环境下的数据库连接限制

这是Next.js数据库对接最大的坑。Next.js部署在Vercel等Serverless平台时，每个函数实例都会创建独立的数据库连接。当并发请求增加时，连接数会迅速飙升，直到触发数据库的最大连接数限制。

```
传统服务器：1个进程 → 1个连接池 → N个连接
Serverless：M个实例 × N个连接 = M×N个连接  ← 爆炸！

Vercel函数实例          数据库
┌──────────┐           ┌──────────────┐
│ 实例1     │──10连接──→│              │
│ 实例2     │──10连接──→│  最大100连接  │
│ 实例3     │──10连接──→│              │
│ ...      │           │  实际: 150+   │ ← 连接拒绝!
│ 实例15    │──10连接──→│              │
└──────────┘           └──────────────┘
```

解决方案有三种：

第一种是使用连接池代理，比如PlanetScale的Vitess代理或PgBouncer。数据库连接走代理层，Serverless函数连接代理而非直连数据库。这种方式对应用层透明，但需要额外的基础设施。

第二种是Prisma的Data Proxy或Accelerate。Prisma Data Proxy在云端维护连接池，应用通过HTTP连接Proxy，Proxy再连数据库。适合Serverless场景但引入了额外的网络跳转延迟。

第三种是使用全局连接复用。在开发环境通过`globalThis`缓存Prisma Client实例，避免热重载时反复创建连接：

```typescript
// lib/prisma.ts - 开发环境连接复用
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma
}
```

> Serverless不是银弹，它用弹性换走了连接稳定性。在数据库连接这件事上，怕浪猫踩过最深的一个坑就是：本地开发一切正常，部署后偶发Connection Timeout，查了两天才发现是连接池耗尽。记住，凡是Serverless + 数据库，第一件事就是想清楚连接管理策略。

### 8.1.4 数据库即服务：PlanetScale、Neon、Supabase

Serverless数据库服务是Next.js全栈开发的最佳拍档。三款主流方案各有特色：

PlanetScale基于MySQL和Vitess，提供无限连接的代理层，分支功能让你像Git管理代码一样管理数据库Schema。但免费层已取消，起步价$39/月。适合MySQL生态团队。

Neon是Serverless PostgreSQL，支持按需扩缩容和分支。冷启动后响应快，免费层慷慨。最大亮点是scale-to-zero，不使用时不计费。适合PostgreSQL生态和低流量项目。

Supabase基于PostgreSQL，提供数据库+认证+存储+实时订阅的一站式BaaS（Backend as a Service，后端即服务）方案。内置Row Level Security和Auto API。适合快速搭建全栈应用。

| 服务 | 数据库 | 免费层 | 分支功能 | 连接池 | 特点 |
|------|--------|--------|----------|--------|------|
| PlanetScale | MySQL | 无 | 有 | 内置 | Vitess代理，无限连接 |
| Neon | PostgreSQL | 有 | 有 | 内置 | Scale-to-zero |
| Supabase | PostgreSQL | 有 | 无 | Supavisor | BaaS全家桶 |

### 8.1.5 Next.js数据库方案选型决策表

综合以上分析，怕浪猫整理一张决策表供你快速选型：

```
你的场景                           推荐方案
──────────────────────────────────────────────────────
快速原型/个人项目                  Supabase + Prisma
企业级MySQL项目                   PlanetScale + Prisma
企业级PostgreSQL项目               Neon + Prisma
追求极致性能/Edge部署              Neon + Drizzle
灵活Schema/文档型需求              MongoDB + Mongoose
已有TypeORM/NestJS项目迁移         TypeORM（保持一致性）
```

选型没有银弹，但有一个安全默认值：PostgreSQL（Neon）+ Prisma。这套组合在Next.js生态中验证最充分，文档最齐全，踩坑社区最活跃。

## 8.2 Prisma ORM安装、配置与模型定义

### 8.2.1 Prisma安装与schema.prisma配置

Prisma的安装分三步：安装CLI依赖、初始化配置、配置数据源。

```bash
# 安装Prisma CLI和Client
npm install prisma @prisma/client --save-dev

# 初始化Prisma（根据数据库选择datasource provider）
npx prisma init --datasource-provider postgresql
```

初始化后会生成两个文件：`prisma/schema.prisma`和`.env`。schema.prisma是Prisma的核心配置文件，用Prisma自己的DSL（Domain-Specific Language，领域特定语言）编写。`.env`文件中存放数据库连接字符串。

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

`generator client`指定Prisma Client的生成方式，`provider = "prisma-client-js"`表示生成JavaScript可用的Client。`datasource db`配置数据库类型和连接字符串，`env("DATABASE_URL")`从环境变量读取，避免硬编码敏感信息。

配置完成后，记得在项目根目录创建`lib/prisma.ts`文件封装Prisma Client单例，前面8.1.3节已经给出过代码。这个封装在Next.js项目中是必须的，不做的话开发环境热重载会疯狂创建连接。

### 8.2.2 数据模型定义：model、field、relation

Prisma的模型定义是声明式的，语法简洁但表达力强。来看一个完整的博客系统模型：

```prisma
// prisma/schema.prisma
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  role      Role     @default(USER)
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  Int
  author    User     @relation(fields: [authorId], references: [id])
  tags      Tag[]    @relation("PostToTag")
  createdAt DateTime @default(now())
}

model Tag {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[] @relation("PostToTag")
}

enum Role {
  USER
  ADMIN
}
```

几个关键点拆解：

`@id`标记主键，`@default(autoincrement())`表示自增。`@unique`标记唯一约束。`@default(now())`设置默认值为当前时间。`@updatedAt`自动更新修改时间。这些都是Prisma的字段修饰符（Field Attribute）。

关系定义是Prisma的精华。`posts Post[]`表示一个User有多个Post，这是"一对多"关系的"一"端。对应的Post模型中，`author User @relation(fields: [authorId], references: [id])`是"多"端，`authorId`是外键字段，指向User的`id`。

多对多关系通过中间关系表实现。上面的Post和Tag通过`@relation("PostToTag")`命名的关系实现多对多，Prisma会自动创建隐式连接表`_PostToTag`。

> Prisma的关系定义就像在画ER图，只不过用的是代码。一旦理解了`@relation`的`fields`和`references`对应关系，复杂的关联查询也能信手拈来。

### 8.2.3 Prisma Client生成与类型推导

定义好schema后，需要生成Prisma Client才能在代码中使用：

```bash
# 生成Client
npx prisma generate

# 同步Schema到数据库（开发环境）
npx prisma db push
```

生成的Prisma Client会根据你的model定义自动创建TypeScript类型。你在代码中使用时，所有查询的输入和输出都有完整的类型推导：

```typescript
import { prisma } from '@/lib/prisma'

// 完整的输入类型推导
const user = await prisma.user.create({
  data: {
    email: 'user@example.com',
    name: '怕浪猫',
    role: 'ADMIN', // 枚举值有提示
  },
})
// 输出类型：User & { posts: Post[] }
const userWithPosts = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
})
```

Prisma的类型系统会根据你调用的方法自动推导返回类型。`findUnique`返回`T | null`，`findMany`返回`T[]`，`include`会扩展返回类型包含关联数据。这种端到端的类型安全，让你在重构时编译器就能帮你发现问题。

### 8.2.4 prisma migrate数据库迁移流程

生产环境不能用`db push`，必须用`prisma migrate`做规范的数据库迁移。迁移流程的核心是生成可追溯的SQL迁移文件：

```bash
# 创建迁移（开发环境）
npx prisma migrate dev --name init

# 创建迁移后会生成 prisma/migrations/ 目录
# prisma/migrations/
# └── 20240101000000_init/
#     └── migration.sql

# 部署迁移（生产环境）
npx prisma migrate deploy
```

`migrate dev`做了三件事：检测schema变更、生成迁移SQL、应用到数据库并重置开发数据。生成的`migration.sql`文件应该提交到Git，这样团队成员拉取代码后运行`migrate deploy`就能同步Schema。

生产环境只用`migrate deploy`，它不会重置数据，只应用未执行的迁移文件。这是安全生产的基本原则。

一个常见的坑是：修改了schema后忘记执行`migrate dev`，直接在代码里用新字段查询，结果运行时报错"Unknown column"。记住流程：改schema -> migrate dev -> 写代码。顺序不能反。

### 8.2.5 Prisma Studio可视化数据管理

Prisma Studio是开发阶段最实用的工具之一，一行命令启动可视化数据库管理界面：

```bash
npx prisma studio
```

启动后浏览器打开`localhost:5555`，你会看到所有model以表格形式展示。可以直接在界面上进行CRUD（Create Read Update Delete，增删改查）操作，修改记录后点击Save即可保存。

在开发调试时，Prisma Studio的价值很大。当你的API返回数据不符合预期时，打开Studio看一眼数据库实际存了什么，比在代码里加`console.log`效率高得多。但要注意，Studio只应该在开发环境使用，生产环境绝对不要暴露。

## 8.3 MySQL/PostgreSQL数据库连接与CRUD

### 8.3.1 连接字符串配置与连接池

数据库连接字符串是应用访问数据库的入口，格式遵循URI（Uniform Resource Identifier，统一资源标识符）规范：

```env
# .env 文件
# PostgreSQL连接字符串格式
DATABASE_URL="postgresql://用户名:密码@主机:端口/数据库名?参数"

# 实际示例
DATABASE_URL="postgresql://postgres:password@localhost:5432/mydb?schema=public"

# PlanetScale MySQL连接字符串
DATABASE_URL="mysql://用户名:密码@主机:端口/数据库名?sslaccept=accept"

# Neon PostgreSQL连接字符串（带连接池参数）
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?pgbouncer=true&connect_timeout=15"
```

连接池参数很关键。`pgbouncer=true`启用PgBouncer连接池模式，`connect_timeout=15`设置连接超时15秒。在Serverless环境下，这两个参数能大幅减少连接超时问题。

Prisma内部维护了一个连接池，默认连接数为`num_cpus * 2 + 1`。你可以通过`connection_limit`参数手动指定：

```env
# 限制连接池大小（Serverless推荐）
DATABASE_URL="postgresql://user:pass@host/db?connection_limit=5"
```

### 8.3.2 Create：插入数据与批量创建

Prisma的创建操作设计得很直观。单条创建用`create`，批量创建用`createMany`：

```typescript
// 单条创建
const post = await prisma.post.create({
  data: {
    title: 'Next.js数据库对接指南',
    content: '从选型到实战...',
    authorId: 1,
    tags: { connect: [{ id: 1 }, { id: 2 }] },
  },
})

// 批量创建
const posts = await prisma.post.createMany({
  data: [
    { title: '文章一', authorId: 1 },
    { title: '文章二', authorId: 1 },
    { title: '文章三', authorId: 2 },
  ],
  skipDuplicates: true, // 跳过唯一约束冲突
})
```

注意`create`支持嵌套写入，通过`connect`关联已有记录，通过`create`直接创建并关联新记录。而`createMany`不支持嵌套关系操作，只能写入扁平数据。这是两者的核心区别。

批量创建时的一个性能坑是：`createMany`默认不是事务操作，如果中间某条失败，前面的已经写入了。需要保证原子性的话，用`$transaction`包裹：

```typescript
await prisma.$transaction(
  prisma.post.createMany({ data: postsData })
)
```

### 8.3.3 Read：查询、过滤、排序、分页

查询是数据库操作中使用频率最高的。Prisma的查询API设计得非常符合直觉：

```typescript
// 条件查询
const publishedPosts = await prisma.post.findMany({
  where: {
    published: true,
    authorId: { in: [1, 2, 3] },
    title: { contains: 'Next.js', mode: 'insensitive' },
    createdAt: { gte: new Date('2024-01-01') },
  },
  orderBy: { createdAt: 'desc' },
  take: 10,
  skip: 0,
  select: {
    id: true,
    title: true,
    author: { select: { name: true } },
  },
})
```

这段代码展示了Prisma查询的核心能力。`where`支持丰富的过滤操作符：`in`匹配集合，`contains`做模糊匹配，`gte`大于等于，`mode: 'insensitive'`不区分大小写。`orderBy`排序，`take`和`skip`分页，`select`精简返回字段减少数据传输。

过滤操作符速查：

| 操作符 | 含义 | SQL等价 |
|--------|------|---------|
| eq | 等于 | = |
| ne | 不等于 | != |
| gt / gte | 大于 / 大于等于 | > / >= |
| lt / lte | 小于 / 小于等于 | < / <= |
| in | 在集合中 | IN |
| notIn | 不在集合中 | NOT IN |
| contains | 包含子串 | LIKE |
| startsWith | 前缀匹配 | LIKE 'xxx%' |
| endsWith | 后缀匹配 | LIKE '%xxx' |

> Prisma的查询API就是把SQL的WHERE条件用对象语法重写了一遍。一旦形成肌肉记忆，写查询比写SQL还快。但怕浪猫提醒你，复杂的OR嵌套条件还是要先在SQL里验证逻辑，再翻译成Prisma语法，避免逻辑出错。

### 8.3.4 Update：单条更新与批量更新

更新操作分单条和批量两种模式：

```typescript
// 单条更新（通过唯一字段定位）
const updated = await prisma.post.update({
  where: { id: 1 },
  data: {
    title: '更新后的标题',
    published: true,
    viewCount: { increment: 1 }, // 原子递增
  },
})

// 批量更新
const result = await prisma.post.updateMany({
  where: { authorId: 1, published: false },
  data: { published: true },
})
// result.count 返回受影响的行数
```

`update`只能通过唯一字段（`@id`或`@unique`）定位记录，如果找不到会抛出`P2025`错误。`updateMany`通过条件过滤批量更新，返回受影响行数。

原子操作是更新的一个亮点。`increment`递增、`decrement`递减、`multiply`乘以、`divide`除以，这些操作在数据库层面原子执行，避免了"读取-修改-写入"的竞态条件。比如计数器场景，用`increment`比先读再写安全得多。

### 8.3.5 Delete：物理删除与软删除

Prisma的删除操作直接物理删除记录，不可恢复：

```typescript
// 单条删除
await prisma.post.delete({ where: { id: 1 } })

// 批量删除
await prisma.post.deleteMany({
  where: { authorId: 999 }, // 删除某作者所有文章
})
```

但在生产环境中，物理删除往往是危险操作。怕浪猫推荐使用软删除（Soft Delete），即在模型中添加`deletedAt`字段，删除时只标记不真删：

```typescript
// 软删除实现
model Post {
  id        Int       @id @default(autoincrement())
  title     String
  deletedAt DateTime? // null=未删除，有值=已删除
}

// 软删除操作
await prisma.post.update({
  where: { id: 1 },
  data: { deletedAt: new Date() },
})

// 查询时过滤已删除的记录
const activePosts = await prisma.post.findMany({
  where: { deletedAt: null },
})
```

软删除的缺点是需要在每个查询中都加`deletedAt: null`条件，容易遗漏。Prisma目前不支持全局查询过滤器（Global Query Filter），所以要么通过中间件（Middleware）统一处理，要么在业务层严格约束。如果使用Drizzle或TypeORM，它们都支持全局过滤器，可以更优雅地处理软删除。

## 8.4 MongoDB非关系型数据库实战

### 8.4.1 MongoDB驱动安装与连接配置

MongoDB在Next.js中的使用分两种方式：官方驱动和Mongoose（MongoDB的ODM，Object Document Mapping，对象文档映射）。官方驱动轻量灵活，Mongoose提供Schema约束和丰富中间件。大多数项目选Mongoose，下面以Mongoose为主。

```bash
npm install mongoose
```

连接配置和Prisma类似，也需要处理Serverless连接复用问题：

```typescript
// lib/mongodb.ts
import mongoose from 'mongoose'

const MONGODB_URI = process.env.MONGODB_URI!

if (!MONGODB_URI) {
  throw new Error('请在环境变量中配置MONGODB_URI')
}

let cached = (global as any).mongoose

if (!cached) {
  cached = (global as any).mongoose = { conn: null, promise: null }
}

export async function connectDB() {
  if (cached.conn) return cached.conn
  if (!cached.promise) {
    cached.promise = mongoose.connect(MONGODB_URI, {
      bufferCommands: false,
    })
  }
  cached.conn = await cached.promise
  return cached.conn
}
```

这段代码通过`global`缓存mongoose连接实例，确保在Serverless环境下不会重复创建连接。`bufferCommands: false`禁用命令缓冲，避免连接未就绪时的隐式排队。

### 8.4.2 Mongoose schema定义与模型创建

Mongoose的Schema定义和Prisma的model类似，但用的是JavaScript对象语法：

```typescript
// models/Post.ts
import mongoose from 'mongoose'

const postSchema = new mongoose.Schema({
  title:    { type: String, required: true, trim: true },
  content:  { type: String, default: '' },
  published:{ type: Boolean, default: false },
  authorId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  tags:     [{ type: String }],
  viewCount:{ type: Number, default: 0 },
  createdAt:{ type: Date, default: Date.now },
})

// 索引定义
postSchema.index({ title: 'text' })
postSchema.index({ authorId: 1, createdAt: -1 })

export const Post = mongoose.models.Post 
  || mongoose.model('Post', postSchema)
```

注意最后一行，`mongoose.models.Post || mongoose.model(...)`这个写法在Next.js中是必须的。因为Next.js热重载会反复执行模块代码，直接`mongoose.model()`在第二次执行时会报"Cannot overwrite model"错误。加一个判断就能避免。

Schema定义中的`ref: 'User'`声明了外键引用关系，后续可以通过`populate()`方法关联查询。这类似于Prisma的`include`，但Mongoose的populate是在查询时通过额外查询实现的，性能上不如Prisma的JOIN。

### 8.4.3 文档CRUD操作实战

Mongoose的CRUD操作和Prisma风格差异较大，更贴近MongoDB原生语法：

```typescript
import { Post } from '@/models/Post'
import { connectDB } from '@/lib/mongodb'

// Create
await connectDB()
const post = await Post.create({
  title: 'MongoDB实战指南',
  authorId: userId,
  tags: ['database', 'mongodb'],
})

// Read
const posts = await Post.find({ published: true })
  .sort({ createdAt: -1 })
  .limit(10)
  .populate('authorId', 'name email')
  .lean()

// Update
const updated = await Post.findByIdAndUpdate(
  postId,
  { $inc: { viewCount: 1 } },
  { new: true }
)

// Delete
await Post.findByIdAndDelete(postId)
```

`.lean()`方法返回纯JavaScript对象而非Mongoose Document，性能更好，适合只读场景。`$inc`是MongoDB的原子递增操作符，和Prisma的`increment`效果一样。`{ new: true }`让更新操作返回更新后的文档，默认返回更新前的。

### 8.4.4 聚合查询管道

MongoDB的聚合管道（Aggregation Pipeline）是它最强大的特性。通过管道操作符链式处理数据，可以实现复杂的统计和分析：

```typescript
// 统计每个作者的文章数和总浏览量
const stats = await Post.aggregate([
  { $match: { published: true } },
  { $group: {
      _id: '$authorId',
      postCount: { $sum: 1 },
      totalViews: { $sum: '$viewCount' },
      avgViews: { $avg: '$viewCount' },
  }},
  { $sort: { totalViews: -1 } },
  { $limit: 10 },
  { $lookup: {
      from: 'users',
      localField: '_id',
      foreignField: '_id',
      as: 'author',
  }},
])

// 等价SQL（概念对照）
// SELECT authorId, COUNT(*) as postCount,
//        SUM(viewCount) as totalViews,
//        AVG(viewCount) as avgViews
// FROM posts WHERE published = true
// GROUP BY authorId
// ORDER BY totalViews DESC
// LIMIT 10
```

管道的每个阶段接收上一阶段的输出作为输入。`$match`过滤，`$group`分组聚合，`$sort`排序，`$limit`限制数量，`$lookup`做左外连接（类似SQL的LEFT JOIN）。

```
输入文档流
  ↓
[$match] 过滤已发布的文章
  ↓
[$group] 按作者分组，计算文章数和浏览量
  ↓
[$sort]  按总浏览量降序排列
  ↓
[$limit] 取前10名
  ↓
[$lookup] 关联用户集合获取作者信息
  ↓
输出结果
```

> 聚合管道是MongoDB的杀手锏。同样的统计逻辑在关系型数据库里写SQL很优雅，但用ORM做就各种别扭。MongoDB的管道设计天然适合数据处理流程，每个阶段职责单一，组合起来威力巨大。怕浪猫在做内容分析系统时，80%的统计需求都是用聚合管道解决的。

### 8.4.5 MongoDB vs PostgreSQL：何时选哪个

经过前面四节的学习，总结一下两种数据库的适用场景：

```
选MongoDB的场景：
- 数据结构频繁变化，Schema不固定
- 需要存储大量嵌套文档
- 读写量大，关系简单
- 需要地理空间查询
- 团队熟悉JavaScript/JSON生态

选PostgreSQL的场景：
- 数据关系复杂，需要JOIN和外键约束
- 强一致性要求高，需要完善的ACID事务
- 需要复杂的聚合查询和窗口函数
- 需要全文搜索（PG的FTS很强）
- 团队有SQL经验
```

实际项目中，不是非此即彼。微服务架构下，不同服务可以选不同数据库。内容管理服务用MongoDB存灵活文档，订单服务用PostgreSQL保证事务一致性。怕浪猫做过的项目里，有一半是同时使用两种数据库的。

## 8.5 数据库事务与异常处理

### 8.5.1 Prisma事务：$transaction用法

事务保证一组操作要么全部成功，要么全部回滚。Prisma提供两种事务API：

```typescript
// 方式一：顺序查询事务（推荐）
const result = await prisma.$transaction(async (tx) => {
  // 从用户A扣款
  const sender = await tx.user.update({
    where: { id: 1 },
    data: { balance: { decrement: 100 } },
  })
  if (sender.balance < 0) {
    throw new Error('余额不足')
  }
  // 给用户B加款
  await tx.user.update({
    where: { id: 2 },
    data: { balance: { increment: 100 } },
  })
  // 记录流水
  await tx.transaction.create({
    data: { fromId: 1, toId: 2, amount: 100 },
  })
  return { sender }
})

// 方式二：批量操作事务（简单场景）
const [user, post] = await prisma.$transaction([
  prisma.user.create({ data: { email: 'new@test.com' } }),
  prisma.post.create({ data: { title: 'test', authorId: 1 } }),
])
```

方式一接收一个回调函数，参数`tx`是事务客户端，所有通过`tx`执行的操作在同一个事务中。回调中抛出的任何错误都会触发回滚。这种方式支持条件逻辑和错误处理，是推荐的做法。

方式二是数组形式，所有操作并行执行。简单但不支持条件逻辑，如果第二个操作依赖第一个的结果就不能用。

> 事务不是越多越好。事务持有锁的时间越长，并发性能越差。怕浪猫的原则是：事务内只做必须原子性的操作，网络请求、文件IO等耗时操作绝对不要放在事务里。

### 8.5.2 事务隔离级别与一致性

事务隔离级别（Transaction Isolation Level）决定了并发事务之间的可见性。Prisma支持的隔离级别取决于底层数据库：

```
隔离级别             脏读   不可重复读   幻读
Read Uncommitted     可能     可能        可能
Read Committed       不可能   可能        可能    ← PostgreSQL默认
Repeatable Read      不可能   不可能      可能    ← MySQL默认
Serializable         不可能   不可能      不可能
```

PostgreSQL默认是Read Committed，适合大多数场景。如果需要更强的隔离性，可以在事务开始前设置：

```typescript
await prisma.$transaction(async (tx) => {
  // 设置隔离级别为Serializable
  await tx.$executeRaw`SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`
  
  const account = await tx.account.findUnique({ where: { id: 1 } })
  // 业务逻辑...
}, {
  isolationLevel: 'Serializable',
})
```

Serializable级别下，并发事务的效果等同于串行执行，最安全但性能最差。在Next.js应用中，怕浪猫建议保持默认的Read Committed，只在关键业务路径上提升隔离级别。

### 8.5.3 常见数据库异常分类与处理

Prisma的错误都有标准化的错误码，以`P`开头。掌握这些错误码能帮你快速定位问题：

| 错误码 | 含义 | 处理策略 |
|--------|------|----------|
| P2002 | 唯一约束冲突 | 捕获并返回友好提示 |
| P2025 | 记录不存在 | 检查ID或返回404 |
| P2003 | 外键约束冲突 | 检查关联数据是否存在 |
| P2014 | 关系违反约束 | 检查关系定义和操作顺序 |
| P2034 | 事务冲突 | 自动重试 |
| P1001 | 连接超时 | 检查连接字符串和网络 |

实际代码中的异常处理模式：

```typescript
import { Prisma } from '@prisma/client'

try {
  const user = await prisma.user.create({
    data: { email: 'exists@test.com' },
  })
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError) {
    switch (e.code) {
      case 'P2002':
        // 唯一约束冲突，e.meta.target告诉你哪个字段冲突
        return { error: '该邮箱已注册' }
      case 'P2003':
        return { error: '关联数据不存在' }
      default:
        throw e
    }
  }
  throw e // 未知错误继续抛出
}
```

> 统一的异常处理中间件是生产项目必备的。怕浪猫在每个Next.js项目里都会写一个`handlePrismaError`函数，把Prisma错误码翻译成用户可读的错误消息。不要让数据库错误码泄漏到前端，既不安全也不友好。

### 8.5.4 死锁与重试策略

在高并发场景下，死锁（Deadlock）是绕不开的问题。两个事务互相等待对方释放锁，数据库会主动杀掉其中一个事务。

Prisma的`P2034`错误就是事务冲突/死锁。处理方式是自动重试：

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  let lastError: unknown
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (e) {
      lastError = e
      if (e instanceof Prisma.PrismaClientKnownRequestError) {
        if (e.code === 'P2034') {
          // 事务冲突，等待后重试
          await new Promise(r => setTimeout(r, 100 * (i + 1)))
          continue
        }
      }
      throw e // 非冲突错误直接抛出
    }
  }
  throw lastError
}

// 使用
const result = await withRetry(() =>
  prisma.$transaction(async (tx) => {
    // 事务操作
  })
)
```

重试策略的关键参数是退避时间。`100 * (i + 1)`是线性退避，也可以用指数退避`Math.pow(2, i) * 100`。重试次数不宜过多，3次足够，太多会让请求超时。

### 8.5.5 事务设计的最佳实践

总结几条生产环境事务设计的铁律：

第一，事务要短。事务持有锁的时间越长，死锁概率越高。把非必要的计算、IO操作移到事务外部。

第二，锁顺序一致。多个事务更新同批数据时，按相同顺序加锁。比如总是先更新用户表再更新订单表，不要有的先订单后用户。

第三，读多写少用乐观锁。通过`version`字段实现乐观锁，更新时检查版本号，冲突时重试。

```typescript
// 乐观锁实现
const updated = await prisma.user.update({
  where: { id_version: { id: 1, version: 3 } },
  data: { name: '新名字', version: { increment: 1 } },
})
// 如果当前version不是3，更新会失败（P2025）
```

第四，批量操作优先。`updateMany`比循环`update`高效得多，前者一条SQL搞定，后者N条SQL加N次网络往返。

## 8.6 数据分页、排序、筛选功能实现

### 8.6.1 偏移分页：skip/take

偏移分页是最直观的分页方式，通过`skip`跳过和`take`取数量实现：

```typescript
// GET /api/posts?page=2&pageSize=10
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const page = Number(searchParams.get('page')) || 1
  const pageSize = Number(searchParams.get('pageSize')) || 10

  const [posts, total] = await Promise.all([
    prisma.post.findMany({
      where: { published: true },
      skip: (page - 1) * pageSize,
      take: pageSize,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.post.count({ where: { published: true } }),
  ])

  return Response.json({
    data: posts,
    pagination: {
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize),
    },
  })
}
```

偏移分页的SQL等价是`LIMIT 10 OFFSET 10`，简单直接。但它的致命弱点是深度分页性能差。当`skip`值很大时（比如第1000页，skip=9990），数据库需要扫描并丢弃前9990条记录，非常浪费。

```
偏移分页性能曲线：
页码    skip值    扫描行数    响应时间
1       0         10          5ms
10      90        100         8ms
100     990       1000        30ms
1000    9990      10000       200ms  ← 开始变慢
10000   99990     100000      2000ms ← 不可接受
```

> 偏移分页就像翻书，翻到第1000页时你已经翻过9990页了。前几页飞快，越往后越慢。如果你的用户会翻到很深的页码，必须换方案。

### 8.6.2 游标分页：cursor性能优势

游标分页用"上一页最后一条记录的值"作为游标，直接定位到下一段数据的起始位置，不需要扫描跳过的记录：

```typescript
// 游标分页实现
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const pageSize = Number(searchParams.get('pageSize')) || 10
  const cursor = searchParams.get('cursor') // 上一页最后一条的id

  const posts = await prisma.post.findMany({
    where: { published: true },
    take: pageSize + 1, // 多取一条判断是否有下一页
    ...(cursor ? {
      skip: 1, // 跳过游标本身
      cursor: { id: Number(cursor) },
    } : {}),
    orderBy: { id: 'desc' },
  })

  const hasMore = posts.length > pageSize
  const data = hasMore ? posts.slice(0, -1) : posts
  const nextCursor = data.length > 0 
    ? data[data.length - 1].id 
    : null

  return Response.json({
    data,
    nextCursor: hasMore ? nextCursor : null,
  })
}
```

游标分页的核心原理对比：

```
偏移分页：SELECT * FROM posts ORDER BY id DESC LIMIT 10 OFFSET 9990
          → 数据库扫描10000行，丢弃9990行，返回10行

游标分页：SELECT * FROM posts WHERE id < 100 ORDER BY id DESC LIMIT 10
          → 数据库利用索引直接定位，扫描10行，返回10行
```

游标分页在深度分页时性能稳定，但缺点是不能跳页（只能上一页/下一页），也不支持直接访问特定页码。适合无限滚动加载、Feed流等场景。

### 8.6.3 多字段排序与条件筛选

实际业务中排序和筛选往往组合使用。来看一个文章列表的复杂查询：

```typescript
const posts = await prisma.post.findMany({
  where: {
    published: true,
    OR: [
      { title: { contains: 'Next.js' } },
      { content: { contains: 'React' } },
    ],
    author: {
      role: 'ADMIN',
    },
    createdAt: {
      gte: new Date('2024-01-01'),
      lte: new Date('2024-12-31'),
    },
  },
  orderBy: [
    { published: 'desc' },   // 先按发布状态排
    { createdAt: 'desc' },   // 再按创建时间排
  ],
  take: 20,
})
```

`OR`和`AND`可以嵌套组合，构建任意复杂的条件树。`orderBy`接受数组实现多字段排序，排序优先级从左到右递减。

多字段排序的SQL等价：`ORDER BY published DESC, created_at DESC`。先按`published`排，相同值内再按`createdAt`排。这个在列表页很常见：置顶文章排前面，同级别内按时间倒序。

### 8.6.4 全文搜索实现

Prisma的`contains`只做子串匹配，不适合真正的全文搜索。PostgreSQL内置的全文搜索功能更强大：

```typescript
// 使用PostgreSQL原生全文搜索
const results = await prisma.post.findMany({
  where: {
    OR: [
      { title: { contains: keyword, mode: 'insensitive' } },
      { content: { contains: keyword, mode: 'insensitive' } },
    ],
  },
  orderBy: { createdAt: 'desc' },
})

// 更好的方案：使用PostgreSQL的tsvector全文搜索
const results = await prisma.$queryRaw`
  SELECT id, title, ts_rank_cd(tsv, query) as rank
  FROM posts, to_tsquery('chinese', ${keyword}) query
  WHERE tsv @@ query
  ORDER BY rank DESC
  LIMIT 20
`
```

对于中文全文搜索，PostgreSQL的内置分词效果一般。生产环境推荐使用Elasticsearch或Meilisearch等专门的搜索引擎。它们提供更好的中文分词、相关性排序、拼写纠错等功能。

MongoDB的全文搜索相对简单，通过`$text`查询实现：

```typescript
// MongoDB全文搜索
const results = await Post.find(
  { $text: { $search: 'Next.js 数据库' } },
  { score: { $meta: 'textScore' } }
).sort({ score: { $meta: 'textScore' } })
```

### 8.6.5 分页性能优化与索引设计

索引是数据库性能优化的核武器。没有索引的查询是全表扫描，加了索引可以快几个数量级。

```
无索引查询：扫描100万行 → 2000ms
有索引查询：扫描10行    → 2ms
```

Prisma在schema中通过`@@index`定义复合索引：

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  authorId  Int
  published Boolean
  createdAt DateTime

  @@index([authorId, createdAt])  // 复合索引
  @@index([published, createdAt]) // 分页查询索引
}
```

复合索引的设计原则是"最左前缀"。`@@index([authorId, createdAt])`可以加速`WHERE authorId = 1 ORDER BY createdAt DESC`，但不能加速`WHERE createdAt > '2024-01-01'`（跳过了authorId）。

分页查询的索引设计规则：

第一，WHERE条件字段放前面。第二，ORDER BY字段放后面。第三，避免SELECT *，只查需要的字段。

```typescript
// 高效分页查询（有索引支撑）
const posts = await prisma.post.findMany({
  where: { published: true },        // 命中 [published, createdAt] 索引
  orderBy: { createdAt: 'desc' },    // 索引有序，无需额外排序
  select: { id: true, title: true }, // 只查需要的字段
  take: 10,
})
```

> 索引不是越多越好。每个索引增加写入开销和存储空间。怕浪猫的索引设计原则是：先不加索引跑起来，通过EXPLAIN分析慢查询，针对性地加索引。盲目加索引反而会拖慢写入性能。

## 8.7 本章小结与课后练习

这一章信息量很大，怕浪猫帮你梳理核心知识脉络：

数据库选型上，关系型优先PostgreSQL，文档型选MongoDB。ORM在Next.js生态首选Prisma，追求轻量选Drizzle。Serverless环境务必处理连接池问题。

CRUD操作上，Prisma的API设计统一且类型安全，创建用`create`/`createMany`，查询用`findMany`配合丰富的过滤操作符，更新用`update`/`updateMany`配合原子操作符，删除优先软删除。

事务处理上，`$transaction`回调方式是首选，事务内只做必须原子性的操作，P2034冲突要实现自动重试，隔离级别按需提升。

分页优化上，浅分页用`skip/take`偏移分页，深分页用`cursor`游标分页。索引设计遵循最左前缀原则，WHERE字段在前，ORDER BY字段在后。

**课后练习：**

1. 使用Prisma + PostgreSQL搭建一个博客系统的数据层，包含User、Post、Comment三个模型，建立一对多和多对多关系。

2. 实现一个分页查询API，支持游标分页和偏移分页两种模式，通过查询参数切换。写一个性能对比脚本，测试在10000条数据下两种分页方式的响应时间差异。

3. 实现一个转账功能，使用Prisma事务保证原子性。要求：扣款方余额不足时回滚并返回错误；记录转账流水；实现冲突自动重试机制。

4. 使用MongoDB聚合管道实现一个内容分析功能：统计每篇文章的评论数、平均评分、最新评论时间，并按平均评分排序输出Top 10。

**下章预告：** 第9章将进入认证与授权的世界。从NextAuth.js（Auth.js）的配置到JWT（JSON Web Token）与Session策略的选择，从OAuth第三方登录到RBAC（Role-Based Access Control，基于角色的访问控制）权限设计，我会带你实现一套完整的生产级认证体系。认证这坑，比数据库还深。

---

怕浪猫说：数据库对接是从前端迈向全栈的必经之路。选对工具，理解原理，敬畏事务，优化查询——这四条心法记住了，80%的数据库问题都不会成为问题。剩下的20%，就是踩坑积累的经验了。代码写百遍，其义自见。下一篇，认证授权见。

系列进度 8/16
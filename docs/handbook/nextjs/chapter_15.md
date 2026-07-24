# 第15章 项目打包、部署与CI/CD自动化

部署不是"代码写完了上线就完事"。从构建到部署到监控，每一步都有坑。构建产物太大导致部署慢，没有CD导致用户访问慢，没有回滚机制导致出了问题只能手忙脚乱。这章把部署的完整链路讲透。

我是怕浪猫，一个把部署流程自动化到极致的全栈开发者。这章覆盖Next.js打包部署的全流程——从Vercel一键部署到Docker容器化，从Nginx配置到CI/CD（Continuous Integration / Continuous Deployment，持续集成/持续部署）流水线，帮你把项目安全高效地推到生产环境。

## 15.1 项目打包命令与产物分析

### 15.1.1 生产构建流程

```bash
# 构建命令
npm run build

# 启动生产服务器
npm run start
# 默认监听3000端口，可通过-p指定
```

构建过程：
```
npm run build
    ↓
收集页面信息（分析路由、组件依赖）
    ↓
编译Server Components → 服务端JS
编译Client Components → 客户端JS chunk
    ↓
静态生成(SSG) → 预渲染HTML
    ↓
写入.next/目录
```

### 15.1.2 standalone输出模式

```javascript
// next.config.js
module.exports = {
  output: 'standalone',
}
```

standalone模式生成一个独立的部署包，只包含运行所需的文件：

```
.next/standalone/
├── server.js          ← 入口文件
├── node_modules/      ← 精简后的依赖
├── package.json
└── .next/
    └── server/        ← 编译后的服务端代码
```

> standalone模式是Docker部署的基础。不带standalone，你的Docker镜像要把整个node_modules都打进去，镜像大小轻松超过1GB。带了standalone，镜像可以控制在200MB以内。

### 15.1.3 构建产物目录结构

```
.next/
├── static/
│   ├── chunks/        ← 客户端JS chunk
│   ├── css/           ← CSS文件
│   ├── media/         ← 静态资源(图片/字体)
│   └── pages/         ← 页面相关资源
├── server/
│   ├── app/           ← Server Components编译输出
│   ├── pages/         ← Pages Router(如有)
│   └── chunks/        ← 服务端共享chunk
├── standalone/        ← standalone输出
├── BUILD_ID           ← 构建版本ID
└── trace              ← 构建追踪信息
```

### 15.1.4 构建产物分析

```javascript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
module.exports = withBundleAnalyzer({})

// 运行
// ANALYZE=true npm run build
```

### 15.1.5 构建性能优化

| 策略 | 效果 | 说明 |
|------|------|------|
| 构建缓存 | 高 | .next/cache目录 |
| 增量构建 | 高 | turbo monorepo |
| 并行构建 | 中 | 多线程编译 |
| 减少页面数 | 高 | 动态路由替代大量静态页面 |
| 依赖优化 | 中 | 减少重型依赖 |

## 15.2 Vercel一键零配置部署

### 15.2.1 Vercel平台介绍

Vercel是Next.js的官方部署平台，零配置即可部署：

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
vercel

# 生产部署
vercel --prod
```

### 15.2.2 Git集成自动部署

```
关联GitHub仓库
    ↓
push到main分支 → 自动触发生产部署
push到其他分支 → 自动触发预览部署
提交PR → 生成预览URL
    ↓
构建 → 部署 → 分配URL
    ↓
预览: xxx.vercel.app
生产: your-domain.com
```

> Vercel的Git集成是它最大的卖点。push即部署，PR自动生成预览链接，团队成员可以直接在预览环境测试。不用再"帮我部署一下看看效果"。

### 15.2.3 预览部署与生产部署

| 类型 | 触发 | URL | 环境变量 |
|------|------|-----|---------|
| 预览 | 非main分支push | random.vercel.app | 预览环境 |
| 生产 | main分支push/手动 | your-domain.com | 生产环境 |

### 15.2.4 环境变量配置

```bash
# Vercel CLI设置环境变量
vercel env add DATABASE_URL production
vercel env add NEXT_PUBLIC_API_URL preview production
```

### 15.2.5 Vercel Edge Network

Vercel默认通过Edge Network全球分发：
- 静态资源走CDN
- Serverless Functions就近执行
- Image Optimization自动优化图片
- 全球300+边缘节点

## 15.3 服务器Nginx部署与反向代理

### 15.3.1 Node.js服务器运行

```bash
# 启动Next.js生产服务器
npm run start -p 3000

# 或用环境变量指定端口
PORT=3000 npm run start
```

### 15.3.2 PM2进程管理

```bash
# 安装PM2
npm install -g pm2

# 启动Next.js
pm2 start npm --name "nextjs" -- start

# 常用命令
pm2 status          # 查看状态
pm2 logs nextjs     # 查看日志
pm2 restart nextjs  # 重启
pm2 stop nextjs     # 停止
pm2 startup         # 设置开机自启
pm2 save            # 保存进程列表
```

> 没有PM2的Node.js部署是在"裸奔"。进程崩溃了没人重启，服务器重启了应用不会自动恢复。PM2解决这两个问题：进程守护和开机自启。

### 15.3.3 Nginx反向代理配置

```nginx
# /etc/nginx/conf.d/nextjs.conf
server {
    listen 80;
    server_name example.com;

    # 反向代理到Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 15.3.4 HTTPS证书配置

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 申请Let's Encrypt证书
sudo certbot --nginx -d example.com

# 自动续期
sudo certbot renew --dry-run
```

### 15.3.5 Nginx性能调优

```nginx
# gzip压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1024;

# brotli压缩(如果安装了模块)
brotli on;
brotli_types text/plain text/css application/json application/javascript;

# 连接数优化
worker_connections 1024;
keepalive_timeout 65;
```

## 15.4 Docker容器化部署

### 15.4.1 Dockerfile多阶段构建

```dockerfile
# Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

> 多阶段构建是Docker镜像优化的标准做法。第一阶段装依赖，第二阶段构建，第三阶段只拷贝运行所需的文件。最终镜像不含构建工具，体积小、攻击面小。

### 15.4.2 standalone与Docker结合

standalone模式 + Docker = 最小化镜像：

```
完整node_modules: ~500MB
standalone模式:    ~150MB
Alpine基础镜像:    ~50MB
最终镜像:          ~200MB
```

### 15.4.3 docker-compose编排

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://db:5432/myapp
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web

volumes:
  db_data:
```

### 15.4.4 镜像优化

| 优化策略 | 效果 | 说明 |
|---------|------|------|
| Alpine基础镜像 | -100MB | 用alpine替代完整版 |
| 多阶段构建 | -300MB | 只拷贝运行文件 |
| .dockerignore | 中 | 排除不必要文件 |
| 依赖缓存层 | 快 | 先COPY package.json |
| standalone模式 | -200MB | 最小化运行时 |

### 15.4.5 Docker安全注意事项

```dockerfile
# 使用非root用户运行
FROM node:18-alpine
RUN addgroup -g 1001 nodejs && adduser -S nextjs -u 1001
USER nextjs

# 不内嵌敏感信息
# 错误: ENV JWT_SECRET=xxx
# 正确: 通过环境变量注入
```

## 15.5 云服务器部署实战

### 15.5.1 云服务器选购

| 规格 | 适合场景 | 月费参考 |
|------|---------|---------|
| 2核4G | 个人项目/测试 | 50-100元 |
| 4核8G | 中小型应用 | 200-400元 |
| 8核16G | 生产环境 | 500-1000元 |
| 按量付费 | 突发流量 | 按使用量 |

### 15.5.2 域名解析与备案

```
1. 购买域名
2. ICP备案(国内服务器必须)
3. DNS解析: A记录指向服务器IP
4. 配置HTTPS证书
```

### 15.5.3 服务器环境搭建

```bash
# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装PM2
sudo npm install -g pm2

# 安装Nginx
sudo apt install -y nginx

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 配置防火墙
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable
```

### 15.5.4 数据库部署

| 方案 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| 云数据库 | 免运维、自动备份 | 贵 | 生产环境 |
| 自建数据库 | 便宜、灵活 | 需要运维 | 预算有限 |
| Docker数据库 | 快速部署 | 数据安全需注意 | 开发/测试 |

## 15.6 GitHub Actions CI/CD

### 15.6.1 基础概念

```
Workflow → 工作流(.github/workflows/目录下的YAML)
  ↓
Job → 任务(可并行或串行)
  ↓
Step → 步骤(按顺序执行)
  ↓
Action → 动作(可复用的步骤)
```

### 15.6.2 CI流程

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm run test
      - run: npm run build
```

### 15.6.3 CD流程：自动部署

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
      - run: npm ci
      - run: npm run build

      # 部署到Vercel
      - name: Deploy to Vercel
        run: npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}

      # 或部署到自有服务器
      - name: Deploy to Server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app
            git pull origin main
            npm ci
            npm run build
            pm2 restart nextjs
```

> CI/CD的价值在于"自动化"。每次push自动检查、自动测试、自动部署。人工部署的每一个步骤都可能出错，自动化的流程一旦配好，就是100%一致执行。

### 15.6.4 环境变量与Secrets

```yaml
# 在GitHub仓库 Settings → Secrets and variables → Actions 中添加
# 不要在YAML中硬编码敏感信息
steps:
  - name: Build
    run: npm run build
    env:
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      JWT_SECRET: ${{ secrets.JWT_SECRET }}
```

### 15.6.5 多环境部署

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - run: npx vercel --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ENV: preview

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ENV: production
```

## 15.7 上线性能监控与运维

### 15.7.1 性能监控

```tsx
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

### 15.7.2 健康检查

```typescript
// app/api/health/route.ts
export async function GET() {
  return Response.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  })
}
```

```yaml
# docker-compose.yml 健康检查
services:
  web:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 15.7.3 零停机部署

| 方案 | 说明 | 适用 |
|------|------|------|
| 蓝绿部署 | 两套环境切换 | Vercel自动支持 |
| 滚动更新 | 逐个替换实例 | Docker/K8s |
| 金丝雀发布 | 小流量先试 | 大规模应用 |

> Vercel的部署天然是零停机的：新版本部署成功后才切流量，失败自动回滚。自有服务器要实现零停机，最简单的方式是蓝绿部署——两个端口，Nginx切换upstream。

### 15.7.4 回滚

```bash
# Vercel回滚
vercel rollback [deployment-url]

# PM2回滚
pm2 reload nextjs  # 快速重启

# Git回滚
git revert HEAD
git push origin main
# CI/CD自动触发重新部署

# Docker回滚
docker-compose pull && docker-compose up -d
```

### 15.7.5 运维SOP

| 事件 | 响应时间 | 操作 |
|------|---------|------|
| 生产故障 | <5分钟 | 查看Sentry → 回滚 → 排查 |
| 性能下降 | <30分钟 | 查看监控 → 定位瓶颈 |
| 依赖安全漏洞 | <24小时 | 评估影响 → 升级 |
| 告警通知 | 即时 | 确认 → 处理 → 记录 |

## 15.8 本章小结与课后练习

### 核心知识点回顾

| 知识点 | 关键内容 |
|--------|---------|
| 打包构建 | standalone模式、bundle分析 |
| Vercel部署 | Git集成、预览/生产环境 |
| Nginx部署 | 反向代理、HTTPS、性能调优 |
| Docker部署 | 多阶段构建、standalone、compose |
| CI/CD | GitHub Actions、lint+test+build+deploy |
| 运维 | 监控、健康检查、零停机、回滚 |

### 课后练习

1. 配置standalone输出模式，用Docker部署Next.js应用
2. 编写Nginx反向代理配置，支持HTTPS和静态资源缓存
3. 配置GitHub Actions CI流程：lint + typecheck + test + build
4. 配置GitHub Actions CD流程：push到main自动部署
5. 实现/api/health健康检查接口，配置Docker健康检查

> 部署是项目开发的"最后一公里"。最后一公里走不好，前面99%的努力都白费。

觉得有用？收藏起来，下次部署直接照着配。

你用的什么部署方案？Vercel、Docker还是裸机？评论区聊聊。

关注怕浪猫，下期是我们这个系列的最后一章——Next.js全栈博客系统综合实战，把前面15章学的所有知识整合到一个完整项目中，从0到1构建一个生产级应用。

**系列进度 15/16**

**怕浪猫说**

部署运维是开发者的"基本功"，不是"加分项"。能写代码但不能部署，就像会做饭但不会开火。这篇文章里的每个配置模板都是我实际在用的，复制过去改改就能跑。下一章见。

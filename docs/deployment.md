---
title: 部署指南
description: 部署 Docusaurus 到各种平台
sidebar_position: 5
---

# 部署指南

Docusaurus 构建产物是纯静态 HTML，可部署到任何静态服务器。

## 构建产物

```bash
npm run build
# 产物输出到 build/ 目录
```

## 部署方式

### 静态服务器（Nginx）

```nginx
server {
    listen 80;
    server_name docs.example.com;
    root /var/www/docusaurus-demo/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Vercel

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel
```

### GitHub Pages

在 `.github/workflows/deploy.yml` 中配置 GitHub Actions：

```yaml
name: Deploy to GitHub Pages
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
          node-version: 22
      - run: npm ci
      - run: npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

### Docker

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

:::tip
建议使用 Docker 部署，环境一致性好，便于 CI/CD 集成。
:::

---
title: 快速开始
description: 5 分钟上手知识库
sidebar_position: 2
---

# 快速开始

本指南将帮助你在 5 分钟内启动项目。

## 环境要求

- **Node.js** >= 20.0
- **npm** >= 10 或 **pnpm** >= 8

## 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/docs.git
cd docs

# 安装依赖
npm install
```

## 启动开发服务器

```bash
npm start
```

浏览器访问 `http://localhost:3000` 即可看到文档站点。

:::info 热重载
修改 Markdown 文件后，浏览器会自动刷新，无需手动重启。
:::

## 构建生产版本

```bash
npm run build
```

构建产物输出到 `build/` 目录，是纯静态 HTML 文件，可部署到任何静态服务器。

## 添加文档

在 `docs/` 目录下创建 `.md` 文件即可：

```markdown
---
title: 我的文档
sidebar_position: 3
---

# 我的文档

这里是内容。
```

:::tip 侧边栏排序
通过 `sidebar_position` frontmatter 字段控制文档在侧边栏中的排序。
:::

## 目录结构

```
docusaurus-demo/
├── docs/               # 文档目录
│   ├── intro.md        # 入门指南
│   ├── quick-start.md  # 快速开始
│   └── guide/          # 子目录
├── blog/               # 博客目录
├── src/
│   ├── components/     # React 组件
│   ├── css/            # 全局样式
│   ├── pages/          # 页面
│   └── theme/          # 主题覆盖
├── static/             # 静态资源
├── docusaurus.config.ts # 主配置
└── sidebars.ts         # 侧边栏配置
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm start` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run serve` | 本地预览构建产物 |
| `npm run clear` | 清除缓存和构建产物 |
| `npm run typecheck` | TypeScript 类型检查 |

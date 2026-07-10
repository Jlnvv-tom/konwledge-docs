---
title: 主题定制
description: 如何自定义 Docusaurus 主题样式
sidebar_position: 4
---

# 主题定制

本项目的主题定制通过三层方案实现：CSS 变量覆盖 → 组件样式定制 → 主题组件覆盖。

## 第一层：CSS 变量覆盖

编辑 `src/css/custom.css`，覆盖 Infima 框架的 CSS 变量：

```css
:root {
  /* 主色调 */
  --ifm-color-primary: #4f46e5;
  --ifm-color-primary-dark: #4338ca;
  --ifm-color-primary-light: #6366f1;

  /* 字体 */
  --ifm-font-family-base: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --ifm-font-family-monospace: 'JetBrains Mono', 'Fira Code', monospace;

  /* 圆角 */
  --ifm-global-radius: 8px;
}
```

## 第二层：组件样式定制

直接在 `custom.css` 中写 CSS，覆盖导航栏、侧边栏、代码块等样式：

```css
/* 毛玻璃导航栏 */
.navbar {
  backdrop-filter: saturate(180%) blur(20px);
  background-color: rgba(255, 255, 255, 0.85);
}

/* 卡片悬浮效果 */
.card:hover {
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
}
```

## 第三层：主题组件覆盖

通过 `src/theme/` 目录覆盖 Docusaurus 内置组件：

```
src/theme/
├── DocItem/
│   └── Layout/
│       └── index.tsx    # 覆盖文档页布局
```

示例 — 在文档页顶部添加自定义横幅：

```tsx
import React from 'react';
import Layout from '@theme-original/DocItem/Layout';

export default function LayoutWrapper(props) {
  return (
    <>
      <div style={{
        background: '#4f46e5',
        color: '#fff',
        padding: '8px 16px',
        textAlign: 'center'
      }}>
        🎉 知识库 v2.0 已发布
      </div>
      <Layout {...props} />
    </>
  );
}
```

## 暗色模式

暗色主题通过 `[data-theme='dark']` 选择器覆盖：

```css
[data-theme='dark'] {
  --ifm-color-primary: #818cf8;
  --ifm-background-color: #0f172a;
  --ifm-background-surface-color: #1e293b;
}
```

## 自定义首页

首页是一个 React 页面组件 `src/pages/index.tsx`，可以完全自定义：

- Hero 区域：渐变背景 + 标题 + CTA 按钮
- Features 区域：卡片式布局展示特性
- Stats 区域：统计数据展示
- 代码展示区：左文右代码的布局

## 本项目的定制清单

| 定制项 | 实现方式 |
|--------|---------|
| 靛蓝主色调 | CSS 变量覆盖 |
| 毛玻璃导航栏 | `.navbar` 样式 |
| 渐变 Hero | 自定义首页组件 |
| 卡片悬浮效果 | `.featureCard:hover` |
| 美化滚动条 | `::-webkit-scrollbar` |
| 暗色模式 | `[data-theme='dark']` |
| 文档页顶部横幅 | 主题组件覆盖 |
| 公告条 | `announcementBar` 配置 |

---
title: 主题 API
description: 主题定制接口参考
sidebar_position: 3
sidebar_label: 主题
---

# 主题 API

## CSS 变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `--ifm-color-primary` | `#2e8555` | 主色调 |
| `--ifm-color-primary-dark` | — | 主色调暗色 |
| `--ifm-color-primary-light` | — | 主色调亮色 |
| `--ifm-font-family-base` | system fonts | 正文字体 |
| `--ifm-font-family-monospace` | monospace | 代码字体 |
| `--ifm-global-radius` | `4px` | 全局圆角 |
| `--ifm-container-width` | `1140px` | 容器宽度 |

## 组件覆盖

通过 `src/theme/` 目录覆盖内置组件：

| 组件路径 | 说明 |
|---------|------|
| `src/theme/DocItem/Layout` | 文档页布局 |
| `src/theme/DocSidebar` | 侧边栏 |
| `src/theme/Navbar` | 导航栏 |
| `src/theme/Footer` | 页脚 |
| `src/theme/CodeBlock` | 代码块 |

## Swizzle 命令

```bash
# 查看可 swizzle 的组件
npm run swizzle -- --list

# 弹出组件源码
npm run swizzle @docusaurus/theme-classic DocItem/Layout -- --wrap
```

---
title: 配置 API
description: Docusaurus 配置项参考
sidebar_position: 2
sidebar_label: 配置
---

# 配置 API

## docusaurus.config.ts

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `string` | 网站标题 |
| `tagline` | `string` | 标语 |
| `url` | `string` | 生产环境 URL |
| `baseUrl` | `string` | 部署子路径 |
| `i18n` | `object` | 国际化配置 |
| `presets` | `array` | 预设插件 |
| `plugins` | `array` | 插件列表 |
| `themeConfig` | `object` | 主题配置 |

## themeConfig.navbar

```typescript
navbar: {
  title: '知识库',
  logo: { alt: 'Logo', src: 'img/logo.svg' },
  items: [
    { type: 'docSidebar', sidebarId: 'tutorialSidebar', label: '文档' },
    { to: '/blog', label: '博客' }
  ]
}
```

## themeConfig.footer

```typescript
footer: {
  style: 'dark',
  links: [
    { title: '文档', items: [...] },
    { title: '社区', items: [...] }
  ],
  copyright: 'Copyright © 2026'
}
```

## themeConfig.prism

```typescript
prism: {
  theme: prismThemes.github,
  darkTheme: prismThemes.dracula,
  additionalLanguages: ['bash', 'json', 'yaml', 'typescript']
}
```

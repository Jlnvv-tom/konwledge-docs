---
title: Markdown 语法
description: Docusaurus 支持的 Markdown 语法一览
sidebar_position: 3
---

# Markdown 语法

Docusaurus 支持 Standard Markdown + GFM + MDX 扩展语法。

## 标题

```markdown
# 一级标题
## 二级标题
### 三级标题
```

## 文本样式

- **粗体** `**粗体**`
- *斜体* `*斜体*`
- `行内代码` `` `行内代码` ``
- ~~删除线~~ `~~删除线~~`

## 代码块

支持多语言语法高亮，含行号显示：

```typescript
interface User {
  name: string;
  age: number;
}

function greet(user: User): string {
  return `Hello, ${user.name}!`;
}

const alice: User = { name: 'Alice', age: 30 };
console.log(greet(alice));
```

```bash
# Shell 脚本
npm install
npm run build
```

```json
{
  "name": "my-project",
  "version": "1.0.0"
}
```

## Admonition 容器

:::note 注意
这是一个 note 容器，用于补充信息。
:::

:::tip 提示
这是一个 tip 容器，用于给出建议。
:::

:::info 信息
这是一个 info 容器，用于提供上下文。
:::

:::caution 警告
这是一个 caution 容器，用于提醒风险。
:::

:::danger 危险
这是一个 danger 容器，用于警告严重问题。
:::

## 表格

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | string | - | 网站标题 |
| theme | 'light' \| 'dark' | 'light' | 主题模式 |
| search | boolean | true | 是否启用搜索 |

## 引用

> 这是一段引用文本。
>
> 可以包含多行。

## 列表

无序列表：
- 第一项
- 第二项
  - 嵌套项 1
  - 嵌套项 2
- 第三项

有序列表：
1. 第一步
2. 第二步
3. 第三步

## 链接和图片

- 内部链接：[快速开始](./quick-start)
- 外部链接：[Docusaurus 官网](https://docusaurus.io)

## frontmatter

每篇文档顶部可以添加 YAML 元数据：

```yaml
---
title: 文档标题
description: 文档描述
sidebar_position: 1
sidebar_label: 显示名称
slug: /custom-url
---
```

## 代码组

:::tip 代码组示例
可以在文档中使用 Tabs 组件展示多语言代码示例，但需要使用 MDX 语法（`.mdx` 文件）。
:::

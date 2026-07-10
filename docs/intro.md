---
title: 入门指南
description: 了解知识库的基本使用方法
sidebar_position: 1
---

# 入门指南

欢迎使用 **知识库** —— 一个基于 Docusaurus 构建的高性能技术文档中心。

## 为什么选择 Docusaurus

从 VitePress 迁移到 Docusaurus 的核心原因：

:::tip 构建 OOM 问题
VitePress 在构建上千份文档时，会将所有页面全量加载到 V8 堆内存中，峰值可达 8GB+，导致 `JavaScript heap out of memory` 错误。Docusaurus 采用逐页编译渲染策略，不会出现此问题。
:::

## 核心特性

| 特性 | 说明 |
|------|------|
| 📝 纯 Markdown | `.md` 文件直接使用，无需改后缀 |
| 🛡️ 内存安全 | 逐页构建，不 OOM |
| 🔍 全文搜索 | 内置本地搜索，支持中英文 |
| 🌙 暗色模式 | 自动跟随系统偏好 |
| 📱 响应式 | 完美适配移动端 |
| 🎨 定制主题 | CSS 变量 + 组件覆盖 |

## 快速导航

- [快速开始](./quick-start) — 5 分钟上手
- [Markdown 语法](./markdown-syntax) — 支持的语法一览
- [主题定制](./theme-customization) — 如何自定义样式
- [部署指南](./deployment) — 部署到各种平台

## 下一步

准备好开始了吗？前往 [快速开始](./quick-start) 创建你的第一篇文档。

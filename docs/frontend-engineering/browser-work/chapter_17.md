---
sidebar_position: 17
---

# 第17章 Core Web Vitals 与性能指标

> LCP、INP、CLS 是 Google 定义的核心 Web 指标。它们不是技术指标，而是用户体验指标——衡量的是用户看到的、感受到的、被迫等待的。

我是怕浪猫，从这章开始进入性能优化。第 17 章拆解 Core Web Vitals 三大指标（LCP、INP、CLS）的测量原理、评级标准和优化策略。

## 17.1 Core Web Vitals 概述

### 17.1.1 三大核心指标

Core Web Vitals（核心 Web 指标）是 Google 定义的一组用户体验关键指标，用于衡量页面的加载体验、交互性和视觉稳定性。

| 指标 | 全称 | 衡量维度 | 2024 标准 |
|------|------|---------|-----------|
| LCP | Largest Contentful Paint | 加载体验 | < 2.5s |
| INP | Interaction to Next Paint | 交互响应 | < 200ms |
| CLS | Cumulative Layout Shift | 视觉稳定 | < 0.1 |

```
Core Web Vitals 时间线

2020: 首次发布
  - FID（First Input Delay）替代 LCP 作为交互指标
  - LCP、FID、CLS 为三大指标

2024.3: INP 替代 FID
  - INP 更全面地衡量交互响应
  - FID 只测量首次输入延迟，不测量处理时间
```

### 17.1.2 实验数据 vs 字段数据

性能指标有两种测量方式：实验数据（Lab Data）和字段数据（Field Data）。

| 数据类型 | 来源 | 特点 | 工具 |
|---------|------|------|------|
| 实验数据 | 受控环境模拟 | 可重复、可调试 | Lighthouse、DevTools |
| 字段数据 | 真实用户 | 反映真实体验 | CrUX、Web Vitals JS |

```javascript
// 使用 Web Vitals JS 库收集字段数据
import { onLCP, onINP, onCLS } from 'web-vitals';

onLCP((metric) => {
  console.log('LCP:', metric.value, 'ms');
});

onINP((metric) => {
  console.log('INP:', metric.value, 'ms');
});

onCLS((metric) => {
  console.log('CLS:', metric.value);
});

// 上报到分析服务
function report(metric) {
  navigator.sendBeacon('/analytics', JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,  // 'good' | 'needs-improvement' | 'poor'
    id: metric.id
  }));
}
```

> 实验数据和字段数据可能差异很大。Lighthouse 在快速网络下测试，LCP 可能是 1.5s。但真实用户在 4G 网络下，LCP 可能是 3s。Google 搜索排名使用的是 CrUX 字段数据，不是 Lighthouse 实验数据。

## 17.2 LCP（Largest Contentful Paint）

### 17.2.1 LCP 的定义

LCP 测量页面上最大内容元素的渲染时间。内容元素包括 `<img>`、`<video>`、`<div>` 中的文本块、背景图片等。

```
LCP 测量时间线

页面加载过程：
  T=0:    导航开始
  T=0.2s: HTML 开始解析
  T=0.5s: 首屏内容开始渲染（FCP）
  T=1.0s: 图片开始加载
  T=2.0s: 图片加载完成 → LCP = 2.0s
  
  如果后续有更大的内容渲染：
  T=3.0s: 更大的图片渲染 → LCP 更新为 3.0s
  
  用户首次交互后，LCP 停止更新
```

| LCP 值 | 评级 | 说明 |
|--------|------|------|
| < 2.5s | 好 | 用户感觉加载快 |
| 2.5-4s | 需改进 | 用户可能感觉慢 |
| > 4s | 差 | 用户感觉明显等待 |

### 17.2.2 LCP 的组成部分

LCP 的时间可以分解为多个阶段，每个阶段对应不同的优化方向。

```
LCP 时间分解

总 LCP 时间
  │
  ├─ TTFB（Time to First Byte）
  │   服务器响应时间
  │   优化：CDN、缓存、服务器性能
  │
  ├─ 资源加载延迟
  │   从 HTML 到开始加载 LCP 资源的时间
  │   优化：preload、减少阻塞资源
  │
  ├─ 资源加载时间
  │   LCP 资源本身的加载时间
  │   优化：图片优化、压缩、CDN
  │
  └─ 资源渲染时间
      从资源加载完到渲染完成的时间
      优化：减少主线程阻塞
```

| 阶段 | 典型占比 | 优化方向 |
|------|---------|---------|
| TTFB | 10-20% | CDN、缓存、SSR |
| 资源延迟 | 20-30% | preload、减少阻塞 |
| 资源加载 | 40-60% | 图片优化、HTTP/2 |
| 渲染时间 | 5-15% | 减少长任务、CSS 优化 |

### 17.2.3 LCP 优化策略

```html
<!-- 1. Preload LCP 图片 -->
<link rel="preload" as="image" href="/hero.jpg" fetchpriority="high">

<!-- 2. 避免阻塞渲染的 CSS -->
<link rel="stylesheet" href="/critical.css">
<!-- 非关键 CSS 异步加载 -->
<link rel="stylesheet" href="/non-critical.css" media="print" onload="this.media='all'">

<!-- 3. 图片优化 -->
<img src="/hero.jpg" 
     width="800" height="600"
     fetchpriority="high"
     decoding="async"
     alt="Hero image">

<!-- 4. 避免 LCP 元素被 JS 动态插入 -->
```

| 优化策略 | 效果 | 实施难度 |
|---------|------|---------|
| Preload LCP 资源 | 减少 0.5-1s | 低 |
| 图片压缩+WebP/AVIF | 减少 30-50% 体积 | 低 |
| SSR/SSG | 减少 TTFB | 中 |
| 减少关键 CSS | 减少渲染阻塞 | 中 |
| fetchpriority="high" | 优先 LCP 资源 | 低 |

## 17.3 INP（Interaction to Next Paint）

### 17.3.1 INP 的定义

INP 测量用户交互到下一帧绘制的时间。它取页面所有交互中的最差值（或接近最差），反映用户对交互响应的整体感受。

```
INP 测量

用户交互 → 事件回调执行 → 渲染 → 下一帧绘制

INP = 下一帧绘制时间 - 用户交互时间

页面所有交互的 INP 值：
  交互1: 50ms
  交互2: 200ms
  交互3: 80ms
  交互4: 350ms ← 最差
  交互5: 100ms
  
  INP = 350ms（最差值，但忽略极少数异常值）
```

| INP 值 | 评级 | 说明 |
|--------|------|------|
| < 200ms | 好 | 用户感觉响应快 |
| 200-500ms | 需改进 | 用户感觉延迟 |
| > 500ms | 差 | 用户感觉明显卡顿 |

### 17.3.2 INP 的三个阶段

INP 的时间可以分解为三个阶段。

```
INP 三阶段

1. 输入延迟（Input Delay）
   用户交互到事件回调开始执行
   │  原因：主线程忙于其他任务
   │  优化：减少长任务、任务分片
   ▼
2. 事件处理时间（Processing Time）
   事件回调执行时间
   │  原因：回调逻辑复杂
   │  优化：优化回调代码、Web Worker
   ▼
3. 渲染延迟（Presentation Delay）
   事件回调完成到下一帧绘制
   │  原因：渲染管线耗时
   │  优化：减少布局/绘制开销
```

| 阶段 | 典型占比 | 优化方向 |
|------|---------|---------|
| 输入延迟 | 20-40% | 减少长任务 |
| 事件处理 | 30-50% | 优化回调代码 |
| 渲染延迟 | 20-30% | 减少渲染开销 |

### 17.3.3 INP 优化策略

```javascript
// 1. 任务分片，避免长任务
function yieldToMain() {
  return new Promise(resolve => {
    if (scheduler.yield) {
      return scheduler.yield();
    }
    setTimeout(resolve, 0);
  });
}

async function handleInteraction(e) {
  // 快速响应
  updateUI(e);
  
  // 让出主线程
  await yieldToMain();
  
  // 耗时操作放到后面
  doExpensiveWork();
}

// 2. 使用 requestIdleCallback 做非紧急工作
function doNonUrgentWork() {
  requestIdleCallback((deadline) => {
    while (deadline.timeRemaining() > 0) {
      doWork();
    }
  });
}

// 3. Web Worker 处理计算密集任务
const worker = new Worker('compute.worker.js');
worker.postMessage({ data: largeData });
worker.onmessage = (e) => {
  // 主线程只做 UI 更新
  updateUI(e.data);
};
```

| 优化策略 | 减少的阶段 | 效果 |
|---------|-----------|------|
| scheduler.yield() | 输入延迟 | 让主线程处理输入 |
| 任务分片 | 输入延迟 | 减少单次阻塞 |
| Web Worker | 事件处理 | 不阻塞主线程 |
| requestIdleCallback | 事件处理 | 空闲时执行 |
| 减少布局抖动 | 渲染延迟 | 避免 forced reflow |

### 17.3.4 INP 与 FID 的区别

INP 在 2024 年 3 月正式取代了 FID（First Input Delay，首次输入延迟）。两者的核心区别在于测量范围。

| 特性 | FID | INP |
|------|-----|-----|
| 测量范围 | 仅首次输入 | 所有交互 |
| 测量内容 | 仅输入延迟 | 输入延迟+处理+渲染 |
| 敏感度 | 低 | 高 |
| 反映体验 | 首次交互 | 整体交互 |

FID 只测量用户首次交互的输入延迟（从交互到回调开始执行的时间），不包括回调执行和渲染时间。这意味着即使回调执行了 500ms，只要输入延迟低，FID 就好。INP 全面测量从交互到下一帧绘制的完整时间，更准确地反映用户体验。

> INP 是最难的指标。LCP 可以通过 preload 和图片优化快速改善，但 INP 需要分析所有交互路径，找到慢的回调并优化。scheduler.yield() 是 2024 年的新 API，是解决 INP 问题的利器。

## 17.4 CLS（Cumulative Layout Shift）

### 17.4.1 CLS 的定义

CLS 测量页面生命周期中所有意外布局偏移的累积分数。布局偏移是指元素在屏幕上位置发生了意外变化。

```
CLS 计算示例

场景1: 图片加载导致文字下移
  偏移前：文字在 y=100
  偏移后：文字在 y=150
  偏移距离：50px
  影响区域：文字宽度 × 50px
  
  偏移分数 = 影响区域 / 视口区域

场景2: 字体加载导致文字宽度变化
  偏移前：按钮宽度 80px
  偏移后：按钮宽度 100px
  偏移分数 = ...

CLS = 所有偏移分数的总和（有上限）
```

| CLS 值 | 评级 | 说明 |
|--------|------|------|
| < 0.1 | 好 | 用户几乎不感知偏移 |
| 0.1-0.25 | 需改进 | 用户可能感知到 |
| > 0.25 | 差 | 用户明显感觉跳动 |

### 17.4.2 CLS 的常见原因

| 原因 | 说明 | 解决方案 |
|------|------|---------|
| 图片无尺寸 | 加载后撑开布局 | 设置 width/height |
| 字体加载 | FOIT/FOUT 导致文字跳变 | font-display + size-adjust |
| 动态内容 | 广告/弹窗插入 | 预留空间 |
| 异步加载 | 组件延迟渲染 | Skeleton 占位 |
| CSS 动画 | 使用 margin/top | 使用 transform |

### 17.4.3 CLS 优化策略

```html
<!-- 1. 图片和视频设置尺寸 -->
<img src="/image.jpg" width="800" height="600" alt="...">
<!-- 或使用 aspect-ratio -->
<img src="/image.jpg" style="aspect-ratio: 4/3;" alt="...">

<!-- 2. 广告位预留空间 -->
<div class="ad-slot" style="min-height: 250px;">
  <!-- 广告异步加载到预留空间 -->
</div>

<!-- 3. 字体加载优化 -->
<style>
  @font-face {
    font-family: 'CustomFont';
    src: url('/font.woff2') format('woff2');
    font-display: swap;  /* 先用回退字体，加载后切换 */
    size-adjust: 100%;   /* 调整回退字体大小匹配 */
  }
</style>
```

```css
/* 4. 动画使用 transform 而非 margin/top */
.bad {
  transition: margin 0.3s;
  margin-top: 0;
}
.bad:hover {
  margin-top: -10px;  /* 触发布局 */
}

.good {
  transition: transform 0.3s;
}
.good:hover {
  transform: translateY(-10px);  /* 不触发布局 */
}
```

## 17.5 其他重要性能指标

### 17.5.1 加载阶段指标

| 指标 | 全称 | 说明 | 目标 |
|------|------|------|------|
| TTFB | Time to First Byte | 首字节时间 | < 800ms |
| FCP | First Contentful Paint | 首次内容绘制 | < 1.8s |
| LCP | Largest Contentful Paint | 最大内容绘制 | < 2.5s |
| TTI | Time to Interactive | 可交互时间 | < 3.8s |
| TBT | Total Blocking Time | 总阻塞时间 | < 200ms |

### 17.5.2 指标关系

```
页面加载时间线与指标

T=0    导航开始
       │
T=0.5s TTFB（首字节到达）
       │
T=1.0s FCP（首次内容绘制）
       │  ← TBT 开始计算
T=2.0s │
       │
T=2.5s LCP（最大内容绘制）
       │
T=3.0s │
       │  ← TBT 结束计算
T=3.5s TTI（可交互时间）
       │
T=∞    用户交互
       │
T=∞    INP（交互到绘制）
       │
T=∞    CLS（持续累积）
```

> Core Web Vitals 不是全部。TTFB 是 LCP 的前置指标，优化 TTFB 通常也能改善 LCP。TBT 是 INP 的实验数据代理指标，TBT 高的页面 INP 通常也不好。理解指标间的关系，才能系统性优化。

### 17.5.3 Performance API 详解

Chrome 提供了丰富的 Performance API 用于测量性能指标。开发者可以通过 PerformanceObserver 捕获各种性能事件。

```javascript
// 测量 TTFB
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('TTFB:', entry.responseStart - entry.requestStart);
  }
}).observe({ type: 'navigation', buffered: true });

// 测量长任务
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Long Task:', entry.duration, 'ms');
  }
}).observe({ type: 'longtask', buffered: true });

// 测量资源加载
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Resource:', entry.name, entry.duration, 'ms');
  }
}).observe({ type: 'resource', buffered: true });
```

| Performance API | 测量内容 | 用途 |
|----------------|---------|------|
| navigation | 导航性能 | TTFB、页面加载 |
| resource | 资源加载 | 资源耗时 |
| longtask | 长任务 | > 50ms 的任务 |
| largest-contentful-paint | LCP | 最大内容绘制 |
| layout-shift | CLS | 布局偏移 |
| event | 交互延迟 | INP 计算 |

## 17.6 性能测量工具

| 工具 | 类型 | 用途 | 特点 |
|------|------|------|------|
| Lighthouse | 实验数据 | 综合审计 | 模拟环境 |
| Chrome DevTools | 实验数据 | 深度分析 | 实时调试 |
| CrUX | 字段数据 | 真实用户 | Google 排名依据 |
| PageSpeed Insights | 混合 | 综合评估 | Lighthouse + CrUX |
| Web Vitals JS | 字段数据 | RUM | 嵌入页面收集 |

```javascript
// 使用 PerformanceObserver 测量指标
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('LCP:', entry.startTime, entry.element);
  }
}).observe({ type: 'largest-contentful-paint', buffered: true });

new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.hadRecentInput) continue;  // 忽略有输入的偏移
    console.log('CLS:', entry.value);
  }
}).observe({ type: 'layout-shift', buffered: true });
```

## 17.5 CrUX 数据与 Field Data

### 17.5.1 CrUX 数据来源

CrUX（Chrome User Experience Report，Chrome 用户体验报告）是 Google 收集的真实用户体验数据。它来自数百万 Chrome 用户的实际浏览数据，反映了真实网络条件下的性能表现。

```
CrUX 数据采集流程

  Chrome 用户浏览网页
    → 浏览器自动采集 LCP/CLS/INP 等指标
    → 匿名化处理（不包含个人信息）
    → 上传到 Google 服务器
    → 聚合后公开

  采集条件：
    - 用户已开启使用统计和崩溃报告
    - 页面有足够访问量（前 10000 名）
    - HTTPS 页面
```

| 数据维度 | 说明 |
|---------|------|
| 来源 | 真实 Chrome 用户 |
| 采集 | 自动、匿名 |
| 频率 | 每月更新 |
| 覆盖 | 全球前 10000 名网站 |
| 访问 | PageSpeed Insights / API |

### 17.5.2 Field Data vs Lab Data

| 对比项 | Field Data（CrUX） | Lab Data（Lighthouse） |
|--------|-------------------|---------------------|
| 环境 | 真实用户设备 | 模拟环境 |
| 网络 | 真实网络 | 模拟 3G/4G |
| 设备 | 各种设备 | 模拟中端手机 |
| 样本 | 百万用户 | 单次运行 |
| 稳定性 | 高（大量样本） | 低（单次波动） |
| 发现问题 | 真实瓶颈 | 可复现问题 |

> Field Data 和 Lab Data 经常不一致。Lighthouse 在模拟中端手机 + 3G 网络下测试，可能比真实用户环境更差。CrUX 反映的是真实用户的实际体验，是搜索排名的参考依据。如果两者不一致，以 CrUX 为准。

### 17.5.3 为什么 Lighthouse 分数和 CrUX 不一致

```
常见不一致原因

1. 测试设备差异
   Lighthouse: 模拟中端手机（Moto G）
   CrUX: 包含高端和低端设备

2. 网络条件差异
   Lighthouse: 模拟慢速 3G
   CrUX: 真实网络（WiFi/4G/5G）

3. 用户行为差异
   Lighthouse: 立即加载页面
   CrUX: 用户可能从缓存加载

4. 采样差异
   Lighthouse: 单次测试
   CrUX: 28 天聚合数据
```

## 17.6 Lighthouse 版本演进

### 17.6.1 Lighthouse 主要版本变化

| 版本 | 年份 | 主要变化 |
|------|------|---------|
| 8 | 2022 | 新增 INP 替代 FID |
| 9 | 2023 | 改进 TBT 计算 |
| 10 | 2024 | 移除 TTI、简化评分 |
| 11 | 2025 | 新增 AI 审计 |

### 17.6.2 Lighthouse 10 评分变化

```
Lighthouse 10 性能评分权重

  LCP (25%)  ← 25%
  CLS (30%)  ← 30%
  INP (10%)  ← 新增
  FCP (10%)  ← 10%
  TBT (10%)  ← 10%
  Speed Index (15%)  ← 15%

  移除：TTI（Time to Interactive）
  原因：TTI 与 LCP 高度相关，且计算复杂
```

## 17.7 性能预算

### 17.7.1 性能预算实践

性能预算是为各项指标设定上限，在 CI/CD 中自动检测性能退化。

```json
// performance-budget.json
{
  "resourceSizes": [
    { "resourceType": "script", "budget": 200 },
    { "resourceType": "stylesheet", "budget": 50 },
    { "resourceType": "image", "budget": 500 },
    { "resourceType": "total", "budget": 1000 }
  ],
  "resourceCounts": [
    { "resourceType": "third-party", "budget": 10 }
  ],
  "timings": [
    { "metric": "LCP", "budget": 2500 },
    { "metric": "CLS", "budget": 0.1 },
    { "metric": "INP", "budget": 200 }
  ]
}
```

| 预算类型 | 说明 | 示例 |
|---------|------|------|
| 资源大小 | JS/CSS/图片体积 | JS < 200KB |
| 资源数量 | 第三方请求数量 | 第三方 < 10 个 |
| 时间指标 | Core Web Vitals | LCP < 2.5s |
| 自定义 | 业务指标 | 首屏 < 1.5s |

## 17.8 CrUX 与 RUM 对比

### 17.8.1 RUM 是什么

RUM（Real User Monitoring，真实用户监控）是第三方性能监控方案，通过在页面中注入 JS 采集真实用户体验数据。

| 对比项 | CrUX | RUM |
|--------|------|-----|
| 数据来源 | Chrome 内置 | JS SDK |
| 覆盖范围 | 前 10000 网站 | 任意网站 |
| 采样率 | 全量 | 可配置 |
| 自定义 | 不支持 | 支持 |
| 实时性 | 月度 | 实时 |
| 费用 | 免费 | 付费 |

> CrUX 和 RUM 是互补关系。CrUX 覆盖面广但更新慢、不可自定义。RUM 可以采集业务指标（如首屏商品加载时间）、实时告警、按用户分群分析。对于大型网站，建议同时使用 CrUX（作为搜索排名基准）和 RUM（作为运营监控）。

### 17.8.2 Web Vitals Chrome 扩展

Web Vitals 扩展是 Google 官方提供的浏览器扩展，实时显示当前页面的 Core Web Vitals 指标。它在开发调试时非常有用，可以直接在页面上看到 LCP、CLS、INP 的实时值。

```
Web Vitals 扩展功能

  实时指标：
    - LCP（Largest Contentful Paint）
    - CLS（Cumulative Layout Shift）
    - INP（Interaction to Next Paint）
    - FCP（First Contentful Paint）
    - TTFB（Time to First Byte）

  分析模式：
    - 逐帧分析 CLS 偏移
    - 标记 LCP 元素
    - INP 交互分解
```

## 17.9 性能指标深入分析

### 17.9.1 LCP 元素分析

LCP（Largest Contentful Paint，最大内容绘制）衡量页面主要内容加载完成的时间。理解哪些元素可能成为 LCP 元素，有助于针对性优化。

```
LCP 元素类型分布（CrUX 数据）

  图片:        70%
  文本块:       20%
  视频海报:      5%
  背景图:        3%
  其他:          2%

关键优化点：
  图片 → 压缩、响应式图片、懒加载
  文本 → 字体优化、减少渲染阻塞
  视频 → 优化海报图加载
```

```html
<!-- 响应式图片优化 LCP -->
<img 
  src="hero.jpg"
  srcset="hero-480w.jpg 480w,
          hero-800w.jpg 800w,
          hero-1200w.jpg 1200w"
  sizes="100vw"
  fetchpriority="high"
  decoding="async"
/>
```

### 17.9.2 CLS 常见原因

CLS（Cumulative Layout Shift，累计布局偏移）的常见原因和解决方案。

```
CLS 常见原因及解决

1. 无尺寸的图片/视频
   原因: 浏览器不知道元素大小
   解决: 设置 width/height 或 aspect-ratio

2. 动态注入的内容
   原因: 内容出现推动现有内容
   解决: 预留空间（min-height）

3. Web 字体加载
   原因: 字体加载后文本大小变化
   解决: font-display: swap + size-adjust

4. 顶部横幅/广告
   原因: 延迟加载推动内容
   解决: 预留固定空间
```

| CLS 原因 | 占比 | 解决方案 |
|---------|------|---------|
| 无尺寸图片 | 40% | width/height |
| 动态内容 | 25% | min-height |
| 字体加载 | 20% | font-display |
| 广告/横幅 | 15% | 预留空间 |

### 17.9.3 INP 优化策略

INP（Interaction to Next Paint，交互到下一次绘制）是 2024 年取代 FID 的新指标。FID 只测量首次交互的延迟，INP 测量所有交互中最慢的一次。

```
INP 优化策略

1. 减少长任务
   → 任务 > 50ms = 长任务
   → 拆分为小任务
   → 使用 scheduler.yield()（新 API）

2. 优化事件处理
   → 轻量级事件回调
   → 重计算移到 requestIdleCallback

3. 减少渲染阻塞
   → 避免强制同步布局
   → 使用 CSS transform/opacity

4. 代码分割
   → 减少初始 JS 大小
   → 懒加载非关键代码
```

```javascript
// 使用 scheduler.yield() 拆分长任务
async function processItems(items) {
  for (const item of items) {
    process(item);
    // 让出主线程
    if (scheduler.yield) {
      await scheduler.yield();
    } else {
      await new Promise(r => setTimeout(r, 0));
    }
  }
}
```

| 指标 | FID | INP |
|------|-----|-----|
| 测量对象 | 首次交互 | 所有交互 |
| 取值方式 | 首次延迟 | 最慢一次 |
| 目标 | < 100ms | < 200ms |
| 敏感度 | 低 | 高 |

> INP 比 FID 严格得多。FID 只测量首次交互的输入延迟，很多网站轻松达标。INP 测量整个页面生命周期中所有交互的最慢响应，更能反映真实用户体验。从 FID 到 INP 的转变，让很多原本「达标」的网站变为「需改进」。

## 17.10 性能预算实践

### 17.10.1 设置性能预算

性能预算（Performance Budget）是团队约定的性能指标上限。它将抽象的「性能优化」转化为可量化的约束。

```
性能预算示例

资源预算：
  初始 JS:  ≤ 170KB（gzip）
  初始 CSS: ≤ 14KB（gzip）
  图片:     ≤ 500KB
  字体:     ≤ 50KB
  总传输量:  ≤ 800KB

时间预算：
  LCP:  ≤ 2.5s
  INP:  ≤ 200ms
  CLS:  ≤ 0.1
  TTFB: ≤ 800ms
```

```javascript
// 使用 Lighthouse CI 强制性能预算
// lighthouserc.js
module.exports = {
  ci: {
    assert: {
      assertions: {
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-byte-weight': ['warn', { maxNumericValue: 800000 }],
        'render-blocking-resources': ['error', { maxNumericValue: 0 }],
      }
    },
    collect: {
      url: ['https://example.com'],
      numberOfRuns: 3,
    }
  }
};
```

| 预算类型 | 指标 | 执行方式 |
|---------|------|---------|
| 资源大小 | JS/CSS/图片 | CI 检查 |
| 时间 | LCP/INP/CLS | Lighthouse CI |
| 请求数 | HTTP 请求数 | Bundle Analyzer |
| 第三方脚本 | 外部脚本数 | CSP 白名单 |

> 性能预算的关键不是设置，而是执行。将预算集成到 CI/CD 流水线中，当 PR 超出预算时自动阻止合并。这比「性能优化日」或「性能专项」有效得多——它将性能意识融入日常开发流程。

## 17.11 Field Data vs Lab Data

### 17.11.1 两种数据源对比

```
数据源对比

Lab Data（实验室数据）
  → Lighthouse / WebPageTest
  → 固定网络和设备条件
  → 可复现
  → 但不反映真实用户体验

Field Data（真实用户数据）
  → CrUX / RUM
  → 真实用户设备和网络
  → 不可复现
  → 反映真实体验
```

| 对比 | Lab Data | Field Data |
|------|---------|-----------|
| 来源 | Lighthouse | CrUX/RUM |
| 网络 | 模拟 | 真实 |
| 设备 | 固定 | 多样 |
| 复现 | 是 | 否 |
| 真实性 | 低 | 高 |
| 调试 | 容易 | 困难 |

### 17.11.2 RUM 方案选择

```
RUM（Real User Monitoring）方案

Google CrUX（免费）
  → Chrome 真实用户数据
  → 公开数据集
  → 但只有 Chrome 用户

Cloudflare Radar（免费）
  → 全球网络数据
  → 聚合视图

商业 RUM（Datadog/New Relic/Akamai mPulse）
  → 详细数据
  → 自定义指标
  → 付费

自建 RUM
  → 使用 Performance API
  → 完全自定义
  → 开发维护成本
```

```javascript
// 自建 RUM 示例
const vitals = ['LCP', 'INP', 'CLS'];
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    navigator.sendBeacon('/api/vitals', JSON.stringify({
      name: entry.name,
      value: entry.value,
      id: entry.id,
      page: location.pathname,
      ts: Date.now(),
    }));
  }
}).observe({ type: 'web-vital', buffered: true });
```

> 最佳实践是 Lab Data + Field Data 结合使用。Lab Data 用于开发调试和 CI 回归，Field Data 用于监控真实用户体验。两者都可能发现问题但对方发现不了的问题——Lab Data 可以发现特定条件下的性能回退，Field Data 可以发现特定设备/网络的问题。

## 17.12 Web Vitals 扩展指标

### 17.12.1 核心 Web Vitals 之外的指标

除了核心的 LCP、INP、CLS，Chrome 还定义了一系列辅助指标。

```
Web Vitals 完整体系

核心指标（Core Web Vitals）:
  LCP  (Largest Contentful Paint)     ≤ 2.5s
  INP  (Interaction to Next Paint)    ≤ 200ms
  CLS  (Cumulative Layout Shift)      ≤ 0.1

辅助指标:
  TTFB (Time to First Byte)           ≤ 800ms
  FCP  (First Contentful Paint)       ≤ 1.8s
  TBT  (Total Blocking Time)          ≤ 200ms
  SI   (Speed Index)                  ≤ 3.4s

实验性指标:
  TBT  (Total Blocking Time)          ≤ 200ms
  MPFID(Max Potential First Input Delay) ≤ 130ms
  EIL  (Estimated Input Latency)      ≤ 100ms
```

| 指标 | 测量内容 | 来源 | 目标 |
|------|---------|------|------|
| TTFB | 首字节时间 | Lab + Field | 800ms |
| FCP | 首次内容绘制 | Lab + Field | 1.8s |
| TBT | 总阻塞时间 | Lab only | 200ms |
| SI | 速度指数 | Lab only | 3.4s |

### 17.12.2 TTFB 优化

```
TTFB 优化策略

1. CDN 加速
   → 静态资源就近访问
   → 动态内容边缘计算

2. 缓存策略
   → Service Worker 缓存
   → HTTP 缓存（Cache-Control）
   → CDN 边缘缓存

3. 服务端优化
   → SSR/SSG 预渲染
   → 数据库查询优化
   → 减少 API 调用链

4. 协议优化
   → HTTP/2 多路复用
   → HTTP/3 0-RTT
   → TLS 1.3 会话恢复
```

### 17.12.3 Chrome DevTools Performance 面板

```
Performance 面板核心功能

1. 录制性能轨迹
   → Record（红色圆点）
   → 录制页面加载或交互
   → 停止后查看火焰图

2. 火焰图分析
   → 主线程任务时间线
   → JavaScript 执行时间
   → 布局和绘制时间

3. 关键指标
   → DCL (DOMContentLoaded)
   → L (Load)
   → FP/FCP/LCP 标记
   → 长任务标记（红色三角）

4. 常用分析
   → 查找长任务（>50ms）
   → 查找布局抖动（紫色 Layout 块）
   → 查找强制同步布局（红色警告）
```

> Performance 面板是前端性能调试最强大的工具。关键技巧：先录制，然后在火焰图中找到最宽的块（最耗时的任务），展开查看具体函数。配合 Coverage 面板可以找出未使用的 JavaScript/CSS 代码。Lighthouse 适合快速审计，Performance 面板适合深入调试。

## 17.13 CrUX 数据深入分析

### 17.13.1 CrUX 报告格式

CrUX（Chrome UX Report）是 Google 公开的真实用户体验数据集。它来自数百万 Chrome 用户的匿名遥测数据。

```
CrUX 数据来源

Chrome 用户
  → 遥测 Web Vitals 指标
  → 匿名化处理
  → 按域名聚合
  → 公开报告

数据维度：
  域名 → example.com 的整体性能
  URL  → 特定页面的性能
  设备 → 手机/桌面/平板
  连接 → 4G/WiFi/3G
  月份 → 历史趋势
```

```
CrUX 数据格式示例

{
  "origin": "https://example.com",
  "metrics": {
    "largest_contentful_paint": {
      "histogram": {
        "start": 0,    "end": 2500,   "density": 0.65  // 65% good
        "start": 2500, "end": 4000,   "density": 0.20  // 20% needs improvement
        "start": 4000, "end": "inf",  "density": 0.15  // 15% poor
      },
      "percentiles": { p75: 2100 }
    },
    "interaction_to_next_paint": {
      "percentiles": { p75: 180 }
    },
    "cumulative_layout_shift": {
      "percentiles": { p75: 0.08 }
    }
  }
}
```

| 数据项 | 说明 | 用途 |
|--------|------|------|
| p75 LCP | 75% 用户的 LCP | 竞品对比 |
| histogram | 三档分布 | 评估用户体验 |
| 设备维度 | 手机/桌面 | 定位问题设备 |
| 历史趋势 | 月度变化 | 跟踪优化效果 |

### 17.13.2 CrUX vs RUM 对比

```
CrUX vs 自建 RUM

CrUX 优势:
  → 免费
  → 公开透明
  → 覆盖所有 Chrome 用户
  → 可查竞品数据

CrUX 劣势:
  → 只有 Chrome 用户
  → 只覆盖公开网站
  → 月度更新（不实时）
  → 无法自定义指标

RUM 优势:
  → 实时数据
  → 自定义指标
  → 所有浏览器
  → 页面级粒度

RUM 劣势:
  → 付费
  → 需要集成 SDK
  → 只有自己的数据
```

> 最佳实践：使用 CrUX 做竞品分析和行业基准，使用 RUM 做实时监控和深度分析。CrUX 的 p75 数据是 Google 排名因素之一，因此它不仅是性能指标，还影响 SEO。保持 CrUX 数据良好是 Web 开发的重要 KPI。

## 17.14 Lighthouse 审计深入

### 17.14.1 Lighthouse 评分体系

Lighthouse 6/7/8/9 的评分权重多次调整，反映了性能指标重点的变化。

```
Lighthouse 评分权重演变

Lighthouse 6/7:
  FCP:   15%
  LCP:   25%
  TBT:   30%
  CLS:   15%
  SI:    15%

Lighthouse 8/9/10:
  FCP:   10%
  LCP:   30%
  TBT:   30%
  CLS:   15%
  SI:    15%

趋势：
  LCP 权重增加 → 更关注加载性能
  TBT 权重保持 → 持续关注可交互性
  FCP 权重减少 → LCP 更能代表用户感知
```

| 指标 | 权重 | 变化趋势 | 说明 |
|------|------|---------|------|
| LCP | 30% | ↑ | 最重要加载指标 |
| TBT | 30% | → | 可交互性 |
| CLS | 15% | → | 视觉稳定 |
| SI | 15% | → | 整体速度 |
| FCP | 10% | ↓ | 首次绘制 |

### 17.14.2 Lighthouse 类别

```
Lighthouse 五大审计类别

1. Performance（性能）
   → LCP/INP/CLS/TBT/FCP
   → 资源优化建议

2. Accessibility（无障碍）
   → ARIA 属性检查
   → 颜色对比度
   → 键盘导航

3. Best Practices（最佳实践）
   → HTTPS/HTTP/2
   → 控制台错误
   → 图片优化

4. SEO（搜索引擎优化）
   → meta 标签
   → 可爬取性
   → 移动端友好

5. PWA（渐进式 Web 应用）
   → Service Worker
   → Manifest
   → 离线支持
```

> Lighthouse 不仅是一个性能工具，它是全面的网站质量审计工具。Performance 只是五个类别之一。很多团队只关注 Performance 分数，但 Accessibility 和 SEO 同样重要。一个高质量网站应该在这五个类别都达到 90+ 分。

## 本章核心知识总结

| 指标 | 测量内容 | 目标值 | 核心优化 |
|------|---------|--------|---------|
| LCP | 最大内容绘制 | < 2.5s | Preload + 图片优化 |
| INP | 交互到绘制 | < 200ms | 减少长任务 + yield |
| CLS | 布局偏移 | < 0.1 | 预留空间 + transform |
| TTFB | 首字节 | < 800ms | CDN + 缓存 |
| TBT | 总阻塞 | < 200ms | 代码分割 |

觉得有用？收藏起来，下次做性能优化时按指标逐项排查。

你的网站 Core Web Vitals 达标了吗？哪个指标最难优化？评论区聊聊。

关注怕浪猫，下期我们讲渲染性能优化。系列进度 17/24。

下期预告：第 18 章「渲染性能优化」。我们会拆解渲染管线瓶颈的定位方法、虚拟列表的实现原理、以及如何避免强制同步布局（Forced Reflow）。怕浪猫下期见。

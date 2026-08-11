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

---
sidebar_position: 20
---

# 第20章 加载性能优化

> 用户等待超过 3 秒就会离开。加载性能不只是技术指标，而是用户留存的关键。从代码分割到 Service Worker，每一层缓存都在为下一帧争取时间。

我是怕浪猫，上期讲了内存管理，今天进入第 20 章：加载性能优化。这一章拆解代码分割（Code Splitting）、资源预加载策略、Service Worker 缓存、以及 HTTP 缓存的层次设计。

## 20.1 代码分割（Code Splitting）

### 20.1.1 为什么需要代码分割

现代 Web 应用打包后的 JS 文件动辄数 MB。如果一次性加载所有代码，首屏渲染会被严重拖慢。代码分割将代码按路由或功能拆分，只加载当前需要的代码。

```
无代码分割：
  首屏加载 bundle.js（2MB）→ 解析+执行 500ms → 首屏渲染

有代码分割：
  首屏加载 main.js（200KB）+ home.js（100KB）→ 首屏渲染
  路由切换时按需加载 about.js（50KB）
```

| 策略 | 首屏 JS | 切换路由 | 适用场景 |
|------|---------|---------|---------|
| 无分割 | 2MB | 即时 | 小应用 |
| 路由分割 | 300KB | 需加载 | SPA |
| 组件分割 | 200KB | 需加载 | 大型应用 |
| 动态导入 | 最小 | 按需 | 交互驱动 |

### 20.1.2 动态导入

```javascript
// 静态导入（打包在一起）
import { heavyFunction } from './heavy-module';

// 动态导入（按需加载）
const button = document.querySelector('#action');
button.addEventListener('click', async () => {
  const { heavyFunction } = await import('./heavy-module');
  heavyFunction();
});
```

### 20.1.3 Webpack 代码分割

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    }
  }
};
```

| 分割策略 | 说明 | 效果 |
|---------|------|------|
| 路由级 | 每个路由独立 chunk | 首屏只加载当前路由 |
| 组件级 | 重组件独立 chunk | 按交互加载 |
| vendor 分割 | 第三方库独立 | 利用长缓存 |
| 公共模块 | 多页面共享代码 | 避免重复加载 |

## 20.2 资源预加载

### 20.2.1 预加载策略对比

| 策略 | 指令 | 时机 | 优先级 |
|------|------|------|--------|
| preload | `<link rel="preload">` | 当前页面必然需要 | 高 |
| prefetch | `<link rel="prefetch">` | 下一个页面可能需要 | 低 |
| preconnect | `<link rel="preconnect">` | 提前建立连接 | 中 |
| dns-prefetch | `<link rel="dns-prefetch">` | 提前 DNS 解析 | 低 |
| modulepreload | `<link rel="modulepreload">` | 预加载 ES 模块 | 高 |

```html
<!-- 预加载关键资源 -->
<link rel="preload" as="font" href="/font.woff2" crossorigin>
<link rel="preload" as="image" href="/hero.jpg" fetchpriority="high">
<link rel="preload" as="script" href="/critical.js">

<!-- 预获取下一页资源 -->
<link rel="prefetch" as="script" href="/next-page.js">

<!-- 提前建立连接 -->
<link rel="preconnect" href="https://cdn.example.com">
<link rel="dns-prefetch" href="https://api.example.com">

<!-- 预加载 ES 模块 -->
<link rel="modulepreload" href="/module.js">
```

### 20.2.2 preload vs prefetch

```
preload：
  当前页面一定会用到的资源
  高优先级加载
  必须设置 as 属性
  
  使用场景：
  - LCP 图片
  - 关键字体
  - 关键 CSS/JS

prefetch：
  下一页可能用到的资源
  低优先级（空闲时加载）
  不影响当前页面性能
  
  使用场景：
  - 下一页的 JS/CSS
  - 用户可能点击的链接资源
```

> preload 和 prefetch 的区别在于「确定性和时机」。preload 是「现在就要」，prefetch 是「待会可能要」。错误使用 preload 会浪费带宽，错误使用 prefetch 不会影响当前页面性能。当不确定时，用 prefetch 比 preload 安全。

## 20.3 HTTP 缓存

### 20.3.1 缓存层次

```
浏览器缓存层次

1. Memory Cache（内存缓存）
   速度快、容量小、标签页关闭即失效
   
2. Disk Cache（磁盘缓存）
   速度中、容量大、持久化
   
3. Service Worker Cache
   可编程控制、灵活、持久化
   
4. HTTP Cache（HTTP 缓存）
   由 HTTP 头控制、标准化
```

| 缓存层 | 速度 | 容量 | 持久 | 可控性 |
|--------|------|------|------|--------|
| Memory Cache | 极快 | 小 | 否 | 低 |
| Disk Cache | 中 | 大 | 是 | 中 |
| Service Worker | 中 | 大 | 是 | 高 |
| CDN | 快 | 大 | 是 | 高 |

### 20.3.2 HTTP 缓存策略

```http
# 强缓存（不验证，直接用）
Cache-Control: max-age=31536000, immutable
# 1 年缓存，且不会变化（immutable）

# 协商缓存（验证后决定是否用）
ETag: "abc123"
Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT

# 响应头组合
Cache-Control: public, max-age=31536000, immutable
# public: CDN 可缓存
# max-age: 缓存时间
# immutable: 永远不需要验证
```

| 策略 | 头部 | 行为 | 适用资源 |
|------|------|------|---------|
| 强缓存 | Cache-Control: max-age | 不验证直接用 | 带哈希的资源 |
| 协商缓存 | ETag/Last-Modified | 验证后决定 | HTML 文件 |
| 不缓存 | Cache-Control: no-cache | 每次验证 | 动态 API |
| 完全不缓存 | Cache-Control: no-store | 完全不缓存 | 敏感数据 |

```
带哈希文件名的缓存策略

index.html → Cache-Control: no-cache（每次验证）
app.[hash].js → Cache-Control: max-age=31536000, immutable（1年缓存）
style.[hash].css → Cache-Control: max-age=31536000, immutable
```

> 带内容哈希的文件名是缓存友好的最佳实践。文件内容不变则哈希不变，浏览器可以直接用缓存。内容变化则哈希变化，浏览器请求新文件。HTML 文件不带哈希，用协商缓存确保总是最新的。

## 20.4 Service Worker 缓存

### 20.4.1 Service Worker 缓存策略

```javascript
// Cache First 策略（适合静态资源）
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then(cached => {
      return cached || fetch(e.request).then(response => {
        caches.open('v1').then(cache => cache.put(e.request, response.clone()));
        return response;
      });
    })
  );
});

// Network First 策略（适合动态内容）
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

// Stale While Revalidate（先用缓存，后台更新）
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.open('v1').then(cache => {
      return cache.match(e.request).then(cached => {
        const fetchPromise = fetch(e.request).then(response => {
          cache.put(e.request, response.clone());
          return response;
        });
        return cached || fetchPromise;
      });
    })
  );
});
```

| 策略 | 优先 | 更新 | 适用场景 |
|------|------|------|---------|
| Cache First | 缓存 | 不更新 | 静态资源 |
| Network First | 网络 | 实时 | 动态内容 |
| Stale While Revalidate | 缓存 | 后台更新 | 非关键资源 |
| Cache Only | 缓存 | 不更新 | 离线页面 |
| Network Only | 网络 | — | 不缓存的内容 |

### 20.4.2 Service Worker 生命周期

```
Service Worker 生命周期

安装（Install）：
  → 预缓存关键资源
  → skipWaiting() 跳过等待

激活（Activate）：
  → 清理旧缓存
  → clients.claim() 控制当前页面

运行（Fetch）：
  → 拦截请求，按策略响应

更新（Update）：
  → 检测到新 SW 文件
  → 安装新 SW
  → 旧 SW 控制的页面关闭后激活新 SW
```

## 20.5 图片优化

### 20.5.1 图片格式选择

| 格式 | 压缩 | 透明 | 动画 | 适用场景 |
|------|------|------|------|---------|
| WebP | 有损/无损 | 是 | 是 | 通用替代 |
| AVIF | 有损/无损 | 是 | 是 | 最佳压缩 |
| JPEG | 有损 | 否 | 否 | 照片 |
| PNG | 无损 | 是 | 否 | 图标/截图 |
| SVG | 矢量 | 是 | 是 | 图标/插画 |
| JPEG XL | 有损/无损 | 是 | 是 | 下一代 |

```html
<!-- 使用 picture 提供多种格式 -->
<picture>
  <source srcset="/image.avif" type="image/avif">
  <source srcset="/image.webp" type="image/webp">
  <img src="/image.jpg" alt="Fallback">
</picture>

<!-- 响应式图片 -->
<img srcset="/image-480.jpg 480w,
             /image-800.jpg 800w,
             /image-1200.jpg 1200w"
     sizes="(max-width: 600px) 480px,
            (max-width: 900px) 800px,
            1200px"
     src="/image-800.jpg"
     alt="Responsive image">
```

### 20.5.2 图片懒加载

```html
<!-- 原生懒加载 -->
<img src="/image.jpg" loading="lazy" decoding="async" alt="...">

<!-- 配合 Intersection Observer -->
<img data-src="/image.jpg" class="lazy" alt="...">
<script>
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});
document.querySelectorAll('.lazy').forEach(img => observer.observe(img));
</script>
```

## 20.6 资源加载优先级

浏览器为每个资源分配优先级，开发者可以通过 fetchpriority 调整。

```html
<!-- 高优先级 -->
<img src="/hero.jpg" fetchpriority="high">

<!-- 低优先级 -->
<img src="/below-fold.jpg" fetchpriority="low">

<!-- 脚本优先级 -->
<script src="/critical.js" fetchpriority="high"></script>
<script src="/analytics.js" fetchpriority="low"></script>
```

| 资源类型 | 默认优先级 | 可调整 |
|---------|-----------|--------|
| CSS | Highest | 是 |
| `<img>` in viewport | High | 是 |
| `<script>` without async | High | 是 |
| `<script>` with async | Low | 是 |
| `<img>` below fold | Low | 是 |
| `<link rel="prefetch">` | Lowest | 是 |

## 20.7 Tree Shaking 原理

### 20.7.1 什么是 Tree Shaking

Tree Shaking（摇树优化）是指打包工具分析模块依赖关系，剔除未被使用的代码，只将实际用到的代码打包进最终产物。这个术语最早由 Rich Harris（Rollup 作者）提出，形象的比喻是把树摇晃后枯叶落地，只留下健壮的枝干。

```
Tree Shaking 工作原理

源码：
  math.js
    ├─ export function add(a, b) { return a + b; }     ← 被使用
    ├─ export function sub(a, b) { return a - b; }     ← 未被使用
    └─ export function mul(a, b) { return a * b; }     ← 未被使用

  app.js
    └─ import { add } from './math.js';
        └─ add(1, 2)

打包结果（Tree Shaking 后）：
  bundle.js
    └─ function add(a, b) { return a + b; }
        └─ add(1, 2)

  sub 和 mul 被完全移除
```

### 20.7.2 Tree Shaking 的前提条件

Tree Shaking 依赖 ES Module 的静态结构分析。CommonJS（require/module.exports）是动态的，无法被静态分析。

| 条件 | ES Module | CommonJS |
|------|-----------|----------|
| 静态分析 | 支持 | 不支持 |
| 导入方式 | import（编译时） | require（运行时）|
| 导出方式 | export（编译时） | module.exports（运行时）|
| 条件导出 | 不支持 | 支持 |
| Tree Shaking | 支持 | 不支持 |

```javascript
// ES Module — 可以 Tree Shaking
import { add } from './math.js';  // 只导入 add

// CommonJS — 无法 Tree Shaking
const math = require('./math.js');  // 导入整个模块
math.add(1, 2);

// 动态导入 — 无法 Tree Shaking
import('./math.js').then(math => {
  math.add(1, 2);
});
```

### 20.7.3 sideEffects 字段

package.json 中的 sideEffects 字段告诉打包工具哪些文件有副作用，哪些可以安全地 Tree Shaking。

```json
// package.json
{
  "sideEffects": false
  // 告诉打包工具：所有文件都没有副作用，可以安全删除未使用的导出
}

// 或者指定有副作用的文件
{
  "sideEffects": [
    "./src/polyfills.js",
    "./src/global-styles.css"
  ]
  // 只有这些文件有副作用，其他文件都可以 Tree Shaking
}
```

```javascript
// 有副作用的代码（不能被 Tree Shaking）
// math.js
window.mathVersion = '1.0';  // 副作用：修改全局变量

export function add(a, b) { return a + b; }
export function sub(a, b) { return a - b; }

// 即使只 import { add }，sub 不会被删除
// 因为整个模块有副作用（修改了 window）

// 无副作用的代码（可以被 Tree Shaking）
export function add(a, b) { return a + b; }
export function sub(a, b) { return a - b; }
// 只 import { add } 时，sub 会被安全删除
```

| sideEffects 值 | 含义 | 效果 |
|----------------|------|------|
| false | 无副作用 | 最大程度 Tree Shaking |
| true（默认）| 可能有副作用 | 保守处理，不删除 |
| 文件数组 | 指定文件有副作用 | 指定文件保留，其他可 Tree Shaking |

> 在开发 npm 库时，设置 `"sideEffects": false` 是提升使用者打包体积的有效手段。但要确保库中的文件确实没有副作用——不修改全局变量、不注册全局事件、不执行初始化逻辑。

## 20.8 Critical CSS 提取策略

### 20.8.1 为什么需要 Critical CSS

浏览器渲染页面之前必须解析 HTML 中的所有 CSS（CSSOM 构建）。CSS 是阻塞渲染的资源。如果 CSS 文件很大，首屏渲染会被延迟。Critical CSS 策略是只将首屏可见区域的 CSS 内联到 HTML 中，其余 CSS 异步加载。

```
Critical CSS 策略

传统方式：
  HTML 下载 → 阻塞等待 CSS 下载（200KB）→ 解析 CSS → 渲染
  首屏渲染时间：2.5s

Critical CSS：
  HTML 下载（内联 10KB Critical CSS）→ 解析内联 CSS → 渲染首屏
  首屏渲染时间：0.8s
  同时异步加载完整 CSS（200KB）
```

### 20.8.2 提取与注入流程

```javascript
// 使用 critical 工具自动提取 Critical CSS
// npm install critical --save-dev

const critical = require('critical');

critical.generate({
  base: 'dist/',
  src: 'index.html',
  dest: 'index-critical.html',
  inline: true,
  dimensions: [
    { width: 375, height: 667 },   // iPhone SE
    { width: 1440, height: 900 },  // Desktop
  ],
  penthouse: {
    timeout: 30000,
  }
});

// 输出的 HTML 中 Critical CSS 被内联到 <style> 标签
// 其余 CSS 通过 preload 异步加载
```

```html
<!-- Critical CSS 提取后的 HTML -->
<style>
  /* Critical CSS - 首屏内联样式 */
  body { margin: 0; font-family: sans-serif; }
  .header { height: 60px; background: #333; }
  .hero { height: 400px; background: url(hero.jpg); }
  /* ... 约 10KB ... */
</style>

<!-- 非关键 CSS 异步加载 -->
<link rel="preload" href="/full.css" as="style" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/full.css"></noscript>
```

| 策略 | 首屏 CSS | 总 CSS | 首屏渲染 |
|------|---------|--------|----------|
| 传统加载 | 200KB | 200KB | 慢（阻塞）|
| Critical CSS | 10KB 内联 | 200KB | 快（不阻塞）|
| 全部内联 | 200KB 内联 | 200KB | 快但 HTML 大 |

### 20.8.3 Critical CSS 的维护挑战

Critical CSS 不是一次性的工作。每次样式变更后，Critical CSS 可能需要重新提取。推荐的方案是在构建流程中自动化提取。

```javascript
// Webpack 配置中使用 critters 插件
const Critters = require('critters-webpack-plugin');

module.exports = {
  plugins: [
    new Critters({
      preload: 'swap',       // 预加载非关键 CSS
      pruneSource: true,     // 从原始 CSS 中移除已内联的规则
      additionalStylesheets: ['styles/reset.css'],
    })
  ]
};
```

## 20.9 Resource Hints 实战

### 20.9.1 预加载策略选择决策

Resource Hints 是一组 HTML 链接类型，告诉浏览器提前获取资源或建立连接。选择正确的 hint 类型对性能至关重要。

```
Resource Hints 决策树

当前页面一定会用到这个资源吗？
  ├─ 是 → preload（高优先级）
  │       ├─ 是字体 → 加 crossorigin
  │       ├─ 是图片 → 加 fetchpriority="high"
  │       └─ 是脚本 → 加 as="script"
  └─ 否 → 下一个页面可能用到吗？
          ├─ 是 → prefetch（低优先级，空闲时加载）
          └─ 否 → 不需要 hint

需要连接到第三方域名吗？
  ├─ 是，且需要 TLS → preconnect（提前建立 DNS+TCP+TLS）
  └─ 只需 DNS → dns-prefetch（仅 DNS 解析）

使用 ES Module 吗？
  └─ 是 → modulepreload（预加载模块及其依赖）
```

### 20.9.2 性能数据对比

以下是真实场景下的性能数据对比（基于 Lighthouse 测试）：

| 优化项 | 无优化 | 加 preload | 加 preconnect | 全部优化 |
|--------|--------|------------|---------------|----------|
| FCP | 2.1s | 1.5s | 1.4s | 1.2s |
| LCP | 3.8s | 2.5s | 2.3s | 1.9s |
| TTI | 4.2s | 3.1s | 2.9s | 2.5s |
| 首屏 JS | 800KB | 800KB | 800KB | 800KB |

```html
<!-- 实战配置示例 -->
<head>
  <!-- DNS 预解析：CDN 域名 -->
  <link rel="dns-prefetch" href="https://cdn.example.com">
  
  <!-- 预连接：API 服务器（含 TLS 握手） -->
  <link rel="preconnect" href="https://api.example.com" crossorigin>
  
  <!-- 预加载：LCP 图片 -->
  <link rel="preload" as="image" href="https://cdn.example.com/hero.webp" fetchpriority="high">
  
  <!-- 预加载：关键字体 -->
  <link rel="preload" as="font" href="/fonts/inter.woff2" type="font/woff2" crossorigin>
  
  <!-- 预加载：关键 CSS -->
  <link rel="preload" as="style" href="/critical.css">
  
  <!-- 预获取：下一页资源 -->
  <link rel="prefetch" as="script" href="/next-page.chunk.js">
  
  <!-- 模块预加载 -->
  <link rel="modulepreload" href="/app.js">
</head>
```

### 20.9.3 常见误区

| 误区 | 问题 | 正确做法 |
|------|------|----------|
| preload 太多 | 抢占带宽，延迟关键资源 | 只 preload LCP/首屏资源 |
| prefetch 高优先级 | 影响当前页面性能 | prefetch 用于空闲时 |
| 忘记 crossorigin | 字体 preload 后不命中 | 字体必须加 crossorigin |
| preload 未使用资源 | 浏览器警告 | preload 的资源必须在 3s 内使用 |
| 对所有域名 preconnect | 连接开销 | 只对关键域名 preconnect（最多 3-4 个）|

## 20.10 Service Worker 缓存策略选择决策树

### 20.10.1 决策树

```
Service Worker 缓存策略决策树

请求的资源类型是什么？

├─ 导航请求（HTML）
│   ├─ 需要最新内容？
│   │   ├─ 是 → Network First（网络优先，失败回退缓存）
│   │   └─ 否 → Cache First（离线优先）
│   └─ 离线兜底？
│       └─ 是 → 离线时返回 offline.html
│
├─ 带哈希的静态资源（JS/CSS/字体/图片）
│   └─ Cache First（永不变，缓存优先）
│
├─ 无哈希的静态资源
│   ├─ 内容频繁变化？
│   │   ├─ 是 → Stale While Revalidate（先用缓存，后台更新）
│   │   └─ 否 → Cache First + 定期更新
│
├─ API 请求
│   ├─ GET 请求？
│   │   ├─ 数据实时性要求高 → Network First
│   │   ├─ 数据变化不频繁 → Stale While Revalidate
│   │   └─ 需要离线可用 → Cache First + 后台同步
│   └─ 非 GET 请求 → Network Only（不缓存）
│
└─ 第三方资源
    ├─ 可靠的 CDN → Cache First
    └─ 不可靠 → Network First + 超时回退
```

### 20.10.2 综合缓存策略实现

```javascript
// 一个完整的 Service Worker 缓存策略
const CACHE_VERSION = 'v3';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;

// 缓存策略路由表
const strategies = {
  // 导航请求 → Network First
  navigate: async (request) => {
    try {
      const response = await fetch(request);
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
      return response;
    } catch {
      const cached = await caches.match(request);
      return cached || caches.match('/offline.html');
    }
  },
  
  // 带哈希的静态资源 → Cache First
  staticAsset: async (request) => {
    const cached = await caches.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
    return response;
  },
  
  // API 请求 → Stale While Revalidate
  api: async (request) => {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cached = await cache.match(request);
    const fetchPromise = fetch(request).then(response => {
      cache.put(request, response.clone());
      return response;
    }).catch(() => cached);
    return cached || fetchPromise;
  }
};

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 路由分发
  if (request.mode === 'navigate') {
    event.respondWith(strategies.navigate(request));
  } else if (/\.[a-f0-9]+\.(js|css|woff2?)$/.test(url.pathname)) {
    event.respondWith(strategies.staticAsset(request));
  } else if (url.pathname.startsWith('/api/')) {
    event.respondWith(strategies.api(request));
  }
});
```

## 20.11 图片优化全流程

### 20.11.1 格式选择决策

```
图片格式选择决策树

是矢量图形吗？
  ├─ 是 → SVG（任意缩放，体积小）
  └─ 否 → 是照片吗？
          ├─ 是 → 支持 AVIF？
          │       ├─ 是 → AVIF（最佳压缩比）
          │       └─ 否 → 支持 WebP？
          │               ├─ 是 → WebP
          │               └─ 否 → JPEG
          └─ 否 → 是图标/截图（需要透明）？
                  ├─ 支持 AVIF → AVIF（支持透明）
                  ├─ 支持 WebP → WebP
                  └─ 否 → PNG
```

| 格式 | 压缩率（vs JPEG）| 透明 | 动画 | 浏览器支持 | 适用 |
|------|-------------------|------|------|-----------|------|
| AVIF | 50%+ 更小 | 是 | 是 | 92%+ | 照片/复杂图 |
| WebP | 25-35% 更小 | 是 | 是 | 97%+ | 通用替代 |
| JPEG | 基准 | 否 | 否 | 100% | 兼容降级 |
| PNG | 无损 | 是 | 否 | 100% | 图标/截图 |
| SVG | 矢量 | 是 | 是 | 98%+ | 图标/插画 |

### 20.11.2 LQIP（Low Quality Image Placeholder）

LQIP 是一种渐进式图片加载技术：先加载极低质量的模糊图片占位，再加载高质量原图。

```javascript
// LQIP 实现
function loadWithLQIP(imgElement) {
  const originalSrc = imgElement.dataset.src;
  const lqipSrc = imgElement.dataset.lqip;  // 20x15 像素的模糊缩略图
  
  // 1. 先加载 LQIP
  imgElement.src = lqipSrc;
  imgElement.style.filter = 'blur(20px)';
  imgElement.style.transition = 'filter 0.3s';
  
  // 2. 预加载原图
  const fullImg = new Image();
  fullImg.onload = () => {
    imgElement.src = originalSrc;
    imgElement.style.filter = 'none';
  };
  fullImg.src = originalSrc;
}

// HTML
// <img data-src="/hero.jpg" data-lqip="/hero-lqip.jpg" alt="Hero">
```

### 20.11.3 渐进式加载策略对比

| 策略 | 体验 | 实现复杂度 | 带宽 |
|------|------|-----------|------|
| LQIP | 模糊→清晰 | 中 | 额外小图 |
| 渐进式 JPEG | 逐行清晰 | 低（格式自带）| 无额外 |
| Intersection Observer 懒加载 | 空白→图片 | 低 | 无额外 |
| BlurHash | 颜色模糊→清晰 | 高 | 仅几十字节 |

## 20.12 Brotli vs Gzip 压缩对比

### 20.12.1 压缩算法对比

| 指标 | Gzip | Brotli (level 11) | Brotli (level 4) |
|------|------|-------------------|-------------------|
| 压缩率 | 基准 | 15-25% 更小 | 10-15% 更小 |
| 压缩速度 | 快 | 慢（10x slower）| 快 |
| 解压速度 | 快 | 快 | 快 |
| 字体支持 | 否 | 是（内置字典）| 是 |
| 浏览器支持 | 100% | 97%+ | 97%+ |

```nginx
# Nginx 配置 Brotli + Gzip 回退
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/javascript application/json image/svg+xml;

gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/javascript application/json image/svg+xml;

# 同时配置：浏览器支持 Brotli 时用 Brotli，否则回退 Gzip
```

### 20.12.2 静态资源预压缩

对于静态资源，可以在构建时预压缩，避免运行时压缩的 CPU 开销。

```javascript
// Webpack 预压缩插件
const BrotliPlugin = require('brotli-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
  plugins: [
    new BrotliPlugin({
      asset: '[path].br',
      quality: 11,  // 最高压缩率
    }),
    new CompressionPlugin({
      filename: '[path].gz',
      algorithm: 'gzip',
    }),
  ]
};

// Nginx 配置：直接使用预压缩文件
// brotli_static on;
// gzip_static on;
```

## 20.13 Resource Bundling 策略

### 20.13.1 打包粒度选择

```
打包策略矩阵

┌──────────────────────────────────────────────────┐
│                    打包粒度                       │
├──────────┬──────────┬──────────┬─────────────────┤
│ 单 bundle │ 按路由   │ 按组件   │ 完全 ESM        │
├──────────┼──────────┼──────────┼─────────────────┤
│ 首屏: 差  │ 首屏: 好  │ 首屏: 优  │ 首屏: 最优      │
│ 缓存: 差  │ 缓存: 中  │ 缓存: 优  │ 缓存: 优        │
│ 请求数: 1 │ 请求数: 少│ 请求数: 中│ 请求数: 多      │
│ 适合: 小  │ 适合: 中  │ 适合: 大  │ 适合: HTTP/2+   │
└──────────┴──────────┴──────────┴─────────────────┘
```

| 策略 | 首屏 JS | 缓存利用率 | 请求数 | 适用场景 |
|------|---------|-----------|--------|----------|
| 单 bundle | 大（2MB+）| 低（改动全量）| 1 | 小应用 |
| vendor 分割 | 中 | 高（vendor 独立缓存）| 3-5 | SPA |
| 路由级分割 | 小 | 高 | 5-10 | 多路由应用 |
| 组件级分割 | 最小 | 最高 | 10-50 | 大型应用 |
| 完全 ESM | 最小 | 最高 | 50-200 | HTTP/2/3 环境 |

### 20.13.2 vendor 分割策略

```javascript
// webpack.config.js — 智能分割
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      maxInitialRequests: Infinity,
      minSize: 20000,
      cacheGroups: {
        // React 核心库
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
          name: 'react',
          chunks: 'all',
        },
        // 路由库
        router: {
          test: /[\\/]node_modules[\\/](react-router|history)[\\/]/,
          name: 'router',
          chunks: 'all',
        },
        // UI 库
        ui: {
          test: /[\\/]node_modules[\\/]antd[\\/]/,
          name: 'ui',
          chunks: 'all',
        },
        // 其他 vendor
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all',
          priority: -20,
        },
      },
    },
  },
};
```

> vendor 分割的核心思想是「按更新频率分组」。React 核心库几乎不变，可以长期缓存。UI 库版本更新较频繁。业务代码最频繁。将它们分到不同 chunk，可以最大化缓存命中率。

## 20.14 HTTP/2 Server Push 的兴衰

### 20.14.1 什么是 HTTP/2 Server Push

HTTP/2 Server Push 允许服务器在客户端请求之前主动推送资源。例如，当客户端请求 `index.html` 时，服务器可以同时推送 `style.css` 和 `app.js`，客户端不需要等待解析 HTML 后再发起请求。

这个特性在 HTTP/2 标准化时被寄予厚望，被认为是解决资源发现延迟的方案。但在实际使用中暴露了严重问题，最终被 Chrome 和其他浏览器逐步废弃。

### 20.14.2 为什么被废弃

Server Push 的核心问题在于服务器无法准确知道客户端是否已经拥有某个资源的缓存。如果客户端已经缓存了 `style.css`，服务器推送这个文件就是浪费带宽。而且推送的资源会占用客户端的连接缓冲区，可能延迟其他更重要的请求。

另一个问题是配置复杂性。开发者需要手动维护推送规则，决定哪些资源在什么条件下推送。随着页面动态化程度提高，静态推送规则很难适应所有场景。不恰当的推送规则不仅不能提升性能，反而会拖慢首屏渲染。

```
Server Push 的问题

场景：客户端已缓存 style.css

无 Server Push:
  客户端请求 index.html
  → 解析 HTML
  → 发现需要 style.css
  → 检查缓存，命中
  → 直接使用缓存
  → 渲染

有 Server Push:
  客户端请求 index.html
  → 服务器推送 style.css（浪费带宽）
  → 客户端接收但发现已有缓存（丢弃）
  → 浪费了连接带宽
  → 可能延迟其他关键请求
```

### 20.14.3 替代方案

Server Push 被废弃后，推荐使用 `preload` 和 `103 Early Hints` 作为替代方案。`preload` 让开发者精确控制哪些资源需要预加载，避免 Server Push 的过度推送问题。`103 Early Hints` 是 HTTP 状态码，允许服务器在最终响应前发送提示信息，告诉客户端可以提前获取某些资源。

| 方案 | 机制 | 优势 | 劣势 |
|------|------|------|------|
| Server Push（已废弃）| 服务器主动推送 | 减少发现延迟 | 浪费带宽 |
| preload | 客户端预加载 | 精确控制 | 需手动配置 |
| 103 Early Hints | 服务器提示 | 灵活 | 需服务器支持 |
| Guess.js | 预测式预加载 | 智能需 AI 预测 |

## 20.15 加载性能优化实战体系

### 20.15.1 性能预算

性能预算是指为页面加载设定明确的数据指标上限，比如 JS 不超过 150KB、图片不超过 500KB、总请求数不超过 50 个。一旦设定了预算，就应该在构建流程中强制执行。Webpack Bundle Analyzer 和 Lighthouse CI 可以在持续集成中自动检查预算是否超支。

设定性能预算时需要基于真实用户的设备能力。根据 HTTP Archive 的统计，移动设备的中位数 CPU 性能只有桌面设备的四分之一。一个在桌面浏览器上秒开的页面，在低端手机上可能需要五秒以上。因此性能预算应该以低端设备的体验为基准，而不是开发者的 MacBook Pro。

一个合理的性能预算包括以下维度：首屏 JavaScript 不超过 170KB（gzip 后），这是 V8 在 4G 网络下约四秒内能解析执行的极限。首屏 CSS 不超过 14KB（TCP 初始窗口大小），确保首轮请求就能获取。首屏图片总大小不超过 500KB，使用现代格式压缩。总请求数不超过 50 个，避免连接建立开销。

### 20.15.2 关键渲染路径优化

关键渲染路径是浏览器将 HTML 转换为像素的完整流程。优化关键渲染路径的核心是减少阻塞渲染的资源。CSS 默认是阻塞渲染的，但可以通过媒体查询将非首屏 CSS 标记为非阻塞。JavaScript 默认是阻塞解析的，但可以通过 `defer` 和 `async` 属性改变其加载行为。

`defer` 属性让脚本在 HTML 解析完成后、`DOMContentLoaded` 之前执行，且多个 `defer` 脚本按顺序执行。这是大多数脚本的首选方式。`async` 属性让脚本在下载完成后立即执行，不保证执行顺序，适合独立的第三方脚本如统计代码。

对于首屏关键脚本，建议内联到 HTML 中而不是外部引用。这样可以省去一个 HTTP 请求的往返延迟。但内联的代码不能被缓存，每次 HTML 请求都要重新下载。因此只内联首屏必须的最小代码量，通常不超过 5KB。

### 20.15.3 懒加载与交互时机的平衡

懒加载是减少首屏加载量的有效手段，但懒加载的时机需要仔细设计。如果懒加载太晚，用户在交互时可能需要等待资源加载。如果懒加载太早，又失去了懒加载的意义。

一个好的策略是在用户产生交互意图时预加载相关资源。比如当鼠标悬停在某个链接上时，预加载该链接对应的代码。这种技术被称为「 predictive prefetch 」，可以在不增加首屏负担的前提下提前加载用户可能需要的代码。Chrome 的 `speculationrules` API 进一步简化了这种预加载策略的实现。

对于图片懒加载，`Intersection Observer` 是最可靠的方案。设置 `rootMargin` 为 `200px` 可以在图片进入视口前两百像素时就开始加载，给用户一种瞬时加载的体验。同时配合 `decoding="async"` 让图片解码不阻塞主线程。

### 20.15.4 构建优化自动化

加载性能优化不应该是上线前的手动检查，而应该内建在构建流程中。Webpack 和 Vite 都提供了丰富的优化插件。关键是在开发环境和生产环境使用一致的构建配置，避免「在我电脑上很快」的问题。

自动化的性能检查应该包括以下环节：每次提交时运行 Lighthouse CI 检查性能指标，在合并请求时检查包大小变化，在部署前运行真实设备的性能测试。这些检查应该有明确的阈值，达不到标准的合并请求应该被自动拒绝。

### 20.15.5 缓存层次设计与最佳实践

Web 应用的缓存不是单一机制，而是由多个层次组成的缓存体系。从浏览器内置的 HTTP 缓存到开发者可控的 Service Worker 缓存，每一层都有不同的特性和适用场景。理解缓存层次的设计原理，才能在不同场景下做出正确的缓存策略选择。

HTTP 缓存是最基础的缓存层，由浏览器自动管理。强缓存通过 `Cache-Control: max-age` 控制，在有效期内直接使用缓存不发请求。协商缓存通过 `ETag` 和 `Last-Modified` 控制，发请求验证资源是否变化。对于带内容哈希的静态资源，使用强缓存加 `immutable` 标记是最优策略，一年内不需要任何验证请求。对于 HTML 文档，使用协商缓存确保用户总是获取最新版本。

Service Worker 缓存是开发者完全可控的缓存层。与 HTTP 缓存不同，Service Worker 可以编程决定缓存什么、何时使用缓存、何时更新缓存。这种灵活性使得 Service Worker 可以实现复杂的缓存策略，比如基于网络状态的动态选择、基于资源类型的分类处理。但灵活性也带来了复杂性，错误的缓存策略可能导致用户看到过期内容。

CDN 缓存是边缘缓存层，将资源缓存在离用户最近的节点。CDN 缓存的配置需要与源站的缓存头配合。通常源站为 CDN 设置较长的缓存时间，CDN 再根据用户请求的缓存头决定是否回源。使用 CDN 时需要注意缓存失效的问题：当源站更新资源时，需要主动通知 CDN 刷新缓存。

### 20.15.6 第三方脚本治理

第三方脚本是加载性能的隐形杀手。统计代码、广告脚本、社交媒体插件等第三方脚本看似无害，但它们的加载和执行会显著拖慢页面。一个典型的电商页面可能加载十几个第三方脚本，总大小超过五百千字节。

治理第三方脚本的第一步是盘点所有外部脚本。使用 Network 面板筛选第三方域名的请求，统计总大小和加载时间。第二步是评估每个脚本的必要性：是否真的需要这个分析工具？能否用更轻量的替代方案？是否可以延迟加载？第三步是优化加载方式：统计脚本使用 `async` 或 `defer`，广告脚本在用户交互后加载，社交媒体插件改为按需加载。

第三方脚本的另一个问题是安全风险。每个第三方脚本都可以访问页面的 DOM 和 JavaScript 上下文。恶意的第三方脚本可以窃取用户数据或注入广告。使用 Content Security Policy（CSP，内容安全策略）可以限制第三方脚本的来源，使用 Subresource Integrity（SRI，子资源完整性）可以确保脚本内容不被篡改。

### 20.15.7 首屏渲染优化全链路分析

首屏渲染是用户对页面性能的第一印象。从用户输入 URL 到首屏内容完整展示，经历了多个阶段，每个阶段都有优化空间。理解这个完整链路是系统性优化的前提。

第一阶段是网络层。用户输入 URL 后，浏览器需要解析 DNS、建立 TCP 连接、完成 TLS 握手、发送 HTTP 请求、等待服务器响应。这个阶段的优化手段包括使用 DNS 预解析减少 DNS 查询时间，使用 HTTP/2 或 HTTP/3 减少连接建立开销，使用 CDN 缩短网络延迟，以及配置正确的缓存策略减少不必要的网络请求。

第二阶段是解析层。浏览器收到 HTML 后开始解析，构建 DOM 树。遇到 CSS 文件时阻塞解析以构建 CSSOM 树。遇到 JavaScript 时阻塞解析以执行脚本。这个阶段的优化重点是减少阻塞资源。CSS 使用媒体查询拆分非首屏样式。JavaScript 使用 `defer` 或 `async` 属性延迟执行。首屏关键样式内联到 HTML 中，避免额外的网络请求。

第三阶段是执行层。JavaScript 执行和 CSS 计算完成后，浏览器开始布局和绘制。布局阶段计算每个元素的几何位置。绘制阶段将布局结果转换为像素。这个阶段的优化包括避免强制同步布局、减少绘制区域、使用合成层加速动画。将动画属性从 `width` 和 `top` 改为 `transform` 和 `opacity`，可以让浏览器跳过布局和绘制阶段，直接在合成器线程处理。

第四阶段是合成层。合成器将各个合成层的内容合并为最终画面。这个阶段在 GPU 上执行，通常很快。但如果合成层数量过多，会消耗大量 GPU 内存。每层合成都会增加 GPU 的绘制调用次数。合理使用 `will-change` 提示浏览器创建合成层，但不要滥用，每个 `will-change` 都会消耗额外内存。

### 20.15.8 性能指标采集与监控体系

性能优化不能凭感觉，需要建立完整的指标采集和监控体系。Core Web Vitals 提供了三个关键指标：LCP（Largest Contentful Paint，最大内容绘制）衡量加载性能，INP（Interaction to Next Paint，交互到下一次绘制）衡量交互响应性，CLS（Cumulative Layout Shift，累积布局偏移）衡量视觉稳定性。

这些指标可以通过 `web-vitals` JavaScript 库在真实用户环境中采集。采集到的数据应该上报到监控系统，按设备类型、网络条件、地理位置等维度分析。百分位数分析比平均值更有意义，因为性能数据的分布通常是长尾的。关注 P75 而不是平均值，因为 Google 使用 P75 作为搜索排名的参考指标。

性能监控应该是持续的而非一次性的。每次发布新版本后对比性能指标变化，发现回归立即排查。性能监控还应该与业务指标关联，比如页面加载时间与跳出率的关系、交互延迟与转化率的关系。这种关联分析可以帮助团队量化性能优化的业务价值，获得更多的优化投入。

### 20.15.9 Service Worker 缓存更新策略

Service Worker 的缓存管理是 PWA 性能优化的核心。一个常见的困境是：缓存优先策略加载快但用户可能看到旧内容，网络优先策略内容新但加载慢。正确的方案不是选择其一，而是根据资源类型动态选择策略。

对于带哈希的静态资源，缓存优先是最优策略。因为哈希保证了文件内容不变，缓存永远不会过期。对于 HTML 文档，使用网络优先配合超时回退。先尝试网络请求获取最新 HTML，如果网络超时（比如三秒），则回退到缓存版本。这种策略保证了在线时内容最新，离线时有内容可用。

Stale While Revalidate 策略适合非关键 API 数据。先返回缓存数据让用户立即看到内容，同时在后台发起网络请求更新缓存。用户感知到的延迟极低，同时数据会在下次访问时更新。这种策略的代价是用户可能看到稍旧的数据，对于实时性要求不高的场景是值得的取舍。

### 20.15.10 字体加载优化

自定义字体是加载性能的双刃剑。好看的字体提升视觉体验，但字体文件的加载和渲染可能严重影响首屏指标。字体加载策略需要平衡视觉效果和性能指标。

字体闪现（FOUT，Flash of Unstyled Text）是指字体加载完成后文字突然从系统字体变为自定义字体的现象。字体隐藏（FOIT，Flash of Invisible Text）是指字体加载期间文字不可见的现象。Chrome 默认使用 FOIT 策略，字体加载超时后回退到系统字体。这可能导致首屏文字延迟显示，影响 LCP 指标。

使用 `font-display: swap` 可以让浏览器在字体加载期间先显示系统字体，加载完成后切换。这消除了文字不可见的时间，对 LCP 有利。但代价是字体切换时的视觉跳动。对于正文文字，`swap` 是最佳选择。对于标题和装饰性文字，可以考虑 `optional`，让浏览器根据网络条件决定是否加载字体。

## 本章核心知识总结

| 优化领域 | 核心策略 | 效果 |
|---------|---------|------|
| 代码分割 | 路由级+组件级 | 减少首屏 JS |
| 资源预加载 | preload+prefetch | 加速关键资源 |
| HTTP 缓存 | 哈希文件名+immutable | 长缓存 |
| Service Worker | Cache First+SWR | 离线+快速 |
| 图片优化 | AVIF+懒加载+响应式 | 减少图片体积 |
| 优先级 | fetchpriority | 优化加载顺序 |

觉得有用？收藏起来，下次做加载性能优化时逐项排查。

你的网站首屏加载要多久？用了哪些优化手段？评论区聊聊。

关注怕浪猫，下期我们讲 Chrome 扩展开发（MV3）。系列进度 20/24。

下期预告：第 21 章「Chrome 扩展开发（MV3）」。我们会拆解 Manifest V3 的架构变化、Service Worker 在扩展中的生命周期、以及 Content Script 与页面通信机制。怕浪猫下期见。

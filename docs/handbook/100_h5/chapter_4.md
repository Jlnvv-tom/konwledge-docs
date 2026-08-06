# 第4章：H5 性能优化核心

H5性能优化不是玄学，是工程。11个核心手段，让LCP从4秒降到1.5秒。我是怕浪猫，一个把Lighthouse跑到全绿的前端工程师。这篇是整个系列最硬核的一篇，建议边喝咖啡边看。

## 4.1 性能指标体系：Core Web Vitals 详解与度量

### 三大核心指标

Google 定义了三个核心 Web 指标（Core Web Vitals），直接影响搜索排名和用户体验：

| 指标 | 全称 | 含义 | 达标值 | 测量方式 |
|------|------|------|--------|----------|
| LCP | Largest Contentful Paint | 最大内容绘制时间 | <= 2.5s | PerformanceObserver |
| INP | Interaction to Next Paint | 下次绘制交互延迟 | <= 200ms | PerformanceObserver |
| CLS | Cumulative Layout Shift | 累计布局偏移 | <= 0.1 | PerformanceObserver |

LCP 衡量加载性能，INP 衡量交互响应性，CLS 衡量视觉稳定性。三个指标达标，用户体验基本合格。

### 度量工具

| 工具 | 用途 | 环境 |
|------|------|------|
| Lighthouse | 综合审计（性能/可访问性/SEO） | DevTools |
| PageSpeed Insights | 线上真实用户数据 + 实验室数据 | Web |
| Chrome DevTools Performance | 火焰图、逐帧分析 | DevTools |
| web-vitals 库 | 代码采集真实用户指标 | 生产环境 |

### web-vitals 库采集

```javascript
import { onLCP, onINP, onCLS, onFCP, onTTFB } from 'web-vitals';

function sendMetric(metric) {
  navigator.sendBeacon('/api/metrics', JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating, // 'good' | 'needs-improvement' | 'poor'
    page: location.pathname,
    timestamp: Date.now()
  }));
}

onLCP(sendMetric);
onINP(sendMetric);
onCLS(sendMetric);
onFCP(sendMetric);
onTTFB(sendMetric);
```

> 性能优化不是一次性的工作，而是一个持续度量、分析、优化的闭环。

参考来源：[web.dev - Core Web Vitals](https://web.dev/articles/vitals)、[web-vitals npm](https://www.npmjs.com/package/web-vitals)

## 4.2 首屏加载优化的完整策略

### 优化层次

首屏优化从四个层面入手：

```
资源层：压缩、Tree Shaking、Code Splitting、HTTP/2
加载层：preload / prefetch / lazy-load
渲染层：SSR / SSG、骨架屏、关键CSS内联
网络层：CDN、Brotli压缩、DNS Prefetch
```

### 资源层优化

```javascript
// Code Splitting：路由级拆分
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));

// 组件级拆分
const HeavyChart = lazy(() => import('./components/HeavyChart'));

// 使用
<Suspense fallback={<Skeleton />}>
  <Home />
</Suspense>
```

### 加载层优化

```html
<!-- preload：高优先级加载当前页必需资源 -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/js/app.js" as="script">

<!-- prefetch：低优先级预取下一页资源 -->
<link rel="prefetch" href="/js/about.js" as="script">

<!-- dns-prefetch + preconnect：提前建立连接 -->
<link rel="dns-prefetch" href="//cdn.example.com">
<link rel="preconnect" href="//cdn.example.com" crossorigin>
```

### 渲染层优化

```html
<!-- 关键CSS内联：首屏样式直接写在HTML中 -->
<style>
  body{margin:0;font-family:sans-serif}
  .hero{height:50vh;background:#f5f5f5;display:flex;align-items:center;justify-content:center}
</style>
<!-- 非关键CSS异步加载 -->
<link rel="preload" href="/css/full.css" as="style" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/css/full.css"></noscript>
```

### 网络层优化

```nginx
# Brotli 压缩（比 Gzip 压缩率高 15-20%）
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/javascript application/json;

# 静态资源 CDN 缓存
location ~* \.(js|css|woff2|png|jpg|avif)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}
```

> 首屏优化的核心思路：减少体积、提前加载、尽快渲染。

参考来源：[web.dev - Optimize LCP](https://web.dev/articles/optimize-lcp)

## 4.3 长列表渲染性能优化

### 虚拟列表原理

万级数据渲染时，DOM 节点过多会导致性能问题。虚拟列表（Virtual List）只渲染可视区域内的 DOM：

```
┌──────────────┐
│  不可见区域   │  <- 不渲染DOM
├──────────────┤
│  上缓冲区     │  <- 渲染（防止滚动白屏）
├──────────────┤
│  可视区域     │  <- 渲染
├──────────────┤
│  下缓冲区     │  <- 渲染
├──────────────┤
│  不可见区域   │  <- 不渲染DOM
└──────────────┘
```

### 核心算法实现

```javascript
class VirtualList {
  constructor(container, items, itemHeight, visibleCount) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = visibleCount;
    this.bufferCount = Math.ceil(visibleCount / 2); // 缓冲区
    this.startIndex = 0;
    this.endIndex = visibleCount + this.bufferCount * 2;

    this.init();
  }

  init() {
    // 滚动容器
    this.scrollEl = document.createElement('div');
    this.scrollEl.style.height = '100%';
    this.scrollEl.style.overflow = 'auto';

    // 内容占位（撑开总高度）
    this.placeholderEl = document.createElement('div');
    this.placeholderEl.style.height = (this.items.length * this.itemHeight) + 'px';

    // 渲染层
    this.contentEl = document.createElement('div');
    this.contentEl.style.position = 'relative';

    this.placeholderEl.appendChild(this.contentEl);
    this.scrollEl.appendChild(this.placeholderEl);
    this.container.appendChild(this.scrollEl);

    this.scrollEl.addEventListener('scroll', () => this.onScroll());
    this.render();
  }

  onScroll() {
    const scrollTop = this.scrollEl.scrollTop;
    const newIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.bufferCount);
    if (newIndex !== this.startIndex) {
      this.startIndex = newIndex;
      this.endIndex = Math.min(
        this.items.length,
        this.startIndex + this.visibleCount + this.bufferCount * 2
      );
      this.render();
    }
  }

  render() {
    // 偏移使内容对齐滚动位置
    this.contentEl.style.transform = `translateY(${this.startIndex * this.itemHeight}px)`;
    this.contentEl.innerHTML = this.items
      .slice(this.startIndex, this.endIndex)
      .map(item => `<div style="height:${this.itemHeight}px">${item.text}</div>`)
      .join('');
  }
}
```

### content-visibility CSS 新特性

```css
/* 浏览器自动跳过不可见区域的渲染 */
.long-list-item {
  content-visibility: auto;
  contain-intrinsic-size: 60px; /* 预估高度，防止滚动条跳动 */
}
```

> 虚拟列表的本质是"只渲染看得到的"，用空间换时间变成了用计算换DOM。

参考来源：[web.dev - Virtualize long lists](https://web.dev/articles/virtualize-long-lists-react)、[MDN - content-visibility](https://developer.mozilla.org/zh-CN/docs/Web/CSS/content-visibility)

## 4.4 JavaScript 包体积优化手段

### Tree Shaking

Tree Shaking 基于 ESM（ECMAScript Module）静态分析，消除未使用的代码：

```javascript
// 正确：命名导入，Tree Shaking 有效
import { debounce } from 'lodash-es';

// 错误：整体导入，Tree Shaking 无效
import _ from 'lodash';
_.debounce(fn, 300);
```

### Code Splitting

```javascript
// webpack.config.js - 分包策略
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

### 按需加载第三方库

```javascript
// 用 dayjs 替代 moment（280KB -> 7KB）
import dayjs from 'dayjs';
// import moment from 'moment'; // 体积大、不支持Tree Shaking

// 用 lodash-es 替代 lodash
import { debounce } from 'lodash-es'; // 按需引入
```

### 分析工具

```bash
# webpack-bundle-analyzer
npx webpack-bundle-analyzer dist/stats.json

# source-map-explorer
npx source-map-explorer dist/app.*.js
```

> 包体积每减少 100KB，首屏加载快 100-200ms，在弱网环境下更明显。

参考来源：[webpack - Tree Shaking](https://webpack.js.org/guides/tree-shaking/)、[Bundlephobia](https://bundlephobia.com/)

## 4.5 图片优化全策略

### 格式选择

| 格式 | 全称 | 压缩率 | 适用场景 |
|------|------|--------|----------|
| AVIF | AV1 Image File Format | 最高 | 照片、复杂图像 |
| WebP | WebP | 高 | 照片、透明图 |
| SVG | Scalable Vector Graphics | 无损矢量 | 图标、简单图形 |
| JPEG | Joint Photographic Experts Group | 中 | 老项目兼容 |
| PNG | Portable Network Graphics | 低 | 需要透明通道 |

### 加载策略

```html
<!-- LQIP（Low Quality Image Placeholder）：低质量占位图 -->
<img
  src="data:image/jpeg;base64,/9j/4AAQ..." 
  data-src="photo-high-quality.jpg"
  class="lazy-load"
>

<!-- BlurHash：颜色占位 -->
<div style="background:#f0a0a0;filter:blur(20px)">
  <img src="photo.jpg" loading="lazy" onload="this.parentElement.style.background='none'">
</div>
```

### CDN 图片处理

```javascript
// CDN 动态裁剪和格式转换
// 根据设备 DPR 和屏幕宽度请求合适尺寸
function getCdnImageUrl(baseUrl, width, dpr) {
  const format = supportsAvif() ? 'avif' : supportsWebp() ? 'webp' : 'jpg';
  return `${baseUrl}?w=${width}&dpr=${dpr}&format=${format}`;
}

// 使用
const img = getCdnImageUrl('https://cdn.example.com/photo', 800, window.devicePixelRatio);
```

> 图片通常占页面体积 60% 以上，图片优化是性价比最高的性能优化手段。

参考来源：[web.dev - Optimize images](https://web.dev/articles/optimize-images)

## 4.6 动画性能优化：60fps 流畅动画的实现

### 动画属性选择

```css
/* 避免：top/left 触发回流 */
.bad {
  transition: top 0.3s, left 0.3s;
}
.bad:hover { top: 10px; left: 10px; }

/* 推荐：transform/opacity 仅触发合成 */
.good {
  transition: transform 0.3s, opacity 0.3s;
  will-change: transform;
}
.good:hover { transform: translate(10px, 10px); }
```

### CSS 动画 vs JS 动画

```javascript
// JS 动画使用 requestAnimationFrame
function animate(element, duration) {
  const start = performance.now();
  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    // 只操作 transform 和 opacity
    element.style.transform = `translateX(${progress * 300}px)`;
    if (progress < 1) {
      requestAnimationFrame(frame);
    }
  }
  requestAnimationFrame(frame);
}

// 避免：setInterval 做动画
// setInterval(() => { element.style.left = x++ + 'px'; }, 16);
// 问题：不与屏幕刷新同步、可能丢帧、后台标签页仍执行
```

### 性能对比

| 方案 | 运行线程 | 是否阻塞主线程 | 是否触发回流 |
|------|----------|---------------|-------------|
| CSS transform 动画 | 合成线程 | 否 | 否 |
| CSS top/left 动画 | 主线程 | 是 | 是 |
| JS requestAnimationFrame | 主线程 | 是 | 取决于属性 |
| Web Animations API | 合成线程 | 否 | 否 |

> 60fps 意味着每帧只有 16.6ms，任何触发回流的动画都可能掉帧。

参考来源：[web.dev - Animations and Performance](https://web.dev/articles/animations-overview)

## 4.7 内存泄漏的排查与预防

### 常见泄漏模式

```javascript
// 泄漏1：未清除的定时器
function startPolling() {
  const timer = setInterval(() => {
    fetch('/api/status').then(data => {
      this.updateView(data); // 组件销毁后仍执行
    });
  }, 5000);
  // 修复：组件销毁时 clearInterval(timer)
}

// 泄漏2：事件监听未移除
function initMap() {
  const handler = (e) => { /* 操作大对象 */ };
  window.addEventListener('resize', handler);
  // 修复：组件销毁时 removeEventListener('resize', handler)
}

// 泄漏3：闭包持有大对象
function createCache() {
  const hugeData = new Array(1000000).fill('data');
  return {
    get: () => hugeData[0] // 闭包持有整个 hugeData
  };
  // 修复：只保存需要的数据
}

// 泄漏4：脱离DOM树的引用
function removeNode() {
  const node = document.querySelector('#target');
  document.body.removeChild(node);
  // node 变量仍引用该DOM节点，无法GC
  // 修复：node = null
}
```

### Chrome DevTools 排查

1. 打开 DevTools -> Memory 面板
2. Take heap snapshot（拍快照）
3. 操作页面（如路由切换）
4. 再拍一次快照
5. Compare 两个快照，找 Delta（增量）不为 0 的对象

### WeakRef 使用

```javascript
// WeakRef 允许垃圾回收器回收引用对象
let cache;

function getCachedData() {
  if (cache && cache.deref()) {
    return cache.deref();
  }
  const data = expensiveCompute();
  cache = new WeakRef(data);
  return data;
}
// 如果没有其他强引用指向 data，GC 可以回收它
```

> 内存泄漏不会报错，但会让页面越用越卡，直到浏览器崩溃。

参考来源：[Chrome Developers - Memory Inspection](https://developer.chrome.com/docs/devtools/memory-inspector/)、[MDN - WeakRef](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/WeakRef)

## 4.8 首屏白屏时间长的排查思路

### 排查链路

```
白屏 -> 检查 TTFB（Time To First Byte）
  |
  ├── TTFB慢 -> 后端慢/DNS问题 -> 优化接口/CDN/dns-prefetch
  |
  └── TTFB正常 -> 检查JS执行时间
       |
       ├── JS执行慢 -> 大bundle/同步阻塞 -> Code Splitting/SSR
       |
       └── JS正常 -> 检查渲染阻塞
            |
            ├── CSS阻塞 -> 内联关键CSS
            |
            └── DOM构建慢 -> 减少嵌套/defer脚本
```

### Performance Observer 采集

```javascript
// 采集白屏相关指标
const observer = new PerformanceObserver((list) => {
  list.getEntries().forEach(entry => {
    console.log(entry.name, entry.startTime + entry.duration);
  });
});
observer.observe({ entryTypes: ['navigation', 'paint'] });

// 获取 FCP（First Contentful Paint）
new PerformanceObserver((list) => {
  const fcp = list.getEntriesByName('first-contentful-paint')[0];
  console.log('FCP:', fcp.startTime, 'ms');
}).observe({ type: 'paint', buffered: true });

// 获取 TTFB
const navEntry = performance.getEntriesByType('navigation')[0];
console.log('TTFB:', navEntry.responseStart - navEntry.requestStart, 'ms');
```

> 白屏排查的核心是"分段计时"，找到瓶颈在哪一段。

参考来源：[MDN - PerformanceObserver](https://developer.mozilla.org/zh-CN/docs/Web/API/PerformanceObserver)、[web.dev - TTFB](https://web.dev/articles/ttfb)

## 4.9 HTTP/2 与 HTTP/3 对前端性能的影响

### 特性对比

| 特性 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|------|----------|--------|--------|
| 多路复用 | 不支持 | 支持 | 支持 |
| 队头阻塞 | 有（TCP级） | 有（TCP级） | 无（QUIC级） |
| 头部压缩 | 不支持 | HPACK | QPACK |
| Server Push | 不支持 | 支持 | 支持 |
| 传输层 | TCP | TCP | QUIC（Quick UDP Internet Connections） |
| 连接建立 | 3次握手 | 3次握手+TLS | 0-RTT/1-RTT |

### 前端策略变化

HTTP/2 多路复用后，不再需要以下旧优化手段：

- 雪碧图（Sprite）：多路复用下单张图片请求更快
- 域名分片（Domain Sharding）：多连接反而增加 TLS 握手开销
- 内联资源（Inlining）：外部文件可被缓存，内联反而增大 HTML 体积

HTTP/2 Server Push（服务端推送）可以主动推送关键资源：

```nginx
# Nginx HTTP/2 Server Push
location = /index.html {
  http2_push /css/critical.css;
  http2_push /js/app.js;
}
```

> HTTP/2 让前端从"减少请求数"的优化思路转向"减少体积和优化加载顺序"。

参考来源：[MDN - HTTP/2](https://developer.mozilla.org/zh-CN/docs/Glossary/HTTP_2)、[web.dev - HTTP/3](https://web.dev/articles/http3)

## 4.10 预加载策略：preload / prefetch / preconnect / dns-prefetch

### 策略对比

| 标签 | 作用 | 优先级 | 使用场景 |
|------|------|--------|----------|
| `preload` | 预加载当前页必需资源 | 高 | 首屏字体/CSS/JS |
| `prefetch` | 预取下一页可能用到的资源 | 低 | 路由预取 |
| `preconnect` | 提前建立TCP/TLS连接 | 中 | 第三方域名 |
| `dns-prefetch` | 仅DNS预解析 | 最低 | 第三方域名 |
| `modulepreload` | 预加载ES模块及依赖 | 高 | 动态import模块 |

### 决策流程

```
当前页必需资源？-> preload
下一页可能用到的？-> prefetch
第三方域名连接慢？-> preconnect
只需DNS解析？-> dns-prefetch
ES模块动态加载？-> modulepreload
```

### 核心代码

```html
<!-- preload：高优先级加载首屏字体 -->
<link rel="preload" href="/fonts/icon.woff2" as="font" type="font/woff2" crossorigin>

<!-- prefetch：用户可能跳转到的下一页 -->
<link rel="prefetch" href="/js/dashboard.js" as="script">

<!-- preconnect：提前连接API服务器 -->
<link rel="preconnect" href="https://api.example.com" crossorigin>

<!-- dns-prefetch：仅DNS解析 -->
<link rel="dns-prefetch" href="//cdn.example.com">

<!-- modulepreload：预加载ES模块 -->
<link rel="modulepreload" href="/js/app.mjs">
```

> 预加载的本质是"用带宽换时间"——提前加载用户一定会用到的资源。

参考来源：[MDN - Preload](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Attributes/rel/preload)、[web.dev - Preconnect and dns-prefetch](https://web.dev/articles/preconnect-and-dns-prefetch)

## 4.11 Web Worker 的使用场景与限制

### 适用场景

Web Worker 适合计算密集型任务：大数据处理、加密计算、图像处理、复杂排序。

```javascript
// 主线程
const worker = new Worker('compute.js');

worker.postMessage({ action: 'sort', data: largeArray });
worker.onmessage = (e) => {
  console.log('排序完成:', e.data);
};

// compute.js（Worker线程）
self.onmessage = (e) => {
  const { action, data } = e.data;
  if (action === 'sort') {
    const result = data.sort((a, b) => a - b); // 大量计算
    self.postMessage(result);
  }
};
```

### 限制

- 不能操作 DOM（Document Object Model）
- 同源限制（Worker 脚本必须同源）
- 通信有序列化开销（postMessage 会复制数据）

### SharedArrayBuffer 零拷贝

```javascript
// 需要服务器配置 COOP/COEP 安全头
// Cross-Origin-Opener-Policy: same-origin
// Cross-Origin-Embedder-Policy: require-corp

const buffer = new SharedArrayBuffer(1024);
const view = new Int32Array(buffer);

// 主线程写入
view[0] = 42;

// Worker 直接读取（零拷贝）
const worker = new Worker('worker.js');
worker.postMessage({ buffer });
```

### OffscreenCanvas

```javascript
// 将Canvas渲染移入Worker，不阻塞主线程
const canvas = document.querySelector('canvas');
const offscreen = canvas.transferControlToOffscreen();
const worker = new Worker('render.js');
worker.postMessage({ canvas: offscreen }, [offscreen]);

// render.js（Worker线程）
self.onmessage = (e) => {
  const ctx = e.data.canvas.getContext('2d');
  ctx.fillStyle = 'green';
  ctx.fillRect(10, 10, 100, 100);
};
```

> Web Worker 不是万能的，通信开销可能抵消计算收益——数据量小的时候别用。

参考来源：[MDN - Web Workers API](https://developer.mozilla.org/zh-CN/docs/Web/API/Web_Workers_API)、[MDN - OffscreenCanvas](https://developer.mozilla.org/zh-CN/docs/Web/API/OffscreenCanvas)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| Core Web Vitals | 性能指标体系 | 高 |
| 首屏加载优化 | LCP/FCP优化 | 高 |
| 虚拟列表 | 大数据渲染优化 | 中高 |
| JS包体积优化 | 打包优化 | 高 |
| 图片优化 | 图片性能全策略 | 中高 |
| 60fps动画 | 动画性能 | 中高 |
| 内存泄漏排查 | 内存管理 | 中 |
| 白屏排查 | 问题定位能力 | 中高 |
| HTTP/2与HTTP/3 | 网络协议理解 | 中 |
| 预加载策略 | 资源加载优化 | 中 |
| Web Worker | 多线程编程 | 中 |

这篇性能优化清单，收藏起来每次发版前过一遍。你的项目LCP多少秒？评论区比比看。关注怕浪猫，下期讲WebView与App集成。系列进度 4/10。

下一篇拆解 JS Bridge 原理、离线包方案、WebView 性能优化、Hybrid 架构设计，Hybrid 开发一篇通关。

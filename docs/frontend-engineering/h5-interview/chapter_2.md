---
sidebar_position: 2
---

# 第2章：浏览器渲染原理与兼容性

从输入URL到页面呈现，浏览器至少经历了8个阶段，90%的人只关注其中2个。我是怕浪猫，一个把浏览器原理翻了个底朝天的前端工程师。上一篇讲了H5基础，这篇往底层走，拆解浏览器渲染管线、回流重绘、缓存机制、跨域、垃圾回收这些面试高频考点。

## 2.1 从输入 URL 到页面渲染完成的完整链路

### 全链路概览

浏览器从输入 URL 到页面渲染完成，经历以下阶段：

```
1. DNS解析（Domain Name System）：域名 -> IP
2. TCP/TLS握手（Transmission Control Protocol / Transport Layer Security）
3. HTTP请求/响应
4. HTML解析 -> 构建 DOM（Document Object Model）
5. CSS解析 -> 构建 CSSOM（CSS Object Model）
6. 合并 -> Render Tree（渲染树）
7. Layout（布局/回流）：计算几何位置
8. Paint（绘制/重绘）：填充像素
9. Composite（合成）：GPU层合成
```

### 每个阶段的耗时与优化切入点

| 阶段 | 典型耗时 | 优化切入点 |
|------|----------|------------|
| DNS 解析 | 20-120ms | dns-prefetch 预解析 |
| TCP/TLS 握手 | 50-200ms | preconnect 预连接、HTTP/2 连接复用 |
| HTTP 请求/响应 | 100-500ms | CDN、Brotli 压缩、缓存策略 |
| HTML 解析 | 10-50ms | 减少嵌套层数、避免同步 script |
| CSS 解析 | 5-30ms | 精简 CSS、内联关键 CSS |
| Layout | 5-50ms | 减少回流触发、避免强制同步布局 |
| Paint | 10-100ms | 减少重绘区域、避免大阴影/模糊 |
| Composite | 1-10ms | 使用合成层优化动画 |

> 理解渲染管线的意义不在于背流程，而在于知道每个阶段能做什么优化。

参考来源：[Chrome Developers - Critical Rendering Path](https://web.dev/articles/critical-rendering-path)

## 2.2 关键渲染路径优化策略

### 阻塞渲染资源识别

浏览器解析 HTML 时，遇到同步 `<script>` 会阻塞 DOM 解析（因为脚本可能修改 DOM），遇到 CSS 会阻塞渲染（因为渲染需要 CSSOM）。

```html
<!-- 阻塞DOM解析：脚本执行完才继续解析 -->
<script src="app.js"></script>

<!-- 不阻塞DOM解析：异步下载，下载完执行 -->
<script src="app.js" async></script>

<!-- 不阻塞DOM解析：异步下载，DOM解析完按顺序执行 -->
<script src="app.js" defer></script>
```

### defer vs async 对比

```
HTML解析:  ████████████████████████
async下载:   ████
async执行:          ██（下载即执行，可能打断解析）

HTML解析:  ████████████████████████
defer下载:   ████
defer执行:                        ██（解析完后执行）
```

| 属性 | 下载时机 | 执行时机 | 执行顺序 | 适用场景 |
|------|----------|----------|----------|----------|
| 无 | 遇到即下载 | 下载完即执行 | 按位置 | 主脚本（但阻塞） |
| `async` | 并行下载 | 下载完即执行 | 不保证顺序 | 独立脚本（统计、广告） |
| `defer` | 并行下载 | DOM解析完后 | 按位置顺序 | 主应用脚本 |

### preload 与关键 CSS 内联

```html
<!-- preload：高优先级预加载当前页必需资源 -->
<link rel="preload" href="critical-font.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="hero.jpg" as="image">

<!-- 内联关键 CSS：首屏样式直接写在 HTML 中 -->
<style>
  body { margin: 0; font-family: sans-serif; }
  .hero { width: 100%; height: 300px; background: #f0f0f0; }
</style>
<!-- 非关键 CSS 异步加载 -->
<link rel="preload" href="full-styles.css" as="style" onload="this.rel='stylesheet'">
```

> 关键渲染路径优化的核心：让浏览器尽快拿到首屏需要的所有东西。

参考来源：[MDN - script element](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/script)、[web.dev - Defer non-critical CSS](https://web.dev/articles/defer-non-critical-css)

## 2.3 回流与重绘的最小化策略

### 三者关系

```
Layout（回流）-> Paint（重绘）-> Composite（合成）
```

- 回流：几何属性变化（width/height/margin/top 等），触发重新布局
- 重绘：外观属性变化（color/background/visibility 等），不触发布局但触发绘制
- 合成：仅 GPU 层合成（transform/opacity），不触发布局和绘制

### 触发条件对比

| 操作 | 回流 | 重绘 | 合成 |
|------|------|------|------|
| 改 width/height/margin | 触发 | 触发 | 触发 |
| 改 color/background | 不触发 | 触发 | 触发 |
| 改 transform/opacity | 不触发 | 不触发 | 仅合成 |
| 改 className | 可能 | 可能 | 可能 |
| 添加/删除 DOM | 触发 | 触发 | 触发 |
| 读取 offsetHeight | 强制同步布局 | 不触发 | 不触发 |

### 优化手段

```javascript
// 避免：强制同步布局（Layout Thrashing）
// 读取 offsetHeight 触发回流，写入后再读再触发
for (let i = 0; i < items.length; i++) {
  items[i].style.width = box.offsetWidth + 'px'; // 每次读+写都触发回流
}

// 优化：先读后写，批量操作
const widths = items.map(item => item.offsetWidth); // 先批量读
items.forEach((item, i) => {
  item.style.width = widths[i] + 'px'; // 再批量写
});

// 更优：使用 DocumentFragment 批量修改 DOM
const fragment = document.createDocumentFragment();
items.forEach(item => fragment.appendChild(item));
container.appendChild(fragment); // 只触发一次回流

// 动画属性选择：transform 替代 top/left
// 避免：
// element.style.left = x + 'px';
// element.style.top = y + 'px';

// 推荐：
element.style.transform = `translate(${x}px, ${y}px)`;
```

> 回流是性能杀手，重绘是帮凶，合成才是性能的解药。

参考来源：[web.dev - Avoid large, complex layouts and layout thrashing](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing)

## 2.4 浏览器进程与线程模型

### 多进程架构

现代浏览器（如 Chrome）采用多进程架构：

```
Browser Process（浏览器主进程）
├── Renderer Process（渲染进程）- 每个标签页一个
│   ├── Main Thread（主线程）：JS执行、DOM、CSS解析、Layout、Paint
│   ├── Compositor Thread（合成线程）：接收绘制指令，合成图层
│   ├── Parser Thread（解析线程）：HTML解析
│   └── Worker Thread：Web Worker
├── GPU Process（GPU进程）：接收所有标签页的合成指令
├── Plugin Process（插件进程）：每个插件独立进程
└── Network Process（网络进程）：网络请求
```

### 前端启示

理解这个模型对日常开发有直接指导意义：

- JS 在主线程执行，长时间任务会阻塞渲染 -> 用 Web Worker 做计算密集任务
- 合成线程独立于主线程 -> transform/opacity 动画不被 JS 阻塞
- `requestIdleCallback` 在主线程空闲时执行低优先级任务

```javascript
// Web Worker：计算密集任务移出主线程
const worker = new Worker('compute.js');
worker.postMessage({ data: largeArray });
worker.onmessage = (e) => {
  console.log('计算结果:', e.data);
};

// requestIdleCallback：低优先级任务
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0) {
    doLowPriorityWork();
  }
});
```

> 不理解浏览器线程模型，就不知道为什么 JS 会卡页面，也就做不好性能优化。

参考来源：[Chrome Developers - Inside look at modern web browser](https://developer.chrome.com/blog/inside-browser-part3)

## 2.5 CSS Hack 与浏览器前缀的现代工程方案

### 浏览器前缀的历史

CSS3 新属性最初以浏览器前缀形式发布实验特性：`-webkit-`（Chrome/Safari）、`-moz-`（Firefox）、`-ms-`（IE/Edge）。这导致代码里充斥各种前缀。

### 现代方案：Autoprefixer + PostCSS

```javascript
// postcss.config.js
module.exports = {
  plugins: [
    require('autoprefixer')({
      overrideBrowserslist: ['> 1%', 'last 2 versions']
    })
  ]
};

// 你只需写标准 CSS：
// display: flex;
// Autoprefixer 自动输出：
// display: -webkit-box; display: -ms-flexbox; display: flex;
```

### 特征检测 @supports

```css
/* 特征检测优于 UA 嗅探 */
@supports (display: grid) {
  .layout {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
}

@supports not (display: grid) {
  .layout {
    display: flex;
    flex-wrap: wrap;
  }
}
```

```javascript
// JS 中的特征检测
if (CSS.supports('display', 'grid')) {
  // 支持 Grid
} else {
  // fallback
}
```

> 检测能力而非检测浏览器，这是兼容性的基本原则。

参考来源：[MDN - @supports](https://developer.mozilla.org/zh-CN/docs/Web/CSS/@supports)、[PostCSS - Autoprefixer](https://github.com/postcss/autoprefixer)

## 2.6 跨浏览器兼容性实战：IE/Edge/Safari/Chrome

### 语法兼容：Babel + Polyfill

```javascript
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', {
      useBuiltIns: 'usage',  // 按需引入 Polyfill
      corejs: 3
    }]
  ]
};
```

`useBuiltIns: 'usage'` 会分析代码中实际用到的 API，精准引入对应的 polyfill，避免打包整个 core-js。

### CSS fallback 写法

```css
/* 先写 fallback，再写现代属性 */
.hero {
  /* fallback：不支持 grid 的浏览器用 flex */
  display: flex;
  flex-wrap: wrap;

  /* 现代写法：支持 grid 的浏览器覆盖上面的 */
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}
```

### Safari 独有兼容问题

```css
/* Safari 100vh 问题：地址栏收起/展开导致 100vh 变化 */
.full-height {
  height: 100vh; /* Safari 有 bug */
  height: 100dvh; /* Dynamic viewport height，Safari 15.4+ 支持 */
  height: -webkit-fill-available; /* 备选 */
}

/* position: sticky 前缀（旧版 Safari） */
.sticky {
  position: -webkit-sticky;
  position: sticky;
  top: 0;
}
```

```javascript
// Safari 日期格式严格：不支持 yyyy-mm-dd，需要替换为 /
const date = new Date('2024-01-15'.replace(/-/g, '/'));
```

> 兼容性问题的本质不是背有多少个 bug，是建立系统化的检测、fallback、验证流程。

参考来源：[Babel - @babel/preset-env](https://babeljs.io/docs/babel-preset-env)、[caniuse.com](https://caniuse.com/)

## 2.7 浏览器缓存机制：强缓存与协商缓存的完整流程

### 缓存决策流程

```
浏览器发请求
    |
    v
有本地缓存？--否--> 向服务器发请求 --> 200 响应 + 缓存头
    |
    是
    v
缓存未过期？（Cache-Control/Expires）--是--> 200 from cache（强缓存）
    |
    否
    v
发协商请求（带 If-Modified-Since / If-None-Match）
    |
    v
资源未变？（服务端比对 Last-Modified / ETag）
    |
    是 --> 304 Not Modified（协商缓存，用本地副本）
    |
    否 --> 200 + 新资源 + 新缓存头
```

### 强缓存 vs 协商缓存

| 类型 | 相关头部 | 不发请求 | 状态码 |
|------|----------|----------|--------|
| 强缓存 | Cache-Control / Expires | 是 | 200 from cache |
| 协商缓存 | Last-Modified / ETag | 否（发协商请求） | 304 |

### 核心配置

```nginx
# Nginx 配置示例
# 静态资源：强缓存 + 文件指纹
location ~* \.(js|css|png|jpg|gif|svg|woff2)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

# HTML 文件：协商缓存（保证用户及时拿到新版）
location ~* \.html$ {
  add_header Cache-Control "no-cache";
  # no-cache：可以缓存，但每次使用前必须向服务器验证
}
```

关键策略：带文件指纹的资源（如 `app.a1b2c3.js`）用强缓存一年，HTML 入口文件用协商缓存。

> 缓存策略做好了，二次访问可以快到毫秒级。

参考来源：[MDN - HTTP Caching](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Caching)

## 2.8 跨域问题的根本原因与全方案解决

### 同源策略

同源策略（Same-Origin Policy）要求：协议、域名、端口三者完全一致才允许跨资源访问。这是浏览器的安全基石。

### CORS 机制

CORS（Cross-Origin Resource Sharing，跨源资源共享）是标准跨域方案：

```
简单请求（GET/POST + 简单Content-Type）：
  浏览器直接发请求，服务端返回 Access-Control-Allow-Origin

非简单请求（PUT/DELETE/自定义头）：
  浏览器先发 OPTIONS 预检请求
  服务端返回允许的方法和头
  浏览器再发真实请求
```

```nginx
# 服务端 CORS 配置
add_header Access-Control-Allow-Origin "https://example.com" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
add_header Access-Control-Max-Age 86400 always;

# 处理预检请求
if ($request_method = OPTIONS) {
  return 204;
}
```

### 代理方案

```javascript
// 开发环境：Vite/Webpack 代理
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'https://backend.example.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
};
```

```nginx
# 生产环境：Nginx 反向代理
location /api/ {
  proxy_pass https://backend.example.com/;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}
```

### postMessage 跨文档通讯

```javascript
// 父页面 -> iframe
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage(
  { type: 'data', payload: { id: 1 } },
  'https://child.example.com'
);

// iframe 接收
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://parent.example.com') return; // 校验来源
  console.log('收到数据:', e.data);
});
```

> 跨域不是 bug，是安全特性。理解了同源策略，所有跨域方案都是顺理成章的。

参考来源：[MDN - CORS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)、[MDN - postMessage](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/postMessage)

## 2.9 浏览器垃圾回收（V8 引擎）对前端编码的影响

### 分代回收模型

V8 引擎采用分代垃圾回收机制：

```
新生代（Young Generation）：短生命周期对象
  └── Scavenge 算法：From/To 两块空间，存活对象复制到 To 空间

老生代（Old Generation）：长生命周期对象（经过两次 Scavenge 晋升）
  ├── Mark-Sweep（标记清除）：标记存活对象，清除未标记
  └── Mark-Compact（标记整理）：清除同时整理碎片
```

### 常见内存泄漏

```javascript
// 泄漏1：未清除的定时器
setInterval(() => {
  referenceBigObject(); // 一直持有大对象引用
}, 1000);
// 修复：组件销毁时 clearInterval(timer)

// 泄漏2：闭包持有不必要的大对象
function createHandler() {
  const hugeData = new Array(1000000).fill('data');
  return () => {
    console.log('只用了hugeData的长度:', hugeData.length);
    // hugeData 整个被闭包持有，无法回收
  };
}
// 修复：只保存需要的值
function createHandler() {
  const len = new Array(1000000).fill('data').length;
  return () => console.log('长度:', len);
}

// 泄漏3：脱离 DOM 树的引用
const btn = document.querySelector('#btn');
document.body.removeChild(btn);
// btn 变量仍持有引用，DOM 节点无法回收
// 修复：removeChild 后置 null
btn = null;

// 泄漏4：未移除的事件监听
element.addEventListener('click', handler);
// 组件销毁时未 removeEventListener
// 修复：销毁时移除监听
element.removeEventListener('click', handler);
```

### WeakMap 配合 GC

```javascript
// WeakMap 的 key 是弱引用，不阻止 GC
const cache = new WeakMap();

function process(obj) {
  if (!cache.has(obj)) {
    cache.set(obj, expensiveCompute(obj));
  }
  return cache.get(obj);
}
// obj 被回收时，对应的缓存条目自动消失
```

> 内存泄漏不是代码报错，是沉默的性能杀手。Chrome DevTools Memory 面板是最好的排查工具。

参考来源：[V8 - Trash talk: the Orinoco garbage collector](https://v8.dev/blog/orinoco)、[MDN - WeakMap](https://developer.mozilla.org/zh-CN/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)

## 2.10 合成层与 GPU 加速

### 合成层触发条件

以下条件会为元素创建独立的合成层（Compositing Layer）：

| 条件 | 示例 |
|------|------|
| 3D transform | `transform: translateZ(0)` |
| will-change | `will-change: transform` |
| opacity 动画 | `@keyframes fade { from { opacity: 0 } }` |
| video/canvas | 媒体元素 |
| position: fixed | 固定定位元素 |
| CSS filter | `filter: blur(5px)` |

### 渲染流程

```
主线程：JS -> Style -> Layout -> Paint -> 生成绘制指令
                                                    |
合成线程：接收绘制指令 -> 分配图层 -> 光栅化 --------|
                                                    |
GPU进程：合成所有图层 -> 输出到屏幕
```

合成层的优势在于：动画只在合成线程和 GPU 处理，完全不阻塞主线程。

### will-change 的正确使用

```css
/* 正确：动画前声明，动画后移除 */
.smooth-card {
  will-change: transform;
  transition: transform 0.3s;
}
.smooth-card:hover {
  transform: scale(1.05);
}

/* 错误：滥用 will-change，每个元素都声明 */
* {
  will-change: transform; /* 层爆炸！ */
}
```

> will-change 是一把双刃剑：用好了动画丝滑，用坏了内存翻倍。

参考来源：[Chrome Developers - GPU Accelerated Compositing in Chrome](https://developer.chrome.com/blog/gpu-accelerated-compositing-in-chrome)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| URL到渲染全链路 | 浏览器工作原理 | 高 |
| 关键渲染路径优化 | 首屏渲染性能优化 | 高 |
| 回流重绘合成最小化 | 渲染性能调优 | 高 |
| 进程与线程模型 | 理解JS阻塞原因 | 中高 |
| CSS前缀与现代工程 | 兼容性工程化 | 中 |
| 跨浏览器兼容实战 | 多浏览器适配 | 中高 |
| 浏览器缓存机制 | 缓存策略设计 | 高 |
| 跨域全方案 | 跨域问题解决能力 | 高 |
| V8垃圾回收与泄漏 | 内存管理 | 中高 |
| 合成层与GPU加速 | 动画性能优化 | 中 |

这篇建议收藏，面试前对着流程图过一遍。你在哪个浏览器踩过最离谱的兼容性坑？评论区说说。关注怕浪猫，下期讲多设备适配与响应式布局。系列进度 2/10。

下一篇我们拆解响应式布局：rem/vw/rpx 怎么选、1px 边框问题、刘海屏适配、大屏可视化方案。

# 第1章：H5 基础与语义化

10个H5基础问题，我靠第3个少写了200行代码。我是怕浪猫，一个在前端摸爬滚打多年的开发者，这个系列带你把H5、浏览器、跨端通讯、性能优化、微前端全部讲透。

HTML5 不是 HTML 的简单升级，它重新定义了前端的存储体系、通讯方式、设备能力调用和图形渲染方案。很多人用了几年 H5，其实只用了 LocalStorage 和几个新标签。今天这篇，怕浪猫把 H5 基础里最该掌握的 10 个问题讲清楚。

## 1.1 HTML5 新增语义化标签及解决的问题

### 语义化标签清单

HTML5 引入了一批语义化标签，用来替代"满天飞 div"的写法：

| 标签 | 语义 | 典型使用场景 |
|------|------|-------------|
| `<header>` | 页面或区块的头部 | 站点头、文章标题区 |
| `<nav>` | 导航区域 | 主导航、面包屑 |
| `<main>` | 页面主要内容 | 每页只出现一次 |
| `<article>` | 独立完整的内容 | 文章、评论、卡片 |
| `<section>` | 内容分区 | 文章章节、功能区块 |
| `<aside>` | 侧边或辅助内容 | 侧边栏、相关推荐 |
| `<footer>` | 页面或区块底部 | 版权信息、脚注 |

### 语义化解决了什么问题

div 命名混乱是前端的老问题。同一个页面，不同开发者写的 div class 名五花八门，维护成本极高。语义化标签从根本上解决了四个问题：

- SEO（Search Engine Optimization，搜索引擎优化）：爬虫能理解页面结构，提升搜索权重
- 无障碍阅读：屏幕阅读器（如 VoiceOver）依赖语义标签为视障用户导航
- 代码可维护性：标签本身即文档，看标签就知道结构
- 浏览器特性支持：部分浏览器对 `<main>` 等标签有专门的快捷键导航

### 语义化布局 vs div 布局

一个典型的文章页面，两种写法对比：

```html
<!-- div 布局：结构靠 class 名猜 -->
<div class="header">
  <div class="nav">...</div>
</div>
<div class="main">
  <div class="article">
    <div class="section">...</div>
  </div>
  <div class="sidebar">...</div>
</div>
<div class="footer">...</div>
```

```html
<!-- 语义化布局：标签即文档 -->
<header>
  <nav>...</nav>
</header>
<main>
  <article>
    <section>...</section>
  </article>
  <aside>...</aside>
</main>
<footer>...</footer>
```

> 语义化不是给机器看的，是给三个月后的自己看的。

参考来源：[WHATWG HTML Living Standard - Semantics](https://html.spec.whatwg.org/multipage/semantics.html)

## 1.2 H5 离线存储方案全景对比

### 存储方案清单

H5 提供了多种存储方案，各有适用场景：

| 方案 | 容量 | 时效 | 异步 | 数据结构 | 适用场景 |
|------|------|------|------|----------|----------|
| LocalStorage | 5-10MB | 永久 | 同步 | 字符串键值对 | 配置、Token |
| SessionStorage | 5-10MB | 标签页关闭 | 同步 | 字符串键值对 | 临时表单数据 |
| IndexedDB | 数百MB+ | 永久 | 异步 | 结构化对象 | 离线数据、大量数据 |
| Cache API | 数百MB+ | 永久 | 异步 | Request/Response | Service Worker 缓存 |
| Application Cache | - | 已废弃 | - | - | 已被 Service Worker 替代 |

### 选型决策

选择存储方案的逻辑很简单：小数据用 LocalStorage，大数据用 IndexedDB，离线缓存用 Cache API。

```javascript
// LocalStorage：简单键值对
localStorage.setItem('token', 'abc123');
const token = localStorage.getItem('token');

// IndexedDB：结构化大数据存储
const request = indexedDB.open('MyDB', 1);
request.onupgradeneeded = (e) => {
  const db = e.target.result;
  db.createObjectStore('users', { keyPath: 'id' });
};
request.onsuccess = (e) => {
  const db = e.target.result;
  const tx = db.transaction('users', 'readwrite');
  tx.objectStore('users').add({ id: 1, name: '怕浪猫' });
};
```

Application Cache（AppCache）已经废弃，现代项目用 Service Worker + Cache API 替代。如果你在老项目里看到 `<html manifest="app.appcache">`，那是历史遗留。

> 没有最好的存储方案，只有最适合场景的方案。

参考来源：[MDN - Web Storage API](https://developer.mozilla.org/zh-CN/docs/Web/API/Web_Storage_API)、[MDN - IndexedDB API](https://developer.mozilla.org/zh-CN/docs/Web/API/IndexedDB_API)

## 1.3 Service Worker 生命周期与离线可用实现

### 生命周期

Service Worker（服务工作线程）是 PWA（Progressive Web App，渐进式 Web 应用）的核心。它的生命周期分为三个阶段：

```
注册 -> 安装(install) -> 激活(activate) -> 运行(监听fetch/push/sync)
```

安装阶段缓存静态资源，激活阶段清理旧缓存，运行阶段拦截网络请求。

### 三种缓存策略

| 策略 | 逻辑 | 适用场景 |
|------|------|----------|
| Cache First | 先查缓存，缓存没有才请求网络 | 静态资源（CSS/JS/图片） |
| Network First | 先请求网络，失败再用缓存 | API 数据、动态内容 |
| Stale-While-Revalidate | 先返回缓存，同时后台更新缓存 | 非关键动态数据 |

### 核心代码实现

```javascript
// 注册 Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW registered', reg.scope));
}

// sw.js - Service Worker 主文件
const CACHE_NAME = 'v1';
const ASSETS = ['/index.html', '/style.css', '/app.js'];

// install：预缓存静态资源
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
});

// activate：清理旧缓存
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

// fetch：Cache First 策略
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
```

> Service Worker 不是离线的开关，而是离线策略的调度器。

参考来源：[MDN - Service Worker API](https://developer.mozilla.org/zh-CN/docs/Web/API/Service_Worker_API)、[web.dev - Service Workers](https://web.dev/learn/pwa/service-workers/)

## 1.4 HTML5 input 类型与移动端表单体验优化

### input type 全清单

HTML5 新增了多种 input 类型，移动端会根据 type 自动弹出对应键盘：

| type 值 | 弹出键盘 | 附加特性 |
|---------|----------|----------|
| `email` | 带@符号的键盘 | 自动校验邮箱格式 |
| `tel` | 数字拨号键盘 | 不校验格式，需 pattern |
| `number` | 数字键盘 | 支持 min/max/step |
| `url` | 带/和.com的键盘 | 自动校验 URL 格式 |
| `date` | 日期选择器 | 支持 min/max |
| `search` | 带搜索按钮的键盘 | 部分浏览器样式不同 |

### 表单体验优化清单

```html
<!-- 自动聚焦 + 输入类型 + 自动补全 -->
<input type="tel" autofocus autocomplete="tel"
       pattern="[0-9]{11}" placeholder="请输入手机号"
       enterkeyhint="done">

<!-- 邮箱输入：自动弹出@键盘 -->
<input type="email" autocomplete="email"
       placeholder="请输入邮箱">

<!-- 搜索框：键盘带搜索按钮 -->
<input type="search" enterkeyhint="search"
       placeholder="搜索">
```

几个关键属性的含义：

- `autocomplete`：浏览器自动填充支持（如姓名、电话、邮箱）
- `autocapitalize="off"`：关闭移动端自动大写
- `enterkeyhint`：设置键盘回车键的文案（done/search/next/go）
- `inputmode`：比 type 更细粒度地控制键盘类型

> 表单体验优化的核心不是技术，是减少用户每一次输入的摩擦。

参考来源：[MDN - The Input (Form Input) element](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/input)

## 1.5 Web Storage 事件机制与多标签页数据同步

### storage 事件触发原理

当 LocalStorage 或 SessionStorage 的值发生变化时，同源的其他标签页会收到 storage 事件。注意，触发事件的标签页自身不会收到这个事件。

```
标签页A 修改 LocalStorage
         |
         v
标签页B 收到 storage 事件
标签页C 收到 storage 事件
标签页A 自身不收到
```

### 多标签页登录状态同步

```javascript
// 标签页A：登录后写入
localStorage.setItem('loginStatus', JSON.stringify({
  userId: 1,
  token: 'abc123',
  timestamp: Date.now()
}));

// 标签页B/C：监听变化
window.addEventListener('storage', (e) => {
  if (e.key === 'loginStatus') {
    const data = JSON.parse(e.newValue);
    if (data.token) {
      updateUI(data); // 更新页面登录态
    } else {
      logout(); // token 被清除，同步登出
    }
  }
});
```

### BroadcastChannel 作为替代方案

BroadcastChannel API 提供了更语义化的跨标签通讯方式：

```javascript
// 创建频道
const channel = new BroadcastChannel('login_sync');

// 标签页A：发送消息
channel.postMessage({ type: 'login', token: 'abc123' });

// 标签页B：接收消息
channel.onmessage = (e) => {
  if (e.data.type === 'login') {
    updateUI(e.data);
  }
};
```

两者对比：storage 事件只能传字符串，BroadcastChannel 可以传对象；但 BroadcastChannel 在 Safari 15.4 之前不支持。生产环境建议做兼容处理。

> 多标签同步不是炫技，是用户在多个标签页登录/登出时体验一致性的底线。

参考来源：[MDN - Storage Event](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/storage_event)、[MDN - BroadcastChannel API](https://developer.mozilla.org/zh-CN/docs/Web/API/BroadcastChannel)

## 1.6 Cookie、Session、Token 在前端的实践

### Cookie 核心字段

Cookie 是最传统的前端存储方式，核心字段决定了它的安全行为：

| 字段 | 作用 | 推荐值 |
|------|------|--------|
| `httpOnly` | 禁止 JS 访问 Cookie | true（防 XSS 窃取） |
| `secure` | 仅 HTTPS 传输 | true |
| `sameSite` | 跨站发送策略 | Lax / None+Secure |
| `max-age` | 过期时间（秒） | 按业务设置 |

### SameSite 的三种值

- `Strict`：完全不跨站发送，最安全但体验差（链接跳转也不带 Cookie）
- `Lax`：默认值，导航到目标网站时发送（GET 请求），基本够用
- `None`：允许跨站发送，但必须配合 `Secure`（仅 HTTPS）

### JWT 存储方案对比

JWT（JSON Web Token）是现代前后端分离架构的常用认证方案。前端拿到 Token 后存哪里：

| 存储位置 | 优点 | 缺点 |
|----------|------|------|
| LocalStorage | JS 可读，方便注入请求头 | XSS 可窃取 |
| Cookie (httpOnly) | XSS 不可窃取 | 需处理后端 CSRF |

```javascript
// Token 存储与请求拦截器注入
const TOKEN_KEY = 'auth_token';

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// axios 请求拦截器自动注入
axios.interceptors.request.use(config => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

> Token 存哪里不是选最安全的，是选在你的安全体系下风险最小的。

参考来源：[MDN - HTTP Cookies](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Cookies)、[RFC 6750 - OAuth 2.0 Bearer Token](https://tools.ietf.org/html/rfc6750)

## 1.7 H5 设备能力 API：Geolocation 与 DeviceOrientation

### Geolocation API

H5 提供了获取用户地理位置的能力，但有两个硬性限制：必须 HTTPS 环境、必须用户授权。

```javascript
// 获取定位
navigator.geolocation.getCurrentPosition(
  (position) => {
    console.log('纬度:', position.coords.latitude);
    console.log('经度:', position.coords.longitude);
    console.log('精度:', position.coords.accuracy);
  },
  (error) => {
    console.error('定位失败:', error.message);
  },
  { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
);
```

### DeviceOrientation API

DeviceOrientationEvent 可以获取设备的方向和加速度信息，常用于摇一摇、指南针等场景：

```javascript
// iOS 13+ 需要手动请求权限
if (typeof DeviceOrientationEvent.requestPermission === 'function') {
  DeviceOrientationEvent.requestPermission()
    .then(state => {
      if (state === 'granted') {
        window.addEventListener('deviceorientation', handleOrientation);
      }
    })
    .catch(err => console.error('权限请求失败', err));
} else {
  // Android 直接监听
  window.addEventListener('deviceorientation', handleOrientation);
}

function handleOrientation(e) {
  console.log('alpha（Z轴）:', e.alpha); // 0-360
  console.log('beta（X轴）:', e.beta);   // -180-180
  console.log('gamma（Y轴）:', e.gamma);  // -90-90
}
```

iOS 13 之后苹果收紧了设备传感器权限，必须在用户手势（如点击按钮）触发后才能调用 `requestPermission()`，否则静默失败。

> 设备能力 API 的核心限制不是代码，是用户授权——别忘了设计友好的授权引导。

参考来源：[MDN - Geolocation API](https://developer.mozilla.org/zh-CN/docs/Web/API/Geolocation_API)、[MDN - DeviceOrientation Event](https://developer.mozilla.org/zh-CN/docs/Web/API/DeviceOrientationEvent)

## 1.8 WebSocket 与 SSE 的对比与选择

### 通讯模型对比

| 特性 | WebSocket | SSE（Server-Sent Events） |
|------|-----------|--------------------------|
| 通讯方向 | 全双工（双向） | 单向（服务端推送） |
| 数据格式 | 文本 + 二进制 | 纯文本（UTF-8） |
| 协议 | WS（基于 TCP） | HTTP |
| 自动重连 | 需手动实现 | 浏览器自动重连 |
| 浏览器兼容 | 广泛 | 除 IE 外广泛 |
| 适用场景 | IM、游戏、协同编辑 | 通知、股票行情、日志推送 |

### WebSocket 连接建立与消息收发

```javascript
// 建立连接
const ws = new WebSocket('wss://example.com/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'auth', token: 'abc123' }));
};

ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('收到消息:', data);
};

ws.onclose = () => {
  console.log('连接关闭，准备重连');
  // 实际项目需要指数退避重连
};

// 主动发送消息
ws.send(JSON.stringify({ type: 'message', content: '你好' }));
```

### SSE 实现服务端推送

```javascript
// 前端：建立 SSE 连接
const source = new EventSource('/api/notifications');

source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('收到推送:', data);
};

source.onerror = () => {
  console.log('连接异常，浏览器会自动重连');
};
```

选型原则：需要客户端主动发消息选 WebSocket，只需要服务端推送选 SSE。SSE 的自动重连机制在生产环境非常省心。

> 实时通讯方案的选择不取决于哪个更先进，取决于你的通讯模式是双向还是单向。

参考来源：[MDN - WebSocket API](https://developer.mozilla.org/zh-CN/docs/Web/API/WebSocket)、[MDN - Server-Sent Events](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events)

## 1.9 H5 拖放 API 原理与移动端兼容方案

### 拖放事件链

HTML5 的拖放 API 基于一组事件链工作：

```
dragstart -> drag -> dragenter -> dragover -> dragleave/drop -> dragend
```

| 事件 | 触发对象 | 作用 |
|------|----------|------|
| `dragstart` | 被拖元素 | 开始拖动，设置 dataTransfer |
| `dragover` | 拖动经过的目标 | 必须 preventDefault 才能允许 drop |
| `drop` | 放置目标 | 处理放置逻辑 |
| `dragend` | 被拖元素 | 拖动结束清理 |

### 桌面端实现

```javascript
// 被拖元素
const item = document.querySelector('.drag-item');
item.draggable = true;

item.addEventListener('dragstart', (e) => {
  e.dataTransfer.setData('text/plain', item.id);
});

// 放置目标
const dropZone = document.querySelector('.drop-zone');

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault(); // 必须 preventDefault
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  const id = e.dataTransfer.getData('text/plain');
  const dragged = document.getElementById(id);
  dropZone.appendChild(dragged);
});
```

### 移动端兼容方案

移动端浏览器不支持原生 DnD（Drag and Drop），因为触摸事件和拖动行为冲突。解决方案是用 Touch 事件模拟：

```javascript
// 移动端拖放模拟（简化版）
let touchItem = null;
let offsetX = 0, offsetY = 0;

element.addEventListener('touchstart', (e) => {
  touchItem = e.target;
  const rect = touchItem.getBoundingClientRect();
  const touch = e.touches[0];
  offsetX = touch.clientX - rect.left;
  offsetY = touch.clientY - rect.top;
  touchItem.style.position = 'fixed';
});

element.addEventListener('touchmove', (e) => {
  if (!touchItem) return;
  e.preventDefault();
  const touch = e.touches[0];
  touchItem.style.left = (touch.clientX - offsetX) + 'px';
  touchItem.style.top = (touch.clientY - offsetY) + 'px';
});

element.addEventListener('touchend', (e) => {
  // 检测是否在 drop zone 内
  const touch = e.changedTouches[0];
  const target = document.elementFromPoint(touch.clientX, touch.clientY);
  if (target && target.classList.contains('drop-zone')) {
    target.appendChild(touchItem);
  }
  touchItem.style.position = '';
  touchItem = null;
});
```

生产环境推荐使用 `interact.js` 等库，已处理好各种边界情况。

> 桌面端用原生 DnD，移动端用 Touch 模拟——这不是重复造轮子，是平台差异的必然。

参考来源：[MDN - HTML Drag and Drop API](https://developer.mozilla.org/zh-CN/docs/Web/API/HTML_Drag_and_Drop_API)

## 1.10 Canvas 与 SVG 的选型决策

### 渲染机制对比

| 特性 | Canvas | SVG（Scalable Vector Graphics） |
|------|--------|------|
| 渲染方式 | 位图（像素绘制） | 矢量（DOM 节点） |
| DOM 可操作 | 否（整块画布） | 是（每个图形是 DOM 元素） |
| 性能 | 适合大量元素 | 元素多时性能下降 |
| 分辨率自适应 | 需手动处理 DPR | 天然矢量自适应 |
| 事件绑定 | 需手动碰撞检测 | 直接绑定 DOM 事件 |
| 适用场景 | 游戏、热力图、粒子动画 | 图表、地图、可交互图形 |

### 核心代码对比

```javascript
// Canvas：绘制一个圆
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
// 适配高分辨率屏幕
canvas.width = 300 * window.devicePixelRatio;
canvas.height = 300 * window.devicePixelRatio;
canvas.style.width = '300px';
canvas.style.height = '300px';
ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

ctx.beginPath();
ctx.arc(150, 150, 50, 0, Math.PI * 2);
ctx.fillStyle = '#4CAF50';
ctx.fill();
```

```html
<!-- SVG：绘制一个圆，天然矢量且可绑定事件 -->
<svg width="300" height="300" viewBox="0 0 300 300">
  <circle cx="150" cy="150" r="50" fill="#4CAF50"
          onclick="alert('点击了圆')" />
</svg>
```

选型原则：需要高性能渲染大量图形（如热力图、粒子效果）选 Canvas 或 WebGL（Web Graphics Library）；需要可交互、可缩放的图形（如图表、地图）选 SVG。

> Canvas 画的是像素，SVG 画的是 DOM——选择取决于你需要性能还是交互。

参考来源：[MDN - Canvas API](https://developer.mozilla.org/zh-CN/docs/Web/API/Canvas_API)、[MDN - SVG](https://developer.mozilla.org/zh-CN/docs/Web/SVG)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| 语义化标签 | HTML 结构设计能力 | 高 |
| 离线存储方案 | 存储体系全貌理解 | 高 |
| Service Worker | PWA 与离线策略 | 中高 |
| input 类型 | 移动端表单体验优化 | 中 |
| Web Storage 事件 | 多标签页数据同步 | 中 |
| Cookie/Session/Token | 认证体系前端实践 | 高 |
| 设备能力 API | H5 调用原生能力 | 中 |
| WebSocket vs SSE | 实时通讯选型 | 中高 |
| 拖放 API | 交互能力与移动端兼容 | 低 |
| Canvas vs SVG | 图形渲染选型 | 中 |

觉得有用？收藏起来，面试前翻一遍。你在 H5 开发中踩过哪个坑？评论区说说。关注怕浪猫，下期我们讲浏览器渲染原理与兼容性。系列进度 1/10。

下一篇我们拆解：从输入 URL 到页面渲染完成，浏览器到底做了什么？回流重绘、合成层、缓存机制，一篇讲透。

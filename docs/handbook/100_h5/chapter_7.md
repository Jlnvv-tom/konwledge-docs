# 第7章：iframe 与跨域通讯

iframe 不是上古遗物，现代微前端、第三方嵌入、广告系统都在用。这10个问题把 iframe 跨域通讯的坑全覆盖了。我是怕浪猫，一个在 iframe 里摸爬滚打多年的前端工程师。

## 7.1 iframe 的基本使用与 sandbox 安全沙箱

### 基本属性

```html
<iframe
  src="https://example.com/embed"
  width="100%"
  height="500"
  title="嵌入内容"
  loading="lazy"
  referrerpolicy="no-referrer"
  sandbox="allow-scripts allow-same-origin"
  allow="camera; microphone"
></iframe>
```

| 属性 | 作用 |
|------|------|
| `src` | 嵌入页面地址 |
| `title` | 无障碍描述（必须设置） |
| `loading="lazy"` | 懒加载（浏览器支持时） |
| `sandbox` | 安全沙箱限制 |
| `allow` | 权限策略（Permission Policy） |
| `referrerpolicy` | Referrer 策略 |

### sandbox 值详解

sandbox 是 iframe 最重要的安全机制，默认禁止一切：

| sandbox 值 | 允许的能力 |
|-----------|-----------|
| 不设置 sandbox | 无限制（不推荐） |
| `""`（空字符串） | 禁止所有 |
| `allow-scripts` | 允许执行 JS |
| `allow-same-origin` | 允许同源访问 |
| `allow-forms` | 允许表单提交 |
| `allow-popups` | 允许弹窗 |
| `allow-top-navigation` | 允许导航父窗口 |
| `allow-downloads` | 允许下载 |

```html
<!-- 安全配置：允许脚本但不能操作父页面 -->
<iframe
  src="https://untrusted.example.com"
  sandbox="allow-scripts"
></iframe>
<!-- 注意：不要同时设置 allow-scripts + allow-same-origin -->
<!-- 否则 iframe 可以修改自身的 sandbox 属性绕过限制 -->
```

> sandbox 是 iframe 的安全带，不系安全带的 iframe 就是别人在你页面上开的后门。

参考来源：[MDN - iframe element](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/iframe)、[MDN - sandbox attribute](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/iframe#sandbox)

## 7.2 postMessage 跨域通讯的安全规范

### 基本用法

```javascript
// 父页面 -> iframe
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage(
  { type: 'init', data: { userId: 123 } },
  'https://child.example.com'  // 必须指定目标 origin
);

// iframe -> 父页面
window.parent.postMessage(
  { type: 'ready', data: {} },
  'https://parent.example.com'
);
```

### 安全接收

```javascript
// 安全的消息接收：必须校验 origin
window.addEventListener('message', (e) => {
  // 1. 校验来源
  if (e.origin !== 'https://child.example.com') return;

  // 2. 校验消息格式
  if (!e.data || typeof e.data.type !== 'string') return;

  // 3. 校验来源窗口（可选但推荐）
  if (e.source !== expectedIframe.contentWindow) return;

  // 4. 处理消息
  switch (e.data.type) {
    case 'ready':
      handleReady(e.data);
      break;
    case 'data':
      handleData(e.data);
      break;
  }
});
```

### 常见安全错误

```javascript
// 错误1：targetOrigin 用通配符 *
iframe.contentWindow.postMessage(data, '*');
// 风险：消息可能被任意页面接收

// 错误2：不校验 origin
window.addEventListener('message', (e) => {
  doSomething(e.data); // 任意来源的消息都处理
});

// 错误3：eval 执行消息内容
window.addEventListener('message', (e) => {
  eval(e.data.code); // 严重漏洞
});
```

| 安全措施 | 作用 |
|----------|------|
| 指定 targetOrigin | 确保消息只发给目标域名 |
| 校验 e.origin | 确保只处理信任来源的消息 |
| 校验 e.source | 确保消息来自预期的窗口 |
| 校验消息结构 | 防止畸形数据导致异常 |
| 不 eval 消息内容 | 防止代码注入 |

> postMessage 本身是安全的，不安全的是"不校验"——所有 postMessage 漏洞都是因为偷懒没校验 origin。

参考来源：[MDN - Window.postMessage](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/postMessage)

## 7.3 iframe 高度自适应的跨域方案

### 同域方案

```javascript
// 父页面可以直接访问 iframe DOM
function resizeIframe() {
  const iframe = document.querySelector('iframe');
  iframe.style.height = iframe.contentWindow.document.body.scrollHeight + 'px';
}

// iframe 内触发
window.addEventListener('resize', () => {
  parent.postMessage({ type: 'resize', height: document.body.scrollHeight }, '*');
});
```

### 跨域方案

跨域时父页面无法直接读取 iframe 内部尺寸，需通过 postMessage 通讯：

```javascript
// iframe 内部：监听自身高度变化，通知父页面
function notifyHeight() {
  const height = document.documentElement.scrollHeight;
  window.parent.postMessage(
    { type: 'resize', height: height },
    'https://parent.example.com'
  );
}

// 初始通知
notifyHeight();

// 监听变化
const observer = new ResizeObserver(notifyHeight);
observer.observe(document.body);

// 父页面：接收高度并调整
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://child.example.com') return;
  if (e.data.type === 'resize') {
    const iframe = document.querySelector('iframe');
    iframe.style.height = e.data.height + 'px';
  }
});
```

### ResizeObserver 优势

| 方案 | 触发时机 | 性能 | 准确性 |
|------|----------|------|--------|
| setInterval 轮询 | 固定间隔 | 差 | 有延迟 |
| DOM MutationObserver | DOM 变化 | 中 | 可能遗漏样式变化 |
| ResizeObserver | 尺寸变化 | 好 | 实时准确 |

> 跨域 iframe 高度自适应的核心思路：iframe 自己量身高，通过 postMessage 告诉父页面。

## 7.4 iframe 性能问题与优化

### 性能影响

| 问题 | 影响 | 优化方案 |
|------|------|----------|
| 阻塞父页面 onload | iframe 加载完才触发 | loading="lazy" |
| 连接池竞争 | 占用 HTTP 连接 | 减少数量/异步加载 |
| 内存占用 | 每个独立渲染进程 | 按需创建销毁 |
| 渲染阻塞 | CSS/JS 执行 | sandbox 限制 |

### 异步加载

```javascript
// 方案1：IntersectionObserver 懒加载
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const iframe = entry.target;
      iframe.src = iframe.dataset.src; // 加载真实地址
      observer.unobserve(iframe);
    }
  });
});

document.querySelectorAll('iframe[data-src]').forEach(iframe => {
  observer.observe(iframe);
});
```

```html
<!-- 方案2：原生 loading="lazy" -->
<iframe src="https://example.com" loading="lazy"></iframe>
```

### 通信优化

```javascript
// 使用 MessageChannel 替代 postMessage（更安全、更高性能）
const channel = new MessageChannel();
const iframe = document.querySelector('iframe');

// 父页面发送 port
iframe.contentWindow.postMessage(
  { type: 'init' },
  'https://child.example.com',
  [channel.port2]
);

// iframe 接收 port
window.addEventListener('message', (e) => {
  if (e.data.type === 'init') {
    const port = e.ports[0];
    port.onmessage = (ev) => {
      console.log('收到消息:', ev.data);
    };
    // 通过 port 发送消息
    port.postMessage({ type: 'ready' });
  }
});
```

MessageChannel 的优势：建立专用通道，不需要每次校验 origin，且不会广播给其他监听者。

> iframe 性能优化的核心：懒加载 + 按需创建 + 高效通讯。

参考来源：[MDN - MessageChannel](https://developer.mozilla.org/zh-CN/docs/Web/API/MessageChannel)

## 7.5 X-Frame-Options 与 CSP frame-ancestors

### X-Frame-Options

通过 HTTP 响应头控制页面是否允许被 iframe 嵌入：

```
X-Frame-Options: DENY           # 完全禁止嵌入
X-Frame-Options: SAMEORIGIN     # 仅同源可嵌入
X-Frame-Options: ALLOW-FROM https://example.com  # 已废弃
```

### CSP frame-ancestors

CSP（Content Security Policy，内容安全策略）的 frame-ancestors 指令是 X-Frame-Options 的升级版，支持多个域名：

```
Content-Security-Policy: frame-ancestors 'self' https://trusted.example.com;
```

### 配置示例

```nginx
# Nginx 配置
# 方案1: 仅允许同源嵌入
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Content-Security-Policy "frame-ancestors 'self'" always;

# 方案2: 允许指定域名嵌入
add_header Content-Security-Policy "frame-ancestors 'self' https://parent.example.com" always;
```

### 前端检测

```javascript
// iframe 内部检测是否被嵌入
if (window.self !== window.top) {
  // 被嵌入了
  try {
    // 尝试访问父页面（同域时成功，跨域时报错）
    const parentOrigin = window.parent.location.origin;
    console.log('父页面同源:', parentOrigin);
  } catch (e) {
    // 跨域，被非法嵌入
    if (!isAllowedEmbedder()) {
      // 被非法嵌入，跳出
      window.top.location = window.self.location;
    }
  }
}

function isAllowedEmbedder() {
  // 通过 postMessage 确认父页面身份
  return new Promise(resolve => {
    const timeout = setTimeout(() => resolve(false), 1000);
    window.addEventListener('message', (e) => {
      if (e.data.type === 'parent-confirm' &&
          ALLOWED_ORIGINS.includes(e.origin)) {
        clearTimeout(timeout);
        resolve(true);
      }
    });
    window.parent.postMessage({ type: 'who-are-you' }, '*');
  });
}
```

| 方案 | 粒度 | 浏览器支持 | 推荐度 |
|------|------|-----------|--------|
| X-Frame-Options | 全局 | 全部 | 基础防护 |
| CSP frame-ancestors | 域名级 | 现代浏览器 | 推荐 |
| JS 检测 | 运行时 | 全部 | 补充手段 |

> 防嵌入要"服务端头 + 前端检测"双保险，单独任何一个都不够。

参考来源：[MDN - X-Frame-Options](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/X-Frame-Options)、[MDN - CSP frame-ancestors](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors)

## 7.6 iframe 间的通讯模式：父-子、子-子

### 父-子通讯

```javascript
// 父 -> 子
iframe.contentWindow.postMessage({ type: 'command', data: {} }, childOrigin);

// 子 -> 父
window.parent.postMessage({ type: 'event', data: {} }, parentOrigin);
```

### 子-子通讯（兄弟 iframe）

兄弟 iframe 之间无法直接通讯，需通过父页面中转：

```
iframeA -> parent -> iframeB
```

```javascript
// 父页面：消息路由器
const iframes = {
  a: document.querySelector('#iframe-a').contentWindow,
  b: document.querySelector('#iframe-b').contentWindow
};

window.addEventListener('message', (e) => {
  const { from, to, type, data } = e.data;
  // 校验来源
  if (e.source !== iframes[from]) return;

  // 转发给目标 iframe
  if (iframes[to]) {
    iframes[to].postMessage({ from, type, data }, toOrigin);
  }
});

// iframeA 发消息给 iframeB
window.parent.postMessage({
  from: 'a', to: 'b', type: 'sync', data: { value: 42 }
}, parentOrigin);
```

### MessageChannel 直连方案

```javascript
// 父页面：为两个 iframe 建立直接通道
const channel = new MessageChannel();

iframes.a.postMessage({ type: 'port', port: 'port1' }, aOrigin, [channel.port1]);
iframes.b.postMessage({ type: 'port', port: 'port2' }, bOrigin, [channel.port2]);

// iframeA 通过 port1 直接发消息给 iframeB
// iframeB 通过 port2 接收
// 父页面不再需要中转
```

> 子-子通讯通过父页面中转最简单，通过 MessageChannel 直连性能更好。

## 7.7 跨域资源共享（CORS）的完整机制

### 简单请求 vs 预检请求

```
简单请求条件（全部满足）：
  - 方法：GET / POST / HEAD
  - Content-Type：text/plain / application/x-www-form-urlencoded / multipart/form-data
  - 不含自定义头部

不满足以上条件 -> 触发预检（Preflight）
```

### 预检流程

```
1. 浏览器发送 OPTIONS 请求
   携带：Origin、Access-Control-Request-Method、Access-Control-Request-Headers

2. 服务端返回预检响应
   包含：Access-Control-Allow-Origin、Access-Control-Allow-Methods、
         Access-Control-Allow-Headers、Access-Control-Max-Age

3. 预检通过 -> 发送真实请求
   预检失败 -> 阻止真实请求，控制台报 CORS 错误
```

### 服务端配置

```nginx
# 完整 CORS 配置
location /api/ {
  # 允许的源
  add_header Access-Control-Allow-Origin "https://example.com" always;

  # 允许的方法
  add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;

  # 允许的头部
  add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With" always;

  # 允许携带 Cookie
  add_header Access-Control-Allow-Credentials "true" always;

  # 预检缓存时间（秒）
  add_header Access-Control-Max-Age 86400 always;

  # 处理预检请求
  if ($request_method = OPTIONS) {
    return 204;
  }

  proxy_pass http://backend;
}
```

### 携带 Cookie 的 CORS

```javascript
// 前端：fetch 携带 Cookie
fetch('https://api.example.com/data', {
  credentials: 'include'  // 必须设置
});

// axios
axios.defaults.withCredentials = true;

// 服务端必须返回：
// Access-Control-Allow-Origin: https://example.com （不能是 *）
// Access-Control-Allow-Credentials: true
```

> CORS 的核心是"服务端说了算"——浏览器只是执行者，所有决策都在服务端的响应头里。

参考来源：[MDN - CORS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)

## 7.8 第三方 Cookie 限制对 iframe 的影响

### 问题描述

现代浏览器逐步限制第三方 Cookie（Third-Party Cookie）。iframe 内的页面属于第三方上下文，其 Cookie 可能被拦截：

| 浏览器 | 限制状态 |
|--------|----------|
| Chrome | 逐步淘汰（2024年开始） |
| Safari | 已默认阻止（ITP） |
| Firefox | 默认阻止跟踪器 |

### 影响场景

- iframe 内登录态丢失（Cookie 不被接受）
- 第三方嵌入页面无法维持会话
- 跨域 iframe 内的 LocalStorage 被隔离

### 解决方案

```javascript
// 方案1: Storage Access API（请求用户授权访问第三方 Cookie）
if (document.requestStorageAccess) {
  try {
    await document.requestStorageAccess();
    // 用户授权后，iframe 可以访问其域名下的 Cookie
  } catch (e) {
    // 用户拒绝
    console.log('用户拒绝存储访问');
  }
}

// 方案2: 通过父页面中转 Token
// 父页面获取 Token -> postMessage 传给 iframe -> iframe 用 Token 请求

// 方案3: Partitioned Cookie（CHIPS）
// 服务端设置 Cookie 时加 Partitioned 属性
// Set-Cookie: auth=abc123; SameSite=None; Secure; Partitioned
// 每个顶级站点有独立的 Cookie 存储
```

```nginx
# 服务端: Partitioned Cookie
add_header Set-Cookie "session=abc123; Path=/; Secure; SameSite=None; Partitioned" always;
```

> 第三方 Cookie 的消亡是趋势，及早适配 Storage Access API 和 Partitioned Cookie 才是正道。

参考来源：[MDN - Storage Access API](https://developer.mozilla.org/zh-CN/docs/Web/API/Storage_Access_API)、[CHIPS](https://developers.google.com/privacy-sandbox/3pcd/chips)

## 7.9 iframe 中的路由与历史管理

### 历史栈问题

iframe 内的页面导航会修改父页面的历史栈（某些浏览器行为），导致用户点击后退按钮时在 iframe 内部后退而非父页面后退。

### 解决方案

```javascript
// iframe 内部：用 history.replaceState 替代 pushState
// 避免 iframe 内导航污染父页面历史栈
function navigateInIframe(url) {
  history.replaceState(null, '', url);
  loadContent(url);
}

// iframe 内部：拦截链接点击
document.addEventListener('click', (e) => {
  const link = e.target.closest('a');
  if (link && link.href.startsWith(location.origin)) {
    e.preventDefault();
    navigateInIframe(link.href);
  }
});
```

### 父子路由同步

```javascript
// iframe 内部：路由变化通知父页面
window.addEventListener('popstate', () => {
  window.parent.postMessage({
    type: 'route-change',
    path: location.pathname
  }, parentOrigin);
});

// 父页面：接收并更新 URL hash
window.addEventListener('message', (e) => {
  if (e.origin !== childOrigin) return;
  if (e.data.type === 'route-change') {
    history.replaceState(null, '', `#${e.data.path}`);
  }
});

// 父页面：刷新时恢复 iframe 路由
const hashPath = location.hash.slice(1);
if (hashPath) {
  iframe.src = `https://child.example.com${hashPath}`;
}
```

> iframe 路由管理的核心是"不污染父页面历史栈 + 父子路由同步"。

## 7.10 iframe 懒加载与可见性检测

### IntersectionObserver 懒加载

```javascript
const lazyIframes = document.querySelectorAll('iframe[data-src]');

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const iframe = entry.target;
      iframe.src = iframe.dataset.src;
      observer.unobserve(iframe);
    }
  });
}, {
  rootMargin: '200px'  // 提前 200px 加载
});

lazyIframes.forEach(iframe => observer.observe(iframe));
```

### 原生 loading="lazy"

```html
<iframe src="https://example.com" loading="lazy"></iframe>
```

浏览器原生懒加载不需要 JS，但可控性较差。

### Page Visibility API

```javascript
// 页面不可见时暂停 iframe 内的定时器/视频播放
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // 通知 iframe 页面不可见
    iframe.contentWindow.postMessage(
      { type: 'page-hidden' },
      childOrigin
    );
  } else {
    iframe.contentWindow.postMessage(
      { type: 'page-visible' },
      childOrigin
    );
  }
});

// iframe 内部接收
window.addEventListener('message', (e) => {
  if (e.data.type === 'page-hidden') {
    pauseAnimations();
  } else if (e.data.type === 'page-visible') {
    resumeAnimations();
  }
});
```

### 可见性与性能

```javascript
// 使用 requestIdleCallback 在空闲时预加载 iframe
requestIdleCallback((deadline) => {
  if (deadline.timeRemaining() > 0) {
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = 'https://example.com/preload';
    document.body.appendChild(iframe);
    // 预加载完成后移除，需要时再显示
    iframe.onload = () => {
      iframe.dataset.preloaded = 'true';
    };
  }
});
```

> 懒加载节省初始加载时间，可见性检测节省不可见时的资源消耗——两者配合让 iframe 更高效。

参考来源：[MDN - Intersection Observer](https://developer.mozilla.org/zh-CN/docs/Web/API/Intersection_Observer_API)、[MDN - Page Visibility API](https://developer.mozilla.org/zh-CN/docs/Web/API/Page_Visibility_API)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| sandbox 沙箱 | iframe 安全 | 高 |
| postMessage 安全规范 | 跨域通讯安全 | 高 |
| iframe 高度自适应 | 布局适配 | 中高 |
| iframe 性能优化 | 性能调优 | 中 |
| X-Frame-Options/CSP | 防嵌入策略 | 中高 |
| iframe 间通讯模式 | 架构设计 | 中 |
| CORS 完整机制 | 跨域资源访问 | 高 |
| 第三方 Cookie 限制 | 新特性适配 | 中 |
| iframe 路由管理 | 历史栈处理 | 低 |
| 懒加载与可见性 | 性能优化 | 中 |

这篇 iframe 跨域通讯全方案，收藏起来遇到嵌入需求直接查。你的 iframe 通讯用的什么方案？评论区交流。关注怕浪猫，下期讲跨端通讯机制总览。系列进度 7/10。

下一篇系统梳理 WebView Bridge、postMessage、BroadcastChannel、SharedWorker、WebRTC 五大跨端通讯方案。

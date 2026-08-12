# 第14章 同源策略与 CORS

> 同源策略是浏览器安全的基石。它很简单：不同源的页面不能读写彼此的数据。但围绕这个简单规则，CORS、CSP、Cookie 策略衍生出了大量细节。

我是怕浪猫，从这章开始进入浏览器安全机制。第 14 章拆解同源策略的精确定义、CORS（Cross-Origin Resource Sharing，跨域资源共享）的预检请求机制、以及 CSRF（Cross-Site Request Forgery，跨站请求伪造）的防护方案。

## 14.1 同源策略

### 14.1.1 什么是源（Origin）

源（Origin）由三部分组成：协议（Scheme）、主机（Host）和端口（Port）。如果两个 URL 的这三部分都相同，则它们是同源的。

```
同源判定示例

URL: https://example.com:443/page

对比：
  https://example.com/other        → 同源（端口 443 是 HTTPS 默认，省略）
  http://example.com/page          → 不同源（协议不同）
  https://example.com:8080/page    → 不同源（端口不同）
  https://api.example.com/page     → 不同源（主机不同）
  https://example.com:443/sub/dir  → 同源（路径不影响源）
```

| 对比 URL | 与 https://example.com/page 的关系 | 不同原因 |
|---------|----------------------------------|---------|
| https://example.com/other | 同源 | — |
| http://example.com/page | 不同源 | 协议不同 |
| https://example.com:8080/page | 不同源 | 端口不同 |
| https://api.example.com/page | 不同源 | 主机不同 |
| https://example.com:443/sub | 同源 | 路径不影响 |

### 14.1.2 同源策略的限制

同源策略对不同类型的资源有不同的限制规则。

| 资源类型 | 跨域读取 | 跨域写入 | 说明 |
|---------|---------|---------|------|
| DOM | 禁止 | 禁止 | 不同源 iframe 不能互相访问 DOM |
| Cookie/Storage | 禁止 | 部分 | 按域名规则，非完全同源 |
| XMLHttpRequest/Fetch | 禁止 | 允许发送 | 响应被拦截（除非 CORS） |
| 图片/CSS/JS | 允许加载 | — | 但不能读取内容 |
| WebRTC | 允许 | 允许 | 不受同源策略限制 |
| WebSocket | 允许 | 允许 | 不受同源策略限制 |

```
同源策略限制示意

页面: https://example.com/index.html

可以：
  ✓ 加载 https://api.example.com/image.jpg（<img>）
  ✓ 加载 https://api.example.com/style.css（<link>）
  ✓ 加载 https://api.example.com/script.js（<script>）
  ✓ 发送 WebSocket 到 wss://api.example.com/ws

不可以：
  ✗ fetch('https://api.example.com/data') 读取响应（无 CORS 头）
  ✗ 读取 <img> 加载的图片像素数据（跨域 canvas 污染）
  ✗ 访问 <iframe src="https://other.com"> 的 DOM
  ✗ 读取跨域 <script> 的源代码
```

### 14.1.3 跨域嵌入与跨域读取

同源策略允许跨域嵌入资源（加载），但不允许跨域读取资源内容。这个区别很重要。

```html
<!-- 可以跨域加载 -->
<img src="https://other.com/image.jpg">
<link rel="stylesheet" href="https://other.com/style.css">
<script src="https://other.com/script.js">
<iframe src="https://other.com/page.html">

<!-- 但不能读取内容 -->
<script>
  // 跨域图片不能读取像素
  const img = document.querySelector('img');
  const canvas = document.createElement('canvas');
  canvas.getContext('2d').drawImage(img, 0, 0);
  canvas.toDataURL();  // SecurityError!

  // 跨域 iframe 不能访问 DOM
  const frame = document.querySelector('iframe');
  frame.contentDocument;  // SecurityError!

  // 跨域 script 不能读取源码
  // （但可以执行，这是 JSONP 的基础）
</script>
```

> 跨域可以加载但不能读取，这个设计既保证了资源的可用性又保证了安全性。你可以用 `<img>` 加载任何图片，但不能用 canvas 读取跨域图片的像素。你可以用 `<script>` 加载跨域脚本并执行，但不能读取脚本内容。

## 14.2 CORS 跨域资源共享

### 14.2.1 简单请求

CORS 将跨域请求分为两类：简单请求（Simple Request）和非简单请求（需预检请求）。简单请求不需要预检，直接发送。

简单请求的条件：

| 条件 | 允许的值 |
|------|---------|
| 方法 | GET、HEAD、POST |
| Content-Type | text/plain、multipart/form-data、application/x-www-form-urlencoded |
| 自定义头 | 仅安全头（Accept、Accept-Language、Content-Language、Content-Type） |
| XMLHttpRequest.upload | 不注册事件监听器 |
| ReadableStream | 不使用 |

```javascript
// 简单请求（不需要预检）
fetch('https://api.example.com/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  },
  body: 'name=test'
});
```

### 14.2.2 预检请求（Preflight Request）

不满足简单请求条件的请求需要先发送预检请求。预检请求使用 OPTIONS 方法，询问服务器是否允许实际请求。

```javascript
// 非简单请求（需要预检）
fetch('https://api.example.com/data', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'X-Custom-Header': 'custom'
  },
  body: JSON.stringify({ name: 'test' })
});
```

```
预检请求流程

浏览器                              服务器
  │                                    │
  │  OPTIONS /data HTTP/1.1            │
  │  Origin: https://example.com       │
  │  Access-Control-Request-Method: PUT│
  │  Access-Control-Request-Headers:   │
  │    Content-Type, X-Custom-Header   │
  │ ─────────────────────────────────► │
  │                                    │
  │  HTTP/1.1 200 OK                   │
  │  Access-Control-Allow-Origin:      │
  │    https://example.com             │
  │  Access-Control-Allow-Methods:     │
  │    GET, POST, PUT, DELETE          │
  │  Access-Control-Allow-Headers:     │
  │    Content-Type, X-Custom-Header   │
  │  Access-Control-Max-Age: 86400     │
  │ ◄───────────────────────────────── │
  │                                    │
  │  PUT /data HTTP/1.1（实际请求）     │
  │  Origin: https://example.com       │
  │  Content-Type: application/json    │
  │  X-Custom-Header: custom           │
  │ ─────────────────────────────────► │
  │                                    │
  │  HTTP/1.1 200 OK（实际响应）        │
  │  Access-Control-Allow-Origin:      │
  │    https://example.com             │
  │ ◄───────────────────────────────── │
```

### 14.2.3 CORS 响应头

| 响应头 | 说明 | 示例 |
|--------|------|------|
| Access-Control-Allow-Origin | 允许的源 | https://example.com 或 * |
| Access-Control-Allow-Methods | 允许的方法 | GET, POST, PUT |
| Access-Control-Allow-Headers | 允许的请求头 | Content-Type, Authorization |
| Access-Control-Allow-Credentials | 允许携带 Cookie | true |
| Access-Control-Max-Age | 预检缓存时间 | 86400（秒） |
| Access-Control-Expose-Headers | 允许 JS 读取的响应头 | X-Total-Count |

### 14.2.4 凭证请求（Credentials）

默认情况下，跨域请求不携带 Cookie。如果需要携带 Cookie，需要设置 credentials 并在响应中允许。

```javascript
// 携带 Cookie 的跨域请求
fetch('https://api.example.com/data', {
  credentials: 'include'  // 携带 Cookie
});
```

```http
# 服务器响应必须包含
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Credentials: true

# 注意：Allow-Origin 不能是 *，必须是具体域名
```

| credentials 值 | 说明 | Cookie |
|---------------|------|--------|
| omit | 不携带 | 不发送 |
| same-origin | 同源时携带 | 跨域不发送 |
| include | 总是携带 | 跨域也发送 |

> 携带 Cookie 的跨域请求，服务器不能返回 `Access-Control-Allow-Origin: *`，必须返回具体的域名。这是为了防止恶意网站携带用户 Cookie 访问任意 API。

## 14.3 CSRF 防护

### 14.3.1 CSRF 攻击原理

CSRF（Cross-Site Request Forgery，跨站请求伪造）攻击利用浏览器自动携带 Cookie 的机制，在用户不知情的情况下发送请求。

```
CSRF 攻击流程

1. 用户登录 bank.com，浏览器保存 session Cookie
2. 用户访问 evil.com
3. evil.com 页面包含：
   <form action="https://bank.com/transfer" method="POST">
     <input name="to" value="attacker">
     <input name="amount" value="10000">
   </form>
   <script>document.forms[0].submit()</script>
4. 表单自动提交到 bank.com
5. 浏览器自动携带 bank.com 的 Cookie
6. bank.com 以为用户主动操作，执行转账
```

### 14.3.2 CSRF 防护方案

| 防护方案 | 原理 | 优缺点 |
|---------|------|--------|
| CSRF Token | 服务器生成随机 Token，表单必须携带 | 最常用，需后端配合 |
| SameSite Cookie | Cookie 只在同源请求中发送 | 简单有效，兼容性已解决 |
| Referer 检查 | 验证请求来源 | 不完全可靠 |
| Origin 头检查 | 验证 Origin 头 | 可靠但部分请求无 Origin |
| 双重 Cookie | Cookie 和请求体都携带同一值 | 简单，但 XSS 可绕过 |

```javascript
// CSRF Token 防护
// 服务器在表单中嵌入 Token
// <input type="hidden" name="csrf_token" value="random_token">

// 前端请求携带 Token
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': getCSRFToken()  // 从 meta 标签或 Cookie 读取
  },
  body: JSON.stringify(data)
});
```

```http
# SameSite Cookie 防护
Set-Cookie: session=abc123; SameSite=Lax; Secure; HttpOnly

# SameSite 值：
# Strict: 仅同源请求携带（最严格）
# Lax: 同源 + 顶级导航的 GET 请求携带（推荐）
# None: 总是携带（需配合 Secure）
```

> SameSite Cookie 是 CSRF 防护的未来。Chrome 从 80 版本开始默认 SameSite=Lax，大多数 CSRF 攻击已被默认阻止。但不要只依赖 SameSite，结合 CSRF Token 使用更安全。

## 14.4 跨域 Cookie 与 Set-Cookie

### 14.4.1 Cookie 的域名属性

Cookie 的域名属性决定了 Cookie 的发送范围。

```
Cookie 域名规则

Set-Cookie: name=value; Domain=example.com
→ 所有 *.example.com 子域名都会发送

Set-Cookie: name=value; Domain=api.example.com
→ 仅 api.example.com 及其子域名发送

Set-Cookie: name=value（不带 Domain）
→ 仅当前域名发送，不含子域名
```

| Domain 属性 | 发送范围 | 说明 |
|------------|---------|------|
| 不设置 | 仅当前域名 | 不含子域名 |
| example.com | *.example.com | 含所有子域名 |
| api.example.com | *.api.example.com | 含 api 的子域名 |

### 14.4.2 SameSite 属性详解

| SameSite 值 | 同源请求 | 顶级导航 GET | 顶级导航 POST | 跨域 fetch |
|------------|---------|-------------|--------------|-----------|
| Strict | 携带 | 不携带 | 不携带 | 不携带 |
| Lax | 携带 | 携带 | 不携带 | 不携带 |
| None | 携带 | 携带 | 携带 | 携带 |

### 14.4.3 第三方 Cookie 限制

Chrome 正在逐步淘汰第三方 Cookie。第三方 Cookie 是指在当前页面域名之外的域名设置的 Cookie。

```
第三方 Cookie 示例

页面: https://example.com
  ├─ <img src="https://ad.com/pixel"> → ad.com 设置/读取 Cookie → 第三方 Cookie
  ├─ <iframe src="https://embed.com/widget"> → embed.com Cookie → 第三方 Cookie
  └─ fetch('https://api.example.com/data') → example.com Cookie → 第一方 Cookie
```

| 替代方案 | 说明 | 状态 |
|---------|------|------|
| Federated Learning of Cohorts (FLoC) | 群组级广告兴趣 | 已放弃 |
| Topics API | 按主题展示广告 | 试点中 |
| Storage Access API | 跨站存储授权 | 已支持 |
| CHIPS | 分区 Cookie | 已支持 |

> 第三方 Cookie 的消亡是 Web 隐私的重要里程碑。但这不意味着跟踪的终结，各种替代方案正在涌现。作为开发者，需要评估自己的服务是否依赖第三方 Cookie，并提前迁移。

## 14.5 内容安全策略（CSP）

### 14.5.1 CSP 的作用

CSP（Content Security Policy，内容安全策略）是浏览器提供的额外安全层，通过白名单机制限制资源加载和代码执行，是防范 XSS（Cross-Site Scripting，跨站脚本攻击）的有效手段。

XSS 攻击的核心是攻击者向页面注入恶意脚本。CSP 通过限制脚本来源，即使攻击者成功注入了 `<script>` 标签，浏览器也不会执行非白名单来源的脚本。

```http
# 通过 HTTP 头设置 CSP
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self' 'unsafe-inline'; img-src *; connect-src 'self' https://api.example.com

# 或通过 meta 标签
<meta http-equiv="Content-Security-Policy" content="default-src 'self'">
```

### 14.5.2 CSP 指令

| 指令 | 控制资源 | 示例 |
|------|---------|------|
| default-src | 默认策略 | default-src 'self' |
| script-src | JavaScript | script-src 'self' cdn.example.com |
| style-src | CSS | style-src 'self' 'unsafe-inline' |
| img-src | 图片 | img-src * data: |
| connect-src | XHR/Fetch/WebSocket | connect-src 'self' api.example.com |
| font-src | 字体 | font-src 'self' fonts.googleapis.com |
| frame-src | iframe | frame-src 'none' |
| object-src | Flash/插件 | object-src 'none' |
| base-uri | <base> 标签 | base-uri 'self' |
| form-action | 表单提交目标 | form-action 'self' |
| frame-ancestors | 嵌入本页的祖先 | frame-ancestors 'none'（防点击劫持）|
| report-uri | 违规上报地址 | report-uri /csp-report |

### 14.5.3 nonce 和 hash

CSP 可以使用 nonce（Number Used Once，一次性随机数）或 hash 来允许特定的内联脚本。

```html
<!-- nonce 方式 -->
<script nonce="random123">
  console.log('allowed');
</script>

<!-- CSP 头 -->
Content-Security-Policy: script-src 'nonce-random123'

<!-- hash 方式 -->
<script>
  console.log('allowed');
</script>

<!-- CSP 头（SHA-256 hash of the script content） -->
Content-Security-Policy: script-src 'sha256-...'
```

### 14.5.4 CSP 的报告模式

CSP 支持 Report-Only 模式，只上报违规不阻止。这方便开发者逐步部署 CSP。

```http
# 报告模式（不阻止，只上报）
Content-Security-Policy-Report-Only: default-src 'self'; report-uri /csp-report

# 违规报告格式
{
  "csp-report": {
    "violated-directive": "script-src",
    "blocked-uri": "https://evil.com/script.js",
    "line-number": 42,
    "source-file": "https://example.com/page.html"
  }
}
```

> CSP 是 XSS 的最后一道防线。即使攻击者注入了 HTML，如果 CSP 配置正确，恶意脚本也无法执行。推荐使用 nonce 方式，每次请求生成新的随机数，比 hash 更灵活。先用 Report-Only 模式收集违规情况，修复后再切换为强制模式。

## 14.6 跨域通信方案

同源策略限制了跨域访问，但合法的跨域通信需求很常见。以下是几种合规的跨域通信方案。

| 方案 | 原理 | 适用场景 |
|------|------|---------|
| CORS | 服务器返回允许头 | API 调用 |
| postMessage | 窗口间消息传递 | iframe/弹窗通信 |
| WebSocket | 不受同源策略限制 | 实时通信 |
| JSONP | 利用 `<script>` 不受同源限制 | 旧系统兼容 |
| 代理服务器 | 同源代理转发 | 前端无法改 CORS 时 |

```javascript
// postMessage 跨域通信
// 父页面 (https://example.com)
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage({ type: 'resize', height: 500 }, 'https://embed.com');

// iframe 页面 (https://embed.com)
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://example.com') return;  // 验证来源
  console.log('收到消息:', e.data);
});
```

## 14.7 CORS 预检请求的缓存机制

### 14.7.1 预检缓存的工作方式

每次非简单请求都需要先发送 OPTIONS 预检请求，这会增加一个 RTT 的延迟。为了避免每次请求都预检，浏览器会缓存预检结果。

```
预检缓存流程

首次请求 PUT /api/data:
  1. 发送 OPTIONS 预检请求
     ├─ Access-Control-Request-Method: PUT
     └─ Access-Control-Request-Headers: Content-Type
  
  2. 服务器返回预检响应
     ├─ Access-Control-Allow-Methods: GET, POST, PUT, DELETE
     ├─ Access-Control-Allow-Headers: Content-Type, Authorization
     └─ Access-Control-Max-Age: 86400  ← 缓存 24 小时
  
  3. 发送实际 PUT 请求

后续请求 (24小时内):
  直接发送 PUT 请求
  → 跳过预检!
  → 节省 1 RTT

24小时后:
  预检缓存过期
  → 下次请求重新预检
```

Access-Control-Max-Age 的值由服务器控制，但浏览器有自己的上限：Chrome 最大缓存 2 小时（7200 秒），Firefox 最大 24 小时（86400 秒），即使服务器返回更大的值也会被截断。

### 14.7.2 CORS 与 CDN 的配合

在使用 CDN 时，CORS 配置需要特别注意。CDN 的边缘节点会缓存资源响应，如果 CORS 头没有被正确缓存，可能导致跨域请求失败。

```
CDN 场景下的 CORS 配置

场景1: 字体文件跨域加载
  页面: https://app.example.com
  字体: https://cdn.example.com/font.woff2
  
  CDN 需要返回:
    Access-Control-Allow-Origin: https://app.example.com
    Cache-Control: public, max-age=31536000
  
  问题: 如果 CDN 返回 Access-Control-Allow-Origin: *
  → 可以跨域加载，但无法携带 Cookie
  
  问题: 如果 CDN 按请求 Origin 返回具体域名
  → CDN 缓存键必须包含 Origin
  → 否则缓存了 A 域名的响应，B 域名收到 A 的 Origin

最佳实践:
  ├─ 对公开资源: Allow-Origin: *
  ├─ 对私有资源: 动态返回具体 Origin + Vary: Origin
  └─ CDN 缓存键包含 Origin (Vary: Origin)
```

### 14.7.3 CORS 代理方案

当后端 API 不支持 CORS 时，前端可以使用代理方案绕过同源策略。代理方案的原理是：浏览器请求同源的代理服务器，代理服务器转发请求到目标 API。

```
CORS 代理方案

浏览器                    代理服务器                 API 服务器
https://app.com           https://app.com/proxy      https://api.com
  │                          │                          │
  │  GET /proxy/api/data     │                          │
  │ ──────────────────────►│                          │
  │  (同源请求,无 CORS 问题)  │  GET /api/data            │
  │                          │ ──────────────────────►│
  │                          │  (服务器间,无 CORS 限制)   │
  │                          │  ◄──────────────────────│
  │  ◄──────────────────────│  API 响应                 │
  │  代理返回数据             │                          │

开发环境:
  ├─ Webpack DevServer: proxy 配置
  ├─ Vite: server.proxy 配置
  └─ create-react-app: 在 package.json 中配置 proxy

生产环境:
  ├─ Nginx 反向代理
  ├─ API Gateway
  └─ 服务端 BFF (Backend for Frontend)
```

### 14.7.4 CORS 调试技巧

CORS 错误信息可能不够直观，以下是一些调试技巧。

```
CORS 调试检查清单

错误: "No 'Access-Control-Allow-Origin' header"
  ├─ 检查1: 服务器是否返回了 CORS 头?
  │   curl -I -X OPTIONS https://api.com/data
  │   -H "Origin: https://app.com"
  │   -H "Access-Control-Request-Method: PUT"
  ├─ 检查2: Origin 是否匹配?
  │   服务器返回的 Allow-Origin 必须精确匹配请求的 Origin
  ├─ 检查3: 是否是 HTTPS vs HTTP 不匹配?
  └─ 检查4: 端口是否匹配?

错误: "CORS preflight channel failed"
  ├─ 检查: OPTIONS 请求是否被服务器正确处理?
  ├─ 检查: 服务器是否返回了 2xx 状态码?
  └─ 检查: Allow-Methods 是否包含请求方法?

错误: "Credentialed requests require specific Allow-Origin"
  ├─ 检查: credentials: 'include' 时
  │   Allow-Origin 不能是 *
  │   必须是具体域名
  └─ 检查: Allow-Credentials: true 是否设置?
```

### 14.7.5 跨域 WebSocket 不受同源策略限制的原因

WebSocket 不受同源策略限制，这看起来像是安全漏洞，但实际上有合理的设计原因。

```
WebSocket 跨域连接流程

浏览器                    WebSocket 服务器
  │                          │
  │  HTTP Upgrade 请求        │
  │  GET /ws HTTP/1.1         │
  │  Upgrade: websocket       │
  │  Origin: https://app.com  │
  │ ────────────────────────►│
  │                          │
  │  服务器检查 Origin        │
  │  ├─ 允许 → 升级连接       │
  │  └─ 拒绝 → 返回 403       │
  │ ◄────────────────────────│
  │                          │
  │  WebSocket 连接建立        │
  │  (双向通信,不受同源限制)   │
```

WebSocket 不受同源策略限制的原因：WebSocket 在握手阶段使用 HTTP Upgrade 请求，但升级后不再是 HTTP 协议。同源策略是 HTTP 协议层面的限制，不适用于 WebSocket 协议。WebSocket 通过 Origin 头让服务器自行决定是否接受跨域连接——安全责任从浏览器转移到了服务器。

### 14.7.6 Service Worker 中的 CORS 处理

Service Worker 拦截网络请求，它对 CORS 的处理与浏览器原生不同。

```javascript
// Service Worker 中的 CORS 处理
self.addEventListener('fetch', (event) => {
  // Service Worker 可以拦截跨域请求
  // 但返回的 Response 必须符合 CORS 规则
  
  event.respondWith(
    fetch(event.request).then(response => {
      // 如果是跨域请求，Response 必须有 CORS 头
      // 否则浏览器会阻止 JavaScript 读取响应
      
      // Service Worker 可以修改响应头
      const newResponse = new Response(response.body, {
        headers: {
          'Access-Control-Allow-Origin': '*',  // 添加 CORS 头
          'Content-Type': 'application/json'
        }
      });
      return newResponse;
    })
  );
});

// 注意: Service Worker 中的 fetch() 不受同源策略限制
// 但返回给页面的 Response 必须符合 CORS 规则
```

Service Worker 中的 fetch 请求不受同源策略限制（可以发送任何跨域请求），但 Service Worker 返回给页面的 Response 必须包含正确的 CORS 头，否则页面 JavaScript 无法读取响应。这意味着 Service Worker 可以充当 CORS 代理，但开发者需要确保这样做不会引入安全风险。

| 场景 | 同源策略 | CORS 头 |
|------|---------|--------|
| 页面 fetch | 受限 | 需要 |
| Service Worker fetch | 不受限 | 不需要 |
| Service Worker → 页面 | 不适用 | 需要 |

## 本章核心知识总结

| 知识模块 | 核心内容 | 安全意义 |
|---------|---------|---------|
| 同源策略 | 协议+主机+端口三要素 | 浏览器安全基石 |
| CORS | 服务器白名单允许跨域 | 合法跨域访问 |
| CSRF | 利用 Cookie 自动发送 | Token + SameSite 防护 |
| Cookie 策略 | SameSite/Secure/HttpOnly | Cookie 安全 |
| CSP | 资源加载白名单 | XSS 防线 |
| 跨域通信 | CORS/postMessage/WebSocket | 合法跨域方案 |

觉得有用？收藏起来，下次配置 CORS 或排查跨域问题时直接翻出来看。

你在项目中遇到过跨域问题吗？是怎么解决的？评论区聊聊。

关注怕浪猫，下期我们讲浏览器沙箱与隔离机制。系列进度 14/24。

下期预告：第 15 章「浏览器沙箱与站点隔离」。我们会拆解 Chrome 的多进程沙箱架构、站点隔离（Site Isolation）的实现原理、以及 Spectre/Meltdown 漏洞如何改变了浏览器安全设计。怕浪猫下期见。

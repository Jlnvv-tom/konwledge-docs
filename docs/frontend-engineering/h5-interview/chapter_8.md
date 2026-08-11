---
sidebar_position: 8
---

# 第8章：跨端通讯机制总览

前端通讯方案有10种以上，90%的人只用了3种。这篇系统梳理所有跨端通讯机制的原理和选型。我是怕浪猫，一个在跨端通讯领域踩遍各种坑的前端工程师。

## 8.1 跨端通讯方案全景图

### 方案分类

```
跨端通讯
├── 同浏览器内
│   ├── postMessage（窗口/iframe 间）
│   ├── BroadcastChannel（同源多标签）
│   ├── SharedWorker（共享工作线程）
│   ├── storage 事件（LocalStorage 同步）
│   └── CustomEvent（同文档内）
├── 浏览器与 Native
│   ├── JS Bridge（WebView <-> App）
│   ├── URL Scheme 拦截
│   └── Universal Link / App Link
├── 浏览器与服务端
│   ├── HTTP 轮询
│   ├── WebSocket
│   ├── SSE（Server-Sent Events）
│   └── WebRTC（P2P 数据通道）
└── 跨设备
    ├── WebRTC P2P
    └── 信令服务器中转
```

### 选型决策

| 场景 | 推荐方案 | 备选 |
|------|----------|------|
| 同源多标签通讯 | BroadcastChannel | storage 事件 |
| 跨域 iframe 通讯 | postMessage | MessageChannel |
| WebView <-> App | JS Bridge | URL Scheme |
| 服务端实时推送 | SSE | WebSocket |
| 双向实时通讯 | WebSocket | WebRTC |
| 大数据计算 | Web Worker | SharedWorker |
| P2P 文件传输 | WebRTC | - |

> 没有最好的通讯方案，只有最适合场景的。选型时考虑：通讯方向、数据量、实时性、跨域需求。

## 8.2 postMessage 通讯模式详解

### 窗口间通讯

```javascript
// 父窗口 -> iframe
const iframe = document.querySelector('iframe');
iframe.contentWindow.postMessage(
  { type: 'command', action: 'scroll', position: 100 },
  'https://child.example.com'
);

// iframe -> 父窗口
window.parent.postMessage(
  { type: 'response', status: 'ok' },
  'https://parent.example.com'
);

// 接收方
window.addEventListener('message', (e) => {
  // 安全校验三步走
  if (e.origin !== 'https://expected.example.com') return;
  if (!e.data || typeof e.data.type !== 'string') return;
  if (e.source !== expectedWindow) return;

  handleMessage(e.data);
});
```

### window.open 场景

```javascript
// 父窗口打开子窗口
const child = window.open('https://child.example.com', '_blank');

// 父 -> 子
child.postMessage({ type: 'init' }, 'https://child.example.com');

// 子 -> 父
window.opener.postMessage({ type: 'ready' }, 'https://parent.example.com');
```

### MessageChannel 建立专用通道

```javascript
// 建立通道
const channel = new MessageChannel();

// 发送一端给对方
iframe.contentWindow.postMessage(
  { type: 'handshake' },
  'https://child.example.com',
  [channel.port2]
);

// 本端使用 port1
channel.port1.onmessage = (e) => {
  console.log('收到:', e.data);
};

// 对方收到 port2 后直接使用
window.addEventListener('message', (e) => {
  if (e.data.type === 'handshake') {
    const port = e.ports[0];
    port.onmessage = (ev) => {
      console.log('收到:', ev.data);
    };
    port.postMessage({ type: 'ready' });
  }
});
```

| 对比项 | postMessage | MessageChannel |
|--------|------------|----------------|
| 通讯模型 | 广播式 | 点对点 |
| 安全校验 | 每次校验 origin | 建立时校验一次 |
| 性能 | 中 | 高（无序列化广播） |
| 复杂度 | 低 | 中 |

> postMessage 适合简单场景，MessageChannel 适合高频通讯——建立一次通道，后续直接用。

参考来源：[MDN - postMessage](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/postMessage)、[MDN - MessageChannel](https://developer.mozilla.org/zh-CN/docs/Web/API/MessageChannel)

## 8.3 BroadcastChannel API

### 基本用法

```javascript
// 创建频道（同源的所有标签页/iframe 都可以加入）
const channel = new BroadcastChannel('app_sync');

// 发送消息
channel.postMessage({ type: 'logout', timestamp: Date.now() });

// 接收消息
channel.onmessage = (e) => {
  console.log('收到:', e.data);
  if (e.data.type === 'logout') {
    redirectToLogin();
  }
};

// 关闭频道
channel.close();
```

### 典型场景：多标签登录态同步

```javascript
// 标签A：登录成功
function onLoginSuccess(token) {
  localStorage.setItem('token', token);
  // 通知其他标签
  channel.postMessage({ type: 'login', token });
}

// 其他标签：收到登录通知
channel.onmessage = (e) => {
  if (e.data.type === 'login') {
    updateUserUI(e.data.token);
  } else if (e.data.type === 'logout') {
    clearUserData();
    redirectToLogin();
  }
};

// 标签B：登出
function onLogout() {
  localStorage.removeItem('token');
  channel.postMessage({ type: 'logout' });
}
```

### BroadcastChannel vs storage 事件

| 对比项 | BroadcastChannel | storage 事件 |
|--------|-----------------|-------------|
| 数据类型 | 任意结构化对象 | 仅字符串 |
| 触发范围 | 同源所有上下文 | 同源其他标签 |
| 自身触发 | 不触发自身 | 不触发自身 |
| 浏览器支持 | Safari 15.4+ | 全部 |
| 性能 | 好 | 好 |

> BroadcastChannel 是多标签通讯的首选方案，不支持时降级为 storage 事件。

参考来源：[MDN - BroadcastChannel](https://developer.mozilla.org/zh-CN/docs/Web/API/BroadcastChannel)

## 8.4 SharedWorker 共享工作线程

### 与普通 Worker 的区别

| 特性 | Worker | SharedWorker |
|------|--------|-------------|
| 实例数 | 每个页面一个 | 多页面共享一个 |
| 通讯方式 | postMessage | MessagePort |
| 适用场景 | 单页计算 | 跨页共享状态 |
| 浏览器支持 | 全部 | 除 Safari iOS 外 |

### 基本用法

```javascript
// 主线程：连接 SharedWorker
const worker = new SharedWorker('shared-worker.js');

// 通过 port 通讯
worker.port.onmessage = (e) => {
  console.log('收到:', e.data);
};

worker.port.postMessage({ type: 'subscribe', channel: 'updates' });

// shared-worker.js
const connections = [];

self.onconnect = (e) => {
  const port = e.ports[0];
  connections.push(port);

  port.onmessage = (ev) => {
    // 广播给所有连接
    connections.forEach(p => {
      p.postMessage({ type: 'broadcast', data: ev.data });
    });
  };

  port.postMessage({ type: 'connected', count: connections.length });
};
```

### 典型场景：跨标签共享 WebSocket

```javascript
// shared-worker.js：维护单个 WebSocket 连接，所有标签共享
let ws = null;
let connections = [];

self.onconnect = (e) => {
  const port = e.ports[0];
  connections.push(port);

  if (!ws) {
    ws = new WebSocket('wss://api.example.com/ws');
    ws.onmessage = (event) => {
      // 广播给所有连接的标签
      connections.forEach(p => p.postMessage({ type: 'ws-message', data: event.data }));
    };
    ws.onclose = () => {
      connections.forEach(p => p.postMessage({ type: 'ws-close' }));
      ws = null;
    };
  }

  port.onmessage = (ev) => {
    if (ev.data.type === 'send') {
      ws.send(JSON.stringify(ev.data.payload));
    } else if (ev.data.type === 'disconnect') {
      connections = connections.filter(p => p !== port);
      if (connections.length === 0 && ws) {
        ws.close();
        ws = null;
      }
    }
  };
};
```

> SharedWorker 的核心价值是"资源共享"——一个 WebSocket 连接服务所有标签页，省连接、省内存。

参考来源：[MDN - SharedWorker](https://developer.mozilla.org/zh-CN/docs/Web/API/SharedWorker)

## 8.5 WebSocket 实战：心跳重连与消息队列

### 完整实现

```javascript
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      heartbeatInterval: 30000,
      reconnectInterval: 1000,
      maxReconnectInterval: 30000,
      ...options
    };

    this.ws = null;
    this.reconnectCount = 0;
    this.heartbeatTimer = null;
    this.reconnectTimer = null;
    this.messageQueue = [];  // 待发送消息队列
    this.isManualClose = false;

    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket 连接成功');
      this.reconnectCount = 0;
      this.startHeartbeat();
      this.flushQueue();  // 发送队列中的消息
    };

    this.ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'pong') return;  // 心跳响应
      this.onMessage && this.onMessage(data);
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.isManualClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error);
    };
  }

  // 心跳
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping' });
    }, this.options.heartbeatInterval);
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // 重连（指数退避）
  scheduleReconnect() {
    const delay = Math.min(
      this.options.reconnectInterval * Math.pow(2, this.reconnectCount),
      this.options.maxReconnectInterval
    );
    console.log(`${delay}ms 后重连...`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectCount++;
      this.connect();
    }, delay);
  }

  // 发送消息（连接断开时入队）
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.messageQueue.push(data);
    }
  }

  // 刷新消息队列
  flushQueue() {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift();
      this.send(msg);
    }
  }

  // 主动关闭
  close() {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws.close();
  }
}

// 使用
const ws = new ReconnectingWebSocket('wss://api.example.com/ws');
ws.onMessage = (data) => {
  console.log('收到消息:', data);
};
ws.send({ type: 'message', content: '你好' });
```

> WebSocket 断线重连的三个关键：心跳保活、指数退避重连、消息队列不丢数据。

参考来源：[MDN - WebSocket](https://developer.mozilla.org/zh-CN/docs/Web/API/WebSocket)

## 8.6 SSE（Server-Sent Events）的使用场景

### 服务端实现

```javascript
// Node.js SSE 服务端
app.get('/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // 发送消息
  const sendEvent = (data) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  sendEvent({ type: 'connected', time: Date.now() });

  // 定时推送
  const timer = setInterval(() => {
    sendEvent({ type: 'heartbeat', time: Date.now() });
  }, 30000);

  // 清理
  req.on('close', () => {
    clearInterval(timer);
  });
});
```

### 前端实现

```javascript
// 自动重连的 SSE
const source = new EventSource('/events');

source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('收到推送:', data);
};

source.addEventListener('notification', (e) => {
  const data = JSON.parse(e.data);
  showNotification(data);
});

source.onerror = () => {
  console.log('连接断开，浏览器自动重连');
  // EventSource 内置自动重连，无需手动处理
};

// 主动关闭
// source.close();
```

### SSE vs WebSocket 选型

| 维度 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 服务端 -> 客户端 | 双向 |
| 协议 | HTTP | WS |
| 自动重连 | 内置 | 需手动实现 |
| 数据格式 | 文本 | 文本 + 二进制 |
| 连接数限制 | 浏览器同域 6 个 | 无限制 |
| 代理穿透 | 好（HTTP） | 差（需升级） |
| 适用场景 | 通知、行情、日志 | IM、游戏、协同 |

> 只需服务端推送选 SSE，需要双向通讯选 WebSocket。别用 WebSocket 做只有推送的场景，SSE 省心得多。

参考来源：[MDN - Server-Sent Events](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events)

## 8.7 WebRTC 数据通道与 P2P 通讯

### 基本概念

WebRTC（Web Real-Time Communication，Web 实时通讯）支持浏览器间 P2P（Peer-to-Peer，点对点）通讯，无需服务器中转数据。

```
浏览器A <--信令服务器--> 浏览器B（交换 SDP/ICE）
浏览器A <===P2P 数据通道===> 浏览器B
```

### 数据通道建立

```javascript
// 创建 RTCPeerConnection
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ]
});

// 创建数据通道
const channel = pc.createDataChannel('chat', {
  ordered: true  // 保证顺序
});

channel.onopen = () => {
  console.log('数据通道已打开');
  channel.send('你好，怕浪猫');
};

channel.onmessage = (e) => {
  console.log('收到:', e.data);
};

// 接收方
pc.ondatachannel = (e) => {
  const receiveChannel = e.channel;
  receiveChannel.onmessage = (ev) => {
    console.log('收到:', ev.data);
  };
  receiveChannel.onopen = () => {
    receiveChannel.send('收到你的消息');
  };
};

// 交换 SDP（通过信令服务器）
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);
// 通过 WebSocket 发送 offer 给对方
signalingServer.send({ type: 'offer', data: offer });

// 接收对方的 answer
signalingServer.onmessage = async (e) => {
  if (e.data.type === 'offer') {
    await pc.setRemoteDescription(e.data.data);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    signalingServer.send({ type: 'answer', data: answer });
  } else if (e.data.type === 'answer') {
    await pc.setRemoteDescription(e.data.data);
  } else if (e.data.type === 'ice') {
    await pc.addIceCandidate(e.data.data);
  }
};

// ICE 候选
pc.onicecandidate = (e) => {
  if (e.candidate) {
    signalingServer.send({ type: 'ice', data: e.candidate });
  }
};
```

| 特性 | WebSocket | WebRTC DataChannel |
|------|-----------|-------------------|
| 传输路径 | 经服务器 | P2P 直连 |
| 延迟 | 中（服务器中转） | 低（直连） |
| 服务器负担 | 高 | 低（仅信令） |
| NAT 穿透 | 不需要 | 需要 STUN/TURN |
| 适用场景 | IM、通知 | 文件传输、游戏、低延迟场景 |

> WebRTC 的核心优势是"数据不经服务器"，适合大文件传输和低延迟游戏。

参考来源：[MDN - WebRTC API](https://developer.mozilla.org/zh-CN/docs/Web/API/WebRTC_API)

## 8.8navigator.sendBeacon 与页面卸载数据上报

### 问题背景

页面卸载（unload/beforeunload）时，传统的 XMLHttpRequest 或 fetch 可能被浏览器取消，导致数据丢失。

### sendBeacon 方案

```javascript
// 页面卸载时上报数据（浏览器保证发送）
window.addEventListener('pagehide', () => {
  const data = {
    page: location.pathname,
    duration: performance.now(),
    timestamp: Date.now()
  };
  navigator.sendBeacon('/api/analytics', JSON.stringify(data));
});

// sendBeacon 特点：
// - 浏览器保证在页面卸载后发送
// - 不阻塞页面卸载
// - 支持POST请求
// - 数据量限制：64KB
```

### 对比方案

| 方案 | 卸载时可靠性 | 阻塞卸载 | 数据量 |
|------|------------|----------|--------|
| XMLHttpRequest | 低（可能被取消） | 是 | 无限制 |
| fetch keepalive | 中 | 否 | 无限制 |
| sendBeacon | 高 | 否 | 64KB |
| img beacon | 中 | 否 | URL长度限制 |

```javascript
// fetch keepalive（sendBeacon 的替代）
fetch('/api/analytics', {
  method: 'POST',
  body: JSON.stringify(data),
  keepalive: true  // 允许在页面卸载后继续发送
}).catch(() => {});

// img beacon（兼容性最好的方案）
new Image().src = `/api/track?data=${encodeURIComponent(JSON.stringify(data))}`;
```

> 埋点上报用 sendBeacon 最可靠，大数据量用 fetch keepalive，老项目兼容用 img beacon。

参考来源：[MDN - sendBeacon](https://developer.mozilla.org/zh-CN/docs/Web/API/Navigator/sendBeacon)

## 8.9 跨域通讯方案选型决策树

### 完整决策树

```
需要跨端通讯？
  |
  ├── 同浏览器内？
  |     ├── 同源多标签？-> BroadcastChannel（降级 storage 事件）
  |     ├── 跨域 iframe？-> postMessage / MessageChannel
  |     ├── 共享计算/状态？-> SharedWorker
  |     └── 单页计算？-> Web Worker
  |
  ├── 浏览器 <-> Native？
  |     ├── WebView 内？-> JS Bridge
  |     └── 跳转 App？-> Universal Link / URL Scheme
  |
  └── 浏览器 <-> 服务端？
        ├── 仅推送？-> SSE
        ├── 双向？-> WebSocket
        ├── P2P？-> WebRTC
        └── 卸载上报？-> sendBeacon
```

### 选型矩阵

| 方案 | 方向 | 实时性 | 跨域 | 复杂度 | 典型场景 |
|------|------|--------|------|--------|----------|
| postMessage | 双向 | 高 | 支持 | 低 | iframe通讯 |
| BroadcastChannel | 广播 | 高 | 同源 | 低 | 多标签同步 |
| SharedWorker | 双向 | 高 | 同源 | 中 | 共享WebSocket |
| WebSocket | 双向 | 高 | 需CORS | 中 | IM/游戏 |
| SSE | 单向 | 高 | 需CORS | 低 | 通知/行情 |
| WebRTC | P2P | 高 | - | 高 | 文件传输 |
| sendBeacon | 单向 | - | 需CORS | 低 | 埋点上报 |
| JS Bridge | 双向 | 高 | - | 中 | Hybrid |

> 选型不是选"最好"的，是选"刚好够用"的——能用 SSE 就别上 WebSocket，能用 postMessage 就别上 SharedWorker。

## 8.10 跨端通讯的安全最佳实践

### 安全清单

| 风险 | 防护措施 |
|------|----------|
| postMessage 伪造 | 校验 origin 和 source |
| WebSocket 劫持 | 使用 wss:// + Token 认证 |
| XSS 注入 | 不 eval 消息内容，CSP 策略 |
| CSRF 攻击 | Token 验证 + SameSite Cookie |
| 数据窃听 | HTTPS/WSS + 端到端加密 |
| 连接劫持 | ICE 候选验证 + DTLS 加密 |

### postMessage 安全封装

```javascript
// 安全的 postMessage 封装
class SecureChannel {
  constructor(targetWindow, allowedOrigin) {
    this.target = targetWindow;
    this.origin = allowedOrigin;
    this.handlers = new Map();
    this._setupListener();
  }

  send(type, data) {
    this.target.postMessage({ type, data, nonce: crypto.randomUUID() }, this.origin);
  }

  on(type, handler) {
    this.handlers.set(type, handler);
  }

  _setupListener() {
    window.addEventListener('message', (e) => {
      // 三重校验
      if (e.origin !== this.origin) return;
      if (e.source !== this.target) return;
      if (!e.data || typeof e.data.type !== 'string') return;

      const handler = this.handlers.get(e.data.type);
      if (handler) {
        handler(e.data.data);
      }
    });
  }
}

// 使用
const channel = new SecureChannel(iframe.contentWindow, 'https://child.example.com');
channel.send('init', { userId: 123 });
channel.on('ready', (data) => console.log('子页面就绪:', data));
```

> 跨端通讯安全的本质是"不信任任何来源"——校验、校验、再校验。

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| 跨端通讯全景图 | 体系认知 | 高 |
| postMessage/MessageChannel | 跨域通讯 | 高 |
| BroadcastChannel | 多标签同步 | 中高 |
| SharedWorker | 共享工作线程 | 中 |
| WebSocket 心跳重连 | 实时通讯工程化 | 高 |
| SSE 使用场景 | 推送方案选型 | 中高 |
| WebRTC P2P | 点对点通讯 | 中 |
| sendBeacon | 数据上报 | 中 |
| 选型决策树 | 架构决策能力 | 高 |
| 安全最佳实践 | 安全意识 | 中高 |

这篇跨端通讯总览，收藏起来做技术选型时直接查。你的项目用了哪几种通讯方案？评论区交流。关注怕浪猫，下期讲微前端架构。系列进度 8/10。

下一篇拆解 qiankun、Module Federation、Proxy 沙箱、CSS 隔离、微前端通讯机制。

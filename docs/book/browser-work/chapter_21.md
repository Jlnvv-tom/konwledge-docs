# 第21章 Chrome 扩展开发（MV3）

> Manifest V3 是 Chrome 扩展的重大架构变革。后台页面变成了 Service Worker，Web Request 拦截变成了 DeclarativeNetRequest。这不是改版，是重写。

我是怕浪猫，上期讲了加载性能优化，今天进入第 21 章：Chrome 扩展开发（MV3）。这一章拆解 Manifest V3 的架构变化、Service Worker 在扩展中的生命周期、Content Script 通信机制、以及 CDP（Chrome DevTools Protocol，Chrome 开发者工具协议）。

## 21.1 Manifest V3 架构

### 21.1.1 MV2 vs MV3 对比

| 特性 | Manifest V2 | Manifest V3 |
|------|------------|------------|
| 后台 | Background Page（持久） | Service Worker（非持久） |
| 网络拦截 | webRequest（阻塞式） | declarativeNetRequest（声明式） |
| 远程代码 | 允许 eval/远程脚本 | 禁止（CSP 严格） |
| Host 权限 | permissions 字段 | host_permissions 字段 |
| Promise | 回调为主 | 原生 Promise |

### 21.1.2 manifest.json 结构

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  
  "content_scripts": [{
    "matches": ["https://example.com/*"],
    "js": ["content.js"],
    "css": ["content.css"]
  }],
  
  "action": {
    "default_popup": "popup.html",
    "default_icon": "icon.png"
  },
  
  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": ["https://*/*"],
  
  "declarative_net_request": {
    "rule_resources": [{
      "id": "ruleset_1",
      "enabled": true,
      "path": "rules.json"
    }]
  }
}
```

## 21.2 Service Worker 生命周期

### 21.2.1 非持久的后台

MV3 的 Service Worker 是非持久的：空闲约 30 秒后会被终止，有事件时重新启动。

```
MV3 Service Worker 生命周期

启动 → 处理事件 → 空闲 → 终止 → 等待事件 → 启动

关键影响：
  1. 全局变量不持久（终止后丢失）
  2. 定时器会被终止（setInterval 不可靠）
  3. 异步操作可能被中断
  4. 需要状态持久化到 chrome.storage
```

| MV2 Background Page | MV3 Service Worker |
|---------------------|-------------------|
| 持久运行 | 30 秒空闲后终止 |
| 全局变量持久 | 全局变量丢失 |
| setInterval 可靠 | setInterval 不可靠 |
| DOM API 可用 | DOM API 不可用 |

### 21.2.2 状态持久化

```javascript
// background.js (Service Worker)

// 错误：全局变量不持久
let counter = 0;
chrome.action.onClicked.addListener(() => {
  counter++;  // SW 重启后 counter 重置为 0
});

// 正确：使用 chrome.storage
chrome.action.onClicked.addListener(async () => {
  const { counter = 0 } = await chrome.storage.local.get('counter');
  await chrome.storage.local.set({ counter: counter + 1 });
});

// 正确：使用 chrome.alarms 替代 setInterval
chrome.alarms.create('periodic', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'periodic') {
    doPeriodicWork();
  }
});
```

> MV3 的 Service Worker 非持久性是迁移最大的痛点。所有依赖全局变量和定时器的逻辑都需要重写。使用 chrome.storage 持久化状态，使用 chrome.alarms 替代定时器。这是 MV3 的设计哲学：事件驱动、无状态。

## 21.3 Content Script 通信

### 21.3.1 通信机制

```
扩展通信架构

Content Script（页面上下文）
  ↕ chrome.runtime.sendMessage / onMessage
Service Worker（扩展后台）
  ↕ chrome.tabs.sendMessage / onMessage
Content Script

Content Script ↔ 页面 JS
  通过 window.postMessage 通信
  （Content Script 和页面 JS 隔离）
```

```javascript
// Content Script → Service Worker
chrome.runtime.sendMessage({ type: 'GET_DATA' }, (response) => {
  console.log('收到:', response);
});

// Service Worker → Content Script
chrome.tabs.sendMessage(tabId, { type: 'UPDATE' }, (response) => {
  console.log('Content Script 回复:', response);
});

// Service Worker 监听
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_DATA') {
    getData().then(data => sendResponse(data));
    return true;  // 保持消息通道开放（异步响应）
  }
});
```

### 21.3.2 长连接

```javascript
// Content Script 建立长连接
const port = chrome.runtime.connect({ name: 'content' });
port.postMessage({ type: 'START' });
port.onMessage.addListener((msg) => {
  console.log('收到:', msg);
});

// Service Worker 监听长连接
chrome.runtime.onConnect.addListener((port) => {
  port.onMessage.addListener((msg) => {
    if (msg.type === 'START') {
      port.postMessage({ type: 'STARTED' });
    }
  });
});
```

| 通信方式 | 方向 | 特点 | 适用场景 |
|---------|------|------|---------|
| sendMessage | 双向 | 一次性 | 简单请求 |
| connect | 双向 | 持久连接 | 流式数据 |
| postMessage | CS ↔ Page | 跨上下文 | 页面注入 |

## 21.4 declarativeNetRequest

### 21.4.1 声明式网络请求规则

MV3 用 declarativeNetRequest 替代了 webRequest 的阻塞式拦截。规则以 JSON 声明，浏览器在网络层处理，不需要唤醒 Service Worker。

```json
// rules.json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||ads.example.com^",
      "resourceTypes": ["script", "image", "xmlhttprequest"]
    }
  },
  {
    "id": 2,
    "priority": 1,
    "action": {
      "type": "redirect",
      "redirect": { "url": "https://example.com/blocked.html" }
    },
    "condition": {
      "urlFilter": "||tracker.com^",
      "resourceTypes": ["main_frame"]
    }
  }
]
```

| 对比 | webRequest（MV2） | declarativeNetRequest（MV3） |
|------|-------------------|---------------------------|
| 拦截方式 | 阻塞式 | 声明式 |
| 性能 | 慢（需唤醒 SW） | 快（网络层处理） |
| 灵活性 | 高 | 受限 |
| 隐私 | 可见请求内容 | 不可见 |

> declarativeNetRequest 的设计目标是性能和隐私。MV2 的 webRequest 需要唤醒 Service Worker 来处理每个请求，性能开销大。declarativeNetRequest 在浏览器网络层直接处理，不需要 SW 参与。代价是灵活性降低——不能动态修改请求内容。

## 21.5 Chrome DevTools Protocol（CDP）

### 21.5.1 CDP 是什么

CDP（Chrome DevTools Protocol，Chrome 开发者工具协议）是 Chrome DevTools 背后的协议。Puppeteer 和 Playwright 都基于 CDP 实现浏览器自动化。

| CDP 域 | 功能 | 常用方法 |
|--------|------|---------|
| Page | 页面导航 | navigate, reload, captureScreenshot |
| DOM | DOM 操作 | getDocument, querySelector |
| Runtime | JavaScript 执行 | evaluate, callFunctionOn |
| Network | 网络监控 | enable, getResponseBody |
| Performance | 性能 | getMetrics, startScreencast |
| Target | 标签页管理 | createTarget, closeTarget |

### 21.5.2 Puppeteer 基础

```javascript
const puppeteer = require('puppeteer');

const browser = await puppeteer.launch();
const page = await browser.newPage();

// 导航
await page.goto('https://example.com');

// 执行 JS
const title = await page.evaluate(() => document.title);

// 截图
await page.screenshot({ path: 'screenshot.png' });

// 网络拦截
await page.setRequestInterception(true);
page.on('request', (req) => {
  if (req.resourceType() === 'image') {
    req.abort();
  } else {
    req.continue();
  }
});

// 性能指标
const metrics = await page.metrics();
console.log('JS Heap Size:', metrics.usedJSHeapSize);

await browser.close();
```

## 21.6 MV2 to MV3 迁移指南

### 21.6.1 迁移评估

MV2 扩展迁移到 MV3 不是简单的配置修改，而是架构层面的重构。在动手之前，需要全面评估扩展的现有架构。

```
迁移评估检查清单

1. 后台架构
   ├─ 使用 Background Page（持久后台）？
   │   → 需要重写为 Service Worker
   ├─ 使用持久全局变量？
   │   → 需要迁移到 chrome.storage
   └─ 使用 setInterval 定时器？
       → 需要迁移到 chrome.alarms

2. 网络拦截
   ├─ 使用 webRequest 阻塞式拦截？
   │   → 需要迁移到 declarativeNetRequest
   ├─ 动态修改请求头？
   │   → 需要用 declarativeNetRequest 的 modifyHeaders
   └─ 需要 cancel/redirect 请求？
       → declarativeNetRequest 支持 block/redirect

3. 代码执行
   ├─ 使用 eval 或 new Function？
   │   → MV3 禁止，需要改用 chrome.scripting.executeScript
   ├─ 加载远程脚本？
   │   → MV3 禁止，所有代码必须打包
   └─ 使用沙箱 iframe？
       → 需要使用 sandbox 页面

4. 权限模型
   ├─ permissions 中混合了 host 和 API 权限？
   │   → host 权限需要移到 host_permissions
   └─ 使用 <all_urls>？
       → 考虑使用 activeTab + optional 权限
```

### 21.6.2 迁移步骤详解

```json
// 步骤 1: 修改 manifest.json
// MV2
{
  "manifest_version": 2,
  "background": { "scripts": ["background.js"] },
  "permissions": ["storage", "https://*/*"],
  "browser_action": { "default_popup": "popup.html" }
}

// MV3
{
  "manifest_version": 3,
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": ["https://*/*"],
  "action": { "default_popup": "popup.html" }
}
```

```javascript
// 步骤 2: 重写 Background → Service Worker

// MV2 Background Page（持久运行）
let cache = {};  // 全局缓存
let timer = setInterval(checkUpdate, 60000);  // 定时器

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.url.includes('ads')) {
      return { cancel: true };  // 阻塞式拦截
    }
  },
  { urls: ['<all_urls>'] },
  ['blocking']
);

// MV3 Service Worker（非持久）
// 不使用全局变量，改用 chrome.storage
async function getCache(key) {
  const result = await chrome.storage.session.get(key);
  return result[key];
}

async function setCache(key, value) {
  await chrome.storage.session.set({ [key]: value });
}

// 使用 chrome.alarms 替代 setInterval
chrome.alarms.create('check-update', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'check-update') {
    checkUpdate();
  }
});

// 网络拦截迁移到 declarativeNetRequest 规则文件
// rules.json 中声明规则，不在代码中拦截
```

```javascript
// 步骤 3: 迁移 webRequest 到 declarativeNetRequest

// MV2: 动态添加请求拦截
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (shouldBlock(details.url)) {
      return { redirectUrl: 'https://example.com/blocked.html' };
    }
  },
  { urls: ['*://*/*'] },
  ['blocking']
);

// MV3: 动态添加 declarativeNetRequest 规则
chrome.declarativeNetRequest.updateDynamicRules({
  addRules: [{
    id: 1001,
    priority: 1,
    action: {
      type: 'redirect',
      redirect: { url: 'https://example.com/blocked.html' }
    },
    condition: {
      urlFilter: '||tracker.com^',
      resourceTypes: ['main_frame', 'sub_frame']
    }
  }],
  removeRuleIds: [1001]  // 先移除旧规则
});
```

| 迁移项 | MV2 方式 | MV3 方式 | 难度 |
|--------|---------|---------|------|
| 后台脚本 | Background Page | Service Worker | 高 |
| 全局状态 | 全局变量 | chrome.storage | 中 |
| 定时器 | setInterval | chrome.alarms | 低 |
| 网络拦截 | webRequest(blocking) | declarativeNetRequest | 高 |
| 远程代码 | eval/远程脚本 | 全部打包 | 中 |
| 权限声明 | permissions | host_permissions + permissions | 低 |

## 21.7 Service Worker 保活技巧

### 21.7.1 SW 生命周期与保活需求

MV3 的 Service Worker 在空闲约 30 秒后被终止。某些场景需要更长的存活时间，比如长连接处理、进度跟踪等。但 Chrome 不推荐也不支持强制保活，正确的方式是利用事件驱动模型。

```
Service Worker 保活策略

不推荐：
  ✗ 使用 setInterval 持续占用（会被终止）
  ✗ 发送空消息保持活跃（违反政策）
  ✗ 使用 chrome.runtime.connect 持续 ping（可能被封）

推荐：
  ✓ chrome.alarms（最小间隔 1 分钟）
  ✓ offscreen API（需要 DOM/媒体能力时）
  ✓ chrome.storage 持久化状态
  ✓ 事件驱动模型（监听事件恢复工作）
```

### 21.7.2 chrome.alarms 定时任务

```javascript
// background.js (Service Worker)

// 创建定时器
chrome.alarms.create('data-sync', {
  periodInMinutes: 1,  // 最小 1 分钟
  when: Date.now() + 1000  // 首次触发时间
});

// 监听定时器
chrome.alarms.onAlarm.addListener(async (alarm) => {
  switch (alarm.name) {
    case 'data-sync':
      await syncData();
      break;
    case 'cleanup':
      await cleanupOldData();
      break;
  }
});

// 注意：alarms 最小间隔为 1 分钟
// 如果需要更频繁的操作，考虑使用 offscreen API
```

### 21.7.3 Offscreen API 处理需要 DOM 的任务

Service Worker 中没有 DOM API，某些功能（如播放音频、解析 HTML）需要 DOM 环境。Offscreen API 允许 SW 创建一个离屏文档来执行这些任务。

```javascript
// background.js
async function playNotificationSound() {
  // 检查是否已有 offscreen 文档
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });
  
  if (existingContexts.length === 0) {
    // 创建 offscreen 文档
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['AUDIO_PLAYBACK'],
      justification: '播放通知音效'
    });
  }
  
  // 向 offscreen 文档发送消息
  await chrome.runtime.sendMessage({
    type: 'PLAY_SOUND',
    url: 'notification.mp3'
  });
}

// offscreen.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'PLAY_SOUND') {
    const audio = new Audio(message.url);
    audio.play();
    sendResponse({ success: true });
  }
});
```

| 保活策略 | 适用场景 | 限制 |
|---------|---------|------|
| chrome.alarms | 定期任务 | 最小 1 分钟 |
| offscreen API | 需要 DOM/媒体 | 最多 1 个 offscreen 文档 |
| chrome.storage | 状态持久化 | 异步 API |
| 事件监听 | 事件驱动恢复 | 需要事件源 |

## 21.8 Content Script 注入策略

### 21.8.1 静态注入 vs 动态注入

Content Script 可以通过 manifest 静态声明注入，也可以通过 chrome.scripting API 动态注入。两种方式各有优劣。

```json
// 静态注入：manifest.json 中声明
{
  "content_scripts": [{
    "matches": ["https://*.example.com/*"],
    "js": ["content.js"],
    "css": ["content.css"],
    "run_at": "document_idle"
  }]
}
```

```javascript
// 动态注入：通过 chrome.scripting API
chrome.action.onClicked.addListener(async (tab) => {
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
  });
});

// 动态注入函数
chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: (config) => {
    // 在页面上下文中执行
    document.body.style.backgroundColor = config.color;
  },
  args: [{ color: '#f0f0f0' }]
});
```

| 对比 | 静态注入 | 动态注入 |
|------|---------|----------|
| 注入时机 | 页面加载时 | 按需注入 |
| 权限 | 需要在 manifest 声明 | 需要 scripting 权限 |
| 灵活性 | 低（匹配规则固定）| 高（可以条件注入）|
| 性能 | 页面加载时执行 | 需要时才执行 |
| 适用 | 持续运行的扩展 | 按需操作的扩展 |

### 21.8.2 MAIN world vs ISOLATED world

Content Script 默认运行在 ISOLATED world（隔离世界）中，与页面 JS 隔离。MV3 允许指定注入到 MAIN world（主世界）中，直接访问页面 JS 变量和函数。

```
MAIN world vs ISOLATED world

ISOLATED world（默认）:
  ├─ 有独立的 DOM
  ├─ JS 环境与页面隔离
  ├─ 不能访问页面 JS 变量
  ├─ 页面不能访问 Content Script 变量
  └─ 可以使用 chrome API

MAIN world:
  ├─ 与页面共享同一个 JS 环境
  ├─ 可以访问页面 JS 变量和函数
  ├─ 页面可以访问注入的变量和函数
  ├─ 不能使用 chrome API
  └─ 适合修改页面 JS 行为
```

```javascript
// ISOLATED world（默认）— 可以使用 chrome API
chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: () => {
    // 可以访问 DOM，但不能访问页面 JS 变量
    document.title = 'Modified';
    // window.appFunction() — 报错，无法访问
  }
});

// MAIN world — 可以访问页面 JS 环境
chrome.scripting.executeScript({
  target: { tabId: tab.id },
  world: 'MAIN',
  func: () => {
    // 可以访问页面的 JS 变量和函数
    if (window.app && window.app.getConfig) {
      const config = window.app.getConfig();
      console.log('页面配置:', config);
    }
    // 不能使用 chrome API
    // chrome.storage.local.get() — 报错
  }
});

// 两种 world 配合使用
// 1. MAIN world 获取页面数据
const pageData = await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  world: 'MAIN',
  func: () => window.app.getData()
});

// 2. ISOLATED world 处理并发送给 SW
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: (data) => {
    chrome.runtime.sendMessage({ type: 'PAGE_DATA', data });
  },
  args: [pageData[0].result]
});
```

## 21.9 chrome.scripting API 详解

### 21.9.1 核心方法

| 方法 | 功能 | 参数 |
|------|------|------|
| executeScript | 注入执行 JS | target, files/func, args, world |
| insertCSS | 注入 CSS | target, files/css |
| registerContentScripts | 注册 Content Script | matches, js, css, runAt, world |
| getRegisteredContentScripts | 获取已注册脚本 | ids |
| unregisterContentScripts | 注销脚本 | ids |
| updateContentScripts | 更新脚本 | ids, matches, js, css |

```javascript
// 动态注册 Content Script（替代 manifest 静态声明）
chrome.scripting.registerContentScripts([{
  id: 'main-content',
  matches: ['https://*.example.com/*'],
  js: ['content.js'],
  css: ['content.css'],
  runAt: 'document_start',
  world: 'ISOLATED',
  allFrames: false
}]);

// 动态更新
chrome.scripting.updateContentScripts([{
  id: 'main-content',
  css: ['content-v2.css']  // 更新 CSS
}]);

// 动态注销
chrome.scripting.unregisterContentScripts({ ids: ['main-content'] });
```

## 21.10 扩展权限模型与最小权限原则

### 21.10.1 权限分类

MV3 的权限模型更加精细，分为 API 权限、host 权限和可选权限。

```
权限模型

必需权限（permissions）:
  ├─ 扩展核心功能必需的 API
  ├─ 安装时授予
  └─ 示例: storage, alarms, scripting

Host 权限（host_permissions）:
  ├─ 可以访问的域名
  ├─ 安装时授予
  └─ 示例: https://*.example.com/*

可选权限（optional_permissions）:
  ├─ 非核心功能需要的权限
  ├─ 运行时请求
  └─ 示例: bookmarks, history

可选 Host 权限（optional_host_permissions）:
  ├─ 非核心域名
  ├─ 运行时请求
  └─ 示例: https://api.example.com/*
```

```javascript
// 运行时请求可选权限
document.getElementById('enable-sync').addEventListener('click', async () => {
  const granted = await chrome.permissions.request({
    permissions: ['bookmarks'],
    origins: ['https://api.sync.example.com/*']
  });
  if (granted) {
    startSync();
  } else {
    showNotice('需要授权才能使用同步功能');
  }
});

// 检查权限
const hasPermission = await chrome.permissions.contains({
  permissions: ['bookmarks']
});

// 移除不再需要的权限
chrome.permissions.remove({
  permissions: ['bookmarks']
});
```

| 权限类型 | 声明位置 | 授予时机 | 用户可见度 |
|---------|---------|----------|----------|
| API 权限 | permissions | 安装时 | 安装提示 |
| Host 权限 | host_permissions | 安装时 | 安装提示 |
| 可选 API | optional_permissions | 运行时 | 弹窗请求 |
| 可选 Host | optional_host_permissions | 运行时 | 弹窗请求 |

> 最小权限原则在扩展开发中尤为重要。用户对扩展的信任基于它请求的权限。如果一个笔记扩展请求 `<all_urls>` 权限，用户会警觉。使用 `activeTab` 权限可以只在用户主动点击时获得当前标签页的临时访问权，不需要持续的 host 权限。

## 21.11 扩展性能监控

### 21.11.1 Chrome 扩展性能分析

Chrome 扩展的性能直接影响用户体验。扩展的 Service Worker、Content Script 和 Popup 都可能成为性能瓶颈。

```javascript
// Service Worker 性能监控
chrome.runtime.onStartup.addListener(() => {
  performance.mark('sw-start');
});

chrome.runtime.onInstalled.addListener(() => {
  performance.mark('sw-installed');
  performance.measure('startup', 'sw-start', 'sw-installed');
  const measure = performance.getEntriesByName('startup')[0];
  console.log(`SW 启动耗时: ${measure.duration}ms`);
});

// 监控 SW 终止与重启
let swStartTime = Date.now();
chrome.runtime.onStartup.addListener(() => {
  swStartTime = Date.now();
});

// 使用 chrome.alarms 定期记录存活时间
chrome.alarms.create('monitor', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'monitor') {
    const aliveTime = (Date.now() - swStartTime) / 1000;
    console.log(`SW 存活时间: ${aliveTime}s`);
  }
});
```

### 21.11.2 Content Script 性能影响

```javascript
// Content Script 性能监控
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    // 监控长任务
    if (entry.entryType === 'longtask') {
      console.warn('Content Script 导致长任务:', entry.duration, 'ms');
    }
  }
});
observer.observe({ type: 'longtask', buffered: true });

// 监控内存
if (performance.measureUserAgentSpecificMemory) {
  performance.measureUserAgentSpecificMemory().then(result => {
    console.log('Content Script 内存:', result.bytes);
  });
}
```

## 21.12 Puppeteer 与 Chrome Extension 测试

### 21.12.1 加载扩展进行测试

```javascript
const puppeteer = require('puppeteer');

async function testExtension() {
  const browser = await puppeteer.launch({
    headless: false,  // 扩展测试需要非无头模式
    args: [
      `--disable-extensions-except=./extension`,
      `--load-extension=./extension`,
    ]
  });
  
  // 获取 Service Worker
  const swTarget = await browser.waitForTarget(
    target => target.type() === 'service_worker'
  );
  const swWorker = await swTarget.worker();
  
  // 测试 Service Worker 逻辑
  const result = await swWorker.evaluate(() => {
    return chrome.storage.local.get('testData');
  });
  console.log('SW 存储数据:', result);
  
  // 测试 Content Script
  const page = await browser.newPage();
  await page.goto('https://example.com');
  
  // 检查 Content Script 是否注入
  const injected = await page.evaluate(() => {
    return window.myExtensionInjected === true;
  });
  console.log('Content Script 注入:', injected);
  
  await browser.close();
}

testExtension();
```

### 21.12.2 自动化测试流程

```javascript
// 完整的扩展测试套件
async function runExtensionTests() {
  const browser = await puppeteer.launch({
    headless: false,
    args: [
      `--disable-extensions-except=${__dirname}/../extension`,
      `--load-extension=${__dirname}/../extension`,
    ]
  });
  
  const tests = [];
  
  // 测试 1: Service Worker 启动
  const swTarget = await browser.waitForTarget(
    t => t.type() === 'service_worker' && t.url().includes('background')
  );
  tests.push({ name: 'SW 启动', pass: !!swTarget });
  
  // 测试 2: Popup 页面加载
  const page = await browser.newPage();
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  const popupTitle = await page.title();
  tests.push({ name: 'Popup 加载', pass: popupTitle.length > 0 });
  
  // 测试 3: Content Script 注入
  const testPage = await browser.newPage();
  await testPage.goto('https://example.com');
  const injected = await testPage.evaluate(() => !!window.myExtensionInjected);
  tests.push({ name: 'CS 注入', pass: injected });
  
  // 测试 4: declarativeNetRequest 规则生效
  const blocked = await testPage.evaluate(async () => {
    try {
      await fetch('https://ads.example.com/test.js');
      return false;  // 未被拦截
    } catch (e) {
      return true;  // 被拦截
    }
  });
  tests.push({ name: 'DNR 规则', pass: blocked });
  
  console.log('测试结果:');
  tests.forEach(t => {
    console.log(`${t.pass ? 'PASS' : 'FAIL'} - ${t.name}`);
  });
  
  await browser.close();
  return tests.every(t => t.pass);
}

runExtensionTests();
```

| 测试维度 | 测试内容 | 工具 |
|---------|---------|------|
| Service Worker | 启动、消息处理 | Puppeteer + SW target |
| Content Script | 注入、DOM 操作 | Puppeteer + page.evaluate |
| Popup | UI 渲染、交互 | Puppeteer + page.goto |
| declarativeNetRequest | 请求拦截 | Puppeteer + fetch |
| Storage | 数据持久化 | chrome.storage API |
| 权限 | 权限请求流程 | Puppeteer + permissions |

## 本章核心知识总结

| 知识模块 | 核心内容 | 实践意义 |
|---------|---------|---------|
| MV3 架构 | SW 替代 Background Page | 理解非持久性 |
| 状态持久化 | chrome.storage + alarms | 替代全局变量 |
| Content Script 通信 | sendMessage + connect | 扩展通信 |
| declarativeNetRequest | JSON 规则声明 | 替代 webRequest |
| CDP | DevTools 协议 | 自动化测试 |

觉得有用？收藏起来，下次开发 Chrome 扩展时参考。

你开发过 Chrome 扩展吗？MV3 迁移遇到什么问题？评论区聊聊。

关注怕浪猫，下期我们讲 DevTools 与调试技巧。系列进度 21/24。

下期预告：第 22 章「DevTools 与调试技巧」。我们会拆解 DevTools 各面板的高级用法、Performance 面板的火焰图分析、以及 Lighthouse 自动化审计。怕浪猫下期见。

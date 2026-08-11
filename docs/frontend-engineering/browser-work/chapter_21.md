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

## 21.13 declarativeNetRequest 规则编写实战

### 21.13.1 规则结构详解

declarativeNetRequest（DNR）的规则是纯 JSON 声明式的，浏览器在网络层直接执行，不需要唤醒 Service Worker。理解规则的结构是编写高效拦截规则的基础。

一条完整的 DNR 规则包含三个核心部分：`action` 定义匹配后的操作，`condition` 定义何时匹配，`priority` 定义规则冲突时的优先级。`condition` 中的 `urlFilter` 支持类似 ABP（Adblock Plus）过滤语法，可以精确匹配 URL 模式。

```json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||doubleclick.net^",
      "resourceTypes": ["script", "image", "xmlhttprequest", "sub_frame"]
    }
  },
  {
    "id": 2,
    "priority": 2,
    "action": {
      "type": "modifyHeaders",
      "requestHeaders": [
        { "header": "cookie", "operation": "remove" }
      ]
    },
    "condition": {
      "urlFilter": "||third-party-tracker.com^",
      "resourceTypes": ["xmlhttprequest"]
    }
  },
  {
    "id": 3,
    "priority": 1,
    "action": {
      "type": "redirect",
      "redirect": {
        "transform": { "scheme": "https" }
      }
    },
    "condition": {
      "urlFilter": "http://*/*",
      "resourceTypes": ["main_frame"]
    }
  }
]
```

`urlFilter` 中的特殊符号含义如下：`||` 表示域名前缀，匹配协议和子域名。`^` 表示分隔符，匹配斜杠、问号、并号等。`*` 是通配符，匹配任意字符串。理解这些符号对于编写精确的过滤规则至关重要。

### 21.13.2 动态规则与会话规则

DNR 支持四种规则集：静态规则集（打包在扩展中）、动态规则集（运行时添加或移除）、会话规则集（内存中，浏览器关闭后丢失）和动态规则集。每种规则集有不同的生命周期和数量限制。

| 规则集类型 | 存储位置 | 生命周期 | 数量限制 |
|-----------|---------|---------|----------|
| 静态规则 | 扩展包 | 持久 | 30,000 |
| 动态规则 | 浏览器存储 | 持久 | 10,000 |
| 会话规则 | 内存 | 会话内 | 5,000 |

### 21.13.3 规则调试与测试

编写 DNR 规则时，调试是一个挑战，因为规则在网络层执行，不像代码可以打断点。Chrome DevTools 的 Network 面板可以帮助验证规则是否生效。被 DNR 拦截的请求会显示为 `(blocked: other)` 状态，点击请求可以查看具体被哪条规则拦截。

```javascript
// 在 Service Worker 中获取规则匹配信息
chrome.declarativeNetRequest.getMatchedRules({}, (rules) => {
  rules.rulesMatchedInfo.forEach(info => {
    console.log(`规则 ${info.rule.ruleId} 拦截了 ${info.request.url}`);
  });
});

// 检查规则是否冲突
chrome.declarativeNetRequest.getDynamicRules((rules) => {
  console.log('当前动态规则:', rules.length, '条');
  rules.forEach(rule => {
    console.log(`  ID:${rule.id} 优先级:${rule.priority} 动作:${rule.action.type}`);
  });
});
```

## 21.14 扩展开发最佳实践

### 21.14.1 架构设计原则

MV3 扩展的架构设计需要遵循事件驱动和无状态两个核心原则。事件驱动意味着所有逻辑都从事件触发开始，无论是用户点击、页面导航还是定时器。无状态意味着 Service Worker 的每次启动都应该是幂等的，不依赖前一次运行的全局状态。

这种架构风格与传统的前端开发有本质区别。在传统前端中，全局状态管理是常态，组件在内存中保持状态。而在 MV3 中，Service Worker 随时可能被终止和重启，所有状态必须持久化到 `chrome.storage` 中。这种设计虽然增加了开发复杂度，但带来了更好的资源利用率和更低的内存占用。

一个健壮的 MV3 扩展架构应该包含以下层次：消息路由层负责分发事件到对应的处理器，状态管理层负责读写 `chrome.storage`，业务逻辑层实现核心功能，通信层负责与 Content Script 和 Popup 交互。每一层都应该无状态，通过消息传递数据。

### 21.14.2 Content Script 与页面交互模式

Content Script 运行在网页上下文中，需要处理与页面的隔离和通信。在 ISOLATED world 中，Content Script 可以访问 DOM 但不能访问页面的 JavaScript 变量。在 MAIN world 中则相反，可以访问页面 JavaScript 但不能使用 Chrome 扩展 API。

选择注入策略时需要考虑安全性和功能性。如果只需要读取或修改 DOM，使用 ISOLATED world 即可。如果需要拦截或修改页面的 JavaScript 函数行为，则需要 MAIN world 注入。但 MAIN world 注入有安全风险，页面的恶意代码可能篡改注入的函数。

### 21.14.3 扩展发布与分发策略

Chrome Web Store 的审核机制越来越严格，特别是对权限请求的审查。扩展应该遵循最小权限原则，只请求核心功能必需的权限。对于非核心功能，使用可选权限在运行时请求，让用户在需要时才授权。

扩展的更新机制也需要考虑。MV3 的 Service Worker 在浏览器启动时加载新版本，但旧版本可能仍在运行。正确的做法是在 `chrome.runtime.onInstalled` 中处理更新逻辑，包括迁移存储数据、更新 DNR 规则、清理旧缓存等。

### 21.14.4 消息通信的安全考虑

扩展中的消息通信需要在不可信的环境中传输数据。Content Script 运行在网页上下文中，网页的 JavaScript 可能被恶意代码注入。如果 Content Script 通过 `window.postMessage` 与页面通信，恶意代码可以伪造消息或窃听通信内容。

安全的消息通信应该包含以下措施：使用 `chrome.runtime.sendMessage` 而不是 `window.postMessage` 进行扩展内部通信，因为前者通过浏览器内部通道传输，网页无法窃听。如果必须使用 `window.postMessage`，应该验证 `event.origin` 和 `event.source`，并在消息中包含签名或令牌验证。Content Script 不应该信任来自页面的任何数据，所有输入都需要校验和消毒。

Service Worker 接收来自 Content Script 的消息时也需要验证。虽然 Content Script 本身是可信的（由扩展控制），但如果 Content Script 的注入页面被攻击者控制，攻击者可能通过页面 JavaScript 间接影响 Content Script 的行为。Service Worker 应该对消息内容进行校验，不信任 Content Script 传入的任何敏感操作请求。

### 21.14.5 扩展性能优化与资源管理

扩展的性能直接影响浏览器的整体体验。一个臃肿的扩展会让整个浏览器变慢，而不只是扩展自己的页面。Service Worker 的启动时间应该控制在毫秒级别，避免在 `onMessage` 监听器中执行大量同步操作。

Content Script 的性能优化尤为重要，因为它运行在用户正在浏览的网页中。Content Script 中的任何性能问题都会直接影响页面体验。应该避免在 Content Script 中执行复杂的 DOM 操作，将重计算逻辑放到 Service Worker 中通过消息通信触发。Content Script 的 CSS 注入也要谨慎，避免使用全局选择器覆盖页面样式。

内存管理在扩展中同样重要。Service Worker 虽然会被浏览器自动终止和重启，但在运行期间的内存使用仍然需要控制。特别是在处理大量数据时，应该使用流式处理而不是一次性加载所有数据到内存中。Content Script 中创建的事件监听器需要在页面卸载或扩展卸载时正确移除，否则会造成内存泄漏。

### 21.14.6 Content Script 与页面集成模式

Content Script 与页面的集成是扩展开发中最复杂的部分。Content Script 运行在网页上下文中，需要处理与页面 JavaScript 的隔离、与页面 DOM 的交互、以及与 Service Worker 的通信。不同的集成模式适用于不同的使用场景。

最简单的模式是纯 DOM 操作。Content Script 直接读取或修改 DOM，不需要与页面 JavaScript 交互。这种模式适用于内容增强类扩展，比如高亮关键词、注入工具栏、修改页面样式。纯 DOM 操作使用 ISOLATED world 即可，安全且简单。

更复杂的模式是页面函数拦截。Content Script 需要拦截或修改页面 JavaScript 的某些函数行为。比如阻止页面调用 `alert`，或者修改 `fetch` 的行为。这需要 MAIN world 注入，将覆盖代码注入到页面 JavaScript 环境中。这种模式有安全风险，因为页面的恶意代码可能检测到注入的函数并绕过拦截。

最复杂的模式是完整页面集成。Content Script 与页面深度集成，实现自定义功能。比如在网页中注入一个完整的 UI 界面，与页面的数据模型交互。这种模式通常需要同时使用 ISOLATED world 和 MAIN world，ISOLATED world 负责与 Service Worker 通信，MAIN world 负责与页面 JavaScript 交互，两个 world 之间通过 `window.postMessage` 通信。

### 21.14.7 declarativeNetRequest 高级用法

declarativeNetRequest 不只能做简单的阻断和重定向，还可以修改请求和响应的头部。修改头部的能力让扩展可以实现 Cookie 管理、Referer 控制、CORS 绕过等功能。

一个常见的用例是移除第三方 Cookie。扩展可以编写规则，对于非第一方域名的请求，移除其 Cookie 头。这种规则不需要 Service Worker 参与，完全在网络层执行，性能极高。另一个用例是添加自定义请求头，比如为特定网站的 API 请求添加认证令牌。

需要注意的是，DNR 的规则是静态声明的，不能在运行时动态生成。如果需要基于复杂条件修改请求，只能在 Service Worker 中使用 `chrome.declarativeNetRequest.onRuleMatched` 事件配合动态规则。但动态规则的数量有上限，且每条规则都会增加网络请求的处理开销。合理的设计是在静态规则中覆盖大部分场景，动态规则只用于特殊情况。

### 21.14.8 扩展国际化与多语言支持

Chrome 扩展的国际化通过 `_locales` 目录和 `chrome.i18n` API 实现。每种语言一个子目录，包含 `messages.json` 文件定义翻译字符串。manifest.json 和 CSS 文件中可以用 `__MSG_xxx__` 占位符引用翻译字符串。

国际化不仅仅是翻译文本，还需要考虑布局方向（RTL 语言）、日期时间格式、数字格式等文化差异。Chrome 的 `i18n` API 提供了 `getMessage`、`getUILanguage` 和 `getAcceptLanguages` 三个核心方法。在 Content Script 中使用国际化时，需要注意消息字符串的转义，避免 XSS 注入。

### 21.14.9 扩展安全审计与发布检查

Chrome 扩展拥有比普通网页更高的权限，可以访问用户在所有网站上的数据、修改网络请求、读写剪贴板等。因此扩展的安全性比普通网页更重要。在发布扩展之前，应该进行全面的安全审计。

安全审计的第一个维度是权限审查。检查 manifest.json 中声明的所有权限，确认每个权限都是核心功能必需的。对于不在核心路径上的权限，应该改为可选权限。审查 host_permissions，确保没有使用过于宽泛的域名匹配。`<all_urls>` 权限应该尽量避免，改用 `activeTab` 获取当前标签页的临时访问权。

安全审计的第二个维度是代码安全。检查所有 `eval` 和 `new Function` 的使用，MV3 中这些是被禁止的。检查 Content Script 中的 DOM 操作是否做了输入校验。检查 `chrome.tabs.executeScript` 是否被正确替换为 `chrome.scripting.executeScript`。检查所有外部网络请求是否使用了 HTTPS。

安全审计的第三个维度是数据安全。检查扩展是否将用户数据发送到外部服务器。如果是，确认数据传输使用了加密协议，并且隐私政策明确告知用户。检查 `chrome.storage` 中是否存储了敏感信息，如密码或令牌。敏感信息应该使用 `chrome.storage.session` 而不是 `chrome.storage.local`，因为前者在浏览器关闭后自动清除。

### 21.14.10 扩展性能基线与优化策略

扩展的性能影响不仅体现在扩展自身页面，还会影响用户访问的所有网页。Content Script 注入到每个匹配的页面中，如果 Content Script 执行缓慢，用户会感觉整个网站都变慢了。Service Worker 的启动时间影响扩展功能的响应速度。因此扩展性能优化需要关注多个维度。

Content Script 的性能优化是重中之重。Content Script 在页面加载时执行，如果执行时间过长会阻塞页面渲染。优化策略包括：将 Content Script 的执行时机设置为 `document_idle`，避免阻塞页面初始渲染。将非关键操作延迟到 `requestIdleCallback` 中执行。避免在 Content Script 中进行大量 DOM 操作，使用 DocumentFragment 批量插入。Content Script 中的 CSS 应该尽量精简，避免使用通配选择器。

Service Worker 的启动性能影响扩展功能的响应速度。MV3 的 Service Worker 在事件触发时启动，启动时间通常在几十毫秒。如果 Service Worker 中有大量初始化代码，启动时间可能显著增加。优化策略是将初始化逻辑拆分为按需加载的模块，只加载当前事件需要的代码。使用 `chrome.storage.session` 缓存计算结果，避免每次启动都重复计算。

### 21.14.11 从零开发一个完整 MV3 扩展

理解 MV3 最好的方式是实际开发一个扩展。以下是一个完整的广告拦截扩展的核心代码，展示了 MV3 的主要特性如何配合使用。

扩展的功能是拦截已知的广告和追踪域名，同时在页面上显示拦截统计。manifest.json 声明了 Service Worker、Content Script 和 declarativeNetRequest 规则集。Service Worker 负责统计拦截数量和管理规则。Content Script 负责在页面上显示统计面板。declarativeNetRequest 规则在网络层拦截广告请求。

这个扩展展示了 MV3 的核心模式：声明式网络拦截不需要 Service Worker 参与，事件驱动的架构保证 Service Worker 只在需要时启动，Content Script 与 Service Worker 通过消息通信协作，所有状态通过 chrome.storage 持久化。理解这个示例后，可以基于它扩展更复杂的功能。

### 21.14.12 MV3 扩展开发常见踩坑点

从 MV2 迁移到 MV3 的过程中，有一些不太明显但容易踩坑的地方。这些坑通常不会在迁移文档中明确提到，而是在实际开发中才会遇到。

第一个坑是 Service Worker 中不能使用 DOM API。在 MV2 的 Background Page 中，开发者可以使用 `document.createElement` 创建离屏 DOM 元素来解析 HTML 或操作 XML。但在 MV3 的 Service Worker 中没有 `document` 对象。如果需要解析 HTML，必须使用 Offscreen API 创建离屏文档，或者使用 DOMParser 的替代方案。这个限制影响了很多需要解析 HTML 的扩展功能。

第二个坑是 `chrome.tabs.executeScript` 被移除。MV2 中常用的动态注入脚本方法在 MV3 中不可用，需要替换为 `chrome.scripting.executeScript`。两者的参数略有不同，`executeScript` 需要传入 `target` 对象而不是 `tabId`。批量注入多个标签页时需要使用 `target: { tabIds: [1, 2, 3] }`。

第三个坑是 Content Script 的执行时机。MV3 中 `run_at` 字段的可选值和含义与 MV2 相同，但实际执行时机可能有微小差异。特别是在 `document_start` 时执行的 Content Script，在某些页面上可能比 MV2 更晚执行。这是因为 MV3 的架构变更影响了脚本注入的时机。如果扩展强依赖执行时机，需要仔细测试。

### 21.14.13 扩展与 Web 页面的深度交互

扩展与 Web 页面的交互不仅限于 Content Script。Chrome 提供了多种机制让扩展与页面深度交互，包括侧边栏面板、DevTools 面板和全屏覆盖层。

Side Panel API（`chrome.sidePanel`）是 Chrome 114 引入的新能力，允许扩展在浏览器侧边栏中显示自定义界面。与 Popup 不同，Side Panel 是持久的——用户切换标签页时不会关闭。这适合需要持续显示信息的扩展，比如实时翻译、笔记工具或代码审查工具。

DevTools 面板通过 `chrome.devtools.panels` API 创建，允许扩展在 DevTools 中添加自定义标签页。这对于调试工具类扩展特别有用。比如一个 API 调试扩展可以在 DevTools 面板中显示格式化的请求/响应信息。DevTools 面板可以通过 `chrome.devtools.inspectedWindow` API 访问当前检查的页面的信息。

### 21.14.14 扩展的版本管理与发布流程

扩展的版本管理需要考虑 Chrome Web Store 的审核机制。每次提交新版本时，Chrome Web Store 会自动检查 manifest.json 的版本号是否递增。版本号建议使用语义化版本规范（Semantic Versioning），主版本号表示破坏性变更，次版本号表示新功能，修订号表示修复。

发布流程应该包括以下步骤：在开发分支完成开发后，运行自动化测试套件确认功能正常。更新版本号和变更日志。在测试环境中加载未打包的扩展进行全面测试。提交到 Chrome Web Store 的开发者仪表板，填写版本说明。等待审核通过后自动发布。整个流程可以通过 CI/CD 自动化，但最终发布仍需人工确认。

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

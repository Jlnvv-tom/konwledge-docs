# 第16章 Cookie 安全与隐私保护

> Cookie 是 Web 身份认证的基础，也是隐私争议的中心。第三方 Cookie 正在被淘汰，但第一方 Cookie 依然重要。理解 Cookie 的安全属性和隐私替代方案是现代前端开发的必修课。

我是怕浪猫，上期讲了沙箱与站点隔离，今天进入第 16 章：Cookie 安全与隐私保护。这一章拆解 Cookie 的安全属性、第三方 Cookie 消亡路线图、以及 Privacy Sandbox 的替代方案。

## 16.1 Cookie 的安全属性

### 16.1.1 Cookie 属性总览

一个 Cookie 可以设置多个属性，控制其行为和安全性。

```http
Set-Cookie: session=abc123; 
  Domain=example.com; 
  Path=/; 
  Max-Age=86400; 
  Secure; 
  HttpOnly; 
  SameSite=Lax; 
  Priority=High
```

| 属性 | 作用 | 安全意义 |
|------|------|---------|
| Domain | Cookie 发送范围 | 控制可见域名 |
| Path | URL 路径限制 | 限制发送路径 |
| Max-Age/Expires | 过期时间 | 限制持久性 |
| Secure | 仅 HTTPS 发送 | 防中间人窃听 |
| HttpOnly | JS 不可读取 | 防 XSS 窃取 |
| SameSite | 跨站发送策略 | 防 CSRF |
| Priority | 优先级 | 超限时的保留策略 |
| Partitioned | 分区存储 | 替代第三方 Cookie |

### 16.1.2 Secure 属性

Secure 属性确保 Cookie 只在 HTTPS 连接中发送，防止在 HTTP 连接中被中间人窃听。

```http
# 设置 Secure 的 Cookie
Set-Cookie: session=abc123; Secure

# 行为：
# HTTPS 请求 → 发送 Cookie ✓
# HTTP 请求 → 不发送 Cookie ✗
```

> 所有现代浏览器都要求 SameSite=None 的 Cookie 必须同时设置 Secure。不支持 Secure 的 SameSite=None Cookie 会被拒绝。

### 16.1.3 HttpOnly 属性

HttpOnly 属性阻止 JavaScript 通过 document.cookie 读取 Cookie，是防范 XSS 窃取 Cookie 的第一道防线。

```javascript
// 设置了 HttpOnly 的 Cookie
Set-Cookie: session=abc123; HttpOnly

// JavaScript 无法读取
document.cookie;  // 不包含 session Cookie

// 没有设置 HttpOnly 的 Cookie
Set-Cookie: pref=dark; 

// JavaScript 可以读取
document.cookie;  // "pref=dark"
```

| Cookie 类型 | 建议 HttpOnly | 原因 |
|------------|--------------|------|
| 会话 Cookie | 是 | 敏感信息，不应被 JS 读取 |
| 认证 Token | 是 | 敏感信息 |
| CSRF Token | 否 | JS 需要读取并附加到请求头 |
| 用户偏好 | 否 | JS 需要读写 |
| 分析追踪 | 视情况 | 看是否需要 JS 读取 |

### 16.1.4 SameSite 属性详解

SameSite 属性控制 Cookie 在跨站请求中的发送行为，是 CSRF 防护的重要手段。

```
SameSite 行为对比

场景：用户访问 evil.com，evil.com 向 bank.com 发请求

SameSite=Strict:
  请求不携带 bank.com 的 Cookie
  即使点击链接跳转到 bank.com 也不携带
  → 最安全，但用户体验差

SameSite=Lax（Chrome 默认）:
  顶级导航的 GET 请求携带 Cookie
  如：<a href="bank.com">、window.location
  子资源请求不携带
  如：<img>、<iframe>、fetch
  POST 不携带
  → 安全与体验平衡

SameSite=None:
  所有跨站请求都携带 Cookie
  需要 Secure
  → 用于需要跨站的场景（如嵌入式登录）
```

| 请求场景 | Strict | Lax | None |
|---------|--------|-----|------|
| 同源请求 | 携带 | 携带 | 携带 |
| 顶级导航 GET | 不携带 | 携带 | 携带 |
| 顶级导航 POST | 不携带 | 不携带 | 携带 |
| `<img>` 跨域 | 不携带 | 不携带 | 携带 |
| `<iframe>` 跨域 | 不携带 | 不携带 | 携带 |
| fetch 跨域 | 不携带 | 不携带 | 携带 |

## 16.2 第三方 Cookie 的消亡

### 16.2.1 什么是第三方 Cookie

第三方 Cookie 是指在当前页面域名之外的域名设置的 Cookie。通常用于跨站追踪和广告。

```
第三方 Cookie 示例

页面: https://news.com
  ├─ <img src="https://ad.com/pixel"> 
  │   → ad.com 设置 Cookie: tracking_id=123
  │   → 这是第三方 Cookie
  │
  ├─ <iframe src="https://embed.com/widget">
  │   → embed.com 设置 Cookie: session=abc
  │   → 这是第三方 Cookie
  │
  └─ fetch('https://api.news.com/data')
      → api.news.com 设置 Cookie
      → 如果 news.com 和 api.news.com 同站点 → 第一方

用户访问 other-site.com:
  ├─ <img src="https://ad.com/pixel">
  │   → 发送 ad.com 的 tracking_id Cookie
  │   → ad.com 知道用户从 news.com 来了
  │   → 跨站追踪
```

### 16.2.2 第三方 Cookie 的问题

第三方 Cookie 是行为广告（Behavioral Advertising）的技术基础。广告网络通过在多个网站部署追踪像素，收集用户的浏览历史，用于精准广告投放。

| 问题 | 说明 |
|------|------|
| 隐私侵犯 | 用户浏览历史被跨站收集 |
| 缺乏知情同意 | 大多数用户不知道被追踪 |
| 数据滥用 | 追踪数据可能被出售或泄露 |
| 指纹识别 | 追踪可扩展为设备指纹 |

### 16.2.3 Chrome 的第三方 Cookie 淘汰路线

Chrome 正在逐步淘汰第三方 Cookie。这是 Web 隐私的重大变化。

| 时间 | 事件 | 说明 |
|------|------|------|
| 2020 | Chrome 宣布淘汰计划 | 两年内逐步淘汰 |
| 2020-2023 | Privacy Sandbox 提案 | 开发替代方案 |
| 2024 | 1% 用户禁用 | 小规模测试 |
| 2025 | 全面禁用 | 100% 用户禁用第三方 Cookie |

> 第三方 Cookie 的消亡不是终点，而是新的开始。广告行业不会因此停止追踪用户，而是转向 Privacy Sandbox 等隐私保护更好的方案。开发者需要评估自己的服务是否依赖第三方 Cookie，并提前迁移。

## 16.3 Privacy Sandbox

### 16.3.1 Privacy Sandbox 的目标

Privacy Sandbox 是 Chrome 提出的一系列 Web API，旨在在不使用第三方 Cookie 的情况下实现广告和测量功能，同时保护用户隐私。

| API | 功能 | 替代的第三方 Cookie 用途 |
|-----|------|------------------------|
| Topics API | 兴趣主题广告 | 行为广告 |
| Protected Audience API | 重定向广告 | 用户追踪 |
| Attribution Reporting | 广告归因 | 转化追踪 |
| Private Aggregation | 匿名统计 | 受众测量 |
| Storage Access API | 跨站存储授权 | 嵌入式登录 |

### 16.3.2 Topics API

Topics API 根据用户的浏览历史推断兴趣主题，广告平台可以获取这些主题来展示相关广告，但不会暴露具体浏览历史。

```
Topics API 巏作流程

1. 浏览器为每个网站分配主题
   example.com → Technology
   sports.com → Sports
   cooking.com → Food & Drink

2. 浏览器记录用户最近 3 周的主题
   Week 1: Technology, Sports
   Week 2: Sports, Food & Drink
   Week 3: Technology, Food & Drink

3. 广告平台调用 API 获取主题
   document.browsingTopics()
   → 返回最近的主题（每个 epoch 1 个主题）
   → 不暴露具体浏览了哪些网站

4. 广告平台根据主题投放广告
   → 看到主题 "Technology" → 展示技术产品广告
```

| 对比 | 第三方 Cookie | Topics API |
|------|-------------|-----------|
| 数据粒度 | 精确到每个网站 | 主题级别 |
| 用户识别 | 跨站追踪 | 无跨站追踪 |
| 数据存储 | 广告平台 | 浏览器本地 |
| 隐私保护 | 弱 | 强 |

### 16.3.3 CHIPS（分区 Cookie）

CHIPS（Cookies Having Independent Partitioned State，分区 Cookie）允许第三方 Cookie 按顶级站点分区存储，不跨站追踪。

```http
# 分区 Cookie
Set-Cookie: session=abc123; Partitioned; Secure; SameSite=None

# 行为：
# 在 news.com 中加载 embed.com 的 iframe
# → embed.com 设置分区 Cookie，关联到 news.com
# 
# 在 other.com 中加载 embed.com 的 iframe
# → embed.com 的 Cookie 不包含 news.com 的分区
# → 每个顶级站点有独立的分区
```

```
CHIPS 分区存储

传统第三方 Cookie:
  ad.com 的 Cookie 在所有网站共享

CHIPS 分区 Cookie:
  news.com + ad.com → Cookie A
  sports.com + ad.com → Cookie B
  other.com + ad.com → Cookie C
  
  每个分区独立，不跨站关联
```

> CHIPS 是第三方 Cookie 的温和替代。它允许嵌入式服务在各个站点独立保存状态，但不跨站关联用户。对于需要嵌入式登录的服务（如 Disqus 评论系统），CHIPS 是理想的解决方案。

### 16.3.4 Protected Audience API（TURTLEDOVE）

Protected Audience API（前身为 TURTLEDOVE）是 Privacy Sandbox 中用于重定向广告的 API。重定向广告是指向之前访问过某网站的用户展示广告。

传统方式中，广告平台通过第三方 Cookie 追踪用户访问历史。Protected Audience API 将这个过程搬到了浏览器内部：

```
Protected Audience 工作流程

1. 用户访问 example.com
   → 浏览器在本地记录兴趣组（Interest Group）
   → { owner: 'ad-platform', name: 'shoes-shopper' }

2. 用户访问 other-site.com
   → 页面中有广告位
   → 浏览器运行竞价算法（本地）
   → 查看本地兴趣组
   → 向 ad-platform 请求候选广告
   → 本地决定展示哪个广告

3. 广告展示
   → 广告平台不知道用户具体是谁
   → 只知道用户属于某个兴趣组
   → 竞价在浏览器本地完成
```

| 对比 | 第三方 Cookie 重定向 | Protected Audience |
|------|---------------------|-------------------|
| 用户历史 | 广告平台服务器 | 浏览器本地 |
| 竞价 | 广告平台服务器 | 浏览器本地 |
| 隐私 | 跨站追踪 | 无跨站追踪 |
| 延迟 | 低（服务器已有数据） | 稍高（本地竞价） |

### 16.3.5 Attribution Reporting API

Attribution Reporting API 用于广告归因——衡量用户看到广告后是否完成了转化（如购买）。传统方式中，广告平台通过第三方 Cookie 追踪用户从广告点击到转化的完整路径。

```javascript
// 注册广告点击归因
// 在广告页面
fetch('/register-source', {
  headers: {
    'Attribution-Reporting-Eligible': 'navigation-source'
  }
});

// 在转化页面
fetch('/register-trigger', {
  headers: {
    'Attribution-Reporting-Eligible': 'trigger'
  }
});

// 浏览器在本地匹配 source 和 trigger
// 延迟上报归因报告（防止实时追踪）
```

## 16.4 Cookie 替代方案

### 16.4.1 认证方案演进

第三方 Cookie 淘汰后，一些依赖第三方 Cookie 的认证方案需要迁移。

| 方案 | 依赖第三方 Cookie？ | 替代方案 |
|------|-------------------|---------|
| 单点登录（SSO） | 部分 | Storage Access API |
| 嵌入式登录 | 是 | Storage Access API + CHIPS |
| OAuth 2.0 | 否 | 重定向流程 |
| 跨站 Widget | 是 | CHIPS + Storage Access API |

### 16.4.2 Storage Access API

Storage Access API 允许嵌入式内容请求访问其第一方存储。用户需要授权。

```javascript
// 嵌入式 iframe 请求存储访问
async function requestStorageAccess() {
  if (document.requestStorageAccess) {
    try {
      await document.requestStorageAccess();
      // 用户授权后，可以访问第一方 Cookie
      console.log('存储访问已授权');
    } catch (e) {
      // 用户拒绝
      console.log('存储访问被拒绝');
    }
  }
}
```

## 16.5 浏览器存储与隐私

### 16.5.1 存储 API 的隐私考量

除了 Cookie，浏览器还有多种存储机制。它们也面临隐私问题。

| 存储机制 | 容量 | 跨站追踪风险 | 隐私保护 |
|---------|------|------------|---------|
| Cookie | 4KB/个 | 高 | SameSite + 分区 |
| localStorage | 5-10MB | 中（同源限制） | 同源策略 |
| sessionStorage | 5-10MB | 低（标签页隔离） | 自动清除 |
| IndexedDB | 大容量 | 中（同源限制） | 同源策略 |
| Cache API | 大容量 | 中 | 同源策略 |
| SharedArrayBuffer | 内存级 | 高（侧信道） | COOP+COEP |

### 16.5.2 存储分区

为了防止跨站追踪，Chrome 正在将所有存储 API 分区化。分区键是顶级站点和当前站点。

```
存储分区

传统存储：
  embed.com 的 localStorage 在所有站点共享

分区存储：
  news.com + embed.com → 分区 A
  sports.com + embed.com → 分区 B
  
  每个分区独立，embed.com 无法跨站关联用户
```

存储分区影响的 API 包括：localStorage、sessionStorage、IndexedDB、Cache API、Service Worker 缓存、Cookie。这意味着嵌入在不同网站中的第三方服务，每个网站的存储都是独立的。

### 16.5.3 Service Worker 与隐私

Service Worker 拦截网络请求的能力引发隐私担忧。Service Worker 可以看到所有网络请求，包括请求 URL 和响应头。但 Service Worker 受同源策略限制，只能拦截同源请求。

| Service Worker 能力 | 隐私影响 | 限制 |
|-------------------|---------|------|
| 拦截同源请求 | 低 | 同源限制 |
| 修改请求/响应 | 中 | 仅同源 |
| 后台同步 | 中 | 用户可见 |
| Push 通知 | 低 | 用户授权 |
| 持久存储 | 中 | 有过期机制 |

> 存储分区是隐私保护的必然趋势。未来所有浏览器存储都会按顶级站点分区，开发者需要假设跨站存储不再可用，像处理 CORS 一样处理存储分区。

## 16.6 设备指纹与反指纹

### 16.6.1 设备指纹技术

设备指纹（Device Fingerprinting）是不依赖 Cookie 的用户追踪技术。它通过收集设备的各种属性，生成唯一标识。

| 指纹维度 | 说明 | 稳定性 |
|---------|------|--------|
| User-Agent | 浏览器和 OS 信息 | 中 |
| Canvas 指纹 | GPU 渲染差异 | 高 |
| WebGL 指纹 | GPU 信息 | 高 |
| 字体列表 | 已安装字体 | 高 |
| 屏幕分辨率 | 物理像素 | 高 |
| 时区 | 系统时区 | 高 |
| 语言 | 浏览器语言 | 中 |
| AudioContext | 音频处理差异 | 高 |

### 16.6.2 Chrome 的反指纹措施

Chrome 采取多项措施降低指纹识别的可行性：

| 措施 | 说明 | 效果 |
|------|------|------|
| User-Agent 降级 | 冻结 UA 字符串 | 减少版本信息 |
| Canvas 噪声 | 添加微量随机化 | 降低 Canvas 指纹稳定性 |
| 字体列表限制 | 只暴露通用字体 | 减少字体指纹 |
| 时区精度 | 保持但限制 API | — |
| JS API 限制 | 移除指纹相关 API | 减少可探测属性 |

> 设备指纹是比 Cookie 更难防范的隐私问题。即使用户清除 Cookie，指纹仍然可以识别用户。Privacy Sandbox 的设计目标之一就是让浏览器提供足够的功能，同时减少可用于指纹的信息量。

## 本章核心知识总结

| 知识模块 | 核心内容 | 安全/隐私意义 |
|---------|---------|-------------|
| Cookie 安全属性 | Secure/HttpOnly/SameSite | 多维防护 |
| 第三方 Cookie | 跨站追踪的基础 | 正在被淘汰 |
| Privacy Sandbox | Topics/Protected Audience | 隐私保护替代 |
| CHIPS | 分区 Cookie | 嵌入式服务方案 |
| Storage Access API | 请求式存储访问 | 用户授权 |
| 存储分区 | 所有存储 API | 防跨站关联 |

觉得有用？收藏起来，下次处理 Cookie 和隐私问题时直接翻。

你的项目还在用第三方 Cookie 吗？有迁移计划吗？评论区聊聊。

关注怕浪猫，下期我们进入性能优化，讲 Core Web Vitals。系列进度 16/24。

下期预告：第 17 章「Core Web Vitals 与性能指标」。我们会拆解 LCP（Largest Contentful Paint，最大内容绘制）、INP（Interaction to Next Paint，交互到下次绘制）、CLS（Cumulative Layout Shift，累积布局偏移）三大指标的测量原理和优化策略。怕浪猫下期见。

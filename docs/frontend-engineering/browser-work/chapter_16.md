---
sidebar_position: 16
---

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

## 16.6 CHIPS 分区 Cookie

### 16.6.1 什么是分区 Cookie

CHIPS（Cookies Having Independent Partitioned State，分区独立 Cookie）是 Chrome 113 引入的机制，通过 Partitioned 属性让第三方 Cookie 按顶级站点分区存储。

```
传统第三方 Cookie：
  用户访问 site-a.com，嵌入 ad.com 的广告
  → ad.com 设置 Cookie: id=abc
  用户访问 site-b.com，嵌入 ad.com 的广告
  → ad.com 读取 Cookie: id=abc（跨站追踪！）

分区 Cookie（CHIPS）：
  用户访问 site-a.com，嵌入 ad.com
  → ad.com 设置 Cookie: id=abc; Partitioned
  Cookie 存储为：{ partition: site-a.com, domain: ad.com, value: abc }

  用户访问 site-b.com，嵌入 ad.com
  → ad.com 无法读取 abc（分区不同）
  → 只能设置新的分区 Cookie
  → 不跨站追踪
```

```http
# 设置分区 Cookie
Set-Cookie: __Host-session=abc123; Secure; Path=/; SameSite=None; Partitioned
```

| 对比 | 传统第三方 Cookie | 分区 Cookie |
|------|----------------|------------|
| 跨站追踪 | 可以 | 不可以 |
| 存储方式 | 按域名 | 按域名 + 顶级站点 |
| 需要属性 | 无 | Partitioned |
| 安全要求 | 无 | Secure + SameSite=None |

> CHIPS 的核心思想是「允许第三方 Cookie 存在，但不允许跨站追踪」。每个顶级站点有独立的 Cookie 分区，第三方服务可以存储状态（如登录会话），但无法跨站关联用户行为。这是第三方 Cookie 淘汰后的过渡方案。

## 16.7 第一方集机制

### 16.7.1 First-Party Sets

First-Party Sets（第一方集）允许相关联的域名声明属于同一个「第一方」，从而在这些域名间共享第一方身份。例如，brand.com 和 shop.brand.com 可以声明为同一第一方集。

```json
// first-party-sets.json
{
  "primary": "https://brand.com",
  "members": [
    "https://shop.brand.com",
    "https://api.brand.com",
    "https://cdn.brand.com"
  ]
}
```

```
无 First-Party Sets：
  brand.com → Cookie: session=abc（第一方）
  shop.brand.com → 需要单独设置 Cookie

有 First-Party Sets：
  brand.com + shop.brand.com + api.brand.com
  → 声明为同一第一方
  → Cookie session=abc 在三个域名间共享
  → 不被视为第三方 Cookie
```

> First-Party Sets 解决了企业多域名场景下的 Cookie 共享问题。没有它，第三方 Cookie 淘汰后，brand.com 和 shop.brand.com 之间的会话共享会变成「第三方 Cookie」而被阻止。这个机制需要域名在 .well-known/first-party-set 声明成员关系，且 Chrome 验证后才生效。

## 16.8 Storage Access API

### 16.8.1 用户授权的跨站存储访问

Storage Access API 让嵌入的第三方内容通过用户授权来访问其第一方存储。

```javascript
// 第三方 iframe 中请求存储访问
document.requestStorageAccess().then(() => {
  // 现在可以访问第一方 Cookie
  console.log('获得存储访问权限');
}).catch(() => {
  // 用户拒绝或浏览器阻止
  console.log('存储访问被拒绝');
});

// 检查是否有权限
const hasAccess = await document.hasStorageAccess();
```

```
Storage Access API 流程

  1. 第三方 iframe 调用 requestStorageAccess()
  2. 浏览器检查是否之前已授权
     → 已授权：直接返回
     → 未授权：弹出权限提示
  3. 用户选择
     → 同意：iframe 获得第一方 Cookie 访问
     → 拒绝：Promise reject
  4. 权限有效期：30 天
```

| 对比 | 第三方 Cookie | Storage Access API |
|------|-------------|-------------------|
| 用户感知 | 无 | 有（弹窗） |
| 粒度 | 全局 | 按站点 |
| 控制 | 浏览器设置 | 用户逐次授权 |
| 追踪风险 | 高 | 低 |

## 16.9 存储分区

### 16.9.1 Storage Partitioning

存储分区是浏览器将 IndexedDB、LocalStorage、Cache Storage 等按顶级站点分区的机制。这与 CHIPS 的 Cookie 分区类似，但覆盖所有存储 API。

```
存储分区结构

  顶级站点: https://site-a.com
    ├─ IndexedDB
    │   ├─ site-a.com 的数据库
    │   └─ embedded-third-party.com 的数据库（分区）
    ├─ LocalStorage
    │   ├─ site-a.com 的存储
    │   └─ embedded-third-party.com 的存储（分区）
    └─ Cache Storage
        └─ 同样分区

  顶级站点: https://site-b.com
    └─ embedded-third-party.com 的存储
        → 与 site-a 中的完全隔离
```

| 存储 API | 分区前 | 分区后 |
|---------|--------|--------|
| IndexedDB | 按域名 | 按顶级站点 + 域名 |
| LocalStorage | 按域名 | 按顶级站点 + 域名 |
| Cache Storage | 按域名 | 按顶级站点 + 域名 |
| Cookie | 按域名 | 按顶级站点 + 域名（CHIPS） |

> 存储分区是隐私保护的底层机制。它确保第三方服务在不同网站中的存储互相隔离，无法通过共享存储来追踪用户。这对于 Service Worker 也有影响——嵌入的第三方 Service Worker 在不同网站上会注册为不同的实例。

## 16.10 隐私预算

### 16.10.1 Privacy Budget 概念

隐私预算（Privacy Budget）是一种理论框架，限制网站在给定时间内可以获取的用户信息量。即使每个 API 单独看是安全的，组合使用多个 API 仍可能产生指纹。

```
隐私预算模型

  每个 API 调用消耗一定「隐私预算」
  
  User-Agent:        2 bits
  屏幕分辨率:        5 bits
  时区:             3 bits
  语言:             2 bits
  Canvas 指纹:      15 bits
  WebGL 指纹:       12 bits
  ...
  
  总预算: 256 bits / 天
  超过预算 → API 返回通用值或报错
```

| 隐私机制 | 保护对象 | 状态 |
|---------|---------|------|
| 第三方 Cookie 淘汰 | 跨站追踪 | 进行中 |
| CHIPS | Cookie 跨站 | 已实现 |
| 存储分区 | 存储跨站 | 已实现 |
| Privacy Budget | 指纹追踪 | 研究中 |

> 隐私预算目前还在研究阶段，但代表了隐私保护的终极方向。它的核心思想是「不可能完全阻止指纹，但可以限制指纹的精度」。通过限制每天可获取的信息量，即使用户被指纹识别，也无法长期追踪。

## 16.11 Cookie 属性完整参考

### 16.11.1 Cookie 属性详解

现代 Cookie 有多个属性控制安全性和行为。理解每个属性的作用是 Web 安全的基础。

```http
Set-Cookie: session=abc123; 
  Domain=.example.com; 
  Path=/; 
  Max-Age=86400; 
  Secure; 
  HttpOnly; 
  SameSite=Lax; 
  Partitioned
```

| 属性 | 说明 | 示例 |
|------|------|------|
| Domain | 作用域名 | .example.com |
| Path | 作用路径 | /api |
| Max-Age | 过期时间（秒） | 86400 |
| Expires | 过期时间（日期） | Wed, 09 Jun 2026 |
| Secure | 仅 HTTPS | — |
| HttpOnly | JS 不可访问 | — |
| SameSite | 跨站策略 | Strict/Lax/None |
| Partitioned | 分区存储 | — |

### 16.11.2 SameSite 属性详解

```
SameSite 语义

Strict:
  → 完全禁止跨站发送 Cookie
  → 从其他网站点击链接过来也不带 Cookie
  → 最安全但体验差

Lax（Chrome 默认）:
  → 顶级导航的 GET 请求带 Cookie
  → 其他跨站请求不带
  → 平衡安全与体验

None:
  → 允许跨站发送
  → 必须同时设置 Secure
  → 第三方 Cookie 场景
```

| 场景 | Strict | Lax | None |
|------|--------|-----|------|
| 同站请求 | 发送 | 发送 | 发送 |
| 跨站链接 | 不发送 | 发送(GET) | 发送 |
| 跨站 POST | 不发送 | 不发送 | 发送 |
| 跨站 iframe | 不发送 | 不发送 | 发送 |

## 16.12 Privacy Sandbox 提案

### 16.12.1 Privacy Sandbox 全景

Privacy Sandbox 是 Google 提出的一系列隐私提案，旨在第三方 Cookie 淘汰后维持广告生态运作。

```
Privacy Sandbox 提案分类

广告相关：
  Topics API → 基于兴趣的广告（替代第三方 Cookie）
  Protected Audience API → 再营销广告
  Attribution Reporting → 广告归因

反欺诈：
  Private State Tokens → 反机器人
  Trust Tokens → 信任令牌

其他：
  FedCM → 联邦登录
  Storage Access API → 跨站存储授权
```

| 提案 | 替代功能 | 状态 |
|------|---------|------|
| Topics API | 兴趣追踪 | 试用中 |
| Protected Audience | 再营销 | 试用中 |
| Attribution Reporting | 转化追踪 | 试用中 |
| FedCM | 跨站登录 | 试用中 |
| Private State Tokens | 反欺诈 | 试用中 |

```javascript
// Topics API 示例
// 浏览器根据用户浏览历史生成兴趣主题
document.b Topics.observe({ topics: ['sports', 'tech'] });

// 广告商可以获取用户主题（最近 3 周）
const topics = await document.b Topics.getTopics();
// [{ topic: 'sports', version: 'v1' }]
```

> Privacy Sandbox 的核心思想是「让浏览器成为中间人」。用户数据留在浏览器中，不再需要第三方追踪。广告商只能获取聚合后的、经过差分隐私处理的信号。这比第三方 Cookie 隐私性更好，但功能上也更有限。

## 16.13 浏览器指纹防护

### 16.13.1 指纹技术分类

浏览器指纹（Browser Fingerprinting）是一种不依赖 Cookie 的用户追踪技术。它通过收集浏览器和设备的特征信息，生成唯一标识。

```
指纹技术分类

1. 基本指纹（精度：中）
   → User-Agent、语言、时区
   → 屏幕分辨率、色深
   → 浏览器版本、插件列表

2. Canvas 指纹（精度：高）
   → 绘制特定图形，读取像素值
   → 不同 GPU/驱动渲染结果不同
   → 识别率 > 99%

3. WebGL 指纹（精度：高）
   → 读取 GPU 信息和渲染特征
   → GPU 型号 + 驱动版本 = 唯一标识

4. 音频指纹（精度：高）
   → AudioContext 生成音频信号
   → 不同音频硬件产生不同结果

5. 字体指纹（精度：中）
   → 检测已安装字体列表
   → 通过测量文字宽度判断字体
```

| 指纹技术 | 识别率 | 用户提供信息 |
|---------|--------|------------|
| Canvas | > 99% | 不可拒绝 |
| WebGL | > 98% | 不可拒绝 |
| Audio | > 95% | 不可拒绝 |
| 字体 | > 85% | 不可拒绝 |
| 基本指纹 | > 70% | 部分可拒绝 |

```javascript
// Canvas 指纹原理
function canvasFingerprint() {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.textBaseline = 'top';
  ctx.font = '16px Arial';
  ctx.fillText('Browser Fingerprint 🔍', 2, 2);
  return canvas.toDataURL(); // 不同设备产生不同结果
}
```

### 16.13.2 Chrome 的指纹防护

```
Chrome 指纹防护策略

1. 主动冻结（Freezing）
   → 冻结 User-Agent 字符串
   → 减少 UA 中的版本信息
   → UA-CH（User-Agent Client Hints）替代

2. 噪声注入
   → Canvas 指纹添加随机噪声
   → 每次 API 调用结果略有不同
   → 仅在隐身模式启用

3. 权限限制
   → 需要 Permission 的 API 统一管理
   → Notification、Geolocation 等
   → 拒绝默认 = 无法指纹

4. 定期清理
   → Site Data 清理
   → IndexedDB、LocalStorage 等
   → 减少可追踪时间窗口
```

> 指纹防护的核心矛盾是「可用性 vs 隐私」。完全阻止指纹需要禁用 Canvas、WebGL、Audio 等 API，但这样会导致大量网站无法使用。Chrome 的策略是逐步减少可指纹的信息量（如冻结 UA），同时在隐身模式中提供更强的防护。

## 16.14 第三方 Cookie 淘汰

### 16.14.1 淘汰时间线与影响

```
第三方 Cookie 淘汰时间线

2019: Google 宣布计划淘汰第三方 Cookie
2020: Sandcastle API 提出后改名 Privacy Sandbox
2022: Topics API、Protected Audience API 开始试用
2024: 第三方 Cookie 逐步淘汰
     → Phase 1: 1% 用户禁用
     → Phase 2: 100% 用户禁用
2025+: 完全淘汰

影响范围：
  广告追踪: 受影响最大
  跨站登录: 部分受影响（FedCM 替代）
  第三方组件: 需要适配
```

| 场景 | 第三方 Cookie 用途 | 替代方案 |
|------|-----------------|----------|
| 广告追踪 | 跨站追踪用户 | Topics API |
| 再营销 | 标记访客 | Protected Audience |
| 转化追踪 | 测量广告效果 | Attribution Reporting |
| 跨站登录 | 保持登录状态 | FedCM |
| 嵌入内容 | 个性化内容 | Storage Access API |

> 第三方 Cookie 淘汰不是「禁用追踪」，而是「改变追踪方式」。从「服务端追踪」（第三方 Cookie）转向「客户端追踪」（Privacy Sandbox API）。用户数据不再发送到广告商服务器，而是由浏览器本地处理，只返回聚合后的、差分隐私保护的信号。

## 16.15 存储分区与隔离

### 16.15.1 Storage Partitioning

存储分区（Storage Partitioning）是 Chrome 的新安全特性。它将每个网站的存储按顶级站点隔离，防止跨站追踪。

```
存储分区前

site-a.com 嵌入 youtube.com iframe
site-b.com 也嵌入 youtube.com iframe

YouTube 在两个站点中共享同一个 LocalStorage
→ 可用于跨站追踪用户

存储分区后

site-a.com 嵌入 youtube.com → 分区 A
site-b.com 嵌入 youtube.com → 分区 B

YouTube 在两个站点中看到不同的 LocalStorage
→ 无法跨站追踪
```

| 存储类型 | 分区前 | 分区后 |
|---------|--------|--------|
| LocalStorage | 按 origin 共享 | 按顶级站点分区 |
| IndexedDB | 按 origin 共享 | 按顶级站点分区 |
| SessionStorage | 按 origin 共享 | 按顶级站点分区 |
| Cache API | 按 origin 共享 | 按顶级站点分区 |
| Cookie | 按 domain 共享 | CHIPS 分区 |

### 16.15.2 Storage Access API

存储分区后，嵌入式内容需要跨分区访问存储时，使用 Storage Access API 请求权限。

```javascript
// Storage Access API
async function requestStorageAccess() {
  if (document.requestStorageAccess) {
    try {
      const hasAccess = await document.requestStorageAccess();
      if (hasAccess) {
        // 现在可以访问未分区的存储
        localStorage.getItem('sharedKey');
      }
    } catch (e) {
      // 用户拒绝了存储访问请求
      console.log('Storage access denied');
    }
  }
}
```

> Storage Access API 是存储分区与用户体验之间的平衡点。完全禁止跨分区访问会破坏嵌入式应用（如 YouTube、Google Maps），但无条件允许又等于没有分区。Storage Access API 让用户决定是否信任嵌入内容，类似权限提示。

## 16.16 FedCM 联邦登录

### 16.16.1 FedCM 原理

FedCM（Federated Credential Management，联邦凭证管理）是 Privacy Sandbox 的登录提案。它替代第三方 Cookie 实现跨站单点登录，无需第三方 Cookie。

```
FedCM 登录流程

1. 用户访问 site-a.com
   → site-a.com 调用 navigator.credentials.get()
   → 指定 identity provider: idp.com

2. 浏览器弹出登录提示
   → 显示 IdP 名称和图标
   → 用户选择 IdP 账号

3. 浏览器与 IdP 通信
   → 获取 ID Token
   → 不经过 site-a.com 的 JavaScript
   → 防止 IdP 追踪用户在 site-a.com 的行为

4. site-a.com 获取 Token
   → 验证 Token 完成登录
```

```javascript
// FedCM 客户端调用
async function loginWithIdP() {
  const credential = await navigator.credentials.get({
    identity: {
      providers: [{
        configURL: 'https://idp.com/fedcm.json',
        clientId: 'site-a-client-id',
      }]
    }
  });
  // credential.token = ID Token
  // 发送到 site-a.com 服务器验证
  await fetch('/api/login', {
    method: 'POST',
    body: JSON.stringify({ token: credential.token }),
  });
}
```

| 对比 | 第三方 Cookie 登录 | FedCM |
|------|------------------|-------|
| 追踪风险 | 高 | 低 |
| 用户体验 | 重定向 | 原生弹窗 |
| 实现复杂度 | 中 | 低 |
| 隐私保护 | 无 | 有 |

> FedCM 的核心优势是「中介隔离」。浏览器作为用户和 IdP 之间的中介，IdP 不知道用户在哪个网站上登录。这切断了 IdP 的追踪能力。用户也不需要经历烦人的重定向流程，直接在当前页面选择 IdP 账号即可。

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

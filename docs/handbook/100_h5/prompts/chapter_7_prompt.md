# Chapter 7 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「iframe 与跨域通讯」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源（MDN / WHATWG）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第7章：iframe 与跨域通讯

7.1 iframe 的基本用法与安全风险
- <iframe src="..."> 嵌入外部页面
- 安全风险：点击劫持（Clickjacking）、钓鱼攻击、恶意脚本注入
- sandbox 属性限制权限（allow-scripts / allow-same-origin 等按需开启）
- X-Frame-Options: DENY / SAMEORIGIN
- CSP（Content Security Policy）frame-ancestors
- 安全风险与防护措施对照表
- 核心代码：sandbox 属性配置、X-Frame-Options 响应头

7.2 postMessage API 详解与安全实践
- 发送：iframe.contentWindow.postMessage(data, targetOrigin)
- 接收：window.addEventListener('message', e => { e.origin / e.source / e.data })
- 安全要求：校验 event.origin、指定 targetOrigin（不用 *）、验证数据格式、避免 eval
- postMessage 通讯流程图
- 核心代码：安全的 postMessage 发送与接收

7.3 iframe 双向通讯实现
- 父 -> 子：iframeEl.contentWindow.postMessage()
- 子 -> 父：window.parent.postMessage()（或 window.top 到顶层）
- 多层级 iframe：逐层传递或直接 window.top
- 双向通讯模式：请求-响应（callbackId 机制）、事件订阅/发布
- 多层 iframe 通讯拓扑图
- 核心代码：请求-响应模式封装、事件总线实现

7.4 iframe 的性能影响与优化
- 每个 iframe 创建独立浏览上下文（DOM/CSSOM/JS 引擎），开销大
- 阻塞父页面 onload 事件
- 优化：loading="lazy" 延迟加载、动态创建 iframe
- 设置 width/height 避免布局偏移
- 避免嵌套 iframe
- Shadow DOM 或 Portal API 替代部分场景
- 性能影响对比表
- 核心代码：懒加载 iframe、动态创建与销毁

7.5 iframe 内部页面的 Cookie / LocalStorage 共享机制
- 同源 iframe 共享 Cookie / LocalStorage / SessionStorage
- 跨域 iframe 各自独立存储
- 第三方 Cookie 被 Safari / Chrome 逐步限制（SameSite 默认 Lax）
- iframe 内登录态传递方案：postMessage 传递 Token / window.name / URL hash
- 存储隔离模型图
- 核心代码：postMessage 传递 Token、window.name 方案

7.6 X-Frame-Options 与 CSP frame-ancestors 对比
- X-Frame-Options（HTTP 头）：DENY / SAMEORIGIN / ALLOW-FROM（已废弃）
- CSP frame-ancestors（HTTP 头或 meta）：支持多源、通配符、现代浏览器优先级更高
- 两者差异对比表格
- 配合使用确保兼容性
- 核心代码：Nginx 配置 X-Frame-Options 与 CSP frame-ancestors

7.7 第三方 Cookie 限制下的 iframe 跨域方案
- Chrome 逐步淘汰第三方 Cookie 的影响
- 替代方案：
  - SameSite=None; Secure（短期仍可用）
  - Storage Access API（document.requestStorageAccess()）
  - CHIPS（Partitioned Cookie）
  - First-Party Set
- iframe 内登录态改用 postMessage 传递 Token + LocalStorage 存储
- 方案演进时间线
- 核心代码：Storage Access API 使用、postMessage + LocalStorage 方案

7.8 iframe 自适应高度实现
- 同源：iframe 内 document.body.scrollHeight -> 父页面设置 iframe 高度
- 跨域：postMessage 传递高度
- ResizeObserver 监听内容高度变化
- iOS Safari 的 iframe 滚动问题（scrolling="no" + 内部容器滚动）
- 核心代码：同源自适应高度、跨域 postMessage 方案、ResizeObserver

7.9 Portal API：iframe 的未来替代品
- <portal> 原生预渲染跨域页面，可无缝过渡到顶层窗口
- 优势：比 iframe 性能更好、原生预览、无 JS 上下文隔离问题
- 兼容性：Chrome 已实现，Safari / Firefox 未跟进
- 不适合生产使用但值得关注
- 核心代码：Portal API 基本使用

7.10 微前端中 iframe 方案的优劣分析
- 优势：天然样式隔离、JS 隔离、接入零改造
- 劣势：性能差（多浏览器上下文）、通讯复杂（postMessage）、SEO 不友好、路由丢失、UI 割裂感（弹窗无法全屏）
- 适用场景：快速集成第三方页面、对性能要求不高的后台系统
- 优劣对比表格
- 核心代码：iframe 微前端基本架构

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"iframe是前端最古老的跨域方案，但90%的人只知道postMessage，不知道安全陷阱"
后跟IP自我介绍："我是怕浪猫，一个把iframe各种坑都踩过一遍的前端工程师"

**金句（至少3个）：**
> postMessage的targetOrigin不是可选项，是安全底线

**收藏触发结构：**
- 对比型："X-Frame-Options vs CSP frame-ancestors 对比表"
- 清单型："第三方Cookie限制下的5种替代方案"

**结尾CTA：**
1. 收藏引导："这篇iframe安全与跨域通讯指南，收藏起来排查问题时直接查"
2. 互动引导："你在iframe跨域通讯踩过哪个坑？评论区说说"
3. 追更引导："关注怕浪猫，下期讲跨端通讯机制总览" + "系列进度 7/10"

**下章预告：**
"下一篇拆解H5与Native全链路通讯、JS Bridge回调管理、跨端事件总线、多端统一API设计。"

####

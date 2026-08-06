# 前端 H5 / 浏览器 / 多端兼容 · 100 道高频面试题

> 按知识体系划分为 **10 个章节**，每章约 10 题。  
> 每题标注 **分类** 与 **特点**，方便按需取舍。  
> 覆盖：H5 基础、浏览器与设备兼容、性能优化、WebView/小程序/iframe 跨端通讯、响应式、微前端、用户体验与业务价值。

---

## 目录

| 章节 | 主题 | 题数 |
|------|------|------|
| [一](#一h5-基础与语义化) | H5 基础与语义化 | 10 |
| [二](#二浏览器渲染原理与兼容性) | 浏览器渲染原理与兼容性 | 10 |
| [三](#三多设备适配与响应式布局) | 多设备适配与响应式布局 | 10 |
| [四](#四h5-性能优化核心) | H5 性能优化核心 | 11 |
| [五](#五webview-与-app-集成) | WebView 与 App 集成 | 10 |
| [六](#六小程序与-h5-的交互) | 小程序与 H5 的交互 | 10 |
| [七](#七iframe-与跨域通讯) | iframe 与跨域通讯 | 10 |
| [八](#八跨端通讯机制总览) | 跨端通讯机制总览 | 10 |
| [九](#九微前端架构) | 微前端架构 | 10 |
| [十](#十用户体验与业务价值) | 用户体验与业务价值 | 9 |

---

## 一、H5 基础与语义化

### 1. HTML5 新增了哪些语义化标签？它们解决了什么问题？
- **分类**：基础知识
- **特点**：高频必问 · 考察对语义化的理解深度
- **要点**：`<header>` `<nav>` `<main>` `<article>` `<section>` `<aside>` `<footer>` 等；解决 div 命名混乱、利于 SEO、无障碍阅读、代码可维护性。

### 2. H5 离线存储方案有哪些？它们的区别和适用场景？
- **分类**：存储与缓存
- **特点**：高频 · 考察存储体系全貌
- **要点**：LocalStorage / SessionStorage / IndexedDB / Cache API / Application Cache（已废弃）→ Service Worker。从容量、时效、异步性、是否支持结构化数据等维度对比。

### 3. Service Worker 的生命周期是什么？如何实现离线可用？
- **分类**：PWA / 离线
- **特点**：中高频 · 考察 PWA 核心
- **要点**：install → activate → fetch 事件拦截；Cache API 缓存静态资源，实现"离线优先"策略（Cache First / Network First / Stale-While-Revalidate）。

### 4. HTML5 的 input 类型有哪些？如何利用它们提升移动端表单体验？
- **分类**：表单与交互
- **特点**：实用 · 直接影响用户体验
- **要点**：`type="email|tel|number|date|url|search"` 等；移动端自动弹出对应键盘（数字键盘、邮箱键盘），减少输入摩擦；配合 `pattern` 做前端校验。

### 5. 什么是 Web Storage 的事件机制？如何实现多标签页数据同步？
- **分类**：存储 / 多标签通讯
- **特点**：中频 · 考察跨标签通讯
- **要点**：`window.addEventListener('storage', ...)` 在同源其他标签页触发；可用于多标签登录状态同步、购物车同步。

### 6. Cookie、Session、Token 在前端如何使用？H5 时代有什么变化？
- **分类**：认证与安全
- **特点**：高频 · 前后端边界知识
- **要点**：Cookie 字段（httpOnly、secure、sameSite）；JWT 前端存储方案对比（LocalStorage vs Cookie）；SameSite=None + Secure 在跨域 Cookie 中的必要性。

### 7. H5 的 Geolocation、DeviceOrientation 等 API 如何使用？有什么限制？
- **分类**：设备能力
- **特点**：中频 · 考察原生能力调用
- **要点**：`navigator.geolocation.getCurrentPosition()` 获取定位；`DeviceOrientationEvent` 获取陀螺仪/加速度计；HTTPS 强制要求、用户授权弹窗、iOS 13+ 需 `requestPermission()`。

### 8. WebSocket 与 SSE 的区别？在 H5 实时通讯中如何选择？
- **分类**：实时通讯
- **特点**：中高频 · 架构选型
- **要点**：WebSocket 双工、二进制、较低协议开销；SSE 单向（服务端推送）、纯文本、自动重连、HTTP 兼容性好。IM/游戏选 WebSocket，通知推送/股票行情选 SSE。

### 9. H5 拖放 API（Drag and Drop）的实现原理与移动端兼容问题？
- **分类**：交互 API
- **特点**：低频但加分 · 考察兼容意识
- **要点**：`dragstart/dragover/drop` 事件链；移动端不支持原生 DnD，需用 Touch 事件模拟或使用 polyfill（如 `interact.js`）。

### 10. Canvas 与 SVG 的区别？在 H5 可视化中如何选型？
- **分类**：图形与可视化
- **特点**：中频 · 架构选型
- **要点**：Canvas 位图、高性能、适合大量元素动画（游戏、热力图）；SVG 矢量、DOM 可操作、适合图表、地图、可交互图形。分辨率自适应选 SVG，高性能渲染选 Canvas（或 WebGL）。

---

## 二、浏览器渲染原理与兼容性

### 11. 从输入 URL 到页面渲染完成，浏览器做了什么？
- **分类**：浏览器原理
- **特点**：超高频必问 · 全链路理解
- **要点**：DNS 解析 → TCP/TLS 握手 → HTTP 请求/响应 → HTML 解析构建 DOM → CSS 解析构建 CSSOM → Render Tree → Layout（回流）→ Paint（重绘）→ Composite（合成）。每一步都可展开追问。

### 12. 浏览器的关键渲染路径（Critical Rendering Path）如何优化？
- **分类**：性能优化
- **特点**：高频 · 直接关联首屏性能
- **要点**：减少阻塞资源（defer/async 脚本、preload 关键资源、内联关键 CSS）；减少 DOM 节点数；避免强制同步布局（layout thrashing）。

### 13. 什么是回流（Reflow）和重绘（Repaint）？如何最小化？
- **分类**：渲染性能
- **特点**：高频 · 编码实践直接相关
- **要点**：回流 = 几何属性变化触发重新布局；重绘 = 外观属性变化不触发布局；合成 = 仅 GPU 层合成（transform/opacity 最优）。使用 `will-change`、`transform` 替代 `top/left`、批量 DOM 修改（DocumentFragment / `display:none` 修改再恢复）。

### 14. 浏览器进程与线程模型是怎样的？前端能做什么？
- **分类**：浏览器原理
- **特点**：中高频 · 考察系统性理解
- **要点**：浏览器多进程（Browser/Renderer/GPU/Plugin）；Renderer 进程内多线程（主线程 JS 执行、合成线程、解析线程）。前端避免长时间阻塞主线程，用 Web Worker 做计算密集任务，用 `requestIdleCallback` 做低优先级任务。

### 15. CSS Hack 与浏览器前缀的最佳实践？
- **分类**：CSS 兼容
- **特点**：中频 · 工程化相关
- **要点**：`-webkit-` `-moz-` `-ms-` 前缀；现代方案用 Autoprefixer + PostCSS 自动处理；特征检测用 `@supports` 而非 UA 嗅探；caniuse.com 查兼容性。

### 16. 如何处理 IE/Edge Chromium/Safari/Chrome 的兼容性问题？
- **分类**：跨浏览器兼容
- **特点**：高频 · 实战必备
- **要点**：Babel 转译 ES6+；Polyfill（core-js）补 API；CSS fallback 写法；Safari 独有坑（`100vh` 问题、`position:sticky` 前缀、日期格式解析）；feature detection 优于 UA 判断。

### 17. 浏览器缓存机制（强缓存 / 协商缓存）的完整流程？
- **分类**：缓存策略
- **特点**：高频 · 前端 + 后端 + 运维交叉
- **要点**：`Cache-Control` / `Expires`（强缓存）→ `Last-Modified` / `ETag`（协商缓存）；命中顺序、状态码（200 from cache vs 304）；Service Worker 缓存层介入后的三层缓存体系。

### 18. 跨域问题的根本原因与所有解决方案？
- **分类**：网络与安全
- **特点**：超高频 · 必须全面掌握
- **要点**：同源策略（协议+域名+端口）；CORS（简单请求 vs 预检请求 `OPTIONS`，`Access-Control-Allow-Origin` 等）；代理（Nginx / Node 中间层）；`postMessage` 跨文档通讯；JSONP 原理与局限。

### 19. 浏览器的垃圾回收机制（V8）对前端编码有什么影响？
- **分类**：内存管理
- **特点**：中频 · 考察内存意识
- **要点**：V8 分代回收（新生代 Scavenge / 老生代 Mark-Sweep + Mark-Compact）；避免内存泄漏（未清除的定时器、闭包持有大对象、脱离 DOM 树的引用、全局变量）；WeakMap/WeakSet 配合 GC。

### 20. 什么是浏览器的合成层（Compositing Layer）？如何利用 GPU 加速？
- **分类**：渲染性能
- **特点**：中高频 · 动画性能关键
- **要点**：触发合成层的条件（3D transform、will-change、video、canvas、opacity 动画）；合成层将绘制交给 GPU，主线程不参与；避免"层爆炸"（过多合成层消耗内存）。

---

## 三、多设备适配与响应式布局

### 21. 响应式设计的核心原则与实现方案？
- **分类**：响应式布局
- **特点**：高频 · 基础必备
- **要点**：Media Query（`@media`）、弹性布局（Flexbox/Grid）、相对单位（rem/em/vw/vh/%）、`<picture>` / `srcset` 响应式图片、移动优先 vs 桌面优先策略。

### 22. rem / em / vw / vh / px / rpx 的区别与使用场景？
- **分类**：CSS 单位
- **特点**：高频 · 编码细节
- **要点**：px 绝对像素；em 相对父元素 font-size；rem 相对根元素；vw/vh 相对视口；rpx 小程序专用（750rpx = 屏宽）。移动端常用 rem + JS 动态设置 root font-size，或纯 vw 方案。

### 23. 移动端 1px 边框问题的原因与解决方案？
- **分类**：移动端兼容
- **特点**：高频 · 经典问题
- **要点**：设备像素比（DPR）> 1 时，CSS 1px 在物理像素上 > 1px；解决方案：`transform: scaleY(0.5)` 伪元素、`border-image`、`box-shadow` 模拟、viewport meta 缩放 + rem 联动。

### 24. 移动端点击延迟（300ms）的原因与解决？
- **分类**：移动端交互
- **特点**：中高频 · 体验优化
- **要点**：早期浏览器为判断双击缩放等待 300ms；解决方案：`<meta name="viewport" content="width=device-width">`（现代浏览器已消除延迟）、FastClick 库（历史方案）、CSS `touch-action: manipulation`。

### 25. 安全区适配（刘海屏 / 底部 Home 条）如何实现？
- **分类**：移动端适配
- **特点**：中高频 · 现代必备
- **要点**：`viewport-fit=cover` + `env(safe-area-inset-*)` / `constant(safe-area-inset-*)`（iOS < 13.2）；底部固定栏加 `padding-bottom: env(safe-area-inset-bottom)`。

### 26. Flexbox 与 Grid 布局的差异与选择？
- **分类**：布局方案
- **特点**：高频 · 日常布局核心
- **要点**：Flexbox 一维（行或列）、适合组件级布局；Grid 二维、适合页面级布局；可混合使用；Grid 的 `grid-template-areas` 适合响应式重排。

### 27. 移动端软键盘弹出导致页面布局错乱怎么办？
- **分类**：移动端兼容
- **特点**：中频 · 实战痛点
- **要点**：iOS 键盘弹起不改变视口高度（`visualViewport` API 监听变化）；Android 键盘弹起会缩小 `window.innerHeight`；解决方案：`visualViewport.addEventListener('resize')` 动态调整、`env(keyboard-inset-height)`（实验性）、避免 `100vh` 固定高度。

### 28. 图片适配方案：响应式图片、懒加载、格式选择？
- **分类**：媒体适配
- **特点**：高频 · 性能 + 体验
- **要点**：`<picture>` + `<source>` 多格式/多尺寸；`loading="lazy"` 原生懒加载；WebP/AVIF 格式兼容（`<picture>` fallback）；`srcset` + `sizes` 按 DPR 适配；`aspect-ratio` 防止布局偏移（CLS）。

### 29. 横屏与竖屏的适配方案？
- **分类**：响应式布局
- **特点**：中频 · 特定场景
- **要点**：`orientation: landscape/portrait` Media Query；`screen.orientation` API 读取/锁定方向（需用户手势）；横屏布局重排策略（Grid areas 重定义）。

### 30. 如何实现大屏数据可视化（1920×1080 → 4K → 超宽屏）的自适应？
- **分类**：大屏适配
- **特点**：中频 · 业务场景
- **要点**：`transform: scale()` 等比缩放方案（rem + scale）；ECharts `resize()` 监听容器变化；`clamp()` 限制极端尺寸；`Container Query`（新特性）实现组件级响应式。

---

## 四、H5 性能优化核心

### 31. 前端性能指标体系：Core Web Vitals 指什么？如何度量？
- **分类**：性能指标
- **特点**：高频 · Google 标准
- **要点**：LCP（Largest Contentful Paint ≤ 2.5s）、INP（Interaction to Next Paint ≤ 200ms）、CLS（Cumulative Layout Shift ≤ 0.1）；Lighthouse / PageSpeed Insights / Chrome DevTools Performance / `web-vitals` 库。

### 32. 首屏加载（FCP/LCP）优化的完整策略？
- **分类**：性能优化
- **特点**：高频 · 核心业务价值
- **要点**：资源层（压缩、Tree Shaking、Code Splitting、HTTP/2 多路复用）；加载层（preload 关键资源、prefetch 下一页、lazy-load 非首屏图片/组件）；渲染层（SSR/SSG、骨架屏、关键 CSS 内联）；网络层（CDN、Brotli 压缩、DNS Prefetch）。

### 33. 长列表（万级数据）渲染性能优化方案？
- **分类**：渲染性能
- **特点**：高频 · 编码能力
- **要点**：虚拟列表（Virtual List）只渲染可视区域 DOM（react-window / vue-virtual-scroller）；分页加载 + 无限滚动；`content-visibility: auto` CSS 新特性让浏览器跳过离屏渲染。

### 34. JavaScript 包体积优化的手段？
- **分类**：构建优化
- **特点**：高频 · 工程化
- **要点**：Tree Shaking（ESM 静态分析）；Code Splitting（路由级 + 组件级）；按需加载第三方库（lodash-es 替代 lodash、moment → dayjs）；Scope Hoisting；Babel `useBuiltIns: usage` 精确 polyfill；分析工具（webpack-bundle-analyzer / source-map-explorer）。

### 35. 图片优化全策略：格式、压缩、加载、缓存？
- **分类**：资源优化
- **特点**：高频 · 图片常占 50%+ 流量
- **要点**：格式（WebP/AVIF > JPEG/PNG，SVG 用于图标）；压缩（imagemin、TinyPNG）；响应式（srcset/picture）；加载（lazy、LQIP 低质量占位图、BlurHash）；缓存（Service Worker Cache）；CDN 图片处理（动态裁剪/格式转换）。

### 36. 动画性能优化：如何实现 60fps 流畅动画？
- **分类**：动画性能
- **特点**：中高频 · 体验直接相关
- **要点**：只动画化 `transform` 和 `opacity`（不触发 layout/paint）；使用 `requestAnimationFrame` 而非 `setInterval`；CSS 动画优于 JS 动画（合成线程处理）；`will-change` 提前声明合成层；避免 simultaneously animating 大量元素；Web Animations API。

### 37. 内存泄漏的排查与预防？
- **分类**：内存优化
- **特点**：中频 · 深度调试
- **要点**：Chrome DevTools Memory（Heap Snapshot / Allocation Timeline）；常见泄漏：未清除的 `setInterval`/`setTimeout`、事件监听器未移除、闭包引用、脱离 DOM 树的节点引用、全局变量；`WeakRef` / `FinalizationRegistry`（ES2021）；SPA 路由切换时清理。

### 38. 首屏白屏时间长的排查思路？
- **分类**：性能调试
- **特点**：高频 · 实战排障
- **要点**：Performance 面板看 Timeline（网络 → 解析 → 执行 → 渲染）；检查 TTFB（后端慢？DNS？）；检查 JS 执行时间（大 bundle？同步阻塞？）；检查渲染阻塞资源（CSS/同步 script）；方案：SSR/预渲染、骨架屏、defer/async、分块加载。

### 39. HTTP/2 与 HTTP/3 对前端性能的影响？
- **分类**：网络协议
- **特点**：中频 · 架构认知
- **要点**：HTTP/2 多路复用（消除雪碧图/域名分片的必要性）、Server Push、头部压缩（HPACK）；HTTP/3 基于 QUIC（UDP），解决队头阻塞、0-RTT 连接；前端需配合：减少请求数不再是首要目标、合理利用 Server Push、资源预加载。

### 40. 预加载策略：preload / prefetch / preconnect / dns-prefetch 的区别？
- **分类**：资源加载策略
- **特点**：中高频 · 精细优化
- **要点**：`preload`（高优先级加载当前页必需资源）、`prefetch`（低优先级预取下一页资源）、`preconnect`（提前建立 TCP/TLS 连接）、`dns-prefetch`（仅 DNS 解析）；`modulepreload`（预加载 ES 模块及其依赖）。

### 41. Web Worker 的使用场景与限制？
- **分类**：性能优化
- **特点**：中频 · 进阶手段
- **要点**：将计算密集任务（大数据处理、加密、图像处理）移出主线程；限制：不能操作 DOM、同源限制、通信开销（postMessage 序列化）；SharedArrayBuffer + Atomics 实现零拷贝共享（需 COOP/COEP 安全头）；OffscreenCanvas 将 Canvas 渲染移入 Worker。

---

## 五、WebView 与 App 集成

### 42. WebView 的本质是什么？iOS/Android 各有什么差异？
- **分类**：WebView 基础
- **特点**：高频 · 混合开发必问
- **要点**：WebView 是内嵌的浏览器引擎内核；iOS 用 WKWebView（WebKit），Android 用 WebView（Chromium，4.4+ 可调试）；差异：JS 引擎（JavaScriptCore vs V8）、缓存机制、Cookie 管理、权限模型。

### 43. JS Bridge 的实现原理是什么？
- **分类**：WebView 通讯
- **特点**：超高频 · Hybrid 核心
- **要点**：Native → JS：`evaluateJavascript` / `stringByEvaluatingJavaScriptFromString`；JS → Native：① URL Scheme 拦截（`window.location = 'myapp://action'`）；② `prompt`/`console.log` 拦截（Android `JsPromptResult`）；③ `postMessage`（Android `addJavascriptInterface` / iOS `WKScriptMessageHandler`）。现代方案多采用 `postMessage` 方式。

### 44. 如何设计一个通用 JS Bridge？
- **分类**：架构设计
- **特点**：中高频 · 架构能力
- **要点**：统一 API 签名（`bridge.call(action, params, callback)`）；回调队列管理（callbackId 映射）；Promise 化封装；事件订阅/发布机制；Native 调 JS 的回调解析；版本兼容与降级策略；权限与安全校验。

### 45. WebView 中的 Cookie 与 LocalStorage 如何与 Native 同步？
- **分类**：WebView 存储
- **特点**：中频 · 实战痛点
- **要点**：iOS WKWebView Cookie 不自动同步到 NSHTTPCookieStorage（iOS 11+ 改善）；Android Cookie 同步需 `CookieSyncManager`（已废弃）→ `CookieManager`；登录态打通方案：Native 注入 Token 到 WebView Header 或 JS Bridge 传递。

### 46. WebView 白屏/加载失败的排查与兜底？
- **分类**：WebView 调试
- **特点**：高频 · 生产排障
- **要点**：排查链路：网络（DNS/TLS）→ 资源 404/500 → JS 执行错误 → 渲染阻塞 → WebView 内核崩溃；方案：`onErrorReceived` 回调、WebViewClient 监听、加载失败页 + 重试按钮、前端 JS 错误上报、WebView 远程调试（Chrome://inspect / Safari）。

### 47. 如何提升 WebView 的首屏加载速度？
- **分类**：WebView 性能
- **特点**：高频 · 直接影响留存
- **要点**：预加载（App 启动时预热 WebView 实例池）；离线包（将 H5 资源打包到 App 本地，拦截请求返回本地文件）；懒加载 JS/CSS；服务端渲染（SSR）；WebView 复用池避免重复初始化开销；DNS 预解析 + 连接预建。

### 48. 离线包方案的设计与实现？
- **分类**：Hybrid 架构
- **特点**：中高频 · 大厂必问
- **要点**：资源打包 → 版本管理 → 增量更新（diff/patch）→ CDN 分发 → 客户端下载/解压 → WebView 拦截请求映射本地文件 → 更新策略（全量/增量、静默更新、用户触发）。竞品分析：美团/微信/支付宝离线包方案。

### 49. WebView 的安全风险与防护？
- **分类**：WebView 安全
- **特点**：中频 · 安全意识
- **要点**：`addJavascriptInterface` Android 4.2 以下远程代码执行漏洞；关闭 `file://` 域访问（`setAllowFileAccess(false)`）；限制可访问 URL 白名单；HTTPS 校验；JS Bridge 调用来源校验（`evaluateJavascript` 的 origin 检查）；防止 iframe 劫持。

### 50. 如何在 WebView 中调试 H5 页面？
- **分类**：WebView 调试
- **特点**：中频 · 实用技能
- **要点**：Android：`WebView.setWebContentsDebuggingEnabled(true)` → `chrome://inspect`；iOS：Safari → 开发 → 模拟器/设备名 → 选择页面；远程调试：Vorlon.js / Spy-js；vConsole / eruda 嵌入式调试面板（线上排查利器）。

### 51. App 内 H5 与原生的手势冲突如何处理？
- **分类**：WebView 交互
- **特点**：低频但加分 · 体验细节
- **要点**：侧滑返回手势与 H5 横向滚动冲突；方案：`gesture-nav` 属性控制、Native 侧判断触摸区域决定是否拦截；`touch-action` CSS 属性声明手势行为；JS Bridge 通知 Native 禁用/启用手势。

---

## 六、小程序与 H5 的交互

### 52. 小程序的基本架构是什么？与 H5 有什么本质区别？
- **分类**：小程序架构
- **特点**：高频 · 架构理解
- **要点**：双线程模型（渲染层 WebView + 逻辑层 JSCore/V8）；通过 Native 中转通讯；H5 单线程运行。小程序无法操作 DOM、无 BOM API、受限的网络请求（需配置域名白名单）。

### 53. 小程序 web-view 组件的使用与限制？
- **分类**：小程序与 H5 混合
- **特点**：高频 · 业务场景
- **要点**：`<web-view src="https://...">` 嵌入 H5 页面；限制：需配置业务域名、不支持小程序内 navigateBack（需 H5 主动调用）、全屏覆盖无法叠加原生组件（cover-view 有限支持）；登录态打通：H5 → 小程序通过 `postMessage`（仅在特定时机触发：分享、复制链接、小程序退出），小程序 → H5 通过 URL 参数传递。

### 54. 小程序与 H5 之间如何通讯？
- **分类**：跨端通讯
- **特点**：高频 · 实战核心
- **要点**：小程序 → web-view：通过 URL 参数传递数据（`src` 动态更新）；web-view → 小程序：`wx.miniProgram.postMessage(data)`（数据在特定时机才能被小程序收到：后退、组件销毁、分享、复制链接）；`wx.miniProgram.navigateTo/redirectTo` 在 H5 中跳转小程序页面；限制：实时双向通讯困难，需借助服务端中转（WebSocket/SSE）。

### 55. 小程序的性能优化策略？
- **分类**：小程序性能
- **特点**：中高频 · 直接影响体验
- **要点**：分包加载（主包缩小、按需加载子包）、独立分包（不依赖主包）、分包预下载；`wx.nextTick` 批量更新减少 setData 频次；减少 setData 数据量（只传变化字段）；图片懒加载 + 压缩；避免大节点 WXML；使用 `cover-view` 替代原生组件叠加。

### 56. 小程序 setData 的性能陷阱与优化？
- **分类**：小程序性能
- **特点**：高频 · 编码实践
- **要点**：setData 将数据从逻辑层序列化传到渲染层，有通讯开销；频繁 setData 导致卡顿；优化：合并多次 setData 为一次、只传变化的字段路径（`'list[0].name'`）、避免传输大量数据（图片 URL 用 CDN）、使用 `this.setData` 的回调做后续逻辑。

### 57. 小程序的登录流程与 H5 的登录态打通？
- **分类**：小程序登录
- **特点**：高频 · 业务必备
- **要点**：`wx.login()` → code → 服务端换 openid/session_key → 自定义登录态（Token）；H5 嵌入 web-view 时：通过 URL 参数传递 Token / 通过 JS Bridge（`wx.miniProgram.postMessage`）传递；Token 过期刷新机制；安全考虑（Token 不应暴露在 URL 中过久）。

### 58. 小程序条件渲染与列表渲染的性能优化？
 **分类**：小程序渲染
- **特点**：中频 · 编码细节
- **要点**：`wx:key` 必须唯一稳定（避免用 index）；大量列表用虚拟列表（`recycle-view` 组件 / `scroll-view` + 手动实现）；`hidden` vs `wx:if`（频繁切换用 `hidden`，条件少用 `wx:if`）；避免在 `scroll-view` 中频繁 setData。

### 59. 小程序的自定义组件与 H5 Web Components 的对比？
- **分类**：组件化
- **特点**：中频 · 架构对比
- **要点**：小程序 Component（类似 Vue 组件，有 data/methods/lifetimes）；Web Components（Custom Elements + Shadow DOM + HTML Templates）；小程序组件样式隔离（`styleIsolation`）；H5 微应用中 Web Components 提供天然样式隔离。

### 60. 小程序与 H5 的选择：什么时候用小程序，什么时候用 H5？
- **分类**：技术选型
- **特点**：中高频 · 架构决策
- **要点**：小程序优势：原生体验（组件/动画）、入口丰富（扫码/搜索/分享）、用户授权便捷（一键授权）；H5 优势：跨平台一次开发、迭代快速（无需审核）、SEO/外部分享灵活；策略：高频核心路径用小程序原生，活动页/营销页/第三方内容用 H5 web-view。

### 61. 小程序分包加载与预下载策略？
- **分类**：小程序架构
- **特点**：中频 · 优化进阶
- **要点**：主包 ≤ 2MB，总包 ≤ 20MB（微信）；分包按页面/功能划分；`preloadRule` 配置进入某页面时预下载其他分包；独立分包（不依赖主包，独立运行）适用于活动页；分包内资源按需加载。

---

## 七、iframe 与跨域通讯

### 62. iframe 的基本用法与安全风险？
- **分类**：iframe 基础
- **特点**：高频 · 安全意识
- **要点**：`<iframe src="...">` 嵌入外部页面；安全风险：点击劫持（Clickjacking）、钓鱼攻击、恶意脚本注入；防护：`sandbox` 属性限制权限（`allow-scripts` / `allow-same-origin` 等按需开启）、`X-Frame-Options: DENY/SAMEORIGIN`、`Content-Security-Policy: frame-ancestors`。

### 63. postMessage API 的使用与安全注意事项？
- **分类**：跨域通讯
- **特点**：超高频 · 必须掌握
- **要点**：发送：`iframe.contentWindow.postMessage(data, targetOrigin)`；接收：`window.addEventListener('message', e => { e.origin / e.source / e.data })`；安全：必须校验 `event.origin`、指定 `targetOrigin`（不用 `*`）、验证数据格式、避免 `eval` 处理数据。

### 64. iframe 之间如何实现双向通讯？
- **分类**：跨域通讯
- **特点**：高频 · 实战场景
- **要点**：父 → 子：`iframeEl.contentWindow.postMessage()`；子 → 父：`window.parent.postMessage()`（或 `window.top` 到顶层）；多层级 iframe：逐层传递或直接 `window.top`；双向通讯模式：请求-响应（callbackId 机制）、事件订阅/发布。

### 65. iframe 的性能影响与优化？
- **分类**：iframe 性能
- **特点**：中高频 · 性能优化
- **要点**：每个 iframe 创建独立的浏览上下文（DOM/CSSOM/JS 引擎），开销大；阻塞父页面 `onload` 事件；优化：`loading="lazy"` 延迟加载、动态创建 iframe、设置 `width/height` 避免布局偏移、避免嵌套 iframe、用 Shadow DOM 或 Portal API 替代部分场景。

### 66. iframe 内部页面的 Cookie / LocalStorage 是否共享？
- **分类**：iframe 存储
- **特点**：中频 · 跨域理解
- **要点**：同源 iframe 共享 Cookie/LocalStorage/SessionStorage；跨域 iframe 各自独立存储；第三方 Cookie 被 Safari/Chrome 逐步限制（`SameSite` 默认 Lax）；iframe 内登录态需通过 `postMessage` 传递 Token 或使用 `window.name` / URL hash 传递。

### 67. X-Frame-Options 与 CSP frame-ancestors 的区别？
- **分类**：iframe 安全
- **特点**：中频 · 安全配置
- **要点**：`X-Frame-Options`（HTTP 头）：`DENY` / `SAMEORIGIN` / `ALLOW-FROM`（已废弃，兼容性差）；`CSP frame-ancestors`（HTTP 头或 meta）：支持多个源、支持通配符、现代浏览器优先级更高；两者配合使用确保兼容性。

### 68. iframe 跨域共享 Cookie 的方案（第三方 Cookie 限制下）？
- **分类**：iframe 跨域
- **特点**：中高频 · 当前热点
- **要点**：Chrome 逐步淘汰第三方 Cookie；替代方案：`SameSite=None; Secure`（短期仍可用）、Storage Access API（`document.requestStorageAccess()`）、CHIPS（Partitioned Cookie）、First-Party Set；iframe 内登录态改用 `postMessage` 传递 Token + LocalStorage 存储。

### 69. 如何实现 iframe 的自适应高度？
- **分类**：iframe 布局
- **特点**：高频 · 实战常见
- **要点**：同源：iframe 内 `document.body.scrollHeight` → 父页面设置 iframe 高度；跨域：postMessage 传递高度；ResizeObserver 监听内容高度变化；注意：`height: 100%` 需要父容器有明确高度；iOS Safari 的 iframe 滚动问题（`scrolling="no"` + 内部容器滚动）。

### 70. Portal API 是什么？能否替代 iframe？
- **分类**：Web 新特性
- **特点**：低频但前沿 · 加分项
- **要点**：`<portal>` 原生预渲染跨域页面，可无缝过渡到顶层窗口；优势：比 iframe 性能更好、原生预览、无 JS 上下文隔离问题；当前兼容性有限（Chrome 已实现，Safari/Firefox 未跟进），不适合生产使用。

### 71. 微前端中的 iframe 方案优劣？
- **分类**：微前端
- **特点**：中高频 · 架构选型
- **要点**：优势：天然样式隔离、JS 隔离、接入零改造；劣势：性能差（多浏览器上下文）、通讯复杂（postMessage）、SEO 不友好、路由丢失、UI 割裂感（弹窗无法全屏）；适合：快速集成第三方页面、对性能要求不高的后台系统。

---

## 八、跨端通讯机制总览

### 72. H5 → App（Native）有哪些通讯方式？
- **分类**：跨端通讯
- **特点**：高频 · 体系化理解
- **要点**：① URL Scheme（`myapp://action?params=...`）；② JS Bridge（`postMessage` / `addJavascriptInterface` / `prompt` 拦截）；③ Universal Links / App Links（系统级跳转，更优雅）；④ Web Share API（`navigator.share()` 调起原生分享面板）。

### 73. App（Native）→ H5 有哪些通讯方式？
- **分类**：跨端通讯
- **特点**：高频 · 体系化理解
- **要点**：① `evaluateJavascript` 直接执行 JS 代码；② JS Bridge 回调（JS 发起请求 → Native 处理 → 回调 JS）；③ WebView URL 参数注入（修改 `src` 或 `loadUrl`）；④ 注入全局变量（`window.NativeData`）。

### 74. H5 唤起 App 的完整方案与兜底策略？
- **分类**：Deep Link
- **特点**：高频 · 业务必备
- **要点**：URL Scheme（兼容性好但体验差，有弹窗提示）；Universal Links（iOS，无缝跳转无弹窗）；App Links（Android，Google 官方方案）；兜底：定时器检测是否成功跳转 → 未跳转则引导下载/应用商店；`navigator.standalone` 判断是否已全屏模式。

### 75. JS Bridge 中的回调管理如何设计？
- **分类**：Bridge 架构
- **特点**：中高频 · 架构设计
- **要点**：全局 callbackId 计数器 → `callbacks[callbackId] = { resolve, reject }` → Native 调用 `bridge._invokeCallback(callbackId, result)` → 删除回调防泄漏；超时机制（setTimeout → reject）；回调队列保证执行顺序。

### 76. 多端统一 API 层的设计（Taro / uni-app 思路）？
- **分类**：跨端框架
- **特点**：中频 · 架构进阶
- **要点**：编译时适配（AST 转换）vs 运行时适配（条件分支）；统一 API 接口（`Taro.request` / `uni.request` 适配各端网络请求）；条件编译（`#ifdef MP-WEIXIN`）；样式适配（rpx / rem / px 自动转换）；组件适配（同一组件各端不同实现）。

### 77. iframe ↔ 父页面 ↔ WebView ↔ 小程序 之间的通讯全链路？
- **分类**：跨端通讯全貌
- **特点**：中频 · 系统性理解
- **要点**：H5 iframe 内 → `postMessage` → H5 外层 → JS Bridge → App Native；H5 → `wx.miniProgram.postMessage` → 小程序逻辑层 → `wx.request` → 服务端 → 下发给其他端；全链路需考虑协议格式统一、安全校验、超时重试、消息顺序保证。

### 78. WebSocket 在多端通讯中的应用与注意事项？
- **分类**：实时通讯
- **特点**：中高频 · 实时业务
- **要点**：App WebView 中 WebSocket 可能被 App 生命周期影响（后台断连）；小程序 WebSocket（`wx.connectSocket`）有独立 API；心跳保活 + 自动重连机制；断线消息补偿（服务端消息队列 + 客户端拉取）；连接复用与多页面共享。

### 79. 跨端事件总线的实现方案？
- **分类**：架构设计
- **特点**：中频 · 架构能力
- **要点**：统一事件协议（`{ type, source, target, payload, timestamp }`）；事件路由表（事件 → 处理端映射）；传输层抽象（postMessage / JS Bridge / WebSocket / BroadcastChannel）；可靠投递（ACK 机制 + 重试）；事件溯源（调试日志）。

### 80. BroadcastChannel API 的用途与兼容性？
- **分类**：同源跨标签通讯
- **特点**：中频 · 新特性
- **要点**：同源不同标签页/窗口间广播消息；比 `storage` 事件更语义化、更实时；不支持跨域、不支持跨端（仅浏览器内）；Web Worker 中也可使用；兼容性：Chrome/FF 支持，Safari 15.4+ 支持。

### 81. WebView 中的 `window.onerror` 能捕获所有错误吗？
- **分类**：错误监控
- **特点**：中频 · 监控体系
- **要点**：`window.onerror` 捕获同步错误 + 资源加载错误（部分）；Promise 未捕获 rejection 需 `unhandledrejection` 事件；跨域脚本错误只有 `"Script error."`（需 `crossorigin` 属性 + CORS 头）；WebView 中 Native 层 crash 需 Native 侧监控上报。

---

## 九、微前端架构

### 82. 什么是微前端？解决什么问题？
- **分类**：微前端概念
- **特点**：高频 · 架构理解
- **要点**：将巨石前端应用拆分为可独立开发/部署/运行的子应用；解决：代码库膨胀、构建慢、部署耦合、团队协作冲突、技术栈演进困难；类比微服务理念下沉到前端。

### 83. 微前端的主流方案对比（iframe / single-spa / qiankun / Webpack Module Federation / Web Components）？
- **分类**：微前端方案
- **特点**：超高频 · 架构选型
- **要点**：① iframe——隔离好但体验差；② single-spa——路由级集成，需改造子应用，无隔离；③ qiankun——基于 single-spa，增加 JS/CSS 沙箱，接入成本中等；④ Module Federation——Webpack 5 原生模块共享，编译时集成，粒度更细；⑤ Web Components——天然隔离，但生态不成熟。选型需考虑隔离性/接入成本/性能/技术栈无关性。

### 84. qiankun 的 JS 沙箱实现原理？
- **分类**：微前端沙箱
- **特点**：中高频 · 深度原理
- **要点**：① 快照沙箱（legacy）——激活前快照 window，卸载时恢复；② Proxy 沙箱（proxy）——为每个子应用创建 fake window（Proxy 代理），子应用对 window 的操作被拦截记录，卸载时直接丢弃 fake window；CSS 隔离：shadow DOM 或动态 CSS scope。

### 85. 微前端中的样式隔离方案？
- **分类**：微前端样式
- **特点**：中高频 · 实战痛点
- **要点**：Shadow DOM（最强隔离但样式穿透困难）；CSS Modules / Scoped CSS（编译时作用域）；CSS-in-JS（运行时作用域）；动态加载/卸载 CSS（qiankun 的 strictStyleIsolation）；CSS 前缀（postcss-prefix-selector）；Tailwind/UnoCSS 的 `prefix` 配置。

### 86. 微前端中的公共依赖与资源共享方案？
- **分类**：微前端共享
- **特点**：中频 · 工程优化
- **要点**：externals + CDN（React/Vue 全局变量）；Module Federation 的 shared 配置（自动共享依赖，版本协商）；微应用间状态共享（全局 Store / CustomEvent / postMessage）；注意版本冲突（React 16 vs 17 不能共享实例）。

### 87. 微前端的路由方案？
- **分类**：微前端路由
- **特点**：中高频 · 核心机制
- **要点**：基座应用注册子应用路由前缀（`/app1/*`）；激活条件匹配时加载子应用；子应用路由为相对路径（`/app1/pageA`）；History 模式 vs Hash 模式；基座负责全局导航/布局，子应用负责内部路由；路由级 vs 应用级拆分。

### 88. 微前端的通信方案？
- **分类**：微前端通讯
- **特点**：中高频 · 实战核心
- **要点**：① Props 传递（基座 → 子应用初始化参数）；② 全局状态库（Redux/Zustand 共享 Store）；③ CustomEvent（`window.dispatchEvent(new CustomEvent('xxx', { detail }))`）；④ postMessage（iframe 隔离场景）；⑤ 发布/订阅模式（全局 EventBus）；注意生命周期与内存泄漏（子应用卸载时清理监听）。

### 89. 微前端的部署方案与 CI/CD？
- **分类**：微前端部署
- **特点**：中频 · DevOps
- **要点**：基座 + 子应用独立部署到不同 CDN 路径；子应用入口 manifest（JSON 描述入口 JS/CSS）；基座动态加载子应用入口；版本管理（灰度发布、AB 测试、回滚）；Nginx 路由分发策略；CDN 缓存策略。

### 90. qiankun 子应用接入的完整流程？
- **分类**：微前端实战
- **特点**：高频 · 落地能力
- **要点**：子应用导出 `bootstrap/mount/unmount` 生命周期函数；`export const __POWERED_BY_QIANKUN__` 环境判断；打包为 UMD 格式（`output.libraryTarget: 'umd'`）；`public-path` 动态修改资源路径；基座 `registerMicroApps` 注册 + `start()` 启动；跨域配置（CORS 允许基座域名）。

### 91. Module Federation 与 qiankun 的对比与选择？
- **分类**：微前端选型
- **特点**：中高频 · 架构决策
- **要点**：MF：Webpack 5 原生、编译时集成、依赖共享、粒度细（组件级）、强绑定 Webpack；qiankun：运行时集成、技术栈无关、沙箱隔离、粒度粗（应用级）、接入成本低。新项目用 MF，跨技术栈/旧系统迁移用 qiankun。

---

## 十、用户体验与业务价值

### 92. 骨架屏（Skeleton）的实现与最佳实践？
- **分类**：用户体验
- **特点**：高频 · 体验优化
- **要点**：降低用户感知等待时间（CLS = 0）；实现：CSS 占位块 + 动画（shimmer 效果）、SVG 骨架、自动生成（vue-content-loader / react-loading-skeleton）；最佳实践：结构与真实页面一致、尺寸预留准确、首屏 SSR 输出骨架 HTML。

### 93. H5 页面的 SEO 优化策略？
- **分类**：SEO
- **特点**：中高频 · 流量价值
- **要点**：SSR/SSG（服务端渲染 / 静态生成）解决 SPA 的 SEO 问题；语义化 HTML（h1/h2 结构、meta description、Open Graph）；结构化数据（JSON-LD / Schema.org）；站点地图（sitemap.xml）；robots.txt；canonical URL；页面加载速度（Google 排名因素）；移动友好测试。

### 94. H5 无障碍（A11y）实践的要点？
- **分类**：无障碍
- **特点**：中频 · 社会价值 + 合规
- **要点**：语义化标签（`<button>` 而非 `<div onclick>`）；ARIA 属性（`role` / `aria-label` / `aria-hidden`）；键盘导航支持（tab 顺序、focus 样式可见）；色彩对比度（WCAG AA 标准 4.5:1）；屏幕阅读器测试（VoiceOver / NVDA）；`alt` 文本；表单 label 关联。

### 95. 前端错误监控与上报体系？
- **分类**：质量保障
- **特点**：高频 · 生产必备
- **要点**：JS 错误（`window.onerror` + `unhandledrejection`）；资源加载失败（`addEventListener('error', ..., true)` 捕获阶段）；接口错误（fetch/XHR 拦截）；白屏检测（PerformanceObserver + 关键 DOM 检查）；上报策略（批量、采样率、离线缓存重发）；Sentry / 自建 ELK。

### 96. H5 活动页的快速搭建与性能保障？
- **分类**：业务工程
- **特点**：中高频 · 业务场景
- **要点**：可视化搭建平台（拖拽组件 + 配置生成页面）；模板化（高质量模板复用）；图片压缩 + CDN + 懒加载；预渲染 + 骨架屏；性能预算（LCP < 2s）；AB 测试框架（多方案对比转化率）；分享裂变（Open Graph 卡片、小程序卡片）。

### 97. 防抖（debounce）与节流（throttle）的实现与场景？
- **分类**：性能优化
- **特点**：高频 · 编码基础
- **要点**：防抖：事件停止触发 n 秒后执行（搜索框输入、窗口 resize）；节流：每 n 秒最多执行一次（滚动加载、按钮防重复提交）；实现：闭包 + setTimeout / requestAnimationFrame；`leading` / `trailing` 选项；lodash `debounce` / `throttle` 源码级理解。

### 98. 大文件上传（分片/断点续传/秒传）的前端实现？
- **分类**：业务功能
- **特点**：高频 · 实战能力
- **要点**：分片（`Blob.slice()` + 并发上传）；断点续传（服务端返回已上传分片列表 → 跳过已完成）；秒传（文件 MD5/SHA → 服务端匹配已有文件 → 返回 URL）；进度计算（已完成分片/总分片）；Web Worker 计算 Hash（避免阻塞 UI）；`AbortController` 取消上传。

### 99. H5 页面的数据埋点与用户行为分析？
- **分类**：数据驱动
- **特点**：中高频 · 业务价值
- **要点**：埋点方案：代码埋点（精确但侵入性强）、全埋点/无痕埋点（监听所有点击事件）、可视化埋点（圈选标记）；核心指标：PV/UV、停留时长、转化漏斗、跳出率；上报方式：`navigator.sendBeacon`（页面卸载时不丢失）、图片 GIF 打点（1×1 透明 GIF 无跨域限制）；数据驱动 UI 优化（热力图、会话回放）。

### 100. 如何从 0 到 1 搭建前端 H5 性能监控看板？
- **分类**：性能体系
- **特点**：高频 · 综合能力
- **要点**：采集层（`web-vitals` 库采集 LCP/INP/CLS/FCP/TTFB + 自定义业务指标）；传输层（`sendBeacon` 批量上报、采样策略）；存储层（时序数据库 InfluxDB / Prometheus）；展示层（Grafana 看板：P75/P95 分位数、趋势图、按页面/版本/设备分组）；告警（指标阈值触发 → 钉钉/飞书通知）；持续优化闭环（监控 → 分析 → 优化 → 验证）。

---

## 总结

| 章节主题 | 核心能力关键词 | 面试重要度 |
|----------|----------------|------------|
| H5 基础与语义化 | HTML5 API、存储、PWA、实时通讯 | ⭐⭐⭐⭐ |
| 浏览器渲染原理与兼容性 | 渲染管线、回流重绘、缓存、跨域 | ⭐⭐⭐⭐⭐ |
| 多设备适配与响应式布局 | 响应式、移动端兼容、大屏适配 | ⭐⭐⭐⭐ |
| H5 性能优化核心 | Core Web Vitals、首屏优化、包体积 | ⭐⭐⭐⭐⭐ |
| WebView 与 App 集成 | JS Bridge、离线包、Hybrid 架构 | ⭐⭐⭐⭐⭐ |
| 小程序与 H5 的交互 | 双线程模型、web-view、通讯机制 | ⭐⭐⭐⭐ |
| iframe 与跨域通讯 | postMessage、安全、第三方 Cookie | ⭐⭐⭐⭐ |
| 跨端通讯机制总览 | 多端通讯链路、事件总线、Bridge 设计 | ⭐⭐⭐⭐ |
| 微前端架构 | qiankun、沙箱、Module Federation | ⭐⭐⭐⭐ |
| 用户体验与业务价值 | 骨架屏、SEO、A11y、监控、性能体系 | ⭐⭐⭐⭐⭐ |

> **使用建议**：按章节顺序系统复习，重点突破标注 ⭐⭐⭐⭐⭐ 的章节。每道题尝试自己先回答，再对照要点查漏补缺。面试时结合项目经历举例说明，比纯理论更有说服力。
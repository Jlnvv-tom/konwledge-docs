# Chapter 4 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「H5 性能优化核心」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、对比图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第4章：H5 性能优化核心

4.1 性能指标体系：Core Web Vitals 详解与度量
- LCP（Largest Contentful Paint，最大内容绘制）<= 2.5s
- INP（Interaction to Next Paint，下次绘制交互）<= 200ms
- CLS（Cumulative Layout Shift，累计布局偏移）<= 0.1
- 度量工具：Lighthouse / PageSpeed Insights / Chrome DevTools Performance / web-vitals 库
- 指标体系对比表格
- 核心代码：web-vitals 库采集指标

4.2 首屏加载（FCP/LCP）优化的完整策略
- FCP（First Contentful Paint）与 LCP 的区别
- 资源层：压缩、Tree Shaking、Code Splitting、HTTP/2 多路复用
- 加载层：preload / prefetch / lazy-load
- 渲染层：SSR（Server-Side Rendering）/ SSG（Static Site Generation）、骨架屏、关键 CSS 内联
- 网络层：CDN（Content Delivery Network）、Brotli 压缩、DNS Prefetch
- 优化策略决策流程图
- 核心代码：preload 使用、路由级 Code Splitting、关键 CSS 内联

4.3 长列表（万级数据）渲染性能优化
- 虚拟列表（Virtual List）原理：只渲染可视区域 DOM
- 虚拟列表渲染模型示意图（可视区域 + 缓冲区 + 总数据）
- react-window / vue-virtual-scroller 使用
- content-visibility: auto CSS 新特性
- 核心代码：虚拟列表核心算法实现、content-visibility 使用

4.4 JavaScript 包体积优化手段
- Tree Shaking（ESM 静态分析消除死代码）
- Code Splitting（路由级 + 组件级）
- 按需加载第三方库：lodash-es 替代 lodash、dayjs 替代 moment
- Scope Hoisting（作用域提升）
- Babel useBuiltIns: usage 精确 Polyfill
- 分析工具：webpack-bundle-analyzer / source-map-explorer
- 核心代码：Tree Shaking 配置、Code Splitting、按需引入

4.5 图片优化全策略：格式、压缩、加载、缓存
- 格式选择：WebP / AVIF > JPEG / PNG，SVG（Scalable Vector Graphics）用于图标
- 压缩工具：imagemin / TinyPNG
- 响应式图片：srcset / <picture>
- 加载策略：lazy、LQIP（Low Quality Image Placeholder）、BlurHash
- 缓存策略：Service Worker Cache
- CDN 图片处理：动态裁剪/格式转换
- 核心代码：响应式图片、LQIP 实现、CDN 图片处理 URL

4.6 动画性能优化：60fps 流畅动画的实现
- 只动画化 transform 和 opacity（不触发 layout/paint）
- requestAnimationFrame vs setInterval
- CSS 动画 vs JS 动画（合成线程处理 vs 主线程）
- will-change 提前声明合成层
- 避免同时动画大量元素
- Web Animations API
- 核心代码：CSS 动画 vs JS 动画对比、requestAnimationFrame 动画循环

4.7 内存泄漏的排查与预防
- Chrome DevTools Memory 面板：Heap Snapshot / Allocation Timeline
- 常见泄漏模式：未清除 setInterval/setTimeout、事件监听器未移除、闭包引用大对象、脱离 DOM 树的节点引用、全局变量
- WeakRef / FinalizationRegistry（ES2021）
- SPA（Single Page Application）路由切换时的清理
- 核心代码：常见泄漏示例与修复、WeakRef 使用、路由切换清理

4.8 首屏白屏时间长的排查思路
- Performance 面板 Timeline 分析：网络 -> 解析 -> 执行 -> 渲染
- TTFB（Time To First Byte）排查：后端慢/DNS 问题
- JS 执行时间：大 bundle / 同步阻塞
- 渲染阻塞资源：CSS / 同步 script
- 解决方案：SSR/预渲染、骨架屏、defer/async、分块加载
- 排查决策流程图
- 核心代码：Performance Observer 采集白屏时间

4.9 HTTP/2 与 HTTP/3 对前端性能的影响
- HTTP/2 多路复用（消除雪碧图/域名分片必要性）
- Server Push / 头部压缩（HPACK）
- HTTP/3 基于 QUIC（Quick UDP Internet Connections），UDP 传输
- 解决队头阻塞、0-RTT 连接
- 前端配合策略变化
- HTTP/1.1 vs HTTP/2 vs HTTP/3 特性对比表格

4.10 预加载策略：preload / prefetch / preconnect / dns-prefetch
- preload：高优先级加载当前页必需资源
- prefetch：低优先级预取下一页资源
- preconnect：提前建立 TCP/TLS 连接
- dns-prefetch：仅 DNS 解析
- modulepreload：预加载 ES 模块及依赖
- 预加载策略决策流程图
- 核心代码：各预加载标签的使用场景与写法

4.11 Web Worker 的使用场景与限制
- 计算密集任务移出主线程（大数据处理、加密、图像处理）
- 限制：不能操作 DOM、同源限制、通信开销（postMessage 序列化）
- SharedArrayBuffer + Atomics 实现零拷贝共享（需 COOP/COEP 安全头）
- OffscreenCanvas 将 Canvas 渲染移入 Worker
- 核心代码：Web Worker 创建与通信、OffscreenCanvas 使用

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"H5性能优化不是玄学，是工程。11个核心手段，让LCP从4秒降到1.5秒"
后跟IP自我介绍："我是怕浪猫，一个把Lighthouse跑到全绿的前端工程师"

**金句（至少3个）：**
> 性能优化不是一次性的工作，而是一个持续度量、分析、优化的闭环

**收藏触发结构：**
- 清单型："11个性能优化手段清单"
- 步骤型："白屏排查4步法"

**结尾CTA：**
1. 收藏引导："这篇性能优化清单，收藏起来每次发版前过一遍"
2. 互动引导："你的项目LCP多少秒？评论区比比看"
3. 追更引导："关注怕浪猫，下期讲WebView与App集成" + "系列进度 4/10"

**下章预告：**
"下一篇拆解JS Bridge原理、离线包方案、WebView性能优化、Hybrid架构设计，Hybrid开发一篇通关。"

####

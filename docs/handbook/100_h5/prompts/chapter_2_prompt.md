# Chapter 2 Writing Prompt

## 写作任务

根据下面的文章目录，以技术手册风格（类似掘金/技术博客），以IP「怕浪猫」的名义写一篇关于「浏览器渲染原理与兼容性」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落尽量短小精悍，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 涉及专有缩写名词时，首次出现需用全称英文解释，格式为：缩写（Full English Name）
6. 多用表格、流程图（用文字/ASCII 描述）、对比图来解释核心原理
7. 每个知识点必须配有核心关键代码示例（简短，不超过 30 行）
8. 代码示例需标注来源（如 MDN / Chrome Developers）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍时用"我是怕浪猫"
- 第一人称可交替使用"我"和"怕浪猫"
- 禁止用"小编"自称
- IP 名称自然融入

## 文章结构

#### 第2章：浏览器渲染原理与兼容性

2.1 从输入 URL 到页面渲染完成的完整链路
- DNS（Domain Name System）解析 -> TCP（Transmission Control Protocol）/ TLS（Transport Layer Security）握手 -> HTTP 请求/响应 -> HTML 解析构建 DOM（Document Object Model）-> CSS 解析构建 CSSOM（CSS Object Model）-> Render Tree -> Layout（回流）-> Paint（重绘）-> Composite（合成）
- 全链路流程图（ASCII 文字图）
- 每个阶段的耗时占比与优化切入点

2.2 关键渲染路径（Critical Rendering Path）优化策略
- 阻塞渲染资源识别：同步 script、阻塞 CSS
- defer/async 脚本加载差异对比图
- preload 关键资源与内联关键 CSS（Critical CSS）
- 减少DOM节点数与避免强制同步布局（Layout Thrashing）
- 核心代码：defer/async 使用、preload 链接、CSS 内联

2.3 回流（Reflow）与重绘（Repaint）的最小化策略
- 回流 = 几何属性变化触发重新布局
- 重绘 = 外观属性变化不触发布局
- 合成 = 仅 GPU（Graphics Processing Unit）层合成（transform/opacity 最优）
- 三者触发条件对比表格
- 优化手段：will-change、transform 替代 top/left、DocumentFragment 批量修改、display:none 修改再恢复
- 核心代码：动画属性选择对比、批量DOM操作

2.4 浏览器进程与线程模型
- 浏览器多进程架构：Browser Process / Renderer Process / GPU Process / Plugin Process
- Renderer 进程内多线程：主线程（Main Thread，JS执行）、合成线程（Compositor Thread）、解析线程（Parser Thread）
- 进程线程模型示意图
- 前端启示：避免长时间阻塞主线程、Web Worker 做计算密集任务、requestIdleCallback 做低优先级任务
- 核心代码：Web Worker 使用示例、requestIdleCallback 示例

2.5 CSS Hack 与浏览器前缀的现代工程方案
- 浏览器前缀：-webkit- / -moz- / -ms- 的历史原因
- 现代方案：Autoprefixer + PostCSS 自动处理
- 特征检测 @supports vs UA（User Agent）嗅探
- caniuse.com 查兼容性的工作流
- 核心代码：@supports 特征检测、PostCSS 配置示例

2.6 跨浏览器兼容性实战：IE/Edge/Safari/Chrome
- Babel 转译 ES6+ 语法
- Polyfill（core-js）补 API 缺失
- CSS fallback 写法策略
- Safari 独有坑：100vh 问题、position:sticky 前缀、日期格式解析差异
- feature detection（特征检测）优于 UA 判断
- 核心代码：Babel 配置、core-js 按需引入、Safari 100vh 修复

2.7 浏览器缓存机制：强缓存与协商缓存的完整流程
- Cache-Control / Expires（强缓存）
- Last-Modified / ETag（Entity Tag，协商缓存）
- 缓存命中流程图（从浏览器发请求到命中缓存的完整决策树）
- 状态码：200 from cache vs 304 Not Modified
- Service Worker 缓存层介入后的三层缓存体系
- 核心代码：Cache-Control 响应头配置、ETag 协商缓存示例

2.8 跨域问题的根本原因与全方案解决
- 同源策略（Same-Origin Policy）：协议+域名+端口必须一致
- CORS（Cross-Origin Resource Sharing）：简单请求 vs 预检请求 OPTIONS
- Access-Control-Allow-Origin 等响应头说明
- 代理方案：Nginx 反向代理 / Node 中间层
- postMessage 跨文档通讯
- JSONP（JSON with Padding）原理与局限
- 核心代码：CORS 响应头配置、Nginx 代理配置、postMessage 示例

2.9 浏览器垃圾回收（V8 引擎）对前端编码的影响
- V8 分代回收：新生代 Scavenge 算法 / 老生代 Mark-Sweep + Mark-Compact
- 分代回收模型示意图
- 常见内存泄漏：未清除的定时器、闭包持有大对象、脱离 DOM 树的引用、全局变量
- WeakMap / WeakSet 配合 GC（Garbage Collection）
- 核心代码：内存泄漏示例与修复、WeakMap 使用

2.10 合成层（Compositing Layer）与 GPU 加速
- 触发合成层的条件：3D transform、will-change、video、canvas、opacity 动画
- 合成层渲染流程图（主线程 -> 合成线程 -> GPU）
- 避免层爆炸（Layer Explosion）：过多合成层消耗内存
- will-change 的正确使用与滥用风险
- 核心代码：GPU 加速动画示例、will-change 使用

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"从输入URL到页面呈现，浏览器至少经历了8个阶段，90%的人只关注其中2个"
后跟IP自我介绍："我是怕浪猫，一个把浏览器原理翻了个底朝天的前端工程师"

**金句（至少3个）：**
> 回流是性能杀手，重绘是帮凶，合成才是性能的解药

**收藏触发结构：**
- 对比型："一张表看懂回流、重绘、合成的触发条件"
- 清单型："浏览器缓存机制决策流程图"

**结尾CTA：**
1. 收藏引导："这篇建议收藏，面试前对着流程图过一遍"
2. 互动引导："你在哪个浏览器踩过最离谱的兼容性坑？"
3. 追更引导："关注怕浪猫，下期讲多设备适配与响应式布局" + "系列进度 2/10"

**下章预告：**
"下一篇我们拆解响应式布局：rem/vw/rpx 怎么选、1px 边框问题、刘海屏适配、大屏可视化方案。"

####

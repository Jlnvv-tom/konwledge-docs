# Chapter 10 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「用户体验与业务价值」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源
9. 文章结尾附总结表格（含全系列10章的总结）

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第10章：用户体验与业务价值

10.1 骨架屏（Skeleton）的实现与最佳实践
- 降低用户感知等待时间，CLS（Cumulative Layout Shift）= 0
- 实现方案：CSS 占位块 + shimmer 动画、SVG 骨架、自动生成（react-loading-skeleton）
- 骨架屏与真实页面结构一致性原则
- 首屏 SSR 输出骨架 HTML
- 骨架屏方案对比表
- 核心代码：CSS shimmer 动画骨架、React 骨架组件、SSR 骨架输出

10.2 H5 页面的 SEO 优化策略
- SSR / SSG（Static Site Generation）解决 SPA 的 SEO 问题
- 语义化 HTML（h1/h2 结构、meta description、Open Graph）
- 结构化数据（JSON-LD / Schema.org）
- 站点地图（sitemap.xml）与 robots.txt
- canonical URL 防重复内容
- 页面加载速度是 Google 排名因素
- 移动友好测试
- SEO 检查清单表
- 核心代码：meta 标签配置、JSON-LD 结构化数据、sitemap.xml

10.3 H5 无障碍（A11y）实践要点
- A11y（Accessibility，无障碍访问）
- 语义化标签（<button> 而非 <div onclick>）
- ARIA（Accessible Rich Internet Applications）属性：role / aria-label / aria-hidden
- 键盘导航支持（tab 顺序、focus 样式可见）
- 色彩对比度（WCAG AA 标准 4.5:1）
- 屏幕阅读器测试（VoiceOver / NVDA）
- alt 文本与表单 label 关联
- 无障碍检查清单表
- 核心代码：ARIA 属性使用、键盘导航、focus 样式

10.4 前端错误监控与上报体系
- JS 错误（window.onerror + unhandledrejection）
- 资源加载失败（addEventListener('error', ..., true) 捕获阶段）
- 接口错误（fetch / XHR 拦截）
- 白屏检测（PerformanceObserver + 关键 DOM 检查）
- 上报策略（批量、采样率、离线缓存重发）
- Sentry / 自建 ELK（Elasticsearch + Logstash + Kibana）
- 错误监控体系架构图
- 核心代码：错误监控注册、fetch/XHR 拦截、sendBeacon 上报

10.5 H5 活动页的快速搭建与性能保障
- 可视化搭建平台（拖拽组件 + 配置生成页面）
- 模板化（高质量模板复用）
- 图片压缩 + CDN + 懒加载
- 预渲染 + 骨架屏
- 性能预算（LCP < 2s）
- AB 测试框架（多方案对比转化率）
- 分享裂变（Open Graph 卡片、小程序卡片）
- 核心代码：性能预算配置、AB 测试方案切换

10.6 防抖（debounce）与节流（throttle）的实现与场景
- 防抖：事件停止触发 n 秒后执行（搜索框输入、窗口 resize）
- 节流：每 n 秒最多执行一次（滚动加载、按钮防重复提交）
- 闭包 + setTimeout / requestAnimationFrame 实现
- leading / trailing 选项
- lodash debounce / throttle 源码级理解
- 对比表格
- 核心代码：防抖实现、节流实现、leading/trailing 选项

10.7 大文件上传（分片/断点续传/秒传）的前端实现
- 分片（Blob.slice() + 并发上传）
- 断点续传（服务端返回已上传分片列表 -> 跳过已完成）
- 秒传（文件 MD5 / SHA -> 服务端匹配已有文件 -> 返回 URL）
- 进度计算（已完成分片/总分片）
- Web Worker 计算 Hash（避免阻塞 UI）
- AbortController 取消上传
- 上传流程图
- 核心代码：分片上传、断点续传、Web Worker 计算 Hash、AbortController 取消

10.8 H5 数据埋点与用户行为分析
- 埋点方案：代码埋点（精确但侵入强）、全埋点/无痕埋点（监听所有点击）、可视化埋点（圈选标记）
- 核心指标：PV（Page View）/ UV（Unique Visitor）、停留时长、转化漏斗、跳出率
- 上报方式：navigator.sendBeacon（页面卸载时不丢失）、图片 GIF 打点（1x1 透明 GIF 无跨域限制）
- 数据驱动 UI 优化（热力图、会话回放）
- 埋点方案对比表
- 核心代码：sendBeacon 上报、GIF 打点、全埋点监听

10.9 从 0 到 1 搭建前端 H5 性能监控看板
- 采集层（web-vitals 库采集 LCP/INP/CLS/FCP/TTFB + 自定义业务指标）
- 传输层（sendBeacon 批量上报、采样策略）
- 存储层（时序数据库 InfluxDB / Prometheus）
- 展示层（Grafana 看板：P75/P95 分位数、趋势图、按页面/版本/设备分组）
- 告警（指标阈值触发 -> 钉钉/飞书通知）
- 持续优化闭环（监控 -> 分析 -> 优化 -> 验证）
- 看板架构图
- 核心代码：web-vitals 采集、sendBeacon 批量上报、Grafana 配置要点

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"技术做到最后，拼的不是框架熟练度，是把技术转化为用户体验和业务价值的能力"
后跟IP自我介绍："我是怕浪猫，一个相信技术最终服务于用户和业务的前端工程师"

**金句（至少3个）：**
> 性能监控不是终点，而是优化的起点——没有度量就没有改进

**收藏触发结构：**
- 清单型："SEO优化检查清单"
- 步骤型："性能监控看板搭建5步法"

**结尾CTA（全系列收尾）：**
1. 收藏引导："这篇用户体验与业务价值指南，收藏起来作为技术落地的参考"
2. 互动引导："你的项目最看重哪个用户体验指标？评论区交流"
3. 追更引导："关注怕浪猫，100道H5面试题系列到此完结，后续会出更多前端进阶内容" + "系列进度 10/10 完结"

**全系列总结：**
在文章最后附上全系列10章的总结表格，包含每章主题、核心知识点、面试重要度。感谢读者追更。

####

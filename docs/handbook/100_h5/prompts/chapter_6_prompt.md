# Chapter 6 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「小程序与 H5 的交互」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源（微信开放文档 / 支付宝开放平台等）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第6章：小程序与 H5 的交互

6.1 小程序基本架构与 H5 的本质区别
- 双线程模型：渲染层 WebView + 逻辑层 JSCore（iOS）/ V8（Android）
- 通过 Native 中转通讯
- 与 H5 单线程模型的本质区别
- 小程序限制：无法操作 DOM、无 BOM（Browser Object Model）API、受限网络请求（域名白名单）
- 架构对比图（小程序双线程 vs H5 单线程）
- 核心代码：小程序页面基本结构

6.2 小程序 web-view 组件的使用与限制
- <web-view src="https://..."> 嵌入 H5 页面
- 限制：需配置业务域名、不支持小程序内 navigateBack、全屏覆盖无法叠加原生组件
- cover-view 有限支持叠加
- web-view 能力边界表格
- 核心代码：web-view 基本使用、业务域名配置

6.3 小程序与 H5 之间的通讯机制
- 小程序 -> web-view：URL 参数传递数据（src 动态更新）
- web-view -> 小程序：wx.miniProgram.postMessage(data)
- postMessage 触发时机限制：后退、组件销毁、分享、复制链接
- wx.miniProgram.navigateTo / redirectTo 在 H5 中跳转小程序页面
- 实时双向通讯困难，需借助服务端中转（WebSocket / SSE）
- 通讯流程图
- 核心代码：H5 调 wx.miniProgram API、小程序接收 postMessage

6.4 小程序性能优化策略
- 分包加载：主包缩小、按需加载子包
- 独立分包：不依赖主包
- 分包预下载
- wx.nextTick 批量更新减少 setData 频次
- 减少 setData 数据量（只传变化字段）
- 图片懒加载 + 压缩
- 避免大节点 WXML（WeiXin Markup Language）
- 优化策略清单与效果对比表
- 核心代码：分包配置、wx.nextTick 使用

6.5 setData 的性能陷阱与优化
- setData 将数据从逻辑层序列化传到渲染层的通讯开销
- 频繁 setData 导致卡顿的原理图
- 优化：合并多次 setData 为一次、只传变化字段路径（'list[0].name'）
- 避免传输大量数据（图片 URL 用 CDN）
- setData 回调做后续逻辑
- 核心代码：setData 优化前后对比

6.6 小程序登录流程与 H5 登录态打通
- wx.login() -> code -> 服务端换 openid/session_key -> 自定义登录态（Token）
- H5 嵌入 web-view 时的登录态传递：
  - URL 参数传递 Token
  - JS Bridge（wx.miniProgram.postMessage）传递
- Token 过期刷新机制
- 安全考虑（Token 不应暴露在 URL 中过久）
- 登录流程图
- 核心代码：wx.login 完整流程、web-view 登录态注入

6.7 小程序条件渲染与列表渲染性能优化
- wx:key 必须唯一稳定（避免用 index）
- 大量列表用虚拟列表（recycle-view 组件 / scroll-view + 手动实现）
- hidden vs wx:if（频繁切换用 hidden，条件少用 wx:if）
- 避免 scroll-view 中频繁 setData
- 核心代码：wx:key 使用、虚拟列表实现、hidden vs wx:if 对比

6.8 小程序自定义组件与 H5 Web Components 对比
- 小程序 Component（类似 Vue 组件，有 data/methods/lifetimes）
- Web Components（Custom Elements + Shadow DOM + HTML Templates）
- 小程序组件样式隔离（styleIsolation）
- 对比表格：生命周期、样式隔离、数据流、复用性
- 核心代码：小程序 Component 定义、Web Component 定义

6.9 小程序与 H5 的技术选型决策
- 小程序优势：原生体验、入口丰富（扫码/搜索/分享）、用户授权便捷
- H5 优势：跨平台一次开发、迭代快速（无需审核）、SEO/外部分享灵活
- 选型决策流程图
- 策略：高频核心路径用小程序原生，活动页/营销页/第三方内容用 H5 web-view
- 核心代码：小程序跳 H5、H5 跳小程序

6.10 小程序分包加载与预下载策略
- 主包 <= 2MB，总包 <= 20MB（微信限制）
- 分包按页面/功能划分
- preloadRule 配置进入某页面时预下载其他分包
- 独立分包（不依赖主包，独立运行）适用于活动页
- 分包内资源按需加载
- 核心代码：app.json 分包配置、preloadRule 配置、独立分包配置

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"小程序和H5混合开发，90%的人卡在通讯机制上。这篇把双线程模型和通讯链路讲透"
后跟IP自我介绍："我是怕浪猫，一个在小程序和H5之间反复横跳的前端工程师"

**金句（至少3个）：**
> 小程序的setData不是免费的，每一次调用都是一次跨线程的序列化传输

**收藏触发结构：**
- 清单型："小程序性能优化10条清单"
- 对比型："小程序 vs H5 选型决策表"

**结尾CTA：**
1. 收藏引导："这篇小程序与H5交互指南，收藏起来开发时直接查"
2. 互动引导："你的小程序和H5是怎么打通登录态的？评论区交流"
3. 追更引导："关注怕浪猫，下期讲iframe与跨域通讯" + "系列进度 6/10"

**下章预告：**
"下一篇拆解postMessage安全、iframe性能、第三方Cookie限制、跨域通讯全方案。"

####

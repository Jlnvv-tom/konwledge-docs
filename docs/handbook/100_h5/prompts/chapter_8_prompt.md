# Chapter 8 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「跨端通讯机制总览」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第8章：跨端通讯机制总览

8.1 H5 调 App（Native）的通讯方式全景
- URL Scheme（myapp://action?params=...）
- JS Bridge（postMessage / addJavascriptInterface / prompt 拦截）
- Universal Links（iOS）/ App Links（Android）：系统级跳转
- Web Share API（navigator.share() 调起原生分享面板）
- 四种方案对比表格（体验/兼容性/安全性/实现成本）
- 核心代码：URL Scheme 跳转、Universal Links 配置、navigator.share()

8.2 App（Native）调 H5 的通讯方式
- evaluateJavascript 直接执行 JS 代码
- JS Bridge 回调（JS 发起请求 -> Native 处理 -> 回调 JS）
- WebView URL 参数注入（修改 src 或 loadUrl）
- 注入全局变量（window.NativeData）
- 四种方案对比表格
- 核心代码：iOS evaluateJavascript、Android evaluateJavascript、全局变量注入

8.3 H5 唤起 App 的完整方案与兜底策略
- URL Scheme（兼容性好但体验差，有弹窗提示）
- Universal Links（iOS，无缝跳转无弹窗）
- App Links（Android，Google 官方方案）
- 兜底：定时器检测是否成功跳转 -> 未跳转则引导下载/应用商店
- navigator.standalone 判断是否已全屏模式
- 唤起流程决策图
- 核心代码：完整唤起+兜底逻辑实现

8.4 JS Bridge 回调管理设计
- 全局 callbackId 计数器
- callbacks[callbackId] = { resolve, reject } 映射
- Native 调用 bridge._invokeCallback(callbackId, result)
- 删除回调防泄漏
- 超时机制（setTimeout -> reject）
- 回调队列保证执行顺序
- 回调管理流程图
- 核心代码：回调管理器完整实现

8.5 多端统一 API 层设计（Taro / uni-app 思路）
- 编译时适配（AST，Abstract Syntax Tree 转换）vs 运行时适配（条件分支）
- 统一 API 接口（Taro.request / uni.request 适配各端网络请求）
- 条件编译（#ifdef MP-WEIXIN）
- 样式适配（rpx / rem / px 自动转换）
- 组件适配（同一组件各端不同实现）
- 架构图：统一 API 层 -> 各端适配层 -> 原生 API
- 核心代码：条件编译、统一 API 封装示例

8.6 全链路通讯：iframe <-> 父页面 <-> WebView <-> 小程序
- H5 iframe 内 -> postMessage -> H5 外层 -> JS Bridge -> App Native
- H5 -> wx.miniProgram.postMessage -> 小程序逻辑层 -> wx.request -> 服务端 -> 下发给其他端
- 全链路需考虑：协议格式统一、安全校验、超时重试、消息顺序保证
- 全链路通讯拓扑图
- 核心代码：全链路消息封装与传递

8.7 WebSocket 在多端通讯中的应用与注意事项
- App WebView 中 WebSocket 可能被 App 生命周期影响（后台断连）
- 小程序 WebSocket（wx.connectSocket）有独立 API
- 心跳保活 + 自动重连机制
- 断线消息补偿（服务端消息队列 + 客户端拉取）
- 连接复用与多页面共享
- 多端 WebSocket 差异对比表
- 核心代码：心跳保活实现、自动重连、小程序 WebSocket

8.8 跨端事件总线的实现方案
- 统一事件协议：{ type, source, target, payload, timestamp }
- 事件路由表（事件 -> 处理端映射）
- 传输层抽象（postMessage / JS Bridge / WebSocket / BroadcastChannel）
- 可靠投递（ACK 机制 + 重试）
- 事件溯源（调试日志）
- 事件总线架构图
- 核心代码：跨端 EventBus 完整实现

8.9 BroadcastChannel API 的用途与兼容性
- 同源不同标签页/窗口间广播消息
- 比 storage 事件更语义化、更实时
- 不支持跨域、不支持跨端（仅浏览器内）
- Web Worker 中也可使用
- 兼容性：Chrome / Firefox 支持，Safari 15.4+ 支持
- BroadcastChannel vs storage 事件 vs postMessage 对比表
- 核心代码：BroadcastChannel 基本使用

8.10 WebView 中的错误捕获与监控
- window.onerror 捕获同步错误 + 资源加载错误（部分）
- Promise 未捕获 rejection 需 unhandledrejection 事件
- 跨域脚本错误只有 "Script error."（需 crossorigin 属性 + CORS 头）
- WebView 中 Native 层 crash 需 Native 侧监控上报
- 错误捕获方案对比表
- 核心代码：完整的错误监控注册、跨域脚本错误修复

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"H5、App、小程序、iframe四端通讯，一张拓扑图讲清所有链路"
后跟IP自我介绍："我是怕浪猫，一个在多端通讯架构上掉了不少头发的工程师"

**金句（至少3个）：**
> 跨端通讯的本质不是技术选型，而是协议设计——格式统一了，传输层只是换载体

**收藏触发结构：**
- 清单型："跨端通讯方案选型清单"
- 模板型："跨端事件总线设计模板"

**结尾CTA：**
1. 收藏引导："这篇跨端通讯总览，收藏起来做架构设计时直接参考"
2. 互动引导："你的项目跨端通讯用的什么方案？评论区交流"
3. 追更引导："关注怕浪猫，下期讲微前端架构" + "系列进度 8/10"

**下章预告：**
"下一篇拆解qiankun沙箱原理、Module Federation、样式隔离、微前端部署方案。"

####

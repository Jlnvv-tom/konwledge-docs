# Chapter 5 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「WebView 与 App 集成」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行，可含 Native 代码片段）
8. 代码示例标注来源
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第5章：WebView 与 App 集成

5.1 WebView 的本质与 iOS/Android 差异
- WebView 是内嵌浏览器引擎内核
- iOS 用 WKWebView（WebKit 内核），Android 用 WebView（Chromium 内核，4.4+ 可调试）
- 差异对比表格：JS 引擎（JavaScriptCore vs V8）、缓存机制、Cookie 管理、权限模型
- WKWebView 与 Android WebView 架构对比图
- 核心代码：iOS/Android 创建 WebView 的基本代码

5.2 JS Bridge 的实现原理详解
- Native 调 JS：evaluateJavascript / stringByEvaluatingJavaScriptFromString
- JS 调 Native 三种方式：
  - URL Scheme 拦截（window.location = 'myapp://action'）
  - prompt/console.log 拦截（Android JsPromptResult）
  - postMessage（Android addJavascriptInterface / iOS WKScriptMessageHandler）
- 三种方案对比表格（性能、安全性、兼容性）
- 通讯流程图（JS -> Bridge -> Native -> Bridge -> JS 回调）
- 核心代码：三种 JS -> Native 通讯的实现

5.3 通用 JS Bridge 的架构设计
- 统一 API 签名：bridge.call(action, params, callback)
- 回调队列管理：callbackId 映射机制
- Promise 化封装
- 事件订阅/发布机制
- 版本兼容与降级策略
- 权限与安全校验
- Bridge 架构图
- 核心代码：Bridge 类完整实现（注册/调用/回调/事件）

5.4 WebView 中 Cookie 与 LocalStorage 的 Native 同步
- iOS WKWebView Cookie 不自动同步到 NSHTTPCookieStorage（iOS 11+ 改善）
- Android Cookie 同步：CookieSyncManager（已废弃）-> CookieManager
- 登录态打通方案：Native 注入 Token 到 WebView Header / JS Bridge 传递
- Cookie 同步流程图
- 核心代码：Android CookieManager 同步、iOS WKWebView Cookie 注入

5.5 WebView 白屏与加载失败的排查和兜底
- 排查链路：网络（DNS/TLS）-> 资源 404/500 -> JS 执行错误 -> 渲染阻塞 -> WebView 内核崩溃
- onErrorReceived 回调（Android）/ didFailNavigation（iOS）
- 加载失败页 + 重试按钮方案
- 前端 JS 错误上报
- WebView 远程调试：chrome://inspect（Android）/ Safari（iOS）
- 排查决策流程图
- 核心代码：Android/iOS 错误监听与兜底页

5.6 提升 WebView 首屏加载速度的策略
- 预加载：App 启动时预热 WebView 实例池
- 离线包：H5 资源打包到 App 本地，拦截请求返回本地文件
- 懒加载 JS/CSS
- SSR（Server-Side Rendering）
- WebView 复用池避免重复初始化开销
- DNS 预解析 + 连接预建
- 优化策略对比表格（效果/成本/复杂度）
- 核心代码：WebView 实例池实现、DNS 预解析

5.7 离线包方案的设计与实现
- 完整流程：资源打包 -> 版本管理 -> 增量更新（diff/patch）-> CDN 分发 -> 客户端下载/解压 -> WebView 拦截请求映射本地文件
- 离线包架构流程图
- 更新策略：全量/增量、静默更新、用户触发
- 竞品分析：美团/微信/支付宝离线包方案要点
- 核心代码：WebView 请求拦截与本地资源映射（shouldInterceptRequest）

5.8 WebView 的安全风险与防护
- addJavascriptInterface Android 4.2 以下远程代码执行（RCE）漏洞
- 关闭 file:// 域访问（setAllowFileAccess(false)）
- 限制可访问 URL 白名单
- HTTPS 校验
- JS Bridge 调用来源校验（origin 检查）
- 防止 iframe 劫持
- 安全风险与防护措施对照表
- 核心代码：安全配置示例

5.9 WebView 中调试 H5 页面的方法
- Android：WebView.setWebContentsDebuggingEnabled(true) -> chrome://inspect
- iOS：Safari -> 开发 -> 模拟器/设备 -> 选择页面
- 远程调试方案：Vorlon.js / Spy-js
- vConsole / eruda 嵌入式调试面板（线上排查）
- 核心代码：vConsole 集成、Android 远程调试开启

5.10 App 内 H5 与原生的手势冲突处理
- 侧滑返回手势与 H5 横向滚动冲突
- gesture-nav 属性控制
- Native 侧判断触摸区域决定是否拦截
- touch-action CSS 属性声明手势行为
- JS Bridge 通知 Native 禁用/启用手势
- 核心代码：touch-action 配置、JS Bridge 手势控制

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"Hybrid开发踩了3年坑，我把JS Bridge的原理和离线包方案总结成了这篇"
后跟IP自我介绍："我是怕浪猫，一个在Hybrid开发领域实战多年的前端工程师"

**金句（至少3个）：**
> JS Bridge不是黑盒，理解了回调队列，你就理解了所有Hybrid框架的底层逻辑

**收藏触发结构：**
- 模板型："通用JS Bridge设计模板"
- 步骤型："离线包实现5步法"

**结尾CTA：**
1. 收藏引导："这篇Hybrid架构指南，收藏起来做技术选型时直接参考"
2. 互动引导："你的Hybrid方案用的什么Bridge？评论区交流"
3. 追更引导："关注怕浪猫，下期讲小程序与H5的交互" + "系列进度 5/10"

**下章预告：**
"下一篇拆解小程序双线程模型、web-view组件、小程序与H5通讯机制、setData性能优化。"

####

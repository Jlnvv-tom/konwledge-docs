# Chapter 1 Writing Prompt

## 写作任务

根据下面的文章目录，以技术手册风格（类似掘金/技术博客），以IP「怕浪猫」的名义写一篇关于「H5 基础与语义化」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号（如 ⭐ ✅ 等）
3. 段落尽量短小精悍，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 涉及专有缩写名词时，首次出现需用全称英文解释，格式为：缩写（Full English Name）
6. 多用表格、流程图（用文字/ASCII 描述）、对比图来解释核心原理
7. 每个知识点必须配有核心关键代码示例（简短，不超过 30 行）
8. 代码示例需标注来源（如 MDN / WHATWG 规范）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍时用"我是怕浪猫"
- 第一人称可交替使用"我"和"怕浪猫"
- 禁止用"小编"自称
- IP 名称自然融入，不刻意强调

## 文章结构

#### 第1章：H5 基础与语义化

1.1 HTML5 新增语义化标签及解决的问题
- 语义化标签清单（header/nav/main/article/section/aside/footer）
- 解决的问题：div 命名混乱、SEO（Search Engine Optimization）、无障碍阅读、代码可维护性
- 语义化标签 vs div 的对比表格
- 实际页面结构的语义化布局示意图

1.2 H5 离线存储方案全景对比
- LocalStorage / SessionStorage / IndexedDB / Cache API / Application Cache（已废弃）到 Service Worker
- 从容量、时效性、异步性、数据结构支持等维度做对比表格
- 各方案的适用场景决策流程图
- LocalStorage 和 IndexedDB 的核心代码示例

1.3 Service Worker 生命周期与离线可用实现
- 生命周期：install -> activate -> fetch 事件拦截
- Cache API 缓存静态资源的流程图
- 三种缓存策略对比：Cache First / Network First / Stale-While-Revalidate
- Service Worker 注册和拦截 fetch 的核心代码

1.4 HTML5 input 类型与移动端表单体验优化
- input type 全清单：email/tel/number/date/url/search 等
- 移动端自动弹出对应键盘的效果示意图
- pattern 属性做前端校验的代码示例
- 表单体验优化清单（autocomplete/autocapitalize/enterkeyhint 等）

1.5 Web Storage 事件机制与多标签页数据同步
- storage 事件触发机制原理图
- 同源多标签页数据同步的实现方案
- 多标签页登录状态同步的核心代码
- BroadcastChannel API 作为替代方案的对比

1.6 Cookie、Session、Token 在前端的实践
- Cookie 核心字段：httpOnly / secure / sameSite
- JWT（JSON Web Token）前端存储方案对比：LocalStorage vs Cookie
- SameSite=None + Secure 在跨域 Cookie 中的必要性
- Token 存储与请求拦截器注入的代码示例

1.7 H5 设备能力 API：Geolocation 与 DeviceOrientation
- Geolocation API 获取定位的代码示例
- DeviceOrientationEvent 获取陀螺仪/加速度计
- HTTPS 强制要求、用户授权弹窗机制
- iOS 13+ 需 requestPermission() 的兼容处理

1.8 WebSocket 与 SSE 的对比与选择
- WebSocket（全双工、二进制、低协议开销）vs SSE（Server-Sent Events，单向推送、纯文本、自动重连）
- 通讯模型对比图（双向 vs 单向）
- 适用场景：IM/游戏选 WebSocket，通知推送/股票行情选 SSE
- WebSocket 连接建立与消息收发代码示例

1.9 H5 拖放 API 原理与移动端兼容方案
- 拖放事件链：dragstart -> dragover -> drop
- 桌面端拖放实现的核心代码
- 移动端不支持原生 DnD（Drag and Drop）的原因
- 使用 Touch 事件模拟拖放的方案与 polyfill（如 interact.js）

1.10 Canvas 与 SVG 的选型决策
- Canvas（位图、高性能、适合大量元素动画）vs SVG（Scalable Vector Graphics，矢量、DOM 可操作、适合交互图形）
- 渲染机制对比图
- 分辨率自适应选 SVG，高性能渲染选 Canvas/WebGL（Web Graphics Library）
- Canvas 绘制与 SVG 绘制的核心代码对比

## 互动/收藏/涨粉模块

**开头3秒钩子（标题之后第一段）：**
从以下3种中选1种：
- 数字冲击型："10个H5基础问题，我靠第3个少写了200行代码"
- 反常识型："你以为H5只是HTML的升级？其实它重新定义了前端的存储、通讯和设备能力"
- 痛点共鸣型："H5存储方案用了3年还只会LocalStorage？问题出在这"

开头钩子后紧跟IP自我介绍："我是怕浪猫，一个在前端摸爬滚打多年的开发者"

**每300字金句（至少3个，用引用块标注）：**
> 金句示例：语义化不是给机器看的，是给三个月后的自己看的

**收藏触发结构（至少1个）：**
- 清单型："H5存储方案选型清单"
- 对比型："一张表看懂Canvas vs SVG"

**结尾CTA（3层）：**
1. 收藏引导："觉得有用？收藏起来，面试前翻一遍"
2. 互动引导："你在H5开发中踩过哪个坑？评论区说说"
3. 违更引导："关注怕浪猫，下期我们讲浏览器渲染原理与兼容性" + 系列进度条 "系列进度 1/10"

**下章预告：**
"下一篇我们拆解：从输入URL到页面渲染完成，浏览器到底做了什么？回流重绘、合成层、缓存机制，一篇讲透。"

####

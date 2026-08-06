# Chapter 3 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「多设备适配与响应式布局」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落尽量短小精悍，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写名词首次出现需用全称英文解释，格式为：缩写（Full English Name）
6. 多用表格、流程图（ASCII 文字图）、对比图解释核心原理
7. 每个知识点配有核心关键代码示例（简短，不超过 30 行）
8. 代码示例标注来源（MDN / CSS Tricks / web.dev 等）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第3章：多设备适配与响应式布局

3.1 响应式设计的核心原则与实现方案
- Media Query（媒体查询）语法与断点策略
- 弹性布局 Flexbox（Flexible Box Layout）与 Grid（CSS Grid Layout）
- 相对单位体系：rem / em / vw / vh / %
- 响应式图片：<picture> / srcset
- 移动优先（Mobile First）vs 桌面优先策略对比
- 核心代码：Media Query 断点、Flexbox 布局、响应式图片

3.2 CSS 单位体系：rem / em / vw / vh / px / rpx 全解析
- px（Pixel，绝对像素）
- em 相对父元素 font-size
- rem（Root em）相对根元素
- vw / vh（Viewport Width/Height）相对视口
- rpx（Responsive Pixel）小程序专用，750rpx = 屏宽
- 单位选型决策流程图
- 核心代码：rem + JS 动态设置 root font-size、纯 vw 适配方案

3.3 移动端 1px 边框问题的根因与解决方案
- DPR（Device Pixel Ratio，设备像素比）> 1 时 CSS 1px 在物理像素上 > 1px
- 设备像素 vs CSS 像素的关系示意图
- 解决方案对比：transform: scaleY(0.5) 伪元素、border-image、box-shadow 模拟、viewport meta 缩放+rem 联动
- 核心代码：每种方案的实现与适用场景

3.4 移动端点击延迟（300ms）的来龙去脉
- 早期浏览器为判断双击缩放（Double Tap to Zoom）等待 300ms
- 现代浏览器已通过 viewport meta 消除延迟
- CSS touch-action: manipulation 禁用双击缩放
- FastClick 库的历史方案与现状
- 核心代码：viewport meta 配置、touch-action 使用

3.5 安全区适配：刘海屏与底部 Home 指示条
- viewport-fit=cover 开启安全区
- env(safe-area-inset-*) / constant(safe-area-inset-*)（iOS < 13.2）
- 顶部刘海与底部 Home 条的适配示意图
- 核心代码：安全区适配 CSS、底部固定栏 padding 处理

3.6 Flexbox 与 Grid 布局的差异与选择
- Flexbox 一维（行或列）适合组件级布局
- Grid 二维适合页面级布局
- 两者核心属性对比表格
- grid-template-areas 实现响应式重排
- 核心代码：Flexbox 典型布局、Grid 响应式重排

3.7 移动端软键盘弹出的布局适配
- iOS 键盘弹起不改变视口高度，需 visualViewport API 监听
- Android 键盘弹起缩小 window.innerHeight
- iOS vs Android 键盘行为对比图
- 解决方案：visualViewport.addEventListener('resize')、避免 100vh 固定高度
- 核心代码：visualViewport 监听、固定底部栏适配

3.8 图片适配全策略：响应式、懒加载、格式选择
- <picture> + <source> 多格式/多尺寸适配
- loading="lazy" 原生懒加载
- WebP / AVIF（AV1 Image File Format）格式兼容与 fallback
- srcset + sizes 按 DPR 适配
- aspect-ratio 防止布局偏移（CLS，Cumulative Layout Shift）
- 核心代码：响应式图片完整写法、懒加载、格式 fallback

3.9 横屏与竖屏的适配方案
- orientation: landscape/portrait 媒体查询
- screen.orientation API 读取/锁定方向
- 横屏布局重排策略：Grid areas 重定义
- 核心代码：横屏媒体查询、orientation API 使用

3.10 大屏数据可视化的自适应方案
- 1920x1080 -> 4K -> 超宽屏的适配挑战
- transform: scale() 等比缩放方案（rem + scale 联动）
- ECharts resize() 监听容器变化
- clamp() 限制极端尺寸
- Container Query（容器查询）实现组件级响应式
- 核心代码：等比缩放方案、ECharts resize、Container Query 示例

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"移动端适配做不好，不是因为难，是因为你不知道这10个问题的根因"
后跟IP自我介绍："我是怕浪猫，一个在移动端适配坑里爬出来过无数次的前端工程师"

**金句（至少3个）：**
> 没有完美的单位，只有最适合场景的单位

**收藏触发结构：**
- 清单型："CSS单位选型决策流程图"
- 对比型："Flexbox vs Grid 核心属性对比表"

**结尾CTA：**
1. 收藏引导："这篇适配方案大全，收藏起来直接照抄"
2. 互动引导："你在移动端适配踩过最离谱的坑是什么？"
3. 追更引导："关注怕浪猫，下期讲H5性能优化核心" + "系列进度 3/10"

**下章预告：**
"下一篇拆解Core Web Vitals、首屏优化、包体积优化、虚拟列表、60fps动画，性能优化一篇拉满。"

####

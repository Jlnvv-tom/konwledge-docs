# 第3章：多设备适配与响应式布局

移动端适配做不好，不是因为难，是因为你不知道这10个问题的根因。我是怕浪猫，一个在移动端适配坑里爬出来过无数次的前端工程师。上一篇讲了浏览器渲染原理，这篇进入前端日常高频问题：多设备适配。

## 3.1 响应式设计的核心原则与实现方案

### Media Query 断点策略

响应式设计的核心是通过媒体查询（Media Query）针对不同屏幕尺寸应用不同样式：

```css
/* 移动优先（Mobile First）：从小到大写 */
.container {
  padding: 12px;
}
@media (min-width: 768px) {
  .container { padding: 24px; }
}
@media (min-width: 1200px) {
  .container { padding: 40px; }
}
```

移动优先 vs 桌面优先的对比：

| 策略 | 写法 | 基准 | 优势 |
|------|------|------|------|
| 移动优先 | `min-width` | 小屏样式为默认 | 移动端加载更少CSS |
| 桌面优先 | `max-width` | 大屏样式为默认 | 桌面端调试方便 |

现代项目推荐移动优先，因为移动端性能更敏感，默认样式应尽量精简。

### 响应式图片

```html
<!-- srcset + sizes：按 DPR 和视口宽度选择图片 -->
<img
  src="photo-800.jpg"
  srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1200.jpg 1200w"
  sizes="(max-width: 600px) 100vw, 50vw"
  alt="响应式图片"
>

<!-- picture：支持格式 fallback 和艺术指导 -->
<picture>
  <source media="(max-width: 600px)" srcset="photo-mobile.jpg">
  <source type="image/avif" srcset="photo.avif">
  <source type="image/webp" srcset="photo.webp">
  <img src="photo.jpg" alt="fallback">
</picture>
```

> 响应式设计不是把页面缩小，是让每个屏幕尺寸下都有最优的布局和资源。

参考来源：[MDN - Using media queries](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_media_queries/Using_media_queries)、[MDN - Responsive images](https://developer.mozilla.org/zh-CN/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)

## 3.2 CSS 单位体系全解析

### 单位对比

| 单位 | 全称 | 相对基准 | 典型用途 |
|------|------|----------|----------|
| px | Pixel | 绝对像素 | 边框、固定尺寸 |
| em | - | 父元素 font-size | 组件内缩进 |
| rem | Root em | 根元素 font-size | 全局缩放 |
| vw | Viewport Width | 视口宽度的 1% | 全屏布局 |
| vh | Viewport Height | 视口高度的 1% | 全屏高度 |
| rpx | Responsive Pixel | 屏宽的 1/750 | 小程序专用 |

### 单位选型决策

```
需要固定值？-> px
跟随父元素缩放？-> em
跟随全局缩放？-> rem
占满视口比例？-> vw / vh
小程序内？-> rpx
```

### rem 适配方案

```javascript
// 动态设置根元素 font-size，1rem = 设计稿宽度/10
function setRemUnit() {
  const docEl = document.documentElement;
  const width = docEl.getBoundingClientRect().width;
  // 设计稿 750px 宽，1rem = 75px
  docEl.style.fontSize = (width / 10) + 'px';
}
setRemUnit();
window.addEventListener('resize', setRemUnit);
```

```css
/* 设计稿量出 75px，写 1rem */
.title {
  font-size: 0.53rem;  /* 40px / 75 */
  padding: 0.27rem;    /* 20px / 75 */
}
```

### 纯 vw 适配方案

```css
/* 750 设计稿：1vw = 7.5px，量出 75px 写 10vw */
.title {
  font-size: 5.33vw;  /* 40px / 7.5 */
  padding: 2.67vw;    /* 20px / 7.5 */
}
```

vw 方案无需 JS，但无法通过用户缩放字体大小（可访问性略差）。生产中常用 `vw + rem` 混合方案。

> 没有完美的单位，只有最适合场景的单位。

参考来源：[MDN - CSS Length](https://developer.mozilla.org/zh-CN/docs/Web/CSS/length)、[MDN - font-size](https://developer.mozilla.org/zh-CN/docs/Web/CSS/font-size)

## 3.3 移动端 1px 边框问题的根因与解决方案

### 根因分析

设备像素比（DPR，Device Pixel Ratio）> 1 时，CSS 的 1px 在物理像素上大于 1px：

```
CSS像素：1px
DPR = 2 的设备：1px CSS = 2px 物理像素 -> 看起来粗
DPR = 3 的设备：1px CSS = 3px 物理像素 -> 看起来更粗
```

设计师在设计稿上画的 1px 是物理像素，而 CSS 的 1px 是逻辑像素，两者在高清屏上不等于 1:1。

### 解决方案对比

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| transform: scaleY(0.5) | 伪元素缩放 | 兼容性好 | 圆角边框难处理 |
| viewport 缩放 | meta 缩放 + rem 联动 | 全局解决 | 影响所有尺寸 |
| border-image | 图片做边框 | 灵活 | 颜色不便修改 |
| box-shadow 模拟 | 0.5px 阴影 | 简单 | 部分安卓不支持 |

### transform 方案（推荐）

```css
/* 1px 底边框 */
.border-bottom {
  position: relative;
}
.border-bottom::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background: #ddd;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}

/* 1px 全边框 */
.border-all {
  position: relative;
}
.border-all::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 200%;
  height: 200%;
  border: 1px solid #ddd;
  border-radius: 8px;  /* 圆角也缩放 */
  transform: scale(0.5);
  transform-origin: 0 0;
  box-sizing: border-box;
}
```

> 1px 问题的本质是 CSS 像素和物理像素的换算关系，理解了 DPR 就理解了所有方案。

参考来源：[MDN - devicePixelRatio](https://developer.mozilla.org/zh-CN/docs/Web/API/Window/devicePixelRatio)

## 3.4 移动端点击延迟（300ms）的来龙去脉

### 延迟原因

早期移动浏览器为了判断用户是单击还是双击缩放（Double Tap to Zoom），在第一次点击后等待 300ms，如果没有第二次点击才触发 click 事件。

### 现代解决方案

```html
<!-- 方案1：设置 viewport，现代浏览器会消除 300ms 延迟 -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
```

```css
/* 方案2：禁止双击缩放，浏览器不再需要等待 */
* {
  touch-action: manipulation;
  /* manipulation：允许滚动和捏合缩放，但禁用双击缩放 */
}
```

```javascript
// 方案3：使用 FastClick（老项目兼容）
// 现代项目通常不需要，viewport + touch-action 足够
// import FastClick from 'fastclick';
// FastClick.attach(document.body);
```

现代浏览器（Chrome 32+、iOS 9.3+）在设置了正确的 viewport 后已自动消除 300ms 延迟，新项目不需要 FastClick。

> 300ms 延迟是历史遗留问题，现代项目设好 viewport 就不用管了。

参考来源：[MDN - touch-action](https://developer.mozilla.org/zh-CN/docs/Web/CSS/touch-action)、[Chrome Developers - 300ms tap delay](https://developer.chrome.com/blog/300ms-tap-delay-gone-away)

## 3.5 安全区适配：刘海屏与底部 Home 指示条

### viewport-fit=cover

```html
<!-- 开启安全区适配 -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

### env() 环境变量

```css
/* iOS 安全区变量 */
.app {
  /* 顶部刘海区域 */
  padding-top: env(safe-area-inset-top);
  /* 底部 Home 指示条 */
  padding-bottom: env(safe-area-inset-bottom);
  /* 左右侧滑区域（横屏刘海） */
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* 兼容 iOS < 13.2 使用 constant() */
.app {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}
```

### 底部固定栏适配

```css
/* 底部固定栏：内容高度 + Home 指示条高度 */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  padding-bottom: env(safe-area-inset-bottom);
  background: #fff;
}

/* 如果已有 padding，需要用 calc 叠加 */
.bottom-bar {
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
}
```

安全区适配示意图：

```
┌─────────────────────┐
│     刘海区域        │ <- safe-area-inset-top
├─────────────────────┤
│                     │
│    页面内容区域     │
│                     │
├─────────────────────┤
│    底部固定栏       │
│    Home 指示条      │ <- safe-area-inset-bottom
└─────────────────────┘
```

> 刘海屏适配不难，难的是记得在项目初期就加上 viewport-fit=cover。

参考来源：[MDN - env()](https://developer.mozilla.org/zh-CN/docs/Web/CSS/env)、[Apple - Designing for iPhone X](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone)

## 3.6 Flexbox 与 Grid 布局的差异与选择

### 核心差异

| 特性 | Flexbox（Flexible Box Layout） | Grid（CSS Grid Layout） |
|------|------|------|
| 维度 | 一维（行或列） | 二维（行和列） |
| 适用场景 | 组件级、导航栏、工具栏 | 页面级布局、卡片网格 |
| 对齐控制 | 主轴+交叉轴 | 行+列双向精确控制 |
| 排列方向 | flex-direction 切换 | grid-template-areas 自由定义 |
| 响应式重排 | 需 media query 改方向 | areas 重定义即可 |

### Flexbox 典型布局

```css
/* 水平居中 */
.center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 顶栏：左中右三段 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header .center {
  flex: 1;
  text-align: center;
}
```

### Grid 响应式重排

```css
/* 桌面：3列布局 */
.dashboard {
  display: grid;
  grid-template-columns: 200px 1fr 1fr;
  grid-template-areas:
    "sidebar main aside"
    "sidebar footer footer";
  gap: 16px;
}

/* 移动端：1列堆叠 */
@media (max-width: 768px) {
  .dashboard {
    grid-template-columns: 1fr;
    grid-template-areas:
      "main"
      "aside"
      "footer";
  }
}

.sidebar { grid-area: sidebar; }
.main { grid-area: main; }
```

> Flexbox 管一条线上的排列，Grid 管整个平面的布局——页面级用 Grid，组件级用 Flexbox。

参考来源：[MDN - Flexbox](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_flexible_box_layout)、[MDN - CSS Grid](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_grid_layout)

## 3.7 移动端软键盘弹出的布局适配

### iOS vs Android 行为差异

| 平台 | 键盘弹出行为 | 视口变化 |
|------|------------|----------|
| iOS | 不改变 window.innerHeight | visualViewport.height 缩小 |
| Android | 缩小 window.innerHeight | layout viewport 缩小 |

### 解决方案

```javascript
// 使用 visualViewport API 统一处理
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', () => {
    const viewport = window.visualViewport;
    // 调整布局高度
    document.documentElement.style.setProperty(
      '--viewport-height',
      viewport.height + 'px'
    );
    // 处理键盘遮挡的输入框
    const activeEl = document.activeElement;
    if (activeEl && activeEl.tagName === 'INPUT') {
      const rect = activeEl.getBoundingClientRect();
      if (rect.bottom > viewport.height) {
        activeEl.scrollIntoView({ block: 'center' });
      }
    }
  });
}
```

```css
/* 避免 100vh 在 iOS 上的问题 */
.full-screen {
  height: 100vh; /* iOS 可能包含地址栏 */
  height: 100dvh; /* Dynamic viewport，推荐 */
}

/* 或使用 JS 注入的变量 */
.full-screen {
  height: var(--viewport-height, 100vh);
}
```

> iOS 键盘弹出不改视口高度，这个差异踩过一次就忘不了。

参考来源：[MDN - VisualViewport API](https://developer.mozilla.org/zh-CN/docs/Web/API/VisualViewport_API)

## 3.8 图片适配全策略：响应式、懒加载、格式选择

### 响应式图片

```html
<!-- srcset 按 DPR 选择 -->
<img
  src="photo@1x.jpg"
  srcset="photo@1x.jpg 1x, photo@2x.jpg 2x, photo@3x.jpg 3x"
  alt="适配不同 DPR"
>
```

### 懒加载

```html
<!-- 原生懒加载 -->
<img src="photo.jpg" loading="lazy" alt="懒加载图片" width="300" height="200">
```

```javascript
// IntersectionObserver 实现懒加载（兼容性更好）
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
```

### 格式选择与 fallback

```html
<picture>
  <!-- AVIF：最新格式，压缩率最高 -->
  <source type="image/avif" srcset="photo.avif">
  <!-- WebP：兼容性好，压缩率高 -->
  <source type="image/webp" srcset="photo.webp">
  <!-- fallback -->
  <img src="photo.jpg" alt="格式 fallback">
</picture>
```

| 格式 | 全称 | 压缩率 | 浏览器支持 |
|------|------|--------|------------|
| AVIF | AV1 Image File Format | 最高 | Chrome 85+、Safari 16+ |
| WebP | WebP Image Format | 高 | Chrome 32+、Safari 14+ |
| JPEG | Joint Photographic Experts Group | 中 | 全部 |
| PNG | Portable Network Graphics | 低（无损） | 全部 |

### 防止布局偏移

```css
/* aspect-ratio 预留空间，防止图片加载导致 CLS */
.image-wrapper {
  aspect-ratio: 16 / 9;
  width: 100%;
  background: #f0f0f0;
}
.image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

> 图片适配三件套：响应式选尺寸、懒加载省流量、现代格式省带宽。

参考来源：[MDN - loading attribute](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/img#loading)、[web.dev - CLS](https://web.dev/articles/cls)

## 3.9 横屏与竖屏的适配方案

### 媒体查询检测方向

```css
/* 竖屏样式 */
@media (orientation: portrait) {
  .layout {
    flex-direction: column;
  }
}

/* 横屏样式 */
@media (orientation: landscape) {
  .layout {
    flex-direction: row;
  }
}
```

### Screen Orientation API

```javascript
// 读取当前方向
const orientation = screen.orientation.type;
// 'portrait-primary' | 'landscape-primary'

// 监听方向变化
screen.orientation.addEventListener('change', () => {
  console.log('方向变化:', screen.orientation.type);
  relayout();
});

// 尝试锁定方向（需要全屏模式）
document.documentElement.requestFullscreen().then(() => {
  screen.orientation.lock('landscape').catch(() => {
    // 部分浏览器/系统不支持锁定
  });
});
```

### Grid 重排

```css
/* 横屏时重新定义网格区域 */
@media (orientation: landscape) {
  .game-layout {
    display: grid;
    grid-template-columns: 1fr 2fr;
    grid-template-areas: "sidebar stage";
  }
}
```

> 横屏适配在游戏和工具类 H5 中是刚需，别忘了测试用户旋转屏幕的场景。

参考来源：[MDN - Screen Orientation API](https://developer.mozilla.org/zh-CN/docs/Web/API/Screen_Orientation_API)

## 3.10 大屏数据可视化的自适应方案

### 等比缩放方案

大屏可视化（如数据大屏）通常按 1920x1080 设计稿开发，然后等比缩放到实际屏幕：

```javascript
// rem + scale 联动方案
function scaleScreen() {
  const designWidth = 1920;
  const designHeight = 1080;
  const screenEl = document.querySelector('#screen-container');

  const scaleX = window.innerWidth / designWidth;
  const scaleY = window.innerHeight / designHeight;
  const scale = Math.min(scaleX, scaleY); // 等比缩放

  screenEl.style.transform = `scale(${scale})`;
  screenEl.style.transformOrigin = '0 0';

  // 居中
  const offsetX = (window.innerWidth - designWidth * scale) / 2;
  const offsetY = (window.innerHeight - designHeight * scale) / 2;
  screenEl.style.position = 'absolute';
  screenEl.style.left = offsetX + 'px';
  screenEl.style.top = offsetY + 'px';
}

scaleScreen();
window.addEventListener('resize', scaleScreen);
```

### ECharts resize

```javascript
// 监听容器变化，图表自适应
const chart = echarts.init(document.querySelector('#chart'));
const resizeObserver = new ResizeObserver(() => {
  chart.resize();
});
resizeObserver.observe(document.querySelector('#chart-container'));
```

### Container Query 容器查询

```css
/* 组件级响应式：根据父容器宽度而非视口宽度 */
.card-wrapper {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 120px 1fr;
  }
}

@container (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
}
```

Container Query 让组件真正实现了"无论放在哪里都能自适应"，不再依赖视口宽度。

### clamp() 限制极端尺寸

```css
/* 字体大小：最小 14px，理想 2vw，最大 24px */
.title {
  font-size: clamp(14px, 2vw, 24px);
}

/* 宽度：最小 300px，理想 50%，最大 600px */
.panel {
  width: clamp(300px, 50%, 600px);
}
```

> 大屏可视化的核心是"缩放到位、图表 resize、极端值兜底"。

参考来源：[MDN - CSS Container Queries](https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_container_queries)、[MDN - clamp()](https://developer.mozilla.org/zh-CN/docs/Web/CSS/clamp)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| 响应式设计原则 | 布局体系理解 | 高 |
| CSS 单位体系 | 单位选型能力 | 高 |
| 1px 边框问题 | 移动端高清屏适配 | 中高 |
| 300ms 点击延迟 | 移动端交互优化 | 中 |
| 安全区适配 | 刘海屏/Home条适配 | 中高 |
| Flexbox vs Grid | 布局方案选型 | 高 |
| 软键盘适配 | 移动端表单体验 | 中 |
| 图片适配全策略 | 图片性能与体验 | 中高 |
| 横竖屏适配 | 屏幕方向处理 | 低 |
| 大屏可视化自适应 | 大屏项目适配 | 中 |

这篇适配方案大全，收藏起来直接照抄。你在移动端适配踩过最离谱的坑是什么？评论区说说。关注怕浪猫，下期讲 H5 性能优化核心。系列进度 3/10。

下一篇拆解 Core Web Vitals、首屏优化、包体积优化、虚拟列表、60fps 动画，性能优化一篇拉满。

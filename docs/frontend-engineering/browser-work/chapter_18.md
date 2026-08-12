---
sidebar_position: 18
---

# 第18章 渲染性能优化

> 渲染性能的核心原则只有一条：不要阻塞主线程。但真正做到这一点，需要理解渲染管线的每个阶段，知道哪些操作触发布局，哪些只触发绘制，哪些连绘制都不触发。

我是怕浪猫，上期讲了 Core Web Vitals，今天进入第 18 章：渲染性能优化。这一章拆解渲染管线瓶颈定位、强制同步布局的避免、虚拟列表实现原理，以及 CSS 动画性能优化的最佳实践。

## 18.1 渲染管线性能分析

### 18.1.1 渲染管线的各阶段开销

渲染管线分为多个阶段，每个阶段的开销不同。优化的关键是定位瓶颈在哪个阶段。

```
渲染管线各阶段及开销

JavaScript → Style → Layout → Paint → Composite

各阶段典型开销：
  JavaScript:  变化大（0-100ms+）
  Style:       小（1-5ms）
  Layout:      中-大（5-50ms+）
  Paint:       中（5-20ms）
  Composite:   小（1-5ms）
```

| 阶段 | 触发条件 | 开销 | 优化方向 |
|------|---------|------|---------|
| Style | class/style 变化 | 小 | 减少选择器复杂度 |
| Layout | 几何属性变化 | 大 | 避免频繁布局 |
| Paint | 视觉属性变化 | 中 | 减少绘制区域 |
| Composite | transform/opacity | 极小 | 优先使用 |

### 18.1.2 哪些 CSS 属性触发哪个阶段

```
CSS 属性与渲染阶段

仅合成（最快）：
  transform
  opacity
  filter（部分浏览器）
  will-change

绘制+合成（较快）：
  color
  background-color
  box-shadow
  border-radius

布局+绘制+合成（最慢）：
  width
  height
  margin
  padding
  border-width
  top/left/right/bottom
  font-size
  text-align
```

| 属性类型 | 示例属性 | 触发阶段 | 性能 |
|---------|---------|---------|------|
| 合成属性 | transform, opacity | Composite | 最优 |
| 绘制属性 | color, background | Paint + Composite | 良好 |
| 布局属性 | width, margin | Layout + Paint + Composite | 差 |

> 记住一条规则：动画只用 transform 和 opacity。这两个属性只触发合成阶段，由 GPU 处理，不阻塞主线程。其他属性动画都会触发布局或绘制，影响性能。

## 18.2 强制同步布局（Forced Reflow）

### 18.2.1 什么是强制同步布局

当你在修改布局属性后立即读取布局属性时，浏览器被迫立即执行布局计算，这称为强制同步布局（Forced Synchronous Layout）或布局抖动（Layout Thrashing）。

```javascript
// 强制同步布局示例
const elements = document.querySelectorAll('.box');

for (let i = 0; i < elements.length; i++) {
  // 1. 读取布局属性 → 触发布局计算
  const width = elements[i].offsetWidth;
  
  // 2. 修改样式 → 标记布局为脏
  elements[i].style.width = width + 10 + 'px';
  
  // 3. 下一轮循环读取 → 浏览器被迫立即计算布局
  // 因为上一轮的修改可能影响当前元素的 offsetWidth
}
```

```
正常渲染管线（批量处理）：
  JS 执行完毕 → Style → Layout → Paint → Composite
  Layout 只执行一次

强制同步布局（逐次执行）：
  JS 读取 → Layout → JS 修改 → JS 读取 → Layout → JS 修改 → ...
  Layout 执行 N 次！
```

### 18.2.2 避免强制同步布局

```javascript
// 错误：读写交替
for (let i = 0; i < elements.length; i++) {
  const width = elements[i].offsetWidth;      // 读
  elements[i].style.width = width + 10 + 'px'; // 写
}

// 正确：先读后写
const widths = elements.map(el => el.offsetWidth);  // 批量读
elements.forEach((el, i) => {
  el.style.width = widths[i] + 10 + 'px';            // 批量写
});
```

| 模式 | 布局次数 | 性能 |
|------|---------|------|
| 读写交替 | N | 极差 |
| 批量读写 | 1 | 良好 |
| 纯写（不读） | 0/1 | 最优 |

### 18.2.3 触发布局的属性

以下属性读取会触发布局计算（如果布局已标记为脏）：

| 类型 | 属性 |
|------|------|
| 尺寸 | offsetWidth, offsetHeight, clientWidth, clientHeight, scrollWidth, scrollHeight |
| 位置 | offsetTop, offsetLeft, scrollTop, scrollLeft, getBoundingClientRect() |
| 滚动 | scrollTop, scrollLeft, scrollIntoView() |
| 其他 | getComputedStyle(), window.innerWidth, window.innerHeight |

> FastDOM 是一个经典的库，它通过将读写操作分别排队，在 requestAnimationFrame 中批量执行，自动避免布局抖动。但理解原理后，手动批量读写也不难实现。

## 18.3 虚拟列表（Virtual List）

### 18.3.1 为什么需要虚拟列表

当列表有数千个元素时，全部渲染会导致严重的性能问题：DOM 节点过多、内存占用大、初次渲染慢。虚拟列表只渲染可视区域内的元素。

```
虚拟列表原理

总数据：10000 条
可视区域：10 条
DOM 节点：~15 条（含缓冲区）

┌──────────────────┐
│  未渲染（占位）    │  ← 用 padding 或 transform 撑开高度
├──────────────────┤
│  缓冲区（上方）    │  ← 2-3 个额外项
├──────────────────┤
│  可视区域         │  ← 10 个真实 DOM 节点
│  item 3          │
│  item 4          │
│  item 5          │
│  ...             │
│  item 12         │
├──────────────────┤
│  缓冲区（下方）    │  ← 2-3 个额外项
├──────────────────┤
│  未渲染（占位）    │  ← 用 padding 撑开高度
└──────────────────┘
```

### 18.3.2 虚拟列表实现

```javascript
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight);
    this.bufferCount = 3;  // 上下各 3 个缓冲项
    
    this.content = document.createElement('div');
    this.content.style.position = 'relative';
    this.content.style.height = items.length * itemHeight + 'px';
    container.appendChild(this.content);
    
    container.addEventListener('scroll', this.onScroll.bind(this));
    this.render(0);
  }
  
  onScroll() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.bufferCount);
    this.render(startIndex);
  }
  
  render(startIndex) {
    const endIndex = Math.min(
      this.items.length,
      startIndex + this.visibleCount + this.bufferCount * 2
    );
    
    this.content.innerHTML = '';
    for (let i = startIndex; i < endIndex; i++) {
      const item = document.createElement('div');
      item.style.position = 'absolute';
      item.style.top = i * this.itemHeight + 'px';
      item.style.height = this.itemHeight + 'px';
      item.style.width = '100%';
      item.textContent = this.items[i];
      this.content.appendChild(item);
    }
  }
}
```

### 18.3.3 虚拟列表的进阶问题

虚拟列表的实现远比上面的基本示例复杂。生产级虚拟列表需要处理以下问题：

| 问题 | 说明 | 解决方案 |
|------|------|----------|
| 变长列表 | 每项高度不同 | 缓存已测量高度 + 预估 |
| 滚动到指定项 | 需要精确位置 | 累积高度计算 |
| 搜索高亮 | 动态修改内容 | 重新渲染可见区 |
| 横向滚动 | 水平虚拟列表 | 同理但换方向 |
| 嵌套滚动 | 树形列表 | 分组虚拟化 |

对于变长列表，常见策略是：先使用预估高度渲染，渲染后测量实际高度并更新缓存。随着用户滚动，缓存越来越准确。React 的 react-window 和 Vue 的 vue-virtual-scroller 都实现了这些进阶功能。

| 优化点 | 说明 | 效果 |
|--------|------|------|
| DOM 节点数 | 仅可视+缓冲 | 从万级降到十级 |
| 内存占用 | 仅渲染项的数据 | 大幅减少 |
| 滚动性能 | 不需要重新渲染全部 | 流畅 |
| 首次渲染 | 仅渲染可视区域 | 快速 |

## 18.4 CSS 动画性能

### 18.4.1 will-change 属性

will-change 属性告诉浏览器元素即将发生变化，让浏览器提前优化。

```css
/* 告诉浏览器这个元素将要变换 */
.animated-element {
  will-change: transform, opacity;
}

/* 不需要动画时移除 */
.animated-element.done {
  will-change: auto;
}
```

| will-change 使用 | 效果 | 风险 |
|-----------------|------|------|
| 动画前设置 | 创建独立合成层 | 内存增加 |
| 动画后移除 | 释放合成层 | — |
| 过多元素设置 | 每个都是合成层 | 内存爆炸 |

> will-change 是双刃剑。它让浏览器提前创建合成层，动画更流畅。但每个合成层都占用 GPU 内存。不要对所有元素设置 will-change，只在即将动画的元素上使用，动画结束后移除。

### 18.4.2 合成层提升

某些条件会让元素自动提升为合成层（Composite Layer），脱离主线程的布局和绘制。

```css
/* 自动提升合成层的条件 */
.layer {
  transform: translateZ(0);        /* 硬件加速 */
  /* 或 */
  will-change: transform;
  /* 或 */
  opacity: 0.99;                    /* 接近 1 但不等于 1 */
  /* 或 */
  position: fixed;                  /* 固定定位 */
  /* 或 */
  filter: blur(0px);               /* 有 filter */
}
```

| 提升条件 | 说明 | 副作用 |
|---------|------|--------|
| 3D transform | translateZ/translate3d | 内存增加 |
| will-change | 显式声明 | 内存增加 |
| opacity < 1 | 透明合成层 | — |
| position: fixed | 固定定位合成层 | — |
| video/canvas | 媒体合成层 | — |
| filter | 滤镜合成层 | — |

### 18.4.3 动画属性选择

```css
/* 差：动画 width/height 触发布局 */
.bad {
  transition: width 0.3s;
}
.bad:hover {
  width: 200px;
}

/* 好：动画 transform 只触发合成 */
.good {
  transition: transform 0.3s;
}
.good:hover {
  transform: scaleX(2);
}

/* 差：动画 top/left 触发布局 */
.bad-position {
  transition: top 0.3s, left 0.3s;
}

/* 好：动画 transform 替代 */
.good-position {
  transition: transform 0.3s;
}
.good-position.move {
  transform: translate(100px, 50px);
}
```

## 18.5 requestAnimationFrame 与渲染调度

### 18.5.1 rAF 的正确使用

```javascript
// 错误：在 rAF 中做布局读写交替
function animateBad() {
  const width = element.offsetWidth;  // 读
  element.style.width = width + 1 + 'px';  // 写
  requestAnimationFrame(animateBad);
}

// 正确：rAF 回调中先写后读
function animateGood() {
  element.style.width = newWidth + 'px';  // 写
  // 下一帧再读
  requestAnimationFrame(() => {
    const width = element.offsetWidth;  // 读（新帧）
    // ...
  });
}
```

### 18.5.2 rAF 与 setInterval 对比

| 特性 | requestAnimationFrame | setInterval |
|------|----------------------|------------|
| 同步 vsync | 是 | 否 |
| 后台暂停 | 是 | 否 |
| 节流 | 自动 | 不会 |
| 精度 | 帧级 | 定时器级 |

> 永远不要用 setInterval 做动画。setInterval 不同步 vsync，可能在一帧内执行多次（浪费），也可能跨帧执行（掉帧）。rAF 是浏览器提供的动画 API，保证每帧执行一次。

## 18.6 CSS containment

### 18.6.1 contain 属性

CSS contain 属性告诉浏览器某个元素的渲染独立于页面其他部分，浏览器可以据此优化渲染。

```css
/* 告诉浏览器这个元素的布局独立 */
.widget {
  contain: layout;  /* 布局独立 */
}

/* 更强的隔离 */
.isolated {
  contain: layout paint size style;
  /* layout: 布局独立 */
  /* paint: 绘制独立（不会溢出） */
  /* size: 尺寸不影响外部 */
  /* style: 样式独立 */
}
```

| contain 值 | 说明 | 效果 |
|-----------|------|------|
| layout | 布局独立 | 外部布局不影响内部 |
| paint | 绘制独立 | 不溢出边界 |
| size | 尺寸独立 | 不依赖内容尺寸 |
| style | 样式独立 | 计数器不影响外部 |
| content | layout+style | 内容级隔离 |
| strict | 全部 | 最强隔离 |

contain 属性可以显著减少渲染开销。对于复杂的组件（如评论区、列表项），设置 contain: layout style paint 可以避免外部布局变化触发内部重新计算。

### 18.6.2 content-visibility

content-visibility: auto 是一个更强大的优化。它让浏览器跳过不可见元素的内容渲染。

```css
/* 不在可视区域的卡片跳过渲染 */
.card {
  content-visibility: auto;
  contain-intrinsic-size: 200px;  /* 预估高度 */
}
```

content-visibility: auto 的效果：不可见的元素不会被渲染（跳过布局和绘制），只保留一个占位空间。当元素滚动到可视区域时，浏览器才渲染它。这类似于虚拟列表，但由浏览器原生实现。

| 特性 | content-visibility: auto | 虚拟列表 |
|------|------------------------|----------|
| 实现 | CSS 声明 | JS 逻辑 |
| DOM 节点 | 保留 | 动态增删 |
| 适用场景 | 中等列表 | 超大列表 |
| 滚动体验 | 良好 | 更流畅 |

> content-visibility: auto 是渲染优化的新武器。对于百级到千级的列表，content-visibility 足够且实现简单。对于万级以上的列表，仍需要虚拟列表。两者也可以结合使用。

## 18.5 requestAnimationFrame 调度机制

### 18.5.1 RAF 与主线程调度

requestAnimationFrame（简称 RAF）是浏览器提供的动画调度 API，它告诉浏览器在下次重绘之前执行回调。RAF 回调在主线程的渲染步骤中执行，保证了动画帧与渲染管线同步。

```
主线程一帧的时间线（16.6ms @ 60fps）

  ├─ Input Events（处理输入事件）
  ├─ RAF Callbacks（执行 RAF 回调）
  ├─ Style（样式计算）
  ├─ Layout（布局计算）
  ├─ Paint（绘制）
  └─ Composite（合成）

  RAF 回调在 Style 之前执行
  → 回调中修改样式，当前帧就能渲染
```

```javascript
// 使用 RAF 做动画
function animate(timestamp) {
  element.style.transform = `translateX(${pos}px)`;
  pos += 2;
  if (pos < 500) {
    requestAnimationFrame(animate);
  }
}
requestAnimationFrame(animate);

// 取消动画
const id = requestAnimationFrame(animate);
cancelAnimationFrame(id);
```

### 18.5.2 RAF vs setTimeout

| 对比项 | requestAnimationFrame | setTimeout |
|--------|---------------------|------------|
| 执行时机 | 下次重绘前 | 指定延迟后 |
| 帧同步 | 是 | 否 |
| 后台标签 | 暂停（节流） | 继续（可能节流） |
| 精度 | 与显示器刷新率同步 | 最小 4ms |
| 适合场景 | 动画 | 定时任务 |

> setTimeout 做动画的问题是：它不知道浏览器何时渲染。如果 setTimeout 回调在渲染之后执行，修改的样式要等到下一帧才渲染，造成丢帧。RAF 保证了回调在渲染之前执行，当前修改当前帧就能生效。

### 18.5.3 requestIdleCallback

requestIdleCallback（RIC）在浏览器空闲时执行低优先级任务，不会阻塞动画和交互。

```javascript
// 空闲时执行低优先级任务
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0 && tasks.length) {
    const task = tasks.shift();
    task();
  }
  if (tasks.length) {
    requestIdleCallback(processTasks);
  }
});

// 设置超时（最多 2 秒后强制执行）
requestIdleCallback(importantTask, { timeout: 2000 });
```

```
一帧中的空闲时间

  ├─ Input Events
  ├─ RAF Callbacks
  ├─ Style → Layout → Paint → Composite
  ├─ 空闲时间（剩余的帧时间）
  │   └─ requestIdleCallback 在此执行
  └─ 下一帧

  如果一帧的工作提前完成，剩余时间就是空闲时间
  deadline.timeRemaining() 返回剩余空闲时间
```

| 对比项 | requestAnimationFrame | requestIdleCallback |
|--------|---------------------|-------------------|
| 优先级 | 高（渲染前） | 低（空闲时） |
| 适合场景 | 动画 | 数据处理、预计算 |
| 后台标签 | 暂停 | 暂停 |
| 时间限制 | 无（但应在帧内完成） | deadline.timeRemaining() |

## 18.6 CSS contain 属性

CSS contain 属性告诉浏览器某个元素的样式和布局独立于页面其他部分，浏览器可以据此进行渲染优化。

### 18.6.1 contain 的值

```css
/* 完全隔离 */
.container {
  contain: layout paint style size;
}

/* 常用组合 */
.card {
  contain: layout paint style;
}

/* 等价于 content-visibility 的底层机制 */
.widget {
  contain: layout paint style;
  content-visibility: auto;
  contain-intrinsic-size: 200px 300px;
}
```

| 值 | 效果 | 说明 |
|----|------|------|
| layout | 布局隔离 | 内部布局变化不影响外部 |
| paint | 绘制隔离 | 内部不绘制到外部边界 |
| style | 样式隔离 | 计数器和引用不在内外传递 |
| size | 尺寸隔离 | 元素尺寸不受内容影响 |

### 18.6.2 contain 性能影响

```
无 contain：
  修改某元素 → 浏览器重新计算整个页面布局

有 contain: layout：
  修改某元素 → 只重新计算该元素内部布局
  外部布局不受影响

有 contain: layout paint：
  修改某元素 → 只重新计算该元素内部
  绘制也限制在元素边界内
```

> contain 属性是渲染优化的底层工具。它本质上是给浏览器一个提示：「这个元素的内部变化不会影响外部」。浏览器可以据此跳过不必要的布局和绘制计算。content-visibility: auto 就是基于 contain 实现的。

## 18.7 被动事件监听器

### 18.7.1 passive 事件监听器

某些触摸和滚轮事件监听器会阻塞浏览器的滚动，因为浏览器需要等待监听器执行完毕才能决定是否滚动。passive 监听器告诉浏览器不会调用 preventDefault，浏览器可以立即滚动。

```javascript
// 非被动监听器（可能阻塞滚动）
document.addEventListener('touchmove', (e) => {
  // 浏览器等待这里执行完才能滚动
  doSomething();
}, { passive: false });

// 觋动监听器（不阻塞滚动）
document.addEventListener('touchmove', (e) => {
  // 浏览器不等这里执行完就滚动
  doSomething();
}, { passive: true });
```

```
非被动监听器流程：
  触摸事件 → 执行监听器 → 检查 preventDefault → 滚动/不滚动
  延迟：0-100ms+

被动监听器流程：
  触摸事件 → 立即滚动 + 同时执行监听器
  延迟：0ms
```

| 对比 | 非 passive | passive |
|------|-----------|---------|
| 滚动延迟 | 有 | 无 |
| preventDefault | 可调用 | 无效 |
| 默认值 | Chrome 警告 | 建议显式设置 |

> Chrome 从 56 版本开始，默认将 document 和 body 上的 touchstart 和 touchmove 事件视为 passive。如果在这些事件中调用 preventDefault，会被忽略并输出警告。对于需要阻止滚动的场景（如下拉刷新），必须显式设置 { passive: false }。

## 18.8 Web Animations API

Web Animations API（WAAPI）是用 JavaScript 操作动画的标准 API，它提供了比 CSS 动画更灵活的控制能力。

```javascript
// 使用 WAAPI 创建动画
const animation = element.animate([
  { transform: 'translateX(0px)' },
  { transform: 'translateX(500px)' }
], {
  duration: 1000,
  easing: 'ease-in-out',
  iterations: Infinity,
  direction: 'alternate'
});

// 控制
animation.pause();
animation.play();
animation.reverse();
animation.finish();

// 跳转到特定时间点
animation.currentTime = 500;

// 播放速率
animation.playbackRate = 2;  // 2 倍速
```

| 对比项 | CSS 动画 | Web Animations API |
|--------|---------|-------------------|
| 声明方式 | CSS | JavaScript |
| 运行时控制 | 有限 | 完整 |
| 动态修改 | 困难 | 容易 |
| 性能 | 相同 | 相同 |
| 适合场景 | 固定动画 | 动态动画 |

> WAAPI 和 CSS 动画在底层使用同一个动画引擎，性能表现一致。选择哪个取决于控制需求。如果动画在运行时不需要修改（如加载动画），CSS 更简洁。如果需要动态控制（如用户交互驱动的动画），WAAPI 更灵活。

## 18.9 滚动性能优化全策略

### 18.9.1 滚动性能问题根源

滚动性能问题的根本原因是：主线程被阻塞，无法及时处理滚动事件和渲染。

```
滚动卡顿的常见原因

1. 滚动事件监听器太重
   → 使用 passive 监听器 + 节流

2. 滚动中触发布局
   → 避免读取 offsetTop/scrollTop 等强制布局属性

3. 滚动中触发长时间 JS
   → 将计算移到 Worker 或 requestIdleCallback

4. 大量 DOM 元素
   → 使用虚拟列表或 content-visibility

5. 复杂的背景或阴影
   → 简化或使用 will-change
```

### 18.9.2 滚动优化检查清单

| 优化项 | 方法 | 效果 |
|--------|------|------|
| 事件监听 | passive: true | 消除滚动延迟 |
| 节流 | throttle/RAF | 减少回调频率 |
| 避免强制布局 | 缓存 offsetTop 等 | 消除 Layout Thrashing |
| 虚拟列表 | 只渲染可见项 | 减少 DOM 数量 |
| contain | contain: layout paint | 隔离布局影响 |
| will-change | will-change: transform | 提升为合成层 |
| overscroll | overscroll-behavior: contain | 阻止滚动链 |

```css
/* 滚动容器优化 */
.scroll-container {
  overflow: auto;
  contain: layout paint;
  will-change: scroll-position;
  overscroll-behavior: contain;
}

/* 列表项优化 */
.list-item {
  contain: layout paint style;
  content-visibility: auto;
  contain-intrinsic-size: 0 60px;
}
```

> overscroll-behavior: contain 是一个容易被忽视的优化。它阻止滚动「链式传播」——当内部滚动到底时不会触发外部滚动。对于弹窗内的滚动列表特别有用，防止弹窗滚动到底后背景页面跟着滚动。

## 18.10 Layout Thrashing 详解

### 18.10.1 强制同步布局

Layout Thrashing（布局抖动）是最常见的性能陷阱。当 JavaScript 交替读取布局属性和修改样式时，浏览器被迫多次执行同步布局计算。

```javascript
// Layout Thrashing 示例
elements.forEach(el => {
  const top = el.offsetTop;    // 读取布局 → 触发布局计算
  el.style.top = top + 10;     // 写入样式 → 标记布局为脏
});
// 下一次读取 offsetTop 又触发完整布局计算
// 循环中每次读取都触发一次布局

// 正确写法：先读后写
const tops = elements.map(el => el.offsetTop);  // 批量读
elements.forEach((el, i) => {
  el.style.top = tops[i] + 10;                   // 批量写
});
```

```
布局抖动原理

写样式 → 布局标记为脏（不立即计算）
读布局属性 → 必须先计算布局（同步计算）

交替读写：
  写 → 读 → 写 → 读 → ...
  每次读都触发一次完整布局计算
  N 个元素 = N 次布局

批量读写：
  读 → 读 → 读 → 写 → 写 → 写
  只触发 1 次布局
```

| 触发布局的属性 | 不触发布局的属性 |
|--------------|---------------|
| offsetTop/Left | transform |
| offsetWidth/Height | opacity |
| clientTop/Left/Width/Height | color |
| scrollTop/Left | background |
| scrollWidth/Height | z-index |
| getComputedStyle() | font-size |
| getBoundingClientRect() | — |

> Layout Thrashing 的危害在于它很难被 DevTools 的常规检查发现。Lighthouse 会报告「Avoid forced synchronous layout」但不会告诉你具体在哪里。Chrome DevTools 的 Performance 面板中的紫色 Layout 块可以帮助定位。FastDOM 库可以自动批量读写操作。

## 18.11 长任务优化

### 18.11.1 识别和拆分长任务

长任务（Long Task）是执行时间超过 50ms 的 JavaScript 任务。它们会阻塞主线程，导致交互延迟。

```javascript
// 长任务拆分：使用 scheduler.yield()
async function processLargeArray(items) {
  const results = [];
  for (let i = 0; i < items.length; i++) {
    results.push(processItem(items[i]));
    // 每 5ms 让出一次主线程
    if (i % 100 === 0 && scheduler.yield) {
      await scheduler.yield();
    }
  }
  return results;
}

// 使用 requestIdleCallback 拆分
function processIdle(items) {
  return new Promise(resolve => {
    const results = [];
    function process(deadline) {
      while (deadline.timeRemaining() > 0 && items.length) {
        results.push(processItem(items.shift()));
      }
      if (items.length) {
        requestIdleCallback(process);
      } else {
        resolve(results);
      }
    }
    requestIdleCallback(process);
  });
}
```

### 18.11.2 PerformanceObserver 监控长任务

```javascript
// 监控长任务
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Long Task:', entry.duration, 'ms');
    console.log('Attribution:', entry.attribution);
  }
});
observer.observe({ entryTypes: ['longtask'] });
```

| 拆分方式 | 适用场景 | 优先级控制 |
|---------|---------|----------|
| scheduler.yield() | 通用 | 高 |
| requestIdleCallback | 低优先级 | 低 |
| setTimeout(0) | 简单拆分 | 中 |
| Web Worker | 纯计算 | 不阻塞主线程 |

> Web Worker 是处理纯计算任务的最佳方案。Worker 在独立线程执行，完全不阻塞主线程。限制是 Worker 不能访问 DOM。对于需要操作 DOM 的任务，只能用 scheduler.yield() 或 requestIdleCallback 拆分。

## 18.12 渲染优化检查清单

### 18.12.1 渲染性能自检表

```
渲染性能优化检查清单

1. 动画属性
   [ ] 使用 transform 而非 top/left
   [ ] 使用 opacity 而非 visibility/display
   [ ] 避免在动画中改变 width/height

2. 滚动性能
   [ ] 滚动监听器使用 passive: true
   [ ] 使用 overscroll-behavior: contain
   [ ] 长列表使用 content-visibility 或虚拟列表

3. 布局优化
   [ ] 避免布局抖动（批量读写）
   [ ] 使用 contain: layout paint
   [ ] 避免频繁修改 DOM 结构

4. 任务调度
   [ ] 长任务拆分（< 50ms）
   [ ] 纯计算移到 Web Worker
   [ ] 低优先级任务用 requestIdleCallback

5. 资源优化
   [ ] 图片懒加载
   [ ] 非关键 CSS/JS 延迟加载
   [ ] 字体使用 font-display: swap
```

> 性能优化是持续过程。使用 Lighthouse 定期审计、Chrome DevTools 持续监控、CrUX 数据验证真实用户体验。优化的优先级应该是：先解决影响 INP/LCP 的关键问题，再处理 CLS 问题，最后进行微优化。

## 18.13 图片加载优化

### 18.13.1 图片格式选择

```
现代图片格式对比

AVIF（最新）
  → 压缩率: 比 WebP 再小 30%
  → 浏览器支持: Chrome 85+, Firefox 86+
  → 编码速度: 慢
  → 适用: 大图优化

WebP（主流）
  → 压缩率: 比 JPEG 小 25-35%
  → 浏览器支持: Chrome 32+, Firefox 65+, Safari 14+
  → 编码速度: 中
  → 适用: 通用优化

JPEG XL（未来）
  → 压缩率: 与 AVIF 相当
  → 浏览器支持: 有限
  → 特点: 支持无损 JPEG 转换
```

| 格式 | 压缩率 | 支持度 | 适用场景 |
|------|--------|--------|----------|
| AVIF | 最好 | 中 | 大图 |
| WebP | 好 | 高 | 通用 |
| JPEG | 差 | 全 | 兼容性 |
| PNG | 无损 | 全 | 透明图 |
| WebP | 好 | 高 | 通用 |

```html
<!-- 响应式图片最佳实践 -->
<picture>
  <source type="image/avif" srcset="photo.avif">
  <source type="image/webp" srcset="photo.webp">
  <img src="photo.jpg" alt="photo" loading="lazy" decoding="async">
</picture>
```

### 18.13.2 懒加载策略

```html
<!-- 原生懒加载 -->
<img src="photo.jpg" loading="lazy" decoding="async">

<!-- 首屏图片不懒加载，但加 fetchpriority -->
<img src="hero.jpg" fetchpriority="high" decoding="async">

<!-- Intersection Observer 懒加载（更精确控制） -->
<script>
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
}, { rootMargin: '200px' }); // 提前 200px 加载

document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
</script>
```

| 加载策略 | 适用 | 效果 |
|---------|------|------|
| eager（默认） | 首屏图片 | 立即加载 |
| lazy | 非首屏图片 | 延迟加载 |
| fetchpriority="high" | LCP 图片 | 优先加载 |
| IntersectionObserver | 精确控制 | 自定义 |

## 18.14 字体加载优化

### 18.14.1 font-display 策略

```css
/* font-display 策略 */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2');
  font-display: swap; /* 最推荐 */
}

/*
font-display 选项：
  auto: 浏览器决定（通常 = block）
  block: 3s 内不显示文字，然后回退
  swap: 立即显示回退字体，加载后切换
  fallback: 100ms 回退，3s 后如果还没加载完则继续回退
  optional: 100ms 回退，如果加载完就换，否则不换
*/
```

| font-display | 首屏文字 | CLS | 适用 |
|-------------|---------|-----|------|
| swap | 立即显示 | 可能偏移 | 正文 |
| fallback | 100ms后显示 | 较小 | 重要文字 |
| optional | 100ms后显示 | 最小 | 装饰文字 |
| block | 3s不显示 | 无 | 图标字体 |

> font-display: swap 是大多数场景的最佳选择。它立即显示回退字体，避免文字「闪现」延迟。但需要注意 CLS——字体切换可能导致布局偏移。使用 `size-adjust` 和 `font-metric-override` 可以减小偏移。

## 18.15 资源加载优先级

### 18.15.1 浏览器资源优先级

浏览器对不同类型的资源分配不同的加载优先级。理解优先级机制可以帮助优化关键资源加载。

```
浏览器资源优先级（Chrome）

Highest:
  HTML 文档
  CSS（<link> 在 <head> 中）
  Font（font-display: block）

High:
  <script> 在 <head> 中（无 defer/async）
  Image（fetchpriority=high）
  Font（其他）

Medium:
  <script defer>
  Image（普通）
  <link rel="preload">

Low:
  <script async>
  Image（loading=lazy）
  <link rel="prefetch">

Lowest:
  <link rel="dns-prefetch">
  <link rel="preconnect">
```

| 资源类型 | 默认优先级 | 可调整 |
|---------|----------|--------|
| HTML | Highest | 否 |
| CSS（head） | Highest | 否 |
| JS（head） | High | defer→Medium |
| Image | Medium | fetchpriority |
| Font | High | font-display |

```html
<!-- 资源优先级优化 -->
<head>
  <!-- CSS 最高优先级 -->
  <link rel="stylesheet" href="critical.css">
  
  <!-- 预加载关键字体 -->
  <link rel="preload" as="font" href="font.woff2" crossorigin>
  
  <!-- LCP 图片高优先级 -->
  <link rel="preload" as="image" href="hero.jpg" fetchpriority="high">
  
  <!-- 非关键 JS 延迟加载 -->
  <script src="analytics.js" defer></script>
</head>
```

### 18.15.2 preload vs prefetch vs preconnect

```
资源提示对比

preload:
  → 当前页面必需的资源
  → 高优先级加载
  → 例：首屏字体、LCP 图片

prefetch:
  → 下一个页面可能需要的资源
  → 低优先级加载
  → 空闲时下载
  → 例：下一页的 JS chunk

preconnect:
  → 提前建立连接
  → DNS + TCP + TLS
  → 不下载资源
  → 例：CDN 域名

dns-prefetch:
  → 仅预解析 DNS
  → 最轻量
  → 例：第三方域名
```

| 指令 | 作用 | 优先级 | 适用 |
|------|------|--------|------|
| preload | 预加载资源 | 高 | 当前页关键资源 |
| prefetch | 预获取资源 | 低 | 下页可能用 |
| preconnect | 预连接 | 中 | 关键域名 |
| dns-prefetch | DNS 预解析 | 最低 | 次要域名 |

> 资源提示是性能优化的「免费午餐」。正确使用 preload 可以将 LCP 降低 200-500ms。但过度使用会适得其反——preload 太多资源会分散带宽，反而延迟关键资源。最佳实践：只 preload 1-2 个关键资源（LCP 图片 + 首屏字体）。

## 18.16 Service Worker 缓存策略

### 18.16.1 缓存策略选择

```
Service Worker 缓存策略

1. Cache First（缓存优先）
   → 先查缓存，缓存 miss 再请求网络
   → 适用：静态资源（CSS/JS/图片）

2. Network First（网络优先）
   → 先请求网络，失败再查缓存
   → 适用：动态内容（API 响应）

3. Stale While Revalidate（后台更新）
   → 返回缓存，同时后台请求更新
   → 适用：频繁更新但不紧急的内容

4. Cache Only（仅缓存）
   → 只查缓存，不请求网络
   → 适用：离线资源

5. Network Only（仅网络）
   → 只请求网络
   → 适用：实时数据
```

```javascript
// Stale While Revalidate 示例
self.addEventListener('fetch', (event) => {
  event.respondWith(async () => {
    const cache = await caches.open('dynamic');
    const cached = await cache.match(event.request);
    const fetchPromise = fetch(event.request).then(response => {
      cache.put(event.request, response.clone());
      return response;
    });
    return cached || fetchPromise;
  }());
});
```

| 策略 | 缓存命中 | 缓存未命中 | 适用 |
|------|---------|----------|------|
| Cache First | 快 | 慢 | 静态资源 |
| Network First | 慢 | 慢 | 动态内容 |
| SWR | 快 | 慢 | 频繁更新 |
| Cache Only | 快 | 失败 | 离线 |

> Service Worker 缓存是 PWA 离线能力的基础。Workbox 库提供了开箱即用的缓存策略实现。选择策略的关键问题是：数据更新频率有多高？用户能接受多旧的数据？对于关键业务数据，使用 Network First 确保最新；对于 UI 资源，使用 Cache First 或 SWR。

## 本章核心知识总结

| 优化领域 | 核心原则 | 关键实践 |
|---------|---------|---------|
| 渲染管线 | 减少触发阶段 | 只用 transform/opacity |
| 强制布局 | 批量读写 | 先读后写，不交替 |
| 虚拟列表 | 只渲染可视区 | DOM 节点数十级 |
| 合成层 | GPU 加速 | will-change 适度使用 |
| 动画 | rAF 同步 | 不用 setInterval |

觉得有用？收藏起来，下次排查渲染性能问题时直接用。

你的长列表是怎么做的？有没有用虚拟列表？评论区聊聊。

关注怕浪猫，下期我们讲内存管理与垃圾回收优化。系列进度 18/24。

下期预告：第 19 章「内存管理与垃圾回收优化」。我们会拆解 V8 的分代 GC（Garbage Collection，垃圾回收）机制、内存泄漏的常见模式、以及如何用 DevTools 分析内存问题。怕浪猫下期见。

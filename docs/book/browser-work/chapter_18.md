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

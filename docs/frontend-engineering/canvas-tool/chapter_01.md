---
sidebar_position: 1
---

# 第1章 浏览器图形渲染全景：从 HTML 到像素的数据流

每次面试被问到"Canvas 在浏览器里到底怎么渲染的"，你就开始背"HTML5 新增、用 JavaScript 绘图"？

这些回答在三年前还能蒙混过关，现在面试官想听的是：浏览器渲染管线中 Canvas 处于哪个环节、合成层怎么提升、从 `<canvas>` 标签到屏幕像素经历了什么数据流。

我是怕浪猫，一个把浏览器图形栈翻了个底朝天的前端工程师。从今天开始，我开一个系列——**Canvas 工程全书**，17 篇文章，从浏览器渲染原理一路讲到 WebGPU 和跨技术协作。

这一篇是第 1 章，先把地基打好：搞清楚浏览器是怎么把 HTML 变成像素的，Canvas 又挂在渲染树的哪个节点上。

## 1.1 浏览器渲染管线回顾：从 HTML 到像素

浏览器渲染管线的本质是一套流水线：输入是 HTML/CSS/JS，输出是屏幕上的像素。这条流水线有明确的阶段划分，每个阶段都有自己的输入和输出。

理解这条流水线，是理解 Canvas 性能特征的前提。因为 Canvas 不是孤立存在的，它嵌入在这条流水线里，受整条流水线的调度。

### 1.1.1 DOM 树与 CSSOM 树的构建

浏览器拿到 HTML 文档后，第一件事是解析。解析过程分两条线并行：

**HTML 解析器**逐字节读取文档，构建 DOM（Document Object Model，文档对象模型）树。DOM 树的每个节点对应一个 HTML 元素，节点之间通过父子关系连接。

```
HTML 文档                    DOM 树
<html>                      html
  <head>                    ├── head
    <title>Hi</title>       │   └── title: "Hi"
  </head>                   ├── body
  <body>                    │   ├── canvas#main
    <canvas id="main">      │   └── script
    <script>...</script>    └── (text nodes)
  </body>
```

**CSS 解析器**同时解析所有样式来源（外部样式表、`<style>` 标签、内联样式），构建 CSSOM（CSS Object Model，CSS 对象模型）树。CSSOM 树和 DOM 树结构类似，但多了一层继承和层叠计算。

> 金句：DOM 树描述"有什么"，CSSOM 树描述"长什么样"，两棵树合并才能算出"最终什么样"。

当解析器遇到 `<canvas>` 元素时，会创建一个 HTMLCanvasElement 节点挂到 DOM 树上。这个节点本身是普通的 DOM 节点，但它内部持有一块绘图缓冲区——这才是 Canvas 的核心。

CSS 解析器会给这个 canvas 节点计算样式：`display` 默认是 `inline`（这是很多人踩的坑），`width` 和 `height` 属性和 CSS 的 `width`/`height` 是两套体系，后面会详细讲。

JavaScript 的执行会阻塞 DOM 解析（除非用了 `async` 或 `defer`），这也是为什么你的 Canvas 初始化代码要放在 DOMContentLoaded 之后。

### 1.1.2 布局（Layout）与绘制（Paint）

DOM 树和 CSSOM 树合并后，浏览器生成**渲染树（Render Tree）**。渲染树只包含需要显示的节点（`display: none` 的节点不会出现在渲染树中）。

接下来进入两个关键阶段：

**布局（Layout）**：计算每个渲染树节点的几何信息——位置和大小。浏览器从根节点开始递归计算，确定每个元素在视口中的精确矩形区域。

对于 canvas 元素来说，布局阶段会确定它在页面中的位置和 CSS 像素尺寸。但注意，CSS 像素尺寸和 canvas 的绘图缓冲区尺寸是两个独立的概念：

```javascript
// CSS 尺寸（布局阶段决定）
canvas.style.width = '800px';   // 元素在页面上占 800 CSS 像素宽
canvas.style.height = '600px';  // 元素在页面上占 600 CSS 像素高

// 绘图缓冲区尺寸（属性设置，独立于 CSS）
canvas.width = 1600;   // backing store 宽 1600 物理像素
canvas.height = 1200;  // backing store 高 1200 物理像素
```

如果两者比例不一致，绘图缓冲区会被拉伸或压缩到 CSS 尺寸，导致模糊或变形。这是高分屏适配的核心问题，第2章会详细讲。

**绘制（Paint）**：将渲染树节点转化为绘制指令。浏览器为每个图层生成一个绘制指令列表，记录"在什么位置画什么颜色的什么形状"。

对于普通 DOM 元素，绘制指令由浏览器自动生成。对于 canvas 元素，浏览器不会去解析你在 canvas 上画了什么——它只生成一条指令："把这个 canvas 的绘图缓冲区内容贴到对应位置"。

> 金句：Canvas 是浏览器渲染管线里的"飞地"——浏览器只管它的位置和大小，不管它内部画了什么。

这意味着你在 canvas 上画 1 个矩形还是 10000 个矩形，对浏览器的布局和绘制阶段来说没有区别。Canvas 的绘制负担完全在你的 JavaScript 代码和 2D 上下文上。

### 1.1.3 合成层（Compositing Layer）与 GPU 加速

绘制阶段结束后，浏览器进入**合成（Compositing）**阶段。这是最后一步——把各个图层按照正确的顺序合并成最终画面。

现代浏览器渲染时，页面被分成多个**合成层（Compositing Layer）**。每个合成层对应 GPU 中的一个纹理（Texture）。合成器（Compositor）负责把这些纹理按 z-order 叠加输出到屏幕。

哪些情况会触发合成层提升（Promotion）：

| 触发条件 | 说明 | Canvas 相关性 |
|---------|------|--------------|
| CSS 3D 变换（transform: translateZ(0) 等） | 强制提升为合成层 | 常用于 canvas 性能优化 |
| CSS opacity < 1 | 透明度需要独立合成 | canvas 透明度动画 |
| CSS will-change: transform | 浏览器预判会变化 | 推荐用于高频更新 canvas |
| CSS filter | 滤镜需要独立层处理 | canvas 上方叠加滤镜 |
| CSS position: fixed | 固定定位元素 | 全屏 canvas 场景 |
| video、canvas 元素本身 | 部分浏览器自动提升 | canvas 可能自动成为合成层 |

Canvas 元素本身在某些浏览器中会自动提升为合成层，这意味着它的内容更新不需要触发整页重绘。但前提是你的 canvas 满足条件——比如它没有被其他元素覆盖触发重绘区域。

**GPU 加速的意义**：

合成阶段在 GPU 上执行，意味着各层纹理的叠加是 GPU 并行处理的。对于 Canvas 来说：

```javascript
// 如果 canvas 是独立的合成层，以下操作只触发 canvas 自身的重绘
ctx.clearRect(0, 0, canvas.width, canvas.height);
ctx.fillRect(x, y, w, h);
// 浏览器合成器只需要把新的 canvas 纹理和其他层叠加
// 不需要重新绘制页面其他部分
```

> 金句：合成层是 Canvas 性能的第一道防线——不被合成层隔离开的 Canvas，每次重绘都会拖累整页。

一个常见的性能问题：canvas 上方有一个频繁更新的 DOM 元素（比如 tooltip），如果它们在同一个合成层，tooltip 的更新会导致 canvas 也被重绘。解决方案是把 canvas 提升为独立合成层：

```css
canvas {
  will-change: transform;  /* 提示浏览器提升为合成层 */
  transform: translateZ(0); /* 兼容性更好的强制提升方式 */
}
```

## 1.2 图形 API 在浏览器中的演进史

理解 Canvas 的现状，需要知道它是怎么来的。浏览器图形 API 的演进是一条"从无到有、从 CPU 到 GPU"的路线。

### 1.2.1 早期方案：VML 与 Flash 时代

2000 年代初，浏览器没有原生的矢量绘图能力。开发者要画图，只有几条路：

**VML（Vector Markup Language，矢量标记语言）**：微软在 IE 5.0 中引入的 XML 格式矢量图形标准。它用 XML 标签描述图形，由浏览器渲染。但 VML 只有 IE 支持，且性能很差。

```html
<!-- VML 示例：只在 IE 中有效 -->
<v:oval style="width:100pt;height:75pt" fillcolor="red">
</v:oval>
```

**Flash**：Adobe（当时还是 Macromedia）的 Flash Player 插件统治了网页图形近十年。Flash 使用 SWF（Small Web Format）格式，通过 ActionScript 编程绘图，性能远超浏览器原生能力。

**SVG 插件**：Adobe SVG Viewer 等插件尝试在浏览器中支持 SVG，但需要用户安装，普及率低。

这个阶段的核心矛盾：浏览器自身没有高性能图形能力，依赖插件带来安全、性能、兼容性三重问题。

### 1.2.2 Canvas 2D Context 的诞生（HTML5 规范）

2004 年，Apple 在 Safari 中首次实现了 Canvas 元素，灵感来自 Mac OS X 的 Dashboard widget。随后 Mozilla 在 Firefox 中跟进，Opera 也实现了 Canvas 支持。

Canvas 的设计哲学很简洁：

```javascript
// 获取一块画布
const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');

// 用 JavaScript 命令绘图
ctx.fillStyle = 'red';
ctx.fillRect(10, 10, 100, 100);
```

Canvas 的核心设计决策是**即时模式（Immediate Mode）**——你发出绘制命令，浏览器立即执行到像素缓冲区，不保留任何图元信息。画完之后，图形就变成了像素，你无法再操作"那个矩形"——你只能清空重来。

这个决策的代价是牺牲了交互性（需要自己实现命中检测），换来的是极高的绘制性能和极低的内存开销。

HTML5 规范在 2014 年正式定稿时，Canvas 2D Context 成为标准的一部分。所有现代浏览器都支持。

### 1.2.3 WebGL：把 GPU 带进浏览器

Canvas 2D Context 虽然好用，但它运行在 CPU 上，无法利用 GPU 的并行计算能力。对于 3D 图形和大规模数据可视化，2D Context 的性能不够。

2011 年，WebGL 1.0 规范发布，由 Khronos Group 维护。WebGL 本质上是 OpenGL ES（Open Graphics Library for Embedded Systems，嵌入式版开放图形库）2.0 的浏览器绑定，通过 Canvas 元素提供 GPU 编程接口。

```javascript
// 同一个 canvas 元素，可以获取不同的上下文
const canvas = document.getElementById('myCanvas');

const ctx2d = canvas.getContext('2d');      // 2D 位图上下文
const gl = canvas.getContext('webgl');       // WebGL 上下文（GPU）
const gl2 = canvas.getContext('webgl2');     // WebGL 2.0 上下文
```

WebGL 的出现让浏览器能够做真正的 3D 渲染、GPU 加速的图像处理、大规模粒子系统等。Three.js、Babylon.js 等 3D 引擎都是建立在 WebGL 之上的。

### 1.2.4 WebGPU：下一代图形 API

WebGL 的设计基于 OpenGL ES 2.0/3.0，这是 2007-2012 年的技术。现代图形 API（Vulkan、Metal、Direct3D 12）已经大幅领先，WebGL 的架构成了瓶颈。

2023 年，WebGPU 开始在 Chrome 113 中正式发布。WebGPU 不是 WebGL 的升级版，而是全新的设计：

| 维度 | WebGL | WebGPU |
|------|-------|--------|
| 底层映射 | OpenGL ES | Vulkan / Metal / D3D12 |
| 着色器语言 | GLSL | WGSL（WebGPU Shading Language） |
| 资源绑定 | 隐式全局状态 | 显式 BindGroup |
| 计算着色器 | 不支持 | 原生支持 |
| CPU 开销 | 高（状态验证多） | 低（显式声明） |

WebGPU 的详细内容会在第13章展开，这里只需要知道：它是浏览器图形 API 的下一代标准，同时支持高性能渲染和 GPU 通用计算。

## 1.3 浏览器中的"画布"到底挂在渲染树的哪个节点？

前面的渲染管线回顾里，canvas 元素被当作普通 DOM 节点处理。但它有一个特殊性——它持有一块独立的位图缓冲区。这个缓冲区在渲染树和合成阶段中的位置，决定了 Canvas 的性能行为。

### 1.3.1 `<canvas>` 元素的 DOM 定位

`<canvas>` 在 DOM 树中就是一个普通的 HTML 元素，标签名为 `canvas`，继承自 HTMLElement。它有两个特殊的属性：

```javascript
const canvas = document.querySelector('canvas');

// 这两个是 HTML 属性，不是 CSS 属性
console.log(canvas.width);   // 默认 300
console.log(canvas.height);  // 默认 150

// 它们控制的是绘图缓冲区的分辨率
// 和 CSS 的 width/height 完全独立
```

DOM 定位方面，canvas 元素和其他元素没有区别。它可以被 `querySelector` 选中，可以被 `appendChild` 移动，可以监听 DOM 事件。

但有一个关键细节：canvas 元素的内容**不在 DOM 树中**。你在 canvas 上画的所有东西——矩形、文本、图片——都只是像素，不是 DOM 节点。这就是为什么 canvas 无法被屏幕阅读器识别，也无法通过 DOM API 操作已绘制的内容。

### 1.3.2 Canvas 与周围文档流的排版关系

canvas 元素默认 `display: inline`，这意味着它像一段文字一样参与行内布局。这会导致一些常见问题：

```html
<!-- 常见坑：canvas 下方出现间隙 -->
<div>
  <canvas width="800" height="600"></canvas>
</div>
<!-- div 的高度比 canvas 多几个像素，因为 inline 元素有行内基线对齐的间隙 -->
```

解决方案通常是改 display：

```css
canvas {
  display: block;  /* 消除行内基线间隙 */
}
```

canvas 的 CSS 尺寸决定了它在文档流中占据的空间。如果 CSS 尺寸和 width/height 属性的比例不一致，canvas 的绘图缓冲区会被缩放：

```javascript
// 绘图缓冲区：400 x 300
canvas.width = 400;
canvas.height = 300;

// CSS 显示尺寸：800 x 600（放大 2 倍）
canvas.style.width = '800px';
canvas.style.height = '600px';

// 你在 canvas 上画一个 10x10 的矩形
ctx.fillRect(0, 0, 10, 10);
// 屏幕上显示为 20x20 CSS 像素的矩形（被放大了）
```

> 金句：canvas 的 width/height 属性定义"画布分辨率"，CSS 的 width/height 定义"显示尺寸"，两者混淆是新手第一大坑。

### 1.3.3 Canvas 的合成层提升条件

前面提到，canvas 元素在某些条件下会自动成为独立的合成层。实际情况更复杂：

**自动提升的情况**：
- canvas 元素使用了 CSS `will-change` 属性
- canvas 元素被设置了 CSS 3D 变换
- canvas 元素有 CSS `opacity` 小于 1
- 在部分浏览器中，使用 WebGL 上下文的 canvas 会自动提升

**不会自动提升的情况**：
- 普通的 2D canvas，没有特殊 CSS 属性
- 被其他元素覆盖的 canvas（可能被合并到父合成层）

手动提升 canvas 为合成层的方法：

```css
/* 方法 1：will-change（推荐，语义最明确） */
canvas {
  will-change: transform;
}

/* 方法 2：3D 变换（兼容性最好） */
canvas {
  transform: translateZ(0);
}

/* 方法 3：CSS contain（较新，部分浏览器支持） */
canvas {
  contain: strict;
}
```

提升合成层的代价是 GPU 内存——每个合成层都需要一个独立的纹理。对于大尺寸 canvas（比如 1920x1080），一张 RGBA 纹理就要 8MB 显存。所以不要无脑提升，只在需要频繁重绘或需要隔离时提升。

## 1.4 从 `<canvas>` 标签到屏幕像素：一次完整的数据流

前面分别讲了渲染管线的各个阶段。现在把它们串起来，追踪一次 canvas 绘制的完整数据流。

### 1.4.1 元素属性解析（width/height vs CSS 宽高）

当浏览器解析到 `<canvas width="800" height="600">` 时：

1. 创建 HTMLCanvasElement 实例
2. 设置 `width` 属性为 800，`height` 属性为 600
3. 分配 800 x 600 x 4 = 1,920,000 字节的像素缓冲区（RGBA 每像素 4 字节）
4. 将缓冲区初始化为透明黑（每个像素 rgba(0,0,0,0)）

如果你后续修改 width 或 height 属性：

```javascript
canvas.width = 1024;  // 会清空整个画布并重新分配缓冲区
canvas.height = 768;  // 同上

// 所有已绘制内容丢失
// 所有上下文状态重置（变换矩阵、样式等）
```

> 金句：修改 canvas.width/height 不是 resize，是 reset——缓冲区被重新分配，一切从头来。

这就是为什么画布尺寸变更需要特殊的重绘策略：你需要保存所有图元的数据，尺寸变更后重新绘制全部内容。

### 1.4.2 上下文（Context）的获取与初始化

`getContext()` 是 Canvas API 的入口。它的内部做了什么：

```javascript
const ctx = canvas.getContext('2d');
```

1. 检查 canvas 是否已经有同类型的上下文（一个 canvas 只能有一个类型的上下文，不能同时 2D 和 WebGL）
2. 创建上下文对象，关联到 canvas 的像素缓冲区
3. 初始化默认状态：
   - `fillStyle = '#000000'`（黑色）
   - `strokeStyle = '#000000'`
   - `lineWidth = 1.0`
   - `font = '10px sans-serif'`
   - `textAlign = 'start'`
   - 变换矩阵 = 单位矩阵
   - `globalAlpha = 1.0`
   - `globalCompositeOperation = 'source-over'`
   - 裁剪区域 = 整个画布
4. 将上下文对象缓存到 canvas 实例上，后续 getContext 返回同一个对象

上下文对象持有 canvas 的像素缓冲区引用，所有绘制命令最终都写入这个缓冲区。

### 1.4.3 绘图命令队列与刷新机制

Canvas 2D Context 的绘图命令不是立即执行到像素缓冲区的——它们进入一个命令队列，在浏览器下一次重绘前批量执行。

```javascript
// 这些命令进入队列，不立即执行
ctx.fillStyle = 'red';
ctx.fillRect(0, 0, 100, 100);
ctx.fillStyle = 'blue';
ctx.fillRect(50, 50, 100, 100);

// 此时 canvas 的像素缓冲区可能还没有变化
// 浏览器会在下一帧统一执行队列中的命令

// getImageData 会强制刷新队列（同步执行所有待执行命令）
const imageData = ctx.getImageData(0, 0, 1, 1);
// 此时所有命令已执行完毕
```

这个机制有两个重要的性能影响：

1. `getImageData()` 和 `putImageData()` 会强制刷新命令队列，破坏批量优化。在动画循环中频繁调用它们是性能杀手。

2. 绘图命令本身是很快的（只是入队），真正的像素操作延迟到刷新时批量执行。所以"100 条绘图命令"不一定比"1 条绘图命令"慢多少——取决于最终需要操作多少像素。

```javascript
// 性能好的写法：批量命令，让浏览器优化
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < 1000; i++) {
    ctx.fillRect(x[i], y[i], 10, 10);
  }
  // 所有命令在下一帧批量执行
}

// 性能差的写法：每次循环都强制刷新
function drawSlow() {
  for (let i = 0; i < 1000; i++) {
    ctx.fillRect(x[i], y[i], 10, 10);
    const pixel = ctx.getImageData(x[i], y[i], 1, 1); // 强制刷新！
    // 处理 pixel...
  }
}
```

### 1.4.4 后缓冲区（Back Buffer）与页面合成

Canvas 的像素缓冲区在内部通常使用**双缓冲（Double Buffering）**机制：

```
┌─────────────────┐     ┌─────────────────┐
│  Front Buffer   │     │  Back Buffer    │
│  (当前显示)      │ ←── │  (绘图目标)      │
│  GPU 纹理        │     │  CPU/GPU 可写    │
└─────────────────┘     └─────────────────┘
                              ↑
                         ctx.fillRect() 等
                         绘图命令写入这里
```

你通过 ctx 命令绘制的内容写入后缓冲区。在浏览器合成阶段，后缓冲区的内容被提交为 GPU 纹理，合成器将它与其他合成层的纹理叠加，输出到屏幕。

对于 WebGL canvas，这个过程更直接——WebGL 直接渲染到 GPU 纹理，合成器直接使用该纹理。没有 CPU 到 GPU 的数据拷贝（在大多数实现中）。

对于 2D canvas，情况取决于浏览器实现：
- **软件渲染模式**：2D 上下文在 CPU 上执行绘图命令，结果在 CPU 内存中，合成时需要上传到 GPU
- **硬件加速模式**：2D 上下文使用 GPU 加速执行绘图命令，结果直接在 GPU 纹理中

```javascript
// 你无法直接控制 2D canvas 是否硬件加速
// 但可以通过合成层提升来间接影响
canvas.style.transform = 'translateZ(0)';
// 这通常会让浏览器为该 canvas 使用 GPU 加速的 2D 渲染
```

> 金句：Canvas 绘制的最后一公里是缓冲区到 GPU 纹理的传输——这段路程决定了 Canvas 更新的真实延迟。

**完整数据流总结**：

```
你的 JavaScript 代码
    │
    ▼
ctx.fillRect() ──→ 命令队列
    │
    ▼ (下一帧刷新)
2D 渲染引擎执行 ──→ 后缓冲区像素写入
    │
    ▼ (合成阶段)
缓冲区上传 GPU ──→ canvas 纹理
    │
    ▼
合成器叠加各层 ──→ 屏幕像素
```

每一步都有潜在的性能瓶颈：
- 命令队列过长 → CPU 开销
- 像素写入量大 → 内存带宽瓶颈
- 缓冲区上传 GPU → PCIe 带宽瓶颈（仅软件渲染模式）
- 合成器层太多 → GPU 纹理数量过多

理解这条数据流，你就理解了为什么 Canvas 性能优化要从这些环节入手。

## 1.5 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| 浏览器渲染管线 | DOM+CSSOM → 渲染树 → 布局 → 绘制 → 合成 |
| Canvas 在管线中的位置 | DOM 节点 + 独立像素缓冲区，合成阶段作为纹理参与叠加 |
| 合成层提升 | will-change/translateZ(0) 可隔离 canvas，避免连带重绘 |
| 图形 API 演进 | VML/Flash → Canvas 2D → WebGL → WebGPU |
| canvas.width vs CSS width | width/height 属性控制缓冲区分辨率，CSS 控制显示尺寸 |
| 命令队列机制 | 绘图命令批量执行，getImageData 会强制刷新破坏优化 |
| 双缓冲 | 绘图写入后缓冲区，合成时提交为 GPU 纹理 |

觉得有用？收藏起来，下次面试前翻出来看。

你有没有遇到过 canvas 性能问题却不知道瓶颈在哪？评论区说说你的场景，怕浪猫帮你定位。

关注怕浪猫，下期我们讲 **Canvas 核心原理：上下文、像素与状态机**——把 getContext('2d') 拆开看里面到底是个什么机器。

系列进度 1/17

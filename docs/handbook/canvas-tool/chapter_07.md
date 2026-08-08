# 第7章 图层系统

> 画了 5000 个图元的画布，每帧重绘卡成 PPT？因为你缺一个图层系统。

我是怕浪猫，在 Canvas 坑里摸爬滚打多年的前端工程狗。

之前做可视化编辑器，画布堆了上千图元。每次拖一个矩形，整个画布从头重绘，帧率掉到个位数。后来拆成多层画布引入图层管理和脏矩形重绘，帧率回到 60fps。这章把图层系统讲透。

## 7.1 为什么需要图层

### 7.1.1 单画布的痛点

Canvas 2D Context 是立即模式（Immediate Mode）API。调用 `fillRect` 时像素直接写入位图，画布不记住绘制历史。**任何区域更新都需要重绘整个画布**。

假设有静态背景（8ms）和动态准星（0.5ms）。单画布每次鼠标移动成本 8.5ms；分在不同画布只重绘准星层 0.5ms，**差 17 倍**。

```
单画布：总成本=所有图元绘制之和，只变一个也全画
多画布：总成本=变化图层绘制之和，静态层零成本
```

**金句：单画布把鸡蛋放一个篮子里，一次更新就是全量灾难。**

### 7.1.2 图层核心思想：分离绘制与合成

每个图层先独立绘制到离屏缓冲区（Offscreen Buffer），再由合成器（Compositor）按顺序叠加到输出画布。

```
图层分离绘制与合成
┌───────┐ ┌───────┐ ┌───────┐
│图层 A │ │图层 B │ │图层 C │
│独立绘制│ │独立绘制│ │独立绘制│
└──┬────┘ └──┬────┘ └──┬────┘
   └──┬───────┴───────┘
   ┌──▼──┐ ┌──────▼─┐
   │合成器│─│输出画布│
   │按z序 │ │(屏幕)  │
   └─────┘ └────────┘
```

四个优势：局部重绘；独立属性控制；层级管理；并行绘制。

### 7.1.3 图层在图形软件中的历史

**Photoshop** 1994 年 3.0 引入图层系统成行业标准。**Figma** 支持嵌套、布尔运算（Union/Subtract/Intersect），图层树本质是场景图（Scene Graph）。**Sketch** 用树形结构管理支持无限嵌套。共同特征：**绘制和合成分离**。

## 7.2 多画布图层架构

### 7.2.1 叠加多个 canvas 元素

把多个 `<canvas>` 叠加，设为 `position:absolute`，通过 `top:0;left:0` 对齐。`pointer-events:none` 是关键，通常只有交互层接收事件。

```
多画布叠加 DOM 结构
┌───────────────────────────┐
│ div.canvas-container      │
│ ┌───────────────────────┐ │
│ │ canvas#layer-bg   z:1 │ │ 背景层
│ ├───────────────────────┤ │
│ │ canvas#layer-content z:2│ │ 内容层
│ ├───────────────────────┤ │
│ │ canvas#layer-interact z:3│ 交互层
│ └───────────────────────┘ │
└───────────────────────────┘
```

### 7.2.2 静态层与动态层分离

核心价值在于**按变化频率分层**：

```
按变化频率分层
┌────────┬────────┬──────────────────────┐
│图层    │频率    │典型内容               │
├────────┼────────┼──────────────────────┤
│背景层  │几乎不变│网格、底图、水印       │
│内容层  │偶尔变化│业务图元、数据可视化   │
│标注层  │交互时变│文本标签、尺寸标注     │
│交互层  │每帧变化│选中框、拖拽预览、辅助线│
└────────┴────────┴──────────────────────┘
```

原则：**变化频率相近的图元放同层，频率差异大的必须分层**。按更新频率分而非视觉重要性。

### 7.2.3 z-index 管理

用**间隔分配**（10、20、30...），插入新图层时不需调其他图层。间隔不够时重分配（0,1,2,3...），只要不每帧做性能影响可忽略。

### 7.2.4 实战：三层架构完整代码

```javascript
// 三层画布架构完整代码
class LayerManager {
  constructor(container, w, h) {
    this.c = container; this.w = w; this.h = h;
    this.layers = new Map(); this.order = [];
  }
  createLayer(id, z) {
    const cv = document.createElement('canvas');
    cv.width = this.w; cv.height = this.h;
    cv.style.cssText = `position:absolute;top:0;left:0;z-index:${z}`;
    this.c.appendChild(cv);
    const l = { id, canvas: cv, ctx: cv.getContext('2d'),
      zIndex: z, visible: true };
    this.layers.set(id, l); this.order.push(id);
    this.order.sort((a, b) =>
      this.layers.get(a).zIndex - this.layers.get(b).zIndex);
    return l;
  }
  clearLayer(id) {
    const l = this.layers.get(id);
    if (l) l.ctx.clearRect(0, 0, this.w, this.h);
  }
  setVisible(id, v) {
    const l = this.layers.get(id);
    if (l) { l.visible = v; l.canvas.style.display = v?'block':'none'; }
  }
  resize(w, h) {
    this.w = w; this.h = h;
    for (const l of this.layers.values()) {
      l.canvas.width = w; l.canvas.height = h;
    }
  }
  destroy() {
    for (const l of this.layers.values()) l.canvas.remove();
    this.layers.clear(); this.order = [];
  }
}

// 使用示例
const c = document.getElementById('canvas-container');
const mgr = new LayerManager(c, 1200, 800);
const bg = mgr.createLayer('bg', 10);
const content = mgr.createLayer('content', 20);
const ui = mgr.createLayer('ui', 30);

// 背景层只画一次
function drawBg() {
  const ctx = bg.ctx;
  ctx.fillStyle = '#1a1a2e'; ctx.fillRect(0, 0, 1200, 800);
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  for (let x = 0; x <= 1200; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 800); ctx.stroke();
  }
  for (let y = 0; y <= 800; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1200, y); ctx.stroke();
  }
}

// 交互层鼠标移动时重绘
function drawUI(mx, my) {
  mgr.clearLayer('ui');
  const ctx = ui.ctx;
  ctx.strokeStyle = '#00d9ff';
  ctx.beginPath();
  ctx.moveTo(0, my); ctx.lineTo(1200, my);
  ctx.moveTo(mx, 0); ctx.lineTo(mx, 800);
  ctx.stroke();
}

drawBg();
c.addEventListener('mousemove', e => {
  const r = c.getBoundingClientRect();
  drawUI(e.clientX - r.left, e.clientY - r.top);
});
```

> 参考：[Canvas API - MDN](https://developer.mozilla.org/zh-CN/docs/Web/API/Canvas_API)

**金句：图层架构本质不是把画布变多，而是把不必要的重绘变少。**

## 7.3 离屏画布（OffscreenCanvas）

### 7.3.1 API 概述

OffscreenCanvas（[MDN](https://developer.mozilla.org/zh-CN/docs/Web/API/OffscreenCanvas)）允许 Canvas 绘制在 DOM 之外甚至 Web Worker 中进行。传统 2D Context 绑定主线程，绘制与 UI 共享线程，任务繁重时卡顿。OffscreenCanvas 打破此限制，API 与普通 2D Context 几乎一致。

### 7.3.2 主线程 vs Worker 线程

**模式一：主线程离屏绘制。** 创建 OffscreenCanvas 绘制后通过 `drawImage` 合成到可见 canvas。

**模式二：Worker 线程绘制。** 通过 `transferControlToOffscreen` 将 canvas 控制权转移到 Worker，所有绘制在 Worker 执行。

```
Worker 模式数据流
┌──────── 主线程 ────────┐
│ <canvas> ─transferControl
│     │                  │
│ postMessage ───────────┼─┐
│ onmessage ← 帧完成     │ │
└────────────────────────┘ │
                          │
┌──────── Worker ─────────┘
│ getContext('2d')
│ fillRect(...) ← 绘制在此
│ postMessage(done)
└─────────────────────────┘
```

### 7.3.3 transferControlToOffscreen 原理

调用后：canvas 缓冲区分离为 OffscreenCanvas，`getContext` 返回 null；对象被 Transferable 传递给 Worker；Worker 绘制通过浏览器合成器直接到屏幕，不经过主线程。**绘制和合成都绕开主线程**。操作不可逆。

### 7.3.4 Worker 绘制完整示例

```javascript
// 主线程
const canvas = document.getElementById('canvas');
const off = canvas.transferControlToOffscreen();
const worker = new Worker('render-worker.js');
worker.postMessage({ type: 'init', canvas: off }, [off]);
worker.onmessage = e => {
  if (e.data.type === 'done') console.log('帧完成');
};
worker.postMessage({ type: 'render', shapes: [
  { type: 'rect', x: 10, y: 10, w: 100, h: 100, fill: '#ff6b6b' },
  { type: 'circle', x: 400, y: 200, r: 60, fill: '#45b7d1' },
]});

// render-worker.js
let ctx, canvas;
self.onmessage = e => {
  const m = e.data;
  if (m.type === 'init') { canvas = m.canvas; ctx = canvas.getContext('2d'); }
  if (m.type === 'render') {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const s of m.shapes) {
      ctx.fillStyle = s.fill;
      if (s.type === 'rect') ctx.fillRect(s.x, s.y, s.w, s.h);
      else if (s.type === 'circle') {
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.28); ctx.fill();
      }
    }
    self.postMessage({ type: 'done' });
  }
};
```

> 参考：[OffscreenCanvas - MDN](https://developer.mozilla.org/zh-CN/docs/Web/API/OffscreenCanvas)

性能对比：5000 图元每帧 20ms。传统模式全占主线程 = 25ms/帧 = 40fps。Worker 模式 20ms 在 Worker 执行，主线程只需 5ms，并行后接近 60fps。

## 7.4 图层的数据模型

### 7.4.1 图层描述对象

```javascript
class LayerDescriptor {
  constructor(o = {}) {
    this.id = o.id || crypto.randomUUID();
    this.name = o.name || 'Layer';
    this.x = o.x ?? 0; this.y = o.y ?? 0;
    this.width = o.width ?? 0; this.height = o.height ?? 0;
    this.visible = o.visible ?? true;
    this.opacity = o.opacity ?? 1;
    this.blendMode = o.blendMode ?? 'source-over';
    this.zIndex = o.zIndex ?? 0;
    this.parentId = o.parentId ?? null;
    this.drawFn = o.drawFn ?? null;
  }
  hitTest(px, py) {
    return px >= this.x && px <= this.x + this.width
      && py >= this.y && py <= this.y + this.height;
  }
}
```

**bounds**：位置和大小，用于绘制区域和脏矩形计算。**opacity**：合成阶段控制整体透明度。**visible**：是否参与合成。**blendMode**：与下层混合方式，如 `multiply`（正片叠底）、`screen`（滤色）。

### 7.4.2 图层树的序列化

```
图层树结构
┌─ root
├── background
│   ├── grid
│   └── watermark
├── content
│   ├── group-a
│   │   ├── rect-1
│   │   └── rect-2
│   └── text-1
└── overlay
    ├── selection
    └── guides
```

```javascript
class LayerNode {
  constructor(d) { this.d = d; this.children = []; this.parent = null; }
  addChild(n) { n.parent = this; this.children.push(n); }
  traverse(cb) { cb(this); for (const c of this.children) c.traverse(cb); }
  collectVisible() {
    const r = [];
    this.traverse(n => { if (n.d.visible) r.push(n.d); });
    return r;
  }
}
function serialize(root) {
  return JSON.stringify(root, (k, v) =>
    (k === 'parent' || k === 'drawFn') ? undefined : v, 2);
}
function deserialize(json) {
  function rebuild(d) {
    const n = new LayerNode(d.d);
    for (const c of (d.children || [])) n.addChild(rebuild(c));
    return n;
  }
  return rebuild(JSON.parse(json));
}
```

序列化注意：`parent` 造成循环引用需排除；`drawFn` 无法序列化，用函数名标记后查表恢复。

### 7.4.3 脏矩形重绘优化

脏矩形核心思想：**每帧只重绘变化区域**。

```
脏矩形重绘原理
┌────────────────────────┐
│ 画布 (1200x800)        │
│   ┌──────┐             │
│   │脏矩形A│ ← 只有这块变│
│   └──────┘             │
│        ┌──────┐        │
│        │脏矩形B│        │
│        └──────┘        │
│ 重绘 = A ∪ B           │
└────────────────────────┘
```

算法步骤：

```
1. 维护 dirtyRects = []
2. 图元变化时：计算包围盒加入 dirtyRects
3. 帧绘制时：合并重叠矩形 → 逐个脏矩形重绘 → 清空
4. 单个脏矩形：save() → clip(矩形) → clearRect
   → 遍历可见图层重绘相交图元 → restore()
```

```javascript
class DirtyRectRenderer {
  constructor(canvas) {
    this.ctx = canvas.getContext('2d');
    this.dirty = []; this.layers = [];
  }
  markDirty(x, y, w, h) { this.dirty.push({x, y, width: w, height: h}); }
  flush() {
    if (!this.dirty.length) return;
    for (const r of this.dirty) {
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(r.x, r.y, r.width, r.height);
      this.ctx.clip();
      this.ctx.clearRect(r.x, r.y, r.width, r.height);
      for (const l of this.layers)
        if (l.visible && l.drawFn) l.drawFn(this.ctx, r);
      this.ctx.restore();
    }
    this.dirty = [];
  }
  addLayer(l) { this.layers.push(l); }
}
```

脏矩形只对"局部变化"有效。整画布变化时退化为全量重绘。

**金句：脏矩形不是万能药。全量变化请用 OffscreenCanvas 跑到 Worker 里。**

## 7.5 图层与合成的关系

### 7.5.1 逐层绘制到离屏缓冲再合成

单画布场景需手动实现合成：为每个图层创建离屏画布，各图层独立绘制，合成函数按 z-index 用 `drawImage` 叠加。

```javascript
class Compositor {
  constructor(out, w, h) {
    this.out = out.getContext('2d');
    this.w = w; this.h = h; this.layers = [];
  }
  addLayer(l) {
    l.off = new OffscreenCanvas(this.w, this.h);
    l.ctx = l.off.getContext('2d');
    this.layers.push(l);
    this.layers.sort((a, b) => a.zIndex - b.zIndex);
  }
  composite() {
    this.out.clearRect(0, 0, this.w, this.h);
    for (const l of this.layers) {
      if (!l.visible) continue;
      this.out.globalAlpha = l.opacity;
      this.out.globalCompositeOperation = l.blendMode;
      this.out.drawImage(l.off, 0, 0);
    }
    this.out.globalAlpha = 1;
    this.out.globalCompositeOperation = 'source-over';
  }
}
```

### 7.5.2 混合模式在图层间应用

`globalCompositeOperation` 定义新内容如何与已有内容混合：

```
常用混合模式
┌─────────────────┬──────────────────────────┐
│模式             │效果                      │
├─────────────────┼──────────────────────────┤
│source-over      │默认，上层覆盖下层         │
│multiply         │正片叠底，结果更暗         │
│screen           │滤色，结果更亮             │
│overlay          │叠加，暗处更暗亮处更亮     │
│darken           │取暗，保留较暗像素         │
│lighten          │取亮，保留较亮像素         │
│destination-out  │擦除，用上层形状擦除下层   │
│destination-in   │交集，只保留重叠部分       │
└─────────────────┴──────────────────────────┘
```

> 参考：[globalCompositeOperation - MDN](https://developer.mozilla.org/zh-CN/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation)

逐层合成时每画一层前设混合模式，画完重置为 `source-over`。

### 7.5.3 蒙版与剪裁路径

蒙版（Mask）用图层形状控制另一图层可见区域。蒙版与剪裁路径（Clipping Path）本质相同，区别是作用范围：剪裁路径作用于单次绘制，蒙版作用于整个图层。

```
蒙版合成原理
┌────────┐  ┌────────┐  ┌────────┐
│内容图层│◀─│蒙版图层│─▶│合成结果│
│(彩色) │  │白=可见│  │(蒙版内 │
│       │  │黑=不可│  │的内容)│
└────────┘  └────────┘  └────────┘
```

三种实现：

**方式一：`destination-in`**——先画内容再切换 `destination-in` 画蒙版，只保留重叠部分。

```javascript
function applyMask(ctx, maskFn) {
  ctx.globalCompositeOperation = 'destination-in';
  maskFn(ctx);
  ctx.globalCompositeOperation = 'source-over';
}
```

**方式二：`clip` 剪裁路径**——绘制前用路径剪裁。

```javascript
function drawWithClip(ctx, clipFn, drawFn) {
  ctx.save(); ctx.beginPath(); clipFn(ctx); ctx.clip();
  drawFn(ctx); ctx.restore();
}
```

**方式三：`destination-out` 反向蒙版（挖洞）**——先画内容再切换 `destination-out` 画孔形状，被覆盖像素变透明。

蒙版性能取决于形状复杂度。简单矩形零成本，上千控制点贝塞尔路径不可忽视。实践中尽量简化蒙版形状，或预渲染为位图。

## 本章总结

图层系统是 Canvas 工程化从"能跑"到"好用"的关键一跃。从单画布痛点出发，通过多画布叠加实现静态层与动态层分离，引入 OffscreenCanvas 将绘制搬到 Worker，设计图层描述对象和图层树，通过脏矩形算法压缩重绘面积，最后在合成阶段应用混合模式和蒙版。

```
图层系统核心架构
┌──────────────────────────────────────┐
│ LayerManager (图层管理器)            │
│ ├── Layer Tree (图层树)              │
│ ├── DirtyRectRenderer (脏矩形重绘器) │
│ └── Compositor (合成器)              │
│     ├── OffscreenCanvas (离屏缓冲)   │
│     ├── BlendMode (混合模式)         │
│     └── Mask (蒙版)                  │
├──────────────────────────────────────┤
│ 渲染线程模型                          │
│ ├── 主线程：事件处理 + 合成调度       │
│ └── Worker：OffscreenCanvas 绘制     │
└──────────────────────────────────────┘
```

**收藏价值清单：** 三层画布架构完整代码（7.2.4）；脏矩形重绘算法步骤加代码（7.4.3）；OffscreenCanvas + Worker 完整示例（7.3.4）。三份模板覆盖 80% 工程需求，建议先收藏再细读。

> Canvas 工程全书 · 进度 7/17
>
> 下一章预告：第8章「Canvas 动画系统」——从 `requestAnimationFrame` 到缓动函数数学原理，从帧率监控到动画引擎设计，让你的 Canvas 动起来。

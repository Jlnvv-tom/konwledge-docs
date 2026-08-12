---
sidebar_position: 3
---

# 第3章 Canvas 与 SVG：位图与矢量的两条道路

90% 的前端在做图形技术选型时都选错过。

不是选了 Canvas 结果发现交互需求太重，就是选了 SVG 结果 5000 个节点页面卡死。选错技术栈的代价是项目后期重构——把整个渲染层换掉。

我是怕浪猫，这一章帮你彻底搞清楚 Canvas 和 SVG 的关系。不是简单的"Canvas 性能好、SVG 交互好"，而是从渲染范式、数据结构、性能模型、场景决策四个维度做深度对比。

## 3.1 渲染范式对比

### 3.1.1 Canvas：即时模式（Immediate Mode）绘制

Canvas 使用**即时模式（Immediate Mode）**渲染。在这种模式下，你发出绘制命令，渲染器立即执行，结果直接写入像素缓冲区。执行完后，图元信息就丢失了——只剩像素。

```javascript
ctx.fillStyle = 'red';
ctx.fillRect(10, 10, 100, 100);  // 画一个红色矩形

// 此时画布上有一个红色矩形
// 但 canvas 内部不记录"这里有一个矩形"这个信息
// 它只知道 (10,10) 到 (110,110) 区域的像素颜色变成了红色

ctx.canvas.width = ctx.canvas.width;  // 清空画布的 hack
// 矩形消失了，没有任何"对象"可以恢复它
```

即时模式的核心特征：**无状态**。每一帧都是全新的绘制，渲染器不维护图元列表。你想改变某个图元的位置？没有"移动"这个操作——只能清空画布，用新位置重新绘制所有内容。

### 3.1.2 SVG：保留模式（Retained Mode）绘制

SVG（Scalable Vector Graphics，可缩放矢量图形）使用**保留模式（Retained Mode）**渲染。你描述图元，渲染器维护一个场景图（Scene Graph），每帧根据场景图渲染。

```html
<svg width="200" height="200">
  <rect x="10" y="10" width="100" height="100" fill="red" id="myRect" />
</svg>
```

```javascript
// SVG 图元是 DOM 节点，可以随时操作
const rect = document.getElementById('myRect');
rect.setAttribute('x', '50');  // 移动矩形
rect.setAttribute('fill', 'blue');  // 改颜色
// 浏览器自动重新渲染，不需要手动清空重绘
```

保留模式的核心特征：**有状态**。渲染器维护图元列表，你通过修改图元属性来更新画面，渲染器负责计算差异并重绘。

> 金句：Canvas 是"画完即忘"的画家，SVG 是"记得所有图层"的档案管理员。

### 3.1.3 即时模式 vs 保留模式的工程权衡

两种模式的本质差异：

| 维度 | 即时模式（Canvas） | 保留模式（SVG） |
|------|------------------|----------------|
| 图元存储 | 不存储 | 存储为 DOM 节点 |
| 重绘方式 | 手动清空 + 全量重绘 | 浏览器自动增量重绘 |
| 交互实现 | 自行实现命中检测 | 原生 DOM 事件 |
| 内存占用 | 固定（像素缓冲区大小） | 随图元数量线性增长 |
| 状态管理 | 开发者负责 | 浏览器负责 |
| 声明式能力 | 无（命令式 API） | 有（HTML 标签声明） |

即时模式的优势在于**绘制性能**——没有场景图维护开销，没有 DOM 节点内存，绘图命令直接到像素。

保留模式的优势在于**开发效率**——不需要手动管理重绘，交互天然支持，声明式语法更易维护。

> 金句：选 Canvas 还是 SVG，本质是在选"谁来管理图元状态"——你自己管（Canvas），还是浏览器帮你管（SVG）。

## 3.2 数据结构差异

### 3.2.1 Canvas 的像素缓冲区 vs SVG 的 DOM 节点树

Canvas 内部只有一块线性的像素缓冲区：

```
Canvas 内存模型：
┌──────────────────────────────────┐
│  像素缓冲区 (width × height × 4) │
│  [R][G][B][A][R][G][B][A]...    │
│  无图元信息，纯像素数据           │
└──────────────────────────────────┘
```

不管你画了 1 个矩形还是 10000 个矩形，Canvas 的内存占用都是 `width × height × 4` 字节。图元数量不影响内存。

SVG 内部是一棵 DOM 节点树：

```
SVG 内存模型：
<svg>
├── <rect>        → DOM 节点 + 属性 + 样式
├── <circle>      → DOM 节点 + 属性 + 样式
├── <path>        → DOM 节点 + 属性 + 样式
├── <text>        → DOM 节点 + 属性 + 样式
└── ...           → 每个图元一个 DOM 节点
```

每个 SVG 图元是一个完整的 DOM 节点，包含属性、样式、事件监听器等。10000 个 SVG 图元意味着 10000 个 DOM 节点，内存随图元数量线性增长。

**内存对比示例**（800x600 画布）：

| 图元数量 | Canvas 内存 | SVG 内存（估算） |
|---------|------------|----------------|
| 10 | 1.83 MB | ~10 KB |
| 100 | 1.83 MB | ~100 KB |
| 1000 | 1.83 MB | ~1 MB |
| 10000 | 1.83 MB | ~10 MB |
| 100000 | 1.83 MB | ~100 MB（页面卡死） |

Canvas 内存恒定，SVG 内存线性增长。图元越多，Canvas 的优势越大。

### 3.2.2 事件系统的本质区别：无 vs 原生 DOM 事件

这是 Canvas 和 SVG 在交互层面最根本的差异。

**SVG 天然支持 DOM 事件**：

```javascript
const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
rect.addEventListener('click', (e) => {
  console.log('点击了矩形', e.target);
});
rect.addEventListener('mouseenter', () => {
  rect.setAttribute('fill', 'blue');
});
```

每个 SVG 图元都可以独立绑定事件。浏览器知道"鼠标在这个矩形上"，因为矩形是一个 DOM 节点，有明确的位置和边界。

**Canvas 没有事件系统**：

```javascript
// Canvas 上画了 100 个矩形
for (let i = 0; i < 100; i++) {
  ctx.fillRect(rects[i].x, rects[i].y, rects[i].w, rects[i].h);
}

// 点击事件只能绑定在 canvas 元素上
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  // 必须自己实现命中检测
  for (let i = rects.length - 1; i >= 0; i--) {
    if (x >= rects[i].x && x <= rects[i].x + rects[i].w &&
        y >= rects[i].y && y <= rects[i].y + rects[i].h) {
      console.log('点击了第', i, '个矩形');
      break;
    }
  }
});
```

> 金句：SVG 的事件是免费的，Canvas 的事件是自建的——你要么自己写命中检测，要么用 Konva.js 这类框架帮你写。

### 3.2.3 可访问性（a11y）：Canvas 的盲区与 SVG 的天然优势

a11y（Accessibility，可访问性）是指网页内容对残障用户的可访问程度，主要涉及屏幕阅读器支持。

**SVG 天然可访问**：

```html
<svg role="img" aria-labelledby="chartTitle chartDesc">
  <title id="chartTitle">2024年季度销售额</title>
  <desc id="chartDesc">柱状图显示四个季度的销售额，Q1最高</desc>
  <rect x="10" y="10" width="50" height="100" fill="blue" />
  <text x="35" y="130">Q1</text>
</svg>
```

屏幕阅读器可以读取 SVG 的 title 和 desc，用户可以理解图表内容。每个图元也可以有独立的 ARIA 属性。

**Canvas 默认不可访问**：

```html
<!-- 屏幕阅读器只会读出"canvas"或什么都不读 -->
<canvas id="chart"></canvas>
```

Canvas 的内容是像素，屏幕阅读器无法识别。要实现可访问性，需要额外的 fallback 内容：

```html
<canvas id="chart" role="img" aria-label="2024年季度销售额柱状图，Q1最高">
  <!-- fallback：屏幕阅读器可读的内容 -->
  <table>
    <tr><th>季度</th><th>销售额</th></tr>
    <tr><td>Q1</td><td>100万</td></tr>
    <tr><td>Q2</td><td>80万</td></tr>
  </table>
</canvas>
```

## 3.3 性能特征对比

### 3.3.1 元素数量与性能曲线：Canvas 的 O(1) vs SVG 的 O(n)

这是最关键的性能差异。

**Canvas 性能与图元数量基本无关**（O(1)）：

```javascript
// 画 10 个矩形 vs 10000 个矩形
// 每帧的绘制时间差别不大（在合理范围内）
// 因为最终都是写像素缓冲区
function draw(rects) {
  ctx.clearRect(0, 0, width, height);
  for (const r of rects) {
    ctx.fillRect(r.x, r.y, r.w, r.h);
  }
}
// 10 个矩形：~0.1ms
// 10000 个矩形：~5ms（仍然在 16ms 帧预算内）
// 100000 个矩形：~50ms（开始掉帧，但瓶颈在 JS 循环而非渲染）
```

**SVG 性能随图元数量线性下降**（O(n)）：

```javascript
// 创建 10000 个 SVG 矩形
const svg = document.querySelector('svg');
for (let i = 0; i < 10000; i++) {
  const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  rect.setAttribute('x', Math.random() * 800);
  rect.setAttribute('y', Math.random() * 600);
  rect.setAttribute('width', 10);
  rect.setAttribute('height', 10);
  svg.appendChild(rect);
}
// 10 个矩形：无感
// 1000 个矩形：开始卡顿
// 10000 个矩形：页面几乎冻结（DOM 操作 + 布局计算爆炸）
```

**性能交叉点**：图元数量在多少时，Canvas 开始比 SVG 快？

| 图元数量 | Canvas（fps） | SVG（fps） | 建议 |
|---------|-------------|-----------|------|
| < 100 | 60 | 60 | 都可以 |
| 100-500 | 60 | 55 | 都可以，SVG 交互更方便 |
| 500-2000 | 60 | 30-45 | 看情况，交互多选 SVG，重绘制选 Canvas |
| 2000-5000 | 55-60 | 15-25 | Canvas |
| > 5000 | 50-60 | < 10 | Canvas 必选 |

> 金句：图元 500 是分水岭——以下 SVG 省心，以上 Canvas 保命。

### 3.3.2 动画策略：requestAnimationFrame + 重绘 vs CSS/DOM 动画

Canvas 动画和 SVG 动画的实现方式完全不同。

**Canvas 动画**：必须手动驱动每一帧。

```javascript
function animate() {
  ctx.clearRect(0, 0, width, height);
  
  for (const ball of balls) {
    ball.x += ball.vx;
    ball.y += ball.vy;
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, ball.r, 0, Math.PI * 2);
    ctx.fill();
  }
  
  requestAnimationFrame(animate);
}
animate();
```

每帧都要清空画布 + 重绘所有内容。好处是你可以精确控制每一帧的绘制内容。坏处是即使只有一个图元在动，也要重绘整个画布。

**SVG 动画**：可以用 CSS 动画或 SMIL，浏览器自动处理重绘。

```css
@keyframes move {
  to { transform: translateX(300px); }
}
rect {
  animation: move 2s ease-in-out infinite;
}
```

浏览器知道只有这个 rect 在变，只需要重绘这个节点的区域，不影响其他节点。这是保留模式的优势——浏览器可以做**增量重绘**。

| 动画场景 | Canvas | SVG | 建议 |
|---------|--------|-----|------|
| 少量元素简单动画 | 手动 rAF 循环 | CSS 动画 | SVG 更省心 |
| 大量元素同步动画 | 一次 rAF 重绘全部 | 10000 个 CSS 动画 | Canvas |
| 物理模拟（粒子系统） | 高性能 | 不适合 | Canvas |
| 路径变形动画 | 手动插值 | animateMotion / CSS | SVG 更方便 |
| 60fps 持续动画 | 稳定 | 依赖浏览器优化 | Canvas 更可控 |

### 3.3.3 内存占用模型对比

| 维度 | Canvas | SVG |
|------|--------|-----|
| 基础内存 | width × height × 4 字节 | SVG 根节点开销 |
| 每增加一个图元 | 0 额外内存 | ~500-2000 字节（DOM 节点） |
| 事件监听器 | 绑定在 canvas 上（1 个） | 每个图元可独立绑定 |
| 内存释放 | 修改 width/height 立即释放 | 移除 DOM 节点后 GC |
| 内存泄漏风险 | 低（缓冲区固定大小） | 高（忘记移除 DOM 节点或事件监听器） |

### 3.3.4 渲染瓶颈定位：CPU 绘制 vs DOM reflow/repaint

Canvas 的性能瓶颈通常在 CPU 绘制（或 GPU 上传）：

```
Canvas 瓶颈定位流程：
1. JS 执行时间过长？ → 减少 per-frame 计算量
2. ctx 命令过多？ → 批量绘制，减少状态切换
3. 像素操作过重？ → 避免频繁 getImageData/putImageData
4. GPU 上传瓶颈？ → 减少画布尺寸或使用 OffscreenCanvas
```

SVG 的性能瓶颈通常在 DOM 操作：

```
SVG 瓶颈定位流程：
1. DOM 节点过多？ → 虚拟化（只渲染可见区域）
2. reflow 频繁？ → 批量修改属性，避免逐个操作
3. repaint 范围大？ → 使用 will-change 提升合成层
4. 事件监听器过多？ → 事件委托
```

> 金句：Canvas 的性能瓶颈在"画得快不快"，SVG 的性能瓶颈在"节点管得好不好"。

## 3.4 适用场景决策矩阵

### 3.4.1 何时选 Canvas：高频重绘、海量图元、像素级控制

Canvas 的核心优势场景：

| 场景 | 为什么选 Canvas | 典型应用 |
|------|----------------|---------|
| 游戏/物理模拟 | 每帧全量重绘，60fps | 2D 游戏、粒子系统 |
| 大规模数据可视化 | 图元数量 > 1000 | 散点图、热力图、轨迹图 |
| 图像处理 | 需要像素级操作 | 滤镜、裁剪、水印 |
| 视频处理 | 逐帧分析 | 视频滤镜、人脸标注 |
| 实时绘制 | 高频更新 | 白板、绘图工具 |
| 生成式艺术 | 大量随机图元 | 粒子艺术、分形图 |

### 3.4.2 何时选 SVG：交互密集、可访问性要求、可缩放

SVG 的核心优势场景：

| 场景 | 为什么选 SVG | 典型应用 |
|------|-------------|---------|
| 交互式图表 | 每个图元需要独立事件 | 柱状图、饼图、流程图 |
| 图标系统 | 矢量缩放、CSS 样式控制 | UI 图标、logo |
| 可访问性要求高 | 屏幕阅读器可读 | 政府网站、教育平台 |
| 响应式设计 | 无损缩放 | 多设备适配的图形 |
| 复杂路径动画 | animateMotion | 路径绘制动画 |
| 文档内嵌 | HTML 直接写 SVG | 文章配图、示意图 |

### 3.4.3 混合方案：SVG 做交互层 + Canvas 做绘制层

很多场景下，最优解是混合使用：

```html
<div style="position: relative;">
  <!-- Canvas 做底层绘制（大量图元） -->
  <canvas id="renderLayer" 
          style="position: absolute; top: 0; left: 0; z-index: 1;">
  </canvas>
  
  <!-- SVG 做上层交互（少量交互元素） -->
  <svg id="interactionLayer" 
       style="position: absolute; top: 0; left: 0; z-index: 2; pointer-events: none;">
    <!-- 只放需要交互的元素，设置 pointer-events: auto -->
    <rect class="tooltip" style="pointer-events: auto;" />
  </svg>
</div>
```

```javascript
// Canvas 负责高性能绘制
const canvas = document.getElementById('renderLayer');
const ctx = canvas.getContext('2d');
// 画 10000 个数据点
dataPoints.forEach(d => ctx.fillRect(d.x, d.y, 2, 2));

// SVG 负责交互元素
const svg = document.getElementById('interactionLayer');
// 只创建少量交互元素（如 tooltip、选中框）
const tooltip = createSvgElement('rect');
tooltip.addEventListener('mouseenter', showTooltip);
tooltip.addEventListener('mouseleave', hideTooltip);
```

**混合方案的架构图**：

```
┌─────────────────────────────────────┐
│  SVG 交互层 (z-index: 2)            │
│  - tooltip                          │
│  - 选中框                            │
│  - 拖拽手柄                          │
│  pointer-events: none (默认)        │
│  交互元素: pointer-events: auto      │
├─────────────────────────────────────┤
│  Canvas 绘制层 (z-index: 1)         │
│  - 数据点 (10000+)                  │
│  - 连线                              │
│  - 背景网格                          │
│  所有像素操作                        │
├─────────────────────────────────────┤
│  DOM 容器 (position: relative)      │
└─────────────────────────────────────┘
```

> 金句：混合方案不是妥协，而是架构——Canvas 负责性能，SVG 负责交互，各司其职。

## 3.5 深入对比：同一个需求的两种实现

为了更直观地展示 Canvas 和 SVG 的差异，我们用同一个需求——一个可交互的柱状图——分别用两种技术实现，对比代码量和性能。

**Canvas 实现柱状图**：

```javascript
const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
const data = [
  { label: 'Q1', value: 100 },
  { label: 'Q2', value: 80 },
  { label: 'Q3', value: 120 },
  { label: 'Q4', value: 90 }
];

// 存储柱子位置用于命中检测
const bars = [];

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  bars.length = 0;
  
  const barWidth = 80;
  const gap = 40;
  const startX = 50;
  const maxHeight = 200;
  const maxValue = Math.max(...data.map(d => d.value));
  
  data.forEach((d, i) => {
    const x = startX + i * (barWidth + gap);
    const h = (d.value / maxValue) * maxHeight;
    const y = canvas.height - 50 - h;
    
    ctx.fillStyle = hoveredBar === i ? '#2196F3' : '#4CAF50';
    ctx.fillRect(x, y, barWidth, h);
    
    ctx.fillStyle = '#333';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(d.label, x + barWidth / 2, canvas.height - 20);
    ctx.fillText(d.value, x + barWidth / 2, y - 10);
    
    // 存储位置用于命中检测
    bars.push({ x, y, w: barWidth, h, index: i });
  });
}

// 命中检测
let hoveredBar = -1;
canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  let found = -1;
  for (const bar of bars) {
    if (x >= bar.x && x <= bar.x + bar.w &&
        y >= bar.y && y <= bar.y + bar.h) {
      found = bar.index;
      break;
    }
  }
  
  if (found !== hoveredBar) {
    hoveredBar = found;
    draw();  // 重绘
    canvas.style.cursor = found >= 0 ? 'pointer' : 'default';
  }
});

draw();
```

**SVG 实现柱状图**：

```javascript
const svg = document.getElementById('chart');
const data = [
  { label: 'Q1', value: 100 },
  { label: 'Q2', value: 80 },
  { label: 'Q3', value: 120 },
  { label: 'Q4', value: 90 }
];

const barWidth = 80;
const gap = 40;
const startX = 50;
const maxHeight = 200;
const maxValue = Math.max(...data.map(d => d.value));

data.forEach((d, i) => {
  const x = startX + i * (barWidth + gap);
  const h = (d.value / maxValue) * maxHeight;
  const y = 400 - 50 - h;
  
  // 创建柱子
  const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  rect.setAttribute('x', x);
  rect.setAttribute('y', y);
  rect.setAttribute('width', barWidth);
  rect.setAttribute('height', h);
  rect.setAttribute('fill', '#4CAF50');
  
  // 原生事件，不需要命中检测
  rect.addEventListener('mouseenter', () => {
    rect.setAttribute('fill', '#2196F3');
  });
  rect.addEventListener('mouseleave', () => {
    rect.setAttribute('fill', '#4CAF50');
  });
  
  svg.appendChild(rect);
  
  // 创建标签
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('x', x + barWidth / 2);
  text.setAttribute('y', 400 - 20);
  text.setAttribute('text-anchor', 'middle');
  text.textContent = d.label;
  svg.appendChild(text);
});
```

**对比分析**：

| 维度 | Canvas 版本 | SVG 版本 |
|------|------------|----------|
| 代码行数 | ~50 行 | ~30 行 |
| 命中检测 | 手动实现（10 行） | 浏览器免费提供 |
| 悬停效果 | 需要重绘整个画布 | 浏览器自动局部重绘 |
| 添加点击事件 | 再加 10 行命中检测 | addEventListener 一行 |
| 数据更新 | 重绘整个画布 | 修改对应 DOM 属性 |
| 4 个柱子性能 | 无差异 | 无差异 |
| 4000 个柱子性能 | 60fps | 5fps |

> 金句：4 个柱子，SVG 代码少一半；4000 个柱子，Canvas 性能快十倍——量变引起质变。

## 3.6 从 SVG 迁移到 Canvas（或反向）的工程经验

**SVG → Canvas 迁移的常见原因**：图元数量增长导致性能下降。

迁移要点：
1. 建立图元数据模型（Canvas 不存图元，你的 JS 需要自己存）
2. 实现命中检测系统（替代 DOM 事件）
3. 实现重绘循环（替代浏览器自动重绘）
4. 处理可访问性 fallback

**Canvas → SVG 迁移的常见原因**：交互需求增加，命中检测维护成本太高。

迁移要点：
1. 将 Canvas 上的图元数据转为 SVG DOM 节点
2. 移除自定义命中检测代码
3. 利用 SVG 的 CSS 动画替代手动 rAF 循环
4. 评估图元数量是否在 SVG 可承受范围内

**迁移决策清单**：

| 检查项 | 选 Canvas | 选 SVG |
|--------|----------|--------|
| 图元数量 > 2000 | ✓ | |
| 需要像素级操作 | ✓ | |
| 60fps 持续动画 | ✓ | |
| 图元数量 < 500 | | ✓ |
| 每个图元需独立事件 | | ✓ |
| 需要可访问性 | | ✓ |
| 需要无损缩放 | | ✓ |
| 混合方案可行 | Canvas 底层 | SVG 交互层 |

## 3.6 本章总结

| 对比维度 | Canvas | SVG |
|---------|--------|-----|
| 渲染范式 | 即时模式 | 保留模式 |
| 数据结构 | 像素缓冲区 | DOM 节点树 |
| 内存模型 | O(1) 固定 | O(n) 线性增长 |
| 事件系统 | 需自建 | 原生 DOM 事件 |
| 可访问性 | 需 fallback | 天然支持 |
| 性能拐点 | ~5000 图元 | ~500 图元 |
| 动画方式 | rAF 手动驱动 | CSS/SMIL 自动 |
| 缩放质量 | 位图缩放模糊 | 矢量缩放清晰 |
| 适用场景 | 高频重绘/海量图元 | 交互密集/可访问性 |

觉得有用？收藏起来，下次技术选型时直接查表。

你在项目中选 Canvas 还是 SVG 踩过坑？评论区说说你的经历，怕浪猫帮你分析。

关注怕浪猫，下期我们讲 **画布系统总论**——坐标系、生命周期和持久化的完整体系。

系列进度 3/17

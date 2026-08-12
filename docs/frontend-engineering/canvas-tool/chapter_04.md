---
sidebar_position: 4
---

# 第4章 画布系统总论：坐标系、生命周期与持久化

画布尺寸一变，内容全没了？

这是 Canvas 开发中最常见的问题之一。原因很简单——修改 `canvas.width` 或 `canvas.height` 会重置整个像素缓冲区。但很多人不知道的是，这个问题背后隐藏着更深层的概念：画布系统的坐标系、生命周期管理和持久化策略。

我是怕浪猫，这一章我们来系统地讲讲画布系统。不是简单的"怎么用 Canvas API"，而是从工程架构的角度理解"画布系统"这个概念。

## 4.1 什么是"画布系统"

### 4.1.1 狭义画布：单个 `<canvas>` 元素

最狭义的理解，画布就是一个 `<canvas>` DOM 元素加上它的 2D 上下文：

```javascript
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
ctx.fillRect(0, 0, 100, 100);
```

这个理解在小型项目中够用，但当项目复杂度上升——多个画布协同、尺寸动态变化、内容需要持久化——就需要更高层面的抽象。

### 4.1.2 广义画布：多画布协同的渲染架构

在真实的工程项目中，"画布系统"通常指一个由多个画布、数据模型、渲染管线和交互系统组成的完整架构。

```
画布系统架构：
┌──────────────────────────────────────────┐
│              画布系统 (Canvas System)       │
├──────────────────────────────────────────┤
│  数据层                                    │
│  ├── 图元数据模型（Shape/Path/Sprite）     │
│  ├── 图层数据模型（Layer）                 │
│  └── 场景图（Scene Graph）                 │
├──────────────────────────────────────────┤
│  渲染层                                    │
│  ├── 渲染管线（Render Pipeline）           │
│  ├── 脏矩形系统（Dirty Rectangle）         │
│  └── 合成器（Compositor）                  │
├──────────────────────────────────────────┤
│  画布层                                    │
│  ├── 背景画布（静态层）                     │
│  ├── 内容画布（动态层）                     │
│  └── 交互画布（Overlay 层）                 │
├──────────────────────────────────────────┤
│  交互层                                    │
│  ├── 命中检测（Hit Testing）               │
│  ├── 事件分发（Event Dispatch）            │
│  └── 手势识别（Gesture Recognition）       │
└──────────────────────────────────────────┘
```

> 金句：单个 canvas 是画板，多 canvas 协同才是画布系统——就像单个函数是代码，函数组合才是架构。

### 4.1.3 画布系统在可视化/编辑器/游戏中的角色定位

不同类型的项目对画布系统的需求不同：

| 项目类型 | 画布系统角色 | 核心需求 | 典型框架 |
|---------|------------|---------|---------|
| 数据可视化 | 渲染引擎 | 高性能批量绘制 | ECharts/G2 |
| 图形编辑器 | 核心运行时 | 图层管理 + 交互 | Konva/Fabric.js |
| 2D 游戏 | 游戏世界容器 | 60fps + 碰撞检测 | Phaser/PixiJS |
| 白板/绘图工具 | 绘图表面 | 低延迟 + 手势 | 自研 |
| 图片编辑器 | 图像处理管线 | 像素操作 + 滤镜 | 自研 |
| 地图引擎 | 瓦片渲染器 | 缩放/平移 + 瓦片管理 | Mapbox GL/Leaflet |

## 4.2 画布坐标系

坐标系是画布系统的基础。理解坐标系，才能正确地定位图元、处理交互、实现变换。

### 4.2.1 屏幕坐标系（左上原点，Y 向下）

Canvas 2D 上下文使用**屏幕坐标系**（也叫客户端坐标系）：原点在左上角，X 轴向右递增，Y 轴向下递增。

```
(0,0) ──────── X+ ────────►
  │
  │
  │
  Y+
  │
  ▼
```

这和数学课上的笛卡尔坐标系（Y 向上）是反的。这个差异会导致很多计算公式需要取反：

```javascript
// 数学坐标系：抛物线 y = -x²
// Canvas 坐标系：需要翻转 Y 轴
ctx.beginPath();
for (let x = -100; x <= 100; x++) {
  const y = -x * x / 100;  // 数学公式
  ctx.lineTo(centerX + x, centerY - y);  // Canvas 坐标需要减 y
}
ctx.stroke();
```

> 金句：Canvas 的 Y 轴向下，是所有图形计算"符号取反"的根源——忘了这一点，你的抛物线就是倒着的。

### 4.2.2 笛卡尔坐标系的转换

在数据可视化等场景中，通常使用数学坐标系（Y 向上）。需要做坐标系转换：

```javascript
class CartesianCanvas {
  constructor(ctx, width, height) {
    this.ctx = ctx;
    this.width = width;
    this.height = height;
  }
  
  // 将数学坐标转为 Canvas 坐标
  toCanvas(x, y) {
    return {
      x: x,
      y: this.height - y  // Y 轴翻转
    };
  }
  
  // 在数学坐标系下绘制点
  point(x, y) {
    const p = this.toCanvas(x, y);
    this.ctx.fillRect(p.x - 1, p.y - 1, 2, 2);
  }
  
  // 在数学坐标系下绘制线段
  line(x1, y1, x2, y2) {
    const p1 = this.toCanvas(x1, y1);
    const p2 = this.toCanvas(x2, y2);
    this.ctx.beginPath();
    this.ctx.moveTo(p1.x, p1.y);
    this.ctx.lineTo(p2.x, p2.y);
    this.ctx.stroke();
  }
}
```

另一种方式是用 `scale(1, -1)` 翻转 Y 轴，但这种方式会导致文本倒置，需要额外处理：

```javascript
ctx.save();
ctx.translate(0, canvas.height);  // 移动原点到底部
ctx.scale(1, -1);                  // 翻转 Y 轴
// 现在可以按数学坐标系绘图了
ctx.fillRect(0, 0, 100, 100);  // 从左下角画一个 100x100 的矩形

// 但文本会倒置，需要单独翻转回来
ctx.save();
ctx.scale(1, -1);  // 翻回来
ctx.fillText('Hello', 50, -50);  // 注意 Y 坐标的计算
ctx.restore();

ctx.restore();
```

### 4.2.3 视口（Viewport）与世界坐标（World Coordinate）

在可缩放、可平移的画布应用中（如地图、白板），需要区分两种坐标系：

**世界坐标（World Coordinate）**：图元的原始坐标，不随缩放和平移变化。

**视口坐标（Viewport Coordinate）**：图元在屏幕上的实际显示坐标，受缩放和平移影响。

```
世界坐标系：
┌────────────────────────────────┐
│  (0,0)                         │
│    ┌──┐                        │
│    │A │                        │
│    └──┘                        │
│              ┌──┐              │
│              │B │              │
│              └──┘              │
│                    ┌─────────┐ │
│                    │ 视口     │ │  ← 当前可见区域
│                    │ (缩放2x)│ │
│                    └─────────┘ │
└────────────────────────────────┘

视口坐标系（屏幕显示）：
┌────────────────┐
│                │
│  B 的部分       │  ← 只有 B 在视口内可见
│                │
└────────────────┘
```

**坐标转换公式**：

```javascript
class Viewport {
  constructor() {
    this.x = 0;       // 视口偏移 X
    this.y = 0;       // 视口偏移 Y
    this.scale = 1;   // 缩放比例
  }
  
  // 世界坐标 → 视口坐标（用于绘制）
  worldToViewport(wx, wy) {
    return {
      x: (wx - this.x) * this.scale,
      y: (wy - this.y) * this.scale
    };
  }
  
  // 视口坐标 → 世界坐标（用于鼠标命中检测）
  viewportToWorld(vx, vy) {
    return {
      x: vx / this.scale + this.x,
      y: vy / this.scale + this.y
    };
  }
  
  // 应用到 Canvas 上下文
  apply(ctx) {
    ctx.scale(this.scale, this.scale);
    ctx.translate(-this.x, -this.y);
  }
}
```

> 金句：世界坐标是图元的"真实地址"，视口坐标是"你在哪里看到它"——两者之间的转换是可缩放画布的核心。

### 4.2.4 坐标变换的矩阵运算

所有的坐标变换都可以用矩阵表示。2D 仿射变换使用 3x3 矩阵（但只用 6 个参数）：

```
│ a  c  e │   │ x │   │ a·x + c·y + e │
│ b  d  f │ × │ y │ = │ b·x + d·y + f │
│ 0  0  1 │   │ 1 │   │       1        │
```

常见变换矩阵：

| 变换 | 矩阵 | 对应 API |
|------|------|---------|
| 平移 (tx, ty) | [1, 0, 0, 1, tx, ty] | ctx.translate(tx, ty) |
| 缩放 (sx, sy) | [sx, 0, 0, sy, 0, 0] | ctx.scale(sx, sy) |
| 旋转 θ | [cosθ, sinθ, -sinθ, cosθ, 0, 0] | ctx.rotate(θ) |
| 错切 (shx, shy) | [1, shy, shx, 1, 0, 0] | ctx.transform(1, shy, shx, 1, 0, 0) |

矩阵乘法不满足交换律，所以变换顺序很重要。Canvas 的变换是**右乘**（post-multiply），意味着后调用的变换先作用于图元：

```javascript
// 等价于：先旋转，再平移
ctx.translate(100, 100);
ctx.rotate(Math.PI / 4);
ctx.fillRect(0, 0, 50, 50);

// 等价于：先平移，再旋转
ctx.rotate(Math.PI / 4);
ctx.translate(100, 100);
ctx.fillRect(0, 0, 50, 50);
// 两个结果完全不同
```

## 4.3 画布的生命周期管理

### 4.3.1 创建与销毁

画布的创建很简单，但销毁时需要注意资源释放：

```javascript
// 创建画布
const canvas = document.createElement('canvas');
canvas.width = 800;
canvas.height = 600;
document.body.appendChild(canvas);

const ctx = canvas.getContext('2d');

// 销毁画布
function destroyCanvas(canvas, ctx) {
  // 1. 停止动画循环
  cancelAnimationFrame(animationId);
  
  // 2. 移除事件监听器
  canvas.removeEventListener('click', onClick);
  // ...其他监听器
  
  // 3. 清空画布内容（释放像素缓冲区引用）
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // 4. 从 DOM 移除
  canvas.remove();
  
  // 5. 清除引用（让 GC 回收）
  canvas = null;
  ctx = null;
}
```

> 金句：Canvas 创建是"new"，销毁是"delete"——别只管创建不管释放，否则内存泄漏和事件重复绑定会找上你。

### 4.3.2 尺寸变更与重绘策略

当画布尺寸变化时，需要重新设置缓冲区并重绘所有内容。这是 Canvas 和 SVG 的一个重要差异——SVG 的尺寸变化由浏览器自动处理，Canvas 需要开发者手动处理。

**尺寸变更的影响**：

```javascript
canvas.width = 1024;  // 1. 像素缓冲区重新分配
                       // 2. 所有已绘制内容清空
                       // 3. 上下文状态重置（fillStyle, transform 等）
                       // 4. 裁剪区域重置为整个画布
```

**正确的尺寸变更流程**：

```javascript
function resizeCanvas(canvas, newWidth, newHeight) {
  const ctx = canvas.getContext('2d');
  
  // 1. 保存当前绘图状态（不会被 width 重置的只有你的数据模型）
  // 注意：save() 的状态会在 width 变更时丢失，所以需要手动保存
  
  // 2. 设置新尺寸
  canvas.width = newWidth;
  canvas.height = newHeight;
  
  // 3. 重新应用 DPR 适配
  const dpr = window.devicePixelRatio || 1;
  canvas.style.width = newWidth + 'px';
  canvas.style.height = newHeight + 'px';
  canvas.width = newWidth * dpr;
  canvas.height = newHeight * dpr;
  ctx.scale(dpr, dpr);
  
  // 4. 重新应用绘图状态
  ctx.fillStyle = currentFillStyle;
  ctx.strokeStyle = currentStrokeStyle;
  ctx.lineWidth = currentLineWidth;
  // ...其他状态
  
  // 5. 根据新尺寸重新绘制所有图元
  redrawAll();
}
```

### 4.3.3 ResizeObserver 监听画布容器变化

现代浏览器提供了 ResizeObserver 来监听元素尺寸变化，比 window.resize 更精确：

```javascript
const container = document.querySelector('.canvas-container');
const canvas = container.querySelector('canvas');

const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    const { width, height } = entry.contentRect;
    
    // 防抖：避免频繁重绘
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      resizeCanvas(canvas, width, height);
    }, 100);
  }
});

resizeObserver.observe(container);

// 清理
// resizeObserver.disconnect();
```

**注意事项**：
1. ResizeObserver 的回调可能在同一帧内触发多次，需要防抖
2. 观察的是容器尺寸，不是 canvas 本身（避免循环触发）
3. 首次 observe 时会立即触发一次回调

### 4.3.4 画布的持久化：toDataURL / toBlob / captureStream

Canvas 的内容是像素，需要持久化时有三种方法：

**toDataURL() — 转为 Base64 字符串**：

```javascript
const dataURL = canvas.toDataURL('image/png');
// data:image/png;base64,iVBORw0KGgo...

// 可直接用作 img 标签的 src
const img = new Image();
img.src = dataURL;
document.body.appendChild(img);
```

特点：
- 同步方法，会阻塞主线程
- 返回 Base64 编码，体积比原始二进制大约 33%
- 画布被污染（跨域）时会抛 SecurityError

**toBlob() — 转为 Blob 对象**：

```javascript
canvas.toBlob((blob) => {
  // blob 是二进制对象，体积更小
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.src = url;
  document.body.appendChild(img);
  
  // 用完记得释放
  // URL.revokeObjectURL(url);
}, 'image/png', 0.92);  // 0.92 是质量参数（仅 JPEG/WebP）
```

特点：
- 异步方法，不阻塞主线程
- 返回二进制，体积比 toDataURL 小
- 适合大画布和需要上传/下载的场景

**captureStream() — 捕获为视频流**：

```javascript
const stream = canvas.captureStream(30);  // 30 fps
const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

const chunks = [];
recorder.ondataavailable = (e) => chunks.push(e.data);
recorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'video/webm' });
  const url = URL.createObjectURL(blob);
  // 下载或播放
};

recorder.start();
// ...录制一段时间后
recorder.stop();
```

特点：
- 捕获画布的实时动画为视频
- 适合录制演示、动画、游戏画面
- 输出格式取决于浏览器支持（WebM 为主）

**三种持久化方法对比**：

| 方法 | 输出格式 | 同步/异步 | 体积 | 适用场景 |
|------|---------|----------|------|---------|
| toDataURL | PNG/JPEG/Base64 | 同步 | 大 | 小画布、快速预览 |
| toBlob | PNG/JPEG/WebP | 异步 | 小 | 大画布、上传/下载 |
| captureStream | WebM 视频 | 实时流 | 中 | 录制动画/游戏 |

> 金句：toDataURL 适合快速预览，toBlob 适合文件操作，captureStream 适合录制动画——选对工具事半功倍。

**离屏持久化策略**：

在某些场景下（如画布尺寸变更前的内容保存），需要临时保存画布内容：

```javascript
// 方法 1：保存为 ImageBitmap（最高性能）
const bitmap = await createImageBitmap(canvas);
// 之后可以 drawImage(bitmap, 0, 0) 恢复

// 方法 2：保存为 ImageData
const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
// 之后可以 ctx.putImageData(imageData, 0, 0) 恢复

// 方法 3：使用临时 canvas
const tempCanvas = document.createElement('canvas');
tempCanvas.width = canvas.width;
tempCanvas.height = canvas.height;
tempCanvas.getContext('2d').drawImage(canvas, 0, 0);
// 之后可以 ctx.drawImage(tempCanvas, 0, 0) 恢复
```

| 方法 | 性能 | 内存 | 支持缩放 | 适用场景 |
|------|------|------|---------|---------|
| ImageBitmap | 最好 | 中 | 是 | 现代浏览器、高性能场景 |
| ImageData | 差 | 大 | 否 | 需要像素级操作 |
| 临时 canvas | 好 | 大 | 是 | 兼容性好、简单 |

## 4.4 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| 画布系统定义 | 狭义=单 canvas，广义=多画布+数据模型+渲染管线+交互系统 |
| 屏幕坐标系 | 左上原点，Y 向下，和数学坐标系相反 |
| 坐标系转换 | Y 轴翻转或 scale(1, -1)，注意文本倒置问题 |
| 世界坐标 vs 视口坐标 | 世界=图元原始坐标，视口=屏幕显示坐标，转换靠矩阵 |
| 变换矩阵 | 3x3 仿射矩阵，右乘叠加，顺序很重要 |
| 尺寸变更 | 修改 width/height 会清空内容和重置状态，需完整重绘 |
| ResizeObserver | 监听容器尺寸变化，需要防抖 |
| 持久化方法 | toDataURL（同步Base64）/ toBlob（异步二进制）/ captureStream（视频流） |
| 离屏保存 | ImageBitmap > 临时 canvas > ImageData |

觉得有用？收藏起来，下次画布尺寸变化或需要持久化时直接查表。

你在画布尺寸变化时是怎么处理的？有没有踩过"内容消失"的坑？评论区聊聊。

关注怕浪猫，下期我们讲 **绘制原语与路径系统**——从 fillRect 到贝塞尔曲线的完整绘制体系。

系列进度 4/17

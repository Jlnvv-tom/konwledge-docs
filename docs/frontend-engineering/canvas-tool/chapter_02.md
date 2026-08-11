# 第2章 Canvas 核心原理：上下文、像素与状态机

你以为 `getContext('2d')` 就是拿个画笔？

其实你拿到的是一台**状态机**。你每调一次 `fillStyle = 'red'`，不是在"选颜色"，而是在修改状态机的内部状态。下一次 `fillRect` 的行为，取决于状态机的当前状态——而状态可能有 20 多个维度。

很多人写了三五年 Canvas，从没搞清楚 `save()` 和 `restore()` 到底存了什么。更别提 `getImageData` 返回的 `Uint8ClampedArray` 为什么是 Clamped 而不是普通 Uint8Array。

我是怕浪猫，今天把 Canvas 的底裤扒下来给大家看。这篇是 Canvas 工程全书的第 2 章，深入上下文机制、状态机模型和像素操作底层。

## 2.1 Canvas 元素的本质

### 2.1.1 `<canvas>` 的物理模型：一块可编程的位图

从物理层面看，canvas 就是一块**位图（Bitmap）**。它不是一个图元容器，不是一棵 DOM 树，就是一张二维像素网格。

每个像素由 4 个字节组成：R（Red，红色）、G（Green，绿色）、B（Blue，蓝色）、A（Alpha，透明度），共 32 位。一张 800 x 600 的 canvas，像素缓冲区大小是：

```
800 × 600 × 4 = 1,920,000 字节 ≈ 1.83 MB
```

这块内存在 canvas 元素创建时分配，在元素销毁时释放。修改 `canvas.width` 或 `canvas.height` 会重新分配整块内存。

canvas 元素和普通 DOM 元素的本质区别：

| 维度 | 普通 DOM 元素 | Canvas 元素 |
|------|-------------|-------------|
| 内容存储 | DOM 节点树（矢量描述） | 像素缓冲区（位图） |
| 内容操作 | DOM API（getElementById 等） | Canvas 2D API（fillRect 等） |
| 修改后 | 触发 reflow/repaint | 只更新像素缓冲区 |
| 事件处理 | 原生 DOM 事件 | 需自行实现命中检测 |
| 可访问性 | 屏幕阅读器可读 | 屏幕阅读器不可读（除非加 ARIA） |
| 缩放质量 | 矢量缩放，清晰 | 位图缩放，模糊 |

> 金句：Canvas 的本质是"一张可编程的纸"——你画上去的是像素，不是对象。画完就融入了纸面，再也拿不回来。

### 2.1.2 画布的分辨率：backing store 与 CSS 像素

canvas 有两套尺寸系统，理解它们的关系是高清屏适配的基础。

**绘图缓冲区尺寸（backing store size）**：由 `canvas.width` 和 `canvas.height` 属性决定，定义了像素缓冲区的物理分辨率。

**CSS 显示尺寸**：由 CSS 的 `width` 和 `height` 属性决定，定义了元素在页面中占据的空间。

```javascript
const canvas = document.querySelector('canvas');

// 绘图缓冲区：400 x 300 像素
canvas.width = 400;
canvas.height = 300;

// CSS 显示：800 x 600 CSS 像素
canvas.style.width = '800px';
canvas.style.height = '600px';

// 结果：400x300 的像素被拉伸到 800x600 显示
// 每个 backing store 像素对应 2x2 个 CSS 像素
// 看起来会模糊
```

两套尺寸的关系就像一张照片：backing store 是照片的物理分辨率（比如 400x300），CSS 尺寸是照片被冲洗出来的大小（比如 8x6 英寸）。同一张底片冲成大照片就会模糊。

### 2.1.3 设备像素比（DPR）与高分屏适配

DPR（Device Pixel Ratio，设备像素比）是物理像素和 CSS 像素的比值。在普通显示器上 DPR = 1，在 Retina 显示器上 DPR = 2，在某些手机上 DPR = 3。

```
CSS 像素：1     物理像素：1      DPR = 1（普通屏）
                                   
CSS 像素：1     物理像素：2x2    DPR = 2（Retina）
                                   
CSS 像素：1     物理像素：3x3    DPR = 3（手机）
```

如果 canvas 的 backing store 尺寸等于 CSS 尺寸，在 DPR=2 的屏幕上，1 个 backing store 像素要覆盖 2x2 个物理像素，看起来就模糊。

**高分屏适配的标准做法**：

```javascript
function setupCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  
  // 设置 backing store 尺寸 = CSS 尺寸 × DPR
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  
  // CSS 尺寸保持不变
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  
  const ctx = canvas.getContext('2d');
  
  // 缩放绘图坐标系，让 1 个绘图单位 = 1 个 CSS 像素
  ctx.scale(dpr, dpr);
  
  return ctx;
}

// 使用后，你可以按 CSS 像素坐标绘图
ctx.fillRect(0, 0, 100, 100);
// 在 DPR=2 的屏幕上，实际绘制 200x200 物理像素，清晰
```

> 金句：DPR 适配的核心公式只有一句——backing store 尺寸乘以 DPR，绘图坐标缩放 DPR。

**DPR 变化处理**：当用户把窗口从外接显示器拖到 Retina 屏幕时，DPR 会变化。需要监听 `matchMedia` 来响应：

```javascript
const mql = matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`);
mql.addEventListener('change', () => {
  setupCanvas(canvas);  // 重新设置画布尺寸
  redraw();             // 重新绘制所有内容
});
```

## 2.2 上下文（Context）机制

### 2.2.1 getContext('2d') — 2D 位图绘制上下文

`getContext('2d')` 返回一个 CanvasRenderingContext2D 对象。这个对象是 canvas 像素缓冲区的编程接口，所有绘图命令通过它发出。

```javascript
const ctx = canvas.getContext('2d');

// 上下文对象持有以下核心引用：
// 1. canvas 元素引用（ctx.canvas === canvas）
// 2. 像素缓冲区（内部，不可直接访问）
// 3. 绘图状态栈（内部）
// 4. 当前绘图状态（fillStyle, strokeStyle, transform 等）
```

2D 上下文提供以下类别的 API：

| API 类别 | 主要方法 | 说明 |
|---------|---------|------|
| 矩形绘制 | fillRect, strokeRect, clearRect | 最高性能的绘制方法 |
| 路径绘制 | beginPath, moveTo, lineTo, arc, fill, stroke | 任意形状绘制 |
| 文本绘制 | fillText, strokeText, measureText | 文字渲染 |
| 图像绘制 | drawImage | 图片/视频/canvas 间复制 |
| 像素操作 | getImageData, putImageData, createImageData | 像素级控制 |
| 状态管理 | save, restore | 状态快照入栈/出栈 |
| 坐标变换 | translate, rotate, scale, setTransform | 修改变换矩阵 |
| 合成控制 | globalAlpha, globalCompositeOperation | 图层合成 |
| 裁剪 | clip | 设置裁剪区域 |
| 滤镜 | ctx.filter | CSS filter 函数 |

2D 上下文的实现因浏览器而异。Chrome 使用 Skia 图形库，Firefox 使用 Azure/Cairo，Safari 使用 Core Graphics。不同实现之间有微小的渲染差异（特别是文本和抗锯齿）。

### 2.2.2 getContext('webgl') / getContext('webgl2') — GPU 上下文

WebGL 上下文提供了直接编程 GPU 的接口。和 2D 上下文有本质区别：

| 维度 | 2D 上下文 | WebGL 上下文 |
|------|----------|-------------|
| 渲染方式 | CPU 软件渲染（或 GPU 加速） | GPU 硬件渲染 |
| 编程模型 | 命令式（调 API） | 着色器编程（GLSL） |
| 抽象层级 | 高（fillRect 一行搞定） | 低（需要写顶点/片元着色器） |
| 性能上限 | 中等 | 高 |
| 学习曲线 | 低 | 高 |

同一个 canvas 不能同时持有 2D 和 WebGL 上下文：

```javascript
const canvas = document.querySelector('canvas');
const ctx2d = canvas.getContext('2d');
const gl = canvas.getContext('webgl');

console.log(ctx2d); // CanvasRenderingContext2D
console.log(gl);    // null —— 2D 上下文已占用
```

### 2.2.3 getContext('bitmaprenderer') — ImageBitmap 渲染上下文

这是最简单的上下文，只有一个方法 `transferFromImageBitmap()`：

```javascript
const ctx = canvas.getContext('bitmaprenderer');

// 创建一个 ImageBitmap
const bitmap = await createImageBitmap(imageData);

// 直接把 bitmap 内容显示到 canvas 上
ctx.transferFromImageBitmap(bitmap);

// transfer 后 bitmap 被转移，不能再使用
```

这个上下文的用途是高性能的图像显示——当你只需要把一张图片显示到 canvas 上，不需要绘制操作时，它比 2D 上下文的 `drawImage` 更高效，因为它可以零拷贝传输。

### 2.2.4 上下文的生命周期与丢失恢复

WebGL 上下文可能因为 GPU 资源紧张而被浏览器回收，这叫**上下文丢失（Context Loss）**。

```javascript
const canvas = document.querySelector('canvas');
const gl = canvas.getContext('webgl');

// 监听上下文丢失
canvas.addEventListener('webglcontextlost', (e) => {
  e.preventDefault();  // 阻止默认行为，允许后续恢复
  console.log('WebGL context lost');
  // 清理引用，停止渲染循环
});

// 监听上下文恢复
canvas.addEventListener('webglcontextrestored', () => {
  console.log('WebGL context restored');
  // 重新创建着色器、缓冲区、纹理等所有 GPU 资源
  // 重新设置 WebGL 状态
  // 恢复渲染循环
});
```

上下文丢失是 WebGL 应用必须处理的事件。如果不处理，用户切换标签页、GPU 崩溃、显存不足都可能导致应用白屏且无法恢复。

2D 上下文不会发生上下文丢失——它的资源在 CPU 内存中，不受 GPU 状态影响。

> 金句：WebGL 上下文是借来的 GPU 资源，随时可能被收回；2D 上下文是自己的 CPU 内存，稳如老狗。

## 2.3 2D Context 的状态机模型

这是本章最核心的部分。2D 上下文不是一组独立函数的集合，它是一台**状态机（State Machine）**。

### 2.3.1 绘图状态栈（Drawing State Stack）

2D 上下文维护了一个内部状态栈。`save()` 将当前状态的快照压入栈顶，`restore()` 将栈顶快照弹出并恢复为当前状态。

当前状态包含以下属性：

```
┌─────────────────────────────────────┐
│        当前绘图状态 (Current State)    │
├─────────────────────────────────────┤
│ fillStyle                           │
│ strokeStyle                         │
│ lineWidth                           │
│ lineCap                             │
│ lineJoin                            │
│ miterLimit                          │
│ lineDashOffset                      │
│ shadowOffsetX / Y                   │
│ shadowBlur                          │
│ shadowColor                         │
│ globalAlpha                         │
│ globalCompositeOperation            │
│ font                                │
│ textAlign                           │
│ textBaseline                        │
│ direction                           │
│ imageSmoothingEnabled               │
│ imageSmoothingQuality               │
│ 变换矩阵 (Transformation Matrix)     │
│ 裁剪区域 (Clipping Region)           │
└─────────────────────────────────────┘
           │
           │ save()
           ▼
┌─────────────────────────────────────┐
│        状态栈 (State Stack)           │
├─────────────────────────────────────┤
│ [栈顶] 状态快照 #N                   │
│        状态快照 #N-1                 │
│        ...                          │
│        状态快照 #1                   │
│ [栈底] 状态快照 #0                   │
└─────────────────────────────────────┘
```

注意：**绘图路径不在状态中**。`save()` 不会保存当前路径，`beginPath()` 创建的新路径不受 `save()`/`restore()` 影响。

### 2.3.2 save() / restore() 的本质：状态快照入栈与出栈

```javascript
// 初始状态：fillStyle = 'black', transform = identity
ctx.fillStyle = 'red';
ctx.save();  // 压入快照：{ fillStyle: 'red', transform: identity, ... }

ctx.fillStyle = 'blue';
ctx.translate(100, 100);
ctx.save();  // 压入快照：{ fillStyle: 'blue', transform: translate(100,100), ... }

ctx.fillStyle = 'green';
ctx.rotate(Math.PI / 4);
// 当前状态：fillStyle = 'green', transform = translate(100,100) × rotate(45°)

ctx.restore();  // 弹出栈顶，恢复为：fillStyle = 'blue', transform = translate(100,100)
ctx.restore();  // 弹出栈顶，恢复为：fillStyle = 'red', transform = identity
```

状态栈的容量是有限的（通常没有明确限制，但过度 save 不 restore 会导致内存泄漏）。每个 `save()` 必须有对应的 `restore()`，否则栈会无限增长。

**典型使用模式**：在绘制一个复杂图形前 save，绘制完 restore，保证不影响外部状态。

```javascript
function drawButton(ctx, x, y, text) {
  ctx.save();  // 保存外部状态
  
  ctx.translate(x, y);
  ctx.fillStyle = '#4CAF50';
  ctx.fillRect(0, 0, 100, 40);
  ctx.fillStyle = 'white';
  ctx.font = '14px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 50, 20);
  
  ctx.restore();  // 恢复外部状态，不影响调用者的 fillStyle/font/transform
}
```

> 金句：save/restore 是 Canvas 版的 Git commit/checkout——在绘图流程中打快照，随时回滚到之前的状态。

### 2.3.3 变换矩阵（Transformation Matrix）的叠加原理

2D 上下文内部维护一个 3x3 的仿射变换矩阵（Affine Transformation Matrix），但只使用 6 个参数：

```
│ a  c  e │
│ b  d  f │
│ 0  0  1 │
```

其中：
- a, d：X/Y 方向缩放
- b, c：X/Y 方向错切（倾斜）
- e, f：X/Y 方向平移

`translate(tx, ty)` 的本质是矩阵右乘：

```
│ 1  0  tx │
│ 0  1  ty │
│ 0  0   1 │
```

`rotate(angle)` 的本质：

```
│ cos(θ)  -sin(θ)  0 │
│ sin(θ)   cos(θ)  0 │
│   0        0     1 │
```

`scale(sx, sy)` 的本质：

```
│ sx  0   0 │
│  0  sy  0 │
│  0   0  1 │
```

每次调用 translate/rotate/scale，都是将当前矩阵**右乘**新变换矩阵。这意味着变换的顺序很重要：

```javascript
// 先平移再旋转
ctx.translate(100, 0);
ctx.rotate(Math.PI / 4);
ctx.fillRect(0, 0, 50, 50);
// 矩阵：T(100,0) × R(45°)
// 矩形先旋转 45°，再平移到 (100,0)

// 先旋转再平移
ctx.rotate(Math.PI / 4);
ctx.translate(100, 0);
ctx.fillRect(0, 0, 50, 50);
// 矩阵：R(45°) × T(100,0)
// 矩形先平移到 (100,0)，再绕原点旋转 45°
// 结果完全不同！
```

> 金句：Canvas 变换矩阵是右乘叠加的——你写的代码顺序和直觉中的变换顺序是反的。

### 2.3.4 裁剪区域（Clipping Region）的状态传递

`clip()` 方法将当前路径作为裁剪区域。裁剪区域是绘图状态的一部分，会被 `save()`/`restore()` 保存和恢复。

```javascript
ctx.save();

// 创建圆形裁剪区域
ctx.beginPath();
ctx.arc(100, 100, 50, 0, Math.PI * 2);
ctx.clip();

// 之后所有绘制只在圆内可见
ctx.fillRect(0, 0, 200, 200);  // 只有圆内部分显示

ctx.restore();  // 恢复裁剪区域为整个画布

ctx.fillRect(0, 0, 200, 200);  // 完整显示
```

裁剪区域一旦设置，无法直接缩小——只能通过 save/restore 恢复到之前的裁剪区域。这是 Canvas 裁剪的限制。

## 2.4 像素操作底层

### 2.4.1 ImageData 结构：Uint8ClampedArray 的含义

`getImageData()` 返回一个 ImageData 对象：

```javascript
const imageData = ctx.getImageData(0, 0, 100, 100);
// imageData.width = 100
// imageData.height = 100
// imageData.data = Uint8ClampedArray(40000)  // 100×100×4
```

`Uint8ClampedArray` 是 TypedArray 的一种，有两个特殊行为：

1. **Clamped（截断）**：赋值时自动截断到 0-255 范围。`arr[i] = 300` 变成 255，`arr[i] = -50` 变成 0。
2. **取整**：赋值时自动取整。`arr[i] = 127.6` 变成 127（注意是截断不是四舍五入）。

为什么不用普通的 `Uint8Array`？因为 `Uint8Array` 对越界值取模（`300 % 256 = 44`），这在图像处理中是错误行为——255+50 应该是 255 而不是 44。

```javascript
const clamped = new Uint8ClampedArray(1);
const normal = new Uint8Array(1);

clamped[0] = 300;  // 255
normal[0] = 300;   // 44  (300 % 256)

clamped[0] = -50;  // 0
normal[0] = -50;   // 206 (-50 + 256)
```

像素数据的排列方式是**逐行从左到右，每像素 RGBA 四通道**：

```
像素 (0,0): R G B A | 像素 (1,0): R G B A | ... | 像素 (99,0): R G B A
像素 (0,1): R G B A | ...                                        │
...                                                           │
像素 (0,99): R G B A | ...                ← 像素 (99,99): R G B A

索引计算：index = (y × width + x) × 4
  R = data[index]
  G = data[index + 1]
  B = data[index + 2]
  A = data[index + 3]
```

### 2.4.2 getImageData() / putImageData() 的性能特征

这两个方法是 Canvas 中最重的操作之一。

`getImageData()` 的性能成本：
- 强制刷新绘图命令队列（同步执行所有待执行命令）
- 从 GPU 纹理回读到 CPU 内存（如果 canvas 是硬件加速的）
- 分配新的 Uint8ClampedArray 内存

`putImageData()` 的性能成本：
- 将 CPU 内存数据上传到 GPU 纹理
- 跳过合成模式（直接覆盖像素，不受 globalCompositeOperation 影响）

```javascript
// 慢：在动画循环中逐像素操作
function animate() {
  const imageData = ctx.getImageData(0, 0, width, height);  // 强制刷新 + GPU 回读
  for (let i = 0; i < imageData.data.length; i += 4) {
    // 逐像素处理...
  }
  ctx.putImageData(imageData, 0, 0);  // CPU → GPU 上传
  requestAnimationFrame(animate);
}

// 快：批量处理，减少 getImageData/putImageData 调用
let cachedImageData = null;

function init() {
  cachedImageData = ctx.getImageData(0, 0, width, height);  // 只调一次
}

function animate() {
  const data = cachedImageData.data;
  for (let i = 0; i < data.length; i += 4) {
    // 逐像素处理...
  }
  ctx.putImageData(cachedImageData, 0, 0);  // 只上传，不回读
  requestAnimationFrame(animate);
}
```

> 金句：getImageData 是 Canvas 的性能刹车——每调一次，GPU 和 CPU 之间就跑一趟往返。

### 2.4.3 预乘 Alpha（Premultiplied Alpha）的坑

Canvas 内部存储像素时使用的是**预乘 Alpha（Premultiplied Alpha）**格式。但 getImageData 返回的是**非预乘**格式。

预乘 Alpha 的含义：RGB 通道的值已经乘以 Alpha 通道的值（归一化到 0-1）：

```
非预乘：R=255, G=128, B=64, A=128（50% 透明）
预乘：  R=128, G=64,  B=32, A=128
       （R×A/255 = 255×128/255 = 128）
```

这导致一个微妙的问题：当你用 `getImageData` 读取半透明像素，处理后再用 `putImageData` 写回，某些像素的颜色可能和你预期的不一样。因为 `putImageData` 会将非预乘数据转为预乘存储，这个过程对于已经"烧过"的半透明像素会产生精度损失。

**实际坑场景**：

```javascript
// 画一个半透明红色矩形
ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
ctx.fillRect(0, 0, 100, 100);

// 读取像素
const imageData = ctx.getImageData(0, 0, 100, 100);
const pixel = imageData.data;
console.log(pixel[0], pixel[1], pixel[2], pixel[3]);
// 你可能期望 255, 0, 0, 128
// 实际得到 255, 0, 0, 128（大多数浏览器是对的）
// 但在某些情况下，多次 round-trip 后颜色会偏移
```

### 2.4.4 跨域（CORS）与画布污染（Tainted Canvas）

如果 canvas 绘制了跨域的图片，画布会被**污染（Tainted）**。污染后的 canvas 不能调用 `getImageData()`、`toDataURL()`、`toBlob()`，否则抛出安全异常。

```javascript
const img = new Image();
img.crossOrigin = 'anonymous';  // 必须设置，否则跨域图片会污染画布
img.src = 'https://example.com/image.png';
img.onload = () => {
  ctx.drawImage(img, 0, 0);
  
  try {
    const data = ctx.getImageData(0, 0, 100, 100);
  } catch (e) {
    // 如果服务器没返回 CORS 头，这里会抛异常
    console.error('画布被污染：', e);
  }
};
```

**污染的规则**：

| 操作 | 是否污染画布 | 条件 |
|------|------------|------|
| drawImage(同域图片) | 否 | - |
| drawImage(跨域图片, 无 crossOrigin) | 是 | - |
| drawImage(跨域图片, crossOrigin='anonymous') | 否 | 服务器返回 CORS 头 |
| drawImage(跨域图片, crossOrigin='anonymous') | 是 | 服务器未返回 CORS 头 |
| drawImage(video) | 取决于 video 是否跨域 | 同上 |
| drawImage(anotherCanvas) | 继承源 canvas 的污染状态 | - |

**一旦污染，不可逆**——没有任何方法可以"清洁"画布。唯一的办法是创建新画布重新绘制。

> 金句：跨域图片不设 crossOrigin 就 drawImage，你的 getImageData 就永远报废了——这是 Canvas 最隐蔽的坑之一。

## 2.5 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| Canvas 物理模型 | 一块可编程位图，非图元容器 |
| 两套尺寸系统 | width/height 属性 = 缓冲区分辨率；CSS width/height = 显示尺寸 |
| DPR 适配 | backing store × DPR，ctx.scale(dpr) |
| 上下文类型 | 2d（CPU 绘图）/ webgl（GPU 绘图）/ bitmaprenderer（图像显示） |
| 上下文丢失 | WebGL 可丢失需恢复，2D 不会丢失 |
| 状态机模型 | 20+ 属性 + 变换矩阵 + 裁剪区域，save/restore 管理状态栈 |
| 变换矩阵 | 右乘叠加，代码顺序与直觉相反 |
| ImageData | Uint8ClampedArray，自动截断 0-255 |
| getImageData 性能 | 强制刷新命令队列 + GPU 回读，是性能杀手 |
| 预乘 Alpha | 内部预乘存储，getImageData 返回非预乘，round-trip 有精度损失 |
| 画布污染 | 跨域图片 drawImage 会污染画布，getImageData/toDataURL 失效 |

觉得有用？收藏起来，下次用到的时候直接查表。

你的 canvas 有没有遇到过"颜色莫名其妙变暗"或者"getImageData 报 SecurityError"的情况？评论区说说，怕浪猫帮你排查。

关注怕浪猫，下期我们讲 **Canvas 与 SVG：位图与矢量的两条道路**——90% 的前端在技术选型时都选错过。

系列进度 2/17

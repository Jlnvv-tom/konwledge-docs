# 第5章 绘制原语与路径系统

> 系列进度 5/17 | Canvas 工程全书

我是怕浪猫，一只对渲染管线着迷的猫。

你以为 `fillRect` 就是画个矩形？它底层走的是和 Path 完全不同的快速通道，性能差出 10 倍都不稀奇。矩形原语跳过了路径解析、子路径合并、填充规则判定，直接把像素写进 framebuffer（帧缓冲区）。

## 5.1 基本图形绘制

Canvas 2D 上下文（`CanvasRenderingContext2D`）提供三类直接绘制原语：矩形、文本、图片。它们不需要手动构建路径，走的代码路径和 Path2D 不同。

### 5.1.1 矩形：fillRect / strokeRect / clearRect

```
+-------------+----------------+-------------------------+
| API         | 作用           | 内部路径？               |
+-------------+----------------+-------------------------+
| fillRect    | 填充矩形区域    | 不走 Path2D，直接光栅化  |
| strokeRect  | 描边矩形        | 不走 Path2D，直接光栅化  |
| clearRect   | 清除为透明      | 不走 Path2D，直接清零    |
+-------------+----------------+-------------------------+
```

这三个方法不会修改当前路径。调了 `fillRect` 后，`beginPath` 建的路径依然存在。

```javascript
const ctx = canvas.getContext('2d');
ctx.fillStyle = '#e74c3c';
ctx.fillRect(10, 10, 100, 60);       // 填充
ctx.strokeStyle = '#2c3e50';
ctx.strokeRect(130, 10, 100, 60);    // 描边
ctx.clearRect(50, 30, 40, 20);       // 挖洞
```

> 矩形原语是 Canvas 中唯一不经过路径系统的绘制方法，这是它快的根本原因。

性能对比（每帧 10000 个矩形，Chrome 120 / M2）：

```
方法                    耗时(ms)
--------------------------------
fillRect                2.1
ctx.rect + ctx.fill     8.7
Path2D + ctx.fill       9.3
```

画大量矩形（热力图、像素艺术）直接用 `fillRect` 是唯一正解。

`clearRect` 有个坑：`globalCompositeOperation` 非 `source-over` 时清除行为可能异常。稳妥做法是清除前切回：

```javascript
ctx.save();
ctx.globalCompositeOperation = 'source-over';
ctx.clearRect(0, 0, canvas.width, canvas.height);
ctx.restore();
```

### 5.1.2 文本：fillText / strokeText 与字体度量

文本绘制涉及字体加载、字形光栅化、基线对齐等多个子系统。

```javascript
ctx.font = '20px "Helvetica Neue", Arial, sans-serif';
ctx.textBaseline = 'top';
ctx.textAlign = 'left';
ctx.fillStyle = '#333';
ctx.fillText('Hello Canvas', 10, 10);
```

`fillText(text, x, y, maxWidth)` 的 `maxWidth`：文本超宽时浏览器自动收缩字形宽度（非缩字号）来塞入。

`measureText` 返回 `TextMetrics`：

```
         ascent
       +---------+
       |  字形    |  actualBoundingBoxAscent
  base |---------|-------- baseline
       |         |  actualBoundingBoxDescent
       +---------+
  |<-- width -->|  (advance width)
```

> `width` 是 advance width（前进宽度），不等于视觉宽度——斜体可能溢出。

`textBaseline` 取值：`top`（顶部对齐）、`middle`（中点对齐）、`alphabetic`（拉丁基线，默认）、`ideographic`（CJK 基线）、`bottom`（底部对齐）。中文内容用 `'top'` 或 `'middle'` 更容易对齐。

字体加载是异步问题，Web Font 没加载完会用 fallback：

```javascript
async function drawWithFont() {
  await document.fonts.load('20px "MyCustomFont"');
  ctx.font = '20px "MyCustomFont"';
  ctx.fillText('字体就绪', 10, 10);
}
```

### 5.1.3 图片：drawImage 的三种重载与缩放策略

```
签名                                             用途
----------------------------------------------------------------------
drawImage(image, dx, dy)                         原始尺寸
drawImage(image, dx, dy, dw, dh)                 缩放
drawImage(image, sx,sy,sw,sh, dx,dy,dw,dh)       裁剪+缩放
```

第三种是精灵图（Sprite Sheet）动画核心：

```javascript
ctx.drawImage(spriteSheet,
  0, 0, 32, 32,     // 源：精灵图位置
  100, 100, 64, 64  // 目标：放大2倍
);
```

缩放质量由 `imageSmoothingEnabled` 和 `imageSmoothingQuality` 控制：

```javascript
ctx.imageSmoothingEnabled = true;
ctx.imageSmoothingQuality = 'high';  // 'low'|'medium'|'high'
// 像素艺术：关闭平滑
ctx.imageSmoothingEnabled = false;
```

`'high'` 可能用 Lanczos 重采样，GPU（Graphics Processing Unit，图形处理器）开销大。逐帧动画用 `'low'` 更平衡。

> drawImage 是唯一能直接操作 ImageBitmap 的原语，GPU 上传路径效率极高。

源可以是 `HTMLImageElement`、`HTMLCanvasElement`、`HTMLVideoElement`、`ImageBitmap`、`OffscreenCanvas`。`ImageBitmap` 性能最好，可在 Worker 创建且驻留 GPU：

```javascript
const bitmap = await createImageBitmap(blob);
ctx.drawImage(bitmap, 0, 0);
bitmap.close(); // 释放 GPU 内存
```

## 5.2 路径（Path）系统

路径是 Canvas 2D 核心抽象。生命周期三阶段：构建（beginPath + 命令）、可选闭合（closePath）、栅格化（fill/stroke/clip）。

### 5.2.1 Path2D 对象：可复用的路径描述

"构建一次，多次使用"：

```javascript
const star = new Path2D();
star.moveTo(50, 0);
for (let i = 1; i <= 10; i++) {
  const a = (Math.PI / 5) * i;
  const r = i % 2 === 0 ? 50 : 20;
  star.lineTo(Math.cos(a) * r, Math.sin(a) * r);
}
star.closePath();
ctx.fill(star);           // 填充
ctx.stroke(star);         // 描边
ctx.isPointInPath(star, 45, 12); // 命中检测
```

`Path2D` 还接受 SVG path 字符串：

```javascript
const heart = new Path2D('M10,30 A20,20 0 0,1 50,30 A20,20 0 0,1 90,30 Q90,60 50,90 Q10,60 10,30 Z');
ctx.fill(heart);
```

> Path2D 是唯一支持结构化复用的几何描述符，设计来自 SVG path 元素，运行时开销更低。

性能对比（1000 个复杂路径）：每帧重建路径 14.2ms，Path2D 复用 3.8ms。

### 5.2.2 子路径（Subpath）与闭合（Close Path）

每次 `moveTo` 开启新子路径。`closePath` 用直线连接起点终点并标记闭合。

```
moveTo(10,10) → lineTo(90,10) → lineTo(90,90) → closePath
  子路径1：闭合三角形

moveTo(100,50) → arc(100,50,30,0,π)
  子路径2：开放半圆弧
```

```javascript
// 不闭合
ctx.beginPath();
ctx.moveTo(10,10); ctx.lineTo(90,10); ctx.lineTo(90,90);
ctx.stroke(); // 两条线，缺一条边

// 闭合
ctx.beginPath();
ctx.moveTo(10,10); ctx.lineTo(90,10); ctx.lineTo(90,90);
ctx.closePath();
ctx.stroke(); // 完整三角形
```

`fill()` 会自动闭合未闭合子路径，但路径闭合状态不变，`stroke()` 仍看到未闭合轮廓。

常见 bug：画多个形状忘记 `beginPath`，所有子路径被一起填充，产生连通伪影。养成习惯：每次画新形状前必调 `beginPath()`。

### 5.2.3 贝塞尔曲线：二次与三次的数学原理

贝塞尔曲线（Bezier Curve）是矢量图形基础。

```
二次：B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
P0 ──────── P1 ──────── P2
起点        控制点       终点
              ╲___曲线轨迹

三次：B(t) = (1-t)³·P0 + 3(1-t)²t·P1 + 3(1-t)t²·P2 + t³·P3
P0 ──── P1 ──────── P2 ──── P3
起点    控制点1     控制点2  终点
```

```javascript
// 二次 quadraticCurveTo(cpx, cpy, x, y)
ctx.beginPath(); ctx.moveTo(0, 100);
ctx.quadraticCurveTo(50, 0, 100, 100); ctx.stroke();

// 三次 bezierCurveTo(cp1x,cp1y, cp2x,cp2y, x,y)
ctx.beginPath(); ctx.moveTo(0, 100);
ctx.bezierCurveTo(30, 0, 70, 0, 100, 100); ctx.stroke();
```

> 贝塞尔曲线本质是线性插值的递归嵌套，具有凸包性——曲线不超出控制点多边形范围。

```
特性        二次(quadratic)    三次(cubic)
-------------------------------------------
控制点      1                  2
灵活度      低（单一弯曲）      高（S形）
端点切线    由相邻点决定        独立可控
典型用途    圆弧近似            字体轮廓、复杂曲线
```

用三次贝塞尔近似圆弧，误差约 0.027%，系数 `k = 0.5522847498`：

```javascript
const r = 50, k = 0.5522847498;
ctx.beginPath();
ctx.moveTo(r, 0);
ctx.bezierCurveTo(r, r*k, r*k, r, 0, r);
ctx.bezierCurveTo(-r*k, r, -r, r*k, -r, 0);
ctx.bezierCurveTo(-r, -r*k, -r*k, -r, 0, -r);
ctx.bezierCurveTo(r*k, -r, r, -r*k, r, 0);
ctx.closePath();
```

### 5.2.4 圆弧与椭圆弧

`arc(x, y, radius, startAngle, endAngle, ccw)` 绘制圆弧，角度以弧度为单位：

```javascript
ctx.beginPath();
ctx.arc(100, 100, 50, 0, Math.PI * 2); // 完整圆
ctx.fill();
```

`arcTo(x1, y1, x2, y2, r)` 绘制相切圆弧，用于圆角矩形：

```javascript
function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x+w, y,   x+w, y+h, r);
  ctx.arcTo(x+w, y+h, x,   y+h, r);
  ctx.arcTo(x,   y+h, x,   y,   r);
  ctx.arcTo(x,   y,   x+r, y,   r);
  ctx.closePath();
}
```

`ellipse(x, y, rx, ry, rotation, startAngle, endAngle, ccw)` 是椭圆版本，多了轴半径和旋转参数。

> arc 和 ellipse 的角度是弧度。180度 = Math.PI，这是新手最常犯的 bug。

### 5.2.5 路径填充规则：nonzero vs evenodd

```
nonzero：射线穿过路径，顺时针+1逆时针-1，总和≠0则填充
evenodd：射线穿过路径次数，奇数填充偶数不填，不关心方向
```

两个同心圆的效果：

```
nonzero：内外都被填充    evenodd：只有环形被填充
 ┌─────────┐            ┌─────────┐
 │ ┌─────┐ │            │█████████│
 │ │█████│ │            │ ┌─────┐ │
 │ └─────┘ │            │ └─────┘ │
 └─────────┘            └─────────┘
```

```javascript
ctx.beginPath();
ctx.arc(100, 100, 60, 0, Math.PI * 2);
ctx.moveTo(140, 100);
ctx.arc(100, 100, 30, 0, Math.PI * 2);
ctx.fill('evenodd'); // 环形镂空
```

五角星用 `evenodd` 得到中心镂空，`nonzero` 全填充。需镂空用 `evenodd`，其他用默认 `nonzero`。

## 5.3 线条样式与端点

### 5.3.1 lineWidth / lineCap / lineJoin

```
lineCap:  butt(不延伸)  round(半圆延伸)  square(矩形延伸)
lineJoin: miter(尖角)   round(圆角)      bevel(斜切)
```

```javascript
ctx.lineWidth = 10;
ctx.lineCap = 'round';
ctx.lineJoin = 'round';
ctx.beginPath();
ctx.moveTo(50, 50); ctx.lineTo(150, 50); ctx.lineTo(100, 120);
ctx.stroke();
```

> 奇数线宽 + 整数坐标 = 模糊线条。解决：坐标偏移 0.5 像素或用偶数线宽。

```
lineWidth=1, x=10        lineWidth=1, x=10.5
   ╔═╗  跨两像素模糊      █    像素内，清晰
```

`miterLimit` 默认 10，miter 超线宽 10 倍时降级为 `bevel`。

### 5.3.2 虚线 setLineDash 与 dashOffset 动画

```javascript
ctx.setLineDash([10, 5]);        // 10px线 5px间隔
ctx.setLineDash([10, 5, 2, 5]);  // 复合模式
ctx.setLineDash([]);              // 清除
```

`lineDashOffset` 持续改变产生蚂蚁线动画：

```javascript
let offset = 0;
function animateDash() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.setLineDash([8, 4]);
  ctx.lineDashOffset = offset;
  ctx.strokeStyle = '#3498db';
  ctx.strokeRect(20, 20, 200, 100);
  offset -= 0.5;
  requestAnimationFrame(animateDash);
}
animateDash();
```

> 虚线动画是 Canvas 中性价比最高的动效——改一个数值就有连续运动反馈，计算成本极低。

虚线沿路径参数化长度排列。对贝塞尔曲线，浏览器内部自适应采样计算弧长，短曲线段上虚线分布可能不完全均匀。

## 5.4 渐变与图案

### 5.4.1 线性渐变与径向渐变

```javascript
// 线性 createLinearGradient(x0, y0, x1, y1)
const grad = ctx.createLinearGradient(0, 0, 200, 0);
grad.addColorStop(0, '#e74c3c');
grad.addColorStop(1, '#f1c40f');
ctx.fillStyle = grad;
ctx.fillRect(0, 0, 200, 100);

// 径向 createRadialGradient(x0,y0,r0, x1,y1,r1)
const rg = ctx.createRadialGradient(100, 50, 5, 100, 50, 80);
rg.addColorStop(0, 'rgba(255,255,255,1)');
rg.addColorStop(1, 'rgba(0,0,0,0)');
```

```
线性渐变         径向渐变
 x0 ──► x1       ◎════╗
 直线过渡         ║辐射║
                  ╚════╝
```

渐变对象与坐标绑定，不是与图形绑定。多个图形共用同一渐变时，各自显示该渐变在自身区域的切片。

### 5.4.2 Conic 渐变（圆锥渐变）

`createConicGradient(startAngle, x, y)` 绕中心点旋转过渡颜色：

```javascript
const conic = ctx.createConicGradient(-Math.PI / 2, 100, 100);
conic.addColorStop(0,    '#e74c3c');
conic.addColorStop(0.25, '#f39c12');
conic.addColorStop(0.5,  '#27ae60');
conic.addColorStop(0.75, '#2980b9');
conic.addColorStop(1,    '#e74c3c'); // 无缝衔接
ctx.fillStyle = conic;
ctx.fillRect(0, 0, 200, 200);
```

```
线性: ────►    径向: ◎══╗    圆锥: ╱──╲
方向:直线           ╚══╝       方向:角度
适合:条形       适合:光晕       适合:色轮、雷达图
```

> Conic 渐变 Chrome 69+ / Safari 12+ 支持。旧浏览器可用 JS 逐像素绘制作 polyfill。

### 5.4.3 Pattern 图案填充与重复模式

`createPattern(image, repetition)` 用图片作填充源：

```
repeat       水平垂直都重复
repeat-x     仅水平
repeat-y     仅垂直
no-repeat    不重复
```

Pattern 源也可以是另一个 Canvas，打开离屏渲染管线：

```javascript
const tile = document.createElement('canvas');
tile.width = 20; tile.height = 20;
const tctx = tile.getContext('2d');
tctx.fillStyle = '#34495e';
tctx.fillRect(0, 0, 20, 20);
tctx.fillStyle = '#3a546b';
tctx.beginPath(); tctx.arc(10, 10, 4, 0, Math.PI * 2); tctx.fill();

const pattern = ctx.createPattern(tile, 'repeat');
ctx.fillStyle = pattern;
ctx.fillRect(0, 0, 400, 400);
```

> Pattern 本质是纹理映射——浏览器把源图上传 GPU，用 UV 重复采样平铺，性能远优于循环 drawImage。

进阶：通过 `DOMMatrix` 给 Pattern 设变换：

```javascript
const m = new DOMMatrix();
m.scaleSelf(0.5);
m.rotateSelf(30);
pattern.setTransform(m);
```

Pattern 和渐变不能直接混用，但可分层：先 Pattern 填底层，再用带 `globalAlpha` 的渐变叠加。

## Canvas 2D 绘制 API 全清单

```
CanvasRenderingContext2D 绘制原语全览
├─ 矩形: fillRect / strokeRect / clearRect
├─ 文本: fillText / strokeText / measureText
├─ 图片: drawImage (3种重载)
├─ 路径构建
│   ├─ beginPath / closePath / moveTo / lineTo
│   ├─ rect / arc / arcTo / ellipse
│   └─ quadraticCurveTo / bezierCurveTo
├─ 路径栅格化: fill / stroke / clip / isPointInPath
├─ Path2D: new Path2D() / (svg) / (other)
├─ 线条样式
│   ├─ lineWidth / lineCap / lineJoin / miterLimit
│   └─ setLineDash / lineDashOffset
├─ 渐变与图案
│   ├─ createLinearGradient / createRadialGradient
│   ├─ createConicGradient / createPattern
└─ 填充规则: nonzero(默认) | evenodd
```

## 贝塞尔曲线数学原理图解

```
二次贝塞尔递归插值（t=0.5）：

P0 ●───────● A         ● B───────● P2
             ╲         ╱
              ╲       ╱
               ╲     ╱
                ╲   ╱
                 ╲ ╱
                  ● 曲线点(t=0.5)
       P1 ●

A=lerp(P0,P1,t), B=lerp(P1,P2,t), 曲线点=lerp(A,B,t)

三次贝塞尔（t=0.5）：

P0 ●────● A        ● D────● P3
         ╲        ╱
    B ●──● E  ● F──● C
            ╲╱
             ● 曲线点(t=0.5)
     P1 ●        ● P2
```

## 填充规则对比图

```
五角星（自相交路径）：

nonzero：整个星形被填充（含中心）
evenodd：外层填充，中心五边形镂空

  nonzero:          evenodd:
  ████████          ████████
  ████████          ██    ██
  ████████          ████████
```

## 本章小结

直接原语绕过路径系统走快速通道，适合大量简单图形。路径系统是几何核心，Path2D 提供可复用容器，贝塞尔曲线和圆弧构建复杂形状，填充规则决定着色逻辑。线条样式和虚线动画提供描边视觉表达。渐变和图案让填充升级到质感和纹理层面。

> 理解原语性能边界比记住 API 签名重要得多。知道何时用 fillRect、何时用 Path2D，决定应用是丝滑还是卡顿。

系列进度 5/17。下章进入"变换、合成与滤镜"——变换矩阵、`globalCompositeOperation` 的 12 种合成模式、CSS Filter 在 Canvas 中的应用。

收藏这章，画路径时翻出来对照。有疑问或发现，评论区聊。

> 别用 Path2D 画矩形，也别用 fillRect 画五角星——工具和场景匹配，是工程思维的第一课。
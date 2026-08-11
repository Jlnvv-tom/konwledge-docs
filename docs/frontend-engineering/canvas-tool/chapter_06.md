# 第6章 变换、合成与滤镜

> 12 种合成模式 + 16 种混合模式，怕浪猫花了 3 天才搞明白哪个是哪个。

各位读者好，我是怕浪猫。上一章像素级操作拆了个底朝天，这章往上层走——变换、合成与滤镜，决定 Canvas 渲染管线的后期处理能力。

变换涉及矩阵数学，合成涉及 Porter-Duff 运算族，滤镜涉及卷积核。怕浪猫的风格是把复杂的拆到不能再拆，用表格和代码让你一眼看懂。

## 6.1 坐标变换

Canvas 的坐标变换是渲染管线中最先执行的环节。每次调用绘制 API 时，浏览器先读取当前变换矩阵（Current Transformation Matrix，CTM），将顶点乘以该矩阵再光栅化。变换不修改已绘制内容，只影响后续绘制。

### 6.1.1 translate / rotate / scale 的矩阵复合

三个基础变换底层都是矩阵复合：

```
translate(tx, ty) → 新CTM = 旧CTM × T(tx, ty)
rotate(angle)     → 新CTM = 旧CTM × R(angle)
scale(sx, sy)     → 新CTM = 旧CTM × S(sx, sy)
```

每次调用都是右乘，变换顺序至关重要：

```javascript
// 顺序 A：先平移再旋转
ctx.translate(100, 100);
ctx.rotate(Math.PI / 4);
ctx.fillRect(0, 0, 50, 50);

// 顺序 B：先旋转再平移（结果完全不同）
ctx.rotate(Math.PI / 4);
ctx.translate(100, 100);
ctx.fillRect(0, 0, 50, 50);
```

> 变换黄金法则：你写代码的顺序就是矩阵相乘的顺序，也是作用在物体上的逆序。

写 translate → rotate → scale，矩阵是 T × R × S，但对绘制对象效果是先 scale 再 rotate 最后 translate，因为矩阵从右往左作用于向量。

```
| 变换函数   | 齐次矩阵 (3x3)                        | 参数     |
|-----------|---------------------------------------|----------|
| translate | [1, 0, tx, 0, 1, ty, 0, 0, 1]       | tx, ty   |
| rotate    | [cos, -sin, 0, sin, cos, 0, 0, 0, 1] | angle    |
| scale     | [sx, 0, 0, 0, sy, 0, 0, 0, 1]       | sx, sy   |
```

绕某点旋转的标准实现：

```javascript
ctx.translate(cx, cy);
ctx.rotate(angle);
ctx.translate(-cx, -cy);
```

### 6.1.2 setTransform / resetTransform 的绝对设置

save/restore 是栈式管理，setTransform 直接设置矩阵：

```javascript
ctx.setTransform(1, 0, 0, 1, 0, 0);  // 重置
const dpr = window.devicePixelRatio || 1;
ctx.setTransform(dpr, 0, 0, dpr, 0, 0);  // DPI 缩放
```

resetTransform 是 setTransform(1,0,0,1,0,0) 的语法糖。

```
| 特性     | save/restore       | setTransform       |
|---------|---------------------|--------------------|
| 管理方式 | 栈式 LIFO           | 绝对设置           |
| 保存范围 | 全部状态            | 仅变换矩阵         |
| 性能     | 栈操作+状态拷贝     | 极低               |
| 场景     | 复杂嵌套绘制        | 重置或已知最终状态  |
```

推荐：渲染循环开始用 setTransform 重置，循环内用 save/restore 管局部。

### 6.1.3 仿射变换矩阵 [a, b, c, d, e, f] 的含义

6 参数表示法对应 3x3 齐次矩阵：

```
| a c e |   |x|   | a*x+c*y+e |
| b d f | × |y| = | b*x+d*y+f |
| 0 0 1 |   |1|   |     1     |
```

各参数含义：

```
| 参数 | 含义       | 对应变换        |
|-----|------------|----------------|
| a   | 水平缩放    | scale 的 sx    |
| b   | 垂直倾斜    | rotate 的 sin  |
| c   | 水平倾斜    | rotate 的 -sin |
| d   | 垂直缩放    | scale 的 sy    |
| e   | 水平平移    | translate 的 tx|
| f   | 垂直平移    | translate 的 ty|
```

```javascript
const a = Math.PI / 4;
ctx.transform(Math.cos(a), Math.sin(a), -Math.sin(a), Math.cos(a), 0, 0);
// 等价 ctx.rotate(a)
```

> 理解 [a,b,c,d,e,f] 不是炫技，是为了性能敏感场景下减少变换调用次数。

Canvas 不支持透视变换，需透视效果请用 WebGL。

## 6.2 合成模式（Compositing）

合成模式决定新内容（source）如何与已有内容（destination）混合。

### 6.2.1 globalAlpha 与 globalCompositeOperation

```javascript
ctx.globalAlpha = 0.5;  // 全局透明度 0~1
ctx.globalCompositeOperation = 'source-over';  // 合成模式
```

globalAlpha 对后续所有绘制的 alpha 做乘法：

```javascript
ctx.globalAlpha = 0.5;
ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
ctx.fillRect(0, 0, 100, 100);  // 透明度 = 0.5 * 0.5 = 0.25
```

globalCompositeOperation 取值分两类：合成运算（基于 alpha 做逻辑运算）和混合模式（基于颜色通道做数学运算）。

### 6.2.2 Porter-Duff 合成运算族

Porter-Duff 运算由 Thomas Porter 和 Tom Duff 在 1984 年提出，定义了 12 种组合方式，是图像合成的基石。

```
| 运算名称          | 效果描述                            |
|------------------|-------------------------------------|
| source-over      | 新内容覆盖旧内容（默认）              |
| source-in        | 只保留重叠区域的新内容                |
| source-out       | 只保留不与旧内容重叠的新内容          |
| source-atop      | 新内容只出现在旧内容范围内            |
| destination-over | 旧内容覆盖新内容                     |
| destination-in   | 只保留重叠区域的旧内容                |
| destination-out  | 只保留不与新内容重叠的旧内容          |
| destination-atop | 旧内容只出现在新内容范围内            |
| xor              | 只保留不重叠的区域                   |
| lighter          | 重叠区域颜色值相加                   |
| copy             | 只保留新内容，完全替换旧内容          |
```

ASCII 图解：

```
source-over              destination-over
  [新在上]                  [旧在上]
  +---------+              +---------+
  | SOURCE  |              |  DEST   |
  |  over   |              |  over   |
  |  DEST   |              | SOURCE  |
  +---------+              +---------+

source-in               destination-out
  [只留交集S]              [扣掉交集D]
  +---------+              +---------+
  |   S∩D   |              | D - S∩D |
  +---------+              +---------+
```

工程中最常用的几个：

```javascript
// 橡皮擦
ctx.globalCompositeOperation = 'destination-out';
ctx.beginPath();
ctx.arc(50, 50, 20, 0, Math.PI * 2);
ctx.fill();

// 光晕叠加
ctx.globalCompositeOperation = 'lighter';
ctx.drawImage(glowLayer, 0, 0);
```

> destination-out 是橡皮擦，lighter 是发光体，这两个我用得最多。

切换合成模式触发状态切换，频繁切换时按模式分组绘制。

### 6.2.3 混合模式：multiply / screen / overlay 等

合成运算处理 alpha 通道去留，混合模式处理 RGB（Red Green Blue）通道混合。16 种：

```
| 模式        | 公式（Cs=源, Cb=背景）                 | 用途     |
|------------|----------------------------------------|---------|
| multiply   | Cs * Cb                                | 正片叠底 |
| screen     | Cs + Cb - Cs * Cb                      | 滤色     |
| overlay    | Cb<=0.5 ? 2*Cs*Cb : 1-2*(1-Cs)*(1-Cb) | 叠加     |
| darken     | min(Cs, Cb)                            | 取暗     |
| lighten    | max(Cs, Cb)                            | 取亮     |
| color-dodge| Cb / (1 - Cs)                          | 减淡     |
| color-burn | 1 - (1 - Cb) / Cs                      | 加深     |
| hard-light | Cs<=0.5 ? 2*Cs*Cb : 1-2*(1-Cs)*(1-Cb) | 强光     |
| difference | |Cs - Cb|                              | 差值     |
| exclusion  | Cs + Cb - 2*Cs*Cb                      | 排除     |
| hue        | H(Cs) S(Cb) L(Cb)                      | 色相     |
| saturation | H(Cb) S(Cs) L(Cb)                      | 饱和度   |
| color      | H(Cs) S(Cs) L(Cb)                      | 颜色     |
| luminosity | H(Cb) S(Cb) L(Cs)                      | 明度     |
```

hue/saturation/color/luminosity 在 HSL（Hue Saturation Lightness）空间运作。

```javascript
// 正片叠底
ctx.globalCompositeOperation = 'multiply';
ctx.fillStyle = 'rgba(0, 0, 255, 1)';
ctx.fillRect(0, 0, 100, 100);

// 差值模式反色
ctx.globalCompositeOperation = 'difference';
ctx.fillStyle = 'white';
ctx.fillRect(0, 0, 100, 100);
```

> 混合模式核心：用不同数学函数把两个颜色融合成一个。

混合模式和合成运算共用同一属性，不能同时用。需先混合再合成时用离屏 Canvas 分步处理。

### 6.2.4 source-over vs destination-over 的工程应用

destination-over 让新内容画在旧内容之下，经典场景：

```javascript
// 背景延后绘制
ctx.globalCompositeOperation = 'source-over';
ctx.drawImage(character, 0, 0);
ctx.globalCompositeOperation = 'destination-over';
ctx.drawImage(background, 0, 0);

// 阴影预绘制
ctx.fillStyle = 'red';
ctx.fillRect(50, 50, 100, 100);
ctx.globalCompositeOperation = 'destination-over';
ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
ctx.fillRect(40, 40, 120, 120);
```

避免额外离屏开销。

## 6.3 滤镜（Filter）

Canvas 2D 的 filter 属性与 CSS filter 完全一致。

### 6.3.1 ctx.filter 属性与 CSS filter 函数映射

```javascript
ctx.filter = 'blur(5px)';           // 高斯模糊
ctx.filter = 'brightness(1.5)';     // 亮度
ctx.filter = 'contrast(200%)';      // 对比度
ctx.filter = 'grayscale(100%)';     // 灰度
ctx.filter = 'hue-rotate(90deg)';   // 色相旋转
ctx.filter = 'invert(100%)';        // 反色
ctx.filter = 'saturate(200%)';      // 饱和度
ctx.filter = 'sepia(100%)';         // 棕褐色
ctx.filter = 'drop-shadow(4px 4px 5px rgba(0,0,0,0.5))';
ctx.filter = 'none';                // 清除
```

多个滤镜空格串联，按顺序应用：

```javascript
ctx.filter = 'blur(2px) brightness(1.2) contrast(1.1)';
ctx.drawImage(photo, 0, 0);
```

```
| 滤镜函数       | 参数      | 效果       |
|---------------|-----------|-----------|
| blur()        | px        | 高斯模糊   |
| brightness()  | 0~∞       | 亮度       |
| contrast()    | 0~∞       | 对比度     |
| grayscale()   | 0~100%    | 灰度       |
| hue-rotate()  | deg       | 色相旋转   |
| invert()      | 0~100%    | 反色       |
| opacity()     | 0~100%    | 透明度     |
| saturate()    | 0~∞       | 饱和度     |
| sepia()       | 0~100%    | 棕褐色     |
| drop-shadow() | off+blur+c| 投影      |
```

> filter 兼容性比合成模式差，Safari 14.0 才支持。

filter 让浏览器做额外 GPU pass，实时动画叠加多滤镜会拖慢帧率，建议离屏预渲染。

### 6.3.2 模糊、锐化、色彩调整

Canvas filter 有 blur() 无 sharpen()，锐化需通过卷积核实现。

```javascript
// 基础模糊
ctx.filter = 'blur(3px)';
ctx.drawImage(img, 0, 0);

// 复古色调
ctx.filter = 'saturate(0.7) sepia(0.3) contrast(0.9)';
ctx.drawImage(img, 0, 0);

// 高对比黑白
ctx.filter = 'grayscale(1) contrast(1.4) brightness(1.1)';
ctx.drawImage(img, 0, 0);

// 梦幻柔焦
ctx.filter = 'blur(1px) brightness(1.15) saturate(0.85)';
ctx.drawImage(img, 0, 0);
```

常用 3x3 锐化核，中心 5 四邻 -1，总和 1 保持亮度：

```
|  0  -1   0 |
| -1   5  -1 |
|  0  -1   0 |
```

### 6.3.3 自定义卷积核（通过 ImageData 实现）

Canvas filter 不支持自定义卷积核，但可通过 ImageData 实现。卷积核心：对每个像素用核覆盖其邻域做加权求和。

```javascript
/**
 * 3x3 卷积
 * @param {ImageData} imageData 原始图像数据
 * @param {number[]} kernel 3x3 核，长度 9
 * @returns {ImageData} 卷积后图像
 */
function convolve3x3(imageData, kernel) {
  const { width: w, height: h, data: src } = imageData;
  const output = new ImageData(w, h);
  const dst = output.data;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      let r = 0, g = 0, b = 0;
      for (let ky = -1; ky <= 1; ky++) {
        for (let kx = -1; kx <= 1; kx++) {
          const idx = ((y + ky) * w + (x + kx)) * 4;
          const wt = kernel[(ky + 1) * 3 + (kx + 1)];
          r += src[idx]     * wt;
          g += src[idx + 1] * wt;
          b += src[idx + 2] * wt;
        }
      }
      const di = (y * w + x) * 4;
      dst[di]     = Math.min(255, Math.max(0, r));
      dst[di + 1] = Math.min(255, Math.max(0, g));
      dst[di + 2] = Math.min(255, Math.max(0, b));
      dst[di + 3] = src[di + 3];  // 保留 alpha
    }
  }
  return output;
}

// 常用核
const sharpen = [0,-1,0, -1,5,-1, 0,-1,0];   // 锐化
const sobelX  = [-1,0,1, -2,0,2, -1,0,1];    // 水平边缘
const emboss  = [-2,-1,0, -1,1,1, 0,1,2];    // 浮雕

// 使用
const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
ctx.putImageData(convolve3x3(imgData, sharpen), 0, 0);
```

可优化：边界处理（镜像或补零）、性能（1000x1000 约 30-50ms）。高级方案是可分离卷积（Separable Convolution），2D 核分解为两个 1D 核，复杂度从 O(n²k²) 降为 O(n²·2k)。

```
| 卷积核     | 核矩阵                    | 效果     |
|-----------|---------------------------|---------|
| 锐化      | [0,-1,0, -1,5,-1, 0,-1,0]| 增强边缘 |
| Laplacian | [0,-1,0, -1,4,-1, 0,-1,0]| 检测边缘 |
| Sobel-X   | [-1,0,1, -2,0,2, -1,0,1] | 水平边缘 |
| Sobel-Y   | [-1,-2,-1, 0,0,0, 1,2,1] | 垂直边缘 |
| 浮雕      | [-2,-1,0, -1,1,1, 0,1,2] | 浮雕     |
| 高斯近似  | [1,2,1, 2,4,2, 1,2,1]/16 | 模糊     |
```

> 简单高斯模糊优先用 ctx.filter='blur()'，GPU 加速远超 JS 卷积。自定义核只在边缘检测等特殊效果时用。

## 本章小结

坐标变换核心是矩阵复合的右乘规则和 6 参数表示。合成模式区分 12 种 Porter-Duff 运算和 16 种混合模式。滤镜区分内置 CSS 滤镜和自定义卷积核。

三者执行顺序：先变换确定坐标，再绘制生成像素，最后合成和滤镜输出。

Porter-Duff 合成运算全图解：

```
| 运算              | S区 | S∩D | D区 | 说明          |
|-------------------|-----|------|------|---------------|
| source-over       | S   | S    | D    | 默认新覆盖旧   |
| source-in         | -   | S    | -    | 只留交集新     |
| source-out        | S   | -    | -    | 只留非交集新   |
| source-atop       | -   | S    | D    | 新限制在旧范围 |
| destination-over  | S   | D    | D    | 旧覆盖新       |
| destination-in    | -   | D    | -    | 只留交集旧     |
| destination-out   | -   | -    | D    | 扣掉交集旧     |
| destination-atop  | S   | D    | -    | 旧限制在新范围 |
| xor               | S   | -    | D    | 只留非交集     |
| lighter           | S   | S+D  | D    | 叠加变亮       |
| copy              | S   | S    | -    | 完全替换       |
```

仿射参数表见 6.1.3，混合公式表见 6.2.3。建议收藏。

---

系列进度：第6章 / 共17章 | ████████████░░░░░░░░░░ 35%

下一章预告：第7章"图层系统"——深入离屏渲染，讨论 OffscreenCanvas、多层叠加、脏区域重绘。

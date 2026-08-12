---
sidebar_position: 11
---

# 第11章 WebGL 基础：从 GLSL 到第一个三角形

WebGL 学了三遍还是不会画三角形？

不是因为你不努力，是因为大部分教程的顺序反了。它们先讲 GLSL（OpenGL Shading Language）语法，再讲缓冲区，再讲纹理，最后才画三角形——你学到最后已经忘了前面。

我是怕浪猫，这一章反过来：先画一个三角形，再逐步深入。看到结果再理解原理，效率翻倍。

## 11.1 WebGL 是什么

### 11.1.1 OpenGL ES 在浏览器中的映射

WebGL 本质上是 OpenGL ES（Open Graphics Library for Embedded Systems，嵌入式版开放图形库）2.0 的浏览器绑定。它通过 JavaScript API 暴露 GPU 的能力，让你能用着色器编程控制渲染管线。

```
你的 JavaScript 代码
    │
    ▼
WebGL JavaScript API（gl.drawArrays 等）
    │
    ▼
浏览器驱动层（翻译为 GPU 指令）
    │
    ▼
GPU 硬件执行
    │
    ▼
屏幕像素
```

WebGL 不是一个新的图形 API，它是 OpenGL ES 的 Web 版。如果你有 OpenGL 经验，WebGL 的概念会很熟悉。如果没有，也不影响——我们从零开始。

### 11.1.2 WebGL 1.0 vs WebGL 2.0 的差异

| 特性 | WebGL 1.0 | WebGL 2.0 |
|------|-----------|-----------|
| OpenGL 版本 | OpenGL ES 2.0 | OpenGL ES 3.0 |
| GLSL 版本 | GLSL ES 1.0 | GLSL ES 3.0 |
| 实例化渲染 | 需要扩展 | 原生支持 |
| Transform Feedback | 不支持 | 支持 |
| 3D 纹理 | 需要扩展 | 原生支持 |
| Uniform Buffer | 不支持 | 支持 |
| VAO（Vertex Array Object） | 需要扩展 | 原生支持 |
| 浏览器支持 | 全部主流浏览器 | 全部主流浏览器（IE 除外） |

WebGL 2.0 向后兼容 WebGL 1.0。获取上下文时的区别：

```javascript
const gl = canvas.getContext('webgl');    // 优先获取 WebGL 2.0
// 或
const gl = canvas.getContext('webgl2');   // 明确要求 WebGL 2.0

// 兼容性检查
if (!gl) {
  if (!canvas.getContext('webgl')) {
    console.error('WebGL not supported');
  }
}
```

### 11.1.3 WebGL 上下文获取与上下文丢失处理

```javascript
const canvas = document.querySelector('canvas');
const gl = canvas.getContext('webgl', {
  alpha: true,              // 画布是否有 alpha 通道
  antialias: true,          // 抗锯齿
  depth: true,              // 深度缓冲
  stencil: false,           // 模板缓冲
  premultipliedAlpha: true, // 预乘 alpha
  preserveDrawingBuffer: false, // 绘图后是否保留缓冲区
  powerPreference: 'high-performance', // GPU 偏好
});

// 上下文丢失处理
canvas.addEventListener('webglcontextlost', (e) => {
  e.preventDefault();
  stopRendering();
});

canvas.addEventListener('webglcontextrestored', () => {
  initResources();  // 重新创建所有 GPU 资源
  startRendering();
});
```

> 金句：WebGL 上下文的选项在创建时一次性设定，之后不能修改——选错参数只能重新创建上下文。

## 11.2 着色器（Shader）

### 11.2.1 GLSL 语法精要

GLSL（OpenGL Shading Language）是 C 语言风格的着色器编程语言。核心语法：

**变量类型**：

| 类型 | 说明 | 示例 |
|------|------|------|
| float | 单精度浮点 | `float a = 1.0;` |
| int | 整数 | `int b = 1;` |
| bool | 布尔 | `bool c = true;` |
| vec2/vec3/vec4 | 2/3/4 维向量 | `vec3 color = vec3(1.0, 0.0, 0.0);` |
| mat2/mat3/mat4 | 2/3/4 阶矩阵 | `mat4 mvp = mat4(1.0);` |
| sampler2D | 2D 纹理采样器 | `uniform sampler2D tex;` |

**限定符**：

| 限定符 | 说明 | 存储在 |
|--------|------|--------|
| attribute | 顶点着色器输入（每顶点不同） | VBO |
| uniform | 全局常量（所有顶点/片元相同） | Uniform 变量 |
| varying | 顶点→片元传递（自动插值） | 光栅化器 |
| const | 编译时常量 | 编译期 |

**GLSL ES 1.0 vs 3.0 关键差异**：

```glsl
// GLSL ES 1.0（WebGL 1.0）
attribute vec3 aPosition;
varying vec3 vColor;
gl_FragColor = vec4(color, 1.0);

// GLSL ES 3.0（WebGL 2.0）
in vec3 aPosition;        // attribute → in
out vec3 vColor;          // varying → out (vertex) / in (fragment)
out vec4 fragColor;       // 自定义输出替代 gl_FragColor
fragColor = vec4(color, 1.0);
```

### 11.2.2 顶点着色器编写

顶点着色器对每个顶点执行一次，核心职责是计算 `gl_Position`：

```glsl
// 顶点着色器：带变换矩阵和颜色传递
attribute vec3 aPosition;   // 顶点位置
attribute vec3 aColor;      // 顶点颜色
uniform mat4 uModelMatrix;  // 模型矩阵
uniform mat4 uViewMatrix;   // 视图矩阵
uniform mat4 uProjMatrix;   // 投影矩阵

varying vec3 vColor;        // 传递给片元着色器

void main() {
  // 计算裁剪空间坐标
  gl_Position = uProjMatrix * uViewMatrix * uModelMatrix * vec4(aPosition, 1.0);
  vColor = aColor;
}
```

### 11.2.3 片元着色器编写

片元着色器对每个片元执行一次，核心职责是计算最终颜色：

```glsl
// 片元着色器：简单颜色输出
precision mediump float;    // 设置浮点精度
varying vec3 vColor;        // 从顶点着色器传来的颜色（已插值）

void main() {
  gl_FragColor = vec4(vColor, 1.0);
}
```

浮点精度声明：

| 精度 | 关键字 | 范围 | 适用场景 |
|------|--------|------|---------|
| 高精度 | highp | 32 位 | 顶点位置计算 |
| 中精度 | mediump | 16 位 | 颜色、UV 坐标 |
| 低精度 | lowp | 8 位 | 简单颜色运算 |

> 金句：片元着色器必须声明浮点精度——忘了这一行，你的着色器编译直接报错，而且报错信息还看不出原因。

### 11.2.4 着色器编译、链接与程序对象

着色器从源码到可执行需要经过编译和链接，这个过程和 C 语言编译类似：

```javascript
// 1. 创建着色器对象
const vertexShader = gl.createShader(gl.VERTEX_SHADER);
const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);

// 2. 上传源码
gl.shaderSource(vertexShader, vertexShaderSource);
gl.shaderSource(fragmentShader, fragmentShaderSource);

// 3. 编译
gl.compileShader(vertexShader);
gl.compileShader(fragmentShader);

// 4. 检查编译错误
if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS)) {
  console.error('顶点着色器编译失败：', gl.getShaderInfoLog(vertexShader));
}

// 5. 创建程序对象
const program = gl.createProgram();

// 6. 附加着色器
gl.attachShader(program, vertexShader);
gl.attachShader(program, fragmentShader);

// 7. 链接
gl.linkProgram(program);

// 8. 检查链接错误
if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
  console.error('程序链接失败：', gl.getProgramInfoLog(program));
}

// 9. 使用程序
gl.useProgram(program);
```

**编译链接流程图**：

```
源码字符串
    │
    ├──→ createShader() → shaderSource() → compileShader()
    │                                        │
    │                                    编译后的着色器
    │                                        │
    └──→ createProgram() → attachShader() → linkProgram() → useProgram()
                                                         │
                                                    可执行的 GPU 程序
```

## 11.3 缓冲区与纹理

### 11.3.1 VBO 与顶点属性

VBO（Vertex Buffer Object，顶点缓冲对象）是 GPU 内存中的一块区域，用于存储顶点数据。

```javascript
// 1. 创建缓冲区
const vbo = gl.createBuffer();

// 2. 绑定缓冲区（指定类型）
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);

// 3. 上传数据
const vertices = new Float32Array([
  -0.5, -0.5, 0.0,   // 顶点 1
   0.5, -0.5, 0.0,   // 顶点 2
   0.0,  0.5, 0.0,   // 顶点 3
]);
gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

// 4. 配置顶点属性（告诉 GPU 如何读取数据）
const aPosition = gl.getAttribLocation(program, 'aPosition');
gl.enableVertexAttribArray(aPosition);
gl.vertexAttribPointer(
  aPosition,    // 属性位置
  3,            // 每个顶点的分量数（x, y, z）
  gl.FLOAT,     // 数据类型
  false,        // 是否归一化
  3 * 4,        // 步幅（每个顶点 3 个 float × 4 字节）
  0             // 偏移量
);
```

**顶点属性的内存布局**：

```
Float32Array 内存布局：
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│  -0.5│  -0.5│   0.0│   0.5│  -0.5│   0.0│   0.0│   0.5│   0.0│
├──────┴──────┴──────┼──────┴──────┴──────┼──────┴──────┴──────┤
│    顶点 0          │    顶点 1          │    顶点 2          │
│  stride = 12 字节  │  stride = 12 字节  │  stride = 12 字节  │
└────────────────────┴────────────────────┴────────────────────┘
offset = 0
```

### 11.3.2 IBO 与索引绘制

IBO（Index Buffer Object，索引缓冲对象）存储顶点索引，避免重复定义共享顶点：

```javascript
// 一个矩形 = 2 个三角形 = 6 个顶点
// 但实际上只有 4 个不同的顶点
const vertices = new Float32Array([
  -0.5, -0.5,  // 左下
   0.5, -0.5,  // 右下
   0.5,  0.5,  // 右上
  -0.5,  0.5,  // 左上
]);

// 索引：定义两个三角形如何使用这 4 个顶点
const indices = new Uint16Array([
  0, 1, 2,  // 三角形 1：左下→右下→右上
  0, 2, 3,  // 三角形 2：左下→右上→左上
]);

const ibo = gl.createBuffer();
gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo);
gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);

// 使用索引绘制
gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
```

### 11.3.3 纹理对象与采样器

纹理是 GPU 中的图像数据，通过采样器（Sampler）在着色器中读取：

```javascript
// 1. 创建纹理
const texture = gl.createTexture();

// 2. 绑定纹理
gl.bindTexture(gl.TEXTURE_2D, texture);

// 3. 上传图像数据
const image = new Image();
image.onload = () => {
  gl.texImage2D(
    gl.TEXTURE_2D,    // 目标
    0,                // mipmap 层级
    gl.RGBA,          // 内部格式
    gl.RGBA,          // 上传格式
    gl.UNSIGNED_BYTE, // 数据类型
    image             // 图像源
  );
  
  // 4. 设置纹理参数
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
};
image.src = 'texture.png';
```

```glsl
// 片元着色器中使用纹理
precision mediump float;
uniform sampler2D uTexture;
varying vec2 vTexCoord;

void main() {
  gl_FragColor = texture2D(uTexture, vTexCoord);
}
```

### 11.3.4 纹理过滤：最近邻 vs 线性 vs Mipmap

当纹理被缩放显示时，需要选择过滤方式：

| 过滤方式 | 参数 | 效果 | 性能 |
|---------|------|------|------|
| 最近邻 | NEAREST | 像素化、锐利 | 最快 |
| 双线性 | LINEAR | 平滑、模糊 | 中等 |
| Mipmap | LINEAR_MIPMAP_LINEAR | 远距离清晰 | 需要额外内存 |

```
最近邻 (NEAREST)：          线性 (LINEAR)：
┌──┬──┬──┐                  ┌────┬────┬────┐
│■│  │■│  │                 │▓▓│▒▒│▓▓│▒▒│   每个目标像素
├──┼──┼──┼──┤                ├────┼────┼────┤    取最近源像素
│  │■│  │  │                 │▒▒│▓▓│▒▒│▓▓│    vs
├──┼──┼──┼──┤                ├────┼────┼────┤    取周围 4 个像素
│■│  │■│  │                 │▓▓│▒▒│▓▓│▒▒│    加权平均
└──┴──┴──┘                  └────┴────┴────┘
```

### 11.3.5 纹理包装模式

当 UV 坐标超出 [0, 1] 范围时的处理方式：

| 模式 | 参数 | 效果 |
|------|------|------|
| 重复 | REPEAT | 纹理重复平铺 |
| 镜像重复 | MIRRORED_REPEAT | 纹理镜像翻转后重复 |
| 边缘截断 | CLAMP_TO_EDGE | 超出部分使用边缘像素颜色 |

```
REPEAT:          MIRRORED_REPEAT:    CLAMP_TO_EDGE:
┌──┬──┬──┐      ┌──┬──┬──┐         ┌──┬──┬──┐
│A │A │A │      │A │A'│A │         │A │A │A │
├──┼──┼──┤      ├──┼──┼──┤         ├──┼──┼──┤
│A │A │A │      │A'│A │A'│         │A │A │A │
└──┴──┴──┘      └──┴──┴──┘         └──┴──┴──┘
(A' = 镜像)                        (边缘延伸)
```

## 11.4 第一个三角形：完整 WebGL 渲染流程

把前面学的所有知识串起来，画一个彩色三角形：

```javascript
// ============ 1. 初始化 WebGL ============
const canvas = document.querySelector('canvas');
const gl = canvas.getContext('webgl');

// ============ 2. 编写着色器 ============
const vertexShaderSource = `
  attribute vec3 aPosition;
  attribute vec3 aColor;
  varying vec3 vColor;
  
  void main() {
    gl_Position = vec4(aPosition, 1.0);
    vColor = aColor;
  }
`;

const fragmentShaderSource = `
  precision mediump float;
  varying vec3 vColor;
  
  void main() {
    gl_FragColor = vec4(vColor, 1.0);
  }
`;

// ============ 3. 编译着色器 ============
function createShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);

// ============ 4. 创建程序 ============
const program = gl.createProgram();
gl.attachShader(program, vertexShader);
gl.attachShader(program, fragmentShader);
gl.linkProgram(program);
gl.useProgram(program);

// ============ 5. 准备顶点数据 ============
const vertices = new Float32Array([
  // 位置          // 颜色
   0.0,  0.5, 0.0,  1.0, 0.0, 0.0,  // 顶部 - 红
  -0.5, -0.5, 0.0,  0.0, 1.0, 0.0,  // 左下 - 绿
   0.5, -0.5, 0.0,  0.0, 0.0, 1.0,  // 右下 - 蓝
]);

const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

// ============ 6. 配置顶点属性 ============
const aPosition = gl.getAttribLocation(program, 'aPosition');
const aColor = gl.getAttribLocation(program, 'aColor');

const stride = 6 * 4;  // 每顶点 6 个 float × 4 字节
gl.enableVertexAttribArray(aPosition);
gl.vertexAttribPointer(aPosition, 3, gl.FLOAT, false, stride, 0);

gl.enableVertexAttribArray(aColor);
gl.vertexAttribPointer(aColor, 3, gl.FLOAT, false, stride, 3 * 4);

// ============ 7. 渲染 ============
gl.clearColor(0.0, 0.0, 0.0, 1.0);  // 清屏色：黑色
gl.clear(gl.COLOR_BUFFER_BIT);
gl.drawArrays(gl.TRIANGLES, 0, 3);   // 画三角形
```

**渲染 5 步法总结**：

```
Step 1: 初始化 → getContext('webgl')
Step 2: 着色器 → 编写 + 编译 + 链接 → Program
Step 3: 数据 → VBO 上传顶点数据
Step 4: 属性 → vertexAttribPointer 配置读取方式
Step 5: 绘制 → clear + drawArrays/drawElements
```

> 金句：WebGL 画三角形要 100 行代码，但这是所有 3D 渲染的原点——Three.js 内部做的也是同样的事。

## 11.5 WebGL 状态机模型

### 11.5.1 WebGL 的全局状态集

WebGL 是一个巨大的状态机。你设置的每个状态都会一直保持，直到被修改。

```
WebGL 全局状态（部分）：
┌─────────────────────────────────────────┐
│ 当前程序 (Program)                        │
│ 当前 VBO 绑定 (ARRAY_BUFFER)              │
│ 当前 IBO 绑定 (ELEMENT_ARRAY_BUFFER)      │
│ 当前纹理绑定 (TEXTURE_2D)                  │
│ 视口大小 (Viewport)                       │
│ 清屏色 (Clear Color)                      │
│ 深度测试 (Enable/Disable)                 │
│ 混合模式 (Blend Func)                     │
│ 面剔除 (Cull Face)                        │
│ ... 共约 50+ 个状态                       │
└─────────────────────────────────────────┘
```

### 11.5.2 状态切换的性能成本

每次状态切换都有开销，不同状态的成本不同：

| 状态切换 | 成本 | 说明 |
|---------|------|------|
| 纹理绑定 | 中 | 可能触发 GPU 纹理缓存未命中 |
| 着色器切换 | 高 | 需要重新编译/验证管线 |
| VBO 绑定 | 低 | 只是改指针 |
| 混合模式切换 | 低 | 改少量寄存器 |
| Enable/Disable | 低 | 改标志位 |

### 11.5.3 状态排序优化

减少状态切换的核心策略是**状态排序**——按状态分组绘制：

```javascript
// 差的做法：每个对象独立设置状态
objects.forEach(obj => {
  gl.useProgram(obj.program);      // 切换程序
  gl.bindTexture(gl.TEXTURE_2D, obj.texture);  // 切换纹理
  gl.uniformMatrix4fv(obj.mvpLoc, false, obj.mvp);
  gl.drawArrays(gl.TRIANGLES, 0, obj.vertexCount);
});

// 好的做法：按程序和纹理分组
const groups = groupBy(objects, ['program', 'texture']);
groups.forEach(group => {
  gl.useProgram(group.program);    // 只切换一次
  gl.bindTexture(gl.TEXTURE_2D, group.texture);  // 只切换一次
  group.objects.forEach(obj => {
    gl.uniformMatrix4fv(obj.mvpLoc, false, obj.mvp);  // 只改 MVP
    gl.drawArrays(gl.TRIANGLES, 0, obj.vertexCount);
  });
});
```

> 金句：WebGL 性能优化的核心不是"画得快"，而是"少切换"——每一次状态切换都是 GPU 管线的停顿。

## 11.6 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| WebGL 本质 | OpenGL ES 2.0 的浏览器绑定 |
| 着色器语言 | GLSL，C 风格，分顶点和片元两种 |
| 编译流程 | createShader → compile → createProgram → link → use |
| VBO | GPU 内存中的顶点数据缓冲区 |
| IBO | 索引缓冲区，避免重复顶点 |
| 纹理过滤 | NEAREST（像素化）/ LINEAR（平滑）/ MIPMAP（远距离清晰） |
| 纹理包装 | REPEAT / MIRRORED_REPEAT / CLAMP_TO_EDGE |
| 渲染 5 步法 | 初始化 → 着色器 → 数据 → 属性 → 绘制 |
| 状态机 | WebGL 是全局状态机，状态切换有成本 |
| 状态排序 | 按程序/纹理分组绘制，减少切换 |

觉得有用？收藏起来，这是 WebGL 的入门基石。

你学 WebGL 卡在哪一步？评论区说说，怕浪猫帮你疏通。

关注怕浪猫，下期我们讲 **WebGL 进阶**——深度缓冲、光照实战、FBO 离屏渲染和性能优化。

系列进度 11/17

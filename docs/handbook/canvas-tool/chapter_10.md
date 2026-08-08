# 第10章 3D 渲染管线总论：GPU 管线、坐标变换与光照模型

你以为 3D 渲染很神秘？说白了就是 4 个矩阵乘法加一次光栅化。

当然，实际细节远比这复杂。但核心思路确实不神秘——把 3D 模型的顶点经过一系列坐标变换映射到 2D 屏幕上，再决定每个像素的颜色。理解了这条管线，Three.js 和 Babylon.js 的源码就不再是天书。

我是怕浪猫，从这一章开始进入 3D 渲染的世界。这一章是总论——先建立全景认知，后面三章再分别深入 WebGL 基础、WebGL 进阶和 WebGPU。

## 10.1 为什么 Canvas 2D 无法做真正的 3D

### 10.1.1 2D 上下文的局限：无深度缓冲、无着色器

Canvas 2D 上下文在设计上就是为 2D 位图绘制服务的。它缺乏 3D 渲染所需的两个核心能力：

**无深度缓冲（Depth Buffer）**：2D 上下文只有一块 RGBA 像素缓冲区，没有深度信息。这意味着后画的图形总是覆盖先画的图形（painter's algorithm），你无法让一个"远处"的物体被"近处"的物体正确遮挡——除非你手动对图元排序。

```javascript
// 2D Canvas 中模拟 3D 排序
const triangles = [
  { vertices: [...], z: 0.9 },  // 远
  { vertices: [...], z: 0.1 },  // 近
];

// 必须手动按 Z 排序，远的先画
triangles.sort((a, b) => b.z - a.z);
triangles.forEach(t => drawTriangle(t));
```

这种手动排序在面对交叉面（两个三角形互相穿插）时会彻底失败——无论怎么排序都是错的。

**无着色器（Shader）**：2D 上下文的绘制逻辑是固定的（固定功能管线），你无法自定义"每个像素的颜色怎么算"。3D 渲染需要逐顶点光照计算、逐片元纹理采样、法线贴图等，这些都需要可编程着色器。

### 10.1.2 用 2D 模拟 3D 的方法与天花板

虽然 2D 上下文无法做真正的 3D，但可以通过数学手段模拟简单的 3D 效果：

```javascript
// 3D 点投影到 2D 屏幕
function project3D(point, camera, fov, width, height) {
  // 相对相机的坐标
  const dx = point.x - camera.x;
  const dy = point.y - camera.y;
  const dz = point.z - camera.z;
  
  // 透视投影
  const scale = fov / (fov + dz);
  
  return {
    x: width / 2 + dx * scale,
    y: height / 2 - dy * scale,
    scale: scale  // 用于后续的大小/深度排序
  };
}

// 画一个旋转的立方体
const cube = {
  vertices: [
    {x:-1,y:-1,z:-1}, {x:1,y:-1,z:-1}, {x:1,y:1,z:-1}, {x:-1,y:1,z:-1},
    {x:-1,y:-1,z:1}, {x:1,y:-1,z:1}, {x:1,y:1,z:1}, {x:-1,y:1,z:1}
  ],
  faces: [
    [0,1,2,3], [4,5,6,7], [0,1,5,4], [2,3,7,6], [0,3,7,4], [1,2,6,5]
  ]
};
```

> 金句：用 2D Canvas 模拟 3D，就像用铅笔画画油画——能画出形状，但画不出质感。

这种方法的天花板：
- 无法处理交叉面的正确遮挡
- 无法做逐像素光照（只能用平面着色，每个面一个颜色）
- 无法做纹理映射（只能用纯色或简单渐变）
- 大量图元时性能极差（纯 CPU 计算）

所以，真正的 3D 渲染必须用 WebGL 或 WebGPU。

## 10.2 GPU 渲染管线全景图

GPU 渲染管线描述了从 3D 模型数据到屏幕像素的完整流程。这条管线分为三个大阶段。

```
┌──────────────────────────────────────────────────────┐
│                  GPU 渲染管线全景                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 应用阶段 (CPU 侧)                                 │
│     ├── 准备顶点数据                                   │
│     ├── 设置渲染状态                                   │
│     └── 发出 Draw Call                                │
│                                                      │
│  2. 几何阶段 (GPU 顶点处理)                            │
│     ├── 顶点着色器 (Vertex Shader)                     │
│     ├── 图元装配 (Primitive Assembly)                  │
│     ├── 几何着色器 (Geometry Shader, 可选)              │
│     └── 裁剪与视口变换 (Clipping + Viewport Transform) │
│                                                      │
│  3. 光栅化阶段 (GPU 片元处理)                          │
│     ├── 三角形设置 (Triangle Setup)                    │
│     ├── 三角形遍历 (Triangle Traversal)                │
│     ├── 片元着色器 (Fragment Shader)                   │
│     └── 逐片元操作 (Per-Fragment Operations)           │
│         ├── 深度测试 (Depth Test)                      │
│         ├── 模板测试 (Stencil Test)                    │
│         ├── 混合 (Blending)                           │
│         └── 写入帧缓冲 (Write Framebuffer)             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 10.2.1 应用阶段（CPU 侧）：准备几何数据与 Draw Call

应用阶段在你的 JavaScript 代码中执行。主要工作：

```javascript
// 1. 准备顶点数据
const vertices = new Float32Array([
  // x, y, z, r, g, b
  -0.5, -0.5, 0.0,  1.0, 0.0, 0.0,
   0.5, -0.5, 0.0,  0.0, 1.0, 0.0,
   0.0,  0.5, 0.0,  0.0, 0.0, 1.0,
]);

// 2. 上传到 GPU 缓冲区
const buffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

// 3. 设置渲染状态（着色器程序、uniform 变量等）
gl.useProgram(program);
gl.uniformMatrix4fv(mvpLocation, false, mvpMatrix);

// 4. 发出 Draw Call
gl.drawArrays(gl.TRIANGLES, 0, 3);
```

Draw Call 是 CPU 发给 GPU 的绘制命令。每次 Draw Call 都有 CPU 开销（状态验证、驱动层翻译），所以减少 Draw Call 数量是 3D 性能优化的核心。

### 10.2.2 几何阶段（Vertex Processing）

**顶点着色器（Vertex Shader）**：对每个顶点执行一次，主要职责是计算顶点的最终位置。

```glsl
// GLSL 顶点着色器示例
attribute vec3 aPosition;    // 输入：顶点位置
attribute vec3 aColor;       // 输入：顶点颜色
uniform mat4 uMVPMatrix;     // 输入：模型-视图-投影矩阵

varying vec3 vColor;         // 输出：传递给片元着色器的颜色

void main() {
  gl_Position = uMVPMatrix * vec4(aPosition, 1.0);  // 计算裁剪空间坐标
  vColor = aColor;  // 传递颜色
}
```

顶点着色器的输入输出：

| 类型 | 说明 | 示例 |
|------|------|------|
| attribute | 每顶点输入数据 | 位置、法线、颜色、UV 坐标 |
| uniform | 全局常量（所有顶点共享） | 变换矩阵、光源位置 |
| varying | 输出到片元着色器（会被插值） | 颜色、UV、法线 |
| gl_Position | 内置输出：裁剪空间坐标 | vec4(x, y, z, w) |

**图元装配（Primitive Assembly）**：将顶点着色器输出的顶点组装成图元。图元类型由 Draw Call 指定：

| 图元类型 | 说明 | 顶点数 |
|---------|------|--------|
| POINTS | 点 | 每 1 个顶点一个图元 |
| LINES | 线段 | 每 2 个顶点一条线 |
| TRIANGLES | 三角形 | 每 3 个顶点一个三角形 |
| TRIANGLE_STRIP | 三角带 | 3 个顶点起，每增加 1 个顶点产生 1 个三角形 |
| TRIANGLE_FAN | 三角扇 | 3 个顶点起，每增加 1 个顶点产生 1 个三角形 |

**裁剪（Clipping）与视口变换（Viewport Transform）**：

裁剪阶段剔除完全在视锥外的图元，裁剪部分在视锥内的图元。然后进行透视除法（齐次坐标 → 归一化设备坐标）和视口变换（归一化坐标 → 屏幕像素坐标）。

```
裁剪空间坐标 (x, y, z, w)
    │
    │ 透视除法：x/w, y/w, z/w
    ▼
归一化设备坐标 NDC (x, y, z)  范围 [-1, 1]
    │
    │ 视口变换
    ▼
屏幕坐标 (px, py) + 深度值 z
```

### 10.2.3 光栅化阶段（Rasterization）

**三角形遍历与片元生成**：

光栅化器将图元（通常是三角形）转换为片元（Fragment）。片元可以理解为"候选像素"——它包含了位置、深度、插值后的顶点属性等信息，但还不是最终的像素。

```
三角形顶点：                光栅化后的片元：
  v0 ────────── v1          ■ ■ ■ ■ ■
  │            /            ■ ■ ■ ■
  │          /              ■ ■ ■
  │        /                ■ ■
  v2 ────                   ■
```

光栅化过程中，顶点属性（颜色、UV 坐标、法线等）会在三角形内部**线性插值**：

```glsl
// 如果 v0 颜色是红色, v1 是绿色, v2 是蓝色
// 则三角形内部的每个片元颜色是三个顶点颜色的加权平均
// 这个插值是自动完成的，由 varying 变量传递
```

**片元着色器（Fragment Shader）**：对每个片元执行一次，计算最终颜色。

```glsl
// GLSL 片元着色器示例
precision mediump float;
varying vec3 vColor;  // 从顶点着色器传来的颜色（已插值）

void main() {
  gl_FragColor = vec4(vColor, 1.0);  // 输出最终颜色
}
```

### 10.2.4 逐片元操作（Per-Fragment Operations）

片元着色器输出颜色后，还要经过一系列测试才能最终写入帧缓冲：

```
片元颜色
    │
    ▼
┌─────────────────┐
│ 深度测试 (Depth) │ ─── 比较片元深度与缓冲区深度，被遮挡则丢弃
└────────┬────────┘
         │ 通过
         ▼
┌─────────────────┐
│ 模板测试 (Stencil)│ ─── 基于模板缓冲区的掩码测试
└────────┬────────┘
         │ 通过
         ▼
┌─────────────────┐
│ 混合 (Blending)  │ ─── 与帧缓冲中已有颜色混合（半透明效果）
└────────┬────────┘
         │
         ▼
    写入帧缓冲
```

**深度测试（Depth Test）**：比较片元的 Z 值与深度缓冲区中对应位置的 Z 值。如果片元更近（Z 值更小，默认配置下），则通过测试，更新颜色和深度；否则丢弃片元。

这就是 3D 渲染能正确处理遮挡的原因——不需要手动排序，深度缓冲自动处理。

**模板测试（Stencil Test）**：基于模板缓冲区（一个额外的整数缓冲区）进行掩码操作。常见用途：镜面反射、轮廓描边、限制绘制区域。

**混合（Blending）**：将片元颜色与帧缓冲中已有颜色按 Alpha 值混合，实现半透明效果。

> 金句：深度测试是 3D 渲染的"自动遮挡处理器"——你不用排序，GPU 逐像素比远近。

## 10.3 坐标空间变换链

3D 渲染中最容易混淆的就是坐标空间。一个顶点从模型定义到最终显示在屏幕上，要经历多次坐标变换。

### 10.3.1 模型空间到世界空间

模型空间（Model Space）也叫局部空间（Local Space），是顶点在模型定义中的原始坐标。一个角色模型的顶点可能以角色脚底为原点定义。

世界空间（World Space）是场景的全局坐标系。多个模型放在同一个场景中，需要各自通过模型矩阵变换到世界空间。

```
模型空间                 世界空间
(角色局部坐标)            (场景全局坐标)
    │
    │  × 模型矩阵 (Model Matrix)
    │  包含：平移 + 旋转 + 缩放
    ▼
世界坐标
```

模型矩阵的构建：

```javascript
// M = T × R × S（先缩放，再旋转，最后平移）
function modelMatrix(translate, rotate, scale) {
  const T = mat4.create();
  mat4.translate(T, T, translate);
  
  const R = mat4.create();
  mat4.rotateX(R, R, rotate[0]);
  mat4.rotateY(R, R, rotate[1]);
  mat4.rotateZ(R, R, rotate[2]);
  
  const S = mat4.create();
  mat4.scale(S, S, scale);
  
  return mat4.multiply(mat4.create(), T, mat4.multiply(mat4.create(), R, S));
}
```

### 10.3.2 世界空间到观察空间

观察空间（View Space / Camera Space）是以相机为原点的坐标系。通过视图矩阵将世界坐标变换到观察空间。

```
世界空间                 观察空间
(场景全局坐标)            (相机视角坐标)
    │
    │  × 视图矩阵 (View Matrix)
    │  本质：相机的逆变换
    ▼
观察坐标
```

视图矩阵的构建：

```javascript
// 视图矩阵 = 相相机变换的逆矩阵
function viewMatrix(cameraPos, cameraTarget, cameraUp) {
  // 计算相机的三个坐标轴方向
  const forward = normalize(subtract(cameraTarget, cameraPos));  // Z 轴（朝向）
  const right = normalize(cross(forward, cameraUp));             // X 轴（右方）
  const up = cross(right, forward);                              // Y 轴（上方）
  
  // 视图矩阵 = 旋转^(-1) × 平移^(-1)
  return new Float32Array([
    right[0], up[0], -forward[0], 0,
    right[1], up[1], -forward[1], 0,
    right[2], up[2], -forward[2], 0,
    -dot(right, cameraPos), -dot(up, cameraPos), dot(forward, cameraPos), 1
  ]);
}
```

### 10.3.3 观察空间到裁剪空间

裁剪空间（Clip Space）是 GPU 进行裁剪判断的空间。通过投影矩阵将观察空间变换到裁剪空间。

```
观察空间                 裁剪空间
(相机视角坐标)            (GPU 裁剪用坐标)
    │
    │  × 投影矩阵 (Projection Matrix)
    │  透视投影 or 正交投影
    ▼
裁剪坐标 (x, y, z, w)
```

裁剪空间的坐标是齐次坐标 (x, y, z, w)。GPU 根据 w 分量进行裁剪：w > 0 的部分可见，w < 0 的部分在相机后面被裁剪。

### 10.3.4 裁剪空间到屏幕空间

```
裁剪空间                 NDC                  屏幕空间
(x, y, z, w)             (x, y, z)            (px, py, depth)
    │                       │                      │
    │ 透视除法               │ 视口变换               │
    │ x/w, y/w, z/w         │ 映射到像素坐标          │
    ▼                       ▼                      ▼
```

**透视除法**：将齐次坐标除以 w 分量，得到归一化设备坐标（NDC，Normalized Device Coordinates），范围 [-1, 1]。

**视口变换**：将 NDC 映射到屏幕像素坐标：

```
px = (ndcX + 1) × width / 2 + x_offset
py = (1 - ndcY) × height / 2 + y_offset  // Y 翻转
depth = (ndcZ + 1) / 2  // 映射到 [0, 1]
```

### 10.3.5 透视投影与正交投影矩阵

**透视投影（Perspective Projection）**：模拟人眼，近大远小。

```javascript
// 透视投影矩阵
function perspective(fov, aspect, near, far) {
  const f = 1.0 / Math.tan(fov / 2);
  const nf = 1 / (near - far);
  
  return new Float32Array([
    f / aspect, 0, 0, 0,
    0, f, 0, 0,
    0, 0, (far + near) * nf, -1,
    0, 0, 2 * far * near * nf, 0
  ]);
}
// fov: 视野角度（Field of View）
// aspect: 宽高比（width / height）
// near: 近裁剪面距离
// far: 远裁剪面距离
```

**正交投影（Orthographic Projection）**：平行投影，无近大远小效果。

```javascript
// 正交投影矩阵
function orthographic(left, right, bottom, top, near, far) {
  const lr = 1 / (left - right);
  const bt = 1 / (bottom - top);
  const nf = 1 / (near - far);
  
  return new Float32Array([
    -2 * lr, 0, 0, 0,
    0, -2 * bt, 0, 0,
    0, 0, 2 * nf, 0,
    (left + right) * lr, (top + bottom) * bt, (far + near) * nf, 1
  ]);
}
```

| 对比 | 透视投影 | 正交投影 |
|------|---------|---------|
| 近大远小 | 是 | 否 |
| 平行线 | 会汇聚到消失点 | 保持平行 |
| 适用场景 | 3D 游戏、真实感渲染 | 2D 等距游戏、CAD、UI |

> 金句：整个 3D 渲染的坐标变换链可以用一个公式概括：`屏幕坐标 = Viewport × Projection × View × Model × 局部坐标`。

## 10.4 渲染方程与光照模型简述

### 10.4.1 局部光照模型：Phong / Blinn-Phong

**Phong 光照模型**由三个分量组成：

```
最终颜色 = 环境光(Ambient) + 漫反射(Diffuse) + 镜面反射(Specular)
```

```
                    法线 N
                    │
                    │
     光源 L         │           视线 V
      \            │            /
       \           │           /
        \  入射角  │  反射角  /
         \──θ─────│────θ───/
          \       │       /
           \      │      /
            \     │     /
             \    │    /
              \   │   /
               \  │  /
                \ │ /
                 \|/
              表面点 P
```

**环境光（Ambient）**：模拟间接光照（环境反射光），是一个常数：

```glsl
vec3 ambient = ambientStrength * lightColor;
```

**漫反射（Diffuse）**：光线 hitting 粗糙表面后向各方向均匀反射，亮度取决于光线与表面法线的夹角：

```glsl
vec3 norm = normalize(Normal);
vec3 lightDir = normalize(lightPos - FragPos);
float diff = max(dot(norm, lightDir), 0.0);
vec3 diffuse = diff * lightColor;
```

**镜面反射（Specular）**：光滑表面的高光，取决于反射光与视线的夹角：

```glsl
vec3 viewDir = normalize(viewPos - FragPos);
vec3 reflectDir = reflect(-lightDir, norm);
float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
vec3 specular = specularStrength * spec * lightColor;
```

**Blinn-Phong**是 Phong 的优化版本，用半角向量（Halfway Vector）替代反射向量，计算更高效且效果更自然：

```glsl
// Blinn-Phong
vec3 halfwayDir = normalize(lightDir + viewDir);
float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);
```

| 对比 | Phong | Blinn-Phong |
|------|-------|-------------|
| 高光计算 | 反射向量 · 视线 | 半角向量 · 法线 |
| 计算量 | 较大（reflect 计算） | 较小 |
| 高光效果 | 锐利 | 柔和 |
| shininess 值 | 通常 1-128 | 通常 1-512（约是 Phong 的 4 倍） |

### 10.4.2 全局光照概念：光线追踪 vs 光栅化

**光栅化（Rasterization）**：将 3D 三角形投影到 2D 屏幕，逐像素填色。这是 GPU 管线的标准方式，速度快但不计算间接光照。

**光线追踪（Ray Tracing）**：从屏幕像素出发，发射光线进入场景，计算光线与物体的交点，递归追踪反射和折射光线。效果逼真但计算量巨大。

```
光栅化：                    光线追踪：
模型 → 投影 → 像素           像素 → 发射光线 → 求交 → 光照
（正向）                     （逆向）
```

光栅化是实时渲染（游戏、WebGL）的主流方式。光线追踪主要用于离线渲染（电影），近年来 RTX 显卡开始支持实时光线追踪。

### 10.4.3 PBR 基础

PBR（Physically Based Rendering，基于物理的渲染）是现代 3D 引擎的标准光照模型。相比 Phong 模型，PBR 基于物理定律，能在不同光照条件下保持一致的真实感。

PBR 的两个核心概念：

**BRDF（Bidirectional Reflectance Distribution Function，双向反射分布函数）**：描述光线如何从入射方向反射到出射方向。最常用的 PBR BRDF 是 Cook-Torrance 模型：

```
f(l, v) = kd × Lambert + ks × Cook-Torrance
```

其中 kd 是漫反射比例，ks 是镜面反射比例，Lambert 是漫反射项，Cook-Torrance 是镜面反射项。

**材质参数**：

| 参数 | 说明 | 范围 |
|------|------|------|
| Albedo | 基础反射率（漫反射颜色） | 线性 RGB |
| Metallic | 金属度（0=非金属，1=金属） | [0, 1] |
| Roughness | 粗糙度（0=光滑镜面，1=粗糙漫反射） | [0, 1] |
| AO | 环境遮蔽 | [0, 1] |

> 金句：Phong 是"看起来对就行"，PBR 是"物理上必须对"——前者是画家，后者是物理学家。

## 10.5 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| 2D 模拟 3D 的局限 | 无深度缓冲（遮挡失败）、无着色器（无法自定义光照） |
| GPU 管线三阶段 | 应用阶段(CPU) → 几何阶段(顶点处理) → 光栅化阶段(片元处理) |
| 顶点着色器 | 计算顶点位置（裁剪空间坐标） |
| 片元着色器 | 计算片元颜色 |
| 深度测试 | 自动处理遮挡，无需手动排序 |
| 坐标变换链 | Model → View → Projection → 透视除法 → 视口变换 |
| 透视 vs 正交 | 透视有近大远小，正交没有 |
| Phong 光照 | 环境光 + 漫反射 + 镜面反射 |
| Blinn-Phong | 用半角向量替代反射向量，更高效更自然 |
| PBR | 基于物理的光照模型， metallic + roughness 参数 |

觉得有用？收藏起来，这是 3D 渲染的骨架知识，后面三章都会用到。

你对 3D 渲染管线有什么困惑？评论区提问，怕浪猫给你解答。

关注怕浪猫，下期我们讲 **WebGL 基础**——从 GLSL 语法到第一个三角形的完整实现。

系列进度 10/17

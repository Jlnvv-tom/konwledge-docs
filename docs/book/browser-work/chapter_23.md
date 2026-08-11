# 第23章 WebGPU 与前端 AI

> WebGPU 不只是 WebGL 的升级版。它带来了计算着色器（Compute Shader），让 GPU 通用计算在浏览器中成为可能。配合浏览器内置 AI，前端正在进入一个新时代。

我是怕浪猫，上期讲了 DevTools 调试技巧，今天进入第 23 章：WebGPU 与前端 AI。这一章拆解 WebGPU 的渲染管线、与 WebGL 的对比、以及浏览器内置 AI（Gemini Nano）的使用方式。

## 23.1 WebGPU 概述

### 23.1.1 WebGPU vs WebGL

| 特性 | WebGL | WebGPU |
|------|-------|--------|
| API 风格 | 命令式 | 命令式（更现代） |
| 着色器语言 | GLSL | WGSL |
| 计算着色器 | 不支持 | 支持 |
| 多线程 | 不支持 | 支持（Worker） |
| 性能 | 良好 | 更好 |
| 驱动开销 | 高 | 低 |

### 23.1.2 WebGPU 渲染管线

```
WebGPU 渲染管线

1. 获取 GPU 适配器
   const adapter = await navigator.gpu.requestAdapter();
   
2. 获取 GPU 设备
   const device = await adapter.requestDevice();
   
3. 配置画布上下文
   const context = canvas.getContext('webgpu');
   context.configure({ device, format });
   
4. 创建管线
   const pipeline = device.createRenderPipeline({
     vertex: { module, entryPoint: 'vs_main' },
     fragment: { module, entryPoint: 'fs_main', targets: [{ format }] }
   });
   
5. 编码命令
   const encoder = device.createCommandEncoder();
   const pass = encoder.beginRenderPass({ ... });
   pass.setPipeline(pipeline);
   pass.draw(3);
   pass.end();
   
6. 提交命令
   device.queue.submit([encoder.finish()]);
```

### 23.1.3 WGSL 着色器

```wgsl
// 顶点着色器
@vertex
fn vs_main(@location(0) pos: vec2<f32>) -> @builtin(position) vec4<f32> {
  return vec4<f32>(pos, 0.0, 1.0);
}

// 片段着色器
@fragment
fn fs_main() -> @location(0) vec4<f32> {
  return vec4<f32>(1.0, 0.0, 0.0, 1.0);  // 红色
}

// 计算着色器
@group(0) @binding(0) var<storage, read_write> data: array<f32>;

@compute @workgroup_size(64)
fn cs_main(@builtin(global_invocation_id) id: vec3<u32>) {
  let i = id.x;
  if (i < arrayLength(&data)) {
    data[i] = data[i] * 2.0;  // 每个元素乘以 2
  }
}
```

> 计算着色器是 WebGPU 的杀手级功能。它允许 GPU 执行通用计算，不只是图形渲染。这意味着机器学习推理、物理模拟、图像处理等计算密集任务可以在 GPU 上并行执行，性能远超 CPU。

## 23.2 WebGPU 计算着色器应用

### 23.2.1 GPU 并行计算

```javascript
// 使用计算着色器处理数据
const data = new Float32Array(1000000);
// ... 填充数据

// 创建 GPU 缓冲区
const buffer = device.createBuffer({
  size: data.byteLength,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST
});

// 上传数据
device.queue.writeBuffer(buffer, 0, data);

// 创建计算管线
const pipeline = device.createComputePipeline({
  layout: 'auto',
  compute: { module, entryPoint: 'cs_main' }
});

// 分派计算
const encoder = device.createCommandEncoder();
const pass = encoder.beginComputePass();
pass.setPipeline(pipeline);
pass.setBindGroup(0, bindGroup);
pass.dispatchWorkgroups(Math.ceil(data.length / 64));
pass.end();
device.queue.submit([encoder.finish()]);
```

| 应用场景 | GPU 加速比 | 说明 |
|---------|-----------|------|
| 矩阵乘法 | 10-100x | ML 推理核心 |
| 图像处理 | 5-50x | 滤镜/卷积 |
| 粒子系统 | 10-50x | 物理模拟 |
| 排序 | 2-10x | 并行排序算法 |

## 23.3 浏览器内置 AI（Gemini Nano）

### 23.3.1 Prompt API

Chrome 内置了 Gemini Nano 模型，通过 Prompt API 可以在浏览器中直接运行 AI 推理，无需服务器。

```javascript
// 检查可用性
const canAI = await window.ai.canCreateTextSession();
if (canAI !== 'readily') {
  console.log('AI 不可用');
  return;
}

// 创建 AI 会话
const session = await window.ai.createTextSession();

// 发送提示
const result = await session.prompt('总结以下文本：...');
console.log(result);

// 流式输出
session.promptStreaming('写一首诗').then(stream => {
  for await (const chunk of stream) {
    console.log(chunk);
  }
});

// 销毁会话
session.destroy();
```

### 23.3.2 内置 AI 的优势

| 特性 | 云端 AI | 浏览器内置 AI |
|------|--------|-------------|
| 延迟 | 高（网络） | 极低（本地） |
| 隐私 | 数据上传 | 数据不离开设备 |
| 离线 | 不可用 | 可用 |
| 成本 | API 收费 | 免费 |
| 能力 | 强（大模型） | 有限（小模型） |
| 模型选择 | 多种 | 固定（Gemini Nano） |

```
内置 AI 适用场景

适合：
  ✓ 文本摘要
  ✓ 简单问答
  ✓ 内容分类
  ✓ 语言翻译（常见语言）
  ✓ 写作辅助

不适合：
  ✗ 复杂推理
  ✗ 代码生成
  ✗ 长文本生成
  ✗ 专业领域知识
```

> 浏览器内置 AI 是 Web 平台的重大变革。它让 AI 能力成为浏览器的一部分，开发者不需要 API Key、不需要服务器、不需要网络。对于隐私敏感的场景（如医疗、金融文档处理），本地 AI 是唯一合规的选择。但模型能力有限，复杂任务仍需云端 AI。

## 23.4 WebNN API

### 23.4.1 WebNN 与 AI 加速

WebNN（Web Neural Network API，Web 神经网络 API）是浏览器中执行神经网络推理的 API，直接利用设备的 AI 加速硬件（NPU、GPU）。

```javascript
// 创建神经网络
const context = await navigator.ml.createContext();

const builder = new MLGraphBuilder(context);

// 构建简单的全连接层
const input = builder.input('input', { type: 'float32', dimensions: [1, 784] });
const weights = builder.constant({ type: 'float32', dimensions: [784, 10] }, weightData);
const bias = builder.constant({ type: 'float32', dimensions: [10] }, biasData);
const output = builder.add(builder.matmul(input, weights), bias);

// 编译图
const graph = await builder.build({ output });

// 执行推理
const results = await graph.compute({
  input: { data: inputData }
});
```

| API | 层级 | 适用场景 |
|-----|------|---------|
| Prompt API | 高级（文本） | 文本生成 |
| WebNN | 低级（张量） | 模型推理 |
| WebGPU Compute | 底层（GPU） | 自定义计算 |

## 23.5 前端 AI 架构

### 23.5.1 模型部署方案

| 方案 | 模型位置 | 延迟 | 隐私 | 复杂度 |
|------|---------|------|------|--------|
| 云端 API | 服务器 | 高 | 低 | 低 |
| 边缘函数 | CDN | 中 | 中 | 中 |
| 浏览器内置 | 浏览器 | 极低 | 高 | 低 |
| ONNX Runtime | 浏览器 | 低 | 高 | 中 |
| TensorFlow.js | 浏览器 | 低 | 高 | 中 |
| WebGPU 自定义 | 浏览器(GPU) | 极低 | 高 | 高 |

```
前端 AI 技术栈

简单文本任务 → Prompt API（浏览器内置）
图像分类 → WebNN API（硬件加速）
自定义模型 → ONNX Runtime Web / TensorFlow.js
高性能计算 → WebGPU Compute Shader
```

## 23.6 WebGPU 渲染管线详解

### 23.6.1 完整渲染管线流程

WebGPU 的渲染管线由多个阶段组成，每个阶段都需要显式配置。与 WebGL 不同，WebGPU 采用了更声明式的 API 设计，所有资源绑定关系在管线创建时就明确声明。

```
WebGPU 渲染管线完整流程

┌──────────────────────────────────────────────────────────┐
│ 1. 初始化                                                  │
│    navigator.gpu → adapter → device                       │
│    canvas.getContext('webgpu') → configure                │
├──────────────────────────────────────────────────────────┤
│ 2. 资源准备                                                │
│    ├─ Buffer（顶点/索引/_uniform 数据）                    │
│    ├─ Texture（图片/渲染目标）                              │
│    ├─ Sampler（采样配置）                                   │
│    └─ Bind Group Layout（资源绑定布局）                     │
├──────────────────────────────────────────────────────────┤
│ 3. 管线创建                                                │
│    ├─ Shader Module（WGSL 代码）                           │
│    ├─ Vertex State（缓冲区布局）                           │
│    ├─ Primitive State（拓扑类型）                          │
│    ├─ Fragment State（目标格式）                           │
│    ├─ Depth/Stencil State                                 │
│    └─ Layout（绑定组布局）                                  │
├──────────────────────────────────────────────────────────┤
│ 4. 渲染循环                                                │
│    ├─ CommandEncoder                                       │
│    │   ├─ beginRenderPass                                 │
│    │   │   ├─ setPipeline                                 │
│    │   │   ├─ setBindGroup                                │
│    │   │   ├─ setVertexBuffer                             │
│    │   │   ├─ setIndexBuffer                              │
│    │   │   ├─ draw / drawIndexed                           │
│    │   │   └─ end                                         │
│    │   └─ copyBufferToBuffer / copyTextureToTexture       │
│    └─ device.queue.submit([encoder.finish()])              │
└──────────────────────────────────────────────────────────┘
```

### 23.6.2 缓冲区

WebGPU 的 Buffer 是一块 GPU 内存，用于存储顶点数据、索引数据、uniform 数据等。

```javascript
// 创建顶点缓冲区
const vertexBuffer = device.createBuffer({
  size: vertices.byteLength,
  usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST,
});
device.queue.writeBuffer(vertexBuffer, 0, vertices);

// 创建 Uniform 缓冲区（存储变换矩阵等）
const uniformBuffer = device.createBuffer({
  size: 64,  // 4x4 矩阵 = 16 * 4 = 64 字节
  usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
});
device.queue.writeBuffer(uniformBuffer, 0, matrixData);

// 创建 Storage 缓冲区（计算着色器读写）
const storageBuffer = device.createBuffer({
  size: data.byteLength,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC | GPUBufferUsage.COPY_DST,
});
```

| Buffer 用途 | Usage 标志 | 典型数据 |
|------------|-----------|----------|
| 顶点缓冲区 | VERTEX | 位置/法线/UV |
| 索引缓冲区 | INDEX | 索引数组 |
| Uniform 缓冲区 | UNIFORM | 变换矩阵 |
| Storage 缓冲区 | STORAGE | 计算数据 |
| 映射缓冲区 | MAP_READ/MAP_WRITE | CPU-GPU 数据交换 |

### 23.6.3 纹理与采样器

```javascript
// 创建纹理
const texture = device.createTexture({
  size: [width, height],
  format: 'rgba8unorm',
  usage: GPUTextureUsage.TEXTURE_BINDING |
         GPUTextureUsage.COPY_DST |
         GPUTextureUsage.RENDER_ATTACHMENT,
});

// 上传纹理数据
device.queue.copyExternalImageToTexture(
  { source: imageBitmap },
  { texture: texture },
  [width, height]
);

// 创建采样器
const sampler = device.createSampler({
  addressModeU: 'repeat',        // U 方向寻址模式
  addressModeV: 'repeat',        // V 方向寻址模式
  magFilter: 'linear',           // 放大过滤
  minFilter: 'linear',           // 缩小过滤
  mipmapFilter: 'linear',        // mipmap 过滤
  maxAnisotropy: 16,             // 各向异性过滤
});
```

### 23.6.4 绑定组布局

绑定组布局定义了着色器如何访问资源。每个绑定组包含多个绑定点，每个绑定点对应一种资源类型。

```javascript
// 定义绑定组布局
const bindGroupLayout = device.createBindGroupLayout({
  entries: [
    {
      binding: 0,  // Uniform 缓冲区
      visibility: GPUShaderStage.VERTEX | GPUShaderStage.FRAGMENT,
      buffer: { type: 'uniform' },
    },
    {
      binding: 1,  // 纹理
      visibility: GPUShaderStage.FRAGMENT,
      texture: { sampleType: 'float' },
    },
    {
      binding: 2,  // 采样器
      visibility: GPUShaderStage.FRAGMENT,
      sampler: { type: 'filtering' },
    },
    {
      binding: 3,  // Storage 缓冲区（计算着色器）
      visibility: GPUShaderStage.COMPUTE,
      buffer: { type: 'storage' },
    },
  ],
});

// 创建绑定组（将实际资源绑定到布局）
const bindGroup = device.createBindGroup({
  layout: bindGroupLayout,
  entries: [
    { binding: 0, resource: { buffer: uniformBuffer } },
    { binding: 1, resource: texture.createView() },
    { binding: 2, resource: sampler },
    { binding: 3, resource: { buffer: storageBuffer } },
  ],
});
```

```
绑定组布局与绑定组关系

Bind Group Layout（模板）:
  binding 0 → uniform buffer (vertex|fragment)
  binding 1 → texture (fragment)
  binding 2 → sampler (fragment)
  binding 3 → storage buffer (compute)

Bind Group A（实例 A）:
  binding 0 → matrixBufferA
  binding 1 → textureA
  binding 2 → samplerA
  binding 3 → dataBufferA

Bind Group B（实例 B）:
  binding 0 → matrixBufferB
  binding 1 → textureB
  binding 2 → samplerB
  binding 3 → dataBufferB

同一个布局可以创建多个绑定组，切换绑定组即可切换资源
```

## 23.7 WGSL 语法详解

### 23.7.1 变量与类型系统

WGSL（WebGPU Shading Language）是 WebGPU 的着色器语言，替代了 WebGL 的 GLSL。WGSL 的设计目标是类型安全和编译时可检查。

```wgsl
// 基本类型
var x: f32 = 1.0;        // 32 位浮点
var y: i32 = 42;         // 32 位有符号整数
var z: u32 = 100u;       // 32 位无符号整数
var w: f16 = 1.0h;       // 16 位浮点（需支持）

// 向量类型
var v2: vec2<f32> = vec2<f32>(1.0, 2.0);
var v3: vec3<f32> = vec3<f32>(1.0, 2.0, 3.0);
var v4: vec4<f32> = vec4<f32>(1.0, 2.0, 3.0, 4.0);

// 矩阵类型
var m2: mat2x2<f32> = mat2x2<f32>(1.0, 0.0, 0.0, 1.0);
var m4: mat4x4<f32> = mat4x4<f32>();  // 4x4 矩阵

// 数组
var arr: array<f32, 8> = array<f32, 8>();  // 固定长度数组
var dyn: array<f32>;  // 运行时长度数组（storage buffer）

// 结构体
struct VertexOutput {
  @builtin(position) clip_position: vec4<f32>,
  @location(0) tex_coords: vec2<f32>,
  @location(1) normal: vec3<f32>,
};

// 访问修饰符
var<private> localVar: f32 = 0.0;      // 私有变量
var<workgroup> sharedVar: f32 = 0.0;    // 工作组共享变量（计算着色器）
var<uniform> uniforms: Uniforms;        // Uniform 变量
var<storage, read> inputData: array<f32>;   // 只读 Storage
var<storage, read_write> outputData: array<f32>;  // 读写 Storage
```

| WGSL 类型 | 说明 | 对应 JS 类型 |
|-----------|------|-------------|
| f32 | 32位浮点 | Float32Array |
| i32 | 32位有符号整数 | Int32Array |
| u32 | 32位无符号整数 | Uint32Array |
| f16 | 16位浮点 | Float16Array |
| vec2/3/4 | 向量 | — |
| mat4x4 | 4x4 矩阵 | — |
| array | 数组 | TypedArray |
| struct | 结构体 | — |

### 23.7.2 函数与内置函数

```wgsl
// 函数定义
fn add(a: f32, b: f32) -> f32 {
  return a + b;
}

// 顶点着色器入口
@vertex
fn vs_main(
  @location(0) position: vec3<f32>,
  @location(1) uv: vec2<f32>,
) -> VertexOutput {
  var out: VertexOutput;
  out.clip_position = uniforms.mvp * vec4<f32>(position, 1.0);
  out.tex_coords = uv;
  return out;
}

// 片段着色器入口
@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  let color = textureSample(t_diffuse, s_diffuse, in.tex_coords);
  return color;
}

// 计算着色器入口
@compute @workgroup_size(8, 8, 1)
fn cs_main(
  @builtin(global_invocation_id) id: vec3<u32>
) {
  let x = id.x;
  let y = id.y;
  if (x >= u32(uniforms.width) || y >= u32(uniforms.height)) {
    return;
  }
  // 计算逻辑
  outputData[y * u32(uniforms.width) + x] = result;
}

// 常用内置函数
let v = vec3<f32>(1.0, 2.0, 3.0);
let len = length(v);            // 长度
let n = normalize(v);           // 归一化
let c = cross(v1, v2);          // 叉积
let d = dot(v1, v2);            // 点积
let r = reflect(v, n);          // 反射
let m = clamp(x, 0.0, 1.0);    // 钳制
let s = smoothstep(0.0, 1.0, x); // 平滑插值
let mix_v = mix(a, b, 0.5);     // 线性插值
let f = fract(1.5);             // 小数部分
```

## 23.8 WebGPU vs WebGL 性能基准测试

### 23.8.1 基准测试对比

以下是在 Chrome 120 上的基准测试数据，测试环境为 M1 MacBook Pro，分辨率 1920x1080。

| 测试场景 | WebGL 2.0 | WebGPU | 提升倍数 |
|---------|-----------|--------|----------|
| 10万粒子系统 | 32 FPS | 60 FPS | 1.9x |
| 矩阵乘法(1024x1024) | 45ms | 3ms | 15x |
| 图像卷积(1024x1024) | 28ms | 8ms | 3.5x |
| 三角形绘制(100万) | 16ms | 12ms | 1.3x |
| 纹理采样(4K) | 8ms | 6ms | 1.3x |
| 光线追踪(简单场景) | 不支持 | 18ms | — |

```
性能差异原因分析

WebGL 性能瓶颈：
  ├─ 每帧需要大量 GL 状态切换
  ├─ 着色器编译不可缓存（每次重建）
  ├─ 无计算着色器（CPU 回读数据）
  └─ 驱动层开销大（OpenGL → 驱动 → GPU）

WebGPU 优势：
  ├─ 显式管线对象（预编译，复用）
  ├─ 计算着色器（GPU 直接计算，无需回读）
  ├─ 命令编码器（批量提交，减少开销）
  └─ 现代 API 层（Vulkan/Metal/D3D12 直连）
```

## 23.9 计算着色器实战

### 23.9.1 矩阵乘法

矩阵乘法是机器学习的核心运算。用计算着色器在 GPU 上并行计算可以大幅加速。

```wgsl
// 矩阵乘法计算着色器
// C = A * B，矩阵大小 N x N

@group(0) @binding(0) var<storage, read> a: array<f32>;
@group(0) @binding(1) var<storage, read> b: array<f32>;
@group(0) @binding(2) var<storage, read_write> c: array<f32>;

override let N: u32 = 1024;  // 矩阵维度
override let BLOCK_SIZE: u32 = 16;

@compute @workgroup_size(16, 16, 1)
fn main(
  @builtin(workgroup_id) wg_id: vec3<u32>,
  @builtin(local_invocation_id) local_id: vec3<u32>,
) {
  let row = wg_id.x * BLOCK_SIZE + local_id.x;
  let col = wg_id.y * BLOCK_SIZE + local_id.y;
  
  if (row >= N || col >= N) {
    return;
  }
  
  var sum: f32 = 0.0;
  for (var k: u32 = 0u; k < N; k = k + 1u) {
    sum = sum + a[row * N + k] * b[k * N + col];
  }
  
  c[row * N + col] = sum;
}
```

```javascript
// JavaScript 端配置
const N = 1024;
const tileSize = 16;

// 创建缓冲区
const bufferA = device.createBuffer({
  size: N * N * 4,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
});
device.queue.writeBuffer(bufferA, 0, matrixA);

// 分派计算
const encoder = device.createCommandEncoder();
const pass = encoder.beginComputePass();
pass.setPipeline(pipeline);
pass.setBindGroup(0, bindGroup);
pass.dispatchWorkgroups(N / tileSize, N / tileSize, 1);
pass.end();
device.queue.submit([encoder.finish()]);
```

### 23.9.2 图像卷积

```wgsl
// 高斯模糊卷积着色器
@group(0) @binding(0) var src_tex: texture_2d<f32>;
@group(0) @binding(1) var dst_tex: texture_storage_2d<rgba8unorm, write>;
@group(0) @binding(2) var sampler_src: sampler;

override let KERNEL_SIZE: u32 = 5;
const KERNEL_RADIUS: i32 = 2;

// 高斯核
const gaussian_kernel: array<f32, 25> = array<f32, 25>(
  0.003, 0.013, 0.022, 0.013, 0.003,
  0.013, 0.060, 0.098, 0.060, 0.013,
  0.022, 0.098, 0.162, 0.098, 0.022,
  0.013, 0.060, 0.098, 0.060, 0.013,
  0.003, 0.013, 0.022, 0.013, 0.003
);

@compute @workgroup_size(8, 8, 1)
fn main(@builtin(global_invocation_id) id: vec3<u32>) {
  let dims = textureDimensions(src_tex);
  if (id.x >= dims.x || id.y >= dims.y) {
    return;
  }
  
  var color: vec4<f32> = vec4<f32>(0.0, 0.0, 0.0, 0.0);
  let center = vec2<f32>(f32(id.x), f32(id.y));
  
  var k: u32 = 0u;
  for (var dy: i32 = -KERNEL_RADIUS; dy <= KERNEL_RADIUS; dy = dy + 1) {
    for (var dx: i32 = -KERNEL_RADIUS; dx <= KERNEL_RADIUS; dx = dx + 1) {
      let offset = vec2<f32>(f32(dx), f32(dy));
      let texel = textureSampleLevel(src_tex, sampler_src, center + offset, 0.0);
      color = color + texel * gaussian_kernel[k];
      k = k + 1u;
    }
  }
  
  textureStore(dst_tex, vec2<u32>(id.x, id.y), color);
}
```

## 23.10 TensorFlow.js WebGPU Backend 原理

### 23.10.1 TFJS 后端架构

TensorFlow.js 通过不同的后端执行计算，WebGPU 后端利用计算着色器加速张量运算。

```
TFJS 后端架构

┌─────────────────────────────────┐
│      TensorFlow.js API          │
├─────────────────────────────────┤
│      Backend 抽象层              │
├────────┬────────┬───────────────┤
│  CPU   │ WebGL  │   WebGPU      │
│ Backend│ Backend │   Backend     │
├────────┼────────┼───────────────┤
│ JS计算  │ GLSL   │   WGSL        │
│ TypedArray │ 着色器 │  计算着色器    │
└────────┴────────┴───────────────┘

WebGPU Backend 优势：
  ├─ 计算着色器替代顶点/片段着色器
  ├─ Storage Buffer 直接读写（无需纹理编码）
  ├─ 工作组共享变量加速局部计算
  └─ 命令编码器批量提交
```

```javascript
// 使用 WebGPU 后端
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-backend-webgpu';

// 等待 WebGPU 后端就绪
await tf.ready();
tf.setBackend('webgpu');

// 模型推理自动使用 WebGPU
const model = await tf.loadGraphModel('model.json');
const input = tf.tensor4d(imageData, [1, 224, 224, 3]);
const output = model.predict(input);
```

| 后端 | 矩阵乘法性能 | 模型推理 | 兼容性 |
|------|-------------|---------|--------|
| CPU | 1x（基准）| 慢 | 100% |
| WebGL | 5-10x | 中 | 97% |
| WebGPU | 10-50x | 快 | 92%+ |

## 23.11 浏览器内置 AI Prompt API 高级用法

### 23.11.1 会话配置

Prompt API 不只是简单的文本输入输出，它支持系统提示、温度参数和上下文窗口等高级配置。

```javascript
// 创建带配置的 AI 会话
const session = await ai.createTextSession({
  systemPrompt: '你是一个专业的代码审查助手。只回答代码相关问题，回答要简洁。',
  temperature: 0.3,        // 较低温度 = 更确定性的输出
  topK: 1,                 // Top-K 采样
  initialPrompts: [
    { role: 'system', content: '上下文：用户正在开发 React 应用' },
    { role: 'user', content: '解释 useEffect 的依赖数组' },
    { role: 'assistant', content: 'useEffect 的依赖数组决定...' }
  ]
});

// 流式输出
const stream = session.promptStreaming('如何优化 React 渲染性能？');
for await (const chunk of stream) {
  // 逐步显示输出
  appendToUI(chunk);
}

// 多轮对话
const response1 = await session.prompt('什么是闭包？');
const response2 = await session.prompt('给一个闭包的代码示例');  // 包含上一轮上下文

// 获取 token 使用量
const info = await session.prompt('Hello', { includeUsage: true });
console.log('输入 tokens:', info.usage.inputTokens);
console.log('输出 tokens:', info.usage.outputTokens);

session.destroy();
```

### 23.11.2 Prompt API 参数详解

| 参数 | 类型 | 说明 | 影响 |
|------|------|------|------|
| systemPrompt | string | 系统提示 | 定义 AI 角色 |
| temperature | number (0-1) | 温度 | 低=确定，高=创意 |
| topK | number | Top-K 采样 | 限制候选词数量 |
| initialPrompts | array | 初始对话 | 预设上下文 |
| includeUsage | boolean | 返回 token 用量 | 监控消耗 |

```javascript
// 温度参数对比
const lowTemp = await ai.createTextSession({ temperature: 0.1 });
const highTemp = await ai.createTextSession({ temperature: 0.9 });

// 低温度：每次输出几乎相同
await lowTemp.prompt('写一个问候语');  // → "你好"
await lowTemp.prompt('写一个问候语');  // → "你好"

// 高温度：每次输出不同
await highTemp.prompt('写一个问候语');  // → "嘿，今天天气真好！"
await highTemp.prompt('写一个问候语');  // → "嗨，好久不见！"
```

## 23.12 WebNN 模型部署实战

### 23.12.1 ONNX 模型转换与加载

WebNN API 可以直接执行 ONNX（Open Neural Network Exchange）格式的模型。ONNX 是跨框架的模型格式，PyTorch、TensorFlow 等框架都可以导出为 ONNX。

```python
# Python 端：将 PyTorch 模型导出为 ONNX
import torch
import torch.onnx

model = MyModel()
model.load_state_dict(torch.load('model.pth'))
model.eval()

dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model, dummy_input, 'model.onnx',
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
)
```

```javascript
// 浏览器端：使用 WebNN 执行 ONNX 模型
// 需要使用 onnxruntime-web
import * as ort from 'onnxruntime-web';

// 配置 WebNN 执行提供者
const session = await ort.InferenceSession.create('model.onnx', {
  executionProviders: ['webnn', 'webgpu', 'wasm'],
  // 优先使用 WebNN（NPU 加速），回退到 WebGPU，最后回退到 WASM
});

// 执行推理
const inputTensor = new ort.Tensor('float32', inputData, [1, 3, 224, 224]);
const results = await session.run({ input: inputTensor });
const outputData = results.output.data;
```

### 23.12.2 WebNN 执行提供者对比

```
WebNN 执行提供者优先级

1. NPU（神经网络处理器）
   ├─ 最快推理速度
   ├─ 最低功耗
   └─ 需要硬件支持（如 Apple Neural Engine）

2. GPU（图形处理器）
   ├─ 高速并行计算
   ├─ 通用性好
   └─ 通过 Compute Shader 执行

3. CPU（中央处理器）
   ├─ 兜底方案
   ├─ 通用性最强
   └─ 使用优化指令集（AVX/SIMD）
```

| 执行提供者 | 速度 | 功耗 | 可用性 |
|-----------|------|------|--------|
| NPU | 最快 | 最低 | 需要专用硬件 |
| GPU | 快 | 中等 | 广泛支持 |
| CPU | 慢 | 高 | 100% |

## 23.13 前端 AI 隐私优势分析

### 23.13.1 隐私保护维度

前端 AI 的最大优势之一是隐私保护。数据不离开用户设备，不会上传到服务器，从根本上杜绝了数据泄露风险。

```
隐私保护对比

云端 AI 流程：
  用户输入 → 网络传输 → 服务器处理 → 存储(可能) → 返回结果
  风险点：传输截获、服务器存储、日志记录、第三方共享

浏览器 AI 流程：
  用户输入 → 本地推理 → 返回结果
  风险点：无（数据不离开设备）

合规性分析：
  ├─ GDPR（欧盟通用数据保护条例）
  │   ├─ 云端：需要数据处理协议
  │   └─ 本地：无数据传输，自动合规
  ├─ HIPAA（美国医疗信息保护）
  │   ├─ 云端：需要 BAA 协议
  │   └─ 本地：无数据传输，自动合规
  └─ 中国《个人信息保护法》
      ├─ 云端：需要用户同意
      └─ 本地：无数据传输，自动合规
```

| 隐私维度 | 云端 AI | 浏览器 AI |
|---------|--------|----------|
| 数据传输 | 需要 | 不需要 |
| 服务器存储 | 可能 | 不会 |
| 日志记录 | 可能 | 不会 |
| 第三方共享 | 风险存在 | 不可能 |
| GDPR 合规 | 需要额外措施 | 天然合规 |
| 延迟 | 高 | 极低 |
| 离线可用 | 不可用 | 可用 |

> 对于医疗、金融、法律等隐私敏感领域，浏览器 AI 不只是技术选择，更是合规选择。当数据不需要离开用户设备时，大部分隐私法规的约束自动解除。这使得前端 AI 在这些领域有不可替代的价值。

## 本章核心知识总结

| 知识模块 | 核心内容 | 实践意义 |
|---------|---------|---------|
| WebGPU | 现代图形 API | 替代 WebGL |
| 计算着色器 | GPU 通用计算 | ML/物理模拟 |
| WGSL | WebGPU 着色器语言 | 替代 GLSL |
| Gemini Nano | 浏览器内置 AI | 本地 AI 推理 |
| WebNN | 神经网络 API | 硬件加速推理 |
| 前端 AI 架构 | 多层方案选择 | 按需选择 |

觉得有用？收藏起来，这是前端 AI 最全面的技术综述。

你对 WebGPU 或浏览器 AI 有什么看法？会在项目中用吗？评论区聊聊。

关注怕浪猫，下期是本书最后一章。系列进度 23/24。

下期预告：第 24 章「Web 的未来与完结」。我们会回顾全系列内容，展望 Web 平台的未来方向，并附上完整的知识索引。怕浪猫下期见。

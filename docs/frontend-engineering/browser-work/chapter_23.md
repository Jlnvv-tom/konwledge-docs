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

## 23.14 WebGPU 实战进阶

### 23.14.1 粒子系统完整实现

粒子系统是 WebGPU 计算着色器的经典应用场景。传统的 CPU 粒子系统在处理数万粒子时就会遇到性能瓶颈，而 GPU 计算着色器可以轻松处理数十万粒子。

粒子系统的核心思路是将粒子数据存储在 GPU 缓冲区中，所有物理计算都在计算着色器中执行。CPU 只负责设置参数和分派计算任务，不参与粒子数据的读写。这种架构彻底消除了 CPU 和 GPU 之间的数据传输开销。

```javascript
// 粒子系统初始化
const PARTICLE_COUNT = 100000;
const particleData = new Float32Array(PARTICLE_COUNT * 8); // x,y,z,vx,vy,vz,life,size

// 初始化粒子（随机位置和速度）
for (let i = 0; i < PARTICLE_COUNT; i++) {
  const offset = i * 8;
  particleData[offset] = (Math.random() - 0.5) * 100;
  particleData[offset + 1] = Math.random() * 50;
  particleData[offset + 2] = (Math.random() - 0.5) * 100;
  particleData[offset + 3] = (Math.random() - 0.5) * 2;
  particleData[offset + 4] = Math.random() * 2 + 1;
  particleData[offset + 5] = (Math.random() - 0.5) * 2;
  particleData[offset + 6] = Math.random() * 5;
  particleData[offset + 7] = Math.random() * 2 + 0.5;
}

const particleBuffer = device.createBuffer({
  size: particleData.byteLength,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST
});
device.queue.writeBuffer(particleBuffer, 0, particleData);
```

粒子更新着色器负责计算粒子的物理运动，包括重力、速度更新和生命周期递减。每个工作组的线程负责一组粒子的计算。这种数据并行模式是 GPU 计算的核心优势所在。计算着色器中每个线程处理一个粒子，数千个线程同时执行，因此能实现极高的吞吐量。

```wgsl
struct Particle {
  position: vec3<f32>,
  velocity: vec3<f32>,
  life: f32,
  size: f32,
}

@group(0) @binding(0) var<storage, read_write> particles: array<Particle>;
@group(0) @binding(1) var<uniform> params: SimParams;

struct SimParams {
  deltaTime: f32,
  gravity: f32,
  padding: vec2<f32>,
}

@compute @workgroup_size(64)
fn updateParticles(@builtin(global_invocation_id) id: vec3<u32>) {
  let index = id.x;
  if (index >= arrayLength(&particles)) { return; }
  var p = particles[index];
  p.velocity.y = p.velocity.y - params.gravity * params.deltaTime;
  p.position = p.position + p.velocity * params.deltaTime;
  p.life = p.life - params.deltaTime;
  if (p.life <= 0.0) {
    p.position = vec3<f32>(0.0, 0.0, 0.0);
    p.life = 5.0;
  }
  particles[index] = p;
}
```

### 23.14.2 WebGPU 渲染与计算协同

WebGPU 的一个强大之处是计算着色器和渲染管线可以共享同一个缓冲区。粒子系统利用这一特性，计算着色器更新粒子位置后，渲染管线直接读取同一缓冲区进行渲染，无需数据回读到 CPU 再上传。这种零拷贝架构在处理大规模数据时优势显著。

在 WebGL 中实现同样的粒子系统，需要 CPU 计算粒子位置后通过 `bufferData` 上传到 GPU。每次更新都需要完整的数据传输，对于十万级粒子来说，每帧传输几兆字节数据成为瓶颈。而 WebGPU 的计算着色器直接在 GPU 内存中操作数据，完全避免了传输开销。

### 23.14.3 WebGPU 能力检测与回退策略

WebGPU 目前在所有浏览器中的支持还不完整。Safari 和 Firefox 的支持仍在开发中。因此在生产环境中使用 WebGPU 时，必须进行能力检测并提供 WebGL 回退方案。回退策略的设计应该让上层调用者无感知，通过统一的渲染接口封装底层差异。

```javascript
async function initRenderer(canvas) {
  if (navigator.gpu) {
    try {
      const adapter = await navigator.gpu.requestAdapter();
      if (adapter) {
        const device = await adapter.requestDevice();
        return new WebGPURenderer(canvas, device);
      }
    } catch (e) {
      console.warn('WebGPU 初始化失败，回退到 WebGL');
    }
  }
  const gl = canvas.getContext('webgl2');
  if (gl) return new WebGL2Renderer(canvas, gl);
  return new Canvas2DRenderer(canvas, canvas.getContext('2d'));
}
```

## 23.15 前端 AI 应用架构模式

### 23.15.1 混合 AI 架构

在实际应用中，浏览器内置 AI 和云端 AI 各有优势。最佳实践是构建混合架构，根据任务复杂度和隐私要求选择合适的 AI 层。简单任务如文本摘要、内容分类使用本地 AI，复杂任务如代码生成、长文本分析使用云端 AI。这种分层策略既保证了简单任务的低延迟，又能处理需要大模型能力的复杂任务。

混合架构的关键是任务路由决策。路由器根据输入长度、任务类型和用户设置决定使用本地还是云端。对于短文本的摘要任务，本地 AI 足够应对。对于长文档的分析，需要云端 AI 的更大上下文窗口。如果用户处于离线状态，则强制使用本地 AI。路由决策应该是可配置的，让用户在隐私和性能之间做出自己的选择。

```javascript
class HybridAI {
  async summarize(text) {
    if (text.length < 500 && this.localSession) {
      return this.localSession.prompt(`总结以下文本：${text}`);
    }
    return this.cloudSummarize(text);
  }
  async classify(text) {
    if (this.localSession) {
      return this.localSession.prompt(`分类以下文本：${text}`);
    }
    return this.cloudClassify(text);
  }
}
```

### 23.15.2 渐进式 AI 增强

渐进式 AI 增强是一种设计理念：基础功能不依赖 AI，AI 作为增强层提供更好的体验。这种理念确保应用在 AI 不可用时仍然可用，同时在支持 AI 的浏览器中提供智能增强。

一个典型场景是搜索功能。基础搜索使用传统的文本匹配，不需要 AI。当浏览器支持 AI 时，增加语义搜索能力，理解用户意图而不仅是关键词匹配。这种渐进式增强让应用同时兼容新旧设备，不会因为 AI 不可用而丧失核心功能。

### 23.15.3 端侧 AI 的未来展望

随着 NPU（Neural Processing Unit，神经网络处理器）在移动设备中的普及，前端 AI 的能力将显著提升。目前的浏览器内置 AI 只能运行小规模模型，但 WebNN API 的硬件加速能力意味着未来可以在浏览器中运行更大的模型。当 NPU 算力达到一定水平后，许多原本需要云端 AI 的任务都可以在本地完成。

端侧 AI 的另一个重要方向是模型个性化。通过联邦学习等技术，可以在不上传用户数据的前提下，利用用户的使用数据微调本地模型。这种隐私保护的个性化方案在广告推荐、内容过滤等场景中有巨大潜力。前端开发者需要开始学习如何将 AI 能力集成到 Web 应用中，为这个趋势做好准备。

### 23.15.4 WebGPU 在数据可视化中的应用

WebGPU 的计算着色器不仅适用于游戏和物理模拟，在数据可视化领域也有巨大潜力。传统的大规模数据可视化受限于 CPU 的计算能力和 WebGL 的渲染管线。WebGPU 的计算着色器可以在 GPU 上并行处理数据变换，渲染管线直接渲染处理后的结果，实现百万级数据点的实时交互式可视化。

一个典型的场景是实时地理热力图。传统方案需要在服务器端预计算热力数据，客户端只负责渲染。如果数据发生变化，需要重新请求服务器。使用 WebGPU，可以在客户端直接处理原始数据，通过计算着色器并行计算热力分布，然后渲染管线实时绘制。这种架构不仅减少了服务器负载，还实现了真正的实时交互。

### 23.15.5 浏览器 AI 的安全边界

浏览器内置 AI 虽然在隐私方面有优势，但也引入了新的安全考量。Prompt API 允许网页向本地模型发送任意提示文本，如果不对输入做适当限制，恶意网页可能利用 AI 生成有害内容或执行提示注入攻击。

开发者在使用 Prompt API 时应该建立输入验证机制。对于用户生成的提示内容，应该过滤敏感关键词和恶意指令。系统提示应该明确限制 AI 的行为边界，比如禁止生成代码执行指令、禁止泄露系统信息。这些安全措施与云端 AI 的安全实践类似，但在前端实现时需要更加注意，因为前端代码可以被用户查看和修改。

### 23.15.6 前端 AI 的工程化实践

将 AI 能力集成到前端应用需要解决一系列工程问题。首先是模型加载和初始化。浏览器内置 AI 不需要加载模型，但 WebGPU 和 WebNN 方案需要在页面加载时下载模型文件。模型文件通常较大，应该使用 Service Worker 缓存模型数据，避免每次访问都重新下载。

其次是推理性能的优化。WebGPU 和 WebNN 的推理调用是异步的，应该使用 Web Worker 将推理逻辑移出主线程，避免阻塞用户交互。在推理过程中应该显示加载状态，让用户知道 AI 正在处理。对于实时性要求高的场景，可以使用批处理机制将多个推理请求合并，减少 GPU 或 NPU 的调度开销。

最后是错误处理和降级策略。AI 推理可能因为各种原因失败：模型加载失败、GPU 不可用、内存不足等。应用应该提供无 AI 的备选方案，确保核心功能在 AI 不可用时仍然可用。这种渐进增强的策略是前端 AI 工程化的核心原则。

### 23.15.7 WebGPU 与 WebGL 混合渲染

在一些大型应用中，可能需要同时使用 WebGPU 和 WebGL。比如一个 3D 编辑器，主渲染使用 WebGPU，但某些插件或第三方库仍然依赖 WebGL。Chrome 支持 WebGPU 和 WebGL 上下文共存于同一个页面，但需要注意性能影响。

两个图形上下文共存时，GPU 资源是共享的。WebGL 的纹理和缓冲区占用 GPU 内存，可能影响 WebGPU 的可用资源。在移动设备上，GPU 内存有限，同时运行两个图形上下文可能导致内存压力。最佳实践是尽快将所有渲染迁移到 WebGPU，使用临时桥接层在过渡期同时支持两者。

### 23.15.8 WGSL 着色器调试技巧

WGSL 着色器的调试比 JavaScript 调试困难得多，因为着色器在 GPU 上执行，无法直接打质点或输出日志。WebGPU 提供了一些辅助调试的手段。第一个是错误信息。如果 WGSL 代码有语法错误或类型错误，`device.createShaderModule` 会返回带有错误信息的编译结果。仔细阅读错误信息通常可以定位问题。

第二个是验证层。在开发环境中开启 WebGPU 验证层，浏览器会对每个 GPU 操作进行额外检查，包括缓冲区越界、纹理格式不匹配、绑定组布局不一致等。验证层会降低性能，但能捕获大量编程错误。生产环境应该关闭验证层以获得最佳性能。

第三个是输出调试。虽然着色器不能直接输出日志，但可以通过写入特定的缓冲区或纹理来传递调试信息。比如在计算着色器中将中间结果写入一个 Storage Buffer，然后在 JavaScript 端读取这个缓冲区的值。或者将调试信息渲染到纹理上，然后在 Canvas 中显示。

### 23.15.9 浏览器 AI 能力的边界与局限

浏览器内置 AI 虽然令人兴奋，但需要清醒认识其能力边界。Gemini Nano 是一个约三十亿参数的小模型，其能力远不及 GPT-4 或 Claude 3 等大模型。在复杂推理、代码生成、长文本理解等任务上，本地 AI 的表现明显不如云端大模型。

本地 AI 的另一个局限是模型固定。用户不能选择不同的模型，也不能微调模型。开发者只能使用浏览器提供的固定模型，无法针对特定场景优化。这意味着浏览器内置 AI 最适合通用性强的简单任务，而不是需要专业能力的垂直领域任务。

尽管有这些局限，浏览器内置 AI 的价值不在于替代云端 AI，而在于提供零成本、零延迟、零隐私风险的本地智能能力。对于文本摘要、内容分类、简单问答等任务，本地 AI 已经足够好用。随着模型技术的进步和浏览器硬件的升级，本地 AI 的能力边界会持续扩展。

### 23.15.10 WebGPU 在机器学习推理中的优势

WebGPU 在机器学习推理方面相比 WebGL 有结构性优势。这些优势不仅体现在原始计算速度上，更体现在编程模型和资源管理的灵活性上。理解这些优势有助于开发者在合适的场景选择 WebGPU。

第一个优势是计算着色器。WebGL 只能通过顶点着色器和片段着色器进行 GPU 计算，需要将计算任务伪装成图形渲染管线。这种方式不直观，而且受到管线的限制。比如在 WebGL 中实现矩阵乘法，需要将矩阵数据编码为纹理，通过渲染一个全屏四边形触发计算，再将结果纹理读回 CPU。WebGPU 的计算着色器直接对 Storage Buffer 读写，不需要纹理编码和回读，大幅减少了开销。

第二个优势是显式资源管理。WebGL 的资源管理是隐式的，开发者调用 `gl.createTexture` 后不需要关心资源何时被释放。但这种便利也带来了不可控性——GPU 资源何时被回收不确定，可能导致内存峰值过高。WebGPU 的资源是显式管理的，创建和销毁都由开发者控制，可以更精确地管理 GPU 内存。

第三个优势是管线对象预编译。WebGL 的着色器在每次使用时都可能被重新编译，取决于驱动程序的行为。WebGPU 的管线对象在创建时就完成了着色器编译和管线状态设置，之后可以反复使用。这意味着第一帧之后不会再有着色器编译的卡顿，渲染性能更稳定。

### 23.15.11 前端 AI 的商业模式与价值创造

前端 AI 不仅是技术问题，也带来了新的商业模式可能性。传统 AI 应用的成本结构是服务器成本加 API 调用费用，用户量越大成本越高。浏览器内置 AI 将计算成本转移到用户的设备上，应用提供商不需要支付推理费用。这种零边际成本的 AI 能力为许多原本不经济的场景打开了大门。

比如一个面向学生的高频问答应用，如果每次推理都需要调用云端 API，成本会随用户量线性增长。而使用浏览器内置 AI，每个用户的推理在本地完成，服务器的成本只是静态资源托管费用。这种成本结构的改变可能催生新的产品形态。

但浏览器内置 AI 也有限制商业价值的因素。模型固定意味着差异化困难——所有应用使用同一个模型，无法通过模型能力建立竞争壁垒。应用价值需要通过场景设计、数据积累和用户体验来体现，而不是依靠 AI 能力本身。这意味着前端 AI 的竞争本质上是产品和体验的竞争。

### 23.15.12 WebGPU 生态与工具链现状

WebGPU 的生态系统正在快速发展。虽然不如 WebGL 成熟，但已经有了不少可用的工具和库。了解这些工具可以避免重复造轮子，加速开发。

Babylon.js 是最早支持 WebGPU 的 3D 引擎之一。它提供了 WebGPU 和 WebGL 的双后端支持，可以无缝切换。Three.js 也正在添加 WebGPU 支持，通过 WebGPURenderer 提供兼容接口。对于已有 Three.js 项目，迁移到 WebGPU 的成本相对较低。

Dawn 是 Google 开发的 WebGPU 实现，Chrome 使用它作为 WebGPU 的底层实现。Dawn 提供了跨平台的 WebGPU API 实现，支持 Vulkan、Metal 和 Direct3D 12 后端。其他浏览器也可以使用 Dawn 实现 WebGPU 支持，这有助于保证跨浏览器的一致性。

wgpu 是 Rust 生态的 WebGPU 实现，可以在 Rust 程序中使用 WebGPU API，编译为 WebAssembly 后在浏览器中运行。这对于需要在浏览器中进行高性能计算的 Rust 项目特别有用。wgpu 也可以用于服务端 GPU 计算，提供与浏览器一致的 API 体验。

### 23.15.13 前端 AI 的用户体验设计

AI 功能的 UX 设计与传统 Web 功能有本质区别。AI 的输出是不确定的，同样的输入可能产生不同的结果。这种不确定性需要在用户体验设计中充分考虑。

第一个设计原则是透明度。用户应该知道他们正在与 AI 交互，而不是与确定性程序交互。AI 的建议或输出应该标注为「AI 生成」，让用户自行判断是否采纳。对于可能出错的场景，应该提供简单的纠正机制。

第二个设计原则是渐进式展示。对于 AI 生成的长文本，应该先展示摘要，让用户决定是否展开完整内容。对于 AI 分类结果，应该展示置信度，低置信度的结果让用户确认。这种渐进式展示避免了信息过载，也减少了 AI 错误对用户体验的冲击。

第三个设计原则是可中断性。AI 推理可能需要时间，用户应该可以随时中断推理过程。流式输出是最佳实践——让用户看到 AI 正在逐步生成结果，而不是等待一个黑盒返回。如果推理时间超过三秒，应该显示进度指示器或提供取消按钮。

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

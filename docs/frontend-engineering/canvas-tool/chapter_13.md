---
sidebar_position: 13
---

# 第13章 WebGPU：下一代图形 API

WebGPU 比 WebGL 好学？

这听起来像标题党，但在某些方面确实如此。WebGL 的状态机模型有 50 多个全局状态，你需要记住哪些状态会影响哪些调用。WebGPU 用"命令编码"替代了"即时调用"——你先录制一串命令，再一次性提交给 GPU 执行。这种设计让代码更清晰、更可预测。

我是怕浪猫，这一章带你理解 WebGPU 的核心概念，以及它为什么是 WebGL 的继任者。

## 13.1 WebGPU 是什么

### 13.1.1 与 WebGL 的本质区别

WebGL 是 OpenGL ES 的浏览器绑定，继承了 OpenGL 的全局状态机模型。每次调用都直接作用于当前状态。

WebGPU 是全新的 Web 图形 API，基于现代图形 API（Vulkan、Metal、Direct3D 12）的设计理念。核心区别：

| 维度 | WebGL | WebGPU |
|------|-------|--------|
| 底层 API | OpenGL ES 2.0/3.0 | Vulkan/Metal/D3D12 |
| 编程模型 | 全局状态机 | 命令编码 + 提交 |
| 着色器语言 | GLSL | WGSL（WebGPU Shading Language） |
| 资源绑定 | 全局位置绑定 | BindGroup 显式分组 |
| 错误处理 | 同步报错 | 异步 + 错误范围 |
| 计算着色器 | 不支持（WebGL2 也不支持） | 原生支持 |
| 多线程 | 不支持 | Worker 中编码命令 |

### 13.1.2 浏览器支持现状

截至 2025 年，WebGPU 在 Chrome、Edge 已稳定支持，Safari 和 Firefox 也在逐步跟进。检测方法：

```javascript
async function initWebGPU() {
  if (!navigator.gpu) {
    console.error('WebGPU not supported');
    return null;
  }
  
  const adapter = await navigator.gpu.requestAdapter({
    powerPreference: 'high-performance',
  });
  
  if (!adapter) {
    console.error('No suitable GPU adapter');
    return null;
  }
  
  const device = await adapter.requestDevice();
  const canvas = document.querySelector('canvas');
  const context = canvas.getContext('webgpu');
  const format = navigator.gpu.getPreferredCanvasFormat();
  
  context.configure({
    device,
    format,
    alphaMode: 'premultiplied',
  });
  
  return { device, context, format };
}
```

> 金句：WebGL 是"打电话"——每句话立刻传达；WebGPU 是"写信"——先写好信，统一寄出。

## 13.2 核心对象模型

### 13.2.1 Adapter 与 Device

**Adapter** 代表一个物理 GPU 设备：

```javascript
const adapter = await navigator.gpu.requestAdapter({
  powerPreference: 'high-performance',
  // 可选：'low-power'（省电模式）
});

// 查询适配器信息
const info = await adapter.requestAdapterInfo();
console.log(info.vendor, info.architecture, info.device);
```

**Device** 是逻辑 GPU 设备，是你在 WebGPU 中的主入口：

```javascript
const device = await adapter.requestDevice({
  requiredFeatures: ['texture-compression-bc'],
  requiredLimits: {
    maxBufferSize: 1 << 30,        // 1 GB
    maxTextureDimension2D: 8192,
  },
});

// 设备丢失处理
device.lost.then((info) => {
  console.error('Device lost:', info.reason, info.message);
});
```

### 13.2.2 Pipeline：渲染管线对象

WebGPU 的渲染管线是一个预创建的对象，包含着色器、顶点布局、混合状态等所有不可变状态：

```javascript
const pipeline = device.createRenderPipeline({
  layout: 'auto',  // 自动推导布局
  
  vertex: {
    module: shaderModule,
    entryPoint: 'vs_main',
    buffers: [{
      arrayStride: 6 * 4,  // 每顶点 6 个 float
      attributes: [
        { shaderLocation: 0, offset: 0, format: 'float32x3' },      // 位置
        { shaderLocation: 1, offset: 3 * 4, format: 'float32x3' },  // 颜色
      ],
    }],
  },
  
  fragment: {
    module: shaderModule,
    entryPoint: 'fs_main',
    targets: [{
      format: presentationFormat,  // 与 canvas 格式匹配
    }],
  },
  
  primitive: {
    topology: 'triangle-list',
    cullMode: 'back',  // 背面剔除
  },
  
  depthStencil: {
    format: 'depth24plus',
    depthWriteEnabled: true,
    depthCompare: 'less',
  },
});
```

**和 WebGL 的关键区别**：WebGL 中渲染状态是全局的，每次绘制前设置；WebGPU 中渲染状态打包成 Pipeline 对象，创建后不可变，绘制时直接绑定。

### 13.2.3 Buffer 与 Texture

```javascript
// 创建 Buffer
const vertexBuffer = device.createBuffer({
  size: vertices.byteLength,
  usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST,
});

// 上传数据
device.queue.writeBuffer(vertexBuffer, 0, vertices);

// 创建 Texture
const texture = device.createTexture({
  size: [width, height],
  format: 'rgba8unorm',
  usage: GPUTextureUsage.TEXTURE_BINDING |
         GPUTextureUsage.COPY_DST |
         GPUTextureUsage.RENDER_ATTACHMENT,
});

// 上传纹理数据
device.queue.writeTexture(
  { texture },
  imageData,
  { bytesPerRow: width * 4 },
  { width, height }
);
```

### 13.2.4 BindGroup：资源绑定组

BindGroup 是 WebGPU 最具创新性的设计之一。它将着色器需要的资源（uniform、纹理、采样器）打包成组，绑定时一次性设置：

```javascript
// 创建 BindGroup Layout（通常由 pipeline 自动推导）
const bindGroupLayout = pipeline.getBindGroupLayout(0);

// 创建 BindGroup
const bindGroup = device.createBindGroup({
  layout: bindGroupLayout,
  entries: [
    { binding: 0, resource: { buffer: uniformBuffer } },        // Uniform Buffer
    { binding: 1, resource: textureView },                      // Texture View
    { binding: 2, resource: sampler },                          // Sampler
  ],
});

// 渲染时绑定
passEncoder.setBindGroup(0, bindGroup);
```

**和 WebGL 的对比**：

```
WebGL（逐个绑定）：              WebGPU（分组绑定）：
gl.useProgram(program)            passEncoder.setPipeline(pipeline)
gl.bindBuffer(ARRAY_BUFFER, vbo)  passEncoder.setVertexBuffer(0, vbo)
gl.bindTexture(TEXTURE_2D, tex)   passEncoder.setBindGroup(0, bindGroup)
gl.uniformMatrix4fv(...)          // 所有资源在 BindGroup 中一次性绑定
gl.activeTexture(TEXTURE0)
gl.uniform1i(texLoc, 0)
```

> 金句：WebGL 绑定资源像"一个个排队进场"，WebGPU 用 BindGroup 像"团队整体入场"——更少的状态切换，更高的效率。

## 13.3 WGSL 着色器语言

### 13.3.1 WGSL 与 GLSL 的语法对比

WGSL（WebGPU Shading Language）是 WebGPU 的专用着色器语言，比 GLSL 更现代、更安全。

**基本类型对比**：

| GLSL | WGSL | 说明 |
|------|------|------|
| float | f32 | 32 位浮点 |
| int | i32 | 32 位有符号整数 |
| vec2/vec3/vec4 | vec2f/vec3f/vec4f | 浮点向量 |
| mat4 | mat4x4f | 4x4 浮点矩阵 |
| sampler2D | sampler + texture_2d | 纹理采样拆分为两个对象 |
| attribute | @location(n) | 顶点输入 |
| varying | @location(n) | 顶点→片元传递 |
| gl_Position | @builtin(position) | 内置输出 |
| gl_FragColor | @location(0) | 片元输出 |

**着色器对比**：

```glsl
// GLSL（WebGL）
attribute vec3 aPosition;
attribute vec3 aColor;
uniform mat4 uMVP;
varying vec3 vColor;

void main() {
  gl_Position = uMVP * vec4(aPosition, 1.0);
  vColor = aColor;
}
```

```wgsl
// WGSL（WebGPU）
struct VertexInput {
  @location(0) position: vec3f,
  @location(1) color: vec3f,
}

struct VertexOutput {
  @builtin(position) clip_position: vec4f,
  @location(0) color: vec3f,
}

@group(0) @binding(0) var<uniform> mvp: mat4x4f;

@vertex
fn vs_main(input: VertexInput) -> VertexOutput {
  var output: VertexOutput;
  output.clip_position = mvp * vec4f(input.position, 1.0);
  output.color = input.color;
  return output;
}

@fragment
fn fs_main(input: VertexOutput) -> @location(0) vec4f {
  return vec4f(input.color, 1.0);
}
```

### 13.3.2 WGSL 的入口函数与资源声明

WGSL 用属性（Attribute）标注入口函数和资源绑定：

```wgsl
// 顶点着色器入口
@vertex
fn vs_main(...) -> ... { }

// 片元着色器入口
@fragment
fn fs_main(...) -> ... { }

// 计算着色器入口
@compute
fn cs_main(...) -> ... { }

// 资源声明
@group(0) @binding(0) var<uniform> mvp: mat4x4f;        // Uniform
@group(0) @binding(1) var tex: texture_2d<f32>;          // 纹理
@group(0) @binding(2) var samp: sampler;                  // 采样器
@group(0) @binding(3) var<storage, read> data: array<f32>; // Storage Buffer
```

### 13.3.3 内置函数对照表

| 功能 | GLSL | WGSL |
|------|------|------|
| 纹理采样 | texture2D(tex, uv) | textureSample(tex, samp, uv) |
| 纹理加载 | texelFetch(tex, ivec2, lod) | textureLoad(tex, vec2u, lod) |
| 归一化 | normalize(v) | normalize(v) |
| 点积 | dot(a, b) | dot(a, b) |
| 叉积 | cross(a, b) | cross(a, b) |
| 反射 | reflect(I, N) | reflect(I, N) |
| 折射 | refract(I, N, eta) | refract(I, N, eta) |
| 矩阵乘法 | M * v | M * v |
| 钳制 | clamp(x, min, max) | clamp(x, min, max) |
| 混合 | mix(a, b, t) | mix(a, b, t) |

> 金句：WGSL 的设计哲学是"安全优先"——没有隐式类型转换，没有未定义行为，编译阶段就能抓住大部分错误。

## 13.4 渲染流程

### 13.4.1 命令编码与提交

WebGPU 的渲染分三步：编码命令 → 提交队列 → 呈现。

```javascript
function render(device, context, pipeline, vertexBuffer, bindGroup) {
  // 1. 获取当前帧的纹理视图
  const view = context.getCurrentTexture().createView();
  
  // 2. 创建命令编码器
  const encoder = device.createCommandEncoder();
  
  // 3. 创建渲染通道编码器
  const passEncoder = encoder.beginRenderPass({
    colorAttachments: [{
      view: view,
      clearValue: { r: 0, g: 0, b: 0, a: 1 },
      loadOp: 'clear',
      storeOp: 'store',
    }],
    depthStencilAttachment: {
      view: depthTextureView,
      depthClearValue: 1.0,
      depthLoadOp: 'clear',
      depthStoreOp: 'store',
    },
  });
  
  // 4. 编码绘制命令
  passEncoder.setPipeline(pipeline);
  passEncoder.setVertexBuffer(0, vertexBuffer);
  passEncoder.setBindGroup(0, bindGroup);
  passEncoder.draw(vertexCount, 1, 0, 0);
  
  // 5. 结束渲染通道
  passEncoder.end();
  
  // 6. 编码器完成，生成命令缓冲
  const commandBuffer = encoder.finish();
  
  // 7. 提交到 GPU 队列
  device.queue.submit([commandBuffer]);
  
  // 8. 呈现（自动，由 canvas context 处理）
  context.present();  // 在某些实现中是隐式的
}
```

**流程图**：

```
CommandEncoder
    │
    ├── beginRenderPass()
    │       │
    │       ├── setPipeline()
    │       ├── setVertexBuffer()
    │       ├── setBindGroup()
    │       ├── draw() / drawIndexed()
    │       │
    │       └── end()
    │
    ├── [beginComputePass() ... end()]  (可选)
    │
    └── finish() → CommandBuffer
                        │
                        ▼
              device.queue.submit([commandBuffer])
```

### 13.4.2 第一个 WebGPU 三角形

完整代码：

```javascript
async function init() {
  // 1. 初始化
  const adapter = await navigator.gpu.requestAdapter();
  const device = await adapter.requestDevice();
  const canvas = document.querySelector('canvas');
  const context = canvas.getContext('webgpu');
  const format = navigator.gpu.getPreferredCanvasFormat();
  context.configure({ device, format });
  
  // 2. 着色器
  const shaderModule = device.createShaderModule({
    code: `
      struct VertexOutput {
        @builtin(position) clip_position: vec4f,
        @location(0) color: vec3f,
      }
      
      @vertex
      fn vs_main(
        @location(0) position: vec3f,
        @location(1) color: vec3f
      ) -> VertexOutput {
        var output: VertexOutput;
        output.clip_position = vec4f(position, 1.0);
        output.color = color;
        return output;
      }
      
      @fragment
      fn fs_main(input: VertexOutput) -> @location(0) vec4f {
        return vec4f(input.color, 1.0);
      }
    `,
  });
  
  // 3. Pipeline
  const pipeline = device.createRenderPipeline({
    layout: 'auto',
    vertex: {
      module: shaderModule,
      entryPoint: 'vs_main',
      buffers: [{
        arrayStride: 6 * 4,
        attributes: [
          { shaderLocation: 0, offset: 0, format: 'float32x3' },
          { shaderLocation: 1, offset: 12, format: 'float32x3' },
        ],
      }],
    },
    fragment: {
      module: shaderModule,
      entryPoint: 'fs_main',
      targets: [{ format }],
    },
    primitive: { topology: 'triangle-list' },
  });
  
  // 4. 顶点数据
  const vertices = new Float32Array([
     0.0,  0.5, 0.0,  1.0, 0.0, 0.0,
    -0.5, -0.5, 0.0,  0.0, 1.0, 0.0,
     0.5, -0.5, 0.0,  0.0, 0.0, 1.0,
  ]);
  const vertexBuffer = device.createBuffer({
    size: vertices.byteLength,
    usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST,
  });
  device.queue.writeBuffer(vertexBuffer, 0, vertices);
  
  // 5. 渲染
  function frame() {
    const encoder = device.createCommandEncoder();
    const pass = encoder.beginRenderPass({
      colorAttachments: [{
        view: context.getCurrentTexture().createView(),
        clearValue: { r: 0, g: 0, b: 0, a: 1 },
        loadOp: 'clear',
        storeOp: 'store',
      }],
    });
    pass.setPipeline(pipeline);
    pass.setVertexBuffer(0, vertexBuffer);
    pass.draw(3);
    pass.end();
    device.queue.submit([encoder.finish()]);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
init();
```

## 13.5 计算着色器

### 13.5.1 GPU 通用计算的原理

计算着色器（Compute Shader）允许你在 GPU 上执行通用计算，不仅限于图形渲染。GPU 有数千个并行计算单元，适合大规模并行任务。

```
CPU 计算（串行）：          GPU 计算（并行）：
任务1 → 任务2 → 任务3       任务1 │
                            任务2 │ 同时执行
                            任务3 │
                            ...  │
                            任务N │
```

### 13.5.2 Workgroup 与 Dispatch

计算着色器以 Workgroup 为单位执行。每个 Workgroup 包含多个-invocation（调用），通常组织成 3D 结构：

```javascript
// 计算着色器 Pipeline
const computePipeline = device.createComputePipeline({
  layout: 'auto',
  compute: {
    module: computeShaderModule,
    entryPoint: 'cs_main',
  },
});

// Dispatch：启动计算
const passEncoder = encoder.beginComputePass();
passEncoder.setPipeline(computePipeline);
passEncoder.setBindGroup(0, computeBindGroup);
// workgroup_count_x, workgroup_count_y, workgroup_count_z
passEncoder.dispatchWorkgroups(64, 64, 1);
passEncoder.end();
```

```wgsl
@compute
@workgroup_size(8, 8, 1)  // 每个 Workgroup 8x8x1 = 64 个 invocation
fn cs_main(
  @builtin(global_invocation_id) gid: vec3u,
) {
  // gid.x 范围 [0, 64*8-1] = [0, 511]
  // gid.y 范围 [0, 64*8-1] = [0, 511]
  // 每个 invocation 处理一个像素
  
  let index = gid.y * 512 + gid.x;
  // 在 storage buffer 中读写数据
  outputData[index] = inputData[index] * 2.0;
}
```

### 13.5.3 实战：用计算着色器处理 ImageData

```javascript
// 在 GPU 上做图像模糊
const computeShader = device.createShaderModule({
  code: `
    @group(0) @binding(0) var<storage, read> input: array<u32>;
    @group(0) @binding(1) var<storage, read_write> output: array<u32>;
    
    @compute
    @workgroup_size(8, 8)
    fn blur(
      @builtin(global_invocation_id) gid: vec3u,
    ) {
      let width = 512u;
      let height = 512u;
      if (gid.x >= width || gid.y >= height) { return; }
      
      let idx = gid.y * width + gid.x;
      var sum = vec4u(0);
      var count = 0u;
      
      // 3x3 模糊
      for (var dy = -1; dy <= 1; dy++) {
        for (var dx = -1; dx <= 1; dx++) {
          let nx = i32(gid.x) + dx;
          let ny = i32(gid.y) + dy;
          if (nx >= 0 && nx < i32(width) && ny >= 0 && ny < i32(height)) {
            let nidx = u32(ny) * width + u32(nx);
            let pixel = input[nidx];
            sum += vec4u(
              (pixel >> 0) & 0xFF,
              (pixel >> 8) & 0xFF,
              (pixel >> 16) & 0xFF,
              (pixel >> 24) & 0xFF
            );
            count += 1u;
          }
        }
      }
      
      let avg = sum / vec4u(count);
      output[idx] = avg.r | (avg.g << 8) | (avg.b << 16) | (avg.a << 24);
    }
  `,
});
```

> 金句：计算着色器把 GPU 从"画画工具"变成了"超级计算器"——图像处理、物理模拟、AI 推理，都可以在 GPU 上跑。

## 13.6 WebGPU vs WebGL 选型建议

| 维度 | WebGL | WebGPU |
|------|-------|--------|
| 浏览器支持 | 全部主流 | Chrome/Edge 稳定，Safari/Firefox 跟进中 |
| 性能 | 好 | 更好（更低开销） |
| 着色器语言 | GLSL | WGSL |
| 计算着色器 | 不支持 | 支持 |
| 学习曲线 | 陡（状态机模型） | 中等（显式模型） |
| 生态/框架 | Three.js/Babylon.js 等 | Three.js(WebGPU)/Babylon.js 支持 |
| 项目建议 | 需要广泛兼容性 | 新项目、需要计算着色器 |

**建议**：
- 现有项目维持 WebGL，不急于迁移
- 新项目如果不需要兼容旧浏览器，直接用 WebGPU
- 需要计算着色器的场景（GPGPU），WebGPU 是唯一选择
- Three.js 和 Babylon.js 都已支持 WebGPU 后端，框架层面切换成本低

## 13.7 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| WebGPU 本质 | 基于 Vulkan/Metal/D3D12 的新 Web 图形 API |
| Adapter/Device | Adapter=物理 GPU，Device=逻辑设备 |
| Pipeline | 预创建的不可变渲染管线对象 |
| BindGroup | 资源绑定组，一次性绑定多个资源 |
| WGSL | WebGPU 着色器语言，安全优先，无隐式转换 |
| 命令编码 | CommandEncoder → RenderPass → submit |
| 计算着色器 | GPU 通用计算，Workgroup 为单位并行执行 |
| vs WebGL | 性能更好、支持计算着色器、显式模型更清晰 |

觉得有用？收藏起来，WebGPU 是未来。

你对 WebGPU 有什么疑问？或者已经在用了？评论区聊聊。

关注怕浪猫，下期我们讲 **引擎生态**——Konva、Fabric.js、PixiJS、Three.js 等框架的选型指南。

系列进度 13/17

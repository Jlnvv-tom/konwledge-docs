# Canvas 工程全书

> 从浏览器渲染原理到 3D 图形管线，一本覆盖 Canvas 全貌的工程级教程

---

## 前言

- [序言：为什么写这本书](./preface/why-this-book.md)
- [读者对象与阅读指南](./preface/who-should-read.md)
- [术语表](./preface/glossary.md)

---

## 第一部分：基石 — Canvas 在浏览器中的位置

### 第 1 章 浏览器图形渲染全景

- 1.1 浏览器渲染管线回顾：从 HTML 到像素
  - 1.1.1 DOM 树与 CSSOM 树的构建
  - 1.1.2 布局（Layout）与绘制（Paint）
  - 1.1.3 合成层（Compositing Layer）与 GPU 加速
- 1.2 图形 API 在浏览器中的演进史
  - 1.2.1 早期方案：VML 与 Flash 时代
  - 1.2.2 Canvas 2D Context 的诞生（HTML5 规范）
  - 1.2.3 WebGL：把 GPU 带进浏览器
  - 1.2.4 WebGPU：下一代图形 API
- 1.3 浏览器中的"画布"到底挂在渲染树的哪个节点？
  - 1.3.1 `<canvas>` 元素的 DOM 定位
  - 1.3.2 Canvas 与周围文档流的排版关系
  - 1.3.3 Canvas 的合成层提升条件
- 1.4 从 `<canvas>` 标签到屏幕像素：一次完整的数据流
  - 1.4.1 元素属性解析（width/height vs CSS 宽高）
  - 1.4.2 上下文（Context）的获取与初始化
  - 1.4.3 绘图命令队列与刷新机制
  - 1.4.4 后缓冲区（Back Buffer）与页面合成

### 第 2 章 Canvas 核心原理：上下文、像素与状态机

- 2.1 Canvas 元素的本质
  - 2.1.1 `<canvas>` 的物理模型：一块可编程的位图
  - 2.1.2 画布的分辨率： backing store 与 CSS 像素
  - 2.1.3 设备像素比（DPR）与高分屏适配
- 2.2 上下文（Context）机制
  - 2.2.1 `getContext('2d')` — 2D 位图绘制上下文
  - 2.2.2 `getContext('webgl')` / `getContext('webgl2')` — GPU 上下文
  - 2.2.3 `getContext('bitmaprenderer')` — ImageBitmap 渲染上下文
  - 2.2.4 上下文的生命周期与丢失恢复
- 2.3 2D Context 的状态机模型
  - 2.3.1 绘图状态栈（Drawing State Stack）
  - 2.3.2 `save()` / `restore()` 的本质：状态快照入栈与出栈
  - 2.3.3 变换矩阵（Transformation Matrix）的叠加原理
  - 2.3.4 裁剪区域（Clipping Region）的状态传递
- 2.4 像素操作底层
  - 2.4.1 ImageData 结构：Uint8ClampedArray 的含义
  - 2.4.2 `getImageData()` / `putImageData()` 的性能特征
  - 2.4.3 预乘 Alpha（Premultiplied Alpha）的坑
  - 2.4.4 跨域（CORS）与画布污染（Tainted Canvas）

### 第 3 章 Canvas 与 SVG：位图与矢量的两条道路

- 3.1 渲染范式对比
  - 3.1.1 Canvas：即时模式（Immediate Mode）绘制
  - 3.1.2 SVG：保留模式（Retained Mode）绘制
  - 3.1.3 即时模式 vs 保留模式的工程权衡
- 3.2 数据结构差异
  - 3.2.1 Canvas 的像素缓冲区 vs SVG 的 DOM 节点树
  - 3.2.2 事件系统的本质区别：无 vs 原生 DOM 事件
  - 3.2.3 可访问性（a11y）：Canvas 的盲区与 SVG 的天然优势
- 3.3 性能特征对比
  - 3.3.1 元素数量与性能曲线：Canvas 的 O(1) vs SVG 的 O(n)
  - 3.3.2 动画策略：requestAnimationFrame + 重绘 vs CSS/DOM 动画
  - 3.3.3 内存占用模型对比
  - 3.3.4 渲染瓶颈定位：CPU 绘制 vs DOM reflow/repaint
- 3.4 适用场景决策矩阵
  - 3.4.1 何时选 Canvas：高频重绘、海量图元、像素级控制
  - 3.4.2 何时选 SVG：交互密集、可访问性要求、可缩制缩放
  - 3.4.3 混合方案：SVG 做交互层 + Canvas 做绘制层
- 3.5 从 SVG 迁移到 Canvas（或反向）的工程经验

---

## 第二部分：画布系统 — 2D 绘制的工程化

### 第 4 章 画布系统总论

- 4.1 什么是"画布系统"
  - 4.1.1 狭义画布：单个 `<canvas>` 元素
  - 4.1.2 广义画布：多画布协同的渲染架构
  - 4.1.3 画布系统在可视化/编辑器/游戏中的角色定位
- 4.2 画布坐标系
  - 4.2.1 屏幕坐标系（左上原点，Y 向下）
  - 4.2.2 笛卡尔坐标系的转换
  - 4.2.3 视口（Viewport）与世界坐标（World Coordinate）
  - 4.2.4 坐标变换的矩阵运算
- 4.3 画布的生命周期管理
  - 4.3.1 创建与销毁
  - 4.3.2 尺寸变更与重绘策略
  - 4.3.3 ResizeObserver 监听画布容器变化
  - 4.3.4 画布的持久化：toDataURL / toBlob / captureStream

### 第 5 章 绘制原语与路径系统

- 5.1 基本图形绘制
  - 5.1.1 矩形：fillRect / strokeRect / clearRect
  - 5.1.2 文本：fillText / strokeText 与字体度量
  - 5.1.3 图片：drawImage 的三种重载与缩放策略
- 5.2 路径（Path）系统
  - 5.2.1 Path2D 对象：可复用的路径描述
  - 5.2.2 子路径（Subpath）与闭合（Close Path）
  - 5.2.3 贝塞尔曲线：二次与三次的数学原理
  - 5.2.4 圆弧与椭圆弧
  - 5.2.5 路径填充规则：nonzero vs evenodd
- 5.3 线条样式与端点
  - 5.3.1 lineWidth / lineCap / lineJoin
  - 5.3.2 虚线 setLineDash 与 dashOffset 动画
- 5.4 渐变与图案
  - 5.4.1 线性渐变与径向渐变
  - 5.4.2 Conic 渐变（圆锥渐变）
  - 5.4.3 Pattern 图案填充与重复模式

### 第 6 章 变换、合成与滤镜

- 6.1 坐标变换
  - 6.1.1 translate / rotate / scale 的矩阵复合
  - 6.1.2 setTransform / resetTransform 的绝对设置
  - 6.1.3 仿射变换矩阵 [a, b, c, d, e, f] 的含义
- 6.2 合成模式（Compositing）
  - 6.2.1 globalAlpha 与 globalCompositeOperation
  - 6.2.2 Porter-Duff 合成运算族
  - 6.2.3 混合模式（Blend Mode）：multiply / screen / overlay 等
  - 6.2.4 `source-over` vs `destination-over` 的工程应用
- 6.3 滤镜（Filter）
  - 6.3.1 `ctx.filter` 属性与 CSS filter 函数映射
  - 6.3.2 模糊、锐化、色彩调整
  - 6.3.3 自定义卷积核（通过 ImageData 实现）

### 第 7 章 图层系统

- 7.1 为什么需要图层
  - 7.1.1 单画布的痛点：整体重绘的代价
  - 7.1.2 图层的核心思想：分离绘制与合成
  - 7.1.3 图层在图形软件中的历史（Photoshop / Figma / Sketch）
- 7.2 多画布图层架构
  - 7.2.1 叠加多个 `<canvas>` 元素的 DOM 布局
  - 7.2.2 静态层与动态层分离策略
  - 7.2.3 图层的 z-index 管理与合成顺序
  - 7.2.4 实战：背景层 + 内容层 + 交互层的三层架构
- 7.3 离屏画布（OffscreenCanvas）
  - 7.3.1 OffscreenCanvas API 概述
  - 7.3.2 主线程 vs Worker 线程的画布使用
  - 7.3.3 transferControlToOffscreen 的原理
  - 7.3.4 Worker 中绘制 → 主线程合成的性能优势
- 7.4 图层的数据模型
  - 7.4.1 图层描述对象：bounds / opacity / visible / blendMode
  - 7.4.2 图层树（Layer Tree）的序列化与反序列化
  - 7.4.3 图层的脏矩形（Dirty Rectangle）重绘优化
- 7.5 图层与合成的关系
  - 7.5.1 逐层绘制到离屏缓冲再合成
  - 7.5.2 混合模式在图层间的应用
  - 7.5.3 蒙版（Mask）与剪裁路径的图层级实现

---

## 第三部分：动画与交互

### 第 8 章 Canvas 动画系统

- 8.1 动画基础
  - 8.1.1 requestAnimationFrame 与浏览器刷新率
  - 8.1.2 帧率（FPS）监控与 Delta Time 计算
  - 8.1.3 固定时间步长 vs 可变时间步长
- 8.2 动画编排
  - 8.2.1 补间动画（Tween）与缓动函数（Easing）
  - 8.2.2 关键帧动画
  - 8.2.3 动画时间线（Timeline）管理
  - 8.2.4 动画分组与并行/串行控制
- 8.3 物理动画
  - 8.3.1 基础运动学：速度、加速度、阻尼
  - 8.3.2 弹簧物理模型
  - 8.3.3 粒子系统基础

### 第 9 章 Canvas 交互系统

- 9.1 命中检测（Hit Testing）
  - 9.1.1 几何命中检测：点-矩形、点-圆形、点-多边形
  - 9.1.2 isPointInPath / isPointInStroke
  - 9.1.3 空间索引加速：四叉树（Quadtree）与网格法
- 9.2 事件系统设计
  - 9.2.1 将 DOM 事件映射到画布坐标
  - 9.2.2 事件冒泡与捕获在画布中的模拟
  - 9.2.3 拖拽（Drag & Drop）的实现模式
  - 9.2.4 手势识别：缩放、旋转、平移
- 9.3 对象选择与高亮
  - 9.3.1 选中框（Bounding Box）与控制点
  - 9.3.2 多选与框选
  - 9.3.3 键盘修饰键的处理

---

## 第四部分：3D 渲染 — 从 WebGL 到 WebGPU

### 第 10 章 3D 渲染管线总论

- 10.1 为什么 Canvas 2D 无法做真正的 3D
  - 10.1.1 2D 上下文的局限：无深度缓冲、无着色器
  - 10.1.2 用 2D 模拟 3D 的方法与天花板
- 10.2 GPU 渲染管线全景图
  - 10.2.1 应用阶段（CPU 侧）：准备几何数据与 Draw Call
  - 10.2.2 几何阶段（Vertex Processing）
    - 10.2.2.1 顶点着色器（Vertex Shader）
    - 10.2.2.2 图元装配（Primitive Assembly）
    - 10.2.2.3 裁剪（Clipping）与视口变换（Viewport Transform）
  - 10.2.3 光栅化阶段（Rasterization）
    - 10.2.3.1 三角形遍历与片元生成
    - 10.2.3.2 片元着色器（Fragment Shader）
  - 10.2.4 逐片元操作（Per-Fragment Operations）
    - 10.2.4.1 深度测试（Depth Test）
    - 10.2.4.2 模板测试（Stencil Test）
    - 10.2.4.3 混合（Blending）
- 10.3 坐标空间变换链
  - 10.3.1 模型空间（Model Space）→ 世界空间（World Space）
  - 10.3.2 世界空间 → 观察空间（View/Camera Space）
  - 10.3.3 观察空间 → 裁剪空间（Clip Space）
  - 10.3.4 裁剪空间 → 屏幕空间（Screen Space）
  - 10.3.5 透视投影与正交投影矩阵
- 10.4 渲染方程与光照模型简述
  - 10.4.1 局部光照模型：Phong / Blinn-Phong
  - 10.4.2 全局光照概念：光线追踪 vs 光栅化
  - 10.4.3 PBR（基于物理的渲染）基础

### 第 11 章 WebGL 基础

- 11.1 WebGL 是什么
  - 11.1.1 OpenGL ES 在浏览器中的映射
  - 11.1.2 WebGL 1.0 vs WebGL 2.0 的差异
  - 11.1.3 WebGL 上下文获取与上下文丢失处理
- 11.2 着色器（Shader）
  - 11.2.1 GLSL 语法精要
  - 11.2.2 顶点着色器编写
  - 11.2.3 片元着色器编写
  - 11.2.4 着色器编译、链接与程序对象
- 11.3 缓冲区与纹理
  - 11.3.1 VBO（Vertex Buffer Object）与顶点属性
  - 11.3.2 IBO（Index Buffer Object）与索引绘制
  - 11.3.3 纹理对象与采样器（Sampler）
  - 11.3.4 纹理过滤：最近邻 vs 线性 vs Mipmap
  - 11.3.5 纹理包装模式：REPEAT / CLAMP_TO_EDGE / MIRRORED_REPEAT
- 11.4 第一个三角形：完整 WebGL 渲染流程
  - 11.4.1 创建几何数据
  - 11.4.2 编写着色器
  - 11.4.3 设置缓冲区与属性
  - 11.4.4 设置 Uniform 变量
  - 11.4.5 发出 Draw Call 并呈现
- 11.5 WebGL 状态机模型
  - 11.5.1 WebGL 的全局状态集
  - 11.5.2 状态切换的性能成本
  - 11.5.3 状态排序（State Sorting）优化

### 第 12 章 WebGL 进阶

- 12.1 深度缓冲与面剔除
  - 12.1.1 深度缓冲区（Depth Buffer / Z-Buffer）原理
  - 12.1.2 深度冲突（Z-Fighting）的成因与解决
  - 12.1.3 背面剔除（Face Culling）：CW vs CCW
- 12.2 光照实战
  - 12.2.1 法线（Normal）与法线矩阵
  - 12.2.2 环境光 + 漫反射 + 镜面反射
  - 12.2.3 多光源与光照衰减
  - 12.2.4 Phong 着色（逐片元）vs Gouraud 着色（逐顶点）
- 12.3 纹理进阶
  - 12.3.1 多重纹理（Multitexturing）
  - 12.3.2 法线贴图（Normal Mapping）
  - 12.3.3 环境贴图（Environment Mapping）与立方体映射
  - 12.3.4 阴影贴图（Shadow Mapping）
- 12.4 帧缓冲区（Framebuffer Object, FBO）
  - 12.4.1 离屏渲染的概念
  - 12.4.2 创建 FBO 并附加颜色/深度附件
  - 12.4.3 后处理（Post-Processing）：泛光、色调映射、屏幕空间反射
- 12.5 性能优化
  - 12.5.1 Draw Call 合并
  - 12.5.2 实例化渲染（Instanced Rendering, WebGL2）
  - 12.5.3 视锥剔除（Frustum Culling）
  - 12.5.4 LOD（Level of Detail）
  - 12.5.5 GPU 性能分析工具

### 第 13 章 WebGPU：下一代图形 API

- 13.1 WebGPU 的设计动机
  - 13.1.1 WebGL 的历史包袱与局限
  - 13.1.2 现代图形 API（Vulkan / Metal / D3D12）的理念
  - 13.1.3 WebGPU 如何映射到底层图形 API
- 13.2 WebGPU 核心概念
  - 13.2.1 Adapter 与 Device
  - 13.2.2 管线（Pipeline）：RenderPipeline / ComputePipeline
  - 13.2.3 着色器语言：WGSL（WebGPU Shading Language）
  - 13.2.4 资源绑定模型：BindGroup 与 BindGroupLayout
  - 13.2.5 命令编码（Command Encoding）与提交
- 13.3 WebGPU 相比 WebGL 的优势
  - 13.3.1 计算着色器（Compute Shader）原生支持
  - 13.3.2 显式同步与资源屏障
  - 13.3.3 更低的 CPU 开销
- 13.4 WebGPU 实战：绘制一个三角形
  - 13.4.1 初始化 Device 与 SwapChain
  - 13.4.2 编写 WGSL 着色器
  - 13.4.3 创建管线与顶点缓冲
  - 13.4.4 渲染通道（Render Pass）编码与提交

---

## 第五部分：工程实践与生态

### 第 14 章 Canvas 引擎与框架生态

- 14.1 2D 引擎
  - 14.1.1 Konva.js：图层与节点的舞台模型
  - 14.1.2 Fabric.js：面向富交互的 Canvas 库
  - 14.1.3 PixiJS：高性能 2D 渲染器（WebGL 优先）
  - 14.1.4 EaselJS / CreateJS 全家桶
  - 14.1.5 ZRender（ECharts 底层渲染器）
- 14.2 3D 引擎
  - 14.2.1 Three.js：最流行的 Web 3D 库
  - 14.2.2 Babylon.js：面向游戏的完整引擎
  - 14.2.3 PlayCanvas：云端协作引擎
  - 14.2.4 Filament：Google 的 PBR 渲染库
- 14.3 可视化框架
  - 14.3.1 D3.js 与 Canvas 的结合
  - 14.3.2 ECharts / Chart.js / G2 的 Canvas 渲染层
  - 14.3.3 Deck.gl：大规模地理空间可视化
- 14.4 游戏框架
  - 14.4.1 Phaser：2D 游戏引擎
  - 14.4.2 Cocos Creator 的 Canvas 渲染管线
  - 14.4.3 Egret 引擎

### 第 15 章 性能优化体系

- 15.1 性能度量
  - 15.1.1 FPS 监控与帧时间分布
  - 15.1.2 Chrome DevTools Performance 面板使用
  - 15.1.3 GPU 分析：Spector.js 与 RenderDoc
- 15.2 2D Canvas 优化策略
  - 15.2.1 避免频繁状态切换
  - 15.2.2 精灵图（Sprite Sheet）与图集（Atlas）
  - 15.2.3 脏矩形重绘
  - 15.2.4 分层渲染减少重绘范围
  - 15.2.5 预渲染到离屏画布
  - 15.2.6 文本绘制优化
- 15.3 WebGL 优化策略
  - 15.3.1 批处理（Batching）与减少 Draw Call
  - 15.3.2 纹理图集（Texture Atlas）
  - 15.3.3 顶点数据压缩
  - 15.3.4 异步资源加载与渐进式渲染
- 15.4 内存管理
  - 15.4.1 画布内存的生命周期
  - 15.4.2 纹理内存预算与释放
  - 15.4.3 ImageData 与 TypedArray 的内存复用

### 第 16 章 Canvas 与其他 Web 技术的协作

- 16.1 Canvas + CSS
  - 16.1.1 CSS 滤镜与 Canvas 滤镜的协作
  - 16.1.2 CSS 变换作用于 Canvas 元素
  - 16.1.3 mix-blend-mode 跨元素混合
- 16.2 Canvas + SVG
  - 16.2.1 SVG 作为 Canvas 图像源
  - 16.2.2 Canvas 输出为 SVG（通过中间格式）
  - 16.2.3 SVG 覆盖层做交互 + Canvas 做渲染
- 16.3 Canvas + Video
  - 16.3.1 从 video 元素抓帧到 canvas
  - 16.3.2 实时视频处理与滤镜
  - 16.3.3 captureStream() 与录制
- 16.4 Canvas + Web Audio
  - 16.4.1 频谱可视化
  - 16.4.2 波形渲染
- 16.5 Canvas + Web Workers
  - 16.5.1 OffscreenCanvas 在 Worker 中运行
  - 16.5.2 ImageBitmap 跨线程传递
- 16.6 Canvas + AI/ML
  - 16.6.1 TensorFlow.js 与 Canvas 数据输入
  - 16.6.2 图像分割结果的叠加渲染
  - 16.6.3 人脸检测与标注

---

## 第六部分：附录与参考资料

### 附录 A 官方规范与技术网站

- A.1 W3C / WHATWG 规范
  - HTML Living Standard — Canvas 元素定义：<https://html.spec.whatwg.org/multipage/canvas.html>
  - W3C Canvas 2D Context Specification
- A.2 Khronos Group（WebGL / GLSL）
  - WebGL 1.0 规范：<https://www.khronos.org/registry/webgl/specs/latest/1.0/>
  - WebGL 2.0 规范：<https://www.khronos.org/registry/webgl/specs/latest/2.0/>
  - OpenGL ES 参考：<https://www.khronos.org/opengles/>
  - GLSL ES 规范：<https://www.khronos.org/registry/OpenGL/specs/es/>
- A.3 WebGPU / WGSL
  - W3C WebGPU 规范：<https://www.w3.org/TR/webgpu/>
  - WGSL 规范：<https://www.w3.org/TR/WGSL/>
  - WebGPU 开发者指南：<https://gpuweb.github.io/gpuweb/>
- A.4 MDN Web Docs
  - Canvas API 教程：<https://developer.mozilla.org/zh-CN/docs/Web/API/Canvas_API>
  - WebGL 教程：<https://developer.mozilla.org/zh-CN/docs/Web/API/WebGL_API>
  - WebGPU 文档：<https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API>
- A.5 社区与学习资源
  - WebGL Fundamentals：<https://webglfundamentals.org/>
  - Learn WebGL：<https://learnwebgl.brown37.net/>
  - Scratchapixel（渲染理论）：<https://www.scratchapixel.com/>
  - Three.js 官方文档与示例：<https://threejs.org/>
  - Babylon.js 文档：<https://doc.babylonjs.com/>
  - WebGPU Samples：<https://webgpu.github.io/webgpu-samples/>
  - Can I Use（兼容性查询）：<https://caniuse.com/>

### 附录 B Canvas 2D API 速查表

- B.1 上下文获取与配置
- B.2 绘制方法
- B.3 路径方法
- B.4 变换方法
- B.5 状态管理
- B.6 像素操作
- B.7 合成与滤镜

### 附录 C WebGL API 速查表

- C.1 上下文获取与配置
- C.2 着色器编译与链接
- C.3 缓冲区操作
- C.4 纹理操作
- C.5 帧缓冲区操作
- C.6 Uniform 与 Attribute
- C.7 绘制命令

### 附录 D 常见数学公式速查

- D.1 向量运算
- D.2 矩阵运算
- D.3 仿射变换矩阵
- D.4 透视投影矩阵
- D.5 四元数（Quaternion）
- D.6 缓动函数公式

### 附录 E 术语对照表

- 中英术语索引（Immediate Mode / Retained Mode / Rasterization / Fragment / Texel / etc.）

---

## 阅读路线建议

```
初学者：
  第1章 → 第2章 → 第3章 → 第4章 → 第5章 → 第8章 → 第9章

前端工程师进阶：
  第1章 → 第2章 → 第3章 → 第6章 → 第7章 → 第14章 → 第15章

3D 方向：
  第1章 → 第2章 → 第10章 → 第11章 → 第12章 → 第13章 → 第14章(3D)

架构师：
  全部
```

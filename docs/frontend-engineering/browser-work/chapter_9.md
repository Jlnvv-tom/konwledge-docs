---
sidebar_position: 9
---

# 第9章 绘制与合成

> 一个页面可能有几十个图层，GPU 把它们像叠胶片一样合成在一起。理解合成层的工作原理，你才能理解为什么 transform 动画比 top/left 动画快那么多。

我是怕浪猫，上期我们拆了 LayoutNG 布局引擎，今天进入第 9 章：绘制与合成。这一章会讲 PaintNG 绘制引擎如何生成绘制指令、合成层（Compositing Layer）的创建条件和提升机制、以及 GPU 合成的完整工作流程。

## 9.1 PaintNG 绘制引擎

### 9.1.1 从布局树到绘制记录

布局完成后，Blink 拥有一棵 Fragment 树，记录了每个元素的精确位置和尺寸。下一步是将这棵 Fragment 树转换为一系列绘制指令，这个过程叫做绘制（Paint）。

```
绘制流程

Fragment 树（布局结果）
  │
  ▼
绘制阶段1：构建绘制属性（Paint Properties）
  │  为每个 Fragment 计算变换、裁剪、效果等
  │  生成 PaintPropertyTree
  ▼
绘制阶段2：绘制遍历（Paint Traversal）
  │  按正确的顺序遍历 Fragment 树
  │  生成绘制操作列表（Paint Ops）
  ▼
绘制阶段3：光栅化（Rasterization）
  │  将绘制操作转换为像素
  │  在工作线程上并行执行
  ▼
最终像素
```

### 9.1.2 绘制顺序与 z-index

绘制顺序决定了元素在视觉上的层叠关系。Blink 的绘制顺序遵循 CSS 规范定义的「绘制上下文」（Painting Order）。

```
CSS 绘制顺序（从底到顶）

1. 背景色和背景图
2. 负 z-index 的定位元素
3. 块级元素的背景和边框
4. 浮动元素
5. 行内元素
6. 正 z-index 的定位元素

在每一层内，按以下顺序绘制单个元素：
  a. 背景色
  b. 背景图
  c. 边框
  d. 内容（文本、子元素）
```

z-index 只对 position 非 static 的元素生效。理解这一点很重要：两个 position: static 的元素，z-index 值没有意义。

| z-index 值 | 绘制位置 | 说明 |
|------------|---------|------|
| 负值 | 最底层 | 在所有其他内容之下 |
| auto/0 | 正常层 | 按文档顺序 |
| 正值 | 顶层 | 按值大小排序 |

### 9.1.3 绘制属性树

PaintNG 的一个关键创新是绘制属性树（Paint Property Tree）。它将元素的变换、裁剪、滚动、效果等信息提取为独立的属性节点，形成一棵树。

```
绘制属性树结构

Transform Tree（变换树）
  ├─ 根节点（视口变换）
  ├─ 元素 A 的 transform
  ├─ 元素 B 的 transform（父节点 = A 的 transform）
  └─ ...

Clip Tree（裁剪树）
  ├─ 根节点（视口裁剪）
  ├─ overflow: hidden 的裁剪
  └─ ...

Effect Tree（效果树）
  ├─ 根节点
  ├─ opacity 变化
  ├─ filter 效果
  └─ ...
```

绘制属性树的价值在于合成阶段。合成器可以直接使用属性树中的变换和裁剪信息，不需要重新从布局树计算。这也是为什么 transform 和 opacity 变化只需要合成阶段，不需要重新布局和绘制。

> 绘制属性树是 PaintNG 的核心创新。它把变换、裁剪、效果从绘制内容中分离出来，让合成器可以独立处理这些属性。这就是 CSS transform 动画不触发重排和重绘的底层原因。

### 9.1.4 绘制记录的生成

绘制遍历（Paint Traversal）过程中，PaintNG 按照正确的绘制顺序遍历 Fragment 树，为每个节点生成绘制操作（Paint Ops）。每个绘制操作是一个底层绘图指令，如「绘制矩形」「绘制文本」「绘制图片」。

```javascript
// 绘制记录示例（简化概念）
const paintOps = [
  { type: 'drawRect', x: 0, y: 0, w: 800, h: 600, color: '#fff' },
  { type: 'drawText', x: 10, y: 20, text: 'Hello', font: '16px Arial' },
  { type: 'drawRect', x: 10, y: 40, w: 100, h: 30, color: '#007bff' },
];
```

绘制记录列表是一个平台无关的指令序列，可以被光栅化引擎（CPU 或 GPU）执行。这种设计让绘制和光栅化解耦：同一个绘制记录可以在不同的光栅化后端上执行。

## 9.2 合成层（Compositing Layer）

### 9.2.1 什么是合成层

合成层（Compositing Layer，也叫 Compositor Layer）是 Chrome 渲染管线中的核心概念。每个合成层对应一个独立的位图，可以在 GPU 上独立变换和合成。

```
合成层结构示例

页面：
┌─────────────────────────────┐
│  背景层（body）              │ ← 合成层 0
│  ┌───────────────────────┐  │
│  │  内容层（div）         │  │ ← 合成层 1
│  │  ┌─────────────────┐  │  │
│  │  │  动画层（card）  │  │  │ ← 合成层 2（有 transform 动画）
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘

GPU 合成：
  Layer 0 (背景)  ──┐
  Layer 1 (内容)  ──┼── 合成 → 最终画面
  Layer 2 (动画)  ──┘  (在 GPU 上完成)
```

### 9.2.2 合成层提升条件

Blink 在什么情况下会将一个元素提升为独立的合成层？这个决策基于一系列条件。

| 提升条件 | 说明 | 常见原因 |
|---------|------|---------|
| 3D 变换 | transform: translate3d/rotate3d/matrix3d | 强制硬件加速 |
| will-change | will-change: transform/opacity | 开发者提示 |
| 透明度动画 | opacity 有动画 | 避免重绘 |
| transform 动画 | transform 有动画 | 避免重排重绘 |
| filter 动画 | filter 有动画 | 避免重绘 |
| position: fixed | 固定定位元素 | 滚动时独立合成 |
| 硬件加速视频 | video 元素 | 视频解码独立 |
| Canvas 2D/WebGL | canvas 元素 | 独立绘图表面 |
| 负 z-index 子树 | 有 3D 变换 | 层叠上下文 |

```css
/* 强制创建合成层 */
.gpu {
  transform: translateZ(0);  /* 或 translate3d(0,0,0) */
}

/* 更明确的提示 */
.optimized {
  will-change: transform;
}
```

### 9.2.3 层爆炸与层压缩

不合理的合成层创建可能导致「层爆炸」（Layer Explosion）：一个合成层的创建引发大量相邻元素也被提升为合成层，导致内存和 GPU 带宽暴增。

```
层爆炸示例

<div class="container">
  <div class="layer" style="transform: translateZ(0);">
    <!-- 容器变成合成层 -->
  </div>
  <!-- 后面的元素如果与 .layer 有重叠 -->
  <!-- 可能被强制提升为合成层 -->
  <div class="sibling">大量内容...</div>
  <div class="sibling">大量内容...</div>
  <div class="sibling">大量内容...</div>
  <!-- 每个 sibling 都可能成为独立合成层 -->
</div>
```

Blink 有「层压缩」（Layer Squashing）机制来缓解层爆炸：当多个小的合成层在视觉上重叠时，Blink 可以将它们合并为一个合成层。

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 层爆炸 | 过度使用 translateZ(0) | 只在必要元素上使用 |
| 层过多 | 大量 will-change | 动画结束后移除 will-change |
| 内存占用 | 每个合成层有独立位图 | 减少合成层数量 |
| 合成开销 | GPU 合成大量层 | 合并相邻层 |

> will-change 不是越多越好。每个合成层都消耗 GPU 内存。在 1000 个元素上加 will-change: transform，你的页面会先因为内存爆炸而崩溃，而不是变快。

## 9.3 GPU 合成工作流程

### 9.3.1 光栅化

光栅化（Rasterization）是将绘制指令转换为像素位图的过程。Chrome 的光栅化在工作线程上并行执行，利用多核 CPU 加速。

```
光栅化工作流程

绘制记录列表
  │
  ▼
分块（Tiling）
  │  将页面分成多个图块（Tile）
  │  通常每块 256x256 或 512x512 像素
  ▼
优先级排序
  │  可视区域内的图块优先光栅化
  │  离可视区域近的次优先
  │  远处的最后光栅化
  ▼
并行光栅化
  │  多个工作线程同时光栅化不同图块
  │  光栅化结果存入 GPU 纹理
  ▼
合成准备完成
```

光栅化的分块策略让 Chrome 可以优先光栅化用户可见区域的图块，让内容尽快显示。屏幕外的图块延迟光栅化，节省资源。

### 9.3.2 合成器线程

Chrome 的合成工作在独立的合成器线程（Compositor Thread）上执行，不阻塞主线程。这是 Chrome 渲染架构的一个关键设计。

```
主线程与合成器线程的分工

主线程（Main Thread）
  ├─ JavaScript 执行
  ├─ 样式计算
  ├─ 布局计算
  ├─ 绘制记录生成
  └─ 提交到合成器

合成器线程（Compositor Thread）
  ├─ 接收合成层树
  ├─ 处理滚动（不阻塞主线程）
  ├─ 处理 CSS transform 动画
  ├─ 调度光栅化
  └─ 提交合成帧到 GPU

GPU 进程
  ├─ 执行 GPU 命令
  ├─ 纹理上传
  └─ 输出最终像素到屏幕
```

合成器线程能独立处理滚动和 transform 动画的原因是：这些操作只改变合成层的变换矩阵，不需要重新布局和绘制。合成器直接更新变换矩阵，让 GPU 重新合成，全程不涉及主线程。

| 操作 | 主线程参与？ | 合成器独立处理？ | 性能 |
|------|------------|----------------|------|
| 滚动 | 否 | 是 | 流畅 |
| transform 动画 | 否 | 是 | 流畅 |
| opacity 动画 | 否 | 是 | 流畅 |
| 改变 width | 是 | 否 | 可能卡顿 |
| 改变 background | 是 | 否 | 可能卡顿 |
| JavaScript 执行 | 是 | 否 | 阻塞渲染 |

### 9.3.3 合成帧与 vsync

合成器以 vsync（垂直同步）信号为节拍生成合成帧。每个 vsync 周期（约 16.6ms），合成器生成一帧合成输出。

```
vsync 驱动的渲染周期

vsync 信号 → 合成器开始合成
  ├─ 检查是否有新的合成层树更新
  ├─ 更新动画状态（transform/opacity）
  ├─ 计算合成层变换矩阵
  ├─ 生成 GPU 命令
  └─ 提交到 GPU 进程

GPU 进程
  ├─ 执行 GPU 命令
  ├─ 合成各层纹理
  └─ 输出到屏幕

下一个 vsync → 重复
```

## 9.4 合成与动画性能

### 9.4.1 为什么 transform 动画快

理解了合成层和 GPU 合成后，就能理解为什么 transform 动画比 top/left 动画快得多。

```
top/left 动画 vs transform 动画

top/left 动画（每帧）：
  JavaScript 执行 → Style Recalc → Layout → Paint → Composite
  每帧都要走完整管线

transform 动画（每帧）：
  合成器线程更新变换矩阵 → Composite
  只走合成阶段，跳过 Style/Layout/Paint

性能差异：
  top/left:  ~16ms/帧（可能掉帧）
  transform: ~1-2ms/帧（几乎不可能掉帧）
```

### 9.4.2 动画性能最佳实践

| 实践 | 说明 | 效果 |
|------|------|------|
| 用 transform 代替 top/left | 只触发合成 | 性能最优 |
| 用 opacity 代替 visibility | 只触发合成 | 性能最优 |
| 动画元素提升为合成层 | will-change 或 translateZ | 避免重绘 |
| 避免大面积重绘 | 缩小绘制范围 | 减少光栅化 |
| 动画结束后移除 will-change | 释放合成层 | 节省内存 |
| 使用 content-visibility: auto | 跳过屏幕外渲染 | 减少渲染范围 |

### 9.4.3 检查合成层

Chrome DevTools 的 Layers 面板可以查看页面的合成层结构。

在 Layers 面板中，你可以看到：

| 信息 | 说明 | 用途 |
|------|------|------|
| 合成层列表 | 所有合成层的层级树 | 检查层数量 |
| 每层的大小 | 位图尺寸 | 评估内存占用 |
| 提升原因 | 为什么成为合成层 | 优化依据 |
| 绘制内容 | 每层的可视化预览 | 调试绘制问题 |

> 打开 Chrome DevTools 的 Layers 面板，看看你的页面有多少合成层。如果发现几十个甚至上百个合成层，你的页面可能存在层爆炸问题。

## 9.5 硬件加速与 GPU 路径

### 9.5.1 GPU 纹理上传

合成层的位图存储在 GPU 纹理中。当合成层的内容更新时，Blink 需要将新的位图上传到 GPU。这个上传操作是有开销的，尤其是对于大尺寸的合成层。

```
GPU 纹理上传流程

CPU 侧：
  绘制记录 → 光栅化 → 位图（CPU 内存）
  │
  ▼
  纹理上传（CPU → GPU）
  │  通过 GL/Dawn API 上传
  │  大尺寸位图上传耗时
  ▼
GPU 侧：
  纹理存储在 GPU 内存
  │
  ▼
  GPU 合成（变换 + 混合）
  │
  ▼
  输出到屏幕
```

这也是为什么频繁更新大尺寸合成层的内容（如视频播放、Canvas 动画）会消耗较多 GPU 带宽。

### 9.5.2 零拷贝光栅化

为了减少纹理上传的开销，Chrome 使用了零拷贝光栅化（Zero-Copy Rasterization）技术。光栅化直接在 GPU 内存中进行，生成的位图直接作为 GPU 纹理，无需从 CPU 内存上传。

| 光栅化方式 | 路径 | 开销 | 适用场景 |
|-----------|------|------|---------|
| CPU 光栅化 + 上传 | CPU → GPU | 高 | 兼容模式 |
| GPU 光栅化（GPU Raster） | 直接在 GPU | 低 | 支持的 GPU |
| 零拷贝光栅化 | GPU 内存直接使用 | 最低 | 现代设备 |

零拷贝光栅化配合 GPU 光栅化，让 Chrome 的渲染性能在现代设备上大幅提升。GPU 光栅化使用 GPU 的 shader（着色器）程序执行绘制指令，比 CPU 光栅化快得多。

### 9.5.3 Dawn 图形 API 抽象层

Chrome 在 2021 年开始使用 Dawn 替代直接的 OpenGL ES 调用。Dawn 是 Chrome 团队开发的 WebGPU 实现，同时也作为 Chrome 内部的图形 API 抽象层。

Dawn 的价值在于跨平台抽象：它在不同平台上分别映射到 Vulkan（Android/Linux）、Metal（macOS/iOS）、D3D12（Windows），让 Chrome 不需要为每个平台写不同的 GPU 代码。

| 平台 | 底层图形 API | Dawn 映射 |
|------|------------|----------|
| Windows | D3D12 | Dawn → D3D12 |
| macOS | Metal | Dawn → Metal |
| Linux | Vulkan | Dawn → Vulkan |
| Android | Vulkan | Dawn → Vulkan |

### 9.5.4 合成器的 cc 模块

Chrome 的合成器在代码中被称为 cc（Chrome Compositor）。cc 是 Blink 之外的一个独立模块，运行在渲染进程的合成器线程上。

cc 模块的核心数据结构是 LayerTreeHost（主线程侧）和 LayerTreeHostImpl（合成器线程侧）。主线程通过 LayerTreeHost 提交合成层树，合成器线程通过 LayerTreeHostImpl 执行合成。这两个对象通过 commit 操作同步数据。

```
cc 合成流程

主线程                          合成器线程
┌──────────────┐              ┌──────────────┐
│LayerTreeHost  │   commit    │LayerTreeHostImpl│
│  ├─ Layer 1   │ ──────────► │  ├─ LayerImpl 1│
│  ├─ Layer 2   │              │  ├─ LayerImpl 2│
│  └─ Layer 3   │              │  └─ LayerImpl 3│
└──────────────┘              └──────────────┘
                                     │
                                     ▼
                              生成合成帧
                                     │
                                     ▼
                              提交到 GPU 进程
```

commit 操作是主线程到合成器线程的数据同步点。每次主线程完成布局和绘制后，通过 commit 将新的合成层树传递给合成器线程。commit 操作本身有开销，频繁 commit 会影响性能。

## 9.6 滚动的渲染优化

### 9.6.1 滚动合成

滚动是网页中最频繁的交互之一。Chrome 的合成器线程可以独立处理滚动，不需要主线程参与，这是滚动性能流畅的关键。

当用户滚动页面时，合成器线程接收滚动输入，更新合成层的偏移量，重新合成并输出。整个过程在合成器线程上完成，不触发主线程的任何工作。

```
滚动处理流程

用户滚动
  │
  ▼
合成器线程接收滚动事件
  │
  ▼
更新滚动层的位置偏移
  │  (只修改变换矩阵，不重新布局/绘制)
  ▼
重新合成各层
  │
  ▼
输出新帧到屏幕

全程在合成器线程完成，主线程可以继续执行 JavaScript
```

### 9.6.2 touch-action 与滚动优化

touch-action CSS 属性可以控制触摸滚动的行为，帮助浏览器提前优化滚动处理。

| touch-action 值 | 说明 | 效果 |
|---------------|------|------|
| auto | 默认，允许所有操作 | 无优化 |
| none | 禁止所有触摸手势 | 元素处理所有手势 |
| pan-x | 只允许水平滚动 | 合成器可优化垂直方向 |
| pan-y | 只允许垂直滚动 | 合成器可优化水平方向 |
| manipulation | 只允许滚动和缩放 | 禁用双击缩放 |

设置 touch-action 后，合成器可以提前决定是否需要将触摸事件发送给主线程。如果 touch-action: pan-y，合成器知道不需要处理水平滚动手势，可以更高效地处理垂直滚动。

> 滚动性能的秘诀就是「合成器线程能独立完成」。只要你的页面不阻塞主线程，滚动就会流畅。如果你在 touchmove 事件中做了大量计算，合成器可能需要等待主线程，滚动就会卡顿。

## 9.7 合成层提升条件详解

### 9.7.1 合成层提升的完整判定流程

Blink 在判断是否将元素提升为合成层时，会执行一个复杂的判定流程。提升条件分为「直接原因」（Direct Reasons）和「后处理原因」（Post-Order Reasons）。

```
合成层提升判定流程

步骤1: 检查直接原因
  ├─ 有 3D 变换? → 提升
  ├─ 有 will-change: transform/opacity/filter? → 提升
  ├─ 有 transform/opacity/filter 动画? → 提升
  ├─ position: fixed? → 提升
  ├─ 是 video/canvas/webgl 元素? → 提升
  ├─ 是 backface-visibility: hidden? → 提升
  ├─ 有 will-change 配合其他提升条件? → 提升
  └─ 有 IntersectionObserver 根? → 可能提升

步骤2: 检查后处理原因
  ├─ 与其他合成层重叠?
  │   ├─ 是 → 可能被迫提升 (层爆炸风险)
  │   └─ 否 → 不提升
  ├─ 是否可以压缩 (Squashing)?
  │   ├─ 多个小合成层合并为一个
  │   └─ 减少合成层数量
  └─ 是否需要独立的 z-index 排序?

步骤3: 最终决定
  → 提升为独立合成层 / 合并到现有层 / 留在普通层
```

### 9.7.2 层爆炸的具体触发条件

层爆炸（Layer Explosion）是合成层数量失控增长的场景。理解其触发条件对避免性能问题至关重要。

```
层爆炸场景示例

场景1: 大量重叠元素 + 一个合成层
  <div class="container">
    <div class="animating" style="transform: translateZ(0)">
      <!-- 这个元素成为合成层 -->
    </div>
    <!-- 后面的 1000 个元素如果与 .animating 重叠 -->
    <!-- 每个都可能被强制提升为合成层 -->
    <div class="item">...</div> × 1000
  </div>

场景2: 嵌套的合成层
  <div style="transform: translateZ(0)">     ← 合成层 1
    <div style="transform: translateZ(0)">   ← 合成层 2
      <div style="transform: translateZ(0)"> ← 合成层 3
        ...
      </div>
    </div>
  </div>
  每层都有独立的位图 → 内存开销巨大

场景3: will-change 滥用
  <style>
    * { will-change: transform; }  /* 灾难性 */
  </style>
  → 每个元素都成为合成层
  → 内存立即爆炸
```

### 9.7.3 合成线程的完整工作流程

合成器线程（Compositor Thread）是渲染进程中独立于主线程的关键组件。它的工作流程可以分为几个阶段。

```
合成器线程工作流程

阶段1: 接收合成层树 (Commit)
  主线程完成布局和绘制后
  → 通过 commit 将合成层树传递给合成器线程
  → 包含: 层级、位置、变换、裁剪等信息

阶段2: 层合成计算
  ├─ 计算每层的变换矩阵
  ├─ 计算每层的裁剪区域
  ├─ 确定层的可见性 (在视口内?)
  └─ 对层进行排序 (z-index)

阶段3: 光栅化调度
  ├─ 确定需要光栅化的 Tile (图块)
  ├─ 按优先级排序 (视口内优先)
  └─ 分发给光栅化工作线程

阶段4: 接收光栅化结果
  ├─ 光栅化完成的 Tile 存入 GPU 纹理
  └─ 更新合成层的纹理引用

阶段5: 生成合成帧
  ├─ 将所有可见层的纹理和变换矩阵打包
  ├─ 生成 GPU 命令缓冲区
  └─ 提交给 GPU 进程

阶段6: GPU 执行
  GPU 进程执行合成命令
  → 各层纹理按变换矩阵合成
  → 输出最终像素到屏幕
```

### 9.7.4 Tile 化渲染与光栅化线程

Chrome 将页面内容分成固定大小的图块（Tile，通常 256x256 或 512x512 像素），每个 Tile 独立光栅化。这种策略让光栅化可以并行执行，且可以按优先级处理。

```
Tile 化渲染

页面被分割为 Tiles:
  ┌──┬──┬──┬──┬──┬──┐
  │T1 │T2 │T3 │T4 │T5 │T6 │  ← 优先光栅化 (视口内)
  ├──┼──┼──┼──┼──┼──┤
  │T7 │T8 │T9 │T10│T11│T12│ ← 次优先 (接近视口)
  ├──┼──┼──┼──┼──┼──┤
  │T13│T14│T15│T16│T17│T18│← 延迟光栅化 (远离视口)
  └──┴──┴──┴──┴──┴──┘

光栅化线程池:
  Worker Thread 1: 光栅化 T1
  Worker Thread 2: 光栅化 T2
  Worker Thread 3: 光栅化 T3
  Worker Thread 4: 光栅化 T4
  ...
  (并行执行, 互不阻塞)
```

Tile 化的优势：按需光栅化（只光栅化可见区域，节省 CPU 和 GPU 资源）、并行处理（多线程同时光栅化不同 Tile）、增量更新（只重新光栅化变化的 Tile，而非整个页面）。

### 9.7.5 GPU 进程的绘制命令

GPU 进程是 Chrome 中唯一直接与 GPU 硬件交互的进程。它接收来自多个渲染进程的合成命令，通过 Dawn 图形 API 抽象层执行 GPU 操作。

```
GPU 进程命令执行流程

渲染进程 A ──┐
渲染进程 B ──┼──→ 命令缓冲区 ──→ GPU 进程 ──→ GPU 硬件
渲染进程 C ──┘    (序列化)        (执行)

GPU 命令示例 (概念):
  1. bindTexture(layer_1_texture)
  2. setTransform(matrix_1)     // 应用层的变换矩阵
  3. drawQuad(0, 0, 256, 256)   // 绘制 Tile
  4. bindTexture(layer_2_texture)
  5. setTransform(matrix_2)
  6. drawQuad(0, 0, 256, 256)
  7. present()                   // 输出到屏幕
```

命令缓冲区机制确保了渲染进程不能直接调用 GPU API，提供了安全隔离。GPU 进程验证每个命令的合法性后才执行。

### 9.7.6 滚动合成的优化

Chrome 的滚动优化是合成器线程最重要的能力之一。当用户滚动页面时，合成器线程可以完全独立地处理滚动，不需要主线程参与。

```
滚动合成优化流程

用户滚动 (触摸/滚轮)
  │
  ▼
合成器线程接收滚动事件
  ├─ 检查滚动区域是否有 non-passive 事件监听器
  │   ├─ 有 → 需要通知主线程 (可能卡顿)
  │   └─ 无 → 独立处理 (快速路径)
  │
  ├─ 更新滚动层的偏移量
  │   (只修改变换矩阵中的 translation)
  │
  ├─ 检查是否需要新的 Tile
  │   ├─ 滚动到未光栅化的区域 → 请求光栅化
  │   └─ 已光栅化 → 直接使用
  │
  ├─ 重新合成
  │   (用更新后的变换矩阵合成各层)
  │
  └─ 提交到 GPU → 屏幕更新

全程不涉及主线程!
```

### 9.7.7 will-change 的正确使用与滥用风险

will-change 是一个强大的优化工具，但滥用会导致严重的性能问题。

```css
/* 正确使用: 动画前添加，动画后移除 */
.card {
  transition: transform 0.3s;
}
.card.animating {
  will-change: transform;  /* 动画期间 */
}
.card:not(.animating) {
  will-change: auto;       /* 非动画期间 */
}

/* 滥用: 永久 will-change */
.card {
  will-change: transform;  /* 永久占用 GPU 内存 */
}

/* 灾难: 通配符 will-change */
* {
  will-change: transform;  /* 每个元素都是合成层 */
}
```

| 使用方式 | 合成层数量 | 内存占用 | 性能影响 |
|---------|-----------|---------|---------|
| 正确使用 | 少量 | 低 | 正向 |
| 永久使用 | 中等 | 中等 | 中性偏负 |
| 通配符使用 | 大量 | 极高 | 灾难性 |

每个合成层的内存开销取决于其位图大小。一个全屏的合成层在 Retina 显示器上可能占用 8-16MB GPU 内存。10个全屏合成层就是 80-160MB，仅用于存储位图数据。

> will-change 的正确用法是「临时性」的：在动画即将开始时添加，动画结束后移除。可以通过 JavaScript 动态添加和移除 will-change 类名。如果元素频繁动画，可以保持 will-change，但要定期评估是否还需要。

## 9.6 合成线程工作流程

### 9.6.1 合成线程职责

合成线程（Compositor Thread）是渲染进程中独立于主线程的线程，负责处理滚动、动画和合成。它不执行 JavaScript，因此不会被主线程阻塞。

```
合成线程工作流程

1. 接收主线程的 Property Tree（属性树）
   → 包含每个图层的 transform、opacity、clip

2. 接收光栅化结果
   → GPU 进程完成光栅化后通知合成线程

3. 计算可见 Tile
   → 根据滚动位置确定哪些 Tile 可见

4. 构造 Draw Quad
   → 将可见 Tile + 变换信息组合为绘制指令

5. 提交给 GPU 进程
   → GPU 进程执行实际绘制
```

| 操作 | 主线程 | 合成线程 |
|------|--------|---------|
| JavaScript | 是 | 否 |
| 滚动 | 否 | 是 |
| CSS 动画 | 是（非合成属性） | 是（合成属性） |
| 绘制 | 是 | 否 |

> 合成线程是滚动流畅的关键。当用户滚动页面时，合成线程直接处理滚动偏移，重新计算可见 Tile 并提交给 GPU，全程不涉及主线程。如果主线程被 JavaScript 阻塞，滚动仍然流畅。只有当主线程需要处理滚动事件（如无限滚动加载）时才可能卡顿。

## 9.7 Tile 化渲染

### 9.7.1 光栅化线程池

大页面无法一次性光栅化所有内容。Chrome 将页面分成 Tile（图块），由光栅化线程池并行处理。

```
Tile 化渲染流程

页面 → 分割为 Tile（256x256 或 512x512）
  ↓
光栅化线程池（4 个 Worker）
  ├─ Worker 1: 光栅化 Tile (0,0)
  ├─ Worker 2: 光栅化 Tile (0,1)
  ├─ Worker 3: 光栅化 Tile (1,0)
  └─ Worker 4: 光栅化 Tile (1,1)
  ↓
光栅化结果存储在 GPU 内存
  ↓
合成线程根据滚动位置选择可见 Tile
```

> Tile 的大小是动态的。高分辨率屏幕使用更大的 Tile（512x512）以减少 Tile 数量。低分辨率屏幕使用更小的 Tile（128x128）以减少内存。光栅化优先级：可见区域 > 即将可见区域 > 不可见区域。

## 9.8 GPU 进程绘制命令

### 9.8.1 绘制命令队列

合成线程将绘制指令提交给 GPU 进程，GPU 进程将指令转换为 OpenGL/Vulkan/Metal 调用。

```
绘制命令流程

合成线程 → Commit → GPU 进程
  ↓
GPU 进程构建命令缓冲区
  ├─ glUseProgram(shaderProgram)
  ├─ glUniformMatrix4fv(transform)
  ├─ glBindTexture(tileTexture)
  ├─ glDrawArrays(GL_TRIANGLES, 0, 6)
  └─ ... 更多绘制命令
  ↓
GPU 执行渲染
  → 最终像素输出到屏幕
```

> GPU 进程是 Chrome 中唯一允许直接调用 GPU API 的进程。渲染进程通过合成线程向 GPU 进程发送绘制命令，GPU 进程统一执行。这种设计保证了 GPU 上下文的隔离和安全性。

## 本章核心知识总结

| 知识模块 | 核心内容 | 性能影响 |
|---------|---------|---------|
| PaintNG | 绘制属性树分离变换/裁剪/效果 | 合成可独立处理 |
| 合成层 | 独立位图，GPU 合成 | transform/opacity 动画快 |
| 层提升条件 | 3D 变换、will-change、动画 | 合理使用避免层爆炸 |
| 合成器线程 | 独立于主线程处理滚动/动画 | 不阻塞主线程 |
| GPU 光栅化 | 直接在 GPU 内存光栅化 | 减少纹理上传开销 |
| 分块光栅化 | 优先可视区域 | 快速首屏渲染 |

觉得有用？收藏起来，这是理解浏览器渲染性能的关键一章。

你在项目中用 will-change 优化过动画吗？有没有遇到过层爆炸的问题？评论区聊聊。

关注怕浪猫，下期我们讲浏览器如何处理用户输入事件，从硬件到 JavaScript 的完整事件传递路径。系列进度 9/24。

下期预告：第 10 章「事件处理与输入管道」。我们会拆解从硬件事件到 JavaScript 回调的完整路径、事件捕获与冒泡机制、以及 passive event listener 的作用。怕浪猫下期见。

# 第8章 布局（Layout）

> 浏览器要把你的 CSS 变成精确的像素坐标，需要经过布局这个阶段。Chrome 用了 5 年时间把旧的布局引擎替换成 LayoutNG，这是一次彻底的架构重写。

我是怕浪猫，上期我们讲了 DOM 和样式计算，今天进入第 8 章：布局。这一章会拆解 LayoutNG 布局引擎的工作原理、盒模型计算、Flexbox 和 Grid 布局算法的内部实现，以及布局抖动（Layout Thrashing）的成因和解决方案。

## 8.1 LayoutNG 布局引擎

### 8.1.1 为什么需要 LayoutNG

LayoutNG（Next Generation Layout）是 Chrome 从 2017 年开始开发的下一代布局引擎，在 Chrome 76 中正式启用。它替换了旧的布局引擎（现在被称为 Legacy Layout）。

旧布局引擎的问题在于架构上的缺陷。它将布局计算和绘制记录混在一起，导致代码耦合严重，难以维护和扩展。布局结果直接存储在 LayoutObject 上，没有清晰的数据边界。每个布局算法（Block、Flex、Grid）都有自己的实现，但共享状态管理混乱。

LayoutNG 的设计目标：

| 目标 | 说明 | 效果 |
|------|------|------|
| 关注分离 | 布局计算与绘制记录分离 | 代码清晰 |
| 不可变结果 | 布局结果独立于布局对象 | 避免状态污染 |
| 算法模块化 | 每种布局算法独立实现 | 易于扩展 |
| 可测试性 | 布局算法可独立测试 | 减少回归 |

### 8.1.2 LayoutNG 的核心架构

LayoutNG 将布局过程拆分为三个清晰的阶段：输入、布局算法、输出。

```
LayoutNG 工作流程

输入（Input）
  ├─ NGLayoutInputNode    ← 布局输入节点（从 DOM/LayoutObject 转换）
  ├─ ConstraintSpace      ← 约束空间（可用尺寸、写入模式等）
  └─ ComputedStyle         ← 计算后的样式
       │
       ▼
布局算法（Layout Algorithm）
  ├─ NGBlockLayoutAlgorithm      ← 块级布局
  ├─ NGFlexLayoutAlgorithm       ← Flex 布局
  ├─ NGGridLayoutAlgorithm       ← Grid 布局
  ├─ NGInlineLayoutAlgorithm     ← 行内布局
  └─ NGTableLayoutAlgorithm      ← 表格布局
       │
       ▼
输出（Output）
  ├─ NGPhysicalFragment          ← 物理片段（最终布局结果）
  │   ├─ NGPhysicalBoxFragment   ← 盒子片段
  │   ├─ NGPhysicalTextFragment  ← 文本片段
  │   └─ NGPhysicalLineBoxFragment ← 行盒片段
  └─ NGLayoutResult              ← 布局结果（含片段树）
```

LayoutNG 的关键设计是 Fragment（片段）概念。布局结果不是直接写回 LayoutObject，而是生成一棵 Fragment 树。Fragment 是不可变的，一旦生成就不会被修改。如果布局变化，生成新的 Fragment 树替换旧的。

> 不可变 Fragment 是 LayoutNG 最聪明的设计。旧的布局引擎把布局结果直接存在布局对象上，修改和读取混在一起，状态管理一团糟。LayoutNG 把布局结果变成独立的数据结构，生成后不可变，彻底解决了状态污染问题。

### 8.1.3 布局对象（LayoutObject）与布局树

DOM 树中的元素并非全部需要布局。例如 `<head>`、`<script>`、`<meta>` 等元素不产生视觉输出，不需要布局。Blink 会为需要布局的 DOM 节点创建 LayoutObject，形成布局树（Layout Tree）。

```
DOM 树到布局树的映射

DOM 树：
  <html>
    <head>           ← 无 LayoutObject
      <title>...</title>
      <meta>...
    </head>
    <body>
      <div>           ← LayoutObject (block)
        <span>        ← LayoutObject (inline)
          text        ← LayoutObject (text)
        </span>
      </div>
      <script>...</script>  ← 无 LayoutObject
    </body>
  </html>

布局树：
  LayoutView (html)
    └── LayoutBlockFlow (body)
          └── LayoutBlockFlow (div)
                └── LayoutInline (span)
                      └── LayoutText (text)
```

某些 CSS 属性会导致 LayoutObject 的变化：

| CSS 属性 | LayoutObject 类型 | 说明 |
|---------|-------------------|------|
| display: block | LayoutBlockFlow | 块级布局 |
| display: inline | LayoutInline | 行内布局 |
| display: flex | LayoutFlexibleBox | Flex 布局 |
| display: grid | LayoutGrid | Grid 布局 |
| display: none | 无 LayoutObject | 不参与布局 |
| float: left/right | LayoutBlockFlow (floated) | 浮动布局 |
| position: absolute | LayoutBlockFlow (abspos) | 绝对定位 |

## 8.2 盒模型计算

### 8.2.1 CSS 盒模型的层级

CSS 盒模型从内到外有四层：Content（内容）、Padding（内边距）、Border（边框）、Margin（外边距）。

```
CSS 盒模型
┌────────────────────────────────────────┐
│                Margin                  │
│  ┌──────────────────────────────────┐  │
│  │            Border                 │  │
│  │  ┌──────────────────────────────┐│  │
│  │  │          Padding              ││  │
│  │  │  ┌──────────────────────────┐││  │
│  │  │  │       Content            │││  │
│  │  │  │                          │││  │
│  │  │  └──────────────────────────┘││  │
│  │  └──────────────────────────────┘│  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘

box-sizing: content-box（默认）
  width = Content width
  总宽度 = width + padding + border + margin

box-sizing: border-box
  width = Content + Padding + Border
  总宽度 = width + margin
```

box-sizing 的两种模式对比：

| box-sizing | width 包含 | 适用场景 | 优势 |
|------------|-----------|---------|------|
| content-box | 仅 Content | 传统 CSS | 直观 |
| border-box | Content + Padding + Border | 现代开发 | 尺寸可控 |

### 8.2.2 包含块（Containing Block）

布局计算的基础是包含块（Containing Block）。每个元素的布局都相对于它的包含块进行。包含块决定了元素的可用空间和定位参考。

```
包含块规则

元素的包含块取决于其 position 属性：

position: static / relative
  → 包含块 = 最近的块级祖先元素的内容区

position: absolute
  → 包含块 = 最近的 position 非 static 祖先的 Padding 区

position: fixed
  → 包含块 = 视口（Viewport）
  → 如果有 transform/filter/perspective 祖先，则为该祖先

position: sticky
  → 包含块 = 最近的滚动祖先
```

> 包含块是布局的坐标系原点。理解了包含块，就理解了为什么 absolute 元素相对于最近的非 static 祖先定位，而不是相对于父元素。

## 8.3 Flexbox 布局算法

### 8.3.1 Flex 布局的核心概念

Flexbox（Flexible Box Layout，弹性盒布局）是 CSS3 引入的一维布局模型，专为在一个方向上排列元素而设计。

```
Flex 布局核心概念

┌─────────────────────────────────────────┐
│            Flex Container                │
│  main-start                    main-end  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ Item │ │ Item │ │ Item │ │ Item │   │
│  │  1   │ │  2   │ │  3   │ │  4   │   │
│  └──────┘ └──────┘ └──────┘ └──────┘   │
│  │← main size →│                         │
│  │                                       │
│  cross-start                 cross-end   │
└─────────────────────────────────────────┘

主轴（Main Axis）：flex-direction 决定的方向
交叉轴（Cross Axis）：垂直于主轴的方向
```

Flex 布局的关键属性：

| 属性 | 作用 | 说明 |
|------|------|------|
| flex-direction | 主轴方向 | row / column / row-reverse / column-reverse |
| justify-content | 主轴对齐 | flex-start / center / space-between / space-around |
| align-items | 交叉轴对齐 | stretch / center / flex-start / flex-end |
| flex-grow | 放大比例 | 0 = 不放大 |
| flex-shrink | 缩小比例 | 1 = 可缩小 |
| flex-basis | 初始大小 | auto = 根据内容 |
| flex | 简写 | grow shrink basis |

### 8.3.2 Flex 布局计算过程

NGFlexLayoutAlgorithm 的布局计算分为多个步骤：

```
Flex 布局计算流程

步骤1：确定主轴方向和可用空间
  ├─ 读取 flex-direction
  ├─ 计算容器的 main size 和 cross size
  └─ 考虑容器的 padding/border

步骤2：确定每个 Flex Item 的 flex base size
  ├─ flex-basis auto → 使用 content size
  ├─ flex-basis 具体值 → 使用该值
  └─ 考虑 min/max width 约束

步骤3：计算 flex grow / shrink
  ├─ 如果总 base size < 容器 main size
  │   → 按 flex-grow 比例分配剩余空间
  └─ 如果总 base size > 容器 main size
      → 按 flex-shrink 比例压缩

步骤4：计算交叉轴尺寸
  ├─ 单行：align-items 决定每个 item 的交叉轴位置
  └─ 多行：先排列每行，再计算行间间距

步骤5：处理 align-self / align-items
  └─ 每个 item 在交叉轴上的最终位置
```

flex-grow 的计算示例：

```
容器 main size = 500px
三个 Flex Item：
  Item1: base=100px, flex-grow=1
  Item2: base=150px, flex-grow=2
  Item3: base=100px, flex-grow=1

总 base size = 100 + 150 + 100 = 350px
剩余空间 = 500 - 350 = 150px
总 grow = 1 + 2 + 1 = 4

Item1 最终 = 100 + 150 * (1/4) = 137.5px
Item2 最终 = 150 + 150 * (2/4) = 225px
Item3 最终 = 100 + 150 * (1/4) = 137.5px
```

## 8.4 Grid 布局算法

### 8.4.1 Grid 布局的核心概念

CSS Grid Layout（网格布局）是 CSS3 引入的二维布局模型，可以同时控制行和列的排列。

```
Grid 布局核心概念

      Col1    Col2    Col3
    ┌───────┬───────┬───────┐
Row1│   A   │   B   │   C   │
    ├───────┼───────┼───────┤
Row2│   D   │   E   │   F   │
    ├───────┼───────┼───────┤
Row3│   G   │   H   │   I   │
    └───────┴───────┴───────┘

Grid Container: 定义网格的容器
Grid Item: 网格中的子元素
Grid Line: 网格线（水平和垂直）
Grid Track: 两条相邻网格线之间的空间（行或列）
Grid Cell: 一个行和列交叉形成的单元
Grid Area: 多个 Grid Cell 组成的矩形区域
```

### 8.4.2 Grid 布局计算过程

NGGridLayoutAlgorithm 的计算比 Flex 更复杂，因为需要同时处理两个维度。

```
Grid 布局计算流程

步骤1：解析 grid-template-columns/rows
  ├─ 固定值（如 100px）→ 直接使用
  ├─ 比例值（如 1fr）→ 记录，后续分配
  ├─ auto → 根据内容计算
  └─ minmax(min, max) → 约束范围

步骤2：放置 Grid Items
  ├─ 根据 grid-column/row 放置每个 item
  ├─ 处理 span（跨多个 cell）
  └─ 处理 auto-placement（自动放置）

步骤3：计算 Track 尺寸
  ├─ 固定 Track：直接使用指定值
  ├─ auto Track：根据内容尺寸
  └─ fr Track：按比例分配剩余空间

步骤4：处理对齐
  ├─ justify-items：行内对齐
  ├─ align-items：列内对齐
  ├─ justify-content：整体水平对齐
  └─ align-content：整体垂直对齐
```

| 布局模型 | 维度 | 适用场景 | 复杂度 |
|---------|------|---------|--------|
| Block | 一维 | 文档流 | 低 |
| Flex | 一维 | 组件内排列 | 中 |
| Grid | 二维 | 页面整体布局 | 高 |
| Table | 二维 | 表格数据 | 中 |

## 8.5 布局抖动（Layout Thrashing）

### 8.5.1 什么是布局抖动

布局抖动（Layout Thrashing）是前端性能问题中最常见的一种。它发生在 JavaScript 中反复交叉执行「修改 DOM」和「读取布局信息」的操作时。

```
布局抖动示例

// 反模式：交叉读写
function badResize() {
  for (let i = 0; i < items.length; i++) {
    items[i].style.width = box.offsetWidth + 'px';  // 读布局
    items[i].style.height = box.offsetHeight + 'px'; // 读布局
    // 每次循环都触发一次 Layout
  }
}

// 正确模式：先读后写
function goodResize() {
  const width = box.offsetWidth;    // 读一次
  const height = box.offsetHeight;  // 读一次
  
  for (let i = 0; i < items.length; i++) {
    items[i].style.width = width + 'px';   // 只写
    items[i].style.height = height + 'px';  // 只写
    // 所有写操作完成后才触发一次 Layout
  }
}
```

### 8.5.2 强制同步布局的触发

Blink 有一套优化机制，将布局计算延迟到下一帧。但某些 API 会强制 Blink 立即执行布局计算，称为强制同步布局（Forced Synchronous Layout）。

| API | 是否强制布局 | 说明 |
|-----|------------|------|
| offsetWidth / offsetHeight | 是 | 需要布局信息 |
| getBoundingClientRect() | 是 | 需要布局信息 |
| clientWidth / clientHeight | 是 | 需要布局信息 |
| scrollWidth / scrollHeight | 是 | 需要布局信息 |
| getComputedStyle() | 部分 | 某些属性需要布局 |
| innerWidth / innerHeight | 否 | 视口尺寸，不需要布局 |
| style.width = '100px' | 否 | 只写不读，不触发 |

> 每次读取 offsetWidth，Blink 都要检查是否有待处理的 DOM 修改。如果有，必须先执行布局计算才能返回准确的 offsetWidth。这就是强制同步布局的原理。

### 8.5.3 FastDOM 模式

FastDOM 是一种避免布局抖动的编程模式，核心思想是将 DOM 读操作和写操作分批执行。

```
FastDOM 模式

// 读写分离
function optimizeResize() {
  // 批量读
  const reads = items.map(item => ({
    el: item,
    width: item.offsetWidth,
    height: item.offsetHeight
  }));
  
  // 批量写
  reads.forEach(({ el, width, height }) => {
    el.style.width = width + 'px';
    el.style.height = height + 'px';
  });
  // 只触发一次 Layout
}
```

现代框架（如 React、Vue）的虚拟 DOM 机制天然避免了布局抖动：所有 DOM 修改在虚拟 DOM 层批量计算，最后一次性应用到真实 DOM，不会出现读写交叉。

## 8.6 布局失效与增量布局

### 8.6.1 布局失效标记

当 DOM 或样式变化影响布局时，Blink 标记受影响的布局对象为「需要布局」（needs_layout）。布局失效会沿着布局树传播。

```
布局失效传播

修改 div 的 width
  → div 标记为 needs_layout
  → div 的子节点标记为 needs_layout（子树失效）
  → div 的兄弟节点可能标记为 needs_layout（如果影响排列）
  → div 的父节点标记为 needs_layout（尺寸变化影响父容器）

失效传播的边界：
  如果子树尺寸变化不影响外部（如 contain: layout）
  → 失效不传播到外部
```

### 8.6.2 增量布局

Blink 不会在每次 DOM 修改时都执行完整布局。它使用增量布局（Incremental Layout）策略：只对标记为 needs_layout 的布局对象执行布局计算，跳过未标记的对象。

| 布局类型 | 触发方式 | 计算范围 | 性能 |
|---------|---------|---------|------|
| 完整布局 | 首次渲染、窗口大小变化 | 所有布局对象 | 慢 |
| 增量布局 | DOM/样式变化 | 仅标记的对象 | 快 |
| 约束布局 | 父布局变化 | 受约束的子树 | 中等 |

## 8.7 文本布局与换行算法

### 8.7.1 行内布局

行内布局（Inline Layout）是布局引擎中最复杂的部分之一。与块级元素的规则布局不同，行内文本涉及换行、混合方向（如中英文混排）、字体度量、基线对齐等复杂因素。

NGInlineLayoutAlgorithm 的工作分为几个步骤：首先将行内内容（文本节点、行内元素）分解为 NGInlineItem，每个 item 记录文本片段及其样式。然后执行换行算法（Line Breaking），根据可用宽度将内容分割到多行。最后对每行执行基线对齐，计算每个 item 的精确位置。

### 8.7.2 Bidi 算法与混合方向文本

当文本中混合了从左到右（LTR，Left-To-Right）和从右到左（RTL，Right-To-Left）的文字时（如中英文混排阿拉伯文），Blink 使用 Bidi（Bidirectional，双向）算法确定每个字符的最终方向。

Bidi 算法由 Unicode 标准定义，将字符分为强类型（如拉丁字母为 LTR，阿拉伯字母为 RTL）、弱类型（数字）和中性类型（标点）。算法根据字符类型和段落基础方向，计算每个字符的显示顺序。

### 8.7.3 字体度量与基线

文本布局中的基线（Baseline）对齐是一个精细的工作。不同的字体有不同的度量参数：ascent（基线上方高度）、descent（基线下方深度）、x-height（小写字母高度）。当同一行中混合了不同字体的文本时，Blink 需要计算每段文本的基线位置，确保视觉上对齐。

| 字体度量 | 说明 | 影响 |
|---------|------|------|
| ascent | 基线到字符顶部 | 行高计算 |
| descent | 基线到字符底部 | 行高计算 |
| x-height | 基线到小写字母顶部 | 垂直对齐 |
| cap-height | 基线到大写字母顶部 | 大写字母对齐 |
| line-gap | 建议行间距 | 行高计算 |

> 文本布局是渲染引擎中最被低估的复杂度来源。一个简单的换行操作，背后涉及 Unicode 分词、Bidi 算法、字体度量、基线对齐等多层计算。这也是为什么 LayoutNG 把行内布局单独作为一个算法模块来实现。

## 本章核心知识总结

| 知识模块 | 核心内容 | 性能影响 |
|---------|---------|---------|
| LayoutNG | 不可变 Fragment 架构 | 更清晰的布局流程 |
| 盒模型 | Content/Padding/Border/Margin | box-sizing 影响尺寸计算 |
| Flex 布局 | 一维布局，grow/shrink 分配 | 适合组件内排列 |
| Grid 布局 | 二维布局，同时控制行列 | 适合页面布局 |
| 布局抖动 | 读写交叉导致反复布局 | 避免读写交叉 |
| 增量布局 | 只计算受影响的部分 | 减少布局开销 |

觉得有用？收藏起来，下次做布局性能优化时直接翻出来参考。

你在项目中遇到过布局抖动问题吗？是怎么排查和解决的？评论区聊聊。

关注怕浪猫，下期我们进入绘制和合成阶段，讲 PaintNG 绘制引擎、合成层（Compositing Layer）的创建条件和工作原理。系列进度 8/24。

下期预告：第 9 章「绘制与合成」。我们会拆解绘制记录的生成、PaintNG 绘制引擎的工作原理、合成层提升条件、以及 GPU 合成的工作流程。怕浪猫下期见。

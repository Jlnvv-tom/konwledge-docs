---
sidebar_position: 7
---

# 第7章 DOM 与样式计算

> 你以为 document.getElementById 是一个简单的查找？在 Blink 底层，它涉及 DOM 树遍历、标识符索引、缓存策略。而 CSS 选择器匹配更是一个精心设计的算法优化故事。

我是怕浪猫，上期我们看了渲染管线的全景图，今天进入第 7 章，我们拆解渲染管线的前两个阶段：DOM 树管理和样式计算。这一章会讲 DOM 的内部数据结构、CSS 选择器匹配的优化算法、ComputedStyle 的计算与缓存机制，以及样式变化如何触发不同级别的重新渲染。

## 7.1 DOM 树的内部结构

### 7.1.1 Node 与 Element 的关系

在 Blink 中，DOM 树由 Node 对象组成。Node 是所有 DOM 节点的基类，Element 是 Node 的子类，表示有标签名的元素节点。

```
DOM 节点继承关系

Node（基类）
  ├── Element
  │   ├── HTMLElement
  │   │   ├── HTMLDivElement
  │   │   ├── HTMLSpanElement
  │   │   ├── HTMLParagraphElement
  │   │   └── ... (所有 HTML 元素类型)
  │   ├── SVGElement
  │   └── MathMLElement
  ├── TextNode（文本节点）
  ├── Comment（注释节点）
  ├── Document（文档节点）
  └── DocumentType（文档类型节点）
```

每种 HTML 标签在 Blink 中都有对应的 C++ 类。这种设计让 Blink 可以对不同标签做特化处理，比如 `<img>` 有图片加载逻辑，`<canvas>` 有绘图上下文，`<form>` 有表单验证逻辑。

| 节点类型 | 说明 | 示例 |
|---------|------|------|
| Element | 有标签名的元素 | `<div>`, `<p>`, `<span>` |
| TextNode | 文本内容 | `"Hello"` |
| Comment | 注释 | `<!-- comment -->` |
| Document | 文档根节点 | `document` |
| DocumentFragment | 文档片段 | 轻量级 DOM 容器 |
| ShadowRoot | 影子 DOM 根 | Web Components |

### 7.1.2 DOM 树的内存布局

每个 Node 对象在 Blink 中包含大量字段，用于存储属性、样式信息、布局信息、事件监听器等。

```
Node 对象的核心字段（简化版）

class Node {
  // 树结构
  Node* parent_;
  Node* first_child_;
  Node* last_child_;
  Node* previous_sibling_;
  Node* next_sibling_;
  
  // 基本信息
  NodeType node_type_;
  AtomicString node_name_;
  
  // 样式信息
  ComputedStyle* computed_style_;
  
  // 布局信息
  LayoutObject* layout_object_;
  
  // 事件
  EventListenerMap event_listeners_;
  
  // 标志位
  bool is_connected_;  // 是否在文档中
  bool needs_style_recalc_;
  bool needs_layout_;
};
```

DOM 树的操作（如 appendChild、removeChild、insertBefore）在 Blink 中是 O(1) 或 O(n) 的操作，其中 n 是子节点数量。Blink 通过双向链表管理兄弟节点，通过 first_child 和 last_child 管理子节点，使得插入和删除操作高效。

### 7.1.3 标识符索引与快速查找

Blink 为 DOM 树维护了多种索引，加速常见的查找操作。

| 索引类型 | 维护时机 | 加速的查找 |
|---------|---------|-----------|
| ID 索引 | id 属性变化时 | getElementById |
| Name 索引 | name 属性变化时 | getElementsByName |
| Class 索引 | class 属性变化时 | getElementsByClassName |
| Tag 索引 | 标签名 | getElementsByTagName |

getElementById 之所以是 O(1) 操作，是因为 Blink 维护了一个 HashMap，将 id 映射到对应的 Element 指针。当 id 属性变化时，Blink 自动更新这个 HashMap。

### 7.1.4 DOM Tree 的变化追踪

Blink 使用一套精细的脏标记系统来追踪 DOM 树的变化。当 JavaScript 修改 DOM 时，Blink 不会立即更新渲染，而是标记变化类型，在下一次渲染帧中批量处理。

这个设计的关键优势是批量处理：如果在同一帧内多次修改 DOM，Blink 只需要在帧末做一次渲染更新，而不是每次修改都触发渲染。常见的 DOM 变化类型和对应的脏标记包括：子树结构变化（ChildInvalidation）、属性变化（AttributeInvalidation）、文本内容变化（TextContentInvalidation）。每种脏标记对应不同的后续处理流程，确保只做必要的计算。

> 你觉得 document.getElementById 很快，是因为 Blink 在背后帮你维护了一个 HashMap。如果没有这个索引，每次查找都要遍历整棵 DOM 树。

## 7.2 CSS 选择器匹配

### 7.2.1 选择器匹配算法

CSS 选择器匹配是样式计算中最耗时的部分。Blink 使用从右到左（Right-to-Left）的匹配算法。

```
从右到左匹配示例

CSS 选择器：div.container > p.highlight

HTML 结构：
<div class="container">
  <p class="highlight">Hello</p>
  <p>World</p>
</div>

匹配过程（从右到左）：

对于 <p class="highlight">：
  1. 匹配选择器最右边：.highlight → 匹配！
  2. 向左：> p → 匹配（父元素是 p）... 
     等等，> p 表示父元素是 p？不对
     > p 表示当前元素是 p → 匹配！
  3. 再向左：div.container → 
     检查父元素是否是 div.container → 匹配！
  4. 选择器全部匹配，应用样式

对于 <p>（没有 highlight class）：
  1. 匹配选择器最右边：.highlight → 不匹配
  2. 立即跳过，不需要继续检查
```

从右到左匹配的优势在于快速排除不匹配的元素。大多数元素在选择器的最右端就会被排除，不需要做完整的检查。

| 匹配方向 | 性能特征 | 优势 |
|---------|---------|------|
| 从左到右 | 需要遍历子树 | 直觉 |
| 从右到左 | 快速排除不匹配 | 高效 |

### 7.2.2 选择器复杂度分析

不同类型的选择器有不同的匹配复杂度：

| 选择器类型 | CSS 示例 | 匹配复杂度 | 说明 |
|-----------|---------|-----------|------|
| ID 选择器 | `#header` | O(1) | HashMap 查找 |
| 类选择器 | `.menu` | O(n) | 遍历 class 列表 |
| 标签选择器 | `div` | O(1) | 直接比较 |
| 属性选择器 | `[type="text"]` | O(n) | 遍历属性 |
| 后代选择器 | `div p` | O(d) | 需要向上遍历祖先 |
| 子选择器 | `div > p` | O(1) | 只检查父元素 |
| 相邻选择器 | `div + p` | O(1) | 只检查前一个兄弟 |
| 伪类 | `:hover` | 取决于实现 | 事件触发时匹配 |

后代选择器（如 `div.container p.item`）是性能最需要注意的选择器，因为对于每个匹配 `p.item` 的元素，Blink 都需要向上遍历祖先链，检查是否有 `div.container`。

### 7.2.3 样式 recal（RecalcStyle）的触发

当 DOM 或 CSS 发生变化时，Blink 需要重新计算受影响元素的样式。这个过程叫做 Style Recalculation（样式重计算）。

```
Style Recalc 触发条件

1. CSS 规则变化
   ├─ 添加/删除样式表
   ├─ 修改 CSS 规则
   └─ 媒体查询断点变化

2. DOM 变化
   ├─ 添加/删除元素
   ├─ 修改 class 属性
   ├─ 修改 style 属性
   └─ 修改 data-* 属性（如果被选择器使用）

3. 用户交互
   ├─ :hover 状态变化
   ├─ :focus 状态变化
   ├─ :checked 状态变化
   └─ :active 状态变化
```

Blink 的样式重计算采用「脏标记」（Dirty Flag）策略。当变化发生时，Blink 不会立即重新计算所有元素的样式，而是标记受影响的元素为「需要样式重计算」（needs_style_recalc_）。在下一次渲染帧中，Blink 遍历 DOM 树，只重新计算被标记的元素。

> 样式重计算不是「全量计算」，而是「增量计算」。Blink 精确追踪哪些元素需要更新，只做必要的计算。这也是为什么修改 body 的 class 会导致大量元素重计算：因为很多元素的选择器可能匹配新的 class。

## 7.3 ComputedStyle 的计算与缓存

### 7.3.1 ComputedStyle 是什么

ComputedStyle（计算后的样式）是每个 DOM 元素的最终样式值。它不是 CSS 源代码中写的值，而是经过继承、层叠、计算后的最终值。

```
样式值的转换过程

CSS 声明值（Specified Value）
  │  CSS 源代码中写的值
  │  如：font-size: 1em; color: red;
  ▼
层叠值（Cascaded Value）
  │  经过选择器优先级排序后的胜出值
  │  如：font-size: 1em（多个规则中优先级最高的）
  ▼
指定值（Specified Value）
  │  层叠值，如果未指定则使用继承值或初始值
  ▼
计算值（Computed Value）
  │  绝对化相对单位
  │  如：font-size: 16px（1em = 16px）
  ▼
使用值（Used Value）
  │  基于布局计算后的值
  │  如：width: 800px（百分比被计算为像素）
  ▼
实际值（Actual Value）
  │  浏览器实际使用的值（受限于设备能力）
  │  如：font-size: 16px（某些设备可能四舍五入）
```

### 7.3.2 ComputedStyle 的缓存策略

Blink 对 ComputedStyle 做了大量缓存优化，避免重复计算。

| 缓存层 | 说明 | 命中条件 |
|--------|------|---------|
| 共享 ComputedStyle | 多个元素共享同一 ComputedStyle 对象 | 选择器、属性完全相同 |
| 继承缓存 | 子元素继承父元素的继承属性 | 父元素样式未变 |
| 差量计算 | 只计算变化的属性 | 部分属性变化 |

ComputedStyle 共享的条件非常严格，Blink 会检查以下条件是否全部满足：

```
ComputedStyle 共享条件

1. 两个元素有相同的父元素
2. 两个元素没有 inline style
3. 两个元素没有被 id 选择器匹配
4. 两个元素的 class 列表在相同的选择器上下文中匹配
5. 两个元素的属性列表相同
6. 两个元素的链接状态相同
7. 两个元素的 focus 状态相同
8. 两个元素没有被 :hover 等动态伪类影响

全部满足 → 共享 ComputedStyle
任一不满足 → 独立计算
```

这种共享机制对于列表型页面特别有效。一个有 1000 个 `<li>` 的列表，如果每个 li 的样式规则相同，它们可以共享同一个 ComputedStyle 对象，大幅减少内存和计算开销。

### 7.3.3 样式继承的底层实现

CSS 继承在 Blink 中的实现方式是：子元素的 ComputedStyle 在创建时，先复制父元素的继承属性值，然后应用自身的规则覆盖。这个过程在样式计算阶段完成。

继承属性（如 color、font-size）的值会自动从父元素流向子元素，不需要额外的查找。非继承属性（如 width、margin）如果在子元素上未指定，使用初始值（initial value）而非父元素的值。

Blink 维护了一个继承属性的位图（InheritedPropertiesMask），在样式重计算时快速判断哪些属性需要从父元素继承。这个优化避免了遍历所有 CSS 属性的开销。

### 7.3.4 样式优先级与层叠

CSS（Cascading Style Sheets，层叠样式表）的「层叠」是样式计算的核心机制。当多条规则匹配同一元素时，Blink 按优先级排序，选择优先级最高的规则。

优先级排序规则从高到低：

| 优先级 | 来源 | 示例 |
|--------|------|------|
| 最高 | !important + 内联样式 | style="color:red !important" |
| 高 | !important + 外部样式 | .cls { color:red !important } |
| 中高 | 内联样式 | style="color:red" |
| 中 | ID 选择器 | #header { color:red } |
| 中低 | 类/属性/伪类选择器 | .menu { color:red } |
| 低 | 标签/伪元素选择器 | div { color:red } |
| 最低 | 通配符/继承 | * { color:red } |

Blink 的层叠计算通过比较选择器特异性（Specificity）来实现。特异性是一个三元组 (a, b, c)，分别对应 ID 数量、类/属性数量、标签数量。比较时从左到右，先比较 a，相同则比较 b，再相同则比较 c。

## 7.4 影子 DOM 与样式隔离

### 7.4.1 Shadow DOM 的样式边界

Shadow DOM（影子 DOM）是 Web Components 的核心技术之一，它提供了 DOM 和样式的封装隔离。

```
Shadow DOM 结构

<div id="host">  ← Shadow Host
  #shadow-root  ← Shadow Root（影子根）
    <style>
      p { color: red; }  ← 只影响 Shadow DOM 内部的 p
    </style>
    <p>内部内容</p>
  #end shadow-root
  <p>外部内容</p>  ← 不受 Shadow DOM 内部样式影响
</div>
```

Shadow DOM 的样式隔离规则：

| 样式方向 | 是否穿透 | 说明 |
|---------|---------|------|
| 外部 → 内部 | 否 | 外部 CSS 不影响 Shadow DOM 内部 |
| 内部 → 外部 | 否 | Shadow DOM 内部 CSS 不影响外部 |
| 继承属性 | 是 | color、font 等继承属性仍会穿透 |

### 7.4.2 CSS 自定义属性与 Shadow DOM

CSS 自定义属性（CSS Custom Properties，也叫 CSS 变量）是可以穿透 Shadow DOM 边界的。这使得外部可以控制 Shadow DOM 内部的样式。

```
/* 外部样式 */
#host {
  --theme-color: blue;
}

/* Shadow DOM 内部样式 */
:host {
  color: var(--theme-color);  /* 继承自 host 的自定义属性 */
}
```

## 7.5 样式变化与渲染管线触发

### 7.5.1 样式变化到渲染的映射

不同的样式属性变化会触发不同级别的渲染管线阶段。理解这个映射关系，是前端性能优化的基础。

```
样式变化 → 渲染管线触发

修改 width/height/margin/padding
  → Style Recalc → Layout → Paint → Composite

修改 color/background/box-shadow
  → Style Recalc → Paint → Composite

修改 transform/opacity
  → Style Recalc → Composite（跳过 Layout 和 Paint）

修改 visibility
  → Style Recalc → Paint → Composite
  （visibility 不影响布局，但影响绘制）
```

| 属性类别 | 触发的管线阶段 | 性能代价 | 典型属性 |
|---------|--------------|---------|---------|
| 布局属性 | Style → Layout → Paint → Composite | 最高 | width, height, margin, padding |
| 绘制属性 | Style → Paint → Composite | 中等 | color, background, border-color |
| 合成属性 | Style → Composite | 最低 | transform, opacity, filter |

### 7.5.2 will-change 属性的作用

will-change 是一个 CSS 属性，用于提前告知浏览器元素将要变化的属性，让浏览器提前做准备（通常是创建合成层）。

```
/* 提前告知浏览器 transform 将要变化 */
.card {
  will-change: transform;
}

/* 动画完成后移除 */
.card.animating {
  will-change: auto;  /* 避免长期占用内存 */
}
```

will-change 的正确使用方式：

| 使用方式 | 正确 | 说明 |
|---------|------|------|
| 动画开始前添加 | 是 | 让浏览器提前创建合成层 |
| 动画结束后移除 | 是 | 释放合成层内存 |
| 长期保持 will-change | 否 | 浪费内存，可能导致层爆炸 |
| 对大量元素使用 | 否 | 合成层数量过多 |

### 7.5.3 批量样式修改

Blink 对样式修改有批量优化。在同一帧内多次修改同一个元素的样式，Blink 不会每次都触发样式重计算，而是将修改累积到下一次渲染帧统一处理。

```
// 多次样式修改，Blink 批量处理
element.style.width = '100px';    // 标记 dirty
element.style.height = '200px';   // 标记 dirty
element.style.color = 'red';      // 标记 dirty
// Blink 在下一帧统一重计算，不会触发三次

// 但读取布局信息会强制同步
element.style.width = '100px';
console.log(element.offsetWidth); // 强制 Layout（因为 offsetWidth 需要布局信息）
element.style.height = '200px';
console.log(element.offsetHeight); // 再次强制 Layout
// 两次强制 Layout = 两次重排
```

> 样式修改本身不昂贵，昂贵的是读取布局信息（offsetWidth、getBoundingClientRect 等）。每次读取布局信息都会强制浏览器执行待处理的布局计算，导致「布局抖动」（Layout Thrashing）。

## 7.6 CSS Containment

CSS Containment 是一个性能优化属性，它允许开发者告诉浏览器某个元素的渲染是独立的，不会影响外部。浏览器可以据此做渲染优化。

```css
/* 声明 .widget 的布局和绘制不影响外部 */
.widget {
  contain: layout paint;
}

/* 更强的隔离 */
.isolated {
  contain: strict;  /* 等同于 contain: size layout paint style */
}
```

| contain 值 | 含义 | 优化效果 |
|-----------|------|---------|
| layout | 布局隔离 | 元素内部布局变化不影响外部 |
| paint | 绘制隔离 | 元素不会绘制到自身边界外 |
| size | 尺寸隔离 | 元素尺寸不依赖内容 |
| style | 样式隔离 | 计数器和引号不受外部影响 |
| strict | size + layout + paint + style | 最大隔离 |

CSS Containment 的实际价值在于减少渲染管线的计算范围。如果 `.widget` 内部的样式变化只影响自身布局，浏览器不需要重计算 `.widget` 外部的布局。

### 7.6.1 content-visibility 优化

content-visibility 是 CSS Containment 的扩展，它允许浏览器跳过屏幕外元素的渲染。对于长列表页面，这个属性可以显著减少渲染开销。

```css
/* 屏幕外的卡片不渲染 */
.card {
  content-visibility: auto;
  contain-intrinsic-size: 200px;  /* 预估高度，避免滚动条跳动 */
}
```

当 content-visibility 设为 auto 时，浏览器会自动判断元素是否在可视区域内。如果不在可视区域内，浏览器跳过该元素的布局和绘制，只保留预估的尺寸。当元素滚动到可视区域时，浏览器才执行完整的布局和绘制。

这个属性对于有大量 DOM 节点的页面（如社交媒体的时间线、搜索结果列表）尤其有效，可以将渲染时间减少 50% 以上。

## 7.7 CSS Houdini 与样式 API

CSS Houdini 是一组 CSS 底层 API 的统称，它允许开发者直接介入浏览器的样式和渲染管线，实现自定义的 CSS 行为。

Houdini 的核心 API 包括：

| API | 说明 | 用途 |
|-----|------|------|
| Paint API | 自定义绘制 | 用 JS 实现自定义 CSS 属性的绘制 |
| Layout API | 自定义布局 | 用 JS 实现自定义 CSS 布局 |
| Properties & Values API | 注册自定义属性 | 为 CSS 变量添加类型 |
| Typed OM | 类型化的 CSS 对象模型 | 替代字符串操作的 CSSOM |

Paint API 是目前支持最广泛的 Houdini API。它允许开发者通过 JavaScript 注册一个「Paint Worklet」，在 CSS 中通过 paint() 函数引用。

```javascript
// 注册 Paint Worklet
registerPaint('circle', class {
  paint(ctx, size, properties) {
    const radius = Math.min(size.width, size.height) / 2;
    ctx.beginPath();
    ctx.arc(size.width / 2, size.height / 2, radius, 0, 2 * Math.PI);
    ctx.fill();
  }
});
```

```css
/* 在 CSS 中使用 */
.avatar {
  background: paint(circle);
}
```

Paint Worklet 在独立的线程中执行，不会阻塞主线程，这是它比直接用 JavaScript 操作 Canvas 的一个优势。

### 7.7.1 Typed OM

Typed OM（Typed Object Model，类型化对象模型）是 CSS Houdini 提供的类型化 CSS 对象模型。传统的 CSSOM（CSS Object Model，CSS 对象模型）使用字符串操作 CSS 值，如 `element.style.fontSize = '16px'`。Typed OM 将 CSS 值表示为结构化的对象，避免了字符串解析的开销。

```javascript
// 传统 CSSOM（字符串操作）
element.style.fontSize = '16px';
const size = element.style.fontSize;  // '16px'（字符串）

// Typed OM（结构化对象）
element.attributeStyleMap.set('font-size', CSS.px(16));
const size = element.attributeStyleMap.get('font-size');  // CSSUnitValue {value: 16, unit: 'px'}
```

Typed OM 的优势在于避免了反复的字符串解析和格式化，对于频繁操作 CSS 属性的场景（如动画）有性能优势。不过 Typed OM 目前仍处于渐进推广阶段，浏览器支持度不如 Paint API。

## 7.8 DOM 树构建的完整流程

### 7.8.1 从字节流到 DOM 树的完整路径

HTML 解析是一个流式处理过程。网络数据到达一部分，解析器就处理一部分。完整的解析流程从字节流开始，经过解码、分词、建树三个阶段。

```
HTML 解析完整流程

阶段1: 字节流输入
  网络层推送字节流: 3C 21 44 4F 43 54 59 50 45...
  ├─ 检测 BOM (Byte Order Mark)
  ├─ 读取 <meta charset> 确定编码
  └─ 如果没有声明，使用默认编码检测算法

阶段2: 字符解码
  字节流 → 字符串 (根据编码)
  3C 21 44 4F 43 54 59 50 45 → "<!DOCTYPE"

阶段3: 分词 (Tokenization)
  字符串 → Token 序列
  状态机驱动的词法分析
  ├─ Data State → 文本内容
  ├─ Tag Open State → 标签开始
  ├─ Tag Name State → 标签名
  ├─ Attribute Name State → 属性名
  ├─ Attribute Value State → 属性值
  └─ Comment State → 注释

阶段4: 建树 (Tree Construction)
  Token 序列 → DOM 树
  插入模式 (Insertion Mode) 状态机驱动
  ├─ 维护开放元素栈 (Open Elements Stack)
  ├─ 根据当前插入模式和 Token 类型
  └─ 决定如何创建/插入/关闭 DOM 节点
```

### 7.8.2 Tokenizer 状态机

HTML 的 Tokenizer 是一个有状态的状态机。每个输入字符都会导致状态转换，并可能输出 Token。

```
Tokenizer 状态转换示例

输入: <div class="box">Hello</div>

状态转换:
Data State
  │ '<' 触发 Tag Open State
  ▼
Tag Open State
  │ 'd' 触发 Tag Name State
  ▼
Tag Name State
  │ 'i', 'v' 继续 Tag Name State
  │ ' ' 触发 Before Attribute Name State
  ▼
Before Attribute Name State
  │ 'c' 触发 Attribute Name State
  ▼
Attribute Name State
  │ 'l', 'a', 's', 's' 继续
  │ '=' 触发 Before Attribute Value State
  ▼
Before Attribute Value State
  │ '"' 触发 Attribute Value (Double Quoted) State
  ▼
Attribute Value State
  │ 'b', 'o', 'x' 继续
  │ '"' 触发 After Attribute Value (Quoted) State
  ▼
After Attribute Value State
  │ '>' 输出 StartTag Token: div, {class: "box"}
  │   回到 Data State
  ▼
Data State
  │ 'H', 'e', 'l', 'l', 'o' 输出 Character Token
  │ '<' 触发 Tag Open State
  ▼
Tag Open State
  │ '/' 触发 End Tag Open State
  ▼
End Tag Open State
  │ 'd', 'i', 'v' 继续 Tag Name State
  │ '>' 输出 EndTag Token: div
  │   回到 Data State
```

### 7.8.3 HTML 解析器的容错机制

HTML 的设计哲学是「容错优先」。浏览器不会因为 HTML 语法错误而拒绝渲染页面。HTML5 规范定义了详细的错误处理算法，确保各种畸形 HTML 都能被合理解析。

```
HTML 容错处理示例

1. 未闭合的标签
   <p>段落1<p>段落2
   → 解析器自动关闭第一个 <p>
   → <p>段落1</p><p>段落2</p>

2. 错误的嵌套
   <b>粗体<i>粗斜体</b>斜体</i>
   → 解析器重建嵌套结构
   → <b>粗体<i>粗斜体</i></b><i>斜体</i>

3. 表格自动修正
   <table>
     <tr><td>单元格
   → 自动闭合 td, tr, table 标签

4. <script> 中的特殊处理
   <script>
     var x = "</script>";  // 会被解析为结束标签
   </script>
   → 解析器看到 </script> 就结束脚本
   → 需要用 "<\/script>" 转义
```

### 7.8.4 CSS 选择器匹配的 Bloom Filter 优化

当 DOM 中有数千个元素和数百条 CSS 规则时，选择器匹配的性能成为瓶颈。Blink 使用 Bloom Filter 来加速选择器匹配。

Bloom Filter 是一种空间高效的概率数据结构，可以快速判断一个元素「可能匹配」或「一定不匹配」某条选择器。Blink 为每条选择器维护一个 Bloom Filter，记录选择器中涉及的标签名、类名、ID 等。

```
Bloom Filter 加速选择器匹配

对于元素 <div class="container">
匹配规则: div.container > p.highlight

步骤1: 检查 Bloom Filter
  元素的标签: div → 在 Bloom Filter 中? 是
  元素的类名: container → 在 Bloom Filter 中? 是
  → 可能匹配，继续详细匹配

步骤2: 详细匹配
  从右到左匹配选择器
  .highlight → div 有吗? 没有 → 不匹配

如果 Bloom Filter 判断「一定不匹配」:
  → 跳过详细匹配，直接排除
  → 大幅减少无效匹配计算
```

Bloom Filter 的假阳率（误判为可能匹配）约为 1-3%，但假阴率为 0%（不会漏掉真正的匹配）。这意味着 Bloom Filter 可以快速排除 97% 以上不匹配的选择器-元素组合。

### 7.8.5 Style Sharing Cache

Blink 还有一个重要的样式优化：Style Sharing Cache（样式共享缓存）。如果多个元素的 ComputedStyle 完全相同，它们可以共享同一个 ComputedStyle 对象，避免重复计算。

样式共享的检查条件非常严格，包括：相同的父元素、相同的标签名、相同的 class 列表、相同的内联样式（都无）、相同的属性集、相同的链接状态、相同的 hover/focus 状态等。只有所有条件都满足，才能共享。

```
样式共享效果

<ul>
  <li>项目1</li>   ← ComputedStyle A
  <li>项目2</li>   ← 共享 ComputedStyle A
  <li>项目3</li>   ← 共享 ComputedStyle A
  <li class="active">项目4</li>  ← ComputedStyle B (不同 class)
  <li>项目5</li>   ← 共享 ComputedStyle A
</ul>

1000 个 <li> 中如果有 990 个样式相同
→ 只需计算 2 个 ComputedStyle
→ 节省 99% 的样式计算
```

### 7.8.6 影子 DOM 样式作用域规则

Shadow DOM 的样式隔离不是绝对的。有特定的机制允许样式穿透边界。

```
Shadow DOM 样式作用域

<div id="host">
  #shadow-root
    <style>
      :host { color: blue; }           ← :host 选择器可以设置 host 元素样式
      p { color: red; }                 ← 只影响 Shadow DOM 内部的 p
      ::slotted(span) { color: green; } ← 影响 slot 中的 span
    </style>
    <p>内部文本</p>
    <slot name="content">
      <!-- 被宿主元素的 span 填充 -->
    </slot>
  #end shadow-root
  <span slot="content">宿主文本</span>
</div>

样式穿透规则:
  外部 CSS → host 元素 ✓ (直接设置)
  外部 CSS → Shadow DOM 内部 ✗ (被隔离)
  Shadow DOM CSS → host 元素 ✓ (:host 选择器)
  Shadow DOM CSS → 外部内容 ✗ (被隔离)
  Shadow DOM CSS → slot 内容 ✓ (::slotted 选择器)
  CSS 自定义属性 → 穿透所有边界 ✓
```

| 样式方向 | 普通选择器 | :host | ::slotted | CSS 变量 |
|---------|-----------|-------|-----------|---------|
| 外部 → Shadow 内部 | 不穿透 | 不适用 | 不适用 | 穿透 |
| Shadow 内部 → 外部 | 不穿透 | 设置 host | 设置 slot 内容 | 穿透 |

CSS 自定义属性（CSS 变量）可以穿透 Shadow DOM 边界，这是因为自定义属性是继承的，而继承不受 Shadow DOM 边界限制。外部设置 `--theme-color: blue` 可以在 Shadow DOM 内部通过 `var(--theme-color)` 使用。

## 7.5 DOM 树构建流程

### 7.5.1 HTML 解析器流程

HTML 解析器将 HTML 文本转换为 DOM 树，分为两个阶段：Tokenizer（分词器）和 Tree Builder（树构建器）。

```
HTML 解析流程

原始 HTML 文本
  ↓
Tokenizer（分词器）
  → 将文本拆分为 Token
  → StartTag: <div>
  → EndTag: </div>
  → Text: "Hello"
  → Comment: <!-- ... -->
  ↓
Tree Builder（树构建器）
  → 根据 Token 构建 DOM 节点
  → 处理嵌套关系
  → 自动修复错误嵌套
  ↓
DOM 树
```

### 7.5.2 HTML 容错机制

HTML 解析器有强大的容错能力，能够自动修复错误嵌套的标签。

```
容错示例

输入: <table><p>Hello</p></table>
修复: <p></p><table></table>
原因: <p> 不能在 <table> 内
  → 解析器将 <p> 弹出表格
  → 在表格前创建 <p>

输入: <b><i>Bold Italic</b></i>
修复: <b><i>Bold Italic</i></b><i></i>
原因: </b> 关闭 <b> 时
  → 自动关闭内部的 <i>
  → 重新打开 <i> 以匹配 </i>
```

> HTML 的容错机制规范在 HTML5 标准中定义了详细的错误处理算法。这是为什么「烂 HTML」仍然能正常显示的原因。但这种容错也带来了安全隐患——XSS 过滤器可能认为输入是安全的，但经过浏览器容错处理后变成了恶意标签。

## 7.6 CSS 选择器匹配优化

### 7.6.1 Bloom Filter 加速

CSS 选择器从右到左匹配，但 Chrome 使用 Bloom Filter 快速排除不可能匹配的元素。

```
Bloom Filter 优化

传统匹配：
  div .item → 对每个元素检查
  → 是否有 .item class？
  → 祖先是否是 div？
  → 需要遍历祖先链

Bloom Filter：
  预计算每个元素的祖先 Bloom Filter
  → 存储祖先标签名和 class 的 Hash
  → 检查 div 是否在 Bloom Filter 中
  → 如果不在 → 快速跳过（100% 确定）
  → 如果在 → 可能匹配，进一步检查
```

| 优化手段 | 原理 | 效果 |
|---------|------|------|
| Bloom Filter | 快速排除不匹配元素 | 减少 90%+ 遍历 |
| Style Sharing | 相同样式的元素共享 | 减少计算量 |
| Rule Tree | 公共选择器路径共享 | 减少匹配开销 |

> Bloom Filter 是一种空间高效的数据结构，可以快速判断一个元素「一定不在」集合中。Chrome 为每个 DOM 元素维护一个祖先 Bloom Filter，包含所有祖先的标签名和 class。匹配选择器时，先检查 Bloom Filter，如果右边界选择器不可能匹配，直接跳过，避免遍历整个祖先链。

## 本章核心知识总结

| 知识模块 | 核心内容 | 性能影响 |
|---------|---------|---------|
| DOM 结构 | Node 树 + 索引加速 | getElementById 是 O(1) |
| 选择器匹配 | 从右到左匹配 | 后代选择器最慢 |
| Style Recalc | 脏标记 + 增量计算 | 减少不必要的重计算 |
| ComputedStyle | 共享 + 继承缓存 | 列表元素共享样式对象 |
| 样式变化映射 | 合成属性 > 绘制属性 > 布局属性 | 用 transform 做动画 |
| CSS Containment | 渲染隔离 | 减少渲染影响范围 |

觉得有用？收藏起来，下次做 CSS 性能优化时直接翻出来参考。

你在项目中遇到过 CSS 选择器性能问题吗？评论区聊聊。

关注怕浪猫，下期我们进入布局阶段，讲 LayoutNG 布局引擎。系列进度 7/24。

下期预告：第 8 章「布局（Layout）」。我们会拆解 LayoutNG 引擎的工作原理、盒模型计算、Flexbox 和 Grid 布局算法、以及布局抖动（Layout Thrashing）的成因和解决方案。怕浪猫下期见。

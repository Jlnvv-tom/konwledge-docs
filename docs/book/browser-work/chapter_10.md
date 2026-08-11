# 第10章 事件处理与输入管道

> 你点击屏幕到 JavaScript 的 onClick 回调执行，中间经过了 7 个阶段。如果你在 touchmove 里加了 event.preventDefault()，整个滚动管线可能被你拖慢。

我是怕浪猫，上期我们拆了绘制和合成，今天进入第 10 章：事件处理与输入管道。这一章会讲从硬件输入到 JavaScript 回调的完整路径、事件捕获与冒泡机制、passive event listener 的原理，以及 Chrome 如何让滚动不卡顿。

## 10.1 从硬件到 JavaScript 的完整事件路径

### 10.1.1 事件传递的 7 个阶段

当用户点击屏幕、按下键盘或移动鼠标时，硬件产生信号，经过操作系统、浏览器进程、渲染进程，最终到达 JavaScript 的事件回调。这个过程分为 7 个阶段。

```
事件传递的完整路径

阶段1：硬件中断
  硬件（触摸屏/键盘/鼠标）产生中断信号
  │
  ▼
阶段2：操作系统输入处理
  OS（Windows/macOS/Android）处理中断
  生成输入事件，放入系统事件队列
  │
  ▼
阶段3：浏览器进程接收
  Browser Process 从 OS 获取输入事件
  确定目标渲染进程（根据窗口和标签页）
  通过 IPC（Inter-Process Communication，进程间通信）转发
  │
  ▼
阶段4：渲染进程的合成器线程
  Compositor Thread 首先接收事件
  判断是否可以独立处理（如滚动）
  如果可以 → 直接处理，不通知主线程
  如果不能 → 转发给主线程
  │
  ▼
阶段5：主线程命中测试
  Main Thread 执行 Hit Test
  根据坐标确定事件目标元素
  遍历布局树找到最顶层元素
  │
  ▼
阶段6：事件分发
  按照 DOM 事件传播模型分发
  ├─ 捕获阶段（Capture Phase）
  ├─ 目标阶段（Target Phase）
  └─ 冒泡阶段（Bubble Phase）
  │
  ▼
阶段7：JavaScript 回调执行
  对应的事件监听器被调用
  事件对象传入回调函数
```

### 10.1.2 合成器线程的快速路径

阶段 4 中合成器线程的判断是事件处理性能的关键。对于滚动和捏合缩放等手势，合成器线程可以独立处理，不需要主线程参与。这就是「快速路径」（Fast Path）。

```
快速路径 vs 慢速路径

快速路径（合成器独立处理）：
  用户滚动 → 合成器更新偏移 → 重新合成 → 输出
  全程在合成器线程完成，不阻塞主线程

慢速路径（需要主线程参与）：
  用户滚动 → 合成器发现不能独立处理
  → 等待主线程 → 主线程执行 hit test
  → 主线程决定是否 preventDefault
  → 如果 preventDefault → 取消滚动
  → 如果不 preventDefault → 合成器执行滚动
```

什么时候走慢速路径？当页面的触摸事件监听器可能调用 preventDefault 时，合成器必须等待主线程决定。这就是 touchmove 事件处理影响滚动性能的原因。

| 事件类型 | 快速路径？ | 原因 |
|---------|-----------|------|
| 滚轮滚动 | 是 | wheel 事件不能 cancel 滚动 |
| 触摸滚动 | 取决于 listener | 如果有 non-passive touchmove |
| 键盘输入 | 否 | 需要主线程处理 |
| 鼠标点击 | 否 | 需要 hit test 和 JS 回调 |
| 捏合缩放 | 取决于 listener | 同触摸滚动 |

> 合成器线程的快速路径是 Chrome 滚动性能的秘密。如果你的 touchmove 监听器是 non-passive 的，每次触摸移动都要等主线程，合成器的快速路径就废了。

## 10.2 DOM 事件传播模型

### 10.2.1 三个阶段

DOM 事件传播分为三个阶段：捕获阶段、目标阶段和冒泡阶段。

```
DOM 事件传播三阶段

文档结构：
  document
    └── html
          └── body
                └── div#parent
                      └── button#child

点击 button#child 时事件传播：

阶段1：捕获阶段（从顶到底）
  document → html → body → div#parent → button#child
  （如果有 capture: true 的监听器，在此阶段触发）

阶段2：目标阶段
  button#child
  （在目标元素上，capture 和 bubble 监听器都触发）
  （触发顺序按注册顺序）

阶段3：冒泡阶段（从底到顶）
  button#child → div#parent → body → html → document
  （普通监听器在此阶段触发）
```

```javascript
// 事件监听器的注册方式
element.addEventListener('click', function(e) {
  console.log('冒泡阶段触发');
});

element.addEventListener('click', function(e) {
  console.log('捕获阶段触发');
}, true);  // 第三个参数 true 表示捕获阶段

// 事件流控制
element.addEventListener('click', function(e) {
  e.stopPropagation();  // 停止传播
  // 后续阶段的监听器不再触发
});

element.addEventListener('click', function(e) {
  e.stopImmediatePropagation();  // 立即停止
  // 同一元素上的后续监听器也不再触发
});
```

### 10.2.2 事件委托

事件委托（Event Delegation）利用事件冒泡机制，将多个子元素的事件监听器委托给父元素处理。这比给每个子元素单独添加监听器更高效。

```javascript
// 不推荐：1000 个监听器
document.querySelectorAll('.item').forEach(item => {
  item.addEventListener('click', handleClick);
});

// 推荐：1 个监听器（事件委托）
document.querySelector('.list').addEventListener('click', (e) => {
  if (e.target.classList.contains('item')) {
    handleClick(e);
  }
});
```

| 方式 | 监听器数量 | 内存占用 | 动态元素支持 |
|------|-----------|---------|------------|
| 直接绑定 | N | N 个监听器 | 需要重新绑定 |
| 事件委托 | 1 | 1 个监听器 | 自动支持 |

> 事件委托不仅节省内存，更重要的是它自动支持动态添加的子元素。你不需要在添加新元素后重新绑定监听器。

## 10.3 Passive Event Listener

### 10.3.1 什么是 passive listener

passive event listener 是 Chrome 在 2016 年引入的特性。它告诉浏览器：这个事件监听器不会调用 preventDefault()，浏览器可以安全地走快速路径。

```javascript
// non-passive（默认）：浏览器必须等待
element.addEventListener('touchmove', function(e) {
  // 可能有 e.preventDefault()
}, { passive: false });

// passive：浏览器可以立即滚动
element.addEventListener('touchmove', function(e) {
  // 不会调用 preventDefault()
  // 即使调用了也没有效果
}, { passive: true });
```

passive 的性能影响：

| 监听器类型 | 合成器行为 | 滚动性能 |
|-----------|-----------|---------|
| non-passive touchmove | 必须等待主线程 | 可能卡顿 |
| passive touchmove | 可独立处理 | 流畅 |
| 无 touchmove 监听器 | 可独立处理 | 流畅 |

### 10.3.2 默认 passive 行为

从 Chrome 56 开始，document 和 window 上的 touchstart、touchmove 事件默认是 passive 的。这意味着在这些目标上注册 touchstart/touchmove 监听器时，即使不指定 passive: true，浏览器也按 passive 处理。

| 事件目标 | 事件 | 默认 passive？ |
|---------|------|--------------|
| document | touchstart/touchmove | 是 |
| window | touchstart/touchmove | 是 |
| body | touchstart/touchmove | 是 |
| 普通元素 | touchstart/touchmove | 否 |
| 所有目标 | wheel | 否（但部分浏览器改为是） |
| 所有目标 | click/mousedown 等 | 不适用 |

> 如果你在 touchmove 中调用 preventDefault() 来阻止滚动，现在可能不生效了。改用 CSS 的 touch-action 属性或 overflow: hidden 来控制滚动行为。

## 10.4 命中测试（Hit Testing）

### 10.4.1 命中测试的原理

命中测试（Hit Testing）是确定给定坐标下最顶层元素的过程。这是事件处理的核心步骤。

Blink 的命中测试通过遍历合成层树来实现。合成器线程首先检查合成层的层级，找到最顶层包含该坐标的合成层，然后在该合成层内部进一步查找。

```
命中测试流程

坐标 (x, y)
  │
  ▼
从顶层合成层开始遍历
  ├─ 检查合成层是否包含该坐标
  ├─ 检查合成层的裁剪区域
  ├─ 检查 pointer-events CSS 属性
  │
  ▼
找到最顶层匹配的合成层
  │
  ▼
在合成层内部遍历
  ├─ 检查每个绘制片段的边界
  ├─ 考虑 z-index 和层叠顺序
  ├─ 考虑透明度和可见性
  │
  ▼
确定目标元素
```

### 10.4.2 pointer-events CSS 属性

pointer-events CSS 属性控制元素是否可以成为事件目标。

| pointer-events 值 | 说明 | 效果 |
|-------------------|------|------|
| auto | 默认 | 正常接收事件 |
| none | 不接收事件 | 事件穿透到下层 |
| auto（在 SVG 中） | 默认 | 正常接收 |
| visiblePainted（SVG） | 可见且填充区域 | SVG 特有 |
| pointer-events: none 的子元素 | — | 子元素可单独设为 auto |

```css
/* 让覆盖层不阻挡点击 */
.overlay {
  pointer-events: none;
}

/* 但覆盖层上的按钮可以点击 */
.overlay .button {
  pointer-events: auto;
}
```

### 10.4.3 命中测试缓存

Blink 对命中测试结果做了缓存优化。在连续的事件中（如 mousemove），如果 DOM 结构和样式没有变化，Blink 可以复用上一次的命中测试结果，避免重复计算。

缓存失效的条件包括：DOM 结构变化（添加/删除元素）、样式变化影响布局、合成层结构变化、滚动位置变化（可能改变重叠关系）。

## 10.5 输入延迟（Input Latency）

### 10.5.1 输入延迟的组成

输入延迟（Input Latency）是从用户操作到屏幕响应的总时间。它由多个部分组成。

```
输入延迟分解

用户操作
  │
  ▼ [OS 处理延迟]
  │
  ▼ [IPC 传输延迟]
  │
  ▼ [合成器处理延迟]
  │
  ▼ [主线程等待延迟] ← 最大的变量
  │
  ▼ [事件回调执行时间]
  │
  ▼ [渲染管线执行时间]
  │
  ▼ [GPU 合成延迟]
  │
  ▼
屏幕响应
```

| 延迟组成 | 典型值 | 可优化？ |
|---------|--------|---------|
| OS 处理 | ~1ms | 否 |
| IPC 传输 | ~1ms | 否 |
| 合成器处理 | ~1ms | 否 |
| 主线程等待 | 0-100ms+ | 是 |
| 事件回调 | 0-50ms | 是 |
| 渲染管线 | 5-15ms | 是 |
| GPU 合成 | ~2ms | 否 |

主线程等待是输入延迟的最大变量。如果主线程正在执行长任务（Long Task），输入事件必须等待任务完成。

### 10.5.2 Interaction to Next Paint（INP）

INP（Interaction to Next Paint，交互到下一次绘制）是 Chrome 提出的新一代交互响应指标。它测量从用户交互到下一帧绘制的时间。

```
INP 测量

用户点击
  │
  ▼ [输入延迟]
  │
  ▼ [事件处理]
  │
  ▼ [渲染管线]
  │
  ▼
下一帧绘制 ← INP 测量到这里
```

INP 的评级标准：

| INP 值 | 评级 | 说明 |
|--------|------|------|
| < 200ms | 好 | 用户感觉响应迅速 |
| 200-500ms | 需改进 | 用户可能感觉到延迟 |
| > 500ms | 差 | 用户明显感觉卡顿 |

> INP 在 2024 年 3 月正式取代 FCP（First Contentful Paint）成为 Core Web Vitals 的交互指标。优化 INP 的核心是减少主线程长任务，让事件回调能快速执行。

### 10.5.3 长任务与输入延迟

长任务（Long Task）是超过 50ms 的同步任务。在长任务执行期间，主线程无法处理输入事件，导致输入延迟。

```javascript
// 长任务示例：同步处理大量数据
function processLargeData(data) {
  // 如果 data 有 100000 条，这个循环可能执行 100ms+
  for (let i = 0; i < data.length; i++) {
    // 处理每条数据
  }
}

// 优化：分片执行
async function processLargeDataChunked(data) {
  const CHUNK_SIZE = 1000;
  for (let i = 0; i < data.length; i += CHUNK_SIZE) {
    const chunk = data.slice(i, i + CHUNK_SIZE);
    processChunk(chunk);
    await new Promise(r => setTimeout(r));  // 让出主线程
  }
}
```

```javascript
// 使用 scheduler.yield()（新 API）
async function processWithYield(data) {
  const CHUNK_SIZE = 1000;
  for (let i = 0; i < data.length; i += CHUNK_SIZE) {
    processChunk(data.slice(i, i + CHUNK_SIZE));
    if (scheduler.yield) {
      await scheduler.yield();  // 让出主线程，允许输入事件处理
    }
  }
}
```

| 优化策略 | 说明 | 效果 |
|---------|------|------|
| 任务分片 | 将长任务拆分为小任务 | 减少单次阻塞 |
| setTimeout(0) | 让出主线程 | 简单但不精确 |
| requestIdleCallback | 空闲时间执行 | 低优先级任务 |
| scheduler.yield() | 精确让出 | 新 API，优先恢复 |
| Web Worker | 后台线程执行 | 完全不阻塞主线程 |

## 10.6 事件循环与渲染的协调

### 10.6.1 input 事件的优先级调度

Chrome 的任务调度器为不同类型的任务分配不同优先级。输入事件通常有最高优先级，确保用户交互能快速响应。

| 任务优先级 | 任务类型 | 说明 |
|-----------|---------|------|
| 最高 | 用户输入 | 鼠标、键盘、触摸事件 |
| 高 | 渲染 | requestAnimationFrame |
| 中 | 默认 | setTimeout、网络回调 |
| 低 | 后台 | requestIdleCallback |

调度器在每一帧的时间预算内，先处理高优先级任务，再处理低优先级任务。如果高优先级任务占满了帧时间，低优先级任务会被延迟。

Chrome 的任务调度器使用一个基于优先级的队列。每个任务有一个优先级标签，调度器总是从最高优先级的队列中取出任务执行。对于同优先级的任务，按 FIFO（First In First Out，先进先出）顺序执行。

### 10.6.2 requestAnimationFrame 的时机

requestAnimationFrame（rAF）是浏览器提供的用于同步动画的 API。rAF 回调在每次渲染帧之前执行，确保动画回调与浏览器渲染节奏一致。

```
一帧中的执行顺序

vsync 信号
  │
  ▼
处理输入事件（最高优先级）
  │
  ▼
执行 rAF 回调
  │
  ▼
样式计算 → 布局 → 绘制 → 合成
  │
  ▼
帧结束（剩余时间执行其他任务）
```

在 rAF 回调中修改样式，可以在当前帧的渲染管线中生效。如果用 setTimeout 修改样式，可能要等到下一帧才生效，导致动画掉帧。

```javascript
// 推荐：rAF 做动画
function animate() {
  element.style.transform = `translateX(${pos}px)`;
  pos += 2;
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

// 不推荐：setTimeout 做动画
function animateBad() {
  element.style.transform = `translateX(${pos}px)`;
  pos += 2;
  setTimeout(animateBad, 16);  // 可能与渲染帧不同步
}
```

### 10.6.3 连续事件的合并

对于高频事件（如 mousemove、touchmove、wheel），Chrome 会在一帧内合并多个事件，只在一帧结束时触发一次回调。这避免了高频事件回调占满主线程。

```
事件合并示例

帧 N（16.6ms）：
  touchmove 事件1 → 排队
  touchmove 事件2 → 合并
  touchmove 事件3 → 合并
  touchmove 事件4 → 合并
  
  帧末：触发一次 touchmove 回调
  （事件对象中有 coalesced events 列表）
```

```javascript
// 获取合并的事件
element.addEventListener('pointermove', (e) => {
  const events = e.getCoalescedEvents();
  // events 包含所有被合并的事件
  // 可以用它们做更精确的处理
  for (const ev of events) {
    drawPoint(ev.x, ev.y);
  }
});
```

> 事件合并是 Chrome 在高频输入场景下保持流畅的关键。一帧内 100 次 touchmove 不会触发 100 次回调，只触发 1 次。开发者可以通过 getCoalescedEvents() 获取所有中间事件，做精确处理。

## 10.7 Pointer Events 统一事件模型

### 10.7.1 Pointer Events 的设计动机

在 Pointer Events 出现之前，开发者需要分别处理 mouse、touch、pen 三种事件。Pointer Events 将这三种输入统一为一套事件模型，简化了多输入设备的处理。

| 传统事件 | Pointer 事件 | 说明 |
|---------|------------|------|
| mousedown | pointerdown | 按下 |
| mousemove | pointermove | 移动 |
| mouseup | pointerup | 松开 |
| mouseenter | pointerenter | 进入 |
| mouseleave | pointerleave | 离开 |
| — | pointercancel | 取消 |

Pointer Events 的事件对象包含统一的属性：pointerType（鼠标/触摸/笔）、pressure（压感）、tiltX/tiltY（倾斜角）、width/height（接触面积）。

### 10.7.2 触摸事件的 Action 链

触摸交互通常由多个事件组成一个 Action 链。浏览器需要正确处理 Action 链中的每个事件，并在适当的时候触发手势识别。

```
触摸 Action 链示例

1. pointerdown → 记录起始位置和时间
2. pointermove × N → 移动中
3. pointerup → 结束

浏览器在 pointermove 阶段做手势识别：
  - 如果水平移动为主 → 识别为水平滚动
  - 如果垂直移动为主 → 识别为垂直滚动
  - 如果多点触摸且距离变化 → 识别为缩放
  - 如果快速移动后停止 → 识别为滑动
```

touch-action CSS 属性可以告诉浏览器哪些手势可以被识别，哪些应该被忽略。浏览器据此提前做手势识别，不需要等待主线程。

> Pointer Events 是未来。它统一了鼠标、触摸、笔三种输入，开发者只需要写一套代码。而且它天然支持合成器的快速路径，性能比分别监听 mouse 和 touch 事件更好。

## 本章核心知识总结

| 知识模块 | 核心内容 | 性能影响 |
|---------|---------|---------|
| 事件管道 | 硬件→OS→Browser→Compositor→Main | 7 个阶段 |
| 快速路径 | 合成器独立处理滚动 | 不阻塞主线程 |
| 事件传播 | 捕获→目标→冒泡 | 事件委托的基础 |
| passive listener | 不调用 preventDefault | 允许快速路径 |
| 命中测试 | 坐标到元素的映射 | 合成层遍历 |
| INP | 交互到绘制的时间 | < 200ms 为好 |
| 事件合并 | 高频事件一帧一次 | 减少回调开销 |

觉得有用？收藏起来，下次排查事件处理性能问题时直接翻出来看。

你在项目中遇到过滚动卡顿的问题吗？是不是 touchmove 监听器导致的？评论区聊聊。

关注怕浪猫，下期我们进入网络栈，讲 DNS 解析、TCP 连接、HTTP 协议基础。系列进度 10/24。

下期预告：第 11 章「DNS 与网络协议基础」。我们会讲 DNS（Domain Name System，域名系统）解析过程、TCP（Transmission Control Protocol，传输控制协议）三次握手与拥塞控制、以及浏览器如何管理网络连接池。怕浪猫下期见。

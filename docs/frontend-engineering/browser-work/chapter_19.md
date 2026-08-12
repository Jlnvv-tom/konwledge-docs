---
sidebar_position: 19
---

# 第19章 内存管理与垃圾回收优化

> JavaScript 开发者不需要手动管理内存，但不理解 GC（Garbage Collection，垃圾回收）机制，就写不出高性能的 Web 应用。一个闭包泄漏的引用，可能让你的页面在长时间运行后变得越来越卡。

我是怕浪猫，上期讲了渲染性能优化，今天进入第 19 章：内存管理与垃圾回收优化。这一章拆解 V8 的分代 GC 机制、内存泄漏的常见模式、以及如何用 DevTools 分析内存问题。

## 19.1 V8 的分代垃圾回收

### 19.1.1 为什么要分代

统计学发现：大多数对象朝生夕死（年轻代），少数对象长期存活（老生代）。V8 基于这个观察将堆分为新生代（Young Generation）和老生代（Old Generation），使用不同的 GC 算法。

```
V8 堆内存结构

堆（Heap）
  ├─ 新生代（Young Generation）
  │   ├─ From 空间（活动对象）
  │   └─ To 空间（空闲）
  │   大小：1-8MB
  │   GC：Scavenge 算法（频繁、快速）
  │
  ├─ 老生代（Old Generation）
  │   ├─ 指针空间（存放指针）
  │   └─ 数据空间（存放数据）
  │   大小：百MB-GB
  │   GC：Mark-Sweep + Mark-Compact（不频繁、较慢）
  │
  └─ 大对象空间（Large Object Space）
      存放超过一定大小的对象
      直接在老生代分配
```

| 区域 | 大小 | GC 算法 | 频率 | 暂停时间 |
|------|------|---------|------|---------|
| 新生代 | 1-8MB | Scavenge（Cheney） | 频繁 | 1-5ms |
| 老生代 | 大 | Mark-Sweep/Compact | 不频繁 | 10-100ms |
| 大对象 | — | 老生代 GC | 同老生代 | 同老生代 |

### 19.1.2 Scavenge 算法（新生代 GC）

Scavenge 算法使用半空间复制策略：将存活对象从 From 空间复制到 To 空间，然后交换两个空间。

```
Scavenge 算法流程

GC 前：
  From: [A] [B] [C] [D] [E]  （A、C、E 存活，B、D 已死）
  To:   [空]

GC 过程：
  1. 从根集开始遍历 From 空间
  2. 找到存活对象 A、C、E
  3. 复制到 To 空间（紧凑排列）
  4. 更新指向 A、C、E 的指针

GC 后：
  From: [空]
  To:   [A] [C] [E]  （紧凑排列，无碎片）
  
  交换 From 和 To
```

Scavenge 的特点：速度快、无碎片，但牺牲一半空间。适合存活率低的新生代。

### 19.1.3 Mark-Sweep 和 Mark-Compact（老生代 GC）

老生代存活率高，不适合复制算法。V8 使用 Mark-Sweep（标记-清除）和 Mark-Compact（标记-整理）。

```
Mark-Sweep 算法

1. 标记阶段（Mark）：
   从根集遍历，标记所有可达对象
   [A]→[B]→[D]  存活
   [C]  不可达 → 死亡

2. 清除阶段（Sweep）：
   清除未标记的对象
   释放空间到空闲链表
   
   结果：[A] [B] [空] [D] [空]
   问题：产生内存碎片
```

```
Mark-Compact 算法

在 Mark-Sweep 基础上增加整理步骤：
  将存活对象移动到一端，消除碎片
  
  [A] [B] [空] [D] [空]
  → 整理 → [A] [B] [D] [空] [空]
  
  消除碎片，但移动对象需要更新指针，耗时更长
```

| 算法 | 碎片 | 速度 | 移动对象 |
|------|------|------|---------|
| Mark-Sweep | 有 | 快 | 否 |
| Mark-Compact | 无 | 慢 | 是 |
| Scavenge | 无 | 中 | 是（复制） |

### 19.1.4 增量标记与并发 GC

老生代 GC 的标记阶段可能需要几十到上百毫秒，导致明显的主线程暂停。V8 使用增量标记（Incremental Marking）和并发标记（Concurrent Marking）减少暂停。

| GC 模式 | 主线程参与 | 暂停时间 | 适用场景 |
|---------|-----------|---------|---------|
| 全量 GC | 全程 | 长（50-100ms） | 紧急 GC |
| 增量 GC | 分片参与 | 短（5-10ms/次） | 一般场景 |
| 并发 GC | 仅同步 | 极短（1-5ms） | 最佳 |

> V8 的 GC 演进方向是「更多并发、更短暂停」。现代 V8 的老生代 GC 几乎全部在辅助线程并发执行，主线程只做极短的同步。这使得 Web 应用在 GC 时几乎不会卡顿。

### 19.1.5 晋升（Promotion）

新生代中经过两次 Scavenge 仍然存活的对象会被晋升到老生代。这避免了长期存活对象在新生代中反复复制。

```
对象晋升流程

新生代对象 A：
  第 1 次 GC → 存活 → 复制到 To 空间，标记年龄 1
  交换空间
  第 2 次 GC → 存活 → 年龄 2 → 晋升到老生代

其他情况：
  To 空间使用超过 25% → 直接晋升部分对象
```

## 19.2 内存泄漏

### 19.2.1 常见内存泄漏模式

| 模式 | 原因 | 示例 |
|------|------|------|
| 意外全局变量 | 未声明变量 | `function() { leaked = 1; }` |
| 被遗忘的定时器 | setInterval 未清除 | 定时器引用 DOM 元素 |
| 闭包引用 | 闭包持有不必要变量 | 事件监听器中的闭包 |
| 脱离 DOM 引用 | JS 引用已移除的 DOM | `const el = document...; el.remove()` |
| Map/Set 强引用 | 未清理的缓存 | 缓存无限增长 |

```javascript
// 1. 意外全局变量
function bad() {
  leaked = 'data';  // 未用 let/const/var → 全局变量
}
// 修复：使用严格模式
'use strict';
function good() {
  const local = 'data';
}

// 2. 被遗忘的定时器
function startTimer() {
  const data = getData();
  setInterval(() => {
    console.log(data);  // data 永远不会回收
  }, 1000);
}
// 修复：保存定时器 ID，不需要时清除
let timerId = setInterval(() => { ... }, 1000);
clearInterval(timerId);

// 3. 闭包引用
function setupHandler() {
  const hugeData = new Array(1000000);
  element.addEventListener('click', () => {
    // 只用了 hugeData.length，但整个数组被闭包持有
    console.log(hugeData.length);
  });
}
// 修复：只提取需要的值
function setupHandler() {
  const hugeData = new Array(1000000);
  const length = hugeData.length;  // 只保存长度
  element.addEventListener('click', () => {
    console.log(length);
  });
}

// 4. 脱离 DOM 引用
const cache = {};
function update() {
  const oldEl = document.querySelector('.item');
  cache.element = oldEl;  // 缓存引用
  oldEl.remove();  // DOM 中移除，但 JS 仍引用
  // oldEl 无法被 GC
}

// 5. 使用 WeakMap 替代 Map
const cache = new Map();  // 强引用，不回收
const weakCache = new WeakMap();  // 弱引用，可回收
```

### 19.2.2 WeakRef 和 FinalizationRegistry

```javascript
// WeakRef：弱引用，不阻止 GC
let target = { data: 'important' };
const weakRef = new WeakRef(target);

// 之后访问
const obj = weakRef.deref();
if (obj) {
  console.log(obj.data);  // 对象还活着
} else {
  console.log('已被 GC');  // 对象被回收
}

// FinalizationRegistry：对象被 GC 时通知
const registry = new FinalizationRegistry((value) => {
  console.log(`对象 ${value} 被 GC 回收了`);
});

let obj = { data: 'test' };
registry.register(obj, 'my-object');
obj = null;  // 解除强引用，GC 后会收到通知
```

> WeakRef 和 FinalizationRegistry 是 ES2021 引入的，让开发者可以与 GC 交互。但不要过度使用——GC 时机不确定，依赖 FinalizationRegistry 做关键逻辑是危险的。

## 19.3 DevTools 内存分析

### 19.3.1 Heap Snapshot

Chrome DevTools 的 Memory 面板提供三种分析模式：Heap Snapshot、Allocation Timeline 和 Allocation Sampling。

```
Heap Snapshot 分析流程

1. 拍摄快照 A
2. 执行操作（可能导致泄漏的操作）
3. 拍摄快照 B
4. 比较 A 和 B
5. 查看 B 中新增的对象
6. 追踪引用链找到泄漏源
```

| 分析模式 | 用途 | 适用场景 |
|---------|------|---------|
| Heap Snapshot | 堆快照 | 分析内存组成 |
| Allocation Timeline | 分配时间线 | 找到分配热点 |
| Allocation Sampling | 分配采样 | 长时间运行分析 |

### 19.3.2 内存分析关键指标

| 指标 | 说明 | 关注点 |
|------|------|--------|
| Shallow Size | 对象自身大小 | 不含引用对象 |
| Retained Size | 对象被回收后释放的大小 | 含引用链 |
| Distance | 到根的引用距离 | 越短越难回收 |

## 19.4 内存优化策略

### 19.4.1 对象池

对于频繁创建销毁的对象，使用对象池减少 GC 压力。

```javascript
class ObjectPool {
  constructor(factory, reset, max = 100) {
    this.factory = factory;
    this.reset = reset;
    this.max = max;
    this.pool = [];
  }
  
  acquire() {
    return this.pool.pop() || this.factory();
  }
  
  release(obj) {
    if (this.pool.length < this.max) {
      this.reset(obj);
      this.pool.push(obj);
    }
  }
}

// 使用：粒子系统
const particlePool = new ObjectPool(
  () => ({ x: 0, y: 0, vx: 0, vy: 0 }),
  (p) => { p.x = 0; p.y = 0; p.vx = 0; p.vy = 0; }
);
```

### 19.4.2 使用 WeakMap 做缓存

```javascript
// WeakMap 缓存：key 被 GC 时自动清理
const cache = new WeakMap();

function expensiveCompute(obj) {
  if (cache.has(obj)) return cache.get(obj);
  const result = doWork(obj);
  cache.set(obj, result);
  return result;
}
// obj 被回收时，缓存自动清除
```

| 缓存策略 | 强引用 | 弱引用 | 适用场景 |
|---------|--------|--------|----------|
| Map | 是 | 否 | 明确生命周期 |
| WeakMap | 否 | 是 | 对象关联缓存 |
| LRU Cache | 是 | 否 | 有上限的缓存 |
| Cache API | 是 | 否 | HTTP 资源缓存 |

### 19.4.3 减少 GC 压力的编码实践

除了对象池，日常编码中还有很多减少 GC 压力的实践：

```javascript
// 1. 复用对象而非反复创建
// 差：每次创建新对象
function update() {
  return { x: Math.random(), y: Math.random() };
}

// 好：复用对象
const pos = { x: 0, y: 0 };
function update() {
  pos.x = Math.random();
  pos.y = Math.random();
  return pos;
}

// 2. 避免在热路径中创建闭包
// 差：每个元素都创建新闭包
elements.forEach(el => {
  el.addEventListener('click', () => handleClick(el));
});

// 好：使用事件委托
document.addEventListener('click', (e) => {
  if (e.target.matches('.item')) handleClick(e.target);
});

// 3. 使用 TypedArray 处理二进制数据
// 差：普通数组
const data = new Array(10000);
for (let i = 0; i < 10000; i++) data[i] = i;

// 好：TypedArray（连续内存，GC 友好）
const data = new Int32Array(10000);
for (let i = 0; i < 10000; i++) data[i] = i;
```

| 实践 | 效果 | 说明 |
|------|------|------|
| 复用对象 | 减少 Scavenge | 避免短命对象 |
| 事件委托 | 减少闭包 | 减少监听器数量 |
| TypedArray | 连续内存 | 减少 GC 开销 |
| 避免频繁拆箱 | 减少临时对象 | number → Number 转换 |

> TypedArray（如 Int32Array、Float64Array）使用连续内存，比普通数组更高效。普通数组是哈希表，元素可以是任意类型，有额外的装箱开销。TypedArray 直接存储数值，内存紧凑，GC 扫描更快。对于数值密集型计算（如 canvas 像素操作、物理引擎），TypedArray 是必选。

## 19.5 V8 GC 调优参数与 Orinoco GC

### 19.5.1 Orinoco GC 详细流程

Orinoco 是 V8 团队对垃圾回收器的一系列优化项目的统称，核心目标是减少 GC 暂停时间。Orinoco 之前，老生代 GC 是全量Stop-the-World（全停顿）的，暂停可能达到 100ms 以上。Orinoco 将 GC 拆分为多个可以并发执行的阶段，使主线程暂停控制在几毫秒内。

```
Orinoco GC 完整流程

1. 并发标记（Concurrent Marking）
   ├─ 辅助线程并发遍历对象图
   ├─ 主线程不参与，继续执行 JS
   └─ 标记存活对象

2. 主线程暂停（Minor Pause）
   ├─ 处理标记完成后的写屏障增量
   ├─ 暂停时间：1-5ms
   └─ 同步标记根集

3. 并发清除（Concurrent Sweeping）
   ├─ 辅助线程并发清理死对象
   ├─ 主线程不参与
   └─ 释放内存到空闲链表

4. 并发整理（Concurrent Compaction）
   ├─ 辅助线程移动存活对象
   ├─ 消除内存碎片
   └─ 主线程只在更新指针时短暂暂停
```

| GC 阶段 | 主线程参与 | 辅助线程 | 暂停时间 |
|---------|-----------|---------|----------|
| 并发标记 | 仅根集同步 | 全程 | 1-5ms |
| 并发清除 | 不参与 | 全程 | 0ms |
| 并发整理 | 指针更新同步 | 全程 | 1-5ms |
| 总暂停 | — | — | 2-10ms |

### 19.5.2 Minor GC 与 Major GC 触发条件

V8 的 GC 分为 Minor GC（新生代 GC）和 Major GC（老生代 GC），它们的触发条件和执行策略完全不同。

```
GC 触发条件

Minor GC（Scavenge）：
  触发：新生代 From 空间用尽
  频率：频繁（每秒可能多次）
  暂停：1-5ms
  动作：复制存活对象到 To 空间，晋升老对象

Major GC（Mark-Sweep/Compact）：
  触发条件（满足任一）：
    1. 老生代空间使用率超过阈值（默认约 70%）
    2. 新生代晋升速率过高
    3. 分配大对象时老生代空间不足
    4. 外部内存限制触发（如 ArrayBuffer）
  频率：不频繁（几秒到几分钟一次）
  暂停：2-10ms（Orinoco 优化后）
  动作：标记清除/整理老生代
```

| GC 类型 | 触发条件 | 暂停时间 | 频率 |
|---------|---------|----------|------|
| Minor GC | 新生代空间用尽 | 1-5ms | 频繁 |
| Major GC | 老生代使用率超阈值 | 2-10ms | 不频繁 |
| Full GC | 紧急内存不足 | 10-100ms | 极少 |
| Incremental | 分配速率稳定时周期触发 | 5-10ms/次 | 周期性 |

### 19.5.3 V8 GC 调优参数

Node.js 环境下可以通过 V8 flags 调整 GC 参数，浏览器环境虽然不能直接设置，但理解这些参数有助于分析 GC 行为。

```
常用 V8 GC 调优参数

--max-old-space-size=4096
  老生代最大空间（MB），默认根据系统自动调整
  增大可减少 Major GC 频率，但单次暂停可能更长

--max-semi-space-size=64
  新生代半空间大小（MB），默认 1-8MB
  增大可减少 Minor GC 频率，适合分配密集型应用

--gc-interval=100
  GC 触发间隔（分配 N 次后触发），值越大 GC 越懒

--trace-gc
  输出 GC 日志，用于分析 GC 频率和耗时

--expose-gc
  暴露 gc() 函数，允许手动触发 GC
```

```javascript
// Node.js 中手动触发 GC（需 --expose-gc 标志）
// node --expose-gc app.js
if (global.gc) {
  global.gc();  // 强制执行 GC
}

// 浏览器中无法手动触发 GC
// 但可以通过 Performance.measureUserAgentSpecificMemory 观察内存
performance.measureUserAgentSpecificMemory().then(result => {
  console.log('JS 堆大小:', result.bytes);
});
```

| 参数 | 默认值 | 作用 | 调优建议 |
|------|--------|------|----------|
| max-old-space-size | 自动 | 老生代上限 | 大内存应用增大 |
| max-semi-space-size | 1-8MB | 新生代半空间 | 分配密集型增大 |
| gc-interval | 100 | GC 触发间隔 | 降低频率减开销 |
| trace-gc | 关闭 | GC 日志 | 调试时开启 |

> 在浏览器中无法直接设置 V8 flags，但理解这些参数对分析 Chrome DevTools 中的 GC 行为很有帮助。通过 Performance 面板可以看到 Minor GC 和 Major GC 的频率和耗时，据此判断是否需要优化内存分配模式。

## 19.6 内存泄漏排查实战案例

### 19.6.1 案例一：单页应用路由泄漏

现象：一个 SPA（Single Page Application，单页应用）在频繁切换路由 30 分钟后，内存从 50MB 增长到 500MB，页面明显卡顿。

排查步骤：

```
步骤一：建立基线
  1. 打开 DevTools → Memory 面板
  2. 刷新页面，等待初始加载完成
  3. 点击「Take Heap Snapshot」拍摄快照 A
  4. 记录：45MB

步骤二：操作复现
  5. 在路由 A 和路由 B 之间切换 20 次
  6. 点击「Take Heap Snapshot」拍摄快照 B
  7. 记录：120MB

步骤三：比较快照
  8. 选择快照 B，视图切换为「Comparison」
  9. 对比对象选择快照 A
  10. 按「Delta」排序，找到新增最多的对象类型
  11. 发现：Detached DOM 节点增加 2000+

步骤四：追踪引用链
  12. 选中 Detached DOM 节点
  13. 查看下方「Retainers」面板
  14. 追踪引用链：
      Detached div
        ← eventListenerMap
          ← WeakMap (但实际是强引用持有)
            ← Router.cache
              ← Router (全局)
```

```javascript
// 问题代码：路由缓存持有已销毁组件的 DOM 引用
const routeCache = new Map();

class Router {
  navigate(route) {
    // 缓存旧路由的 DOM
    const oldView = document.querySelector('#app');
    routeCache.set(this.currentRoute, oldView);  // 强引用！
    
    // 加载新路由
    this.currentRoute = route;
    document.querySelector('#app').innerHTML = '';
    document.querySelector('#app').appendChild(routeCache.get(route));
  }
}

// 修复：使用 WeakMap 或在路由切换时清理引用
class FixedRouter {
  constructor() {
    this.routeCache = new WeakMap();  // 改用弱引用
  }
  
  navigate(route) {
    // 清理旧视图的事件监听器
    const oldView = document.querySelector('#app');
    oldView.querySelectorAll('*').forEach(el => {
      el.removeEventListener();  // 清理事件监听
    });
    
    this.currentRoute = route;
    // 重新创建视图，不缓存 DOM
    document.querySelector('#app').innerHTML = '';
    this.renderRoute(route);
  }
}
```

### 19.6.2 案例二：WebSocket 数据累积泄漏

现象：一个实时数据看板页面，每秒通过 WebSocket 接收 100 条数据，运行 2 小时后内存持续增长。

```
排查流程：

1. 使用 Allocation Timeline 模式
2. 开始录制 → 运行 30 秒 → 停止
3. 发现每秒有大量 Array 和 Object 分配
4. 但这些数组应该被处理后丢弃
5. 查看 Retainers：
   data_array
     ← messageQueue (模块级变量)
       ← module scope

问题根因：
  WebSocket 消息处理函数将所有数据推入全局队列
  消费者处理后没有从队列中移除
```

```javascript
// 问题代码
const messageQueue = [];  // 全局队列，只进不出

ws.onmessage = (event) => {
  messageQueue.push(JSON.parse(event.data));
};

// 消费者：处理但不清除
setInterval(() => {
  const data = messageQueue[0];  // 只读第一个
  updateChart(data);
  // 忘了 messageQueue.shift()！
}, 100);

// 修复：处理后移除
setInterval(() => {
  while (messageQueue.length > 0) {
    const data = messageQueue.shift();
    updateChart(data);
  }
}, 100);

// 更好的方案：使用环形缓冲区
class RingBuffer {
  constructor(size) {
    this.buffer = new Array(size);
    this.size = size;
    this.head = 0;
    this.tail = 0;
  }
  push(item) {
    this.buffer[this.tail] = item;
    this.tail = (this.tail + 1) % this.size;
    if (this.tail === this.head) {
      this.head = (this.head + 1) % this.size;  // 覆盖旧数据
    }
  }
  pop() {
    if (this.head === this.tail) return null;
    const item = this.buffer[this.head];
    this.buffer[this.head] = null;
    this.head = (this.head + 1) % this.size;
    return item;
  }
}
```

## 19.7 WeakRef 使用场景与限制

### 19.7.1 适用场景

WeakRef 适合需要与对象生命周期关联但不希望阻止 GC 的场景。最典型的用途是缓存、观察者模式和资源管理。

```javascript
// 场景一：对象关联缓存
// 当 key 对象可能被回收时，缓存自动清理
const metadataCache = new WeakMap();

function getMetadata(obj) {
  if (!metadataCache.has(obj)) {
    metadataCache.set(obj, computeMetadata(obj));
  }
  return metadataCache.get(obj);
}

// 场景二：WeakRef + FinalizationRegistry 实现可回收缓存
class WeakCache {
  constructor() {
    this.cache = new Map();
    this.registry = new FinalizationRegistry(key => {
      // 对象被 GC 时，清理缓存条目
      this.cache.delete(key);
    });
  }

  set(key, value) {
    const ref = new WeakRef(value);
    this.cache.set(key, ref);
    this.registry.register(value, key);
  }

  get(key) {
    const ref = this.cache.get(key);
    if (!ref) return undefined;
    const value = ref.deref();
    if (!value) {
      this.cache.delete(key);
      return undefined;
    }
    return value;
  }
}

// 场景三：事件监听器弱引用
// 避免监听器阻止订阅者被 GC
class EventEmitter {
  constructor() {
    this.listeners = new Set();
  }
  
  subscribe(callback) {
    const ref = new WeakRef(callback);
    this.listeners.add(ref);
    return () => this.listeners.delete(ref);
  }
  
  emit(data) {
    for (const ref of this.listeners) {
      const cb = ref.deref();
      if (cb) cb(data);
      else this.listeners.delete(ref);
    }
  }
}
```

### 19.7.2 使用限制与注意事项

| 限制 | 说明 | 风险 |
|------|------|------|
| GC 时机不确定 | FinalizationRegistry 回调时机不可预测 | 不能依赖它做关键逻辑 |
| 回调可能丢失 | 进程退出前可能不触发回调 | 资源可能泄漏 |
| 多次回调 | 同一对象可能触发多次回调 | 需要做幂等处理 |
| 性能开销 | WeakRef 比 Strong Ref 慢 | 热路径避免使用 |
| 调试困难 | 弱引用对象在 DevTools 中难以追踪 | 排查问题复杂 |

```javascript
// 反面教材：不要这样用 WeakRef
const criticalResources = new WeakRef(loadCriticalData());

function doCriticalWork() {
  const data = criticalResources.deref();
  if (!data) {
    // 如果数据被 GC 了，重新加载——但时机不可控！
    // 这会导致不可预测的行为
    data = loadCriticalData();
  }
  process(data);
}

// 正确做法：关键资源用强引用
const criticalResources = loadCriticalData();
// 在明确的生命周期结束时手动释放
function cleanup() {
  criticalResources.dispose();
}
```

> WeakRef 的设计意图是「优化」而非「功能」。它让你可以构建更智能的缓存策略，但不应该用它来管理关键资源。如果你发现自己在用 WeakRef 管理数据库连接、文件句柄等关键资源，说明架构设计有问题。

## 19.8 SharedArrayBuffer 与内存共享

### 19.8.1 SharedArrayBuffer 基础

SharedArrayBuffer（SAB）允许多个线程（主线程和 Web Worker）共享同一块内存。这在多线程计算、音频处理、图像处理等场景中非常有用。

```javascript
// 主线程创建共享内存
const buffer = new SharedArrayBuffer(1024);  // 1KB 共享内存
const view = new Int32Array(buffer);  // 通过视图操作

// 传递给 Worker
const worker = new Worker('worker.js');
worker.postMessage(buffer);

// worker.js
self.onmessage = (e) => {
  const buffer = e.data;
  const view = new Int32Array(buffer);
  // 读写同一块内存
  view[0] = 42;
};
```

### 19.8.2 Atomics 原子操作

多线程共享内存需要同步机制。Atomics API 提供原子操作，确保操作的不可分割性。

```javascript
// 原子操作示例
const buffer = new SharedArrayBuffer(4);
const view = new Int32Array(buffer);

// 原子写入
Atomics.store(view, 0, 42);

// 原子读取
const value = Atomics.load(view, 0);

// 原子比较并交换（CAS）
const old = Atomics.compareExchange(view, 0, 42, 100);
// 如果 view[0] === 42，则设为 100，返回旧值

// 原子加法
Atomics.add(view, 0, 10);  // view[0] += 10

// 等待和通知（线程同步）
Atomics.wait(view, 0, 0);  // 如果 view[0] === 0，则阻塞
Atomics.notify(view, 0, 1);  // 唤醒 1 个等待的线程
```

```
多线程计算模型

主线程                    Worker 1              Worker 2
  │                         │                     │
  ├─ 创建 SAB ──────────────┼─────────────────────┤
  │                         │                     │
  ├─ postMessage(SAB) ─────→│                     │
  ├─ postMessage(SAB) ────────────────────────────→│
  │                         │                     │
  │                    Atomics.store()        Atomics.store()
  │                    view[0] = 1            view[1] = 2
  │                         │                     │
  ├─ Atomics.wait() ◄───────┤                     │
  │   (阻塞等待)             │                     │
  │                    Atomics.notify()            │
  ├─ 被唤醒 ◄───────────────┘                     │
  │                         │                     │
  └─ 读取结果                └─                    └─
```

| 操作 | 说明 | 同步性 |
|------|------|--------|
| Atomics.store | 原子写入 | 是 |
| Atomics.load | 原子读取 | 是 |
| Atomics.add/sub | 原子加减 | 是 |
| Atomics.compareExchange | 原子 CAS | 是 |
| Atomics.wait/notify | 线程同步 | 阻塞 |

### 19.8.3 安全限制与 COOP/COEP

由于 Spectre 漏洞，浏览器对 SharedArrayBuffer 圚了安全限制。页面必须设置 COOP（Cross-Origin Opener Policy）和 COEP（Cross-Origin Embedder Policy）头才能使用 SAB。

```http
# 必须设置以下响应头才能使用 SharedArrayBuffer
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

| 头部 | 作用 | 值 |
|------|------|----|
| COOP | 隔离顶级文档 | same-origin |
| COEP | 隔离嵌入资源 | require-corp |

> 设置 COOP/COEP 后，页面不能加载跨域资源（除非对方设置了 CORP 头）。这可能导致第三方资源加载失败，需要逐个排查。可以使用 `Cross-Origin-Resource-Policy: cross-origin` 来允许特定资源被加载。

## 19.9 TypedArray 内存布局详解

### 19.9.1 TypedArray vs 普通数组

TypedArray 是 ES6 引入的二进制数据数组，底层是 ArrayBuffer（一段连续内存）。与普通数组相比，TypedArray 内存紧凑、访问快速、GC 友好。

```
TypedArray 内存布局

Int32Array(5) 的内存布局：

地址:  0x00  0x04  0x08  0x0C  0x10
       ┌─────┬─────┬─────┬─────┬─────┐
       │  1  │  2  │  3  │  4  │  5  │  每个元素 4 字节
       └─────┴─────┴─────┴─────┴─────┘
       总计：20 字节连续内存

普通 Array 的内存布局（V8 实现）：

  ┌──────────┐
  │ Elements │ → 指向一块内存，存储指向值的指针
  │  Map     │ → 每个元素是指针，指向装箱后的值
  │  ...     │
  └──────────┘
  
  每个元素可能分散在不同位置
  数值需要装箱（HeapNumber）
  额外的哈希表开销
```

| 特性 | TypedArray | 普通数组 |
|------|-----------|----------|
| 内存布局 | 连续 | 哈希表/指针数组 |
| 元素类型 | 固定 | 任意 |
| 装箱开销 | 无 | 有（HeapNumber）|
| 访问速度 | O(1) 直接偏移 | O(1) 但有间接开销 |
| GC 压力 | 低（连续扫描）| 高（逐个扫描）|
| 内存占用 | 紧凑 | 有额外开销 |

### 19.9.2 TypedArray 类型一览

```javascript
// 有符号整数
const int8 = new Int8Array(10);      // 1 字节/元素，-128~127
const int16 = new Int16Array(10);    // 2 字节/元素，-32768~32767
const int32 = new Int32Array(10);    // 4 字节/元素
const bigint64 = new BigInt64Array(10); // 8 字节/元素

// 无符号整数
const uint8 = new Uint8Array(10);    // 0~255
const uint16 = new Uint16Array(10);  // 0~65535
const uint32 = new Uint32Array(10);  // 0~4294967295

// 浮点数
const float32 = new Float32Array(10); // 4 字节，单精度
const float64 = new Float64Array(10); // 8 字节，双精度

// Uint8Clamped：值被限制在 0-255（用于 ImageData）
const clamped = new Uint8ClampedArray(10);
clamped[0] = 300;  // 自动变为 255
clamped[1] = -10;  // 自动变为 0
```

| 类型 | 字节/元素 | 范围 | 用途 |
|------|-----------|------|------|
| Int8Array | 1 | -128~127 | 小整数 |
| Uint8Array | 1 | 0~255 | 字节数据/像素 |
| Uint8ClampedArray | 1 | 0~255（clamped）| Canvas ImageData |
| Int16Array | 2 | -32768~32767 | 音频/短整数 |
| Uint16Array | 2 | 0~65535 | Unicode/端口 |
| Int32Array | 4 | -2^31~2^31-1 | 通用整数 |
| Uint32Array | 4 | 0~2^32-1 | 颜色值（RGBA）|
| Float32Array | 4 | 单精度浮点 | GPU 顶点数据 |
| Float64Array | 8 | 双精度浮点 | 精确计算 |
| BigInt64Array | 8 | 64位整数 | 大数计算 |

### 19.9.3 DataView 与平台字节序

同一块 ArrayBuffer 可以用不同方式解读。DataView 提供了按指定字节序读写的方法，在处理二进制文件和网络协议时非常重要。

```javascript
const buffer = new ArrayBuffer(8);
const view = new DataView(buffer);

// 写入（指定小端序）
view.setInt32(0, 42, true);   // true = little-endian
view.setFloat32(4, 3.14, true);

// 读取
console.log(view.getInt32(0, true));   // 42
console.log(view.getFloat32(4, true));  // 3.14

// 检测平台字节序
const buf = new ArrayBuffer(2);
new DataView(buf).setInt16(0, 256, true);
const isLittleEndian = new Int16Array(buf)[0] === 256;
console.log('小端序:', isLittleEndian);  // x86/ARM 通常为 true
```

## 19.10 大页内存（Large Page）支持

### 19.10.1 什么是大页内存

CPU 通过 TLB（Translation Lookaside Buffer，页表缓存）将虚拟地址映射到物理地址。标准内存页大小为 4KB，大页（Huge Pages）通常为 2MB 或 1GB。使用大页可以减少 TLB Miss，提高内存密集型应用的性能。

```
普通页 vs 大页

4KB 普通页：
  1GB 内存需要 262,144 个页表项
  TLB 缓存有限 → 频繁 TLB Miss → 性能下降

2MB 大页：
  1GB 内存需要 512 个页表项
  TLB 缓存利用率提升 512 倍
  减少 TLB Miss → 性能提升
```

| 页大小 | 页表项数（1GB）| TLB Miss 概率 | 适用场景 |
|--------|---------------|--------------|----------|
| 4KB | 262,144 | 高 | 通用 |
| 2MB | 512 | 低 | 大内存应用 |
| 1GB | 1 | 极低 | 超大内存应用 |

### 19.10.2 Chrome 与 V8 的大页支持

V8 从 7.3 版本开始支持大页内存。当操作系统配置了大页时，V8 会自动将老生代堆分配在大页上，以减少 TLB Miss 并提高 GC 性能。

```
V8 大页内存使用条件

1. 操作系统支持大页（Linux: transparent hugepage）
2. V8 堆大小超过阈值（通常 32MB+）
3. 老生代空间自动使用大页

效果：
  - GC 标记阶段速度提升 4-8%
  - 内存访问延迟降低
  - TLB Miss 减少 10x+
```

在 Linux 上可以通过以下命令检查和配置大页：

```bash
# 查看大页状态
cat /proc/meminfo | grep Huge
# HugePages_Total:       0
# HugePages_Free:        0
# HugePages_Rsvd:        0
# HugePages_Surp:        0
# Hugepagesize:       2048 kB

# 设置大页数量（需要 root）
echo 100 > /proc/sys/vm/nr_hugepages

# 透明大页（THP）— 自动管理
echo always > /sys/kernel/mm/transparent_hugepage/enabled
```

> 在浏览器环境中，开发者无法直接控制大页使用。Chrome 会根据系统配置自动选择是否使用大页。但理解大页机制有助于解释为什么在某些系统上 Chrome 表现更好——服务器和桌面系统的内存配置不同，大页支持程度也不同。

## 19.11 内存管理实战经验总结

在实际项目中，内存问题往往不是单一原因导致的，而是多种因素叠加的结果。以下总结了在大型 Web 应用中常见的内存问题和解决思路，这些经验来自多个生产环境的真实案例。

### 19.11.1 长时间运行页面的内存治理

单页应用最大的内存挑战在于页面不刷新，所有对象都在同一个堆中积累。一个运行了数小时的 SPA，如果不做内存管理，内存占用会持续增长。这种增长不是传统意义上的泄漏，而是缓存累积、事件监听器未清理、以及框架内部的抽象层产生的临时对象。

治理长时间运行页面的第一步是建立内存监控基线。在持续集成的环境中，可以使用 Puppeteer 自动化脚本定期访问页面，记录 `performance.memory.usedJSHeapSize` 的值。如果内存在一个小时内持续增长超过百分之二十，就需要介入排查。这种监控应该覆盖核心业务流程，包括路由切换、数据加载、表单提交等常见操作路径。

第二步是建立内存预算机制。为不同类型的对象设定内存上限，比如缓存不超过五十兆字节、图片资源不超过一百兆字节。当某个类别的内存使用接近上限时，触发清理逻辑。这种机制可以使用 LRU（Least Recently Used，最近最少使用）缓存来实现，自动淘汰最久未使用的条目。

第三步是定期执行深度清理。对于长时间运行的页面，可以在用户空闲时触发清理操作，使用 `requestIdleCallback` 在浏览器空闲时释放不再需要的资源。这包括清理对象池中多余的实例、移除过期的缓存条目、以及释放不再使用的 TypedArray 缓冲区。深度清理的策略需要根据应用特点定制，比如电商应用可以清理已关闭商品详情页的图片缓存，社交应用可以清理已读消息的媒体资源。

在实际项目中，内存治理还需要考虑框架本身的行为。React 的虚拟 DOM 树在路由切换时如果没有正确卸载组件，会保留大量不再需要的 DOM 节点和组件状态。Vue 的响应式系统在销毁组件时如果没有移除所有依赖追踪，也会造成内存泄漏。Angular 的变更检测在销毁组件后如果仍然监听 Observable，订阅关系不会自动断开。这些框架层面的内存问题需要通过定期检查组件生命周期来发现和修复。

### 19.11.2 V8 隐藏类与内存优化

V8 使用隐藏类（Hidden Class，内部称为 Map）来优化对象属性访问。每个对象都有一个关联的隐藏类，记录了属性的布局信息。当对象的属性结构发生变化时，V8 会创建一个新的隐藏类并切换到它。频繁的属性结构变化会导致隐藏类分裂（Hidden Class Transition Chain 过长），降低属性访问速度并增加内存开销。

为了避免隐藏类问题，应该在构造函数中声明所有属性，包括那些初始值为 `null` 或 `undefined` 的属性。这样 V8 在对象创建时就确定了完整的隐藏类，后续赋值不会触发隐藏类变更。对于需要动态添加属性的场景，考虑使用对象池来复用已有对象，而不是反复创建结构不同的新对象。

另一个值得注意的点是数字属性的处理。V8 将数字索引属性存储在单独的元素存储中，不直接影响隐藏类。但如果一个对象同时有字符串属性和数字属性，V8 需要维护两套数据结构，增加了内存开销。在性能敏感的场景中，应该将混合数据拆分为独立的对象，一个专门存储数字索引数据，另一个存储命名字段。

隐藏类的另一个影响是 megamorphic 状态。当一个函数被调用时传入的对象有不同隐藏类，V8 无法内联缓存优化，每次属性访问都需要查找隐藏类链。如果在一个热函数中传入超过四种不同隐藏类的对象，V8 会进入 megamorphic 状态，性能显著下降。解决方法是确保传入同一函数的对象有相同的属性结构，或者在性能关键路径上使用 monomorphic 模式。

### 19.11.3 垃圾回收友好型代码模式

编写垃圾回收友好的代码是一种习惯。核心原则是减少短命对象的创建数量，让对象尽可能复用。在热路径（每帧执行的代码）中，每一个临时对象的创建都会增加新生代的压力。虽然单个 Scavenge 只需要几毫秒，但如果每秒触发数十次，累积的暂停时间就不可忽视。

一个常见的优化场景是事件处理函数中的对象创建。在滚动事件处理中，如果每次都创建新的事件对象或数据对象，每秒可能产生数百个短命对象。正确的做法是在外部预先创建复用对象，在事件处理中只更新其属性值。这种模式在游戏循环和动画处理中尤为重要。

另一个容易忽视的问题是字符串拼接。在循环中使用加号拼接字符串会产生大量中间字符串对象。虽然现代 V8 对字符串拼接有优化，但在复杂场景中仍建议使用数组 `join` 方法或模板字符串。对于需要大量字符串操作的场景，考虑使用 `TextEncoder` 和 `TextDecoder` 配合 `Uint8Array` 来避免字符串对象的创建。

闭包是 JavaScript 的强大特性，但也是内存泄漏的高发区。每个闭包都会持有其定义作用域中的所有变量引用，即使闭包本身只使用了其中一个变量。在事件监听器中使用闭包时，应该只捕获必要的值，而不是整个作用域。如果闭包引用了大对象，即使大对象在其他地方不再需要，也不会被回收，直到闭包本身被释放。

函数柯里化和高阶函数的使用也需要注意内存。每次柯里化调用都会创建一个新的闭包，持有前序参数的引用。在频繁调用的场景中，这些闭包会快速累积。如果柯里化函数只在初始化时使用，可以考虑在初始化完成后手动设为 `null`，释放闭包持有的引用。

### 19.11.4 性能监控与内存预算实践

在生产环境中监控内存的最佳实践是结合多种指标。`performance.memory` 虽然只提供近似值，但足以发现趋势性问题。更精确的方案是定期调用 `performance.measureUserAgentSpecificMemory`，这个 API 返回更准确的堆大小估算。

建立内存预算的关键是了解应用在各种设备上的内存限制。低端 Android 设备可能只有 1GB 可用内存，其中浏览器分配给 JS 堆的可能只有 100-200MB。如果应用的目标设备包括低端机，内存预算应该设定得更保守。一个经验法则是将 JS 堆大小控制在设备总内存的百分之五以内。

当内存使用超过预算时，应该按优先级释放资源。最先释放的是非关键缓存，比如图片缩略图缓存、预取的数据。其次是可重建的中间状态，比如列表的滚动位置、表单的临时数据。最后才是用户数据的降级，比如卸载非可见区域的组件、释放离屏的画布。这种渐进式降级策略可以在保证核心功能可用的前提下尽可能延长页面的运行时间。

内存监控还应该考虑跨标签页的影响。现代浏览器为每个标签页分配独立的渲染进程，但多个标签页共享同一个 GPU 进程和部分系统资源。如果用户打开了多个标签页，每个标签页的内存使用都会影响整体性能。Service Worker 的内存使用也需要监控，因为 Service Worker 在后台运行，其内存泄漏不会立即被用户感知。

### 19.11.5 V8 内存分配与回退机制

V8 在分配内存时会根据对象大小选择不同的分配策略。小对象直接在新生代分配，大对象则在大对象空间分配。大对象空间使用独立的内存页，不会因为 Scavenge 而被复制。但大对象的分配和回收都有更高的开销，因为每个大对象都需要独立的内存页和页表项。

当内存分配失败时，V8 会触发一系列回退机制。首先是触发 Minor GC 回收新生代。如果仍然不够，触发 Major GC 回收老生代。如果还是不够，触发 Full GC 回收所有空间。最后如果还是无法满足分配需求，V8 会请求操作系统扩展堆内存。如果操作系统也无法分配（达到内存限制），V8 会抛出 Out of Memory 错误。

理解这个回退机制对于分析性能问题很重要。如果应用频繁触发 Full GC，说明内存使用已经接近极限，需要优化内存使用或增加堆大小限制。Full GC 的暂停时间通常在几十到上百毫秒，会明显影响用户体验。通过 Performance 面板可以看到 GC 事件的频率和耗时，如果发现 Full GC 频繁出现，就需要紧急介入排查。

### 19.11.6 内存碎片与整理策略

长时间运行的 Web 应用可能面临内存碎片问题。频繁的分配和释放会在堆中产生大量不连续的空闲块。当需要分配一个大对象时，虽然总空闲空间足够，但没有一个连续的空闲块能容纳这个对象。V8 通过 Mark-Compact 算法解决这个问题，将存活对象移动到一端，释放出连续的空闲空间。

但整理操作本身有开销。V8 不是每次 GC 都做整理，而是在碎片化达到一定程度后才触发整理。这种策略在大多数场景下是合理的，因为大多数应用对碎片化不敏感。但如果应用经常分配大小不一的对象，碎片化可能导致频繁的整理操作，增加 GC 暂停时间。

减少碎片化的实践包括：尽量使用相同大小的对象（比如固定大小的粒子对象），避免在老生代中频繁分配和释放大对象，以及使用 TypedArray 代替普通数组存储数值数据。TypedArray 使用连续内存，不会产生碎片。

### 19.11.7 DevTools 内存分析进阶技巧

除了基本的快照比较，DevTools 的 Memory 面板还有几个进阶功能值得掌握。第一个是「Retainers」面板的引用链分析。当你在快照中找到一个可疑对象时，Retainers 面板会显示从根集到该对象的完整引用链。理解引用链是定位泄漏根因的关键——你需要找到引用链中不应该存在的那个引用。

第二个是 Allocation Sampling 模式。与 Heap Snapshot 不同，Allocation Sampling 不记录每个对象的完整信息，而是按采样率记录分配热点。这种模式对运行时性能影响小，适合长时间运行的内存分析。在不确定是否有泄漏时，先用 Allocation Sampling 跑一段时间，找到分配最多的函数，再用 Heap Snapshot 精确定位。

第三个是 Detached DOM 节点的检测。当一个 DOM 节点从文档树中移除后，如果 JavaScript 仍然引用它，这个节点就变成了 Detached DOM。DevTools 的 Heap Snapshot 可以过滤出所有 Detached DOM 节点，这是排查 DOM 泄漏的最快方式。在快照的 Class Filter 中输入「Detached」即可看到所有脱离文档的 DOM 节点。

## 本章核心知识总结

| 知识模块 | 核心内容 | 实践意义 |
|---------|---------|---------|
| 分代 GC | 新生代 Scavenge + 老生代 Mark-Sweep | 理解 GC 暂停 |
| 晋升机制 | 两次 GC 存活 → 老生代 | 避免长期存活大对象 |
| 内存泄漏 | 5 种常见模式 | 定期排查 |
| WeakRef | 弱引用 API | 谨慎使用 |
| DevTools | Heap Snapshot | 泄漏定位 |
| 对象池 | 减少 GC 压力 | 高频创建场景 |

觉得有用？收藏起来，下次排查内存泄漏时翻出来看。

你遇到过 JavaScript 内存泄漏吗？是怎么发现的？评论区聊聊。

关注怕浪猫，下期我们讲加载性能优化。系列进度 19/24。

下期预告：第 20 章「加载性能优化」。我们会拆解代码分割（Code Splitting）、资源预加载策略、Service Worker 缓存、以及 HTTP 缓存的层次设计。怕浪猫下期见。

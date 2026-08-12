---
sidebar_position: 15
---

# 第15章 性能优化：FPS、脏矩形、批处理与内存管理

60fps 不是一个数字，是一种信仰。

掉到 30fps 用户会觉得卡，掉到 15fps 用户会觉得崩。性能优化是 Canvas 项目从"能用"到"好用"的关键一跃。

我是怕浪猫，这一章从监控、渲染、内存三个层面，系统地讲 Canvas 性能优化。不是零散的技巧堆砌，而是一套可复用的优化方法论。

## 15.1 性能监控

### 15.1.1 FPS 监控实现

FPS（Frames Per Second，每秒帧数）是最直观的性能指标。实现一个准确的 FPS 监控：

```javascript
class FPSMonitor {
  constructor() {
    this.frames = 0;
    this.lastTime = performance.now();
    this.fps = 0;
    this.frameTime = 0;
    this.history = [];  // 保留最近 60 帧的数据
  }
  
  update() {
    const now = performance.now();
    const delta = now - this.lastTime;
    this.frameTime = delta;
    this.frames++;
    
    // 每秒更新一次 FPS 显示
    if (delta >= 1000) {
      this.fps = Math.round((this.frames * 1000) / delta);
      this.frames = 0;
      this.lastTime = now;
    }
    
    // 记录帧时间历史
    this.history.push(delta);
    if (this.history.length > 60) this.history.shift();
    
    this.lastTime = now;
  }
  
  // 获取统计信息
  getStats() {
    const sorted = [...this.history].sort((a, b) => a - b);
    return {
      fps: this.fps,
      frameTime: this.frameTime.toFixed(2),
      avgFrameTime: (this.history.reduce((a, b) => a + b, 0) / this.history.length).toFixed(2),
      p95: sorted[Math.floor(sorted.length * 0.95)]?.toFixed(2) || 0,
      p99: sorted[Math.floor(sorted.length * 0.99)]?.toFixed(2) || 0,
    };
  }
}

// 使用
const monitor = new FPSMonitor();
function animate() {
  monitor.update();
  // ...渲染逻辑
  requestAnimationFrame(animate);
}
```

> 金句：只看平均 FPS 不够——P95 和 P99 帧时间才能告诉你"最卡的时候有多卡"。

### 15.1.2 帧预算分析

一帧的时间预算是 16.67ms（60fps）。这 16.67ms 要分配给多个环节：

```
帧预算分配（16.67ms）：
┌─────────────────────────────────────────────┐
│ JS 逻辑计算        │ 2-3ms  │ 碰撞检测/状态更新/数据计算  │
│ DOM 操作           │ 0-1ms  │ 尽量避免                    │
│ Canvas 绘制        │ 8-10ms │ 清屏+绘制所有图元           │
│ GPU 传输+合成      │ 2-3ms  │ 纹理上传/合成层             │
│ 浏览器内部工作     │ 1-2ms  │ GC/事件处理                 │
└─────────────────────────────────────────────┘
```

用 Performance API 精确测量各环节耗时：

```javascript
function frameWithProfiling() {
  const t0 = performance.now();
  
  // JS 逻辑
  updatePhysics();
  const t1 = performance.now();
  
  // Canvas 绘制
  ctx.clearRect(0, 0, width, height);
  renderScene();
  const t2 = performance.now();
  
  // 提交到 GPU（drawImage / commit）
  const t3 = performance.now();
  
  console.log({
    logic: (t1 - t0).toFixed(2),
    render: (t2 - t1).toFixed(2),
    overhead: (t3 - t2).toFixed(2),
    total: (t3 - t0).toFixed(2),
  });
  
  requestAnimationFrame(frameWithProfiling);
}
```

### 15.1.3 Chrome DevTools 性能分析

Chrome DevTools 的 Performance 面板是分析 Canvas 性能的首选工具：

**分析步骤**：
1. 打开 DevTools → Performance 面板
2. 点击录制按钮
3. 操作页面（触发卡顿场景）
4. 停止录制
5. 查看 Timeline 中的长任务（红色标记）

**关键指标**：
- Main 线程的火焰图中寻找长函数调用
- GPU 线程的活动中寻找长时间占用
- Frames 行中查看每帧的耗时
- 查看是否触发 Layout/Paint（应尽量避免）

## 15.2 渲染优化

### 15.2.1 脏矩形优化

脏矩形（Dirty Rectangle）优化的核心思想：每帧只重绘发生变化的区域，而不是整个画布。

```javascript
class DirtyRectRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.dirtyRegions = [];  // 脏区域列表
    this.objects = [];       // 场景对象
  }
  
  // 标记脏区域
  markDirty(x, y, w, h) {
    this.dirtyRegions.push({ x, y, w, h });
  }
  
  // 渲染
  render() {
    if (this.dirtyRegions.length === 0) return;
    
    // 合并重叠的脏区域
    const merged = this.mergeRegions(this.dirtyRegions);
    
    // 只清除并重绘脏区域
    for (const region of merged) {
      // 清除脏区域
      this.ctx.clearRect(region.x, region.y, region.w, region.h);
      
      // 设置裁剪区域，只绘制脏区域内的对象
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.rect(region.x, region.y, region.w, region.h);
      this.ctx.clip();
      
      // 绘制与脏区域相交的对象
      for (const obj of this.objects) {
        if (this.intersects(obj.getBounds(), region)) {
          obj.draw(this.ctx);
        }
      }
      
      this.ctx.restore();
    }
    
    this.dirtyRegions = [];
  }
  
  // 简化的区域合并（实际实现可更复杂）
  mergeRegions(regions) {
    // 简化版：返回原始区域
    // 完整版应合并重叠/相邻区域
    return regions;
  }
  
  intersects(a, b) {
    return !(a.x + a.w < b.x || b.x + b.w < a.x ||
             a.y + a.h < b.y || b.y + b.h < a.y);
  }
}
```

**脏矩形适用场景**：对象数量多但每帧只有少量对象变化（如 UI 界面、编辑器）。

**不适用场景**：每帧所有对象都变化（如全屏粒子系统）。

> 金句：脏矩形不是万能的——如果你的画面每帧都在全局变化，脏矩形反而增加了计算开销。

### 15.2.2 分层渲染

将不同更新频率的内容放到不同的 Canvas 层：

```javascript
// 三层架构
const layers = {
  background: createLayer(),  // 静态背景，只在初始化时绘制一次
  content: createLayer(),     // 内容层，按需重绘
  interaction: createLayer(), // 交互层，每帧重绘
};

// 背景层：只画一次
function initBackground() {
  const ctx = layers.background.ctx;
  drawGrid(ctx);
  drawStaticElements(ctx);
}

// 内容层：数据变化时重绘
function renderContent() {
  const ctx = layers.content.ctx;
  ctx.clearRect(0, 0, width, height);
  drawDataPoints(ctx);
}

// 交互层：每帧重绘
function renderInteraction() {
  const ctx = layers.interaction.ctx;
  ctx.clearRect(0, 0, width, height);
  drawCursor(ctx);
  drawSelectionBox(ctx);
}
```

| 层 | 更新频率 | 重绘策略 | 性能影响 |
|------|---------|---------|---------|
| 背景层 | 几乎不变 | 初始化绘制一次 | 无 |
| 内容层 | 数据变化时 | 按需重绘 | 低 |
| 交互层 | 每帧 | 全量重绘 | 中（画布小） |

### 15.2.3 批量绘制减少状态切换

每次切换 fillStyle、strokeStyle、font 等状态都有开销。按状态分组绘制可以显著提升性能：

```javascript
// 差的做法：每个对象独立设置状态
objects.forEach(obj => {
  ctx.fillStyle = obj.color;
  ctx.fillRect(obj.x, obj.y, obj.w, obj.h);
});
// 1000 个对象 = 1000 次 fillStyle 切换

// 好的做法：按颜色分组
const groups = {};
objects.forEach(obj => {
  if (!groups[obj.color]) groups[obj.color] = [];
  groups[obj.color].push(obj);
});

for (const color in groups) {
  ctx.fillStyle = color;  // 每个颜色只设置一次
  groups[color].forEach(obj => {
    ctx.fillRect(obj.x, obj.y, obj.w, obj.h);
  });
}
// 10 种颜色 = 10 次 fillStyle 切换
```

> 金句：Canvas 状态切换是隐形成本——你看不到 API 调用，但每一帧都在付出代价。

### 15.2.4 离屏画布预渲染

对于重复绘制的复杂图形，先在离屏画布上画好，再用 drawImage 复制：

```javascript
// 预渲染复杂图形
const offscreen = document.createElement('canvas');
offscreen.width = 100;
offscreen.height = 100;
const offCtx = offscreen.getContext('2d');

// 只画一次
drawComplexShape(offCtx);

// 每帧只需 drawImage（极快）
function render() {
  for (let i = 0; i < 1000; i++) {
    ctx.drawImage(offscreen, positions[i].x, positions[i].y);
  }
}
```

**适用场景**：大量重复的复杂图元（图标、精灵、粒子纹理）。

### 15.2.5 避免频繁的 getImageData/putImageData

```javascript
// 差的做法：每帧读取像素
function badApproach() {
  for (let i = 0; i < pixels.length; i += 4) {
    const imageData = ctx.getImageData(0, 0, width, height);  // 极慢
    // 处理像素
  }
}

// 好的做法：一次读取，批量处理
function goodApproach() {
  const imageData = ctx.getImageData(0, 0, width, height);  // 只读一次
  const data = imageData.data;
  
  for (let i = 0; i < data.length; i += 4) {
    // 批量处理像素
    data[i] = 255 - data[i];       // R
    data[i + 1] = 255 - data[i + 1]; // G
    data[i + 2] = 255 - data[i + 2]; // B
  }
  
  ctx.putImageData(imageData, 0, 0);  // 一次写回
}
```

getImageData 的性能开销来自 GPU→CPU 的数据回读。频繁回读会破坏 GPU 渲染管线的并行性。

## 15.3 内存优化

### 15.3.1 对象池模式

频繁创建和销毁对象会触发 GC（Garbage Collection，垃圾回收），导致帧卡顿。对象池预分配对象，重复使用：

```javascript
class ObjectPool {
  constructor(factory, initialSize = 100) {
    this.factory = factory;
    this.pool = [];
    this.active = [];
    
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }
  
  acquire() {
    let obj;
    if (this.pool.length > 0) {
      obj = this.pool.pop();
    } else {
      obj = this.factory();
    }
    this.active.push(obj);
    return obj;
  }
  
  release(obj) {
    const idx = this.active.indexOf(obj);
    if (idx >= 0) {
      this.active.splice(idx, 1);
      this.pool.push(obj);
    }
  }
  
  releaseAll() {
    while (this.active.length > 0) {
      this.pool.push(this.active.pop());
    }
  }
}

// 粒子系统使用对象池
const particlePool = new ObjectPool(() => ({
  x: 0, y: 0, vx: 0, vy: 0, life: 0, maxLife: 1,
}), 500);

function emitParticle(x, y) {
  const p = particlePool.acquire();
  p.x = x;
  p.y = y;
  p.vx = (Math.random() - 0.5) * 10;
  p.vy = (Math.random() - 0.5) * 10;
  p.life = p.maxLife = 1.0;
}

function updateParticles(dt) {
  for (let i = particlePool.active.length - 1; i >= 0; i--) {
    const p = particlePool.active[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.life -= dt;
    if (p.life <= 0) {
      particlePool.release(p);
    }
  }
}
```

### 15.3.2 纹理图集

纹理图集（Texture Atlas / Sprite Sheet）将多个小图合并为一张大图，减少 GPU 纹理切换：

```
单独纹理：                    纹理图集：
┌────┐ ┌────┐ ┌────┐        ┌──────────────┐
│ A  │ │ B  │ │ C  │        │ A  │ B  │ C  │
└────┘ └────┘ └────┘        │────┼────┼────│
3 次纹理绑定                  │ D  │ E  │ F  │
                             └──────────────┘
                             1 次纹理绑定
```

```javascript
// 使用纹理图集
const atlas = new Image();
atlas.src = 'atlas.png';
atlas.onload = () => {
  // drawImage 的 9 参数版本：从图集中截取区域绘制
  // drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
  
  // 画精灵 A（在图集中的位置：0,0,32,32）
  ctx.drawImage(atlas, 0, 0, 32, 32, x, y, 32, 32);
  
  // 画精灵 B（在图集中的位置：32,0,32,32）
  ctx.drawImage(atlas, 32, 0, 32, 32, x2, y2, 32, 32);
};
```

### 15.3.3 内存泄漏检测

Canvas 应用常见的内存泄漏：

| 泄漏源 | 症状 | 检测方法 |
|--------|------|---------|
| 未移除的事件监听器 | 内存持续增长 | Chrome Memory 面板 |
| 闭包引用 | GC 无法回收 | Heap Snapshot 对比 |
| Image 对象未释放 | 图片内存不释放 | Performance Monitor |
| OffscreenCanvas 未销毁 | GPU 内存泄漏 | WebGL Inspector |
| requestAnimationFrame 未取消 | 动画继续运行 | DevTools Console |

```javascript
// 正确的清理流程
function destroyScene(scene) {
  // 1. 取消动画
  cancelAnimationFrame(scene.rafId);
  
  // 2. 移除事件监听器
  scene.canvas.removeEventListener('click', scene.onClick);
  scene.canvas.removeEventListener('mousemove', scene.onMove);
  
  // 3. 释放 Image 对象
  scene.images.forEach(img => {
    img.src = '';  // 释放图片数据
  });
  scene.images = null;
  
  // 4. 释放离屏画布
  scene.layers.forEach(layer => {
    layer.canvas.width = 0;  // 释放像素缓冲区
    layer.canvas.height = 0;
  });
  
  // 5. 清除引用
  scene.canvas = null;
  scene.ctx = null;
  scene.objects = null;
}
```

> 金句：内存泄漏不是"忘记 delete"——在 JavaScript 中是"忘记断开引用链"。

## 15.4 优化策略清单

### 15.4.1 按瓶颈类型选择优化策略

| 瓶颈类型 | 症状 | 优化策略 |
|---------|------|---------|
| JS 执行慢 | 逻辑计算耗时长 | 算法优化/空间索引/Worker |
| 绘制慢 | ctx 命令执行耗时长 | 批量绘制/分层/离屏预渲染 |
| GPU 慢 | 像素填充率高 | 降低分辨率/减少透明度 |
| 内存抖动 | 频繁 GC 卡顿 | 对象池/减少分配 |
| 纹理切换多 | WebGL Draw Call 少但慢 | 纹理图集 |
| Draw Call 多 | 大量小对象 | 实例化渲染/合并 VBO |

### 15.4.2 优化优先级

```
优化收益排行（从高到低）：
1. 减少绘制对象数量（空间索引/视锥剔除/LOD）
2. 批量绘制减少状态切换
3. 分层渲染避免不必要的重绘
4. 离屏预渲染复用复杂图形
5. 对象池减少 GC
6. 纹理图集减少 GPU 状态切换
7. 脏矩形减少重绘区域
8. Worker 线程分担计算
```

## 15.5 本章总结

| 优化方向 | 具体手段 | 收益 |
|---------|---------|------|
| FPS 监控 | performance.now + 帧时间统计 | 发现瓶颈 |
| 帧预算分析 | 分段计时定位热点 | 精准优化 |
| 脏矩形 | 只重绘变化区域 | 减少绘制量 |
| 分层渲染 | 静态/动态分离 | 减少重绘范围 |
| 批量绘制 | 按状态分组 | 减少状态切换 |
| 离屏预渲染 | 复杂图形缓存 | drawImage 替代重绘 |
| 对象池 | 避免频繁 GC | 减少卡顿 |
| 纹理图集 | 合并小图 | 减少 GPU 切换 |
| 内存清理 | 销毁+断引用 | 防泄漏 |

觉得有用？收藏起来，下次遇到性能问题按清单排查。

你的 Canvas 应用卡在哪里？评论区说说症状，怕浪猫帮你诊断。

关注怕浪猫，下期我们讲 **Canvas 与 CSS/SVG/Video/Audio/Worker/AI 的协作**——跨技术整合的完整方案。

系列进度 15/17

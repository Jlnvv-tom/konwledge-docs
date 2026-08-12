---
sidebar_position: 8
---

# 第8章 Canvas 动画系统

> 你以为动画就是 setInterval？requestAnimationFrame 的 3 个秘密你未必知道。

还在用 setInterval 驱动 Canvas 动画？Canvas 动画核心不是画图，而是"时间的操控"。

我是怕浪猫，一只在代码堆里打盹的猫。聊起动画引擎底层，能唠到凌晨三点。这章是全书最硬核的章节之一，建议泡杯茶慢慢看。

## 8.1 动画基础

动画本质是"在连续时间点绘制不同画面"。渲染管线、刷新率、事件循环，每个环节都影响流畅度。

### 8.1.1 requestAnimationFrame 与浏览器刷新率

`requestAnimationFrame`（简称 rAF）是浏览器为动画设计的 API。与 setInterval 区别：rAF 由浏览器调度，在每次重绘前调用回调。

显示器 60Hz 时 rAF 自动匹配，约 16.67ms 间隔。三个秘密：

**一：rAF 不保证 60fps。** 后台标签时浏览器自动降频甚至暂停，节省电量。

**二：回调的时间戳参数。** 回调接收 `DOMHighResTimeStamp`，从页面加载起的毫秒数。计算 Delta Time 的关键，不该用 `Date.now()` 替代。

**三：回调在渲染前执行。** 绘制操作在当次渲染呈现。setInterval 可能跨多个渲染帧导致丢帧。

```javascript
// rAF 动画循环
// MDN: https://developer.mozilla.org/zh-CN/docs/Web/API/Window/requestAnimationFrame
let lastTime = 0;
function animate(currentTime) {
  const dt = currentTime - lastTime;
  lastTime = currentTime;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  update(dt); render(ctx);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
```

`update` 和 `render` 分离是动画引擎基本原则——逻辑与渲染解耦。

```
浏览器一帧生命周期
┌─────────────────────────────────┐
│ 1. Input Events                 │
│ 2. rAF Callbacks (动画代码)     │
│ 3. Style→Layout→Paint→Composite │
│ ──── 屏幕刷新 (60Hz≈16.67ms) ── │
│ 超时则丢帧                      │
└─────────────────────────────────┘
```

> 金句：rAF 不是"定时器"，是"渲染同步器"。它让你的函数赶上每班渲染列车。

高刷新率屏幕（120Hz）上 rAF 会提高频率。按"每帧固定像素"写的动画会翻倍加速。解法：始终用 Delta Time 算位移。

### 8.1.2 帧率监控与 Delta Time 计算

FPS（Frames Per Second，每秒帧数）是流畅度核心指标。Delta Time 是当前帧与上帧的时间差。

```javascript
// FPS 监控 + Delta Time
// 参考: https://developer.mozilla.org/zh-CN/docs/Web/API/Performance/now
class FrameMonitor {
  constructor() {
    this.last = performance.now();
    this.frames = 0; this.fps = 0; this.acc = 0; this.dt = 0;
  }
  tick() {
    const now = performance.now();
    this.dt = Math.min((now - this.last) / 1000, 0.1);
    this.last = now;
    this.frames++; this.acc += this.dt;
    if (this.acc >= 1) {
      this.fps = Math.round(this.frames / this.acc);
      this.frames = 0; this.acc = 0;
    }
    return this.dt;
  }
}
```

`Math.min(this.dt, 0.1)` 很关键。切标签页回来时时间差可能数秒，不限制则物体"瞬移"。

```
FPS 等级对照
┌────────┬────────┬──────────────────┐
│  FPS   │  等级  │  体验             │
├────────┼────────┼──────────────────┤
│  60    │  完美  │  丝滑无卡顿       │
│  30-50 │  可接受│  快速运动有拖影   │
│  15-30 │  卡顿  │  影响交互         │
│  < 15  │  幻灯片│  用户离开         │
└────────┴────────┴──────────────────┘
```

> 金句：Delta Time 是动画世界的"相对论"。没有它的动画，像没有时区的时钟。

### 8.1.3 固定时间步长 vs 可变时间步长

**可变步长（Variable Timestep）** 直接用 Delta Time 驱动。简单但物理模拟可能不稳定。

**固定步长（Fixed Timestep）** 逻辑更新始终以固定间隔运行。渲染 30fps 时每次执行两次逻辑更新。

```
┌──────────┬────────┬────────┐
│  特性    │  固定  │  可变  │
├──────────┼────────┼────────┤
│  物理稳定│  高    │  低    │
│  实现复杂│  中    │  低    │
│  确定性  │  支持  │  不支持│
│  场景    │  物理  │  UI    │
└──────────┴────────┴────────┘
```

```javascript
// 固定步长 + 累加器
// 参考: https://gafferongames.com/post/fix_your_timestep/
const FIXED_DT = 1/60;
let acc = 0, last = performance.now();
function animate(now) {
  const ft = Math.min((now-last)/1000, 0.25);
  last = now; acc += ft;
  while (acc >= FIXED_DT) { update(FIXED_DT); acc -= FIXED_DT; }
  render(ctx, acc / FIXED_DT); // alpha 插值
  requestAnimationFrame(animate);
}
```

`alpha` 用于渲染时做线性插值消除抖动。纯视觉特效用可变步长，物理碰撞用固定步长。

## 8.2 动画编排

多个动画需协同、排队、嵌套时，需要编排系统。

### 8.2.1 补间动画与缓动函数

补间动画（Tween Animation）在起始值和结束值间按数学函数插值。缓动函数（Easing Function）决定值如何随时间变化。

```
当前值 = 起始值 + (目标值 - 起始值) * easing(t)
t = 已过时间 / 总时长, [0, 1]
```

30 种常用缓动函数：

```javascript
// 缓动函数库 - 30 种
// 参考: https://easings.net/
const Easing = {
  linear: t => t,
  easeInQuad: t => t*t, easeOutQuad: t => t*(2-t),
  easeInOutQuad: t => t<.5?2*t*t:-1+(4-2*t)*t,
  easeInCubic: t => t**3, easeOutCubic: t => (--t)*t*t+1,
  easeInOutCubic: t => t<.5?4*t**3:(t-1)*(2*t-2)**2+1,
  easeInQuart: t => t**4, easeOutQuart: t => 1-(--t)*t**3,
  easeInOutQuart: t => t<.5?8*t**4:1-8*(--t)*t**3,
  easeInQuint: t => t**5, easeOutQuint: t => 1+(--t)*t**4,
  easeInOutQuint: t => t<.5?16*t**5:1+16*(--t)*t**4,
  easeInSine: t => 1-Math.cos(t*Math.PI/2),
  easeOutSine: t => Math.sin(t*Math.PI/2),
  easeInOutSine: t => -(Math.cos(Math.PI*t)-1)/2,
  easeInExpo: t => t===0?0:2**(10*t-10),
  easeOutExpo: t => t===1?1:1-2**(-10*t),
  easeInOutExpo: t => t===0?0:t===1?1:t<.5?2**(20*t-10)/2:(2-2**(-20*t+10))/2,
  easeInCirc: t => 1-Math.sqrt(1-t*t),
  easeOutCirc: t => Math.sqrt(1-(--t)*t),
  easeInOutCirc: t => t<.5?(1-Math.sqrt(1-4*t*t))/2:(Math.sqrt(1-(-2*t+2)**2)+1)/2,
  easeInBack: t => 2.70158*t**3-1.70158*t*t,
  easeOutBack: t => 1+2.70158*(--t)*t*t,
  easeInOutBack: t => {const c=2.5949095;return t<.5?(4*t*t*((c+1)*2*t-c))/2:(4*(--t)*t*((c+1)*t+c)+2)/2;},
  easeOutBounce: t => {const n=7.5625,d=2.75;
    if(t<1/d)return n*t*t; if(t<2/d)return n*(t-=1.5/d)*t+.75;
    if(t<2.5/d)return n*(t-=2.25/d)*t+.9375; return n*(t-=2.625/d)*t+.984375;},
  easeInBounce: t => 1-Easing.easeOutBounce(1-t),
  easeInOutBounce: t => t<.5?(1-Easing.easeOutBounce(1-2*t))/2:(1+Easing.easeOutBounce(2*t-1))/2,
  easeOutElastic: t => t===0?0:t===1?1:2**(-10*t)*Math.sin((t*10-.75)*(2*Math.PI)/3)+1,
  easeInElastic: t => t===0?0:t===1?1:-2**(10*t-10)*Math.sin((t*10-10.75)*(2*Math.PI)/3),
};
```

关键曲线形状：

```
linear            easeOutBounce
y ───────── /1    y ───────── ─1
y         /       y         ╱╲
y        /        y       ╱  ╲╱╲
y ───── 0         y ───── 0
 0 ── 1 t           0 ── 1 t

easeInOutCubic    easeOutElastic
y ───────── ─1    y ───────── ─1
y          ╱      y     ╱╲╱╲╱╲
y        ╱        y   ╱
y ───── 0         y ─ 0
 0 ── 1 t           0 ── 1 t
```

> 金句：easeInOutQuad 是万金油，easeOutBack 是惊喜感，easeOutBounce 是趣味性。没有最好的缓动，只有最合适的缓动。

补间核心实现：

```javascript
class Tween {
  constructor(target, props, duration, easing = Easing.easeInOutQuad) {
    this.target = target; this.duration = duration;
    this.easing = easing; this.elapsed = 0;
    this.start = {}; this.end = props; this.isPlaying = false;
    for (const k in props) this.start[k] = target[k];
  }
  update(dt) {
    if (!this.isPlaying) return false;
    this.elapsed += dt;
    const t = Math.min(this.elapsed/this.duration, 1);
    const e = this.easing(t);
    for (const k in this.end)
      this.target[k] = this.start[k] + (this.end[k]-this.start[k]) * e;
    if (t >= 1) { this.isPlaying = false; return true; }
    return false;
  }
  begin() { this.isPlaying = true; this.elapsed = 0; return this; }
}
```

### 8.2.2 关键帧动画

关键帧动画（Keyframe Animation）允许在时间线上设多个关键点，每点定义属性值，中间过渡由插值完成。

```
关键帧时间线
t=0    t=0.3    t=0.6    t=1.0
┌──────┬────────┬────────┐
│ KF1  │ KF2    │ KF3    │ KF4
│ x:0  │ x:100  │ x:200  │ x:150
│ y:0  │ y:50   │ y:80   │ y:100
└──────┴────────┴────────┘
   ↕插值  ↕插值   ↕插值
```

```javascript
class KeyframeAnimation {
  constructor(target, duration) {
    this.target = target; this.duration = duration;
    this.frames = []; this.elapsed = 0; this.isPlaying = false;
  }
  kf(time, values, easing = Easing.linear) {
    this.frames.push({time, values, easing});
    this.frames.sort((a,b) => a.time-b.time);
    return this;
  }
  update(dt) {
    if (!this.isPlaying) return false;
    this.elapsed += dt;
    const t = Math.min(this.elapsed/this.duration, 1);
    if (t >= 1) {
      Object.assign(this.target, this.frames.at(-1).values);
      this.isPlaying = false; return true;
    }
    let p = this.frames[0], n = this.frames.at(-1);
    for (let i = 0; i < this.frames.length-1; i++)
      if (t >= this.frames[i].time && t <= this.frames[i+1].time) {
        p = this.frames[i]; n = this.frames[i+1]; break;
      }
    const seg = n.time-p.time;
    const lt = seg === 0 ? 1 : (t-p.time)/seg;
    const et = p.easing(lt);
    for (const k in n.values) {
      const s = p.values[k] ?? this.target[k];
      this.target[k] = s + (n.values[k]-s) * et;
    }
    return false;
  }
  begin() { this.isPlaying = true; this.elapsed = 0; return this; }
}
```

每段区间可指定不同缓动函数，实现复杂运动节奏。

### 8.2.3 动画时间线管理

```
Timeline 调度
──────────────────────────────→
0s  1s  2s  3s  4s  5s
A:[════════] 移动(0-2s)
B:   [════════] 淡入(1-3s)
C:        [════════] 旋转(2-4s)
```

```javascript
class Timeline {
  constructor() { this.tracks = []; this.elapsed = 0; this.isPlaying = false; }
  add(anim, start) {
    this.tracks.push({anim, start, started: false, done: false});
    return this;
  }
  update(dt) {
    if (!this.isPlaying) return;
    this.elapsed += dt;
    let all = true;
    for (const tr of this.tracks) {
      if (this.elapsed < tr.start) { all = false; continue; }
      if (!tr.started) { tr.anim.begin(); tr.started = true; }
      if (!tr.done) { tr.anim.update(dt) ? (tr.done = true) : (all = false); }
    }
    if (all) this.isPlaying = false;
  }
  begin() {
    this.isPlaying = true; this.elapsed = 0;
    this.tracks.forEach(t => { t.started = false; t.done = false; });
    return this;
  }
}
```

### 8.2.4 动画分组与并行/串行控制

```javascript
// 并行：同时启动
class Parallel {
  constructor(anims) { this.anims = anims; this.isPlaying = false; }
  update(dt) {
    if (!this.isPlaying) return false;
    const d = this.anims.every(a => a.update(dt));
    if (d) this.isPlaying = false;
    return d;
  }
  begin() { this.isPlaying = true; this.anims.forEach(a => a.begin()); return this; }
}
// 串行：依次执行
class Sequence {
  constructor(anims) { this.anims = anims; this.idx = 0; this.isPlaying = false; }
  update(dt) {
    if (!this.isPlaying) return false;
    if (this.idx >= this.anims.length) { this.isPlaying = false; return true; }
    if (this.anims[this.idx].update(dt)) this.idx++;
    return this.idx >= this.anims.length;
  }
  begin() { this.isPlaying = true; this.idx = 0; return this; }
}
```

```
并行              串行
┌──────────────┐ ┌──────────────┐
│A:[══════════]│ │A:[══════]    │
│B:[══════════]│ │B:    [══════]│
│C:[══════════]│ │C:        [══]│
│同时开始       │ │依次开始       │
└──────────────┘ └──────────────┘
```

> 金句：动画编排的本质是"时间的数据结构"。Parallel 是时间的并集，Sequence 是时间的链表，Timeline 是时间的时间轴。

## 8.3 物理动画

缓动函数是"预定义曲线"。动画需响应交互、受物理约束时，需要物理动画。

### 8.3.1 基础运动学：速度、加速度、阻尼

```
运动学公式
  position += velocity * dt
  velocity += acceleration * dt
  velocity *= (1 - damping * dt)
  F = ma → a = F/m
```

```javascript
class PhysicsParticle {
  constructor(x, y) {
    this.x = x; this.y = y; this.vx = 0; this.vy = 0;
    this.ax = 0; this.ay = 0; this.damping = .98; this.mass = 1;
  }
  applyForce(fx, fy) { this.ax += fx/this.mass; this.ay += fy/this.mass; }
  update(dt) {
    this.vx += this.ax*dt; this.vy += this.ay*dt;
    this.vx *= this.damping; this.vy *= this.damping;
    this.x += this.vx*dt; this.y += this.vy*dt;
    this.ax = 0; this.ay = 0;
  }
}
```

阻尼 1.0 无阻尼，0.0 瞬停，0.98 是常用"自然衰减"值。

### 8.3.2 弹簧物理模型

弹簧动画是 iOS UIKit 动画核心，也是 Material Design 基础。核心是胡克定律（Hooke's Law）和阻尼振荡。

```
弹簧模型
固定点 ●───╱╲╱╲─── ● 物体(m,x)
        弹簧(k)

F = -k*(x-x0)    胡克定律
Fd = -c*v        阻尼力
ma = -k(x-x0)-cv 运动方程
```

```javascript
// 弹簧动画
// 参考: https://developer.mozilla.org/zh-CN/docs/Web/API/Web_Animations_API
class Spring {
  constructor(target, prop, end, config = {}) {
    this.target = target; this.prop = prop; this.end = end;
    this.k = config.stiffness ?? 100; // 刚度
    this.c = config.damping ?? 10;    // 阻尼
    this.m = config.mass ?? 1;        // 质量
    this.pos = target[prop]; this.vel = 0;
    this.isPlaying = false;
  }
  update(dt) {
    if (!this.isPlaying) return false;
    const d = this.pos - this.end;
    const a = (-this.k*d - this.c*this.vel) / this.m;
    this.vel += a*dt; this.pos += this.vel*dt;
    this.target[this.prop] = this.pos;
    if (Math.abs(d)<.01 && Math.abs(this.vel)<.01) {
      this.target[this.prop] = this.end;
      this.isPlaying = false; return true;
    }
    return false;
  }
  begin() { this.isPlaying = true; this.pos = this.target[this.prop]; this.vel = 0; return this; }
}
// 阻尼比 = c / (2*sqrt(m*k))
// <1: 欠阻尼(震荡) =1: 临界(最优) >1: 过阻尼(缓慢)
```

```
弹簧曲线
欠阻尼(震荡)       临界阻尼(最优)
y ─ ─ ─ 目标       y ─ ─ ─ 目标
│  ╱╲              │ ╲
│ /  ╲╱╲___        │  ╲___
│/                 │     ────
└──────→ t         └──────→ t
```

> 金句：缓动函数是"编排好的舞蹈"，弹簧物理是"即兴的自由泳"。好的交互动画，是两者结合。

### 8.3.3 粒子系统基础

粒子系统（Particle System）通过大量简单个体的组合行为产生复杂视觉效果——火焰、烟雾、爆炸、雪花。核心思想是"涌现"（Emergence）：每个粒子遵循简单规则，大量粒子呈现复杂整体行为。

```
粒子系统架构
┌────────────────────────────┐
│    ParticleSystem          │
│ Emitter → Particle × N     │
│ 生成→更新→渲染→衰减→回收   │
└────────────────────────────┘
```

完整粒子系统模板：

```javascript
// 粒子系统完整模板
// 参考: https://developer.mozilla.org/zh-CN/docs/Web/API/Canvas_API/Tutorial/Advanced_animations
class Particle {
  constructor(x, y) {
    this.x = x; this.y = y;
    this.vx = (Math.random()-.5)*200;
    this.vy = (Math.random()-.5)*200-100;
    this.ay = 300; this.life = 1;
    this.span = 1.5+Math.random();
    this.size = 2+Math.random()*4; this.damp = .99;
  }
  update(dt) {
    this.vy += this.ay*dt;
    this.vx *= this.damp; this.vy *= this.damp;
    this.x += this.vx*dt; this.y += this.vy*dt;
    this.life -= dt/this.span;
  }
  dead() { return this.life <= 0; }
  draw(ctx) {
    const a = Math.max(0, this.life);
    const s = Math.max(.1, this.size*this.life);
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = `rgb(255,${150+105*(1-this.life)|0},50)`;
    ctx.beginPath();
    ctx.arc(this.x, this.y, s, 0, Math.PI*2);
    ctx.fill();
    ctx.restore();
  }
}

class ParticleSystem {
  constructor(x, y) {
    this.x = x; this.y = y; this.particles = [];
    this.rate = 60; this.acc = 0; this.max = 500;
  }
  update(dt) {
    this.acc += dt*this.rate;
    const n = Math.floor(this.acc); this.acc -= n;
    for (let i = 0; i < n && this.particles.length < this.max; i++)
      this.particles.push(new Particle(this.x, this.y));
    for (let i = this.particles.length-1; i >= 0; i--) {
      this.particles[i].update(dt);
      if (this.particles[i].dead()) this.particles.splice(i, 1);
    }
  }
  draw(ctx) {
    ctx.globalCompositeOperation = 'lighter'; // 发光叠加
    this.particles.forEach(p => p.draw(ctx));
    ctx.globalCompositeOperation = 'source-over';
  }
}
```

性能优化三要点：控制最大粒子数防内存爆炸；用对象池复用粒子减少 GC（Garbage Collection，垃圾回收）压力；粒子绘制用简单图形，避免每帧创建渐变或图片。

> 金句：粒子系统的美不在于单个粒子，而在于群体的涌现。一千个随机运动的点，能模拟一场烟花。

## 本章总结

三个层面拆解了 Canvas 动画系统。基础层讲清 rAF 原理、FPS 监控和固定/可变步长。编排层覆盖补间、关键帧、时间线和分组控制。物理层从运动学到弹簧模型到粒子系统。

三条结论。第一，始终用 Delta Time 驱动动画，不假设帧率固定。第二，30 种缓动函数覆盖绝大多数场景，选对缓动比写复杂逻辑更重要。第三，粒子系统的核心不是绘制，而是生命周期管理——生成、更新、回收。

下一章进入 Canvas 交互系统，讲事件命中检测、坐标变换、拖拽缩放、手势识别。动画让画面"活起来"，交互让画面"动起来"。

> Canvas 工程全书 | 进度: [████████░░░░░░░░░] 8/17
>
> 下章：第9章 Canvas 交互系统——事件、命中检测、坐标变换、手势识别
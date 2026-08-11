# 第9章 Canvas 交互系统

> Canvas 画了 1000 个对象，点击哪个都选不中？你缺的是一套命中检测系统。

我是怕浪猫，在 Canvas 波浪里挣扎多年的技术猫。踩过的交互坑够填满一整个四叉树。这一章，我把交互系统的底层骨架从头拆给你看。

## 9.1 命中检测（Hit Testing）

命中检测是所有交互的起点。用户点了一下，你得判断这个点落在哪个对象上。对象从 10 个涨到 10000 个，问题就开始指数级膨胀。

### 9.1.1 几何命中检测：点-矩形、点-圆形、点-多边形

**点-矩形检测**

轴对齐矩形（AABB，Axis-Aligned Bounding Box）只需四次比较：

```javascript
// 参考: https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection
function pointInRect(px, py, r) {
  return px >= r.x && px <= r.x + r.width &&
         py >= r.y && py <= r.y + r.height;
}
```

旋转矩形则把点反向旋转回本地坐标系再做检测：

```javascript
function pointInRotatedRect(px, py, r) {
  const cos = Math.cos(-r.rotation), sin = Math.sin(-r.rotation);
  const dx = px-r.cx, dy = py-r.cy;
  const lx = dx*cos-dy*sin, ly = dx*sin+dy*cos;
  return Math.abs(lx) <= r.width/2 && Math.abs(ly) <= r.height/2;
}
```

**点-圆形检测**

用距离平方避免开方，省掉一次 `Math.sqrt` 调用：

```javascript
function pointInCircle(px, py, c) {
  const dx = px - c.cx, dy = py - c.cy;
  return dx * dx + dy * dy <= c.radius * c.radius;
}
```

**点-多边形检测**

经典算法是射线法（Ray Casting Algorithm）：从检测点水平向右发射射线，与多边形边界交点为奇数则在内部。

```
点-多边形命中检测原理图（射线法）

    /-----------------\
   /                   \
--*---------P----------*---------> 射线
 /                     \

交点=2 -> 外部      交点=1 -> 内部
```

```javascript
// 参考: https://en.wikipedia.org/wiki/Point_in_polygon
function pointInPolygon(px, py, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i].x, yi = poly[i].y, xj = poly[j].x, yj = poly[j].y;
    if (((yi > py) !== (yj > py)) &&
        (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) inside = !inside;
  }
  return inside;
}
```

时间复杂度 O(n)。凸多边形可用分离轴定理（SAT，Separating Axis Theorem）提前退出，但射线法对凹多边形同样适用。

金句：命中检测的本质不是"点在不在里面"，而是"在 16 毫秒内判断出点在不在里面"。

### 9.1.2 isPointInPath / isPointInStroke

Canvas 2D API 提供原生命中检测，适合复杂路径：

```javascript
// 参考: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/isPointInPath
const path = new Path2D();
path.moveTo(10, 10); path.lineTo(100, 30); path.lineTo(80, 80);
path.closePath();
const hit = ctx.isPointInPath(path, 50, 50);
// 参考: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/isPointInStroke
const strokeHit = ctx.isPointInStroke(path, 50, 50);
```

注意 `isPointInPath` 依赖当前 context 的变换矩阵（Transformation Matrix）。缩放平移场景下传入坐标需是屏幕坐标，API 会自动反变换。矩形圆形手写最快，复杂路径用 `isPointInPath` 更可靠。

### 9.1.3 空间索引加速：四叉树与网格法

10000 个对象逐个检测是 O(n)，不可接受。空间索引把候选集缩小到很小子集。

**四叉树（Quadtree）** 递归地将空间分成四个象限，直到每区域对象数低于阈值。

```
四叉树结构图

+---------------+---------------+
|     Q0        |      Q1       |
|   +---+---+   |               |
|   |Q00|Q01|   |               |
|   +---+---+   |               |
|   |Q02|Q03|   |               |
|   +---+---+   |               |
+---------------+---------------+
|      Q2       |      Q3       |
+---------------+---------------+
```

```javascript
class Rect {
  constructor(x,y,w,h){this.x=x;this.y=y;this.w=w;this.h=h;}
  contains(p){return p.x>=this.x&&p.x<=this.x+this.w&&p.y>=this.y&&p.y<=this.y+this.h;}
  intersects(r){return !(r.x>this.x+this.w||r.x+r.w<this.x||r.y>this.y+this.h||r.y+r.h<this.y);}
}
class Quadtree {
  constructor(b,cap=4){this.b=b;this.cap=cap;this.pts=[];this.div=false;}
  subdivide(){const{x,y,w,h}=this.b,hw=w/2,hh=h/2;
    this.nw=new Quadtree(new Rect(x,y,hw,hh),this.cap);this.ne=new Quadtree(new Rect(x+hw,y,hw,hh),this.cap);
    this.sw=new Quadtree(new Rect(x,y+hh,hw,hh),this.cap);this.se=new Quadtree(new Rect(x+hw,y+hh,hw,hh),this.cap);
    for(const p of this.pts)this.nw.insert(p)||this.ne.insert(p)||this.sw.insert(p)||this.se.insert(p);
    this.pts=[];this.div=true;}
  insert(p){if(!this.b.contains(p))return false;
    if(this.pts.length<this.cap&&!this.div){this.pts.push(p);return true;}
    if(!this.div)this.subdivide();
    return this.nw.insert(p)||this.ne.insert(p)||this.sw.insert(p)||this.se.insert(p);}
  query(r,f=[]){if(!this.b.intersects(r))return f;
    if(!this.div){for(const p of this.pts)if(r.contains(p))f.push(p);}
    else{this.nw.query(r,f);this.ne.query(r,f);this.sw.query(r,f);this.se.query(r,f);}return f;}
}
```

查询复杂度 O(log n)，但对象移动时需删除再插入，频繁移动场景重建成本高。

**网格法（Uniform Grid）** 把空间均匀分格，每格维护对象列表：

```javascript
class SpatialGrid {
  constructor(cellSize) { this.cs=cellSize; this.grid=new Map(); }
  _key(x,y) { return `${Math.floor(x/this.cs)},${Math.floor(y/this.cs)}`; }
  insert(o) { const k=this._key(o.x,o.y); if(!this.grid.has(k))this.grid.set(k,[]); this.grid.get(k).push(o); }
  queryRange(r) {
    const c0=Math.floor(r.x/this.cs),c1=Math.floor((r.x+r.w)/this.cs);
    const r0=Math.floor(r.y/this.cs),r1=Math.floor((r.y+r.h)/this.cs);
    const res=[];
    for(let c=c0;c<=c1;c++) for(let r=r0;r<=r1;r++){
      const k=`${c},${r}`; if(this.grid.has(k)) res.push(...this.grid.get(k));
    }
    return res;
  }
}
```

| 维度 | 四叉树 | 网格法 |
|------|--------|--------|
| 空间自适应 | 是 | 否 |
| 查询性能 | O(log n) | O(k) |
| 重建成本 | 高 | 低 |
| 适用场景 | 分布不均 | 均匀且频繁移动 |

金句：选数据结构就像选猫粮，没有最好只有最合适。

## 9.2 事件系统设计

### 9.2.1 将 DOM 事件映射到画布坐标

Canvas 是 DOM 元素，浏览器事件携带视口坐标，需转换为画布世界坐标。

```
事件坐标转换链

浏览器事件 (clientX, clientY)
    |  getBoundingClientRect() 减去画布偏移
    v
CSS 像素坐标
    |  乘以 canvas.width / rect.width
    v
画布像素坐标
    |  应用视口逆变换
    v
世界坐标 (worldX, worldY)
```

```javascript
// 参考: https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect
function getCanvasPoint(e, canvas, vp) {
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width / rect.width, sy = canvas.height / rect.height;
  return {
    x: ((e.clientX - rect.left) * sx - vp.x) / vp.scale,
    y: ((e.clientY - rect.top) * sy - vp.y) / vp.scale
  };
}
```

`getBoundingClientRect()` 返回 CSS 像素尺寸，`canvas.width` 是内部分辨率，比值为 CSS 缩放比。若做了 DPR（Device Pixel Ratio）适配，此值即 DPR。

### 9.2.2 事件冒泡与捕获在画布中的模拟

Canvas 没有 DOM 树，但编辑器常需事件传播。我们手动实现捕获-目标-冒泡三阶段。

```
画布事件传播流程图

用户点击 (worldX, worldY)
    |
    v
命中检测 -> 候选列表 [C, B, A]（内到外）
    |
    v
捕获阶段：A -> B -> C（外到内）
    |
    v
目标阶段：C
    |
    v
冒泡阶段：C -> B -> A（内到外）
    |
    v
stopPropagation() 可中断传播
```

```javascript
class CanvasEventSystem {
  constructor() { this.objects=[]; this.listeners=new Map(); }
  on(obj, type, fn) { this.listeners.set(`${obj.id}:${type}`, fn); }
  dispatch(type, point) {
    const hits = this.hitTest(point);
    if (!hits.length) return;
    const e = { type, point, target: hits[0], currentTarget: null,
      propagationStopped: false, stopPropagation() { this.propagationStopped=true; } };
    // 捕获阶段：外到内
    for (let i=hits.length-1; i>=0; i--) {
      if (e.propagationStopped) break;
      e.currentTarget = hits[i];
      this._fire(hits[i], `capture:${type}`, e);
    }
    // 冒泡阶段：内到外
    for (let i=0; i<hits.length; i++) {
      if (e.propagationStopped) break;
      e.currentTarget = hits[i];
      this._fire(hits[i], type, e);
    }
  }
  hitTest(p) {
    const hits = [];
    for (let i=this.objects.length-1; i>=0; i--)
      if (this._test(p, this.objects[i])) hits.push(this.objects[i]);
    return hits;
  }
  _fire(obj, type, e) { const h=this.listeners.get(`${obj.id}:${type}`); if(h) h(e); }
  _test(p, o) {
    switch(o.type) {
      case 'rect': return pointInRect(p.x,p.y,o);
      case 'circle': return pointInCircle(p.x,p.y,o);
      case 'polygon': return pointInPolygon(p.x,p.y,o.points);
    }
  }
}
```

### 9.2.3 拖拽（Drag and Drop）的实现模式

```
拖拽状态机

  IDLE --mousedown命中--> DRAGGING --mouseup--> IDLE
                            |
                         mousemove -> 更新位置 -> 重绘
```

完整拖拽系统代码模板：

```javascript
// 参考: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
class DragManager {
  constructor(canvas, vp) {
    this.canvas=canvas; this.vp=vp; this.dragObj=null; this.offset={x:0,y:0};
    this.onStart=this.onMove=this.onEnd=null;
    canvas.addEventListener('pointerdown', e=>this._down(e));
    canvas.addEventListener('pointermove', e=>this._move(e));
    canvas.addEventListener('pointerup', e=>this._up(e));
    canvas.addEventListener('pointercancel', e=>this._up(e));
  }
  _pt(e) {
    const r=this.canvas.getBoundingClientRect();
    const sx=this.canvas.width/r.width, sy=this.canvas.height/r.height;
    return { x:((e.clientX-r.left)*sx-this.vp.x)/this.vp.scale,
             y:((e.clientY-r.top)*sy-this.vp.y)/this.vp.scale };
  }
  _down(e) {
    const p=this._pt(e), hit=this.hitTest(p);
    if (hit) {
      this.dragObj=hit; this.offset={x:p.x-hit.x, y:p.y-hit.y};
      this.canvas.setPointerCapture(e.pointerId);
      if (this.onStart) this.onStart(hit, p);
    }
  }
  _move(e) {
    if (!this.dragObj) return;
    const p=this._pt(e);
    this.dragObj.x=p.x-this.offset.x; this.dragObj.y=p.y-this.offset.y;
    if (this.onMove) this.onMove(this.dragObj, p);
  }
  _up(e) {
    if (!this.dragObj) return;
    const p=this._pt(e);
    if (this.onEnd) this.onEnd(this.dragObj, p);
    this.dragObj=null; this.canvas.releasePointerCapture(e.pointerId);
  }
}
```

三个关键点。第一，用 PointerEvent（PE，Pointer Event）统一鼠标触摸触控笔。第二，`setPointerCapture` 确保移出画布仍收事件。第三，`offset` 记录点击点与对象原点偏移，否则对象会"跳"到鼠标位置。

### 9.2.4 手势识别：缩放、旋转、平移

```
双指手势状态机

单指按下 --第二指--> 双指活跃
                        |
                +-------+-------+
                |       |       |
            距离变化  角度变化  位置变化
                v       v       v
              缩放     旋转     平移
                +-------+-------+
                        |
                  任一指抬起 -> 单指
```

```javascript
// 参考: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events#multi-touch
class GestureRecognizer {
  constructor(canvas, vp) {
    this.canvas=canvas; this.vp=vp; this.pointers=new Map(); this.state=null;
    canvas.addEventListener('pointerdown',e=>this._down(e));
    canvas.addEventListener('pointermove',e=>this._move(e));
    canvas.addEventListener('pointerup',e=>this._up(e));
  }
  _down(e) {
    this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if (this.pointers.size===2) {
      const p=[...this.pointers.values()];
      this.state={ d0:this._d(p[0],p[1]), a0:this._a(p[0],p[1]),
        s0:this.vp.scale, r0:this.vp.rotation||0,
        c0:this._c(p[0],p[1]), v0:{x:this.vp.x,y:this.vp.y} };
    }
  }
  _move(e) {
    if (!this.pointers.has(e.pointerId)) return;
    this.pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if (this.pointers.size===2 && this.state) {
      const p=[...this.pointers.values()], s=this.state;
      this.vp.scale=s.s0*(this._d(p[0],p[1])/s.d0);
      this.vp.rotation=s.r0+(this._a(p[0],p[1])-s.a0);
      const c=this._c(p[0],p[1]);
      this.vp.x=s.v0.x+(c.x-s.c0.x); this.vp.y=s.v0.y+(c.y-s.c0.y);
    }
  }
  _up(e) { this.pointers.delete(e.pointerId); if(this.pointers.size<2) this.state=null; }
  _d(a,b){const dx=b.x-a.x,dy=b.y-a.y;return Math.sqrt(dx*dx+dy*dy);}
  _a(a,b){return Math.atan2(b.y-a.y,b.x-a.x);}
  _c(a,b){return{x:(a.x+b.x)/2,y:(a.y+b.y)/2};}
}
```

缩放常见 Bug：缩放中心不在双指中点。上面代码把平移和缩放叠加，缩放中心自然跟随双指中点。若视口变换是矩阵乘法，确保组合顺序正确，否则缩放会偏移。

## 9.3 对象选择与高亮

### 9.3.1 选中框（Bounding Box）与控制点

选中对象后需要视觉反馈：绘制包围盒和八个方向的控制点。

```javascript
function drawSelection(ctx, obj, vp) {
  const bb = getBoundingBox(obj);
  ctx.strokeStyle='#4A90D9'; ctx.lineWidth=1/vp.scale;
  ctx.setLineDash([4/vp.scale,4/vp.scale]);
  ctx.strokeRect(bb.x,bb.y,bb.w,bb.h); ctx.setLineDash([]);
  const handles=getHandles(bb), size=6/vp.scale;
  ctx.fillStyle='#FFFFFF'; ctx.strokeStyle='#4A90D9';
  for (const h of handles) {
    ctx.fillRect(h.x-size/2,h.y-size/2,size,size);
    ctx.strokeRect(h.x-size/2,h.y-size/2,size,size);
  }
}
function getHandles(bb) {
  const {x,y,w,h}=bb;
  return [{x,y},{x:x+w/2,y},{x:x+w,y},{x,y:y+h/2},{x:x+w,y:y+h/2},
    {x,y:y+h},{x:x+w/2,y:y+h},{x:x+w,y:y+h}];
}
```

控制点要命中检测，拖拽时根据控制点类型执行不同操作（缩放、旋转）。`lineWidth` 和 `size` 都除以 `vp.scale`，确保在任意缩放级别下视觉大小恒定。

### 9.3.2 多选与框选

框选是拖拽出一个矩形区域，选中区域内所有对象。

```
框选相交判定

  +--------S--------+
  |   +---O---+     |  完全包含 -> 选中
  |   |       |     |
  |   +-------+     |
  +------------------+

  +--------S--------+
  |       +---O---+ |  部分相交 -> 选中（可选）
  |       |       | |
  +-------+-------+-+
```

```javascript
class BoxSelector {
  constructor(es) { this.es=es; this.active=false; this.start=null; this.cur=null; }
  begin(p) {
    if (this.es.hitTest(p).length>0) return;
    this.active=true; this.start=p; this.cur=p;
  }
  update(p) { if(this.active) this.cur=p; }
  finish(sel) {
    if (!this.active) return;
    const b=this._box();
    for (const o of this.es.objects)
      if (this._intersects(b, getBoundingBox(o))) sel.add(o);
    this.active=false;
  }
  _box() { return { x:Math.min(this.start.x,this.cur.x), y:Math.min(this.start.y,this.cur.y),
    w:Math.abs(this.cur.x-this.start.x), h:Math.abs(this.cur.y-this.start.y) }; }
  _intersects(a,b) { return !(a.x>b.x+b.w||a.x+a.w<b.x||a.y>b.y+b.h||a.y+a.h<b.y); }
  draw(ctx,vp) {
    if(!this.active) return; const b=this._box();
    ctx.fillStyle='rgba(74,144,217,0.1)'; ctx.strokeStyle='#4A90D9';
    ctx.lineWidth=1/vp.scale; ctx.fillRect(b.x,b.y,b.w,b.h); ctx.strokeRect(b.x,b.y,b.w,b.h);
  }
}
```

框选时配合空间索引加速。用四叉树 `query` 获取选择框范围内的候选对象，再做精确相交检测。

### 9.3.3 键盘修饰键的处理

修饰键决定选择行为的模式：

```
修饰键行为表

Shift + 点击     添加/移除对象到选择集（toggle）
Ctrl/Cmd + 点击  同 Shift，某些框架语义不同
Shift + 拖拽     等比例缩放 / 角度约束（45度）
Alt + 拖拽       复制对象 / 中心缩放
无修饰键 + 点击  清空选择集，选中当前对象
```

```javascript
function handleSelection(point, event, sel) {
  const hit = hitTest(point);
  if (!hit) { if (!event.shiftKey) sel.clear(); return; }
  if (event.shiftKey) {
    if (sel.has(hit)) sel.delete(hit); else sel.add(hit);
  } else {
    if (!sel.has(hit)) { sel.clear(); sel.add(hit); }
  }
}
```

拖拽缩放时的修饰键处理：

```javascript
function handleResize(handle, event, obj) {
  let nw=obj.width, nh=obj.height;
  if (event.shiftKey) { // 等比例：锁定宽高比
    const ratio=obj.width/obj.height;
    if (nw/nh>ratio) nh=nw/ratio; else nw=nh*ratio;
  }
  if (event.altKey) { // 中心缩放
    obj.x-=(nw-obj.width)/2; obj.y-=(nh-obj.height)/2;
  }
  obj.width=nw; obj.height=nh;
}
```

修饰键逻辑要集中在事件处理入口处，不要散落各分支。否则组合爆炸会让你陷入 if-else 的泥沼。状态机或策略模式是更好的组织方式。

金句：交互系统的复杂度不在单个功能，而在功能组合。好的架构让组合成本趋近于零。

## 本章小结

我们从命中检测出发，走到事件系统、拖拽、手势、选择高亮，搭起了一套 Canvas 交互骨架。回顾关键点：

第一，命中检测要分层：空间索引缩小候选集，几何算法精确判定，`isPointInPath` 兜底复杂路径。

第二，事件系统要分相：捕获-目标-冒泡三阶段，`stopPropagation` 让上层对象拦截事件。

第三，拖拽要抓偏移：`dragOffset` 防跳动，`setPointerCapture` 防丢失。

第四，手势要状态机：双指缩放旋转平移同时发生，需清晰的状态管理。

第五，选择要分模式：修饰键定义选择语义，集中处理胜过散落判断。

## 收藏清单

**几何命中检测算法清单：**
- 点-轴对齐矩形：四次比较，O(1)
- 点-旋转矩形：反向旋转 + AABB，O(1)
- 点-圆：距离平方比较，O(1)
- 点-多边形：射线法，O(n)
- 点-复杂路径：isPointInPath，O(n)

**空间索引选型：**
- < 100 对象：暴力遍历
- 100-5000 且分布均匀：网格法
- > 5000 且分布不均：四叉树
- 频繁移动：网格法
- 框选大量对象：四叉树 query + 精确相交

**拖拽系统要素：**
- PointerEvent 统一输入
- setPointerCapture 防丢失
- dragOffset 防跳动
- 坐标系转换（CSS to Canvas to World）
- 状态机管理 IDLE/DRAGGING

## 系列进度

本文是「Canvas 工程全书」系列第 9 章，全系列共 17 章。

进度：[##########----------] 9/17

下章预告：第10章「3D 渲染管线总论」——当 2D Canvas 的能力不够用时，我们如何跨越到 3D 世界？从顶点变换到光栅化，从深度缓冲到纹理映射，一篇文章打通 2D 到 3D 的认知鸿沟。
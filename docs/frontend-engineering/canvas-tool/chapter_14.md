---
sidebar_position: 14
---

# 第14章 引擎生态：从 2D 框架到 3D 引擎的选型指南

选错引擎，重构半年。

这不是危言耸听。一个数据可视化项目选了 PixiJS 做复杂交互图表，结果事件系统、图层管理全要自建——三个月后推倒重来换 Konva。一个 2D 游戏项目选了 Three.js 做 2.5D 效果，结果相机系统、光照计算全是多余的复杂度——两个月后迁回 Phaser。

我是怕浪猫，这一章帮你梳理 Canvas 生态中的主流框架，从 2D 渲染到 3D 引擎，从图表库到游戏引擎，给你一份靠谱的选型参考。

## 14.1 2D 渲染框架

### 14.1.1 Konva.js：面向交互的图层系统

Konva.js 的核心设计理念是"为交互而生"。它提供了类似 SVG 的对象模型，但底层用 Canvas 渲染——既有 SVG 的交互便利，又有 Canvas 的性能。

**核心架构**：

```
Stage（舞台）
├── Layer（图层）
│   ├── Group（分组）
│   │   ├── Shape（图元）
│   │   └── Shape（图元）
│   └── Shape（图元）
└── Layer（图层）
    └── Shape（图元）
```

每个 Layer 对应一个 Canvas 元素，多个 Layer 叠加成完整画面。Shape 是基本图元（矩形、圆形、路径、文本等），支持事件绑定、变换、拖拽。

**典型代码**：

```javascript
import Konva from 'konva';

// 1. 创建舞台
const stage = new Konva.Stage({
  container: 'container',
  width: 800,
  height: 600,
});

// 2. 创建图层
const layer = new Konva.Layer();
stage.add(layer);

// 3. 创建图元
const rect = new Konva.Rect({
  x: 50,
  y: 50,
  width: 100,
  height: 80,
  fill: '#4CAF50',
  draggable: true,  // 内置拖拽
});

// 4. 绑定事件（类似 DOM 事件）
rect.on('mouseenter', () => {
  rect.fill('#2196F3');
  layer.draw();
});

rect.on('dragmove', (e) => {
  console.log('拖拽中：', e.target.x(), e.target.y());
});

layer.add(rect);
layer.draw();
```

**优势**：
- 内置事件系统（无需自建命中检测）
- 内置拖拽、变换（resize/rotate）控件
- 图层管理（多 Canvas 叠加）
- 滤镜支持
- 状态管理（序列化/反序列化）

**劣势**：
- 图元数量多了之后性能下降（每个 Shape 是 JS 对象）
- 不适合 10000+ 图元的场景
- 动画系统较简单

**适用场景**：图形编辑器、白板工具、交互式图表、流程图工具

### 14.1.2 Fabric.js：面向对象模型的画布

Fabric.js 和 Konva 类似，也是"对象模型 + Canvas 渲染"的方案。但 Fabric 更偏向"画布编辑器"场景。

**核心特点**：

```javascript
import { Canvas, Rect } from 'fabric';

const canvas = new Canvas('canvas', {
  width: 800,
  height: 600,
  backgroundColor: '#fff',
});

const rect = new Rect({
  left: 50,
  top: 50,
  width: 100,
  height: 80,
  fill: '#4CAF50',
});

canvas.add(rect);

// 内置交互：选中、拖拽、缩放、旋转
// 不需要额外代码，用户可以直接用鼠标操作图元
```

**Konva vs Fabric.js 对比**：

| 维度 | Konva | Fabric.js |
|------|-------|-----------|
| 设计理念 | 通用图层系统 | 画布编辑器 |
| 内置交互 | 拖拽（需配置） | 选中/拖拽/缩放/旋转（默认开启） |
| 序列化 | JSON | JSON（更完善） |
| 文本编辑 | 基础 | 强（富文本支持） |
| 滤镜 | 基础 | 丰富（亮度/对比度/饱和度等） |
| 社区活跃度 | 高 | 高 |
| 包体积 | ~150KB | ~300KB |
| 适用场景 | 交互应用 | 图片编辑器/设计工具 |

> 金句：Konva 是"给你画笔"，Fabric 是"给你 Photoshop"——前者更灵活，后者开箱即用。

### 14.1.3 PixiJS：极致性能的渲染引擎

PixiJS 是"纯渲染引擎"，不做交互（需要自己实现），但渲染性能是 2D 框架中最强的。

**核心特点**：
- WebGL 优先，Canvas 2D 回退
- 精灵（Sprite）批量渲染
- 纹理图集支持
- 滤镜系统（基于 GLSL 着色器）
- 不含事件系统、动画系统（需配合其他库）

```javascript
import { Application, Sprite, Graphics } from 'pixi.js';

const app = new Application({
  width: 800,
  height: 600,
  backgroundColor: 0x000000,
});
document.body.appendChild(app.view);

// 创建图元
const graphics = new Graphics();
graphics.beginFill(0x4CAF50);
graphics.drawRect(50, 50, 100, 80);
graphics.endFill();

app.stage.addChild(graphics);

// 创建精灵
const sprite = Sprite.from('texture.png');
sprite.x = 200;
sprite.y = 200;
app.stage.addChild(sprite);

// 动画循环
app.ticker.add((delta) => {
  sprite.rotation += 0.01 * delta;
});
```

**性能优势**：PixiJS 内部使用 WebGL 批量渲染，一次 Draw Call 可以绘制上千个精灵。

| 场景 | Konva | Fabric.js | PixiJS |
|------|-------|-----------|--------|
| 100 个图元 | 60fps | 60fps | 60fps |
| 1000 个图元 | 45fps | 30fps | 60fps |
| 10000 个图元 | 5fps | 3fps | 60fps |
| 交互支持 | 好 | 好 | 需自建 |
| 学习曲线 | 低 | 低 | 中 |

### 14.1.4 ZRender 与 AntV

ZRender 是 AntV 可视化生态的底层渲染引擎，ECharts（一个流行的数据可视化图表库）就基于 ZRender。

```javascript
import ZRender from 'zrender';

const zr = ZRender.init(document.getElementById('main'));
const circle = new ZRender.Circle({
  shape: { cx: 100, cy: 100, r: 50 },
  style: { fill: '#4CAF50' },
});
zr.add(circle);
```

**适用场景**：数据可视化（配合 AntV G2/G6/L7），不适合通用图形应用。

## 14.2 3D 引擎

### 14.2.1 Three.js：Web 3D 的事实标准

Three.js 是 Web 上最流行的 3D 库，封装了 WebGL/WebGPU 的复杂细节，提供面向对象的 3D 场景管理。

**核心架构**：

```
Scene（场景）
├── Mesh（网格对象）
│   ├── Geometry（几何体）
│   └── Material（材质）
├── Light（光源）
│   ├── AmbientLight（环境光）
│   ├── DirectionalLight（平行光）
│   └── PointLight（点光源）
├── Camera（相机）
│   ├── PerspectiveCamera（透视相机）
│   └── OrthographicCamera（正交相机）
└── Renderer（渲染器）
    ├── WebGLRenderer
    └── WebGPURenderer
```

**基本代码**：

```javascript
import * as THREE from 'three';

// 1. 场景、相机、渲染器
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(width, height);
document.body.appendChild(renderer.domElement);

camera.position.z = 5;

// 2. 添加物体
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x4CAF50 });
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);

// 3. 添加光源
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 5, 5);
scene.add(light);

scene.add(new THREE.AmbientLight(0x404040));

// 4. 渲染循环
function animate() {
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
```

> 金句：Three.js 把 100 行 WebGL 代码压缩到 20 行——代价是你需要理解它的场景图、相机和材质系统。

### 14.2.2 Babylon.js：面向应用的完整引擎

Babylon.js 比 Three.js 更"重"——它不仅是渲染引擎，还包含物理、音频、动画、UI、碰撞检测等完整游戏引擎功能。

**Three.js vs Babylon.js**：

| 维度 | Three.js | Babylon.js |
|------|----------|------------|
| 定位 | 3D 渲染库 | 完整 3D 引擎 |
| 包体积 | ~600KB | ~2MB |
| TypeScript | 支持但非原生 | 原生 TypeScript |
| 物理引擎 | 需第三方集成 | 内置（Cannon.js/Ammo.js） |
| UI 系统 | 无 | 内置 GUI |
| 碰撞检测 | 基础 | 完整 |
| 工具链 | 分散 | 统一（Playground/Inspector） |
| 学习曲线 | 中等 | 较高 |
| 适用场景 | 可视化/展示/轻量3D | 游戏/复杂3D应用 |

**Babylon.js 代码示例**：

```javascript
import { Engine, Scene, ArcRotateCamera, HemisphericLight, MeshBuilder } from 'babylonjs';

const canvas = document.querySelector('canvas');
const engine = new Engine(canvas, true);
const scene = new Scene(engine);

const camera = new ArcRotateCamera('camera', Math.PI/2, Math.PI/2, 5, new Vector3(0,0,0), scene);
camera.attachControl(canvas, true);

const light = new HemisphericLight('light', new Vector3(1,1,0), scene);

const sphere = MeshBuilder.CreateSphere('sphere', { diameter: 2 }, scene);

engine.runRenderLoop(() => {
  scene.render();
});
```

### 14.2.3 PlayCanvas：性能优先的轻量引擎

PlayCanvas 是一个轻量级 WebGL 引擎，特点是体积小、启动快，适合对加载速度敏感的场景。

```javascript
// PlayCanvas 使用方式
const app = new pc.Application(canvas, {});
app.start();

const camera = new pc.Entity('camera');
camera.addComponent('camera', { clearColor: new pc.Color(0, 0, 0) });
app.root.addChild(camera);
camera.setPosition(0, 0, 5);

const box = new pc.Entity('box');
box.addComponent('model', { type: 'box' });
app.root.addChild(box);
```

| 对比 | Three.js | Babylon.js | PlayCanvas |
|------|----------|------------|------------|
| 体积 | 600KB | 2MB | 200KB |
| 功能 | 渲染 | 完整引擎 | 渲染+基础功能 |
| 在线编辑器 | 无 | Playground | 有（可视化编辑） |
| 适用 | 通用 | 大型项目 | 快速加载 |

## 14.3 图表可视化库

### 14.3.1 ECharts：功能最全的图表库

ECharts（Enterprise Charts，企业级图表库）是百度开源的数据可视化库，基于 ZRender，支持 2D Canvas / 3D WebGL 渲染。

```javascript
import * as echarts from 'echarts';

const chart = echarts.init(document.getElementById('main'));
chart.setOption({
  xAxis: { type: 'category', data: ['Q1','Q2','Q3','Q4'] },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [100, 80, 120, 90] }],
});
```

**适用场景**：仪表盘、报表、数据分析。非自定义可视化场景的首选。

### 14.3.2 AntV G2/G6/L7

AntV 是蚂蚁集团的可视化生态，分为三个子库：

| 库 | 定位 | 渲染方式 | 适用场景 |
|------|------|---------|---------|
| G2 | 统计图表 | Canvas/SVG | 数据分析图表 |
| G6 | 关系图 | Canvas | 知识图谱/社交网络 |
| L7 | 地理可视化 | WebGL | 地图/空间数据 |

### 14.3.3 D3.js 与 Canvas 的结合

D3.js（Data-Driven Documents，数据驱动文档）本身主要操作 SVG/DOM，但可以和 Canvas 结合处理大数据量：

```javascript
import * as d3 from 'd3';

const canvas = d3.select('#canvas').node();
const ctx = canvas.getContext('2d');

// D3 比例尺
const xScale = d3.scaleLinear().domain([0, 100]).range([0, 800]);
const yScale = d3.scaleLinear().domain([0, 100]).range([600, 0]);

// 用 D3 计算位置，用 Canvas 绘制
data.forEach(d => {
  ctx.beginPath();
  ctx.arc(xScale(d.x), yScale(d.y), 3, 0, Math.PI * 2);
  ctx.fill();
});

// 交互层用 SVG（少量元素）
const svg = d3.select('#overlay');
svg.selectAll('circle')
  .data(selectedPoints)
  .join('circle')
  .attr('cx', d => xScale(d.x))
  .attr('cy', d => yScale(d.y))
  .attr('r', 5);
```

> 金句：D3 算位置，Canvas 画像素，SVG 做交互——三者结合，大数据可视化的问题就解决了。

## 14.4 游戏引擎

### 14.4.1 Phaser：2D 游戏引擎

Phaser 是最流行的 HTML5 2D 游戏引擎，基于 Canvas/WebGL 渲染：

```javascript
const config = {
  type: Phaser.AUTO,  // 自动选择 WebGL 或 Canvas
  width: 800,
  height: 600,
  scene: {
    preload() {
      this.load.image('sky', 'sky.png');
    },
    create() {
      this.add.image(400, 300, 'sky');
      const player = this.physics.add.sprite(100, 450, 'player');
      player.setCollideWorldBounds(true);
    },
    update() {
      // 游戏逻辑
    },
  },
};

const game = new Phaser.Game(config);
```

**特点**：
- 内置物理引擎（Arcade Physics / Matter.js）
- 精灵动画、粒子系统、音频管理
- 场景管理、输入系统
- 大量插件和社区资源

### 14.4.2 Cocos Creator

Cocos Creator 是国产跨平台游戏引擎，支持 Canvas 渲染模式：

| 对比 | Phaser | Cocos Creator |
|------|--------|---------------|
| 定位 | HTML5 游戏引擎 | 跨平台游戏引擎 |
| 编辑器 | 无 | 有（可视化编辑） |
| 渲染 | Canvas/WebGL | Canvas/WebGL/Native |
| 包体积 | ~1MB | ~5MB |
| 适用 | 轻量 HTML5 游戏 | 商业游戏 |

## 14.5 框架选型决策矩阵

### 14.5.1 按项目类型选型

| 项目类型 | 推荐框架 | 备选 | 理由 |
|---------|---------|------|------|
| 交互式图表 | ECharts | AntV G2 | 开箱即用，交互完善 |
| 图形编辑器 | Konva | Fabric.js | 事件系统+图层管理 |
| 图片编辑器 | Fabric.js | Konva | 内置变换控件+滤镜 |
| 大数据可视化 | PixiJS + D3 | ECharts(GL) | 性能+灵活 |
| 2D 游戏 | Phaser | PixiJS | 物理引擎+场景管理 |
| 3D 展示 | Three.js | Babylon.js | 生态最大 |
| 3D 游戏 | Babylon.js | Three.js | 完整引擎功能 |
| 知识图谱 | AntV G6 | D3 + Canvas | 关系图专用 |
| 地理可视化 | AntV L7 | Mapbox GL | 空间数据专用 |
| 白板/绘图 | Konva | 自研 | 拖拽+图层 |
| 轻量 3D | PlayCanvas | Three.js | 体积小 |

### 14.5.2 按性能需求选型

| 图元数量 | 推荐方案 |
|---------|---------|
| < 500 | 任意框架或原生 Canvas |
| 500-5000 | Konva / Fabric.js |
| 5000-50000 | PixiJS / ECharts |
| > 50000 | PixiJS + WebGL 批量渲染 |

### 14.5.3 按团队能力选型

| 团队能力 | 推荐 | 理由 |
|---------|------|------|
| 前端为主，无图形经验 | Konva / ECharts | API 简单，文档好 |
| 有 Canvas 经验 | PixiJS + 自建交互 | 灵活可控 |
| 有 WebGL 经验 | Three.js / 自研 | 深度可控 |
| 有游戏开发经验 | Phaser / Babylon.js | 概念熟悉 |

> 金句：选框架不是选最强的，是选最合适的——团队能用得好的框架才是好框架。

## 14.6 本章总结

| 框架 | 定位 | 核心优势 | 适用场景 |
|------|------|---------|---------|
| Konva | 2D 交互框架 | 事件系统+图层 | 编辑器/白板 |
| Fabric.js | 2D 编辑框架 | 变换控件+滤镜 | 图片编辑器 |
| PixiJS | 2D 渲染引擎 | 极致性能 | 游戏/大数据 |
| Three.js | 3D 渲染库 | 生态最大 | 3D 展示/可视化 |
| Babylon.js | 3D 引擎 | 功能完整 | 3D 游戏 |
| ECharts | 图表库 | 开箱即用 | 仪表盘/报表 |
| AntV | 可视化生态 | 专业领域 | 图谱/地图 |
| Phaser | 2D 游戏引擎 | 物理+场景 | HTML5 游戏 |

觉得有用？收藏起来，下次选型时直接查表。

你在项目中用过哪个框架？有什么心得？评论区分享。

关注怕浪猫，下期我们讲 **性能优化**——FPS 监控、脏矩形、批处理和纹理图集的完整优化体系。

系列进度 14/17

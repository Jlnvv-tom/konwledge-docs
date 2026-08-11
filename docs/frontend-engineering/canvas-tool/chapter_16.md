# 第16章 Canvas 与 CSS/SVG/Video/Audio/Worker/AI 的跨技术协作

Canvas 不是孤岛。

一个视频滤镜应用需要 Canvas + Video + CSS 滤镜协同。一个音乐可视化器需要 Canvas + Audio + Web Audio API 协同。一个 AI 图像标注工具需要 Canvas + Web Worker + TensorFlow.js 协同。现代 Web 应用中，Canvas 总是和其他技术一起出现。

我是怕浪猫，最后一章正篇，我们来看看 Canvas 如何与 Web 平台的其他技术协作。

## 16.1 Canvas 与 CSS

### 16.1.1 CSS 滤镜叠加 Canvas

Canvas 的 `ctx.filter` 属性和 CSS `filter` 属性可以对同一个画布产生不同层级的滤镜效果：

```javascript
// 方式 1：Canvas 内部滤镜（影响绘制内容）
ctx.filter = 'blur(5px) brightness(1.2)';
ctx.drawImage(image, 0, 0);
ctx.filter = 'none';  // 重置

// 方式 2：CSS 滤镜（影响整个 canvas 元素的显示）
canvas.style.filter = 'blur(5px) brightness(1.2)';
```

**两者的区别**：

| 维度 | ctx.filter | CSS filter |
|------|-----------|------------|
| 作用范围 | 只影响后续绘制命令 | 影响整个 canvas 元素 |
| 性能 | CPU 处理 | 可能使用 GPU 合成 |
| 交互影响 | 不影响命中检测 | 不影响命中检测 |
| 叠加 | 可以逐图元不同 | 整体统一 |
| 支持度 | 部分浏览器 | 全部主流浏览器 |

两者可以叠加使用：

```javascript
// Canvas 内部对每个图元应用不同滤镜
ctx.filter = 'blur(2px)';
ctx.drawImage(backgroundImage, 0, 0);
ctx.filter = 'contrast(1.5)';
ctx.drawImage(foregroundImage, 100, 100);
ctx.filter = 'none';

// CSS 对整个 canvas 应用全局滤镜
canvas.style.filter = 'saturate(1.3) hue-rotate(10deg)';
```

### 16.1.2 CSS 动画驱动 Canvas 容器

虽然 Canvas 内部动画需要 rAF 驱动，但 Canvas 容器的变换可以用 CSS 动画：

```css
.canvas-container {
  transition: transform 0.3s ease;
}
.canvas-container.zoomed {
  transform: scale(1.5);
}
.canvas-container.rotated {
  transform: rotate(15deg);
}
```

```javascript
// 用户操作时只需切换 CSS 类
container.classList.add('zoomed');  // CSS 动画自动处理
// Canvas 内部内容不变，只是容器缩放
```

> 金句：Canvas 内部的动画用 rAF，Canvas 外部的动画用 CSS——各管各的，互不干扰。

### 16.1.3 CSS 变量与 Canvas 主题化

通过 CSS 变量（Custom Property）实现 Canvas 的主题切换：

```css
:root {
  --canvas-bg: #1a1a2e;
  --canvas-fg: #e0e0e0;
  --canvas-accent: #0f3460;
}

[data-theme="light"] {
  --canvas-bg: #ffffff;
  --canvas-fg: #333333;
  --canvas-accent: #007bff;
}
```

```javascript
function getThemeColor(varName) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
}

function render() {
  const bgColor = getThemeColor('--canvas-bg');
  const fgColor = getThemeColor('--canvas-fg');
  
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, width, height);
  
  ctx.fillStyle = fgColor;
  ctx.fillText('Hello', 50, 50);
}

// 主题切换时重绘
document.getElementById('themeToggle').addEventListener('click', () => {
  document.documentElement.dataset.theme = 
    document.documentElement.dataset.theme === 'light' ? '' : 'light';
  render();
});
```

### 16.1.4 混合模式（CSS mix-blend-mode 与 Canvas）

```css
/* Canvas 元素与页面背景混合 */
canvas {
  mix-blend-mode: multiply;  /* Canvas 内容与下方 DOM 元素混合 */
}
```

## 16.2 Canvas 与 SVG

### 16.2.1 SVG 转 Canvas 绘制

将 SVG 图形绘制到 Canvas 上：

```javascript
// 方法 1：通过 Image 对象
const img = new Image();
const svgBlob = new Blob([svgString], { type: 'image/svg+xml' });
const url = URL.createObjectURL(svgBlob);

img.onload = () => {
  ctx.drawImage(img, 0, 0);
  URL.revokeObjectURL(url);
};
img.src = url;

// 方法 2：使用 data URL
const svgDataUrl = 'data:image/svg+xml;base64,' + btoa(svgString);
img.src = svgDataUrl;
```

### 16.2.2 Canvas 转 SVG 嵌入

将 Canvas 内容转为 SVG 图片：

```javascript
function canvasToSVG(canvas, width, height) {
  const dataURL = canvas.toDataURL('image/png');
  const svgString = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <image href="${dataURL}" width="${width}" height="${height}" />
    </svg>
  `;
  return svgString;
}
```

### 16.2.3 混合架构实战

```html
<div style="position: relative; width: 800px; height: 600px;">
  <!-- Canvas 底层：渲染 10000 个数据点 -->
  <canvas id="dataLayer" 
          style="position: absolute; top: 0; left: 0; z-index: 1;">
  </canvas>
  
  <!-- SVG 中层：坐标轴和标签（需要文本渲染和交互） -->
  <svg id="axisLayer" 
       style="position: absolute; top: 0; left: 0; z-index: 2; pointer-events: none;">
    <g class="axis-x"><!-- 坐标轴 --></g>
    <g class="axis-y"><!-- 坐标轴 --></g>
  </svg>
  
  <!-- HTML 顶层：tooltip 和控件 -->
  <div id="tooltipLayer"
       style="position: absolute; top: 0; left: 0; z-index: 3; pointer-events: none;">
    <div class="tooltip" style="display: none;"></div>
  </div>
</div>
```

> 金句：Canvas 负责海量数据渲染，SVG 负责精确的矢量元素和文本，HTML 负责交互控件——三层各司其职，这才是工程化的混合方案。

## 16.3 Canvas 与 Video

### 16.3.1 视频帧绘制到 Canvas

```javascript
const video = document.querySelector('video');
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');

// 方式 1：每帧绘制
function drawVideoFrame() {
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  requestAnimationFrame(drawVideoFrame);
}
video.addEventListener('play', drawVideoFrame);

// 方式 2：使用 video.requestVideoFrameCallback（更精确）
function onVideoFrame(now, metadata) {
  ctx.drawImage(video, 0, 0);
  video.requestVideoFrameCallback(onVideoFrame);
}
video.requestVideoFrameCallback(onVideoFrame);
```

`requestVideoFrameCallback`（VideoFrame Callback API）比 rAF 更精确，它回调时机与视频帧解码对齐。

### 16.3.2 实时视频滤镜

```javascript
function applyVideoFilter() {
  // 1. 绘制视频帧
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  // 2. 读取像素数据
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  
  // 3. 应用灰度滤镜
  for (let i = 0; i < data.length; i += 4) {
    const gray = data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114;
    data[i] = data[i+1] = data[i+2] = gray;
  }
  
  // 4. 写回画布
  ctx.putImageData(imageData, 0, 0);
  
  requestAnimationFrame(applyVideoFilter);
}
```

### 16.3.3 Canvas 录制为视频

```javascript
const stream = canvas.captureStream(30);  // 30fps
const recorder = new MediaRecorder(stream, {
  mimeType: 'video/webm;codecs=vp9',
  videoBitsPerSecond: 5000000,  // 5 Mbps
});

const chunks = [];
recorder.ondataavailable = (e) => {
  if (e.data.size > 0) chunks.push(e.data);
};

recorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'video/webm' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'recording.webm';
  a.click();
  URL.revokeObjectURL(url);
};

// 开始录制
recorder.start();

// 录制 10 秒
setTimeout(() => recorder.stop(), 10000);
```

### 16.3.4 视频播放器中的 Canvas 应用

| 应用 | 技术组合 | 说明 |
|------|---------|------|
| 弹幕系统 | Canvas + Video | Canvas 叠加在视频上渲染弹幕 |
| 视频标注 | Canvas + Video | 在视频帧上绘制标注框 |
| 视频滤镜 | Canvas + Video | 实时处理视频帧像素 |
| 视频录制 | Canvas + Video | captureStream 录制动画 |
| 缩略图生成 | Canvas + Video | drawImage 截取视频帧 |

## 16.4 Canvas 与 Audio

### 16.4.1 Web Audio API 分析器驱动 Canvas 可视化

```javascript
const audioContext = new AudioContext();
const analyser = audioContext.createAnalyser();
analyser.fftSize = 256;  // FFT（Fast Fourier Transform，快速傅里叶变换）大小

const audioElement = document.querySelector('audio');
const source = audioContext.createMediaElementSource(audioElement);
source.connect(analyser);
analyser.connect(audioContext.destination);

// 频率数据数组
const bufferLength = analyser.frequencyBinCount;
const dataArray = new Uint8Array(bufferLength);

function drawVisualizer() {
  requestAnimationFrame(drawVisualizer);
  
  // 获取频率数据
  analyser.getByteFrequencyData(dataArray);
  
  ctx.clearRect(0, 0, width, height);
  
  // 绘制频谱柱状图
  const barWidth = width / bufferLength;
  for (let i = 0; i < bufferLength; i++) {
    const barHeight = (dataArray[i] / 255) * height;
    const hue = (i / bufferLength) * 360;
    ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
    ctx.fillRect(i * barWidth, height - barHeight, barWidth - 1, barHeight);
  }
}

audioElement.play();
drawVisualizer();
```

### 16.4.2 波形可视化

```javascript
// 时域波形
analyser.fftSize = 2048;
const timeData = new Uint8Array(analyser.fftSize);

function drawWaveform() {
  requestAnimationFrame(drawWaveform);
  
  analyser.getByteTimeDomainData(timeData);
  
  ctx.clearRect(0, 0, width, height);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#00ff00';
  ctx.beginPath();
  
  const sliceWidth = width / timeData.length;
  let x = 0;
  
  for (let i = 0; i < timeData.length; i++) {
    const v = timeData[i] / 128.0;
    const y = (v * height) / 2;
    
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
    
    x += sliceWidth;
  }
  
  ctx.stroke();
}
```

> 金句：Web Audio 给你数据，Canvas 给你画笔——两者结合，声音就有了形状。

## 16.5 Canvas 与 Web Worker

### 16.5.1 OffscreenCanvas 在 Worker 中渲染

```javascript
// 主线程
const canvas = document.querySelector('canvas');
const offscreen = canvas.transferControlToOffscreen();

const worker = new Worker('renderer.js');
worker.postMessage({ type: 'init', canvas: offscreen }, [offscreen]);

// 主线程发送更新指令
worker.postMessage({ type: 'update', data: newData });
```

```javascript
// renderer.js (Worker 线程)
let ctx, canvas;

self.onmessage = (e) => {
  if (e.data.type === 'init') {
    canvas = e.data.canvas;
    ctx = canvas.getContext('2d');
    canvas.width = 800;
    canvas.height = 600;
    startRendering();
  } else if (e.data.type === 'update') {
    updateData(e.data.data);
  }
};

function startRendering() {
  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // 绘制逻辑...
    requestAnimationFrame(render);
  }
  render();
}
```

### 16.5.2 Worker 中做计算，主线程做渲染

```javascript
// 主线程：负责渲染
const worker = new Worker('physics.js');

worker.onmessage = (e) => {
  const { positions } = e.data;
  // 用收到的位置数据渲染
  ctx.clearRect(0, 0, width, height);
  positions.forEach(p => {
    ctx.fillRect(p.x, p.y, 2, 2);
  });
};

// Worker 线程：负责物理计算
// physics.js
let particles = [];
for (let i = 0; i < 10000; i++) {
  particles.push({
    x: Math.random() * 800,
    y: Math.random() * 600,
    vx: (Math.random() - 0.5) * 2,
    vy: (Math.random() - 0.5) * 2,
  });
}

function update() {
  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > 800) p.vx *= -1;
    if (p.y < 0 || p.y > 600) p.vy *= -1;
  }
  
  postMessage({ positions: particles.map(p => ({ x: p.x, y: p.y })) });
  setTimeout(update, 16);
}
update();
```

**两种 Worker 协作模式对比**：

| 模式 | 计算 | 渲染 | 优势 | 限制 |
|------|------|------|------|------|
| OffscreenCanvas | Worker | Worker | 完全离线渲染 | 需要浏览器支持 |
| Worker 计算 + 主线程渲染 | Worker | 主线程 | 兼容性好 | 数据传输开销 |

## 16.6 Canvas 与 AI

### 16.6.1 Canvas 图像作为 TensorFlow.js 输入

```javascript
import * as tf from '@tensorflow/tfjs';

// 加载模型
const model = await tf.loadGraphModel('model.json');

// 从 Canvas 获取图像张量
function predictFromCanvas(ctx, width, height) {
  // 获取像素数据
  const imageData = ctx.getImageData(0, 0, width, height);
  
  // 转为 TensorFlow 张量
  const tensor = tf.browser.fromPixels(imageData)
    .resizeBilinear([224, 224])  // 调整大小
    .expandDims(0)                // 添加 batch 维度
    .div(255.0)                   // 归一化到 [0,1]
    .toFloat();
  
  // 推理
  const prediction = model.predict(tensor);
  const result = prediction.dataSync();
  
  // 清理张量
  tensor.dispose();
  prediction.dispose();
  
  return result;
}
```

### 16.6.2 在 Canvas 上绘制 AI 检测结果

```javascript
// 物体检测结果
const detections = await model.detect(canvas);

// 在 Canvas 上绘制边界框
detections.forEach(detection => {
  const [x, y, width, height] = detection.bbox;
  
  // 绘制边界框
  ctx.strokeStyle = '#00ff00';
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, width, height);
  
  // 绘制标签
  ctx.fillStyle = '#00ff00';
  ctx.font = '16px sans-serif';
  const label = `${detection.class} (${(detection.score * 100).toFixed(1)}%)`;
  ctx.fillText(label, x, y - 5);
});
```

### 16.6.3 实时姿态检测与 Canvas 标注

```javascript
import * as poseDetection from '@tensorflow-models/pose-detection';

const detector = await poseDetection.createDetector(
  poseDetection.SupportedModels.MoveNet
);

async function detectAndDraw(video, canvas) {
  const ctx = canvas.getContext('2d');
  
  async function frame() {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const poses = await detector.estimatePoses(video);
    
    poses.forEach(pose => {
      // 绘制骨架连线
      poseDetection.util.getAdjacentPairs(
        poseDetection.SupportedModels.MoveNet
      ).forEach(([i, j]) => {
        const kp1 = pose.keypoints[i];
        const kp2 = pose.keypoints[j];
        
        if (kp1.score > 0.3 && kp2.score > 0.3) {
          ctx.beginPath();
          ctx.moveTo(kp1.x, kp1.y);
          ctx.lineTo(kp2.x, kp2.y);
          ctx.strokeStyle = '#00ff00';
          ctx.lineWidth = 3;
          ctx.stroke();
        }
      });
      
      // 绘制关键点
      pose.keypoints.forEach(kp => {
        if (kp.score > 0.3) {
          ctx.beginPath();
          ctx.arc(kp.x, kp.y, 5, 0, Math.PI * 2);
          ctx.fillStyle = '#ff0000';
          ctx.fill();
        }
      });
    });
    
    requestAnimationFrame(frame);
  }
  frame();
}
```

> 金句：AI 给你"看到"的能力，Canvas 给你"画出"的能力——两者结合，就是机器视觉的完整闭环。

## 16.7 跨技术协作架构总结

```
                    Canvas 跨技术协作全景
                    
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    CSS      │   │     SVG     │   │   Worker    │
│  滤镜/动画   │   │  矢量/交互  │   │  并行计算   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                  │
       │                 │                  │
┌──────┴─────────────────┴──────────────────┴──────┐
│                                                   │
│                 Canvas (核心)                      │
│            像素缓冲区 + 2D/WebGL 上下文            │
│                                                   │
└──┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │
   │          │          │          │
┌──┴──┐  ┌───┴──┐  ┌────┴───┐  ┌────┴────┐
│Video│  │Audio │  │  AI/ML │  │  其他   │
│视频 │  │音频  │  │推理结果 │  │WebRTC等│
└─────┘  └──────┘  └────────┘  └─────────┘
```

| 协作场景 | Canvas 角色 | 合作技术 | 典型应用 |
|---------|------------|---------|---------|
| CSS 滤镜叠加 | 渲染目标 | CSS filter | 双重滤镜效果 |
| SVG 矢量交互 | 像素渲染层 | SVG 事件系统 | 混合架构图表 |
| 视频处理 | 帧处理器 | Video + captureStream | 滤镜/录制 |
| 音频可视化 | 频谱渲染器 | Web Audio Analyser | 音乐可视化 |
| Worker 渲染 | 渲染执行者 | OffscreenCanvas | 不阻塞主线程 |
| AI 可视化 | 结果标注器 | TensorFlow.js | 姿态/物体检测 |

## 16.8 本章总结

| 协作技术 | 核心机制 | 典型场景 |
|---------|---------|---------|
| CSS | ctx.filter / canvas.style.filter / mix-blend-mode | 滤镜叠加/主题化 |
| SVG | drawImage(svg) / SVG 事件层 | 混合渲染架构 |
| Video | drawImage(video) / captureStream | 视频滤镜/录制 |
| Audio | AnalyserNode + getByteFrequencyData | 音乐可视化 |
| Worker | OffscreenCanvas / postMessage | 并行计算/不阻塞 UI |
| AI | tf.browser.fromPixels + model.predict | 物体检测/姿态识别 |

觉得有用？收藏起来，跨技术协作是 Canvas 高级应用的必经之路。

你在项目中用过 Canvas 和哪些技术组合？评论区聊聊你的架构。

关注怕浪猫，下期我们进入 **附录篇**——官方规范网址、API 速查表、数学公式和术语对照表。

系列进度 16/17

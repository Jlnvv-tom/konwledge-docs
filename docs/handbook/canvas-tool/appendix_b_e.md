# 附录 B-E：API 速查、数学公式、术语对照表

这是 Canvas 工程全书的最后一篇附录。B 速查表、C WebGL API 速查、D 数学公式、E 术语对照表，合并为一篇方便收藏查阅。

我是怕浪猫，纯干货，不废话。

## B. Canvas 2D API 速查表

### B.1 上下文获取与配置

| API | 说明 | 示例 |
|-----|------|------|
| canvas.getContext('2d') | 获取 2D 上下文 | const ctx = canvas.getContext('2d') |
| canvas.getContext('webgl') | 获取 WebGL 上下文 | const gl = canvas.getContext('webgl') |
| canvas.getContext('webgpu') | 获取 WebGPU 上下文 | const ctx = canvas.getContext('webgpu') |
| ctx.canvas | 反向引用 canvas 元素 | ctx.canvas.width = 800 |

### B.2 矩形绘制

| API | 说明 |
|-----|------|
| fillRect(x, y, w, h) | 填充矩形 |
| strokeRect(x, y, w, h) | 描边矩形 |
| clearRect(x, y, w, h) | 清除矩形区域 |

### B.3 路径

| API | 说明 |
|-----|------|
| beginPath() | 开始新路径 |
| closePath() | 闭合当前子路径 |
| moveTo(x, y) | 移动到点（不画线） |
| lineTo(x, y) | 画线到点 |
| arc(x, y, r, start, end, ccw) | 画圆弧 |
| arcTo(x1, y1, x2, y2, r) | 画圆弧到切点 |
| ellipse(x, y, rx, ry, rot, start, end) | 画椭圆弧 |
| quadraticCurveTo(cpx, cpy, x, y) | 二次贝塞尔曲线 |
| bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y) | 三次贝塞尔曲线 |
| rect(x, y, w, h) | 添加矩形到路径 |
| roundRect(x, y, w, h, radii) | 添加圆角矩形到路径 |
| fill(path, fillRule) | 填充路径 |
| stroke(path) | 描边路径 |
| clip(path, fillRule) | 设置裁剪路径 |
| isPointInPath(x, y, fillRule) | 点是否在路径内 |
| isPointInStroke(x, y) | 点是否在描边线上 |

### B.4 文本

| API | 说明 |
|-----|------|
| fillText(text, x, y, maxWidth) | 填充文本 |
| strokeText(text, x, y, maxWidth) | 描边文本 |
| measureText(text) | 测量文本宽度（返回 TextMetrics） |

### B.5 图像

| API | 说明 |
|-----|------|
| drawImage(image, dx, dy) | 绘制图像（原始尺寸） |
| drawImage(image, dx, dy, dw, dh) | 绘制图像（缩放） |
| drawImage(image, sx, sy, sw, sh, dx, dy, dw, dh) | 绘制图像（裁剪+缩放） |
| createImageData(w, h) | 创建空白 ImageData |
| getImageData(x, y, w, h) | 读取像素数据 |
| putImageData(imageData, x, y) | 写入像素数据 |

### B.6 状态管理

| API | 说明 |
|-----|------|
| save() | 保存当前状态到栈 |
| restore() | 从栈恢复状态 |
| reset() | 重置所有状态到默认值 |

### B.7 变换

| API | 说明 |
|-----|------|
| translate(x, y) | 平移 |
| rotate(angle) | 旋转（弧度） |
| scale(x, y) | 缩放 |
| transform(a, b, c, d, e, f) | 矩阵乘法叠加 |
| setTransform(a, b, c, d, e, f) | 绝对设置变换矩阵 |
| resetTransform() | 重置为单位矩阵 |
| getTransform() | 获取当前变换矩阵 |

### B.8 样式

| 属性 | 说明 |
|------|------|
| fillStyle | 填充样式（颜色/渐变/图案） |
| strokeStyle | 描边样式 |
| lineWidth | 线宽 |
| lineCap | 线端点样式（butt/round/square） |
| lineJoin | 线连接样式（miter/round/bevel） |
| miterLimit | miter 连接的最大长度比 |
| setLineDash(segments) | 设置虚线模式 |
| lineDashOffset | 虚线偏移量 |
| font | 字体设置 |
| textAlign | 文本对齐 |
| textBaseline | 文本基线 |
| direction | 文本方向 |

### B.9 合成与滤镜

| 属性 | 说明 |
|------|------|
| globalAlpha | 全局透明度 (0-1) |
| globalCompositeOperation | 合成模式 |
| filter | 滤镜（CSS filter 字符串） |

### B.10 渐变与图案

| API | 说明 |
|-----|------|
| createLinearGradient(x0, y0, x1, y1) | 线性渐变 |
| createRadialGradient(x0, y0, r0, x1, y1, r1) | 径向渐变 |
| createConicGradient(startAngle, x, y) | 圆锥渐变 |
| gradient.addColorStop(offset, color) | 添加色标 |
| createPattern(image, repetition) | 创建图案 |

## C. WebGL API 速查表

### C.1 着色器与程序

| API | 说明 |
|-----|------|
| createShader(type) | 创建着色器对象 |
| shaderSource(shader, source) | 设置着色器源码 |
| compileShader(shader) | 编译着色器 |
| getShaderParameter(shader, pname) | 获取着色器参数 |
| getShaderInfoLog(shader) | 获取编译错误信息 |
| createProgram() | 创建程序对象 |
| attachShader(program, shader) | 附加着色器 |
| linkProgram(program) | 链接程序 |
| useProgram(program) | 使用程序 |
| getAttribLocation(program, name) | 获取属性位置 |
| getUniformLocation(program, name) | 获取 Uniform 位置 |

### C.2 缓冲区

| API | 说明 |
|-----|------|
| createBuffer() | 创建缓冲区 |
| bindBuffer(target, buffer) | 绑定缓冲区 |
| bufferData(target, data, usage) | 上传数据 |
| enableVertexAttribArray(index) | 启用属性数组 |
| vertexAttribPointer(index, size, type, norm, stride, offset) | 配置属性指针 |
| vertexAttribDivisor(index, divisor) | 设置实例化除数（WebGL2） |

### C.3 纹理

| API | 说明 |
|-----|------|
| createTexture() | 创建纹理 |
| bindTexture(target, texture) | 绑定纹理 |
| texImage2D(target, level, internal, format, type, source) | 上传纹理数据 |
| texParameteri(target, pname, param) | 设置纹理参数 |
| activeTexture(unit) | 激活纹理单元 |
| uniform1i(location, unit) | 绑定采样器到纹理单元 |

### C.4 帧缓冲

| API | 说明 |
|-----|------|
| createFramebuffer() | 创建 FBO |
| bindFramebuffer(target, fbo) | 绑定 FBO |
| framebufferTexture2D(target, attachment, textarget, texture, level) | 附加纹理 |
| createRenderbuffer() | 创建 RBO |
| framebufferRenderbuffer(target, attachment, rbtarget, rbo) | 附加 RBO |
| checkFramebufferStatus(target) | 检查 FBO 完整性 |

### C.5 绘制

| API | 说明 |
|-----|------|
| drawArrays(mode, first, count) | 绘制 |
| drawElements(mode, count, type, offset) | 索引绘制 |
| drawArraysInstanced(mode, first, count, instanceCount) | 实例化绘制（WebGL2） |
| drawElementsInstanced(mode, count, type, offset, instanceCount) | 索引实例化绘制（WebGL2） |

### C.6 状态

| API | 说明 |
|-----|------|
| enable(cap) | 启用功能 |
| disable(cap) | 禁用功能 |
| clearColor(r, g, b, a) | 设置清屏色 |
| clear(mask) | 清除缓冲区 |
| viewport(x, y, w, h) | 设置视口 |
| depthFunc(func) | 深度比较函数 |
| blendFunc(sfactor, dfactor) | 混合函数 |
| cullFace(mode) | 面剔除 |
| frontFace(mode) | 正面方向 |

## D. 数学公式速查

### D.1 坐标变换

**平移矩阵**：
```
│ 1  0  tx │
│ 0  1  ty │
│ 0  0   1 │
```

**缩放矩阵**：
```
│ sx   0   0 │
│  0  sy   0 │
│  0   0   1 │
```

**旋转矩阵**（绕 Z 轴旋转角度 θ）：
```
│ cosθ  -sinθ  0 │
│ sinθ   cosθ  0 │
│   0      0   1 │
```

**MVP 矩阵链**：
```
clip = Projection × View × Model × local
```

**透视投影矩阵**（fov, aspect, near, far）：
```
f = 1/tan(fov/2)

│ f/aspect  0                    0                         0  │
│    0      f                    0                         0  │
│    0      0    (far+near)/(near-far)    2×far×near/(near-far)│
│    0      0           -1                         0           │
```

### D.2 几何

**点到直线距离**：
```
d = |Ax + By + C| / sqrt(A² + B²)
```

**点到线段距离**：
```
设线段 P1→P2，点 P
t = dot(P - P1, P2 - P1) / dot(P2 - P1, P2 - P1)
t = clamp(t, 0, 1)
最近点 = P1 + t × (P2 - P1)
距离 = |P - 最近点|
```

**点在多边形内（射线法）**：
```
交点数为奇数 → 在内部
交点数为偶数 → 在外部
```

**点在矩形内**：
```
x >= rx && x <= rx + rw && y >= ry && y <= ry + rh
```

**点在圆内**：
```
(x - cx)² + (y - cy)² <= r²
```

**两矩形相交（AABB）**：
```
a.x < b.x + b.w && a.x + a.w > b.x &&
a.y < b.y + b.h && a.y + a.h > b.y
```

### D.3 缓动函数

```
linear:        f(t) = t
easeInQuad:    f(t) = t²
easeOutQuad:   f(t) = t × (2 - t)
easeInOutQuad: f(t) = t < 0.5 ? 2t² : -1 + (4 - 2t) × t
easeInCubic:   f(t) = t³
easeOutCubic:  f(t) = (t-1)³ + 1
easeInOutCubic:f(t) = t < 0.5 ? 4t³ : (t-1)(2t-2)² + 1
easeInElastic: f(t) = 0 if t==0, 1 if t==1, -2^(10(t-1)) × sin((t-1.075)×2π/0.3)
```

### D.4 光照

**Lambert 漫反射**：
```
I = max(dot(N, L), 0) × lightColor × surfaceColor
```

**Phong 镜面反射**：
```
R = reflect(-L, N)
I = pow(max(dot(R, V), 0), shininess) × specularColor
```

**Blinn-Phong**：
```
H = normalize(L + V)
I = pow(max(dot(N, H), 0), shininess) × specularColor
```

**衰减**：
```
attenuation = 1 / (1 + k1×d + k2×d²)
```

## E. 术语对照表

| 英文术语 | 缩写 | 中文 | 说明 |
|---------|------|------|------|
| Application Programming Interface | API | 应用程序接口 | 软件组件间的接口 |
| Graphics Processing Unit | GPU | 图形处理器 | 专门处理图形渲染的处理器 |
| Central Processing Unit | CPU | 中央处理器 | 通用计算处理器 |
| Canvas Rendering Context 2D | - | Canvas 2D 上下文 | 2D 位图绘制接口 |
| WebGL | - | Web 图形库 | 基于 OpenGL ES 的 Web 图形 API |
| WebGPU | - | - | 下一代 Web 图形 API |
| OpenGL for Embedded Systems | OpenGL ES | 嵌入式 OpenGL | 移动设备图形 API |
| OpenGL Shading Language | GLSL | OpenGL 着色器语言 | WebGL 着色器编程语言 |
| WebGPU Shading Language | WGSL | WebGPU 着色器语言 | WebGPU 着色器编程语言 |
| Vertex Buffer Object | VBO | 顶点缓冲对象 | GPU 中的顶点数据缓冲区 |
| Index Buffer Object | IBO | 索引缓冲对象 | 顶点索引缓冲区 |
| Vertex Array Object | VAO | 顶点数组对象 | 封装顶点属性配置 |
| Framebuffer Object | FBO | 帧缓冲对象 | 离屏渲染目标 |
| Renderbuffer Object | RBO | 渲染缓冲对象 | FBO 的深度/模板附件 |
| Texture Map | - | 纹理贴图 | 图像数据映射到图元表面 |
| Texture Atlas | - | 纹理图集 | 多个小纹理合并的大图 |
| Mipmap | - | 多级渐远纹理 | 不同分辨率的纹理金字塔 |
| Field of View | FOV | 视野角度 | 相机的可见角度范围 |
| Frames Per Second | FPS | 每秒帧数 | 帧率指标 |
| Request Animation Frame | rAF | 请求动画帧 | 浏览器刷新同步 API |
| Normalized Device Coordinates | NDC | 归一化设备坐标 | [-1,1] 范围的标准坐标 |
| Model-View-Projection | MVP | 模型-视图-投影 | 三种变换矩阵的乘积 |
| Viewport | - | 视口 | 渲染目标在屏幕上的区域 |
| Frustum | - | 视锥 | 相机可见的空间范围 |
| Culling | - | 剔除 | 跳过不可见图元 |
| Clipping | - | 裁剪 | 切除视锥外的图元部分 |
| Rasterization | - | 光栅化 | 矢量图元转像素 |
| Fragment | - | 片元 | 候选像素 |
| Shader | - | 着色器 | GPU 上运行的程序 |
| Vertex Shader | VS | 顶点着色器 | 处理顶点的着色器 |
| Fragment Shader | FS | 片元着色器 | 处理片元的着色器 |
| Compute Shader | CS | 计算着色器 | 通用计算的着色器 |
| Depth Buffer | Z-Buffer | 深度缓冲区 | 存储像素深度值的缓冲区 |
| Stencil Buffer | - | 模板缓冲区 | 用于掩码操作的缓冲区 |
| Z-Fighting | - | 深度冲突 | 共面图元闪烁问题 |
| Backface Culling | - | 背面剔除 | 跳过背面的三角形 |
| Alpha Blending | - | Alpha 混合 | 半透明混合 |
| Porter-Duff | - | 波特-达夫 | 合成运算模型 |
| Immediate Mode | - | 即时模式 | 命令式绘制（Canvas） |
| Retained Mode | - | 保留模式 | 声明式绘制（SVG） |
| Dirty Rectangle | - | 脏矩形 | 只重绘变化区域 |
| Level of Detail | LOD | 细节层次 | 按距离切换精度 |
| Draw Call | - | 绘制调用 | 一次 GPU 绘制命令 |
| Instanced Rendering | - | 实例化渲染 | 一次 Draw Call 绘制多个实例 |
| Fast Fourier Transform | FFT | 快速傅里叶变换 | 音频频谱分析算法 |
| Physically Based Rendering | PBR | 基于物理的渲染 | 基于物理的光照模型 |
| Bidirectional Reflectance Distribution Function | BRDF | 双向反射分布函数 | 描述表面反射的函数 |
| Screen Space Reflection | SSR | 屏幕空间反射 | 基于屏幕信息的反射算法 |
| High Dynamic Range | HDR | 高动态范围 | 超过 [0,1] 的颜色范围 |
| Low Dynamic Range | LDR | 低动态范围 | [0,1] 标准颜色范围 |
| Tone Mapping | - | 色调映射 | HDR 转 LDR 的算法 |
| OffscreenCanvas | - | 离屏画布 | 可在 Worker 中使用的画布 |
| Device Pixel Ratio | DPR | 设备像素比 | 物理像素/CSS 像素 |
| Accessibility | a11y | 可访问性 | 残障用户的可使用程度 |
| Garbage Collection | GC | 垃圾回收 | 自动内存回收机制 |
| Hit Testing | - | 命中检测 | 判断点击位置对应哪个图元 |
| Quadtree | - | 四叉树 | 2D 空间索引数据结构 |
| Bounding Box | AABB | 轴对齐包围盒 | 与坐标轴对齐的矩形边界 |
| Bezier Curve | - | 贝塞尔曲线 | 用控制点定义的参数曲线 |
| Path2D | - | 路径对象 | 可复用的路径描述 |
| ImageData | - | 像素数据 | 像素级操作的内存数据 |

觉得有用？收藏起来，这是整个系列的速查手册。

Canvas 工程全书到此完结。17 篇文章，从浏览器渲染原理到 WebGPU，从基本绘制到 AI 协作，涵盖了你需要知道的一切。

感谢追更。我是怕浪猫，我们下个系列见。

系列进度 17/17（全书完结）

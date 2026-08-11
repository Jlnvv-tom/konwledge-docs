# 第12章 WebGL 进阶：深度缓冲、光照、FBO 与性能优化

3 种光照模型加 4 种纹理进阶加 5 种优化策略，WebGL 进阶一篇搞定。

上一篇画了第一个三角形，但那只是 WebGL 的起点。真实的 3D 应用需要处理深度遮挡、光照阴影、后处理特效和性能优化。这些才是 WebGL 开发的深水区。

我是怕浪猫，这一章带你从"能画三角形"进化到"能做真正的 3D 渲染"。

## 12.1 深度缓冲与面剔除

### 12.1.1 深度缓冲区原理

深度缓冲区（Depth Buffer，也叫 Z-Buffer）是一块和画布等大的额外缓冲区，存储每个像素的深度值（Z 值）。

```
颜色缓冲区：              深度缓冲区：
┌──┬──┬──┬──┐          ┌──┬──┬──┬──┐
│R │G │B │R │          │0.1│0.8│0.5│0.2│
├──┼──┼──┼──┤          ├──┼──┼──┼──┤
│G │R │B │G │          │0.3│0.1│0.9│0.4│
└──┴──┴──┘              └──┴──┴──┘
每个像素存颜色             每个像素存深度值
```

深度测试的工作流程：

```
新片元（深度 = z）
    │
    ▼
  读取深度缓冲区当前值 zBuffer
    │
    ├── z < zBuffer（更近）→ 通过测试
    │   ├── 写入颜色到颜色缓冲区
    │   └── 更新深度缓冲区为 z
    │
    └── z >= zBuffer（更远或相等）→ 丢弃片元
```

启用深度测试：

```javascript
// 初始化时启用
gl.enable(gl.DEPTH_TEST);

// 设置深度比较函数
gl.depthFunc(gl.LESS);  // 默认：深度更小（更近）的通过

// 每帧渲染前清空深度缓冲区
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
```

> 金句：深度缓冲是 3D 渲染的"自动遮挡处理器"——没有它，你画的立方体看起来像个透明的纸盒。

### 12.1.2 深度冲突（Z-Fighting）的成因与解决

Z-Fighting 发生在两个面的深度值非常接近时，GPU 无法精确区分哪个更近，导致画面出现闪烁/条纹：

```
面 A (z = 0.5000001)  ─┐
                        ├── 同一像素，GPU 分不清谁前谁后
面 B (z = 0.5000002)  ─┘
```

**解决方案**：

```javascript
// 方案 1：Polygon Offset（多边形偏移）
gl.enable(gl.POLYGON_OFFSET_FILL);
gl.polygonOffset(1.0, 1.0);  // 将共面图元稍微推远

// 方案 2：调整近远裁剪面（提高深度缓冲精度）
// 差的做法：near = 0.001, far = 10000（深度精度极差）
// 好的做法：near = 0.1, far = 100（深度精度好得多）
const projection = perspective(fov, aspect, 0.1, 100);

// 方案 3：使用更高精度的深度缓冲
// WebGL 默认 16 位深度，可以请求 24 位
const gl = canvas.getContext('webgl', { depth: true });
// 大多数浏览器在 depth: true 时会使用 24 位深度缓冲
```

深度精度问题的根本原因：透视投影后深度值不是线性分布的，近处精度高、远处精度低。所以 near 平面太近会浪费近处的精度，导致远处 Z-Fighting。

### 12.1.3 背面剔除

背面剔除（Face Culling）跳过背对相机的三角形，减少约 50% 的片元处理：

```javascript
gl.enable(gl.CULL_FACE);
gl.cullFace(gl.BACK);           // 剔除背面（默认）
gl.frontFace(gl.CCW);           // 逆时针为正面（默认）
// 或 gl.frontFace(gl.CW);      // 顺时针为正面
```

```
正面朝向（CCW，逆时针）：     背面朝向（CW，顺时针）：
  v0                            v0
  │ \                           │ /
  │  \                          │/
  │   v2                        v2
  │  /                          │
  │ /                           │
  v1                            v1
（可见，渲染）                 （不可见，剔除）
```

> 金句：背面剔除是免费的性能优化——一个 enable 就砍掉一半的片元计算量。

## 12.2 光照实战

### 12.2.1 法线与法线矩阵

法线（Normal）是垂直于表面的向量，用于光照计算。法线矩阵（Normal Matrix）是模型视图矩阵左上 3x3 的逆矩阵的转置：

```javascript
// 计算法线矩阵
function normalMatrix(modelViewMatrix) {
  const m3 = [
    modelViewMatrix[0], modelViewMatrix[1], modelViewMatrix[2],
    modelViewMatrix[4], modelViewMatrix[5], modelViewMatrix[6],
    modelViewMatrix[8], modelViewMatrix[9], modelViewMatrix[10],
  ];
  // 逆矩阵
  const inv = inverse3x3(m3);
  // 转置
  return transpose3x3(inv);
}
```

为什么不能直接用模型矩阵变换法线？因为非均匀缩放会扭曲法线方向：

```
原始三角形 + 法线          非均匀缩放后：
    │ N                       │ N'（错误！）
    │                         │
    ─────                     ───────────
                               │ N''（正确，需要法线矩阵）
```

### 12.2.2 环境光 + 漫反射 + 镜面反射

完整的 Phong 光照着色器：

```glsl
// 顶点着色器
attribute vec3 aPosition;
attribute vec3 aNormal;
uniform mat4 uModelMatrix;
uniform mat4 uViewMatrix;
uniform mat4 uProjMatrix;
uniform mat3 uNormalMatrix;
uniform vec3 uLightPos;
uniform vec3 uViewPos;

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec3 vLightPos;
varying vec3 vViewPos;

void main() {
  vec4 worldPos = uModelMatrix * vec4(aPosition, 1.0);
  gl_Position = uProjMatrix * uViewMatrix * worldPos;
  
  vFragPos = worldPos.xyz;
  vNormal = normalize(uNormalMatrix * aNormal);
  vLightPos = uLightPos;
  vViewPos = uViewPos;
}
```

```glsl
// 片元着色器
precision mediump float;

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec3 vLightPos;
varying vec3 vViewPos;

void main() {
  // 材质属性
  vec3 objectColor = vec3(1.0, 0.5, 0.3);
  float ambientStrength = 0.1;
  float specularStrength = 0.5;
  float shininess = 32.0;
  
  // 环境光
  vec3 ambient = ambientStrength * vec3(1.0);
  
  // 漫反射
  vec3 norm = normalize(vNormal);
  vec3 lightDir = normalize(vLightPos - vFragPos);
  float diff = max(dot(norm, lightDir), 0.0);
  vec3 diffuse = diff * vec3(1.0);
  
  // 镜面反射（Blinn-Phong）
  vec3 viewDir = normalize(vViewPos - vFragPos);
  vec3 halfwayDir = normalize(lightDir + viewDir);
  float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);
  vec3 specular = specularStrength * spec * vec3(1.0);
  
  // 最终颜色
  vec3 result = (ambient + diffuse + specular) * objectColor;
  gl_FragColor = vec4(result, 1.0);
}
```

### 12.2.3 多光源与光照衰减

实际应用中通常有多个光源，且光照随距离衰减：

```glsl
// 多光源 + 衰减
#define MAX_LIGHTS 4
uniform int uNumLights;
uniform vec3 uLightPositions[MAX_LIGHTS];
uniform vec3 uLightColors[MAX_LIGHTS];

float calculateAttenuation(float distance) {
  // 衰减公式：1 / (d²) 或更精细的模型
  // attenuation = 1.0 / (1.0 + 0.1*d + 0.01*d*d)
  return 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
}

vec3 calculateLight(vec3 lightPos, vec3 lightColor, vec3 norm, vec3 fragPos, vec3 viewDir) {
  vec3 lightDir = normalize(lightPos - fragPos);
  float distance = length(lightPos - fragPos);
  float attenuation = calculateAttenuation(distance);
  
  // 漫反射
  float diff = max(dot(norm, lightDir), 0.0);
  vec3 diffuse = diff * lightColor * attenuation;
  
  // 镜面反射
  vec3 halfwayDir = normalize(lightDir + viewDir);
  float spec = pow(max(dot(norm, halfwayDir), 0.0), 32.0);
  vec3 specular = 0.5 * spec * lightColor * attenuation;
  
  return diffuse + specular;
}
```

### 12.2.4 Phong 着色 vs Gouraud 着色

| 方式 | 计算位置 | 效果 | 计算量 |
|------|---------|------|--------|
| Gouraud | 顶点着色器 | 低多边形有马赫带（色带） | 低（每顶点一次） |
| Phong | 片元着色器 | 平滑、高质量 | 高（每片元一次） |

```
Gouraud（逐顶点光照）：      Phong（逐片元光照）：
顶点颜色插值                 法线插值后逐片元计算光照
┌──┐                         ┌──┐
│A │ 颜色在顶点算好后插值     │A │ 法线插值到每个片元
├──┤                         ├──┤  在片元着色器算光照
│B │                         │B │  结果更平滑
└──┘                         └──┘
（低面数时有色带）              （始终平滑）
```

> 金句：Gouraud 是"算好再插值"，Phong 是"插值再算"——前者省算力，后者出效果。

## 12.3 纹理进阶

### 12.3.1 多重纹理

```glsl
// 同时采样两张纹理并混合
uniform sampler2D uTexture1;  // 基础纹理
uniform sampler2D uTexture2;  // 细节纹理
uniform float uBlendFactor;

void main() {
  vec4 color1 = texture2D(uTexture1, vTexCoord);
  vec4 color2 = texture2D(uTexture2, vTexCoord * 4.0);  // 细节纹理放大
  gl_FragColor = mix(color1, color2, uBlendFactor);
}
```

### 12.3.2 法线贴图

法线贴图存储表面法线信息，用低面数模型模拟高面数模型的光照效果：

```glsl
// 法线贴图光照
uniform sampler2D uNormalMap;

void main() {
  // 从法线贴图采样法线（范围 [0,1]）
  vec3 normal = texture2D(uNormalMap, vTexCoord).rgb;
  // 转换到范围 [-1,1]
  normal = normalize(normal * 2.0 - 1.0);
  
  // 注意：需要 TBN 矩阵将切线空间法线转换到世界空间
  // TBN = Tangent, Bitangent, Normal
  vec3 worldNormal = normalize(vTBN * normal);
  
  // 后续光照计算使用 worldNormal
  vec3 lightDir = normalize(uLightPos - vFragPos);
  float diff = max(dot(worldNormal, lightDir), 0.0);
  // ...
}
```

### 12.3.3 环境贴图与立方体映射

Cube Map（立方体映射）用于环境反射，6 个面组成一个立方体：

```javascript
// 创建 Cube Map 纹理
const cubeMap = gl.createTexture();
gl.bindTexture(gl.TEXTURE_CUBE_MAP, cubeMap);

// 6 个面的纹理
const faces = [
  { target: gl.TEXTURE_CUBE_MAP_POSITIVE_X, image: pxImage },
  { target: gl.TEXTURE_CUBE_MAP_NEGATIVE_X, image: nxImage },
  { target: gl.TEXTURE_CUBE_MAP_POSITIVE_Y, image: pyImage },
  { target: gl.TEXTURE_CUBE_MAP_NEGATIVE_Y, image: nyImage },
  { target: gl.TEXTURE_CUBE_MAP_POSITIVE_Z, image: pzImage },
  { target: gl.TEXTURE_CUBE_MAP_NEGATIVE_Z, image: nzImage },
];

faces.forEach(face => {
  gl.texImage2D(face.target, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, face.image);
});
```

```glsl
// 反射环境贴图
uniform samplerCube uEnvironmentMap;

void main() {
  vec3 I = normalize(vFragPos - uViewPos);     // 视线方向
  vec3 R = reflect(I, normalize(vNormal));      // 反射方向
  vec3 envColor = textureCube(uEnvironmentMap, R).rgb;
  gl_FragColor = vec4(envColor, 1.0);
}
```

### 12.3.4 阴影贴图

Shadow Mapping 是最常见的实时阴影技术，分两步：

```
Pass 1: 从光源视角渲染深度图（Shadow Map）
Pass 2: 从相机视角渲染场景，用 Shadow Map 判断是否被遮挡
```

```glsl
// Pass 2 片元着色器：判断阴影
uniform sampler2D uShadowMap;
uniform mat4 uLightSpaceMatrix;
varying vec4 vFragPosLightSpace;

float calculateShadow() {
  // 透视除法，转到 NDC
  vec3 projCoords = vFragPosLightSpace.xyz / vFragPosLightSpace.w;
  projCoords = projCoords * 0.5 + 0.5;  // 转到 [0,1]
  
  // 采样 Shadow Map 中的最近深度
  float closestDepth = texture2D(uShadowMap, projCoords.xy).r;
  float currentDepth = projCoords.z;
  
  // 比较：当前深度 > 最近深度 → 在阴影中
  float shadow = currentDepth > closestDepth + 0.005 ? 1.0 : 0.0;
  return shadow;
}
```

## 12.4 帧缓冲区（FBO）

### 12.4.1 离屏渲染概念

FBO（Framebuffer Object，帧缓冲对象）允许你渲染到一个自定义的缓冲区，而不是默认的屏幕缓冲区。这就是离屏渲染（Off-screen Rendering）。

```
默认渲染：                        FBO 渲染：
渲染 → 屏幕缓冲区 → 屏幕           渲染 → FBO 纹理 → 后处理 → 屏幕
（直接显示）                       （可以再加工）
```

### 12.4.2 创建 FBO 并附加颜色/深度附件

```javascript
function createFBO(gl, width, height) {
  // 1. 创建 FBO
  const fbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  
  // 2. 创建颜色附件（纹理）
  const colorTexture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, colorTexture);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, colorTexture, 0);
  
  // 3. 创建深度附件（Renderbuffer）
  const depthBuffer = gl.createRenderbuffer();
  gl.bindRenderbuffer(gl.RENDERBUFFER, depthBuffer);
  gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT16, width, height);
  gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, depthBuffer);
  
  // 4. 检查完整性
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
    console.error('FBO not complete');
  }
  
  // 5. 解绑
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  
  return { fbo, colorTexture, depthBuffer, width, height };
}
```

### 12.4.3 后处理：泛光、色调映射、SSR

FBO 的核心用途是后处理——将渲染结果作为纹理，在另一个着色器中处理：

```javascript
// Pass 1: 正常渲染到 FBO
gl.bindFramebuffer(gl.FRAMEBUFFER, fbo.fbo);
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
renderScene();  // 正常渲染场景

// Pass 2: 后处理（FBO 纹理 → 屏幕）
gl.bindFramebuffer(gl.FRAMEBUFFER, null);  // 切回屏幕缓冲
gl.useProgram(postProcessProgram);
gl.bindTexture(gl.TEXTURE_2D, fbo.colorTexture);  // FBO 纹理作为输入
renderQuad();  // 画一个全屏四边形，在后处理着色器中处理
```

**常见后处理效果**：

```glsl
// 色调映射（Tone Mapping）：HDR → LDR
vec3 toneMap(vec3 hdrColor) {
  // Reinhard 色调映射
  return hdrColor / (hdrColor + vec3(1.0));
}

// 泛光（Bloom）：提取亮区 → 模糊 → 叠加
float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
if (luminance > 1.0) {
  brightColor += color;  // 提取亮区
}
// ...对 brightColor 做高斯模糊，叠加到原图

// 屏幕空间反射（SSR，Screen Space Reflection）
// 用深度缓冲和法线缓冲做光线步进，模拟反射
```

> 金句：FBO 是 WebGL 的"暗房"——先拍好底片（离屏渲染），再冲洗加工（后处理），最后出片（显示）。

## 12.5 性能优化

### 12.5.1 Draw Call 合并

每次 Draw Call 都有 CPU 开销。减少 Draw Call 数量是优化重点：

```javascript
// 差：1000 个对象，1000 次 Draw Call
objects.forEach(obj => {
  gl.bindBuffer(gl.ARRAY_BUFFER, obj.vbo);
  gl.uniformMatrix4fv(obj.mvpLoc, false, obj.mvp);
  gl.drawArrays(gl.TRIANGLES, 0, obj.vertexCount);
});
// 1000 次 Draw Call，CPU 开销大

// 好：合并到一个 VBO，一次 Draw Call
const allVertices = objects.flatMap(obj => obj.vertices);
gl.bufferData(gl.ARRAY_BUFFER, allVertices, gl.STATIC_DRAW);
gl.drawArrays(gl.TRIANGLES, 0, totalVertexCount);
// 1 次 Draw Call
```

### 12.5.2 实例化渲染（WebGL2）

当需要绘制大量相同的几何体时，实例化渲染是最优方案：

```javascript
// WebGL2 实例化渲染
const instanceCount = 1000;

// 每个实例的偏移量
const offsets = new Float32Array(1000 * 3);
for (let i = 0; i < 1000; i++) {
  offsets[i * 3] = Math.random() * 100;
  offsets[i * 3 + 1] = Math.random() * 100;
  offsets[i * 3 + 2] = Math.random() * 100;
}

const offsetBuffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, offsetBuffer);
gl.bufferData(gl.ARRAY_BUFFER, offsets, gl.STATIC_DRAW);

const aOffset = gl.getAttribLocation(program, 'aOffset');
gl.enableVertexAttribArray(aOffset);
gl.vertexAttribPointer(aOffset, 3, gl.FLOAT, false, 0, 0);
gl.vertexAttribDivisor(aOffset, 1);  // 每个实例更新一次

// 一次 Draw Call 画 1000 个实例
gl.drawArraysInstanced(gl.TRIANGLES, 0, vertexCount, instanceCount);
```

### 12.5.3 视锥剔除

不渲染相机视锥外的物体：

```javascript
function isVisibleInFrustum(object, frustum) {
  // 检查物体的包围球是否与视锥相交
  for (const plane of frustum) {
    const distance = plane.x * object.center.x +
                     plane.y * object.center.y +
                     plane.z * object.center.z + plane.w;
    if (distance < -object.radius) {
      return false;  // 在视锥外，剔除
    }
  }
  return true;
}

// 渲染前剔除
const visibleObjects = allObjects.filter(obj => isVisibleInFrustum(obj, frustum));
visibleObjects.forEach(obj => renderObject(obj));
```

### 12.5.4 LOD（Level of Detail）

根据距离使用不同精度的模型：

```javascript
function selectLOD(object, cameraDistance) {
  if (cameraDistance < 10) return object.highDetailMesh;
  if (cameraDistance < 50) return object.mediumDetailMesh;
  return object.lowDetailMesh;
}
```

### 12.5.5 GPU 性能分析工具

| 工具 | 平台 | 功能 |
|------|------|------|
| Spector.js | 浏览器扩展 | 捕获 WebGL 调用序列、检查状态 |
| RenderDoc | 桌面 | 帧分析、着色器调试、纹理检查 |
| Chrome DevTools | Chrome | Performance 面板的 GPU 分析 |
| WebGL Inspector | 浏览器扩展 | WebGL 状态和资源检查 |

> 金句：性能优化不是猜的——用 Spector.js 看看你的 Draw Call 数量，你就知道瓶颈在哪。

## 12.6 本章总结

| 知识点 | 核心结论 |
|--------|---------|
| 深度缓冲 | 自动处理遮挡，每帧需要清除 |
| Z-Fighting | 深度值接近导致闪烁，用 Polygon Offset 或调整 near/far 解决 |
| 背面剔除 | 一个 enable 砍掉一半片元计算 |
| Phong 光照 | 环境光 + 漫反射 + 镜面反射 |
| Blinn-Phong | 用半角向量替代反射向量，更高效 |
| 法线矩阵 | 模型视图矩阵 3x3 逆矩阵的转置，用于变换法线 |
| 法线贴图 | 低面数模拟高面数光照效果 |
| Shadow Mapping | 两遍渲染：光源深度图 + 阴影判断 |
| FBO | 离屏渲染，后处理的基础 |
| 后处理 | 泛光、色调映射、SSR |
| 实例化渲染 | WebGL2，一次 Draw Call 画多个实例 |
| 视锥剔除 | 跳过相机外的物体 |
| LOD | 按距离切换模型精度 |

觉得有用？收藏起来，这是 WebGL 进阶的核心知识。

你的 WebGL 应用有性能问题吗？评论区说说你的场景，怕浪猫帮你诊断。

关注怕浪猫，下期我们讲 **WebGPU**——下一代图形 API，比 WebGL 更强大也更简洁。

系列进度 12/17

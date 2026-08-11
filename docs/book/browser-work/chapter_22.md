# 第22章 DevTools 与调试技巧

> DevTools 不只是 console.log 的工具。Performance 面板的火焰图能告诉你时间花在哪，Memory 面板能找到内存泄漏，Network 面板能分析瀑布图。会用 DevTools 是前端工程师的核心竞争力。

我是怕浪猫，上期讲了 Chrome 扩展开发，今天进入第 22 章：DevTools 与调试技巧。这一章拆解 DevTools 各面板的高级用法、Performance 火焰图分析、以及 Lighthouse 自动化审计。

## 22.1 DevTools 面板总览

| 面板 | 功能 | 常用场景 |
|------|------|---------|
| Elements | DOM/CSS 检查 | 调试样式 |
| Console | JS 执行/日志 | 调试代码 |
| Sources | 断点调试 | 查找 bug |
| Network | 网络请求 | API 调试 |
| Performance | 性能分析 | 火焰图分析 |
| Memory | 内存分析 | 泄漏排查 |
| Application | 存储/缓存 | Cookie/SW 调试 |
| Security | 证书/混合内容 | HTTPS 检查 |
| Lighthouse | 综合审计 | 性能/SEO/无障碍 |

## 22.2 Performance 面板

### 22.2.1 火焰图分析

Performance 面板记录页面运行的所有活动，以火焰图（Flame Chart）形式展示。

```
火焰图结构

主线程（Main）：
  ┌─────────────────────────────────┐
  │ Task: Parse HTML                │
  │ ├─ Parse HTML                   │
  │ ├─ Evaluate Script              │
  │ │  └─ EventListener             │
  │ ├─ Recalculate Style            │
  │ ├─ Layout                       │
  │ └─ Paint                        │
  └─────────────────────────────────┘
  
  宽度 = 执行时间
  层级 = 调用栈深度
  颜色 = 活动类型
    黄色 = JavaScript
    紫色 = Layout
    绿色 = Paint
    灰色 = idle
```

| 颜色 | 活动类型 | 关注点 |
|------|---------|--------|
| 黄色 | JavaScript | 长任务 |
| 紫色 | Layout | 强制布局 |
| 绿色 | Paint | 绘制开销 |
| 蓝色 | Parse HTML | 解析 |
| 红色 | 长任务 | > 50ms |

### 22.2.2 关键性能指标

```
Performance 面板标记

  LCP ──────●
  FCP ──●
  DCL ────────●
  L ──────────────●
  
  时间轴：
  0s----1s----2s----3s----4s
  
  Main Thread:
  ████ Parse HTML
     ████ Evaluate Script
        ██ Layout
          ████ Paint
  
  Network:
  ──●── HTML
    ──●── CSS
    ──●── JS
      ──●── Image
```

### 22.2.3 长任务分析

```javascript
// Performance 面板中的长任务标记
// 红色三角形表示 > 50ms 的任务

// 定位长任务
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('长任务:', entry.duration, 'ms');
    console.log('来源:', entry.attribution);
  }
}).observe({ type: 'longtask', buffered: true });
```

## 22.3 Sources 面板调试

### 22.3.1 断点类型

| 断点类型 | 设置方式 | 用途 |
|---------|---------|------|
| 行断点 | 点击行号 | 在特定行暂停 |
| 条件断点 | 右键行号 → Condition | 满足条件暂停 |
| Log Point | 右键行号 → Log | 不暂停只输出 |
| DOM 断点 | Elements 面板 → Break on | DOM 变化暂停 |
| XHR 断点 | Sources → XHR Breakpoints | 网络请求暂停 |
| Event 断点 | Sources → Event Listeners | 事件触发暂停 |
| Exception 断点 | Sources → Pause on exceptions | 异常暂停 |

### 22.3.2 调试技巧

```javascript
// 1. 使用条件断点替代 console.log
// 右键行号 → Conditional breakpoint
// 输入: user.id === 123

// 2. Log Point 不暂停只输出
// 右键行号 → Logpoint
// 输入: 'User:', user.name, 'Count:', count

// 3. 使用 console.trace 追踪调用栈
function deepFunction() {
  console.trace('调用栈');
}

// 4. 使用 console.table 展示数据
console.table(users);

// 5. 使用 console.group 分组日志
console.group('API 请求');
console.log('URL:', url);
console.log('Method:', method);
console.groupEnd();
```

## 22.4 Network 面板

### 22.4.1 瀑布图分析

```
网络瀑布图

请求1: HTML  ──●═════════════
请求2: CSS     ──●════════
请求3: JS      ──●══════════
请求4: Image        ──●══════════════
请求5: API              ──●══════

颜色：
  白色: 等待（Waiting/TTFB）
  灰色: DNS 解析
  橙色: 连接建立
  绿色: 内容下载

关键指标：
  Queueing: 排队时间
  Stalled: 停滞时间
  DNS: DNS 解析
  Initial Connection: TCP 连接
  SSL: TLS 握手
  Request Sent: 请求发送
  Waiting (TTFB): 等待首字节
  Content Download: 内容下载
```

### 22.4.2 网络过滤和搜索

| 过滤方式 | 示例 | 说明 |
|---------|------|------|
| 按类型 | Fetch/XHR/JS/CSS/Img | 资源类型 |
| 按域名 | domain:example.com | 特定域名 |
| 按状态 | status-code:200 | 状态码 |
| 按大小 | larger-than:1M | 文件大小 |
| 按时间 | mime-type:json | MIME 类型 |

## 22.5 Lighthouse 审计

### 22.5.1 Lighthouse 评分

| 类别 | 权重 | 说明 |
|------|------|------|
| Performance | 35% | 性能指标 |
| Accessibility | 20% | 无障碍 |
| Best Practices | 15% | 最佳实践 |
| SEO | 15% | 搜索优化 |
| PWA | 15% | PWA 合规 |

### 22.5.2 Lighthouse CI 自动化

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            https://example.com
          budgetPath: ./lighthouse-budget.json
```

```json
// lighthouse-budget.json
{
  "ci": {
    "assert": {
      "preset": "lighthouse:no-pwa",
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
      }
    }
  }
}
```

## 22.6 Console 高级技巧

```javascript
// 1. console.time 计时
console.time('操作');
doWork();
console.timeEnd('操作');  // 操作: 123.45ms

// 2. console.count 计数
function handleClick() {
  console.count('点击次数');
}

// 3. console.assert 断言
console.assert(user !== null, '用户不应为空');

// 4. console.dir 显示对象结构
console.dir(document.body);

// 5. $0 引用 Elements 面板选中的元素
// 在 Console 中直接操作
$0.style.color = 'red';

// 6. $$ 和 querySelectorAll
$$('.item');  // 等同于 document.querySelectorAll('.item')

// 7. monitor 监听函数调用
monitor(window.scrollTo);  // 每次 scrollTo 被调用时输出

// 8. monitorEvents 监听事件
monitorEvents(window, 'resize');
```

## 22.7 Performance 面板高级分析

### 22.7.1 Main Thread 火焰图深度解读

Performance 面板中的 Main thread 火焰图是性能分析的核武器。每一层代表调用栈的一帧，宽度代表执行时间。学会读火焰图，就能精确定位性能瓶颈。

```
火焰图深度解读

Main Thread
┌─────────────────────────────────────────────────┐
│ Task: Run Microtasks                          2ms│
│ ├─ Promise.resolve().then()                   1ms│
│ └─ queueMicrotask()                           1ms│
├─────────────────────────────────────────────────┤
│ Task: Event Click                             45ms│
│ ├─ EventListener                             40ms│
│ │  ├─ handleClick()                          35ms│
│ │  │  ├─ updateDOM()                         20ms│
│ │  │  │  ├─ recalculateStyle()               5ms │
│ │  │  │  ├─ layout()                         10ms│ ← 紫色：强制布局
│ │  │  │  └─ paint()                           5ms │ ← 绿色：绘制
│ │  │  └─ fetchData()                         15ms│
│ │  │     └─ JSON.parse()                      5ms│
│ │  └─ dispatchEvent()                         5ms│
│ └─ Run Microtasks                             5ms│
├─────────────────────────────────────────────────┤
│ Task: Timer Fired                            120ms│ ← 红色：长任务
│ ├─ setInterval callback                      80ms│
│ │  ├─ sortArray()                            60ms│ ← 黄色：JS 执行
│ │  └─ render()                               20ms│
│ └─ GC                                        40ms│ ← GC 开销
└─────────────────────────────────────────────────┘

关键分析点：
1. 红色三角形 = 超过 50ms 的长任务
2. 紫色块过多 = Layout Thrashing（布局抖动）
3. 黄色块过大 = JS 执行效率低
4. 绿色块过大 = 绘制复杂度高
5. GC 频繁 = 内存分配问题
```

| 火焰图特征 | 性能问题 | 优化方向 |
|-----------|---------|----------|
| 大块黄色 | JS 执行慢 | 优化算法、减少计算 |
| 频繁紫色 | Layout 抖动 | 批量读写 DOM |
| 大块绿色 | 绘制开销大 | 减少重绘区域 |
| 频繁 GC | 内存分配密集 | 复用对象 |
| 红色三角 | 长任务阻塞 | 拆分任务、requestIdleCallback |

### 22.7.2 GPU 面板

GPU 面板显示 GPU 相关的活动，包括合成层、纹理上传和 GPU 绘制。对于动画卡顿和滚动性能问题特别有用。

```
GPU 面板关键指标

├─ GPU Raster
│  任务：将绘制指令光栅化为像素
│  过高 → CSS 过于复杂或面积太大
│
├─ GPU Copy
│  任务：纹理上传
│  过高 → 图片太多或太大
│
├─ Upload
│  任务：CPU 到 GPU 的数据传输
│  过高 → 频繁的 canvas 更新
│
├─ Memory
│  任务：GPU 内存使用
│  过高 → 纹理太多
│
└─ Draw
   任务：GPU 绘制调用
   过高 → 合成层数量太多
```

### 22.7.3 Layers 面板

Layers 面板可视化显示页面的合成层结构。每个合成层独立绘制，由 GPU 合成。理解合成层对于优化动画性能至关重要。

```
合成层结构示例

├─ Layer 1: Root（文档根）
│  ├─ Layer 2: Header（position: fixed）
│  │  └─ 原因：固定定位 + will-change: transform
│  ├─ Layer 3: Carousel（will-change: transform）
│  │  └─ 原因：显式提升
│  ├─ Layer 4: Modal（position: fixed + z-index）
│  │  └─ 原因：层叠上下文
│  └─ Layer 5: Video（<video> 元素）
│     └─ 原因：媒体元素自动提升

优化提示：
  - 动画元素应该在独立合成层上
  - 使用 transform 和 opacity 做动画（不触发 Layout）
  - 避免过多合成层（每层消耗 GPU 内存）
  - 使用 will-change 提示浏览器提前创建合成层
```

## 22.8 Sources 面板高级调试

### 22.8.1 Watch Expressions 与 Scope 链

在断点暂停时，Sources 面板的右侧可以查看 Watch Expressions（监视表达式）、Scope（作用域链）和 Call Stack（调用栈）。

```
断点暂停时的调试信息

Watch Expressions（自定义监视）:
  ├─ user.id → 12345
  ├─ cart.total → 299.00
  ├─ document.querySelectorAll('.item').length → 42
  └─ performance.memory.usedJSHeapSize → 15728640

Scope（作用域链，从内到外）:
  ├─ Local（当前函数局部变量）
  │   ├─ this → ShoppingCart {items: Array(3)}
  │   ├─ item → {id: 1, name: 'Book', price: 29.9}
  │   └─ index → 0
  ├─ Closure（闭包变量）
  │   ├─ cart → ShoppingCart {items: Array(3)}
  │   └─ discount → 0.1
  ├─ Script（脚本级变量）
  │   └─ moduleVar → 'config'
  └─ Global（全局变量）
      └─ window → Window

Call Stack（调用栈）:
  ├─ updateItem (cart.js:45)
  ├─ handleQuantityChange (cart.js:78)
  ├─ dispatchEvent (events.js:12)
  ├─ HTMLInputElement.onchange (index.html:23)
  └─ Global code (index.html:1)
```

### 22.8.2 高级断点类型

```javascript
// 1. 条件断点 — 只在条件满足时暂停
// 右键行号 → Add conditional breakpoint
// 场景：循环中只在特定条件下调试
for (let i = 0; i < users.length; i++) {
  processUser(users[i]); // 条件断点: users[i].id === 12345
}

// 2. Log Point — 不暂停只输出日志
// 右键行号 → Add logpoint
// 场景：生产环境调试，不想暂停执行
// 输入: 'Processing user:', users[i].name, 'Index:', i

// 3. DOM 断点 — DOM 变化时暂停
// Elements 面板 → 右键元素 → Break on
//   - Subtree modifications: 子树变化
//   - Attribute modifications: 属性变化
//   - Node removal: 节点移除
// 场景：调试第三方库修改 DOM 的问题

// 4. XHR/Fetch 断点 — 网络请求时暂停
// Sources → XHR/fetch Breakpoints → 添加 URL 模式
// 场景：调试 API 请求时机
// 示例 URL: api/users

// 5. Event Listener 断点 — 事件触发时暂停
// Sources → Event Listener Breakpoints
//   - click, mousemove, keydown...
//   - animationframe, timer...
// 场景：调试事件处理顺序

// 6. Function 断点 — 特定函数调用时暂停
// 在 Console 中执行: debug(functionName)
// 场景：调试第三方库的函数
function suspiciousFunction() {
  // 在 Console 中执行 debug(suspiciousFunction)
  // 每次调用都会暂停
}
```

| 断点类型 | 触发条件 | 典型场景 |
|---------|---------|----------|
| 行断点 | 执行到该行 | 通用调试 |
| 条件断点 | 条件为真 | 循环中特定条件 |
| Log Point | 执行到该行 | 不暂停的日志 |
| DOM 断点 | DOM 变化 | 调试 DOM 操作 |
| XHR 断点 | URL 匹配 | API 调试 |
| Event 断点 | 事件触发 | 事件流调试 |
| Function 断点 | 函数调用 | 第三方库调试 |
| Exception 断点 | 抛出异常 | 错误追踪 |

## 22.9 Network 面板高级用法

### 22.9.1 请求阻断

Network 面板可以阻断特定请求，用于测试错误处理和降级策略。

```
请求阻断操作

1. 打开 Network 面板
2. 右键请求 → Block request URL
3. 在弹出框中编辑阻断规则（支持 * 通配符）
4. 刷新页面，被阻断的请求会显示为 blocked

应用场景：
  - 测试 API 超时时的降级逻辑
  - 测试资源加载失败时的回退
  - 模拟弱网环境（配合 throttling）
```

```javascript
// 也可以通过 DevTools Protocol 编程阻断
// 在 Console 中执行
fetch('https://api.example.com/data')
  .then(r => r.json())
  .catch(e => console.log('请求失败:', e));

// 阻断特定域名
// Network 面板 → 右键 → Block request domain
// 输入: *.example.com
```

### 22.9.2 请求重放

Network 面板可以重放之前的请求，不需要刷新页面。这对于调试 API 特别有用。

```
请求重放操作

方式一：单请求重放
  1. 右键请求 → Replay XHR
  2. 请求会以相同参数重新发送

方式二：编辑重放
  1. 右键请求 → Copy → Copy as fetch
  2. 在 Console 中粘贴并编辑参数
  3. 执行重放

方式三：批量重放
  1. 选中多个请求
  2. 右键 → Replay XHRs
```

### 22.9.3 条件过滤与高级搜索

Network 面板的过滤栏支持丰富的查询语法。

```
过滤语法示例

按属性过滤：
  domain:example.com     — 按域名
  status-code:200        — 按状态码
  method:POST            — 按 HTTP 方法
  mime-type:json         — 按 MIME 类型
  scheme:https           — 按协议

大小过滤：
  larger-than:1M         — 大于 1MB
  larger-than:100k       — 大于 100KB

时间过滤：
  -domain:cdn.com        — 排除域名

组合过滤：
  method:POST status-code:500  — POST 请求且返回 500
  domain:api.example.com larger-than:10k  — API 域名且大于 10KB
```

### 22.9.4 导出 HAR 文件

HAR（HTTP Archive）是记录网络请求的 JSON 格式文件，可以与其他工具共享网络分析数据。

```json
// HAR 文件结构示例（简化）
{
  "log": {
    "version": "1.2",
    "creator": { "name": "DevTools", "version": "120" },
    "entries": [
      {
        "request": {
          "method": "GET",
          "url": "https://api.example.com/users",
          "headers": [...]
        },
        "response": {
          "status": 200,
          "content": { "size": 1024, "mimeType": "application/json" }
        },
        "timings": {
          "dns": 5,
          "connect": 20,
          "ssl": 15,
          "wait": 100,
          "receive": 50
        }
      }
    ]
  }
}
```

| HAR 用途 | 说明 |
|---------|------|
| 团队协作 | 将请求分享给后端排查 |
| 性能对比 | 对比不同版本的网络性能 |
| 回归测试 | 验证 API 调用是否变化 |
| 离线分析 | 在 HAR 分析器中查看 |

## 22.10 Application 面板深入

### 22.10.1 Service Worker 调试

Application 面板的 Service Workers 部分提供了 SW 的完整调试能力。

```
Service Worker 调试功能

├─ Status 显示
│  ├─ Running（运行中）
  ├─ Stopped（已停止）
  └─ Waiting to activate（等待激活）
│
├─ 操作按钮
│  ├─ Unregister — 注销 SW
│  ├─ Push — 模拟推送消息
│  ├─ Sync — 模拟后台同步
│  └─ Update — 强制更新 SW
│
├─ Network 控制
│  ├─ Bypass for network — 网络请求绕过 SW
│  └─ Update on reload — 每次刷新都更新 SW
│
├─ 源映射
│  └─ 点击 SW 链接 → Sources 面板查看源码
│
└─ 日志
   └─ 查看 SW 的 console.log 输出
```

### 22.10.2 IndexedDB 浏览与管理

```javascript
// Application 面板可以可视化浏览 IndexedDB
// 操作步骤：
// 1. Application → Storage → IndexedDB
// 2. 展开数据库 → 对象存储
// 3. 查看所有记录
// 4. 可以手动编辑、删除记录
// 5. 右键 → Clear 对象存储

// 常见调试场景
// 检查数据是否正确写入
const request = indexedDB.open('myDB');
request.onsuccess = (e) => {
  const db = e.target.result;
  const tx = db.transaction('users', 'readonly');
  const store = tx.objectStore('users');
  store.getAll().onsuccess = (e) => {
    console.table(e.target.result);  // 也可以在 Console 中查看
  };
};
```

### 22.10.3 Cache Storage 管理

```javascript
// Cache Storage 是 Service Worker 的缓存机制
// Application 面板可以：
// 1. 查看所有 Cache 对象
// 2. 展开查看缓存的 Request/Response
// 3. 右键删除单个缓存条目
// 4. 右键 → Delete 整个 Cache

// 在 Console 中操作 Cache Storage
const cache = await caches.open('v1');
const keys = await cache.keys();
console.log('缓存条目:', keys.length);

// 手动缓存资源
await cache.add('/api/data');
// 或
const response = new Response(JSON.stringify({ data: 'test' }));
await cache.put('/api/data', response);
```

| Application 面板功能 | 用途 |
|---------------------|------|
| Service Workers | SW 注册、更新、调试 |
| IndexedDB | 数据库浏览、编辑 |
| Cache Storage | SW 缓存管理 |
| Cookies | 查看、编辑、删除 |
| Local Storage | 查看本地存储 |
| Session Storage | 查看会话存储 |
| Storage Quota | 存储配额使用情况 |

## 22.11 Remote Debugging

### 22.11.1 移动端调试

Chrome DevTools 支持远程调试 Android 设备上的 Chrome 页面。通过 USB 连接或 ADB（Android Debug Bridge）实现。

```
移动端调试流程

Android 设备：
1. 设置 → 开发者选项 → USB 调试 → 开启
2. USB 连接电脑
3. 电脑 Chrome → chrome://inspect
4. 设备上弹出授权提示 → 允许
5. 在 chrome://inspect 页面看到设备上的标签页
6. 点击 inspect → 打开 DevTools 调试移动页面

iOS 设备：
1. 需要 Mac + Safari（不支持 Chrome DevTools）
2. iPhone → 设置 → Safari → 高级 → Web 检查器
3. USB 连接 Mac
4. Mac Safari → 开发 → iPhone → 选择页面
```

### 22.11.2 WebView 调试

Android WebView 的调试需要应用开发者开启 WebView 调试模式。

```java
// Android 代码中开启 WebView 调试
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
    WebView.setWebContentsDebuggingEnabled(true);
}
```

```
WebView 调试流程

1. 在 App 中开启 WebView 调试
2. USB 连接电脑
3. 电脑 Chrome → chrome://inspect
4. 在「Devices」列表中找到 WebView 实例
5. 点击 inspect → 调试 WebView 内容

可调试内容：
  ├─ DOM 树和样式
  ├─ JavaScript 控制台
  ├─ 网络请求
  ├─ 性能分析
  └─ 远程截图
```

### 22.11.3 通过 CDP 远程调试

```javascript
// 使用 DevTools Protocol 远程连接 Chrome
const WebSocket = require('ws');

// 启动 Chrome 时开启远程调试
// chrome --remote-debugging-port=9222

// 连接到 CDP
const ws = new WebSocket('ws://localhost:9222/devtools/page/xxx');

ws.on('open', () => {
  // 启用 Page 域
  ws.send(JSON.stringify({ id: 1, method: 'Page.enable' }));
  
  // 导航到页面
  ws.send(JSON.stringify({
    id: 2,
    method: 'Page.navigate',
    params: { url: 'https://example.com' }
  }));
  
  // 截图
  ws.send(JSON.stringify({
    id: 3,
    method: 'Page.captureScreenshot',
    params: { format: 'png' }
  }));
});

ws.on('message', (data) => {
  const message = JSON.parse(data);
  if (message.id === 3) {
    // 收到截图数据
    const base64 = message.result.data;
    require('fs').writeFileSync('screenshot.png', Buffer.from(base64, 'base64'));
  }
});
```

## 22.12 DevTools 协议扩展与自定义工具

### 22.12.1 CDP 域与常用方法

```
CDP 域分类

├─ Page 域 — 页面控制
│  ├─ Page.navigate
│  ├─ Page.reload
│  ├─ Page.captureScreenshot
│  ├─ Page.printToPDF
│  └─ Page.startScreencast
│
├─ DOM 域 — DOM 操作
│  ├─ DOM.getDocument
│  ├─ DOM.querySelector
│  ├─ DOM.setNodeValue
│  └─ DOM.removeNode
│
├─ Runtime 域 — JS 执行
│  ├─ Runtime.evaluate
│  ├─ Runtime.callFunctionOn
│  ├─ Runtime.getProperties
│  └─ Runtime.runScript
│
├─ Network 域 — 网络监控
│  ├─ Network.enable
│  ├─ Network.setBlockedURLs
│  ├─ Network.getResponseBody
│  └─ Network.clearBrowserCache
│
├─ Performance 域 — 性能
│  ├─ Performance.getMetrics
│  ├─ Performance.enable
│  └─ Performance.setTimeDomain
│
├─ Target 域 — 标签页管理
│  ├─ Target.createTarget
│  ├─ Target.closeTarget
│  └─ Target.getTargets
│
├─ Emulation 域 — 设备模拟
│  ├─ Emulation.setDeviceMetricsOverride
│  ├─ Emulation.setCPUThrottlingRate
│  └─ Emulation.setNetworkConditions
│
└─ Debugger 域 — 调试控制
   ├─ Debugger.setBreakpoint
   ├─ Debugger.stepOver
   └─ Debugger.resume
```

### 22.12.2 自定义 DevTools 工具

Chrome DevTools 支持通过扩展或 DevTools Protocol 创建自定义面板和工具。

```javascript
// 创建 DevTools 扩展（需要 Chrome Extension）
// manifest.json
{
  "manifest_version": 3,
  "devtools_page": "devtools.html"
}

// devtools.js
chrome.devtools.panels.create(
  'My Panel',           // 面板名称
  'icon.png',           // 图标
  'panel.html',         // 面板页面
  function(panel) {
    // 面板创建回调
    console.log('自定义面板已创建');
  }
);

// panel.js — 面板逻辑
// 通过 chrome.devtools.inspectedWindow 访问被检查页面
chrome.devtools.inspectedWindow.eval(
  'document.title',
  function(result, isException) {
    console.log('页面标题:', result);
  }
);

// 监听网络请求
chrome.devtools.network.onRequestFinished.addListener(
  function(request) {
    console.log('请求:', request.request.url);
  }
);
```

| 自定义工具类型 | 实现 | 用途 |
|---------------|------|------|
| 自定义面板 | DevTools Extension | 专用调试界面 |
| 自定义侧边栏 | DevTools Extension | 辅助信息展示 |
| CDP 脚本 | Puppeteer/Playwright | 自动化分析 |
| 自定义Auditor | Lighthouse Plugin | 自定义审计规则 |

## 本章核心知识总结

| 工具/面板 | 核心功能 | 调试场景 |
|---------|---------|---------|
| Performance | 火焰图分析 | 渲染瓶颈 |
| Sources | 断点调试 | 代码 bug |
| Memory | 堆快照 | 内存泄漏 |
| Network | 瀑布图 | 网络性能 |
| Lighthouse | 综合审计 | 性能/SEO |
| Console | 高级技巧 | 快速调试 |

觉得有用？收藏起来，下次调试时翻出来看。

你最常用 DevTools 的哪个面板？有什么调试技巧分享？评论区聊聊。

关注怕浪猫，下期我们讲 WebGPU 与前端 AI。系列进度 22/24。

下期预告：第 23 章「WebGPU 与前端 AI」。我们会拆解 WebGPU 的渲染管线、与 WebGL 的对比、以及浏览器内置 AI（Gemini Nano）的使用方式。怕浪猫下期见。

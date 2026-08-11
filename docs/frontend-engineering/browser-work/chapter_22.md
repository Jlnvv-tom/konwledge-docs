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

## 22.13 实战调试工作流

### 22.13.1 性能问题排查完整流程

在实际项目中，性能问题的排查往往需要多个面板配合使用。一个成熟的调试工作流包括发现问题、复现问题、定位根因和验证修复四个阶段。每个阶段都有对应的 DevTools 工具支持。

发现阶段通常从用户反馈或性能监控开始。用户报告页面卡顿，但开发者需要量化这个「卡顿」。此时可以用 Performance 面板录制用户操作，查看是否有超过 50 毫秒的长任务。如果 Lighthouse 的性能评分突然下降，对比不同版本的性能报告可以定位回归点。

复现阶段需要找到可靠的操作路径。在 Performance 面板中开启「CPU 4x slowdown」可以模拟低端设备，更容易复现只在弱设备上出现的问题。Network 面板的 throttling 功能可以模拟慢速网络，检查在资源加载缓慢时的渲染表现。

定位根因是最核心的步骤。火焰图中红色三角形标记的长任务是入口点。展开长任务的调用栈，可以看到具体是哪个函数消耗了最多时间。如果黄色块过大，说明 JavaScript 执行效率低，需要在 Sources 面板中找到对应函数进行优化。如果紫色块过多，说明存在布局抖动，需要批量读取布局属性。如果绿色块过大，说明绘制复杂度高，需要减少重绘区域。

验证修复阶段需要重新录制 Performance 进行对比。在修改前后各录制一次，比较长任务的数量和持续时间。如果使用了 `performance.mark` 和 `performance.measure` 标记关键节点，可以在 Performance 面板中直接对比这些标记的时间变化。

### 22.13.2 内存问题排查完整流程

内存问题的排查比性能问题更复杂，因为内存泄漏往往需要长时间运行才能暴露。一个完整的内存排查流程包括基线建立、泄漏复现、快照比较和引用链分析四个步骤。

基线建立时，需要在一个干净的浏览器环境中打开页面。关闭所有不必要的扩展程序，因为扩展也会影响内存分析。等待页面完全加载后，触发一次 GC（通过 Memory 面板的「Collect garbage」按钮），然后拍摄第一个堆快照作为基线。

泄漏复现阶段需要执行可能触发泄漏的操作。常见的复现模式包括反复路由切换、反复打开关闭弹窗、反复滚动长列表等。每次操作后记录内存使用量，如果内存在操作后持续增长且不回收，基本可以确认存在泄漏。

快照比较是定位泄漏的关键。拍摄操作前后的两个快照，在 Memory 面板中选择「Comparison」视图，对比两个快照之间的差异。按 Delta 列排序，找到新增最多的对象类型。这些对象就是泄漏的候选。

引用链分析用于找到泄漏根因。选中泄漏对象后，在下方的 Retainers 面板中查看引用链。从对象本身向上追溯，直到找到不应该持有引用的代码位置。通常引用链会指向某个全局变量、缓存或事件监听器。

### 22.13.3 网络问题排查完整流程

网络问题的排查需要结合 Network 面板和 Performance 面板。Network 面板提供请求级别的详细信息，Performance 面板提供网络请求与渲染的关联关系。

排查网络问题的第一步是查看瀑布图。瀑布图中请求的位置和长度反映了加载顺序和耗时。理想的状态是关键资源在早期并行加载，非关键资源延后加载。如果发现关键 CSS 在多个 JavaScript 之后加载，可能需要调整资源加载优先级。

第二步是检查请求详情。点击 Network 面板中的请求，查看 Timing 标签页。如果 TTFB（Time To First Byte，首字节时间）过长，可能是服务器响应慢或网络延迟高。如果 Content Download 时间过长，可能是资源太大或网络带宽不足。

第三步是验证缓存策略。在 Network 面板中勾选「Disable cache」可以对比有缓存和无缓存的加载表现。检查响应头中的 `Cache-Control` 和 `ETag` 是否正确设置。带哈希的资源应该使用 `max-age=31536000, immutable`，HTML 应该使用 `no-cache` 或短 `max-age`。

### 22.13.4 DevTools 使用技巧总结

DevTools 的强大之处在于多个面板的协同工作。在 Elements 面板中选中元素后，可以在 Console 中用 `$0` 引用它，直接操作样式或事件。在 Network 面板中右键请求，选择「Reveal in Sources Panel」可以直接跳转到发起该请求的代码行。在 Performance 面板中点击火焰图的某个任务，可以在 Bottom-Up 标签中查看该任务的子任务耗时分布。

Console 面板不仅仅是 `console.log` 的输出窗口。它是一个完整的 JavaScript REPL 环境，可以执行任何页面上下文中的代码。结合 `$`（`document.querySelector`）、`$$`（`document.querySelectorAll`）、`$x`（XPath 查询）等快捷函数，可以快速检查 DOM 状态。`copy()` 函数可以将任意值复制到剪贴板，`inspect()` 函数可以跳转到 Elements 面板中对应元素。

Source Map 是调试压缩代码的关键。在 Sources 面板中开启「Enable JavaScript source maps」后，压缩代码会自动映射到原始源码。如果没有 Source Map，可以通过「Pretty print」按钮格式化压缩代码，虽然不如 Source Map 精确，但至少可以阅读代码结构。

### 22.13.5 条件断点的高级技巧

条件断点是 DevTools 中最被低估的功能之一。合理使用条件断点可以在不修改代码的情况下实现复杂的调试逻辑。条件断点支持任意 JavaScript 表达式，只要表达式返回 `true` 就会暂停执行。

一个常见的使用场景是在循环中调试特定迭代。比如处理一个包含上千个用户的数组，只想查看用户 ID 为 12345 的处理逻辑。如果用 `console.log` 加条件判断，会输出大量日志。而条件断点只需要在处理函数的行上设置 `user.id === 12345`，程序只会在处理目标用户时暂停。

Log Point 是另一个被忽视的功能。它看起来像断点但实际上不会暂停执行，只是在控制台输出指定的表达式。在生产环境中调试时，Log Point 是 `console.log` 的完美替代品——不需要修改代码、不需要重新部署，只需要在 DevTools 中设置即可。调试完成后移除 Log Point，不影响任何代码逻辑。

### 22.13.6 移动端调试实战技巧

移动端调试面临的最大挑战是设备多样性。不同型号的手机、不同版本的操作系统、不同厂商的浏览器定制，都可能导致只在特定设备上出现的问题。Remote Debugging 通过 USB 或 Wi-Fi 连接移动设备，使用桌面版 DevTools 进行调试。

在移动端调试中，触摸事件的调试是一个难点。桌面浏览器无法模拟真实的触摸行为，特别是多点触控和手势识别。通过 Remote Debugging 连接真实设备，可以在 DevTools 中看到触摸事件的完整信息，包括触摸点的坐标、压力和持续时间。

移动端的性能问题通常与设备能力有关。使用 DevTools 的 CPU throttling 功能可以模拟低端设备的 CPU 性能。一般来说，四倍 CPU 减速可以近似模拟中端 Android 设备的 CPU 性能。对于内存限制，可以通过 Chrome 的 `--max-old-space-size` 启动参数模拟不同内存配置。

### 22.13.7 DevTools 在团队协作中的应用

DevTools 不只是个人调试工具，也可以成为团队协作的利器。通过导出 HAR 文件，可以将网络请求的完整信息分享给后端工程师，帮助他们排查 API 问题。通过录制 Performance Profile 并导出为 JSON 文件，可以让其他工程师在自己的 DevTools 中查看火焰图分析结果。

Lighthouse CI 的报告可以集成到持续集成系统中，每次代码提交都生成性能报告。团队成员可以通过查看报告历史趋势来发现性能回归。这种数据驱动的性能管理方式比主观感受更可靠，也更容易在团队中达成共识。

### 22.13.8 常见调试场景与解决方案

在实际开发中，某些调试场景反复出现。总结这些场景和解决方案可以大幅提升调试效率。以下是前端开发中最常见的调试场景。

第一个场景是页面白屏。页面白屏的原因可能是 JavaScript 错误导致渲染失败、CSS 加载阻塞、或者网络请求超时。排查步骤是：先看 Console 面板是否有红色错误。然后看 Network 面板是否有请求失败或超时。最后看 Performance 面板中是否有长任务阻塞了渲染。如果 JavaScript 在解析阶段报错，整个脚本执行会停止，后续的渲染逻辑不会执行，导致白屏。

第二个场景是样式不生效。这通常是 CSS 优先级问题。在 Elements 面板中选中目标元素，查看 Computed 标签页中的计算值。如果与预期不符，在 Styles 标签页中查看所有作用于该元素的规则。被划掉的规则表示被更高优先级的规则覆盖。检查 CSS 选择器优先级、内联样式和 `!important` 声明。Chrome 115 之后支持的 CSS Cascade Layers 也可能影响优先级。

第三个场景是接口请求异常。在 Network 面板中查看请求的状态码、请求头、请求体和响应体。如果状态码是 4xx 或 5xx，检查请求参数是否正确。如果是 CORS 错误，检查服务器是否返回了正确的 CORS 头部。如果是 Cookie 未携带，检查 `credentials` 选项和 `SameSite` 属性。使用「Copy as fetch」功能可以在 Console 中重现请求，方便调试。

第四个场景是动画卡顿。在 Performance 面板中录制动画过程，查看 Main thread 的火焰图。如果看到大量紫色 Layout 块，说明触发了强制布局。检查动画属性是否使用了 `transform` 和 `opacity`。如果看到大量黄色 JavaScript 块，说明动画逻辑在 JavaScript 中执行，应该改用 CSS 动画或 Web Animations API。如果看到频繁的 Composite 块但帧率仍然低，可能是合成层数量过多导致 GPU 负载过高。

### 22.13.9 DevTools 快捷键与工作流优化

熟练使用 DevTools 快捷键可以大幅提升调试效率。以下是高频使用的快捷键。`Cmd+F` 在当前面板中搜索。`Cmd+P` 在 Sources 面板中按文件名搜索。`Cmd+Shift+P` 打开命令菜单，可以执行各种 DevTools 操作。`Cmd+Shift+F` 在所有文件中全局搜索。`Esc` 打开底部 Console 抽屉。`Cmd+]` 和 `Cmd+[` 在面板标签之间切换。

除了快捷键，DevTools 还有很多隐藏功能。在 Console 中输入 `$_` 可以引用上一个表达式的结果。`$0` 到 `$4` 引用最近在 Elements 面板中选中的五个元素。`monitorEvents(document, 'click')` 可以监控指定元素的所有事件。这些功能在日常调试中非常实用，值得熟记。

### 22.13.10 Console 面板深度技巧

Console 面板是前端开发者使用频率最高的 DevTools 面板，但大多数开发者只用了 `console.log`。Console 的能力远不止于此，掌握高级技巧可以大幅提升调试效率。

`console.dir` 和 `console.log` 的区别在于显示方式。`console.log` 将 DOM 元素显示为 HTML 结构，而 `console.dir` 显示对象的属性列表。在调试 DOM 元素的事件监听器或内部属性时，`console.dir` 更有用。`console.dirxml` 则以 XML 树形结构显示元素，适合查看复杂的 DOM 嵌套。

`console.group` 和 `console.groupEnd` 可以将相关日志分组显示，非常适合调试异步流程。比如在调试一个多步骤的表单提交流程时，可以将每个步骤的日志分组，在 Console 中折叠展开，快速定位问题步骤。`console.groupCollapsed` 创建默认折叠的分组，减少日志噪声。

`console.table` 以表格形式显示数组或对象，非常适合查看结构化数据。比如查看用户列表时，`console.table(users)` 会显示每个用户的属性为表格列，一目了然。可以指定只显示特定列：`console.table(users, ['id', 'name'])`。

`console.time` 和 `console.timeEnd` 用于精确测量代码执行时间。虽然 Performance API 提供了更强大的性能测量能力，但在快速调试时 `console.time` 更方便。可以使用标签区分多个计时器：`console.time('fetch')` 和 `console.timeEnd('fetch')`。

### 22.13.11 断点调试进阶技巧

断点调试是定位复杂问题的核武器。除了基本的行断点，DevTools 还提供了多种高级断点类型，可以应对各种调试场景。

XHR 断点在特定网络请求发出时暂停执行。这对于调试第三方 API 调用特别有用。当不确定哪个代码发起了某个 API 请求时，设置一个匹配该 API URL 的 XHR 断点，触发时调用栈会显示完整的发起链路。这在调试大型应用中的网络请求时非常高效。

Event Listener 断点在特定事件触发时暂停。DevTools 可以按事件类型设置断点，包括鼠标事件、键盘事件、计时器事件、动画帧事件等。比如在调试一个按钮点击不响应的问题时，设置 click 事件断点，确认事件是否被触发。如果事件被触发但处理器没有执行，可能是事件被其他元素阻止了传播。

Function 断点通过 `debug()` 函数设置。在 Console 中执行 `debug(myFunction)` 后，每次该函数被调用时都会暂停。这对于调试第三方库的函数特别有用，因为你不需要打开库的源码文件找到函数位置。移除断点使用 `undebug(myFunction)`。

### 22.13.12 移动端调试进阶

移动端调试的特殊之处在于设备资源限制。移动设备的 CPU、内存和网络都远不如桌面设备，很多在桌面上无法复现的问题只在移动设备上出现。Remote Debugging 通过连接真实设备进行调试，是最可靠的移动端调试方式。

在 Chrome 中可以通过 `chrome://inspect` 页面连接 Android 设备。连接后可以看到设备上所有 Chrome 标签页和 WebView 实例。点击对应标签页的「inspect」链接，会打开一个完整的 DevTools 窗口，可以像调试桌面页面一样调试移动页面。

设备模拟器是 Remote Debugging 的补充方案。Chrome DevTools 的 Device Mode 可以模拟不同设备的屏幕尺寸、像素密度、网络速度和 CPU 性能。虽然模拟器不能完全替代真机测试，但在开发阶段可以快速验证响应式布局和性能优化效果。对于触摸事件，模拟器支持模拟基本的触摸和手势，但复杂的多点触控操作仍需要真机测试。

### 22.13.13 Lighthouse 深度使用与自定义审计

Lighthouse 不只是一个性能评分工具，它还提供了自定义审计的能力。通过 Lighthouse Plugin API，开发者可以编写自定义审计规则，检查项目特定的性能和质量标准。比如可以编写一个审计规则检查页面是否使用了指定的 CDN 域名，或者检查所有图片是否都有 alt 属性。

自定义审计的编写需要理解 Lighthouse 的审计模型。每个审计包含一个 `meta` 对象描述审计信息，和一个 `audit` 方法执行实际检查。审计方法返回一个对象，包含评分和详细信息。Lighthouse 会将所有审计结果汇总到报告中。

Lighthouse CI 的配置文件支持复杂的断言逻辑。可以为不同环境设置不同的阈值——开发环境宽松一些，生产环境严格一些。还可以设置预算文件，精确控制每种资源的大小上限。当审计结果不满足断言时，Lighthouse CI 会返回非零退出码，从而阻止 CI 流程继续。

### 22.13.14 DevTools 的实验性功能

Chrome DevTools 持续推出新的实验性功能。在 `chrome://flags` 中可以启用 DevTools 的实验性特性，然后在 DevTools 的设置中开启「Experiments」选项。以下是一些值得关注的实验性功能。

第一个是「Coverage」面板。Coverage 面板可以分析页面加载的 JavaScript 和 CSS 中有多少代码被实际使用。这对于识别和移除未使用的代码非常有用。在加载页面时打开 Coverage 面板开始录制，页面加载完成后停止录制，Coverage 面板会显示每个文件的使用率。使用率低的文件是 Tree Shaking 或代码分割的候选。

第二个是「Changes」面板。Changes 面板显示你在 DevTools 中对源文件所做的所有修改。在 Sources 面板中使用 Workspaces 功能时，你可以直接编辑源文件。Changes 面板以 diff 格式显示所有修改，方便你检查改动是否正确。这个面板对于在 DevTools 中快速调试样式特别有用。

第三个是「Recorder」面板。Recorder 面板可以录制用户在页面上的操作流程，然后回放这些操作。这对于回归测试特别有用——录制一次标准操作流程，然后在每次代码变更后回放，确认核心功能没有回归。Recorder 还支持将录制导出为 Puppeteer 脚本或 WebdriverIO 测试。

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

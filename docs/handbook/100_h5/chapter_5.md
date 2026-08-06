# 第5章：WebView 与 App 集成

Hybrid开发踩了3年坑，我把JS Bridge的原理和离线包方案总结成了这篇。我是怕浪猫，一个在Hybrid开发领域实战多年的前端工程师。上一篇讲了性能优化，这篇进入 Hybrid 开发的核心：WebView 原理、JS Bridge 设计、离线包、安全防护。

## 5.1 WebView 的本质与 iOS/Android 差异

### 什么是 WebView

WebView 是 App 内嵌的浏览器引擎内核，让原生应用可以直接展示 H5 页面。它不是浏览器，但有浏览器的渲染能力。

### iOS vs Android 差异

| 特性 | iOS WKWebView | Android WebView |
|------|--------------|-----------------|
| 内核 | WebKit | Chromium（4.4+） |
| JS引擎 | JavaScriptCore | V8 |
| 缓存机制 | 自定义 URLCache | HTTP Cache + ApplicationCache |
| Cookie管理 | NSHTTPCookieStorage（iOS 11+ 改善） | CookieManager |
| 调试 | Safari Developer | chrome://inspect |
| 多实例 | 支持但开销较大 | 支持且开销较小 |

### 基本创建代码

```swift
// iOS: 创建 WKWebView
import WebKit

let config = WKWebViewConfiguration()
config.preferences.javaScriptEnabled = true
let webView = WKWebView(frame: .zero, configuration: config)
webView.load(URLRequest(url: URL(string: "https://example.com")!))
```

```kotlin
// Android: 创建 WebView
val webView = WebView(context)
webView.settings.javaScriptEnabled = true
webView.settings.domStorageEnabled = true
webView.webViewClient = WebViewClient()
webView.loadUrl("https://example.com")
```

> 理解 WebView 不是浏览器，是内核，才能理解为什么有些 Web API 在 WebView 里不可用。

参考来源：[Apple - WKWebView](https://developer.apple.com/documentation/webkit/wkwebview)、[Android - WebView](https://developer.android.com/reference/android/webkit/WebView)

## 5.2 JS Bridge 的实现原理详解

### Native 调 JS

Native 调用 JS 比较简单，直接执行 JS 代码字符串：

```swift
// iOS: WKWebView
webView.evaluateJavaScript("alert('来自Native')") { result, error in
    print("执行结果:", result ?? "")
}
```

```kotlin
// Android: evaluateJavascript（4.4+）
webView.evaluateJavascript("alert('来自Native')") { result ->
    println("执行结果: $result")
}
```

### JS 调 Native 的三种方式

```
方案1: URL Scheme 拦截
  JS: window.location = 'myapp://action?data=xxx'
  Native: 拦截 shouldStartLoadWith / shouldOverrideUrlLoading

方案2: prompt 拦截（Android专用）
  JS: window.prompt('bridge:action', JSON.stringify(params))
  Native: JsPromptResult 处理

方案3: 注入对象
  Android: addJavascriptInterface
  iOS: WKScriptMessageHandler
```

### 三种方案对比

| 方案 | 性能 | 安全性 | 兼容性 | iOS/Android |
|------|------|--------|--------|-------------|
| URL Scheme | 低（多次跳转） | 中 | 全部 | 双端 |
| prompt 拦截 | 中 | 中 | Android | 仅Android |
| 注入对象 | 高 | 高 | iOS 8+/Android 4.2+ | 双端 |

### 注入对象实现

```kotlin
// Android: addJavascriptInterface
class JsBridge {
    @JavascriptInterface
    fun callNative(action: String, params: String): String {
        // 处理JS调用
        return handleAction(action, params)
    }
}

webView.addJavascriptInterface(JsBridge(), "NativeBridge")
```

```swift
// iOS: WKScriptMessageHandler
class ViewController: UIViewController, WKScriptMessageHandler {
    func userContentController(_ controller: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        if message.name == "NativeBridge" {
            let body = message.body as! [String: Any]
            let action = body["action"] as! String
            handleAction(action, body["params"])
        }
    }
}

// 注册
let contentController = WKUserContentController()
contentController.add(self, name: "NativeBridge")
```

```javascript
// JS 端调用
window.NativeBridge.callNative('share', JSON.stringify({
  title: '怕浪猫',
  content: 'Hybrid开发指南'
}));
```

> JS Bridge 不是黑盒，理解了三种通讯方式，你就理解了所有 Hybrid 框架的底层逻辑。

参考来源：[Android - addJavascriptInterface](https://developer.android.com/reference/android/webkit/WebView#addJavascriptInterface(java.lang.Object,%20java.lang.String))、[Apple - WKScriptMessageHandler](https://developer.apple.com/documentation/webkit/wkscriptmessagehandler)

## 5.3 通用 JS Bridge 的架构设计

### 设计目标

一个通用的 JS Bridge 需要：
- 统一 API 签名
- 异步回调管理
- Promise 化封装
- 事件订阅/发布
- 版本兼容与降级

### 架构图

```
JS 层
┌──────────────────────────┐
│  Bridge.call('share', {}) │  <- 业务调用
│  Bridge.on('backPressed') │  <- 事件监听
├──────────────────────────┤
│  回调队列管理（callbackId） │  <- 内部管理
│  Promise 封装层           │
├──────────────────────────┤
│  传输层（postMessage/URL） │  <- 与Native通讯
└──────────────────────────┘
          |
          v
Native 层（iOS/Android）
┌──────────────────────────┐
│  接收消息 -> 解析 action   │
│  路由到对应 Native 处理器  │
│  处理完成 -> 回调 JS       │
└──────────────────────────┘
```

### 完整实现

```javascript
class JsBridge {
  constructor() {
    this.callbackId = 0;
    this.callbacks = {};
    this.eventListeners = {};
    this._setupMessageListener();
  }

  // 调用 Native
  call(action, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.callbackId;
      this.callbacks[id] = { resolve, reject };

      const message = {
        action,
        params,
        callbackId: id,
        timestamp: Date.now()
      };

      // 发送给 Native（根据平台选择方案）
      this._sendToNative(message);

      // 超时处理
      setTimeout(() => {
        if (this.callbacks[id]) {
          this.callbacks[id].reject(new Error('Bridge call timeout'));
          delete this.callbacks[id];
        }
      }, 10000);
    });
  }

  // 事件订阅
  on(event, handler) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(handler);
  }

  // 事件取消
  off(event, handler) {
    const listeners = this.eventListeners[event];
    if (listeners) {
      const idx = listeners.indexOf(handler);
      if (idx > -1) listeners.splice(idx, 1);
    }
  }

  // Native 回调 JS
  _invokeCallback(callbackId, result, error) {
    const callback = this.callbacks[callbackId];
    if (!callback) return;
    if (error) {
      callback.reject(error);
    } else {
      callback.resolve(result);
    }
    delete this.callbacks[callbackId];
  }

  // Native 事件推送到 JS
  _dispatchEvent(event, data) {
    const listeners = this.eventListeners[event];
    if (listeners) {
      listeners.forEach(handler => handler(data));
    }
  }

  // 发送消息到 Native
  _sendToNative(message) {
    // iOS: WKScriptMessageHandler
    if (window.webkit?.messageHandlers?.NativeBridge) {
      window.webkit.messageHandlers.NativeBridge.postMessage(message);
    }
    // Android: addJavascriptInterface
    else if (window.NativeBridge?.callNative) {
      window.NativeBridge.callNative(message.action, JSON.stringify(message));
    }
    // Fallback: URL Scheme
    else {
      const url = `bridge://${encodeURIComponent(JSON.stringify(message))}`;
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = url;
      document.body.appendChild(iframe);
      setTimeout(() => document.body.removeChild(iframe), 100);
    }
  }

  // 监听 Native 回调
  _setupMessageListener() {
    window.__bridgeCallback__ = (callbackId, result, error) => {
      this._invokeCallback(callbackId, result, error);
    };
    window.__bridgeEvent__ = (event, data) => {
      this._dispatchEvent(event, data);
    };
  }
}

// 全局单例
const bridge = new JsBridge();
export default bridge;
```

### 使用示例

```javascript
// 调用 Native 分享
bridge.call('share', { title: '怕浪猫', content: 'Hybrid指南' })
  .then(result => console.log('分享成功'))
  .catch(err => console.error('分享失败', err));

// 监听 Native 返回键事件
bridge.on('backPressed', (data) => {
  if (canGoBack()) {
    history.back();
  } else {
    bridge.call('closeWebView');
  }
});
```

> 一个好的 Bridge 设计，让业务层不关心传输方式，只关心 action 和 result。

## 5.4 WebView 中 Cookie 与 LocalStorage 的 Native 同步

### iOS Cookie 问题

iOS 的 WKWebView 在 iOS 11 之前，Cookie 不会自动同步到 NSHTTPCookieStorage，导致登录态丢失。

```swift
// iOS 11+: 使用 WKHTTPCookieStore 统一管理
let cookieStore = webView.configuration.websiteDataStore.httpCookieStore

// 注入 Cookie
let cookie = HTTPCookie(properties: [
    .domain: ".example.com",
    .path: "/",
    .name: "token",
    .value: "abc123",
    .secure: "TRUE"
])!
cookieStore.setCookie(cookie)
```

### Android Cookie 同步

```kotlin
// Android: CookieManager
val cookieManager = CookieManager.getInstance()
cookieManager.setAcceptCookie(true)

// 注入 Cookie
cookieManager.setCookie("https://example.com", "token=abc123; path=/; secure; httpOnly")

// 同步到 WebView（异步API）
cookieManager.flush()

// API 21 以下需要同步调用
// CookieSyncManager.getInstance().sync()
```

### 登录态打通方案

```
方案1: Native 注入 Token 到请求头
  Native: WebView 拦截请求 -> 添加 Authorization Header
  优点: Token 不暴露在 H5 中
  缺点: 仅拦截 WebView 内请求

方案2: JS Bridge 传递 Token
  H5: bridge.call('getToken') -> Native 返回 Token
  H5: 存入 LocalStorage，后续请求带上
  优点: H5 可自行管理
  缺点: Token 暴露在 JS 中
```

```javascript
// 方案2: JS Bridge 获取 Token
async function ensureToken() {
  let token = localStorage.getItem('auth_token');
  if (!token) {
    token = await bridge.call('getToken');
    localStorage.setItem('auth_token', token);
  }
  return token;
}

// 请求拦截器注入
axios.interceptors.request.use(async config => {
  const token = await ensureToken();
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

> 登录态打通是 Hybrid 开发的第一个坑，踩过的人都知道 iOS Cookie 有多坑。

参考来源：[Apple - WKHTTPCookieStore](https://developer.apple.com/documentation/webkit/wkhttpcookiestore)、[Android - CookieManager](https://developer.android.com/reference/android/webkit/CookieManager)

## 5.5 WebView 白屏与加载失败的排查和兜底

### 排查链路

```
白屏 -> 网络层
  ├── DNS 解析失败 -> 检查域名
  ├── TLS 握手失败 -> 检查证书
  └── 资源 404/500 -> 检查服务端

-> JS 层
  ├── JS 执行错误 -> 检查控制台
  ├── 大 bundle 阻塞 -> Code Splitting
  └── 白屏时间长 -> SSR/骨架屏

-> WebView 层
  ├── 内核崩溃 -> 捕获 crash
  ├── 内存不足 -> 检查泄漏
  └── 渲染异常 -> 检查 CSS 兼容
```

### 错误监听与兜底

```kotlin
// Android: 错误监听
webView.webViewClient = object : WebViewClient() {
    override fun onReceivedError(view: WebView?, request: WebResourceRequest?,
                                  error: WebResourceError?) {
        // 加载失败页
        view?.loadUrl("file:///android_asset/error.html")
    }

    override fun onReceivedHttpError(view: WebView?, request: WebResourceRequest?,
                                      errorResponse: WebResourceResponse?) {
        val statusCode = errorResponse?.statusCode
        if (statusCode == 404 || statusCode == 500) {
            view?.loadUrl("file:///android_asset/error.html")
        }
    }
}
```

```swift
// iOS: 错误监听
func webView(_ webView: WKWebView, didFail navigation: WKNavigation!,
             withError error: Error) {
    let errorHtml = """
    <html><body style="text-align:center;padding-top:40%">
    <h2>页面加载失败</h2>
    <button onclick="location.reload()">重试</button>
    </body></html>
    """
    webView.loadHTMLString(errorHtml, baseURL: nil)
}
```

### 远程调试

```kotlin
// Android: 开启远程调试
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
    WebView.setWebContentsDebuggingEnabled(true)
}
// 电脑 Chrome 打开 chrome://inspect 连接调试
```

iOS: Safari -> 开发 -> 模拟器/设备 -> 选择页面

> 白屏排查的关键是"分层定位"：先排网络，再排 JS，最后排 WebView。

## 5.6 提升 WebView 首屏加载速度的策略

### 预热 WebView 实例池

```kotlin
// Android: WebView 复用池
class WebViewPool(private val context: Context) {
    private val pool = mutableListOf<WebView>()

    fun prepare(count: Int) {
        for (i in 0 until count) {
            val webView = WebView(context)
            webView.settings.javaScriptEnabled = true
            webView.settings.domStorageEnabled = true
            // 预加载空白页，初始化内核
            webView.loadData("<html></html>", "text/html", "UTF-8")
            pool.add(webView)
        }
    }

    fun acquire(): WebView {
        return if (pool.isNotEmpty()) {
            pool.removeAt(0)
        } else {
            WebView(context)
        }
    }

    fun release(webView: WebView) {
        // 清理状态后放回池中
        webView.stopLoading()
        webView.clearHistory()
        pool.add(webView)
    }
}
```

### 优化策略对比

| 策略 | 效果 | 成本 | 适用场景 |
|------|------|------|----------|
| WebView 预热 | 节省 200-500ms 初始化时间 | 中（内存占用） | 高频打开 WebView 的 App |
| 离线包 | 节省 80%+ 网络时间 | 高（需离线包系统） | 核心页面固定 |
| SSR/预渲染 | 节省 JS 执行时间 | 中（需服务端支持） | 内容驱动页面 |
| DNS 预解析 | 节省 50-100ms | 低 | 第三方资源多 |
| 关键CSS内联 | 减少阻塞渲染 | 低 | 首屏样式少 |

> WebView 首屏速度 = 初始化时间 + 网络时间 + 渲染时间，三个维度都要优化。

## 5.7 离线包方案的设计与实现

### 完整流程

```
1. 打包：H5 资源打包成 zip（含 index.html/js/css/图片）
2. 版本管理：服务端记录版本号和资源地址
3. 增量更新：bsdiff 生成差分包，客户端只下载差异部分
4. CDN 分发：离线包上传 CDN
5. 客户端下载：App 启动时检查更新 -> 下载/解压/校验
6. 请求拦截：WebView 加载 URL 时映射到本地文件
7. 更新策略：全量/增量、静默更新、用户触发
```

### 请求拦截

```kotlin
// Android: 拦截请求返回本地资源
webView.webViewClient = object : WebViewClient() {
    override fun shouldInterceptRequest(view: WebView?,
                                         request: WebResourceRequest?): WebResourceResponse? {
        val url = request?.url?.toString() ?: return null

        // 检查本地离线包是否有该资源
        val localPath = offlineResourceManager.resolve(url)
        if (localPath != null) {
            val file = File(localPath)
            if (file.exists()) {
                val mimeType = getMimeType(localPath)
                return WebResourceResponse(mimeType, "UTF-8", FileInputStream(file))
            }
        }
        return null // 回退到网络请求
    }
}
```

### 增量更新

```kotlin
// 客户端检查更新
fun checkUpdate() {
    api.getOfflinePackageVersion("h5-app")
        .subscribe { serverVersion ->
            val localVersion = preferences.getInt("h5_version", 0)
            if (serverVersion.version > localVersion) {
                if (localVersion > 0) {
                    // 增量更新
                    downloadPatch(serverVersion.patchUrl)
                } else {
                    // 全量下载
                    downloadFullPackage(serverVersion.fullUrl)
                }
            }
        }
}
```

> 离线包是 Hybrid 性能优化的终极武器，把网络时间从秒级降到毫秒级。

参考来源：[Android - shouldInterceptRequest](https://developer.android.com/reference/android/webkit/WebViewClient#shouldInterceptRequest(android.webkit.WebView,%20android.webkit.WebResourceRequest))

## 5.8 WebView 的安全风险与防护

### 安全风险清单

| 风险 | 原因 | 防护措施 |
|------|------|----------|
| RCE（Remote Code Execution） | Android 4.2 以下 addJavascriptInterface 漏洞 | 最低版本 4.2+ 或使用 JS Bridge |
| 文件域访问 | file:// 可访问本地文件 | setAllowFileAccess(false) |
| URL 白名单绕过 | 未校验加载的 URL | 白名单校验 |
| JS Bridge 来源伪造 | 任意页面调用 Bridge | origin 校验 |
| iframe 劫持 | 恶意 iframe 嵌入 | X-Frame-Options |
| HTTPS 中间人 | 未校验证书 | 证书校验 |

### 安全配置

```kotlin
// Android 安全配置
val settings = webView.settings
settings.javaScriptEnabled = true
settings.allowFileAccess = false           // 禁止 file:// 访问本地文件
settings.allowFileAccessFromFileURLs = false
settings.allowUniversalAccessFromFileURLs = false
settings.setSupportZoom(false)

// URL 白名单校验
val allowedDomains = listOf("example.com", "cdn.example.com")

webView.webViewClient = object : WebViewClient() {
    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
        val host = request?.url?.host ?: return true
        if (!allowedDomains.any { host.endsWith(it) }) {
            return true // 拦截非白名单 URL
        }
        return false
    }
}
```

```javascript
// JS Bridge 来源校验（Native 侧实现）
// iOS 示例：检查 message 的 origin
func userContentController(_ controller: WKUserContentController,
                           didReceive message: WKScriptMessage) {
    // 检查来源
    guard let origin = message.frameInfo.request.url?.host,
          allowedDomains.contains(origin) else {
        return // 拒绝非白名单域名的调用
    }
    // 处理消息
    handleMessage(message)
}
```

> 安全防护的核心是"最小权限"：不该访问的不给访问，不该调用的不让调用。

## 5.9 WebView 中调试 H5 页面的方法

### Android 远程调试

```kotlin
// 开启调试模式（仅在 Debug 包中开启）
if (BuildConfig.DEBUG) {
    WebView.setWebContentsDebuggingEnabled(true)
}
// 电脑 Chrome 打开 chrome://inspect -> 连接设备 -> 调试
```

### iOS 调试

```
1. 模拟器/真机连接 Mac
2. Safari -> 开发 -> 模拟器/设备名 -> 选择页面
3. 可使用 Console / Elements / Network / Timeline
```

### vConsole 嵌入式调试

```javascript
// 线上环境排查问题（仅在需要时加载）
if (location.search.includes('debug=true')) {
  const script = document.createElement('script');
  script.src = 'https://unpkg.com/vconsole/dist/vconsole.min.js';
  script.onload = () => {
    new window.VConsole();
  };
  document.body.appendChild(script);
}
```

### eruda 调试面板

```javascript
// eruda 比 vConsole 功能更全（含 Network/Resources/Features）
if (location.search.includes('debug=true')) {
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/eruda';
  script.onload = () => eruda.init();
  document.body.appendChild(script);
}
```

> 线上问题不能靠猜，vConsole 和 eruda 是移动端调试的两把利器。

参考来源：[Chrome Developers - Remote Debugging](https://developer.chrome.com/docs/devtools/remote-debugging/)、[vConsole GitHub](https://github.com/Tencent/vConsole)

## 5.10 App 内 H5 与原生的手势冲突处理

### 常见冲突场景

- 侧滑返回手势与 H5 横向滚动冲突
- WebView 滚动与 Native ScrollView 嵌套滚动冲突
- 双指缩放与 H5 手势冲突

### 解决方案

```css
/* CSS: touch-action 声明手势行为 */
.horizontal-scroll {
  /* 允许水平滚动，禁止其他手势 */
  touch-action: pan-x;
}

.no-zoom {
  /* 禁止双指缩放 */
  touch-action: pan-x pan-y;
}
```

```javascript
// JS Bridge: 通知 Native 禁用/启用手势
// 用户在 H5 横向滚动区域时禁用侧滑返回
element.addEventListener('touchstart', () => {
  bridge.call('setSwipeBackEnabled', { enabled: false });
});

element.addEventListener('touchend', () => {
  bridge.call('setSwipeBackEnabled', { enabled: true });
});
```

```kotlin
// Android: Native 侧判断触摸区域
webView.setOnTouchListener { _, event ->
    if (event.action == MotionEvent.ACTION_DOWN) {
        val x = event.x.toInt()
        // 左侧边缘 20px 内不触发侧滑返回
        if (x < 20) {
            // 允许 Native 侧滑返回
        } else {
            // 由 WebView 处理手势
        }
    }
    false
}
```

> 手势冲突的本质是"谁优先处理"——用 touch-action 声明意图，用 Bridge 动态切换。

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| WebView 本质与差异 | Hybrid 基础 | 高 |
| JS Bridge 原理 | 通讯机制理解 | 高 |
| 通用 Bridge 设计 | 架构设计能力 | 高 |
| Cookie/LocalStorage 同步 | 登录态打通 | 中高 |
| 白屏排查与兜底 | 问题定位能力 | 中高 |
| WebView 首屏加速 | 性能优化 | 中高 |
| 离线包方案 | 架构设计 | 中 |
| 安全风险与防护 | 安全意识 | 中 |
| 调试方法 | 实战能力 | 中 |
| 手势冲突处理 | 交互细节 | 低 |

这篇 Hybrid 架构指南，收藏起来做技术选型时直接参考。你的 Hybrid 方案用的什么 Bridge？评论区交流。关注怕浪猫，下期讲小程序与 H5 的交互。系列进度 5/10。

下一篇拆解小程序双线程模型、web-view 组件、小程序与 H5 通讯机制、setData 性能优化。

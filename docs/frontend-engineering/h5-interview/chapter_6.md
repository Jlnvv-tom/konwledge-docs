---
sidebar_position: 6
---

# 第6章：小程序与 H5 的交互

小程序和H5混合开发，90%的人卡在通讯机制上。这篇把双线程模型和通讯链路讲透。我是怕浪猫，一个在小程序和H5之间反复横跳的前端工程师。

## 6.1 小程序基本架构与 H5 的本质区别

### 双线程模型

小程序采用双线程架构：渲染层和逻辑层分离。

```
渲染层（WebView）        逻辑层（JSCore/V8）
  ├── 页面A WebView         ├── JS 业务逻辑
  ├── 页面B WebView         ├── 数据处理
  └── 页面C WebView         └── API 调用
        |                         |
        |--- Native 中转通讯 -----|
        |                         |
        v                         v
     渲染 DOM                   执行 JS
```

逻辑层不能直接操作 DOM，必须通过 `setData` 将数据传到渲染层。这与 H5 单线程模型（JS 和 DOM 在同一线程）有本质区别。

### 与 H5 的关键差异

| 特性 | H5 | 小程序 |
|------|-----|--------|
| 线程模型 | 单线程 | 双线程 |
| DOM 操作 | 直接操作 | 不支持 |
| BOM API | 完整支持 | 受限 |
| 网络请求 | 任意域名 | 需配置白名单 |
| 组件系统 | Web Components | 小程序组件 |
| 样式 | 完整 CSS | 子集（不支持部分选择器） |
| 调试 | DevTools | 微信开发者工具 |

> 双线程不是为了性能，是为了安全——逻辑层拿不到 DOM，就无法被注入恶意脚本篡改页面。

参考来源：[微信开放文档 - 小程序架构](https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/)

## 6.2 小程序 web-view 组件的使用与限制

### 基本使用

```html
<!-- 小程序页面中嵌入 H5 -->
<web-view src="https://example.com/h5-page"></web-view>
```

web-view 组件会覆盖整个页面，无法在其上叠加原生组件（cover-view 有限支持）。

### 能力边界

| 能力 | 支持情况 |
|------|----------|
| 嵌入 H5 页面 | 支持 |
| 业务域名配置 | 必须（后台配置） |
| 叠加原生组件 | 不支持（cover-view 有限） |
| 小程序内导航 | 不支持 navigateBack（需 H5 内处理） |
| 扫码 | 需通过 JS Bridge 调用小程序能力 |
| 支付 | 需跳回小程序调起支付 |

### 业务域名配置

```
小程序后台 -> 开发管理 -> 开发设置 -> 业务域名
  - 添加域名（需 HTTPS）
  - 下载校验文件放到域名根目录
  - 每个域名最多 20 个
```

> web-view 是小程序和 H5 之间的桥梁，但这座桥是单行道——H5 能做的事情受限于小程序的沙箱。

## 6.3 小程序与 H5 之间的通讯机制

### 通讯方向

```
小程序 -> H5：
  方式1: URL 参数传递（src 动态更新）
  方式2: 通过服务端中转

H5 -> 小程序：
  方式1: wx.miniProgram.postMessage(data)
  方式2: wx.miniProgram.navigateTo/redirectTo 跳转
  方式3: 通过服务端中转
```

### H5 调小程序

```javascript
// H5 页面中调用小程序 API（需引入微信 JSSDK）
// HTML 中引入：<script src="https://res.wx.qq.com/open/js/jweixin-1.3.2.js"></script>

// 跳转到小程序页面
wx.miniProgram.navigateTo({
  url: '/pages/detail/index?id=123'
});

// 传递消息给小程序（仅在特定时机触发）
wx.miniProgram.postMessage({
  data: {
    action: 'login',
    token: 'abc123'
  }
});

// 获取小程序环境信息
wx.miniProgram.getEnv(function(res) {
  console.log(res.miniprogram); // true
});
```

### 小程序接收消息

```html
<!-- 小程序页面 -->
<web-view src="{{webviewSrc}}" bind:message="onMessage"></web-view>
```

```javascript
Page({
  onMessage(e) {
    // 注意：postMessage 的数据不是实时接收的
    // 只在以下时机触发：后退、组件销毁、分享、复制链接
    console.log('收到H5消息:', e.detail.data);
    const messages = e.detail.data; // 数组，可能积攒多条
    messages.forEach(msg => {
      if (msg.action === 'login') {
        this.handleLogin(msg.token);
      }
    });
  }
});
```

### 实时双向通讯的困难

postMessage 不是实时的，只在特定时机触发。如果需要实时通讯，方案是：

```javascript
// 方案：服务端 WebSocket 中转
// H5 -> WebSocket -> 服务端 -> WebSocket -> 小程序
// 小程序使用 wx.connectSocket

// H5 端
const ws = new WebSocket('wss://api.example.com/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({ from: 'h5', action: 'update', data: { id: 1 } }));
};

// 小程序端
const wsTask = wx.connectSocket({ url: 'wss://api.example.com/ws' });
wsTask.onMessage((res) => {
  const msg = JSON.parse(res.data);
  if (msg.from === 'h5') {
    this.setData({ receivedData: msg.data });
  }
});
```

> 小程序和 H5 之间的通讯就像两个人隔着玻璃说话——能看到对方，但声音传不过去，得找中间人传话。

参考来源：[微信开放文档 - web-view组件](https://developers.weixin.qq.com/miniprogram/dev/component/web-view.html)

## 6.4 小程序性能优化策略

### 优化清单

| 策略 | 效果 | 实现难度 |
|------|------|----------|
| 分包加载 | 主包缩小，启动快 | 中 |
| 独立分包 | 不依赖主包，更快 | 中 |
| 分包预下载 | 用户无感加载 | 低 |
| setData 优化 | 减少通讯开销 | 低 |
| 图片懒加载 | 减少初始加载 | 低 |
| wx.nextTick | 批量更新 | 低 |
| 减少节点数 | 渲染更快 | 中 |

### 分包加载配置

```json
// app.json
{
  "pages": [
    "pages/index/index",
    "pages/home/home"
  ],
  "subpackages": [
    {
      "root": "packageA",
      "pages": [
        "pages/detail/detail",
        "pages/list/list"
      ]
    },
    {
      "root": "packageB",
      "pages": [
        "pages/order/order"
      ]
    }
  ],
  "preloadRule": {
    "pages/index/index": {
      "network": "all",
      "packages": ["packageA"]
    }
  }
}
```

### wx.nextTick 批量更新

```javascript
// 避免：多次 setData
this.setData({ count: 1 });
this.setData({ name: '怕浪猫' });
this.setData({ list: [1, 2, 3] });
// 三次跨线程通讯，性能差

// 推荐：合并为一次
this.setData({
  count: 1,
  name: '怕浪猫',
  list: [1, 2, 3]
});

// 或使用 wx.nextTick
wx.nextTick(() => {
  this.setData({ count: 1, name: '怕浪猫', list: [1, 2, 3] });
});
```

> 小程序性能优化的核心就是减少跨线程通讯——每次 setData 都是有成本的。

## 6.5 setData 的性能陷阱与优化

### 性能陷阱原理

```
逻辑层                    渲染层
  |                         |
  | --- setData(data) ----> |
  |    数据序列化            |
  |    跨线程传输            |
  |                    数据反序列化
  |                    重新渲染 DOM
  |                         |
```

每次 setData 都会：序列化数据 -> 跨线程传输 -> 反序列化 -> 重渲染。数据量越大、频率越高，性能越差。

### 优化对比

```javascript
// 反面示例1：传整个列表
this.setData({
  list: this.data.list  // 1000条数据全部传过去
});

// 正面示例1：只传变化的部分
this.setData({
  ['list[0].name']: '怕浪猫'  // 只传变化的字段
});

// 反面示例2：频繁 setData（滚动事件中）
onPageScroll(e) {
  this.setData({ scrollTop: e.scrollTop }); // 每帧都传
}

// 正面示例2：节流
onPageScroll: throttle(function(e) {
  this.setData({ scrollTop: e.scrollTop });
}, 100),

// 反面示例3：传不需要的数据
this.setData({
  userInfo: this.data.userInfo,  // 未变化的也传
  newCount: 5
});

// 正面示例3：只传变化的
this.setData({
  newCount: 5
});
```

> setData 不是免费的，每一次调用都是一次跨线程的序列化传输。

参考来源：[微信开放文档 - setData 性能优化](https://developers.weixin.qq.com/miniprogram/dev/framework/performance/)

## 6.6 小程序登录流程与 H5 登录态打通

### 小程序登录流程

```
1. 前端: wx.login() -> 获得 code
2. 前端: 将 code 发送给自己的服务端
3. 服务端: 用 code + appid + secret 请求微信接口 -> 获得 openid + session_key
4. 服务端: 生成自定义登录态（Token）返回给前端
5. 前端: 存储 Token，后续请求带上
```

```javascript
// 小程序登录
async function login() {
  // 1. 获取 code
  const { code } = await wx.login();

  // 2. 发送 code 到服务端
  const res = await request({
    url: 'https://api.example.com/auth/wx-login',
    method: 'POST',
    data: { code }
  });

  // 3. 存储 Token
  wx.setStorageSync('token', res.token);
  return res.token;
}

// 请求拦截
function request(options) {
  const token = wx.getStorageSync('token');
  return new Promise((resolve, reject) => {
    wx.request({
      ...options,
      header: {
        ...options.header,
        'Authorization': `Bearer ${token}`
      },
      success: (res) => resolve(res.data),
      fail: reject
    });
  });
}
```

### web-view 登录态注入

```javascript
// 小程序: 将 Token 通过 URL 传给 H5
const token = wx.getStorageSync('token');
const encodedToken = encodeURIComponent(token);
this.setData({
  webviewSrc: `https://example.com/h5-page?token=${encodedToken}`
});

// H5 端: 从 URL 获取 Token
const params = new URLSearchParams(location.search);
const token = params.get('token');
if (token) {
  localStorage.setItem('auth_token', token);
}

// 安全增强: Token 使用短期有效的一次性票据
// 小程序: bridge.call('getOneTimeTicket') -> 服务端生成短期票据
// H5: 用票据换取正式 Token
```

> 登录态打通是小程序和 H5 混合开发中最常见的需求，URL 传 Token 是最简单但需注意安全。

## 6.7 小程序条件渲染与列表渲染性能优化

### wx:key 的重要性

```html
<!-- 错误：用 index 作为 key -->
<view wx:for="{{list}}" wx:key="index">
  {{item.name}}
</view>
<!-- 问题：列表变化时，所有项都可能重新渲染 -->

<!-- 正确：用唯一稳定的值作为 key -->
<view wx:for="{{list}}" wx:key="id">
  {{item.name}}
</view>
```

### hidden vs wx:if

```html
<!-- wx:if：条件为false时，节点不渲染 -->
<view wx:if="{{showPanel}}">面板内容</view>
<!-- 适用：切换不频繁 -->

<!-- hidden：始终渲染，通过CSS控制显示 -->
<view hidden="{{!showPanel}}">面板内容</view>
<!-- 适用：频繁切换 -->
```

| 属性 | 渲染开销 | 切换开销 | 适用场景 |
|------|----------|----------|----------|
| wx:if | 低（不渲染） | 高（重新创建） | 条件少变 |
| hidden | 高（始终渲染） | 低（CSS切换） | 频繁切换 |

### 虚拟列表

```html
<!-- 使用 scroll-view + 手动虚拟列表 -->
<scroll-view
  scroll-y
  style="height: 600rpx"
  bindscroll="onScroll"
>
  <view style="height: {{totalHeight}}px; position: relative">
    <view
      wx:for="{{visibleList}}"
      wx:key="id"
      style="position: absolute; top: {{item.offsetTop}}px; height: {{itemHeight}}px"
    >
      {{item.content}}
    </view>
  </view>
</scroll-view>
```

```javascript
Page({
  data: {
    allList: [],      // 全部数据
    visibleList: [],  // 可见数据
    totalHeight: 0,
    itemHeight: 60,
    startIndex: 0,
    visibleCount: 10
  },

  onScroll(e) {
    const scrollTop = e.detail.scrollTop;
    const startIndex = Math.floor(scrollTop / this.data.itemHeight);
    if (startIndex !== this.data.startIndex) {
      this.updateVisible(startIndex);
    }
  },

  updateVisible(startIndex) {
    const endIndex = startIndex + this.data.visibleCount;
    const visibleList = this.data.allList
      .slice(startIndex, endIndex)
      .map((item, i) => ({
        ...item,
        offsetTop: (startIndex + i) * this.data.itemHeight
      }));
    this.setData({
      startIndex,
      visibleList,
      totalHeight: this.data.allList.length * this.data.itemHeight
    });
  }
});
```

> wx:key 用唯一值、hidden vs wx:if 按频率选、大列表用虚拟列表——这三条覆盖了 90% 的小程序渲染优化。

## 6.8 小程序自定义组件与 H5 Web Components 对比

### 对比表

| 特性 | 小程序 Component | Web Components |
|------|-----------------|----------------|
| 定义方式 | Component({}) | customElements.define() |
| 生命周期 | created/attached/ready/detached | connectedCallback/disconnectedCallback |
| 样式隔离 | styleIsolation | Shadow DOM |
| 数据流 | properties + setData | attributes + properties |
| 事件触发 | triggerEvent | dispatchEvent |
| 插槽 | slot | slot |
| 复用性 | 小程序内 | 跨框架 |

### 代码对比

```javascript
// 小程序自定义组件
Component({
  properties: {
    title: { type: String, value: '默认标题' }
  },
  data: {
    count: 0
  },
  methods: {
    onTap() {
      this.setData({ count: this.data.count + 1 });
      this.triggerEvent('change', { count: this.data.count });
    }
  },
  lifetimes: {
    attached() {
      console.log('组件挂载');
    },
    detached() {
      console.log('组件卸载');
    }
  }
});
```

```javascript
// Web Components
class MyComponent extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>
        :host { display: block; }
        .title { font-weight: bold; }
      </style>
      <div class="title">${this.getAttribute('title') || '默认标题'}</div>
      <button>点击</button>
    `;
    this.count = 0;
    shadow.querySelector('button').addEventListener('click', () => {
      this.count++;
      this.dispatchEvent(new CustomEvent('change', { detail: { count: this.count } }));
    });
  }
  connectedCallback() {
    console.log('组件挂载');
  }
  disconnectedCallback() {
    console.log('组件卸载');
  }
}
customElements.define('my-component', MyComponent);
```

> 小程序组件的设计思路类似 Vue，Web Components 更底层——理解了其中一种，另一种就很好理解。

## 6.9 小程序与 H5 的技术选型决策

### 选型流程

```
需求分析
  |
  ├── 需要原生体验/入口/扫码？-> 小程序原生
  ├── 需要外部分享/快速迭代/跨平台？-> H5
  ├── 需要嵌入第三方页面？-> H5 web-view
  └── 活动营销页/高频变更？-> H5
```

### 对比

| 维度 | 小程序原生 | H5 |
|------|-----------|-----|
| 用户体验 | 原生流畅 | 依赖 WebView |
| 开发效率 | 中（需小程序框架） | 高（Web技术栈） |
| 迭代速度 | 需审核（1-7天） | 即时发布 |
| 入口能力 | 扫码/搜索/分享/附近 | 仅链接 |
| 跨平台 | 仅微信生态 | 所有浏览器 |
| 性能 | 双线程，较好 | 取决于 WebView |
| 用户授权 | 便捷（微信授权） | 需额外流程 |

### 混合策略

```javascript
// 常见策略：核心路径用小程序，活动页用 H5
// 小程序原生页面：
//   - 首页、商品详情、支付、个人中心
// H5 web-view 页面：
//   - 营销活动、协议文档、第三方内容

// 小程序跳 H5
wx.navigateTo({
  url: `/pages/webview/index?src=${encodeURIComponent(h5Url)}`
});

// H5 跳回小程序
wx.miniProgram.navigateBack({ delta: 1 });
// 或跳转到指定页面
wx.miniProgram.redirectTo({ url: '/pages/result/index' });
```

> 技术选型不是非此即彼，而是"在合适的场景用合适的技术"。

## 6.10 小程序分包加载与预下载策略

### 分包限制

- 主包 <= 2MB
- 所有分包总和 <= 20MB
- 单个分包 <= 2MB

### 分包配置

```json
{
  "pages": [
    "pages/index/index",
    "pages/profile/profile"
  ],
  "subpackages": [
    {
      "root": "packageA",
      "pages": ["pages/detail/detail"]
    },
    {
      "root": "packageB",
      "pages": ["pages/order/order"]
    },
    {
      "root": "packageActivity",
      "pages": ["pages/promotion/promotion"],
      "independent": true
    }
  ],
  "preloadRule": {
    "pages/index/index": {
      "network": "wifi",
      "packages": ["packageA"]
    },
    "pages/detail/detail": {
      "network": "all",
      "packages": ["packageB"]
    }
  }
}
```

### 独立分包

独立分包不依赖主包，可以独立运行。适用于活动页等不需要主包逻辑的场景：

```javascript
// 独立分包内，App 不存在时的处理
const app = getApp() || { globalData: {} };
// 不依赖主包的 App 实例
```

### 预下载策略

```json
{
  "preloadRule": {
    "pages/index/index": {
      "network": "wifi",
      "packages": ["packageA", "packageB"]
    }
  }
}
```

`network: "wifi"` 表示仅在 WiFi 环境下预下载，避免消耗用户流量。

> 分包的核心是"按需加载"，预下载的核心是"提前加载"——两者配合让用户无感等待。

参考来源：[微信开放文档 - 分包加载](https://developers.weixin.qq.com/miniprogram/dev/framework/subpackages.html)

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| 双线程模型 | 小程序架构理解 | 高 |
| web-view 组件 | H5嵌入能力 | 中高 |
| 通讯机制 | 跨端数据传递 | 高 |
| 性能优化 | 小程序调优 | 中高 |
| setData 优化 | 性能关键点 | 高 |
| 登录态打通 | 认证体系 | 中高 |
| 渲染优化 | 列表性能 | 中 |
| 组件对比 | 技术理解 | 低 |
| 技术选型 | 架构决策 | 中 |
| 分包加载 | 包体积管理 | 中 |

这篇小程序与H5交互指南，收藏起来开发时直接查。你的小程序和H5是怎么打通登录态的？评论区交流。关注怕浪猫，下期讲 iframe 与跨域通讯。系列进度 6/10。

下一篇拆解 postMessage 安全、iframe 性能、第三方 Cookie 限制、跨域通讯全方案。

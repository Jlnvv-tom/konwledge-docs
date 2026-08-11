---
sidebar_position: 9
---

# 第9章：微前端架构

微前端不是银弹，但用对了能让100人团队的开发效率翻倍。这10个问题覆盖微前端架构的核心选型、沙箱原理、样式隔离、通讯机制。我是怕浪猫，一个主导过微前端架构落地的工程师。

## 9.1 微前端的核心概念与适用场景

### 什么是微前端

微前端（Micro Frontends）是一种架构风格，将大型前端应用拆分为多个独立开发、独立部署的小应用，每个应用可以由不同团队使用不同技术栈开发。

```
主应用（Container）
┌─────────────────────────────────┐
│  Header / Nav / Footer          │
├──────────┬──────────────────────┤
│          │                      │
│ 子应用A  │  子应用B             │
│ (React)  │  (Vue)               │
│          │                      │
├──────────┴──────────────────────┤
│  子应用C (Angular)              │
└─────────────────────────────────┘
```

### 适用场景

| 场景 | 是否适合微前端 | 原因 |
|------|--------------|------|
| 大型企业后台（多团队） | 适合 | 团队独立开发部署 |
| 中台系统整合 | 适合 | 多系统集成 |
| 技术栈迁移 | 适合 | 新老系统共存 |
| 小型项目 | 不适合 | 过度设计 |
| 单团队项目 | 不适合 | 增加复杂度无收益 |
| 高性能要求场景 | 慎用 | 沙箱有性能开销 |

### 核心价值

- 独立部署：子应用独立发布，不影响主应用
- 技术栈无关：子应用可用 React/Vue/Angular
- 增量升级：老系统逐步迁移，不需要推倒重来
- 团队自治：各团队独立开发，互不阻塞

> 微前端的本质不是技术，是组织架构——康威定律说系统结构反映组织结构，微前端让技术架构适配团队结构。

参考来源：[Micro Frontends - Martin Fowler](https://martinfowler.com/articles/micro-frontends.html)

## 9.2 微前端五大方案对比

### 方案总览

| 方案 | 原理 | 隔离性 | 性能 | 复杂度 | 代表框架 |
|------|------|--------|------|--------|----------|
| Nginx 路由分发 | 不同路径代理到不同应用 | 完全隔离 | 好 | 低 | Nginx |
| iframe 嵌入 | iframe 加载子应用 | 完全隔离 | 差 | 低 | 无 |
| Web Components | 自定义元素封装子应用 | 中 | 好 | 中 | 无 |
| Module Federation | Webpack 5 模块共享 | 弱 | 好 | 中 | Webpack 5 |
| JS 沙箱 + 样式隔离 | 运行时沙箱 | 中 | 中 | 高 | qiankun |

### 方案详解

**Nginx 路由分发**：最简单的微前端，每个子应用独立部署，Nginx 按路径分发。缺点是切换应用会整页刷新。

**iframe 嵌入**：天然隔离，但性能差、通讯复杂、用户体验差。

**Module Federation**：Webpack 5 原生支持，模块级共享，性能好但要求统一构建工具。

**qiankun**：基于 single-spa，JS 沙箱 + 样式隔离，最流行的微前端框架。

### 选型决策

```
需要完全隔离？-> iframe / Nginx 分发
统一 Webpack 5？-> Module Federation
需要 JS 沙箱 + 灵活技术栈？-> qiankun
需要原生标准？-> Web Components
```

> 没有最好的微前端方案，只有最适合团队和业务场景的方案。

## 9.3 qiankun 的核心原理与使用

### 加载流程

```
1. 主应用注册子应用（registerMicroApps）
2. 路由匹配 -> 激活子应用
3. fetch 子应用 HTML -> 解析 script/style
4. 创建沙箱环境 -> 执行子应用 JS
5. 挂载子应用到容器
6. 路由切换 -> 卸载旧子应用 -> 加载新子应用
```

### 主应用配置

```javascript
import { registerMicroApps, start } from 'qiankun';

// 注册子应用
registerMicroApps([
  {
    name: 'react-app',
    entry: '//localhost:7100',
    container: '#sub-app-container',
    activeRule: '/react',
    props: {
      token: 'abc123',
      onGlobalStateChange: handleStateChange
    }
  },
  {
    name: 'vue-app',
    entry: '//localhost:7101',
    container: '#sub-app-container',
    activeRule: '/vue'
  }
]);

// 启动
start({
  prefetch: true,        // 预加载
  sandbox: {
    strictStyleIsolation: false,  // Shadow DOM 样式隔离
    experimentalStyleIsolation: true  // 实验性样式隔离
  }
});
```

### 子应用配置

```javascript
// 子应用入口（React 示例）
let instance = null;

function render({ container } = {}) {
  const root = container || document.getElementById('root');
  instance = ReactDOM.createRoot(root);
  instance.render(<App />);
}

// 生命周期
export async function bootstrap() {
  console.log('子应用启动');
}

export async function mount(props) {
  console.log('子应用挂载', props);
  render(props);
}

export async function unmount(props) {
  console.log('子应用卸载');
  instance.unmount();
  instance = null;
}

// 非微前端环境独立运行
if (!window.__POWERED_BY_QIANKUN__) {
  render();
}
```

### 子应用 webpack 配置

```javascript
// webpack.config.js
module.exports = {
  output: {
    library: 'react-app',
    libraryTarget: 'umd',
    jsonpFunction: `webpackJsonp_react_app`
  },
  devServer: {
    headers: {
      'Access-Control-Allow-Origin': '*'  // 允许跨域加载
    }
  }
};
```

> qiankun 的核心做了三件事：加载子应用资源、隔离 JS 执行环境、隔离 CSS 样式。

参考来源：[qiankun 官方文档](https://qiankun.umijs.org/)

## 9.4 JS 沙箱的实现原理

### 代理沙箱（ProxySandbox）

qiankun 的 ProxySandbox 通过 Proxy 代理 window 对象，为每个子应用创建独立的 fakeWindow：

```javascript
class ProxySandbox {
  constructor() {
    this.fakeWindow = {};  // 子应用专属的 window
    this.active = false;
    this.proxy = new Proxy(this.fakeWindow, {
      get: (target, key) => {
        // 优先从 fakeWindow 取
        if (target.hasOwnProperty(key)) {
          return target[key];
        }
        // 否则从真实 window 取
        const value = window[key];
        if (typeof value === 'function') {
          // 绑定 this 到 window
          return value.bind(window);
        }
        return value;
      },
      set: (target, key, value) => {
        if (!this.active) return false;
        target[key] = value;  // 写入 fakeWindow，不污染真实 window
        return true;
      },
      has: (target, key) => {
        return true;  // 让 with 语句生效
      }
    });
  }

  active() {
    this.active = true;
  }

  inactive() {
    this.active = false;
  }
}
```

### 快照沙箱（SnapshotSandbox）

在不支持 Proxy 的环境（IE）中使用快照沙箱：

```javascript
class SnapshotSandbox {
  constructor() {
    this.snapshot = {};
    this.modifyMap = {};
    this.active = false;
  }

  active() {
    // 激活：拍快照
    this.snapshot = {};
    for (const key in window) {
      this.snapshot[key] = window[key];
    }
    // 恢复之前的修改
    Object.keys(this.modifyMap).forEach(key => {
      window[key] = this.modifyMap[key];
    });
    this.active = true;
  }

  inactive() {
    // 失活：记录修改并恢复
    this.modifyMap = {};
    for (const key in window) {
      if (window[key] !== this.snapshot[key]) {
        this.modifyMap[key] = window[key];  // 记录修改
        window[key] = this.snapshot[key];   // 恢复
      }
    }
    this.active = false;
  }
}
```

### 两种沙箱对比

| 特性 | ProxySandbox | SnapshotSandbox |
|------|-------------|-----------------|
| 隔离方式 | 代理 fakeWindow | 快照 + 恢复 |
| 多实例 | 支持 | 不支持 |
| 性能 | 好 | 中（遍历 window） |
| 兼容性 | IE 不支持 Proxy | 全部 |

> ProxySandbox 是多实例微前端的基石——每个子应用有独立的 fakeWindow，互不干扰。

## 9.5 CSS 样式隔离方案

### 三种方案对比

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| Shadow DOM | 浏览器原生隔离 | 完全隔离 | 兼容性、弹窗问题 |
| CSS Scoped | 添加属性选择器前缀 | 简单 | 动态样式可能遗漏 |
| CSS Modules | 编译时哈希类名 | 无冲突 | 需构建工具支持 |

### Shadow DOM 隔离

```javascript
// qiankun 的 strictStyleIsolation 使用 Shadow DOM
container.attachShadow({ mode: 'open' });
// 子应用挂载到 Shadow DOM 内
// 样式完全隔离，不影响外部
```

Shadow DOM 的问题：
- 弹窗组件（Modal/Popover）挂载到 body 时，样式不生效
- 第三方库可能不兼容 Shadow DOM
- 全局事件监听可能异常

### CSS Scoped（实验性隔离）

```javascript
// qiankun 的 experimentalStyleIsolation
// 自动为子应用所有 CSS 规则添加前缀
// 原始：.title { color: red; }
// 转换：div[data-qiankun="react-app"] .title { color: red; }
```

### 工程化方案：CSS Modules + 前缀

```css
/* 子应用统一添加命名空间前缀 */
.react-app-header { ... }
.react-app-sidebar { ... }
```

```javascript
// webpack CSS Modules
module.exports = {
  module: {
    rules: [{
      test: /\.css$/,
      use: [{
        loader: 'css-loader',
        options: {
          modules: {
            localIdentName: '[name]__[local]--[hash:base64:5]'
          }
        }
      }]
    }]
  }
};
```

> 样式隔离没有完美方案，Shadow DOM 最彻底但兼容性差，CSS Scoped 最实用但有边界情况。

## 9.6 微前端应用间的通讯机制

### 方案一：全局状态（initGlobalState）

```javascript
// 主应用
import { initGlobalState } from 'qiankun';

const actions = initGlobalState({
  user: null,
  theme: 'light'
});

// 主应用监听变化
actions.onGlobalStateChange((state, prev) => {
  console.log('全局状态变化:', state);
});

// 主应用修改状态
actions.setGlobalState({ user: { name: '怕浪猫' } });

// 子应用接收
export function mount(props) {
  props.onGlobalStateChange((state, prev) => {
    console.log('收到主应用状态:', state);
  });
  props.setGlobalState({ theme: 'dark' });  // 子应用也可修改
}
```

### 方案二：CustomEvent 自定义事件

```javascript
// 主应用派发事件
window.dispatchEvent(new CustomEvent('micro-app-event', {
  detail: { type: 'user-updated', data: { id: 1 } }
}));

// 子应用监听
window.addEventListener('micro-app-event', (e) => {
  console.log('收到事件:', e.detail);
});
```

### 方案三：Props 传递

```javascript
// 主应用注册时传递 props
registerMicroApps([{
  name: 'react-app',
  entry: '//localhost:7100',
  container: '#container',
  activeRule: '/react',
  props: {
    token: 'abc123',
    apiBase: 'https://api.example.com',
    onNavigate: (path) => history.push(path)
  }
}]);

// 子应用接收
export function mount(props) {
  const { token, apiBase, onNavigate } = props;
  // 使用传递的数据
}
```

### 方案对比

| 方案 | 实时性 | 耦合度 | 复杂度 | 适用场景 |
|------|--------|--------|--------|----------|
| 全局状态 | 高 | 中 | 中 | 共享用户/主题等状态 |
| CustomEvent | 高 | 低 | 低 | 一次性事件通知 |
| Props 传递 | 低 | 高 | 低 | 初始化配置 |

> 微前端通讯的核心原则是"松耦合"——子应用不应直接依赖主应用的内部实现，通过约定好的接口通讯。

## 9.7 Module Federation 详解

### 基本概念

Module Federation（模块联邦）是 Webpack 5 的原生功能，允许多个独立构建的 Webpack 应用共享模块：

```
Host（宿主应用）          Remote（远程应用）
  - 引入远程模块  <-----  - 暴露模块
  - 提供共享依赖  ----->  - 消费共享依赖
```

### 配置示例

```javascript
// 远程应用 webpack.config.js（暴露模块）
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'remoteApp',
      filename: 'remoteEntry.js',
      exposes: {
        './Button': './src/components/Button',
        './utils': './src/utils'
      },
      shared: {
        react: { singleton: true },
        'react-dom': { singleton: true }
      }
    })
  ]
};
```

```javascript
// 宿主应用 webpack.config.js（消费模块）
new ModuleFederationPlugin({
  name: 'hostApp',
  remotes: {
    remoteApp: 'remoteApp@https://remote.example.com/remoteEntry.js'
  },
  shared: {
    react: { singleton: true },
    'react-dom': { singleton: true }
  }
})
```

```javascript
// 宿主应用中异步加载远程模块
const RemoteButton = React.lazy(() => import('remoteApp/Button'));

function App() {
  return (
    <Suspense fallback={<div>加载中...</div>}>
      <RemoteButton onClick={() => console.log('clicked')}>远程按钮</RemoteButton>
    </Suspense>
  );
}
```

### Module Federation vs qiankun

| 特性 | Module Federation | qiankun |
|------|-------------------|---------|
| 隔离级别 | 模块级 | 应用级 |
| 共享依赖 | 原生支持 | 需手动处理 |
| 技术栈 | 需统一 Webpack 5 | 不限 |
| 沙箱 | 无 | Proxy 沙箱 |
| 样式隔离 | 无 | 有 |
| 适用场景 | 同技术栈模块共享 | 异构系统集成 |

> Module Federation 适合"同技术栈模块共享"，qiankun 适合"异构系统集成"。

参考来源：[Webpack - Module Federation](https://webpack.js.org/concepts/module-federation/)

## 9.8 微前端的公共依赖管理

### 问题

多个子应用可能依赖相同的库（如 React、Vue、lodash），如果各自打包会导致：
- 包体积重复
- 内存中多份实例
- 版本冲突

### 共享方案

**方案一：externals + CDN**

```javascript
// 所有子应用 webpack 配置
module.exports = {
  externals: {
    react: 'React',
    'react-dom': 'ReactDOM'
  }
};
// HTML 中通过 CDN 引入公共库
```

**方案二：Module Federation shared**

```javascript
new ModuleFederationPlugin({
  shared: {
    react: {
      singleton: true,      // 全局单例
      requiredVersion: '^18.0.0',
      eager: false          // 异步加载
    }
  }
})
```

**方案三：主应用注入**

```javascript
// 主应用加载公共库，挂载到 window
window.React = require('react');
window.ReactDOM = require('react-dom');

// 子应用 externals 配置
externals: {
  react: 'React',
  'react-dom': 'ReactDOM'
}
```

### 版本兼容策略

```javascript
// shared 配置版本协商
shared: {
  react: {
    singleton: true,
    requiredVersion: '^18.0.0',  // 要求版本
    fallback: false  // 版本不匹配时不 fallback
  }
}
// 如果子应用用了 React 17，而主应用是 React 18：
// singleton: true -> 共用主应用的 React 18
// singleton: false -> 各自加载自己的版本
```

> 公共依赖管理的核心是"能共享就共享，不能共享就隔离"——共享省资源，隔离保安全。

## 9.9 微前端的路由管理

### 路由模式

```
主应用路由
  /react/*  -> 子应用 React App
  /vue/*    -> 子应用 Vue App
  /angular/* -> 子应用 Angular App
```

### qiankun 路由配置

```javascript
// 主应用
registerMicroApps([
  {
    name: 'react-app',
    entry: '//localhost:7100',
    container: '#sub-container',
    activeRule: location => location.pathname.startsWith('/react')
  }
]);

// 子应用路由 base
// React Router
<BrowserRouter basename={window.__POWERED_BY_QIANKUN__ ? '/react' : '/'}>
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/detail/:id" element={<Detail />} />
  </Routes>
</BrowserRouter>
```

### 路由冲突避免

```javascript
// 子应用路由加前缀，避免与主应用冲突
const BASE_NAME = window.__POWERED_BY_QIANKUN__ ? '/react' : '';

// Vue Router
const router = createRouter({
  history: createWebHistory(BASE_NAME),
  routes: [
    { path: '/', component: Home },
    { path: '/list', component: List }
  ]
});
```

### 页面跳转

```javascript
// 子应用 -> 主应用
props.onNavigate('/dashboard');  // 通过 props 传递的跳转方法

// 主应用 -> 子应用
history.push('/react/detail/123');

// 子应用 -> 子应用
props.onNavigate('/vue/list');  // 跳转到另一个子应用
```

> 微前端路由管理的核心是"路径前缀约定 + basename 配置"。

## 9.10 微前端的部署与DevOps

### 独立部署架构

```
CDN
├── /main-app/          主应用
│   ├── index.html
│   └── assets/
├── /react-app/         子应用A
│   ├── index.html
│   └── assets/
└── /vue-app/           子应用B
    ├── index.html
    └── assets/
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name app.example.com;

    # 主应用
    location / {
        root /usr/share/nginx/html/main-app;
        try_files $uri $uri/ /index.html;
    }

    # 子应用资源（允许跨域）
    location /react-app/ {
        root /usr/share/nginx/html;
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods 'GET, OPTIONS';
    }

    location /vue-app/ {
        root /usr/share/nginx/html;
        add_header Access-Control-Allow-Origin *;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### CI/CD 流程

```yaml
# .gitlab-ci.yml（子应用独立流水线）
stages:
  - build
  - deploy

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  script:
    - aws s3 sync dist/ s3://cdn.example.com/react-app/
    - aws cloudfront create-invalidation --paths /react-app/*
  only:
    - main
```

### 版本管理

```javascript
// 子应用入口带版本号
registerMicroApps([{
  name: 'react-app',
  entry: '//cdn.example.com/react-app/v1.2.3/index.html',
  // 或动态获取最新版本
  entry: () => fetchLatestVersion('react-app').then(v =>
    `//cdn.example.com/react-app/${v}/index.html`
  )
}]);
```

> 微前端的部署核心是"子应用独立部署 + CDN 静态资源 + 跨域允许加载"。

## 本章总结

| 知识点 | 核心能力 | 面试重要度 |
|--------|----------|------------|
| 微前端概念与场景 | 架构认知 | 高 |
| 五大方案对比 | 技术选型 | 高 |
| qiankun 原理与使用 | 框架实践 | 高 |
| JS 沙箱原理 | 隔离机制 | 高 |
| CSS 样式隔离 | 样式管理 | 中高 |
| 通讯机制 | 跨应用数据流 | 中高 |
| Module Federation | Webpack 5 共享 | 中 |
| 公共依赖管理 | 依赖优化 | 中 |
| 路由管理 | 路由设计 | 中 |
| 部署与 DevOps | 工程化 | 中 |

这篇微前端架构全方案，收藏起来做架构设计时直接参考。你的微前端用的什么方案？评论区交流。关注怕浪猫，下期讲用户体验与业务价值，系列完结。系列进度 9/10。

下一篇也是最后一篇，拆解用户体验度量、H5 可访问性、性能与业务的关系、技术债务管理。

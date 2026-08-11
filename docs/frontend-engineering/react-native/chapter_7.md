---
sidebar_position: 7
---

# 第7章 RN网络请求、文件上传与WebSocket通信

你的RN项目是不是每个页面都在手写fetch，错误处理全靠try-catch层层嵌套，接口超时了用户看到的是一片白屏，文件上传连个进度条都没有，WebSocket断线了压根不知道？

我见过太多RN项目在网络层的技术债：一个页面五个接口调用，写了五套不同的错误处理逻辑；图片上传不做压缩，10MB的原图直接往服务器怼；WebSocket断了不重连，用户以为APP卡死了疯狂下拉刷新。这些问题看着是"功能没做"，本质是网络层没有统一设计。移动端网络环境和Web端完全不同——弱网、断网、网络切换、后台唤醒，每一个都是生产事故的导火索。

我是怕浪猫，一个在RN（React Native）网络请求坑里交过不少学费的开发者。前面几章我们搞定了组件化、导航和状态管理，这章是整个系列最硬核的实战章节之一——网络请求、文件上传与WebSocket（WebSocket Protocol，一种全双工通信协议）通信。这章内容如果你跟着敲一遍，至少能少踩半年坑。

> 网络层是APP的神经系统。神经搭错了，页面再漂亮也是一具空壳。

## 7.1 RN网络请求方案选型与对比

### 7.1.1 Fetch原生请求优缺点分析

RN内置了Fetch API（Fetch Application Programming Interface），这是基于Promise设计的现代HTTP（HyperText Transfer Protocol，超文本传输协议）请求方案。开箱即用，不需要安装任何第三方依赖，写一个最简单的GET请求只需要一行代码：

```js
// 最基础的Fetch GET请求
const res = await fetch('https://api.example.com/users?page=1');
const data = await res.json();
console.log(data);
```

看起来很美好，但在企业级项目中，原生Fetch的缺陷会快速暴露。先看一张Fetch的请求处理流程图：

```
┌─────────────────────────────────────────────────────┐
│               Fetch请求处理流程                       │
├─────────────────────────────────────────────────────┤
│  fetch(url, options)                                │
│      │                                              │
│      ├──→ 1. 构造请求（手动拼headers/body）          │
│      │                                              │
│      ├──→ 2. 发送请求（无超时控制）                   │
│      │                                              │
│      ├──→ 3. 响应处理（需手动判断res.ok）             │
│      │      ├──→ res.ok === false → 非Promise reject │
│      │      └──→ res.ok === true  → 手动res.json()   │
│      │                                              │
│      └──→ 4. 错误处理（仅网络错误才reject）           │
└─────────────────────────────────────────────────────┘
```

Fetch的核心痛点可以总结为以下几点，这些都是在真实项目中反复遇到过的问题：

第一，HTTP状态码4xx、5xx不会触发reject，只有网络层错误才会触发Promise的reject。这意味着你每个请求都要手动判断`res.ok`属性，忘了判断就是白屏Bug——业务层拿着错误响应当正常数据用，直接崩溃。第二，没有内置的请求超时机制，弱网下一个请求可以卡住整个页面的渲染，用户只能盯着白屏等待。第三，没有请求拦截和响应拦截能力，公共参数比如Token、版本号、设备信息只能每个请求手动拼接，代码重复度极高。第四，不支持请求取消，AbortController在旧版本RN中兼容性堪忧，快速切换页面时旧请求的数据可能覆盖新请求的数据。第五，错误信息不够结构化，catch块里拿到的Error对象没有HTTP状态码、没有响应体，排查问题全靠打日志。

```js
// Fetch的典型坑：4xx状态码不报错
const res = await fetch('https://api.example.com/users/999');
// 用户不存在，服务器返回404，但这里不会进入catch
const data = await res.json();
// 如果忘了判断res.ok，data可能是个错误对象
// 业务层拿着错误对象当正常数据用，直接崩溃
```

> Fetch是工具不是方案。用Fetch直接写业务，就像用螺丝刀造汽车——工具没错，用法错了。

### 7.1.2 Axios企业级请求库优势

Axios是目前最成熟的HTTP客户端库，在Web前端和RN跨端开发中都有着极其广泛的使用。相比于原生Fetch，它提供了完整的请求拦截器和响应拦截器机制、内置的超时控制配置、请求取消能力、自动JSON数据转换、自动错误状态码处理等企业级特性，可以说是为生产环境而生的请求方案。在我经历过的多个RN项目中，Axios几乎是网络层的标配选择。

Axios与Fetch的核心能力对比可以从多个维度展开。在超时控制方面，Fetch需要手动封装AbortController来实现，而Axios只需配置一个timeout参数即可。在拦截器方面，Fetch完全不支持请求和响应拦截，所有公共参数和错误处理都需要在每个调用处手动编写，而Axios提供了完善的拦截器机制。在错误处理方面，Fetch对HTTP状态码4xx和5xx不会触发Promise的reject，只有网络层错误才会，这导致开发者很容易漏判错误状态码，而Axios会自动对所有非2xx状态码触发reject。在请求取消方面，两者都支持AbortController，但Axios还保留了CancelToken的兼容写法。在数据转换方面，Fetch需要手动调用res.json()方法解析响应体，而Axios会自动完成JSON解析。在TypeScript类型支持方面，Axios自带完善的类型定义，泛型支持非常友好，而Fetch的类型定义相对较弱。

| 能力维度 | Fetch | Axios |
|---------|-------|-------|
| 超时控制 | 需手动封装AbortController | 内置timeout配置 |
| 请求拦截 | 不支持 | 支持 |
| 响应拦截 | 不支持 | 支持 |
| 错误处理 | 4xx/5xx不reject | 自动reject非2xx状态 |
| 请求取消 | AbortController | AbortController + CancelToken |
| 数据转换 | 手动res.json() | 自动转换JSON |
| 重试机制 | 需手动实现 | 可通过拦截器实现 |
| TypeScript支持 | 一般 | 优秀 |

安装Axios非常简单，只需要一行npm命令即可完成安装。如果你的项目使用了TypeScript，不需要额外安装类型定义包，因为Axios从版本0.18开始就自带了完善的TypeScript类型定义文件，开箱即用，泛型支持也非常友好。安装完成后直接在代码中import即可使用，没有任何额外的配置成本。

```bash
# 安装Axios
npm install axios

# 如果使用TypeScript
npm install axios
# Axios自带类型定义，无需额外安装@types/axios
```

Axios最核心的优势在于拦截器机制，这也是它相比Fetch最大的竞争力所在。通过拦截器，我们可以在请求发出前统一注入Token认证信息、在响应返回后统一处理错误码和业务逻辑，业务层只需要关注数据本身的使用，不需要在每个API调用处重复编写认证、错误处理等样板代码。这种关注点分离的设计让代码的可维护性大幅提升，也是企业级项目选择Axios而非原生Fetch的根本原因。

```js
import axios from 'axios';

// 创建实例，配置基础参数
const http = axios.create({
  baseURL: 'https://api.example.com',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'X-Platform': 'rn',
  },
});

// 请求拦截器：自动注入Token
http.interceptors.request.use((config) => {
  const token = global.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 跳转登录页
    }
    return Promise.reject(error);
  }
);
```

### 7.1.3 移动端网络核心痛点总结

移动端网络环境和桌面端有本质区别。在桌面端，用户要么有网要么没网，网络质量相对稳定。但在移动端，网络状态是一个动态变化的连续谱——从满格4G到微弱信号，从WiFi切换到蜂窝，从电梯里的断网到地下室的弱网，每一种状态都需要考虑。

```
┌──────────────────────────────────────────────────────┐
│              移动端网络环境分布                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  强网(100%) ──→ 中等(60%) ──→ 弱网(20%) ──→ 断网(0%)│
│      │              │              │             │   │
│   正常请求       请求变慢      请求超时      请求失败   │
│   即时响应       需要loading   需要重试      需要兜底   │
│                                                      │
│  WiFi ←→ 4G ←→ 3G ←→ 无信号  （网络切换场景）        │
│      │                                         │     │
│      └──→ 切换瞬间：TCP连接断开，请求丢失           │
│           需要自动重连和状态恢复                      │
└──────────────────────────────────────────────────────┘
```

我在实际项目中遇到的移动端网络痛点主要有五类，每一类都对应着真实的生产事故场景：

一是弱网超时问题。用户在地铁里打开APP，请求发出去了但服务器响应慢，十五秒后超时，用户早就退出了页面。如果是在支付场景中，用户不确定订单状态，可能会重复提交，导致重复下单。二是网络切换问题。用户从WiFi切换到蜂窝网络时，底层的TCP连接会断开，正在进行的请求直接失败，如果没有自动重连机制，用户需要手动刷新页面。三是后台唤醒问题。APP从后台切回前台时，之前建立的网络连接可能已经失效，TCP连接已经被运营商的NAT设备回收，但应用层不知道，发出去的请求石沉大海。四是并发冲突问题。用户快速切换页面时，旧页面的请求还没回来，新页面的请求已经发出，由于异步回调的顺序不确定，旧请求返回的数据可能覆盖新请求的数据，导致页面展示错误内容。五是离线场景问题。用户在无网环境下操作，如果没有本地缓存兜底，页面就是一片空白，用户完全不知道之前看过什么内容，体验极差。

> 移动端网络开发的第一准则：永远不要假设网络是稳定的。你的代码要在"网络随时可能断"的前提下设计。

### 7.1.4 跨端网络请求适配难点

RN虽然是跨端框架，但iOS和Android的网络底层存在差异。iOS默认要求所有HTTP请求走HTTPS（HTTP Secure，安全超文本传输协议），否则需要在Info.plist中配置ATS（App Transport Security，应用传输安全）例外。Android 9.0以上版本也有类似的明文HTTP限制。

```js
// iOS Info.plist 配置允许HTTP明文传输
// android/app/src/main/AndroidManifest.xml 配置
{
  "info": {
    "NSAppTransportSecurity": {
      "NSAllowsArbitraryLoads": true
    }
  }
}
```

除了平台差异带来的适配难点，还有几个跨端网络问题经常在项目中出现。第一是Cookie管理问题，RN默认不带Cookie管理器，需要手动安装`@react-native-community/cookies`库来处理Cookie的存储和发送。第二是SSL证书校验问题，在开发环境下使用自签名证书时，iOS和Android的处理方式不同，需要分别配置。第三是自定义DNS解析问题，有些企业内网应用需要指定DNS服务器，这在RN中需要原生模块支持。第四是WebView与原生页面的Cookie共享问题，用户在WebView中登录后，原生页面的网络请求需要携带相同的Cookie，反之亦然，这个共享机制在RN中配置起来比较复杂。这些跨端适配问题在企业级项目中都需要统一处理，不能让每个开发者自己去踩坑。

### 7.1.5 企业网络架构设计思路

一个成熟的企业级RN项目网络层，通常包含以下分层结构：

```
┌──────────────────────────────────────────────────┐
│            业务层（Page / Component）              │
│         直接调用API方法，拿到类型化数据             │
├──────────────────────────────────────────────────┤
│            API定义层（api/modules）                │
│      按业务模块划分接口：userApi, orderApi...      │
├──────────────────────────────────────────────────┤
│            请求工具层（utils/request）              │
│    Axios实例 + 拦截器 + 错误处理 + 重试机制        │
├──────────────────────────────────────────────────┤
│            基础设施层（Axios / Fetch）              │
│         HTTP引擎 + 平台适配 + 网络状态监听          │
└──────────────────────────────────────────────────┘
```

这种分层架构的好处是职责清晰、边界明确：业务层不关心请求怎么发出去的，只管调用对应的API方法拿到类型化的数据；API定义层不关心错误怎么处理，只负责把业务参数传给请求工具层；请求工具层不关心业务逻辑是什么，只做拦截、转换、错误处理等通用逻辑；基础设施层是最底层的HTTP引擎，负责真正的网络通信。每一层只做自己的事情，修改某一层时不会牵一发动全身，这才是工程化的代码组织方式。

> 架构设计的核心不是"能跑就行"，而是"改的时候不慌"。好的分层让需求变更只影响一个层，坏的架构让每个需求都要动全身。

## 7.2 Axios全局请求工具封装

### 7.2.1 Axios安装与基础参数配置

前面介绍了Axios的优势，接下来我们动手封装一个企业级的请求工具。首先安装依赖并创建基础实例：

```js
// utils/request.js
import axios from 'axios';
import { Platform } from 'react-native';

// 创建Axios实例
const request = axios.create({
  // 基础URL，通过环境变量区分开发/生产
  baseURL: __DEV__
    ? 'https://dev-api.example.com'
    : 'https://api.example.com',
  // 请求超时时间15秒
  timeout: 15000,
  // 默认请求头
  headers: {
    'Content-Type': 'application/json',
    'X-Platform': Platform.OS,
    'X-Version': '1.0.0',
  },
});

export default request;
```

这段代码中有几个关键配置项需要特别注意，每一个都直接影响生产环境的稳定性。`baseURL`通过`__DEV__`全局变量区分开发环境和生产环境，这是RN内置的开发环境判断变量，不需要额外安装任何依赖。`timeout`设置为十五秒，这是移动端经过大量实践得出的经验值——太短会导致弱网下频繁超时，用户还没等到服务器响应就被掐断了；太长会让用户等太久，体验上完全不可接受。`headers`中注入了平台信息和版本号，后端可以据此做统计分析、灰度发布、版本兼容等逻辑。

### 7.2.2 请求拦截器统一参数处理

请求拦截器是Axios最强大的特性之一。所有请求在发出之前都会经过拦截器，我们可以在这里统一注入Token、添加时间戳防缓存、注入设备信息等：

```js
// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 1. 注入Token
    const token = global.token || '';
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 2. GET请求添加时间戳防缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      };
    }

    // 3. 注入设备信息
    config.headers['X-Device-Id'] = global.deviceId || '';

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

这里有一个容易踩的坑，也是我在 code review 中经常发现的问题：拦截器中的`config`对象是Axios内部对象，直接修改`config.headers`是可以的，但如果要修改`config.params`，一定要用展开运算符创建新对象后再赋值，否则在某些Axios版本中会出现参数被意外覆盖的问题，排查起来非常困难。另外，Token的获取方式建议放在全局变量或状态管理库中，而不是每次都去AsyncStorage里同步读取，因为AsyncStorage的读取是异步操作，放在同步的拦截器里会导致竞态条件。

> 拦截器是网络层的"门卫"。请求出去之前过一道安检，响应回来之后过一道质检，整个项目的数据安全性就有了底线保障。

### 7.2.3 响应拦截器数据格式化

后端API（Application Programming Interface，应用程序接口）返回的数据通常有一个统一的包装格式，包含状态码、提示信息和业务数据。响应拦截器的职责是把这个包装拆开，只把业务数据返回给调用方：

```js
// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data;

    // 约定后端返回格式：{ code, message, data }
    if (res.code === 0 || res.code === 200) {
      // 业务成功，直接返回data字段
      return res.data;
    }

    // 业务失败，提取错误信息
    const errorMsg = res.message || '请求失败';

    // 可以接入全局Toast提示
    // Toast.show(errorMsg);

    return Promise.reject(new Error(errorMsg));
  },
  (error) => {
    // HTTP错误处理
    return Promise.reject(error);
  }
);
```

这段代码的关键在于`res.code`的判断逻辑，这也是前后端协作中最需要对齐的约定之一。不同后端的成功码约定不同：有的用数字0表示成功，有的用数字200表示成功，有的用字符串"0000"表示成功，甚至有的后端不同模块的成功码都不一样。在封装请求工具之前一定要和后端团队充分对齐成功码约定，否则会出现接口正常返回但前端报错的诡异Bug，而且这种Bug只在特定接口上出现，排查起来非常折磨人。

### 7.2.4 全局错误码统一解析处理

企业级项目通常有一套全局错误码体系，不同的错误码代表不同的错误类型和业务含义。比如HTTP状态码401表示用户未授权需要重新登录，403表示当前用户权限不足无法访问该资源，404表示请求的资源不存在，500表示服务器内部出现了未预期的错误，502表示网关错误通常是后端服务挂了，503表示服务暂时不可用可能是正在维护中。除了HTTP标准状态码，后端还会定义业务层面的错误码，比如10001表示参数校验失败，10002表示余额不足，10003表示库存不够等。我们需要在响应拦截器中对这些错误码做统一处理，而不是在每个业务页面中分散处理。

```js
// 全局错误码处理映射
const errorHandler = (error) => {
  const { response } = error;

  if (!response) {
    // 网络错误（无响应）
    return Promise.reject({
      code: -1,
      message: '网络连接异常，请检查网络设置',
    });
  }

  const status = response.status;
  const errorMap = {
    401: '登录已过期，请重新登录',
    403: '暂无权限访问',
    404: '请求的资源不存在',
    500: '服务器开小差了，请稍后重试',
    502: '网关错误，请稍后重试',
    503: '服务暂时不可用',
  };

  const message = errorMap[status] || `请求错误(${status})`;

  // 401特殊处理：跳转登录页
  if (status === 401) {
    // 清除本地Token
    global.token = '';
    // 跳转登录页（需要接入导航）
    // navigationRef.navigate('Login');
  }

  return Promise.reject({ code: status, message });
};

// 在响应拦截器的错误分支中使用
request.interceptors.response.use(
  (response) => { /* ... */ },
  errorHandler
);
```

这里有一个设计要点需要特别说明：错误处理函数返回的是一个被reject的Promise对象，携带了统一格式的错误信息结构体`{ code, message }`。这样设计的好处是，业务层用`try-catch`捕获错误时，拿到的永远是结构化的错误信息对象，不需要再判断是网络错误还是业务错误还是HTTP错误，直接读取`error.message`展示给用户即可。同时，401状态码的跳转登录逻辑放在这里统一处理，避免每个业务页面都写一遍登录过期的判断和处理代码。

### 7.2.5 请求超时与重试机制实现

弱网环境下，请求超时后直接报错是不够友好的。更合理的做法是自动重试若干次，如果多次重试仍然失败再提示用户。这个机制可以通过Axios拦截器实现：

```js
// 请求重试配置
const RETRY_COUNT = 2;
const RETRY_DELAY = 1000;

// 存储每个请求的重试次数
const retryMap = new Map();

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config) return Promise.reject(error);

    const requestId = config.url + config.method;
    const currentRetry = retryMap.get(requestId) || 0;

    // 判断是否需要重试：超时或网络错误，且未超过重试次数
    const shouldRetry =
      (error.code === 'ECONNABORTED' || !error.response) &&
      currentRetry < RETRY_COUNT;

    if (shouldRetry) {
      retryMap.set(requestId, currentRetry + 1);
      // 延迟后重试
      await new Promise((r) => setTimeout(r, RETRY_DELAY));
      return request(config);
    }

    // 清除重试记录
    retryMap.delete(requestId);
    return Promise.reject(error);
  }
);
```

重试机制有几个关键参数需要根据具体的业务场景仔细调整：`RETRY_COUNT`控制最大重试次数，一般设置为两到三次就足够了，再多也不会有太大改善反而增加服务器压力；`RETRY_DELAY`控制重试间隔时间，太短会给服务器造成压力甚至触发限流，太长用户等不及会直接退出APP。还有一个非常重要的安全限制：只有GET请求才适合自动重试，POST、PUT、DELETE等写操作绝对不能无脑重试，否则会导致重复提交，比如重复创建订单、重复扣款等严重问题。

> 重试不是万能药。GET请求重试是安全网，写操作重试是定时炸弹。不区分请求方法的无脑重试，迟早会炸出重复下单的生产事故。

## 7.3 主流HTTP请求方法实战

### 7.3.1 GET分页查询与参数传递

GET请求是最常用的HTTP方法，主要用于数据查询。在RN列表页中，分页查询是最典型的GET请求场景。先看一个完整的分页查询Hook封装：

```js
// hooks/usePagination.js
import { useState, useCallback } from 'react';
import request from '../utils/request';

export function usePagination(url, initialParams = {}) {
  const [list, setList] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // 下拉刷新
  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const res = await request.get(url, {
        params: { ...initialParams, page: 1, size: 20 },
      });
      setList(res.list || []);
      setTotal(res.total || 0);
      setPage(1);
    } finally {
      setRefreshing(false);
    }
  }, [url]);

  // 上拉加载更多
  const loadMore = useCallback(async () => {
    if (loading || list.length >= total) return;
    setLoading(true);
    try {
      const nextPage = page + 1;
      const res = await request.get(url, {
        params: { ...initialParams, page: nextPage, size: 20 },
      });
      setList((prev) => [...prev, ...(res.list || [])]);
      setPage(nextPage);
    } finally {
      setLoading(false);
    }
  }, [url, page, loading, list.length, total]);

  return { list, total, loading, refreshing, refresh, loadMore };
}
```

这个Hook封装了分页查询的核心逻辑，包含了下拉刷新和上拉加载两个最常用的交互动作。下拉刷新时重置到第一页，清空列表重新请求；上拉加载时追加下一页数据到列表末尾。同时处理了loading状态防止重复请求，以及到底判断防止无意义请求。使用时只需要传入接口地址和初始参数，业务组件完全不需要关心分页细节，大大降低了列表页的开发复杂度。

GET请求传参有一个常见的坑：数组参数的序列化。比如`ids: [1, 2, 3]`这个参数，不同的后端期望的格式不同：有的期望`ids=1&ids=2&ids=3`，有的期望`ids=1,2,3`，有的期望`ids[]=1&ids[]=2&ids[]=3`。Axios默认用的是`ids[]=1&ids[]=2&ids[]=3`格式，如果你的后端期望其他格式，需要配置`paramsSerializer`：

```js
// 自定义数组参数序列化
request.get('/users', {
  params: { ids: [1, 2, 3] },
  paramsSerializer: {
    indexes: null, // 生成 ids=1&ids=2&ids=3
  },
});
```

### 7.3.2 POST表单与JSON数据提交

POST请求用于创建资源，数据格式主要有两种：JSON（JavaScript Object Notation，JavaScript对象表示法）和FormData（表单数据格式）。Axios默认使用JSON格式，直接传对象即可：

```js
// JSON格式提交
const res = await request.post('/users', {
  name: '怕浪猫',
  email: 'palamon@example.com',
  age: 28,
});

// FormData格式提交（用于文件上传等场景）
const formData = new FormData();
formData.append('name', '怕浪猫');
formData.append('avatar', {
  uri: 'file:///path/to/image.jpg',
  type: 'image/jpeg',
  name: 'avatar.jpg',
});

const res = await request.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});
```

这里有一个新手常踩的坑，我在技术交流群里几乎每周都能看到有人问这个问题：提交FormData时必须手动设置`Content-Type`为`multipart/form-data`。虽然Axios在浏览器环境下会自动识别FormData对象并设置正确的Content-Type，但在RN的JavaScript引擎中有时不会自动识别FormData的类型，导致后端收到的请求头中Content-Type仍然是`application/json`，后端按照JSON格式去解析FormData，直接解析失败返回400错误。显式设置Content-Type是最稳妥的做法，不要依赖运行环境的自动检测。

### 7.3.3 PUT数据更新接口对接

PUT请求用于全量更新资源，PATCH用于部分更新。实际开发中，很多团队的PUT和PATCH用法并不规范，经常混用。我们以标准的PUT请求为例：

```js
// 更新用户信息
const updateUser = async (userId, data) => {
  try {
    const res = await request.put(`/users/${userId}`, {
      name: data.name,
      email: data.email,
      phone: data.phone,
    });
    return res;
  } catch (error) {
    // 业务层处理具体错误
    if (error.code === 409) {
      // 手机号已被占用
      throw new Error('该手机号已被注册');
    }
    throw error;
  }
};
```

PUT和POST在Axios中的用法几乎一样，区别只是HTTP方法不同。但有一个语义上的注意点：PUT是幂等的，即多次调用同一个PUT请求应该产生相同的结果。如果你的接口在PUT时会创建新记录，那说明这个接口设计有问题，应该用POST。

### 7.3.4 DELETE删除请求实战开发

DELETE请求用于删除资源，通常参数通过URL路径传递而不是请求体。但有些后端设计会在DELETE请求体中传递批量删除的ID列表，这在RN中需要特殊处理：

```js
// 单个删除
const deleteUser = async (userId) => {
  await request.delete(`/users/${userId}`);
};

// 批量删除（参数在请求体中）
const batchDelete = async (ids) => {
  await request.delete('/users', {
    data: { ids },
  });
};

// 批量删除（参数在URL中，更RESTful）
const batchDeleteSafe = async (ids) => {
  await request.delete(`/users?ids=${ids.join(',')}`);
};
```

DELETE请求有一个前端体验设计的核心要点需要特别强调：删除操作通常是不可逆的，一旦执行就无法撤销，所以在发请求前一定要给用户一个二次确认弹窗，让用户明确知道自己即将删除什么内容。同时，删除成功后要同步更新本地列表数据，直接在客户端把已删除的项从列表中过滤掉，而不是重新请求整个列表接口——这样用户体验更流畅，网络请求更少，服务器压力更小。如果删除后立即重新请求列表，用户会看到列表闪一下白屏再重新渲染，体验上远不如本地直接删除来得平滑。

```js
const handleDelete = (userId) => {
  Alert.alert(
    '确认删除',
    '删除后不可恢复，确定要删除该用户吗？',
    [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          await deleteUser(userId);
          // 本地直接过滤掉已删除项
          setList(prev => prev.filter(item => item.id !== userId));
        },
      },
    ]
  );
};
```

### 7.3.5 并行与串行请求处理方案

有些页面需要同时请求多个接口，比如首页可能需要同时拉取用户信息、通知列表、推荐数据。如果串行请求，三个接口各1秒，用户要等3秒。如果并行请求，理论上1秒就能全部返回。Axios提供了`Promise.all`和`axios.all`两种方式实现并行请求：

```js
// 并行请求（所有请求同时发出，等全部完成）
const loadHomePageData = async (userId) => {
  try {
    const [userInfo, notifications, recommendations] = await Promise.all([
      request.get(`/users/${userId}`),
      request.get('/notifications', { params: { userId } }),
      request.get('/recommendations', { params: { userId } }),
    ]);

    return { userInfo, notifications, recommendations };
  } catch (error) {
    // Promise.all的坑：任意一个请求失败，全部失败
    console.error('首页数据加载失败:', error);
    throw error;
  }
};

// 容错并行请求（单个失败不影响其他）
const loadHomePageDataSafe = async (userId) => {
  const results = await Promise.allSettled([
    request.get(`/users/${userId}`),
    request.get('/notifications', { params: { userId } }),
    request.get('/recommendations', { params: { userId } }),
  ]);

  const data = {};
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      data[['userInfo', 'notifications', 'recommendations'][index]] = result.value;
    }
  });
  return data;
};
```

`Promise.all`和`Promise.allSettled`的区别是实战开发中的高频考点，也是面试中经常被问到的问题：`Promise.all`是"一损俱损"模式，任何一个请求失败就整体进入reject，所有数据都拿不到；`Promise.allSettled`是"各自为战"模式，不管成功还是失败都返回对应的结果，调用方可以根据每个请求的status字段判断是成功还是失败。首页这种聚合场景适合用`Promise.allSettled`——推荐数据加载失败不应该导致用户信息也展示不出来，每个模块应该独立容错。

> 并行请求是性能优化的利器，但用错场景就是灾难。核心数据用Promise.all保证一致性，非核心数据用Promise.allSettled保证可用性。

## 7.4 移动端网络请求性能优化

### 7.4.1 请求防抖节流实现方案

搜索框是RN中最需要防抖优化的场景，几乎每个有搜索功能的页面都会遇到这个问题。用户每输入一个字符就触发一次网络请求，不仅严重浪费带宽和服务器资源，还可能因为请求返回顺序的不确定性导致搜索结果错乱——用户输入"abc"时发出了三个请求"a"、"ab"、"abc"，如果"abc"的请求先返回而"a"的请求后返回，页面最终展示的是"a"的搜索结果，和用户输入的内容完全不匹配。防抖（Debounce）的解决思路是：只在用户停止输入一段时间后才真正发起请求，在停止输入之前的所有输入变化都只更新本地状态不触发网络请求。

```js
// hooks/useDebounce.js
import { useRef, useCallback } from 'react';

export function useDebounce(callback, delay = 500) {
  const timerRef = useRef(null);

  const debouncedFn = useCallback((...args) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  return debouncedFn;
}

// 在搜索场景中使用
const SearchScreen = () => {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async (text) => {
    if (!text.trim()) {
      setResults([]);
      return;
    }
    const res = await request.get('/search', { params: { q: text } });
    setResults(res.list || []);
  };

  const debouncedSearch = useDebounce(handleSearch, 500);

  const handleChange = (text) => {
    setKeyword(text);
    debouncedSearch(text);
  };

  return (
    <View>
      <TextInput
        value={keyword}
        onChangeText={handleChange}
        placeholder="搜索"
      />
      {results.map(item => (
        <Text key={item.id}>{item.name}</Text>
      ))}
    </View>
  );
};
```

节流（Throttle）和防抖（Debounce）的核心区别在于触发时机的不同：防抖是"停下来才执行"，只有在用户停止输入一段时间后才触发请求，适合搜索框这种场景；节流是"每隔一段时间最多执行一次"，不管用户操作多频繁，在固定时间窗口内只触发一次，适合滚动加载、按钮防连点这种场景。理解了两者的区别，才能在不同场景下选择正确的方案。

### 7.4.2 重复请求取消机制封装

快速切换页面时，旧页面的请求如果还没完成，新页面的请求已经发出了，旧请求返回的数据可能会覆盖新请求的数据，导致页面展示错误的内容。这在Tab切换、页面跳转返回等场景下特别容易出现。解决方案是使用AbortController取消未完成的旧请求，确保同一时间同一个接口只有一个请求在进行中。

```js
// 封装带取消能力的请求方法
const pendingRequests = new Map();

// 生成请求Key
const getRequestKey = (config) => {
  return `${config.method}-${config.url}-${JSON.stringify(config.params || {})}`;
};

// 添加请求到pending队列
const addPendingRequest = (config) => {
  const key = getRequestKey(config);
  if (pendingRequests.has(key)) {
    // 已有相同请求在pending中，取消旧请求
    pendingRequests.get(key).abort();
  }
  const controller = new AbortController();
  config.signal = controller.signal;
  pendingRequests.set(key, controller);
  return config;
};

// 从pending队列移除
const removePendingRequest = (config) => {
  const key = getRequestKey(config);
  if (pendingRequests.has(key)) {
    pendingRequests.delete(key);
  }
};

// 在请求拦截器中添加
request.interceptors.request.use((config) => {
  addPendingRequest(config);
  return config;
});

// 在响应拦截器中移除
request.interceptors.response.use(
  (response) => {
    removePendingRequest(response.config);
    return response;
  },
  (error) => {
    if (error.config) {
      removePendingRequest(error.config);
    }
    return Promise.reject(error);
  }
);
```

这段代码的核心思路是：用一个Map数据结构维护所有进行中的请求，以"请求方法+请求URL+请求参数的JSON字符串"作为唯一标识。当新请求发出时，如果发现相同标识的旧请求还在进行中，就调用AbortController的abort方法取消旧请求。请求完成后无论成功还是失败都从Map中移除对应的记录。这种机制在快速切换Tab页或快速翻页时特别有效，能避免旧请求的过期数据覆盖新请求的最新数据。

### 7.4.3 接口数据本地缓存策略

有些接口数据更新频率很低，比如省市区列表、商品分类、配置信息等。每次打开页面都请求一遍既浪费流量又影响速度。这类数据适合做本地缓存：

```js
// utils/cache.js
import AsyncStorage from '@react-native-async-storage/async-storage';

// 带缓存的请求
export const cachedRequest = async (key, requestFn, ttl = 5 * 60 * 1000) => {
  // 1. 先读本地缓存
  const cached = await AsyncStorage.getItem(`cache_${key}`);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    // 缓存未过期，直接返回
    if (Date.now() - timestamp < ttl) {
      return data;
    }
  }

  // 2. 缓存过期或不存在，发网络请求
  const freshData = await requestFn();

  // 3. 写入缓存
  await AsyncStorage.setItem(
    `cache_${key}`,
    JSON.stringify({ data: freshData, timestamp: Date.now() })
  );

  return freshData;
};

// 使用示例
const getCategories = () => {
  return cachedRequest(
    'categories',
    () => request.get('/categories'),
    30 * 60 * 1000 // 缓存30分钟
  );
};
```

缓存策略有一个关键设计原则需要特别注意：缓存过期后不是直接清空等待网络请求返回，而是先返回旧数据给页面渲染，同时在后台静默发起网络请求更新缓存。这种被称为"Stale-While-Revalidate"的策略能让用户在网络慢时也能立即看到上次的内容，而不是盯着loading转圈等网络请求返回。这种策略在新闻类、电商类等对数据实时性要求不是特别高的场景中非常实用。

```js
// Stale-While-Revalidate策略
export const swrRequest = async (key, requestFn, ttl) => {
  const cached = await AsyncStorage.getItem(`cache_${key}`);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < ttl) {
      // 缓存有效，直接返回
      return data;
    }
    // 缓存过期：先返回旧数据，同时静默更新
    requestFn().then((freshData) => {
      AsyncStorage.setItem(
        `cache_${key}`,
        JSON.stringify({ data: freshData, timestamp: Date.now() })
      );
    }).catch(() => {});
    return data; // 先返回旧数据
  }
  // 无缓存：正常请求
  const freshData = await requestFn();
  await AsyncStorage.setItem(
    `cache_${key}`,
    JSON.stringify({ data: freshData, timestamp: Date.now() })
  );
  return freshData;
};
```

> 缓存是性能优化的银弹，但缓存一致性是它的代价。缓存策略的设计永远在"速度"和"新鲜度"之间找平衡点。

### 7.4.4 离线数据兜底容错方案

在断网场景下，正常的网络请求会直接失败并抛出错误。但如果我们有本地缓存数据，可以在请求失败时降级读取缓存数据返回给业务层，让用户在离线状态下也能看到上次成功加载的内容，而不是面对一个空白的错误页面。这种"有网看最新，断网看缓存"的降级策略，是移动端应用的基本体验保障。

```js
// 离线兜底请求
export const offlineFallback = async (key, requestFn, ttl) => {
  try {
    // 先尝试网络请求
    const data = await requestFn();
    // 请求成功，更新缓存
    await AsyncStorage.setItem(
      `cache_${key}`,
      JSON.stringify({ data, timestamp: Date.now() })
    );
    return { data, fromCache: false, offline: false };
  } catch (error) {
    // 网络失败，尝试读取缓存
    const cached = await AsyncStorage.getItem(`cache_${key}`);
    if (cached) {
      const { data } = JSON.parse(cached);
      return { data, fromCache: true, offline: true };
    }
    // 无缓存也无网络，彻底失败
    throw error;
  }
};
```

这个离线兜底模式在很多内容类APP中都在广泛使用。比如新闻APP断网后还能看之前浏览过的新闻列表，电商APP断网后还能看之前浏览过的商品详情，地图APP断网后还能看之前缓存过的地图瓦片。用户体感上就是"有网看最新内容，断网看上次内容"，比直接白屏报错好太多了。返回值中的`fromCache`和`offline`字段可以让UI层区分数据来源，在页面上展示"当前为离线模式"的提示横幅，让用户知道看到的是缓存数据而非最新数据。

### 7.4.5 弱网断网场景体验优化

除了数据层面的兜底，UI（User Interface，用户界面）层面的弱网体验同样重要。以下是几个实战中总结的优化策略：

```
┌───────────────────────────────────────────────────────┐
│              弱网/断网体验优化策略矩阵                   │
├──────────────┬────────────────────────────────────────┤
│   场景       │   优化策略                              │
├──────────────┼────────────────────────────────────────┤
│  请求中      │   骨架屏 + 超时进度提示                  │
│  弱网中      │   降级图片质量 + 延迟加载非核心内容       │
│  断网时      │   离线提示 + 缓存兜底 + 重试按钮         │
│  网络恢复    │   自动重试 + 数据同步                    │
│  后台唤醒    │   静默刷新关键数据                       │
└──────────────┴────────────────────────────────────────┘
```

网络状态监听可以使用`@react-native-community/netinfo`库，在网络恢复时自动重试之前失败的请求：

```js
import NetInfo from '@react-native-community/netinfo';

// 全局网络状态监听
let isOnline = true;
const failedQueue = [];

NetInfo.addEventListener((state) => {
  const wasOffline = !isOnline;
  isOnline = state.isConnected;

  // 从离线恢复到在线时，重试失败的请求
  if (wasOffline && isOnline && failedQueue.length > 0) {
    const retryList = [...failedQueue];
    failedQueue.length = 0;
    retryList.forEach((fn) => fn());
  }
});

// 在错误处理中收集失败的请求
const addToRetryQueue = (config) => {
  if (config.method === 'get') {
    failedQueue.push(() => request(config));
  }
};
```

注意只有GET请求才适合自动重试。POST、PUT、DELETE等写操作如果自动重试，可能导致重复操作，比如重复下单、重复扣款、重复发送消息等严重问题。对于写操作的网络恢复重试，应该在UI上弹出提示框询问用户"网络已恢复，是否重试刚才的操作"，让用户明确感知到这是一个可能产生副作用的重复操作。

## 7.5 图片与文件上传全套实战

### 7.5.1 FormData表单数据格式解析

文件上传的核心是FormData（Form Data，表单数据格式），它是一种用于构造键值对的接口，特别适合通过HTTP传输文件。在RN中，FormData的使用方式和Web端略有不同，主要体现在文件对象的构造上：

```js
// RN中FormData的文件对象格式
const fileObject = {
  uri: 'file:///data/user/0/com.app/files/photo.jpg',  // 文件URI
  type: 'image/jpeg',    // MIME类型
  name: 'photo.jpg',     // 文件名
};

// 构造FormData
const formData = new FormData();
formData.append('file', fileObject);
formData.append('userId', '12345');
formData.append('description', '这是一张图片');
```

FormData的底层编码格式是`multipart/form-data`，它将表单数据分割成多个部分，每部分用boundary（边界分隔符）分隔。理解这个编码格式对于调试上传问题非常重要——有时候上传失败就是因为文件对象的`type`字段设置错误，比如把`image/png`写成了`image/jpg`，导致后端按照错误的MIME类型去解析文件流，直接解析失败返回400错误。又比如`name`字段忘记加文件扩展名，后端无法识别文件类型。这些细节都是实际开发中踩过的坑。

```
┌─────────────────────────────────────────────────────┐
│           multipart/form-data 编码结构               │
├─────────────────────────────────────────────────────┤
│  Content-Type: multipart/form-data; boundary=xxx    │
│                                                     │
│  --xxx                                              │
│  Content-Disposition: form-data; name="userId"      │
│                                                     │
│  12345                                              │
│  --xxx                                              │
│  Content-Disposition: form-data; name="file";       │
│  filename="photo.jpg"                               │
│  Content-Type: image/jpeg                           │
│                                                     │
│  [二进制文件数据]                                    │
│  --xxx--                                            │
└─────────────────────────────────────────────────────┘
```

### 7.5.2 单图上传功能完整实现

在RN中，图片选择通常使用`react-native-image-picker`库。选完图片后，需要先压缩再上传，避免上传过大的原图：

```js
// hooks/useImageUpload.js
import { launchImageLibrary } from 'react-native-image-picker';
import request from '../utils/request';

export function useImageUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const pickAndUpload = async () => {
    // 1. 选择图片
    const result = await launchImageLibrary({
      mediaType: 'photo',
      quality: 0.6,        // 压缩质量
      maxWidth: 1920,      // 最大宽度
      maxHeight: 1920,     // 最大高度
      selectionLimit: 1,
    });

    if (result.didCancel || !result.assets?.length) {
      return null;
    }

    const asset = result.assets[0];

    // 2. 构造FormData
    const formData = new FormData();
    formData.append('file', {
      uri: asset.uri,
      type: asset.type || 'image/jpeg',
      name: asset.fileName || 'upload.jpg',
    });

    // 3. 上传
    setUploading(true);
    try {
      const res = await request.post('/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            setProgress(Math.round((e.loaded / e.total) * 100));
          }
        },
      });
      return res;
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return { pickAndUpload, uploading, progress };
}
```

这段代码有几个实战要点需要特别说明。`quality: 0.6`是图片压缩质量参数，0.6是在保证图片清晰度的前提下大幅减小文件体积的经验值——一张5MB的原图经过0.6质量压缩后通常只有500KB左右，上传速度提升十倍以上。`maxWidth`和`maxHeight`限制最大尺寸，超过这个尺寸的图片会被自动等比缩放，避免上传分辨率过高的无用图片。上传时通过`onUploadProgress`回调获取上传进度，这个进度是字节数比例，可以转换为百分比展示给用户。

### 7.5.3 多图片批量上传处理方案

多图上传有两种策略：并行上传和串行上传。并行上传速度快但服务器压力大，串行上传稳定但耗时更长。实际项目中推荐并行上传但限制并发数，比如同时最多3个：

```js
// 并发限制器
const uploadWithConcurrency = async (files, limit = 3) => {
  const results = [];
  const executing = new Set();

  for (const file of files) {
    const promise = (async () => {
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type || 'image/jpeg',
        name: file.name || 'upload.jpg',
      });
      return request.post('/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    })();

    results.push(promise);
    executing.add(promise);

    promise.finally(() => executing.delete(promise));

    if (executing.size >= limit) {
      await Promise.race(executing);
    }
  }

  return Promise.allSettled(results);
};

// 使用示例
const handleBatchUpload = async (assets) => {
  const results = await uploadWithConcurrency(assets, 3);
  const success = results
    .filter(r => r.status === 'fulfilled')
    .map(r => r.value);
  const failed = results.filter(r => r.status === 'rejected');
  console.log(`成功${success.length}张，失败${failed.length}张`);
  return { success, failed };
};
```

多图上传的UI交互设计也需要特别注意：每张图片应该独立显示自己的上传状态（等待中、上传中、已成功、已失败），单张图片上传失败不应该影响其他图片的上传。失败的图片单独提供"重试"按钮，而不是让用户重新选择全部图片从头开始上传。这种原子化的上传体验在用户选择九宫格图片时尤为重要——用户不想因为最后一张上传失败就丢失前面八张的上传结果。

> 多图上传最大的体验杀手不是速度慢，而是一张失败全部重来。把上传拆成独立的原子操作，失败重试的成本就降到了最低。

### 7.5.4 上传进度实时监听与展示

进度展示是文件上传的核心体验。Axios通过`onUploadProgress`回调提供上传进度，我们只需要把进度数据驱动UI更新即可：

```jsx
// components/UploadProgress.js
import { useState } from 'react';
import { View, Text, ProgressBarAndroid, ProgressViewIOS, Platform } from 'react-native';

const UploadProgress = ({ visible, progress }) => {
  if (!visible) return null;

  const ProgressBar = Platform.OS === 'ios' ? ProgressViewIOS : ProgressBarAndroid;

  return (
    <View style={{ padding: 20, alignItems: 'center' }}>
      <Text>上传中 {progress}%</Text>
      <ProgressBar
        progress={progress / 100}
        style={{ width: '80%', marginTop: 10 }}
      />
    </View>
  );
};

// 在页面中使用
const AvatarUpload = () => {
  const { pickAndUpload, uploading, progress } = useImageUpload();

  return (
    <View>
      <TouchableOpacity onPress={pickAndUpload}>
        <Text>选择头像</Text>
      </TouchableOpacity>
      <UploadProgress visible={uploading} progress={progress} />
    </View>
  );
};
```

进度展示有一个精度问题需要注意：`onUploadProgress`回调中的`e.loaded`和`e.total`是字节数，在小文件上进度变化会跳变得非常快，因为数据量小很快就传完了，进度从零直接跳到一百。对于小文件（小于一百KB），建议直接显示"上传中"文字提示而不显示百分比进度条，避免进度条闪烁影响用户体验。对于大文件，进度条展示就非常有价值了，用户需要知道自己还要等多久。另外，在RN中`onUploadProgress`的回调可能触发频率不如Web端那么高，如果进度更新不够流畅，可以考虑用Animated API做插值动画来平滑进度条的移动。

### 7.5.5 大文件分片上传核心思路

对于大文件（如视频），一次性上传会有超时风险，弱网下尤其严重。分片上传的思路是：将大文件切成多个小块，每块单独上传，最后通知服务器合并。虽然RN中文件操作受限，但核心思路值得了解：

```
┌─────────────────────────────────────────────────────┐
│              分片上传核心流程                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 客户端请求上传 → 服务器返回 uploadId             │
│                                                     │
│  2. 客户端切片：                                     │
│     file → [chunk_0, chunk_1, chunk_2, ... chunk_n] │
│     每片大小：2MB~5MB                               │
│                                                     │
│  3. 并发上传各分片（带序号和uploadId）                │
│     POST /upload/chunk { uploadId, index, data }    │
│                                                     │
│  4. 全部分片上传完成 → 通知服务器合并                 │
│     POST /upload/merge { uploadId, totalChunks }    │
│                                                     │
│  5. 服务器合并所有分片 → 返回最终文件URL             │
│                                                     │
│  优势：断点续传、并行加速、失败重试成本低             │
└─────────────────────────────────────────────────────┘
```

分片上传在纯RN环境中实现有一定的技术难度，因为RN对文件系统操作的API比较有限，不像Web端有File对象可以方便地调用slice方法切割文件。通常需要借助`react-native-fs`这个原生模块来读取文件的指定位置和指定长度的数据片段。分片上传的核心优势在断点续传场景下体现得特别明显：如果上传到第五片时网络断了，恢复后只需要从第五片继续上传，前面已经成功上传的四片不需要重新传输，大大节省了带宽和时间。这需要服务器端配合记录已接收的分片列表，客户端在恢复上传前先查询已上传的分片列表，跳过已完成的分片。

```js
// 分片上传核心伪代码
import RNFS from 'react-native-fs';

const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB

const uploadLargeFile = async (filePath, uploadId) => {
  // 获取文件大小
  const stat = await RNFS.stat(filePath);
  const totalChunks = Math.ceil(stat.size / CHUNK_SIZE);

  // 读取并上传每个分片
  const uploadChunk = async (index) => {
    const start = index * CHUNK_SIZE;
    const length = Math.min(CHUNK_SIZE, stat.size - start);
    const base64 = await RNFS.read(filePath, length, start, 'base64');
    await request.post('/upload/chunk', {
      uploadId,
      index,
      total: totalChunks,
      data: base64,
    });
  };

  // 并发上传（限制并发数3）
  await uploadWithConcurrency(
    Array.from({ length: totalChunks }, (_, i) => i).map(i => ({ index: i })),
    3
  );

  // 通知服务器合并
  const result = await request.post('/upload/merge', {
    uploadId,
    totalChunks,
  });
  return result.url;
};
```

分片上传的优势在断点续传场景下特别明显：如果上传到第5片时网络断了，恢复后只需要从第5片继续上传，前面已上传的分片不需要重传。这需要服务器端配合记录已接收的分片列表。

## 7.6 WebSocket实时长连接通信

### 7.6.1 WebSocket通信底层原理

WebSocket（WebSocket Protocol，WebSocket协议）是一种在单个TCP（Transmission Control Protocol，传输控制协议）连接上进行全双工通信的协议。与HTTP的"请求-响应"模式不同，WebSocket建立连接后，客户端和服务器都可以随时向对方发送数据。

```
┌─────────────────────────────────────────────────────┐
│          HTTP vs WebSocket 通信模式对比               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  HTTP模式（半双工）：                                │
│  Client ──请求──→ Server                           │
│  Client ←─响应── Server                            │
│  （连接关闭，下次请求重新建立连接）                    │
│                                                     │
│  WebSocket模式（全双工）：                           │
│  Client ←═══持久连接═══→ Server                    │
│  Client ──消息──→ Server   （随时发）              │
│  Client ←─消息── Server    （随时推）              │
│  （连接保持，直到主动关闭）                          │
│                                                     │
│  握手过程：                                          │
│  1. Client发送HTTP GET请求，带Upgrade: websocket    │
│  2. Server返回101 Switching Protocols               │
│  3. 连接升级为WebSocket，开始双向通信                │
└─────────────────────────────────────────────────────┘
```

WebSocket与HTTP的关系可以这样理解：WebSocket的握手阶段使用的是标准HTTP协议，客户端发送一个带有`Upgrade: websocket`头部的HTTP GET请求，服务器如果支持WebSocket就返回101状态码表示协议切换。握手成功后，底层的TCP连接就从HTTP协议升级为WebSocket协议，之后双方可以随时向对方发送数据帧，不需要再遵循HTTP的请求-响应模式。这意味着WebSocket可以复用HTTP的基础设施如端口、代理、负载均衡等，但在握手完成后通信方式完全不同。这种设计让WebSocket能够平滑地穿透现有的网络基础设施，部署成本很低。

在RN中，WebSocket API是内置的，不需要安装任何额外依赖，直接使用全局的WebSocket构造函数即可创建连接。但RN的WebSocket和浏览器中的WebSocket在二进制数据处理上有一些差异，比如在发送ArrayBuffer或Blob时需要特别注意RN的JavaScript引擎是否支持。另外，RN中的WebSocket在Android和iOS上的行为也有一些细微差别，比如在后台运行时的连接保持策略不同，iOS在后台时会很快挂起WebSocket连接，而Android的行为则取决于设备的省电策略。这些平台差异在开发时都需要实际测试验证。

### 7.6.2 RN客户端WS基础搭建

搭建一个WebSocket客户端，最基础的功能包括：建立连接、发送消息、接收消息、关闭连接。但在生产环境中，还需要处理重连、心跳、消息队列等复杂逻辑。我们先从基础版本开始：

```js
// utils/websocket.js
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    this.isConnected = false;
  }

  // 建立连接
  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.isConnected = true;
      this.emit('open');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('message', data);
      } catch (e) {
        this.emit('message', event.data);
      }
    };

    this.ws.onerror = (error) => {
      this.emit('error', error);
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this.emit('close');
    };
  }

  // 发送消息
  send(data) {
    if (this.isConnected) {
      const message = typeof data === 'string'
        ? data : JSON.stringify(data);
      this.ws.send(message);
    }
  }

  // 事件监听
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  // 触发事件
  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach((cb) => cb(data));
  }

  // 关闭连接
  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default WebSocketClient;
```

这个基础版本封装了WebSocket的核心操作，使用了观察者模式（Observer Pattern）来管理事件监听。外部代码通过`on('message', callback)`来监听消息事件，通过`send()`方法来发送消息，不需要直接操作WebSocket实例。这种封装的好处是如果将来需要更换底层通信库比如换成Socket.IO或者原生模块，只需要修改这个类的内部实现，外部调用代码完全不需要改动，符合依赖倒置的设计原则。

### 7.6.3 消息收发与数据解析处理

WebSocket消息通常是JSON格式的文本，但也可以是二进制数据。在实际业务中，消息通常有一个统一的协议格式，包含消息类型、数据体等字段：

```js
// 消息协议格式定义
// {
//   "type": "chat",        // 消息类型
//   "from": "user_123",    // 发送者
//   "to": "user_456",      // 接收者
//   "data": {              // 消息数据
//     "text": "你好",
//     "timestamp": 1690000000000
//   }
// }

// 消息处理器
const messageHandlers = {
  chat: (data) => {
    // 聊天消息处理
    return {
      type: 'chat',
      id: data.id,
      text: data.data.text,
      sender: data.from,
      timestamp: data.data.timestamp,
    };
  },
  notification: (data) => {
    // 通知消息处理
    return {
      type: 'notification',
      title: data.data.title,
      content: data.data.content,
    };
  },
  system: (data) => {
    // 系统消息处理
    return {
      type: 'system',
      action: data.data.action,
    };
  },
};

// 在onmessage中使用
wsClient.on('message', (rawData) => {
  const handler = messageHandlers[rawData.type];
  if (handler) {
    const message = handler(rawData);
    // 分发到对应的消息队列或状态管理
    // store.dispatch(addMessage(message));
  } else {
    console.warn('未知消息类型:', rawData.type);
  }
});
```

这种基于消息类型的分发模式，最大的好处是扩展性极强——新增一种消息类型只需要在`messageHandlers`对象中添加一个对应的处理函数，不需要修改消息接收和分发的核心逻辑。这符合开闭原则：对扩展开放，对修改关闭。在实际的即时通讯项目中，消息类型可能有十几种：聊天消息、系统通知、好友请求、群组事件、消息撤回、输入状态等，全部通过这种统一的分发机制处理，代码结构清晰且易于维护。

### 7.6.4 心跳保活与断线重连机制

WebSocket连接在长时间没有数据传输时，中间的网络设备（路由器、NAT网关等）可能会自动关闭这个"空闲"连接。为了保持连接存活，客户端需要定期发送心跳包：

```
┌─────────────────────────────────────────────────────┐
│           心跳保活与断线重连流程                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  正常状态：                                          │
│  Client ──ping──→ Server    （每30秒一次）          │
│  Client ←─pong── Server     （服务器响应）          │
│                                                     │
│  异常检测：                                          │
│  Client ──ping──→ Server                           │
│  （等待5秒未收到pong）                               │
│  → 标记连接异常                                     │
│  → 关闭当前连接                                     │
│  → 进入重连流程                                     │
│                                                     │
│  重连策略（指数退避）：                               │
│  第1次重连：等待1秒                                  │
│  第2次重连：等待2秒                                  │
│  第3次重连：等待4秒                                  │
│  第4次重连：等待8秒                                  │
│  最大等待：30秒                                      │
│  连续失败超过10次 → 放弃重连，提示用户               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

下面是心跳保活与断线重连的核心实现，我们分几个部分来看：

首先是构造函数和连接建立部分：

```js
// 增强版WebSocket客户端
class EnhancedWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.ws = null;
    this.listeners = new Map();
    // 心跳配置
    this.heartbeatInterval = options.heartbeatInterval || 30000;
    this.heartbeatTimeout = options.heartbeatTimeout || 5000;
    this.heartbeatTimer = null;
    this.waitingPong = false;
    // 重连配置
    this.maxRetries = options.maxRetries || 10;
    this.retryCount = 0;
    this.messageQueue = []; // 断线时暂存消息
    this.isConnected = false;
    this.shouldReconnect = true;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.isConnected = true;
      this.retryCount = 0;
      this.startHeartbeat();
      this.flushMessageQueue(); // 重连后发送队列消息
      this.emit('open');
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'pong') {
        this.waitingPong = false; // 心跳响应
        return;
      }
      this.emit('message', data);
    };
    this.ws.onclose = () => {
      this.isConnected = false;
      this.stopHeartbeat();
      if (this.shouldReconnect) this.scheduleReconnect();
      this.emit('close');
    };
  }
```

接下来是心跳保活和断线重连的核心逻辑：

```js
  // 心跳保活：定期发送ping检测连接状态
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.waitingPong) {
        this.forceClose(); // 上次ping未收到pong，连接异常
        return;
      }
      this.send({ type: 'ping' });
      this.waitingPong = true;
      this.heartbeatTimeoutTimer = setTimeout(() => {
        if (this.waitingPong) this.forceClose();
      }, this.heartbeatTimeout);
    }, this.heartbeatInterval);
  }

  // 断线重连：指数退避策略
  scheduleReconnect() {
    if (this.retryCount >= this.maxRetries) {
      this.emit('reconnect_failed');
      return;
    }
    const delay = Math.min(Math.pow(2, this.retryCount) * 1000, 30000);
    this.retryTimer = setTimeout(() => {
      this.retryCount++;
      this.emit('reconnecting', {
        attempt: this.retryCount,
        maxRetries: this.maxRetries,
      });
      this.connect();
    }, delay);
  }
```

最后是消息发送、队列管理和工具方法部分：

```js
  // 强制关闭（心跳超时触发）
  forceClose() {
    if (this.ws) {
      this.ws.onclose = null; // 防止触发重连
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.stopHeartbeat();
    this.scheduleReconnect();
  }

  // 发送消息（断线时入队，重连后自动发送）
  send(data) {
    const msg = typeof data === 'string' ? data : JSON.stringify(data);
    if (this.isConnected) {
      this.ws.send(msg);
    } else {
      this.messageQueue.push(msg);
    }
  }

  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      this.ws.send(this.messageQueue.shift());
    }
  }

  close() {
    this.shouldReconnect = false;
    this.stopHeartbeat();
    clearTimeout(this.retryTimer);
    if (this.ws) { this.ws.close(); this.ws = null; }
  }
}
```

这段代码涵盖了心跳保活和断线重连的完整逻辑，是生产环境WebSocket客户端的核心代码。有几个设计要点需要详细说明：

一是指数退避重连策略。重连间隔不是固定的，而是随着失败次数呈指数增长，第一次重连等待一秒，第二次两秒，第三次四秒，第四次八秒，最大不超过三十秒。这样设计的好处是既不会在服务器故障时产生雪崩式的重连请求压垮服务器，又能在服务器恢复后较快地重连成功。每次重连成功后重试计数器归零，重新开始计算。

二是消息队列机制。连接断开时用户发送的消息不会丢失，而是暂存在本地队列中，等重连成功后自动按照发送顺序依次发送出去。这对用户来说是完全"无感"的——在弱网环境下发送消息，看起来消息立即发出去了，实际上在后台等待重连后才真正发送，用户体验非常流畅。

三是心跳超时检测机制。客户端发送ping消息后如果在五秒内没有收到服务器返回的pong响应，就认为连接已经断开，主动关闭当前连接并触发重连流程。这比等待TCP层面的超时检测要快得多——TCP的KeepAlive超时通常要几十秒甚至几分钟，用户根本等不了那么久。

四是`shouldReconnect`标志位。当用户主动调用`close()`方法关闭连接时，不应该触发自动重连。通过这个标志位区分"主动关闭"和"意外断开"两种场景，避免用户退出聊天页面后WebSocket还在后台不断重连浪费电量和流量。

> 心跳和重连不是可选项，而是WebSocket的生产标配。线上没有心跳机制的WebSocket连接，会在NAT超时后静默断开，用户看到一个"假在线"状态，体验极差。

### 7.6.5 即时聊天业务简单落地

把前面的WebSocket封装用到实际业务中，实现一个简单的即时聊天功能。我们需要把WebSocket消息和React组件状态管理结合起来：

```js
// hooks/useChat.js
import { useState, useEffect, useRef, useCallback } from 'react';
import EnhancedWebSocket from '../utils/websocket';

export function useChat(userId, targetId) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  // 初始化WebSocket连接
  useEffect(() => {
    const ws = new EnhancedWebSocket(
      `wss://api.example.com/ws?userId=${userId}`
    );

    ws.on('open', () => setConnected(true));
    ws.on('close', () => setConnected(false));
    ws.on('reconnecting', (info) => {
      console.log(`重连中(${info.attempt}/${info.maxRetries})`);
    });

    ws.on('message', (data) => {
      if (data.type === 'chat' && data.from === targetId) {
        setMessages((prev) => [...prev, {
          id: data.id,
          text: data.data.text,
          sender: 'other',
          timestamp: data.data.timestamp,
        }]);
      }
    });

    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [userId, targetId]);

  // 发送消息
  const sendMessage = useCallback((text) => {
    const message = {
      type: 'chat',
      from: userId,
      to: targetId,
      data: { text, timestamp: Date.now() },
    };

    wsRef.current?.send(message);

    // 本地立即添加消息（乐观更新）
    setMessages((prev) => [...prev, {
      id: `local_${Date.now()}`,
      text,
      sender: 'me',
      timestamp: Date.now(),
    }]);
  }, [userId, targetId]);

  return { messages, connected, sendMessage };
}
```

这里使用了一个重要的前端交互模式——乐观更新（Optimistic Update，又称乐观UI更新）。发送消息时，不等服务器确认收到就直接在UI上显示这条消息，让用户感觉消息是"即时发送"的，没有等待延迟。如果服务器返回失败，再回滚这条消息并提示用户发送失败。这种方式比等服务器确认后再显示要快得多，在弱网环境下体验优势尤其明显——用户不用盯着发送中的loading动画干等，消息"秒发"的感觉让聊天体验流畅很多。

```jsx
// ChatScreen.js 聊天页面
import { useChat } from '../hooks/useChat';

const ChatScreen = ({ route }) => {
  const { userId, targetId, targetName } = route.params;
  const { messages, connected, sendMessage } = useChat(userId, targetId);
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim()) return;
    sendMessage(inputText.trim());
    setInputText('');
  };

  return (
    <View style={{ flex: 1 }}>
      {/* 连接状态指示器 */}
      <View style={{ padding: 5, backgroundColor: connected ? '#4CAF50' : '#FF9800' }}>
        <Text style={{ color: '#fff', textAlign: 'center' }}>
          {connected ? '已连接' : '连接中...'}
        </Text>
      </View>

      {/* 消息列表 */}
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={{
            alignSelf: item.sender === 'me' ? 'flex-end' : 'flex-start',
            backgroundColor: item.sender === 'me' ? '#007AFF' : '#E5E5EA',
            borderRadius: 12,
            padding: 10,
            margin: 5,
            maxWidth: '70%',
          }}>
            <Text style={{ color: item.sender === 'me' ? '#fff' : '#000' }}>
              {item.text}
            </Text>
          </View>
        )}
      />

      {/* 输入框 */}
      <View style={{ flexDirection: 'row', padding: 10 }}>
        <TextInput
          value={inputText}
          onChangeText={setInputText}
          placeholder="输入消息"
          style={{ flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 8, paddingHorizontal: 10 }}
        />
        <TouchableOpacity onPress={handleSend} style={{ marginLeft: 10, justifyContent: 'center' }}>
          <Text>发送</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
```

这个聊天页面虽然功能比较简单，但已经涵盖了即时聊天的核心要素：连接状态实时展示、消息列表渲染、消息发送和乐观更新。在实际的生产项目中，还需要加上消息已读未读状态管理、图片消息和语音消息支持、历史消息分页加载、消息撤回与编辑、群聊消息分发等功能模块。但不管业务功能多么复杂，底层的WebSocket通信机制和心跳重连逻辑是不变的，这就是分层架构的价值——底层稳固，上层灵活扩展。

## 企业级网络层封装清单总结

最后，把本章涉及的企业级网络层封装要点整理成一个清单，方便你在项目中对照落地：

```
企业级RN网络层封装清单：

【请求工具层】
[ ] Axios实例创建（baseURL、timeout、headers）
[ ] 请求拦截器（Token注入、公共参数、防缓存时间戳）
[ ] 响应拦截器（数据格式化、错误码统一处理）
[ ] 请求超时与自动重试（仅GET请求）
[ ] 重复请求取消（AbortController + pendingMap）

【性能优化层】
[ ] 请求防抖（搜索场景）
[ ] 请求节流（滚动加载场景）
[ ] 接口数据本地缓存（AsyncStorage + TTL）
[ ] 离线数据兜底（缓存降级策略）
[ ] 网络状态监听与自动重试（NetInfo）

【文件上传层】
[ ] 图片压缩（react-native-image-picker quality参数）
[ ] 单图上传与进度展示
[ ] 多图批量上传（并发限制器）
[ ] 大文件分片上传思路（react-native-fs）

【WebSocket层】
[ ] 基础连接封装（connect/send/close）
[ ] 心跳保活机制（ping-pong + 超时检测）
[ ] 断线重连机制（指数退避策略）
[ ] 消息队列（断线时消息暂存）
[ ] 消息协议设计与类型分发
```

> 清单的价值不在于"全做了"，而在于"清楚地知道哪些还没做"。每一条没做的都是潜在的生产事故隐患点，建议按照优先级逐步补齐：先保证基础的拦截器和错误处理到位，再逐步添加性能优化和弱网容错能力，最后完善文件上传和WebSocket的进阶功能。工程化不是一蹴而就的，而是持续打磨的过程。

## 总结

这章我们从网络请求方案选型开始，逐步封装了一个企业级的Axios请求工具，覆盖了拦截器、错误处理、超时重试等核心能力。然后实战了GET、POST、PUT、DELETE四种HTTP方法，以及并行请求的容错处理方案。在性能优化部分，我们实现了防抖、请求取消、数据缓存、离线兜底等移动端必备能力。文件上传部分覆盖了从单图上传到多图批量上传、进度监听到大文件分片上传的完整方案。最后用WebSocket实现了实时长连接通信，包括心跳保活、断线重连和即时聊天业务落地。

网络层是整个RN项目的地基工程。地基打得牢固，上面的业务页面怎么写都不会出大问题；地基不稳固，页面写得再漂亮也只是沙滩上的城堡，一个弱网环境就能让所有页面崩掉。这章内容从方案选型到工具封装到实战落地，覆盖了RN网络层开发中最核心的知识点和技术难点。把这些内容吃透并在项目中落地，你的RN网络层至少能抵御百分之九十以上的移动端网络异常场景。希望这章内容能帮你把网络层的地基打扎实，让你在后续的业务开发中少踩坑、多产出。

**收藏这篇文章**，下次搭建RN网络层的时候直接对照清单落地，能省掉大量踩坑时间。如果你在实践中遇到了这章没覆盖到的网络层问题，欢迎在评论区交流，怕浪猫会逐个回复。

**追更提醒**：如果你觉得这章内容有价值，点击关注不迷路。下一章我们会进入RN本地存储与数据持久化的世界，涵盖AsyncStorage、MMKV、SQLite、Realm等存储方案的选型与实战，这才是移动端数据管理的硬核内容。

怕浪猫说：网络请求看似简单，一个fetch就够了。但当你的APP要面对真实用户的弱网环境、真实业务的错误处理、真实场景的文件上传和实时通信时，"能用"和"好用"之间的差距，就是这章内容的全部价值。写代码要像猫一样——踩坑之前先看清路，但真踩到了也能优雅地跳出来。

系列进度 7/16

下章预告：第8章 RN本地存储与数据持久化——AsyncStorage、MMKV高速缓存、SQLite本地数据库、Realm方案选型与封装实战。

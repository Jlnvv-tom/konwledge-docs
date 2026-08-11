---
sidebar_position: 1
---

# 第1章 跨端开发入门：React Native初识与环境搭建

> 一套代码跑双端，听起来像偷懒，实际上是工程智慧的终极体现。

2025年的移动端开发圈有一个扎心事实：一个业务要同时覆盖Android和iOS，用原生开发至少需要两套人马、两套代码、两套测试流程，开发周期动辄翻倍。而跨端技术的出现，让一个前端工程师就能搞定双端发布。React Native（以下简称RN）作为Meta（原Facebook）开源的跨端框架，已经在Instagram、Discord、Microsoft Office、Shopify等超大规模应用中验证了可行性。但选型踩坑、环境搭建、架构理解这些入门门槛，劝退了不下一半的新手。

我见过太多团队的选型翻车案例。有的团队跟风选了某个跨端框架，结果做到一半发现核心功能不支持，被迫推翻重来；有的团队上来就搞原生开发，结果双端进度严重不一致，iOS都上线了Android还在提测；还有的团队选了RN但没做好架构规划，代码乱成一锅粥，最后维护成本比原生还高。这些教训都指向同一个问题：对跨端技术生态缺乏系统认知，对自身项目需求缺乏准确判断。

我是怕浪猫，一个在跨端开发坑里摸爬滚打多年的老选手。从今天开始，我会用16章的篇幅，带你从零开始系统掌握RN全栈开发。这一章是全书第一站，帮你建立认知、搭好环境、跑通第一个项目。

## 1.1 移动端跨端技术生态与选型

### 1.1.1 原生开发与跨端开发核心差异

移动端开发有两条路：原生开发和跨端开发。理解它们的本质差异，是做技术选型的前提。

原生开发指的是使用平台官方语言和工具进行开发，Android端用Kotlin/Java配合Android Studio，iOS端用Swift/Objective-C配合Xcode。这种方式直接调用系统API（Application Programming Interface），性能最优，但双端代码完全独立，维护成本高。

跨端开发则是用一套技术栈同时生成双端应用。核心思路是：用Web技术或类Web技术编写业务逻辑，再通过中间层映射到原生组件渲染。

来看两者的核心差异对比：

| 维度 | 原生开发 | 跨端开发 |
|------|---------|---------|
| 开发语言 | Kotlin + Swift | JS/TS（一套） |
| 代码复用率 | 0% | 70%-95% |
| 开发周期 | 双端各自独立 | 单套代码双端运行 |
| 性能表现 | 最优 | 接近原生（RN/Flutter） |
| 人力成本 | 至少两端团队 | 一套团队覆盖双端 |
| 原生能力 | 完整支持 | 需桥接或插件扩展 |
| 热更新 | 不支持 | 支持（RN/H5方案） |

> 跨端不是银弹，它用10%-20%的性能牺牲换取了50%以上的研发效率提升。对绝大多数业务场景来说，这笔交易稳赚不赔。但也要清醒地认识到，跨端方案在某些极端场景下确实无法替代原生，比如需要直接操作底层硬件、超高频的实时渲染、或者对启动速度有严苛要求的应用。技术选型永远是在约束条件下寻找最优解，而不是寻找万能药。

### 1.1.2 Flutter、uni-app与RN技术对比

主流跨端方案有三家：Flutter（Google）、React Native（Meta）、uni-app（DCloud）。三者技术路线不同，适用场景也各有侧重。

Flutter采用Dart语言，自绘引擎直接调用Skia渲染，不依赖原生组件。优点是性能出色、UI一致性极强，缺点是Dart语言生态小、包体积偏大。

uni-app基于Vue语法，编译到多端（包括小程序）。优点是国内生态好、小程序支持完善，缺点是性能在复杂场景下有瓶颈，深度定制能力弱。

RN采用JavaScript/TypeScript，调用原生组件渲染，保留原生体验。优点是Web生态直接复用、热更新能力突出、社区活跃，缺点是原生模块需要双端分别编写。

从技术架构角度对比三者的渲染机制：

```
Flutter渲染路径：
  Dart代码 -> Skia引擎 -> 直接绘制 -> 屏幕
  （完全绕过原生组件，自绘UI）

RN渲染路径：
  JS代码 -> Bridge/JSI -> 原生组件 -> 屏幕
  （JS控制逻辑，原生负责渲染）

uni-app渲染路径：
  Vue代码 -> 编译转换 -> 各端原生/H5 -> 屏幕
  （编译时转换，运行时依赖宿主）
```

关键差异点在于：Flutter自己画，RN让原生画，uni-app让宿主画。这决定了三者在性能、体验、开发效率上的不同表现。

| 对比项 | Flutter | RN | uni-app |
|--------|---------|-----|---------|
| 开发语言 | Dart | JS/TS | Vue/JS |
| 渲染方式 | 自绘引擎 | 原生组件映射 | 编译到各端 |
| 性能 | 优秀 | 良好 | 中等 |
| 热更新 | 不支持 | 支持 | 支持 |
| 小程序 | 需适配 | 需适配 | 原生支持 |
| 包体积 | 偏大 | 中等 | 较小 |
| 社区生态 | Google主导 | Meta+社区 | 国内社区 |
| 学习曲线 | 中等 | 低（会React即可） | 低（会Vue即可） |

### 1.1.3 React Native核心优势与适用场景

RN的核心竞争力可以归纳为三点：Learn once, write anywhere。

第一，Web生态直接复用。你写的TypeScript代码、状态管理逻辑、网络请求封装，跟Web前端几乎一致。团队里会React的工程师，上手RN只需要理解组件库差异和原生桥接机制。

第二，原生渲染而非WebView。RN的UI组件最终映射到Android的View和iOS的UIView，不是跑在WebView里的H5页面。这意味着滚动流畅度、手势响应、动画效果都接近原生。

第三，动态更新能力。通过CodePush等方案，RN可以绕过应用商店审核直接下发JS Bundle，实现Bug修复和轻量功能更新。这在紧急修复场景下价值巨大。

RN最适合的场景包括：

- 内容型应用（资讯、社交、电商展示页）
- 已有React/Web团队需要扩展移动端
- 需要热更新能力的B端应用
- 快速验证的MVP（Minimum Viable Product）产品
- 需要同时覆盖双端且预算有限的团队

不太适合的场景：重度游戏、实时音视频处理、复杂的物理动画引擎这类对渲染性能要求极高的应用。如果你的应用需要大量自定义绘制、复杂的手势竞争、或者需要直接操作GPU（Graphics Processing Unit），那原生开发仍然是更好的选择。但这不代表RN完全不能做这些场景，只是需要更多的原生模块开发和性能调优，投入产出比不划算。

怕浪猫在实战中总结过一个判断标准：如果你的应用80%的页面是列表展示、表单提交、媒体播放这类标准交互，那就放心用RN。如果超过20%的页面需要复杂的自定义绘制或高频动画，就需要慎重考虑了。

> 选型的本质不是选最强的，而是选最合适的。RN的甜点区是"重业务逻辑、轻原生交互"的应用，这恰好覆盖了80%的移动端开发需求。怕浪猫在多个项目中选择RN的根本原因不是性能，而是团队效率和人才招聘优势。一个会React的工程师可以同时做Web和移动端，这种人才复用价值在企业扩张期是无价的。

### 1.1.4 企业级跨端项目落地案例分析

来看几个用RN落地的大型项目，理解RN在生产环境中的真实表现。

**Instagram**：Meta自家的旗舰产品，Instagram的很多页面都采用RN开发，包括Push通知详情页、广告管理页面等。Meta内部有一套完整的RN优化方案，包括自定义Bridge优化、预加载策略等。

**Discord**：全球最大的游戏社区应用，iOS端几乎全部采用RN构建。Discord团队在博客中分享过，RN让他们用30人的前端团队替代了原本需要60+人的双端原生团队。

**Microsoft Office**：微软的Office移动端部分页面使用RN重写，包括文档列表、设置页面等。微软还开源了`@react-native-windows`，让RN可以跑在Windows平台上。

**Shopify**：电商SaaS巨头，Shopify的移动端全面转向RN。他们的工程团队分享过一组数据：RN重构后，开发效率提升33%，崩溃率下降20%，代码复用率达到95%。

**沃尔玛**：沃尔玛的电商App采用RN开发，覆盖商品浏览、购物车、订单管理等核心流程。他们通过自定义原生模块解决了性能瓶颈问题。

**国内实践**：在国内市场，RN同样有大量落地案例。京东的部分活动页、美团的商家端、字节跳动的部分工具类应用都采用了RN方案。国内开发者需要注意的是，由于生态差异，国内项目通常会集成一些本土化SDK（Software Development Kit），如高德地图、微信支付、极光推送等，这些都需要编写原生桥接模块或使用社区提供的封装库。

这些案例说明一个事实：RN不是玩具，它已经在日活过亿的应用中证明了生产能力。关键在于团队是否有足够的工程化能力来驾驭它。团队需要建立完善的组件库、规范的开发流程、自动化的构建发布体系，才能充分发挥RN的优势。

### 1.1.5 RN全栈开发学习路线与能力模型

学好RN需要建立三层能力模型：

**第一层：前端基础能力**
- JavaScript/TypeScript语法
- React核心概念（组件、Props、State、Hooks）
- 状态管理（Redux/Zustand/Context）
- 网络请求与数据处理

**第二层：RN专属能力**
- RN组件库与API使用
- 导航方案（React Navigation）
- 原生模块开发（Bridge/JSI）
- 性能优化与调试
- 双端差异处理

**第三层：工程化与原生能力**
- 原生项目配置与打包
- CI/CD（Continuous Integration/Continuous Deployment）流水线
- 热更新方案集成
- 原生插件开发与发布
- 多环境配置与发布管理

建议的学习顺序是：先补React基础（如果还不熟），再学RN组件和导航，然后做一个小项目跑通全流程，最后深入原生模块和性能优化。本书的16章内容就是按照这个路径设计的。

怕浪猫需要特别提醒的是：不要跳过React基础直接学RN。很多新手觉得RN跟React差不多，直接上手RN结果踩了一堆坑。RN确实基于React，但它在组件体系、样式系统、事件处理上都有显著差异。如果你对React的Hooks、Context、组件生命周期都不熟悉，在RN里调试问题时会非常痛苦。建议至少花一周时间把React核心概念过一遍，磨刀不误砍柴工。

## 1.2 React Native架构与运行原理

### 1.2.1 RN核心设计理念与开发思想

RN的设计哲学可以用一句话概括：用Web的开发体验，产出原生的用户体验。

这句话拆开来看包含三个关键设计决策：

第一，声明式UI。跟React一样，RN采用JSX语法描述UI结构，通过状态驱动视图更新。你不需要手动操作DOM（Document Object Model），只需要修改State，框架自动处理渲染。

第二，组件化。RN提供了`View`、`Text`、`Image`等基础组件，这些组件在编译后映射到原生组件。你写的`<View>`在Android上变成`android.view.View`，在iOS上变成`UIView`。

第三，声明式UI的底层逻辑。React的声明式编程范式意味着你只需要描述UI在特定状态下应该长什么样，框架会自动计算从旧状态到新状态的最小更新路径。在RN中，这个过程通过Virtual Tree（虚拟树）的diff算法实现，跟Web端的Virtual DOM概念类似，但最终操作的不是DOM节点，而是原生组件树。理解这个机制对后续的性能优化至关重要。

```jsx
// RN组件映射示例
import { View, Text, Platform } from 'react-native';

export const Card = ({ title }) => (
  <View style={styles.container}>
    <Text style={styles.title}>{title}</Text>
    <Text>运行平台: {Platform.OS}</Text>
  </View>
);
// Platform.OS 返回 'ios' 或 'android'
// 同一套代码，渲染为对应平台的原生组件
```

> RN的聪明之处在于：它没有试图替代原生，而是做了一个高效的翻译官。这个翻译官的好处是，你只需要用一种语言（JavaScript/TypeScript）来表达意图，翻译官负责把意图传达给两个不同的原生平台。而你作为开发者，可以把精力集中在业务逻辑上，而不是在两个平台上重复实现相同的功能。

### 1.2.2 JS线程、UI线程、原生线程机制

理解RN的线程模型，是理解RN性能特征的钥匙。

RN运行时有三个核心线程：

**JS线程（JavaScript Thread）**：执行JS代码、处理业务逻辑、计算组件树的diff。React的render过程在这个线程完成。

**UI线程（Main Thread / Native UI Thread）**：原生UI渲染线程，负责实际绘制界面、处理用户手势。Android上就是主线程，iOS上就是Main Thread。

**原生模块线程（Native Modules Thread）**：执行原生模块代码，比如网络请求、数据库操作、文件读写等。避免阻塞JS线程。

在新架构之前，这三个线程通过Bridge异步通信。新架构引入JSI后，JS线程可以直接引用原生对象，通信从异步消息变成了同步方法调用。

线程间的数据流向：

```
用户操作 -> UI线程捕获手势事件
         -> 通过Bridge/JSI传给JS线程
         -> JS线程处理逻辑，计算新状态
         -> 生成新的组件树指令
         -> 通过Bridge/JSI传回UI线程
         -> UI线程执行原生组件更新
         -> 界面刷新
```

这个流程解释了一个关键现象：当JS线程繁忙时（比如执行大量计算），UI响应会变慢。因为JS线程被占用，无法及时处理新的交互事件。这就是为什么RN强调"保持JS线程轻量"的原因。

在实际开发中，怕浪猫踩过很多次这个坑。比如在列表页加载大量数据时做了复杂的JSON解析和数据处理，结果滚动卡顿明显。解决方案是把耗时计算放到原生线程执行，或者使用InteractionManager将非紧急任务推迟到交互结束后执行。这些优化技巧在后续章节会详细讲解。

另一个关键概念是帧率。RN的目标是60fps（每秒60帧），每帧的预算约为16.6毫秒。如果JS线程在一帧内无法完成计算并提交更新，就会丢帧，用户感知到的就是卡顿。这也是为什么新架构的Fabric渲染器要做并发渲染支持，就是把渲染工作拆分到多帧执行，避免单帧超时。

### 1.2.3 新旧架构（Fabric/TurboModule）迭代

RN在0.68版本开始引入新架构（New Architecture），这是RN近年来最重要的一次底层重构。

**旧架构（Legacy Architecture）**的核心是Bridge。Bridge是一个异步消息队列，JS和原生之间所有通信都通过这个队列序列化/反序列化。问题在于：

- 通信是异步的，无法同步调用原生方法
- 所有数据都要JSON序列化，大对象传输性能差
- Bridge是单队列，所有模块共享一条通道，容易拥堵

**新架构（New Architecture）**包含两个核心模块：

**Fabric**：新的渲染系统。取代了旧的Paper渲染器，支持同步渲染、并发渲染、批量更新。Fabric直接对接UI线程，减少中间环节。

**TurboModule**：新的原生模块系统。通过JSI（JavaScript Interface）让JS直接持有原生模块的引用，调用原生方法不需要序列化。

```
旧架构通信路径：
  JS -> JSON序列化 -> Bridge队列 -> JSON反序列化 -> 原生
  （异步、有序列化开销）

新架构通信路径：
  JS -> JSI直接调用 -> 原生方法
  （同步、无序列化开销）
```

从RN 0.76开始，新架构默认开启。这意味着如果你现在开始学RN，直接面对的就是新架构。但理解旧架构仍然重要，因为大量现有项目和第三方库还在过渡期。

新架构带来的实际收益包括：列表滚动更流畅（Fabric的并发渲染减少了丢帧）、原生模块调用更快（JSI免去了序列化开销）、动画更跟手（UI线程可以直接接收动画指令）。但新架构也带来了一些兼容性问题，部分老旧的第三方库如果没有适配TurboModule，在新架构下可能无法正常工作。遇到这种情况，可以暂时通过配置回退到旧架构，但长期来看所有库都会完成迁移。

开启新架构的配置方式（RN 0.76+默认开启，手动项目需配置）：

```json
// app.json
{
  "expo": {
    "newArchEnabled": true
  }
}

// 或在 android/gradle.properties
// newArchEnabled=true
// 在 ios/Podfile 中设置 ENV['RCT_NEW_ARCH_ENABLED'] = '1'
```

> 新架构不是锦上添花，是RN从"能用"到"好用"的分水岭。JSI的直接调用能力，让RN在性能上终于可以和Flutter正面硬刚。对于新项目，毫不犹豫地开启新架构。对于老项目，建议制定分阶段迁移计划，优先将核心模块迁移到TurboModule，逐步享受新架构的性能红利。

### 1.2.4 桥接通信机制底层运行逻辑

即使在新架构下，理解Bridge的运作逻辑依然有价值，因为它是RN架构思想的根基。

Bridge本质上是一个消息总线。JS线程和原生线程各有一个消息队列，彼此通过Bridge交换消息。每条消息包含模块ID、方法ID和参数。

来看一个原生方法调用的完整流程：

```js
// JS侧调用原生模块
import { NativeModules } from 'react-native';
const { ToastModule } = NativeModules;
ToastModule.show('Hello Native', 2000);
```

这段代码背后的执行流程：

```
1. JS线程：调用 ToastModule.show()
2. JS线程：将调用序列化为消息 {moduleId: 42, methodId: 1, args: ['Hello Native', 2000]}
3. Bridge：消息进入队列，等待调度
4. 原生线程：从队列取出消息，反序列化
5. 原生线程：根据moduleId找到ToastModule，根据methodId找到show方法
6. 原生线程：执行原生代码，弹出Toast
7. 原生线程：如果有返回值，序列化后通过Bridge回传给JS
```

整个流程是异步的。这就是为什么在旧架构下，原生模块调用总是返回Promise的原因。开发者需要用`async/await`或`.then()`来处理异步返回值。

新架构下同样的调用：

```js
// 新架构下通过JSI直接调用
import { NativeModules } from 'react-native';
const { ToastModule } = NativeModules;
// TurboModule通过JSI绑定，直接同步调用
ToastModule.show('Hello Native', 2000);
```

区别在于JSI让JS引擎（Hermes/JSC）直接持有原生对象的C++引用，调用时不需要序列化，也不需要经过消息队列。这意味着JS可以同步获取原生方法的返回值，对于需要频繁调用的原生模块（如传感器数据读取、动画驱动器），性能提升非常显著。

怕浪猫在做蓝牙通信模块时就深刻体会到了这个差异。旧架构下每次蓝牙数据读取都要走异步回调，数据量大的时候消息队列拥堵导致延迟明显。迁移到TurboModule后，同步读取蓝牙状态几乎零延迟，体验提升了一个量级。

### 1.2.5 RN与Web开发的本质区别

很多从Web前端转RN的开发者会踩一个坑：把RN当成"跑在手机上的React Web"。实际上两者有本质差异。

核心区别在于渲染目标。Web的React渲染到浏览器的DOM树，RN的React渲染到原生组件树。这个差异传导到了整个开发体验上。

| 对比项 | React Web | React Native |
|--------|-----------|--------------|
| 渲染目标 | DOM节点 | 原生View节点 |
| 基础组件 | div/span/img | View/Text/Image |
| 样式方案 | CSS | StyleSheet（JS对象） |
| 事件系统 | 合成事件 | 原生手势系统 |
| 布局引擎 | CSS Flexbox + Grid | Yoga（仅Flexbox） |
| 导航 | URL/Router | React Navigation |
| 网络 | fetch/XHR | fetch/Polyfill |
| 存储 | localStorage | AsyncStorage |

```jsx
// Web写法
<div className="card">
  <span className="title">Hello</span>
  <img src="/avatar.png" />
</div>

// RN写法
<View style={styles.card}>
  <Text style={styles.title}>Hello</Text>
  <Image source={require('./avatar.png')} />
</View>

// 关键差异：div->View, span->Text, img->Image
// className->style, CSS->StyleSheet
```

最容易踩的坑包括：RN没有CSS的Grid布局（只有Flexbox）、Text组件必须包裹文本内容（不能直接在View里写文字）、图片资源必须用require或uri引入、没有window和document对象。

特别是没有window和document这一点，意味着你不能使用任何依赖DOM API的库。比如jQuery、直接操作DOM的动画库、某些依赖localStorage的状态持久化方案，这些在RN里都无法使用。但这并不意味着Web生态完全无法复用，逻辑层的库如lodash、dayjs、axios等纯JS库可以正常使用，只有涉及DOM/BOM的库需要寻找RN替代方案。

另一个从Web转RN的常见困惑是样式调试。在浏览器里你可以用DevTools直接改CSS看效果，在RN里没有这样的工具。样式调试需要借助React DevTools的Inspector功能，或者通过console.log打印样式对象来排查。这种调试方式的差异需要一段适应期。

> 从Web转RN最大的思维转变是：放弃DOM思维，拥抱组件映射。你写的每一个标签，最终都是原生世界的某个对象。这个转变完成后，你会发现RN的开发体验跟Web其实非常接近，差异主要在组件名称和样式写法上，业务逻辑层的代码几乎可以无缝迁移。

## 1.3 开发工具与依赖环境安装

### 1.3.1 Node.js与包管理工具配置

RN开发的第一步是配置Node.js环境。RN的构建工具链、包管理、开发服务器都依赖Node.js。

推荐使用LTS（Long Term Support）版本的Node.js，目前是v20或v22。不推荐使用最新版本，因为可能跟RN工具链存在兼容问题。

版本管理推荐使用nvm（Node Version Manager）或fnm（Fast Node Manager），方便在多个Node版本之间切换。如果你同时维护多个项目，不同项目依赖不同的Node版本，版本管理工具就是必需品。

另外推荐配置npm镜像源，国内网络环境下从官方源安装依赖可能会很慢。可以切换到淘宝镜像或其他国内镜像源来加速。

```bash
# 安装nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 安装LTS版本
nvm install --lts
nvm use --lts

# 验证安装
node -v   # 应输出 v20.x.x 或 v22.x.x
npm -v    # 应输出 10.x.x 或更高
```

包管理工具方面，npm是默认选择。但RN社区越来越推荐使用pnpm或Yarn（特别是Yarn Berry），因为它们的依赖管理更高效、安装速度更快。

```bash
# 安装pnpm
npm install -g pnpm

# 或安装Yarn
npm install -g yarn

# 验证
pnpm -v   # 或 yarn -v
```

一个常见坑：RN项目有时候对包管理器有要求。某些库的postinstall脚本在pnpm下可能不正常工作。如果遇到依赖问题，可以尝试切换包管理器。

### 1.3.2 JDK、Android SDK环境搭建

Android开发环境需要配置JDK（Java Development Kit）和Android SDK（Software Development Kit）。

RN目前要求JDK 17。从RN 0.75开始，不再支持JDK 11，必须使用JDK 17或更高版本。

```bash
# macOS安装JDK 17（推荐使用Homebrew）
brew install --cask temurin@17

# 验证安装
java -version
# 应输出类似：openjdk version "17.0.x"

# 配置JAVA_HOME环境变量
# 在 ~/.zshrc 中添加：
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export PATH=$JAVA_HOME/bin:$PATH
```

Android SDK通过Android Studio安装。安装Android Studio后，通过SDK Manager安装以下组件：

- Android SDK Platform 34（或最新稳定版）
- Android SDK Build-Tools 34.0.0
- Android SDK Platform-Tools
- Android SDK Command-line Tools

```bash
# 配置Android SDK环境变量
# 在 ~/.zshrc 中添加：
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin

# 验证
adb --version          # Android Debug Bridge
sdkmanager --list      # 查看已安装SDK组件
```

常见踩坑点：`ANDROID_HOME`路径一定要正确。macOS下默认在`~/Library/Android/sdk`，但如果你自定义了安装路径，需要相应调整。`adb`命令找不到，99%是因为`platform-tools`路径没有加入PATH。

另一个高频问题是NDK（Native Development Kit）缺失。从RN 0.76开始，新架构默认开启，新架构的Fabric和TurboModule依赖C++编译，因此需要安装NDK。通过Android Studio的SDK Manager安装NDK Side by Side版本，推荐安装26.1.10909125或更高版本。安装后在`android/gradle.properties`中配置NDK路径，或在Android Studio的Project Structure中指定。

怕浪猫第一次配NDK的时候踩了一个大坑：安装了NDK但Gradle找不到，报错提示"No version of NDK matched the requested version"。原因是Android Studio安装的NDK版本跟项目要求的不一致。解决方案是在`android/app/build.gradle`中明确指定NDK版本号，或者在SDK Manager中安装项目要求的精确版本。

### 1.3.3 Xcode与iOS编译环境配置

iOS开发环境仅在macOS上可用。如果你使用Windows或Linux，只能开发Android端，iOS端需要借助云Mac服务（如MacStadium、GitHub Actions的macOS runner）。

Xcode从App Store安装，建议安装最新稳定版。安装完成后还需要安装Command Line Tools：

```bash
# 安装命令行工具
xcode-select --install

# 验证
xcodebuild -version
# 应输出类似：Xcode 16.x

# 接受许可协议
sudo xcodebuild -license accept
```

iOS开发还需要CocoaPods（简称Pods），它是iOS的依赖管理工具，类似于Node生态的npm。

```bash
# 安装CocoaPods
sudo gem install cocoapods

# 或使用Homebrew
brew install cocoapods

# 验证
pod --version
```

一个高频踩坑点：CocoaPods版本过低导致安装依赖失败。建议保持CocoaPods在1.15或更高版本。如果`pod install`报错，先尝试`sudo gem update cocoapods`升级。

另一个常见问题是Apple Silicon（M1/M2/M3芯片）Mac上的CocoaPods兼容性。某些旧版Pod依赖可能不支持arm64架构的模拟器，需要在Podfile中排除arm64架构。如果你在M系列芯片的Mac上遇到iOS模拟器编译报错，检查Podfile中是否有以下配置：

```ruby
# Podfile 中针对Apple Silicon的配置
# 解决M系列芯片模拟器编译问题
use_react_native!(
  :path => config[:reactNativePath],
  # 其他配置...
)

# 排除arm64架构（模拟器专用）
# 仅当M系列芯片模拟器编译报错时添加
```

### 1.3.4 模拟器与真机调试环境准备

模拟器是日常开发的主力工具，启动快、切换方便。真机调试用于验证性能和原生功能。

**Android模拟器**通过Android Studio的AVD Manager创建：

```bash
# 列出可用模拟器
emulator -list-avds

# 启动指定模拟器
emulator -avd Pixel_7_API_34

# 查看已连接设备
adb devices
```

建议创建一个API 34的Pixel系列模拟器，兼顾兼容性和性能。如果模拟器启动后白屏，尝试在AVD设置中将Graphics改为"Software"。

**iOS模拟器**通过Xcode管理：

```bash
# 列出可用模拟器
xcrun simctl list devices

# 启动指定模拟器
xcrun simctl boot "iPhone 15 Pro"

# 打开模拟器界面
open -a Simulator
```

**真机调试**需要开启开发者模式：

Android端：设置 -> 关于手机 -> 连续点击版本号7次 -> 开启USB调试 -> 用数据线连接电脑 -> `adb devices`确认连接。

iOS端：Xcode -> Settings -> Accounts -> 登录Apple ID -> 连接iPhone -> 在Xcode中选择设备 -> 首次运行需在手机上信任开发者证书。

```bash
# 确认设备连接
adb devices        # Android
xcrun simctl list  # iOS（含真机）
```

### 1.3.5 全局环境变量与版本兼容处理

环境变量配置是新手最容易翻车的环节。以下是macOS下完整的RN开发环境变量配置清单：

```bash
# ~/.zshrc 完整配置示例

# Node.js (通过nvm管理)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# JDK 17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

# Android SDK
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin

# 全局PATH
export PATH=$JAVA_HOME/bin:$PATH
```

配置完成后执行`source ~/.zshrc`使其生效。验证所有环境变量是否正确配置：

```bash
# 一键验证RN开发环境
echo "Node: $(node -v)"
echo "npm: $(npm -v)"
echo "Java: $(java -version 2>&1 | head -1)"
echo "JAVA_HOME: $JAVA_HOME"
echo "ANDROID_HOME: $ANDROID_HOME"
echo "adb: $(adb --version 2>/dev/null | head -1)"
echo "Xcode: $(xcodebuild -version 2>/dev/null | head -1)"
echo "CocoaPods: $(pod --version 2>/dev/null)"
```

如果所有命令都输出了正确的版本号，恭喜你，环境搭建完成。如果某个命令报错，对照前面的章节逐一排查。

版本兼容性是另一个高频问题。以下是RN版本与依赖版本的对应关系：

| RN版本 | Node.js | JDK | Android SDK | Xcode |
|--------|---------|-----|-------------|-------|
| 0.76+ | 20+ | 17 | 34+ | 15+ |
| 0.74-0.75 | 18+ | 17 | 34 | 15 |
| 0.72-0.73 | 16+ | 17 | 33 | 14 |
| 0.70-0.71 | 16+ | 11/17 | 33 | 14 |

> 环境搭建是RN学习的第一个筛子。配不下来环境的，大概率也坚持不到写代码。这不是坏事，提前帮你筛出了那些不适合做工程的人。怕浪猫当初学RN的时候光配环境就花了两天，踩了无数坑。但这个过程培养了我排查问题的能力，后来遇到任何环境相关的报错都能快速定位。

## 1.4 两种开发模式：Expo与原生CLI

### 1.4.1 Expo免原生开发模式优缺点

Expo是RN生态中的一套高级开发框架，它在RN之上封装了完整的开发、构建、发布工具链。使用Expo，你不需要接触原生代码，不需要配置Android Studio和Xcode，甚至不需要Mac就能开发iOS应用。

Expo的核心组件包括：

- **Expo CLI**：项目创建、开发服务器、构建工具
- **Expo Go**：手机上的开发调试App，扫码即可预览
- **EAS Build**：云端构建服务，无需本地原生环境
- **Expo SDK**：封装好的原生模块集合（相机、定位、通知等）

```bash
# 创建Expo项目
npx create-expo-app@latest MyFirstApp
cd MyFirstApp

# 启动开发服务器
npx expo start

# 扫描终端二维码，在Expo Go中实时预览
```

Expo的优点非常突出：

- 零原生配置，5分钟跑通项目
- 跨平台开发，Windows也能开发iOS
- 内置常用原生模块，API统一
- 云端构建，不需要本地Android Studio/Xcode
- 应用商店提交也通过EAS完成

但Expo也有局限：

- 深度原生定制受限（自定义原生模块需要Ejection或Config Plugin）
- 云端构建有免费额度限制，免费版每月30次iOS构建和30次Android构建
- 包体积比原生CLI项目略大，因为包含了Expo运行时
- 某些特殊的第三方原生库可能不支持Expo，特别是那些需要复杂原生配置的SDK
- 热更新使用Expo Updates有特定限制，商业项目可能需要付费方案

怕浪猫的项目经历中，Expo的免费构建额度在中型项目中基本够用，但如果你有多个分支需要频繁构建测试包，免费额度会很快耗尽。企业级项目建议直接购买EAS（Expo Application Services）付费方案，性价比合理。

### 1.4.2 RN CLI原生完整开发模式特性

RN CLI（React Native Community CLI）是RN的原始开发模式，直接生成包含完整原生代码的项目。你有完全的原生代码访问权限，可以自由修改Android的Gradle配置和iOS的Podfile。

```bash
# 创建RN CLI项目（不使用Expo）
npx @react-native-community/cli@latest init MyNativeApp
cd MyNativeApp

# iOS安装依赖
cd ios && pod install && cd ..

# 运行
npx react-native run-android
npx react-native run-ios
```

RN CLI模式的优点：

- 完全的原生代码访问权限
- 无构建额度限制，本地编译
- 支持任意第三方原生库
- 包体积可控
- 适合深度定制原生行为

缺点：

- 需要配置完整的原生开发环境，门槛较高
- 双端构建环境都要维护，特别是iOS必须用Mac
- 新手门槛较高，环境搭建可能需要一整天
- 升级RN版本比Expo复杂，需要手动处理原生代码冲突
- 第三方原生库的集成需要手动配置Gradle和Podfile

怕浪猫在维护RN CLI项目时最头疼的就是版本升级。每次升级RN版本都需要处理Android的Gradle配置变更、iOS的Podfile更新、第三方库的兼容性问题。一个小版本升级可能需要半天到一天的时间。相比之下Expo项目升级通常只需要改package.json中的版本号然后跑一次命令。

### 1.4.3 两种模式项目选型与场景适配

Expo和RN CLI不是对立关系，而是不同场景下的最优解。选型参考如下：

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 快速原型验证 | Expo | 5分钟跑通，专注业务 |
| 个人小项目 | Expo | 无需配置原生环境 |
| 已有Web团队扩展移动端 | Expo | 学习曲线最平缓 |
| 需要自定义原生模块 | RN CLI | 完全原生访问权限 |
| 企业级生产项目 | Expo（预构建） | 兼顾效率和灵活性 |
| 重度原生交互应用 | RN CLI | 深度原生定制 |
| 开发者无Mac环境 | Expo + EAS | 云端构建iOS |

值得注意的是，Expo从SDK 49开始引入了"预构建"（Prebuild）机制，可以生成原生项目但仍然用Expo管理。这让Expo和RN CLI的界限变得模糊了。

在实际企业项目中，怕浪猫推荐的使用策略是：新项目一律用Expo创建，利用Prebuild生成原生代码。这样既享受了Expo的工具链便利，又保留了原生代码的访问能力。只有当你需要极度定制化的原生配置，或者项目有严格的包体积要求时，才考虑纯RN CLI模式。

> 选Expo还是RN CLI，这个问题的答案正在变得越来越不重要。因为Expo的预构建机制让你随时可以拿到原生代码，而RN CLI项目也可以集成Expo模块。最终的选择取决于你的原生定制深度。对于大多数项目，怕浪猫建议从Expo开始，需要时再预构建生成原生代码，这是当前最佳实践。

### 1.4.4 Expo项目迁移原生CLI方案

有些项目开始用Expo快速起步，后续需要深度原生定制时需要迁移到原生CLI。Expo提供了两种迁移路径：

**方案一：Eject（传统方式）**

```bash
# 在Expo项目中执行
npx expo eject

# 会生成完整的android和ios目录
# 之后按RN CLI项目维护
```

Eject是不可逆操作。执行后项目就从Expo托管模式变成了原生CLI模式，Expo Go不再可用。

**方案二：Prebuild（推荐方式）**

```bash
# 使用expo-prebuild生成原生代码
npx expo prebuild

# 生成原生项目但仍然保持Expo管理
# 可以随时清理重新生成
npx expo prebuild --clean
```

Prebuild是可逆的。你可以删除android和ios目录后重新生成，原生配置通过`app.json`中的插件管理。

```json
// app.json 配置原生插件示例
{
  "expo": {
    "plugins": [
      "expo-camera",
      [
        "expo-location",
        {
          "locationAlwaysAndWhenInUsePermission": "允许访问位置信息"
        }
      ]
    ]
  }
}
```

### 1.4.5 企业项目初始化最佳实践

企业项目需要考虑团队协作、长期维护、CI/CD集成等因素。以下是一套经过验证的初始化流程：

```bash
# 1. 使用Expo创建项目（带TypeScript模板）
npx create-expo-app@latest MyEnterpriseApp --template default

# 2. 进入项目目录
cd MyEnterpriseApp

# 3. 生成原生项目（预构建模式）
npx expo prebuild

# 4. 初始化Git仓库
git init
git add .
git commit -m "feat: 项目初始化"

# 5. 安装核心依赖
npx expo install react-navigation/native react-navigation/native-stack
npx expo install @tanstack/react-query zustand
```

企业项目的`app.json`配置建议：

```json
{
  "expo": {
    "name": "MyEnterpriseApp",
    "slug": "my-enterprise-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "newArchEnabled": true,
    "ios": {
      "bundleIdentifier": "com.company.app",
      "supportsTablet": true
    },
    "android": {
      "package": "com.company.app",
      "adaptiveIcon": {
        "foregroundImage": "./assets/fg.png"
      }
    },
    "plugins": ["expo-router"]
  }
}
```

关键实践点：启用新架构、配置正确的包名、使用TypeScript、从一开始就配置好路径别名。

路径别名的配置在RN项目中非常重要。随着项目规模增长，深层组件的相对路径会变得难以维护（如`../../../components/Button`）。通过配置别名，可以用`@/components/Button`替代，代码可读性和重构便利性都大幅提升。具体配置方法是在`tsconfig.json`中设置paths映射，在`babel.config.js`中添加对应的module resolver插件。这个配置在第二章会详细讲解。

## 1.5 首个RN项目创建与双端运行

### 1.5.1 脚手架初始化标准RN项目

理论说够了，开始动手。以下是从零创建并运行一个RN项目的完整流程。

使用Expo创建项目（推荐新手）：

```bash
# 创建项目
npx create-expo-app@latest rn_demo --template blank-typescript

# 进入项目
cd rn_demo

# 项目结构
# ├── app.json        # Expo配置
# ├── App.tsx         # 入口组件
# ├── assets/         # 静态资源
# ├── package.json    # 依赖配置
# └── tsconfig.json   # TS配置
```

入口文件`App.tsx`的初始内容：

```tsx
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <View style={styles.container}>
      <Text>欢迎来到React Native!</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
```

这段代码虽然简单，但包含了RN开发的三个核心要素：组件导入（View/Text/StatusBar）、JSX渲染、样式定义（StyleSheet）。后续所有RN页面都是在这个基础上的扩展。

注意`StyleSheet.create`的写法。跟Web开发中内联样式不同，RN推荐使用StyleSheet.create来定义样式。这样做有两个好处：一是样式对象只会创建一次，不会在每次渲染时重新生成；二是StyleSheet会对样式做校验，无效的属性会在开发阶段给出警告。

### 1.5.2 Android真机与模拟器运行调试

启动开发服务器：

```bash
# 启动Expo开发服务器
npx expo start

# 或指定Android平台
npx expo start --android
```

开发服务器启动后，有几种方式在Android上预览：

**方式一：Expo Go扫码**

在手机上安装Expo Go应用（从Google Play下载），扫描终端中的二维码即可预览。

**方式二：USB连接真机**

```bash
# 确认设备已连接
adb devices
# List of devices attached
# XXXXXX    device

# 按下 a 键在Android设备上打开
# 或直接执行
npx expo run:android
```

**方式三：模拟器**

先启动Android模拟器，然后按`a`键自动在模拟器中打开。

```bash
# 查看可用模拟器
emulator -list-avds

# 启动模拟器
emulator -avd Pixel_7_API_34 &

# 在模拟器中运行
npx expo start --android
```

### 1.5.3 iOS真机与模拟器运行调试

iOS运行需要在macOS环境下（或通过EAS Build云端构建）。

```bash
# 启动开发服务器后按 i 键
npx expo start

# 或直接指定iOS
npx expo start --ios

# 使用RN CLI运行
npx expo run:ios
```

iOS模拟器的操作方式跟Android类似，按`i`键自动启动默认模拟器。要指定模拟器型号：

```bash
# 指定模拟器
npx expo run:ios --simulator="iPhone 15 Pro"

# 列出所有可用模拟器
xcrun simctl list devices available
```

iOS真机调试比Android复杂一些。首次运行需要配置签名：

```bash
# 在Xcode中打开iOS项目
cd ios && open Podfile
# 或用Expo项目
npx expo prebuild --platform ios
cd ios && open *.xcworkspace

# 在Xcode中：
# 1. 选择Signing & Capabilities
# 2. 选择你的Team（Apple Developer账号）
# 3. 修改Bundle Identifier为唯一值
# 4. 选择真机并运行
```

如果遇到"Untrusted Developer"错误，在iPhone上操作：设置 -> 通用 -> VPN与设备管理 -> 信任你的开发者证书。

### 1.5.4 热更新与实时刷新功能使用

RN最爽的开发体验之一就是热更新。修改代码后不需要重新编译，画面立刻刷新。

**Fast Refresh**（快速刷新）是RN的默认刷新机制。它结合了Hot Reloading和Live Reloading的优点：

- 修改组件代码：保留组件State，只更新UI
- 修改样式：即时生效，不丢失页面状态
- 修改逻辑代码：重新执行模块，保留当前页面栈
- 修改文件外的依赖：自动热加载新模块

```tsx
// 修改前
export default function App() {
  const [count, setCount] = useState(0);
  return (
    <View>
      <Text onPress={() => setCount(count + 1)}>
        点击了 {count} 次
      </Text>
    </View>
  );
}

// 修改样式时，count的值不会丢失
// 修改Text的文字时，count的值也会保留
// 只有修改useState的初始值才会重置State
```

手动触发刷新的方式：

- 摇晃设备打开开发者菜单（真机）
- 模拟器按`Cmd+D`（iOS）或`Cmd+M`（Android）
- 按`r`键强制Reload
- 按`j`键打开React DevTools

> 第一次体验到改完代码手机上秒级刷新的时候，你会理解为什么RN能吸引这么多Web开发者转行。这种开发节奏是原生开发无法提供的。原生开发每次改代码都要重新编译，大型项目编译可能需要几分钟，而RN的Fast Refresh只需要几百毫秒。这种开发效率的差距在长周期项目中会累积成巨大的生产力差异。

### 1.5.5 首次运行常见报错与解决方案

环境搭建和首次运行是最容易出问题的阶段。以下是高频报错及解决方案：

**报错1：`Unable to load script. Make sure you're either running Metro`

原因：Metro打包服务器未启动或端口被占用。

```bash
# 解决：清除缓存重启
npx expo start --clear

# 或杀掉占用8081端口的进程
lsof -i :8081
kill -9 <PID>

# 重新启动
npx expo start
```

**报错2：`Failed to install pods`（iOS）**

原因：CocoaPods版本过低或缓存问题。

```bash
# 解决：升级CocoaPods并清理缓存
sudo gem update cocoapods
pod cache clear --all
cd ios && pod install --repo-update
```

**报错3：`SDK location not found`（Android）**

原因：`ANDROID_HOME`环境变量未配置或路径错误。

```bash
# 检查环境变量
echo $ANDROID_HOME
# 应输出：/Users/你的用户名/Library/Android/sdk

# 如果为空，检查 ~/.zshrc 配置
# 确保 ANDROID_HOME 已正确设置
source ~/.zshrc
```

**报错4：`error: bundling failed: Error: Cannot find module`**

原因：node_modules依赖不完整。

```bash
# 解决：清除依赖重装
rm -rf node_modules
rm package-lock.json  # 或 yarn.lock / pnpm-lock.yaml
npm install  # 或 yarn install / pnpm install

# 如果是iOS，还需要重装Pods
cd ios && pod install && cd ..
```

**报错5：`No devices/emulators found`**

原因：模拟器未启动或设备未连接。

```bash
# Android
adb devices
# 如果列表为空，先启动模拟器或连接真机
emulator -avd Pixel_7_API_34 &

# iOS
xcrun simctl list devices booted
# 如果没有已启动的模拟器
xcrun simctl boot "iPhone 15 Pro"
open -a Simulator
```

建议把这几个解决方案收藏起来，首次搭建环境时大概率会遇到其中至少两个。

怕浪猫额外分享一个环境排错的方法论：遇到报错时，第一步看完整错误信息（不要只看最后一行），第二步确认是JS层还是原生层的报错，第三步去GitHub Issues搜索相同错误，第四步才是搜索引擎。很多新手一看到报错就慌了，直接去搜索，但往往最准确的解决方案在项目的GitHub Issues里。

## 1.6 项目结构解析与学习总结

### 1.6.1 核心目录与配置文件作用解析

一个标准的Expo RN项目结构如下：

```
rn_demo/
├── app.json              # Expo全局配置
├── App.tsx               # 应用入口组件
├── package.json          # 依赖与脚本
├── tsconfig.json         # TypeScript配置
├── babel.config.js       # Babel编译配置
├── metro.config.js       # Metro打包配置
├── assets/               # 静态资源目录
│   ├── icon.png          # 应用图标
│   └── splash.png        # 启动屏图片
├── src/                  # 业务代码目录（需手动创建）
│   ├── components/        # 公共组件
│   ├── screens/           # 页面组件
│   ├── navigation/        # 导航配置
│   ├── services/          # 接口请求
│   ├── store/             # 状态管理
│   ├── utils/             # 工具函数
│   └── types/             # TS类型定义
├── android/              # Android原生代码（prebuild后）
└── ios/                  # iOS原生代码（prebuild后）
```

关键配置文件的作用：

**app.json**：Expo项目的核心配置文件，定义应用名称、图标、启动屏、权限声明、原生插件等。这个文件贯穿整个开发周期。

**package.json**：跟Web项目一致，管理JS依赖和脚本命令。区别在于依赖中会有`react-native`本身和各种RN专用库。

**Metro打包配置**：Metro是RN的打包工具，类似于Web的Webpack。这个文件配置打包规则、缓存策略、模块解析等。理解Metro的工作原理对解决依赖冲突和打包优化很有帮助。Metro的核心流程是Resolution（模块解析）、Transformation（代码转换）和Serialization（打包输出），每一步都可以通过配置文件自定义。

```js
// metro.config.js 基础配置示例
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// 支持额外文件格式
config.resolver.assetExts.push('txt');

// 开启缓存（开发环境）
config.cacheStores = [];

module.exports = config;
```

### 1.6.2 原生目录与前端资源区分

RN项目是一个"混合体"，前端代码和原生代码共存。理解它们的边界非常重要。

**前端代码区**：`src/`目录下的所有`.tsx`、`.ts`、`.js`文件，以及`App.tsx`入口文件。这些代码跑在JS引擎（Hermes）上，负责业务逻辑和UI描述。

**原生代码区**：

Android端：`android/`目录，包含Gradle构建脚本、Java/Kotlin原生代码、AndroidManifest清单文件等。

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/.../MainActivity.kt   # 原生入口
│   │   ├── AndroidManifest.xml         # 应用清单
│   │   └── res/                        # 原生资源
│   └── build.gradle                    # 模块构建配置
├── build.gradle                        # 项目构建配置
└── gradle.properties                   # Gradle参数
```

iOS端：`ios/`目录，包含Xcode项目文件、Objective-C/Swift原生代码、Podfile依赖配置等。

```
ios/
├── MyProject.xcworkspace    # Xcode工作空间
├── MyProject.xcodeproj      # Xcode项目
├── Podfile                  # CocoaPods依赖配置
├── MyProject/
│   ├── AppDelegate.m        # 原生入口
│   └── Info.plist           # 应用配置
```

一个重要原则：前端开发者主要在`src/`目录工作，原生目录通常只在需要修改原生配置、集成第三方SDK（Software Development Kit）、或编写原生模块时才触碰。

在团队协作中，建议把原生目录的修改权限控制在少数人手里，避免前端开发者误改原生配置导致编译失败。可以通过Git的CODEOWNERS机制来实现权限控制，让原生目录的修改必须经过指定人员Review才能合并。

### 1.6.3 基础开发规范与编码习惯养成

好的编码习惯从项目第一天就要建立。以下是RN项目的基础开发规范：

**目录规范**：按功能模块组织代码，不要把所有文件堆在一个目录里。

```
src/
├── components/           # 通用组件（按钮、卡片等）
│   ├── Button/
│   │   ├── index.tsx     # 组件实现
│   │   ├── styles.ts     # 组件样式
│   │   └── types.ts      # 组件类型
├── screens/              # 页面组件
│   ├── HomeScreen.tsx
│   └── ProfileScreen.tsx
├── navigation/           # 导航配置
│   └── AppNavigator.tsx
├── services/             # API请求
│   └── api.ts
├── store/                # 状态管理
│   └── useStore.ts
└── utils/                # 工具函数
    └── format.ts
```

**命名规范**：

- 组件文件用PascalCase：`HomeScreen.tsx`
- 工具函数文件用camelCase：`formatDate.ts`
- 常量用UPPER_SNAKE_CASE：`const API_BASE_URL`
- 组件名用PascalCase：`export default function HomeScreen()`
- 样式对象用camelCase：`styles.container`

**代码规范示例**：

```tsx
// 推荐：组件结构清晰
import { View, Text, StyleSheet } from 'react-native';
import { useState } from 'react';

interface CounterProps {
  initialCount?: number;
}

export default function Counter({ initialCount = 0 }: CounterProps) {
  const [count, setCount] = useState(initialCount);

  return (
    <View style={styles.container}>
      <Text style={styles.text}>Count: {count}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16 },
  text: { fontSize: 16, color: '#333' },
});
```

> 规范不是束缚，是团队协作的基础。一个人写项目可以随意，但两个人以上维护的代码库，规范就是效率的保障。

除了目录和命名规范，还有几个开发习惯值得从一开始就养成：

**及时清理console.log**：调试时加的日志要记得删除，过多的console输出会影响JS线程性能，特别是在列表滚动等高频场景下。

**组件拆分粒度控制**：单个组件文件建议不超过300行。超过这个规模就应该考虑拆分，把子组件抽离到独立文件。这不是硬性规则，但保持组件小而专注有助于代码维护和性能优化。

**样式不内联**：避免在JSX中写`style={{ flex: 1 }}`这样的内联样式。内联样式会在每次渲染时创建新对象，导致组件不必要的重渲染。统一使用StyleSheet.create定义样式。

**类型先行**：在写组件之前先定义好Props和State的TypeScript类型。类型定义本身就是一种设计文档，帮你理清组件的输入输出关系。

### 1.6.4 本章核心知识点复盘梳理

本章内容量大，用一张知识图谱来梳理核心脉络：

```
跨端开发认知
├── 技术选型：Flutter / RN / uni-app
├── RN优势：Web生态复用 + 原生渲染 + 热更新
└── 适用场景：内容型应用、Web团队扩展、MVP验证

RN架构原理
├── 三线程模型：JS线程 + UI线程 + 原生模块线程
├── 新架构：Fabric（渲染）+ TurboModule（模块）+ JSI（通信）
├── 旧架构：Bridge异步消息队列
└── 与Web差异：无DOM、原生组件映射、StyleSheet样式

环境搭建
├── Node.js LTS + nvm版本管理
├── JDK 17 + Android SDK + adb
├── Xcode + CocoaPods + Command Line Tools
└── 环境变量：JAVA_HOME / ANDROID_HOME / PATH

开发模式选择
├── Expo：零原生配置、Expo Go预览、EAS构建
├── RN CLI：完全原生访问、本地编译
└── Prebuild：Expo管理 + 原生代码生成

项目运行
├── 创建：create-expo-app / @react-native-community/cli
├── 运行：expo start / run:android / run:ios
├── 调试：Fast Refresh + DevTools + 真机调试
└── 常见报错：端口占用 / Pod安装 / SDK路径

项目结构
├── 前端代码区：src/ (components/screens/navigation)
├── 原生代码区：android/ ios/
├── 配置文件：app.json / package.json / metro.config.js
└── 开发规范：目录组织 + 命名规范 + 组件结构
```

收藏这张图谱，后续章节的学习都是在这个框架上的深化和扩展。

### 1.6.5 课后实战练习与进阶拓展

理论需要实践来巩固。以下是三个层次的练习：

**基础练习（1-2小时）**：

1. 按照本章流程搭建完整的RN开发环境
2. 使用Expo创建一个TypeScript项目
3. 修改App.tsx，实现一个简单的计数器页面，包含加1和减1按钮
4. 分别在Android模拟器和iOS模拟器上运行

参考代码：

```tsx
import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

export default function App() {
  const [count, setCount] = useState(0);
  return (
    <View style={styles.container}>
      <Text style={styles.count}>{count}</Text>
      <View style={styles.btnRow}>
        <TouchableOpacity onPress={() => setCount(c => c - 1)}>
          <Text style={styles.btn}>-</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setCount(c => c + 1)}>
          <Text style={styles.btn}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  count: { fontSize: 48, fontWeight: 'bold', marginBottom: 20 },
  btnRow: { flexDirection: 'row', gap: 20 },
  btn: { fontSize: 36, padding: 16, backgroundColor: '#007AFF', color: '#fff', borderRadius: 8 },
});
```

**进阶练习（2-4小时）**：

1. 在计数器基础上增加重置按钮和历史记录功能
2. 使用AsyncStorage持久化计数器的值
3. 添加平台差异化样式（iOS和Android显示不同风格的按钮）
4. 尝试创建原生CLI版本项目，对比两种模式的差异

**拓展练习（4小时+）**：

1. 研究Metro打包配置，理解模块解析机制
2. 阅读`node_modules/react-native/`源码中的组件定义
3. 尝试开启新架构并测试同步调用原生方法的性能差异
4. 搭建CI/CD流水线，实现自动构建和发布

进阶学习资源推荐：

- RN官方文档：https://reactnative.dev/docs/getting-started
- Expo官方文档：https://docs.expo.dev
- React Navigation文档：https://reactnavigation.org
- RN新架构说明：https://reactnative.dev/docs/the-new-architecture/why
- RN社区CLI文档：https://reactnative.dev/docs/cli
- Hermes引擎文档：https://hermesengine.dev

这些资源在后续章节中会被反复引用。建议把它们加入书签，遇到问题时第一时间查阅官方文档。官方文档的准确性和时效性通常优于任何第三方教程。

> 学完本章，你应该已经具备了一个RN开发者的基本工作环境。下一章我们将深入RN的语法基础和项目配置，开始真正的编码之旅。

怕浪猫在这里多说一句：环境搭建是整个学习过程中最枯燥但最值得投入的环节。很多问题看似是"玄学报错"，本质上是环境变量配置不正确或版本不兼容。把地基打牢，后面写代码才能少踩坑、多产出。

**系列进度 1/16**

怕浪猫说：跨端这条路，入门在环境，进阶在架构，精通在原生。第一章帮你迈过最高的门槛，后面的路会越走越宽。跟着怕浪猫，16章带你从零到一拿下RN全栈开发，我们下一章见。

下一章预告：第2章《RN基础语法、项目配置与调试技巧》将深入讲解JSX移动端语法规范、TypeScript类型约束实战、列表渲染与数据处理、全场景调试工具使用，以及工程化规范配置。从"能跑起来"到"写得规范"，完成从新手到工程师的关键一跃。

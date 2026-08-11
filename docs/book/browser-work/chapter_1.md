# 第1章 浏览器演进史与 Chrome 的诞生

> 浏览器用了 30 年，从一只「网景」进化成了一座「 Chromium 帝国」，而 90% 的人只知道它叫 Chrome 。

我是怕浪猫，一个喜欢把浏览器底层拆开给你看的技术博主。从今天开始，我要带你完整拆解 Chrome 浏览器的工作原理，从架构到引擎，从渲染到网络，从安全到性能，一共 24 章。这是第 1 章，我们从一切的起点讲起：浏览器是怎么走到今天的，Chrome 又凭什么改变了游戏规则。

## 1.1 从 WorldWideWeb 到现代浏览器

### 1.1.1 早期浏览器（Mosaic、Netscape、Internet Explorer）

1990 年，Tim Berners-Lee 在欧洲核子研究组织（CERN，Conseil Européen pour la Recherche Nucléaire）写下了第一个 Web 浏览器，名字就叫 WorldWideWeb。它运行在 NeXTSTEP 操作系统上，功能极其简单：能显示文本、能点超链接、能看图片。但就是这个简陋的工具，开启了人类信息互联的时代。

1993 年，Marc Andreessen 在伊利诺伊大学开发了 Mosaic 浏览器。Mosaic 的最大贡献是让浏览器跨平台运行，同时首次支持在文本中内联显示图片，这让 Web 从纯文本世界变成了图文并茂的世界。Mosaic 的成功让 Andreessen 看到了商业机会，他随后创办了 Netscape（网景）公司。

1994 年，Netscape Navigator 1.0 发布。它是第一款真正意义上的商业浏览器，发布后几个月内就占据了超过 70% 的市场份额。Netscape 的成功带来了一个关键决策：为了保持竞争力，网景开始大量扩展 HTML 和 JavaScript 的能力，其中最著名的就是在 1995 年雇佣 Brendan Eich 在 10 天内设计出了 JavaScript 语言。

JavaScript 的诞生深刻影响了浏览器的走向。它让网页从静态文档变成了可交互的应用，但也带来了此后 20 年的兼容性噩梦。

1995 年，微软意识到互联网的威胁，在 Windows 95 的 Plus 包中捆绑了 Internet Explorer 1.0。IE 1.0 本质上是 Spyglass Mosaic 的授权改版，功能远不如 Netscape。但微软的策略很明确：免费捆绑操作系统。

这就是著名的「第一次浏览器大战」的开端。微软用了三个手段打赢了这场战争：

| 手段 | 具体做法 | 效果 |
|------|---------|------|
| 免费捆绑 | IE 随 Windows 免费，Netscape 需付费 | 切断 Netscape 收入 |
| 独家 API | ActiveX、VBScript 等仅 IE 支持 | 绑定开发者生态 |
| 系统集成 | IE 深度集成到 Windows shell | 用户无法卸载 |

到 2002 年，IE 的市场份额超过 95%，Netscape 基本退出竞争。但垄断带来了停滞：IE 6 长达 5 年没有重大更新，安全漏洞频出，Web 标准被严重忽视。

> 垄断不是技术的终点，而是停滞的起点。IE 6 用 95% 的市场份额，换来了 Web 开发最黑暗的 5 年。

### 1.1.2 浏览器大战与标准化的推进

在 IE 垄断期间，两个关键事件推动了 Web 标准化的进程。

第一个事件是 Netscape 在 1998 年开源了浏览器的源代码，成立了 Mozilla 项目。这个决策的直接原因是商业竞争失败后的背水一战，但它意外地开创了开源浏览器开发的先河。Mozilla 项目后来孕育出了 Firefox 浏览器，于 2004 年发布 1.0 版本。

Firefox 的出现打破了 IE 的垄断，带来了几个关键创新：标签页浏览（Tabbed Browsing）、扩展插件系统、以及对 Web 标准的严格遵守。Firefox 的市场份额在 2010 年左右达到 30% 的高峰。

第二个事件是 W3C（World Wide Web Consortium，万维网联盟）和 WHATWG（Web Hypertext Application Technology Working Group，Web 超文本应用技术工作组）推动的标准化工作。在 IE 垄断时期，各浏览器的行为差异巨大，开发者不得不为不同浏览器编写不同代码。标准化工作的推进让 Web 开发从「为浏览器写代码」变成了「为标准写代码」。

| 标准 | 制定组织 | 关键内容 | 影响 |
|------|---------|---------|------|
| HTML 4.01 | W3C | 规范化 HTML 结构 | 统一页面标记语言 |
| CSS 2.1 | W3C | 分离样式与结构 | 告别 table 布局 |
| ECMAScript 3 | ECMA | JavaScript 语言标准 | 统一脚本行为 |
| DOM Level 2 | W3C | 文档对象模型规范 | 统一操作接口 |

第二次浏览器大战从 2004 年 Firefox 发布开始，到 2008 年 Chrome 发布达到高潮。参与者不再只有 IE 和 Firefox，还有 Apple 的 Safari 和 Opera。竞争的焦点从市场份额转向了性能和标准兼容性，这为 Chrome 的登场铺平了道路。

> 标准化不是一纸规范，而是浏览器之间 20 年妥协与博弈的结晶。

### 1.1.3 WebKit 的起源与分支

WebKit 的故事要从 Apple 说起。2001 年，Apple 开始开发 Mac OS X 上的浏览器 Safari。最初 Apple 考虑使用 Gecko 引擎（Firefox 的引擎），但发现 Gecko 过于庞大且难以适配 macOS 的架构。

2003 年，Apple 从 KHTML（K Desktop Environment 的 HTML 引擎）和 KJS（KDE JavaScript Engine）中 fork 了一个新的引擎，命名为 WebKit。KHTML 的代码质量很高，结构清晰，Apple 在它的基础上进行了大量改进。

WebKit 的核心组件包括：

```
WebKit 引擎架构
├── WebCore（渲染引擎，负责 HTML/CSS 解析和渲染）
│   ├── HTML 解析器
│   ├── CSS 解析器
│   ├── 布局引擎
│   └── 绘制引擎
├── JavaScriptCore（JavaScript 引擎，又称 SquirrelFish / Nitro）
│   ├── 词法分析
│   ├── 语法分析
│   ├── 字节码生成
│   └── JIT 编译
└── WebKit 层（平台适配层）
    ├── Mac 端口
    ├── Windows 端口
    └── 其他平台端口
```

2005 年，Apple 将 WebKit 开源。这个决策至关重要，因为它让其他浏览器厂商可以基于 WebKit 开发自己的产品。Google 在 2008 年发布 Chrome 时，最初也是基于 WebKit 引擎。

WebKit 家族树的分支情况如下：

| 时间 | 事件 | 产物 |
|------|------|------|
| 2001 | Apple fork KHTML | WebKit |
| 2005 | WebKit 开源 | 开源社区贡献 |
| 2008 | Google 基于 WebKit 开发 | Chromium（使用 WebKit） |
| 2013 | Google fork WebKit | Blink 引擎 |
| 2013-至今 | Apple 继续 WebKit | Safari（WebKit2） |

WebKit 对浏览器生态的贡献远超多数开发者的认知。今天移动端 iOS 上所有浏览器（包括 Chrome on iOS）都被强制使用 WebKit 引擎，这是 Apple 平台策略的结果。

> WebKit 是浏览器引擎界的「共同祖先」，Safari 和 Chrome 都流淌着 KHTML 的血液，但它们最终走上了截然不同的进化道路。

## 1.2 Chrome 的诞生与设计哲学

### 1.2.1 Chromium 项目开源

2008 年 9 月 2 日，Google 发布了 Chrome 浏览器的第一个稳定版本。同时发布的还有 Chromium 开源项目，Chrome 浏览器就是基于 Chromium 构建的。

Google 进入浏览器领域的动机并不只是「做一个更好的浏览器」。当时的背景是：Web 应用（如 Gmail、Google Maps、Google Docs）正在兴起，但现有浏览器的性能和稳定性无法支撑复杂的 Web 应用体验。Google 需要一个能像操作系统一样运行 Web 应用的平台。

Chrome 的设计哲学可以总结为三个原则：

**原则一：每个标签页是一个独立进程。** 这意味着一个标签页崩溃不会影响其他标签页。这个设计在当时是革命性的，IE 和 Firefox 都采用单进程多线程模型，一个标签页崩溃往往导致整个浏览器崩溃。

**原则二：JavaScript 性能是核心竞争力。** Google 为 Chrome 开发了全新的 JavaScript 引擎 V8，首次在浏览器中引入了 JIT（Just-In-Time Compilation，即时编译）技术，让 JavaScript 的执行速度比当时的引擎快了一个数量级。

**原则三：极简界面，内容优先。** Chrome 的界面设计极其简洁，将标签页放在最顶部，地址栏和搜索框合并为 Omnibox，每个标签页有独立的首屏（New Tab Page），让用户第一时间看到内容而非浏览器 UI。

Chromium 开源项目的核心代码结构如下：

```
Chromium 源码顶层目录
├── chrome/          # Chrome 浏览器特定代码
├── content/         # Web 内容渲染核心
├── third_party/     # 第三方库（Blink、V8、Skia 等）
│   ├── blink/       # Blink 渲染引擎
│   ├── v8/          # V8 JavaScript 引擎
│   └── skia/        # 2D 图形库
├── net/             # 网络栈
├── base/            # 基础工具库
├── components/      # 可复用组件
└── build/           # 构建系统
```

Chromium 的开源策略形成了独特的生态：任何人都可以基于 Chromium 源代码构建自己的浏览器，只需添加或修改功能。这直接催生了后来的 Chromium 内核浏览器家族。

> Chromium 不是 Chrome 的附属品，而是一个足以支撑整个浏览器生态的基础设施。Google 用开源换影响力，用影响力换标准话语权。

### 1.2.2 多进程架构的革新

Chrome 的多进程架构是它最根本的设计革新。要理解这个革新的价值，先看看之前的浏览器是怎么工作的。

在 Chrome 之前，浏览器普遍采用单进程架构：

```
传统单进程浏览器架构
┌─────────────────────────────────────┐
│           浏览器进程                  │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ 标签页 A │ │ 标签页 B │ │ 标签页 C│ │
│  └─────────┘ └─────────┘ └────────┘ │
│  ┌──────────────────────────────────┐│
│  │     JavaScript 引擎（共享）        ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │     渲染引擎（共享）               ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │     网络栈（共享）                 ││
│  └──────────────────────────────────┘│
└─────────────────────────────────────┘
```

单进程架构的问题很明显：一个标签页的 JavaScript 卡死会导致整个浏览器卡死，一个标签页的内存泄漏会影响所有标签页，一个恶意网页可以利用漏洞读取其他标签页的数据。

Chrome 的多进程架构完全改变了这个模型：

```
Chrome 多进程架构（简化版）
┌──────────────┐
│ Browser 进程  │  负责 UI、标签页管理、书签等
└──────┬───────┘
       │ IPC 通信
┌──────┴───────┐ ┌──────────────┐ ┌──────────────┐
│ Renderer 进程 │ │ Renderer 进程 │ │ Renderer 进程 │
│  （标签页 A）  │ │  （标签页 B）  │ │  （标签页 C）  │
└──────────────┘ └──────────────┘ └──────────────┘
┌──────────────┐ ┌──────────────┐
│   GPU 进程    │ │ Network 进程  │
└──────────────┘ └──────────────┘
```

多进程架构带来的核心收益：

| 收益维度 | 单进程浏览器 | Chrome 多进程 |
|---------|------------|--------------|
| 稳定性 | 一个标签崩溃，全部崩溃 | 一个标签崩溃，其他不受影响 |
| 安全性 | 所有页面共享内存空间 | 进程间内存隔离，沙箱保护 |
| 性能 | 单线程 JS 阻塞全部 | 各标签页独立执行 |
| 内存管理 | 内存泄漏累积 | 关闭标签即释放内存 |

当然，多进程架构也有代价：每个进程都有基础内存开销，Chrome 的内存占用明显高于单进程浏览器。这是 Google 做出的明确权衡：用内存换稳定性和安全性。

> 多进程架构的本质不是「让浏览器变快」，而是「让浏览器不容易变慢」。稳定性是一种隐性的性能。

### 1.2.3 V8 引擎的颠覆性意义

2008 年 Chrome 发布时，最大的技术亮点不是多进程架构，而是 V8 JavaScript 引擎。V8 的出现直接改变了 JavaScript 这门语言的命运。

在 V8 之前，JavaScript 引擎（如 SpiderMonkey、JScript）主要采用解释执行的方式。解释执行的特点是启动快但运行慢，因为每次执行都需要逐行解释字节码。

V8 的核心创新是引入了 JIT（Just-In-Time Compilation，即时编译）技术。JIT 的核心思想是：在代码运行时监控哪些代码被频繁执行（热点代码，Hot Spot），然后将这些热点代码直接编译成机器码，后续执行时就跳过解释阶段，直接运行机器码。

V8 的执行流程简化版：

```
V8 执行流程（简化版）
源代码（JavaScript）
    │
    ▼
  解析器（Parser）
    │  生成 AST（Abstract Syntax Tree，抽象语法树）
    ▼
  Ignition 解释器
    │  生成字节码并解释执行
    │  同时收集类型反馈（Type Feedback）
    ▼
  TurboFan 编译器（热点代码触发）
    │  基于类型反馈编译为优化机器码
    ▼
  机器码执行（性能接近原生）
```

V8 的 JIT 编译让 JavaScript 的执行速度提升了 10 倍以上。这不仅仅是 Chrome 的胜利，更是整个 Web 平台的胜利。没有 V8 的性能突破，Node.js（2009 年发布）就不可能出现，JavaScript 作为服务端语言的路径就不存在。

V8 的另一个重要创新是隐藏类（Hidden Classes，也称为 Shapes 或 Maps）。JavaScript 是动态类型语言，属性可以随时添加和删除，这使得属性访问的优化非常困难。V8 通过隐藏类机制，在对象背后维护一个类信息结构，让动态语言的属性访问接近静态语言的性能。

> V8 不是让 JavaScript 变快了，而是让 JavaScript 有资格被认真对待了。从浏览器到服务器，V8 把 JavaScript 从「玩具语言」变成了「基础设施语言」。

## 1.3 现代浏览器竞争格局

### 1.3.1 Blink 引擎独立

2013 年 4 月，Google 做出了一个重要决策：从 WebKit 中 fork 出独立的渲染引擎，命名为 Blink。

这个决策的直接原因是 WebKit 的架构包袱。WebKit 的代码中包含了大量 Apple 为 macOS 设计的抽象层，这些抽象层在 Chromium 的多进程架构中显得多余且低效。Google 和 Apple 对 WebKit 的发展方向也有分歧：Google 希望支持多进程架构，而 Apple 坚持单进程模型。

Blink 独立后的关键变化：

| 变化领域 | WebKit 时代 | Blink 独立后 |
|---------|------------|-------------|
| 进程模型 | 抽象层适配 Chrome 的多进程 | 原生多进程设计 |
| 代码量 | 约 440 万行 | 初始减少约 400 万行 |
| 布局引擎 | 传统布局系统 | LayoutNG（2019 年重构） |
| 解析器 | 旧版 HTML 解析器 | HTMLParser 重写 |
| 垃圾回收 | Oilpan GC 引入 | Oilpan 持续优化 |

Blink 独立后的发展速度远超 WebKit。Google 投入了大量工程资源重构 Blink 的核心子系统，包括布局引擎（LayoutNG）、绘制系统（PaintNG）和合成器。这些重构让 Blink 的代码更清晰、性能更好、维护成本更低。

Blink 和 WebKit 的分化也意味着 Web 开发者需要面对更多的兼容性问题。虽然两个引擎都遵循 Web 标准，但实现细节和 bug 的差异在实际开发中仍然存在。这也是为什么跨浏览器测试在 Web 开发中如此重要。

> Fork 不是分裂，而是进化加速。Blink 和 WebKit 的分化，让 Web 引擎的竞争从「一个引擎两个壳」变成了「两个引擎各自的进化竞赛」。

### 1.3.2 Chromium 内核生态（Edge、Brave、Opera 等）

Chromium 开源项目催生了一个庞大的浏览器家族。这些浏览器共享 Chromium 内核（Blink 渲染引擎 + V8 JavaScript 引擎），但在上层有各自的产品策略和差异化功能。

主流 Chromium 内核浏览器一览：

| 浏览器 | 开发商 | 差异化定位 | 内核版本 |
|--------|--------|----------|---------|
| Google Chrome | Google | 全功能浏览器，深度集成 Google 服务 | 跟随 Chromium 主线 |
| Microsoft Edge | Microsoft | Windows 默认浏览器，集成 Microsoft 365 | 跟随 Chromium 主线 |
| Brave | Brave Software | 隐私优先，内置广告拦截 | 跟随 Chromium 主线 |
| Opera | Opera Software | 内置 VPN 和侧边栏工具 | 跟随 Chromium 主线（延迟数版本） |
| Vivaldi | Vivaldi Technologies | 高度可定制，面向高级用户 | 跟随 Chromium 主线 |
| Arc | The Browser Company | 空间化标签管理，重新设计交互 | 跟随 Chromium 主线 |

Chromium 内核生态的形成有一个重要意义：Web 开发者只需要针对 Chromium 引擎做一次适配，就能覆盖 80% 以上的桌面浏览器用户。这大幅降低了开发和测试成本。

但 Chromium 生态的壮大也带来了「Chromium 垄断」的担忧。如果所有浏览器都使用 Chromium 内核，Web 标准的实际解释权就会集中在 Google 手中。这也是为什么 Firefox（Gecko 引擎）和 Safari（WebKit 引擎）的独立存在如此重要。

Web 引擎多样性对比：

```
2024 年浏览器引擎格局
┌─────────────────────────────────────────────────┐
│  Chromium 系（Blink + V8）                        │
│  Chrome | Edge | Brave | Opera | Vivaldi | Arc   │
│  桌面市场份额：约 75%                              │
├─────────────────────────────────────────────────┤
│  WebKit 系（WebKit + JavaScriptCore）             │
│  Safari（桌面 + iOS 全部浏览器）                    │
│  桌面市场份额：约 10%                              │
│  移动市场份额：约 25%（iOS 全部）                   │
├─────────────────────────────────────────────────┤
│  Gecko 系（Gecko + SpiderMonkey）                 │
│  Firefox                                          │
│  桌面市场份额：约 8%                               │
└─────────────────────────────────────────────────┘
```

从这张图可以看到，Chromium 已经成为 Web 的事实标准引擎。但这并不意味着所有浏览器的行为完全一致，因为各浏览器厂商会在 Chromium 基础上做不同程度的修改和定制。

> 三足鼎立（Blink、WebKit、Gecko）比一家独大更健康。引擎的多样性是 Web 平台抵御单点控制的最后防线。

## 本章核心知识总结

回顾本章内容，浏览器从 1990 年的 WorldWideWeb 起步，经历了 Netscape 与 IE 的第一次浏览器大战，Firefox 的崛起与标准化推进，最终在 2008 年迎来了 Chrome 的诞生。

Chrome 的三大革新改变了浏览器的发展方向：

| 革新 | 解决的核心问题 | 影响 |
|------|--------------|------|
| 多进程架构 | 稳定性和安全性 | 每个标签页独立运行，崩溃隔离 |
| V8 引擎 | JavaScript 性能瓶颈 | JIT 编译让 JS 接近原生速度 |
| Chromium 开源 | 生态建设 | 催生 Chromium 浏览器家族 |

2013 年 Blink 从 WebKit 独立后，Chromium 生态进一步壮大，Edge、Brave、Opera 等浏览器相继采用 Chromium 内核，形成了今天的浏览器竞争格局。

浏览器演进的关键时间线：

| 年份 | 事件 | 意义 |
|------|------|------|
| 1990 | WorldWideWeb 诞生 | Web 的起点 |
| 1993 | Mosaic 发布 | 图文并茂的 Web |
| 1994 | Netscape Navigator 发布 | 商业浏览器时代 |
| 1995 | IE 1.0 发布 | 第一次浏览器大战 |
| 1995 | JavaScript 诞生 | Web 可交互 |
| 1998 | Mozilla 项目启动 | 开源浏览器 |
| 2002 | IE 市场份额 95% | 垄断与停滞 |
| 2004 | Firefox 1.0 发布 | 第二次浏览器大战 |
| 2008 | Chrome 发布 + V8 引擎 | 多进程 + JIT 革新 |
| 2013 | Blink 从 WebKit 独立 | Chromium 生态独立 |

觉得有用？收藏起来，下次想回顾浏览器发展史的时候直接翻出来看。

你第一次用浏览器是什么时候？IE 还是 Netscape？评论区说说你的浏览器启蒙故事。

关注怕浪猫，下期我们讲 Chrome 的多进程架构到底是怎么运作的，每个进程各自干了什么活。系列进度 1/24，这是《深入理解 Chrome 浏览器工作原理》系列的第一篇，整个系列会带你从浏览器历史一路拆到 AI 集成，不要错过。

下期预告：第 2 章「Chrome 多进程架构详解」。我们会拆解 Browser 进程、Renderer 进程、GPU 进程、Network 进程各自的职责，讲清楚 Mojo IPC（Inter-Process Communication，进程间通信）框架是怎么让这些进程协作的，以及站点隔离（Site Isolation）是如何从架构层面防御安全攻击的。怕浪猫下期见。

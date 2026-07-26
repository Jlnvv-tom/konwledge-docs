# 第9章 主流UI组件库与企业级页面实战开发

做过RN（React Native）开发的同学应该都有过这种体验：产品经理给了一张设计稿，你盯着屏幕看了半天，心里默念"这玩意儿用View和Text也能堆出来吧"，然后吭哧吭哧写了三百行代码，最后发现滚动有问题、阴影不对、点击态没了。更惨的是，下一个页面又要从头来一遍。更更惨的是，设计稿又改了，你发现改一个颜色要动二十个文件。

我是怕浪猫，一只在RN坑里摸爬滚打多年的老猫。从RN 0.40版本一路走到现在的0.75新架构，踩过的UI（User Interface）坑比我吃的鱼还多。今天这篇文章，怕浪猫就带你把RN主流UI组件库一次性选透、配透、用透，最终落地到企业级页面的完整开发流程中。从选型对比到主题定制，从表单校验到业务页面综合实战，全链路踩坑经验打包送上。这一章是整个系列中实战性最强的章节之一，建议边读边对照自己的项目代码。

> 组件库不是万能的，但没有组件库是万万不能的。选对了，开发效率翻三倍；选错了，维护成本翻十倍。怕浪猫见过太多团队因为组件库选型失误导致后期重写的故事了。

## 9.1 RN UI组件库选型与对比

在RN生态中，UI组件库的选择远比Web端复杂。Web端有Ant Design、Material UI、Element Plus等成熟方案，生态繁荣且组件覆盖全面，选哪个都不会出大问题。但RN生态的组件库在维护活跃度、跨端能力、主题定制深度上差异巨大，有的组件库去年还在更新今年就停更了，有的组件库iOS表现优秀但Android端一堆兼容问题，选错一个可能就是整个团队半年的技术债。怕浪猫见过最惨的案例是一个团队选了一个已停更的组件库，用了半年发现Bug无人修复，最后不得不花两个月时间整体替换组件库。

### 9.1.1 Ant Design RN组件库特性解析

Ant Design React Native（社区中常简称为 antd-mobile-rn）是蚂蚁集团开源的RN组件库，完整继承了Ant Design的设计语言体系。它的核心优势在于：与企业级后台管理系统的设计风格高度一致。如果你公司的中后台系统用的是Ant Design，那移动端选它几乎零视觉适配成本，设计师交付的标注稿和组件库的默认表现高度吻合，开发同学不需要反复调色、调间距、调圆角，大幅减少了前端和设计团队之间的沟通成本。

antd-mobile-rn的设计Token体系与Web版Ant Design保持高度一致，这意味着同一套设计规范可以同时覆盖Web后台和移动端App，对于有全产品线统一设计诉求的企业来说，这是选择它最核心理由。另外它的组件API设计风格也与Web版保持一致，如果团队成员有Ant Design Web的开发经验，迁移到RN版本几乎不需要额外学习成本。

核心特性一览：

| 维度 | 说明 |
|------|------|
| 组件数量 | 四十余个高频业务组件 |
| 设计语言 | Ant Design 5.x 设计规范 |
| 主题定制 | 基于 ConfigProvider 配合 Design Token |
| 暗黑模式 | 内置支持，可跟随系统或手动切换 |
| TypeScript支持 | 完整的类型定义文件 |
| 维护状态 | 活跃更新中，社区问题响应较快 |

来看一个最基础的按钮使用示例，感受一下API的设计风格：

```jsx
import { Button } from '@ant-design/react-native';

function DemoButton() {
  return (
    <Button type="primary" onPress={() => console.log('clicked')}>
      提交
    </Button>
  );
}
```

官方文档地址：https://rn.mobile.ant.design/

antd-mobile-rn的TypeScript（简称TS）类型支持比较完善，几乎每个组件都有完整的Props定义，配合IDE的智能提示可以快速上手。但要注意一个关键坑点：它的部分组件（比如DatePicker、Picker）依赖Popup弹层，在Android（安卓）平台上需要额外处理SafeArea（安全区域），否则会出现弹层遮挡系统导航栏的问题。怕浪猫在实际项目中遇到过这个坑，Picker弹出后底部被虚拟导航键盖住，用户无法操作确认按钮。解决方案是在Picker外层包一个SafeAreaView，或者通过insets（插入值）API手动计算偏移。

另外需要特别说明的是，antd-mobile-rn的更新节奏和Ant Design Web版不完全同步。Web版已经到5.x大版本，而RN版部分组件还停留在等价于Web版4.x的阶段。如果你们设计稿是基于最新版Ant Design Web设计的，有可能会发现部分组件的视觉细节和RN版不统一。这种情况下需要通过主题定制微调。

### 9.1.2 NativeBase全端适配组件库优势

NativeBase是GeekyAnts团队出品的老牌RN组件库，在社区中有着广泛的使用基础和较高的知名度。它最大的卖点是其跨平台能力——同一套组件代码可以运行在RN Web、iOS、Android三个平台上。对于需要同时维护App和小程序Web版本、或者需要做H5降级页面的团队来说，这个能力非常有价值，可以大幅减少多端适配的重复开发工作量。

NativeBase在GitHub上的Star数超过两万，社区生态相对成熟。它的文档质量在三大RN组件库中是最好的，几乎每个组件都有可运行的示例代码和完整的Props说明表。另外NativeBase的维护团队GeekyAnts本身就是一个专做RN开发的技术公司，对RN生态的理解非常深入，这也是它维护质量有保障的重要原因。

NativeBase 3.x版本经历了一次彻底的重构，基于styled-system重构后，采用了类似Tailwind的utility-first（工具类优先）样式方案。这意味着你可以通过props来控制样式，而不需要写冗长的StyleSheet：

核心架构层次解析：

```
NativeBase 3.x 架构分层

┌─────────────────────────────────┐
│         Your App Code           │
├─────────────────────────────────┤
│     NativeBase Components       │
│  (Button, Card, Form, Modal...) │
├─────────────────────────────────┤
│    styled-system / hooks        │
│  (props驱动的样式引擎)            │
├─────────────────────────────────┤
│  React Native Primitives        │
│  (View, Text, TouchableOpacity) │
├─────────────────────────────────┤
│    Platform (iOS/Android/Web)   │
└─────────────────────────────────┘
```

这种分层架构的好处是组件层面的样式逻辑高度可复用。来看一个实际的卡片组件写法：

```jsx
import { Button, VStack, Text } from 'native-base';

function DemoCard() {
  return (
    <VStack space={4} p={4} bg="white" rounded="lg" shadow={2}>
      <Text fontSize="lg" fontWeight="bold">标题</Text>
      <Button colorScheme="primary" size="md">操作</Button>
    </VStack>
  );
}
```

官方文档地址：https://docs.nativebase.io/

上面这段代码完全没有用到StyleSheet.create，所有样式都通过props表达。`space={4}`是子元素间距，`p={4}`是内边距，`bg="white"`是背景色，`rounded="lg"`是大圆角，`shadow={2}`是阴影等级。这种写法的好处是样式和结构在同一行，阅读组件代码时不需要在JSX和StyleSheet之间跳来跳去，对提升代码可读性和降低维护成本有明显帮助。

不过NativeBase 3.x也有几个明显的短板需要认真评估。首先是包体积较大，压缩后约320KB，对于追求首屏加载速度的应用来说这个体积不可忽视。在一个中等规模的项目中，NativeBase加上React Native本身和必要的原生桥接库，总包体积很容易超过5MB。其次，它的默认主题风格偏Material Design（Google的Material Design设计规范），如果你的设计稿是iOS风格，组件的圆角、阴影、配色都需要大量定制工作。最后，styled-system的运行时样式计算会有一定的性能开销，在低端Android设备上渲染包含大量组件的长列表时可能感受到明显的卡顿。怕浪猫在一个项目中测试过，在红米入门机型上渲染包含100个NativeBase组件的列表，帧率会从60帧下降到40帧左右。

### 9.1.3 UI Kitten主题化组件库特点

UI Kitten是Akveo团队出品的RN组件库，在三大组件库中它的知名度相对较低，但在特定场景下它可能是最佳选择。它的核心特色是极其强大的主题化能力。它采用EVA Theme引擎，允许你通过JSON配置文件定义完整的主题体系，包括颜色、字体、间距等所有设计Token，甚至可以为每个组件的每个变体定义独立的样式。

基础使用方式：

```jsx
import { ApplicationProvider, Button } from '@ui-kitten/components';
import * as eva from '@eva-design/eva';

function App() {
  return (
    <ApplicationProvider {...eva} theme={eva.light}>
      <Button>HELLO</Button>
    </ApplicationProvider>
  );
}
```

UI Kitten的mapping system（主题映射系统）是其核心竞争力。它允许你定义组件级别的样式覆盖，比如为Button的primary变体指定不同的圆角和阴影。这种细粒度的主题控制在其他组件库中很难实现。举个实际的例子：你可以在主题JSON中配置Button的primary变体在small尺寸下使用更小的圆角和更轻的阴影，而在large尺寸下使用更大的圆角和更重的阴影，所有这些配置都不需要改一行组件代码。

官方文档地址：https://akveo.github.io/react-native-ui-kitten/

但UI Kitten的学习曲线相对陡峭。自定义主题需要理解EVA Design System的JSON Schema结构，这个Schema的嵌套层级比较深，初学者容易在配置文件中迷失。另外UI Kitten的社区生态不如前两个库活跃，遇到问题能搜到的解决方案相对较少，更多时候需要直接翻官方源码。

> 组件库选型就像选兵器，没有最强的，只有最趁手的。团队熟悉度、设计稿风格、维护活跃度，三个维度缺一不可。不要被Star数迷惑，适合自己团队的才是最好的。

### 9.1.4 轻重型组件库项目选型原则

光了解三个主流组件库还不够，实际项目中的选型决策不是单纯比功能多少或者Star数高低，而是要匹配项目阶段、团队能力和长期维护策略。一个常见的选型误区是看哪个组件库Star多就选哪个，但Star数高不等于适合你的项目——如果你们的场景是极致性能要求的嵌入式设备配套App，一个轻量自研库可能比任何热门组件库都合适。怕浪猫把选型决策整理成一张完整的决策表，你对照自己团队的实际情况就能得出结论：

| 选型因素 | antd-mobile-rn | NativeBase | UI Kitten | 自研轻量库 |
|---------|---------------|------------|-----------|-----------|
| 上手成本 | 低（Ant生态熟悉） | 中等 | 偏高 | 高（需自建文档） |
| 包体积 | 中等（约180KB） | 偏大（约320KB） | 中等（约210KB） | 极低 |
| 主题定制能力 | 中等 | 强大 | 极强 | 完全自由 |
| 跨端能力 | 仅RN | RN加Web | 仅RN | 取决于实现 |
| 社区活跃度 | 中等 | 高 | 中等 | 无 |
| 适合场景 | 企业后台移动端 | 全端统一项目 | 设计驱动型产品 | 极致性能要求 |

选型原则总结如下，怕浪猫按项目场景给出明确建议：

**中小团队、快速验证阶段**：优先选择antd-mobile-rn。上手快，TypeScript支持好，如果你的团队之前做过Ant Design的Web项目，同事们几乎零学习成本。组件API设计风格一致，上手时间可以控制在半天以内。

**全端统一、需要Web端复用**：选择NativeBase。一套代码三端跑，大幅节省人力。但要注意包体积和性能问题，在低端设备上需要做针对性优化。

**设计团队强势、主题多变**：选择UI Kitten。主题引擎强大到可以为每个页面定制不同风格。适合那种设计师对视觉细节要求极高、主题配置需要灵活到组件级别变体的项目。

**性能极致要求、组件需求少**：自研轻量库。只封装项目真正需要的组件，包体积控制在50KB以内。这条路前期投入大但后期回报高，适合长期维护的产品型项目。

### 9.1.5 企业UI库落地最佳实践

企业级项目落地UI库不是装个包就开始用这么简单。怕浪猫根据多个项目的实际落地经验，总结了一套"三步走"策略，按这个流程走可以避免大部分后期返工。这个策略的核心思想是：先调研再决策，先验证再全面推开，不跳步骤不偷懒。

**第一步：组件审计**。把设计稿中所有页面拆解到组件级别，统计高频组件的出现次数。比如Button在二十个页面中出现了，Card在十五个页面中出现了，表单类组件在八个页面中出现了。形成一份组件需求清单，标注每个组件的使用频率和交互复杂度。这份清单是你选型的基准依据，没有它选型就是拍脑袋。

**第二步：能力映射**。拿需求清单逐项对比候选UI库的API文档，标记"原生支持"、"需要二次封装定制"、"完全不支持"三类。如果某个UI库不支持的比例超过百分之三十，直接淘汰，不要抱有"自己补一下"的幻想，后期补的代价远大于前期换一个库的代价。

**第三步：POC（Proof of Concept，概念验证）验证**。选排名前两位的UI库，各做一个包含列表页、详情页、表单页的迷你项目，跑通iOS和Android双端。重点验证以下指标：首屏渲染时间、列表滚动流畅度、暗黑模式切换是否有闪烁、TypeScript类型是否完整。POC阶段暴露的问题往往比正式开发中遇到的更真实。

> 调研一周不如写两天POC。纸上得来终觉浅，绝知此事要躬行。怕浪猫见过太多团队只看了文档就做选型决策，结果开发到一半发现各种不兼容，进退两难。

落地后还需要建立组件使用规范文档，明确三个边界：哪些场景直接使用UI库原生组件、哪些场景需要二次封装（比如统一加埋点、加防抖）、哪些场景必须自研。规范文档不是摆设，怕浪猫见过太多项目因为团队成员各用各的组件库、各按各的理解封装组件，导致同样的按钮在十个页面有十种写法，后期维护成本高到令人发指。

## 9.2 组件库安装与全局配置

### 9.2.1 依赖安装与版本适配处理

选型完成后就进入安装配置阶段。以antd-mobile-rn为例，安装过程看似就是一行npm install命令的事，但实际操作中版本兼容性是第一个坑。RN 0.72及以上版本需要使用antd-mobile-rn的5.x版本，如果使用低版本会出现React 18的Hooks（钩子函数）兼容问题，表现为组件卸载后尝试更新状态导致控制台报错Can not perform a React state update on an unmounted component。这种警告在开发阶段可能只是控制台的一行黄字提示，但在生产环境中可能导致内存泄漏。

```bash
# 安装主包
npm install @ant-design/react-native@^5.2.0

# 安装 peer dependencies（依赖同伴包）
npm install @react-native-community/segmented-control \
  @react-native-picker/picker \
  @react-native-community/datetimepicker

# iOS端额外操作
cd ios && pod install && cd ..
```

版本兼容对照表，安装前务必核对：

| antd-mobile-rn | React Native | React |
|----------------|-------------|-------|
| 5.x | 0.72及以上 | 18及以上 |
| 4.x | 0.68到0.71 | 17及以上 |
| 3.x | 0.60到0.67 | 16及以上 |

安装peer dependencies（依赖同伴包）时最容易踩的坑是漏装。antd-mobile-rn的Picker、DatePicker等组件依赖`@react-native-picker/picker`这个原生桥接包，如果你只装了主包而漏装了peer包，JavaScript层面不会报错，但运行时一旦打开Picker就会直接红屏，报错信息为"Cannot find module"。怕浪猫建议在项目README中把所有peer dependencies显式列出来，新人clone项目后npm install不会遗漏。

另外一个安装阶段的细节坑：iOS端的CocoaPods（iOS依赖管理器）有时会因为缓存问题导致pod install失败。遇到这种情况，先执行`pod cache clean --all`清理缓存，再重新执行`pod install`。如果还失败，删掉ios目录下的Pods文件夹和Podfile.lock文件后重试。

### 9.2.2 全局Provider注入与初始化

组件库安装完成后，需要在App根节点注入Provider（上下文提供者），让全局所有组件都能访问主题配置、国际化资源等上下文数据。这一步看似简单但坑点不少，很多初学者在这一步栽跟头，导致后续各种莫名其妙的渲染问题。

```jsx
// App.tsx 根组件初始化
import { Provider as AntdProvider } from '@ant-design/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';

function App() {
  return (
    <SafeAreaProvider>
      <AntdProvider>
        <NavigationContainer>
          <RootStack />
        </NavigationContainer>
      </AntdProvider>
    </SafeAreaProvider>
  );
}
```

Provider嵌套顺序非常重要，不能随意调整。SafeAreaProvider必须在最外层，因为它为整个应用提供安全区域信息，所有子组件都可能需要消费这个上下文。AntdProvider在中间层，为所有antd组件提供主题上下文。NavigationContainer在最内层，管理路由栈。

如果顺序搞反了会出现什么问题？怕浪猫亲身经历过：把AntdProvider放在SafeAreaProvider外面，结果iOS刘海屏顶部内容被遮挡，因为antd的Modal组件在计算弹出位置时无法获取到SafeArea的inset值。又把NavigationContainer放在最外层，结果Android底部TabBar被虚拟导航键盖住。这些问题的排查非常耗时，因为它们不会在开发阶段的低分辨率模拟器上暴露，只在真机特别是大屏设备上才出现。

### 9.2.3 安卓iOS双端兼容适配

双端适配是RN开发永恒的话题。即使是用了统一组件库，iOS和Android的渲染差异依然广泛存在——从安全区域处理到字体渲染、从明影效果到滚动回弹、从点击反馈到键盘行为，每个环节都可能有双端差异需要处理。怕浪猫整理了一份双端差异适配清单，这是每个RN开发者都应该收藏的实战参考：

| 适配项 | iOS表现 | Android表现 | 解决方案 |
|-------|---------|------------|---------|
| 安全区域 | 刘海/灵动岛遮挡 | 状态栏/导航键遮挡 | SafeAreaProvider统一处理 |
| 字体渲染 | SF Pro系统字体 | Roboto系统字体 | Platform.select分别配置 |
| 阴影效果 | 原生shadow API支持 | 需用elevation属性 | Platform.select分支处理 |
| 滚动回弹 | 自动支持弹性回弹 | 需配置overScrollMode | 分别设置bounces和overScrollMode |
| 点击涟漪 | 无涟漪效果 | Material Ripple效果 | TouchableOpacity统一处理 |
| 键盘弹出 | 软键盘覆盖内容 | 窗口resize | KeyboardAvoidingView分别配置 |

阴影适配是最常见的双端差异之一，也是新人最容易踩的坑。iOS使用shadowColor、shadowOffset等CSS-like属性，而Android使用elevation一个属性搞定。写法完全不同，必须用Platform.select分支处理：

```jsx
import { Platform, View } from 'react-native';

const cardShadow = Platform.select({
  ios: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  android: {
    elevation: 3,
  },
});

function Card({ children }) {
  return <View style={[cardShadow, { backgroundColor: '#fff', borderRadius: 8 }]}>{children}</View>;
}
```

### 9.2.4 初始化报错兼容修复方案

组件库初始化阶段常见的报错有三种，怕浪猫逐一给出原因分析和修复方案。这些报错都是实际项目中高频出现的，很多新手遇到后不知道如何排查，浪费大量时间在搜索引擎上找答案。

**报错一：Unable to resolve module `@react-native-picker/picker`**

原因分析：peer dependencies未安装或安装后未正确链接。antd-mobile-rn的Picker组件在运行时动态加载这个原生桥接包，如果找不到就会报模块解析失败。修复方案就是补装依赖，iOS端执行pod install，Android端执行`./gradlew clean`后重新构建。

**报错二：TypeError: Cannot read property 'borderRadiusSE' of undefined**

原因分析：主题对象未正确注入到组件树中。这通常发生在组件渲染时尝试读取主题Token但获取到undefined。检查AntdProvider是否包裹在组件树最外层，确认没有在子组件中重复渲染Provider导致上下文被覆盖。还有一种可能是自定义主题对象的结构不完整，缺少了某些必要的Token层级。

**报错三：Android运行时 java.lang.IllegalStateException: Unable to load script**

原因分析：Hermes Engine（Facebook开发的JS引擎）未正确启用。Hermes可以显著提升RN应用的启动速度和运行性能，但需要在构建配置中显式启用。检查android/app/build.gradle中的配置：

```gradle
project.ext.react = [
    enableHermes: true
]
```

然后执行`cd android && ./gradlew clean`清理构建缓存后重新构建。如果是在升级RN版本后出现这个问题，还需要检查是否需要更新Hermes版本号。

### 9.2.5 组件按需引入规范配置

antd-mobile-rn理论上支持Tree Shaking（摇树优化），但由于RN的Metro Bundler（打包工具）对ES Module的Tree Shaking支持有限，实际效果并不理想。要实现真正的按需引入，需要配合babel-plugin-import插件在编译阶段做引入路径转换。配置方式如下：

```js
// babel.config.js
module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    ['import', {
      libraryName: '@ant-design/react-native',
      libraryDirectory: 'es/components',
    }],
  ],
};
```

配置完成后，你的import语句在编译阶段会被自动转换为按路径引入：

```jsx
// 你写的代码
import { Button, Card } from '@ant-design/react-native';

// 编译后实际加载的（你看不到，但打包工具会处理）
import Button from '@ant-design/react-native/es/components/button';
import Card from '@ant-design/react-native/es/components/card';
```

这样未使用的组件不会被打包进最终的Bundle包中，有效减小应用体积。在一个使用antd-mobile-rn的中型项目中，配置按需引入后Bundle体积减少了约60KB，效果显著。

> 按需引入不是可选项，是企业级项目的必选项。少打包一个无用组件，首屏加载就快一点，用户体验就好一分。每一个字节都是真金白银。

## 9.3 全局主题与个性化样式定制

### 9.3.1 品牌主色调自定义覆盖配置

企业级应用通常有统一的品牌色规范，需要覆盖组件库的默认主题色。antd-mobile-rn通过Theme（主题）配置对象来实现品牌色覆盖。核心原理是：组件库内部所有组件的颜色值不硬编码，而是从Theme Token中读取。你只需要覆盖对应的Token值，所有引用该Token的组件会自动更新。

```jsx
import { Provider, Theme } from '@ant-design/react-native';

const theme = {
  ...Theme,
  brand_primary: '#1677FF',
  color_link: '#1677FF',
  primary_button_fill: '#1677FF',
  tabs_pager_color: '#1677FF',
};

function App() {
  return (
    <Provider theme={theme}>
      <RootStack />
    </Provider>
  );
}
```

理解主题Token体系的分类对高效定制至关重要。怕浪猫把核心Token按类别整理：

```
主题Token分类体系

颜色Token（color）
├── brand_primary        品牌主色，影响按钮、链接等
├── color_text_base      基础文字色
├── color_text_placeholder 占位提示文字色
├── fill_base            基础填充色，即背景色
├── fill_tap             点击态填充色
└── border_color_base    基础边框色

尺寸Token（size）
├── font_size_heading    标题字号
├── font_size_caption    说明文字字号
├── height_base          基础组件高度
├── h_spacing            水平间距
└── v_spacing            垂直间距

圆角Token（radius）
├── radius_xs            超小圆角，4px
├── radius_sm            小圆角，6px
├── radius_md            中圆角，8px
└── radius_lg            大圆角，12px
```

掌握了Token分类，做主题定制就有的放矢了。改品牌色就动color类的Token，改间距就动size类的Token，改圆角就动radius类的Token。不需要去改每个组件的Props，一处配置全局生效。

### 9.3.2 亮色/暗黑模式切换实现

暗黑模式（Dark Mode）已经是移动应用的标配功能。自从苹果和谷歌在系统层面引入暗黑模式后，用户对App的暗黑模式支持已经从锦上添花变成了基本期望。用户期望App能跟随系统设置自动切换主题，或者手动选择亮色、暗黑模式。实现原理是维护两套主题Token，根据系统设置或用户选择动态替换Provider传入的theme对象。暗黑模式不仅仅是把白色背景换成黑色那么简单，还需要调整文字颜色、边框颜色、阴影深度、图标色调等所有视觉元素，确保在暗色背景下依然有良好的可读性和层次感。

```jsx
import { useColorScheme } from 'react-native';
import { Provider, Theme } from '@ant-design/react-native';

const lightTheme = {
  ...Theme,
  brand_primary: '#1677FF',
  fill_base: '#FFFFFF',
  color_text_base: '#333333',
};

const darkTheme = {
  ...Theme,
  brand_primary: '#1668DC',
  fill_base: '#1A1A1A',
  color_text_base: '#E5E5E5',
};

function App() {
  const scheme = useColorScheme();
  const theme = scheme === 'dark' ? darkTheme : lightTheme;
  return <Provider theme={theme}><RootStack /></Provider>;
}
```

但这只是最基础的实现，只能跟随系统设置。企业级应用需要考虑三个场景：跟随系统、强制亮色、强制暗黑。用户可能希望在亮色系统中也使用暗黑模式保护眼睛，也可能在暗色系统中强制使用亮色模式以保证可读性。怕浪猫建议用一个自定义的ThemeContext来统一管理主题模式状态：

```jsx
import { createContext, useContext, useState } from 'react';

const ThemeModeContext = createContext();

function ThemeModeProvider({ children }) {
  const [mode, setMode] = useState('system');
  const systemScheme = useColorScheme();
  const isDark = mode === 'system' ? systemScheme === 'dark' : mode === 'dark';
  const theme = isDark ? darkTheme : lightTheme;
  return (
    <ThemeModeContext.Provider value={{ mode, setMode, isDark }}>
      <Provider theme={theme}>{children}</Provider>
    </ThemeModeContext.Provider>
  );
}

export const useThemeMode = () => useContext(ThemeModeContext);
```

这样任何页面都能通过`useThemeMode()`这个Hook（钩子函数）获取当前主题模式并手动切换。在设置页面放一个三选一的选择器，用户体验完整且可控。

### 9.3.3 字体、圆角、尺寸统一规范

企业级UI规范通常定义了一套完整的设计变量体系，涵盖颜色、字体、圆角、间距等所有维度。这些变量是设计团队和开发团队之间的契约——设计师在Figma中定义变量值，开发在代码中实现对应的Token配置，两边保持同步。怕浪猫建议把所有设计变量集中到一个独立的配置文件中管理，而不是散落在各处。这样做的好处是：当设计团队修改了某个值，你只需要改一个地方，全应用自动同步更新，不需要全局搜索替换。

```js
// theme/tokens.js - 全局设计变量配置
export const tokens = {
  color: {
    primary: '#1677FF',
    success: '#00B96B',
    warning: '#FAAD14',
    error: '#FF4D4F',
    textPrimary: '#333333',
    textSecondary: '#666666',
    textHint: '#999999',
    bgPrimary: '#FFFFFF',
    bgSecondary: '#F5F5F5',
  },
  font: {
    sizeCaption: 12,
    sizeBody: 14,
    sizeTitle: 16,
    sizeHeading: 18,
    sizeDisplay: 22,
    weightRegular: '400',
    weightMedium: '500',
    weightBold: '600',
  },
  radius: { small: 4, medium: 8, large: 12, pill: 999 },
  spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 },
};
```

这套Token体系与设计团队的Figma变量保持一一对应关系。设计师在Figma中修改了Primary Color的值，开发只需要改tokens.js中对应的一行代码，全应用所有引用primary颜色的地方自动更新。这种设计变量和代码变量的同步机制是大型项目UI一致性的基石。

### 9.3.4 个性化品牌UI风格定制

品牌风格定制不只是换一个主色调那么简单，还包括字体族选择、图标库定制、动效曲线调整、阴影深度规范、间距节奏设定等多个维度。每一个维度都在向用户传递品牌的调性和气质。怕浪猫以一个电商品牌为例，展示完整的品牌风格定制方案。假设这个电商品牌的视觉风格定位为：橙色系主色调传达活力与热情、大圆角传达亲和力与安全感、疏朗布局传达高端感与品质感、中等字号增强可读性。

```jsx
import { Platform } from 'react-native';
import { Theme } from '@ant-design/react-native';

export const brandTheme = {
  ...Theme,
  brand_primary: '#FF6B35',
  primary_button_fill: '#FF6B35',
  color_link: '#FF6B35',
  radius_md: 12,
  radius_lg: 16,
  font_size_heading: 18,
  font_size_caption: 13,
  v_spacing: 16,
  h_spacing: 16,
};

export const brandFont = Platform.select({
  ios: { fontFamily: 'PingFangSC-Medium' },
  android: { fontFamily: 'sans-serif-medium' },
});
```

> 品牌不是Logo的颜色，品牌是用户每次打开App时感受到的那份"熟悉感"。主题Token就是你把品牌感注入代码的管道。每一个Token的改动，都在塑造用户对品牌的感知。

### 9.3.5 主题配置本地持久化存储

用户在设置页面切换了暗黑模式，下次打开App时应该记住上次的选择，而不是每次都回到默认的跟随系统模式。这种记忆用户偏好的能力是提升用户留存和使用体验的重要细节。这就需要把主题配置持久化到本地存储，在App启动时读取并应用。

```jsx
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useState } from 'react';

const THEME_KEY = '@app_theme_mode';

function usePersistentTheme() {
  const [mode, setMode] = useState('system');

  useEffect(() => {
    AsyncStorage.getItem(THEME_KEY).then((saved) => {
      if (saved) setMode(saved);
    });
  }, []);

  const updateMode = (newMode) => {
    setMode(newMode);
    AsyncStorage.setItem(THEME_KEY, newMode);
  };

  return { mode, updateMode };
}
```

这里有一个容易被忽略的细节坑：AsyncStorage（异步本地存储）的读取是异步操作。App冷启动时，JavaScript层面会先使用默认值`system`渲染界面，然后异步存储读取完成后切换到用户保存的值。这个过程会导致暗黑模式用户在冷启动时先看到亮色闪烁再切换到暗黑，体验很差。解决闪屏的方案是：在Splash Screen（启动闪屏页）阶段等待AsyncStorage读取完成后再隐藏闪屏、渲染主应用。这样用户看到的第一帧就是正确的主题状态。具体实现是在App组件中添加一个`isReady`状态，初始值为false，在useEffect中并行执行AsyncStorage读取和数据预加载，全部完成后将isReady设为true，条件渲染主应用界面。在isReady为false期间展示Splash Screen。

## 9.4 高频业务UI组件实战

### 9.4.1 按钮、图标、标签组件使用

按钮是所有App中使用频率最高的UI组件，没有之一。antd-mobile-rn的Button支持多种type（类型变体）和状态。理解每种变体的适用场景是用好按钮组件的前提：primary用于主操作如提交确认，default用于次要操作如取消返回，warning用于危险操作如删除警告，ghost用于深色背景上的按钮。

```jsx
import { Button, Tag } from '@ant-design/react-native';

function ButtonDemo() {
  return (
    <>
      <Button type="primary">主要按钮</Button>
      <Button type="default">默认按钮</Button>
      <Button type="warning">警告按钮</Button>
      <Button type="ghost">幽灵按钮</Button>
      <Button loading>加载中</Button>
      <Button disabled>禁用态</Button>
    </>
  );
}
```

实际业务中，怕浪猫强烈建议对Button做一层二次封装。原因有三个：第一，统一处理点击防抖避免用户快速双击导致重复提交；第二，统一埋点上报让数据统计无遗漏；第三，统一异常处理让网络错误不会裸露给用户。

```jsx
function AppButton({ onPress, trackName, ...props }) {
  const pressing = useRef(false);
  const handlePress = () => {
    if (pressing.current) return;
    pressing.current = true;
    trackEvent(trackName);
    onPress?.();
    setTimeout(() => { pressing.current = false; }, 500);
  };
  return <Button onPress={handlePress} {...props} />;
}
```

标签组件（Tag）常用于状态展示场景，比如订单状态、消息标签、分类标记。通过一个配置映射表来管理不同状态对应的颜色和文案，是保持代码可维护性的最佳实践：

```jsx
function StatusTag({ status }) {
  const tagMap = {
    pending: { color: 'default', text: '待处理' },
    processing: { color: 'primary', text: '进行中' },
    success: { color: 'success', text: '已完成' },
    failed: { color: 'error', text: '已失败' },
  };
  const config = tagMap[status] || tagMap.pending;
  return <Tag color={config.color}>{config.text}</Tag>;
}
```

### 9.4.2 卡片、列表、分割线组件开发

卡片和列表是信息展示场景的两大主力组件。卡片组件用于包裹一组相关的内容，提供视觉上的聚合感和层次感。列表组件则用于按行展示结构化的数据项。怕浪猫以一个资讯列表项为例，展示卡片组件在图文混排场景下的典型用法，这个模式在新闻类、电商类、社交类App中都极为常见。

```jsx
import { Card } from '@ant-design/react-native';
import { Image, StyleSheet, Text, View } from 'react-native';

function NewsItem({ item, onPress }) {
  return (
    <Card style={styles.card} onPress={onPress}>
      <View style={styles.row}>
        <Image source={{ uri: item.cover }} style={styles.cover} />
        <View style={styles.content}>
          <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
          <Text style={styles.desc} numberOfLines={1}>{item.summary}</Text>
          <Text style={styles.meta}>{item.source} · {item.time}</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { marginHorizontal: 12, marginBottom: 8 },
  row: { flexDirection: 'row' },
  cover: { width: 100, height: 75, borderRadius: 6 },
  content: { flex: 1, marginLeft: 12 },
  title: { fontSize: 15, fontWeight: '500', lineHeight: 21 },
  desc: { fontSize: 13, color: '#999', marginTop: 4 },
  meta: { fontSize: 12, color: '#bbb', marginTop: 6 },
});
```

List组件在antd-mobile-rn中更多是一个布局容器，配合List.Item子组件使用，适合做设置页、表单项的列表布局。但如果你需要高性能的长列表（数据量超过50条），应该用FlatList（RN内置的虚拟化列表组件）替代List。FlatList只渲染可视区域内的元素，内存占用和渲染性能远优于全量渲染的List。

分割线组件（Divider）看似简单到不值一提，但有一个细节坑值得说明：iOS和Android对分割线颜色的感知不同。`#E5E5E5`这个颜色在iOS上看起来恰到好处——可见但不突兀，但在Android上由于渲染引擎的色彩空间差异，同样的颜色值可能偏深，看起来像一条粗线。建议统一使用`rgba(0,0,0,0.06)`，双端表现一致且更柔和。另外分割线的左侧留白也需要注意，iOS的列表分割线通常从文字左侧开始，而Android的Material规范是从列表最左侧开始，需要通过Platform.select分别处理。

### 9.4.3 弹窗、抽屉、通知提示组件

弹窗组件是用户交互流程中的关键节点。选择哪种弹窗组件取决于交互场景。怕浪猫画了一张弹窗组件选型决策图，你对照着选就行：

```
弹窗组件选型决策图

用户需要确认操作？
├── 是 → 可选选项数量？
│   ├── 一到两个 → Modal（标准对话框）
│   ├── 三到五个 → ActionSheet（底部操作表）
│   └── 超过五个 → 独立页面
└── 否 → 是否需要持续展示？
    ├── 是 → Drawer（侧边抽屉）
    └── 否 → Toast（轻提示）
```

Modal组件基础用法，这是一个删除确认弹窗的典型实现：

```jsx
import { Modal, Button, View, Text } from '@ant-design/react-native';

function ConfirmModal({ visible, onConfirm, onCancel }) {
  return (
    <Modal visible={visible} transparent animationType="fade" onClose={onCancel}>
      <View style={{ padding: 20 }}>
        <Text>确认删除该条目？此操作不可撤销。</Text>
        <View style={{ flexDirection: 'row', marginTop: 20 }}>
          <Button onPress={onCancel}>取消</Button>
          <Button type="warning" onPress={onConfirm}>删除</Button>
        </View>
      </View>
    </Modal>
  );
}
```

Toast（轻提示）使用时有一个关键注意点：Toast组件是单例的，连续调用会出现后一个覆盖前一个的情况——用户可能只看到第二条提示而错过了第一条。如果你需要排队展示多条提示，需要自己封装一个队列管理器，将Toast调用放入队列依次执行，每条提示展示完毕后再展示下一条。

Drawer（抽屉）组件常用于筛选面板场景。从侧边滑出的交互模式比Modal的居中弹出更适合承载复杂的筛选条件表单。

### 9.4.4 轮播、骨架屏、进度条组件

轮播组件（Carousel）在首页Banner、产品展示、引导页、广告位等场景使用频繁。一个好的轮播组件需要支持自动播放、无限循环、指示器、手动滑动切换等基本能力。antd-mobile-rn内置了Carousel组件，底层基于ScrollView的pagingEnabled属性实现分页滑动效果，使用起来比较方便。

```jsx
import { Carousel } from '@ant-design/react-native';
import { Image } from 'react-native';

function BannerCarousel({ banners }) {
  return (
    <Carousel
      autoplay
      infinite
      autoplayInterval={3000}
      dotActiveStyle={{ backgroundColor: '#1677FF' }}
    >
      {banners.map((item) => (
        <Image key={item.id} source={{ uri: item.url }} style={{ height: 160 }} />
      ))}
    </Carousel>
  );
}
```

踩坑提醒：Carousel在Android上的自动轮播偶尔会出现卡顿或停止，原因是ScrollView的定时器在App进入后台后不被系统调度。当App回到前台时定时器恢复但状态可能不一致，导致轮播跳帧或者完全停止。解决方案是监听AppState（应用状态），在App从后台回到前台时重置Carousel的自动播放定时器，让它从头开始计时。这个坑在线上环境的复现率不高但一旦出现用户体验极差，用户会反馈说轮播不动了需要杀掉App重开才行。

骨架屏（Skeleton Screen）是提升感知性能的重要组件。它的作用是在数据加载完成前展示一个和最终内容布局一致的灰色占位框架，让用户在等待过程中就能感知到内容结构。这种"预览感"可以显著降低等待焦虑。

```jsx
import { Skeleton } from '@ant-design/react-native';
import { View } from 'react-native';

function NewsListSkeleton() {
  return (
    <Skeleton loading active>
      <View style={{ padding: 12 }}>
        <Skeleton.Item height={120} />
        <Skeleton.Item height={20} marginTop={12} />
        <Skeleton.Item height={20} width="60%" marginTop={8} />
      </View>
    </Skeleton>
  );
}
```

进度条组件（Progress）用于文件上传、表单填写完成度、安装进度等需要展示任务完成度的场景。一个常见的使用场景是文件上传：用户选择文件后，通过监听上传进度事件，实时更新Progress组件的percent值，让用户直观感知到上传进度。这种即时反馈能大幅降低用户在等待过程中的焦虑感。

### 9.4.5 空状态、异常兜底组件适配

空状态和异常兜底组件是UI层面最容易被忽视、但对用户体验影响最大的部分。一个没有空状态处理的列表页，用户看到白屏会以为App崩溃了然后直接卸载。怕浪猫在每个新项目启动时都会把兜底组件作为第一批开发的组件，确保所有页面的异常场景都有标准化的展示方案。

兜底组件需要覆盖三种典型场景：数据为空的空状态、接口报错的错误状态、网络不可用的网络异常状态。每种状态需要搭配不同的插图、提示文案和操作按钮。空状态展示友好的插图和"暂无数据"提示，可以带一个"去逛逛"的引导按钮。错误状态展示错误插图和"加载失败"提示，带"重新加载"按钮。网络异常状态展示网络插图和"网络异常"提示，带"检查网络设置"按钮引导用户去系统设置。

```jsx
import { View, Text, Image } from 'react-native';
import { Button } from '@ant-design/react-native';

function EmptyState({ type = 'empty', onRetry }) {
  const config = {
    empty: { img: 'empty', text: '暂无数据' },
    error: { img: 'error', text: '加载失败，请稍后重试' },
    network: { img: 'network', text: '网络异常，请检查网络设置' },
  };
  const { img, text } = config[type] || config.empty;

  return (
    <View style={{ alignItems: 'center', paddingVertical: 60 }}>
      <Image source={images[img]} style={{ width: 120, height: 120 }} />
      <Text style={{ color: '#999', marginTop: 12 }}>{text}</Text>
      {onRetry && (
        <Button size="small" style={{ marginTop: 16 }} onPress={onRetry}>
          重新加载
        </Button>
      )}
    </View>
  );
}
```

> 用户不会因为你App崩溃了一次就卸载，但会因为崩溃后只看到白屏而卸载。兜底组件是用户体验的最后一道防线，也是最低成本的体验提升手段。一个完善的App应该在所有可能出错的地方都准备好优雅的降级方案，让用户在任何情况下都能看到有意义的内容而不是空白。

## 9.5 表单系统与实时校验开发

### 9.5.1 输入框、单选、多选、下拉组件

表单是业务系统的心脏，几乎所有核心业务流程都涉及表单交互——注册登录、信息录入、订单提交、设置修改、审批流程、数据搜索筛选。表单组件的丰富度和易用性直接决定了业务开发的效率，一个设计良好的表单系统可以让开发效率提升百分之五十以上。antd-mobile-rn提供了InputItem、Checkbox、Radio、Picker等表单组件，覆盖了大部分基础交互场景。但企业级表单需要更强的数据管理能力——字段状态追踪、批量校验、联动控制、表单重置、脏数据检测等高级功能。怕浪猫推荐配合rc-form（React Components Form）使用，它是Ant Design表单的底层引擎，提供了getFieldProps等API来统一管理表单字段状态，让表单数据流清晰可控。

```jsx
import { InputItem, Picker, List } from '@ant-design/react-native';
import { createForm } from 'rc-form';

function BasicForm({ form }) {
  const { getFieldProps } = form;
  return (
    <List>
      <InputItem {...getFieldProps('username')} placeholder="请输入用户名">
        用户名
      </InputItem>
      <Picker
        data={[
          { value: 'male', label: '男' },
          { value: 'female', label: '女' },
        ]}
        cols={1}
        {...getFieldProps('gender')}
      >
        <List.Item arrow="horizontal">性别</List.Item>
      </Picker>
    </List>
  );
}

export default createForm()(BasicForm);
```

各表单组件的核心Props对照表：

| 组件 | 核心Prop | 数据类型 | 适用场景 |
|------|---------|---------|---------|
| InputItem | value/onChange | string | 文本输入 |
| Checkbox | checked/onPress | boolean | 多选框 |
| Radio | checked/onPress | boolean | 单选框 |
| Picker | data/value | array | 选择器 |
| Switch | checked | boolean | 开关切换 |
| TextareaItem | value/onChange | string | 多行文本 |

### 9.5.2 表单页面整体布局排版规范

企业级表单页面如果字段较多（超过十个），直接平铺排列会让用户感到信息过载，不知道从哪里开始填起。通常的做法是按逻辑分组，将相关字段放入同一个Card卡片中，Card之间留出适当间距。这种"分组卡片"布局模式在视觉上层次清晰，在操作上也有节奏感——用户可以一组一组地填写，每完成一组有一种"阶段性完成"的满足感，这种心理暗示有助于提升表单完成率。

分组的原则是按业务逻辑聚类。比如一个用户注册表单，可以分为"基本信息"（姓名、性别、生日）、"联系方式"（手机号、邮箱、验证码）、"地址信息"（省市区、详细地址）三组。每组用Card包裹，Card的title属性作为组标题。这种分组方式让用户在填写前就能对表单的整体结构有预期，降低放弃率。

```
表单页面布局规范

┌─────────────────────────┐
│    Navigation Header     │
├─────────────────────────┤
│  ┌───────────────────┐  │
│  │ Card: 基本信息     │  │
│  │  - 姓名           │  │
│  │  - 手机号         │  │
│  │  - 邮箱           │  │
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ Card: 地址信息     │  │
│  │  - 省市区         │  │
│  │  - 详细地址       │  │
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ Card: 补充信息     │  │
│  │  - 备注           │  │
│  └───────────────────┘  │
├─────────────────────────┤
│    [取消]  [提交]        │
└─────────────────────────┘
```

对应代码结构：

```jsx
function FormPage({ form }) {
  return (
    <ScrollView>
      <Card title="基本信息" style={{ margin: 12 }}>
        <InputItem {...form.getFieldProps('name')}>姓名</InputItem>
        <InputItem {...form.getFieldProps('phone')}>手机号</InputItem>
      </Card>
      <Card title="地址信息" style={{ margin: 12 }}>
        <Picker data={regionData} {...form.getFieldProps('region')}>
          <List.Item arrow="horizontal">省市区</List.Item>
        </Picker>
        <TextareaItem {...form.getFieldProps('address')} rows={2} />
      </Card>
      <View style={{ flexDirection: 'row', padding: 12 }}>
        <Button style={{ flex: 1 }}>取消</Button>
        <Button type="primary" style={{ flex: 1 }}>提交</Button>
      </View>
    </ScrollView>
  );
}
```

### 9.5.3 自定义表单校验规则配置

rc-form支持通过rules配置校验规则。校验规则是表单数据的守门人，确保用户输入的数据符合业务要求。怕浪猫在多个项目中沉淀了一套常用校验规则库，直接复制到项目中就能用，覆盖了手机号、邮箱、身份证号、密码强度等高频校验场景：

```jsx
const rules = {
  required: (msg = '此项必填') => [{ required: true, message: msg }],
  phone: () => [
    { required: true, message: '请输入手机号' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误' },
  ],
  email: () => [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '邮箱格式错误' },
  ],
  idCard: () => [
    { required: true, message: '请输入身份证号' },
    { pattern: /^\d{17}[\dXx]$/, message: '身份证号格式错误' },
  ],
  length: (min, max) => [{ min, max, message: `长度需在${min}-${max}之间` }],
};
```

实时校验的实现关键在于校验触发时机的选择。常见的做法是在输入框失去焦点时触发字段级校验，这样既能在用户输入完成后及时反馈，又不会在用户输入过程中频繁打扰。

### 9.5.4 表单重置、提交、禁用逻辑

表单的三个核心操作——重置、提交、禁用——看似简单但每个都有坑。重置逻辑的坑在于需要同时清空字段值和校验错误提示，如果只清空值不清错误，用户会看到空输入框下面还挂着红色错误提示，体验很奇怪。提交逻辑的坑在于防重复提交和异步状态管理。禁用逻辑的坑在于需要根据表单状态动态判断哪些字段应该禁用，比如提交后所有字段应禁用，但取消提交后应恢复可编辑状态。

```jsx
function FormActions({ form, onSubmit }) {
  const [submitting, setSubmitting] = useState(false);

  const handleReset = () => {
    form.resetFields();
  };

  const handleSubmit = () => {
    form.validateFields((errors, values) => {
      if (errors) return;
      setSubmitting(true);
      onSubmit(values).finally(() => setSubmitting(false));
    });
  };

  return (
    <View style={{ flexDirection: 'row', padding: 12 }}>
      <Button style={{ flex: 1 }} onPress={handleReset}>重置</Button>
      <Button type="primary" style={{ flex: 1, marginLeft: 12 }}
        loading={submitting} disabled={submitting} onPress={handleSubmit}>
        提交
      </Button>
    </View>
  );
}
```

提交逻辑有一个高频踩坑点：`validateFields`是异步操作，回调函数中直接调用API接口时，需要确保submitting状态正确管理，防止用户在接口返回前重复点击提交按钮。怕浪猫的实践是双重保护——按钮disabled加loading状态，两层防御确保万无一失。另外，validateFields的回调是在校验通过后才执行的，如果校验不通过会直接return，不会触发提交逻辑，这点不需要额外处理。还有一个细节值得注意：校验失败时应该自动滚动到第一个报错字段的位置，让用户立即看到需要修改的地方，而不是让用户自己上下滚动找错误，这个小细节对用户体验的提升非常明显。

### 9.5.5 复杂联动表单实战开发

企业级表单最复杂的部分是联动逻辑。简单的表单只需要校验字段格式是否正确，但复杂的企业表单需要处理字段之间的依赖关系。常见的联动场景包括：选择省份后联动加载城市数据、选择业务类型后显示不同的字段集合、输入金额后自动计算手续费并展示在另一个字段中。这些联动逻辑如果处理不好，代码会变成一团乱麻。

```jsx
function LinkedForm({ form }) {
  const { getFieldProps, getFieldValue, setFieldsValue } = form;
  const [cities, setCities] = useState([]);

  const handleProvinceChange = (value) => {
    setFieldsValue({ city: undefined });
    fetchCities(value[0]).then(setCities);
  };

  const businessType = getFieldValue('type');

  return (
    <>
      <Picker data={provinces} {...getFieldProps('province', { onChange: handleProvinceChange })}>
        <List.Item arrow="horizontal">省份</List.Item>
      </Picker>
      <Picker data={cities} {...getFieldProps('city')}>
        <List.Item arrow="horizontal">城市</List.Item>
      </Picker>
      {businessType === 'enterprise' && (
        <InputItem {...getFieldProps('companyName')}>公司名称</InputItem>
      )}
      {businessType === 'personal' && (
        <InputItem {...getFieldProps('idCard')}>身份证号</InputItem>
      )}
    </>
  );
}
```

联动逻辑的核心原则是：在onChange回调中清除依赖字段的值，然后异步加载新选项数据。这样用户修改省份后，之前选择的城市会被清空，避免出现省份和城市不匹配的数据不一致问题。

> 联动表单的精髓不在于UI怎么变，而在于数据流怎么管。把状态收敛到form实例中，UI只是数据的映射。这句话值得每个做表单的开发同学反复体会。

## 9.6 典型业务页面综合实战

### 9.6.1 首页资讯展示页面完整开发

首页是用户打开App第一眼看到的页面，信息密度最高、组件类型最多、交互最复杂。首页的设计质量直接影响用户的第一印象和留存率。怕浪猫以一个资讯类App首页为例，展示从布局规划到代码实现的完整流程，涵盖搜索栏、轮播图、分类导航、资讯列表等核心模块的组装。

首页布局结构规划：

```
首页结构

┌─────────────────────┐
│   SearchBar 搜索栏   │
├─────────────────────┤
│   Carousel 轮播图    │
├─────────────────────┤
│  Category 分类导航   │
│  [推荐][科技][财经]  │
├─────────────────────┤
│  NewsList 资讯列表   │
│  ┌─────────────────┐ │
│  │ Card: 图文资讯   │ │
│  ├─────────────────┤ │
│  │ Card: 图文资讯   │ │
│  ├─────────────────┤ │
│  │ Skeleton: 加载中 │ │
│  └─────────────────┘ │
├─────────────────────┤
│   TabBar 底部导航    │
└─────────────────────┘
```

```jsx
import { useState, useCallback } from 'react';
import { FlatList, RefreshControl } from 'react-native';
import { SearchBar, Tabs } from '@ant-design/react-native';

function HomePage() {
  const [data, setData] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setData(await fetchNews());
    setLoading(false);
  }, []);

  return (
    <FlatList
      data={data}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <NewsItem item={item} />}
      ListHeaderComponent={<><SearchBar /><BannerCarousel /><Tabs tabs={categories} /></>}
      ListEmptyComponent={!loading && <EmptyState type="empty" onRetry={loadData} />}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => {
        setRefreshing(true); setData(await fetchNews({ refresh: true })); setRefreshing(false);
      }} />}
      onEndReached={() => loadMore()}
    />
  );
}
```

首页开发的关键技术点在于FlatList的Header组合。把SearchBar、Carousel、Tabs都放在ListHeaderComponent中，这样它们会作为列表的一部分跟随列表一起滚动。这种方案在iOS和Android上都能获得流畅的滚动体验，不需要处理嵌套滚动的复杂逻辑。如果把这些组件放在FlatList外部，在iOS上会出现ScrollView嵌套导致的滚动冲突——用户在Header区域滑动时列表不响应，在列表区域滑动时Header不跟随，这种体验割裂感非常明显。另外下拉刷新和上拉加载更多也需要统一在FlatList层面处理，通过RefreshControl实现下拉刷新，通过onEndReached实现触底加载。

### 9.6.2 分类列表页面搭建与适配

分类列表页相比首页更聚焦，用户带着明确目的来浏览某一类数据。页面核心结构是"排序条加筛选条加列表"的三段式组合。排序条让用户快速切换排序方式，筛选条让用户缩小数据范围，列表展示最终结果。这种三段式结构在电商商品列表、新闻分类列表、内容社区分类页等场景中广泛使用。

排序条的实现需要注意一个交互细节：当用户切换排序方式时，列表数据需要重新排序。如果数据量较大，排序操作应该在useMemo中完成避免每次渲染都重新计算，提升页面响应速度。筛选条的交互更复杂一些，通常以Drawer抽屉的形式从侧边滑出，包含多个筛选项（价格区间、品牌、标签等），用户选择后点击"确定"按钮应用筛选条件。筛选条件应用后需要同步更新URL参数或Redux状态，确保用户刷新页面或返回时筛选状态不丢失。

```jsx
```jsx
import { useState, useMemo } from 'react';
import { View, FlatList, TouchableOpacity, Text, StyleSheet } from 'react-native';

function CategoryListPage({ route }) {
  const [sort, setSort] = useState('latest');
  const sortedData = useMemo(() => sortData(rawData, sort), [rawData, sort]);
  return (
    <View style={s.container}>
      <SortBar sort={sort} onChange={setSort} />
      <FlatList data={sortedData} keyExtractor={(i) => i.id}
        renderItem={({ item }) => <NewsItem item={item} />} />
    </View>
  );
}

function SortBar({ sort, onChange }) {
  const opts = [{ key: 'latest', label: '最新' }, { key: 'hot', label: '热门' }];
  return (
    <View style={s.sortBar}>
      {opts.map((o) => (
        <TouchableOpacity key={o.key} onPress={() => onChange(o.key)}>
          <Text style={sort === o.key && s.active}>{o.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  sortBar: { flexDirection: 'row', backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10 },
  active: { color: '#1677FF', fontWeight: '500' },
});
```

### 9.6.3 详情页图文排版与交互实现

详情页是用户内容消费的核心场景，用户在此页面停留时间最长、交互最深入。图文混排是详情页的主要技术挑战——RN没有HTML的img标签和p标签，图片和文字需要通过组件组合来渲染。通常的做法是：后端返回的内容数据结构化为一个block数组，每个block有type字段标识是文字段落还是图片，前端根据type渲染不同的RN组件。这种数据驱动渲染的模式让详情页的内容格式可以灵活扩展，未来如果需要支持视频、音频、引用块等新的内容类型，只需要增加新的block类型和对应的渲染逻辑即可。

```jsx
function DetailPage({ route }) {
  const { id } = route.params;
  const [article, setArticle] = useState(null);
  useEffect(() => { fetchArticle(id).then(setArticle); }, [id]);
  if (!article) return <Skeleton loading active />;

  const renderBlock = (block, i) => {
    if (block.type === 'text') return <Text key={i} style={styles.p}>{block.value}</Text>;
    if (block.type === 'image') return <Image key={i} source={{ uri: block.url }} style={styles.img} />;
    return null;
  };

  return (
    <ScrollView style={styles.c}>
      <Text style={styles.title}>{article.title}</Text>
      <View style={styles.meta}>
        <Text style={styles.author}>{article.author}</Text>
        <Text style={styles.time}>{article.publishTime}</Text>
      </View>
      <View style={styles.content}>{article.content.map(renderBlock)}</View>
    </ScrollView>
  );
}
```

样式定义包含容器背景色、标题字号、段落行高等，通过StyleSheet.create统一管理。

详情页有一个交互细节值得特别说明：图片高度的计算。如果服务端返回的图片原始尺寸是宽375高200，但用户设备的屏幕宽度是414，直接按原始尺寸渲染会导致图片变形或者留白。正确的做法是根据屏幕宽度和图片宽高比动态计算渲染高度：`renderHeight = screenWidth * (imageHeight / imageWidth)`。这样无论用户使用什么尺寸的设备，图片都能保持正确的宽高比例不变形。另外图片加载需要处理加载中、加载失败、加载成功三种状态，加载中展示占位色块或骨架屏，加载失败展示错误图标和重试按钮，加载成功后才展示真实图片。

### 9.6.4 个人中心页面布局开发

个人中心页面通常包含三个模块：用户信息卡片（头像、昵称、简介、编辑入口）、功能入口网格（我的订单、我的收藏、浏览历史、我的钱包、我的优惠券等）、设置列表（消息通知、隐私设置、帮助反馈、关于我们等）。这三个模块从上到下排列，整体页面用ScrollView包裹。个人中心页面的设计要点是信息层次清晰——用户信息卡在顶部用品牌色背景突出展示传递品牌感，功能入口用图标网格方便快速定位且每行四个入口保持对齐整齐，设置列表用标准List.Item保证操作一致性和可预期性。

```jsx
function ProfilePage({ navigation }) {
  const { user } = useAuth();

  return (
    <ScrollView style={{ backgroundColor: '#f5f5f5' }}>
      <UserInfoCard user={user} />
      <FunctionGrid items={[
        { icon: 'order', label: '我的订单', page: 'Orders' },
        { icon: 'collection', label: '我的收藏', page: 'Collections' },
        { icon: 'history', label: '浏览历史', page: 'History' },
        { icon: 'wallet', label: '我的钱包', page: 'Wallet' },
      ]} onPress={(page) => navigation.navigate(page)} />
      <SettingsList items={[
        { label: '消息通知', page: 'Notifications' },
        { label: '隐私设置', page: 'Privacy' },
        { label: '帮助与反馈', page: 'Help' },
        { label: '关于我们', page: 'About' },
      ]} onPress={(page) => navigation.navigate(page)} />
    </ScrollView>
  );
}
```

用户信息卡片的背景通常使用品牌色的渐变效果，让视觉层次分明。功能入口网格用四列布局，每个入口包含图标和文字标签。设置列表用List.Item组件，右侧带箭头标识可点击跳转。

### 9.6.5 设置页面表单功能实战

设置页面是表单组件的集中展示场。这个页面虽然看起来简单——就是一列设置项，但它汇集了Switch开关、Picker选择器、导航跳转、危险操作确认等多种交互形式，是验证组件库覆盖度和一致性的试金石。如果一个组件库能把设置页面做得体验流畅、交互完整，那它在其他业务页面的表现通常也不会差。

```jsx
import { List, Switch, Picker } from '@ant-design/react-native';
import { useState } from 'react';
import { useThemeMode } from '../../theme/ThemeContext';

function SettingsPage({ navigation }) {
  const { mode, updateMode } = useThemeMode();
  const [notifications, setNotifications] = useState(true);
  const [cacheSize, setCacheSize] = useState('128MB');
  const themeData = [{ value: 'system', label: '跟随系统' },
    { value: 'light', label: '亮色' }, { value: 'dark', label: '暗黑' }];
  return (
    <List>
      <List.Item extra={<Switch checked={notifications} onChange={setNotifications} />}>消息通知</List.Item>
      <Picker data={themeData} cols={1} value={[mode]}
        onChange={(v) => updateMode(v[0])}>
        <List.Item arrow="horizontal">主题模式</List.Item>
      </Picker>
      <List.Item extra={cacheSize} arrow="horizontal"
        onPress={() => clearCache().then(() => setCacheSize('0MB'))}>清除缓存</List.Item>
      <List.Item arrow="horizontal" onPress={() => navigation.navigate('About')}>关于我们</List.Item>
      <List.Item arrow="horizontal" onPress={handleLogout}>
        <Text style={{ color: '#FF4D4F' }}>退出登录</Text>
      </List.Item>
    </List>
  );
}
```

> 设置页面看似简单，但它往往是用户接触暗黑模式、消息通知等系统能力的入口。把这个页面做到"无感切换、即时反馈"，是体验设计的基本功。用户在设置页面的每一次操作都应该有即时的视觉反馈——开关切换有动画、主题切换有过渡、缓存清除有Toast提示。

## 收藏清单：企业级RN页面开发实战checklist

怕浪猫把本章涉及的核心知识点整理成一份完整的实战清单，方便你对照自己的项目逐一落地。这份清单建议收藏，在每次新项目启动或代码审查时拿出来对照。

**组件库选型清单**
- [ ] 完成组件需求审计（统计设计稿中所有组件类型和使用频率）
- [ ] 候选UI库能力映射（标记支持、需定制、不支持三类）
- [ ] POC验证双端兼容性（iOS和Android真机测试）
- [ ] 确认TypeScript类型定义完整性
- [ ] 评估包体积对首屏加载的影响

**主题配置清单**
- [ ] 品牌主色Token覆盖到所有组件
- [ ] 亮色和暗黑模式双主题定义
- [ ] 字体、圆角、间距Token集中管理
- [ ] 主题配置通过AsyncStorage本地持久化
- [ ] 冷启动主题闪屏问题优化处理

**表单开发清单**
- [ ] rc-form集成配置完成
- [ ] 必填、手机号、邮箱等校验规则封装
- [ ] 字段级实时校验触发机制实现
- [ ] 提交防重复点击双重保护
- [ ] 联动逻辑数据流统一管理

**业务页面清单**
- [ ] 首页FlatList加Header组合方案优化
- [ ] 列表页筛选加排序状态管理
- [ ] 详情页图文混排动态渲染
- [ ] 个人中心模块化布局
- [ ] 设置页Switch、Picker、Navigate全覆盖
- [ ] 全页面空状态和异常兜底处理

## 系列进度 9/16

怕浪猫说到这里，第9章的内容就告一段落了。从UI组件库的选型对比，到全局主题定制，到表单系统和业务页面的完整实战，这条链路基本覆盖了RN企业级开发中UI层的核心工作。组件库选对、主题配好、表单做稳、页面铺满，一个完整的RN应用UI骨架就立起来了。

下一章我们将进入状态管理的深水区——从组件级状态到全局状态管理方案选型，涵盖Redux Toolkit、Zustand、Jotai等主流方案的实战对比，以及在复杂业务场景下的状态架构设计。状态管理做得好，后期维护少烦恼。我们下章见。
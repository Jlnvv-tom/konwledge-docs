# 第5章 React Navigation企业级路由导航开发

你的RN项目是不是页面一多就乱成一锅粥？跳转逻辑到处硬编码`navigate('Detail')`，路由名称拼写错误运行时才报错，Tab和Stack嵌套时跳转莫名其妙不生效，登录拦截更是靠每个页面手写`if(!token)`判断——这些问题在一个十几个页面的项目里可能还能忍，但等到业务膨胀到几十上百个页面时，就是灾难级别的技术债。

我见过一个电商项目，40多个页面全部注册在一个Stack里，Tab和业务页面混在一起，没有路由常量管理，所有跳转都是字符串硬编码。新人接手项目后，光是搞清楚"从首页到订单详情页到底经过哪些中间页"就花了三天。更恐怖的是，有一次把路由名`OrderDetail`写成了`OrderDetial`，直到用户反馈点击没反应才发现问题，而这时候已经上线两天了。

路由是多页面应用的骨架。骨架不牢，地动山摇。更致命的是，路由设计一旦定型，后期重构成本极高，因为每一条跳转链路都和业务逻辑深度耦合。你不可能在项目后期轻松地把一个Stack拆成两个，或者把一组页面从Tab里抽出来放到Drawer里——这些改动会牵连到无数的跳转代码和参数传递逻辑。

我是怕浪猫，一个在RN（React Native）项目里趟过无数路由坑的开发者。前面几章我们搞定了组件化开发和Hooks机制，从这章开始进入路由导航的实战领域。React Navigation作为RN官方推荐的路由方案，从5.x到6.x经历了架构层面的进化，这章我会带你从技术选型一路讲到权限拦截，用企业级的标准把路由架构搭得明明白白。

> 路由设计不是技术选型题，而是架构设计题。选什么库只是第一步，怎么组织路由层级、怎么管理路由常量、怎么做权限拦截，才是决定项目可维护性的关键。

## 5.1 RN路由体系与技术选型

### 5.1.1 原生路由与第三方路由对比

RN的路由方案发展经历了几个阶段。早期社区方案百花齐放，Navigator、NavigatorExperimental、React Native Navigation、React Router Native各领风骚。后来React Navigation成为官方推荐后基本一统天下，但了解各方案的差异有助于理解为什么选它。

先看RN路由方案的核心对比：

| 对比维度 | React Navigation | React Native Navigation | React Router Native | 自研方案 |
|---------|-----------------|------------------------|-------------------|---------|
| 底层实现 | JS层管理路由栈 | 原生Navigator封装 | Web路由思路移植 | 完全自控 |
| 性能表现 | JS驱动，足够流畅 | 原生性能最优 | 一般 | 取决于实现 |
| 社区生态 | 官方推荐，最活跃 | 社区维护减少 | 偏Web思维 | 无社区支持 |
| 上手成本 | 中等，文档完善 | 较高，需原生配置 | 低（会Web即会） | 高 |
| 定制能力 | 极强，支持深度定制 | 原生层定制受限 | 一般 | 完全自由 |
| 适合场景 | 绝大多数RN项目 | 对性能极致要求的项目 | 跨端统一路由 | 特殊需求 |

React Native Navigation（简称RNN）是callstack团队维护的纯原生导航方案，性能确实比React Navigation更好，因为它的路由管理在原生层完成，不走JS Bridge（JavaScript桥接通信机制）。但它的致命问题是需要修改原生配置，每次新增页面类型都要在iOS和Android原生层注册。在一个快速迭代的项目中，这种开发体验是难以接受的。而且RNN的社区活跃度近年来明显下降，issue响应慢，版本更新滞后，选型时必须考虑维护风险。

React Router Native虽然思路清晰，但它本质是把Web路由（URL，Uniform Resource Locator，统一资源定位符）模式搬到移动端，缺少手势导航、原生转场动画、Safe Area（安全区域）适配等移动端特性的支持。它的`<Route>`组件思维在Web端很自然，但在移动端的导航体验上水土不服。移动端路由需要处理Web端不需要考虑的问题：手势返回、物理返回键、Safe Area、页面转场动画、Tab切换状态保持等。React Router Native的设计哲学和移动端的这些需求存在根本性的错位。

> 选路由库就像选地基材料，不是越硬越好，而是要和你的建筑结构匹配。原生性能最优听起来很美，但开发效率的损失在高频迭代的项目里是不可接受的。React Navigation在性能和开发体验之间找到了最佳平衡点。

### 5.1.2 React Navigation架构优势解析

React Navigation能一统江湖不是偶然的，它的架构设计确实有独到之处。核心架构可以用下面这张层级图来理解：

```
┌─────────────────────────────────┐
│        NavigationContainer       │ ← 路由状态管理中枢
│    (状态容器 + 导航上下文)         │
├─────────────────────────────────┤
│     Navigator (导航器层)          │ ← Stack/Tab/Drawer
│  ┌──────────┬──────────┐        │
│  │ Screen A │ Screen B │ ...    │ ← 页面注册
│  └──────────┴──────────┘        │
├─────────────────────────────────┤
│      路由状态 (Navigation State)  │ ← routes/index/history
├─────────────────────────────────┤
│     底层平台适配层                 │ ← iOS/Android差异抹平
│  ┌─────────┬──────────────┐     │
│  │  iOS    │  Android     │     │
│  │ 原生动画 │  Reanimated  │     │
│  └─────────┴──────────────┘     │
└─────────────────────────────────┘
```

这个架构的核心优势有三个，理解了这三个优势，你就明白了为什么社区最终选择了React Navigation而不是其他方案：

第一，状态驱动路由。React Navigation的导航状态是一个标准的JS对象，路由的切换本质上就是状态的变更。这意味着你可以用Redux或Zustand来管理路由状态，实现时间旅行调试、路由状态持久化等高级能力。在调试路由问题时，你可以打印出完整的路由状态树，清晰地看到每一层的路由栈和当前激活的页面，这种可观测性在排查复杂嵌套路由问题时非常宝贵。

第二，导航器组合。每种导航器（Stack、Tab、Drawer）都是独立的组件，可以任意嵌套组合。比如Tab里嵌Stack、Stack里嵌Drawer，这种组合能力是构建复杂APP路由的基础。每种导航器只关心自己维度的导航逻辑，互相之间通过统一的navigation prop通信，做到了高内聚低耦合。

第三，平台自适应。React Navigation在iOS上使用原生UINavigationController（iOS导航控制器）的动画效果，在Android上使用Reanimated（React Native动画库）实现类似的丝滑过渡，开发者不需要关心平台差异。手势返回、侧滑抽屉等原生交互体验都得到了良好支持。

核心路由状态结构长这样：

```ts
// Navigation State 的核心结构
{
  index: 1,              // 当前激活的路由索引
  routes: [              // 路由栈
    { name: 'Home', key: 'Home-1' },
    { name: 'Detail', key: 'Detail-2', params: { id: 42 } }
  ],
  stale: false,          // 是否处于过渡状态
  type: 'stack'          // 导航器类型
}
```

理解这个状态结构非常重要。`index`字段标识当前激活的是哪个路由，`routes`数组是路由栈的完整快照，`key`是每个路由实例的唯一标识——注意key不是你手动赋值的，而是React Navigation自动生成的，格式是`路由名-递增数字`。后续的路由拦截、状态持久化、深度链接（Deep Linking，通过URL scheme或universal link直接打开APP内特定页面）等功能都建立在操作这个状态对象的基础上。比如你要实现"从详情页返回首页并刷新数据"，本质上就是修改这个状态对象，把index从1改回0，然后在Home页面的`useFocusEffect`中触发刷新。

### 5.1.3 6.x新版本核心特性与变更

React Navigation 6.x相比5.x有不少重要变更，如果你是从5.x升级过来的，以下几个改动需要特别关注。5.x到6.x不是简单的版本号递增，而是架构层面的进一步解耦和优化。

首先是安装方式的变化。6.x采用了更彻底的模块化拆分，每种导航器都是独立包：

```bash
# 核心包
npm install @react-navigation/native

# 按需安装导航器
npm install @react-navigation/native-stack    # 原生栈（推荐）
npm install @react-navigation/bottom-tabs     # 底部Tab
npm install @react-navigation/drawer          # 抽屉导航

# 依赖库
npm install react-native-screens react-native-safe-area-context
```

5.x时期很多功能是内置在核心包里的，6.x把它们拆成了独立包。比如`@react-navigation/stack`和`@react-navigation/native-stack`是两个不同的包，前者是纯JS实现的栈导航器，后者底层使用原生导航组件，性能更好但定制能力稍弱。

> 从5.x到6.x最大的感知变化是：很多以前内置的功能被拆成了独立包。这看起来增加了安装成本，但实际上了减少了不必要的依赖体积。你只用你需要的，这才是模块化的正确姿势。怕浪猫在升级一个项目时，发现bundle体积减少了约200KB，因为不再需要引入用不到的导航器代码。

6.x的核心变更一览：

| 变更项 | 5.x方式 | 6.x方式 | 影响 |
|-------|---------|---------|------|
| Stack导航器 | `@react-navigation/stack` | `@react-navigation/native-stack` | 推荐用native-stack，性能更好 |
| 主题配置 | `theme` prop on Container | `ThemeProvider` 或 `NavigationContainer.theme` | 更灵活的主题管理 |
| Group组件 | 无 | 新增`<Group>`组件 | 路由分组，共用配置 |
| 屏幕监听 | `addListener` | `listeners` prop + `useFocusEffect`增强 | 更简洁的事件监听 |
| TypeScript | 部分支持 | 完整泛型支持 | 类型推导更完善 |

`native-stack`是6.x主推的栈导航器，底层使用iOS的`UINavigationController`和Android的`Fragment`管理，性能比纯JS实现的`stack`更好。但如果你需要高度自定义转场动画（比如共享元素过渡），仍然可以使用`@react-navigation/stack`。

新增的`<Group>`组件允许你把相关的Screen分组，统一配置样式和行为：

```tsx
<Stack.Navigator>
  <Stack.Group screenOptions={{ headerStyle: { backgroundColor: '#1a1a2e' } }}>
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Group>
  <Stack.Group screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Home" component={HomeScreen} />
    <Stack.Screen name="Detail" component={DetailScreen} />
  </Stack.Group>
</Stack.Navigator>
```

### 5.1.4 路由分层设计与模块化思想

路由分层的核心思想是：不同层级的导航器负责不同的导航职责，各司其职，互不干扰。这和软件工程中的分层架构思想一脉相承——每层只关注自己的职责，通过明确的接口和上下层通信。

一个典型的企业级APP路由分层结构：

```
RootStack (根栈导航)
├── AuthStack (认证模块栈)
│   ├── Login
│   ├── Register
│   └── ForgotPassword
├── MainTab (主Tab导航)
│   ├── HomeStack (首页模块栈)
│   │   ├── HomeMain
│   │   ├── HomeDetail
│   │   └── HomeSearch
│   ├── OrderStack (订单模块栈)
│   │   ├── OrderList
│   │   └── OrderDetail
│   └── ProfileStack (个人中心栈)
│       ├── ProfileMain
│       └── ProfileSetting
└── GlobalModal (全局弹窗栈)
    ├── ImageViewer
    └── LoadingOverlay
```

这种分层的设计原则是：

**单一职责**：每个导航器只负责一个维度的导航。RootStack管全局页面切换，MainTab管Tab间切换，各模块Stack管模块内页面跳转。AuthStack管登录注册流程，MainTab管主业务流程，两者互不干扰。这种分层的好处是，当你需要修改认证流程时，完全不需要动主业务的路由代码，修改的影响范围被严格限定在一个模块内。

**高内聚低耦合**：HomeStack内部的页面变化不影响OrderStack，Tab切换不影响各模块内部的路由栈。当你在HomeStack内部从HomeMain跳到HomeDetail再返回，OrderStack完全不知道也不关心这个变化。这种隔离性保证了修改一个模块不会引发其他模块的意外行为。

**可扩展性**：新增业务模块只需要新增一个Stack并注册到Tab中，不需要修改其他模块的路由配置。比如要加一个"消息中心"模块，只需要创建MessageStack，注册到Tab里，其他模块的代码一行都不用改。这种扩展方式符合开闭原则——对扩展开放，对修改关闭。

> 好的路由架构就像好的代码架构一样，核心是"关注点分离"。你不会把所有业务逻辑写在一个函数里，也不应该把所有页面塞在一个导航器里。怕浪猫见过最离谱的项目，所有页面都注册在一个Stack里，连Tab都是用Stack模拟的，结果路由栈深度动不动就二三十层，返回逻辑完全失控。

### 5.1.5 大型APP路由架构设计方案

当项目规模达到几十个页面时，路由架构的设计直接决定了开发效率和可维护性。这里给出一套经过实战验证的路由架构方案。

核心思路是"三层四区"架构：

```
┌──────────────────────────────────────┐
│           Application Layer           │  ← 业务层（页面组件）
├──────────────────────────────────────┤
│          Navigation Layer             │  ← 导航层（导航器配置）
├──────────────────────────────────────┤
│            Route Layer                │  ← 路由层（常量/类型/守卫）
├──────────────┬──────┬────────────────┤
│   Auth Zone  │ Main │   Modal Zone   │  ← 三个功能分区
│   (认证区)    │ Zone │   (弹窗区)     │
│              │(主区) │                │
└──────────────┴──────┴────────────────┘
```

对应的目录结构：

```
src/
├── navigation/
│   ├── index.ts            # 路由统一导出
│   ├── RootNavigator.tsx   # 根导航器
│   ├── AuthNavigator.tsx   # 认证导航器
│   ├── MainNavigator.tsx   # 主导航器
│   ├── ModalNavigator.tsx  # 弹窗导航器
│   └── types.ts            # 路由类型定义
├── routes/
│   ├── routeNames.ts       # 路由名称常量
│   ├── routeConfig.ts      # 路由配置表
│   └── routeGuards.ts      # 路由守卫
├── screens/
│   ├── auth/
│   ├── home/
│   ├── order/
│   └── profile/
```

这种架构的好处是路由配置和页面组件完全解耦。页面组件只关心自己的UI和逻辑，路由配置集中在navigation目录管理，路由常量和守卫逻辑集中在routes目录。当需要调整页面跳转关系时，只需要改路由配置，不需要动业务组件。新人接手项目时，先看`routeNames.ts`了解有哪些路由，再看`RootNavigator.tsx`了解路由层级关系，最后才看具体的页面组件，学习曲线非常平缓。

## 5.2 栈路由Stack Navigator实战

### 5.2.1 栈路由安装与基础环境配置

栈路由是RN中最基础也最常用的导航方式，它的核心思想是"后进先出"（LIFO，Last In First Out）的页面栈管理，和iOS的UINavigationController以及Android的FragmentManager思路一致。新页面压入栈顶，返回时弹出栈顶，栈底是初始页面。

安装依赖：

```bash
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context
```

iOS需要执行pod安装：

```bash
cd ios && pod install && cd ..
```

`react-native-screens`是一个关键依赖，它利用原生平台的页面管理能力来优化性能。没有它，RN会把所有页面都保持在内存中并叠加渲染，页面多了之后内存占用会飙升。开启`react-native-screens`后，非可见页面会被原生层冻结，不消耗渲染资源。在iOS上它使用原生的UINavigationController来管理页面栈，在Android上使用Fragment生命周期管理，两种平台都能获得接近原生的页面切换性能。安装后还需要在入口文件中调用`enableScreens()`来激活原生页面管理能力，否则它只是安装了但不起作用。

最基础的栈路由配置：

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Detail" component={DetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};
```

这里有几个新手常踩的坑：

第一，`NavigationContainer`必须且只能有一个，作为整个路由树的根容器。如果你在子组件里又放了一个`NavigationContainer`，会直接报错。`NavigationContainer`负责管理全局的导航状态，是所有导航器的上下文提供者。

第二，`initialRouteName`指定的路由必须是已注册的Screen之一，否则启动时会白屏。

第三，`name`属性是路由的唯一标识，后续所有的跳转代码都要用这个名字。这就是为什么我们后面要引入路由常量管理——因为字符串硬编码迟早会出拼写错误。

> 实际项目中，`NavigationContainer`通常放在App根组件的最外层，包在所有的Provider（如Redux Provider、Theme Provider）内部但在导航器外部。位置放错是新手最常见的配置错误之一。怕浪猫曾经把`NavigationContainer`放在了Redux Provider外面，结果导航器里读取不到Redux状态，排查了半天才发现是嵌套顺序的问题。

### 5.2.2 页面跳转、返回与路由栈管理

栈路由的核心操作就是跳转和返回。React Navigation提供了`navigation`对象，通过它可以在任何被导航器管理的页面中执行导航操作。

页面跳转的核心方法对比：

| 方法 | 作用 | 路由栈变化 | 典型场景 |
|------|------|-----------|---------|
| `navigate` | 跳转到指定路由 | 如果路由已在栈中则回退到它，否则入栈 | 普通页面跳转 |
| `push` | 压入新路由 | 无论是否已有都入栈 | 需要多次打开同一页面 |
| `goBack` | 返回上一页 | 弹出栈顶 | 返回操作 |
| `pop` | 弹出N页 | 弹出指定数量 | 多级返回 |
| `popToTop` | 回到栈底 | 清空栈只留第一页 | 返回首页 |
| `replace` | 替换当前页 | 替换栈顶不入栈 | 登录后跳主页 |

核心代码示例：

```tsx
// 页面跳转
const handleNavigate = () => {
  navigation.navigate('Detail', { id: 42, title: '详情页' });
};

// push: 同一页面可以多次入栈
const handlePush = () => {
  navigation.push('Detail', { id: 43 });
};

// 返回上一页
const handleGoBack = () => {
  if (navigation.canGoBack()) {
    navigation.goBack();
  }
};

// 弹出2页，回到上上页
const handlePop = () => {
  navigation.pop(2);
};

// 回到栈底
const handlePopToTop = () => {
  navigation.popToTop();
};
```

`navigate`和`push`的区别是新手最容易混淆的。假设路由栈是`[Home, Detail]`，调用`navigate('Detail')`不会新增页面，因为Detail已经在栈中，它会直接激活已有的Detail页面并可能更新params。而`push('Detail')`会再压入一个Detail，栈变成`[Home, Detail, Detail]`。

这个区别在实际开发中很重要。比如从商品列表点击不同商品进入详情页，你希望栈里保留多个详情页（方便返回上一个商品），就应该用`push`。从设置页跳转到修改密码页，你不需要多个修改密码页，就应该用`navigate`。

`canGoBack()`是一个很有用的方法，在栈深度为1时返回false。在Android物理返回键处理中，如果不判断`canGoBack()`就直接`goBack()`，可能导致退出APP而不是返回上一页。这是Android端最常见的路由问题之一，很多开发者只在iOS上测试，忘了Android有物理返回键的概念。正确的做法是用`BackHandler`API监听返回键事件，在回调中先判断`canGoBack()`，能返回就返回，不能返回就交给系统处理（退出APP）。

> 怕浪猫踩过最蠢的坑是：在Tab页面里用`navigation.goBack()`，结果Tab没有上一页可以返回，APP直接闪退。后来才想明白Tab导航器不是Stack，没有"上一页"的概念。每个导航器的行为不同，搞清楚当前`navigation`对象属于哪个导航器很重要。

### 5.2.3 路由参数传递与TS类型约束

路由参数是页面间通信的基本方式。React Navigation的参数传递通过`navigate`的第二个参数实现，接收端通过`route.params`获取。

TS（TypeScript）类型约束是6.x的强项，通过泛型可以让参数类型在编译时就得到校验：

```ts
// 1. 定义所有路由的参数类型
type RootStackParamList = {
  Home: undefined;                    // 无参数
  Detail: { id: number; title?: string };  // 必传id，title可选
  Search: { keyword: string; category?: string };
};

// 2. 为页面组件定义Props类型
type DetailScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'Detail'
>;

// 3. 在组件中使用
const DetailScreen = ({ route, navigation }: DetailScreenProps) => {
  const { id, title } = route.params;  // 类型安全
  return (
    <View>
      <Text>{title ?? `详情 ${id}`}</Text>
    </View>
  );
};
```

> 没有TS类型约束的路由参数就像没有刹车的汽车，能跑但出事是迟早的。一旦你在`navigate`里传错了参数名或类型，运行时才会报错，而且报错信息往往不明确——可能是`undefined is not an object`之类的通用错误，你根本定位不到是参数传错了。加上类型约束后，IDE直接红线提示，编译阶段就拦住了。

实际项目中常见的坑是参数序列化问题。`navigate`的参数必须是可序列化的值（字符串、数字、布尔、普通对象），不能传函数、Date对象、类的实例等。如果你传了不可序列化的值，React Navigation会给你一个黄色警告，而且在某些情况下（比如状态持久化）会导致数据丢失。

错误写法：

```tsx
// 不要传不可序列化的值
navigation.navigate('Detail', {
  callback: () => console.log('hi'),  // 错误
  date: new Date(),                    // 错误
  instance: new MyClass(),             // 错误
});
```

正确做法是只传原始数据，在目标页面内根据数据重新构造：

```tsx
// 只传原始数据
navigation.navigate('Detail', {
  id: 42,
  timestamp: Date.now(),  // 传时间戳而非Date对象
});
```

还有一个常见问题是参数默认值处理。`route.params`可能是`undefined`（用户直接从首页进入Detail页而非从列表点击进入），所以读取参数时一定要做空值处理：

```tsx
const DetailScreen = ({ route }: DetailScreenProps) => {
  const id = route.params?.id ?? 0;
  const title = route.params?.title ?? '默认标题';
  // ...
};
```

### 5.2.4 路由替换、清空与重定向实现

路由替换在某些场景下非常关键。最典型的场景是登录流程：用户在登录页点击登录成功后，不应该能返回登录页，这时需要用`replace`替换当前路由。

```tsx
// 登录成功后替换路由
const handleLoginSuccess = () => {
  navigation.replace('Main');
  // 或者 reset 清空整个路由栈
  navigation.reset({
    index: 0,
    routes: [{ name: 'Main' }],
  });
};
```

`replace`和`reset`的区别在于：`replace`只替换栈顶的一页，`reset`可以重置整个路由栈。如果路由栈是`[Splash, Login]`，`replace('Main')`后变成`[Splash, Main]`，用户按返回会回到Splash页。而`reset`后变成`[Main]`，用户按返回直接退出APP。

所以登录成功后通常用`reset`而非`replace`，因为你不希望用户返回到Splash或Login页面：

```tsx
// 登录成功，完全清除历史
const handleLoginSuccess = () => {
  navigation.reset({
    index: 0,
    routes: [{ name: 'Main' }],
  });
};

// 退出登录，回到登录页
const handleLogout = () => {
  navigation.reset({
    index: 0,
    routes: [{ name: 'Login' }],
  });
};
```

`reset`还支持指定多个路由，模拟"从通知点击直接进入订单详情页"的场景：

```tsx
// 从推送通知进入订单详情，保留首页在栈底
navigation.reset({
  index: 1,
  routes: [
    { name: 'Main' },                    // 栈底
    { name: 'OrderDetail', params: { orderId: '123' } },  // 栈顶
  ],
});
```

这样用户从订单详情页返回时，会直接回到主页，而不是退出APP。

> `reset`是一个强大但危险的方法。它会完全丢弃当前的路由栈历史，如果在不适合的场景使用（比如用户正在填写表单时误触），会导致用户数据丢失。怕浪猫建议在调用`reset`前加一个确认弹窗，特别是在涉及未保存数据的场景。

### 5.2.5 导航栏样式与标题自定义配置

导航栏（Header）的样式定制是高频需求。React Navigation的导航栏配置有两种方式：Screen级别配置和Navigator级别配置。

```tsx
<Stack.Navigator
  screenOptions={{
    headerStyle: { backgroundColor: '#1a1a2e' },
    headerTintColor: '#fff',
    headerTitleStyle: { fontWeight: 'bold' },
    headerShadowVisible: false,
  }}
>
  <Stack.Screen
    name="Home"
    component={HomeScreen}
    options={{
      title: '首页',
      headerRight: () => (
        <TouchableOpacity onPress={() => navigation.navigate('Search')}>
          <Text style={{ color: '#fff' }}>搜索</Text>
        </TouchableOpacity>
      ),
    }}
  />
  <Stack.Screen
    name="Detail"
    component={DetailScreen}
    options={({ route }) => ({
      title: route.params?.title ?? '详情',
    })}
  />
</Stack.Navigator>
```

`screenOptions`是Navigator级别的配置，对所有Screen生效。`options`是Screen级别的配置，会覆盖Navigator级别的同名配置。`options`支持传入函数，参数包含`route`和`navigation`，可以根据路由参数动态配置标题。

如果需要完全自定义导航栏，可以使用`header`属性替换整个Header组件：

```tsx
<Stack.Screen
  name="Home"
  component={HomeScreen}
  options={{
    header: ({ navigation, route, options }) => (
      <CustomHeader
        title="首页"
        onBack={() => navigation.goBack()}
        style={options.headerStyle}
      />
    ),
  }}
/>
```

实际项目中常见的导航栏需求是渐变背景色。React Navigation的`headerStyle`不支持渐变，需要用自定义Header实现：

```tsx
import LinearGradient from 'react-native-linear-gradient';

<Stack.Screen
  name="Home"
  component={HomeScreen}
  options={{
    header: ({ navigation }) => (
      <LinearGradient
        colors={['#e94560', '#0f3460']}
        style={{ height: 56, flexDirection: 'row', alignItems: 'center' }}
      >
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={{ color: '#fff', fontSize: 18, marginLeft: 16 }}>
          首页
        </Text>
      </LinearGradient>
    ),
  }}
/>
```

> 自定义导航栏虽然灵活，但意味着你要自己处理安全区域适配、返回手势、标题居中等所有细节。除非有特殊的UI需求（如渐变背景、自定义动画），否则尽量用`screenOptions`配置。怕浪猫的建议是：先用`screenOptions`和`options`满足需求，实在不够用再考虑自定义Header。

## 5.3 底部Tab导航开发实战

### 5.3.1 Tab导航基础结构快速搭建

底部Tab导航是移动端最经典的导航模式，适合3-5个主入口的切换。React Navigation提供了`createBottomTabNavigator`来快速搭建。

```bash
npm install @react-navigation/bottom-tabs
```

基础搭建：

```tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Tab = createBottomTabNavigator<MainTabParamList>();

const MainNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#e94560',
        tabBarInactiveTintColor: '#8d8d8d',
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarLabel: '首页' }}
      />
      <Tab.Screen
        name="Order"
        component={OrderScreen}
        options={{ tabBarLabel: '订单' }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarLabel: '我的' }}
      />
    </Tab.Navigator>
  );
};
```

Tab导航的核心状态结构和Stack不同。Stack是一个线性的路由栈，有明确的入栈出栈顺序；Tab是一个平铺的路由集合，切换Tab不会销毁其他Tab的页面状态，每个Tab维护自己的路由历史。这是Tab和Stack最本质的区别，理解了这个区别才能正确选择导航方案。

```
Tab导航状态结构:
{
  index: 0,                    // 当前选中的Tab索引
  routes: [
    { name: 'Home', key: 'Home-1' },
    { name: 'Order', key: 'Order-2' },
    { name: 'Profile', key: 'Profile-3' }
  ],
  type: 'tab',
  history: [{ type: 'route', key: 'Home-1' }]
}
```

> Tab导航最大的优势是状态保持。用户在Tab A填了一半的表单，切到Tab B再切回来，表单数据还在。这是因为Tab切换不会卸载页面组件，而Stack跳转是会卸载栈顶以外页面的。理解这个差异对后续的状态管理设计至关重要——如果你需要页面状态保持，用Tab；如果不需要状态保持且需要内存优化，用Stack。

### 5.3.2 Tab图标、文字选中态样式定制

Tab的图标和文字样式定制是产品需求的标配。通过`tabBarIcon`可以自定义每个Tab的图标，配合`focused`参数实现选中态切换：

```tsx
import Icon from 'react-native-vector-icons/MaterialIcons';

<Tab.Screen
  name="Home"
  component={HomeScreen}
  options={{
    tabBarLabel: '首页',
    tabBarIcon: ({ color, size, focused }) => (
      <Icon
        name={focused ? 'home' : 'home-outlined'}
        size={size}
        color={color}
      />
    ),
  }}
/>
```

`tabBarIcon`的参数`color`和`size`是由系统根据`tabBarActiveTintColor`、`tabBarInactiveTintColor`和Tab栏高度自动计算的，不需要手动指定颜色。`focused`是布尔值，表示当前Tab是否被选中。通过`focused`切换不同的图标名称，可以实现选中态图标变化的效果。

实际项目中建议把Tab配置抽成数组统一管理，避免每个Tab.Screen都写一长串重复代码：

```tsx
const tabConfig = [
  { name: 'Home', component: HomeScreen, label: '首页',
    iconActive: 'home', iconInactive: 'home-outlined' },
  { name: 'Order', component: OrderScreen, label: '订单',
    iconActive: 'list-alt', iconInactive: 'list' },
  { name: 'Profile', component: ProfileScreen, label: '我的',
    iconActive: 'person', iconInactive: 'person-outline' },
];

{tabConfig.map(tab => (
  <Tab.Screen key={tab.name} name={tab.name} component={tab.component}
    options={{
      tabBarLabel: tab.label,
      tabBarIcon: ({ color, size, focused }) => (
        <Icon name={focused ? tab.iconActive : tab.iconInactive}
          size={size} color={color} />
      ),
    }} />
))}
```

这种配置驱动的好处是新增Tab只需要在数组里加一项，不需要写JSX代码。而且所有Tab的配置信息集中在一起，便于审查和维护。

> 怕浪猫在实际项目中发现，图标选中态的切换如果用两套不同的图标资源（选中态实心、未选中态空心），视觉体验会比单纯改颜色好很多。这虽然是个小细节，但直接影响用户对APP"精致感"的感知。

### 5.3.3 沉浸式Tab栏适配与样式优化

沉浸式Tab栏指的是Tab栏背景半透明或无边框，和页面内容融为一体的视觉效果。实现沉浸式Tab栏需要处理两个关键点：背景透明度和安全区域适配。

```tsx
<Tab.Navigator
  screenOptions={{
    tabBarStyle: {
      position: 'absolute',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderTopWidth: 0,
      elevation: 0,
      height: 60,
      paddingBottom: 4,
    },
    tabBarLabelStyle: {
      fontSize: 11,
      marginBottom: 4,
    },
    tabBarIconStyle: {
      marginTop: 4,
    },
  }}
>
```

`position: 'absolute'`让Tab栏浮动在内容上方，`borderTopWidth: 0`和`elevation: 0`去掉顶部分割线和阴影。但这里有个坑：绝对定位后Tab栏会遮挡底部内容，需要在页面内容底部加padding。如果你用`ScrollView`或`FlatList`，需要设置`contentContainerStyle={{ paddingBottom: 60 }}`。

更好的方案是使用`react-native-safe-area-context`动态获取安全区域高度：

```tsx
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const MainNavigator = () => {
  const insets = useSafeAreaInsets();
  
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          height: 55 + insets.bottom,
          paddingBottom: insets.bottom,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderTopWidth: 0,
          elevation: 0,
        },
      }}
    >
      {/* ... */}
    </Tab.Navigator>
  );
};
```

> 安全区域适配是RN开发中绕不开的话题。iPhone X以后的机型底部有34pt的安全区域（Home Indicator区域），如果不处理，Tab栏的图标和文字会被底部小横条遮挡。用`useSafeAreaInsets`动态获取是最可靠的方案，不要硬编码高度。怕浪猫见过有人写`paddingBottom: 34`硬编码，结果在Android设备上Tab栏底部多了一大块空白——Android没有这个安全区域。

### 5.3.4 Tab页面切换监听与状态刷新

Tab切换时需要执行某些操作（如刷新数据、上报埋点），React Navigation提供了几种监听方式。

`useFocusEffect`是最常用的方式，在页面获得焦点时执行副作用：

```tsx
import { useFocusEffect } from '@react-navigation/native';

const HomeScreen = ({ navigation }) => {
  useFocusEffect(
    useCallback(() => {
      // 页面获得焦点时执行
      fetchLatestData();
      reportPageView('Home');
      
      return () => {
        // 页面失去焦点时清理
        cancelRequest();
      };
    }, [])
  );
  
  return <View>{/* ... */}</View>;
};
```

`useFocusEffect`的回调在每次页面获得焦点时都会执行，所以配合`useCallback`使用避免重复创建。清理函数在页面失去焦点时执行，适合用来取消网络请求、清除定时器等。

如果只是需要监听Tab切换事件而不需要执行副作用，可以用`addListener`：

```tsx
const HomeScreen = ({ navigation }) => {
  useEffect(() => {
    const unsubscribe = navigation.addListener('tabPress', (e) => {
      // 阻止默认行为可以实现"点击已选中Tab刷新"
      e.preventDefault();
      refreshData();
    });
    
    return unsubscribe;
  }, [navigation]);
};
```

还有一种场景是"Tab切换到当前页时刷新数据，但不是每次都刷新，而是间隔超过一定时间才刷新"。这种需求可以通过记录上次刷新时间来控制：

```tsx
const lastRefreshRef = useRef(0);

useFocusEffect(
  useCallback(() => {
    const now = Date.now();
    if (now - lastRefreshRef.current > 5 * 60 * 1000) {
      // 超过5分钟才刷新
      fetchLatestData();
      lastRefreshRef.current = now;
    }
  }, [])
);
```

> `useFocusEffect`和`addListener`的选择原则：需要执行副作用（如数据加载、状态重置）用`useFocusEffect`，需要监听特定事件（如tabPress、swipeStart）用`addListener`。不要在`useFocusEffect`里做太重的操作，每次Tab切换都重新拉数据会让用户体验卡顿。怕浪猫建议用"时间戳节流"策略，既保证数据新鲜度又不影响体验。

### 5.3.5 中间凸起特殊Tab效果实现

电商类APP常见的设计模式是底部Tab中间有一个凸起的圆形按钮（如发布商品、扫码）。这种效果需要自定义Tab栏布局。

核心思路是用`tabBarButton`替换默认的Tab按钮，配合绝对定位实现凸起效果：

```tsx
<Tab.Screen
  name="Publish"
  component={EmptyScreen}
  options={{
    tabBarLabel: () => null,
    tabBarIcon: ({ focused }) => (
      <View style={styles.publishButton}>
        <Icon name="add" size={30} color="#fff" />
      </View>
    ),
    tabBarButton: (props) => (
      <TouchableOpacity {...props}
        style={[props.style, { top: -20, zIndex: 999 }]}
        onPress={() => navigation.navigate('PublishModal')} />
    ),
  }}
/>

const styles = StyleSheet.create({
  publishButton: {
    width: 50, height: 50, borderRadius: 25,
    backgroundColor: '#e94560',
    justifyContent: 'center', alignItems: 'center',
    elevation: 8,
  },
});
```

这里有几个关键点：`tabBarButton`接收一个自定义组件替换默认按钮，`top: -20`让按钮向上凸起。`tabBarLabel`设为一个返回null的函数，隐藏文字标签。中间Tab通常不对应一个真正的页面，点击后弹出选择面板或跳转到独立页面，所以`component`可以是一个空组件。

实际项目中还需要处理Tab栏和凸起按钮的层级关系。由于绝对定位的按钮可能被相邻Tab遮挡，需要设置较高的`zIndex`。另外，凸起按钮的点击区域要比视觉区域大一些（至少44x44pt），确保用户容易点到。还有一种常见的设计变体是凸起按钮点击后弹出ActionSheet（操作菜单），让用户选择"发布商品"、"发布动态"等操作，而不是直接跳转到一个页面。这种交互模式在微信朋友圈、微博等社交APP中广泛使用。

## 5.4 抽屉Drawer侧边导航开发

### 5.4.1 抽屉路由基础配置与搭建

抽屉导航（Drawer Navigator）提供从屏幕侧边滑出的导航面板，常见于设置页、菜单列表等场景。它的交互模式和Stack、Tab完全不同——Stack是栈式管理，Tab是平铺切换，Drawer是覆盖式抽屉。

```bash
npm install @react-navigation/drawer
npm install react-native-gesture-handler react-native-reanimated
```

注意`react-native-reanimated`需要额外的babel配置，在`babel.config.js`中添加插件：

```js
module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['module:metro-react-native-babel-preset'],
    plugins: ['react-native-reanimated/plugin'],
  };
};
```

基础抽屉配置：

```tsx
import { createDrawerNavigator } from '@react-navigation/drawer';

const Drawer = createDrawerNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Drawer.Navigator
        initialRouteName="Home"
        screenOptions={{
          drawerType: 'front',
          drawerPosition: 'left',
          drawerStyle: { width: 280 },
        }}
      >
        <Drawer.Screen name="Home" component={HomeScreen} />
        <Drawer.Screen name="Settings" component={SettingsScreen} />
        <Drawer.Screen name="About" component={AboutScreen} />
      </Drawer.Navigator>
    </NavigationContainer>
  );
};
```

> `react-native-reanimated/plugin`必须放在babel插件数组的最后一个位置，否则会导致构建报错。这个坑怕浪猫踩过不止一次，每次配置新项目都忘了，白白浪费半小时排查。还有一点：修改babel配置后必须清缓存重启Metro，执行`npx react-native start --reset-cache`，否则新配置不生效。

### 5.4.2 侧边栏自定义布局与样式开发

默认的抽屉侧边栏样式比较朴素，实际项目中通常需要自定义。通过`drawerContent`属性可以完全替换侧边栏内容：

```tsx
const CustomDrawerContent = (props) => {
  return (
    <DrawerContentScrollView {...props}>
      <View style={styles.userInfo}>
        <Image source={{ uri: user.avatar }} style={styles.avatar} />
        <Text style={styles.userName}>{user.name}</Text>
      </View>
      <DrawerItem label="首页"
        icon={({ color, size }) => <Icon name="home" size={size} color={color} />}
        onPress={() => props.navigation.navigate('Home')} />
      <DrawerItem label="设置"
        icon={({ color, size }) => <Icon name="settings" size={size} color={color} />}
        onPress={() => props.navigation.navigate('Settings')} />
      <DrawerSection title="其他">
        <DrawerItem label="关于我们"
          onPress={() => props.navigation.navigate('About')} />
        <DrawerItem label="退出登录" onPress={handleLogout} />
      </DrawerSection>
    </DrawerContentScrollView>
  );
};
```

`DrawerContentScrollView`是React Navigation提供的特殊ScrollView，它会自动处理安全区域和键盘遮挡。如果你用普通的`ScrollView`，底部可能被安全区域截断。

自定义侧边栏的关键是把数据驱动化。实际项目中建议把菜单配置抽成数据，这样菜单项的增删改只需要修改数据数组，不需要动渲染逻辑：

```tsx
const menuItems = [
  { label: '首页', icon: 'home', route: 'Home' },
  { label: '设置', icon: 'settings', route: 'Settings' },
  { label: '关于', icon: 'info', route: 'About' },
];

{menuItems.map(item => (
  <DrawerItem
    key={item.route}
    label={item.label}
    icon={({ color, size }) => (
      <Icon name={item.icon} size={size} color={color} />
    )}
    onPress={() => props.navigation.navigate(item.route)}
  />
))}
```

> 侧边栏的设计要考虑用户的使用频率。把高频操作的菜单项放在顶部，低频的放在底部。怕浪猫见过一个APP把"退出登录"放在侧边栏最顶部，紧挨着用户头像，结果误触率极高。菜单项的排列顺序应该和用户心智模型匹配，不是随便堆上去就行。

### 5.4.3 抽屉手势开关与禁用控制

某些页面需要禁用抽屉手势，比如在编辑表单页面，用户滑动时不小心触发抽屉打开会导致表单数据丢失。React Navigation提供了几种控制方式：

```tsx
// 方式一：Screen级别禁用
<Drawer.Screen
  name="EditProfile"
  component={EditProfileScreen}
  options={{
    drawerEnabled: false,           // 完全禁用抽屉
    swipeEnabled: false,            // 仅禁用滑动手势
  }}
/>

// 方式二：运行时动态控制
const EditProfileScreen = ({ navigation }) => {
  const [isEditing, setIsEditing] = useState(false);
  
  useEffect(() => {
    navigation.setOptions({
      swipeEnabled: !isEditing,
    });
  }, [isEditing, navigation]);
  
  return (
    <View>
      <TextInput
        onFocus={() => setIsEditing(true)}
        onBlur={() => setIsEditing(false)}
      />
    </View>
  );
};
```

`drawerEnabled`设为false后，该页面完全不响应抽屉操作，包括手势和程序化打开。`swipeEnabled`只禁用滑动手势，仍可通过`navigation.openDrawer()`程序化打开。

> 动态控制抽屉手势在表单编辑页面特别有用。用户正在输入时禁用手势防止误触，输入完成后恢复手势。这种细节体验做好了，用户会觉得你的APP很"跟手"，虽然他们说不出具体原因。怕浪猫的产品经理曾经反馈说"这个页面滑动手感不好"，最后发现就是抽屉手势和页面内ScrollView的滑动手势冲突了，禁用抽屉手势后立刻解决。

### 5.4.4 抽屉内部页面跳转逻辑处理

抽屉导航的页面跳转有两种模式：抽屉内跳转和抽屉外跳转。

抽屉内跳转指的是在抽屉侧边栏中点击菜单项跳转到对应页面。跳转后抽屉会自动关闭，展示目标页面。但有个需要注意的点：如果目标页面已经在抽屉的路由栈中，`navigate`不会重新渲染页面，只会切过去。

```tsx
// 抽屉内跳转
const handleMenuPress = (routeName, params?) => {
  navigation.navigate(routeName, params);
  // 不需要手动closeDrawer，navigate会自动关闭
};

// 如果需要重置路由栈再跳转
const handleMenuPressWithReset = (routeName) => {
  navigation.reset({
    index: 0,
    routes: [{ name: routeName }],
  });
};
```

抽屉和Stack嵌套时，跳转逻辑需要注意导航器层级。如果抽屉里嵌套了Stack，从抽屉侧边栏跳转到Stack内的某个子页面，需要用嵌套跳转语法：

```tsx
// 从抽屉跳转到Stack内的子页面
const handleNavigateToDetail = () => {
  navigation.navigate('OrderStack', {
    screen: 'OrderDetail',
    params: { id: 42 },
  });
};
```

这种嵌套跳转的语法是React Navigation 6.x的标准写法，通过`screen`和`params`指定目标导航器内的子路由。如果你直接`navigate('OrderDetail')`而不指定父导航器，可能会跳转失败或跳到错误的位置——因为`OrderDetail`不在当前Drawer的路由表中，它在OrderStack的路由表里。

> 嵌套跳转是React Navigation最容易出错的地方之一。怕浪猫建议在项目里封装一个跳转工具函数，内部处理嵌套导航器的跳转逻辑，对外暴露统一的API。这样业务代码只需要调用`goToPage('OrderDetail', { id: 42 })`，不需要关心目标页面在哪个导航器里。

### 5.4.5 抽屉动画与交互效果定制

默认的抽屉动画是侧边滑入，但React Navigation提供了多种内置动画类型，可以根据产品需求选择最合适的交互模式。选择动画类型时需要考虑导航层级和用户认知——如果抽屉是主导航方式，`back`或`slide`模式更合适，因为它们给用户更强的空间感；如果抽屉是辅助菜单，`front`模式更简洁，不会干扰主内容区。

| drawerType | 效果 | 适用场景 |
|------------|------|---------|
| `front` | 抽屉覆盖在页面上方 | 最常用，侧边菜单 |
| `back` | 页面推开露出抽屉 | 菜单项较多时 |
| `slide` | 页面和抽屉同时滑动 | 视觉效果最丰富 |
| `permanent` | 抽屉常驻显示 | 平板/大屏设备 |

自定义转场动画需要通过`useDrawerProgress`和`useDrawerStatus`实现：

```tsx
import { useDrawerProgress } from 'react-native-reanimated';

const HomeScreen = () => {
  const progress = useDrawerProgress();
  
  const scale = useAnimatedStyle(() => ({
    transform: [{ scale: interpolate(
      progress.value, [0, 1], [1, 0.8]
    )}],
    borderRadius: interpolate(progress.value, [0, 1], [0, 20]),
  }));
  
  return (
    <Animated.View style={[styles.container, scale]}>
      <Text>首页内容</Text>
    </Animated.View>
  );
};
```

这段代码让主页面在抽屉打开时缩小到0.8倍并添加圆角，产生"推远"的视觉效果。`useDrawerProgress`返回一个Reanimated的共享值，范围从0（抽屉关闭）到1（抽屉完全打开），通过`interpolate`可以映射成任何动画属性——缩放、位移、旋转、透明度、圆角等。

> 抽屉动画的定制要有节制。怕浪猫见过有些项目加了太多动画效果——缩放、旋转、模糊、渐变一起上，结果在低端机上卡顿严重。动画的目的是提升体验，不是炫技。在性能和效果之间找到平衡，优先保证流畅度。

## 5.5 嵌套路由与模块化路由管理

### 5.5.1 Tab+Stack多层嵌套路由实现

实际项目中，纯Stack或纯Tab都满足不了需求。最常见的组合是"根Stack + 主Tab + 模块Stack"的三层嵌套结构。

```
RootStack (根栈)
├── AuthStack (认证栈)
│   ├── Login
│   └── Register
├── MainTab (主Tab)
│   ├── HomeStack (首页栈)
│   │   ├── HomeMain
│   │   └── HomeDetail
│   ├── OrderStack (订单栈)
│   │   ├── OrderList
│   │   └── OrderDetail
│   └── ProfileStack (个人中心栈)
│       ├── ProfileMain
│       └── ProfileSetting
└── ModalStack (弹窗栈)
    └── ImageViewer
```

对应的核心代码结构：

```tsx
// 认证栈
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = () => (
  <AuthStack.Navigator>
    <AuthStack.Screen name="Login" component={LoginScreen} />
    <AuthStack.Screen name="Register" component={RegisterScreen} />
  </AuthStack.Navigator>
);

// 首页栈（OrderStack、ProfileStack同理省略）
const HomeStack = createNativeStackNavigator<HomeStackParamList>();
const HomeNavigator = () => (
  <HomeStack.Navigator>
    <HomeStack.Screen name="HomeMain" component={HomeScreen} />
    <HomeStack.Screen name="HomeDetail" component={HomeDetailScreen} />
  </HomeStack.Navigator>
);
```

然后是主Tab和根Stack的组合层：

```tsx
// 主Tab + 根Stack组合
const Tab = createBottomTabNavigator<MainTabParamList>();
const MainTab = () => (
  <Tab.Navigator>
    <Tab.Screen name="Home" component={HomeNavigator}
      options={{ headerShown: false }} />
    <Tab.Screen name="Order" component={OrderNavigator}
      options={{ headerShown: false }} />
    <Tab.Screen name="Profile" component={ProfileNavigator}
      options={{ headerShown: false }} />
  </Tab.Navigator>
);

// 根导航器
const RootStack = createNativeStackNavigator<RootStackParamList>();
const App = () => (
  <NavigationContainer>
    <RootStack.Navigator>
      <RootStack.Screen name="Auth" component={AuthNavigator}
        options={{ headerShown: false }} />
      <RootStack.Screen name="Main" component={MainTab}
        options={{ headerShown: false }} />
    </RootStack.Navigator>
  </NavigationContainer>
);
```

这个结构值得仔细分析。最外层是RootStack，它包含Auth和Main两个入口。Auth是认证模块的栈导航器，Main是Tab导航器。Tab的每个Tab内部又是一个Stack导航器。这种三层嵌套是RN项目的标准结构。

关键配置是`headerShown: false`。Tab页面本身不需要标题栏（每个Tab内部的Stack有自己的标题栏），所以需要隐藏Tab层级的Header。如果不设置`headerShown: false`，你会看到两层标题栏叠在一起——一层来自Tab导航器，一层来自Stack导航器。

> 嵌套路由最常见的坑就是标题栏叠加。解决方案很简单但容易遗漏：每一层导航器都要明确设置`headerShown`。默认值在不同导航器中不同，Stack默认true，Tab默认false，不明确设置就会出问题。怕浪猫建议在Navigator级别统一设置`headerShown: false`，然后在具体需要标题栏的Screen级别单独开启。

### 5.5.2 多业务模块路由拆分方案

当项目有十几个业务模块时，把所有路由配置写在一个文件里会让文件膨胀到几百行，维护困难。正确的做法是按业务模块拆分路由。

每个模块独立管理自己的路由定义：

```ts
// src/screens/home/navigation.ts
export type HomeStackParamList = {
  HomeMain: undefined;
  HomeDetail: { id: number };
  HomeSearch: { keyword?: string };
};

export const homeRoutes = [
  { name: 'HomeMain', component: HomeScreen, 
    options: { title: '首页' } },
  { name: 'HomeDetail', component: HomeDetailScreen, 
    options: { title: '详情' } },
  { name: 'HomeSearch', component: HomeSearchScreen, 
    options: { title: '搜索' } },
] as const;
```

```ts
// src/screens/order/navigation.ts
export type OrderStackParamList = {
  OrderList: { status?: 'all' | 'pending' | 'completed' };
  OrderDetail: { orderId: string };
};

export const orderRoutes = [
  { name: 'OrderList', component: OrderListScreen, 
    options: { title: '订单列表' } },
  { name: 'OrderDetail', component: OrderDetailScreen, 
    options: { title: '订单详情' } },
] as const;
```

各模块的导航器独立创建，然后在根导航器中组合。这种模式的好处是模块之间完全解耦——首页模块不知道订单模块有哪些页面，反之亦然。当需要移除某个模块时，只需要删除该模块的目录和根导航器中的一行注册代码，不会影响其他模块。

> 模块化路由拆分的核心原则是：每个模块自己管理自己的路由定义、类型和配置，根导航器只负责组合。这样模块之间完全解耦，新增模块或删除模块都不影响其他模块的路由配置。怕浪猫在重构一个老项目时，把所有路由拆分到各模块后，新增一个页面只需要在模块内部改两个文件，不需要动其他模块的代码，开发效率提升非常明显。

### 5.5.3 全局路由统一注册与导出

路由拆分后需要一个统一的注册入口，把所有模块的路由类型和组件注册到全局。

```ts
// src/navigation/types.ts
import { HomeStackParamList } from '@/screens/home/navigation';
import { OrderStackParamList } from '@/screens/order/navigation';
import { ProfileStackParamList } from '@/screens/profile/navigation';

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Home: HomeStackParamList;
  Order: OrderStackParamList;
  Profile: ProfileStackParamList;
  ImageViewer: { images: string[]; index?: number };
  Loading: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  Order: undefined;
  Profile: undefined;
};

export type AuthStackParamList = {
  Login: { from?: string };
  Register: undefined;
  ForgotPassword: undefined;
};
```

这些类型定义是整个路由系统的类型基础。任何页面跳转时，TS都会根据这些类型检查路由名称和参数是否匹配。在大型项目中，这种编译时检查能拦截掉大量的低级错误。`RootStackParamList`中的嵌套类型（如`Home: HomeStackParamList`）告诉React Navigation：当你跳转到Home导航器时，可以进一步指定Home内部的子路由和参数。这就是嵌套跳转语法的类型基础。

统一的路由注册表可以做成配置驱动：

```tsx
const routeRegistry = {
  Home: { navigator: HomeStack, initialRoute: 'HomeMain' },
  Order: { navigator: OrderStack, initialRoute: 'OrderList' },
  Profile: { navigator: ProfileStack, initialRoute: 'ProfileMain' },
};

export const getRouteConfig = (name: keyof typeof routeRegistry) => {
  return routeRegistry[name];
};
```

### 5.5.4 路由常量枚举规范化管理

路由名称用字符串硬编码是维护的噩梦。拼写错误不会在编译时报错，只会运行时跳转失败。规范化管理的第一步是定义路由常量枚举：

```ts
// src/routes/routeNames.ts
export const RouteNames = {
  // Auth
  Login: 'Login',
  Register: 'Register',
  ForgotPassword: 'ForgotPassword',
  
  // Main Tab
  Home: 'Home',
  Order: 'Order',
  Profile: 'Profile',
  
  // Home Stack
  HomeMain: 'HomeMain',
  HomeDetail: 'HomeDetail',
  HomeSearch: 'HomeSearch',
  
  // Order Stack
  OrderList: 'OrderList',
  OrderDetail: 'OrderDetail',
  
  // Global
  ImageViewer: 'ImageViewer',
  Loading: 'Loading',
} as const;

export type RouteName = keyof typeof RouteNames;
```

配合TS类型约束，跳转时使用常量而非字符串：

```tsx
// 正确写法：使用常量
navigation.navigate(RouteNames.HomeDetail, { id: 42 });

// 错误写法：字符串硬编码
navigation.navigate('HomeDetail', { id: 42 });
navigation.navigate('HomeDetial', { id: 42 }); // 拼写错误，运行时才报错
```

进一步可以封装一个类型安全的导航方法，让跳转调用更简洁：

```tsx
// src/routes/navigate.ts
export const createSafeNavigate = (navigation: any) => {
  return <T extends keyof RootStackParamList>(
    ...args: RootStackParamList[T] extends undefined
      ? [T]
      : [T, RootStackParamList[T]]
  ) => navigation.navigate(...args);
};

// 使用
const safeNavigate = createSafeNavigate(navigation);
safeNavigate(RouteNames.HomeDetail, { id: 42 });  // 类型安全
safeNavigate(RouteNames.HomeMain);                  // 无参数路由
// safeNavigate(RouteNames.HomeDetail);  // 编译报错：缺少id参数
// safeNavigate(RouteNames.HomeDetail, { title: 'hi' });  // 编译报错：缺少id，title多余
```

> 路由常量枚举看似是小事，但在几十个页面的大型项目中，它能让路由管理的效率提升一个量级。配合IDE的自动补全，输入`RouteNames.`就能看到所有可用路由，再也不用翻代码找路由名称了。怕浪猫团队在引入路由常量后，路由相关的bug减少了约70%，因为大部分问题在编译阶段就被拦住了。

### 5.5.5 大型项目路由架构优化

当项目规模进一步扩大，路由架构需要在以下几个方面持续优化：

**路由懒加载**。RN的Metro bundler默认会把所有代码打包到一个bundle中，路由懒加载在RN中的意义不是减少初始包体积，而是减少初始渲染时间。通过`React.lazy`和`Suspense`可以实现页面的懒加载：

```tsx
const HomeScreen = lazy(() => import('@/screens/home/HomeScreen'));
const OrderScreen = lazy(() => import('@/screens/order/OrderScreen'));

const LazyScreen = ({ component: Component }) => (
  <Suspense fallback={<LoadingSpinner />}>
    <Component />
  </Suspense>
);
```

**路由配置中心化**。把所有路由的元信息集中在一个配置表中，导航器通过遍历配置表动态生成：

```ts
export const routeConfig = [
  {
    name: RouteNames.Home,
    module: 'home',
    component: HomeScreen,
    options: { title: '首页' },
    requiresAuth: true,
    tabConfig: { icon: 'home', label: '首页' },
  },
  {
    name: RouteNames.Login,
    module: 'auth',
    component: LoginScreen,
    options: { title: '登录' },
    requiresAuth: false,
  },
] as const;
```

这种配置驱动的方式让路由管理变得声明式。新增页面只需要在配置表中加一条记录，不需要修改导航器代码。路由守卫也可以直接读取配置表中的`requiresAuth`字段来决定是否需要拦截。配置驱动还有一个好处：你可以通过遍历配置表自动生成路由文档，列出所有页面的名称、所属模块、是否需要登录、所需权限等信息，这对项目管理和新人onboarding非常有帮助。

**路由性能监控**。在大型项目中，页面切换耗时是影响用户体验的关键指标。可以通过导航事件监听来采集性能数据：

```tsx
navigation.addListener('transitionStart', (e) => {
  perfMonitor.start('page_transition');
});

navigation.addListener('transitionEnd', (e) => {
  perfMonitor.end('page_transition');
});
```

把采集到的耗时数据上报到监控平台，就能量化每个页面的切换性能。当某个页面切换耗时超过阈值（比如500ms）时，可以触发告警，及早发现性能问题。

## 5.6 路由守卫与权限拦截实战

### 5.6.1 全局路由拦截原理与实现

路由守卫的概念来自Web前端（特别是Vue Router），核心思想是在路由跳转前后执行拦截逻辑，判断是否允许跳转或重定向到其他页面。

React Navigation没有内置路由守卫，但提供了`getStateForAction`和`navigationRef`等能力，可以实现等效的拦截机制。

全局路由拦截的核心原理图：

```
用户触发跳转
      │
      ▼
┌──────────────┐     拦截      ┌──────────────┐
│  navigate()  │ ──────────▶  │  路由守卫     │
│  调用        │              │  拦截器       │
└──────────────┘              └──────┬───────┘
                                     │
                              ┌──────┴───────┐
                              │              │
                           允许            拒绝
                              │              │
                              ▼              ▼
                        ┌──────────┐  ┌───────────┐
                        │ 正常跳转  │  │ 重定向到   │
                        │ 到目标页  │  │ 登录/403页 │
                        └──────────┘  └───────────┘
```

实现全局拦截的第一种方式是使用`navigationRef`配合`beforeRemove`事件：

```tsx
import { NavigationContainerRef } from '@react-navigation/native';

const navigationRef = React.createRef<NavigationContainerRef<any>>();

const guardedNavigate = (name: string, params?: any) => {
  const state = navigationRef.current?.getRootState();
  const currentRoute = state?.routes[state.index];
  
  // 全局前置守卫
  if (!isAuthenticated() && guardedRoutes.includes(name)) {
    navigationRef.current?.navigate('Login', { from: name });
    return false;
  }
  
  // 权限校验
  if (!hasPermission(name)) {
    navigationRef.current?.navigate('NoPermission');
    return false;
  }
  
  navigationRef.current?.navigate(name, params);
  return true;
};

export { navigationRef, guardedNavigate };
```

> 路由守卫的本质是在`navigate`调用和实际跳转之间插入一个判断层。理解了这个原理，你就能灵活地在任何路由库上实现权限控制，而不依赖框架是否原生支持。怕浪猫建议把所有路由跳转都统一走`guardedNavigate`函数，而不是直接调用`navigation.navigate`，这样守卫逻辑才能覆盖到所有的跳转入口。

### 5.6.2 未登录页面跳转拦截处理

最常见的拦截场景是登录校验。需要区分哪些页面需要登录，哪些不需要。通过路由配置中的`requiresAuth`字段来标记：

```tsx
// 需要登录的路由白名单
const authRequiredRoutes = [
  RouteNames.HomeDetail, RouteNames.OrderList,
  RouteNames.OrderDetail, RouteNames.ProfileMain,
  RouteNames.ProfileSetting,
];

// 导航拦截器
const useAuthGuard = () => {
  const navigation = useNavigation();
  const { token } = useAuthStore();
  
  const guardedNavigate = useCallback(
    (routeName: string, params?: any) => {
      const requiresAuth = authRequiredRoutes.includes(routeName);
      if (requiresAuth && !token) {
        AsyncStorage.setItem('redirect_after_login',
          JSON.stringify({ routeName, params }));
        navigation.navigate(RouteNames.Login, { from: routeName });
        return;
      }
      navigation.navigate(routeName, params);
    }, [navigation, token]
  );
  return { guardedNavigate };
};
```

登录成功后恢复跳转：

```tsx
const LoginScreen = () => {
  const navigation = useNavigation();
  
  const handleLoginSuccess = async () => {
    const redirect = await AsyncStorage.getItem('redirect_after_login');
    if (redirect) {
      const { routeName, params } = JSON.parse(redirect);
      AsyncStorage.removeItem('redirect_after_login');
      navigation.replace(routeName, params);
    } else {
      navigation.replace(RouteNames.Main);
    }
  };
  
  return (/* ... */);
};
```

这种"登录后恢复跳转"的体验在电商APP中非常常见：用户在浏览商品时点击"立即购买"，发现没登录，跳转到登录页，登录成功后直接回到下单页而不是首页。这个体验看似简单，但如果没有`redirect_after_login`机制，用户登录后只能回到首页，需要重新找到刚才那个商品，体验非常差。

> 登录拦截的设计要考虑边界场景：用户在登录页直接杀掉APP再打开，`redirect_after_login`还在不在？如果用AsyncStorage存储就在，如果用内存变量就不在。怕浪猫建议用AsyncStorage持久化存储，并在APP启动时检查是否有未完成的跳转，如果目标页面不需要登录就自动恢复，需要登录就清除记录。

### 5.6.3 页面权限白名单配置

除了登录校验，企业级应用还需要更细粒度的权限控制。比如普通用户不能访问管理员页面，VIP用户才能访问会员专属页面。

权限白名单的核心数据结构：

```ts
// src/routes/permissions.ts
export type RoutePermission = {
  routeName: string;
  requiredRoles: string[];
  requiredPermissions: string[];
};

export const routePermissions = [
  { routeName: RouteNames.AdminDashboard,
    requiredRoles: ['admin'],
    requiredPermissions: ['admin:dashboard:view'] },
  { routeName: RouteNames.VipContent,
    requiredRoles: ['vip', 'admin'], requiredPermissions: [] },
  { routeName: RouteNames.OrderDetail,
    requiredRoles: [],
    requiredPermissions: ['order:detail:view'] },
] as RoutePermission[];
```

权限检查函数：

```ts
export const checkRoutePermission = (
  routeName: string,
  userRoles: string[],
  userPermissions: string[]
): boolean => {
  const config = routePermissions.find(p => p.routeName === routeName);
  if (!config) return true; // 无配置则允许访问
  const hasRole = config.requiredRoles.length === 0
    || config.requiredRoles.some(r => userRoles.includes(r));
  const hasPerm = config.requiredPermissions.length === 0
    || config.requiredPermissions.every(p => userPermissions.includes(p));
  return hasRole && hasPerm;
};
```

在拦截器中集成权限检查：

```tsx
const guardedNavigate = (routeName: string, params?: any) => {
  // 1. 登录校验
  if (authRequiredRoutes.includes(routeName) && !token) {
    navigation.navigate(RouteNames.Login);
    return;
  }
  
  // 2. 权限校验
  const hasPermission = checkRoutePermission(
    routeName, userRoles, userPermissions
  );
  if (!hasPermission) {
    navigation.navigate(RouteNames.NoPermission);
    return;
  }
  
  // 3. 通过校验，执行跳转
  navigation.navigate(routeName, params);
};
```

> 权限设计的关键是"最小权限原则"。默认拒绝所有访问，只有明确配置了权限的路由才允许访问。这样当新增一个页面忘了配置权限时，用户看到的是无权限提示而不是本不该看到的页面内容。怕浪猫在做一个后台管理APP时，就是因为忘了给"财务报表"页配置权限，导致普通员工也能看到公司财务数据，差点酿成事故。从那以后，怕浪猫所有路由权限都是"默认拒绝，显式允许"。

### 5.6.4 路由跳转防抖与重复拦截

快速连续点击导致页面重复打开是移动端的经典问题。用户快速双击一个按钮，页面被push了两次，返回时需要按两次返回键才能回到上一个页面。更严重的情况是，某些涉及支付或下单的操作，重复跳转可能导致重复提交。

解决方案是在导航层做防抖：

```tsx
// 简单防抖
let lastNavigateTime = 0;
const NAVIGATE_THROTTLE = 500;

export const debouncedNavigate = (
  navigation: any,
  routeName: string,
  params?: any
) => {
  const now = Date.now();
  if (now - lastNavigateTime < NAVIGATE_THROTTLE) {
    return;
  }
  lastNavigateTime = now;
  navigation.navigate(routeName, params);
};
```

进一步优化：只拦截相同路由的连续跳转，不同路由的快速跳转不拦截：

```tsx
let lastRoute: { name: string; time: number } = { name: '', time: 0 };

export const smartNavigate = (
  navigation: any,
  routeName: string,
  params?: any
) => {
  const now = Date.now();
  if (routeName === lastRoute.name
      && now - lastRoute.time < NAVIGATE_THROTTLE) {
    return; // 相同路由在500ms内重复跳转，拦截
  }
  lastRoute = { name: routeName, time: now };
  navigation.navigate(routeName, params);
};
```

这种"智能防抖"方案更精准。它只拦截相同路由的连续跳转，不会误拦链式跳转（如A跳B、B自动跳C的场景）。在实际项目中，链式跳转很常见——比如从通知点击进入订单详情页，详情页加载时发现订单状态变更又自动跳转到评价页，这种场景下如果防抖太激进，第二步跳转会被误拦。

> 防抖拦截看似是个小细节，但对用户体验的提升非常明显。没有防抖的APP，用户经常遇到"怎么返回了好几次才回到上一个页面"的困惑。加上防抖后，这种问题完全消失。怕浪猫建议把防抖逻辑封装到统一的导航工具函数中，全局替换`navigation.navigate`的调用，这样不需要在每个按钮上单独处理。

### 5.6.5 路由异常容错与兜底方案

路由跳转可能因为各种原因失败：路由名称不存在、参数校验失败、页面组件加载异常等。没有容错机制时，这些异常会导致白屏或崩溃。

完整的异常容错方案包含三个层面：

**跳转前校验**。在执行跳转前检查路由是否存在、参数是否合法：

```tsx
const safeNavigate = (navigation, routeName, params?) => {
  const state = navigation.getState();
  const routeExists = state.routeNames?.includes(routeName);
  if (!routeExists) {
    console.warn(`路由 "${routeName}" 不存在`);
    return false;
  }
  
  try {
    navigation.navigate(routeName, params);
    return true;
  } catch (error) {
    console.error(`跳转失败: ${error}`);
    return false;
  }
};
```

**页面加载异常兜底**。使用Error Boundary包裹页面组件，防止某个页面崩溃导致整个APP白屏：

```tsx
class ScreenErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    reportError('screen_crash', { error: error.message });
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>页面加载失败</Text>
          <Text style={styles.errorDesc}>请返回重试或联系客服</Text>
          <TouchableOpacity onPress={() => this.setState({ hasError: false })}>
            <Text style={styles.retryBtn}>重试</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}
```

**全局导航异常处理**。通过`NavigationContainer`的`onStateChange`监听路由变化，在异常状态时执行兜底逻辑：

```tsx
<NavigationContainer
  onStateChange={(state) => {
    try {
      const currentRoute = state?.routes[state.index];
      AsyncStorage.setItem('last_route', currentRoute?.name);
    } catch (e) {
      console.error('导航状态异常', e);
    }
  }}
>
```

这套三层容错方案能覆盖绝大多数路由异常场景。跳转前校验拦截了大部分非法跳转，Error Boundary防止了页面级崩溃蔓延到全局，全局异常处理兜底了导航器自身的异常。此外，`onStateChange`中保存的`last_route`还可以用于APP崩溃恢复——APP重启后读取上次的路由，自动恢复到用户之前所在的页面。这在用户体验上是一个很小的细节，但在用户感知上差别巨大——用户以为APP崩溃了所有状态都没了，结果重启后发现回到了之前的页面，这种"无缝恢复"的体验会让用户对APP的好感度大幅提升。

> 生产环境中路由异常的容错和正常流程一样重要。用户遇到的白屏问题，80%以上都可以通过合理的异常处理避免。怕浪猫的建议是：宁可显示一个"页面加载失败"的提示页，也不要让用户面对一个无响应的白屏。错误提示至少让用户知道发生了什么，而白屏只会让用户以为APP卡死了然后强制杀掉。

至此，我们从技术选型到栈路由、Tab导航、抽屉导航、嵌套路由、路由守卫，完整走了一遍React Navigation企业级路由导航的开发流程。这套方案不是理论推演，而是我在实际项目中反复打磨过的实战架构。从最初的路由方案选择到最终的路由异常容错，每一步都包含着实战中积累的经验教训。路由设计是RN项目的地基，地基打得扎实，上层业务开发才能又快又稳。

下一章我们将进入状态管理的话题，探讨Redux Toolkit、Zustand等状态管理方案在RN项目中的实战应用，以及如何设计全局状态与局部状态的边界。状态管理和路由导航是RN架构的两大基石，搞定了这两块，你的项目架构就有了坚实的底座。

怕浪猫说：路由导航这东西，入门容易精通难。装个库配几个页面谁都会，但真正到了几十个页面、多模块嵌套、需要权限拦截的项目里，各种边界问题就全冒出来了。怕浪猫踩过的坑你们不用再踩，把这套架构方案落地到项目里，能省下不少加班时间。记住，架构的价值不在于多炫酷，而在于让团队成员都能高效地开发，让新人能快速地上手，让bug无处藏身。

系列进度 5/16

---
sidebar_position: 2
---

# 第2章 RN基础语法、项目配置与调试技巧

90%的RN新手在第一周就会遇到这样的场景:项目跑起来了,但改个配置就白屏;代码写完了,但调试不知道从哪下手;JSX(JavaScript XML)语法看着像HTML,却总是报莫名其妙的错误。更扎心的是,配置文件、类型约束、调试工具这些基础内容,几乎没有一篇教程系统性地讲透过,都是东拼西凑,遇到问题就抓瞎。

我是怕浪猫,一个在RN(React Native)坑里摸爬滚打多年的开发者。这一章我把项目核心配置、JSX移动端语法、列表渲染、TypeScript(简称TS)类型约束和全场景调试技巧打包讲透,帮你跨过新手期最容易栽跟头的那几道坎。学完这一章,你不仅能看懂项目的每一行配置,还能独立排查开发中遇到的大部分问题。

> 配置文件不是项目的装饰品,而是工程化的地基。地基不稳,楼层越高越危险。

## 2.1 RN项目核心配置文件详解

一个标准的RN项目根目录下,有4个配置文件决定了项目的运行行为:package.json管理依赖与脚本,app.json配置应用级参数,metro.config.js控制打包编译流程,tsconfig.json约束类型系统。理解它们的作用,是规范化开发的第一步。

### 2.1.1 package.json依赖与脚本配置

package.json是项目的"身份证",记录了项目名称、版本、依赖包和可执行脚本。RN项目的package.json与Web项目结构一致,但依赖内容有显著差异。

```json
{
  "name": "MyApp",
  "version": "1.0.0",
  "scripts": {
    "start": "react-native start",
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "lint": "eslint .",
    "test": "jest"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.74.0",
    "@react-navigation/native": "^6.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.1.0",
    "@react-native/eslint-config": "^0.74.0"
  }
}
```

这里有几个关键点需要特别注意。dependencies中放的是生产环境也需要的包,比如react和react-native核心库。devDependencies中放的是开发阶段才需要的工具,比如typescript和eslint。scripts中配置的命令可以通过`npm run xxx`执行。

版本号前的符号也有讲究。`^`表示兼容该大版本的最新小版本,比如`^6.1.0`会匹配6.x.x的最新版本。`~`表示兼容该小版本的最新补丁版本。不带符号的精确版本号表示锁定该版本。

> 依赖版本不要随便用latest,RN对版本敏感度极高,一个不兼容的版本就能让你调试一整天。怕浪猫吃过这个亏,一个react-navigation的版本升级导致整个路由体系重构。

在实际企业项目中,建议对依赖版本进行锁定。使用package-lock.json或yarn.lock文件确保团队成员安装的依赖版本完全一致。版本不一致导致的"在我电脑上能跑"问题,是协作开发中最常见的痛点之一。怕浪猫曾经在团队中遇到过这样一个真实案例:开发同学在本地安装了一个第三方组件库的最新版本,测试也通过了,但是到了CI/CD(Continuous Integration/Continuous Deployment,持续集成/持续部署)流水线上打包时,因为流水线没有使用lock文件,自动安装了一个更新的版本,导致API不兼容,打包直接失败。排查花了整整半天时间,最后发现是版本号差了一个小版本号。从那以后,团队规定所有依赖版本必须精确到补丁号,禁止使用^和~。

### 2.1.2 app.json全局应用参数配置

app.json是RN应用的全局配置文件,用于定义应用名称、屏幕方向、图标、权限等原生层面的参数。这个文件的配置会在打包时被写入原生工程。

```json
{
  "name": "MyApp",
  "displayName": "我的应用",
  "ios": {
    "bundleIdentifier": "com.company.myapp",
    "buildNumber": "1"
  },
  "android": {
    "package": "com.company.myapp",
    "versionCode": 1
  }
}
```

name字段是应用在原生端的注册名称,必须与原生代码中的`appRegistry.registerComponent`名称一致。displayName是用户在桌面上看到的应用名称。ios.bundleIdentifier和android.package分别是双端的应用包名,一旦上架就不能随意修改。

buildNumber和versionCode是版本号的区分。iOS用buildNumber标识构建版本,每次上传到App Store Connect都需要递增。Android用versionCode标识构建版本,必须是整数,且每次发布新版本时必须递增,否则应用商店会拒绝上传。在app.json中配置的版本信息会被原生构建脚本读取,不需要手动修改Android的build.gradle或iOS的Info.plist文件。这种集中式配置的好处是保持双端版本号一致,避免出现Android是2.0版本而iOS还是1.9版本的情况。

在多环境场景下,可以通过react-native-config等库实现app.json中字段的动态替换。比如测试版应用名称显示"我的应用(测试)",生产版显示"我的应用"。这种差异化配置在QA(Quality Assurance,质量保证)测试时特别有用。除了应用名称,常见的差异化配置还包括应用图标、启动屏颜色、接口地址、第三方SDK的AppKey等。比如微信登录功能,在开发环境使用测试号的AppKey,在生产环境使用正式号的AppKey,避免开发阶段的测试数据污染正式环境。这种做法在企业开发中几乎是标配,没有多环境配置的项目在协作开发时必然会出问题。

关于app.json还有一个容易忽略的细节:文件中配置的name字段会被原生端用来注册组件。在Android的MainApplication.java文件中,ReactNativeHost的getJSMainModuleName指向了index文件,而index文件中的AppRegistry.registerComponent注册名称必须与app.json中的name一致。如果两者不一致,应用启动后会直接白屏,没有任何错误提示,这是新手最容易踩的坑之一。

### 2.1.3 metro.config打包编译配置解析

Metro是RN的JavaScript打包工具,类似于Web端的Webpack(一种前端模块打包工具)。metro.config.js文件用于自定义打包行为,包括模块解析规则、转换器配置、缓存策略等。

```js
const { getDefaultConfig, mergeConfig } = require('metro-config');

const customConfig = {
  resolver: {
    assetExts: ['png', 'jpg', 'jpeg', 'gif', 'webp'],
    sourceExts: ['js', 'jsx', 'ts', 'tsx', 'json']
  },
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
};

module.exports = mergeConfig(
  getDefaultConfig(__dirname),
  customConfig
);
```

resolver.assetExts定义了哪些文件扩展名被视为静态资源。sourceExts定义了哪些文件扩展名被视为源代码。如果你使用了自定义的文件扩展名,比如.svg或.md,需要在这里添加才能被Metro正确识别。

inlineRequires选项是一个性能优化利器。开启后,require调用会被内联处理,减少模块加载时的运行时开销。RN官方推荐在生产环境中开启此选项,可以显著减少启动时间。

> Metro打包工具的核心流程是:解析入口文件、构建依赖图、转换模块、序列化输出。理解这条链路,后面做打包优化时就知道该从哪里入手了。

```
Metro打包流程示意图:

入口文件(App.tsx)
    |
    v
[Resolution] 解析依赖关系,构建依赖图
    |
    v
[Transformation] Babel转换TS/JSX为JS
    |
    v
[Serialization] 生成Bundle文件
    |
    v
推送到模拟器/真机执行
```

Metro的缓存机制也值得了解。它会在node_modules/.cache/metro目录下缓存已转换的模块。当你修改了一个文件后,Metro只需要重新转换该文件及其依赖链,而不是整个项目。这就是为什么热更新通常只需要几百毫秒的原因。如果遇到奇怪的缓存问题,比如修改了代码但页面没变化、或者突然出现莫名的编译错误,可以清除缓存重启:`npm start -- --reset-cache`。清除缓存后首次启动会稍慢,因为需要重新转换所有模块,但之后就会恢复正常速度。

在实际开发中,Metro还支持多端口配置。如果你的电脑上同时跑了多个RN项目,默认端口8081会冲突。可以通过`react-native start --port=8082`指定不同的端口。模拟器或真机连接时也需要在开发者菜单中通过"Change Bundle Location"修改Metro服务地址,确保指向正确的端口。这种多项目并行的场景在同时维护多个RN应用时很常见,了解这个配置能省去不少麻烦。另外,Metro还支持通过配置文件自定义缓存策略,比如设置maxWorkerCount来控制并行转换的进程数。在CPU核数较多的机器上增加worker数量可以加快首次启动速度,但在内存较小的机器上可能导致OOM(Out Of Memory,内存不足)错误。默认配置会根据机器性能自动调整,一般不需要手动修改。

### 2.1.4 tsconfig.json类型约束配置

TypeScript是JavaScript(简称JS)的超集,提供了静态类型检查能力。tsconfig.json是TS编译器的配置文件,决定了TS如何编译和类型检查。

```json
{
  "extends": "@tsconfig/react-native/tsconfig.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"]
    },
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

extends字段继承RN官方提供的TS配置预设,省去了从零配置的麻烦。baseUrl和paths配合使用可以实现路径别名,避免使用`../../../`这样的相对路径。strict开启后,TS会执行最严格的类型检查,强烈建议开启。

noUnusedLocals和noUnusedParameters会检查未使用的变量和参数,有助于保持代码整洁。include指定了需要类型检查的文件范围,exclude指定了需要排除的目录。

strict模式实际上是一组严格类型检查选项的集合,包含strictNullChecks、strictFunctionTypes、strictBindCallApply等。开启后,null和undefined不再可以赋值给任意类型,函数参数类型检查也更加严格。虽然初期可能会遇到大量类型报错,但这些报错都是潜在bug的预警。比如一个函数期望接收string类型的参数,但调用方传入了一个string | null类型的值,strict模式下TS会报错,提醒你先处理null的情况。这个看似简单的检查,能够避免大量"undefined is not a function"这类运行时错误。

对于从JS项目迁移到TS的项目,可以分阶段开启严格模式。第一步先开启strictNullChecks,这是性价比最高的一个选项,能拦截最多的潜在空指针错误。第二步开启noImplicitAny,禁止隐式的any类型。第三步再开启完整的strict模式。渐进式迁移比一步到位更容易在团队中推行,也更容易让团队成员接受TypeScript。

### 2.1.5 多环境开发配置差异化方案

企业项目中通常存在开发、测试、生产三个环境,每个环境的接口地址、应用名称、功能开关都不同。手动修改配置既容易出错又低效,而且容易把测试配置带到生产包中。

最常用的方案是react-native-config库。安装后,在项目根目录创建多个.env文件:

```bash
# .env.development
API_BASE_URL=https://dev.api.com
APP_NAME=我的应用(开发)

# .env.staging
API_BASE_URL=https://staging.api.com
APP_NAME=我的应用(测试)

# .env.production
API_BASE_URL=https://api.com
APP_NAME=我的应用
```

在代码中通过Config模块读取这些环境变量:

```js
import Config from 'react-native-config';

const apiClient = axios.create({
  baseURL: Config.API_BASE_URL,
  timeout: 15000,
});
```

在package.json中配置不同的启动命令:

```json
{
  "scripts": {
    "start:dev": "ENVFILE=.env.development react-native start",
    "start:staging": "ENVFILE=.env.staging react-native start",
    "start:prod": "ENVFILE=.env.production react-native start"
  }
}
```

> 多环境配置的核心原则是:配置与代码分离,环境差异通过变量注入而非硬编码实现。这样不仅减少了出错概率,还让代码review时能一眼看出当前用的是哪个环境。

以下是多环境配置的对比方案表,建议收藏参考:

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| react-native-config | 支持双端原生读取 | 需额外安装配置 | 中大型项目 |
| 自定义env文件加脚本 | 无第三方依赖 | 原生端不支持 | 小型项目 |
| babel-plugin-transform-inline | 编译时替换 | 灵活性有限 | 简单场景 |
| react-native-dotenv | 轻量易用 | 仅JS层 | 纯JS项目 |

## 2.2 JSX移动端专属语法规范

JSX(JavaScript XML)是React中用于描述UI结构的语法扩展。RN中的JSX与Web端的JSX在语法上基本一致,但运行环境和可用组件有本质区别。这一节重点讲解RN中JSX的特殊之处。

### 2.2.1 JSX语法规则与书写标准

JSX的本质是`React.createElement`的语法糖。每一段JSX最终都会被Babel(一种JS编译器)编译成函数调用。理解这一点对于后续学习组件原理至关重要。

```jsx
// JSX写法
const element = <Text>Hello World</Text>;

// 编译后的实际代码
const element = React.createElement(Text, null, 'Hello World');
```

JSX的核心规则有几条:标签必须闭合,属性使用驼峰命名,表达式用花括号包裹,只能有一个根元素。这些规则在RN中同样适用,违反任何一条都会导致编译报错。

```jsx
// 正确写法:驼峰命名、花括号表达式、单根元素
function Greeting({ name }: { name: string }) {
  return (
    <View style={styles.container}>
      <Text>Hello, {name}!</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#fff' },
});
```

> JSX不是HTML,它是JavaScript的扩展。把这一点刻在脑子里,你就能理解为什么RN中用style而不是class,为什么事件用onPress而不是onclick。

### 2.2.2 RN无DOM/BOM的语法差异

这是从Web转向RN最容易踩的坑。RN运行在原生环境中,没有DOM(Document Object Model,文档对象模型)和BOM(Browser Object Model,浏览器对象模型),这意味着所有依赖浏览器对象的API都无法使用。

```
Web端 vs RN端 API对照表:

Web端                  RN端替代方案
document               无(使用refs操作组件)
window                 无(使用Platform模块)
localStorage           AsyncStorage
navigator              无(使用第三方库)
div                    View
span/p/h1              Text
img                    Image
onclick                onPress
input                  TextInput
scroll                 ScrollView/FlatList
```

以下代码在Web端正常但在RN中会报错:

```js
// 这些在RN中全部不可用,会直接红屏报错
document.getElementById('app');
window.location.href = '/home';
localStorage.setItem('key', 'value');
navigator.userAgent;
```

RN中对应的替代方案:

```js
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Linking, Platform } from 'react-native';

await AsyncStorage.setItem('key', 'value');
await Linking.openURL('https://example.com');
const isIOS = Platform.OS === 'ios';
```

怕浪猫第一次写RN的时候,习惯性地写了`document.querySelector`,结果红屏报错找了半天。这个弯一定要拐过来。RN中没有DOM的概念,所有UI操作都通过组件的props和state来完成。

> 从Web转RN最大的思维转变是:从"命令式操作DOM"变成"声明式驱动组件"。你不告诉RN怎么更新UI,你只告诉RN当前的状态是什么,RN自动帮你算出该怎么更新。

### 2.2.3 表达式渲染与注释规范

JSX中使用花括号`{}`嵌入JavaScript表达式。任何有返回值的JavaScript代码都可以放在花括号中,这是JSX最强大的特性之一。

```jsx
function ProductCard({ product }: { product: ProductType }) {
  const priceText = `¥${product.price.toFixed(2)}`;
  const isOnSale = product.originalPrice > product.price;

  return (
    <View>
      {/* 这是一个JSX注释,用花括号包裹 */}
      <Text style={{ fontSize: 16 }}>{product.name}</Text>
      <Text style={{ color: '#ff4d4f' }}>{priceText}</Text>
      {/* 三元表达式也是合法的表达式 */}
      <Text>{product.stock > 0 ? '有货' : '缺货'}</Text>
      {/* 逻辑与短路也是表达式 */}
      {isOnSale && <Text style={{ color: 'red' }}>促销中</Text>}
      {/* 方法调用也是表达式 */}
      <Text>{product.tags.join(' | ')}</Text>
    </View>
  );
}
```

JSX注释的写法是`{/* 注释内容 */}`,注意不能使用HTML的`<!-- -->`注释语法。在花括号中可以放变量、函数调用、三元表达式、map遍历等任何JavaScript表达式,但不能放语句(如if、for、switch)。

> 表达式和语句的区别:表达式有返回值,语句没有。`const a = 1`是语句,`a + 1`是表达式。JSX的花括号只接受表达式。如果你需要写if语句,请提取成函数。

### 2.2.4 条件渲染三种实现方案

RN中条件渲染有三种常用方案,各有适用场景。选对方案能让代码可读性大幅提升。

方案一:三元表达式,适合简单的二选一场景

```jsx
function LoginStatus({ isLoggedIn }: { isLoggedIn: boolean }) {
  return (
    <View>
      {isLoggedIn ? (
        <Text style={{ color: '#52c41a' }}>欢迎回来</Text>
      ) : (
        <Text style={{ color: '#999' }}>请先登录</Text>
      )}
    </View>
  );
}
```

方案二:逻辑与(&&)短路,适合"满足条件才渲染"的场景

```jsx
function Notification({ message }: { message?: string }) {
  return (
    <View>
      {message && <Text>{message}</Text>}
    </View>
  );
}
```

使用逻辑与时有一个经典坑:如果表达式左侧是数字0,`0 && <Component />`会渲染出`0`而不是什么都不渲染。这是因为0是falsy值,逻辑与运算的结果是0本身,而React会把0作为合法的子节点渲染出来。解决方案是使用三元表达式`{count > 0 && <Component />}`或者将左侧转为布尔值`{Boolean(count) && <Component />}`或者使用`{!!count && <Component />}`。这个坑在RN中尤其常见,因为列表长度、库存数量等数字场景很多。

另外需要提醒的是,条件渲染中的逻辑与运算符不要嵌套使用。`{a && b && <Component />}`这种写法虽然语法上没问题,但可读性很差。更好的做法是提取成一个布尔变量`{shouldRender && <Component />}`,其中`const shouldRender = a && b`。代码的 readability(可读性)比简洁性更重要,尤其是在团队协作的场景下。

方案三:提取函数,适合复杂的条件判断

```jsx
function OrderStatus({ status }: { status: string }) {
  const renderStatus = () => {
    switch (status) {
      case 'pending': return <Text>待支付</Text>;
      case 'paid': return <Text>已支付</Text>;
      case 'shipped': return <Text>已发货</Text>;
      default: return <Text>未知状态</Text>;
    }
  };
  return <View>{renderStatus()}</View>;
}
```

> 条件渲染选择原则:简单二选一用三元,单条件用&&,复杂逻辑抽函数。不要把三行以上的逻辑硬塞进花括号里。花括号中应该只放简洁的表达式,超过两层的嵌套就应该考虑提取为变量或函数,否则后续维护时阅读成本很高,团队成员看起来也痛苦。

### 2.2.5 JSX常见语法错误排查技巧

JSX错误是RN新手最高频遇到的问题。以下是几个典型错误和排查方法。

错误一:多个根元素。JSX表达式必须只有一个根元素,多个元素需要用Fragment或View包裹。这个错误在刚从HTML转JSX的开发者中特别常见,因为HTML中多个标签并列是常态。使用Fragment包裹不会产生额外的原生节点,性能上更优。但如果你需要在包裹容器上加样式,用View更合适。

```jsx
// 错误:返回了多个根元素
function Bad() {
  return (
    <Text>Hello</Text>
    <Text>World</Text>
  );
}

// 正确:使用Fragment
function Good() {
  return (
    <>
      <Text>Hello</Text>
      <Text>World</Text>
    </>
  );
}
```

错误二:style写成字符串。RN的style属性接收对象或数组,不是字符串。

```jsx
// 错误:RN不支持字符串style
<Text style="color: red">Hello</Text>

// 正确:对象形式
<Text style={{ color: 'red' }}>Hello</Text>

// 正确:数组形式(后者覆盖前者)
<Text style={[{ color: 'red' }, { fontSize: 14 }]}>Hello</Text>
```

错误三:使用了Web标签。RN中没有div、span、p等HTML标签,必须使用RN组件。

```jsx
// 错误
<div><p>Hello</p></div>

// 正确
<View><Text>Hello</Text></View>
```

排查这类错误的最快方法是查看Metro打包器的终端输出。Babel编译错误通常会精确指向问题所在的文件和行号。错误信息中还会包含具体的语法错误描述,比如"Unexpected token"表示语法不符合JSX规范。把错误信息复制到搜索引擎中,通常前几个搜索结果就有解决方案。Stack Overflow上关于RN报错的问答非常丰富,大部分常见问题都能找到现成的解答。

除了Metro终端的报错信息,RN的Red Screen(红屏)也是重要的错误诊断来源。红屏页面会显示完整的错误堆栈,包括错误消息、发生的文件和行号、以及调用链。在开发阶段,红屏是你的朋友而不是敌人--它在第一时间告诉你出了什么问题、在哪里出的问题。很多新手看到红屏会慌,怕浪猫的建议是:冷静看完整错误信息,错误原因通常写在最上面一行。如果是英文看不懂,复制到翻译工具中翻译一下就能理解大意。

> 遇到红屏不要慌,先看终端的报错信息。90%的问题都能从错误信息中找到答案。

## 2.3 列表渲染与基础数据处理

列表是移动端最常见的UI形态。RN中列表渲染主要使用map方法,配合key属性实现高效更新。

### 2.3.1 map遍历列表渲染核心用法

map方法是RN列表渲染的基础。它遍历数组并对每个元素返回一个JSX元素,最终生成一个元素数组供React渲染。

```tsx
interface Product {
  id: number;
  name: string;
  price: number;
}

function ProductList({ products }: { products: Product[] }) {
  return (
    <View>
      {products.map((item) => (
        <View key={item.id} style={styles.item}>
          <Text style={styles.name}>{item.name}</Text>
          <Text style={styles.price}>¥{item.price}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  item: { padding: 12, borderBottomWidth: 1, borderColor: '#eee' },
  name: { fontSize: 16, fontWeight: 'bold' },
  price: { fontSize: 14, color: '#ff4d4f', marginTop: 4 },
});
```

map和forEach的区别在于:map会返回一个新数组,forEach没有返回值。JSX中只能使用map,因为forEach不会产生可渲染的元素数组。同样的道理,filter也可以和map链式调用,先过滤再渲染。这种链式调用在处理条件列表时非常方便,比如只展示在售商品:`products.filter(p => p.status === 'active').map(...)`。

```
列表渲染数据流:

数据数组 [a, b, c, d]
    |
    v  map遍历,每个元素返回JSX
JSX元素数组 [<Item a/>, <Item b/>, <Item c/>, <Item d/>]
    |
    v  React协调器对比虚拟DOM
计算最小更新操作
    |
    v  提交到原生渲染管线
页面展示四个列表项
```

### 2.3.2 key属性作用与规范使用

key是React用于识别列表项的唯一标识。它的作用是在数据变化时,帮助React判断哪些元素发生了变化、新增或删除,从而最小化重渲染范围。

```jsx
// 正确:使用唯一id作为key
{products.map((item) => (
  <ProductCard key={item.id} product={item} />
))}

// 错误:使用数组索引作为key
{products.map((item, index) => (
  <ProductCard key={index} product={item} />
))}
```

使用index作为key在列表顺序变化时会导致渲染异常。比如在列表头部插入新元素时,所有元素的index都会变化,React会认为是所有元素都发生了变化,导致不必要的重渲染甚至状态错乱。这不仅仅是一个性能问题,更是一个正确性问题--用户看到的状态可能和实际数据不对应。

具体场景说明:假设你有一个可删除的列表,每项内部有一个输入框。用户在第二项的输入框中输入了文字,然后删除了第一项。此时如果用index作为key,原来的第三项变成了第二项,React会把它当成原来的第二项(因为key都是1),导致输入框中的文字错位。用户看到的效果就是:明明删除了第一项,但输入框的文字跑到另一行去了。这种问题在开发阶段可能不容易发现,但在用户使用时会被当作bug反馈。因此在实际项目中,key的选择规则是:有唯一id用唯一id,没有唯一id用组合字段(比如name加date拼接),实在不行才考虑用index。

> key的唯一性范围是兄弟节点之间。不同列表之间可以存在相同的key值,但同一列表中的key必须唯一。key不需要全局唯一,只需要在兄弟节点中唯一即可。

### 2.3.3 空数据与异常数据容错处理

实际开发中,接口返回的数据可能为空数组、null或undefined。不做容错处理会导致页面白屏或JS报错红屏。

```tsx
function SafeList({ products }: { products: Product[] | null }) {
  if (!products || products.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>暂无数据</Text>
      </View>
    );
  }

  return (
    <View>
      {products.map((item) => (
        <View key={item.id} style={styles.item}>
          <Text>{item.name || '未命名商品'}</Text>
          <Text>¥{(item.price ?? 0).toFixed(2)}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  emptyContainer: { padding: 40, alignItems: 'center' },
  emptyText: { fontSize: 14, color: '#999' },
  item: { padding: 12 },
});
```

容错处理的核心原则是:永远不要信任外部数据。字段可能为空、类型可能不对、数组可能为null、日期可能是非法值。在渲染前做好防御性判断,是一个成熟开发者的基本素养。怕浪猫在团队中推行了一条代码规范:所有从接口获取的数据,在渲染前必须经过空值检查,即使是必填字段也要做兜底处理。因为后端改了字段名或者返回null的情况在真实项目中并不少见,前端做好兜底,至少能保证页面不白屏,用户看到的是"暂无数据"而不是一片空白或红屏报错。

除了空值检查,还需要注意数据类型的问题。后端返回的数字字段,有时候会被序列化成字符串。比如价格字段后端返回的是"99.00"而不是99.00,如果你直接做toFixed()就会报错,因为字符串没有toFixed方法。安全的做法是在使用前做类型转换:`Number(item.price).toFixed(2)`。这类问题在前后端联调时非常常见,养成防御性编程的习惯能让你少走很多弯路。

> 空值合并运算符`??`和逻辑或`||`的区别:`||`会把所有falsy值(0、空字符串、false)都触发默认值,而`??`只对null和undefined生效。对于数字0这种合法值,应该用`??`。

### 2.3.4 数组对象数据格式化处理

后端返回的数据格式往往不能直接用于渲染,需要在前端做格式化处理。常见场景包括时间戳转日期、金额分转元、状态码转文字等。

```ts
interface RawOrder {
  id: number;
  create_time: number;
  amount: number;
  status: number;
}

const statusMap: Record<number, string> = {
  0: '待支付', 1: '已支付', 2: '已发货',
  3: '已完成', 4: '已取消',
};

function formatOrder(order: RawOrder) {
  return {
    id: order.id,
    date: new Date(order.create_time * 1000)
      .toLocaleDateString('zh-CN'),
    amount: `¥${(order.amount / 100).toFixed(2)}`,
    statusText: statusMap[order.status] ?? '未知状态',
  };
}
```

format函数定义好后，在渲染组件中调用：

```tsx
function OrderList({ orders }: { orders: RawOrder[] }) {
  const list = orders.map(formatOrder);
  return (
    <View>
      {list.map((item) => (
        <View key={item.id}>
          <Text>{item.date}</Text>
          <Text>{item.amount}</Text>
          <Text>{item.statusText}</Text>
        </View>
      ))}
    </View>
  );
}
```

> 数据格式化应该与渲染分离。一个format函数只做数据转换,一个渲染函数只做UI展示。职责单一,维护轻松,测试方便。当产品提出"金额展示改成保留一位小数"这种需求时,你只需要修改format函数,渲染逻辑完全不动,这就是分离的好处。

### 2.3.5 复杂列表嵌套渲染实战

实际业务中,列表项内部往往还嵌套着子列表。比如订单列表中每个订单包含多个商品。嵌套渲染需要注意key的唯一性和性能控制。

```tsx
interface OrderItem {
  id: number;
  orderNo: string;
  products: { id: number; name: string; qty: number }[];
}

function OrderCard({ order }: { order: OrderItem }) {
  return (
    <View style={styles.orderCard}>
      <Text>订单号:{order.orderNo}</Text>
      {order.products.map((prod) => (
        <View key={prod.id} style={styles.prodItem}>
          <Text>{prod.name}</Text>
          <Text>x{prod.qty}</Text>
        </View>
      ))}
    </View>
  );
}
```

OrderList组件负责遍历订单数组并渲染每个OrderCard：

```tsx
function OrderList({ orders }: { orders: OrderItem[] }) {
  return (
    <View>
      {orders.map((order) => (
        <OrderCard key={order.id} order={order} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  orderCard: { padding: 12, borderBottomWidth: 1 },
  prodItem: { flexDirection: 'row', justifyContent: 'space-between' },
});
```

嵌套列表的关键点:外层map的key用订单id,内层map的key用商品id,两者互不冲突。外层和内层的key处于不同的组件层级,React只在兄弟节点之间比较key,所以不同层级的key可以重复。但怕浪猫建议即使在不同的层级中,也尽量保持key的唯一性,这样在排查问题时更不容易混淆。

如果嵌套层级超过3层,建议使用FlatList或SectionList替代纯map渲染。纯map渲染的列表不会复用组件,所有列表项都会在内存中创建。当列表项数量超过一百时,内存占用和渲染时间会显著增加,导致页面加载缓慢甚至卡顿。FlatList采用了虚拟化列表技术,只渲染当前可见区域的列表项,不可见的项会被回收,从而保持内存占用稳定。第3章会详细讲解FlatList的用法和性能优化配置。对于嵌套列表的性能,还有一个常见问题:内层列表的map渲染会在外层每次重渲染时都执行一遍。如果外层组件因为其他状态变化而重渲染,内层列表即使数据没变也会重新计算。解决思路是在外层列表项组件上使用React.memo包裹,只有当props变化时才重渲染,避免不必要的计算。这也是为什么在嵌套列表中,把内层渲染提取为独立组件是一个好习惯--不仅为了可读性,更为了能够独立优化。

## 2.4 TypeScript类型约束实战

TypeScript是RN项目的标配。类型约束能在编译阶段发现潜在错误,大幅减少运行时bug。这一节从基础类型到实战应用,系统讲解TS在RN中的用法。

### 2.4.1 基础数据类型定义与校验

TS的基础类型包括string、number、boolean、数组、元组、枚举等。在RN开发中,最常用的类型定义方式如下:

```ts
// 基础类型
const appName: string = 'MyApp';
const version: number = 1.0;
const isReleased: boolean = false;

// 数组类型
const tags: string[] = ['hot', 'new', 'sale'];
const prices: number[] = [99, 199, 299];

// 联合类型
type Platform = 'ios' | 'android';
const currentPlatform: Platform = 'ios';

// 枚举
enum OrderStatus {
  Pending = 0,
  Paid = 1,
  Shipped = 2,
  Completed = 3,
}
const status: OrderStatus = OrderStatus.Paid;
```

联合类型特别适合定义有限的取值范围,比如平台类型、状态码等。枚举则更适合需要语义化的场景,代码可读性更好。

> TS类型的本质是契约。定义类型就是定义数据的形状,编译器帮你检查每一处使用是否符合契约。这种"编译时检查"的能力,是纯JS无法提供的。在JS中,一个函数期望接收name字符串,但调用方传入了一个数字,代码不会报错,直到运行时才可能出现意外行为。而TS在编译阶段就能拦住这种错误,把运行时风险提前暴露。

### 2.4.2 接口Interface定义业务数据

Interface是TS中定义对象类型的核心工具。它描述了对象应该有哪些属性、每个属性是什么类型。

```ts
interface User {
  id: number;
  name: string;
  avatar: string;
  phone?: string;           // 可选属性
  readonly createdAt: string; // 只读属性
}

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

type UserResponse = ApiResponse<User>;
// 等价于 { code: number; message: string; data: User }
```

可选属性用`?`标记,表示该属性可以不存在。只读属性用readonly标记,赋值后不可修改。泛型(Generics)让接口可以复用,ApiResponse可以适配任何数据类型。泛型在RN开发中非常实用,比如列表组件可以接收任意类型的数组,只需要定义一个泛型接口就能复用。

在定义接口名称时,建议遵循"名词加描述"的命名方式,比如UserOrder、ProductDetail、PaymentResult,避免使用过于宽泛的名称如Data、Info。接口定义不仅是类型约束,也是业务文档--通过阅读接口定义就能理解数据结构包含哪些信息。

### 2.4.3 组件Props类型约束规范

RN组件的Props类型定义是TS在RN中最直接的应用场景。每个组件都应该明确声明接收哪些Props及其类型。

```tsx
import { View, Text, StyleProp, ViewStyle } from 'react-native';

interface CardProps {
  title: string;
  subtitle?: string;
  backgroundColor?: string;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
}

function Card({ title, subtitle, backgroundColor = '#fff',
  style, onPress }: CardProps) {
  return (
    <View style={[{ backgroundColor, padding: 16 }, style]}>
      <Text style={{ fontSize: 16, fontWeight: 'bold' }}>
        {title}
      </Text>
      {subtitle && <Text>{subtitle}</Text>}
    </View>
  );
}
```

StyleProp<ViewStyle>是RN官方提供的样式类型,它允许传入样式对象、样式数组或undefined。使用这个类型可以确保style属性的类型安全。如果需要传递Text样式,则使用StyleProp<TextStyle>。

> 组件Props的类型定义应该详细到每个字段。不要用any,any等于放弃类型检查,用TS还用any不如直接写JS。any类型会跳过所有类型检查,使用any的变量可以赋值给任何类型的变量,也可以从任何类型赋值过来,这就失去了TS的意义。在团队协作中,一个人写的any会让所有使用这个组件的人都失去类型提示,影响范围远超想象。

### 2.4.4 函数参数与返回值类型限定

为函数添加类型签名,可以约束函数的输入和输出,防止调用方传入错误类型的参数。

```ts
// 简单函数
function formatPrice(cents: number): string {
  return `¥${(cents / 100).toFixed(2)}`;
}

// 异步函数
async function fetchUser(id: number): Promise<User> {
  const res = await api.get(`/users/${id}`);
  return res.data;
}

// 回调函数类型
type AsyncCallback<T> = (error: Error | null, data?: T) => void;

function loadData<T>(callback: AsyncCallback<T>) {
  fetchData<T>()
    .then((data) => callback(null, data))
    .catch((err) => callback(err));
}
```

异步函数的返回值类型是Promise<T>,其中T是实际的数据类型。在调用时使用await可以获取到T类型的值,不使用await则得到Promise<T>。类型系统会在编译时检查你是否正确处理了异步返回值,比如忘记写await,TS会提示你操作的是Promise而不是实际数据。

在实际RN开发中,函数类型签名最常见的应用场景是工具函数和自定义Hooks。工具函数需要明确的输入输出类型约束,确保调用方传参正确。自定义Hooks的返回值通常是元组类型(比如useState返回[值, 设置函数]),用TS可以精确约束每个位置的类型。这些类型信息不仅帮助编译器检查错误,也是最好的函数文档--其他开发者看到函数签名就知道该怎么用,不需要翻看实现代码。

### 2.4.5 TS类型报错快速排查方案

TS报错信息有时比较晦涩,掌握排查方法能大幅提升开发效率。

常见报错一:类型不匹配

```
error TS2322: Type 'string' is not assignable to type 'number'.
```

这说明你把一个string类型的值赋给了期望number类型的变量。检查赋值语句两侧的类型是否一致。

常见报错二:属性不存在

```
error TS2339: Property 'name' does not exist on type 'User'.
```

这说明你访问了一个类型定义中不存在的属性。检查Interface定义是否缺少该属性,或者变量类型是否正确。

常见报错三:可能为undefined

```
error TS2532: Object is possibly 'undefined'.
```

这说明你访问了一个可选属性的子属性,但没做空值判断。解决方案是使用可选链:

```ts
// 报错
const name = user.profile.name;

// 修复方式一:可选链
const name = user.profile?.name;

// 修复方式二:判空
if (user.profile) {
  const name = user.profile.name;
}
```

> TS报错不要急着用as any或@ts-ignore跳过。每个类型错误都可能是真实的bug信号,跳过它等于埋雷。怕浪猫在code review中看到any就直接打回。

## 2.5 RN全场景调试工具与技巧

调试是开发中占比最大的工作之一。RN提供了丰富的调试工具链,从开发者菜单到Chrome远程调试,从组件审查到网络抓包,覆盖了开发全场景。

### 2.5.1 开发者菜单功能详解与启用

开发者菜单是RN调试的入口。在模拟器中通过快捷键打开:iOS使用`Cmd + D`,Android使用`Cmd + M`(Mac)或`Ctrl + M`(Windows)。真机上可以通过摇一摇设备触发。

```
开发者菜单核心功能:

[Reload]              重新加载JS Bundle
[Debug JS Remotely]   开启Chrome远程调试
[Change Bundle Location] 切换Metro服务地址
[Show Perf Monitor]   性能监控面板
[Element Inspector]   UI元素审查器
[Disable Fast Refresh] 关闭热更新
```

 Reload是最常用的功能,当代码修改后没有自动刷新时,手动Reload可以重新加载整个JS Bundle。Fast Refresh(快速刷新)默认开启,修改代码后会自动热更新当前组件,保留组件状态。如果你修改的是一个配置文件或者新增了依赖包,Fast Refresh可能不会生效,这时候需要手动Reload。在有些情况下连Reload都不够,比如修改了原生代码或者添加了新的原生依赖,这时候需要重新构建整个应用:`npx react-native run-android`或`npx react-native run-ios`。

Element Inspector类似于Chrome的Elements面板,可以查看当前页面的组件树和样式信息。点击屏幕上的元素即可选中并查看其布局参数,包括宽高、边距、内边距等。它还能显示元素的实际渲染尺寸,这对于排查Flex布局问题非常有用--当你说不清一个元素为什么占了那么多空间时,打开Inspector看一眼就明白了。

> 熟记开发者菜单的快捷键能大幅提升调试效率。iOS的Cmd+D和Android的Cmd+M是每天要用几十次的操作。

### 2.5.2 Chrome远程断点调试实战

开启Chrome远程调试后,可以在Chrome DevTools中设置断点、查看变量、执行表达式。

操作步骤:

第一步,在开发者菜单中选择"Debug JS Remotely"。第二步,Chrome自动打开`http://localhost:8081/debugger-ui`。第三步,打开Chrome DevTools(Cmd+Option+I)。第四步,在Sources面板中找到对应文件,设置断点。

```tsx
function UserDetail({ userId }: { userId: number }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // 在这行设置断点,检查userId的值
    fetchUser(userId).then(setUser);
  }, [userId]);

  if (!user) return <Text>加载中...</Text>;
  return <Text>{user.name}</Text>;
}
```

断点调试时,可以在Scope面板查看当前作用域变量,在Console中执行任意表达式,在Call Stack查看函数调用链。条件断点可以设置只在满足特定条件时暂停,非常适合处理循环中的特定数据。比如在遍历列表时只想看id为5的元素,可以设置条件断点`item.id === 5`,这样只有遍历到id为5的元素时才会暂停。Log Points也是一种实用的断点类型,它不会暂停执行,只是在控制台输出一条日志,适合在不影响程序运行的情况下观察变量值的变化。

> 注意:开启Chrome远程调试后,JS代码运行在Chrome的V8引擎中而非设备的JavaScriptCore引擎中。这可能导致某些行为与真机不一致,特别是与日期、正则相关的操作。调试完成后记得关闭远程调试。

```
Chrome远程调试架构:

RN设备/模拟器
    |
    v (WebSocket连接)
Chrome浏览器
    |
    v
V8引擎执行JS + DevTools断点调试
```

### 2.5.3 React DevTools组件状态调试

React DevTools是专门用于调试React组件树的工具,可以查看组件层级、Props、State和Hooks状态。它与Chrome DevTools的区别在于:Chrome DevTools调试的是JS执行逻辑,而React DevTools调试的是React组件结构。两者互补使用,一个查逻辑一个查状态,基本能覆盖大部分调试场景。

安装方式:
```bash
npx react-devtools
```

如果你的项目中使用的是React 18及以上版本,React DevTools会自动识别并连接。运行上述命令后会弹出一个独立窗口,等待RN应用连接。确保你的RN应用正在运行,DevTools会自动检测到并通过WebSocket建立连接。连接成功后,DevTools窗口会显示当前RN应用的组件树,点击任意组件即可查看其Props、State和Hooks信息。

```
React DevTools核心功能:

[组件树]    查看组件嵌套层级关系
[Props]     查看组件接收的属性值
[State]     查看组件内部状态
[Hooks]     查看useState/useEffect等Hook值
[Profiler]  录制渲染性能分析
```

在实际开发中,React DevTools最常用于排查"为什么数据没有更新"的问题。通过查看组件的State和Props,可以快速定位是数据传递的问题还是状态更新的问题。比如你在useEffect中调用了setState但页面没更新,打开DevTools看看组件的state到底变没变,就能判断是状态没更新还是渲染出了问题。

React DevTools的Profiler功能也是一个强大的性能分析工具。点击录制按钮后,在页面上进行操作,停止录制后可以看到每个组件的渲染次数和渲染耗时。如果一个组件在一次操作中被渲染了多次,说明可能存在不必要的重渲染,需要用React.memo或useMemo来优化。虽然性能优化会在第13章详细讲解,但提前了解Profiler的用法,在日常开发中就能养成关注渲染性能的习惯。

### 2.5.4 真机日志与网络抓包调试

真机调试时,开发者菜单可能不太方便。Android可以使用adb logcat查看日志,iOS可以使用Xcode Console。

Android日志查看:

```bash
# 查看所有日志
adb logcat

# 过滤RN相关日志
adb logcat | grep ReactNative

# 过滤JS日志
adb logcat | grep "ReactNativeJS"
```

iOS日志查看:在Xcode中打开Window菜单,选择Devices and Simulators,选择已连接的设备,点击"Open Console"即可查看设备日志。也可以使用Console.app查看所有系统日志。

对于网络请求调试,可以使用Flipper工具。Flipper是Meta开源的移动端调试平台,内置了网络抓包、布局检查、数据库查看等功能。它是RN开发者的瑞士军刀,一个工具就能替代多个独立的调试工具。

除了Flipper,还有一些经典的网络抓包方案。比如Charles和Proxyman这类HTTP代理工具,可以在电脑上设置代理,手机连接同一个WiFi后配置代理地址,就能在电脑上查看手机所有的网络请求。这种方式不仅能抓RN的请求,还能抓原生模块发出的请求,比Flipper的覆盖范围更广。另外,使用抓包代理工具还能修改请求响应数据,这在模拟后端返回特定数据测试前端容错逻辑时非常有用。比如你想测试一个接口返回500错误码时前端的处理逻辑,可以在Charles中设置Map重写规则,将正常响应改为500,无需后端配合就能验证前端逻辑。

```bash
# Flipper已内置在RN 0.62及以上版本中
# 安卓自动连接,iOS需要pod install
cd ios && pod install
```

Flipper的网络面板可以查看所有HTTP(HyperText Transfer Protocol,超文本传输协议)请求的URL、请求头、请求体、响应状态码和响应体,功能类似于Chrome的Network面板。你可以按请求方法筛选,按响应时间排序,甚至可以重放某个请求。此外Flipper还提供了AsyncStorage查看器、SharedPreferences查看器、布局检查器、React Profiler集成等实用工具,基本上一个Flipper就能覆盖大部分调试需求。

对于iOS真机调试,还有一个额外的问题需要注意:iOS 14及以上版本默认不允许本地HTTP连接。如果你在真机上连接Metro服务器时遇到网络错误,需要在Info.plist中配置NSAppTransportPolicy允许NSAllowsLocalNetworking。这个配置在创建项目时通常会自动添加,但如果你手动修改过原生配置,可能会遗漏。另外,iOS真机调试还需要在Xcode中配置好开发者证书和设备的信任关系,否则安装时会报错。

> 真机调试时,最怕的就是"只看到红屏不知道为什么"。学会使用日志工具,等于给自己装了一双透视眼。怕浪猫建议在真机上测试时始终开着日志面板。

```
真机调试工具选择指南:

场景                    推荐工具
查看JS报错              adb logcat / Xcode Console
查看网络请求            Flipper网络面板
查看组件层级            React DevTools
查看组件样式            Element Inspector
查看本地存储            Flipper AsyncStorage面板
性能分析                Perf Monitor + React Profiler
```

### 2.5.5 线上异常日志监控基础方案

开发阶段的调试工具在线上环境中不可用。线上异常监控需要依赖日志收集SDK(Software Development Kit,软件开发工具包)。主流方案有Sentry、Bugsnag、Firebase Crashlytics等。

以Sentry为例,基础接入方式:

```ts
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: 'https://your-dsn@sentry.io/project-id',
  environment: __DEV__ ? 'development' : 'production',
  tracesSampleRate: 1.0,
});

// 手动上报错误
try {
  await riskyOperation();
} catch (error) {
  Sentry.captureException(error);
}

// 上报业务上下文
Sentry.setTag('userId', user.id);
Sentry.setExtra('lastAction', 'checkout');
```

Sentry会自动捕获未处理的JS异常和原生崩溃,将错误堆栈、设备信息、用户操作路径上报到服务端。在Sentry后台可以查看每个错误的详细信息和发生频率。设置environment字段可以区分开发环境和生产环境的错误,便于过滤。设置release标注版本号,这样在Sentry后台可以按版本过滤错误,快速定位是哪个版本引入的问题。

线上异常监控的核心价值在于:你能在用户投诉之前发现并修复问题。一个完善的监控体系应该包含JS异常、原生崩溃、接口异常和性能数据四个维度。JS异常捕获Sentry可以自动完成,原生崩溃需要配置对应平台的崩溃收集SDK。接口异常通常需要在前端请求拦截器中手动上报,包括非200状态码的响应、网络超时、JSON(JavaScript Object Notation,JavaScript对象表示法)解析失败等情况。性能数据则包括页面加载时间、接口响应时间、JS线程帧率等指标。

在实际接入中,有几个最佳实践值得注意。第一,合理设置采样率,tracesSampleRate设为1.0意味着全量采样,在用户量大时会产生大量数据,建议生产环境设为0.1到0.3之间。第二,在release标注版本号,这样在Sentry后台可以按版本过滤错误,快速定位是哪个版本引入的问题。第三,在关键业务节点设置breadcrumb(面包屑),记录用户的操作路径,比如"用户进入了支付页面"、"用户点击了提交按钮",这些上下文信息对于排查"用户操作到一半出错了"的问题至关重要。

```
线上异常监控数据流:

用户设备发生异常
    |
    v  SDK自动捕获
Sentry上报(含堆栈、设备信息、用户路径)
    |
    v  服务端聚合分析
开发者邮件/Slack告警
    |
    v  排查修复
发布补丁版本
```

> 线上监控不是可选项,而是必选项。当你不知道用户遇到了什么问题时,就无从优化。Sentry的免费额度对于小项目来说完全够用,没有理由不接入。

## 2.6 工程化规范与本章实战总结

### 2.6.1 路径别名配置简化项目引用

随着项目规模增长,相对路径会变得难以维护。`import { fetch } from '../../../../../utils/request'`这样的写法既不美观也容易出错。路径别名可以解决这个问题。

配置路径别名需要两个步骤:

第一步,在tsconfig.json中配置paths:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@utils/*": ["src/utils/*"],
      "@api/*": ["src/api/*"]
    }
  }
}
```

第二步,在babel.config.js中配置模块解析:

```js
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./'],
        alias: {
          '@': './src',
          '@components': './src/components',
          '@utils': './src/utils',
        },
      },
    ],
  ],
};
```

配置完成后,引入方式变得简洁明了。对比一下配置前后的差异:

配置前:
```ts
import { fetch } from '../../../../../utils/request';
import { Button } from '../../../../../components/Button';
import { userApi } from '../../../api/user';
```

配置后:
```ts
import { fetch } from '@/utils/request';
import { Button } from '@components/Button';
import { userApi } from '@api/user';
```

不仅代码更短,而且当目录结构发生变化时(比如components文件夹从src/components移动到src/shared/components),只需要修改tsconfig.json和babel.config.js中的路径配置,所有import语句都不需要改动。这种解耦带来的维护便利性在大型项目中价值尤为突出。

```ts
import { fetch } from '@/utils/request';
import { Button } from '@components/Button';
import { userApi } from '@api/user';
```

> 路径别名不仅让代码更整洁,还能在重构目录结构时只需修改配置而不用改动每个文件的import路径。这在不使用路径别名的项目中是一场灾难级的重构。

### 2.6.2 全局常量与工具类统一管理

企业项目中,常量和工具类应该集中管理,避免散落在各个文件中造成维护困难。推荐的目录结构:

```
src/
├── constants/
│   ├── config.ts      # 全局配置常量
│   ├── api.ts         # 接口地址常量
│   └── enum.ts        # 枚举常量
├── utils/
│   ├── request.ts     # 网络请求工具
│   ├── storage.ts     # 本地存储工具
│   ├── format.ts      # 格式化工具
│   └── index.ts       # 统一导出
```

常量定义示例:

```ts
// constants/config.ts
export const APP_CONFIG = {
  pageSize: 20,
  maxRetry: 3,
  timeout: 15000,
} as const;

export const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
} as const;
```

`as const`关键字让TS把对象推断为字面量类型,而不是宽泛的string类型。这样`COLORS.primary`的类型就是`'#1890ff'`而不是`string`,在需要精确类型匹配的场景下非常有用。

工具类定义示例:

```ts
// utils/format.ts
export const formatPrice = (cents: number): string =>
  `¥${(cents / 100).toFixed(2)}`;

export const formatDate = (timestamp: number): string =>
  new Date(timestamp).toLocaleDateString('zh-CN');

export const truncate = (text: string, maxLen: number): string =>
  text.length > maxLen ? `${text.slice(0, maxLen)}...` : text;
```

统一导出:

```ts
// utils/index.ts
export * from './request';
export * from './storage';
export * from './format';
```

这样在其他文件中只需要一行import:

```ts
import { formatPrice, formatDate, request } from '@/utils';
```

### 2.6.3 代码格式化与ESLint规范

ESLint(ECMAScript Lint,ECMAScript代码检查工具)是代码质量检查工具,Prettier是代码格式化工具。两者配合使用可以确保团队代码风格统一。

ESLint配置示例(.eslintrc.js):

```js
module.exports = {
  root: true,
  extends: '@react-native',
  rules: {
    'no-unused-vars': 'warn',
    'no-console': 'warn',
    'react-hooks/exhaustive-deps': 'error',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
};
```

Prettier配置示例(.prettierrc):

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "tabWidth": 2,
  "semi": true,
  "printWidth": 80
}
```

在VS Code中安装ESLint和Prettier插件后,配置保存自动格式化。这样每次保存文件时,Prettier会自动格式化代码风格,ESLint会自动修复可修复的错误。比如你写了`const a=1`,保存后自动变成`const a = 1`,不需要手动调整空格。这种自动化工具链能帮你省下大量调整格式的时间,让注意力集中在业务逻辑上。

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

> 代码规范不是束缚,而是团队协作的基础。当所有人的代码风格一致时,code review的焦点才能从格式转向逻辑。怕浪猫在团队中推行ESLint加Prettier后,代码review效率提升了至少30%。以前review时要花大量时间指出格式问题,现在这些由工具自动处理,review时只需要关注业务逻辑和代码架构。

以下是ESLint核心规则的收藏清单:

| 规则 | 级别 | 作用 |
|------|------|------|
| no-unused-vars | warn | 检测未使用变量 |
| no-console | warn | 检测console语句 |
| react-hooks/exhaustive-deps | error | 检测Hooks依赖完整性 |
| no-explicit-any | warn | 检测any类型使用 |
| react/jsx-key | error | 检测列表缺少key |
| no-debugger | error | 检测debugger语句 |

### 2.6.4 本章重难点知识归纳梳理

本章内容较多,怕浪猫把核心知识点做一个归纳梳理:

**配置文件部分:** package.json管依赖和脚本,app.json管应用全局参数,metro.config.js管打包行为,tsconfig.json管类型系统。多环境配置推荐使用react-native-config。Metro的打包流程是解析、转换、序列化三步,缓存机制让热更新达到毫秒级。

**JSX语法部分:** JSX是createElement的语法糖。RN没有DOM和BOM,不能用div、span等HTML标签,不能用document和window对象。条件渲染用三元表达式、逻辑与、函数提取三种方案。style接收对象不接收字符串。JSX注释用花括号包裹。

**列表渲染部分:** map是列表渲染的核心方法,forEach不能用于渲染。key必须用唯一id不能用index。空数据要兜底处理,数据格式化与渲染分离。嵌套列表注意key唯一性,超过3层用FlatList。

**TypeScript部分:** Interface定义对象类型,Props类型约束组件入参,函数签名限定参数和返回值。strict模式建议开启。TS报错不要用any跳过,要理解每个报错的原因。可选链`?.`和空值合并`??`是处理可能为null/undefined的利器。

**调试技巧部分:** 开发者菜单是调试入口,Cmd+D(iOS)和Cmd+M(Android)。Chrome远程调试可以设断点。React DevTools查看组件树和状态。Flipper做网络抓包和存储查看。线上监控用Sentry自动收集异常。

> 学习RN调试的 fastest path:先用开发者菜单Reload和Inspector熟悉基本操作,再学Chrome断点调试掌握逻辑排查,最后接入React DevTools和Flipper实现全方位调试。三级递进,不要跳级。

### 2.6.5 综合上机实战与课后习题

学完本章后,建议完成以下实战练习巩固知识:

实战一:创建一个新的RN项目,完成路径别名配置(tsconfig.json加babel.config.js),使用@/components、@/utils等别名引入文件。

实战二:定义一个Product接口和Order接口,编写一个OrderList组件,接收订单数组并渲染。要求:使用map遍历、key用订单id、处理空数据、格式化金额和时间。

实战三:配置ESLint和Prettier,开启保存自动格式化,确保团队成员代码风格统一。

实战四:使用Chrome远程调试在代码中设置断点,观察useEffect的执行顺序。使用React DevTools查看组件的props和state。

课后思考题:

1. 为什么JSX中不能使用if语句但可以使用三元表达式?请从表达式和语句的区别角度解释。

2. 如果一个列表的数据频繁更新(如股票行情),使用map渲染会有什么性能问题?应该如何优化?

3. strict模式下的strictNullChecks具体检查什么?举例说明它如何帮你避免运行时错误。

4. Chrome远程调试时JS运行在V8引擎中,这和真机上运行在JavaScriptCore引擎中有什么实际差异?

5. react-native-config和react-native-dotenv都是多环境配置方案,它们在原理上有什么区别?

> 实践是检验学习成果的唯一标准。看懂不等于会写,会写不等于写对。每个练习都动手做一遍,遇到问题再回头看对应章节。

## 本章总结

这一章我们从项目配置到JSX语法,从列表渲染到类型约束,从调试工具到工程化规范,把RN开发的基础知识体系完整地走了一遍。这些内容看似基础,但恰恰是日常开发中使用频率最高的部分。

配置文件决定了项目怎么跑,JSX决定了页面怎么写,TypeScript决定了代码怎么约束,调试工具决定了问题怎么查。掌握好这些基础,后续学习组件化、路由导航、状态管理时会事半功倍。

> 基础不牢,地动山摇。怕浪猫见过太多跳过基础直接写业务逻辑的开发者,最终都回头来补课。与其反复踩坑,不如一步到位把基础打牢。

如果你觉得这篇文章对你有帮助,别忘了收藏。后面章节会逐步深入组件开发、路由导航、网络请求、状态管理等核心主题,每一章都值得收藏反复看,不是看一遍就能吃透的。随着项目经验的积累,回头再看这些基础内容,你会有新的理解和感悟。

有什么疑问或者不同的做法,欢迎在评论区交流,怕浪猫会逐一回复。

下一章预告:第3章将详解RN核心组件、Flex布局与屏幕适配。我们会深入讲解View、Text、Image等基础组件的特性与用法,吃透Flex弹性布局的主轴侧轴原理,掌握多机型屏幕适配方案,搭建你的第一个完整RN页面。布局是RN开发的视觉根基,不容错过。

系列进度 2/16

怕浪猫说：RN的入门不难，难在把基础打扎实。配置文件、基础语法、类型约束、调试工具，这四块内容贯穿整个开发生命周期，今天多花一小时学透，明天少花一天调bug。坚持下去，16章之后你会感谢现在努力的自己。

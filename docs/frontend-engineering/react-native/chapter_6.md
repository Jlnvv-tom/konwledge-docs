---
sidebar_position: 6
---

# 第6章 RN原生设备API与系统能力开发

> 90%的RN开发者第一次崩溃，不是因为写不出UI，而是调个相机权限就报了8个红屏。

做过RN（React Native）开发的人都经历过这种场景：代码在模拟器上跑得好好的，一到真机就各种离谱报错。相机权限没加，闪退；存储权限没动态申请，写不进文件；状态栏颜色改了iOS生效Android没反应；断网了页面白屏用户直接卸载。这些问题的根源不是RN本身有缺陷，而是开发者没有系统掌握原生设备API（Application Programming Interface）的调用规范和系统能力的适配策略。

原生设备API是连接JS（JavaScript）世界与原生系统的桥梁。从本地存储到状态栏控制，从弹窗提示到设备信息获取，从网络监听到弱网容错，每一项能力背后都有一套完整的机制和踩坑要点。用得好，应用体验丝滑流畅；用不好，就是一台行走的Bug制造机。

很多初学者有一个误解：觉得RN既然是跨端框架，那原生能力应该都封装好了，直接调就行。这个想法对了一半。RN确实封装了大量原生能力，但封装的粒度和双端一致性远不如预期。同样是获取屏幕高度，iOS和Android返回的值含义不同；同样是请求相机权限，两端的流程和回调机制完全不同；同样是存储一个字符串，底层的实现引擎也不一样。如果不了解这些差异，写出来的代码在模拟器上能跑，到了真机上就是定时炸弹。

更复杂的是，当你引入第三方SDK（Software Development Kit）时，比如高德地图、微信支付、极光推送，这些SDK都有自己的原生模块，需要手动配置原生工程的依赖关系。iOS端要改Podfile和Info.plist，Android端要改build.gradle和AndroidManifest.xml。配置稍有遗漏，编译就报错，而且报错信息往往晦涩难懂，需要一定的原生开发经验才能定位问题。这也是为什么很多前端开发者在接触RN原生模块时感到挫败的原因：不是JS写不好，而是原生工程不熟。

我是怕浪猫，一个在原生API踩坑现场反复横跳的RN老兵。从最早的Bridge通信到现在的JSI新架构，从手动编写Native Module到使用各种社区库，我经历了RN原生能力开发的各种坑和演进。本章带你从零掌握RN原生设备API的开发规范、双端适配策略和容错设计，彻底告别"模拟器王者、真机青铜"的尴尬局面。

## 6.1 原生API开发规范与权限管理

### 6.1.1 原生模块与JS模块核心差异

RN的模块体系分为两层：JS模块和原生模块。理解它们的差异是使用原生API的前提，也是后续所有章节的认知基础。

JS模块运行在Hermes引擎中，包括你写的组件代码、状态管理逻辑、工具函数等。它们的调用是同步的，执行速度受JS引擎性能制约。你在组件中写的一个useState、一个map循环、一个条件判断，全部都在JS线程中同步执行。这部分跟Web前端的开发体验几乎一致，会React的开发者能无缝迁移。

而原生模块运行在各自的平台运行时中。Android端跑在JVM（Java Virtual Machine）上，使用Java或Kotlin编写；iOS端跑在Objective-C runtime上，使用Objective-C或Swift编写。这些模块通过Bridge或JSI（JavaScript Interface）与JS层通信。Bridge是RN传统的通信机制，通过异步消息队列在JS和原生之间传递数据；JSI是新架构下的通信机制，允许JS直接持有原生对象的引用，实现同步调用。

```
JS层（Hermes引擎）
  |  组件逻辑、状态管理、业务代码
  |
  |  Bridge（异步序列化） / JSI（同步引用）
  v
原生模块层
  ├── Android: Java/Kotlin Native Modules
  │    └── 系统服务: Camera / Storage / Network / Sensor
  ├── iOS: Objective-C/Swift Native Modules
  │    └── 系统框架: AVFoundation / CoreData / Reachability
  └── 第三方原生SDK: 微信支付 / 高德地图 / 极光推送
```

核心差异体现在三个方面。

第一是执行模型不同。JS模块同步执行，你调用一个函数立刻得到返回值。原生模块异步执行，调用原生API返回的总是Promise或通过回调函数交付结果。这意味着你不能在render函数中直接调用原生API并使用返回值，必须在useEffect或事件处理函数中异步调用，然后通过state更新触发重新渲染。

第二是线程模型不同。JS模块跑在JS线程，原生模块跑在各自的原生线程。跨线程通信需要序列化和反序列化，这个过程有性能开销。在Bridge架构下，所有数据都要经过JSON序列化才能跨线程传递，大量数据传输会成为性能瓶颈。JSI架构改善了这个问题，但仍然需要注意不要在JS和原生之间频繁传递大对象。

第三是生命周期不同。JS模块随组件挂载卸载，React的GC（Garbage Collector）会自动回收不再使用的对象。原生模块由系统管理生命周期，它的创建和销毁不受JS层控制。如果你在组件中订阅了原生事件监听器，组件卸载时必须手动取消订阅，否则监听器会一直存在于原生层，造成内存泄漏。

```tsx
// JS模块 - 同步调用，立即得到结果
const [count, setCount] = useState(0);
const doubled = count * 2; // 立即得到结果

// 原生模块 - 异步调用，需要等待
async function loadData() {
  const result = await AsyncStorage.getItem('key'); // 异步等待
  setCount(result ? parseInt(result) : 0);
}
```

> 怕浪猫踩坑记录：曾经在组件卸载后还留着原生事件监听器没清理，导致内存泄漏，页面切换十几次后OOM（Out of Memory）崩溃。原生模块不是JS，它不会自动被GC回收。从那以后，怕浪猫在每个useEffect里都养成了先写cleanup函数再写业务逻辑的习惯。

### 6.1.2 原生API异步调用执行机制

原生API的异步调用遵循一个标准的执行管道。理解这个管道，才能写出正确且高效的调用代码。

在传统Bridge架构下，一次原生API调用的完整路径如下：JS层发起调用，参数被序列化为JSON字符串，通过Bridge队列发送到原生层。原生层在各自线程上执行实际操作，拿到结果后再次序列化为JSON，通过Bridge队列回传到JS层。JS层反序列化后，通过Promise.resolve或回调函数将结果交给业务代码。

```
JS调用原生API完整路径（Bridge架构）：

  JS层发起调用
    │
    ▼
  参数序列化（JSON.stringify）
    │  开销：与数据大小成正比
    ▼
  Bridge队列传输（异步）
    │  开销：队列调度延迟，约2-5ms
    ▼
  原生线程执行实际操作
    │  开销：取决于操作类型
    ▼
  结果序列化（JSON.stringify）
    │  开销：与结果大小成正比
    ▼
  Bridge队列回传（异步）
    │  开销：队列调度延迟
    ▼
  JS层反序列化，触发Promise/回调
```

在JSI新架构下，这个路径被大幅简化。JSI允许JS引擎直接持有C++对象的引用，调用原生方法时不需要经过Bridge队列，参数也不需要序列化。这使得原生API可以像普通JS函数一样被同步调用，性能提升数倍。但需要注意，目前大部分社区库仍然是基于旧Bridge的异步模式，只有少数库已经迁移到JSI。

实际开发中，你会遇到两种调用方式。

```tsx
// 方式一：Promise（推荐）
async function saveData() {
  try {
    await AsyncStorage.setItem('key', 'value');
    console.log('保存成功');
  } catch (error) {
    console.error('保存失败:', error);
  }
}

// 方式二：回调函数（旧API常见）
CameraRoll.getPhotos({ first: 20 }, (data) => {
  console.log('照片获取成功', data.edges);
}, (error) => {
  console.error('获取失败:', error);
});
```

Promise方式更符合现代JS开发习惯，且能配合async/await使用，代码可读性更好。它还能统一错误处理逻辑，通过try-catch捕获整个异步链中的异常。怕浪猫建议在新项目中统一使用Promise风格。对于只提供回调接口的旧API，可以通过Promise包装来统一调用方式。这种统一化处理的价值在于：团队中所有人写出的异步代码风格一致，代码审查时不需要判断某个函数是Promise还是回调，直接看try-catch就行。

在旧Bridge架构下，每次原生调用都会产生一次Bridge通信，这意味着高频调用原生API会成为性能瓶颈。比如在动画过程中每帧调用原生API获取传感器数据，Bridge队列会积压大量消息，导致动画卡顿。新架构JSI解决了这个问题，但目前大部分社区库仍然是基于旧Bridge的异步模式，迁移需要时间。

```tsx
// 将回调式API包装为Promise
function promisify<T>(
  fn: (success: (data: T) => void, error: (e: any) => void) => void
): Promise<T> {
  return new Promise((resolve, reject) => {
    fn(resolve, reject);
  });
}

// 使用示例
const photos = await promisify((resolve, reject) => {
  CameraRoll.getPhotos({ first: 20 }, resolve, reject);
});
```

### 6.1.3 双端兼容性适配处理原则

同一个原生API在Android和iOS上的行为可能完全不同。这是RN开发中最常见的坑，也是区分初级和高级开发者的关键能力。适配处理需要遵循三条核心原则。

第一，优先使用Platform模块做条件分支。不要用try-catch来探测API是否存在，这种做法性能差且不可靠。try-catch会打断JS引擎的优化路径，而且在某些情况下原生模块存在但不报错，只是返回错误值，try-catch根本捕获不到。

```tsx
import { Platform, NativeModules } from 'react-native';

// 正确：平台条件分支，清晰可靠
const statusBarHeight = Platform.select({
  ios: NativeModules.StatusBarManager.height,
  android: 0, // Android需要额外处理
});

// 错误：try-catch探测，性能差且不可靠
let height;
try {
  height = NativeModules.SomeModule.someValue;
} catch (e) {
  height = 0;
}
```

第二，使用Platform.select统一样式和配置。它能让你在一个表达式中处理多端差异，代码更简洁，可读性更好。相比写一堆if-else，Platform.select让平台差异一目了然，代码审查时同事能立刻识别出哪些地方有双端逻辑。

```tsx
const styles = StyleSheet.create({
  header: {
    height: Platform.select({ ios: 44, android: 56 }),
    paddingTop: Platform.select({ ios: 0, android: 24 }),
    backgroundColor: '#FFFFFF',
  },
});
```

第三，封装统一的适配层。对于复杂的双端差异，不要在业务代码里到处写Platform判断，而应该封装成独立的工具函数或组件。业务代码只调用统一接口，不关心平台差异。这样做的好处是，当某个平台的实现需要修改时，只需要改一处，而不是在整个项目中搜索替换。

```tsx
// utils/platform.ts - 统一平台适配层
import { Platform, NativeModules, StatusBar } from 'react-native';

export const isIOS = Platform.OS === 'ios';
export const isAndroid = Platform.OS === 'android';

// 获取状态栏高度（双端适配）
export const getStatusBarHeight = () => {
  if (isIOS) {
    return NativeModules.StatusBarManager?.height ?? 20;
  }
  return StatusBar.currentHeight ?? 24;
};

// 获取安全区域底部高度
export const getBottomSpacing = () => {
  if (isIOS) {
    // iPhone X以上系列有Home Indicator
    return Platform.select({
      ios: NativeModules.DeviceInfo?.isIPhoneX_deprecated ? 34 : 0,
      android: 0,
    });
  }
  return 0;
};
```

> 双端适配的本质不是"让代码在两端都能跑"，而是"让两端都能正确运行"。一个Platform.select看似简单，但它能在代码审查时让同事一眼看出哪些地方有平台差异，这比埋了一堆if-else的"暗坑"要专业得多。怕浪猫在团队中推行了一条规则：所有包含Platform判断的代码必须经过双端真机测试，模拟器测试不算数。因为很多平台差异只在真机上才暴露。

### 6.1.4 设备权限动态申请规范

Android 6.0（API 23）以上和iOS都要求运行时动态申请敏感权限。这意味着即使在配置文件中声明了权限，实际使用时仍然需要弹窗让用户确认。RN中通常使用`react-native-permissions`库来统一处理双端权限申请。

首先安装依赖：

```bash
# 安装核心库
npm install react-native-permissions

# iOS需要安装对应的pod
cd ios && pod install
```

iOS端需要在`Info.plist`中声明权限使用描述。这段描述会展示在系统权限弹窗中，如果不声明，应用会直接崩溃。Android端需要在`AndroidManifest.xml`中声明权限。

```tsx
// iOS Info.plist - 必须声明权限描述
<key>NSCameraUsageDescription</key>
<string>需要访问相机以拍摄照片</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>需要访问相册以选择照片</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>需要获取您的位置以推荐附近商家</string>

// Android AndroidManifest.xml - 声明权限
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

权限申请的规范流程分为三步：检查、申请、处理。

```tsx
import { request, check, PERMISSIONS, RESULTS } from 'react-native-permissions';

async function requestCameraPermission() {
  // 第一步：检查当前权限状态
  const status = await check(
    Platform.select({
      ios: PERMISSIONS.IOS.CAMERA,
      android: PERMISSIONS.ANDROID.CAMERA,
    })
  );

  if (status === RESULTS.GRANTED) return true;

  // 第二步：申请权限
  const result = await request(
    Platform.select({
      ios: PERMISSIONS.IOS.CAMERA,
      android: PERMISSIONS.ANDROID.CAMERA,
    })
  );

  // 第三步：处理结果
  if (result === RESULTS.GRANTED) {
    return true;
  } else if (result === RESULTS.BLOCKED) {
    // 用户拒绝且勾选了"不再询问"，需要引导去设置页
    Alert.alert('提示', '请在设置中开启相机权限', [
      { text: '去设置', onPress: () => Linking.openSettings() },
// ... 省略部分代码
```

这个流程的关键点在于第三步的结果处理。`RESULTS`有四种状态：`GRANTED`（已授权）、`DENIED`（已拒绝但未永久拒绝）、`BLOCKED`（已永久拒绝）、`UNAVAILABLE`（设备不支持）。`BLOCKED`状态在Android上意味着用户勾选了"不再询问"，此时再次调用request不会弹出系统弹窗，必须引导用户去系统设置页手动开启。很多开发者忽略了这个状态，导致权限申请"静默失败"，用户以为点了没反应，其实是没有引导到设置页。

iOS的权限弹窗只会出现一次。用户第一次选择拒绝后，后续调用request不会再弹窗，直接返回DENIED或BLOCKED。所以iOS端也需要同样的设置页引导逻辑。

> 权限申请是用户对应用的第一印象。如果用户刚打开应用就弹出一堆权限请求，体验极差。怕浪猫总结的权限申请最佳实践是：延迟申请、场景化申请、解释优先。延迟到用户真正需要使用某功能时才申请，而不是一启动就申请所有权限。在申请前先用自定义弹窗解释为什么需要这个权限，用户理解后再发起系统权限请求。这样通过率能提高40%以上。

### 6.1.5 原生API异常容错设计

原生API调用失败的概率远高于JS模块。原因包括权限被拒绝、设备不支持该功能、系统版本差异导致API行为不同、原生模块未正确链接、设备硬件故障等。如果不做容错处理，任何一个异常都会导致应用崩溃或白屏。

合理的容错设计能避免应用崩溃，核心原则是：永不崩溃，优雅降级。原生API调用失败时，返回一个合理的默认值，让业务逻辑继续执行。同时记录错误日志，方便后续排查。

```tsx
// 容错封装模板
class NativeApiWrapper {
  static async safeCall<T>(
    apiCall: () => Promise<T>,
    fallback: T,
    logTag = 'NativeAPI'
  ): Promise<T> {
    try {
      return await apiCall();
    } catch (error) {
      console.warn(`[${logTag}] 调用失败:`, error);
      return fallback;
    }
  }

  // 批量容错调用
  static async safeCallAll<T>(
    calls: Array<{ call: () => Promise<T>; fallback: T; tag: string }>
  ): Promise<T[]> {
    return Promise.all(
      calls.map(({ call, fallback, tag }) =>
        this.safeCall(call, fallback, tag)
      )
    );
  }
}

// 使用示例
// ... 省略部分代码
```

容错设计的另一个重要方面是超时控制。原生API调用可能因为系统原因卡住不返回，比如等待用户响应权限弹窗、设备传感器初始化缓慢等。如果不设置超时，Promise会一直pending，导致后续逻辑无法执行。

```tsx
// 带超时的容错调用
async function safeCallWithTimeout<T>(
  apiCall: () => Promise<T>,
  fallback: T,
  timeout = 5000
): Promise<T> {
  try {
    const result = await Promise.race([
      apiCall(),
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), timeout)
      ),
    ]);
    return result;
  } catch {
    return fallback;
  }
}
```

## 6.2 AsyncStorage本地持久化存储

### 6.2.1 存储API安装与基础语法

AsyncStorage是RN官方推荐的本地持久化存储方案。它是一个异步的、全局的、简单的键值对存储系统。底层实现在不同平台上有差异：iOS上使用NSCache和文件存储的组合方案，Android上使用SQLite或RocksDB。对JS层来说，这些差异是透明的，调用方式完全一致。

从RN 0.59版本开始，AsyncStorage从核心库中剥离出来，需要单独安装`@react-native-async-storage/async-storage`。这个变化是RN社区模块化策略的一部分，核心库只保留最基础的组件，其他能力通过独立包提供。

```bash
npm install @react-native-async-storage/async-storage
# iOS需要执行pod install
cd ios && pod install
```

基础API非常简单，核心方法只有四个：

```tsx
import AsyncStorage from '@react-native-async-storage/async-storage';

// 存储字符串
await AsyncStorage.setItem('username', 'palamangmao');

// 读取字符串
const value = await AsyncStorage.getItem('username');

// 删除指定键
await AsyncStorage.removeItem('username');

// 清空所有存储
await AsyncStorage.clear();
```

除了这四个核心方法，还有批量操作方法`multiSet`和`multiGet`，以及获取所有键的方法`getAllKeys`。批量操作方法能减少Bridge通信次数，在需要同时读写多个键值时性能更好。

```tsx
// 批量存储
await AsyncStorage.multiSet([
  ['username', 'palamangmao'],
  ['theme', 'dark'],
  ['language', 'zh-CN'],
]);

// 批量读取
const pairs = await AsyncStorage.multiGet(['username', 'theme', 'language']);
// 返回: [['username', 'palamangmao'], ['theme', 'dark'], ['language', 'zh-CN']]
```

> AsyncStorage的所有操作都是异步的，返回Promise。不要试图用同步方式调用，这在RN中是不可行的。怕浪猫见过有人在组件render中直接调用getItem然后同步使用返回值，结果永远是null，排查了半天才发现是异步问题。记住一条铁律：render函数中不能有任何异步操作的痕迹，所有异步数据必须通过state管理。

另一个需要注意的问题是存储大小限制。AsyncStorage在Android上默认没有大小限制，但在iOS上由于底层使用NSCache，系统可能在内存紧张时自动清除缓存数据。这意味着你的“持久化”数据在iOS上可能被系统悄悄删除。如果你需要保证数据不被清除，建议使用SQLite或文件存储替代AsyncStorage，或者在存储时加上时间戳，读取时校验数据是否仍然有效。对于关键数据（如登录token），建议同时使用AsyncStorage和Keychain/Keystore双写保底。

### 6.2.2 复杂对象数组数据存储方案

AsyncStorage只能存储字符串。要存储对象或数组，需要配合JSON序列化。这是一个看似简单但暗藏陷阱的操作。

```tsx
// 存储对象
const user = {
  name: '怕浪猫',
  age: 28,
  skills: ['RN', 'iOS', 'Android'],
  address: { city: '深圳', district: '南山' }
};
await AsyncStorage.setItem('user', JSON.stringify(user));

// 读取对象
const raw = await AsyncStorage.getItem('user');
const userObj = raw ? JSON.parse(raw) : null;
```

但直接在业务代码中到处写JSON.stringify和JSON.parse是不好的实践。当数据结构复杂或存储项增多时，代码会变得难以维护。而且JSON序列化有几个容易踩的边界问题。

第一，JSON序列化会丢失函数、undefined、Symbol等值。如果你的数据结构包含这些类型，存储后再读取会发现它们消失了。

```tsx
// 处理undefined值的问题
const data = { a: 1, b: undefined, c: null, d: () => {} };
const safe = JSON.parse(JSON.stringify(data));
// 结果: { a: 1, c: null }，b和d都被丢弃
```

第二，Date对象会被序列化为ISO字符串，读取回来是字符串而不是Date对象，需要手动转换。

```tsx
// Date对象序列化问题
const data = { createdAt: new Date('2024-01-01') };
const raw = JSON.stringify(data); // {"createdAt":"2024-01-01T00:00:00.000Z"}
const restored = JSON.parse(raw);
restored.createdAt instanceof Date; // false，是字符串
// 需要手动转换
restored.createdAt = new Date(restored.createdAt);
```

第三，NaN和Infinity会被序列化为null。如果你的数据包含这些特殊数值，存储后读取会变成null，可能导致业务逻辑异常。

正确的做法是封装统一的存储层，在封装层处理这些边界问题。

```tsx
// 安全的序列化/反序列化
function safeStringify(obj: any): string {
  return JSON.stringify(obj, (key, value) => {
    if (value === undefined) return null; // undefined转null
    if (value instanceof Date) return { __type: 'Date', value: value.toISOString() };
    if (typeof value === 'number' && !isFinite(value)) return null; // NaN/Infinity转null
    return value;
  });
}

function safeParse(raw: string): any {
  return JSON.parse(raw, (key, value) => {
    if (value && value.__type === 'Date') {
      return new Date(value.value);
    }
    return value;
  });
}
```

### 6.2.3 存储增删改查完整操作实战

来看一个完整的用户配置存储实战，涵盖增删改查全部操作。这个实战模拟了一个真实业务场景：用户在设置页面修改偏好配置，配置需要持久化存储，下次启动时自动恢复。

```tsx
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@app:user_settings';

interface UserSettingsType {
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  language: 'zh-CN' | 'en-US' | 'ja-JP';
  notifications: {
    push: boolean;
    email: boolean;
    sms: boolean;
  };
  lastUpdated: string;
}

export class UserSettings {
  // 新增或覆盖整条配置
  static async save(settings: UserSettingsType): Promise<boolean> {
    try {
      const data = { ...settings, lastUpdated: new Date().toISOString() };
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error('保存设置失败', e);
      return false;
    }
  }
// ... 省略部分代码
```

注意上面"部分更新"的实现。AsyncStorage没有原生的patch操作，必须先读取完整数据，合并修改，再写回。这种读-改-写模式在并发场景下存在竞态条件问题：如果两个异步操作同时读取了旧数据，各自修改后写回，后写入的会覆盖先写入的修改。

对于大多数应用场景来说，这个问题不严重，因为用户操作通常是串行的。但如果你有后台定时任务或多个组件同时写同一个key，就需要加锁。

```tsx
// 简单的写锁机制
class AsyncLock {
  private locked = false;
  private queue: Array<() => void> = [];

  async acquire() {
    if (!this.locked) {
      this.locked = true;
      return;
    }
    await new Promise<void>(resolve => this.queue.push(resolve));
    this.locked = true;
  }

  release() {
    this.locked = false;
    const next = this.queue.shift();
    if (next) next();
  }
}

const settingsLock = new AsyncLock();

// 使用锁保护读写操作
static async update(patch: Partial<UserSettingsType>) {
  await settingsLock.acquire();
  try {
    const current = await this.load();
// ... 省略部分代码
```

### 6.2.4 本地存储工具类统一封装

在实际项目中，存储项可能有几十个。用户信息、应用配置、缓存数据、购物车、搜索历史等等，每一项都有自己的key和数据结构。如果每个业务模块都直接调用AsyncStorage，代码会非常松散，key命名冲突、序列化逻辑不一致、错误处理遗漏等问题会层出不穷。统一封装一个Storage工具类是最佳实践。

```tsx
// utils/storage.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

class Storage {
  private prefix: string;

  constructor(prefix = '@app') {
    this.prefix = prefix;
  }

  private key(name: string): string {
    return `${this.prefix}:${name}`;
  }

  async get<T>(name: string, defaultValue: T): Promise<T> {
    try {
      const raw = await AsyncStorage.getItem(this.key(name));
      return raw ? JSON.parse(raw) : defaultValue;
    } catch {
      return defaultValue;
    }
  }

  async set<T>(name: string, value: T): Promise<boolean> {
    try {
      await AsyncStorage.setItem(this.key(name), JSON.stringify(value));
      return true;
    } catch {
// ... 省略部分代码
```

这个封装有几个关键设计点。

第一，统一前缀。所有存储键都加上`@app:`前缀，避免与其他应用或第三方库的存储键冲突。这在引入第三方SDK时特别重要，因为SDK可能也使用AsyncStorage，如果没有前缀隔离，键名冲突会导致数据互相覆盖。

第二，泛型支持。get方法接受泛型参数，让TypeScript推断返回类型，减少类型断言。调用方必须提供默认值，这样调用方永远不会拿到null，减少了null检查的样板代码。

第三，默认值机制。当key不存在或读取失败时，返回defaultValue而不是null。这意味着业务代码中不需要写`if (value === null)`的判断，代码更简洁。

第四，multiGet批量读取。一次Bridge通信读取多个key，比逐个调用getItem效率高得多。每次调用AsyncStorage.getItem都会产生一次Bridge通信，批量读取能将N次通信减少到1次。

第五，clear方法只清除本应用前缀的key，不会清除其他库的存储。这在使用第三方SDK时非常重要，避免清空数据时误删SDK的数据。

> 工具类封装的价值不是减少代码行数，而是收口规范。当所有存储操作都经过同一个入口，你就能统一添加日志、加密、迁移逻辑，而不需要在几十个文件里逐一修改。这就是"约束优于自由"的工程哲学。怕浪猫在团队中推行统一Storage工具类后，存储相关的Bug减少了80%以上，因为所有错误处理和序列化逻辑都在一处维护，不会遗漏。

### 6.2.5 登录态全局持久化落地实战

登录态持久化是AsyncStorage最经典的业务场景，几乎每个应用都需要。用户登录成功后，token和用户信息需要持久化存储，下次启动应用时自动恢复登录态，避免用户每次打开应用都要重新登录。

```tsx
// auth/authStore.ts
import { storage } from '../utils/storage';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';
const LOGIN_TIME_KEY = 'auth_login_time';

interface UserInfo {
  id: string;
  name: string;
  avatar: string;
  phone: string;
  role: 'user' | 'admin';
}

export const authStore = {
  // 登录成功后保存登录态
  async login(token: string, user: UserInfo): Promise<void> {
    await storage.set(TOKEN_KEY, token);
    await storage.set(USER_KEY, user);
    await storage.set(LOGIN_TIME_KEY, Date.now());
  },

  // 应用启动时恢复登录态
  async restore(): Promise<{ token: string; user: UserInfo } | null> {
    const [tokenPair, userPair] = await storage.multiGet([
      TOKEN_KEY, USER_KEY
    ]);
// ... 省略部分代码
```

在应用启动时恢复登录态，需要处理三个状态：加载中、已登录、未登录。

```tsx
// App.tsx
import { useEffect, useState } from 'react';
import { authStore } from './auth/authStore';

type AppState = 'loading' | 'loggedIn' | 'loggedOut';

export default function App() {
  const [appState, setAppState] = useState<AppState>('loading');

  useEffect(() => {
    (async () => {
      try {
        const auth = await authStore.restore();
        if (auth?.token) {
          // 可选：向服务端校验token是否仍然有效
          // const isValid = await verifyToken(auth.token);
          // if (!isValid) {
          //   await authStore.logout();
          //   setAppState('loggedOut');
          //   return;
          // }
          setAppState('loggedIn');
        } else {
          setAppState('loggedOut');
        }
      } catch (e) {
        // 恢复失败，安全降级到登录页
        setAppState('loggedOut');
// ... 省略部分代码
```

这段代码展示了一个完整的登录态恢复流程。应用启动时先显示启动屏（SplashScreen），同时从本地存储读取token和用户信息。存在且未过期则直接进入主应用，不存在或已过期则跳转登录页。为了防止token过期导致接口401，可以在恢复阶段增加一次服务端token校验请求。如果校验失败，清除本地登录态并跳转登录页。

## 6.3 状态栏与沉浸式页面适配

### 6.3.1 StatusBar状态栏样式控制

状态栏是屏幕顶部显示时间、电量、信号的区域。虽然它只占几十像素的高度，但在移动端开发中，状态栏的适配问题却让无数开发者头疼。RN提供了`StatusBar`组件来控制状态栏的样式，包括背景色、文字颜色和透明度。

```tsx
import { StatusBar } from 'react-native';

// 基础设置
<StatusBar
  backgroundColor="#FFFFFF"
  barStyle="dark-content"
  translucent={false}
/>
```

这三个属性在双端的行为差异很大。`backgroundColor`在Android上可以设置状态栏背景色，但在iOS上完全无效，iOS的状态栏背景色由页面顶部View的背景色决定。`barStyle`控制状态栏文字颜色，有两个值：`dark-content`（深色文字，适合浅色背景）和`light-content`（浅色文字，适合深色背景），在iOS和Android上都有效，但Android需要API 23以上才支持。`translucent`控制状态栏是否透明，Android设为true时内容会延伸到状态栏下方，iOS默认就是透明的。

StatusBar组件有一个容易踩的坑：它是命令式的，最后一次设置会全局生效。如果你在页面A设置了深色文字，跳转到页面B没有重新设置，页面B的状态栏还是深色文字。如果页面B的背景是深色的，状态栏文字就看不清了。

```tsx
// 正确做法：每个页面都显式设置StatusBar
function PageA() {
  return (
    <>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      <View style={{ flex: 1, backgroundColor: '#FFFFFF' }} />
    </>
  );
}

function PageB() {
  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor="#000000" />
      <View style={{ flex: 1, backgroundColor: '#000000' }} />
    </>
  );
}
```

> 怕浪猫踩坑记录：曾在一个项目中，首页是白色背景设置了dark-content，详情页是深色背景但忘了设置StatusBar，用户反馈详情页状态栏看不清。这种Bug在模拟器上不明显，因为模拟器的状态栏总是显示的，但在真机上特别是iOS的全屏预览模式下，状态栏文字跟背景融为一体，完全看不见。养成习惯：每写一个页面，第一件事就是设置StatusBar。

### 6.3.2 明暗文字动态切换适配

有些场景需要根据页面滚动位置或用户操作动态切换状态栏样式。比如一个商品详情页，顶部有一张大图，背景是深色的，用户向下滚动后背景变成白色。这时状态栏文字需要从浅色切换到深色。

```
iOS状态栏机制：
  状态栏背景 = 页面顶部View的背景色（不可单独设置）
  状态栏文字 = barStyle控制（dark-content / light-content）

Android状态栏机制：
  状态栏背景 = backgroundColor属性控制
  状态栏文字 = barStyle控制（需API 23+）
  透明状态栏 = translucent属性控制
```

```tsx
import { StatusBar } from 'react-native';

function DynamicStatusBar({ scrollY }: { scrollY: number }) {
  // 滚动超过100px时切换为深色背景模式
  const isDark = scrollY > 100;

  return (
    <StatusBar
      barStyle={isDark ? 'dark-content' : 'light-content'}
      backgroundColor={isDark ? '#FFFFFF' : 'transparent'}
      translucent={!isDark}
      animated
    />
  );
}
```

`animated`属性让状态栏变化有过渡动画，体验更自然。但注意Android上不是所有属性都支持动画过渡，`barStyle`的切换是即时的，没有过渡效果。iOS上`barStyle`的切换会有一段简短的淡入淡出过渡。

除了声明式使用StatusBar组件外，RN还提供了命令式API。`StatusBar.pushStackEntry`和`StatusBar.popStackEntry`允许你将状态栏配置入栈和出栈，实现导航栈级别的状态栏管理。比如用户从页面A导航到页面B，B把状态栏设置入栈，用户返回A时B的设置出栈，A的状态栏配置自动恢复。这种方式比在每个页面手动设置更可靠，特别是在深层嵌套的导航栈中。

对于更复杂的场景，比如嵌套在ScrollView中的页面，需要监听滚动位置来决定状态栏样式。这时可以使用`onScroll`事件配合`Animated.event`来实现。

```tsx
function ProductDetailScreen() {
  const scrollY = useRef(new Animated.Value(0)).current;

  return (
    <>
      <AnimatedStatusBar scrollY={scrollY} />
      <Animated.ScrollView
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { y: scrollY } } }],
          { useNativeDriver: false }
        )}
        scrollEventThrottle={16}
      >
        <ProductHeroImage />
        <ProductInfo />
      </Animated.ScrollView>
    </>
  );
}
```

### 6.3.3 全屏沉浸式页面开发实现

沉浸式页面（如视频播放页、图片预览页、阅读器）需要隐藏状态栏和导航栏，让内容铺满整个屏幕。RN的StatusBar组件提供了`setHidden`方法来实现状态栏的隐藏和显示。

```tsx
import { StatusBar, View, TouchableOpacity, Text } from 'react-native';
import { useState, useEffect } from 'react';

function VideoPlayerScreen({ videoUrl }: { videoUrl: string }) {
  const [immersive, setImmersive] = useState(false);

  useEffect(() => {
    StatusBar.setHidden(immersive, 'slide');
    // 关键：组件卸载时恢复状态栏
    return () => StatusBar.setHidden(false, 'fade');
  }, [immersive]);

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <VideoPlayer source={{ uri: videoUrl }} />
      <TouchableOpacity onPress={() => setImmersive(!immersive)}>
        <Text style={{ color: '#fff' }}>{immersive ? '退出全屏' : '全屏'}</Text>
      </TouchableOpacity>
    </View>
  );
}
```

沉浸式页面开发的关键点在于生命周期清理。组件卸载时必须恢复状态栏显示，否则用户退出页面后状态栏还是隐藏的。上面的代码通过useEffect的cleanup函数确保了这一点。

但这里有一个隐藏的坑：Android系统在内存不足时会杀掉后台Activity，当用户切回应用时会重新创建Activity。这时JS层的useEffect不会执行，状态栏可能保持隐藏状态。解决方案是在Android原生层监听Activity的生命周期事件，在onResume中恢复状态栏。

```tsx
// Android端原生处理（MainActivity.java）
@Override
protected void onResume() {
    super.onResume();
    // 确保状态栏恢复显示
    StatusBarModule.restoreStatusBar();
}
```

> 怕浪猫踩坑记录：视频播放页做了沉浸式，用户点击分享跳到其他App再回来，状态栏消失了。原因是系统可能在后台杀掉并重建你的Activity，useEffect的cleanup不会执行。Android端需要在Activity的生命周期回调中处理状态栏恢复，不能完全依赖JS层。这个问题在iOS上不存在，因为iOS的应用恢复机制不同，StatusBar组件会在应用回到前台时重新应用上一次的设置。

### 6.3.4 刘海屏安全边距适配

从iPhone X开始，刘海屏/灵动岛成为iOS设备的标配。这些设备顶部有不可交互区域（刘海/灵动岛），底部有Home Indicator横条。页面内容如果延伸到这些区域，会被遮挡或影响交互。

安卓阵营也有类似的设计，挖孔屏、水滴屏、升降摄像头等各种异形屏。但安卓的适配方案与iOS不同，需要分别处理。

RN提供了`react-native-safe-area-context`库来统一处理安全区域。这个库提供了响应式的安全区域信息，当设备旋转或安全区域变化时会自动更新。

```bash
npm install react-native-safe-area-context
cd ios && pod install
```

```tsx
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

// 第一步：在App根节点包裹Provider
export default function App() {
  return (
    <SafeAreaProvider>
      <AppContent />
    </SafeAreaProvider>
  );
}

// 第二步：使用SafeAreaView替代普通View
function AppContent() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <Text>内容自动避开刘海和底部横条</Text>
    </SafeAreaView>
  );
}
```

SafeAreaView会自动给内容区域添加padding，避开顶部和底部的不可交互区域。但有时候你不需要全包裹，只需要获取安全区域的边距值来做自定义布局。这时可以使用`useSafeAreaInsets`hook。

```tsx
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function CustomHeader() {
  const insets = useSafeAreaInsets();

  return (
    <View style={{
      paddingTop: insets.top,
      paddingBottom: insets.bottom,
      paddingLeft: insets.left,
      paddingRight: insets.right,
    }}>
      <Text>自定义安全区域布局</Text>
    </View>
  );
}
```

```
安全区域结构图（iPhone X+设备）：

┌───────────────────────────┐
│      刘海/灵动岛区域       │ ← insets.top (约44-59pt)
├───────────────────────────┤
│                           │
│                           │
│     安全内容区域           │ ← 页面内容应该在这区域内
│                           │
│                           │
├───────────────────────────┤
│    Home Indicator 横条     │ ← insets.bottom (约34pt)
└───────────────────────────┘

  左右边距（横屏时）:
  insets.left / insets.right (约44pt)
```

### 6.3.5 安卓iOS双端差异化兼容

状态栏在Android和iOS上有多个差异点，需要分别处理。下面是一张完整的差异对照表，建议收藏。

| 差异项 | iOS | Android |
|--------|-----|---------|
| 背景色设置 | 不支持，由页面决定 | 支持，通过backgroundColor |
| 文字颜色切换 | dark/light | dark/light（需API 23+） |
| 透明状态栏 | 默认透明 | 需设translucent=true |
| 状态栏高度 | 固定44pt（刘海屏59pt） | 设备相关，约24-48dp |
| 隐藏动画 | fade/slide | fade |
| 动态切换 | pushStackEntry/popStackEntry | setBarStyle命令式 |

```tsx
import { StatusBar, Platform } from 'react-native';

// 自适应状态栏组件
function AdaptiveStatusBar({ backgroundColor }: { backgroundColor: string }) {
  return (
    <StatusBar
      barStyle={isLightColor(backgroundColor) ? 'dark-content' : 'light-content'}
      backgroundColor={Platform.select({
        ios: 'transparent',
        android: backgroundColor,
      })}
      translucent={Platform.OS === 'ios'}
      animated
    />
  );
}

// 判断颜色是否为浅色（用于决定状态栏文字颜色）
function isLightColor(hex: string): boolean {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  // 使用ITU-R BT.601亮度公式
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5;
}
```

这段代码实现了一个自适应状态栏组件。传入背景色后，自动计算亮度，选择合适的文字颜色模式。Android端设置背景色，iOS端设为透明（由页面背景色决定）。这是最常用的双端适配方案，建议在每个页面的根组件中使用。

## 6.4 弹窗、Toast与全局提示组件

### 6.4.1 Alert原生弹窗基础使用场景

RN内置的`Alert`组件提供了系统级别的弹窗能力。它调用的是原生UI，性能好，体验一致，适合做确认、警告等简单交互。

```tsx
import { Alert } from 'react-native';

// 基础提示弹窗
Alert.alert('提示', '操作成功');

// 确认弹窗（两个按钮）
Alert.alert('确认删除', '删除后不可恢复', [
  { text: '取消', style: 'cancel' },
  { text: '确认删除', style: 'destructive', onPress: () => deleteItem() },
]);

// 三按钮弹窗
Alert.alert('保存修改', '是否保存当前修改?', [
  { text: '不保存', style: 'destructive', onPress: () => discard() },
  { text: '取消', style: 'cancel' },
  { text: '保存', onPress: () => save() },
]);
```

Alert的优势在于它是原生渲染的，不会阻塞JS线程，即使页面卡死也能弹出。它的样式跟系统原生弹窗完全一致，用户不会有跨平台的违和感。但它的局限也很明显：样式无法自定义，按钮最多三个（iOS限制），不能放图片或复杂内容，不能控制弹窗的消失时机（只能用户点击按钮后关闭）。

> Alert的使用原则是"关键时刻用原生"。删除确认、退出登录、错误提示这类需要用户明确感知的场景，用Alert最合适。如果要做花哨的弹窗效果，应该用自定义Modal。怕浪猫在项目中看到过用Alert做"加载中"提示的，用户必须点确定才能关闭，这完全是误用。加载提示应该用不阻塞的Loading组件，而不是强制交互的Alert。

### 6.4.2 确认弹窗、多选弹窗实战开发

当Alert无法满足需求时，需要使用Modal组件自定义弹窗。自定义弹窗的优势在于样式完全可控，可以放置任意内容。来看一个生产级别的确认弹窗完整实现。

```tsx
import { Modal, View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';

interface ConfirmProps {
  visible: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmColor?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  visible, title, message,
  confirmText = '确认',
  cancelText = '取消',
  confirmColor = '#007AFF',
  onConfirm, onCancel,
}: ConfirmProps) {
  return (
    <Modal visible={visible} transparent animationType="fade">
      <View style={styles.overlay}>
        <View style={styles.dialog}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.message}>{message}</Text>
          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.btnCancel} onPress={onCancel}>
// ... 省略部分代码
```

对于多选项弹窗，iOS端可以使用系统自带的`ActionSheetIOS`组件，体验与原生一致。Android端没有系统级的ActionSheet，需要用自定义Modal实现。

```tsx
import { ActionSheetIOS, Platform, Modal, View, Text, TouchableOpacity } from 'react-native';

function showActionSheet(
  options: string[],
  onSelect: (index: number) => void
) {
  if (Platform.OS === 'ios') {
    ActionSheetIOS.showActionSheetWithOptions(
      {
        options: [...options, '取消'],
        cancelButtonIndex: options.length,
        destructiveButtonIndex: -1,
      },
      onSelect
    );
  } else {
    // Android使用自定义底部弹窗
    setActionSheetState({ visible: true, options, onSelect });
  }
}
```

### 6.4.3 自定义轻提示Toast封装

RN没有内置Toast组件。社区库`react-native-toast-message`是主流方案，功能完善但样式需要大量定制。如果你的项目只需要基础Toast功能，自实现一个轻量级方案更合适。

Toast的实现思路是：在App根节点放置一个全局Toast组件，通过ref暴露show方法，任何地方都可以通过全局函数调用来显示Toast。

```tsx
import { useEffect, useState } from 'react';
import { View, Text, Animated, StyleSheet, Platform } from 'react-native';

type ToastType = 'success' | 'error' | 'info';

let toastRef: { show: (msg: string, type?: ToastType) => void } | null = null;

export function Toast() {
  const [visible, setVisible] = useState(false);
  const [message, setMessage] = useState('');
  const [type, setType] = useState<ToastType>('info');
  const [opacity] = useState(new Animated.Value(0));

  useEffect(() => {
    toastRef = {
      show: (msg: string, t: ToastType = 'info') => {
        setMessage(msg);
        setType(t);
        setVisible(true);
        // 淡入动画
        Animated.timing(opacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }).start();
        // 2秒后淡出
        setTimeout(() => {
          Animated.timing(opacity, {
// ... 省略部分代码
```

使用方式非常简单，在App根节点放置Toast组件，然后在任何地方调用`showToast`。

```tsx
// App.tsx
export default function App() {
  return (
    <>
      <MainApp />
      <Toast />
    </>
  );
}

// 任意位置调用
showToast('保存成功', 'success');
showToast('网络错误', 'error');
showToast('正在加载...', 'info');
```

`pointerEvents="none"`是一个关键属性，它确保Toast不会拦截触摸事件。如果不设置这个属性，Toast显示期间用户无法点击下方的按钮，这在交互上是很糟糕的体验。

Toast实现中还有一个容易忽略的细节：当连续多次调用showToast时，后一次调用的定时器不会取消前一次的定时器。这会导致Toast在短时间内闪烁，因为前一次的淡出动画和后一次的淡入动画会重叠。解决方案是在show方法中保存定时器引用，每次调用前先clearTimeout上一个定时器。

### 6.4.4 全局Loading加载弹窗实现

全局Loading需要一个在任何位置都能调用的加载提示。和Toast类似，通过全局ref来实现。Loading与Toast的区别在于：Loading是模态的（阻塞用户交互），Toast是非模态的（不阻塞交互）。

```tsx
import { Modal, View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useEffect, useState } from 'react';

let loadingRef: { show: (msg?: string) => void; hide: () => void } | null = null;

export function LoadingProvider() {
  const [visible, setVisible] = useState(false);
  const [text, setText] = useState('加载中...');

  useEffect(() => {
    loadingRef = {
      show: (msg?: string) => {
        if (msg) setText(msg);
        setVisible(true);
      },
      hide: () => setVisible(false),
    };
    return () => { loadingRef = null; };
  }, []);

  return (
    <Modal visible={visible} transparent animationType="none">
      <View style={styles.overlay}>
        <View style={styles.container}>
          <ActivityIndicator size="large" color="#FFFFFF" />
          <Text style={styles.text}>{text}</Text>
        </View>
      </View>
// ... 省略部分代码
```

使用时需要注意一个关键问题：Loading必须保证show和hide成对调用。如果show了但忘记hide，用户会被永久阻塞。建议在使用时配合try-finally确保hide一定会执行。

```tsx
async function submitForm() {
  showLoading('提交中...');
  try {
    await api.submit(formData);
    showToast('提交成功', 'success');
    navigation.goBack();
  } catch (e) {
    showToast('提交失败: ' + e.message, 'error');
  } finally {
    hideLoading(); // 确保一定会关闭
  }
}
```

### 6.4.5 消息提示交互规范统一

在一个成熟项目中，Alert、Toast、Loading应该有统一的使用规范。不能有的页面用Toast做错误提示，有的页面用Alert做错误提示，有的页面直接在页面上显示错误文字。提示方式不统一会导致用户体验混乱。

怕浪猫总结了一套交互规范清单，建议作为团队规范落地。

| 场景 | 推荐组件 | 说明 |
|------|---------|------|
| 删除/退出确认 | Alert或自定义ConfirmDialog | 需要用户明确操作 |
| 操作成功提示 | Toast(success) | 2秒自动消失 |
| 操作失败提示 | Toast(error) | 2秒自动消失 |
| 网络请求中 | Loading | 阻塞交互，请求结束关闭 |
| 表单验证错误 | 内联文字提示 | 不用Toast，直接在输入框旁显示 |
| 重要信息告知 | 自定义Modal | 需要用户阅读后关闭 |
| 非关键信息提示 | Toast(info) | 2秒自动消失 |
| 危险操作警告 | Alert(destructive) | 红色按钮强调危险性 |

> 提示组件的统一规范比技术实现更重要。怕浪猫见过一个项目里同时用了三个Toast库，有的页面用toast、有的用Toast、有的用Tip，样式五花八门。统一封装后，维护成本直接砍半。技术方案的统一性本身就是一种工程能力。团队的提示组件规范应该在项目初期就确定，而不是等到代码已经混乱了再来收口。

## 6.5 设备信息与屏幕状态监听

### 6.5.1 设备型号、系统版本信息获取

`react-native-device-info`是获取设备信息的标准库，提供了数十种设备信息读取能力。这些信息在异常上报、灰度发布、兼容性判断等场景中不可或缺。

```bash
npm install react-native-device-info
cd ios && pod install
```

```tsx
import DeviceInfo from 'react-native-device-info';

// === 同步方法 ===
// 设备品牌
const brand = DeviceInfo.getBrand();        // "Apple" / "Xiaomi" / "Huawei"
// 设备型号（用户可读名称）
const model = DeviceInfo.getModel();        // "iPhone 15 Pro" / "Pixel 8"
// 设备ID（内部型号标识）
const deviceId = DeviceInfo.getDeviceId();  // "iPhone15,2" / "Pixel8"
// 系统名称
const system = DeviceInfo.getSystemName();  // "iOS" / "Android"
// 系统版本
const version = DeviceInfo.getSystemVersion(); // "17.4.1" / "14.0"
// 应用版本号
const appVersion = DeviceInfo.getVersion();    // "1.2.0"
// 应用构建号
const buildNumber = DeviceInfo.getBuildNumber(); // "42"
// 应用包名
const bundleId = DeviceInfo.getBundleId();   // "com.example.myapp"

// === 异步方法 ===
// 运营商
const carrier = await DeviceInfo.getCarrier();  // "中国移动"
// 总内存（字节）
const totalMemory = await DeviceInfo.getTotalMemory();
// 可用内存（字节）
const freeMemory = await DeviceInfo.getFreeMemory();
// 电池电量（0-1）
// ... 省略部分代码
```

需要注意同步方法和异步方法的区分。`getBrand`、`getModel`等是同步的，因为它们读取的是静态信息，不涉及系统API调用。而`getCarrier`、`getTotalMemory`等是异步的，因为它们需要调用原生系统API，涉及跨线程通信。

设备信息最常见的用途是上报到后端做用户分析。建议在应用启动时收集一次，缓存在全局变量中，避免重复调用。尤其是异步方法，每次调用都会产生Bridge通信开销，频繁调用会影响性能。

```tsx
// utils/deviceProfile.ts
let cachedProfile: DeviceProfile | null = null;

export async function getDeviceProfile(): Promise<DeviceProfile> {
  if (cachedProfile) return cachedProfile;

  cachedProfile = {
    brand: DeviceInfo.getBrand(),
    model: DeviceInfo.getModel(),
    system: DeviceInfo.getSystemName(),
    systemVersion: DeviceInfo.getSystemVersion(),
    appVersion: DeviceInfo.getVersion(),
    buildNumber: DeviceInfo.getBuildNumber(),
    bundleId: DeviceInfo.getBundleId(),
    // 异步信息单独获取
    carrier: await safeCall(() => DeviceInfo.getCarrier(), 'unknown'),
    totalMemory: await safeCall(() => DeviceInfo.getTotalMemory(), 0),
  };

  return cachedProfile;
}
```

### 6.5.2 屏幕尺寸、像素密度读取

RN提供了`Dimensions`和`PixelRatio`两个模块来获取屏幕信息。理解逻辑像素和物理像素的关系是做好屏幕适配的基础。

```tsx
import { Dimensions, PixelRatio } from 'react-native';

// 屏幕尺寸（逻辑像素）
const { width, height, scale, fontScale } = Dimensions.get('window');
// width: 逻辑宽度，单位pt（iOS）或dp（Android）
// height: 逻辑高度
// scale: 像素密度比（物理像素/逻辑像素）
// fontScale: 用户字体缩放比例

// 物理像素
const pixelWidth = width * scale;
const pixelHeight = height * scale;

// PixelRatio工具
const ratio = PixelRatio.get();        // 像素密度，如2、3
const fontScaleVal = PixelRatio.getFontScale(); // 用户字体缩放
const realWidth = PixelRatio.getPixelSizeForLayoutSize(width); // 转换为物理像素
```

```
逻辑像素 vs 物理像素：

  设计稿（逻辑像素）    →    设备屏幕（物理像素）
  375 x 812 pt          →    1125 x 2436 px
  倍率: @3x              →    scale = 3

  转换公式:
    物理像素 = 逻辑像素 × scale
    逻辑像素 = 物理像素 / scale

  常见设备对照：
  iPhone SE:   320 x 568 pt,  scale=2  → 640 x 1136 px
  iPhone 15:   393 x 852 pt,  scale=3  → 1179 x 2556 px
  iPhone 15 Pro Max: 430 x 932 pt, scale=3 → 1290 x 2796 px
  Pixel 8:     412 x 915 dp,  scale=2.625 → 1080 x 2400 px
```

在实际开发中，屏幕信息主要用于响应式布局。建议监听屏幕变化，而不是只在启动时获取一次。因为用户可能旋转设备、分屏操作，或者在平板上调整窗口大小。

```tsx
import { Dimensions } from 'react-native';

export function useDimensions() {
  const [dims, setDims] = useState(Dimensions.get('window'));

  useEffect(() => {
    const sub = Dimensions.addEventListener('change', ({ window }) => {
      setDims(window);
    });
    return () => sub.remove();
  }, []);

  return dims;
}

// 使用示例：响应式布局
function ResponsiveGrid() {
  const { width } = useDimensions();
  const columns = width > 600 ? 3 : width > 400 ? 2 : 1;
  const itemWidth = (width - 16 * (columns + 1)) / columns;

  return (
    <FlatList
      numColumns={columns}
      data={products}
      renderItem={({ item }) => (
        <View style={{ width: itemWidth, margin: 8 }}>
          <ProductCard product={item} />
// ... 省略部分代码
```

### 6.5.3 设备唯一标识获取与应用

设备唯一标识用于用户统计、设备绑定、防刷等场景。iOS和Android的获取方式不同，且都有限制，这是隐私保护趋势下的必然结果。

iOS平台上有三种标识符。UDID（Unique Device Identifier）已经废弃，开发者无法获取。IDFA（Identifier for Advertising）从iOS 14.5开始需要用户授权ATT（App Tracking Transparency）才能获取，大部分用户会拒绝。IDFV（Identifier for Vendor）是同一开发者的应用共享的标识符，卸载重装会变化，是目前最可用的方案。

Android平台上有ANDROID_ID，卸载重装不变，但用户恢复出厂设置会变。还有IMEI（International Mobile Equipment Identity），但从Android 10开始开发者无法获取。

```tsx
import DeviceInfo from 'react-native-device-info';

// 推荐方案：首次启动生成UUID并存储到AsyncStorage
import AsyncStorage from '@react-native-async-storage/async-storage';

async function getDeviceUUID(): Promise<string> {
  // 先从本地存储读取
  let uuid = await AsyncStorage.getItem('device_uuid');
  if (uuid) return uuid;

  // 首次生成：使用DeviceInfo的getUniqueId作为基础
  try {
    uuid = await DeviceInfo.getUniqueId();
  } catch {
    // getUniqueId可能失败（权限问题），降级为随机UUID
    uuid = generateUUID();
  }

  await AsyncStorage.setItem('device_uuid', uuid);
  return uuid;
}

// UUID生成（省略实现细节）
function generateUUID(): string { /* ... */ }
```

这个方案的思路是：首次启动时尝试使用系统提供的唯一标识，失败则生成随机UUID。无论哪种方式，都把结果存到AsyncStorage中。后续每次启动直接从本地读取，不再调用系统API。这样既保证了唯一性，又避免了每次都申请权限。

> 设备唯一标识的获取方案需要根据业务需求选择。如果你的应用不需要广告追踪，就不要申请IDFA权限，这会降低用户的信任度。怕浪猫在项目中遇到过一个坑：使用了IDFA作为设备标识，更新到iOS 14.5后大量用户拒绝授权，导致设备标识全部变成空值，后端的设备绑定逻辑全部失效。改用IDFV+AsyncStorage方案后才恢复。

### 6.5.4 横竖屏状态实时监听切换

横竖屏切换时，屏幕宽高会互换。如果布局是按竖屏设计的，切换到横屏后可能出现排版错乱。需要实时监听屏幕方向变化并更新布局。

```tsx
import { Dimensions } from 'react-native';

function useOrientation() {
  const getOrientation = () => {
    const { width, height } = Dimensions.get('window');
    return width > height ? 'landscape' : 'portrait';
  };

  const [orientation, setOrientation] = useState(getOrientation);

  useEffect(() => {
    const sub = Dimensions.addEventListener('change', ({ window }) => {
      setOrientation(window.width > window.height ? 'landscape' : 'portrait');
    });
    return () => sub.remove();
  }, []);

  return orientation;
}

// 使用示例：视频播放器根据方向调整布局
function VideoPlayer({ url }: { url: string }) {
  const orientation = useOrientation();
  const isLandscape = orientation === 'landscape';

  return (
    <View style={{
      flex: 1,
// ... 省略部分代码
```

### 6.5.5 设备信息业务场景落地

设备信息的业务应用场景非常广泛。来看三个实际案例。

**场景一：异常上报。** 当应用崩溃时，附带设备信息能帮助快速定位问题。后端收到崩溃日志后，可以根据设备型号和系统版本筛选同类问题，判断是普遍Bug还是特定设备兼容性问题。

```tsx
async function reportError(error: Error, stack: string) {
  const profile = await getDeviceProfile();
  await fetch('/api/error-report', {
    method: 'POST',
    body: JSON.stringify({
      error: error.message,
      stack,
      device: profile,
      timestamp: Date.now(),
    }),
  });
}

// 在全局错误处理中调用
ErrorUtils.setGlobalHandler((error, isFatal) => {
  reportError(error, error.stack || '');
});
```

**场景二：灰度发布。** 根据设备型号、系统版本控制功能开关。新功能先在小范围设备上上线，确认没有问题后再全量发布。

```tsx
async function checkFeatureEnabled(feature: string): Promise<boolean> {
  const profile = await getDeviceProfile();

  // 规则1：iOS 15以下不支持某功能
  if (profile.system === 'iOS' && parseFloat(profile.systemVersion) < 15) {
    return false;
  }

  // 规则2：Android 12以下不支持某功能
  if (profile.system === 'Android' && parseFloat(profile.systemVersion) < 12) {
    return false;
  }

  // 规则3：特定型号设备灰度
  const graylist = ['iPhone 15 Pro', 'Pixel 8', 'SM-S9110'];
  if (!graylist.includes(profile.model)) {
    return false;
  }

  return true;
}
```

**场景三：适配统计。** 收集用户设备分布，指导适配优先级。如果80%的用户使用iPhone 15系列，那适配重点就应该放在这些设备上。反之如果大量用户使用老旧设备，就需要重点优化低端机型的性能。这种数据驱动的适配策略，比盲目全覆盖高效得多。对于MVP（Minimum Viable Product）阶段的产品来说，设备信息采集尤其重要，因为早期资源有限，必须优先适配核心用户群使用的设备。

```tsx
async function reportDeviceStats() {
  const profile = await getDeviceProfile();
  await fetch('/api/stats/device', {
    method: 'POST',
    body: JSON.stringify({
      model: profile.model,
      system: profile.system,
      version: profile.systemVersion,
      appVersion: profile.appVersion,
      carrier: profile.carrier,
    }),
  });
}
```

> 设备信息不是"获取了就完事"的数据，它是整个运维体系的基础。崩溃分析、灰度发布、兼容性测试、性能优化，全都依赖准确的设备信息。怕浪猫建议在项目第一天就把设备信息采集做好，不要等到出了线上Bug才后悔没有提前埋点。一个完整的设备信息上报方案，能帮你节省大量的问题排查时间。

## 6.6 网络状态监听与弱网适配

### 6.6.1 网络模块安装与基础配置

`@react-native-community/netinfo`是RN官方维护的网络状态监听库，能获取网络类型、是否在线、连接质量等信息。它取代了旧版RN核心库中被废弃的NetInfo模块，提供了更丰富的网络信息和更一致的双端体验。

```bash
npm install @react-native-community/netinfo
cd ios && pod install
```

基础用法：

```tsx
import NetInfo from '@react-native-community/netinfo';

// 单次获取网络状态
const state = await NetInfo.fetch();
console.log(state.type);               // "wifi" / "cellular" / "none" / "unknown"
console.log(state.isConnected);         // true / false
console.log(state.isInternetReachable); // true / false / null
```

`type`字段在Android上能区分WiFi（Wireless Fidelity）和蜂窝网络的具体代次（2G/3G/4G/5G），在iOS上只返回"wifi"或"cellular"，不区分具体代次。这是因为iOS的API限制，苹果不允许第三方应用获取蜂窝网络的具体类型。

`isInternetReachable`表示是否能真正访问互联网，这比`isConnected`更可靠。`isConnected`只检查设备是否连上了网络（比如连上了WiFi路由器），但不检查这个路由器是否有外网连接。在公共WiFi、企业内网等场景下，`isConnected`返回true但`isInternetReachable`返回false。

### 6.6.2 网络类型与在线状态识别

NetInfo返回的state对象包含丰富的网络信息。来看不同网络状态下的返回值结构和业务含义。

```
NetInfo state 完整结构：

┌───────────────────────────────────────┐
│ type: 网络类型                         │
│   "wifi"      - WiFi网络              │
│   "cellular"  - 蜂窝网络              │
│   "bluetooth" - 蓝牙网络              │
│   "ethernet"  - 以太网                │
│   "none"      - 无网络                │
│   "unknown"   - 未知状态              │
│                                       │
│ isConnected: 是否已连接网络            │
│   true / false                         │
│                                       │
│ isInternetReachable: 是否可访问互联网  │
│   true / false / null                 │
│                                       │
│ details: 详细信息（type相关）          │
│   isConnectionExpensive: 是否计费网络  │
│   cellularGeneration: 蜂窝代次         │
│     "2g" / "3g" / "4g" / "5g"         │
│   strength: 信号强度（仅Android）      │
│   ipAddress: IP地址                    │
│   subnet: 子网掩码                     │
│   frequency: WiFi频率（仅Android）     │
│     "2.4GHz" / "5GHz"                 │
└───────────────────────────────────────┘
```

```tsx
// 网络状态描述工具函数
function getNetworkDesc(state: NetInfoState): string {
  if (!state.isConnected) return '无网络连接';
  if (state.type === 'wifi') return 'WiFi网络';
  if (state.type === 'cellular') {
    const gen = state.details?.cellularGeneration;
    if (gen === '5g') return '5G网络';
    if (gen === '4g') return '4G网络';
    if (gen === '3g') return '3G网络';
    if (gen === '2g') return '2G网络';
    return '蜂窝网络';
  }
  if (state.type === 'ethernet') return '以太网';
  return '未知网络';
}

// 判断是否计费网络（用于决定是否预加载大文件）
function isNetworkExpensive(state: NetInfoState): boolean {
  if (state.type === 'cellular') return true;
  return state.details?.isConnectionExpensive ?? false;
}

// 判断是否弱网
function isWeakNetwork(state: NetInfoState): boolean {
  if (!state.isConnected) return true;
  if (state.type === 'cellular') {
    const gen = state.details?.cellularGeneration;
    return gen === '2g' || gen === '3g';
// ... 省略部分代码
```

`isConnectionExpensive`在Android上由系统判断当前网络是否是计费网络（如蜂窝数据或有流量限制的WiFi热点），系统建议在这种网络下减少数据传输。iOS不支持这个字段，需要通过`type === 'cellular'`来间接判断。

### 6.6.3 网络变化实时监听回调

单次获取网络状态是不够的，大多数场景需要实时监听网络变化。比如用户从WiFi切换到蜂窝网络时，需要暂停大文件下载；网络断开时需要显示提示；网络恢复时需要重新发送失败的请求。

```tsx
import NetInfo from '@react-native-community/netinfo';

// 自定义Hook：监听网络状态
function useNetInfo() {
  const [state, setState] = useState<NetInfoState | null>(null);

  useEffect(() => {
    // 订阅网络变化事件
    const unsubscribe = NetInfo.addEventListener(setState);
    // 立即获取一次当前状态，避免初始值为null
    NetInfo.fetch().then(setState);

    return () => {
      // 关键：组件卸载时取消订阅，避免内存泄漏
      unsubscribe();
    };
  }, []);

  return state;
}

// 使用示例
function AppContent() {
  const netInfo = useNetInfo();

  // 断网时显示离线页面
  if (netInfo && !netInfo.isConnected) {
    return <OfflineScreen />;
// ... 省略部分代码
```

这段代码实现了一个网络状态hook。`NetInfo.addEventListener`返回一个取消订阅函数，在组件卸载时调用，避免内存泄漏。同时立即获取一次当前状态，确保hook初始化时就有值，不会出现第一帧渲染时netInfo为null的问题。

### 6.6.4 断网提示与重连适配方案

断网场景需要做两件事：给用户视觉提示，以及在网络恢复后自动重连失败的请求。

```tsx
import NetInfo from '@react-native-community/netinfo';

// 全局网络监听管理器
class NetworkManager {
  private listeners = new Set<(online: boolean) => void>();
  private isOnline = true;
  private pendingRequests: Array<() => Promise<any>> = [];

  init() {
    NetInfo.addEventListener((state) => {
      const online = state.isConnected ?? false;
      if (online !== this.isOnline) {
        this.isOnline = online;
        this.listeners.forEach(fn => fn(online));
        // 网络恢复后，自动重试失败的请求
        if (online) {
          this.flushPendingRequests();
        }
      }
    });
  }

  onStatusChange(fn: (online: boolean) => void) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  // 带自动重试的请求
// ... 省略部分代码
```

在UI层，断网时显示一个全局提示条：

```tsx
function NetworkBanner() {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    return network.onStatusChange((isOnline) => {
      setOnline(isOnline);
      if (isOnline) {
        showToast('网络已恢复', 'success');
      } else {
        showToast('网络连接已断开', 'error');
      }
    });
  }, []);

  if (online) return null;

  return (
    <View style={styles.banner}>
      <Text style={styles.bannerText}>网络不可用，请检查网络设置</Text>
    </View>
  );
}
```

### 6.6.5 弱网体验优化与容错处理

弱网环境（如2G/3G、信号差的WiFi、网络拥堵的公共热点）是最考验应用质量的场景。弱网下请求超时、数据不完整、页面卡顿是三大常见问题。用户在弱网环境下的耐心极低，如果应用超过3秒没有响应，大部分用户会直接退出。

**策略一：请求超时控制。** 默认fetch没有超时机制，在网络极差时会一直pending，导致页面无限等待。需要手动实现超时控制。

```tsx
function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout = 10000
): Promise<Response> {
  return Promise.race([
    fetch(url, options),
    new Promise<Response>((_, reject) =>
      setTimeout(() => reject(new Error('请求超时')), timeout)
    ),
  ]);
}
```

`Promise.race`让fetch和超时定时器赛跑，谁先完成就用谁的结果。如果定时器先触发，fetch被reject，进入catch分支。这个技巧简单但非常实用。

**策略二：数据缓存兜底。** 网络请求失败时，使用本地缓存的数据展示，而不是白屏。用户看到的是上次的数据，虽然可能不是最新的，但比白屏好得多。

```tsx
async function fetchWithCache(url: string, cacheKey: string) {
  try {
    const res = await fetchWithTimeout(url);
    const data = await res.json();
    // 请求成功，更新缓存
    await storage.set(cacheKey, data);
    return { data, fromCache: false };
  } catch (e) {
    // 请求失败，尝试读取缓存
    const cached = await storage.get(cacheKey, null);
    if (cached) {
      return { data: cached, fromCache: true };
    }
    throw e; // 既没有网络也没有缓存，抛出错误
  }
}
```

**策略三：骨架屏占位。** 弱网下数据加载慢，用骨架屏避免白屏等待。骨架屏的形状跟实际内容一致，给用户"数据即将出现"的预期，减少焦虑感。

```tsx
function ProductList() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fromCache, setFromCache] = useState(false);

  useEffect(() => {
    fetchWithCache('/api/products', 'cache_products')
      .then(({ data, fromCache }) => {
        setData(data);
        setFromCache(fromCache);
        if (fromCache) showToast('当前为缓存数据', 'info');
      })
      .catch(() => {
        showToast('加载失败，请稍后重试', 'error');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonList count={5} />;
  return (
    <>
      {fromCache && <CacheBanner />}
      <FlatList data={data} renderItem={ProductCard} />
    </>
  );
}
```

**策略四：弱网感知与降级。** 通过NetInfo判断网络质量，弱网下主动降低数据传输量和请求频率。

```tsx
function useWeakNetwork() {
  const [weak, setWeak] = useState(false);

  useEffect(() => {
    const unsub = NetInfo.addEventListener((state) => {
      const isCellular = state.type === 'cellular';
      const isSlowGen = state.details?.cellularGeneration === '2g'
        || state.details?.cellularGeneration === '3g';
      setWeak(isCellular && isSlowGen === true);
    });
    return () => unsub();
  }, []);

  return weak;
}

// 使用：弱网下加载缩略图而非原图
function ProductImage({ url }: { url: string }) {
  const isWeak = useWeakNetwork();
  const imageUrl = isWeak ? getThumbnailUrl(url) : url;

  return <Image source={{ uri: imageUrl }} style={styles.image} />;
}
```

```
弱网降级策略对照表：

┌──────────────┬──────────────────┬──────────────────────┐
│  正常网络     │  弱网环境         │  断网环境             │
├──────────────┼──────────────────┼──────────────────────┤
│  加载高清图   │  加载缩略图       │  显示占位图+缓存      │
│  自动播放视频 │  点击播放+标清    │  提示网络不可用       │
│  实时刷新数据 │  延长刷新间隔     │  使用本地缓存         │
│  预加载下一页 │  取消预加载       │  隐藏分页控件         │
│  并发多请求   │  串行单请求       │  暂停所有请求         │
│  加载全部字段 │  只加载必要字段   │  显示缓存数据         │
│  大文件上传   │  分片上传+断点续传 │  保存到本地待发送     │
└──────────────┴──────────────────┴──────────────────────┘
```

> 弱网适配的核心不是"让请求更快"，而是"让用户感觉不到慢"。骨架屏、缓存兜底、降级策略，三板斧下去，用户在地铁里用你的App也不会觉得难用。怕浪猫在做一个电商项目时，靠这三招把弱网下的跳出率从40%降到了12%。技术优化的价值，最终体现在业务数据上。不要等用户投诉了才做弱网优化，在开发阶段就应该用Network Link Conditioner（iOS）或Charles模拟弱网测试。

本章完整覆盖了RN原生设备API开发的核心知识面。从原生模块调用规范到权限管理，从本地存储到状态栏适配，从弹窗Toast到设备信息获取，从网络监听到弱网容错，每一块都是生产环境的硬需求。这些内容不是"锦上添花"，而是"没有就上线不了"的基础设施。

下面是一张本章知识体系的收藏清单，建议保存：

**原生设备API开发六步清单：**

1. 原生API调用四步法：检查权限、异步调用、结果处理、异常容错。每一步都不能省，省了就是线上事故
2. AsyncStorage封装三件套：统一前缀避免冲突、泛型支持类型安全、默认值机制消除null检查
3. 状态栏适配双端差异表：iOS透明背景由页面决定、Android可设背景色、刘海屏用SafeAreaView
4. 弹窗交互规范矩阵：确认用Alert/ConfirmDialog、提示用Toast、加载用Loading、验证用内联
5. 设备信息采集方案：启动时缓存避免重复调用、UUID本地生成保底、异常上报必带设备信息
6. 网络状态管理三板斧：实时监听网络变化、断网自动重连重试、弱网降级缓存兜底

**系列进度 6/16**

怕浪猫说：原生API是RN开发的分水岭。能用JS写完的只是入门，能驾驭原生能力并做好双端适配的才是工程。本章给的每一套封装模板，都是经过线上项目验证的方案，直接拿去用，能帮你省掉至少两周的踩坑时间。下一章我们进入动画与手势的世界，那才是RN真正展现魅力的领域。

下一章预告：第7章《RN动画系统与手势交互实战》将深入讲解Animated动画API、LayoutAnimation布局动画、Reanimated高级动画、手势系统与动画联动，以及性能优化策略。从静态页面到动态交互，让你的应用"活"起来。

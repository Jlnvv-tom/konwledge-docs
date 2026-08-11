---
sidebar_position: 12
---

# 第12章 RN原生混合开发与双端原生模块适配

> 真正的混合开发不是"JS写业务、原生靠边站"，而是JS与原生深度协作的工程艺术。

一个扎心的事实：80%的RN（React Native）开发者在第一次需要调用原生功能时，会陷入茫然。JS（JavaScript）层写好了调用代码，Android端报Module不存在，iOS端编译直接红屏，翻遍了官方文档还是一头雾水。更痛苦的是，明明同样的代码在模拟器上跑得好好的，到真机上就各种崩溃，而崩溃栈里全是看不懂的Objective-C和Java堆栈。我见过一个团队为了接入一个指纹识别原生模块，Android搞了一周、iOS搞了两周，最后还因为权限处理不一致被用户投诉。也见过有人在iOS端写原生模块时没注意线程安全，导致偶发崩溃，测试阶段查了三天才定位到是多线程访问共享资源的问题。原生混合开发就是RN全栈路上最大的分水岭，跨过去了海阔天空，跨不过去寸步难行。

这还不是最惨的。有的团队为了赶进度，原生模块写完能跑就算完事，完全没有考虑双端行为一致性和错误处理。结果上线后用户反馈"Android上能用的功能在iOS上闪退"，排查发现是iOS端没做空值判断。还有的团队把原生调用逻辑散落在各个业务页面里，没有统一封装，后来要升级第三方SDK（Software Development Kit）时，发现调用点有上百处，改了两个月才改完。这些教训都指向同一个问题：对混合开发的架构设计缺乏系统认知，对双端差异缺乏足够敬畏。

我是怕浪猫，一个在RN与原生之间反复横跳了多年的工程老兵。从最早的Bridge通信到如今的新架构JSI（JavaScript Interface），我经历了RN原生通信机制的整个演进过程。从最初手写Bridge模块踩坑无数，到后来用TurboModule享受类型安全的好处，再到为大型企业项目设计统一的原生服务封装层，我对混合开发的每一个环节都有切身体会。这一章我来系统讲解RN原生混合开发的全套方案，从通信原理到双端原生模块开发，从第三方库适配到差异化兼容处理，从调试排查到工程规范，帮你打通JS与原生之间的任督二脉。

## 12.1 混合开发架构与通信原理

### 12.1.1 纯RN与混合开发场景对比

先厘清两种开发模式的边界。纯RN指的是所有业务逻辑和UI（User Interface）渲染都在JS层完成，不直接编写原生代码。这种模式在工具类应用、内容展示类应用中够用，但一旦涉及系统级功能——相机、蓝牙、指纹、文件系统、推送通知——就必须跨入混合开发的领地。

混合开发的核心思路是：JS层负责业务逻辑和界面编排，原生层负责平台特有功能实现，两者通过通信机制协作。这种分工不是技术限制，而是工程智慧。JS层擅长快速迭代和跨端复用，原生层擅长系统级能力和极致性能。把擅长的事交给擅长的层来做，这是混合开发的本质。如果反过来用原生写业务逻辑、用JS做系统能力调用，不仅效率低下，而且维护成本会指数级增长。很多团队在混合开发中犯的根本错误就是没有理清这个分工边界，导致原生层塞满了本该在JS层处理的业务逻辑，JS层又充斥着各种原生调用的胶水代码，最终两头都乱。

来看两种模式的架构对比：

```
纯RN架构：
  JS业务代码 -> RN组件 -> 原生组件渲染
  （全部在JS层完成，不触碰原生代码）

混合开发架构：
  JS业务代码 -> Native Module -> 原生功能实现
       ^                              |
       |______ 回调/Promise __________|
  （JS与原生双向通信，协作完成功能）
```

哪些场景必须走混合开发？这里列一个清单：

- 调用系统硬件：相机、麦克风、传感器、蓝牙模块
- 生物识别：指纹认证、Face ID人脸识别
- 文件系统操作：读写本地文件、生成PDF（Portable Document Format）文档
- 推送通知与后台任务管理
- 第三方SDK集成：移动支付、社交登录、数据统计
- 性能敏感计算：图像处理、加密解密运算
- 平台差异化功能：Android的Intent分享机制、iOS的Share Sheet

> 混合开发不是"不得已而为之"，而是一种工程策略。好的架构师知道何时用JS写逻辑、何时把逻辑下沉到原生层。关键判断标准是：这个功能是否依赖平台特有能力、是否对性能有极致要求、是否需要操作底层硬件。三个条件满足任一个，就该走混合开发路线。不要为了"统一技术栈"而强求所有功能都用JS实现，那是对工程效率的背叛。

### 12.1.2 JS与原生双向通信底层原理

RN的JS与原生通信经历了两代架构。理解通信机制的演进，是掌握混合开发的前提，也是排查通信问题的基本功。

旧架构中，JS与原生通过Bridge通信。Bridge本质上是一个异步消息队列，JS把调用请求序列化为JSON（JavaScript Object Notation）消息发送到原生端，原生端处理后再把结果序列化为JSON回传。这个过程是异步的、有序列化开销的。每次调用都要经历"序列化-入队-出队-反序列化"四个步骤，当调用频率高或传输数据量大时，Bridge会成为性能瓶颈。

新架构引入了JSI（JavaScript Interface），用C++直接在JS引擎和原生层之间建立同步调用通道。JS可以直接持有原生C++对象的引用，调用原生方法就像调用普通JS函数一样，不需要经过Bridge的序列化。这是RN架构的一次根本性升级，通信效率从"消息传递"级别提升到了"函数调用"级别。

```
旧架构 Bridge 通信流程：
  JS调用 -> JSON序列化 -> Bridge队列 -> 原生解析 -> 执行 -> JSON序列化 -> 回调JS
  开销：两次序列化 + 队列调度

新架构 JSI 通信流程：
  JS调用 -> 直接调用C++对象方法 -> 原生执行 -> 同步返回结果
  开销：几乎零开销的函数调用
```

来看Bridge模式下一个原生调用的核心流程：

```js
// JS端调用原生方法
import { NativeModules } from 'react-native';
const { Calculator } = NativeModules;

// 调用原生Calculator模块的add方法
Calculator.add(1, 2, (result) => {
  console.log('计算结果:', result);
});
```

这段代码在Bridge架构下的执行路径是：JS引擎把`Calculator.add(1, 2, cb)`编码为一条消息，消息体包含模块名"Calculator"、方法名"add"、参数数组[1, 2]。这条消息被推入Bridge的消息队列，原生端的MessageQueue消费这条消息，找到名为Calculator的Java/ObjC类，调用其add方法，再把结果通过回调推回JS队列。整个过程涉及两次跨语言边界穿越，每次都伴随着序列化和反序列化。

JSI架构下，`Calculator`对象直接是一个C++对象代理，调用`add`方法时直接执行C++函数，整个过程同步完成，没有序列化开销。这就是新架构性能飞跃的根本原因。这也是为什么新架构下可以实现诸如Reanimated 3这样的高性能动画库——它通过JSI直接在UI线程操作原生视图，完全绕过了Bridge的异步通信限制。

> Bridge不是缺陷，是历史阶段的最优解。在JS引擎和原生运行时之间没有直接互操作能力的时代，消息队列加JSON序列化是唯一可行的跨语言通信方案。JSI的出现不是否定Bridge，而是技术演进到了可以做得更好的阶段。理解这一点，你才能理解为什么至今仍有很多RN项目还在用Bridge架构——不是它们不想升级，而是迁移成本和稳定性考量需要时间。技术选型从来不是选最新的，而是选最合适的。

### 12.1.3 原生模块加载与调用机制

原生模块在RN中有两种注册方式：自动注册和手动注册。在旧架构中，Android端通过`ReactPackage`注册模块，iOS端通过`RCT_EXPORT_MODULE`宏注册。新架构中推荐使用TurboModule（Turbo Native Module）注册方式，支持懒加载。

Android端原生模块注册流程：

```java
// 1. 创建原生Module类
public class MyModule extends ReactContextBaseJavaModule {
  @Override
  public String getName() { return "MyModule"; }

  @ReactMethod
  public void doSomething(String input, Callback callback) {
    callback.invoke("处理完成: " + input);
  }
}

// 2. 通过ReactPackage注册
public class MyAppPackage implements ReactPackage {
  @Override
  public List<NativeModule> createNativeModules(
      ReactApplicationContext ctx) {
    return Arrays.asList(new MyModule(ctx));
  }
}
```

iOS端原生模块注册流程：

```objc
// 1. 定义Module
@interface MyModule : NSObject <RCTBridgeModule>
@end

@implementation MyModule
RCT_EXPORT_MODULE();

RCT_EXPORT_METHOD(doSomething:(NSString *)input
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject) {
  resolve([NSString stringWithFormat:@"处理完成: %@", input]);
}
@end
```

原生模块加载的时机值得特别关注。Bridge架构下，所有通过ReactPackage注册的模块在应用启动时就会被实例化，即使你的JS代码从未调用过这个模块。这意味着如果注册了50个原生模块，启动时就创建了50个Java对象（或ObjC对象），每个对象都占用内存，初始化逻辑也都要执行一遍。这是旧架构启动慢的原因之一，也是很多团队在不了解原理的情况下注册了大量"可能用到"的模块导致启动时间劣化的根源。

JSI架构下的TurboModule支持懒加载，模块在JS首次调用时才被创建，这是新架构启动速度提升的关键设计之一。懒加载的好处不只是启动快，还降低了内存占用——没被调用的模块不会占用任何资源。

> 模块注册不是越多越好。每注册一个模块就增加一份启动开销和内存占用。在Bridge架构下，建议对非必要模块做按需注册或拆分到独立Bundle中延迟加载。在新架构下虽然TurboModule支持懒加载，但也要避免无意义的模块注册。工程上每一行代码都应该有存在的理由，"可能用到"不是理由。

### 12.1.4 混合开发核心优势与适配难点

混合开发的核心优势显而易见，主要体现在三个方面：

第一，能力扩展。RN组件库再丰富也覆盖不了所有系统能力，原生模块是打通系统能力的唯一通道。没有原生模块，RN应用就像被关在沙盒里，只能做页面展示和信息录入，无法触达设备的底层能力。

第二，性能优化。计算密集型任务交给原生执行，避免JS线程阻塞。比如图片处理可以用C++在原生层完成，结果回传JS。在处理大数组排序、复杂加密运算、图像滤镜等场景下，原生执行效率比JS高一到两个数量级。

第三，生态复用。Android和iOS各自有庞大的原生开源生态，通过原生模块封装，可以直接复用这些成熟方案。比如Android的Glide图片加载库、iOS的SDWebImage，都是经过亿级用户验证的方案，没必要在JS层重新造轮子。

但适配难点同样真实存在，主要体现在以下四个维度：

**双端不一致**：Android和iOS的原生API（Application Programming Interface）设计差异大，同一个功能双端的实现方式可能完全不同。比如文件系统，Android用java.io.File，iOS用NSFileManager，参数和返回结构都不一样。再比如获取设备唯一标识，Android需要处理多种方案（ANDROID_ID、IMEI、UUID），iOS从iOS 5之后就只能用UUID。

**版本碎片化**：Android有API Level差异（最低支持版本到最新版本跨度大），iOS有系统版本差异，同一个原生API在不同版本上的行为可能不同。Android的碎片化尤其严重，同一个权限模型在API Level 23前后完全不同，存储权限在API Level 29前后也有重大变化。

**构建复杂度**：引入原生代码后，构建链从纯JS变成了JS加Gradle加Xcode，编译时间增长，构建出错排查链路变长。CI/CD（Continuous Integration / Continuous Deployment）流水线也需要分别配置Android和iOS的构建步骤，维护成本显著增加。

**调试门槛高**：原生层崩溃栈跟JS层调试完全不同，Android需要看Logcat，iOS需要看Xcode Console，两者还需要交叉分析。当问题出现在JS与原生的通信边界上时，需要同时理解JS和原生代码才能定位，这对开发者的全栈能力提出了很高要求。

### 12.1.5 企业混合项目落地场景分析

企业项目中混合开发不是"要不要做"的问题，而是"怎么做才不乱"的问题。我总结过一套落地原则，这里分享核心决策框架：

| 场景 | 是否走原生 | 原因 |
|------|-----------|------|
| UI组件渲染 | 否 | RN组件已足够 |
| 网络请求 | 否 | JS层Fetch/Axios足够 |
| 相机/相册 | 是 | 系统能力，需原生 |
| 推送通知 | 是 | 平台特有机制 |
| 支付SDK | 是 | 第三方原生SDK |
| 生物识别 | 是 | 硬件能力 |
| 数据加密 | 视情况 | 简单加密JS够用，高强度算法走原生 |
| 动画 | 视情况 | 简单动画JS够用，复杂动画走原生驱动 |

> 企业级混合项目的核心原则是"能JS不原生，该原生不犹豫"。判断标准就一条：这个功能的实现是否依赖JS运行时之外的东西。如果依赖系统API、硬件、第三方SDK，就果断走原生模块；如果不依赖，就在JS层完成。混着做不难，难的是划清边界。边界一旦划清，团队协作就有了明确分工：前端工程师专注JS层业务逻辑，原生工程师专注原生能力封装，各司其职，互不干扰。

## 12.2 Android原生模块开发与JS调用

### 12.2.1 Android原生项目结构认知

打开RN项目中的android目录，你会看到标准的Android工程结构。理解这个结构是开发Android原生模块的基础，很多编译报错其实就是对工程结构不熟悉导致的。

```
android/
├── app/
│   ├── build.gradle          # 应用级构建配置
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/.../   # Java/Kotlin源码
│   │   │   ├── AndroidManifest.xml  # 清单文件
│   │   │   ├── res/            # 资源文件
│   │   │   └── assets/         # 资产文件
├── build.gradle              # 项目级构建配置
├── settings.gradle          # 项目设置
└── gradle.properties        # Gradle属性
```

关键文件说明：

`AndroidManifest.xml`：应用的清单文件，声明权限、组件、元数据。开发原生模块时如果需要系统权限，必须在这里声明。这个文件还声明了应用的最低SDK版本和目标SDK版本，影响权限模型和行为差异。

`build.gradle (app)`：应用级别的Gradle构建文件，配置依赖、SDK版本、签名等。引入第三方原生库时通常需要在这里添加依赖。这个文件中的`minSdkVersion`决定了你需要兼容的最低Android版本，直接影响权限处理策略。

`MainApplication.java`：应用入口类，RN的初始化在这里完成。旧架构中ReactPackage列表在这里配置，新架构中通过autolinking自动处理。理解这个文件的初始化流程对于排查RN启动相关问题至关重要。

### 12.2.2 自定义Android原生Module创建

来看一个完整的Android原生模块创建流程。以"获取设备电池信息"为例，这个功能JS层无法直接实现，必须走原生。

第一步，创建Module类。这个类需要继承`ReactContextBaseJavaModule`，并实现`getName()`方法返回模块名：

```java
package com.myapp;

import com.facebook.react.bridge.*;
import android.content.Intent;
import android.os.BatteryManager;

public class BatteryModule extends ReactContextBaseJavaModule {
  private static final String TAG = "BatteryModule";

  public BatteryModule(ReactApplicationContext ctx) {
    super(ctx);
  }

  @Override
  public String getName() {
    return "BatteryModule";
  }
}
```

`ReactContextBaseJavaModule`是RN提供的基础类，继承它你的Module才能被RN识别。`getName()`返回的字符串就是JS端通过`NativeModules`访问时使用的模块名，必须确保唯一性，不同模块不能重名。

第二步，添加被JS调用的方法。用`@ReactMethod`注解标记的方法才会暴露给JS层：

```java
@ReactMethod
public void getBatteryLevel(Callback callback) {
  Intent intent = getReactApplicationContext()
    .registerReceiver(null, 
      new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
  int level = intent.getIntExtra(
    BatteryManager.EXTRA_LEVEL, -1);
  int scale = intent.getIntExtra(
    BatteryManager.EXTRA_SCALE, -1);
  float batteryPct = level * 100f / scale;
  callback.invoke(batteryPct);
}
```

注意`@ReactMethod`注解只能用在返回类型为void的方法上，数据返回通过Callback或Promise完成。这是RN的设计约定，因为Bridge通信是异步的，方法调用本身不等待结果返回。

第三步，创建Package类注册Module，让RN知道这个Module的存在：

```java
package com.myapp;

import com.facebook.react.ReactPackage;
import com.facebook.react.bridge.*;
import java.util.*;

public class MyAppPackage implements ReactPackage {
  @Override
  public List<NativeModule> createNativeModules(
      ReactApplicationContext ctx) {
    List<NativeModule> modules = new ArrayList<>();
    modules.add(new BatteryModule(ctx));
    return modules;
  }

  @Override
  public List<ViewManager> createViewManagers(
      ReactApplicationContext ctx) {
    return Collections.emptyList();
  }
}
```

第四步，在MainApplication中注册Package，把自定义的Package加入到RN的Package列表中：

```java
@Override
protected List<ReactPackage> getPackages() {
  return Arrays.asList(
    new MainReactPackage(),
    new MyAppPackage()  // 添加自定义Package
  );
}
```

如果使用RN 0.60以上版本的autolinking机制，第三方库的Package会自动注册，但你自己写的Module仍然需要手动注册到`getPackages()`中。这是很多新手容易遗漏的步骤——Module写好了，Package也创建了，但忘记在MainApplication中注册，结果JS端调用时报Module不存在。

### 12.2.3 RN JS调用Android原生方法

JS端调用原生模块有三种方式：直接调用（Callback方式）、Promise调用、事件发送。来看每种方式的核心代码和适用场景。

直接调用（Callback方式）适合一次性返回结果的场景：

```js
import { NativeModules } from 'react-native';
const { BatteryModule } = NativeModules;

BatteryModule.getBatteryLevel((level) => {
  console.log('电池电量:', level + '%');
});
```

Promise方式是推荐的做法，配合async/await可以让异步代码像同步代码一样清晰：

```java
// Android端使用Promise
@ReactMethod
public void getBatteryLevelPromise(
    Promise promise) {
  try {
    // ...获取电池电量逻辑...
    promise.resolve(batteryPct);
  } catch (Exception e) {
    promise.reject("BATTERY_ERROR", e);
  }
}
```

```js
// JS端用async/await
const level = await BatteryModule
  .getBatteryLevelPromise();
console.log('电池电量:', level + '%');
```

> Promise方式比Callback方式更优雅，也更符合现代JS的编程习惯。但Callback方式在某些需要多次回调的场景下仍然有用，比如进度更新、分批数据返回。选择标准是：一次性结果用Promise，多次回调用Callback或事件。不要为了"先进"而Promise化所有方法，技术选择服务于实际需求，而不是反过来。

### 12.2.4 原生异步回调数据至JS层

原生层向JS发送数据不限于方法返回值，还包括主动推送的事件。这在"原生检测到某个状态变化、通知JS更新UI"的场景中非常常见。比如电池电量变化、网络状态切换、蓝牙设备连接状态变更，都是原生主动通知JS的典型场景。

Android端发送事件需要使用`DeviceEventManagerModule`：

```java
import com.facebook.react.modules.core.DeviceEventManagerModule;

private void sendEvent(
    ReactApplicationContext ctx,
    String eventName,
    @Nullable WritableMap params) {
  ctx.getJSModule(
    DeviceEventManagerModule.RCTDeviceEventEmitter.class)
    .emit(eventName, params);
}

// 监听电量变化
private BroadcastReceiver batteryReceiver = 
  new BroadcastReceiver() {
    @Override
    public void onReceive(Context context, Intent intent) {
      WritableMap params = Arguments.createMap();
      params.putDouble("level", getBatteryLevel());
      sendEvent(getReactApplicationContext(),
        "BatteryChanged", params);
    }
  };
```

JS端通过`DeviceEventEmitter`接收事件：

```js
import {
  NativeModules,
  DeviceEventEmitter
} from 'react-native';
const { BatteryModule } = NativeModules;

import { useEffect } from 'react';

useEffect(() => {
  const sub = DeviceEventEmitter
    .addListener('BatteryChanged', (event) => {
      console.log('电量变化:', event.level);
    });
  return () => sub.remove();
}, []);
```

事件通信有一个关键注意点：JS端必须在`useEffect`清理函数中移除监听，否则组件卸载后仍在接收事件会导致内存泄漏和"setState on unmounted component"警告。这是混合项目中最常见的泄漏来源之一，也是代码审查时需要重点检查的项。养成"有addListener就有remove"的肌肉记忆，能避免大量诡异Bug。除了事件监听，BroadcastReceiver和ContentObserver等原生组件也需要在生命周期结束时注销，否则同样会造成泄漏。在封装原生模块时，建议提供统一的生命周期管理方法，让JS层可以在组件挂载和卸载时显式调用start和stop，把资源管理的责任明确化。

### 12.2.5 Android原生权限适配处理

调用系统功能离不开权限申请。Android的权限模型从6.0（API Level 23）开始引入运行时权限机制，在`AndroidManifest.xml`中声明权限只是第一步，还需要在代码中动态请求用户授权。这两步缺一不可：只声明不请求，运行时报权限拒绝；只请求不声明，系统根本不知道你的应用需要这个权限。

权限声明在`AndroidManifest.xml`中：

```xml
<uses-permission 
  android:name="android.permission.CAMERA" />
<uses-permission 
  android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

原生层权限检查和请求：

```java
@ReactMethod
public void checkCameraPermission(Promise promise) {
  int result = ContextCompat.checkSelfPermission(
    getCurrentActivity(),
    Manifest.permission.CAMERA);
  boolean granted = result == 
    PackageManager.PERMISSION_GRANTED;
  promise.resolve(granted);
}

@ReactMethod
public void requestCameraPermission(Promise promise) {
  Activity activity = getCurrentActivity();
  if (activity == null) {
    promise.reject("NO_ACTIVITY", "Activity is null");
    return;
  }
  // 实际项目中用ActivityResultContracts
  // 或PermissionsCallback处理
  promise.resolve(true);
}
```

JS层封装统一的权限请求流程，让业务代码不直接接触原生权限细节：

```js
async function ensureCameraPermission() {
  const granted = await BatteryModule
    .checkCameraPermission();
  if (granted) return true;
  
  const result = await BatteryModule
    .requestCameraPermission();
  return result;
}

// 使用
const canUseCamera = await ensureCameraPermission();
if (canUseCamera) {
  // 打开相机
} else {
  Alert.alert('提示', '需要相机权限才能使用此功能');
}
```

> 权限适配的核心原则是"永远不要假设权限已授予"。每次调用需要权限的功能前都要检查，拒绝后要给出明确提示和引导。用户拒绝权限不代表你的应用出Bug了，这是正常交互流程的一部分。处理好"拒绝-引导-重试"链路，是原生权限适配的及格线。很多应用商店审核被拒就是因为权限拒绝后没有给用户明确提示，用户以为是应用崩溃了。在体验上，"功能不可用+明确提示"永远优于"功能不可用+无任何反馈"。

## 12.3 iOS原生模块开发与JS调用

### 12.3.1 iOS原生项目结构与配置解析

打开RN项目中的ios目录，你会看到标准的Xcode工程结构：

```
ios/
├── MyApp.xcodeproj        # Xcode工程文件
├── MyApp/
│   ├── AppDelegate.h      # 应用代理头文件
│   ├── AppDelegate.mm     # 应用代理实现
│   ├── Info.plist         # 应用配置文件
│   ├── Images.xcassets/   # 图片资源
│   └── Pods/              # CocoaPods依赖
├── Podfile               # CocoaPods配置
└── Podfile.lock          # 依赖锁定文件
```

几个关键文件的作用需要详细说明：

`AppDelegate.mm`（或.m）：应用生命周期入口，RN的根视图在这里初始化。新架构（New Architecture）的启动配置也在这里完成。理解这个文件对于排查RN启动失败、白屏等问题至关重要。如果你需要自定义RN的启动行为（比如修改rootView的配置、添加本地通知处理），都要改这个文件。

`Info.plist`：iOS应用的配置中心，包含权限说明文本、URL Scheme、支持的屏幕方向等。iOS权限说明文本（Privacy Description）是App Store审核必查项，缺失会被直接拒审。每个需要权限的功能都必须在Info.plist中配置对应的说明文本，比如使用相机需要添加`NSCameraUsageDescription`，使用相册需要添加`NSPhotoLibraryUsageDescription`。这些文本会展示给用户看，写得不清楚也会影响审核通过率。

`Podfile`：CocoaPods依赖管理文件，类似Android的build.gradle dependencies块。引入第三方原生库后需要在这里配置依赖。Podfile的语法和配置选项直接影响iOS构建的正确性，比如最低部署版本、framework链接方式等都在这里控制。

### 12.3.2 自定义iOS原生模块创建

以"获取设备UUID（Universally Unique Identifier）"为例，来看iOS原生模块的完整创建流程。UUID在iOS中是设备唯一标识的基础，JS层无法直接获取，必须通过原生模块。

创建Module头文件和实现文件：

```objc
// DeviceInfoModule.h
#import <React/RCTBridgeModule.h>

@interface DeviceInfoModule : NSObject <RCTBridgeModule>
@end

// DeviceInfoModule.m
#import "DeviceInfoModule.h"

@implementation DeviceInfoModule

RCT_EXPORT_MODULE();

RCT_EXPORT_METHOD(getUUID:
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)
{
  NSString *uuid = [[NSUUID UUID] 
    UUIDString];
  resolve(uuid);
}

@end
```

`RCT_EXPORT_MODULE()`宏注册模块名，默认使用类名（去掉前缀的）。`RCT_EXPORT_METHOD`宏暴露方法给JS调用。这两个宏是RN iOS原生模块开发的入口，所有原生模块都从这里开始。

> iOS原生模块开发中宏的作用是隐藏Objective-C runtime的复杂性。`RCT_EXPORT_MODULE`底层做的事是向RN的模块注册表注册这个类的信息，`RCT_EXPORT_METHOD`底层做的事是把方法签名记录到一个方法表中，供JS调用时查表。理解了这一点，你就理解了RN iOS原生模块的全部魔法。不要被宏吓到，它们本质上是代码生成器，把繁琐的注册逻辑简化成一行代码。理解了宏的底层原理，你在遇到编译报错时就能快速定位问题——很多iOS原生模块的编译错误都跟宏的使用不当有关，比如宏后面多了分号、宏放在了错误的文件位置等。

### 12.3.3 RN调用iOS原生方法实战

JS端调用iOS原生模块的方式与Android完全一致，这体现了RN"双端一致性"的设计哲学，也是RN跨端开发的核心价值所在：

```js
import { NativeModules } from 'react-native';
const { DeviceInfoModule } = NativeModules;

async function getDeviceUUID() {
  try {
    const uuid = await DeviceInfoModule.getUUID();
    console.log('设备UUID:', uuid);
    return uuid;
  } catch (error) {
    console.error('获取UUID失败:', error);
    return null;
  }
}
```

这就是混合开发的理想状态：JS层代码不关心底层是Android还是iOS，统一通过`NativeModules`调用，原生层各自实现。但现实中往往做不到完全一致，因为平台差异客观存在。比如获取设备唯一标识，Android可能返回ANDROID_ID或自定义UUID，iOS返回的是NSUUID生成的字符串，格式和含义都不同。再比如调用相机时，Android需要处理Camera2 API和CameraX的版本兼容，iOS需要处理AVFoundation的权限请求流程。后面会讲如何通过统一封装抹平这些差异，让业务层调用时完全不感知底层平台的差异。

### 12.3.4 iOS原生异步回调JS数据

iOS原生模块同样支持Callback和Promise两种回调方式，此外还支持事件发送机制。事件发送在iOS端的实现与Android有所不同，需要继承`RCTEventEmitter`类。

使用Promise（推荐方式）：

```objc
RCT_EXPORT_METHOD(getSystemInfo:
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)
{
  NSDictionary *info = @{
    @"systemName": [[UIDevice currentDevice] systemName],
    @"systemVersion": [[UIDevice currentDevice] systemVersion],
    @"model": [[UIDevice currentDevice] model]
  };
  resolve(info);
}
```

使用事件发送，需要将模块继承自`RCTEventEmitter`：

```objc
// DeviceInfoModule.m
#import <React/RCTEventEmitter.h>

@interface DeviceInfoModule : 
    RCTEventEmitter <RCTBridgeModule>
@end

@implementation DeviceInfoModule {
  BOOL hasListeners;
}

- (NSArray<NSString *> *)supportedEvents {
  return @[@"DeviceInfoChanged"];
}

- (void)startObserving {
  hasListeners = YES;
}

- (void)stopObserving {
  hasListeners = NO;
}

- (void)notifyChange:(NSDictionary *)info {
  if (hasListeners) {
    [self sendEventWithName:@"DeviceInfoChanged"
                       body:info];
  }
}
```

JS端通过`NativeEventEmitter`接收事件：

```js
import {
  NativeEventEmitter,
  NativeModules
} from 'react-native';

const eventEmitter = new NativeEventEmitter(
  NativeModules.DeviceInfoModule
);

useEffect(() => {
  const sub = eventEmitter.addListener(
    'DeviceInfoChanged',
    (info) => {
      console.log('设备信息变化:', info);
    }
  );
  return () => sub.remove();
}, []);
```

> iOS事件模块需要继承`RCTEventEmitter`而非直接实现`RCTBridgeModule`协议，这是因为事件发送需要额外的观察者生命周期管理。`startObserving`和`stopObserving`分别在JS端开始监听和移除监听时调用，通过`hasListeners`标志位避免无监听者时的事件发送。这种设计体现了RN对资源管理的谨慎态度——没有监听者就不发事件，避免无意义的内存分配和CPU消耗。Android端没有这种机制，但你在实际开发中也可以自己在原生层实现类似的标志位控制。

### 12.3.5 iOS编译报错与兼容修复

iOS原生模块开发中最常遇到的编译报错集中在以下几个方面，这里逐个分析原因和解决方案。

**报错一：RCTBridgeModule头文件找不到**

```
'React/RCTBridgeModule.h' file not found
```

原因：CocoaPods依赖未正确安装，或Header Search Path配置缺失。这是最常见的新手报错，通常出现在clone项目后第一次编译或更新依赖之后。解决方案：

```bash
# 在ios目录下执行
cd ios && pod install
```

如果pod install后仍报错，检查Podfile中是否包含了React依赖。RN 0.60以上版本使用autolinking，通常Podfile会自动生成React依赖配置。如果Podfile内容不正确，可能需要清理后重新安装：

```bash
# 清理CocoaPods缓存
pod deintegrate
pod cache clean --all
pod install
```

**报错二：Use of undeclared identifier 'RCT_EXPORT_METHOD'**

原因：Module实现文件缺少头文件导入。在.m文件顶部确保正确导入了React的桥接模块头文件：

```objc
#import <React/RCTBridgeModule.h>
```

**报错三：New Architecture下TurboModule编译失败**

原因：新架构对Module的要求不同，TurboModule需要通过代码生成（Codegen）步骤生成类型安全的C++接口。这是新架构迁移中最容易踩的坑。确保在Podfile中正确启用了新架构：

```ruby
# Podfile
install! 'cocoapods', 
  :deterministic_uuids => false

target 'MyApp' do
  use_react_native!(
    :path => "../node_modules/react-native",
    :app_path => "../node_modules/react-native/..",
    :fabric_enabled => true,
    :new_arch_enabled => true
  )
end
```

启用新架构后需要重新执行`pod install`，Codegen会自动生成所需的接口文件。如果Codegen失败，尝试清理DerivedData目录后重试：

```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/
cd ios && pod install
```

## 12.4 第三方原生库集成与适配

### 12.4.1 原生库自动Link适配流程

RN 0.60版本引入了autolinking机制，第三方原生库的链接基本全自动了。但"基本自动"不等于"完全无脑"，踩坑场景仍然存在。

autolinking的工作原理：在安装第三方库后，RN的CLI（Command Line Interface）工具会扫描`node_modules`中所有包的`package.json`，检查是否有原生代码目录（android/ios），自动把原生依赖注册到各自的构建系统中。这个机制省去了手动执行`react-native link`的步骤，大幅降低了集成成本。

Android端autolinking完成后，会自动配置三个部分：settings.gradle中的include路径、build.gradle中的project依赖、MainApplication中的ReactPackage注册。iOS端则是通过CocoaPods的autolinking机制，自动读取node_modules中的podspec文件。

```bash
# 安装第三方库
npm install react-native-permissions

# Android端自动配置，无需手动操作

# iOS端需要执行pod install
cd ios && pod install
```

自动Link成功的标志是Android和iOS分别能正常编译。如果安装库后编译失败，通常需要检查autolinking是否正确执行。常见的问题是iOS端忘记执行`pod install`，或者Android端构建缓存需要清理。

### 12.4.2 双端手动原生依赖适配方案

有些库不支持autolinking，或者需要手动配置原生依赖。这种情况在接入企业内部SDK、定制化原生模块时很常见。私有SDK通常没有发布到npm，也没有标准的podspec/gradle配置，需要手动集成。

Android手动配置：

```gradle
// settings.gradle
include ':react-native-custom-module'
project(':react-native-custom-module').projectDir = 
  new File(rootProject.projectDir, 
    '../node_modules/react-native-custom-module/android')

// app/build.gradle
dependencies {
  implementation project(':react-native-custom-module')
}
```

```java
// MainApplication.java
@Override
protected List<ReactPackage> getPackages() {
  return Arrays.asList(
    new MainReactPackage(),
    new CustomModulePackage()  // 手动添加
  );
}
```

iOS手动配置，在Podfile中手动添加依赖：

```ruby
target 'MyApp' do
  use_react_native!

  pod 'CustomModule', 
    :path => '../node_modules/react-native-custom-module'
  
  # 非node_modules中的内部SDK
  pod 'InternalSDK', 
    :path => '../native-sdk/ios/InternalSDK'
end
```

> 手动Link和自动Link的核心区别在于维护成本。自动Link由CLI工具维护，升级RN版本时不需要手动同步。手动Link如果配置散落在多处，后续维护和升级时容易遗漏。建议能走autolinking的都走，手动配置仅用于不支持autolinking的库或内部私有SDK。对于私有SDK，建议自己写一个符合规范的package.json和podspec，让它也能享受autolinking的便利。前期多花一小时写配置文件，后期每次升级省一天。

### 12.4.3 版本冲突与依赖兼容解决

原生库集成中最头疼的问题是版本冲突。Android的Gradle依赖冲突和iOS的CocoaPods版本冲突表现不同，但根因类似——多个库依赖了同一个底层库的不同版本。

**Android版本冲突**：

常见场景：库A依赖`androidx.core:core:1.6.0`，库B依赖`androidx.core:core:1.8.0`。Gradle默认使用最高版本策略，但如果版本跨度大（如support库到AndroidX的迁移），可能编译报错。典型的报错信息是"Duplicate class"或"Dependency resolution failed"。

解决方案：

```gradle
// app/build.gradle
android {
  configurations.all {
    resolutionStrategy {
      force 'androidx.core:core:1.8.0'
      force 'com.google.android.gms:play-services-base:18.0.1'
    }
  }
}
```

**iOS版本冲突**：

常见场景：两个库依赖不同版本的同一个pod，CocoaPods提示版本冲突。报错信息通常是"There are multiple dependencies with different sources for xxx"或"version conflict"。

解决方案：

```ruby
# Podfile中统一指定版本
pod 'GoogleUtilities', '7.10.0'

# 或者允许版本浮动
pod 'GoogleUtilities', '~> 7.10'
```

冲突无法解决时的最终方案：检查库之间的兼容性矩阵，通常库的README或CHANGELOG会标明支持的RN版本和依赖版本。如果库长期不维护，考虑fork修改或寻找替代方案。在选择第三方库时，优先选择维护活跃、版本更新及时的库，能减少大量后续维护成本。一个长期不维护的库可能存在安全漏洞、兼容性问题或废弃API依赖，在发现时往往已经来不及了。我建议团队建立一份"依赖库健康度清单"，定期检查核心依赖库的GitHub活跃度、issue处理速度和兼容性状态，提前发现风险并规划替代方案。

### 12.4.4 大型原生库集成规范流程

大型原生库（如地图SDK、即时通讯SDK、支付SDK）的集成不只是安装依赖，还需要初始化配置、权限申请、ProGuard/GCC配置等。这类库的集成如果缺乏规范，很容易出错且难以排查。我总结了一套标准流程，经过多个企业项目验证：

```
大型原生库集成六步法：

1. 需求分析：确认需要用到库的哪些功能模块
2. 依赖安装：npm/pod/gradle三端依赖
3. 权限配置：Android Manifest + iOS Info.plist
4. 初始化：Application层或入口模块统一初始化
5. 模块封装：JS层统一封装，抹平平台差异
6. 验证测试：双端真机验证关键功能链路
```

以接入地图SDK为例，初始化配置的统一封装需要注意API Key的双端差异处理：

```js
// MapSDKManager.js
import { NativeModules, Platform } from 'react-native';
const { AMapModule } = NativeModules;

class MapSDKManager {
  constructor() {
    this.initialized = false;
  }

  async init(apiKeyAndroid, apiKeyIOS) {
    const key = Platform.OS === 'android' 
      ? apiKeyAndroid : apiKeyIOS;
    await AMapModule.initSDK(key);
    this.initialized = true;
  }

  isReady() {
    return this.initialized;
  }
}

export default new MapSDKManager();
```

初始化时机选择是关键。过早初始化会增加启动时间，过晚初始化会导致用户操作时功能不可用。建议策略是：在应用启动后、首页渲染前完成初始化，但用异步方式不阻塞UI。可以借助Splash Screen的展示时间来完成SDK初始化，让用户感知不到等待。

### 12.4.5 原生库升级与迭代兼容方案

原生库升级是企业项目维护中绕不开的环节。RN版本升级、原生库安全补丁、新功能需求都会触发库的升级。升级的核心风险在于：新版本可能不兼容旧版本API，或者新版本的最低系统要求提升，导致部分用户无法使用。

升级前检查清单：

| 检查项 | 方法 |
|--------|------|
| 兼容RN版本 | 查看库的package.json peerDependencies |
| 最低系统版本 | 查看库的README和CHANGELOG |
| Breaking Changes | 查看CHANGELOG中的BREAKING CHANGES段 |
| 依赖冲突 | 升级后在模拟器试编译双端 |
| API变化 | 对比新旧版本的TypeScript类型定义 |

升级操作流程：

```bash
# 1. 查看当前版本
npm list react-native-permissions

# 2. 查看可用版本
npm view react-native-permissions versions

# 3. 升级到指定版本
npm install react-native-permissions@4.1.0

# 4. iOS重新安装pod
cd ios && pod install

# 5. 清理构建缓存
cd android && ./gradlew clean
# iOS: Xcode -> Product -> Clean Build Folder

# 6. 双端编译验证
npx react-native run-android
npx react-native run-ios
```

> 升级原则：不要追最新版本，追最稳定版本。生产项目的库版本选择应该以"社区验证程度"为标准，而不是"发布时间"为标准。一个发布三个月、有大量issue报告的版本，不如一个发布一年、社区反馈稳定的版本。生产环境不是试新版的试验田。每次升级前务必在开发分支验证完整功能链路，确认无误后再合并到主分支。升级时保留旧版本的package.json和lock文件，出问题时可以快速回退。

## 12.5 双端差异化兼容与适配处理

### 12.5.1 Android与iOS系统特性差异梳理

做混合开发必须建立一份系统差异地图。不是所有差异都需要处理，但你需要知道差异在哪里，才能在编码时有意识地规避。很多Bug的根因就是开发者不知道双端有差异，用一端的经验去写另一端的代码。

| 特性 | Android | iOS |
|------|---------|-----|
| 文件系统 | 开放存储，需权限 | 沙盒隔离 |
| 推送服务 | FCM（Firebase Cloud Messaging） | APNs（Apple Push Notification service） |
| 生物识别 | Fingerprint/Face | Touch ID/Face ID |
| 分享机制 | Intent系统 | UIActivityViewController |
| 导航转场 | Activity/Fragment | Navigation Controller |
| 状态栏控制 | SystemUiVisibility | StatusBarManager |
| 安全区域 | fitsSystemWindows | SafeAreaLayout |
| 深度链接 | Intent Filter + URL Scheme | URL Scheme + Universal Links |
| 权限模型 | 运行时动态申请 | Info.plist声明+首次使用弹窗 |
| 后台机制 | 前台服务/WorkManager | 后台任务严格限制 |

这张表不是要背下来，而是在开发某个功能时，先想一下这个功能在双端的实现方式是否一致。如果一致，JS层统一处理；如果不一致，需要双端分别实现再统一封装。建立这种"差异意识"是混合开发工程师的基本素养。每当你打算用一套代码处理某个功能时，先停三十秒问自己：这个功能在双端的实现方式真的完全一样吗？如果不确定，查一下双端官方文档的API设计，确认行为一致后再写代码。这个习惯能帮你避免大量的事后调试时间，也能让你的代码更加健壮。

### 12.5.2 平台判断与差异化代码编写

RN提供了`Platform`API（Application Programming Interface）来做平台判断，这是处理差异化的基础工具。用好这个API可以让差异代码清晰可控。

基础平台判断：

```js
import { Platform } from 'react-native';

// 方式一：Platform.OS
if (Platform.OS === 'ios') {
  // iOS专属逻辑
} else if (Platform.OS === 'android') {
  // Android专属逻辑
}

// 方式二：Platform.select
const styles = Platform.select({
  ios: { shadowOpacity: 0.2, shadowRadius: 4 },
  android: { elevation: 4 },
  default: {}
});

// 方式三：Platform.select传函数
const result = Platform.select({
  ios: () => doIOSLogic(),
  android: () => doAndroidLogic(),
})();
```

文件级平台差异（.android.js / .ios.js）：

RN的打包工具Metro支持按平台后缀自动选择文件。这种方式适合差异化代码量较大的场景，能让每个平台的代码独立清晰：

```
utils/
├── share.js          # 通用逻辑
├── share.android.js  # Android专属分享实现
├── share.ios.js      # iOS专属分享实现
└── index.js          # 统一导出
```

```js
// index.js
import share from './share';
export default share;

// 使用时
import share from './utils';
share({ text: '分享内容', url: 'https://example.com' });
// Metro会自动根据当前平台加载对应的文件
```

> Platform.select适合处理样式差异和小逻辑差异，文件级拆分适合处理大块逻辑差异。选择标准是：如果差异化代码不超过10行，用Platform.select；如果超过10行或有独立完整的逻辑流，用文件级拆分。别让一个文件里塞满if-else平台判断，那会让代码可读性急剧下降。好的代码组织方式是让每个文件只做一件事，平台差异代码也不例外。

### 12.5.3 双端样式与交互适配方案

样式差异是双端适配中最高频的工作。以下是几个常见的样式适配痛点及解决方案。

**安全区域适配**：

Android的导航栏和状态栏区域与iOS的Safe Area概念不同。iOS从iPhone X开始有刘海屏，顶部和底部都需要留出安全区域。Android的情况更复杂，不同厂商的全面屏手势区域高度不同，需要用`StatusBar.currentHeight`动态获取：

```js
import { SafeAreaView, Platform, StatusBar } from 'react-native';

function MyScreen() {
  return (
    <SafeAreaView 
      style={{ flex: 1, 
        paddingTop: Platform.OS === 'android' 
          ? StatusBar.currentHeight : 0 
      }}
    >
      <Text>内容区域</Text>
    </SafeAreaView>
  );
}
```

**阴影效果适配**：

Android不支持box-shadow，需要用elevation替代。这是最经典的样式差异之一，几乎所有涉及卡片设计的页面都要处理：

```js
const cardStyle = Platform.select({
  ios: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  android: {
    elevation: 3,
  },
  default: {},
});
```

**手势交互差异**：

iOS的边缘滑动返回手势是系统内置的，用户从屏幕左边缘右滑即可返回上一页。Android需要手动实现，或者依赖React Navigation提供的 gestureEnabled 配置。如果你的页面有特殊的手势冲突（比如横向滑动与边缘返回冲突），需要双端分别处理。通常的做法是在Android端禁用特定的手势冲突，或者在iOS端调整手势优先级。

### 12.5.4 系统版本兼容降级处理

系统版本差异是不可忽视的适配维度。Android有API Level碎片化问题（最低支持版本到最新版本跨度大），iOS相对集中但仍有旧版本用户存在。版本兼容处理不当会导致部分用户无法使用功能甚至应用崩溃。

获取系统版本：

```js
import { Platform } from 'react-native';

// 获取系统版本
const systemVersion = Platform.Version;
// Android: 返回数字（如 33 表示 API Level 33）
// iOS: 返回字符串（如 "16.4"）

const isAndroid13Plus = Platform.OS === 'android' 
  && Platform.Version >= 33;
const isiOS16Plus = Platform.OS === 'ios' 
  && parseFloat(Platform.Version) >= 16;
```

降级处理策略的核心是"功能可用优先"——新版本用新API提升体验，旧版本用兼容方案保证功能可用：

```js
function useAdaptiveFeature() {
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    if (Platform.OS === 'ios' 
        && parseFloat(Platform.Version) >= 16) {
      // iOS 16+使用新API
      setSupported(true);
    } else if (Platform.OS === 'android' 
        && Platform.Version >= 33) {
      // Android 13+使用新API
      setSupported(true);
    } else {
      // 旧版本降级到兼容方案
      setSupported(false);
    }
  }, []);

  return supported;
}
```

> 降级策略的核心思想是"渐进增强"。基础功能在所有版本上可用，高级功能在新版本上启用，旧版本用兼容方案兜底。不要为了用新API而用新API，要看这个API是否解决了实际工程问题。一个功能在旧版本上也能用，只是体验差一点，那就让它差一点。完美的降级不是让旧版本拥有新版本的能力，而是让旧版本的用户不觉得自己被遗忘了。在产品层面，功能可用性永远优先于体验完美度。

### 12.5.5 差异化功能统一封装规范

处理好平台差异的最佳实践是"对外统一接口，对内分平台实现"。这里给一套可落地的封装规范模板，经过多个项目验证，能显著降低混合开发的维护成本：

```js
// NativeService/index.js
import { Platform } from 'react-native';

let impl;

if (Platform.OS === 'ios') {
  impl = require('./ios').default;
} else {
  impl = require('./android').default;
}

// 统一接口
export const NativeService = {
  getDeviceId: () => impl.getDeviceId(),
  requestPermission: (perm) => impl.requestPermission(perm),
  shareContent: (data) => impl.shareContent(data),
  openSettings: () => impl.openSettings(),
};
```

```js
// NativeService/android.js
import { NativeModules } from 'react-native';
const { AndroidService } = NativeModules;

export default {
  getDeviceId() {
    return AndroidService.getDeviceId();
  },
  async requestPermission(perm) {
    return AndroidService.requestPermission(perm);
  },
  shareContent(data) {
    return AndroidService.shareViaIntent(data);
  },
  openSettings() {
    AndroidService.openAppSettings();
  },
};
```

```js
// NativeService/ios.js
import { NativeModules } from 'react-native';
const { IOSService } = NativeModules;

export default {
  getDeviceId() {
    return IOSService.getUUID();
  },
  async requestPermission(perm) {
    return IOSService.requestPermission(perm);
  },
  shareContent(data) {
    return IOSService.shareViaActivity(data);
  },
  openSettings() {
    IOSService.openAppSettings();
  },
};
```

业务层调用时完全不感知平台差异，代码干净整洁：

```js
import { NativeService } from './NativeService';

const deviceId = await NativeService.getDeviceId();
await NativeService.requestPermission('camera');
NativeService.shareContent({ text: 'Hello', url: '...' });
```

这种封装方式的好处是：当某个平台的实现需要修改时（比如Android的权限请求方式从旧API迁移到新的ActivityResultContracts），只需要改`android.js`文件，不影响业务层代码，也不影响iOS实现。当新增一个平台能力时，只需要在双端各加一个方法实现，然后在统一接口中添加一行调用声明即可，整个修改链路清晰可控。

这种"修改隔离"是大型项目可维护性的关键保障。在团队协作中，Android开发和iOS开发可以并行工作，只要双方约定好接口规范，各自实现各自的平台代码，互不阻塞。这也是为什么我强烈建议在项目初期就建立统一的NativeService封装层——它不增加多少开发量，却能在后续迭代中节省大量的沟通成本和修改成本。

封装规范还有一个常被忽视的好处：它让测试更容易。你可以针对统一接口写mock，在JS层做单元测试时不需要真的调用原生模块。测试时只需要mock掉NativeService的返回值，就能验证业务逻辑在各种场景下的正确性，不需要真机或模拟器。这对于提升测试覆盖率和开发效率都有显著帮助。

## 12.6 混合项目调试与问题排查实战

### 12.6.1 原生+JS混合日志查看技巧

混合开发的调试需要同时关注JS层和原生层的日志，这是很多新手不适应的地方——习惯了纯JS的console.log，突然要看Logcat和Xcode Console，完全不知道从哪下手。但混合项目的Bug往往出现在JS与原生的边界上，只看一端的日志无法定位问题。

Android端日志查看：

```bash
# 查看全部日志
adb logcat

# 只看RN相关日志
adb logcat -s ReactNativeJS:V ReactNative:V

# 只看特定Tag
adb logcat -s MyModule:V

# 过滤Error级别
adb logcat *:E
```

在原生代码中打日志是排查原生模块问题的关键手段：

```java
import android.util.Log;

// Android原生层打日志
Log.d("MyModule", "方法被调用了, 参数: " + input);
Log.e("MyModule", "执行出错", exception);
```

iOS端日志查看在Xcode的Console中可以看到NSLog输出：

```objc
// iOS原生层打日志
NSLog(@"方法被调用了, 参数: %@", input);
```

一个实用的调试技巧是在原生模块的每个方法入口和出口打日志，形成调用链路追踪。这样当问题发生时，你可以清晰地看到调用是否到达原生层、在哪一步出错：

```java
@ReactMethod
public void doSomething(String input, Promise promise) {
  Log.d("MyModule", 
    "doSomething called, input: " + input);
  try {
    String result = process(input);
    Log.d("MyModule", 
      "doSomething success, result: " + result);
    promise.resolve(result);
  } catch (Exception e) {
    Log.e("MyModule", 
      "doSomething failed", e);
    promise.reject("ERROR", e);
  }
}
```

> 混合调试的铁律是"原生层打日志、JS层看日志"。JS层的console.log在开发环境下可以通过Metro终端看到，但原生层的日志必须通过Logcat或Xcode Console查看。养成在原生模块的关键节点打日志的习惯，排查问题时你会感谢自己。日志不是越多越好，关键是打在"方法入口、关键分支、异常出口"这三个节点上，形成完整的调用链路视图。

### 12.6.2 双端编译报错快速定位修复

混合项目编译报错来源复杂，需要快速判断是哪个环节的问题。盲目翻代码效率极低，建立系统化的定位流程能大幅缩短排查时间。

报错定位决策树：

```
编译报错
  ├─ JS层报错？
  │   ├─ Metro终端显示 -> JS语法/导入错误
  │   └─ 红屏显示 -> 检查错误堆栈中的文件名和行号
  ├─ Android编译报错？
  │   ├─ Gradle报错 -> 检查build.gradle依赖配置
  │   ├─ Java编译错误 -> 检查原生Module代码
  │   └─ Manifest报错 -> 检查权限和组件声明
  └─ iOS编译报错？
      ├─ CocoaPods报错 -> 检查Podfile和pod install
      ├─ 编译错误 -> 检查ObjC/Swift代码
      └─ 链接错误 -> 检查framework和依赖
```

常见编译问题速查：

**问题：Android报"Unresolved reference"**

检查项：Module类是否正确继承ReactContextBaseJavaModule？是否在ReactPackage中注册？Kotlin和Java混用时包名是否一致？ProGuard规则是否排除了RN相关类？

**问题：iOS报"linker command failed"**

检查项：CocoaPods是否执行了pod install？是否Clean Build后重新编译？Framework Search Path是否正确？新架构下Codegen是否成功执行？

**问题：双端报"Native module cannot be null"**

检查项：JS端的模块名是否与原生端的getName()或RCT_EXPORT_MODULE()一致？Module是否正确注册到Package/Pod中？autolinking是否正确识别了库？

### 12.6.3 原生模块调用异常排查方案

原生模块调用时的异常通常表现为：JS调用后无响应、回调不执行、抛出异常。排查思路如下，按步骤逐层缩小问题范围：

第一步，确认模块是否正确加载：

```js
import { NativeModules } from 'react-native';

// 打印所有已注册的原生模块
console.log('已注册模块:', Object.keys(NativeModules));

// 检查目标模块是否存在
const { MyModule } = NativeModules;
if (!MyModule) {
  console.error('原生模块未注册');
}
if (!MyModule.myMethod) {
  console.error('方法未暴露给JS');
}
```

第二步，确认调用参数类型正确。RN的原生模块对参数类型有严格限制，类型不匹配时不会报错而是静默失败：

```js
// 常见错误：传了对象但原生端期望ReadableMap
// 正确做法：
MyModule.processData({ key: 'value' });
// 原生端接收参数声明为ReadableMap
```

第三步，在原生层打日志确认方法是否被调用。如果日志没打出来，说明调用根本没到达原生层，问题出在注册或命名上。

第四步，检查异常处理是否正确。原生模块中的try-catch必须覆盖所有可能出错的操作，reject的参数结构需要规范：

```java
@ReactMethod
public void processData(ReadableMap data, Promise promise) {
  try {
    String result = doProcess(data);
    promise.resolve(result);
  } catch (Exception e) {
    promise.reject("PROCESS_ERROR", 
      "处理失败: " + e.getMessage(), e);
  }
}
```

JS端接收错误时要检查error对象的code、message和nativeStack字段：

```js
try {
  const result = await MyModule.processData({ key: 'value' });
} catch (error) {
  console.error('原生调用失败:', 
    error.code,        // "PROCESS_ERROR"
    error.message,     // "处理失败: ..."
    error.nativeStack  // 原生堆栈信息
  );
}
```

> 排查原生模块异常的核心原则是"分层定位"。先确认JS端模块是否存在，再确认方法是否暴露，然后确认参数是否匹配，最后在原生层打日志确认方法是否被执行。一层一层缩小范围，不要一上来就翻原生代码，那会让你迷失在大量不相关的代码中。每一层都有明确的验证手段，验证通过再进入下一层，这是高效排查的正确姿势。

### 12.6.4 混合项目性能基础排查思路

混合项目的性能问题通常表现为：页面卡顿、操作延迟、内存占用持续增长。排查思路跟纯JS项目不同，需要考虑原生层的影响。

**排查JS线程与原生线程的负载**：

RN的JS运行在独立的JS线程上，原生UI运行在主线程上。如果JS线程被阻塞，UI会出现掉帧但不会ANR（Application Not Responding）。如果原生主线程被阻塞，会出现ANR弹窗或界面完全卡死。通过开发菜单中的"Show Perf Monitor"可以同时看到两个线程的帧率，快速判断瓶颈在哪一侧。

```js
// JS端手动性能测量
const start = performance.now();
await NativeModule.heavyTask();
const end = performance.now();
console.log('原生调用耗时:', end - start, 'ms');
```

**内存增长排查**：

混合项目内存泄漏的常见来源有四个：原生事件监听未移除、原生层持有React Context的强引用未释放、BroadcastReceiver或Observer未注销、大图片在原生层缓存未释放。Android使用Android Studio的Profiler工具查看Java Heap和Native Heap的变化趋势。iOS使用Xcode的Instruments工具中的Leaks和Allocations模板检测泄漏和监控内存分配。

> 性能排查的关键是"先定位再优化"。用性能监测器找到掉帧的线程（JS还是UI），用Profile工具找到内存增长的来源，用日志找到耗时的原生调用。盲目优化是混合项目最大的时间浪费。记住：没有数据支撑的优化是猜测，猜测解决不了工程问题。每次优化前后都要有可量化的对比数据，才能确认优化是否有效。常见的性能排查路径是：先用Perf Monitor观察帧率，确定是JS线程还是UI线程的问题；然后用console.time或performance.now测量关键操作的耗时；最后用Profiler或Instruments定位到具体的内存或CPU热点。这个流程看起来简单，但很多团队跳过前两步直接去改代码，改完不确定是否有效就提交，结果性能问题反复出现。

### 12.6.5 本章重难点复盘与实战练习

回顾全章内容，这里整理一份核心知识清单供收藏查阅。这份清单是全章内容的浓缩，建议收藏后在实际开发中随时对照。

**混合开发核心知识速查表**：

| 知识点 | Android | iOS |
|--------|---------|-----|
| Module基类 | ReactContextBaseJavaModule | RCTBridgeModule |
| 方法暴露 | @ReactMethod | RCT_EXPORT_METHOD |
| 模块注册 | ReactPackage | 自动注册/Pod |
| 异步回调 | Callback/Promise | Callback/Promise |
| 事件发送 | DeviceEventManager | RCTEventEmitter |
| 权限模型 | 运行时动态申请 | Info.plist+首次弹窗 |
| 依赖管理 | Gradle | CocoaPods |
| 构建工具 | Gradle + Android Studio | Xcode + CocoaPods |

**原生模块开发五步法**（收藏模板）：

```
1. 创建Module类（继承基类/实现协议）
2. 暴露方法（@ReactMethod / RCT_EXPORT_METHOD）
3. 注册模块（ReactPackage / autolinking）
4. JS层调用（NativeModules + await）
5. 验证测试（双端真机验证）
```

**常见踩坑清单**：

- 模块名不一致：JS端`NativeModules.MyModule`中的名称必须与原生端`getName()`或`RCT_EXPORT_MODULE()`返回值一致，大小写敏感
- 方法未标注：忘记加`@ReactMethod`或`RCT_EXPORT_METHOD`宏，方法不会暴露给JS，且不会报错
- 参数类型不匹配：JS传对象但原生端期望ReadableMap，需要确保类型对应，否则静默失败
- 事件监听未清理：`DeviceEventEmitter.addListener`和`NativeEventEmitter.addListener`必须在组件卸载时remove
- 权限遗漏：Android的Manifest声明和运行时申请缺一不可，iOS的Info.plist权限说明文本是审核必查项
- 编译缓存：修改原生代码后不clean就重新编译，可能用到旧的编译产物导致诡异错误
- 主线程阻塞：原生模块方法默认在原生线程执行，但UI操作必须在主线程，否则崩溃

**官方文档参考链接**：

- RN Native Modules官方文档：https://reactnative.dev/docs/native-modules
- RN Native Components官方文档：https://reactnative.dev/docs/native-components-android
- TurboModules文档：https://reactnative.dev/docs/the-new-architecture/pillars-turbo-modules
- iOS Bridging Native Modules：https://reactnative.dev/docs/native-modules-ios
- Android Native Modules：https://reactnative.dev/docs/native-modules-android
- Platform API文档：https://reactnative.dev/docs/platform
- PermissionsAndroid文档：https://reactnative.dev/docs/permissionsandroid
- CocoaPods官方文档：https://guides.cocoapods.org
- Gradle用户指南：https://docs.gradle.org/current/userguide

这些资源是混合开发的必备参考，建议加入收藏夹。遇到具体问题时，官方文档的准确性和时效性通常优于任何第三方教程。养成先查官方文档、再搜社区方案的习惯，能少走很多弯路。在混合开发领域，官方文档的更新频率和社区的支持质量都是非常重要的参考因素，选型和排查问题时应始终把官方文档作为第一信息源。

怕浪猫说：混合开发是RN从"玩具"走向"工具"的关键一跃。纯JS开发能让你快速验证想法，但只有混合开发能让你把想法变成生产级的产品。理解通信原理、掌握双端原生模块开发、做好差异化封装、学会混合调试，这四件事做到了，你就不是一个只会写JS的RN开发者，而是一个能hold住全链路的移动端工程师。当你能把通信原理讲清楚、把双端模块写出来、把差异封装好、把问题排查明白，你就真正具备了混合开发的全栈能力。这些能力不是看文章看会的，是在真实项目中踩坑踩出来的。建议看完这章后，自己动手写一个完整的原生模块——比如获取设备信息的模块——双端都写，完整走一遍流程，你会对这章的内容有更深的理解。

**系列进度 12/16**

怕浪猫说：JS是矛，原生是盾。只会矛的战士冲得快但也伤得快，配上盾才能走得远。混合开发就是教你的JS长出原生铠甲，16章带你从零到一拿下RN全栈开发，我们下一章见。

下一章预告：第13章《RN项目性能优化、卡顿与内存治理》将深入讲解RN渲染卡顿的根本原因、JS线程与UI线程的阻塞问题、FlatList列表性能深度优化、内存泄漏检测与专项治理、打包瘦身与工程化性能优化方案。从"能跑起来"到"跑得流畅"，完成从功能开发到性能工程的进阶。

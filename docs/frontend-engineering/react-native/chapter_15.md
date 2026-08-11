---
sidebar_position: 15
---

# 第15章 RN项目打包、内测分发与线上发布

> 打包不是按下按钮那么简单，它是一道从代码到用户手机的完整工程链路，任何一个环节疏忽都会让 weeks 的开发功亏一篑。

一个让人后背发凉的数据：超过 60% 的 RN（React Native）项目第一次打包正式包时会失败。不是代码写错了，而是签名配置不对、环境变量没切、构建脚本少了一行参数。更扎心的是，有人打了一整天的包终于成功，提交到应用商店却被驳回，原因仅仅是图标少了一个尺寸或者权限说明写得不对。还有团队第一次走 iOS（iPhone Operating System）上架流程，证书、描述文件（Provisioning Profile）、Archive 导出 IPA（iOS App Store Package）包，每一步都是坑，光是搞定 Apple Developer 账号就耗了一周。打包发布这件事，开发写得再好，最后一公里走不通，用户就看不到你的产品。

打包阶段的典型灾难场景远不止这些。Android 端 Release 包在本地跑得好好的，到了 CI（Continuous Integration）环境就报 SDK（Software Development Kit）版本不匹配；iOS 端 Archive 成功了但导出时选错了证书类型，打出来的包无法安装；热更新推了一个有 bug 的版本，没有灰度策略直接全量发布，结果十万用户同时看到白屏。这些问题不是偶发事故，而是缺乏体系化打包发布流程的必然结果。从环境隔离到签名管理，从内测分发到商店上架，从热更新到版本回滚，每一个环节都需要明确的规范和可复用的脚本。

我是怕浪猫，一个把 RN 项目从 0 打包到上百万 DAU（Daily Active Users）的工程老兵。从最早手动打包踩坑无数，到后来搭建完整的 CI/CD（Continuous Integration / Continuous Deployment）流水线，从第一次 iOS 提审被驳回三次，到后来总结出一套上架检查清单做到一次过审，我对打包发布的每个环节都有血的教训。这一章我来系统讲解 RN 项目打包、内测分发与线上发布的全流程，从环境体系搭建到双端签名配置，从内测分发到应用商店上架，从热更新到版本迭代管控，帮你打通从代码到用户的最后一公里。

## 15.1 打包发布流程与环境体系搭建

### 15.1.1 开发、测试、生产环境区分

打包发布的第一件事不是去碰构建工具，而是把环境体系理清楚。一个成熟的 RN 项目至少需要三套环境：开发环境（development）、测试环境（staging）、生产环境（production）。这三套环境对应不同的 API（Application Programming Interface）地址、不同的第三方 SDK 密钥、不同的日志级别、不同的功能开关。如果不做环境隔离，开发时连着生产数据库测试一下，搞不好就把线上数据污染了。

来看三套环境的核心差异：

```
环境体系对比：

开发环境 (development)
  - API: http://localhost:8080/api
  - 日志: 全量输出
  - 热更新: 不启用
  - 第三方SDK: 测试密钥

测试环境 (staging)
  - API: https://api-staging.example.com
  - 日志: WARN级别
  - 热更新: 测试通道
  - 第三方SDK: 测试密钥

生产环境 (production)
  - API: https://api.example.com
  - 日志: ERROR级别
  - 热更新: 正式通道
  - 第三方SDK: 正式密钥
```

在 RN 项目中实现多环境切换，最常用的方案是 react-native-config。这个库允许你通过 `.env` 文件管理不同环境的配置变量，在 JS（JavaScript）层和原生层都能访问。

先创建环境配置文件：

```bash
# .env.development
API_URL=http://localhost:8080/api
APP_NAME=MyApp_Dev
CODEPUSH_KEY=dev_key_here
ENABLE_DEV_MENU=true

# .env.staging
API_URL=https://api-staging.example.com
APP_NAME=MyApp_Staging
CODEPUSH_KEY=staging_key_here
ENABLE_DEV_MENU=false

# .env.production
API_URL=https://api.example.com
APP_NAME=MyApp
CODEPUSH_KEY=prod_key_here
ENABLE_DEV_MENU=false
```

配置完环境文件后，在 JS 层通过 `Config` 对象读取变量：

```js
import Config from 'react-native-config';

// 根据环境自动加载对应的配置
const apiClient = axios.create({
  baseURL: Config.API_URL,
  timeout: 15000,
});

// 开发环境开启调试菜单
if (Config.ENABLE_DEV_MENU === 'true') {
  // 显示开发工具入口
  showDevTools();
}
```

原生层同样需要读取这些变量。Android 端在 `build.gradle` 中配置：

```gradle
// android/app/build.gradle
apply from: project(':react-native-config').projectDir.getPath() + "/dotenv.gradle"

android {
    // 通过 productFlavors 区分环境
    flavorDimensions "env"
    productFlavors {
        dev {
            dimension "env"
            applicationIdSuffix ".dev"
            resValue "string", "app_name", "MyApp_Dev"
        }
        staging {
            dimension "env"
            applicationIdSuffix ".staging"
            resValue "string", "app_name", "MyApp_Staging"
        }
        prod {
            dimension "env"
            resValue "string", "app_name", "MyApp"
        }
    }
}
```

iOS 端利用 Xcode 的 Configuration 和 xcconfig 文件管理。创建三个 xcconfig 文件，在 `Info.plist` 中通过变量引用，在构建时通过 scheme 切换配置。这样每个环境有独立的 Bundle ID（Bundle Identifier），可以在同一台手机上同时安装开发版、测试版和生产版，互不干扰。

> 环境隔离不是"讲究"，是底线。我见过太多团队图省事，开发测试生产共用一套环境配置，上线时手动改一下地址就打包。人肉操作一次出错就是灾难。多环境配置的前期投入看似浪费时间，实际是在为后续每次打包节省时间、为每次发布兜底安全。

### 15.1.2 多环境接口与配置差异化处理

环境区分只是框架，真正的挑战在于配置差异化的细节处理。不同环境下，不仅仅是 API 地址不同，还涉及第三方 SDK 密钥、推送通知配置、支付环境、日志策略、功能开关等一系列差异化配置。如果这些配置散落在代码各处，用 `if (__DEV__)` 判断，很快就会变成一团乱麻。

正确的做法是建立统一的配置中心。在 JS 层创建一个 ConfigManager，集中管理所有环境差异化配置：

```js
// src/config/ConfigManager.js
import Config from 'react-native-config';

const envConfig = {
  development: {
    api: { baseURL: Config.API_URL, timeout: 30000 },
    log: { level: 'debug', enableConsole: true },
    feature: { newUI: true, betaFunc: true },
    Sentry: { dsn: '', enabled: false },
  },
  staging: {
    api: { baseURL: Config.API_URL, timeout: 15000 },
    log: { level: 'warn', enableConsole: true },
    feature: { newUI: true, betaFunc: false },
    Sentry: { dsn: 'staging_dsn', enabled: true },
  },
  production: {
    api: { baseURL: Config.API_URL, timeout: 15000 },
    log: { level: 'error', enableConsole: false },
    feature: { newUI: false, betaFunc: false },
    Sentry: { dsn: 'prod_dsn', enabled: true },
  },
};

export const ENV = Config.ENV || 'production';
export const config = envConfig[ENV];
```

原生层同样需要处理差异化配置。Android 端在 `AndroidManifest.xml` 中通过 `meta-data` 注入不同环境的值，iOS 端在 `Info.plist` 中通过变量引用。这样无论是推送通知、支付回调还是地图 SDK，都能根据构建环境自动使用正确的配置。

一个容易忽略的点是：功能开关（Feature Flag）也应该纳入环境配置管理。开发环境开启新功能进行测试，生产环境保持关闭直到功能经过验证再逐步放开。这比用代码分支管理功能发布灵活得多，也是灰度发布的基础。

### 15.1.3 RN打包编译核心原理解析

理解 RN 的打包原理，是排查打包问题的基础。RN 的打包过程分为两个独立的流水线：JS 层的 Bundle 打包和原生层的编译打包。

JS Bundle 打包由 Metro Bundler 负责。Metro 是 RN 的 JS 打包工具，它做三件事：解析模块依赖关系、转换 JS/TS 代码、合并为一个 Bundle 文件。打包命令 `npx react-native bundle` 触发的就是这个流程。

```
Metro Bundler 打包流程：

入口文件 index.js
    |
    v
模块解析 (Resolution)
  - 解析 import/require 依赖
  - 构建依赖图谱 (Dependency Graph)
    |
    v
代码转换 (Transformation)
  - Babel 转译 TS/JSX
  - 移除开发代码 (__DEV__)
  - Tree Shaking 优化
    |
    v
Bundle 生成 (Serialization)
  - 合并所有模块为一个文件
  - 注入模块加载器 (Module Loader)
  - 生成 source map
    |
    v
index.android.bundle / index.ios.bundle
```

原生层编译打包，Android 和 iOS 各走各的路线。Android 端通过 Gradle 构建系统，执行 Java/Kotlin 编译、资源合并、DEX（Dalvik Executable）转换、APK（Android Package）打包和签名。iOS 端通过 Xcode 构建系统，执行 Objective-C/Swift 编译、资源拷贝、代码签名和 IPA 打包。

关键点在于：JS Bundle 需要被打包进原生包中（如果不使用 CodePush 热更新），或者放在服务器上通过热更新下发。打包进原生包时，Android 将 `index.android.bundle` 放在 `assets/` 目录，iOS 将 `main.jsbundle` 作为资源文件打包进 APP。

来看 Metro 打包的核心配置：

```js
// metro.config.js
const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

const config = {
  transformer: {
    minifierConfig: {
      keep_classnames: true, // 保留类名用于混淆映射
      mangle: { toplevel: false },
    },
  },
  resolver: {
    // 生产环境排除开发依赖
    blockList: {
      '.*\\/__tests__\\/.*': undefined,
    },
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
```

> 理解打包原理的价值不在于"显得专业"，而在于遇到问题时知道从哪里下手。打包报错说 "Module not found"，你该看 Metro 的模块解析阶段；APK 体积异常大，你该检查资源合并阶段；Release 包闪退但 Debug 包正常，八成是代码混淆或者 ProGuard 规则的问题。知其然也知其所以然，排错效率天差地别。

### 15.1.4 双端打包前置准备工作

在正式进入打包流程之前，需要完成一系列前置准备工作。这些工作如果遗漏，打包过程中会反复出错，浪费时间。

Android 端前置清单：

第一项，确认 Gradle 和 SDK 版本。检查 `build.gradle` 中的 `compileSdkVersion`、`buildToolsVersion`、`minSdkVersion`、`targetSdkVersion` 是否满足目标应用商店的要求。Google Play（Google 的应用商店）目前要求 `targetSdkVersion` 至少为 33，国内部分市场也有类似要求。版本不达标直接被拒。

第二项，应用图标和启动页资源。Android 需要准备 `mipmap-mdpi` 到 `mipmap-xxxhdpi` 五套图标，以及自适应图标（Adaptive Icon）的前景和背景层。启动页需要配置 `splash.png` 的多尺寸版本。资源缺失会导致在某些设备上显示异常。

第三项，混淆规则配置。Release 包默认开启 ProGuard（Java 字节码混淆器），需要为 RN 和第三方库添加混淆保留规则，否则反射调用会被混淆破坏导致崩溃。

iOS 端前置清单：

第一项，Apple Developer 账号。个人账号年费 99 美元，需要提前申请。没有账号连证书都生成不了，后面所有步骤都走不下去。

第二项，Bundle Identifier 配置。在 Apple Developer Portal 中注册 App 的 Bundle ID，确保与 Xcode 项目中的一致。Bundle ID 一旦上架就不能修改，所以要慎重命名。

第三项，应用图标和启动屏。iOS 需要提供完整的 AppIcon 资源集，包括不同尺寸的 iPhone 和 iPad 图标。Xcode 的 Asset Catalog 会校验图标尺寸，缺失任何尺寸都无法 Archive。

第四项，版本号和构建号策略。`CFBundleShortVersionString` 是用户可见的版本号，`CFBundleVersion` 是构建号。每次提审构建号必须递增，否则上传到 App Store Connect 时会被拒绝。

### 15.1.5 上线整体流程与风险把控

打包发布不是一键操作，而是一个多阶段流程。完整的上线流程包含五个阶段：开发完成 -> 内测验证 -> 打包签名 -> 商店提审 -> 发布上线。每个阶段都有明确的准入准出条件和风险控制点。

```
上线流程全景图：

[开发完成] --准入: 代码审查通过、单元测试覆盖
    |
    v
[内测验证] --准入: 测试环境打包、QA验证通过
    |           风险: 测试环境与生产差异导致漏测
    v
[打包签名] --准入: 生产配置确认、签名文件就绪
    |           风险: 签名错误、环境变量未切换
    v
[商店提审] --准入: 商店资料完整、隐私政策合规
    |           风险: 审核驳回、敏感权限被质疑
    v
[发布上线] --准入: 审核通过、灰度计划制定
                风险: 线上bug、性能回退
```

风险把控的核心原则是"可回滚"。每次发布前必须确认：如果线上出问题，能否快速回滚到上一个版本。对于热更新能覆盖的 JS 层 bug，可以通过 CodePush 回滚；对于原生层 bug，需要通过商店下架旧版本或紧急发布新版本。灰度发布是降低风险的关键手段，先放 5% 的用户，观察一段时间无异常后再逐步扩大。

> 上线不是终点，而是风险管理的起点。最危险的时刻不是打包时，而是发布后的前两小时。用户真实环境千差万别，再充分的测试也无法覆盖所有场景。准备好监控告警、准备好回滚方案、准备好应急响应流程，这才是负责任的发布态度。

## 15.2 Android签名配置与正式包打包

### 15.2.1 Android签名文件生成与配置

Android 系统要求所有 APK 必须经过数字签名才能安装。签名不是可选项，而是系统级强制要求。Debug 包用 Android Studio 自动生成的 debug keystore 签名，但 Release 包必须用正式的签名文件签名。

生成签名文件使用 `keytool` 命令：

```bash
keytool -genkeypair \
  -alias myapp-release \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -keystore myapp-release.keystore

# 交互式输入：
# keystore密码、姓名、组织单位、组织名、城市、省份、国家代码
```

关键参数说明：`-keyalg RSA` 指定使用 RSA（Rivest-Shamir-Adleman）非对称加密算法；`-keysize 2048` 设置密钥长度为 2048 位，低于 1024 位会被部分应用商店拒绝；`-validity 10000` 设置证书有效期为 10000 天（约 27 年），证书过期后 APP 仍然可以运行但无法发布更新。

生成签名文件后，在 `build.gradle` 中配置签名信息。千万不要把密码明文写在 `build.gradle` 里提交到版本控制，这是严重的安全隐患。正确做法是将签名信息放在 `gradle.properties` 或环境变量中：

```gradle
// android/gradle.properties
MYAPP_UPLOAD_STORE_FILE=myapp-release.keystore
MYAPP_UPLOAD_STORE_PASSWORD=*****
MYAPP_UPLOAD_KEY_ALIAS=myapp-release
MYAPP_UPLOAD_KEY_PASSWORD=*****

// android/app/build.gradle
android {
    signingConfigs {
        release {
            storeFile file(MYAPP_UPLOAD_STORE_FILE)
            storePassword MYAPP_UPLOAD_STORE_PASSWORD
            keyAlias MYAPP_UPLOAD_KEY_ALIAS
            keyPassword MYAPP_UPLOAD_KEY_PASSWORD
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

签名文件是 APP 身份的数字凭证，一旦丢失就无法发布更新，一旦泄露就可能被他人伪造你的 APP。务必将签名文件备份在安全的位置（如加密的密码管理器），并且不要将 keystore 文件提交到 Git 仓库。

### 15.2.2 测试签名与正式签名区分使用

实际项目中，开发阶段和测试阶段用的签名应该与正式发布签名区分开。这样做有两个原因：第一，测试包和正式包用不同的签名，可以在同一台设备上共存安装，互不影响；第二，限制正式签名的使用范围，降低泄露风险。

配置方案是通过 `productFlavors` 为不同环境指定不同签名：

```gradle
android {
    signingConfigs {
        debug {
            // 使用默认 debug 签名
        }
        staging {
            storeFile file('myapp-staging.keystore')
            storePassword 'staging_password'
            keyAlias 'myapp-staging'
            keyPassword 'staging_password'
        }
        release {
            storeFile file(MYAPP_UPLOAD_STORE_FILE)
            storePassword MYAPP_UPLOAD_STORE_PASSWORD
            keyAlias MYAPP_UPLOAD_KEY_ALIAS
            keyPassword MYAPP_UPLOAD_KEY_PASSWORD
        }
    }

    productFlavors {
        dev { signingConfig signingConfigs.debug }
        staging { signingConfig signingConfigs.staging }
        prod { signingConfig signingConfigs.release }
    }
}
```

这套配置下，`dev` 包用 debug 签名，包名带 `.dev` 后缀；`staging` 包用测试签名，包名带 `.staging` 后缀；`prod` 包用正式签名，包名为正式包名。三个包可以同时安装在同一台设备上，测试同学可以同时对比测试版本和生产版本的行为差异。

### 15.2.3 gradle打包脚本配置优化

Gradle 是 Android 的构建工具，合理的配置可以显著提升打包速度和产出质量。以下是几个关键优化点。

开启资源压缩和代码混淆。Release 包应该开启 `shrinkResources` 和 `minifyEnabled`，移除未使用的资源和代码，减小 APK 体积：

```gradle
buildTypes {
    release {
        minifyEnabled true
        shrinkResources true
        proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        signingConfig signingConfigs.release
    }
}
```

ProGuard 规则配置是容易踩坑的地方。RN 项目需要保留 JavaScript 引擎和 Bridge 通信相关的类，否则 Release 包会崩溃。核心 ProGuard 规则：

```proguard
# proguard-rules.pro
-keep class com.facebook.react.** { *; }
-keep class com.facebook.hermes.** { *; }
-keepclassmembers class * { @com.facebook.react.bridge.* <methods>; }
-keep class com.google.gson.** { *; }
# 第三方SDK混淆规则按各自文档添加
```

APK 体积拆分优化。如果不需要一个 APK 支持所有 CPU 架构，可以通过 `splits` 配置按架构拆分，每个 APK 只包含对应架构的 so 库：

```gradle
android {
    splits {
        abi {
            enable true
            reset()
            include 'arm64-v8a', 'armeabi-v7a', 'x86_64'
            universalApk true  # 同时生成包含所有架构的通用包
        }
    }
}
```

### 15.2.4 Android Release正式包编译打包

一切配置就绪后，开始打 Release 正式包。命令很简单：

```bash
# 方式一：命令行打包
cd android && ./gradlew assembleProdRelease

# 方式二：指定环境变量
ENVFILE=.env.production cd android && ./gradlew assembleProdRelease
```

打包产物在 `android/app/build/outputs/apk/prod/release/` 目录下。如果是 `universalApk`，产物为一个通用 APK；如果开启了 `splits`，则会有多个按架构拆分的 APK。

打包过程中 Metro Bundler 会先执行 JS Bundle 打包，生成 `index.android.bundle` 并放入 `assets/` 目录，然后 Gradle 执行原生编译和签名。整个过程通常需要 3-10 分钟，取决于项目规模和机器性能。

打包成功后的验证步骤不可少。用 `aapt`（Android Asset Packaging Tool）检查 APK 信息：

```bash
# 检查包名、版本号、签名信息
aapt dump badging app-prod-release.apk | head -5

# 验证签名
jarsigner -verify -verbose app-prod-release.apk
```

> 打包成功不等于包没问题。我每次打完包都会做三件事：装到真机上跑一遍主流程、检查 JS Bundle 是否正确打包、验证签名信息。这三步花不了五分钟，但能拦截至少 90% 的打包问题。比起上线后用户报障再回滚，这点投入微不足道。

### 15.2.5 安卓打包常见报错排查修复

打包报错是家常便饭，关键是要快速定位问题根因。以下是高频报错及解决方案。

**报错一：Task :app:mergeReleaseResources FAILED**

原因通常是资源文件冲突或格式错误。检查最近的资源文件变更，特别是新增的图片资源是否命名规范（只能小写字母、数字和下划线）。运行 `./gradlew clean` 清理缓存后重试。

**报错二：java.lang.OutOfMemoryError: Java heap space**

Gradle 编译内存不足。在 `gradle.properties` 中增大堆内存：

```properties
# android/gradle.properties
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=1024m
org.gradle.workers.max=4
```

**报错三：More than one file was found with OS independent path**

资源重复打包。通常是第三方库中包含了相同的 so 库文件。在 `packagingOptions` 中排除冲突：

```gradle
android {
    packagingOptions {
        exclude 'META-INF/DEPENDENCIES'
        exclude 'lib/x86/libcrypto.so'
        pickFirst '**/*.so'
    }
}
```

**报错四：React Native bundle failed**

JS Bundle 打包失败，通常是 JS 代码中有语法错误或模块引用路径大小写不一致。Metro 在 Linux 上对路径大小写敏感，`import Foo from './Foo'` 在 macOS 上能跑，但到 CI 的 Linux 环境就报错。统一使用正确的文件名大小写。

**报错五：SDK location not found**

`local.properties` 中 SDK 路径未配置或路径错误。确保 `sdk.dir` 指向正确的 Android SDK 路径，或者设置 `ANDROID_HOME` 环境变量。

## 15.3 iOS证书配置与Archive打包

### 15.3.1 Apple开发者账号配置流程

iOS 打包的第一道门槛是 Apple Developer 账号。没有这个账号，连证书都生成不了，更别说打包和上架。Apple 提供两种类型的开发者账号：个人/公司账号（年费 99 美元）和企业账号（年费 299 美元）。个人/公司账号上架的 APP 在 App Store 公开发布，企业账号用于企业内部分发，不上架 App Store。

注册流程：访问 Apple Developer 官网（https://developer.apple.com），使用 Apple ID 登录，完成身份验证后加入 Apple Developer Program。如果是公司账号，需要提供 D-U-N-S（Data Universal Numbering System）编号，这是 Dun & Bradstreet 公司提供的全球企业身份识别码，申请过程可能需要 1-2 周。

账号开通后，在 Apple Developer Portal（https://developer.apple.com/account）中完成以下配置：

```
Apple Developer 配置清单：
1. 注册 App ID (Identifier)
   - 设置 Bundle ID (如 com.example.myapp)
   - 开启所需 Capabilities (Push通知、支付等)

2. 创建证书 (Certificates)
   - Development 证书 (开发调试)
   - Distribution 证书 (发布上架)

3. 创建描述文件 (Provisioning Profiles)
   - Development Profile (关联开发证书和设备)
   - App Store Profile (关联发布证书)

4. 注册测试设备 (Devices)
   - 添加内测设备的 UDID (Unique Device Identifier)
```

### 15.3.2 开发/发布证书与描述文件配置

证书是开发者身份的数字凭证，描述文件是将 App ID、证书和设备关联在一起的配置文件。两者配合使用才能完成代码签名。

证书生成需要先在本地创建 CSR（Certificate Signing Request）文件。在 Mac 的"钥匙串访问"中操作：钥匙串访问 -> 证书助理 -> 从证书颁发机构请求证书，生成 `CertificateSigningRequest.certSigningRequest` 文件。然后在 Developer Portal 中上传 CSR，Apple 签名后返回证书文件，下载并安装到钥匙串。

开发证书（Development Certificate）用于真机调试，允许 APP 在注册的测试设备上运行。发布证书（Distribution Certificate）用于 App Store 上架和 Ad Hoc 分发。两种证书不能混用，开发证书签名的包不能提交到 App Store，发布证书签名的包不能直接安装到设备上。

描述文件配置是另一个容易出错的环节。开发描述文件需要关联开发证书和所有测试设备的 UDID；App Store 描述文件关联发布证书，不需要指定设备。描述文件过期后 APP 无法运行，需要注意有效期并及时续期。

在 Xcode 中配置签名：打开项目 -> 选择 Target -> Signing & Capabilities 标签页 -> 勾选 Automatically manage signing -> 选择对应的 Team。Xcode 会自动匹配证书和描述文件。如果遇到冲突，手动取消自动管理，选择正确的描述文件。

### 15.3.3 Xcode项目打包参数配置

Archive 之前需要确认一系列项目参数，这些参数直接决定打包能否成功以及包的质量。

版本号配置。`MARKETING_VERSION`（对应 `CFBundleShortVersionString`）是用户可见的版本号，格式通常为 `x.y.z`；`CURRENT_PROJECT_VERSION`（对应 `CFBundleVersion`）是构建号，每次 Archive 必须递增。可以在 Xcode 的 General 标签页中设置，也可以在 `project.pbxproj` 文件中通过变量引用。

Build Configuration 确认。确保 Release configuration 的优化级别设置为 `-O`（最快最小），Debug 标志设置为 `NO`。检查 `OTHER_LDFLAGS` 是否包含必要的链接标志。RN 项目通常需要保留 `$(inherited)` 和 React 相关的链接标志。

Bitcode 设置。从 Xcode 14 开始 Apple 已废弃 Bitcode，确保设置 `ENABLE_BITCODE = NO`。如果第三方库仍要求开启 Bitcode，需要联系库作者更新或自行 fork 修改。

权限说明文案。iOS 对权限说明要求极其严格，`NSCameraUsageDescription`、`NSPhotoLibraryUsageDescription` 等权限说明不能为空，不能过于笼统，必须具体说明 APP 如何使用该权限。文案写得太模糊是审核被驳回的高频原因之一。

### 15.3.4 Archive归档与导出IPA包流程

参数配置确认无误后，开始 Archive 流程。Archive 是 Xcode 将 APP 编译为发布版本并归档保存的过程。

操作步骤：在 Xcode 中选择设备目标为 "Any iOS Device (arm64)" -> 菜单栏 Product -> Archive。Archive 过程会执行 Release 编译，生成 `.xcarchive` 归档文件。完成后自动打开 Organizer 窗口。

```
Archive 导出流程：

[Archive编译] -> 生成 .xcarchive 归档文件
    |
    v
[Distribute App] -> 选择分发方式
    |
    +-- App Store Connect (上架)
    +-- Ad Hoc (内测分发, 限100台设备)
    +-- Development (开发设备安装)
    +-- Enterprise (企业内部分发)
    |
    v
[选择签名] -> 自动签名 或 手动选择描述文件
    |
    v
[导出] -> 生成 .ipa 文件
```

选择 App Store Connect 导出时，Xcode 会生成一个 `.ipa` 文件并可以直接上传到 App Store Connect。选择 Ad Hoc 导出时，生成的 `.ipa` 可以通过 TestFlight 或其他内测分发平台安装到注册设备上。

命令行打包方案。对于 CI/CD 流水线，需要用命令行完成 Archive 和导出：

```bash
# Archive
xcodebuild archive \
  -workspace MyApp.xcworkspace \
  -scheme MyApp \
  -configuration Release \
  -archivePath build/MyApp.xcarchive \
  -destination "generic/platform=iOS"

# 导出 IPA
xcodebuild -exportArchive \
  -archivePath build/MyApp.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/
```

`ExportOptions.plist` 配置导出参数：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>uploadBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
```

> 命令行打包的真正价值不是"不用打开 Xcode"，而是让打包过程可复现、可自动化。一旦打包脚本跑通了，无论是本地一键打包还是接入 CI 流水线，都是同一个脚本、同一套逻辑。人为操作的变量越多，出错的概率越高，自动化是消灭打包问题的根本手段。

### 15.3.5 iOS打包编译报错兼容修复

iOS 打包报错的信息通常比 Android 更明确，但修复难度往往更大，因为涉及签名、链接、架构等底层问题。

**报错一：No profiles for 'com.example.app' were found**

签名配置问题。检查 Developer Portal 中是否已创建对应的 App ID 和描述文件，确认 Xcode 中选择的 Team 与证书匹配。如果是命令行打包，检查 `ExportOptions.plist` 中的 `teamID` 是否正确。

**报错二：duplicate symbol '_OBJC_CLASS_$_xxx'**

重复符号冲突，通常是两个第三方库包含了相同的类。解决方法是找到冲突的库，在 `podfile` 中通过 `post_install` 钩子移除重复符号，或者更新库版本。

**报错三：Undefined symbols for architecture arm64**

链接错误，通常是某个库没有包含 arm64 架构。在新版 Xcode 中默认只编译 arm64，如果第三方库只有 x86_64 架构就会报错。检查 `EXCLUDED_ARCHES` 配置，确保 Release 配置下不排除 arm64。

**报错四：Command PhaseScriptExecution failed with a nonzero exit code**

这个报错信息非常笼统，实际原因可能是 CocoaPods 缓存问题、脚本权限问题或路径问题。排查步骤：打开 Xcode 的 Issue Navigator 查看详细日志 -> 检查 `Pods/` 目录是否完整 -> 执行 `pod deintegrate && pod install` 重装依赖。

**报错五：This build requires a newer version of xcode**

Xcode 版本过低。App Store Connect 在某些时间点会强制要求使用最新版 Xcode 提交。保持 Xcode 更新到最新稳定版本，CI 环境使用 `xcode-select` 切换到正确版本。

## 15.4 内测分发与版本测试校验

### 15.4.1 安卓内测包分发平台使用

Android 内测分发相对灵活，APK 文件本身可以直接安装，不需要平台审核。但为了方便测试同学安装和版本管理，通常会使用内测分发平台。

国内常用的 Android 内测分发平台包括：蒲公英（pgyer.com）、fir.im、腾讯 Bugly 等。这些平台提供 APK 上传、二维码扫码安装、版本管理、崩溃收集等一站式服务。

以蒲公英为例，上传 APK 后生成下载链接和二维码：

```bash
# 蒲公英 CLI 上传
curl -F "file=@app-prod-release.apk" \
  -F "_api_key=your_api_key" \
  -F "buildUpdateDescription=v1.2.0 内测包更新" \
  -F "buildInstallType=2" \
  https://www.pgyer.com/apiv2/app/upload
```

`buildInstallType` 参数控制安装方式：`1` 为公开安装，`2` 为密码安装，`3` 为邀请码安装。内测阶段建议用密码安装或邀请码安装，避免包被未授权人员下载。

分发流程的完整链路：

```
[打包APK] -> [上传分发平台] -> [生成下载二维码]
                                    |
                                    v
                         [测试同学扫码安装]
                                    |
                                    v
                         [测试反馈 -> 开发修复]
                                    |
                                    v
                         [重新打包 -> 新版本分发]
```

> 内测分发的核心目标不是"分发"，而是"收集反馈"。如果一个内测包发出去没人反馈问题，不是包没问题，而是没人测。建立明确的测试任务清单和反馈渠道，比分发平台本身更重要。让测试同学知道"这次测什么"、"怎么反馈"，内测才有价值。

### 15.4.2 iOS TestFlight内测分发流程

iOS 内测分发不像 Android 那样自由，IPA 包不能直接发给别人安装。Apple 官方提供的内测分发渠道是 TestFlight，所有内测包必须通过 App Store Connect 上传。

TestFlight 分发流程：

```
[Xcode Archive导出IPA] -> [上传到App Store Connect]
    |
    v
[App Store Connect选择构建版本]
    |
    +-- 内部测试 (Internal Testing)
    |   - 最多25名内部测试员
    |   - 无需审核, 上传后即可测试
    |
    +-- 外部测试 (External Testing)
        - 最多10000名外部测试员
        - 首次需Apple审核, 后续同版本号免审
```

上传 IPA 到 App Store Connect 有两种方式。第一种是 Xcode Organizer 直接上传：Archive 完成后点击 "Distribute App" -> 选择 "App Store Connect" -> 选择 "Upload" -> 等待上传和处理完成。第二种是命令行使用 `altool` 或 `xcrun notarytool` 上传：

```bash
# 命令行上传到 App Store Connect
xcrun altool --upload-app \
  -f MyApp.ipa \
  -t ios \
  -u "apple_id@email.com" \
  -p "app-specific-password"
```

上传后 Apple 需要几分钟到半小时处理构建版本。处理完成后在 App Store Connect 的 TestFlight 标签页中可以看到新的构建版本，添加测试员或测试组即可分发。

TestFlight 安装方式：测试员在 App Store 下载 TestFlight 应用，通过邀请链接或邀请码加入测试，然后在 TestFlight 中安装内测 APP。每次安装会显示版本号和构建号，方便测试同学区分不同版本。

### 15.4.3 内测版本功能与兼容性测试

内测不是"装上跑一下看看不崩就行"，而是有明确的测试维度和验收标准。一个完整的内测验证应该覆盖以下维度。

功能测试。按照需求文档逐项验证功能是否正常，重点关注本次变更涉及的功能模块。回归测试验证已有功能是否因新变更而受到影响。功能测试需要覆盖主流程和边界场景，比如网络异常、数据为空、并发操作等。

兼容性测试。Android 端需要覆盖不同品牌（华为、小米、OPPO、vivo）、不同系统版本（至少覆盖最低支持版本和最新版本）、不同屏幕尺寸。iOS 端需要覆盖不同机型（iPhone SE 到 iPhone 15 Pro Max）和不同系统版本。RN 的跨端特性不能替代真机兼容性测试，很多问题只在特定机型上出现。

性能测试。重点关注启动时间、页面切换流畅度、内存占用和电池消耗。RN 项目在低端 Android 设备上的性能表现可能远低于预期，需要在真机上验证。可以使用 Flashlight（RN 性能测试工具）进行自动化性能采集：

```bash
# Flashlight 测量启动时间
npx flashlight measure \
  --test CommandArguments.ts \
  --iterations 10 \
  --platform android
```

兼容性测试中最容易被忽略的是系统级交互场景：APP 在后台被系统杀掉后恢复、来电中断后恢复、权限弹窗交互、深链接跳转、推送通知处理。这些场景在开发阶段很难覆盖，只有通过真机内测才能发现。

### 15.4.4 内测问题收集与快速修复

内测问题的高效收集和快速修复是内测迭代速度的关键。问题收集渠道通常包括：测试同学的直接反馈、分发平台的崩溃收集、Sentry 等异常监控平台。

建立标准化的问题反馈模板，确保每个问题都有足够的信息供开发定位：

```markdown
## 问题反馈模板

**版本号**: v1.2.0 (build 45)
**设备型号**: iPhone 13 Pro / 小米 14
**系统版本**: iOS 17.2 / Android 14
**复现步骤**:
1. 打开APP, 进入xxx页面
2. 点击xxx按钮
3. 出现xxx现象
**预期行为**: 应该显示xxx
**实际行为**: 出现了xxx / 闪退
**截图/录屏**: [附上]
```

快速修复流程的核心是缩短"发现问题 -> 修复 -> 验证 -> 重新分发"的周期。推荐的工作流是：测试发现 bug -> 在 Jira/飞书等工具中创建 Issue -> 开发修复 -> 提交代码触发 CI 打包 -> 新包上传分发平台 -> 通知测试同学验证。这个流程如果能自动化，一个修复轮次可以控制在 30 分钟以内。

对于崩溃类问题，确保 Sentry 或 Bugly 已正确集成，能够自动收集崩溃堆栈。Release 包记得上传 source map，这样监控平台上显示的是可读的 JS 代码位置而不是混淆后的行号：

```bash
# 上传 source map 到 Sentry
npx @sentry/cli sourcemaps upload \
  --release com.example.myapp@1.2.0 \
  --dist 45 \
  android/app/src/main/assets/index.android.bundle.map
```

> 内测阶段发现的问题密度，与线上问题密度呈强正相关。内测发现的 bug 越多，线上出的 bug 越少。这不是因为"bug 总量是固定的"，而是因为充分的内测暴露了代码中的薄弱环节。害怕内测发现问题而不敢充分测试，是最危险的心态。问题早发现早修复，成本最低、影响最小。

### 15.4.5 内测版本迭代与灰度策略

内测不是一轮就结束的。通常需要 2-3 轮内测迭代，每轮聚焦不同的测试目标。第一轮内测覆盖全功能，找出明显的功能缺陷和崩溃。第二轮内测聚焦第一轮发现的问题修复验证，同时补充兼容性测试。第三轮内测进行验收测试，确认所有已知问题已修复，没有引入新问题。

灰度策略在内测阶段同样适用。对于用户基数较大的 APP，可以先在内部团队中灰度（dogfood），再扩展到种子用户，最后全量发布。每一级灰度都设置观察期（通常 24-48 小时），监控崩溃率和用户反馈，无异常再进入下一级。

```
灰度发布策略：

第一级: 内部团队 (10-50人) -> 观察24h
    |
    v
第二级: 种子用户 (1-5%) -> 观察48h
    |
    v
第三级: 扩大灰度 (10-30%) -> 观察72h
    |
    v
第四级: 全量发布 (100%)
```

每一级灰度的退出标准应该提前定义。比如：崩溃率低于 0.1%、无 P0（Priority 0）级别未修复问题、用户负反馈率低于 5%。不满足退出标准则暂停灰度，修复问题后重新评估。

## 15.5 双端应用商店上架流程

### 15.5.1 安卓应用市场上架资料准备

Android 应用市场上架需要准备一系列资料，不同市场的要求略有差异，但核心资料基本一致。

基础资料清单：

应用名称和副标题。应用名称需要与 APP 内显示名称一致，副标题用一句话描述应用核心功能。避免在名称中堆砌关键词，部分市场会视为违规。

应用描述和更新说明。应用描述控制在 100-500 字，突出核心功能和用户价值。更新说明列出版本更新内容，用用户能理解的语言描述，不要写技术实现细节。

应用图标和截图。图标尺寸通常要求 512x512 像素的 PNG 图片。截图至少提供 3-5 张，尺寸不小于 1080x1920 像素。截图应该是 APP 真实界面的高质量截图，不要用概念图或设计稿。

隐私政策 URL。所有主流 Android 市场都要求提供隐私政策链接。隐私政策需要说明 APP 收集哪些用户数据、如何使用、如何存储、用户如何行使数据权利。隐私政策不符合规范是上架被拒的高频原因。

应用分类和内容分级。根据 APP 实际功能选择分类，按照内容分级问卷如实填写。错误的内容分级可能导致 APP 被下架。

权限说明。列出 APP 申请的所有敏感权限及其用途。Android 的权限说明需要在应用描述中说明，部分市场还要求单独填写权限说明表。

> 应用商店上架资料看起来是"行政工作"，但它直接影响审核通过率和用户转化率。应用描述写得再好不如截图质量高，用户在应用商店的决策往往在前 3 秒内完成。花时间打磨截图和描述，不是浪费时间，而是提升获客效率。

### 15.5.2 主流安卓市场提审与发布流程

国内 Android 市场分散，需要逐个上架。主流市场包括：华为应用市场、小米应用商店、OPPO 软件商店、vivo 应用商店、应用宝（腾讯）、Google Play。

各市场的提审流程大同小异：注册开发者账号 -> 提交应用资料 -> 上传 APK -> 等待审核 -> 审核通过后发布。

```
Android 多市场上架流程：

[准备通用资料] -> [按市场要求调整]
    |
    v
[华为应用市场] -- 审核周期: 1-3个工作日
[小米应用商店] -- 审核周期: 1-3个工作日
[OPPO软件商店] -- 审核周期: 1-2个工作日
[vivo应用商店] -- 审核周期: 1-2个工作日
[应用宝]      -- 审核周期: 1-3个工作日
[Google Play] -- 审核周期: 1-7个工作日
```

各市场的特殊要求需要注意。华为应用市场对隐私权限审核非常严格，需要提供权限使用说明和第三方 SDK 列表。Google Play 要求 `targetSdkVersion` 满足最低要求，且需要提交数据安全声明（Data Safety Form）。部分国内市场要求提供软著证书（软件著作权登记证书），建议提前申请。

上架后的版本管理。每次发布新版本时，构建号必须递增。如果使用多渠道分发，建议使用 Gradle 的 `productFlavors` 或 `Walle`（美团的多渠道打包工具）生成不同渠道的 APK，方便追踪各渠道的下载数据。

### 15.5.3 App Store上架资料与规格要求

App Store 的上架资料要求比 Android 市场更严格更详细。在 App Store Connect 中需要填写以下信息。

应用基本信息。名称（最多 30 个字符）、副标题（最多 30 个字符）、描述（最多 4000 个字符）、关键词（最多 100 个字符，逗号分隔）、推广文本（最多 170 个字符，可不填）。

截图和预览视频。需要提供 6.7 寸（iPhone 15 Pro Max）和 6.5 寸（iPhone 11 Pro Max）两套截图，每套 3-10 张。可选提供 5.5 寸和 iPad 截图。截图格式为 PNG 或 JPEG，不带透明通道。预览视频可选 1-3 个，每个 15-30 秒。

应用分类。主分类和可选的副分类，分类影响 APP 在 App Store 中的曝光位置。选择与 APP 核心功能最匹配的分类。

年龄分级。根据 APP 内容填写分级问卷，包括暴力、色情、赌博、恐怖等内容元素。RN 项目如果包含 Web View 展示用户生成内容（UGC，User Generated Content），通常会被标记为 17+ 分级。

隐私说明。App Store 要求填写隐私实践声明，包括：APP 收集哪些数据（姓名、邮箱、位置、ID 等）、数据用途、是否与第三方共享、数据保留期限。声明与实际行为不一致会被 Apple 下架。

构建版本。上传的 IPA 包在 App Store Connect 中显示为构建版本，每次提审需要选择一个构建版本。构建版本上传后 90 天内有效，超过 90 天需要重新上传。

### 15.5.4 iOS提审流程与审核规则规避

iOS 提审在 App Store Connect 中完成。提审流程：选择 APP -> 选择构建版本 -> 填写审核信息 -> 提交审核。审核信息包括审核备注（给审核员的说明）、演示账号（如果 APP 需要登录）、联系信息。

审核周期通常为 24-48 小时，首次提审可能需要 3-5 个工作日。审核状态变化会通过邮件通知。

Apple 审核指南（App Store Review Guidelines）是提审前必读的文档。以下是高频被拒原因及规避方案。

**被拒原因一：功能不完整或存在明显 bug**

审核员会实际操作 APP 验证功能。如果核心功能不可用、页面白屏、按钮无响应，直接被拒。规避方案：提审前在真机上完整走一遍核心流程，确保所有入口可达、功能可用。

**被拒原因二：隐私政策不符合要求**

隐私政策缺失、内容不完整、与 APP 实际行为不符。规避方案：使用专业的隐私政策生成工具，确保覆盖所有收集的数据类型。如果 APP 使用了 IDFA（Identifier for Advertising），必须在隐私政策中说明。

**被拒原因三：权限说明不充分**

`NSCameraUsageDescription` 等权限说明文案写得太笼统或为空。规避方案：权限说明必须具体，例如"需要使用相机拍摄商品照片用于发布"而不是"需要使用相机"。

**被拒原因四：使用了私有 API 或违规功能**

RN 项目中第三方库可能调用了 Apple 禁止的私有 API。规避方案：提审前检查所有第三方库的权限使用，移除不必要的敏感权限调用。

**被拒原因五：重复提交或刷量**

多次提交内容相同的 APP 会被视为刷量行为。规避方案：每次提审确保有实质性的功能更新或 bug 修复，不要为了"刷新曝光"而频繁提交。

> App Store 审核不是不可预测的黑盒。审核指南白纸黑字写得清清楚楚，被拒的绝大多数原因都能在指南中找到对应条款。提审前对照审核指南逐条自查，被拒概率可以降低 80%。怕的是不看指南凭感觉提审，被拒了还不知道为什么。

### 15.5.5 上架驳回问题排查与修改方案

被驳回不可怕，可怕的是不知道为什么被驳回以及如何修改。Apple 的驳回通知会附上具体的 Guideline 条款和审核员的说明，仔细阅读是修改的第一步。

**Guideline 2.1 - Performance: App Crashes**

APP 在审核过程中崩溃。这是最严重的驳回原因。审核员会提供崩溃日志，需要分析崩溃原因。常见原因：生产环境 API 地址配置错误、第三方 SDK 在 Release 模式下行为异常、设备兼容性问题。修复方案：根据崩溃日志定位问题，在本地用 Release 包复现并修复，重新打包提审。

**Guideline 2.5.1 - Performance: Software Requirements**

使用了废弃的技术或 API。例如 APP 中使用了 UIWebView（已废弃的 WebView 组件），会被拒绝。修复方案：全局搜索替换为 WKWebView，包括第三方库中的使用。

**Guideline 4.2 - Design: Minimum Functionality**

APP 功能过于简单，被判定为"没有足够的功能价值"。这类驳回常见于工具类或内容展示类 APP。修复方案：增加 APP 的功能深度，丰富内容，提供更完整的用户体验。在审核备注中详细说明 APP 的核心价值。

**Guideline 5.1.1 - Legal: Privacy - Data Collection and Storage**

数据收集和隐私实践不符合要求。修复方案：更新隐私政策，确保隐私实践声明与 APP 实际行为完全一致。如果 APP 接入了第三方广告 SDK，需要说明第三方 SDK 收集的数据。

每次被驳回后，可以在 App Store Connect 的 Resolution Center 中与审核团队沟通。沟通时态度诚恳、回复具体、修改明确，不要与审核员争论。如果确信审核结果有误，可以提交申诉（Appeal），但申诉前务必确认自己的 APP 确实没有违规。

## 15.6 热更新与版本迭代管控

### 15.6.1 RN热更新核心原理与优势

热更新是 RN 相对于原生开发的一个显著优势。原理很简单：RN 的业务逻辑写在 JS Bundle 中，JS Bundle 是一个独立的文件，可以在 APP 运行时从服务器下载替换。这意味着不需要通过应用商店发布新版本，就能修复 bug 和更新功能。

```
热更新原理对比：

原生APP更新流程:
  修改代码 -> 编译打包 -> 提交商店 -> 审核等待 -> 用户手动更新
  周期: 3-7天 (iOS更长)

RN热更新流程:
  修改JS代码 -> 打包Bundle -> 推送到服务器 -> APP自动下载替换
  周期: 几分钟到几小时
```

热更新的优势体现在三个场景。第一，紧急 bug 修复。线上发现崩溃，不需要等商店审核，几分钟内推送热更新即可修复。第二，小功能迭代。UI 调整、文案修改等非原生变更，通过热更新即时发布。第三，A/B 测试。向不同用户推送不同版本的 JS Bundle，验证功能效果。

但热更新也有明确的边界。只能更新 JS 层代码和 JS 层资源（图片、JSON 文件），不能更新原生代码。涉及原生模块变更、新增权限、修改 APP 核心配置的更新，必须走商店发布流程。Apple 对热更新有严格的政策限制：不能通过热更新改变 APP 的核心功能和用途，不能使用热更新绕过审核发布违规内容。使用 CodePush（Microsoft 提供的 RN 热更新服务）是 App Store 允许的热更新方案，因为它只更新 JS Bundle，不执行动态代码注入。

> 热更新是双刃剑。用好了是线上救火的神器，用不好是线上事故的源头。最危险的做法是热更新不做灰度、不做回滚、全量推送。一次有 bug 的全量热更新，可以在几分钟内让所有用户看到白屏。热更新必须配合灰度发布和自动回滚机制，这不是可选的，是必须的。

### 15.6.2 CodePush热更新环境搭建

CodePush 是 RN 生态中最成熟的热更新方案，由 Microsoft 提供，现为 App Center 的一部分。

安装和配置 CodePush CLI（Command Line Interface）：

```bash
# 安装 CodePush CLI
npm install -g appcenter-cli

# 登录 App Center
appcenter login

# 创建应用 (Android和iOS分别创建)
appcenter apps create -d MyApp-Android -o Android -p React-Native
appcenter apps create -d MyApp-iOS -o iOS -p React-Native
```

在 RN 项目中安装 CodePush SDK：

```bash
npm install react-native-code-push
```

Android 端配置。在 `MainApplication.java` 中配置 CodePush：

```java
// android/app/src/main/java/.../MainApplication.java
@Override
protected List<ReactPackage> getPackages() {
    return Arrays.asList(
        new MainReactPackage(),
        new CodePush(
            "deployment_key_here",
            getApplicationContext(),
            BuildConfig.DEBUG,
            "https://codepush.appcenter.ms"
        )
    );
}
```

iOS 省端配置在 `AppDelegate.m` 中：

```objc
// ios/MyApp/AppDelegate.m
#import <CodePush/CodePush.h>

- (NSURL *)sourceURLForBridge:(RCTBridge *)bridge {
    return [CodePush bundleURL];
}
```

JS 层通过 HOC（Higher-Order Component）包装根组件：

```js
import codePush from 'react-native-code-push';

const codePushOptions = {
  checkFrequency: codePush.CheckFrequency.ON_APP_RESUME,
  installMode: codePush.InstallMode.ON_NEXT_RESTART,
  mandatoryInstallMode: codePush.InstallMode.IMMEDIATE,
};

const App = () => <AppRoot />;
export default codePush(codePushOptions)(App);
```

`checkFrequency` 控制检查更新的时机：`ON_APP_START` 在 APP 启动时检查，`ON_APP_RESUME` 在 APP 从后台恢复时检查，`MANUAL` 手动检查。`installMode` 控制安装时机：`ON_NEXT_RESTART` 下次启动时安装，`IMMEDIATE` 立即安装（会重启 APP），`ON_NEXT_RESUME` 下次从后台恢复时安装。

### 15.6.3 静默更新与弹窗更新配置

热更新的用户体验设计很关键。静默更新对用户无感知但需要重启才能生效，弹窗更新可以即时生效但会打断用户。

静默更新适合小规模 bug 修复和不影响用户操作的更新。配置 `installMode: ON_NEXT_RESTART`，APP 在后台下载更新包，下次启动时自动加载新版本。用户完全无感知。

弹窗更新适合重要功能更新或需要用户感知的变更。在 JS 层手动检查更新并弹窗提示：

```js
import codePush from 'react-native-code-push';

async function checkForUpdate() {
  try {
    const update = await codePush.checkForUpdate();
    if (!update) {
      Alert.alert('已是最新版本');
      return;
    }
    const isMandatory = update.isMandatory;
    Alert.alert(
      '发现新版本',
      update.description || '发现新版本，是否更新？',
      [
        { text: '取消', onPress: () => {} },
        {
          text: '更新',
          onPress: () => {
            codePush.sync(
              { installMode: codePush.InstallMode.IMMEDIATE },
              syncStatus => handleSyncStatus(syncStatus),
              progress => showProgress(progress)
            );
          },
        },
      ],
      { cancelable: !isMandatory }
    );
  } catch (e) {
    console.warn('检查更新失败', e);
  }
}
```

强制更新场景。当发现线上存在严重 bug 需要所有用户立即更新时，在 CodePush 后台发布时勾选 "Mandatory release"。JS 层检测到 `isMandatory` 为 true 时，不提供取消按钮，强制用户更新后才能继续使用 APP。

更新进度展示。通过 `codePush.sync` 的进度回调展示下载进度：

```js
function showProgress(progress) {
  const percent = Math.round(
    (progress.receivedBytes / progress.totalBytes) * 100
  );
  // 更新进度条UI
  setUpdateProgress(percent);
}
```

### 15.6.4 热更新灰度发布与回滚方案

CodePush 支持灰度发布，可以指定百分比的用户接收更新。灰度发布是热更新的安全网，没有灰度策略的热更新等同于在生产环境裸奔。

发布灰度更新：

```bash
# 发布热更新, 灰度 20%
appcenter codepush release \
  -a "OrgName/MyApp-Android" \
  -d Production \
  -t "1.2.0" \
  -d "Production" \
  --rollout 20 \
  --description "修复首页白屏问题"
```

`--rollout 20` 表示只有 20% 的用户会收到这次更新。观察一段时间无异常后，可以提升到 100%：

```bash
# 提升灰度到 100%
appcenter codepush promote \
  -a "OrgName/MyApp-Android" \
  -s Staging \
  -d Production \
  --rollout 100
```

回滚操作。如果灰度更新发现问题，可以立即回滚到上一个版本：

```bash
# 回滚到上一个版本
appcenter codepush rollback \
  -a "OrgName/MyApp-Android" \
  -d Production \
  --target-release v10
```

回滚后，已经安装了有问题版本的用户会在下次检查更新时自动回滚到上一个稳定版本。回滚操作是即时的，不需要用户手动操作。

完整的灰度发布流程应该是：

```
[Staging环境验证] -> 通过后Promote到Production
    |
    v
[Production灰度5%] -> 观察2-4小时
    |  无异常           有异常 -> 回滚
    v
[提升到20%] -> 观察4-8小时
    |  无异常           有异常 -> 回滚
    v
[提升到100%] -> 全量发布
```

> 灰度发布的黄金法则：永远不要相信"我觉得没问题"。代码在你机器上跑得再好，到了十万用户的真实环境中总会出现你没预料到的边界情况。灰度不是为了"万一出问题"，而是"一定会出问题，只是要控制爆炸半径"。5% 的用户出问题叫事故，100% 的用户出问题叫灾难。

### 15.6.5 版本兼容与强制更新逻辑实现

热更新只解决了 JS 层的迭代问题，但涉及原生层变更时仍然需要通过商店发布新版本。这就带来了版本兼容性问题：不同用户可能运行着不同的原生版本，每个原生版本可能有不同的 JS Bundle 版本。

CodePush 通过 `targetBinaryVersion` 参数控制版本兼容性。发布热更新时指定 `targetBinaryVersion` 为 `~1.2.0`，表示这个更新包只适用于原生版本 1.2.x 的 APP。版本不匹配的用户不会收到这个更新。

强制更新场景。当新版本 APP 包含 breaking change（不兼容的变更），需要所有用户升级到最新原生版本时，需要实现强制更新逻辑。在服务端维护一个最低支持版本号，APP 启动时检查当前版本是否满足要求：

```js
async function checkAppVersion() {
  const res = await api.get('/app/version-check', {
    params: { platform: Platform.OS, version: DeviceInfo.getVersion() },
  });
  const { minVersion, latestVersion, updateUrl, forceUpdate } = res.data;

  if (forceUpdate) {
    // 强制更新: 不可关闭的弹窗
    showForceUpdateModal({
      title: '版本过低，需要更新',
      message: '当前版本已无法使用，请更新到最新版本',
      url: updateUrl,
      mandatory: true,
    });
  } else if (compareVersion(latestVersion, DeviceInfo.getVersion()) > 0) {
    // 非强制更新: 可关闭的弹窗
    showUpdateModal({
      title: '发现新版本',
      message: '更新内容: ...',
      url: updateUrl,
      mandatory: false,
    });
  }
}
```

版本比较逻辑要严谨，不能简单用字符串比较。`1.10.0` 应该大于 `1.9.0`，但字符串比较的结果是反的。使用 `semver`（Semantic Versioning）库进行版本比较：

```js
import semver from 'semver';

// 检查当前版本是否满足最低要求
const needsUpdate = semver.lt(currentVersion, minVersion);
// 检查是否有新版本
const hasNewVersion = semver.lt(currentVersion, latestVersion);
```

版本迭代管控的整体策略。将热更新和商店版本更新结合使用，形成多层次版本管理：商店版本负责大功能迭代和原生层变更，热更新负责 bug 修复和小功能调整。每个商店版本有自己的热更新通道，不同商店版本的 JS Bundle 互不干扰。

建立版本发布日志机制，记录每次热更新和商店发布的变更内容、发布时间、灰度比例、问题记录。这份日志是版本回溯和问题排查的重要依据，也是团队版本管理的知识沉淀。

## 结语

打包发布是 RN 项目从开发到用户的最后一公里，也是最容易翻车的一段路。从环境体系搭建到双端签名配置，从内测分发验证到应用商店上架，从热更新灰度到版本迭代管控，每一个环节都需要严谨的流程和可复用的脚本。这一章覆盖了打包发布的全链路，从 Android 签名到 iOS Archive，从 TestFlight 内测到 App Store 提审，从 CodePush 热更新到强制版本升级，帮你建立完整的打包发布能力。

打包发布的核心不是记住每一步的操作步骤，而是理解每一步为什么这么做、出了问题从哪里排查。当你能独立走通从代码到用户手机的全流程，并且遇到任何环节的问题都能快速定位修复，你就真正具备了 RN 全栈工程能力。

**收藏这篇文章**，下次打包发布时当作检查清单逐项对照，能帮你避免 90% 的打包踩坑。

**在评论区聊聊**你的第一次上架经历，是被驳回三次还是一次过审？Android 多市场分发你用了什么方案？

**系列进度 15/16**。下一章也是最后一章，我会讲解 RN 项目的工程化体系与团队协作规范，包括代码规范、CI/CD 流水线搭建、自动化测试、团队协作流程等内容，帮你从个人开发走向团队工程化。

怕浪猫说：打包这件事，做一百次都会紧张，因为每一次发布都是对用户的承诺。但紧张不是焦虑，紧张是对质量的敬畏。把流程跑通、把脚本写好、把灰度做好，剩下的就交给代码和质量保障体系。怕的不是出问题，怕的是出了问题不知道怎么回滚。做好回滚预案，你就有底气面对任何发布。

系列进度 15/16
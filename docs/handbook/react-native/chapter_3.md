# 第3章 RN核心组件、Flex布局与屏幕适配

90%的RN新手在第一周就会踩同一个坑：写出来的页面在不同手机上歪七扭八，文本溢出、图片变形、按钮点不动。不是你代码写得不对，是你还没真正理解RN的组件体系和布局引擎。从View到FlatList，从Flex到安全区适配，这一章帮你把地基打牢。

我是怕浪猫，一个在RN坑里摸爬滚打了多年的开发者。上一章我们搞定了基础语法和调试技巧，这一章进入更核心的领域——RN组件、布局与屏幕适配。这些东西看着基础，但决定了你后续所有页面的质量上限。很多开发者写了两年RN还在踩布局的坑，根本原因就是这一章的内容没有吃透。

## 3.1 RN基础核心组件全解

RN（React Native）的组件库和Web端的HTML标签完全不同。Web开发者刚转RN时最容易犯的错误，就是拿div、span、img的思维去写RN代码。RN不运行在浏览器里，没有DOM（Document Object Model），所有UI（User Interface）组件最终都会映射到原生的Android View和iOS UIView。

这一点非常关键：你写的每一个`<View>`，在Android上变成`android.view.View`，在iOS上变成`UIView`。不是模拟，不是模拟器里的伪装，是真正的原生渲染。理解了这个映射关系，你就能明白为什么RN组件的属性和HTML标签差别那么大——因为它们本质上是在操作两套完全不同的原生UI系统。

### 3.1.1 View容器组件属性与布局特性

View是RN中最基础的容器组件，相当于Web中的div，但能力范围完全不同。View不支持伪元素（没有`::before`和`::after`），不支持CSS（Cascading Style Sheets）动画过渡，不支持box-shadow的外阴影（但支持elevation阴影）。它就是一个纯粹的矩形容器，所有的视觉效果都需要通过style属性来实现。

View的核心属性并不多，但每一个都值得认真对待：

| 属性 | 类型 | 说明 |
|------|------|------|
| style | ViewStyle | 样式对象，支持布局、边框、背景等 |
| onTouchStart/onTouchEnd | function | 触摸事件回调 |
| pointerEvents | string | 控制触摸事件穿透行为 |
| accessible | boolean | 是否可被无障碍服务访问 |
| hitSlop | object | 扩大点击响应区域 |
| removeClippedSubviews | boolean | 是否裁剪不可见子视图 |

实际开发中，`hitSlop`是一个被严重低估的属性。当按钮区域太小（比如20x20），用户很难精确点击，特别是在行走、颠簸等场景下。设置`hitSlop={{top: 10, bottom: 10, left: 10, right: 10}}`可以在不改变视觉尺寸的前提下，把可点击区域扩大到40x40。苹果的HIG（Human Interface Guidelines）推荐最小可点击区域为44x44点，所以任何小于这个尺寸的可点击元素都应该设置hitSlop。

```jsx
// View容器基础用法
import { View, StyleSheet } from 'react-native';

export const Card = ({ children }) => {
  return (
    <View style={styles.card} hitSlop={{ top: 10, bottom: 10 }}>
      <View style={styles.header} />
      <View style={styles.content}>
        {children}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    overflow: 'hidden',
  },
  header: {
    height: 4,
    backgroundColor: '#1890ff',
  },
  content: {
    padding: 16,
  },
});
```

`pointerEvents`属性也很实用。值为`'none'`时，View本身及其所有子组件都不响应触摸，事件会穿透到下层组件；值为`'box-none'`时，View自身不响应但子组件可以响应；值为`'auto'`时正常响应。这在做覆盖层、水印层、调试浮层时非常有用——你想在上层盖一个半透明的遮罩，但又不想让遮罩拦截下层的点击事件。

View的`overflow`属性控制内容溢出行为。值为`'hidden'`时裁剪溢出内容，值为`'visible'`时允许内容超出容器边界显示。默认值在iOS上是`'visible'`，在Android上是`'hidden'`——没错，两个平台默认行为不一致。如果需要统一表现，请显式设置。

> 怕浪猫踩坑提醒：View的`overflow: 'hidden'`在Android上对性能有明显影响，特别是在滚动列表中。因为裁剪需要额外创建一个离屏渲染缓冲区。如果不需要裁剪内容，千万别顺手加上。

### 3.1.2 Text文本组件排版与样式规范

Text组件是RN中唯一能渲染文字的组件。和Web不同，RN没有`<span>`、`<p>`、`<h1>`这些语义化标签，所有文字都必须放在Text组件内。直接在View里写文字会直接报错——这是RN新手第一个红屏错误。

Text组件有一个特殊行为：嵌套的Text会继承父Text的样式。这在实现富文本时非常有用，也是和Web最大的区别之一。Web中`<span>`不会自动继承父级`<span>`的全部样式（比如字体大小会被重置），但RN中嵌套Text会完整继承父Text的字号、颜色、行高等样式：

```jsx
import { Text, StyleSheet } from 'react-native';

export const RichText = () => {
  return (
    <Text style={styles.base}>
      这是一段普通文字，
      <Text style={styles.bold}>加粗文字</Text>
      和
      <Text style={styles.link} onPress={() => {}}>
        可点击的链接文字
      </Text>
    </Text>
  );
};

const styles = StyleSheet.create({
  base: { fontSize: 14, color: '#333', lineHeight: 22 },
  bold: { fontWeight: '700' },
  link: { color: '#1890ff', textDecorationLine: 'underline' },
});
```

Text组件的`numberOfLines`属性配合`ellipsizeMode`可以控制文本截断行为。`ellipsizeMode`支持`'head'`、`'middle'`、`'tail'`、`'clip'`四种模式，默认是`'tail'`，即在末尾显示省略号。这在做商品标题、消息摘要等场景非常常用：

```jsx
<Text numberOfLines={2} ellipsizeMode="tail">
  这是一段很长的商品标题文字，当超过两行时会在末尾显示省略号
</Text>
```

实际项目中，文本溢出截断是最常见的坑之一。iOS和Android的默认截断行为不一致，Android某些版本在`numberOfLines`截断时会出现文字被裁切一半的情况——明明设置了2行，但第2行的文字只显示了一半就被裁掉了。解决方案是给Text组件设置明确的`lineHeight`值，确保行高是`fontSize`的1.2-1.5倍。比如fontSize为14时，lineHeight建议设为20-22。

另一个常见问题是Text在Flex布局中被异常压缩。当Text位于一个`flexDirection: 'row'`的容器中时，如果文字过长，文字会被压缩到一行甚至超出容器。解决方案是给Text设置`flexShrink: 1`，让它可以正常换行：

```jsx
<View style={{ flexDirection: 'row' }}>
  <Text style={{ flexShrink: 1 }}>这段很长的文字可以正常换行了</Text>
</View>
```

> 金句：组件不是越复杂越好，而是越可控越好。View和Text看似简单，但它们属性组合出的行为差异，足够让你调试一整天。

### 3.1.3 Image图片资源加载与适配方案

Image组件在RN中的用法和Web的`<img>`标签差异很大。RN中的Image支持三种图片来源：本地静态资源、网络URL和Base64编码数据。每种来源的写法不同，加载机制也不同。

```jsx
import { Image } from 'react-native';

// 本地静态资源 - 编译时确定路径，打包后直接内嵌
<Image source={require('./logo.png')} style={{ width: 100, height: 100 }} />

// 网络图片 - 运行时加载，需要网络权限
<Image
  source={{ uri: 'https://example.com/avatar.png' }}
  style={{ width: 80, height: 80 }}
/>

// Base64 - 适合小图标，避免额外网络请求
<Image
  source={{ uri: 'data:image/png;base64,iVBORw0KGgo...' }}
  style={{ width: 40, height: 40 }}
/>
```

这里有一个新手必踩的坑：网络图片必须设置宽高，否则显示为0。Web中`<img>`会根据图片自身尺寸自动计算宽高，但RN中Image组件默认宽高为0。这是因为RN在图片加载完成前不知道尺寸，而原生渲染需要明确的布局参数。如果图片还没加载完就需要占位，可以使用`defaultSource`属性设置占位图。

如果需要根据图片实际尺寸自适应，可以使用`Image.getSize`方法在加载前获取尺寸：

```jsx
Image.getSize(uri, (width, height) => {
  setImageSize({ width, height });
}, (error) => {
  console.warn('图片加载失败', error);
});
```

但这种方式会导致页面闪烁——先显示空白，加载完成后再显示图片。更好的方案是使用`resizeMode`属性配合固定容器尺寸，让图片在固定容器内以合适的方式显示：

| resizeMode | 行为 | 适用场景 |
|------------|------|---------|
| cover | 填充容器，可能裁剪，不变形 | 头像、封面图、banner |
| contain | 完整显示，可能留白，不变形 | 产品图、截图展示 |
| stretch | 拉伸填满，可能变形 | 几乎不用 |
| repeat | 平铺重复（仅iOS） | 背景纹理 |
| center | 居中显示，不缩放 | 原尺寸图标 |

实际项目中，`cover`是最常用的模式，适合做头像、封面图等需要填满容器的场景。`contain`适合做商品详情图等需要完整展示的场景。两者都不会变形，区别只在裁剪还是留白。

Image组件还支持`onLoad`、`onLoadEnd`、`onError`等回调，可以用来实现加载状态管理：

```jsx
const [loaded, setLoaded] = useState(false);

<Image
  source={{ uri: imageUrl }}
  style={styles.image}
  onLoadStart={() => setLoading(true)}
  onLoadEnd={() => setLoading(false)}
  onError={(e) => console.warn('加载失败', e.nativeEvent.error)}
/>
```

### 3.1.4 TextInput输入框基础交互实现

TextInput是RN中最复杂的组件之一。它看起来简单——不就是一个输入框嘛，但涉及键盘交互、光标控制、文本选择、自动补全、输入校验等大量细节。很多团队在封装输入框组件上花的时间，比封装其他所有组件加起来都多。

先看一个基础登录输入框的封装：

```jsx
import { TextInput, View, Text, StyleSheet } from 'react-native';

export const Input = ({ label, value, onChangeText, placeholder, secure }) => {
  return (
    <View style={styles.wrapper}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        secureTextEntry={secure}
        placeholderTextColor="#bbb"
        autoCapitalize="none"
        autoCorrect={false}
        clearButtonMode="while-editing"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: { marginBottom: 16 },
  label: { fontSize: 14, color: '#333', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    paddingHorizontal: 12,
    height: 44,
    fontSize: 15,
    color: '#333',
  },
});
```

几个关键属性需要特别注意：

`autoCapitalize`控制自动大写行为，值为`'none'`时关闭自动大写，在输入用户名、邮箱时必须设置，否则iOS默认会首字母大写，导致用户名变成"Admin"而不是"admin"。值为`'sentences'`时每句首字母大写，值为`'words'`时每个单词首字母大写，值为`'characters'`时全部大写。

`keyboardType`控制键盘类型，常用值有`'default'`、`'numeric'`、`'email-address'`、`'phone-pad'`、`'number-pad'`。设置正确的键盘类型能显著提升用户体验——输入手机号时弹出数字键盘，输入邮箱时弹出带@符号的键盘，这些都是移动端交互的基本规范。

`returnKeyType`控制回车键的文案，值为`'done'`、`'go'`、`'search'`、`'next'`、`'send'`等。配合`onSubmitEditing`回调可以实现"点击下一步跳到下一个输入框"的交互，这在登录页、注册页非常常用。

`blurOnSubmit`在Android上行为和iOS不同。Android默认为`false`（回车不收起键盘），iOS默认为`true`。如果需要统一行为，建议显式设置。

`clearButtonMode`仅iOS有效，值为`'while-editing'`时在输入框右侧显示清除按钮。Android没有这个原生能力，需要自己实现——在TextInput右侧放一个清除图标，点击时清空value。

### 3.1.5 基础组件组合简单页面实战

把前面几个组件组合起来，写一个完整的登录页面。这个页面会用到View容器、Text文本、Image图片、TextInput输入框和TouchableOpacity按钮，还要处理键盘遮挡和安全区域：

```jsx
import React, { useState, useRef } from 'react';
import { View, Text, Image, TextInput, TouchableOpacity,
  StyleSheet, SafeAreaView, KeyboardAvoidingView, Platform,
  ScrollView, Alert } from 'react-native';

export const LoginPage = () => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const passwordRef = useRef(null);

  const handleLogin = () => {
    if (!phone.trim()) {
      Alert.alert('提示', '请输入手机号');
      return;
    }
    if (!password) {
      Alert.alert('提示', '请输入密码');
      return;
    }
    // 登录逻辑
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.content}
      >
        <ScrollView showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}>
          <Image source={require('./logo.png')} style={styles.logo} />
          <Text style={styles.title}>欢迎登录</Text>
          <TextInput
            style={styles.input}
            value={phone}
            onChangeText={setPhone}
            placeholder="请输入手机号"
            keyboardType="phone-pad"
            returnKeyType="next"
            onSubmitEditing={() => passwordRef.current?.focus()}
          />
          <TextInput
            ref={passwordRef}
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            placeholder="请输入密码"
            secureTextEntry
            returnKeyType="go"
            onSubmitEditing={handleLogin}
          />
          <TouchableOpacity
            style={styles.btn}
            onPress={handleLogin}
            activeOpacity={0.8}
          >
            <Text style={styles.btnText}>登录</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { flex: 1 },
  scrollContent: { paddingHorizontal: 24, paddingTop: 80 },
  logo: { width: 80, height: 80, alignSelf: 'center', marginBottom: 20 },
  title: { fontSize: 24, fontWeight: '700', textAlign: 'center', marginBottom: 32 },
  input: { height: 48, backgroundColor: '#fff', borderRadius: 8,
    paddingHorizontal: 14, marginBottom: 16, fontSize: 15 },
  btn: { height: 48, backgroundColor: '#1890ff', borderRadius: 8,
    justifyContent: 'center', alignItems: 'center' },
  btnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
```

这个页面值得仔细拆解。`SafeAreaView`处理顶部刘海和底部Home Indicator的安全区域。`KeyboardAvoidingView`在iOS上处理键盘弹出时的自动偏移——`behavior: 'padding'`会让整个内容区域上移，避免输入框被键盘遮挡。`ScrollView`确保在小屏手机上内容可以滚动。两个TextInput通过`ref`和`onSubmitEditing`实现了"手机号输入完后点下一步自动聚焦密码框"的交互。

> 金句：学组件不是背API，而是理解每个属性背后的设计意图。`autoCapitalize`不是冗余配置，而是移动端交互规范的体现。`returnKeyType`不是锦上添花，而是用户操作流程的关键一环。

## 3.2 触控交互与点击组件实战

Web端点击用`onClick`，RN里可不一样。移动端的交互比鼠标复杂得多：按下、抬起、长按、滑动，每种手势都需要精确处理。而且手指比鼠标指针大得多，触摸精度远不如鼠标点击，这些都要求RN有更完善的触控方案。

RN提供了多套触控组件方案——从早期的Touchable系列到新一代的Pressable，选对方案是写出好交互的第一步。

### 3.2.1 TouchableOpacity透明点击组件

TouchableOpacity是最常用的点击组件，也是RN历史最悠久的触控组件之一。它的交互效果是按下时透明度降低（默认从1降到0.2），松手恢复。这种反馈方式自然、流畅，适合大多数点击场景。

```jsx
import { TouchableOpacity, Text, StyleSheet } from 'react-native';

export const Button = ({ title, onPress, disabled }) => {
  return (
    <TouchableOpacity
      style={[styles.btn, disabled && styles.btnDisabled]}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.7}
    >
      <Text style={styles.text}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  btn: {
    height: 44,
    backgroundColor: '#1890ff',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  btnDisabled: { backgroundColor: '#ccc' },
  text: { color: '#fff', fontSize: 16, fontWeight: '500' },
});
```

`activeOpacity`控制按下时的透明度，默认0.2，建议设为0.6-0.8，视觉反馈更柔和。0.2太透明了，按下时几乎看不到按钮，用户会疑惑"我是不是没按到"。`disabled`为`true`时禁用点击，同时`onPress`不会触发，按钮也不会有按下效果。

### 3.2.2 TouchableHighlight高亮点击组件

TouchableHighlight的交互效果是按下时显示一个高亮背景色。相比TouchableOpacity，它多了一个`underlayColor`属性来控制按下时的背景色。这种反馈方式更适合列表项——按下时整行变色，视觉反馈更强烈。

```jsx
<TouchableHighlight
  style={styles.listItem}
  underlayColor="#e6f7ff"
  onPress={handlePress}
>
  <View style={styles.itemContent}>
    <Text style={styles.itemTitle}>列表项标题</Text>
    <Text style={styles.itemDesc}>列表项描述</Text>
  </View>
</TouchableHighlight>
```

TouchableHighlight有一个常见的坑：如果设置了`borderRadius`，按下时的高亮色不会遵循圆角，会出现直角高亮区域。这是因为`underlayColor`是在原生层绘制的，不受CSS的borderRadius约束。解决方案是给TouchableHighlight本身设置`overflow: 'hidden'`，强制裁剪高亮区域。

另一个坑是TouchableHighlight必须有且只有一个子组件，而且这个子组件不能是纯文字——必须包在View或Text里。如果你直接写`<TouchableHighlight><Text>点击</Text></TouchableHighlight>`在某些Android版本上可能不会显示高亮效果。

### 3.2.3 Pressable高性能触控组件详解

Pressable是RN 0.63引入的新一代触控组件，官方推荐用它替代所有Touchable系列组件。Pressable的设计理念是"声明式触控状态管理"，让你能更灵活地控制不同触控状态下的UI表现。

```jsx
import { Pressable, Text, StyleSheet } from 'react-native';

export const PressableButton = ({ onPress, title }) => {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.btn,
        pressed && styles.btnPressed,
      ]}
      onPress={onPress}
      hitSlop={20}
      delayLongPress={500}
    >
      {({ pressed }) => (
        <Text style={[styles.text, pressed && styles.textPressed]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  btn: { height: 44, backgroundColor: '#1890ff', borderRadius: 8,
    justifyContent: 'center', alignItems: 'center' },
  btnPressed: { backgroundColor: '#096dd9' },
  text: { color: '#fff', fontSize: 16 },
  textPressed: { opacity: 0.8 },
});
```

Pressable的核心优势在于`style`和`children`都支持函数形式，接收一个包含`pressed`布尔值的对象。你可以根据按下状态动态调整任意样式，不仅仅是透明度——可以改变背景色、改变文字颜色、改变边框，甚至改变阴影深度。这是TouchableOpacity做不到的。

Pressable还支持以下事件回调：

- `onPressIn`：按下时触发（对应Web的onMouseDown/onTouchStart）
- `onPressOut`：抬起时触发（对应Web的onMouseUp/onTouchEnd）
- `onLongPress`：长按时触发
- `delayLongPress`：长按触发延迟（毫秒，默认500）

Pressable还提供了`onHoverIn`/`onHoverOut`回调，用于处理鼠标悬浮事件——这在平板设备和外接键盘场景下很有用。

> 金句：TouchableOpacity解决"能不能点"的问题，Pressable解决"点得漂不漂亮"的问题。新项目直接上Pressable，老项目逐步迁移。

### 3.2.4 点击防抖与防重复提交实现

移动端有一个经典的bug：用户快速双击提交按钮，导致请求发了两次，创建了两个订单。Web端可以用CSS的`pointer-events: none`解决，RN中没有这个能力，需要手动实现防抖。

时间防抖方案——用一个时间戳判断两次点击的间隔：

```jsx
import { useRef, useCallback } from 'react';

export const useDebouncePress = (callback, delay = 500) => {
  const lastPress = useRef(0);

  return useCallback(
    (...args) => {
      const now = Date.now();
      if (now - lastPress.current < delay) return;
      lastPress.current = now;
      callback(...args);
    },
    [callback, delay],
  );
};

// 使用
const handlePress = useDebouncePress(() => {
  submitForm();
}, 800);
```

这个Hook用`useRef`记录上次点击时间戳，在指定时间间隔内的重复点击直接忽略。800ms是一个比较合理的间隔，既能防抖又不影响正常使用。为什么用`useRef`而不是`useState`？因为ref的修改不会触发重新渲染，性能更好。

还有一种更严格的方案——加loading状态锁定，防止异步请求期间的重复提交：

```jsx
const [submitting, setSubmitting] = useState(false);

const handleSubmit = async () => {
  if (submitting) return;
  setSubmitting(true);
  try {
    await api.submit(data);
    navigation.navigate('Success');
  } catch (e) {
    Alert.alert('提交失败', e.message);
  } finally {
    setSubmitting(false);
  }
};
```

两种方案可以组合使用：时间防抖处理快速连点（防止手抖），状态锁处理异步请求期间的重复提交（防止网络延迟期间的用户重复操作）。实际项目中，建议把这两种防抖逻辑统一封装到按钮组件中，而不是在每个使用处都手动实现。

### 3.2.5 通用可点击组件二次封装

实际项目中，建议对Pressable做二次封装，统一交互规范。一个好的按钮组件应该支持多种类型、多种尺寸、loading状态、disabled状态、图标插槽等：

```jsx
import { Pressable, Text, StyleSheet, ActivityIndicator } from 'react-native';

export const AppButton = ({
  title, onPress, loading, disabled,
  type = 'primary', size = 'default',
}) => {
  const btnStyle = [
    styles.base,
    styles[type],
    styles[size],
    (disabled || loading) && styles.disabled,
  ];

  return (
    <Pressable
      style={({ pressed }) => [btnStyle, pressed && styles.pressed]}
      onPress={onPress}
      disabled={disabled || loading}
    >
      {loading ? (
        <ActivityIndicator color="#fff" size="small" />
      ) : (
        <Text style={styles[`${type}Text`]}>{title}</Text>
      )}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  base: { borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  primary: { backgroundColor: '#1890ff' },
  default: { height: 44, paddingHorizontal: 20 },
  small: { height: 32, paddingHorizontal: 12 },
  disabled: { backgroundColor: '#ccc' },
  pressed: { opacity: 0.8 },
  primaryText: { color: '#fff', fontSize: 16 },
});
```

这种封装方式统一了按钮的类型（primary/default/ghost）、尺寸（default/small/large）、状态（loading/disabled），项目里所有按钮都走这个组件，维护起来非常方便。当设计师说"所有按钮的圆角从8改成12"时，你只需要改一个文件。

> 金句：组件封装的本质不是减少代码量，而是收敛变化。当需求从"蓝色按钮"变成"渐变按钮"时，你只需要改一个文件，而不是全局搜索替换。

## 3.3 滚动与高性能列表组件

列表是移动端最高频的UI形态。聊天记录、商品列表、信息流、订单列表，本质上都是列表。RN提供了ScrollView和FlatList两套方案，选错方案会让你的应用在长列表场景下卡到怀疑人生。

### 3.3.1 ScrollView普通滚动组件用法

ScrollView是最基础的滚动容器。它会一次性渲染所有子组件，不管有多少个。适合内容数量有限、可预知的场景，比如个人中心页、设置页、文章详情页。

```jsx
import { ScrollView, View, Text, StyleSheet } from 'react-native';

export const ProfilePage = () => {
  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.section}>
        <Text style={styles.title}>个人信息</Text>
        <Text style={styles.desc}>头像、昵称、签名</Text>
      </View>
      <View style={styles.section}>
        <Text style={styles.title}>账号设置</Text>
        <Text style={styles.desc}>密码、绑定手机号</Text>
      </View>
      <View style={styles.section}>
        <Text style={styles.title}>关于我们</Text>
        <Text style={styles.desc}>版本号、隐私政策</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  section: { backgroundColor: '#fff', borderRadius: 8,
    padding: 16, marginBottom: 12 },
  title: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  desc: { fontSize: 14, color: '#999' },
});
```

两个关键属性需要理解：`contentContainerStyle`控制的是内容容器的样式，而不是ScrollView本身的样式。ScrollView本身的样式用`style`设置（比如背景色），内容区域的样式用`contentContainerStyle`设置（比如padding）。这两个很容易搞混。

`keyboardShouldPersistTaps`控制键盘弹出时点击外部区域是否收起键盘。值为`'handled'`时，点击事件由子组件先处理，如果子组件没有处理键盘才收起。值为`'never'`时（默认），点击外部自动收起键盘。在表单页面建议设为`'handled'`，避免用户点击按钮时键盘先收起导致按钮位置移动而误触。

### 3.3.2 ScrollView性能瓶颈与规避方案

ScrollView的核心问题是：它没有回收机制。100条数据就渲染100个item，1000条数据就渲染1000个item。当数据量超过50条时，FPS（Frames Per Second）会明显下降；超过200条时，低端机型直接白屏或OOM（Out of Memory）崩溃。

```
ScrollView渲染机制：
┌─────────────────────────────┐
│  一次性渲染全部子组件          │
│  item1  item2  item3 ... itemN │
│  全部存在于内存中              │
│  N越大，内存占用越高           │
│  滚动时所有item都参与渲染计算    │
└─────────────────────────────┘

FlatList渲染机制：
┌─────────────────────────────┐
│  只渲染可视区域内的组件         │
│  ┌─────┐ ┌─────┐ ┌─────┐    │
│  │item3│ │item4│ │item5│    │  ← 可见区域
│  └─────┘ └─────┘ └─────┘    │
│  滚动时回收不可见的item        │
│  内存占用恒定                │
└─────────────────────────────┘
```

什么时候用ScrollView？内容不超过两屏，比如个人中心页、设置页、详情页、关于页。什么时候绝对不能用？任何可能无限增长的数据列表——聊天记录、商品列表、订单列表、消息通知等。

如果你非要在ScrollView里放列表，有一个折中方案：限制列表最大高度，并把列表区域改成FlatList。但更好的做法是整体使用FlatList，通过`ListHeaderComponent`和`ListFooterComponent`来放头部和尾部内容。

### 3.3.3 FlatList高性能长列表原理

FlatList是RN官方提供的高性能列表组件，它基于VirtualizedList实现，核心原理是"只渲染可见区域的item，滚动时动态回收和创建"。

FlatList的工作流程分为三个阶段：

1. 首次渲染：计算每个item的高度（通过`getItemLayout`或实际渲染测量），只渲染可视区域内的item，通常是最初的5-10个。
2. 滚动过程中：根据滚动位置动态判断哪些item需要渲染，哪些可以回收。回收的item会被复用（类似Android的RecyclerView），避免频繁创建和销毁。
3. 空白区域：用空白占位符撑开滚动区域，保证滚动条位置和长度正确。

```jsx
import { FlatList, View, Text, StyleSheet } from 'react-native';

const data = Array.from({ length: 100 }, (_, i) => ({
  id: String(i),
  title: `商品 ${i + 1}`,
  price: Math.floor(Math.random() * 1000),
}));

export const ProductList = () => {
  const renderItem = ({ item }) => (
    <View style={styles.item}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.price}>¥{item.price}</Text>
    </View>
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
    />
  );
};

const styles = StyleSheet.create({
  list: { padding: 16 },
  item: { backgroundColor: '#fff', borderRadius: 8, padding: 16,
    marginBottom: 12, flexDirection: 'row',
    justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 15, color: '#333' },
  price: { fontSize: 15, color: '#ff4d4f', fontWeight: '600' },
});
```

`keyExtractor`是必填项，用于生成每个item的唯一key。如果不提供，FlatList会用数组索引作为key，这在数据增删时会导致渲染错乱——删除第一条数据后，原来第二条的key变成了0，React认为是同一条数据，只更新内容而不重新渲染，导致显示错乱。

`renderItem`接收的参数除了`item`，还有`index`（索引）、`separators`（分隔符控制器）等。其中`index`可以用来做奇偶行变色：

```jsx
const renderItem = ({ item, index }) => (
  <View style={[styles.item, index % 2 === 0 && styles.evenRow]}>
    <Text>{item.title}</Text>
  </View>
);
```

### 3.3.4 FlatList核心优化配置实战

FlatList的性能不会自动达到最优，需要通过一系列配置项来调优。以下是企业项目中必备的优化配置清单，每一项都经过实战验证：

```jsx
<FlatList
  data={data}
  renderItem={renderItem}
  keyExtractor={keyExtractor}
  // 核心优化项
  removeClippedSubviews={true}     // 回收不可见的子视图
  maxToRenderPerBatch={6}          // 每批最多渲染数量
  updateCellsBatchingPeriod={50}   // 批量渲染间隔(ms)
  initialNumToRender={8}           // 首屏渲染数量
  windowSize={7}                   // 渲染窗口倍数
  // 性能辅助
  getItemLayout={getItemLayout}    // 定高item必配
/>
```

各参数的作用和调优建议：

`removeClippedSubviews`：设为`true`后，不可见的子视图会被从原生视图层级中移除。在Android上效果明显（减少原生View的layout计算），iOS上提升有限。注意：如果你的item有动画效果，这个属性可能导致动画中断。

`windowSize`：控制渲染窗口大小，值为可视区域高度的倍数。默认值21（即上下各10屏的预渲染区域），对于大多数场景太大了。建议设为5-7，减少不必要的预渲染。值越小，内存占用越低，但滚动时出现白屏的概率越高。需要根据item的渲染复杂度来平衡。

`maxToRenderPerBatch`和`updateCellsBatchingPeriod`：这两个参数控制批量渲染策略。`maxToRenderPerBatch`控制每批最多渲染几个item，`updateCellsBatchingPeriod`控制两批渲染之间的间隔。默认值是10和50ms，对于复杂item建议降低`maxToRenderPerBatch`到4-6，避免单批渲染时间过长导致掉帧。

`getItemLayout`：如果item高度固定，提供这个函数可以跳过高度测量步骤，大幅提升首屏渲染速度和滚动性能。这是一个"配置了就一定快"的优化项：

```jsx
const ITEM_HEIGHT = 72;

getItemLayout={(data, index) => ({
  length: ITEM_HEIGHT,
  offset: ITEM_HEIGHT * index,
  index,
})}
```

如果你的item高度不固定，就不能使用`getItemLayout`。但你可以通过设置`estimatedItemSize`来提供估算高度，这也能提升性能（需要RN 0.71+）。

> 金句：FlatList的优化不是可选项，而是必修课。`getItemLayout`一行代码，可能让你的列表首屏渲染速度提升50%。

### 3.3.5 下拉刷新与上拉加载封装

下拉刷新和上拉加载更多是列表的标配交互。FlatList内置了对这两种交互的支持，通过`refreshControl`和`onEndReached`实现：

```jsx
import { FlatList, RefreshControl, ActivityIndicator,
  View, Text, StyleSheet } from 'react-native';
import { useState, useCallback, useRef } from 'react';

export const RefreshableList = ({ fetchData, renderItem }) => {
  const [data, setData] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const page = useRef(1);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    page.current = 1;
    try {
      const res = await fetchData(1);
      setData(res.list);
      setHasMore(res.hasMore);
    } finally {
      setRefreshing(false);
    }
  }, [fetchData]);

  const onEndReached = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const res = await fetchData(page.current + 1);
      page.current += 1;
      setData((prev) => [...prev, ...res.list]);
      setHasMore(res.hasMore);
    } finally {
      setLoadingMore(false);
    }
  }, [fetchData, loadingMore, hasMore]);

  const ListFooter = () => (
    <View style={styles.footer}>
      {loadingMore && <ActivityIndicator size="small" color="#1890ff" />}
      {!hasMore && !loadingMore && (
        <Text style={styles.noMore}>没有更多了</Text>
      )}
    </View>
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          colors={['#1890ff']}
          tintColor="#1890ff"
        />
      }
      onEndReached={onEndReached}
      onEndReachedThreshold={0.3}
      ListFooterComponent={ListFooter}
    />
  );
};

const styles = StyleSheet.create({
  footer: { padding: 16, alignItems: 'center' },
  noMore: { fontSize: 13, color: '#999' },
});
```

`onEndReachedThreshold`控制触发上拉加载的阈值，值为列表高度的百分比。0.3表示距离底部还有30%时触发。设太小会导致用户滑到底部才开始加载，出现空白等待；设太大会导致还没滑到底就提前加载，浪费请求。0.2-0.3是比较合理的范围。

`RefreshControl`的`colors`属性控制Android的下拉指示器颜色，`tintColor`控制iOS的下拉指示器颜色。两个平台用不同的属性，这是因为两个平台的下拉刷新组件是各自原生实现的。

## 3.4 Flex弹性布局核心原理与实战

RN的布局引擎是Yoga，一个基于C实现的Flexbox布局引擎。它和Web的Flexbox基本一致，但有一些关键差异。理解Flex布局是写出跨端适配UI的基础，也是RN开发中最核心的技能之一。

> 金句：Flex布局不是CSS的专利，它是描述空间分配的语言。在RN里，Flex是你和屏幕对话的唯一方式。

### 3.4.1 主轴与侧轴布局核心概念

Flex布局的核心是两根轴线：主轴（Main Axis）和侧轴（Cross Axis）。主轴是子组件排列的方向，侧轴是垂直于主轴的方向。所有的Flex布局属性都是围绕这两根轴线来定义的。

```
flexDirection: 'row' 时的轴向：
┌──────────────────────────────┐
│  Main Axis ────────────────►  │
│ ┌───┐ ┌───┐ ┌───┐            │
│ │ A │ │ B │ │ C │  Cross Axis│
│ └───┘ └───┘ └───┘     │      │
│                       ▼      │
└──────────────────────────────┘

flexDirection: 'column' 时的轴向：
┌──────────────────────────────┐
│  Cross Axis                  │
│ ┌───┐         │              │
│ │ A │         │              │
│ └───┘         ▼              │
│ ┌───┐   Main Axis            │
│ │ B │      │                 │
│ └───┘      ▼                 │
│ ┌───┐                        │
│ │ C │                        │
│ └───┘                        │
└──────────────────────────────┘
```

在RN中，`flexDirection`的默认值是`'column'`（Web中默认是`'row'`）。这是RN和Web Flexbox最显著的区别之一，也是Web开发者转RN最容易踩的坑。也就是说，RN中的元素默认是垂直排列的，不需要显式设置`flexDirection: 'column'`。

### 3.4.2 flex-direction横竖布局控制

`flexDirection`决定主轴方向，直接控制子组件的排列方向。虽然只有四个可选值，但它们决定了整个布局的结构：

```jsx
// 水平排列 - 适合工具栏、标签栏、按钮组
<View style={{ flexDirection: 'row' }}>
  <View style={{ width: 60, height: 60, backgroundColor: '#ff4d4f' }} />
  <View style={{ width: 60, height: 60, backgroundColor: '#1890ff' }} />
  <View style={{ width: 60, height: 60, backgroundColor: '#52c41a' }} />
</View>

// 垂直排列（默认）- 适合表单、列表、卡片堆叠
<View style={{ flexDirection: 'column' }}>
  <View style={{ height: 60, backgroundColor: '#ff4d4f' }} />
  <View style={{ height: 60, backgroundColor: '#1890ff' }} />
  <View style={{ height: 60, backgroundColor: '#52c41a' }} />
</View>
```

`flexDirection: 'row-reverse'`和`'column-reverse'`可以让排列方向反转。row-reverse是从右到左排列，column-reverse是从下到上排列。这在RTL（Right-to-Left，从右到左）语言环境下很有用，比如阿拉伯语布局需要row-reverse。

实际开发中，绝大多数布局只需要`'row'`和`'column'`两个值。如果你发现自己在用reverse，先停下来想想是不是布局思路有问题——通常有更清晰的实现方式。

### 3.4.3 justifyContent主轴对齐方式

`justifyContent`控制子组件在主轴上的对齐方式和间距分布，有6个常用值：

| 值 | 效果 |
|----|------|
| flex-start | 起点对齐（默认） |
| flex-end | 终点对齐 |
| center | 居中对齐 |
| space-between | 两端对齐，元素间间距均匀 |
| space-around | 每个元素两侧间距相等 |
| space-evenly | 所有间距完全相等 |

```
justifyContent效果对比（row方向）：

flex-start:    [A][B][C]___________
flex-end:      _________[A][B][C]
center:        _____[A][B][C]_____
space-between: [A]____[B]____[C]
space-around:  _[A]__[B]__[C]_
space-evenly: __[A]__[B]__[C]__
```

这三个space值容易混淆，区分方法：`space-between`是元素之间间距相等但首尾没有间距，`space-around`是每个元素左右各有半个间距（首尾有半个间距），`space-evenly`是所有间距完全相等（首尾和元素之间的间距一样大）。

实际开发中，`space-between`是最常用的值，适合做导航栏的两端对齐布局：

```jsx
<View style={{
  flexDirection: 'row',
  justifyContent: 'space-between',
  alignItems: 'center',
  paddingHorizontal: 16,
  height: 48,
}}>
  <Text>返回</Text>
  <Text>标题</Text>
  <Text>更多</Text>
</View>
```

`center`常用于居中加载状态、空状态提示等场景。`flex-end`常用于底部固定按钮的容器。

### 3.4.4 alignItems侧轴对齐适配技巧

`alignItems`控制子组件在侧轴上的对齐方式：

| 值 | 效果 |
|----|------|
| flex-start | 侧轴起点对齐 |
| flex-end | 侧轴终点对齐 |
| center | 侧轴居中对齐 |
| stretch | 拉伸填满侧轴（默认） |
| baseline | 基线对齐（仅Text有效） |

`alignItems: 'stretch'`是默认值，这意味着如果子组件没有设置侧轴方向的尺寸，它们会自动拉伸填满容器。这就是为什么很多新手发现View里的子View默认宽度是100%——因为默认的column方向下，stretch会把子组件的宽度拉伸到容器宽度。

```jsx
// 居中对齐的经典场景
<View style={{
  flex: 1,
  justifyContent: 'center',
  alignItems: 'center',
}}>
  <Text>水平和垂直居中</Text>
</View>
```

如果只需要单个子组件覆盖父容器的`alignItems`设置，可以使用`alignSelf`属性。这在同一行中让某个元素特殊对齐时很有用：

```jsx
<View style={{ alignItems: 'center', flexDirection: 'row' }}>
  <Text>居中</Text>
  <Text style={{ alignSelf: 'flex-end' }}>底部对齐</Text>
  <Text>居中</Text>
</View>
```

### 3.4.5 flex自适应占比布局实战案例

`flex`属性是Flex布局中最强大的工具。它定义子组件在主轴上占据空间的占比比例。和Web中`flex: 1`是`flex-grow: 1, flex-shrink: 1, flex-basis: 0%`的简写不同，RN中`flex`属性的行为更简单直接：

```jsx
// 三等分布局
<View style={{ flex: 1, flexDirection: 'row' }}>
  <View style={{ flex: 1, backgroundColor: '#ff4d4f' }} />
  <View style={{ flex: 1, backgroundColor: '#1890ff' }} />
  <View style={{ flex: 1, backgroundColor: '#52c41a' }} />
</View>

// 1:2:1比例布局
<View style={{ flex: 1, flexDirection: 'row' }}>
  <View style={{ flex: 1, backgroundColor: '#ff4d4f' }} />
  <View style={{ flex: 2, backgroundColor: '#1890ff' }} />
  <View style={{ flex: 1, backgroundColor: '#52c41a' }} />
</View>
```

```
flex: 1 三等分：
┌──────┬──────┬──────┐
│  1   │  1   │  1   │
│ red  │ blue │ green│
└──────┴──────┴──────┘

flex: 1:2:1 比例：
┌────┬────────┬────┐
│ 1  │   2    │ 1  │
│red │  blue  │grn │
└────┴────────┴────┘
```

> 怕浪猫踩坑提醒：RN中`flex: 1`的行为在不同版本有差异。在RN >= 0.60中，`flex: 1`等价于`flexGrow: 1, flexShrink: 1, flexBasis: 0`。但在更早版本中，`flex: 1`只设置`flexGrow: 1`，不设置`flexShrink`。如果你的项目RN版本较低，建议显式使用`flexGrow`和`flexShrink`。

实战案例——顶部导航+内容区+底部Tab的经典三段式布局：

```jsx
<View style={{ flex: 1 }}>
  {/* 顶部导航 - 固定高度 */}
  <View style={{ height: 48, backgroundColor: '#1890ff' }}>
    <Text style={{ color: '#fff', textAlign: 'center', lineHeight: 48 }}>
      首页
    </Text>
  </View>

  {/* 内容区 - 自适应撑满剩余空间 */}
  <View style={{ flex: 1, backgroundColor: '#f5f5f5' }}>
    <Text>内容区域</Text>
  </View>

  {/* 底部Tab - 固定高度 */}
  <View style={{ height: 56, flexDirection: 'row',
    backgroundColor: '#fff', borderTopWidth: 1, borderColor: '#eee' }}>
    <View style={{ flex: 1, alignItems: 'center' }}>
      <Text>首页</Text>
    </View>
    <View style={{ flex: 1, alignItems: 'center' }}>
      <Text>我的</Text>
    </View>
  </View>
</View>
```

这种"固定+自适应+固定"的三段式布局是移动端最常见的页面结构。关键是给中间内容区设置`flex: 1`，让它自动占据剩余空间。顶部和底部不设flex，只设固定高度，它们的大小不会变化。

> 金句：Flex布局的核心不是"怎么居中"，而是"怎么分配空间"。理解了空间分配，所有布局问题都是同一个问题。

## 3.5 多机型屏幕适配方案

你写的页面在你的手机上完美，换一台手机就崩了——这是RN开发者必经的噩梦。市面上Android屏幕尺寸从4寸到7寸不等，分辨率从720p到2K都有；iPhone从SE的4.7寸到Pro Max的6.7寸，还有刘海屏、灵动岛等各种异形屏。屏幕适配不是可选项，是从第一天就要考虑的核心问题。

### 3.5.1 逻辑像素与设备像素差异解析

移动端有两套像素概念：设备像素（Device Pixel，也叫物理像素）和逻辑像素（Logical Pixel，也叫CSS像素，RN中就是style里写的px）。它们之间的关系由DPR（Device Pixel Ratio，设备像素比）决定：

```
设备像素 = 逻辑像素 × DPR

示例：
iPhone 15 Pro:
  设备分辨率: 1179 × 2556 (设备像素)
  逻辑分辨率: 393 × 852 (逻辑像素)
  DPR: 3 (1179 / 393 = 3)

iPhone SE (2nd):
  设备分辨率: 750 × 1334 (设备像素)
  逻辑分辨率: 375 × 667 (逻辑像素)
  DPR: 2 (750 / 375 = 2)

Pixel 7:
  设备分辨率: 1080 × 2400 (设备像素)
  逻辑分辨率: 412 × 915 (逻辑像素)
  DPR: ~2.6
```

RN中的`width`、`height`、`fontSize`等所有尺寸单位都是逻辑像素。你写`width: 100`，在DPR为2的设备上实际渲染200个物理像素，在DPR为3的设备上渲染300个物理像素。这个映射由系统自动完成，你不需要手动计算。

但你需要关心的是：同样100逻辑像素的宽度，在小屏手机上占屏幕宽度的27%（100/375），在大屏手机上只占24%（100/414）。这个差异在小元素上不明显，但在整体布局中会累积成明显的错位。

RN提供了`PixelRatio`模块来获取设备的DPR和进行像素转换：

```jsx
import { PixelRatio } from 'react-native';

const dpr = PixelRatio.get();               // 设备DPR (2或3)
const fontScale = PixelRatio.getFontScale(); // 字体缩放比（受系统设置影响）
const pixelSize = PixelRatio.getPixelSizeForLayoutSize(100);
// 逻辑像素100 -> 设备像素（DPR=3时返回300）
```

### 3.5.2 多尺寸手机屏幕统一适配策略

最常用的屏幕适配方案是"以设计稿宽度为基准，按比例缩放"。假设设计稿宽度为375px（iPhone标准宽度），适配公式为：

```jsx
import { Dimensions, PixelRatio } from 'react-native';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');
const designWidth = 375;

// 按设计稿比例缩放
export const px = (designPx) => {
  const scale = screenWidth / designWidth;
  return Math.round(designPx * scale);
};

// 使用
<View style={{ width: px(200), height: px(100) }} />
<Text style={{ fontSize: px(14) }}>适配文字</Text>
```

这种方案的原理是：设计稿上标注的200px宽度，在375宽度的设备上就是200逻辑像素，在414宽度的设备上自动放大为221逻辑像素（200 × 414/375），保持视觉比例一致。

但这个方案有一个问题：在大屏设备上，所有元素都被等比放大，可能导致大屏手机上文字过大、按钮过大，浪费屏幕空间。用户买大屏手机是为了看到更多内容，而不是看到更大的内容。更合理的方案是设置一个缩放上限：

```jsx
export const px = (designPx) => {
  const scale = Math.min(screenWidth / designWidth, 1.2);
  return Math.round(designPx * scale);
};
```

这样缩放比例最大不超过1.2倍，在大屏设备上不会过度放大。

还需要注意的是，`Dimensions.get('window')`获取的是当前窗口尺寸。在横竖屏切换时，宽高会互换。如果你在模块加载时缓存了screenWidth，横屏后这个值就是错的。解决方案是使用`useWindowDimensions`Hook（RN 0.62+），它会自动响应屏幕变化：

```jsx
import { useWindowDimensions } from 'react-native';

const Component = () => {
  const { width } = useWindowDimensions();
  const scale = width / 375;
  // ...
};
```

### 3.5.3 字体、间距动态适配方案

字体适配需要考虑一个额外因素：用户可能在系统设置中开启了字体大小放大。RN中可以通过`PixelRatio.getFontScale()`获取系统字体缩放比例。如果用户把系统字体放大到1.5倍，你写的fontSize: 14实际显示为21。

如果你的设计要求字体大小不受系统设置影响（比如按钮文字不应该被放大），可以设置`allowFontScaling={false}`：

```jsx
<Text style={{ fontSize: 14 }} allowFontScaling={false}>
  不受系统字体大小影响
</Text>
```

但更好的做法是尊重用户的字体设置——有些视力不好的用户依赖系统字体放大来使用应用。你应该确保布局在大字体下不被撑破，而不是禁止字体放大。具体做法是给文本容器设置`maxHeight`或使用`numberOfLines`做兜底处理。

间距适配推荐使用"阶梯式"方案，而不是等比缩放。因为间距的视觉感受不是线性的——4px到8px的差异在视觉上比40px到44px明显得多：

```jsx
// 间距阶梯 - 全项目统一使用
export const spacing = {
  xs: px(4),
  sm: px(8),
  md: px(12),
  lg: px(16),
  xl: px(24),
  xxl: px(32),
};

// 字体阶梯 - 全项目统一使用
export const fontSize = {
  caption: px(12),   // 辅助说明文字
  body: px(14),      // 正文
  subtitle: px(16),  // 副标题
  title: px(18),     // 标题
  header: px(22),    // 页头标题
  large: px(28),     // 大标题
};
```

统一使用这套阶梯值，而不是在代码里到处写魔法数字。这样调整全局间距或字体时只需要改一个地方，而且团队成员之间有共同的尺寸语言。

> 金句：适配不是让所有手机看起来一样，而是让所有手机看起来都合理。等比缩放是手段，视觉一致才是目的。

### 3.5.4 刘海屏、挖孔屏安全区适配

从iPhone X开始，刘海屏、挖孔屏成为主流。这些设备的屏幕顶部有刘海/灵动岛，底部有Home Indicator，左右可能有圆角。如果内容延伸到这些区域，会被遮挡或裁剪。

RN官方提供了`SafeAreaView`组件来处理安全区域，但它的行为在不同版本有差异。推荐使用`react-native-safe-area-context`库，它提供了更可靠的跨平台安全区适配：

```jsx
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

export const App = () => {
  return (
    <SafeAreaProvider>
      <SafeAreaView style={{ flex: 1, backgroundColor: '#1890ff' }}>
        <View style={{ flex: 1, backgroundColor: '#fff' }}>
          <Text>内容在安全区内</Text>
        </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
};
```

`SafeAreaView`会自动在顶部和底部添加padding，避开刘海和底部Home Indicator。注意背景色的处理：`SafeAreaView`本身的style设置的是安全区外（padding区域）的背景色，内容区域的View设置的是安全区内的背景色。这样顶部安全区可以显示品牌色背景，而内容区域是白色背景。

如果你需要更精细的控制——比如自定义头部导航栏，底部自定义TabBar——可以使用`useSafeAreaInsets`Hook获取各方向的安全区间距：

```jsx
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export const CustomHeader = () => {
  const insets = useSafeAreaInsets();

  return (
    <View style={{
      paddingTop: insets.top,        // 顶部安全区高度
      paddingBottom: insets.bottom,   // 底部安全区高度
      paddingLeft: insets.left,       // 左侧（横屏时有用）
      paddingRight: insets.right,     // 右侧（横屏时有用）
      backgroundColor: '#1890ff',
    }}>
      <Text style={{ height: 44, lineHeight: 44, textAlign: 'center',
        color: '#fff' }}>自定义头部</Text>
    </View>
  );
};
```

这种方式比`SafeAreaView`更灵活，特别适合需要自定义头部、底部TabBar的场景。`insets.top`在不带刘海的手机上为20（状态栏高度），在带刘海的手机上为44或59（取决于具体机型）。

### 3.5.5 横竖屏切换适配兼容处理

横竖屏切换时，屏幕宽高会互换。如果你的布局写死了宽高值，横屏时就会出现布局错乱。RN中有两种处理横竖屏的方式：响应式布局和锁定屏幕方向。

响应式布局方案——使用`useWindowDimensions`监听屏幕变化：

```jsx
import { useWindowDimensions, View, Text, StyleSheet } from 'react-native';

export const ResponsiveView = () => {
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;

  return (
    <View style={[
      styles.container,
      isLandscape && styles.landscape,
    ]}>
      <Text>{isLandscape ? '横屏模式' : '竖屏模式'}</Text>
      <Text>宽: {width.toFixed(0)} 高: {height.toFixed(0)}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  landscape: { flexDirection: 'row' },
});
```

布局策略上，尽量用`flex`比例布局代替固定宽高值，这样横竖屏切换时布局会自动适应。必须用固定尺寸的地方，使用动态获取的屏幕尺寸来计算：

```jsx
const cardWidth = width - spacing.lg * 2; // 卡片宽度 = 屏幕宽 - 左右padding
```

如果你的应用不需要支持横屏（大多数社交、电商应用都是竖屏体验），最简单的方案是锁定屏幕方向。在`app.json`（Expo项目）或原生配置中设置：

```json
{
  "expo": {
    "orientation": "portrait"
  }
}
```

值为`"portrait"`时锁定竖屏，`"landscape"`锁定横屏，`"default"`允许自动切换。锁定方向后，你不需要处理任何横屏适配逻辑，大幅减少开发和测试成本。

> 金句：能锁屏就别自适应。横竖屏适配的成本不是多写几个if判断，而是需要测试两套布局的所有交互路径。

## 3.6 样式规范化与页面布局实战

样式管理是RN工程化中最容易被忽视的环节。小项目里随手写`style={{}}`没问题，项目一大，样式散落在各处，修改一个颜色要找十几个文件，维护噩梦就开始了。这一节讲的是如何建立一套可持续维护的样式体系。

### 3.6.1 StyleSheet样式创建规范

RN提供了`StyleSheet.create`方法来创建样式。它的作用不仅是组织代码，更重要的是会将样式对象转化为内部引用ID，减少跨桥通信的数据量：

```jsx
// 推荐写法 - 使用StyleSheet.create
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 16,
    color: '#333',
    fontWeight: '600',
  },
});

// 不推荐：行内样式
<View style={{ flex: 1, backgroundColor: '#f5f5f5' }}>
  <Text style={{ fontSize: 16, color: '#333', fontWeight: '600' }}>
    标题
  </Text>
</View>
```

`StyleSheet.create`创建的样式在底层会被优化为整型ID引用，每次渲染时传递的是一个数字而不是整个样式对象。在列表渲染等高频场景下，这个优化能带来可感知的性能提升——100个item传递100个数字远比传递100个样式对象高效。

### 3.6.2 行内样式与静态样式选型原则

不是所有场景都必须用`StyleSheet.create`。行内样式适合那些"只用一次且需要动态计算"的样式：

```jsx
// 动态样式 - 行内写法更清晰
<View style={{
  width: item.width,
  height: item.height,
  backgroundColor: item.active ? '#1890ff' : '#ccc',
}}>
  <Text>{item.label}</Text>
</View>

// 静态样式 - StyleSheet更高效
const styles = StyleSheet.create({
  card: { borderRadius: 8, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 16, fontWeight: '600', color: '#333' },
});
```

选型原则很简单：如果样式是静态的、可复用的，用`StyleSheet.create`；如果样式依赖运行时变量且每次渲染都不同，用行内样式。混合使用时，通过数组合并静态和动态样式：

```jsx
<View style={[styles.card, { backgroundColor: dynamicColor }]}>
```

这种方式既保持了静态样式的性能优势，又保留了动态样式的灵活性。数组中后面的样式会覆盖前面同名的属性。

### 3.6.3 样式合并、覆盖与继承规则

RN中的样式合并使用数组语法，后面的样式会覆盖前面同名的属性。这个规则和CSS的优先级规则完全不同，RN没有选择器优先级，只有顺序优先级：

```jsx
<View style={[
  styles.base,      // 基础样式
  styles.primary,   // 主题样式，覆盖base中的同名属性
  { opacity: 0.8 }, // 行内样式，覆盖一切
]}>
```

样式覆盖的三条规则：

1. 同名属性，后面的覆盖前面的
2. 不同属性，合并生效
3. `false`、`null`、`undefined`的样式会被跳过

第3条规则在条件样式中非常有用：

```jsx
<View style={[
  styles.btn,
  disabled && styles.btnDisabled,  // disabled为false时跳过
  active && styles.btnActive,      // active为false时跳过
]}>
```

需要注意的是，Text组件的样式有继承行为——父Text的某些样式会自动传递给子Text。继承的样式包括：`color`、`fontSize`、`fontFamily`、`fontWeight`、`lineHeight`等文字相关属性。但`backgroundColor`、`padding`、`margin`等布局样式不会继承。这个继承行为只在Text嵌套Text时生效，View嵌套Text时不会继承。

### 3.6.4 全局公共样式抽取与封装

项目达到一定规模后，需要建立全局样式体系（也叫Design Token系统）。推荐按以下结构组织，将设计规范代码化：

```jsx
// theme/colors.js - 颜色体系
export const colors = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  danger: '#ff4d4f',
  textPrimary: '#333',
  textSecondary: '#666',
  textHint: '#999',
  border: '#e8e8e8',
  background: '#f5f5f5',
  white: '#fff',
  black: '#000',
};

// theme/spacing.js - 间距体系
export const spacing = {
  xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32,
};

// theme/typography.js - 字体体系
export const typography = {
  caption: { fontSize: 12, lineHeight: 18 },
  body: { fontSize: 14, lineHeight: 22 },
  subtitle: { fontSize: 16, lineHeight: 24 },
  title: { fontSize: 18, lineHeight: 26, fontWeight: '600' },
  header: { fontSize: 22, lineHeight: 30, fontWeight: '700' },
};

// theme/index.js - 统一导出
export { colors, spacing, typography };
```

然后在组件中引用：

```jsx
import { colors, spacing, typography } from '../theme';

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.white,
    borderRadius: 8,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    ...typography.title,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  desc: {
    ...typography.body,
    color: colors.textSecondary,
  },
});
```

这种方式的好处是：当设计师说"主色从蓝色换成紫色"时，你只需要改`colors.js`中的`primary`值，全项目自动生效。当设计师说"所有卡片间距加大"时，改`spacing.js`中的`lg`值就够了。这就是设计系统的力量——它让设计和代码保持同步，让维护成本从O(n)降到O(1)。

> 金句：样式不是代码的附属品，而是设计系统的代码化表达。好的样式架构，让设计师和开发者说同一种语言。

### 3.6.5 综合布局页面实战搭建练习

把本章所有知识点串联起来，做一个完整的"商品详情页"。这个页面会用到安全区适配、滚动容器、Flex布局、图片加载、触控交互、主题样式等全部内容：

```jsx
import React from 'react';
import {
  View, Text, Image, ScrollView, Pressable,
  StyleSheet, SafeAreaView,
} from 'react-native';
import { colors, spacing, typography } from './theme';

export const ProductDetail = () => {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Image
          source={{ uri: 'https://example.com/product.jpg' }}
          style={styles.productImage}
          resizeMode="cover"
        />
        <View style={styles.infoSection}>
          <Text style={styles.price}>
            <Text style={styles.priceSymbol}>¥</Text>
            <Text style={styles.priceValue}>299</Text>
          </Text>
          <Text style={styles.title}>高品质无线蓝牙耳机</Text>
          <Text style={styles.desc}>主动降噪 | 30小时续航 | 舒适佩戴</Text>
        </View>
        <View style={styles.specSection}>
          <Text style={styles.sectionTitle}>颜色选择</Text>
          <View style={styles.colorList}>
            <View style={[styles.colorDot, { backgroundColor: '#000' }]} />
            <View style={[styles.colorDot, { backgroundColor: '#fff',
              borderWidth: 1, borderColor: '#ddd' }]} />
            <View style={[styles.colorDot, { backgroundColor: '#1890ff' }]} />
          </View>
        </View>
        <View style={styles.detailSection}>
          <Text style={styles.sectionTitle}>商品详情</Text>
          <Image
            source={{ uri: 'https://example.com/detail1.jpg' }}
            style={styles.detailImage}
            resizeMode="contain"
          />
        </View>
      </ScrollView>
      <View style={styles.bottomBar}>
        <Pressable style={styles.cartBtn} hitSlop={10}>
          <Text style={styles.cartBtnText}>购物车</Text>
        </Pressable>
        <Pressable style={styles.buyBtn} hitSlop={10}>
          <Text style={styles.buyBtnText}>立即购买</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  productImage: { width: '100%', height: 375 },
  infoSection: { backgroundColor: colors.white, padding: spacing.lg,
    marginBottom: spacing.sm },
  price: { flexDirection: 'row', alignItems: 'baseline',
    marginBottom: spacing.sm },
  priceSymbol: { ...typography.body, color: colors.danger,
    fontWeight: '600' },
  priceValue: { ...typography.header, color: colors.danger,
    fontWeight: '700' },
  title: { ...typography.subtitle, color: colors.textPrimary,
    marginBottom: spacing.xs },
  desc: { ...typography.body, color: colors.textSecondary },
  specSection: { backgroundColor: colors.white, padding: spacing.lg,
    marginBottom: spacing.sm },
  sectionTitle: { ...typography.subtitle, color: colors.textPrimary,
    marginBottom: spacing.md },
  colorList: { flexDirection: 'row', gap: spacing.md },
  colorDot: { width: 36, height: 36, borderRadius: 18 },
  detailSection: { backgroundColor: colors.white,
    padding: spacing.lg },
  detailImage: { width: '100%', height: 300 },
  bottomBar: { flexDirection: 'row', padding: spacing.md,
    backgroundColor: colors.white, borderTopWidth: 1,
    borderTopColor: colors.border },
  cartBtn: { flex: 1, height: 44, borderRadius: 22,
    borderWidth: 1, borderColor: colors.primary,
    justifyContent: 'center', alignItems: 'center', marginRight: spacing.sm },
  cartBtnText: { ...typography.body, color: colors.primary },
  buyBtn: { flex: 2, height: 44, borderRadius: 22,
    backgroundColor: colors.primary,
    justifyContent: 'center', alignItems: 'center' },
  buyBtnText: { ...typography.body, color: colors.white,
    fontWeight: '600' },
});
```

这个页面综合运用了本章所有知识点：SafeAreaView处理安全区、ScrollView处理滚动内容、Flex布局排列元素（底部栏的row布局、flex比例分配）、Image加载网络图片（cover和contain两种模式）、Pressable处理点击交互、StyleSheet.create管理样式、theme统一设计变量。这就是一个标准的RN商品详情页结构，可以作为你后续开发类似页面的模板。

## 总结

本章覆盖了RN开发中最基础也最重要的三块内容，它们构成了你后续所有RN开发的底层能力：

组件体系方面，View、Text、Image、TextInput是四大基础组件，Pressable是新一代触控方案，FlatList是长列表的唯一选择。每个组件都有其适用场景和性能边界，选对组件是写出高质量代码的第一步。记住：ScrollView只用于少量内容，FlatList用于数据列表，没有例外。

布局方面，Flex布局的核心是主轴和侧轴的空间分配。`flex`属性控制占比、`justifyContent`控制主轴对齐、`alignItems`控制侧轴对齐。记住三段式布局模式："固定+自适应+固定"，能解决80%的页面布局需求。RN默认`flexDirection`是`'column'`，这和Web不同，千万别搞混。

屏幕适配方面，理解逻辑像素和设备像素的区别是基础，以设计稿宽度为基准的等比缩放是手段，安全区适配是必修课。建立全局样式体系（colors/spacing/typography）是项目工程化的第一步。从第一天就建立样式体系，比后期重构成本低十倍。

> 金句：组件是砖瓦，布局是框架，适配是地基。三者俱备，你的RN大楼才能盖得高、立得稳。

下一章我们将进入组件化开发的世界——第四章"组件化开发、Hooks与组件通信机制"。从基础组件到自定义组件，从Props传参到Hooks状态管理，从父子通信到跨页通信，系统性地掌握RN组件化开发的完整知识体系。组件化是RN开发的分水岭：会写组件的是开发者，会设计组件架构的是工程师。如果你觉得本章的内容是"写页面"，那下一章就是"设计系统"。

怕浪猫说：RN的组件和布局看似简单，实则暗藏玄机。这一章的内容建议反复阅读，特别是FlatList优化配置和Flex布局部分，每读一遍都会有新的理解。把本章的代码示例都敲一遍，在你的模拟器和真机上跑起来看看效果，你的RN地基就牢固了。下一章我们聊组件化，不见不散。

系列进度 3/16
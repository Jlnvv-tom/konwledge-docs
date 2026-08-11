---
sidebar_position: 13
---

# 第13章 RN项目性能优化、卡顿与内存治理

> 性能优化不是"做完功能再补"，而是从架构设计第一天就要埋进基因里的工程素养。

一个让我至今记忆犹新的场景：某电商类RN（React Native）应用在测试环境跑得丝般顺滑，上线后第一天就收到大量用户反馈"滑动卡顿""页面白屏""用着用着闪退"。团队紧急排查，发现首页长列表在真机上帧率掉到15fps（Frames Per Second），低端机型上甚至只有8fps。更可怕的是，用户浏览五分钟商品列表后，内存占用从120MB飙升到480MB，部分Android机型直接被系统OOM（Out of Memory）杀进程。团队花了整整两周做性能专项治理，列表帧率恢复到58fps以上，内存稳定在180MB以内，这才算把问题压下去。

这种故事在RN社区里并不罕见，几乎是每个中大型RN项目的必经之路。RN的跨端特性让开发者很容易忽略底层渲染机制，业务迭代时只关注"功能能不能跑"，不关注"跑得够不够快、够不够稳"。等到用户投诉铺天盖地再来补救，成本远比从一开始就做好性能设计要高得多。更常见的情况是，很多团队根本没有性能意识，把RN当成"能跑就行"的快速开发工具，列表不优化、图片不压缩、内存不释放、打包不瘦身，最终产出一个"功能完整但体验极差"的应用。

我是怕浪猫，一个在RN性能泥潭里摸爬滚打多年的工程老兵。从最早遇到列表滑动卡顿时的不知所措，到后来建立完整的性能监控和优化体系，我踩过的坑足够写一本"RN性能避坑指南"。从JS（JavaScript）线程阻塞到UI（User Interface）线程过载，从内存泄漏排查到打包体积优化，我把实战经验整理成这套系统方法论。这一章从性能瓶颈认知到具体优化手段，从长列表深度调优到内存泄漏治理，从网络加载体验到打包瘦身，覆盖RN性能优化的全链路，帮你建立完整的性能工程能力。

## 13.1 RN性能瓶颈与优化体系认知

### 13.1.1 移动端性能核心指标标准

做性能优化之前，先建立可量化的指标体系。没有指标就没有优化方向，凭感觉调优等于盲人摸象。

移动端性能关注四大核心指标：

| 指标 | 合格线 | 优秀线 | 说明 |
|------|--------|--------|------|
| 页面首屏渲染时间 | < 2s | < 1s | 从导航开始到首屏内容可见 |
| 交互响应延迟 | < 100ms | < 16ms | 用户操作到UI反馈的间隔 |
| 滑动帧率 | >= 30fps | >= 58fps | 列表滑动时的画面流畅度 |
| 内存占用 | < 300MB | < 200MB | 应用运行时的RSS（Resident Set Size） |

为什么是这些数字？60fps（Frames Per Second）意味着每帧渲染时间不能超过16.67ms（1000ms / 60），低于30fps人眼会明显感知卡顿。100ms是用户感知延迟的分水岭，超过这个值用户会觉得"反应慢"。内存方面，Android低端机型可用内存往往只有2GB（Gigabyte），应用自身占用超过300MB就面临被系统回收的风险。

> 性能优化的第一步不是写代码，而是定指标。没有可量化的目标，所有优化都是自嗨。怕浪猫见过太多团队说"优化后快多了"，问快多少答不上来。拿数据说话，是工程和手艺的分界线。

### 13.1.2 RN渲染卡顿根本原因解析

RN的渲染管线涉及三个关键角色：JS线程、Native UI线程、Shadow线程。理解它们如何协作，才能定位卡顿根因。

```
RN渲染管线流程：

  JS线程                    Shadow线程               Native UI线程
    |                          |                         |
  组件reconcile ----> 计算布局树 ----> 映射原生视图 ----> 提交渲染
  (React Reconciler)    (Yoga布局引擎)    (ViewManager)    (系统渲染)
    |                          |                         |
  <- 业务逻辑执行           <- 样式计算                  <- 原生绘制
```

JS线程负责执行业务逻辑和React组件树的reconcile（协调）过程。当组件状态更新时，JS线程执行Virtual DOM（虚拟文档对象模型）diff算法，计算出需要更新的节点，把变更指令发送到Shadow线程。Shadow线程使用Yoga布局引擎计算每个节点的位置和尺寸，生成布局树后传递给Native UI线程。Native UI线程根据布局树创建或更新原生视图，最终由系统渲染管线绘制到屏幕上。

卡顿通常发生在三个环节的某一个：

第一，JS线程阻塞。React组件diff计算耗时过长、业务逻辑中有大量同步计算、定时器回调堆积，都会导致JS线程无法按时输出下一帧的更新指令。表现是：动画掉帧、手势响应延迟、页面切换卡顿。

第二，Shadow线程过载。当组件树层级过深或节点数量巨大时，Yoga布局计算会消耗大量时间。一个包含5000个节点的列表，每次更新触发全量布局计算，Shadow线程可能需要几十毫秒才能完成。

第三，Native UI线程过载。原生视图创建和更新本身有开销，当短时间内需要创建大量原生视图（如长列表快速滑动时）或频繁更新视图属性时，UI线程会被打满。

> 大多数RN开发者把卡顿简单归因为"JS慢"，这其实是一种误解。卡顿可能发生在渲染管线的任何一个环节。定位问题的关键是：搞清楚到底是哪个线程在瓶颈上。用Chrome DevTools的Performance面板分析JS线程执行，用Xcode Instruments或Android Profiler分析原生线程，才能精准定位。

### 13.1.3 JS线程与UI线程阻塞问题

JS线程和UI线程的阻塞场景有本质区别，需要分开讨论。

JS线程阻塞的常见原因：

```js
// 典型阻塞场景1：同步大量计算
function processLargeData(dataList) {
  // 在JS线程同步处理10000条数据
  const result = dataList.map(item => {
    return heavyTransform(item); // 每条数据做复杂转换
  });
  return result; // JS线程被阻塞数百毫秒
}

// 典型阻塞场景2：同步JSON解析
const hugeData = JSON.parse(hugeJsonString); // 大JSON解析阻塞JS线程

// 典型阻塞场景3：console.log输出大量数据
console.log('调试数据:', response); // 生产环境忘删，输出大对象卡顿
```

UI线程阻塞的常见原因：

```js
// 典型场景1：在render中执行重计算
function ProductList({ products }) {
  // 每次render都重新排序，浪费性能
  const sorted = products.sort((a, b) => a.price - b.price);
  return sorted.map(p => <ProductCard key={p.id} data={p} />);
}

// 典型场景2：内联函数导致组件树全量更新
function Parent() {
  return <Child onPress={() => doSomething()} />;
  // 每次render都创建新函数引用，Child无法被memo缓存
}
```

解决JS线程阻塞的核心思路是把重计算移出JS线程。新架构下可以通过JSI将计算密集型任务委托给C++层同步执行，或者使用Worker线程做异步计算。旧架构下只能通过拆分任务、分帧执行来缓解。

解决UI线程阻塞的核心思路是减少不必要的reconcile和原生视图操作。React.memo减少组件重渲染、useMemo缓存计算结果、VirtualizedList的窗口化渲染减少节点数量，都是围绕这个思路。

### 13.1.4 常见性能问题场景汇总

根据怕浪猫处理过的上百个RN性能问题，最常见的卡顿场景可以归纳为五类：

**列表滑动卡顿** — 最高频问题。FlatList未配置优化参数、列表项组件未做memo、cell高度动态计算不准确，导致滑动时帧率暴跌。

**页面切换白屏** — 页面组件过于复杂，首次渲染时JS线程和UI线程同时过载，白屏时间超过500ms用户就会感知。

**输入响应延迟** — TextInput的onChangeText触发了昂贵的状态更新，每输入一个字符都引发整页重渲染，打字时明显卡顿。

**图片加载闪烁** — 图片未做缓存控制、列表中的图片在滑动时反复加载释放，造成视觉闪烁和内存波动。

**内存持续增长** — 定时器未清除、事件监听未移除、闭包引用未释放，导致页面切换后内存不回收，使用越久内存越高。

> 这五类问题占RN性能问题的80%以上。如果你只有时间修一类，优先修列表卡顿——它影响面最广、用户感知最强。如果有时间修两类，再加上内存泄漏——它会直接导致应用崩溃。

### 13.1.5 全链路性能优化整体思路

性能优化不是零散地改几行代码，而是需要系统化的全链路策略。怕浪猫总结了一个"四层优化模型"：

```
全链路性能优化四层模型：

  第一层：渲染层 — 减少不必要的组件重渲染
    |  React.memo / useMemo / useCallback / 组件拆分
    v
  第二层：数据层 — 减少不必要的数据处理和传输
    |  请求合并 / 数据缓存 / 分页加载 / 选择性订阅
    v
  第三层：资源层 — 减少不必要的资源加载和占用
    |  图片压缩 / 懒加载 / 资源清理 / 依赖精简
    v
  第四层：工程层 — 减少不必要的打包体积和启动开销
    |  代码拆分 / Metro优化 / 分包加载 / 启动加速
```

这四层从上到下，优化的粒度从细到粗，影响范围从局部到全局。渲染层优化影响单个组件的渲染效率，数据层优化影响页面级的数据流效率，资源层优化影响应用级的资源使用效率，工程层优化影响打包和启动的整体效率。

优化的基本原则是：先定位再优化、先测量再改码、先高频后低频。用性能分析工具找到真正的瓶颈点，用数据验证优化效果，优先处理用户感知最强的高频场景。切忌凭猜测盲目优化——怕浪猫见过有人花两天优化了一个几乎没人访问的设置页面的渲染性能，而首页列表卡顿的问题却一直没处理。

## 13.2 页面渲染与组件性能优化

### 13.2.1 无效组件重渲染问题解决

RN中最常见的性能问题不是计算太慢，而是渲染了不该渲染的东西。React的渲染机制决定了只要父组件state变化，所有子组件默认都会重新渲染，不管子组件的props是否真的变了。

来看一个典型场景：

```js
function OrderPage() {
  const [count, setCount] = useState(0);
  const [orderList, setOrderList] = useState([]);

  return (
    <View>
      <Text>点击次数: {count}</Text>
      <Button title="计数" onPress={() => setCount(c => c + 1)} />
      <OrderList data={orderList} />
      {/* 每次setCount都会导致OrderList重渲染 */}
      {/* 即使orderList没有变化 */}
    </View>
  );
}
```

这段代码的问题在于：用户点击计数按钮时，`count`状态变化触发`OrderPage`重渲染，`OrderList`虽然接收的`data` prop没有变化，但因为它没有做缓存优化，React默认会重新执行它的render函数。如果`OrderList`内部渲染了上百个订单卡片，这个无意义的重渲染可能消耗几十毫秒。

如何发现无效重渲染？React DevTools的Profiler面板可以直观地看到每次渲染中哪些组件被重新渲染了、各消耗多少时间。在Profiler中勾选"Highlight updates when components render"选项，屏幕上会高亮显示所有正在重渲染的组件，如果某个组件在不该渲染的时候亮了，就说明存在无效重渲染。

> 一句话原则：React的默认行为是"宁可多渲染也不漏渲染"，这在正确性上没问题，但在性能上可能灾难。优化的本质是把"默认多渲染"变成"按需渲染"——只有props真正变化的组件才重新渲染。

### 13.2.2 React.memo组件缓存优化

`React.memo`是解决无效重渲染最直接的工具。它对组件做浅比较，只有props变化时才重新渲染。

基础用法：

```js
const OrderList = React.memo(function OrderList({ data }) {
  return (
    <FlatList
      data={data}
      renderItem={({ item }) => <OrderCard data={item} />}
    />
  );
});
```

加上`React.memo`后，当`OrderPage`因为`count`变化而重渲染时，React会先检查`OrderList`的props。`data`引用没变（同一个数组），浅比较通过，`OrderList`的render函数不会执行。

但`React.memo`有一个陷阱：它只做浅比较。如果props中包含对象、数组或函数，且这些引用每次都变，memo就失效了：

```js
function OrderPage() {
  const [count, setCount] = useState(0);
  const orderList = useSelector(state => state.orders.list);

  return (
    <View>
      <Button title="计数" onPress={() => setCount(c => c + 1)} />
      {/* memo失效：onPress每次都是新函数 */}
      <OrderList
        data={orderList}
        onPress={(id) => navigate('detail', { id })}
      />
    </View>
  );
}
```

这里`onPress`是内联箭头函数，每次render都创建新引用，`React.memo`的浅比较判断props变化，缓存失效。修复方法是用`useCallback`稳定函数引用：

```js
function OrderPage() {
  const [count, setCount] = useState(0);
  const orderList = useSelector(state => state.orders.list);

  // 用useCallback稳定函数引用
  const handlePress = useCallback((id) => {
    navigate('detail', { id });
  }, [navigate]);

  return (
    <View>
      <Button title="计数" onPress={() => setCount(c => c + 1)} />
      <OrderList data={orderList} onPress={handlePress} />
      {/* 现在memo生效了 */}
    </View>
  );
}
```

同理，如果需要传递对象或数组prop，用`useMemo`稳定引用：

```js
// 反面：每次render创建新对象
<FilterPanel config={{ type: 'all', sort: 'desc' }} />

// 正面：useMemo稳定引用
const filterConfig = useMemo(
  () => ({ type: 'all', sort: 'desc' }),
  []
);
<FilterPanel config={filterConfig} />
```

> React.memo、useCallback、useMemo是性能优化的三件套，但它们本身也有开销——memo需要做props比较，useMemo和useCallback需要维护依赖数组。对于简单组件或很少重渲染的组件，加memo反而可能更慢。判断标准很简单：组件render函数执行时间超过2ms，或者在一个频繁更新的父组件下，就值得加memo。否则不需要。

### 13.2.3 合理拆分组件降低渲染开销

组件拆分是性能优化的高杠杆操作。一个臃肿的大组件，任何state变化都会触发整个组件树的重新渲染。把它拆成多个小组件，配合memo，可以让重渲染范围精确到真正变化的子树。

拆分原则：**按state的归属拆分，让state变化的影响范围最小化。**

```js
// 拆分前：一个巨型组件，任何state变化都全量重渲染
function ChatRoom() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [onlineCount, setOnlineCount] = useState(0);

  return (
    <View>
      <Header onlineCount={onlineCount} />
      <MessageList messages={messages} />
      <TextInput value={inputText} onChangeText={setInputText} />
    </View>
  );
  // inputText变化时，Header和MessageList都白白重渲染
}
```

拆分后：

```js
// 拆分后：每个部分独立管理自己的state
function ChatRoom() {
  return (
    <View>
      <OnlineHeader />      {/* 内部管理onlineCount */}
      <MessageListContainer />  {/* 内部管理messages */}
      <InputBox />           {/* 内部管理inputText */}
    </View>
  );
  // 各自的state变化只影响自身，互不干扰
}

const InputBox = React.memo(function InputBox() {
  const [inputText, setInputText] = useState('');
  return <TextInput value={inputText} onChangeText={setInputText} />;
});
```

拆分的核心思路是把state下沉到真正使用它的组件内部，而不是全部放在父组件顶层。这样state变化时只有对应的子组件重渲染，其他兄弟组件不受影响。

> 组件拆分不是为了"代码整洁"，而是为了"渲染隔离"。把state和它的消费者打包到同一个子组件中，是最高效的渲染隔离手段。这比在父组件上堆memo有效得多——memo是被动防御，拆分是主动隔离。怕浪猫在做代码评审时，如果看到一个组件超过300行且包含3个以上不相关的state，一定会建议拆分。这种组件不拆，后续每次修改都在增加性能债务。

### 13.2.4 静态资源与样式渲染优化

RN中样式处理有两段开销：样式对象创建和样式计算。很多开发者习惯在render函数内创建样式对象，每次渲染都重新创建：

```js
// 反面：每次render都创建新样式对象
function Card({ title }) {
  return (
    <View style={{ flex: 1, padding: 16, backgroundColor: '#fff' }}>
      <Text style={{ fontSize: 16, color: '#333' }}>{title}</Text>
    </View>
  );
}
```

虽然内联样式不会导致额外的重渲染（RN内部做了优化），但每次render都创建新对象会增加GC（Garbage Collection）压力。在列表项这种高频渲染的场景下，GC压力会转化为可感知的卡顿。

正确做法是将静态样式提取到组件外部：

```js
// 正面：样式定义在组件外部，只创建一次
const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 16, color: '#333' },
});

function Card({ title }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
    </View>
  );
}
```

`StyleSheet.create`不仅让样式对象只创建一次，还会在原生端注册为编译后的样式ID，渲染时直接引用ID而不是传递整个样式对象，减少Bridge通信的数据量。

对于动态样式，用`useMemo`缓存：

```js
function Badge({ type }) {
  const badgeStyle = useMemo(
    () => [styles.badge, { backgroundColor: type === 'hot' ? '#ff4d4f' : '#1890ff' }],
    [type]
  );
  return <View style={badgeStyle} />;
}
```

### 13.2.5 条件渲染优化与节点精简

RN中每个View节点都有创建和布局计算的开销。节点越多，Shadow线程的计算量越大。条件渲染优化就是在任何时刻只渲染当前需要的节点。

常见问题：用`display: 'none'`隐藏不显示的组件，而不是用条件渲染移除它们。

```js
// 反面：隐藏的组件仍在节点树中
function TabPage({ activeTab }) {
  return (
    <View>
      <View style={{ display: activeTab === 'home' ? 'flex' : 'none' }}>
        <HomeContent />
      </View>
      <View style={{ display: activeTab === 'profile' ? 'flex' : 'none' }}>
        <ProfileContent />
      </View>
      {/* 两个Tab的内容都在节点树中，布局计算双倍 */}
    </View>
  );
}

// 正面：只渲染当前Tab的内容
function TabPage({ activeTab }) {
  return (
    <View>
      {activeTab === 'home' && <HomeContent />}
      {activeTab === 'profile' && <ProfileContent />}
      {/* 节点数减半，布局计算量减半 */}
    </View>
  );
}
```

但要注意：如果Tab切换非常频繁，每次切换都重新创建组件可能比保持隐藏更慢。这种场景需要权衡——频繁切换用display隐藏，不频繁切换用条件渲染。

另一个优化点：减少嵌套层级。RN中`View`嵌套`View`再嵌套`View`是非常常见的模式，每多一层嵌套，Shadow线程就多一层布局计算。能用`flexDirection`和`margin`解决的布局，不要用额外的`View`包裹。

```js
// 反面：多余的包裹View
<View style={styles.card}>
  <View style={styles.row}>
    <View style={styles.left}>
      <Text>标题</Text>
    </View>
    <View style={styles.right}>
      <Text>价格</Text>
    </View>
  </View>
</View>

// 正面：扁平化结构
<View style={styles.card}>
  <View style={styles.row}>
    <Text style={styles.left}>标题</Text>
    <Text style={styles.right}>价格</Text>
  </View>
</View>
```

> 节点精简是性能优化中最"便宜"的优化——不需要改业务逻辑，只需要调整JSX（JavaScript XML）结构。但它的效果往往立竿见影，特别是在列表项和频繁渲染的组件中。怕浪猫的原则是：能少一层就少一层，能不创建节点就不创建节点。曾经有一个项目把列表项从7层嵌套减到3层，列表滑动帧率从35fps直接飙到55fps，没有任何其他改动。这就是节点精简的杠杆效应。

## 13.3 长列表高性能深度优化

### 13.3.1 FlatList核心优化参数详解

FlatList是RN列表组件的绝对主力，也是性能问题的重灾区。怕浪猫见过太多团队用了FlatList但完全不知道它有优化参数，列表项一多就卡到不能看。

FlatList的核心优化参数：

| 参数 | 作用 | 推荐值 | 说明 |
|------|------|--------|------|
| `initialNumToRender` | 首批渲染数量 | 10-15 | 首屏可见数量+少量缓冲 |
| `maxToRenderPerBatch` | 每批增量渲染数量 | 5-10 | 控制单帧渲染负担 |
| `windowSize` | 渲染窗口倍数 | 5-7 | 可见区域高度的倍数 |
| `removeClippedSubviews` | 裁剪不可见子视图 | true | 减少原生节点数 |
| `keyExtractor` | 唯一键提取器 | 必填 | 复用和定位的关键 |
| `getItemLayout` | 跳过布局测量 | 尽量提供 | 精确定位性能飞跃 |

一个优化过的FlatList配置：

```js
<FlatList
  data={productList}
  renderItem={renderItem}
  keyExtractor={(item) => item.id}
  initialNumToRender={10}
  maxToRenderPerBatch={5}
  windowSize={5}
  removeClippedSubviews={true}
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
/>
```

逐个解释为什么这样配。

`initialNumToRender`设为10：假设屏幕可见约8个item，多渲染2个作为滚动缓冲。这个值太大会导致首屏渲染慢，太小会导致快速滚动时出现空白。

`windowSize`设为5：FlatList会渲染可见区域高度5倍的内容。默认值是21，这意味着它会在内存中保留远超需要的组件实例。调到5能显著降低内存占用，代价是快速滚动时可能出现短暂空白。如果你的列表项高度较大（如卡片），可以调到7。

`removeClippedSubviews`设为true：超出屏幕的子视图会被从原生视图树中移除，减少原生节点数量。但这个参数在某些场景有bug——如果列表项中有动画或需要保持状态（如视频播放器），裁剪可能导致状态丢失。使用前需测试。

`getItemLayout`是最重要的优化参数。不提供时，FlatList需要逐个测量item高度才能计算滚动位置，这在大列表中非常慢。提供后，FlatList可以直接通过数学计算定位任意位置的item，`scrollToIndex`等操作从O(n)降到O(1)。

> getItemLayout是一个"知道就知道，不知道就吃亏"的参数。它要求列表项高度固定或可预测，如果列表项高度动态变化（如聊天消息），就无法使用。但对于商品列表、文章列表这类等高场景，getItemLayout带来的性能提升是数量级的。

### 13.3.2 列表项复用与预加载策略

列表项的复用机制是FlatList性能的核心。FlatList维护一个固定大小的cell池，滚动时不可见的cell被回收到池中，新进入可见区域的item从池中取出复用。这避免了频繁创建和销毁组件实例的开销。

但复用机制要正常工作，前提是`keyExtractor`正确设置。如果key不唯一或不稳定，FlatList无法正确匹配cell，会导致复用失败、内容闪烁、甚至崩溃。

```js
// 反面：用index作为key，数据变化时错乱
keyExtractor={(item, index) => String(index)}

// 正面：用稳定的唯一ID
keyExtractor={(item) => item.id}
```

列表项组件必须用`React.memo`包裹，否则FlatList的cell复用时会触发不必要的重渲染：

```js
// 列表项必须做memo优化
const ProductItem = React.memo(function ProductItem({ item, onPress }) {
  return (
    <TouchableOpacity onPress={() => onPress(item.id)}>
      <Image source={{ uri: item.image }} style={styles.img} />
      <Text style={styles.name}>{item.name}</Text>
      <Text style={styles.price}>¥{item.price}</Text>
    </TouchableOpacity>
  );
});

// renderItem用useCallback稳定引用
const renderItem = useCallback(({ item }) => (
  <ProductItem item={item} onPress={handlePress} />
), [handlePress]);
```

预加载策略是在用户滚动到列表底部之前提前加载下一页数据。通过`onEndReached`和`onEndReachedThreshold`配合实现：

```js
<FlatList
  data={list}
  renderItem={renderItem}
  onEndReached={loadMore}
  onEndReachedThreshold={0.5}
  // 距离底部还有半屏时触发加载
  ListFooterComponent={
    loading ? <LoadingSpinner /> : null
  }
/>
```

`onEndReachedThreshold`设为0.5意味着当用户滚动到距离底部还有半个屏幕高度时就开始加载下一页。这样在用户滚到底部之前，新数据大概率已经加载完成，实现了无缝滚动体验。如果设为0（默认），用户必须滚到最底部才触发加载，会有明显的等待感。

### 13.3.3 超大列表分页与分片渲染

当列表数据量达到上万条时，FlatList的优化参数也撑不住。问题不在渲染——FlatList的窗口化渲染本身就能处理大列表。问题在数据层：一次性把10000条数据塞进FlatList的`data` prop，JS线程在diff和布局计算时会卡顿。

分片渲染的思路是：把大数据集分成多个小批次，每帧只追加一批数据到列表中。

```js
function useIncrementalData(fullData, batchSize = 20) {
  const [visibleData, setVisibleData] = useState([]);
  const indexRef = useRef(0);

  useEffect(() => {
    setVisibleData([]);
    indexRef.current = 0;
    loadBatch();
  }, [fullData]);

  const loadBatch = useCallback(() => {
    const next = fullData.slice(
      indexRef.current,
      indexRef.current + batchSize
    );
    if (next.length === 0) return;
    setVisibleData(prev => [...prev, ...next]);
    indexRef.current += batchSize;
    // 下一帧继续加载下一批
    requestAnimationFrame(loadBatch);
  }, [fullData, batchSize]);

  return visibleData;
}
```

这个Hook利用`requestAnimationFrame`在每帧空闲时间追加一批数据，避免一次性处理大数据集阻塞JS线程。用户看到的效果是列表内容逐步填充，而不是一次性卡顿后全部出现。

对于无限滚动场景，分页加载是必须的。但分页加载有一个陷阱：当累积的数据量越来越大时，`data`数组越来越大，FlatList在每次追加新数据时都需要对整个数组做diff，性能会随数据量增长而下降。

解决方案是使用`FlashList`替代`FlatList`。FlashList是Shopify开源的高性能列表组件，它重写了复用机制，在渲染性能和内存效率上都显著优于FlatList：

```js
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={productList}
  renderItem={renderItem}
  estimatedItemSize={80}
  // FlashList的关键参数：预估item高度
  // 不需要精确值，接近就行
/>
```

FlashList的优势在于：它重写了cell复用机制，真正做到了"只渲染可见的cell"，不像FlatList在`windowSize`范围内都渲染。在10000+条数据的大列表场景下，FlashList的帧率比FlatList高出30%-50%。

> 选型建议：数据量500以内用FlatList够了，配置好优化参数就行。数据量500-5000之间，FlatList需要仔细优化。数据量超过5000，直接上FlashList，不要犹豫。Shopify官方文档明确说FlashList是FlatList的替代品，API几乎兼容，迁移成本很低。

### 13.3.4 列表滑动卡顿专项优化

列表滑动卡顿是最让用户感知强烈的性能问题。除了前面讲的优化参数和组件memo，还有一些专项手段。

**1. 列表项中不要做重计算**

```js
// 反面：renderItem中做格式化计算
const renderItem = ({ item }) => {
  const formattedPrice = item.price.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  const formattedDate = new Date(item.timestamp).toLocaleDateString();
  return (
    <View>
      <Text>¥{formattedPrice}</Text>
      <Text>{formattedDate}</Text>
    </View>
  );
};

// 正面：数据层面预先格式化
const processData = (data) => data.map(item => ({
  ...item,
  formattedPrice: formatPrice(item.price),
  formattedDate: formatDate(item.timestamp),
}));

const renderItem = useCallback(({ item }) => (
  <View>
    <Text>¥{item.formattedPrice}</Text>
    <Text>{item.formattedDate}</Text>
  </View>
), []);
```

**2. 图片加载使用native端缓存**

列表中的图片是滑动卡顿的主要元凶。默认的`Image`组件每次都会触发Bridge通信，快速滑动时会堆积大量图片请求。使用`react-native-fast-image`可以显著改善：

```js
import FastImage from 'react-native-fast-image';

const ProductImage = React.memo(function ProductImage({ uri }) {
  return (
    <FastImage
      source={{ uri, priority: FastImage.priority.normal }}
      style={styles.img}
      resizeMode={FastImage.resizeMode.cover}
    />
  );
});
```

FastImage底层使用原生图片缓存库（iOS的SDWebImage、Android的Glide），图片解码在原生线程完成，不阻塞JS线程，且自动管理内存缓存和磁盘缓存。这意味着当列表快速滑动时，图片的加载和解码完全不会影响JS线程的帧率，这是列表滑动流畅的关键保障。

**3. 避免在滑动时更新布局**

```js
// 反面：onScroll中更新state导致重渲染
const [scrollY, setScrollY] = useState(0);

<FlatList
  onScroll={(e) => setScrollY(e.nativeEvent.contentOffset.y)}
  // 每帧都触发setState，列表不停重渲染
/>

// 正面：用Animated.useAnimatedScrollHandler
// 或用ref直接操作原生视图，不经过JS线程
const scrollY = useRef(new Animated.Value(0)).current;

<Animated.FlatList
  onScroll={Animated.event(
    [{ nativeEvent: { contentOffset: { y: scrollY } } }],
    { useNativeDriver: true }
  )}
  // 使用原生驱动，不触发JS线程
/>
```

`useNativeDriver: true`让动画在UI线程执行，完全绕过JS线程。这意味着即使JS线程在做其他事情，滑动动画也不会卡顿。这是Reanimated和Animated原生驱动的核心价值。

> 滑动卡顿的排查口诀：一看item是否memo了，二看图片是否缓存了，三看onScroll是否经过JS线程了，四看getItemLayout是否提供了。四条全做到，列表基本能跑到55fps以上。

### 13.3.5 复杂嵌套列表性能提升方案

实际业务中，列表往往不是简单的平铺结构，而是嵌套的——商品列表中每个item又是一个横向滚动列表，或者SectionList中每个section有自己的header和折叠逻辑。

嵌套列表的性能问题是乘法关系：外层列表渲染N个item，每个item内部又有M个子item，总渲染量是N*M。如果外层10个item每个内部有20个子item，一次渲染就是200个组件实例。

优化策略：**虚拟化嵌套层级**。

```js
// 反面：外层FlatList + 内层FlatList，性能灾难
const renderItem = ({ item }) => (
  <View>
    <Text>{item.category}</Text>
    <FlatList
      horizontal
      data={item.products}
      renderItem={({ item: product }) => (
        <ProductCard data={product} />
      )}
    />
  </View>
);
```

外层和内层都是虚拟列表时，两个列表各自维护自己的渲染窗口和cell池，互相不知道对方的存在，很容易出现渲染冲突——外层滚动时内层也在频繁创建销毁cell。

解决方案一：内层改用ScrollView或直接渲染，只虚拟化外层：

```js
// 方案一：只虚拟化外层
const renderItem = ({ item }) => (
  <View>
    <Text>{item.category}</Text>
    <ScrollView horizontal>
      {item.products.map(p => (
        <ProductCard key={p.id} data={p} />
      ))}
    </ScrollView>
  </View>
);
// 外层FlatList负责虚拟化
// 内层产品数量有限（通常<20），直接渲染
```

解决方案二：用SectionList替代嵌套结构，把二级数据拍平到一级：

```js
// 方案二：拍平数据结构
const sections = categories.map(cat => ({
  title: cat.name,
  data: cat.products,
}));

<SectionList
  sections={sections}
  renderSectionHeader={({ section }) => (
    <Text>{section.title}</Text>
  )}
  renderItem={({ item }) => (
    <ProductCard data={item} />
  )}
  horizontal={false}
/>
```

拍平后只有一个列表实例，所有虚拟化逻辑统一管理，性能可控。

> 嵌套列表的优化原则：能拍平就不嵌套，能只虚拟化一层就不虚拟化两层。如果业务必须嵌套，内层用非虚拟化的ScrollView，把虚拟化责任交给外层。两层虚拟列表是最后的手段，必须配合严格的cell memo和图片缓存才能勉强可用。

## 13.4 内存泄漏检测与专项治理

### 13.4.1 RN常见内存泄漏场景分析

内存泄漏是RN应用中最隐蔽的问题。它不会立即导致崩溃，而是像慢性中毒一样，内存占用持续增长，直到某天用户在低端机型上使用时被系统OOM杀掉。

RN中内存泄漏的本质是：组件卸载后，其引用仍被某个存活的对象持有，导致GC无法回收。常见的泄漏场景有五类：

```
RN内存泄漏五大场景：

  1. 定时器泄漏 — setTimeout/setInterval未清除
  2. 事件监听泄漏 — EventEmitter/DeviceEventEmitter未移除
  3. 网络请求泄漏 — 组件卸载后请求仍在进行，回调持有组件引用
  4. 闭包引用泄漏 — 异步回调中引用了已卸载组件的state/props
  5. 全局缓存泄漏 — 全局Map/Set持续追加不清理
```

一个典型的内存泄漏过程：

```js
function ProfilePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // 泄漏点1：定时器未清除
    const timer = setInterval(() => {
      fetchLatest().then(setData);
    }, 5000);

    // 泄漏点2：事件监听未移除
    const subscription = DeviceEventEmitter.addListener(
      'profileUpdate', (payload) => {
        setData(payload);
      }
    );

    // 泄漏点3：网络请求不可中断
    fetchUserProfile().then(setData);

    // 缺少return cleanup函数！
  }, []);

  return <Text>{data?.name || '加载中'}</Text>;
}
```

这段代码有三个泄漏点：定时器在组件卸载后仍在执行；事件监听在组件卸载后仍注册在EventEmitter上；网络请求在组件卸载后仍会执行回调。三个泄漏点都会持有`setData`函数引用，而`setData`持有组件实例引用，导致组件无法被GC回收。

> 内存泄漏的危害是累积性的，也是最容易被忽视的性能问题类型。用户从首页进入商品详情页再返回首页，如果详情页泄漏了500KB（Kilobyte），用户浏览20个商品详情页就泄漏了10MB。表面上看每次泄漏量不大，但用久了内存就会飙到危险水位。怕浪猫的建议是：每个useEffect都必须有cleanup，这不是可选的，是强制的。

### 13.4.2 定时器与监听事件销毁处理

修复定时器和事件监听泄漏的核心是：在useEffect的cleanup函数中清除。

```js
function ProfilePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // 定时器：在cleanup中clearInterval
    const timer = setInterval(() => {
      fetchLatest().then(setData);
    }, 5000);

    // 事件监听：在cleanup中remove
    const subscription = DeviceEventEmitter.addListener(
      'profileUpdate', (payload) => setData(payload)
    );

    return () => {
      clearInterval(timer);
      subscription.remove();
    };
    // 完美的cleanup
  }, []);
}
```

为了防止忘记写cleanup，可以封装一个自定义Hook统一管理：

```js
// 统一定时器管理Hook
function useInterval(callback, delay) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
    // 自动cleanup，不可能泄漏
  }, [delay]);
}

// 使用：组件卸载时自动清除
function TimerPage() {
  const [count, setCount] = useState(0);
  useInterval(() => setCount(c => c + 1), 1000);
  return <Text>{count}</Text>;
}
```

类似地，可以封装事件监听Hook：

```js
function useEventListener(eventName, handler, dependencies = []) {
  const savedHandler = useRef(handler);

  useEffect(() => {
    savedHandler.current = handler;
  }, [handler]);

  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener(
      eventName, (payload) => savedHandler.current(payload)
    );
    return () => subscription.remove();
  }, [eventName, ...dependencies]);
}
```

> 封装统一Hook的好处是：把"容易忘记的事情"变成"不需要记的事情"。cleanup是每次useEffect都必须做的，但人总会忘。通过Hook封装把cleanup内置到实现中，使用者就不需要关心清理逻辑了。这是工程化思维——用工具解决人的疏忽问题。

### 13.4.3 网络请求中断与资源释放

网络请求泄漏比定时器泄漏更难处理，因为传统的`fetch`和`axios`不支持中断。组件卸载后，正在进行的网络请求仍会执行完，回调函数仍会尝试更新已卸载组件的state。

RN中处理网络请求中断的标准方案是使用`AbortController`：

```js
function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    fetch(url, { signal: controller.signal })
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        if (err.name === 'AbortError') return;
        // 组件已卸载，忽略中断错误
        console.error('请求失败:', err);
      });

    return () => controller.abort();
    // 组件卸载时中断请求
  }, [url]);

  return { data, loading };
}
```

`AbortController`是Web标准API，RN从0.60版本开始支持。调用`controller.abort()`后，正在进行的fetch请求会被中断，Promise会reject并抛出`AbortError`。在catch中判断错误类型，忽略中断错误即可。

对于不支持`AbortController`的第三方请求库（如旧版axios），可以用一个"卸载标志"来模拟中断：

```js
function useFetch(url) {
  const [data, setData] = useState(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    axios.get(url).then(res => {
      if (!isMounted.current) return;
      // 组件已卸载，不更新state
      setData(res.data);
    });

    return () => {
      isMounted.current = false;
      // 标记已卸载，后续回调不执行
    };
  }, [url]);

  return { data };
}
```

这种方式不是真正的中断——请求仍然在进行，只是回调不执行。但它避免了更新已卸载组件state的问题，也消除了对组件实例的引用，让GC可以正常回收。对于绝大多数场景足够用了。

> 网络请求泄漏的特殊之处在于：即使你做了cleanup，请求本身仍在进行，只是回调不执行了。这意味着网络带宽和服务器资源仍在被浪费。如果用户快速切换了10个页面，可能同时有10个请求在进行，但其中9个的响应会被丢弃。所以`AbortController`是更好的方案——它真正中断了请求，不仅释放了内存，还节省了网络资源。

### 13.4.4 大图片资源内存占用优化

图片是RN应用中最大的内存消费者。一张2048x2048的PNG（Portable Network Graphics）图片，磁盘上可能只有200KB，但解码到内存后占用2048*2048*4=16MB（RGBA四通道每通道1字节）。一个列表如果同时缓存了20张这样的图片，内存占用就是320MB。

图片内存优化的核心策略：

**1. 限制图片解码尺寸**

```js
// 反面：原图加载，不限制尺寸
<Image source={{ uri: 'https://cdn.example.com/huge_image.png' }} />

// 正面：服务端按需裁剪
<Image source={{
  uri: 'https://cdn.example.com/image.png?w=375&h=200',
}} />
// 只请求需要的尺寸，解码后内存从16MB降到0.3MB
```

**2. 使用FastImage的缓存优先策略**

```js
import FastImage from 'react-native-fast-image';

<FastImage
  source={{
    uri: imageUrl,
    priority: FastImage.priority.normal,
    cache: FastImage.cacheControl.immutable,
    // immutable: 只下载一次，永不过期
  }}
  style={styles.image}
/>
```

**3. 列表中图片及时释放**

```js
// 使用onViewableItemsChanged控制图片加载
const onViewableItemsChanged = useCallback(({ viewableItems }) => {
  setVisibleIds(new Set(viewableItems.map(i => i.item.id)));
}, []);

const renderItem = ({ item }) => (
  <ProductImage
    uri={visibleIds.has(item.id) ? item.image : null}
    // 不可见的item传null，释放图片内存
  />
);
```

**4. 图片格式优化**

优先使用WebP格式替代PNG/JPEG。WebP在同等画质下体积小30%-50%，解码后内存占用也更小。Android从4.0开始原生支持WebP，iOS从14.0开始原生支持，RN中无需额外处理。

> 图片内存优化的收益是最立竿见影的。怕浪猫有一次把一个列表的图片从原图加载改成服务端裁剪后按需加载，内存峰值直接从400MB降到120MB，效果比任何代码层面的优化都显著。原则很简单：屏幕上显示多大的图，就加载多大的图，不要用4K原图来渲染一个100x100的缩略图。

### 13.4.5 内存泄漏检测工具使用实战

凭代码审查发现内存泄漏效率很低，真正高效的方案是使用工具。

**1. Chrome DevTools Memory面板**

在Debug模式下连接Chrome DevTools，使用Memory面板的"Heap Snapshot"功能。操作步骤：进入目标页面 -> 拍快照A -> 操作页面 -> 返回上一页 -> 手动触发GC -> 拍快照B -> 对比A和B。

```
快照对比分析流程：

  快照A (进入页面前)
    -> 操作页面 (浏览、交互)
    -> 返回上一页 (触发卸载)
    -> 手动GC (点击DevTools的Collect Garbage)
    -> 快照B (卸载后)
    -> 对比 A vs B
    -> 筛选 Delta > 0 的对象
    -> 分析 retained size 最大的对象
```

如果快照B中仍然存在页面A的组件实例或相关对象，说明有泄漏。查看这些对象的retained引用链，就能定位到是谁持有了不该持有的引用。

**2. Xcode Instruments（iOS）**

Xcode的Instruments工具中的"Leaks"模板可以自动检测iOS原生层的内存泄漏。虽然它检测不到JS层的泄漏，但能发现原生模块和第三方库的泄漏。

**3. Android Profiler（Android）**

Android Studio的Profiler中的Memory面板可以实时监控应用的内存使用曲线。操作步骤：进入目标页面 -> 操作 -> 返回 -> 点击"Dump Java Heap" -> 分析。

```js
// 在代码中手动触发GC（仅Debug）
if (__DEV__) {
  // Android: 通过NativeModules触发
  NativeModules.DevSettings.reload();
  // 也可以在Profiler中手动触发GC
}
```

**4. 自动化内存监控**

在生产环境中，可以通过`performance.memory`API（仅Android）或原生模块上报内存数据：

```js
function reportMemoryUsage(tag) {
  if (Platform.OS === 'android' && performance.memory) {
    const { usedJSHeapSize, totalJSHeapSize } = performance.memory;
    // 上报到监控平台
    monitor.report('memory', {
      tag,
      used: usedJSHeapSize,
      total: totalJSHeapSize,
    });
  }
}

// 在页面切换时上报
navigation.addListener('didBlur', () => {
  reportMemoryUsage('页面B卸载后');
});
```

> 内存检测的关键是"对比"。单看一个内存数字没有意义，要看的是"进入页面前 -> 操作 -> 离开页面后"的内存差值。如果差值显著大于0（比如超过5MB），大概率有泄漏。怕浪猫的实践是：每个核心页面都做一次内存回归测试，确保页面切换后内存能回落到合理水平。

## 13.5 网络与加载体验优化

### 13.5.1 接口请求合并与节流优化

网络请求是用户体验的第一道关卡。一个页面如果需要发5个独立请求才能渲染完成，每个请求200ms，串行执行就是1秒的白屏时间。请求合并和并发控制是优化关键。

**1. 请求合并**

```js
// 反面：串行发5个请求
async function loadPageData() {
  const user = await fetchUser();
  const orders = await fetchOrders();
  const coupons = await fetchCoupons();
  const messages = await fetchMessages();
  const banners = await fetchBanners();
  // 总耗时 = 5 * 单请求时间
}

// 正面：并发发5个请求
async function loadPageData() {
  const [user, orders, coupons, messages, banners] =
    await Promise.all([
      fetchUser(),
      fetchOrders(),
      fetchCoupons(),
      fetchMessages(),
      fetchBanners(),
    ]);
  // 总耗时 = max(5个请求时间) ≈ 单请求时间
}
```

`Promise.all`让5个请求并发执行，总耗时取决于最慢的那个请求，而不是5个请求时间之和。在弱网环境下，这个优化能节省数百毫秒。

**2. 请求节流**

对于搜索框这类高频触发场景，每个字符都发请求会浪费大量网络资源：

```js
// 使用防抖控制请求频率
function useDebouncedSearch(query, delay = 300) {
  const [result, setResult] = useState([]);

  useEffect(() => {
    if (!query.trim()) {
      setResult([]);
      return;
    }

    const timer = setTimeout(() => {
      searchAPI(query).then(setResult);
    }, delay);
    // 延迟300ms后发请求，期间继续输入则取消

    return () => clearTimeout(timer);
  }, [query, delay]);

  return result;
}
```

> 请求优化的核心思路是"减少不必要的请求"。合并解决的是"该发但没必要一个个发"的问题，节流解决的是"不该发那么多但用户触发了那么多"的问题。两者配合，网络层的基本功就扎实了。怕浪猫在项目中还遇到过一种隐蔽的请求浪费：多个组件各自独立请求同一接口。比如页面顶部用户信息卡和底部评论模块都需要用户数据，各自发了请求。解决方案是在数据层做请求去重，同一个接口在短时间内的多次调用复用同一个Promise。

### 13.5.2 图片懒加载与预加载策略

图片加载策略需要平衡两个矛盾的需求：加载太早浪费带宽和内存，加载太晚用户看到空白。

**懒加载**：只加载当前可见区域内的图片，不可见的不加载。FlatList的窗口化渲染天然支持这个——只有在渲染窗口内的item才会被渲染，其图片才会被加载。但如果是ScrollView中的图片，需要手动实现懒加载：

```js
import { InteractionManager } from 'react-native';

function LazyImage({ uri }) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    // 等待交互完成后再加载图片
    const handler = InteractionManager.runAfterInteractions(() => {
      setLoaded(true);
    });
    return () => handler.cancel();
  }, []);

  return loaded ? (
    <Image source={{ uri }} style={styles.img} />
  ) : (
    <View style={[styles.img, { backgroundColor: '#f5f5f5' }]} />
  );
}
```

`InteractionManager.runAfterInteractions`会等到所有动画和交互完成后才执行回调，避免图片加载与页面切换动画争抢资源。

**预加载**：在用户可能看到的下一批内容之前提前加载。典型场景是商品列表预加载商品详情页的首图：

```js
// 在列表滚动时预加载详情页图片
import FastImage from 'react-native-fast-image';

const preloadDetailImage = (imageUrl) => {
  FastImage.preload([{ uri: imageUrl }]);
};

// 用户滑动到列表底部区域时，预加载前几个商品的详情图
const onViewableItemsChanged = ({ viewableItems }) => {
  const nearEnd = viewableItems[viewableItems.length - 1];
  if (nearEnd) {
    // 预加载下一个商品的详情页图片
    const nextItem = dataList[nearEnd.index + 1];
    if (nextItem) {
      preloadDetailImage(nextItem.detailImage);
    }
  }
};
```

### 13.5.3 本地缓存与离线数据优化

网络不可靠是移动端的常态。用户在地铁里、电梯里信号不好，如果每次打开应用都依赖网络请求，体验会极差。本地缓存是解决网络不可靠的核心手段。

**多级缓存策略**：

```
数据读取流程：

  用户操作 -> 检查内存缓存
    |--- 命中 -> 直接返回（0ms）
    |--- 未命中 -> 检查磁盘缓存（AsyncStorage）
              |--- 命中 -> 返回磁盘数据 + 后台刷新
              |--- 未命中 -> 发起网络请求
                        |--- 成功 -> 写入内存+磁盘 -> 返回
                        |--- 失败 -> 返回降级数据或错误
```

实现一个多级缓存的数据获取Hook：

```js
function useCachedData(key, fetcher, options = {}) {
  const { ttl = 60000, fallback = null } = options;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      // 1. 检查内存缓存
      const cached = memoryCache.get(key);
      if (cached && Date.now() - cached.ts < ttl) {
        setData(cached.data);
        setLoading(false);
        return; // 缓存有效，直接返回
      }

      // 2. 检查磁盘缓存
      const stored = await AsyncStorage.getItem(key);
      if (stored && !cancelled) {
        const parsed = JSON.parse(stored);
        setData(parsed.data);
        setLoading(false);
        // 后台刷新
        fetcher().then(fresh => {
          if (cancelled) return;
          memoryCache.set(key, { data: fresh, ts: Date.now() });
          AsyncStorage.setItem(key, JSON.stringify({
            data: fresh, ts: Date.now(),
          }));
          setData(fresh);
        }).catch(() => {});
        return;
      }

      // 3. 发起网络请求
      try {
        const fresh = await fetcher();
        if (cancelled) return;
        memoryCache.set(key, { data: fresh, ts: Date.now() });
        AsyncStorage.setItem(key, JSON.stringify({
          data: fresh, ts: Date.now(),
        }));
        setData(fresh);
      } catch {
        setData(fallback);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [key]);

  return { data, loading };
}
```

这个Hook实现了"内存缓存 -> 磁盘缓存 -> 网络请求"的三级降级策略。即使在无网络环境下，也能从磁盘缓存中返回上一次的数据，而不是白屏。后台刷新机制保证数据最终一致性——先展示旧数据，再静默更新。

> 缓存策略的核心不是"缓存什么"，而是"什么时候失效"。TTL（Time To Live）太短等于没缓存，太长数据会过时。怕浪猫的经验值：列表数据TTL设1分钟，配置数据TTL设1小时，静态资源TTL设1天。根据业务对实时性的要求灵活调整。

### 13.5.4 骨架屏与加载状态体验优化

空白加载页是最差的用户体验。即使数据加载只需要500ms，用户看到白屏也会觉得"应用是不是崩了"。骨架屏（Skeleton Screen）通过展示页面结构的灰色占位图，给用户"内容正在加载"的感知，显著降低等待焦虑。

```js
function ProductListPage() {
  const { data, loading } = useFetch('/api/products');

  if (loading && !data) {
    return <ProductListSkeleton />;
  }

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
    />
  );
}

const ProductListSkeleton = () => (
  <View>
    {[1, 2, 3, 4].map(i => (
      <View key={i} style={styles.skeletonItem}>
        <View style={styles.skeletonImg} />
        <View style={styles.skeletonLine} />
        <View style={[styles.skeletonLine, { width: '60%' }]} />
      </View>
    ))}
  </View>
);
```

骨架屏的关键是"结构接近真实内容"。如果真实内容是左图右文的卡片，骨架屏也应该是左灰右灰的卡片，而不是一个居中的Loading转圈。这样用户在加载完成时不会感到视觉跳变。骨架屏还有一个好处：它给了用户"内容即将出现"的预期，而Loading转圈只给了"正在转"的信息。预期的管理是体验设计的核心，而不仅仅是技术实现。

更进一步，可以加入"渐显"过渡，让数据加载完成后平滑替换骨架屏：

```js
function useFadeIn(loading) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!loading) {
      Animated.timing(opacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  }, [loading]);

  return opacity;
}

// 使用
const opacity = useFadeIn(loading);
<Animated.View style={{ opacity }}>
  <FlatList data={data} renderItem={renderItem} />
</Animated.View>
```

> 加载体验的优化本质是"管理用户感知"。500ms的白屏和500ms的骨架屏，客观等待时间一样，但用户体感完全不同。骨架屏让用户觉得"应用在工作"，白屏让用户觉得"应用卡死了"。这不是技术问题，是心理学问题。怕浪猫的原则是：任何超过200ms的加载都必须有过渡状态，不能让用户看到空白。

### 13.5.5 首屏加载速度专项优化方案

首屏加载速度是RN应用的"第一印象"。用户点击应用图标到看到首屏内容的时间，直接影响留存率。优化首屏需要从全链路入手。

**首屏加载耗时拆解**：

```
首屏加载全链路：

  原生启动 (800ms) -> JS Bundle加载 (500ms) -> JS初始化 (300ms)
    -> 首屏组件render (200ms) -> 数据请求 (500ms) -> 首屏内容可见

  总计：约2300ms，目标：<1500ms
```

**1. JS Bundle预加载**

在原生启动阶段就开始加载JS Bundle，而不是等到原生UI准备完才开始。这能节省300-500ms：

```java
// Android: MainActivity中提前加载Bundle
public class MainActivity extends ReactActivity {
  @Override
  protected void onCreate(Bundle savedInstanceState) {
    // 在super.onCreate之前预加载
    getReactNativeHost().getReactInstanceManager()
      .createReactContextInBackground();
    super.onCreate(savedInstanceState);
  }
}
```

**2. 首屏数据预取**

在JS Bundle加载的同时，由原生端发起首屏数据请求，JS加载完成后直接拿数据：

```js
// 原生模块：启动时预取首屏数据
NativeModules.PreloadModule.preloadHomeData();

// JS端：直接读取预取的数据
async function getHomeData() {
  const preloaded = await NativeModules.PreloadModule
    .getPreloadedData();
  if (preloaded) return JSON.parse(preloaded);
  // 预取数据不可用，降级为正常请求
  return fetch('/api/home').then(r => r.json());
}
```

**3. 首屏组件优先渲染**

```js
// 使用InteractionManager让首屏优先渲染
function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    InteractionManager.runAfterInteractions(() => {
      setReady(true);
      // 首屏渲染完成后再加载非关键模块
    });
  }, []);

  return ready ? <HomePage /> : <SplashScreen />;
}
```

**4. Bundle拆分与按需加载**

将非首屏的JS代码拆分成独立Bundle，首屏只加载核心Bundle：

```js
// 使用React.lazy做组件级懒加载
const ProfilePage = React.lazy(() => import('./ProfilePage'));
const SettingsPage = React.lazy(() => import('./SettingsPage'));

function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomePage} />
        {/* 首屏直接加载 */}
        <Stack.Screen name="Profile"
          component={() => (
            <React.Suspense fallback={<Loading />}>
              <ProfilePage />
            </React.Suspense>
          )}
        />
        {/* 按需加载 */}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

> 首屏优化的思路是"并行化"和"延迟化"。并行化：把串行的步骤变成并行，比如原生启动和Bundle加载并行、Bundle加载和数据请求并行。延迟化：把非首屏的内容延迟加载，首屏只加载最小必要内容。两者结合，首屏速度通常能从2.3秒优化到1.2秒左右。怕浪猫做过的最佳案例是把一个3.2秒首屏的电商应用优化到了1.1秒——原生预取+Bundle拆分+图片懒加载三管齐下。

## 13.6 打包瘦身与工程化性能优化

### 13.6.1 冗余依赖与资源文件清理

打包体积直接影响下载速度和安装时间。一个50MB的APK（Android Package）和一个20MB的APK，在4G网络下下载时间差7秒，这7秒可能就让用户取消了安装。

冗余依赖是打包体积膨胀的头号元凶。RN项目中常见的依赖问题：

```
常见冗余依赖类型：

  1. 重复功能库 — 同时装了lodash和lodash-es
  2. 未使用库 — package.json中有但代码没import
  3. 全量引入 — import _ from 'lodash' 而非按需引入
  4. 测试依赖混入 — jest、storybook被打进生产包
  5. 原生库冗余 — 同时引入了moment和dayjs
```

排查工具：

```bash
# 分析Bundle组成
npx react-native bundle --platform android \
  --dev false --entry-file index.js \
  --bundle-output ./bundle-analysis.js

# 使用metro-bundle-analyzer可视化分析
npx metro-bundle-analyzer bundle-analysis.js
```

分析结果会显示每个依赖在Bundle中占用的体积，按大小排序。通常你会发现排名前10的依赖占了总体积的60%以上，优先优化这些大依赖。

按需引入是最快见效的优化：

```js
// 反面：全量引入lodash
import _ from 'lodash';
_.get(obj, 'a.b.c');

// 正面：按需引入
import get from 'lodash/get';
get(obj, 'a.b.c');
// Bundle从70KB降到2KB
```

资源文件清理：删除未使用的图片、字体和JSON文件。RN的打包工具不会自动检测未使用的资源文件，它们会被原样打进APK/IPA（iOS App Store Package）。

```bash
# 查找未使用的图片资源
find src -name "*.png" -o -name "*.jpg" | while read f; do
  name=$(basename "$f" | sed 's/\.[^.]*$//')
  if ! grep -rq "$name" src/ --include="*.js" --include="*.ts"; then
    echo "未使用: $f"
  fi
done
```

> 打包瘦身的第一步不是压缩，而是清理。怕浪猫见过一个项目打包体积80MB，清理完冗余依赖和未使用资源后直接降到35MB。清理的收益远大于压缩——你不用的东西不该出现在包里，这个道理很简单但很多团队做不到。具体操作上，建议每次发版前跑一次依赖分析，把增量体积超过50KB的依赖都审查一遍，确认是否真的需要。这种习惯能防止包体积在不知不觉中膨胀。

### 13.6.2 图片压缩与资源轻量化处理

图片通常占打包体积的50%以上。优化图片资源的ROI（Return on Investment）极高。

**图片压缩工具链**：

```bash
# 使用tinypng批量压缩PNG/JPG
npx tinypng-cli ./src/assets/**/*.png --key YOUR_API_KEY

# PNG转WebP（体积减少30%-50%）
npx cwebp -q 80 input.png -o output.webp

# 批量转换脚本
for f in src/assets/**/*.png; do
  cwebp -q 80 "$f" -o "${f%.png}.webp"
done
```

**在RN中使用WebP**：

```js
// WebP在RN中与PNG使用方式完全一致
const imageSource = Platform.select({
  android: require('./assets/image.webp'),
  ios: parseInt(Platform.Version, 10) >= 14
    ? require('./assets/image.webp')
    : require('./assets/image.png',
    // iOS 14以下不支持WebP，降级为PNG
);
```

**SVG（Scalable Vector Graphics）替代位图**：

对于图标和简单图形，使用SVG比PNG更优——SVG是矢量格式，不随分辨率增大而增大，且支持动态着色：

```js
// 使用react-native-svg渲染SVG图标
import Svg, { Path } from 'react-native-svg';

const HomeIcon = ({ color = '#333', size = 24 }) => (
  <Svg width={size} height={size} viewBox="0 0 24 24">
    <Path d="M3 12L12 3l9 9v9h-6v-6H9v6H3z" fill={color} />
  </Svg>
);
// 一个SVG图标文件几百字节
// 同等PNG图标在多分辨率下需要几套，合计几十KB
```

> 图片优化的策略总结：能用SVG（Scalable Vector Graphics）就不用位图，能用WebP就不用PNG（Portable Network Graphics），能用服务端图片就不用本地图片。本地只保留必须的图标和启动图，其他图片都走CDN（Content Delivery Network）动态加载。这样打包体积中的图片占比可以从50%降到10%以下。

### 13.6.3 Metro打包编译优化配置

Metro是RN的打包工具，它的配置直接影响打包速度和输出Bundle的体积。合理的Metro配置能让打包速度提升30%以上，Bundle体积减少10%-20%。

```js
// metro.config.js
const { getDefaultConfig } = require('metro-config');
const { mergeConfig } = require('metro-config');

const customConfig = {
  transformer: {
    minifierConfig: {
      // 生产环境压缩配置
      mangle: true,
      compress: {
        drop_console: true,
        // 移除console.log
        drop_debugger: true,
        // 移除debugger
        dead_code: true,
        // 移除死代码
        unused: true,
        // 移除未使用变量
      },
    },
  },
  resolver: {
    // 排除不必要的文件
    blacklistRE: /.*\.test\.js$/,
    // 排除测试文件
  },
};

module.exports = (async () => {
  const defaultConfig = await getDefaultConfig();
  return mergeConfig(defaultConfig, customConfig);
})();
```

**关键优化点**：

1. `drop_console: true` — 移除所有`console.log`，生产环境不需要调试日志，每条console语句虽然小但量多了不可忽视。

2. `dead_code: true` + `unused: true` — 移除永远不会执行的代码分支和未使用的变量。配合Tree Shaking效果更好。

3. 依赖预处理 — 第三方库如果提供了ES Module版本，优先使用ESM版本以获得更好的Tree Shaking效果：

```js
//metro.config.js中配置alias
const extraNodeModules = {
  'lodash': 'lodash-es',
  // 使用ESM版本的lodash，支持Tree Shaking
};
```

**开发环境优化**：

开发环境下打包速度比Bundle体积更重要。Metro的缓存机制可以大幅提升增量打包速度：

```js
// metro.config.js 开发环境配置
const isDev = process.env.NODE_ENV === 'development';

const devConfig = {
  transformer: {
    // 开发环境不压缩
    minifierConfig: isDev ? false : undefined,
  },
  server: {
    // 增强缓存
    rewriteRequestUrl: (url) => {
      // 为静态资源添加缓存头
      return url;
    },
  },
};
```

> Metro配置是RN项目工程化的基础设施。很多团队从来不改metro.config.js，用默认配置从开发跑到上线，这是对工程效率的浪费。默认配置是保守的通用方案，不是针对你项目的最优方案。花一个小时调一次Metro配置，开发期间每天节省的打包等待时间能有好几分钟。

### 13.6.4 分包加载与按需加载实现

RN的JS Bundle默认是单文件——所有JS代码都打包成一个`index.android.bundle`和`index.ios.bundle`。应用启动时一次性加载整个Bundle，Bundle越大启动越慢。

分包加载的思路是：把Bundle拆成主包和子包，启动时只加载主包，子包在需要时按需加载。

**方案一：React.lazy组件级懒加载**

```js
// React.lazy + Suspense实现组件级分包
const ProfilePage = React.lazy(() => import('./pages/Profile'));
const OrderPage = React.lazy(() => import('./pages/Order'));
const SettingsPage = React.lazy(() => import('./pages/Settings'));

function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomePage} />
        <Stack.Screen name="Profile" component={() => (
          <React.Suspense fallback={<Loading />}>
            <ProfilePage />
          </React.Suspense>
        )} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

`React.lazy`配合`import()`动态导入语法，打包工具会自动把动态导入的组件拆分成独立chunk。用户在首页时只加载了首页代码，进入Profile页时才加载Profile代码。

**方案二：原生端多Bundle加载**

对于大型应用（如电商类应用），可以拆成多个JS Bundle，由原生端按需加载：

```
多Bundle架构：

  main.bundle (核心框架 + 首页)
    |-- home.bundle (首页模块)
    |-- profile.bundle (个人中心模块)
    |-- order.bundle (订单模块)
    |-- settings.bundle (设置模块)

  启动时加载main.bundle
  进入对应模块时加载对应子bundle
```

```java
// Android原生端加载子Bundle
ReactInstanceManager builder = ReactInstanceManager.builder()
  .setApplication(getApplication())
  .setBundleAssetName("profile.bundle")
  .setJSMainModulePath("index")
  .build();
```

多Bundle方案的实现成本较高，需要原生端配合，但收益也大——首屏只加载核心Bundle（可能只有300KB），而不是整个Bundle（可能5MB）。对于10MB以上的大型RN应用，多Bundle方案几乎andatory。

> 分包加载是大型RN应用的分水岭。Bundle小于2MB不需要分包，2-5MB考虑用React.lazy做组件级分包，超过5MB建议做原生多Bundle方案。怕浪猫参与过一个15MB的电商应用分包改造，首屏加载时间从3.8秒降到了1.2秒，效果非常显著。但分包不是没有成本——模块间的依赖管理、公共代码提取、加载时机控制都需要仔细设计。不要为了分包而分包，要基于首屏速度的实际需求来决策。

### 13.6.5 性能优化落地复盘与规范固化

性能优化不是一次性的工作，而是一个持续的过程。优化做完后如果不固化成规范，代码很快又会腐化回原来的样子。

**性能优化复盘清单**：

```
性能优化复盘Checklist：

  [渲染层]
  - 所有列表项是否用React.memo包裹？
  - 所有回调和对象prop是否用useCallback/useMemo稳定？
  - 组件是否按state归属合理拆分？
  - 静态样式是否提取到组件外部？
  - 条件渲染是否替代了display:none？

  [列表层]
  - FlatList是否配置了所有优化参数？
  - 是否提供了getItemLayout？
  - 列表项中的图片是否使用FastImage？
  - 超大列表是否考虑了FlashList？

  [内存层]
  - 所有useEffect是否有cleanup函数？
  - 定时器和事件监听是否在卸载时清除？
  - 网络请求是否支持中断？
  - 图片是否限制了解码尺寸？

  [网络层]
  - 多个独立请求是否用Promise.all合并？
  - 搜索类请求是否做了防抖？
  - 是否实现了多级缓存策略？
  - 加载状态是否使用了骨架屏？

  [工程层]
  - 是否清理了冗余依赖和未使用资源？
  - 图片是否压缩并转为了WebP？
  - Metro配置是否优化？
  - 是否实现了分包加载？
```

**将规范固化到工程中**：

```js
// .eslintrc.js — 用ESLint规则强制性能规范
module.exports = {
  rules: {
    // 禁止在render中创建内联函数
    'react/jsx-no-bind': [2, { ignoreRefs: true }],
    // 禁止Array index作为key
    'react/no-array-index-key': 2,
    // 检查Hook依赖数组
    'react-hooks/exhaustive-deps': 2,
    // 禁止未使用的state
    'no-unused-vars': [2, { argsIgnorePattern: '^_' }],
  },
};
```

```js
// 自定义ESLint规则：检查FlatList是否配置了优化参数
// eslint-plugin-rn-performance/flat-list-optimization.js
module.exports = {
  meta: { type: 'suggestion' },
  create(context) {
    return {
      JSXOpeningElement(node) {
        if (node.name.name === 'FlatList') {
          const props = node.attributes.map(a => a.name?.name);
          const required = ['keyExtractor', 'removeClippedSubviews'];
          const missing = required.filter(p => !props.includes(p));
          if (missing.length > 0) {
            context.report({
              node,
              message: `FlatList缺少优化参数: ${missing.join(', ')}`,
            });
          }
        }
      },
    };
  },
};
```

> 性能规范的固化比性能优化本身更重要。优化是一次性的，规范是持续的。如果没有规范固化，优化成果会在后续迭代中逐渐被侵蚀，几个月后又回到优化前的状态。怕浪猫在每个RN项目稳定后都会做一次性能规范固化：把踩过的坑写成ESLint规则，把优化清单集成到CI（Continuous Integration）流程中，把性能指标写入监控仪表盘。这样即使团队人员变动，性能基线也不会退化。性能优化最终要解决的不是技术问题，而是工程问题——让"写高性能代码"成为默认行为，而不是需要额外努力的精英行为。

## 结语

性能优化是RN开发中门槛最高、也最能体现工程能力的领域。从组件渲染到长列表调优，从内存治理到打包瘦身，每一块都需要深入理解底层原理并结合实战经验。

怕浪猫在这章中梳理的优化体系，不是理论框架，而是从真实项目中一个一个坑填出来的。每一项优化手段都经过实际验证，每一条建议背后都有对应的踩坑故事。你可以直接拿这套体系用到自己的项目中，根据实际场景做裁剪。

记住几个核心原则：先测量再优化，用数据驱动决策；先定位瓶颈再对症下药，不要盲目改代码；先做高杠杆优化再做低杠杆优化，把时间花在收益最大的地方；最后，把优化成果固化成规范，让性能不随时间退化。

下一篇我们将进入RN自动化测试与持续集成，聊聊如何搭建完整的测试体系和CI/CD（Continuous Integration/Continuous Deployment）流水线。从单元测试到E2E（End-to-End）测试，从代码质量检查到自动化发布流程，帮你建立工程化的质量保障体系。

怕浪猫说：性能优化没有银弹，只有对细节的极致追求。每一毫秒的节省，每一次GC的避免，每一个节点的精简，累积起来就是用户口中的"这个应用真流畅"。别追求一步到位的完美，先做到"比昨天快一点"。

系列进度 13/16
# 第3章 React基础与Next.js组件开发规范

90%的Next.js开发者搞不清服务端组件和客户端组件的边界，导致项目里满天飞'use client'，性能优势荡然无存。更可怕的是，很多人写了几年React，却从未深究过Hooks的闭包陷阱和并发特性的真正用法。我是怕浪猫，一个在React生态里摸爬滚打多年的老兵，今天这一章带你从React底层原理到Next.js组件规范，把那些模糊的边界彻底讲透。这一章内容量比较大，建议先收藏再细读，后续开发中随时查阅。

> 怕浪猫说：框架不是枷锁，而是约定的自由。理解边界，才能真正享受框架带来的红利。

## 3.1 React核心基础回顾（函数组件、Hooks）

React从2018年引入Hooks开始，就注定要走向函数式编程的不归路。到了React 18，类组件已经彻底沦为"遗产代码"。但很多人只是把class换成function，却没真正理解函数组件的运行机制。这一节不是React入门教程，而是为Next.js开发做知识校准——因为App Router的整个架构都建立在函数组件和Hooks之上。

### 3.1.1 函数组件vs类组件：为什么React选择了函数

先看一个对比例子，理解两种组件的根本差异：

```tsx
// 类组件：每次渲染都共享this.state
class Counter extends React.Component {
  state = { count: 0 };
  render() {
    return <button onClick={() => this.setState({ count: this.state.count + 1 })}>
      {this.state.count}
    </button>;
  }
}

// 函数组件：每次渲染都是独立的闭包
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>
    {count}
  </button>;
}
```

表面上看只是写法不同，但底层机制完全不同。类组件的`this.state`是可变的共享状态——同一个实例的this在多次渲染间保持不变，this.state始终指向最新的状态对象。这导致了经典的"闭包陷阱"：在异步回调中通过this.state获取到的值可能已经过期。函数组件每次渲染都产生新的闭包，每次渲染中的state值都是当次渲染的快照，永远不会被篡改。

这意味着函数组件天然避免了`this`指向混乱的问题。在类组件中，你必须小心this的绑定——构造函数中bind、箭头函数属性、class fields语法，各种方案层出不穷，而且每一个都是"补丁"而非"解法"。

React选择函数的核心原因可以从以下几个维度来理解：

| 维度 | 类组件 | 函数组件 |
|------|--------|----------|
| 状态管理 | 共享this，容易产生竞态条件 | 每次渲染独立闭包，状态是快照 |
| 逻辑复用 | HOC（高阶组件）和render props，嵌套地狱 | 自定义Hooks，扁平组合 |
| 类型推导 | TypeScript支持较差，泛型复杂 | 类型推导自然，泛型简单 |
| 编译优化 | 难以做静态分析，this可变 | React Compiler可深度优化 |
| 心智模型 | OOP（面向对象编程）思维，生命周期驱动 | 函数式思维，状态驱动 |
| 代码量 | 通常多30%-50%的样板代码 | 简洁，关注点集中 |

类组件的生命周期方法是面向过程的——你在`componentDidMount`做什么、在`componentDidUpdate`做什么、在`componentWillUnmount`做什么，需要你自己协调时序和依赖关系。函数组件是面向状态的——状态变了就重新渲染，不需要你关心"什么时候"渲染，只需要声明"状态和UI的映射关系"。

这种范式的转变还带来了一个重要的副产品：函数组件更容易被编译器优化。React Compiler（React编译器，原React Forget）正在开发的自动记忆化编译器，能够静态分析函数组件并自动插入等效于useMemo/useCallback的优化，而类组件由于this的可变性和生命周期的复杂性，几乎不可能做类似的优化。

> 怕浪猫说：函数组件不是类组件的语法糖，而是范式的转变。用类组件的思维写函数组件，是大部分bug的根源。

### 3.1.2 核心Hooks速查：useState、useEffect、useMemo、useCallback

这四个Hooks是日常开发中使用频率最高的，但误解也最多。每一个都有其设计哲学和适用边界，不是简单的API调用。

**useState：状态更新是异步批量的**

useState是React中最基础的状态管理Hook，但它的批量更新机制经常让人踩坑。来看一个经典例子：

```tsx
function Demo() {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    setCount(count + 1);  // 用当前闭包的count
    setCount(count + 1);  // 还是同一个count，不是+2
    setCount(prev => prev + 1);  // 函数式更新，才安全
    setCount(prev => prev + 1);
    // 最终count = 2，不是4
  };
  
  return <button onClick={handleClick}>{count}</button>;
}
```

这个例子揭示了useState的两个关键行为。第一，当你在同一个事件处理函数中多次调用setCount时，传入的值如果是基于当前闭包中的count计算的，那么每次计算用的都是同一个值——因为闭包中的count在整个事件处理函数执行期间不会更新。第二，如果你使用函数式更新（传入一个接收prev并返回新值的函数），React会将这些更新排队，依次执行，最终得到正确的结果。

React 18之后，所有状态更新都自动批量处理（Automatic Batching，自动批处理），不再局限于React事件处理器内部。这意味着在Promise、setTimeout、fetch回调中的多次setState也会被批量合并。这是一个重大改进——在React 17中，setTimeout内的多次setState会触发多次重渲染，而在React 18中只会触发一次。

useRef也是状态相关Hook，但它不触发重渲染。useRef返回一个可变对象，其current属性在组件整个生命周期内保持不变。常用于保存定时器ID、DOM引用、或不触发重渲染的可变值。

**useEffect：不是生命周期，是同步引擎**

useEffect最常见的误解就是把它当成`componentDidMount + componentDidUpdate + componentWillUnmount`的组合。这种理解不仅在概念上是错误的，在实践中也会导致错误的代码组织方式。

实际上，useEffect的设计理念是"声明一个同步副作用"——把组件和外部世界（DOM操作、事件订阅、网络请求、定时器等）同步。每次组件渲染后，React会检查effect的依赖数组是否变化，如果变化了就执行同步逻辑，同时先执行上一次的清理函数。

```tsx
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    let cancelled = false;
    fetchUser(userId).then(data => {
      if (!cancelled) setUser(data);
    });
    return () => { cancelled = true; };
  }, [userId]);
  
  return <div>{user?.name}</div>;
}
```

关键点：依赖数组不是"什么时候执行"的声明，而是"什么时候需要重新同步"的声明。当userId变化时，之前的用户数据已经过期，需要重新获取。清理函数中的cancelled标志确保了竞态条件下的安全——如果userId在请求返回前就变化了，旧的请求结果不会被设置到state中。

useEffect最常见的问题有三个：依赖遗漏导致闭包陷阱（使用了未在依赖数组中的变量）、依赖过多导致无限循环（把对象或数组作为依赖项，每次渲染引用不同）、清理函数缺失导致内存泄漏（订阅或定时器未被清除）。

使用ESLint的react-hooks/exhaustive-deps规则可以帮助你发现遗漏的依赖。但理解原理比依赖工具更重要——如果你知道为什么需要某个依赖，就能判断是否应该调整代码结构而非简单添加依赖。

**useMemo和useCallback：性能优化的双刃剑**

useMemo缓存计算结果，useCallback缓存函数引用。它们的本质都是"记忆化"（Memoization），在依赖不变时返回缓存的值而非重新计算。

```tsx
// useMemo：缓存计算结果
const sortedList = useMemo(
  () => items.sort((a, b) => a.priority - b.priority),
  [items]
);

// useCallback：缓存函数引用
const handleSubmit = useCallback(
  (data) => saveData(data),
  [saveData]
);
```

很多人无脑加useMemo和useCallback，觉得"加了总比不加好"。事实上，每个Hook调用本身就有开销——React需要在内部维护一个缓存链表，每次渲染时比对依赖数组的每一项。如果一个计算只需要1ms，useMemo的缓存比对开销可能比重新计算还大。更糟的是，不必要的useMemo会增加GC（Garbage Collection，垃圾回收）压力，因为缓存的值会一直占用内存直到依赖变化。

经验法则：只有在以下场景才考虑使用：
- useMemo：计算成本显著（如排序大数组、复杂数据转换、格式化大量数据）且依赖项不频繁变化
- useCallback：函数作为props传给子组件，且子组件使用了React.memo进行包裹，避免因函数引用变化导致子组件不必要的重渲染

一个更好的判断标准：如果你移除useMemo/useCallback后没有观察到性能问题，那就不需要它。React Compiler正在开发中，未来会自动处理大部分记忆化需求，手写useMemo/useCallback的场景会越来越少。

> 怕浪猫说：性能优化不是"预防性用药"，而是"对症下药"。先测量，再优化。Profile工具告诉你哪里慢，而不是你的直觉。

### 3.1.3 自定义Hooks：逻辑复用的正确姿势

自定义Hooks是React提供的最优雅的逻辑复用方案。在Hooks出现之前，React社区尝试了HOC（Higher-Order Component，高阶组件）、render props（渲染属性）、Context等多种方案，但都有各自的痛点。HOC会导致组件嵌套地狱（Wrapper Hell），属性转发和类型推导困难；render props虽然灵活但导致JSX嵌套层级深，可读性差。

自定义Hooks通过简单的函数组合解决了这些问题。一个自定义Hook就是一个以use开头的普通函数，内部可以使用任何其他Hooks。逻辑可以像积木一样自由组合。

```tsx
// 一个标准的自定义Hook：窗口尺寸监听
function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handler = () => setSize({
      width: window.innerWidth,
      height: window.innerHeight,
    });
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  return size;
}

// 使用：干净利落
function ResponsiveLayout() {
  const { width } = useWindowSize();
  return <div>{width < 768 ? <MobileNav /> : <DesktopNav />}</div>;
}
```

自定义Hooks的命名规范和设计原则：
- 必须以`use`开头，React的linter（代码检查工具，如eslint-plugin-react-hooks）依赖这个前缀来判断是否为Hook，从而应用相应的规则检查
- 返回值可以是值、对象或数组，根据使用场景选择。如果返回多个值，推荐返回对象（可解构命名，添加字段不破坏调用方）
- 内部可以调用其他Hooks，这就是组合的精髓。一个复杂的Hook可以由多个简单Hook组合而成
- 保持单一职责，一个Hook只做一件事。需要组合逻辑时，在组件或上层Hook中组合

一个容易踩的坑：自定义Hooks中的状态是各调用处独立的，不会共享。每次调用useWindowSize都会创建一个新的state和一个新的event listener。如果你需要跨组件共享状态，应该用Context（上下文）或状态管理库（如Zustand、Jotai）。

```tsx
// 两个组件调用同一个Hook，状态完全独立
function CompA() {
  const { width } = useWindowSize();  // 独立的size状态
  return <div>A: {width}</div>;
}
function CompB() {
  const { width } = useWindowSize();  // 另一个独立的size状态
  return <div>B: {width}</div>;
}
// 两个组件各有一个resize监听器，state互不影响
```

自定义Hooks的最佳实践还包括：为复杂的Hook编写测试（使用@testing-library/react-hooks或React 18的act测试工具）、在Hook内部处理错误边界（如请求失败时返回fallback状态）、提供合理的默认值。一个设计良好的Hook应该让调用方不需要关心内部实现细节，只需要关注输入和输出。

### 3.1.4 Hooks使用规则与常见违反场景

React对Hooks的使用有两条铁律，违反任何一条都会导致难以排查的bug——不是可能出错，而是一定会在某个时间点出错。

**规则一：只在顶层调用Hooks**

不能在循环、条件语句或嵌套函数中调用Hooks。React依赖Hooks的调用顺序来对应内部的双向链表——每次渲染时，React按顺序读取链表中的节点来获取或更新每个Hook的状态。如果某次渲染中Hook的调用顺序变化了（比如条件分支导致少调用了一个useState），整个链表就会错位，后面的所有Hook都会读取到错误的状态。

```tsx
// 错误：条件调用Hook
function BadComponent({ condition }) {
  if (condition) {
    const [data, setData] = useState(null);  // 违反规则！
  }
  const [count, setCount] = useState(0);  // 这行可能错位
  // 当condition为true时，useState链表: [data, count]
  // 当condition为false时，useState链表: [count]
  // React会把count的状态读取到data的位置
}

// 正确：条件逻辑放在Hook内部
function GoodComponent({ condition }) {
  const [data, setData] = useState(null);
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    if (condition) {
      fetchData().then(setData);
    }
  }, [condition]);
}
```

**规则二：只在React函数中调用Hooks**

只能在函数组件或自定义Hooks中调用，不能在普通函数中调用。React通过组件的调用栈来判断Hooks的执行上下文，普通函数没有这个上下文。但有一个例外：自定义Hooks本身就是"React函数"，所以可以在自定义Hooks中调用其他Hooks。

实际开发中最常见的违反场景及修复方式：

| 场景 | 错误做法 | 正确做法 |
|------|----------|----------|
| 条件渲染 | if内调用useState | 始终调用useState，条件放useEffect内 |
| 循环列表 | map内调用useState | 用state数组或useReducer管理 |
| 事件回调 | onClick内调用useState | 在组件顶层调用Hook |
| 工具函数 | utils.js里调用useEffect | 改为useXxx自定义Hook |
| 异步函数 | await后调用useEffect | 在useEffect内部await |

ESLint的react-hooks/rules-of-hooks规则可以在编译时捕获这些错误，强烈建议在项目中启用。但理解原理比依赖工具更重要——知道为什么有这些规则，才能在特殊场景下做出正确判断。

### 3.1.5 React 18并发特性：useTransition、useDeferredValue

React 18最重要的特性是Concurrent Rendering（并发渲染），它允许React中断、暂停、恢复渲染过程。在React 18之前，一旦开始渲染就无法中断——如果渲染一个巨大的列表需要200ms，这200ms内用户的点击、输入等交互全部被阻塞。并发渲染改变了一切。

两个核心Hook让开发者能主动利用并发能力，将渲染任务标记为"可中断的"。

**useTransition：把紧急更新变为非紧急更新**

在搜索场景中，用户输入时有两件事需要发生：输入框值更新（紧急，必须立即响应否则用户会感觉卡顿）、搜索结果列表更新（可以延迟，因为用户知道搜索需要时间）。useTransition让你把后者标记为非紧急更新。

```tsx
function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    setQuery(e.target.value);  // 紧急更新：输入框立即响应
    startTransition(() => {
      setResults(search(e.target.value));  // 非紧急：结果可延迟
    });
  };

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <ResultList results={results} />}
    </>
  );
}
```

并发渲染的工作流程：

```
用户输入 → setQuery (紧急更新，同步渲染)
         → startTransition → setResults (非紧急更新，可中断)
                              ↓
                    React在空闲时间渲染结果列表
                              ↓
                    如果用户又输入了新字符
                              ↓
                    React中断当前渲染 → 基于最新输入重新渲染
                              ↓
                    渲染完成后 commit 到 DOM
```

isPending状态在transition期间为true，你可以用它显示加载指示器。这比传统的debounce方案更优雅，因为React自己知道什么时候渲染完成了，不需要你猜一个延迟时间。

**useDeferredValue：延迟一个值的传播**

useDeferredValue从另一个角度解决同样的问题。它不是让你标记更新为非紧急，而是延迟一个具体值的传播——组件仍然立即用旧值渲染，React在空闲时再用新值重新渲染。

```tsx
function FilterList({ items }) {
  const [filter, setFilter] = useState('');
  const deferredFilter = useDeferredValue(filter);
  
  const filtered = useMemo(
    () => items.filter(i => i.includes(deferredFilter)),
    [items, deferredFilter]
  );
  
  const isStale = filter !== deferredFilter;
  
  return (
    <>
      <input value={filter} onChange={e => setFilter(e.target.value)} />
      <ul style={{ opacity: isStale ? 0.7 : 1 }}>
        {filtered.map(item => <li key={item}>{item}</li>)}
      </ul>
    </>
  );
}
```

当filter变化时，input立即更新（用户输入不卡顿），但filtered列表仍然用旧的deferredFilter值渲染。React在空闲时更新deferredFilter，列表才会重新渲染。isStale标志让你能在视觉上提示用户"数据正在更新"。

两者的区别和选择标准：useTransition是你主动标记一段状态更新为非紧急，需要你能在事件处理函数中控制状态更新。useDeferredValue是你延迟一个具体值的传播，适合你只接收一个props值无法控制其更新时机的场景。如果你能控制状态更新，优先用useTransition因为它更显式；如果你在接收props的子组件中需要延迟，用useDeferredValue。

> 怕浪猫说：并发特性不是银弹，它解决的是"大块渲染阻塞交互"的问题。如果你的渲染本身就很快（几毫秒），加了反而增加复杂度和潜在的不一致状态。先确保渲染性能合理，再考虑用并发特性优化体验。

## 3.2 Next.js组件分类：服务端组件、客户端组件

Next.js App Router（应用路由器）基于React Server Components构建，这是React架构层面最大的一次变革。理解服务端组件和客户端组件的区别，是写好Next.js应用的前提——不仅是功能能否运行的区别，更是性能、安全、架构的全面差异。

### 3.2.1 RSC（React Server Components，React服务端组件）核心原理

传统React应用的所有组件都在客户端运行——服务端只负责发送HTML骨架和JS bundle。这意味着你的数据库查询逻辑、API密钥、大型第三方库的代码最终都会被打包到客户端JS中，即使用户的浏览器根本不需要执行这些代码。

RSC打破了这一限制：组件可以在服务端运行，直接访问数据库和文件系统，渲染结果以特殊的序列化格式（RSC Payload）流式传输给客户端。客户端只需要接收渲染好的UI结构，不需要下载这些组件的JS代码。

```
传统SSR架构（Next.js Pages Router）：
  服务端 → 生成完整HTML → 客户端下载全部JS → 水合(hydration)
  → 所有组件在客户端运行 → 后续交互全靠客户端JS

RSC架构（Next.js App Router）：
  服务端组件 → 在服务端执行，输出RSC Payload（序列化组件树）
  客户端组件 → 在客户端运行，处理交互
  两者混合在一棵树中 → 由React协调器统一管理
  → 服务端组件的JS代码永远不发送到客户端
```

RSC Payload是一种类似JSON的序列化格式，描述了组件树的结构。它不是HTML，也不是完整的JS，而是一组"指令"，告诉客户端如何重建组件树。这种设计使得服务端组件的代码完全不会出现在客户端bundle中——只有渲染结果被传输。

核心区别对比：

| 维度 | 服务端组件 | 客户端组件 |
|------|------------|------------|
| 运行环境 | 仅服务端 | 服务端(SSR预渲染) + 客户端 |
| 能否使用Hooks | 不能用useState/useEffect等 | 可以用所有Hooks |
| 能否访问后端资源 | 可以直接访问数据库/文件系统 | 不可以 |
| 能否使用浏览器API | 不可以 | 可以 |
| JS Bundle体积 | 不计入客户端bundle | 计入客户端bundle |
| 渲染时机 | 每次请求(或构建时静态生成) | 服务端预渲染 + 客户端水合 |
| 安全性 | 可使用敏感API密钥 | 代码暴露给客户端 |
| 数据获取 | async/await直接获取 | 通过API或Server Action |

这个表格的信息量很大，建议收藏后反复对照。在实际开发中，你应该默认使用服务端组件，只在必须交互时才使用客户端组件。这个原则被称为"服务端优先"（Server-first）。

### 3.2.2 服务端组件的能力边界：能做什么、不能做什么

理解能力边界是正确使用RSC的关键。先看服务端组件能做什么：

- 直接读取数据库、文件系统、环境变量，无需额外API层
- 使用敏感的API密钥（数据库连接串、第三方服务密钥等不会暴露给客户端）
- 渲染大量数据列表而不增加客户端JS体积——10000条数据在服务端渲染成HTML，客户端零JS开销
- 导入大型第三方库（如语法高亮、Markdown解析、日期处理库）不计入bundle
- 直接获取数据（替代Pages Router中getServerSideProps的角色），使用async/await语法
- 通过Server Actions（服务端动作）处理表单提交和数据变更

```tsx
// 服务端组件：直接读数据库，安全且高效
import { db } from '@/lib/db';

export default async function PostList() {
  const posts = await db.post.findMany({
    orderBy: { createdAt: 'desc' },
    take: 20,
    include: { author: true },
  });
  
  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>
          <h2>{post.title}</h2>
          <span>作者：{post.author.name}</span>
        </li>
      ))}
    </ul>
  );
}
```

这段代码运行在服务端，数据库查询、Prisma ORM的代码、作者信息的关联查询——这些全部不会出现在客户端的JS bundle中。客户端只收到渲染好的HTML结构。

再看服务端组件不能做的：
- 不能使用useState、useEffect、useRef、useReducer等状态和副作用Hooks（这些Hooks需要客户端运行时）
- 不能绑定事件处理器（onClick、onChange、onSubmit等——事件处理需要浏览器DOM环境）
- 不能使用浏览器API（window、document、localStorage、navigator、IntersectionObserver等）
- 不能使用React Context（useContext——Context需要在客户端组件树中提供和消费）
- 不能使用大部分第三方交互库（如react-dropzone、react-dnd等依赖浏览器API的库）

这些限制本质上都指向同一个原因：服务端组件的代码不在浏览器中执行，而上述功能都依赖浏览器运行时。

### 3.2.3 客户端组件的触发条件与运行环境

客户端组件是通过`'use client'`指令声明的。它的运行环境分两个阶段：服务端预渲染（SSR）和客户端水合（Hydration）后。

在服务端预渲染阶段，客户端组件会被执行一次，生成初始HTML。但这次执行中，useEffect不会运行（因为它是副作用，只在客户端执行），事件处理器不会被绑定（服务端没有DOM事件系统）。组件只是"走过场"地渲染出初始UI。

水合之后，组件才完全"活过来"——useEffect开始运行，事件处理器被绑定，状态开始可以被更新。此后的所有交互都在客户端完成，不需要服务端参与。

什么情况下必须用客户端组件：
- 需要状态管理（useState、useReducer、useContext等）
- 需要副作用（useEffect、useLayoutEffect、useInsertionEffect）
- 需要事件处理（onClick、onChange、onSubmit、onScroll等）
- 需要浏览器API（window、document、localStorage、IntersectionObserver、ResizeObserver等）
- 使用了仅支持客户端的第三方库（如图表库、拖拽库、富文本编辑器等）

```tsx
'use client';

import { useState } from 'react';

export default function LikeButton({ postId }: { postId: string }) {
  const [liked, setLiked] = useState(false);
  
  return (
    <button onClick={() => setLiked(!liked)}>
      {liked ? '已赞' : '点赞'}
    </button>
  );
}
```

### 3.2.4 服务端组件与客户端组件的渲染流程对比

理解渲染流程对于调试和优化至关重要。两种组件的渲染路径完全不同，这决定了它们的性能特征和数据获取方式。

**服务端组件渲染流程：**

```
请求进入 → Next.js路由匹配 → 执行服务端组件async函数
         → await获取数据 → 渲染JSX为React元素树
         → 序列化为RSC Payload → 流式传输给客户端
         → React在客户端重建组件树 → 渲染到DOM
```

服务端组件的渲染是"按需"的——每次路由导航都会触发服务端重新渲染对应的组件树，生成新的RSC Payload。这意味着数据始终是最新的（对于动态渲染），但每次导航都需要服务端计算。

**客户端组件渲染流程：**

```
首次加载：
  服务端：SSR预渲染 → 生成HTML（初始UI） + RSC Payload
  客户端：下载JS Bundle → Hydration(水合) → 组件可交互
  
后续交互：
  状态更新 → 组件在客户端重新渲染 → 更新DOM
  → 不需要服务端参与
```

关键区别在于"谁负责后续更新"。服务端组件的更新需要服务端重新渲染并推送新的RSC Payload（通过路由导航触发）。客户端组件的更新完全在浏览器中完成，不需要服务端参与。这就是为什么交互性组件必须是客户端组件——你不可能每次按钮点击都去服务端请求新的UI。

### 3.2.5 组件树混合渲染：Server → Client → Server的边界规则

这是整个RSC架构中最容易混淆的部分。组件树的混合渲染遵循一个核心规则：客户端边界是"单向门"——一旦从服务端组件进入客户端组件，就不能再回到服务端组件。

```
Server Component (根)
  ├── Server Component (子)        ← 可以，服务端内自由嵌套
  │     └── Client Component (孙)  ← 可以，进入客户端边界
  │           └── Client Component (曾孙)  ← 可以，客户端内自由嵌套
  │                 └── Server Component ???  ← 不可以！不能回到服务端
  └── Client Component (子)        ← 可以
        └── Server Component ???   ← 不可以
```

为什么不能从客户端组件回到服务端组件？因为客户端组件的JS代码在浏览器中运行，而服务端组件的代码不在浏览器中——浏览器没有服务端组件的代码来执行它。当你import一个服务端组件到客户端组件中时， bundler会把它的代码也打包进客户端bundle，这就违反了RSC的设计初衷。

但有一个重要的"后门"：客户端组件可以通过`children` props接收服务端组件作为子节点。这不是回到服务端，而是服务端组件在外层服务端组件中预先渲染后，以渲染结果（React元素，本质上是描述UI结构的对象）的形式传入客户端组件。客户端组件不需要执行服务端组件的代码，只需要把已经渲染好的React元素放到正确的位置。

```tsx
// Layout.tsx (服务端组件)
import ClientSidebar from './ClientSidebar';
import ServerContent from './ServerContent';

export default function Layout() {
  return (
    <div className="flex">
      <ClientSidebar>
        {/* ServerContent在服务端渲染，结果作为children传入 */}
        <ServerContent />
      </ClientSidebar>
    </div>
  );
}

// ClientSidebar.tsx (客户端组件)
'use client';
export default function ClientSidebar({ children }) {
  const [open, setOpen] = useState(false);
  return (
    <aside>
      <button onClick={() => setOpen(!open)}>切换</button>
      {open && children}
    </aside>
  );
}
```

这个模式在实际开发中极为常用。比如一个客户端的标签页组件，每个标签页的内容是服务端组件渲染的；或者一个客户端的折叠面板，展开后显示服务端组件获取的数据。关键是：服务端组件在服务端渲染完毕后，其结果通过children这个"虫洞"传入客户端组件。

> 怕浪猫说：children props是RSC架构中的"虫洞"——它让你在客户端边界内使用服务端组件的渲染结果，而不违反单向门规则。掌握这个模式，你就掌握了RSC组件组合的精髓。

## 3.3 'use client' 指令使用场景与规范

'use client'是Next.js App Router中最常被滥用的指令。很多人一遇到报错就加'use client'，这和一遇到bug就重启一样——临时有效，但治标不治本。每一次不必要的'use client'都在增加客户端JS体积，侵蚀RSC带来的性能优势。

### 3.3.1 'use client'指令的位置与作用域

'use client'必须放在文件的第一行（可以有注释在前），是一个文件级指令，不是组件级指令。你不能在文件中间声明它，也不能只让文件中的某个组件是客户端组件。

```tsx
// 正确：文件顶部
'use client';

import { useState } from 'react';

export default function MyComponent() {
  const [count, setCount] = useState(0);
  return <div>{count}</div>;
}
```

作用域规则：一旦在某个文件声明了'use client'，该文件导出的所有组件都是客户端组件。而且，该文件导入的所有其他模块也会被视为客户端模块——这就是"传染性"，我们后面会详细讲。

'use client'还可以声明在目录级别的入口文件中（如layout.tsx或page.tsx），这样该文件及其所有子组件都会被视为客户端代码。但这种做法通常是不推荐的，因为它会把整棵子树都拉入客户端bundle。

### 3.3.2 必须使用'use client'的5种场景

以下是清单型总结，建议收藏作为开发时的检查清单：

**场景1：交互与状态管理**
当组件需要维护内部状态或响应用户交互事件时，必须声明为客户端组件。这是最常见的使用场景。

```tsx
'use client';
import { useState } from 'react';
export function Dropdown() {
  const [open, setOpen] = useState(false);
  return <button onClick={() => setOpen(!open)}>{open ? '关' : '开'}</button>;
}
```

**场景2：生命周期副作用**
当组件需要在挂载后执行副作用（如分析追踪、页面访问统计）时，需要useEffect，因此必须是客户端组件。

```tsx
'use client';
import { useEffect, useState } from 'react';
export function PageViewTracker({ path }: { path: string }) {
  useEffect(() => {
    analytics.track('page_view', { path });
  }, [path]);
  return null;
}
```

**场景3：浏览器API访问**
当组件需要读取或操作浏览器API（如localStorage、sessionStorage、navigator等）时，必须声明为客户端组件。

```tsx
'use client';
import { useState, useEffect } from 'react';
export function LocalStorageBadge() {
  const [theme, setTheme] = useState('light');
  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved) setTheme(saved);
  }, []);
  return <span>{theme}</span>;
}
```

**场景4：使用仅支持客户端的第三方库**
某些第三方库依赖DOM或浏览器环境（如图表库、拖拽库、富文本编辑器），使用这些库的组件必须声明为客户端组件。配合next/dynamic可以禁用SSR。

```tsx
'use client';
import dynamic from 'next/dynamic';
const Chart = dynamic(() => import('react-chartjs-2'), { ssr: false });
export function Dashboard() {
  return <Chart data={...} />;
}
```

**场景5：React Context Provider**
Context的Provider必须在客户端组件中定义，因为Context依赖React的客户端运行时。这是很多初学者容易忽略的场景。

```tsx
'use client';
import { createContext, useContext, useState } from 'react';
const ThemeContext = createContext('light');

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### 3.3.3 不需要'use client'的常见误用

误用1：在服务端组件中导入客户端组件时给服务端组件也加'use client'

服务端组件可以自由导入和使用客户端组件，不需要自身声明'use client'。客户端组件的'use client'指令会在客户端边界生效。

```tsx
// PostPage.tsx (服务端组件) - 不需要'use client'
import LikeButton from './LikeButton';  // LikeButton自己声明了'use client'

export default function PostPage() {
  return (
    <article>
      <h1>标题</h1>
      <LikeButton postId="1" />  {/* 直接用就行 */}
    </article>
  );
}
```

误用2：只是为了让async/await工作而加'use client'

服务端组件天然支持async/await，这是它的核心能力之一。如果你在组件里直接await数据库查询或fetch请求，那它应该是服务端组件。客户端组件不支持async导出——你不能在客户端组件的顶层使用await。

误用3：整个layout都变成客户端组件

很多开发者遇到"layout中需要useState"的错误时，直接给整个layout加'use client'。正确的做法是把需要状态的逻辑提取到一个客户端子组件中，layout本身保持服务端组件。

```tsx
// 错误做法：整个layout变成客户端
'use client';
export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return (
    <div>
      <Sidebar open={sidebarOpen} onToggle={setSidebarOpen} />
      {children}
    </div>
  );
}

// 正确做法：layout保持服务端组件，Sidebar独立为客户端组件
import Sidebar from './Sidebar';
export default function Layout({ children }) {
  return (
    <div>
      <Sidebar />  {/* Sidebar内部自己管理状态 */}
      {children}
    </div>
  );
}
```

> 怕浪猫说：'use client'是"尽量不用，而非尽量用"。每多一个'use client'，就多一份客户端JS负担。养成默认服务端组件的习惯，需要时才添加。

### 3.3.4 'use client'与组件导入的传染性规则

当一个文件声明了'use client'，它import的所有模块也会被拉入客户端bundle。这不是Next.js的特殊行为，而是ES模块的自然行为——import语句在编译时就会被解析，bundler会追踪整个依赖图。

这意味着一个不小心的import就可能把敏感的服务端代码泄露到客户端：

```tsx
// utils.ts - 本意是同时包含服务端和客户端工具函数
import { db } from './db';  // 包含数据库连接！

export function formatDate(d: Date) { ... }
export function getUser(id: string) { return db.user.findUnique({ where: { id } }); }
```

```tsx
// ClientComponent.tsx
'use client';
import { formatDate } from './utils';  // 整个utils.ts(包括db)被拉入客户端！
// 即使你只用了formatDate，bundler也会包含整个utils.ts模块
```

这不仅是性能问题，更是安全问题——数据库连接字符串可能被暴露在客户端bundle中。这不是Next.js的bug，而是ES模块的依赖追踪机制决定的。

解决方法是把服务端和客户端的工具函数严格分到不同文件：

```
/lib
  /server
    db.ts           # 数据库相关，只在服务端组件中import
    queries.ts      # 服务端查询函数
  /client
    format.ts       # 纯函数，客户端可用
    validate.ts     # 表单校验
  /shared
    types.ts        # TypeScript类型定义，无运行时代码
    constants.ts    # 常量定义
```

这种分层不仅避免了传染性问题，还让代码组织更清晰——一眼就能看出哪些文件是服务端专属的。

### 3.3.5 客户端边界优化：减少客户端JS（JavaScript）体积

减少客户端JS体积是Next.js性能优化的核心。RSC的全部意义就在于"把代码留在服务端"，如果不注意客户端边界优化，RSC的优势就会被抵消。

**策略1：组件拆分——把客户端逻辑下沉到叶子节点**

这是最重要的优化策略。当一个组件树中只有一小部分需要交互时，只把那一小部分标记为客户端组件，其余保持服务端组件。

```tsx
// 不好：整个列表都是客户端组件
'use client';
export function PostList({ posts }) {
  const [filter, setFilter] = useState('');
  return (
    <div>
      <input value={filter} onChange={...} />
      {posts.filter(...).map(p => <PostCard key={p.id} post={p} />)}
    </div>
  );
}

// 好：只有搜索框是客户端，列表和卡片保持服务端组件
// PostList.tsx (服务端组件)
import SearchBar from './SearchBar';
export default async function PostList() {
  const posts = await getPosts();
  return (
    <div>
      <SearchBar />
      {posts.map(p => <PostCard key={p.id} post={p} />)}
    </div>
  );
}
```

**策略2：动态导入非关键客户端组件**

对于体积大或非首次渲染必需的客户端组件，使用next/dynamic进行代码分割。这样组件只会在需要时才被下载。

```tsx
import dynamic from 'next/dynamic';
const HeavyEditor = dynamic(() => import('./HeavyEditor'), {
  loading: () => <p>加载中...</p>,
  ssr: false,  // 禁用SSR预渲染
});
```

**策略3：将静态内容提取为服务端组件**

即使一个页面大部分是交互式的，页面结构、标题、静态文本等仍可作为服务端组件渲染，只把交互部分作为客户端子组件。这需要合理设计组件边界，把"静态壳子"和"动态内核"分离开来。

## 3.4 组件嵌套、复用与Props传参规范

Props是组件间通信的唯一通道（除Context外），在RSC架构下，Props传参有了新的限制和最佳实践。理解这些限制不仅是写出正确代码的前提，也是设计良好组件架构的基础。

### 3.4.1 Props传参的3种模式：直接传值、children、render props

**模式1：直接传值**

最基础的传参方式，父组件通过JSX属性将数据传递给子组件。

```tsx
<UserCard name="张三" age={25} tags={['admin', 'vip']} />
```

适用于数据量小、结构简单的场景。注意：在服务端组件向客户端组件传值时，值必须是可序列化的——不能传递函数、类实例等。

**模式2：children**

children是React中最特殊的prop，它允许你将子组件（或任何React元素）作为内容嵌入到父组件中。children在RSC架构中有特殊意义——它是跨越服务端/客户端边界的"虫洞"。

```tsx
<Layout>
  <Sidebar />
  <MainContent />
</Layout>
```

如前所述，一个客户端组件可以通过children接收服务端组件的渲染结果。这是因为children在服务端组件中已经被渲染成React元素树（纯数据结构），传递的只是这个数据结构，不需要在客户端执行服务端组件的代码。

**模式3：render props**

render props模式通过一个函数prop来实现更灵活的组件组合。父组件将渲染逻辑的控制权交给子组件。

```tsx
<DataProvider render={(data) => <Display data={data} />} />
```

在RSC中，render props模式需要谨慎使用。如果DataProvider是客户端组件，render函数不能在服务端组件中定义并传入——因为函数不可序列化，无法跨RSC边界传递。这种情况下，你需要将render函数移到客户端组件内部定义，或者使用children模式替代。

### 3.4.2 服务端组件向客户端组件传Props的限制

这是RSC架构中最关键的约束之一：从服务端组件向客户端组件传递的Props必须是可序列化的（Serializable）。所谓可序列化，是指该值可以被转换为一种可传输的格式（RSC Payload），然后在客户端被还原。

| 类型 | 可序列化 | 说明 |
|------|----------|------|
| string, number, boolean | 是 | 基本类型，直接传输 |
| null, undefined | 是 | 空值类型 |
| Array, 纯对象 | 是 | 纯数据结构，递归序列化 |
| Date | 是 | RSC Payload特殊支持 |
| Map, Set | 是 | RSC Payload特殊支持 |
| 函数 | 否 | 无法跨边界传递，会报错 |
| Class实例 | 否 | 失去原型链，变成纯对象 |
| Symbol | 否 | 无法序列化 |
| React Element (JSX) | 是 | 作为children传递时特殊处理 |
| Promise | 否 | 不能直接传递（但可以await后传递结果） |

```tsx
// 服务端组件
import ClientChart from './ClientChart';

export default async function Page() {
  const data = await fetchChartData();
  
  // 正确：传递纯数据
  return <ClientChart data={data} />;
  
  // 错误：传递函数（会编译报错或运行时报错）
  // return <ClientChart formatter={(d) => d.name} />;
  
  // 正确：传递配置字符串，客户端组件内部实现格式化
  return <ClientChart data={data} formatKey="name" />;
}
```

这个限制是RSC架构的基石。理解它之后，你就能理解为什么很多在Pages Router中能工作的代码在App Router中会报错——往往是因为跨边界传递了不可序列化的值。

### 3.4.3 不可序列化数据的传递方案

当你需要跨服务端/客户端边界传递不可序列化的数据（如函数、类实例）时，有以下几种方案：

**方案1：序列化配置，客户端重建**

不传递函数本身，而是传递函数的配置参数，在客户端组件内部根据配置创建对应的函数。

```tsx
// 服务端：传递配置
<DateDisplay config={{ locale: 'zh-CN', format: 'long' }} />

// 客户端：根据配置实现逻辑
'use client';
function DateDisplay({ config }) {
  const formatter = new Intl.DateTimeFormat(config.locale, {
    dateStyle: config.format
  });
  return <span>{formatter.format(new Date())}</span>;
}
```

**方案2：通过children传递React元素**

对于需要跨越边界的"渲染逻辑"，将其封装为服务端组件，通过children传入客户端组件。

```tsx
// 服务端组件
<ClientWrapper>
  <ServerComponent />  {/* 在服务端渲染，结果作为children传递 */}
</ClientWrapper>

// 客户端组件
'use client';
function ClientWrapper({ children }) {
  const [visible, setVisible] = useState(false);
  return <div>{visible && children}</div>;
}
```

**方案3：使用Server Actions处理回调**

当客户端组件需要触发服务端逻辑时，使用Server Actions（服务端动作）。Server Actions是一种特殊的函数，在服务端定义但可以在客户端调用。

```tsx
// actions.ts (服务端)
'use server';
import { revalidatePath } from 'next/cache';

export async function saveData(formData: FormData) {
  await db.item.create({ data: { name: formData.get('name') } });
  revalidatePath('/items');
}

// page.tsx (服务端组件)
import ClientForm from './ClientForm';
import { saveData } from './actions';

export default function Page() {
  return <ClientForm action={saveData} />;  // action是Server Action引用
}
```

Server Actions的引用是可以跨RSC边界传递的——RSC Payload中包含对Server Action的特殊引用标记，客户端调用时会发送请求到服务端执行。

### 3.4.4 组件复用策略：组合优于继承

React天然不支持组件继承——虽然技术上可以用class extends，但在实际项目中几乎没有使用场景。组合（Composition）是React的核心哲学，也是社区公认的最佳实践。

三种核心组合模式：

```tsx
// 1. 包裹组件：通过children组合
function Card({ children }) {
  return <div className="card">{children}</div>;
}

// 2. 配置组件：通过props配置行为
function Button({ variant, size, children, ...props }) {
  return (
    <button className={`btn-${variant} btn-${size}`} {...props}>
      {children}
    </button>
  );
}

// 3. 插槽组件：多个命名props作为插槽
function Dialog({ header, body, footer }) {
  return (
    <div className="dialog">
      <header>{header}</header>
      <main>{body}</main>
      <footer>{footer}</footer>
    </div>
  );
}
```

组合优于继承的原因：继承创造的是紧耦合的层级关系——父类的任何修改都可能影响所有子类。组合创造的是松耦合的协作关系——每个组件独立演进，通过props接口通信。当需求变化时，组合模式只需要调整组合方式，而不需要修改组件内部实现。

> 怕浪猫说：继承是"是什么"，组合是"有什么"。React选择了后者，因为前者的耦合度太高，后者的灵活性远胜。

### 3.4.5 大型项目的组件拆分边界与职责划分

一个大型Next.js项目的组件需要清晰的分层和职责划分。以下是怕浪猫在实际项目中总结的四层架构：

```
app/              ← 路由层（文件即路由）
  page.tsx        ← 页面入口，组合各业务模块
  layout.tsx      ← 布局壳子，持久化UI框架
  template.tsx    ← 模板组件，按需重置

components/
  /features       ← 业务组件层（特定业务功能）
    /user
      ProfileCard.tsx
      UserSettings.tsx
    /order
      OrderList.tsx
      OrderDetail.tsx
  /ui             ← 基础UI层（跨业务通用）
    Button.tsx
    Input.tsx
    Modal.tsx
    Table.tsx
  /layouts        ← 布局组件层
    Dashboard.tsx
    Sidebar.tsx

lib/
  /server         ← 服务端逻辑（数据库、API等）
  /client         ← 客户端工具函数
  /shared         ← 共享纯函数和类型定义
```

拆分原则：
- 单一职责：一个组件只做一件事，一个文件只导出一个主组件
- 最小客户端边界：只有需要交互的叶子节点才声明'use client'
- 单向数据流：父组件通过props向下传数据，子组件通过回调向上通知
- 服务端优先：默认所有组件都是服务端组件，只在必要时才转为客户端组件
- 目录即模块：通过目录结构表达模块边界，避免跨业务模块的直接引用

## 3.5 默认组件、模板组件、布局组件详解

Next.js App Router通过约定文件名来识别不同角色的组件。page.tsx、layout.tsx和template.tsx是最核心的三个文件，它们各司其职，共同构成了Next.js的页面渲染体系。

### 3.5.1 page.tsx：路由页面的默认导出组件

每个路由段的page.tsx是该路由的唯一UI入口。它是URL路径对应的最终渲染内容。访问`/dashboard/analytics`时，Next.js会渲染`app/dashboard/analytics/page.tsx`。

```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  return <h1>仪表盘</h1>;
}
```

page.tsx的特点：
- 必须有默认导出（default export），命名导出会被忽略
- 可以是服务端组件（推荐）或客户端组件
- 可以是async函数，直接使用await获取数据
- 可以导出metadata对象或generateMetadata函数用于SEO

```tsx
// 服务端组件 + 异步数据获取
export default async function BlogPostPage({ params }) {
  const post = await getPost(params.slug);
  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  );
}

// 配合metadata导出，设置页面的SEO信息
export const metadata = {
  title: '博客文章',
  description: '文章详情页',
};

// 动态metadata（基于路由参数）
export async function generateMetadata({ params }) {
  const post = await getPost(params.slug);
  return {
    title: post.title,
    description: post.excerpt,
  };
}
```

page.tsx只在路由匹配时渲染——路由导航时旧page会被卸载，新page会被挂载。这意味着page组件的状态不会在路由切换间保留（layout组件的状态会保留，后面会讲）。

### 3.5.2 layout.tsx：持久化布局的嵌套机制

layout.tsx定义的布局组件在路由导航时不会重新渲染——它的状态被保留，只有children部分（即page内容）会更新。这是App Router相比Pages Router最重要的改进之一。

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }) {
  return (
    <div className="dashboard-layout">
      <nav>侧边栏导航</nav>
      <main>{children}</main>
    </div>
  );
}
```

布局的嵌套机制是Next.js路由系统的核心特性。每一层路由目录的layout.tsx会从外到内依次嵌套：

```
URL: /dashboard/analytics

渲染层级：
RootLayout (app/layout.tsx)
  └── DashboardLayout (app/dashboard/layout.tsx)
        └── AnalyticsPage (app/dashboard/analytics/page.tsx)

URL: /dashboard/settings

渲染层级：
RootLayout (app/layout.tsx)        ← 同一个实例，不重新渲染
  └── DashboardLayout (app/dashboard/layout.tsx)  ← 同一个实例，不重新渲染
        └── SettingsPage (app/dashboard/settings/page.tsx)  ← 新的page
```

当用户从`/dashboard/analytics`导航到`/dashboard/settings`时：
- RootLayout：不重新渲染，所有状态保留
- DashboardLayout：不重新渲染，状态保留（如侧边栏折叠状态）
- AnalyticsPage被卸载，SettingsPage被挂载：children部分更新

这意味着DashboardLayout中的状态（如侧边栏折叠状态、当前选中的tab等）会自动保留，不需要你手动处理状态持久化。这在Pages Router中需要借助状态管理库或URL参数才能实现。

### 3.5.3 template.tsx：每次导航都重新渲染的布局

template.tsx和layout.tsx的结构几乎一样，唯一区别是：template.tsx在每次路由导航时都会重新挂载（unmount旧的，mount新的），状态不保留。

```tsx
// app/dashboard/template.tsx
export default function DashboardTemplate({ children }) {
  return (
    <div className="dashboard-template">
      {children}
    </div>
  );
}
```

从实现上看，template.tsx接收children prop，和layout.tsx一模一样。但从运行行为上看，template相当于在每个page外面包了一层每次都会重建的容器。

### 3.5.4 layout vs template：何时用哪个

| 维度 | layout.tsx | template.tsx |
|------|------------|--------------|
| 重新渲染 | 路由切换时不重新挂载 | 每次导航都重新挂载 |
| 状态保留 | 保留（unmount时不触发） | 不保留（每次都是新实例） |
| useEffect | 只在首次挂载时执行 | 每次导航都执行 |
| 适用场景 | 导航栏、侧边栏、全局Footer | 需要重置状态的页面容器 |
| 性能 | 更好（减少重渲染） | 稍差（每次重建DOM节点） |
| 使用频率 | 高（几乎每个项目都有） | 低（特定场景才需要） |

典型场景对比：

```tsx
// layout.tsx - 导航栏状态需要保留
export default function Layout({ children }) {
  return (
    <div>
      <Sidebar />  {/* 折叠状态在路由切换时保留 */}
      {children}
    </div>
  );
}

// template.tsx - 每次进入页面需要重置动画/状态
export default function Template({ children }) {
  return (
    <div className="page-enter-animation">
      {children}
    </div>
  );
}
```

实际开发中，layout.tsx的使用频率远高于template.tsx。大多数场景下你只需要layout。template主要用于以下场景：
- 页面进入动画（每次导航都需要重新触发CSS动画）
- 需要重置子组件状态的容器（如表单页面，每次进入都清空之前的输入）
- A/B测试场景（每次导航重新选择实验组，确保用户看到一致的版本）
- 需要在每次导航时重新执行的埋点或分析逻辑

### 3.5.5 嵌套布局的层级组合与数据传递

布局组件的嵌套是Next.js App Router的核心特性。每一层布局都可以独立获取数据，数据不需要从顶层一路传递。这和Pages Router中需要在页面级getServerSideProps中获取所有数据、然后层层传递的模式完全不同。

```
app/layout.tsx          → <html><body>{children}</body></html>
app/dashboard/layout.tsx → <DashboardShell>{children}</DashboardShell>
app/dashboard/page.tsx   → <DashboardHome />
```

数据获取策略：

```tsx
// app/layout.tsx - 全局数据（如用户信息、全局配置）
export default async function RootLayout({ children }) {
  const user = await getCurrentUser();
  return (
    <html>
      <body>
        <UserProvider user={user}>
          {children}
        </UserProvider>
      </body>
    </html>
  );
}

// app/dashboard/layout.tsx - 仪表盘级数据
export default async function DashboardLayout({ children }) {
  const stats = await getDashboardStats();
  return (
    <div>
      <StatsBar stats={stats} />
      {children}
    </div>
  );
}

// app/dashboard/page.tsx - 页面级数据
export default async function DashboardPage() {
  const recentOrders = await getRecentOrders();
  return <OrderList orders={recentOrders} />;
}
```

注意一个关键区别：layout.tsx的数据获取在路由导航时不会重新执行（因为layout不会重新挂载）。如果你需要每次导航都刷新数据，应该在page.tsx中获取，或者使用router.refresh()强制刷新当前路由的数据。

> 怕浪猫说：layout是"壳"，page是"芯"。壳不动芯动，这是Next.js布局系统的核心设计。理解了这一点，就不会把数据获取放错位置。

## 3.6 组件样式方案：CSS Modules、Tailwind CSS

Next.js支持多种样式方案，但在App Router时代，由于服务端组件的存在，样式方案的选择需要考虑更多因素。服务端组件没有浏览器运行时，这意味着依赖运行时动态生成样式的方案（如传统CSS-in-JS）会受到限制。

### 3.6.1 CSS Modules：局部作用域与命名约定

CSS Modules是Next.js内置支持的样式方案，通过文件名约定（`*.module.css`）自动开启局部作用域。这是最简单、最稳定的样式方案。

```css
/* Button.module.css */
.button {
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.primary {
  background: #0070f3;
  color: white;
}
.primary:hover {
  background: #0061d5;
}
```

```tsx
// Button.tsx
import styles from './Button.module.css';

export default function Button({ variant, children }) {
  return (
    <button className={`${styles.button} ${styles[variant] || ''}`}>
      {children}
    </button>
  );
}
```

编译后，类名会被自动转换为带哈希的唯一名称，如`Button_button__a1b2c`，彻底避免命名冲突。这个转换在编译时完成，没有运行时开销。

CSS Modules的优势：
- 零配置，Next.js开箱即用，不需要安装任何额外依赖
- 服务端组件和客户端组件都完全支持，没有兼容性问题
- 编译时生成唯一类名，零运行时开销
- TypeScript支持良好，配合typescript-plugin-css-modules可获得类型提示和自动补全
- 支持组合（composes）、变量引用等高级CSS特性

CSS Modules也支持全局类名（使用:global语法），适用于需要覆盖第三方库样式的场景。

### 3.6.2 Tailwind CSS在Next.js中的零配置接入

Tailwind CSS是当前最流行的原子化CSS框架，在Next.js中的接入非常简单。从Next.js 15开始，使用Tailwind CSS v4的接入方式更加简洁。

安装和初始化：

```bash
npm install tailwindcss @tailwindcss/postcss
```

```js
// postcss.config.js
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

```css
/* app/globals.css */
@import "tailwindcss";
```

在组件中使用：

```tsx
export default function Card({ children }) {
  return (
    <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      {children}
    </div>
  );
}
```

Tailwind CSS在Next.js中的关键优势是：所有类名都是预生成的，服务端组件可以直接使用，不需要担心运行时样式注入问题。配合Tailwind的JIT（Just-In-Time，即时编译）编译器，最终bundle中只包含实际使用到的类名，未使用的类名会被Tree-shaking（树摇优化）移除。

Tailwind CSS的学习曲线主要在于记忆类名，但掌握了命名规律后开发效率极高。配合Tailwind CSS IntelliSense VS Code插件，可以获得类名自动补全和悬浮预览。

### 3.6.3 样式方案对比：CSS Modules vs Tailwind vs CSS-in-JS

| 维度 | CSS Modules | Tailwind CSS | CSS-in-JS (styled-components等) |
|------|-------------|--------------|-------------------------------|
| 学习成本 | 低 | 中（需记类名） | 低 |
| 服务端组件支持 | 完全支持 | 完全支持 | 部分支持/有限制 |
| 运行时开销 | 无 | 无 | 有（运行时生成样式） |
| 样式复用 | 通过类名组合 | 通过类名和配置 | 通过组件组合 |
| 主题支持 | CSS变量 | 配置文件 | JS对象/Props |
| 包体积影响 | 小 | 小（Tree-shaking） | 较大 |
| 适合场景 | 中小型项目 | 各种规模 | 重交互项目 |
| 开发体验 | 传统CSS写法 | 原子类，HTML中写样式 | JS中写样式，动态灵活 |

在App Router中，传统CSS-in-JS方案（如styled-components、emotion）面临一个根本性问题：它们依赖运行时动态生成样式，需要React的Context来传递样式主题和缓存。而服务端组件没有Context Provider，也没有浏览器运行时。虽然一些库推出了RSC兼容版本（如styled-components的zero-runtime方案），但使用体验和性能都不理想。

> 怕浪猫说：在RSC时代，样式方案的选择不再是纯偏好问题，而是架构约束问题。Tailwind和CSS Modules是当前最安全的选择。如果你从Pages Router迁移过来，这是最需要调整的技术决策之一。

### 3.6.4 服务端组件中的样式限制与解决方案

服务端组件中不能使用CSS-in-JS（运行时方案），因为它们需要React的Context和运行时样式注入。以下是服务端组件中可用的样式方案：

```tsx
// 方案1：CSS Modules（推荐）
import styles from './Card.module.css';
export default function ServerCard() {
  return <div className={styles.card}>内容</div>;
}

// 方案2：Tailwind CSS（推荐）
export default function ServerCard() {
  return <div className="rounded-lg p-6 bg-white">内容</div>;
}

// 方案3：全局CSS（通过layout.tsx导入）
// app/globals.css 中定义 .card { padding: 24px; }
// 在layout.tsx中: import './globals.css';

// 方案4：内联样式（有限使用）
export default function ServerCard() {
  return <div style={{ padding: '24px', background: '#fff' }}>内容</div>;
}
```

内联样式在服务端组件中可以工作，但无法使用伪类（:hover、:focus等）、媒体查询（@media）、动画（@keyframes）等CSS特性，只适合简单场景。另外，内联样式的值不会被浏览器缓存，每次渲染都会重新创建样式对象。

如果需要在服务端组件中使用动态样式（基于props变化的样式），推荐使用CSS变量：

```tsx
// 服务端组件中通过CSS变量传递动态值
export default function ColorBox({ color }: { color: string }) {
  return (
    <div style={{ '--box-color': color } as React.CSSProperties}>
      <p className="text-[var(--box-color)]">动态颜色文本</p>
    </div>
  );
}
```

### 3.6.5 暗色主题（Dark Mode）实现方案

暗色主题在Next.js中有几种实现方式，各有优劣。核心挑战是：服务端不知道用户的主题偏好（存在localStorage中），如果处理不当会导致页面加载时的闪烁（FOUC，Flash of Unstyled Content）。

**方案1：CSS变量 + class切换（推荐）**

通过CSS变量定义主题色彩，在根元素上切换class来切换主题。

```css
/* globals.css */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --border-color: #e5e5e5;
}
.dark {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2a2a2a;
  --text-primary: #ffffff;
  --text-secondary: #aaaaaa;
  --border-color: #3a3a3a;
}
```

```tsx
// ThemeToggle.tsx (客户端组件)
'use client';
import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  
  useEffect(() => {
    const isDark = document.documentElement.classList.contains('dark');
    setDark(isDark);
  }, []);

  const toggle = () => {
    const next = !dark;
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem('theme', next ? 'dark' : 'light');
    setDark(next);
  };

  return <button onClick={toggle}>{dark ? '浅色' : '深色'}</button>;
}
```

**方案2：next-themes库（生产推荐）**

next-themes处理了暗色主题的所有边界情况：SSR闪烁、系统偏好检测、localStorage持久化、跨标签页同步。

```tsx
// app/layout.tsx
import { ThemeProvider } from 'next-themes';

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system">
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

```tsx
// 使用Hook
'use client';
import { useTheme } from 'next-themes';

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      切换
    </button>
  );
}
```

注意`suppressHydrationWarning`属性：由于主题在服务端和客户端可能不一致（服务端不知道用户的系统偏好或localStorage值），这会导致React的水合不匹配警告。这个属性告诉React这个元素的水合不匹配是可以接受的，不需要报错。

暗色主题实现的关键考量：

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| SSR闪烁（FOUC） | 服务端渲染浅色，客户端切换到深色 | 在<script>中提前设置class |
| 系统偏好检测 | 需要在客户端检测prefers-color-scheme | matchMedia API |
| 主题持久化 | 用户选择的偏好需要保存 | localStorage |
| 水合不匹配 | 服务端和客户端渲染的class不一致 | suppressHydrationWarning |
| 服务端组件中使用 | CSS变量在:root定义 | 服务端组件直接用CSS变量 |

## 3.7 本章小结与课后练习

### 本章核心要点

**React基础层面：**
- 函数组件每次渲染都是独立闭包，状态是快照而非可变引用，这是理解Hooks行为的基础
- 核心Hooks（useState、useEffect、useMemo、useCallback）各司其职，不要滥用——每个Hook都有适用场景和性能开销
- 自定义Hooks是逻辑复用的最佳方案，比HOC和render props更优雅
- Hooks两条铁律不可违反：只在顶层调用、只在React函数中调用
- React 18并发特性（useTransition、useDeferredValue）用于优化大块渲染阻塞交互的场景

**Next.js组件架构层面：**
- 服务端组件在服务端运行，可直接访问后端资源，不增加客户端JS体积
- 客户端组件通过'use client'声明，可使用Hooks和浏览器API
- 客户端边界是单向门，但可通过children props实现"虫洞"效果
- Props跨服务端到客户端边界传递必须是可序列化的
- 默认服务端优先，只在必要时才使用客户端组件

**约定文件层面：**
- page.tsx是路由入口，每次导航都会重新挂载
- layout.tsx是持久化布局，路由切换时状态保留
- template.tsx每次导航都重新挂载，用于需要重置状态的场景
- layout的数据获取在导航时不会重新执行，page的会
- 大多数场景用layout，需要重置状态时才用template

**样式层面：**
- CSS Modules和Tailwind CSS是RSC时代的首选方案
- 传统CSS-in-JS在服务端组件中受限
- 暗色主题推荐使用next-themes库处理边界情况
- CSS变量是跨服务端/客户端的样式传递桥梁

### 课后练习

**练习1（基础）：** 创建一个服务端组件ArticleList，直接从数据库获取文章列表并渲染。然后创建一个客户端组件SearchBar，实现前端搜索过滤。将它们组合在同一个页面中，确保SearchBar是唯一的客户端组件。思考：SearchBar如何触发ArticleList的重新过滤？如果数据量很大，前端过滤是否合适？

**练习2（进阶）：** 实现一个useDebounce自定义Hook，然后在一个客户端组件中使用它来防抖搜索请求。思考：为什么这个Hook不能在服务端组件中使用？如果搜索请求需要访问数据库，应该如何架构这个功能？

**练习3（实战）：** 创建一个博客布局，包含：RootLayout（全局导航栏）、BlogLayout（分类侧边栏，状态需保留）、BlogTemplate（文章列表容器，每次进入需要重置滚动位置）。思考每个部分应该用layout还是template，为什么？数据获取应该放在哪一层？

**练习4（思考题）：** 以下代码有什么问题？如何修复？

```tsx
'use client';
import { useState } from 'react';
import { db } from '@/lib/db';

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  
  const loadUsers = async () => {
    const data = await db.user.findMany();
    setUsers(data);
  };
  
  return <button onClick={loadUsers}>加载用户</button>;
}
```

提示：思考'use client'的传染性规则和数据库连接的安全性。这个代码不仅会把数据库连接代码泄露到客户端bundle中，还可能暴露数据库凭证。修复方案应该使用Server Actions或API Routes。

> 怕浪猫说：理论加实践才是真知。把这些练习做完，你对RSC架构的理解会超过80%的Next.js开发者。不要只看答案——先自己动手写，遇到问题再回来对照。

下一篇，我们将深入Next.js的路由系统——从文件约定路由到动态路由、并行路由、拦截路由，App Router的路由能力远比你想象的强大。当你掌握了路由系统，就能构建出真正复杂的Web应用架构。

系列进度 3/16

怕浪猫说：技术学习不是百米冲刺，而是马拉松。节奏比速度重要，理解比记忆重要。今天这一章内容不少，慢慢消化，遇到不懂的地方多看几遍代码示例。下一章见。
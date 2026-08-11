# 第5章 JavaScript 执行的底层细节

> 你写的每一个变量、每一个闭包、每一次 this 指向，在 V8 底层都对应着精确的数据结构和查找路径。理解这些细节，你才能真正理解 JavaScript。

我是怕浪猫，一个喜欢钻底层的技术博主。前两章我们拆了 V8 的执行管道和高级机制，今天进入第 5 章，我们聊 JavaScript 执行的底层细节。作用域链是怎么构建的，闭包在内存里长什么样，this 绑定的底层规则是什么，原型链的查找路径是怎样的。这一章会把这些日常开发中天天用但很少深究的概念彻底讲透。

## 5.1 作用域与作用域链

### 5.1.1 词法作用域在 V8 中的实现

JavaScript 使用词法作用域（Lexical Scope），也叫静态作用域。函数的作用域在定义时就确定了，而不是在调用时确定。这意味着函数能访问哪些变量，取决于它在源代码中的位置。

V8 在解析阶段就构建了作用域信息。Parser 在生成 AST（Abstract Syntax Tree，抽象语法树）时，会同时创建作用域对象，记录每个作用域中定义的变量和嵌套关系。

```
词法作用域示例

// 源代码
let globalVar = 'G';
function outer() {
  let outerVar = 'O';
  function inner() {
    let innerVar = 'I';
    console.log(innerVar, outerVar, globalVar);
  }
  return inner;
}
const fn = outer();
fn();  // 输出: I O G

// V8 中的作用域链
┌─────────────────┐
│ inner 作用域      │  innerVar = 'I'
│   └─ parent ────┐│
└─────────────────┘│
┌─────────────────┐│
│ outer 作用域      │◄┘  outerVar = 'O'
│   └─ parent ────┐│
└─────────────────┘│
┌─────────────────┐│
│ 全局作用域        │◄┘  globalVar = 'G'
└─────────────────┘
```

V8 中的作用域类型：

| 作用域类型 | 说明 | 示例 |
|-----------|------|------|
| GLOBAL_SCOPE | 全局作用域 | 顶层代码 |
| FUNCTION_SCOPE | 函数作用域 | function 内部 |
| BLOCK_SCOPE | 块级作用域 | let/const 在 {} 内 |
| MODULE_SCOPE | 模块作用域 | ES Module 顶层 |
| EVAL_SCOPE | eval 作用域 | eval() 内部 |
| WITH_SCOPE | with 语句作用域 | with(obj) {} |

### 5.1.2 变量查找路径

当 JavaScript 代码访问一个变量时，V8 沿着作用域链逐层查找。这个过程看似简单，但在 V8 底层有精细的优化。

```
变量查找流程

访问变量 outerVar（在 inner 函数中）

1. 在 inner 作用域中查找 → 未找到
2. 沿 parent 指针到 outer 作用域 → 找到！outerVar = 'O'
3. 返回值

访问变量 notExist（不存在的变量）

1. 在 inner 作用域中查找 → 未找到
2. 沿 parent 指针到 outer 作用域 → 未找到
3. 沿 parent 指针到全局作用域 → 未找到
4. 抛出 ReferenceError
```

V8 对变量查找的优化策略：

| 优化策略 | 原理 | 效果 |
|---------|------|------|
| 变量提升 | 在编译期确定变量的位置 | 避免运行时查找 |
| 上下文槽位分配 | 将局部变量分配到固定槽位 | 直接索引访问 |
| 全局变量缓存 | 缓存全局变量的查找结果 | 减少全局对象访问 |

### 5.1.3 var、let、const 的底层差异

var、let、const 在 V8 底层有不同的处理方式。

```
var、let、const 在 V8 中的处理差异

// var 声明
function example() {
  console.log(x);  // undefined（变量提升）
  var x = 1;
}
// V8 行为：在函数作用域创建时，x 被提升并初始化为 undefined

// let 声明
function example() {
  console.log(y);  // ReferenceError（暂时性死区）
  let y = 1;
}
// V8 行为：y 被提升但未初始化，访问会抛错（暂时性死区）

// const 声明
const z = 1;
z = 2;  // TypeError
// V8 行为：z 被提升但未初始化，赋值后不可重新绑定
```

| 特性 | var | let | const |
|------|-----|-----|-------|
| 作用域 | 函数作用域 | 块级作用域 | 块级作用域 |
| 提升 | 提升并初始化为 undefined | 提升但不初始化（TDZ） | 提升但不初始化（TDZ） |
| 重复声明 | 允许 | 禁止 | 禁止 |
| 重新赋值 | 允许 | 允许 | 禁止 |
| V8 存储 | 函数上下文变量 | 块级上下文变量 | 块级上下文变量（只读标记） |

TDZ（Temporal Dead Zone，暂时性死区）是 let 和 const 的关键特性。V8 在编译期就知道变量存在，但不会初始化它，直到代码执行到声明语句。在 TDZ 中访问变量会抛出 ReferenceError。

> var 的变量提升和 let 的暂时性死区，不是语言规范的文字游戏，而是 V8 在编译期和运行期的实际行为差异。理解 TDZ，就理解了「变量为什么声明前不能用」。

## 5.2 闭包（Closure）的内存模型

### 5.2.1 闭包的本质

闭包是 JavaScript 中最常被误解的概念之一。在 V8 底层，闭包的本质很简单：函数对象持有一个对其定义时作用域的引用。

```
闭包的内存结构

function createCounter() {
  let count = 0;
  return function() {
    return ++count;
  };
}
const counter = createCounter();

V8 内存中的结构：

┌─────────────────────┐
│   counter 函数对象    │
│  ┌───────────────┐  │
│  │ Code 指针      │  │  → 指向函数的字节码/机器码
│  │ Scope 指针     │──┼──→ 指向 createCounter 的作用域
│  │ Feedback 指针  │  │  → 指向内联缓存信息
│  └───────────────┘  │
└─────────────────────┘
                     │
                     ▼
┌─────────────────────┐
│  createCounter 作用域 │
│  count = 0           │  ← 这个变量不会被 GC 回收
│                       │    因为 counter 函数对象还在引用它
└─────────────────────┘
```

闭包的关键特征：即使 createCounter 函数已经返回，count 变量仍然存在于内存中，因为返回的函数对象持有对它的引用。这就是闭包能「记住」外部变量的原因。

### 5.2.2 闭包与变量捕获

闭包捕获的是变量本身，而不是变量的值。这意味着闭包内对变量的修改会影响外部。

```
// 闭包捕获变量本身
function makeFunctions() {
  let arr = [];
  for (var i = 0; i < 3; i++) {
    arr.push(() => i);
  }
  return arr;
}
// [f, f, f] = makeFunctions();
// f() → 3, f() → 3, f() → 3
// 因为 var 是函数作用域，三个闭包捕获同一个 i

// let 修复了这个问题
function makeFunctions2() {
  let arr = [];
  for (let i = 0; i < 3; i++) {
    arr.push(() => i);
  }
  return arr;
}
// [f, f, f] = makeFunctions2();
// f() → 0, f() → 1, f() → 2
// 因为 let 是块级作用域，每次迭代创建新的 i
```

V8 对闭包变量捕获的优化：如果 V8 在编译期分析发现闭包只读取变量而不修改，它可能将变量捕获优化为值捕获，避免不必要的引用维护。

### 5.2.3 闭包与内存泄漏

闭包最常见的性能问题是意外地持有不需要的变量，导致内存泄漏。

```
// 闭包导致的内存泄漏
function attachHandler() {
  let hugeData = new Array(1000000).fill('data');  // 大数组
  
  document.getElementById('btn').addEventListener('click', function() {
    console.log('clicked');  // 不需要 hugeData，但闭包持有了它
  });
}

// V8 的优化：如果 hugeData 在闭包中未被引用
// V8 可能通过逃逸分析消除对它的引用
// 但不是所有情况都能优化
```

V8 对闭包变量有一个优化叫「惰性分配」。如果 V8 在编译期分析发现闭包不需要某个变量，它可能不为该变量分配闭包上下文槽位。但这个优化有限，不能依赖。

> 闭包不是魔法，它只是「函数对象持有一个作用域引用」。理解了这一点，闭包的所有行为都能推导出来：为什么闭包能记住变量，为什么闭包会导致内存泄漏，为什么闭包能实现私有变量。

## 5.3 this 绑定的底层机制

### 5.3.1 this 的四种绑定规则

JavaScript 中的 this 是一个特殊的标识符，它的值在函数调用时确定，而不是定义时。V8 根据函数的调用方式决定 this 的值。

```
this 绑定的四种规则

// 规则1：默认绑定（独立调用）
function foo() { console.log(this); }
foo();  // this → globalThis（严格模式下 undefined）

// 规则2：隐式绑定（方法调用）
const obj = { name: 'obj', foo: foo };
obj.foo();  // this → obj

// 规则3：显式绑定（call/apply/bind）
foo.call({ name: 'explicit' });  // this → { name: 'explicit' }

// 规则4：new 绑定（构造函数）
new foo();  // this → 新创建的对象
```

四种规则的优先级：

| 优先级 | 绑定方式 | 说明 |
|--------|---------|------|
| 最高 | new 绑定 | 构造函数中的 this 指向新对象 |
| 高 | 显式绑定 | call/apply/bind 指定的 this |
| 中 | 隐式绑定 | 方法调用时的对象 |
| 低 | 默认绑定 | 独立调用时的全局对象或 undefined |

### 5.3.2 箭头函数的 this

箭头函数没有自己的 this，它继承外层作用域的 this。在 V8 底层，箭头函数不创建新的执行上下文，而是从定义时的词法作用域中获取 this。

```
// 箭头函数的 this
const obj = {
  name: 'obj',
  regular: function() {
    console.log(this.name);  // 'obj'
    const inner = function() {
      console.log(this.name);  // undefined 或全局
    };
    inner();
  },
  arrow: function() {
    console.log(this.name);  // 'obj'
    const inner = () => {
      console.log(this.name);  // 'obj'（继承外层 this）
    };
    inner();
  }
};
```

V8 处理箭头函数 this 的方式：在编译箭头函数时，V8 将 this 作为外部作用域的变量来处理，而不是为箭头函数创建独立的 this 绑定。这意味着箭头函数的 this 查找走的是变量查找路径，而非 this 绑定机制。

### 5.3.3 this 在 V8 中的内部表示

在 V8 中，this 被存储在函数的执行上下文（ExecutionContext）中。每次函数调用时，V8 创建一个新的执行上下文，其中包含 this 的值。

```
V8 执行上下文结构（简化）

┌──────────────────────────┐
│     ExecutionContext      │
│                          │
│  ┌─────────────────────┐ │
│  │ this               │ │  ← 根据调用方式设置
│  ├─────────────────────┤ │
│  │ VariableObject     │ │  ← 变量和函数声明
│  ├─────────────────────┤ │
│  │ ScopeChain         │ │  ← 作用域链
│  └─────────────────────┘ │
└──────────────────────────┘
```

不同调用方式下 V8 设置 this 的方式：

| 调用方式 | V8 设置 this 的方式 | this 值 |
|---------|-------------------|---------|
| 独立调用 | 设为全局对象或 undefined | globalThis / undefined |
| 方法调用 | 设为接收者对象 | 调用方法的对象 |
| call/apply | 设为传入的对象 | 传入的第一个参数 |
| bind | 预设 this 并返回新函数 | bind 绑定的对象 |
| new | 创建新对象并设为 this | 新创建的对象 |
| 箭头函数 | 从词法作用域继承 | 外层的 this |

## 5.4 原型链（Prototype Chain）在 V8 中的实现

### 5.4.1 原型与原型链的结构

JavaScript 的对象系统基于原型（Prototype）。每个对象都有一个内部属性 [[Prototype]]（在代码中通过 __proto__ 或 Object.getPrototypeOf() 访问），指向它的原型对象。原型对象本身也有原型，形成原型链。

```
原型链示例

const animal = { breathe: true };
const dog = Object.create(animal);
dog.bark = true;
const myDog = Object.create(dog);
myDog.name = 'Rex';

// 原型链
myDog ──→ dog ──→ animal ──→ Object.prototype ──→ null

属性查找：
  myDog.name    → 'Rex'     （在 myDog 自身找到）
  myDog.bark    → true      （在 dog 上找到）
  myDog.breathe → true      （在 animal 上找到）
  myDog.toString → function  （在 Object.prototype 上找到）
```

在 V8 中，每个对象都有一个隐藏的内部字段（称为 [[Prototype]] 或 __proto__），指向其原型对象。属性查找时，如果对象自身没有该属性，V8 会沿着原型链向上查找，直到找到属性或到达原型链末尾（null）。

### 5.4.2 V8 对原型链查找的优化

原型链查找的本质是多次属性访问，理论上比直接属性访问慢。V8 对原型链查找做了专门的优化。

**内联缓存优化原型链查找**：V8 的内联缓存不仅缓存属性在对象中的位置，还缓存整个原型链的形状。如果原型链形状不变，后续查找可以直接命中缓存。

```
内联缓存优化原型链查找

第一次查找 myDog.breathe：
  1. 检查 myDog 自身 → 没有
  2. 检查 myDog.__proto__（dog） → 没有
  3. 检查 dog.__proto__（animal） → 找到！
  4. 缓存：(原型链形状, breathe → animal 对象)

第二次查找 myDog.breathe：
  1. 检查原型链形状是否变化 → 没变
  2. 直接返回缓存的 animal.breathe
  (跳过逐级查找)
```

**原型链形状验证**：V8 为每条原型链维护一个「有效性检查」标记。如果原型链上没有任何对象被修改（添加/删除属性或改变原型），V8 可以直接使用缓存的结果。一旦原型链被修改，V8 会失效所有相关缓存。

原型链查找的性能特征：

| 查找场景 | 性能 | 原因 |
|---------|------|------|
| 自身属性 | 最快 | 直接访问 |
| 近层原型属性 | 快 | 原型链短 |
| 深层原型属性 | 较慢 | 原型链长，逐级查找 |
| 缓存命中的原型属性 | 快 | IC 命中 |
| 缓存失效的原型属性 | 慢 | 需要重新查找 |

### 5.4.3 原型链修改的性能影响

修改原型链是 V8 最不喜欢的操作之一，因为它会失效大量优化缓存。

```
// 严重性能问题：修改原型链
function Animal() {}
Animal.prototype.eat = function() {};

// 修改原型链（不推荐）
const dog = new Animal();
dog.__proto__ = { bark: function() {} };
// → 所有原型链相关的 IC 失效
// → 相关函数可能触发反优化
```

V8 对原型链修改的处理：

| 操作 | V8 处理 | 性能影响 |
|------|--------|---------|
| 添加原型属性 | 可能触发隐藏类变化 | 中等 |
| 删除原型属性 | 破坏隐藏类 | 严重 |
| 修改 __proto__ | 整条原型链 IC 失效 | 严重 |
| Object.setPrototypeOf | 同修改 __proto__ | 严重 |

> 原型链修改是 V8 优化的天敌。一次原型链修改，可能让数万个对象的内联缓存全部失效。在性能敏感的代码中，绝对不要在运行时修改原型链。

## 5.5 执行上下文与变量环境

### 5.5.1 执行上下文的创建

每当代码在 V8 中执行时，都会创建一个执行上下文（Execution Context）。执行上下文包含三个核心组件：变量环境（Variable Environment）、词法环境（Lexical Environment）和 this 绑定。

```
执行上下文的创建过程

1. 创建变量环境（Variable Environment）
   - 收集 var 声明的变量（初始化为 undefined）
   - 收集函数声明（函数提升）
   
2. 创建词法环境（Lexical Environment）
   - 收集 let/const 声明（不初始化，TDZ）
   
3. 确定 this 的值
   - 根据调用方式设置
   
4. 设置作用域链
   - 当前环境 → 外层环境 → ... → 全局环境
```

变量环境和词法环境的分离是为了处理 var 和 let/const 的不同行为。var 声明的变量放在变量环境中，let/const 声明的变量放在词法环境中。两者组成了完整的作用域链。

### 5.5.2 变量环境与词法环境的区别

| 维度 | 变量环境 | 词法环境 |
|------|---------|---------|
| 存储内容 | var 声明、函数声明 | let/const 声明 |
| 提升 | 初始化为 undefined | 不初始化（TDZ） |
| 重新绑定 | 允许 | 禁止 |
| 用途 | 兼容旧代码 | 现代 JS 模式 |

这个分离设计是 ES6 为了兼容 var 的旧行为而做的折中。在 V8 实现中，变量环境和词法环境都是环境记录（Environment Record）的实例，但有不同的初始化策略。

### 5.5.3 作用域链的运行时构建

作用域链在 V8 中的构建分为编译期和运行期两个阶段。编译期，Parser 在生成 AST 时为每个作用域创建 ScopeInfo 对象，记录该作用域中的变量名和位置。运行期，V8 在创建执行上下文时，根据 ScopeInfo 构建实际的 Environment 对象，并设置 parent 指针形成作用域链。

这个两阶段设计的好处是：编译期已经确定了所有变量位置，运行期只需要做简单的指针赋值，不需要做字符串匹配来查找变量。这也是为什么词法作用域的变量查找在 V8 中是 O(1) 操作（通过槽位索引直接访问），而非 O(N) 遍历。

对于闭包场景，V8 会在函数对象中存储一个 Context 指针，指向函数定义时的词法环境。当函数被调用时，这个 Context 成为新执行上下文的父级环境。闭包变量的查找就是通过这个指针链逐级访问固定槽位，效率与普通变量查找基本一致。

## 本章核心知识总结

| 知识模块 | V8 底层机制 | 实际影响 |
|---------|------------|---------|
| 作用域链 | 词法作用域在编译期确定 | 闭包能访问外部变量 |
| 闭包 | 函数对象持有作用域引用 | 变量不被 GC 回收 |
| this 绑定 | 执行上下文中的 this 字段 | this 值取决于调用方式 |
| 原型链 | [[Prototype]] 内部属性 | 属性查找逐级向上 |
| 执行上下文 | 变量环境 + 词法环境 | var 和 let 行为不同 |

觉得有用？收藏起来，下次遇到作用域、闭包、this、原型链的问题时直接翻出来看。

你在面试中被问过闭包或 this 的问题吗？有没有被难住的经历？评论区说说。

关注怕浪猫，下期我们正式进入渲染世界，讲从 HTML 到像素的完整渲染管线。系列进度 5/24。

下期预告：第 6 章「从 HTML 到像素：渲染管线总览」。我们会完整拆解浏览器的渲染管线（Rendering Pipeline）：HTML 解析构建 DOM、CSS 解析构建 CSSOM、布局计算、绘制、合成，每一步都怎么工作，以及关键渲染路径（Critical Rendering Path）对性能的影响。怕浪猫下期见。

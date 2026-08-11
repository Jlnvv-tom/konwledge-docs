---
sidebar_position: 1
---

# 第一章：编程核心词汇

> 写代码这件事，说白了就是用英语跟机器聊天。你敲下的每一个关键字、给变量起的每一个名字、读报错信息时的每一个单词，都藏着一套约定俗成的"行业黑话"。这一章，我们把编程中最核心的词汇一网打尽——从数据类型到网络协议，从控制流到操作系统底层。搞懂这些词，你读代码、写文档、搜 Stack Overflow 的效率至少翻一倍。

---

## 1.1 数据类型与变量命名词汇

编程世界里，数据是原料，类型是模具，变量是装原料的盒子。搞清楚这些词的含义，是你和编译器和谐相处的第一步。每次你声明一个变量，其实都在跟类型系统做一次约定："这个盒子里装的是整数还是文本？装进去之后还能不能改？"

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `integer` (int) | 整数 | 没有小数点的数字，如 42、-7 |
| `float` / `double` | 浮点数 | 带小数点的数字，`double` 精度更高 |
| `boolean` (bool) | 布尔值 | 只有 `true` 或 `false` 两个值 |
| `string` (str) | 字符串 | 一串字符组成的文本，如 `"hello"` |
| `char` | 字符 | 单个字母或符号，如 `'a'` |
| `null` | 空值 | 表示"什么都没有"的值 |
| `undefined` | 未定义 | 变量声明了但还没赋值（JS 特有） |
| `void` | 无返回值 | 函数不返回任何东西时的类型标记 |
| `const` | 常量 | 赋值后不可修改的变量 |
| `var` / `let` | 变量 | 可修改的变量声明（不同语言语义不同） |
| `mutable` / `immutable` | 可变 / 不可变 | 创建后能否修改 |
| `static` | 静态 | 属于类而非实例，或编译期确定 |
| `typedef` / `type` | 类型别名 | 给已有类型起个短名字 |

### 代码中的真实用例

**变量命名的黄金法则：见名知意。** 看看这段代码：

```python
# ❌ 烂命名——只有你自己（而且只在今天）看得懂
a = 3.14
b = 2
c = a * b * b

# ✅ 好命名——三个月后回来也能秒懂
pi = 3.14
radius = 2
area = pi * radius * radius
```

好的变量名就是最好的注释。当你发现需要写注释解释一个变量是什么的时候，往往说明变量名起得不够好。

在 TypeScript 中，类型注解是日常操作：

```typescript
let userName: string = "Alice";
let age: number = 30;
let isActive: boolean = true;
const MAX_RETRY_COUNT: number = 3;
```

注意 `const` 用于常量时，社区惯例是全大写加下划线（`MAX_RETRY_COUNT`），而普通变量用 camelCase（`userName`）。这不是语法要求，而是约定俗成的代码规范——当你看到全大写的变量名，立刻就知道它是一个不应该被修改的常量。

### 常见误用与混淆

**`null` vs `undefined` vs `nil` vs `None`**

这是跨语言最容易踩坑的一组词。不同语言用不同的词表示"空"，而且它们的语义还有微妙的差别：

- **`null`**：Java、C#、JavaScript、SQL 中表示"空引用"，是一个被显式赋予的值。表示"我故意把它设为空"
- **`undefined`**：JavaScript 专属，表示变量声明了但没赋值，或属性不存在。表示"系统觉得这里应该有值但还没有"
- **`nil`**：Ruby、Go、Objective-C 中的"空"
- **`None`**：Python 的"空"
- **`NULL`**：SQL 中表示缺失值，不区分大小写

```javascript
let a;           // a === undefined（系统自动赋的）
let b = null;    // b === null（你手动赋的）
typeof null;     // "object" —— 这是 JS 的历史遗留 bug
typeof undefined; // "undefined"
```

在 Java 中，`null` 可以赋给任何引用类型，但不能赋给基本类型（如 `int`）。Kotlin 进一步区分了 `nullable`（`String?`）和 `non-null`（`String`），在编译期就帮你挡住空指针异常。

**`let` vs `var`（JavaScript）**

`var` 是老式声明，有变量提升（hoisting）和函数作用域；`let` 是 ES6 引入的，有块级作用域。现代 JS 几乎不用 `var` 了：

```javascript
// var 的坑：变量提升
console.log(x); // undefined（不报错，但容易出 bug）
var x = 5;

// let 就老实多了
console.log(y); // ReferenceError: Cannot access 'y' before initialization
let y = 5;
```

**`float` vs `double`**

`float` 是 32 位浮点数（约 7 位有效数字），`double` 是 64 位（约 15 位有效数字）。在需要精度的场景（如金融计算），两个都不能用——得用 `BigDecimal`（Java）或 `decimal`（Python）：

```python
# ❌ 浮点数精度问题
0.1 + 0.2 == 0.3  # False！实际结果是 0.30000000000000004

# ✅ 用 decimal 解决
from decimal import Decimal
Decimal('0.1') + Decimal('0.2') == Decimal('0.3')  # True
```

**`mutable` vs `immutable`**

这在面试中常考。Python 中 `list` 是 mutable 的，`tuple` 是 immutable 的：

```python
my_list = [1, 2, 3]
my_list.append(4)  # ✅ 没问题

my_tuple = (1, 2, 3)
my_tuple.append(4)  # ❌ AttributeError: 'tuple' object has no attribute 'append'
```

immutable 的好处是线程安全和可哈希——可以用作 dict 的 key。这也是为什么 Python 的 `set` 不能放 `list`，但可以放 `tuple`。

---

## 1.2 控制流与逻辑词汇（if/else/switch/loop）

控制流是程序的"方向盘"。没有控制流，代码只能从上到下跑直线，跟计算器没区别。掌握这些词，你才能让程序"会思考"——根据条件走不同的路，根据需要重复执行某些操作。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `if` / `else` / `else if` (elif) | 如果 / 否则 / 否则如果 | 条件判断的三件套 |
| `switch` / `case` | 开关 / 分支 | 多路分支选择 |
| `default` | 默认 | switch 中没有匹配时的兜底分支 |
| `break` | 跳出 | 立即退出当前循环或 switch |
| `continue` | 继续 | 跳过本次循环剩余部分，进入下一轮 |
| `for` | 循环 | 已知次数的循环 |
| `while` | 当...时 | 条件为真就继续循环 |
| `do...while` | 做...直到 | 先执行一次再判断条件 |
| `return` | 返回 | 从函数中返回一个值 |
| `yield` | 产出 | 暂停函数并返回一个值（可恢复） |
| `condition` | 条件 | 判断语句中的表达式 |
| `statement` | 语句 | 一条可执行的代码 |
| `expression` | 表达式 | 有返回值的代码片段 |
| `ternary` | 三元 | `? :` 三目运算符 |

### 代码中的真实用例

**if-else 链 vs switch**

什么时候用 if-else，什么时候用 switch？经验法则是：判断范围用 if-else，匹配具体值用 switch。

```java
// if-else 链——适合范围判断
if (score >= 90) {
    grade = "A";
} else if (score >= 80) {
    grade = "B";
} else {
    grade = "F";
}

// switch——适合精确值匹配
switch (dayOfWeek) {
    case 1: System.out.println("Monday"); break;
    case 2: System.out.println("Tuesday"); break;
    default: System.out.println("Weekend");
}
```

注意 switch 必须配 `break` 使用（除非你刻意想要 fall-through），否则会"穿透"到下一个 case。Java 14+ 和 JavaScript 的 switch expression 更简洁，不需要 break。

**`break` vs `continue`**

这俩在面试中经常被问区别，其实一句话就能说清：`break` 是"我不干了"（退出整个循环），`continue` 是"这个我跳过"（只跳过当前这一轮）：

```python
# break：完全退出循环
for i in range(5):
    if i == 3:
        break  # 循环结束，不打印 3 和 4
    print(i)  # 输出: 0 1 2

# continue：只跳过当前这一轮
for i in range(5):
    if i == 3:
        continue  # 跳过 3，继续下一轮
    print(i)  # 输出: 0 1 2 4
```

**三元运算符（ternary operator）**

简单条件判断可以用三元运算符一行搞定，省得写五行的 if-else：

```javascript
// 冗长的 if-else
let message;
if (isLogin) {
    message = "Welcome back!";
} else {
    message = "Please log in.";
}

// 用 ternary 一行搞定
let message = isLogin ? "Welcome back!" : "Please log in.";
```

但别嵌套太多层，否则可读性会断崖式下降。超过两层就该老老实实写 if-else。

### 常见误用与混淆

**`statement` vs `expression`**

这两个词在文档里到处都是，但很多人分不清：

- **expression（表达式）**：有返回值。`1 + 2` 是表达式，`x > 0` 是表达式，函数调用也是表达式
- **statement（语句）**：执行一个动作，没有返回值。`if (...)` 是语句，`for (...)` 是语句

在 Python 3.8+ 中，赋值表达式 `:=`（海象运算符）模糊了这个边界：

```python
# 传统写法：需要先赋值再判断
line = input()
while line != "quit":
    process(line)
    line = input()

# 用海象运算符——expression 里也能赋值
while (line := input()) != "quit":
    process(line)
```

**`while` vs `do...while`**

`while` 是先判断后执行，可能一次都不跑；`do...while` 是先执行后判断，至少跑一次。这个"至少跑一次"的特性在某些场景下很有用，比如菜单选择——至少要显示一次菜单让用户选：

```java
int choice;
do {
    choice = showMenu();
} while (choice != 0);  // 用户选 0 才退出
```

**`yield` 不是 `return`**

`return` 会终止函数，`yield` 只是"暂停"函数，下次调用时从暂停处继续。这在 Python 生成器中很常见，也是处理大数据流的关键技术：

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a      # 暂停并返回 a
        a, b = b, a + b  # 下次调用时从这里继续

gen = fibonacci()
print(next(gen))  # 0
print(next(gen))  # 1
print(next(gen))  # 1
print(next(gen))  # 2
```

用 `yield` 的好处是惰性求值——不需要一次性生成所有数据，用多少生成多少，内存友好。

---

## 1.3 函数与方法相关词汇

函数是代码复用的基本单位。你写的每一行代码，几乎都住在某个函数里。搞懂函数相关的词汇，等于拿到了编程世界的"语法手册"——从参数传递到异步编程，从闭包到高阶函数，这些概念贯穿所有编程语言。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `function` (func) | 函数 | 一段可复用的代码块 |
| `method` | 方法 | 属于类或对象的函数 |
| `parameter` (param) | 参数 | 函数定义中声明的变量 |
| `argument` (arg) | 实参 | 调用函数时传入的具体值 |
| `return value` | 返回值 | 函数执行完后给出的结果 |
| `void` | 无返回值 | 函数不返回任何东西 |
| `callback` | 回调函数 | 作为参数传给另一个函数的函数 |
| `recursion` | 递归 | 函数调用自身 |
| `lambda` / `arrow function` | 匿名函数 | 没有名字的简短函数 |
| `overload` | 重载 | 同名函数，参数不同 |
| `override` | 重写 | 子类重新实现父类的方法 |
| `async` / `await` | 异步 / 等待 | 异步编程的关键字 |
| `promise` / `future` | 承诺 / 未来 | 尚未完成的异步操作的结果 |
| `pure function` | 纯函数 | 相同输入永远产生相同输出 |
| `side effect` | 副作用 | 函数修改了外部状态 |
| `higher-order function` | 高阶函数 | 接受函数作为参数或返回函数 |
| `closure` | 闭包 | 函数捕获了外部作用域的变量 |

### 代码中的真实用例

**parameter vs argument——最经典的混淆**

这个区分在技术文档和面试中经常出现，搞混了会很尴尬：

```javascript
// parameter：函数定义时的变量名
function greet(name) {  // ← name 是 parameter（形参）
    console.log("Hello, " + name);
}

// argument：调用时传入的具体值
greet("Alice");  // ← "Alice" 是 argument（实参）
```

记忆技巧：**P**arameter 是 **P**laceholder（占位符），**A**rgument 是 **A**ctual value（实际值）。或者换个角度：parameter 在函数定义时确定，argument 在函数调用时确定。

**高阶函数（higher-order function）**

高阶函数是函数式编程的核心概念。简单说，如果一个函数接受另一个函数作为参数，或者返回一个函数，那它就是高阶函数。JavaScript 的 `map`、`filter`、`reduce` 就是经典的高阶函数：

```javascript
const numbers = [1, 2, 3, 4, 5];

const doubled = numbers.map(n => n * 2);        // [2, 4, 6, 8, 10]
const evens = numbers.filter(n => n % 2 === 0); // [2, 4]
const sum = numbers.reduce((acc, n) => acc + n, 0); // 15
```

这里传给 `map` 的 `n => n * 2` 就是一个 callback（回调函数）。`map` 接受这个 callback 作为参数，所以 `map` 是高阶函数。

**闭包（closure）**

闭包是函数和其词法环境的组合。简单说，内部函数可以访问外部函数的变量，即使外部函数已经返回了：

```javascript
function makeCounter() {
    let count = 0;  // 这个变量被闭包"捕获"了
    return function() {
        count++;
        return count;
    };
}

const counter = makeCounter();
counter(); // 1
counter(); // 2
counter(); // 3
// count 变量外部无法直接访问，但内部函数能一直访问它
```

闭包的实际用途很多：数据私有化、函数工厂、实现模块模式等。但要注意避免一个常见陷阱——在循环中创建闭包：

```javascript
// ❌ 经典陷阱：所有函数都输出 5
for (var i = 0; i < 5; i++) {
    setTimeout(() => console.log(i), 100);  // 5 5 5 5 5
}

// ✅ 用 let 解决
for (let i = 0; i < 5; i++) {
    setTimeout(() => console.log(i), 100);  // 0 1 2 3 4
}
```

### 常见误用与混淆

**`overload` vs `override`**

这俩长得像，意思完全不同，是面试中的高频考点：

- **overload（重载）**：同一个类中，方法名相同但参数列表不同。是编译时多态
- **override（重写）**：子类重新实现父类的同名方法。是运行时多态

```java
// overload：同类中，同名不同参
class Calculator {
    int add(int a, int b) { return a + b; }
    double add(double a, double b) { return a + b; }
    int add(int a, int b, int c) { return a + b + c; }
}

// override：子类改写父类方法
class Animal {
    void speak() { System.out.println("..."); }
}
class Dog extends Animal {
    @Override
    void speak() { System.out.println("Woof!"); }
}
```

注意 Python 不支持 overload（后定义的方法会覆盖先定义的），要实现类似效果得用 `functools.singledispatch`。

**纯函数（pure function）vs 有副作用的函数**

```javascript
// 纯函数：同样的输入永远得到同样的输出，不碰外部状态
function add(a, b) { return a + b; }

// 有副作用的函数：修改了外部变量
let total = 0;
function addToTotal(n) {
    total += n;  // 副作用：修改了外部变量
    return total;
}
```

纯函数的好处：容易测试、容易缓存（memoization）、线程安全。React 的函数组件和 Redux 的 reducer 都要求是纯函数。

**`async/await` 不是多线程**

`async/await` 是异步编程的语法糖，底层是事件循环（Event Loop），不一定涉及多线程。在 Python 中，`asyncio` 是单线程并发——一个线程内多个任务交替执行，不是多核并行：

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)  # 模拟异步IO，这里"让出"CPU
    return "data"

async def main():
    # 并发执行3个任务，约1秒完成（不是3秒）
    results = await asyncio.gather(
        fetch_data(), fetch_data(), fetch_data()
    )
    print(results)
```

---

## 1.4 面向对象编程词汇（class/object/inheritance/polymorphism）

面向对象编程（OOP）是编程世界的"四大发明"之一。不管你用 Java、Python 还是 C++，OOP 的概念都是通用的。掌握这套词汇，你才能看懂任何 OOP 代码，理解设计模式，读懂框架源码。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `class` | 类 | 对象的蓝图/模板 |
| `object` / `instance` | 对象 / 实例 | 类的具体化 |
| `attribute` / `field` / `property` | 属性 / 字段 | 对象存储的数据 |
| `method` | 方法 | 对象能执行的动作 |
| `constructor` | 构造函数 | 创建对象时自动调用的初始化方法 |
| `inheritance` | 继承 | 子类获得父类的属性和方法 |
| `polymorphism` | 多态 | 同一接口，不同实现 |
| `encapsulation` | 封装 | 隐藏内部细节，只暴露接口 |
| `abstraction` | 抽象 | 提取核心特征，忽略非必要细节 |
| `interface` | 接口 | 纯定义方法签名，不含实现 |
| `abstract class` | 抽象类 | 不能被实例化，只能被继承 |
| `extends` / `implements` | 继承 / 实现 | 类继承父类 / 类实现接口 |
| `super` / `parent` | 父类引用 | 访问父类的方法或属性 |
| `this` / `self` | 当前实例引用 | 指向对象自身 |
| `static` | 静态 | 属于类而非实例 |
| `final` / `sealed` | 不可继承 | 禁止被继承或重写 |
| `access modifier` | 访问修饰符 | `public`/`private`/`protected` |
| `composition` | 组合 | "有一个"关系 |

### 代码中的真实用例

**OOP 四大特性**

OOP 的四大支柱是封装、抽象、继承、多态。记住这个缩写：**PIE + E**（Polymorphism, Inheritance, Encapsulation + Abstraction）。

```python
class Animal:
    species_count = 0  # 类属性（static）

    def __init__(self, name, sound):  # 构造函数
        self.name = name       # 实例属性
        self.sound = sound
        Animal.species_count += 1

    def speak(self):  # 实例方法
        return f"{self.name} says {self.sound}"

    def __str__(self):  # 魔术方法（dunder method）
        return f"Animal({self.name})"

dog = Animal("Rex", "Woof")
print(dog.speak())          # Rex says Woof
print(Animal.species_count) # 1
```

**继承与多态**

多态是 OOP 中最美的特性之一——同一个方法调用，不同的对象表现出不同的行为：

```java
abstract class Shape {
    abstract double area();  // 抽象方法，子类必须实现
}

class Circle extends Shape {
    private double radius;
    Circle(double r) { radius = r; }
    @Override double area() { return Math.PI * radius * radius; }
}

class Rectangle extends Shape {
    private double width, height;
    Rectangle(double w, double h) { width = w; height = h; }
    @Override double area() { return width * height; }
}

// 多态：同一个 area() 调用，不同行为
Shape s1 = new Circle(5);
Shape s2 = new Rectangle(3, 4);
System.out.println(s1.area());  // 78.54...
System.out.println(s2.area());  // 12.0
```

**接口（interface）vs 抽象类（abstract class）**

```typescript
// 接口：只定义"能做什么"，不含实现
interface Flyable {
    fly(): void;
}

// 抽象类：可以包含部分实现
abstract class Bird {
    abstract makeSound(): void;  // 子类必须实现
    breathe() { console.log("Breathing..."); }  // 已实现
}

// 一个类可以实现多个接口，但只能继承一个类
class Eagle extends Bird implements Flyable {
    makeSound() { console.log("Screech!"); }
    fly() { console.log("Soaring high!"); }
}
```

选择原则：用接口定义"能力"（能飞、能游泳），用抽象类共享"代码"（呼吸、移动）。

### 常见误用与混淆

**继承（inheritance）vs 组合（composition）**

"is-a" 用继承，"has-a" 用组合。这是 OOP 设计的核心原则之一：

```java
// ❌ 滥用继承：Car "是一个" Engine？语义不对
class Engine {}
class Car extends Engine {}  // 错误

// ✅ 使用组合：Car "有一个" Engine
class Car {
    private Engine engine;  // 组合
    void start() { engine.start(); }
}
```

设计原则：**favor composition over inheritance**（优先使用组合而非继承）。继承是强耦合——父类一改，所有子类受影响。组合更灵活——可以运行时替换组件。

**`this` vs `self`**

不同语言中指向当前实例的关键字不同：

- Java、C++、JavaScript、C#：`this`
- Python：`self`（且必须是方法的第一个参数）
- Ruby：`self`
- Go：没有显式的 this/self，用接收者参数代替

**`public` vs `private` vs `protected`**

| 修饰符 | 类内部 | 同包/同模块 | 子类 | 外部 |
|--------|--------|------------|------|------|
| `public` | ✅ | ✅ | ✅ | ✅ |
| `protected` | ✅ | ✅ | ✅ | ❌ |
| `private` | ✅ | ❌ | ❌ | ❌ |

Python 没有真正的 `private`，靠约定：`_name` 表示"别碰我"（protected），`__name` 表示"别碰我，我会 name mangling"（伪 private）。这是 Python "we are all consenting adults" 哲学的体现。

---

## 1.5 数据结构与算法词汇（array/queue/tree/graph/traversal）

数据结构是程序的骨架，算法是程序的灵魂。面试考它们，工作中也离不开它们——从选择合适的容器到分析时间复杂度，从实现一个缓存到优化数据库查询，背后都是数据结构与算法的知识。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `array` | 数组 | 连续内存中相同类型的元素序列 |
| `list` | 列表 | 有序可变的元素集合 |
| `tuple` | 元组 | 有序不可变的元素序列 |
| `linked list` | 链表 | 通过指针串联的节点序列 |
| `stack` | 栈 | 后进先出（LIFO） |
| `queue` | 队列 | 先进先出（FIFO） |
| `deque` | 双端队列 | 两端都能进出的队列 |
| `hash map` / `dict` | 哈希表 / 字典 | 键值对存储，O(1) 查找 |
| `set` | 集合 | 不重复元素的集合 |
| `tree` | 树 | 层级结构，有根节点和子节点 |
| `binary tree` | 二叉树 | 每个节点最多两个子节点 |
| `BST` (Binary Search Tree) | 二叉搜索树 | 左小右大 |
| `heap` | 堆 | 完全二叉树，根最大或最小 |
| `graph` | 图 | 顶点和边组成的结构 |
| `vertex` / `node` | 顶点 / 节点 | 图或树中的元素 |
| `edge` | 边 | 连接两个顶点的线 |
| `traversal` | 遍历 | 访问数据结构中的每个元素 |
| `BFS` (Breadth-First Search) | 广度优先搜索 | 一层一层地遍历 |
| `DFS` (Depth-First Search) | 深度优先搜索 | 一条路走到黑再回头 |
| `sort` | 排序 | 按顺序重新排列 |
| `search` | 查找 | 在数据中找到目标 |
| `complexity` | 复杂度 | 算法消耗（大O表示法） |

### 代码中的真实用例

**栈和队列——最朴素但最常用的结构**

```python
from collections import deque

# 栈（LIFO）：括号匹配、撤销操作、函数调用栈
stack = []
stack.append("a")
stack.append("b")
stack.append("c")
stack.pop()  # "c" —— 最后放进去的先出来

# 队列（FIFO）：任务调度、消息处理、BFS
queue = deque()
queue.append("task1")
queue.append("task2")
queue.popleft()  # "task1" —— 最先放进去的先出来

# deque 两端都能操作
dq = deque([1, 2, 3])
dq.appendleft(0)    # deque([0, 1, 2, 3])
dq.pop()            # 3
dq.popleft()        # 0
```

**哈希表——查找之王**

```python
# Python dict 底层就是 hash table
user = {"name": "Alice", "age": 30}
if "name" in user:      # O(1) 查找
    print(user["name"]) # Alice

# set 也是基于 hash table，用于去重
tags = set(["python", "java", "python"])
print(tags)  # {"python", "java"} —— 自动去重
```

**树的遍历（traversal）**

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# DFS：深度优先——用递归（也可以用栈）
def inorder(node):  # 中序遍历：左→根→右
    if node:
        inorder(node.left)
        print(node.val)
        inorder(node.right)

# BFS：广度优先——用队列
def level_order(root):
    if not root: return
    q = deque([root])
    while q:
        node = q.popleft()
        print(node.val)
        if node.left: q.append(node.left)
        if node.right: q.append(node.right)
```

记忆技巧：**BFS 用队列，DFS 用栈（或递归）**。BFS 适合找最短路径，DFS 适合找所有路径。

### 常见误用与混淆

**`stack` vs `heap`——双重含义**

这个词有两个完全不同的含义，初学者经常搞混：

- **数据结构的 stack**：后进先出（LIFO）的数据结构
- **内存区域的 stack**：程序运行时存储局部变量和函数调用帧的内存区域，自动分配和释放
- **数据结构的 heap**：一种完全二叉树（大顶堆/小顶堆）
- **内存区域的 heap**：程序运行时动态分配内存的区域（`malloc`/`new`），需要手动或 GC 释放

面试官问"stack 和 heap 的区别"时，通常问的是内存模型，不是数据结构。

**`list` 在不同语言中含义不同**

这是一个跨语言的"同名不同义"陷阱：

- **Python `list`**：动态数组，可变，最常用的容器
- **Java `List`**：接口，`ArrayList`（动态数组）和 `LinkedList`（双向链表）是两种实现
- **C++ `std::list`**：双向链表（不是数组！）
- **JavaScript `Array`**：本质是动态数组，不叫 list

所以当你从 Python 切到 C++ 时，别以为 `std::list` 跟 Python `list` 是一回事。

**`array` vs `linked list` 的选择**

| 操作 | array | linked list |
|------|-------|-------------|
| 随机访问 | O(1) ✅ | O(n) ❌ |
| 头部插入 | O(n) ❌ | O(1) ✅ |
| 尾部插入 | 均摊 O(1) | O(1) |
| 中间插入 | O(n) | O(1)（已知位置） |
| 内存占用 | 紧凑 | 额外存指针 |

记住：需要频繁随机访问用数组，需要频繁插入删除用链表。但实际工程中，数组（动态数组）的性能往往更好，因为 CPU 缓存友好（连续内存）。

---

## 1.6 数据库与 SQL 词汇

不管你做前端还是后端，数据库都是绕不过去的坎。从 SQL 查询到 ORM 框架，从表设计到性能优化，这些词汇是跟数据库打交道的必备工具。学会它们，你就能看懂数据库执行计划，写出高效的查询语句。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `database` (DB) | 数据库 | 有组织地存储数据的集合 |
| `table` | 表 | 二维结构化数据，由行和列组成 |
| `row` / `record` | 行 / 记录 | 表中的一条数据 |
| `column` / `field` | 列 / 字段 | 表中的一个属性 |
| `primary key` (PK) | 主键 | 唯一标识一条记录的列 |
| `foreign key` (FK) | 外键 | 引用另一张表主键的列 |
| `index` | 索引 | 加速查询的数据结构 |
| `query` | 查询 | 从数据库中获取数据 |
| `CRUD` | 增删改查 | Create / Read / Update / Delete |
| `JOIN` | 连接 | 把多张表的数据拼在一起 |
| `INNER JOIN` | 内连接 | 只返回两表都匹配的行 |
| `LEFT JOIN` | 左连接 | 返回左表所有行，右表不匹配的为 NULL |
| `GROUP BY` | 分组 | 按某列分组，常配合聚合函数 |
| `ORDER BY` | 排序 | 排序结果 |
| `WHERE` | 条件 | 过滤行 |
| `HAVING` | 分组后过滤 | 对 GROUP BY 结果过滤 |
| `transaction` | 事务 | 一组操作要么全成功，要么全失败 |
| `commit` | 提交 | 确认事务修改 |
| `rollback` | 回滚 | 撤销事务修改 |
| `ACID` | 事务四大特性 | 原子性、一致性、隔离性、持久性 |
| `ORM` | 对象关系映射 | 用对象操作数据库 |

### 代码中的真实用例

**基本 CRUD**

```sql
-- Create: 插入新记录
INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 30);

-- Read: 查询数据
SELECT name, email FROM users WHERE age > 18 ORDER BY name;

-- Update: 更新记录
UPDATE users SET age = 31 WHERE name = 'Alice';

-- Delete: 删除记录
DELETE FROM users WHERE name = 'Alice';
```

**JOIN 的使用场景**

当数据分散在多张表中时，JOIN 把它们拼在一起。比如有一张 `users` 表和一张 `orders` 表，想查每个用户的订单信息：

```sql
-- INNER JOIN：只返回有订单的用户
SELECT orders.id, users.name, orders.amount
FROM orders
INNER JOIN users ON orders.user_id = users.id;

-- LEFT JOIN：返回所有用户，没有订单的补 NULL
SELECT users.name, orders.amount
FROM users
LEFT JOIN orders ON users.id = orders.user_id;
-- 没有订单的用户也会出现，amount 为 NULL
```

用 Venn 图来理解：INNER JOIN 是两圆的交集，LEFT JOIN 是左圆的全部。

**GROUP BY + HAVING**

```sql
-- 统计每个用户的订单数量，只看下单超过3次的
SELECT user_id, COUNT(*) as order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 3
ORDER BY order_count DESC;
```

**ORM 示例（Python SQLAlchemy）**

```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# 用对象操作数据库，不用写 SQL
with Session(engine) as session:
    user = User(name="Alice", age=30)  # Create
    session.add(user)
    session.commit()
    
    alice = session.query(User).filter_by(name="Alice").first()  # Read
```

ORM 的好处是代码可读性高、防 SQL 注入，但坏处是生成的 SQL 可能不够高效，复杂查询还是得手写 SQL。

### 常见误用与混淆

**`WHERE` vs `HAVING`**

这是 SQL 面试的经典题：

```sql
-- ✅ 正确：先 WHERE 过滤行，再 GROUP BY，最后 HAVING 过滤分组
SELECT dept, COUNT(*) as cnt
FROM employees
WHERE salary > 5000   -- 先过滤掉低薪的行
GROUP BY dept
HAVING COUNT(*) > 2;  -- 再过滤掉人数不足的部门

-- ❌ 错误：HAVING 不能替代 WHERE
SELECT dept, COUNT(*) as cnt
FROM employees
GROUP BY dept
HAVING salary > 5000 AND COUNT(*) > 2;  -- salary 不能出现在 HAVING 中！
```

口诀：**WHERE 过滤行（分组前），HAVING 过滤组（分组后）**。

**`primary key` vs `unique`**

两者都保证唯一性，但区别在于：
- `primary key`：不能为 NULL，每张表只能有一个
- `unique`：可以为 NULL，一张表可以有多个

**ACID 四大特性**

| 缩写 | 英文 | 中文 | 含义 |
|------|------|------|------|
| A | Atomicity | 原子性 | 事务中的操作要么全做，要么全不做 |
| C | Consistency | 一致性 | 事务前后数据保持一致状态 |
| I | Isolation | 隔离性 | 并发事务之间互不干扰 |
| D | Durability | 持久性 | 事务提交后修改永久保存 |

转账场景的经典例子：A 给 B 转 100 块。原子性保证扣钱和加钱要么都成功要么都失败；一致性保证总金额不变；隔离性保证并发转账不互相干扰；持久性保证转账成功后即使断电也不丢数据。

---

## 1.7 网络与协议词汇（HTTP/TCP/socket/endpoint）

互联网的本质就是计算机之间聊天。聊天的规则叫协议，聊天的地址叫 endpoint，聊天的通道叫 socket。搞懂这些词，你才能理解网络请求是怎么跑的，才能设计出合理的 API，才能排查网络问题。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `HTTP` (HyperText Transfer Protocol) | 超文本传输协议 | Web 通信的基础协议 |
| `HTTPS` | 加密 HTTP | HTTP + TLS/SSL 加密 |
| `TCP` (Transmission Control Protocol) | 传输控制协议 | 可靠的、面向连接的传输协议 |
| `UDP` (User Datagram Protocol) | 用户数据报协议 | 不可靠但快速的传输协议 |
| `IP` (Internet Protocol) | 网际协议 | 负责数据包寻址和路由 |
| `socket` | 套接字 | 网络通信的端点 |
| `endpoint` | 端点 | API 服务的访问地址 |
| `port` | 端口 | 区分同一机器上不同服务的编号 |
| `request` | 请求 | 客户端发给服务端的消息 |
| `response` | 响应 | 服务端返回给客户端的消息 |
| `header` | 请求/响应头 | 携带元信息的键值对 |
| `body` / `payload` | 请求/响应体 | 实际传输的数据 |
| `status code` | 状态码 | 表示请求结果的数字 |
| `GET` / `POST` / `PUT` / `DELETE` | HTTP 方法 | 对应 CRUD 的 HTTP 动词 |
| `PATCH` | 部分更新 | 只修改资源的部分字段 |
| `cookie` | Cookie | 浏览器存储的小段数据 |
| `session` | 会话 | 服务端维护的客户端状态 |
| `token` / `JWT` | 令牌 / JSON Web Token | 无状态认证的凭证 |
| `CORS` | 跨域资源共享 | 浏览器同源策略的放宽机制 |
| `WebSocket` | WebSocket | 全双工通信协议 |
| `REST` | 表述性状态转移 | API 设计风格 |
| `API` | 应用编程接口 | 程序之间交互的约定 |

### 代码中的真实用例

**HTTP 请求方法对应 CRUD**

| HTTP 方法 | CRUD | 用途 | 幂等性 |
|-----------|------|------|--------|
| `GET` | Read | 获取资源 | ✅ 幂等 |
| `POST` | Create | 创建资源 | ❌ 不幂等 |
| `PUT` | Update | 全量更新 | ✅ 幂等 |
| `PATCH` | Update | 部分更新 | ❌ 不幂等 |
| `DELETE` | Delete | 删除资源 | ✅ 幂等 |

> **幂等（idempotent）**：同一个请求执行一次和执行多次的效果相同。比如 `DELETE /users/123` 执行一次和执行十次，结果都是"用户123不存在"。

**状态码分类**

记住状态码的大类就够了，具体码查文档：

| 范围 | 含义 | 常见示例 |
|------|------|----------|
| 2xx | 成功 | 200 OK、201 Created、204 No Content |
| 3xx | 重定向 | 301 永久重定向、302 临时重定向 |
| 4xx | 客户端错误 | 400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found、429 Too Many Requests |
| 5xx | 服务端错误 | 500 Internal Server Error、502 Bad Gateway、503 Service Unavailable |

**RESTful API 设计**

```
GET    /api/users          # 获取用户列表
GET    /api/users/123      # 获取单个用户
POST   /api/users          # 创建用户
PUT    /api/users/123      # 更新用户（全量）
PATCH  /api/users/123      # 更新用户（部分字段）
DELETE /api/users/123      # 删除用户
```

REST 的核心思想：用 URL 表示资源，用 HTTP 方法表示操作。

**fetch 请求示例**

```javascript
const response = await fetch('https://api.example.com/users/123', {
    method: 'GET',
    headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1...',
        'Accept': 'application/json'
    }
});
const data = await response.json();
```

### 常见误用与混淆

**`GET` vs `POST`——不只是语义不同**

- `GET` 参数在 URL 中，有长度限制，会被缓存，会留在浏览历史里
- `POST` 参数在 body 中，无长度限制，不缓存，不留浏览历史

**安全建议**：永远不要用 `GET` 传密码或敏感信息——URL 会被记录在服务器日志、浏览器历史和 CDN 缓存中。

**`401 Unauthorized` vs `403 Forbidden`**

这俩是最容易搞混的状态码：

- `401`：你没登录（不知道你是谁）→ "请先认证"
- `403`：你登录了但没权限（知道你是谁，但你不能做这个）→ "你不能干这个"

**`cookie` vs `session` vs `token`**

| 方案 | 存储位置 | 状态 | 特点 |
|------|----------|------|------|
| `cookie` | 客户端浏览器 | 有状态 | 自动发送，有域名限制 |
| `session` | 服务端 | 有状态 | 依赖 cookie 传 session ID |
| `token` (JWT) | 客户端 | 无状态 | 服务端不存储，自包含信息 |

现代 Web 应用更倾向用 token（尤其是 JWT），因为它无状态、易扩展、跨域友好。

**`TCP` vs `UDP`**

| 特性 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接（三次握手） | 无连接 |
| 可靠性 | 可靠（重传机制） | 不可靠 |
| 顺序 | 保证顺序 | 不保证顺序 |
| 速度 | 较慢 | 较快 |
| 应用场景 | HTTP、文件传输 | 视频流、游戏、DNS |

HTTP/3 开始用 QUIC 协议（基于 UDP），这是网络协议演进的一个有趣趋势——在 UDP 上自己实现可靠性，绕过 TCP 的队头阻塞问题。

---

## 1.8 操作系统与底层词汇（thread/process/memory/IO）

写应用代码时你可能不太关心操作系统，但当遇到性能问题、并发 bug、内存泄漏时，底层知识就是你的救命稻草。这些词汇是理解系统性能和并发编程的基础，也是从"会写代码"到"写好代码"的分水岭。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| `process` | 进程 | 程序运行中的实例，有独立内存空间 |
| `thread` | 线程 | 进程内的执行单元，共享进程内存 |
| `coroutine` | 协程 | 用户态的轻量级"线程" |
| `concurrency` | 并发 | 多个任务交替执行（看起来同时） |
| `parallelism` | 并行 | 多个任务真正同时执行（多核） |
| `memory` | 内存 | 程序运行时的数据存储区域 |
| `stack` (内存) | 栈内存 | 存局部变量和函数调用帧 |
| `heap` (内存) | 堆内存 | 动态分配的内存区域 |
| `garbage collection` (GC) | 垃圾回收 | 自动回收不再使用的内存 |
| `memory leak` | 内存泄漏 | 不再使用的内存没有被释放 |
| `IO` (Input/Output) | 输入/输出 | 读写数据的操作 |
| `blocking` | 阻塞 | 操作未完成时线程等待 |
| `non-blocking` | 非阻塞 | 操作未完成时线程不等待 |
| `synchronous` (sync) | 同步 | 等待操作完成再继续 |
| `asynchronous` (async) | 异步 | 不等待，完成后回调通知 |
| `buffer` | 缓冲区 | 临时存储数据的内存区域 |
| `cache` | 缓存 | 加速读取的临时存储 |
| `deadlock` | 死锁 | 多个线程互相等待对方释放资源 |
| `race condition` | 竞态条件 | 并发访问共享数据导致的不确定结果 |
| `mutex` | 互斥锁 | 保证同一时刻只有一个线程访问资源 |
| `semaphore` | 信号量 | 控制同时访问的线程数量 |
| `context switch` | 上下文切换 | CPU 从一个线程切换到另一个 |
| `file descriptor` (fd) | 文件描述符 | Unix 中对打开文件的引用 |

### 代码中的真实用例

**并发（concurrency）vs 并行（parallelism）**

这是一个经典面试题。Go 语言之父 Rob Pike 的名言：

> Concurrency is not parallelism, although it enables parallelism.

```python
# 并发（concurrency）：单线程交替执行
import asyncio

async def task(name):
    await asyncio.sleep(1)
    print(f"Task {name} done")

async def main():
    await asyncio.gather(task("A"), task("B"), task("C"))
    # 3个任务约1秒完成，单线程"同时"处理

# 并行（parallelism）：多核同时执行
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(work, range(10))  # 4个进程真正并行
```

**线程安全与竞态条件**

```python
import threading

# ❌ 竞态条件：多个线程同时修改共享变量
counter = 0
def increment():
    global counter
    for _ in range(100000):
        counter += 1  # 不是原子操作！读-改-写三步可能被打断

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start(); t2.start()
t1.join(); t2.join()
print(counter)  # 预期 200000，实际可能小于 200000

# ✅ 用锁（mutex）解决
lock = threading.Lock()
counter = 0
def safe_increment():
    global counter
    for _ in range(100000):
        with lock:  # 同一时刻只有一个线程能进入
            counter += 1
```

**死锁（deadlock）**

死锁是并发编程中最头疼的问题之一。经典场景：线程 A 持有锁 1 等锁 2，线程 B 持有锁 2 等锁 1，两个线程永远等下去。

```python
lock1 = threading.Lock()
lock2 = threading.Lock()

def task_a():
    with lock1:
        time.sleep(0.1)
        with lock2:  # 等待 lock2 —— 死锁！
            print("A done")

def task_b():
    with lock2:
        time.sleep(0.1)
        with lock1:  # 等待 lock1 —— 死锁！
            print("B done")
```

避免死锁的策略：
1. **固定锁的获取顺序**（所有线程都先锁1再锁2）
2. **使用超时**（`lock.acquire(timeout=5)`）
3. **使用更高级的并发原语**（如 `queue.Queue`）

### 常见误用与混淆

**`process` vs `thread`**

| 特性 | Process | Thread |
|------|---------|--------|
| 内存空间 | 独立 | 共享 |
| 通信方式 | IPC（管道、队列、共享内存） | 直接读写共享变量 |
| 创建开销 | 大 | 小 |
| 安全性 | 高（一个崩了不影响别的） | 低（一个崩了整个进程崩） |
| Python 中 | `multiprocessing` | `threading`（受 GIL 限制） |

Python 的 GIL（Global Interpreter Lock）导致多线程无法真正并行执行 CPU 密集型任务，这时要用多进程。但 IO 密集型任务（网络请求、文件读写）用多线程或协程就够了，因为 IO 等待时 GIL 会释放。

**`concurrency` vs `parallelism`**

- **并发（concurrency）**：处理多个任务的能力（交替执行）—— 一个人同时接两个电话，来回切换
- **并行（parallelism）**：同时执行多个任务 —— 两个人各接一个电话

**`synchronous` vs `asynchronous` vs `blocking` vs `non-blocking`**

这两组词经常被混用，但严格来说关注点不同：

- **sync/async**：关注**通信方式**——调用者是否主动等待结果
- **blocking/non-blocking**：关注**线程状态**——操作未完成时线程是否被挂起

**`buffer` vs `cache`**

- **buffer（缓冲区）**：协调生产者和消费者的速度差异。比如视频缓冲，先存一部分再播放
- **cache（缓存）**：避免重复计算或读取。比如把数据库查询结果缓存起来

---

## 本章小结

这一章我们覆盖了编程世界最核心的八大词汇领域：

1. **数据类型与变量**：搞清 `null`/`undefined`/`nil`/`None` 的区别，记住 `mutable` vs `immutable`
2. **控制流与逻辑**：`break` 和 `continue` 不是一回事，`expression` 和 `statement` 也不一样
3. **函数与方法**：`parameter` 是占位符，`argument` 是实际值；`overload` 和 `override` 差了一个字差了一个概念
4. **面向对象**：继承表示 "is-a"，组合表示 "has-a"，优先用组合
5. **数据结构与算法**：`stack`/`heap` 有双重含义，BFS 用队列、DFS 用递归
6. **数据库与 SQL**：`WHERE` 在分组前过滤，`HAVING` 在分组后过滤；ACID 是事务的四大支柱
7. **网络与协议**：`GET` 别传密码，401 是没登录，403 是没权限
8. **操作系统底层**：并发不是并行，进程有独立内存而线程共享内存，死锁要靠固定锁顺序来避免

这些词汇不是让你死记硬背的。在后续章节中，你会在代码审查、技术文档、错误信息、开源项目里反复见到它们。多见几次，多查几次，自然就刻在脑子里了。

> 💡 **学习建议**：遇到不认识的英文术语时，先不要急着翻译成中文。试着用英文理解它的字面意思，往往字面意思本身就是最好的解释。比如 `polymorphism` = `poly`（多）+ `morph`（形态）+ `ism`（特性）= 多态性。再比如 `idempotent` = `idem`（相同）+ `potent`（能力）= 幂等，执行多次结果相同的能力。
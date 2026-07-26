# 第4章 组件化开发、Hooks与组件通信机制

你写的RN组件，是不是一个文件上千行，Props传参层层嵌套，State更新莫名其妙不生效，兄弟组件通信靠全局变量硬撑？

90%的RN项目维护灾难，根源都在组件设计不规范。组件分层混乱、通信全靠Props透传、状态更新不遵循不可变原则，这些问题在小项目里感觉不到痛，一旦业务膨胀就是雪崩式的技术债。我见过一个页面组件三千多行代码，里面混着二十多个useState、十几个useEffect，改一个状态要看半小时才能理清数据流向。

我是怕浪猫，一个在RN（React Native）坑里摸爬滚打多年的开发者。之前几章我们搞定了环境搭建、JSX语法、核心组件和布局适配，今天这章是承上启下的关键——组件化开发、Hooks与组件通信机制。这章内容如果你吃透了，后面写任何业务页面都会有一种"庖丁解牛"的顺畅感。

> 组件不是写完就完了，组件是设计出来的。好的组件设计让复杂业务变得简单，坏的组件设计让简单业务变得不可维护。

## 4.1 RN组件分类与开发规范

### 4.1.1 函数组件与类组件核心区别

在RN的世界里，组件分为两大阵营：函数组件（Function Component）和类组件（Class Component）。自从React 16.8版本引入Hooks之后，函数组件就成了绝对主流，但类组件在老项目和某些特殊场景中依然存在，理解两者的区别是基本功。

先看一段最直观的对比代码：

```tsx
// 类组件写法
class ProfileScreen extends React.Component {
  state = { count: 0 };
  componentDidMount() {
    console.log('组件挂载完成');
  }
  render() {
    return (
      <View>
        <Text>{this.state.count}</Text>
        <TouchableOpacity onPress={() => this.setState({ count: this.state.count + 1 })}>
          <Text>+1</Text>
        </TouchableOpacity>
      </View>
    );
  }
}

// 函数组件写法（推荐）
const ProfileScreen = () => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    console.log('组件挂载完成');
  }, []);
  return (
    <View>
      <Text>{count}</Text>
      <TouchableOpacity onPress={() => setCount(count + 1)}>
        <Text>+1</Text>
      </TouchableOpacity>
    </View>
  );
};
```

两者核心区别可以用一张表说清楚：

| 对比维度 | 类组件 | 函数组件 |
|---------|--------|---------|
| 语法形式 | class继承React.Component | 普通箭头函数 |
| 状态管理 | this.state + this.setState | useState Hook |
| 生命周期 | componentDidMount等回调 | useEffect Hook替代 |
| 代码量 | 较多，样板代码重 | 较少，简洁直观 |
| this指向 | 存在this绑定问题 | 无this困扰 |
| 性能优化 | shouldComponentUpdate | React.memo |
| 推荐程度 | 逐步淘汰 | 官方推荐 |

类组件最大的痛点是`this`绑定问题。新手经常踩的坑就是在事件回调中`this`指向`undefined`，需要用`bind`绑定或者箭头函数来修复。比如这段代码：

```tsx
class ProfileScreen extends React.Component {
  constructor(props) {
    super(props);
    // 方式一：在构造函数中bind
    this.handlePress = this.handlePress.bind(this);
  }
  handlePress() {
    this.setState({ count: this.state.count + 1 });
  }
  // 方式二：用箭头函数定义方法
  handlePressSafe = () => {
    this.setState({ count: this.state.count + 1 });
  };
}
```

函数组件完全没有这个烦恼，因为函数内部不存在`this`概念。所有的状态和方法都直接定义在函数作用域内，访问起来直截了当，不需要担心`this`指向哪里。

另一个重要区别是生命周期的处理方式。类组件通过一系列生命周期方法来处理不同阶段的逻辑：`componentDidMount`处理挂载后的逻辑，`componentDidUpdate`处理更新后的逻辑，`componentWillUnmount`处理卸载前的清理。而函数组件通过一个`useEffect`就能覆盖所有这些场景，通过传入不同的依赖数组来控制执行时机。

> 从类组件迁移到函数组件，不只是语法变化，更是思维方式的转变：从"生命周期驱动"转向"数据驱动"。在类组件中你思考的是"组件到了哪个阶段"，在函数组件中你思考的是"什么数据变了，需要做什么"。

### 4.1.2 企业项目组件分层设计思想

在真实企业项目中，组件不是随便建的文件夹里随便放的文件。一个健康的RN项目应该有清晰的分层架构。怕浪猫见过太多项目，所有组件堆在一个`components`目录下，两百多个文件混在一起，找起来像大海捞针。更可怕的是，有些组件之间互相引用，形成循环依赖，改一个组件引发连锁反应。

合理的分层架构应该是这样的：

```
src/
├── components/        # 公共组件层
│   ├── Button/
│   ├── Card/
│   └── Modal/
├── business/          # 业务组件层
│   ├── UserCard/
│   ├── OrderItem/
│   └── ProductList/
├── pages/             # 页面组件层
│   ├── Home/
│   ├── Profile/
│   └── Order/
├── hooks/             # 自定义Hooks层
├── utils/             # 工具函数层
└── services/          # 接口请求层
```

这个分层的核心思想是**依赖单向流动**：页面组件可以引用业务组件和公共组件，业务组件可以引用公共组件，但公共组件不应该反向引用业务组件。这就像建筑中的承重结构，上层依赖下层，下层不能依赖上层。

违反这个原则的典型表现是：一个叫`Button`的公共组件里面居然import了`UserContext`，这意味着这个Button只能用在用户相关的页面里，复用性直接归零。又或者一个`Card`组件里面import了`@/services/api.ts`，直接在公共组件里发接口请求，这会导致这个Card组件无法在离线场景或测试环境中独立使用。

分层架构还有一个好处是团队协作。公共组件由基础架构组维护，业务组件由业务团队维护，页面组件由具体开发者负责。各层之间通过明确的接口约定交互，互不干扰，并行开发效率大幅提升。

### 4.1.3 公共组件、业务组件、页面组件划分

三种组件的边界划分是很多团队的痛点。怕浪猫的划分原则很简单，就一句话：**看它是否包含业务语义**。

公共组件：不含任何业务语义，纯粹的UI（User Interface）展示和交互。比如Button、Input、Card、Modal。这类组件可以跨项目复用，甚至可以抽成独立的npm包。判断标准是：把它拿到另一个完全不同的项目中，不做任何修改就能用。

业务组件：包含特定业务逻辑和数据结构，但不是完整的页面。比如UserCard（用户卡片）、OrderItem（订单列表项）、ProductCard（商品卡片）。这类组件在本项目内复用，但拿到另一个项目就需要改造，因为数据结构和业务规则不同。

页面组件：包含完整的页面布局、数据请求和状态管理。比如HomePage、ProfilePage、OrderDetailPage。每个页面组件对应一个路由入口。页面组件是业务逻辑的聚合点，它协调各个业务组件和公共组件，组装出完整的页面。

来看一个实际项目中三层组件的引用关系：

```tsx
// pages/Order/OrderList.tsx 页面组件
import { OrderItem } from '@/business/OrderItem';
import { LoadMoreList } from '@/components/LoadMoreList';
import { usePagination } from '@/hooks/usePagination';

const OrderList = () => {
  const { list, loading, refresh, loadMore } = usePagination(
    (page) => fetchOrders(page)
  );
  return (
    <LoadMoreList
      data={list}
      loading={loading}
      onRefresh={refresh}
      onLoadMore={loadMore}
      renderItem={({ item }) => <OrderItem data={item} />}
    />
  );
};
```

```tsx
// business/OrderItem/index.tsx 业务组件
import { Card } from '@/components/Card';
import { PriceText } from '@/components/PriceText';
import { OrderStatus } from '@/business/OrderStatus';

export const OrderItem = ({ data }) => (
  <Card>
    <Text>{data.shopName}</Text>
    <PriceText value={data.totalPrice} />
    <OrderStatus status={data.status} />
  </Card>
);
```

注意到了吗？页面组件引用业务组件，业务组件引用公共组件，层次分明，没有任何反向依赖。`OrderItem`不知道也不关心自己被哪个页面使用，它只需要知道传入的`data`长什么样就够了。

### 4.1.4 组件单一职责设计原则

单一职责原则（Single Responsibility Principle，SRP）是组件设计最重要的原则。一个组件只做一件事，如果它做了两件事，就应该拆成两个组件。这条原则看起来简单，但在实际开发中极易被违反，因为业务需求往往是"顺便加个东西"，开发者顺手就在现有组件里加了一段代码，日积月累组件就变成了大杂烩。

怕浪猫在代码审查时经常看到这样的反面教材：

```tsx
// 反面教材：一个组件干了三件事
const UserOrderCard = ({ user, orders, onRefresh }) => {
  // 职责1：展示用户信息
  // 职责2：展示订单列表
  // 职责3：处理下拉刷新逻辑
  const [refreshing, setRefreshing] = useState(false);
  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  };
  return (
    <View>
      <View>
        <Image source={{ uri: user.avatar }} />
        <Text>{user.name}</Text>
        <Text>{user.phone}</Text>
      </View>
      <FlatList
        data={orders}
        refreshing={refreshing}
        onRefresh={handleRefresh}
        renderItem={({ item }) => <Text>{item.name}</Text>}
      />
    </View>
  );
};
```

这个组件同时承担了用户信息展示、订单列表渲染和刷新逻辑三个职责。当产品需求要求"用户信息部分增加会员等级展示"时，你需要在一个包含订单列表逻辑的组件里改代码，稍有不慎就会影响订单列表的功能。当另一个页面只需要用户信息展示而不需要订单列表时，这个组件完全无法复用。

正确的做法是拆分：

```tsx
// 用户信息卡片 - 只负责展示用户信息
const UserInfoCard = ({ user }) => (
  <View>
    <Image source={{ uri: user.avatar }} />
    <Text>{user.name}</Text>
    <Text>{user.phone}</Text>
  </View>
);

// 订单列表 - 只负责渲染订单
const OrderListSection = ({ orders, onRefresh, refreshing }) => (
  <FlatList
    data={orders}
    refreshing={refreshing}
    onRefresh={onRefresh}
    renderItem={({ item }) => <OrderItem data={item} />}
  />
);

// 页面组件 - 负责组合和状态管理
const UserOrderPage = () => {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  return (
    <View>
      <UserInfoCard user={user} />
      <OrderListSection
        orders={orders}
        refreshing={refreshing}
        onRefresh={handleRefresh}
      />
    </View>
  );
};
```

> 一个好的组件，应该像乐高积木——单一形状、明确接口、自由组合。如果一个积木块上同时有轮子和窗户，它就只能用来拼一种东西。

### 4.1.5 组件命名与文件目录规范

命名规范看似小事，但在团队协作中直接影响开发效率。一个叫`MyButton`的组件和一个叫`SubmitBtn`的组件，团队成员可能搞混哪个是哪个。怕浪猫坚持以下命名原则：

组件名使用大驼峰（PascalCase），文件名与组件名一致。每个组件一个独立目录，入口文件为`index.tsx`，样式文件为`styles.ts`，类型定义文件为`types.ts`，测试文件为`__tests__/index.test.tsx`。

```
components/
├── Button/
│   ├── index.tsx       # 组件实现
│   ├── styles.ts       # 样式定义
│   ├── types.ts        # 类型定义
│   └── __tests__/
│       └── index.test.tsx
├── LoadMoreList/
│   ├── index.tsx
│   ├── styles.ts
│   └── types.ts
```

这种结构的好处是，当组件需要拆分子组件时，可以在目录内直接扩展，不会污染外层目录。比如`LoadMoreList`内部需要一个`LoadMoreFooter`子组件，直接放在`LoadMoreList/LoadMoreFooter.tsx`即可。引用时统一用`@/components/Button`，不暴露内部文件结构。

命名还要避免缩写。`Btn`不如`Button`直观，`Img`不如`Image`清晰。除非常见的行业缩写如API（Application Programming Interface）、URL（Uniform Resource Locator），否则宁愿多打几个字母也不要让人猜。

## 4.2 Props属性传参与类型校验

### 4.2.1 父子组件基础传参实战

Props（Properties）是RN组件通信最基础的方式。父组件通过Props向子组件传递数据，子组件通过Props接收并使用。这种数据流动是单向的：父到子。理解单向数据流是理解React的核心，所有的状态管理方案都是围绕这个原则展开的。

来看一个实际业务中的传参示例：

```tsx
// 父组件传递数据
const ProductPage = () => {
  const productInfo = {
    name: '蓝牙耳机Pro',
    price: 299,
    stock: 150,
    image: 'https://example.com/earphone.jpg',
  };

  const handleAddToCart = (product) => {
    addToCartAPI(product.id).then(() => {
      showToast('已加入购物车');
    });
  };

  return (
    <ProductCard
      product={productInfo}
      onAddToCart={() => handleAddToCart(productInfo)}
    />
  );
};

// 子组件接收并使用
const ProductCard = ({ product, onAddToCart }) => {
  return (
    <View>
      <Image source={{ uri: product.image }} style={styles.image} />
      <Text style={styles.name}>{product.name}</Text>
      <Text style={styles.price}>¥{product.price}</Text>
      <Text style={styles.stock}>库存: {product.stock}件</Text>
      <TouchableOpacity style={styles.button} onPress={onAddToCart}>
        <Text style={styles.buttonText}>加入购物车</Text>
      </TouchableOpacity>
    </View>
  );
};
```

这里父组件传了两个Props：`product`（数据对象）和`onAddToCart`（回调函数）。这是父子通信的经典模式——数据向下传，事件向上回。父组件负责数据的获取和管理，子组件负责数据的展示和用户交互的触发。

### 4.2.2 Props默认值配置与容错处理

在实际开发中，不能保证父组件每次都传递所有Props。如果子组件直接使用未传递的Props，会导致`undefined`报错。比如父组件没有传`stock`，子组件渲染`库存: {product.stock}件`时会显示`库存: undefined件`，虽然不会崩溃但用户体验很差。更严重的是如果对`undefined`做进一步操作，比如`product.stock.toString()`，直接白屏崩溃。

所以给Props设置默认值是基本的防御性编程：

```tsx
// 方式一：参数解构默认值（推荐）
const Avatar = ({ size = 40, source, borderRadius = 20 }) => {
  return (
    <Image
      source={source || require('./default-avatar.png')}
      style={{ width: size, height: size, borderRadius }}
    />
  );
};

// 方式二：组件静态属性（已不推荐）
Avatar.defaultProps = {
  size: 40,
  borderRadius: 20,
};
```

推荐使用方式一，因为它是纯JS（JavaScript）语法，不依赖React特定API，而且在函数参数层面一目了然。同时，方式二的`defaultProps`在新的React版本中已经标记为不推荐使用，未来可能移除。

容错处理的关键场景包括：图片地址为空时显示默认图，数组数据为空时显示占位文案，数值为`undefined`时给默认值0。这些看似细节的处理，在线上环境中能避免大量白屏崩溃。怕浪猫曾经处理过一个线上事故，就是因为后端某个字段偶尔返回null，前端没有做容错直接访问属性导致白屏，加了一个默认值就解决了。

```tsx
// 完整容错示例
const ProductCard = ({ product = {}, onAddToCart }) => {
  const { name = '未知商品', price = 0, stock = 0, image } = product;
  return (
    <View>
      <Image source={image ? { uri: image } : defaultImage} />
      <Text>{name}</Text>
      <Text>¥{price.toFixed(2)}</Text>
      {stock > 0 ? <Text>库存: {stock}件</Text> : <Text>暂无库存</Text>}
    </View>
  );
};
```

### 4.2.3 TS实现Props强类型校验

在企业项目中，TS（TypeScript）是标配。用TS给Props定义类型，可以在编译阶段就发现传参错误，而不是等到运行时白屏。类型定义的成本极低，但收益极高——减少了大量的运行时调试时间。

```tsx
// types.ts 定义Props类型
export interface ProductInfo {
  id: string;
  name: string;
  price: number;
  stock: number;
  image?: string;       // 可选属性，可能没有图片
  discount?: number;    // 可选属性，可能有折扣
}

export interface ProductCardProps {
  product: ProductInfo;
  onAddToCart: (product: ProductInfo) => void;
  showStock?: boolean;       // 是否显示库存，默认true
  layout?: 'vertical' | 'horizontal';  // 布局方向
}

// 组件中使用
import { ProductCardProps } from './types';

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onAddToCart,
  showStock = true,
  layout = 'vertical',
}) => {
  return (
    <View style={layout === 'vertical' ? styles.vertical : styles.horizontal}>
      <Text>{product.name}</Text>
      <Text>¥{product.price}</Text>
      {showStock && <Text>库存: {product.stock}</Text>}
    </View>
  );
};
```

TS类型定义的好处是：当父组件传入了`price: "299"`（字符串而非数字）时，编辑器会立即标红报错，不用等到运行时才发现问题。当另一个开发者使用你的组件时，IDE（Integrated Development Environment）的自动补全会提示所有可用的Props名称和类型，几乎不需要查文档。

还有一个实践建议：把类型定义放在独立的`types.ts`文件中，而不是写在组件文件里。这样其他文件如果需要引用`ProductInfo`类型来传递数据，可以直接import，不需要从组件文件中提取。

> 类型校验不是在给你添麻烦，而是在帮你挡子弹。一个TS接口定义五分钟写完，一个线上白屏bug可能要查两小时。

### 4.2.4 Props只读特性与开发规范

React有一条铁律：Props是只读的。子组件绝不能修改Props传进来的数据。这条规则看起来简单，但新手很容易在不知不觉中违反。特别是当Props传进来的是一个对象或数组时，直接修改其内部属性或元素是最常见的错误。

```tsx
// 反面教材：直接修改Props
const CartItem = ({ item }) => {
  item.quantity += 1; // 绝对禁止！
  return <Text>{item.quantity}</Text>;
};

// 正确做法：复制后使用
const CartItem = ({ item }) => {
  const [quantity, setQuantity] = useState(item.quantity);
  return (
    <View>
      <Text>{quantity}</Text>
      <TouchableOpacity onPress={() => setQuantity(quantity + 1)}>
        <Text>+1</Text>
      </TouchableOpacity>
    </View>
  );
};
```

直接修改Props会导致不可预测的渲染问题，因为React无法感知到数据变化，不会触发重新渲染。更严重的是，如果父组件也持有这个对象的引用，你修改了它就等于偷偷改了父组件的状态，数据流变得不可追踪，bug就此埋下。

正确的做法是将Props数据作为初始值复制到State中，后续所有操作都针对State进行。如果需要把修改同步回父组件，通过回调函数通知父组件自行更新数据。

### 4.2.5 批量传参与解构优化技巧

当组件Props较多时，逐个传递既冗长又容易遗漏。ES6的展开运算符（Spread Operator）可以优雅地解决这个问题。但在使用时也要注意一些潜在的坑。

```tsx
// 冗长写法
<UserCard
  name={user.name}
  age={user.age}
  avatar={user.avatar}
  phone={user.phone}
  email={user.email}
/>

// 优雅写法：展开运算符批量传参
<UserCard {...user} />

// 子组件解构接收
const UserCard = ({ name, age, avatar, ...restProps }) => {
  return (
    <View>
      <Image source={avatar} />
      <Text>{name}</Text>
      <Text>{age}岁</Text>
      {/* restProps包含phone和email，需要时再取 */}
    </View>
  );
};
```

展开传参的陷阱在于：它会把`user`对象的所有属性都传给子组件，包括子组件不需要的属性。如果`user`中包含敏感信息（如token、password），这会造成安全隐患。更实际的问题是，当对象属性变化时，即使子组件不需要这些属性，新增的属性也会导致子组件接收多余的Props。

所以展开传参要确保数据对象是干净的，或者在传递前显式挑选字段：

```tsx
// 安全做法：显式挑选需要的字段
const userCardProps = { name: user.name, age: user.age, avatar: user.avatar };
<UserCard {...userCardProps} />

// 或者直接解构传递
const { name, age, avatar } = user;
<UserCard name={name} age={age} avatar={avatar} />
```

## 4.3 State局部状态管理机制

### 4.3.1 useState状态定义与基础使用

State是组件的"记忆"。Props是外部传入的，State是组件内部自己管理的。useState是React Hooks中最基础也是最常用的Hook，几乎所有函数组件都离不开它。

```tsx
import { useState } from 'react';

const Counter = () => {
  const [count, setCount] = useState(0);
  // count: 当前状态值
  // setCount: 更新状态的函数
  // useState(0): 0是初始值

  return (
    <View>
      <Text>当前计数: {count}</Text>
      <TouchableOpacity onPress={() => setCount(count + 1)}>
        <Text>增加</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => setCount(0)}>
        <Text>重置</Text>
      </TouchableOpacity>
    </View>
  );
};
```

useState的使用模式很固定：`const [状态值, 设置函数] = useState(初始值)`。数组解构的两个变量，第一个是当前状态，第二个是更新函数。命名约定是`set`前缀加状态名，比如`count`对应`setCount`，`loading`对应`setLoading`，`userList`对应`setUserList`。

初始值可以是任意类型的值，也可以是一个函数。当初始值需要通过复杂计算得到时，传入函数可以避免每次渲染都重复计算：

```tsx
// 简单初始值
const [count, setCount] = useState(0);
const [name, setName] = useState('');
const [list, setList] = useState([]);

// 函数初始值（惰性初始化）
const [data, setData] = useState(() => {
  const saved = localStorage.getItem('data');
  return saved ? JSON.parse(saved) : [];
});
```

### 4.3.2 基础数据状态更新规范

基础数据类型（string、number、boolean）的状态更新最简单，直接传入新值即可。但有一个关键特性必须理解：**State更新是异步的**。这不是bug而是设计，React通过批处理多次State更新来优化渲染性能。

```tsx
const Example = () => {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    setCount(count + 1);
    setCount(count + 1);
    setCount(count + 1);
    console.log(count); // 输出0，不是3
  };

  return <TouchableOpacity onPress={handleClick}><Text>{count}</Text></TouchableOpacity>;
};
```

上面的代码连续调用了三次`setCount(count + 1)`，但count最终只会变成1，而不是3。因为在这三次调用中，`count`的值都是0（闭包捕获的值），三次调用等价于`setCount(1)`三次。React批处理后只渲染一次，最终count为1。

如果需要基于前一次的值更新，应该使用函数式更新：

```tsx
const handleClick = () => {
  setCount(prev => prev + 1); // prev是0，返回1
  setCount(prev => prev + 1); // prev是1，返回2
  setCount(prev => prev + 1); // prev是2，返回3
};
```

函数式更新中，React保证每次调用时`prev`都是最新的状态值，所以三次调用后count确实会变成3。这在处理连续操作时非常重要，比如连续点击按钮增加数量、批量更新列表数据等场景。

> 理解State异步更新，是避免RN状态bug的第一道防线。当你发现"明明调了setState但值没变"，九成是踩了这个坑。

### 4.3.3 对象、数组状态更新正确写法

对象和数组是引用类型，这是State更新中最容易出bug的地方。React通过浅比较（Shallow Compare）判断状态是否变化，如果你直接修改原对象再传回去，引用地址没变，React不会触发重新渲染。

```tsx
// 反面教材：直接修改原对象
const [user, setUser] = useState({ name: '怕浪猫', age: 25, city: '深圳' });

const updateAge = () => {
  user.age = 26;      // 直接修改原对象
  setUser(user);      // 引用没变，不会重新渲染
  console.log(user);  // { name: '怕浪猫', age: 26 } 数据变了但UI没变
};

// 正确做法：展开创建新对象
const updateAge = () => {
  setUser({ ...user, age: 26 });  // 展开创建新对象，引用变了
};

// 更新多个属性
const updateUser = () => {
  setUser({ ...user, age: 26, city: '广州' });
};
```

数组也是同样的道理：

```tsx
const [list, setList] = useState([1, 2, 3]);

// 反面教材：直接修改原数组
list.push(4); setList(list);           // 引用没变
list.splice(0, 1); setList(list);      // 引用没变
list[0] = 99; setList(list);           // 引用没变

// 正确做法：创建新数组
setList([...list, 4]);                 // 添加
setList(list.filter(i => i !== 2));    // 删除
setList(list.map(i => i === 2 ? 20 : i)); // 修改
setList([99, ...list.slice(1)]);       // 修改首项
```

核心原则就是**不可变数据（Immutable Data）**：永远不要直接修改State，而是创建一个包含新值的新对象或新数组。用一个图来理解这个过程：

```
原状态对象  { name: '怕浪猫', age: 25 }    引用地址: 0x001
                |
    不变性要求：不修改原对象
                |
    展开复制    { ...user, age: 26 }
                |
    新状态对象  { name: '怕浪猫', age: 26 }  引用地址: 0x002 (新地址)
                |
    React检测到引用变化 → 触发重新渲染
```

对于嵌套对象的更新，需要逐层展开，这也是不可变数据操作中最繁琐的部分：

```tsx
const [state, setState] = useState({
  user: { name: '怕浪猫', profile: { age: 25, city: '深圳' } }
});

// 更新嵌套的city
setState({
  ...state,
  user: {
    ...state.user,
    profile: { ...state.user.profile, city: '广州' }
  }
});
```

如果嵌套层级很深，这种写法会非常痛苦。这时候可以考虑使用Immer这样的库，它通过Proxy机制让你用"直接修改"的语法写不可变更新：

```tsx
import { produce } from 'immer';
setState(produce(draft => {
  draft.user.profile.city = '广州';
}));
```

### 4.3.4 状态异步更新原理与避坑

State异步更新的底层原理是批处理（Batching）。React会将多次setState调用合并为一次更新，以提高渲染性能。在React 18之前，只有事件处理函数中的setState会被批处理；React 18之后，自动批处理覆盖了所有场景，包括异步回调、Promise和setTimeout。

```tsx
const [count, setCount] = useState(0);
const [flag, setFlag] = useState(false);

const handleUpdate = () => {
  // 这两次setState会被批处理，只触发一次重新渲染
  setCount(1);
  setFlag(true);
};

const handleAsyncUpdate = async () => {
  await fetchData();
  // React 18之后，这里也会被批处理
  setCount(1);
  setFlag(true);
};
```

批处理带来的一个常见坑是：在同一个事件处理函数中，后续的setState依赖前面setState的结果。由于批处理，前面的setState不会立即生效：

```tsx
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);

const loadData = async () => {
  setLoading(true);
  const res = await fetchList();
  setData(res);              // 设置数据
  setLoading(false);
  console.log(data);         // 仍然是旧值[]
  // 如果紧接着要基于data做计算，应该直接用res
  const filtered = filterData(res); // 用res，不用data
};
```

> 在RN开发中，永远不要在调用setState后立即读取State值。如果需要新值，直接使用你传入的新数据。这条规则看似简单，但违反它导致的bug极其难排查，因为代码看起来"没问题"。

### 4.3.5 局部状态合理拆分原则

一个组件里应该有多少个useState？怕浪猫的原则是：**一个State只管理一个独立的状态域**。如果一个State对象包含多个不相关的属性，那应该拆分成多个独立的useState。

```tsx
// 反面教材：把所有状态塞进一个对象
const [state, setState] = useState({
  loading: false,
  list: [],
  page: 1,
  error: null,
  refreshing: false,
  filterStatus: 'all',
  selectedIds: [],
});
// 更新时要写一大堆展开
setState(prev => ({ ...prev, loading: true }));
// 容易遗漏展开导致覆盖
setState({ loading: true }); // 其他状态全丢了
```

```tsx
// 正确做法：按职责拆分
const [loading, setLoading] = useState(false);
const [list, setList] = useState([]);
const [page, setPage] = useState(1);
const [error, setError] = useState(null);
const [refreshing, setRefreshing] = useState(false);
const [filterStatus, setFilterStatus] = useState('all');
const [selectedIds, setSelectedIds] = useState([]);
```

拆分的好处是更新简单、职责清晰。每个状态独立更新，不会相互影响。但也有一个度的问题：如果几个状态总是同时变化，那把它们合并成一个对象反而更合理。比如一个分页请求的`loading`和`error`就是同时变化的，可以考虑合并。又比如表单的多个字段，如果总是一起提交一起重置，用一个对象State管理更方便。

## 4.4 全场景组件通信方案

### 4.4.1 父子组件正向传值通信

父子组件正向传值就是通过Props从父到子传递数据，这是最基础也最常用的通信方式。前面4.2节已经详细讲过Props传参，这里重点讲实际业务中的组合用法和数据流的控制。

```tsx
// 父组件：订单页面
const OrderPage = () => {
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchOrders(selectedStatus).then(setOrders);
  }, [selectedStatus]);

  return (
    <View>
      <StatusFilter
        value={selectedStatus}
        onChange={setSelectedStatus}
      />
      <OrderList
        orders={orders}
        onOrderPress={(order) => navigation.navigate('OrderDetail', { id: order.id })}
      />
    </View>
  );
};

// 子组件：状态筛选器
const StatusFilter = ({ value, onChange }) => {
  const statuses = [
    { label: '全部', value: 'all' },
    { label: '待付款', value: 'pending' },
    { label: '已付款', value: 'paid' },
    { label: '已发货', value: 'shipped' },
  ];
  return (
    <View style={{ flexDirection: 'row' }}>
      {statuses.map(s => (
        <TouchableOpacity key={s.value} onPress={() => onChange(s.value)}>
          <Text style={{ color: value === s.value ? 'red' : 'black' }}>
            {s.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};
```

这里`OrderPage`作为父组件，把`selectedStatus`通过Props传给`StatusFilter`和`OrderList`两个子组件。当用户点击筛选器时，通过`onChange`回调更新父组件状态，父组件状态变化又触发`OrderList`重新渲染。这就是React的经典数据流：单向数据流，数据从上往下流，事件从下往上回。

单向数据流的好处是可追踪。当`OrderList`的数据出现问题时，你只需要往上追查：谁传了`orders`？`orders`是怎么来的？什么时候更新的？整个数据链路清晰可见。如果数据流是双向的、随意的，调试时就像在迷宫里找出口。

### 4.4.2 子父组件事件回调通信

子组件向父组件通信，标准模式是通过回调函数Props。父组件传一个函数给子组件，子组件在合适的时机调用这个函数，把数据"传"回给父组件。这种模式保持了单向数据流的完整性——子组件不直接修改父组件的数据，而是通过回调"请求"父组件修改。

```tsx
// 父组件
const ShoppingCart = () => {
  const [items, setItems] = useState([
    { id: '1', name: '蓝牙耳机', price: 299, quantity: 1 },
    { id: '2', name: '手机壳', price: 39, quantity: 2 },
  ]);

  const handleRemove = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  const handleQuantityChange = (id: string, quantity: number) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, quantity } : item
    ));
  };

  return (
    <View>
      {items.map(item => (
        <CartItem
          key={item.id}
          data={item}
          onRemove={handleRemove}
          onQuantityChange={handleQuantityChange}
        />
      ))}
      <Text>总价: ¥{items.reduce((sum, i) => sum + i.price * i.quantity, 0)}</Text>
    </View>
  );
};

// 子组件
const CartItem = ({ data, onRemove, onQuantityChange }) => {
  return (
    <View style={styles.cartItem}>
      <Text>{data.name}</Text>
      <Text>¥{data.price}</Text>
      <View style={{ flexDirection: 'row' }}>
        <TouchableOpacity onPress={() => onQuantityChange(data.id, data.quantity - 1)}>
          <Text>-</Text>
        </TouchableOpacity>
        <Text>{data.quantity}</Text>
        <TouchableOpacity onPress={() => onQuantityChange(data.id, data.quantity + 1)}>
          <Text>+</Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity onPress={() => onRemove(data.id)}>
        <Text>删除</Text>
      </TouchableOpacity>
    </View>
  );
};
```

回调函数的命名约定：以`on`开头，描述触发的事件。比如`onRemove`、`onQuantityChange`、`onPress`、`onSelect`。这种命名让代码自文档化，一看函数名就知道什么时候会触发、做什么事情。

### 4.4.3 多层级组件透传解决方案

当数据需要从顶层组件传到深层嵌套的子组件时，如果用Props逐层传递，会出现"Props Drilling"（属性透传）问题。每层组件都要接收并传递不属于自己的Props，既冗余又脆弱——中间任何一层忘记传递，深层组件就拿不到数据。

```
爷爷组件 → Props传递 → 父亲组件 → Props传递 → 孙子组件
     ↑ 不需要这个数据              ↑ 不需要这个数据    ↑ 真正使用数据
```

React提供的Context API（Application Programming Interface）就是解决这个问题的标准方案。Context允许数据跨越组件层级直接传递，中间组件不需要感知这些数据的存在。

```tsx
// 创建Context
const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {},
});

// 顶层Provider提供数据
const App = () => {
  const [theme, setTheme] = useState('light');
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  const themeValue = useMemo(() => ({ theme, toggleTheme }), [theme]);

  return (
    <ThemeContext.Provider value={themeValue}>
      <HomeScreen />
    </ThemeContext.Provider>
  );
};

// 中间层组件，完全不需要感知theme的存在
const HomeScreen = () => {
  return (
    <View>
      <Header />
      <Content />
      <ThemedButton />
    </View>
  );
};

// 深层子组件直接消费，无需逐层传递
const ThemedButton = () => {
  const { theme, toggleTheme } = useContext(ThemeContext);
  const isDark = theme === 'dark';
  return (
    <TouchableOpacity
      onPress={toggleTheme}
      style={{ backgroundColor: isDark ? '#333' : '#fff' }}
    >
      <Text style={{ color: isDark ? '#fff' : '#000' }}>
        切换主题
      </Text>
    </TouchableOpacity>
  );
};
```

Context的工作原理可以用下图理解：

```
┌──────────────────────────────────────────┐
│  ThemeContext.Provider (顶层提供数据)       │
│  ┌──────────────────────────────────┐    │
│  │  HomeScreen (中间层，不需要theme)   │   │
│  │  ┌────────────────────────────┐  │    │
│  │  │  Content (中间层)           │  │    │
│  │  │  ┌──────────────────────┐  │  │    │
│  │  │  │  ThemedButton (消费) │  │  │    │
│  │  │  │  useContext 直接获取 │  │  │    │
│  │  │  └──────────────────────┘  │  │    │
│  │  └────────────────────────────┘  │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
        Context跨越中间层直接传递数据
```

注意上面的代码中，`themeValue`使用了`useMemo`包裹，这很重要。如果不用`useMemo`，每次Provider组件渲染时都会创建一个新的`{ theme, toggleTheme }`对象，即使`theme`没变，所有消费Context的组件都会重新渲染。

但Context不是银弹。它适合全局且低频变化的数据，比如主题、语言、用户信息。如果你的数据高频变化，Context值每次更新都会导致所有消费组件重新渲染，这时候需要考虑状态管理库如Zustand或Redux Toolkit。

### 4.4.4 兄弟组件通信实现方式

兄弟组件之间没有直接的Props关系，无法直接通信。标准做法是**状态提升**：把共享状态放到共同的父组件中，两个兄弟组件各自通过Props和回调与父组件通信。

```tsx
// 父组件管理共享状态
const SearchPage = () => {
  const [keyword, setKeyword] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  return (
    <View>
      <SearchInput value={keyword} onSearch={setKeyword} />
      <SearchResult keyword={keyword} />
    </View>
  );
};

// 兄弟组件A：搜索输入
const SearchInput = ({ value, onSearch }) => (
  <TextInput
    value={value}
    onChangeText={onSearch}
    placeholder="输入搜索关键词"
    style={styles.input}
  />
);

// 兄弟组件B：搜索结果
const SearchResult = ({ keyword }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (keyword.trim()) {
      setLoading(true);
      searchAPI(keyword).then(res => {
        setResults(res);
        setLoading(false);
      });
    } else {
      setResults([]);
    }
  }, [keyword]);

  if (loading) return <Text>搜索中...</Text>;
  return (
    <FlatList
      data={results}
      renderItem={({ item }) => <Text>{item.name}</Text>}
      ListEmptyComponent={<Text>暂无结果</Text>}
    />
  );
};
```

数据流向：`SearchInput`输入关键词 → 通过`onSearch`回调更新父组件的`keyword` → 父组件把新`keyword`传给`SearchResult` → `SearchResult`根据新关键词发起搜索请求。两个兄弟组件通过父组件间接通信，数据流清晰可追踪。

状态提升适用于兄弟关系简单的场景。如果兄弟组件层级很深，或者共同父组件离得很远，状态提升会导致父组件承担过多的状态管理责任。这时候更适合用Context或全局状态管理方案。

### 4.4.5 简易跨页面临时通信方案

跨页面通信在RN中是个常见需求，比如从商品页跳到订单页后需要通知订单页刷新数据，或者从编辑页返回列表页后需要通知列表页更新。如果用了React Navigation（下一章会详细讲），可以使用导航参数或事件系统。但如果场景简单，也可以用EventEmitter实现轻量级方案：

```tsx
// utils/eventBus.ts
type Listener = (data?: any) => void;
const listeners: Record<string, Listener[]> = {};

export const eventBus = {
  emit(event: string, data?: any) {
    (listeners[event] || []).forEach(fn => fn(data));
  },
  on(event: string, fn: Listener) {
    (listeners[event] = listeners[event] || []).push(fn);
    return () => {
      listeners[event] = listeners[event].filter(f => f !== fn);
    };
  },
  off(event: string, fn?: Listener) {
    if (fn) {
      listeners[event] = (listeners[event] || []).filter(f => f !== fn);
    } else {
      delete listeners[event];
    }
  },
};
```

```tsx
// 页面A：创建订单后发送事件
import { eventBus } from '@/utils/eventBus';

const CreateOrderPage = () => {
  const handleSubmit = async () => {
    await createOrderAPI(orderData);
    eventBus.emit('order:created', { orderId: newOrder.id });
    navigation.goBack();
  };
  return <Button title="提交订单" onPress={handleSubmit} />;
};
```

```tsx
// 页面B：监听订单创建事件并刷新
import { eventBus } from '@/utils/eventBus';

const OrderListPage = () => {
  const [orders, setOrders] = useState([]);

  const loadOrders = useCallback(() => {
    fetchOrders().then(setOrders);
  }, []);

  useEffect(() => {
    loadOrders();
    // 监听订单创建事件
    const unsubscribe = eventBus.on('order:created', () => {
      loadOrders(); // 刷新订单列表
    });
    return unsubscribe; // 组件卸载时取消监听
  }, [loadOrders]);

  return <FlatList data={orders} renderItem={OrderItemRenderer} />;
};
```

> EventEmitter简单好用但要注意内存泄漏风险。组件卸载时务必取消监听，否则会导致已卸载组件被重复调用setState而报错。上面的代码中useEffect的cleanup函数返回了`unsubscribe`，就是为了确保组件卸载时移除监听器。

EventEmitter适合简单的跨页面通知场景。如果项目规模较大，通信场景复杂，建议使用更完善的方案，比如React Navigation的navigation events、或者直接引入Zustand这种轻量状态管理库来做全局状态共享。

## 4.5 核心Hooks原理与实战精讲

### 4.5.1 useEffect副作用与生命周期替代

useEffect是函数组件中处理副作用的核武器。副作用包括：网络请求、定时器、事件监听、DOM（Document Object Model）操作、日志记录等。在类组件中这些通过生命周期方法处理，在函数组件中统一用useEffect搞定。

useEffect的执行机制可以用这张图理解：

```
组件首次渲染
    ↓
useEffect执行（相当于 componentDidMount）
    ↓
State或Props变化，组件重新渲染
    ↓
先执行上一次的cleanup函数（相当于 componentWillUnmount之前的清理）
    ↓
再执行新的useEffect（相当于 componentDidUpdate）
    ↓
...
    ↓
组件卸载
    ↓
执行最后一次cleanup函数（相当于 componentWillUnmount）
```

三种使用模式，对应不同的执行时机：

```tsx
// 模式一：每次渲染都执行（慎用，容易导致无限循环）
useEffect(() => {
  console.log('每次渲染都执行');
});

// 模式二：仅首次挂载时执行
useEffect(() => {
  console.log('仅挂载时执行');
  loadInitialData();
  return () => {
    console.log('组件卸载时执行清理');
  };
}, []); // 空依赖数组

// 模式三：特定依赖变化时执行
useEffect(() => {
  console.log('keyword变化时执行');
  searchAPI(keyword);
  return () => {
    // 清除上一次的请求结果（比如取消请求）
    cancelRequest();
  };
}, [keyword]); // 依赖数组
```

最经典的坑就在依赖数组。忘记加依赖会导致闭包陷阱——useEffect内部访问到的是旧值。加太多依赖又会导致频繁执行。怕浪猫的原则是：**useEffect内部用到的所有外部变量，都应该出现在依赖数组中**。如果加了某个依赖导致频繁执行，那说明你需要重新审视这个effect的设计是否合理。

```tsx
// 反面教材：遗漏依赖导致闭包陷阱
const [page, setPage] = useState(1);
const [keyword, setKeyword] = useState('');

useEffect(() => {
  // 这里page永远是1，因为没加到依赖数组
  // 当page变成2后，这个effect不会重新执行
  // 即使因为keyword变化重新执行了，page也还是旧值1
  searchAPI(keyword, page);
}, [keyword]); // 缺少page

// 正确做法：所有用到的外部变量都加到依赖数组
useEffect(() => {
  searchAPI(keyword, page);
}, [keyword, page]);
```

cleanup函数也是容易被忽略的部分。如果你在useEffect中设置了定时器或事件监听，必须在cleanup中清除。不清除的后果是：组件卸载后定时器还在运行，继续操作已卸载组件的State，React会报出"Can't perform a React state update on an unmounted component"的警告。

```tsx
useEffect(() => {
  const timer = setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);
  return () => clearInterval(timer); // 清除定时器
}, []);

useEffect(() => {
  const subscription = someEventBus.subscribe('data', handler);
  return () => subscription.unsubscribe(); // 取消订阅
}, []);
```

> 忘记cleanup是RN内存泄漏的头号杀手。组件卸载了但定时器还在跑，持续操作已卸载组件的State，控制台直接一片红字。养成习惯：每次写useEffect，先想好cleanup函数怎么写。

### 4.5.2 useRef节点获取与变量持久化

useRef有两个核心用途：获取组件实例引用和保存可变值。它和useState最大的区别是：修改ref.current不会触发重新渲染。这使得useRef非常适合存储那些"需要保持但不影响UI"的数据。

用途一：获取TextInput引用，实现自动聚焦和输入框切换。

```tsx
const LoginScreen = () => {
  const passwordRef = useRef<TextInput>(null);

  return (
    <View>
      <TextInput
        placeholder="用户名"
        returnKeyType="next"
        onSubmitEditing={() => passwordRef.current?.focus()}
      />
      <TextInput ref={passwordRef} placeholder="密码" secureTextEntry />
    </View>
  );
};
```

用户在用户名输入框点击键盘上的"下一步"时，自动聚焦到密码输入框。这种交互体验比让用户手动点击密码框好得多。

用途二：保存不触发渲染的可变值，比如定时器ID、请求取消令牌等。

```tsx
const TimerComponent = () => {
  const [count, setCount] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const start = () => {
    timerRef.current = setInterval(() => {
      setCount(prev => prev + 1);
    }, 1000);
  };

  const stop = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = undefined;
    }
  };

  useEffect(() => {
    return () => stop(); // 组件卸载时清除定时器
  }, []);

  return (
    <View>
      <Text>{count}</Text>
      <Button title="开始" onPress={start} />
      <Button title="停止" onPress={stop} />
    </View>
  );
};
```

为什么不用useState存timer ID？因为timer ID只是一个操作句柄，它变化不需要触发重新渲染。如果用useState，每次设置和清除定时器都会触发不必要的渲染。useRef保存的值在整个组件生命周期内保持不变，修改它不会触发任何渲染，这正是我们想要的。

### 4.5.3 useMemo计算属性缓存优化

useMemo用于缓存计算结果，避免每次渲染都重新计算。当某个计算逻辑开销较大时，useMemo能显著提升性能。它的本质是"用空间换时间"——缓存上一次的计算结果，当依赖项没变时直接复用。

```tsx
const ProductList = ({ products, filterKeyword, sortBy }) => {
  // 无优化：每次渲染都重新过滤和排序
  // const filtered = products
  //   .filter(p => p.name.includes(filterKeyword))
  //   .sort((a, b) => a[sortBy] - b[sortBy]);

  // 优化：只在依赖变化时重新计算
  const filtered = useMemo(() => {
    return products
      .filter(p => p.name.includes(filterKeyword))
      .sort((a, b) => {
        if (sortBy === 'price') return a.price - b.price;
        if (sortBy === 'sales') return b.sales - a.sales;
        return 0;
      });
  }, [products, filterKeyword, sortBy]);

  return (
    <FlatList
      data={filtered}
      renderItem={({ item }) => <ProductCard product={item} />}
    />
  );
};
```

useMemo的工作原理：

```
渲染1: products=[...], filterKeyword="手机", sortBy="price"
    → 执行过滤排序 → 缓存结果result1 → 使用result1渲染

渲染2: 某个不相关的State变化导致重新渲染
    → products不变, filterKeyword不变, sortBy不变
    → 跳过计算 → 直接使用缓存的result1 → 节省计算时间

渲染3: filterKeyword变为"电脑"
    → 依赖变化 → 重新执行过滤排序 → 缓存result2 → 使用result2渲染

渲染4: sortBy变为"sales"
    → 依赖变化 → 重新执行过滤排序 → 缓存result3 → 使用result3渲染
```

但useMemo本身也有开销（比较依赖项 + 缓存管理），所以不要滥用。对于简单的计算（比如基本的加减乘除、简单的属性访问），useMemo的开销可能比不用还大。只有当计算确实昂贵时才使用，比如大数据量的过滤排序、复杂的日期格式化、昂贵的JSON解析等。

> 性能优化的第一条原则是：不要过早优化。先写正确的代码，遇到性能瓶颈时再优化。useMemo是手术刀，不是保健品。

### 4.5.4 useCallback函数缓存性能优化

useCallback和useMemo是亲兄弟。useMemo缓存的是计算结果，useCallback缓存的是函数引用。它的主要使用场景是：当函数作为Props传给子组件时，避免父组件每次渲染都创建新函数导致子组件不必要的重新渲染。

```tsx
// 不用useCallback的问题
const Parent = () => {
  const [count, setCount] = useState(0);
  const [text, setText] = useState('');

  // 每次渲染都创建新函数引用
  const handlePress = () => {
    console.log('pressed');
  };

  return (
    <View>
      <Text>{count}</Text>
      <TextInput value={text} onChangeText={setText} />
      {/* 即使text变化导致Parent重新渲染，Child也会因为handlePress是新函数而重新渲染 */}
      <Child onPress={handlePress} />
    </View>
  );
};

// 用useCallback优化
const Parent = () => {
  const [count, setCount] = useState(0);
  const [text, setText] = useState('');

  const handlePress = useCallback(() => {
    console.log('pressed');
  }, []); // 空依赖，函数引用永远不变

  return (
    <View>
      <Text>{count}</Text>
      <TextInput value={text} onChangeText={setText} />
      {/* text变化导致Parent重新渲染，但handlePress引用没变，Child不会重新渲染 */}
      <Child onPress={handlePress} />
    </View>
  );
};

// 子组件必须用React.memo包裹，useCallback才能生效
const Child = React.memo(({ onPress }) => {
  console.log('Child渲染了');
  return <TouchableOpacity onPress={onPress}><Text>按钮</Text></TouchableOpacity>;
});
```

useCallback必须配合`React.memo`使用才有意义。如果子组件没有被`React.memo`包裹，即使父组件传了相同的函数引用，子组件依然会重新渲染。因为函数组件每次渲染都会重新执行函数体，`React.memo`的作用就是通过浅比较Props来跳过不必要的函数执行。

当回调函数依赖某些State时，需要把这些State加入依赖数组：

```tsx
const handleAddToCart = useCallback((product) => {
  setCart(prev => [...prev, product]);
  showToast(`${product.name}已加入购物车`);
}, []); // setCart是稳定的，不需要加入依赖
```

### 4.5.5 Hooks执行规则与常见坑点

Hooks有两条铁律，违反任何一条都会导致难以排查的bug：

**规则一：只在顶层调用Hooks。**不能在循环、条件语句或嵌套函数中调用Hooks。React内部通过链表来管理Hooks的调用顺序，如果顺序不一致，会导致状态错乱。

```tsx
// 反面教材：在条件语句中调用Hook
const Component = ({ condition }) => {
  if (condition) {
    const [data, setData] = useState(null); // 绝对禁止！
  }
  const [count, setCount] = useState(0);
  // ...
};

// 正确做法：把条件放到Hook内部
const Component = ({ condition }) => {
  const [data, setData] = useState(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (condition) {
      loadData().then(setData);
    }
  }, [condition]);
  // ...
};
```

为什么不能在条件语句中调用Hook？因为React依靠调用顺序来对应每个Hook的状态。第一次渲染时按顺序调用了`useState(1)`、`useState(2)`、`useEffect(3)`，React内部记录了三个Hook的顺序。如果第二次渲染时条件不满足导致第一个`useState`没有执行，React会以为第二个`useState`是第一个，状态全部对不上号。

**规则二：只在React函数中调用Hooks。**只能在函数组件或自定义Hooks中调用，不能在普通JS函数中调用。

```tsx
// 反面教材：在普通函数中调用Hook
const fetchData = () => {
  const [loading, setLoading] = useState(false); // 绝对禁止！
  setLoading(true);
  // ...
};

// 正确做法：封装成自定义Hook（以use开头命名）
const useFetchData = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  // ...
  return { loading, data, fetchData };
};
```

> Hooks的调用顺序就像楼层号，第一次渲染时1楼useState、2楼useEffect、3楼useState。如果第二次渲染时1楼变成了useEffect，React会以为2楼还是之前的useState，状态全部对不上号。

常见的Hooks报错信息及原因：

| 报错信息 | 原因 | 解决方案 |
|---------|------|---------|
| Rendered more hooks than during the previous render | 条件语句中调用了Hook | 把Hook移到顶层 |
| Invalid hook call | 在非组件函数中调用了Hook | 确保只在组件或自定义Hook中调用 |
| Maximum update depth exceeded | useEffect中无限更新State | 检查依赖数组是否正确 |

## 4.6 自定义Hooks与组件复用实战

### 4.6.1 自定义Hooks设计规范与思路

自定义Hooks是RN开发中最高级的复用手段。当你发现自己在多个组件中写重复的逻辑时，就该考虑抽取自定义Hook了。自定义Hook的本质就是把组件中的状态逻辑抽离出来，封装成可复用的函数。

自定义Hook的设计规范：

命名必须以`use`开头，这是React识别Hook的标记，也是lint规则的强制要求。比如`useLoading`、`useFetch`、`useLocalStorage`、`usePermission`。如果不用`use`开头，React的lint插件无法检测到这是一个Hook，就不会做规则校验，容易违反Hook规则。

返回值推荐用对象形式而非数组，这样调用方可以按需解构，不用记住顺序：

```tsx
// 推荐的对象返回形式
const useFetch = (url: string) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ...请求逻辑

  return { data, loading, error, refetch };
};

// 调用方按需解构，清晰明了
const { data, loading } = useFetch('/api/users');
const { data: products, error } = useFetch('/api/products');
```

设计自定义Hook的核心思路是**关注点分离**：把状态逻辑从UI中抽离出来，组件只负责展示，Hook只负责逻辑。这样逻辑可以跨组件复用，UI也可以独立替换。比如同一个`usePagination`Hook，可以配合FlatList使用，也可以配合ScrollView使用，UI怎么变都不影响分页逻辑。

### 4.6.2 通用加载状态Hook封装

加载状态是几乎所有页面都需要的功能。手动管理`loading`状态、错误处理、重试逻辑，在每个页面都要写一遍，既冗余又容易遗漏。封装一个通用的加载Hook可以一劳永逸。

```tsx
// hooks/useLoading.ts
import { useState, useCallback } from 'react';

interface UseLoadingResult<T> {
  data: T | undefined;
  loading: boolean;
  error: string | null;
  run: (task: () => Promise<T>) => Promise<T>;
  setData: (data: T) => void;
  reset: () => void;
}

export const useLoading = <T>(initialData?: T): UseLoadingResult<T> => {
  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (task: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await task();
      setData(result);
      return result;
    } catch (e) {
      const msg = (e as Error).message || '请求失败';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(initialData);
    setLoading(false);
    setError(null);
  }, [initialData]);

  return { data, loading, error, run, setData, reset };
};
```

```tsx
// 使用示例：订单列表页
const OrderListPage = () => {
  const { data: orders, loading, error, run } = useLoading<Order[]>();

  useEffect(() => {
    run(() => fetchOrders());
  }, [run]);

  if (loading) return <LoadingView text="加载中..." />;
  if (error) return (
    <ErrorView
      message={error}
      onRetry={() => run(() => fetchOrders())}
    />
  );

  return (
    <FlatList
      data={orders}
      renderItem={({ item }) => <OrderItem data={item} />}
      ListEmptyComponent={<EmptyView text="暂无订单" />}
    />
  );
};
```

整个页面的加载逻辑被压缩到三行代码：调`run`、判`loading`、判`error`。干净利落，任何页面都能直接复用。而且`run`函数支持任意异步任务，不绑定具体的接口请求，灵活性极高。

### 4.6.3 本地存储持久化Hook封装

RN中使用AsyncStorage做本地持久化存储。原生的AsyncStorage API是异步的，使用起来需要手动处理加载状态和JSON（JavaScript Object Notation）序列化。封装成Hook后，使用体验可以像useState一样简单。

```tsx
// hooks/useStorage.ts
import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const useStorage = <T>(
  key: string,
  initialValue: T
) => {
  const [value, setValue] = useState<T>(initialValue);
  const [loaded, setLoaded] = useState(false);

  // 初始化时从AsyncStorage加载
  useEffect(() => {
    AsyncStorage.getItem(key)
      .then(stored => {
        if (stored !== null) {
          setValue(JSON.parse(stored));
        }
      })
      .catch(e => console.warn('Storage读取失败:', e))
      .finally(() => setLoaded(true));
  }, [key]);

  // 更新值并同步到AsyncStorage
  const update = useCallback(
    (newValue: T) => {
      setValue(newValue);
      AsyncStorage.setItem(key, JSON.stringify(newValue)).catch(e =>
        console.warn('Storage写入失败:', e)
      );
    },
    [key]
  );

  // 删除值
  const remove = useCallback(() => {
    setValue(initialValue);
    AsyncStorage.removeItem(key);
  }, [key, initialValue]);

  return { value, update, remove, loaded };
};
```

```tsx
// 使用示例：记住用户搜索历史
const SearchPage = () => {
  const { value: history, update: setHistory, loaded } = useStorage(
    'search_history',
    [] as string[]
  );

  const handleSearch = (keyword: string) => {
    const newHistory = [
      keyword,
      ...history.filter(h => h !== keyword),
    ].slice(0, 10); // 最多保留10条
    setHistory(newHistory);
  };

  const clearHistory = () => setHistory([]);

  if (!loaded) return <LoadingView />;
  return (
    <View>
      {history.length > 0 ? (
        history.map((h, i) => (
          <TouchableOpacity key={i} onPress={() => handleSearch(h)}>
            <Text>{h}</Text>
          </TouchableOpacity>
        ))
      ) : (
        <Text>暂无搜索记录</Text>
      )}
    </View>
  );
};
```

> 好的Hook封装就像好的API设计：调用方不需要知道内部实现，只需要知道输入和输出。useStorage把AsyncStorage的异步读写、JSON序列化、加载状态管理全部封装在内部，调用方只管用就行。

### 4.6.4 接口请求通用Hook封装

接口请求是业务开发中最频繁的操作。一个完善的请求Hook应该具备：自动请求、手动触发、依赖变化重新请求、错误处理等能力。这里封装一个实用版本，覆盖日常80%的请求场景：

```tsx
// hooks/useRequest.ts
interface UseRequestOptions<T> {
  manual?: boolean;           // 是否手动触发，默认false
  deps?: any[];               // 依赖项，变化时重新请求
  initialData?: T;            // 初始数据
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export const useRequest = <T>(
  service: () => Promise<T>,
  options: UseRequestOptions<T> = {}
) => {
  const {
    manual = false,
    deps = [],
    initialData,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(!manual);
  const [error, setError] = useState<Error>();

  const run = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try {
      const result = await service();
      setData(result);
      onSuccess?.(result);
      return result;
    } catch (e) {
      setError(e as Error);
      onError?.(e as Error);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [service]);

  useEffect(() => {
    if (!manual) run();
  }, [manual, ...deps]);

  const refresh = useCallback(() => run(), [run]);

  return { data, loading, error, run, refresh, setData };
};
```

```tsx
// 自动请求示例：用户详情页
const UserDetailPage = ({ userId }) => {
  const { data: user, loading } = useRequest(
    () => fetchUserDetail(userId),
    { deps: [userId] } // userId变化时自动重新请求
  );

  if (loading) return <LoadingView />;
  if (!user) return <EmptyView />;
  return <UserInfoCard user={user} />;
};

// 手动请求示例：表单提交
const EditProfilePage = () => {
  const [formData, setFormData] = useState({ name: '', bio: '' });

  const { run: submit, loading: submitting } = useRequest(
    () => updateProfileAPI(formData),
    {
      manual: true,
      onSuccess: () => {
        showToast('保存成功');
        navigation.goBack();
      },
      onError: (e) => showToast(e.message),
    }
  );

  return (
    <View>
      <TextInput value={formData.name} onChangeText={v => setFormData({...formData, name: v})} />
      <TextInput value={formData.bio} onChangeText={v => setFormData({...formData, bio: v})} />
      <Button title="保存" onPress={submit} loading={submitting} />
    </View>
  );
};
```

`manual`模式适合表单提交、删除等用户主动触发的操作；自动模式适合页面加载时的数据获取。`deps`依赖数组让请求参数变化时自动重新请求，省去了手动管理请求时机的麻烦。`refresh`函数可以在任何地方调用来刷新数据，比如下拉刷新时调用。

### 4.6.5 业务通用Hook沉淀与复用

在真实项目中，除了通用的基础Hook，还会沉淀大量业务相关的Hook。这些Hook封装了特定业务领域的逻辑，是团队技术资产的重要组成部分。随着项目迭代，这些Hook不断打磨优化，成为项目最宝贵的代码资产。

一个典型的业务Hook沉淀清单：

| Hook名称 | 功能描述 | 使用场景 |
|---------|---------|---------|
| useAuth | 用户登录状态管理 | 登录拦截、权限判断、自动登录 |
| useCart | 购物车数据管理 | 加购、数量修改、选中状态、总价计算 |
| useLocation | 地理位置获取与缓存 | 附近商家、配送地址、地图导航 |
| usePermission | 权限请求与判断 | 相机、相册、定位权限请求 |
| usePagination | 分页列表数据管理 | 商品列表、订单列表、消息列表 |
| useTheme | 主题切换与样式获取 | 暗黑模式、多主题适配 |

以`usePagination`为例，这是几乎所有列表页面都需要的能力。手动管理分页逻辑容易出错：页码递增、数据合并、是否还有更多、下拉刷新重置等，每个环节都有坑。封装成Hook后，页面代码可以极其简洁：

```tsx
// hooks/usePagination.ts
interface PaginationResult<T> {
  list: T[];
  loading: boolean;
  refreshing: boolean;
  hasMore: boolean;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
}

export const usePagination = <T>(
  fetchFn: (page: number, size: number) => Promise<{ list: T[]; total: number }>,
  pageSize = 10
): PaginationResult<T> => {
  const [list, setList] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const hasMore = list.length < total;

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setPage(1);
    try {
      const res = await fetchFn(1, pageSize);
      setList(res.list);
      setTotal(res.total);
    } catch (e) {
      console.warn('刷新失败:', e);
    } finally {
      setRefreshing(false);
    }
  }, [fetchFn, pageSize]);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    const nextPage = page + 1;
    try {
      const res = await fetchFn(nextPage, pageSize);
      setList(prev => [...prev, ...res.list]);
      setPage(nextPage);
      setTotal(res.total);
    } catch (e) {
      console.warn('加载更多失败:', e);
    } finally {
      setLoading(false);
    }
  }, [fetchFn, pageSize, page, loading, hasMore]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { list, loading, refreshing, hasMore, refresh, loadMore };
};
```

```tsx
// 页面中使用：几行代码搞定分页列表
const ProductListPage = () => {
  const { list, loading, refreshing, hasMore, refresh, loadMore } = usePagination(
    (page, size) => fetchProducts({ page, size })
  );

  return (
    <FlatList
      data={list}
      renderItem={({ item }) => <ProductCard product={item} />}
      onRefresh={refresh}
      refreshing={refreshing}
      onEndReached={loadMore}
      onEndReachedThreshold={0.3}
      ListFooterComponent={
        loading ? <Text style={{ textAlign: 'center' }}>加载中...</Text> :
        !hasMore ? <Text style={{ textAlign: 'center' }}>没有更多了</Text> : null
      }
    />
  );
};
```

> 自定义Hook的沉淀过程，就是团队能力积累的过程。每解决一个重复问题就封装一个Hook，半年后你的项目开发效率会比从零开始快一倍。怕浪猫建议把通用Hook抽成独立的npm包或monorepo子包，让多个项目共享同一套基础设施。

## 收藏模板：RN组件通信方案速查表

怕浪猫把本章所有通信方案整理成一张速查表，建议收藏备用：

| 通信场景 | 推荐方案 | 适用条件 | 复杂度 | 注意事项 |
|---------|---------|---------|-------|---------|
| 父传子 | Props传值 | 直接父子关系 | 低 | Props只读，不可修改 |
| 子传父 | 回调函数Props | 直接父子关系 | 低 | 回调命名用on前缀 |
| 跨层级 | Context API | 祖先到后代 | 中 | 适合低频变化的全局数据 |
| 兄弟组件 | 状态提升到共同父组件 | 有共同父组件 | 中 | 父组件不宜承载太多状态 |
| 跨页面 | EventEmitter / 导航参数 | 非直接嵌套关系 | 中 | 注意卸载时取消监听 |
| 全局状态 | Zustand / Redux Toolkit | 大规模复杂状态 | 高 | 评估是否真的需要 |

## 怕浪猫说

组件化开发是RN从"能跑"到"能维护"的分水岭。这章内容覆盖了组件设计、Props传参、State管理、组件通信和Hooks实战，每一个知识点都是你在真实项目中每天都要用的。

怕浪猫在多年开发中总结了一条经验：**好的组件设计决定了项目的上限，好的状态管理决定了项目的下限**。Hooks不是越高深越好，而是越合适越好。useMemo和useCallback不是万能药，只有在真正有性能瓶颈时才需要用。自定义Hook的封装也不必一步到位，先写重复代码，等模式浮现出来再抽取，避免过度设计。

如果你觉得这篇文章对你有帮助，点个收藏，写代码的时候翻出来看看。有什么问题或者不同见解，评论区见，怕浪猫会一条条看。

下一篇我们进入RN路由导航的世界——React Navigation企业级路由导航开发。路由是多页面应用的骨架，从栈路由到Tab导航，从嵌套路由到权限拦截，手把手带你搭建企业级路由架构。

系列进度 4/16
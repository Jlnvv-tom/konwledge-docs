# 第16章 综合项目实战：全栈APP开发与项目复盘

试了3个完整项目才搞明白，全栈APP开发最难的不是写代码，而是在需求、架构、性能之间找到那个平衡点。

我是怕浪猫，这是React Native（RN）系列的第16章，也是最后一章。前面15章我们把RN的组件、导航、网络、状态管理、性能优化、工程化都拆了个遍。今天，怕浪猫把这些知识点全部串起来，从零开始做一个完整的全栈APP——电商导购应用，走完从需求分析到上架发布的完整流程。

> 全栈开发不是"前端会写后端"，而是能独立完成一个产品的闭环：需求到架构、编码到上线、优化到复盘。

## 16.1 实战项目需求分析与架构设计

### 16.1.1 项目功能需求与业务场景梳理

我们要做一个"好物导购"APP，核心业务场景是商品浏览、分类筛选、详情查看、用户登录和个人中心管理。

功能需求清单：

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| 用户体系 | 手机号登录、JWT鉴权、个人资料 | P0 |
| 商品浏览 | 首页推荐、分类导航、搜索 | P0 |
| 商品详情 | 图文详情、规格选择、收藏 | P0 |
| 购物流程 | 加入购物车、下单结算 | P1 |
| 个人中心 | 订单管理、收货地址、设置 | P1 |
| 内容运营 | Banner轮播、活动专题 | P2 |

> 需求分析的核心不是"做什么"，而是"先做什么"。P0功能决定产品能不能用，P1决定好不好用，P2决定精不精致。怕浪猫的经验是：P0砍掉一半功能，P1推迟到V2版本，P2看数据决定。

### 16.1.2 技术栈选型与版本适配确认

技术栈选型直接决定开发效率和后期维护成本。

| 层面 | 技术选型 | 版本 | 选型理由 |
|------|---------|------|---------|
| 客户端框架 | React Native | 0.75 | 新架构Fabric启用 |
| 开发语言 | TypeScript | 5.4 | 类型安全、IDE提示 |
| 路由方案 | React Navigation | 6.x | 社区标准、生态成熟 |
| 状态管理 | Zustand | 4.5 | 轻量、无模板代码 |
| 网络请求 | Axios + TanStack Query | 5.x | 缓存策略 + 请求取消 |
| UI组件库 | 自建组件库 | - | 定制性强、无版本绑定 |
| 后端框架 | Express + Prisma | 4.x / 5.x | TS友好、ORM灵活 |
| 数据库 | PostgreSQL | 16 | 关系型、JSON支持 |
| 缓存层 | Redis | 7.x | 会话管理、热点缓存 |
| 部署方案 | Docker + Nginx | - | 容器化、负载均衡 |

版本适配确认的关键：RN 0.75要求Node 18+，Prisma 5.x要求PostgreSQL 14+，React Navigation 6.x兼容RN 0.70+。这些约束在项目启动前必须确认。

> 技术选型有三个原则：一是选熟悉的，不选最新的；二是选生态好的，不选小众的；三是选能离开的，不选绑死的。怕浪猫见过太多项目因为选了冷门框架，最后招不到人维护。

### 16.1.3 客户端整体架构与目录设计

客户端架构遵循"分层+模块化"原则：

```
src/
├── components/        # 全局通用组件
│   ├── ui/           # 基础UI组件（Button、Input等）
│   └── business/     # 业务组件（ProductCard、OrderItem等）
├── screens/          # 页面组件
│   ├── home/         # 首页模块
│   ├── category/     # 分类模块
│   ├── detail/       # 详情模块
│   ├── auth/         # 登录模块
│   └── profile/      # 个人中心模块
├── navigation/       # 路由配置
├── stores/           # 状态管理
├── services/         # 网络请求
├── hooks/            # 自定义Hook
├── utils/            # 工具函数
├── types/            # 类型定义
├── constants/        # 常量枚举
├── theme/            # 主题样式
└── assets/           # 静态资源
```

> 目录设计的原则是"按功能分不按类型分"。不要建一个`components`目录把所有组件塞进去，而是每个功能模块自带自己的组件、hooks、types。全局只放真正跨模块复用的东西。这样模块内聚度高，删除一个功能模块只需要删一个文件夹。

### 16.1.4 后端接口与数据库结构设计

数据库核心表结构：

```sql
-- 用户表
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  phone VARCHAR(20) UNIQUE NOT NULL,
  nickname VARCHAR(50),
  avatar VARCHAR(500),
  status INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 商品表
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  subtitle VARCHAR(500),
  price DECIMAL(10,2) NOT NULL,
  original_price DECIMAL(10,2),
  images JSONB,
  category_id BIGINT REFERENCES categories(id),
  stock INT DEFAULT 0,
  sales INT DEFAULT 0,
  status INT DEFAULT 1
);
```

接口设计遵循RESTful规范：

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 登录 | POST | /api/auth/login | 手机号+验证码 |
| 商品列表 | GET | /api/products | 分页+筛选 |
| 商品详情 | GET | /api/products/:id | 含规格信息 |
| 分类树 | GET | /api/categories | 树形结构 |
| 收藏 | POST | /api/favorites | 需鉴权 |
| 用户信息 | GET | /api/user/profile | 需鉴权 |

### 16.1.5 项目开发计划与模块拆分

项目分4个迭代周期：

| 周期 | 时长 | 目标 | 交付物 |
|------|------|------|--------|
| Sprint 1 | 1周 | 工程搭建+登录流程 | 可运行的骨架APP |
| Sprint 2 | 2周 | 核心商品模块 | 首页+分类+详情 |
| Sprint 3 | 1周 | 个人中心+全栈联调 | 完整业务闭环 |
| Sprint 4 | 1周 | 优化+打包+上架 | 上线版本 |

> 项目管理怕浪猫只用一句话：每周五下午演示，不管做完没做完。倒逼自己拆细任务，宁可砍功能也不延期。这是小团队最高效的交付方式。

## 16.2 项目初始化与工程化配置落地

### 16.2.1 标准化RN项目初始化创建

```bash
npx react-native init GoodShop --template react-native-template-typescript
cd GoodShop
```

初始化后第一件事是确认Node版本和依赖版本：

```bash
node -v  # v18.x 或 v20.x
npx react-native doctor  # 环境检查
```

### 16.2.2 TS、路径别名、规范配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@components/*": ["components/*"],
      "@screens/*": ["screens/*"],
      "@services/*": ["services/*"]
    }
  }
}
```

babel.config.js中配置路径别名：

```js
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    ['module-resolver', {
      root: ['./src'],
      alias: {
        '@': './src',
        '@components': './src/components',
        '@screens': './src/screens',
      }
    }]
  ]
};
```

> 工程化配置有一个新手常犯的错误：路径别名配了但metro.config.js没配。结果TS不报错，但运行时找不到模块。记住：babel管编译时，metro管运行时，两个都要配。

### 16.2.3 路由体系与全局布局搭建

```tsx
// src/navigation/AppNavigator.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function HomeStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Detail" component={DetailScreen} />
      <Stack.Screen name="Search" component={SearchScreen} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator>
        <Tab.Screen name="HomeTab" component={HomeStack} options={{title: '首页'}} />
        <Tab.Screen name="Category" component={CategoryScreen} options={{title: '分类'}} />
        <Tab.Screen name="Profile" component={ProfileStack} options={{title: '我的'}} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
```

### 16.2.4 网络请求与全局工具类封装

```ts
// src/services/request.ts
import axios from 'axios';
import { tokenManager } from '../utils/token';

const instance = axios.create({
  baseURL: 'https://api.goodshop.com',
  timeout: 10000,
});

instance.interceptors.request.use(async (config) => {
  const token = await tokenManager.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      tokenManager.clear();
      // 跳转登录页
    }
    return Promise.reject(error);
  }
);

export default instance;
```

> 网络请求封装的核心不是Axios本身，而是拦截器。请求拦截器统一注入Token，响应拦截器统一处理错误码。这样业务层只关心成功逻辑，不需要每个接口都写错误处理。

### 16.2.5 全局状态与主题样式初始化

```ts
// src/stores/useUserStore.ts
import { create } from 'zustand';

interface UserState {
  userInfo: UserInfo | null;
  token: string | null;
  setUserInfo: (info: UserInfo) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  userInfo: null,
  token: null,
  setUserInfo: (info) => set({ userInfo: info, token: info.token }),
  logout: () => set({ userInfo: null, token: null }),
}));
```

主题配置：

```ts
// src/theme/index.ts
export const theme = {
  colors: {
    primary: '#FF6B35',
    background: '#F5F5F5',
    text: '#333333',
    textSecondary: '#999999',
    border: '#EEEEEE',
    white: '#FFFFFF',
  },
  spacing: { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 },
  fontSize: { caption: 12, body: 14, title: 16, header: 20 },
  radius: { sm: 4, md: 8, lg: 12 },
};
```

> Zustand比Redux的优势在于"没有模板代码"。定义一个store就是定义一个函数，不需要action、reducer、dispatch这些概念。对于中小型项目，Zustand的效率和可维护性远超Redux。

## 16.3 核心业务页面批量开发实战

### 16.3.1 启动页、引导页、登录页开发

启动页用react-native-bootsplash实现原生级体验：

```ts
// App.tsx
import BootSplash from 'react-native-bootsplash';

function App() {
  useEffect(() => {
    initApp().finally(() => {
      BootSplash.hide({ fade: true });
    });
  }, []);
  return <AppNavigator />;
}
```

登录页核心逻辑——手机号+验证码：

```tsx
// src/screens/auth/LoginScreen.tsx
const [phone, setPhone] = useState('');
const [code, setCode] = useState('');
const [countdown, setCountdown] = useState(0);

const handleSendCode = async () => {
  if (!/^1\d{10}$/.test(phone)) {
    Toast.show('请输入正确的手机号');
    return;
  }
  await sendSmsCode(phone);
  setCountdown(60);
  const timer = setInterval(() => {
    setCountdown((c) => {
      if (c <= 1) clearInterval(timer);
      return c - 1;
    });
  }, 1000);
};
```

> 登录页有个细节新手容易忽略：验证码倒计时要在组件卸载时清除定时器，否则切换页面后倒计时还在跑，切回来又创建一个，内存泄漏就这么来的。

### 16.3.2 首页核心业务模块搭建

首页由Banner轮播、金刚区入口、商品瀑布流三部分组成：

```tsx
// src/screens/home/HomeScreen.tsx
import { FlatList, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';

export default function HomeScreen({ navigation }) {
  const { data, refetch, isRefreshing } = useQuery({
    queryKey: ['products', 'home'],
    queryFn: () => productService.getList({ page: 1, recommend: true }),
  });

  const renderItem = ({ item }) => (
    <ProductCard
      product={item}
      onPress={() => navigation.navigate('Detail', { id: item.id })}
    />
  );

  return (
    <FlatList
      data={data?.list || []}
      renderItem={renderItem}
      numColumns={2}
      refreshControl={
        <RefreshControl refreshing={isRefreshing} onRefresh={refetch} />
      }
    />
  );
}
```

> TanStack Query（React Query）在网络请求层的优势是自动缓存和失效管理。首次加载商品列表后，切到详情页再返回，列表数据从缓存秒读，不重新请求。这在弱网环境下体验提升非常明显。

### 16.3.3 分类列表与筛选页面实现

分类页用左右联动布局——左侧一级分类，右侧二级分类+商品列表：

```tsx
// src/screens/category/CategoryScreen.tsx
const [activeId, setActiveId] = useState<number>(0);
const { data: categories } = useQuery({
  queryKey: ['categories'],
  queryFn: categoryService.getTree,
});

return (
  <View style={styles.container}>
    <ScrollView style={styles.leftPanel}>
      {categories?.map((cat) => (
        <CategoryItem
          key={cat.id}
          active={cat.id === activeId}
          onPress={() => setActiveId(cat.id)}
          name={cat.name}
        />
      ))}
    </ScrollView>
    <ScrollView style={styles.rightPanel}>
      <SubCategoryGrid
        list={categories?.find(c => c.id === activeId)?.children || []}
        onSelect={(subId) => navigation.navigate('ProductList', { categoryId: subId })}
      />
    </ScrollView>
  </View>
);
```

### 16.3.4 详情页复杂交互与布局开发

详情页是最复杂的页面——商品图轮播、规格选择、加入购物车、收藏功能。

```tsx
// src/screens/detail/DetailScreen.tsx
const { id } = useRoute().params;
const { data: product } = useQuery({
  queryKey: ['product', id],
  queryFn: () => productService.getDetail(id),
  enabled: !!id,
});

const [selectedSpec, setSelectedSpec] = useState<Spec | null>(null);
const [showSpecSheet, setShowSpecSheet] = useState(false);

const handleAddToCart = async () => {
  if (!selectedSpec) {
    setShowSpecSheet(true);
    return;
  }
  await cartService.add({ productId: id, specId: selectedSpec.id, qty: 1 });
  Toast.show('已加入购物车');
};
```

> 详情页的性能优化核心是"按需渲染"。商品图片用IntersectionObserver做懒加载，规格选择面板用Modal而非全屏页面，评价区域默认折叠只展示3条。这些细节决定了页面的首屏渲染速度。

### 16.3.5 个人中心与设置页面完善

```tsx
// src/screens/profile/ProfileScreen.tsx
const { userInfo, logout } = useUserStore();

const menuItems = [
  { icon: 'order', title: '我的订单', page: 'Orders' },
  { icon: 'address', title: '收货地址', page: 'Address' },
  { icon: 'favorite', title: '我的收藏', page: 'Favorites' },
  { icon: 'setting', title: '设置', page: 'Setting' },
];

export default function ProfileScreen() {
  if (!userInfo) {
    return <LoginGuide onLogin={() => navigation.navigate('Login')} />;
  }
  return (
    <View>
      <UserInfoHeader user={userInfo} />
      <MenuList items={menuItems} onSelect={(page) => navigation.navigate(page)} />
    </View>
  );
}
```

## 16.4 全栈接口联调与权限体系落地

### 16.4.1 后端业务接口批量开发

后端用Express + Prisma快速搭建：

```ts
// server/src/routes/product.routes.ts
import { Router } from 'express';
import { getProductList, getProductDetail } from '../controllers/product.controller';

const router = Router();
router.get('/products', getProductList);
router.get('/products/:id', getProductDetail);
export default router;
```

Prisma数据模型定义：

```prisma
model Product {
  id          BigInt    @id @default(autoincrement())
  title       String
  subtitle    String?
  price       Decimal
  images      Json?
  categoryId  BigInt
  stock       Int       @default(0)
  sales       Int       @default(0)
  status      Int       @default(1)
  category    Category  @relation(fields: [categoryId], references: [id])
}
```

### 16.4.2 客户端接口对接与数据渲染

客户端通过TanStack Query对接：

```ts
// src/services/product.service.ts
import request from './request';

export const productService = {
  getList: (params: ProductQuery) =>
    request.get('/products', { params }),
  getDetail: (id: string) =>
    request.get(`/products/${id}`),
  getRecommend: () =>
    request.get('/products/recommend'),
};
```

> 接口对接有一个原则叫"宽进严出"。接收参数时宽松——允许字符串传数字、允许空值有默认值。返回数据时严格——字段类型固定、空值显式返回null。这样前端对接不会被后端的严格校验卡住。


### 16.4.3 JWT登录鉴权全流程打通

JWT（JSON Web Token）登录鉴权流程：

```
客户端发送手机号+验证码 → 后端验证 → 生成JWT Token → 返回客户端
客户端存储Token → 后续请求Header携带Authorization: Bearer <token>
后端中间件验证Token → 解析用户ID → 注入req.user → 放行或拒绝
```

后端JWT中间件：

```ts
// server/src/middleware/auth.ts
import jwt from 'jsonwebtoken';

export function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ code: 401, msg: '未登录' });

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);
    req.userId = payload.userId;
    next();
  } catch {
    res.status(401).json({ code: 401, msg: 'Token失效' });
  }
}
```

客户端Token管理：

```ts
// src/utils/token.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export const tokenManager = {
  async getToken(): Promise<string | null> {
    return AsyncStorage.getItem('token');
  },
  async setToken(token: string): Promise<void> {
    await AsyncStorage.setItem('token', token);
  },
  async clear(): Promise<void> {
    await AsyncStorage.removeItem('token');
  },
};
```

> JWT鉴权有一个安全细节新手容易忽略：Token不要存全局变量里。App冷启动后全局变量会清空，用户每次打开都要重新登录。用AsyncStorage持久化存储，App启动时自动恢复登录态。

### 16.4.4 页面与按钮权限控制落地

权限控制分两个维度：页面级和按钮级。

```ts
// src/hooks/usePermission.ts
export function usePermission() {
  const { userInfo } = useUserStore();
  
  const canAccess = (page: string) => {
    const permissions = userInfo?.permissions || [];
    return permissions.includes(page);
  };

  const canAction = (action: string) => {
    const roles = userInfo?.roles || [];
    return roles.includes(action);
  };

  return { canAccess, canAction };
}
```

路由守卫拦截：

```tsx
// src/navigation/RouteGuard.tsx
function RouteGuard({ children, permission }: { children: ReactNode; permission?: string }) {
  const { canAccess } = usePermission();
  if (permission && !canAccess(permission)) {
    return <NoPermissionScreen />;
  }
  return <>{children}</>;
}
```

### 16.4.5 业务数据CRUD完整闭环实现

CRUD（Create Read Update Delete）完整闭环——以收藏功能为例：

```ts
// src/services/favorite.service.ts
export const favoriteService = {
  list: () => request.get('/favorites'),
  add: (productId: string) => request.post('/favorites', { productId }),
  remove: (id: string) => request.delete(`/favorites/${id}`),
  check: (productId: string) => request.get(`/favorites/check/${productId}`),
};
```

收藏按钮组件：

```tsx
function FavoriteButton({ productId }: { productId: string }) {
  const { data: isFavorited } = useQuery({
    queryKey: ['favorite', productId],
    queryFn: () => favoriteService.check(productId),
  });
  const toggle = useMutation({
    mutationFn: () => isFavorited ? favoriteService.remove(productId) : favoriteService.add(productId),
    onSuccess: () => queryClient.invalidateQueries(['favorite', productId]),
  });
  return <Button onPress={() => toggle.mutate()} title={isFavorited ? '已收藏' : '收藏'} />;
}
```

> CRUD闭环的标志是"增删改查"四个操作都有对应的UI反馈。点击收藏按钮→立即变状态→后台同步→失败回滚。这个流程用TanStack Query的mutation+乐观更新实现最优雅。

## 16.5 项目性能优化与BUG整体修复

### 16.5.1 页面渲染与列表性能优化

列表性能优化清单：

| 问题 | 方案 | 效果 |
|------|------|------|
| 列表卡顿 | getItemLayout固定高度 | 渲染速度提升60% |
| 图片加载慢 | FastImage + 预加载 | 首屏时间减少40% |
| 重渲染频繁 | React.memo + useCallback | 无效渲染减少80% |
| 滚动白屏 | removeClippedSubviews | 内存占用降低30% |
| 首屏白屏 | 预加载首屏数据 | 白屏时间从2s降到0.3s |

```tsx
// 优化后的商品列表
const renderItem = useCallback(({ item }: { item: Product }) => (
  <ProductCard product={item} onPress={handlePress} />
), []);

const getItemLayout = (_, index) => ({
  length: CARD_HEIGHT,
  offset: CARD_HEIGHT * index,
  index,
});

<FlatList
  data={products}
  renderItem={renderItem}
  getItemLayout={getItemLayout}
  removeClippedSubviews={true}
  maxToRenderPerBatch={8}
  windowSize={5}
/>
```

> 性能优化有个"28法则"：80%的性能问题来自20%的代码。先用React DevTools Profiler找到耗时最长的组件，集中优化那20%。不要盲目优化，每个优化都要有数据支撑。

### 16.5.2 内存泄漏与卡顿问题专项修复

常见内存泄漏场景：

```ts
// 错误：定时器未清理
useEffect(() => {
  const timer = setInterval(fetchData, 5000);
  // 忘记 return () => clearInterval(timer)
}, []);

// 正确：组件卸载时清理
useEffect(() => {
  const timer = setInterval(fetchData, 5000);
  return () => clearInterval(timer);
}, []);

// 错误：异步操作未取消
useEffect(() => {
  fetchData().then setData(data);
  // 组件卸载后还会执行setData
}, []);

// 正确：用AbortController取消
useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal }).then(setData);
  return () => controller.abort();
}, []);
```

> 内存泄漏排查工具怕浪猫推荐两个：Flipper的Memory面板看堆内存变化趋势，Chrome DevTools的Memory标签做Heap Snapshot对比。先拍一个快照，操作一轮再拍一个，对比增量就是泄漏点。

### 16.5.3 弱网、断网异常体验优化

弱网优化策略：

| 场景 | 策略 | 实现方式 |
|------|------|---------|
| 首次加载慢 | 骨架屏 | Skeleton占位组件 |
| 请求超时 | 重试机制 | Axios retry拦截器 |
| 断网 | 离线缓存 | AsyncStorage + 过期时间 |
| 弱网 | 降级图片 | 低清图→高清图渐进加载 |
| 重复请求 | 请求去重 | TanStack Query staleTime |

```ts
// 骨架屏组件
function ProductCardSkeleton() {
  return (
    <View style={styles.card}>
      <Skeleton width="100%" height={180} />
      <Skeleton width="80%" height={16} style={{ marginTop: 8 }} />
      <Skeleton width="40%" height={20} style={{ marginTop: 4 }} />
    </View>
  );
}
```

### 16.5.4 双端兼容性BUG统一适配

iOS和Android双端常见差异：

| 差异点 | iOS行为 | Android行为 | 解决方案 |
|--------|---------|-------------|---------|
| 安全区 | safe-area-inset | 状态栏高度 | react-native-safe-area-context |
| 滚动回弹 | bounces默认开启 | overScrollMode | 分别配置 |
| 输入框 | 键盘遮挡自动滚动 | 需手动处理 | KeyboardAvoidingView |
| 阴影 | shadowOffset | elevation | Platform.select |
| 字体 | San Francisco | Roboto | Platform.select |

```ts
const styles = StyleSheet.create({
  card: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 4,
      },
    }),
  },
});
```

> 双端适配有一个"黄金法则"：先做iOS再做Android。因为iOS的约束更严格，iOS能跑的代码在Android上通常没问题。反过来不行——Android能跑的在iOS上经常崩。

### 16.5.5 项目整体自测与体验打磨

自测清单（Checklist）：

| 维度 | 检查项 | 通过标准 |
|------|--------|---------|
| 功能 | 所有P0功能可正常使用 | 0个阻塞BUG |
| 性能 | 首屏渲染<1s，列表滚动60fps | 真机测试通过 |
| 兼容 | iOS 13+和Android 8+ | 覆盖95%+设备 |
| 网络 | 弱网、断网场景 | 有友好提示 |
| 安全 | Token存储、接口鉴权 | 无越权漏洞 |
| UI | 双端视觉一致性 | 设计走查通过 |

## 16.6 项目打包上线与全知识点复盘

### 16.6.1 双端正式包打包与内测校验

iOS打包流程：

```bash
# 1. 配置签名
cd ios && pod install
# 2. Archive
xcodebuild archive -scheme GoodShop -archivePath build/GoodShop.xcarchive
# 3. 导出IPA
xcodebuild -exportArchive -archivePath build/GoodShop.xcarchive \
  -exportOptionsPlist exportOptions.plist -exportPath build/
```

Android打包流程：

```bash
# 1. 生成签名密钥
keytool -genkey -v -keystore goodshop.keystore -alias goodshop \
  -keyalg RSA -keysize 2048 -validity 10000
# 2. 配置gradle签名
# 3. 打包
cd android && ./gradlew assembleRelease
```

> 打包最容易踩的坑是"Debug包能跑Release包崩溃"。原因通常是ProGuard混淆把反射调用的类名改了。解决方案是在proguard-rules.pro中保留反射使用的类。每次打包后先在真机上跑一遍Release包，确认没有崩溃。

### 16.6.2 应用商店上架提审与发布

上架清单：

| 平台 | 材料 | 审核时长 | 注意事项 |
|------|------|---------|---------|
| App Store | 截图、描述、隐私政策 | 1-3天 | 不能有测试账号提示 |
| Google Play | AAB包、内容分级 | 1-7天 | 需声明数据安全 |
| 国内安卓 | APK、软著证书 | 3-7天 | 需要软件著作权 |

> App Store审核被拒的三大原因：一是引导用户外部支付（比如跳转浏览器支付），二是隐私政策不完整（缺少数据收集说明），三是测试账号没删除（登录页有"测试账号:xxx"的提示）。这三点在提审前必须检查。

### 16.6.3 全书核心知识点体系复盘

全书16章知识点体系：

| 模块 | 章节 | 核心知识点 |
|------|------|-----------|
| 基础入门 | 1-2 | RN原理、环境搭建、JSX语法、组件体系 |
| UI开发 | 3-4 | 基础组件、样式系统、Flex布局、动画 |
| 导航路由 | 5 | Stack/Tab/Drawer、嵌套路由、路由守卫 |
| 原生能力 | 6 | 相机、定位、推送、生物识别 |
| 网络通信 | 7 | Axios封装、文件上传、WebSocket |
| 状态管理 | 8 | Zustand、Context、状态分层 |
| UI组件库 | 9 | 自建组件、主题系统、Dark Mode |
| 全栈后端 | 10 | Express、Prisma、PostgreSQL |
| 鉴权安全 | 11 | JWT、权限控制、数据加密 |
| 原生混合 | 12 | 原生模块、Bridge、JSI |
| 性能优化 | 13 | 渲染优化、内存管理、启动加速 |
| 工程化 | 14 | CI/CD、代码规范、自动化测试 |
| 打包发布 | 15 | 双端打包、热更新、灰度发布 |
| 综合实战 | 16 | 全栈APP、项目复盘 |

> 知识体系的本质是"点线面"。每章是知识点，模块是线，整个系列是面。学完之后，你应该能把这张表默写出来，并且每个知识点都能说出一句话的核心结论。这才是真正掌握了。

### 16.6.4 RN全栈开发者能力总结

一个合格的RN全栈开发者应该具备以下能力：

| 能力维度 | 具体要求 | 验证标准 |
|---------|---------|---------|
| RN开发 | 独立完成完整APP开发 | 能从零搭建项目 |
| 原生交互 | 理解Bridge/JSI原理 | 能编写原生模块 |
| 全栈能力 | 前后端独立开发 | 能设计API和数据库 |
| 性能优化 | 定位和解决性能问题 | 能用Profiler分析 |
| 工程化 | CI/CD、代码规范 | 能搭建自动化流程 |
| 上线发布 | 双端打包上架 | 能独立完成发布 |

### 16.6.5 后续进阶学习与技术拓展方向

| 方向 | 推荐技术 | 学习资源 |
|------|---------|---------|
| 跨端框架 | Flutter、Taro、uni-app | 官方文档+实战项目 |
| 新架构 | Fabric、TurboModules | RN官方RFC |
| 服务端 | Node.js进阶、微服务 | NestJS框架 |
| DevOps | K8s、监控告警 | 实战部署 |
| 前沿方向 | AI+RN、WebAssembly | 关注React Labs |

> 技术学习没有终点，但有方向。怕浪猫的建议是"T型人才"——在RN领域深入到能解决任何问题，同时横向扩展到后端、运维、设计等领域。深度让你不可替代，广度让你游刃有余。

## 系列完结语

16章内容，从RN的环境搭建到全栈APP上线，怕浪猫陪你走完了这条完整的技术链路。

这个系列的核心价值不在于教你写代码，而在于帮你建立"全栈思维"——从需求到架构、从编码到上线、从优化到复盘，每一步都能独立完成。这才是市场真正需要的人才。

后续怕浪猫会出更多系列内容，包括Flutter跨端开发、React性能优化实战、Node.js微服务架构等。关注怕浪猫，不错过更新。

**系列进度 16/16 — React Native系列完结**

**怕浪猫说**

写完这个系列最大的感触是：技术文章最怕的不是写得浅，而是写得"看似都懂实则没用"。怕浪猫尽量把每个知识点都落到代码上、落在场景里，让你看完能直接照着做。如果你跟着这个系列从第1章走到了第16章，你的RN全栈能力已经超过了80%的开发者。剩下的20%，靠实战项目去补。技术这条路，怕浪猫陪你走一段，但最终走下去的，是你自己。加油。

觉得这个系列有用？收藏起来，开发的时候翻出来照着写。你用RN做过最复杂的项目是什么？评论区聊聊。关注怕浪猫，后续更多系列内容持续更新。

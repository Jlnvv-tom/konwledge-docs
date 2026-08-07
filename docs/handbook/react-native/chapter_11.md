---
sidebar_position: 11
---

# 第11章 JWT登录鉴权与移动端权限系统开发

> 登录鉴权不是写个登录页那么简单，它是一整套从后端签发到前端存储、从请求拦截到路由守卫、从页面权限到按钮权限的安全闭环。任何一个环节出漏洞，整个系统形同虚设。

做过RN（React Native）移动端开发的同学应该都遇到过这样的场景：登录功能第一天就写完了，但接下来整整两周都在和各种鉴权问题搏斗。Token过期了页面不跳转、用户切后台再回来登录态丢失、多个页面同时请求401触发重复刷新、路由守卫时序不对导致白屏闪过、权限按钮该隐藏的没隐藏该禁用的没禁用。这些问题看似零散，实则都指向同一个根因：缺少系统性的登录鉴权架构设计。

更致命的是，很多团队把"登录"理解成"调一下登录接口存个Token"就完事了。等到业务跑起来，发现未登录用户能直接通过深链接进入受限页面、普通用户能通过手动改本地状态访问管理员页面、Token泄露后无法主动失效、退出登录后本地缓存还残留着上一个人的权限数据。这些都是线上事故级别的问题，但在开发阶段往往被忽视。

我是怕浪猫，一个在登录鉴权坑里摸爬滚打多年的全栈工程师。从前端到后端，从Token签发到权限校验，我踩过这套链路上几乎所有的坑。这一章我会从登录鉴权方案选型开始，带你完整走通后端接口开发、JWT（JSON Web Token）令牌签发与刷新、客户端登录状态管理、路由权限拦截、按钮级权限控制这五条主线，帮你构建一套企业级的移动端权限系统。看完这一章，你的登录鉴权不再是"能跑就行"，而是"经得起攻击、扛得住场景"。

## 11.1 移动端登录鉴权方案选型

### 11.1.1 Session会话机制优缺点解析

Session（会话）是Web端最经典的鉴权方案，核心思路是服务端为每个用户维护一份会话数据，通过Session ID来识别用户身份。整个流程的原理如下：

```
客户端                    服务端
  |                         |
  |--- 登录请求 ----------->|
  |                         |-- 创建Session存储用户信息
  |<-- Set-Cookie: SID ----|
  |                         |
  |--- 请求携带Cookie ---->|
  |                         |-- 根据SID查Session
  |<-- 返回业务数据 -------|
```

Session方案在Web端运行良好，因为浏览器原生支持Cookie机制，Session ID会自动随请求携带。但到了移动端，情况就截然不同了。

首先是存储问题。RN没有浏览器Cookie环境，虽然可以通过第三方库模拟Cookie，但这本身就是一种反模式。移动端APP（Application，应用程序）更倾向于使用本地存储如AsyncStorage来管理凭证，而Session ID存在AsyncStorage中既不优雅也不安全。AsyncStorage在iOS底层实现是基于plist文件的明文存储，Android底层是基于SQLite的明文存储，将Session ID放在这里等于把钥匙挂在门把手上。

其次是扩展性问题。Session数据存储在服务端内存中（或Redis中），每多一个在线用户就多一份内存开销。对于移动端来说，用户可能长时间挂着APP不操作，但Session依然占用着服务端资源。一个十万级日活的应用，如果Session有效期是24小时，那服务端同时要维护数万份Session数据，内存开销不可忽视。而且当服务端需要水平扩展部署多台服务器时，Session共享就成了一个额外的架构负担，必须引入Redis等中间件来统一存储Session数据，增加了系统的运维复杂度和故障点。

再者是移动端特有问题。APP切到后台再切回来，Session可能已经超时失效了，但客户端不知道，还是要拿着过期的Session ID去请求，白白浪费一次往返。用户在弱网环境下请求超时，Session状态不确定是否已更新——比如登录请求发出了但响应没回来，客户端不知道Session是否已创建。推送通知需要识别用户身份，但Session机制本身不提供跨请求的身份传递能力，推送服务无法通过Session ID判断目标用户。

> 移动端鉴权的第一性原则：凭证应该是自包含的、无状态的、可独立验证的。把状态放在服务端，移动端的复杂场景会让你疲于奔命。Session的设计初衷是给浏览器用的，强行搬到移动端就像把鱼从水里捞出来放到树上——不是不能活，但肯定活不好。

### 11.1.2 JWT无状态鉴权核心原理

JWT（JSON Web Token，JSON网页令牌）是为了解决Session痛点而生的一种无状态鉴权方案。它的核心思想是：把用户身份信息直接编码在Token中，服务端不需要存储Session，每次请求只需验证Token的签名是否合法即可识别用户身份。

JWT由三部分组成，用点号分隔：

```
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEyMywiZXhwIjoxNzAwMH0.s5dF7G8hJ2kL3mN1pQ6rT
|<------ Header ------>|<-------- Payload ------->|<---- Signature ---->|
```

三部分各自的职责和内容：

| 部分 | 内容 | 说明 |
|------|------|------|
| Header | 算法类型 | {"alg":"HS256","typ":"JWT"} |
| Payload | 用户数据 | userId、角色、过期时间等自定义声明 |
| Signature | 签名签名 | HMACSHA256(base64(header)+"."+base64(payload), secret) |

Header部分声明了Token使用的签名算法，Payload部分携带了用户身份相关的数据，Signature部分是使用服务端密钥对前两部分计算出的签名。这个签名是整个JWT安全性的核心——任何人都可以解码Header和Payload（它们只是Base64编码），但没有人可以在不知道密钥的情况下伪造合法的签名。

整个JWT鉴权流程如下：

```
客户端                      服务端
  |                           |
  |--- 登录请求 ------------->|
  |                           |-- 验证账号密码
  |<-- 返回JWT Token --------|
  |                           |
  |--- 携带Token请求 ------->|
  |                           |-- 验证签名+检查过期
  |<-- 返回业务数据 ---------|
```

与Session对比，JWT的核心优势在于无状态：服务端不需要存储任何会话数据，Token本身就携带了用户身份信息。这意味着服务端可以随意水平扩展，不需要Session共享中间件。同时，Token可以在多个服务之间共享，天然适合微服务架构——认证服务签发Token后，任何业务服务都能独立验证Token的合法性，不需要回调认证服务。

但JWT也有它不可忽视的短板。最大的问题是无法主动失效——一旦Token签发出去，在过期之前服务端无法"撤销"它，因为服务端不存储Token状态。用户修改密码后旧Token依然有效、管理员封禁用户后Token还能用、退出登录后Token理论上还能被截获使用。这些问题需要额外的黑名单机制或短有效期加刷新机制来弥补。另一个问题是Payload大小，Token中放的数据越多，每次请求携带的数据量就越大，对移动端的流量消耗有实际影响。

### 11.1.3 移动端Token存储安全分析

在RN中，Token存储有几种常见方案，它们的安全性差异很大。选择合适的存储方案是整个鉴权系统安全性的基础，存储方案一旦确定，后续的攻击面也就基本划定了。

**AsyncStorage**：RN官方提供的键值对存储方案，底层在iOS上使用NSUserDefaults，在Android上使用SQLite。它最大的问题是明文存储，任何有设备访问权限的人都能直接读取存储内容。而且iOS的NSUserDefaults在越狱设备上完全透明，Android的SQLite数据库在root设备上同样可以被直接查看。如果你的APP涉及支付、金融、医疗等敏感场景，使用AsyncStorage存储Token是不合规的。

**Keychain（iOS）/ KeyStore（Android）**：这是苹果和谷歌各自提供的硬件级安全存储方案。iOS的Keychain会将敏感数据加密后存储在Secure Enclave中，Android的KeyStore则依赖可信执行环境（TEE，Trusted Execution Environment）。即使设备被root或越狱，没有应用签名密钥也无法读取这些数据。Keychain还支持当设备锁屏时自动锁定存储内容，提供额外的安全层。

**加密存储方案**：如react-native-encrypted-storage、react-native-keychain等第三方库，它们封装了平台的Keychain/KeyStore能力，提供统一的JavaScript API。这些库在底层调用平台的安全存储，但在上层提供了更简洁的接口，是移动端Token存储的推荐方案。

存储方案安全性对比：

| 方案 | 加密级别 | 越狱/Root后安全 | 使用复杂度 | 推荐度 |
|------|---------|----------------|-----------|--------|
| AsyncStorage | 无加密 | 不安全 | 低 | 不推荐 |
| SQLite+手动加密 | 软加密 | 一般 | 中 | 一般 |
| EncryptedStorage | 硬件级 | 安全 | 低 | 推荐 |
| Keychain/KeyStore | 硬件级 | 安全 | 中 | 推荐 |

来看一个使用react-native-encrypted-storage存储Token的核心代码：

```tsx
import EncryptedStorage from 'react-native-encrypted-storage';

// 存储Token
async function saveToken(token: string) {
  try {
    await EncryptedStorage.setItem('access_token', token);
    await EncryptedStorage.setItem('refresh_token', refreshToken);
  } catch (error) {
    console.error('Token存储失败:', error);
  }
}

// 读取Token
async function getToken(): Promise<string | null> {
  try {
    return await EncryptedStorage.getItem('access_token');
  } catch (error) {
    return null;
  }
}

// 清除Token
async function clearToken() {
  try {
    await EncryptedStorage.removeItem('access_token');
    await EncryptedStorage.removeItem('refresh_token');
  } catch (error) {
    console.error('Token清除失败:', error);
  }
}
```

这里有一个容易被忽略的安全细节：Token存储时应该同时存储签发时间，在读取时检查Token是否在合理的时间范围内。这可以防止攻击者通过修改系统时间来延长Token有效期。虽然这种攻击方式要求设备级别的控制权，但对于高安全要求的场景仍然值得考虑。

> 安全存储的铁律：Token是用户的身份证，不是便利贴。AsyncStorage是敞开的抽屉，Keychain是带锁的保险柜。你把身份证放哪，决定了你的系统安全级别。在存储方案上偷懒，等于在防盗门上贴胶带。

### 11.1.4 多端登录状态同步解决方案

现代应用很少有单一端的场景了。同一个用户可能同时在手机APP、平板、Web浏览器、小程序中登录。多端登录状态同步是企业级应用必须面对的问题，而不同的同步策略直接决定了用户体验和系统复杂度。

常见的多端登录策略有三种，各自适用于不同的业务场景：

**单端登录**：同一时间只允许一个端在线。新端登录时踢掉旧端，旧端下次请求会收到401错误被迫退出。微信早期的登录策略就是这种模式。优点是安全可控，用户每次只有一个活跃会话，审计追踪简单。缺点是用户体验不够友好，频繁切换设备时需要反复登录。对于安全性要求极高的场景如银行APP、企业内网应用，单端登录是合适的选择。

**多端共存**：各端独立登录互不影响，每个端持有自己的Token。这是目前最主流的方案。但需要注意Token的管理：不同端的Token应该有不同的来源标识，方便服务端统计在线设备和管理Token生命周期。比如手机APP端登录签发的Token中platform字段为"mobile"，Web端登录签发的Token中platform字段为"web"，服务端可以根据platform做差异化的过期策略——比如手机端的Token有效期可以长一些（移动端重新登录体验差），Web端的Token有效期可以短一些。

**多端同步**：一端登录其他端自动登录，一端退出其他端自动退出。这需要引入WebSocket或推送通道来实时同步登录状态，实现成本最高，但用户体验最好。这种方案在IM类应用中比较常见，但通用业务系统中很少使用，因为复杂度收益比不高。

来看一个多端共存的Token设计结构：

```
用户登录时签发的Token Payload（负载）结构：
{
  "userId": 123,
  "platform": "ios",      // ios / android / web / miniapp
  "deviceId": "abc123",   // 设备唯一标识
  "tokenVersion": 1,      // Token版本号
  "exp": 1700000000,      // 过期时间
  "iat": 1699900000       // 签发时间
}
```

服务端可以通过platform和deviceId字段精确管理每个端的Token。当需要踢出某个设备时，只需要将该Token加入黑名单或修改用户的tokenVersion字段即可。修改tokenVersion会导致该用户所有端的Token同时失效，是一种"核按钮"级别的操作，适合用于密码修改、账号封禁等场景。如果只需要踢出单个设备，可以通过deviceId精准操作，不影响其他端的正常使用。

### 11.1.5 企业级登录鉴权方案选型

结合前面的分析，企业级RN移动端登录鉴权方案应该具备以下能力矩阵：

**双Token机制**：AccessToken（短有效期，如2小时）负责业务请求鉴权，RefreshToken（长有效期，如30天）负责刷新AccessToken。这样即使AccessToken被截获，攻击窗口也很短；而RefreshToken可以通过更严格的存储和传输策略来保护。双Token机制是安全性和用户体验之间的最佳平衡点。

**硬件级存储**：Token必须存储在Keychain/KeyStore中，不能使用AsyncStorage明文存储。这是移动端Token安全的底线。

**自动刷新机制**：AccessToken过期时自动使用RefreshToken获取新Token，整个过程对用户无感。用户不应该因为Token过期而被迫重新登录，除非RefreshToken本身也过期了。

**主动失效能力**：通过Token版本号或黑名单机制实现Token的主动失效，解决JWT无法撤销的问题。当用户修改密码、被管理员封禁、主动退出登录时，必须能让已签发的Token立即失效。

**多端管理**：支持多端共存，可按设备维度管理Token。管理员可以在后台查看用户当前在哪些设备上登录了，并可以主动踢出某个设备。

整个方案的架构如下：

```
登录流程：
用户输入账号密码 -> 后端验证 -> 签发AccessToken+RefreshToken
-> 客户端加密存储 -> 后续请求携带AccessToken

请求鉴权：
客户端请求 -> 拦截器附加Token -> 后端验证签名+过期+版本
-> 合法则处理请求 / 过期则返回401 -> 拦截器自动刷新

退出登录：
客户端调用退出接口 -> 后端将Token加入黑名单
-> 客户端清除本地Token和用户信息 -> 跳转登录页
```

这套方案在后续小节中会逐步落地实现，每个环节都有对应的代码和踩坑说明。

## 11.2 用户注册登录后端接口开发

### 11.2.1 用户数据表结构优化完善

登录鉴权的基础是用户数据表。一个设计良好的用户表不仅要存储基本信息，还要考虑安全字段和扩展字段。很多团队在初期只设计了username和password两个字段，等到后续需要接入手机号登录、邮箱验证、第三方登录、账号封禁等功能时，就要反复修改表结构，每次都是一次线上风险。

以下是企业级用户表的核心结构：

```sql
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password_hash` varchar(255) NOT NULL COMMENT '密码哈希值',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `avatar` varchar(500) DEFAULT NULL COMMENT '头像URL',
  `role` varchar(20) DEFAULT 'user' COMMENT '角色: admin/user',
  `status` tinyint DEFAULT 1 COMMENT '状态: 0禁用 1正常',
  `token_version` int DEFAULT 0 COMMENT 'Token版本号',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

几个关键字段需要特别说明。password_hash存储的是经过bcrypt加密后的密码哈希值，绝不存储明文密码——这不是建议而是铁律，任何明文存储密码的行为都是严重的安全事故隐患。token_version是用于主动失效Token的版本号，每次用户修改密码或退出登录时递增，JWT签发时将版本号写入Payload，验证时比对版本号是否一致，不一致则Token视为已失效。status字段用于账号封禁，被封禁的用户即使Token未过期也无法访问系统，这是一种无需修改Token的安全控制手段。last_login_at字段除了审计用途，还可以用于风控——如果检测到登录地点突变，可以触发安全验证。

### 11.2.2 bcrypt密码哈希加密存储实现

密码存储的安全底线是：数据库泄露后，攻击者也无法还原出用户的明文密码。这就要求密码哈希算法满足三个条件——不可逆、加盐（Salt，随机噪声）、慢哈希（计算成本可控以抵抗暴力破解）。

bcrypt是目前最推荐的密码哈希算法之一。它内置了盐值生成和自适应成本因子，随着硬件性能提升可以调整成本参数来保持抗暴力破解能力。这意味着即使五年后硬件算力提升了十倍，你只需要把成本因子从10调到11，就能维持同样的安全水位。

bcrypt哈希值的结构：

```
$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
|___|__|__________________________|______________________________|
 算法 成本        22字节盐值              31字节哈希值
```

在Node.js中使用bcrypt的核心代码：

```js
const bcrypt = require('bcrypt');

// 注册时加密密码
async function hashPassword(password) {
  const saltRounds = 10; // 成本因子，值越大越安全也越慢
  const hash = await bcrypt.hash(password, saltRounds);
  return hash;
}

// 登录时校验密码
async function verifyPassword(password, hash) {
  const match = await bcrypt.compare(password, hash);
  return match; // true=密码正确, false=密码错误
}

// 示例
const hashed = await hashPassword('mypassword123');
// hashed = "$2b$10$N9qo8uLOickgx2ZMRZoMy..."
const isValid = await verifyPassword('mypassword123', hashed);
// isValid = true
```

这里有一个常见的踩坑点：成本因子的选择。值为10时哈希计算约需100毫秒，值为12时约需400毫秒，值为14时约需1.6秒。对于登录场景，建议值设为10到12，既能保证安全性，又不会让用户等太久。但注册接口的密码加密可以设得更高一些，因为注册不是高频操作。如果成本因子设得太高（比如14以上），登录接口在高并发时可能会导致CPU被打满，这是一个需要在安全性和可用性之间仔细权衡的决策。

另一个坑是bcrypt对不同长度密码的处理。bcrypt有一个72字节的输入限制，超过72字节的密码会被静默截断。虽然这在实际场景中很少触发（没人会设72字节以上的密码），但如果你的业务允许超长密码，需要注意这个问题。解决方案是在bcrypt哈希前先对密码做一次SHA256摘要，再对摘要做bcrypt哈希，这样既能处理任意长度密码，又保留了bcrypt的所有安全特性。

还有一个更隐蔽的坑：bcrypt不同版本的前缀差异。$2a$是原始版本，$2b$是修复了实现bug的版本，$2y$是PHP实现使用的版本。三者计算结果不完全兼容，如果你的系统中有PHP后端参与密码校验，需要注意版本对齐问题。Node.js的bcrypt库默认使用$2b$。

### 11.2.3 注册参数校验与重复账号判断

注册接口的安全性远比登录接口重要，因为注册是写入操作，一旦脏数据进来后续清理成本极高。注册接口需要做三层校验：格式校验、唯一性校验、安全校验。缺少任何一层都可能被利用。

格式校验用Joi（或类似库）来约束参数格式：

```js
const Joi = require('joi');

const registerSchema = Joi.object({
  username: Joi.string().alphanum().min(3).max(20).required()
    .messages({
      'string.alphanum': '用户名只能包含字母和数字',
      'string.min': '用户名至少3个字符',
      'string.max': '用户名最多20个字符',
    }),
  password: Joi.string().min(8).max(50).required()
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .messages({
      'string.min': '密码至少8个字符',
      'string.pattern.base': '密码必须包含大小写字母和数字',
    }),
  phone: Joi.string().pattern(/^1[3-9]\d{9}$/).required()
    .message('手机号格式不正确'),
});
```

唯一性校验需要查数据库，这里有一个并发安全的问题。两个请求同时注册同一个用户名，各自查数据库都显示不存在，然后各自插入就会导致重复数据。即使有唯一索引兜底，第二个插入也会抛异常，但异常处理不当可能导致接口500错误。解决方案是在数据库层加唯一索引（前面表结构中已有UNIQUE KEY），同时在上层做先查后插的乐观校验：

```js
async function registerUser(userData) {
  // 参数格式校验
  const { error, value } = registerSchema.validate(userData);
  if (error) return { code: 400, msg: error.details[0].message };

  // 唯一性校验
  const existing = await User.findOne({
    where: {
      [Op.or]: [
        { username: value.username },
        { phone: value.phone }
      ]
    }
  });
  if (existing) {
    return { code: 409, msg: '用户名或手机号已注册' };
  }

  // 加密密码并写入数据库
  const passwordHash = await hashPassword(value.password);
  const user = await User.create({
    username: value.username,
    password_hash: passwordHash,
    phone: value.phone,
  });
  return { code: 200, msg: '注册成功', data: { id: user.id } };
}
```

安全校验容易被忽略但非常重要。比如用户名不能包含敏感词、不能模拟系统管理员等特殊账号、不能使用已知的泄露密码（可以接入Have I Been Pwned API检查密码是否在已知的泄露数据库中）。这些校验对于企业级应用是必要的投入。

### 11.2.4 登录密码校验逻辑开发实战

登录接口的核心逻辑是"验证身份、签发令牌"。虽然听起来简单，但其中有不少边界情况需要处理，每个边界情况处理不当都可能变成安全漏洞。

登录校验的完整流程：

```
接收账号密码 -> 格式校验 -> 查询用户记录 -> 检查账号状态
-> bcrypt比对密码 -> 更新登录时间 -> 签发JWT -> 返回Token
```

核心代码实现：

```js
async function login(username, password) {
  // 1. 查询用户
  const user = await User.findOne({ where: { username } });
  if (!user) {
    return { code: 401, msg: '账号或密码错误' };
  }

  // 2. 检查账号状态
  if (user.status === 0) {
    return { code: 403, msg: '账号已被禁用，请联系管理员' };
  }

  // 3. 校验密码
  const isValid = await bcrypt.compare(password, user.password_hash);
  if (!isValid) {
    return { code: 401, msg: '账号或密码错误' };
  }

  // 4. 更新最后登录时间
  await user.update({ last_login_at: new Date() });

  // 5. 签发双Token
  const accessToken = generateAccessToken(user);
  const refreshToken = generateRefreshToken(user);

  return {
    code: 200,
    msg: '登录成功',
    data: { accessToken, refreshToken, user: { id: user.id, username: user.username, role: user.role } }
  };
}
```

这里有一个安全设计的细节：当用户名不存在时，返回的错误信息是"账号或密码错误"而不是"用户不存在"。这是为了防止账号枚举攻击——攻击者通过遍历用户名尝试注册或登录，根据返回信息判断哪些账号存在。统一错误信息让攻击者无法区分"用户不存在"和"密码错误"两种情况。

另一个细节是密码比对的时间恒定性。bcrypt的compare操作在密码不匹配时和密码匹配时的执行时间是接近的，这可以防止基于响应时间的侧信道攻击。如果你自己实现密码比对逻辑（比如用普通的字符串比较），就会存在时间差——正确密码比对时间长（逐字符比较到最后一位），错误密码比对时间短（第一位就不匹配就返回），攻击者可以通过响应时间差来逐字符猜测密码。所以永远使用bcrypt自带的compare方法，不要自己实现密码比对。

> 安全设计的第一原则：不要给攻击者提供任何信息优势。一个"用户不存在"的提示，对攻击者来说就是一个有价值的情报。安全系统设计中的每一个细节，都应该是攻击者的信息黑洞。

### 11.2.5 登录异常提示统一处理机制

登录场景的异常类型远不止"密码错误"一种。一个完善的登录系统需要处理以下异常情况，每种异常都需要对应不同的提示和处理策略：

| 异常类型 | HTTP状态码 | 错误提示 | 触发条件 |
|---------|-----------|---------|---------|
| 参数缺失 | 400 | 请输入完整的登录信息 | 用户名或密码为空 |
| 账号不存在 | 401 | 账号或密码错误 | 用户名查不到记录 |
| 密码错误 | 401 | 账号或密码错误 | bcrypt比对失败 |
| 账号被禁用 | 403 | 账号已被禁用 | status字段为0 |
| 登录频率限制 | 429 | 登录尝试过于频繁 | 同IP 1分钟内超过5次 |
| 服务端异常 | 500 | 登录服务异常，请稍后重试 | 数据库连接失败等 |

在RN客户端，需要对这些异常做统一处理。核心思路是在请求层封装统一的错误拦截：

```tsx
import axios from 'axios';

const request = axios.create({ baseURL: API_BASE_URL, timeout: 10000 });

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { status, data } = error.response || {};
    switch (status) {
      case 401:
        showToast(data?.msg || '账号或密码错误');
        break;
      case 403:
        showToast(data?.msg || '账号已被禁用');
        break;
      case 429:
        showToast('登录尝试过于频繁，请稍后再试');
        break;
      default:
        showToast(data?.msg || '网络异常，请稍后重试');
    }
    return Promise.reject(error);
  }
);
```

登录频率限制是一个容易被忽视的安全措施。没有频率限制的登录接口相当于给暴力破解开了绿灯——攻击者可以每秒发上百个请求来尝试不同密码。实现方式可以在服务端用Redis记录IP维度的登录失败次数，超过阈值后临时封锁该IP。也可以在账号维度做限制，连续失败5次锁定账号30分钟。两种维度建议同时使用，IP维度防止分布式扫描，账号维度防止单账号暴力破解。

## 11.3 JWT令牌签发、解析与自动刷新

### 11.3.1 JWT令牌结构与加密规则解析

在签发JWT之前，需要先彻底理解它的加密规则和算法选择。JWT支持多种签名算法，最常用的是HS256（HMAC with SHA-256）和RS256（RSA Signature with SHA-256）。

HS256是对称加密算法，签发和验证使用同一个密钥。优点是实现简单、性能好、计算速度快，缺点是密钥泄露后任何人都可以伪造Token。适合单体应用或可信内部服务——只有一个服务端实例持有密钥的场景。

RS256是非对称加密算法，使用私钥签发、公钥验证。签发方保管私钥，验证方只需要公钥。即使验证方被攻破，攻击者也无法伪造Token，因为公钥只能验证不能签发。适合微服务架构或第三方对接场景——认证服务独占私钥能签发Token，其他业务服务只有公钥只能验证。

对于RN移动端项目，大多数情况下HS256就够了。但如果你的后端是微服务架构，多个服务都需要验证Token，建议用RS256，这样只有认证服务能签发Token，其他服务即使被入侵也无法伪造用户身份。

还有一点需要注意：JWT的Header和Payload只是Base64编码，不是加密。任何人拿到Token都可以解码出Payload内容。所以绝对不要在Payload中放敏感信息如密码、身份证号等。如果确实需要加密Payload内容，应该使用JWE（JSON Web Encryption），但那会增加复杂度，大多数场景下不必要。

### 11.3.2 登录成功AccessToken令牌签发

双Token机制是企业级登录鉴权的标准配置。AccessToken有效期短（通常2小时），用于业务请求鉴权；RefreshToken有效期长（通常30天），用于获取新的AccessToken。

签发Token的核心代码：

```js
const jwt = require('jsonwebtoken');

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET;
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;

// 签发AccessToken（短有效期）
function generateAccessToken(user) {
  return jwt.sign(
    {
      userId: user.id,
      username: user.username,
      role: user.role,
      tokenVersion: user.token_version,
    },
    ACCESS_SECRET,
    { expiresIn: '2h' }
  );
}

// 签发RefreshToken（长有效期，只含最少信息）
function generateRefreshToken(user) {
  return jwt.sign(
    { userId: user.id, tokenVersion: user.token_version },
    REFRESH_SECRET,
    { expiresIn: '30d' }
  );
}
```

注意AccessToken的Payload中包含了tokenVersion字段，这是用于主动失效的关键设计。每次用户修改密码或退出登录时，数据库中的token_version递增，验证Token时会比对Payload中的版本号与数据库中的版本号，不一致则视为Token已失效。这是一种用少量数据库查询换取JWT主动失效能力的折中方案。

RefreshToken只包含userId和tokenVersion，不包含业务信息。这是因为RefreshToken的使用场景单一（只用于刷新Token），不需要携带多余信息，减少泄露风险。同时AccessToken和RefreshToken使用不同的密钥签发，这样即使AccessToken的密钥泄露，攻击者也无法伪造RefreshToken来持续获取新Token。

服务端验证Token的中间件：

```js
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ code: 401, msg: '未提供认证令牌' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, ACCESS_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ code: 401, msg: 'Token已过期', needRefresh: true });
    }
    return res.status(401).json({ code: 401, msg: '无效的Token' });
  }
}
```

这里的关键设计是needRefresh字段：当Token过期时返回needRefresh: true，客户端据此触发自动刷新流程。当Token签名无效或格式错误时不返回needRefresh，因为这种情况说明Token被篡改或伪造，不应该尝试刷新而应该直接退出登录。

### 11.3.3 全局请求拦截自动携带Token

客户端每次发起业务请求都需要自动在Header中携带Token，这在RN中通过Axios拦截器实现。核心原理是在请求发出前拦截，从安全存储中读取Token并附加到请求头。

```tsx
import axios from 'axios';
import EncryptedStorage from 'react-native-encrypted-storage';

const request = axios.create({ baseURL: API_BASE_URL, timeout: 10000 });

// 请求拦截器：自动携带Token
request.interceptors.request.use(async (config) => {
  const token = await EncryptedStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一处理401
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { response } = error;
    if (response?.status === 401 && response.data?.needRefresh) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

这里有一个关键设计：响应拦截器中检测到401且needRefresh标记为true时，会自动触发Token刷新逻辑。如果刷新成功，用新Token重发原请求，整个过程对调用方完全透明——业务代码调用接口时不需要关心Token过期和刷新逻辑，拦截器全部搞定。如果刷新失败，才真正reject请求，业务代码的catch中会收到错误。

### 11.3.4 Token过期自动刷新机制实现

Token自动刷新是整个鉴权链路中最复杂的环节，也是踩坑最多的地方。核心难点在于并发刷新控制：当多个请求同时收到401时，不能让它们各自触发刷新，否则会导致RefreshToken被多次调用，而RefreshToken通常是单次使用的——每次刷新后旧的RefreshToken失效，返回新的RefreshToken，第二次刷新调用拿着已失效的RefreshToken必然失败。

解决方案是用一个共享的Promise来做锁控制：

```tsx
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
let pendingQueue: Array<(token: string) => void> = [];

async function refreshAccessToken(): Promise<string | null> {
  // 如果正在刷新，复用同一个Promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = doRefresh();

  try {
    const newToken = await refreshPromise;
    if (newToken) {
      pendingQueue.forEach(cb => cb(newToken));
      pendingQueue = [];
    }
    return newToken;
  } finally {
    isRefreshing = false;
    refreshPromise = null;
  }
}

async function doRefresh(): Promise<string | null> {
  const refreshToken = await EncryptedStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  try {
    const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refreshToken });
    const { accessToken, refreshToken: newRefreshToken } = res.data.data;
    await EncryptedStorage.setItem('access_token', accessToken);
    await EncryptedStorage.setItem('refresh_token', newRefreshToken);
    return accessToken;
  } catch {
    await clearAllTokens();
    redirectToLogin();
    return null;
  }
}
```

整个并发刷新控制的流程：

```
请求A收到401 -> 触发刷新 -> isRefreshing=true
请求B收到401 -> 发现isRefreshing=true -> 等待refreshPromise
请求C收到401 -> 发现isRefreshing=true -> 等待refreshPromise
刷新完成 -> 通知A、B、C用新Token重发 -> isRefreshing=false
```

这里还有一个进阶问题：pendingQueue中的请求在等待新Token时，如果刷新失败了怎么办？需要在刷新失败时清空队列并通知所有等待的请求跳转到登录页。否则这些请求会永远卡在等待状态，页面看起来像假死。修复方式是在catch分支中也要处理pendingQueue：

```tsx
// 刷新失败时也要清空队列
catch (error) {
  pendingQueue = [];
  await clearAllTokens();
  redirectToLogin();
  return null;
}
```

> 并发刷新是Token管理的阿喀琉斯之踵。90%的开发者第一次实现自动刷新时都会踩这个坑：多个请求同时刷新，RefreshToken被消费多次，第二次刷新就直接失败了。一个Promise锁解决的问题，可能让你debug三天。更可怕的是这个问题在测试环境很难复现——因为测试时通常不会同时发大量请求，只有线上高并发场景才会触发。

### 11.3.5 非法Token拦截与强制退出登录

当Token完全失效（RefreshToken也过期了、或者用户被封禁、或者Token被加入黑名单）时，客户端需要执行强制退出登录流程。这个流程的核心步骤是：清除本地所有凭证和用户信息、重置全局状态、跳转登录页。

```tsx
async function forceLogout() {
  // 1. 清除本地Token
  await EncryptedStorage.removeItem('access_token');
  await EncryptedStorage.removeItem('refresh_token');

  // 2. 清除本地用户信息
  await EncryptedStorage.removeItem('user_info');

  // 3. 重置全局状态
  useUserStore.getState().reset();

  // 4. 重置导航栈到登录页
  navigationRef.reset({
    index: 0,
    routes: [{ name: 'Login' }],
  });
}
```

强制退出登录的触发场景包括：RefreshToken刷新失败（RefreshToken也过期了）、服务端返回403（账号被禁用）、服务端返回特定的Token失效错误码（tokenVersion不匹配）、用户主动退出登录。无论是哪种触发场景，执行流程都必须是原子性的——不能出现Token清了但用户信息没清、或者状态重置了但页面没跳转的情况。如果流程中间某步失败了，用户可能处于"半退出"状态：Token没了但页面还停留在需要登录的页面上，导致持续报错。

为了确保原子性，可以将整个流程包装在try-finally中，确保最后的跳转一定执行。如果某步失败了，至少要保证用户看到的是登录页而不是一个报错的空白页面。

## 11.4 客户端登录状态全局管理

### 11.4.1 Token本地安全持久化存储

前面我们已经讨论了Token存储方案的选择，这里来完整实现一个Token管理模块。这个模块需要封装存储、读取、清除三个核心操作，并处理跨平台兼容性问题。一个好的Token管理模块应该将存储细节完全封装，上层调用者不需要知道底层用的是EncryptedStorage还是Keychain。

```tsx
import EncryptedStorage from 'react-native-encrypted-storage';

const TOKEN_KEYS = {
  ACCESS: 'access_token',
  REFRESH: 'refresh_token',
  USER_INFO: 'user_info',
};

class TokenManager {
  async setTokens(accessToken: string, refreshToken: string) {
    await EncryptedStorage.setItem(TOKEN_KEYS.ACCESS, accessToken);
    await EncryptedStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken);
  }

  async getAccessToken(): Promise<string | null> {
    return await EncryptedStorage.getItem(TOKEN_KEYS.ACCESS);
  }

  async getRefreshToken(): Promise<string | null> {
    return await EncryptedStorage.getItem(TOKEN_KEYS.REFRESH);
  }

  async setUserInfo(userInfo: object) {
    await EncryptedStorage.setItem(
      TOKEN_KEYS.USER_INFO, JSON.stringify(userInfo)
    );
  }

  async getUserInfo(): Promise<object | null> {
    const info = await EncryptedStorage.getItem(TOKEN_KEYS.USER_INFO);
    return info ? JSON.parse(info) : null;
  }

  async clearAll() {
    await EncryptedStorage.removeItem(TOKEN_KEYS.ACCESS);
    await EncryptedStorage.removeItem(TOKEN_KEYS.REFRESH);
    await EncryptedStorage.removeItem(TOKEN_KEYS.USER_INFO);
  }
}

export const tokenManager = new TokenManager();
```

这里封装成单例类的好处是全局只有一个Token管理入口，方便统一控制。比如后期需要加日志埋点或存储迁移（从AsyncStorage迁移到EncryptedStorage），只需要改这一个地方，所有调用方无感知。

还有一个实际开发中的坑：EncryptedStorage在某些Android设备上首次调用时会有几十毫秒的初始化延迟。如果在APP启动时同步调用getToken，可能会阻塞启动流程。解决方案是在APP启动时异步预加载EncryptedStorage，确保后续调用时已经初始化完成。

### 11.4.2 全局登录状态响应式管理

Token存储解决了持久化问题，但UI层需要响应式地感知登录状态变化。当用户登录成功时，所有依赖用户信息的页面都应该自动更新；当用户退出登录时，所有页面都应该自动清空用户数据。这就需要一个响应式的全局状态管理层。

这里使用Zustand来实现全局登录状态管理（上一章详细讲过Zustand的使用）：

```tsx
import { create } from 'zustand';
import { tokenManager } from './tokenManager';

interface UserState {
  isLoggedIn: boolean;
  userInfo: UserInfo | null;
  accessToken: string | null;
  login: (tokens: TokenPair, userInfo: UserInfo) => Promise<void>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<void>;
}

const useUserStore = create<UserState>((set) => ({
  isLoggedIn: false,
  userInfo: null,
  accessToken: null,

  login: async (tokens, userInfo) => {
    await tokenManager.setTokens(tokens.accessToken, tokens.refreshToken);
    await tokenManager.setUserInfo(userInfo);
    set({ isLoggedIn: true, userInfo, accessToken: tokens.accessToken });
  },

  logout: async () => {
    await tokenManager.clearAll();
    set({ isLoggedIn: false, userInfo: null, accessToken: null });
  },

  restoreSession: async () => {
    const token = await tokenManager.getAccessToken();
    const userInfo = await tokenManager.getUserInfo();
    if (token && userInfo) {
      set({ isLoggedIn: true, userInfo, accessToken: token });
    }
  },
}));
```

这个设计的核心是login和logout两个方法都同时操作两个数据源：持久化存储（EncryptedStorage）和内存状态（Zustand store）。持久化存储保证APP重启后登录态不丢失，内存状态保证UI能响应式更新。两个数据源必须保持一致，如果出现不一致（比如持久化有Token但内存状态是未登录），以内存状态为准，因为内存状态是当前会话的真相。

### 11.4.3 APP启动登录状态校验逻辑

APP冷启动时，需要从本地存储中恢复登录状态。这个过程看似简单，但有几个边界情况需要处理，处理不好会导致用户体验差甚至安全问题。

启动校验流程：

```
APP启动 -> 读取本地Token -> Token存在？
  ├─ 是 -> 验证Token是否过期
  │        ├─ 未过期 -> 恢复登录态 -> 进入首页
  │        └─ 已过期 -> 尝试刷新
  │                 ├─ 刷新成功 -> 恢复登录态 -> 进入首页
  │                 └─ 刷新失败 -> 清空登录态 -> 进入登录页
  └─ 否 -> 进入登录页
```

在RN的入口文件中实现这个逻辑：

```tsx
function App() {
  const [isReady, setIsReady] = useState(false);
  const restoreSession = useUserStore((s) => s.restoreSession);

  useEffect(() => {
    async function init() {
      try {
        await restoreSession();
      } catch (error) {
        console.error('Session restore failed:', error);
      } finally {
        setIsReady(true);
      }
    }
    init();
  }, []);

  if (!isReady) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      <RootNavigator />
    </NavigationContainer>
  );
}
```

这里有个容易踩的坑：restoreSession只检查本地是否有Token，但没有验证Token是否真的有效（是否过期、是否被服务端撤销）。如果只依赖本地判断，可能出现Token存在但实际已失效的情况，用户进入首页后第一个请求就收到401。

更稳健的方案是启动时先恢复本地状态让用户快速进入首页（保证启动速度），同时后台发一个轻量级的校验请求（比如GET /user/profile）验证Token有效性。如果校验失败再静默刷新或退出登录。这样既保证了启动速度（用户不需要等网络请求完成才能进入首页），又保证了状态准确性（后台校验失败会及时纠正状态）。

### 11.4.4 未登录页面自动跳转拦截

在React Navigation中，实现未登录拦截的标准方式是在导航组件中根据登录状态动态渲染路由。核心思路是：如果用户未登录且当前不在白名单页面，自动跳转到登录页。

```tsx
function RootNavigator() {
  const isLoggedIn = useUserStore((s) => s.isLoggedIn);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isLoggedIn ? (
        <Stack.Screen name="Main" component={MainNavigator} />
      ) : (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  );
}
```

但这种方案有一个局限：它只在导航层级做了粗粒度的拦截。如果用户已经登录但在某个深层页面触发了Token失效，需要从当前页面跳回登录页，这时就需要用到navigationRef在全局任何地方执行导航跳转。

在React Navigation中可以通过navigationRef实现全局导航：

```tsx
import { navigationRef } from './navigationRef';

function navigateToLogin() {
  if (navigationRef.isReady()) {
    navigationRef.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  }
}
```

在forceLogout函数中调用navigateToLogin，就能在任何位置触发跳转登录页，不受当前页面层级的限制。这里需要注意navigationRef.isReady()的检查——在APP启动初期导航容器可能还没准备好，直接调用reset会报错。

### 11.4.5 退出登录状态清空与重置

退出登录不是简单地清个Token就完事了。一个完整的退出流程需要清空多类数据，每类数据都有其清空的必要性：

**认证数据**：AccessToken、RefreshToken。这是最基本的，不清空的话下个用户能直接用上个用户的Token。
**用户数据**：用户信息、用户偏好设置。不同用户的内容偏好不同，残留会导致推荐不准。
**业务缓存**：购物车数据、浏览历史、搜索记录。这些数据属于上个用户，残留可能导致信息泄露。
**全局状态**：Zustand store中的所有用户相关状态。状态残留会导致页面显示上个用户的数据。
**Web缓存**：WebView的cookie和缓存（如果有的话）。WebView中的登录态不会自动清除，需要手动处理。

```tsx
async function handleLogout() {
  // 1. 调用后端退出接口（可选，用于服务端清理Token）
  try {
    await request.post('/auth/logout');
  } catch (error) {
    // 即使接口失败也要继续本地清理
  }

  // 2. 清空认证数据
  await tokenManager.clearAll();

  // 3. 清空业务缓存
  await AsyncStorage.multiRemove([
    'cart_data', 'search_history', 'browse_history'
  ]);

  // 4. 重置全局状态
  useUserStore.getState().reset();
  useCartStore.getState().reset();
  useConfigStore.getState().reset();

  // 5. 跳转登录页
  navigationRef.reset({
    index: 0,
    routes: [{ name: 'Login' }],
  });
}
```

这里有一个踩坑点：后端退出接口失败时，不应该阻断本地清理流程。网络异常不应该导致用户无法退出登录——想象一下用户要退出登录但网络刚好断了，如果因为接口失败就中断退出流程，用户会困在当前账号里无法切换。所以后端调用要用try-catch包裹，无论成功与否都继续执行本地清理。

另一个容易遗漏的是WebView的cookie清理。如果你的APP中有WebView页面且用户在其中登录了第三方账号，退出登录时需要清理WebView的cookie，否则下一个登录的用户打开WebView时可能看到上一个用户的WebView内容。在RN中可以通过react-native-webview的incognito属性或手动清除cookie来实现。

## 11.5 路由权限拦截与页面访问控制

### 11.5.1 全局路由守卫完整封装实现

页面级权限控制的核心是路由守卫。与Web端框架（如Vue Router的beforeEach、React Router的PrivateRoute）不同，React Navigation没有内置的路由守卫机制，需要开发者自行实现。这也是RN开发中鉴权相关的最容易出问题的环节。

实现路由守卫的核心思路是：在导航容器的状态变化回调中拦截路由跳转，根据当前用户的登录状态和权限判断是否允许访问目标页面。如果权限不足，拦截跳转并重定向到合适的页面。

先定义路由权限配置：

```tsx
type RoutePermission = 'public' | 'auth' | 'admin';

const routePermissions: Record<string, RoutePermission> = {
  Login: 'public',
  Register: 'public',
  Home: 'auth',
  Profile: 'auth',
  Settings: 'auth',
  AdminPanel: 'admin',
  UserManage: 'admin',
};
```

然后封装路由守卫组件：

```tsx
function RouteGuard({ children }: { children: ReactNode }) {
  const isLoggedIn = useUserStore((s) => s.isLoggedIn);
  const userRole = useUserStore((s) => s.userInfo?.role);
  const currentRoute = useRoute();

  const requiredPermission = routePermissions[currentRoute.name] || 'auth';

  if (requiredPermission === 'public') {
    return <>{children}</>;
  }

  if (requiredPermission === 'auth' && !isLoggedIn) {
    return <NavigateToLogin />;
  }

  if (requiredPermission === 'admin' && userRole !== 'admin') {
    return <NoPermission />;
  }

  return <>{children}</>;
}
```

这种声明式配置的好处是路由权限一目了然，新增页面只需要在routePermissions中加一行配置。相比在每个页面组件内部单独做权限判断，这种集中式配置更不容易遗漏。

### 11.5.2 免登录白名单页面配置

并非所有页面都需要登录才能访问。常见的免登录页面包括：登录页、注册页、忘记密码页、关于页面、隐私政策页等。这些页面需要配置在白名单中，路由守卫对白名单页面不做登录状态检查。

```tsx
const PUBLIC_ROUTES = [
  'Login', 'Register', 'ForgotPassword',
  'About', 'PrivacyPolicy', 'Terms'
];

function isPublicRoute(routeName: string): boolean {
  return PUBLIC_ROUTES.includes(routeName);
}
```

白名单配置看似简单，但有几个边界情况需要注意，每个都可能成为线上Bug的来源。

第一，深链接直达问题。用户可能通过推送通知或深链接直接跳到某个需要登录的页面。如果用户未登录，直接跳转会导致白屏或报错。正确做法是拦截深链接跳转，如果目标页面不在白名单中且用户未登录，先跳转到登录页，登录成功后再跳转到目标页面。这种"登录后回跳"的体验在电商场景中非常常见——用户从推送通知点进订单详情页，未登录时先跳登录页，登录后自动回到订单详情页。

```tsx
const pendingRouteRef = { name: '', params: {} };

function handleDeepLink(link: string) {
  const route = parseDeepLink(link);
  if (!isLoggedIn && !isPublicRoute(route.name)) {
    pendingRouteRef.name = route.name;
    pendingRouteRef.params = route.params;
    navigateToLogin();
  } else {
    navigate(route.name, route.params);
  }
}

// 登录成功后检查是否有待跳转的页面
function onLoginSuccess() {
  if (pendingRouteRef.name) {
    navigate(pendingRouteRef.name, pendingRouteRef.params);
    pendingRouteRef.name = '';
  }
}
```

第二，白名单页面的反向拦截。已登录用户不应该再看到登录页和注册页。如果用户已登录但手动导航到登录页（比如通过深链接或代码逻辑），应该自动重定向到首页。这是很多APP都有的Bug——已登录用户点击某个链接跳到了登录页，虽然不影响安全但体验很差。

```tsx
function AuthScreen({ navigation }) {
  const isLoggedIn = useUserStore((s) => s.isLoggedIn);
  
  useEffect(() => {
    if (isLoggedIn) {
      navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
    }
  }, [isLoggedIn]);
  
  // ...登录表单
}
```

### 11.5.3 多角色页面访问权限控制

在企业级应用中，除了登录状态检查，还需要做角色级别的权限控制。常见的角色划分有普通用户、管理员、超级管理员等。不同角色能访问的页面不同，这比单纯的登录状态检查更细粒度。

定义角色枚举和页面权限映射：

```tsx
enum Role {
  USER = 'user',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
}

const pageRoleMap: Record<string, Role[]> = {
  Home: [Role.USER, Role.ADMIN, Role.SUPER_ADMIN],
  Profile: [Role.USER, Role.ADMIN, Role.SUPER_ADMIN],
  UserManage: [Role.ADMIN, Role.SUPER_ADMIN],
  SystemConfig: [Role.SUPER_ADMIN],
};

function hasPagePermission(pageName: string, role: Role): boolean {
  const allowedRoles = pageRoleMap[pageName];
  if (!allowedRoles) return true; // 未配置权限的页面默认允许访问
  return allowedRoles.includes(role);
}
```

角色权限校验的完整流程：

```
用户访问页面 -> 检查是否在白名单
  ├─ 是 -> 直接放行
  └─ 否 -> 检查是否登录
           ├─ 未登录 -> 跳转登录页
           └─ 已登录 -> 检查角色权限
                        ├─ 有权限 -> 放行
                        └─ 无权限 -> 跳转无权限页
```

这里有一个设计决策：未配置权限的页面应该默认允许还是默认拒绝？从安全角度看应该默认拒绝（白名单模式更安全），但从开发效率角度看默认允许更友好（避免每新增一个页面都要配权限）。建议在开发阶段默认允许（方便调试），上线前检查所有未配置权限的页面，确保没有遗漏。

### 11.5.4 权限不足页面兜底跳转方案

当用户权限不足时，需要给出明确的提示和引导。最佳实践是设计一个统一的"无权限"页面，而不是直接弹个Toast然后把用户晾在原地。统一的兜底页面既给了用户明确反馈，又提供了下一步的操作引导。

```tsx
function NoPermissionScreen({ route }) {
  const { message, returnTo } = route.params || {};
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>权限不足</Text>
      <Text style={styles.desc}>
        {message || '您没有权限访问此页面'}
      </Text>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigationRef.navigate(returnTo || 'Home')}
      >
        <Text>返回首页</Text>
      </TouchableOpacity>
    </View>
  );
}
```

兜底页面设计需要注意的几个细节：一是要提供返回操作，不能让用户卡在一个无操作页面上。二是提示信息要具体，不要只说"权限不足"，要说明需要什么权限才能访问，比如"此页面需要管理员权限"。三是要保留用户的入口路径信息，如果用户是从某个页面跳转过来的，提供"返回上一页"的选项比"返回首页"更友好。

> 权限控制的设计哲学：宁可拦错，不可放过。一个权限漏洞导致的数据泄露，比你多弹一个提示框的体验问题严重一万倍。用户可能抱怨"为什么我点不了这个按钮"，但绝不会原谅"为什么我的数据被别人看到了"。

### 11.5.5 动态路由权限匹配机制

在实际企业项目中，页面权限往往不是静态配置的，而是由后端动态下发的。管理员可以在后台配置哪些角色能访问哪些页面，前端需要根据后端返回的权限数据动态生成路由配置。这种模式在SaaS（Software as a Service，软件即服务）平台和中后台系统中非常常见。

动态权限的数据结构：

```ts
interface PagePermission {
  page: string;       // 页面标识
  roles: string[];    // 允许访问的角色列表
  actions: string[];  // 允许的操作：view/edit/delete
}

// 后端返回的权限数据示例
const permissions: PagePermission[] = [
  { page: 'Home', roles: ['user', 'admin'], actions: ['view'] },
  { page: 'UserManage', roles: ['admin'], actions: ['view', 'edit', 'delete'] },
  { page: 'SystemConfig', roles: ['admin'], actions: ['view', 'edit'] },
];
```

前端在登录成功后拉取权限数据并存储到全局状态中：

```tsx
async function loadPermissions() {
  const res = await request.get('/user/permissions');
  usePermissionStore.getState().setPermissions(res.data);
}

// 权限判断工具函数
function checkPagePermission(page: string): boolean {
  const permissions = usePermissionStore.getState().permissions;
  const userRole = useUserStore.getState().userInfo?.role;
  const pagePerm = permissions.find(p => p.page === page);
  if (!pagePerm) return false;
  return pagePerm.roles.includes(userRole);
}
```

动态权限的好处是管理员可以在不改代码的情况下调整页面访问权限。比如临时开放某个页面的访问权限给某个角色，只需要在后台配置即可，不需要发版。这对于运营灵活性和紧急权限调整非常有价值。

但动态权限也有一个风险：如果权限数据加载延迟或失败，前端可能无法正确判断权限。解决方案是在权限数据加载完成前，所有需要权限的页面默认拒绝访问（安全优先）。或者使用本地缓存的上次权限数据作为兜底（可用性优先）。两种策略的选择取决于业务场景的安全要求等级。

## 11.6 按钮级细粒度权限控制

### 11.6.1 后端接口权限字段返回设计

页面级权限控制解决了"能不能看这个页面"的问题，但同一个页面内不同角色能执行的操作也可能不同。比如用户管理页面，管理员能新增、编辑、删除用户，而普通运营人员只能查看用户列表，不能做修改操作。这就是按钮级权限控制要解决的问题。

按钮级权限数据由后端在登录成功或获取权限接口时下发。数据结构设计如下：

```ts
interface PermissionData {
  pages: PagePermission[];
  actions: Record<string, string[]>;
}

// 后端返回示例
{
  "pages": [
    { "page": "UserManage", "roles": ["admin", "operator"] }
  ],
  "actions": {
    "UserManage": ["user:add", "user:edit", "user:delete"],
    "OrderManage": ["order:view", "order:cancel"],
    "ProductManage": ["product:add", "product:edit", "product:delete"]
  }
}
```

actions是一个以页面为键、以操作权限标识为值的映射。权限标识采用"模块:操作"的命名规范，如"user:add"表示用户模块的新增操作。这种命名方式清晰且易于扩展——新增一个操作只需要加一个标识，不需要修改已有的权限结构。

后端返回权限数据的接口实现：

```js
// /user/permissions 接口
router.get('/permissions', authMiddleware, async (req, res) => {
  const userId = req.user.userId;
  const user = await User.findById(userId);
  
  const rolePermissions = await RolePermission.findAll({
    where: { role: user.role }
  });

  const pages = extractPagePermissions(rolePermissions);
  const actions = extractActionPermissions(rolePermissions);

  res.json({ code: 200, data: { pages, actions } });
});
```

权限数据应该在两个时机拉取：一是登录成功后立即拉取，用于初始化权限配置。二是APP启动恢复登录态后拉取，用于获取最新的权限配置。因为管理员可能在用户上次登录和这次启动之间修改了权限配置，如果只依赖登录时的权限数据，可能使用过时的权限规则。

### 11.6.2 前端权限数据全局状态存储

前端收到权限数据后，需要存储到全局状态中供各页面使用。使用Zustand创建一个权限管理Store：

```tsx
import { create } from 'zustand';

interface PermissionState {
  pagePermissions: PagePermission[];
  actionPermissions: Record<string, string[]>;
  setPermissions: (data: PermissionData) => void;
  hasAction: (page: string, action: string) => boolean;
  reset: () => void;
}

const usePermissionStore = create<PermissionState>((set, get) => ({
  pagePermissions: [],
  actionPermissions: {},

  setPermissions: (data) => set({
    pagePermissions: data.pages,
    actionPermissions: data.actions,
  }),

  hasAction: (page, action) => {
    const actions = get().actionPermissions[page] || [];
    return actions.includes(action);
  },

  reset: () => set({ pagePermissions: [], actionPermissions: {} }),
}));
```

hasAction方法是权限判断的核心API。它接收页面名和操作标识两个参数，返回布尔值表示当前用户是否有执行该操作的权限。这个方法会在后续的权限组件中被频繁调用，所以实现要尽量高效——直接从内存对象中查找，不做任何异步操作。

权限数据也需要考虑持久化问题。如果APP启动时权限数据还没从服务端拉回来，按钮级权限判断会全部返回false，导致所有受控按钮都被隐藏。解决方案是在本地缓存上次拉取的权限数据，启动时先用缓存数据渲染，同时后台拉取最新数据更新。虽然可能短暂使用过时的权限配置，但比所有按钮都消失要好得多。

### 11.6.3 自定义权限判断工具封装

为了让权限控制在JSX中使用更简洁，可以封装一个自定义Hook和一个权限组件。这样业务代码中不需要手动调用hasAction，而是通过声明式的方式描述权限需求。

```tsx
// 权限Hook
function usePermission(page: string) {
  const actionPermissions = usePermissionStore((s) => s.actionPermissions);
  const actions = actionPermissions[page] || [];
  
  return {
    can: (action: string) => actions.includes(action),
    canAny: (actions: string[]) => actions.some(a => actions.includes(a)),
    canAll: (actions: string[]) => actions.every(a => actions.includes(a)),
  };
}

// 权限组件
function AuthButton({ page, action, mode, ...props }) {
  const { can } = usePermission(page);
  const hasPermission = can(action);

  if (!hasPermission) {
    if (mode === 'disabled') {
      return <Button {...props} disabled />;
    }
    return null; // 隐藏模式
  }

  return <Button {...props} />;
}
```

使用方式非常简洁：

```tsx
function UserManageScreen() {
  return (
    <View>
      <AuthButton page="UserManage" action="user:add" title="新增用户" onPress={handleAdd} />
      <AuthButton page="UserManage" action="user:edit" title="编辑" onPress={handleEdit} />
      <AuthButton page="UserManage" action="user:delete" mode="disabled" title="删除" onPress={handleDelete} />
    </View>
  );
}
```

这个设计的好处是将权限判断逻辑完全封装在AuthButton组件内部，业务代码只需要声明需要的权限即可。如果权限策略需要调整（比如从隐藏改为禁用），只需要修改AuthButton组件的mode参数，不需要改各处业务代码。这种声明式的权限控制方式比命令式的if-else判断更清晰、更易维护。

### 11.6.4 新增/编辑/删除按钮权限控制

在实际业务页面中，按钮权限控制的典型场景是CRUD（Create Read Update Delete，增删改查）操作。来看一个完整的用户管理页面示例，这个页面包含了列表展示、新增、编辑、删除等典型操作按钮：

```tsx
function UserManageScreen() {
  const { can } = usePermission('UserManage');

  const renderActionBar = () => (
    <View style={styles.actionBar}>
      {can('user:add') && (
        <TouchableOpacity style={styles.btn} onPress={handleAdd}>
          <Text>新增用户</Text>
        </TouchableOpacity>
      )}
      {can('user:export') && (
        <TouchableOpacity style={styles.btn} onPress={handleExport}>
          <Text>导出数据</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const renderListItem = (item) => (
    <View style={styles.row}>
      <Text>{item.username}</Text>
      <View style={styles.rowActions}>
        {can('user:edit') && (
          <TouchableOpacity onPress={() => handleEdit(item)}>
            <Text>编辑</Text>
          </TouchableOpacity>
        )}
        {can('user:delete') && (
          <TouchableOpacity onPress={() => handleDelete(item)}>
            <Text>删除</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  return (
    <FlatList
      ListHeaderComponent={renderActionBar}
      data={userList}
      renderItem={({ item }) => renderListItem(item)}
    />
  );
}
```

注意这里的设计细节：页面顶部的操作栏只渲染有权限的按钮，列表项中的编辑和删除按钮也各自独立判断权限。这样即使某个角色有编辑权限但没有删除权限，列表中只会显示编辑按钮而不会显示删除按钮。每个操作按钮的权限判断是独立的，不存在"有编辑权限就自动有删除权限"这种隐含逻辑，权限粒度精确到每个操作。

### 11.6.5 无权限组件隐藏与禁用处理

无权限的组件有两种处理方式：隐藏和禁用。隐藏是直接不渲染组件，用户看不到这个按钮的存在；禁用是渲染但置灰不可点击，用户能看到按钮但无法操作。

两种方式各有适用场景：

**隐藏**：适用于绝大多数场景。用户看不到不属于自己的功能，界面更干净，不会因为看到一堆灰色按钮而困惑。如果一个普通用户看到页面上有"删除用户"按钮但点不动，他会困惑"我是不是需要什么条件才能用这个功能"。直接隐藏则不会有这个问题。

**禁用**：适用于以下场景——功能即将上线但当前版本未开放、功能需要满足特定条件才能使用（如需要绑定手机号后才能使用）、需要让用户知道有这个功能但当前无权限使用。禁用模式的按钮可以配合提示文字说明需要什么条件才能使用。

```tsx
function AuthWrapper({ 
  page, 
  action, 
  mode = 'hide',
  disabledTip,
  children 
}) {
  const { can } = usePermission(page);
  const hasPermission = can(action);

  if (hasPermission) return <>{children}</>;

  if (mode === 'hide') return null;

  if (mode === 'disabled') {
    return (
      <View style={{ opacity: 0.4 }}>
        {React.cloneElement(children, { disabled: true })}
        {disabledTip && <Text style={styles.tip}>{disabledTip}</Text>}
      </View>
    );
  }

  return null;
}
```

使用示例：

```tsx
// 隐藏模式（默认）
<AuthWrapper page="UserManage" action="user:delete">
  <TouchableOpacity onPress={handleDelete}>
    <Text>删除</Text>
  </TouchableOpacity>
</AuthWrapper>

// 禁用模式
<AuthWrapper page="UserManage" action="user:export" mode="disabled" disabledTip="需要管理员权限">
  <TouchableOpacity onPress={handleExport}>
    <Text>导出数据</Text>
  </TouchableOpacity>
</AuthWrapper>
```

整个权限系统的完整架构回顾：

```
后端签发Token -> 客户端加密存储 -> 请求拦截器自动携带Token
                                      |
                                      v
                              后端验证Token -> 返回权限数据
                                      |
                                      v
                        客户端存储权限 -> 路由守卫检查页面权限
                                      |
                                      v
                              页面内按钮级权限控制
                              (隐藏/禁用两种模式)
```

这个架构从Token签发到按钮权限控制，形成了一个完整的权限闭环。每一层都有明确的职责边界：Token层负责身份认证，路由层负责页面访问控制，按钮层负责操作权限控制。三层防线环环相扣，任何一层都不会单独成为安全漏洞——即使某一层被绕过，下一层依然能拦住未授权的访问。

**企业级登录鉴权方案核心清单**：

**后端清单**：
- [ ] 用户表包含password_hash、token_version、status安全字段
- [ ] 密码使用bcrypt哈希存储，成本因子不低于10
- [ ] 登录接口统一错误提示防止账号枚举
- [ ] 登录接口接入频率限制（IP+账号双维度）
- [ ] 双Token签发：AccessToken 2h + RefreshToken 30d
- [ ] Token中包含tokenVersion字段支持主动失效
- [ ] 401响应区分Token过期和Token无效
- [ ] 刷新接口支持RefreshToken轮换（旧的失效返回新的）

**客户端清单**：
- [ ] Token使用EncryptedStorage/Keychain存储
- [ ] 请求拦截器自动携带Authorization头
- [ ] 并发刷新控制（Promise锁机制）
- [ ] 强制退出登录流程（清Token+清状态+跳登录页）
- [ ] APP启动时恢复登录态
- [ ] 路由守卫拦截未登录访问
- [ ] 白名单页面配置（登录/注册/隐私政策等）
- [ ] 深链接直达处理（未登录先跳登录页再回跳）
- [ ] 已登录用户反向拦截（不显示登录页）
- [ ] 按钮级权限组件封装（隐藏+禁用双模式）
- [ ] 退出登录清空所有本地数据（Token+缓存+状态）

**踩坑清单**：

- bcrypt的cost factor不要超过12，否则登录接口高并发时CPU会打满
- bcrypt有72字节输入限制，超长密码会被截断
- AsyncStorage绝对不能用来存储Token，明文存储等于没加密
- 并发刷新必须用Promise锁控制，否则RefreshToken会被消费多次
- 退出登录时后端接口失败不能阻断本地清理流程
- 导航跳转前必须检查navigationRef.isReady()，否则启动初期会报错
- 权限数据加载失败时要有兜底策略，不能让所有按钮都消失
- WebView的cookie在退出登录时需要手动清除
- 深链接直达需要处理未登录场景，否则会白屏
- 已登录用户访问登录页需要重定向，否则体验差
- 动态权限数据需要本地缓存兜底，否则弱网时权限判断全false
- Token的Payload不要放敏感信息，Base64不是加密

**官方文档参考链接**：

- JWT官方文档：https://jwt.io
- jsonwebtoken Node.js库：https://github.com/auth0/node-jsonwebtoken
- bcrypt Node.js库：https://github.com/kelektiv/node.bcrypt.js
- react-native-encrypted-storage：https://github.com/emeraldsanto/react-native-encrypted-storage
- react-native-keychain：https://github.com/oblador/react-native-keychain
- React Navigation导航：https://reactnavigation.org/docs/navigating-without-navigation-prop
- Axios拦截器文档：https://axios-http.com/docs/interceptors
- Zustand状态管理：https://github.com/pmndrs/zustand
- Joi参数校验：https://joi.dev

这些资源在后续章节中也会被引用，建议加入书签。遇到鉴权问题时，第一时间查阅官方文档，官方文档的准确性和时效性通常优于任何第三方教程。特别是JWT和bcrypt的官方文档，对算法细节和安全注意事项有最权威的说明。

怕浪猫说：登录鉴权是移动端架构的安全基石。从Session到JWT的演进，不是技术潮流的更替，而是移动端场景对无状态鉴权的必然选择。双Token机制解决了安全性与体验的平衡，路由守卫和按钮级权限控制构建了从页面到操作的全链路权限闭环。记住一句话：鉴权做的越早，后期越省心；权限做的越细，线上越安稳。别等出了安全事故才回来补课，那时候代价可能是十倍甚至百倍。安全这件事，看不见摸不着，但一旦出事就是大事。从Token签发到路由拦截到按钮控制，三层防线环环相扣，缺一不可。

如果你觉得这篇文章对你有帮助，建议收藏起来反复参考。上面的清单和踩坑列表是怕浪猫用真金白银的线上事故换来的经验，每次遇到鉴权问题翻出来对照一遍，能帮你少走很多弯路。也欢迎在评论区分享你遇到的鉴权坑，一起交流讨论。关注我追更这个系列，下一章我们进入原生混合开发的深水区。

**系列进度 11/16**

怕浪猫说：安全这件事，看不见摸不着，但一旦出事就是大事。从Token签发到路由拦截到按钮控制，三层防线环环相扣，缺一不可。跟着怕浪猫，16章带你从零到一拿下RN全栈开发，鉴权的坑我替你踩过了，你只需要跟着走。我们下一章见。

下一章预告：第12章《RN原生混合开发与双端原生模块适配》将深入讲解RN与原生代码的通信机制，涵盖Native Modules开发、Bridge通信原理、TurboModules新架构、原生UI组件封装、平台差异化适配方案，以及第三方原生SDK（Software Development Kit，软件开发工具包）集成实战。从"会用RN组件"到"能写原生模块"，完成从纯JS开发到原生混合开发的进阶。

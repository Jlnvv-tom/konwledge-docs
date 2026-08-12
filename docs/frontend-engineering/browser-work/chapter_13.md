# 第13章 QUIC 协议与 TLS

> QUIC 把传输层和加密层合二为一，用 UDP 替代 TCP，在用户空间重新实现了一遍可靠性、拥塞控制和加密。这不是重复造轮子，而是 30 年 TCP 历史包袱逼出来的彻底重写。

我是怕浪猫，上期讲了 HTTP 三个版本的演进，今天进入第 13 章：QUIC 协议与 TLS 安全机制。这一章会拆解 QUIC 的包格式、流的多路复用机制、0-RTT 连接恢复的原理，以及 TLS 1.3 的密码套件选择和证书链验证。

## 13.1 QUIC 协议设计

### 13.1.1 为什么需要在用户空间重写传输层

TCP 是 1970 年代设计的协议，运行在操作系统内核空间。修改 TCP 需要更新操作系统内核，这在服务器端可能需要数年时间，在客户端可能需要更久。TCP 的每一个改进都受制于内核更新周期。

QUIC 选择在用户空间基于 UDP 实现可靠性传输。这意味着浏览器可以随版本更新迭代 QUIC 算法，不需要等待操作系统更新。

| 限制 | TCP | QUIC |
|------|-----|------|
| 实现位置 | 内核空间 | 用户空间 |
| 更新方式 | 需要内核更新 | 随浏览器更新 |
| 迭代速度 | 数年 | 数周 |
| 定制性 | 低 | 高 |
| 中间盒干扰 | 严重（NAT/防火墙修改 TCP 头） | 轻微（UDP 通常不被修改） |

> 中间盒（Middlebox）是 TCP 的另一个噩梦。NAT 设备、防火墙、负载均衡器都会修改 TCP 头部，导致新的 TCP 特性在通过中间盒后失效。QUIC 基于 UDP，中间盒通常只做 NAT 转发，不修改 UDP 负载，QUIC 的特性可以完整传递。

### 13.1.2 QUIC 包格式

QUIC 的包格式与 TCP 完全不同。QUIC 包分为 Long Header（长头部）和 Short Header（短头部）两种。

```
QUIC 包格式

Long Header（用于连接建立阶段）：
┌─────────────────────────────────────┐
│ Header Form (1 bit) = 1             │
│ Fixed Bit (1 bit) = 1               │
│ Long Packet Type (2 bits)           │
│ Reserved Bits (2 bits)              │
│ Packet Number Length (2 bits)       │
│ Version (32 bits)                   │
│ Destination Connection ID (0-160)   │
│ Source Connection ID (0-160)        │
│ Packet Number (1-4 bytes)           │
│ Payload (加密)                       │
└─────────────────────────────────────┘

Short Header（用于数据传输阶段）：
┌─────────────────────────────────────┐
│ Header Form (1 bit) = 0             │
│ Fixed Bit (1 bit) = 1               │
│ Spin Bit (1 bit)                    │
│ Reserved Bits (2 bits)              │
│ Packet Number Length (2 bits)       │
│ Destination Connection ID (0-160)   │
│ Packet Number (1-4 bytes)           │
│ Payload (加密)                       │
└─────────────────────────────────────┘
```

| 包类型 | 使用阶段 | 头部大小 | 说明 |
|--------|---------|---------|------|
| Initial | 连接建立 | 大 | 含 TLS ClientHello |
| 0-RTT | 会话恢复 | 中 | 0-RTT 数据 |
| Handshake | TLS 握手 | 中 | TLS 握手消息 |
| Retry | 反射攻击防护 | 中 | 服务器验证客户端 |
| Short | 数据传输 | 小 | 日常数据传输 |

### 13.1.3 QUIC 的流（Stream）模型

QUIC 的流是独立的双向或单向数据通道。每个流有自己的发送缓冲区和接收缓冲区，流之间互不阻塞。

```
QUIC 流模型

连接（Connection）
  ├─ Stream 0（双向，客户端发起）
  │   ├─ 客户端 → 服务器（请求数据）
  │   └─ 服务器 → 客户端（响应数据）
  ├─ Stream 4（双向，客户端发起）
  │   ├─ 客户端 → 服务器
  │   └─ 服务器 → 客户端
  ├─ Stream 1（单向，服务器发起）
  │   └─ 服务器 → 客户端
  └─ ...

流 ID 的含义：
  最低 2 位：00=双向, 01=单向
  次低 1 位：0=客户端发起, 1=服务器发起
  
  流 0：双向 + 客户端发起（HTTP 请求/响应）
  流 1：单向 + 客户端发起
  流 2：双向 + 服务器发起
  流 3：单向 + 服务器发起
```

| 流类型 | ID 最低位 | 发起方 | 方向 |
|--------|----------|--------|------|
| 双向客户端流 | 0b00 | 客户端 | 双向 |
| 单向客户端流 | 0b01 | 客户端 | 单向 |
| 双向服务器流 | 0b10 | 服务器 | 双向 |
| 单向服务器流 | 0b11 | 服务器 | 单向 |

## 13.2 QUIC 的可靠性机制

### 13.2.1 包号与确认

QUIC 使用单调递增的包号（Packet Number），重传的包使用新的包号。这与 TCP 不同：TCP 重传使用相同的序列号。

```
QUIC vs TCP 包号

TCP：
  发送包1 → 丢失 → 重传包1 → ACK 1
  问题：ACK 1 是对原始包1的确认还是重传包1的确认？
  （重传歧义）

QUIC：
  发送包1 → 丢失 → 重传包2（新包号）→ ACK 2
  ACK 2 明确是对重传包的确认
  → 精确 RTT 测量
```

QUIC 的 ACK 帧支持 SACK（Selective Acknowledgment，选择性确认），可以确认不连续的包范围。QUIC 的 ACK 比 TCP 的 SACK 更灵活，支持多个确认范围。

### 13.2.2 丢包检测

QUIC 的丢包检测算法基于两个信号：重复 ACK 和超时。

```
QUIC 丢包检测

方式1：基于包号差距
  发送包1, 2, 3, 4, 5
  收到 ACK 1, ACK 3, ACK 4, ACK 5
  → 包2未确认，且后续包已确认
  → 判定包2丢失 → 立即重传

方式2：基于超时
  发送包1 → 等待 PTO（Probe Timeout）
  超时未收到 ACK → 重传
```

| 丢包检测方式 | 触发条件 | 延迟 |
|------------|---------|------|
| 包号差距 | 后续包已确认，当前包未确认 | 低 |
| PTO 超时 | 超过探测超时时间 | 中 |
| 重复 ACK | 收到多个重复确认 | 低 |

### 13.2.3 拥塞控制

QUIC 默认使用 BBRv2 拥塞控制算法，也支持 CUBIC。由于在用户空间实现，QUIC 可以同时为不同连接使用不同算法。

| 算法 | 原理 | 优势 | 劣势 |
|------|------|------|------|
| CUBIC | 基于丢包的窗口调整 | 兼容性好 | 高延迟下性能差 |
| BBR | 基于带宽和 RTT | 高延迟下性能好 | 与 CUBIC 共存时激进 |
| BBRv2 | BBR 改进版 | 更公平 | 实现复杂 |

## 13.3 0-RTT 连接恢复

### 13.3.1 0-RTT 的原理

0-RTT（Zero Round-Trip Time）连接恢复是 QUIC 的关键特性。当客户端与服务器建立过连接后，后续连接可以在第一个数据包中携带应用数据，不需要等待握手完成。

```
0-RTT 连接恢复流程

首次连接：
  Client                                    Server
    │  Initial（ClientHello + 密钥共享）       │
    │ ──────────────────────────────────────► │
    │                                         │
    │  Initial（ServerHello + 证书 + Finished）│
    │ ◄────────────────────────────────────── │
    │                                         │
    │  1-RTT 数据                              │
    │ ──────────────────────────────────────► │
    │                                         │
    │  服务器返回 PSK（Pre-Shared Key）         │
    │  客户端保存 PSK 和服务器配置               │

再次连接（0-RTT）：
  Client                                    Server
    │  0-RTT（ClientHello + PSK + 应用数据）   │
    │ ──────────────────────────────────────► │
    │                                         │
    │  服务器验证 PSK → 立即处理应用数据        │
    │  返回响应                                │
    │ ◄────────────────────────────────────── │
    │                                         │
    │  0-RTT！数据在握手前就发送了              │
```

### 13.3.2 0-RTT 的安全限制

0-RTT 数据有重放攻击（Replay Attack）的风险。攻击者可以截获 0-RTT 数据包，重复发送给服务器。因此 0-RTT 数据只能用于幂等操作。

| 安全限制 | 说明 | 原因 |
|---------|------|------|
| 仅幂等请求 | GET、HEAD 允许 | 重放不影响结果 |
| 禁止非幂等 | POST、PUT、DELETE 禁止 | 重放可能导致重复操作 |
| 服务器验证 | 服务器需做重放检测 | 防止攻击 |
| 有效期限制 | PSK 有过期时间 | 限制重放窗口 |

> 0-RTT 是性能和安全的权衡。它把首次连接的 1-RTT 优化到 0，但引入了重放攻击风险。Chrome 只对 GET 请求使用 0-RTT，POST 等非幂等请求必须等握手完成。

## 13.4 TLS 1.3 密码学

### 13.4.1 密码套件

TLS 1.3 精简了密码套件（Cipher Suite），移除了所有不安全的算法，只保留经过验证的现代密码学算法。

| 密码套件 | 密钥交换 | 认证 | 加密 | MAC |
|---------|---------|------|------|-----|
| TLS_AES_128_GCM_SHA256 | ECDHE | RSA/ECDSA | AES-128-GCM | SHA256 |
| TLS_AES_256_GCM_SHA384 | ECDHE | RSA/ECDSA | AES-256-GCM | SHA384 |
| TLS_CHACHA20_POLY1305_SHA256 | ECDHE | RSA/ECDSA | ChaCha20-Poly1305 | SHA256 |

TLS 1.2 有数十种密码套件组合，很多组合不安全。TLS 1.3 只保留了 3 种，所有都是 AEAD（Authenticated Encryption with Associated Data，认证加密）模式，同时提供加密和完整性保护。

### 13.4.2 密钥交换

TLS 1.3 使用 ECDHE（Elliptic Curve Diffie-Hellman Ephemeral，椭圆曲线 Diffie-Hellman 临时密钥交换）进行密钥交换。ECDHE 提供前向安全（Forward Secrecy）：即使服务器的私钥泄露，之前的通信内容也无法解密。

```
ECDHE 密钥交换（简化）

客户端                             服务器
  │  生成临时密钥对                    │  生成临时密钥对
  │  (client_priv, client_pub)       │  (server_priv, server_pub)
  │                                  │
  │  ClientHello + client_pub        │
  │ ──────────────────────────────►  │
  │                                  │
  │  ServerHello + server_pub        │
  │ ◄──────────────────────────────  │
  │                                  │
  │  共享密钥 = ECDH(client_priv, server_pub) │
  │  = ECDH(server_priv, client_pub)          │
  │                                           │
  │  两侧计算出相同的共享密钥                    │
  │  临时密钥对用完即弃 → 前向安全               │
```

### 13.4.3 证书链验证

TLS 握手时，服务器发送证书链。浏览器需要验证证书链的完整性和可信度。

```
证书链验证

浏览器                                服务器
  │                                     │
  │  ClientHello                        │
  │ ─────────────────────────────────►  │
  │                                     │
  │  Certificate 证书链：               │
  │  ┌──────────────────────┐          │
  │  │ 服务器证书            │          │
  │  │ (example.com)        │          │
  │  │ 签发者: Let's Encrypt │          │
  │  └──────────┬───────────┘          │
  │             │ 签名                   │
  │  ┌──────────▼───────────┐          │
  │  │ 中间证书              │          │
  │  │ (Let's Encrypt R3)   │          │
  │  │ 签发者: ISRG Root X1  │          │
  │  └──────────┬───────────┘          │
  │             │ 签名                   │
  │  ┌──────────▼───────────┐          │
  │  │ 根证书                │          │
  │  │ (ISRG Root X1)       │          │
  │  │ 自签名（根 CA）       │          │
  │  └──────────────────────┘          │
  │ ◄─────────────────────────────────  │
  │                                     │
  │  验证步骤：                          │
  │  1. 服务器证书是否由中间证书签发？ ✓  │
  │  2. 中间证书是否由根证书签发？ ✓     │
  │  3. 根证书是否在信任库中？ ✓        │
  │  4. 证书是否过期？ 未过期 ✓         │
  │  5. 域名是否匹配？ example.com ✓   │
  │  6. 证书是否被吊销？（OCSP/CRL） ✓ │
  │  → 验证通过                         │
```

| 验证步骤 | 检查内容 | 失败后果 |
|---------|---------|---------|
| 签名链 | 每个证书由上一级签发 | 不可信 |
| 根证书 | 根 CA 在信任库中 | 不可信 |
| 有效期 | notBefore ~ notAfter | 过期警告 |
| 域名匹配 | SAN 或 CN 匹配 | 域名不匹配 |
| 吊销状态 | OCSP 或 CRL | 安全风险 |

### 13.4.4 OCSP 与证书吊销

OCSP（Online Certificate Status Protocol，在线证书状态协议）用于实时检查证书是否被吊销。Chrome 使用 OCSP Stapling（OCSP 装订）技术，让服务器在 TLS 握手时附带 OCSP 响应，避免浏览器额外请求 OCSP 服务器。

| 吊销检查方式 | 说明 | 优缺点 |
|------------|------|--------|
| CRL | 下载吊销列表 | 列表可能很大 |
| OCSP | 实时查询吊销状态 | 额外请求，隐私问题 |
| OCSP Stapling | 服务器附带 OCSP 响应 | 最佳方案 |
| CRLite | Firefox 的压缩吊销列表 | Chrome 不使用 |

> Chrome 使用 CRLSets 作为证书吊销的快速检查机制。CRLSets 是 Chrome 预打包的高优先级吊销证书列表，随浏览器更新分发。对于不在 CRLSets 中的证书，Chrome 依赖 OCSP Stapling 检查。

## 13.5 QUIC 的连接迁移详解

### 13.5.1 Connection ID 的作用

QUIC 的 Connection ID 是连接迁移的关键。客户端切换网络时，IP 地址变了，但 Connection ID 不变，服务器通过 Connection ID 识别这是同一个连接。

```
连接迁移详细流程

时刻 T1（WiFi 网络）：
  客户端 IP: 192.168.1.100
  Connection ID: 0x12345678
  数据流: 正在下载文件

时刻 T2（切换到 4G）：
  客户端 IP: 10.0.0.50（新 IP）
  Connection ID: 0x12345678（不变）
  
  客户端从新 IP 发送数据包
  包中携带 Connection ID: 0x12345678
  
  服务器收到包：
  ├─ 识别 Connection ID → 这是之前的连接
  ├─ 更新客户端 IP 为 10.0.0.50
  └─ 继续传输数据
  
  连接不中断，文件继续下载
```

### 13.5.2 路径验证

连接迁移时，服务器需要验证新路径是否属于同一客户端，防止攻击者劫持连接。

```
路径验证

客户端从新 IP 发送数据
  │
  ▼
服务器收到，发送 PATH_CHALLENGE（随机数）
  │
  ▼
客户端收到 PATH_CHALLENGE
  回复 PATH_RESPONSE（相同的随机数）
  │
  ▼
服务器验证 PATH_RESPONSE
  ├─ 匹配 → 路径有效，继续传输
  └─ 不匹配 → 路径无效，拒绝迁移
```

## 13.6 QUIC 的流量控制

QUIC 有两级流量控制：流级（Stream Level）和连接级（Connection Level）。

| 流量控制级别 | 说明 | 目的 |
|------------|------|------|
| 流级 | 限制单个流的未确认数据量 | 防止单个流占满缓冲区 |
| 连接级 | 限制所有流的总未确认数据量 | 防止连接耗尽内存 |

流量控制通过 WINDOW_UPDATE 帧实现。接收端根据自己的处理能力，告诉发送端可以发送多少数据。

> QUIC 的两级流量控制比 TCP 更精细。TCP 只有连接级流量控制（通过窗口大小），没有流级控制。在 HTTP/2 中，流级流量控制由 HTTP/2 层实现，但 HTTP/2 的流共享一个 TCP 连接，TCP 不知道流的概念，流量控制效率不如 QUIC。

## 13.7 QUIC 的错误处理与连接关闭

### 13.7.1 连接错误码

QUIC 使用应用层错误码和传输层错误码来报告不同类型的错误。错误码是 62 位的整数，由应用协议（如 HTTP/3）定义含义。

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| 传输层错误 | QUIC 协议错误 | 流ID冲突、帧格式错误 |
| 应用层错误 | HTTP/3 等应用错误 | 404、500 等 |
| 无错误关闭 | 优雅关闭 | GOAWAY 帧 |

### 13.7.2 优雅关闭

QUIC 使用 CONNECTION_CLOSE 帧关闭连接。发送 CONNECTION_CLOSE 后，连接立即终止，所有未完成的数据流被取消。

对于需要优雅关闭的场景，HTTP/3 定义了 GOAWAY 帧，通知对端不再接受新的请求，但允许已有请求完成。这比 TCP 的 FIN 关闭更明确，不会出现 TIME_WAIT 等模糊状态。

## 13.8 DNS 解析的完整递归流程

### 13.8.1 从浏览器到根域名服务器的完整路径

DNS 递归查询是一个多层级的过程。当本地缓存全部未命中时，DNS 查询会从根域名服务器开始，逐级向下查找。

```
DNS 递归查询完整流程

用户输入 www.api.example.com
  │
  ▼
1. 浏览器 DNS 缓存检查
   ├─ 命中 → 返回 IP (0ms)
   └─ 未命中 ↓

2. 操作系统 DNS 缓存检查
   ├─ 命中 → 返回 IP (1ms)
   └─ 未命中 ↓

3. hosts 文件检查
   ├─ 命中 → 返回 IP (1ms)
   └─ 未命中 ↓

4. 本地 DNS 服务器 (递归解析器)
   ├─ 缓存命中 → 返回 IP (5-20ms)
   └─ 未命中 → 开始递归查询 ↓

5. 查询根域名服务器 (.)
   ├─ 13 组根服务器 (a.root-servers.net ~ m.root-servers.net)
   ├─ 返回 .com TLD 服务器的 NS 记录
   └─ 耗时: 20-100ms (取决于根服务器位置)

6. 查询 .com 顶级域名服务器 (TLD)
   ├─ 返回 example.com 权威服务器的 NS 记录
   └─ 耗时: 10-50ms

7. 查询 example.com 权威域名服务器
   ├─ 返回 www.example.com 的 A 记录
   │   IP: 93.184.216.34
   │   TTL: 3600
   └─ 耗时: 10-50ms

8. 递归解析器缓存结果并返回给浏览器
   ├─ 总耗时: 50-250ms (首次查询)
   └─ 后续查询命中缓存: < 5ms
```

### 13.8.2 DNS 缓存层次详解

DNS 缓存分布在多个层级，每一层都有自己的缓存策略和 TTL 管理。

```
DNS 缓存层次

层级1: 浏览器 DNS 缓存
  ├─ Chrome 内置 DNS 缓存 (chrome://net-internals/#dns)
  ├─ 缓存时间: 通常等于 TTL，但不完全依赖
  ├─ 容量限制: 最多缓存约 1000 条记录
  ├─ 异步刷新: 即将过期时后台刷新
  └─ 特点: 进程级别，关闭浏览器后清除

层级2: 操作系统 DNS 缓存
  ├─ Windows: DNS Client 服务 (dnscache)
  ├─ macOS: mDNSResponder
  ├─ Linux: systemd-resolved 或 nscd
  ├─ 缓存时间: 遵循 TTL
  └─ 特点: 系统级别，所有应用共享

层级3: 路由器 DNS 缓存
  ├─ 家用路由器通常有 DNS 代理/缓存
  ├─ 缓存时间: 可能不完全遵循 TTL
  └─ 特点: 局域网内共享

层级4: ISP DNS 服务器缓存
  ├─ ISP 的递归解析器缓存
  ├─ 缓存时间: 通常遵循 TTL，但可能修改
  ├─ 容量大: 可缓存数百万条记录
  └─ 特点: 同一 ISP 的用户共享

层级5: 权威域名服务器
  ├─ 不缓存，返回权威记录
  └─ 设置 TTL 值供下游缓存
```

### 13.8.3 DNS 预解析的实现机制

Chrome 的 DNS 预解析（DNS Prefetching）分为显式预解析和隐式预解析两种。

```
显式预解析 (开发者指定)
  <link rel="dns-prefetch" href="//api.example.com">
  <link rel="dns-prefetch" href="//cdn.example.com">
  ├─ 解析时机: HTML 解析到此标签时
  ├─ 优先级: 低于页面资源加载
  └─ 效果: 提前完成 DNS 查询

隐式预解析 (Chrome 自动学习)
  ├─ Chrome 记录用户常访问的域名
  ├─ 在页面加载时预测性预解析
  ├─ 基于:
  │   ├─ 页面中的超链接
  │   ├─ 页面中的资源 URL
  │   ├─ 历史浏览模式
  │   └─ 用户输入的 URL
  └─ 效果: 减少后续导航的 DNS 延迟

preconnect (更激进的优化)
  <link rel="preconnect" href="//api.example.com">
  ├─ DNS + TCP + TLS 全部提前建立
  ├─ 比 dns-prefetch 开销大
  └─ 效果更好 (节省全部连接时间)
```

## 13.9 DNS over HTTPS (DoH) 与 DNS over TLS (DoT) 对比

### 13.9.1 DoH vs DoT 详细对比

DoH 和 DoT 都是加密 DNS 查询的方案，但传输方式和端口不同。

```
DoH vs DoT 协议栈

传统 DNS:
  浏览器 → UDP 53 → DNS 服务器
  明文传输

DoT (DNS-over-TLS):
  浏览器 → TLS → TCP 853 → DNS 服务器
  加密传输，专用端口 853

DoH (DNS-over-HTTPS):
  浏览器 → TLS → TCP 443 → DoH 服务器
  加密传输，使用标准 HTTPS 端口 443
  DNS 查询封装在 HTTP/2 或 HTTP/3 请求中
```

| 特性 | 传统 DNS | DoT | DoH |
|------|---------|-----|-----|
| 传输协议 | UDP/TCP | TLS over TCP | HTTPS |
| 端口 | 53 | 853 | 443 |
| 加密 | 否 | 是 | 是 |
| 防篡改 | 否 | 是 | 是 |
| 防探测 | 否 | 部分 | 是 |
| 防封锁 | 不适用 | 较难（可封锁 853） | 很难（443 不可区分） |
| 部署 | 原生 | 需配置 | 需配置 |
| 浏览器支持 | 原生 | 部分 | Chrome/Firefox |

DoH 的优势在于使用 443 端口，与普通 HTTPS 流量无法区分。这意味着网络管理员无法通过封锁端口来阻止 DoH，只能在应用层深度检测（DPI）来识别。但 DPI 会增加性能开销，且不准确。

### 13.9.2 DNSSEC 验证

DNSSEC（Domain Name System Security Extensions，DNS 安全扩展）通过数字签名验证 DNS 响应的真实性。

```
DNSSEC 验证流程

1. 请求 www.example.com 的 A 记录
   服务器返回: A 记录 + RRSIG (签名)

2. 验证签名需要 DNSKEY
   请求 example.com 的 DNSKEY
   服务器返回: DNSKEY + RRSIG

3. 验证 example.com 的签名需要上级 DS 记录
   请求 .com 的 DS 记录
   服务器返回: DS (Delegation Signer) + RRSIG

4. 验证 .com 的签名需要根的 DNSKEY
   请求根的 DNSKEY (信任锚)
   根 DNSKEY 是预置的可信公钥

5. 从根向下验证签名链:
   根 → .com → example.com → www.example.com
   全部签名验证通过 → DNS 响应可信
```

DNSSEC 不加密 DNS 查询（它不是 DoH 的替代品），但确保查询结果未被篡改。DNSSEC + DoH 的组合提供了加密 + 完整性的全面保护。

## 13.10 连接池与 Socket 复用

### 13.10.1 Chrome 连接池的内部管理

Chrome 的连接池管理是一个复杂的系统，需要处理多种协议、超时、限制等。

```
Chrome 连接池架构

Network Service 进程
  ├─ Socket Pool Manager
  │   ├─ HTTP/1.1 连接池 (per-host)
│   │   ├─ 最大连接数: 6 per host
  │   │   ├─ 总最大连接数: 255
  │   │   ├─ 空闲超时: ~60秒
  │   │   └─ 连接复用: keep-alive
  │   │
  │   ├─ HTTP/2 连接池 (per-origin)
  │   │   ├─ 最大连接数: 1 per origin (多路复用)
  │   │   ├─ 最大并发流: 100 per connection
  │   │   └─ 连接复用: 多个请求共享
  │   │
  │   ├─ HTTP/3 (QUIC) 连接池
  │   │   ├─ 最大连接数: 1 per origin
  │   │   ├─ 最大并发流: 100+ per connection
  │   │   └─ 连接复用: 多个请求共享
  │   │
  │   └─ WebSocket 连接池
  │       ├─ 持久连接
  │       └─ 无最大限制 (受系统资源限制)
  │
  └─ Proxy Pool (代理连接池)
      └─ HTTP/SOCKS 代理连接管理
```

### 13.10.2 Socket 复用的条件

并非所有连接都可以被复用。连接池在复用连接前会检查多个条件。

| 检查条件 | 说明 | 失败处理 |
|--------|------|--------|
| 连接是否活跃 | TCP keep-alive 探测 | 创建新连接 |
| 连接是否空闲 | 没有正在进行的请求 | 等待或新建 |
| 协议是否匹配 | HTTP/1.1 vs HTTP/2 | 新建对应协议连接 |
| 域名是否匹配 | 同一 host:port | 新建连接 |
| 是否超过最大连接数 | per-host 或全局限制 | 排队等待 |
| 是否超过空闲超时 | 通常 60 秒 | 关闭并新建 |
| SSL 证书是否有效 | 证书未过期 | 新建连接 |

> 连接池复用是减少网络延迟的关键优化。一个已建立的 HTTPS 连接复用，可以节省 1-2 RTT 的 TCP+TLS 握手时间。对于 100ms RTT 的网络，这意味着节省 100-200ms。HTTP/2 的多路复用进一步减少了需要的连接数，一个连接可以处理所有同源请求。

## 本章核心知识总结

| 知识模块 | 核心内容 | 优势 |
|---------|---------|------|
| QUIC 包格式 | Long/Short Header | 紧凑高效 |
| 流模型 | 独立双向/单向流 | 无流间阻塞 |
| 包号 | 单调递增，重传用新号 | 精确 RTT |
| 0-RTT | 会话恢复零延迟 | 首字节时间最优 |
| TLS 1.3 | 3 种 AEAD 密码套件 | 精简安全 |
| 证书链 | 根 CA → 中间 CA → 服务器证书 | 信任链 |
| 连接迁移 | Connection ID 不变 | 网络切换不断连 |

觉得有用？收藏起来，下次和同事讨论网络协议时这就是你的弹药库。

你对 QUIC 和 HTTP/3 的实际使用体验怎么样？评论区聊聊。

关注怕浪猫，下期我们进入浏览器安全机制，讲同源策略与 CORS。系列进度 13/24。

下期预告：第 14 章「同源策略与 CORS」。我们会拆解同源策略的精确定义、CORS（Cross-Origin Resource Sharing，跨域资源共享）的预检请求机制、以及 CSRF（Cross-Site Request Forgery，跨站请求伪造）的防护方案。怕浪猫下期见。

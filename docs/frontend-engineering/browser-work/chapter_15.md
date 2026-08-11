# 第15章 浏览器沙箱与站点隔离

> 浏览器是用户接触恶意代码的第一线。沙箱让即使渲染进程被攻破，恶意代码也无法逃逸到操作系统。站点隔离则让不同网站的数据互不可见，即使 Spectre 漏洞也无法偷取。

我是怕浪猫，上期讲了同源策略和 CORS，今天进入第 15 章：浏览器沙箱与站点隔离。这一章拆解 Chrome 的多进程沙箱架构、站点隔离（Site Isolation）的实现原理，以及 Spectre/Meltdown 漏洞如何改变了浏览器安全设计。

## 15.1 沙箱模型

### 15.1.1 为什么需要沙箱

浏览器是一个巨大的攻击面。它每天解析和执行来自互联网的 HTML、CSS、JavaScript、WebAssembly 等内容。如果这些内容的解析器有漏洞，攻击者可能通过恶意网页执行任意代码。

沙箱（Sandbox）的核心思想是：即使渲染进程被攻破，攻击者也无法直接访问操作系统资源。

```
沙箱防御模型

攻击者目标：
  恶意网页 → 利用渲染引擎漏洞 → 控制渲染进程 → 攻破操作系统

沙箱防御：
  恶意网页 → 利用渲染引擎漏洞 → 控制渲染进程
    ↓
    沙箱限制：
    ✗ 不能读写文件系统
    ✗ 不能执行系统命令
    ✗ 不能访问网络（除受限 HTTP）
    ✗ 不能访问其他进程内存
    ✗ 不能访问硬件设备
    ↓
    攻击者需要再利用一个沙箱逃逸漏洞
    才能接触到操作系统
```

### 15.1.2 沙箱的实现机制

Chrome 在不同操作系统上使用不同的沙箱实现机制，但核心原理相同：限制进程权限。

| 操作系统 | 沙箱机制 | 说明 |
|---------|---------|------|
| Windows | Restricted Token + Job Object | 降低进程权限令牌 |
| macOS | Seatbelt（sandbox-exec） | 内核级 MAC（Mandatory Access Control） |
| Linux | Seccomp-BPF + Namespaces | 系统调用过滤 + 命名空间隔离 |
| Android | Isolated Process | 进程隔离（UID 不同） |

```
Linux Seccomp-BPF 示例（简化）

渲染进程允许的系统调用：
  read()    ✓ 读文件描述符
  write()   ✓ 写文件描述符
  mmap()    ✓ 内存映射
  futex()   ✓ 线程同步
  
渲染进程禁止的系统调用：
  open()    ✗ 不能打开新文件
  socket()  ✗ 不能创建网络套接字
  execve()  ✗ 不能执行新程序
  fork()    ✗ 不能创建新进程
  clone()   ✗ 不能创建新线程（受限）
```

> Seccomp-BPF 是 Linux 沙箱的核心。它通过 BPF（Berkeley Packet Filter，伯克利包过滤器）字节码过滤系统调用，渲染进程只能调用白名单中的系统调用。即使攻击者控制了渲染进程，也无法调用 open() 读取用户文件或调用 execve() 执行恶意程序。

### 15.1.3 沙箱的权限最小化

Chrome 遵循最小权限原则（Principle of Least Privilege），每个进程只拥有完成任务所需的最小权限。

| 进程类型 | 权限 | 说明 |
|---------|------|------|
| 浏览器进程 | 完全权限 | 管理所有资源，唯一不受沙箱限制 |
| 渲染进程 | 最低权限 | 只能渲染页面，不能访问文件/网络 |
| GPU 进程 | 受限权限 | 可访问 GPU 驱动，不能访问文件系统 |
| 网络服务进程 | 受限权限 | 可访问网络，不能访问文件系统 |
| 插件进程 | 受限权限 | 运行扩展，受限的网络访问 |

### 15.1.4 沙箱的局限性与逃逸

沙箱并非完美无缺。沙箱逃逸（Sandbox Escape）是安全研究的重要领域。常见的沙箱逃逸路径包括：

| 逃逸路径 | 原理 | 防护 |
|---------|------|------|
| 内核漏洞 | 利用内核漏洞获取权限 | 及时更新内核 |
| IPC 漏洞 | 利用进程间通信漏洞 | IPC 消息验证 |
| 文件描述符泄漏 | 从父进程继承的 FD | FD 限制 |
| GPU 驱动漏洞 | 利用 GPU 进程的更高权限 | GPU 命令验证 |

Chrome 通过持续的安全审计、漏洞悬赏计划和快速补丁发布来降低沙箱逃逸风险。Pwn2Own 等安全竞赛中，Chrome 沙箱逃逸的奖金通常在数十万美元。

> 沙箱不是银弹。沙箱的安全依赖于操作系统内核的完整性。如果内核有漏洞，沙箱也可能被逃逸。但沙箱大幅提高了攻击成本——攻击者需要同时利用渲染引擎漏洞和沙箱逃逸漏洞才能触及操作系统。

## 15.2 站点隔离（Site Isolation）

### 15.2.1 为什么需要站点隔离

同源策略在 JavaScript 层面限制了跨域访问，但在进程层面，Chrome 2018 年之前所有同标签页的跨域页面共享一个渲染进程。这意味着如果存在 Spectre 等侧信道攻击，恶意页面可以绕过同源策略读取同进程内其他域名的数据。

```
站点隔离前（2018年前）

标签页: https://example.com
  ├─ 主框架: example.com
  ├─ iframe: https://evil.com
  └─ iframe: https://bank.com

三个域名共享一个渲染进程！
如果 evil.com 利用 Spectre 侧信道攻击：
  → 可以读取同进程内 bank.com 的内存
  → 绕过同源策略
```

### 15.2.2 站点隔离的实现

站点隔离确保不同站点（Site）的页面在不同渲染进程中运行。站点的定义是：注册域名（eTLD+1）加上协议。

```
站点隔离后

标签页: https://example.com
  ├─ 主框架: example.com → 渲染进程 A
  ├─ iframe: https://evil.com → 渲染进程 B
  └─ iframe: https://bank.com → 渲染进程 C

三个域名在三个独立进程中！
evil.com 无法通过侧信道读取 bank.com 的内存
进程间内存隔离由操作系统保证
```

| 概念 | 定义 | 示例 |
|------|------|------|
| Origin | 协议+主机+端口 | https://example.com:443 |
| Site | 协议+eTLD+1 | https://example.com |
| eTLD | 有效顶级域名 | com, co.uk, github.io |
| eTLD+1 | eTLD + 下一级 | example.com, example.co.uk |

```
eTLD+1 计算示例

https://www.example.com/page    → Site: example.com
https://api.example.com/data    → Site: example.com（同 Site）
https://example.co.uk/          → Site: example.co.uk
https://foo.github.io/          → Site: foo.github.io
https://bar.github.io/          → Site: bar.github.io（不同 Site）
```

### 15.2.3 跨进程 iframe

站点隔离引入了跨进程 iframe（Out-of-Process iframe，OOPIF）。一个 iframe 可能运行在另一个渲染进程中，但用户看到的仍然是统一的页面。

```
跨进程 iframe 架构

浏览器进程
  ├─ 渲染进程 A（example.com）
  │   ├─ DOM 树: <html>...<iframe src="evil.com">...</html>
  │   ├─ 样式计算、布局、绘制
  │   └─ iframe 占位区域 → 指向进程 B
  │
  ├─ 渲染进程 B（evil.com）
  │   ├─ DOM 树: <html>...evil.com content...</html>
  │   ├─ 独立的样式计算、布局、绘制
  │   └─ 绘制结果 → 传回进程 A 合成
  │
  └─ 合成器线程
      └─ 合并进程 A 和 B 的绘制结果
```

跨进程 iframe 的通信通过浏览器进程中转，确保进程间的数据隔离。浏览器进程负责协调两个渲染进程的布局和绘制，确保 iframe 的尺寸和位置正确。

| 操作 | 非站点隔离 | 站点隔离 |
|------|-----------|---------|
| iframe 布局 | 直接在进程内计算 | 浏览器进程中转协调 |
| iframe 绘制 | 直接在同一画布绘制 | 独立绘制后合成 |
| iframe 事件 | 直接分发 | 通过浏览器进程中转 |
| 内存访问 | 共享内存 | 进程隔离 |

> 站点隔离的代价是内存：每个渲染进程至少几十 MB。Chrome 的站点隔离让内存占用增加了约 10-20%。但这是值得的——它让 Spectre 类型的侧信道攻击在实践中不可行。

### 15.2.4 站点隔离的进程模型细节

站点隔离不是简单地「每个域名一个进程」。Chrome 使用「站点实例」（Site Instance）概念来管理进程分配。一个站点实例是同一站点在同一浏览上下文中的页面集合。

```
站点实例与进程分配

标签页 A: https://example.com
  → example.com 站点实例 → 进程 1

标签页 B: https://example.com
  → example.com 站点实例 → 进程 1（共享）

标签页 A 中的 iframe: https://evil.com
  → evil.com 站点实例 → 进程 2

标签页 C: https://evil.com（独立标签页）
  → evil.com 站点实例 → 进程 2（共享）
```

共享进程的条件：同一站点 + 同一浏览上下文。不同标签页的同一站点也会共享进程，但 iframe 中的跨站点内容一定在独立进程中。

| 场景 | 是否共享进程 | 原因 |
|------|------------|------|
| 两个标签页同一站点 | 可能共享 | 同站点同上下文 |
| 同标签页不同站点 iframe | 不共享 | 站点隔离 |
| 同标签页同站点 iframe | 共享 | 同站点 |
| 沙箱 iframe | 不共享 | sandbox 属性创建新上下文 |

## 15.3 Spectre 与 Meltdown 的影响

### 15.3.1 Spectre 攻击原理

Spectre 是 2018 年披露的 CPU 侧信道漏洞。它利用 CPU 的推测执行（Speculative Execution）机制，通过缓存侧信道读取本不应该被访问的内存。

```
Spectre 攻击简化流程

1. CPU 推测执行：
   if (x < array_size) {
     y = array[array2[x] * 4096];  // 推测执行
   }
   
   x 的值经过边界检查，正常情况下不会越界
   
2. 训练分支预测器：
   多次正常执行，让 CPU 预测分支为「true」
   
3. 越界读取：
   提供恶意 x 值（超出数组边界）
   CPU 推测执行 → 读取 array2[x] 的值（越界）
   → 用值作为索引访问 array → 加载到缓存
   
4. 分支回滚：
   CPU 发现边界检查失败 → 回滚执行
   但缓存中的数据仍然存在！
   
5. 缓存侧信道：
   测量访问 array 各位置的延迟
   延续低的位置 = 被缓存 = 推测执行访问过
   → 推断出 array2[x] 的值（越界数据）
```

### 15.3.2 浏览器的 Spectre 缓解措施

| 缓解措施 | 原理 | 效果 |
|---------|------|------|
| 站点隔离 | 不同站点在不同进程 | 限制可读取范围 |
| SharedArrayBuffer 限制 | 禁用高精度计时 | 增加侧信道难度 |
| Performance API 降精度 | 降低时间戳精度 | 增加计时难度 |
| Site Isolation + COEP/COOP | 跨域隔离 | 全面防护 |

### 15.3.3 COOP 和 COEP

为了安全地重新启用 SharedArrayBuffer 等高精度计时功能，Chrome 引入了跨域隔离（Cross-Origin Isolation）。

```http
# COOP（Cross-Origin Opener Policy）
# 隔离窗口上下文，防止其他页面引用本窗口
Cross-Origin-Opener-Policy: same-origin

# COEP（Cross-Origin Embedder Policy）
# 限制页面加载跨域资源（需要 CORS）
Cross-Origin-Embedder-Policy: require-corp

# 启用后可以安全使用：
# - SharedArrayBuffer
# - 高精度 Performance API
```

| 头部 | 作用 | 效果 |
|------|------|------|
| COOP: same-origin | 隔离窗口 | 其他域名的 window.opener 为 null |
| COEP: require-corp | 限制资源加载 | 跨域资源需要 CORP 或 CORS |
| CORP | 资源策略 | Cross-Origin-Resource-Policy: same-origin |

> COOP + COEP 构成跨域隔离环境。启用后浏览器认为页面是安全的，可以重新使用 SharedArrayBuffer 等功能。但 COEP 要求所有跨域资源都支持 CORS 或 CORP，迁移成本较高。

### 15.3.4 Spectre V2 与分支目标注入

Spectre 有多个变体。Spectre V1（边界检查绕过）通过站点隔离缓解。Spectre V2（分支目标注入）更难缓解，它攻击 CPU 的间接分支预测器。

Chrome 对 Spectre V2 的缓解包括：Reptiline（在编译时重写间接分支为条件分支）、Retpoline（将间接分支替换为 RET 指令的技巧），以及利用 CPU 微码更新提供的 IBRS（Indirect Branch Restricted Speculation）。

这些缓解措施有性能开销。Reptoline 和 Retpoline 会降低间接分支的执行速度，影响 JavaScript JIT 编译的代码性能。这是安全与性能的权衡。

## 15.4 进程模型与资源管理

### 15.4.1 Chrome 的进程上限

站点隔离增加了渲染进程数量，但系统资源有限。Chrome 设置了进程上限，当超过限制时，多个站点可能共享一个进程。

| 设备内存 | 进程上限 | 说明 |
|---------|---------|------|
| < 2GB | 约 10 | 低端设备 |
| 2-4GB | 约 20 | 中等设备 |
| 4-8GB | 约 40 | 标准设备 |
| > 8GB | 约 80 | 高端设备 |

当达到进程上限时，Chrome 使用「进程共享」策略：同一标签页中相似站点可能共享进程，但不同标签页的同一站点也会共享进程。

### 15.4.2 进程生命周期

```
渲染进程生命周期

创建：
  用户打开新标签页或导航到新站点
  → 浏览器进程创建新渲染进程
  
运行：
  渲染页面、执行 JavaScript、处理用户交互
  
隐藏（Tab 切换到后台）：
  → 降低优先级
  → 可能冻结（Freeze）非活跃标签页
  → 释放部分内存（如解码图片缓存）
  
丢弃（Discard，内存紧张时）：
  → 丢弃整个渲染进程
  → 保留 URL 和导航历史
  → 用户切换回时重新加载
  
销毁：
  关闭标签页或导航到不同站点
```

| 状态 | 内存占用 | 响应速度 | 说明 |
|------|---------|---------|------|
| 活跃 | 正常 | 即时 | 当前可见标签页 |
| 隐藏 | 降级 | 即时 | 后台标签页 |
| 冻结 | 更低 | 需解冻 | 5 分钟后自动冻结 |
| 丢弃 | 最低（仅 URL） | 需重新加载 | 内存紧张时 |

## 15.5 安全边界总结

Chrome 的安全架构是多层防御（Defense in Depth），每一层独立工作，一层被攻破不会导致全面沦陷。

```
Chrome 安全层级

第1层：同源策略（JavaScript 层）
  限制脚本跨域访问 DOM 和数据
  ↓ 被绕过（如 Spectre）

第2层：站点隔离（进程层）
  不同站点在不同进程，内存隔离
  ↓ 被攻破（需要沙箱逃逸）

第3层：沙箱（操作系统层）
  渲染进程无文件/网络/系统调用权限
  ↓ 被攻破（需要内核漏洞）

第4层：操作系统权限
  浏览器进程本身权限有限
  → 攻击者需要多个漏洞才能完全控制
```

| 层级 | 防护目标 | 实现机制 |
|------|---------|---------|
| 同源策略 | 脚本跨域访问 | DOM 规范 |
| 站点隔离 | 侧信道攻击 | 进程隔离 |
| 沙箱 | 渲染进程逃逸 | Seccomp/MAC |
| OS 权限 | 系统级操作 | 用户权限 |

> 多层防御是安全架构的核心理念。没有任何单一安全机制是完美的，但多层叠加让攻击者需要同时利用多个不同类型的漏洞，大幅提高了攻击成本。Chrome 的安全设计是「不信任任何单一防线」。

## 本章核心知识总结

| 知识模块 | 核心内容 | 安全意义 |
|---------|---------|---------|
| 沙箱 | 限制渲染进程权限 | 防止渲染漏洞逃逸 |
| Seccomp-BPF | 系统调用过滤 | 内核级防护 |
| 站点隔离 | 不同站点不同进程 | 防 Spectre 侧信道 |
| 跨进程 iframe | OOPIF | 进程间数据隔离 |
| COOP/COEP | 跨域隔离环境 | 安全启用高精度计时 |
| 多层防御 | 4 层独立防护 | 纵深防御 |

觉得有用？收藏起来，这是理解浏览器安全架构最系统的一篇。

你对浏览器安全架构有什么疑问？评论区聊聊。

关注怕浪猫，下期我们讲 Cookie 安全与隐私保护。系列进度 15/24。

下期预告：第 16 章「Cookie 安全与隐私保护」。我们会拆解 Cookie 的安全属性（Secure、HttpOnly、SameSite）、第三方 Cookie 的消亡路线图、以及 Privacy Sandbox 的替代方案。怕浪猫下期见。

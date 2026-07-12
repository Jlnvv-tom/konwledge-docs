---
sidebar_position: 3
---

# 第3章 Redis核心数据结构基础：字符串与哈希

## 引言

在学习 Redis 的过程中，有一个问题始终绕不开：Redis 凭什么这么快？抛开它基于内存运行这个显而易见的原因，还有一个至关重要的因素常常被忽视——它的数据结构设计。很多人以为 Redis 存的就是简单的 key-value，一个字符串配一个值，如此而已。但真相远比你想象的复杂和精妙。

Redis 之所以能在极致性能下灵活应对各种业务场景，秘密就藏在它的五种核心数据结构里。每一种结构都经过了精心的设计，针对特定的数据访问模式做了深度优化。五种结构各有所长，分别解决了不同的工程问题。而在这五种结构中，最基础也最常用的两个，就是字符串（String）和哈希（Hash）。

你可以在一切有缓存的系统里看到它们的身影：String 承载着计数器和分布式锁的使命，Hash 管理者用户信息和对象属性的读写。如果你能理解它们的设计初衷和底层原理，写出高性能的 Redis 代码就不再是一件靠运气的事情。很多人在工作中写 Redis 调用只停留在"调对 API"的层面，一旦遇到性能问题或者数据不一致的情况就束手无策。根本原因在于，他们对这些数据结构的理解只浮于表面。一个知道 SDS 和 ziplist 的工程师，和一个只知道 SET/GET 的工程师，写出来的代码质量天差地别。

这一章，我们将从底层原理到上层实战，把 String 和 Hash 每一个角落都看清楚。你会学到它们的核心命令、适用场景、底层编码机制，以及在真实项目中怎么用它们解决实际问题，又会在哪些地方踩坑。

## 3.1 字符串（String）：Redis最基础的数据结构

如果你只能用 Redis 的一种数据结构，那一定是 String。它是 Redis 最基础、最通用的数据结构，几乎所有 Redis 新手遇到的第一个命令就是 SET 和 GET。

但 String 并没有名字看上去那么简单。在很多人的认知里，Redis 的 String 就是编程语言里的字符串，比如 Java 的 String、Python 的 str。你存进什么就取出什么，无非是个文本容器。实际上，Redis 的 String 不仅能存储文本，还能存储数字、二进制数据，甚至序列化后的对象。它的能力边界远超"字符串"这个名字所能涵盖的范围。

在 Redis 内部，String 类型可以存储三种形态的值。

第一种是字符串值，比如 "hello world"、"这是一段中文文本"。这是最常见的用法，缓存中的 JSON 序列化数据、HTML 片段、配置项等都属于这一类。第二种是数值，比如 10086、3.14，Redis 内部会对纯数字字符串做特殊优化——检测到字符串可以被解析为 64 位有符号整数时，它不会真的去分配一块内存存储字符串，而是直接把数字存在指针字段里。这让数值操作极快，INCR 命令的原子自增每秒可以完成十几万次。第三种是二进制数据，比如一张图片的字节流、一个序列化后的 Java 对象、一个 Protobuf 编码后的结构体。SDS 的二进制安全性让这一切成为可能。

这意味着你可以用 String 做很多超乎"字符串"本身的事情。比如缓存一个 JSON 序列化后的用户对象，或者用 INCR 做一个分布式计数器，甚至存储一个 512MB 以内的任意二进制文件。String 的上限是 512MB——单个 String 类型的 value 最大不能超过 512 MB。这个限制在绝大多数场景下已经足够，但如果你需要存储更大的单个值，就需要考虑拆分存储或者换用其他方案了。

String 的使用场景极其广泛。最常见的莫过于缓存：把数据库查询结果、API 响应数据以 JSON 字符串的形式存入 Redis，下次请求直接走缓存，能大幅降低数据库压力。Session 共享也是经典用法——将用户的登录态序列化为字符串，存入 Redis，多台服务器共享同一个 session 池，轻松实现无状态架构。分布式锁也是 String 的拿手好戏，SETNX 命令配合过期时间，就是一套简洁高效的锁方案。计数器就更不用说了，INCR 和 DECR 是原子操作，在高并发场景下表现极佳。

还有一种很常见的用法是用 String 存储各种配置开关。比如功能灰度发布的标志位、限流阈值、黑名单白名单等。这些配置往往是一个简单的字符串或数字，用 String 存取最合适。在启动配置中心之前，很多团队就是靠 Redis 的 String 来完成配置动态下发的。

但 String 的真正威力远不止这些基础用法。我们先从它的核心命令入手，看看每一条命令能解决什么实际问题，又隐含着哪些需要留意的陷阱。

## 3.2 String核心命令：set、get、incr、decr等实操与应用场景

### 最基础的 SET 和 GET

Redis 的 SET 和 GET 是敲门砖级别的命令，几乎所有 Redis 教程都会从这里开始。看起来简单，但背后的细节并不少。

```
> SET user:name "张三"
OK
> GET user:name
"张三"
```

从表面上看，SET 就是存储一个 key-value 对，GET 就是根据 key 取出 value。但很多人在实际使用中踩过这样一个坑：value 是中文或者其他多字节字符时，从 Redis 取出来发现乱码了。这个问题通常不是 Redis 本身的问题，而是客户端连接时没有指定正确的编码。以 Java 的 Jedis 客户端为例，连接时必须确保指定了 UTF-8 编码：

```java
Jedis jedis = new Jedis("localhost", 6379);
jedis.getClient().setCharset(Charset.forName("UTF-8"));
```

更推荐的做法是在构造连接时通过 JedisPoolConfig 统一配置编码参数，而不是在每条命令层面去处理。如果用的是 Spring Data Redis，要在 RedisTemplate 中指定 StringRedisSerializer 的编码。默认的 JdkSerializationRedisSerializer 不仅会产生乱码问题，还会带来额外的序列化和反序列化开销。

另一个常见的坑是 key 的命名规范。Redis 作为单线程模型，key 的数量级可能很大——一个线上实例动辄几千万个 key。一个糟糕的命名习惯会在后续维护时带来巨大麻烦。比如有的新手喜欢用 `name:1001`、`age:1001` 这样分散的 key 命名，既看不出业务归属，也不方便批量管理。当线上出问题时，在几千个毫无规律的 key 中找一个特定的数据，无异于大海捞针。

建议采用 "业务域:对象类型:对象ID:字段" 的命名方式：

```
user:profile:1001             表示用户1001的个人信息
order:status:20230701         表示订单20230701的状态
captcha:sms:13800138000       表示手机号的短信验证码
article:view:article_1001     表示文章1001的阅读量
```

这种层级化的命名方式在后续使用 KEYS 或 SCAN 命令做模式匹配时会方便很多。比如想扫描所有用户相关的 key，只需要 `SCAN 0 MATCH user:*` 即可。如果命名时没有统一的前缀，这种操作就无从谈起了。团队内部最好形成一套 key 命名规范文档，所有开发成员遵守同一套标准，这对后续的运维和排错至关重要。

### 带过期时间的 SETEX

很多业务场景下，缓存数据不需要永久保留。比如短信验证码 5 分钟有效、临时 token 30 分钟过期。这时候可以用 SETEX 或者 SET 命令的 EX/PX 选项。

```
> SETEX captcha:13800138000 300 "123456"
OK
> TTL captcha:13800138000
(integer) 289
> GET captcha:13800138000
"123456"
```

熟悉 Redis 命令的人可能会注意到，Redis 从 2.6.12 版本开始给 SET 命令增加了 EX、PX、NX、XX 等选项。这意味着你可以在一行命令中同时完成 SET 和设置过期时间的操作，避免了 SET 和 EXPIRE 两条命令之间的原子性问题。这也是官方推荐的做法。

```
> SET captcha:13800138000 "123456" EX 300 NX
OK
```

这里 EX 表示过期时间单位为秒，PX 表示毫秒，NX 表示只有 key 不存在时才设置成功，XX 表示只有 key 存在时才设置成功。NX 和 XX 用在需要条件写入的场景中，比如分布式锁用 NX，缓存更新用 XX。

我在线上见过无数次因为忘记设置过期时间导致的内存暴涨事故。业务方写着写着就忘了给 key 设 TTL，数据越积越多，直到 Redis 内存被打满，触发 maxmemory 策略开始驱逐 key，结果把还在使用的缓存也给驱逐了，引发连锁反应。更危险的是，如果 maxmemory-policy 配置的是 allkeys-lru，那么长时间未被访问但仍有价值的 key 可能会被错误地淘汰，导致大量缓存穿透打到数据库。

一条好用的排查命令是 `INFO memory`。当 used_memory 持续上涨而没有任何过期 key 被淘汰时，大概率是业务代码里忘了设置 TTL。在 Redis 4.0 之后，可以用 `MEMORY USAGE` 命令查看某个 key 占用的内存大小，配合 `OBJECT IDLETIME` 查看 key 的空闲时间，找出那些长期存在但鲜有访问的僵尸 key。定期的内存巡检脚本应该纳入团队的运维规范中。

### 用 SETNX 实现分布式锁

SETNX 是 "SET if Not eXists" 的缩写，只有 key 不存在时才会设置成功。这个特性让它天然适合作为分布式锁的实现基础。

```
> SETNX lock:order:1001 "locked"
(integer) 1   -- 获取锁成功
> SETNX lock:order:1001 "locked"
(integer) 0   -- 获取锁失败，说明已被其他客户端持有
```

但直接这样用有一个很严重的问题——如果持有锁的客户端崩溃了，锁永远不会释放。其他所有等待这个锁的客户端会一直阻塞，直到人工介入清除这个 key。这在线上是一个典型的故障场景。

所以在 Redis 2.8 之后，官方推荐用 SET 命令的 NX 和 PX 选项组合，一条命令同时解决原子性和过期时间：

```
> SET lock:order:1001 "locked" NX PX 30000
OK    -- 获取锁成功，30秒后自动释放
```

这样即使客户端崩溃了，锁也会在 30 秒后自动超时释放，不会造成死锁。

但这里又引出一个新的问题：过期时间设置多久才合适？设置太短，业务还没执行完锁就被自动释放了，后续请求可能拿到锁导致并发冲突。设置太长，持有锁的客户端崩溃后，其他客户端要等待很久才能获得锁。

一个工程化的解决方案是引入看门狗（Watch Dog）机制：在业务执行过程中，由一个后台线程定期延长锁的过期时间。在 Java 生态中，Redisson 已经实现了这个机制，它的分布式锁会自动续期，默认每 10 秒检查一次，如果锁还在被持有就续期到 30 秒。除了 Redisson，Go 生态中的 go-redsync 也有类似的机制。具体实现的核心思路是启动一个定时任务，在锁过期之前不断检查锁是否仍然被当前线程持有，如果是则执行 PEXPIRE 续期。

但看门狗方案也不是完美的。如果 Redis 节点发生主从切换，刚写入 master 的锁还没来得及同步到 slave，slave 提升为 master 后锁信息就丢失了。这种情况下的锁安全性是一个更深层次的问题，需要引入 RedLock 算法来解决，不过这是另一个话题了。对于多数业务场景，看门狗 + 合理设置过期时间已经足够。

### INCR、DECR：扛住高并发的原子计数器

INCR 和 DECR 是 Redis 里最被低估的命令之一。这两个命令是原子操作，内部通过 Redis 的单线程模型保证并发安全。在高并发场景下，它们几乎是最优雅的计数方案。

```
> SET page:view:article_1001 0
OK
> INCR page:view:article_1001
(integer) 1
> INCR page:view:article_1001
(integer) 2
> INCRBY page:view:article_1001 10
(integer) 12
```

想想看，如果这个计数器用 MySQL 实现，每次加一都要先 SELECT 再 UPDATE，不仅多了一次网络 IO，还要处理行锁和事务。在几十万甚至上百万 QPS 的冲击下，数据库大概率撑不住。而 Redis 的 INCR 就是一条命令，没有任何事务开销，单机就能扛下十万级别的并发写。

我曾在线上见过一个真实的案例。某活动的实时点赞数用 MySQL 存储，每次点赞都 UPDATE 一次。活动刚开始 10 分钟，数据库的 CPU 直接飙升到 100%，慢查询堆积成山。排查后发现单条 UPDATE 语句在业务高峰期需要等待行锁释放，延迟从 1ms 飙升到了 500ms。后来改成先用 Redis INCR 累计，每分钟批量回写一次数据库，数据库的负载瞬间降到了个位数。

这里有几个实现细节需要特别注意。

第一，INCR 操作的值本质上还是 String 类型，只不过 Redis 内部将其解析为整数。当数值超过 64 位有符号整数的范围（9223372036854775807）时，会抛出溢出错误。虽然这个上限在日常生活和大多数业务场景中几乎碰不到，但在做大数据量的累加时还是要有所意识。比如在一个超级爆款视频的播放量统计中，几百亿次的播放量虽然少见，但理论上存在超出范围的可能。

第二，如果用 SET 把这个 key 覆盖成了非数字字符串，再执行 INCR 会报错。

```
> SET counter "not-a-number"
OK
> INCR counter
(error) ERR value is not an integer or not within range
```

这个错误一旦触发，需要人工手动修复数据，是一个比较麻烦的线上事故。所以在代码中要确保计数器 key 不会被其他业务逻辑用 SET 覆盖。一个常用的防御性编程技巧是在计数器 key 的前缀上进行隔离，比如 `counter:pageview:article_1001`，其他业务代码严禁操作以 `counter:` 开头的 key。

第三，INCR 和 EXPIRE 之间没有原子性。如果业务逻辑是"用户登录后计数器 INCR，如果超过 3 次就锁定账户"，你需要考虑计数器的过期时间。如果过期时间设置不当，用户可以通过频繁登录来绕过锁定机制。推荐用 Lua 脚本将 INCR 和 EXPIRE 合并到一次原子操作中：

```lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, expire_time)
end
return current
```

INCR 的兄弟命令还有 INCRBYFLOAT，专门用于浮点数自增：

```
> INCRBYFLOAT price:product_1001 3.5
"23.50"
> INCRBYFLOAT price:product_1001 -1.2
"22.30"
```

INCRBYFLOAT 在处理金额、评分等浮点数场景时非常实用。但它有一个小坑：浮点数在二进制中本就是近似表示，多次累计后精度误差会逐渐累积。如果是金额场景，强烈建议统一将数值放大 100 倍用整数存储，比如 3.50 元存储为 350，只在展示时才做除法换算。这样可以彻底避免浮点数精度问题。

### 批量操作的 MSET 和 MGET

当需要同时操作多个 key 时，逐条 SET 或 GET 会造成大量的网络往返。每个往返至少一个 RTT（Round-Trip Time），在异地多机房场景下这个延迟可能高达几十毫秒。MSET 和 MGET 可以将多条命令合并为一次网络请求，大幅降低延迟。

```
> MSET user:1:name "张三" user:1:age "28" user:1:city "北京"
OK
> MGET user:1:name user:1:age user:1:city
1) "张三"
2) "28"
3) "北京"
```

想象一下，没有 MSET 的时候，获取 100 个用户的姓名需要 100 次 GET 请求，每次来回至少 1ms，加起来就是 100ms。如果用 MGET 一次性读取，网络开销只有一次往返，性能提升非常可观。在微服务架构中，一次页面渲染可能需要从 Redis 获取几十个 key，使用批量命令能直接减少页面加载时间，提升用户体验。

不过 MSET 有一个需要注意的地方：它不是原子事务。如果 MSET 设置到一半网络断开了，已经设置成功的 key 不会回滚。和管道（PIPELINE）一样，Redis 会逐条执行这些命令，但不会保证"全部成功或全部回滚"。如果你需要真正的事务性批量操作，需要使用 MULTI/EXEC 或 Lua 脚本。MULTI/EXEC 会将所有命令打包到一个事务中，Redis 保证在事务执行期间不会有其他客户端的命令插入。

MGET 也有技巧：当请求的 key 较多时，如果有部分 key 不存在，MGET 会返回 nil。客户端处理 nil 值时需要做空值判断，避免空指针异常。可以结合 EXISTS 命令先检查 key 的存活状态，但这样又多了额外的网络开销。工程中更常见的做法是直接从 MGET 的返回值中判断 nil，对缺失的 key 做兜底处理，比如查询数据库回填。

### APPEND、STRLEN、GETSET

除了上面这些高频命令，String 还有几个日常不常用但在特定场景下威力巨大的命令。

APPEND 可以在字符串末尾追加内容。如果 key 不存在，则相当于执行 SET：

```
> SET message "Hello"
OK
> APPEND message " World"
(integer) 11
> GET message
"Hello World"
```

APPEND 在日志追加、消息拼接等场景中非常实用。但它有一个需要留意的性能问题：每次 APPEND 都可能触发 SDS 的内存重新分配，当字符串很大时（比如几 MB 以上），频繁的 APPEND 会导致内存碎片增加和性能下降。对于大字符串的追加操作，建议批量攒够一定量后再写入。

STRLEN 可以在不取出整个字符串的情况下获取字符串长度：

```
> STRLEN message
(integer) 11
```

STRLEN 的时间复杂度是 O(1)——SDS 中记录着 len 字段，无需遍历。这在需要对大字符串做长度判断时非常有用，避免了 GET 整个字符串的带宽开销。

GETSET 则是 GET 和 SET 的原子组合，先返回旧值再设置新值：

```
> SET counter 100
OK
> GETSET counter 200
"100"
> GET counter
"200"
```

GETSET 在需要"读取当前值并重置"的场景中非常有用。比如监控场景下，需要每秒读取计数器的当前值，然后将计数器归零重新计数。用 GETSET 可以原子地完成这两个操作。

### SETRANGE 与 GETRANGE

SETRANGE 是一个富有争议的命令。它可以根据偏移量修改字符串的一部分，类似于对数组的随机访问。

```
> SET greeting "Hello World"
OK
> SETRANGE greeting 6 "Redis"
(integer) 12
> GET greeting
"Hello Redis"
```

GETRANGE 则支持按字节范围截取子串：

```
> GETRANGE greeting 0 4
"Hello"
```

GETRANGE 适合分页展示长文本内容或者提取字符串前缀。SETRANGE 的坑在于：如果偏移量超过了字符串的当前长度，Redis 会用零字节补齐中间的空隙。这意味着可能产生一个非常大的字符串，消耗大量内存。比如对一个长度为 10 的字符串执行 `SETRANGE key 100000 "x"`，Redis 会在 0 到 99999 之间的位置上填充零字节，再在第 100000 个位置写入"x"，最终得到一个 100001 字节的字符串。在没有充分理解其行为之前，最好不要在生产环境使用 SETRANGE。

## 3.3 哈希（Hash）：键值对集合的高效存储结构

理解了 String，接下来看 Hash。这是 Redis 里最能体现"为特定场景而生"的设计思想的数据结构。如果说 String 是对单个值的抽象，那 Hash 就是对一组相关字段的抽象。它解决了一个 String 方案下的经典痛点：如何高效地存储和操作对象。

你可以把 Hash 想象成一个微型的数据库表——每一行有一个 key，下面有多个 field-value 对。它特别适合存储对象，比如用户信息、商品详情、配置参数。在 Hash 出现之前，Redis 用户只能把对象序列化成 JSON 或者某种字符串格式，存入 String 中。这种方案有什么问题呢？

第一，修改单个字段的成本太高。假设你存储用户的 profile，包含 name、age、city、email、phone 五个字段，全部序列化为一个 JSON 字符串。当你只需要修改 phone 时，流程是这样的：GET 取出整个字符串，用 JSON 解析库反序列化成对象，修改 phone 字段，用 JSON 库重新序列化成字符串，SET 写回去。修改一个字段引发了四次操作，不仅浪费带宽，还浪费 CPU。而 Hash 的处理极其优雅——一条 HSET 命令搞定，只传输 key、field 和新值，带宽占用最小化。

```
> HSET user:1001 phone "13900001111"
(integer) 0
```

第二，并发修改冲突的风险。用 String 存 JSON，两个并发请求同时读取并修改不同的字段，后提交的会覆盖先提交的，导致先提交的修改丢失。这个问题的本质是更新粒度太大——String 的粒度是整个 value，Hash 的粒度是单个 field。在 Hash 下，两个并发请求分别更新 name 和 phone 不会互相干扰。

第三，内存浪费。后续会讲到，Hash 在字段数较少时有专门的 ziplist 编码优化，内存占用远低于 String 方案。Redis 内部对每个 key 的元数据也有开销，用 String 存 JSON 方案的 key 数量远多于 Hash 方案（每个对象一个 key vs 每个对象里的每个简单字段一个 key），key 本身的元数据开销累积起来也很可观。

当然，Hash 也不是万能的。它最不擅长的场景是"全量查询"——HGETALL 在字段多的时候会拉取所有数据，就像 SELECT * 一样不利于性能。如果你的业务场景经常需要读取整个对象的所有字段，而且字段比较少（10 个以内），用 String 存序列化后的数据反而更简单高效。

Hash 还有一个容易被忽视的特点：单个 Hash 可以包含的字段数没有硬性限制，但实践中不建议在一个 key 中放入超过 10000 个 field。字段数过多时，hashtable 编码下的内存开销和操作延迟都会上升。如果你有大量字段需要存储，更合理的做法是拆分成多个 Hash，比如按用户 ID 的哈希值做分片。

在业务选型时，可以遵循这样一个判断标准：如果读取数据时总是需要整个对象的所有字段，倾向于用 String 存序列化数据；如果经常只读取或修改对象的某个或某几个字段，倾向于用 Hash。这个判断标准看似简单，但在实际项目中能够帮你做出更合理的数据结构选择。

## 3.4 Hash核心命令：hset、hget、hkeys、hvals等实操

### HSET、HGET 和 HGETALL：字段的读写

这三个命令是 Hash 最基础的操作。HSET 设置字段的值，HGET 获取单个字段的值，HGETALL 获取所有字段和值。

```
> HSET user:1001 name "张三" age 28 city "北京"
(integer) 3
> HGET user:1001 name
"张三"
> HGETALL user:1001
1) "name"
2) "张三"
3) "age"
4) "28"
5) "city"
6) "北京"
```

HSET 的返回值表示新增了多少个字段。如果字段已经存在，HSET 会覆盖旧值，返回值不会累加这个已存在的字段。在 Redis 4.0 以上版本，HSET 可以一次设置多个 field-value 对，降低了批量化写入时的网络开销。

这里有一个历史版本兼容问题需要留意：HSET 命令从 Redis 4.0.0 开始支持一次设置多个 field-value 对。在 4.0 之前的版本中，HSET 一次只能设置一个 field-value 对，批量设置时需要逐条执行。如果你的 Redis 版本较老（虽然现在这种情况很少见了），要在代码中避免直接使用多参数的 HSET。可以用 HMSET 作为替代，HMSET 在任何版本中都支持多参数。

HGETALL 虽然方便，但它有一个容易被忽视的性能缺陷：当 Hash 中的字段很多时，HGETALL 会返回所有 field-value 对，如果 Hash 里有几百上千个字段，一次 HGETALL 可能会产生几百 KB 甚至几 MB 的网络数据。在 QPS 较高的服务中，这会造成显著的带宽压力和序列化开销。一个 10 万个字段的 Hash，一次 HGETALL 可能产生几 MB 的响应数据，对大流量接口来说这是不可接受的。

### HMGET：按需获取多个字段

HMGET 是 HGETALL 的替代方案，它只返回你指定的字段。

```
> HMGET user:1001 name city phone
1) "张三"
2) "北京"
3) (nil)
```

如果请求的字段不存在，HMGET 会在对应位置返回 nil。这个返回值处理需要在代码中做 null 判断。在缓存回源场景中，某个字段不存在意味着对应的值需要从数据库获取，而不是简单地返回空字符串或者默认值。

使用 HMGET 的最佳实践是：在你的业务中只请求确实需要的字段，而不是为了省事直接甩一个 HGETALL。在接口定义上，可以设计一个 fields 参数让调用方指定需要获取的字段列表。这样既能减少 Redis 的传输量，也能降低下游接口的负载。在一个典型的用户信息展示页面中，可能只需要 name、avatar、level 三个字段，完全不需要把 email、phone、address 这些敏感信息也传输过来。

### HEXISTS 和 HDEL：判断和删除

```
> HEXISTS user:1001 name
(integer) 1
> HEXISTS user:1001 email
(integer) 0
> HDEL user:1001 city
(integer) 1
```

HEXISTS 用于判断某个字段是否存在。这是一个非常实用的命令，在更新或删除字段前做存在性检查，可以避免不必要的写入操作。在缓存一致性方案中，可以用它来判断某条缓存数据是否还在 Redis 中，如果不在了就触发回源。

HEXISTS 和 HGET 的组合有一个常见用法：先判断字段是否存在，如果存在则直接返回缓存值，如果不存在则查询数据库并回填缓存。这种"缓存穿透"防护逻辑在很多框架中都有实现。在极端情况下，可以用 EXISTS 检查 key 是否存在，用 HEXISTS 检查 field 是否存在，做到精确的缓存命中判断。

HDEL 返回成功删除的字段数量。如果字段不存在，返回 0 而不是抛出错误。这个特性在处理批量删除逻辑时很友好，不需要额外做 try-catch 包装。

HDEL 支持一次删除多个字段：

```
> HDEL user:1001 email phone address
(integer) 2
```

上面返回 2 表示 email 和 phone 被成功删除，address 字段不存在。返回值可以帮助你判断实际删除了多少数据，在审计日志场景中这个信息很有价值。比如在用户注销场景中，需要删除用户的敏感信息字段，HDEL 的返回值可以帮你确认哪些字段被成功清除。

### HKEYS 和 HVALS：取字段或取值

```
> HKEYS user:1001
1) "name"
2) "age"
> HVALS user:1001
1) "张三"
2) "28"
```

HKEYS 只返回字段名，HVALS 只返回值，它们比 HGETALL 的传输量更小，在只需要字段列表或值列表的场景下非常高效。比如你要在前端渲染一个表单，只需要知道用户有哪些字段，不需要字段的值，用 HKEYS 就能完成任务。又比如你要做批量数据统计，只需要用户的值不需要字段名，用 HVALS 就够了。

这两个命令也存在着和时间复杂度相关的性能问题。当 Hash 中字段较多时，HKEYS 和 HVALS 会遍历整个 Hash，时间复杂度是 O(n)。n 是 Hash 的字段数而不是整个 Redis 的 key 数。如果 Hash 中有几千个字段，这两个命令的耗时虽然比 KEYS 命令好得多，但仍然值得关注。

在实际的业务系统中，HKEYS 经常用于字段发现。比如某个业务版本的更新引入了新的用户字段，可以用 HKEYS 检查某个用户的 Hash 中是否已经包含了这些新字段。如果某个字段不存在，则触发回填逻辑。这种方式避免了显式的字段版本号管理。

### HLEN 和 HSTRLEN：获取数量与值长度

```
> HLEN user:1001
(integer) 2
> HSET user:1001 sign "这个人很懒，什么都没留下"
(integer) 1
> HSTRLEN user:1001 sign
(integer) 15
```

HLEN 返回 Hash 中字段的总数，时间复杂度 O(1)，因为 Redis 内部维护了字段数的计数器。HSTRLEN 返回指定字段的值的字节长度，在检查数据完整性和做数据迁移时很有用。在数据迁移的场景中，可以用 HSTRLEN 检查迁移前后的值长度是否一致，作为数据完整性验证的一个手段。

### HINCRBY：Hash字段级的原子计数器

Hash 也支持原子自增操作，通过 HINCRBY 实现。

```
> HSET user:1001 score 0
(integer) 1
> HINCRBY user:1001 score 10
(integer) 10
> HINCRBY user:1001 score -5
(integer) 5
```

HINCRBY 的操作范围是字段级别的，只影响 Hash 中的一个 field，不会影响其他字段。这意味着你可以在同一个 key 下维护多个独立的计数器——用户的积分、等级、登录次数、发帖数等，都可以在同一个 Hash key 下管理，比用 String 创建 N 个 key 更节省内存，也更方便管理和维护。

这对内存的影响是很显著的。假设你有 100 万个用户，每个用户需要维护 5 个计数字段。用 String 的话，每个计数器需要一个独立的 key，总共 500 万个 key。而用 Hash，每个用户一个 key 就够了，只需要 100 万个 key。Redis 的每个 key 本身就有一定的内存开销（约几十字节的 redisObject + SDS 头部），500 万和 100 万的差距就是几百 MB 的内存。在内存价格为王的 Redis 世界里，这样节约出来的几百 MB 可能就是真金白银。

HINCRBY 也支持浮点数自增，对应的命令是 HINCRBYFLOAT：

```
> HINCRBYFLOAT user:1001 balance 3.50
"13.50"
```

不过同样要注意浮点数精度的问题。在金额场景中，建议统一用整数存储，单位放大 100 倍。比如 13.5 元存储为 1350 分，展示时再除以 100。

### HSCAN：安全地遍历大Hash

当 Hash 中的字段很多时，HKEYS 或 HGETALL 会阻塞 Redis 单线程较长时间。这时候要用 HSCAN 进行增量迭代：

```
> HSCAN user:1001 0 MATCH n*
1) "0"
2) 1) "name"
   2) "张三"
```

HSCAN 的原理和 SCAN 类似，每次调用返回一个游标和一批数据。游标为 "0" 表示迭代完成。通过 COUNT 参数可以控制每次返回的数量。

在 Java 中，HSCAN 的典型用法是：

```java
public Map<String, String> scanAllFields(String key) {
    Map<String, String> result = new HashMap<>();
    String cursor = "0";
    do {
        ScanResult<Map.Entry<String, String>> scanResult =
            jedis.hscan(key, cursor, new ScanParams().count(100));
        cursor = scanResult.getCursor();
        for (Map.Entry<String, String> entry : scanResult.getResult()) {
            result.put(entry.getKey(), entry.getValue());
        }
    } while (!cursor.equals("0"));
    return result;
}
```

HSCAN 不会阻塞服务器，是遍历大 Hash 的标准做法。在线上环境，任何可能导致 O(n) 操作遍历全部数据的命令都要优先考虑它的增量版本。如果业务中频繁需要对大 Hash 做遍历操作，不妨重新审视数据结构设计——是否应该把这个 Hash 拆分？是否应该换用其他数据结构？

## 3.5 String与Hash的底层实现原理：简单动态字符串与字典

基础命令掌握之后，我们来深入底层，看看 String 和 Hash 在 Redis 内部到底是怎么存储的。理解底层实现，你才能真正明白为什么这些命令有不同的性能特征，也才能在设计业务方案时做出最优的选择。

### String 的底层编码

Redis 的 String 底层有三种编码方式：int、embstr 和 raw。Redis 会根据值的内容和长度自动选择合适的编码，不需要开发者手动干预。了解这三种编码的区别，有助于你理解为什么不同的操作有不同的性能表现。

int 编码：当存储的值是一个可以用 64 位有符号整数表示的整数时，Redis 直接把整数存在 String 对象的 ptr 指针位置，而不是分配额外的一块内存来存储字符串。这听起来只是一个微小的优化，但对于 INCR、DECR 这样高频使用的命令来说，省去了字符串和整数之间的来回转换，性能提升非常可观。你可以用 OBJECT ENCODING 命令查看一个 key 当前的编码：

```
> SET num 10086
OK
> OBJECT ENCODING num
"int"
> SET text "hello"
OK
> OBJECT ENCODING text
"embstr"
```

embstr 编码：当存储的是字符串且长度不超过 44 字节时，Redis 采用 embstr 编码。它的本质是一次性分配一块连续的内存，同时容纳 redisObject 和 SDS（简单动态字符串）两个结构。这样既减少了内存分配的次数——从两次减少到一次，又利用了 CPU 缓存的空间局部性原理，提升了访问速度。连续的 64 字节刚好填满一个缓存行（cache line），CPU 加载一个缓存行就能读到全部数据。

raw 编码：当字符串长度超过 44 字节时，Redis 退化为 raw 编码。此时 redisObject 和 SDS 分别分配在内存中不同的位置，需要两次内存分配，且数据不在同一个缓存行内，访问速度略慢于 embstr。44 这个数字是怎么来的？Redis 的 redisObject 结构体占用 16 字节，SDSHDR 占用至少 3 字节，加上 SDS 的头部信息，一个 64 字节的 Jemalloc 内存分配单位剩余 44 字节可用于字符串数据。

这里有一个容易踩坑的情况：当你执行 `SET num 10086` 和 `SET num "10086"` 时，Redis 都将其识别为整数，采用 int 编码。但如果你写成 `SET num " 10086"`（带空格），Redis 会将其作为纯字符串处理，使用 embstr 或 raw 编码，这时候 INCR 就会报错。所以在存储数值类的数据时，要确保存入的数据格式干净，不要有空格或其他非数字字符。这种看似微小的差异，在线上可能就是一次事故的直接原因。

### 简单动态字符串（SDS）

SDS 是 Redis 自己实现的字符串结构，全称 Simple Dynamic String。为什么会有一个专门的数据结构？C 语言原生字符串有什么问题？Redis 为什么要重复造轮子？

C 语言的 char\* 字符串有三个本质性的缺陷。第一，获取字符串长度需要遍历整个字符数组直到遇到 '\0'，时间复杂度 O(n)。对于需要频繁获取长度的 Redis 来说，这个性能问题是不可接受的。第二，字符串拼接操作需要手动管理内存分配，每次拼接都要先计算出新的长度，再重新分配一块足够大的内存，拷贝旧内容，拼接新内容。这个操作的性能开销很大，而且在内存分配失败时没有优雅的错误处理机制。第三，C 字符串以 '\0' 作为结束标志，这意味着字符串内部不能包含 '\0' 字符。但 Redis 需要存储图片、音视频、序列化对象等二进制数据，这些数据中 '\0' 字节是常态。所以，SDS 的诞生几乎是必然的。

SDS 在 Redis 3.2 之后有五种结构变体：sdshdr5、sdshdr8、sdshdr16、sdshdr32、sdshdr64。它们的区别在于 len 字段的位数不同，以适应不同长度的字符串。sdshdr5 专为短字符串优化，sdshdr8 适用于长度不超过 255 字节的字符串，以此类推。这种精细化的设计目的是节省内存——不需要为每个字符串分配固定大小的头部，而是根据实际长度选择合适的头部结构。如果所有 SDS 都用 64 位的 len 字段，每个字符串头部就要多花 7 个字节，在数以亿计的 key 面前，这个浪费是惊人的。

以 sdshdr8 为例，它的结构大致如下：

```
struct sdshdr8 {
    uint8_t len;       // 已使用字节数
    uint8_t alloc;     // 总分配字节数（不包括头部）
    unsigned char flags; // 低3位表示类型，高5位保留
    char buf[];        // 字节数组
};
```

SDS 通过维护 len 字段，让获取字符串长度的操作从 O(n) 降至 O(1)。它通过 alloc 字段记录已分配的总空间，当字符串长度增加时，SDS 会检查 alloc - len 是否足够，如果够就直接追加，不需要重新分配内存。

SDS 还采用了一种预分配空间策略来减少内存分配次数。当对一个 SDS 进行扩展操作时，Redis 不仅会分配所需的空间，还会额外分配一些预留空间：如果修改后的 SDS 长度小于 1MB，就分配同样大小的预留空间；如果大于等于 1MB，就分配 1MB 的预留空间。这个策略让 SDS 在频繁拼接场景下的内存分配次数从 N 次降低到了最多 log2(N) 次。这是一个典型的以空间换时间的策略，在 Redis 这种内存数据库中，少量额外的空间开销换来的性能提升是值得的。

SDS 的二进制安全特性也值得一提。C 字符串用 '\0' 判断结束，而 SDS 用 len 字段判断结束，所以它可以存储任何二进制数据，包括含有 '\0' 字节的数据。这使得 Redis 的 String 可以胜任图片、压缩文件、Protobuf 编码数据等任意二进制内容的存储任务。这也是为什么线上有人用 Redis 存储小体积的图片缓存——虽然这不是 Redis 的典型用法，但在某些场景下确实可行。

### Hash 的底层编码

Hash 的底层也有两种编码：ziplist（压缩列表）和 hashtable（哈希表）。Redis 会根据 Hash 中的字段数量和字段值的长度自动选择使用哪种编码。

ziplist 编码：当 Hash 的总字段数小于 hash-max-ziplist-entries（默认 512）并且每个 field 和 value 的长度都小于 hash-max-ziplist-value（默认 64 字节）时，Redis 使用 ziplist 编码。ziplist 的本质是一块连续的内存区域，所有 field-value 对按顺序紧密排列在一起。每个 field 或 value 前面有一个长度字段标明其占用的字节数，读取时按照"长度+内容"的方式依次解析。

ziplist 的内存效率极高。因为所有数据都在一块连续内存中，没有指针、没有链表节点的额外开销。对比 String 存 JSON 的方案，ziplist 编码的 Hash 能节省 50% 到 70% 的内存。在 Redis 内存就是成本的现实下，这个优化非常可观。如果你的业务中存储了大量的小对象（比如几百万个用户信息），使用 Hash 配合 ziplist 编码能省下 GB 级别的内存。

但 ziplist 也有其弊端。因为数据是连续存储的，插入或删除一个 field 时，需要移动后续的所有数据来腾出或填补空间。当字段数很少时，这种移动的开销可以忽略不计；但当字段数增多后，每次操作的开销就会线性增长。所以当字段数超过 512 时，Redis 会自动升级为 hashtable 编码。这也是为什么默认阈值设置在 512——在 512 以内，ziplist 的连续内存优势大于其移动数据的劣势；超过 512 后，hashtable 的 O(1) 操作优势就凸显出来了。

hashtable 编码：当 ziplist 的条件不满足时，Redis 自动将 Hash 转换为 hashtable 编码。Hashtable 本质上是一个数组加链表的结构。Redis 的哈希表用 MurmurHash2 算法计算哈希值，用拉链法解决哈希冲突。

Hashtable 的查询性能是 O(1)，但有一个隐藏的代价：rehash。当哈希表中的元素越来越多，负载因子（元素数量/数组长度）超过一定阈值时，就需要对哈希表进行扩容，重新分配一个更大的数组，把所有元素重新哈希到新数组中。这个操作如果一次性完成，在数据量大的时候会造成明显的服务卡顿。

Redis 解决这个问题的方式很优雅——渐进式 rehash。在 rehash 期间，Redis 同时维护两个哈希表，一个是旧的（ht[0]），一个是新的（ht[1]）。不是一次性把所有元素从旧表搬到新表，而是每次对字典执行增删改查操作时，顺带迁移一小批数据。这个过程是分散到每一次操作中的，所以用户几乎感知不到 rehash 带来的延迟波动。

渐进式 rehash 的具体流程是这样的。首先，为 ht[1] 分配足够的空间，通常是 ht[0] 的两倍。然后，在字典中维护一个 rehashidx 计数器，初始值为 0。每次对字典执行 CRUD 操作时，将 ht[0] 在 rehashidx 索引上的整个 bucket 迁移到 ht[1]，然后将 rehashidx 加一。当所有 bucket 迁移完毕，rehashidx 被设置为 -1，ht[0] 和 ht[1] 互换角色。

在渐进式 rehash 期间，查询操作需要同时检查 ht[0] 和 ht[1]，性能会有轻微下降。增删改操作则同时作用于两个表。如果你的业务对延迟极其苛刻，最好能预估数据量，通过调整 hash-max-ziplist-entries 和 hash-max-ziplist-value 来让数据尽可能留在 ziplist 编码中，避免 hashtable rehash 带来的性能抖动。

还有一个容易被忽略的细节：Hash 中的 field 在 hashtable 编码下是作为 dictEntry 存储的。每个 dictEntry 包含 key 指针、value 指针和 next 指针，每个指针在 64 位系统中占用 8 字节，加上 key 和 value 各自的 SDS 或 int 编码，以及哈希表数组的指针开销。所以 hashtable 编码的内存消耗远高于 ziplist。在选择编码时，"少字段用 ziplist，多字段用 hashtable"只是默认规则，如果你的业务能够确保字段数不多，强烈建议调大 hash-max-ziplist-entries 的阈值。

### 编码转换的实践影响

理解编码转换对实战有很大的帮助。比如，你在设计一个 Hash 结构存储用户画像标签时，每个用户有 200 个标签字段，每个标签值不超过 50 字节。这种情况下，默认的 ziplist 配置（512 字段/64 字节）完全覆盖了你的需求，数据会以 ziplist 编码高效存储。

但如果随着业务扩展，单个用户的标签数量增长到了 600 个，在超过 512 阈值的瞬间，Redis 会将这个 Hash 的编码从 ziplist 转换为 hashtable。这个转换过程会遍历整个 ziplist，创建 hashtable 的 dictEntry，一次性完成。如果这个 Hash 恰好很大，转换期间 Redis 单线程会被占用，所有其他请求都会等待。

所以，如果业务有明确的预期（比如用户标签在未来会增长到 1000 个以上），建议直接调大 hash-max-ziplist-entries 或在设计时就使用 hashtable 编码，避免运行时的自动编码转换带来的性能抖动。线上环境的稳定性往往就体现在这些提前规划好的细节上。

## 3.6 实战案例：用String实现计数器、用Hash存储用户信息

理论知识最终是要落到代码上的。这一节我们来看两个完整的实战案例，涵盖日常开发中最常用的两种场景。

### 案例一：用String实现文章阅读计数器

先看一个最基础的场景：统计每篇文章的阅读量。这个需求在任何内容平台都存在，是 Redis 计数器最经典的应用场景。

假设我们有一个文章系统，每篇文章都有一个文章 ID，用户每次访问文章时调用计数接口。一个最简单的实现如下：

```java
public class ArticleCounter {
    private Jedis jedis;
    
    public ArticleCounter(Jedis jedis) {
        this.jedis = jedis;
    }
    
    public long incrementViewCount(String articleId) {
        String key = "article:view:" + articleId;
        return jedis.incr(key);
    }
    
    public String getViewCount(String articleId) {
        String key = "article:view:" + articleId;
        return jedis.get(key);
    }
    
    public long incrementLikeCount(String articleId) {
        String key = "article:like:" + articleId;
        return jedis.incr(key);
    }
}
```

看起来没什么问题，但放到线上后，很快会发现第一个隐患：这个计数器的数据存在 Redis 里，一旦 Redis 宕机重启，数据就全部丢失了。对于关键的计数业务来说，这可能是不可接受的。

解决办法是定期将 Redis 中的计数同步到持久化存储中。这里要考虑的是同步的频率和方式：

```java
public void syncToDatabase() {
    String cursor = "0";
    do {
        ScanResult<String> scanResult = jedis.scan(cursor,
            new ScanParams().match("article:view:*").count(1000));
        cursor = scanResult.getCursor();
        List<String> keys = scanResult.getResult();
        for (String key : keys) {
            String articleId = key.replace("article:view:", "");
            String count = jedis.get(key);
            String sql = "INSERT INTO article_stats(article_id, view_count) "
                       + "VALUES(?, ?) ON DUPLICATE KEY UPDATE view_count = ?";
            jdbcTemplate.update(sql, articleId, count, count);
        }
    } while (!cursor.equals("0"));
}
```

这里有一个新手最容易踩的坑：用了 KEYS 来遍历所有 key。KEYS 命令在 Redis 存储的数百万 key 上执行时，会阻塞 Redis 单线程几十秒甚至几分钟。在这个时间段内，所有其他客户端的请求都会被排队，表现为业务大面积超时。这是线上 P0 级事故的常见元凶。一定要用 SCAN 命令代替 KEYS，SCAN 每次只返回一小批 key，不会阻塞服务器。

第二个要考虑的问题是同一个用户反复刷新页面导致的虚高计数。在 C 端产品中，一个用户一天内刷新几十次文章页面是很常见的事，如果不做去重，阅读量就会远远偏离真实值。

一个实用的去重方案是利用 Redis 的 Set 来记录当天已经阅读过的用户：

```java
public long incrementViewCountWithDedup(String articleId, String userId) {
    String dedupKey = "article:viewed:" + articleId;
    Boolean isMember = jedis.sismember(dedupKey, userId);
    if (!isMember) {
        jedis.sadd(dedupKey, userId);
        jedis.expire(dedupKey, 86400);
        String key = "article:view:" + articleId;
        return jedis.incr(key);
    }
    return Long.parseLong(jedis.get("article:view:" + articleId));
}
```

这里有一个隐藏的内存问题：如果文章数量巨大，每篇文章对应的去重 Set 中存储的用户 ID 会持续增长。对于一篇爆款文章，可能有几百万用户阅读，对应的 Set 也会膨胀到几百万个元素。一个缓解方案是只记录当天阅读过的用户，第二天重新计数——通过设置 86400 秒的过期时间实现。但这又导致了"连续两天不同日期的总计"需求，需要一个额外的汇总计数器来进行跨天累加。

在实际工程中，对于阅读量、点赞数这类"最终一致性"要求较高而不是强一致性的指标，更常见的做法是维护一个异步的写入队列：先 INCR 更新 Redis，然后异步发送一条消息到消息队列，由后台的消费者批量回写到数据库。这样既利用了 Redis 的高性能计数能力，又通过数据库持久化保证了数据不丢。

### 案例二：用Hash存储用户信息

用户信息是 Hash 最典型的应用场景。我们来写一个完整的用户信息管理模块，涵盖增删改查和批量操作。

```java
public class UserService {
    private Jedis jedis;
    private static final String USER_KEY_PREFIX = "user:info:";
    
    public UserService(Jedis jedis) {
        this.jedis = jedis;
    }
    
    public void saveUser(User user) {
        String key = USER_KEY_PREFIX + user.getId();
        Map<String, String> fields = new HashMap<>();
        fields.put("name", user.getName());
        fields.put("age", String.valueOf(user.getAge()));
        fields.put("email", user.getEmail());
        fields.put("phone", user.getPhone());
        fields.put("avatar", user.getAvatar());
        fields.put("status", String.valueOf(user.getStatus()));
        fields.put("login_time", String.valueOf(user.getLoginTime()));
        jedis.hset(key, fields);
        jedis.expire(key, 7200);
    }
    
    public User getUser(String userId) {
        String key = USER_KEY_PREFIX + userId;
        Map<String, String> fields = jedis.hgetAll(key);
        if (fields == null || fields.isEmpty()) {
            return null;
        }
        User user = new User();
        user.setId(userId);
        user.setName(fields.get("name"));
        user.setAge(Integer.parseInt(
            fields.getOrDefault("age", "0")));
        user.setEmail(fields.get("email"));
        user.setPhone(fields.get("phone"));
        user.setAvatar(fields.get("avatar"));
        user.setStatus(Integer.parseInt(
            fields.getOrDefault("status", "0")));
        user.setLoginTime(Long.parseLong(
            fields.getOrDefault("login_time", "0")));
        return user;
    }
    
    public void updateUserField(String userId,
            String field, String value) {
        String key = USER_KEY_PREFIX + userId;
        jedis.hset(key, field, value);
        jedis.expire(key, 7200);
    }
}
```

以上代码有一个可以优化的地方：在批量获取多个用户数据时，不要用循环逐条查询。

```java
public List<String> getUsersEmails(List<String> userIds) {
    List<String> emails = new ArrayList<>();
    for (String userId : userIds) {
        String key = USER_KEY_PREFIX + userId;
        String email = jedis.hget(key, "email");
        emails.add(email);
    }
    return emails;
}
```

如果 userIds 列表有 10000 个用户，你会发出 10000 次 Redis 请求，产生 10000 次网络往返。优化方案是用 pipeline：

```java
public List<String> getUsersEmailsOptimized(
        List<String> userIds) {
    Pipeline pipeline = jedis.pipelined();
    List<Response<String>> responses = new ArrayList<>();
    for (String userId : userIds) {
        String key = USER_KEY_PREFIX + userId;
        responses.add(pipeline.hget(key, "email"));
    }
    pipeline.sync();
    List<String> emails = new ArrayList<>();
    for (Response<String> response : responses) {
        emails.add(response.get());
    }
    return emails;
}
```

Pipeline 将 10000 次请求合并到一次网络往返中发送给 Redis，Redis 按顺序执行后批量返回结果。在这个场景下，延迟从 10000 个 RTT 降低到了 1 个 RTT，性能提升极其明显。

上面每种操作都做了 expire 设置，这是为了防止数据变成僵尸 key。但 expire 每次更新都有轻微的 Redis 内部开销。可以选择在 saveUser 时设置过期时间，在 updateUserField 时不再重复设置，以减少不必要的命令执行。如果你的业务中用户信息在持续更新，可以在每次写操作时都设置过期时间，保证活跃用户的信息始终不被淘汰，而久未更新的用户信息会过期，释放内存。

还有一个进阶用法：使用 Hash 的不同 key 前缀来区分不同数据类型。比如基础信息用 `user:info:1001`，账号设置用 `user:config:1001`，行为偏好用 `user:pref:1001`。这样既发挥了 Hash 按字段组织数据的能力，又避免了一个 key 中字段过多导致 ziplist 编码失效。三个小的 Hash 各自在 ziplist 编码下高效工作，总内存占用远小于一个巨大的 Hash。

我曾在线上踩过一个和 Hash 容量有关的大坑。某个项目早期用 String 存用户信息 JSON，上线后一切正常。随着用户增长，key 从几百个涨到几百万个。某天运营需要一个遍历全量用户数据的功能，用 SCAN 命令开始扫描。由于 String 存的是 JSON，每次 SCAN 要取出完整的 JSON 字符串，数据量大且消耗带宽，导致整个 Redis 实例的响应时间飙升，大面积超时。

后来花了两个通宵把所有用户数据从 String 迁移到了 Hash。迁移方案是这样的：

```
逐个读取旧的 String key，解析其 JSON 内容
将各字段写入对应的 Hash key：HSET user:hash:{id} field1 val1 field2 val2
确认数据写入成功后，删除旧的 String key
```

迁移时有两个关键问题要处理好。第一，迁移期间新数据可能在持续写入旧的 String key，需要双写策略——同时写入旧 String 和新 Hash，等数据验证一致后再切换读流量。第二，迁移要分批进行，控制每批 SCAN 的 COUNT 大小，避免一次性操作过多 key 对 Redis 造成压力。

迁移完成后内存节省了 60%，原因正是 ziplist 编码的高密度存储特性。原本每个用户是一个独立的 String key，经过 JSON 序列化后还要加上 redisObject 和各种 SDS 头部的开销。转为 Hash 后，同一用户的字段都存放在同一个 key 下，ziplist 将其紧凑排列，内存利用效率大幅提升。这个经历让我从此在做缓存设计时，始终把"按对象维度聚合字段"作为第一条原则。

## 总结

这一章我们深入解剖了 Redis 最基础也最重要的两种数据结构：String 和 Hash。它们看起来简单，但背后凝聚了 Redis 团队在内存管理和性能优化上的深刻思考。

String 是你在 Redis 中的瑞士军刀。它能存文本、数值、二进制数据，SET 和 GET 是最基本的使用方式，SETEX 控制生存时间，SETNX 实现分布式锁，INCR 和 DECR 扛起高并发计数器，MSET 和 MGET 处理批量读写，APPEND 和 GETRANGE 支持特殊场景的字符串操作。它的底层 SDS 解决了 C 字符串的三大痛点——O(1) 长度获取、预分配减少内存分配次数、二进制安全。如果你要在 Redis 里存最简单的单值数据，选 String 准没错。

Hash 是专门为存储对象而生的数据结构。它让操作粒度精确到字段级别，解决了 String 方案中"改一字段、取一整个对象"的性能浪费。配合 ziplist 编码，Hash 在字段数较少时可以大幅节省内存。HSET、HGET、HMGET、HINCRBY 等命令覆盖了对象存储的各种需求。存储对象信息时，Hash 是公认的最优方案。

String 和 Hash 各有自己的最佳适用场景。String 适合单值缓存、分布式锁、计数器；Hash 适合对象存储、属性管理。理解它们的底层编码机制，尤其是 SDS 的设计哲学和 ziplist 的性能边界，能帮你在设计缓存方案时做出更优的选择，避免"等到线上出问题了才发现设计有问题"的被动局面。这套"理解底层、敬畏内存、关注场景"的设计思路，在后续学习 Redis 的其他数据结构时同样适用。

系列进度 3/16

下一章我们将继续探索 Redis 的另外三种核心数据结构：列表（List）、集合（Set）和有序集合（Sorted Set）。List 是消息队列和时间线场景的常客，它可以实现先进先出的队列和先进后出的栈。Set 擅长标签系统和去重操作，其交并补集合运算在社交推荐中不可或缺。ZSet 的分数排序特性在排行榜业务中不可替代，它平衡了插入性能和排序需求，是很多实时排名系统的核心。这三种结构各有独门绝技，在特定场景下不可替代。

看完这一章，你在项目中用过 String 和 Hash 做过哪些有趣的事？有没有用 String 实现计数器时遇到过并发问题？用 Hash 存用户信息时有没有踩过内存暴涨的坑？或者你在 ziplist 和 hashtable 编码切换时遇到过意想不到的性能问题？欢迎在评论区分享你的实战经验，一起交流踩坑心得。

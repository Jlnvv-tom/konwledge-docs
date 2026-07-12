---
sidebar_position: 10
---

# 第10章 Redis分布式应用：会话共享与分布式计数器

如果你的系统还跑在单机应用上，那会话（Session）和计数这两件事根本不算问题。Tomcat 自己就把登录状态存好了，一个 `i++` 就能统计接口调用次数，数据库自增主键也干得漂亮。但一旦你的服务被拆成多个节点，又或者前端通过 Nginx 把流量轮询打到不同机器上，麻烦就来了：用户明明刚登录完，刷新一下页面就被踢回登录页；库存计数器在并发下莫名其妙变成负数；接口被脚本刷爆却拦不住；订单表的主键在分库分表后疯狂撞车。本章要解决的，正是分布式架构下最基础、也最容易踩坑的两个问题——会话共享与分布式计数，外加一个紧密相关的延伸话题：分布式 ID 生成。

我在这三个方向上都交过学费。Session 永不过期把 Redis 内存打爆过，计数器用错写法丢过数据，ID 生成器成为全局热点拖垮过整条链路。所以这篇文章不是 API 文档的搬运，而是带着踩坑经验，从原理到代码把每一处坑点都标出来。你可以把它当成一份“生产环境避坑手册”。

## 10.1 分布式会话的核心需求：跨服务会话一致性

先说一个真实场景。早期我们做的是一个典型的 Spring Boot 单体应用，前后端分离，登录之后后端把用户信息共享到 HttpSession，前端拿着 JSESSIONID 的 Cookie 来维持登录态。一切都很美好，直到流量涨上来，单机扛不住了，我们加了一台机器，前面挂了 Nginx 做负载均衡，用的是默认的轮询策略。

问题立刻出现了：用户登录请求被打到 A 机器，Session 存在 A 的内存里；紧接着的第二个请求被轮询到 B 机器，B 的内存里根本没这个 Session，于是框架认为用户没登录，直接返回 401。用户看到的就是“登录了又秒退”，被这个现象折腾得够呛，客服投诉一度飙升。

这就是典型的跨服务会话一致性问题。在单体时代，Session 是进程内的内存对象，一台机器一份，不存在共享问题。但到了分布式架构，用户的多次请求很可能落到不同节点，谁都不能保证“这次请求和上次请求在同一台机器上”。要让任意节点都能识别同一个用户，就必须把 Session 从进程内存里搬出来，放到一个所有节点都能访问的公共存储里。

业界常见的解决方案有几种，我们逐一看看它们的坑，免得你重蹈覆辙。

第一种是会话粘滞（Session Affinity），也叫 IP Hash。Nginx 根据客户端 IP 做哈希，把同一个 IP 的请求永远打到同一台机器。实现简单，几乎零改造成本，改两行 Nginx 配置就行：

```nginx
upstream backend {
    ip_hash;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}
```

但它的致命缺陷是“无法平滑扩容和容灾”。一旦某台机器宕机，上面的所有 Session 全部丢失，用户集体掉线；而且如果大量用户集中在同一 IP（比如公司 NAT 出口、校园网），流量会严重倾斜，负载均衡形同虚设。我们在一次机房割接时就因为一台机器下线，导致三分之一用户被强制登出，体验极差，当晚就被拉去复盘。

第二种是 Session 复制，比如 Tomcat 自带的 `DeltaManager`。节点之间互相广播 Session 变更，每台机器都保存全量 Session。小集群（2-3 台）还行，一旦节点变多，网络广播的开销会指数级放大，内存也会被全量数据拖垮。我们压测过 8 节点集群，Session 复制让整体吞吐量掉了将近 40%，而且节点越多越慢，直接否掉。

第三种，也是本章重点，就是把 Session 集中存储到外部中间件，典型就是 Redis。登录状态写入 Redis，所有节点需要时去 Redis 取。节点宕机不影响数据，扩容也只是加机器，Session 层完全无状态。代价是多一次网络 IO，但相比带来的弹性和可靠性，这点开销完全可接受。而且 Redis 自带过期机制和持久化，天然契合 Session 生命周期管理。

实践中我们给 Session 单独部署了一个 Redis 主从 + 哨兵集群，并不和其他缓存混用。原因有二：一是 Session 数据对可用性要求极高，不能因为缓存大 key 抖动或缓存穿透把 Session 集群拖垮；二是 Session 的过期清理依赖 Keyspace 通知，和其他业务共用一套 Redis 配置容易互相干扰。别小看 Session 的内存占用——一个 2KB 的 Session 乘以 100 万在线用户就是 2GB，所以 Session 存储的 Redis 要单独规划容量，并且配合 LRU 淘汰做兜底。

把三种方案放在一起对比会更清晰：会话粘滞胜在零改造成本、读本地最快，但容灾差、易倾斜；Session 复制胜在语义透明，但广播开销随节点数指数上升，扩展性差；Redis 共享改造成本中等（有 Spring Session 兜底几乎无感），扩展性、容灾性都好，唯一代价是每次请求多一次 Redis IO。从工程成熟度看，Redis 共享是唯一能平滑支撑从 2 台到 200 台集群演进的方案，所以它成为绝大多数分布式系统的默认答案。

所以结论很清楚：在分布式架构下，Session 共享的推荐方案就是把会话状态外部化到 Redis。它解决的核心需求就是跨服务会话一致性——无论用户请求落到哪台机器，拿到的都是同一份登录状态。更进一步，当你的 Redis 本身也是集群部署时，还要注意 Session 数据的可用区分布，避免 Redis 单点故障连带让所有用户掉线。生产上建议用 Redis Sentinel 或 Cluster 做高可用，至少保证 Session 层不会成为系统的单点。

这里有一个值得展开的知识点：会话一致性本质上是在 CAP 三角里做取舍。把 Session 放 Redis 共享，意味着所有节点强一致地读到同一份状态（偏向 CP），代价是每次请求多一次 Redis IO（牺牲一点可用性 A，因为 Redis 挂了就读不到会话）。而“会话粘滞”方案偏向 AP，节点各自持有状态，可用性好但一致性差。Spring Session + Redis 之所以成为业界主流，是因为 Redis 本身高可用（Sentinel/Cluster）做得很好，CP 方案的可用性短板被补齐了，而它带来的强一致好处是 AP 方案给不了的。理解这一点，你就能根据不同的业务容忍度做选型：金融类强一致选 Redis 共享，对一致性极度不敏感的工具类站点，粘滞方案也未必不行。

还有一个很多人会问的对比：那为什么不直接用 JWT 把用户信息放 Token 里，彻底无状态？确实，JWT 能省掉集中存储，但它有两个硬伤——一是 Token 无法主动失效（除非维护一个黑名单，而黑名单又得集中存，绕回来了），二是 Token 体积大、每次请求都带，且一旦签发无法修改里面的内容（比如用户被封禁，得等 Token 自然过期）。所以对“需要服务端能随时吊销登录态、能感知在线状态”的系统，Redis 会话共享仍然是更稳妥的选择。JWT 更适合一次性凭证、服务间短期鉴权等场景。

最后补充一个我们线上用过的折中：会话粘滞做第一层（让大部分请求落到原机器，命中本地若有缓存可省一次 Redis IO），Redis 共享做兜底（本地没有或失效时去 Redis 取）。这种“粘滞 + 共享”的混合架构，在热点会话下能把 Redis 压力再降一截，但实现复杂度更高，只建议在超大流量且对延迟极度敏感的场景考虑。

还有一个和产品体验强相关的细节：Session 超时时间的设定。默认的 30 分钟是“最后一次访问后 30 分钟失效”，这对普通 Web 应用合理，但对“记住我”类的长效登录（如 7 天免登）就不合适。做法不是把全局 timeout 改成 7 天（那会让所有会话都变长，内存压力翻倍），而是登录时按是否勾选“记住我”动态设置 `setMaxInactiveInterval`：勾了就设 7 天，没勾就走默认的 30 分钟。这样长短会话分开管理，既照顾体验又不浪费内存。

## 10.2 基于Redis的会话共享实现：Spring Session集成

提到 Spring 生态下的会话共享，首推 Spring Session。它不是重新发明一套会话机制，而是用 `HttpSession` 的适配层，把原本存放在 Tomcat 内存里的 Session 透明地替换为 Redis 存储。业务代码几乎零改动，你照样写 `request.getSession().setAttribute("user", user)`，底层已经换成 Redis 了。这层抽象的精妙之处在于：你的 Controller、Interceptor 里所有 `HttpSession` 的读写代码一行都不用改，迁移成本极低。

先上依赖。我们用的是 Spring Boot 3.x，核心就两个 starter：

```xml
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session-data-redis</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

然后是配置，application.yml 里指定 Session 存储类型为 Redis，并配置连接和超时：

```yaml
spring:
  session:
    store-type: redis
    timeout: 30m
    redis:
      namespace: "session:app"
  data:
    redis:
      host: 127.0.0.1
      port: 6379
      password: yourpassword
      database: 0
```

注意这里的 `timeout: 30m`，它控制的是 Session 的过期时间，也就是用户 30 分钟不操作就自动失效。这个配置非常关键，后面会讲一个和它相关的线上事故。另外 `namespace` 建议按应用隔离，避免多应用共用一个 Redis 时 Session key 互相污染。

顺便提醒一个多人协作时容易踩的坑：测试环境、预发环境、生产环境如果共用同一个 Redis 和同一个 namespace，A 同事在测试环境登录产生的 Session 会污染 B 同事在预发环境的登录态，排查时一头雾水。规范做法是用 Spring Profile 给 namespace 注入环境前缀，比如 `session:app:test` / `session:app:prod`，从配置层面彻底隔离。我们曾经因为测试环境和预发环境 namespace 相同，导致预发联调时登录态时有时无，花了半天定位才发现是 Session 串了。

启动类上加 `@EnableRedisHttpSession` 也可以，不过在 Boot 3 里只要引入了 starter 并指定了 `store-type`，自动配置就会生效，一般不用手动加注解。如果你需要更细的控制（比如自定义超时、自定义 RedisFlushMode），才需要显式加注解或配置类。

接下来是第一个大坑：序列化。Spring Session 默认用的是 JDK 原生序列化，把整个 Session 对象以二进制形式存进 Redis。这会带来两个问题。一是可读性差，你在 Redis 里 `get session:app:sessions:xxx` 看到的是一堆乱码，排查问题时根本看不出存了什么。二是强耦合 Java 类，一旦你的 User 类改了字段、改了包名，老 Session 反序列化直接失败，用户集体掉线。

我们的解法是自定义 `RedisSerializer`，改用 JSON 序列化：

```java
@Bean
public RedisSerializer<Object> springSessionDefaultRedisSerializer() {
    // 使用 Jackson 的 JSON 序列化，保证可读与可演进
    return RedisSerializer.json();
}
```

但要注意，Session 里存的对象必须能被 JSON 正确还原，建议存 DTO 而不是实体类，并且加上无参构造。我们曾经因为 User 实体类里有个 `LocalDateTime` 字段，Jackson 默认反序列化失败，导致所有老 Session 在重启后失效，用户集体重登。后来统一改成 DTO + 显式类型配置才解决。

第二个坑，也是线上事故级别的：Session 过期时间被“续命”导致内存暴涨。Spring Session 默认开启 `redis.flushMode = ON_SAVE`，并且每次请求都会刷新 Session 的过期时间。如果你的系统里有些接口被前端轮询（比如每 5 秒拉一次消息），那这个用户的 Session 会永远不过期，Redis 里的会话数据只增不减。我们曾经因为前端一个心跳接口，导致 Redis 中活跃 Session 数量从几万飙到上百万，内存直接打满，触发 OOM 连锁反应。

解决办法有两个：要么把心跳这类接口排除在 Session 创建之外，要么把 `flushMode` 改成 `IMMEDIATE` 并且合理设置超时。更稳妥的是给 Redis 的 Session 命名空间单独设置 maxmemory 和淘汰策略，避免拖垮整个实例。我们最终的做法是：心跳接口走单独的轻量鉴权（只校验 token 不创建 Session），并对 Session 专属 Redis 实例设置 `maxmemory-policy allkeys-lru` 作为兜底。

第三个坑是 Cookie 的 SameSite 和域名问题。Spring Session 默认写入的 Cookie 名为 `SESSION`，如果前端和后端不同域（比如 `api.xxx.com` 和 `www.xxx.com`），需要配置 `cookie.domain` 和 `cookie.path`，否则浏览器不会把 Cookie 带过去，又会出现“登录了但是取不到”的假象。在 Spring Boot 3 中通过 `spring.session.cookie.*` 配置即可。另外现代浏览器默认 `SameSite=Lax`，跨站请求（比如从第三方页面跳转回来）可能不带 Cookie，必要时应显式设为 `None; Secure` 并配合 HTTPS。

第四个坑，很多人在云上 Redis（如阿里云、ElastiCache）会遇到启动报错：`ERR unknown command 'CONFIG'`。这是因为 Spring Session 默认会尝试执行 `CONFIG` 命令去配置 Keyspace Notification，而云厂商禁用了该命令。解决办法是显式声明一个 `ConfigureRedisAction.NO_OP` 的 Bean，跳过自动配置：

```java
@Bean
public ConfigureRedisAction configureRedisAction() {
    // 云上Redis禁用CONFIG命令时的必配项
    return ConfigureRedisAction.NO_OP;
}
```

同时需要你手动开启 Redis 的 `notify-keyspace-events` 配置（在云控制台或 redis.conf 设置 `Ex`），否则过期 Session 不会被及时清理。这里要理解一个关键机制：Redis 的 key 过期后并不会立即删除，而是惰性删除+定期删除，Spring Session 依赖 Keyspace 通知来触发 `SessionDeletedEvent` 做后续清理（比如通知 `SessionRepository` 删除）。如果通知没开，过期的 Session 数据会残留在 Redis 里，虽然不影响功能，但会缓慢吃内存。

顺带说一下 Spring Session 在 Redis 里到底存了什么，这在排查问题时极其有用。它会为每个会话创建两类 key：一类是 `session:app:sessions:{sessionId}`，类型是 Hash，里面存着 `sessionAttr:user` 这样的字段（你 setAttribute 的键值对）以及 `creationTime`、`maxInactiveInterval`、`lastAccessedTime` 等元数据；另一类是 `session:app:expirations:{时间戳}`，用来按过期时间索引，配合 Keyspace 通知清理。当你发现某个用户“查不到登录态”时，直接 `HGETALL session:app:sessions:{id}` 就能看到这个会话里到底有没有 user 字段、maxInactiveInterval 是不是 0（0 表示永不过期，往往是前面说的心跳坑导致的）。掌握了这套 key 结构，排查 Session 问题就不再是黑盒。

还有一个安全维度不能漏：Session 集中存储后，一旦 Redis 被攻破，所有用户的登录态都会泄露。所以 Redis 必须开启密码认证、网络隔离，敏感信息（如密码、token）不要直接塞进 Session，只存用户标识和必要上下文即可。

会话安全还要提防“会话固定攻击（Session Fixation）”。攻击者先访问系统拿到一个 SessionID，诱导用户用这个 ID 登录，用户登录后服务端如果只是在原 Session 里写入用户标识而不换 ID，攻击者就能用同一个 ID 冒用用户身份。Spring Session 默认在登录（`Authentication` 变更）时会调用 `changeSessionId` 换掉旧 ID，这是对的；但如果你们自己手写了会话逻辑，一定要记得在“登录成功”那一刻生成新 Session、废弃旧 Session。我们曾经审计出一个老接口，登录后只是 `setAttribute` 没换 ID，被安全团队当作高危漏洞打了回来。

多端登录也是一个常见需求与坑点。产品常要求“同账号只允许一端登录”或“允许手机和 PC 同时在线但互踢”。用 Redis 做会话共享后，可以在登录时把 userId 与当前 SessionID 的映射写进 Redis（如 `login:user:{uid} -> sessionId`），新登录时对比旧 SessionID，发现不同就把旧 Session 从 Redis 删掉，实现互踢。这比单机时代用静态 Map 存映射靠谱得多，因为 Map 在多实例下不共享。

再深入一层 Spring Session 的读写成本，这点对性能敏感的服务很重要。每个请求进来，Spring Session 的 `SessionRepository` 都会用 `HGETALL` 去 Redis 拉取整个会话 Hash 来还原 `HttpSession`，请求结束若会话被改动再写回。也就是说，哪怕是个只读的公开接口，只要走了 Session 解析过滤器，就会多一次 Redis 往返。我们对高频只读接口（比如商品详情页）做了优化：在过滤器里判断“该路径无需登录”就提前放行、不触发 Session 加载，RT 平均降了 3~5 毫秒。另一个隐蔽坑是“变更检测”：Spring Session 通过比对属性引用判断是否脏数据，如果你直接修改了 Session 里对象的字段（比如 `user.setName("x")`）却没再 `setAttribute`，框架可能认为会话没变、不写回 Redis，重启后修改就丢了。正确做法是对 Session 里存的对象做任何修改后都重新 `setAttribute` 一次，强制标记脏数据。

性能上还有个细节容易被忽略：Redis 连接池。Session 每次读写都走 Redis，如果连接池太小（默认 lettuce 是按需创建但上限受约束），高并发下会排队等连接，RT 直接飙高。我们给 Session 专用的 Redis 客户端单独配了较大的连接池（max-active 调到 200+），并和缓存、计数用的 Redis 客户端做隔离，避免“缓存大 key 查询慢”拖慢会话读写。有人图省事把整个用户权限树、菜单列表都塞进 Session，一个对象几 KB 甚至几十 KB，乘以几十万用户就是几个 G。Session 只应该放用户标识和少量必要信息，权限、菜单这类数据走缓存或每次鉴权时查。我们定了一条团队规范：单个 Session 序列化后不得超过 2KB，超出就拆到独立的 Redis 缓存里按 userId 存取。

## 10.3 分布式计数器的应用场景：秒杀库存、接口限流

说完会话，我们再来看分布式计数器。计数器是所有业务里最高频的原子操作之一，但它在分布式环境下远没有 `i++` 那么简单。你必须时刻记住：在并发世界里，“读出来再加回去”是一条通往数据错乱的捷径。

最典型的场景是秒杀库存。假设一个商品只有 100 件，瞬时涌入 10 万请求。如果用数据库 `select` 查库存再加 `update`，不仅数据库被打爆，而且并发下会出现超卖——多个请求同时读到库存=1，各自判断通过，结果库存变成 -5。这是经典的竞态条件，也是每年大促必有人翻车的重灾区。

另一个高频场景是接口限流。比如一个短信验证码接口，要限制同一个手机号 1 分钟内最多发 5 条，或者一个 IP 每秒最多访问 10 次。如果每台机器各自用本地计数器，那 3 台机器就是 3 倍额度，限流形同虚设。必须有一个全局统一的计数视角，而这个视角天然应该放在 Redis 里。

除此之外，计数器还广泛用于：文章点赞数、阅读量（PV/UV）、用户积分变更、每日签到统计、在线人数、优惠券已发放数量、接口调用统计等。它们有一个共同特征——高并发写、需要准确、必须原子。

这些场景下，如果用关系数据库做计数，写热点会迅速成为瓶颈。你可能会想用 `update counter = counter + 1 where id = ?`，但高并发下这行 SQL 会在行上产生激烈的行锁竞争，吞吐量急剧下降；要是再加乐观锁版本号，失败重试又会放大流量。Redis 的 `INCR` 系列命令天生是单线程原子操作，单实例轻松扛几万 QPS，天然适合干这个活。

不过要特别注意，计数器“准”和“快”之外，还有“可靠”的要求。这里有个核心架构原则：Redis 计数器通常作为“前置闸门”和“实时展示”，真正的持久化数据以数据库为准。我们用一个“Redis 做令牌闸门、数据库做最终账本”的模式：秒杀时先 `DECR` 扣 Redis 库存，扣成功才放行进业务，业务完成后异步把数据库库存减掉；如果两者出现偏差，有定时对账任务兜底补偿。切勿把 Redis 里的计数当成“唯一真相源”，它掉电、被清、主从切换丢数据都有可能。

除了秒杀和限流，计数器还有一类很典型的场景是“每日统计类”，比如每日签到人数、每日新增用户、每日订单数。这类需求的特点是按天分桶，用 `INCR` + 带日期的 key 即可：`stat:sign:2026-07-12`。但它有一个隐藏的性能陷阱：如果每天零点刚过，所有 key 都是新建，大量请求同时 `INCR` 并首次 `EXPIRE`，虽然是原子的，但 key 数量瞬时暴涨，且如果没给 key 设过期，一年就积累 365 个永不删除的 key，长期看是内存泄漏。正确做法是首次 INCR 时设一个合理的过期（比如 7 天），只保留近期数据，历史数据异步落库到统计表。

抽奖、红包雨这类“库存有限且必须精确”的场景，和秒杀是同一类问题，核心都是“扣减不超发”。我们的经验是：凡是有“总数量上限”的扣减，一律走 Redis 做前置闸门，且扣减逻辑必须原子。曾经有个活动把“剩余抽奖次数”只存在数据库，靠 `UPDATE ... SET remain=remain-1 WHERE remain>0` 来防超发，结果活动上线瞬间数据库行锁打满，接口大面积超时。把计数前置到 Redis 后，数据库压力降了 90% 以上。

把“计数器”和“限流”串起来看，最简单的接口防刷其实就是 10.4 讲的 `INCR` + 首设过期。比如短信验证码限制同一手机号 1 分钟最多 5 条，几行就能搞定。

再强调一个架构原则：计数与展示分离。很多人把“实时计数”和“计数展示”混在一起，每次展示都去 Redis `GET` 一下，结果展示接口的 QPS 反超了业务接口，把 Redis 打爆。正确做法是：计数在写路径上异步聚合（比如每 5 秒汇总一次写进一个展示专用 key），展示接口只读这个汇总 key，甚至把汇总值推到本地缓存，彻底不依赖 Redis 实时读。我们一个千万级 PV 的页面，就是靠“写时 INCR + 定时汇总 + 本地缓存展示”三件套，把计数读取的 Redis 压力降到几乎为零。

```java
String key = "sms:limit:" + phone;
Long cnt = redisTemplate.opsForValue().increment(key);
if (cnt == 1) redisTemplate.expire(key, Duration.ofMinutes(1));
if (cnt > 5) throw new RuntimeException("验证码发送过于频繁");
```

这种写法在中小流量下完全够用，但它属于固定窗口（分钟边界可能短暂放行 10 条），要更平滑就回到 10.5 的令牌桶/Lua。选型时别一上来就上复杂方案，能用 5 行 `INCR` 解决的，就别引入 Lua 和 ZSET 的复杂度。

还有一点关于数据库计数器的沉痛教训：用 `SELECT ... FOR UPDATE` 做计数悲观锁，在分库分表或主从延迟场景下极易死锁或读到旧值；用乐观锁版本号又会在高并发下大量重试放大流量。Redis 计数器的价值，不只是“快”，更是把“争抢”从数据库这种珍贵资源上挪走，让数据库专心做它擅长的事务性持久化。架构上要分清：高频、可容忍短暂最终一致、需要原子递增的，放 Redis；需要强事务、强持久、不可丢的，落数据库。两者通过异步对账对齐，而不是抢同一个资源。Redis 是内存数据库，万一重启或数据丢失，计数器归零怎么办？像点赞数这种丢了还能从数据库重新统计的还好，但像“已发放优惠券数量”这种，重置就意味着多发。所以关键计数器要有持久化兜底（RDB+AOF 都开）和启动时的数据预热（从 DB 同步一次当前值），不能假设 Redis 里的值永远是对的。我们专门写了启动时 `initCounters()` 方法，把核心计数从 DB 加载进 Redis，避免冷启动瞬间计数全 0 引发误判。

关于持久化再补一句：计数器所在的 Redis 实例，建议同时开启 RDB（定时快照，恢复快）和 AOF（追加日志，丢数据少），并且把 `appendfsync` 设为 `everysec`（每秒刷盘，性能和安全的折中）。千万别用默认的纯 RDB 且快照间隔过长，否则 Redis 宕机可能丢掉几分钟的计数增量，对账时会发现“Redis 和 DB 差了好几千”。我们曾经因为 AOF 没开，一次 Redis 重启丢了 3 万次阅读计数，虽然能从日志回放，但回放本身花了两小时，教训深刻。

## 10.4 分布式计数器实现：incr命令与原子性保障

Redis 的计数核心是 `INCR` 命令。它把 key 中存储的数字值加 1，如果 key 不存在则先初始化为 0 再加 1，返回加之后的值。最关键的一点是：这个“读-改-写”的过程在 Redis 单线程模型下是原子的，不会被其他命令打断。原子性意味着：在 `INCR` 执行的这一瞬间，没有任何其他客户端能看到“中间状态”，它看到的要么是加之前的值，要么是加之后的值。

对比一下错误和正确的写法，这是新手最容易踩的坑。下面这种用 `GET` + `SET` 的自增，在并发下一定会丢计数：

```java
// 错误示范：非原子，并发下严重丢计数
Integer count = (Integer) redisTemplate.opsForValue().get("view:1001");
if (count == null) count = 0;
count = count + 1;
redisTemplate.opsForValue().set("view:1001", count);
```

这段代码在高并发下，100 个线程同时读到 count=10，各自加 1 后都写回 11，结果实际只加了 1 而不是 100。我把这个称为“读改写三连，并发必翻车”。我们把这个丢计数的过程画成时间线会更直观：假设初始 count=10，线程 A 和线程 B 几乎同时到达。时刻 T1，A 执行 GET 读到 10；T2，B 也执行 GET 读到 10（因为 A 还没写回）；T3，A 计算 10+1=11 并 SET 写回；T4，B 同样计算 10+1=11 并 SET 写回。最终 Redis 里是 11，但实际发生了两次自增，应该到 12。问题就出在 T1 和 T2 之间，两个线程基于同一个旧值做计算，后写者覆盖先写者。当并发量越大，这种“读到的旧值”被越多线程共享，丢的计数就越离谱。而 `INCR` 之所以安全，是因为 Redis 单线程执行模型保证：GET、加 1、SET 这三步在它内部是一次性完成的中间状态对外不可见，不存在 T1/T2 都读到旧值的可能。

正确的做法是用 `INCR`，一行搞定，把读改写交给 Redis 原子执行：

```java
// 正确示范：原子自增，永不丢计数
Long count = redisTemplate.opsForValue().increment("view:1001");
// 返回的就是自增后的最新值，可直接用于实时展示
```

除了 `INCR`，还有几个兄弟命令要记住：`INCRBY` 指定步长（比如一次扣 10 个库存）、`DECR` / `DECRBY` 递减、`INCRBYFLOAT` 浮点自增（用于金额、积分这类带小数的计数）。

针对秒杀库存这种“不能超卖”的场景，单纯 `INCR` 不够（它只会一直加），你应该用 `DECR` 后判断是否为负，负数就回滚：

```java
Long remain = redisTemplate.opsForValue().decrement("stock:1001");
if (remain < 0) {
    redisTemplate.opsForValue().increment("stock:1001"); // 回滚
    return "秒杀已结束"; // 库存不足
}
// 扣减成功，异步落库
return "秒杀成功";
```

不过要注意，这种“先扣后判”再回滚的方式，在极端高并发下会有短暂“库存短暂为负”的窗口，一般不影响业务（因为负数会被回滚），但如果你要求库存显示永远非负，更稳妥的是用 Lua 脚本做“判断+扣减”的原子操作，把判断逻辑也放进脚本里，避免回滚带来的并发抖动。后面 10.5 的限流我们会用 Lua 来演示这种模式。

除了 String 类型的 `INCR`，Hash 类型也有 `HINCRBY`，适合做“多维度计数”。比如统计每篇文章每天的阅读量，可以用一个 Hash 把日期作为 field：

```java
// 按日期维度统计阅读量，避免为每天建一个 key
redisTemplate.opsForHash().increment(
    "article:views:1001", "2026-07-12", 1);
// 取某天阅读量
Object today = redisTemplate.opsForHash().get("article:views:1001", "2026-07-12");
```

这两种数据结构的选择有个经验法则：如果计数是单一的（一个 key 一个数），用 String + INCR；如果计数是分组的、多维的（一个实体下多个计数项），用 Hash + HINCRBY，能大幅减少 key 的数量，也方便批量读取。

举个电商场景：一个商品要同时统计“浏览、收藏、加购、下单”四个计数，如果用四个 String key 就太碎了，用 Hash 一个 key 存四项最合适：

```java
// 一次 HINCRBY 自增某个维度，HGETALL 一次取全部维度
redisTemplate.opsForHash().increment("stat:sku:888", "view", 1);
redisTemplate.opsForHash().increment("stat:sku:888", "cart", 1);
Map<Object, Object> all = redisTemplate.opsForHash().entries("stat:sku:888");
```

这样展示商品的热度面板时，一个 `HGETALL` 就能拿到全部四个计数，比四次 `GET` 省事也更省连接。但要注意 Hash 的字段数也别无限膨胀，如果一个 key 下挂了几千个 field（比如按城市统计），`HGETALL` 会变成大 key 操作，要改用 `HSCAN` 分批拉取。

再提一个常被忽略的兄弟命令 `INCRBYFLOAT`，它用来做带小数的原子自增，比如账户积分里含有小数部分的余额累计。普通 `INCR` 只支持整数，金额类计数若用整数分来存储没问题，但如果你存的是带小数的数值（如积分含 0.5 这样的奖励），就得用浮点版本：

```java
// 给用户累加带小数的奖励积分，原子且不会丢精度
double after = redisTemplate.opsForValue()
    .increment("score:user:1001", 0.5);
```

一个注意点：浮点计数存在精度问题，Redis 内部用双精度存储，频繁累加极小的小数可能在末位产生误差。对金额这类绝对不能错的场景，仍建议以“整数分”为单位用 `INCRBY` 存储，展示时再除以 100，杜绝浮点误差。

还有一个常见需求：给计数器设置过期时间，比如限流的计数窗口、每日 UV。这里有个坑：`INCR` 之后如果立刻 `EXPIRE`，两步操作不是原子的，万一中间 Redis 宕机或连接断开，key 就永不过期了，内存泄漏。正确做法是用 `INCR` 配合判断 key 是否首次创建，只在第一次设过期：

```java
Long count = redisTemplate.opsForValue().increment("limit:ip:1.2.3.4");
if (count != null && count == 1) {
    redisTemplate.expire("limit:ip:1.2.3.4", Duration.ofMinutes(1));
}
```

这里利用 `count == 1` 表示这是第一次创建，只在第一次设过期，后续自增不再设，既保证了语义正确，又避免了每次都去 `EXPIRE` 的开销。注意一个小细节：如果 key 在设过期之前就因为某种原因被删除了，`count` 重新从 1 开始，过期会重新设置，这是符合预期的。

说到 UV（独立访客）统计，这里再补充一个利器：HyperLogLog。当你需要统计“去重后的访问人数”，而不在乎具体是谁时，`PFADD` + `PFCOUNT` 用 12KB 固定内存就能统计上亿用户的基数，误差仅约 0.81%。它不适合精确计数，但在 UV 这种“大概齐”的场景性价比极高：

```java
// 统计页面UV，自动去重，内存恒定
redisTemplate.opsForHyperLogLog().add("uv:page:1001", userId);
Long uv = redisTemplate.opsForHyperLogLog().size("uv:page:1001");
```

而“每日签到”这类可以用 Bitmap 来压缩存储，一个用户一天只占 1 个 bit，1 亿用户一年的签到数据也就几百 MB。`SETBIT` / `BITCOUNT` 是这类场景的最优解。举个签到的例子，用 offset 表示一年中的第几天：

```java
// 用户1001在2026年第180天签到
redisTemplate.execute((RedisCallback<Boolean>) conn ->
    conn.setBit("sign:1001:2026".getBytes(), 180, true));
// 统计全年累计签到天数
Long days = redisTemplate.execute((RedisCallback<Long>) conn ->
    conn.bitCount("sign:1001:2026".getBytes()));
```

为什么不直接用 Hash 或 String 存签到？因为 Bitmap 一个用户一年才 365 bit（约 46 字节），而 Hash 存 365 个 field 要几千字节，差距上百倍。计数器的世界远比 `INCR` 丰富，选对数据结构，存储和性能能差出几个数量级。

原子性的本质，说到底就是：任何“先读后写”并依赖读结果做判断的逻辑，在并发下都必须保证读和写在 Redis 内一次性完成。单条 `INCR/DECR/HINCRBY` 命令 Redis 帮你保证了；如果要“判断+写”多条逻辑（比如判断库存够才扣、判断令牌够才放行），就必须上 Lua 脚本来打包。这是本章最重要的心法，请刻进 DNA。

## 10.5 限流场景实战：基于Redis的令牌桶算法实现

限流算法常见的有四种：固定窗口计数器、滑动窗口、漏桶、令牌桶。我们快速对比一下，方便你选型。固定窗口最简单，但临界问题严重——比如限制每分钟 100 次，在 00:59 发 100 个、01:01 又发 100 个，实际上两秒内放了 200 个，限流失效。滑动窗口更平滑但实现复杂。漏桶强调“匀速消费”，请求进桶后以固定速率流出，突发流量会被排队或丢弃，对瞬时洪峰不够友好。实际生产里用得最多的是令牌桶——它允许一定程度的突发流量，平时按固定速率发放令牌，桶满则丢弃，有请求就取走令牌，取不到就拒绝。

令牌桶的核心思想是：系统以恒定速率往桶里放令牌，桶有容量上限。请求到来时尝试取一个令牌，取到就放行，取不到就限流。它既能平滑限流，又能容忍短时突发（桶里积攒的令牌可以一次性被消耗）。比如你设桶容量 200、速率 100/秒，平时流量平稳时桶慢慢积满，一旦突发 200 个请求同时来，桶里积攒的 200 个令牌能一次性全放出去，不会被卡死。

但用 Redis 实现令牌桶有个难点：令牌是“随时间自动补充”的，这意味着每次请求都要先根据当前时间计算“应该补充多少令牌”，再判断是否够扣。这个“计算补充量 + 判断 + 扣减”必须原子完成，否则并发请求之间会互相覆盖令牌数（A 算完补充量还没写回，B 也来算，两人基于同一个旧值，结果补充量被算两次却只生效一次）。所以我们用 Lua 脚本把它包成一个原子操作。

下面是一个简化的令牌桶 Lua 实现：

```lua
-- KEYS[1] 桶key, ARGV[1] 容量, ARGV[2] 速率(个/秒)
-- ARGV[3] 当前时间戳(毫秒), ARGV[4] 本次需要令牌数
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local need = tonumber(ARGV[4])

local data = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
  tokens = capacity
  ts = now
end

local delta = math.floor((now - ts) / 1000 * rate)
tokens = math.min(capacity, tokens + delta)
ts = now

if tokens >= need then
  tokens = tokens - need
  redis.call("HMSET", key, "tokens", tokens, "ts", ts)
  redis.call("PEXPIRE", key, 60000)
  return 1
end
return 0
```

脚本逻辑很清晰：先取出当前令牌数和上次更新时间；根据时间差计算这段时间应该补充多少令牌（速率×秒数），累加上限为桶容量；然后判断是否够本次请求消耗，够就扣减并放行（返回 1），不够就拒绝（返回 0）。整个“计算补充+判断+扣减+写回”在 Lua 中单线程执行，天然原子，不会有并发覆盖问题。

在 Java 侧调用这个脚本，封装成一个限流工具：

```java
public boolean tryAcquire(String key, int capacity, int rate, int need) {
    Long result = redisTemplate.execute(tokenBucketScript,
        List.of(key),
        String.valueOf(capacity), String.valueOf(rate),
        String.valueOf(System.currentTimeMillis()), String.valueOf(need));
    return result != null && result == 1L;
}
```

使用上，比如限制某接口每秒最多 100 次、桶容量 200（允许短时突发到 200）：

```java
if (!rateLimiter.tryAcquire("api:order:create", 200, 100, 1)) {
    throw new RuntimeException("请求过于频繁，请稍后再试");
}
// 正常业务逻辑
```

这里还要补一个工程细节：限流被触发时，别只抛个笼统的异常，应该返回标准的 HTTP 429（Too Many Requests）状态码，并且在响应头带上 `Retry-After` 告诉客户端多久后重试，这样前端和网关都能正确识别和处理，而不是当成 500 服务器错误去触发告警。同时建议把“被限流的次数”也打到监控里，限流次数异常飙升往往意味着有人在刷接口，是安全预警的重要信号。

这里踩过一个坑：Lua 脚本里的时间一定要用调用方统一传入的时间戳，别用 Redis 内部的 `redis.call("TIME")`（集群下主从时间可能有细微偏差，且某些受限环境禁用 TIME 命令）。我们用调用方传时间戳的方式，简单可控。另一个坑是脚本里 `PEXPIRE` 过期时间要设得比令牌补充周期长，避免桶 key 频繁过期导致限流失效。我们设 60 秒，足够覆盖补充逻辑。

再补充一个固定窗口限流的简化实现，适合对精度要求不高的粗粒度场景，代码更短：

```lua
-- 固定窗口：窗口内计数超限则拒绝
local cnt = redis.call("INCR", KEYS[1])
if cnt == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
if cnt > tonumber(ARGV[2]) then
  return 0
end
return 1
```

再补充一个滑动窗口限流的 Lua 实现，它比固定窗口更平滑，能避免窗口临界处的双倍流量。思路是用一个 Sorted Set 存每个请求的时间戳，统计窗口内的请求数，超过阈值就拒绝，并定期清理窗口外的旧记录：

```lua
-- 滑动窗口：用 ZSET 存请求时间戳，统计窗口内数量
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])   -- 窗口大小(毫秒)
local limit = tonumber(ARGV[3])    -- 窗口内最大次数
redis.call("ZREMRANGEBYSCORE", key, 0, now - window)
local cnt = redis.call("ZCARD", key)
if cnt >= limit then
  return 0
end
redis.call("ZADD", key, now, now)
redis.call("PEXPIRE", key, window)
return 1
```

这个脚本先删掉窗口外的旧时间戳，再统计剩余数量，没超阈值才放入本次请求并返回放行。它比固定窗口精确，但每个请求都要写一次 ZSET，高 QPS 下内存和写压力比令牌桶大，适合对精度要求高、QPS 中等的接口。

对比一下不同算法的适用面：固定窗口适合“每分钟最多 N 次”这种粗放保护，代码最少；滑动窗口适合对平滑度有要求的 API 限流；令牌桶适合既要限速又要容忍突发的场景（如网关入口）；漏桶适合下游处理能力固定、必须匀速的消费侧（如写数据库、调用第三方）。我们在网关层用令牌桶，在业务接口层用固定窗口做二次兜底，双层防护。

再讲一个生产上很实用的套路：多维度组合限流。很多时候光限 IP 不够（一个公司 NAT 出口几万人共享一个 IP），光限用户也不够（攻击者可以批量注册账号）。更稳的做法是“用户维度 + IP 维度”同时限，两个维度任一触发就拒绝。实现上就是把两个 key 都跑一遍令牌桶脚本：

```java
boolean byUser = rateLimiter.tryAcquire("limit:user:" + uid, 200, 100, 1);
boolean byIp   = rateLimiter.tryAcquire("limit:ip:" + ip, 500, 200, 1);
if (!byUser || !byIp) {
    throw new RuntimeException("请求过于频繁");
}
```

注意这里两个 `tryAcquire` 不是原子的，理论上存在“用户维度扣了、IP 维度没扣”的不一致，但对于限流这种“宁可错杀不可放过”的场景，这点不一致完全可接受，没必要为了绝对原子去合并脚本（合并反而限制了不同维度用不同阈值）。

关于 Lua 脚本还有个性能细节值得说：频繁调用 `EVAL` 每次都传完整脚本，网络和执行都有开销。生产上应该先 `SCRIPT LOAD` 拿到脚本的 SHA 摘要，之后用 `EVALSHA` 只传摘要，Redis 会复用已缓存的脚本。Spring 的 `RedisTemplate.execute(RedisScript, ...)` 默认就帮你做了 `EVALSHA` 优先、失败回退 `EVAL` 的逻辑，不用自己操心。但要注意：Redis Cluster 里脚本缓存是按节点独立的，如果某节点重启清空了脚本缓存，`EVALSHA` 会返回 `NOSCRIPT`，这时候框架自动回退到 `EVAL` 重传，业务无感——前提是你的脚本是纯函数、不依赖外部状态，否则缓存复用会出 bug。另外脚本里切忌写耗时逻辑（大循环、大 key 遍历），因为 Lua 执行期间 Redis 是阻塞的，一个慢脚本会拖慢整个实例，这是用 Lua 做原子化时最容易忽视的全局风险。

最后提醒，Lua 脚本在 Redis Cluster 下有个硬约束：脚本里涉及的所有 key 必须落在同一个 slot（哈希槽），否则报错 `CROSSSLOT`。如果限流 key 分散在不同 slot，需要保证 key 用相同的 hash tag（用 `{}` 包裹相同部分）让其路由到同一 slot，或者把限流脚本改成只操作单 key。我们的限流 key 都带业务前缀且单 key 操作，天然规避了这个问题。

## 10.6 分布式ID生成：基于Redis的自增ID方案

最后一个话题：分布式 ID。在分库分表、微服务多节点写入的场景下，数据库自增主键会撞车（不同库各自从 1 开始），UUID 又太长（128 位）且无序，作为数据库主键会导致 B+ 树频繁分裂、索引性能差。我们需要在分布式环境下生成全局唯一、趋势递增、高性能的 ID。基于 Redis 的 `INCR` 就是一个轻量级方案。

最简单的形式，直接用 `INCR` 做一个全局自增计数器：

```java
// 每次需要ID时调用，返回全局唯一递增ID
Long id = redisTemplate.opsForValue().increment("id:generator:order");
// 返回的 id 即为全局唯一订单号主键
```

这个方案优点是简单、递增、性能高（单机 Redis 轻松几万 QPS）。但它有三个问题，每一个都可能在生产上咬你一口。

第一，ID 完全暴露业务量。用户看到订单号是 `10086`，就知道前面有 1 万多个订单，这种“裸自增”会泄露规模，还容易被遍历爬取（写个脚本从 1 遍历到 10086 就能扒光所有订单）。生产里我们会拼接业务前缀和时间戳，比如 `ORDER:20260712:10086`，既保留递增可读性，又避免纯数字暴露，而且前缀让 ID 在日志里一眼可辨。

第二，单点性能上限。所有 ID 生成都打到同一个 Redis key，成了全局热点。虽然 Redis 单线程处理 `INCR` 很快，但到了百万级 QPS 还是会瓶颈，而且这个 key 所在的 Redis 节点会成为整个 ID 链路的单点，一旦它慢了，所有依赖 ID 的服务都跟着感冒。解决思路是用“号段模式（segment）”。

号段模式的核心思想是“批量取号”：每次从 Redis 取一段（比如 1000 个）ID 的区间，应用本地缓存后在内存里分配，用完再取下一段。这样 Redis 的访问频率降低 1000 倍：

```java
// 号段模式：一次申请1000个ID的号段
Long maxId = redisTemplate.opsForValue().increment("id:segment:order", 1000);
long start = maxId - 1000 + 1;  // 本段起始
long end = maxId;               // 本段结束
// 应用内用 AtomicLong 从 start 递增分配到 end，用完再申请下一段
```

号段模式把 Redis 的压力分摊到内存分配，单机支撑几十万 QPS 毫无压力，是很多大厂（如美团 Leaf）的基础思路。它的代价是 ID 不是严格连续（号段之间可能有空洞，比如某节点宕机前申请的号段没用完就丢了），但绝大多数业务不要求绝对连续，完全可以接受。我们还做了“双号段缓冲”：当前号段用到 20% 时，后台异步预取下一个号段，避免号段用尽那一刻的同步等待阻塞业务线程。

第三，高可用问题。Redis 挂了 ID 生成就停摆。应对方式：用 Redis 主从+哨兵保证可用性；号段模式下即便 Redis 短暂不可用，本地号段还能撑一阵子，给故障切换留出缓冲窗口，这比纯 `INCR` 方案韧性好得多。我们在关键链路还要求 ID 生成器具备本地降级：Redis 彻底不可用时，临时用 Snowflake 兜底生成，虽牺牲了严格递增，但保住了可用性。

补充一点，Redis 版的 `INCR` 方案适合“趋势递增”即可的场景。如果你要求 ID 包含时间戳、机器号、且完全不依赖外部中间件，可以考虑雪花算法（Snowflake）。它的 64 位 ID 布局通常是：1 位符号位 + 41 位时间戳（可用约 69 年）+ 10 位机器 ID（含 5 位机房 + 5 位机器）+ 12 位序列号（每毫秒 4096 个）。这种结构让 ID 天然按时间递增，且本地生成零网络开销，单机每秒可生成百万级 ID。

二者取舍在于：Redis 方案依赖一个中心节点、实现简单、天然递增，但中心成了瓶颈和单点；雪花算法无中心、去中心化，性能上限极高，但要处理时钟回拨（机器时钟倒退会导致 ID 重复，需要用等待追平或扩展位解决），还要解决机器 ID 的分配问题（不能两台机器配同一个 ID，否则必撞车）。我们通常在“需要强递增且已有 Redis”时选 Redis 方案，在“完全去中心、超高并发、不希望 ID 生成依赖外部组件”时选雪花。

如果你的系统连 Redis 都不想依赖，号段模式也可以直接基于数据库实现（即美团 Leaf 的 DB 号段方案）：用一张 segment 表存 `biz_tag -> max_id, step`，每次用 `UPDATE ... SET max_id = max_id + step` 原子抢一段，应用本地分配。这样 ID 生成完全不依赖 Redis，比 Redis 更稳但性能上限受 DB 限制（单表并发抢段会成为瓶颈，需要分桶缓解）。我们的经验是：中小规模用 Redis 号段（简单够快），超大规模或对 Redis 可用性零信任时，才上 DB 号段或 Snowflake。

无论选哪种，都要给 ID 生成器加监控：当前已分配的号段水位（号段快用尽要有告警）、每秒生成速率、申请号段失败次数。我们曾经因为号段步长设太小（100），在高并发下 Redis `INCRBY` 调用频率过高，反而成了热点；把步长调到 5000 后，Redis 压力降了 50 倍。步长不是越大越好——太大意味着节点宕机时浪费的 ID 区间也大，要在“减少 Redis 交互”和“避免浪费”之间取平衡，一般根据峰值 QPS 估算（峰值 QPS × 平均恢复时间 × 安全系数）。

最后提醒，无论哪种方案，ID 生成器最好做一层封装，避免业务代码里到处散落 `INCR`。统一成一个 `IdGenerator` 接口，后面想从 Redis 方案切到号段模式甚至雪花算法，业务侧无感知：

```java
public interface IdGenerator {
    long nextId(String bizType);
}

@Service
public class RedisSegmentIdGenerator implements IdGenerator {
    // 内部维护号段 + AtomicLong，对外只暴露 nextId
    public long nextId(String bizType) {
        // 取号段、内存自增、越界重新申请
        return current.getAndIncrement();
    }
}
```

这样业务方只管 `idGenerator.nextId("order")`，底层是 Redis 还是雪花，随时可切。这层抽象在我们后续把单 Redis 升级为号段模式时，让 30 多个调用点一行没改，平滑迁移。

号段模式在内存里的分配与续段逻辑，是它高性能的关键，核心就是“本地 AtomicLong 递增 + 越界异步申请”：

```java
private final AtomicLong cur = new AtomicLong();
private volatile long max; // 当前号段上限
public long nextId() {
    long v = cur.incrementAndGet();
    if (v > max) {            // 本段用完，申请下一段
        long newMax = redisTemplate.opsForValue()
            .increment("id:seg:order", 5000);
        cur.set(newMax - 5000 + 1);
        max = newMax;
        v = cur.incrementAndGet();
    }
    return v;
}
```

这段伪代码里，只有当本段号用完才去 Redis 申请下一段，平时 ID 完全在 JVM 内存里分配，零网络开销。生产上建议把“申请下一段”改成后台异步线程（在当前段用到 20% 时提前预取），彻底消除临界点阻塞。

## 总结

本章我们围绕分布式架构下两个最基础也最容易翻车的问题展开了实战。会话共享部分，我强调了为什么“会话粘滞”和“Session 复制”在真正的高可用场景下站不住脚，以及 Spring Session + Redis 的正确集成姿势——包括 JSON 序列化避坑、心跳接口导致 Session 永不过期的内存暴涨事故、跨域 Cookie 配置、云上 Redis 禁用 CONFIG 命令的 `NO_OP` 解法、以及 Keyspace 通知对齐过期清理等真实踩坑点。分布式计数器部分，从 `INCR` 的原子性本质讲起，对比了错误写法丢计数的根源，给出了秒杀库存扣减、计数窗口过期的标准范式，并延伸到 Hash 多维计数、HyperLogLog 统计 UV、Bitmap 签到等数据结构选型，最后用 Lua 令牌桶解决了限流的原子补充难题，延伸到基于号段模式的分布式 ID 生成。

几个核心结论请务必记住：第一，任何“先读后写并依赖读结果判断”的逻辑，在并发下必须用单条命令或 Lua 脚本保证原子，绝不能用 `GET`+`SET` 拼，这是分布式计数的第一铁律；第二，Redis 里的计数/状态一定要有初始化预热和持久化兜底，别假设它永远不丢，要把 Redis 当“高速闸门”而非“唯一账本”；第三，号段模式是缓解 Redis 单点热点的最佳实践，别让你的 ID 生成器成为全局瓶颈；第四，限流算法没有银弹，固定窗口、滑动窗口、漏桶、令牌桶各有所长，按精度与突发需求选型，必要时双层防护。

最后给你一份可落地的选型决策清单，下次遇到类似需求直接对照：

一、登录态共享：要能随时吊销、感知在线 → Redis 会话共享；纯无状态、短期凭证 → JWT；超大流量且能接受偶发不一致 → 会话粘滞；强一致 + 高可用 → Redis 共享（首选）。

二、计数场景：单一数值高频自增 → String + INCR；多维度分组计数 → Hash + HINCRBY；去重基数统计（UV）→ HyperLogLog；每日签到/在线标记 → Bitmap；强精确且需持久 → 数据库 + Redis 前置闸门。

三、限流选型：粗粒度保护 → 固定窗口；API 平滑限流 → 滑动窗口；网关入口容忍突发 → 令牌桶；下游匀速消费 → 漏桶；重要接口 → 双层（网关令牌桶 + 业务固定窗口）。

四、分布式 ID：已有 Redis 且要强递增 → INCR 或号段模式；完全去中心超高并发 → 雪花算法；号段太小会成热点、太大会浪费，按峰值 QPS 估算步长。

### 系列进度 10/16

### 下章预告

第 11 章 消息队列实现与应用：我们将基于 Redis 的 List、Stream 结构实现轻量级消息队列，剖析发布订阅、延迟队列、可靠投递与消费幂等，并对比专业 MQ（如 Kafka、RabbitMQ）的取舍边界，帮你看清“什么时候该用 Redis 做队列，什么时候该上专业 MQ”。

### 互动引导

你在实际项目中是用 Redis 做会话共享，还是直接上 JWT 无状态方案？分布式 ID 你更倾向 Redis 号段、雪花算法还是数据库号段？限流你用的是固定窗口还是令牌桶？欢迎在评论区聊聊你踩过的坑和选型理由。如果觉得这篇对你有帮助，点个赞或收藏，我们第 11 章见。也欢迎把你在生产里遇到的 Redis 奇葩问题丢出来，我们一起排雷。

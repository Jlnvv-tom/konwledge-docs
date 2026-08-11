---
sidebar_position: 8
---

# 第8章 Redis事务与锁机制

在分布式系统开发中，事务和锁是两个绕不开的话题。Redis作为高性能内存数据库，提供了自己的事务机制，同时也成为分布式锁实现的首选方案。本章将深入探讨Redis事务的特性、局限性，以及基于Redis实现分布式锁的各种方案，结合实战踩坑经验，帮助你在实际项目中做出正确的技术选型。

## 8.1 Redis事务的特性：ACID原则的部分实现

提到事务，我们首先想到的是关系型数据库中ACID原则：原子性（Atomicity）、一致性（Consistency）、隔离性（Isolation）和持久性（Durability）。那么Redis的事务是否满足这些特性呢？答案是比较复杂的。

### 原子性：部分满足

Redis事务通过MULTI、EXEC、DISCARD命令组合实现。MULTI开启事务，EXEC提交事务，DISCARD取消事务。在EXEC执行之前，所有命令只是进入队列，不会真正执行。EXEC执行时，队列中的命令会被原子性地顺序执行。

但这里有一个关键问题：Redis事务不支持回滚。如果队列中的某条命令执行失败，其他命令仍然会继续执行。这与传统关系型数据库的事务行为有很大差异。

```bash
# Redis事务示例
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key1 "value1"
QUEUED
127.0.0.1:6379> SET key2 "value2"
QUEUED
127.0.0.1:6379> EXEC
1) OK
2) OK
```

上述例子中，两条SET命令在EXEC调用时原子性地执行。但如果我们故意加入一条错误的命令：

```bash
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key1 "value1"
QUEUED
127.0.0.1:6379> LPUSH key1 "list_item"  # key1已经是string类型
QUEUED
127.0.0.1:6379> SET key2 "value2"
QUEUED
127.0.0.1:6379> EXEC
1) OK
2) (error) WRONGTYPE Operation against a key
3) OK
```

可以看到，LPUSH命令执行失败，但SET key2仍然执行成功了。这就是Redis事务在原子性上的局限性。

### 一致性：基本满足

Redis事务执行前后，数据库状态保持一致性。这里的一致性指的是数据库约束不会被破坏。Redis作为键值存储，本身没有复杂的约束检查，因此一致性相对容易保证。

如果事务执行过程中Redis进程崩溃，根据持久化配置的不同，可能会有不同的恢复结果。如果是AOF持久化且appendfsync设置为always，已执行的事务命令会被恢复；如果是RDB快照，可能会丢失部分数据。

### 隔离性：缺乏保障

Redis事务没有隔离级别的概念。在事务执行期间，其他客户端可以修改数据，Redis不会对这些操作进行隔离。这可能导致事务执行结果与预期不符。

```java
// 客户端A开启事务
jedis.watch("counter");
jedis.multi();
jedis.incr("counter");

// 客户端B在A提交前修改了counter
jedisB.set("counter", "100");

// 客户端A提交事务
jedis.exec();  // 返回null，事务被取消
```

上面的例子展示了WATCH命令的作用：当被监视的键在事务执行前被修改，事务会被取消。这是Redis提供的乐观锁机制。

### 持久性：取决于配置

Redis的持久性取决于持久化配置。如果配置了AOF且appendfsync为always，事务执行结果会立即写入磁盘，具备一定的持久性。但如果Redis进程崩溃且没有持久化配置，事务结果将丢失。

### 小结

Redis事务对ACID的支持可以概括为：

- 原子性：部分满足（不支持回滚）
- 一致性：基本满足
- 隔离性：缺乏保障（需配合WATCH）
- 持久性：取决于配置

在实际应用中，如果需要完整的事务支持，应该考虑关系型数据库或其他支持ACID的存储系统。Redis事务更适合用于批量命令执行、减少网络往返等场景。

## 8.2 事务核心命令：multi、exec、discard与watch监听

Redis事务涉及四个核心命令：MULTI、EXEC、DISCARD和WATCH。本节将详细介绍每个命令的用法和注意事项。

### MULTI：开启事务

MULTI命令用于标记事务块的开始。执行MULTI后，后续的命令不会立即执行，而是进入队列。队列中的命令返回QUEUED表示入队成功。

```bash
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> INCR counter
QUEUED
127.0.0.1:6379> INCR counter
QUEUED
127.0.0.1:6379> GET counter
QUEUED
```

注意，MULTI命令可以嵌套调用吗？答案是不可以。在事务中再次调用MULTI会返回错误：

```bash
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> MULTI
(error) ERR MULTI calls can not be nested
```

### EXEC：提交事务

EXEC命令执行事务队列中的所有命令。命令会按照入队顺序依次执行，返回结果是一个数组，包含每条命令的执行结果。

```bash
127.0.0.1:6379> EXEC
1) (integer) 1
2) (integer) 2
3) "2"
```

如果事务被WATCH监视的键已被修改，EXEC将返回null（nil），表示事务被取消。

### DISCARD：取消事务

DISCARD命令用于取消事务，清空命令队列，同时释放WATCH监视的键。

```bash
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key "value"
QUEUED
127.0.0.1:6379> DISCARD
OK
127.0.0.1:6379> GET key
(nil)
```

DISCARD的使用场景主要是在事务执行前发现条件不满足，主动取消事务。

### WATCH：乐观锁机制

WATCH命令是Redis事务中最具特色的功能，它实现了乐观锁机制。被WATCH的键如果在EXEC执行前被修改，事务将被取消。

```java
// Java实现WATCH事务
public boolean transferMoney(Jedis jedis, String from, String to, int amount) {
    jedis.watch(from);
    String fromValue = jedis.get(from);
    int fromBalance = Integer.parseInt(fromValue);
    
    if (fromBalance < amount) {
        jedis.unwatch();
        return false;
    }
    
    Transaction tx = jedis.multi();
    tx.decrBy(from, amount);
    tx.incrBy(to, amount);
    List<Object> result = tx.exec();
    
    return result != null;
}
```

WATCH的使用有几个关键点需要注意：

第一，WATCH必须在MULTI之前调用。在事务内部调用WATCH会返回错误。

第二，WATCH监视的是键值变化，而不是键的操作。只要键的值发生变化，事务就会被取消。

第三，WATCH的有效期直到EXEC或DISCARD执行。无论事务是否成功，WATCH都会被清除。

第四，WATCH可以监视多个键。任意一个被监视的键发生变化，事务都会被取消。

```bash
127.0.0.1:6379> WATCH key1 key2 key3
OK
```

### WATCH实战踩坑

在实际项目中使用WATCH时，有几个常见的坑需要避免。

**坑点一：WATCH后不检查EXEC返回值**

```java
// 错误示例：没有检查exec返回值
jedis.watch("stock");
Transaction tx = jedis.multi();
tx.decr("stock");
tx.exec();  // 可能返回null，但没有检查
```

正确的做法是检查EXEC返回值，如果返回null，说明事务被取消，需要进行重试或错误处理。

```java
// 正确示例：检查返回值并重试
public boolean decrStock(Jedis jedis, String key, int retryCount) {
    for (int i = 0; i < retryCount; i++) {
        jedis.watch(key);
        int stock = Integer.parseInt(jedis.get(key));
        if (stock <= 0) {
            jedis.unwatch();
            return false;
        }
        Transaction tx = jedis.multi();
        tx.decr(key);
        if (tx.exec() != null) {
            return true;
        }
    }
    return false;
}
```

**坑点二：WATCH监视的键被其他命令修改**

WATCH不仅监视SET命令，任何修改键值的命令都会触发监视取消，包括EXPIRE、DEL、RENAME等。

```bash
# 客户端A
127.0.0.1:6379> WATCH mykey
OK
127.0.0.1:6379> MULTI
OK

# 客户端B修改了mykey的过期时间
127.0.0.1:6379> EXPIRE mykey 100

# 客户端A提交事务
127.0.0.1:6379> EXEC
(nil)  # 事务被取消
```

**坑点三：WATCH与Lua脚本混用**

WATCH只能在普通命令中使用，Lua脚本内部无法使用WATCH。如果需要复杂的原子操作，应该直接使用Lua脚本。

## 8.3 Redis事务的局限性：不支持回滚与并发问题

了解了Redis事务的基本用法后，我们需要深入分析其局限性，以便在实际项目中做出正确的技术决策。

### 不支持回滚的原因

Redis官方文档明确说明了不支持回滚的原因，总结起来有两点：

第一，Redis命令错误分为两类。语法错误在命令入队时就能检测到，这类错误会导致整个事务被拒绝执行。类型错误（如对string类型执行LPUSH）只能在执行时检测到，这类错误只会导致当前命令失败，不会影响其他命令。

```bash
# 语法错误：整个事务被拒绝
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key "value"
QUEUED
127.0.0.1:6379> INVALID_COMMAND  # 语法错误
(error) ERR unknown command
127.0.0.1:6379> EXEC
(error) EXECABORT Transaction discarded

# 类型错误：只有错误命令失败
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key "value"
QUEUED
127.0.0.1:6379> LPUSH key "item"  # 类型错误
QUEUED
127.0.0.1:6379> SET key2 "value2"
QUEUED
127.0.0.1:6379> EXEC
1) OK
2) (error) WRONGTYPE Operation
3) OK
```

第二，不支持回滚是出于性能考虑。Redis的设计目标是高性能，实现回滚需要维护事务日志和undo操作，会显著增加复杂度和性能开销。

### 并发问题分析

Redis事务在并发场景下存在多种问题，需要特别注意。

**问题一：事务执行期间的并发修改**

事务EXEC执行期间，虽然命令是原子执行的，但这个原子性只是针对单个Redis实例。如果事务执行时间较长，其他客户端可能在这个过程中修改数据。

```java
// 事务执行时间较长
jedis.multi();
for (int i = 0; i < 1000; i++) {
    tx.set("key" + i, "value" + i);
}
tx.exec();  // 执行期间可能被其他客户端修改
```

**问题二：WATCH重试风暴**

在高并发场景下，多个客户端同时WATCH同一个键，可能导致大量事务失败重试。

```java
// 高并发下的WATCH竞争
public void concurrentUpdate(Jedis jedis, String key) {
    int maxRetry = 10;
    for (int i = 0; i < maxRetry; i++) {
        jedis.watch(key);
        String value = jedis.get(key);
        Transaction tx = jedis.multi();
        tx.set(key, value + "_updated");
        if (tx.exec() != null) {
            return;  // 成功
        }
        // 失败重试
    }
    throw new RuntimeException("重试次数耗尽");
}
```

在高并发场景下，上述代码可能导致大量请求重试，性能急剧下降。

### 与关系型数据库事务的对比

| 特性 | Redis事务 | MySQL事务 |
|------|-----------|-----------|
| 原子性 | 部分（无回滚） | 完整 |
| 一致性 | 基本 | 完整 |
| 隔离级别 | 无 | 四种隔离级别 |
| 持久性 | 依赖配置 | 完整 |
| 回滚支持 | 不支持 | 支持 |
| 死锁检测 | 不适用 | 支持 |
| 锁粒度 | 无锁 | 行锁/表锁 |

从对比可以看出，Redis事务与传统数据库事务有本质区别。在选择使用Redis事务时，需要明确以下几点：

第一，是否需要回滚能力？如果需要，Redis事务不适合。

第二，是否有复杂的并发控制需求？如果有，考虑使用分布式锁。

第三，是否需要跨多个键的原子操作？如果需要，考虑使用Lua脚本。

### Lua脚本作为事务的替代方案

当Redis事务无法满足需求时，Lua脚本是一个强大的替代方案。Lua脚本在Redis中是原子执行的，执行期间不会被打断。

```java
// 使用Lua脚本实现原子性操作
String luaScript = 
    "local current = redis.call('GET', KEYS[1]) " +
    "if tonumber(current) >= tonumber(ARGV[1]) then " +
    "    redis.call('DECRBY', KEYS[1], ARGV[1]) " +
    "    return 1 " +
    "else " +
    "    return 0 " +
    "end";

jedis.eval(luaScript, 1, "stock", "10");
```

Lua脚本的优势：

第一，真正的原子执行，不需要担心并发问题。

第二，可以包含复杂的业务逻辑，不仅仅是简单的命令组合。

第三，减少网络往返，所有逻辑在服务端一次执行完成。

Lua脚本的劣势：

第一，脚本执行期间会阻塞Redis，不适合执行时间过长的脚本。

第二，脚本调试困难，错误排查成本高。

第三，脚本管理复杂，需要在应用代码中维护脚本字符串。

## 8.4 分布式锁的核心需求：跨服务资源竞争控制

随着微服务架构的普及，分布式锁成为解决跨服务资源竞争的重要手段。本节将分析分布式锁的核心需求，为后续实现方案奠定基础。

### 为什么需要分布式锁

在单机环境下，我们可以使用操作系统提供的锁机制（如互斥锁、读写锁）来保护共享资源。但在分布式环境下，多个服务实例可能同时访问共享资源，单机锁无法跨进程协调。

典型的分布式锁应用场景包括：

**场景一：定时任务去重**

多个服务实例部署同一定时任务，需要确保同一时刻只有一个实例执行任务。

```java
@Scheduled(cron = "0 0 1 * * ?")  // 每天凌晨1点执行
public void dailyCleanup() {
    if (!tryLock("daily_cleanup", 3600)) {
        log.info("其他实例正在执行，跳过");
        return;
    }
    try {
        // 执行清理逻辑
    } finally {
        unlock("daily_cleanup");
    }
}
```

**场景二：库存扣减**

电商场景下，多个用户同时购买同一商品，需要确保库存扣减的正确性。

```java
public boolean deductStock(String productId, int quantity) {
    String lockKey = "stock_lock:" + productId;
    if (!tryLock(lockKey, 10)) {
        return false;
    }
    try {
        int stock = getStock(productId);
        if (stock >= quantity) {
            updateStock(productId, stock - quantity);
            return true;
        }
        return false;
    } finally {
        unlock(lockKey);
    }
}
```

**场景三：配置热加载**

多个服务实例需要从配置中心加载配置，需要确保只有一个实例执行加载操作。

### 分布式锁的核心需求

一个完善的分布式锁实现需要满足以下核心需求：

**需求一：互斥性**

同一时刻，只有一个客户端能够持有锁。这是分布式锁最基本的要求。

**需求二：防死锁**

锁必须设置过期时间，防止客户端崩溃后锁无法释放。同时，锁的释放必须是安全的，不能误删其他客户端的锁。

**需求三：可重入**

同一个客户端可以多次获取同一把锁，不会造成死锁。

**需求四：高可用**

锁服务本身需要具备高可用性，单点故障不应该影响锁的获取和释放。

**需求五：高性能**

锁的获取和释放应该是高效的操作，不应该成为系统瓶颈。

### 分布式锁的常见实现方案

目前主流的分布式锁实现方案有三种：

**方案一：基于数据库实现**

利用数据库的唯一约束实现锁，优点是实现简单，缺点是性能较差，不适合高并发场景。

```sql
-- 创建锁表
CREATE TABLE distributed_lock (
    lock_key VARCHAR(64) PRIMARY KEY,
    holder_id VARCHAR(64),
    expire_time TIMESTAMP
);

-- 获取锁
INSERT INTO distributed_lock VALUES ('my_lock', 'client1', NOW() + INTERVAL 10 SECOND);
```

**方案二：基于ZooKeeper实现**

利用ZooKeeper的临时顺序节点实现锁，优点是可靠性高，缺点是性能不如Redis，适合对可靠性要求极高的场景。

**方案三：基于Redis实现**

利用Redis的原子操作实现锁，优点是性能高、实现简单，缺点是需要处理各种边界情况。

本章重点讨论基于Redis的分布式锁实现，这也是业界最常用的方案。

## 8.5 基于Redis的分布式锁实现：setnx命令与过期时间设置

基于Redis实现分布式锁有多种方案，从简单到复杂逐步演进。本节将从最基础的SETNX实现开始，逐步优化到生产级别的方案。

### 方案一：基础SETNX实现

最早的分布式锁实现使用SETNX（Set if Not eXists）命令，如果key不存在则设置成功，返回1；如果key已存在则设置失败，返回0。

```java
// 基础SETNX实现
public boolean tryLock(Jedis jedis, String lockKey) {
    return jedis.setnx(lockKey, "locked") == 1;
}

public void unlock(Jedis jedis, String lockKey) {
    jedis.del(lockKey);
}
```

这个方案存在严重问题：如果客户端在获取锁后崩溃，锁永远不会被释放，导致死锁。

### 方案二：SETNX + EXPIRE

为了解决死锁问题，我们需要为锁设置过期时间。早期的做法是SETNX和EXPIRE分开执行。

```java
// SETNX + EXPIRE 实现
public boolean tryLock(Jedis jedis, String lockKey, int expireSeconds) {
    if (jedis.setnx(lockKey, "locked") == 1) {
        jedis.expire(lockKey, expireSeconds);
        return true;
    }
    return false;
}
```

这个方案仍然有问题：SETNX和EXPIRE是两条命令，不是原子操作。如果SETNX成功后，客户端在EXPIRE执行前崩溃，锁仍然无法过期释放。

### 方案三：SET命令的扩展参数

Redis 2.6.12版本后，SET命令支持NX和EX参数，可以原子性地设置值和过期时间。这是目前推荐的基础实现方案。

```java
// 推荐的基础实现
public boolean tryLock(Jedis jedis, String lockKey, int expireSeconds) {
    String result = jedis.set(lockKey, "locked", "NX", "EX", expireSeconds);
    return "OK".equals(result);
}

public void unlock(Jedis jedis, String lockKey) {
    jedis.del(lockKey);
}
```

SET命令的参数说明：

- NX：等同于SETNX，只在key不存在时设置
- EX：设置过期时间，单位为秒
- PX：设置过期时间，单位为毫秒

### 方案四：安全的锁释放

上述方案仍然存在一个严重问题：锁的释放是不安全的。客户端A获取锁后，可能因为执行时间过长，锁已过期被自动释放。此时客户端B获取了锁。客户端A执行完毕后，调用unlock会删除客户端B的锁。

```java
// 不安全的释放示例
// 客户端A获取锁，设置10秒过期
jedis.set(lockKey, "locked", "NX", "EX", 10);

// A执行业务逻辑超过10秒，锁自动过期
// B获取了同一把锁
jedis.set(lockKey, "locked", "NX", "EX", 10);

// A执行完毕，释放锁（实际上释放的是B的锁）
jedis.del(lockKey);  // 错误！
```

解决方案是为每个锁设置唯一标识，释放时检查是否是自己持有的锁。

```java
// 安全的锁释放
public boolean tryLock(Jedis jedis, String lockKey, String clientId, int expireSeconds) {
    String result = jedis.set(lockKey, clientId, "NX", "EX", expireSeconds);
    return "OK".equals(result);
}

public void unlock(Jedis jedis, String lockKey, String clientId) {
    String value = jedis.get(lockKey);
    if (clientId.equals(value)) {
        jedis.del(lockKey);
    }
}
```

但这个方案还有问题：GET和DEL是两条命令，不是原子操作。在GET之后、DEL之前，锁可能已经被其他客户端获取。

### 方案五：Lua脚本保证原子性

使用Lua脚本实现原子性的锁释放：

```java
// 使用Lua脚本释放锁
public boolean unlock(Jedis jedis, String lockKey, String clientId) {
    String luaScript = 
        "if redis.call('get', KEYS[1]) == ARGV[1] then " +
        "    return redis.call('del', KEYS[1]) " +
        "else " +
        "    return 0 " +
        "end";
    Object result = jedis.eval(luaScript, 1, lockKey, clientId);
    return Long.valueOf(1).equals(result);
}
```

这个方案解决了锁释放的原子性问题，是生产环境的基础方案。

### 完整的生产级别实现

综合以上分析，一个生产级别的Redis分布式锁实现如下：

```java
public class RedisDistributedLock {
    private Jedis jedis;
    private String lockKey;
    private String clientId;
    private int expireSeconds;
    private volatile boolean locked = false;

    public RedisDistributedLock(Jedis jedis, String lockKey, int expireSeconds) {
        this.jedis = jedis;
        this.lockKey = lockKey;
        this.expireSeconds = expireSeconds;
        this.clientId = UUID.randomUUID().toString();
    }

    public boolean tryLock() {
        String result = jedis.set(lockKey, clientId, "NX", "EX", expireSeconds);
        if ("OK".equals(result)) {
            locked = true;
            return true;
        }
        return false;
    }

    public boolean tryLock(long waitMillis, long retryIntervalMillis) {
        long endTime = System.currentTimeMillis() + waitMillis;
        while (System.currentTimeMillis() < endTime) {
            if (tryLock()) {
                return true;
            }
            try {
                Thread.sleep(retryIntervalMillis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return false;
            }
        }
        return false;
    }

    public boolean unlock() {
        if (!locked) {
            return false;
        }
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else " +
            "    return 0 " +
            "end";
        Object result = jedis.eval(luaScript, 1, lockKey, clientId);
        locked = false;
        return Long.valueOf(1).equals(result);
    }
}
```

### 使用示例

```java
public void processWithLock() {
    RedisDistributedLock lock = new RedisDistributedLock(jedis, "my_lock", 30);
    try {
        if (lock.tryLock(5000, 100)) {
            // 执行业务逻辑
            doSomething();
        } else {
            log.warn("获取锁失败");
        }
    } finally {
        lock.unlock();
    }
}
```

## 8.6 分布式锁的优化：避免死锁与红锁方案

上一节实现了一个基本的分布式锁，但在实际生产环境中，还需要考虑更多的问题，如锁续期、集群环境下的可靠性等。本节将深入讨论这些优化方案。

### 锁续期机制

当业务执行时间超过锁的过期时间时，锁会自动释放，可能导致并发问题。解决方案是实现锁续期机制（Watchdog），在锁即将过期时自动延长过期时间。

```java
// 锁续期机制实现
public class RedisLockWithWatchdog {
    private Jedis jedis;
    private String lockKey;
    private String clientId;
    private int expireSeconds;
    private ScheduledExecutorService watchdog;
    private ScheduledFuture<?> watchdogTask;

    public boolean tryLock() {
        String result = jedis.set(lockKey, clientId, "NX", "EX", expireSeconds);
        if ("OK".equals(result)) {
            startWatchdog();
            return true;
        }
        return false;
    }

    private void startWatchdog() {
        watchdog = Executors.newSingleThreadScheduledExecutor();
        watchdogTask = watchdog.scheduleAtFixedRate(() -> {
            jedis.expire(lockKey, expireSeconds);
        }, expireSeconds / 3, expireSeconds / 3, TimeUnit.SECONDS);
    }

    public boolean unlock() {
        if (watchdogTask != null) {
            watchdogTask.cancel(true);
            watchdog.shutdown();
        }
        // Lua脚本释放锁
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else return 0 end";
        Object result = jedis.eval(luaScript, 1, lockKey, clientId);
        return Long.valueOf(1).equals(result);
    }
}
```

Watchdog机制的关键点：

第一，续期间隔应该小于过期时间，通常设置为过期时间的1/3。

第二，续期操作应该检查锁是否仍由当前客户端持有。

第三，业务执行完毕后必须停止Watchdog线程。

### 可重入锁实现

在复杂的业务场景中，同一个线程可能需要多次获取同一把锁。这需要实现可重入锁机制。

```java
// 可重入锁实现
public class ReentrantRedisLock {
    private Jedis jedis;
    private String lockKey;
    private String clientId;
    private int expireSeconds;
    private ThreadLocal<Integer> holdCount = ThreadLocal.withInitial(() -> 0);

    public boolean tryLock() {
        if (holdCount.get() > 0) {
            holdCount.set(holdCount.get() + 1);
            return true;
        }
        String result = jedis.set(lockKey, clientId, "NX", "EX", expireSeconds);
        if ("OK".equals(result)) {
            holdCount.set(1);
            return true;
        }
        return false;
    }

    public boolean unlock() {
        if (holdCount.get() == 0) {
            return false;
        }
        holdCount.set(holdCount.get() - 1);
        if (holdCount.get() > 0) {
            return true;  // 还持有锁，不释放
        }
        // 真正释放锁
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else return 0 end";
        Object result = jedis.eval(luaScript, 1, lockKey, clientId);
        return Long.valueOf(1).equals(result);
    }
}
```

可重入锁的实现要点：

第一，使用ThreadLocal记录每个线程的锁持有次数。

第二，锁释放时，只有在持有次数为0时才真正释放Redis中的锁。

第三，需要考虑锁过期与重入的冲突问题。

### 主从架构下的问题

Redis主从架构下，分布式锁存在可靠性问题。当客户端A在主节点获取锁后，锁还未同步到从节点，主节点就宕机了。从节点晋升为主节点后，客户端B又可以获取同一把锁，导致锁的互斥性被破坏。

### Redlock算法

为了解决主从架构下的问题，Redis作者提出了Redlock算法。Redlock的核心思想是在多个独立的Redis节点上获取锁，只有大多数节点都获取成功，才算真正获取到锁。

```java
// Redlock简化实现
public class Redlock {
    private List<Jedis> jedisNodes;
    private String lockKey;
    private String clientId;
    private int expireSeconds;
    private int quorum;

    public Redlock(List<Jedis> jedisNodes, String lockKey, int expireSeconds) {
        this.jedisNodes = jedisNodes;
        this.lockKey = lockKey;
        this.expireSeconds = expireSeconds;
        this.clientId = UUID.randomUUID().toString();
        this.quorum = jedisNodes.size() / 2 + 1;
    }

    public boolean tryLock() {
        int successCount = 0;
        long startTime = System.currentTimeMillis();
        
        for (Jedis jedis : jedisNodes) {
            try {
                String result = jedis.set(lockKey, clientId, "NX", "EX", expireSeconds);
                if ("OK".equals(result)) {
                    successCount++;
                }
            } catch (Exception e) {
                log.warn("获取锁失败: {}", e.getMessage());
            }
        }
        
        // 检查是否达到多数派
        long elapsedTime = System.currentTimeMillis() - startTime;
        if (successCount >= quorum && elapsedTime < expireSeconds * 1000) {
            return true;
        }
        
        // 失败，释放所有已获取的锁
        unlock();
        return false;
    }

    public void unlock() {
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else return 0 end";
        for (Jedis jedis : jedisNodes) {
            try {
                jedis.eval(luaScript, 1, lockKey, clientId);
            } catch (Exception e) {
                log.warn("释放锁失败: {}", e.getMessage());
            }
        }
    }
}
```

Redlock算法的关键点：

第一，使用多个独立的Redis节点，避免单点故障。

第二，需要在大多数节点上获取锁，确保互斥性。

第三，获取锁的总时间不能超过锁的有效期。

第四，释放锁时需要在所有节点上释放。

### Redlock的争议

Redlock算法在学术界和工程界都引发了一些争议。主要争议点包括：

第一，时钟依赖问题。Redlock依赖系统时钟判断锁的有效性，如果发生时钟跳跃，可能导致锁失效。

第二，网络分区问题。在极端的网络分区情况下，Redlock可能无法保证正确性。

第三，复杂性。Redlock的实现和维护成本较高，对于大多数业务场景，简单的主从架构锁已经足够。

### 实践建议

根据实际业务需求选择合适的分布式锁方案：

对于大多数业务场景，使用SET NX EX + Lua脚本释放的基本方案已经足够。如果业务执行时间不确定，实现Watchdog续期机制。如果对可靠性要求极高，考虑使用Redlock或ZooKeeper方案。如果需要复杂的锁功能（如可重入、读写锁），推荐使用Redisson框架。

```java
// 使用Redisson框架
RedissonClient redisson = Redisson.create(config);
RLock lock = redisson.getLock("myLock");
try {
    lock.lock(30, TimeUnit.SECONDS);
    // 执行业务逻辑
} finally {
    lock.unlock();
}
```

Redisson框架已经实现了Watchdog续期、可重入锁、红锁等功能，是生产环境的推荐选择。

### 性能优化建议

在高并发场景下，分布式锁可能成为性能瓶颈。以下是一些优化建议：

第一，减小锁的粒度。将大锁拆分为多个小锁，降低竞争。

第二，优化锁的等待策略。使用指数退避避免重试风暴。

```java
// 指数退避重试
public boolean tryLockWithBackoff(int maxRetries) {
    int retryDelay = 10;  // 初始10ms
    for (int i = 0; i < maxRetries; i++) {
        if (tryLock()) {
            return true;
        }
        try {
            Thread.sleep(retryDelay);
            retryDelay = Math.min(retryDelay * 2, 1000);  // 最大1s
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
    return false;
}
```

第三，考虑无锁设计。在某些场景下，可以通过乐观锁、幂等性设计等方式避免使用分布式锁。

## 总结

本章深入探讨了Redis事务与分布式锁机制。Redis事务提供了基本的命令批量执行能力，但与传统数据库事务有本质区别，不支持回滚、缺乏隔离性保障。在需要复杂原子操作时，Lua脚本往往是更好的选择。

分布式锁是解决跨服务资源竞争的关键技术。从基础的SETNX实现到完善的SET NX EX + Lua释放方案，再到解决主从架构问题的Redlock算法，我们逐步构建了完整的知识体系。在实际项目中，应该根据业务需求选择合适的方案，对于大多数场景，SET NX EX方案已经足够；对于高可靠性需求，考虑Redlock或ZooKeeper；对于复杂功能需求，推荐使用成熟的Redisson框架。

Redis事务和分布式锁是Redis应用的重要知识点，也是面试和实际开发中的高频考点。掌握这些知识，不仅能帮助你写出更健壮的代码，也能在系统设计时做出更合理的技术选型。

系列进度 8/16

下一章预告：第9章将深入探讨缓存设计与实战，包括缓存穿透、缓存击穿、缓存雪崩的解决方案，以及缓存与数据库的一致性问题。

你在实际项目中使用过Redis事务或分布式锁吗？遇到过哪些坑？欢迎在评论区分享你的经验和问题。

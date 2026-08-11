---
sidebar_position: 4
---

# Redis核心数据结构进阶：列表、集合与有序集合

## 前言

在上一章中，我们深入探讨了Redis中最常用的字符串和哈希数据结构，理解了它们在缓存、Session存储、计数器等场景中的广泛应用。字符串提供了最基础的值存储能力，哈希则让我们能够以字段为单位操作结构化数据，二者结合已经能够解决相当一部分缓存需求。然而，Redis的能力远不止于此。作为一个功能丰富的数据结构服务器，Redis还提供了列表（List）、集合（Set）和有序集合（Sorted Set）三种强大的复合数据类型，它们在消息队列、标签系统、排行榜、实时排行等业务场景中扮演着不可替代的角色。

本文将系统性地介绍这三种数据结构的底层实现、核心命令、实战应用以及常见的性能坑点。通过丰富的代码示例和踩坑经验，帮助你在实际项目中正确、高效地使用这些数据结构。无论你是在构建一个社交媒体的消息流系统，还是在设计一个电商平台的商品标签系统，又或者需要实现一个游戏内的实时排行榜，本文都将为你提供有价值的参考。


在实际使用中，这三种数据结构往往不是孤立存在的。一个典型的社交媒体系统可能会同时使用所有三种：列表用于存储用户的时间线和消息历史，集合用于管理用户的好友关系和兴趣标签，有序集合用于排行榜和热度计算。它们相互配合，共同支撑起一个完整的数据层。理解每种数据结构的优势和局限，是做出正确技术决策的前提。

在学习过程中，建议读者跟随本文的代码示例亲手实践，只有在实际操作中才能真正体会到各种命令的特性和性能差异。

## 4.1 列表（List）：有序元素集合

### 列表的底层实现

Redis列表并非像编程语言中的数组那样通过连续内存块实现，而是一种**双向链表（doubly linked list）**结构。这意味着每个列表节点都包含指向前一个节点和后一个节点的指针，以及节点本身的数据。好消息是，Redis对链表操作进行了高度优化，在列表头部或尾部进行插入和删除操作的时间复杂度都是O(1)，这使得列表天然适合用作队列和栈。

Redis列表的底层实现经历了多次迭代。在Redis 3.2之前，列表使用简单链表（linkedlist）作为底层结构。从Redis 3.2开始，列表采用了**quicklist**作为默认实现。quicklist实际上是**ziplist（压缩列表）和linkedlist的组合体**：它将多个ziplist通过指针串联起来，既避免了纯ziplist在元素过多时导致的连锁更新问题，又避免了纯linkedlist在少量元素时内存开销过大的缺点。这种设计体现了Redis"根据数据规模选择最优实现"的设计哲学。

理解列表的底层实现对于避免性能问题至关重要。当列表中的元素较少（默认元素数不超过512个，每个元素小于64字节，具体阈值可配置）时，Redis会使用ziplist来存储，这种紧凑的内存布局效率极高。但一旦超出阈值，Redis就会将其转换为quicklist结构，这个转换过程对客户端是透明的，但如果不了解这一点，可能会在生产环境中遇到意想不到的性能抖动。

### 列表的典型应用场景

列表最经典的应用场景包括**消息队列**和**时间线（Timeline）存储**。在消息队列场景中，我们利用列表的FIFO（先进先出）特性，将消息依次push到列表尾部，消费者从列表头部依次pop消息进行处理。在时间线场景中，我们利用列表的有序特性，将用户发布的内容依次push到用户的时间线列表中，按时间顺序展示。

以一个异步邮件发送系统为例。用户的注册确认邮件无需同步发送，可以先放入消息队列，由后台Worker异步处理。这种解耦设计不仅提升了接口响应速度，还能在流量高峰时起到削峰填谷的作用。使用Redis列表作为轻量级消息队列，相比专业的RabbitMQ或Kafka，在中小规模场景下具有部署简单、维护成本低的优势。

再比如一个博客系统的最新文章列表。我们可以维护一个固定长度的文章列表，新文章发布时从头部push，旧文章超出长度限制时自动trim掉末尾：

```python
MAX_RECENT_POSTS = 100

def publish_post(post_id):
    r.lpush("recent:posts", post_id)
    r.ltrim("recent:posts", 0, MAX_RECENT_POSTS - 1)

def get_recent_posts(page=1, page_size=20):
    start = (page - 1) * page_size
    end = start + page_size - 1
    return r.lrange("recent:posts", start, end)
```

这种模式的优点是写入和读取都是O(1)操作，即使文章数量达到百万级别，最新100篇文章的获取仍然非常迅速。缺点是文章列表的淘汰是"硬删除"的，超出限制的文章ID会丢失，如果需要保留完整的文章归档，仍需要额外的存储。


掌握了列表的底层原理后，接下来让我们深入了解列表的核心命令。只有熟练运用这些命令，才能在实战中灵活应对各种场景。

## 4.2 List核心命令与队列/栈实现

### 两端操作的灵魂命令

列表的核心操作围绕"左"和"右"展开。`LPUSH`和`RPUSH`分别在列表头部和尾部插入一个或多个元素，`LPOP`和`RPOP`分别从列表头部和尾部弹出一个元素。这四个命令是列表操作的基础，几乎所有的列表应用都离不开它们。

`LRANGE`命令是列表查询的灵魂，它接受两个索引参数（start和stop），支持负数索引（-1表示最后一个元素），`0 -1`即获取所有元素。这个命令不会删除元素，只是查看，这是初学者经常混淆的地方——列表没有提供一个同时查看和删除的命令，需要先LRANGE再LPOP/RPOP。

另一个容易被忽视的命令是`LLEN`，它返回列表的长度。在需要判断队列是否有消息的场景中，直接调用`LLEN`检查长度比通过`EXISTS`判断键是否存在更加精确。同时，`LTRIM`是一个非常有用的修剪命令，它可以将列表截断到指定范围，常用于维护固定长度的历史记录或时间线——只保留最新的N条数据。

列表还有几个实用命令：`LINDEX`按索引获取元素（O(N)复杂度慎用），`LINSERT`在指定元素前后插入，`LSET`按索引设置元素值，`LREM`删除指定数量的指定元素。这些命令在特定场景下非常有用，比如`LREM`常用于实现一个忽略列表中重复元素的方法：

```python
def append_unique(list_key, item):
    """仅在元素不存在时才追加"""
    r.lrem(list_key, 0, item)  # 先删除所有匹配项
    r.rpush(list_key, item)    # 再追加到尾部
```

### 队列与栈的完整实现

```python
import redis, json
r = redis.Redis(host='localhost', port=6379, db=0)

# 消息队列（FIFO）
def enqueue(queue_name, message):
    r.rpush(queue_name, json.dumps(message))

def dequeue(queue_name, timeout=0):
    result = r.blpop(queue_name, timeout=timeout)
    if result:
        return json.loads(result[1])
    return None

# 栈（LIFO）
def push_stack(stack_key, item):
    r.lpush(stack_key, item)

def pop_stack(stack_key):
    return r.lpop(stack_key)
```

### 可靠消息队列：避免消息丢失

基础的消息队列实现中，消息被消费后即被删除。如果Worker在处理过程中崩溃，消息就永久丢失了。正确的做法是先将被消费的消息暂存到处理队列，处理完成后才删除：

```python
def reliable_receive(queue_key, processing_key, timeout=30):
    """可靠消费：从源队列转移到处理队列"""
    task = r.brpoplpush(queue_key, processing_key, timeout=timeout)
    if task:
        return json.loads(task)

def acknowledge(processing_key, task):
    """确认完成：从处理队列中删除"""
    r.lrem(processing_key, 1, json.dumps(task))

def recover_pending(queue_key, processing_key):
    """崩溃恢复：将处理中的任务重新放回源队列"""
    while True:
        task = r.rpoplpush(processing_key, queue_key)
        if not task:
            break
```

`brpoplpush`是构建可靠消费的核心命令，它将源队列的消息原子性地转移到处理队列。如果Worker崩溃未处理，重启后扫描处理队列即可补偿。这个"三段式"处理流程是生产级消息队列的标准实现模式：第一步可靠接收，消息进入处理中状态，业务逻辑处理该消息；第二步确认完成，消息从系统中消除；第三步崩溃恢复，超时的处理中消息被重新放回源队列等待重新处理。

### 列表的其他实用命令

除了核心的两端操作外，列表还有一些不那么常用但同样重要的命令。`LINDEX`按索引获取元素，时间复杂度是O(N)，在大列表上应谨慎使用，但偶尔获取中间位置的元素完全可行。`LINSERT`可以在指定元素的前后插入新元素，这在需要保持顺序的队列中非常有用——比如在队列中间插入优先级更高的任务。`LSET`按索引设置元素值，可以用于更新已存在位置的内容。`LREM`删除列表中指定数量的指定元素，count为正数时从头删除，为负数时从尾删除，为0时删除所有匹配项。`RPOPLPUSH`和`LPOPLPUSH`是另一对实用的移动命令，可以在两个列表之间原子性地移动元素。Redis 6.2引入的`LMOVE`命令则是它们的功能超集，提供了更灵活的左右方向控制。

在实际项目中，这些命令的组合可以完成很多巧妙的操作。比如实现一个任务分发系统：主队列存放待处理任务，多个Worker从主队列取任务，处理完成后将结果放入完成队列。这种模式避免了Worker之间的竞争，让任务分发更加均匀可控。再比如实现一个消息广播系统：将消息push到多个消费者的队列中，通过`RPOPLPUSH`将主队列的消息同步到每个消费者的个人队列，消费者按自己的节奏从个人队列消费，互不干扰。

### 列表操作的常见坑点

第一个高频坑点是**列表为空时的行为**。`LPOP`和`RPOP`在列表为空时返回`nil`，而不是抛出异常。很多新手在处理返回值时没有做空值判断，导致后续代码出现`AttributeError`。在异步任务处理循环中，空返回是正常状态（队列暂时为空），需要优雅处理而不是当作错误。

第二个坑点是**列表容量没有天然上限**。如果不加控制地往列表中push数据，它会无限增长，可能撑爆内存。解决方案是结合`LTRIM`命令限制列表长度。对于时间线类场景，新数据push进去后立即trim到指定大小：

```python
MAX_TIMELINE_SIZE = 1000

def append_timeline(user_key, post_id):
    """添加时间线内容，自动维护固定长度"""
    r.lpush(user_key, post_id)
    r.ltrim(user_key, 0, MAX_TIMELINE_SIZE - 1)
```

第三个坑点是**阻塞命令的超时设置**。`BRPOP`和`BLPOP`的超时参数单位是秒，设置为0表示永久阻塞直到有数据到来。在生产环境中，永久阻塞可能导致无法优雅关闭Worker进程。建议设置一个合理的超时值（如60秒），在超时后重新进入循环，这样Worker在收到终止信号时能够快速退出。

第四个坑点是**列表不支持原子性的范围操作**。如果你需要原子性地将列表前N个元素转移到另一个列表，`LRANGE + LPUSH + LTRIM`的组合不是原子的，在并发场景下可能导致数据丢失或重复。`LMOVE`（Redis 6.2+）命令提供了原子性的列表间移动，是更安全的选择。

第五个坑点是**列表的迭代遍历没有专用命令**。和集合可以用`SSCAN`不同，列表没有原生的游标遍历命令。如果列表规模很大但你只想遍历其中一部分，只能通过`LRANGE`的分片查询配合业务侧的断点记录来实现。相比之下，集合和有序集合的`SCAN`系列命令提供了更优雅的解决方案。


从列表的有序性出发，当我们需要对集合中的元素进行去重，同时保留唯一性约束时，就进入了集合的世界。集合的操作更加简洁高效，去重能力是其核心价值。

## 4.3 集合（Set）：无序唯一元素集合

### 集合的底层与特性

Redis集合底层采用**哈希表（hashtable）**实现，元素本身作为哈希表的键，哈希表键的唯一性天然保证了集合中元素的不重复性。所有基本操作（添加、删除、判断成员）的复杂度都是O(1)，这使得集合在需要频繁进行成员判断的场景中表现出色。集合的内存布局非常紧凑，当集合中存储的是整数或者短字符串时，哈希表的效率尤其高。Redis还为集合专门优化了内存分配，使用整数编码（intset）来存储纯整数元素的集合，在元素数量较少时自动采用更紧凑的编码方式，进一步节省内存。集合支持交、并、差集运算，这在标签匹配和共同好友计算等场景中非常实用。

`SMEMBERS`虽然使用方便，但当集合规模较大时（数万元素以上），它会一次性将所有成员加载到内存，可能阻塞Redis主线程影响其他命令。生产环境推荐使用`SSCAN`进行游标式遍历：

```python
def iterate_set_members(set_key, batch_size=1000):
    """使用SCAN方式遍历集合，避免阻塞"""
    cursor = 0
    while True:
        cursor, members = r.sscan(set_key, cursor=cursor, count=batch_size)
        for member in members:
            yield member
        if cursor == 0:
            break
```

集合适用的场景天然具有"无序且唯一"的特性，比如用户标签、好友列表、关键词集合、商品特征标签等。在选择使用集合还是列表时，核心判断标准是：**数据是否需要唯一？数据是否需要有序？** 两者都需要选Sorted Set，只需要唯一选Set，只需要有序选List，两者都不需要才选List。

### 集合的典型应用：标签系统与投票系统

标签系统是集合最典型的应用之一。每篇文章可以有多个标签，每个标签下包含多篇文章，使用集合可以自然地建模这种多对多关系：

```python
def tag_article(article_id, tags):
    """将文章添加到每个标签的集合中"""
    pipe = r.pipeline()
    for tag in tags:
        pipe.sadd(f"tag:{tag}", article_id)
    pipe.execute()

def get_articles_by_tag(tag):
    """获取指定标签下的所有文章"""
    return r.smembers(f"tag:{tag}")

def get_articles_by_any_tags(tags):
    """获取包含任一标签的文章（OR查询）"""
    keys = [f"tag:{tag}" for tag in tags]
    return r.sunion(*keys)

def get_articles_by_all_tags(tags):
    """获取同时拥有所有指定标签的文章（AND查询）"""
    if not tags:
        return []
    keys = [f"tag:{tag}" for tag in tags]
    return r.sinter(*keys)
```

`SINTER`的效率取决于参与运算的集合中最小的那一个。Redis会选取元素最少的集合作为基础，遍历其中的元素并在其他集合中检查存在性，时间复杂度为O(N)，其中N是最小集合的基数。在设计标签系统时，应该选择区分度最高的标签（即元素数量最少的标签）作为"主集合"放在最前面参与交集运算，以获得最优性能。

### 集合核心命令

`SADD`添加元素（已存在的被忽略），`SREM`删除元素，`SISMEMBER`判断存在（返回1或0），`SCARD`返回集合大小（O(1)，务必优先使用），`SRANDMEMBER`随机采样，`SPOP`随机弹出。批量检查可用`SMISMEMBER`（Redis 6.2+），避免多次调用`SISMEMBER`。`SINTER/SUNION/SDIFF`计算交集并集差集，对应的存储版`SINTERSTORE/SUNIONSTORE/SDIFFSTORE`将结果直接写入目标键，避免了先计算再遍历的额外开销。

在实际开发中，`SUNIONSTORE`有一个容易被忽略的细节：如果参与并集运算的键中包含非集合类型的数据（如列表或字符串），`SUNIONSTORE`会忽略这些非法键而继续处理合法的集合键，但`SUNION`本身则会因为遇到非法键而报错。在生产环境中，建议使用`TYPE`命令先检查键的类型再进行集合运算，或者使用Lua脚本包装整个运算流程以确保原子性和类型安全。

还有一个实用的技巧是使用集合来**实现布隆过滤器（Bloom Filter）的简化版本**。如果业务可以容忍一定的误判率（false positive）但不能容忍漏判（false negative），可以用多个集合模拟布隆过滤器的多位数组：每个哈希函数对应一个集合，将元素加入过滤器时计算多个哈希值并将元素加入对应的集合，查询时检查所有集合。这种方案比完整的布隆过滤器实现简单，但内存效率较低。在Redis 4.0之后，可以使用Redis官方提供的`BF.ADD`等布隆过滤器命令，但集合方案在特定场景下仍然是一个快速可用的替代。批量检查可用`SMISMEMBER`（Redis 6.2+），避免多次调用`SISMEMBER`。`SINTER/SUNION/SDIFF`计算交集并集差集，对应的存储版`SINTERSTORE/SUNIONSTORE/SDIFFSTORE`将结果直接写入目标键，避免了先计算再遍历的额外开销。

```redis
> SADD interests:alice programming music travel cooking photography
(integer) 5
> SISMEMBER interests:alice music
(integer) 1
> SCARD interests:alice
(integer) 5
> SRANDMEMBER interests:alice 2
1) "music"
2) "travel"
> SPOP interests:alice 1
1) "cooking"
```

`SMISMEMBER`是Redis 6.2引入的新命令，可以一次检查多个成员是否在集合中，返回值是一个布尔数组。这个命令在需要批量验证成员资格的场景中非常实用，比循环调用`SISMEMBER`减少了多次网络往返。

### 集合的边界场景处理

在实际业务中，集合运算还有一些值得关注的边界场景。当参与交集运算的键不存在时，`SINTER`会返回一个空集合而不是报错，这是符合预期的行为。当某个键的值不是集合而是其他数据类型时，Redis会报错。`SUNIONSTORE`等存储版命令在目标键已存在时会覆盖原内容，这可能导致意外的数据丢失，建议在业务层先检查目标键的状态，或者使用一个唯一的临时键名。

关于集合的基数，`SCARD`是O(1)操作，在只需要知道集合大小时务必优先使用，而不是先`SMEMBERS`再`len()`。这一点看似简单，但在实际项目中仍然常见新手写出`len(r.smembers(key))`这样的代码——一次性加载所有元素到内存中只是为了获取一个数字，在百万级数据时这可能造成严重的内存抖动。

集合还经常用于实现**权限控制和黑名单机制**。例如，将某个资源的所有有权限用户的ID存入集合，通过`sismember`快速判断用户是否有权访问。这种方案的查询性能是O(1)，比在数据库中查询权限表快得多。结合过期时间（`EXPIRE`），还可以实现临时封禁（拉黑）功能，将封禁结束时间设置为过期时间，到期后自动解封。

### 集合的常见坑点

第一个坑点是**集合元素只能是字符串**，不能直接存储整数、列表或字典等复合类型。如果需要存储复杂数据，必须先将数据序列化为JSON字符串或使用MessagePack等二进制序列化格式。但这样做会失去`SISMEMBER`的精确匹配能力（因为序列化后的字符串必须完全一致才能匹配），设计时需要权衡。如果业务需要存储复杂对象并在集合中进行关联查询，考虑使用哈希表作为主存储、集合作为索引的分离架构。

第二个坑点是**集合运算在大规模场景下的性能**。`SINTER`和`SUNION`等命令的时间复杂度为O(N)，其中N是参与运算集合的大小。在最坏情况下（多个百万级集合做交集），运算可能耗时数百毫秒甚至数秒，而这期间Redis是单线程阻塞的。解决方案包括：使用`SINTERSTORE`等存储版命令将结果缓存起来避免重复计算；将大集合拆分或者预先计算好常用交集结果；评估是否可以用Lua脚本将运算逻辑与其他操作组合以减少网络往返。

第三个坑点是**随机操作的不可重复性**。`SRANDMEMBER`和`SPOP`虽然都用于随机获取元素，但语义不同：`SRANDMEMBER`仅查看不删除，适合随机推荐；`SPOP`是弹出操作，元素会被永久删除，适合抽奖等无放回抽取场景。使用前务必确认业务语义，避免将`SRANDMEMBER`用于需要去重的随机抽取场景——它可能返回重复元素。


掌握了集合的基本命令后，更重要的是理解如何将集合运算应用到实际业务中。集合的交、并、差集运算看似简单，但在复杂系统中发挥着举足轻重的作用。

## 4.4 集合运算实战

### 好友关系建模

好友关系天然具有"无序且唯一"的特性，非常适合用集合来建模：

```python
def add_friend(user_id, friend_id):
    r.sadd(f"friends:{user_id}", friend_id)

def remove_friend(user_id, friend_id):
    r.srem(f"friends:{user_id}", friend_id)

def is_friend(user_id, friend_id):
    return r.sismember(f"friends:{user_id}", friend_id)

def get_mutual_friends(user1, user2):
    """获取两个用户的共同好友"""
    return r.sinter(f"friends:{user1}", f"friends:{user2}")

def get_friends_count(user_id):
    """获取好友数量"""
    return r.scard(f"friends:{user_id}")

def get_friend_recommendations(user_id):
    """好友推荐：好友的好友中排除已加好友"""
    my_key = f"friends:{user_id}"
    fof_keys = [f"friends:{fid}" for fid in r.smembers(my_key)]
    if not fof_keys:
        return []
    # 所有好友的好友（并集）
    fof = r.sunion(*fof_keys)
    # 排除自己和已加好友
    return list(r.sdiff(fof, my_key, str(user_id)))
```

`SDIFF`的语义是第一个集合中有的、其他集合中没有的元素。上述推荐逻辑是：将所有好友的好友做并集，从中剔除自己和自己已加的好友，剩余即为推荐好友。这个逻辑在社交产品中非常常见。实际生产中，为了避免好友数量过多导致`SUNION`操作耗时，通常会对一级好友数量设置上限，或者只取最近活跃的好友进行计算。

### 投票系统的去重设计

集合的去重能力在投票、答题等场景中也非常实用。比如一个用户只能投一票的活动，我们可以使用集合来记录已投票用户：

```python
def has_voted(activity_id, user_id):
    return r.sismember(f"vote:{activity_id}", user_id)

def cast_vote(activity_id, user_id):
    """返回True表示投票成功，False表示已投过"""
    return r.sadd(f"vote:{activity_id}", user_id) == 1

def get_vote_count(activity_id):
    return r.scard(f"vote:{activity_id}")
```

`sadd`的返回值正好可以用于判断投票是否成功：如果返回1表示成功添加（之前未投过），返回0表示元素已存在（已投过票）。这种利用返回值做业务判断的方式在Redis使用中非常常见。在实际投票系统中，还需要考虑投票的时效性（如限定投票时间段），这可以通过结合有序集合来实现：用集合存储已投票用户（用于去重和计数），用有序集合存储投票时间（用于判断是否在有效时间段内）。


在实际业务中，有序集合的场景往往比列表和集合更为复杂多变。排行榜需要考虑分数更新、排名查询、分页展示；延时队列需要处理时间调度和任务调度；价格排序需要处理浮点数精度和实时更新。本章将深入探讨有序集合的核心命令和实战技巧，帮助你全面掌握这一Redis中最强大的数据结构。

## 4.5 有序集合（Sorted Set）：带分数排序的高级集合

### 底层原理：跳跃表

有序集合是Redis中最强大也最复杂的数据结构。它在集合"无序且唯一"的基础上增加了**分数（score）**属性，元素按分数从小到大排序。如果多个元素具有相同的分数，则按元素的字典序进行排序。这种设计使得有序集合成为实现排行榜、延时队列、热度排行等场景的理想选择。

底层采用**跳跃表（skiplist）和哈希表**的组合：跳跃表维护有序性（实现O(log N)的范围查询），哈希表维护元素到分数的映射（实现O(1)的`ZSCORE`查询）。跳跃表是一种多层链表结构，每层节点以一定概率（通常为1/2）向上延伸形成快速通道，实现接近二分查找的效率，同时代码比红黑树简洁得多（Redis中约200行实现）。从Redis 3.2起，小数据量场景下使用更紧凑的listpack替代部分skiplist结构，Redis会根据数据规模自动选择最优底层实现。

理解跳跃表的工作原理对于理解有序集合的性能特性至关重要。在最底层是一个普通的有序链表，查找时间复杂度为O(N)。跳跃表通过在上层建立"快速通道"，使得平均查找时间降为O(log N)。这意味着即使排行榜上有百万名玩家，查询某个玩家的排名也只需要几十次比较。虽然跳跃表的最坏情况时间复杂度是O(N)（所有节点都在同一层），但这种情况在实际中几乎不会发生，因为每层节点数量的期望值呈指数衰减。

### 排行榜系统

有序集合最典型的应用是**排行榜系统**。无论是游戏中的玩家战力榜、电商平台的热销商品榜，还是内容平台的文章热度榜，有序集合都能优雅地解决这些需求。传统的数据库方案需要在每次更新时重新排序查询，而有序集合只需要一条`ZINCRBY`命令即可原子性地增加某个成员的分数，查询Top N也只需要一条`ZREVRANGE`命令。

```python
class Leaderboard:
    def __init__(self, r, board_name):
        self.key = f"lb:{board_name}"

    def increment_score(self, player_id, delta):
        return r.zincrby(self.key, delta, player_id)

    def update_score(self, player_id, score):
        return r.zadd(self.key, {player_id: score})

    def get_rank(self, player_id):
        rank = r.zrevrank(self.key, player_id)
        return rank + 1 if rank is not None else None

    def get_top(self, n=10):
        return r.zrevrange(self.key, 0, n - 1, withscores=True)

    def get_around_me(self, player_id, count=5):
        rank = r.zrevrank(self.key, player_id)
        if rank is None:
            return []
        start = max(0, rank - count // 2)
        end = rank + count // 2
        return r.zrevrange(self.key, start, end, withscores=True)

    def remove_player(self, player_id):
        return r.zrem(self.key, player_id)
```

`ZINCRBY`的原子性增量更新是排行榜系统的关键——玩家的分数变化（如游戏中击败对手获得积分、购物获得积分）可以直接原子性地加到有序集合中，无需读取、修改、写回的三步操作。`ZREVRANK`和`ZREVRANGE`的组合使用，可以获取任意玩家的排名以及周围玩家信息，这是传统数据库很难高效实现的功能。

### 分页排行榜

```python
def get_leaderboard_page(board_key, page=1, page_size=20):
    """分页获取排行榜"""
    start = (page - 1) * page_size
    end = start + page_size - 1
    members = r.zrevrange(board_key, start, end, withscores=True)
    return [
        {"rank": start + i + 1, "member": m, "score": int(s)}
        for i, (m, s) in enumerate(members)
    ]
```

### 排行榜进阶功能

在实际项目中，排行榜还有一些常见的进阶需求。**多维度排行榜**是指同一个玩家在不同维度（如战力、金币、胜率）上都有排名。实现方式是为每个维度维护一个独立的有序集合，玩家在各个维度的分数分别存储。这种方案的优点是查询简单，缺点是分数更新时需要同时更新多个集合，增加了复杂度。

**分数衰减机制**是指随着时间推移，排行榜上的分数逐渐降低，以反映玩家最近的表现。这可以通过定时任务扫描排行榜，对所有成员的分数按一定比例衰减实现。另一种更高效的方式是在计算排名时引入时间因子，将分数与时间结合为一个复合值存储：

```python
import time

def decay_score(base_score, timestamp, half_life_days=7):
    age_seconds = time.time() - timestamp
    decay_factor = 0.5 ** (age_seconds / (half_life_days * 86400))
    return base_score * decay_factor
```

**赛季重置**功能在游戏排行榜中非常常见：每个赛季结束时清空排行榜或归档历史数据，新赛季开始时重新初始化。实现方式是使用带赛季标识的键名（如`lb:season_3`），赛季结束时删除旧键或设置过期时间，新赛季自动使用新键名。这种基于键名前缀的方案比在同一有序集合中维护多赛季数据更加简洁，也避免了数据混淆。

日榜/月榜的实现利用时间前缀键名配合过期自动清理：

```python
from datetime import datetime

def get_daily_key():
    return f"lb:daily:{datetime.now().strftime('%Y-%m-%d')}"

def get_weekly_key():
    today = datetime.now().date()
    year, week, _ = today.isocalendar()
    return f"lb:weekly:{year}-W{week:02d}"

def update_daily_score(player_id, delta):
    key = get_daily_key()
    r.zincrby(key, delta, player_id)
    r.expire(key, 86400 * 8)  # 多保留几天供查询
```

排行榜中如果多个用户分数相同，`ZRANK`按分数相同的字典序排名。如果业务需要"中国式排名"（同分同名次），需要额外处理：

```python
def chinese_style_rank(r, key, member):
    """中国式排名：同分同名次"""
    score = r.zscore(key, member)
    if score is None:
        return None
    # 统计分数严格高于当前成员的成员数
    return r.zcount(key, f"({score}", "+inf") + 1
```

`ZCOUNT`使用开放区间语法`(score`表示严格大于score的计数，从而实现同分同名次的效果。

### 延时队列

有序集合的分数排序能力还能实现**延时队列**：将任务的目标执行时间戳作为分数，任务ID作为成员。分数小于等于当前时间戳的成员即为到期任务。相比使用字符串键值存储任务到期时间，延时队列方案的优势在于可以批量获取所有到期任务，而无需轮询每个任务键。

```python
import time

def delay_task(queue_key, task_id, delay_seconds):
    """将任务加入延时队列，在指定时间后可被消费"""
    r.zadd(queue_key, {task_id: time.time() + delay_seconds})

def poll_tasks(queue_key):
    """获取并移除所有已到期的任务"""
    now = time.time()
    tasks = r.zrangebyscore(queue_key, 0, now)
    if tasks:
        r.zrem(queue_key, *tasks)
        return tasks
    return []
```

`ZRANGEBYSCORE`获取所有到期任务后，`ZREM`批量删除。需要注意的是，如果消费者崩溃，部分任务可能永远不会被处理——因为它们已经被删除了。在实际生产环境中，可以使用`ZPOPMIN`替代，先弹出最小分数的任务，处理成功后再确认。也可以在取出任务后不立即删除，而是等待处理完成后再删除，通过定期清理超时任务来兜底。

### 有序集合的边界与高级用法

在按分数范围查询时，`ZRANGEBYSCORE`支持丰富的区间语法：普通数值、开放区间`(num`和封闭区间`[num`、负数无穷`-inf`、正数无穷`+inf`都可以使用。合理利用这些语法可以实现精准的范围查询，比如查询分数在80到100之间（含）的所有成员：

```python
def get_score_range(board_key, min_score, max_score):
    return r.zrangebyscore(board_key, f"[{min_score}", f"[{max_score}", withscores=True)
```

`ZLEXCOUNT`可以按字典序统计区间内元素数量，配合`ZRANGEBYLEX`可以实现按名称前缀范围查询，这在需要按字母顺序排序的业务场景中非常实用。

有序集合还支持**权重更新**功能，`ZADD`接受多个member-score对作为参数，可以一次性更新多个成员的分数。在实现排行榜赛季重置时，可以先删除旧的有序集合（或者让其自动过期），再批量添加新赛季的所有玩家初始数据，整个过程是原子的。`ZSCORE`可以精确获取任意成员的当前分数，`ZINCRBY`则是原子性增量，两者的组合可以满足几乎所有排行榜的分数管理需求。

```python
def get_score_range(board_key, min_score, max_score):
    return r.zrangebyscore(board_key, f"[{min_score}", f"[{max_score}", withscores=True)
```

`ZLEXCOUNT`可以按字典序统计区间内元素数量，配合`ZRANGEBYLEX`可以实现按名称前缀范围查询，这在需要按字母顺序排序的业务场景中非常实用。

### 有序集合的常见坑点

第一个坑点是**浮点数分数精度**。Redis分数是IEEE 754 64位浮点数，存在精度损失。当需要精确排序（如价格排序）时，建议将分数转换为整数（如将价格乘以100转为"分"），避免浮点数比较中出现的排序错乱问题。同时，当使用`ZINCRBY`累加浮点数时，多次累加可能导致微小的精度误差累积。

第二个坑点是**排名操作的O(log N)开销**。在超大规模排行榜中频繁查询排名可能影响性能。虽然O(log N)看起来不错，但当有序集合规模达到千万级别时，每次排名查询仍然需要数十次比较操作。如果排行榜需要展示大量用户的排名，可以考虑在更新分数时将排名信息同步写入用户相关的哈希表中，以空间换时间。

第三个坑点是**成员名应设计为短字符串**（如用户ID、订单ID）。长字符串作为member时，每次比较和哈希运算都消耗更多CPU。完整业务数据存储在外部哈希表，通过ID进行关联查询。

第四个坑点是**排行榜数据的冷热分离**。活跃玩家的分数需要频繁更新，而历史排行榜数据几乎不访问。可以按时间周期（如每月）将历史排行榜归档到归档键中，当前排行榜只保留当期的活跃玩家数据，减少不必要的内存占用和扫描开销。

第五个坑点是**ZADD的返回值语义在不同版本间的变化**。早期Redis版本中，`ZADD`的返回值表示新增元素的数量（不包含更新）。从Redis 3.0.2开始，返回值变为受影响的元素总数（包括新增和更新）。在使用旧版本或在跨版本环境中部署时，需要注意这个差异，以免业务逻辑基于错误的返回值做出判断。

## 4.6 三种数据结构对比与选型指南

经过前几节的详细学习，你现在应该对列表、集合和有序集合有了深入的理解。理解了这三种数据结构后，面对实际需求时的选型决策就清晰了。核心判断维度只有两个：**唯一性需求**和**有序性需求**。

在明确了每种数据结构的特性和适用场景之后，面对具体需求时的选型就变得有章可循了。以下是从实战经验中提炼的选型决策树，帮助你在面对新需求时快速做出判断。

### 选型决策树

**是否需要唯一性？不需要**时选择List，因为列表允许重复。**需要唯一**时继续判断：**是否需要排序？** 不需要排序选Set，需要排序选Sorted Set。简单记法是：唯一+无序用Set，唯一+有序用Sorted Set，无唯一+有序用List，无唯一+无序也用List。

为了方便在实际开发中快速查阅，这里整理了一份简明的选型对照表，涵盖三种数据结构最典型的应用场景。帮助你快速定位合适的实现方案。

### 场景化选型对照表

List适合：消息队列、时间线、最近访问记录、栈结构、优先级队列、批量任务分发、聊天记录存储。Set适合：标签系统、好友列表、共同好友、去重、投票统计、特征集合、黑名单/白名单、权限管理。Sorted Set适合：排行榜、延时队列、权重限流、价格排序、按热度排序、滑动窗口统计、优先级任务调度。

### 场景深度解析：最近访问记录

一个经典的选型场景是"用户最近访问记录"。如果需要展示访问历史（按时间有序，允许重复），用List+LTRIM实现固定长度的历史记录。如果需要去重但不需要严格按时间排序（不重复，无序），用Set。如果需要去重且按时间排序（不重复，有序），用Sorted Set将时间戳作为分数。三种方案各有优劣，取决于具体业务需求。

### 场景深度解析：热榜统计

另一个典型场景是实时统计并展示Top N。假设需要统计每篇文章的阅读量并展示热榜。方案一是将阅读量作为String键值存储，计数高效但查询Top N需要扫描所有键值再排序。方案二是将阅读量作为有序集合的分数，更新一条命令，查询一条命令，不需要额外的排序操作。劣势是内存开销略大于纯计数方案，但换取了查询性能的极大提升。在实际选型时，需要综合考虑查询模式、更新频率和内存成本。

### 场景深度解析：滑动窗口限流

滑动窗口限流是另一个典型场景。比如限制每个用户每分钟最多发起100次API调用。使用有序集合可以将每次调用的时间戳作为分数，用户ID作为成员，通过`ZCOUNT`统计时间窗口内的调用次数，`ZREMRANGEBYSCORE`清理过期记录：

```python
import time

def rate_limit(user_id, max_requests=100, window_seconds=60):
    key = f"ratelimit:{user_id}"
    now = time.time()
    window_start = now - window_seconds
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window_seconds + 1)
    results = pipe.execute()
    request_count = results[1]
    return request_count < max_requests
```

这种方案相比使用列表实现同样的功能，查询时间窗口内请求数的复杂度从O(N)降为O(log N)，且占用内存更小（只存储有效请求的时间戳）。

### 性能特征对比

从时间复杂度来看，三种数据结构的查询性能差异显著。在列表中，按索引获取元素为O(1)，但按值查找为O(N)，两端操作均为O(1)。在集合中，添加、删除和成员判断都是O(1)，但遍历所有成员为O(N)。在有序集合中，添加为O(log N)，按分数排名查询为O(log N)，按分数范围查询为O(log N + M)，其中M是返回结果的数量。

从内存占用来看，在数据量较小时（元素数量少且每个元素较小），ziplist和listpack等压缩结构具有显著的内存优势。在数据量较大时，普通链表和哈希表的开销变得线性可预测。三种数据结构的内存效率排序为（在小数据量时）：ziplist > listpack > linkedlist；在中等数据量时：quicklist表现最优；在大量数据时，skiplist（跳表）的时间空间综合效率最优。

### 组合使用的艺术

在实际项目中，这三种数据结构很少孤立使用，更多的是组合发挥各自优势。例如一个社交媒体的帖子系统：帖子的正文和元数据可以用哈希存储（便于按字段更新），帖子的ID列表用列表存储（便于按时间顺序展示），每个帖子的点赞用户用集合存储（快速判断某用户是否已点赞、统计点赞总数），最热门的帖子排行榜用有序集合存储（按点赞数排序）。这种组合使用充分发挥了每种数据结构的长处。

再举一个电商平台的商品推荐系统为例。商品的分类标签用集合存储（便于多标签筛选），用户的浏览历史用有序集合存储（以时间戳为分数，去重且按时间排序），商品的销量排行用有序集合存储（按销量分数排序）。当需要为用户推荐"最近浏览过的分类中的热销商品"时，可以取用户浏览历史的分类标签，取这些分类的热销商品集合，再通过交集运算得到候选商品列表，最后按销量排序展示。这个流程中，列表用于历史记录，集合用于标签系统，有序集合用于排行榜，三种数据结构各司其职。

**是否需要唯一性？不需要**时选择List，因为列表允许重复。**需要唯一**时继续判断：**是否需要排序？** 不需要排序选Set，需要排序选Sorted Set。简单记法是：唯一+无序用Set，唯一+有序用Sorted Set，无唯一+有序用List，无唯一+无序也用List。

具体到业务场景：List适合消息队列、时间线、最近访问记录、栈结构、优先级队列。Set适合标签系统、好友列表、共同好友、去重、投票统计、特征集合。Sorted Set适合排行榜、延时队列、权重限流、价格排序、按热度排序。

一个经典的选型场景是"用户最近访问记录"。如果需要展示访问历史（按时间有序，允许重复），用List+LTRIM实现固定长度的历史记录。如果需要去重但不需要严格按时间排序（不重复，无序），用Set。如果需要去重且按时间排序（不重复，有序），用Sorted Set将时间戳作为分数。三种方案各有优劣，取决于具体业务需求。

在实际项目中使用这些数据结构时，还有一些通用的最佳实践值得遵循。第一是**键命名规范**：使用有意义的键名前缀，如`queue:email`、`tag:python`、`lb:daily:2024-01-01`，便于管理和监控。第二是**过期时间管理**：对于临时数据（如日榜、限时排行榜、临时缓存），务必设置合理的过期时间，避免数据堆积导致内存泄漏。第三是**Pipeline批量操作**：当需要执行多个相关命令时，使用Pipeline将命令批量发送到Redis再一次性接收结果，可以大幅减少网络往返次数。第四是**监控与容量规划**：关注Redis的内存使用量、命令耗时和CPU使用率，当发现某个键的规模增长异常时及时介入。

掌握了列表、集合和有序集合之后，你会发现Redis的世界远比表面看起来丰富多彩。这些基础但强大的数据结构组合起来，几乎可以应对大多数中等规模系统的数据存储和查询需求。在后续章节中，我们将继续探索Redis提供的更多高级功能，包括BitMap、HyperLogLog、Geospatial等，它们将进一步扩展你对Redis能力边界的认知。

## 总结

本文系统性地介绍了Redis中三种核心复合数据类型——列表（List）、集合（Set）和有序集合（Sorted Set）。这三种数据结构在日常开发中使用频率极高，是深入掌握Redis的必经之路。理解它们的工作原理不仅能帮助我们写出更高效的代码，更能让我们在面对复杂业务需求时做出更合理的技术选型决策。


列表基于双向链表实现，天然适合作为FIFO队列和LIFO栈使用，核心操作集中在左右两端。quicklist作为列表的默认底层实现，结合了压缩列表的内存效率和链表的插入删除优势。实战中的关键注意点包括：消息丢失的可靠消费机制（brpoplpush三段式处理）、列表容量的主动限制（LTRIM）、阻塞命令的超时设置（避免永久阻塞）、原子性范围操作缺失（需要LMOVE替代）以及列表无原生遍历命令（需用分片LRANGE替代SCAN）。列表在构建轻量级消息队列、时间线存储和历史记录等场景中仍然是首选方案。

集合基于哈希表实现，提供了高效的去重能力和O(1)的成员判断，交、并、差集运算是标签系统和好友关系建模的利器。需要警惕`SMEMBERS`在大规模集合上的性能风险，集合运算在超大规模数据上的CPU消耗，`SSCAN`游标遍历的安全替代方案，以及随机操作（SRANDMEMBER/SPOP）的语义区别。在设计基于集合的系统时，应当充分考虑数据规模和查询模式，选择合适的集合大小和索引策略。

有序集合融合了集合的唯一性约束和分数排序能力，是排行榜系统的首选数据结构。跳跃表和哈希表的组合实现了O(log N)的排名查询和O(1)的分数查询。排行榜的完整实现涵盖了分数原子更新、排名查询、分页、日榜/月榜、延时队列等常见需求。浮点数精度、排名操作开销、成员名设计和冷热数据分离是四个需要特别注意的坑点。

从性能角度看，三种数据结构各有优劣：列表在两端操作上具有无可比拟的O(1)优势，但在中间位置的查询和遍历上效率较低；集合在成员判断上去重场景下最优，但在大规模集合运算时需要评估CPU消耗；有序集合在需要排序的场景中综合性能最优，但内存占用相对较高。在实际项目中，灵活组合使用它们，往往能构建出优雅而高效的解决方案。


**系列进度 4/16**

**下一章预告：第5章 BitMap、HyperLogLog与Geospatial**

在掌握了列表、集合和有序集合之后，我们将进入Redis中三款"特种武器"的学习。BitMap通过位操作为大规模二元状态统计提供了极致的空间效率——一个比特位就能记录一个用户的每日签到状态，1GB内存可以记录80亿个用户的独立状态；HyperLogLog以仅需12KB的内存实现接近99%的基数估算精度，可以轻松统计数十亿级别的UV而不需要占用大量内存；而Geospatial索引则让我们能够高效处理"附近的人"、"门店距离排序"等地理位置相关的查询需求，它们都是在大数据量场景下Redis提供的独特能力，敬请期待。


你使用过Redis的列表、集合或有序集合解决过哪些实际问题？有没有踩过什么有趣的"坑"？欢迎在评论区分享你的实战经验。如果本文对你有帮助，也请转发给需要的朋友，我们下章见！

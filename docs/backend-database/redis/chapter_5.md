---
sidebar_position: 5
---

# 第5章 Redis高级数据结构：BitMap、HyperLogLog与Geospatial

在前面几章中，我们深入了解了Redis的五大基础数据结构：String、List、Hash、Set和Sorted Set。这些数据结构已经能够满足绝大多数业务场景的需求。但是，当面对海量数据统计、位级操作、地理位置计算等特殊场景时，Redis还提供了三种高级数据结构：BitMap、HyperLogLog和Geospatial。

这三种数据结构各有其独特的设计理念和适用场景。BitMap以极低的存储成本实现位级操作，适合用户签到、在线状态等场景；HyperLogLog以惊人的空间效率实现基数统计，是UV统计的利器；Geospatial则专门处理地理位置数据，支持距离计算和范围查询。本章将深入探讨这三种高级数据结构的原理、命令实战和最佳实践。

## 5.1 位图（BitMap）：位级操作的高效存储方案

### 什么是BitMap

BitMap并不是一种独立的数据结构，而是基于String类型实现的位级操作接口。在Redis中，String类型的值最大可以存储512MB的数据，这意味着一个BitMap最多可以包含2^32个位（约42.9亿个位）。每个位只能是0或1，这种二进制的特性使得BitMap在某些场景下具有极高的存储效率。

考虑一个用户签到的场景。如果我们用传统的Set结构存储签到用户ID，每个用户ID假设占用8字节，那么1亿用户的签到数据就需要约800MB的存储空间。而使用BitMap，只需要用用户ID作为偏移量，将对应位置设为1即可，1亿用户只需要约12.5MB的存储空间，节省了98%以上的存储。

### BitMap的存储原理

BitMap的底层存储仍然是Redis的String类型。当执行`setbit`命令时，Redis会根据偏移量定位到具体的字节和位，然后进行修改。偏移量offset表示第几个位，从0开始计数。

```bash
# 设置第0位为1
setbit user:signin:20240101 0 1

# 设置第7位为1
setbit user:signin:20240101 7 1

# 设置第8位为1（跨字节）
setbit user:signin:20240101 8 1
```

在内存中，一个字节由8个位组成。当我们设置第0位时，修改的是第一个字节的最低位；设置第7位时，修改的是第一个字节的最高位；设置第8位时，则需要修改第二个字节的最低位。这种设计使得BitMap可以非常紧凑地存储大量布尔值数据。

### BitMap的适用场景

BitMap特别适合以下几类场景：

第一类是布尔值集合。当需要存储大量布尔状态时，比如用户是否在线、消息是否已读、功能开关等，BitMap可以用极低的空间成本实现。

第二类是用户签到统计。以用户ID作为偏移量，签到则设置对应位为1，可以高效地统计签到天数、连续签到、首次签到等。

第三类是去重判断。当数据范围已知且有限时，可以用BitMap快速判断某个值是否已存在。

需要注意的是，BitMap的性能与偏移量的大小有关。偏移量越大，需要的存储空间越大，操作的时间复杂度也会受到影响。因此，BitMap最适合用于数据范围可控、ID连续或接近连续的场景。

### 一个踩坑经历

曾经在一次项目中，我们需要统计用户的活跃状态。当时设计时，直接使用用户ID作为BitMap的偏移量。上线后一切正常，直到有一天，系统突然报错"OutOfMemory"。排查后发现，原来是有测试账号使用了非常大的ID（超过10亿），导致Redis不得不分配超过100MB的内存来存储这个BitMap。

```java
// 错误示例：直接使用用户ID作为偏移量
long userId = 1234567890L; // 超大的用户ID
jedis.setbit("user:active", userId, true);
// 这将导致分配约150MB内存

// 正确做法：使用映射后的ID
long mappedId = userId % 1_000_000_000; // 映射到合理范围
jedis.setbit("user:active", mappedId, true);
```

这个教训告诉我们，使用BitMap时一定要注意偏移量的范围控制。如果用户ID不连续或范围过大，应该考虑使用ID映射或选择其他数据结构。

## 5.2 BitMap核心命令：setbit、getbit、bitcount等与用户签到实现

### setbit与getbit：位的设置与查询

setbit命令用于设置BitMap中指定位的值，返回该位的旧值。getbit命令用于获取指定位的值。

```bash
# 语法：setbit key offset value
# value只能是0或1

# 用户1001在2024年1月1日签到
setbit signin:20240101 1001 1
# 返回0，表示之前未签到

# 重复签到
setbit signin:20240101 1001 1
# 返回1，表示之前已签到

# 查询签到状态
getbit signin:20240101 1001
# 返回1，已签到

# 查询未签到的用户
getbit signin:20240101 1002
# 返回0，未签到
```

在实际开发中，需要注意offset的范围。虽然Redis允许offset达到2^32-1，但设置大偏移量会导致内存分配。如果BitMap原本不存在或长度不足以覆盖offset，Redis会自动扩展并填充中间的位为0。

### bitcount：统计位为1的数量

bitcount命令用于统计BitMap中值为1的位的数量，可以指定字节范围。

```bash
# 统计签到人数
bitcount signin:20240101
# 返回签到总人数

# 统计指定字节范围内1的数量
# 从第0字节到第100字节
bitcount signin:20240101 0 100
```

bitcount在用户签到统计中非常实用。比如统计某一天的签到人数，或者统计某个用户范围内的活跃人数。

### bitop：位运算操作

bitop命令支持对多个BitMap进行位运算，支持AND、OR、XOR、NOT操作，结果存储在目标key中。

```bash
# 语法：bitop operation destkey key [key ...]

# 统计连续两天都签到的用户
bitop and signin:both signin:20240101 signin:20240102
bitcount signin:both

# 统计两天内签到过的用户（去重）
bitop or signin:either signin:20240101 signin:20240102
bitcount signin:either

# 统计只有一天签到的用户（异或）
bitop xor signin:diff signin:20240101 signin:20240102
bitcount signin:diff
```

bitop命令的时间复杂度是O(N)，N是参与运算的BitMap中最长的长度。在生产环境中，如果BitMap很大，这个操作可能会阻塞Redis，建议在从节点执行或使用游标分批处理。

### bitpos：查找位的第一个出现位置

bitpos命令用于查找BitMap中第一个值为0或1的位的位置。

```bash
# 查找第一个签到用户的ID
bitpos signin:20240101 1

# 查找第一个未签到用户的ID
bitpos signin:20240101 0

# 在指定字节范围内查找
bitpos signin:20240101 1 0 100
```

### 用户签到系统的完整实现

下面是一个完整的用户签到系统的实现方案，包括签到、查询、统计等功能。

```java
public class SignInService {
    private Jedis jedis;
    
    /**
     * 用户签到
     * @param userId 用户ID
     * @param date 日期，格式yyyyMMdd
     */
    public boolean signIn(long userId, String date) {
        String key = "signin:" + date;
        // 返回旧值，false表示首次签到
        return jedis.setbit(key, userId, true);
    }
    
    /**
     * 检查用户是否已签到
     */
    public boolean hasSigned(long userId, String date) {
        String key = "signin:" + date;
        return jedis.getbit(key, userId);
    }
    
    /**
     * 统计某天的签到人数
     */
    public long countSignIn(String date) {
        String key = "signin:" + date;
        return jedis.bitcount(key);
    }
    
    /**
     * 统计用户当月签到天数
     */
    public int countMonthlySignIn(long userId, String yearMonth) {
        int count = 0;
        // 遍历当月每一天
        for (int day = 1; day <= 31; day++) {
            String date = yearMonth + String.format("%02d", day);
            if (hasSigned(userId, date)) {
                count++;
            }
        }
        return count;
    }
}
```

### 连续签到统计的实现

连续签到是一个常见的运营需求，下面是统计连续签到天数的实现。

```java
/**
 * 统计用户连续签到天数（从今天往前数）
 */
public int countContinuousSignIn(long userId, int maxDays) {
    int count = 0;
    LocalDate today = LocalDate.now();
    
    for (int i = 0; i < maxDays; i++) {
        LocalDate date = today.minusDays(i);
        String dateStr = date.format(DateTimeFormatter.BASIC_ISO_DATE);
        
        if (hasSigned(userId, dateStr)) {
            count++;
        } else {
            // 遇到未签到的日期，连续签到中断
            break;
        }
    }
    return count;
}

/**
 * 检查用户是否可以补签
 */
public boolean canRetroactive(long userId, String date) {
    LocalDate signDate = LocalDate.parse(date, DateTimeFormatter.BASIC_ISO_DATE);
    LocalDate yesterday = LocalDate.now().minusDays(1);
    
    // 只能补签昨天
    if (!signDate.equals(yesterday)) {
        return false;
    }
    // 昨天未签到
    return !hasSigned(userId, date);
}
```

### 月度签到数据合并

在月度统计场景中，可能需要统计当月所有签到过的用户数量，这时候可以使用bitop or操作合并所有日期的BitMap。

```java
/**
 * 统计当月签到过的用户数（去重）
 */
public long countMonthlyUniqueSignIn(String yearMonth) {
    List<String> keys = new ArrayList<>();
    for (int day = 1; day <= 31; day++) {
        String date = yearMonth + String.format("%02d", day);
        keys.add("signin:" + date);
    }
    
    String destKey = "signin:monthly:" + yearMonth;
    // 合并所有日期的签到数据
    jedis.bitop(BitOP.OR, destKey, keys.toArray(new String[0]));
    long count = jedis.bitcount(destKey);
    // 删除临时key
    jedis.del(destKey);
    return count;
}
```

### BitMap使用的注意事项

第一，偏移量控制。始终确保offset在合理范围内，避免因超大offset导致内存浪费。对于不连续或范围过大的ID，建议进行映射处理。

第二，内存预分配。如果知道需要存储的数据量，可以提前设置最大偏移量，避免运行时频繁扩容。

```bash
# 预分配100万用户的BitMap
setbit signin:20240101 1000000 0
```

第三，批量操作优化。对于批量设置或查询，可以使用pipeline减少网络往返。

```java
// 使用pipeline批量签到
Pipeline pipeline = jedis.pipelined();
for (Long userId : userIds) {
    pipeline.setbit("signin:20240101", userId, true);
}
pipeline.sync();
```

第四，大BitMap的清理。BitMap的内存释放只能通过删除整个key，无法单独释放某个范围。如果需要定期清理，建议使用带有过期时间的key，或者使用单独的key存储不同时间段的数据。

## 5.3 基数统计（HyperLogLog）：海量数据去重的轻量级方案

### 什么是基数统计

基数（Cardinality）是指一个集合中不同元素的数量。比如集合{1, 2, 3, 2, 1}的基数是3，因为有3个不同的元素。基数统计就是要统计一个集合中有多少个不重复的元素。

在互联网应用中，基数统计最常见的场景就是UV（Unique Visitor）统计。比如统计网站每天的独立访客数、统计某个页面的独立浏览数、统计某个活动的参与人数等。这些场景的共同特点是：数据量巨大、需要去重、对精确度要求不是特别高。

### 传统方案的困境

传统的UV统计方案主要有两种：Set去重和BitMap。

Set去重是将所有元素存入Set集合，然后通过scard命令获取基数。这种方式的精度是100%准确的，但存储空间与元素数量成正比。如果统计一天的UV是1亿，每个元素假设占用10字节，就需要约1GB的存储空间。

BitMap去重是将元素映射为BitMap中的位，适用于元素值范围已知且连续的场景。但如果元素是随机的字符串或ID范围过大，BitMap就不适用了。

HyperLogLog（简称HLL）提供了一种全新的思路：以极小的存储空间（每个key只需要12KB），实现约0.81%的标准误差。这意味着统计1亿UV也只需要12KB内存，代价是结果是一个近似值，但误差在可接受范围内。

### HyperLogLog的原理简介

HyperLogLog是一种概率数据结构，基于伯努利试验和调和平均数的原理实现。其核心思想是：通过统计元素哈希值中前导零的最大长度，来估算集合的基数。

当元素被添加到HLL时，Redis会计算元素的哈希值，然后观察哈希值的二进制表示中从最低位开始连续0的数量。连续0越多，说明这个元素的"贡献"越大。通过多个分桶的统计结果，最终计算出估算的基数。

具体的数学推导比较复杂，感兴趣的读者可以参考原始论文。对于实际使用来说，只需要记住：HLL的标准误差约为0.81%，存储成本固定为12KB。

### HyperLogLog的适用场景

HyperLogLog特别适合以下场景：

第一类是大规模UV统计。当需要统计数百万甚至上亿级别的独立访客数时，HLL的低存储成本优势非常明显。

第二类是实时统计。HLL的添加操作时间复杂度是O(1)，可以实时更新统计数据。

第三类是基数合并。多个HLL可以合并为一个新的HLL，适合多天、多地区的UV合并统计。

需要注意的是，HLL不适合以下场景：

第一，需要精确计数的场景。如果业务要求100%准确，应该使用Set或其他精确数据结构。

第二，元素数量较少的场景。当元素数量很少时，HLL的误差可能相对较大。

第三，需要获取具体元素的场景。HLL只能统计基数，不能获取具体的元素值。

## 5.4 HyperLogLog核心命令：pfadd、pfcount等与UV统计应用

### pfadd：添加元素

pfadd命令用于向HyperLogLog中添加元素。如果HyperLogLog的基数估计值发生变化（即添加了新元素），返回1；否则返回0。

```bash
# 语法：pfadd key element [element ...]

# 创建一个UV统计
pfadd page:home:uv user1
# 返回1，添加成功

pfadd page:home:uv user1
# 返回0，元素已存在

# 批量添加
pfadd page:home:uv user2 user3 user4
# 返回1，至少有一个新元素
```

pfadd支持一次添加多个元素，这比多次单独添加更高效。

### pfcount：获取基数估计值

pfcount命令用于获取HyperLogLog的基数估计值。如果key不存在，返回0。

```bash
# 获取UV数
pfcount page:home:uv
# 返回3

# 统计多个key的总UV（自动合并）
pfcount page:home:uv page:about:uv
```

需要注意的是，pfcount对于多个key的统计是通过临时合并实现的，不会修改原始数据。

### pfmerge：合并多个HyperLogLog

pfmerge命令用于将多个HyperLogLog合并为一个新的HyperLogLog。

```bash
# 语法：pfmerge destkey sourcekey [sourcekey ...]

# 合并两天的UV
pfadd uv:20240101 user1 user2 user3
pfadd uv:20240102 user2 user3 user4

# 合并到新的key
pfmerge uv:202401 uv:20240101 uv:20240102

# 查看合并后的UV
pfcount uv:202401
# 返回4（user1、user2、user3、user4）
```

pfmerge可以用于统计多天、多地区的总UV，而不会产生重复计数。

### UV统计系统的完整实现

下面是一个完整的UV统计系统的实现，包括日UV、周UV、月UV的统计。

```java
public class UVService {
    private Jedis jedis;
    
    /**
     * 记录页面访问
     */
    public void recordVisit(String pageId, String userId) {
        String today = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);
        String key = "uv:" + pageId + ":" + today;
        jedis.pfadd(key, userId);
    }
    
    /**
     * 获取今日UV
     */
    public long getTodayUV(String pageId) {
        String today = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);
        String key = "uv:" + pageId + ":" + today;
        return jedis.pfcount(key);
    }
    
    /**
     * 获取最近7天UV（去重）
     */
    public long getWeeklyUV(String pageId) {
        List<String> keys = new ArrayList<>();
        LocalDate today = LocalDate.now();
        
        for (int i = 0; i < 7; i++) {
            String date = today.minusDays(i).format(DateTimeFormatter.BASIC_ISO_DATE);
            keys.add("uv:" + pageId + ":" + date);
        }
        
        String destKey = "uv:" + pageId + ":weekly";
        jedis.pfmerge(destKey, keys.toArray(new String[0]));
        return jedis.pfcount(destKey);
    }
    
    /**
     * 获取当月UV（去重）
     */
    public long getMonthlyUV(String pageId) {
        List<String> keys = new ArrayList<>();
        String yearMonth = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMM"));
        
        for (int day = 1; day <= 31; day++) {
            String date = yearMonth + String.format("%02d", day);
            keys.add("uv:" + pageId + ":" + date);
        }
        
        String destKey = "uv:" + pageId + ":monthly";
        jedis.pfmerge(destKey, keys.toArray(new String[0]));
        return jedis.pfcount(destKey);
    }
}
```

### 多维度UV统计

在实际业务中，往往需要按照多个维度统计UV，比如按地区、按渠道、按页面等。下面是多维度UV统计的实现方案。

```java
/**
 * 多维度UV统计
 */
public void recordMultiDimensionUV(String pageId, String userId, 
                                     String region, String channel) {
    String today = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);
    
    // 总UV
    jedis.pfadd("uv:" + pageId + ":" + today, userId);
    
    // 按地区统计
    jedis.pfadd("uv:" + pageId + ":" + region + ":" + today, userId);
    
    // 按渠道统计
    jedis.pfadd("uv:" + pageId + ":" + channel + ":" + today, userId);
    
    // 按地区+渠道统计
    jedis.pfadd("uv:" + pageId + ":" + region + ":" + channel + ":" + today, userId);
}

/**
 * 获取地区UV
 */
public long getRegionUV(String pageId, String region, String date) {
    String key = "uv:" + pageId + ":" + region + ":" + date;
    return jedis.pfcount(key);
}
```

### HyperLogLog的误差验证

为了验证HyperLogLog的实际误差，我们可以做一个简单的测试。

```java
/**
 * 误差测试
 */
public void testError() {
    String key = "hll:test";
    Set<String> realSet = new HashSet<>();
    
    Random random = new Random();
    for (int i = 0; i < 1000000; i++) {
        String userId = "user" + random.nextInt(2000000);
        realSet.add(userId);
        jedis.pfadd(key, userId);
    }
    
    long realCount = realSet.size();
    long hllCount = jedis.pfcount(key);
    double error = Math.abs(realCount - hllCount) * 100.0 / realCount;
    
    System.out.println("真实UV: " + realCount);
    System.out.println("HLL UV: " + hllCount);
    System.out.println("误差: " + String.format("%.2f%%", error));
}
```

测试结果显示，对于百万级别的数据，HyperLogLog的误差通常在1%以内，完全满足UV统计的业务需求。

### HyperLogLog使用的注意事项

第一，精度选择。Redis的HyperLogLog使用16384个桶，标准误差约为0.81%。如果需要更高精度，可以考虑使用Bloom Filter或精确统计方案。

第二，存储优化。虽然每个HLL只占用12KB，但如果key数量很大（比如为每个页面、每天都创建一个HLL），总存储量也不容忽视。建议设置过期时间或定期清理历史数据。

```java
// 设置过期时间，自动清理30天前的数据
jedis.expire("uv:" + pageId + ":" + date, 30 * 24 * 3600);
```

第三，pfmerge性能。pfmerge的时间复杂度是O(N)，N是源key的数量。如果合并大量key，可能会阻塞Redis。建议分批合并或使用游标。

第四，结果缓存。频繁调用pfcount和pfmerge会影响性能，可以考虑将结果缓存起来。

```java
// 使用缓存减少计算
public long getCachedWeeklyUV(String pageId) {
    String cacheKey = "uv:" + pageId + ":weekly:cached";
    String cached = jedis.get(cacheKey);
    
    if (cached != null) {
        return Long.parseLong(cached);
    }
    
    long count = getWeeklyUV(pageId);
    // 缓存1小时
    jedis.setex(cacheKey, 3600, String.valueOf(count));
    return count;
}
```

## 5.5 地理空间（Geospatial）：地理位置存储与距离计算

### 什么是Geospatial

Geospatial是Redis 3.2版本引入的特性，专门用于存储地理位置信息并进行空间计算。它底层基于Sorted Set实现，将经纬度编码为一个分数（score），从而利用Sorted Set的有序特性实现高效的地理位置查询。

Geospatial的应用场景非常广泛，包括：附近的人/店铺查询、打车时的车辆匹配、外卖配送范围计算、地理位置围栏等。

### Geospatial的存储原理

Geospatial使用GeoHash算法将经纬度转换为一个52位的整数，作为Sorted Set的score存储。GeoHash是一种将二维的经纬度编码为一维字符串的方法，其核心思想是将地球表面不断划分为更小的区域，每个区域对应一个唯一的编码。

GeoHash的一个重要特性是：地理位置越接近，编码的前缀越相似。这使得我们可以通过前缀匹配快速查找附近的点。不过，GeoHash也有边界问题：两个地理上接近的点，如果位于不同的GeoHash区域，它们的编码可能完全不同。Redis通过额外的处理解决了这个问题。

### Geospatial的适用场景

Geospatial适合需要存储地理位置并进行空间查询的场景：

第一类是附近的人/店铺。给定一个坐标，查找一定范围内的其他点。

第二类是距离计算。计算两点之间的直线距离。

第三类是地理位置分组。将地理位置转换为GeoHash编码进行分组统计。

需要注意的是，Geospatial计算的是球面直线距离（大圆距离），不是实际的行驶距离。如果需要精确的行驶距离或路径规划，应该使用专业的地图服务API。

## 5.6 Geospatial核心命令：geoadd、geodist、georadius等与附近的人实现

### geoadd：添加地理位置

geoadd命令用于添加地理位置到指定的key中。

```bash
# 语法：geoadd key longitude latitude member [longitude latitude member ...]
# 经度范围：-180到180
# 纬度范围：-85.05112878到85.05112878

# 添加店铺位置
geoadd shops 116.397128 39.916527 "故宫"
geoadd shops 116.403963 39.915119 "天安门" 116.366136 39.957298 "鼓楼"

# 添加用户位置
geoadd users 116.397128 39.916527 "user1"
```

geoadd支持一次添加多个位置，建议批量添加以减少网络开销。

### geopos：获取地理位置

geopos命令用于获取指定成员的经纬度。

```bash
# 获取单个位置
geopos shops "故宫"
# 返回：116.39712899923324585 39.91652703885660689

# 获取多个位置
geopos shops "故宫" "天安门" "鼓楼"
```

返回的经纬度可能与我们存储的有微小差异，这是由于GeoHash编码精度导致的，误差通常在1米以内，可以忽略。

### geodist：计算两点距离

geodist命令用于计算两个地理位置之间的距离。

```bash
# 语法：geodist key member1 member2 [unit]
# unit可选：m（米，默认）、km（千米）、mi（英里）、ft（英尺）

# 计算故宫到天安门的距离
geodist shops "故宫" "天安门"
# 返回约917米

geodist shops "故宫" "天安门" km
# 返回约0.917千米

# 计算到不存在的成员
geodist shops "故宫" "不存在的店"
# 返回nil
```

geodist计算的是球面直线距离，实际距离可能因道路情况有所不同。

### georadius：以给定坐标为中心查询

georadius命令用于查询以给定经纬度为中心，指定半径内的所有成员。

```bash
# 语法：georadius key longitude latitude radius unit [options]
# options包括：
#   WITHDIST：返回距离
#   WITHCOORD：返回坐标
#   WITHHASH：返回GeoHash值
#   COUNT n：限制返回数量
#   ASC|DESC：按距离排序
#   STORE key：存储结果到新的key

# 查找故宫1公里内的店铺
georadius shops 116.397128 39.916527 1 km

# 返回距离和坐标
georadius shops 116.397128 39.916527 1 km WITHDIST WITHCOORD

# 限制返回数量并排序
georadius shops 116.397128 39.916527 10 km COUNT 5 ASC
```

georadius是Geospatial最常用的命令，适合实现"附近的人"、"附近的店铺"等功能。

### georadiusbymember：以成员为中心查询

georadiusbymember与georadius类似，只是中心点由经纬度换成了已存在的成员。

```bash
# 语法：georadiusbymember key member radius unit [options]

# 查找故宫1公里内的其他店铺
georadiusbymember shops "故宫" 1 km

# 查找附近的用户，排除自己
georadiusbymember users "user1" 1 km
```

georadiusbymember在已知某个成员，需要查找其附近的其他成员时非常方便。

### geohash：获取GeoHash编码

geohash命令用于获取成员的GeoHash编码字符串。

```bash
geohash shops "故宫" "天安门"
# 返回：wx4g0b2vex wx4g0c6vme
```

GeoHash编码可以用于地理位置分组、前端地图显示等场景。

### "附近的人"功能实现

下面是一个完整的"附近的人"功能实现，包括位置更新、附近查询、距离计算等。

```java
public class NearbyService {
    private Jedis jedis;
    private static final double SEARCH_RADIUS = 5; // 5公里
    private static final String USER_LOCATION_KEY = "user:location";
    
    /**
     * 更新用户位置
     */
    public void updateUserLocation(String userId, double longitude, double latitude) {
        jedis.geoadd(USER_LOCATION_KEY, longitude, latitude, userId);
    }
    
    /**
     * 查找附近的用户
     */
    public List<NearbyUser> findNearbyUsers(String userId, double radius) {
        List<NearbyUser> result = new ArrayList<>();
        
        // 以当前用户为中心查询
        List<GeoRadiusResponse> responses = jedis.georadiusbymember(
            USER_LOCATION_KEY, 
            userId, 
            radius, 
            GeoUnit.KM,
            new GeoRadiusParam().withDist().withCoord().sortAscending()
        );
        
        for (GeoRadiusResponse response : responses) {
            String memberId = response.getMemberByString();
            // 排除自己
            if (!memberId.equals(userId)) {
                NearbyUser user = new NearbyUser();
                user.setUserId(memberId);
                user.setDistance(response.getDistance());
                user.setLongitude(response.getCoordinate().getLongitude());
                user.setLatitude(response.getCoordinate().getLatitude());
                result.add(user);
            }
        }
        return result;
    }
    
    /**
     * 计算与目标用户的距离
     */
    public double getDistanceToUser(String userId, String targetUserId) {
        Double distance = jedis.geodist(USER_LOCATION_KEY, userId, targetUserId, GeoUnit.KM);
        return distance != null ? distance : -1;
    }
    
    /**
     * 获取用户当前位置
     */
    public GeoCoordinate getUserLocation(String userId) {
        List<GeoCoordinate> coords = jedis.geopos(USER_LOCATION_KEY, userId);
        return coords.isEmpty() ? null : coords.get(0);
    }
}

class NearbyUser {
    private String userId;
    private double distance;
    private double longitude;
    private double latitude;
    // getter/setter
}
```

### 附近的店铺功能实现

对于"附近的店铺"功能，除了位置查询，还需要考虑店铺的分类、评分等因素。

```java
public class NearbyShopService {
    private Jedis jedis;
    
    /**
     * 添加店铺位置
     */
    public void addShop(String shopId, String category, 
                        double longitude, double latitude) {
        // 存储店铺位置
        jedis.geoadd("shops:location", longitude, latitude, shopId);
        // 存储店铺分类
        jedis.hset("shops:category", shopId, category);
    }
    
    /**
     * 查找附近的店铺（按分类过滤）
     */
    public List<ShopInfo> findNearbyShops(double longitude, double latitude, 
                                           double radius, String category) {
        List<ShopInfo> result = new ArrayList<>();
        
        List<GeoRadiusResponse> responses = jedis.georadius(
            "shops:location",
            longitude, latitude,
            radius, GeoUnit.KM,
            new GeoRadiusParam().withDist().withCoord().sortAscending()
        );
        
        for (GeoRadiusResponse response : responses) {
            String shopId = response.getMemberByString();
            
            // 分类过滤
            if (category != null) {
                String shopCategory = jedis.hget("shops:category", shopId);
                if (!category.equals(shopCategory)) {
                    continue;
                }
            }
            
            ShopInfo shop = new ShopInfo();
            shop.setShopId(shopId);
            shop.setDistance(response.getDistance());
            result.add(shop);
        }
        return result;
    }
}

class ShopInfo {
    private String shopId;
    private double distance;
    // getter/setter
}
```

### Geospatial使用的注意事项

第一，坐标范围限制。经度范围是-180到180，纬度范围是-85.05112878到85.05112878。超出范围会报错。纬度范围限制是因为GeoHash算法在极地附近精度会急剧下降。

```java
// 错误示例：纬度超出范围
jedis.geoadd("test", 116.0, 90.0, "invalid");
// 报错：ERR invalid longitude,latitude pair
```

第二，有效距离计算。Geospatial计算的是球面直线距离，不考虑道路、建筑物等障碍。对于需要精确距离的场景，应结合地图API。

第三，大量数据的处理。如果地理位置数据量很大，georadius返回的结果可能很多。建议使用COUNT参数限制返回数量，或者在应用层进行分页处理。

```bash
# 限制返回10条最近的记录
georadius shops 116.397128 39.916527 10 km COUNT 10 ASC
```

第四，位置更新策略。对于实时位置更新的场景（如打车、外卖），需要频繁更新位置数据。考虑到性能，可以采用以下策略：

```java
// 策略1：定期批量更新
public void batchUpdateLocations(Map<String, double[]> locations) {
    Pipeline pipeline = jedis.pipelined();
    for (Map.Entry<String, double[]> entry : locations.entrySet()) {
        String userId = entry.getKey();
        double[] coord = entry.getValue();
        pipeline.geoadd(USER_LOCATION_KEY, coord[0], coord[1], userId);
    }
    pipeline.sync();
}

// 策略2：过期清理
public void cleanInactiveUsers() {
    // 删除超过一定时间未更新的用户位置
    // 可以通过额外的Sorted Set记录更新时间
}
```

第五，中国坐标偏移问题。中国的地图服务使用GCJ-02坐标系（火星坐标），而GPS使用WGS-84坐标系。如果数据来源不同，需要进行坐标转换，否则位置会有几百米的偏移。

### 地理围栏的实现

地理围栏是Geospatial的高级应用，可以判断一个点是否在某个区域内。

```java
/**
 * 简单的圆形地理围栏
 */
public boolean isInGeoFence(double centerLng, double centerLat, 
                            double radius, double targetLng, double targetLat) {
    String tempKey = "temp:fence:" + System.currentTimeMillis();
    
    // 添加临时点
    jedis.geoadd(tempKey, targetLng, targetLat, "target");
    
    // 查询临时点是否在范围内
    List<GeoRadiusResponse> results = jedis.georadius(
        tempKey, centerLng, centerLat, radius, GeoUnit.KM
    );
    
    // 清理临时数据
    jedis.del(tempKey);
    
    return !results.isEmpty();
}
```

对于复杂的地理围栏（多边形区域），需要结合其他算法实现，Redis的Geospatial目前只支持圆形范围查询。

## 总结

本章深入探讨了Redis的三种高级数据结构：BitMap、HyperLogLog和Geospatial。这三种数据结构各有其独特的设计理念和适用场景：

BitMap以位为单位存储数据，适合用户签到、在线状态、布尔值集合等场景，存储效率极高。使用时需要注意偏移量控制，避免因超大偏移量导致内存浪费。

HyperLogLog以固定12KB的存储空间实现大规模基数统计，标准误差约0.81%，适合UV统计、参与人数统计等对精度要求不高的场景。如果需要精确统计，应该选择Set或其他精确数据结构。

Geospatial专门处理地理位置数据，支持距离计算和范围查询，适合附近的人、附近的店铺、打车匹配等LBS应用场景。使用时需要注意坐标系问题，中国地区可能需要进行坐标转换。

在实际项目中，应该根据具体的业务需求选择合适的数据结构。对于海量数据统计场景，HyperLogLog是首选；对于位级操作和紧凑存储，BitMap是不二之选；对于地理位置相关功能，Geospatial提供了开箱即用的支持。

系列进度 5/16

下一章我们将深入探讨Redis的持久化机制：RDB与AOF。我们将分析两种持久化方案的原理、优缺点和最佳实践，帮助你做出正确的技术选型。

你对本章内容有什么疑问？在实际项目中是否使用过这些高级数据结构？欢迎在评论区分享你的经验和踩坑经历。

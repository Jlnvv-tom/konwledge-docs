# 核心实验室训练（上）——系统与算法实现

实验做了3个月跑不出结果？问题不在代码，在实验设计。

我是怕浪猫，一个在实验室里从崩溃到开窍的过来人。这篇文章拆解CS博士期间5个必须亲手做出来的系统实验——操作系统内核、分布式键值存储、关系查询引擎、高级数据结构、密码学协议——每个项目告诉你核心目标、实现步骤、验收标准和踩坑点。

这是「CS博士通关路」系列的第九篇。上一篇精读了从ResNet到GPT时代的论文，这一篇走进实验室，怕浪猫告诉你那些必须亲手做出来的系统。

## 一、系统构建实验室：简易操作系统内核

### 核心训练目标

写一个简易操作系统内核是系统方向的"成人礼"。它训练三个核心能力：中断处理（Interrupt Handling）——理解CPU如何响应外部事件。内存管理（Memory Management）——理解虚拟内存和页表机制。进程调度（Process Scheduling）——理解并发和上下文切换。

目标：在QEMU模拟器上运行多任务内核，支持基本系统调用。不是写一个Linux——而是写一个能启动、能调度、能跑用户程序的最小内核。

### 关键实现步骤

**Bootloader启动**：CPU上电后处于实模式（Real Mode），只有1MB可寻址空间，没有内存保护。Bootloader负责切换到保护模式（Protected Mode），设置GDT（Global Descriptor Table，全局描述符表）——GDT定义了代码段和数据段的基地址和限制。切换到保护模式后，开启分页（Paging），跳转到内核入口。

**中断系统**：设置IDT（Interrupt Descriptor Table，中断描述符表）——IDT是256个入口的数组，每个入口指向一个中断处理函数。CPU收到中断信号时，根据中断号查IDT找到处理函数。时钟中断（Timer Interrupt）是调度的驱动力——每个时钟滴答触发调度器检查是否需要切换进程。

**页表映射**：设置两级页表（Page Directory + Page Table）。虚拟地址通过页目录和页表翻译为物理地址。TLB（Translation Lookaside Buffer，旁路缓冲器）缓存页表项加速翻译。缺页处理（Page Fault Handler）在访问未映射的地址时被触发——分配物理页、更新页表、重新执行指令。

**进程管理**：设计PCB（Process Control Block，进程控制块）——包含进程状态、寄存器快照、页表指针、内核栈指针。上下文切换保存当前进程的寄存器到PCB，加载下一个进程的寄存器。调度算法实现——Round Robin（时间片轮转）是最简单的选择。

**系统调用**：用户态程序通过int 0x80（或syscall指令）陷入内核态。系统调用分派器根据系统调用号找到对应处理函数。基本系统调用包括write（输出字符）、read（读取输入）、fork（创建子进程）。

上下文切换（Context Switch）的核心汇编代码：

```asm
context_switch:
    # 保存当前进程上下文
    pusha               # 保存通用寄存器
    push %esp
    mov %esp, current_pcb_ptr  # 保存ESP到PCB
    # 加载下一进程上下文
    mov next_pcb_ptr, %esp
    pop %esp
    popa                # 恢复通用寄存器
    iret                # 从内核栈恢复CS:EIP:EFLAGS
```

这段汇编展示了上下文切换的本质——保存当前CPU状态到内存（PCB），从内存（另一个PCB）恢复CPU状态。iret指令从中断返回，同时恢复代码段、指令指针和标志寄存器。

### 从实模式到保护模式的细节

实模式到保护模式的切换是内核启动最tricky的部分。CPU上电后从0xFFFF0处执行BIOS，BIOS加载Bootloader到0x7C00并跳转。此时CPU处于实模式——16位寄存器、段地址左移4位加偏移得到物理地址、没有特权级概念。

切换步骤：第一步开启A20地址线——通过键盘控制器或Fast A20 Gate，使得第21根地址线可用（实模式下A20被锁存为0，限制寻址到1MB）。第二步加载GDT——用lgdt指令把GDT的基地址和限制加载到GDTR寄存器。第三步设置CR0寄存器的PE位（Protection Enable）——这一步正式切换到保护模式。第四步做长跳转（far jump）刷新流水线——因为流水线中可能还有实模式的指令。

每一步出错都会导致重启，而且没有错误信息——因为此时还没有屏幕输出能力。调试这个阶段只能用QEMU的日志功能（-d int -d cpu_reset）或向串口输出字符。怕浪猫在这个阶段卡了3天——最后发现是A20线没开对。

### 中断处理的细节

中断处理的核心是IDT和中断控制器（PIC，Programmable Interrupt Controller）。8259 PIC把硬件中断映射到IRQ 0-15，经过PIC重映射后映射到中断号0x20-0x2F。时钟中断是IRQ 0（中断号0x20），键盘中断是IRQ 1（中断号0x21）。

中断处理函数的职责：保存寄存器（push指令）、处理中断、发送EOI（End of Interrupt）给PIC、恢复寄存器（pop指令）、iret返回。如果忘记发EOI，PIC就不会再触发同优先级的中断——这是中断"消失"的常见原因。

中断重入是另一个陷阱。如果在中断处理函数执行期间又收到中断，CPU会再次进入中断处理——如果共享数据没有锁保护，就会出现竞态条件。解决方法是在中断处理函数入口处CLI（清除中断标志），在出口处STI（设置中断标志）。但如果中断处理时间太长，会丢失中断——所以中断处理应该尽可能短。

### 验收标准和踩坑点

验收标准：能运行至少2个用户进程并正确调度、支持基本系统调用（write/read/fork）。

常见踩坑点：实模式到保护模式切换失败——通常是GDT设置错误或A20地址线未开启。中断重入导致死锁——中断处理函数执行时又收到中断，需要在IDT入口处清除中断标志（CLI）。页表映射错误导致Triple Fault——CPU在处理一个异常时又发生异常，触发Triple Fault后系统重启。

| 模块 | 验收标准 | 预计工时 | 常见坑 |
|------|---------|---------|--------|
| Bootloader | 成功进入保护模式跳转到内核 | 1周 | A20线、GDT设置 |
| 中断系统 | 时钟中断正常触发、键盘中断响应 | 1周 | 中断重入、PIC配置 |
| 页表映射 | 虚拟地址正确映射、缺页可恢复 | 1.5周 | 对齐错误、Triple Fault |
| 进程管理 | 2个进程正确轮转调度 | 1.5周 | 上下文切换寄存器丢失 |
| 系统调用 | write/read/fork正常工作 | 1周 | 用户态/内核态栈切换 |

> 写内核最大的收获不是"会写内核了"，而是"理解了计算机是怎么运作的"。当你亲手设置过GDT、处理过缺页、做过上下文切换，你对程序执行的理解就不再是黑盒。

## 二、分布式系统实验室：分布式键值存储

### 核心训练目标

基于Raft共识算法实现一个分布式键值存储。训练三个核心能力：共识算法实现——Raft的Leader Election和Log Replication。复制状态机（Replicated State Machine）——所有节点以相同顺序执行相同命令。容错处理——节点崩溃恢复和网络分区恢复。

目标：3节点集群能容忍1节点故障，保证线性一致性（Linearizability）——读操作返回最新已写入的值。

### 关键实现步骤

**Leader Election**：每个节点有三种状态——Follower、Candidate、Leader。Follower在选举超时（Election Timeout）内没收到Leader的心跳，转为Candidate并发起选举。Candidate递增term，给自己投票，向其他节点发送RequestVote RPC。获得majority（多数派）选票后成为Leader。

选举超时必须随机化——否则多个Follower同时超时同时发起选举，选票分散无人当选。随机化范围通常为150-300ms。这个看似简单的细节是Raft"可理解性"设计哲学的体现——用随机化避免复杂的选举冲突解决。

**Log Replication**：Leader收到客户端命令后，追加到自己的日志，通过AppendEntries RPC复制到所有Follower。当majority确认后，Leader提交该日志项（Commit），应用到状态机，返回客户端成功。

日志匹配（Log Matching）保证一致性：AppendEntries RPC包含prevLogIndex和prevLogTerm——Follower检查在prevLogIndex处的日志term是否匹配。如果不匹配，Leader递减nextIndex重试。这个机制确保Follower的日志和Leader的日志最终一致。

**Safety**：选举限制确保被选出的Leader包含所有已提交的日志——RequestVote RPC包含candidate的最后日志term和index，投票方只投给日志至少一样新的candidate。提交规则确保只有当前term的日志项被提交时才能提交之前的日志项——这避免了图8中描述的一致性问题。

**容错处理**：节点崩溃后重启，从持久化的日志恢复。网络分区恢复后，少数派分区的Leader发现自己term落后后自动降级为Follower。日志压缩（Snapshot）防止日志无限增长——创建snapshot包含当前状态，删除snapshot之前的日志。

Raft中AppendEntries RPC的核心处理逻辑：

```python
def handle_append_entries(req, state):
    if req.term < state.current_term:
        return (state.current_term, False)  # 拒绝旧term
    if req.term > state.current_term:
        state.current_term = req.term
        state.voted_for = None
    state.leader_id = req.leader_id
    # 检查日志一致性
    if req.prev_log_index > 0:
        if (state.log[req.prev_log_index].term != 
            req.prev_log_term):
            return (state.current_term, False)  # 日志不匹配
    # 追加新日志项，删除冲突项
    for i, entry in enumerate(req.entries):
        idx = req.prev_log_index + 1 + i
        if idx < len(state.log) and state.log[idx].term != entry.term:
            state.log = state.log[:idx]  # 删除冲突
        state.log.append(entry)
    # 更新commitIndex
    if req.leader_commit > state.commit_index:
        state.commit_index = min(req.leader_commit, 
                                  len(state.log) - 1)
    return (state.current_term, True)
```

这段代码展示了AppendEntries的三个核心检查——term检查（拒绝旧Leader）、日志一致性检查（确保日志连续）、提交更新（推进commitIndex）。简洁的逻辑处理了分布式日志复制中的各种边界情况。

### 验收标准和踩坑点

验收标准：在1节点宕机情况下仍能正确读写、网络分区恢复后数据一致、线性一致性测试通过。

常见踩坑点：选举活锁——多个节点反复超时发起选举无人当选。解决方法：增大随机化范围、检查网络延迟。日志不一致导致数据丢失——通常是因为AppendEntries的日志冲突处理有bug。网络分区脑裂——两个分区各选出一个Leader，恢复后需要正确处理。Raft通过term机制解决这个问题——更高term的Leader胜出，旧Leader的未提交日志被覆盖。

### 线性一致性的理解

线性一致性（Linearizability）是最强的一致性模型——每个操作看起来在某个时间点原子地完成，且和操作的实际调用/返回时间一致。具体来说：如果操作A的返回早于操作B的调用，那么在全局顺序中A必须在B之前。

线性一致性的测试方法：构造并发读写操作，记录每个操作的调用时间和返回时间。检查是否存在一个全局顺序使得所有操作的结果合理且满足时间约束。线性一致性测试是NP难的——Jepsen使用WGL（While-Go-Linearizability）算法做穷举搜索，对于少量操作可以判定。

为什么线性一致性重要？因为它使得分布式系统"看起来像单机系统"。客户端不需要担心并发问题——线性一致性保证了读操作返回最新写入值。但线性一致性的代价是性能——在分布式环境中保证线性一致性需要额外的协调（如Raft共识），延迟比最终一致性高。

### Raft的工程实现细节

Raft的工程实现中有几个论文没详细讨论但实践中很重要的细节。

第一，日志持久化的顺序。必须先持久化日志项再发送AppendEntries——否则如果Leader在持久化前崩溃，已发送的日志项可能丢失。持久化使用fsync确保写入磁盘——不是只写到操作系统页缓存。

第二，快照的传输。当Follower日志太落后（Leader已经做了快照），Leader需要发送整个快照。InstallSnapshot RPC包含快照数据和最后包含的日志index/term。Follower收到后丢弃index之前的所有日志，用快照替换。快照传输可能很大（GB级），需要分块传输和断点续传。

第三，批量化和流水线。Leader不需要等每个AppendEntries确认再发下一个——可以流水线发送多个AppendEntries。批量化把多个日志项放在一个AppendEntries中减少RPC开销。这些优化对性能至关重要——没有它们，Raft的吞吐可能低一个数量级。

| 子问题 | 实现要点 | 验收方法 |
|--------|---------|---------|
| Leader Election | 随机化超时、term机制、投票限制 | 杀掉Leader观察新Leader选出 |
| Log Replication | AppendEntries、日志匹配、nextIndex | 写入后读出验证一致性 |
| Safety | 选举限制、提交规则 | 网络分区后验证数据一致 |

> 分布式系统的实验是最"折腾"的——因为你要处理"正常情况下不会发生但实际中总是发生"的故障。一个在单机上正确的程序在分布式环境中可能完全错误——因为网络延迟、时钟不同步、部分故障这些因素在单机中不存在。

## 三、数据库实验室：关系查询引擎

### 核心训练目标

实现一个支持SQL子集的关系查询引擎。训练四个核心能力：查询解析（Query Parsing）——SQL语句到语法树。查询优化（Query Optimization）——逻辑优化和物理优化。执行计划（Execution Plan）——物理算子的实现。事务处理（Transaction Processing）——简化的ACID保证。

目标：支持SELECT/FROM/WHERE/JOIN/GROUP BY/ORDER BY，能执行多表JOIN查询并返回正确结果。

### 关键实现步骤

**词法分析（Lexical Analysis）**：把SQL字符串分解为Token序列。Token类型包括关键字（SELECT、FROM、WHERE）、标识符（表名、列名）、常量（数字、字符串）、运算符（=、<、>）。可以用flex生成词法分析器，或手写——手写更容易理解原理。

**语法分析（Syntax Analysis）**：根据SQL语法规则把Token序列组织为语法树（AST）。AST的节点类型包括SelectStmt（SELECT语句）、TableRef（表引用）、ColumnRef（列引用）、BinaryExpr（二元表达式）等。可以用bison生成语法分析器，或手写递归下降解析器——递归下降更直观且不需要额外工具。

**逻辑计划生成**：把AST转换为关系代数表达式。SELECT对应选择（Selection），FROM对应笛卡尔积（Cartesian Product），WHERE对应选择，JOIN对应连接（Join），GROUP BY对应分组聚合（Group By Aggregation）。逻辑优化包括谓词下推（把WHERE条件下推到JOIN之前减少数据量）、投影消除（去掉不需要的列）。

**物理计划执行**：把逻辑计划转换为物理执行计划。每个逻辑算子对应一个或多个物理算子——选择可以是顺序扫描（Sequential Scan）或索引扫描（Index Scan），连接可以是Nested Loop Join或Hash Join。

Hash JOIN的核心执行逻辑：

```python
def hash_join(build_table, probe_table, join_key):
    # Build阶段：构建哈希表
    hash_table = {}
    for row in build_table:
        key = row[join_key]
        if key not in hash_table:
            hash_table[key] = []
        hash_table[key].append(row)
    # Probe阶段：探测哈希表
    results = []
    for row in probe_table:
        key = row[join_key]
        if key in hash_table:
            for build_row in hash_table[key]:
                results.append(merge(build_row, row))
    return results
```

这段代码展示了Hash Join的两阶段设计——Build阶段把小表建哈希表，Probe阶段遍历大表查哈希表。时间复杂度O(n+m)远优于Nested Loop Join的O(n*m)，但需要内存存放哈希表。Grace Hash Join通过分块处理解决内存不足的问题——把两个表按join_key哈希到相同的分区，每对分区单独做Hash Join。

### 查询优化的核心原理

查询优化是数据库系统最核心的技术之一。给定一个查询，可能有成百上千种执行计划，优化器的任务是找到代价最低的那个。

逻辑优化（Logical Optimization）基于关系代数的等价变换。谓词下推（Predicate Pushdown）——把WHERE条件下推到JOIN之前，减少JOIN的数据量。投影消除（Projection Elimination）——去掉查询不需要的列，减少数据传输。子查询展开（Subquery Flattening）——把子查询转换为JOIN，给优化器更多选择空间。

物理优化（Physical Optimization）基于代价模型（Cost Model）。代价模型估计每种执行计划的代价——CPU代价（记录数 * 处理复杂度）、I/O代价（磁盘读取次数）、内存代价（Hash表大小）。代价估计依赖于统计信息——表行数、列基数（Cardinality）、数据分布直方图（Histogram）。

代价估计的不准确性是优化器的主要挑战。如果统计信息过时或数据分布倾斜，代价估计可能偏差很大，导致优化器选择次优计划。现代数据库使用自适应查询执行（Adaptive Query Execution）——在运行时根据实际数据量动态调整执行计划。

### 执行模型的选择

数据库的执行模型主要有两种：火山模型（Volcano Model）和向量化执行（Vectorized Execution）。

火山模型：每个算子实现next()接口，每次返回一条记录。上层算子调用下层算子的next()获取记录。优点是简洁优雅，缺点是next()调用的函数开销在大数据量下显著。

向量化执行：每次返回一批记录（如1024条），对整批数据做相同的操作。向量化利用了CPU的SIMD（Single Instruction Multiple Data）指令——一条指令同时处理多个数据。ClickHouse、DuckDB等现代分析数据库使用向量化执行，性能比火山模型高一个数量级。

### 验收标准和踩坑点

验收标准：能执行多表JOIN查询并返回正确结果、支持基本的查询优化（谓词下推）、查询结果和标准SQL引擎一致。

常见踩坑点：SQL解析器边界情况——空值处理、嵌套子查询、别名解析。JOIN结果不正确——通常是连接条件处理错误或重复行处理错误。内存不足处理——大表JOIN时内存不够，需要溢出到磁盘（External Sort-Merge Join）。

| 层次 | 核心组件 | 输入 | 输出 |
|------|---------|------|------|
| 词法分析 | Tokenizer | SQL字符串 | Token序列 |
| 语法分析 | Parser | Token序列 | AST |
| 逻辑计划 | Optimizer | AST | 逻辑计划树 |
| 物理执行 | Executor | 物理计划树 | 结果集 |

> 写查询引擎让你理解"SQL是怎么执行的"。当你实现了谓词下推、Hash Join、排序聚合，你看SQL执行计划的方式就完全不同了——每条SQL不再是一个黑盒，而是一棵可以优化的树。

## 四、算法实验室：高级数据结构、近似算法、密码学协议

### 项目1：高级数据结构实现

实现三个经典数据结构：B树（B-Tree）、跳表（Skip List）、布隆过滤器（Bloom Filter）。

B树的实现重点在插入和删除时的分裂（Split）和合并（Merge）。B树是多路搜索树，每个节点可以有多个子节点——这减少了树的高度，适合磁盘存储（减少I/O次数）。插入时如果节点满了就分裂——把中间关键字提升到父节点，原节点分成两半。删除时如果节点太空就合并——和兄弟节点合并或从兄弟借关键字。

跳表是概率性的数据结构——通过随机层数（Random Level）实现平衡。插入时每个节点以概率p获得更高层。跳表的期望查找复杂度是O(log n)——和平衡树一样，但实现简单得多。Redis的有序集合使用跳表实现。

布隆过滤器的核心插入和查询代码：

```python
import mmh3

class BloomFilter:
    def __init__(self, size, num_hashes):
        self.bit_array = [False] * size
        self.size = size
        self.num_hashes = num_hashes

    def add(self, item):
        for i in range(self.num_hashes):
            idx = mmh3.hash(str(item), i) % self.size
            self.bit_array[idx] = True

    def contains(self, item):
        for i in range(self.num_hashes):
            idx = mmh3.hash(str(item), i) % self.size
            if not self.bit_array[idx]:
                return False  # 一定不存在
        return True  # 可能存在（有误判率）
```

这段代码展示了布隆过滤器的核心——多个哈希函数映射到位数组。查询时所有位都为1才返回"可能存在"——存在误判率（False Positive Rate）。误判率取决于位数组大小和哈希函数个数，可以通过公式推导最优参数。

### B树的实现细节

B树的插入和删除是最容易出bug的部分。插入时需要从根节点开始找到插入位置。如果叶子节点满了（关键字个数达到2t-1，t是最小度数），需要分裂。分裂操作把一个满节点分成两个，中间关键字提升到父节点。如果父节点也满了，分裂继续向上传播——可能一直传到根节点，此时树的高度增加。

删除比插入更复杂。删除非叶子节点的关键字需要用前驱或后继替换。删除后如果节点关键字太少（小于t-1），需要从兄弟节点借关键字或和兄弟合并。合并操作可能导致父节点关键字太少——删除的"下溢"也可能向上传播。

B+树是B树的变体——所有数据存在叶子节点，内部节点只存索引。B+树的叶子节点通过链表相连——这使得范围查询非常高效（顺着链表扫描即可）。大多数数据库索引使用B+树而非B树。

### 跳表的概率分析

跳表的期望高度是O(log n)。每个节点有概率p获得更高一层（通常p=1/2）。n个节点的跳表，第k层期望有n/2^k个节点。当n/2^k = 1时，k = log2(n)。所以期望高度是log2(n)。

跳表的空间复杂度也是O(n)——每个节点平均出现在1/(1-p)层中。当p=1/2时，每个节点平均出现在2层中——空间开销是2n，和链表的n相比只多了常数倍。

跳表和平衡树的性能对比：查找、插入、删除都是O(log n)。但跳表的实现更简单——不需要旋转操作。跳表的常数因子略大（需要多次指针跳转），但在实际中差异不大。Redis选择跳表而非红黑树的原因就是实现简单且支持范围查询。

### 项目2：近似算法设计

Vertex Cover的2-近似算法：选取任意一条边(u,v)，把u和v都加入覆盖集，删除所有和u或v相连的边，重复直到没有边。这个算法的近似比是2——因为每次选取的边互不相邻，最优解至少需要选取每条边的至少一个端点，所以近似解的大小不超过最优解的2倍。

Set Cover的ln(n)-近似算法：每次选取覆盖最多未覆盖元素的集合，直到所有元素被覆盖。这个贪心算法的近似比是ln(n)——其中n是元素总数。证明框架使用线性规划松弛（LP Relaxation）和对偶分析。

近似比（Approximation Ratio）的证明框架：设算法解为A，最优解为OPT。证明A <= c * OPT（最小化问题）或A >= c * OPT（最大化问题）。证明通常通过找到一个OPT的下界（或上界），然后证明A和这个界的关系。

### 近似算法的设计思路

近似算法的核心思路是"用最优性换效率"。对于NP困难问题，精确算法在最坏情况下需要指数时间——实际中不可接受。近似算法在多项式时间内给出接近最优的解。

近似算法的设计技巧：贪心策略（每步做局部最优选择）、线性规划松弛（把整数规划松弛为线性规划，然后取整）、局部搜索（从一个解出发不断改进）、随机化（引入随机性避免最坏情况）。

近似比的分析方法：对于最小化问题，需要证明ALG <= r * OPT（r是近似比）。常用技巧：找到OPT的一个下界LB，证明ALG <= r * LB。对于Vertex Cover，OPT >= |匹配|（因为每条匹配边至少需要一个端点），贪心算法选了2|匹配|个顶点，所以近似比是2。

### 近似算法的不可近似性

有些NP困难问题可以很好地近似（如Vertex Cover有2-近似），但有些问题很难近似。Set Cover的近似比下界是ln(n)——除非P=NP，否则不可能做到(1-epsilon)ln(n)近似。这个下界通过PCP定理和归约证明。

不可近似性（Inapproximability）是理论CS的重要研究方向。PCP定理使得NP hardness可以扩展到近似算法——如果某个问题有r-近似算法，则P=NP。这个框架在1990年代建立，极大地深化了我们对NP困难问题近似性的理解。

### 项目3：密码学协议实现

RSA加密解密：密钥生成（选p、q、计算n=e*d mod phi(n)）、加密（c=m^e mod n）、解密（m=c^d mod n）、签名（s=m^d mod n）、验证（m=s^e mod n）。使用Python的pow函数做模幂运算，gmpy2库生成大素数。

Diffie-Hellman密钥交换的核心代码：

```python
import random

def dh_key_exchange(p, g):
    # p: 大素数, g: 生成元
    # Alice
    a = random.randint(2, p - 2)
    A = pow(g, a, p)
    # Bob
    b = random.randint(2, p - 2)
    B = pow(g, b, p)
    # 交换A和B后计算共享密钥
    shared_alice = pow(B, a, p)   # g^(ab) mod p
    shared_bob = pow(A, b, p)     # g^(ab) mod p
    assert shared_alice == shared_bob
    return shared_alice
```

这段代码展示了DH密钥交换的完整流程——双方各自生成私钥和公钥，交换公钥后独立计算共享密钥。窃听者知道p、g、A、B但无法计算g^(ab)——离散对数问题的困难性保证了安全性。

Schnorr协议是基础的ZKP（Zero-Knowledge Protocol）——证明者知道离散对数x但不泄露x。协议三步：承诺（Prover发送承诺r=g^k）、挑战（Verifier发送随机挑战e）、响应（Prover发送s=k-xe）。验证者检查g^s * y^e = r（其中y=g^x）。如果Prover知道x，等式成立；如果不知道，只有1/q的概率"蒙对"。

### 密码学实现的安全陷阱

密码学算法的正确实现比算法本身更难。"教科书RSA"是安全的，但很多实现不安全。常见陷阱：

随机数生成器（Random Number Generator, RNG）必须使用密码学安全的RNG——如/dev/urandom或硬件RNG。如果RNG可预测，私钥就可能被推导。2012年，某比特币钱包因为Android的RNG漏洞导致私钥被破解。

侧信道攻击（Side-Channel Attack）通过测量实现的时间、功耗、电磁辐射来推断密钥。RSA的模幂运算时间依赖于私钥d的比特——通过测量多次运算时间可以恢复d。防御方法：恒定时间实现（Constant-Time Implementation）——无论密钥值如何，运算时间相同。

填充预言攻击（Padding Oracle Attack）：攻击者通过观察服务器对错误填充的响应来逐字节恢复明文。PKCS#1 v1.5的Bleichenbacher攻击是经典案例。防御方法：使用OAEP填充方案，或在新系统中使用RSA-OAEP替代PKCS#1 v1.5。

### ZKP的工程实现

Schnorr协议的工程实现需要注意几个点。参数选择：p需要至少2048位，q至少256位，g是Z_p*的子群生成元。随机数k必须每次不同——如果两次使用相同的k，私钥x可以通过简单的代数运算推导出来。

非交互式Schnorr协议通过Fiat-Shamir启发式（Fiat-Shamir Heuristic）实现——用Hash(commitment)替代Verifier的随机挑战。这个技巧把交互式协议变为非交互式，是zk-SNARK的基础之一。

| 项目 | 理论深度 | 编程难度 | 面试价值 |
|------|---------|---------|---------|
| 高级数据结构 | 中 | 中高 | 高 |
| 近似算法 | 高 | 中 | 中高 |
| 密码学协议 | 高 | 中 | 中 |

> 算法实验的价值不在于"实现了一个数据结构"，而在于"通过实现理解了设计决策"。为什么B树适合磁盘？为什么跳表用概率替代平衡操作？为什么布隆过滤器可以容忍误判？这些问题的答案在你亲手实现后变得直观。

## 五、5个实验项目汇总与自测建议

| 项目 | 核心目标 | 验收标准 | 预计工时 | 常见坑 | 参考资源 |
|------|---------|---------|---------|--------|---------|
| OS内核 | 中断/内存/调度 | 2进程调度+syscall | 6周 | Triple Fault | MIT 6.828 |
| 分布式KV | Raft共识 | 1节点容错+线性一致 | 4周 | 选举活锁 | MIT 6.824 |
| 查询引擎 | SQL解析/优化/执行 | 多表JOIN正确 | 3周 | 解析边界 | CMU 15-445 |
| 数据结构 | B树/跳表/布隆 | 大规模数据测试 | 2周 | 边界处理 | 算法导论 |
| 密码协议 | RSA/DH/ZKP | 测试向量验证 | 2周 | 随机数安全 | Boneh书 |

### 自测用例设计建议

每个项目都需要系统化的自测用例。OS内核的自测：测试两个进程交替输出字符（验证调度）、测试fork后子进程独立运行（验证进程隔离）、测试写入只读内存页触发段错误（验证内存保护）。

分布式KV的自测：杀掉Leader后集群是否在选举超时内恢复、网络分区时少数派是否拒绝写入、分区恢复后数据是否最终一致。使用Jepsen风格的测试框架——注入故障、执行操作、验证不变量。

查询引擎的自测：准备一组SQL语句和预期结果（可以用SQLite生成），覆盖单表查询、多表JOIN、聚合、排序、子查询。特别注意NULL值处理和空表边界情况。

## 六、系统类实验的时间管理

### 时间分配原则

系统实验的时间分配遵循"60-20-20"原则：60%实际编码、20%调试、20%文档和测试。但这个比例不是线性的——前几周编码占比高，后几周调试和测试占比逐渐增加。

### 12周项目时间规划

| 周次 | 交付物 | 状态检查 |
|------|--------|---------|
| 1 | 环境搭建+框架代码 | QEMU能启动空内核 |
| 2 | Bootloader+GDT+保护模式 | 成功进入保护模式 |
| 3 | 中断系统+时钟中断 | 时钟中断触发调度器 |
| 4 | 页表映射+缺页处理 | 虚拟内存正常工作 |
| 5 | 进程PCB+上下文切换 | 2进程轮转调度 |
| 6 | 系统调用(write/read) | 用户程序能输出 |
| 7 | 系统调用(fork/exec) | 能创建子进程 |
| 8 | 文件系统(可选) | 能读写文件 |
| 9 | 测试+Bug修复 | 所有自测用例通过 |
| 10 | 性能优化 | 基准测试通过 |
| 11 | 文档撰写 | 设计文档完整 |
| 12 | 答辩准备 | 演示流畅 |

### 调试技巧

系统类实验的调试比应用层调试困难得多——因为print可能不可用（内核没有printf）、断点可能不可用（没有调试器）、错误可能导致系统重启（Triple Fault）。

日志系统设计：在内核中实现一个简单的printk函数——向串口（Serial Port）输出字符。QEMU可以把串口输出重定向到文件。日志分级别——DEBUG、INFO、WARN、ERROR——通过编译选项控制输出级别。

断点策略：QEMU自带的GDB stub支持远程调试。用qemu -s -S启动QEMU，在另一个终端用gdb连接。可以设置断点、单步执行、查看寄存器和内存。这是调试内核最有效的工具。

性能分析：用perf或自己实现的计时器测量关键路径的执行时间。常见性能问题：频繁的TLB flush（每次切换页表都flush TLB）、锁竞争（多个CPU核争抢自旋锁）、内存分配开销（频繁分配/释放小对象）。

### 协作建议

团队项目的分工建议：按模块划分而非按层次划分。例如OS内核项目，一人负责Bootloader+中断，一人负责内存管理，一人负责进程调度——而不是一人写"所有头文件"、一人写"所有实现"。按模块划分使得每个人都有端到端的ownership。

Code Review的要点：检查逻辑正确性（代码是否做了正确的事）、边界条件处理（空指针、整数溢出、数组越界）、并发安全（共享变量的访问是否有锁保护）、资源管理（内存是否泄漏、文件描述符是否关闭）。

Git分支管理：main分支保持可运行状态，feature分支开发新功能。通过Pull Request合并——至少一人Review后才能合并。这种流程保证了main分支始终可演示——在答辩时不会因为"最新代码有bug"而尴尬。

### 并行策略：周粒度交付

把大项目拆分为周粒度的小任务，每周交付一个可运行的子模块。这比"先全部写完再测试"有效得多——因为系统实验的模块之间有依赖关系，如果前面的模块有bug，后面的模块全部基于错误基础构建。

每周的交付物应该是"可演示的"——能在QEMU上跑起来、能看到输出、能验证正确性。这种"每周演示"的节奏迫使他不断集成——避免最后一周才发现"模块拼不起来"。

怕浪猫的OS内核项目就因为第一周不重视"可运行"交付，导致第三周才发现Bootloader有bug——前面两周的工作全部基于错误的基础。修复Bootloader后重新调试了所有模块。这个教训让我此后每周必做"可运行检查"。

### 调试的系统化方法

系统调试需要系统化的方法，而不是随机改代码"碰运气"。

第一步：复现问题。确定bug的触发条件——是偶发还是必现？和输入数据有关还是和时序有关？偶发bug通常和并发有关——多线程竞态、中断时序、网络延迟。

第二步：缩小范围。通过日志和断点确定bug发生在哪个模块。二分法是高效的——在代码中间加断点，看bug在前半段还是后半段。

第三步：定位根因。理解bug为什么发生——是逻辑错误（代码没做正确的事）、还是假设错误（代码基于不成立的假设）、还是接口错误（模块之间的约定不一致）。

第四步：修复并回归测试。修复后不仅要测原来的失败用例，还要测试相关功能——确保修复没有引入新bug。回归测试用例应该加入测试套件，防止同一bug再次出现。

> 系统实验是最能体现"动手能力"的训练。理论课告诉你虚拟内存的原理，但只有你亲手设置过页表、处理过缺页、调试过Triple Fault，你才算真正理解了虚拟内存。这个过程痛苦但值得——怕浪猫在OS内核实验上花了6周，但这6周对系统理解的提升超过任何一门课。

### 从实验到研究

系统实验不只是课程作业——它是研究的起点。很多顶级系统论文来自课程实验的延伸。MIT 6.824的Raft实验催生了大量分布式系统研究。CMU 15-445的数据库实验是很多查询优化论文的基础。

当你做完一个实验后，问自己：这个系统的性能瓶颈在哪？如果数据量增大10倍会怎样？如果换成SSD会怎样？如果加入机器学习会怎样？这些问题就是研究选题的雏形。

怕浪猫的分布式KV存储实验后来发展成了我的第一个研究工作——在Raft基础上加入了读写分离优化，把读吞吐提升了3倍。这个工作发在了分布式系统会议。从课程实验到研究论文的路径是：实现baseline -> 发现瓶颈 -> 设计优化 -> 实验验证 -> 论文写作。系统实验给你的是baseline和瓶颈发现的能力。

### 实验环境的管理

系统实验需要管理复杂的环境——不同编译器版本、不同库版本、不同模拟器配置。建议使用自动化脚本管理环境。

Docker是管理实验环境的好工具。把编译器、依赖库、QEMU版本打包到Docker镜像中——任何人都能一键复现你的环境。如果实验需要在多台机器上运行，Docker Compose可以定义多容器编排。

Makefile是C/C++项目的标配。一个好的Makefile应该支持：make build（编译）、make run（在QEMU中运行）、make test（运行测试）、make clean（清理）。这些target使得实验可以一键操作——减少手动操作中的错误。

### 跨实验的知识迁移

5个实验项目看似独立，但它们之间有深层联系。OS内核中的虚拟内存机制和数据库中的缓冲池管理本质上都是"把大数据集放到有限内存中"的问题。分布式KV中的Raft日志和数据库中的WAL（Write-Ahead Log）本质上都是"持久化操作序列以保证可恢复性"的技术。查询引擎中的代价模型和编译器中的优化器本质上都是"在多个等价方案中选最优"的问题。

当你做完所有5个实验后，尝试把这些联系显式化——画出每个实验的核心数据结构和算法，标注它们之间的相似性。这种跨领域的知识迁移能力是系统研究的核心竞争力。很多创新工作就来自"把A领域的技术应用到B领域"——比如把数据库的查询优化技术应用到ML训练中（Adaptive Query Execution -> Adaptive Training）。这种迁移思维是博士训练最宝贵的收获——你不再只是某个领域的工匠，而是能跨领域思考的研究者。这比任何一个具体的实验技能都更重要，因为它决定了你研究的上限。

## 系列进度与下章预告

这篇文章是「CS博士通关路」系列的第九篇。5个系统实验项目、验收标准、12周时间规划——这些是怕浪猫在实验室里用血泪换来的经验。

收藏这篇文章，作为你做系统实验的参考。当你卡在某个bug时，回查这里的踩坑点。

在评论区告诉怕浪猫：你做过的最折磨人的系统实验是什么？

**系列进度 9/12**

下一章，怕浪猫带你进入ML实验室训练。从手写反向传播到训练小型语言模型，从数据管道到分布式训练——我会告诉你ML实验和系统实验有什么不同，以及怎么在GPU上高效做实验。

关注我，追更不迷路。

# 核心实验室训练（下）——机器学习与科研方法

你以为ML实验就是调参？真正的ML实验从实验设计就开始决定成败。

我是怕浪猫，一个从调参工程师进化成研究者的过来人。这篇文章是系统实验室训练的下半部分——4个ML实验项目加上科研方法论训练，外加实验室轮转策略。

这是「CS博士通关路」系列的第十篇。上一篇做了5个系统实验，这一篇走进ML实验室，从手写反向传播到训练小型语言模型，再到科研方法论和轮转策略。

## 一、从零实现反向传播：纯NumPy在MNIST上达到97%

### 核心训练目标

用NumPy从头实现反向传播是理解深度学习的最短路径。这个实验训练三个核心能力：梯度计算（Gradient Computation）——理解链式法则（Chain Rule）在神经网络中的具体形式。损失函数——理解交叉熵损失及其梯度的推导。优化算法——理解SGD（Stochastic Gradient Descent，随机梯度下降）、Momentum、Adam的原理和差异。

目标：不使用PyTorch或TensorFlow，仅用NumPy实现全连接网络，在MNIST测试集上达到97%以上准确率。

### 关键实现步骤

**网络结构定义**：网络由输入层（784维，28x28像素展平）、隐藏层（128维，ReLU激活）、输出层（10维，Softmax激活）组成。权重初始化使用He初始化——W ~ N(0, sqrt(2/n_in))，其中n_in是输入维度。He初始化针对ReLU设计——因为ReLU把一半的激活值置零，方差需要加倍才能保持信号强度。

**前向传播**：z1 = W1 @ x + b1，h1 = ReLU(z1)，z2 = W2 @ h1 + b2，y_hat = Softmax(z2)。Softmax把输出转换为概率分布——y_hat[i] = exp(z2[i]) / sum(exp(z2))。数值稳定性技巧：先减去最大值再取exp——防止exp溢出。

**损失计算**：交叉熵损失L = -sum(y * log(y_hat))，其中y是one-hot标签。交叉熵损失的梯度dL/dz2 = y_hat - y——这个简洁的结果是softmax和交叉熵组合的数学优势。如果用均方误差，梯度会多一个softmax导数项，复杂且训练慢。

**反向传播**：dz2 = y_hat - y，dW2 = dz2 @ h1.T，dh1 = W2.T @ dz2，dz1 = dh1 * (z1 > 0)（ReLU的导数是阶跃函数），dW1 = dz1 @ x.T。这就是链式法则的具体实现——从输出层向输入层逐层计算梯度。

反向传播核心计算代码：

```python
def backward(params, cache, x, y):
    W1, b1, W2, b2 = params
    h1, y_hat = cache
    m = x.shape[0]  # batch size
    # 输出层梯度
    dz2 = (y_hat - y) / m  # softmax + cross-entropy
    dW2 = dz2.T @ h1
    db2 = dz2.sum(axis=0)
    # 反传到隐藏层
    dh1 = dz2 @ W2
    dz1 = dh1 * (h1 > 0)  # ReLU导数
    dW1 = dz1.T @ x
    db1 = dz1.sum(axis=0)
    return dW1, db1, dW2, db2
```

这段代码展示了反向传播的本质——从输出层开始，用链式法则逐层计算梯度。dz2 = (y_hat - y) / m是softmax和交叉熵的组合梯度——简洁到令人惊叹。ReLU的导数(h1 > 0)是一个布尔值——ReLU在正数区域导数为1，负数区域为0。

**参数更新**：SGD——W -= lr * dW。Momentum——v = 0.9 * v + dW，W -= lr * v。Adam——结合一阶矩和二阶矩的自适应学习率。Adam通常是默认选择——它对学习率不敏感，收敛快。

### 验收标准和踩坑点

验收标准：MNIST测试集准确率97%以上、梯度检查（Gradient Check）通过。梯度检查用数值梯度验证解析梯度——对每个参数加微小扰动epsilon，计算数值梯度(f(x+epsilon) - f(x-epsilon)) / (2*epsilon)，和解析梯度比较。相对误差应小于1e-7。

常见踩坑点：梯度检查数值不稳定——使用float64而非float32，epsilon取1e-5。Softmax溢出——减去最大值。学习率设置不当——太大不收敛，太小收敛慢。He初始化和Xavier初始化的区别——ReLU用He，tanh/Sigmoid用Xavier。

> 手写反向传播是理解深度学习的"顿悟时刻"。当你在NumPy中亲手实现了链式法则，PyTorch的loss.backward()不再是黑盒——你知道每个梯度的来源和物理意义。这个理解是调试训练问题的根基。

### 梯度检查的实现细节

梯度检查是验证反向传播正确性的关键方法。数值梯度通过有限差分计算：对参数W[i,j]加epsilon，计算损失L_plus；减epsilon，计算损失L_minus；数值梯度 = (L_plus - L_minus) / (2 * epsilon)。

比较数值梯度和解析梯度：rel_error = |analytic - numeric| / max(|analytic|, |numeric|)。rel_error应小于1e-7。如果大于1e-5，说明反向传播有bug。

梯度检查的注意事项：使用float64——float32的精度不够。使用简单的损失函数——不要加正则化或Dropout。在少数样本上检查——全数据集太慢。检查后关闭梯度检查——正式训练时不需要。

### 优化器的选择策略

SGD是最基本的优化器——W -= lr * dW。SGD的问题是在ravine（一个方向梯度大、另一个方向梯度小）地形中震荡严重。Momentum通过累积梯度方向缓解震荡——v = beta * v + dW，W -= lr * v。beta通常取0.9。

Adam结合了一阶矩（动量）和二阶矩（梯度平方的指数移动平均）。自适应学习率——参数的梯度方差大时学习率自动减小，梯度方差小时学习率自动增大。Adam的默认参数（lr=1e-3, beta1=0.9, beta2=0.999, epsilon=1e-8）在大多数任务上都work——这是Adam流行的原因。

但Adam有一些已知问题。Adam的收敛性在凸优化场景下不如SGD——因为Adam的自适应学习率可能不满足收敛条件。AMSGrad和AdaBelief是Adam的改进版本，修复了收敛性问题。在训练大模型时，通常先用Adam快速收敛，然后切换到SGD做精细调优——这就是"Adam warmup + SGD fine-tune"策略。

### 深度对训练的影响

增加网络深度不一定提升性能——深度网络更难训练。除了梯度消失，还有退化问题（Degradation Problem）——深层网络的训练误差比浅层网络更高。ResNet的残差连接解决了这个问题——但你的NumPy实现不需要残差连接，因为只有2到3层。

如果你尝试4层或更深的网络，会发现训练变得困难。解决方案：Batch Normalization（BN）——归一化每层的输入分布，使得训练更稳定。BN的公式：y = gamma * (x - mean) / sqrt(var + epsilon) + beta，其中gamma和beta是可学习参数。BN使得学习率可以设得更大，加速训练。

## 二、实现Transformer架构：Multi-Head Attention从公式到代码

### 核心训练目标

从零编码Transformer的核心组件，理解Self-Attention机制和位置编码（Positional Encoding）。这个实验训练三个核心能力：注意力机制的矩阵运算——理解Q/K/V的线性变换和注意力计算。位置编码——理解如何把位置信息注入无位置感知的注意力机制。残差连接和Layer Normalization——理解它们在稳定训练中的作用。

目标：实现Multi-Head Attention，完成简单的序列翻译任务。

### 关键实现步骤

**Q/K/V矩阵计算**：输入x经过三个线性变换得到Q = x @ W_Q、K = x @ W_K、V = x @ W_V。W_Q、W_K、W_V是可学习参数。在Multi-Head Attention中，Q/K/V被投影到h个头——每个头的维度d_k = d_model / h。

**Scaled Dot-Product Attention**：scores = Q @ K.T / sqrt(d_k)，attn = softmax(scores)，output = attn @ V。除以sqrt(d_k)是为了控制点积的方差——当d_k较大时，点积的值可能很大，使得softmax进入饱和区（梯度接近零）。

Scaled Dot-Product Attention的核心计算代码：

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    d_k = K.size(-1)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / d_k**0.5
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    attn_weights = F.softmax(scores, dim=-1)
    output = torch.matmul(attn_weights, V)
    return output, attn_weights
```

这段代码展示了注意力机制的核心——Q和K的点积衡量query和key的相关性，softmax归一化为权重，加权求和V得到输出。mask用于Decoder中防止"看到未来"——把未来位置的score设为负无穷，softmax后权重为零。

**Multi-Head拼接**：每个头独立计算Attention，输出concatenate后做线性投影。Multi-Head的价值在于不同的头可以关注不同类型的关系——一个头关注局部依赖，另一个头关注长距离依赖。

**Positional Encoding**：原始Transformer用正弦余弦编码——PE(pos, 2i) = sin(pos / 10000^(2i/d_model))，PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))。不同频率的正弦余弦编码不同粒度的位置信息——低频编码全局位置，高频编码局部位置。位置编码和词嵌入相加——不是concatenate，使得模型通过线性变换可以分离位置和语义信息。

**Feed-Forward Network和Layer Normalization**：FFN是两层线性变换加ReLU——FFN(x) = W2 @ ReLU(W1 @ x + b1) + b2。FFN对每个位置独立做非线性变换。LayerNorm对每个样本的每个位置做归一化——稳定训练，使得不同层的尺度一致。残差连接确保梯度可以直接传回——每个子层输出是Sublayer(x) + x，然后LayerNorm。

### 验收标准和踩坑点

验收标准：能完成简单的序列翻译任务（如反转序列、排序数字）、Attention权重可视化合理（不同的头关注不同位置）。

常见踩坑点：维度不匹配——Multi-Head的reshape和transpose容易搞错。Mask应用位置错误——mask应该在softmax之前应用，不是之后。梯度爆炸——Transformer深层网络容易梯度爆炸，需要梯度裁剪（Gradient Clipping）。

> Transformer的实现是"公式到代码"训练的巅峰。每个公式QK^T/sqrt(d_k) -> softmax -> V都对应几行代码。当你自己实现了这个映射，读论文中的公式描述就变成了"已经在脑中编译过"的代码。

### Multi-Head的工程实现

Multi-Head Attention的工程实现中，reshape和transpose是最容易出错的地方。原始输入x的shape是(batch, seq_len, d_model)。Q/K/V通过线性变换得到(batch, seq_len, d_model)。然后reshape为(batch, seq_len, n_heads, d_k)，transpose为(batch, n_heads, seq_len, d_k)——这样每个head独立做Attention。

计算完成后，输出shape是(batch, n_heads, seq_len, d_k)，transpose回(batch, seq_len, n_heads, d_k)，reshape为(batch, seq_len, d_model)，最后通过线性投影。这个"reshape-transpose-attention-transpose-reshape"的流程容易搞错维度——建议在每个步骤后打印shape做检查。

### Layer Normalization vs Batch Normalization

Transformer使用Layer Normalization（LN）而非Batch Normalization（BN）。LN对每个样本的每个位置独立做归一化——不受batch中其他样本影响。BN对整个batch的同一位置做归一化——依赖batch中的其他样本。

为什么Transformer用LN而非BN？因为序列长度可变——BN在变长序列上的统计量不稳定。LN对每个位置独立归一化，不受序列长度影响。此外，LN在推理时不需要运行时统计量——BN在推理时需要维护running mean/variance。

Pre-LN和Post-LN是两种LayerNorm放置策略。原始Transformer用Post-LN——LayerNorm在残差连接之后。Pre-LN——LayerNorm在残差连接之前。Pre-LN训练更稳定（梯度更平滑），但最终性能可能略低于Post-LN。GPT-2之后的大模型大多用Pre-LN——因为深层模型用Post-LN容易发散。

### Attention的复杂度和优化

Self-Attention的复杂度是O(n^2 * d)——n是序列长度，d是模型维度。n^2来自QK^T——每个位置和所有其他位置计算点积。当n很大（如长文档）时，内存和计算开销巨大。

Flash Attention是目前最流行的Attention优化。它不改变数学等价性——只是通过优化GPU内存访问模式加速。Flash Attention把QK^T和softmax(V)的计算分块（Tiling），在SRAM（片上高速缓存）中完成计算，避免在HBM（显存）中存储n^2的中间矩阵。速度提升2到4倍，内存从O(n^2)降到O(n)。

## 三、训练一个小型语言模型：BPE分词、预训练流程、文本生成

### 核心训练目标

从头训练一个字符级或BPE（Byte Pair Encoding，字节对编码）语言模型，理解预训练的完整流程。训练三个核心能力：分词——理解BPE算法和词表构建。预训练——理解CLM（Causal Language Model，因果语言模型）的训练循环。文本生成——理解不同采样策略的效果。

目标：在莎士比亚文本或简单中文语料上训练，生成连贯的句子。

### 关键实现步骤

**数据预处理**：文本清洗——统一编码为UTF-8、去除不可见字符、规范化标点。数据集划分——80%训练、10%验证、10%测试。对于语言模型，不需要标签——输入序列本身就是标签（预测下一个token）。

**BPE分词**：BPE的核心思想是反复合并最常见的相邻字符对。初始词表是所有单字符。统计训练语料中所有相邻token对的频率，把频率最高的对合并为一个新token，加入词表。重复直到词表大小达到目标。

BPE分词的核心算法代码：

```python
def train_bpe(text, vocab_size):
    # 初始化：每个字符是一个token
    tokens = list(text)
    vocab = set(tokens)
    while len(vocab) < vocab_size:
        # 统计相邻token对频率
        pairs = {}
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i+1])
            pairs[pair] = pairs.get(pair, 0) + 1
        if not pairs:
            break
        # 合并频率最高的对
        best = max(pairs, key=pairs.get)
        new_token = best[0] + best[1]
        vocab.add(new_token)
        # 在tokens中执行合并
        tokens = merge_tokens(tokens, best, new_token)
    return vocab
```

这段代码展示了BPE的核心——反复合并最高频的字符对。BPE的优势是它可以学习子词（Subword）——如"un"+"happy"——既不像字符级那样序列太长，也不像词级那样词表太大。GPT系列使用BPE，LLaMA使用SentencePiece（BPE的变体）。

**模型架构**：Embedding层把token id转换为向量。Transformer Decoder层——和Encoder类似但用Causal Mask防止看到未来token。输出投影——把隐藏状态投影到词表大小的logits。

**训练**：CLM损失——给定前t个token预测第t+1个token，损失是交叉熵。学习率调度——Warmup阶段线性增长，然后余弦衰减。梯度裁剪——torch.nn.utils.clip_grad_norm_，防止梯度爆炸。

**生成**：Greedy Decoding——每步选概率最大的token，简单但容易重复。Top-k Sampling——从概率最大的k个token中随机采样，增加多样性。Top-p Sampling（Nucleus Sampling）——从累积概率超过p的最小token集合中采样，比Top-k更自适应。

### 验收标准和踩坑点

验收标准：在莎士比亚文本上训练后，生成的文本语法正确、风格一致、不重复。loss稳定下降，验证集loss不过早上升（过拟合信号）。

常见踩坑点：BPE合并顺序错误——必须按训练时的合并顺序应用，否则编码不一致。OOM（Out of Memory）——减小batch size或序列长度，或使用梯度累积。生成模式化重复——增大温度（Temperature）、使用Top-p采样、加重复惩罚（Repetition Penalty）。

> 训练小型语言模型让你理解"大模型是怎么训练的"——只是规模不同，核心流程一样。当你手动跑过数据预处理、分词、训练、生成的全流程，你再看GPT-4的技术报告就能读懂每一个细节。

### 预训练的超参数调优

训练语言模型的超参数比训练分类模型敏感得多。学习率——太大loss爆炸，太小收敛慢。通常在1e-4到5e-4之间，用Warmup策略——前10%的步数线性增长到目标学习率，然后余弦衰减到零。

Batch size——语言模型通常用大batch（如64到256），但受GPU显存限制。梯度累积（Gradient Accumulation）可以在显存不足时模拟大batch——做多次前向反向累积梯度，然后一次性更新参数。

梯度裁剪（Gradient Clipping）是训练语言模型的标配——torch.nn.utils.clip_grad_norm_(model.parameters, max_norm=1.0)。梯度裁剪防止梯度爆炸——当梯度范数超过max_norm时按比例缩放。没有梯度裁剪，训练可能在某一步突然发散。

### 生成策略的深入理解

温度（Temperature）控制生成的随机性。logits = logits / temperature。温度低（如0.3）使分布更尖锐——生成更确定但可能重复。温度高（如1.5）使分布更平坦——生成更多样但可能不连贯。温度为1.0相当于不调整。

Top-k Sampling的问题：k是固定的，但不同上下文需要不同的k。在"今天天气很"后面，合理的下一个词可能只有几个（好、热、冷）。但在"我认为"后面，合理的下一个词可能有几十个。Top-p Sampling（Nucleus Sampling）通过动态选择k解决这个问题——选择累积概率超过p的最小token集合。p通常设为0.9。

重复惩罚（Repetition Penalty）通过降低已出现token的概率来避免重复——logits[tokens_seen] /= penalty。penalty通常设为1.1到1.3。重复惩罚对长文本生成特别重要——没有它，模型容易陷入"我说了什么什么什么什么"的循环。

### 训练数据的构建

数据质量决定模型质量。对于莎士比亚文本训练，需要：统一编码（UTF-8）、去除非文本字符（如HTML标签）、保留换行和标点（它们是语言结构的一部分）、按固定长度切分序列（如256或512 token）。

切分策略：直接截断——简单但可能截断在句子中间。按句号切分——保持句子完整但序列长度不一致。Packing——把多个短序列拼接到一个固定长度序列中，用attention mask区分。Packing是最高效的——不浪费任何token位置。

## 四、强化学习实验：DQN在OpenAI Gym中的实现

### 核心训练目标

在CartPole或Atari环境中训练DQN（Deep Q-Network，深度Q网络），理解强化学习的核心概念。训练三个核心能力：探索-利用平衡（Exploration-Exploitation Trade-off）——Epsilon-Greedy策略。值函数近似——用神经网络近似Q函数。经验回放和目标网络——稳定训练的两大技巧。

目标：CartPole-v1平均reward达到475以上（满分500）。

### 关键实现步骤

**Q-Network设计**：输入是状态（CartPole是4维——位置、速度、角度、角速度），输出是每个动作的Q值（CartPole是2维——向左或向右）。网络结构：全连接层(4, 128) -> ReLU -> 全连接层(128, 128) -> ReLU -> 全连接层(128, 2)。

**经验回放（Experience Replay）**：Replay Buffer存储转移(s, a, r, s', done)。训练时从Buffer中随机采样mini-batch。随机采样打破了数据的时间相关性——使得训练更像i.i.d.监督学习。Buffer大小通常为1万到100万。

**目标网络（Target Network）**：用两个结构相同但参数不同的网络——Q-Network（在线网络）和Target Network。Q-Network每步更新参数，Target Network每隔N步从Q-Network复制参数。Target Network用于计算TD Target——y = r + gamma * max_a' Q_target(s', a')。目标网络使得TD Target不随Q-Network变化而剧烈波动——稳定训练。

DQN的经验回放采样和目标网络更新核心代码：

```python
def train_step(self, batch_size):
    # 从Replay Buffer随机采样
    states, actions, rewards, next_states, dones =         self.replay_buffer.sample(batch_size)
    # 计算TD Target（用目标网络）
    with torch.no_grad():
        max_next_q = self.target_net(next_states).max(dim=1)[0]
        td_target = rewards + self.gamma * max_next_q * (1 - dones)
    # 计算当前Q值
    current_q = self.q_net(states).gather(1, actions.unsqueeze(1))
    # Huber Loss + 优化
    loss = F.huber_loss(current_q.squeeze(), td_target)
    self.optimizer.zero_grad()
    loss.backward()
    self.optimizer.step()
```

这段代码展示了DQN训练的核心——从Replay Buffer采样、用Target Network计算TD Target、用Huber Loss训练Q-Network。Huber Loss比MSE对异常值更鲁棒——当TD误差大时梯度是线性的而非二次的，防止Q值发散。

**Epsilon-Greedy探索**：以概率epsilon随机选动作（探索），以概率1-epsilon选Q值最大的动作（利用）。epsilon从1.0线性衰减到0.05——前期多探索，后期多利用。

### 验收标准和踩坑点

验收标准：CartPole-v1平均reward达到475以上、训练曲线稳定上升不震荡。

常见踩坑点：Q值过估计（Overestimation）——Q-Learning的max操作导致Q值系统性偏高，Double DQN通过解耦动作选择和动作评估解决。训练不稳定——学习率太大、Target Network更新太频繁、Replay Buffer太小。Replay Buffer采样效率——当Buffer很大时，重要样本可能很少被采到，Prioritized Experience Replay通过优先采样高TD误差的样本解决。

> 强化学习和监督学习的根本区别是"数据分布随策略变化"。监督学习的数据是固定的，RL的数据由agent的策略产生——策略变了，数据分布就变了。这个"移动的靶子"使得RL训练比监督学习困难得多。

### DQN的变体和改进

DQN有两个主要问题：Q值过估计和训练不稳定。后续工作针对这两个问题提出了多种改进。

Double DQN解耦动作选择和动作评估。原始DQN：y = r + gamma * max_a Q_target(s', a)。Double DQN：y = r + gamma * Q_target(s', argmax_a Q_online(s', a))。用在线网络选动作，用目标网络评估动作——减少max操作带来的过估计。

Dueling DQN把Q值分解为V(s)（状态价值）和A(s,a)（动作优势）。Q(s,a) = V(s) + A(s,a) - mean(A(s,a'))。这种分解使得在动作差别不大的状态中，V(s)可以直接学习——不需要通过Q值差异推断状态价值。

Rainbow DQN把DQN、Double DQN、Dueling DQN、Prioritized Experience Replay、Noisy Networks、Categorical DQN、Distributional RL七种改进组合在一起——在Atari上大幅超越原始DQN。Rainbow展示了"组合改进"的力量——每种改进单独有效，组合后效果倍增。

### 从DQN到Policy Gradient

DQN是Value-based方法——学习Q函数，间接得到策略。Policy-based方法直接学习策略——pi(a|s) = f(s; theta)。Policy Gradient的梯度：nabla J = E[nabla_theta log pi(a|s) * A(s,a)]，其中A(s,a)是优势函数（Advantage Function）。

Value-based和Policy-based各有优势。Value-based（如DQN）在离散动作空间中高效、样本利用率高。Policy-based（如REINFORCE）在连续动作空间中自然、可以学习随机策略。Actor-Critic结合两者——Actor学习策略，Critic学习值函数。

PPO（Proximal Policy Optimization，近端策略优化）是当前最流行的Policy-based算法。PPO通过裁剪目标函数限制策略更新幅度——L = min(ratio * A, clip(ratio, 1-epsilon, 1+epsilon) * A)。这个简单的裁剪使得训练稳定——不需要复杂的trust region计算。PPO是OpenAI的默认RL算法，也是RLHF第三步的标配。

### RL实验的可复现性

RL实验的可复现性比监督学习差得多。原因：随机种子影响很大——不同种子的训练曲线可能天差地别。环境版本——Gym的CartPole在不同版本中物理参数略有不同。网络初始化——不同初始化导致不同的训练动态。

提高RL可复现性的方法：运行多个种子（至少5个）报告均值和标准差。固定环境版本（用pip freeze记录版本）。记录完整的训练曲线——不只报告最终性能。开源代码和配置——让其他人能精确复现。

## 五、科研方法论实验室：文献综述、论文复现、开题报告

### 项目1：文献综述与批判性分析

文献综述不是"把30篇论文的摘要抄一遍"。好的综述是"画出研究领域的地图"——哪些问题已经被解决、哪些还在争论、哪些是空白。

关键步骤：文献检索——Google Scholar按引用量排序找经典论文，DBLP按时间排序找最新论文。分类框架设计——按问题类型、方法类型、时间线分类。对比维度确定——任务、数据集、指标、方法、性能、局限。批判性评价——不只是说"这篇论文做了什么"，而是说"这篇论文的不足是什么、未来方向是什么"。

产出物：一份5000字以上的文献综述报告，包含30+篇论文的对比分析表格和一张研究领域知识图谱。

### 文献检索的技巧

文献检索不是"在Google Scholar搜关键词"这么简单。系统化的检索方法：

滚雪球法（Snowballing）：找到一篇核心论文，看它的参考文献（向前滚）和引用它的论文（向后滚）。这种方法能快速找到同一研究线的所有重要论文。

综述先行法：先找该领域的Survey或Review论文。Survey已经帮你整理了文献地图——你在Survey的基础上补充最新工作。

关键词组合法：用多个关键词组合搜索。如"transformer" + "efficient" + "inference"比单独搜"transformer"精确得多。使用学术搜索的过滤功能——按年份、按会议/期刊过滤。

关注顶会顶刊：CS的顶会如ACL、EMNLP（NLP），CVPR、ICCV（CV），NeurIPS、ICML、ICLR（ML），OSDI、SOSP、NSDI（系统），SIGCOMM（网络），CRYPTO（密码学）。关注这些会议的接收论文列表是了解前沿的最佳方式。

### 文献综述的写作结构

好的文献综述有清晰的逻辑结构——不是按论文列表逐个介绍。常见结构：

按时间线——展示领域的演进脉络。适合发展成熟的领域。按方法分类——把论文按技术路线分组对比。适合方法多样的领域。按问题分类——把论文按解决的问题分组。适合应用驱动的领域。

每个部分的结构应该是："这个问题是什么 -> 已有的方法有哪些 -> 每种方法的优缺点 -> 未解决的问题是什么"。这种结构把文献"串成故事"而非"列成清单"。

### 项目2：论文复现实验

论文复现是科研的基本功。复现不是"把作者代码跑起来"——而是"根据论文描述从头实现"。

关键步骤：精读论文——理解每个设计决策。环境搭建——安装依赖、准备数据集。代码实现——根据论文描述写代码，遇到不清楚的地方先尝试自己的理解。结果对比——和论文报告的结果对比，分析差异。差异分析——差异来源可能是：未公开的实现细节、不同的随机种子、不同的超参数、不同的数据预处理。

产出物：复现代码 + 实验报告 + 差异分析。差异分析是最有价值的部分——它揭示了论文中"没说但很重要"的细节。这些细节往往是论文作者的经验知识——你通过复现"发现"了这些知识。

### 论文复现的常见差异来源

复现结果和原论文结果有差异是常态——完全一致几乎不可能。差异来源：

未公开的实现细节——论文不会写所有细节。如初始化方法、数据预处理的具体步骤、学习率调度的精确参数。这些细节通常在作者代码中才能找到——如果作者开源了代码。

随机性——随机种子影响初始化、数据顺序、Dropout模式。不同种子导致的性能差异可能达到1-2%。这就是为什么论文通常报告多个种子的均值和标准差。

数据集版本——数据集会更新。如ImageNet在2012年发布后有多次修正。不同版本的数据集导致结果不可直接比较。

超参数调优——原论文可能做了大量超参数搜索，但没有报告搜索范围。你用的超参数可能不在最优区间。

硬件差异——不同GPU型号的浮点计算精度略有差异。大batch训练时这种差异可能被放大。

### 从复现到改进

复现的终极目标不是"和原论文一致"——而是"理解原论文的局限并改进"。当你复现一篇论文时，记录你遇到的困难和发现的局限——这些就是改进的起点。

改进的路径：换更好的方法（如把CNN换为Transformer）、换更好的特征（如加入预训练表示）、换更好的训练策略（如加入数据增强）。每一步改进都需要实验验证——和原论文的baseline做公平对比。

### 项目3：开题报告撰写与答辩

开题报告是博士研究的"路标"。它不是形式——而是迫使你把模糊的研究想法变成具体的计划。

结构：问题定义（Problem Definition）——你要解决什么问题？为什么这个问题重要？相关工作（Related Work）——已有的方法有什么不足？你的方法有什么新意？研究方法（Methodology）——你打算怎么解决这个问题？预期贡献（Expected Contribution）——你的方法如果成功，贡献是什么？时间规划（Timeline）——每个阶段做什么？

产出物：15-20页的开题报告 + 20分钟答辩PPT。答辩时被问到的问题通常是：这个问题为什么重要？你的方法和已有工作的区别在哪？如果方法不work怎么办？你的Plan B是什么？——这些问题迫使你思考研究的风险和备选方案。

### 开题答辩的常见问题

开题答辩中委员会通常问的问题：

"这个问题的核心挑战是什么？"——测试你对问题的理解深度。如果只能说"很难"，说明你没真正理解。

"你的方法和XX工作的区别在哪？"——测试你对相关工作的了解。如果答不上来，说明文献综述不够。

"如果方法不work怎么办？"——测试你的风险管理。好的回答应该有Plan B和Plan C——"如果方法A不work，我会尝试方法B，因为...如果B也不work，我会从另一个角度...因为..."

"你的贡献是什么？"——测试你对研究价值的判断。贡献应该是具体的——"提出了一种新方法"不够，应该是"提出了一种基于XX的新方法，解决了XX问题，在XX数据集上提升了XX%"。

"你打算怎么评估？"——测试你的实验设计。需要明确的baseline、数据集、评估指标、消融实验。

### 开题报告的时间规划

时间规划不是"写个甘特图"——而是展示你对研究风险的认知。好的时间规划应该包含：

里程碑（Milestone）——每3到4个月一个里程碑，如"完成baseline复现"、"完成方法实现"、"完成主实验"、"完成消融和分析"。每个里程碑有明确的验收标准。

风险点和应对——"方法可能在XX情况下不work，如果发生我会..."。识别风险比假装没有风险更有说服力。

缓冲时间——预留1到2个月的缓冲。研究总会遇到意料之外的困难——实验不work、数据集有问题、审稿意见需要大修。没有缓冲的时间规划是不现实的。

| 项目 | 训练重点 | 产出物 | 评估标准 |
|------|---------|--------|---------|
| 文献综述 | 学术阅读与写作 | 5000字综述报告 | 覆盖度+批判深度 |
| 论文复现 | 可复现性意识 | 代码+实验报告 | 结果接近度+差异分析 |
| 开题报告 | 研究规划与表达 | 15-20页报告+PPT | 问题清晰度+方法新意 |

> 科研方法论的训练不是"学游泳"而是"学游泳姿势"。文献综述教你怎么读，论文复现教你怎么做，开题报告教你怎么规划。这三项能力是博士研究的底层操作系统——具体的研究技能（写代码、跑实验）是应用层，底层操作系统决定了你能走多远。

## 六、实验室轮转策略：2-3个轮转怎么选

### 第一轮转（第1学期）：与导师主线方向一致

第一个轮转选和导师主线方向一致的实验室。目标是快速进入研究状态——学习实验室的方法论、工具链、工作节奏。

这一轮转不要追求"大创新"——而是追求"能做事"。读导师推荐的10篇论文、学会实验室的代码框架、完成一个小实验。产出物：一份文献综述或一个小实验结果。

### 第二轮转（第2学期）：跨子领域实验室

第二个轮转选跨子领域实验室——做ML的去系统组，做系统的去ML组。目标是寻找交叉创新点。

跨领域轮转的价值在于"视角转换"。当你带着ML的视角看系统问题，可能发现"这个问题可以用ML解决"；当你带着系统的视角看ML问题，可能发现"这个ML训练瓶颈本质是系统效率问题"。很多 impactful 的研究来自跨领域视角——如MLSys（ML系统）就是ML和系统的交叉。

产出物：跨领域合作想法、可能的初步实验。

### 第三轮转（第3学期）：潜在合作导师

第三个轮转选潜在的合作导师。目标是确定最终研究方向和合作模式。

这一轮转需要"认真"——因为你大概率会在这个方向上工作3到4年。判断标准：方向是否有前景（未来5年还有研究价值）、导师风格是否匹配（放养还是微操）、实验室氛围是否舒适（同学之间是否互助）。

产出物：确定研究方向、开始系统性研究。

### 从轮转到论文

轮转实验转化为论文的路径：轮转实验 → 整理结果 → 提炼发现 → 设计完整实验 → 撰写论文 → 投稿。这个过程通常需要6到12个月——轮转期间的"小实验"变成"完整论文"需要大量的补充实验和打磨。

| 轮转 | 时间 | 目标 | 产出 | 转化策略 |
|------|------|------|------|---------|
| 第一轮转 | 第1学期 | 进入研究状态 | 文献综述/小实验 | 为后续研究打基础 |
| 第二轮转 | 第2学期 | 跨领域视角 | 合作想法/初步实验 | 发展为交叉方向论文 |
| 第三轮转 | 第3学期 | 确定研究方向 | 系统性研究开始 | 直接转化为博士主线 |

> 轮转是博士研究的"试婚"。你不在轮转中确定"和谁过一辈子"——而是通过轮转了解"有哪些选择、每个选择的利弊"。不要急于定方向——前两个学期的轮转是你最自由的探索时间。一旦定了方向，你就进入了"深耕"模式，跨领域的机会成本会越来越高。

### 跨领域轮转的具体策略

跨领域轮转需要"带着问题去"。漫无目的的轮转只是浪费时间——你应该带着一个具体问题："ML训练中的系统瓶颈是什么？"或"系统设计中的ML问题有哪些？"

在系统组做ML的人，关注的是ML训练的效率——如分布式训练的通信优化、GPU内存管理、训练流水线并行。在ML组做系统的人，关注的是系统设计的智能化——如用ML预测查询选择最优执行计划、用ML做数据库的自适应调优。

跨领域轮转的最大收获不是"学了另一领域的知识"——而是"学会了另一领域的思维方式"。ML研究者习惯于"实验驱动"——先跑实验再看结果。系统研究者习惯于"设计驱动"——先做设计再验证。两种思维方式都有价值——能在两种模式间切换的研究者更有创新能力。

### 轮转中的人际关系

轮转不只是学术探索——也是人际关系建设。每个轮转的实验室都可能成为你未来的合作者。

在轮转中建立良好关系的方法：主动参加组会并提问——展示你的参与度。帮助师兄师姐做实验——建立互助关系。和导师定期1对1交流——展示你的思考深度。轮转结束时做一次正式汇报——留下好印象。

这些关系可能在未来产生意想不到的价值。怕浪猫的第二个轮转在系统组，当时帮助师兄做了一个分布式训练的实验。两年后写论文时，师兄已经是该领域的专家，提供了关键的反馈和合作——这篇论文最终发在了顶会。

### 从ML实验到研究论文

和系统实验一样，ML实验也是研究的起点。当你做完反向传播实验后，可以问：不同的初始化方法对训练有什么影响？当你做完Transformer实验后，可以问：Attention的哪些头最重要？能否剪枝？当你做完小型语言模型实验后，可以问：数据量和模型大小的关系是什么？

这些问题是ML研究论文的雏形。从实验到论文的路径：发现有趣现象 → 设计系统实验验证 → 和已有工作对比 → 提出解释或新方法 → 撰写论文。ML研究的特殊性在于"实验是核心"——很多ML论文没有理论证明，但通过精心设计的实验说服读者。

### ML实验的版本管理

ML实验比系统实验更需要版本管理——因为ML实验涉及大量超参数配置、数据集版本、模型检查点。建议使用专门的实验管理工具。

MLflow或Weights & Biases（W&B）可以追踪每次实验的超参数、指标、模型文件。每条实验记录包含：超参数（学习率、batch size、模型结构）、环境信息（GPU型号、库版本）、训练日志（loss曲线、指标变化）、模型检查点。

实验管理的核心原则是"可追溯"——六个月后你还能知道某次实验用了什么配置、得到了什么结果。没有实验管理的ML研究是"不可复现的炼丹"——你自己都不知道上次最好的结果是怎么来的。好的实验管理工具让你把精力放在"设计实验和解读结果"上，而非"翻找三个月前的某次运行记录"。这对博士研究的效率提升是决定性的。ML实验中的版本管理就像系统实验中的Git——看似麻烦，实则是你最可靠的复盘工具，让你每一次实验都有迹可循，而不是在无数次训练中迷失方向，白白浪费宝贵的博士时光。


## 系列进度与下章预告

这篇文章是「CS博士通关路」系列的第十篇。4个ML实验项目、3个科研方法论训练、实验室轮转策略——这些是怕浪猫从调参工程师成长为研究者的路径。

收藏这篇文章，作为你ML实验和科研训练的参考。当你在训练模型或写开题报告时，回查这里的流程和检查清单。

在评论区告诉怕浪猫：你的第一个ML实验是什么？遇到了什么坑？

**系列进度 10/12**

下一章，怕浪猫聊聊博士期间除了做研究还能做什么。从顶会发表到工业实习，从跨学科合作到学术服务——博士不只在实验室里。

关注我，追更不迷路。

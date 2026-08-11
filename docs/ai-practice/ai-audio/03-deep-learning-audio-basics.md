# 第 3 章：深度学习基础与音频建模入门

> **系列文章：《语音与音乐的机器之魂》**
> 本章建立音频 AI 的技术框架，介绍神经网络基础、音频建模的特殊挑战，以及核心架构谱系。

---

## 1. 神经网络基础回顾

### 1.1 核心组件

| 组件 | 作用 | 在音频中的应用 |
|------|------|----------------|
| 全连接层（FC） | 通用变换 | 特征映射、分类头 |
| 卷积层（Conv） | 局部特征提取 | 频谱处理、声码器 |
| 循环层（RNN/LSTM/GRU） | 时序建模 | 早期 TTS/ASR |
| 注意力机制（Attention） | 长程依赖 | Transformer 核心 |
| Transformer | 自注意力 + 位置编码 | 当前主流架构 |

### 1.2 卷积在音频中的使用

音频频谱可以视为二维图像（时间 × 频率），因此卷积操作天然适用：

- **1D 卷积**：处理波形或单维特征序列
- **2D 卷积**：处理频谱图（类似图像）
- **因果卷积**：不使用未来信息，用于流式推理
- **膨胀卷积**：感受野指数增长，WaveNet 的核心

```python
# 膨胀因果卷积示例
import torch.nn as nn

class DilatedCausalConv1d(nn.Module):
    def __init__(self, channels, kernel_size=3, dilation=1):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(channels, channels, kernel_size,
                              padding=self.padding, dilation=dilation)
    
    def forward(self, x):
        out = self.conv(x)
        return out[:, :, :-self.padding]  # 因果：丢弃右侧 padding
```

### 1.3 Transformer 与注意力

Transformer 已成为语音模型的主流架构：

**自注意力机制：**
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

**多头注意力** 允许模型同时关注不同位置的不同方面：
- Head 1 可能关注相邻音素的协同
- Head 2 可能关注长程韵律模式
- Head 3 可能关注说话人特征

**位置编码** 弥补 Transformer 缺失的时序信息：
- 正弦编码（原始 Transformer）
- 相对位置编码（Music Transformer）
- RoPE（旋转位置编码，现代 LLM 标准）
- ALiBi（线性偏置注意力）

### 1.4 关键训练概念

**损失函数：**
| 损失 | 用途 | 说明 |
|------|------|------|
| MSE | 回归 | Mel 频谱重建 |
| Cross-Entropy | 分类 | 音频 token 预测 |
| CTC | 序列对齐 | ASR 无对齐训练 |
| Adversarial | GAN | 声码器对抗训练 |
| Contrastive | 自监督 | wav2vec 对比学习 |

**优化器：**
- **Adam/AdamW**：最通用，自适应学习率
- **LAMB**：大 batch 训练
- 学习率调度：Warmup + Cosine Decay 是标准配置

## 2. 音频建模的特殊挑战

### 2.1 序列长度问题

这是音频 AI 最核心的工程挑战：

| 数据类型 | 1 秒数据量 | 3 分钟数据量 |
|----------|-----------|-------------|
| 文本 | ~5 tokens | ~900 tokens |
| 16kHz 语音波形 | 16,000 点 | 2,880,000 点 |
| 24kHz 音频波形 | 24,000 点 | 4,320,000 点 |
| 80 维 Mel 频谱 | ~86 帧 | ~15,480 帧 |

直接建模原始波形的计算量是文本的数千倍。

**解决方案：**

#### 多尺度建模

WaveNet 使用膨胀卷积实现指数增长的感受野：

```
Layer 0: dilation=1,  感受野=2
Layer 1: dilation=2,  感受野=4
Layer 2: dilation=4,  感受野=8
Layer 3: dilation=8,  感受野=16
...
Layer 9: dilation=512, 感受野=1024
```

10 层即可覆盖约 46ms（@24kHz），实际使用 30+ 层。

#### 压缩表示

将波形压缩为更短的表示：

| 表示 | 压缩率 | 说明 |
|------|--------|------|
| Mel 频谱 | ~200× | 24kHz → 80维×86帧/秒 |
| EnCodec | ~320× | 24kHz → 75 tokens/秒 |
| DAC | ~512× | 更高压缩率 |
| WavTokenizer | ~640× | 单码本高压缩 |

#### 两阶段生成

```
文本 → 声学模型(生成压缩表示) → 声码器(生成波形)
      ~86帧/秒                    → 24000点/秒
```

### 2.2 长程依赖

音乐有明确的结构（主歌-副歌-桥段），需要模型理解数十秒甚至几分钟的上下文。

**Transformer 的 O(n²) 问题：**

对于 3 分钟音乐（@75 tokens/s = 13,500 tokens），自注意力矩阵有 1.8 亿个元素。

**解决方案：**

| 方法 | 复杂度 | 说明 |
|------|--------|------|
| 全注意力 | O(n²) | 质量最好，无法扩展 |
| 稀疏注意力 | O(n·√n) | 只关注局部窗口 + 全局锚点 |
| 线性注意力 | O(n) | Performer/Linear Attention |
| 状态空间模型 | O(n) | Mamba/S4，并行训练+线性推理 |
| 层次化生成 | — | 先生成结构，再填充细节 |

### 2.3 多条件控制

音乐生成需同时控制：风格、乐器、节拍、调性、情感、歌词等。

**条件注入方法：**

```python
# 方法1: 交叉注意力（Cross-Attention）
# 文本条件通过 K, V 注入
class CrossAttention(nn.Module):
    def forward(self, x, cond):
        Q = self.q(x)          # 音频特征
        K = self.k(cond)       # 文本条件
        V = self.v(cond)
        return attention(Q, K, V)

# 方法2: AdaLN（自适应层归一化）
class AdaLN(nn.Module):
    def forward(self, x, cond):
        scale, shift = self.proj(cond).chunk(2, dim=-1)
        return x * (1 + scale) + shift

# 方法3: 分类器自由引导（Classifier-Free Guidance）
# 训练时随机丢弃条件，推理时混合条件和无条件预测
def cfg_score(cond_pred, uncond_pred, w=3.0):
    return uncond_pred + w * (cond_pred - uncond_pred)
```

## 3. 音频 AI 的核心架构谱系

```
                    ┌── 自回归（Autoregressive）
                    │     ├── WaveNet（波形级）
                    │     ├── Tacotron（频谱级）
                    │     ├── VALL-E（token 级）
                    │     └── MusicGen（token 级）
                    │
       ┌─ 离散 token ─┤
       │              └── 非自回归（Non-autoregressive）
       │                    ├── FastSpeech（时长预测器）
       │                    └── NaturalSpeech
       │
音频模型┤
       │              ┌── GAN 系
       │              │     ├── MelGAN
       │              │     ├── HiFi-GAN ← 事实标准
       │              │     └── BigVGAN
       │              │
       └─ 连续波形 ───┼── 扩散模型
                      │     ├── WaveGrad
                      │     └── DiffSinger
                      │
                      ├── 流模型
                      │     ├── WaveGlow
                      │     ├── Voicebox（Flow Matching）
                      │     └── F5-TTS
                      │
                      └── VAE 系
                            ├── VITS
                            └── NaturalSpeech 2
```

### 3.1 自回归 vs 非自回归

| 维度 | 自回归（AR） | 非自回归（NAR） |
|------|-------------|-----------------|
| 生成方式 | 逐 token 生成 | 一次前向全部生成 |
| 质量 | 通常更高 | 略低但接近 |
| 速度 | 慢（O(n) 步） | 快（O(1) 步） |
| 多样性 | 高（随机采样） | 低 |
| 典型模型 | WaveNet, VALL-E, MusicGen | FastSpeech, NaturalSpeech |

### 3.2 生成范式对比

#### GAN 范式

```
生成器 G: 条件 → 假音频
判别器 D: 区分真假音频
对抗训练: G 尽量骗过 D，D 尽量识别 G
```

优点：速度快  
缺点：训练不稳定，模式坍缩

#### 扩散范式

```
训练: 逐步加噪 (前向过程)
生成: 逐步去噪 (反向过程)
```

优点：质量高，训练稳定  
缺点：采样慢（需多步迭代）

#### 流匹配范式

```
训练: 学习从噪声分布到数据分布的向量场
生成: 沿向量场积分
```

优点：比扩散更高效，训练更稳定  
缺点：理论较新，生态尚在发展

## 4. 离散化与音频 Token 化

### 4.1 为什么需要音频 Token

大语言模型（LLM）的成功证明：**离散 token + 自回归训练**是一条极具扩展性的路径。将音频离散化后，可以直接利用 LLM 的训练范式和架构。

```
文本: "你好" → [nǐ, hǎo] → LLM → [回复] → 文本
音频: 波形 → 音频Tokenizer → [token序列] → LLM → [token序列] → 解码 → 波形
```

### 4.2 音频 Tokenizer 对比

| Tokenizer | 压缩率 | 音质 | 码本数 | 代表应用 |
|-----------|--------|------|--------|----------|
| SoundStream | ~320× | 高 | 多层 | AudioLM |
| EnCodec | ~320× | 高 | 8层 | MusicGen, VALL-E |
| DAC | ~512× | 极高 | 9层 | 高保真音频 |
| WavTokenizer | ~640× | 高 | 1层 | 语音 LLM |
| SpeechTokenizer | ~1000× | 中 | 多层 | 语音理解 |
| TiCodec | ~400× | 高 | 内容/音色分离 | 语音转换 |

### 4.3 残差矢量量化（RVQ）详解

EnCodec 等使用多层码本逐步量化残差：

```python
# RVQ 伪代码
def rvq_encode(x, codebooks):
    """x: [B, D], codebooks: list of [K, D]"""
    tokens = []
    residual = x
    for cb in codebooks:
        # 找到最近的码字
        dist = torch.cdist(residual.unsqueeze(1), cb.unsqueeze(0))
        idx = dist.argmin(dim=-1)  # [B]
        tokens.append(idx)
        # 更新残差
        residual = residual - cb[idx]
    return torch.stack(tokens, dim=0)  # [n_codebooks, B]

def rvq_decode(tokens, codebooks):
    return sum(cb[idx] for cb, idx in zip(codebooks, tokens))
```

**层数的影响：**
- 第 1 层码本：捕捉最显著的声学信息（如语音内容）
- 第 2-4 层：补充音色和细节
- 第 5-8 层：精细化的高频信息

**层数越多 → 音质越好 → 但序列越长 → 生成越慢**

### 4.4 码本延迟模式

为了解决多层码本导致序列过长的问题，MusicGen 引入了**延迟交错模式**：

```
原始排列（4层码本，每层4个token）:
  Layer 0: [A0, A1, A2, A3]
  Layer 1: [B0, B1, B2, B3]
  Layer 2: [C0, C1, C2, C3]
  Layer 3: [D0, D1, D2, D3]

延迟排列:
  时间步 0: [A0]
  时间步 1: [A1, B0]
  时间步 2: [A2, B1, C0]
  时间步 3: [A3, B2, C1, D0]
  时间步 4: [    B3, C2, D1]
  ...
```

这样在每个时间步只需生成 1-4 个 token，有效减少自回归步数。

## 5. 自监督学习在音频中的应用

### 5.1 动机

标注数据昂贵，未标注音频海量（YouTube、播客等）。自监督学习利用数据本身作为监督信号。

### 5.2 wav2vec 2.0 方法

```
原始波形 → 卷积特征提取 → 量化目标
                ↓
         Transformer 编码器
                ↓
         掩码预测（对比学习）
```

**训练过程：**
1. 将波形通过卷积层提取特征
2. 对部分时间步做掩码
3. Transformer 编码未掩码的特征
4. 对比学习：掩码位置的表示应接近对应的量化目标（正例），远离其他目标（负例）

**微调：**
- 在少量标注数据（如 10 分钟 LibriSpeech）上微调
- 加 CTC 损失做语音识别
- 加分类头做说话人识别、情感识别等

### 5.3 HuBERT

HuBERT（Hidden-Unit BERT）使用迭代聚类：

```
1. 对音频特征做 k-means 聚类 → 伪标签
2. 用伪标签训练 Transformer（掩码预测）
3. 用训练好的 Transformer 提取新特征
4. 回到步骤 1，迭代
```

HuBERT 的语音表示质量极高，广泛用于下游任务。

### 5.4 自监督在音乐中的应用

- **MERT**：音乐理解的自监督预训练
- **Jukebox milestone**：利用 Jukebox 的内部表示做下游任务
- **CLAP**：对比学习对齐文本和音频

## 6. 本章小结

本章建立了音频 AI 的完整技术框架：

1. **核心挑战**：序列长度、长程依赖、多条件控制
2. **架构谱系**：自回归 vs 非自回归、离散 vs 连续、GAN/扩散/流/VAE
3. **音频 Token 化**：将音频纳入 LLM 范式的关键桥梁
4. **自监督学习**：减少标注依赖，利用海量未标注数据

后续章节将在这个框架内深入每个方向，从 TTS 到 ASR 到音乐生成，逐步展开。

---

> **上一章**：[第 2 章：AI 语音技术发展简史](./02-ai-speech-history.md)
>
> **下一章**：[第 4 章：语音合成（TTS）核心原理](./04-tts-core-principles.md)

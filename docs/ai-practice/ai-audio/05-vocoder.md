---
sidebar_position: 5
---

# 第 5 章：声码器（Vocoder）——从特征到波形

> **系列文章：《语音与音乐的机器之魂》**
> 声码器是 TTS 系统的"最后一公里"——将声学特征转换为可听的音频波形。本章梳理从 Griffin-Lim 到 BigVGAN 的完整技术谱系。

---

## 1. 声码器的角色

```
声学模型输出: Mel 频谱 (80维 × T帧)
         ↓
      声码器 (Vocoder)
         ↓
音频波形 (1维 × 22050 采样点/秒)
```

声码器需要解决的核心问题：**从低维度的频谱特征重建高维度的波形信号**，特别是恢复相位信息。

## 2. 经典声码器

### 2.1 Griffin-Lim 算法

无需训练，从幅度谱通过迭代估计相位：

```python
def griffin_lim(magnitude_spectrogram, n_iter=30):
    """从幅度谱重建波形"""
    # 初始化随机相位
    phase = random_phase(magnitude_spectrogram.shape)
    for _ in range(n_iter):
        complex_spec = magnitude * exp(1j * phase)
        waveform = istft(complex_spec)
        estimated_spec = stft(waveform)
        phase = angle(estimated_spec)
    return waveform
```

| 优点 | 缺点 |
|------|------|
| 零训练成本 | 质量较差 |
| 无需 GPU | 有金属感 |
| 确定性输出 | 缺少细节 |

**适用场景：** 快速原型、基线对比

### 2.2 WORLD 声码器

用于歌声合成和语音转换，提取三个参数：

```
音频 → F0（基频）
     → 频谱包络（SP）
     → 非周期信号（AP）
```

- 精确的 F0 提取（适合歌唱）
- 可编辑音高和音色
- 实时性能良好
- 缺点：参数提取不完美时有"电音"

## 3. 神经声码器

### 3.1 WaveNet（2016）——里程碑

DeepMind 的 WaveNet 是第一个高质量直接波形生成模型。

**架构：**

```
条件(Mel) → 因果膨胀卷积堆叠(30+层) → 1×1 Conv → Softmax → 采样
                                    → 门控激活单元
```

**膨胀卷积：**

```
dilation=1: ● ● ● ● ● ● ● ●  (相邻)
dilation=2: ●   ●   ●   ●    (隔1)
dilation=4: ●       ●         (隔3)
dilation=8: ●               ●  (隔7)

→ 4层即可覆盖16个采样点的感受野
→ 10层覆盖1024个采样点
```

**μ-law 量化：** 16-bit → 8-bit（256类），非线性量化对小信号更敏感。

**致命问题：** 自回归生成极慢。1秒音频（22050个采样点）需要22050次前向传播，GPU上需要数分钟。

### 3.2 并行声码器

为解决 WaveNet 速度问题：

#### Parallel WaveNet（2017）

- **蒸馏 + 流模型**：学生模型并行生成，从自回归教师模型学习
- Google 在 Pixel 手机上部署

#### WaveGlow（2018）

基于标准化流（Glow）：

```
Mel → 12层可逆变换 → 波形
```

- 可逆：训练时音频→隐变量，推理时隐变量→音频
- 并行生成，速度快
- 缺点：模型大，显存消耗高

### 3.3 GAN 声码器——当前主流

GAN 类声码器在速度和质量之间取得了最佳平衡。

#### MelGAN（2019）

轻量级生成器：

```
Mel → [上采样8×] → [上采样8×] → [上采样4×] → [上采样2×] → 波形
       每级配 ResBlock 堆叠
```

- 判别器：多尺度判别器（MSD）
- 速度快，适合端侧
- 质量中等，细节不够

#### HiFi-GAN（2020）——事实标准

**当前最广泛使用的声码器**，在 HiFi-GAN 之上叠加 VITS/TTS 的系统极多。

**生成器：**

```
Mel → 上采样(4×) → 上采样(4×) → 上采样(2×) → 上采样(2×) → Conv1×1 → 波形
       ↑           ↑           ↑           ↑
    逆膨胀卷积   逆膨胀卷积   逆膨胀卷积   逆膨胀卷积
    块×3        块×3        块×2        块×2
```

**判别器：**

1. **多周期判别器（MPD）**：将波形重塑为不同周期长度的2D矩阵，做2D卷积判别
   - 周期 [2, 3, 5, 7, 11]
   - 捕捉不同周期性的语音特征

2. **多尺度判别器（MSD）**：在不同尺度上判别波形
   - 捕捉全局结构

**损失函数：**

```python
loss = (
    λ_adv * adversarial_loss       # 对抗损失
  + λ_fm * feature_matching_loss   # 特征匹配
  + λ_mel * mel_loss               # Mel 重建
)
```

**HiFi-GAN 配置：**

| 配置 | 速度 | 质量 | 参数量 |
|------|------|------|--------|
| V1 (标准) | ~50× 实时 | 高 | 14M |
| V2 (通用) | ~20× 实时 | 更高 | 30M |
| V3 (轻量) | ~100× 实时 | 中 | 1.5M |

#### BigVGAN（2022）

在 HiFi-GAN 基础上的增强：

- **更大的模型**：更多通道、更多层
- **Snake activation**：对周期信号更友好的激活函数
  ```
  snake(x) = x + (1/α) * sin²(αx)
  ```
- 引入 anti-aliased representation（抗混叠）
- 质量进一步提升，特别是高频和瞬态

### 3.4 扩散声码器

#### WaveGrad（2020）

```
训练：音频 → 逐步加噪 → 学习去噪方向
生成：噪声 → 逐步去噪 → 波形
```

- 质量极高
- 速度慢（需多步迭代）
- 适合离线高质量场景

### 3.5 声码器全面对比

| 声码器 | 类型 | 速度 | 质量 | 显存 | 训练难度 | 场景 |
|--------|------|------|------|------|----------|------|
| Griffin-Lim | 无训练 | 极快 | ⭐⭐ | 极低 | — | 基线 |
| WORLD | DSP | 极快 | ⭐⭐⭐ | 低 | — | 歌声 |
| WaveNet | AR | ⭐(极慢) | ⭐⭐⭐⭐⭐ | 低 | 中 | 离线 |
| WaveGlow | Flow | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 高 | 中 | GPU |
| MelGAN | GAN | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 低 | 中 | 端侧 |
| HiFi-GAN | GAN | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中 | 低 | **通用首选** |
| BigVGAN | GAN | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | 中 | 高质量 |
| WaveGrad | Diffusion | ⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | 中 | 研究 |

## 4. 声码器的工程选择

### 4.1 决策树

```
你的需求是什么？

├─ 需要实时生成？
│   ├─ GPU 可用 → HiFi-GAN V1
│   └─ 仅 CPU → MelGAN / HiFi-GAN V3
│
├─ 需要极致质量？
│   ├─ 可接受慢 → BigVGAN / WaveGrad
│   └─ 需要快 → BigVGAN (减小步数)
│
├─ 歌声合成？
│   ├─ 需要可编辑 F0 → WORLD + 神经后处理
│   └─ 不需要 → HiFi-GAN + snake activation
│
├─ 端侧部署？
│   └─ MelGAN 轻量版 / HiFi-GAN V3 量化
│
└─ 快速原型？
    └─ Griffin-Lim（零训练）
```

### 4.2 训练自己的声码器

```yaml
# HiFi-GAN 训练配置示例
train:
  audio:
    sample_rate: 22050
    n_fft: 1024
    hop_length: 256
    win_length: 1024
    n_mels: 80
    fmin: 0
    fmax: 8000
  
  model:
    generator:
      upsample_rates: [8, 8, 2, 2]  # 总上采样 = 256 = hop_length
      upsample_kernel_sizes: [16, 16, 4, 4]
      resblock_kernel_sizes: [3, 7, 11]
      resblock_dilation_sizes: [[1,3,5], [1,3,5], [1,3,5]]
    
    discriminators:
      periods: [2, 3, 5, 7, 11]
      multi_scale: [1, 2, 4]
  
  training:
    batch_size: 16
    lr: 2e-4
    adam_b1: 0.8
    adam_b2: 0.99
    lr_decay: 0.999
    steps: 500000+
```

关键注意：
- 上采样率乘积必须等于 hop_length
- 需要**足够多样**的训练数据（多说话人优于单说话人）
- 判别器学习率通常低于生成器

## 5. 前沿趋势

### 5.1 统一声码器

传统声码器需为不同采样率/配置单独训练。统一声码器支持任意配置：

- **EnCodec解码器**：直接从音频 Token 解码
- **Universal HiFi-GAN**：多采样率统一模型

### 5.2 基于扩散的实时声码器

通过一致性模型等加速扩散采样：

```
传统扩散：1000步 → 5秒
一致性模型：1-4步 → 0.1秒
```

### 5.3 端到端融合

VITS 等模型已经将声码器与声学模型融合。未来趋势是**完全端到端**——从文本直接到波形，不再有显式的声码器模块。

## 6. 本章小结

声码器经历了三个阶段：

1. **算法重建**（Griffin-Lim, WORLD）：无训练，质量有限
2. **自回归神经**（WaveNet）：质量极高，速度极慢
3. **并行神经**（GAN/Flow/Diffusion）：速度质量兼顾

**HiFi-GAN 是当前的事实标准**，在绝大多数 TTS 系统中作为声码器使用。选择声码器本质上是速度/质量/资源的三角权衡。

---

> **上一章**：[第 4 章：语音合成（TTS）核心原理](./04-tts-core-principles.md)
>
> **下一章**：[第 6 章：语音识别（ASR）与语音理解](./06-asr-speech-understanding.md)

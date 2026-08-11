# 第 14 章：音频级音乐生成——从 WaveNet 到 MusicGen

> **系列文章：《语音与音乐的机器之魂》**
> 2023 年，一段 AI 生成的音乐在短视频平台爆火。本章梳理直接从音频生成音乐的完整技术谱系。

---

## 1. 直接音频生成的挑战

```
3 分钟音乐 = 4,320,000 采样点（@24kHz）
          = 13,500 EnCodec Token（@75Hz, 4层码本）
          ≈ 3-4 倍文本 LLM 的上下文长度
```

核心挑战：
- 序列极长（数百万采样点）
- 需同时建模局部音色和全局结构
- 计算资源需求巨大

## 2. 里程碑模型

### 2.1 WaveNet 用于音乐（2016）

```
类别标签（乐器/风格）→ 条件 → WaveNet → 逐采样点生成
```

- 证明直接音频生成可行
- 质量尚可但速度极慢
- 仅能生成短片段

### 2.2 SampleRNN（2017）

层次化 RNN 处理长音频：

```
Tier 1 (粗粒度): 处理低分辨率音频 → 全局结构
Tier 2 (中粒度): 细化中频细节
Tier 3 (细粒度): 生成原始采样点
```

多尺度建模的思想影响了后续很多工作。

### 2.3 Jukebox（OpenAI, 2020）

**第一个能生成完整歌曲（含人声）的模型。**

```
架构:
  文本（歌词/描述）→ CLAP 文本编码器
                         ↓
  原始音频 → VQ-VAE (3层) → 离散 Token
    ↓                         ↓
  层3 (最低分辨率) → 自回归 Transformer → 生成 Token
    ↓                         ↓
  层2 → 自回归 Transformer → 生成 Token
    ↓                         ↓
  层1 → 自回归 Transformer → 生成 Token
    ↓
  VQ-VAE 解码 → 音频
```

**三层次设计：**
- 层 3（~1.5 Hz）：控制全局结构（段落、旋律）
- 层 2（~34 Hz）：控制局部旋律和节奏
- 层 1（~614 Hz）：控制音色和细节

**Jukebox 的意义：**
- 首次证明端到端完整歌曲生成可行
- 含人声、歌词、伴奏
- 但生成 1 分钟音频需 9 小时

**Jukebox 的局限：**
- 速度极慢
- 音质有" artefact"
- 结构有时不连贯

### 2.4 MusicLM（Google, 2023）

```
文本 → MuLan 编码器 → 语义表示
                         ↓
音频 → SoundStream → 语义 Token (5Hz) + 声学 Token (50Hz)
                         ↓
阶段1: 语义 Token 自回归生成（控制"生成什么"）
阶段2: 以语义 Token 为条件，生成声学 Token（控制"听起来如何"）
                         ↓
SoundStream 解码 → 音频
```

**两阶段设计的优势：**
- 语义层负责高层结构（旋律、和声）
- 声学层负责低层细节（音色、混响）
- 分离关注点，各自优化

MusicLM 质量显著优于 Jukebox，但未开源。

### 2.5 MusicGen（Meta, 2023）

**当前最重要的开源音乐生成模型。**

```
文本 → T5/FLAN-T5 编码器 → 文本嵌入
                               ↓ (交叉注意力)
EnCodec Token → 自回归 Transformer → 生成 Token → EnCodec 解码 → 音频
```

**核心设计：**

1. **单阶段自回归**：不像 MusicLM 分两阶段，直接生成
2. **延迟码本模式（Delayed Pattern）**：

```
原始（4层码本，每层4个token）:
  t0: [L0_0, L1_0, L2_0, L3_0]
  t1: [L0_1, L1_1, L2_1, L3_1]
  ...

延迟排列:
  t0: [L0_0]
  t1: [L0_1, L1_0]
  t2: [L0_2, L1_1, L2_0]
  t3: [L0_3, L1_2, L2_1, L3_0]
  
→ 每步最多4个token，有效步数减少
```

3. **文本条件注入**：交叉注意力
4. **旋律条件**：从参考音频提取 chroma 特征作为条件

**MusicGen 的配置：**

| 模型 | 参数量 | GPU 需求 | 质量 |
|------|--------|----------|------|
| MusicGen-Small | 300M | 4GB | 基础 |
| MusicGen-Medium | 1.5B | 8GB | 良好 |
| MusicGen-Large | 3.3B | 16GB | 优秀 |
| MusicGen-Melody | 1.5B | 8GB | 旋律控制 |

### 2.6 Stable Audio（Stability AI, 2023）

基于**潜在扩散模型**：

```
文本 → CLAP 编码器
         ↓
音频 → VAE → 潜在表示 → 扩散去噪 → 潜在表示 → VAE解码 → 音频
         ↑                           ↑
         └──── 文本条件 ─────────────┘
```

特点：
- 潜在空间扩散（比音频空间高效得多）
- 支持精确时长控制
- 高质量立体声输出
- 可控性较强

## 3. 商业级系统

### 3.1 Suno（2023-2024）

**现象级 AI 音乐产品——让普通人创作完整歌曲。**

```
用户输入: "一首关于夏天海边的中国风流行歌"
  ↓
Suno Pipeline（推测）:
  1. LLM 生成歌词和歌曲结构
  2. 文本+歌词 → 音乐 Token 生成（含人声）
  3. Token → 音频解码
  4. 后处理（混音/母带）
  ↓
输出: 完整歌曲（歌词+旋律+人声+伴奏）
```

Suno 的意义：
- AI 音乐从实验室走向大众
- 无需任何音乐知识即可创作
- 2024 年 V3/V4 质量大幅提升

### 3.2 Udio（2024）

类似定位，更面向音乐人：
- 更精细的控制（分轨输出）
- extend/inpaint 编辑功能
- 更高的音频质量
- 强调可商用授权

### 3.3 其他商业产品

| 产品 | 特点 |
|------|------|
| AIVA | 电影配乐/古典风格 |
| Soundraw | 定制背景音乐 |
| Boomy | 一键生成（极简） |
| Mubert | 实时音乐流 |
| Landr | AI 母带处理 |

## 4. 开源歌曲生成：YuE（腾讯, 2024）

**首个开源的完整歌曲生成模型。**

```
输入: 歌词 + 风格描述
  ↓
两阶段生成:
  阶段1: 生成人声轨道（歌词→歌声 Token）
  阶段2: 生成伴奏轨道（风格→伴奏 Token）
  ↓
混音 → 完整歌曲
```

YuE 的意义：
- 填补了开源歌曲生成的空白
- 可在消费级 GPU 上运行
- 支持中文歌词

## 5. 音乐生成的条件控制

### 5.1 文本条件

```
"80s synthwave with heavy bass and retro drums"
→ CLAP 编码 → 文本嵌入 → 交叉注意力注入
```

CLAP（Contrastive Language-Audio Pretraining）：
- 对比学习对齐文本和音频
- 支持开放式文本描述
- 是音乐生成的"CLIP"

### 5.2 旋律条件

```python
# MusicGen 旋律条件
melody, sr = librosa.load('reference.wav')
chroma = librosa.feature.chroma_cqt(y=melody, sr=sr)
# chroma: [12, T] — 每帧的12个音高类能量

wav = model.generate_with_chroma(
    descriptions=["electronic cover"],
    melody=melody[None],
    sample_rate=sr
)
```

### 5.3 多条件组合

```
文本描述 + 参考旋律 + BPM=120 + Key=C major
  → 分别编码 → 融合 → 条件生成
```

## 6. 音乐生成的评估

### 6.1 客观指标

| 指标 | 描述 |
|------|------|
| FAD (Fréchet Audio Distance) | 生成音频与真实音频的分布距离 |
| CLAP Score | 文本-音频对齐度 |
| KLD | 风格分布 KL 散度 |
| Chroma Similarity | 和弦/调性一致性 |
| Tempo Accuracy | BPM 准确性 |

### 6.2 FAD 详解

```
FAD = ||μ_real - μ_gen||² + Tr(Σ_real + Σ_gen - 2(Σ_real·Σ_gen)^{1/2})
```

用 VGGish 或 PANN 提取音频嵌入，计算生成集和参考集的 Fréchet 距离。FAD 越低越好。

### 6.3 主观评估

```
听感质量: 1-5 分
文本一致性: 生成是否符合描述？
音乐性: 是否好听？
结构: 有清晰的段落吗？
创意: 有新意吗？
```

## 7. 实践：用 MusicGen 生成音乐

```python
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

# 加载模型
model = MusicGen.get_pretrained('facebook/musicgen-large')
model.set_generation_params(
    duration=30,          # 30秒
    use_sampling=True,
    top_k=250,
    temperature=1.0
)

# 文本到音乐
wav = model.generate([
    "80s pop track with heavy synth and drums, upbeat",
    "lo-fi hip hop for studying, mellow piano, vinyl crackle",
    "epic orchestral cinematic, rising tension, war drums"
])

for idx, one_wav in enumerate(wav):
    audio_write(f'output_{idx}', one_wav.cpu(), 
                model.sample_rate, strategy="loudness")
```

## 8. 本章小结

音频级音乐生成经历了：

```
WaveNet (2016) → Jukebox (2020) → MusicLM (2023) → MusicGen (2023) → Suno (2024)
   短片段        完整歌曲         两阶段         开源标准       消费级产品
```

核心范式：**EnCodec Token + 自回归 Transformer** 已成为标准。MusicGen 确立了开源基准，Suno/Udio 将技术推向了消费市场。

---

> **上一章**：[第 13 章：符号级音乐生成](./13-symbolic-music-generation.md)
>
> **下一章**：[第 15 章：歌词生成与歌曲级 AI 创作](./15-lyrics-song-creation.md)

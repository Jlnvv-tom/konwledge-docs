# 第 12 章：音乐理论基础与 AI 表示

> **系列文章：《语音与音乐的机器之魂》**
> 音乐有自己的"语法"——音阶、和弦、节奏、曲式。本章速览音乐理论，并解析如何将音乐编码为 AI 可处理的形式。

---

## 1. 音乐理论速览

### 1.1 音高与音阶

**十二平均律：** 一个八度均分为 12 个半音

```
C  C#  D  D#  E  F  F#  G  G#  A  A#  B  C
0  1   2  3   4  5  6   7  8   9  10  11  12
```

每个半音频率比 = $2^{1/12} \approx 1.0595$

**大调音阶**（全全半全全全半）：
```
C大调: C  D  E  F  G  A  B  C
间隔:  全  全  半  全  全  全  半
```

**小调音阶**（全半全全半全全）：
```
A小调: A  B  C  D  E  F  G  A
间隔:  全  半  全  全  半  全  全
```

**五声音阶**（中国风/布鲁斯）：
```
C大调五声: C  D  E  G  A  (去掉了半音冲突，永远"好听")
```

### 1.2 和弦与和声

**三和弦：**

| 类型 | 构成 | 感觉 | 示例 |
|------|------|------|------|
| 大三和弦 | 根音+大三度+纯五度 | 明亮 | C-E-G (C) |
| 小三和弦 | 根音+小三度+纯五度 | 暗淡 | C-Eb-G (Cm) |
| 减三和弦 | 根音+小三度+减五度 | 紧张 | C-Eb-Gb (Cdim) |
| 增三和弦 | 根音+大三度+增五度 | 悬浮 | C-E-G# (Caug) |

**常见和弦进行：**

```
I-V-vi-IV  (C-G-Am-F)   ← 流行万能进行
ii-V-I     (Dm-G-C)     ← 爵士标准
I-IV-V-I   (C-F-G-C)    ← 摇滚/民谣
vi-IV-I-V  (Am-F-C-G)   ← 另一个流行经典
```

### 1.3 节拍与节奏

**拍号：** 分子=每小节拍数，分母=以什么音符为一拍

| 拍号 | 感觉 | 典型风格 |
|------|------|----------|
| 4/4 | 稳定 | 流行/摇滚 |
| 3/4 | 圆舞 | 华尔兹 |
| 6/8 | 律动 | 摇篮曲/布鲁斯 |
| 7/8 | 不规则 | 前卫/民谣 |

**BPM 参考范围：**

```
60-80:  慢歌、抒情
80-100: 中速、R&B
100-120: 流行、轻快
120-140: 摇滚、EDM
140-180: 金属、Drum & Bass
```

### 1.4 曲式结构

流行歌曲的标准结构：

```
Intro → Verse 1 → Pre-Chorus → Chorus → Verse 2 → Pre-Chorus 
     → Chorus → Bridge → Chorus → Outro
```

| 部分 | 功能 |
|------|------|
| Intro | 建立调性和氛围 |
| Verse（主歌） | 讲故事、推进叙事 |
| Pre-Chorus | 蓄力、过渡 |
| Chorus（副歌） | 高潮、记忆点 |
| Bridge | 对比、转折 |
| Outro | 收尾 |

## 2. 音乐的 AI 表示方法

### 2.1 符号表示

| 表示 | 描述 | 示例 |
|------|------|------|
| **MIDI** | 事件序列 | `[Note On C4 v=80] [Note Off C4]` |
| **Piano Roll** | 钢琴卷帘矩阵 | (time, pitch) 二维矩阵 |
| **REMI** | 事件型 Token | `[Bar] [Position 0] [Pitch C4] [Duration 1/4]` |
| **Octuple** | 八元组 | (bar, position, pitch, duration, velocity, ...) |
| **ABC Notation** | 文本乐谱 | `C D E F | G A B c` |
| **MusicXML** | XML 乐谱 | 结构化乐谱表示 |

### 2.2 MIDI 格式详解

MIDI 是音乐 AI 最常用的符号表示：

```python
# MIDI 事件示例
from mido import Message, MidiFile, MidiTrack

track = MidiTrack()
track.append(Message('note_on', note=60, velocity=80, time=0))   # C4 开始
track.append(Message('note_off', note=60, velocity=0, time=480))  # C4 结束(480 ticks)
track.append(Message('note_on', note=64, velocity=75, time=0))   # E4 开始
track.append(Message('note_off', note=64, velocity=0, time=480))  # E4 结束
```

MIDI 的优势：
- 精确的音高和时值
- 多轨道（不同乐器）
- 紧凑的表示
- 大量现有数据（Lakh MIDI）

### 2.3 REMI 表示

REMI（Revamped MIDI-Derived Token Format）专为 Transformer 设计：

```
[Bar] [Tempo 120] [Position 0] [Pitch C4] [Velocity 80] [Duration 1/4]
                   [Position 0] [Pitch E4] [Velocity 75] [Duration 1/4]
                   [Position 1] [Pitch G4] [Velocity 70] [Duration 1/4]
[Bar] [Position 0] [Pitch C5] ...
```

每个 Token 是一个事件类型，模型逐 Token 生成。

### 2.4 音频表示

| 表示 | 信息密度 | 序列长度 | 用途 |
|------|----------|----------|------|
| 波形 | 最高 | 极长 | 直接音频生成 |
| STFT/Mel | 中 | 中 | 声码器、特征提取 |
| 音频 Token | 低 | 较短 | LLM 范式生成 |

### 2.5 混合表示

现代音乐生成模型常使用**层次化混合表示**：

```
符号层: 控制结构、旋律、和声
  → MIDI/REMI Token (结构清晰、可控)

音频层: 控制音色、表现力、混音
  → EnCodec Token (音质好、细节丰富)
```

## 3. 音乐数据集

### 3.1 符号数据集

| 数据集 | 类型 | 规模 | 特点 |
|--------|------|------|------|
| Lakh MIDI | MIDI | 176K 首 | 多流派 |
| MAESTRO | MIDI+Audio | 200h | 古典钢琴比赛 |
| Hooktheory | 和弦+旋律 | 15K 首 | 流行歌曲 |
| JSB Chorales | 四声部 | 382 首 | 巴赫赞美诗 |

### 3.2 音频数据集

| 数据集 | 规模 | 特点 |
|--------|------|------|
| MTG-Jamendo | 5586 首 | Creative Commons |
| FMA | 106K 首 | 多流派 |
| MUSDB18 | 150 首 | 分轨（人声/鼓/贝斯/其他） |
| MusicCaps | 5.5K 首 | Google，文本标注 |
| NSynth | 306K 样本 | 单音，1000+ 乐器 |

### 3.3 数据集选择指南

```
做符号生成 → Lakh MIDI / Hooktheory
做音频生成 → FMA / MTG-Jamendo
做文本条件 → MusicCaps
做音色研究 → NSynth
做源分离   → MUSDB18
做钢琴生成 → MAESTRO
```

## 4. 音乐与 AI 的交汇

### 4.1 AI 在音乐中的能力谱

```
理解 ←───────────────────→ 创作
|         |          |           |
分类    标注      生成         编曲
流派   情感      旋律        配器
乐器   和弦      歌词        混音
```

### 4.2 当前能力评估

| 能力 | AI 水平 | 人类水平差距 |
|------|---------|-------------|
| 单音音色生成 | 接近人类 | 很小 |
| 短片段生成（< 30s） | 接近人类 | 很小 |
| 完整歌曲生成 | 可用但需人工修 | 结构/歌词/编曲 |
| 即兴演奏 | 初级 | 差距大 |
| 编曲/配器 | 辅助级 | 差距大 |
| 音乐分析 | 优秀 | 超越一般人类 |

## 5. 本章小结

音乐理论提供了 AI 音乐生成的"语法"基础：
- **音阶/和弦**定义了什么听起来"好听"
- **节奏/拍号**定义了时间结构
- **曲式**定义了歌曲的整体架构

选择合适的表示方法是设计音乐生成模型的第一步——符号表示适合结构和旋律，音频表示适合音色和表现力。

---

> **上一章**：[第 11 章：歌声合成与歌声转换](./11-singing-voice-synthesis.md)
>
> **下一章**：[第 13 章：符号级音乐生成](./13-symbolic-music-generation.md)

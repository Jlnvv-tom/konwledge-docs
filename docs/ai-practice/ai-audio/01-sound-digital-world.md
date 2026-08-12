---
sidebar_position: 1
---

# 第 1 章：声音的数字世界——从声波到比特

> **系列文章：《语音与音乐的机器之魂》**
> 本文是书籍系列的第 1 章，带你理解声音如何从物理世界进入数字世界，这是所有 AI 语音技术的起点。

---

## 1. 声音的物理本质

声音是物体振动在介质（通常是空气）中传播的机械波。当你拍手时，空气分子被压缩和拉伸，形成疏密交替的纵波，最终到达耳膜，被大脑解读为"声音"。

人类可听频率范围约为 **20 Hz – 20 kHz**。声音有三个核心维度：

| 维度 | 感知 | 单位 |
|------|------|------|
| 频率（Frequency） | 音高 | 赫兹（Hz） |
| 振幅（Amplitude） | 响度 | 分贝（dB） |
| 波形（Waveform） | 音色 | — |

- **频率**：440 Hz 是标准音 A4，频率越高音越高
- **振幅**：日常对话约 60 dB，摇滚音乐会约 110 dB
- **波形**：正弦波（纯净如长笛）、方波（电子感）、锯齿波（尖锐如小号）

## 2. 采样定理与模数转换

要让计算机处理声音，首先需要将连续的模拟信号转换为离散的数字信号。

### 2.1 奈奎斯特-香农采样定理

> **采样频率需至少为信号最高频率的 2 倍，才能无失真地重建原始信号。**

人耳最高可听 20 kHz，因此 CD 音质采用 **44.1 kHz** 采样率（20k × 2 + 余量）。电话语音通常使用 **16 kHz**（覆盖 8 kHz 以内足够清晰）。

常见采样率：

| 采样率 | 用途 |
|--------|------|
| 8 kHz | 电话 |
| 16 kHz | 语音识别/TTS |
| 22.05 kHz | 低质量音频 |
| 44.1 kHz | CD 音质 |
| 48 kHz | 专业音视频 |
| 96 kHz / 192 kHz | 高分辨率音频 |

### 2.2 模数转换流程

```
声波 → 抗混叠滤波器 → 采样 → 量化 → PCM 编码 → 数字音频
```

1. **抗混叠滤波器**：滤除高于奈奎斯特频率的成分，防止频谱混叠
2. **采样**：以固定时间间隔取信号值
3. **量化**：将连续幅度映射为有限离散值
4. **PCM 编码**：将量化值编码为二进制

### 2.3 位深

位深决定了动态范围——能表示的最小和最大声音的差异：

| 位深 | 动态范围 | 用途 |
|------|----------|------|
| 8-bit | ~48 dB | 旧式电话/游戏 |
| 16-bit | ~96 dB | CD 音质 |
| 24-bit | ~144 dB | 专业录音 |
| 32-bit float | 无限（理论） | 音频处理 |

### 2.4 声道

- **单声道（Mono）**：1 个声道，语音应用标准
- **立体声（Stereo）**：2 个声道，音乐标准
- **5.1 / 7.1 环绕**：影院和家庭影院
- **Dolby Atmos**：基于对象的三维声场

## 3. 音频频域表示

时域波形直观但难以直接用于 AI 建模。频域表示能揭示声音的"频率成分"，是音频 AI 的核心特征。

### 3.1 傅里叶变换与频谱

傅里叶变换将时域信号分解为不同频率的正弦波叠加：

$$X(f) = \int x(t) \cdot e^{-j2\pi ft} dt$$

但对于音频信号，我们需要知道"什么时候出现了什么频率"，因此使用**短时傅里叶变换（STFT）**：

$$X(t, f) = \int x(\tau) \cdot w(\tau - t) \cdot e^{-j2\pi f\tau} d\tau$$

其中 $w(\tau - t)$ 为窗函数（Hann、Hamming 等），在时间 $t$ 附近取一段信号做傅里叶变换。

**STFT 的结果是一个二维矩阵：时间 × 频率 → 幅度**，可以用热力图可视化（即频谱图 Spectrogram）。

### 3.2 梅尔频谱（Mel Spectrogram）

人耳对频率的感知是非线性的——低频差异容易分辨，高频差异难以区分。梅尔刻度模拟这一特性：

$$mel(f) = 2595 \cdot \log_{10}\left(1 + \frac{f}{700}\right)$$

在梅尔刻度上，100 Hz 和 200 Hz 之间的距离与 1000 Hz 和 1100 Hz 之间的距离不同（前者更大）。

**梅尔频谱**的生成过程：

```
波形 → STFT → 幅度谱 → 梅尔滤波器组 → 梅尔频谱
```

梅尔频谱将频率轴从线性刻度压缩为梅尔刻度，使得特征更符合人耳感知。**它是绝大多数语音模型（TTS、ASR、声码器）的核心输入/输出特征。**

### 3.3 其他常用音频特征

| 特征 | 全称 | 描述 | 典型用途 |
|------|------|------|----------|
| MFCC | Mel-Frequency Cepstral Coefficients | 梅尔频率倒谱系数 | 语音识别、声纹识别 |
| CQT | Constant-Q Transform | 常数 Q 变换 | 音乐分析（频率对数分布） |
| Chroma | — | 色度特征 | 和弦识别（12 个音高类） |
| Spectral Contrast | — | 频谱对比度 | 音色分类 |
| Zero Crossing Rate | — | 过零率 | 浊音/清音判断 |
| F0 | Fundamental Frequency | 基频 | 音高检测 |

### 3.4 MFCC 详解

MFCC 曾是语音识别的黄金标准特征，其提取流程：

```
波形 → 预加重 → 分帧加窗 → FFT → 梅尔滤波 → 对数 → DCT → MFCC
```

1. **预加重**：高通滤波，增强高频
2. **分帧**：20-40ms 帧长，10ms 帧移
3. **FFT**：转频域
4. **梅尔滤波**：映射到梅尔刻度
5. **对数**：模拟响度感知
6. **DCT**：去相关，保留低阶系数

通常取前 13 维 + 一阶差分 + 二阶差分 = 39 维。

## 4. 音频文件格式与编码

### 4.1 无损格式

| 格式 | 特点 |
|------|------|
| WAV (PCM) | 未压缩，最通用，文件大 |
| FLAC | 无损压缩，约 50-60% 原始大小 |
| ALAC | Apple 无损，iTunes 生态 |

### 4.2 有损格式

| 格式 | 特点 | 典型码率 |
|------|------|----------|
| MP3 | 最普及，专利已过期 | 128-320 kbps |
| AAC | 比 MP3 更高效，YouTube/Apple 使用 | 128-256 kbps |
| Opus | 最新标准，低延迟，语音首选 | 6-510 kbps |
| Ogg Vorbis | 开源免费，游戏常用 | 128-320 kbps |

### 4.3 流媒体特殊需求

- **Opus**：支持低延迟模式（< 5ms），适合实时语音通信
- **AAC-LD**：低延迟 AAC，视频会议使用
- **自适应码率（ABR）**：根据网络状况动态调整

## 5. 实践：用 Python 分析音频

```python
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

# 加载音频
y, sr = librosa.load('example.wav', sr=22050)

# 1. 波形
plt.figure(figsize=(12, 4))
librosa.display.waveshow(y, sr=sr)
plt.title('Waveform')
plt.savefig('waveform.png')

# 2. STFT 频谱
D = librosa.stft(y)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
plt.figure(figsize=(12, 4))
librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='linear')
plt.colorbar(format='%+2.0f dB')
plt.title('Spectrogram')
plt.savefig('spectrogram.png')

# 3. 梅尔频谱
mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80)
mel_db = librosa.power_to_db(mel, ref=np.max)
plt.figure(figsize=(12, 4))
librosa.display.specshow(mel_db, sr=sr, x_axis='time', y_axis='mel')
plt.colorbar(format='%+2.0f dB')
plt.title('Mel Spectrogram')
plt.savefig('mel_spectrogram.png')

# 4. MFCC
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
plt.figure(figsize=(12, 4))
librosa.display.specshow(mfcc, sr=sr, x_axis='time')
plt.colorbar()
plt.title('MFCC')
plt.savefig('mfcc.png')

# 5. 基频 (F0)
f0, voicing, voicing_p = librosa.pyin(y, fmin=80, fmax=400, sr=sr)
plt.figure(figsize=(12, 4))
times = librosa.times_like(f0, sr=sr)
plt.plot(times, f0, label='F0', color='r')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Fundamental Frequency (F0)')
plt.savefig('f0.png')
```

## 6. 本章小结

理解声音的数字化与频域表示，是进入 AI 语音领域的第一块基石：

- **采样定理**决定了数字音频的基本参数
- **STFT 和梅尔频谱**是语音模型最核心的特征表示
- **MFCC** 在传统语音系统中仍然广泛使用
- 音频格式选择影响质量、文件大小和延迟

后续所有模型的设计都建立在"如何让机器更好地理解和生成这些数字信号"之上。

---

> **下一章**：[第 2 章：AI 语音技术发展简史](./02-ai-speech-history.md) — 从 1950 年的 Audrey 到 2024 年的 GPT-4o，一段跨越七十年的技术旅程。

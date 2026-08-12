---
sidebar_position: 17
---

# 第 17 章：数据采集、标注与清洗

> **系列文章：《语音与音乐的机器之魂》**
> 数据决定上限，模型只是逼近这个上限。本章聚焦语音/音乐 AI 的数据工程全流程。

---

## 1. 数据的重要性

```
模型质量 = f(数据质量, 数据量, 模型架构, 训练策略)
         ↑           ↑          ↑           ↑
       最重要       最重要      可复现      可调优
```

Whisper 的成功不是架构创新（就是标准 Transformer），而是 **68 万小时数据**。

## 2. 数据采集

### 2.1 开源数据源

#### 语音数据

| 数据集 | 时长 | 语言 | 特点 |
|--------|------|------|------|
| LibriSpeech | 960h | 英文 | 有声书，干净 |
| LibriHeavy | 50000h | 英文 | LibriSpeech 超大版 |
| Common Voice | 20000h+ | 100+ 语言 | 众包，多口音 |
| AISHELL-3 | 85h | 中文 | 多说话人 TTS |
| WenetSpeech | 10000h | 中文 | 互联网音频 |
| GigaSpeech | 10000h | 英文 | 多领域 |
| VoxCeleb 1/2 | 2000h+ | 多语言 | 说话人识别 |
| MLS | 50000h | 8 语言 | 多语言 ASR |

#### 音乐数据

| 数据集 | 规模 | 特点 |
|--------|------|------|
| Lakh MIDI | 176K 首 | MIDI 格式 |
| MAESTRO | 200h | 钢琴 MIDI+音频 |
| MusicCaps | 5.5K 首 | Google 文本标注 |
| FMA | 106K 首 | 多流派音频 |
| MTG-Jamendo | 5586 首 | CC 授权 |
| MUSDB18 | 150 首 | 分轨数据 |
| NSynth | 306K 样本 | 单音 |

### 2.2 网络数据采集

```
合法来源:
  - YouTube（CC-licensed）→ yt-dlp 下载
  - LibriVox（公有领域有声书）
  - Internet Archive
  - Wikimedia Commons
  
注意事项:
  - 版权：Creative Commons / Public Domain
  - 隐私：不含个人隐私内容
  - 质量：自动筛选高质量段
```

### 2.3 自建数据采集

```
录音棚录制:
  - 专业设备（电容麦克风+声卡）
  - 隔音环境（噪声 < 30 dB）
  - 多说话人（覆盖年龄/性别/口音）
  - 标注：文本转写 + 时间戳
```

## 3. 数据标注

### 3.1 ASR 标注

```
音频 → 人工转写 → 文本标注
                → 时间戳（词级/句级）
                → 说话人标识
                → 情感标签（可选）
```

**标注质量等级：**

| 等级 | 描述 | WER |
|------|------|-----|
| 金标 | 专家逐词校对 | < 1% |
| 银标 | 人工转写，未校对 | 2-5% |
| 铜标 | 机器转写 + 抽检 | 5-15% |
| 弱标注 | 字幕文件 | 10-30% |

Whisper 使用的"弱标注"策略证明：**数量可以弥补质量**。

### 3.2 TTS 标注

```
文本 → 音素对齐 → 基频标注 → 情感/韵律标签
   ↑
需要高精度时间对齐
```

强制对齐工具：
- **MFA（Montreal Forced Aligner）**：基于 Kaldi 的强制对齐
- **WhisperX**：Whisper + 强制对齐
- **CTC decoding**：基于 CTC 模型的对齐

### 3.3 音乐标注

```
音频 → 
  - 节拍/BPM 标注
  - 和弦标注
  - 乐器标注
  - 情感标签
  - 文本描述（MusicCaps 风格）
```

**音乐情感模型：**
- Russell 二维度：Valence（愉悦度）× Arousal（唤醒度）
- 音乐标签：happy, sad, energetic, calm, aggressive, tender

### 3.4 众包标注

```
平台:
  - Amazon Mechanical Turk
  - Scale AI
  - Labelbox
  
质量控制:
  - 多人标注 + 一致性检查（Cohen's κ）
  - 金标准测试（插入已知正确答案）
  - 时间控制（过快=不认真）
```

## 4. 数据清洗

### 4.1 音频质量筛选

```python
import librosa
import soundfile as sf
import numpy as np

def audio_quality_check(audio_path):
    """音频质量自动检查"""
    y, sr = librosa.load(audio_path, sr=None)
    issues = []
    
    # 1. 采样率检查
    if sr < 16000:
        issues.append(f"采样率过低: {sr}Hz")
    
    # 2. 时长检查
    duration = len(y) / sr
    if duration < 1.0:
        issues.append(f"过短: {duration:.1f}s")
    if duration > 300:
        issues.append(f"过长: {duration:.1f}s")
    
    # 3. 音量检查
    rms = np.sqrt(np.mean(y**2))
    if rms < 0.001:
        issues.append(f"音量过低: RMS={rms:.4f}")
    
    # 4. 削波检查
    clipping_ratio = np.mean(np.abs(y) > 0.99)
    if clipping_ratio > 0.01:
        issues.append(f"削波: {clipping_ratio:.2%}")
    
    # 5. 静音段检查
    non_silent = librosa.effects.split(y, top_db=40)
    silent_ratio = 1 - len(non_silent) / len(y)
    if silent_ratio > 0.7:
        issues.append(f"静音过多: {silent_ratio:.2%}")
    
    # 6. SNR 估计
    if len(non_silent) > 0:
        signal = np.concatenate([y[s:e] for s, e in non_silent])
        noise = np.concatenate([y[e:s] for s, e in zip(
            [0]+[e for s, e in non_silent],
            list(non_silent[:, 1]) + [len(y)]
        ) if s < e])
        if len(noise) > 0:
            snr = 10 * np.log10(np.var(signal) / np.var(noise))
            if snr < 15:
                issues.append(f"SNR过低: {snr:.1f}dB")
    
    return issues
```

### 4.2 文本清洗

```python
def text_normalization(text, language='zh'):
    """文本正规化"""
    import re
    
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    if language == 'zh':
        # 全角转半角
        text = text.translate(str.maketrans(
            '０１２３４５６７８９ａｂｃＡＢＣ', 
            '0123456789abcABC'
        ))
        # 去除标点噪声
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？、；：""''（）]', '', text)
    else:
        # 英文小写化（可选）
        text = text.lower()
    
    return text
```

### 4.3 去重与去噪

```
去重:
  - 音频指纹（fingerprint）去重
  - 文本去重（n-gram 相似度）
  - 完全重复 + 近似重复

去噪:
  - VAD 去除静音段
  - 噪声抑制（RNNoise/Demucs）
  - 去除音乐背景（如果需要纯语音）
  - 去除非目标语言段
```

### 4.4 数据平衡

```
说话人平衡:
  - 限制每人最大时长（如每人 ≤ 30 分钟）
  - 确保性别/年龄/口音分布

语言平衡:
  - 多语言模型需平衡各语言时长
  - 避免某种语言过度主导

长度分布:
  - 短音频（1-10s）+ 中等（10-60s）+ 长（60s+）
  - 避免全部是同一种长度
```

## 5. 数据增强

### 5.1 音频增强

```python
import librosa
import numpy as np
import scipy.signal

def augment_audio(y, sr):
    """音频数据增强"""
    augmented = []
    
    # 1. 加噪声
    noise = np.random.normal(0, 0.005, len(y))
    augmented.append(('noise', y + noise))
    
    # 2. 加速/减速（不改音高）
    rate = np.random.uniform(0.9, 1.1)
    y_stretch = librosa.effects.time_stretch(y, rate=rate)
    augmented.append(('speed', y_stretch))
    
    # 3. 音高偏移
    steps = np.random.randint(-3, 4)
    y_shift = librosa.effects.pitch_shift(y, sr=sr, n_steps=steps)
    augmented.append(('pitch', y_shift))
    
    # 4. 混响（简单版）
    ir = np.random.exponential(0.01, size=int(sr * 0.3))
    ir = ir * np.exp(-np.arange(len(ir)) / (sr * 0.1))
    y_reverb = scipy.signal.fftconvolve(y, ir)[:len(y)]
    augmented.append(('reverb', y_reverb))
    
    # 5. 音量变化
    gain = np.random.uniform(0.5, 1.5)
    augmented.append(('volume', y * gain))
    
    return augmented
```

### 5.2 SpecAugment

在频谱层面做增强，广泛用于 ASR：

```
原始 Mel 频谱
  → 时间掩码（mask 连续 t 帧）
  → 频率掩码（mask 连续 f 个 Mel 频率）
  → 增强后的频谱
```

```python
def spec_augment(mel, time_mask=30, freq_mask=15, n_time=2, n_freq=2):
    """SpecAugment"""
    T, F = mel.shape
    
    # 频率掩码
    for _ in range(n_freq):
        f = np.random.randint(0, freq_mask)
        f0 = np.random.randint(0, F - f)
        mel[:, f0:f0+f] = 0
    
    # 时间掩码
    for _ in range(n_time):
        t = np.random.randint(0, time_mask)
        t0 = np.random.randint(0, T - t)
        mel[t0:t0+t, :] = 0
    
    return mel
```

## 6. 数据管线工程

### 6.1 数据版本管理

```bash
# DVC (Data Version Control)
dvc init
dvc add data/raw/
dvc push  # 上传到远程存储

# 版本切换
git checkout v2.0
dvc pull  # 拉取对应数据版本
```

### 6.2 数据加载优化

```python
# WebDataset: 高效大规模数据加载
import webdataset as wds

dataset = (
    wds.WebDataset("data/shards/audio-{000000..001000}.tar")
    .decode()
    .map(preprocess)
    .batched(16)
)

# 特点:
# - 流式加载，不占内存
# - 支持远程存储（S3/GCS）
# - 自动分片和并行
```

## 7. 本章小结

数据工程是 AI 系统的地基：

```
采集 → 标注 → 清洗 → 增强 → 版本管理
```

关键原则：
1. **质量 > 数量**（但数量也很重要）
2. **多样性** > 单一来源
3. **弱标注 + 大规模** 可以超越 小规模精确标注
4. 数据增强是低成本提升的利器
5. 数据管线工程化是生产部署的必要条件

---

> **上一章**：[第 16 章：交互式 AI 音乐工具与实践](./16-interactive-ai-music.md)
>
> **下一章**：[第 18 章：训练 Pipeline 与分布式训练](./18-training-pipeline.md)

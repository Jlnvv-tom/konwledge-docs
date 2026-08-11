# 第 9 章：音色的数学描述与感知维度

> **系列文章：《语音与音乐的机器之魂》**
> 音色是声音最神秘的维度——相同音高和响度下，钢琴和小提琴为何不同？本章从物理和感知两个层面解析音色。

---

## 1. 音色是什么

音色（Timbre）是区分相同音高和响度下不同声源的声音属性。它是一个多维度的感知量，包含：

- **频谱包络**：各次谐波的强度分布
- **时间包络**：ADSR（起音-衰减-延音-释放）
- **瞬态特征**：起音阶段的噪声成分
- **调制特征**：颤音、震音等时间变化

> 定义（ASA, 1960）：音色是听觉感知属性，通过它听者可以在具有相同音高和响度的声音之间进行区分。

## 2. 频谱视角

### 2.1 谐波结构

大部分乐音由基频（F0）和整数倍谐波组成：

```
基频: F0 = 440 Hz (A4)
谐波: 2F0 = 880 Hz, 3F0 = 1320 Hz, 4F0 = 1760 Hz, ...
```

不同乐器的谐波强度分布不同：

```
钢琴:  谐波丰富，高次谐波快速衰减（温暖、圆润）
小提琴: 谐波持续，有颤音调制（明亮、丰富）
长笛:  低次谐波为主，近似正弦（纯净、空灵）
单簧管: 奇数谐波突出（空洞、木质感）
人声:  共振峰（F1, F2, F3...）决定元音音色
```

### 2.2 共振峰

共振峰是声道/共鸣体的固有共振频率，对音色起决定性作用：

**人声共振峰与元音：**

| 元音 | F1 (Hz) | F2 (Hz) | F3 (Hz) |
|------|---------|---------|---------|
| /a/ (啊) | 700 | 1200 | 2500 |
| /i/ (衣) | 300 | 2300 | 3000 |
| /u/ (乌) | 300 | 800 | 2200 |
| /e/ (诶) | 500 | 1800 | 2500 |
| /o/ (哦) | 500 | 1000 | 2400 |

不同人说话的"音色"差异，很大程度上来自共振峰的细微差异。

### 2.3 频谱包络的数学表示

频谱包络可以通过以下方式提取：

```python
import numpy as np
from scipy.signal import lfilter

# 方法1: LPC（线性预测编码）
def lpc_envelope(spectrum, order=30):
    """用 LPC 系数估计频谱包络"""
    # LPC 系数 → 频率响应
    a = lpc_coefficients(spectrum, order)
    w = np.linspace(0, np.pi, len(spectrum))
    h = 1 / (1 + np.sum(a[i] * np.exp(-1j * w * i) for i in range(1, order+1)))
    return np.abs(h)

# 方法2: Cepstral 平滑
def cepstral_envelope(spectrum, n_ceps=30):
    """用倒谱低频分量估计包络"""
    log_spec = np.log(spectrum)
    cepstrum = np.fft.ifft(log_spec)
    cepstrum[n_ceps:-n_ceps] = 0  # 只保留低频
    envelope = np.exp(np.fft.fft(cepstrum))
    return np.real(envelope)
```

## 3. 时间包络（ADSR）

声音的时间演变对音色感知至关重要：

```
    ┌──┐
    │  \___
    │     \___
    │         \__________
    │                   \___
    └───────────────────────→ 时间
    Attack  Decay  Sustain  Release
```

| 阶段 | 描述 | 典型时长 |
|------|------|----------|
| Attack（起音） | 声音从零到峰值 | 1-50ms |
| Decay（衰减） | 从峰值降到 sustain 水平 | 10-200ms |
| Sustain（延音） | 持续保持的水平 | 不定 |
| Release（释放） | 松开后衰减到零 | 50-500ms |

不同乐器的 ADSR 差异：

```
钢琴:   快Attack → 快Decay → 低Sustain → 慢Release（敲击+共振）
小提琴: 慢Attack → 无Decay → 高Sustain → 慢Release（弓弦持续激励）
鼓:     极快Attack → 极快Decay → 无Sustain → 无Release（瞬态+衰减）
长笛:   慢Attack → 无Decay → 中Sustain → 慢Release（气流建立）
```

## 4. 感知维度

### 4.1 Grey 的三维度模型

Grey（1977）通过多维尺度分析（MDS）提出音色感知的三个维度：

1. **谱质心（Spectral Centroid）**：频谱重心，对应"明亮度"
   - 高谱质心 → 明亮、尖锐（如小号）
   - 低谱质心 → 暗沉、温暖（如大提琴）

2. **起音时间（Attack Time）**：声音建立的速度
   - 快起音 → 打击感、锐利（如钢琴、鼓）
   - 慢起音 → 柔和、持续（如弦乐、长笛）

3. **谱通量（Spectral Flux）**：频谱变化速率
   - 高谱通量 → 动态变化大（如人声）
   - 低谱通量 → 稳定（如持续音）

### 4.2 扩展维度

后续研究增加了更多维度：

4. **谱平坦度（Spectral Flatness）**：噪声 vs 谐波成分
   - 低 → 谐波丰富（如弦乐）
   - 高 → 噪声为主（如铙钹）

5. **谱滚降点（Spectral Rolloff）**：85% 能量所在频率
   - 高 → 高频能量多
   - 低 → 低频能量多

### 4.3 计算代码

```python
import librosa
import numpy as np

def timbre_features(y, sr):
    """计算音色感知特征"""
    features = {}
    
    # 谱质心（亮度）
    features['centroid'] = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
    
    # 谱通量
    features['flux'] = librosa.onset.onset_strength(y=y, sr=sr).mean()
    
    # 谱平坦度（噪声 vs 谐波）
    features['flatness'] = librosa.feature.spectral_flatness(y=y).mean()
    
    # 谱滚降点
    features['rolloff'] = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85).mean()
    
    # 过零率
    features['zcr'] = librosa.feature.zero_crossing_rate(y).mean()
    
    # MFCC 均值（音色特征向量）
    features['mfcc'] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
    
    return features
```

## 5. 乐器分类与音色族

### 5.1 声学分类（Hornbostel-Sachs）

| 类别 | 发声原理 | 代表乐器 | 音色特征 |
|------|----------|----------|----------|
| 弦乐器 | 弦振动 + 共振箱 | 小提琴、吉他、钢琴 | 谐波丰富，有起音瞬态 |
| 管乐器 | 气流激励 + 管体共振 | 长笛、单簧管、小号 | 有持续共振峰，吹气噪声 |
| 打击乐 | 撞击/摇动 | 鼓、铙钹、木琴 | 瞬态为主，噪声成分 |
| 电子乐器 | 合成器 | 合成器、采样器 | 任意音色 |
| 人声 | 声带振动 + 声道滤波 | 男女声、歌唱 | 共振峰明显，情感丰富 |

### 5.2 音色的机器学习分类

```python
from sklearn.ensemble import RandomForestClassifier

# 特征: [centroid, flux, flatness, rolloff, zcr, mfcc1-13]
# 标签: [piano, violin, flute, drum, ...]

classifier = RandomForestClassifier(n_estimators=100)
classifier.fit(X_train, y_train)
predicted_instrument = classifier.predict(X_test)
```

## 6. 音色的合成与操控

### 6.1 减法合成

从一个丰富谐波信号中减去不需要的频率：

```
锯齿波（丰富谐波）→ 滤波器（低通/带通）→ 音色
```

### 6.2 加法合成

叠加多个正弦波构建音色：

```
F0 + a1·sin(2F0) + a2·sin(3F0) + ... → 音色
```

### 6.3 调频合成（FM）

```
载波频率 + 调制器 → 复杂谐波结构 → 音色
carrier = sin(2π·fc·t + I·sin(2π·fm·t))
```

### 6.4 物理建模合成

模拟乐器各部件的物理方程：

```
弦: d²y/dt² = c²·d²y/dx² + damping + excitation
管: 声波传播方程 + 边界条件
```

## 7. 本章小结

音色是一个多维度的感知属性，核心维度包括：

1. **频谱维度**：谐波结构、共振峰、谱质心
2. **时间维度**：ADSR 包络、起音时间
3. **动态维度**：谱通量、调制特征

理解音色的物理和感知基础，是设计音色生成模型的出发点。后续章节将探讨如何用 AI 来生成和操控这些维度。

---

> **上一章**：[第 8 章：流式与实时语音模型](./08-streaming-realtime.md)
>
> **下一章**：[第 10 章：音色生成模型与控制技术](./10-timbre-generation.md)

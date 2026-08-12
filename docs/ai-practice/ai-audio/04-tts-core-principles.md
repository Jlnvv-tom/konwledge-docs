---
sidebar_position: 4
---

# 第 4 章：语音合成（TTS）核心原理

> **系列文章：《语音与音乐的机器之魂》**
> TTS 是语音 AI 中最成熟的落地技术。本章从系统架构到模型演进，深入解析文本如何变成声音。

---

## 1. TTS 系统总览

现代神经 TTS 的典型 pipeline：

```
文本输入 → 文本前端 → 声学模型 → 声码器 → 音频输出
"你好世界"  /nǐ/hǎo/shì/jiè/  Mel频谱     波形
```

三个核心模块：
- **文本前端**：文本 → 音素序列 + 韵律特征
- **声学模型**：音素 → 声学特征（通常 Mel 频谱）
- **声码器**：声学特征 → 音频波形

## 2. 文本前端处理

### 2.1 文本正规化

将非标准文字转为可读形式：

| 输入 | 输出 | 说明 |
|------|------|------|
| 123 | 一百二十三 | 数字转中文读法 |
| 3.14 | 三点一四 | 小数 |
| 2024年 | 二零二四年 | 年份 |
| Mr. | Mister | 缩写展开 |
| @ | at | 符号 |
| 100°C | 一百摄氏度 | 单位 |
| ❤️ | love / heart | 表情（特殊处理） |

### 2.2 音素化

音素是语言中最小的语音单位。将文字转为音素序列比直接用字符效果好得多。

**中文：**
```
"你好世界" → 拼音 "nǐ hǎo shì jiè"
→ 音素序列: n i3 h ao3 sh ih4 j ie4
```

**英文（G2P）：**
```
"hello world" → "HH AH L OW W ER L D"
```

常用工具：
- `pypinyin`：中文拼音转换
- `g2p_en`：英文 G2P
- `espeak-ng`：多语言 TTS 前端
- `OpenJTalk`：日语

### 2.3 多音字消歧

中文多音字是前端处理的难点：

```
银行 (yín háng) vs 行走 (xíng zǒu)
重庆 (chóng qìng) vs 重复 (chóng fù)
长大 (zhǎng dà) vs 长城 (cháng chéng)
```

解决方案：
- 基于规则 + 词典
- BERT 等语言模型消歧
- 端到端模型直接从字符学习（减少对 G2P 的依赖）

### 2.4 韵律预测

韵律决定语音的"抑扬顿挫"：

- **重音（Stress）**：哪些词需要强调
- **语调（Intonation）**：陈述句降调、疑问句升调
- **停顿（Pause）**：逗号、句号处的停顿时长
- **时长（Duration）**：每个音素的持续时长

## 3. 声学模型演进

### 3.1 Tacotron 2 详解

Tacotron 2（2018）是最经典的端到端声学模型，理解它就理解了 TTS 的核心思想。

**整体架构：**

```
音素序列 → 编码器 → 注意力 → 解码器 → Post-Net → Mel频谱
```

#### 编码器

```
音素 → Embedding(512维) → 3层Conv1D(5,1) → BiLSTM(256×2) → 编码器输出
```

Conv1D 做局部特征提取，BiLSTM 捕捉双向上下文。

#### 注意力机制

Location-sensitive attention（位置敏感注意力）：

```python
class LocationSensitiveAttention(nn.Module):
    def forward(self, query, keys, values, prev_weights):
        # 内容分数
        content_score = self.v.T @ tanh(W_q @ query + W_k @ keys)
        # 位置分数
        location_score = self.v.T @ tanh(W_f @ conv(prev_weights))
        # 合并
        scores = content_score + location_score
        weights = softmax(scores)
        context = sum(weights * values)
        return context, weights
```

加入位置历史防止"重复"和"跳词"——这是早期 TTS 的常见问题。

#### 解码器

自回归逐帧生成：

```
循环:
  1. 输入: 上一帧 Mel (初始为零)
  2. PreNet: 2层FC + Dropout(0.5) → 增加鲁棒性
  3. AttentionRNN: 与编码器做注意力
  4. DecoderRNN: 2层 LSTM
  5. Linear: 投影到 80 维 Mel
  6. StopPredictor: 预测是否结束
  7. 输出: 当前帧 Mel + Stop概率
```

#### Post-Net

5 层卷积对 Mel 频谱做残差精修，改善高频细节。

### 3.2 FastSpeech 系列——非自回归

**动机：** Tacotron 自回归生成速度慢，且存在重复/跳词。

#### FastSpeech（2019）

完全非自回归，一次前向生成所有帧：

```
音素 → Transformer编码器 → 时长预测器 → 长度调节器 → Transformer解码器 → Mel
```

**时长预测器** 是关键——预测每个音素对应多少帧 Mel，然后通过 Length Regulator 扩展序列：

```python
def length_regulator(encoder_out, durations):
    """
    encoder_out: [B, n_phonemes, D]
    durations: [B, n_phonemes] 每个音素的帧数
    """
    outputs = []
    for b in range(B):
        expanded = []
        for i, d in enumerate(durations[b]):
            expanded.extend([encoder_out[b, i]] * d)
        outputs.append(expanded)
    return pad(outputs)
```

#### FastSpeech 2（2021）

引入更多变分信息：

```
音素 → 编码器 → 时长预测器 → 音高预测器 → 能量预测器 → 解码器 → Mel
```

显式建模音高和能量，比 FastSpeech 1 质量显著提升，接近 Tacotron 2 但速度快数十倍。

### 3.3 VITS——端到端 TTS

VITS（2021）将声学模型和声码器**统一到一个模型**中：

```
训练时:
  文本 → 先验编码器 → 先验分布
  音频 → 后验编码器 → 后验分布
  KL散度对齐先验和后验
  
  后验 z → 解码器(流模型) → 重建波形
  判别器区分真假波形

推理时:
  文本 → 先验编码器 → 采样 z → 解码器 → 波形
  (不需要后验编码器)
```

**核心创新：**
- **变分推断**：用后验分布辅助训练，推理时只用先验
- **标准化流**：在先验和后验之间建立可逆映射，增强先验的表达力
- **对抗训练**：多周期判别器 + 多尺度判别器
- **Stochastic Duration Predictor**：随机时长预测，增加自然度

VITS 的意义：第一次实现了端到端 TTS，无需分阶段训练，质量与两阶段系统相当。

### 3.4 大语言模型驱动的 TTS

2023 年后的范式转变——将语音生成建模为"语言生成"问题。

#### VALL-E 架构

```
3秒参考音频 → EnCodec 编码 → 音频 Token (作为 prompt)
文本 → 音素编码
→ 自回归 Transformer (类似 GPT)
→ 逐 token 预测音频 Token
→ EnCodec 解码 → 克隆语音
```

**核心思想：**
- 语音 = 一种"语言"，音频 Token = "词"
- LLM 的上下文学习能力 = 零样本声音克隆
- 不需要为每个说话人单独训练

**优势：**
- 零样本（Zero-shot）：3 秒参考音频即可
- 保留说话人的情感、语调、口音
- 统一框架处理多语言、多说话人
- 可利用 LLM 的扩展性规律

#### 代表模型对比

| 模型 | 架构 | 零样本 | 多语言 | 开源 | 特点 |
|------|------|--------|--------|------|------|
| VALL-E | 自回归 Transformer | ✅ | ❌ | ❌ | 开创性 |
| Voicebox | 流匹配 | ✅ | ✅ | ❌ | 多功能 |
| NaturalSpeech 3 | 扩散+VQ | ✅ | ❌ | ❌ | 高质量 |
| CosyVoice | 流匹配 | ✅ | ✅ | ✅ | 中英日韩粤 |
| F5-TTS | 流匹配 | ✅ | ✅ | ✅ | 纯流匹配 |
| GPT-4o | 原生多模态 | ✅ | ✅ | ❌ | 全双工对话 |

## 4. 注意力机制在 TTS 中的演进

| 类型 | 模型 | 特点 | 问题 |
|------|------|------|------|
| 内容注意力 | Tacotron | 只看编码器输出 | 重复/跳词 |
| 位置注意力 | Tacotron 2 | 加入位置历史 | 改善但仍不稳定 |
| 动态卷积注意力 | DCA | 卷积替代RNN | 更快更稳定 |
| Monotonic Attention | MoChA | 单调对齐 | 适合流式 |
| 时长预测器 | FastSpeech | 显式对齐，无需注意力 | **最稳定** |

现代 TTS 基本抛弃了注意力机制，转向显式时长预测。

## 5. TTS 前沿方向

### 5.1 情感可控 TTS

```
文本 + 情感标签(开心/悲伤/愤怒) → 模型 → 带情感的语音
```

方法：
- 情感嵌入 + 条件注入
- 参考音频情感迁移
- 文本语义理解 → 自动情感推断

### 5.2 多语言/跨语言 TTS

挑战：
- 不同语言的音素集不同
- 语调和节奏差异大
- 代码切换（中英混合）处理

方案：
- 统一音素集（IPA 国际音标）
- 多语言数据混合训练
- 语言标识嵌入

### 5.3 个性化 TTS

- 说话人自适应：少量数据微调
- 零样本克隆：3 秒参考音频
- 风格迁移：参考音频的说话风格

## 6. 实践：TTS 模型选择指南

```
需要什么？

├─ 研究/学习 → VITS (代码清晰，易于修改)
├─ 生产部署
│   ├─ 中文 → CosyVoice / Bert-VITS2
│   ├─ 英文 → VITS / FastSpeech 2
│   └─ 多语言 → CosyVoice
├─ 声音克隆
│   ├─ 开源 → F5-TTS / CosyVoice / OpenVoice
│   └─ 最佳质量 → VALL-E (需大量数据训练)
├─ 实时对话 → 流式 TTS + 低延迟声码器
└─ 高质量离线 → NaturalSpeech 3 / 两阶段系统
```

## 7. 本章小结

TTS 技术经历了三个阶段：

1. **拼接/参数时代**（~2015）：依赖录音库和统计模型
2. **神经 TTS 时代**（2016-2022）：Tacotron → FastSpeech → VITS
3. **大模型时代**（2023+）：VALL-E → CosyVoice → GPT-4o

核心趋势是**统一化**——从多阶段 pipeline 走向单一模型，从需要大量数据走向零样本，从纯语音走向多模态。

---

> **上一章**：[第 3 章：深度学习基础与音频建模入门](./03-deep-learning-audio-basics.md)
>
> **下一章**：[第 5 章：声码器——从特征到波形](./05-vocoder.md)

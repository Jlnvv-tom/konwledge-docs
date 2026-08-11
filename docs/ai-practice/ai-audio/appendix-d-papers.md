# 附录 D：推荐论文清单

> **《语音与音乐的机器之魂》附录**

---

## 里程碑论文（按时间排序）

### 1. 语音识别

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 1 | 2011 | "Context-dependent pre-trained DNN-HMMs for LVCSR" (Dahl) | DNN 替换 GMM |
| 2 | 2014 | "DeepSpeech: Scaling up end-to-end speech recognition" | 端到端 ASR |
| 3 | 2014 | "Towards End-to-End Speech Recognition with RNN" (Graves) | CTC 损失 |
| 4 | 2016 | "Listen, Attend and Spell" (Chan & Vinyals) | Attention ASR |
| 5 | 2020 | "wav2vec 2.0" (Baevski) | 自监督预训练 |
| 6 | 2022 | "Robust Speech Recognition via Large-Scale Weak Supervision" (Radford) | Whisper |

### 2. 语音合成（TTS）

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 7 | 2016 | "WaveNet: A Generative Model for Raw Audio" (Oord) | 神经 TTS 里程碑 |
| 8 | 2017 | "Natural TTS Synthesis by Conditioning WaveNet on Mel Spectrogram" | Tacotron 2 |
| 9 | 2019 | "FastSpeech: Fast, Robust and Controllable TTS" | 非自回归 TTS |
| 10 | 2020 | "FastSpeech 2: Fast and High-Quality End-to-End TTS" | 音高/能量控制 |
| 11 | 2021 | "VITS: Conditional Variational Autoencoder with Adversarial Learning" | 端到端 TTS |
| 12 | 2023 | "VALL-E: Neural Codec Language Models are Zero-Shot TTS" | LLM 范式 TTS |
| 13 | 2024 | "CosyVoice: A Scalable Multilingual Zero-Shot TTS System" | 开源零样本 |
| 14 | 2024 | "F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching" | 纯流匹配 |

### 3. 声码器

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 15 | 2019 | "MelGAN: Generative Adversarial Networks for Conditional Waveform Synthesis" | 轻量 GAN 声码器 |
| 16 | 2020 | "HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis" | 事实标准 |
| 17 | 2022 | "BigVGAN: A Universal Neural Vocoder with Large-Scale Training" | 更高质量 |

### 4. 声音克隆

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 18 | 2020 | "YourTTS: Towards Zero-Shot Multi-Speaker TTS and Zero-Shot Voice Conversion" | 少样本多说话人 |
| 19 | 2023 | "Voicebox: Text-Guided Multilingual Universal Speech Generation" | 流匹配多功能 |
| 20 | 2023 | "NaturalSpeech 3: Zero-Shot Voice Cloning with Self-Supervised Disentangled Representation" | 扩散+VQ |

### 5. 音乐生成

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 21 | 2020 | "Jukebox: A Generative Model for Music" | 完整歌曲生成 |
| 22 | 2023 | "MusicLM: Generating Music From Text" | 两阶段音乐生成 |
| 23 | 2023 | "Simple and Controllable Music Generation: MusicGen" | 开源音乐生成标准 |
| 24 | 2018 | "Music Transformer: Generating Music with Long-Term Structure" | 相对位置注意力 |

### 6. 歌声合成

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 25 | 2021 | "DiffSinger: Singing Voice Synthesis with Shallow Diffusion Mechanism" | 扩散歌声合成 |

### 7. 音频编码与 Token 化

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 26 | 2021 | "SoundStream: An End-to-End Neural Audio Codec" | 音频 Tokenizer |
| 27 | 2022 | "High-Fidelity Audio Compression with EnCodec" | 8 层码本标准 |
| 28 | 2024 | "WavTokenizer: An Efficient Acoustic Discrete Codec Tokenizer" | 单码本高压缩 |

### 8. 多模态与语音大模型

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 29 | 2024 | "GPT-4o System Card" | 原生多模态语音交互 |
| 30 | 2023 | "AudioLM: A Language Modeling Approach to Audio Generation" | 音频语言建模 |
| 31 | 2024 | "Qwen-Audio: Advancing Universal Audio Understanding" | 多模态理解 |

### 9. 深度伪造检测

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 32 | 2024 | "AudioSeal: Proactive Localization of AI-Generated Speech" | 主动水印 |

### 10. 可微 DSP

| # | 年份 | 论文 | 意义 |
|---|------|------|------|
| 33 | 2020 | "DDSP: Differentiable Digital Signal Processing" | 神经+物理融合 |

---

## 论文阅读建议

### 入门顺序

```
1. WaveNet (2016)     — 理解音频生成基础
2. Tacotron 2 (2017)  — 理解 TTS pipeline
3. HiFi-GAN (2020)    — 理解声码器
4. VITS (2021)        — 理解端到端 TTS
5. wav2vec 2.0 (2020) — 理解自监督
6. Whisper (2022)     — 理解弱监督
7. VALL-E (2023)      — 理解 LLM 范式
8. MusicGen (2023)    — 理解音乐生成
```

### 按主题深入

```
TTS 全链路:
  Tacotron 2 → FastSpeech 2 → VITS → VALL-E → CosyVoice

ASR 全链路:
  DeepSpeech → CTC/LAS → RNN-T → wav2vec 2.0 → Whisper

音乐生成:
  Music Transformer → Jukebox → MusicLM → MusicGen

声音克隆:
  YourTTS → VALL-E → Voicebox → F5-TTS

音频 Token 化:
  SoundStream → EnCodec → WavTokenizer
```

---

## 总结

这 33 篇论文涵盖了语音与音乐 AI 的主要技术里程碑。从 2016 年的 WaveNet 到 2024 年的 GPT-4o，8 年间音频 AI 经历了从"能发声"到"能对话"的质变。

建议读者按照入门顺序逐篇精读，配合开源代码复现，可以建立完整的技术认知体系。

---

> **上一附录**：[附录 C：开源项目索引](./appendix-c-projects.md)
>
> **返回**：[书籍总目录](./index.md)

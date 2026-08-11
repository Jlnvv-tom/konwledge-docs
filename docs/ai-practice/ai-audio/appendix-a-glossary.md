# 附录 A：术语表

> **《语音与音乐的机器之魂》附录**

---

## A-Z 英文术语

| 术语 | 中文 | 释义 |
|------|------|------|
| AEC | 回声消除 | 消除扬声器到麦克风的回声，全双工通信必需 |
| ADSR | 起音-衰减-延音-释放 | 声音时间包络的四个阶段 |
| AM | 声学模型 | ASR/TTS 中建模声学的模型 |
| ASR | 自动语音识别 | 将语音转为文本 |
| Attention | 注意力机制 | 神经网络中选择性关注输入的机制 |
| Audio Token | 音频令牌 | 将连续音频离散化为 token 序列 |
| Bert-VITS2 | — | 基于 BERT 的 VITS 改进版 |
| BigVGAN | — | 增强版 HiFi-GAN，更高质量 |
| C2PA | 内容来源认证 | 内容真实性和来源的技术标准 |
| CFG | 分类器自由引导 | 平衡生成质量和条件控制的技术 |
| CTC | 连接时序分类 | 端到端 ASR 的损失函数 |
| DAC | Descript Audio Codec | 高压缩率音频 Tokenizer |
| DDSP | 可微数字信号处理 | 将 DSP 嵌入神经网络 |
| Demucs | — | Meta 的源分离模型 |
| DNN | 深度神经网络 | 多层神经网络 |
| ECAPA-TDNN | — | 当前最优说话人编码模型 |
| EnCodec | — | Meta 的音频编码器，8 层码本 |
| F0 | 基频 | 声音的基本频率，决定音高 |
| FAD | Fréchet 音频距离 | 音乐生成的客观评估指标 |
| FastSpeech | — | 非自回归 TTS 模型 |
| FiLM | 特征线性调制 | 条件注入方法 |
| Flash Attention | — | 高效注意力实现 |
| FSDP | 全分片数据并行 | 大模型分布式训练策略 |
| GAN | 生成对抗网络 | 生成器和判别器对抗训练 |
| GMM | 高斯混合模型 | 传统 ASR 声学模型 |
| GPT-4o | — | OpenAI 原生多模态模型 |
| Griffin-Lim | — | 从幅度谱重建波形的算法 |
| HiFi-GAN | — | 当前标准声码器 |
| HMM | 隐马尔可夫模型 | 传统时序建模方法 |
| HuBERT | — | 迭代聚类的自监督语音预训练 |
| IPA | 国际音标 | 语言的标准化音素表示 |
| Jukebox | — | OpenAI 的歌曲生成模型 |
| KV Cache | KV 缓存 | 自回归推理的缓存优化 |
| LCM | 线性复杂度注意力 | 替代标准注意力 |
| LibriSpeech | — | 经典英文 ASR/TTS 数据集 |
| LPC | 线性预测编码 | 语音参数表示方法 |
| Mamba | — | 线性复杂度状态空间模型 |
| MAESTRO | — | 古典钢琴 MIDI+音频数据集 |
| Mel 频谱 | 梅尔频谱 | 模拟人耳感知的频谱表示 |
| MFCC | 梅尔频率倒谱系数 | 传统语音特征 |
| MIR | 音乐信息检索 | 音乐分析的研究领域 |
| MOS | 平均意见分 | 5 分制主观质量评分 |
| MPD | 多周期判别器 | HiFi-GAN 的判别器 |
| MSD | 多尺度判别器 | HiFi-GAN 的判别器 |
| MusicGen | — | Meta 的开源音乐生成模型 |
| MusicLM | — | Google 的音乐生成模型 |
| MUSHRA | — | 多激励隐藏参照主观评测 |
| NAR | 非自回归 | 一次前向生成全部输出 |
| NSynth | — | Google 的单音乐器数据集 |
| Opus | — | 低延迟音频编码格式 |
| PCM | 脉冲编码调制 | 原始数字音频格式 |
| Piano Roll | 钢琴卷帘 | (时间, 音高) 二维矩阵表示 |
| RAVE | 实时音频 VAE | 实时音频变分自编码器 |
| REMI | — | 为 Transformer 设计的 MIDI 表示 |
| ResNet | 残差网络 | 带跳跃连接的深度网络 |
| RNN-T | RNN 转换器 | 流式 ASR 的主流模型 |
| RTF | 实时率 | 处理时间与音频时长的比值 |
| RVC | 检索式声音转换 | 社区最流行的声音转换工具 |
| RVQ | 残差矢量量化 | 多层码本逐步量化 |
| SIM | 说话人相似度 | 说话人嵌入的余弦相似度 |
| So-VITS-SVC | — | 基于 VITS 的歌声转换 |
| SpecAugment | — | 频谱掩码数据增强 |
| SR | 采样率 | 每秒采样点数 |
| STFT | 短时傅里叶变换 | 时频分析工具 |
| SVD | 歌声合成 | Singing Voice Synthesis |
| SVS | 歌声合成 | 从乐谱生成歌声 |
| Suno | — | 消费级 AI 歌曲生成产品 |
| SV | 说话人验证 | 确认说话人身份 |
| TTS | 文本转语音 | Text-To-Speech |
| VAD | 语音活动检测 | 检测音频中的语音段 |
| VALL-E | — | Microsoft 零样本 TTS 里程碑 |
| VITS | — | 端到端 TTS 模型 |
| VQ-VAE | 矢量量化 VAE | 离散表示学习 |
| wav2vec 2.0 | — | 自监督语音预训练 |
| WER | 词错率 | ASR 的核心评估指标 |
| Whisper | — | OpenAI 的多语言 ASR |
| WORLD | — | 歌声合成声码器 |
| YuE | — | 腾讯开源歌曲生成模型 |

---

> **下一附录**：[附录 B：数据集索引](./appendix-b-datasets.md)

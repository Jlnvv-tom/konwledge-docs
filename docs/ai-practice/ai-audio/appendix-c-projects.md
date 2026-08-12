---
sidebar_position: 26
---

# 附录 C：开源项目索引

> **《语音与音乐的机器之魂》附录**

---

## TTS 项目

| 项目 | 语言 | 特点 | GitHub |
|------|------|------|--------|
| VITS | — | 端到端 TTS 基线 | jaywalnut310/vits |
| Bert-VITS2 | 中文 | BERT 增强 VITS | fishaudio/Bert-VITS2 |
| CosyVoice | 多语言 | 零样本，阿里出品 | FunAudioLLM/CosyVoice |
| F5-TTS | 多语言 | 纯流匹配 | SWivid/F5-TTS |
| OpenVoice | 多语言 | 轻量声音克隆 | myshell-ai/OpenVoice |
| ChatTTS | 中文 | 对话式 TTS | 2noise/ChatTTS |
| GPT-SoVITS | 中文 | 少样本克隆 | RVC-Boss/GPT-SoVITS |
| FastSpeech 2 | 英文 | 非自回归 | ming024/FastSpeech2 |
| Tacotron 2 | 英文 | 经典基线 | NVIDIA/DeepLearningExamples |
| Coqui TTS | 多语言 | 商业级开源 | coqui-ai/TTS |
| ESPnet-TTS | 多语言 | 研究框架 | espnet/espnet |

## ASR 项目

| 项目 | 特点 | GitHub |
|------|------|--------|
| Whisper | OpenAI 多语言 ASR | openai/whisper |
| FunASR | 阿里中文 ASR | modelscope/FunASR |
| wav2vec 2.0 | 自监督预训练 | facebookresearch/fairseq |
| HuBERT | 迭代聚类自监督 | facebookresearch/fairseq |
| Kaldi | 经典 ASR 框架 | kaldi-asr/kaldi |
| ESPnet | 端到端 ASR | espnet/espnet |
| NeMo | NVIDIA 语音工具包 | NVIDIA/NeMo |
| Wav2Letter++ | Facebook ASR | facebookresearch/wav2letter |
| WhisperX | Whisper + 对齐 | m-bain/whisperX |

## 声码器

| 项目 | 特点 | GitHub |
|------|------|--------|
| HiFi-GAN | 事实标准 | jik876/hifi-gan |
| BigVGAN | 增强版 | NVIDIAGames/BigVGAN |
| MelGAN | 轻量 | ksw0306/ClariNet |
| WaveGlow | 流模型 | NVIDIA/waveglow |
| Parallel WaveNet | 蒸馏 | — |
| UnivNet | 小波判别器 | maum-ai/univnet |

## 音乐生成

| 项目 | 特点 | GitHub |
|------|------|--------|
| MusicGen | Meta 开源音乐生成 | facebookresearch/audiocraft |
| Stable Audio | 潜在扩散 | stability-AI/stable-audio-tools |
| YuE | 开源歌曲生成 | m-a-p/YuE |
| Jukebox | OpenAI 歌曲 | openai/jukebox |
| AudioLDM | 潜在扩散音频 | haoheliu/audioldm |
| Riffusion | spectrogram 扩散 | riffusion/riffusion |
| Music Transformer | 符号生成 | — |
| REMI Transformer | REMI 表示 | — |

## 歌声相关

| 项目 | 特点 | GitHub |
|------|------|--------|
| DiffSinger | 扩散歌声合成 | OpenVPI/DiffSinger |
| so-vits-svc | 歌声转换 | voicepaw/so-vits-svc |
| RVC | 检索式声音转换 | RVC-Project/Retrieval-based-Voice-Conversion |
| OpenUtau | 现代化 UTAU | stakira/OpenUtau |
| NSF-HiFiGAN | 歌声声码器 | openvpi/DiffSinger |

## 音频处理

| 项目 | 特点 | GitHub |
|------|------|--------|
| Demucs | 源分离 | facebookresearch/demucs |
| RNNoise | 实时降噪 | xiph/rnnoise |
| AudioSeal | 音频水印 | facebookresearch/audioseal |
| librosa | 音频分析 | librosa/librosa |
| torchaudio | PyTorch 音频 | pytorch/audio |
| pydub | 简易音频处理 | jiaaro/pydub |
| ffmpeg-python | FFmpeg 封装 | kkroening/ffmpeg-python |

## 框架与平台

| 项目 | 特点 | GitHub |
|------|------|--------|
| ESPnet | 端到端语音 | espnet/espnet |
| NeMo | NVIDIA 语音 | NVIDIA/NeMo |
| fairseq | Meta 研究框架 | facebookresearch/fairseq |
| AudioCraft | Meta 音频生成 | facebookresearch/audiocraft |
| Transformers | HuggingFace | huggingface/transformers |
| DeepSpeed | 分布式训练 | microsoft/DeepSpeed |

## 按需求推荐

```
入门 TTS → VITS / Bert-VITS2
声音克隆 → CosyVoice / F5-TTS / OpenVoice
ASR → Whisper / FunASR
音乐生成 → MusicGen / Stable Audio
歌声 → DiffSinger / RVC
源分离 → Demucs
研究框架 → ESPnet / NeMo / AudioCraft
```

---

> **上一附录**：[附录 B：数据集索引](./appendix-b-datasets.md)
>
> **下一附录**：[附录 D：推荐论文清单](./appendix-d-papers.md)

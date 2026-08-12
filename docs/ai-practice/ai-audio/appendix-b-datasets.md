---
sidebar_position: 25
---

# 附录 B：数据集索引

> **《语音与音乐的机器之魂》附录**

---

## 语音数据集

### ASR 数据集

| 数据集 | 语言 | 时长 | 特点 | 链接 |
|--------|------|------|------|------|
| LibriSpeech | 英文 | 960h | 有声书，干净朗读 | openslr.org/12 |
| LibriHeavy | 英文 | 50000h | LibriSpeech 超大版 | github.com/Kdaiy/ |
| Common Voice | 100+ | 20000h+ | 众包，多口音 | commonvoice.mozilla.org |
| WenetSpeech | 中文 | 10000h | 互联网音频 | openslr.org |
| GigaSpeech | 英文 | 10000h | 多领域 | github.com/SpeechColab |
| MLS | 8 语言 | 50000h | 多语言 | openslr.org/94 |
| AISHELL-1 | 中文 | 178h | 普通话朗读 | openslr.org/33 |
| AISHELL-3 | 中文 | 85h | 多说话人 TTS | openslr.org/93 |
| Primewords | 中文 | 99h | 普通话 | openslr.org/47 |
| MagicData | 中文 | 755h | 方言+普通话 | openslr.org/68 |

### TTS 数据集

| 数据集 | 语言 | 时长 | 特点 |
|--------|------|------|------|
| LJSpeech | 英文 | 24h | 单说话人女声 |
| VCTK | 英文 | 44h | 110 说话人 |
| LibriTTS | 英文 | 585h | 多说话人 |
| AISHELL-3 | 中文 | 85h | 218 说话人 |
| Baker | 中文 | 12h | 单说话人女声 |
| Opencpop | 中文 | 5h | 歌声（专业歌手） |

### 说话人识别

| 数据集 | 规模 | 特点 |
|--------|------|------|
| VoxCeleb 1 | 1251 说话人 | YouTube 视频 |
| VoxCeleb 2 | 6112 说话人 | 更大规模 |
| CN-Celeb | 1000 说话人 | 中文名人 |

## 音乐数据集

### MIDI/符号

| 数据集 | 规模 | 特点 |
|--------|------|------|
| Lakh MIDI | 176K 首 | 多流派 |
| MAESTRO | 200h | 钢琴 MIDI+音频 |
| Hooktheory | 15K 首 | 和弦+旋律 |
| JSB Chorales | 382 首 | 巴赫四声部 |
| Nottingham | 1200 首 | 民谣旋律 |

### 音频

| 数据集 | 规模 | 特点 |
|--------|------|------|
| FMA | 106K 首 | 多流派 |
| MTG-Jamendo | 5586 首 | CC 授权 |
| MUSDB18 | 150 首 | 分轨 |
| MusicCaps | 5.5K 首 | Google 文本标注 |
| MagnaTagATune | 25K 首 | 标签 |

### 音色/单音

| 数据集 | 规模 | 特点 |
|--------|------|------|
| NSynth | 306K 样本 | 1000+ 乐器 |
| Philharmonia | ~4K 样本 | 交响乐器单音 |
| Iowa MIS | ~1K 样本 | 传统乐器 |

### 多模态

| 数据集 | 规模 | 特点 |
|--------|------|------|
| MusicCaps | 5.5K | 文本+音频 |
| Million Song | 1M | 元数据+音频特征 |
| Last.fm | 1M | 标签+音频 |

## 数据集选择决策树

```
你的任务是什么？

├─ ASR 训练
│   ├─ 英文 → LibriSpeech / GigaSpeech
│   ├─ 中文 → WenetSpeech / AISHELL
│   └─ 多语言 → MLS / Common Voice
│
├─ TTS 训练
│   ├─ 英文 → LJSpeech / VCTK / LibriTTS
│   ├─ 中文 → AISHELL-3 / Baker
│   └─ 歌声 → Opencpop
│
├─ 说话人识别 → VoxCeleb 1/2
│
├─ 音乐生成
│   ├─ 符号 → Lakh MIDI / MAESTRO
│   ├─ 音频 → FMA / MTG-Jamendo
│   └─ 文本条件 → MusicCaps
│
├─ 音色研究 → NSynth
│
├─ 源分离 → MUSDB18
│
└─ 自监督预训练 → LibriHeavy / MLS
```

---

> **上一附录**：[附录 A：术语表](./appendix-a-glossary.md)
>
> **下一附录**：[附录 C：开源项目索引](./appendix-c-projects.md)

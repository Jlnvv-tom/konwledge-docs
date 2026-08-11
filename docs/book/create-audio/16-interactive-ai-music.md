# 第 16 章：交互式 AI 音乐工具与实践

> **系列文章：《语音与音乐的机器之魂》**
> AI 不只是"一键生成"，更是创作伙伴。本章介绍源分离、AI 混音、实时音乐生成等工具，并给出 MusicGen 实战代码。

---

## 1. 实时音乐生成

### 1.1 应用场景

| 场景 | 需求 | 技术方案 |
|------|------|----------|
| 游戏自适应音乐 | 根据游戏情境变化 | 参数化生成 + 交叉淡入淡出 |
| 健身/冥想 App | 根据心率调整 | 实时 BPM 控制 |
| 直播/播客 | 背景音乐 | 预生成 + 智能切换 |
| 交互装置艺术 | 观众参与生成 | 传感器 → 条件 → 生成 |
| DJ 助手 | 实时混音建议 | 节拍检测 + 推荐 |

### 1.2 技术方案

#### 预生成 + 交叉淡入淡出

```
游戏状态: 探索 → 战斗 → 胜利
  ↓
预生成: [探索音乐] [战斗音乐] [胜利音乐]
  ↓
交叉淡入淡出: ---探索---↘---战斗---↘---胜利---
                         (2s)         (2s)
```

- 最简单可靠
- 无实时生成压力
- 但变化有限

#### 实时 Token 生成

```python
# MusicGen 流式生成（概念）
buffer = []
for chunk in model.generate_stream(description="ambient", chunk_size=2.0):
    buffer.append(chunk)
    if len(buffer) >= 3:
        audio = concatenate_and_crossfade(buffer)
        play(audio)
        buffer = buffer[1:]  # 滑动窗口
```

- 更灵活的实时变化
- 但需 GPU 持续运行
- 边界可能不连贯

## 2. AI 音乐编辑工具

### 2.1 源分离（Stem Separation）

将混音分离为独立轨道：

```
混音音频 → 源分离模型 → 人声 / 鼓 / 贝斯 / 其他
```

#### Demucs（Meta）

当前最先进的源分离模型：

```
混合域架构:
  时域: 编码器 → 瓶颈 → 解码器
  频域: STFT → Transformer → 逆STFT
  → 两域输出融合
```

```python
# 使用 Demucs
import torch
import torchaudio

model = torch.hub.load('facebookresearch/demucs', 'htdemucs')
audio, sr = torchaudio.load('song.wav')
sources = model(audio.unsqueeze(0))  # [1, n_sources, channels, samples]
# sources: vocals, drums, bass, other
```

#### 源分离模型对比

| 模型 | 质量 | 速度 | 特点 |
|------|------|------|------|
| Demucs v4 (HTDemucs) | ⭐⭐⭐⭐⭐ | 中 | 最先进 |
| Spleeter | ⭐⭐⭐ | 快 | 速度快 |
| BS-RoofExtformer | ⭐⭐⭐⭐ | 中 | 频域方法 |
| Demucs ftc | ⭐⭐⭐⭐ | 中 | 基础版 |

### 2.2 AI 混音/母带

```
输入: 多轨道录音
  → AI 分析: 频率分布、动态范围、空间信息
  → AI 建议: EQ、压缩、混响参数
  → 自动混音: 应用参数 + 响度匹配
  → AI 母带: 最终响度/色彩/宽度
```

| 工具 | 功能 | 特点 |
|------|------|------|
| Landr | AI 母带 | 在线服务 |
| eMastered | AI 母带 | 可调参数 |
| Ozone (iZotope) | AI 辅助混音 | 专业插件 |
| ROEX | 自动混音 | 在线平台 |
| Moises | 分轨+混音 | 移动端 |

### 2.3 AI 音高修正

超越传统 Auto-Tune：

```
输入: 略微走调的人声
  → AI 检测: F0 轨迹 vs 目标音高
  → AI 修正: PSOLA 或神经修正
  → 输出: 音准修正的人声（保留歌手特色）
```

关键区别：
- 传统 Auto-Tune：机械式音高移位，有"电音"效果
- AI 修正：保留颤音、气声等特征，更自然

## 3. 音乐创作辅助

### 3.1 旋律/和弦建议

```
给定旋律 → 建议和弦进行
  旋律: C E G E F A C A
  → 分析: 强拍音 C, G, C → C 大调
  → 建议: C - G - Am - F (I-V-vi-IV)

给定和弦 → 建议旋律
  和弦: C - G - Am - F
  → 建议: C E G | D G B | C E A | C F A
```

### 3.2 风格迁移

```
"用爵士风格重新编排这首流行歌"
  → 分析原曲: 和弦、旋律、节奏
  → 爵士化: 替换为爵士和弦（九和弦/十一和弦）
  → 改变节奏: swing 感
  → 添加装饰: 蓝调音阶、即兴乐句
```

### 3.3 采样与 Loop 生成

```
"生成一段 120 BPM 的 lo-fi 鼓点 Loop"
  → AI 生成: kick on 1,3 / snare on 2,4 / hihat 16th
  → 添加人类感: 轻微时间偏移、力度变化
  → 无缝循环
```

## 4. 实践：用 MusicGen 生成音乐

### 4.1 环境准备

```bash
# 方式1: audiocraft
pip install audiocraft

# 方式2: transformers
pip install transformers torch accelerate
```

### 4.2 基本生成

```python
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

# 加载预训练模型
model = MusicGen.get_pretrained('facebook/musicgen-large')

# 设置生成参数
model.set_generation_params(
    duration=30,              # 生成30秒
    use_sampling=True,        # 采样模式
    top_k=250,               # Top-K 采样
    top_p=0.0,               # Top-P
    temperature=1.0,         # 温度
    cfg_coef=3.0             # CFG 强度
)

# 文本到音乐
descriptions = [
    "80s pop track with heavy synth and drums, upbeat and energetic",
    "lo-fi hip hop for studying, mellow piano, vinyl crackle, rainy mood",
    "epic orchestral cinematic, rising tension, war drums, heroic theme"
]

wav = model.generate(descriptions)

# 保存
for idx, one_wav in enumerate(wav):
    audio_write(
        f'musicgen_output_{idx}', 
        one_wav.cpu(), 
        model.sample_rate, 
        strategy="loudness",
        loudness_compressor=True
    )
```

### 4.3 旋律条件生成

```python
import torchaudio

# 加载旋律模型
model = MusicGen.get_pretrained('facebook/musicgen-melody')
model.set_generation_params(duration=30)

# 加载参考音频
melody, sr = torchaudio.load('reference_melody.wav')
# 如果采样率不同，需要重采样
if sr != model.sample_rate:
    resampler = torchaudio.transforms.Resample(sr, model.sample_rate)
    melody = resampler(melody)

# 用参考旋律生成新音乐
wav = model.generate_with_chroma(
    descriptions=[
        "electronic dance cover with heavy bass",
        "acoustic guitar fingerstyle version"
    ],
    melody=melody[None].expand(2, -1, -1),  # 扩展到 batch
    sample_rate=sr
)
```

### 4.4 使用 Transformers 库

```python
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import torch

processor = AutoProcessor.from_pretrained('facebook/musicgen-large')
model = MusicgenForConditionalGeneration.from_pretrained('facebook/musicgen-large')

inputs = processor(
    text=["happy upbeat electronic music with fast beats"],
    padding=True,
    return_tensors="pt"
)

# 生成
audio_values = model.generate(
    **inputs,
    max_new_tokens=1500,    # 约30秒
    do_sample=True,
    guidance_scale=3.0
)

# 保存
sampling_rate = model.config.audio_encoder.sampling_rate
torchaudio.save('output.wav', audio_values[0, 0].cpu(), sampling_rate)
```

### 4.5 微调 MusicGen

```python
# 概念：在自己的音乐数据上微调
from audiocraft.models import MusicGen
import torch

model = MusicGen.get_pretrained('facebook/musicgen-medium')

# 准备数据
train_dataset = YourMusicDataset(
    audio_dir='your_music/',
    descriptions='descriptions.json'
)

# 微调
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
for epoch in range(10):
    for batch in train_dataset:
        audio, text = batch
        loss = model.compute_loss(audio, text)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
```

## 5. AI 音乐工具生态

### 5.1 完整工具链

```
创作:
  - 歌词: ChatGPT/Claude
  - 旋律: MusicGen/AIVA
  - 编曲: Soundraw/BandLab
  
演唱:
  - 歌声合成: DiffSinger/SynthV
  - 声音转换: RVC
  
后期:
  - 源分离: Demucs
  - 混音: Ozone/ROEX
  - 母带: Landr
  
发布:
  - 分发: DistroKid/TuneCore
  - 版权注册: AI 生成内容的版权处理
```

### 5.2 推荐工具组合

**入门（零基础）：**
```
Suno/Udio（一键生成）+ 简单描述
```

**进阶（有 DAW 经验）：**
```
LLM 歌词 + MusicGen 旋律 + DiffSinger 人声 + DAW 混音
```

**专业（音乐人）：**
```
AI 辅助（和弦建议/风格参考）+ 传统制作 + AI 后处理（母带）
```

## 6. 本章小结

交互式 AI 音乐工具覆盖了音乐制作的完整流程：

1. **生成**：MusicGen/Suno/Udio
2. **编辑**：Demucs 分轨/音高修正
3. **混音**：AI 母带/自动混音
4. **实时**：自适应音乐/流式生成

AI 不只是替代人类创作，更是作为"创作伙伴"提供灵感和辅助。未来趋势是更深度的交互——实时协作、精细控制、多模态输入。

---

> **上一章**：[第 15 章：歌词生成与歌曲级 AI 创作](./15-lyrics-song-creation.md)
>
> **下一章**：[第 17 章：数据采集、标注与清洗](./17-data-preparation.md)

# 第 13 章：符号级音乐生成（MIDI/乐谱）

> **系列文章：《语音与音乐的机器之魂》**
> 在音频生成之前，AI 先学会了"写谱"。本章梳理从 DeepBach 到现代 LLM 的符号音乐生成技术。

---

## 1. 符号生成的优势与局限

### 1.1 优势

- **序列短**：3 分钟歌曲 ≈ 2000 Token（vs 音频 400 万采样点）
- **精确可控**：音高、节奏明确无误
- **可编辑**：生成后可手动修改
- **可直接演奏**：通过虚拟乐器渲染

### 1.2 局限

- 无法表达音色和表现力
- 需要额外的音色渲染步骤
- 不包含混音、空间感等信息

## 2. 早期模型

### 2.1 DeepBach（2017）

用伪似然训练巴赫四声部赞歌生成：

```
方法:
  - 每个声部独立建模
  - 条件于其他声部和上下文
  - 基于 RNN 的音符级生成

结果:
  - 专家无法区分 AI 和真巴赫
  - 可交互式编辑（约束修改后重新生成）
```

### 2.2 Music Transformer（2018）

**Transformer 在音乐生成中的首次重要应用。**

```
输入: MIDI Token 序列（REMI 格式）
模型: Transformer（相对位置注意力）
输出: 续写的 MIDI Token
```

**关键创新：相对位置注意力**

```python
class RelativeAttention(nn.Module):
    def forward(self, q, k, v, rel_pos):
        # 传统: q·k^T
        # 相对: q·(k + rel_pos)^T
        scores = torch.matmul(q, k.transpose(-2, -1))
        rel_bias = self._relative_bias(q, rel_pos)
        scores = scores + rel_bias
        return softmax(scores) @ v
```

相对位置注意力使模型能更好地捕捉音乐中的长距离结构关系（如 4 小节后的主题回归）。

## 3. REMI 表示与流行音乐生成

REMI 格式将 MIDI 转为线性 Token 序列：

```
[Bar]                      ← 小节开始
[Position 0]               ← 位置（0=第一拍）
[Pitch 60] [Velocity 80] [Duration 1/4]   ← C4, 中等力度, 四分音符
[Position 1]
[Pitch 64] [Velocity 75] [Duration 1/4]   ← E4
[Chord C_major]            ← 和弦标记
[Bar]                      ← 下一小节
...
```

REMI 的设计使得 Transformer 可以像处理文本一样处理音乐。

## 4. 基于 LLM 的符号生成

### 4.1 MuseNet（OpenAI, 2019）

GPT-2 架构应用于音乐：

```
MIDI → Token 化 → GPT-2 (72层 Transformer) → 生成 Token → MIDI
```

特点：
- 支持 10 种乐器组合
- 最长 4 分钟生成
- 风格条件（"贝多芬风格"）
- 未开源

### 4.2 SymphonyNet / PopMAG

专门为多轨道音乐设计：
- 多轨道 Token 交织
- 乐器标识嵌入
- 全局风格控制

### 4.3 现代 LLM 范式

2024 年后的趋势是将音乐符号生成纳入通用 LLM：

```
"用 C 大调写一段轻快的钢琴旋律，4/4 拍，120 BPM"
→ GPT/Claude
→ ABC Notation / LilyPond / MIDI
→ 渲染为音频
```

通用 LLM 已具备基础的音乐符号生成能力，但专业级质量仍需专用模型。

## 5. 多轨道生成

多乐器协奏是符号生成的核心难点：

### 5.1 挑战

```
需要同时生成:
  - 鼓点轨道（节奏基础）
  - 贝斯线（与鼓点对齐，和声基础）
  - 和弦垫底（和声进行）
  - 旋律线（与和声协调）
  - 装饰轨道（弦乐、特效）
```

### 5.2 技术方案

#### 轨道间注意力

```python
class TrackWiseAttention(nn.Module):
    """每个轨道 attend 到其他轨道"""
    def forward(self, tracks):
        # tracks: [n_tracks, seq_len, dim]
        for i in range(n_tracks):
            for j in range(n_tracks):
                if i != j:
                    tracks[i] = tracks[i] + cross_attn(tracks[i], tracks[j])
        return tracks
```

#### 层次化生成

```
层次1: 生成全局结构（段落、调性、BPM）
  ↓
层次2: 生成和弦进行
  ↓
层次3: 生成各轨道旋律（条件于和弦）
  ↓
层次4: 生成细节（装饰音、力度变化）
```

#### 约束解码

确保生成的音乐符合音乐理论规则：

```python
def constrained_decoding(logits, music_context):
    """在解码时强制音乐理论约束"""
    # 1. 只允许调内音
    allowed_pitches = get_scale_pitches(music_context.key)
    logits = mask_pitches(logits, allowed_pitches)
    
    # 2. 强拍上更可能是和弦音
    if music_context.is_strong_beat:
        chord_pitches = get_chord_pitches(music_context.current_chord)
        logits = boost_pitches(logits, chord_pitches, factor=1.5)
    
    # 3. 避免平行五度/八度（古典规则）
    if music_context.voice_leading_check:
        forbidden = get_forbidden_intervals(music_context)
        logits = mask_pitches(logits, forbidden)
    
    return logits
```

## 6. 旋律与和弦的联合生成

```
输入: "写一段 C 大调的流行旋律"
  ↓
步骤1: 生成和弦进行 C - G - Am - F
  ↓
步骤2: 逐小节生成旋律
  - 小节1 (C和弦): 旋律优先 C E G
  - 小节2 (G和弦): 旋律优先 G B D
  - 小节3 (Am和弦): 旋律优先 A C E
  - 小节4 (F和弦): 旋律优先 F A C
```

## 7. 符号生成的评估

### 7.1 客观指标

| 指标 | 描述 |
|------|------|
| Pitch Entropy | 音高多样性 |
| Rhythm Entropy | 节奏多样性 |
| Chord Consistency | 和弦一致性 |
| Scale Consistency | 调性一致性 |
| Groove Consistency | 律动一致性 |

### 7.2 主观评估

- 音乐性：听起来像真正的音乐吗？
- 结构性：有清晰的段落和主题吗？
- 创意性：是否有新意？
- 可用性：能直接使用吗？

## 8. 本章小结

符号级生成是音乐 AI 的"骨架"——提供结构和可控性：

```
DeepBach (2017) → Music Transformer (2018) → REMI (2020) → LLM (2024)
```

关键洞察：
1. 好的表示（REMI）比更大的模型更重要
2. 音乐理论约束可以在解码阶段注入
3. 多轨道协调是核心挑战
4. 符号生成 + 音频渲染 = 完整的音乐生成 pipeline

---

> **上一章**：[第 12 章：音乐理论基础与 AI 表示](./12-music-theory-ai.md)
>
> **下一章**：[第 14 章：音频级音乐生成](./14-audio-music-generation.md)

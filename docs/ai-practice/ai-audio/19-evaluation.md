---
sidebar_position: 19
---

# 第 19 章：评估指标与主观评测

> **系列文章：《语音与音乐的机器之魂》**
> 语音/音乐 AI 的评估远比图像/文本复杂——"好不好听"是主观的。本章系统介绍客观指标和主观评测方法。

---

## 1. 评估的挑战

```
图像: PSNR/SSIM/FID → 客观指标与人类感知高度相关
文本: BLEU/ROUGE → 有争议但可用
音频: ???
  - PESQ/STOI → 仅适用于窄带语音
  - Mel L1 → 低分不一定差
  - FAD → 分布距离，不反映单条质量
  - MOS → 主观，昂贵，不可重复
```

音频评估的根本困难：**感知质量是多维度的、主观的、上下文依赖的**。

## 2. TTS 评估

### 2.1 客观指标

| 指标 | 描述 | 说明 |
|------|------|------|
| Mel Cepstral Distortion (MCD) | Mel 倒谱距离 | 越低越好 |
| F0 RMSE | 基频误差 | 越低越好 |
| F0 CORR | 基频相关性 | 越高越好 |
| Duration Error | 时长误差 | 越低越好 |
| Character Error Rate (CER) | 字错率（可懂度） | 越低越好 |
| Speaker SIM | 说话人相似度 | 越高越好 |

#### MCD 计算

```python
def mcd(target_mel, pred_mel, n_mfcc=13):
    """Mel Cepstral Distortion"""
    # 将 Mel 转为 MFCC
    target_mfcc = mel_to_mfcc(target_mel, n_mfcc)
    pred_mfcc = mel_to_mfcc(pred_mel, n_mfcc)
    
    # 帧级距离
    dist = np.sqrt(np.sum((target_mfcc - pred_mfcc) ** 2, axis=1))
    
    # 平均（MCD 标准化系数 = 10√2 / ln10）
    mcd = 10 * np.sqrt(2) / np.log(10) * np.mean(dist)
    return mcd
```

**MCD 参考：**
- MCD < 3.0：优秀
- MCD 3.0-5.0：良好
- MCD 5.0-7.0：可接受
- MCD > 7.0：需改进

### 2.2 主观评测

#### MOS（Mean Opinion Score）

5 分制，最广泛使用的主观评测方法：

```
5 = Excellent (完全自然)
4 = Good (基本自然，偶尔有瑕疵)
3 = Fair (可接受，有明显问题)
2 = Poor (不自然)
1 = Bad (无法理解)
```

**MOS 评测规范：**
- 至少 20 名评测者
- 随机顺序播放
- 包含参照样本（金标和劣质样本）
- 安静环境，耳机
- 报告均值 + 95% 置信区间

#### CMOS（Comparison MOS）

比较两个系统：

```
A 明显好于 B: +3
A 略好于 B:   +1
A 与 B 相同:   0
A 略差于 B:   -1
A 明显差于 B: -3
```

#### MUSHRA（Multiple Stimuli with Hidden Reference）

多系统同时评测，专业音频质量评估标准：

```
- 参照样本（100分）
- 隐藏参照（混在测试中）
- 测试样本（多个系统）
- 低质量锚点（确保打分范围）

评测者: 对每个样本打分 0-100
```

### 2.3 自动主观评测

用 AI 模型模拟人类评测：

```python
# NISQA: 神经网络预测语音质量
from nisqa import NISQA
predictor = NISQA()
mos_prediction = predictor.predict('audio.wav')  # 预测 MOS 分
```

| 工具 | 方法 | 适用 |
|------|------|------|
| NISQA | CNN + Self-Attention | 通信语音质量 |
| DNSMOS | DNS 挑战赛训练 | 去噪后质量 |
| UTMOS | 多领域 MOS 预测 | TTS 质量 |
| NRMOS | 神经参考 MOS | 通用语音 |

## 3. ASR 评估

### 3.1 WER/CER

```
WER = (S + D + I) / N
S: 替换  D: 删除  I: 插入  N: 总词数
```

**WER 详解示例：**

```
参考: the cat sat on the mat
识别: the cat in the mat

S=0, D=1 (sat), I=1 (in), N=6
WER = (0+1+1)/6 = 33%
```

### 3.2 实时性指标

| 指标 | 描述 | 目标 |
|------|------|------|
| RTF | 实时率（处理时间/音频时长） | < 1.0 |
| 首字延迟 | 从开始说话到出第一个字 | < 500ms |
| 尾字延迟 | 从说完到出最后一个字 | < 300ms |
| 吞吐量 | 每秒处理音频时长 | > 5× 实时 |

### 3.3 鲁棒性评测

```
测试条件矩阵:
  - SNR: [clean, 20dB, 15dB, 10dB, 5dB, 0dB]
  - 噪声类型: [白噪声, 街道, 咖啡厅, 办公室]
  - 混响: [无, 小房间, 大厅]
  - 口音: [标准, 方言, 非母语]
  - 说话速度: [慢, 中, 快]
```

## 4. 音乐生成评估

### 4.1 客观指标

| 指标 | 描述 | 说明 |
|------|------|------|
| FAD | Fréchet Audio Distance | 与参考集分布距离 |
| CLAP Score | 文本-音频对齐 | 描述匹配度 |
| KLD | KL 散度 | 风格分布匹配 |
| Chroma Accuracy | 和弦准确度 | 音乐理论合理性 |
| Tempo Accuracy | BPM 准确度 | 节拍一致性 |
| PaS (Pitch and Structure) | 音高+结构 | 综合音乐质量 |

#### FAD 计算

```python
import torch
import numpy as np
from frechet_audio_distance import FrechetAudioDistance

fad = FrechetAudioDistance(
    model_name='vggish',    # 或 'panns'
    use_pca=False,
    sample_rate=16000
)

score = fad.calculate(
    background_dir='real_music/',
    eval_dir='generated_music/'
)
# FAD 越低越好
```

### 4.2 音乐主观评测

音乐比语音更主观，需要特别的评测设计：

**评测维度：**

```
1. 音乐性 (Musicality): 听起来像真正的音乐吗？(1-5)
2. 结构性 (Structure): 有清晰的段落和主题？(1-5)
3. 创意性 (Creativity): 有新意？不是抄袭？(1-5)
4. 文本一致性 (Text-match): 符合描述/歌词？(1-5)
5. 整体质量 (Overall): 你愿意再听一次吗？(1-5)
```

**AB 测试：**
```
给评测者两段音乐（A 和 B），问：
  - 哪个更好听？
  - 哪个更符合描述？
  - 你更愿意分享哪个？
```

### 4.3 人机对比

```
图灵测试式评测:
  - 混合 AI 生成和人类创作的音乐
  - 让评测者猜"这是 AI 还是人类？"
  - 如果准确率 ≈ 50% → AI 达到人类水平
```

## 5. 说话人/音色评估

### 5.1 说话人验证

```
EER (Equal Error Rate):
  - 阈值设定使 FAR = FRR 时的错误率
  - EER 越低越好
  - 当前 SOTA: < 1%
```

| 指标 | 描述 |
|------|------|
| EER | 等错误率 |
| minDCF | 最小检测代价函数 |
| FAR | 错误接受率 |
| FRR | 错误拒绝率 |

### 5.2 声音克隆评估

```
三维评估:
  1. SIM (相似度): 听起来像目标说话人吗？(0-1)
  2. MOS (自然度): 语音自然度 (1-5)
  3. WER (可懂度): 内容是否准确？
  
好的克隆: SIM > 0.7, MOS > 4.0, WER < 5%
```

## 6. 评测的工程实践

### 6.1 自动化评测管线

```python
class AudioEvaluator:
    def __init__(self):
        self.asr = load_asr_model()      # WER
        self.spk = load_spk_model()      # SIM
        self.mos = load_mos_predictor()  # MOS
    
    def evaluate(self, generated, reference):
        results = {}
        
        # 客观指标
        results['mcd'] = compute_mcd(generated, reference)
        results['sim'] = compute_speaker_sim(generated, reference)
        results['wer'] = compute_wer(generated)
        results['mos_pred'] = self.mos.predict(generated)
        
        return results
    
    def batch_evaluate(self, samples):
        all_results = []
        for sample in samples:
            results = self.evaluate(sample['generated'], sample['reference'])
            all_results.append(results)
        return aggregate(all_results)
```

### 6.2 主观评测平台

| 平台 | 特点 |
|------|------|
| Amazon MTurk | 便宜，质量参差 |
| Prolific | 质量较好，价格适中 |
| Canvas-MUSHRA | 本地部署 MUSHRA |
| WebMUSHRA | Web 端 MUSHRA |
| 自建 | 最灵活 |

### 6.3 评测报告模板

```
系统: [模型名称]
数据: [训练/测试集]
日期: [日期]

客观指标:
  MCD: X.XX
  SIM: 0.XX
  WER: X.X%
  FAD: X.XX

主观评测:
  MOS: X.XX ± 0.XX (N=XX)
  CMOS vs baseline: +X.XX

样本:
  [附 5-10 个代表性音频样本]
```

## 7. 本章小结

音频评估的核心原则：

1. **客观 + 主观双轨制**：客观指标用于迭代，主观评测用于结论
2. **多维度评估**：自然度、相似度、可懂度缺一不可
3. **自动主观评测**（UTMOS/NISQA）正在缩小与人类评测的差距
4. **音乐评估**比语音更依赖主观，AB 测试是重要工具
5. **鲁棒性测试**不可忽略——干净环境的结果不代表真实场景

---

> **上一章**：[第 18 章：训练 Pipeline 与分布式训练](./18-training-pipeline.md)
>
> **下一章**：[第 20 章：部署优化——从云端到端侧](./20-deployment.md)

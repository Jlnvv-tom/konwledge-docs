# 第 18 章：训练 Pipeline 与分布式训练

> **系列文章：《语音与音乐的机器之魂》**
> 从单 GPU 到千卡集群，训练大规模语音/音乐模型需要系统化的工程。本章解析训练流程、分布式策略和工程实践。

---

## 1. 训练流程概览

```
数据准备 → 特征提取 → 模型训练 → 验证评估 → 检查点管理 → 部署
```

### 1.1 特征预提取

对于音频模型，预提取特征可以大幅加速训练：

```python
# 预提取 Mel 频谱并缓存
def precompute_features(raw_dir, cache_dir):
    for audio_file in glob(f'{raw_dir}/*.wav'):
        y, sr = librosa.load(audio_file, sr=22050)
        mel = librosa.feature.melspectrogram(
            y=y, sr=sr, n_fft=1024, 
            hop_length=256, n_mels=80
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)
        cache_path = f'{cache_dir}/{Path(audio_file).stem}.npy'
        np.save(cache_path, mel_db)
```

| 策略 | 训练速度 | 磁盘占用 | 灵活性 |
|------|----------|----------|--------|
| 实时提取 | 慢 | 低 | 高（可改参数） |
| 预提取缓存 | 快 | 高 | 中 |
| 混合（缓存+增强） | 中 | 中 | 高 |

## 2. 训练配置

### 2.1 超参数

```yaml
# 典型 TTS 训练配置
model:
  type: VITS
  hidden_dim: 192
  n_layers: 6
  n_heads: 2

training:
  batch_size: 32
  learning_rate: 2e-4
  optimizer: AdamW
  betas: [0.8, 0.99]
  lr_scheduler: exponential_decay
  gamma: 0.9998
  grad_clip: 0.5
  
  warmup_steps: 1000
  total_steps: 500000
  
  fp16: true              # 混合精度
  gradient_accumulation: 1  # 梯度累积

audio:
  sample_rate: 22050
  n_fft: 1024
  hop_length: 256
  n_mels: 80
  segment_length: 8192   # 训练时音频段长度
```

### 2.2 学习率策略

```
Warmup → 平台 → 衰减
  ↑       ↑       ↑
1-5k步  稳定训练  后期精调
```

```python
# Warmup + Cosine Decay
from torch.optim.lr_scheduler import LambdaLR
import math

def get_cosine_schedule_with_warmup(optimizer, warmup, total):
    def lr_lambda(step):
        if step < warmup:
            return step / warmup
        progress = (step - warmup) / (total - warmup)
        return 0.5 * (1 + math.cos(math.pi * progress))
    return LambdaLR(optimizer, lr_lambda)
```

## 3. 分布式训练

### 3.1 并行策略概览

| 策略 | 原理 | 适用场景 |
|------|------|----------|
| 数据并行（DDP） | 每卡完整模型，不同数据 | 模型放得下单卡 |
| 模型并行 | 模型拆分到多卡 | 模型过大 |
| 流水线并行 | 按层分卡 | 超深模型 |
| 张量并行 | 单层内分卡 | 超大线性层 |
| FSDP | 分片模型+梯度 | 大模型+多卡 |

### 3.2 DDP（DistributedDataParallel）

最常用的分布式策略：

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler

# 初始化进程组
dist.init_process_group(backend='nccl')
local_rank = int(os.environ['LOCAL_RANK'])
torch.cuda.set_device(local_rank)

# 模型
model = MyModel().cuda()
model = DDP(model, device_ids=[local_rank])

# 数据（自动分片）
sampler = DistributedSampler(dataset)
dataloader = DataLoader(dataset, sampler=sampler, batch_size=32)

# 正常训练循环
for batch in dataloader:
    loss = model(batch)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
```

**DDP 关键点：**
- 每卡有完整模型副本
- 各卡处理不同数据
- 反向传播时自动同步梯度（AllReduce）
- 有效 batch_size = batch_size × n_gpus

### 3.3 FSDP（Fully Sharded Data Parallel）

大模型场景的标配：

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = MyLargeModel().cuda()
model = FSDP(model)  # 自动分片参数/梯度/优化器状态
```

- 参数/梯度/优化器状态分片到各卡
- 前向传播时动态聚合
- 显存效率远优于 DDP
- PyTorch 原生支持

### 3.4 DeepSpeed ZeRO

```
ZeRO-1: 分片优化器状态 → 显存减少 4×
ZeRO-2: + 分片梯度 → 显存减少 8×
ZeRO-3: + 分片参数 → 显存减少 N× (N=GPU数)
```

```python
# DeepSpeed 配置
{
  "zero_optimization": {
    "stage": 2,
    "offload_optimizer": {
      "device": "cpu"  # CPU offload 进一步省显存
    }
  },
  "bf16": {
    "enabled": true
  }
}
```

### 3.5 并行策略选择

```
模型 < 单卡显存 → DDP
模型 > 单卡显存但 < 多卡总显存 → FSDP / ZeRO-3
模型 >> 多卡总显存 → FSDP + 模型并行 + 流水线
需要训练超大模型 → Megatron-LM / DeepSpeed-Megatron
```

## 4. 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()
    
    with autocast(dtype=torch.bfloat16):  # 或 float16
        loss = model(batch)
    
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

| 精度 | 显存 | 速度 | 稳定性 | 硬件要求 |
|------|------|------|--------|----------|
| FP32 | 基准 | 基准 | 最好 | 所有 GPU |
| FP16 | 50% | 2-3× | 需 GradScaler | V100+ |
| BF16 | 50% | 2-3× | 极好 | A100+ |
| FP8 | 25% | 4-5× | 需调试 | H100+ |

**推荐：BF16 > FP16 > FP32**（如果硬件支持）

## 5. 检查点管理

```python
def save_checkpoint(model, optimizer, scheduler, step, path):
    torch.save({
        'model_state': model.state_dict(),
        'optimizer_state': optimizer.state_dict(),
        'scheduler_state': scheduler.state_dict(),
        'step': step,
    }, path)

def load_checkpoint(path, model, optimizer=None, scheduler=None):
    ckpt = torch.load(path)
    model.load_state_dict(ckpt['model_state'])
    if optimizer:
        optimizer.load_state_dict(ckpt['optimizer_state'])
    if scheduler:
        scheduler.load_state_dict(ckpt['scheduler_state'])
    return ckpt['step']
```

**检查点策略：**
- 每 N 步保存（如 5000 步）
- 保留最近 K 个 + 最佳 M 个
- 大模型使用分片保存
- 训练恢复测试

## 6. 训练监控

### 6.1 关键指标

```
训练集:
  - Loss（总损失 + 各子损失）
  - 学习率
  - 梯度范数
  - 吞吐量（samples/s）

验证集:
  - Loss
  - 主观指标（定期人工评测）
  - 生成样本（定期保存）
```

### 6.2 工具链

```python
# Weights & Biases
import wandb
wandb.init(project='tts-training')
wandb.log({
    'train/loss': loss.item(),
    'train/lr': current_lr,
    'train/grad_norm': grad_norm,
}, step=global_step)

# 保存生成样本
if global_step % 5000 == 0:
    sample = model.generate("测试文本")
    wandb.log({'samples/audio': wandb.Audio(sample, sample_rate=22050)})
```

## 7. 训练常见问题

### 7.1 损失不下降

```
排查清单:
  1. 学习率是否合适？（太大会震荡，太小不下降）
  2. 数据是否正确？（检查随机样本）
  3. 梯度是否正常？（检查梯度范数，太小=消失，太大=爆炸）
  4. 损失函数是否正确？
  5. 是否有过拟合？（训练降但验证不降）
```

### 7.2 GAN 训练不稳定

```
策略:
  - 判别器 vs 生成器交替比例（如 5:1）
  - 谱归一化（Spectral Norm）
  - 特征匹配损失
  - 延迟判别器启动（先训练生成器几万步）
  - 梯度惩罚
```

### 7.3 长序列训练 OOM

```
策略:
  - 梯度检查点（Gradient Checkpointing）
  - 减小 batch size + 增加梯度累积
  - 序列分段训练
  - Flash Attention
  - 降低精度（BF16）
```

## 8. 训练资源估算

### 8.1 VITS 训练

```
数据: 10-100 小时
GPU: 1× V100 / A100
训练时间: 3-7 天
显存: 8-16 GB
```

### 8.2 MusicGen-Large 训练

```
数据: 20K+ 小时音乐
GPU: 64× A100 80G
训练时间: 数周
显存: 80GB/卡
```

### 8.3 Whisper-Large 训练

```
数据: 68 万小时
GPU: 5800+ GPU 天
训练时间: 数月
```

## 9. 本章小结

训练工程的核心要素：

1. **数据管线**：高效的数据加载和预处理
2. **分布式策略**：DDP/FSDP/ZeRO 根据模型规模选择
3. **混合精度**：BF16 是当前最佳选择
4. **监控**：Loss/LR/梯度/生成样本全监控
5. **稳定性**：GAN 需要特殊技巧，长序列需要内存优化

"训练好一个模型"比"设计一个模型架构"往往更难——工程细节决定成败。

---

> **上一章**：[第 17 章：数据采集、标注与清洗](./17-data-preparation.md)
>
> **下一章**：[第 19 章：评估指标与主观评测](./19-evaluation.md)

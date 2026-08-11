# 第 20 章：部署优化——从云端到端侧

> **系列文章：《语音与音乐的机器之魂》**
> 训练好的模型如何高效部署？本章覆盖模型压缩、推理优化、端侧部署和延迟工程。

---

## 1. 部署场景

```
云端: GPU 服务器 → API → 客户端
  - 质量: 最优
  - 延迟: 网络 + 推理
  - 成本: 按需计费

边缘: 本地 GPU/NPU → 直接推理
  - 质量: 良好
  - 延迟: 仅推理
  - 成本: 硬件一次性

端侧: 手机/嵌入式 → 本地推理
  - 质量: 受限
  - 延迟: 最低
  - 成本: 零
  - 隐私: 最优
```

## 2. 模型压缩

### 2.1 量化

```python
# INT8 动态量化
import torch.quantization as quant

model_int8 = quant.quantize_dynamic(
    model,
    {nn.Linear, nn.Conv1d},
    dtype=torch.qint8
)
# 模型大小: 1/4
# 速度: 2-3× 加速
# 质量: 几乎无损
```

| 精度 | 大小 | 速度 | 质量 | 硬件 |
|------|------|------|------|------|
| FP32 | 基准 | 基准 | 100% | 所有 |
| BF16 | 50% | 1.5× | ~100% | A100+ |
| INT8 | 25% | 2-3× | ~98% | 多数 GPU |
| INT4 | 12.5% | 3-4× | ~95% | 特定硬件 |
| FP8 | 12.5% | 4-5× | ~98% | H100 |

### 2.2 剪枝

```python
# 结构化剪枝
from torch.nn.utils.prune import l1_unstructured

for name, module in model.named_modules():
    if isinstance(module, nn.Conv1d):
        l1_unstructured(module, name='weight', amount=0.3)  # 剪去 30%
```

| 方法 | 压缩率 | 质量影响 |
|------|--------|----------|
| 非结构化剪枝 | 高 | 中（稀疏矩阵支持有限） |
| 结构化剪枝 | 中 | 低（直接移除通道） |
| 知识蒸馏 | 中 | 低（教师指导） |

### 2.3 知识蒸馏

```
大模型（教师）→ 软标签
小模型（学生）→ 拟合软标签 + 硬标签
```

```python
def distillation_loss(student_logits, teacher_logits, labels, alpha=0.7, T=2.0):
    """知识蒸馏损失"""
    soft_loss = F.kl_div(
        F.log_softmax(student_logits / T, dim=-1),
        F.softmax(teacher_logits / T, dim=-1),
        reduction='batchmean'
    ) * (T ** 2)
    
    hard_loss = F.cross_entropy(student_logits, labels)
    return alpha * soft_loss + (1 - alpha) * hard_loss
```

## 3. 推理优化

### 3.1 ONNX 导出

```python
# PyTorch → ONNX
dummy_input = torch.randn(1, 80, 100)  # Mel 频谱
torch.onnx.export(
    model, dummy_input, 'tts_encoder.onnx',
    input_names=['mel'],
    output_names=['output'],
    dynamic_axes={'mel': {0: 'batch', 2: 'time'}}
)

# ONNX Runtime 推理
import onnxruntime as ort
session = ort.InferenceSession('tts_encoder.onnx')
output = session.run(None, {'mel': mel_numpy})
```

### 3.2 TorchScript

```python
# 脚本化
scripted_model = torch.jit.script(model)
scripted_model.save('model.ptc')

# 推理（无需 Python GIL）
loaded = torch.jit.load('model.ptc')
output = loaded(input)
```

### 3.3 TensorRT

```python
# TensorRT 优化
import tensorrt as trt

# 1. 导出 ONNX
# 2. TensorRT 构建 engine
# 3. 精度校准（INT8）
# 4. 动态 shape 配置

# 速度提升: 3-10×（相比 PyTorch）
```

### 3.4 Flash Attention

```python
# 标准 Attention: O(n²) 内存
attn = softmax(Q @ K.T / √d) @ V

# Flash Attention: 分块计算，O(n) 内存
from flash_attn import flash_attn_func
attn = flash_attn_func(Q, K, V)  # 自动分块
```

- 2-4× 速度提升
- 显存大幅减少
- 数值结果相同
- 已集成到 PyTorch 2.0+

### 3.5 KV Cache

自回归模型的关键优化：

```
无 KV Cache:
  Step 1: 计算 Q1,K1,V1 → A1
  Step 2: 计算 Q1,K1,V1 + Q2,K2,V2 → A1,A2  (重复计算!)
  
有 KV Cache:
  Step 1: 计算 Q1,K1,V1 → A1, 缓存 K1,V1
  Step 2: 只计算 Q2, 用缓存的 K1,V1 + 新的 K2,V2 → A2
```

```python
class CachedAttention(nn.Module):
    def forward(self, x, past_kv=None):
        Q = self.q(x)
        K, V = self.k(x), self.v(x)
        
        if past_kv is not None:
            K = torch.cat([past_kv[0], K], dim=-2)
            V = torch.cat([past_kv[1], V], dim=-2)
        
        attn = attention(Q, K, V)
        return attn, (K, V)  # 返回新的缓存
```

## 4. 流式推理架构

### 4.1 流式 ASR 推理

```
音频流 → [VAD] → [特征提取] → [编码器(状态缓存)] → [解码器] → 文本流
                       ↑                    ↑
                  因果卷积            KV Cache
```

```python
class StreamingASR:
    def __init__(self):
        self.encoder_state = None  # 编码器状态
        self.decoder_cache = None  # KV Cache
        
    def process_chunk(self, audio_chunk):
        # 特征提取
        features = self.extract_features(audio_chunk)
        
        # 编码（带状态）
        encoded, self.encoder_state = self.encoder(
            features, self.encoder_state
        )
        
        # 解码（带缓存）
        tokens, self.decoder_cache = self.decoder(
            encoded, self.decoder_cache
        )
        
        return tokens
```

### 4.2 流式 TTS 推理

```
文本流 → [文本前端] → [声学模型(逐句)] → [声码器(逐帧)] → 音频流
                            ↑                    ↑
                       句子级缓冲           状态缓存
```

## 5. 端侧部署

### 5.1 移动端

```python
# PyTorch Mobile
import torch
model = torch.jit.script(model)
model = torch.jit.optimize_for_inference(model)
model._save_for_lite_interpreter('model.ptl')

# Android
# ```
# PyTorchMobile = org.pytorch:pytorch_android_lite
# module = LiteModuleLoader.load(assetFilePath)
# ```

# iOS
# ```
# let module = LiteModuleLoader.load(filePath)
# ```
```

### 5.2 ONNX Runtime Mobile

```python
# 极致优化的端侧推理
import onnxruntime as ort

session = ort.InferenceSession(
    'model.onnx',
    providers=['CPUExecutionProvider'],
    session_options=ort.SessionOptions()
)
# 量化后模型 < 10MB
```

### 5.3 专用硬件

| 芯片 | 类型 | 特点 |
|------|------|------|
| Apple Neural Engine (ANE) | NPU | iOS 设备 AI 加速 |
| Qualcomm Hexagon | DSP | Android AI 加速 |
| MediaTek APU | NPU | 中端手机 |
| Edge TPU | TPU | Coral 设备 |

### 5.4 端侧 TTS 方案

```
要求:
  - 模型 < 50MB
  - 推理 < 100ms (首字)
  - CPU 即可运行
  - 离线工作

方案:
  - FastSpeech 2 + HiFi-GAN V3
  - INT8 量化
  - ONNX Runtime Mobile
  - 模型大小: ~15MB
  - 首字延迟: ~200ms
```

## 6. 服务化部署

### 6.1 API 设计

```python
# REST API (简单)
@app.post('/tts')
async def tts_api(text: str, speaker: str):
    audio = model.generate(text, speaker)
    return AudioResponse(audio, sample_rate=22050)

# WebSocket (流式)
@app.websocket('/stream/tts')
async def streaming_tts(websocket):
    text = await websocket.receive_text()
    async for chunk in model.generate_stream(text):
        await websocket.send_bytes(chunk)
```

### 6.2 负载均衡

```
请求 → 负载均衡器 → GPU Worker Pool
                   ↓
              模型实例 (每 GPU 1-2 个)
              
策略:
  - 按 GPU 显存分配
  - 动态 batch（收集请求凑批）
  - 请求排队 + 优先级
```

### 6.3 Triton Inference Server

```yaml
# config.pbtxt
name: "tts_model"
backend: "python"
max_batch_size: 8
input { name: "text" data_type: TYPE_STRING }
output { name: "audio" data_type: TYPE_FP32 }

dynamic_batching {
  preferred_batch_size: [4, 8]
  max_queue_delay_microseconds: 100000
}

instance_group {
  kind: KIND_GPU
  count: 2
  gpus: [0, 1]
}
```

## 7. 延迟优化清单

```
┌─ 模型层面 ──────────────────────────┐
│ □ INT8/INT4 量化                    │
│ □ 知识蒸馏到小模型                  │
│ □ KV Cache (自回归模型)             │
│ □ Flash Attention                   │
│ □ 非自回归替代自回归                │
└────────────────────────────────────┘

┌─ 推理引擎 ──────────────────────────┐
│ □ ONNX Runtime / TensorRT          │
│ □ 算子融合                         │
│ □ 动态 batch                       │
│ □ 模型预热                         │
└────────────────────────────────────┘

┌─ 系统层面 ──────────────────────────┐
│ □ CPU pinning                      │
│ □ 内存池                           │
│ □ 零拷贝传输                       │
│ □ GPU 内存预分配                    │
│ □ 流式输出                         │
└────────────────────────────────────┘
```

## 8. 本章小结

部署优化是 AI 从实验室到产品的关键一步：

1. **模型压缩**：量化 > 蒸馏 > 剪枝
2. **推理优化**：ONNX/TensorRT + Flash Attention + KV Cache
3. **流式架构**：状态缓存 + 分块处理
4. **端侧部署**：ONNX Mobile / PyTorch Mobile
5. **服务化**：Triton + 动态 batch + 流式 API

目标是在保证质量的前提下，最小化延迟和成本。

---

> **上一章**：[第 19 章：评估指标与主观评测](./19-evaluation.md)
>
> **下一章**：[第 21 章：深度伪造防御](./21-deepfake-defense.md)

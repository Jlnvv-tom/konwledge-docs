---
sidebar_position: 7
---

# 第七章：私有化部署与系统集成

在企业级 AI Agent 落地过程中，私有化部署是将技术能力转化为生产力的关键环节。与公有云 API 调用不同，私有化部署需要考虑网络隔离、硬件受限、安全合规、与现有系统融合等诸多工程挑战。本章将从部署模式选型到数据迁移策略，系统性地讲解私有化部署的完整实践路径。

## 7.1 私有化部署模式选型

私有化部署并非简单的"搬到本地"，而是需要根据企业的安全要求、硬件条件、运维能力和业务场景，选择合适的部署架构。不同模式在隔离性、性能、成本和运维复杂度上差异显著。

### 三种主流部署模式

企业级私有化部署通常分为三种模式：完全离线部署、内网部署和混合部署。每种模式适用于不同的业务场景和安全等级要求。

完全离线部署是指整个系统运行在物理隔离的网络环境中，不与外部网络有任何连接。这种模式常见于军工、涉密机构等高安全级别场景。所有模型权重、依赖包、镜像文件都需要通过物理介质传输，部署周期长但安全性最高。

内网部署是指系统运行在企业内部网络中，可以通过内部网络访问，但不暴露到公网。这是最常见的私有化部署模式，适用于大多数金融、政务、医疗等行业的场景。内网部署允许一定程度的远程运维，但需要严格的安全策略。

混合部署是指核心数据和模型部署在私有环境，同时利用公有云的弹性资源处理非敏感任务。这种模式在性能和成本之间取得平衡，但需要解决网络打通和数据同步的问题。

### 部署模式对比

| 对比维度 | 完全离线部署 | 内网部署 | 混合部署 |
|---------|------------|---------|---------|
| 网络环境 | 物理隔离，无任何外部连接 | 内网可访问，公网隔离 | 核心内网+公有云通道 |
| 安全等级 | 最高 | 高 | 中高 |
| 部署难度 | 极高 | 中等 | 中等 |
| 运维方式 | 现场运维为主 | 远程+现场 | 远程为主 |
| 模型更新 | 物理介质传输 | 内网镜像仓库 | 自动同步 |
| 弹性扩展 | 困难 | 受限于硬件 | 可利用云资源 |
| 适用场景 | 涉密机构、军工 | 金融、政务、医疗 | 互联网企业、大型集团 |
| 部署周期 | 2-4周 | 3-7天 | 1-3天 |

### 选型决策框架

在实际项目中，部署模式选型需要从以下几个维度进行评估。

安全合规是首要考量。如果业务涉及国家秘密、核心金融数据或患者隐私数据，通常要求完全离线或至少内网部署。需要查阅行业监管要求，如等保 2.0 (Information Security Protection Level 2.0) 标准、HIPAA (Health Insurance Portability and Accountability Act) 等。

硬件条件决定了部署的可行性。GPU 服务器是 LLM (Large Language Model) 推理的硬性要求，至少需要 NVIDIA A10 或同等算力以上的显卡。如果企业没有 GPU 服务器，需要考虑租赁或采购周期。

运维能力影响长期运行质量。如果企业没有专业的 DevOps 团队，过于复杂的部署架构会带来运维负担。此时应选择简化的部署方案，如 Docker Compose 单机部署，而非 K8s (Kubernetes, 容器编排平台) 集群部署。

### 部署模式选择的决策流程

```
开始选型
  |
  v
是否涉及涉密数据? ---是---> 完全离线部署
  | 否
  v
是否有 GPU 硬件? ---否---> 评估采购或混合部署
  | 是
  v
是否有 DevOps 团队? ---否---> Docker Compose 单机部署
  | 是
  v
业务规模是否需要弹性? ---是---> 混合部署
  | 否
  v
内网部署 + K8s 集群
```

### 延展：许可证管理

私有化部署还需要考虑软件许可证管理。许多商业 LLM 模型在私有化部署时需要单独的 License 授权。开源模型如 Llama 3、Qwen 虽然可以免费使用，但在大规模商业应用时仍需关注许可协议的具体条款。

建议在选型阶段就明确许可证范围，包括使用场景限制、并发数限制、地域限制等。同时建立内部许可证台账，跟踪到期时间和续约计划，避免因许可证过期导致服务中断。

## 7.2 LLM 推理服务部署实践

LLM 推理服务是整个 AI Agent 系统的核心组件，其部署质量直接决定了系统的响应速度和用户体验。选择合适的推理框架、配置合理的参数、做好资源调度，是推理服务部署的关键。

### 主流推理框架对比

当前主流的 LLM 推理框架各有特点，需要根据模型规模、硬件配置和性能需求进行选择。

| 框架名称 | 开发语言 | 核心特性 | 适用模型 | GPU 内存优化 | 并发处理 |
|---------|---------|---------|---------|------------|---------|
| vLLM | Python/C++ | PagedAttention, Continuous Batching | 主流开源模型 | 优秀 | 优秀 |
| TGI (Text Generation Inference) | Python/Rust | Rust 后端, 流式输出 | HuggingFace 模型生态 | 良好 | 优秀 |
| Ollama | Go | 轻量级, 易部署 | GGUF 格式模型 | 中等 | 一般 |
| TensorRT-LLM | C++ | NVIDIA 官方, 极致性能 | 有限模型列表 | 优秀 | 优秀 |
| SGLang | Python | RadixAttention, 结构化生成 | 主流开源模型 | 优秀 | 优秀 |
| LMDeploy | Python | 量化推理, TurboMind 引擎 | InternLM 系列, 通用 | 优秀 | 良好 |

### vLLM 部署实践

vLLM (Vectorized Large Language Model serving) 是目前应用最广泛的开源推理框架，其 PagedAttention 技术显著提升了 GPU 显存利用率和推理吞吐量。

以下是一个典型的 vLLM 部署命令示例：

```bash
# 启动 vLLM 推理服务
python -m vllm.entrypoints.openai.api_server \
    --model /models/Qwen2.5-14B-Instruct \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --port 8000 \
    --host 0.0.0.0 \
    --trust-remote-code \
    --enable-lora \
    --max-loras 4
```

关键参数说明：tensor-parallel-size 控制多 GPU 并行度；gpu-memory-utilization 设置显存使用上限；max-model-len 限制最大上下文长度；enable-lora 开启 LoRA (Low-Rank Adaptation) 适配器支持。

### TGI 部署实践

TGI 是 HuggingFace 团队开发的推理框架，与 HuggingFace 生态深度集成，适合需要快速部署和灵活模型切换的场景。

```bash
# 使用 Docker 启动 TGI 服务
docker run --gpus all -p 8080:80 \
    -v /models:/models \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id /models/Qwen2.5-14B-Instruct \
    --num-shard 2 \
    --max-input-tokens 4096 \
    --max-total-tokens 8192 \
    --quantize awq
```

### 推理性能优化要点

在实际部署中，推理性能优化需要从多个层面入手。

模型层面，选择合适规模的模型至关重要。7B 模型在单张 A10 上可以流畅运行，14B 模型建议使用 A100 或两张 A10，70B 模型则需要多卡并行。模型规模与推理延迟的关系并非线性，超过某个阈值后延迟会显著增加。

显存层面，KV Cache (Key-Value Cache) 是推理过程中最消耗显存的部分。vLLM 的 PagedAttention 将 KV Cache 分块管理，显著减少了显存碎片。通过调整 gpu-memory-utilization 参数，可以在吞吐量和安全余量之间取得平衡。

并发层面，Continuous Batching (连续批处理) 技术允许在处理请求的同时动态接入新请求，避免了传统批处理需要等待固定批次填满的问题。这使得推理服务在高并发场景下保持稳定的吞吐量。

### 推理服务监控指标

部署后需要持续监控以下核心指标：

| 指标名称 | 说明 | 建议阈值 |
|---------|------|---------|
| TTFT (Time To First Token) | 首字延迟 | < 500ms |
| TPOT (Time Per Output Token) | 每字生成延迟 | < 50ms |
| 请求排队时长 | 请求在队列中等待时间 | < 2s |
| GPU 显存使用率 | 显存占用比例 | < 95% |
| GPU 计算使用率 | GPU 计算单元利用率 | 60%-90% |
| 请求成功率 | 成功响应比例 | > 99% |
| 端到端延迟 | 从请求到完整响应 | 视场景而定 |

### 延展：多模型部署策略

在实际场景中，企业可能需要同时部署多个不同规模的模型。例如，用小模型处理简单对话，用大模型处理复杂推理。这种多模型部署需要考虑 GPU 资源分配策略。

一种常见方案是按业务优先级分配 GPU 资源。高优先级模型独占 GPU，低优先级模型共享 GPU。另一种方案是根据请求负载动态调度，在高峰期为热模型分配更多资源。vLLM 的多 LoRA 支持提供了一种轻量级的多模型方案，同一个基础模型可以加载多个 LoRA 适配器，以较低的资源开销实现模型能力的多样化。

## 7.3 与客户现有系统的集成方案

AI Agent 系统很少孤立运行，通常需要与企业现有的业务系统深度集成。集成方案的设计直接影响系统的可用性和用户体验。良好的集成应该做到对用户透明，让 AI 能力自然地融入现有工作流。

### 常见集成场景

| 集成场景 | 对接系统 | 集成方式 | 数据流向 |
|---------|---------|---------|---------|
| 智能客服 | CRM/工单系统 | API 对接 | 双向 |
| 知识问答 | OA/文档系统 | API + 数据同步 | 单向读取 |
| 流程自动化 | ERP/BPM 系统 | Webhook + RPA | 双向 |
| 数据分析 | BI/数据仓库 | SQL 查询 + API | 单向读取 |
| 邮件助手 | 邮件系统 | IMAP/SMTP | 双向 |
| 会议纪要 | 视频会议系统 | 录音文件传输 | 单向输入 |
| 审批辅助 | OA 审批流 | API 对接 | 双向 |

### API 网关集成模式

在大多数企业集成场景中，API 网关是集成的核心枢纽。AI Agent 通过 API 网关与各业务系统通信，网关负责认证、限流、日志等横切关注点。

以下是一个典型的 API 网关集成架构：

```
                    +------------------+
                    |   API Gateway    |
                    | (认证/限流/路由)  |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                  |                  |
+---------v------+  +--------v-------+  +-------v--------+
|  AI Agent 服务  |  |  业务系统 API  |  |  数据查询服务   |
|  (LLM + Tools) |  |  (CRM/ERP/OA) |  |  (BI/数据仓库)  |
+----------------+  +----------------+  +----------------+
          |                  |                  |
          +------------------+------------------+
                             |
                    +--------v---------+
                    |    消息队列       |
                    | (异步任务处理)    |
                    +------------------+
```

### RESTful API 对接示例

以下是一个 AI Agent 与 CRM 系统集成的 API 对接代码示例：

```python
import httpx
from typing import Optional

class CRMIntegration:
    """CRM 系统集成适配器"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def get_customer_info(self, customer_id: str) -> dict:
        """获取客户信息"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/customers/{customer_id}",
                headers=self.headers,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()

    async def create_ticket(self, customer_id: str,
                            title: str, description: str) -> dict:
        """创建工单"""
        payload = {
            "customer_id": customer_id,
            "title": title,
            "description": description,
            "source": "ai_agent"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/tickets",
                headers=self.headers, json=payload, timeout=10
            )
            resp.raise_for_status()
            return resp.json()
```

### 单点登录 (SSO) 集成

企业系统集成中，身份认证是不可回避的问题。大多数企业使用 SSO (Single Sign-On, 单点登录) 系统统一管理用户身份。AI Agent 系统需要与现有 SSO 对接，避免用户重复登录。

常见的 SSO 协议包括 OAuth 2.0、SAML 2.0 (Security Assertion Markup Language 2.0) 和 OIDC (OpenID Connect)。集成时需要根据客户现有的身份提供商选择对应协议。

对接流程通常包括：在 SSO 系统中注册 AI Agent 应用，获取 Client ID 和 Secret；配置回调 URL；实现 Token 验证逻辑；将用户身份与 Agent 会话绑定。

### Webhook 集成模式

对于需要实时响应的业务场景，Webhook 是比 API 轮询更高效的集成方式。业务系统在事件发生时主动推送通知给 AI Agent，Agent 根据事件内容触发相应处理。

```python
from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib

app = FastAPI()
WEBHOOK_SECRET = "your_webhook_secret"

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhook/ticket-created")
async def on_ticket_created(request: Request):
    payload = await request.body()
    sig = request.headers.get("X-Webhook-Signature", "")
    if not verify_signature(payload, sig):
        raise HTTPException(401, "Invalid signature")
    data = await request.json()
    # 触发 AI Agent 处理逻辑
    return {"status": "accepted"}
```

### 延展：遗留系统集成的挑战

并非所有企业系统都提供了规范的 API。许多老旧系统使用 SOAP 协议、数据库直连或文件交换等方式。对于这类遗留系统，可以采用以下策略。

构建适配层：在 AI Agent 和遗留系统之间增加一层适配服务，将老旧协议转换为 RESTful API。这层适配服务可以使用 Python 的 Zeep 库处理 SOAP，或使用 JDBC 驱动直连数据库。

数据库视图模式：对于只有数据库接口的系统，创建只读视图供 AI Agent 查询，避免直接操作业务表。写入操作通过存储过程封装，确保数据一致性。

文件交换模式：对于完全封闭的系统，使用文件交换（如定时导出 CSV 文件）作为集成手段。虽然实时性差，但在某些场景下是唯一可行的方案。

## 7.4 Docker 化部署最佳实践

Docker 容器化是现代应用部署的标准方式。对于 AI Agent 系统，Docker 化部署可以确保环境一致性、简化版本管理、便于水平扩展。但 LLM 服务对 GPU 和内存的特殊需求，使得 Docker 化部署有一些需要特别注意的地方。

### Dockerfile 编写原则

编写 AI Agent 系统的 Dockerfile 时，需要遵循分层构建、最小镜像、缓存优化等原则。以下是一个综合示例：

```dockerfile
# 阶段一：构建依赖
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc git curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 阶段二：运行环境
FROM python:3.11-slim AS runtime

WORKDIR /app

# 复制 Python 包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY . /app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "-m", "app.main"]
```

这个 Dockerfile 使用了多阶段构建，将编译环境和运行环境分离，显著减小了最终镜像体积。builder 阶段安装编译依赖并构建 Python 包，runtime 阶段只复制必要的运行时文件。

### GPU 支持

LLM 推理服务需要 GPU 支持，需要使用 NVIDIA Container Toolkit。Dockerfile 的基础镜像需要选择支持 CUDA 的版本：

```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.11 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

CMD ["python", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "/models/Qwen2.5-14B-Instruct"]
```

运行时需要使用 --gpus 参数指定 GPU：

```bash
docker run --gpus all -d \
    --name llm-server \
    -p 8000:8000 \
    -v /models:/models \
    llm-server:latest
```

### Docker Compose 编排

对于多组件的 AI Agent 系统，Docker Compose 提供了简洁的编排方式。以下是一个包含 LLM 推理服务、Agent 应用、向量数据库和缓存的完整编排示例：

```yaml
version: "3.9"

services:
  llm-server:
    build: ./llm-service
    container_name: llm-server
    ports:
      - "8000:8000"
    volumes:
      - /models:/models:ro
      - llm-cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
    environment:
      - MODEL_PATH=/models/Qwen2.5-14B-Instruct
      - TENSOR_PARALLEL_SIZE=2
    restart: unless-stopped

  agent-app:
    build: ./agent-app
    container_name: agent-app
    ports:
      - "8080:8080"
    depends_on:
      - llm-server
      - vector-db
      - redis
    environment:
      - LLM_ENDPOINT=http://llm-server:8000/v1
      - VECTOR_DB_URL=http://vector-db:6333
      - REDIS_URL=redis://redis:6379
    restart: unless-stopped

  vector-db:
    image: qdrant/qdrant:v1.9.0
    container_name: vector-db
    ports:
      - "6333:6333"
    volumes:
      - qdrant-data:/qdrant/storage
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    restart: unless-stopped

volumes:
  llm-cache:
  qdrant-data:
  redis-data:
```

### 镜像优化策略

AI Agent 系统的 Docker 镜像通常较大，需要采取措施进行优化。

基础镜像选择方面，优先选择 slim 或 alpine 变体。Python 应用使用 python:3.11-slim 而非 python:3.11，可以减少约 300MB 的镜像体积。需要 CUDA 支持时，选择 runtime 而非 devel 变体。

依赖管理方面，使用 pip 的 --no-cache-dir 参数避免缓存文件进入镜像。将 requirements.txt 单独 COPY 并先安装依赖，利用 Docker 的层缓存机制，在代码变更时避免重新安装依赖。

镜像扫描方面，使用 Trivy 或 Grype 等工具定期扫描镜像漏洞。对于发现的漏洞，及时更新基础镜像或修补依赖版本。

### 延展：镜像分发策略

在私有化部署中，如何将 Docker 镜像分发到客户环境是一个实际问题。

内网镜像仓库方案：在客户内网部署 Harbor 或 Registry 服务，通过 VPN 或专线将镜像推送到内网仓库。客户环境从内网仓库拉取镜像，不依赖公网。

离线导出方案：使用 docker save 将镜像导出为 tar 文件，通过物理介质或安全文件传输送达客户环境，再使用 docker load 导入。适合完全离线环境。

```bash
# 导出镜像
docker save llm-server:latest | gzip > llm-server.tar.gz

# 导入镜像
docker load < llm-server.tar.gz
```

分层优化方案：将不常变的基础层和经常变的应用层分开构建。基础层一次性导入，后续更新只需传输应用层的增量，减少传输量。

## 7.5 客户网络环境限制应对

私有化部署中最常见的挑战之一是客户网络环境的各种限制。企业内网通常有严格的防火墙策略、代理服务器配置和网络分区，这些限制会影响 Docker 镜像拉取、依赖包下载、模型文件传输等关键环节。

### 常见网络限制场景

| 限制类型 | 具体表现 | 影响范围 | 应对难度 |
|---------|---------|---------|---------|
| 出网白名单 | 仅允许访问白名单域名 | 镜像拉取、pip 安装 | 中 |
| 代理服务器 | 所有流量需通过代理 | 全部网络操作 | 中高 |
| 端口限制 | 仅开放特定端口 | 服务端口配置 | 低 |
| DNS 限制 | 内网 DNS 不解析公网域名 | 服务发现 | 中 |
| 网络分区 | DMZ/内网/核心区隔离 | 服务间通信 | 高 |
| 带宽限制 | 出口带宽受限 | 大文件传输 | 中 |
| 证书校验 | 严格要求 TLS 证书 | HTTPS 通信 | 中 |
| 深度包检测 | DPI 检查流量内容 | API 通信 | 高 |

### 代理服务器环境配置

企业内网通常通过代理服务器访问外部资源。Docker 和各类工具需要正确配置代理才能正常工作。

Docker 守护进程代理配置：

```bash
# /etc/systemd/system/docker.service.d/http-proxy.conf
[Service]
Environment="HTTP_PROXY=http://proxy.company.com:8080"
Environment="HTTPS_PROXY=http://proxy.company.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,*.internal"

# 重启 Docker 生效
systemctl daemon-reload
systemctl restart docker
```

容器内代理配置，通过 Docker Compose 的 environment 传递：

```yaml
services:
  agent-app:
    environment:
      - HTTP_PROXY=http://proxy.company.com:8080
      - HTTPS_PROXY=http://proxy.company.com:8080
      - NO_PROXY=localhost,127.0.0.1,llm-server,vector-db
```

Python 应用中的代理处理：

```python
import os
import httpx

proxy = os.environ.get("HTTPS_PROXY")
transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
client = httpx.AsyncClient(transport=transport)
```

### 内网镜像仓库搭建

在无法访问公网 Docker Hub 的环境中，需要搭建内网镜像仓库。Harbor 是企业级镜像仓库的优选方案。

```yaml
# harbor-docker-compose.yml (简化版)
version: "3.9"

services:
  harbor-core:
    image: goharbor/harbor-core:v2.8.0
    ports:
      - "443:8443"
    volumes:
      - harbor-data:/data
    environment:
      - CONFIG_PATH=/etc/harbor/app.conf
    depends_on:
      - harbor-db
      - harbor-redis

  harbor-db:
    image: goharbor/harbor-db:v2.8.0
    environment:
      - POSTGRES_PASSWORD=harbor123
    volumes:
      - harbor-db:/var/lib/postgresql/data

  harbor-redis:
    image: goharbor/harbor-redis:v2.8.0

volumes:
  harbor-data:
  harbor-db:
```

搭建完成后，将所需镜像推送到内网仓库，客户环境通过内网地址拉取镜像，完全绕开公网依赖。

### 离线依赖包准备

Python 依赖包在离线环境中需要提前准备。使用 pip download 将所有依赖下载到本地，打包后传输到客户环境。

```bash
# 在有网环境下载依赖
pip download -r requirements.txt -d ./packages

# 打包
tar -czf packages.tar.gz packages/

# 在离线环境安装
tar -xzf packages.tar.gz
pip install --no-index --find-links=./packages -r requirements.txt
```

### 网络分区通信方案

在严格的网络分区环境中，不同区域之间的通信需要通过特定的中间层。常见模式是在 DMZ (Demilitarized Zone, 隔离区) 部署反向代理，内网通过 DMZ 代理访问外部服务，外部请求也通过 DMZ 代理访问内网服务。

```
[外部网络] <---> [DMZ 反向代理] <---> [内网 AI Agent 服务]
                      |
                      v
               [核心数据区] (严格限制)
```

在这种架构下，需要配置 Nginx 或 HAProxy 作为反向代理，负责跨区域请求的转发和安全校验。同时需要在防火墙上开放必要的端口，并配置访问控制列表。

### 延展：网络诊断工具包

建议在部署前准备一套网络诊断工具包，用于快速定位网络问题。工具包应包含以下能力：

端口连通性检测：使用 nc (Netcat) 或 telnet 检测目标端口是否可达。带宽测试：使用 iperf3 测试网络吞吐量。DNS 解析检测：使用 nslookup 或 dig 检查域名解析。TLS 证书验证：使用 openssl s_client 检查证书链。

将这些工具封装为一键诊断脚本，在部署前运行，可以提前发现大部分网络问题，避免部署过程中断。

## 7.6 模型量化与资源优化

在私有化部署场景中，GPU 资源往往是最大的成本项。模型量化技术可以在几乎不损失推理质量的前提下，显著降低模型对显存的需求，使得在有限硬件上部署更大模型成为可能。

### 量化方法对比

模型量化是将模型参数从高精度浮点数转换为低精度表示的过程。主流的量化方法有以下几种：

| 量化方法 | 原始精度 | 量化精度 | 显存节省 | 质量损失 | 推理加速 | 适用场景 |
|---------|---------|---------|---------|---------|---------|---------|
| FP16 | FP32 | FP16 | 约50% | 极小 | 1.5-2x | 默认选择 |
| BF16 | FP32 | BF16 | 约50% | 极小 | 1.5-2x | 训练+推理 |
| INT8 (PTQ) | FP32 | INT8 | 约75% | 小 | 2-3x | 资源受限 |
| INT4 (GPTQ) | FP32 | INT4 | 约87.5% | 中等 | 2-4x | 极限压缩 |
| INT4 (AWQ) | FP32 | INT4 | 约87.5% | 较小 | 2-4x | 推荐方案 |
| GGUF Q4_K_M | FP32 | 4-bit | 约87.5% | 较小 | 1.5-3x | CPU 推理 |
| FP8 (NVIDIA) | FP32 | FP8 | 约75% | 极小 | 2-3x | H100/L40S |

### AWQ 量化实践

AWQ (Activation-aware Weight Quantization) 是目前质量最优的 INT4 量化方法之一。它通过分析激活值分布来保护重要权重，在大幅压缩模型的同时保持良好的推理质量。

```python
# AWQ 量化流程示例
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "/models/Qwen2.5-14B-Instruct"
quant_path = "/models/Qwen2.5-14B-Instruct-AWQ"

# 加载量化配置
quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM"
}

# 加载模型并量化
model = AutoAWQForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)
model.quantize(tokenizer, quant_config=quant_config)

# 保存量化后的模型
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
```

量化后的模型可以直接被 vLLM 加载，只需在启动参数中指定 quantization：

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /models/Qwen2.5-14B-Instruct-AWQ \
    --quantization awq \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.85
```

### 显存占用实测对比

以 Qwen2.5-14B 模型为例，不同量化方式在单张 A100 (80GB) 上的实际表现：

| 量化方式 | 模型占用 | KV Cache 可用 | 最大并发 | TTFT | 吞吐量 |
|---------|---------|-------------|---------|------|--------|
| FP16 | 约 28GB | 约 50GB | 30+ | 320ms | 1200 tok/s |
| INT8 | 约 15GB | 约 63GB | 40+ | 280ms | 1800 tok/s |
| AWQ INT4 | 约 8GB | 约 70GB | 50+ | 250ms | 2200 tok/s |

可以看到，INT4 量化不仅节省了显存，还因为减少了内存带宽压力而提升了推理速度。

### CPU 推理优化

在某些场景下，客户没有 GPU 资源或 GPU 资源不足，需要使用 CPU 进行推理。虽然 CPU 推理速度远不如 GPU，但通过合理优化，可以满足低并发场景的需求。

GGUF (GPT-Generated Unified Format) 是为 CPU 推理优化的模型格式。Ollama 和 llama.cpp 使用 GGUF 格式，通过 SIMD (Single Instruction Multiple Data) 指令集加速推理。

```bash
# 使用 Ollama 加载 GGUF 模型
ollama create qwen2.5-14b -f Modelfile

# Modelfile 内容
# FROM /models/qwen2.5-14b-q4_k_m.gguf
# PARAMETER num_ctx 4096
# PARAMETER num_thread 8
# PARAMETER temperature 0.7
```

CPU 推理的性能关键在于内存带宽。使用多通道高频内存（如 DDR5 5600MHz）可以显著提升推理速度。在双路服务器上，确保模型分布在 NUMA (Non-Uniform Memory Access) 节点上，避免跨节点内存访问。

### 延展：KV Cache 优化

除了模型权重的量化，KV Cache 的优化也是节省显存的重要手段。vLLM 支持多种 KV Cache 量化选项。

KV Cache INT8 量化可以将缓存大小减半，对长上下文场景效果显著。配置方式为在启动参数中添加 --kv-cache-dtype int8。FP8 量化在 Hopper 架构 GPU 上提供更好的精度和速度。

此外，Prefix Caching (前缀缓存) 技术可以缓存相同前缀的 KV Cache，对于系统提示词固定的场景可以显著降低重复计算。在 vLLM 中通过 --enable-prefix-caching 开启。

### 资源调度优化

在多租户场景下，合理的资源调度可以最大化硬件利用率。建议根据请求优先级分配资源：高优先级请求分配更多 KV Cache 空间，低优先级请求在队列中等待。通过设置最大等待时间，避免低优先级请求无限等待。

对于批处理请求，动态调整 batch size。在 GPU 负载较低时增大 batch size 提升吞吐量，在负载较高时减小 batch size 降低延迟。

## 7.7 高可用部署架构设计

生产环境的 AI Agent 系统需要具备高可用性，避免单点故障导致服务中断。高可用架构的设计需要从应用层、推理层、数据层三个维度进行考虑，通过冗余部署、负载均衡和故障转移机制保障服务持续可用。

### 高可用架构总览

```
                      [用户请求]
                          |
                          v
                 +--------+--------+
                 |   负载均衡器     |
                 | (Nginx/HAProxy) |
                 +--------+--------+
                          |
           +--------------+--------------+
           |              |              |
    +------v------+ +-----v------+ +----v-------+
    | Agent 实例1 | | Agent 实例2 | | Agent 实例3 |
    | (无状态)    | | (无状态)    | | (无状态)    |
    +------+------+ +-----+------+ +----+-------+
           |              |              |
           +------+-------+------+-------+
                  |              |
           +------v------+ +-----v------+
           | LLM 推理节点1| | LLM 推理节点2|
           | (主)         | | (备/负载)   |
           +------+------+ +-----+------+
                  |              |
           +------v--------------v------+
           |      共享存储层            |
           | (Redis + 向量数据库 + DB) |
           +---------------------------+
```

### 应用层高可用

AI Agent 应用层应设计为无状态服务，所有状态信息存储在 Redis 或外部存储中。无状态设计使得实例可以随时增减，配合负载均衡器实现水平扩展。

```nginx
# Nginx 负载均衡配置
upstream agent_backend {
    least_conn;
    server 10.0.1.11:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.13:8080 max_fails=3 fail_timeout=30s backup;
}

server {
    listen 443 ssl;
    server_name agent.company.com;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    location / {
        proxy_pass http://agent_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 5s;
        proxy_read_timeout 300s;
    }

    location /health {
        access_log off;
        return 200 "ok";
    }
}
```

关键配置说明：least_conn 策略将请求分配给连接数最少的实例；max_fails 和 fail_timeout 配置健康检查；backup 参数指定备份实例。

### 推理层高可用

LLM 推理服务的高可用比应用层更复杂，因为推理服务是有状态的（模型加载到 GPU 内存中）。常见策略是主备模式和双活模式。

主备模式：部署两个推理节点，一个主节点处理请求，一个备节点保持模型加载但待命。主节点故障时，负载均衡器将请求切换到备节点。切换时间通常在 10-30 秒。

双活模式：两个推理节点同时处理请求，通过负载均衡器分发流量。如果一个节点故障，另一个节点承担全部负载。双活模式需要确保单个节点有足够资源处理全部流量，否则需要降级策略。

```python
# 推理服务健康检查端点
from fastapi import FastAPI
import torch

app = FastAPI()

@app.get("/health")
async def health_check():
    checks = {
        "model_loaded": model is not None,
        "gpu_available": torch.cuda.is_available(),
        "gpu_memory_free": torch.cuda.mem_get_info()[0]
            if torch.cuda.is_available() else 0,
    }
    all_healthy = all([
        checks["model_loaded"],
        checks["gpu_available"],
        checks["gpu_memory_free"] > 1e9  # 至少1GB空闲
    ])
    return {"status": "healthy" if all_healthy else "degraded",
            "checks": checks}
```

### 数据层高可用

数据层的高可用需要根据存储类型分别设计。

Redis 集群：使用 Redis Sentinel 或 Redis Cluster 实现自动故障转移。Sentinel 模式适合主从架构，Cluster 模式适合分片场景。对于会话缓存等场景，Sentinel 模式即可满足需求。

向量数据库：Qdrant 支持集群部署，通过分片和副本实现高可用。建议至少部署 3 个节点，配置 2 个副本。写入操作通过一致性协议确保数据一致性。

PostgreSQL 数据库：使用流复制实现主从同步，配合 Patroni 实现自动故障转移。主节点故障时，Patroni 自动将从节点提升为主节点。

### 故障转移流程

当某个组件发生故障时，系统应自动执行故障转移流程：

```
组件故障检测 (健康检查失败)
        |
        v
负载均衡器摘除故障节点
        |
        v
请求转发到健康节点
        |
        v
触发告警通知运维人员
        |
        v
自动尝试重启故障节点
        |
   +----+----+
   |         |
恢复成功   恢复失败
   |         |
重新加入   人工介入
负载均衡
```

### 延展：优雅降级策略

在资源严重不足或多个节点同时故障的情况下，系统应能优雅降级而非完全不可用。

推理服务降级：当所有 GPU 节点不可用时，切换到 CPU 推理或调用备用的小模型 API。虽然响应速度下降，但服务保持可用。功能裁剪降级：关闭非核心功能（如多模态理解、长文档处理），只保留基础对话能力。流量控制降级：通过限流降低请求量，确保已接受的请求能够正常处理。

降级策略应在代码中预埋开关，通过配置中心或环境变量控制，避免在故障发生时临时修改代码。建议定期进行故障演练，验证降级策略的有效性。

## 7.8 K8s vs Docker Compose 选型

容器编排工具的选择是私有化部署架构设计的重要决策。K8s 和 Docker Compose 是两种最常用的方案，它们在功能丰富度、运维复杂度和适用场景上有显著差异。

### 核心维度对比

| 对比维度 | Kubernetes | Docker Compose |
|---------|-----------|----------------|
| 学习曲线 | 陡峭 | 平缓 |
| 部署复杂度 | 高 | 低 |
| 集群管理 | 原生支持 | 不支持 |
| 自动扩缩容 | 原生支持 (HPA/VPA) | 不支持 |
| 服务发现 | 内置 DNS | 依赖容器名 |
| 负载均衡 | 内置 Service | 需手动配置 |
| 滚动更新 | 原生支持 | 需脚本辅助 |
| 健康检查 | liveness/readiness probe | HEALTHCHECK 指令 |
| 配置管理 | ConfigMap/Secret | 环境变量/.env 文件 |
| GPU 调度 | Device Plugin | --gpus 参数 |
| 存储管理 | PV/PVC | volumes |
| 网络策略 | NetworkPolicy | 无 |
| 资消耗 | 较高 (控制面) | 极低 |
| 单机适用性 | 过重 | 合适 |
| 最低节点数 | 建议3+ | 1 |
| 运维人员要求 | 专业 K8s 运维 | 基础运维 |

### Docker Compose 适用场景

Docker Compose 适合以下场景：单机部署或双机主备部署；团队没有专业 K8s 运维人员；部署节点数少于 5 个；业务规模固定，不需要弹性扩展；部署环境资源有限，无法运行 K8s 控制面。

在实际项目中，许多中小型客户的私有化部署使用 Docker Compose 即可满足需求。配合自动化脚本实现更新和备份，可以达到不错的运维效果。

### K8s 适用场景

K8s 适合以下场景：多节点集群部署；需要自动扩缩容；微服务架构，服务数量多；需要灰度发布和滚动更新；有专业 DevOps 团队；对可用性要求极高。

对于大型企业客户，K8s 通常是标准化的基础设施平台。AI Agent 系统部署到 K8s 上可以与现有基础设施无缝融合，利用平台能力实现自动化运维。

### K8s 部署示例

以下是一个 AI Agent 服务在 K8s 上的部署清单示例：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-app
  namespace: ai-agent
  labels:
    app: agent-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-app
  template:
    metadata:
      labels:
        app: agent-app
    spec:
      containers:
      - name: agent-app
        image: registry.internal/agent-app:v1.2.0
        ports:
        - containerPort: 8080
        env:
        - name: LLM_ENDPOINT
          value: "http://llm-service:8000/v1"
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
  namespace: ai-agent
spec:
  selector:
    app: agent-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### GPU 节点调度

在 K8s 上调度 GPU 任务需要安装 NVIDIA Device Plugin。安装后，可以在 Pod 规格中请求 GPU 资源：

```yaml
spec:
  containers:
  - name: llm-server
    image: registry.internal/llm-server:v1.0
    resources:
      limits:
        nvidia.com/gpu: 2
    volumeMounts:
    - name: models
      mountPath: /models
      readOnly: true
  volumes:
  - name: models
    hostPath:
      path: /data/models
      type: Directory
  nodeSelector:
    accelerator: nvidia-a100
```

### 选型决策建议

在实际项目中，选型决策应遵循以下原则：

业务规模是首要考量。如果部署节点数在 3 个以内，Docker Compose 是更务实的选择。K8s 的控制面本身就需要至少 1-2 个节点的资源开销，在小规模部署中性价比不高。

运维能力决定上限。K8s 的强大功能需要专业运维来支撑。如果团队没有 K8s 经验，贸然使用会带来运维风险。Docker Compose 虽然功能有限，但运维简单，出问题容易定位。

未来扩展预留空间。如果预期业务会快速增长，需要频繁扩容，那么即使初期规模较小，也建议选择 K8s。后续从 Docker Compose 迁移到 K8s 的成本较高。

### 延展：轻量级 K8s 发行版

对于想要使用 K8s 但又觉得标准版太重的场景，可以考虑轻量级 K8s 发行版。

K3s 是 Rancher 推出的轻量级 K8s，将所有组件打包为单个二进制文件，资源开销极低。适合边缘计算和资源受限环境。单节点 K3s 可以替代 Docker Compose，同时保留 K8s API 兼容性。

MicroK8s 是 Canonical 推出的轻量级 K8s，通过 snap 安装，适合开发测试环境。支持一键启用 GPU、DNS、存储等附加组件。

这些轻量级方案在功能上与标准 K8s 基本兼容，但在高可用控制面方面有所限制。对于生产环境，建议使用标准 K8s 或至少 K3s 的高可用模式。

## 7.9 部署后健康检查与验证

部署完成并不意味着工作结束。全面的健康检查和验证是确保系统稳定运行的关键步骤。一套完善的健康检查流程可以在问题影响用户之前发现并解决。

### 健康检查清单

| 检查类别 | 检查项 | 验证方法 | 预期结果 |
|---------|--------|---------|---------|
| 基础设施 | GPU 可用性 | nvidia-smi | 所有 GPU 状态正常 |
| 基础设施 | 磁盘空间 | df -h | 剩余空间 > 20% |
| 基础设施 | 内存使用 | free -h | 使用率 < 80% |
| 基础设施 | 网络连通 | ping/curl | 所有内部组件可达 |
| 容器状态 | 容器运行 | docker ps | 所有容器 Up |
| 容器状态 | 容器健康 | docker inspect | Health: healthy |
| 容器状态 | 日志错误 | docker logs | 无 ERROR 级别日志 |
| 模型服务 | 模型加载 | POST /v1/models | 返回模型列表 |
| 模型服务 | 推理测试 | POST /v1/chat/completions | 正常返回结果 |
| 模型服务 | 响应延迟 | 多次请求计时 | TTFT < 500ms |
| Agent 服务 | API 可达 | curl /health | 200 OK |
| Agent 服务 | 功能验证 | 发送测试对话 | 正确响应 |
| Agent 服务 | 工具调用 | 触发工具调用 | 工具正确执行 |
| 数据存储 | Redis 连接 | redis-cli ping | PONG |
| 数据存储 | 向量数据库 | Qdrant health API | green |
| 数据存储 | 数据库连接 | pg_isready | accepting |
| 安全 | TLS 证书 | openssl s_client | 证书有效 |
| 安全 | 防火墙规则 | iptables -L | 仅必要端口开放 |
| 安全 | 访问日志 | 检查日志 | 无异常访问 |

### 自动化健康检查脚本

```bash
#!/bin/bash
# deploy_health_check.sh - 部署后健康检查脚本

PASS=0
FAIL=0

check() {
    local name=$1
    local cmd=$2
    local expected=$3
    local result=$(eval "$cmd" 2>&1)
    if echo "$result" | grep -q "$expected"; then
        echo "[PASS] $name"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $name: $result"
        FAIL=$((FAIL + 1))
    fi
}

# 基础设施检查
check "GPU 可用性" "nvidia-smi --query-gpu=name --format=csv,noheader" "NVIDIA"
check "磁盘空间" "df -h / | awk 'NR==2{print \$5}' | tr -d '%'" "[0-9]"
check "内存使用" "free | awk '/Mem/{printf \"%.0f\", \$3/\$2*100}'" "[0-9]"

# 容器状态检查
check "LLM 服务容器" "docker inspect -f '{{.State.Status}}' llm-server" "running"
check "Agent 服务容器" "docker inspect -f '{{.State.Status}}' agent-app" "running"
check "Redis 容器" "docker inspect -f '{{.State.Status}}' redis-cache" "running"
check "向量数据库容器" "docker inspect -f '{{.State.Status}}' vector-db" "running"

# 服务端点检查
check "LLM 健康检查" "curl -s http://localhost:8000/health" "ok"
check "Agent 健康检查" "curl -s http://localhost:8080/health" "ok"
check "Redis 连接" "docker exec redis-cache redis-cli ping" "PONG"

# 模型推理测试
check "模型列表" "curl -s http://localhost:8000/v1/models | grep model" "model"

echo ""
echo "========================="
echo "通过: $PASS  失败: $FAIL"
echo "========================="
exit $FAIL
```

### 功能性验证测试

除了基础设施层面的健康检查，还需要进行功能性验证，确保 AI Agent 的核心功能正常。

对话能力验证：发送一组标准测试问题，验证回复的完整性和正确性。测试问题应覆盖不同类型：事实性问答、推理任务、多轮对话、代码生成等。

工具调用验证：测试 Agent 是否能正确调用配置的工具。例如，让 Agent 查询客户信息，验证它是否正确调用了 CRM API 并返回结果。

知识库检索验证：测试 RAG (Retrieval-Augmented Generation) 功能是否正常。发送与知识库内容相关的问题，验证 Agent 是否能检索到正确的文档片段并基于其内容回答。

流式输出验证：测试 SSE (Server-Sent Events) 流式响应是否正常工作。验证首字延迟和整体流畅度。

### 性能基准测试

部署后应进行性能基准测试，建立性能基线，供后续对比参考。

```python
import asyncio
import time
import httpx

async def benchmark_llm():
    """LLM 推理性能基准测试"""
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": "Qwen2.5-14B-Instruct",
        "messages": [{"role": "user", "content": "请用200字介绍人工智能的发展历程"}],
        "max_tokens": 300,
        "stream": False
    }

    results = []
    for i in range(10):
        start = time.time()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60)
            elapsed = time.time() - start
            results.append(elapsed)

    avg = sum(results) / len(results)
    p50 = sorted(results)[len(results)//2]
    p99 = sorted(results)[int(len(results)*0.99)]
    print(f"平均: {avg:.2f}s  P50: {p50:.2f}s  P99: {p99:.2f}s")

asyncio.run(benchmark_llm())
```

### 延展：持续监控体系

健康检查不应只在部署后执行一次，而应建立持续监控体系。

基础设施监控：使用 Prometheus + Grafana 监控 CPU、内存、磁盘、网络等基础指标。配置告警规则，在指标异常时自动通知。

应用监控：在 Agent 应用中埋点，记录请求量、响应时间、错误率等业务指标。使用 OpenTelemetry 采集链路追踪数据，便于问题定位。

日志聚合：使用 ELK (Elasticsearch, Logstash, Kibana) 或 Loki 聚合所有容器的日志。配置日志告警规则，在出现 ERROR 级别日志时触发通知。

建议制定监控告警的分级响应机制：P0 级别（服务不可用）立即电话通知；P1 级别（性能严重下降）5 分钟内即时消息通知；P2 级别（异常但不影响服务）邮件通知并记录工单。

## 7.10 数据迁移策略与实施

在 AI Agent 系统的私有化部署中，数据迁移是一个容易被低估的环节。无论是从旧系统迁移到新系统，还是从开发环境迁移到生产环境，数据迁移都需要周密的计划和严格的执行。不当的数据迁移可能导致数据丢失、服务中断或数据不一致等严重问题。

### 数据迁移的类型

在私有化部署场景中，数据迁移通常涉及以下几种类型：

| 迁移类型 | 源端 | 目标端 | 数据量 | 复杂度 | 迁移窗口 |
|---------|------|--------|-------|--------|---------|
| 知识库迁移 | 开发环境 | 生产环境 | 中大 | 中 | 计划内 |
| 会话历史迁移 | 旧系统 | 新系统 | 中 | 中 | 计划内 |
| 用户数据迁移 | CRM/OA | Agent 系统 | 中 | 高 | 计划内 |
| 模型权重迁移 | 构建环境 | 生产环境 | 大 | 低 | 计划内 |
| 向量索引迁移 | 开发环境 | 生产环境 | 中 | 中 | 计划内 |
| 灾备数据迁移 | 主集群 | 灾备集群 | 持续 | 高 | 实时 |
| 版本升级迁移 | 旧版本 | 新版本 | 全量 | 高 | 计划内 |

### 迁移策略对比

不同的迁移策略适用于不同的场景，需要根据业务要求、数据量和停机窗口选择合适的策略。

| 策略名称 | 描述 | 停机时间 | 数据一致性 | 回滚难度 | 适用场景 |
|---------|------|---------|-----------|---------|---------|
| 停机迁移 | 停止服务，全量迁移 | 长 | 高 | 易 | 首次部署 |
| 双写迁移 | 新旧系统同时写入 | 短 | 高 | 中 | 版本升级 |
| 增量迁移 | 先全量后增量同步 | 极短 | 高 | 难 | 大数据量 |
| 蓝绿迁移 | 两套环境切换 | 几乎为零 | 高 | 易 | 环境升级 |
| 滚动迁移 | 分批迁移数据 | 零 | 中 | 中 | 分片数据 |
| CDC 迁移 | 基于变更日志同步 | 零 | 高 | 难 | 数据库迁移 |

### 知识库数据迁移

知识库是 AI Agent 系统中最核心的数据资产之一。知识库迁移不仅涉及文档文件的传输，还包括向量索引的重建或迁移。

文件迁移阶段：将文档文件从源端复制到目标端。使用 rsync 增量同步可以减少传输量。传输完成后进行 MD5 校验，确保文件完整性。

```bash
# 知识库文件增量同步
rsync -avz --progress \
    --checksum \
    /source/knowledge-base/ \
    user@target-server:/data/knowledge-base/

# 校验文件完整性
find /data/knowledge-base -type f -exec md5sum {} + | sort > target_md5.txt
diff source_md5.txt target_md5.txt
```

向量索引迁移阶段：如果目标环境的向量数据库类型与源端相同，可以直接导出导入向量数据。如果不同，需要重新进行文本嵌入计算。

```python
# Qdrant 向量数据导出
from qdrant_client import QdrantClient

source_client = QdrantClient(url="http://source:6333")
target_client = QdrantClient(url="http://target:6333")

# 分批导出并导入
offset = 0
batch_size = 1000
collection = "knowledge_base"

while True:
    records, next_offset = source_client.scroll(
        collection_name=collection,
        limit=batch_size,
        offset=offset
    )
    if not records:
        break
    target_client.upsert(
        collection_name=collection,
        points=records
    )
    offset = next_offset
    print(f"已迁移 {offset} 条记录")
```

### 会话历史迁移

会话历史数据通常存储在 Redis 或数据库中。迁移时需要注意数据格式兼容性和时间顺序一致性。

Redis 数据迁移可以使用 RDB 文件或 AOF 文件直接迁移，也可以使用 redis-shake 工具进行增量同步。

```bash
# 使用 redis-shake 进行数据迁移
# shake.conf
[source]
address = "source-redis:6379"
password = "source_password"

[target]
address = "target-redis:6379"
password = "target_password"

[advanced]
rdbParallel = 2
# 启动迁移
./redis-shake.linux -conf=shake.conf -type=sync
```

数据库数据迁移推荐使用 pg_dump/pg_restore 进行 PostgreSQL 数据迁移，或使用 mysqldump 进行 MySQL 数据迁移。对于大规模数据，使用数据库原生工具的并行导出导入功能可以显著缩短迁移时间。

### 模型权重迁移

模型权重文件通常较大（14B 模型约 28GB），迁移时需要考虑传输效率和文件完整性。

```bash
# 大文件分块传输与校验
# 源端分块
split -b 1G model.bin model_part_

# 传输后合并
cat model_part_* > model.bin

# SHA256 完整性校验
sha256sum model.bin > model.sha256
# 目标端验证
sha256sum -c model.sha256
```

对于内网环境，建议使用内网文件服务器或对象存储（如 MinIO）作为中转，避免直接点对点传输的稳定性问题。

### 迁移验证与回滚

迁移完成后，必须进行全面的验证，确保数据完整性和一致性。

数据量校验：对比源端和目标端的记录数，确保数量一致。对于向量数据库，对比集合中的点数；对于关系数据库，对比表行数。

抽样比对：随机抽取若干条记录，对比字段内容是否一致。对于向量数据，可以计算余弦相似度验证。

功能验证：在目标环境执行典型业务流程，验证数据能够被正确读取和使用。

回滚预案：迁移前准备回滚脚本和数据备份。如果迁移后发现问题，能够在最短时间内回滚到迁移前状态。回滚预案应包含数据备份位置、回滚步骤、验证方法和通知流程。

### 延展：数据迁移的工程化

在企业级部署中，数据迁移应该工程化、自动化，避免人工操作带来的风险。

建议构建迁移工具集，包含以下组件：数据导出器，负责从源端提取数据；数据传输器，负责安全传输数据；数据导入器，负责将数据写入目标端；数据校验器，负责验证迁移结果的完整性和一致性；迁移编排器，负责协调各组件的执行顺序和异常处理。

将迁移流程封装为可重复执行的脚本或工具，配合 CI/CD (Continuous Integration/Continuous Deployment, 持续集成/持续部署) 流水线，可以实现一键迁移。每次迁移自动生成迁移报告，记录迁移时间、数据量、校验结果等关键信息。

对于需要频繁迁移的场景（如多客户部署），可以进一步将迁移工具容器化，通过 Docker 运行迁移任务，确保迁移环境的一致性和可重复性。迁移工具镜像中预置所有必要的依赖和配置，运维人员只需指定源端和目标端信息即可执行迁移。

### 本章知识点总结

| 序号 | 知识点 | 核心要点 |
|------|--------|---------|
| 1 | 私有化部署模式 | 完全离线、内网、混合三种模式，根据安全等级和硬件条件选型 |
| 2 | LLM 推理框架 | vLLM 适合高性能场景，Ollama 适合轻量部署，TGI 适合 HF 生态 |
| 3 | 系统集成方案 | API 网关为核心枢纽，支持 RESTful API、Webhook、SSO 等多种集成方式 |
| 4 | Docker 化部署 | 多阶段构建优化镜像，Docker Compose 编排多组件，GPU 支持需 NVIDIA Toolkit |
| 5 | 网络限制应对 | 代理配置、内网镜像仓库、离线依赖包准备、网络分区通信方案 |
| 6 | 模型量化优化 | AWQ INT4 量化是推荐方案，显存节省约 87.5%，推理速度也有提升 |
| 7 | 高可用架构 | 无状态应用层 + 主备/双活推理层 + 冗余数据层，配合故障自动转移 |
| 8 | 编排工具选型 | 小规模用 Docker Compose，大规模用 K8s，轻量场景可考虑 K3s |
| 9 | 健康检查验证 | 部署后执行基础设施、容器、服务、功能四层检查，建立持续监控体系 |
| 10 | 数据迁移策略 | 根据场景选择停机/增量/双写等策略，迁移后必须验证并准备回滚预案 |

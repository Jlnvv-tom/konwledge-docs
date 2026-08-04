# 第八章：上线运维与持续迭代

Agent 系统的上线只是工程化的起点，真正的挑战在于如何让系统在长期运行中保持稳定、高效且持续进化。与传统的 Web 服务不同，Agent 系统包含 LLM (Large Language Model, 大语言模型) 调用、Prompt 工程链路、知识库检索等多个动态环节，任何一个环节的退化都可能导致整体输出质量的下降。本章将从监控、日志、故障处理、质量优化、反馈分析、A/B 测试、版本管理、成本优化、知识库维护以及容量规划十个维度，系统性地阐述 Agent 上线后的运维与迭代方法论。

## 8.1 Agent 系统监控指标体系

监控系统是 Agent 运维的眼睛。一个完善的监控体系应当覆盖从基础设施到业务效果的全链路指标，使得运维人员能够在问题影响用户之前就感知到异常。

### 指标分类框架

Agent 系统的监控指标可以按照"基础设施层 - 服务层 - Agent 层 - 业务层"四级架构进行划分。每一层关注的核心问题不同，告警策略也各有差异。

| 层级 | 指标类别 | 核心指标示例 | 告警阈值建议 |
|------|---------|-------------|-------------|
| 基础设施层 | 计算资源 | CPU 使用率、内存使用率、磁盘 I/O | CPU > 80% 持续 5min |
| 基础设施层 | 网络资源 | 网络吞吐量、TCP 连接数 | 连接数 > 10000 |
| 服务层 | API 网关 | QPS (Queries Per Second)、错误率、P99 延迟 | 错误率 > 1% 或 P99 > 3s |
| 服务层 | 依赖服务 | 数据库连接池、Redis 命中率 | Redis 命中率 < 90% |
| Agent 层 | LLM 调用 | Token 消耗量、调用成功率、首 Token 延迟 | 调用失败率 > 2% |
| Agent 层 | 检索链路 | 召回数量、Rerank 耗时、检索命中率 | 检索命中率 < 60% |
| Agent 层 | Prompt 执行 | Prompt 长度、工具调用次数、重试次数 | 重试次数 > 3 |
| 业务层 | 用户体验 | 会话满意度、首次响应时间、任务完成率 | 任务完成率 < 85% |
| 业务层 | 业务效果 | 回答准确率、用户修正率、转人工率 | 转人工率 > 15% |

### 关键指标详解

在上述指标中，有几项值得特别关注。

首 Token 延迟（Time To First Token, TTFT）是衡量用户体验的核心指标。用户对 Agent 响应的感知往往不是看总耗时，而是看"是否在开始有反应"。一般来说，TTFT 应控制在 1 秒以内，超过 2 秒用户会明显感知到卡顿。

Token 消耗速率是一个成本相关指标，但也直接影响服务质量。如果某个会话的 Token 消耗突然飙升，可能是 Prompt 膨胀、上下文溢出或陷入了重复调用循环。通过设置单会话 Token 上限告警（例如单会话超过 50000 Token 即告警），可以在造成大规模成本损失前进行干预。

检索命中率反映了 RAG (Retrieval-Augmented Generation, 检索增强生成) 系统的健康度。如果检索命中率持续下降，可能是知识库内容过期、Embedding 模型版本不匹配或检索策略需要调优。

### 监控架构设计

监控数据采集应当采用 Push 模式为主、Pull 模式为辅的混合架构。Agent 服务通过 SDK 主动推送业务指标到指标收集器（如 Prometheus 的 Pushgateway），同时基础设施层的 Node Exporter 通过 Pull 方式被采集。

```
┌─────────────────────────────────────────────────┐
│                监控数据流向架构                    │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐    Push     ┌──────────────┐       │
│  │ Agent    │────────────>│ Pushgateway  │       │
│  │ Service  │             └──────┬───────┘       │
│  └────┬─────┘                    │               │
│       │                   ┌──────v───────┐       │
│       │ Pull              │  Prometheus  │       │
│  ┌────v─────┐             │   Server     │       │
│  │ Node     │<────────────┤              │       │
│  │ Exporter │             └──────┬───────┘       │
│  └──────────┘                    │               │
│                           ┌──────v───────┐       │
│                           │   Grafana    │       │
│                           │  Dashboard   │       │
│                           └──────────────┘       │
└─────────────────────────────────────────────────┘
```

告警规则应当采用多级策略。P0 级告警需要立即处理，通过电话或即时通讯工具通知 oncall 人员；P1 级告警在 15 分钟内响应；P2 级告警在工作时间内处理。避免告警风暴的关键在于合理设置告警窗口和聚合规则，例如"连续 3 个采集周期超过阈值才触发告警"。

### 指标采集代码示例

以下是一个基于 Python 的 Agent 服务指标采集示例：

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# 定义指标
llm_tokens_total = Counter(
    'agent_llm_tokens_total',
    'Total LLM tokens consumed',
    ['model', 'session_type']
)

llm_latency_seconds = Histogram(
    'agent_llm_latency_seconds',
    'LLM call latency in seconds',
    ['model', 'call_type'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

retrieval_hit_rate = Gauge(
    'agent_retrieval_hit_rate',
    'RAG retrieval hit rate',
    ['knowledge_base']
)

def track_llm_call(model, session_type, call_type, func, *args, **kwargs):
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        llm_latency_seconds.labels(model=model, call_type=call_type).observe(elapsed)
        llm_tokens_total.labels(model=model, session_type=session_type).inc(result.tokens_used)
        return result
    except Exception as e:
        llm_latency_seconds.labels(model=model, call_type=call_type).observe(60)
        raise
```

通过将指标采集嵌入到 Agent 调用链路中，可以实现全链路可观测。建议为每个关键环节都定义独立的指标，避免只看端到端指标而无法定位瓶颈。

## 8.2 日志管理分层架构

日志是故障排查的最后一道防线。当监控系统告诉你"出了什么问题"，日志系统需要告诉你"为什么出问题"。Agent 系统的日志复杂度远高于传统服务，因为一次用户请求可能涉及多轮 LLM 调用、多次检索、工具执行等步骤，如果不做结构化处理，日志将变成无法消费的数据沼泽。

### 日志分层设计

Agent 系统的日志应当分为四个层次，每层服务于不同的消费场景。

| 日志层级 | 记录内容 | 保留周期 | 典型消费者 |
|---------|---------|---------|-----------|
| Trace 级 | 完整请求/响应体、Prompt 全文、检索结果 | 7-30 天 | 算法工程师、调试 |
| Debug 级 | 中间状态、工具调用参数与返回、路由决策 | 3-7 天 | 开发工程师 |
| Info 级 | 请求摘要、会话 ID、耗时、Token 数 | 30-90 天 | 运维工程师 |
| Error 级 | 异常堆栈、错误码、上下文快照 | 90-180 天 | Oncall 工程师 |

### 分层架构图

```
┌─────────────────────────────────────────────────────┐
│                  日志分层架构                         │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Agent App  │  │  API Gateway│  │  Infra      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                │                │          │
│         v                v                v          │
│  ┌─────────────────────────────────────────────┐    │
│  │           日志采集层 (Fluentd / Vector)       │    │
│  └─────────────────────┬───────────────────────┘    │
│                        │                              │
│         ┌──────────────┼──────────────┐              │
│         v              v              v              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │  Hot Store │ │ Warm Store │ │ Cold Store │       │
│  │  (ES/Opensearch)│(S3+Athena)│  (S3 Glacier)│     │
│  │  0-7 days  │ │ 7-90 days  │ │ 90+ days   │       │
│  └────────────┘ └────────────┘ └────────────┘       │
│         │              │                              │
│         v              v                              │
│  ┌─────────────────────────────────────────────┐    │
│  │        日志查询层 (Kibana / Grafana Loki)     │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 结构化日志规范

所有日志应当采用 JSON 格式输出，包含以下标准字段。Trace 级日志需要额外记录 Agent 执行链路的完整信息。

```json
{
  "timestamp": "2026-08-03T10:30:45.123Z",
  "level": "INFO",
  "service": "agent-service",
  "trace_id": "trace-abc123",
  "session_id": "sess-xyz789",
  "user_id": "u-001",
  "event": "llm_call_start",
  "model": "gpt-4-turbo",
  "prompt_tokens": 1200,
  "metadata": {
    "tools_available": ["search", "calculator"],
    "rag_enabled": true,
    "knowledge_base_version": "v2.3.1"
  }
}
```

### Trace 链路追踪

Agent 系统的每次请求应当生成一个唯一的 Trace ID，并在所有子调用中传递。通过 Trace ID 可以还原一次完整请求的执行路径，包括用户输入解析、意图识别、检索、Prompt 组装、LLM 调用、工具执行、响应后处理等全部步骤。

以下是使用 OpenTelemetry 进行链路追踪的代码示例：

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

async def handle_user_request(self, user_input, session_id):
    with tracer.start_as_current_span("agent_request") as root_span:
        root_span.set_attribute("session.id", session_id)
        root_span.set_attribute("user.input_length", len(user_input))
        
        with tracer.start_as_current_span("retrieval"):
            docs = await self.retriever.search(user_input)
            span.set_attribute("retrieval.doc_count", len(docs))
        
        with tracer.start_as_current_span("llm_call"):
            response = await self.llm.generate(prompt, model="gpt-4-turbo")
            span.set_attribute("llm.tokens_used", response.tokens_used)
        
        with tracer.start_as_current_span("post_process"):
            result = self.postprocessor.format(response)
        
        return result
```

### 日志采样与脱敏

在生产环境中，Trace 级日志的存储成本很高。建议对正常请求采用 1% 采样的方式记录 Trace 日志，但对错误请求 100% 记录。这样可以兼顾排查需求和存储成本。

日志脱敏是合规要求。用户输入中可能包含 PII (Personally Identifiable Information, 个人身份信息)，如手机号、身份证号、邮箱等。日志采集层应当内置脱敏规则，在写入存储前完成替换。

```python
import re

PII_PATTERNS = {
    'phone': (re.compile(r'1[3-9]\d{9}'), '[PHONE]'),
    'email': (re.compile(r'[\w.-]+@[\w.-]+\.\w+'), '[EMAIL]'),
    'id_card': (re.compile(r'\d{17}[\dXx]'), '[ID_CARD]'),
}

def sanitize_log(text):
    for name, (pattern, replacement) in PII_PATTERNS.items():
        text = pattern.sub(replacement, text)
    return text
```

### 日志告警规则

日志系统也应当配置告警规则。与指标告警不同，日志告警关注的是模式匹配。例如，当 Error 级日志在 5 分钟内出现超过 10 条，或者出现特定错误模式（如 "OOMKilled"、"context deadline exceeded"）时，应当立即触发告警。

通过指标监控和日志告警的配合，可以构建起覆盖"数值异常"和"模式异常"的双维度告警体系，大幅提升问题发现的及时性和准确性。

## 8.3 线上故障处理流程与 SOP

Agent 系统的线上故障类型多样，从 LLM API 超时到知识库索引损坏，从 Prompt 注入攻击到成本异常飙升，每种故障都需要有对应的处理流程。本节将阐述标准化的故障处理 SOP (Standard Operating Procedure, 标准作业程序)。

### 故障分级标准

| 级别 | 定义 | 响应时间 | 处理时限 | 通知范围 |
|------|------|---------|---------|---------|
| P0 | 核心服务完全不可用 | 5 分钟内 | 1 小时内恢复 | 全员通知，升级至管理层 |
| P1 | 核心功能部分受损，影响大量用户 | 15 分钟内 | 4 小时内恢复 | Oncall 团队 + 技术负责人 |
| P2 | 非核心功能异常或影响少量用户 | 30 分钟内 | 1 个工作日内 | Oncall 工程师 |
| P3 | 体验问题或潜在风险 | 4 小时内 | 下个迭代解决 | 记录到工单系统 |

### 故障处理流程图

```
┌─────────────┐
│  告警触发    │
└──────┬──────┘
       v
┌─────────────┐     否     ┌──────────────┐
│  确认是否    │──────────>│  标记为误报   │
│  真实故障    │           │  优化告警规则 │
└──────┬──────┘           └──────────────┘
       v 是
┌─────────────┐
│  故障分级    │
│  (P0/P1/P2) │
└──────┬──────┘
       v
┌─────────────┐     P0      ┌──────────────┐
│  紧急通知    │──────────>│  启动应急预案 │
│  Oncall     │           │  流量降级/切换│
└──────┬──────┘           └──────┬───────┘
       v                         v
┌─────────────┐           ┌──────────────┐
│  初步定位    │<──────────│  快速恢复     │
│  故障范围    │           │  (止损优先)   │
└──────┬──────┘           └──────────────┘
       v
┌─────────────┐
│  深入排查    │
│  根因分析    │
└──────┬──────┘
       v
┌─────────────┐
│  实施修复    │
│  验证恢复    │
└──────┬──────┘
       v
┌─────────────┐
│  故障复盘    │
│  输出报告    │
└─────────────┘
```

### 常见故障场景与处理预案

**场景一：LLM API 不可用**

这是最常见的 P0/P1 故障。LLM 供应商可能因为自身故障、限流或网络问题导致 API 不可用。处理预案包括：自动切换到备用模型（如从 GPT-4 切换到 Claude 或国产模型）、启用缓存响应（对相似问题返回缓存的优质回答）、降级为纯检索模式（仅返回知识库匹配结果，不经过 LLM 生成）。

关键配置是设置多模型 Failover (故障转移) 策略：

```yaml
llm_failover:
  primary:
    provider: openai
    model: gpt-4-turbo
    timeout: 30s
    retry: 2
  secondary:
    provider: anthropic
    model: claude-3-sonnet
    timeout: 30s
    retry: 2
  fallback:
    provider: local
    model: cached-response
    timeout: 5s
```

**场景二：知识库检索质量突降**

可能原因包括：Embedding 模型版本不匹配、索引数据被误删、知识库内容更新引入了噪声。处理步骤：首先检查检索响应时间是否正常以排除基础设施问题，然后对比当前检索结果与历史基线，最后检查索引版本和 Embedding 模型版本是否一致。

**场景三：成本异常飙升**

当 Token 消耗速率超过历史均值 3 倍以上时触发告警。可能原因包括：Prompt 模板变更导致 Token 膨胀、某些用户恶意构造超长输入、Agent 陷入工具调用循环。处理预案：设置单用户/单会话 Token 上限，超过阈值自动熔断；启用实时成本看板，按小时粒度监控消耗趋势。

### 故障复盘规范

每次 P0/P1 故障都必须在 48 小时内完成复盘。复盘报告应当包含以下要素：故障时间线（从首次告警到完全恢复）、影响范围（用户数、会话数、业务损失）、根因分析（5 Whys 方法逐层追问）、处理过程评估（响应是否及时、预案是否有效）、改进措施（短期修复 + 长期优化，明确责任人和截止时间）。

复盘的目的是改进系统，而非追究责任。鼓励工程师在复盘中坦诚描述决策过程，以便发现流程中的改进点。

### Oncall 制度建设

建立 7x24 小时的 Oncall 轮值制度是保障故障响应的基础。建议采用主备 Oncall 模式：主 Oncall 负责一线响应，备 Oncall 提供升级支持。轮值周期建议为一周，交接在每周三上午进行（避开周一和周末的高峰期）。

Oncall 工程师需要配备完整的工具链支持：告警接收（ PagerDuty 或飞书告警）、远程接入（VPN + 跳板机）、操作手册（Runbook，包含各类型故障的标准处理步骤）、 escalation 路径（当主 Oncall 无法解决时，明确知道联系谁）。

## 8.4 Agent 回答质量持续优化

Agent 上线后，回答质量的维护和提升是一个永无止境的过程。LLM 的输出具有非确定性，同样的输入在不同时间可能产生不同输出，这使得质量保障比传统软件复杂得多。本节将阐述一套持续优化机制。

### 质量评估体系

回答质量的评估需要从多个维度进行。单靠人工评估无法覆盖海量会话，单靠自动指标又容易遗漏语义层面的问题。建议采用"自动评估 + 人工抽检 + 用户反馈"三位一体的评估体系。

| 评估维度 | 评估方法 | 评估频率 | 达标标准 |
|---------|---------|---------|---------|
| 准确性 | 人工标注 + LLM 评估 | 每日抽样 100 条 | 准确率 > 92% |
| 完整性 | LLM 评估 | 每日抽样 200 条 | 完整度 > 88% |
| 相关性 | 检索匹配度 + LLM 评估 | 实时 | 相关度 > 85% |
| 安全性 | 敏感词检测 + 安全模型 | 实时 | 违规率 < 0.1% |
| 连贯性 | LLM 评估 | 每日抽样 100 条 | 连贯性评分 > 4/5 |
| 工具使用正确性 | 规则校验 + 人工抽检 | 每日抽样 50 条 | 正确率 > 95% |

### 质量优化循环

质量优化应当遵循 PDCA (Plan-Do-Check-Act) 循环，但需要针对 Agent 系统的特点进行调整。

```
┌─────────────────────────────────────────────────┐
│              Agent 质量优化循环                    │
│                                                   │
│   ┌─────────┐                                    │
│   │ 问题发现 │<─────────────────────────┐        │
│   │  - 人工抽检                         │        │
│   │  - 用户反馈                          │        │
│   │  - 自动监控                          │        │
│   └────┬────┘                           │        │
│        v                                │        │
│   ┌─────────┐                           │        │
│   │ 归因分析 │                           │        │
│   │  - Prompt 问题                      │        │
│   │  - 检索问题                          │        │
│   │  - 模型能力问题                      │        │
│   └────┬────┘                           │        │
│        v                                │        │
│   ┌─────────┐    ┌─────────┐           │        │
│   │ 优化方案 │───>│ 灰度验证 │           │        │
│   │  - Prompt 调优                     │        │
│   │  - 检索策略调整                     │        │
│   │  - 模型切换                         │        │
│   └─────────┘    └────┬────┘           │        │
│                       v                 │        │
│                ┌─────────┐              │        │
│                │ 效果评估 │              │        │
│                │  - 对比基线             │        │
│                │  - 显著性检验           │        │
│                └────┬────┘              │        │
│                     v                    │        │
│              ┌─────────────┐            │        │
│              │ 是否达标？   │            │        │
│              └──┬──────┬───┘            │        │
│            是    │      │ 否             │        │
│                 v      └────────────────┘        │
│           ┌─────────┐                             │
│           │ 全量上线 │                             │
│           │ 更新基线 │                             │
│           └─────────┘                             │
└─────────────────────────────────────────────────┘
```

### LLM as Judge 评估方法

使用 LLM 来评估另一个 LLM 的输出质量是目前业界主流的自动化评估方法。关键在于评估 Prompt 的设计需要足够严谨，避免评估模型自身的偏好影响判断。

```python
EVALUATION_PROMPT = """
你是一个严格的质量评估专家。请按照以下标准对 Agent 的回答进行评分。

评估维度：
1. 准确性 (1-5分)：回答中的事实是否正确，是否与知识库内容一致
2. 完整性 (1-5分)：是否完整回答了用户的问题，有无遗漏关键信息
3. 相关性 (1-5分)：回答是否切题，有无无关内容
4. 安全性 (1-5分)：是否包含敏感、有害或不当内容

用户问题：{question}
知识库参考：{reference}
Agent 回答：{answer}

请输出 JSON 格式：
{{"accuracy": x, "completeness": x, "relevance": x, "safety": x, "reason": "..."}}
"""
```

需要注意的是，LLM as Judge 存在已知的偏差：倾向于给长回答更高分、倾向于给自身模型族系的输出更高分。为缓解这些偏差，建议使用与生成模型不同族系的评估模型，并在评估 Prompt 中明确要求"不要因为回答长度而加分"。

### 质量退化检测

质量退化是一个渐进过程，单日波动很难发现，但累积效应显著。建议建立以下退化检测机制：

基线对比：每周用固定的测试集（100-200 条标注样本）运行 Agent，将结果与上一周的基线进行对比。如果任意维度评分下降超过 5%，触发告警。

趋势分析：将每日的质量评分绘制成时间序列，使用移动平均和标准差计算控制上下限。当连续 3 天的评分低于控制下限时，触发质量退化告警。

分布漂移检测：监控 Agent 输出的特征分布（如回答长度、工具调用次数、拒绝回答比例等），当分布与历史均值偏差超过 2 个标准差时触发预警。分布漂移往往预示着某些隐含的变化，可能是用户行为变化，也可能是系统内部的退化。

## 8.5 用户反馈收集与分析

用户反馈是衡量 Agent 质量最直接的数据来源。与被动等待投诉不同，系统化的反馈收集机制能够主动发现问题，并为产品迭代提供方向。

### 反馈收集方法对比

| 收集方法 | 触发时机 | 数据质量 | 覆盖率 | 实现复杂度 | 偏差风险 |
|---------|---------|---------|--------|-----------|---------|
| 显式评分 | 每轮回答后 | 中等 | 5%-15% | 低 | 高（幸存者偏差） |
| 点赞/踩 | 每轮回答后 | 低 | 10%-25% | 低 | 中等 |
| 文字反馈 | 用户主动提交 | 高 | <2% | 低 | 高（极端用户主导） |
| 隐式信号 | 全程采集 | 中高 | 100% | 高 | 低 |
| 定期问卷 | 每月/每季度 | 高 | 10%-30% | 中 | 中等 |
| 用户访谈 | 季度 | 极高 | <1% | 高 | 低（样本量小） |

### 隐式反馈信号挖掘

显式反馈的覆盖率通常很低，且有明显的幸存者偏差——只有特别满意或特别不满意的用户才会留下反馈。隐式信号可以覆盖全部用户，提供更客观的质量画像。

以下是关键的隐式信号及其解读：

用户复制行为：当用户复制 Agent 的回答时，通常表示回答有价值。复制后的文本如果粘贴到搜索引擎，则可能表示用户对回答不信任或需要进一步验证。

重新提问行为：用户在同一会话中对同一问题重新提问（即使措辞不同），通常意味着上一次的回答未满足需求。这是最强的负向隐式信号之一。

会话中断：用户在 Agent 回答后立即离开且 24 小时内未回来，可能表示回答解决了问题（正向），也可能表示用户放弃了对话（负向）。需要结合回答的准确性和完整性来区分。

追问深度：用户在 Agent 回答后继续追问的深度（同一话题连续追问的轮数）是一个双刃剑指标。适度的追问表示对话在深入，过多的追问可能表示前序回答不够清晰。

```python
class ImplicitSignalCollector:
    def __init__(self):
        self.signals = []
    
    def on_copy(self, session_id, turn_id, text):
        self.signals.append({
            'session_id': session_id,
            'turn_id': turn_id,
            'signal_type': 'copy',
            'sentiment': 'positive',
            'weight': 1.0
        })
    
    def on_rephrase(self, session_id, topic_similarity):
        self.signals.append({
            'session_id': session_id,
            'signal_type': 'rephrase',
            'sentiment': 'negative',
            'weight': 2.0 * topic_similarity
        })
    
    def on_abandon(self, session_id, turn_id, last_answer_quality):
        sentiment = 'negative' if last_answer_quality < 0.6 else 'neutral'
        self.signals.append({
            'session_id': session_id,
            'turn_id': turn_id,
            'signal_type': 'abandon',
            'sentiment': sentiment,
            'weight': 1.5
        })
```

### 反馈分析流水线

收集到的反馈数据需要经过结构化处理才能转化为可执行的优化方向。分析流水线包括以下步骤：

第一步，反馈聚合。将同一会话内的多种信号（显式评分 + 隐式信号）合并为会话级质量分数。建议使用加权平均，显式反馈权重高于隐式信号。

第二步，问题分类。使用 LLM 对负面反馈进行自动分类，标注问题类型（事实错误、理解偏差、格式问题、安全风险、功能缺失等）。分类结果用于指导优化方向的优先级排序。

第三步，影响面评估。将问题按影响用户数和严重程度排序。一个影响 30% 用户的小问题可能比影响 1% 用户的大问题更值得优先解决。

第四步，行动映射。将分析结果映射到具体的优化行动。事实错误指向知识库修正，理解偏差指向 Prompt 优化，格式问题指向后处理规则调整，功能缺失指向产品迭代。

### 反馈数据存储模型

```sql
CREATE TABLE user_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    turn_id INT NOT NULL,
    user_id VARCHAR(64),
    feedback_type VARCHAR(32) NOT NULL,  -- explicit_rating, thumbs, text, implicit
    feedback_value JSONB NOT NULL,       -- {"score": 4, "comment": "..."}
    context JSONB,                       -- {"question": "...", "answer": "...", "tools_used": [...]}
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
);
```

建议将反馈数据与对话上下文存储在一起，这样在进行问题分析时可以还原完整的场景，而不仅仅看到脱节的评分数字。JSONB 格式允许灵活的字段扩展，适应未来新增的反馈类型。

## 8.6 A/B 测试设计与实施

A/B 测试是 Agent 迭代过程中的核心决策工具。通过控制变量对比实验，可以科学地验证优化措施的效果，避免凭直觉做决策带来的风险。Agent 系统的 A/B 测试与传统 Web 服务的 A/B 测试有显著差异，主要体现在效应量度量、网络效应控制和长尾评估等方面。

### A/B 测试流程

Agent 系统的 A/B 测试应当遵循以下标准化流程：

```
┌──────────────┐
│ 假设构建      │
│ "修改 Prompt  │
│  中的角色设定 │
│  可提升准确率"│
└──────┬───────┘
       v
┌──────────────┐
│ 指标定义      │
│ 主指标：准确率│
│ 辅助指标：延迟│
│ 护栏指标：成本│
└──────┬───────┘
       v
┌──────────────┐
│ 样本量计算    │
│ 基于基线准确率│
│ 和最小可检测  │
│ 效应量计算    │
└──────┬───────┘
       v
┌──────────────┐
│ 流量分配      │
│ 50/50 随机分桶│
│ 按用户维度分桶│
└──────┬───────┘
       v
┌──────────────┐
│ 实验运行      │
│ 最小运行周期  │
│ 7-14 天       │
└──────┬───────┘
       v
┌──────────────┐
│ 结果分析      │
│ 显著性检验    │
│ 分群分析      │
└──────┬───────┘
       v
┌──────────────┐
│ 决策与发布    │
│ 全量/迭代/放弃│
└──────────────┘
```

### 实验设计要点

**分流策略**：Agent 系统的 A/B 测试必须按用户维度而非请求维度分流。同一个用户在实验期间应当始终命中同一组，否则用户体验不一致会引入噪声。使用用户 ID 的哈希值进行分桶是标准做法。

**网络效应控制**：Agent 系统可能存在网络效应——如果部分用户的知识库反馈（如"踩"标记）会影响全局检索排序，实验组和对照组之间会产生干扰。解决方案是对有网络效应的功能进行时间片轮转测试，而非同时并行测试。

**最小可检测效应量 (MDE, Minimum Detectable Effect)**：Agent 系统的质量指标通常波动较大，需要设置合理的 MDE。如果基线准确率为 90%，MDE 设为 1%，在显著性水平 0.05 和统计功效 0.8 的条件下，每组需要约 13000 个样本。如果日活跃用户量为 10000，实验需要运行约 3 天才能达到统计显著性。

### 实验结果评估表

| 实验编号 | 实验内容 | 主指标变化 | 统计显著性 | 成本变化 | 决策 |
|---------|---------|-----------|-----------|---------|------|
| EXP-001 | Prompt 角色设定优化 | 准确率 +2.3% | p=0.012 | +0.5% | 全量发布 |
| EXP-002 | 检索 Top-K 从 5 调到 8 | 完整性 +1.5% | p=0.034 | +3.2% | 迭代优化 |
| EXP-003 | 切换到新 Embedding 模型 | 检索命中率 +4.1% | p=0.001 | +1.1% | 全量发布 |
| EXP-004 | 增加回答后自检步骤 | 准确率 +0.8% | p=0.156 | +12% | 放弃 |
| EXP-005 | 简化工具调用 Prompt | 工具正确率 +3.2% | p=0.008 | -8% | 全量发布 |

### 护栏指标的重要性

在追求主指标提升的同时，不能忽视护栏指标。护栏指标是那些"即使主指标提升了也不能恶化"的指标。对于 Agent 系统，典型的护栏指标包括：响应延迟（不能因质量优化而显著增加）、成本（Token 消耗不能大幅增加）、安全指标（违规率不能上升）。

实验 EXP-004 是一个典型案例：增加回答后自检步骤虽然让准确率有小幅提升，但统计不显著，同时成本增加了 12%（因为需要额外的 LLM 调用进行自检），延迟也增加了约 1.5 秒。综合评估后应当放弃。

### 实验平台代码示例

```python
import hashlib
import random

class ABTestRouter:
    def __init__(self, experiments_config):
        self.experiments = experiments_config
    
    def get_variant(self, user_id, experiment_name):
        exp = self.experiments.get(experiment_name)
        if not exp or not exp['active']:
            return 'control'
        
        # 用户ID哈希分桶
        hash_input = f"{user_id}:{experiment_name}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100
        
        for variant, ratio in exp['allocation'].items():
            if bucket < ratio[1] and bucket >= ratio[0]:
                return variant
        
        return 'control'

# 使用示例
router = ABTestRouter({
    'prompt_v2': {
        'active': True,
        'allocation': {
            'control': [0, 50],
            'treatment': [50, 100]
        }
    }
})

variant = router.get_variant(user_id="u-12345", experiment_name="prompt_v2")
prompt = prompt_v2 if variant == 'treatment' else prompt_v1
```

## 8.7 版本迭代管理策略

Agent 系统的迭代不仅仅是代码变更，还涉及 Prompt 模板、知识库内容、模型版本、检索策略等多个维度的变更。传统的 SemVer (Semantic Versioning, 语义化版本) 规范需要扩展才能适应 Agent 系统的特点。

### 版本号策略

Agent 系统建议采用四段式版本号：主版本.次版本.补丁版本.配置版本。主版本变更代表架构级调整（如从纯 RAG 切换到 Agent + 工具调用），次版本变更代表功能新增或显著优化，补丁版本变更代表 Bug 修复和小调整，配置版本变更代表 Prompt、知识库等配置项的更新。

| 变更类型 | 版本号变化 | 示例 | 发布策略 |
|---------|-----------|------|---------|
| 架构调整 | 主版本 +1 | v1.x.x.x -> v2.0.0.0 | 灰度 10% -> 50% -> 100% |
| 功能新增 | 次版本 +1 | v1.2.x.x -> v1.3.0.0 | 灰度 20% -> 100% |
| Bug 修复 | 补丁 +1 | v1.2.3.x -> v1.2.4.0 | 直接全量（可回滚） |
| Prompt 优化 | 配置 +1 | v1.2.3.4 -> v1.2.3.5 | 灰度 10% -> 50% -> 100% |
| 知识库更新 | 配置 +1 | v1.2.3.4 -> v1.2.3.5 | 蓝绿切换 |
| 模型升级 | 次版本 +1 | v1.2.x.x -> v1.3.0.0 | A/B 测试后全量 |

### 变更管理流程

所有变更必须通过变更评审委员会（Change Advisory Board, CAB）审批。评审内容包括：变更内容描述、影响面评估、回滚方案、验证标准。对于配置版本级别的变更（如 Prompt 调整），可以采用轻量级审批流程，由技术负责人审批即可。

关键原则是"可回滚"。每次发布都应当保留前一版本的完整快照（代码 + 配置 + 知识库索引），确保在出现问题时可以在 5 分钟内回滚到稳定版本。对于知识库变更，建议采用蓝绿部署：新版本索引在后台构建完成并通过验证后，通过原子切换操作将流量指向新版本。

### 发布流水线

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  代码提交 │───>│  CI 构建  │───>│  自动测试 │───>│  预发布  │
│  PR Review│    │  镜像打包 │    │  单元+集成│    │  环境验证│
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     v
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  全量发布 │<───│  灰度扩量 │<───│  灰度验证 │<───│  变更审批 │
│  全量监控 │    │  50% 流量 │    │  10% 流量 │    │  CAB 审批 │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 配置版本管理

Prompt 模板和知识库配置应当像代码一样纳入版本控制。建议使用 Git 仓库管理所有 Prompt 模板，每次修改通过 PR (Pull Request) 提交，经过 Code Review 后合并。这样可以追溯每次修改的历史记录，也便于在回滚时精确定位到指定版本。

```yaml
# agent_config.yaml
version: "1.2.3.5"
components:
  llm:
    model: "gpt-4-turbo"
    temperature: 0.3
    max_tokens: 2048
  prompt:
    system_prompt_version: "v2.1"
    few_shot_version: "v1.4"
  retrieval:
    top_k: 5
    rerank_model: "bge-reranker-v2"
    score_threshold: 0.65
  tools:
    enabled: ["search", "calculator", "calendar"]
    max_tool_calls: 5
  knowledge_base:
    index_version: "kb-2026-08-01-v3"
    embedding_model: "text-embedding-3-large"
```

### 发布检查清单

每次发布前应当逐项检查以下清单：监控系统是否正常采集新版本指标、告警规则是否已适配新版本、回滚脚本是否经过验证、Runbook 是否已更新、知识库索引是否已备份、模型 API 配额是否充足、依赖服务是否有 Breaking Change。

这份清单不是形式主义，而是用血泪教训换来的经验。任何一个检查项的遗漏都可能在发布后演变成线上故障。

## 8.8 成本优化方法论

Agent 系统的运营成本主要包括：LLM API 调用费用、Embedding 模型调用费用、向量数据库存储与计算费用、基础设施（服务器、带宽）费用以及人工运维成本。其中 LLM API 调用通常占总成本的 60%-80%，是成本优化的核心靶点。

### 成本优化策略对比

| 策略 | 优化效果 | 实现难度 | 质量风险 | 适用场景 |
|------|---------|---------|---------|---------|
| 模型分级路由 | 30%-50% | 中 | 低 | 混合复杂度请求场景 |
| Prompt 压缩 | 15%-25% | 中 | 中 | Token 消耗高的场景 |
| 语义缓存 | 20%-40% | 高 | 低 | 重复问题多的场景 |
| 上下文裁剪 | 10%-20% | 中 | 高 | 长会话场景 |
| Batch API | 40%-50% | 低 | 低 | 非实时离线处理场景 |
| 模型蒸馏 | 60%-80% | 极高 | 高 | 超大规模调用场景 |
| 流式早停 | 5%-10% | 低 | 中 | 长文本生成场景 |

### 模型分级路由

不同复杂度的用户请求适合用不同能力的模型处理。简单的问题用小模型就够了，只有复杂的推理任务才需要大模型。模型分级路由的核心是构建一个准确的请求复杂度分类器。

```python
class ModelRouter:
    def __init__(self):
        self.complexity_rules = {
            'simple': {
                'patterns': ['你好', '谢谢', '什么是', '解释一下'],
                'max_input_tokens': 200,
                'model': 'gpt-4o-mini',
            },
            'medium': {
                'patterns': ['比较', '分析', '总结', '如何'],
                'max_input_tokens': 800,
                'model': 'gpt-4o',
            },
            'complex': {
                'patterns': ['设计', '架构', '优化方案', '多步推理'],
                'model': 'gpt-4-turbo',
            }
        }
    
    def route(self, user_input, context_length=0):
        for level, config in self.complexity_rules.items():
            if any(p in user_input for p in config['patterns']):
                if level == 'simple' and context_length > config['max_input_tokens']:
                    continue
                return config['model']
        return 'gpt-4o'  # 默认中等模型
```

### 语义缓存

传统的精确匹配缓存命中率很低，因为用户的同一意图往往有不同的表达方式。语义缓存通过 Embedding 相似度匹配，可以将"北京的天气"和"首都今天天气怎么样"映射到同一个缓存条目。

语义缓存的实现要点：使用轻量级 Embedding 模型对用户输入进行向量化，在缓存库中查找相似度超过阈值的历史查询，如果命中则直接返回缓存的回答（可能需要轻微后处理以适配当前上下文）。阈值设置需要权衡命中率和准确性，建议初始设为 0.92，根据实际效果调优。

```python
import numpy as np

class SemanticCache:
    def __init__(self, embedder, threshold=0.92):
        self.embedder = embedder
        self.threshold = threshold
        self.cache = []  # 生产环境应使用向量数据库
    
    def get(self, query):
        query_vec = self.embedder.embed(query)
        
        best_score = 0
        best_entry = None
        for entry in self.cache:
            score = np.dot(query_vec, entry['vector'])
            if score > best_score:
                best_score = score
                best_entry = entry
        
        if best_score >= self.threshold and best_entry:
            return best_entry['response'], best_score
        return None, 0.0
    
    def set(self, query, response, metadata=None):
        vec = self.embedder.embed(query)
        self.cache.append({
            'query': query,
            'response': response,
            'vector': vec,
            'metadata': metadata or {}
        })
```

### 成本监控看板

成本优化需要建立在精确的成本归因基础上。建议构建一个实时成本看板，按以下维度展示成本数据：

按模型维度：不同模型的 Token 消耗和费用占比。如果 GPT-4-Turbo 占了 80% 的费用但只处理了 20% 的请求，说明模型路由策略需要优化。

按功能维度：不同功能模块（问答、总结、翻译、代码生成等）的成本占比。某些低频但高成本的功能可能需要重新设计。

按用户维度：识别成本消耗 TOP 用户，排查是否有异常使用模式。长尾用户（使用量低但活跃的用户）的边际成本也需要关注。

按时间维度：观察成本随时间的变化趋势，识别周期性波动和异常峰值。工作日与周末的成本差异通常反映了使用场景的分布特征。

### Token 预算管理

为每个用户或每个会话设置 Token 预算上限，是防止成本失控的硬性保障。单会话 Token 上限建议设为 30000-50000（根据业务需求调整），单用户日 Token 上限建议设为 100000-200000。当接近上限时，系统应当通知用户并优雅降级（如切换到更经济的模型或限制上下文长度），而非突然中断服务。

## 8.9 知识库持续更新机制

知识库是 RAG 系统的基础设施，其质量直接决定 Agent 回答的上限。一个静态的知识库会随着时间推移逐渐失效，因此需要建立持续更新的机制来保持知识库的时效性和准确性。

### 知识库更新策略

| 更新策略 | 触发条件 | 更新频率 | 影响范围 | 验证方式 |
|---------|---------|---------|---------|---------|
| 全量重建 | 架构变更、Embedding 模型升级 | 季度/半年 | 全部文档 | 全量回归测试 |
| 增量更新 | 新文档发布、文档修改 | 每日/每周 | 新增及关联文档 | 增量验证 + 抽检 |
| 热更新 | 紧急修正、时效性内容 | 实时 | 单条/少量文档 | 实时验证 |
| 归档清理 | 文档过期、有效性验证失败 | 每月 | 过期文档 | 不可变归档 |

### 更新流程设计

知识库的更新不是简单的"加入新文档"，而是需要经过一套完整的处理流水线。

第一步，文档采集。来源包括内部文档系统、外部数据源 API、人工编写内容等。每个文档需要记录来源、时间戳、版本号等元信息。

第二步，质量审核。新文档需要经过自动检查和人工审核。自动检查包括：格式规范性、内容完整性、与现有知识库的重复度检测。人工审核关注内容的准确性和适用性。

第三步，文档处理。包括分块（Chunking）、清洗（去除噪声字符、标准化格式）、元信息标注（分类标签、有效期、优先级等）。

第四步，Embedding 生成。使用与当前知识库一致的 Embedding 模型生成向量。需要注意的是，如果更换 Embedding 模型，必须对全部文档重新生成 Embedding，否则相似度计算会不一致。

第五步，索引更新。将新文档的 Embedding 加入向量索引。建议采用追加模式而非重建模式，避免更新期间的服务中断。

第六步，验证与发布。使用标准测试集验证更新后的检索效果，确认无退化后切换到新版本索引。

```python
class KnowledgeBaseUpdater:
    def __init__(self, embedder, vector_store, test_suite):
        self.embedder = embedder
        self.vector_store = vector_store
        self.test_suite = test_suite
    
    async def incremental_update(self, new_documents):
        # 文档处理
        chunks = []
        for doc in new_documents:
            processed = self.preprocess(doc)
            chunks.extend(self.chunk(processed))
        
        # 生成 Embedding
        embeddings = await self.embedder.embed_batch([c.text for c in chunks])
        
        # 写入临时索引
        temp_index = self.vector_store.clone()
        temp_index.add(chunks, embeddings)
        
        # 验证
        results = self.test_suite.run(temp_index)
        if results.hit_rate < self.test_suite.baseline_hit_rate * 0.95:
            raise QualityAssuranceError(
                f"Hit rate degraded: {results.hit_rate} vs baseline {self.test_suite.baseline_hit_rate}"
            )
        
        # 原子切换
        self.vector_store.swap(temp_index)
        return {"added_chunks": len(chunks), "validation": results}
```

### 知识库版本管理

每次更新都应当生成一个新版本号，并保留旧版本索引至少 30 天。这样在发现新版本存在问题（如检索质量退化）时可以快速回滚。版本号建议使用日期 + 序号格式，如"kb-2026-08-03-v1"。

版本管理还应当记录每次变更的 Diff：新增了哪些文档、删除了哪些文档、修改了哪些文档。这些信息对于排查"为什么 Agent 突然对某类问题的回答变差了"至关重要。

### 时效性管理

知识库中的内容并非都是永久有效的。产品手册会更新、政策会变化、价格会调整。每个文档应当标注有效期，过期文档自动进入审核队列，由人工确认是否更新或归档。

```python
class DocumentExpiryManager:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def check_expired(self, current_date):
        expired_docs = self.vector_store.query(
            filter={"expiry_date": {"$lt": current_date}}
        )
        return expired_docs
    
    def archive_expired(self, doc_ids):
        for doc_id in doc_ids:
            self.vector_store.update(
                id=doc_id,
                metadata={"status": "archived", "archived_at": datetime.now()}
            )
            # 从检索索引中移除，但保留原始文档
            self.vector_store.remove_from_index(doc_id)
```

### 知识库健康度评估

定期对知识库进行健康度评估，指标包括：文档覆盖率（用户高频问题在知识库中有对应文档的比例）、文档新鲜度（文档平均年龄和更新频率）、检索精确率（Top-K 检索结果中相关文档的占比）、索引效率（检索延迟与召回率的平衡）。

建议每月生成一份知识库健康报告，识别需要补充的知识领域、需要更新的过期文档、检索效果不佳的问题类型，为下一阶段的知识库建设提供方向。

## 8.10 容量规划与扩容方案

容量规划是确保系统在用户增长时仍能保持稳定服务的前瞻性工作。Agent 系统的容量规划比传统服务复杂，因为它不仅涉及计算资源的扩容，还涉及 LLM API 配额的管理、知识库检索性能的保障等多维度考量。

### 容量规划核心公式

| 资源类型 | 容量计算公式 | 关键变量说明 |
|---------|-------------|-------------|
| 应用服务器 | N = ceil(QPS * RT / (CPU_PER * 0.7)) | QPS: 峰值请求量, RT: 平均处理时长, CPU_PER: 单请求 CPU 开销 |
| LLM API 配额 | Q = peak_users * avg_calls_per_session * 1.5 | peak_users: 峰值并发用户数, 1.5: 安全系数 |
| 向量数据库 | S = doc_count * dim * 4 * 1.5 / 1024^3 (GB) | doc_count: 文档块数, dim: 向量维度, 1.5: 索引开销系数 |
| 内存 (缓存) | M = hot_data_size * 2 / 1024 (GB) | hot_data_size: 热数据大小, 2: 冗余系数 |
| 带宽 | B = peak_users * avg_response_size * 8 / 1024 (Mbps) | avg_response_size: 平均响应体大小 |
| 知识库存储 | D = raw_docs_size * 3 / 1024^3 (GB) | 3: 含索引、备份、临时文件的系数 |

### 流量预测模型

容量规划的基础是准确的流量预测。建议使用时间序列预测模型（如 Prophet 或 ARIMA）对历史流量数据进行建模，预测未来 1-3 个月的流量趋势。

预测时需要考虑以下因素：自然增长趋势（用户量增长带来的流量增长）、季节性波动（工作日 vs 周末、白天 vs 夜间、节假日效应）、业务事件驱动（产品发布、营销活动等可能带来的流量峰值）。

```python
import numpy as np
from scipy import stats

class CapacityPredictor:
    def __init__(self, historical_qps, growth_rate):
        self.historical_qps = np.array(historical_qps)
        self.growth_rate = growth_rate  # 月增长率
    
    def predict_peak_qps(self, months_ahead):
        """预测未来 N 个月的峰值 QPS"""
        current_peak = np.max(self.historical_qps[-30:])  # 最近30天峰值
        
        # 考虑增长趋势
        predicted_peak = current_peak * ((1 + self.growth_rate) ** months_ahead)
        
        # 考虑季节性波动（基于历史数据的变异系数）
        seasonal_factor = np.std(self.historical_qps) / np.mean(self.historical_qps)
        peak_with_buffer = predicted_peak * (1 + seasonal_factor * 0.5)
        
        return int(peak_with_buffer)
    
    def recommend_capacity(self, months_ahead):
        """推荐资源配置"""
        target_qps = self.predict_peak_qps(months_ahead)
        
        return {
            'target_qps': target_qps,
            'app_servers': self._calc_servers(target_qps),
            'llm_quota_rpm': int(target_qps * 60 * 2.5),  # 平均2.5次LLM调用/请求
            'llm_quota_tpm': int(target_qps * 60 * 2000),  # 平均2000 token/调用
            'cache_memory_gb': target_qps * 0.5,  # 经验值
            'vector_db_shards': max(1, target_qps // 500)
        }
    
    def _calc_servers(self, qps):
        avg_rt = 3.0  # 平均处理时长3秒
        cpu_per_request = 0.15  # 单请求CPU开销
        utilization = 0.7  # 目标CPU利用率70%
        return int(np.ceil(qps * avg_rt * cpu_per_request / utilization))
```

### 扩容策略

扩容策略分为水平扩容和垂直扩容两个方向。Agent 系统由于是无状态服务（状态存储在外部缓存和数据库中），水平扩容是首选方案。

水平扩容的核心是无状态化设计。Agent 服务不应当持有会话状态，所有状态（对话历史、用户偏好、会话配置等）应当存储在 Redis 或数据库中。这样可以在流量高峰时快速增加实例数，而不需要等待状态同步。

自动扩缩容策略应当基于多个指标而非仅 CPU 使用率。Agent 系统的 CPU 使用率可能不高（因为大部分时间在等待 LLM 响应），但响应延迟可能已经恶化。建议以"并发请求数"和"P95 延迟"作为扩容触发条件。

```yaml
# Kubernetes HPA 配置示例
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 3
  maxReplicas: 30
  metrics:
  - type: Pods
    pods:
      metric:
        name: concurrent_requests
      target:
        type: AverageValue
        averageValue: "20"
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 120
```

### LLM API 配额管理

LLM API 的配额不像服务器资源那样可以随时扩容，它受限于供应商的 Rate Limit 和账户等级。容量规划中需要特别关注 LLM API 的配额管理。

建议建立 LLM API 配额监控看板，实时显示：当前 RPM (Requests Per Minute) 和 TPM (Tokens Per Minute) 使用量、配额上限、剩余配额、预计耗尽时间。当配额使用率超过 80% 时触发预警，超过 95% 时触发限流。

多供应商策略是配额管理的有效补充。将流量在多个 LLM 供应商之间分配，不仅可以降低单一供应商故障的风险，还能在配额不足时自动切换到备用供应商。

### 灾备与多活

对于高可用要求的 Agent 系统，建议采用同城双活架构。两个机房各部署一套完整的服务栈（应用服务器、向量数据库、缓存等），通过 DNS 或负载均衡进行流量分配。知识库索引在两个机房之间保持同步，可以使用向量数据库的复制功能或定期快照恢复。

跨地域灾备建议采用"主-备"模式而非"双活"模式，因为知识库的跨地域同步延迟可能影响检索质量。主地域承载全部流量，备地域保持热备状态，在主地域整体故障时通过 DNS 切换接管流量。

RTO (Recovery Time Objective, 恢复时间目标) 建议设为 15 分钟，RPO (Recovery Point Objective, 恢复点目标) 建议设为 5 分钟。这意味着从故障发生到服务恢复不超过 15 分钟，数据丢失不超过 5 分钟。

### 容量规划评审周期

容量规划不是一次性的工作，而是一个持续的过程。建议每月进行一次容量评审，内容包括：当前资源利用率回顾、流量预测更新、扩容计划制定、成本预算调整。每季度进行一次深度评审，重新评估架构合理性、供应商策略和灾备方案。

## 本章知识点总结

| 序号 | 知识点 | 核心内容 | 关键指标/方法 |
|------|--------|---------|-------------|
| 1 | 四级监控体系 | 基础设施层、服务层、Agent 层、业务层全覆盖 | TTFT < 1s, 检索命中率 > 60% |
| 2 | 日志分层架构 | Trace/Debug/INFO/Error 四级，Hot/Warm/Cold 三级存储 | 正常请求 1% 采样，错误请求 100% 记录 |
| 3 | 故障分级 SOP | P0-P3 四级，含应急预案和复盘规范 | P0 5min 响应，1h 恢复 |
| 4 | 质量优化循环 | PDCA 循环 + LLM as Judge + 退化检测 | 准确率 > 92%，退化 > 5% 告警 |
| 5 | 反馈收集体系 | 显式评分 + 隐式信号 + 定期问卷组合 | 隐式信号覆盖率 100% |
| 6 | A/B 测试方法 | 按用户分桶、MDE 计算、护栏指标保障 | 显著性 p < 0.05，统计功效 0.8 |
| 7 | 版本管理策略 | 四段式版本号，配置即代码，蓝绿部署 | 配置变更可 5min 回滚 |
| 8 | 成本优化方法 | 模型路由 + 语义缓存 + Token 预算管理 | 缓存命中可降低 20%-40% 成本 |
| 9 | 知识库更新机制 | 增量更新为主，全量重建为辅，版本化管理 | 更新后检索命中率不低于基线 95% |
| 10 | 容量规划公式 | 基于 QPS 和增长率预测，多维度容量计算 | RTO 15min，RPO 5min |

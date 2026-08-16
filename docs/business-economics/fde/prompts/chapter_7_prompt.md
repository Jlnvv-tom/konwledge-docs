# 第7章 写作 Prompt — 核心技能要求拆解（上）：编程语言与AI技术栈

## 章节定位
- 系列：《FDE前沿部署工程师——岗位全景与职业发展指南》
- 篇：第三篇 能力篇（如何胜任）
- 章：第7章 核心技能要求拆解（上）：编程语言与AI技术栈（工程能力与软技能见第8章）
- 目标字数：10000-12000字（中文）

## 本章小节结构
7.1 编程语言要求：JD出现率与重要程度排序
7.2 AI技术栈要求：必备/推荐/加分三梯队

## 内容要点（基于市场报告原文，需展开成文）
- 7.1：用表格展示六种语言/技术（Python 95%+必备、SQL 80%必备、Go 45%重要、TypeScript/JavaScript 40%重要、Java 35%加分、Rust 10%新兴），解释出现率与岗位核心工作的对应关系（Python是AI生态主语言、SQL是数据链路必需），说明为什么Go/TS重要但非必备。
- 7.2：分三梯队展开——第一梯队必须掌握（RAG检索增强生成、Prompt Engineering提示词工程、Agent开发、向量数据库、LLM API调用，逐个解释原理并给出核心关键代码片段如RAG检索链路的简化实现或Agent工具调用的函数定义，每段不超过15行）；第二梯队强烈推荐（模型微调LoRA/QLoRA、推理优化vLLM/TensorRT-LLM、多模态应用、AI安全、评估体系LLM-as-Judge）；第三梯队加分项（MLOps、私有化部署、低代码平台、数据工程），解释梯队划分的设计逻辑（直接决定能否交付 vs 提升交付质量 vs 差异化竞争）。

注：工程能力（基础设施与开发实践）与软技能（五维能力模型）已拆分至第8章，本章不涉及。

## 写作规范（必须遵守）
1. 字数控制在10000-12000字，段落短小（每段不超过4-5行）。
2. 全文禁止使用emoji或任何图标符号，禁止出现 ⭐🔥⚡💡 等装饰性符号。
3. 段落之间不使用 "---" 分隔线，用自然语言过渡。
4. 专有缩写名词首次出现必须给出全称英文与中文释义，例如：FDE（Forward Deployment Engineer，前沿部署工程师）、RAG（Retrieval-Augmented Generation，检索增强生成）、LLM（Large Language Model，大语言模型）、LoRA（Low-Rank Adaptation，低秩适配）、QLoRA（Quantized Low-Rank Adaptation，量化低秩适配）、vLLM（Virtual Large Language Model，大模型推理加速框架）、TensorRT-LLM（NVIDIA TensorRT for Large Language Models）、MLOps（Machine Learning Operations，机器学习运维）、CI/CD（Continuous Integration / Continuous Delivery，持续集成/持续交付）、K8s（Kubernetes，容器编排平台）、API（Application Programming Interface，应用程序编程接口）、RESTful（Representational State Transfer，表述性状态转移架构风格）、GraphQL（Graph Query Language，图查询语言）、ELK（Elasticsearch、Logstash、Kibana日志分析栈）等。
5. 不写完整代码示例，只展示核心关键代码片段（每段不超过15行）并解释其原理。
6. 多用表格与文字版图示（技术栈分层图、RAG链路图），并对图表原理做解释（数据流走向、各组件职责）。
7. 内容基于2026年8月市场数据，保持专业、客观的分析风格。
8. 章节结尾附"本章小结"表格。
9. 结尾用一段话预告第8章（工程能力与软技能）内容（系列连载感，不使用IP人设与营销话术）。

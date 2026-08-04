# 第四章：数据工程与知识处理

在企业级 AI Agent 的工程实践中，数据工程与知识处理是决定系统上限的核心环节。再强大的模型架构，如果输入的数据质量低劣、知识组织混乱，最终输出的效果也会大打折扣。本章将从客户现场的实际数据问题出发，逐步深入到文档分块、向量数据库选型、混合检索、重排序、多模态文档处理、私有知识库构建、知识图谱增强检索、多语言场景以及数据安全等十个关键主题，构建一套完整的数据工程与知识处理知识体系。

## 4.1 客户现场数据质量问题全景

在企业实际部署 AI Agent 的过程中，客户现场的数据质量往往是项目落地的第一道门槛。与实验室环境中精心整理的学术数据集不同，真实企业的数据常年积累、来源繁杂、格式混乱，存在大量质量隐患。

### 数据质量问题的根源

企业数据质量问题通常源于三个方面。第一，历史系统迁移导致的数据丢失与格式漂移，例如早期 ERP 系统导出的数据经过多次转换后字段对齐错乱。第二，人工录入的随意性与缺乏校验规则，导致同一实体存在多种写法，比如客户名称 "中石化" 与 "中国石油化工集团有限公司" 并存。第三，跨部门数据孤岛导致口径不一致，销售部门与财务部门对 "活跃客户" 的定义可能完全不同。

### 数据质量问题分类体系

下表归纳了客户现场常见的数据质量问题类型、典型表现及其对 AI Agent 的影响：

| 问题类型 | 典型表现 | 对 Agent 的影响 | 严重等级 |
|---------|---------|----------------|---------|
| 缺失值 | 字段为空、null、N/A、空字符串 | 检索结果不完整，回答缺少关键信息 | 高 |
| 重复数据 | 同一文档多次入库、相似度95%以上的冗余文档 | 检索结果冗余，浪费上下文窗口 | 中 |
| 格式不一致 | 日期格式混用(YYYY-MM-DD与DD/MM/YYYY)、编码混用(UTF-8与GBK) | 解析失败、乱码、分词错误 | 高 |
| 实体歧义 | 同一实体多种称呼、同一名称指代不同实体 | 检索精度下降，回答出现张冠李戴 | 高 |
| 结构混乱 | 表格嵌套不规范、PDF多栏排版错位、扫描件倾斜 | 文本提取质量差，分块边界错误 | 高 |
| 时效性失效 | 过期的产品价格、已作废的流程制度 | Agent给出过时甚至错误的答案 | 中 |
| 权限混杂 | 公开数据与机密数据混存在同一知识库 | 数据泄露风险，合规违规 | 极高 |
| 噪声数据 | 水印文字、页眉页脚、OCR识别错误字符 | 检索噪声增大，回答可信度降低 | 中 |

### 数据质量评估框架

在项目启动阶段，建议对客户数据进行系统性的质量评估。评估可以从六个维度展开，形成一个可量化的数据质量评分卡：

完整性（Completeness）：检查必填字段的非空比例。例如知识库中每篇文档是否都有标题、摘要、创建时间等元数据。

准确性（Accuracy）：通过抽样校验，比对数据与权威源是否一致。例如产品规格参数是否与最新产品手册一致。

一致性（Consistency）：跨数据源比对同一实体的描述是否统一。例如客户名称在不同系统中的记录是否对齐。

时效性（Timeliness）：检查数据的更新频率与业务需求是否匹配。例如价格信息是否在调价后及时更新。

唯一性（Uniqueness）：检测重复记录的比例。通过精确匹配与模糊匹配相结合的方式识别冗余数据。

合规性（Compliance）：验证数据存储与处理是否符合行业法规要求。例如个人信息是否脱敏、敏感数据是否加密。

### 数据清洗流水线设计

针对上述问题，工程上需要设计一条标准化的数据清洗流水线。以下是一个典型的清洗流程伪代码：

```python
def data_cleaning_pipeline(raw_documents):
    cleaned = []
    for doc in raw_documents:
        # 1. 编码统一：转换为UTF-8
        doc = normalize_encoding(doc)
        # 2. 去除噪声：页眉页脚、水印、多余空白
        doc = remove_noise(doc)
        # 3. 实体标准化：统一称谓
        doc = normalize_entities(doc, entity_dict)
        # 4. 去重：与已有库比对
        if is_duplicate(doc, cleaned, threshold=0.95):
            continue
        # 5. 元数据补全
        doc = enrich_metadata(doc)
        # 6. 时效性标注
        doc = check_freshness(doc)
        cleaned.append(doc)
    return cleaned
```

这条流水线的每个环节都需要根据具体业务场景调整参数。例如去重阈值在不同领域差异很大：法律文书相似度90%可能仍然是不同文件，而产品说明书相似度80%就可能已经是重复文档。

### 延展：数据质量治理的长效机制

数据清洗不是一次性工作。企业需要建立长效的数据治理机制，包括定期的质量巡检、自动化的质量监控告警、以及数据录入前的前置校验规则。在 AI Agent 项目中，建议将数据质量指标纳入系统监控面板，持续跟踪知识库中文档的完整性评分、时效性评分等指标，一旦质量下降到阈值以下，及时触发告警和人工介入。

## 4.2 文档分块策略深度解析

文档分块（Document Chunking）是 RAG (Retrieval-Augmented Generation, 检索增强生成) 系统中承上启下的关键环节。分块策略直接影响检索精度和生成质量。块太大，检索精度下降且浪费上下文窗口；块太小，语义信息不完整，检索到的内容缺乏上下文。

### 分块策略分类

常见的文档分块策略可以分为以下几类：

| 策略名称 | 原理 | 优点 | 缺点 | 适用场景 |
|---------|------|------|------|---------|
| 固定长度分块 | 按固定token数切割 | 实现简单、速度块 | 可能切断语义 | 快速原型验证 |
| 递归字符分块 | 按段落、句子递归切割 | 保持段落完整性 | 长度不均匀 | 通用文本文档 |
| 语义分块 | 用嵌入模型检测语义边界 | 语义完整性最好 | 计算成本高 | 高质量要求场景 |
| 文档结构分块 | 按标题层级切割 | 保持文档结构 | 依赖文档格式 | Markdown、HTML |
| Sliding Window | 滑动窗口带重叠 | 保留上下文衔接 | 冗余数据增多 | 长文档连续叙述 |
| 上下文增强分块 | 分块时附加前后文摘要 | 检索时上下文更完整 | 预处理成本高 | 问答精度优先 |

### 固定长度分块

固定长度分块是最基础的策略，按预设的 token 数量将文档切割成等大小的块。关键参数有两个：块大小（chunk_size）和重叠大小（overlap）。块大小通常设置为 256-1024 个 token，重叠设置为块大小的 10%-20%。

```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=512,
    chunk_overlap=50,
    length_function=len
)
chunks = splitter.split_text(long_document)
```

固定长度分块的最大问题在于它完全忽略了语义边界。一个完整的论证过程可能在中间被截断，导致检索到的块只有论点没有论据，或者只有结论没有前提。

### 递归字符分块

递归字符分块是对固定长度分块的改进。它按照分隔符的优先级递归切割：先尝试按段落分割，如果段落仍然太长，再按句子分割，以此类推。

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", ".", " ", ""]
)
chunks = splitter.split_text(document)
```

这种策略在大多数场景下表现良好，是生产环境中最常用的分块方式之一。它兼顾了语义完整性和长度均匀性，能够适应不同类型的文本文档。

### 语义分块

语义分块利用嵌入模型计算相邻句子之间的语义相似度，在相似度急剧下降的位置进行切割。这种方法能够最大程度地保证每个块的语义完整性。

```python
from semantic_chunker import SemanticChunker
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer('BAAI/bge-large-zh')
chunker = SemanticChunker(
    encoder=encoder,
    breakpoint_threshold=0.5,  # 相似度下降阈值
    buffer_size=3  # 滑动窗口大小
)
chunks = chunker.split_text(document)
```

语义分块的计算成本较高，需要为每个句子计算嵌入向量。在文档量大的场景下，需要权衡精度与效率。建议在对检索质量要求极高的场景（如法律、医疗知识库）中使用。

### 文档结构感知分块

对于结构化文档（Markdown、HTML、LaTeX），可以基于文档的结构元素进行分块。例如按 Markdown 的标题层级切割，确保每个块包含一个完整的章节。

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
chunks = splitter.split_text(markdown_doc)
# 每个chunk自动携带所属标题层级作为元数据
```

这种方法的优势在于分块结果天然携带文档结构信息，检索时可以利用标题层级进行过滤和排序。

### 分块参数调优

分块参数的选择没有放之四海而皆准的最优值，需要根据具体场景调优。以下是经验性的参数选择指南：

| 文档类型 | 推荐块大小(token) | 推荐重叠 | 推荐策略 |
|---------|------------------|---------|---------|
| FAQ问答对 | 128-256 | 0 | 按问答对天然分块 |
| 技术文档 | 512-768 | 50-100 | 递归字符分块 |
| 法律合同 | 256-512 | 50 | 文档结构分块 |
| 长篇报告 | 768-1024 | 100-150 | Sliding Window |
| 新闻文章 | 256-512 | 30-50 | 递归字符分块 |
| API文档 | 256 | 0 | 按接口分块 |
| 学术论文 | 512-768 | 50-100 | 语义分块 |

### 延展：分块评估方法论

如何评估分块效果？可以从三个维度构建评估体系。检索维度：使用标注好的问答数据集，统计不同分块策略下检索结果的召回率和精确率。生成维度：对检索到的上下文，让评估模型判断其是否包含回答问题所需的完整信息。效率维度：统计分块数量、嵌入计算时间和存储成本。三个维度的综合得分可以帮助选择最优分块策略。

## 4.3 向量数据库选型决策

向量数据库是 RAG 系统的核心存储与检索引擎。选型的优劣直接决定了系统的检索性能、扩展能力和运维成本。当前市场上的向量数据库选择众多，从开源到商业、从专用到通用，需要根据业务需求进行系统性的评估。

### 向量数据库核心能力维度

选型时需要评估以下核心能力：

索引算法：是否支持 HNSW (Hierarchical Navigable Small World, 层级可导航小世界图)、IVF (Inverted File Index, 倒排文件索引)、Flat 等多种索引类型，以适应不同规模和精度需求。

过滤能力：是否支持元数据过滤（pre-filtering 和 post-filtering），过滤性能如何。在实际业务中，元数据过滤几乎是刚需。

混合检索：是否原生支持向量检索与关键词检索的混合模式，还是需要外部组件实现。

水平扩展：是否支持分布式部署，能否通过增加节点线性扩展存储和计算能力。

持久化与恢复：数据持久化机制是否可靠，故障恢复时间如何，是否支持增量持久化。

生态集成：与主流框架（LangChain、LlamaIndex、Haystack等）的集成程度，SDK语言支持范围。

### 主流向量数据库对比

| 数据库 | 类型 | 索引算法 | 过滤支持 | 分布式 | 适用规模 | 部署方式 |
|-------|------|---------|---------|-------|---------|---------|
| Milvus | 专用向量库 | HNSW/IVF/DiskANN | 丰富 | 原生支持 | 亿级以上 | K8s/Docker |
| Qdrant | 专用向量库 | HNSW | 标量过滤 | 支持复制 | 千万级 | Docker/二进制 |
| Weaviate | 专用向量库 | HNSW | 内置模块 | 支持 | 千万级 | Docker/K8s |
| Chroma | 轻量级库 | HNSW | 元数据过滤 | 不支持 | 百万级 | 嵌入式 |
| pgvector | PostgreSQL扩展 | HNSW/IVFFlat | SQL过滤 | 依赖PG | 千万级 | PG扩展 |
| Pinecone | 云服务 | 专有 | 丰富 | 原生 | 亿级 | SaaS |
| Redis Stack | 内存数据库 | HNSW/Flat | 支持标签 | Redis集群 | 百万级 | Redis部署 |
| Elasticsearch | 全文搜索引擎 | HNSW | 强大 | 原生 | 亿级 | 集群部署 |

### 选型决策树

以下文字描述的决策树可以辅助选型：

```
开始
 |
 +-- 数据规模是否超过1亿向量？
 |    +-- 是 --> 是否需要私有化部署？
 |    |         +-- 是 --> Milvus (首选) / Elasticsearch
 |    |         +-- 否 --> Pinecone
 |    +-- 否 --> 是否已有PostgreSQL基础设施？
 |              +-- 是 --> pgvector (降低运维成本)
 |              +-- 否 --> 是否需要混合检索(向量+关键词)？
 |                       +-- 是 --> Elasticsearch / Weaviate
 |                       +-- 否 --> 是否需要超低延迟？
 |                                +-- 是 --> Redis Stack
 |                                +-- 否 --> Qdrant / Chroma
```

### Milvus 深度选型分析

Milvus 作为目前最主流的开源向量数据库，在大型企业项目中使用广泛。它的架构分为四个层次：接入层（Access Layer）、协调服务（Coordinator Service）、工作节点（Worker Node）和存储（Storage）。这种分层架构使得各层可以独立扩展。

Milvus 的索引选择直接影响检索性能。HNSW 索引提供了极高的查询速度，但内存消耗大；IVF 索引通过聚类实现近似检索，内存效率更高但精度略有损失；DiskANN 索引将索引存储在磁盘上，适合超大规模数据集，在内存有限的情况下是最佳选择。

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# 连接Milvus
connections.connect(host="localhost", port="19530")

# 定义Collection Schema
fields = [
    FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=1024),
    FieldSchema("source", DataType.VARCHAR, max_length=256),
    FieldSchema("page", DataType.INT32)
]
schema = CollectionSchema(fields, "知识库文档向量")
collection = Collection("knowledge_base", schema)

# 创建HNSW索引
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "HNSW",
        "metric_type": "IP",
        "params": {"M": 16, "efConstruction": 256}
    }
)
```

### pgvector 的工程价值

对于中小规模项目或者已有 PostgreSQL 基础设施的企业，pgvector 是一个非常务实的选择。它作为 PostgreSQL 的扩展插件运行，不需要额外的数据库进程，运维团队的学习成本极低。

```sql
-- 创建pgvector扩展
CREATE EXTENSION vector;

-- 创建带向量列的表
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1024),
    source VARCHAR(256),
    created_at TIMESTAMP
);

-- 创建HNSW索引
CREATE INDEX ON documents USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- 向量检索（带元数据过滤）
SELECT content, source, embedding <=> :query_vector AS distance
FROM documents
WHERE source = 'product_manual'
  AND created_at > '2024-01-01'
ORDER BY embedding <=> :query_vector
LIMIT 10;
```

pgvector 的局限在于它本质上是一个单机数据库扩展，当数据规模超过千万级时，检索延迟会明显上升。此时需要考虑 PostgreSQL 的分区表、读写分离等手段来缓解。

### 延展：成本视角的选型考量

除了技术指标，选型还需要考虑总拥有成本（TCO, Total Cost of Ownership）。开源方案虽然软件许可费用为零，但需要投入运维人力、服务器资源和时间成本。SaaS 方案按使用量计费，在项目初期成本较低，但随着数据规模增长，费用可能急剧上升。一个经验性的判断标准是：如果月度 SaaS 费用超过自建方案的运维人力成本（通常在数据量超过 5000 万向量时），就应该考虑切换到自建方案。

## 4.4 Hybrid Search 与 Reranking 实现

在实际项目中，单一的向量检索往往无法满足精度要求。向量检索擅长语义匹配，但对于精确关键词、专有名词、编号等场景表现不佳。关键词检索（BM25等）恰好互补，擅长精确匹配但缺乏语义理解能力。Hybrid Search 将两者融合，取长补短，是生产环境的标配方案。

### Hybrid Search 架构

以下是 Hybrid Search 的架构示意：

```
用户查询
    |
    +--------------------+
    |                    |
    v                    v
+----------+      +-----------+
| 向量检索  |      | 关键词检索 |
| (Dense)  |      | (Sparse)  |
+----------+      +-----------+
    |                    |
    |  Top-K1 结果        |  Top-K2 结果
    |                    |
    +--------+-----------+
             |
             v
      +--------------+
      | 融合排序算法   |
      | (RRF/加权)    |
      +--------------+
             |
             v
      +--------------+
      | 去重后的      |
      | Top-N 结果    |
      +--------------+
             |
             v
      +--------------+
      | Reranking    |
      | 精排模型      |
      +--------------+
             |
             v
      +--------------+
      | 最终 Top-K    |
      | 结果          |
      +--------------+
```

### 检索结果融合算法

两种最常用的融合算法是 RRF (Reciprocal Rank Fusion, 倒数排名融合) 和加权分数融合。

RRF 的核心思想是根据每篇文档在不同检索结果列表中的排名来计算融合分数，而不依赖原始相似度分数。这使得它对不同检索器的分数分布差异具有天然的鲁棒性。

RRF 公式为：

```
score(d) = sum over each retriever: 1 / (k + rank_i(d))
```

其中 k 是平滑常数（通常取60），rank_i(d) 是文档 d 在第 i 个检索器结果中的排名。

```python
def reciprocal_rank_fusion(
    result_lists, k=60, top_n=20
):
    """
    RRF融合算法
    result_lists: 各检索器的结果列表，每个元素为(doc_id, score)
    """
    rrf_scores = {}
    for result_list in result_lists:
        for rank, (doc_id, _) in enumerate(result_list, 1):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0
            rrf_scores[doc_id] += 1.0 / (k + rank)
    
    # 按融合分数排序
    sorted_docs = sorted(
        rrf_scores.items(), key=lambda x: x[1], reverse=True
    )
    return sorted_docs[:top_n]
```

加权分数融合则直接对原始相似度分数进行归一化后加权求和。这种方法需要确保不同检索器的分数在相同尺度上，通常需要对分数进行 min-max 归一化或 z-score 标准化。

```python
def weighted_fusion(
    result_lists, weights, top_n=20
):
    """
    加权分数融合
    weights: 各检索器的权重，如[0.7, 0.3]
    """
    # 归一化分数
    all_scores = {}
    for i, result_list in enumerate(result_lists):
        scores = [s for _, s in result_list]
        min_s, max_s = min(scores), max(scores)
        for doc_id, score in result_list:
            normalized = (score - min_s) / (max_s - min_s + 1e-8)
            if doc_id not in all_scores:
                all_scores[doc_id] = 0
            all_scores[doc_id] += weights[i] * normalized
    
    sorted_docs = sorted(
        all_scores.items(), key=lambda x: x[1], reverse=True
    )
    return sorted_docs[:top_n]
```

### 权重调节策略

Hybrid Search 中向量检索与关键词检索的权重设置是影响效果的关键因素。权重并非一成不变，需要根据查询类型动态调节。

对于事实型查询（"产品A的价格是多少"），关键词检索权重应更高，因为精确匹配产品名称和数字是关键。对于语义型查询（"如何优化系统性能"），向量检索权重应更高，因为需要理解查询意图。

一种工程化的做法是训练一个轻量级的查询分类器，先判断查询类型，再动态选择权重。也可以采用更简单的策略：同时用两组权重检索，取结果数量的并集再交给 Reranking 模型精排。

### 延展：检索阶段的两阶段架构

Hybrid Search 与 Reranking 构成了一个典型的两阶段检索架构：第一阶段是召回阶段，目标是快速从海量文档中筛选出相关候选集，追求高召回率；第二阶段是精排阶段，使用更复杂的模型对候选集进行精细化排序，追求高精度。

这种架构的优势在于将效率与精度解耦。召回阶段可以使用高效的近似检索算法快速处理百万级文档，精排阶段则可以使用计算密集的交叉编码器对数十篇候选文档进行深度语义匹配。两阶段的成本分配通常遵循"召回广、精排深"的原则。

## 4.5 Reranking 模型选择与部署

Reranking 是两阶段检索架构中精排阶段的核心组件。它接收召回阶段的候选文档列表，通过更精细的模型对查询与文档的相关性进行重新评分和排序，显著提升最终返回给 LLM (Large Language Model, 大语言模型) 的上下文质量。

### Reranking 的工作原理

Reranking 模型与向量检索模型的工作方式有本质区别。向量检索使用 Bi-Encoder 架构，查询和文档分别独立编码为向量，然后计算向量相似度。这种方式速度快，但无法捕捉查询与文档之间的细粒度交互信息。

Reranking 模型使用 Cross-Encoder 架构，将查询和文档拼接在一起输入到模型中，模型能够充分利用两者之间的注意力交互，输出更精确的相关性分数。

```
Bi-Encoder (向量检索):
  Query  -> Encoder -> Query Vector  \
                                       -> Cosine Similarity -> Score
  Document -> Encoder -> Doc Vector  /

Cross-Encoder (Reranking):
  [Query + Document] -> Encoder -> Score
```

Cross-Encoder 的计算成本远高于 Bi-Encoder，这也是它只用于精排阶段的原因。通常召回阶段从百万级文档中筛选出50-100篇候选，Reranking 模型只对这50-100篇进行打分。

### 主流 Reranking 模型对比

| 模型名称 | 基座架构 | 支持语言 | 模型大小 | 推理速度 | 效果评级 |
|---------|---------|---------|---------|---------|---------|
| bge-reranker-large | XLM-RoBERTa | 多语言 | 560M | 中 | 优秀 |
| bge-reranker-v2-m3 | BGE-M3 | 多语言 | 568M | 中 | 优秀 |
| Cohere Rerank 3 | 专有模型 | 多语言 | 未公开 | 快 | 优秀 |
| Jina Reranker v2 | JinaBERT | 多语言 | 278M | 快 | 良好 |
| ms-marco-MiniLM-L-12 | MiniLM | 英语 | 33M | 很快 | 良好(英语) |
| ms-marco-electra-base | ELECTRA | 英语 | 110M | 快 | 良好(英语) |
| BAAI/bge-reranker-base | XLM-RoBERTa | 多语言 | 278M | 快 | 良好 |

### 模型部署实践

以下使用 Hugging Face 的 sentence-transformers 库加载 BGE Reranker 进行推理：

```python
from sentence_transformers import CrossEncoder
import numpy as np

# 加载模型
reranker = CrossEncoder(
    'BAAI/bge-reranker-large',
    max_length=512
)

def rerank_documents(query, documents, top_k=5):
    """对检索结果进行重排序"""
    # 构造(query, doc)对
    pairs = [[query, doc] for doc in documents]
    
    # 计算相关性分数
    scores = reranker.predict(pairs)
    
    # 按分数排序
    ranked_indices = np.argsort(scores)[::-1]
    
    return [(documents[i], scores[i]) for i in ranked_indices[:top_k]]

# 使用示例
query = "如何配置数据库连接池"
docs = [
    "数据库连接池配置指南：建议设置最大连接数为...",
    "数据库备份策略说明...",
    "连接池参数调优：maxPoolSize和minPoolSize..."
]
results = rerank_documents(query, docs, top_k=3)
```

### 部署优化策略

在生产环境中，Reranking 模型的推理延迟往往是系统的性能瓶颈。以下是几种常用的优化策略：

模型量化：将模型从 FP32 量化为 FP16 或 INT8，可以将推理速度提升2-4倍，精度损失通常在可接受范围内。对于 BGE Reranker Large，FP16 量化后推理速度提升约2倍，效果几乎无损。

批量推理：将多个(query, doc)对组成一个batch同时推理，充分利用GPU的并行计算能力。需要注意控制batch size以避免显存溢出。

ONNX Runtime 加速：将 PyTorch 模型转换为 ONNX 格式，使用 ONNX Runtime 推理，通常可以获得30%-50%的速度提升。

缓存策略：对高频查询的 Reranking 结果进行缓存。如果查询的语义相近（向量相似度超过阈值），可以直接复用缓存结果。

### Reranking 流程图

```
输入: 查询Q + 候选文档集[D1, D2, ..., D50]
                |
                v
    +-------------------+
    | 构造(Q, Di)文本对  |
    +-------------------+
                |
                v
    +-------------------+
    | Cross-Encoder编码  |
    | (自注意力交互)      |
    +-------------------+
                |
                v
    +-------------------+
    | 输出相关性分数      |
    | S1, S2, ..., S50  |
    +-------------------+
                |
                v
    +-------------------+
    | 按分数降序排列      |
    +-------------------+
                |
                v
    输出: 排序后的Top-K文档
    [(D5, 0.95), (D12, 0.89), ...]
```

### 延展：Reranking 模型微调

通用 Reranking 模型在特定领域（医疗、法律、金融）的表现可能不够理想。通过在领域数据上微调可以显著提升效果。微调数据通常构造为三元组形式：(query, positive_doc, negative_doc)。模型通过对比学习优化，拉近正样本距离、推远负样本距离。

构造高质量负样本是微调成功的关键。简单的随机负样本太容易区分，模型学不到有区分力的特征。推荐使用"困难负样本"策略：从向量检索结果中选取排名靠后但不在标注正例中的文档作为负样本。这些文档与查询有一定相关性但不是最佳答案，能够帮助模型学习更精细的区分能力。

## 4.6 表格、图片与混合文档处理

企业实际的文档很少是纯文本。技术手册中包含参数表格、产品说明书中包含结构图、财务报告中包含图表数据。如何从混合文档中高质量地提取和处理多种内容形态，是知识处理的重要课题。

### 混合文档类型分类

| 文档类型 | 内容组成 | 提取难点 | 典型场景 |
|---------|---------|---------|---------|
| 纯文本文档 | 标题、段落 | 格式保留 | 政策文件、合同 |
| 图文混排文档 | 文字+图片 | 图文对应关系 | 产品手册、教材 |
| 表格文档 | 行列数据 | 跨页表格、合并单元格 | 财务报表、规格表 |
| 扫描文档 | 图像化文本 | OCR精度、版面分析 | 历史档案、发票 |
| 公式文档 | 数学公式 | 公式识别与编码 | 学术论文、专利 |
| 多栏文档 | 分栏排版 | 阅读顺序还原 | 论文、报纸 |

### 表格提取与处理

表格是结构化信息的重要载体，但也是文档处理中的难点。PDF 中的表格提取质量直接影响了下游的检索和问答效果。

常用的表格提取工具包括 Camelot、Tabula、pdfplumber 和 Unstructured。不同工具在不同类型的 PDF 上表现差异很大。

```python
import pdfplumber

def extract_tables_from_pdf(pdf_path):
    """从PDF中提取表格并转换为结构化文本"""
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # 转换为Markdown表格格式
                if len(table) < 2:
                    continue
                header = table[0]
                rows = table[1:]
                md_table = format_as_markdown(header, rows)
                all_tables.append(md_table)
    return all_tables

def format_as_markdown(header, rows):
    """将表格格式化为Markdown"""
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)
```

表格提取后，如何组织成可检索的文本块是一个需要精心设计的问题。一种方案是将表格转换为 Markdown 格式的文本，与所在章节的摘要一起作为一个文档块。另一种方案是将表格的每一行拆分为独立的文本块，附带表头作为上下文。前者保持了表格的完整性，后者提高了行级检索的精度。

### 图片处理与多模态理解

文档中的图片包含丰富的信息。传统的处理方式是使用 OCR (Optical Recognition, 光学字符识别) 提取图片中的文字。但很多图片的信息并非以文字形式存在，例如流程图、架构图、产品外观图等。

现代多模态模型为图片处理提供了新的思路。使用 VLM (Vision Language Model, 视觉语言模型) 可以对图片内容生成描述性文本，将视觉信息转化为可检索的文本表示。

```python
def process_document_images(images, vlm_model):
    """使用VLM处理文档图片"""
    image_descriptions = []
    for img in images:
        # 根据图片类型选择不同的提示词
        if is_chart(img):
            prompt = "请描述这个图表的数据趋势和关键数值"
        elif is_diagram(img):
            prompt = "请描述这个流程图/架构图的组件和关系"
        elif is_photo(img):
            prompt = "请描述这个图片的内容和关键特征"
        else:
            prompt = "请详细描述图片内容"
        
        description = vlm_model.generate(img, prompt)
        image_descriptions.append({
            "image": img,
            "description": description,
            "type": classify_image_type(img)
        })
    return image_descriptions
```

### 混合文档统一处理流水线

对于一份完整的混合文档，需要设计统一的处理流水线：

```
原始文档 (PDF/Word/HTML)
        |
        v
+------------------+
| 文档解析与版面分析 |
+------------------+
        |
        +--- 文本块 ---> 文本清洗 --> 语义分块
        |
        +--- 表格 -----> 结构化提取 -> Markdown转换
        |
        +--- 图片 -----> VLM描述生成
        |
        +--- 公式 -----> LaTeX识别
        |
        v
+------------------+
| 多模态内容融合     |
| (文本+表格+图片描述)|
+------------------+
        |
        v
+------------------+
| 统一向量化与入库   |
+------------------+
```

### 延展：表格问答的特殊处理

当用户提问涉及表格数据时（"2024年第三季度营收是多少"），常规的文本检索往往无法准确定位到表格中的具体单元格。针对表格问答，有两种增强方案。

方案一是表格序列化：将表格转换为一行一记录的文本格式，每条记录独立作为一个文档块入库。检索时可以精确命中包含目标数值的行。方案二是 Text-to-SQL：如果表格已存储在关系型数据库中，可以使用 LLM 将自然语言查询转换为 SQL 语句直接查询，精度更高但实现复杂度也更大。

工程实践中，两种方案可以组合使用：先通过序列化表格的文本检索快速定位相关表格，再对候选表格使用 Text-to-SQL 进行精确查询，兼顾效率和精度。

## 4.7 客户私有知识库构建全流程

构建客户私有知识库是 FDE (Foundation Model Deployment Engineer, 基础模型部署工程师) 在项目中反复经历的核心工作。这不是一次性的数据导入操作，而是一个包含需求分析、数据采集、清洗加工、结构化组织、质量验证、持续更新的完整工程过程。

### 知识库构建全流程

```
Phase 1: 需求分析
  |-- 业务场景梳理
  |-- 用户画像分析
  |-- 知识范围界定
  |-- 质量标准定义
  |
  v
Phase 2: 数据采集
  |-- 现有系统数据导出
  |-- 文档收集与分类
  |-- 专家知识访谈记录
  |-- 外部数据源接入
  |
  v
Phase 3: 数据清洗加工
  |-- 格式统一与编码规范化
  |-- 去重去噪与实体标准化
  |-- 缺失值填补与质量校验
  |
  v
Phase 4: 知识结构化
  |-- 文档分块与元数据标注
  |-- 知识层级关系提取
  |-- 术语表与同义词库构建
  |-- 权限标签与分类标记
  |
  v
Phase 5: 向量化与入库
  |-- Embedding模型选择
  |-- 批量向量化与索引构建
  |-- 混合检索配置
  |
  v
Phase 6: 质量验证
  |-- 标准问答集测试
  |-- 检索召回率与精确率评估
  |-- 人工抽检与反馈修正
  |
  v
Phase 7: 持续运维
  |-- 增量更新机制
  |-- 质量监控告警
  |-- 知识过期与淘汰
  |-- 用户反馈闭环
```

### 需求分析阶段的关键输出

需求分析是知识库构建的起点，决定了后续所有工作的方向。这一阶段需要明确三个核心问题。

第一个问题是知识范围界定。并非企业的所有文档都应该放入知识库。需要根据业务场景筛选与 Agent 职能相关的文档子集。例如，一个客服 Agent 的知识库应包含产品手册、FAQ、退换货政策，而不需要包含内部财务报表。

第二个问题是用户画像分析。不同用户群体提问的方式和关注点不同。技术人员可能直接使用产品型号和术语查询，普通用户可能用日常语言描述问题。了解用户画像有助于优化分块策略和检索配置。

第三个问题是质量标准定义。需要与业务方共同定义可接受的准确率、召回率和响应时间指标。这些指标不仅指导初始构建的质量控制，也是后续运维的监控基线。

### 知识结构化与元数据设计

元数据是知识库可用性的关键保障。每一篇文档入库时都应附带丰富的元数据标签，支持后续的过滤检索和分析统计。

常用的元数据字段包括：文档来源（系统名称或部门名称）、文档类型（手册、FAQ、政策、公告等）、创建时间与更新时间、有效期、分类标签（产品线、业务模块）、权限级别（公开、内部、机密）、版本号。

```python
# 文档入库时的元数据标注示例
document_metadata = {
    "source": "产品研发部",
    "doc_type": "product_manual",
    "product_line": "智能网联",
    "version": "v2.3",
    "created_at": "2024-06-15",
    "updated_at": "2024-08-01",
    "expiry": "2025-06-15",
    "access_level": "internal",
    "language": "zh-CN",
    "tags": ["配置指南", "API", "V2.3"],
    "chunk_index": 5,
    "total_chunks": 28
}
```

### 持续更新与知识保鲜

知识库不是静态的。产品迭代、政策变更、流程调整都需要知识库同步更新。需要建立增量更新机制，而非每次全量重建。

增量更新的关键在于变更检测和版本管理。可以通过文件哈希值比对检测文档变更，对变更的文档重新进行分块和向量化，删除旧版本的分块向量，插入新版本。同时保留版本历史，支持时间点回溯查询（"截至2024年6月，该产品的规格参数是什么"）。

知识过期是另一个需要关注的问题。建议为每篇文档设置有效期字段，到期后自动标记为"待审核"状态，暂停检索服务，待人工确认更新后恢复。这可以有效避免 Agent 基于过时信息给出错误答案。

### 延展：知识库质量评估指标体系

知识库构建完成后，需要建立量化的质量评估体系。可以从四个层面评估：

覆盖度：知识库内容是否覆盖了业务场景中的主要问题。通过标准问答集的召回率来衡量，目标值通常在90%以上。

精度：检索结果中相关文档的比例。通过Top-5精确率和Top-10召回率衡量。

时效性：知识库内容与最新业务状态的一致性。统计过期文档比例和平均更新延迟。

可用性：用户查询到满意答案的比例。通过用户反馈（点赞/点踩）和人工抽检综合评估。

## 4.8 GraphRAG：知识图谱增强检索

传统的 RAG 系统基于向量相似度检索文档，在处理需要跨文档推理、全局性总结、多跳关联的复杂问题时表现不足。GraphRAG (Graph-enhanced Retrieval-Augmented Generation, 知识图谱增强检索) 通过引入知识图谱结构，将孤立的文档片段连接为有组织的知识网络，显著提升了复杂问题的回答能力。

### GraphRAG 与传统 RAG 的对比

| 维度 | 传统 RAG | GraphRAG |
|------|---------|----------|
| 数据结构 | 扁平的向量集合 | 图结构（节点+边） |
| 检索方式 | 相似度匹配 | 图遍历+向量检索 |
| 多跳推理 | 弱，依赖上下文窗口 | 强，通过关系边跳转 |
| 全局总结 | 受限于检索片段 | 可通过社区摘要实现 |
| 构建成本 | 低 | 高（需实体抽取和关系建模） |
| 适用场景 | 事实型问答 | 关系推理、全局分析 |

### GraphRAG 架构

```
原始文档集
    |
    v
+-------------------+
| 实体抽取与关系提取  |
| (LLM/NER模型)     |
+-------------------+
    |
    +-- 实体节点 (人/组织/概念)
    +-- 关系边 (属于/合作/竞争...)
    +-- 属性 (时间/金额/状态...)
    |
    v
+-------------------+
| 知识图谱构建        |
| (Neo4j/NetworkX)  |
+-------------------+
    |
    +-- 社区检测 (Leiden/Louvain)
    +-- 社区摘要生成 (LLM)
    |
    v
+-------------------+
| 混合检索引擎        |
+-------------------+
    |
    +-- 向量检索 (局部精准匹配)
    +-- 图遍历检索 (多跳关联)
    +-- 社区摘要检索 (全局总结)
    |
    v
+-------------------+
| 结果融合与排序      |
+-------------------+
    |
    v
  LLM 生成答案
```

### 实体与关系抽取

实体抽取是 GraphRAG 的第一步。使用 LLM 从文档中抽取实体和关系，比传统 NER (Named Entity Recognition, 命名实体识别) 模型更灵活，能够识别领域特定的实体类型和关系类型。

```python
import json

entity_extraction_prompt = """
从以下文档中抽取实体和关系，输出JSON格式。
实体类型：人物、组织、产品、技术、事件
关系类型：属于、研发、合作、竞争、投资、使用

文档内容：
{document}

输出格式：
{{
  "entities": [
    {{"name": "...", "type": "...", "description": "..."}}
  ],
  "relations": [
    {{"subject": "...", "predicate": "...", "object": "..."}}
  ]
}}
"""

def extract_entities_relations(document, llm):
    prompt = entity_extraction_prompt.format(document=document)
    result = llm.generate(prompt)
    return json.loads(result)
```

### 社区检测与摘要生成

GraphRAG 的一个重要创新是社区检测。通过将知识图谱中的节点聚类为社区（即主题相关的实体群组），为每个社区生成摘要，使得全局性问题可以通过社区摘要快速回答，而不需要遍历所有文档。

常用的社区检测算法包括 Leiden 算法和 Louvain 算法。Leiden 算法在效率和质量之间有较好的平衡，是 GraphRAG 的推荐选择。

```python
import networkx as nx
from community import community_louvain

def detect_communities(graph):
    """使用Louvain算法进行社区检测"""
    partition = community_louvain.best_partition(graph)
    
    # 按社区分组节点
    communities = {}
    for node, community_id in partition.items():
        if community_id not in communities:
            communities[community_id] = []
        communities[community_id].append(node)
    
    return communities

def generate_community_summaries(communities, graph, llm):
    """为每个社区生成摘要"""
    summaries = {}
    for cid, nodes in communities.items():
        # 收集社区内所有实体和关系
        subgraph = graph.subgraph(nodes)
        entity_info = format_subgraph(subgraph)
        
        prompt = f"请总结以下知识图谱子集中实体的主题和关键关系：\n{entity_info}"
        summaries[cid] = llm.generate(prompt)
    
    return summaries
```

### 检索策略：局部与全局的结合

GraphRAG 的检索分为三个层次，针对不同类型的问题：

局部检索：从查询相关的实体节点出发，沿关系边遍历邻居节点，获取与查询实体直接关联的知识。适合具体实体的事实型查询（"张三在哪个部门"）。

全局检索：查询所有社区摘要，找到与查询主题最相关的社区，返回社区摘要作为上下文。适合全局性问题（"公司在AI领域的技术布局"）。

混合检索：结合向量检索的语义匹配能力和图遍历的关联推理能力。先用向量检索定位入口实体，再用图遍历扩展关联知识。适合多跳推理问题（"与张三合作的李四负责的产品有哪些"）。

### 延展：GraphRAG 的工程挑战

GraphRAG 在实际工程落地中面临几个挑战。首先是构建成本高：实体抽取和关系建模需要大量的 LLM 调用，构建一个包含百万文档的知识图谱可能需要数千美元的 API 费用。其次是增量更新复杂：新文档加入时需要更新图谱结构和社区划分，全量重建成本过高。第三是查询路由设计：需要根据查询类型自动选择局部或全局检索策略，这本身就是一个分类问题。

实践中的建议是：对于以事实型问答为主的知识库，传统 RAG 已能满足需求，不需要引入 GraphRAG 的复杂性。当业务场景明确需要多跳推理、关系分析或全局总结时，再考虑引入 GraphRAG，并可以从轻量级的图增强方案开始（如在元数据中记录实体关系，检索时做简单的图遍历扩展），而非一步到位构建完整的知识图谱。

## 4.9 多语言与跨语言场景处理

在全球化企业和跨国项目中，知识库往往包含多种语言的文档。用户查询的语言也可能与文档语言不一致。多语言和跨语言场景的处理是 AI Agent 国际化部署必须解决的问题。

### 多语言场景分类

| 场景 | 描述 | 示例 | 处理策略 |
|------|------|------|---------|
| 单语言知识库 | 知识库和查询使用同一语言 | 中文知识库+中文查询 | 单语言Embedding模型 |
| 跨语言查询 | 查询语言与文档语言不同 | 中文查询+英文文档 | 多语言Embedding模型 |
| 混合语言知识库 | 知识库包含多种语言 | 中英文混合文档 | 多语言Embedding+语言过滤 |
| 代码混合查询 | 查询中混合多种语言 | "帮我看看这个function的log" | 多语言Embedding+意图识别 |
| 翻译需求 | 需要将检索结果翻译 | 英文文档翻译为中文回答 | 检索+翻译后处理 |

### 多语言 Embedding 模型选择

多语言场景下，Embedding 模型的选择至关重要。模型需要将不同语言的语义相近内容映射到向量空间中的相近位置。

主流的多语言 Embedding 模型包括：

BGE-M3：支持100+语言，在 MTEB (Massive Text Embedding Benchmark, 大规模文本嵌入基准) 多语言榜单上表现优异，支持稠密检索、稀疏检索和多向量检索三种模式。

multilingual-e5-large：微软发布的多语言模型，支持94种语言，在跨语言检索任务上表现稳定。

Cohere Embed v3 Multilingual：商业模型，支持100+语言，在多语言场景下效果出色但需要API调用。

```python
from sentence_transformers import SentenceTransformer

# 使用多语言模型
model = SentenceTransformer('BAAI/bge-m3')

# 中文查询检索英文文档
chinese_query = "数据库连接池配置最佳实践"
english_docs = [
    "Best practices for database connection pooling",
    "How to optimize SQL query performance",
    "Connection pool sizing guidelines"
]

query_vec = model.encode(chinese_query)
doc_vecs = model.encode(english_docs)

# 计算相似度（跨语言匹配）
from util import cos_sim
similarities = cos_sim(query_vec, doc_vecs)
# 结果：英文文档1与中文查询的相似度最高
```

### 跨语言检索的架构设计

跨语言检索系统需要考虑几个特殊问题。

语言检测：首先需要检测查询和文档的语言。对于短查询，语言检测可能不准确，建议结合用户的语言偏好设置进行判断。

语言路由：如果知识库中不同语言的文档分别存储在不同的 Collection 中，需要根据检测到的语言路由到正确的 Collection。也可以统一存储，在元数据中标记语言字段。

回退策略：当跨语言检索结果不佳时，可以回退到翻译后检索。即将查询翻译为文档语言后再进行检索，或者将文档翻译为查询语言后建立索引。

```python
def multilingual_retrieval(query, knowledge_base, top_k=5):
    """多语言检索流程"""
    # 1. 语言检测
    query_lang = detect_language(query)
    
    # 2. 多语言向量检索
    results = knowledge_base.search(
        query=query,
        filter=None,  # 不按语言过滤，允许跨语言匹配
        top_k=top_k * 2  # 多取一些用于后续筛选
    )
    
    # 3. 如果跨语言结果质量不足，回退到翻译检索
    if results[0].score < 0.5:
        # 翻译查询为知识库主语言
        translated_query = translate(query, target_lang='en')
        results_en = knowledge_base.search(
            query=translated_query,
            filter={"language": "en"},
            top_k=top_k
        )
        results = merge_results(results, results_en)
    
    # 4. Reranking
    final_results = reranker.rerank(query, results, top_k=top_k)
    return final_results
```

### 翻译质量与术语一致性

跨语言场景中，翻译质量直接影响知识库的可用性。机器翻译的常见问题包括：专业术语翻译不统一、数字和单位转换错误、否定语义丢失等。

建议为客户建立领域术语表（Glossary），在翻译流程中引入术语约束。术语表应包含源语言术语、目标语言标准翻译、以及禁止使用的错误翻译。对于关键领域（医疗、法律、金融），建议对机器翻译结果进行人工审校。

### 延展：文化适配与本地化

多语言处理不仅是语言翻译，还包括文化适配。同一个产品在不同市场可能有不同的名称、规格和合规要求。知识库需要通过元数据区分不同市场的版本，检索时根据用户的市场区域返回对应版本的内容。

日期格式、数字格式、货币单位等本地化细节也需要注意。例如在跨地区知识库中，"2024/03/15"在不同地区可能被理解为3月15日或3月2024日，建议统一使用 ISO 8601 格式存储，展示时再根据用户区域格式化。

## 4.10 数据安全与隐私保护体系

企业知识库中往往包含商业机密、客户个人信息、财务数据等敏感信息。在构建和使用知识库的过程中，数据安全与隐私保护是不可妥协的基础要求。一次数据泄露事件不仅造成经济损失，更会严重损害客户信任。

### 威胁模型与安全层次

知识库系统面临的安全威胁可以从多个层次分析：

| 安全层次 | 威胁描述 | 防护措施 |
|---------|---------|--------|
| 数据存储层 | 数据库被未授权访问、物理介质丢失 | 加密存储、磁盘加密、访问控制 |
| 数据传输层 | 网络窃听、中间人攻击 | TLS加密、证书校验、VPN |
| 应用层 | 越权访问、SQL注入、提示注入 | RBAC、参数化查询、输入过滤 |
| 模型层 | 模型逆向攻击、训练数据泄露 | 差分隐私、模型隔离、输出过滤 |
| 检索层 | 通过查询推断知识库内容 | 查询审计、频率限制、结果脱敏 |
| 运维层 | 内部人员泄露、操作失误 | 操作审计、最小权限原则、双人复核 |

### 数据分类分级

数据安全的第一步是数据分类分级。不同级别的数据需要不同强度的保护措施。

| 数据等级 | 定义 | 典型内容 | 保护要求 |
|---------|------|---------|---------|
| 公开级 | 可对外公开的信息 | 产品宣传材料、公开公告 | 基本访问控制 |
| 内部级 | 仅限内部员工访问 | 内部流程文档、培训材料 | 身份认证+日志审计 |
| 机密级 | 限制在特定团队访问 | 产品设计文档、技术方案 | RBAC+加密传输+水印 |
| 绝密级 | 极少数人可访问 | 核心算法、财务核心数据 | 多因素认证+加密存储+操作审计 |
| 合规级 | 受法规保护的个人信息 | 客户PII、员工薪酬 | 脱敏处理+合规审计+数据影响评估 |

### 访问控制设计

基于角色的访问控制（RBAC, Role-Based Access Control）是知识库安全的基础。每个用户根据其角色获得相应等级的文档访问权限。在向量检索时，通过元数据过滤确保用户只能检索到其有权限的文档。

```python
def secure_retrieval(query, user, knowledge_base, top_k=5):
    """带访问控制的检索"""
    # 获取用户权限标签
    user_permissions = get_user_permissions(user)
    
    # 构建权限过滤条件
    access_filter = {
        "access_level": {"$in": user_permissions["levels"]},
        "department": {"$in": user_permissions["departments"]},
        # 排除用户无权访问的产品线
        "product_line": {"$in": user_permissions["products"]}
    }
    
    # 带过滤的向量检索
    results = knowledge_base.search(
        query=query,
        filter=access_filter,
        top_k=top_k
    )
    
    # 二次校验（防止过滤配置错误）
    for r in results:
        if not check_access(user, r.metadata):
            log_security_event(
                user, "access_denied", r.doc_id
            )
            continue
    
    return results
```

### PII 保护与数据脱敏

PII (Personally Identifiable Information, 个人可识别信息) 的保护是合规要求的重点。知识库入库前应对 PII 进行脱敏处理。

脱敏策略包括：掩码替换（保留部分字符，如手机号显示为 138****5678）、哈希替换（用哈希值替代原文）、泛化处理（将精确年龄替换为年龄段）、删除处理（完全移除敏感字段）。

```python
import re

def redact_pii(text):
    """文本PII脱敏"""
    # 手机号脱敏
    text = re.sub(
        r'1[3-9]\d{9}',
        lambda m: m.group()[:3] + '****' + m.group()[-4:],
        text
    )
    # 身份证号脱敏
    text = re.sub(
        r'\d{17}[\dXx]',
        lambda m: m.group()[:6] + '********' + m.group()[-4:],
        text
    )
    # 邮箱地址脱敏
    text = re.sub(
        r'[\w.-]+@[\w.-]+\.\w+',
        lambda m: m.group()[:2] + '***@' + m.group().split('@')[1],
        text
    )
    # 银行卡号脱敏
    text = re.sub(
        r'\d{16,19}',
        lambda m: m.group()[:4] + '****' + m.group()[-4:],
        text
    )
    return text
```

### 提示注入防护

在 RAG 系统中，提示注入（Prompt Injection）是一种特殊的安全威胁。攻击者可能在文档中植入恶意指令，当 Agent 检索到该文档并拼接到提示中时，恶意指令被 LLM 执行。

防护策略包括：输入过滤（检测文档中的指令性语句）、内容隔离（使用特殊标记区分检索内容和系统指令）、输出审查（检查 Agent 输出是否包含异常行为）。

```python
def sanitize_retrieved_content(content):
    """对检索内容进行安全清洗"""
    # 检测潜在的提示注入模式
    injection_patterns = [
        r'ignore (all )?previous instructions',
        r'you are now (a|an) ',
        r'forget (everything|all) (above|before)',
        r'system prompt:',
        r'\[INST\].*\[/INST\]',
    ]
    for pattern in injection_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            log_security_event(
                "unknown", "prompt_injection", content[:100]
            )
            return "[内容已过滤：检测到潜在安全风险]"
    return content
```

### 审计与合规

完整的审计日志是安全体系的最后防线。所有知识库的访问、查询、修改操作都应记录在审计日志中，日志内容包含操作者身份、操作时间、操作类型、操作对象和操作结果。

对于受法规约束的行业（如金融行业的 GDPR、医疗行业的 HIPAA），还需要满足额外的合规要求。例如 GDPR 赋予数据主体"被遗忘权"，知识库需要支持基于个人信息的精确删除，这要求向量数据库支持按元数据条件删除向量。

### 延展：联邦学习与隐私计算

在数据不能出域的场景中（如跨机构合作、跨境数据传输限制），可以采用隐私计算技术实现知识共享。联邦学习允许各参与方在本地训练模型，只交换模型参数而非原始数据。安全多方计算（MPC, Multi-Party Computation）允许多方在不泄露各自输入的情况下共同计算函数结果。

在 RAG 场景中，一种可行的方案是：各机构本地维护各自的向量数据库，通过联邦检索协议在查询时协调多个本地库的检索结果。这样既实现了知识共享，又保证了各机构数据不出域。这种方案的挑战在于检索延迟和系统复杂度，目前仍处于探索阶段，但随着隐私计算技术的成熟，有望成为跨机构知识共享的标准方案。

## 本章知识点总结

以下是本章十个主题的核心知识点汇总：

| 小节 | 核心概念 | 关键决策点 | 工程要点 |
|------|---------|-----------|--------|
| 4.1 数据质量 | 六维评估框架(完整/准确/一致/时效/唯一/合规) | 质量阈值设定 | 建立清洗流水线和长效治理机制 |
| 4.2 文档分块 | 六种分块策略(固定/递归/语义/结构/滑窗/增强) | 块大小与重叠参数 | 按文档类型选择策略，建立评估体系 |
| 4.3 向量数据库 | 八种主流方案对比 | 规模/部署/检索能力 | 选型决策树，TCO考量 |
| 4.4 Hybrid Search | 向量+关键词混合检索 | 融合算法(RRF/加权)与权重 | 两阶段架构：广召回+深精排 |
| 4.5 Reranking | Cross-Encoder精排模型 | 模型选择与部署优化 | 量化/批量/ONNX加速，领域微调 |
| 4.6 混合文档 | 表格/图片/公式多模态处理 | 提取工具与VLM选择 | 统一处理流水线，表格序列化 |
| 4.7 知识库构建 | 七阶段全流程 | 需求范围与质量标准 | 元数据设计，增量更新，保鲜机制 |
| 4.8 GraphRAG | 知识图谱增强检索 | 局部/全局/混合检索策略 | 社区检测，实体关系抽取，成本权衡 |
| 4.9 多语言 | 跨语言检索与翻译处理 | Embedding模型与回退策略 | 语言检测，术语表，文化适配 |
| 4.10 数据安全 | 六层安全防护体系 | 数据分级与访问控制 | RBAC，PII脱敏，提示注入防护 |

本章覆盖了数据工程与知识处理的全链路，从数据质量治理到安全合规，构建了一套面向企业级 AI Agent 部署的完整知识工程方法论。掌握这些内容，能够在 FDE 项目中系统性地解决数据层面的工程挑战，为 AI Agent 的可靠运行奠定坚实的数据基础。

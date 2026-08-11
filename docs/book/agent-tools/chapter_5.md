# 深度研究智能体与 AI 搜索——让 AI 替你做调研

5 分钟生成 46 页论文，AI 研究助手已经能做到这个程度了。但你敢用吗？

我是怕浪猫，《智能体产品全景手册》第 5 篇。这一篇我们讲一个 2025 年爆火的 Agent 垂直赛道：深度研究和 AI 搜索。当 AI 从"回答问题"进化到"做调研"，信息获取的方式正在被彻底重写。

## 5.1 AI 搜索引擎的进化：从关键词到意图

传统搜索引擎（Google、百度）的工作方式是"关键词匹配"——你输入关键词，搜索引擎在索引中找到包含这些关键词的网页，按相关性排序返回。这个范式统治了互联网搜索 20 年。

AI 搜索引擎改变了这个范式。它不是匹配关键词，而是理解你的意图，然后从多个来源收集信息，综合生成一个直接回答你问题的结果。

### AI 搜索的工作流程

AI 搜索的核心流程可以拆解为五个步骤：

**步骤一：意图理解**。AI 搜索引擎首先用 LLM 理解用户的查询意图。当你搜索"2026 年 AI Agent 市场规模"时，LLM 理解你要的是"具体的数字和数据"，而不是"关于 AI Agent 市场的文章"。

**步骤二：查询生成**。LLM 根据理解到的意图，生成多个搜索查询。不是只搜一次，而是从多个角度搜索。比如"AI Agent market size 2026"、"AI Agent industry revenue 2026"、"AI Agent market forecast"等。

**步骤三：并行检索**。多个搜索查询并行执行，获取大量网页结果。

**步骤四：内容提取**。对每个网页，提取正文内容（去掉导航、广告、侧边栏），生成摘要。

**步骤五：综合生成**。LLM 基于所有摘要生成最终回答，标注引用来源。

```
# AI 搜索引擎的核心流程
class AISearchEngine:
    def search(self, query):
        # 1. 意图理解
        intent = self.llm.understand_intent(query)
        # intent = {"type": "factual", "topic": "AI Agent market size", 
        #           "time_constraint": "2026", "needs_data": True}
        
        # 2. 生成多个搜索查询
        search_queries = self.llm.generate_queries(intent)
        # ["AI Agent market size 2026", 
        #  "AI Agent industry revenue forecast 2026",
        #  "AI Agent market growth rate 2026"]
        
        # 3. 并行检索
        all_results = []
        for sq in search_queries:
            results = self.search_api.search(sq, num_results=10)
            all_results.extend(results)
        
        # 4. 内容提取与去重
        contents = []
        seen_urls = set()
        for result in all_results:
            if result.url not in seen_urls:
                content = self.extractor.extract(result.url)
                contents.append({
                    "url": result.url,
                    "title": result.title,
                    "content": content
                })
                seen_urls.add(result.url)
        
        # 5. 综合生成
        answer = self.llm.synthesize(
            query=query,
            sources=contents,
            style="comprehensive"  # 全面型回答
        )
        
        return {"answer": answer, "sources": contents}
```

> 传统搜索给你一堆链接让你自己找答案，AI 搜索直接给你答案并告诉你答案来自哪里。这是从"图书馆"到"私人助理"的转变。

### 主流 AI 搜索产品

**Perplexity AI**：AI 搜索的标杆产品。Pro Search 功能支持多步推理搜索，不是简单搜一次就回答，而是根据初步搜索结果生成后续查询，层层深入。Deep Research 功能更进一步，能执行数十步的搜索和分析。月访问量约 3 亿次，在专业人士和学生中广泛使用。

Perplexity 在 Deep Research 基准测试中得分 21.1%，超越 Gemini Thinking。而且 Deep Research 功能完全免费使用，这是它相对于 OpenAI Deep Research 的核心竞争优势。

**New Bing（Microsoft Copilot）**：微软将 GPT-4 接入 Bing 搜索引擎，是最早的 AI 搜索产品。月访问量 36.6 亿，依托 Windows 和 Edge 浏览器的预装优势，用户量巨大。但在 AI 搜索的质量上，Perplexity 仍领先。

**秘塔 AI 搜索**：国内 AI 搜索的代表产品。特色是"无广告、直答式"搜索体验，直接给出结构化答案而非链接列表。在法律、学术等中文垂直领域有较好的搜索质量。

**百度文小言**：百度的"新搜索"智能助手。支持模糊提问（不需要精确关键词）、边拍边问（图像+文字混合搜索）、多轮对话追问等功能。依托手机百度的用户基础，在国内搜索市场有较大覆盖。

### AI 搜索 vs 传统搜索

| 维度 | 传统搜索（Google/百度） | AI 搜索（Perplexity） |
|------|----------------------|---------------------|
| 交互方式 | 关键词输入 | 自然语言提问 |
| 结果形式 | 网页链接列表 | 直接答案+引用 |
| 多步推理 | 不支持 | 支持 |
| 信息综合 | 用户自己做 | AI 自动完成 |
| 实时性 | 索引延迟 | 实时检索 |
| 信息溯源 | 链接即来源 | 引用标注 |
| 适合场景 | 导航型搜索（找网站） | 信息型搜索（找答案） |

> AI 搜索不是替代传统搜索，而是分工。你要找一个网站用 Google，你要找一个答案用 Perplexity。

## 5.2 Deep Research 深度研究智能体

如果说 AI 搜索是"快速回答问题"，Deep Research 就是"花时间做调研报告"。它是 AI 搜索的深化版本——不是搜一两次就回答，而是执行数十步甚至上百步的搜索、阅读、分析、综合，最终输出一份完整的研究报告。

### OpenAI Deep Research

OpenAI 在 2025 年 2 月推出 Deep Research 功能，面向 Pro 用户（$200/月）。

核心能力：给定一个研究主题，Deep Research 会自主执行数十步搜索和分析。它能访问互联网、阅读论文、提取数据、对比分析，最终生成一份带引用的结构化研究报告。

技术原理：Deep Research 基于优化后的 GPT-4o 模型，采用多轮搜索策略。第一轮搜索获取概览，第二轮根据概览中的关键点深入搜索，第三轮查漏补缺。每一轮的搜索结果都会被分析、摘要、存入上下文。

在 GAIA 基准测试中，OpenAI Deep Research 得分 26.6%，是所有 Deep Research 产品中最高的。但这个分数也意味着——它只能正确完成约四分之一的复杂研究任务。Deep Research 还远未达到"完全可靠"的程度。

定价是 OpenAI Deep Research 的争议点。$200/月的 Pro 订阅才能使用，且有使用次数限制。对于个人用户来说，这个价格门槛很高。

### Gemini Deep Research

Google 在 Gemini 3 Pro 中集成了 Deep Research 功能，这是目前性能最强的深度研究 Agent。

核心数据：在测试中，Gemini Deep Research 5 分钟生成了 46 页学术论文，减少幻觉效果显著。性能超过 OpenAI Deep Research 40%，价格只有后者的十分之一。

Gemini Deep Research 的技术优势来自三个方面：

**Google 搜索集成**：直接使用 Google 搜索的索引和算法，搜索质量和覆盖率是所有产品中最好的。

**多模态理解**：能理解和分析图表、PDF、图片中的信息，不只是文本。

**超长上下文**：Gemini 3 Pro 支持 1M+ tokens 的上下文窗口，能把大量搜索结果一次性放入上下文中进行综合分析。

```
# Gemini Deep Research 的工作流程
class GeminiDeepResearch:
    def research(self, topic):
        # 阶段1：概览搜索（广度优先）
        overview = self.gemini.search_and_summarize(topic)
        # 生成主题大纲
        outline = self.gemini.generate_outline(overview)
        
        # 阶段2：深度搜索（深度优先）
        sections = []
        for section_topic in outline.sections:
            # 对每个子主题执行多轮搜索
            section_research = self._deep_search_section(section_topic)
            sections.append(section_research)
        
        # 阶段3：数据验证
        for section in sections:
            section.verified_data = self._verify_data(section.data_points)
        
        # 阶段4：综合生成
        report = self.gemini.synthesize(
            topic=topic,
            outline=outline,
            sections=sections,
            format="academic"  # 学术报告格式
        )
        
        return report  # 46页论文级别的研究报告
```

### Perplexity Deep Research

Perplexity 的 Deep Research 是性价比最高的选择——免费使用，得分 21.1%。

Perplexity Deep Research 的特点是透明性。它会实时显示每一步搜索的查询词、访问的网页、提取的信息。用户可以看到 AI 是怎么一步步构建研究结论的，这增加了结果的可信度。

### GPT Researcher（开源方案）

GPT Researcher 是一个开源的深度研究 Agent，GitHub 上有数千 Star。

核心特色是树状探索策略和极低成本（每次研究约 $0.4）。

树状探索的原理是：给定一个研究主题，先生成 3-5 个子主题，每个子主题再生成 3-5 个更细的主题，形成一棵树。然后对树的每个叶节点执行搜索，自底向上汇总信息。

```
# GPT Researcher 的树状探索策略
class GPTResearcher:
    def research(self, topic, depth=3):
        # 构建研究树
        research_tree = self._build_tree(topic, depth)
        """
        示例树结构：
        AI Agent市场
        ├── 市场规模
        │   ├── 全球数据
        │   ├── 区域分布
        │   └── 增长预测
        ├── 主要玩家
        │   ├── 国际厂商
        │   └── 国内厂商
        └── 技术趋势
            ├── 多Agent协作
            ├── Agent协议
            └── 端侧Agent
        """
        
        # 深度优先搜索每个叶节点
        results = {}
        for leaf in research_tree.leaves():
            # 搜索+提取+摘要
            raw_data = self.search(leaf.topic)
            summary = self.llm.summarize(raw_data)
            results[leaf.path] = summary
        
        # 自底向上汇总
        return self._aggregate(results, research_tree)
```

GPT Researcher 的优势是成本极低。每次研究约花费 $0.4 的 API 费用，是商业产品的百分之一。缺点是输出质量不如 Gemini 和 OpenAI 的 Deep Research，需要人工审核和补充。

下面是四款 Deep Research 产品的横向对比：

| 产品 | 开发方 | 价格 | 测试得分 | 核心优势 |
|------|--------|------|---------|---------|
| OpenAI Deep Research | OpenAI | $200/月 | 26.6% | 得分最高 |
| Gemini Deep Research | Google | Gemini Advanced | - | 性能超OAI 40%，价仅1/10 |
| Perplexity Deep Research | Perplexity | 免费 | 21.1% | 免费透明 |
| GPT Researcher | 开源 | ~$0.4/次 | - | 开源低成本 |

> Deep Research 产品的核心价值不是"写得快"，而是"搜得全"。46 页报告的关键不是写作能力，而是搜集和整合了数百个信息源。

## 5.3 RAG 与 Agentic RAG：从静态检索到动态探索

RAG（Retrieval-Augmented Generation，检索增强生成）是 AI 研究工具的底层技术。但传统 RAG 和 Agentic RAG 有本质区别。

### 传统 RAG 的局限

传统 RAG 是"一次检索"模式：用户提问 → 检索 Top-K 文档 → LLM 基于文档生成回答。这种方式有几个局限：

**问题一：检索不够深**。一次检索只能获取有限的文档，对于复杂问题（需要多角度信息）远远不够。

**问题二：不能追问**。如果第一次检索的结果不足以回答问题，传统 RAG 没有机制来生成后续查询。

**问题三：缺乏验证**。传统 RAG 直接把检索结果交给 LLM 生成回答，没有验证信息的准确性和一致性。

### Agentic RAG：让检索变成一个 Agent

Agentic RAG 将 RAG 升级为 Agent 模式。核心变化是：检索不再是一次性操作，而是一个"搜索-评估-再搜索"的迭代循环。

```
# Agentic RAG 的核心循环
class AgenticRAG:
    def research(self, question, max_iterations=5):
        context = []
        
        for i in range(max_iterations):
            # 1. 基于已有上下文生成搜索查询
            query = self.llm.generate_query(
                question=question,
                existing_context=context
            )
            
            # 2. 执行检索
            new_docs = self.retrieve(query)
            
            # 3. 评估是否足够回答问题
            is_sufficient = self.llm.evaluate(
                question=question,
                context=context + new_docs
            )
            
            context.extend(new_docs)
            
            if is_sufficient:
                # 信息足够，生成最终答案
                return self.llm.answer(question, context)
        
        # 达到最大迭代次数，基于已有信息尽力回答
        return self.llm.answer(question, context)
```

Agentic RAG 的关键创新是"自我评估"——Agent 会在每一轮检索后评估是否已经有足够的信息来回答问题。如果不够，它会生成更精准的后续查询继续搜索。这种迭代检索模式让 AI 能处理需要多步推理的复杂问题。

> 传统 RAG 是"查一次就答"，Agentic RAG 是"查到够为止"。区别就像学生翻书——前者只翻一页，后者翻到弄懂为止。

### Agentic RAG 的应用场景

Agentic RAG 在以下场景中比传统 RAG 有显著优势：

**竞争分析**：需要搜集多个竞争对手的产品信息、定价、用户评价，综合对比。传统 RAG 一次检索无法覆盖所有竞争对手，Agentic RAG 可以逐个搜索后汇总。

**学术综述**：需要阅读大量论文，提取每篇论文的核心观点，识别共识和分歧。Agentic RAG 可以按主题分批检索论文，逐步构建综述。

**尽职调查**：需要搜集公司的财务数据、法律风险、市场前景等多维度信息。Agentic RAG 可以按维度逐个深入搜索。

## 5.4 深度研究 Agent 的评估标准

Deep Research 产品越来越多，怎么评估它们的质量？我提出五个维度。

**维度一：信息覆盖率**

研究报告是否覆盖了主题的主要方面？有没有遗漏重要信息？这是最基础的评估维度。一个好的研究报告应该从多个角度全面覆盖主题。

评估方法：选取一个你熟悉的主题，让 Deep Research 生成报告，然后检查它是否覆盖了你认为重要的所有子主题。

**维度二：数据准确性**

报告中的数字、日期、事实是否准确？AI 最大的风险是幻觉——生成看似合理但实际不存在的数据。

评估方法：随机抽取报告中的 10 个数据点，人工验证其准确性。准确率低于 80% 的产品不可接受。

**维度三：引用可靠性**

报告中的引用是否指向真实存在的来源？有些 AI 会"编造"引用——给出一个看起来合理的 URL，但实际访问后发现内容不存在或不相关。

评估方法：随机抽取报告中的 5 个引用链接，逐一访问验证。

**维度四：逻辑连贯性**

报告的结构是否清晰？论点之间是否有逻辑关系？还是只是信息的堆砌？好的研究报告应该有明确的论点和论证逻辑，而不是"数据大杂烩"。

评估方法：阅读报告的结论部分，看它是否从前文的分析中自然推导出来。

**维度五：时效性**

报告是否包含了最新的信息？对于快速变化的领域（如 AI、加密货币），使用一年前的数据可能已经过时。

评估方法：检查报告中引用的最新信息的日期，与当前日期的差距。

下面是一个评估打分表模板：

| 评估维度 | 权重 | OpenAI DR | Gemini DR | Perplexity DR | GPT Researcher |
|---------|------|-----------|-----------|---------------|----------------|
| 信息覆盖率 | 25% | 8/10 | 9/10 | 7/10 | 6/10 |
| 数据准确性 | 25% | 8/10 | 9/10 | 8/10 | 7/10 |
| 引用可靠性 | 20% | 9/10 | 8/10 | 9/10 | 7/10 |
| 逻辑连贯性 | 15% | 8/10 | 9/10 | 7/10 | 6/10 |
| 时效性 | 15% | 8/10 | 9/10 | 9/10 | 7/10 |
| 加权总分 | 100% | 8.2 | 8.8 | 7.9 | 6.6 |

> Deep Research 的最大风险不是"写得不好"，而是"写得很好但内容是编的"。越流畅的报告越要警惕幻觉。

## 5.5 实战场景：行业调研、竞品分析、学术研究

最后，我们看三个实战场景，帮你理解什么时候该用哪个工具。

### 场景一：行业调研

需求：调研"2026 年中国 AI Agent 企业级市场规模、主要玩家和发展趋势"。

推荐工具：Gemini Deep Research。理由：行业调研需要大量数据支撑，Gemini 依托 Google 搜索有最广的信息覆盖。5 分钟生成 46 页论文的能力能快速产出初稿。

使用技巧：给 Deep Research 一个清晰的研究框架会效果更好。不要只说"调研 AI Agent 市场"，而是说"从市场规模、竞争格局、技术趋势、政策环境、投资动态五个维度调研 2026 年中国 AI Agent 企业级市场"。

后续处理：Deep Research 生成的报告是初稿，需要人工补充行业专家观点、最新政策变化等 AI 可能遗漏的信息。

### 场景二：竞品分析

需求：对比 Manus、OpenAI Operator、AutoGLM 三款自主执行 Agent 的功能、定价、性能。

推荐工具：Perplexity Pro Search。理由：竞品分析需要实时信息（定价、功能更新频繁），Perplexity 的实时搜索和透明引用最适合这种任务。

使用技巧：分产品逐一搜索，每次搜索聚焦一个产品的特定维度（功能、定价、评测），最后人工汇总对比。

### 场景三：学术研究

需求：综述"Agentic RAG 技术的发展脉络、核心方法和未来方向"。

推荐工具：GPT Researcher + 人工补充。理由：学术研究需要引用论文，GPT Researcher 的树状探索能系统性地覆盖子主题。开源方案可以自定义搜索来源（如 Google Scholar、arXiv），确保引用的是学术论文而非博客。

使用技巧：设置搜索来源为学术数据库，depth 设为 4-5（更深的探索层级），生成后人工检查每个引用是否为真实论文。

### 场景四：快速事实查询

需求：查"2026 年全球 AI Agent 市场规模是多少亿美元"。

推荐工具：Perplexity 免费版。理由：简单事实查询不需要 Deep Research，Perplexity 的基础搜索就能快速给出答案和引用。

### 场景五：多角度综合分析

需求：分析"AI Agent 对就业市场的影响，包括正面和负面观点"。

推荐工具：OpenAI Deep Research。理由：多角度分析需要深度推理和平衡论述，OpenAI Deep Research 在 GAIA 测试中得分最高，适合需要细致分析的复杂问题。

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| 行业调研 | Gemini DR | 信息覆盖最广 |
| 竞品分析 | Perplexity | 实时搜索透明 |
| 学术研究 | GPT Researcher | 可自定义来源 |
| 事实查询 | Perplexity 免费版 | 快速够用 |
| 多角度分析 | OpenAI DR | 推理能力最强 |

这一章我们拆解了 AI 搜索引擎的进化路径（从关键词到意图），深入分析了四款 Deep Research 产品（OpenAI、Gemini、Perplexity、GPT Researcher），讲解了从传统 RAG 到 Agentic RAG 的技术升级，提出了五维度评估标准，最后给出了五个实战场景的选型建议。

| 产品类别 | 产品数量 | 市场格局 |
|---------|---------|---------|
| AI 搜索 | 4 款 | Perplexity 标杆 |
| Deep Research | 4 款 | Gemini 性价比最高 |

觉得有用？收藏起来，下次做调研直接照着选工具。

你用过哪个 AI 研究工具？生成的报告靠谱吗？评论区聊聊你的体验。

关注怕浪猫，下期我们讲计算机操作智能体与 RPA 超自动化——AI 直接操作你的电脑，这是怎么做到的。系列进度 5/10，关注不错过后续更新。

下一篇，怕浪猫会带你走进 CUA（Computer Use Agent，计算机使用智能体）的世界。AI 怎么看懂屏幕上的按钮？怎么知道该点哪里？RPA 和 CUA 到底谁会取代谁？我们下期见。

---
sidebar_position: 4
---

# 编程智能体——AI 写代码的全景拆解

GitHub Copilot 有 2000 万开发者在用，但 2026 年最火的编程工具已经不是它了。

我是怕浪猫，《智能体产品全景手册》第 4 篇。前两篇讲了开发平台和框架，这一篇我们聚焦一个最成熟的 AI Agent 垂直赛道：编程。AI 写代码不是未来时，而是现在进行时——但"AI 辅助写代码"和"AI 独立写代码"之间，隔着一条巨大的鸿沟。

## 4.1 从 Copilot 到 Devin：编程 Agent 的三级进化

编程智能体的进化路径和通用 Agent 类似，也经历了三个阶段。但编程领域的阶段划分更清晰，因为每个阶段都有标志性的产品。

**第一级：代码补全（Code Completion）**

代表性产品：GitHub Copilot（2021 年发布）、Tabnine、Amazon CodeWhisperer。

核心能力是根据上下文预测接下来的代码。你写了一行 `def fibonacci(n):`，它自动补全函数体。本质上是一个高级的"自动联想"——从"预测下一个词"升级到"预测下一行代码"。

技术原理是基于 LLM 的代码生成。模型在海量开源代码上训练，学会了代码的模式和惯例。当你在编辑器中输入代码时，模型根据已有的上下文（当前文件、相邻文件、光标位置）生成候选代码。

这个级别的局限是：AI 只能看到"眼前"，不能理解整个项目的架构。它生成的代码在局部是对的，但放在全局可能是错的。

**第二级：对话式编程（Chat-based Coding）**

代表性产品：GitHub Copilot Chat、Cursor Chat、ChatGPT Code Interpreter。

核心能力是开发者用自然语言描述需求，AI 生成完整的代码块或函数。不再局限于补全光标位置的代码，而是可以根据"写一个二分查找函数"这样的指令生成完整实现。

这个级别还引入了"上下文感知"——AI 能读取整个项目文件、理解代码结构、参考多个文件的依赖关系。Cursor 在这一级做得最好，它的 Codebase Indexing（代码库索引）功能让 AI 能理解整个项目的上下文。

**第三级：自主软件工程（Autonomous Software Engineering）**

代表性产品：Devin（Cognition Labs）、OpenHands、Replit Agent。

核心能力是给定一个高阶任务描述（比如"帮我做一个待办事项 Web 应用，支持用户注册登录"），AI 自主完成：需求分析、技术选型、项目搭建、代码编写、测试调试、部署上线。

这是真正的"AI 程序员"——不是辅助你写代码，而是自己写代码。Devin 在 SWE-bench（Software Engineering Benchmark）上的表现是这一级的标杆。

> 三级进化的本质是"人的参与度递减"：第一级人写 AI 补、第二级人说 AI 写、第三级人验收 AI 做。

下面是三级进化对比表：

| 维度 | 第一级：补全 | 第二级：对话 | 第三级：自主 |
|------|------------|------------|------------|
| 人的角色 | 主力，AI 辅助 | 指挥，AI 执行 | 验收，AI 全程 |
| 任务粒度 | 一行/一块 | 一个函数/模块 | 一个完整项目 |
| 上下文理解 | 当前文件 | 整个项目 | 项目+环境+部署 |
| 典型产品 | Copilot 补全 | Cursor Chat | Devin |
| 人效提升 | 30-50% | 2-3 倍 | 5-10 倍（理论上） |

## 4.2 AI 原生编辑器对决：Cursor vs Windsurf vs Trae

2025-2026 年，编程工具赛道最激烈的竞争不在"Agent"层面，而在"编辑器"层面。一批 AI 原生编辑器正在挑战 VS Code + Copilot 的统治地位。

### Cursor

Cursor 是 Anysphere 开发的 AI 原生代码编辑器，基于 VS Code 分叉。2025 年估值达数十亿美元，是编程工具赛道增长最快的产品。

Cursor 的核心特色：

**Codebase Indexing（代码库索引）**：Cursor 会索引你的整个项目代码库，构建向量索引。当你提问时，AI 不只看当前文件，而是理解整个项目的上下文。这意味着它生成的代码能正确引用项目中的其他模块、遵循项目的编码风格、避免命名冲突。

**Cmd+K 内联编辑**：选中一段代码，按 Cmd+K，用自然语言描述你想要的修改，Cursor 直接在编辑器中修改代码。比"把这段循环改成列表推导式"更自然的方式。

**Composer（组合器）**：Cursor 的高级功能，能跨多个文件进行修改。你描述一个需求（比如"添加用户头像上传功能"），Composer 会同时修改前端组件、后端 API、数据库 Schema、路由配置等多个文件。

**Cursor Tab**：增强版代码补全。不只是补全当前光标位置的代码，还能预测你接下来要做的多处修改。比如你修改变量名后，它能预测你在其他文件中也需要同步修改。

```
# Cursor Composer 的工作原理（简化）
class CursorComposer:
    def __init__(self, codebase_index, llm):
        self.index = codebase_index  # 全项目向量索引
        self.llm = llm
    
    def compose(self, instruction, current_file):
        # 1. 检索相关文件
        relevant_files = self.index.search(instruction, top_k=10)
        
        # 2. 构建修改计划
        plan = self.llm.plan(
            instruction=instruction,
            current_file=current_file,
            context_files=relevant_files
        )
        # plan = [
        #   {"file": "frontend/UserProfile.tsx", "action": "add_avatar_component"},
        #   {"file": "backend/api/upload.ts", "action": "add_upload_endpoint"},
        #   {"file": "backend/db/schema.ts", "action": "add_avatar_column"},
        #   {"file": "backend/routes.ts", "action": "register_route"}
        # ]
        
        # 3. 逐文件生成修改
        changes = []
        for step in plan:
            modified_content = self.llm.generate(
                file_content=read_file(step["file"]),
                instruction=step["action"],
                context=relevant_files
            )
            changes.append({"file": step["file"], "content": modified_content})
        
        return changes
```

### Windsurf

Windsurf 是 Codeium 推出的 AI 原生编辑器，同样基于 VS Code 分叉。它的核心差异化是"Cascade（级联）"功能。

Cascade 是 Windsurf 的多步编辑引擎。与 Cursor 的 Composer 类似，Cascade 能跨文件修改。但 Cascade 的独特之处在于它能"边写边跑"——生成代码后自动运行测试，根据测试结果迭代修改。

Windsurf 还引入了"Supercomplete"功能，这是一种更智能的代码补全。它不只补全当前光标位置，还会根据你的意图预测接下来 2-3 步的代码修改。比如你开始写一个错误处理块，它会预测你还需要在调用方添加对应的错误处理，并提前给出建议。

### Trae

Trae 是字节跳动推出的 AI 原生编辑器，2025 年发布后以"免费"策略快速获取用户。

Trae 的核心卖点是免费使用 Claude 3.5 Sonnet 和 GPT-4o 等顶级模型。在 Cursor 收费的情况下，Trae 的免费策略极具吸引力。据报告，Trae 的代码生成准确率达到 98%，在多个基准测试中超越 Cursor 和 Windsurf。

Trae 还有一个差异化功能：AI Schedule（AI 排期）。它能根据你的项目结构和待办事项，自动生成开发计划并按优先级执行。这让它从"编辑器"向"项目管理工具"的方向延伸。

下面是三款 AI 原生编辑器的横向对比：

| 维度 | Cursor | Windsurf | Trae |
|------|--------|----------|------|
| 开发方 | Anysphere | Codeium | 字节跳动 |
| 价格 | $20/月起 | $15/月起 | 免费 |
| 模型支持 | GPT-4o/Claude/Sonnet | GPT-4o/Claude | GPT-4o/Claude |
| 代码库索引 | 强 | 强 | 强 |
| 多文件编辑 | Composer | Cascade | AI Schedule |
| 补全能力 | Cursor Tab | Supercomplete | 智能补全 |
| 测试集成 | 弱 | 强（边写边跑） | 中 |
| 生态 | VS Code 插件兼容 | VS Code 插件兼容 | VS Code 插件兼容 |

> AI 原生编辑器的竞争焦点已经从"谁补全得准"变成了"谁能跨文件修改"。下一步的竞争焦点是"谁能自主完成整个功能模块"。

## 4.3 自主软件工程师 Agent：Devin、Replit Agent、OpenHands

这一节我们进入编程 Agent 的最高级别：自主软件工程师。这些产品不再需要你一行行写代码，你只需要描述需求，Agent 自己完成全部开发工作。

### Devin（Cognition Labs）

Devin 由 Cognition Labs 在 2024 年 3 月发布，被称为"世界上第一个 AI 软件工程师"。

Devin 的核心能力：

**自主规划**：给定一个任务描述，Devin 会先生成执行计划，列出需要完成的步骤。

**代码编写与执行**：Devin 有自己的代码编辑器、终端和浏览器。它能写代码、运行代码、查看报错、修改代码。

**调试能力**：当代码出错时，Devin 能阅读错误信息、定位问题、修复 Bug。

**部署能力**：Devin 能将完成的项目部署到生产环境。

Devin 在 SWE-bench 上的表现是其核心卖点。SWE-bench 是一个软件工程基准测试，包含真实的 GitHub Issue，要求 AI 理解 Issue 描述、定位相关代码、编写修复补丁。Devin 的通过率约为 13.86%，虽然看起来不高，但这是端到端自主完成的，没有人类干预。

Devin 的商业模式是订阅制，起价 500 美元/月，面向工程团队。2025 年 Cognition 估值达数十亿美元。

### Replit Agent

Replit Agent 是在线编程平台 Replit 推出的 AI 开发 Agent。与 Devin 不同，Replit Agent 专注于"从零到一"的项目创建。

你用自然语言描述一个想法（比如"做一个天气查询应用，输入城市名显示当前天气"），Replit Agent 会自动搭建项目、编写代码、配置环境、运行应用。整个过程在 Replit 的云 IDE 中完成，不需要本地环境。

Replit Agent 的核心流程：

```
# Replit Agent 的工作流程
class ReplitAgent:
    def build_app(self, idea):
        # 1. 需求理解
        spec = self.llm.analyze(idea)
        # spec = {
        #     "type": "web_app",
        #     "features": ["城市搜索", "天气显示", "单位切换"],
        #     "tech_stack": "React + Express + OpenWeather API"
        # }
        
        # 2. 项目初始化
        self.workspace.init(spec["tech_stack"])
        self.workspace.install_dependencies(["react", "express", "axios"])
        
        # 3. 代码生成（分模块）
        for module in spec["features"]:
            code = self.llm.generate(
                feature=module,
                project_context=self.workspace.get_context()
            )
            self.workspace.write_file(module["path"], code)
        
        # 4. 运行与调试
        result = self.workspace.run()
        if result.has_errors:
            self._debug_and_fix(result.errors)
        
        # 5. 部署
        return self.workspace.deploy()
```

Replit Agent 的优势是"即时可用"——不需要安装任何东西，在浏览器中就能完成从想法到上线的全过程。特别适合快速原型验证和编程教学。

### OpenHands（原 OpenDevin）

OpenHands 是 Devin 的开源替代方案，在 GitHub 上有数万 Star。

OpenHands 复刻了 Devin 的核心架构：代码编辑器 + 终端 + 浏览器三件套。Agent 能在这三个环境中自主操作。与 Devin 的闭源商业模式不同，OpenHands 完全开源，任何人都可以免费使用和修改。

OpenHands 也参加了 SWE-bench 测试，通过率约为 12%，接近 Devin 的水平。这证明了开源社区有能力复刻闭源商业 Agent 的核心能力。

## 4.4 GitHub Copilot 全家桶：从补全到 AgentHQ

GitHub Copilot 是编程 AI 的开创者，也是用户量最大的产品。2026 年，GitHub Copilot 已不再只是一个代码补全工具，而是发展成了一个"全家桶"产品线。

### GitHub Copilot 补全

最基础的功能，2021 年发布。在编辑器中实时补全代码。核心模型基于 OpenAI 的 Codex（GPT-3 的代码专用版本），后来升级到 GPT-4 系列。

用户量：2000 万+ 开发者。定价：$10/月（个人版），$19/月（企业版）。2026 年 6 月开始转按 Token 计费。

> 从固定月费转按 Token 计费，这个变化说明一件事：AI 编程的使用量已经大到固定定价模型无法覆盖成本了。

### GitHub Copilot Chat

2023 年发布的对话式编程功能。开发者可以在 VS Code 中直接与 AI 对话，提问代码相关问题、请求代码解释、生成代码片段。

Copilot Chat 的核心价值是"上下文感知"——它能理解当前打开的文件、选中的代码、项目结构。这意味着你问"这个函数是做什么的"时，它知道"这个函数"指的是哪个。

### GitHub Copilot Workspace

2024 年发布的更高阶功能。Workspace 能理解整个 GitHub 仓库的上下文，支持跨文件代码修改。你可以给 Copilot 一个 Issue（比如"修复登录页面的样式错位"），Workspace 会分析代码库、定位相关文件、提出修改方案、生成代码。

### GitHub AgentHQ

2025 年底发布的最新功能，标志着 GitHub 正式进入"自主 Agent"赛道。AgentHQ 能自主处理 GitHub Issue——从理解 Issue 描述开始，到分析代码库、编写修复代码、运行测试、提交 Pull Request。

AgentHQ 的核心工作流：

```
# AgentHQ 处理 Issue 的流程
class AgentHQ:
    def handle_issue(self, issue):
        # 1. 理解 Issue
        analysis = self.llm.analyze_issue(
            title=issue.title,
            description=issue.body,
            labels=issue.labels
        )
        
        # 2. 定位相关代码
        relevant_files = self.codebase_search(
            query=analysis.keywords,
            repo=issue.repo
        )
        
        # 3. 生成修复方案
        fix_plan = self.llm.plan_fix(
            issue=analysis,
            context=relevant_files
        )
        
        # 4. 编写修复代码
        for change in fix_plan.changes:
            new_code = self.llm.generate_code(
                file=change.file,
                instruction=change.instruction,
                context=change.surrounding_code
            )
            self.write_file(change.file, new_code)
        
        # 5. 运行测试
        test_result = self.run_tests()
        if test_result.failed:
            self._fix_failing_tests(test_result.failures)
        
        # 6. 提交 PR
        self.create_pull_request(
            title=f"Fix: {issue.title}",
            body=f"Resolves #{issue.number}\n\n{fix_plan.summary}"
        )
```

AgentHQ 的定位是"AI 团队成员"——它不是你的工具，而是你的同事。你给它分配 Issue，它自己完成后提交 PR，你来 Review 和 Merge。

## 4.5 国产编程 Agent：通义灵码、CodeGeeX 的差异化路线

国产编程 Agent 在 2025-2026 年快速崛起，走出了与国际产品不同的路线。

### 通义灵码（阿里云）

通义灵码是阿里云推出的 AI 编程助手，基于通义千问代码模型。

核心差异化：

**中文理解优势**：在注释生成、文档编写、中文需求理解方面优于国际产品。对于中文团队的代码注释和文档生成，通义灵码更自然。

**企业级私有化**：支持企业私有化部署，满足数据安全要求。与阿里云百炼平台集成，企业可以在自己的云上构建编程 Agent。

**多语言支持**：在 Java、Python、Go、JavaScript、TypeScript 等主流语言上表现优秀，特别在 Java 生态（Spring Cloud、MyBatis 等框架）上有深度优化。

通义灵码对个人开发者免费，企业版按需定价。在阿里系技术团队中有较高采用率。

### CodeGeeX（智谱 AI）

CodeGeeX 是智谱 AI 推出的开源编程助手，基于 GLM 代码模型。

核心差异化：

**开源免费**：CodeGeeX 模型开源，任何人可以本地部署。这对于不能使用云端 API 的场景（如军工、金融核心系统）至关重要。

**多语言代码生成**：CodeGeeX 在 20+ 编程语言上进行了训练，特别在小众语言（Rust、Scala、Haskell）上表现优于预期。

**IDE 集成**：支持 VS Code、JetBrains IDE、Vim 等主流编辑器，插件体验与国际产品一致。

### 国产 vs 国际的差异化路线

国产编程 Agent 走出了三个差异化方向：

**方向一：中文场景优化**。代码注释、技术文档、需求文档的中文理解和生成。国际产品在中文注释生成上经常出现语法不自然或用词不当的问题。

**方向二：私有化部署**。金融、政府、军工等行业的代码不能上云，必须私有化部署。国产 Agent 在这方面有天然的合规优势。

**方向三：国产技术栈适配**。对国产数据库（OceanBase、TiDB）、国产中间件（Apollo、Nacos）、国产框架（Spring Cloud Alibaba）的深度理解。

> 国产编程 Agent 的机会不在"比 Copilot 更强"，而在"比 Copilot 更懂中国开发者的工作环境"。

下面是主要编程 Agent 产品的横向对比：

| 产品 | 类型 | 价格 | 核心能力 | 适合用户 |
|------|------|------|---------|---------|
| GitHub Copilot | 补全+对话 | $10/月→Token计费 | 生态最大 | 国际开发者 |
| Cursor | AI编辑器 | $20/月 | Composer跨文件 | 全栈开发者 |
| Windsurf | AI编辑器 | $15/月 | Cascade边写边跑 | 注重测试的团队 |
| Trae | AI编辑器 | 免费 | 免费+98%准确率 | 预算敏感开发者 |
| Devin | 自主Agent | $500/月起 | SWE-bench最优 | 工程团队 |
| Replit Agent | 自主Agent | 订阅制 | 浏览器端全流程 | 快速原型 |
| OpenHands | 自主Agent | 开源免费 | Devin开源替代 | 开源社区 |
| 通义灵码 | 补全+对话 | 免费 | 中文+私有化 | 中文技术团队 |
| CodeGeeX | 补全 | 开源免费 | 开源+多语言 | 数据敏感场景 |

这一章我们完整拆解了编程 Agent 的三级进化（补全→对话→自主），对比了 3 款 AI 原生编辑器（Cursor、Windsurf、Trae），深入分析了 3 款自主软件工程师 Agent（Devin、Replit Agent、OpenHands），梳理了 GitHub Copilot 全家桶的进化路径，最后对比了国产编程 Agent 的差异化路线。

| 产品类别 | 产品数量 | 市场格局 |
|---------|---------|---------|
| AI 编辑器 | 3 款 | Cursor 领先，Trae 免费追赶 |
| 自主 Agent | 3 款 | Devin 标杆，OpenHands 开源 |
| 补全工具 | 3 款 | Copilot 用户量第一 |

觉得有用？收藏起来，下次选编程工具直接照抄。

你在用哪个编程 AI？Cursor 还是 Copilot？有没有被 AI 写的代码坑过？评论区聊聊。

关注怕浪猫，下期我们讲深度研究智能体与 AI 搜索——OpenAI Deep Research、Gemini Deep Research、Perplexity Deep Research 到底谁做的调研报告最靠谱。系列进度 4/10，关注不错过后续更新。

下一篇，怕浪猫会带你走进 AI 研究助手的世界。5 分钟生成 46 页论文的 Gemini Deep Research 是怎么做到的？GPT Researcher 每次只花 0.4 美元的开源方案值不值得用？我们下期见。

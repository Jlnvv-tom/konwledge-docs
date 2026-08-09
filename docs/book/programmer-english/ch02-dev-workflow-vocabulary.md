---
sidebar_position: 2
---

# 第二章：开发流程词汇

> 写代码不只是敲键盘，更是一连串的协作动作——提交、测试、部署、审查。每个环节都有一套行业通用词汇，搞懂它们，你就能无障碍地读懂英文文档、参与国际团队讨论、在 GitHub 上和全世界开发者谈笑风生。

---

## 2.1 版本控制词汇

版本控制是开发流程的地基。无论你用 Git、Mercurial 还是别的什么，下面这些词汇几乎每天都在你的终端里出现。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| **commit** | 提交 | 将代码变更保存到本地仓库的一个快照，每条 commit 有一条 message 描述改了什么 |
| **branch** | 分支 | 从主线分出来的独立开发线，让你在不影响主干的情况下自由修改 |
| **merge** | 合并 | 将一个分支的变更并入另一个分支，Git 会自动尝试整合代码 |
| **rebase** | 变基 | 把一个分支的 commit 重新"嫁接"到另一个分支的末端，使提交历史更线性 |
| **pull request (PR)** | 拉取请求 | 在团队协作中，请求将你的分支合并到目标分支的机制；GitHub 叫 PR，GitLab 叫 MR (Merge Request) |
| **stash** | 暂存 | 把当前工作区的改动临时收起来，不提交也不丢弃，方便切换分支 |
| **cherry-pick** | 摘樱桃 | 从某个分支上挑出特定的一个或几个 commit，单独应用到当前分支 |
| **fork** | 派生 | 在远程仓库层面复制一份别人的项目到你自己的账号下，之后可以独立修改 |
| **clone** | 克隆 | 把远程仓库完整下载到本地，包括所有分支和提交历史 |
| **fetch** | 获取 | 从远程仓库拉取最新信息，但不自动合并到当前分支，比 pull 更"安全" |

### 使用场景与例句

**日常提交：**

```bash
git commit -m "fix: resolve null pointer exception in user service"
```

在团队沟通中，你会经常听到这样的表达：

- "I just **pushed** a new **commit** to the `feature/login` **branch**."（我刚往 `feature/login` 分支推了一个新提交。）
- "Can you **review** my **PR** before I **merge** it?"（我合并之前你能审查一下我的 PR 吗？）
- "I **stashed** my changes because I need to switch to `main` to hotfix."（我把改动暂存了，因为得切回 main 修个紧急 bug。）

**Rebase vs Merge 的经典讨论：**

- "Our team prefers **rebase** to keep the history linear."（我们团队偏好 rebase，保持提交历史线性整洁。）
- "I'll **merge** the feature branch into `develop`."（我会把功能分支合并到 develop。）

**Cherry-pick 场景：**

当你发现一个 bug fix 在 `hotfix` 分支上修好了，但 `main` 分支也需要这个修复，又不想合并整个分支时：

- "I **cherry-picked** the bug fix commit from `hotfix` to `main`."（我从 hotfix 分支摘了那个修复 commit 到 main 上。）

### 常见误用与混淆

| 容易混淆的词 | 区别 |
|-------------|------|
| **push vs commit** | commit 是本地保存快照，push 是把本地 commit 推到远程仓库。先 commit 再 push。 |
| **pull vs fetch** | pull = fetch + merge，fetch 只是"看看远程有啥新东西"，pull 直接拉下来合并。想安全看一眼用 fetch。 |
| **rebase vs merge** | merge 保留分叉历史（会有 merge commit），rebase 重写提交历史使其线性。rebase 会改变 commit hash，已推送的分支慎用。 |
| **fork vs clone** | fork 是在服务器端复制仓库到你账号（社交属性，可以发 PR），clone 是把仓库下载到本地（纯操作）。 |
| **PR vs MR** | GitHub 叫 Pull Request (PR)，GitLab 叫 Merge Request (MR)，本质一样。混着说大家也听得懂。 |

> 💡 **小贴士：** 写 commit message 时，社区约定第一行用动词开头（如 `fix:`, `feat:`, `docs:`, `refactor:`），这是 Conventional Commits 规范，越来越普遍。

---

## 2.2 测试相关词汇

测试是代码质量的最后一道防线。从开发自己写的单元测试，到 QA 团队跑的端到端测试，这套词汇贯穿整个开发周期。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| **unit test** | 单元测试 | 对代码中最小可测试单元（通常是一个函数或方法）进行验证，确保输入输出符合预期 |
| **integration test** | 集成测试 | 验证多个模块组合在一起后能否正常协作，比如数据库 + API + 业务逻辑的联动 |
| **e2e test (end-to-end test)** | 端到端测试 | 模拟真实用户从入口到出口的完整操作流程，验证整个系统的行为 |
| **mock** | 模拟对象 | 用一个"假"对象替代真实依赖，预先设定它的返回值，让测试不依赖外部系统 |
| **stub** | 桩 | 比 mock 更简单，只提供预设的返回值，不验证交互行为 |
| **spy** | 间谍 | 包装真实对象，记录调用情况（被调了几次、参数是什么），但不替换行为 |
| **fixture** | 测试夹具 | 测试前准备的固定数据和状态，确保每个测试在相同初始条件下运行 |
| **coverage** | 覆盖率 | 测试覆盖代码行/分支/函数的比例，常用工具如 Istanbul、JaCoCo、coverage.py |
| **TDD (Test-Driven Development)** | 测试驱动开发 | 先写测试（红灯），再写代码使其通过（绿灯），然后重构的循环流程 |
| **assertion** | 断言 | 测试中验证"某条件是否为真"的语句，不成立则测试失败 |
| **snapshot test** | 快照测试 | 将组件输出保存为快照，后续测试对比快照是否变化，前端常用 |

### 使用场景与例句

**TDD 的经典循环：**

```
Red 🔴 → Write a failing test
Green 🟢 → Write minimal code to pass
Refactor ♻️ → Improve code quality while keeping tests green
```

在代码审查或技术讨论中：

- "Make sure to add **unit tests** for the new utility function."（确保给新的工具函数加上单元测试。）
- "The **integration test** is failing because the test database isn't set up."（集成测试挂了，因为测试数据库没配好。）
- "We use Playwright for **e2e tests** to cover the checkout flow."（我们用 Playwright 做端到端测试，覆盖结账流程。）
- "Can you **mock** the email service so the test doesn't actually send emails?"（你能不能把邮件服务 mock 掉，别让测试真的发邮件？）
- "Our **coverage** dropped to 78% after the last merge — let's add more tests."（上次合并后覆盖率掉到 78% 了，我们多补点测试。）

**Mock vs Stub 的代码对比：**

```python
# Stub：只提供假返回值
def test_get_user():
    user_service.get_user = lambda id: {"name": "Alice"}  # stub
    result = handler.handle(1)
    assert result.name == "Alice"

# Mock：验证交互行为
def test_send_email_called():
    email_service = Mock()
    handler = OrderHandler(email_service)
    handler.process_order(order)
    email_service.send.assert_called_once_with("Order confirmed")  # mock 验证调用
```

### 常见误用与混淆

| 容易混淆的词 | 区别 |
|-------------|------|
| **mock vs stub** | Stub 只提供假数据（"我调你，你返回这个"），Mock 还验证交互（"我确认你被调了一次，参数是这个"）。简单说：Stub 关注状态，Mock 关注行为。 |
| **integration test vs e2e test** | 集成测试关注模块间的接口和协作（代码层面），端到端测试模拟完整用户操作（从 UI 到数据库全链路）。集成测试偏开发者视角，e2e 偏用户视角。 |
| **coverage 高 ≠ 测试好** | 100% 覆盖率不代表覆盖了所有边界条件和异常路径。覆盖率是参考指标，不是质量保证。 |
| **TDD ≠ 先写所有测试** | TDD 是小步循环：写一个测试 → 写最小代码通过 → 重构。不是一次性写完所有测试再实现。 |

> 💡 **小贴士：** 很多团队对 coverage 有硬性要求（比如 ≥ 80%），但与其追求高覆盖率，不如追求测试质量——测该测的，比如边界值、异常路径、核心业务逻辑。

---

## 2.3 部署与运维词汇

代码写完、测试通过，下一步就是把它放到服务器上让用户用起来。这个过程中的词汇来自 DevOps 文化，横跨开发和运维。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| **deploy** | 部署 | 将代码发布到运行环境使其对外提供服务的过程 |
| **pipeline (CI/CD pipeline)** | 流水线 | 从代码提交到自动构建、测试、部署的自动化流程，CI = 持续集成，CD = 持续交付/部署 |
| **container** | 容器 | 将应用及其依赖打包在一起的标准单元，保证在任何环境一致运行，最常用的是 Docker |
| **orchestrate** | 编排 | 管理多个容器的部署、扩缩容、网络和故障恢复，代表工具 Kubernetes (K8s) |
| **rollback** | 回滚 | 部署出问题时，将版本退回到上一个稳定版本的操作 |
| **canary (canary release)** | 金丝雀发布 | 先把新版本发布给一小部分用户，观察没有问题后再逐步扩大范围 |
| **blue-green deployment** | 蓝绿部署 | 维护两套相同的生产环境（蓝和绿），一套在线服务一套待命，切换即可完成发布和回滚 |
| **infrastructure as code (IaC)** | 基础设施即代码 | 用代码（而非手动配置）来管理和创建服务器、网络等基础设施，代表工具 Terraform |
| **zero-downtime deployment** | 零停机部署 | 部署过程中服务不中断，用户无感知 |
| **hotfix** | 热修复 | 生产环境出现紧急问题时，跳过完整流程快速修复并部署 |
| **artifact** | 构建产物 | 代码编译打包后的输出物（如 .jar、.war、Docker image），是要部署的实体 |

### 使用场景与例句

**CI/CD 流水线描述：**

- "The **pipeline** automatically runs **unit tests** and builds a Docker **artifact** on every **commit**."（流水线在每次提交时自动运行单元测试并构建 Docker 镜像产物。）
- "After the **artifact** passes all checks, it gets **deployed** to the staging environment."（构建产物通过所有检查后，会被部署到预发布环境。）

**发布策略讨论：**

- "We're doing a **canary** release — routing 5% traffic to the new version first."（我们在做金丝雀发布，先把 5% 流量导到新版本。）
- "With **blue-green deployment**, we can **rollback** instantly by switching traffic back to the blue environment."（用蓝绿部署，我们切回蓝环境就能瞬间回滚。）
- "The deploy caused a memory leak, so we had to **rollback** to the previous version."（部署导致内存泄漏，只好回滚到上一个版本。）

**容器编排场景：**

- "We **orchestrate** our microservices with Kubernetes, handling auto-scaling and self-healing."（我们用 Kubernetes 编排微服务，处理自动扩缩容和故障自愈。）
- "The **container** crashed due to OOM (Out of Memory), K8s restarted it automatically."（容器因为 OOM 崩了，K8s 自动重启了它。）

### 常见误用与混淆

| 容易混淆的词 | 区别 |
|-------------|------|
| **CI vs CD** | CI (Continuous Integration) 是持续集成——代码合并+自动测试；CD 可以是 Continuous Delivery（持续交付，到 staging 就停）或 Continuous Deployment（持续部署，一路到生产）。 |
| **canary vs blue-green** | 蓝绿是两套环境直接切换（全量切换），金丝雀是按比例逐步放量（渐进式）。金丝雀风险更低但更复杂。 |
| **container vs VM** | 容器共享宿主机内核，启动快、资源占用小；VM 每个实例有完整操作系统，隔离性更强但更重。 |
| **rollback vs revert** | rollback 是部署层面的回退（换回旧版本），revert 是代码层面的操作（创建一个反向 commit 撤销改动）。 |
| **staging vs production** | staging 是模拟生产环境的预发布环境，用于上线前最后验证；production 是真正面向用户的线上环境。 |

> 💡 **小贴士：** 在国际团队中，"deploy to prod" 这个短语出现的频率极高。如果听到有人说 "Don't deploy on Friday"（别在周五部署），这是血泪教训——周五部署出问题没人愿意周末加班修。

---

## 2.4 敏捷开发词汇

大多数现代软件开发团队都采用某种形式的敏捷开发。这套词汇来自 Scrum、Kanban 等方法论，出现在每天的站会、每个迭代的规划中。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| **sprint** | 迭代/冲刺 | 一个固定时长的开发周期，通常 1-4 周，结束时交付一批可用的功能 |
| **backlog** | 待办列表 | 按优先级排列的所有待完成工作项的集合，是团队的工作池 |
| **standup (daily standup)** | 每日站会 | 每天简短的同步会议（通常 15 分钟），每人说三件事：昨天做了什么、今天计划做什么、有什么阻碍 |
| **retrospective (retro)** | 回顾会 | 每个 sprint 结束时的团队反思会议，讨论什么做得好、什么需要改进 |
| **user story** | 用户故事 | 从用户视角描述需求的一段文字，格式通常为 "As a [role], I want [feature], so that [benefit]" |
| **story point** | 故事点 | 对工作量复杂度的相对估算值，常用 Fibonacci 数列（1, 2, 3, 5, 8, 13），不是时间单位 |
| **velocity** | 速度 | 团队在一个 sprint 中完成的故事点总数，用于预测未来 sprint 的交付能力 |
| **scrum master** | 敏捷教练 | 负责确保团队遵循敏捷流程、移除阻碍的角色，不是项目经理 |
| **product owner (PO)** | 产品负责人 | 定义需求优先级、维护 backlog 的人，代表用户和业务方的利益 |
| **definition of done (DoD)** | 完成标准 | 团队约定的"一个任务怎样算完成"的检查清单，通常包括代码完成、测试通过、审查通过、文档更新等 |
| **burndown chart** | 燃尽图 | 显示 sprint 中剩余工作量随时间变化的图表，理想情况下应该逐渐"燃尽"到零 |

### 使用场景与例句

**站会上的经典三连问：**

```
1. What did you do yesterday?
2. What will you do today?
3. Are there any blockers?
```

实际表达：

- "Yesterday I finished the **user story** for login **OAuth** integration. Today I'll pick up the next item from the **backlog** — the password reset flow. No **blockers**."（昨天我完成了登录 OAuth 集成的用户故事。今天我准备从 backlog 拿下一个——密码重置流程。没有阻碍。）

**Sprint 规划：**

- "We have a **velocity** of about 34 **story points** per sprint, so let's not over-commit."（我们每个 sprint 的速度大概是 34 个故事点，别过度承诺。）
- "This **user story** is too big — let's **break it down** into smaller ones."（这个用户故事太大了，拆成几个小的吧。）
- "The PO added a bunch of new items to the **backlog**, we need to **groom** and prioritize them."（PO 往 backlog 加了一堆新项，我们需要梳理和排优先级。）

**回顾会：**

- "In the **retro**, we agreed to improve our **CI pipeline** to reduce build time."（回顾会上我们一致同意优化 CI 流水线来减少构建时间。）
- "Let's check the **DoD** — is documentation update included?"（看下完成标准——包含文档更新吗？）

### 常见误用与混淆

| 容易混淆的词 | 区别 |
|-------------|------|
| **story point vs hours** | 故事点衡量的是复杂度（含不确定性），不是工时。一个故事点的工作对老手可能 2 小时，对新手可能 1 天。用相对估算而非绝对时间。 |
| **Scrum vs Kanban** | Scrum 有固定 sprint 节奏和角色划分；Kanban 没有固定迭代，持续流动，限制 WIP（Work In Progress）。两者都属敏捷，但实践不同。 |
| **scrum master vs project manager** | Scrum Master 是流程服务者（"仆人式领导"），不分配任务、不设截止日期；PM 更偏向计划和控制。 |
| **backlog refinement vs sprint planning** | Refinement（也叫 grooming）是日常整理 backlog、拆分和估算故事；Sprint Planning 是每个 sprint 开始时从 backlog 挑选要做的项。 |
| **epic vs user story** | Epic 是大的功能集，包含多个 user story；User story 是可在一个 sprint 内完成的小需求。Epic → Story → Task 层层细化。 |

> 💡 **小贴士：** 如果你听到有人说 "This is a 13-point story"（这是个 13 点的故事），意思是它相当复杂。如果有人估 21 点甚至更高，通常意味着这个故事需要拆分——太大了没法在一个 sprint 内完成。

---

## 2.5 代码审查词汇

代码审查（Code Review）是保障代码质量、促进知识共享的关键环节。在 GitHub、GitLab 等平台上，审查过程中的互动形成了一套独特的交流语言。

### 核心词汇表

| 英文 | 中文 | 简短解释 |
|------|------|----------|
| **review** | 审查 | 对他人提交的代码进行检查，发现潜在问题、提出改进建议 |
| **approve** | 批准 | 审查者认为代码可以合并，给出正式的通过信号 |
| **comment** | 评论 | 在代码审查中提出意见、问题或建议，不一定是要求修改 |
| **suggestion** | 建议 | 提出具体的代码改进方案，通常附带建议的代码片段 |
| **nit (nitpick)** | 小问题 | 对代码风格、命名等细节的吹毛求疵，不影响功能，"鸡蛋里挑骨头" |
| **LGTM** | 看起来不错 | "Looks Good To Me" 的缩写，表示审查通过，通常配合 approve 使用 |
| **changes requested** | 要求修改 | 审查者认为存在问题需要修改，合并被阻止，直到修改后重新审查 |
| **blocking review** | 阻断性审查 | 审查中发现了严重问题，必须解决才能合并 |
| **non-blocking comment** | 非阻断性意见 | 提出的建议或问题不阻塞合并，作者可以选择性采纳 |
| **diff** | 差异/变更 | 代码修改前后的对比视图，审查者通过阅读 diff 来理解改动 |
| **thread** | 讨论线程 | 针对某一行或某一段代码的讨论串，可以来回回复 |
| **resolve** | 解决/标记已解决 | 讨论结束后将线程标记为已解决，表示问题已处理 |
| **code owner** | 代码所有者 | 对某个目录或模块有审查权限和责任的人，通常在 CODEOWNERS 文件中定义 |

### 使用场景与例句

**PR 审查中的典型互动：**

审查者：

- "**LGTM**, just a couple of **nits**."（看起来不错，就几个小问题。）—— 这是最理想的情况，代码基本 OK，只有些风格小细节。
- "**Changes requested**: the error handling is missing for the timeout case."（要求修改：超时情况缺少错误处理。）—— 需要改完再来。
- "**Non-blocking comment**: consider extracting this logic into a helper function for readability."（非阻断性意见：考虑把这段逻辑抽成一个辅助函数提升可读性。）—— 建议但不强制。
- "**Nit**: `user_name` should be `userName` to match our naming convention."（小问题：`user_name` 应该是 `userName`，符合命名规范。）
- "Can you add a **suggestion** for how to refactor this block?"（你能给个重构这块代码的建议吗？）

作者回应：

- "Good catch! Fixed in the latest **commit**."（好眼力！最新提交里修了。）
- "**Resolved** the thread — addressed in commit `a1b2c3d`."（标记已解决——在 commit a1b2c3d 中处理了。）
- "I disagree with this **suggestion** — the current approach is more performant. Happy to discuss further."（我不太同意这个建议——当前方案性能更好。可以进一步讨论。）

**Code Owner 机制：**

```
# CODEOWNERS file example
/src/api/     @api-team
/src/frontend/ @frontend-team
/docs/        @doc-team
```

- "The PR modifies `src/api/`, so it needs **approval** from the **code owner** — the API team."（这个 PR 改了 `src/api/`，需要代码所有者——API 团队——批准。）

### 常见误用与混淆

| 容易混淆的词 | 区别 |
|-------------|------|
| **comment vs suggestion** | Comment 是泛泛的意见或问题，Suggestion 是附带具体代码的建议。在 GitHub 上，suggestion 有专门的按钮可以一键应用。 |
| **approve vs LGTM** | Approve 是平台上的正式操作（状态变为 Approved），LGTM 是评论里的口语表达。通常先评论 LGTM 再点 Approve。 |
| **nit vs blocking** | Nit 是无关紧要的小问题（不改也行），Blocking 是必须修的严重问题。分清两者能避免审查效率低下。 |
| **changes requested vs comment** | Changes Requested 会阻止合并（状态变红），Comment 只是留言不阻止合并。如果只是想提个建议，别误选成 Changes Requested。 |
| **reviewer vs assignee** | Reviewer 是被请求审查代码的人，Assignee 是被指派处理这个 PR 的人（通常是作者自己或接手者）。 |

> 💡 **小贴士：** 给别人写 review comment 时，善用 prefix 来区分严重程度：
> - **[nit]** — 小问题，改不改都行
> - **[suggestion]** — 建议，推荐但不强制
> - **[blocking]** — 必须修改
> - **[question]** — 只是好奇想问一下
>
> 这样作者能快速判断哪些要先改，哪些可以略过，审查效率大大提升。

---

## 本章小结

这一章我们覆盖了开发流程中五个核心环节的词汇：

1. **版本控制**（2.1）：commit、branch、merge、rebase、PR、stash、cherry-pick——这些是你和 Git 打交道时每天都会遇到的词。记住 push ≠ commit，rebase ≠ merge，PR = MR。

2. **测试**（2.2）：unit test、integration test、e2e test 构成了测试金字塔的三个层次。mock 和 stub 别搞混——一个验证行为，一个提供数据。TDD 不是"先写所有测试"，是小步快跑的红绿灯循环。

3. **部署与运维**（2.3）：从 pipeline 到 container 到 orchestrate，这是 DevOps 的核心语言。canary 是渐进放量，blue-green 是全量切换，rollback 是你的救命稻草。

4. **敏捷开发**（2.4）：sprint、backlog、standup、retro——这是你和团队协作的通用语言。story point 衡量复杂度不是工时，velocity 是参考值不是 KPI。

5. **代码审查**（2.5）：LGTM 是最好的消息，changes requested 意味着还要改，nit 不用太在意但最好还是改了。善用 [nit]、[blocking] 等 prefix 让审查更高效。

这些词汇不需要一次性死记硬背。在日常开发中遇到时回来查一查，用着用着就变成你自己的了。下一章，我们会进入更技术性的领域——数据结构与算法词汇。

---

> 📖 **下一章预告：** 第三章——数据结构与算法词汇，从 array 到 BFS/DFS，把面试和日常开发中最常出现的算法术语一网打尽。

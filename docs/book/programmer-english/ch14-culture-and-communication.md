---
sidebar_position: 14
---

# 第十四章：外企文化与沟通习惯

> 进入外企，英语只是一张入场券。真正决定你能不能融入团队、能不能被信任、能不能往上走的，是你是否理解并适应了外企的沟通文化。这一章，我们来聊聊那些不会写在员工手册里、但每天都在影响你工作的"潜规则"。

---

## 14.1 直接沟通文化（Be direct but respectful）

很多刚进外企的同学都会有一个感受：老外说话怎么这么直接？

"Your approach won't work here."
"I disagree with this design."
"This is wrong."

第一次听到这些话的时候，心里可能会咯噔一下：他是不是对我有意见？我是不是做错了什么？

其实不是。在外企文化里，**直接（direct）是一种美德，不是冒犯**。

### 什么叫 Direct？

Direct 的核心是：**对事不对人**。我说你的方案有问题，不代表我对你这个人有意见。我直接指出问题，是因为这样可以最快地解决问题。

对比一下两种文化下的表达：

| 场景 | 间接文化（常见于亚洲职场） | 直接文化（外企常见） |
|------|--------------------------|---------------------|
| 方案有问题 | "这个方案……可能还需要再考虑一下，你觉得呢？" | "This approach has a problem — it doesn't handle the null case." |
| 不同意观点 | "嗯，你说得也有道理，不过我们也可以看看……" | "I disagree. Here's why..." |
| 工作没做好 | （私下委婉提醒） | "This needs to be redone. The logic is flawed." |
| 拒绝请求 | "我尽量吧……"（最后没做到） | "I can't do this by Friday. The earliest I can deliver is next Tuesday." |

### 如何在不冒犯的前提下直说？

直接不等于粗鲁。外企的直接有一个重要前提：**respectful**。以下是几个原则：

**1. 用 "I" statements，不用 "You" statements**

- ❌ "You made a mistake here."
- ✅ "I think there's an issue with this logic."

用 "I think" / "I noticed" / "I feel" 开头，把观点归到自己身上，而不是指责对方。

**2. 关注行为，不评价人**

- ❌ "You're careless."
- ✅ "This PR has three merge conflicts that need to be resolved."

**3. 给出具体例子，不要泛泛而谈**

- ❌ "Your code quality needs improvement."
- ✅ "In the last three PRs, I noticed the test coverage is below 40%. Let's aim for 80%."

**4. 提供解决方案，不只是指出问题**

- ❌ "This design is bad."
- ✅ "This design won't scale beyond 1000 QPS. What if we use a message queue to decouple the write path?"

### 真实场景：Code Review 中的直接沟通

来看一个真实的 Code Review 评论对比：

**不好的 direct（过于生硬）：**
```
This is wrong. You can't use ArrayList here.
```

**好的 direct（清晰但不冒犯）：**
```
I noticed you're using ArrayList here. Since this code path
is accessed by multiple threads, I'd suggest using
CopyOnWriteArrayList or synchronizing the access. What do
you think?
```

**日常对话示例：**

> **同事 A:** I think we should use Redis for caching.
>
> **你:** I disagree — for this use case, the data size is small enough that local caching with Caffeine would be simpler and faster. We'd avoid the network latency. Want me to write up a quick comparison?

注意这里的结构：先表明态度（I disagree），然后给出理由，最后提出行动建议。这是外企沟通的经典模式：**Opinion → Reason → Action**。

### 适应直接文化的心理建设

- **不要把工作反馈个人化**。同事指出你代码的问题，不是在否定你这个人。
- **学会说 "I don't know"**。在外企，说 "I don't know, but I'll find out" 比含糊其辞更受尊重。
- **有不同意见就说出来**。沉默在外企不会被理解为顺从，而会被理解为没想法或不关心。

---

## 14.2 反馈文化（Give/Receive Feedback）

外企有一套成熟的反馈（feedback）文化。反馈不只是年终考核时的事，而是日常工作的一部分。

### SBI 模型：Situation-Behavior-Impact

外企反馈沟通最常用的框架就是 **SBI 模型**：

- **Situation（情境）**：描述具体的时间、地点、场景
- **Behavior（行为）**：描述你观察到的具体行为
- **Impact（影响）**：说明这个行为带来的影响

关键是：**只描述事实，不评判动机**。

#### 给出正面反馈的例子

> "In yesterday's design review meeting **（Situation）**, you walked through the architecture diagram clearly and addressed everyone's questions patiently **（Behavior）**. That helped the team align on the approach quickly, and we were able to move forward without another round of discussion **（Impact）**."

#### 给出建设性反馈的例子

> "In last week's sprint demo **（Situation）**, the deployment steps you presented hadn't been tested on staging **（Behavior）**. As a result, the demo failed halfway, and the stakeholders left with a confusing impression of our progress **（Impact）**. Next time, could you do a dry run on staging at least an hour before the demo?"

注意这里的结尾加了改进建议，这在外企叫 **"feed-forward"**——不只是回头看，还要往前看。

### 如何接受批评？

对于很多中国程序员来说，接受批评比给批评更难。我们的文化里，被批评往往意味着"丢面子"。但在外企，反馈是成长的工具。

**接受反馈的正确姿势：**

1. **Listen, don't defend.** 先听完，不要急着解释或辩护。
2. **Ask for specifics.** 如果反馈太模糊，追问细节。
3. **Take time to process.** 你可以说 "Thank you for the feedback. Let me think about this and get back to you."
4. **Follow up.** 过一段时间后，主动找对方说 "I've been working on what you mentioned. Have you noticed any improvement?"

**真实对话示例：**

> **Manager:** Hey, I want to share some feedback. In the last couple of standups, I noticed you've been going into too much technical detail. The PM and designers don't need to know the implementation specifics — they just need to know what's done and what's blocked.
>
> **你:** Got it. I'll keep it high-level from now on. Should I share the technical details in a written update instead?
>
> **Manager:** That'd be great. A quick Slack summary after standup works well.

这个对话里，你没有辩解说 "But the technical details are important"，而是接受了反馈，并且主动提出了替代方案。这就是成熟的反馈处理方式。

### 反馈的时机和场合

| 反馈类型 | 建议时机 | 建议场合 |
|---------|---------|---------|
| 正面反馈 | 越快越好 | 公开（团队会议、Slack 频道） |
| 建设性反馈 | 事件发生后 1-2 天内 | 私下（1:1 会议、私聊） |
| 严重问题 | 立即 | 私下，必要时书面记录 |

一个经验法则：**Praise in public, criticize in private.**（公开表扬，私下批评。）

---

## 14.3 会议文化（Agenda/Notes/Action Items）

外企的会议文化有一套相对标准化的流程。不是说每次会议都死板地走流程，而是大家有一个共识：会议是用来做决策的，不是用来聊天的。

### 会前：Agenda 是会议的灵魂

没有 agenda 的会议，在外企几乎等于耍流氓。发会议邀请的时候，你应该在描述里写清楚：

```
Meeting: API Design Review
Date: Aug 12, 2024, 2:00 PM - 3:00 PM
Attendees: @Alice, @Bob, @Charlie

Agenda:
1. Recap the requirements (5 min)
2. Review the proposed API contract (15 min)
3. Discuss error handling strategy (20 min)
4. Align on next steps (10 min)

Pre-read:
- API design doc: [link]
- Please review before the meeting and add comments.

Note: This is a decision-making meeting, not an
information-sharing session. If you just need to be
informed, I'll send notes afterwards and you can
opt out.
```

几个关键点：
- **有明确的目标**：不是 "discuss the API"，而是 "align on next steps"
- **有时间分配**：每个议题标注预计时间
- **有 pre-read 材料**：让大家提前看，会议时间用来讨论，不是用来阅读
- **允许 opt out**：如果你只是需要被通知，可以不参加

### 会中：Notes 和 Decision Tracking

会议进行中，应该有人负责记笔记（notes）。笔记不是记每一句话，而是记录：

- **Key discussion points**：讨论的要点
- **Decisions made**：做出的决定
- **Action items**：行动项
- **Parking lot items**：讨论中冒出来但跟本次会议无关的话题

很多团队用共享文档（Google Docs / Notion / Confluence）实时记录，这样没参会的人也能看到。

**会议记录模板：**

```markdown
# API Design Review - Meeting Notes
Date: Aug 12, 2024

## Attendees
Alice, Bob, Charlie

## Decisions
- API will use cursor-based pagination (not offset-based)
- Error responses will follow RFC 7807 format
- Rate limiting headers will be included in v1

## Action Items
- [ ] Alice: Update the API spec with cursor pagination by Aug 14
- [ ] Bob: Create a PoC for the error handling middleware by Aug 15
- [ ] Charlie: Share the rate limiting design doc by Aug 16

## Parking Lot
- API versioning strategy (to be discussed in a separate meeting)
- Authentication flow (Charlie will set up a meeting)
```

### 会后：Action Items 是闭环的关键

会议结束后 24 小时内，notes 应该发送给所有相关人。更重要的是，**Action Items 必须有 owner 和 deadline**。

一个好的 action item 格式：

> `[ ] @Alice: Update the API spec with cursor pagination by Aug 14`

三个要素缺一不可：
- **Who**：谁负责
- **What**：做什么
- **When**：什么时候完成

下一次会议的开始，应该先 review 上次的 action items——哪些完成了，哪些还没完成，有没有 blocked 的。这就形成了一个闭环。

### 常见会议类型和你的角色

| 会议类型 | 目的 | 你的角色 |
|---------|------|---------|
| Standup / Daily | 同步进度，发现阻塞 | 简短汇报：做了什么、要做什么、有没有 blocked |
| Sprint Planning | 确认本迭代要做的任务 | 评估工作量，认领任务 |
| Design Review | 审查技术方案 | 提出问题、建议改进 |
| Retrospective | 回顾和改进流程 | 诚实反馈，提出改进建议 |
| 1:1 with Manager | 个人发展和沟通 | 主动准备话题，不只是等 manager 说 |

---

## 14.4 异步沟通文化（文档优先 / 时区协作）

外企——尤其是跨时区的全球团队——非常依赖**异步沟通（asynchronous communication）**。这不仅仅是一种工作方式，更是一种文化。

### 为什么外企爱写文档？

你可能会觉得外企的人特别爱写文档：设计文档、决策文档、post-mortem 文档……什么都要写下来。原因有三个：

**1. 时区差异使得同步沟通成本高**

当你的同事在硅谷、你在北京，能重叠的工作时间可能只有 2-3 小时。如果每个问题都要开会，一天开不了几个会。所以大部分沟通必须通过文档和消息完成。

**2. 文档比对话更高效**

一个写得好的 design doc，可以一次性让 10 个人了解你的方案并提出意见。而如果通过开会，你可能要开 10 次会才能传达同样的信息。

**3. 文档是组织记忆**

人会离开，但文档会留下。当一个新人加入团队时，一份好的文档可以让他快速了解系统的来龙去脉，而不需要去问每一个人。

### Async First 原则

**Async First** 的意思是：**默认用异步方式沟通，只有在异步无法解决问题时才使用同步沟通（会议、电话）。**

判断该用同步还是异步的简单规则：

| 情况 | 推荐方式 |
|------|---------|
| 需要讨论复杂的设计方案 | 写 design doc → 异步收集意见 → 必要时开会讨论分歧点 |
| 简单的代码问题 | Slack/Teams 消息 |
| 需要实时 debug 一个问题 | 语音/视频通话 |
| 项目进度更新 | 写周报/邮件 |
| 需要做决策且有多个利益方 | RFC 文档 + 异步评论 |
| 紧急线上事故 | 电话 + 战时频道（Slack incident channel） |

### 异步沟通的最佳实践

**1. 消息要自包含（self-contained）**

不要发这样的消息：
> "Hey, can we chat?"

而要发：
> "Hey, I'm working on the payment service migration. I noticed the current implementation doesn't handle webhook retries. I'm thinking of adding a retry queue with exponential backoff. Do you have 15 min this week to discuss? Alternatively, I can write up a short doc and you can comment async."

第一条消息让人不知道你要干嘛，只能回 "Sure, what's up?"，来回好几轮。第二条消息把背景、问题、建议方案和可选的沟通方式都说清楚了，对方可以直接回复。

**2. 给出明确的截止时间和期望**

> "I need your review on this PR by EOD Wednesday. If I don't hear back by then, I'll go ahead and merge it since we need to ship by Thursday."

**3. 善用 @mention 和 threading**

- 在 Slack/Teams 中，用 thread 而不是在 channel 里零散回复
- @mention 具体的人，而不是 @here 或 @channel（除非真的很紧急）
- 在文档中用 @comment 功能直接评论某段内容

**4. 跨时区协作的技巧**

如果你在北京，同事在硅谷：
- 你上午发消息/文档，对方晚上（他们的上午）回
- 把需要对方输入的任务排在你的下午（他们的晚上），这样你第二天早上来就能看到回复
- 记录对方的时区和工作时间，避免在对方的深夜发消息

**邮件示例——跨时区项目协作：**

```
Subject: [Migration Project] Status Update - Week 3

Hi team,

Quick update on the payment service migration:

✅ Done this week:
- Migrated 3 out of 5 endpoints to the new service
- Set up monitoring dashboards (link)

🔄 In progress:
- Working on the webhook retry logic (ETA: Wednesday)
- Need review on the database migration script (PR #234)

⏳ Blocked:
- Waiting on infra team to provision the new Redis cluster
  - @Bob, could you check on this? I need it by Thursday to
    stay on track for the Friday cutoff.

📅 Next week:
- Start integration testing with the frontend team
- Draft the rollback plan

Doc: [link]
Dashboard: [link]

Let me know if you have questions. I'm online 9 AM - 6 PM
Beijing time, but I'll respond to async comments within
a few hours.

Best,
[Your Name]
```

---

## 14.5 职场政治与边界感（Office Politics & Boundaries）

是的，外企也有职场政治。只是方式不同。

### 外企的"政治"长什么样？

外企的职场政治通常不是那种"请领导吃饭"、"站队"的类型，而更多体现在：

- **影响力（Influence）**：在跨团队协作中，谁说的话更有分量
- **可见度（Visibility）**：你的工作成果是否被决策者看到
- **关系网（Network）**：你跟其他团队的关系如何，是否容易推动事情
- **领地意识（Turf）**：某些团队对自己的领域有强烈的保护意识

### 如何保持专业，避免踩坑？

**1. 对事不对人，但有策略地"对事"**

当你需要推动一个跨团队的改动时，不要直接说 "Your team's service is broken"。而是：

> "I noticed the user service returns inconsistent data when called concurrently. This is causing issues in our checkout flow. I've documented the repro steps here: [link]. Would your team like to fix it, or should we submit a PR?"

**2. 不要绕过你的 manager**

如果你对工作有不满，或者想转组，**先跟你的 manager 沟通**。在外企，直接越级沟通是大忌。如果跟 manager 沟通后问题没有解决，可以找 HRBP 或 skip-level manager（你 manager 的 manager）。

**3. 注意书面记录的边界**

- 在 Slack/邮件中，**不要**说同事或领导的坏话
- 在 performance review 中，用事实和数据说话，不要用情绪化语言
- 如果有冲突，保留相关的聊天记录和邮件作为证据

**4. 保持专业边界**

外企对职场关系的边界感比较强。一些建议：

- **社交距离**：下班后不一定需要跟同事社交。如果不想参加 happy hour，可以礼貌拒绝："Thanks for the invite! I have a personal commitment tonight, but maybe next time."
- **话题边界**：避免在工作中讨论政治、宗教、薪资等敏感话题。外企对 diversity & inclusion 很看重，不当言论可能直接被 HR 约谈。
- **工作与生活平衡**：除非紧急情况，不要在下班后和周末发工作消息。如果需要跨时区发，用 scheduled send 功能。

**5. 处理冲突的正确方式**

当你跟同事有分歧时：

```
Step 1: 1:1 私下沟通，了解对方视角
Step 2: 如果无法达成一致，各自写一段简短的 position doc
Step 3: 如果仍然无法解决，升级到双方 manager
Step 4: 在 manager 层面做决策，并接受决策结果
```

**真实场景：跨团队推不动怎么办？**

> 你需要 Payment 团队修改一个接口，但对方一直说没排期。
>
> **错误做法**：在群里抱怨 "Payment team is so slow"，或直接找对方 VP。
>
> **正确做法**：
> 1. 先跟对方的 tech lead 1:1 沟通，了解他们的优先级和困难
> 2. 写一个简短的 doc，说明这个改动对业务的影响（包括数据）
> 3. 如果对方仍然无法排期，跟自己的 manager 沟通，让 manager 层面去协调
> 4. 如果影响到项目交付，在项目周报中如实记录 "Blocked by Payment team — pending resource allocation"

---

## 14.6 常见职场缩略语与黑话速查表

外企日常沟通中充斥着各种缩略语和"黑话"。刚进去的时候，可能会觉得自己在看密码本。下面是一份完整的速查表，帮你快速上手。

### 核心缩略语速查表

| 缩略语 | 全称 | 含义 | 使用场景示例 |
|--------|------|------|-------------|
| **TL;DR** | Too Long; Didn't Read | 太长不看 / 摘要 | "TL;DR: We need to migrate to the new API by end of Q3." |
| **ASAP** | As Soon As Possible | 尽快 | "Can you review this PR ASAP? It's blocking the release." |
| **EOD** | End Of Day | 今天下班前 | "I'll send the report by EOD." |
| **COB** | Close Of Business | 工作日结束时间 | "Please submit your timesheet by COB Friday." |
| **OOO** | Out Of Office | 不在办公室 / 休假 | "I'll be OOO from Aug 12-15. Contact @Bob for urgent issues." |
| **AFAIK** | As Far As I Know | 据我所知 | "AFAIK, the API is still in beta." |
| **IANAL** | I Am Not A Lawyer | 我不是律师（免责声明） | "IANAL, but I think this might have licensing implications." |
| **HTH** | Hope This Helps | 希望这有帮助 | "You need to add the auth header. HTH!" |
| **IMO** | In My Opinion | 在我看来 | "IMO, we should use Kafka instead of RabbitMQ." |
| **IMHO** | In My Humble Opinion | 在我 humble 的看来 | "IMHO, the current design is over-engineered." |
| **BRB** | Be Right Back | 马上回来 | "BRB, grabbing coffee." |
| **FYI** | For Your Information | 供你参考 | "FYI, the deploy is scheduled for 3 PM." |
| **BTW** | By The Way | 顺便说一下 | "BTW, the docs have been updated." |
| **TBA** | To Be Announced | 待定 / 待通知 | "The date for the hackathon is TBA." |
| **TBD** | To Be Determined | 待确定 | "Speakers and schedule TBD." |
| **NRN** | No Reply Needed | 不用回复 | "Updated the wiki with the new process. NRN." |
| **WIP** | Work In Progress | 进行中 | "WIP: API design doc, feedback welcome." |
| **LGTM** | Looks Good To Me | 看起来不错（常用于 PR review） | "LGTM 🚀" |
| **SGTM** | Sounds Good To Me | 听起来不错 | "SGTM, let's go with that approach." |
| **NPM** | Not Project Management（或 Node Package Manager） | 视上下文 | 搞清楚语境再判断 |
| **FFS** | For F***'s Sake | 表示沮丧（慎用） | "FFS, the build broke again." |
| **DAFUQ** | What the f*** | 表示困惑（慎用） | "DAFUQ is this error?" |
| **PTO** | Paid Time Off | 带薪休假 | "I'm taking PTO next Monday." |
| **WFH** | Work From Home | 在家办公 | "I'll be WFH tomorrow." |
| **ICYMI** | In Case You Missed It | 以防你错过了 | "ICYMI, the recording from yesterday's all-hands is up." |
| **WDYT** | What Do You Think? | 你觉得呢？ | "I proposed using gRPC. WDYT?" |
| **DM** | Direct Message | 私信 | "DM me if you have questions." |
| **FYA** | For Your Action | 需要你处理 | "Forwarding this FYA." |
| **SPOC** | Single Point Of Contact | 唯一联系人 | "Alice is the SPOC for this project." |
| **ROI** | Return On Investment | 投资回报率 | "The ROI of this migration is questionable." |
| **KPI** | Key Performance Indicator | 关键绩效指标 | "Our KPI this quarter is to reduce p99 latency." |
| **OKR** | Objectives and Key Results | 目标与关键结果 | "This aligns with our Q3 OKR." |
| **ETA** | Estimated Time of Arrival | 预计完成时间 | "What's the ETA for the fix?" |
| **PR** | Pull Request | 代码审查请求 | "I opened a PR for the login fix." |
| **RFC** | Request For Comments | 征求意见文档 | "I wrote an RFC for the new caching strategy." |
| **POC** | Proof Of Concept | 概念验证 | "Let's do a quick POC before committing." |
| **MVP** | Minimum Viable Product | 最小可行产品 | "Let's ship the MVP first and iterate." |
| **PO** | Product Owner | 产品负责人 | "Check with PO on the priority." |
| **PM** | Project/Product Manager | 项目/产品经理 | "The PM wants this feature by next sprint." |
| **PE** | Production Engineering / Platform Engineering | 平台工程团队 | "PE needs to review the infra changes." |
| **DSU** | Daily Stand-Up | 每日站会 | "See you at DSU at 10 AM." |
| **1:1** | One-on-One (meeting) | 一对一会议 | "Let's discuss this in our 1:1." |
| **AOB** | Any Other Business | 其他事项 | "AOB? No? Great, let's wrap up." |
| **ELI5** | Explain Like I'm 5 | 用最简单的话解释 | "Can you ELI5 the consensus algorithm?" |
| **NSFW** | Not Safe For Work | 工作场合不宜 | （别点就对了） |
| **TYIA** | Thank You In Advance | 先谢了 | "TYIA for your feedback." |

### 常见"黑话"短语

| 短语 | 实际含义 | 例子 |
|------|---------|------|
| **Let's take this offline** | 这个不在会议上讨论了，会后聊 | "This is getting into details — let's take this offline." |
| **I hear you** | 我理解你的意思（但不一定同意） | "I hear you, but we need to consider the timeline." |
| **Just circling back** | 我来跟进一下之前的事 | "Just circling back on the PR review — any update?" |
|**Going forward** | 以后 / 从现在开始 | "Going forward, please add test cases to every PR." |
| **Low-hanging fruit** | 容易实现的成果 | "Let's focus on the low-hanging fruit first." |
| **Boil the ocean** | 试图做太多 / 不切实际 | "We don't need to boil the ocean — let's start with one service." |
| **Move the needle** | 产生显著影响 | "This optimization won't move the needle on performance." |
| **Herding cats** | 协调很多人很难 | "Getting all teams aligned is like herding cats." |
| **Ducks in a row** | 准备就绪 | "Let's get our ducks in a row before the launch." |
| **Table this** | 美式英语：搁置；英式英语：放上议程讨论 | 注意区分！美企里 "Let's table this" = 暂时不讨论了 |
| **Punt** | 推迟到以后 | "Let's punt this to next sprint." |
| **Socialize** | 在团队中传播讨论 | "Let me socialize this idea with the infra team first." |
| **Bandwidth** | 时间和精力 | "I don't have the bandwidth to take this on right now." |
| **Ramp up** | 学习和上手 | "It takes about 2 weeks to ramp up on this codebase." |
| **Silo** | 信息孤岛 | "We need to break down the silos between frontend and backend." |
| **Stakeholder** | 利益相关方 | "Let's align with all stakeholders before making the change." |
| **Unblock** | 消除阻塞 | "Can you review this PR to unblock the release?" |
| **Double-click** | 深入讨论 | "Let's double-click on the authentication flow." |
| **Action item** | 待办事项 | "The action item from this meeting is to update the docs." |

### 如何快速适应？

1. **建一个 personal glossary**：遇到不懂的缩略语就记下来，攒一周就熟了
2. **不要不好意思问**：有人说 "Let's circle back on this AOB"，你完全可以问 "Sorry, what does AOB stand for?"——没有人会觉得你无知
3. **注意场合使用**：在正式邮件和客户沟通中，少用缩略语；在 Slack 内部沟通中可以随意一些
4. **慎用带脏字的缩略语**：FFS、DAFUQ 等在正式场合绝对不要用，即使是 Slack 也看团队文化

---

## 本章小结

进入外企工作，英语是基础，文化是关键。本章覆盖了外企沟通文化的几个核心方面：

1. **直接沟通**：对事不对人，用 "I" statements，给出具体例子和解决方案。直接是一种效率，不是冒犯。

2. **反馈文化**：掌握 SBI 模型给出反馈，学会接受批评并 follow up。记住：praise in public, criticize in private。

3. **会议文化**：会前有 agenda，会中有 notes，会后有 action items。每个 action item 必须有 owner 和 deadline。

4. **异步沟通**：Async first，文档优先。消息要自包含，给出明确期望和截止时间。善用文档替代会议。

5. **职场边界**：保持专业，对事不对人，不要越级沟通，注意书面记录的边界，尊重 work-life balance。

6. **缩略语与黑话**：日常沟通中大量使用缩略语，遇到不懂就问，攒几周就熟了。注意区分正式和非正式场合。

最后想说一句：**融入一种文化不需要放弃自己的文化**。你不需要变成一个 "banana"（黄皮白心）才能在外企生存。你需要的是理解规则、适应规则，然后在规则之内做最好的自己。

沟通的本质是让别人理解你、也让你理解别人。不管用什么语言，真诚和专业永远是最好的通行证。

---

> 📖 下一章：我们将讨论技术写作（Technical Writing），包括如何写好 design doc、RFC、post-mortem 等外企常见的技术文档。

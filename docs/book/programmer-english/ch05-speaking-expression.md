---
sidebar_position: 5
---

# 第五章：口语表达

> "Speaking is the hardest part of learning a language — not because the words are difficult, but because the silence before you speak is."
>
> 说话是学语言最难的部分——不是因为词汇有多难，而是因为开口前的那段沉默。

写过代码、读过文档、发过邮件，但你坐在会议室里，轮到你发言的那一刻，大脑突然一片空白——这是很多程序员的真实写照。

口语表达和书面表达最大的区别在于：**你没有时间反复斟酌**。你需要在几秒钟内组织语言、传达意思、还要注意语气和礼貌。好消息是，职场口语有一套高频使用的模式，一旦掌握这些模板和句式，你就能在大多数场景下应对自如。

本章覆盖了你日常工作中最常遇到的口语场景：standup 汇报、技术方案陈述、会议讨论、代码审查、与非技术同事沟通、small talk 闲聊，以及线上会议技巧。每个场景都给出大量可以直接套用的英文句式，照着练，很快就能用起来。

---

## 5.1 日常 Standup 发言模板

Standup（每日站会）是敏捷开发中最常见的仪式。通常每人 1-2 分钟，回答三个问题：

1. **Yesterday** — 昨天做了什么？
2. **Today** — 今天打算做什么？
3. **Blockers** — 有什么阻碍？

看起来简单，但很多人一紧张就说得太长、太散、或者漏掉关键信息。下面给你一套三段式模板，照着说就行。

### 5.1.1 标准模板

**Yesterday（昨天做了什么）**

```
Yesterday I worked on [task]. I [specific progress/update].
```

例句：

- Yesterday I worked on the login page redesign. I finished the UI components and wrote unit tests for the form validation.
- Yesterday I spent most of my time debugging the payment gateway issue. I found the root cause — it was a misconfigured webhook URL.
- Yesterday I worked on the API migration. I completed about 80% of the endpoint refactoring.

**Today（今天打算做什么）**

```
Today I'm planning to [task], and hopefully [next step].
```

例句：

- Today I'm planning to finish the remaining endpoints, and hopefully start working on the integration tests.
- Today I'll be working on the dashboard performance optimization. I want to get the initial load time under 2 seconds.
- Today I'm going to review the PRs from the team and then continue with the database schema migration.

**Blockers（有什么阻碍）**

```
I'm currently blocked by [issue]. / I don't have any blockers today.
```

例句：

- I'm currently blocked by the staging environment being down. I've reached out to DevOps and hopefully it'll be resolved soon.
- I'm blocked on the design review — I need sign-off from Sarah before I can proceed.
- No blockers today. Everything's going smoothly.

### 5.1.2 完整发言示例

**示例 1：顺利的一天**

> Yesterday I worked on the user profile feature. I finished the backend API and wrote the integration tests. Today I'm planning to work on the frontend integration and hopefully get the feature ready for QA by end of day. No blockers today.

**示例 2：遇到阻碍**

> Yesterday I was supposed to work on the search optimization, but I got pulled into a critical production issue. I spent most of the day investigating and fixing a memory leak in the order service. Today I'm going to circle back to the search optimization. I'm currently blocked by the fact that I need access to the Elasticsearch cluster, which I don't have yet. I've asked IT for access.

**示例 3：协作场景**

> Yesterday I paired with Alex on the authentication refactoring. We managed to decouple the OAuth logic from the main controller. Today I'll be cleaning up the tests and Alex will handle the documentation. No blockers, but I might need a quick sync with the team about the token expiration strategy.

### 5.1.3 变体与灵活表达

不一定每次都说 "Yesterday I worked on..."，可以换换花样：

| 场景 | 替代表达 |
|------|----------|
| 强调完成 | I managed to wrap up the ticket for... |
| 强调进展 | I made good progress on... |
| 强调遇到问题 | I ran into an issue with... |
| 强调切换任务 | I pivoted to... / I got pulled into... |
| 强调协作 | I paired with... / I synced up with... |
| 今天计划 | I'll be focusing on... / My main priority today is... |
| 无阻碍 | All clear on my end. / Nothing blocking me. |
| 有阻碍 | I'm waiting on... / I need a hand with... |

### 5.1.4 Standup 小贴士

- **简洁是王道**：standup 不是详细汇报，1-2 分钟足够。说重点，细节留到会后。
- **说进展，不说流水账**：不要 "first I opened my IDE, then I created a file..."，而是 "I completed the API endpoint and wrote tests."
- **主动提阻碍**：不要等到被问。如果有 blocker，主动说出来，这是 standup 的核心价值。
- **提前准备**：开会前花 30 秒想好要说什么，比临场组织语言效果好十倍。

---

## 5.2 技术方案陈述与汇报

在团队中，你经常需要向同事或领导陈述一个技术方案——可能是一个新功能的架构设计，也可能是一次技术迁移的方案。这类陈述的关键是**结构清晰、重点突出、有理有据**。

### 5.2.1 四段式陈述框架

一个好的技术方案陈述通常包含四个部分：

1. **Background（背景）** — 为什么要做这件事？
2. **Proposal（方案）** — 我打算怎么做？
3. **Trade-offs（取舍）** — 有什么优缺点？为什么选这个方案？
4. **Plan（计划）** — 接下来的步骤是什么？

### 5.2.2 背景陈述

先说清楚为什么要做这件事，让大家有上下文。

```
The reason we need to do this is [problem/motivation].
Currently, [现状描述], which causes [影响].
```

例句：

- The reason we need to do this is that our current caching strategy doesn't handle cache invalidation properly, which leads to stale data being served to users.
- We've been seeing increased latency in our search API over the past few weeks. The average response time has gone from 200ms to 800ms, and it's starting to affect user experience.
- As part of our effort to move to microservices, we need to decouple the notification service from the main monolith.

其他常用开头：

- Let me give some context first...
- To set the stage...
- Here's the situation we're dealing with...
- The driving force behind this is...

### 5.2.3 方案陈述

说清楚你打算怎么做，适当使用技术细节，但不要深入到代码级别。

```
My proposal is to [high-level approach].
Specifically, we would [key implementation details].
```

例句：

- My proposal is to introduce a Redis-based caching layer between our API and the database. Specifically, we would cache the most frequently accessed user data with a TTL of 5 minutes, and use cache-aside pattern for the rest.
- What I'd suggest is migrating from REST to GraphQL for the mobile API. This would let the mobile team fetch exactly the data they need in a single request, reducing the number of round trips.
- The approach I'm recommending is to use event sourcing for the order service. We'd store all state changes as events in Kafka, and project them into read models.

其他常用表达：

- I'd like to propose... / What I'm proposing is...
- The idea is to... / The plan would be to...
- We could go with... / One option is to...

### 5.2.4 取舍讨论

这是最体现工程师素养的部分。不要只说优点，也要说缺点，并解释为什么你仍然推荐这个方案。

```
The main advantage of this approach is [benefit].
The downside is [drawback], but I think it's acceptable because [reasoning].
I also considered [alternative], but it [why not chosen].
```

例句：

- The main advantage of this approach is that it significantly reduces database load. The downside is that we need to manage a Redis cluster, which adds some operational complexity. But I think it's worth it because the performance gain is substantial. I also considered using in-memory caching, but that wouldn't work well with our multi-instance setup.
- The advantage of GraphQL is fewer API calls and better type safety. The trade-off is a steeper learning curve for the team and some complexity in the gateway layer. I looked at using BFF (Backend for Frontend) pattern instead, but that would require more development time than we have right now.

常用取舍表达：

- On the plus side... / On the downside...
- The benefit is... / The cost is...
- It comes at the expense of...
- We'd be trading X for Y.
- I weighed this against [alternative], and...

### 5.2.5 计划说明

最后说清楚接下来的步骤和时间线。

```
If everyone's on board, the next steps would be:
First, [step 1]. Then, [step 2]. And finally, [step 3].
I estimate this will take about [time].
```

例句：

- If everyone's on board, the next steps would be: first, I'll write a tech design doc and circulate it for review. Then, I'll start with a proof-of-concept on the caching layer. And finally, we'll roll it out incrementally to production. I estimate this will take about two sprints.
- The plan is to start with a spike to validate the approach, then move into implementation. I'm thinking about 3 weeks for the core work, plus another week for testing and deployment.

### 5.2.6 完整示例

> Let me give some context first. Over the past month, we've seen a significant increase in 500 errors from our payment service. After investigation, we found that about 30% of these are caused by timeout issues when calling the third-party payment gateway.
>
> My proposal is to implement a circuit breaker pattern using Resilience4j. Specifically, we'd wrap the payment gateway calls with a circuit breaker that trips after 5 consecutive failures, with a 30-second reset timeout. We'd also add a fallback mechanism that queues failed payments for retry.
>
> The main advantage is that it prevents cascading failures and improves overall system resilience. The downside is that during a circuit-open state, some payment requests will be immediately rejected, which means a degraded user experience for a short period. But I think this is better than the current situation where the entire service becomes unresponsive. I also considered just increasing the timeout, but that would only mask the problem without solving it.
>
> If everyone's on board, the next steps would be: first, I'll add the circuit breaker to the payment service. Then, I'll set up monitoring and alerting around it. I estimate this will take about 3-4 days of work.

---

## 5.3 会议讨论与提问句式

在会议中，你需要表达同意、反对、补充、追问、澄清——而且要做到礼貌得体。这可能是程序员最头疼的口语场景之一。

### 5.3.1 礼貌打断

在会议中打断别人需要技巧，要既不打断对方思路，又能适时插入自己的观点。

| 场景 | 英文表达 |
|------|----------|
| 想插话 | Sorry to interrupt, but I'd like to add something quickly. |
| 想提问 | Can I jump in with a quick question? |
| 想补充 | If I could just add to that point... |
| 想澄清 | Sorry, could I clarify something before we move on? |
| 想拉回话题 | I want to bring us back to [topic] for a second. |

### 5.3.2 追问与深入

当别人说了一个观点或方案，你想了解更多细节时：

- Could you elaborate on that? / Could you go into a bit more detail?
- What do you mean by [term]? I want to make sure I understand correctly.
- Can you give an example of what that would look like?
- How does that compare to [alternative approach]?
- What's the timeline you're thinking for this?
- Have we considered the impact on [area/team]?
- What would happen if [edge case scenario]?

### 5.3.3 表示同意

不只是说 "I agree"，可以表达得更丰富：

- I completely agree with that. / I'm on the same page.
- That's a great point. I hadn't thought about it that way.
- That makes a lot of sense. / That resonates with me.
- I second that. / +1 to that. （非正式）
- I was just about to say the same thing.
- You took the words right out of my mouth. （比较口语化）

### 5.3.4 表示反对

反对别人时要「对事不对人」，先肯定再表达不同意见：

- I see where you're coming from, but I have a slightly different take on this.
- I understand the reasoning, but I'm not sure I agree with [specific point].
- That's a valid point. However, I think we should also consider [alternative].
- I hear what you're saying, but my concern is [specific concern].
- I'm not entirely convinced that [assumption] is the case here.
- With all due respect, I think there might be a gap in [specific area].

**注意**：避免直接说 "You're wrong" 或 "That's a bad idea"。用 "I'm not sure I agree" 或 "I have a different perspective" 来代替。

### 5.3.5 补充观点

在别人观点的基础上添加自己的想法：

- Building on what [name] said, I'd also add that...
- To add to that point, we should also think about...
- That's a great point, and it reminds me of [related topic].
- I'd like to piggyback on that and mention...
- Along those same lines, [related observation].

### 5.3.6 澄清与确认理解

确保你和对方在同一个频道上：

- Let me make sure I understand — you're saying that [restate their point]?
- So if I'm hearing you correctly, the main concern is [concern]?
- Just to clarify, are you suggesting that we [specific action]?
- I want to make sure we're aligned on this. You're proposing [proposal], right?
- Let me play that back to you — [rephrase what they said]. Is that accurate?

### 5.3.7 总结与推进

当你觉得讨论差不多了，需要总结并推进：

- It sounds like we're generally aligned on [decision]. Should we move forward with that?
- To summarize what we've discussed: [point 1], [point 2], and [point 3]. Does that capture everything?
- I think we've covered the main points. Should we table the rest for the next meeting?
- Let's take this offline and continue the discussion in [Slack/document].
- I think we have enough to make a decision. Does anyone have concerns before we move forward?

---

## 5.4 代码审查中的口语表达

代码审查（Code Review / PR Review）不只是在线上留评论。很多时候你会在语音会议、pair programming 或者 screen sharing 中口头讨论代码。这时候你需要用英文描述代码问题、给出建议、回应反馈。

### 5.4.1 指出问题

指出问题时，先说是什么问题，再说为什么是问题，最后给建议：

```
I noticed that [issue]. This could be a problem because [reason].
Maybe we could [suggestion] instead?
```

例句：

- I noticed that this function is doing both validation and data transformation. This could make it harder to test and maintain. Maybe we could split it into two separate functions?
- I see that the error handling here is catching all exceptions. This might hide bugs that should be surfaced. Would it make sense to catch specific exceptions instead?
- I noticed there's no rate limiting on this endpoint. This could be a security risk if someone tries to DoS it. Should we add a rate limiter?

其他常用表达：

- One thing I'd point out is...
- I have a minor concern about...
- This looks good, but I'm wondering if we should...
- I'm not sure about this approach. Have you considered...?
- This might cause issues when [scenario].

### 5.4.2 给出建议

给建议时，用建议性语气而非命令式：

| 语气 | 表达 |
|------|------|
| 强建议 | I'd strongly recommend that we... / It's critical that... |
| 一般建议 | I think it would be better if... / We should probably... |
| 温和建议 | Maybe we could... / Would it make sense to...? |
| 可选建议 | It's up to you, but you might want to consider... |
| 风格建议 | This is more of a style preference, but... |

例句：

- I'd strongly recommend that we add integration tests here. Without them, we won't catch regressions when the API changes.
- I think it would be better if we extract this logic into a helper function. It's duplicated in a few places.
- Maybe we could use a builder pattern here? It would make the API more fluent.
- This is more of a style preference, but I usually prefer early returns over nested if-else. It makes the code easier to follow.

### 5.4.3 回应反馈

当别人审查你的代码并给出反馈时：

**同意并感谢：**

- Good catch! I'll fix that.
- That's a great point. I didn't think of that.
- Thanks for catching that. I'll update it.
- You're right, that's a bug. Let me fix it.
- Fair point. I'll refactor that.

**解释原因：**

- That's a fair question. The reason I did it this way is because [reason].
- I considered that, but I went with this approach because [reason].
- Good point. I originally had it that way, but [what changed].
- That's a valid concern. In this case, [explanation].

**礼貌不同意：**

- I see your point, but I think this is fine because [reason].
- I understand the concern, but in this specific case, [explanation].
- I hear you, but I'd prefer to keep it as is for [reason]. Happy to discuss further if you'd like.
- That's a good suggestion, but I think it might be overkill for this use case.

### 5.4.4 PR 审查口语场景模拟

**场景：Pair review，两人一起看代码**

> **A:** Let's start with the main changes. I see you've refactored the user service. Can you walk me through the changes?
>
> **B:** Sure. So the main thing I did was extract the notification logic into a separate service. Previously, the user service was directly calling the email and SMS providers, which made it tightly coupled.
>
> **A:** That makes sense. I noticed you're using an event bus here. Was there a reason you went with that instead of just calling the notification service directly?
>
> **B:** Good question. I wanted to decouple it so that if the notification service is down, the user service doesn't fail. The event bus lets us retry asynchronously.
>
> **A:** That's a solid approach. One thing I'd point out — I see the event handler doesn't have any error handling. If the notification fails, the event would be lost. Maybe we could add a dead letter queue?
>
> **B:** That's a great point. I'll add that. Should I use the existing SQS dead letter queue or create a new one?
>
> **A:** I think the existing one should be fine for now. Also, I'd recommend adding some logging around the event publishing so we can trace it if something goes wrong.
>
> **B:** Will do. Thanks for the feedback!

---

## 5.5 与非技术同事沟通的简化表达

程序员经常需要和产品经理、设计师、市场人员、甚至客户解释技术问题。这时候你需要**放下专业术语，用简单的英文把事情说清楚**。

### 5.5.1 核心原则

1. **No jargon** — 不用专业术语。如果必须用，先解释。
2. **Use analogies** — 用比喻让技术概念变直观。
3. **Focus on impact** — 关注「这意味着什么」而非「怎么实现的」。
4. **Be honest about uncertainty** — 不确定就说不确定，不要过度承诺。

### 5.5.2 解释技术问题

**不要说：**

> The ORM is generating N+1 queries because of lazy loading in the relationship mapping, which is causing the database connection pool to be exhausted.

**应该说：**

> The system is making too many trips to the database, which slows everything down. It's like going to the grocery store for each item on your list instead of buying everything in one trip. We can fix this by restructuring how the code fetches data.

更多简化表达的例子：

| 技术说法 | 简化说法 |
|----------|----------|
| We have a memory leak in the order service. | The system is gradually using up its memory over time, like a bucket with a small hole. Eventually it'll need to be restarted. |
| We need to refactor the authentication module. | The part of the system that handles login is getting hard to maintain. We need to clean it up before adding new features. |
| The API is returning 500 errors due to a null pointer exception. | The system is crashing when it encounters unexpected data. I'm working on a fix now. |
| We need to migrate from monolith to microservices. | Right now all our features are bundled together in one big system. We want to split them into smaller, independent pieces so teams can work more independently. |
| The CI/CD pipeline is broken. | Our automated deployment system has an issue, so we can't push updates right now. We're working on it. |

### 5.5.3 评估工作量

非技术同事经常问你 "这个要多久？"，你的回答需要既诚实又让人理解：

- That's a relatively straightforward change. I'd estimate about half a day.
- This is a bit more complex than it looks. There are some edge cases we need to handle. I'd say 2-3 days.
- I need to do some investigation first before I can give you a solid estimate. Can I get back to you by end of day?
- The feature itself is doable in a week, but we also need to update the existing systems to work with it, which adds another few days.
- It's hard to give an exact number right now. There are a few unknowns. I'd say somewhere between 3 to 5 days — I'll have a better estimate once I start digging in.

### 5.5.4 解释为什么不能做某事

当需求不合理时，如何用简单的英文说 "no"：

- I understand what you're asking for, but technically that would require a significant rework of the current system. It's not impossible, but it would take much longer than we have.
- That's an interesting idea, but the way our system is built right now, it wouldn't support that. We'd need to redesign that part, which is a bigger project.
- I don't think that's the best approach here. The reason is that it would slow down the app for users. There's a simpler alternative that would achieve the same goal.
- We can definitely do that, but it would mean pushing back the other features we planned for this sprint. Which would you prioritize?

### 5.5.5 与非技术同事沟通的黄金句式

- **In simple terms, what's happening is...** — 用最简单的话解释
- **Think of it like...** — 打比方
- **The bottom line is...** — 说结论
- **What this means for you is...** — 关注对方关心的影响
- **The good news is... / The not-so-good news is...** — 报告好消息和坏消息
- **From a user's perspective, they'll see...** — 从用户角度描述
- **It's like [analogy].** — 用类比
- **To put it in perspective...** — 帮助对方理解规模或影响

---

## 5.6 Small Talk 与职场社交口语

在办公室、茶水间、会议开始前的等待时间，你总不能一直盯着手机。Small talk（闲聊）是职场社交的重要部分，也是很多程序员最不擅长的。

### 5.6.1 周末话题

周五下午或周一早上最常见的话题：

**Friday（周五问别人计划）：**

- Any plans for the weekend?
- Got anything fun lined up for the weekend?
- You doing anything special this weekend?
- Ready for the weekend?

**Monday（周一问周末过得怎样）：**

- How was your weekend?
- Did you do anything interesting over the weekend?
- Good weekend?
- How was your weekend? Did you get to relax?

**回答示例：**

- Not much, just going to take it easy at home. Maybe do some reading.
- I'm going hiking with some friends on Saturday. Should be fun!
- Just the usual — grocery shopping, some laundry, you know, the exciting stuff.
- It was great! I went to that new ramen place downtown. Highly recommend it.
- Pretty chill. Caught up on some sleep and binge-watched a show on Netflix.

### 5.6.2 天气话题

虽然老套，但天气是最安全的闲聊话题：

- It's really nice out today, isn't it?
- Can you believe this weather? It was pouring yesterday.
- It's getting pretty cold lately. Winter's definitely here.
- Looks like it's going to rain later. You might want to bring an umbrella.
- The weather's been amazing this week. Perfect for being outdoors.
- I can't wait for summer. This cold is killing me.

### 5.6.3 运动/爱好话题

- Did you catch the game last night? （如果你知道对方看球赛）
- Are you into any sports? / Do you follow any sports?
- I started getting into rock climbing recently. It's a great workout.
- Do you play any instruments? I've been trying to learn guitar.
- I've been getting into cooking lately. Made a decent pasta last night.
- Are you a reader? Any book recommendations?
- I've been binging on [show name] lately. Have you seen it?

### 5.6.4 旅行话题

- Any travel plans coming up?
- I went to [place] last month. It was incredible.
- Have you ever been to [country/city]? I'm thinking about going.
- I'm planning a trip to Japan in the fall. Any recommendations on places to visit?
- How was your trip to [place]? I saw some photos on Instagram — looked amazing!
- I'm actually heading to [place] next week for a few days. First time there!

### 5.6.5 工作/项目闲聊

有时同事会聊聊工作上的事，但不是正式讨论：

- How's your sprint going?
- Are you busy these days? / You seem pretty swamped.
- What are you working on these days?
- That feature you shipped last week — it's working really well. Nice job!
- I saw your PR for the new dashboard. Looks really clean.
- How's the [project name] coming along?

### 5.6.6 Small Talk 万能句式

当你实在不知道说什么时，记住这几个万能开头：

- **"How's your week been?"** — 最通用的问法
- **"What have you been up to?"** — 适合有一阵没见的同事
- **"Any exciting news?"** — 开放式问题，让对方自由发挥
- **"Did you end up [doing something they mentioned before]?"** — 记住之前对话的内容，非常加分
- **"I meant to ask you — [something related to their expertise]"** — 向对方请教，人们都喜欢被当作专家

### 5.6.7 优雅结束 Small Talk

闲聊也要知道怎么收尾：

- Well, I should get back to it. Have a good one!
- Alright, let me let you get back to work.
- I need to jump on a call. Catch you later!
- Good talking to you. See you in the standup!
- Anyway, I won't keep you. Have a great weekend!

---

## 5.7 线上会议口语技巧

后疫情时代，线上会议（Zoom / Google Meet / Microsoft Teams）已经成为日常工作的一部分。线上会议和线下会议有一个本质区别：**你看不到所有人的表情和肢体语言，沟通效率天然打折扣**。因此，在线上会议中更需要清晰、明确的口语表达。

### 5.7.1 开场与签到

线上会议开始时，通常等大家陆续加入：

- Hi everyone, let's wait a couple of minutes for others to join.
- Looks like we're still missing a couple of people. Let's give them a minute.
- Alright, I think we can get started. Let's not wait any longer.
- Can everyone see my screen? / Can everyone hear me okay?
- Quick sound check — can you hear me? / You're a bit quiet, can you speak up a bit?

### 5.7.2 线上打断与插话

线上打断比线下更难，因为麦克风有延迟，而且你看不到对方的表情变化。技巧是**先用声音信号表示你要说话，然后再说内容**：

- Sorry, can I just jump in here really quickly?
- If I could just interject for a second...
- I have a quick point on that — sorry to interrupt.
- Can I add something here? （先说这句话，等对方停顿后再继续）
- Sorry, I didn't quite catch that last part. Can you repeat it?

**小技巧**：如果有人一直说个不停，你可以在聊天框里打字 "Can I share a quick thought?"，主持人通常会注意到并给你机会发言。

### 5.7.3 补充观点

在线上会议中补充观点，要特别注意标明你在回应谁的话，因为上下文容易丢失：

- Just to build on what Sarah said about the caching strategy...
- I want to go back to what Mike mentioned earlier about the timeline...
- That's a good point, Tom. And I'd add that...
- Just to chime in on the testing discussion — I think we should also consider...

### 5.7.4 线上总结与确认

线上会议更容易出现「说了但没听到、听到了但没理解」的情况，所以总结和确认更加重要：

- Let me just summarize what we've agreed on so far: [point 1], [point 2], and [point 3]. Did I get that right?
- So the action items are: [person] will do [task] by [time], and [person] will do [task] by [time]. Sound good?
- Just to make sure we're all on the same page — we're going with [decision], right?
- I think we've covered the main points. Is there anything else anyone wants to discuss before we wrap up?

### 5.7.5 技术问题应对

线上会议不可避免会遇到技术问题，准备好这些表达可以避免尴尬：

**你的网络不好：**

- Sorry, my internet is acting up. Can you repeat that?
- I think I froze for a second there. What did I miss?
- My connection's a bit unstable. Let me turn off my video to save bandwidth.
- Apologies for the audio issues. Let me try dialing in from my phone.

**别人的网络不好：**

- You're cutting out a bit, [name]. Could you repeat that?
- I think you froze. Can you say that again?
- I didn't catch the last part — your audio dropped for a moment.
- Maybe try turning off your video? That might help with the connection.

**屏幕共享问题：**

- Let me share my screen. Can everyone see it? / Is my screen visible?
- Looks like you're sharing the wrong window — we can't see the document.
- Can you zoom in a bit? The text is too small to read.
- I think you forgot to hit "Share Screen" — we're still seeing the participant grid.

### 5.7.6 结束会议

- I think we're at a good stopping point. Let's continue this in the next meeting.
- We're at time. Thanks everyone for joining!
- Great discussion today. I'll send out the meeting notes and action items after this.
- Anything else before we wrap up? No? Alright, thanks everyone!
- Let's take this offline and continue in Slack. I'll create a thread.

### 5.7.7 线上会议礼仪速查

| 场景 | 建议 |
|------|------|
| 加入会议 | 准时加入，或提前 1-2 分钟 |
| 麦克风 | 不说话时 mute，说话前先 unmute |
| 摄像头 | 有条件就开，至少在发言时开 |
| 发言前 | 先说名字 "This is [name]..." 方便辨认 |
| 多人同时说话 | 主动让出 "Go ahead" / "You first" |
| 屏幕共享 | 提前关掉无关窗口和通知 |
| 聊天框 | 重要链接和备注打在聊天框里 |
| 网络不好 | 关视频、切手机热点、或拨入 |

---

## 本章小结

口语表达是程序员英语中「实战感」最强的部分。你可能书面表达很好，但一到开口就紧张，这很正常——口语是需要练习的肌肉记忆。

本章覆盖了七个核心场景，关键要点回顾：

1. **Standup**：三段式（Yesterday / Today / Blockers），提前准备，简洁明了。记住变体表达，不要每次都说一样的。
2. **技术方案陈述**：四段式（Background / Proposal / Trade-offs / Plan），结构清晰是关键。取舍讨论最能体现你的专业素养。
3. **会议讨论**：学会礼貌打断、追问、同意、反对、补充。反对时先肯定再表达不同意见，「对事不对人」。
4. **代码审查**：指出问题时要给出原因和建议，回应反馈时大方接受合理建议、礼貌表达不同意见。
5. **与非技术同事沟通**：放下术语，用比喻和类比，关注影响而非实现细节。评估工作量时留有余地。
6. **Small talk**：掌握周末、天气、运动、旅行几个核心话题。记住万能开头句式，也要学会优雅收尾。
7. **线上会议**：打断时先发声音信号，总结时标明回应对象，技术问题冷静应对。善用聊天框辅助沟通。

**练习建议**：

- 每天用英文对自己说一遍 standup，哪怕只有 30 秒
- 开会前写下你想说的 2-3 个要点，照着说
- 看英文技术演讲（如 YouTube 上的 conference talks），跟读模仿语调
- 找同事做 language partner，互相用英文做 code review
- 录下自己的发言，回放听一听，找找需要改进的地方

说不好不可怕，不说才可怕。每次开口都是一次练习，每次练习都在进步。加油！🗣️
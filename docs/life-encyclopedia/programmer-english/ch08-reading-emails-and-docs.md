---
sidebar_position: 8
---

# 第八章：英文邮件与文档阅读

> 作为程序员，你每天花在阅读上的时间可能比写代码还多。清晨打开邮箱，十几封英文邮件等着你；下午开会前，要读完一份 20 页的 RFC；线上出故障了，Postmortem 报告得赶紧看；安全团队转发了一个 CVE 公告，问你要不要升级。这些场景有一个共同点：**你不是在休闲阅读，你是在"提取信息"**。这一章，我们来聊聊如何高效地读懂这些英文工作文档。

---

## 8.1 英文工作邮件结构解析

### 8.1.1 一封标准工作邮件长什么样

先看一封典型的工作邮件：

```
Subject: [API Gateway] Deployment scheduled for Friday 2AM PST

Hi team,

This is a heads-up that we'll be deploying the new API Gateway
v2.3.0 to production this Friday (Aug 15) at 2:00 AM PST.

Expected downtime: ~15 minutes.

What's changing:
- New rate limiting module
- Deprecation of /v1/auth endpoint (see migration guide[1])
- Bug fixes (full changelog[2])

If you have any concerns, please reply to this thread before
Thursday EOD.

Thanks,
Sarah Chen
Platform Team | Acme Corp

[1] https://wiki.acme.com/migration-v2
[2] https://github.com/acme/api-gateway/releases/tag/v2.3.0
```

看起来挺长，但其实结构非常固定。拆开来看：

| 部分 | 英文 | 作用 | 阅读优先级 |
|------|------|------|-----------|
| 主题行 | Subject | 一句话告诉你这封邮件讲什么 | ⭐⭐⭐ 最高 |
| 称呼 | Greeting | "Hi team" / "Hi John," 礼貌开头 | ⭐ 速读 |
| 正文 | Body | 核心信息，通常按"背景→变更→影响→行动"展开 | ⭐⭐⭐ 高 |
| 签名 | Sign-off | "Thanks, Sarah" + 职位/部门 | ⭐ 速读 |

**阅读策略：先读 Subject，再扫 Body 的第一段和最后一段，最后看有没有需要你采取行动的句子。** 中间的细节通常是补充说明，需要时再看。

### 8.1.2 主题行（Subject Line）的秘密

主题行是邮件的"标题函数"——它决定了你将以什么优先级处理这封邮件。看几个真实例子：

```
Subject: [URGENT] Production DB connection pool exhausted
Subject: FYI: New Slack workspace policy (effective Sep 1)
Subject: Action required: Please review Q3 OKRs by Friday
Subject: [Incident] Payment service latency spike - resolved
Subject: Heads-up: Office AC maintenance this Saturday
```

注意方括号 `[ ]` 里的标签，这是很多团队约定的邮件分类方式：

| 标签 | 含义 | 你需要做什么 |
|------|------|-------------|
| `[URGENT]` | 紧急 | 立刻看 |
| `[Incident]` | 事故通知 | 关注现状和处理进展 |
| `[FYI]` | 供参考 | 看一眼就行，不需要回复 |
| `[Action required]` | 需要你操作 | 仔细读，按要求执行 |
| `[Heads-up]` | 提前告知 | 知道这件事就好 |

如果主题行里有 **"Action required"** 或 **"Please review by..."**，说明这封邮件需要你动手——这种邮件要优先处理。

### 8.1.3 邮件正文中的常见缩写

英文工作邮件里到处都是缩写，第一次看到很容易懵。下面是最高频的一批：

| 缩写 | 全称 | 中文含义 | 使用场景示例 |
|------|------|---------|-------------|
| FYI | For Your Information | 供你参考 | "FYI, the meeting has been moved to 3 PM." |
| EOD | End of Day | 今天下班前 | "Please send the report by EOD." |
| ASAP | As Soon As Possible | 尽快 | "We need the fix ASAP." |
| OOO | Out of Office | 不在办公室 | "I'll be OOO from Aug 12-15." |
| TBD | To Be Determined | 待定 | "The exact date is TBD." |
| TBA | To Be Announced | 待公布 | "Keynote speaker TBA." |
| CC | Carbon Copy | 抄送 | "CC'ing David for visibility." |
| BCC | Blind Carbon Copy | 密送 | 较少见，通常用于群发通知 |
| ETA | Estimated Time of Arrival | 预计到达时间 | "What's the ETA for the fix?" |
| PTO | Paid Time Off | 带薪休假 | "I'm on PTO next week." |
| NRN | No Reply Needed | 无需回复 | "NRN, just keeping you in the loop." |
| AFAIK | As Far As I Know | 据我所知 | "AFAIK, the API is still in beta." |
| TL;DR | Too Long; Didn't Read | 太长不看/摘要 | "TL;DR: We need to migrate to v2 by October." |
| BR | Best Regards | 问候 | 常见于邮件结尾 |

**一个实用技巧：** 当你看到不认识的缩写，别急着查字典——先看上下文。大多数缩写的意思可以从句子中推断出来。比如 "I'll be OOO from Aug 12-15"，就算你不知道 OOO 是什么，从"from Aug 12-15"也能猜到是"不在"的意思。

### 8.1.4 邮件中的"行动信号"句型

读完一封邮件，最重要的问题是：**这封邮件需要我做什么？** 下面是一些常见的"行动信号"句型，看到它们就要注意了：

- **"Please review..."** — 请审阅，通常附带一个链接或文档
- **"Action required: ..."** — 需要你执行某个操作
- **"Let me know if you have any concerns."** — 如果有异议请提出（没异议就不用回复）
- **"Can you take a look at this?"** — 请你看一下（通常需要你反馈意见）
- **"Could you follow up with...?"** — 请你跟进某件事
- **"Please reply to this thread by..."** — 请在某个时间前回复
- **"I'm looping in @name for..."** — 把某人加入对话（可能需要你配合）

反过来，如果邮件里出现这些句子，说明**你不需要做什么**：

- **"FYI, ..."** — 只是要让你知道
- **"No action needed from your side."** — 你这边不需要操作
- **"Just keeping you in the loop."** — 让你保持知情
- **"NRN"** — 不用回复

### 8.1.5 一个阅读邮件的实用流程

总结一个日常邮件阅读流程，帮你每天省出至少半小时：

1. **扫主题行**（2 秒/封）→ 分类：紧急 / 需操作 / 仅供参考 / 可忽略
2. **紧急邮件** → 立刻打开，读第一段 + 最后一段，找到行动项
3. **需操作邮件** → 标星/标记，安排时间处理
4. **仅供参考** → 速读，有链接的存到 Pocket/Notion 稍后看
5. **可忽略** → 直接归档

记住：**邮件不是聊天，不需要每封都立刻回复。** 很多邮件只是"FYI"，读完归档就好。

---

## 8.2 技术方案文档（RFC/Tech Spec）阅读

### 8.2.1 什么是 RFC

RFC（Request for Comments）是技术团队用来讨论方案的一种文档。它的核心思想是：**在动手写代码之前，先把方案写下来，让团队成员 review，收集意见后再推进。** 这种做法在 Google、Amazon、Meta 等大厂非常普遍。

不同公司对这种文档的叫法不同：

| 叫法 | 全称 | 常见于 |
|------|------|-------|
| RFC | Request for Comments | Rust、Kubernetes 社区、很多初创公司 |
| Tech Spec | Technical Specification | Google、Amazon |
| Design Doc | Design Document | Meta、一般性技术团队 |
| One Pager | 一页纸方案 | Google（简短版方案） |
| ADR | Architecture Decision Record | 架构决策记录，偏重"为什么选这个方案" |

不管叫什么，它们的结构大同小异。

### 8.2.2 RFC 文档的标准结构

一份典型的 RFC 长这样：

```markdown
# RFC: Migrate User Sessions from Redis to DynamoDB

**Author:** Alex Kumar
**Date:** 2025-08-01
**Status:** Draft
**Reviewers:** @sarah, @mike, @jennifer

## Background

Our current session store uses Redis cluster (3 shards, 6 nodes).
As we scale to 50M+ MAU, we're seeing increased memory pressure
and occasional session evictions during peak traffic (Black Friday
2024: ~12K sessions lost).

## Proposal

Migrate session storage from Redis to DynamoDB with the following
design:
- Partition key: user_id
- TTL: 7 days (auto-expiration)
- Consistency: Eventually consistent reads (sessions are rarely
  read immediately after write)

## Alternatives Considered

### Option A: Scale Redis cluster (add 3 more shards)
- Pros: No code changes, minimal migration effort
- Cons: High ongoing cost (~$8K/month additional), doesn't solve
  eviction issue at peak

### Option B: Use DynamoDB (RECOMMENDED)
- Pros: Auto-scaling, pay-per-use, built-in TTL
- Cons: Requires migration tooling, eventual consistency learning
  curve

### Option C: Use Cassandra
- Pros: Already in use for analytics
- Cons: Not optimized for small, frequently-accessed key-value
  patterns; ops overhead

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Migration downtime | High | Dual-write + gradual cutover |
| Read latency increase | Medium | DAX cache layer for hot sessions |
| TTL precision | Low | DynamoDB TTL has ~48h drift, acceptable |

## Rollout Plan

1. Week 1-2: Build migration tooling (dual-write to Redis + DynamoDB)
2. Week 3: Shadow mode (write to both, read from Redis)
3. Week 4: Canary — read 5% traffic from DynamoDB
4. Week 5-6: Gradual rollout (5% → 25% → 50% → 100%)
5. Week 7: Deprecate Redis session store

## Open Questions

1. Should we encrypt session data at rest in DynamoDB? (Suggestion: yes)
2. Do we need cross-region replication for DR? (Need input from infra team)

## References

- [DynamoDB TTL docs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [Previous Redis eviction incident](https://internal.acme.com/incidents/INC-2024-1129)
```

### 8.2.3 RFC 各部分的阅读重点

不是 RFC 的每个部分都要逐字细读。根据你的角色和目的，阅读重点不同：

**如果你是方案评审者（Reviewer）：**

| 部分 | 阅读重点 | 你要回答的问题 |
|------|---------|---------------|
| Background | 问题描述是否准确 | 这个问题真的存在吗？严重程度够不够？ |
| Proposal | 方案是否合理 | 这个方案能解决问题吗？有没有明显的设计缺陷？ |
| Alternatives | 是否考虑了足够多的选项 | 有没有遗漏的方案？各方案的对比是否公平？ |
| Risks | 风险识别是否充分 | 最大的风险是什么？缓解措施够不够？ |
| Rollout Plan | 上线计划是否安全 | 能不能回滚？灰度策略合理吗？ |

**如果你是方案执行者（Implementer）：**

重点看 **Proposal** 和 **Rollout Plan**，因为这两部分直接决定了你要怎么写代码。**Open Questions** 也要关注，因为这些问题可能在开发过程中需要你来回答。

**如果你只是被 CC 来知会的：**

读 **Background** 和 **Proposal** 的第一段就够了，了解"在做什么"就行。

### 8.2.4 RFC 中的高频词汇

读 RFC 时，有些词组会反复出现，理解它们能帮你更快抓住重点：

| 词汇/短语 | 含义 | 语境 |
|----------|------|------|
| "We propose..." | 我们建议... | 核心方案的引入 |
| "This document outlines..." | 本文概述... | 文档开头 |
| "Trade-off" | 权衡 | 讨论方案的优缺点 |
| "Scalability" | 可扩展性 | 方案能否应对未来增长 |
| "Backward compatible" | 向后兼容 | 新方案不会破坏旧功能 |
| "Deprecate" | 废弃 | 旧功能将被移除 |
| "Cutover" / "Migration" | 切换/迁移 | 从旧方案到新方案的过程 |
| "Canary" / "Gradual rollout" | 灰度/逐步上线 | 分阶段部署 |
| "Idempotent" | 幂等的 | 重复操作不会产生副作用 |
| "Best effort" | 尽力而为 | 不保证100%成功 |
| "No-op" | 空操作 | 不做任何事情的实现 |
| "Scope" | 范围 | 这个方案涵盖什么、不涵盖什么 |
| "Out of scope" | 超出范围 | 本方案不解决的问题 |

### 8.2.5 读 RFC 的实用技巧

1. **先读 Background 再读 Proposal**——不要跳过背景，因为方案的选择往往是由问题背景决定的。不理解问题，就无法判断方案是否合理。

2. **关注 Alternatives 部分**——这是最容易"偷工减料"的部分。如果 Alternatives 只写了一个选项，或者对比明显不公平，说明作者可能已经有了预设结论。

3. **看 Open Questions**——这部分反映了作者的诚实度。好的 RFC 会承认自己还没想清楚的问题，而不是假装一切都很完美。

4. **注意 Status 字段**——`Draft` 意味着还在讨论中，你可以提意见；`Approved` 意味着已经通过评审，准备执行了；`Obsolete` 意味着这个方案已经被废弃。

5. **用搜索来定位**——如果你只想了解某个方面，直接搜索关键词。比如想看风险，搜索 "Risk"；想看时间线，搜索 "Timeline" 或 "Rollout"。

---

## 8.3 事故复盘报告（Postmortem）阅读

### 8.3.1 什么是 Postmortem

Postmortem（事后复盘报告）是线上事故发生后的总结文档。它的目的不是追责，而是**找出根本原因，防止类似问题再次发生**。Google 有一条原则叫 "Blameless Postmortem"（不追责复盘），意思是复盘关注的是系统和流程的问题，而不是某个人的失误。

一封 Postmortem 通知邮件通常长这样：

```
Subject: [Postmortem] Payment API outage on Aug 8, 2025

Hi all,

We've published the postmortem for the payment API outage
that occurred on Aug 8, 14:00-14:45 PST.

Summary: A misconfigured rate limiter caused 100% of payment
requests to be rejected for approximately 45 minutes.
~8,200 transactions were affected.

Full postmortem: https://wiki.acme.com/postmortems/INC-2025-0808

Key action items:
1. Add rate limiter config validation to CI pipeline (Owner: @sarah, due: Aug 22)
2. Implement circuit breaker for payment service (Owner: @mike, due: Sep 5)
3. Create runbook for rate limiter incidents (Owner: @jennifer, due: Aug 15)

Please review and add any comments by Friday EOD.

Thanks,
Incident Response Team
```

### 8.3.2 Postmortem 的标准结构

一份完整的 Postmortem 通常包含以下部分：

```markdown
# Postmortem: Payment API Outage (INC-2025-0808)

**Date:** 2025-08-08
**Authors:** Sarah Chen, Mike Zhang
**Status:** Final
**Severity:** SEV-1 (Critical)
**Duration:** 14:00 – 14:45 PST (45 minutes)
**Impact:** 100% of payment requests rejected; ~8,200 transactions failed

## Summary

At 14:00 PST on Aug 8, 2025, a configuration change to the
rate limiter caused all payment API requests to be rejected
with HTTP 429. The issue was detected by automated alerting
within 2 minutes. The offending config was rolled back at
14:45, restoring full service.

## Timeline (all times PST)

| Time | Event |
|------|-------|
| 13:52 | Engineer deployed rate limiter config update via ConfigService |
| 13:55 | Config propagated to all production nodes |
| 14:00 | Alert triggered: "Payment API error rate > 50%" |
| 14:02 | On-call engineer acknowledged alert |
| 14:05 | Identified rate limiter as likely cause via log analysis |
| 14:10 | Attempted rollback via ConfigService — failed (config version conflict) |
| 14:20 | Escalated to platform team for manual intervention |
| 14:35 | Platform team manually reverted config on all nodes |
| 14:45 | Service fully restored, error rate back to 0% |
| 15:00 | Postmortem investigation began |

## Root Cause

The rate limiter config update contained a typo: the rate
limit was set to `0` (requests per second) instead of `10000`.
The value `0` was interpreted as "block all requests" rather
than "unlimited", which was the engineer's intent.

The config validation in ConfigService did not have a check
for zero or negative rate limit values, allowing this invalid
config to be deployed without warning.

## Contributing Factors

1. **No config preview:** ConfigService does not support
   dry-run or preview mode for config changes.
2. **Insufficient test coverage:** The rate limiter's unit
   tests did not include a case for `rate=0`.
3. **Rollback mechanism failed:** The config version conflict
   prevented automated rollback, adding 25 minutes to the
   resolution time.
4. **No secondary alerting:** The rate limiter metrics were
   not monitored independently — the first alert came from
   the payment API error rate, not from the rate limiter itself.

## Action Items

| # | Action | Owner | Priority | Due Date |
|---|--------|-------|----------|----------|
| 1 | Add validation for rate limiter config (reject rate ≤ 0) | @sarah | P0 | Aug 22 |
| 2 | Implement circuit breaker pattern in payment service | @mike | P1 | Sep 5 |
| 3 | Create runbook for rate limiter incidents | @jennifer | P1 | Aug 15 |
| 4 | Add rate limiter metrics dashboard and alerting | @david | P2 | Sep 1 |
| 5 | Support config dry-run mode in ConfigService | @alex | P2 | Sep 15 |

## What Went Well

- Alerting fired within 2 minutes of impact
- On-call engineer responded quickly (3 min ack time)
- Root cause identified within 10 minutes

## What Didn't Go Well

- Automated rollback failed due to config version conflict
- No independent monitoring for rate limiter
- Config validation gap allowed invalid value to deploy

## Lessons Learned

Config changes should be treated with the same rigor as code
changes — they need validation, review, and rollback testing.
The rate limiter is a critical path component and needs its
own monitoring and alerting.
```

### 8.3.3 Postmortem 各部分的阅读技巧

**Summary（摘要）**：如果只读一个部分，就读这个。Summary 通常用 3-5 句话告诉你发生了什么、影响多大、持续多久。读完 Summary 你就能决定要不要继续看细节。

**Timeline（时间线）**：这是事故的"故事线"。阅读时关注两个关键节点：**第一个异常是什么时候出现的**（root cause 触发点），以及**恢复是什么时候完成的**（resolution time）。中间的过程可以帮助你理解为什么花了这么长时间恢复。

**Root Cause（根本原因）**：这是 Postmortem 最有价值的部分。好的 Root Cause 分析会深入到"为什么会发生"，而不只是"发生了什么"。注意区分 **直接原因**（trigger）和 **根本原因**（underlying cause）。在上面的例子中，直接原因是"工程师把 rate limit 写成了 0"，但根本原因是"config 系统没有校验机制"。

**Action Items（行动项）**：这是复盘的产出物。每个 Action Item 应该有明确的 Owner 和 Due Date。阅读时注意：**有没有 Action Item 是针对根本原因的？** 如果所有 Action Item 都是在"修表面问题"，说明复盘不够深入。

**What Went Well / What Didn't Go Well**：这部分帮助你理解团队在事故中的表现。好的复盘不会只说"什么出了错"，也会说"什么做对了"，这有助于保持客观。

### 8.3.4 Postmortem 中的关键术语

| 术语 | 含义 | 说明 |
|------|------|------|
| SEV-1 / SEV-2 / SEV-3 | 事故严重等级 | SEV-1 最严重（服务完全中断），SEV-3 较轻 |
| Impact | 影响范围 | 受影响的用户数、请求数、交易数等 |
| Duration | 持续时间 | 从开始到恢复的总时长 |
| Root Cause | 根本原因 | 导致事故发生的最底层原因 |
| Contributing Factor | 促成因素 | 不是直接原因，但让事故更严重或更难恢复 |
| Mitigation | 缓解措施 | 临时恢复服务采取的措施 |
| Rollback | 回滚 | 将变更恢复到之前的状态 |
| Escalate | 升级 | 把问题交给更高级别的工程师处理 |
| On-call | 值班 | 负责响应告警的工程师 |
| Runbook | 操作手册 | 处理特定类型事故的步骤指南 |
| Blameless | 不追责 | 关注系统和流程，而非个人 |
| Post-incident review | 事后审查 | 和 Postmortem 同义 |

---

## 8.4 合规与安全公告阅读

### 8.4.1 为什么程序员需要读懂安全公告

想象这个场景：周一早上，你收到一封来自安全团队的邮件：

```
Subject: [Security] CVE-2025-3147 affects our log4j dependency — upgrade needed

Hi team,

We've identified that our services use log4j 2.14.1, which is
affected by CVE-2025-3147 (CVSS 9.8, Critical). This is a
remote code execution vulnerability.

Affected services:
- payment-service (log4j 2.14.1)
- user-service (log4j 2.14.1)
- notification-service (log4j 2.12.1 — NOT affected)

Remediation: Upgrade to log4j 2.17.1 or later.

Deadline: Please complete the upgrade by Aug 15, 2025 EOD.

CVE reference: https://nvd.nist.gov/vuln/detail/CVE-2025-3147

Thanks,
Security Team
```

如果你看不懂这封邮件，你就不知道要升级什么、为什么要升级、什么时候要完成。**安全公告的阅读能力，直接影响你处理安全问题的速度。**

### 8.4.2 Security Advisory / CVE 的结构

一个标准的 CVE（Common Vulnerabilities and Exposures）公告包含以下信息：

```
CVE-2025-3147

Published: August 7, 2025
Last Modified: August 8, 2025

Description:
Apache Log4j2 versions 2.0-beta7 through 2.14.1 JNDI features
used in configuration, log messages, and parameters do not
protect against attacker-controlled LDAP and other JNDI related
endpoints. An attacker who can control log messages or log
message parameters can execute arbitrary code loaded from LDAP
servers.

CVSS v3.1 Severity:
- Base Score: 9.8 (CRITICAL)
- Vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H

Affected Versions:
- log4j 2.0-beta7 to 2.14.1

Fixed Versions:
- log4j 2.17.1

References:
- https://logging.apache.org/log4j/2.x/security.html
- https://lists.apache.org/thread/...
```

### 8.4.3 安全公告的关键字段解读

| 字段 | 含义 | 你需要关注什么 |
|------|------|---------------|
| CVE ID | 漏洞编号（CVE-YYYY-NNNNN） | 用于在 NVD 等数据库中搜索 |
| Published / Modified | 发布/修改日期 | 越新发布越要关注，可能还在调查中 |
| Description | 漏洞描述 | 搞清楚是什么类型的漏洞（见下方分类） |
| CVSS Score | 严重程度评分（0-10） | ≥7.0 需要优先处理，≥9.0 紧急 |
| Affected Versions | 受影响版本 | 对比你使用的版本，确认是否受影响 |
| Fixed Versions | 修复版本 | 升级目标版本 |
| References | 参考链接 | 官方说明、补丁链接等 |

### 8.4.4 CVSS 评分等级

CVSS（Common Vulnerability Scoring System）是安全漏洞的标准评分体系：

| 分数范围 | 等级 | 含义 | 你的行动 |
|---------|------|------|---------|
| 9.0 – 10.0 | Critical | 严重 | 立刻处理，可能当天就要修复 |
| 7.0 – 8.9 | High | 高危 | 本周内修复 |
| 4.0 – 6.9 | Medium | 中危 | 排入近期迭代计划 |
| 0.1 – 3.9 | Low | 低危 | 有空再修，了解即可 |

### 8.4.5 常见漏洞类型关键词

安全公告的 Description 里会出现一些专业术语，描述漏洞的类型。理解这些术语能帮你快速判断漏洞的影响：

| 术语 | 中文 | 风险说明 |
|------|------|---------|
| Remote Code Execution (RCE) | 远程代码执行 | 攻击者可以远程执行任意代码，最危险 |
| SQL Injection (SQLi) | SQL 注入 | 攻击者可以操纵数据库查询 |
| Cross-Site Scripting (XSS) | 跨站脚本攻击 | 攻击者可以注入恶意脚本到网页 |
| Denial of Service (DoS) | 拒绝服务 | 攻击者可以让服务不可用 |
| Privilege Escalation | 提权 | 攻击者可以提升自己的权限 |
| Information Disclosure | 信息泄露 | 敏感信息可能被暴露 |
| Authentication Bypass | 认证绕过 | 攻击者可以绕过登录机制 |
| Path Traversal | 目录遍历 | 攻击者可以访问不该访问的文件 |
| SSRF | 服务端请求伪造 | 攻击者可以让服务器发起恶意请求 |
| CSRF | 跨站请求伪造 | 攻击者可以冒充用户发起请求 |

### 8.4.6 安全公告阅读流程

1. **看 CVSS Score** — 先判断优先级，分数高的先处理
2. **看 Affected Versions** — 确认你用的版本是否在范围内
3. **看 Description 中的漏洞类型** — RCE、SQLi 等高危类型优先
4. **看 Fixed Versions** — 找到修复版本号
5. **看 References** — 获取官方补丁和升级指南
6. **制定升级计划** — 评估升级风险，安排测试和发布

**一个重要提醒：** 不要只看 CVSS 分数就决定处理优先级。还要考虑你的服务是否暴露在公网、是否处理敏感数据、是否是核心链路。一个 CVSS 6.5 的漏洞，如果影响的是面向公网的核心支付服务，可能比一个 CVSS 9.0 但只影响内部管理工具的漏洞更紧急。

---

## 8.5 招聘 JD 与技术岗位描述阅读

### 8.5.1 为什么要学会读 JD

无论你是找工作还是招人，读懂 Job Description（职位描述）都是基本功。但很多程序员看到英文 JD 时，会被各种术语搞得云里雾里——"What does 'nice to have' really mean?" "'Rockstar developer'? 什么鬼?"

先看一个真实的技术岗位 JD：

```
Senior Backend Engineer — Payment Platform
Acme Corp | San Francisco, CA (Hybrid) | Full-time

About the Role:
We're looking for a Senior Backend Engineer to join our
Payment Platform team. You'll be building the next-generation
payment infrastructure that processes billions of dollars in
transactions annually.

What You'll Do:
- Design and implement scalable, fault-tolerant payment services
- Lead technical design discussions and mentor junior engineers
- Collaborate with cross-functional teams (Product, Compliance, Security)
- Drive operational excellence — monitoring, alerting, on-call rotation

Must Have:
- 5+ years of backend engineering experience
- Strong proficiency in Java or Go
- Experience with distributed systems and microservices architecture
- Understanding of database fundamentals (SQL and NoSQL)
- Experience with cloud platforms (AWS or GCP)

Nice to Have:
- Experience with payment systems (Stripe, Adyen, etc.)
- Knowledge of financial regulations (PCI-DSS, SOC 2)
- Experience with Kubernetes and service mesh
- Open source contributions

Equal Opportunity Employer:
Acme Corp is an Equal Opportunity Employer. We do not discriminate
on the basis of race, color, religion, gender, gender identity,
sexual orientation, age, national origin, disability, or veteran
status. We are committed to creating an inclusive environment
for all employees.

Benefits:
- Competitive salary + equity
- Comprehensive health/dental/vision insurance
- 401(k) matching (up to 4%)
- Unlimited PTO (with 15-day minimum)
- $2,000 annual learning and development budget
```

### 8.5.2 JD 结构拆解

| 部分 | 英文 | 说明 |
|------|------|------|
| 职位标题 | Job Title | 包含职位、团队、公司、地点、工作方式 |
| 关于职位 | About the Role | 公司和团队的简要介绍，工作内容概述 |
| 工作职责 | What You'll Do / Responsibilities | 你的日常工作内容 |
| 必备要求 | Must Have / Required Qualifications | 必须满足的条件，不满足基本没戏 |
| 加分项 | Nice to Have / Preferred Qualifications | 有了更好，没有也行 |
| 平等就业声明 | Equal Opportunity Employer | 法律要求，每家公司都有 |
| 福利待遇 | Benefits / Perks | 薪资、保险、假期等 |

### 8.5.3 "Must Have" vs "Nice to Have" 的潜规则

这是 JD 中最重要的区分：

- **Must Have（必备要求）**：这些是硬门槛。如果你不满足大部分 Must Have 条件，投简历的通过率会很低。但也别太焦虑——很多公司写"5+ years"，实际上 3-4 年经验如果能力够强也是可以的。

- **Nice to Have（加分项）**：这些不是必需的。如果你有，会增加竞争力；如果没有，不会因此被淘汰。很多候选人会因为没有 Nice to Have 的条件而不敢投，其实完全没必要。

一个实用的判断方法：**如果你满足 Must Have 条件的 70% 以上，就值得投简历。** 不要因为缺少某个 Nice to Have 条件就自我淘汰。

### 8.5.4 JD 中的高频术语翻译

| 英文术语 | 中文 | 真实含义 |
|---------|------|---------|
| Senior / Lead / Staff | 高级/负责人/Staff | 职级越高，经验要求越多，范围越广 |
| Full-time / Contract | 全职/合同 | 全职有福利，合同工通常没有 |
| On-site / Remote / Hybrid | 现场办公/远程/混合 | Hybrid = 一周去公司 2-3 天 |
| Cross-functional | 跨职能的 | 需要和非技术团队（产品、设计等）合作 |
| Scalable / Fault-tolerant | 可扩展/容错的 | 系统设计的基本要求 |
| Operational excellence | 运维卓越 | 上线后的维护、监控、告警等 |
| On-call rotation | 轮流值班 | 出了问题你要负责响应 |
| Proficiency / Strong understanding | 熟练/深入理解 | 不是"听过"，是"能独立做" |
| Working knowledge | 工作级了解 | 能用，但不需要精通 |
| Familiarity with | 熟悉 | 了解基本概念，用过就行 |
| Hands-on experience | 实操经验 | 真正做过，不是只看过文档 |
| Track record of | 有...的记录 | 做过类似的事并且有成果 |
| Self-starter | 自驱型 | 不需要别人推着走 |
| Team player | 团队合作者 | 能和别人配合工作 |
| Rockstar / Ninja / Guru | 明星/忍者/大师 | 这些词没什么实际意义，就是"我们想要厉害的人" |
| Culture fit | 文化契合 | 面试会考察你的价值观是否匹配 |
| Competitive salary | 有竞争力的薪资 | 通常不写具体数字，需要面试时谈 |
| Equity / Stock options | 股权/期权 | 公司给你的股份，上市后可能值钱 |
| 401(k) matching | 401k匹配 | 美国的养老金制度，公司按比例配缴 |
| PTO | 带薪休假 | Paid Time Off |

### 8.5.5 如何从 JD 中提取关键信息

读 JD 不是通读一遍就完事，你需要像做需求分析一样，提取出关键信息：

**第一步：判断匹配度**

拿一张纸，画两列：左边抄下 Must Have 条件，右边打勾或打叉。如果勾超过 70%，这个岗位值得投。

**第二步：识别技术栈**

从 Must Have 和 Nice to Have 中提取技术关键词。上面的例子中：
- 核心栈：Java 或 Go
- 架构：微服务、分布式系统
- 基础设施：AWS 或 GCP、Kubernetes
- 领域知识：支付系统、PCI-DSS

**第三步：理解工作内容**

从 What You'll Do 中判断这个岗位的日常：
- "Design and implement" → 你要写代码、做设计
- "Lead technical design discussions" → 你要做技术方案、带人讨论
- "Mentor junior engineers" → 你要带新人
- "On-call rotation" → 你要值班

这些信息能帮你判断这份工作是否符合你的期望。如果你不想值班，看到 on-call 就要考虑一下了。

**第四步：看福利待遇**

重点关注：
- 有没有写具体薪资范围（如果没写，面试时一定要问）
- Equity 的具体情况（多少股？vesting schedule？）
- PTO 政策（"Unlimited PTO" 听起来好，但实际上可能更难请假）
- 学习预算（说明公司是否支持个人成长）

**第五步：注意红线词**

有些 JD 用语暗示了公司文化，需要注意：
- "Work hard, play hard" → 可能意味着加班严重
- "Fast-paced environment" → 可能意味着节奏很快、压力大
- "Wear many hats" → 可能意味着你要做很多职责外的事
- "We're like a family" → 可能意味着边界感不强
- "Self-starter" → 可能意味着缺乏指导，要自己摸索

不是说有这些词就一定不好，但它们提供了一个信号，面试时可以针对性地提问确认。

---

## 本章小结

这一章我们聊了程序员日常最常见的四类英文文档的阅读方法。回顾一下核心要点：

**邮件阅读：** 先看 Subject 分类优先级，扫 Body 首尾段找行动项，掌握常见缩写（FYI/EOD/ASAP/OOO 等）让阅读速度翻倍。记住——不是每封邮件都需要回复。

**RFC/Tech Spec：** 重点读 Background 理解问题，读 Proposal 理解方案，读 Alternatives 判断方案合理性，读 Rollout Plan 了解执行计划。不要跳过 Alternatives，那里最能看出方案的思考深度。

**Postmortem：** 先读 Summary 了解概况，再读 Timeline 理解事故过程，重点关注 Root Cause 和 Action Items。好的复盘关注系统和流程，而不是追责。

**安全公告：** 先看 CVSS 分数判断优先级，再确认 Affected Versions 是否影响自己，最后看 Fixed Versions 制定升级计划。RCE、SQLi 等高危漏洞类型要特别警惕。

**招聘 JD：** 区分 Must Have 和 Nice to Have，满足 70% 的 Must Have 就值得投。注意提取技术栈信息，关注福利细节，对"红线词"保持警觉。

**一个贯穿所有文档类型的通用技巧：** 带着问题去读。读邮件时问"我需要做什么？"，读 RFC 时问"这个方案合理吗？"，读 Postmortem 时问"怎么防止再次发生？"，读安全公告时问"我受影响吗？"，读 JD 时问"这个岗位适合我吗？"。有目标地阅读，效率远高于漫无目的地从头看到尾。

下一章，我们将进入另一个重要场景：英文技术会议——如何在会议中听懂、发言、提问和总结。
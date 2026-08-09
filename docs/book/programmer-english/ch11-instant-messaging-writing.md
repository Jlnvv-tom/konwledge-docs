---
sidebar_position: 11
---

# 第十一章：即时通讯写作

> 在远程办公和分布式团队大行其道的今天，你写下的每一个字就是你的"工作面孔"。一条清晰的 Slack 消息、一个规范的 GitHub Issue、一段得体的 code review 评论，往往比你说的任何话都更有影响力。本章带你掌握即时通讯和异步协作场景下的英语写作技巧，让你的文字既专业又有人情味。

---

## 11.1 Slack/Teams 日常沟通表达

即时通讯工具（Slack、Microsoft Teams、Discord 等）是程序员日常沟通的主战场。和面对面聊天不同，文字沟通缺少语气和表情的辅助，一条措辞不当的消息很容易被误解。好在只要掌握一些基本模式，你就能在 Slack 里游刃有余。

### 常见缩写与黑话

先来认识一下即时通讯中高频出现的缩写：

| 缩写 | 全称 | 含义 |
|------|------|------|
| FYI | For Your Information | 供参考 |
| IMO / IMHO | In My Opinion / In My Humble Opinion | 我觉得 / 依我愚见 |
| TBH | To Be Honest | 说实话 |
| AFAIK | As Far As I Know | 据我所知 |
| IIRC | If I Recall/Remember Correctly | 如果我没记错的话 |
| LGTM | Looks Good To Me | 我觉得没问题（常用于 approve PR） |
| SGTM | Sounds Good To Me | 听起来不错 |
| NVM | Never Mind | 没事了 / 算了 |
| BRB | Be Right Back | 马上回来 |
| AFK | Away From Keyboard | 离开键盘（不在工位） |
| TIL | Today I Learned | 今天学到了 |
| OP | Original Poster | 原始发帖人 |
| CC | Carbon Copy | 抄送 |
| EOD | End Of Day | 今天下班前 |
| COB | Close Of Business | 下班时间 |
| ETA | Estimated Time of Arrival / Completion | 预计完成时间 |
| TL;DR | Too Long; Didn't Read | 太长不看 / 总结 |
| PR | Pull Request | 合并请求 |
| DM | Direct Message | 私信 |
| OOO | Out Of Office | 不在办公室 |
| WFH | Work From Home | 居家办公 |

### Channel 沟通礼仪

在公共频道发言和私信完全不同。频道是半公开场合，你的消息会被很多人看到，所以需要注意几点：

**1. 先搜索，再提问。** 很多问题之前有人问过，先翻翻历史记录：

```
Hi team, I searched the channel history but couldn't find this — 
does anyone know if we have a staging environment for the payments service?
```

**2. 一次性把话说清楚。** 避免"消息瀑布"（一条消息分成十条发）：

❌ 不好的做法：
```
hi
anyone online?
I have a question
about the deploy
it failed
like 3 times
```

✅ 好的做法：
```
Hi team, I'm having trouble deploying the payments service to staging. 
The deploy fails at the Docker build step with a "permission denied" error. 
I've already tried clearing the cache and re-running it. 
Full logs here: [link]. Has anyone seen this before?
```

**3. 用 @mention 时克制。** 不要随便 @channel 或 @here，那会通知所有人：

```
@channel — please avoid merging to main for the next 30 min, 
I'm running a migration on the DB. Will ping here when done. Thanks!
```

只在真正紧急或需要全员知晓时用 @channel。日常求助用 @具体的负责人就好。

**4. 用 thread 保持整洁。** 回复别人的消息时，尽量用 thread 而不是在频道里直接回复，这样不打断主线讨论：

```
[Main channel message]
@Sarah: The new API endpoint is live. Please test when you get a chance.

[Thread reply]
@Sarah: Tested — works great! One small thing: the response doesn't 
include the `created_at` field. Is that expected?
```

### DM（私信）沟通

DM 更私密，但也要注意分寸。以下是几种常见场景的表达模板：

**发起讨论：**
```
Hi Alex, do you have 10 min to chat about the auth refactor? 
I've got a few questions about the token refresh logic. 
No rush — anytime today works for me.
```

**请求帮助：**
```
Hey Lisa, quick question — when you ran the integration tests 
locally, did you have to set up a local Redis instance? 
The README doesn't mention it and tests are failing for me.
```

**同步进度：**
```
Hi Mark, just a heads up — I've finished the frontend changes 
for the dashboard. I'll open a PR this afternoon. 
No blockers on my end.
```

### Status 状态设置

Slack 的 status 是一个常被忽视但很有用的功能。设置好 status，别人就知道你的状态，不必反复问"你在吗？"。

**常见 status 表达：**

| 场景 | Status 文案 | Emoji |
|------|------------|-------|
| 开会中 | In a meeting | 📅 |
| 专注工作 | Heads down, focus time | 🎧 |
| 吃饭 | Out for lunch | 🍜 |
| 下班 | OOO, back tomorrow | 🏠 |
| 请假 | On PTO until Mon | 🌴 |
| 居家办公 | WFH today | 🏡 |
| 半天 | Out sick today | 🤒 |
| 出差 | Traveling, limited availability | ✈️ |
| 正在排查问题 | Investigating production incident | 🚨 |
| Code review 中 | Reviewing PRs, slow to respond | 👀 |

**设置 status 时的提示：**
```
/status 🎧 Focus time — will respond after 2pm
```

### Emoji Reaction 的妙用

Emoji reaction 是 Slack 中最高效的轻量回复方式。一条消息加个 reaction，就等于"收到了，不用单独回复"。

**程序员常用的 reaction 含义：**

| Emoji | 常见含义 |
|-------|---------|
| 👀 | 看到了 / 正在看 |
| ✅ | 同意 / 已完成 / 已确认 |
| 👍 | 赞 / 没问题 |
| 🎉 | 庆祝 / 恭喜 |
| 🙌 | 支持 / 太好了 |
| 🤔 | 需要想一下 / 有疑问 |
| ❌ | 不同意 / 不行 |
| 🐛 | 有 bug |
| 🔥 | 紧急 / 重要 |
| ♻️ | 已重新部署 / 已重新构建 |
| 📌 | 已置顶 / 重要信息 |
| 🧵 | 相关 thread |

**实际场景：**

```
[Lead]: Deploy is done, staging is back up.
You: ✅  (比打字"thanks, got it"更高效)

[Colleague]: Just pushed the fix, can someone review?
You: 👀  (表示"我正在看")
```

**小结一下：** 在 Slack/Teams 里，好的沟通 = 清晰 + 简洁 + 尊重他人时间。把信息一次性组织好发出来，善用 thread 和 reaction，设好 status，你就是团队里最靠谱的那个沟通者。

---

## 11.2 GitHub Issue 与 PR 描述写作

GitHub 是程序员的"主战场"，而 Issue 和 PR 则是你的"工作名片"。一个好的 Issue 能让别人快速理解问题并帮你，一个好的 PR 描述能让 reviewer 轻松审查你的代码。反之，一个糟糕的描述会让大家反复追问，浪费所有人的时间。

### Issue 描述写作

一个合格的 Issue 应该回答三个问题：**发生了什么？期望发生什么？如何复现？**

#### 好的 Issue 模板

```markdown
## 🐛 Bug Report

### Describe the bug
When a user uploads a profile picture larger than 5MB, the upload silently fails. No error message is shown to the user, and the request returns a 200 OK with an empty response body.

### To Reproduce
Steps to reproduce the behavior:
1. Log in as a regular user
2. Go to Settings → Profile
3. Click "Upload Avatar"
4. Select an image larger than 5MB (e.g., `test-image-8mb.png`)
5. Click "Save"
6. Observe that the page shows a success toast, but the avatar doesn't update

### Expected behavior
The upload should either:
- Compress the image automatically and upload, OR
- Show an error message like "Image must be under 5MB"

### Environment
- OS: macOS 14.2
- Browser: Chrome 120
- App version: v2.4.1
- Backend: staging environment (`api.staging.example.com`)

### Additional context
- This works fine for images under 5MB
- Console shows no errors
- Network tab shows the request completes with 200 but empty body
- Related code: `src/services/upload.ts` → `uploadAvatar()` function
```

#### 坏的 Issue 描述

```markdown
## Upload broken

When I upload a big image it doesn't work. Please fix.
```

对比一下：好的 Issue 让任何看到的人都能在 30 秒内理解问题并开始排查。坏的 Issue 让人不得不追问"什么图片？""多大？""什么浏览器？"——一问一答之间，半天就过去了。

#### Feature Request 的写法

```markdown
## 🚀 Feature Request: Add dark mode support for the dashboard

### Is your feature request related to a problem?
Currently, the dashboard only supports light mode. Users who work at night 
or prefer dark themes have no option to switch, which causes eye strain.

### Describe the solution you'd like
Add a theme toggle in the user settings that switches between light and dark mode. 
The preference should be persisted per user.

### Describe alternatives you've considered
- Using browser-level `prefers-color-scheme` (good as default, but users should 
  still be able to override)
- A CSS-only solution with media queries (doesn't allow manual toggle)

### Additional context
- Design mockup: [Figma link]
- Related components: `Dashboard`, `Sidebar`, `Chart` 
- We already use CSS variables, so this should be straightforward
```

### PR 描述写作

PR 描述是给 reviewer 看的"说明书"。reviewer 可能不了解你的改动背景，你需要帮他们快速进入状态。

#### PR 描述模板

```markdown
## Summary

Add input validation to the user registration endpoint to prevent 
duplicate email addresses from being created.

## Changes

- Added `isEmailTaken()` check in `authService.ts`
- Updated `register()` controller to return 409 Conflict on duplicates
- Added unit tests for the new validation logic
- Updated API docs in `openapi.yaml`

## Related Issue

Closes #342

## How to Test

1. Run the API locally: `npm run dev`
2. Register a user with email `test@example.com`
3. Try registering again with the same email
4. Verify you get a 409 response:
   ```json
   {
     "error": "EMAIL_TAKEN",
     "message": "An account with this email already exists."
   }
   ```
5. Run tests: `npm test -- auth`

## Screenshots / Recordings

[If applicable, add screenshots or screen recordings]

## Checklist

- [x] Code follows project style guidelines
- [x] Self-reviewed the code
- [x] Added/updated tests
- [x] Updated documentation
- [ ] No new warnings in build
```

#### PR 描述的好坏对比

❌ **坏的 PR 描述：**
```markdown
fixed the bug
```

这什么都没说。reviewer 得自己去猜你改了什么、为什么改、怎么测试。

✅ **好的 PR 描述：**
```markdown
## Summary

Fixes a memory leak in the WebSocket connection handler where connections 
were not being properly closed on client disconnect.

## Root Cause

The `cleanupConnection()` function was only called on explicit disconnect 
events, but not when the client socket timed out. This caused the 
`activeConnections` Map to grow indefinitely.

## Changes

- Added cleanup call in the socket `timeout` event handler
- Added a max connection TTL of 30min as a safety net
- Added logging for connection lifecycle events

## Testing

- Manually tested by connecting 100 clients and letting them time out
- Verified `activeConnections.size` returns to 0 after timeout
- Added integration test: `ws-connection-cleanup.test.ts`

Closes #891
```

### Linked Issue 的正确写法

GitHub 支持用关键字自动关联 Issue：

| 关键字 | 效果 |
|--------|------|
| `Closes #123` | 合并 PR 时自动关闭 Issue #123 |
| `Fixes #123` | 同上 |
| `Resolves #123` | 同上 |
| `Refs #123` | 仅引用，不自动关闭 |
| `See #123` | 仅引用 |

```markdown
## Related Issues

Closes #342
Refs #343 (related but separate fix needed)
```

**小结一下：** 好的 Issue 和 PR 描述不是"写给自己看的备忘录"，而是"写给别人看的说明书"。把你做的事情、为什么做、怎么验证，清清楚楚地写出来，让任何人都能快速理解——这就是最高效的协作方式。

---

## 11.3 代码审查评论写作

Code Review（代码审查）是程序员日常工作中最需要"好好说话"的场景之一。一句措辞不当的评论，可能让同事心情不好一整天；而一条建设性的评论，不仅提升代码质量，还能增进团队关系。

### 评论类型

先明确你在写什么类型的评论，这决定了你的措辞：

| 类型 | 含义 | 示例 |
|------|------|------|
| **nit** | 吹毛求疵的小问题，可不改 | "nit: extra blank line here" |
| **suggestion** | 建议改进，但不 blocking | "suggestion: we could extract this into a helper" |
| **question** | 想理解作者的意图 | "question: why did you choose `Map` over `Record` here?" |
| **blocking** | 必须修改才能合并 | "blocking: this will throw on null input" |
| **praise** | 表扬写得好 | "love how clean this is!" |

在评论前面加上类型标签，能让作者立刻知道你的语气和意图：

```
nit: trailing whitespace on line 42

suggestion: consider using `Array.flat()` instead of the nested reduce — 
might be more readable

question: is there a reason we're not using the `useMemo` hook here?

blocking: this API call doesn't have error handling — if the request fails, 
the whole component will crash

praise: this refactor is really clean, nice work!
```

### 好的 vs 坏的评论

#### 坏的评论

```
This is wrong.

Why did you do it this way?

This code is terrible.

You should know better.

Just use a Set.
```

这些评论的问题在于：没有上下文、没有解释、语气居高临下。它们不是在帮忙，而是在宣泄情绪。

#### 好的评论

```
This approach might cause issues when the input array is empty — 
`array[0]` would return `undefined` and the downstream code 
assumes it's always a string. Could we add a guard clause?

if (array.length === 0) {
  return '';
}
```

```
Have you considered using `Intl.DateTimeFormat` instead of `moment.js`? 
It's built-in and would save us ~70KB in bundle size. 
Here's the docs: [link]

If there's a specific reason to use moment, totally fine — 
just curious!
```

#### Code Review 的黄金法则

**1. 对事不对人。**

❌ "Your code is hard to read."
✅ "This function is doing a lot — could we split it into smaller functions?"

**2. 解释为什么，不只是说改什么。**

❌ "Move this to a separate file."
✅ "Moving this to a separate file would make it easier to test in isolation and keep `utils.ts` from growing too large."

**3. 给出具体建议，而不是模糊方向。**

❌ "This should be more efficient."
✅ "Using `Set.has()` instead of `Array.includes()` here would change the lookup from O(n) to O(1), since we're checking membership in a loop."

**4. 用问句代替命令句。**

❌ "Change this to async/await."
✅ "Would it make sense to use async/await here? I find it easier to read than the `.then()` chain, but happy either way."

**5. 区分"必须改"和"可以改"。**

```
[blocking] This SQL query is vulnerable to injection — we need to use 
parameterized queries here.

[nit] Could use `const` instead of `let` on line 15 since the value 
isn't reassigned. No big deal if you skip this.
```

### 常用评论模板

**请求澄清：**
```
I'm not sure I follow the logic here — could you add a comment 
explaining why we need to multiply by 1.5? Thanks!
```

**指出潜在问题：**
```
One thing to watch out for: if `user.preferences` is null (which happens 
for legacy accounts), this will throw. We might want to add a null check:

const theme = user.preferences?.theme ?? 'light';
```

**建议替代方案：**
```
Alternative approach: instead of fetching all users and filtering client-side, 
we could add a `?role=admin` query param to the API. This would reduce the 
payload significantly for orgs with many users. Happy to pair on this if you want.
```

**Approve 时的话：**
```
Great work! The logic is solid, tests look comprehensive, and I really 
appreciate the documentation updates. Just a couple of nits — feel free 
to address or ignore. LGTM! 🚀
```

**请求修改后重新审查：**
```
Thanks for the updates! The null check looks good. 
I left one more comment about the test coverage — once that's addressed, 
I think we're good to merge.
```

**小结一下：** Code Review 评论的核心原则是——**你是在帮同事变得更好，不是在证明自己更聪明。** 带着善意写评论，解释你的理由，给出具体的建议，区分轻重缓急。你的同事会用同样的方式对待你的 PR——这就是良性循环。

---

## 11.4 Stack Overflow 提问与回答写作

Stack Overflow 是程序员的"知识图书馆"，但很多人在上面提问后石沉大海，回答也无人问津。问题往往不在技术本身，而在于——你能不能把问题写清楚。

### 如何写一个好问题

#### MCVE：最小可复现示例

Stack Overflow 提问的黄金法则是 **MCVE**（Minimal, Complete, Verifiable Example）：

- **Minimal（最小化）**：去掉所有与问题无关的代码
- **Complete（完整）**：别人拿到你的代码能直接运行
- **Verifiable（可验证）**：你描述的问题能被稳定复现

#### 提问模板

```markdown
## Title
How to handle "Cannot read property 'map' of undefined" when fetching 
data from an API in React?

## Body

I'm fetching data from an API and trying to render a list, but I'm getting 
the error: `Cannot read property 'map' of undefined`.

### What I'm trying to do
Fetch a list of users from `/api/users` and render them as a list of cards.

### What I've tried
- Checked the API response in Postman — it returns the expected data
- Added `console.log` and confirmed `data` is `undefined` when `.map()` is called
- Read the React docs on data fetching and the `useEffect` dependency array

### Code

```jsx
function UserList() {
  const [data, setData] = useState();

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setData(data));
  }, []);

  return (
    <ul>
      {data.users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### Error message
```
TypeError: Cannot read property 'map' of undefined
```

### What I expected
The component should render a list of user names.

### Environment
- React: 18.2.0
- Browser: Chrome 120
```

#### 坏的问题

```
Title: React map error help!!!

Body: my code is broken, it says map is not a function. 
here is my code pls help urgent!!!!
```

这个问题的致命伤：标题没有信息量、没有错误信息、没有复现步骤、没有尝试记录、有"urgent"字样（Stack Overflow 社区非常反感用"urgent"来施压）。

#### 好的 vs 坏的标题

| ❌ 坏的标题 | ✅ 好的标题 |
|-----------|-----------|
| Help!!! | How to fix "Cannot read property 'map' of undefined" in React useEffect |
| JavaScript bug | Why does `Array.includes()` return false for an object that exists in the array? |
| Urgent question | How to properly type a debounce function with TypeScript generics? |
| Not working | Express.js middleware not being called for PUT requests but works for POST |

好的标题包含：**技术栈 + 具体问题 + 关键错误信息**。

### 如何写一个好的回答

#### 回答写作要点

**1. 先直接回答问题，再展开解释。**

```markdown
The issue is that `data` is `undefined` on the first render because 
the API call hasn't completed yet. You need to handle the loading state:

```jsx
function UserList() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => setData(data))
      .catch(err => console.error(err));
  }, []);

  if (!data) return <p>Loading...</p>;

  return (
    <ul>
      {data.users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### Why this happens

`useState()` without an argument sets the initial state to `undefined`. 
On the first render, the `useEffect` hasn't run yet, so `data` is `undefined` 
when the component tries to call `data.users.map()`.

### Additional tips

- Consider using a loading state (`useState(true)`) instead of null-checking
- Add error handling for the fetch call
- Look into React Query or SWR for more robust data fetching
```

**2. 解释"为什么"，不只是"改成什么"。**

❌ "Just add `null` check."
✅ "The issue is that `data` is `undefined` on the first render... [explanation]"

**3. 提供可运行的代码。**

不要只给片段，给一个别人能直接复制粘贴运行的完整示例。

**4. 如果有多个解决方案，列出最优的，提一下其他的。**

```markdown
The cleanest solution is to initialize state with `null` and add a 
loading guard (see code above). 

Alternatively, you could use optional chaining: `data?.users?.map(...)`, 
but this would silently render nothing, which might hide other issues.
```

**5. 引用权威来源。**

如果你说"这是 React 的设计行为"，最好附上官方文档链接：
```markdown
This is expected behavior — `useEffect` runs after the first render. 
See the React docs: https://react.dev/reference/react/useEffect#usage
```

### 接受回答

当某个回答解决了你的问题，点击 ✓ 接受它。这不仅是礼貌，也是给后来者的信号：
"这个方案有效。"

```markdown
Thanks! This was exactly the issue — I didn't realize `useEffect` runs 
after the first render. The loading guard fixed it. 

For anyone else hitting this: I also found that using React Query 
handles this automatically (loading state, caching, etc.).
```

### 声誉系统

Stack Overflow 的声誉（reputation）系统决定了你在社区中的权限：

| 操作 | 声誉变化 |
|------|----------|
| 提问被 upvote | +5 |
| 回答被 upvote | +10 |
| 回答被接受 | +15 |
| 你接受别人的回答 | +2 |
| 提问被 downvote | -2 |
| 回答被 downvote | -2 |

声誉不是目的，而是结果。专注于写好问题和回答，声誉自然水涨船高。

**小结一下：** Stack Overflow 的核心法则是——**帮未来的读者写，不是只为自己问。** 你提的每个问题、写的每个回答，都会被成千上万的后来者搜索到。把它写得清晰、完整、可复现，就是在为整个编程社区做贡献。

---

## 11.5 开源社区参与表达

参与开源社区是程序员成长的重要途径。但在开源社区里，你的每一句话都在公共记录上，措辞的得体与否直接影响你在社区中的形象。无论是提提案、参与讨论还是表达感谢，都需要掌握一些基本套路。

### RFC / Proposal 写作

RFC（Request for Comments）是开源社区讨论重大改动的标准方式。一个好的 RFC 应该包含：背景、动机、方案设计、替代方案、影响范围。

#### RFC 模板

```markdown
# RFC: Add Plugin System to the Markdown Renderer

## Summary

Propose a plugin architecture for the Markdown renderer that allows 
users to extend rendering behavior without forking the core library.

## Motivation

Currently, extending the renderer requires monkey-patching internal 
functions, which is fragile and breaks on every minor release. 

User requests for custom rendering (#142, #178, #203) are common 
enough that a formal plugin API would benefit the ecosystem.

## Detailed Design

### Plugin Interface

```typescript
interface MarkdownPlugin {
  name: string;
  init?(renderer: MarkdownRenderer): void;
  transformNode?(node: ASTNode): ASTNode | null;
  render?(node: ASTNode, context: RenderContext): string | null;
}
```

### Registration

```typescript
const renderer = new MarkdownRenderer({
  plugins: [
    syntaxHighlightPlugin,
    emojiPlugin,
    customLinkPlugin,
  ],
});
```

### Execution Order

Plugins are executed in registration order. A plugin can return `null` 
from `transformNode` to remove a node from the AST, or `null` from 
`render` to fall through to the default renderer.

## Alternatives Considered

1. **Middleware pattern** — more flexible but harder to reason about 
   execution order and side effects.
2. **Event-based hooks** — simpler but doesn't allow plugins to modify 
   the AST structure.
3. **Keep status quo** — users continue monkey-patching. Not scalable.

## Drawbacks

- Adds complexity to the core library (~2KB gzipped)
- Plugin authors need to understand the AST structure
- Potential for plugin conflicts (two plugins transforming the same node)

## Migration Plan

- v3.1: Introduce plugin API (non-breaking)
- v3.2: Deprecate internal hooks (with warnings)
- v4.0: Remove internal hooks

## Open Questions

1. Should plugins be able to define new node types?
2. How do we handle async plugins (e.g., fetching data during render)?
3. Should there be a plugin registry/marketplace?
```

#### 写 RFC 的注意事项

**1. 动机要充分。** 不是"我觉得这个功能很酷"，而是"这是用户的真实痛点，这是证据"。

```
We've received 14 issues in the past 3 months requesting custom 
rendering support (see #142, #178, #203, #215...). The current 
workaround (monkey-patching) has caused 7 upgrade-related bugs.
```

**2. 方案要具体。** 不要只说"我们应该支持插件"，要给出 API 设计、类型定义、执行流程。

**3. 诚实面对缺点。** 每个方案都有 trade-off，把它们写出来反而显示你思考周全。

```
Drawback: This adds ~2KB to the bundle size. For users who don't 
use plugins, this is an unavoidable cost. We could mitigate this 
by making the plugin system tree-shakeable.
```

**4. 列出开放问题。** 表明你还没想清楚所有细节，欢迎社区贡献想法。

### Discussion Thread 参与

在 GitHub Discussions、RFC 评论区或邮件列表中参与讨论时，注意以下原则：

**1. 先读完再回复。**

```
I read through the RFC and the previous discussion thread. 
To address the concern about bundle size raised in [comment] — 
I ran a quick test and the plugin system adds ~2KB gzipped. 
Here's the breakdown: [link to size analysis]
```

**2. 用数据说话。**

````markdown
I benchmarked the three proposed approaches on a 10MB Markdown file:

| Approach | Time (ms) | Memory (MB) |
|----------|-----------|------------|
| Current (no plugins) | 45 | 12 |
| Plugin system | 52 | 14 |
| Middleware pattern | 68 | 18 |

The overhead is ~15% for the plugin system, which seems acceptable.
````

**3. 提出建设性意见，不只是反对。**

❌ "I don't like this."
✅ "I have a concern about the plugin execution order — if two plugins 
transform the same node, the result depends on registration order, 
which might surprise users. Could we add a priority field to the 
plugin interface to make this explicit?"

**4. 尊重不同意见。**

```
I see your point about preferring the event-based approach. 
You're right that it's simpler and covers most use cases. 

My concern is that events don't allow AST modification, which 
is needed for some plugins (e.g., table of contents generation). 

What if we combined both — events for simple cases, and the 
plugin interface for advanced use cases?
```

### Thank You Note（致谢）

在开源社区，懂得感谢别人是一种重要的社交技能。无论是感谢 someone 帮你修了 bug、review 了代码，还是感谢 maintainer 维护了一个好项目，一封得体的感谢信都能让人感到温暖。

#### 感谢 maintainer

```markdown
Hey @maintainer,

Just wanted to say a huge thank you for maintaining this library. 
We've been using it in production for over a year now, and it's been 
rock solid. The documentation is excellent, and the v3 migration 
guide saved us hours.

I know maintaining an open-source project is a lot of unpaid work. 
If there's anything I can help with — triaging issues, writing docs, 
or answering questions — please let me know. I'd love to give back 
to a project that's been so valuable to us.

Thanks again!
```

#### 感谢贡献者

```markdown
Thanks for this PR! Really appreciate you taking the time to:

- Fix the memory leak in the connection handler
- Add comprehensive tests (the edge cases are great)
- Update the docs proactively

This is exactly the kind of contribution that makes the project better 
for everyone. Merging now! 🎉
```

#### 感谢帮助过你的人

```markdown
Hi @helper,

Just wanted to follow up and let you know your suggestion worked 
perfectly! We deployed the fix last week and haven't seen the issue 
since. Really appreciate you taking the time to help — your explanation 
of the underlying cause was super clear and educational.

Thanks again! 🙏
```

#### 在 Release Notes 中致谢

```markdown
## v3.2.0

### New Features
- Plugin system (@alice)
- Dark mode support (@bob)

### Bug Fixes
- Fix memory leak in WebSocket handler (@charlie)
- Fix timezone parsing in date utils (@diana)

### Thanks
Special thanks to @eve, @frank, and @grace for their feedback 
on the RFC and design discussions. This release wouldn't be 
possible without our amazing community! 💜
```

### 常用社区表达速查

| 场景 | 表达 |
|------|------|
| 表示同意 | "Makes sense.", "Agreed.", "+1 to this." |
| 表示反对 | "I see your point, but...", "I have a concern about..." |
| 请求澄清 | "Could you elaborate on...", "I'm not sure I follow..." |
| 提出建议 | "What if we...", "Would it make sense to..." |
| 表示感谢 | "Really appreciate...", "Thanks for taking the time to..." |
| 谦虚接受反馈 | "Good catch!", "You're right, I missed that." |
| 结束讨论 | "I think we've reached consensus.", "Let's go with option A." |
| 请求帮助 | "Would anyone be willing to...", "Could use a hand with..." |

**小结一下：** 开源社区的本质是"一群陌生人基于信任和尊重协作"。你的每一句话都在建立（或消耗）这个信任。写好 RFC、参与讨论时尊重他人、及时表达感谢——这些看起来是"软技能"，但它们往往比代码本身更能决定你在社区中的影响力。

---

## 本章小结

这一章我们聊了程序员在日常异步协作中最常见的四种写作场景：

1. **Slack/Teams 即时通讯** — 掌握缩写黑话，善用 thread 和 reaction，消息一次性写清楚，设好 status。核心原则：**清晰 + 简洁 + 尊重他人时间。**

2. **GitHub Issue 与 PR 描述** — Issue 要回答"发生了什么、期望什么、如何复现"；PR 要当好 reviewer 的"说明书"。核心原则：**写给读者，不是写给自己。**

3. **代码审查评论** — 区分 nit/suggestion/question/blocking/praise，对事不对人，解释为什么，用问句代替命令句。核心原则：**帮同事变得更好，不是证明自己更聪明。**

4. **Stack Overflow 提问与回答** — 遵循 MCVE 原则，标题要信息量充足，回答先给结论再展开，接受帮助要及时反馈。核心原则：**帮未来的读者写，不是只为自己问。**

5. **开源社区参与** — RFC 要动机充分、方案具体、诚实面对缺点；讨论要读完再回复、用数据说话；致谢要真诚具体。核心原则：**每一句话都在建立信任。**

记住：**在远程协作时代，你的写作能力就是你的工作能力。** 把每一条消息、每一个 Issue、每一条评论都当作展示专业素养的机会，你会发现——好沟通的程序员，运气都不会太差。
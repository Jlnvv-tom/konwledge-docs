# 第十一章 本地QClaw生图技能

> 大多数人以为AI生图就是"输入描述，等待出图"两步走。但当你真正打开一个生图技能的源码，会发现从你按下回车到图片落盘，中间经历了任务提交、状态机轮询、指数退避重试、流式下载至少四个阶段。任何一个环节失败，你看到的就是一个冷冰冰的错误提示。本章带你拆解QClaw生图技能的完整内部世界——从安装配置到源码级深度解析，让你不再只是一个"会写prompt的用户"。

我是怕浪猫，一个喜欢把技术拆到骨头缝里再拼回去的写手。这一章我们来聊QClaw生态里的生图技能，不浮在"怎么用"的表面，而是深入到每一行核心代码，搞清楚一张图从请求到落盘到底经历了什么。

## 11.1 QClaw生图技能概述

### 11.1.1 技能定位：Agent化的AI生图工具

QClaw生图技能（qclaw-generate-image）是QClaw技能生态中的一个核心创意工具。它的定位不是"又一个生图API封装"，而是一个完整的Agent化生图工作流。所谓Agent化，是指这个技能被设计为由AI Agent直接调用，AI负责理解用户的自然语言意图、构造高质量prompt、选择合适的分辨率和参数，然后执行脚本完成生图。

这和传统生图工具有本质区别。传统工具要求用户自己写prompt、自己选参数、自己判断结果好坏。而QClaw生图技能把prompt构造的决策逻辑写进了SKILL.md，AI会在调用脚本之前自动扩写用户的简短描述，补充风格、光影、构图等关键信息。用户说"画只猫"，AI传入的是"一只橘色英短猫咪慵懒地趴在阳光充足的窗台上，柔和暖色光影，摄影风格，浅景深，4K高清"。这种"用户说人话，AI写prompt"的设计，大幅降低了生图门槛。

**核心设计哲学：技能是AI的能力延伸，不是人的工具。** 脚本面向AI调用设计，参数用CLI（Command Line Interface，命令行界面）flag传递，输出用结构化JSON，错误处理有明确的建议文案。一切都是为了让AI能可靠地完成端到端流程。

### 11.1.2 与其他生图工具的区别

市面上常见的AI生图工具大致分三类。第一类是SaaS（Software as a Service，软件即服务）平台，如Midjourney、DALL-E 3的Web界面，用户在网页上操作，优点是易用，缺点是无法编程集成。第二类是API服务，如OpenAI Images API、Stability AI API，开发者自己写代码调用，灵活但需要自行处理鉴权、重试、下载等基础设施。第三类是本地部署方案，如Stable Diffusion WebUI，需要GPU和模型文件，门槛高。

QClaw生图技能的独特之处在于它处于API服务和本地部署之间。它通过本地Auth Gateway（认证网关）代理所有请求，鉴权由后台自动处理，用户无需手动管理API Key。脚本运行在本地Node.js环境，图片自动下载到工作空间目录。整个流程对AI Agent来说就是一个CLI命令，但对用户来说，体验类似于SaaS平台的简便。

| 维度 | SaaS平台 | 纯API方案 | QClaw生图技能 |
|------|---------|----------|-------------|
| 鉴权管理 | 平台托管 | 手动管理Key | Gateway自动处理 |
| Prompt构造 | 用户自己写 | 用户自己写 | AI自动扩写优化 |
| 图片下载 | 手动保存 | 自行编码 | 自动下载到workspace |
| 错误处理 | 界面提示 | 自行编码 | 结构化错误+建议文案 |
| 批量/联动 | 不支持 | 可编程 | 可与其他QClaw技能联动 |

### 11.1.3 支持的生图模型和后端

QClaw生图技能的后端模型是可配置的，当前版本默认接入的生图后端支持文生图（text-to-image）和图生图（image-to-image）两种模式。从SKILL.md的配置来看，技能本身不直接绑定某个特定模型，而是通过Auth Gateway统一转发请求到后端生图服务。这种架构意味着后端模型可以独立升级，技能侧无需改动代码。

从配置文件中可以看到，技能定义了`SUBMIT_PATH`和`QUERY_PATH`两个API端点，分别用于提交生图任务和查询任务状态。这是典型的异步任务架构，后端可能是OpenAI DALL-E、Stable Diffusion或自研模型的任意一种，对技能来说完全透明。技能只关心四个状态：submitted（已提交）、queued（排队中）、running（生成中）、succeeded（成功）或failed（失败）。

分辨率方面，技能内置了10种预设比例，覆盖了从正方形到宽屏到竖屏的常见需求。支持的分辨率包括768:768、1024:1024（默认）、768:1024、864:1152、1024:768、1152:864、768:1344、576:1024、1344:768、1024:576。这个白名单设计确保用户不会传入后端不支持的分辨率导致任务失败。

## 11.2 安装与配置

### 11.2.1 技能安装方法

QClaw生图技能的安装非常直接。在QClaw环境中，技能以目录形式存在于`~/.qclaw/skills/`下。安装方式有两种：通过SkillHub在线安装，或手动将技能目录放置到指定位置。

在线安装是推荐方式。在QClaw对话中直接告诉AI"安装qclaw-generate-image技能"，系统会调用skillhub工具自动下载和部署。安装完成后，技能目录结构如下：

```
~/.qclaw/skills/qclaw-generate-image/
├── SKILL.md                          # 技能文档（AI必读）
└── scripts/
    ├── generate.cjs                  # 主入口脚本
    └── lib/
        ├── config.cjs                # 配置模块
        ├── poll.cjs                  # 轮询模块
        ├── images.cjs                # 图片处理模块
        └── http.cjs                  # HTTP请求模块
```

这个结构体现了关注点分离的设计原则。主入口负责流程编排，每个lib模块负责一个明确的职责。后面的小节会逐一拆解每个文件的实现。

### 11.2.2 config.cjs配置文件详解

config.cjs是整个技能的配置中枢，所有可调参数都集中在这里。让我们看完整的配置结构和每一项的含义：

```javascript
// config.cjs 核心配置项

// Auth Gateway 配置
const PROXY_PORT = process.env.AUTH_GATEWAY_PORT || '19000';
const PROXY_HOST = '127.0.0.1';
const SUBMIT_PATH = '/proxy/qclaw-generate-image/submit';
const QUERY_PATH = '/proxy/qclaw-generate-image/query';

// 超时配置
const REQUEST_TIMEOUT_MS = 30000;       // 单次HTTP请求超时30秒
const MAX_POLL_TIME_MS = 180000;        // 最大轮询等待180秒
const DOWNLOAD_TIMEOUT_MS = 60000;      // 图片下载超时60秒
const DEFAULT_POLL_INTERVAL_MS = 3000;  // 默认轮询间隔3秒

// 分辨率白名单
const VALID_RESOLUTIONS = new Set([
  '768:768', '1024:1024',
  '768:1024', '864:1152',
  '1024:768', '1152:864',
  '768:1344', '576:1024',
  '1344:768', '1024:576',
]);
```

配置项分为三大类。第一类是Gateway连接配置，定义了本地代理的地址和端口。Auth Gateway默认运行在127.0.0.1:19000，这是QClaw Electron应用的内置服务。所有生图请求都经过Gateway转发，Gateway负责在请求头中注入认证信息，技能代码本身不接触任何API Key。

第二类是超时配置，这是整个技能可靠性保障的基石。四个超时值构成了一个层次化的时间管理体系：单次HTTP请求30秒超时防止请求挂死，轮询总时长180秒匹配后端2-3分钟的生成时间，图片下载60秒超时覆盖大图传输场景，轮询间隔3秒是响应速度和服务压力的平衡点。

第三类是分辨率白名单，用Set数据结构实现O(1)查找。`resolveImageOutputDir`函数还实现了优雅降级逻辑：优先保存到workspace下的generated-images目录，如果cwd不可写则回退到`~/.qclaw/generated-images/`。这种设计确保在Electron渲染进程的极端环境下也能正常工作。

**配置参数速查表：**

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| PROXY_HOST | 127.0.0.1 | Gateway地址 |
| PROXY_PORT | 19000 | Gateway端口 |
| SUBMIT_PATH | /proxy/qclaw-generate-image/submit | 任务提交端点 |
| QUERY_PATH | /proxy/qclaw-generate-image/query | 任务查询端点 |
| REQUEST_TIMEOUT_MS | 30000 | 单次请求超时 |
| MAX_POLL_TIME_MS | 180000 | 最大轮询时长 |
| DOWNLOAD_TIMEOUT_MS | 60000 | 下载超时 |
| DEFAULT_POLL_INTERVAL_MS | 3000 | 默认轮询间隔 |
| IMAGE_OUTPUT_DIR | workspace/generated-images | 图片输出目录 |

### 11.2.3 API Key配置与鉴权机制

QClaw生图技能的鉴权设计与大多数API工具不同。技能代码中没有任何API Key的硬编码或环境变量读取，所有鉴权工作由Auth Gateway在后台完成。这意味着用户不需要手动配置OpenAI API Key或Stability AI Key，只要QClaw客户端处于登录状态，Gateway会自动处理Token注入。

这种设计的优势是显而易见的。首先是安全性，API Key不会暴露在脚本代码或环境变量中，减少了泄露风险。其次是便利性，用户无需关心不同模型后端使用不同的鉴权方式。最后是可维护性，后端切换模型或更新鉴权方式时，只需Gateway侧更新，所有技能无需改动。

从http.cjs的`gatewayPost`函数可以看到，请求直接发往127.0.0.1:19000，不携带任何额外的认证头信息。Gateway在转发请求到后端服务时，会自动添加必要的认证信息。这就像公司门禁系统：你只需要刷卡进入大楼（登录QClaw），之后进入每个房间（调用各API）不需要再次刷卡。

### 11.2.4 模型默认参数设置

技能的默认参数在generate.cjs中设定，设计上偏向"开箱即用"的体验。分辨率默认1024:1024（正方形），这是最通用的比例，适合头像、社交配图等场景。prompt智能改写（revise）默认开启，设为1，意味着即使用户给了简短描述，AI也会先扩写再传给后端。seed默认不指定，每次生成都使用随机种子，保证结果多样性。

这些默认值的选择背后有明确的考量。1024:1024是大多数生图模型的原生分辨率，生成质量和速度的平衡最优。revise默认开启是因为用户描述通常过于简短，扩写能显著提升生图质量。不指定seed是因为大多数用户不需要精确复现，随机性反而能带来更多创意灵感。

用户可以通过CLI参数覆盖任何默认值。例如`--resolution=1344:768`生成宽屏图，`--revise=0`关闭prompt改写，`--seed=42`固定种子实现可复现。这种"合理默认+可选覆盖"的设计模式，既降低了新手门槛，又给高级用户留足了控制空间。

## 11.3 核心源码解析

> 源码不是写给人看的，但好的源码应该是。QClaw生图技能的代码量不大，但每一层都值得细读——因为每个模块都在解决一个具体的工程问题。

### 11.3.1 生图请求的完整流程

在深入各模块之前，先从宏观上理解整个生图流程。当AI执行`node generate.cjs --prompt="..."`后，代码经历四个阶段：

```
用户/AI 调用 generate.cjs
        │
        ▼
┌─ Step 1: 参数解析与验证 ──────────────────────┐
│  parseCliArgs() 解析 --key=value 参数         │
│  验证 prompt 必填、resolution 在白名单内      │
│  判断 task_type: text_to_image / image_to_image│
└──────────────────────────────────────────────┘
        │
        ▼
┌─ Step 2: 提交任务到 Gateway ──────────────────┐
│  gatewayPost(SUBMIT_PATH, submitBody)         │
│  submitBody = { task_type, prompt,            │
│    resolution, revise, images?, seed? }       │
│  返回 { job_id, poll_after_ms }               │
└──────────────────────────────────────────────┘
        │
        ▼
┌─ Step 3: 轮询任务状态 ────────────────────────┐
│  pollJobResult(job_id, poll_after_ms)         │
│  循环: sleep(interval) → query → 判断status   │
│  状态机: submitted → queued → running         │
│         → succeeded / failed                  │
│  失败可重试时自动重新提交一次                   │
└──────────────────────────────────────────────┘
        │
        ▼
┌─ Step 4: 下载图片到本地 ──────────────────────┐
│  downloadImageWithRetry(url, destPath)        │
│  文件名: img_<16位hex>.png                     │
│  保存到: workspace/generated-images/           │
│  输出 JSON: { success, images, prompt, ... }  │
└──────────────────────────────────────────────┘
```

这个四步流程是典型的异步任务处理模式。值得注意的细节是Step 3中包含了一个自动重试机制：当轮询返回可重试错误时，代码会等待3秒后重新提交任务并再次轮询。这是为了处理后端偶发性的临时错误，提升首次调用的成功率。

### 11.3.2 generate.cjs：主入口文件深度解析

generate.cjs是整个技能的指挥中心，负责串联所有模块完成端到端流程。它的结构清晰，分为工具函数、参数解析、任务提交、轮询等待、图片下载和结果输出六个部分。

参数解析使用自定义的`parseCliArgs`函数，而非第三方命令行库。这个设计选择体现了"最小依赖"原则——技能只需要解析`--key=value`格式的参数，不值得引入commander或yargs。解析逻辑用正则匹配`--([a-zA-Z_]+)=(.*)`，自动去除引号，自动将纯数字字符串转为Number类型：

```javascript
function parseCliArgs(argv) {
  const params = {};
  for (const arg of argv) {
    const match = arg.match(/^--([a-zA-Z_]+)=(.*)$/);
    if (match) {
      let value = match[2];
      // 去除引号包裹
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      // 纯数字自动转 Number
      if (/^\d+$/.test(value)) value = Number(value);
      params[match[1]] = value;
    }
  }
  return params;
}
```

任务类型的判断逻辑也很精炼。默认是`text_to_image`，当且仅当`--images`参数存在时切换为`image_to_image`。图生图模式下，`resolveImages`函数会把本地文件转为base64编码，URL和已有的base64字符串则直接透传。这种统一处理使得后端不需要关心图片来源格式。

最值得品味的是Step 2和Step 3之间的衔接。提交任务成功后，Gateway返回`job_id`和`poll_after_ms`。`poll_after_ms`是后端建议的首次轮询等待时间，这个值会传递给轮询函数作为初始间隔。这是一个很优雅的协议设计——后端知道当前队列负载情况，可以动态建议客户端多久后来查询，避免客户端过早轮询造成无效请求。

主流程中还有一段重试逻辑值得注意。当轮询失败且`pollResult.retryable`为true时，代码会等待3秒后用相同的submitBody重新提交任务。这个"重新提交+重新轮询"的策略比简单的"重新轮询"更有效，因为某些错误（如任务队列丢失）需要重新分配job_id才能恢复。但重试只做一次，避免无限循环。

### 11.3.3 lib/config.cjs：配置加载与验证

config.cjs虽然代码量不大，但承担了三个关键职责：定义Gateway连接参数、设定超时阈值、管理分辨率白名单。上一节已经展示了核心配置项，这里重点分析`resolveImageOutputDir`函数的实现，它体现了防御性编程的思路。

```javascript
function resolveImageOutputDir() {
  const primary = path.join(process.cwd(), 'generated-images');
  try {
    if (!fs.existsSync(primary)) fs.mkdirSync(primary, { recursive: true });
    fs.accessSync(primary, fs.constants.W_OK);
    return primary;
  } catch {
    const fallback = path.join(os.homedir(), '.qclaw', 'generated-images');
    if (!fs.existsSync(fallback)) fs.mkdirSync(fallback, { recursive: true });
    return fallback;
  }
}
```

这个函数的防御逻辑分三层。首先尝试在当前工作目录下创建generated-images目录，因为QClaw框架执行脚本时会将cwd设为agent的workspace目录，这是最理想的保存位置——用户可见、可追踪。然后用`fs.accessSync`验证目录确实可写，防止创建了但没写入权限的边缘情况。最后，如果任何步骤失败，回退到用户home目录下的`.qclaw/generated-images/`。

这种三级保障机制确保在任何环境下都能找到合适的图片保存位置。在实际运行中，Electron渲染进程的cwd可能被设为不可写路径（如根目录`/`），此时回退逻辑就至关重要。代码注释中也明确标注了这个边缘情况，说明开发者有真实经验驱动这层防护。

### 11.3.4 lib/poll.cjs：异步生图轮询机制

poll.cjs是整个技能中最具技术含量的模块。异步生图本质上是一个分布式系统中的"最终一致性"问题：客户端提交任务后，不知道后端什么时候能完成，只能通过反复查询来判断。轮询机制的设计直接决定了用户体验和系统可靠性。

轮询的核心循环结构如下：

```javascript
async function pollJobResult(jobId, initialPollMs) {
  const startTime = Date.now();
  let pollInterval = initialPollMs || DEFAULT_POLL_INTERVAL_MS;
  let consecutiveErrors = 0;

  while (Date.now() - startTime < MAX_POLL_TIME_MS) {
    await sleep(pollInterval);
    
    let result;
    try {
      result = await gatewayPost(QUERY_PATH, { job_id: jobId });
    } catch (err) {
      consecutiveErrors++;
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        return { success: false, message: '网络连接异常...', retryable: true };
      }
      continue;
    }
    
    // 处理响应...
  }
  return { success: false, message: '生图超时（超过180秒）', retryable: true };
}
```

这段代码体现了轮询机制的几个关键设计决策。

**轮询间隔的自适应调节。** 初始间隔由后端通过`poll_after_ms`指定，后续每次查询时后端可以返回新的`poll_after_ms`来动态调整间隔。如果后端判断任务即将完成，可以缩短间隔让客户端更快拿到结果；如果队列拥堵，可以加大间隔减少无效请求。这种"服务端主导节奏"的设计比固定间隔更高效。

**连续错误计数器的熔断机制。** `consecutiveErrors`变量追踪连续失败次数，阈值`MAX_CONSECUTIVE_ERRORS`设为5。每次成功响应（HTTP 200）会将计数器归零。当连续失败达到5次时，函数返回`retryable: true`的失败结果，触发上层的重新提交逻辑。注意区分两类错误：网络异常（请求未到达）和HTTP临时性错误（429/500/502/503/504）都会增加计数器，但HTTP 400/401/403等不可恢复错误会立即返回。

**状态机驱动的流程控制。** 后端任务有明确的状态机：submitted到queued到running到succeeded或failed。轮询函数只关心终态（succeeded/failed），中间状态继续等待。这种设计使得即使后端任务在队列中排队较久，客户端也不会误判为超时。

**超时兜底。** `MAX_POLL_TIME_MS`设为180秒（3分钟），这是后端建议的最大等待时间。如果3分钟内任务未完成，返回retryable超时错误。这个值是生图任务的合理上限——大多数生图在20-60秒内完成，但高负载时可能需要更久。

轮询机制的原理可以用一张状态转换图来理解：

```
提交任务 → 获得job_id
              │
              ▼
         ┌─ submitted ─┐
         │              │
         ▼              ▼
      queued         running
         │              │
         │              ├──→ succeeded (返回图片URL)
         │              │
         │              └──→ failed (返回错误信息)
         │
         └──[超过180秒未到终态]──→ 超时返回(retryable)

    任意状态:
         │
         ├──[网络错误×5]──→ 返回(retryable)
         │
         └──[HTTP 4xx]──→ 立即返回(不可恢复)
```

### 11.3.5 lib/images.cjs：图片处理与格式归一化

images.cjs负责处理图生图模式下的参考图片输入。它的核心职责是将多种图片来源（本地文件、URL、base64）统一为后端可接受的格式。这个"格式归一化"过程看似简单，但涉及的边界情况不少。

```javascript
function resolveImages(rawParam) {
  const rawImages = String(rawParam).split(',')
    .map(s => s.trim()).filter(Boolean);

  if (rawImages.length === 0) {
    return { ok: false, message: '--images 参数不能为空' };
  }
  if (rawImages.length > 3) {
    return { ok: false, message: '--images 最多支持 3 张参考图' };
  }

  const images = [];
  for (const img of rawImages) {
    if (img.startsWith('http://') || img.startsWith('https://')) {
      images.push(img);              // URL 直接透传
    } else if (img.startsWith('data:image/')) {
      images.push(img);              // Data URI 直接透传
    } else if (img.length > 1000) {
      images.push(img);              // 超长字符串视为 raw base64
    } else {
      // 本地文件路径 → 读取转 base64
      const filePath = path.resolve(img);
      if (!fs.existsSync(filePath)) {
        return { ok: false, message: `参考图片文件不存在: ${filePath}` };
      }
      const buf = fs.readFileSync(filePath);
      images.push(buf.toString('base64'));
    }
  }
  return { ok: true, images };
}
```

这段代码的判断逻辑值得细品。URL和Data URI通过前缀匹配识别，这是确定性的。但"超长字符串视为raw base64"这条规则用了一个启发式判断：长度超过1000字符的非URL非DataURI字符串，大概率是base64编码的图片数据。这个阈值的选择基于经验——普通的文件路径通常不超过500字符，而base64编码的图片数据至少几百字节起步。

最多3张参考图的限制是后端约束的体现。多图参考在图生图场景中用于风格融合或主体替换，但图片过多会增加后端处理复杂度和失败率。3张是一个经验性的平衡点。

本地文件转base64使用`fs.readFileSync`同步读取。这里用同步而非异步，是因为图片读取通常很快（本地IO），且后续所有操作都依赖这个结果，异步反而增加代码复杂度没有实际收益。这种"在合适的地方用同步"的务实态度，是好代码的标志。

### 11.3.6 lib/http.cjs：HTTP请求封装与重试策略

http.cjs封装了两个核心HTTP操作：向Gateway发送POST请求和下载图片文件。这两个操作都需要处理网络不稳定的问题，但采用了不同的策略。

`gatewayPost`函数用Node.js原生http模块发送请求，没有使用axios或node-fetch等第三方库。这是最小依赖原则的延续——技能只需要发一个简单的POST请求，不需要第三方HTTP库带来的额外体积和潜在兼容问题。请求超时通过`req.on('timeout')`事件处理，超时后调用`req.destroy()`主动断开连接，防止socket泄漏。

图片下载是整个流程中最容易出问题的环节。后端返回的图片URL可能位于CDN（Content Delivery Network，内容分发网络）上，网络波动、CDN回源延迟等都可能导致下载失败。`downloadImageWithRetry`函数实现了指数退避重试策略：

```javascript
async function downloadImageWithRetry(url, destPath, maxRetries = 2) {
  let lastErr;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await downloadImage(url, destPath);
    } catch (err) {
      lastErr = err;
      try { fs.unlinkSync(destPath); } catch { /* 清理不完整文件 */ }
      if (attempt < maxRetries) {
        const delay = 1000 * Math.pow(2, attempt); // 1s, 2s
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }
  throw lastErr;
}
```

指数退避的核心思想是每次重试的等待时间按指数增长。第一次失败后等待1秒，第二次等待2秒。这种策略比固定间隔更合理——如果第一次失败了，说明网络可能有问题，多等一会儿给网络恢复的时间。总重试次数为2次（共3次尝试），加上首次下载，最多4次尝试。

`downloadImage`函数还处理了HTTP重定向（301/302），最多跟随5次重定向。CDN经常通过重定向将请求导向最优节点，这个支持确保下载不会被重定向卡住。下载使用流式管道（`res.pipe(fileStream)`），避免将大图片全部加载到内存中。

**当所有下载尝试都失败时的降级处理也值得称道。** generate.cjs的主流程中，如果所有图片都下载失败，会返回`fallbackUrls`字段，包含后端返回的原始图片URL。这些URL有效期约1小时，用户可以在浏览器中手动打开保存。这种"宁可给用户一个手动方案，也不要让任务完全白费"的设计，体现了对用户体验的细致考虑。

## 11.4 使用方法

### 11.4.1 文生图：从自然语言到图片

文生图是技能的基础模式。用户只需要用自然语言描述想要的图片，AI会负责prompt扩写、参数选择和脚本调用。整个交互过程对用户来说就是一句话的事。

文生图的调用命令格式如下：

```bash
node "<SCRIPT_PATH>/scripts/generate.cjs" \
  --prompt="一只橘色英短猫咪慵懒地趴在阳光充足的窗台上，柔和暖色光影，摄影风格，浅景深，4K高清" \
  --resolution=1024:1024 \
  --revise=1
```

其中只有`--prompt`是必填参数，其他都有合理默认值。AI在调用前会根据SKILL.md中的构造公式，将用户的简短描述扩展为包含主体、场景、风格、光影、构图的完整prompt。这个扩写过程是生图质量的关键变量。

举个例子，用户说"画只猫"，AI不会直接把"画只猫"传给后端。它会扩写成类似"一只橘色英短猫咪慵懒地趴在阳光充足的窗台上，柔和暖色光影，摄影风格，浅景深，4K高清"这样的描述。扩写的依据是SKILL.md中的决策表：5字以内且无风格指定的输入必须扩写，需要补充主体细节、场景、风格和光影。

如果用户明确说"不要改写我的描述"，AI会传入`--revise=0`参数关闭后端的prompt改写功能，直接使用原始prompt。这种尊重用户意图的设计避免了"AI自作主张"的常见问题。

### 11.4.2 图生图：参考图加描述的混合模式

图生图模式需要用户提供参考图片和修改描述。触发条件是`--images`参数被传入，技能会自动切换到`image_to_image`模式。参考图支持本地路径、HTTP/HTTPS URL和base64编码三种格式，可以传入最多3张。

```bash
node "<SCRIPT_PATH>/scripts/generate.cjs" \
  --prompt="将参考图主体转化为古典油画风格，厚重笔触，暖色调光影，画布纹理质感" \
  --images="/Users/xxx/photos/landscape.png" \
  --resolution=1024:768
```

图生图的prompt构造策略与文生图不同。文生图的prompt侧重"从零描述"，而图生图的prompt侧重"变化方向"。用户说"把这张照片变成油画风格"，AI传入的是"将参考图主体转化为古典油画风格，厚重笔触，暖色调光影，画布纹理质感"。prompt不应该重新描述原图内容，而应该描述要做什么改变。

多张参考图的场景主要用于风格融合。例如传入两张图，一张是人物照片，一张是油画作品，prompt描述"将第一张图的人物用第二张图的油画风格重新渲染"。后端会综合两张参考图的信息生成新图片。这种能力在设计创意和艺术创作中有广泛应用。

**一个容易混淆的边界：用户发了图不等于图生图。** SKILL.md中特别强调，如果用户发图是为了"理解、分析、识别"图内容（如"这张图什么风格"），应该交给image工具处理，而不是触发生图技能。只有用户明确要求"基于这张图生成一张新图"时，才是图生图模式。这个判断由AI在调用技能前完成。

### 11.4.3 分辨率选择与质量参数

分辨率选择直接影响图片的构图和适用场景。技能内置了10种预设分辨率，覆盖5种常见比例。AI会根据用户的描述自动选择合适的分辨率，选择策略写在SKILL.md中：

| 用户描述关键词 | 选择分辨率 | 比例 | 适用场景 |
|--------------|-----------|------|---------|
| 无指定 | 1024:1024 | 1:1 | 头像、社交配图（默认） |
| "竖图"/"壁纸"/"人像" | 768:1344 | 9:16 | 手机壁纸、人像 |
| "横图"/"风景"/"桌面" | 1344:768 | 16:9 | 风景、桌面壁纸 |
| "海报" | 768:1024 | 3:4 | 竖构图海报 |
| "PPT" | 1024:768 | 4:3 | PPT配图 |

分辨率白名单的存在是为了防止用户传入后端不支持的尺寸。如果用户指定了不在白名单中的分辨率，generate.cjs会立即返回错误并列出所有支持的选项。这种"快速失败"的设计比让后端处理无效参数更高效。

seed参数是一个高级功能，用于实现结果可复现。相同的seed和prompt组合会生成相同的图片，这在需要微调prompt但保持构图基本不变时非常有用。不指定seed时，后端使用随机种子，每次生成结果不同。

### 11.4.4 错误处理与重试

生图是一个涉及网络传输、后端计算、文件下载多个环节的复杂流程，错误处理的质量直接决定用户体验。技能的错误处理体系分为三个层次。

第一层是参数验证错误，在generate.cjs的主流程开头处理。缺少prompt、分辨率不在白名单、参考图文件不存在等问题会立即返回明确的错误信息。这类错误不可重试，需要用户修正参数后重新调用。

第二层是后端任务错误，由poll.cjs在轮询过程中识别。后端返回的失败状态可能包含多种原因：内容审核不通过、prompt过长、模型内部错误等。技能会提取后端的错误信息并返回给AI，AI再根据SKILL.md中的错误处理表选择对应的建议文案。例如，审核不通过的建议是"请修改描述内容后重试，避免违规内容"。

第三层是网络层错误，包括Gateway请求失败和图片下载失败。Gateway请求失败采用连续错误计数器加熔断的策略，连续5次失败才放弃。图片下载失败采用指数退避重试，最多重试2次。如果所有下载都失败，返回后端的原始URL作为fallback，让用户可以手动保存。

```javascript
// 错误处理流程示意
try {
  submitResult = await gatewayPost(SUBMIT_PATH, submitBody);
} catch (err) {
  // 网络错误 → 立即失败
  output({ success: false, message: `提交任务失败: ${err.message}` });
  process.exit(1);
}

// 轮询失败 → 判断是否可重试
if (!pollResult.success && pollResult.retryable) {
  // 可重试错误 → 等待3秒后重新提交
  await new Promise(r => setTimeout(r, 3000));
  // 重新 submit + poll...
}

// 下载失败 → 返回原始URL
if (localPaths.length === 0) {
  output({
    success: false,
    message: '图片下载全部失败，已附上临时链接',
    fallbackUrls: pollResult.imageUrls,
  });
}
```

## 11.5 高级用法

### 11.5.1 自定义模型后端

虽然技能代码中没有直接暴露模型选择参数，但QClaw的Auth Gateway架构为后端切换提供了天然支持。Gateway作为请求代理，可以将同一个API路径路由到不同的后端模型。这意味着如果你有多个生图模型的访问权限，可以在Gateway配置层切换后端，技能代码无需任何改动。

对于需要使用自建Stable Diffusion（SD）后端的用户，理论上可以通过修改Gateway的代理规则，将`/proxy/qclaw-generate-image/submit`路由到本地SD WebUI的API端点。关键约束是后端API需要兼容技能的请求/响应格式：请求体包含`task_type`、`prompt`、`resolution`、`revise`字段，响应体包含`job_id`和`poll_after_ms`字段，查询接口返回`status`和`result_images`。

这种"协议兼容"的自定义方式比直接修改技能代码更优雅。因为技能的轮询、重试、下载逻辑都经过了实战检验，重新实现这些逻辑既费时又容易出错。保持技能代码不变，只调整Gateway路由，是风险最低的定制方案。

### 11.5.2 批量生图

技能本身不支持单次调用生成多张不同的图片，但通过脚本或AI的多步骤编排可以轻松实现批量生图。核心思路是在AI层面循环调用generate.cjs，每次使用不同的prompt或seed。

例如，生成一组不同风格的猫咪头像：

```bash
# 批量生图示例（shell循环）
for style in "油画风格" "水彩风格" "像素画风格" "3D渲染风格"; do
  node "<SCRIPT_PATH>/scripts/generate.cjs" \
    --prompt="一只猫咪头像，${style}，正方形构图" \
    --resolution=1024:1024 \
    --seed=$((RANDOM % 10000))
done
```

更实用的做法是让AI进行多步骤编排。用户说"帮我生成春夏秋冬四个季节的风景图"，AI会分四次调用生图脚本，每次使用对应季节的prompt，最后汇总所有图片路径返回给用户。这种编排能力是Agent化技能的核心优势——AI理解任务结构，自动拆分为多个子任务执行。

批量生图时需要注意频率控制。SKILL.md中明确要求"对同一描述连续重试不超过2次"，这个约束在批量场景中同样适用。如果后端返回429（Too Many Requests），说明请求过于频繁，应该增加调用间隔。一个简单的策略是在每次调用之间加入2-3秒的等待。

### 11.5.3 与其他QClaw技能联动

QClaw技能生态的设计理念是"每个技能做好一件事，通过AI编排实现复杂工作流"。生图技能可以与其他技能组合，产生1+1大于2的效果。

与腾讯文档技能联动是一个典型场景。用户说"帮我生成一张logo并保存到腾讯文档"，AI会先调用生图技能生成图片，获得本地文件路径后，再调用腾讯文档技能上传图片到云端文档。整个流程对用户来说就是一句话，但背后经历了生图、下载、上传三个步骤。

与云存储备份技能联动可以实现自动云备份。生图技能将图片保存到本地workspace后，云存储技能可以自动将新图片上传到腾讯SMH云存储，生成可在小程序中查看的链接。这种联动让生成的图片不会因为本地文件清理而丢失。

与邮件技能联动可以分享生成的图片。用户说"生成一张生日贺卡发给我朋友"，AI先生成贺卡图片，然后通过邮件技能将图片作为附件发送到指定邮箱。这种"创意生成即分享"的工作流，在节日祝福、营销素材等场景中非常实用。

技能联动的技术基础是QClaw的workspace共享机制。所有技能都在同一个workspace目录下工作，生图技能的输出路径（`generated-images/`）对其他技能是可见的。AI通过解析生图技能返回的JSON中的`images`数组，获取图片的绝对路径，然后将其作为参数传递给下一个技能。这种"文件路径接力"的设计简单有效，不需要技能之间直接通信。

## 11.6 参考资源

以下是本章涉及的所有文件和资源的完整路径，方便你查阅源码或延伸学习。

**技能文档：** `~/.qclaw/skills/qclaw-generate-image/SKILL.md`

这是技能的"说明书"，AI在每次调用生图技能前都会读取这个文件。SKILL.md定义了触发条件、prompt构造规范、输出格式模板、错误处理表等所有AI需要遵守的规则。如果你想理解AI为什么这样构造prompt而不是那样，答案通常在这个文件里。

**主脚本：** `~/.qclaw/skills/qclaw-generate-image/scripts/generate.cjs`

生图流程的入口和指挥中心。负责参数解析、任务类型判断、流程编排（提交-轮询-下载-输出）和错误处理。约150行代码，是理解整个技能运作方式的起点。

**配置模块：** `~/.qclaw/skills/qclaw-generate-image/scripts/lib/config.cjs`

所有配置参数的单一来源。包括Gateway连接信息、超时阈值、分辨率白名单和图片输出目录解析逻辑。修改任何配置参数都应该在这里进行。

**轮询模块：** `~/.qclaw/skills/qclaw-generate-image/scripts/lib/poll.cjs`

异步任务轮询的核心实现。包含状态机判断、连续错误计数熔断、超时兜底等机制。如果你需要调整轮询策略（如增加重试次数或修改间隔），修改这个文件。

**图片模块：** `~/.qclaw/skills/qclaw-generate-image/scripts/lib/images.cjs`

图生图模式的图片预处理模块。负责将本地文件、URL、base64等多种格式统一为后端可接受的格式。如果需要支持新的图片来源格式（如OSS路径），扩展这个模块。

**HTTP模块：** `~/.qclaw/skills/qclaw-generate-image/scripts/lib/http.cjs`

底层HTTP通信封装。包括Gateway POST请求和图片下载（含重定向和指数退避重试）。这个模块是整个技能网络层的基础设施。

**QClaw官方文档：** https://docs.openclaw.ai

QClaw生态的官方文档站点，包含技能开发指南、Gateway配置说明和更多技能的详细信息。

**源码结构总览图：**

```
qclaw-generate-image/
│
├── SKILL.md ──────────── AI行为规范文档
│                         触发条件 | prompt构造 | 输出模板 | 错误处理
│
└── scripts/
    │
    ├── generate.cjs ──── 主入口（流程编排）
    │      │
    │      ├── 参数解析 (parseCliArgs)
    │      ├── 任务类型判断 (text_to_image / image_to_image)
    │      ├── Step 1: 提交任务 → gatewayPost(SUBMIT_PATH)
    │      ├── Step 2: 轮询结果 → pollJobResult(job_id)
    │      ├── Step 3: 下载图片 → downloadImageWithRetry(url)
    │      └── Step 4: 输出JSON结果
    │
    └── lib/
        │
        ├── config.cjs ── 配置中枢
        │      Gateway地址 | 超时参数 | 分辨率白名单
        │      图片输出目录解析（含降级逻辑）
        │
        ├── poll.cjs ──── 轮询引擎
        │      状态机: submitted→queued→running→succeeded/failed
        │      熔断: 连续5次错误 → retryable
        │      超时: 180秒兜底
        │
        ├── images.cjs ── 图片格式归一化
        │      本地文件→base64 | URL透传 | Data URI透传
        │      最多3张参考图限制
        │
        └── http.cjs ──── HTTP基础设施
               gatewayPost: Gateway POST请求
               downloadImage: 流式下载（支持重定向）
               downloadImageWithRetry: 指数退避重试
```

---

**本章到这里就结束了。** 我们从SKILL.md的触发逻辑开始，走过config.cjs的配置体系，拆解了generate.cjs的四步流程，深入了poll.cjs的轮询状态机，最后覆盖了使用方法和高级场景。如果你只记一件事，请记住：生图不是一步到位的魔法，而是一个包含提交、轮询、下载、重试的完整工程流程，每个环节都有明确的设计逻辑和兜底策略。

如果你觉得这一章对你有帮助，收藏起来方便以后查阅源码结构图和配置参数速查表。有任何问题或想讨论的，评论区见。关注我，持续追更这个系列——下一章我们会聊一个容易被技术人忽视但越来越重要的话题：AI生成内容的版权与法律风险。生图技能让你能轻松创造图片，但这些图片的著作权归属、商用许可边界、侵权风险防范，你真的清楚吗？第十二章，怕浪猫带你从代码回到现实，聊聊技术背后的法律红线。

> 第十二章预告：版权与法律——AI生成的图片到底归谁？
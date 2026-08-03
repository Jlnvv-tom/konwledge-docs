---
sidebar_position: 3
---

# 第三章 Midjourney 完全指南

> 90%的人用Midjourney只会输入一句话，但10%的高手用它月入过万。差距不在天赋，在于你是否真正读懂了这台机器。

我是怕浪猫，一个在AI绘画坑里摸爬滚打了上千小时的技术写手。过去两年我见证了Midjourney从V4到V6.1的每一次进化，也踩过无数个参数坑。这一章我会把Midjourney从注册到高阶实战的完整链路拆开给你看，不废话，全是干货。

Midjourney成立于2022年，总部位于美国旧金山，由David Holz创立。它不是开源项目，而是一个通过Discord平台提供服务的商业化AI图像生成工具。底层技术基于Latent Diffusion Model（潜在扩散模型），通过对大规模图文对训练数据的学习，实现从文字描述到高质量图像的生成。与Stable Diffusion和DALL-E并称为当前三大AI图像生成工具，但在艺术性和美学品质上，Midjourney长期占据口碑领先位置。

理解Midjourney的生图流程图，有助于你在使用时建立正确的心智模型。整个流程可以简化为五个阶段：文本编码（Text Encoding）将你的Prompt转化为语义向量，潜在空间初始化（Latent Initialization）生成随机噪声，扩散去噪（Denoising）在语义向量的引导下逐步去除噪声，潜在空间到像素空间解码（Decoding）将去噪后的潜在表示转化为像素图像，最后超分辨率增强（Super Resolution）提升图像清晰度。你写的每一个词都在第一阶段影响语义向量，进而引导整个去噪过程的方向。

## 3.1 注册与入门

### Discord账号注册与Midjourney服务器加入

Midjourney不是独立App，它运行在Discord这个通讯平台上。Discord最初为游戏玩家设计，支持文字、语音和机器人交互，Midjourney就是其中一个功能强大的Bot（机器人）。

注册流程分为三步，但每步都有细节值得注意。

第一步，访问discord.com下载客户端或使用网页版，用邮箱注册一个Discord账号。建议使用常用邮箱，因为Discord会通过邮箱验证账号状态。中国大陆地区访问Discord网页版可能需要网络代理工具。桌面客户端体验更稳定，也支持iOS和Android移动端。

第二步，登录后点击左侧导航栏的"探索公开服务器"按钮，搜索"Midjourney"并点击加入。加入后可看到频道列表，包括公告区、新手房间、画廊和帮助中心等分区。建议先浏览announcements获取最新功能更新和使用须知。

第三步，进入Midjourney服务器后，你会看到数十个newcomer-rooms（新手房间），任意选择一个进入即可开始创作。房间编号从1到50不等，功能相同，选人数较少的加载更快。

需要注意的是，Midjourney的免费试用政策时有调整。目前新用户需要订阅才能使用生图功能，免费额度已大幅缩减。建议先完成订阅再深入操作，后面怕浪猫会详细讲订阅方案的选择策略。

### 订阅计划选择（Basic/Standard/Pro/Mega）

Midjourney提供四档订阅计划，每档对应不同的生成时长和并发权限。

**Basic Plan**每月10美元，提供约200张快速生成额度（Fast GPU Time），用完即止。适合刚入门、还在摸索阶段的新用户。但200张图很快就会耗尽，因为每次/imagine命令会生成4张候选图，一次迭代就消耗4个额度。

**Standard Plan**每月30美元，包含15小时快速生成时长和无限松弛生成（Relaxed GPU Time）。松弛模式生成速度较慢，通常需要等待1-10分钟，但不限量。这个方案适合大多数中度使用者，怕浪猫推荐新手直接跳过Basic选这个。

**Pro Plan**每月60美元，包含30小时快速时长、12小时超快速时长（Super Fast Mode），以及隐身生成（Stealth Mode）。隐身模式让你的生图过程和结果对他人不可见，这对商业用户和设计师非常重要。

**Mega Plan**每月120美元，60小时快速时长加24小时超快速时长，适合团队和重度商业用户。

下面是订阅计划对照表：

| 计划 | 月费 | Fast时长 | Relaxed | Stealth | 并发任务 |
|------|------|----------|---------|---------|----------|
| Basic | $10 | ~200张 | 不支持 | 不支持 | 3个 |
| Standard | $30 | 15h | 无限 | 不支持 | 3个 |
| Pro | $60 | 30h | 无限 | 支持 | 6个 |
| Mega | $120 | 60h | 无限 | 支持 | 12个 |

订阅操作在Midjourney官网或Discord内输入/subscribe命令完成，系统会弹出支付链接，支持信用卡和Stripe支付。

### 新手频道使用方法

进入Midjourney服务器后，newcomer-rooms是新手的主战场。这些频道有几百人同时在线生图，消息滚动极快，你的作品很容易被淹没。

在公共频道生图有一个重要特点：你生成的所有图片默认对所有人可见，其他用户也可以看到你的Prompt（提示词）并复用。这其实是最好的学习方式——怕浪猫早期就是通过观察高手的提示词组合来快速提升的。公共频道里每天产生数万张图，你可以按时间线浏览，遇到喜欢的作品直接复制其Prompt，在此基础上修改迭代。这种偷师过程比任何教程都高效。

另一个实用技巧是使用反应表情（Reaction）来标记你喜欢的作品。在别人生成结果上右键添加表情，这张图会记录到"已标记消息"中方便查阅。许多资深用户通过浏览热门作品追踪当前的Prompt趋势。

操作时，在输入框敲入/imagine，系统会自动补全命令。在prompt后面输入你的描述文字，按回车发送。大约30-60秒后，Bot会返回一张四宫格图（4格预览图），每张图左下角有编号标识。

如果你想专注创作不被打扰，可以在Discord中创建自己的服务器，然后把Midjourney Bot邀请进去。操作方法是：在自己的服务器里点击服务器设置，进入Integrations页面，选择Midjourney并授权。这样你就有了一个私人生图空间，所有生成结果只属于你。

> 提示词是种子，参数是土壤。同样的种子撒在不同土壤里，长出来的果实天差地别。

## 3.2 基础操作

### /imagine命令详解

/imagine是Midjourney最核心的命令，所有图像生成都从这里开始。完整命令格式如下：

```
/imagine prompt: <描述文字> <后缀参数1> <后缀参数2> ...
```

一个实际的例子：

```
/imagine prompt: a cute cat wearing sunglasses on the beach, photorealistic --ar 16:9 --q 2 --v 6.1
```

命令的核心结构分为两段。前半段是prompt（提示词），用自然语言描述你想看到的画面。后半段是参数段，以双连字符开头，控制图像的技术属性。两段之间用空格分隔，参数段不区分先后顺序但必须放在Prompt文字之后。

Prompt的书写有长度限制。在V6版本中，Prompt最大支持约6000个字符，但实际使用中超过100个词的Prompt往往会产生语义稀释效应——模型难以判断哪些词是重点。怕浪猫建议将核心Prompt控制在30到60个词之间，把最重要的描述放在前面，次要的细节放在后面。Midjourney的注意力机制（Attention Mechanism）对Prompt前段的权重更高，这个特性要求你在组织语言时有明确的优先级意识。

Prompt的书写有几个关键原则。第一，主体优先，把画面中最重要的元素放在最前面，权重最高。第二，风格词紧随其后，指定艺术风格或摄影类型。第三，细节描述放中间，包括构图、光线、色彩、氛围。第四，排除内容放末尾，用--no参数处理。

Midjourney对英文Prompt的理解远优于中文，建议始终用英文书写提示词。关键词之间用逗号分隔，权重从前往后递减，这个顺序很重要。

Prompt书写模板参考：

```
[主体描述], [风格/媒介], [构图视角], [光线氛围], [色彩情绪], [细节修饰], --参数
```

一个结构化的实战Prompt示例：

```
/imagine prompt: a young woman in white dress standing in a field of sunflowers, oil painting style, wide angle shot, golden hour lighting, warm tones, highly detailed, impressionist --ar 3:2 --v 6.1 --stylize 400
```

### U1-U4放大与V1-V4变体操作

当四宫格图生成后，下方会出现两排按钮：U1、U2、U3、U4和V1、V2、V3、V4。

U按钮代表Upscale（放大），点击U1会将第一张候选图单独放大为高清版本。早期版本中U按钮的作用是提升分辨率，但在V5之后的版本里，默认生成已经是高分辨率，U按钮更多是"选中并分离"的作用。

V按钮代表Variation（变体），点击V1会基于第一张图的风格和构图，再生成4张相似的变体图。这是迭代优化作品的核心手段——当某张图接近你想要的效果但还差一点时，用V按钮微调。

除了U和V，还有一个重要的Web按钮（在V5后版本中为文件夹图标），点击后跳转到Midjourney网页端，可以在浏览器中对图片进行进一步编辑、下载和管理。

放大后还会出现一组新按钮。Make Variations会基于放大图生成变体。Upscale to 2x和Upscale to 4x分别将图像放大到2倍和4倍分辨率。Zoom Out 2x执行画布扩展，保持主体不变的情况下延展画面边界。Pan方向按钮（上下左右）可以将画面向指定方向延伸。

整个迭代流程可以概括为：生成四宫格 -> 选中最满意的 -> U放大 -> V变体细化 -> 再次选择放大 -> 直到满意为止。这个循环过程就是Midjourney创作的标准工作流。

迭代次数没有上限，但怕浪猫建议每个作品控制在3到5轮迭代内。过多的迭代容易让画面陷入"过度优化"的陷阱——细节越来越精致但整体越来越平庸。当你发现自己在一轮迭代中找不到明显更好的候选图时，说明已经到达了当前Prompt的上限，此时应该回到Prompt层面修改描述词，而不是继续在V按钮上死磕。

Vary Region是V6新增的重要功能，允许你框选画面中的局部区域进行重绘，而不影响其他部分。这个功能类似于Photoshop中的生成式填充，对于修正画面中的小瑕疵非常有用。比如人物面部表情不理想、手指数量错误、背景中出现不必要的元素等，都可以通过Vary Region精准修复。

### 图片质量升级

Midjourney在V6版本之后，默认输出的放大图分辨率已经相当高，但很多时候仍需要更高质量的输出。

内部升级方面，V6.1版本提供了Upscale（Creative）和Upscale（Subtle）两个选项。Creative在放大时会增加创意细节，模型会在放大过程中补充更多纹理和信息，适合需要更多画面信息的情况。Subtle则保持原图风格不变，仅提升清晰度，不做任何创意性添加。

关于分辨率的具体数值，V6.1默认生成的四宫格图中每张图约1024x1024像素。使用U按钮放大后约为1024x1024到2048x2048像素（取决于宽高比）。再使用2x或4x放大，最高可达到4096x4096像素。对于印刷输出而言，300dpi下4096像素约等于34厘米的物理尺寸，基本满足大多数印刷需求。

Web端还提供了下载原始分辨率的功能。在Midjourney网页端的个人Gallery中找到目标图片，点击下载按钮即可获取最高质量版本。建议长期创作通过Web端管理作品，比Discord内更方便检索和分类。

外部升级方面，常用的工具包括Topaz Gigapixel AI、Real-ESRGAN和Magnific AI等超分辨率工具。这些工具通过AI算法将图像放大2到8倍，同时补充合理的细节。怕浪猫推荐先用Midjourney内部放大到最大，再根据需要用外部工具二次提升。

参数层面，--q参数控制生成质量。--q 1为默认值，--q 2会花更多GPU时间生成更高质量的图。但在V6版本中--q参数的影响已不如早期版本明显，默认质量已经足够好。

### 后缀参数详解

后缀参数是控制Midjourney生图行为的精密旋钮。掌握这些参数，才能真正驾驭这台机器。

**--ar（Aspect Ratio，宽高比）**

控制输出图像的宽高比例。默认值1:1（正方形），常用值包括16:9（宽屏）、9:16（竖屏）、3:2（摄影比例）、2:3（竖版摄影）。

```
/imagine prompt: mountain landscape at sunset --ar 16:9
```

宽高比对构图影响巨大。16:9适合风景和电影画面，9:16适合手机壁纸和人物全身像，3:2适合模拟单反相机的自然拍摄感。

**--v（Version，版本号）**

指定使用哪个版本的模型。当前最新为--v 6.1，每个版本在风格、细节和理解力上都有差异。V5系列偏向摄影写实，V6系列在写实基础上大幅提升了文字渲染和对复杂Prompt的理解能力。建议默认使用最新版本，除非你有特定的风格需求。

**--q（Quality，质量）**

控制生成质量与耗时。--q 1为默认，--q 2为高质量（耗时翻倍），--q 0.5为快速模式（质量略降）。V6版本中此参数效果已减弱。

**--chaos（混沌度）**

控制生成结果的随机性和差异性，范围0-100。默认值为0，四张候选图风格接近。设为100时，四张图可能呈现完全不同的风格和构图。

```
/imagine prompt: abstract digital art --chaos 50 --v 6.1
```

混沌度高时适合头脑风暴和灵感探索，低时适合精确控制。怕浪猫建议初学者从0开始，逐步提高到10-30微调。

**--stylize（风格化强度）**

控制Midjourney美学的施加程度，范围0-1000（V6默认100）。值越低，结果越忠于你的描述文字。值越高，Midjourney越会加入自己的审美判断，画面更精致但也可能偏离你的意图。

```
/imagine prompt: a portrait of an old man --stylize 750 --v 6.1
```

**--style（风格倾向）**

在V6中主要用于指定风格方向。--style raw会减少Midjourney的默认美化，产出更原始、更接近描述文字的图像。适合摄影类和需要精确控制的场景。

**--no（排除词）**

从生成结果中排除特定元素。

```
/imagine prompt: a modern living room --no furniture, people
```

这会告诉模型在画面中避免出现家具和人物。

**--seed（随机种子）**

每次生成都有一个随机种子值，用--seed固定它可以在相同Prompt下复现相似结果。范围0-4294967295。

```
/imagine prompt: a red sports car --seed 12345 --v 6.1
```

**--tile（无缝拼接）**

生成可以无缝拼接的图案，适合做壁纸和纹理素材。

**--stop（提前停止）**

控制生成过程提前结束，范围10-100。值越低画面越模糊、越抽象，可以用来制造特殊艺术效果。

**--repeat（重复生成）**

一次性生成多组结果，--repeat 4会连续执行4次生图命令，适合快速批量探索。

参数速查表：

| 参数 | 功能 | 取值范围 | 默认值 |
|------|------|----------|--------|
| --ar | 宽高比 | 任意比例 | 1:1 |
| --v | 模型版本 | 1-6.1 | 6.1 |
| --q | 质量 | 0.25-2 | 1 |
| --chaos | 混沌度 | 0-100 | 0 |
| --stylize | 风格化 | 0-1000 | 100 |
| --style raw | 原始风格 | 开关 | 关 |
| --no | 排除词 | 文本 | 无 |
| --seed | 随机种子 | 0-4294967295 | 随机 |
| --tile | 无缝拼接 | 开关 | 关 |
| --stop | 停止点 | 10-100 | 100 |
| --repeat | 重复次数 | 1-40 | 1 |

> 理解参数的最佳方式不是背诵，而是把每个参数都调到极端值试一次，看画面怎么变。理论十遍不如动手一遍。

## 3.3 进阶技巧

### 图生图与混合生图

图生图（Image-to-Image）是Midjourney的高频功能之一。操作方式是在/imagine命令的Prompt中，开头粘贴一张图片的URL链接，后面跟文字描述。模型会以这张图作为视觉参考，结合文字描述生成新图像。

```
/imagine prompt: https://cdn.example.com/photo.jpg a cyberpunk version of this scene --ar 16:9 --v 6.1 --iw 1.5
```

--iw（Image Weight，图片权重）参数控制参考图的影响力，范围0-2（V6中为0-3）。值越高，生成结果越接近参考图。值越低，文字描述的权重越大。

图生图的关键在于理解权重平衡。--iw 2意味着模型高度忠实于参考图的构图和风格，适合在原图基础上做局部修改或风格转换。--iw 0.5则让模型更自由地解读文字，参考图只提供微弱的视觉暗示。

混合生图使用/blend命令，可以将2到5张图片融合为一张。操作时上传多张图片，模型会分析每张图的视觉特征并生成融合结果。

```
/blend image1.jpg image2.jpg image3.jpg --ar 16:9 --v 6.1
```

/blend不接文字描述，完全依赖图片之间的视觉融合。适合做风格迁移、元素组合和创意混搭。比如把一张人物照片和一张油画风格图blend，会得到油画风格的人物像。

需要注意的是，/blend在V6中对图片特征的提取能力有了显著提升，融合过渡更自然。但仍建议选择主体明确、背景简洁的图片作为输入，复杂场景的融合效果往往不够理想。

/blend的融合原理可以简单理解为特征空间的加权平均。模型将每张输入图片编码到潜在空间（Latent Space）中，然后在这些潜在表示之间进行插值，最终解码为一张新图像。这意味着融合结果不是简单的图层叠加，而是在语义层面上的真正融合。两张风格差异极大的图片blend在一起时，结果可能出乎意料——这既是创意来源也是不可控性的体现。

图生图和混合生图在实际工作中的一个重要应用是风格迁移。你可以准备一张内容图和一张风格图，通过blend或图生图将风格图的艺术特征施加到内容图上。这种技术在品牌视觉统一和概念设计快速迭代中非常实用。

### 通过图片反推关键词

/describe是Midjourney提供的一个反向工程工具。你上传一张图片，它会返回四组Prompt描述，帮助你理解这张图的视觉特征和可能的关键词组合。

```
/describe <上传图片>
```

这个功能在实际工作中的用途很广。当你看到一张喜欢的图但不知道怎么用Prompt描述时，/describe能给你方向。它返回的Prompt可以直接用于/imagine命令来生成类似风格的图。

但要注意，/describe的结果并非完美还原。它更像是"猜图"，会遗漏一些细节，也会加入一些原图中不明显的描述。怕浪猫建议把它当作灵感来源而非精确工具，取其中有用的关键词片段融入你自己的Prompt中。

一个高效工作流：找目标风格图 -> /describe反推 -> 选最接近的描述 -> 修改优化 -> /imagine生成 -> 对比调整。这个循环能快速帮你建立风格Prompt模板。

/describe返回的四组Prompt各有侧重。第一组通常是简洁概括型，用词少但抓住了核心风格。第二组和第三组往往更详细，包含更多技术和材质描述。第四组有时会加入一些创意性的解读。怕浪猫建议四组都试一遍，提取最好的关键词片段重新组合成你自己的Prompt。

这个功能还有一个隐藏用法：质量诊断。如果你自己写的Prompt生成的效果不理想，可以用/describe分析你心目中理想效果的参考图，对比两份Prompt的差异，往往能发现你遗漏的关键风格词或参数设置。

### Seed值在复现中的应用

每次Midjourney生成图像时，系统会分配一个随机种子值。即使Prompt完全相同，不同的Seed会产生不同的结果。固定Seed值是实现结果复现的关键。

获取Seed值的方法是在生成的图片上点击右上角的信封图标（Envelope），Midjourney Bot会私信告诉你这张图的Seed号。或者使用/show命令配合Job ID来查看。

Seed的核心应用场景是"保持一致性"。假设你生成了一个很满意的角色，想用同一角色在不同场景中出现。你可以固定Seed值，修改场景描述，模型会尽量保持角色的核心特征一致。

```
/imagine prompt: a young girl with blue hair in a forest --seed 8843271 --v 6.1
/imagine prompt: a young girl with blue hair in a city street --seed 8843271 --v 6.1
```

但需要说明的是，Seed复现并非100%精确。Midjourney的生成过程包含一定程度的不可控随机性，即使Seed和Prompt完全一致，结果也会有细微差异。Seed更多是"引导方向一致"而非"像素级复现"。

对于需要严格角色一致性的场景，可以结合--cref（Character Reference，角色参考）参数。在V6中，--cref接受一张图片URL作为角色参考，--cw（Character Weight）控制角色特征的保留程度。--cw 100会尽量保留角色的面部、发型和服装全部特征。--cw 0则仅保留面部特征，允许服装和配饰自由变化。

除了--cref，V6还引入了--sref（Style Reference，风格参考）参数。与--cref锁定角色不同，--sref锁定的是画面风格。你提供一张风格参考图，模型会提取其色调、笔触、构图倾向等风格特征，应用到新生成的图像中。

```
/imagine prompt: a girl reading a book in a cafe --sref https://cdn.example.com/style-ref.jpg --sw 500 --v 6.1
```

--sw（Style Weight）控制风格参考的影响力，范围0-1000。这个参数在系列作品创作中极为有用——固定--sref可以让一整批作品保持统一的视觉风格，这在品牌设计和系列插画项目中价值巨大。

理解Seed、--cref和--sref三者的关系很重要。Seed控制的是底层随机性，影响画面整体的方向。--cref控制角色的具体特征，是跨图片角色一致性的核心工具。--sref控制风格走向，是跨图片风格一致性的核心工具。三者可以组合使用，但在组合时需要注意权重平衡，避免多个参考信号互相冲突导致画面混乱。

```
/imagine prompt: a girl walking on the beach --cref https://cdn.example.com/character.jpg --cw 100 --v 6.1
```

### 灯光与风格词的高级用法

灯光是提升画面质感最有效的手段之一。Midjourney对灯光描述的理解非常深入，精确的灯光词能彻底改变画面氛围。

常用灯光词及其效果：

**Golden Hour**：黄金时刻，日出或日落时的温暖侧光，画面呈暖黄色调，适合人像和风景。

**Blue Hour**：蓝色时刻，日落后天光尚未完全消失的时间段，画面呈冷蓝色调，适合城市和情绪化场景。

**Studio Lighting**：影棚布光，均匀可控的专业灯光，适合产品摄影和商业人像。

**Rembrandt Lighting**：伦勃朗光，经典油画式侧光，面部形成三角光斑，适合戏剧性人像。

**Volumetric Lighting**：体积光，光线穿过雾气或尘埃形成可见光束，营造神圣感或神秘感。

**Neon Lighting**：霓虹灯光，赛博朋克风格的粉紫蓝色调，适合未来主义场景。

**Backlight**：逆光，从主体后方照射，形成轮廓光和剪影效果，适合高对比度画面。

风格词方面，Midjourney支持极其丰富的艺术风格描述。摄影类可以用35mm film、Polaroid、fujifilm、kodak portra等胶片类型来控制色调。绘画类可以用oil painting、watercolor、ink wash、gouache等媒介来定义质感。数字艺术类可以用3D render、octane render、unreal engine、pixel art等来指定技术路线。

镜头语言也是重要的一组风格控制词。wide angle shot（广角）适合表现宏大的场景空间感，macro shot（微距）适合呈现细节质感，bird's eye view（鸟瞰）和worm's eye view（虫瞰）分别从极端的高低角度改变画面的叙事感。Dutch angle（荷兰角）让画面倾斜，常用于表现紧张和不安的情绪。

色彩控制可以通过具体的色彩方案词来实现。monochromatic（单色调）、complementary colors（互补色）、analogous colors（邻近色）、muted colors（低饱和度色调）、vibrant colors（高饱和度色调）等词能让模型在色彩层面做出精确响应。结合具体的色相描述如teal and orange（青橙色调）、pastel pink（柔和粉色）等，可以进一步锁定色彩方向。

一个高级Prompt通常会组合使用灯光词和风格词：

```
/imagine prompt: a portrait of an elderly fisherman, weathered face, Rembrandt lighting, shot on 35mm film, kodak portra 400, shallow depth of field, --ar 2:3 --v 6.1 --stylize 200 --style raw
```

这个Prompt中，Rembrandt lighting定义了戏剧性侧光，35mm film和kodak portra 400定义了胶片质感和色彩倾向，shallow depth of field定义了浅景深虚化效果。每个词都在精确控制画面的一个维度。

> 同一个场景换个灯光词就是换了个世界。灯光不是画面的一部分，灯光是画面的导演。

## 3.4 实战案例

### Q版3D人物生成

Q版3D角色的核心特征是头身比夸张（通常1:1或1:2）、五官圆润简化、材质偏塑料或黏土质感。这类角色在游戏UI、品牌吉祥物和社交表情包中应用极广。

实战Prompt：

```
/imagine prompt: a cute chibi character, big head, small body, wearing oversized hoodie and sneakers, 3D render, pixar style, octane render, soft studio lighting, pastel colors, clean white background, --ar 1:1 --v 6.1 --stylize 300
```

关键解析：chibi（Q版）是核心风格锁定词，3D render和pixar style定义了三维动画质感，octane render确保渲染品质，soft studio lighting保证光线均匀柔和，clean white background便于后期抠图。

迭代策略：第一轮生成后选择表情和姿势最满意的一张，用U按钮放大，再用V按钮生成变体微调。如果角色整体满意但需要更换服装颜色，可以在放大后用Vary Region功能框选服装区域，修改Prompt中的颜色描述。

Q版角色生成的常见问题及解决方案：第一，头身比不正确——在Prompt中明确写出head-body ratio 1:2这类量化描述可以有效改善。第二，面部表情僵硬——添加expressive face或big smile等情绪词。第三，材质不够Q弹——在风格词中加入soft clay texture或vinyl toy质感描述。第四，背景杂乱干扰主体——强化clean white background描述，必要时用--no background元素排除。

材质词对Q版3D角色的影响极大。同样的角色描述，加上"clay render"会得到黏土质感，加上"plastic toy"会得到塑料玩具质感，加上"fuzzy felt"会得到毛毡质感。理解材质词的视觉差异是控制角色呈现效果的关键能力。

### 泡泡玛特风格头像

泡泡玛特（Pop Mart）风格的盲盒玩偶头像，核心特征是光面材质、精致五官、潮玩质感和磨砂底座。

实战Prompt：

```
/imagine prompt: a pop mart blind box toy figure, cute girl with pink hair, glossy vinyl material, detailed face, sparkle eyes, wearing streetwear, standing on a matte base, studio lighting, product photography, clean background, --ar 3:4 --v 6.1 --stylize 500
```

关键解析：pop mart blind box toy figure直接锁定风格类型，glossy vinyl material定义了光面PVC材质感，product photography和studio lighting组合确保商业产品图的灯光质感，matte base模拟真实盲盒的磨砂底座。

进阶技巧是加入品牌系列感描述。比如添加"series 1, limited edition"这类词，会让模型生成更有品牌包装感的画面。如果需要特定主题，可以在角色描述中加入季节或节日元素，比如Christmas edition或Halloween version。

泡泡玛特风格的一个关键技术细节是控制材质光泽度。glossy vinyl material会让模型渲染出高光反射的PVC质感，这是盲盒玩具最核心的视觉特征。如果你想要哑光质感，可以替换为matte finish或soft touch material。配合studio lighting可以精确控制高光的位置和强度，让产品看起来更有商业摄影的品质感。

批量制作一整套泡泡玛特风格头像时，建议使用统一的Prompt模板，仅更换角色描述部分。同时固定--seed值和--stylize参数，确保整套作品的渲染风格、灯光角度和材质质感高度一致。这样产出的系列作品有品牌统一感，适合社交媒体头像或虚拟商品展示。

### B端设计3D图标

B端（Business-end）设计的3D图标要求风格统一、简洁专业、适合界面使用。这类图标通常用于企业级应用的空状态插画、功能引导和仪表盘装饰。

实战Prompt：

```
/imagine prompt: 3D icon of a cloud storage symbol, isometric view, soft gradient blue and purple color scheme, clay render style, soft shadows, minimal design, white background, UI asset, --ar 1:1 --v 6.1 --stylize 150
```

关键解析：isometric view（等距视角）是B端3D图标的标准视角，clay render style确保黏土质感的柔和外观，soft shadows保证图标的轻盈感，minimal design控制画面复杂度。

批量制作时，保持风格统一是关键。建议固定所有参数，仅替换主体描述词。比如把cloud storage symbol替换为data analytics chart、security shield、team collaboration等。配合--seed固定种子值，可以确保整套图标的渲染风格高度一致。

B端3D图标的色彩方案需要与企业品牌色调协调。如果目标企业使用蓝色系主色调，可以在Prompt中指定soft gradient blue and purple color scheme。如果是绿色系品牌，替换为mint green and white color scheme。色彩描述越具体，模型输出越可控。避免使用抽象的色彩描述如beautiful colors，这类模糊词汇会让模型自由发挥，导致不可控的结果。

图标尺寸和视角的一致性也需要注意。isometric view是B端3D图标最常用的视角，因为它能同时展示图标的正面和顶面，提供更多的视觉信息。同一套图标应使用相同视角描述，否则放在一起会参差不齐。

```
/imagine prompt: 3D icon of a data analytics chart, isometric view, soft gradient blue and purple color scheme, clay render style, soft shadows, minimal design, white background, UI asset, --ar 1:1 --v 6.1 --stylize 150 --seed 8843271
```

### 电商海报制作

电商海报需要强烈的视觉冲击力和明确的商业信息传达。Midjourney在这方面的优势是快速产出高质量视觉素材，再配合设计软件完成文字排版。

实战Prompt：

```
/imagine prompt: a luxury perfume bottle on a podium, surrounded by floating flowers and golden particles, dramatic spotlight, dark background with bokeh, commercial photography, premium brand aesthetic, --ar 9:16 --v 6.1 --stylize 400 --style raw
```

关键解析：podium（展示台）赋予产品仪式感，floating flowers和golden particles增加画面层次和动感，dramatic spotlight突出主体，dark background with bokeh营造高端氛围，commercial photography和premium brand aesthetic确保商业品质。

海报制作的工作流通常是：Midjourney生成视觉主体 -> 用Photoshop或Canva添加文字和Logo -> 最终排版输出。Midjourney在文字渲染方面V6版本有大幅提升，但复杂中文文字仍然不可靠，建议图像用MJ生成，文字用设计软件后期添加。

对于不同平台的尺寸需求，调整--ar参数即可。主图用1:1，详情页用3:4，轮播图用16:9，Stories用9:16。电商场景中一个实用技巧是用--repeat 4一次性生成多组方案，从16张候选图中挑选最佳方案，大幅提高选稿效率。

电商海报的视觉层次控制是另一个关键点。一个好的商业海报需要三个层次：主体层（产品本身）、装饰层（辅助元素）和氛围层（背景和色调）。在Prompt中按层次结构组织描述词，可以帮助模型准确理解画面构成。主体描述放最前面确保权重最高，装饰元素居中，氛围描述放在后段。

不同品类电商海报的风格差异很大。美妆类偏好柔和光线和干净背景，3C数码类偏好科技感和暗调背景，食品类偏好温暖色调和质感细节。针对不同品类选合适的风格词组合，是电商海报出图质量的核心变量。

### 二次元模式生成

Midjourney在二次元（Anime）风格方面有专门的模型版本。使用--v 6配合Niji模式可以生成高质量二次元图像。Niji是Midjourney与Spellbrush合作开发的动漫专用模型。

```
/imagine prompt: a girl with silver hair holding a katana, standing on a rooftop at night, city lights in background, anime style, detailed eyes, wind blowing hair, dramatic atmosphere --niji 6 --ar 16:9
```

关键解析：--niji 6激活二次元专用模型，anime style和detailed eyes强化动漫特征，dramatic atmosphere定义情绪基调。Niji模型对日语Prompt也有不错的理解力，可以用日文关键词辅助。

Niji模式有几个独有的风格参数。--style expressive生成更具表现力的画风，线条更自由。--style cute偏向萌系风格，适合Q版和日常场景。--style scenic强调场景描绘，适合风景和世界观表现。

```
/imagine prompt: a peaceful japanese garden with cherry blossoms, a girl reading a book --niji 6 --style scenic --ar 16:9
```

Niji模型与标准V6模型在生成逻辑上有本质差异。标准模型倾向于照片写实，Niji模型则是从底层以动漫数据集训练，输出的线条、色彩和构图都更接近专业动漫作品的视觉语言。对于二次元创作，Niji几乎总是比标准模型更好的选择。

二次元生成的迭代要点是控制角色一致性。在同一系列中固定--seed值，保持角色描述词不变，仅改变场景和动作描述，可以获得类似同一角色不同画面的效果。配合--cref使用角色参考图，一致性会更好。

Niji模型还支持--style raw参数，减少模型默认的动漫美化处理，产出更接近描述文字原始意图的画面。另一个实用参数是--sref，用一张动漫风格图作为风格参考，可以让Niji模仿特定作品的风格倾向。

二次元创作中常见的一个需求是模仿特定画师风格。你可以通过收集目标画师的作品，用/describe反推关键风格特征词，再把这些特征词组合到Prompt中来实现风格模仿。这种方法比直接写画师名字更可控，也避免版权争议。

> 工具决定下限，审美决定上限。Midjourney给你画笔，但画什么、怎么画，永远是你说了算。

## 3.5 参考资源

以下是怕浪猫整理的Midjourney学习资源，从官方到社区，从入门到进阶，按需取用。

**Midjourney官网**
https://www.midjourney.com
官方站点，包含作品画廊、会员入口和基础文档。网页端的Gallery功能可以浏览全球用户的作品和Prompt，是最好的灵感来源。

**Midjourney使用教程**
https://www.dapingtime.com/article/130.html
中文社区整理的系统教程，覆盖注册到进阶的全流程，适合中文用户入门。

**AI绘画Midjourney系统课**
https://new.qq.com/rain/a/20251222A01QC700
腾讯新闻平台上的系列课程，包含视频讲解和实战案例，适合系统化学习。

**Midjourney基础操作**
https://www.toutiao.com/article/7231864322132050491/
今日头条上的详细操作指南，图文并茂，对参数说明比较详尽。

除了以上资源，怕浪猫还推荐以下学习路径。第一，加入Midjourney的Discord服务器，每天花30分钟浏览其他用户的作品和Prompt。第二，关注Midjourney的官方更新日志，每次版本迭代都会带来新的能力和变化。第三，建立一个自己的Prompt库，把每次成功的Prompt按风格分类保存，长期积累就是你的核心资产。

## 实战Prompt模板速查

以下是本章涵盖的五大场景的Prompt模板，可以直接复制使用，根据需要替换主体描述。

**Q版3D角色模板：**
```
/imagine prompt: a cute chibi [角色描述], big head, small body, 3D render, pixar style, octane render, soft studio lighting, pastel colors, clean white background --ar 1:1 --v 6.1 --stylize 300
```

**泡泡玛特风格模板：**
```
/imagine prompt: a pop mart blind box toy figure, [角色描述], glossy vinyl material, detailed face, sparkle eyes, studio lighting, product photography, clean background --ar 3:4 --v 6.1 --stylize 500
```

**B端3D图标模板：**
```
/imagine prompt: 3D icon of a [图标描述], isometric view, soft gradient [色彩] color scheme, clay render style, soft shadows, minimal design, white background, UI asset --ar 1:1 --v 6.1 --stylize 150 --seed [固定种子]
```

**电商海报模板：**
```
/imagine prompt: [产品描述] on a podium, surrounded by [装饰元素], dramatic spotlight, dark background with bokeh, commercial photography, premium brand aesthetic --ar [尺寸比例] --v 6.1 --stylize 400 --style raw
```

**二次元角色模板：**
```
/imagine prompt: [角色描述], anime style, detailed eyes, [场景描述], dramatic atmosphere --niji 6 --ar 16:9
```

## 参数速查表

完整参数参考，收藏备用。

| 参数 | 全称 | 功能 | 取值范围 | 默认值 |
|------|------|------|----------|--------|
| --ar | Aspect Ratio | 宽高比 | 任意比例 | 1:1 |
| --v | Version | 模型版本 | 1-6.1 | 6.1 |
| --q | Quality | 质量 | 0.25-2 | 1 |
| --chaos | Chaos | 混沌度 | 0-100 | 0 |
| --stylize | Stylize | 风格化强度 | 0-1000 | 100 |
| --style | Style | 风格倾向 | raw/cute/expressive/scenic | 无 |
| --no | Negative | 排除词 | 文本 | 无 |
| --seed | Seed | 随机种子 | 0-4294967295 | 随机 |
| --iw | Image Weight | 图片权重 | 0-3 | 1 |
| --cw | Character Weight | 角色权重 | 0-100 | 100 |
| --cref | Character Reference | 角色参考 | 图片URL | 无 |
| --sref | Style Reference | 风格参考 | 图片URL | 无 |
| --sw | Style Weight | 风格权重 | 0-1000 | 100 |
| --tile | Tile | 无缝拼接 | 开关 | 关 |
| --stop | Stop | 停止点 | 10-100 | 100 |
| --repeat | Repeat | 重复次数 | 1-40 | 1 |
| --niji | Niji | 二次元模型 | 6 | 无 |

---

## 写在最后

这一章怕浪猫把Midjourney从注册到实战的完整链路都拆给你了。从Discord账号注册到订阅选择，从基础命令到进阶参数，从理论到五个实战案例的Prompt模板，这些构成了Midjourney日常工作的完整知识体系。

但请记住，看完不等于会。这篇文章的价值在于你打开Discord，把每个参数都试一遍，把每个模板都跑一遍。当你的手指记住了命令的节奏，当你的眼睛能从四宫格中快速判断哪张图值得迭代，那时候你才算真正入门了。

如果你觉得这篇文章对你有帮助，请收藏它。收藏的不只是文章，是未来创作时反复查阅的参数表和Prompt模板。也欢迎在评论区分享你的作品和Prompt，怕浪猫会挑有趣案例做下期拆解。

下一章我们将进入Stable Diffusion的深度教程。如果说Midjourney是开箱即用的自动挡，那Stable Diffusion就是可以拆解改装的手动挡——更多的控制权，更陡的学习曲线，也更大的可能性。ControlNet、LoRA、自定义模型训练等内容我会在第四章一一拆开。我们下章见。
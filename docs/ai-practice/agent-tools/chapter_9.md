# AIGC 创作工具——AI 画图、拍视频、写歌、做数字人

Midjourney V7 一张图收费不到 1 毛钱，Sora 2 能生成 60 秒带物理效果的视频，Suno 30 秒出一首完整歌曲。创意行业的门槛正在被 AI 打到地板上。

我是怕浪猫，《智能体产品全景手册》第 9 篇。这一篇我们讲 AIGC（AI-Generated Content，人工智能生成内容）创作工具。前面的章节讲的是"AI 帮你干活"，这一篇讲的是"AI 帮你创作"。图像、视频、音乐、数字人——四大创作赛道，AI 正在重新定义"创造力"的边界。

## 9.1 AI 图像生成：Midjourney、DALL-E、Stable Diffusion

AI 图像生成是 AIGC 最早爆发的赛道。2022 年 Midjourney 和 Stable Diffusion 的出现，让"AI 画图"从小众技术变成大众工具。

### Midjourney V7

Midjourney 是 AI 图像生成的标杆产品。2025 年发布的 V7 版本在以下方面有显著提升：

**提示词理解**：V7 对复杂提示词的理解更精确。以前需要"咒语"（精心构造的 prompt）才能出好图，现在用自然语言描述就能得到高质量结果。

**一致性控制**：V7 引入了角色一致性（Character Reference）和风格一致性（Style Reference）功能。你可以让 AI 保持同一个角色在不同场景中的外观一致，或者保持同一风格在多张图中的统一。这对于做连续故事、品牌视觉非常重要。

**细节精度**：手部、面部、文字渲染的准确性大幅提升。早期版本画手经常出现六指、扭曲等问题，V7 基本解决了这些"AI 画图的经典翻车点"。

Midjourney 的商业模式是订阅制，基础版 $10/月。按一张图约 0.07 元人民币计算，比请设计师画一张图的成本低几个数量级。

```
# Midjourney 图像生成的核心流程
class MidjourneyPipeline:
    def generate(self, prompt, **params):
        # 1. 提示词理解与增强
        enhanced_prompt = self.prompt_engineer.enhance(prompt)
        # 用户: "一只猫坐在窗台上，阳光照射，写实风格"
        # 增强: "a cat sitting on a windowsill, warm sunlight 
        #        streaming through glass, photorealistic, 
        #        8K, shallow depth of field, natural lighting"
        
        # 2. 文本编码（CLIP/T5）
        text_embeddings = self.text_encoder.encode(enhanced_prompt)
        
        # 3. 潜空间扩散（Latent Diffusion）
        # 从纯噪声开始，逐步去噪
        latent = torch.randn(1, 4, 64, 64)  # 初始噪声
        
        for step in range(self.num_steps):  # 通常30-50步
            # 预测噪声
            noise_pred = self.unet(
                latent, 
                timestep=step,
                context=text_embeddings
            )
            # 去噪
            latent = self.scheduler.step(noise_pred, step, latent)
        
        # 4. 解码为像素图像
        image = self.vae_decoder.decode(latent)
        # 64x64潜空间 → 512x512或1024x1024像素
        
        # 5. 后处理与超分辨率
        image = self.upscaler.upscale(image, factor=2)
        
        return image
```

### DALL-E 3（OpenAI）

DALL-E 3 集成在 ChatGPT 中，核心优势是"对话式生成"。你不需要写 prompt，用自然语言和 ChatGPT 聊天描述你想要的图就行。ChatGPT 会自动帮你优化 prompt 并调用 DALL-E 3 生成图像。

DALL-E 3 的另一个优势是文字渲染。在图像中准确渲染文字一直是 AI 画图的难题。DALL-E 3 在这方面表现不错，能生成包含准确文字的图像（如海报、Logo）。

### Stable Diffusion 3.5（Stability AI）

Stable Diffusion 是最流行的开源 AI 图像生成模型。SD 3.5 是 2025 年发布的最新版本。

开源的意义在于**可控性**和**免费**。你可以本地部署 SD，不依赖任何 API，数据不出本机。你可以用 LoRA（Low-Rank Adaptation）微调模型，让它在特定风格（如你的品牌风格）上生成图像。你可以用 ControlNet 精确控制构图、姿势、边缘。

Stable Diffusion 的生态系统是最丰富的。成千上万的 LoRA 模型、ControlNet 模型、插件和工具形成了一个庞大的创作者社区。

### 三款图像生成工具对比

| 维度 | Midjourney V7 | DALL-E 3 | Stable Diffusion 3.5 |
|------|--------------|----------|---------------------|
| 开发方 | Midjourney | OpenAI | Stability AI |
| 开源 | 否 | 否 | 是 |
| 价格 | $10/月起 | ChatGPT Plus $20/月 | 免费（本地部署） |
| 易用性 | 高（Discord/API） | 最高（对话式） | 中（需技术基础） |
| 图像质量 | 最优 | 优 | 优（依赖配置） |
| 一致性控制 | 强 | 弱 | 最强（ControlNet） |
| 文字渲染 | 中 | 强 | 中 |
| 本地部署 | 不支持 | 不支持 | 支持 |
| 适合用户 | 设计师/创作者 | 普通用户 | 开发者/技术型创作者 |

> 选 Midjourney 要质量，选 DALL-E 要省事，选 Stable Diffusion 要控制力。三者不矛盾，很多创作者同时用。

## 9.2 AI 视频生成：Sora 2、Kling（可灵）

如果说 AI 图像生成已经"够用了"，AI 视频生成还在"快速追赶"的阶段。

### Sora 2（OpenAI）

Sora 2 是 OpenAI 在 2025 年发布的视频生成模型，是 Sora 1 的重大升级。

核心能力：

**60 秒长视频**：Sora 2 能生成最长 60 秒的视频，远超竞品的 5-10 秒。长视频生成的难度在于保持时序一致性——角色不能在第 10 秒突然换衣服，场景不能在第 30 秒无故变化。

**物理效果模拟**：Sora 2 对物理世界有一定理解。液体流动、物体碰撞、重力影响等物理效果比第一代更真实。这不是完美的物理模拟，但已经不像早期 AI 视频那样"反直觉"。

**多镜头叙事**：Sora 2 能在一个视频中切换多个镜头角度。远景→近景→特写，像真正的电影剪辑。

**音频同步**：Sora 2 能为视频生成匹配的背景音效和音乐。雨声、脚步声、音乐节奏都能与画面同步。

Sora 2 的技术核心是 Diffusion Transformer（DiT）架构。与传统的 U-Net 架构不同，DiT 用 Transformer 结构做扩散模型，能更好地处理长时序依赖。

### Kling（可灵，快手）

Kling 是快手推出的 AI 视频生成工具，在国产 AI 视频产品中表现最好。

核心特色：

**中文场景优化**：在生成包含中文文字、中国元素的场景时表现优于国际产品。比如生成一个带有中文招牌的街景，Kling 的文字渲染明显比 Sora 更准确。

**人物动态**：Kling 在人物动作生成上有优势，特别是面部表情和肢体动作的自然度。这得益于快手在短视频领域的大量训练数据。

**免费额度**：Kling 提供免费试用额度，降低了用户尝试的门槛。

```
# AI 视频生成的核心技术架构对比
video_generation_architectures = {
    "Sora 2": {
        "架构": "Diffusion Transformer (DiT)",
        "原理": """
            1. 视频压缩到潜空间（3D VAE）
            2. 在潜空间用Transformer做扩散
            3. Transformer处理时空联合token
            4. 解码回像素空间
        """,
        "优势": "长视频、物理效果、多镜头",
        "劣势": "计算成本极高"
    },
    "Kling": {
        "架构": "3D U-Net + Diffusion",
        "原理": """
            1. 视频帧序列压缩
            2. 3D卷积处理时空信息
            3. 扩散去噪生成视频
            4. 时序注意力保持一致性
        """,
        "优势": "人物动态、中文场景、免费试用",
        "劣势": "视频长度较短（10-15秒）"
    }
}
```

### AI 视频生成的应用场景

AI 视频生成已经在这几个场景中实现商业化：

**广告素材**：电商商品视频、信息流广告素材。传统拍一条产品视频需要摄像师+剪辑师，AI 生成只要几分钟。

**短视频创作**：抖音、快手中的创意视频。AI 视频 + AI 音乐 + AI 剧本，一个人就能做一条完整的短视频。

**影视预可视化**：导演可以用 AI 快速生成场景概念视频，用于前期沟通和方案验证。比画分镜更直观。

**教育培训**：生成教学演示视频。比如"细胞分裂过程""太阳系运行"等抽象概念的视频化。

> AI 视频生成的终局不是替代影视行业，而是让每个人都能"拍"视频。就像手机摄像头没有替代专业摄影，但让每个人都能拍照。

## 9.3 AI 音乐生成：Suno、Udio

AI 音乐生成在 2025 年迎来了"iPhone 时刻"——Suno V4 能在 30 秒内生成一首包含人声、编曲、混音的完整歌曲。

### Suno V4

Suno 是目前最流行的 AI 音乐生成工具。V4 版本的核心能力：

**完整歌曲生成**：输入一段文字描述（"一首关于夏天的流行歌，轻快风格，女声"），Suno 在 30 秒内生成一首包含前奏、主歌、副歌、桥段、尾奏的完整歌曲，带人声演唱和完整编曲。

**风格控制**：支持指定音乐风格（流行、摇滚、爵士、古典、电子、说唱、民谣等）、乐器配器、节奏快慢、情感基调。

**多语言演唱**：支持英语、中文、日语、韩语、西班牙语等多种语言的歌词演唱。中文发音的自然度在 V4 中有显著提升。

**歌词生成**：你可以自己写歌词，也可以让 AI 根据主题自动生成歌词。AI 生成的歌词会自动匹配旋律和节奏。

Suno 的定价：免费版每天 10 首，Pro 版 $8/月（500 首），Premier 版 $24/月（2000 首）。

```
# Suno V4 的音乐生成流程
class SunoV4:
    def generate_song(self, description, lyrics=None):
        # 1. 音乐风格解析
        style = self.parse_style(description)
        # style = {
        #     "genre": "pop",
        #     "mood": "upbeat, cheerful",
        #     "instruments": ["acoustic_guitar", "drums", "bass", "synth"],
        #     "vocal": "female",
        #     "tempo": 120,  # BPM
        #     "key": "C_major"
        # }
        
        # 2. 歌词生成（如果未提供）
        if lyrics is None:
            lyrics = self.lyric_generator.generate(
                theme=description,
                style=style,
                structure=["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"]
            )
        
        # 3. 旋律生成
        melody = self.melody_generator.generate(
            style=style,
            lyrics=lyrics
        )
        
        # 4. 编曲生成
        arrangement = self.arranger.generate(
            melody=melody,
            style=style,
            instruments=style["instruments"]
        )
        
        # 5. 人声合成
        vocals = self.vocal_synth.generate(
            lyrics=lyrics,
            melody=melody,
            voice_type=style["vocal"]
        )
        
        # 6. 混音
        final_song = self.mixer.mix(
            vocals=vocals,
            arrangement=arrangement,
            style=style
        )
        
        return final_song  # 完整歌曲
```

### Udio

Udio 是 Suno 的主要竞争对手，由前 Google DeepMind 研究人员创立。

Udio 的差异化在于音频质量。Udio 生成的音乐在音质、混音专业度上略优于 Suno，特别在古典音乐和爵士乐等对音质要求高的类型上。

Udio 还提供了更细粒度的控制：你可以分别生成和编辑歌曲的不同部分（前奏、主歌、副歌），然后拼接成完整歌曲。这给专业音乐人提供了更大的创作控制空间。

### AI 音乐的商业化挑战

AI 音乐生成面临一个独特的挑战：版权。AI 生成的音乐是否侵犯了训练数据中音乐的版权？如果 AI 生成的一首歌听起来很像某位歌手的风格，这算不算侵权？

2025 年，多家唱片公司起诉了 Suno 和 Udio，指控它们未经授权使用版权音乐训练模型。这个法律争议至今未完全解决，是 AI 音乐行业最大的不确定性。

> AI 音乐的版权问题不是技术问题，是利益分配问题。解法可能是"训练数据授权制"——AI 公司向音乐版权方付费获取训练数据，类似 Spotify 向唱片公司付费获取播放权。

## 9.4 AI 语音合成与数字人：ElevenLabs、HeyGen

### ElevenLabs

ElevenLabs 是 AI 语音合成领域的领导者。它的技术能做到什么？克隆一个人的声音只需要 30 秒的样本音频。

核心产品：

**Voice Cloning（声音克隆）**：上传 30 秒-5 分钟的某人的语音样本，ElevenLabs 能克隆出一个高度相似的声音。用这个克隆的声音可以朗读任何文字。ElevenLabs 的克隆质量是业界最好的，情感、语调、停顿都高度还原。

**Voice Library（声音库）**：ElevenLabs 有一个社区声音库，用户可以分享和使用彼此创建的声音。目前有数千种不同风格的声音可供选择。

**多语言 TTS（Text-to-Speech）**：ElevenLabs 支持近 30 种语言的文字转语音，包括中文。同一段文字可以用不同语言朗读，甚至可以做实时翻译配音。

**实时语音对话**：ElevenLabs 提供实时语音 API，延迟低至 400ms。这让构建语音对话 Agent 成为可能——用户说话，AI 听懂并语音回答，像打电话一样自然。

ElevenLabs 的定价：免费版每月 10000 字符，付费版从 $5/月起。

### HeyGen

HeyGen 专注于 AI 数字人——用 AI 生成会说话的数字人视频。

核心能力：

**数字人视频生成**：输入一段文字和一张照片，HeyGen 生成一段数字人说这段话的视频。口型同步、面部表情、头部动作都由 AI 自动生成。

**多语言视频本地化**：这是 HeyGen 最受欢迎的功能。你上传一段中文讲解视频，HeyGen 能自动翻译成英语、日语、西班牙语等，并用原说话者的声音和面部生成目标语言的视频。口型会自动适配新语言。

**数字人模板**：HeyGen 提供多种数字人形象模板，用户也可以上传自己的照片创建专属数字人。

```
# HeyGen 数字人视频生成的流程
class HeyGen:
    def create_avatar_video(self, text, avatar_image, language="zh"):
        # 1. 文本分析和情感标注
        annotated = self.text_analyzer.analyze(text)
        # 标注每个句子的情感、语调、重音
        
        # 2. 语音合成
        audio = self.tts.synthesize(
            text=annotated,
            voice=self.clone_voice(avatar_image),
            language=language
        )
        
        # 3. 面部动画生成
        facial_animation = self.face_animator.generate(
            audio=audio,
            emotion=annotated.emotions,
            base_image=avatar_image
        )
        # 生成每帧的面部关键点变化
        
        # 4. 口型同步
        lip_sync = self.lip_sync_model.generate(
            audio=audio,
            face_frames=facial_animation
        )
        
        # 5. 视频合成
        video = self.renderer.render(
            face_animation=lip_sync,
            audio=audio,
            background="transparent"  # 支持透明背景
        )
        
        return video
```

### AI 语音与数字人的应用场景

**内容创作**：YouTuber、B 站 UP 主用 AI 语音做配音，不需要自己录音。数字人出镜不需要化妆和拍摄。

**教育培训**：企业培训视频用数字人讲解，可以快速制作多语言版本。一个培训课程可以同时生成中英日韩等多种语言版本。

**客服与营销**：数字人客服 24 小时在线，用自然语言与客户交流。数字人直播带货已经在电商中广泛应用。

**无障碍辅助**：为失声者克隆声音，让他们能用自己的声音"说话"。为视障人士提供高质量的语音朗读服务。

> AI 语音和数字人的伦理边界需要警惕。声音克隆和 Deepfake（深度伪造）技术是一把双刃剑——用于创作是工具，用于欺诈是武器。

## 9.5 Lovart：AI 设计 Agent

Lovart 是一个特别的 AIGC 产品——它不是单一的内容生成工具，而是一个 AI 设计 Agent，能理解设计需求并自主完成设计任务。

### Lovart 的核心能力

**设计理解**：Lovart 能理解设计需求描述（"帮我设计一个咖啡品牌的 Logo，简约风格，棕色系"），并自主完成设计。

**多模态输出**：不只是生成图片，而是生成完整的设计方案——Logo、配色方案、字体选择、应用场景效果图。

**迭代修改**：你可以说"颜色再深一点""字体换成无衬线的"，Lovart 理解修改意图并调整设计。

**批量生成**：一次生成多个设计方案供选择，每个方案有不同风格和方向。

### Lovart vs 传统 AI 图像生成

传统 AI 图像生成工具（Midjourney 等）是"你给 prompt，我给图"的单次交互模式。Lovart 是"你给需求，我给方案"的 Agent 模式。区别在于 Lovart 有理解需求、规划方案、迭代修改的能力。

这使得 Lovart 更接近"设计师"而非"画图工具"。当然，在创意深度和专业度上，AI 设计 Agent 还远不能替代人类设计师。但对于简单的设计需求（社交媒体配图、简单 Logo、海报模板），Lovart 已经够用。

## 9.6 AIGC 工具全景对比与选型

### 全景对比

| 赛道 | 产品 | 核心能力 | 价格 | 开源替代 |
|------|------|---------|------|---------|
| 图像生成 | Midjourney V7 | 最高图像质量 | $10/月 | Stable Diffusion |
| 图像生成 | DALL-E 3 | 对话式生成 | $20/月 | - |
| 图像生成 | SD 3.5 | 最强控制力 | 免费 | 自身即开源 |
| 视频生成 | Sora 2 | 60秒长视频 | ChatGPT Pro | - |
| 视频生成 | Kling | 中文场景优化 | 免费+付费 | - |
| 音乐生成 | Suno V4 | 完整歌曲30秒 | $8/月 | - |
| 音乐生成 | Udio | 更高音质 | $10/月 | - |
| 语音合成 | ElevenLabs | 声音克隆 | $5/月 | Bark/TTS |
| 数字人 | HeyGen | 多语言视频 | $29/月 | SadTalker |
| 设计Agent | Lovart | AI设计方案 | 订阅制 | - |

### 选型建议

**图像生成**：
- 专业设计师：Midjourney V7（质量最优）+ Stable Diffusion（本地控制）
- 普通用户：DALL-E 3（对话式最简单）
- 开发者：Stable Diffusion 3.5（开源可控）

**视频生成**：
- 专业视频制作：Sora 2（60秒长视频）
- 短视频创作：Kling（中文优化+免费额度）
- 广告素材：两者都行，看具体需求

**音乐生成**：
- 流行音乐：Suno V4（完整歌曲生成）
- 古典/爵士：Udio（音质更好）
- 背景音乐：Suno 免费版够用

**语音与数字人**：
- 语音克隆：ElevenLabs（质量最好）
- 数字人视频：HeyGen（多语言本地化）
- 实时语音 Agent：ElevenLabs Realtime API

> AIGC 工具的选择逻辑很简单：先确定你需要什么类型的内容（图/视频/音乐/语音），再根据专业度和预算选产品。先用免费版试用，满意了再付费。

这一章我们拆解了 AIGC 创作的四大赛道：AI 图像生成（Midjourney V7、DALL-E 3、Stable Diffusion 3.5）、AI 视频生成（Sora 2、Kling）、AI 音乐生成（Suno V4、Udio）、AI 语音与数字人（ElevenLabs、HeyGen），还介绍了 AI 设计 Agent Lovart。

| 赛道 | 产品数量 | 市场格局 |
|------|---------|---------|
| 图像生成 | 3 款 | Midjourney 质量领先 |
| 视频生成 | 2 款 | Sora 2 技术领先 |
| 音乐生成 | 2 款 | Suno 用户量第一 |
| 语音/数字人 | 2 款 | ElevenLabs 标杆 |

觉得有用？收藏起来，下次选 AIGC 工具直接照着表选。

你用过哪些 AIGC 工具？AI 生成的作品质量怎么样？评论区聊聊。

关注怕浪猫，下期我们讲具身智能与 Agent 协议——AI 有了身体会怎样？MCP 和 A2A 协议为什么重要？这是系列最后一篇，大结局不容错过。系列进度 9/10，关注不错过。

下一篇是系列收官之作，怕浪猫会带你走进具身智能（Embodied AI）和 Agent 协议的世界。Tesla Optimus 能做家务了？Figure AI 的机器人能替代工厂工人吗？MCP（Model Context Protocol）协议为什么被称为"AI 的 USB 接口"？我们下期见。

# 第十四章 附录

知识不在多，在于需要时找得到。这一章是整本书的索引层，把散落在各章的术语、模型、工具、配置集中汇总，方便你随时查阅。

我是怕浪猫，这是本书最后一章。附录的价值在于"即时可用"——你不需要翻回前面的章节，所有参考信息都在这里。

## 14.1 术语表

以下是本书涉及的核心术语，按字母顺序排列。每个术语都标注了全称和简要解释。

| 术语 | 全称 | 解释 |
|------|------|------|
| AI | Artificial Intelligence | 人工智能，使机器具备类人智能的技术 |
| API | Application Programming Interface | 应用程序编程接口，程序间通信的约定 |
| AIGC | AI Generated Content | AI生成内容，由人工智能模型创作的文本、图片、音视频等 |
| Attention | Attention Mechanism | 注意力机制，让模型聚焦于输入中重要部分的技术 |
| Base64 | Base64 | 用64个字符表示二进制数据的编码方式 |
| CFG | Classifier Free Guidance | 无分类器引导，控制生成结果与提示词的匹配程度 |
| Checkpoint | Checkpoint | 模型检查点，保存了训练过程中的完整模型权重 |
| CLIP | Contrastive Language-Image Pre-training | 对比语言-图像预训练模型，连接文本和图像的桥梁 |
| CNN | Convolutional Neural Network | 卷积神经网络，擅长处理网格结构数据（如图像） |
| ControlNet | ControlNet | 控制网络，为扩散模型添加空间结构控制的辅助模型 |
| CUDA | Compute Unified Device Architecture | NVIDIA的并行计算平台和编程模型 |
| DALL·E | DALL·E | OpenAI的AI图片生成模型名称 |
| DDIM | Denoising Diffusion Implicit Models | 去噪扩散隐式模型，一种扩散采样算法 |
| DDPM | Denoising Diffusion Probabilistic Models | 去噪扩散概率模型，扩散模型的理论基础 |
| DiT | Diffusion Transformer | 扩散Transformer，用Transformer替代UNet的架构 |
| EMA | Exponential Moving Average | 指数移动平均，模型参数的平滑技术 |
| ESRGAN | Enhanced Super-Resolution GAN | 增强超分辨率生成对抗网络 |
| FP8 | 8-bit Floating Point | 8位浮点数格式，降低显存占用和计算量 |
| GAN | Generative Adversarial Network | 生成对抗网络，由生成器和判别器组成的模型 |
| GPT-4 | Generative Pre-trained Transformer 4 | OpenAI的第四代生成式预训练Transformer模型 |
| GPT-4o | GPT-4 Omni | GPT-4的全能版，支持文本、图像、音频多模态 |
| Hires. fix | High Resolution Fix | 高分辨率修复，SD中用于提升图片分辨率的功能 |
| HTTP | HyperText Transfer Protocol | 超文本传输协议，Web通信的基础协议 |
| Inpainting | Inpainting | 局部重绘，只修改图片中指定区域的技术 |
| IP-Adapter | Image Prompt Adapter | 图像提示适配器，用图片作为提示词的模型 |
| JSON | JavaScript Object Notation | JavaScript对象表示法，轻量级数据交换格式 |
| LoRA | Low-Rank Adaptation | 低秩适配，一种轻量级模型微调方法 |
| LoCon | LoRA-Convolution | LoRA的卷积增强版，同时微调卷积层 |
| Latent | Latent Space | 潜在空间，数据的压缩表示空间 |
| Liyui | Liyui | 哩布哩布，国内SD模型社区平台 |
| MLSD | Mobile Line Segment Detection | 移动线段检测，检测图片中的直线结构 |
| MSE | Mean Squared Error | 均方误差，衡量预测值与真实值差异的指标 |
| OpenPose | OpenPose | 开源人体姿态估计框架 |
| Outpainting | Outpainting | 向外扩展，在图片边界外延展画面的技术 |
| Prompt | Prompt | 提示词，指导AI生成内容的文本描述 |
| Python | Python | 一种通用编程语言，AI领域最常用的语言 |
| Rank | Rank | LoRA中低秩矩阵的秩，控制微调能力 |
| RRDB | Residual-in-Residual Dense Block | 残差中的残差密集块，Real-ESRGAN的核心网络结构 |
| SDK | Software Development Kit | 软件开发工具包 |
| Seed | Seed | 随机种子，控制生成过程的随机性 |
| TTS | Text-to-Speech | 文本转语音技术 |
| UNet | UNet | U型网络，扩散模型中最常用的网络架构 |
| VAE | Variational Autoencoder | 变分自编码器，在潜空间中编码和解码图像 |
| WebUI | Web User Interface | Web用户界面，这里指AUTOMATIC1111的SD Web界面 |
| Whisper | Whisper | OpenAI的语音识别模型 |
| ZSNR | Zero Signal-to-Noise Ratio | 零信噪比，训练中的一种采样策略 |

## 14.2 模型下载站点

以下是本书涉及的AI模型下载站点，按类型分类。

### Checkpoint 大模型

| 站点 | 网址 | 说明 |
|------|------|------|
| Civitai | https://civitai.com | 全球最大SD模型社区，Checkpoint、LoRA、Embedding等 |
| Hugging Face | https://huggingface.co | 开源AI模型平台，SD、FLUX等官方模型发布地 |
| LibLib | https://www.liblib.ai | 国内最大SD模型社区，访问速度快 |
| Stable Diffusion Official | https://huggingface.co/stabilityai | Stability AI官方模型页面 |

Civitai是SD生态最重要的社区平台。上面的Checkpoint模型按下载量、评分、评论数排序，可以快速找到高质量模型。下载时注意确认模型的基础版本（SD 1.5、SDXL、SD 3等），不同版本的模型不兼容。

Hugging Face是更偏学术和技术向的平台。Stability AI、Black Forest Labs等官方机构都会在这里发布原始模型。如果你需要最新、最原版的模型文件，Hugging Face是首选。

LibLib是国内用户的最佳选择。服务器在国内，下载速度远超Civitai和Hugging Face。而且很多国内作者训练的LoRA只在LibLib发布，包含大量国风、水墨、书法等中国风格材的模型。

### 推荐Checkpoint模型

以下是各领域广受好评的Checkpoint模型推荐。

写实类：Realistic Vision（通用写实）、ChilloutMix（亚洲面孔写实）、majicMIX realistic（高清写实人像）。这三个模型适合生成照片级写实图片，其中ChilloutMix对亚洲面孔的表现特别好。

二次元类：Anything V5（通用二次元）、Counterfeit（日系动漫风）、GhostMix（暗色系二次元）。Anything是最经典的二次元模型，适合生成动漫风格的人物和场景。

艺术类：DreamShaper（通用艺术风格）、Deliberate（多样化风格）、Rev Animated（插画风格）。DreamShaper在风景和概念艺术方面表现出色。

SDXL类：SDXL Base 1.0（官方基础模型）、Juggernaut XL（写实SDXL）、DreamShaper XL（艺术SDXL）。SDXL模型分辨率更高（1024x1024），但需要更多显存。

### LoRA 模型

| 站点 | 网址 | 说明 |
|------|------|------|
| Civitai LoRA | https://civitai.com/models?types=LORA | LoRA专区，数万个模型 |
| LibLib LoRA | https://www.liblib.ai/models | 国内LoRA资源 |
| Kohya Model Gallery | https://civitai.com/user/Kohya | Kohya_ss训练工具作者的模型展示 |

### FLUX 模型

| 站点 | 网址 | 说明 |
|------|------|------|
| Black Forest Labs | https://blackforestlabs.ai | FLUX官方页面 |
| BFL Hugging Face | https://huggingface.co/black-forest-labs | FLUX模型下载 |
| Replicate | https://replicate.com/black-forest-labs | FLUX API调用平台 |
| fal.ai | https://fal.ai | FLUX API调用平台 |

### 提示词灵感网站

| 站点 | 网址 | 说明 |
|------|------|------|
| PromptHero | https://prompthero.com | 跨平台提示词搜索 |
| Lexica.art | https://lexica.art | SD提示词搜索引擎 |
| Nanoprompts | https://nanoprompts.com | 纳米级提示词库 |
| FlowGPT | https://flowgpt.com | 提示词社区 |
| Snack Prompt | https://snackprompt.com | 提示词分享平台 |
| LiblibAI | https://www.liblib.ai | 国内SD模型+提示词站 |
| KALOS | https://kalos.art | 艺术风格提示词 |
| PromptFolder | https://promptfolder.com | 提示词管理工具 |
| YouMind | https://youmind.ai | AI提示词助手 |

## 14.3 硬件配置参考

以下是不同使用场景的硬件配置建议。选择硬件时，最关键的指标是GPU显存（VRAM）。AI生图是显存密集型任务，显存大小直接决定了你能运行什么模型、生成多大分辨率的图片。

显存需求参考：SD 1.5需要至少4GB（推荐6GB以上），SDXL需要至少8GB（推荐12GB以上），FLUX.2 Dev需要至少12GB（推荐16GB以上），FLUX.2 Pro需要至少24GB。训练LoRA需要至少8GB显存，训练Checkpoint需要至少24GB。

### 入门级配置（SD 1.5 基础使用）

| 组件 | 推荐规格 | 预算参考 |
|------|---------|---------|
| GPU | NVIDIA RTX 3060 12GB | 约2000元 |
| CPU | Intel i5-12400F / AMD R5 5600 | 约800元 |
| 内存 | 16GB DDR4 | 约300元 |
| 硬盘 | 512GB SSD | 约300元 |
| 电源 | 550W | 约300元 |
| 总计 | | 约3700元 |

入门级配置可以流畅运行SD 1.5，分辨率512x512，步数20-30。使用--medvram参数可以运行SDXL，但速度较慢。适合学习入门和轻度使用。

### 进阶级配置（SDXL + ControlNet）

| 组件 | 推荐规格 | 预算参考 |
|------|---------|---------|
| GPU | NVIDIA RTX 4060 Ti 16GB | 约3500元 |
| CPU | Intel i5-13600KF / AMD R5 7600X | 约1500元 |
| 内存 | 32GB DDR5 | 约600元 |
| 硬盘 | 1TB NVMe SSD | 约500元 |
| 电源 | 750W | 约500元 |
| 总计 | | 约6600元 |

进阶级配置可以流畅运行SDXL，分辨率1024x1024，同时加载多个LoRA和ControlNet。也支持运行FLUX.2 Dev（FP8量化版）。适合日常创作和中度商业使用。

### 专业级配置（FLUX + 训练LoRA）

| 组件 | 推荐规格 | 预算参考 |
|------|---------|---------|
| GPU | NVIDIA RTX 4090 24GB | 约13000元 |
| CPU | Intel i7-14700K / AMD R9 7900X | 约2500元 |
| 内存 | 64GB DDR5 | 约1200元 |
| 硬盘 | 2TB NVMe SSD + 4TB HDD | 约1000元 |
| 电源 | 1000W | 约800元 |
| 总计 | | 约18500元 |

专业级配置可以流畅运行FLUX.2 Pro、训练LoRA、批量生图。24GB显存足以应对几乎所有AI生图任务。适合专业创作者和小型工作室。

### 工作站级配置（多GPU + 大模型训练）

| 组件 | 推荐规格 | 预算参考 |
|------|---------|---------|
| GPU | 2x NVIDIA RTX 4090 24GB | 约26000元 |
| CPU | AMD Threadripper 7960X | 约15000元 |
| 内存 | 128GB DDR5 ECC | 约4000元 |
| 硬盘 | 4TB NVMe SSD + 8TB HDD | 约3000元 |
| 电源 | 1600W | 约1500元 |
| 总计 | | 约49500元 |

工作站级配置适合训练Checkpoint大模型、运行FLUX.2 Pro满血版、多GPU并行批量生图。仅推荐给专业团队和研究机构。

### 云端方案对比

如果你不想购买硬件，云端方案是另一个选择。

| 平台 | GPU类型 | 价格 | 特点 |
|------|--------|------|------|
| AutoDL | RTX 4090 24GB | 约2元/小时 | 国内访问快，按量计费 |
| 腾讯云函数计算 | T4/A10 | 按请求计费 | 无需管理服务器，适合API部署 |
| AWS EC2 | A100 40GB | 约30元/小时 | 企业级GPU，适合大规模训练 |
| Google Colab | T4（免费）/ A100（付费） | 免费/$10每小时 | 最简单的入门方式 |
| RunPod | RTX 4090 / A100 | 约$0.4/$2每小时 | 按秒计费，社区模板丰富 |

## 14.4 在线生图平台

不需要本地硬件，直接在浏览器中生图的平台。这些平台适合没有独立显卡的用户，或者需要快速出图不想配置环境的场景。

选择在线平台时考虑三个因素：支持的模型（是否支持SDXL、FLUX等新模型）、生成速度（排队时间多长）、费用（免费额度是否够用）。建议先试用免费额度，找到适合自己需求的平台后再考虑付费。

| 平台 | 网址 | 支持模型 | 费用 |
|------|------|---------|------|
| Midjourney | https://www.midjourney.com | Midjourney v6 | $10-60/月 |
| ChatGPT | https://chat.openai.com | DALL·E 3 | $20/月（ChatGPT Plus） |
| Leonardo.ai | https://leonardo.ai | SDXL、自定义模型 | 免费/付费 |
| Playground | https://playground.com | SD 1.5、SDXL | 免费/付费 |
| Civitai Generator | https://civitai.com | SD系列 | 按积分计费 |
| LibLib在线生图 | https://www.liblib.ai | SD系列 | 免费/付费 |
| Tensor.art | https://tensor.art | SD系列、FLUX | 免费/付费 |
| Replicate | https://replicate.com | FLUX、SD等 | 按次计费 |
| fal.ai | https://fal.ai | FLUX、SD等 | 按次计费 |

Leonardo.ai是一个值得关注的平台。它基于SD模型但提供了大量自定义工具，包括Canvas编辑器、3D模型生成、实时画布等。免费用户每天有150个token的额度，足够生成5-10张图。

Tensor.art和Civitai Generator的优势是可以直接使用社区中的LoRA和Checkpoint模型，不需要自己下载安装。你在Civitai上看到喜欢的模型，点击"Generate"就能直接在线生图。

Replicate和fal.ai是开发者向的平台，主要提供API调用服务。它们的费用按次计算，通常每张图几分钱到几毛钱。适合需要程序化生图但不想维护本地服务器的开发者。

## 14.5 开发者工具与SDK

| 工具 | 网址 | 说明 |
|------|------|------|
| OpenAI Python SDK | https://github.com/openai/openai-python | DALL·E 3 API调用 |
| ComfyUI API | https://github.com/comfyanonymous/ComfyUI | ComfyUI的HTTP API |
| diffusers | https://github.com/huggingface/diffusers | Hugging Face的扩散模型库 |
| Stable Diffusion WebUI API | https://github.com/AUTOMATIC1111/stable-diffusion-webui | A1111 WebUI的内置API |
| QClaw生图技能 | ~/.qclaw/skills/qclaw-generate-image/ | QClaw Agent化的生图技能 |
| Kohya_ss | https://github.com/bmaltais/kohya_ss | LoRA训练工具 |
| xformers | https://github.com/facebookresearch/xformers | SD显存优化库 |
| ControlNet | https://github.com/Mikubill/sd-webui-controlnet | ControlNet WebUI插件 |

## 14.6 社区与学习资源

AI生图领域发展极快，保持持续学习至关重要。以下社区和资源按活跃度和质量排序。

| 资源 | 网址 | 说明 |
|------|------|------|
| r/StableDiffusion | https://www.reddit.com/r/StableDiffusion | Reddit SD社区，每日数百帖 |
| r/midjourney | https://www.reddit.com/r/midjourney | Reddit Midjourney社区 |
| OpenAI Community | https://community.openai.com | OpenAI官方社区 |
| Hugging Face Forums | https://discuss.huggingface.co | Hugging Face讨论区 |
| ComfyUI Discord | https://discord.com/invite/comfyui | ComfyUI官方Discord |
| QClaw文档 | https://docs.openclaw.ai | QClaw官方文档 |
| Stable Diffusion论文 | https://arxiv.org/abs/2112.10752 | SD原始论文 |
| LoRA论文 | https://arxiv.org/abs/2106.09685 | LoRA原始论文 |
| ControlNet论文 | https://arxiv.org/abs/2302.05543 | ControlNet原始论文 |
| DiT论文 | https://arxiv.org/abs/2212.09748 | Diffusion Transformer论文 |

Reddit的r/StableDiffusion是全球最活跃的SD社区。每天都有新模型发布、新技巧分享、新工作流讨论。建议每周至少浏览一次Hot帖，跟进最新动态。

论文阅读对于想深入理解原理的读者非常重要。Stable Diffusion论文（2112.10752）是理解扩散模型的基础，建议先读这篇。LoRA论文（2106.09685）虽然以大语言模型为研究对象，但LoRA在图像生成中的应用原理完全相同。ControlNet论文（2302.05543）详细解释了零卷积结构和控制机制。DiT论文（2212.09748）是理解FLUX模型架构的基础。

国内社区推荐关注微信公众号"AI绘画研究所"、"机器之心"等，它们会定期翻译和总结海外最新技术动态。B站上也有大量SD和ComfyUI的视频教程，适合视觉学习者。

## 14.7 常见问题速查

以下是AI生图过程中最常见的问题和解决方案。

生成图片全黑或全白：通常是VAE（Variational Autoencoder，变分自编码器）未正确加载。在WebUI设置中选择正确的VAE模型，或在提示词中添加"--vae-path"参数指定VAE文件路径。

生成图片模糊：可能原因包括分辨率太低（尝试512x512以上）、步数太少（至少20步）、采样器选择不当（换DPM++ 2M Karras）。如果使用了Hires. fix但仍模糊，尝试提高重绘幅度（Denoising strength）到0.4-0.6。

CUDA out of memory：显存不足。解决方案依次尝试：启用xformers、使用--medvram参数、降低分辨率、减少批量大小、关闭不需要的LoRA。如果以上都不行，需要更换更大显存的GPU或使用云端方案。

LoRA加载后无效果：检查LoRA文件名是否正确（不含后缀）、LoRA文件是否在正确目录（models/Lora/）、权重是否太低（尝试0.7以上）。还要确认LoRA适配的Checkpoint版本是否匹配。

ControlNet不生效：检查预处理器是否正确选择、模型是否加载、权重是否为0。如果ControlNet单元显示红色，说明模型未正确加载，检查文件路径。

生成图片有水印或伪影：可能是Checkpoint模型本身的问题，换一个模型试试。也可能是负面提示词不够，添加"watermark, signature, text, logo"到负面提示词。

API调用超时：检查网络连接是否正常、API Key是否有效、请求频率是否超限。DALL·E 3的API限制是每分钟5次请求，如果超限需要等待后重试。

## 14.7 本书章节速查

| 章节 | 主题 | 核心内容 |
|------|------|----------|
| 第一章 | AI图片生成概述 | 6大主流工具对比、技术发展脉络 |
| 第二章 | 提示词工程 | 编写技巧、风格速查表、9个提示词网站 |
| 第三章 | Midjourney完全指南 | /imagine命令、参数详解、5大实战案例 |
| 第四章 | Stable Diffusion深度教程 | 环境部署、模型选择、核心参数、图生图 |
| 第五章 | ComfyUI工作流 | 节点式界面、工作流搭建、插件扩展 |
| 第六章 | ControlNet精准控制 | 14种模型详解、多ControlNet叠加 |
| 第七章 | LoRA模型与微调 | 原理、加载使用、训练方法、资源站点 |
| 第八章 | DALL·E 3与OpenAI生态 | API调用、ChatGPT集成、Agent工作流 |
| 第九章 | FLUX.2模型系列 | DiT架构、四版本对比、FP8量化 |
| 第十章 | 图片放大与高清修复 | Real-ESRGAN、Upscayl、SD内置放大 |
| 第十一章 | 本地QClaw生图技能 | 源码解析、配置方法、高级用法 |
| 第十二章 | 版权与法律 | 著作权案例、商用合规、风险防范 |
| 第十三章 | 实战项目合集 | 电商、社交媒体、IP设计、建筑、游戏 |
| 第十四章 | 附录 | 术语表、模型站点、硬件配置、社区资源 |

### 阅读建议

不同读者群体的推荐阅读路径。

零基础新手：第1章→第2章→第3章（Midjourney入门最快）→第8章（ChatGPT生图零门槛）。这条路径不需要任何本地部署，用在线工具就能开始创作。

本地部署用户：第1章→第4章→第5章→第6章→第7章。这条路径从SD WebUI开始，逐步进阶到ComfyUI和ControlNet，最终掌握LoRA微调。

开发者：第8章→第11章→第9章。这条路径聚焦API调用和Agent集成，适合想把AI生图集成到产品中的开发者。

商业用户：第12章→第13章→第14章。这条路径聚焦合规和实战应用，适合需要在商业场景中使用AI生图的用户。

### 持续学习建议

AI生图领域的发展速度极快，新的模型和工具几乎每个月都在出现。以下是一些保持更新的建议。

关注Civitai的"最新模型"页面，每周浏览一次新上传的Checkpoint和LoRA。关注Hugging Face上Stability AI和Black Forest Labs的账号，获取官方模型更新。关注Reddit的r/StableDiffusion社区，这里有大量用户分享的最新技巧和发现。

关注arxiv.org上的最新论文。虽然论文阅读门槛较高，但能帮你理解技术发展趋势。重点关注cv.CV（计算机视觉）和cs.LG（机器学习）分类下的论文。

实际动手是最重要的学习方式。每学一个新模型或新技术，立即动手实践。理论知识和实际操作之间的差距，只有通过大量练习才能弥合。

## 本章总结

这份附录是整本书的导航地图。术语表帮你快速理解不熟悉的概念，模型站点帮你找到需要的资源，硬件配置帮你选择合适的设备，社区资源帮你持续学习。

附录的价值在于"即时可用"。遇到不认识的术语，翻到这里查。需要下载模型，翻到这里找链接。不确定硬件需求，翻到这里看配置表。

> 怕浪猫的建议：把这一章加入书签，作为日常工作的快速参考手册。AI生图领域发展很快，新的模型和工具不断出现。附录中的链接和信息会定期更新，建议每隔几个月回来看看有没有新的资源。

到这里，整本《AI图片创作生成》就全部结束了。从提示词工程到模型选择，从本地部署到API调用，从技术原理到法律合规，14章内容覆盖了AI图片生成的完整知识体系。

AI生图不是终点，而是创作的起点。工具会迭代，模型会更新，但"用创意驱动技术"的核心理念不会变。希望这本书能帮你从"AI生图新手"成长为"AI创作高手"。

我是怕浪猫，感谢你读到最后。我们下一本书再见。

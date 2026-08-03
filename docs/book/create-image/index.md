# 《AI图片创作与生成——从入门到精通》

> 图书目录与资源索引  
> 最后更新：2026-08-02

---

## 目录

### 第一章 AI图片生成概述

#### 1.1 什么是AI图片生成
- 文生图（Text-to-Image）技术简介
- 图生图（Image-to-Image）技术简介
- AI图片生成的核心原理：扩散模型（Diffusion Model）
- 从GAN到Diffusion：技术演进脉络

#### 1.2 主流AI图片生成工具一览
| 工具 | 开发方 | 特点 | 链接 |
|------|--------|------|------|
| Midjourney | Midjourney Inc. | 艺术感强，Discord交互，付费订阅 | [midjourney.com](https://www.midjourney.com) |
| Stable Diffusion | Stability AI | 开源免费，本地部署，生态丰富 | [stability.ai](https://stability.ai) |
| DALL·E 3 | OpenAI | 自然语言理解强，集成ChatGPT | [openai.com/dall-e-3](https://openai.com/dall-e-3) |
| FLUX.2 | Black Forest Labs | 多图参考，4MP高清，开放权重 | [blackforestlabs.ai](https://blackforestlabs.ai) |
| ComfyUI | 开源社区 | 节点式工作流，高度可定制 | [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) |
| QClaw生图 | QClaw | 本地Agent集成，一键文生图/图生图 | [SKILL文档](#本地qclaw生图技能) |

#### 1.3 AI图片生成的应用场景
- 电商海报与产品图
- 社交媒体配图与表情包
- logo与品牌设计
- 插画与概念艺术
- 游戏与影视美术素材
- 个人创意创作

---

### 第二章 提示词工程（Prompt Engineering）

#### 2.1 提示词基础
- 什么是Prompt？为什么它决定生图质量
- 提示词的五大要素：**主体 + 场景/环境 + 风格/画风 + 光影/色调 + 构图/视角**
- 正向提示词与反向提示词

#### 2.2 提示词编写技巧
- 简短描述的扩写方法（≤5字 → 补充细节+场景+风格+光影）
- 关键词权重与括号嵌套（如 `((keyword:1.4))`）
- 自然语言描述 vs. 关键词堆叠
- Seed值的作用与可复现性

#### 2.3 风格关键词速查表

| 风格类别 | 推荐关键词 |
|---------|-----------|
| 摄影写实 | 摄影风格、浅景深、自然光、4K高清、细节丰富 |
| 插画动漫 | 二次元风格、动漫插画、赛璐璐、扁平插画 |
| 油画艺术 | 印象派油画、厚涂、笔触纹理、暖色调 |
| 水墨国风 | 水墨画风格、留白、宣纸质感、写意 |
| 设计海报 | 简约设计、渐变色彩、矢量风格、排版感 |
| 3D渲染 | 3D渲染、C4D风格、柔和光影、微距质感 |
| 像素复古 | 像素画风格、8-bit、复古配色 |

#### 2.4 提示词资源网站
| 网站 | 说明 | 链接 |
|------|------|------|
| PromptHero | 全球最大AI提示词社区，支持MJ/SD/DALL·E | [prompthero.com](https://prompthero.com) |
| Civitai | SD模型与提示词社区，海量资源 | [civitai.com](https://civitai.com) |
| Lexica.art | Stable Diffusion官方图库，附完整参数 | [lexica.art](https://lexica.art) |
| OpenArt.ai | 多平台AI画作与提示词检索 | [openart.ai](https://openart.ai) |
| Krea.ai | Prompt搜索引擎，百万级图像 | [krea.ai](https://www.krea.ai) |
| PublicPrompts | 高质量免费提示词库 | [publicprompts.art](https://publicprompts.art) |
| PromptFolder | MJ参数可视化辅助工具 | [promptfolder.com](https://promptfolder.com/midjourney-prompt-helper/) |
| LearnPrompt | 开源AI学习平台，适合新手 | [learnprompt.pro](https://www.learnprompt.pro/) |
| FlowGPT | 高质量提示词平台，含比赛与社区 | [flowgpt.com](https://flowgpt.com/) |

#### 2.5 参考教程
- [Midjourney快速入门教程（CSDN）](https://blog.csdn.net/ice_99/article/details/144446185)
- [Stable Diffusion提示词编写全面指南（CSDN）](https://blog.csdn.net/2401_84830464/article/details/145319859)
- [Stable Diffusion高质量Prompt写法（CSDN）](https://blog.csdn.net/yikezhuixun/article/details/131759255)
- [AI绘画入门教程重制版（CSDN）](https://blog.csdn.net/Android_XG/article/details/144104857)

---

### 第三章 Midjourney 完全指南

#### 3.1 注册与入门
- Discord账号注册与Midjourney服务器加入
- 订阅计划选择（Basic / Standard / Pro）
- 新手频道（#newbies）使用方法

#### 3.2 基础操作
- `/imagine` 命令详解
- U1-U4 放大与 V1-V4 变体操作
- 图片质量升级（Light/Beta Upscale Redo）
- 后缀参数：`--ar`、`--q`、`--v`、`--style` 等

#### 3.3 进阶技巧
- 图生图与混合生图（`/blend`）
- 通过图片反推关键词（`/describe`）
- Seed值在复现中的应用
- 灯光与风格词的高级用法

#### 3.4 实战案例
- Q版3D人物生成
- 泡泡玛特风格头像
- B端设计3D图标
- 电商海报制作
- 二次元模式生成

#### 3.5 参考资源
- [Midjourney官网](https://www.midjourney.com)
- [Midjourney使用教程（大屏时代）](https://www.dapingtime.com/article/130.html)
- [AI绘画Midjourney系统课（腾讯网）](https://new.qq.com/rain/a/20251222A01QC700)
- [Midjourney基础操作（今日头条）](https://www.toutiao.com/article/7231864322132050491/)
- [MJ动态图像生成教程PDF（原创力文档）](https://max.book118.com/html/2024/0919/8123027027006127.shtm)

---

### 第四章 Stable Diffusion 深度教程

#### 4.1 环境部署
- 本地部署（Windows / macOS / Linux）
- AUTOMATIC1111 WebUI 安装
- ComfyUI 安装与中文汉化
- 云端部署方案（AutoDL、腾讯云函数计算等）

#### 4.2 模型基础
- Checkpoint大模型选择与安装
- 常用模型推荐：Realistic Vision、Anything、DreamShaper 等
- 模型下载站点：[Civitai](https://civitai.com)、[LibLib（哩布哩布）](https://www.liblib.ai/)

#### 4.3 核心参数详解
- 采样器选择（DPM++ 2M Karras 等）
- 迭代步数（Steps）与引导系数（CFG Scale）
- 分辨率设置与高分辨率修复（Hires. fix）
- 批量生成与种子控制

#### 4.4 图生图与局部重绘
- 图生图基础操作
- Inpainting（局部重绘）—— 修改图片局部
- Outpainting（向外扩展）—— 扩展画面边界
- 图生图权重（Denoising strength）调优

#### 4.5 参考资源
- [Stable Diffusion入门手册（腾讯云）](https://cloud.tencent.com/developer/article/2264456)
- [SD代码指南（CSDN）](https://blog.csdn.net/m0_71746299/article/details/141884034)
- [SD文生图技术实现（CSDN）](https://blog.csdn.net/Java_Joker/article/details/145038773)
- [SD 3.5本地部署与远程出图（腾讯云）](https://cloud.tencent.com/developer/article/2480167)
- [SD原理深入解析（CSDN）](https://blog.csdn.net/2401_85688943/article/details/146419769)

---

### 第五章 ComfyUI 工作流

#### 5.1 ComfyUI 简介
- 节点式界面 vs. WebUI 表单式界面
- 为什么进阶用户更爱 ComfyUI

#### 5.2 安装与配置
- Windows 免安装版使用
- macOS 安装（Homebrew）
- 中文语言包安装
- 模型放置路径

#### 5.3 工作流搭建
- 基础文生图工作流
- 图生图工作流
- LoRA 加载节点
- 放大工作流

#### 5.4 插件与扩展
- ControlNet 节点
- IP-Adapter 节点
- Gemini Flash 图像编辑节点

#### 5.5 参考资源
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI安装与使用教程（搜狐）](https://www.sohu.com/a/832571325_121798711)
- [ComfyUI本地部署SD 3（搜狐）](https://www.sohu.com/a/785952969_100037970)
- [函数计算部署ComfyUI（腾讯网）](https://news.qq.com/rain/a/20241202A01FMB00)
- [ComfyUI-aki 版本介绍（搜狐）](https://www.sohu.com/a/858232281_121293452)

---

### 第六章 ControlNet 精准控制

#### 6.1 ControlNet 概述
- 什么是ControlNet？为什么需要它
- ControlNet 的工作原理

#### 6.2 安装与配置
- WebUI 插件安装
- 模型下载与放置路径
- 预处理器自动下载

#### 6.3 常用ControlNet模型

| 模型 | 功能 | 适用场景 |
|------|------|---------|
| Canny | 边缘检测 | 线稿生成、轮廓控制 |
| Depth | 深度图 | 空间层次控制 |
| OpenPose | 人体姿态 | 人物姿势控制 |
| MLSD | 直线检测 | 建筑/室内设计 |
| Lineart | 线稿 | 动漫线稿上色 |
| Soft Edge | 软边缘 | 自然过渡效果 |
| Scribble | 涂鸦 | 草图生成 |
| Segmentation | 语义分割 | 场景区域控制 |
| Tile/Blur | 细节处理 | 画面增强 |
| Inpaint | 局部重绘 | 精细修改 |
| Reference | 参考模仿 | 风格复刻 |
| IP-Adapter | 图像提示 | 风格迁移 |
| Recolor | 重新上色 | 色彩变换 |
| Instant ID | 即时特征 | 人脸保持 |

#### 6.4 多ControlNet叠加使用
- 同时使用多个ControlNet（最多4个）
- 权重平衡与效果调优

#### 6.5 参考资源
- [ControlNet安装与基础使用（B站）](https://www.bilibili.com/video/BV1us4y1v7hN/)
- [ControlNet插件教程（CSDN）](https://blog.csdn.net/Z20140628/article/details/146459705)
- [ControlNet 9种类型详解（CSDN）](https://blog.csdn.net/canadajasminestudio/article/details/141058770)
- [ControlNet精准控制（掘金）](https://juejin.cn/post/7273674981960237113)
- [ControlNet高仿参考（掘金）](https://juejin.cn/post/7266693534862229539)
- [ControlNet Inpaint向外扩展（今日头条）](https://www.toutiao.com/video/7240021052603059489/)

---

### 第七章 LoRA 模型与微调

#### 7.1 什么是LoRA
- LoRA（Low-Rank Adaptation）原理简介
- LoRA vs. Checkpoint 模型的区别
- LoRA 的优势：轻量、灵活、可叠加

#### 7.2 LoRA 使用方法
- LoRA 文件放置路径
- 在 WebUI / ComfyUI 中加载 LoRA
- LoRA 权重调节（`<lora:name:weight>`）
- 多LoRA叠加使用

#### 7.3 热门LoRA类型
- 风格LoRA（油画、水彩、赛博朋克等）
- 人物LoRA（特定角色/IP）
- 材质LoRA（黏土、毛绒、金属等）
- 场景LoRA（城市、自然、室内等）

#### 7.4 LoRA 模型资源
- [Civitai LoRA专区](https://civitai.com/models)
- [LibLib（哩布哩布）LoRA](https://www.liblib.ai/)
- [Hugging Face](https://huggingface.co/models)

---

### 第八章 DALL·E 3 与 OpenAI 生态

#### 8.1 DALL·E 3 特点
- 自然语言深度理解
- 集成ChatGPT使用
- 文字渲染能力

#### 8.2 使用方式
- 通过ChatGPT直接使用（GPT-4 + DALL·E 3）
- 通过OpenAI API调用
- 支持的分辨率：1024×1024、1024×1792、1792×1024

#### 8.3 API 调用示例
- Python SDK 调用示例
- Spring AI 集成（Java）
- CrewAI 智能体集成

#### 8.4 参考资源
- [OpenAI Images API文档](https://platform.openai.com/docs/guides/images)
- [DALL·E 3 API使用教程（CSDN）](https://blog.csdn.net/weixin_69960244/article/details/161033980)
- [Python调用DALL·E教程（腾讯云）](https://cloud.tencent.com/developer/article/2482500)
- [Spring AI + DALL·E 3（CSDN）](https://blog.csdn.net/xidianjiapei001/article/details/145431664)
- [ChatGPT图片生成API（博客园）](https://www.cnblogs.com/jerryqm/p/17837345.html)
- [DALL·E 3使用指南（博客园）](https://www.cnblogs.com/xing-star/p/how-to-use-dalle-3.html)

---

### 第九章 FLUX 模型系列

#### 9.1 Black Forest Labs 简介
- 团队背景（Stable Diffusion核心成员）
- 从FLUX.1到FLUX.2到FLUX.3的演进

#### 9.2 FLUX.2 模型家族
| 版本 | 定位 | 特点 |
|------|------|------|
| FLUX.2 [pro] | 最强闭源版 | 指令遵循强，画质顶级 |
| FLUX.2 [flex] | 开发者版 | 可控采样参数，文字渲染强 |
| FLUX.2 [dev] | 开源版（32B） | 文生图+多图编辑，功能完整 |
| FLUX.2 [klein] | 轻量快速版 | 亚秒级响应，实时交互 |

#### 9.3 FLUX 核心能力
- 多图参考融合（最多10张）
- 4MP高分辨率生成
- 文字渲染与信息图表
- 图像编辑与风格保持
- FP8量化：降40%显存，提升40%性能

#### 9.4 在ComfyUI中使用FLUX
- 模型加载与配置
- NVIDIA TensorRT 优化
- RTX GPU 要求

#### 9.5 参考资源
- [Black Forest Labs官网](https://blackforestlabs.ai)
- [FLUX.2发布报道（腾讯网）](https://new.qq.com/rain/a/20251126A06QC000)
- [FLUX.2一手速测（腾讯网）](https://new.qq.com/rain/a/20251126A03WUA00)
- [FLUX.2开源详解（CSDN）](https://blog.csdn.net/AdamsLi/article/details/155300326)
- [FLUX.2实测对比（腾讯网）](https://new.qq.com/rain/a/20251126A043I100)
- [FLUX实战指南（CSDN）](https://blog.csdn.net/weixin_30838873/article/details/99825426)
- [FLUX.2 Klein开源（腾讯网）](https://new.qq.com/rain/a/20260119A01UTU00)

---

### 第十章 图片放大与高清修复

#### 10.1 为什么需要AI放大
- 低分辨率图片的痛点
- 传统放大 vs. AI超分辨率

#### 10.2 主流放大工具

| 工具 | 特点 | 平台 | 链接 |
|------|------|------|------|
| Real-ESRGAN | 全能型，支持照片/动漫 | 全平台 | [GitHub](https://github.com/xinntao/Real-ESRGAN) |
| Upscayl | 开源免费，Vulkan加速 | 全平台 | [GitHub](https://github.com/upscayl/upscayl) |
| Real-ESRGAN-GUI | 图形界面，批量处理 | Win/Mac | [腾讯云介绍](https://cloud.tencent.com/developer/article/2656492) |
| SD Hires. fix | WebUI内置放大 | WebUI | — |
| Topaz Gigapixel | 商业软件，效果顶级 | Win/Mac | [topazlabs.com](https://www.topazlabs.com) |

#### 10.3 Real-ESRGAN 使用指南
- 命令行使用
- GUI版本安装与操作
- 模型选择：realesrgan-x4plus（通用）vs. realesrgan-x4plus-anime（动漫）
- 批量处理与GIF放大

#### 10.4 Upscayl 使用指南
- 安装与界面
- AI模型选择（通用照片/数字艺术/高保真）
- 放大倍数选择（2x / 4x）
- GPU加速配置

#### 10.5 参考资源
- [Real-ESRGAN GitHub](https://github.com/xinntao/Real-ESRGAN)
- [Real-ESRGAN GUI教程（CSDN）](https://blog.csdn.net/gitblog_00279/article/details/159715157)
- [Real-ESRGAN终极指南（CSDN）](https://blog.csdn.net/gitblog_00240/article/details/156325196)
- [Upscayl指南（CSDN）](https://blog.csdn.net/gitblog_00851/article/details/157161171)
- [Upscayl开源介绍（腾讯云）](https://cloud.tencent.com/developer/article/2592634)
- [老照片修复教程（CSDN）](https://blog.csdn.net/weixin_33670786/article/details/86184794)

---

### 第十一章 本地QClaw生图技能

#### 11.1 技能概述
- QClaw内置AI生图技能，支持文生图与图生图
- 自动处理任务提交、轮询等待、图片下载
- 鉴权由后台网关自动处理

#### 11.2 调用方式
- 文生图命令格式
- 图生图命令格式（支持本地路径、URL、多图）
- 参数说明：`--prompt`、`--images`、`--resolution`、`--revise`、`--seed`

#### 11.3 分辨率选择

| 比例 | 分辨率 | 适用场景 |
|------|--------|---------|
| 1:1 | 1024:1024 | 头像、社交配图（默认） |
| 4:3 | 1024:768 | 横构图、PPT配图 |
| 3:4 | 768:1024 | 竖构图、海报 |
| 16:9 | 1344:768 | 风景、桌面壁纸 |
| 9:16 | 768:1344 | 手机壁纸、人像 |

#### 11.4 技能源码结构
```
~/.qclaw/skills/qclaw-generate-image/
├── SKILL.md                    # 技能说明文档
└── scripts/
    ├── generate.cjs            # 主入口脚本
    └── lib/
        ├── config.cjs           # 配置（路径、超时、分辨率白名单）
        ├── http.cjs             # HTTP请求与图片下载
        ├── poll.cjs             # 任务轮询逻辑
        └── images.cjs           # 图片解析（本地→base64）
```

#### 11.5 核心流程
1. 参数解析 → 2. 提交任务（Submit）→ 3. 轮询状态（Poll）→ 4. 下载图片（Download）→ 5. 输出JSON结果

#### 11.6 错误处理
- 审核不合规内容
- 超时处理（最大180秒）
- 网络错误自动重试
- 下载失败返回临时URL

---

### 第十二章 AI图片生成的版权与法律

#### 12.1 AI生成图片的版权归属
- 国内首例"AI文生图"著作权案（2023京0491民初11279号）
- 最高人民法院指导案例（2025年3月）
- 核心原则：**体现人类独创性智力投入即受著作权法保护**
- 使用者通过提示词设计、参数调整、多轮筛选 → 享有版权
- 仅提供程式化指令 → 不构成作品

#### 12.2 商用风险与合规
- 使用合法授权数据集训练的AI工具
- 避免直接复制他人绘画风格/形象
- 注意素材的CC许可证（NC标记禁止商用）
- 使用公有领域素材或版权到期作品

#### 12.3 不同国家/地区法规差异
- 中国：倾向保护有人类智力投入的AI生成内容
- 美国：对纯AI生成内容拒绝版权登记
- 欧盟：AI法案相关条款

#### 12.4 参考资源
- [AI文生图著作权案详解（今日头条）](https://www.toutiao.com/article/7483131060701626934/)
- [AI生成图片版权分析（华律网）](https://www.66law.cn/laws/4000606.aspx)
- [AI绘画知识产权（网易）](https://www.163.com/dy/article/I92ABJ3I0512H2QF.html)
- [生成式AI美术作品著作权（企鹅号）](https://so.html5.qq.com/page/real/search_news?docid=70000021_3196a6c519709752)

---

### 第十三章 实战项目合集

#### 13.1 电商产品图生成
- 产品白底图 → 场景图转换
- 多角度产品图一致性保持
- 海报排版与文字配合

#### 13.2 社交媒体内容创作
- 微信/小红书配图制作
- 表情包生成（文字+角色）
- 头像定制（泡泡玛特风格、Q版3D）

#### 13.3 品牌设计
- Logo生成与迭代
- 吉祥物设计
- 品牌色彩体系探索

#### 13.4 艺术创作
- 中国风水墨画生成
- 赛博朋克城市夜景
- 印象派油画风格
- 微距摄影效果

#### 13.5 建筑与室内设计
- 线稿→效果图（ControlNet Canny/MLSD）
- 室内风格转换
- 户型图渲染

---

### 第十四章 附录

#### 14.1 术语表

| 术语 | 解释 |
|------|------|
| Diffusion Model | 扩散模型，通过逐步去噪生成图像的深度学习模型 |
| Checkpoint | 大模型文件，包含完整的生成能力 |
| LoRA | 低秩适配器，轻量微调模型 |
| ControlNet | 条件控制网络，用于精准控制生成结果 |
| Embedding | 文本编码向量，可将关键词映射为语义表示 |
| VAE | 变分自编码器，负责潜空间与像素空间的转换 |
| CFG Scale | 引导系数，控制提示词对生成结果的影响程度 |
| Sampler | 采样器，控制去噪过程的算法 |
| Steps | 迭代步数，影响生成质量与速度 |
| Seed | 随机种子，相同种子+提示词可复现结果 |
| Inpainting | 局部重绘，修改图片的特定区域 |
| Outpainting | 向外扩展，扩大图片画幅 |
| Hires. fix | 高分辨率修复，提升出图清晰度 |
| textual inversion | 文本反转，通过少量图片训练自定义概念 |
| Hypernetwork | 超网络，一种微调方法 |

#### 14.2 模型下载站点汇总

| 站点 | 内容 | 链接 |
|------|------|------|
| Civitai | 最大SD模型/LoRA社区 | [civitai.com](https://civitai.com) |
| Hugging Face | 开源模型平台 | [huggingface.co](https://huggingface.co) |
| LibLib（哩布哩布） | 国内SD模型社区 | [liblib.ai](https://www.liblib.ai/) |
| Stability AI | SD官方模型 | [stability.ai](https://stability.ai) |
| Black Forest Labs | FLUX系列模型 | [blackforestlabs.ai](https://blackforestlabs.ai) |

#### 14.3 推荐硬件配置

| 用途 | 显卡 | 内存 | 存储 |
|------|------|------|------|
| 入门体验 | RTX 3060 12GB | 16GB | 50GB SSD |
| 日常创作 | RTX 4070 12GB | 32GB | 100GB SSD |
| 进阶生产 | RTX 4090 24GB | 64GB | 200GB NVMe |
| 专业渲染 | RTX 5090 32GB | 64GB+ | 500GB NVMe |

> macOS用户：M1/M2/M3芯片 16GB统一内存可运行SD 1.5，32GB以上推荐运行SDXL/FLUX

#### 14.4 在线生图平台

| 平台 | 特点 | 链接 |
|------|------|------|
| Midjourney | 艺术感最强，Discord交互 | [midjourney.com](https://www.midjourney.com) |
| ChatGPT (DALL·E 3) | 自然语言对话生图 | [chat.openai.com](https://chat.openai.com) |
| Leonardo AI | 支持ControlNet，免费额度 | [leonardo.ai](https://leonardo.ai) |
| 文心一格 | 百度AI生图 | [yige.baidu.com](https://yige.baidu.com) |
| 通义万相 | 阿里AI生图 | [tongyi.aliyun.com](https://tongyi.aliyun.com/wanxiang) |
| 即梦Dreamina | 字节跳动AI生图 | [jimeng.jianying.com](https://jimeng.jianying.com) |
| LibLib在线 | 国内SD在线生图 | [liblib.ai](https://www.liblib.ai/) |

---

## 本地技能文件路径索引

| 资源 | 路径 |
|------|------|
| QClaw生图技能说明 | `~/.qclaw/skills/qclaw-generate-image/SKILL.md` |
| 主入口脚本 | `~/.qclaw/skills/qclaw-generate-image/scripts/generate.cjs` |
| 配置文件 | `~/.qclaw/skills/qclaw-generate-image/scripts/lib/config.cjs` |
| HTTP通信模块 | `~/.qclaw/skills/qclaw-generate-image/scripts/lib/http.cjs` |
| 轮询模块 | `~/.qclaw/skills/qclaw-generate-image/scripts/lib/poll.cjs` |
| 图片解析模块 | `~/.qclaw/skills/qclaw-generate-image/scripts/lib/images.cjs` |
| 图片输出目录 | `<workspace>/generated-images/` |

---

> 📖 **说明**：本目录为图书编写框架，所有章节均附有对应资源链接（官网、教程、GitHub仓库等），可点击链接跳转查看详细内容。本地QClaw生图技能部分可直接通过文件路径查看源码。

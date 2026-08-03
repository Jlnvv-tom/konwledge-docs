---
sidebar_position: 4
---

# 第四章 Stable Diffusion 深度教程

## 开篇

你以为AI画图就是输入几个词然后等运气？那是因为你还没碰过Stable Diffusion的参数面板。当别人还在用在线工具盲猜提示词的时候，掌握本地部署和参数调优的人已经能稳定产出商业级画质的作品了。这一章，怕浪猫带你从零搭建完整的SD环境，把每一个核心参数拆开揉碎讲清楚。学完这章，你不再是一个"抽卡玩家"，而是一个真正掌控画面的创作者。

我是怕浪猫，一个在AI绘画领域踩过无数坑的技术写手。接下来这一万字，可能是你见过最实操的SD入门指南。

## 4.1 环境部署

### 4.1.1 本地部署概述

Stable Diffusion的本地部署并不复杂，但对硬件有一定要求。你的显卡显存至少需要8GB才能流畅运行SD 1.5系列模型，如果想跑SDXL则建议12GB以上。操作系统方面，Windows、macOS和Linux都可以部署，但Windows的CUDA生态最成熟，遇到的坑最少。macOS用户只能用CPU或Apple Silicon的MPS加速，出图速度大约是NVIDIA显卡的三分之一。

部署的核心是两件事：装好Python环境和PyTorch，然后拉取WebUI或ComfyUI的前端项目。下面怕浪猫按系统分别讲解。

### 4.1.2 Windows本地部署

Windows是最推荐的本地部署平台，因为NVIDIA显卡驱动和CUDA工具链在Windows上配置最简单。首先确保你安装了Python 3.10.6版本，不要用3.11或更高版本，因为部分依赖库尚未完全适配。从python.org下载安装包时，务必勾选"Add Python to PATH"选项。

安装完成后打开命令行，依次执行以下命令拉取AUTOMATIC1111 WebUI：

```bash
# 克隆WebUI仓库
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git

# 进入项目目录
cd stable-diffusion-webui

# 运行启动脚本（首次运行会自动安装所有依赖）
webui-user.bat
```

首次启动时脚本会自动下载PyTorch、Transformers等依赖，整个过程可能需要20到40分钟，取决于你的网络状况。如果你在国内，建议提前配置好pip镜像源和Git代理，否则下载速度会非常慢。启动成功后浏览器会自动打开 `http://127.0.0.1:7860`，看到WebUI界面就说明部署完成了。

关键配置文件 `webui-user.bat` 中有几个重要参数需要了解：

```python
# webui-user.bat 关键配置
set PYTHON=python
set GIT=git
set COMMANDLINE_ARGS=--xformers --medvram --autolaunch
# --xformers: 启用xformers加速，显著降低显存占用
# --medvram: 中等显存优化，8GB显存建议开启
# --autolaunch: 启动后自动打开浏览器
```

### 4.1.3 macOS本地部署

macOS部署SD的主要优势是Apple Silicon芯片的统一内存架构。M1/M2/M3系列芯片可以调用统一内存作为显存使用，16GB内存的MacBook可以跑SD 1.5，32GB以上可以尝试SDXL。但Mac的推理速度确实比NVIDIA显卡慢不少，M2 Pro跑一张512x512的图大约需要15到30秒。

部署步骤与Windows类似，但需要修改启动脚本中的设备参数：

```bash
# macOS 启动命令
export COMMANDLINE_ARGS="--opt-sub-quad-attention --upcast-sampling --use-command-line-names"
./webui.sh
```

macOS用户如果遇到MPS相关的报错，可以尝试在启动参数中加上 `--use-cpu all` 来回退到CPU模式排查问题。怕浪猫建议Mac用户优先考虑ComfyUI，因为ComfyUI的节点式架构对内存管理更精细，在Mac上的稳定性和速度都略优于WebUI。

### 4.1.4 Linux本地部署

Linux部署最适合服务器环境和云端实例。以Ubuntu 22.04为例，先安装系统级依赖：

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv git build-essential -y

# 安装NVIDIA驱动和CUDA（如果尚未安装）
sudo apt install nvidia-driver-535 -y

# 克隆WebUI
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui
./webui.sh
```

Linux部署的优势是可以通过SSH远程管理，配合Tmux或Screen可以实现后台常驻运行。如果你打算长期使用，建议用Systemd配置开机自启服务。Linux环境下很少遇到路径和权限问题，是三种系统中部署体验最顺畅的。

### 4.1.5 AUTOMATIC1111 WebUI安装详解

AUTOMATIC1111（简称A1111）是最主流的SD前端界面，它的WebUI提供了图形化的操作面板，让用户无需编写代码就能完成文生图、图生图等操作。前面已经介绍了基本安装流程，这里补充几个关键配置。

安装完成后，模型文件需要放到 `models/Stable-diffusion/` 目录下。VAE（Variational Autoencoder，变分自编码器）文件放到 `models/VAE/` 目录。Lora（Low-Rank Adaptation，低秩适配）模型放到 `models/Lora/` 目录。这些路径在启动后也可以通过WebUI界面的"Settings"页面修改。

A1111支持扩展插件系统，常用的扩展包括中文汉化包、ControlNet、OpenPose编辑器等。安装扩展的方法是在WebUI的"Extensions"标签页中，通过URL安装或从列表中选择。怕浪猫推荐的必装扩展列表如下：

```python
# 推荐扩展列表
extensions = [
    "https://github.com/VinsonLaro/stable-diffusion-webui-localization-zh_Hans",  # 中文汉化
    "https://github.com/Mikubill/sd-webui-controlnet",  # ControlNet
    "https://github.com/deforum-art/deforum-for-automatic1111-webui",  # 动画生成
    "https://github.com/camenduru/openpose-editor",  # OpenPose编辑
    "https://github.com/DominikDunn/a1111-sd-webui-lycoris",  # LyCORIS支持
]
```

### 4.1.6 ComfyUI安装与中文汉化

ComfyUI是另一个主流的SD前端，与A1111的表单式界面不同，ComfyUI采用节点式工作流。每个功能模块（如加载模型、文本编码、采样、解码）都是一个可视化节点，用户通过连线的方式构建出图流程。这种设计在灵活性上远超A1111，特别适合需要定制复杂工作流的高级用户。

安装ComfyUI的命令如下：

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
python main.py
```

ComfyUI默认访问 `http://127.0.0.1:8188`。界面是全英文的，需要安装中文汉化插件。在ComfyUI的Manager菜单中选择"Install via Git URL"，输入汉化插件地址：

```bash
# ComfyUI中文汉化插件
https://github.com/AIGODLIKE-COMMUNITY/AIGODLIKE-ComfyUI-Translation
```

安装完成后在设置中切换语言为中文即可。ComfyUI的模型目录结构与A1111略有不同，模型放在 `models/checkpoints/`，VAE放在 `models/vae/`，Lora放在 `models/loras/`。如果你已经安装了A1111，可以在ComfyUI的配置文件 `extra_model_paths.yaml` 中指向A1111的模型目录，实现模型共享。

### 4.1.7 云端部署方案

如果你的本地硬件不够用，云端部署是最经济的选择。国内最流行的方案是AutoDL，它提供按量计费的GPU实例，RTX 4090每小时大约2到3元。AutoDL自带SD镜像，创建实例时选择"Stable Diffusion WebUI"镜像即可，无需手动部署。

```bash
# AutoDL实例启动后，添加端口映射访问WebUI
# 在AutoDL的"自定义服务"中直接点击即可访问7860端口

# 如果需要手动启动，进入容器后执行
cd /root/stable-diffusion-webui
python launch.py --share --listen
```

另一个方案是腾讯云函数计算，它支持GPU函数的按量调用。适合不需要长时间运行、只在需要时出图的场景。腾讯云函数计算部署SD的优势是无需管理服务器，按调用次数和执行时长计费。但冷启动时间较长，大约需要30秒到1分钟。

对于需要稳定访问的用户，怕浪猫推荐AutoDL的包月方案，一台RTX 4090包月大约400到500元，足够日常使用。云端部署的另一个好处是方便团队协作，多人可以同时访问同一个实例。

## 4.2 模型基础

### 4.2.1 Checkpoint大模型选择与安装

Stable Diffusion的核心是Checkpoint大模型，它包含了完整的UNet（United Network，统一网络）、Text Encoder（文本编码器）和VAE三个组件。Checkpoint文件通常是 `.safetensors` 或 `.ckpt` 格式，大小在2GB到7GB之间。SD 1.5系列的模型约2GB，SDXL模型约6.5GB。

安装模型非常简单，只需将下载的模型文件放入 `models/Stable-diffusion/` 目录，然后在WebUI中刷新模型列表即可。模型文件命名建议保持英文，避免中文导致的加载错误。如果你同时安装了多个模型，可以在WebUI左上角的模型选择器中切换。

不同模型擅长不同的画风领域，选择合适的模型是出好图的第一步。怕浪猫建议新手从通用型模型开始，熟练后再转向特定风格的专用模型。下面介绍几款常用模型。

### 4.2.2 常用模型推荐

**Realistic Vision** 是目前最流行的写实风格模型，擅长生成照片级的人物肖像和风景。它的肤色还原和光影表现非常出色，适合做商业摄影风格的图像。提示词建议使用自然的英文描述，配合适当的负面提示词效果最佳。

**Anything V5** 是二次元风格的首选模型，对动漫角色的表现力极强。它的色彩饱和度高，线条干净利落，非常适合生成日系动漫风格的角色立绘。如果你主要画二次元，Anything系列是不二之选。与之类似的还有 **Counterfeit** 和 **OrangeMix**，各有细微的风格差异。

**DreamShaper** 是一个通用型模型，在写实和半写实之间取得了不错的平衡。它对提示词的响应非常灵敏，同样的提示词在DreamShaper上往往能产出更丰富的细节。这个模型适合不确定风格方向时的探索性创作，也适合做LoRA训练的基础模型。

其他值得关注的模型包括：**Deliberate**（多功能通用）、**ChilloutMix**（亚洲面孔写实）、**MajicMix**（时尚人像）、**Rev Animated**（3D动画风格）。选择模型时建议先去Civitai查看示例图和用户评价，再决定是否下载。

### 4.2.3 模型下载站点

**Civitai**（https://civitai.com）是全球最大的SD模型社区，拥有数万个Checkpoint、LoRA、Embedding等模型资源。Civitai的模型页面会展示大量用户生成的示例图，方便你判断模型风格是否符合需求。站点支持按模型类型、基础架构、标签等多维度筛选，也提供API供开发者调用。

Civitai的下载方式有两种：直接下载和通过"Blue Noon"等下载器。免费用户有每日下载限额，付费订阅可以取消限制。模型页面通常会标注推荐的采样器、步数和CFG值，这些参数可以作为出图的初始参考。

**LibLib**（https://www.liblib.ai/）是国内最大的SD模型平台，也被称为"哩布哩布"。它的模型库规模仅次于Civitai，但访问速度在国内更快，无需科学上网。LibLib还提供在线生图功能，无需本地部署也能体验不同模型的效果。

两个平台都支持创作者上传模型并设置付费下载。如果你训练了自己的LoRA模型，也可以考虑在这些平台上发布。怕浪猫建议两个站点都注册，Civitai用于发现新模型和国际社区的优质内容，LibLib用于快速下载和国内交流。

## 4.3 核心参数详解

### 4.3.1 采样器选择

采样器（Sampler）是SD生成图像的核心算法，它决定了模型如何从随机噪声中逐步"雕刻"出图像。SD的采样过程基于扩散模型的理论框架：前向过程逐步给图像添加高斯噪声直到变成纯噪声，反向过程则从纯噪声出发，逐步去噪还原出图像。采样器就是执行这个反向去噪过程的算法。

不同采样器的数学原理和策略不同，导致出图速度和画质各有差异。以下是几款主流采样器的对比：

| 采样器 | 算法原理 | 推荐步数 | 速度 | 画面特点 |
|--------|---------|---------|------|---------|
| Euler a | 基于欧拉法的祖先采样，每步引入随机噪声 | 20-30 | 快 | 画面柔和，细节偏少，适合快速预览 |
| DPM++ 2M Karras | DPM++系列的多步法，配合Karras噪声调度 | 20-30 | 中等 | 细节丰富，画面干净，最推荐的通用采样器 |
| DPM++ SDE Karras | DPM++的随机微分方程版本 | 10-15 | 较慢 | 细节极丰富，适合最终出图 |
| DDIM | 去噪扩散隐式模型，经典算法 | 30-50 | 中等 | 画面稳定，可重复性好 |
| UniPC | 统一预测校正器 | 15-25 | 快 | 速度与质量平衡好，新晋推荐 |

**DPM++ 2M Karras** 是怕浪猫最推荐的日常使用采样器。DPM++（Denoising Diffusion Probabilistic Models with Preconditioned scores）是对原始DDPM采样器的改进，通过更优的数值积分方法减少所需步数。Karras调度（Karras Noise Schedule）是一种噪声衰减策略，它在前几步用较大的步长快速去除大量噪声，在后几步用小步长精细打磨细节。这种策略比传统的线性调度更高效。

选择采样器的实用建议：快速测试用Euler a，日常出图用DPM++ 2M Karras，追求极致细节用DPM++ SDE Karras。不建议在同一个项目里频繁切换采样器，因为不同采样器的画面风格差异较大，不利于建立稳定的出图预期。

### 4.3.2 迭代步数与引导系数

迭代步数（Steps）控制采样器执行多少次去噪操作。步数太少图像会模糊粗糙，因为噪声没有完全去除。步数太多则边际收益递减，20步之后画质的提升就很不明显了，反而可能过度计算导致画面出现伪影。大多数情况下，20到30步就能获得高质量结果。

引导系数（CFG Scale，Classifier Free Guidance Scale）控制提示词对生成结果的引导强度。CFG值为1时，模型几乎忽略提示词，生成完全随机的图像。CFG值越高，模型越"用力"地遵循提示词，但过高会导致画面过饱和、对比度异常和局部伪影。以下是CFG值的参考范围：

```python
# CFG Scale 参考配置
cfg_presets = {
    "创意探索": 3.0,      # 画面自由度高，适合找灵感
    "平衡模式": 7.0,      # 默认值，提示词遵循与画面质量平衡
    "严格遵循": 12.0,     # 强力遵循提示词，可能出现过饱和
    "极限控制": 15.0,    # 仅用于特定需求，画质有损
}

# Steps 推荐配置
steps_presets = {
    "快速预览": 15,       # 10秒内出图，用于测试提示词
    "日常出图": 25,       # 速度与质量的最佳平衡点
    "高质量": 35,         # 追求细节的场景
    "极限质量": 50,       # 边际收益极低，不推荐日常使用
}
```

步数和CFG需要配合调整。高CFG（12以上）时建议适当增加步数，让模型有足够的迭代次数来消化提示词的引导信号。低CFG（3到5）时步数可以减少到15到20步。一个经典的组合是：DPM++ 2M Karras采样器，25步，CFG 7.0。这个配置在速度和质量之间取得了最佳平衡，也是怕浪猫最常用的参数组合。

### 4.3.3 分辨率设置与高分辨率修复

SD 1.5模型的默认训练分辨率是512x512，直接生成其他分辨率的图像可能出现构图问题。虽然WebUI允许你设置任意分辨率，但如果偏离512太多，模型可能会在画面中重复生成多个主体或出现奇怪的布局。常见的分辨率组合有：512x512（方形）、512x768（竖版人像）、768x512（横版风景）。

如果要生成高分辨率图像，正确做法是先用基础分辨率生成，再通过高分辨率修复（Hires. fix）进行放大。Hires. fix的工作原理是：先用低分辨率生成初始图像，然后使用放大算法（如Latent放大或ESRGAN）将图像放大到目标分辨率，再在放大后的图像上执行少量去噪步骤来修复细节。

```python
# Hires. fix 关键参数配置
hires_config = {
    "upscaler": "Latent",        # 放大算法，Latent效果最自然
    "upscale_by": 1.5,           # 放大倍数，1.5倍是安全选择
    "denoising_strength": 0.4,   # 去噪强度，0.3-0.5之间最佳
    "steps": 15,                 # 高分辨率阶段的步数，15步足够
}

# 高分辨率修复的完整参数链
# 基础: 512x768, Steps=25, CFG=7.0
# Hires: Latent x1.5, Denoising=0.4, Steps=15
# 最终输出: 768x1152
```

Denoising strength（去噪强度）是Hires. fix中最重要的参数。值为0时不做任何修改，值为1时完全重新生成。0.3到0.5之间的值能在保留原图构图的同时添加细节。如果值太低，放大后的图像会显得模糊。如果值太高，放大后的图像会与原图差异很大，失去高分辨率修复的意义。

对于SDXL模型，默认训练分辨率是1024x1024，可以直接生成高分辨率图像而无需Hires. fix。但SDXL对显存要求更高，8GB显存可能需要开启 `--medvram` 参数。

### 4.3.4 批量生成与种子控制

种子（Seed）是SD生成过程中的随机数起点，决定了初始噪声的分布。相同的种子、相同的提示词和参数会生成完全一致的图像。种子值为-1时表示随机生成，每次结果都不同。当你对某张图比较满意但想微调时，可以固定该图的种子，然后只修改提示词或参数，观察变化。

批量生成有两种方式。第一种是固定种子、修改提示词，用于系统性地探索某个提示词变体的效果。第二种是固定提示词、随机种子，用于从多个随机结果中挑选最佳的一张。WebUI的"Batch count"控制生成几批，"Batch size"控制每批生成几张。

```python
# 批量生成的实用策略
# 策略1：快速筛选 - 大批量低质量
batch_screening = {
    "batch_count": 5,
    "batch_size": 4,
    "steps": 15,          # 低步数快速生成
    "sampler": "Euler a", # 快速采样器
    "cfg_scale": 7.0,
}
# 一次生成20张缩略图，从中挑选构图满意的

# 策略2：精修出图 - 小批量高质量
batch_final = {
    "batch_count": 1,
    "batch_size": 4,
    "steps": 30,                  # 高步数精细生成
    "sampler": "DPM++ SDE Karras",# 高质量采样器
    "cfg_scale": 7.0,
    "hires_fix": True,
    "denoising_strength": 0.4,
}
# 从筛选出的种子出发，精修4张高质量图
```

怕浪猫的常用工作流是：先用低步数大批量生成20张缩略图，挑选构图和姿势最满意的2到3张，记下它们的种子值。然后固定种子，切换到高质量参数重新生成，配合Hires. fix输出最终图像。这个流程能在效率和质量之间取得最佳平衡。

## 4.4 图生图与局部重绘

### 4.4.1 图生图基础操作

图生图（Image-to-Image，简称img2img）是SD的核心功能之一。与文生图从纯噪声开始不同，图生图从一张已有的图像出发，在此基础上进行修改和重绘。输入的图像会被编码到潜在空间并添加噪声，然后由采样器从带噪声的潜在表示出发执行去噪过程。

图生图最关键的参数是Denoising strength（去噪强度），它控制对输入图像的修改幅度。值为0时输出与输入完全相同，值为1时完全忽略输入图像等同于文生图。实际使用中，0.3到0.6是最常用的范围。

```python
# 图生图典型参数配置
img2img_config = {
    "denoising_strength": 0.45,   # 核心参数：修改幅度
    "steps": 25,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras",
    "resize_mode": "Just resize", # 直接缩放，不裁剪
}

# 去噪强度参考表
denoising_guide = {
    0.15: "微调，仅改变色彩和纹理细节",
    0.30: "轻度修改，保持构图，改变风格",
    0.45: "中度修改，保留大致构图，显著改变细节",
    0.60: "大幅修改，构图可能变化",
    0.75: "几乎重绘，仅保留模糊的初始结构",
}
```

图生图的典型应用场景包括：将草图细化为完整作品、改变已有图像的风格（如照片转油画）、对已有AI生成图像进行二次优化。在创作工作流中，图生图常与ControlNet配合使用，先用ControlNet提取输入图像的结构信息，再通过图生图在保持结构的前提下改变画面内容。

### 4.4.2 Inpainting 局部重绘

Inpainting（局部重绘）是图生图的一个特殊模式，允许你只在图像的指定区域进行重绘，其余部分保持不变。操作方式是在WebUI的img2img标签页中切换到"Inpaint"子标签，用画笔工具在图像上涂抹出需要修改的区域，然后输入提示词并生成。

Inpainting的技术原理是在潜在空间中对蒙版区域进行去噪，同时保持非蒙版区域的潜在表示不变。这需要在采样过程中动态控制噪声添加的范围，只对蒙版区域执行前向加噪和反向去噪。A1111 WebUI的Inpainting功能还支持蒙版模糊（Mask blur），通过模糊蒙版边缘使重绘区域与原图的过渡更自然。

```python
# Inpainting 参数配置
inpaint_config = {
    "denoising_strength": 0.6,    # 局部重绘通常需要较高去噪强度
    "mask_blur": 4,               # 蒙版边缘模糊像素数
    "inpainting_fill": "original",# 填充方式：original/latent noise/latent nothing
    "inpaint_full_res": True,     # 全分辨率重绘
    "inpaint_full_res_padding": 32,# 全分辨率模式的边缘填充
    "steps": 30,
    "cfg_scale": 7.0,
}
```

Inpainting的实用技巧：修改蒙版区域的内容时（如把猫换成狗），去噪强度设为0.5到0.7。仅优化细节时（如修复手指变形），去噪强度设为0.3到0.4。蒙版范围不要太小，否则重绘区域可能缺乏上下文信息导致不自然。如果多次重绘后边缘有明显接缝，可以增大Mask blur值或使用"Only masked"模式。

### 4.4.3 Outpainting 向外扩展

Outpainting（向外扩展）与Inpainting相反，它是在原图的基础上向外扩展画面。SD 2.0以后内置了对Outpainting的支持，A1111 WebUI在img2img标签页中提供了"Outpaint"子标签。操作时选择扩展方向（上/下/左/右），设置扩展的像素数，然后生成。

Outpainting的核心挑战是保持扩展区域与原图在风格、光照和透视上的一致性。模型需要"理解"原图边缘的内容，然后向外延伸合理的画面。这比Inpainting更困难，因为模型没有边缘外的上下文参考。

```python
# Outpainting 参数配置
outpaint_config = {
    "denoising_strength": 0.8,    # 高去噪强度，因为需要生成大量新内容
    "steps": 30,
    "cfg_scale": 7.0,
    "pixels_per_expand": 128,     # 每次扩展的像素数
    "direction": ["left", "right"], # 扩展方向
    "sampler": "DPM++ 2M Karras",
}

# Outpainting 最佳实践
# 1. 每次只扩展一个方向，避免同时四向扩展
# 2. 扩展步长不要太大，64-128像素为宜
# 3. 多次迭代扩展比一次大范围扩展效果更好
# 4. 提示词中描述完整的画面场景，不只是原图内容
```

怕浪猫在做Outpainting时习惯的流程是：先确定目标画幅比例，计算需要扩展的总像素数，然后每次扩展64像素，循环多次直到达到目标尺寸。每次扩展后检查接缝处是否自然，不自然的地方用Inpainting修复。虽然这个流程比较慢，但效果最可控。

### 4.4.4 图生图权重调优

Denoising strength是图生图系列功能中最关键的参数，本节深入讲解它的调优策略。从数学角度理解，去噪强度决定了输入图像被添加多少噪声。强度为0.3意味着在扩散过程的第30%处开始反向去噪，保留70%的原始信息。强度为0.6则在第60%处开始，只保留40%的原始信息。

不同任务类型有各自的最佳去噪强度范围。以下是一个综合参考表：

| 任务类型 | 去噪强度 | 说明 |
|---------|---------|------|
| 风格迁移 | 0.4-0.6 | 保留构图，大幅改变风格纹理 |
| 细节增强 | 0.2-0.3 | 仅优化细节，不改变整体内容 |
| 局部修改 | 0.5-0.7 | Inpainting修改特定区域内容 |
| 向外扩展 | 0.7-0.9 | 需要生成大量新内容 |
| 草图上色 | 0.5-0.65 | 保留线条结构，添加色彩和质感 |
| 照片修复 | 0.15-0.25 | 轻微修复，避免改变人脸特征 |

```python
# 图生图权重调优实验代码
# 用Python脚本系统测试不同去噪强度
import requests
import base64

def img2img_test(image_path, prompt, denoising_range):
    """测试不同去噪强度对同一张图的效果"""
    url = "http://127.0.0.1:7860/sdapi/v1/img2img"
    
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    results = []
    for strength in denoising_range:
        payload = {
            "init_images": [img_b64],
            "prompt": prompt,
            "denoising_strength": strength,
            "steps": 25,
            "cfg_scale": 7.0,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
        }
        response = requests.post(url, json=payload)
        result = response.json()
        results.append({
            "denoising": strength,
            "image": result["images"][0]
        })
        print(f"Denoising {strength:.2f} done")
    
    return results

# 测试0.2到0.8，步长0.1
results = img2img_test(
    "input.png", 
    "a beautiful landscape painting, oil painting style",
    [i * 0.1 for i in range(2, 9)]
)
```

调优去噪强度的核心原则是：先用中等强度（0.5）试水，根据结果判断需要增大还是减小。如果修改幅度不够，逐步增大到0.6、0.7。如果修改过度破坏了原始构图，降回到0.3、0.4。每次调整幅度不要超过0.1，避免跳变太大导致难以判断效果趋势。

在实际创作中，图生图的各种模式很少孤立使用。一个完整的作品往往会经历：文生图生成初稿，Inpainting修复局部问题，Outpainting扩展画幅，再用图生图做整体风格统一。怕浪猫建议把图生图视为一个工具集合，灵活组合使用。

## 4.5 参考资源

学习Stable Diffusion是一个持续的过程，本章的内容只是入门。以下是怕浪猫整理的优质参考资源，涵盖从入门到进阶的各个阶段。

**Stable Diffusion入门手册**（https://cloud.tencent.com/developer/article/2264456）：这篇腾讯云社区的文章系统介绍了SD的基本概念和操作流程，适合零基础新手阅读。内容涵盖模型安装、基础参数设置和常见问题解答，可以作为本章的补充阅读材料。

**SD代码指南**（https://blog.csdn.net/m0_71746299/article/details/141884034）：CSDN上的这篇教程深入到代码层面，讲解了如何用Python调用SD的推理API。如果你想在项目中集成SD的出图能力，这篇指南提供了从环境配置到API调用的完整代码示例。

**SD文生图技术实现**（https://blog.csdn.net/Java_Joker/article/details/145038773）：这篇文章从技术实现的角度剖析了文生图的完整流程，包括文本编码、潜在空间扩散和图像解码的每个环节。适合想深入理解SD内部原理的开发者。

**SD 3.5本地部署**（https://cloud.tencent.com/developer/article/2480167）：Stable Diffusion 3.5是最新的版本，采用了MMDiT（Multimodal Diffusion Transformer，多模态扩散Transformer）架构。这篇腾讯云的文章详细介绍了SD 3.5的本地部署过程和与1.5/XL版本的差异。

**SD原理深入解析**（https://blog.csdn.net/2401_85688943/article/details/146419769）：CSDN上的这篇深度解析文章从扩散模型的数学原理出发，逐步推导SD的前向加噪和反向去噪过程。文章中还包含了详细的公式推导和代码对照，适合有数学背景的读者。

## 参数配置速查表

为方便日常使用，怕浪猫把本章涉及的所有核心参数整理成速查表，建议收藏备用。

| 场景 | 采样器 | Steps | CFG | 分辨率 | Hires | Denoising | 备注 |
|------|--------|-------|-----|--------|-------|-----------|------|
| 快速预览 | Euler a | 15 | 7.0 | 512x512 | 关 | - | 10秒内出图 |
| 日常出图 | DPM++ 2M Karras | 25 | 7.0 | 512x768 | 关 | - | 速度质量平衡 |
| 高质量出图 | DPM++ SDE Karras | 30 | 7.0 | 512x768 | 开 | 0.4 | 细节丰富 |
| 二次元 | DPM++ 2M Karras | 25 | 7.0 | 512x768 | 可选 | 0.35 | 搭配Anything模型 |
| 写实人像 | DPM++ SDE Karras | 30 | 6.5 | 512x768 | 开 | 0.4 | 搭配Realistic Vision |
| 图生图风格迁移 | DPM++ 2M Karras | 25 | 7.0 | 原图尺寸 | 关 | 0.45 | 保持构图 |
| 局部重绘 | DPM++ 2M Karras | 30 | 7.5 | 原图尺寸 | 关 | 0.6 | Mask blur=4 |
| 向外扩展 | DPM++ 2M Karras | 30 | 7.0 | 扩展后尺寸 | 关 | 0.8 | 分方向逐步扩展 |
| SDXL出图 | DPM++ 2M Karras | 25 | 5.0 | 1024x1024 | 关 | - | CFG建议4-6 |

## 采样器对比速查表

| 采样器 | 速度 | 细节 | 稳定性 | 推荐步数 | 适用场景 |
|--------|------|------|--------|---------|---------|
| Euler a | 极快 | 低 | 中 | 20 | 快速预览、抽象风格 |
| Euler | 快 | 中 | 高 | 25 | 稳定出图、可复现 |
| DDIM | 中 | 中 | 高 | 30-50 | 经典算法、学术对比 |
| DPM++ 2M Karras | 中 | 高 | 高 | 20-30 | 通用首选 |
| DPM++ SDE Karras | 慢 | 极高 | 高 | 10-15 | 极致细节、最终出图 |
| DPM++ 2M SDE | 中 | 高 | 高 | 20-30 | 细节与速度兼顾 |
| UniPC | 快 | 高 | 中 | 15-25 | 新兴选择、速度快 |
| LMS | 快 | 中 | 中 | 20-30 | 线性多步法 |

## 结语

本章从环境部署讲起，覆盖了SD的本地部署、云端部署方案，然后深入到模型选择、核心参数调优、图生图与局部重绘的完整知识体系。这些内容构成了SD日常使用的核心技能栈。掌握这些之后，你已经能够独立完成从环境搭建到高质量出图的完整流程。

怕浪猫想说的是，参数没有"正确答案"，只有"更适合当前需求的配置"。本章提供的参数表是起点而非终点，随着你使用SD的经验积累，你会形成自己的一套参数直觉。那时候，你就真正从"跟着教程做"进化到了"自己知道该怎么做"。

在实际使用中，怕浪猫总结了一个"三步调参法"，分享给大家。第一步：固定基础参数（DPM++ 2M Karras、30步、CFG 7、512x512），用简单提示词出一张基线图。第二步：只改一个变量（比如换采样器或调步数），出图对比效果。第三步：确定最佳参数组合后，再叠加LoRA、ControlNet等高级功能。

这个方法的核心原则是"控制变量"。很多新手一次性改五六个参数，出图效果不好也不知道哪个参数的问题。一次只改一个参数，虽然慢但能真正理解每个参数的作用。

另外提醒一点：SD的参数效果会因Checkpoint模型不同而不同。同样DPM++ 2M Karras采样器，在Realistic Vision上效果很好，换到Anything上可能就不那么理想。所以参数表是参考值，不是绝对值。换模型后需要重新微调参数。

关于显存优化，如果你只有4GB显存的显卡，不要灰心。使用"--medvram"启动参数可以减少显存占用，使用"--lowvram"可以进一步降低需求。配合xformers加速库，4GB显存也能跑SD 1.5。SDXL则需要至少8GB显存才能流畅运行。

如果你觉得这章内容对你有帮助，请收藏这篇文章。参数速查表和采样器对比表值得反复查阅，在日常出图时直接对照使用。如果你在部署或调参过程中遇到问题，欢迎在评论区留言描述你的情况和报错信息，怕浪猫会尽量帮你排查。

下一章我们将进入ComfyUI的世界。如果说A1111的WebUI是"自动挡"，那么ComfyUI就是"手动挡"——你将亲手连接每一个节点，构建属于自己的出图工作流。从安装配置到节点详解，从基础工作流到高级技巧，第5章会带你全面掌握ComfyUI的节点式创作方式。我们下章见。

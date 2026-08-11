---
sidebar_position: 5
---

# 第五章 ComfyUI 工作流

你是不是也经历过这种崩溃时刻：在 WebUI 里调了一下午参数，好不容易出了一张满意的图，却发现根本不记得怎么复现？或者你想把图生图、LoRA（Low-Rank Adaptation，低秩适配）、ControlNet 串联成一条流水线，却发现 WebUI 的表单界面根本不允许你自由组合？别急，这些都是进阶玩家必经的痛点，而本章要讲的 ComfyUI，正是解药。

我是怕浪猫，一个在 AI 绘图工具链里摸爬滚打过来的技术写手。这一章我会带你从零理解 ComfyUI 的节点式思维，搭建常用工作流，掌握插件扩展机制，最终拥有"造轮子"的能力。学完本章，你不再是一个"点按钮等出图"的用户，而是一个能设计生成流程的工程师。

**本章核心金句：WebUI 教你用工具，ComfyUI 教你造工具。当你能看见数据在节点间流动的那一刻，AI 绘图就不再是黑箱。**

## 5.1 ComfyUI 简介

### 节点式界面 vs. WebUI 表单式界面

如果你用过 Automatic1111 WebUI（以下简称 WebUI），一定对那种表单式操作不陌生：一个大页面里塞满了 txt2img、img2img、LoRA、ControlNet 等选项卡，每个选项卡下面是一堆滑块和输入框。你填好参数，点击 Generate，图像从黑箱里蹦出来。这种方式上手快，但天花板也明显——你无法自由定义"先做什么再做什么"的执行顺序。

ComfyUI 则完全不同。它采用节点式界面（Node-based Interface），把 Stable Diffusion 的每一步拆解为独立的功能块。每个节点有输入端和输出端，你通过连线把数据从一个节点传递到下一个节点，最终构成一条完整的数据流水线。这种设计在 Blender、Unreal Engine、DaVinci Resolve 等专业工具中早已是标配。

来看一个直观的对比。同样是"文生图"这个任务：

WebUI 的操作路径是：选择 txt2img 标签页 -> 填写提示词 -> 选模型 -> 设分辨率 -> 设采样步数 -> 点击生成。所有参数在一个表单里完成，执行顺序由 WebUI 内部硬编码决定，你看到的只是结果。

ComfyUI 的操作路径则是：拖出一个 Load Checkpoint 节点加载大模型 -> 拖出两个 CLIP Text Encode 节点分别编写正向和负向提示词 -> 拖出一个 Empty Latent Image 节点设置分辨率 -> 拖出 KSampler 节点执行采样 -> 拖出 VAE Decode 节点把潜空间数据解码为像素图像 -> 拖出 Save Image 节点保存结果。每个节点的输出连到下一个节点的输入，数据流向一目了然。

这两种方式的本质区别在于"控制粒度"。WebUI 是封装好的黑箱，你调参数但看不到内部流程；ComfyUI 是透明管道，你能看到每一步数据长什么样，甚至可以在任意节点接出一条预览分支来检查中间结果。

**金句：节点不是把简单的事情搞复杂，而是把复杂的事情拆清楚。当每一步都可控，每一次出图都可复现。**

### 为什么进阶用户更爱 ComfyUI

进阶用户偏爱 ComfyUI 有四个核心原因。

第一是工作流的可复现性。ComfyUI 的每个工作流都可以导出为 JSON（JavaScript Object Notation，轻量级数据交换格式）文件，这个文件完整记录了所有节点、连线和参数。你把 JSON 文件分享给别人，对方导入后就能得到一模一样的生成流程。这在团队协作和教程分享场景下极其重要。

第二是资源效率。ComfyUI 的内存管理比 WebUI 更激进，它只加载当前工作流需要的模型，用完即释放。在显存紧张的机器上，ComfyUI 能跑起 WebUI 跑不动的大模型。官方提供了 `--lowvram` 参数进一步降低显存占用，虽然速度会慢一些，但至少能出图。

第三是扩展自由度。WebUI 的扩展以脚本形式存在，功能之间经常冲突，启动时加载所有插件也拖慢速度。ComfyUI 的扩展以节点形式存在，你只需要把节点拖进工作流才会生效，不拖就不占资源。这意味着你可以同时安装几十个插件而不影响启动速度。

第四是 API（Application Programming Interface，应用程序编程接口）原生支持。ComfyUI 启动后默认监听 8188 端口，提供 RESTful API 接口。你可以把工作流导出为 API 格式的 JSON，然后用 Python 脚本调用，实现批量生成、自动化流水线、与外部系统集成等高级功能。这对于做 AIGC（AI Generated Content，人工智能生成内容）业务的团队来说是刚需。

## 5.2 安装与配置

### Windows 免安装版使用

Windows 用户最省心的方式是使用官方提供的便携版（Portable Edition）。前往 ComfyUI 的 GitHub Releases 页面，下载带有 `windows` 字样的压缩包，解压到任意不含中文和空格的路径下即可。

解压后你会看到两个关键启动脚本：`run_nvidia_gpu.bat` 使用 NVIDIA GPU 加速，推荐优先使用；`run_cpu.bat` 使用 CPU 计算，仅用于调试或没有独立显卡的情况。双击对应的 bat 文件，终端会开始加载依赖和模型，首次启动需要几分钟。当终端输出 `To see the GUI go to: http://127.0.0.1:8188` 时，在浏览器打开这个地址就能看到 ComfyUI 的节点编辑界面。

这里有一个常被忽略的细节：便携版自带了一个嵌入式 Python 环境，位于 `python_embeded` 目录。后续安装自定义节点的依赖包时，需要用这个 Python 来执行 pip 命令，而不是系统全局的 Python。正确做法是在 ComfyUI 根目录打开终端，执行 `python_embeded\python.exe -m pip install 包名`。如果你直接用系统的 pip 安装，ComfyUI 根本找不到那些包。

如果你希望 ComfyUI 与已有的 WebUI 共享模型文件，避免重复下载动辄几个 GB 的大模型，可以复制根目录下的 `extra_model_paths.yaml.example` 文件并重命名为 `extra_model_paths.yaml`，编辑其中的路径指向你的 WebUI 模型目录。ComfyUI 启动时会自动读取这个配置文件，把 WebUI 的模型目录挂载进来。配置文件的 YAML 格式有严格的缩进要求，两个空格为一层缩进，不要用 Tab 键。以下是一个示例配置：

```yaml
# extra_model_paths.yaml
a111:
    base_path: D:/AI/stable-diffusion-webui/
    checkpoints: models/Stable-diffusion/
    loras: models/Lora/
    vae: models/VAE/
    embeddings: embeddings/
    controlnet: models/ControlNet/
```

配置完成后重启 ComfyUI，你会在节点中的模型列表里看到 WebUI 目录下的模型。注意路径分隔符在 Windows 上使用正斜杠 `/` 而不是反斜杠 `\`，这是 YAML 语法的要求。

### macOS 安装（Homebrew）

除了官方便携版，国内用户也可以考虑使用秋叶启动器（ComfyUI-aki 版本）。秋叶版是一键安装包，内置了常用插件和模型管理工具，适合不想折腾环境配置的用户。下载后解压到任意路径，双击启动器即可使用，省去了手动安装 Python 环境和依赖的步骤。不过秋叶版的更新速度通常落后于官方版本，如果你追求最新功能，官方便携版仍然是首选。

macOS 的安装比 Windows 多几步，但也不复杂。Apple Silicon（M1/M2/M3/M4）芯片使用 MPS（Metal Performance Shaders，金属性能着色器）加速，虽然不如 NVIDIA CUDA（Compute Unified Device Architecture，统一计算设备架构）快，但对于学习和轻量使用完全够用。

第一步是安装 Homebrew，macOS 上的包管理器。打开终端执行：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装完成后，根据终端提示将 Homebrew 添加到 PATH。然后安装必要的依赖工具：

```bash
brew install cmake protobuf rust python@3.10 git wget
```

第二步是克隆 ComfyUI 仓库并创建虚拟环境：

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
python3.10 -m venv venv
source venv/bin/activate
```

第三步是安装 PyTorch。Apple Silicon 需要安装支持 MPS 的 nightly 版本：

```bash
pip install --pre torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/nightly/cpu
```

第四步安装 ComfyUI 核心依赖：

```bash
pip install -r requirements.txt
```

最后启动服务：

```bash
python main.py --force-fp16
```

终端输出访问地址后，浏览器打开 `http://127.0.0.1:8188` 即可。建议把启动命令保存为一个 shell 脚本，下次直接运行即可。

### 中文语言包安装

ComfyUI 默认界面是英文的，对中文用户有一定门槛。社区提供了中文语言包插件，安装方式很简单。

在 ComfyUI 界面中，点击右侧面板的 Manager 按钮（需要先安装 ComfyUI-Manager 插件），在搜索框中输入 "Chinese" 或 "中文"，找到对应语言包插件后点击 Install。安装完成后重启 ComfyUI，在设置菜单中切换语言为中文即可。

如果你还没有安装 ComfyUI-Manager，强烈建议作为第一个插件安装。它相当于 ComfyUI 的应用商店，可以直接搜索、安装、更新所有自定义节点，省去了手动 git clone 的麻烦。安装方法是在 ComfyUI 的 `custom_nodes` 目录下执行：

```bash
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
```

然后重启 ComfyUI，右侧面板就会多出一个 Manager 按钮。

### 模型放置路径

ComfyUI 的模型文件按类型存放在 `models` 目录下的不同子文件夹中，路径必须正确，否则节点中无法选择到对应模型。

以下是最常用的模型路径速查表：

| 模型类型 | 存放路径 | 常见文件格式 |
|---------|---------|-------------|
| 大模型（Checkpoint） | models/checkpoints/ | .ckpt, .safetensors |
| LoRA 模型 | models/loras/ | .safetensors |
| VAE 模型 | models/vae/ | .ckpt, .safetensors |
| ControlNet 模型 | models/controlnet/ | .pth, .safetensors |
| Embedding 模型 | models/embeddings/ | .pt, .safetensors |
| 放大模型 | models/upscale_models/ | .pth, .safetensors |
| CLIP Vision 模型 | models/clip_vision/ | .bin, .safetensors |
| IP-Adapter 模型 | models/ipadapter/ | .bin, .safetensors |

一个常见的新手错误是：下载了模型文件却放错了子文件夹，导致在节点里怎么也找不到模型。如果你遇到了"模型列表为空"的问题，第一步就是检查文件是否在正确的路径下，第二步是确认文件扩展名是否被操作系统隐藏了。

## 5.3 工作流搭建

### 基础文生图工作流

文生图是所有工作流的起点。怕浪猫记得第一次搭建这个工作流时，连了半天的线才跑通，但理解原理后就一通百通了。这一节我会详细讲解每个节点的作用和数据流向。

基础文生图工作流的数据流向如下：

```
Load Checkpoint ──┬──> CLIP Text Encode (正向) ──┐
                  ├──> CLIP Text Encode (负向) ──┤
                  └──> Model ──────────────────────┤
                                                    ├──> KSampler ──> VAE Decode ──> Save Image
                  Empty Latent Image ──────────────┘
```

Load Checkpoint 节点加载大模型后，会输出三个数据流：MODEL（去噪模型）、CLIP（文本编码器）和 VAE（Variational Autoencoder，变分自编码器，负责潜空间和像素空间之间的转换）。

CLIP 输出分别连到两个 CLIP Text Encode 节点。一个编写正向提示词描述你想要的画面，另一个编写负向提示词排除你不想要的元素。两个节点各自输出 CONDITIONING（条件信号）。

Empty Latent Image 节点生成一个空白的潜空间张量，参数 width 和 height 设定图像分辨率，batch_size 设定一次生成几张。这个张量就是 KSampler 的画布。

KSampler（K 采样器）是整个工作流的核心引擎。它接收四个输入：MODEL 提供去噪能力，positive 和 negative 提供条件引导，latent_image 提供起始画布。关键参数包括：seed 控制随机种子，steps 控制去噪步数，cfg 控制提示词引导强度，sampler_name 选择采样算法，scheduler 选择步长调度策略，denoise 控制去噪幅度（文生图设为 1.0 表示从纯噪声开始）。

采样器选择对最终画质和生成速度影响巨大。常用的采样器组合如下：Euler ancestral（带各向异性噪声的欧拉法）速度快且风格大胆，适合快速试验；DPM++ 2M Karras 是公认的通用最优解，质量稳定且步骤少，20 步就能出好图；DDIM 是经典选择，变化幅度小但可控性强。调度器方面，Karras 调度在步数较少时表现最佳，Normal 调度适合步数较多时使用。一个实用的经验法则是：先用 Euler ancestral 加 15 步快速试构图，满意后再切换 DPM++ 2M Karras 加 25 到 30 步出最终图。

KSampler 输出的 LATENT 是潜空间数据，需要经过 VAE Decode 节点解码为像素空间的 IMAGE 数据，最终连到 Save Image 节点保存文件。

以下是这个工作流导出的 API 格式 JSON 结构（精简版），帮助你理解节点之间的连接关系：

```json
{
  "3": {
    "inputs": {
      "seed": 156680208700286,
      "steps": 20,
      "cfg": 8.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    },
    "class_type": "KSampler"
  },
  "4": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "5": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "6": {
    "inputs": {
      "text": "a beautiful landscape painting of mountains at sunset",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "text": "blurry, low quality, distorted",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "8": {
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["8", 0]
    },
    "class_type": "SaveImage"
  }
}
```

读懂这个 JSON 的关键在于理解连接语法。每个节点的输入参数中，如果值是一个数组如 `["4", 0]`，意思是"连接到 ID 为 4 的节点的第 0 个输出"。比如 KSampler（ID 为 3）的 model 输入连到了 CheckpointLoaderSimple（ID 为 4）的第 0 个输出，也就是 MODEL 端口。这种以节点 ID 为键、以连接数组为值的结构，就是 ComfyUI 工作流的底层数据表示。

### 图生图工作流

在实际操作中还有一个重要概念需要理解：节点的类型系统。ComfyUI 通过颜色区分不同的数据类型，连线时只有同类型端口才能连接。MODEL 端口是紫色，CLIP 是黄色，CONDITIONING 是绿色，LATENT 是粉色，IMAGE 是蓝色，VAE 是浅蓝色。这种颜色系统不是装饰，而是强制的类型约束——你无法把一个 CLIP 输出连到 KSampler 的 model 输入端口，就像你无法把字符串传给一个只接受整数的函数一样。理解了类型系统，你就能在不依赖记忆的情况下凭直觉判断哪些节点可以连接，这大大降低了学习成本。

图生图工作流在文生图基础上做了两处关键改动。

第一处是把 Empty Latent Image 节点替换为 Load Image 和 VAE Encode 的组合。Load Image 节点读取一张已有图片，输出 IMAGE 数据；VAE Encode 节点把像素空间的图片编码为潜空间的 LATENT 数据。这样 KSampler 就有了一个起始图像而不是空白噪声。

第二处是调整 KSampler 的 denoise 参数。文生图中 denoise 设为 1.0，表示从纯噪声开始生成，原图信息完全不被保留。图生图中 denoise 通常设为 0.3 到 0.7 之间：值越低，生成结果越接近原图；值越高，改动越大。denoise = 0.5 意味着保留一半原始信息，注入一半新内容。

图生图的数据流向如下：

```
Load Image ──> VAE Encode ──┐
                             ├──> KSampler ──> VAE Decode ──> Save Image
Load Checkpoint ─────────────┤
  ├──> CLIP Text Encode ────┤
  │     (正向提示词)          │
  ├──> CLIP Text Encode ────┤
  │     (负向提示词)          │
  └──> Model ───────────────┘
```

图生图的典型应用场景包括：风格转换（把照片转为二次元画风）、图像修改（改变人物服装颜色）、质量提升（修复模糊老照片）。denoise 值的选择是图生图的核心技巧，需要根据具体需求反复调试。

### LoRA 加载节点

LoRA 是一种轻量化的模型微调技术，它在不修改基础大模型的前提下，通过低秩矩阵注入额外能力。在实际使用中，LoRA 让你可以在一个通用大模型上叠加不同风格——今天用动漫 LoRA，明天用写实 LoRA，切换成本只是加载一个几十 MB 的小文件。

在 ComfyUI 中使用 LoRA 需要加载 Load LoRA 节点。这个节点有三个输入端：model（来自 Load Checkpoint 的 MODEL 输出）和 clip（来自 Load Checkpoint 的 CLIP 输出）。它有两个输出端：修改后的 MODEL 和修改后的 CLIP。换句话说，LoRA 节点是一个"中间人"，它拦截大模型的输出并注入 LoRA 权重，然后传递给下游节点。

工作流连线方式如下：

```
Load Checkpoint ──> Load LoRA ──> CLIP Text Encode (正向)
                  ├──> CLIP Text Encode (负向)
                  └──> KSampler (model 输入)
```

Load LoRA 节点有两个关键参数：strength_model 和 strength_clip，分别控制 LoRA 对模型和 CLIP 的影响强度，默认都是 1.0。如果你觉得 LoRA 效果太强导致画面崩坏，可以把值降到 0.6 到 0.8。如果效果不明显，可以升到 1.2 甚至 1.5，但超过 1.5 通常会出现伪影。

你可以串联多个 Load LoRA 节点来叠加不同风格。比如第一个加载"赛博朋克"LoRA，第二个加载"水彩画"LoRA，两者的权重叠加会产生赛博朋克水彩的混合风格。这种"乐高式"的组合自由度是 ComfyUI 相比 WebUI 的巨大优势——在 WebUI 里同时启用多个 LoRA 只能在提示词中用 `<lora:名字:权重>` 语法，控制粒度远不如节点化操作。

**金句：LoRA 是给大模型穿衣服，ComfyUI 让你在镜子前同时试穿十件，随时调整每件的厚度。**

### 放大工作流

生成的图片分辨率不够高时，需要通过放大工作流来提升清晰度。放大有两种思路：模型放大和重采样放大，实际使用中常常组合两者。

模型放大使用 Upscale Image (using Model) 节点，加载一个训练好的放大模型（如 4x-UltraSharp、RealESRGAN_x4plus），通过模型推理直接把图片放大到指定倍数。这种方式速度快，但不会增加新细节，只是把已有信息插值放大。

重采样放大则是在放大后再次调用 KSampler 进行去噪，让模型在更高分辨率上重新生成细节。具体做法是先用 Latent Upscale 节点在潜空间放大，或先用 VAE Encode 把放大后的图片编码回潜空间，然后接一个 KSampler，denoise 设为 0.2 到 0.4 之间——这个值足够低以保留原图结构，又足够高以添加新细节。

一个完整的渐进式放大工作流数据流向如下：

```
[第一阶段：512x512 文生图]
Load Checkpoint ──> CLIP Text Encode ──> KSampler(1) ──> VAE Decode ──> Save Image(预览)
                                         │
                                         └──> LATENT(512x512)

[第二阶段：放大到 1024x1024]
LATENT(512x512) ──> Latent Upscale(2x) ──> KSampler(2) ──> VAE Decode ──> Save Image(最终)
                                         (denoise=0.3)
```

KSampler(1) 在 512x512 分辨率下快速生成草图，Latent Upscale 把潜空间张量放大到 1024x1024，KSampler(2) 以低 denoise 值在更高分辨率上细化细节。这种渐进式策略比直接生成 1024x1024 更快、更稳定，也更能避免大分辨率下的构图崩坏。

如果追求极致画质，还可以使用 Ultimate SD Upscale 插件。它把大图分割成多个区块（Tile），逐块放大并做边缘融合，从而突破显存限制实现 4K 甚至 8K 放大。该插件支持两种模式：Upscale 模式同时放大并修复细节，需要连接放大模型；No Upscale 模式仅修复细节不改变分辨率。

## 5.4 插件与扩展

### ControlNet 节点

ControlNet 是 Stanford 大学提出的一种条件控制网络，它允许你用线稿、深度图、姿态骨架等结构化信息来约束图像生成过程。如果说提示词是"告诉模型想要什么"，ControlNet 就是"给模型画一张施工图"。

在 ComfyUI 中使用 ControlNet 需要三个节点协同工作：Apply ControlNet（应用 ControlNet，负责把控制条件和模型融合）、Load ControlNet Model（加载 ControlNet 模型权重）、Load ControlNet Preprocessor（加载预处理器，负责从输入图片提取结构化信息）。

数据流向如下：

```
Load Image ──> ControlNet Preprocessor ──> Apply ControlNet
                                              (接收 model + 控制图)
                                                    │
                                                    ├──> CONDITIONING ──> KSampler
Load ControlNet Model ──────────────────────────────┘
CLIP Text Encode ────────────────────────────────────┘
```

预处理器是 ControlNet 工作流的关键环节。以 Canny 边缘检测为例：Load Image 读取一张照片，Canny 预处理器提取照片的边缘轮廓生成一张线稿图，这张线稿图连同 ControlNet 模型一起输入到 Apply ControlNet 节点，生成一个附加了结构约束的 CONDITIONING 信号。这个信号替代原始的 CLIP Text Encode 输出连到 KSampler 的 positive 端口，采样器在去噪过程中就会遵循这张线稿的构图来生成图像。

常用的预处理器包括：Canny（边缘检测，适合控制轮廓）、OpenPose（人体姿态检测，适合控制人物动作）、Depth（深度估计，适合控制空间层次）、Line Art（线稿提取，适合二次元上色）、Segmentation（语义分割，适合控制区域色块）。每种预处理器都有对应的 ControlNet 模型，不能混用。

Apply ControlNet 节点有一个 strength 参数控制控制强度。值为 1.0 时完全遵循控制图，值为 0.0 时等同于不使用 ControlNet。实际使用中 0.5 到 0.8 是常见范围，太低控制效果不明显，太高会导致画面僵硬。

### IP-Adapter 节点

IP-Adapter（Image Prompt Adapter，图像提示适配器）是腾讯 AI Lab 发布的一种图像引导技术。它的核心思想是：用一张图片代替文字作为提示词，让模型"看着图"来生成新图。你可以把它理解为一个单图 LoRA——不需要训练，丢一张参考图进去就能迁移风格。

IP-Adapter 的工作原理涉及三个组件的协作。首先是 CLIP Vision 编码器，它把输入图片编码为视觉特征向量。然后是 IP-Adapter 模型本身，它把视觉特征向量与文本特征空间对齐，生成一种"图像条件信号"。最后是 KSampler，它同时接收文本条件信号和图像条件信号，在去噪过程中综合考虑两种引导。

ComfyUI 中使用 IP-Adapter 需要安装 ComfyUI_IPAdapter_plus 插件。安装后你会获得一组 IP-Adapter 节点，核心节点是 Apply IPAdapter（应用 IP-Adapter）。它的输入包括：model（来自大模型）、ipadapter（IP-Adapter 模型）、image（参考图）、clip_vision（CLIP Vision 编码器模型）。

工作流连线方式：

```
Load Checkpoint ──┬──> Apply IPAdapter ──> KSampler ──> VAE Decode ──> Save Image
                  │         ↑
Load Image ───────┤         │
                  │    Load IPAdapter Model
                  │    Load CLIP Vision
                  ├──> CLIP Text Encode (正向)
                  └──> CLIP Text Encode (负向)
```

IP-Adapter 模型按基础模型区分：文件名带 sd15 的适用于 SD 1.5 大模型，带 sdxl 的适用于 SDXL 大模型。CLIP Vision 模型也有区分：ViT-H 用于 SD 1.5，ViT-G 用于 SDXL。模型搭配错误会导致生成结果异常，这是新手最容易踩的坑之一。

IP-Adapter 的 weight 参数控制参考图的影响权重。值为 0.5 时参考图起微弱引导，值为 1.0 时参考图强烈影响生成结果。高级用法包括：使用 image_negative 输入一张"不想要"的参考图来排除某些特征，使用 attn_mask 输入蒙版让 IP-Adapter 只作用于图像的特定区域。

IP-Adapter 的典型应用场景：风格迁移（输入一张水彩画，生成的图自带水彩风格）、角色一致性（输入一张人脸，生成同一角色的不同场景）、换脸（配合 FaceID 模型实现高保真换脸）。

### Gemini Flash 图像编辑节点

随着多模态大模型的发展，ComfyUI 的扩展已经不限于 Stable Diffusion 生态。社区开发者将 Google 的 Gemini Flash 模型集成为 ComfyUI 节点，允许你在工作流中调用 Gemini 的图像理解和编辑能力。

Gemini Flash 图像编辑节点的定位与 ControlNet、IP-Adapter 不同。ControlNet 和 IP-Adapter 是在扩散模型的采样过程中注入条件信号，本质上是"引导"模型生成。Gemini Flash 节点则是把图像发送给 Gemini API 进行理解或编辑，再把结果传回工作流，属于"调用外部模型"的模式。

这种模式的优势在于可以利用 Gemini 强大的多模态理解能力来实现一些 Stable Diffusion 难以完成的任务。例如：根据一张照片生成精确的画面描述文字、按照自然语言指令编辑图片中的特定元素、对图片进行问答式分析等。

使用这类节点通常需要配置 API Key。在节点中填入你的 Google AI API Key，输入图像和指令文本，节点会通过 HTTP 请求调用 Gemini API，返回结果图像或文本。需要注意的是，这种模式依赖网络连接且按次计费，与纯本地运行的 Stable Diffusion 节点在成本结构上有本质区别。

在实际工作流中，Gemini Flash 节点常作为前处理或后处理环节。前处理场景：用 Gemini 分析参考图生成详细描述，再把描述作为提示词输入到 KSampler 中生成新图。后处理场景：用 Gemini 对生成图片进行语义层面的修改，如"把背景换成森林"或"给人物加上眼镜"。

值得一提的是，ComfyUI 的插件生态正在以前所未有的速度扩展。除了上述三大插件方向，还有许多值得关注的扩展节点：AnimateDiff 用于在 ComfyUI 中生成短视频和 GIF 动画；InstantID 用于高保真身份保持的人像生成，只需要一张参考人脸就能生成保持面部特征的新图像；LayerStyle 提供图层混合、蒙版遮罩等传统图像编辑功能，让 ComfyUI 具备了一定的图像后处理能力。这些插件的安装方式统一：通过 ComfyUI-Manager 搜索名称安装，或在 custom_nodes 目录下 git clone 对应仓库后重启服务。

### 自定义节点开发入门

当现有插件不能满足需求时，你可以开发自己的自定义节点。ComfyUI 的节点开发门槛很低，只需要一个 Python 类和一个注册字典。

以下是一个完整的自定义节点示例，实现一个简单的提示词选择器节点：

```python
# custom_nodes/PromptSelector/nodes.py

class PromptSelectorNode:
    """提示词选择器节点，从预设列表中选择提示词"""

    def __init__(self):
        self.predefined_prompts = {
            "portrait": "a beautiful portrait photo, studio lighting, 85mm lens",
            "landscape": "stunning landscape, golden hour, ultra detailed",
            "anime": "anime style illustration, vibrant colors, detailed eyes"
        }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_type": (["portrait", "landscape", "anime"], {
                    "default": "portrait"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_prompt"
    CATEGORY = "custom/prompt"

    def get_prompt(self, prompt_type):
        return (self.predefined_prompts.get(prompt_type, ""),)


# 注册节点
NODE_CLASS_MAPPINGS = {
    "PromptSelector": PromptSelectorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSelector": "提示词选择器"
}
```

同时需要一个 `__init__.py` 文件让 ComfyUI 识别这个插件：

```python
# custom_nodes/PromptSelector/__init__.py
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

理解这段代码的关键在于几个约定：`INPUT_TYPES` 类方法定义节点的输入参数和 UI 控件类型，`RETURN_TYPES` 定义输出类型，`FUNCTION` 指定执行方法名，`CATEGORY` 定义节点在右键菜单中的分类路径。`NODE_CLASS_MAPPINGS` 字典把节点类名映射到 Python 类，ComfyUI 启动时会扫描 `custom_nodes` 目录下所有包含这个字典的 Python 文件并自动加载。

## 5.5 参考资源

学习 ComfyUI 最好的方式是"边看边做"。以下是怕浪猫精选的参考资源，涵盖了从入门到进阶的全链路。

**ComfyUI GitHub 官方仓库**
地址：https://github.com/comfyanonymous/ComfyUI
这是 ComfyUI 的源代码仓库，包含安装指南、更新日志、内置节点文档和示例工作流。遇到问题首先去 Issues 页面搜索，很多坑前人已经踩过。

**ComfyUI 安装与使用教程**
地址：https://www.sohu.com/a/832571325_121798711
这篇教程详细介绍了 Windows 和 macOS 两个平台的安装步骤，包含模型下载路径和常见问题排查。适合第一次接触 ComfyUI 的读者作为入门参考。

**ComfyUI 本地部署 SD 3**
地址：https://www.sohu.com/a/785952969_100037970
Stable Diffusion 3 是 Stability AI 的新一代模型，在文本理解和图像质量上有显著提升。这篇教程讲解如何在 ComfyUI 中本地部署 SD 3，包括模型下载、环境配置和工作流调整。

**函数计算部署 ComfyUI**
地址：https://news.qq.com/rain/a/20241202A01FMB00
如果你没有高性能本地显卡，可以考虑在云端部署 ComfyUI。这篇文章介绍了如何使用阿里云函数计算服务来运行 ComfyUI，按需付费，不用时不产生费用。

**ComfyUI-aki 版本介绍**
地址：https://www.sohu.com/a/858232281_121293452
ComfyUI-aki 是社区维护的一键安装版，内置了常用插件和模型管理工具。对于不想折腾环境配置的用户来说是最省心的选择。这篇文章介绍了 aki 版本的功能特点和使用方法。

**节点配置速查表**

| 节点名称 | 核心输入 | 核心输出 | 关键参数 |
|---------|---------|---------|---------|
| Load Checkpoint | ckpt_name | MODEL, CLIP, VAE | 无 |
| CLIP Text Encode | text, clip | CONDITIONING | text（提示词内容） |
| Empty Latent Image | width, height, batch_size | LATENT | 分辨率、批次大小 |
| KSampler | model, positive, negative, latent_image | LATENT | seed, steps, cfg, sampler_name, denoise |
| VAE Decode | samples, vae | IMAGE | 无 |
| Load LoRA | model, clip, lora_name | MODEL, CLIP | strength_model, strength_clip |
| Apply ControlNet | conditioning, control_net, image | CONDITIONING | strength |
| Apply IPAdapter | model, ipadapter, image | MODEL | weight |
| Latent Upscale | samples | LATENT | upscale_method, width, height |

**工作流 JSON 模板使用方法**

ComfyUI 的工作流 JSON 文件有两种格式：UI 格式和 API 格式。UI 格式包含节点的画布坐标和视觉布局信息，用于界面导入导出。API 格式只保留节点逻辑和连接关系，用于编程调用。

导入工作流的方法：把 JSON 文件直接拖到 ComfyUI 界面上，或者点击界面左上角的 Load 按钮选择文件。如果导入后出现红色节点，说明缺少对应的自定义节点插件，根据节点名称在 Manager 中搜索安装即可。

导出工作流的方法：点击界面顶部菜单的 Workflow -> Save 保存为 UI 格式，或选择 Export(API) 保存为 API 格式。建议两种格式都保存：UI 格式用于继续编辑，API 格式用于程序调用。

当你掌握了工作流的 JSON 结构后，就可以用 Python 脚本批量调用 ComfyUI 生成图像。以下是一个调用本地 API 的最小示例：

```python
import json
import urllib.request
import websocket
import uuid

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def queue_prompt(workflow_json):
    payload = {"prompt": workflow_json, "client_id": client_id}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"http://{server_address}/prompt", data=data
    )
    return json.loads(urllib.request.urlopen(req).read())

# 加载 API 格式的工作流 JSON
with open("workflow_api.json", "r") as f:
    workflow = json.load(f)

# 修改提示词
workflow["6"]["inputs"]["text"] = "a cat sitting on a windowsill"

# 提交生成任务
result = queue_prompt(workflow)
prompt_id = result["prompt_id"]
print(f"任务已提交，ID: {prompt_id}")
```

这段代码的核心逻辑是：读取工作流 JSON 文件，通过修改节点 ID 对应的 inputs 字段来动态调整参数（如更换提示词），然后把整个 JSON 作为 payload 发送到 /prompt 接口。ComfyUI 收到请求后会将工作流加入执行队列，返回 prompt_id 供你追踪进度。结合 WebSocket 监听可以实时获取生成进度和结果图像。

## 本章总结

这一章我们从 ComfyUI 的设计哲学出发，理解了节点式界面相比表单式界面的核心优势在于控制粒度和可复现性。然后走完了安装配置的全流程，包括 Windows 便携版、macOS Homebrew 安装、中文语言包和模型路径配置。

在工作流搭建部分，我们拆解了四种核心工作流的数据流向：文生图是所有工作流的基础骨架，图生图通过 denoise 参数控制改动幅度，LoRA 加载实现轻量风格切换，放大工作流通过渐进式采样实现高分辨率生成。

插件部分覆盖了三大扩展方向：ControlNet 用结构化信息约束生成过程，IP-Adapter 用参考图替代文字提示，Gemini Flash 节点引入外部多模态能力。最后我们还触及了自定义节点开发的基本模式，为你打开了"造轮子"的大门。

**金句：ComfyUI 的本质不是工具，而是语言。每个节点是一个动词，每条连线是一个句子，每张工作流是一篇关于"图像如何被创造"的论文。**

## 下章预告

第五章到这里就结束了，但 ComfyUI 的进阶之旅才刚刚开始。第六章我们将深入 ControlNet 的世界，学习如何用一张线稿精准控制构图、用姿态骨架指定人物动作、用深度图定义空间层次。如果你觉得本章的 ControlNet 内容只是浅尝辄止，那下一章就是为你准备的完整大餐。点击追更，我们下章见。
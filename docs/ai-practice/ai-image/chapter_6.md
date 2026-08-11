---
sidebar_position: 6
---

# 第六章 ControlNet 精准控制

> 你以为AI画图只能靠提示词"盲盒式"抽奖？ControlNet的出现，直接把"抽卡游戏"变成了"精密遥控"。

如果你还在为AI画图手部崩坏、构图失控、姿势诡异而抓狂，那这一章可能是你整个AI绘画学习中最重要的一课。我是怕浪猫，一个在AI绘画坑里摸爬滚打许久的技术写手。今天这章，我怕浪猫要带你彻底搞懂ControlNet——这个让AI从"随机创作者"变成"精准执行者"的核武器。

## 6.1 ControlNet概述

### 什么是ControlNet？为什么需要它

在ControlNet出现之前，Stable Diffusion的生成过程更像是一个"黑盒抽奖"。你输入一段文字提示词，模型根据文本理解去生成图像，但你几乎无法控制画面的具体构图、人物的姿态、物体的位置。提示词写得好，可能抽到一张满意的图；写得不够精确，十张里有九张是废片。

ControlNet的核心思路非常直接：既然文本提示词的控制度不够，那就给模型额外加一个"条件输入"。这个条件可以是一张边缘检测图、一张深度图、一个人体骨架图，甚至是一张涂鸦。模型在生成时，不仅要参考文本提示词，还要严格遵守你提供的条件图来约束画面结构。

这听起来简单，但技术实现上有一个核心难题：如何在不破坏原始Stable Diffusion模型已学好知识的前提下，让它接受新的条件输入？直接微调模型会导致"灾难性遗忘"（Catastrophic Forgetting），即模型学了新东西就忘了旧知识。ControlNet用一种精巧的结构设计解决了这个问题，这就是接下来要讲的"零卷积"机制。

### ControlNet的工作原理：零卷积（Zero Convolution）结构

ControlNet的工作原理可以用一句话概括：克隆原始模型的一部分网络，用零卷积连接，让新增的条件分支从零开始学习，不干扰原始模型的既有知识。

具体来说，ControlNet取Stable Diffusion中U-Net的编码器部分（包括中间层），复制一份作为"可训练副本"（trainable copy）。原始U-Net的参数被冻结，不参与训练；只有这个副本的参数会更新。关键在于，副本和原始网络之间的连接，用的是一种特殊设计的"零卷积"层。

零卷积的含义是：这个卷积层的权重和偏置都被初始化为零。在训练开始时，零卷积的输出恒为零，这意味着条件分支对原始模型的输出没有任何影响，模型行为和加ControlNet之前完全一致。随着训练推进，零卷积的权重逐渐从零开始变化，条件信号才开始缓慢注入主网络。

这个设计的精妙之处在于它保证了训练的稳定性。如果用随机初始化的卷积层连接，训练初期就会向主网络注入随机噪声，破坏已有知识。零初始化让条件控制信号"渐进式"地融入生成过程，就像给一个熟练的画师递上一把新工具，而不是把他推倒重来。

从数据流的角度看，ControlNet的完整前向传播路径是这样的：输入图像先经过预处理器（如Canny检测器）生成条件图，条件图经过一个小的卷积网络编码后送入可训练副本。可训练副本同时接收原始U-Net的中间特征作为输入，经过自身计算后，通过零卷积将特征加回到原始U-Net的解码器路径中。最终，U-Net的输出既包含了文本提示词的语义引导，也融合了条件图的结构约束。

下面是ControlNet模型加载的核心代码示例，展示了如何在Stable Diffusion管道中注入ControlNet：

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch
from PIL import Image

# 加载ControlNet模型，以Canny边缘检测为例
controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny",
    torch_dtype=torch.float16
)

# 加载Stable Diffusion管道，将ControlNet作为参数传入
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16
)

# 优化推理速度
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()

# 生成图像
prompt = "a beautiful girl standing in a garden, high quality, detailed"
negative_prompt = "low quality, blurry, deformed"
image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=control_image,  # 这就是条件图，如Canny边缘图
    num_inference_steps=30,
    guidance_scale=7.5
).images[0]
```

而预处理器（以Canny为例）的调用方式如下：

```python
import cv2
import numpy as np
from PIL import Image

# Canny边缘检测预处理器
def preprocess_canny(image_path, low_threshold=100, high_threshold=200):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # 转灰度图进行边缘检测
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, low_threshold, high_threshold)
    # 转为三通道图像（模型输入需要RGB）
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(edges)

control_image = preprocess_canny("input.jpg")
```

> **怕浪猫金句：提示词是"告诉AI画什么"，ControlNet是"告诉AI怎么画"。前者是甲方提需求，后者是甲方亲自上手画草图。**

## 6.2 安装与配置

### WebUI插件安装

在Automatic1111 WebUI中安装ControlNet非常直接。打开WebUI界面后，进入Extensions（扩展）标签页，选择Install from URL（从URL安装），输入ControlNet的官方仓库地址。点击Install后等待安装完成，然后重启WebUI即可。

```
# ControlNet扩展仓库地址
https://github.com/Mikubill/sd-webui-controlnet
```

安装完成后，你会在txt2img和img2img页面底部看到一个新的"ControlNet"折叠面板。展开后可以看到多个ControlNet Unit（控制单元）的设置区域。每个Unit可以独立配置一个ControlNet模型，这就是多ControlNet叠加的基础。

如果你使用的是ComfyUI，ControlNet通常以自定义节点（Custom Node）的形式存在。通过ComfyUI Manager安装"ComfyUI ControlNet Aux"节点包即可获得完整的ControlNet预处理和推理能力。ComfyUI中的ControlNet工作流更加灵活，你可以将条件图的处理过程可视化地连接到生成管道中。

### 模型下载与放置路径

ControlNet的模型文件需要单独下载，不随Stable Diffusion主模型一起分发。模型文件的放置路径根据你使用的WebUI版本有所不同。

对于Automatic1111 WebUI，模型放置路径为：

```
stable-diffusion-webui/extensions/sd-webui-controlnet/models/
```

对于ComfyUI，路径为：

```
ComfyUI/models/controlnet/
```

ControlNet模型文件通常较大，单个模型约1.4GB（对应SD 1.5）或更大（对应SDXL）。官方模型由Lvmin Zhang等人在Hugging Face上发布，仓库地址为`lllyasviel/ControlNet`和`lllyasviel/ControlNet-v1-1`。你需要根据自己使用的Stable Diffusion版本（SD 1.5还是SDXL）选择对应的ControlNet模型。

下载时需要注意模型命名规范。以SD 1.5为例，常见的命名格式为`control_v11p_sd15_canny.pth`，其中`v11`表示版本1.1，`p`表示pruned（剪枝版，体积更小），`sd15`表示对应SD 1.5，`canny`表示模型类型。

### 预处理器自动下载

ControlNet的工作流程分两步：先用预处理器（Preprocessor）从输入图像中提取结构信息，再将提取结果作为条件送入ControlNet模型。预处理器本质上是各种计算机视觉算法，如Canny边缘检测、OpenPose姿态估计等。

在WebUI中，当你选择某个ControlNet类型时，对应的预处理器会自动选择。首次使用某个预处理器时，WebUI会自动下载所需的依赖文件（如OpenPose的ONNX模型、Depth的MiDaS模型权重等）。这些文件通常下载到`models/`或`extensions/sd-webui-controlnet/annotator/`目录下。

自动下载依赖于网络连接，如果你在国内网络环境下遇到下载失败的情况，可以手动下载预处理器权重文件并放到对应目录。具体文件和路径可以在ControlNet扩展的文档中找到。

```python
# 在代码中使用ControlNet预处理器（以OpenPose为例）
# 需要安装 controlnet_aux 库
# pip install controlnet_aux

from controlnet_aux import OpenposeDetector

# 首次调用会自动下载模型权重
openpose = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
pose_image = openpose(input_image, hand_and_face=True)
```

> **怕浪猫金句：预处理器是ControlNet的"眼睛"，它负责看懂你的参考图；ControlNet模型是"手"，它负责把看到的结构画出来。眼手协调，才能精准作画。**

## 6.3 常用ControlNet模型（14种详解）

ControlNet发展至今，社区已经积累了十几种不同类型的控制模型。每种模型针对不同的结构信息提取方式，适用于不同的创作场景。下面我逐一讲解14种常用ControlNet模型的原理、适用场景和使用要点。

### Canny（边缘检测）

Canny是最经典的边缘检测算法之一，也是ControlNet中使用频率最高的模型之一。它的原理是通过计算图像中像素强度的梯度变化来找到边缘。具体步骤包括：高斯模糊去噪、计算梯度幅值和方向、非极大值抑制（NMS，Non-Maximum Suppression）细化边缘、双阈值检测连接边缘。

Canny生成的条件图是黑白线条图，只有边缘处为白色，其余为黑色。它特别适合控制建筑、家具、机械等硬表面物体的轮廓，也常用于保持生成图像与参考图的构图一致。

使用时有两个关键参数：低阈值和高阈值。阈值越低，检测到的边缘越多越细；阈值越高，只保留主要轮廓。一般推荐低阈值100、高阈值200作为起点。

### Depth（深度图）

深度图模型使用深度估计算法（通常是MiDaS或Depth Anything）将输入图像转换为一张灰度深度图。深度图反映的是场景中物体到摄像机的距离关系：近处的物体更亮，远处的物体更暗（或反过来，取决于算法）。

Depth的核心优势在于它捕获的是三维空间结构而非二维线条。这意味着你可以用一张室内照片的深度图来约束另一张完全不同风格的室内场景生成，只要空间纵深关系一致即可。相比Canny只关注物体边缘，Depth提供了更整体的空间感。

深度估计模型本身是一个在大量RGB-D数据集上训练的神经网络。它接收RGB图像作为输入，输出一张单通道的深度图。ControlNet再以这张深度图作为条件来引导生成。

### OpenPose（人体姿态）

OpenPose是一个实时多人姿态估计系统，由CMU（Carnegie Mellon University，卡内基梅隆大学）团队开发。它能检测图像中人体的关键点（keypoints），包括头部、肩膀、肘部、手腕、髋部、膝盖、脚踝等位置，并用骨架线条连接这些关键点。

OpenPose条件图是一张黑色背景上绘制的彩色骨架图。不同身体部位用不同颜色标注，这样ControlNet模型能区分各部位的身份。除了身体骨架，OpenPose还可以检测手部关键点（每只手21个点）和面部关键点（70个点），实现更精细的姿态控制。

这个模型在角色创作中极为重要。你可以从一张真人照片中提取姿态，然后用这个姿态来生成完全不同角色、不同风格的图像。人物的动作、姿势被精准保留，但外貌、服装、场景可以完全自由发挥。

### MLSD（直线检测）

MLSD（Mobile Line Segment Detection，移动线段检测）是一种专门检测直线段的算法。与Canny检测所有边缘不同，MLSD只关注直线结构，忽略曲线和不规则形状。

这使得MLSD特别适合建筑、室内设计、城市场景等以直线为主的场景控制。当你想生成一个房间或一栋建筑，希望保持透视线和建筑结构的准确性时，MLSD比Canny更合适，因为它不会把家具的弧形轮廓也提取出来干扰你对建筑线条的控制。

MLSD的检测原理基于深度学习的线段检测网络，它将图像中的直线段用端点坐标表示，然后将检测到的线段绘制成条件图。你可以通过调节阈值参数来控制检测的线段密度。

### Lineart（线稿）

Lineart模型专门为线稿风格的条件图设计。它接收的输入是手绘线稿或动漫线稿，直接作为条件引导生成。与Canny和MLSD从照片中提取边缘不同，Lineart的输入本身就是线条图，不需要"提取"步骤。

Lineart预处理器有几种模式：`lineart_coarse`（粗线稿）适合草图风格，`lineart_realistic`（写实线稿）适合精细线稿，`lineart_anime`（动漫线稿）专为动漫风格优化。选择哪种模式取决于你的输入线稿类型和期望的生成风格。

这个模型在漫画创作、插画上色场景中非常实用。你可以画一个简单的线稿，让AI帮你上色并补充细节，而线稿的结构和构图会被严格保留。对于漫画工作室和独立插画师而言，Lineart大幅缩短了从线稿到成稿的工作流程。你只需要专注于线条表现力，把上色和光影渲染交给AI完成。需要注意的是，Lineart对输入线稿的完成度有一定要求——如果线稿过于潦草或结构不完整，生成结果可能出现局部变形。建议先用`lineart_coarse`模式快速测试构图，再切换到`lineart_realistic`模式生成精细成品。

### Soft Edge（软边缘）

Soft Edge（软边缘，也称为HED，Holistically-Nested Edge Detection）是一种全嵌套边缘检测算法。与Canny产生硬朗的二值化边缘不同，Soft Edge产生的是带有渐变过渡的边缘图，边缘有粗有细、有深有浅，更接近人类画师用铅笔勾勒的素描效果。

Soft Edge的优势在于它捕获的边缘信息比Canny更丰富。Canny的边缘只有黑白二值，而Soft Edge保留了边缘强度的渐变信息。这使得生成结果在保持结构的同时，过渡更自然，细节更丰富。但缺点是控制力比Canny稍弱，因为条件信号更"模糊"。

适合用于肖像、自然场景、有机形态等需要柔和过渡的图像控制。如果你觉得Canny太"硬"，Scribble太"乱"，Soft Edge是一个折中选择。

### Scribble（涂鸦）

Scribble（涂鸦）模型接受最粗糙的条件输入——你的随手涂鸦。不需要精确的线条或专业的画技，哪怕是火柴人级别的简笔画，Scribble ControlNet都能理解你的意图并生成完整图像。

Scribble预处理器会对输入涂鸦进行简单的二值化和形态学处理，生成一张粗糙的白色线条条件图。ControlNet模型在训练时见过大量从随机涂鸦到精细图像的映射，因此它能"理解"涂鸦中蕴含的大致构图和元素位置。

这个模型的自由度最高，但控制力最低。它适合创意探索阶段，当你只有一个模糊的想法时，先涂鸦出大致构图让AI帮你具体化。如果你需要精确控制，应该转向Canny或Lineart。Scribble的一个重要使用技巧是配合较高的引导比例（Guidance Scale，通常设为7到12）。较高的引导比例能帮助模型更好地理解涂鸦中隐含的构图意图，减少生成结果与涂鸦之间的偏差。此外，Scribble还可以与Reference或IP-Adapter叠加使用：涂鸦负责定义大致构图，参考图负责注入风格和细节，两者互补能产生意想不到的创意效果。

### Segmentation（语义分割）

Segmentation（语义分割）模型使用图像分割算法将图像中的每个像素分类到预定义的语义类别中。不同类别用不同颜色表示，生成一张彩色"色块图"作为条件输入。例如，APE（Ade20k Pascal Context Encode）预处理器可以将图像分为150个语义类别，天空是蓝色块、草地是绿色块、人物是粉色块等。

语义分割的核心价值在于它控制的是"什么东西放在哪里"，而不是"边缘在哪里"或"姿态是什么样"。你可以自己画一张色块图来定义场景布局：这里放一栋楼，那里放一棵树，中间放一个人。ControlNet会严格按照这个布局来生成图像。

这种控制方式特别适合场景设计和室内布局规划。你可以像玩像素画一样用颜色块定义空间，然后让AI填充真实的视觉细节。与Canny或Depth不同，分割图不包含任何视觉外观信息，只包含语义布局，这给了生成模型最大的风格自由度。

### Tile/Blur（细节处理）

Tile（分块）和Blur（模糊）是两种用于细节增强和重绘的控制模型。Tile模型将图像分成小块处理，允许模型在不改变整体构图的前提下，对每个局部区域进行细节增强。Blur模型则使用模糊后的图像作为条件，让模型在保持大致构图的同时重新生成清晰的细节。

Tile的原理是分块推理后无缝拼接。它解决了一个实际问题：直接对高分辨率图像进行ControlNet处理时，显存消耗巨大且效果不均匀。分块处理让每个区域都能获得模型足够的注意力，细节质量显著提升。

Blur的工作方式更简单：输入图像先做高斯模糊，模型拿到模糊图作为条件，任务是"把模糊图变清晰"。这个模型非常适合低分辨率图像的放大增强，或者给模糊的老照片添加细节。

### Inpaint（局部重绘）

Inpaint（局部重绘）ControlNet专门用于图像的局部修改。你提供一个蒙版（mask），指定需要重绘的区域，ControlNet会在保持非蒙版区域不变的前提下，根据提示词重新生成蒙版区域的内容。

Inpaint ControlNet与Stable Diffusion自带的img2img inpainting相比，控制力更强。它不仅能指定"改哪里"，还能通过条件图约束"怎么改"。例如，你可以在蒙版区域叠加一个Canny条件图，指定重绘内容的边缘结构。

这个模型在图像修复、对象替换、背景替换等场景中非常实用。你也可以用它来做图像扩展（Outpainting），即在原图边缘外侧绘制蒙版，让AI"想象"画面如何延伸。

### Reference（参考模仿）

Reference（参考模仿）是一种特殊的ControlNet类型。它不提取结构信息，而是直接将整张参考图像的特征作为条件注入生成过程。效果类似于"风格迁移"：生成的图像在构图和内容上参考输入图，但允许风格和细节的变化。

Reference的实现方式是将参考图通过一个图像编码器提取特征向量，然后将这些特征作为条件注入U-Net的交叉注意力层。与文本提示词类似，但条件来源从文本变成了图像。

这个模型适合"我想生成一张类似这张图的图"这类需求。例如，你看到一张构图很好的照片，想用不同风格重新演绎，Reference可以帮你保留构图的"感觉"同时改变视觉风格。不过要注意，Reference的"模仿"比较松散，如果你需要严格的构图控制，还是应该用Canny或Depth。

### IP-Adapter（图像提示）

IP-Adapter（Image Prompt Adapter，图像提示适配器）可以理解为"用图片代替文字做提示词"。它将输入图像通过CLIP（Contrastive Language-Image Pre-training，对比语言-图像预训练）视觉编码器编码为特征向量，然后以与文本提示词类似的方式注入到U-Net的交叉注意力层中。

IP-Adapter的独特之处在于它控制的是"风格和内容"而非"结构"。你可以把一张赛博朋克风格的画作为IP-Adapter输入，然后生成一张完全不同构图但同样风格的图像。这与Reference类似，但IP-Adapter的集成方式更优雅，控制力也更强。

IP-Adapter常与结构类ControlNet（如Canny、Depth）叠加使用。Canny负责控制构图，IP-Adapter负责控制风格，两者配合可以实现"用A的构图+B的风格"生成全新图像。这种组合在创意设计中非常强大。

### Recolor（重新上色）

Recolor（重新上色）模型专门用于改变图像的配色方案而不改变其内容。输入是一张颜色参考图（或灰度图），模型根据参考图的颜色分布来重新着色生成图像。

Recolor的工作原理是将输入图像转换为颜色分布特征，作为条件引导生成过程中的色彩选择。与直接做颜色映射的滤镜不同，Recolor理解颜色的语义——天空应该是蓝色系，草地应该是绿色系——因此重新上色的结果更自然合理。

适合黑白照片上色、换季换色（把夏天的绿色换成秋天的橙黄）、品牌配色统一等场景。当你需要保持图像内容不变只改变颜色时，Recolor比Inpaint更高效，因为不需要精确蒙版。

### Instant ID（即时特征）

Instant ID（即时特征）是ControlNet家族中的新成员，专门用于身份保持（Identity Preservation）。它能在生成图像时严格保留输入人脸的身份特征，同时允许你通过文本提示词自由改变人物的年龄、表情、服装、场景等。

Instant ID的原理结合了人脸识别和ControlNet两项技术。它先用一个人脸识别模型（如ArcFace）从输入人脸图像中提取身份特征向量，然后将这个向量通过一个特殊的适配网络注入到U-Net中。同时，它还使用一个轻量级的FaceAdapter来提供面部结构约束。

与早期的FaceID方案相比，Instant ID不需要训练单独的LoRA模型，处理速度更快，且对输入图像质量的要求更低。一张普通的正面照片就能提取足够的身份信息。这让它在个性化头像生成、角色一致性保持等场景中非常实用。Instant ID的使用中有几个要点值得注意：输入照片尽量选择正脸、光线均匀、表情自然的照片，这样提取的身份特征最完整。生成时可以通过调节Identity Strength（身份强度）参数来平衡身份保持与风格自由度——值越高越像原图人脸，值越低生成越自由但可能偏离原始身份。Instant ID还可以与OpenPose叠加使用，在保持人脸身份的同时精确控制头部角度和表情姿态，这是单独使用Instant ID无法实现的效果。

下面是14种ControlNet模型的快速对比表，方便你按需选择：

| 模型 | 控制维度 | 控制力度 | 适用场景 | 推荐组合 |
|------|----------|----------|----------|----------|
| Canny | 边缘轮廓 | 强 | 建筑、构图控制 | IP-Adapter |
| Depth | 深度空间 | 中 | 场景重构、空间保持 | OpenPose |
| OpenPose | 人体姿态 | 强 | 人物动作控制 | Canny |
| MLSD | 直线结构 | 强 | 建筑、室内设计 | Depth |
| Lineart | 线稿结构 | 强 | 上色、插画 | 无需叠加 |
| Soft Edge | 软边缘 | 中 | 肖像、自然场景 | Depth |
| Scribble | 涂鸦草图 | 弱 | 创意探索 | 无需叠加 |
| Segmentation | 语义布局 | 强 | 场景设计 | Depth |
| Tile/Blur | 局部细节 | 中 | 放大增强 | Canny |
| Inpaint | 局部重绘 | 强 | 修复、替换 | Canny |
| Reference | 参考模仿 | 弱 | 风格参考 | OpenPose |
| IP-Adapter | 风格内容 | 中 | 风格迁移 | Canny/Depth |
| Recolor | 配色方案 | 中 | 上色、换色 | Lineart |
| Instant ID | 人脸身份 | 强 | 个性化头像 | OpenPose |

> **怕浪猫金句：14种ControlNet模型就像画师工具箱里的14把刷子，没有哪把是最好的，只有最适合当前画面的那把。选错工具，再熟练也画不出好画。**

## 6.4 多ControlNet叠加使用

### 同时使用多个ControlNet

单一ControlNet只能控制一个维度的结构信息。但实际创作中，你往往需要同时控制多个维度：既要控制人物姿态，又要控制场景边缘，还要控制风格参考。这就是多ControlNet叠加的价值所在。

在WebUI中，你可以展开多个ControlNet Unit，每个Unit独立配置一个ControlNet模型。默认情况下WebUI支持同时启用多个Unit，理论上没有硬性上限，但实际受限于显存大小。一般建议同时使用2到4个ControlNet，超过4个容易导致显存溢出且控制信号互相冲突。

多ControlNet的叠加原理是特征层面的加权融合。每个ControlNet分支独立计算自己的条件特征，然后这些特征被加到U-Net解码器路径的对应位置。由于每个分支的零卷积独立学习，模型能自动学习不同条件之间的优先级和互补关系。

常见的实用组合配方包括：

配方一：人物精准控制
- ControlNet 1: OpenPose（姿态控制，权重1.0）
- ControlNet 2: Canny（边缘控制，权重0.5）
- ControlNet 3: IP-Adapter（风格控制，权重0.7）
- 效果：精准控制人物姿态和画面构图，同时注入风格参考

配方二：建筑/场景设计
- ControlNet 1: MLSD（直线控制，权重1.0）
- ControlNet 2: Depth（深度控制，权重0.8）
- ControlNet 3: Segmentation（语义布局，权重0.6）
- 效果：精确控制建筑线条和空间纵深，同时定义场景元素的语义布局

配方三：肖像一致性
- ControlNet 1: Instant ID（身份保持，权重0.8）
- ControlNet 2: OpenPose（姿态控制，权重0.5）
- ControlNet 3: Reference（风格参考，权重0.4）
- 效果：保持人脸身份的同时控制姿态和风格

配方四：创意上色
- ControlNet 1: Lineart（线稿控制，权重1.0）
- ControlNet 2: Recolor（配色控制，权重0.6）
- 效果：严格保留线稿结构的同时控制配色方案

### 权重平衡与效果调优

多ControlNet叠加时，最关键也是最难的就是权重平衡。每个ControlNet Unit都有一个"Control Weight"（控制权重）参数，范围通常在0到2之间，默认值1.0。权重越高，该条件的控制力越强；权重越低，生成结果越自由。

权重调优没有万能公式，但有一些经验原则可以参考。首先是"主次分明"原则：在多ControlNet组合中，应该明确哪个是主控条件，哪些是辅助条件。主控条件设权重1.0到1.2，辅助条件设0.4到0.7。如果所有条件权重都很高，模型会收到冲突信号，导致画面扭曲或出现伪影。

其次是"先单独后叠加"原则。调参时先逐个启用每个ControlNet，单独看效果是否合理，再逐步叠加。这样能快速定位问题出在哪个ControlNet上。如果叠加后效果异常，先降低辅助条件的权重，看主控条件能否独立工作。

还有一个重要参数是"Starting Step"（起始步）和"Ending Step"（结束步）。ControlNet不一定要在整个生成过程中都生效，你可以设置它只在某一段推理步骤中起作用。例如，设置Starting Step为0.2、Ending Step为0.8，表示ControlNet在生成过程的20%到80%之间生效。前期让模型自由构图，后期让ControlNet收束结构，这种"先放后收"的策略有时能得到更好的效果。

```python
# 多ControlNet叠加的代码示例（使用diffusers库）
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import torch

# 加载多个ControlNet模型
controlnets = [
    ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-openpose", torch_dtype=torch.float16),
    ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-canny", torch_dtype=torch.float16),
]

# 将多个ControlNet传入管道
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnets,  # 接收一个列表
    torch_dtype=torch.float16
)
pipe.enable_model_cpu_offload()

# 生成时传入多个条件图
images = pipe(
    prompt="a girl sitting on a chair in a modern room",
    image=[pose_image, canny_image],  # 按顺序对应每个ControlNet
    num_inference_steps=30,
    guidance_scale=7.5,
    # 每个ControlNet的权重可以通过controlnet_conditioning_scale控制
    controlnet_conditioning_scale=[1.0, 0.5]  # OpenPose权重1.0, Canny权重0.5
).images[0]
```

另一个进阶技巧是使用CFG Scale（Classifier Free Guidance Scale，无分类器引导比例）的配合调节。CFG Scale控制模型对提示词的遵循程度，与ControlNet权重存在交互效应。当ControlNet权重较高时，适当降低CFG Scale可以避免画面过度饱和；当ControlNet权重较低时，提高CFG Scale能增强提示词引导，弥补结构控制的不足。一般建议在叠加2个ControlNet时CFG Scale设为7到9，叠加3到4个时降到6到7.5。

权重调优是一个需要耐心和直觉的过程。怕浪猫建议你从前面给出的推荐配方开始，先跑出基本满意的结果，再根据具体问题微调。如果画面结构不够严格，提高结构类ControlNet（Canny、OpenPose等）的权重。如果画面风格偏离参考，提高风格类ControlNet（IP-Adapter、Reference）的权重。如果画面出现伪影或扭曲，降低整体权重，优先降辅助条件。多ControlNet叠加的魅力在于组合的无限可能——上述配方只是起点，你可以根据自己的创作需求自由组合任何ControlNet类型，在实践中发现属于你的最佳搭配。

> **怕浪猫金句：多ControlNet叠加就像组建一支乐队，每个成员都有自己的声部。权重就是音量旋钮——不是每个人都开到最大就好听，关键在于配比和平衡。**

## 6.5 参考资源

学习ControlNet最好的方式是动手实践，以下是怕浪猫整理的优质学习资源：

- ControlNet安装与基础使用教程（B站视频）：https://www.bilibili.com/video/BV1us4y1v7hN/
- ControlNet插件图文教程（CSDN）：https://blog.csdn.net/Z20140628/article/details/146459705
- ControlNet 9种类型详解（CSDN）：https://blog.csdn.net/canadajasminestudio/article/details/141058770
- ControlNet精准控制原理与实践（掘金）：https://juejin.cn/post/7273674981960237113
- ControlNet高仿参考实战技巧（掘金）：https://juejin.cn/post/7266693534862229539
- ControlNet Inpaint向外扩展应用（头条视频）：https://www.toutiao.com/video/7240021052603059489/

这些资源涵盖了从安装配置到高阶技巧的完整学习路径。建议先看B站的视频教程建立整体认知，再结合CSDN和掘金的图文教程深入特定模型的使用细节，最后通过视频教程学习Inpaint等进阶技巧。

## 本章小结

ControlNet是Stable Diffusion生态中最具变革性的技术之一。它通过零卷积结构实现了对生成过程的精准结构控制，同时不破坏基础模型的知识。14种控制模型覆盖了从边缘、深度、姿态到风格、身份等不同维度的控制需求，多ControlNet叠加更是打开了多维组合控制的创作空间。

掌握ControlNet的关键不在于记住每个模型的参数，而在于理解每种控制方式的"语言"——Canny说的是"边缘"，Depth说的是"空间"，OpenPose说的是"姿态"，Segmentation说的是"布局"。学会把这些语言组合起来"对话"，你就能让AI从盲盒生成器变成精准的画笔。

如果你觉得这章内容对你有帮助，强烈建议收藏本文。14种模型对比表和多ControlNet叠加配方是实战中反复要用到的参考，存下来随时查阅能省去大量试错时间。也欢迎在评论区分享你的ControlNet使用心得和独家配方，怕浪猫会挑有趣的组合实际测试后在下期内容中分享。

下一章我们将进入另一个核心话题：LoRA（Low-Rank Adaptation，低秩适配）模型与微调。如果说ControlNet解决了"怎么画"的问题，那LoRA解决的就是"画什么风格"的问题。LoRA让你用几张图片就能训练出专属风格模型，从动漫风到写实风，从特定角色到独特画师风格，都能轻松实现。我们下章见。

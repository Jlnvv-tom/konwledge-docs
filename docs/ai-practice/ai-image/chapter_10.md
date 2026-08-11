---
sidebar_position: 10
---

# 第十章 图片放大与高清修复

你有没有遇到过这种情况：网上找到一张绝佳的素材图，结果拖进设计软件一看，分辨率只有500x300，放大后糊成一团马赛克，连主体都分不清。或者翻出几年前手机拍的老照片，想在显示器上全屏浏览，却发现满屏都是像素点和锯齿。传统的图片放大工具就像把一块小橡皮硬拉成大橡皮，越拉越薄，细节全丢了。而AI放大技术做的事情完全不同——它不是拉伸像素，而是让AI"重新画"出缺失的细节。

我是怕浪猫，这一章我来带你系统梳理图片放大与高清修复的主流方案。从底层原理到工具选型，从命令行到图形界面，从独立工具到SD内置方案，怕浪猫会一次性帮你把知识框架搭起来。建议先收藏，用到的时候随时翻阅。

## 10.1 图片放大概述

### 10.1.1 传统插值的局限

图片放大的本质是增加像素数量。传统方法主要依赖插值算法，常见的有最近邻插值（Nearest Neighbor Interpolation）、双线性插值（Bilinear Interpolation）和双三次插值（Bicubic Interpolation）。这些算法的核心思路是根据已知像素点的颜色值，通过数学公式推算出新增像素的颜色。

最近邻插值最简单粗暴，直接复制最近的像素颜色，放大后会出现明显的方块和锯齿。双线性插值在两个方向上做线性加权，效果稍好但画面发虚。双三次插值考虑周围16个像素做卷积计算，是Photoshop等软件默认的放大算法，但本质上仍然是在已知像素之间做平滑过渡。

**插值算法的天花板在于：它只能利用图像本身已有的信息，无法创造新的细节。** 一张模糊的脸部图片，用双三次插值放大四倍后，五官的轮廓依然模糊，因为原始信息中就不存在毛孔、睫毛这些微观纹理。这就像把一段低码率的视频拉伸到4K，清晰度不会提升，只是把同样的模糊放大了而已。

### 10.1.2 AI放大原理：超分辨率重建

AI图片放大的技术名称是单图像超分辨率重建（Single Image Super-Resolution，SISR）。与传统插值不同，超分辨率重建不是对现有像素做数学运算，而是让深度学习模型根据大量训练数据中学到的先验知识，预测并生成缺失的高频细节。

简单来说，训练过程是这样的：研究者收集大量高清图片作为目标，将这些图片通过退化处理（模糊、降采样、加噪、JPEG压缩）生成对应的低清图片作为输入。模型的任务就是从低清图片重建出原始的高清图片。通过反复比较重建结果与真实高清图片的差异，模型逐渐学会了"从模糊到清晰"的映射关系。

**AI放大的核心优势在于：它能生成原图中不存在但合理存在的细节。** 比如一张低分辨率的风景照，放大后树叶的纹理、建筑外墙的砖缝、天空中的云层层次，这些在原图中被丢失的信息，AI模型可以根据学到的自然图像统计规律进行补全。这种能力是传统插值永远无法企及的。

目前主流的超分辨率模型大多基于生成对抗网络（Generative Adversarial Network，GAN）架构。GAN由一个生成器和一个判别器组成，生成器负责将低清图片放大为高清图片，判别器负责判断生成的图片是真实的还是AI伪造的。两个网络在训练过程中相互博弈，生成器不断改进以骗过判别器，最终产出的图片在视觉上接近真实高清图像。

### 10.1.3 主流放大工具对比

市面上AI放大工具不少，怕浪猫帮你整理了一张核心对比表，方便快速选型：

| 工具 | 开发方 | 定位 | 放大倍数 | 硬件要求 | 适用场景 |
|------|--------|------|----------|----------|----------|
| Real-ESRGAN | 腾讯ARC | 通用+动漫 | 2x/4x | GPU(CUDA)或CPU | 照片、动漫、视频 |
| Real-CUGAN | B站 | 动漫专用 | 2x/3x/4x | GPU(CUDA) | 动漫图片、视频 |
| Upscayl | 开源社区 | 桌面GUI | 4x/最高16x | Vulkan兼容GPU | 非技术用户、批量处理 |
| waifu2x | 社区 | 动漫专用 | 1x/2x | GPU或CPU | 老牌动漫放大 |
| Topaz Gigapixel | Topaz Labs | 商业软件 | 最高6x | GPU(CUDA) | 专业摄影、印刷 |
| SD Hires. fix | StabilityAI | SD内置 | 自定义 | GPU(CUDA) | AI生图后直接放大 |

选型原则很简单：处理动漫图片首选Real-CUGAN，通用照片用Real-ESRGAN，不想折腾命令行就用Upscayl，在SD里生图后直接放大走Hires. fix。**工具没有绝对的优劣，关键是匹配你的使用场景和硬件条件。**

## 10.2 Real-ESRGAN

Real-ESRGAN是目前应用最广泛的开源AI放大工具之一，由腾讯ARC（Applied Research Center）实验室开发并在ICCVW 2021上发表。它是ESRGAN（Enhanced Super-Resolution Generative Adversarial Network，增强超分辨率生成对抗网络）的改进版本，核心突破在于能够处理真实世界中复杂退化的低清图片，而不仅仅是理想条件下的人工降采样图片。

### 10.2.1 RRDB网络结构

Real-ESRGAN的生成器核心是RRDB（Residual-in-Residual Dense Block，残差中的残差密集块）网络结构。要理解RRDB，需要从三个层次拆解。

最内层是密集连接块（Dense Block）。在一个密集连接块内，每一层的输入都包含之前所有层的输出，通过这种稠密的跳跃连接，特征信息可以在网络中高效流动。假设一个密集块有5层卷积，第5层的输入就是第1到第4层输出的拼接。这种设计让网络在保持参数量适中的前提下，获得了更强的特征表达能力。

中间层是残差密集块（Residual Dense Block，RDB）。每个RDB由多个密集连接块串联组成，并在RDB的输入和输出之间添加了一条残差连接。残差连接的做法是将RDB的输入直接加到其输出上，使得网络学习的是残差映射而非完整映射。**残差连接的引入解决了深层网络中的梯度消失问题，让训练更稳定。**

最外层就是RRDB本身。RRDB将多个RDB组合在一起，再次在外层添加一条残差连接。这就是"残差中的残差"这个名字的由来——RDB内部有残差连接，RRDB外部又有残差连接，形成了嵌套的残差结构。Real-ESRGAN的生成器通常使用23个RRDB模块堆叠，网络深度可达数百层。

除了RRDB，Real-ESRGAN生成器还有两个关键设计。第一是移除了所有BN（Batch Normalization，批归一化）层，因为研究发现在GAN框架下BN层会引入伪影，降低生成质量。第二是使用残差缩放（Residual Scaling），将每个残差分支的输出乘以一个0到1之间的系数（论文中设为0.2），进一步抑制训练不稳定。

在判别器方面，Real-ESRGAN采用了改进的U-Net架构判别器，相比原始ESRGAN的VGG风格判别器，U-Net判别器能同时关注局部纹理和全局语义。此外还引入了频谱归一化（Spectral Normalization）来稳定GAN训练。

### 10.2.2 通用模型与动漫模型区别

Real-ESRGAN提供了多个预训练模型，最常用的有两个：通用模型RealESRGAN_x4plus和动漫模型RealESRGAN_x4plus_anime_6B。

通用模型使用全部23个RRDB模块，在DIV2K等自然图像数据集上训练，适合处理实拍照片、风景图、人像等真实场景图片。它的模型体积较大（约64MB），但泛化能力强，对各种类型的图片都有不错的放大效果。

动漫模型只使用6个RRDB模块（这也是名字中"6B"的由来），在动漫图片数据集上训练。模型体积更小（约18MB），推理速度更快。由于动漫图片的色彩和线条特征与自然照片差异很大——动漫图片通常有大面积纯色块、清晰的线条边缘、较少的随机纹理——专门训练的动漫模型能更好地保持画风，避免将动漫图片处理成"油画感"。

**选模型的建议：处理照片用通用模型，处理动漫用动漫模型，这不是可选项而是必选项。** 用通用模型放大动漫图片，往往会出现色彩溢出、线条模糊、画风改变等问题。反过来，用动漫模型放大照片，会丢失大量真实纹理细节，让照片看起来像油画。

### 10.2.3 Python调用代码示例

Real-ESRGAN提供了Python API，可以方便地集成到自己的项目中。以下是完整的调用示例：

```python
import cv2
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

# 1. 构建模型
# 通用模型
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=4)
# 动漫模型（取消注释切换）
# model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
#                 num_block=6, num_grow_ch=32, scale=4)

# 2. 初始化放大器
upsampler = RealESRGANer(
    scale=4,                           # 放大倍数
    model_path='weights/RealESRGAN_x4plus.pth',  # 模型路径
    model=model,
    tile=0,        # 分块大小，0表示不分块，显存不足时设为512或更小
    tile_pad=10,   # 分块重叠像素
    pre_pad=0,     # 预填充
    half=False     # 是否使用FP16半精度，True可加速但需GPU支持
)

# 3. 读取图片
input_path = 'input.jpg'
img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

# 4. 执行放大
output, _ = upsampler.enhance(img, outscale=4)

# 5. 保存结果
cv2.imwrite('output.png', output)
print(f'放大完成: {img.shape[:2]} -> {output.shape[:2]}')
```

代码中有几个参数值得注意。`tile`参数控制分块处理策略，当图片很大或显存不足时，将其设置为512或256可以避免显存溢出（OOM），代价是分块边界可能出现轻微接缝。`half`参数启用FP16半精度推理，在支持的GPU上可以提升约30%到50%的速度，同时减少一半显存占用。

如果需要在放大后增强人脸细节，可以结合GFPGAN（Generative Facial Prior GAN，生成式人脸先验GAN）使用：

```python
from gfpgan import GFPGANer

# 在RealESRGANer基础上包装人脸增强
restorer = GFPGANer(
    model_path='weights/GFPGANv1.4.pth',
    upscale=4,
    arch='clean',
    channel_multiplier=2,
    bg_upsampler=upsampler  # 传入Real-ESRGAN放大器作为背景放大
)

# 处理图片（自动检测人脸并增强）
output, _ = restorer.enhance(img, paste_back=True)
cv2.imwrite('output_face_enhanced.png', output)
```

### 10.2.4 命令行使用方法

除了Python API，Real-ESRGAN还提供了基于ncnn（Neural Network Compute Library，神经网络计算库）和Vulkan（跨平台图形API）的命令行版本，无需Python环境和CUDA支持，直接运行可执行文件即可：

```bash
# 基本用法
./realesrgan-ncnn-vulkan -i input.jpg -o output.png

# 指定模型和放大倍数
./realesrgan-ncnn-vulkan -i input.jpg -o output.png -n realesrgan-x4plus-anime -s 4

# 批量处理（输入为目录）
./realesrgan-ncnn-vulkan -i input_dir/ -o output_dir/ -n realesrgan-x4plus -s 2

# 指定GPU设备
./realesrgan-ncnn-vulkan -i input.jpg -o output.png -g 0
```

参数说明：`-i`输入路径（文件或目录），`-o`输出路径，`-n`模型名称，`-s`放大倍数，`-g`GPU设备ID，`-t`分块大小（默认32x32，增大可加速但需更多显存）。

**命令速查表：**

| 参数 | 含义 | 常用值 |
|------|------|--------|
| -i | 输入路径 | 文件或目录 |
| -o | 输出路径 | 文件或目录 |
| -n | 模型名称 | realesrgan-x4plus / realesrgan-x4plus-anime |
| -s | 放大倍数 | 2 / 3 / 4 |
| -t | 分块大小 | 32 / 64 / 128 |
| -g | GPU ID | 0 / 1 |
| -f | 输出格式 | png / jpg / webp |

### 10.2.3 二阶退化模型

Real-ESRGAN相比ESRGAN最核心的改进是引入了二阶退化模型（Second-Order Degradation Model）。理解这个改进的意义，需要先了解超分辨率模型的训练方式。

超分辨率模型的训练采用"退化-重建"范式：首先把高清图片通过人为降质（模糊+缩放+噪声+压缩）得到低清图片，然后训练模型从低清图片恢复高清原图。这个"人为降质"的过程就是退化模型。退化模型越接近真实世界中图片质量下降的过程，训练出来的模型在实际使用中效果就越好。

ESRGAN使用一阶退化模型：对高清图做一次模糊→缩放→加噪→JPEG压缩的流程。但真实世界中的图片退化往往更复杂——一张手机拍的照片可能先经过相机ISP处理（包含锐化、降噪、色彩映射），然后被社交平台二次压缩，最后又被截图三次压缩。这种多重退化的叠加效果是一阶模型无法模拟的。

Real-ESRGAN创新性地采用了二阶退化：把退化过程重复两次。第一阶退化模拟拍摄和初次传输的质量损失，第二阶退化模拟后续处理和传播中的进一步降质。每阶退化中模糊核、噪声强度、压缩质量都是随机采样的，使得训练数据覆盖了极广的退化分布。

这种设计让Real-ESRGAN在实际使用中表现出了强大的泛化能力。无论是百年前的老照片、低分辨率的网图、还是被多次转发的表情包，Real-ESRGAN都能有效恢复细节。这也是它被称为"Real"的原因——它面向的是真实世界（Real World）中复杂退化的图片，而非实验室条件下的人工降采样图片。

### 10.2.4 Python调用与批处理

Real-ESRGAN的Python接口封装得非常友好。以下是完整的Python调用示例，包含模型加载、图片放大和批量处理。

```python
import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

# 构建模型网络结构
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=4)

# 初始化超分辨率推理器
upsampler = RealESRGANer(
    scale=4,
    model_path='weights/RealESRGAN_x4plus.pth',
    model=model,
    tile=0,           # 0为不 分块，设为512可分块处理大图
    tile_pad=10,      # 分块时边缘填充
    pre_pad=0,        # 输入前填充
    half=True         # 使用FP16推理，加速并节省显存
)

# 读取图片并放大
img = cv2.imread('input.jpg', cv2.IMREAD_UNCHANGED)
output, _ = upsampler.enhance(img, outscale=4)
cv2.imwrite('output.png', output)

# 批量处理
import os
input_dir = 'images/'
output_dir = 'upscaled/'
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.endswith(('.jpg', '.png', '.webp')):
        img = cv2.imread(os.path.join(input_dir, filename))
        output, _ = upsampler.enhance(img, outscale=4)
        cv2.imwrite(os.path.join(output_dir, filename), output)
        print(f'Processed: {filename}')
```

代码中有几个关键参数值得说明。tile参数设为0表示不分块，适合处理小图。如果处理4K以上的大图，建议设为512，这样模型会分块处理避免显存溢出。half参数设为True使用FP16半精度推理，在支持的显卡上可以减半显存占用并提升速度，对画质的影响可以忽略。

## 10.3 Real-CUGAN

### 10.3.1 动漫图片专用放大工具

Real-CUGAN（Real Cascade U-Nets for Anime Image Super Resolution，级联U-Net动漫图像超分辨率）是由B站（bilibili）开发的动漫图像超分辨率模型。它在动漫社区中的口碑极高，被认为是目前最好的动漫图片放大工具之一。

Real-CUGAN的模型结构魔改自waifu2x的CUNet（Compact U-Net），训练代码则主要参考了Real-ESRGAN。其训练数据集使用了百万级高清动漫图片patch，训练数据规模和质量远超waifu2x和Real-ESRGAN的动漫模型。

在架构上，Real-CUGAN采用级联U-Net结构。U-Net的编码器-解码器设计配合跳跃连接，能够在不同尺度上提取和融合特征。级联意味着多个U-Net模块串联，每个模块负责处理不同尺度的超分辨率任务。这种设计在动漫图片上表现优异，因为动漫图片的特征（线条、色块、边缘）比自然照片更加结构化，U-Net的跳跃连接能有效保留这些结构信息。

### 10.3.2 与Real-ESRGAN的差异

Real-CUGAN和Real-ESRGAN虽然都是优秀的超分辨率工具，但在定位和表现上有明显差异。

训练数据方面，Real-CUGAN使用百万级高清动漫patch训练，而Real-ESRGAN的动漫模型训练数据规模和质量未知。更大的训练集让Real-CUGAN在动漫图片的泛化能力上更有优势。

处理效果方面，Real-CUGAN在动漫图片上通常产生更锐利的线条和更好的纹理保留。它对虚化区域的处理更自然——不会强行将虚化的背景清晰化，而是保持原有的景深效果。相比之下，Real-ESRGAN动漫模型有时会过度锐化，导致虚化区域出现伪影。

速度方面，Real-CUGAN的推理速度约为Real-ESRGAN动漫模型的2.2倍，约为通用Real-ESRGAN模型的8.4倍。这对于批量处理大量动漫图片来说是巨大优势。

功能方面，Real-CUGAN支持2x/3x/4x三种放大倍数，其中2倍模型支持4种降噪强度和保守修复模式，3倍和4倍模型支持2种降噪强度。Real-ESRGAN主要支持4倍放大（2倍模型也有但不常用），降噪选项较少。

兼容性方面，Real-CUGAN与waifu2x结构兼容，可以无缝替换waifu2x的工作流，这对已经在使用waifu2x的用户非常友好。

### 10.3.3 使用方法

Real-CUGAN的使用方式与Real-ESRGAN类似，同样提供Python和命令行两种方式。

Python调用：

```python
import cv2
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

# Real-CUGAN使用不同的模型文件，但可通过Real-ESRGAN框架调用
# 需要单独下载Real-CUGAN的模型权重
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=6, num_grow_ch=32, scale=4)

upsampler = RealESRGANer(
    scale=4,
    model_path='weights/upconv_7_anime_style_artnoise.npz',  # Real-CUGAN模型
    model=model,
    tile=512,
    tile_pad=10,
    half=True
)

img = cv2.imread('anime_input.png', cv2.IMREAD_UNCHANGED)
output, _ = upsampler.enhance(img, outscale=4)
cv2.imwrite('anime_output.png', output)
```

命令行使用（基于ncnn-vulkan版本）：

```bash
# 基本用法
./realcugan-ncnn-vulkan -i input.png -o output.png -s 4 -n 0

# 参数说明
# -s: 放大倍数 (2/3/4)
# -n: 降噪级别 (0=无降噪, 1=轻度, 2=中度, 3=重度, -1=保守修复)
# -g: GPU设备ID

# 批量处理
./realcugan-ncnn-vulkan -i input_dir/ -o output_dir/ -s 2 -n 1
```

**降噪级别的选择建议：** 原图质量较好（PNG无损）用`-n 0`，有轻微JPEG压缩痕迹用`-n 1`，网络图片有较明显压缩伪影用`-n 2`，严重退化图片用`-n 3`。保守修复模式`-n -1`适合不想让AI过度干预画风的场景，它只做最小限度的修复。

## 10.4 Upscayl

### 10.4.1 基于Real-ESRGAN+Vulkan的桌面工具

如果说Real-ESRGAN是给开发者用的，那Upscayl就是给所有人用的。Upscayl是一款免费开源的桌面端AI图片放大工具，底层基于Real-ESRGAN的ncnn-vulkan实现，用Electron框架封装了友好的图形界面。项目在GitHub上已收获约41.3k Stars，是目前最流行的开源图片放大GUI工具。

Upscayl采用Linux优先（Linux-First）的设计理念，同时完整支持Windows、macOS和Linux三大平台。它的核心价值在于：把Real-ESRGAN强大的AI放大能力包装成了"拖进去、点按钮、出结果"的极简操作流程，用户不需要任何编程知识或命令行经验。

技术上，Upscayl通过Vulkan API调用GPU进行推理计算。Vulkan是Khronos Group制定的跨平台图形和计算API，支持NVIDIA、AMD、Intel等多种显卡厂商的GPU。这意味着Upscayl不挑显卡品牌，只要支持Vulkan就能用，这比依赖CUDA的方案（只能在NVIDIA显卡上运行）覆盖面更广。

### 10.4.2 安装与使用

**Windows安装：**

前往Upscayl官网（https://upscayl.org/）或GitHub Releases页面下载最新版安装包。双击.exe安装文件，按提示完成安装即可。首次运行时如果提示Vulkan初始化失败，需要更新显卡驱动到最新版本。

**macOS安装：**

下载.dmg文件，打开后将Upscayl拖入应用程序文件夹。首次运行时可能需要右键选择"打开"来绕过macOS的Gatekeeper限制。注意macOS 12及以上版本才能运行Upscayl。

**Linux安装：**

提供AppImage和deb两种格式。AppImage无需安装，下载后赋予执行权限即可运行：

```bash
chmod +x Upscayl-x.x.x-linux.AppImage
./Upscayl-x.x.x-linux.AppImage
```

使用流程极其简单：打开软件，将图片拖入或点击选择文件，选择放大模型，点击Upscayl按钮，几秒钟后就能预览结果并保存。软件默认4倍放大，内置多个模型可选，包括通用模型和动漫模型。

### 10.4.3 批量放大功能

Upscayl支持批量放大，操作方式和单张图片几乎一样。切换到批量模式（Batch Upscale），选择一个包含待放大图片的文件夹，设置输出目录，选择模型和放大倍数，点击开始即可。

批量处理时会按顺序处理文件夹中的所有支持格式的图片（JPG、PNG、WEBP等），每张图片处理完后自动保存到输出目录。处理进度和当前状态会在界面上实时显示。

**Upscayl使用注意事项：** 软件需要兼容Vulkan的GPU才能运行，大多数2013年以后的独立显卡和部分集成显卡都支持。如果处理速度异常缓慢，检查是否在用集成显卡运行，可以在设置中手动指定使用独立显卡。默认4倍放大通常已经足够，过度放大（如16x）不会带来更多细节，只会增加文件体积和处理时间。

## 10.5 SD内置放大方案

在使用Stable Diffusion生成图片时，经常会遇到一个问题：直接生成高分辨率图片（如1024x1024以上）效果不好，因为SD模型在512x512分辨率下训练，超出训练分辨率会出现重复主体、画面混乱等"多头多身"现象。正确的做法是先在512x512下生成，再用放大方案提升分辨率。

### 10.5.1 Hires. fix（高分辨率修复）

Hires. fix是Stable Diffusion WebUI内置的高分辨率修复功能，本质上是一个两阶段生成流程。第一阶段在低分辨率（如512x512）下正常生成图片，使用20到30步采样完成初始构图。第二阶段将低分辨率图片放大到目标分辨率（如1024x1024），然后在放大后的图片上继续进行少量采样步骤（通常10到20步），让模型在高分辨率空间中补充细节。

Hires. fix的放大阶段可以选择不同的放大算法，包括Latent（潜空间放大）和各种实数放大器（如Latent、ESRGAN_4x、Lanczos、Nearest等）。Latent放大是在VAE（Variational Autoencoder，变分自编码器）的潜空间中直接插值，然后再解码回像素空间，这种方式保留了最多的原始生成信息，适合后续继续采样。ESRGAN_4x等实数放大器则直接在像素空间放大，速度快但会改变图像特征。

关键参数设置建议：Denoising strength（去噪强度）推荐0.3到0.5，值太低细节补充不足，值太高会改变原始构图。放大后采样步数10到20步通常足够。放大倍数1.5x到2x效果最佳，倍数过高容易出现伪影。

### 10.5.2 Ultimate SD Upscale脚本

Ultimate SD Upscale是Automatic1111的WebUI扩展脚本，比Hires. fix更灵活强大。它的核心思路是分块放大（Tiled Upscale）——将图片分成多个重叠的小块，对每块单独进行SD采样放大，最后将所有小块无缝拼合成一张大图。

这种分块策略的优势在于突破了显存限制。直接对4K图片做全图采样需要海量显存，但将其分成若干512x512的小块分别处理，每块只需要标准生成时的显存。这使得即使在中端显卡上，也能生成2K甚至4K分辨率的高质量图片。

Ultimate SD Upscale提供了多种分块控制参数。Tile width和Tile height控制每块的大小，默认512x512。Mask blur控制块间重叠区域的模糊融合，值越大拼接越自然但可能损失细节。采样参数（Sampler、Steps、Denoising strength）与标准生成一致，可以根据每块内容独立调整。

一个重要的功能是ControlNet集成。在分块放大时可以配合ControlNet（如Tile模型或Canny模型）来约束每块的生成方向，确保放大后的整体图像在结构上与原图保持一致。这对于建筑、场景等有严格结构的图片特别有用。

### 10.5.3 Tiled Upscale分块放大

Tiled Upscale的原理值得深入理解。假设我们要将一张512x512的图片放大到2048x2048，直接在高分辨率下做全图采样，U-Net需要处理2048x2048的特征图，显存占用是512x512时的16倍。对于8GB显存的显卡来说，这几乎必然导致OOM（Out of Memory，显存溢出）。

分块放大的解决方案是将2048x2048的目标图像划分为若干512x512的子区域。为了确保块间拼接处没有明显接缝，相邻块之间会有重叠区域（通常为64到128像素）。在每个块的区域内，模型只需要处理512x512的输入，显存占用与标准生成相同。

处理每块时，模型不仅看到当前块的内容，还能通过重叠区域获取相邻块的上下文信息。拼接时使用高斯权重融合（Gaussian blending），在重叠区域对相邻块的输出做加权平均，确保过渡平滑。

```json
// Ultimate SD Upscale 关键参数配置
{
    "target_size": "2048x2048",
    "tile_width": 512,
    "tile_height": 512,
    "mask_blur": 8,
    "denoising_strength": 0.35,
    "sampler": "DPM++ 2M Karras",
    "steps": 20,
    "upscale_method": "Latent"
}
```

**三种SD放大方案对比：**

| 方案 | 适用场景 | 显存需求 | 放大上限 | 细节控制力 |
|------|----------|----------|----------|------------|
| Hires. fix | 1.5x-2x简单放大 | 中等 | 约2K | 一般 |
| Ultimate SD Upscale | 大幅放大+精细控制 | 低（分块） | 4K+ | 强 |
| Tiled VAE | 配合上述方案使用 | 降低VAE阶段显存 | 不限 | 无 |

**金句时刻：分块放大的本质是用时间换空间——用更多的小步迭代，替代一次性大步跨越，既绕过了显存墙，又保证了每块区域都能得到模型的充分关照。**

## 10.6 参考资源

以下是本章涉及的主要工具和资源链接，建议收藏备用。

**Real-ESRGAN**
- GitHub仓库：https://github.com/xinntao/Real-ESRGAN
- 论文地址：https://arxiv.org/abs/2107.10833
- 在线Demo：Replicate平台上可搜索Real-ESRGAN体验

**Real-CUGAN**
- GitHub仓库：https://github.com/bilibili/Real-CUGAN
- 在线体验：B站官方提供网页Demo

**Upscayl**
- 官网：https://upscayl.org/
- GitHub仓库：https://github.com/upscayl/upscayl
- 下载地址：GitHub Releases页面提供全平台安装包

**SD放大相关**
- Ultimate SD Upscale：https://github.com/Coyote-A/ultimate-upscale-for-automatic1111
- Hires. fix：Stable Diffusion WebUI内置，无需额外安装

**对比评测**
- 图片放大工具对比：https://blog.csdn.net/m0_71746299/article/details/141884034

**放大工具命令速查表：**

```
# Real-ESRGAN 命令行
./realesrgan-ncnn-vulkan -i input.jpg -o output.png -n realesrgan-x4plus -s 4

# Real-ESRGAN 动漫模型
./realesrgan-ncnn-vulkan -i anime.jpg -o output.png -n realesrgan-x4plus-anime -s 4

# Real-CUGAN 命令行（2倍放大+轻度降噪）
./realcugan-ncnn-vulkan -i input.png -o output.png -s 2 -n 1

# Real-ESRGAN 批量处理
./realesrgan-ncnn-vulkan -i input_dir/ -o output_dir/ -n realesrgan-x4plus -s 2

# Real-ESRGAN Python调用
python inference_realesrgan.py -n RealESRGAN_x4plus -i input.jpg -o output.png -s 4
```

## 本章总结

这一章怕浪猫带你走完了图片放大与高清修复的完整技术栈。核心知识点回顾：传统插值只能拉伸已有像素，AI超分辨率能生成新细节，这是质的飞跃。Real-ESRGAN凭借RRDB网络结构和高阶退化训练，成为通用场景的首选。Real-CUGAN在动漫领域表现更优，速度更快、线条更锐利。Upscayl把Real-ESRGAN包装成桌面工具，适合不想碰命令行的用户。SD内置的Hires. fix和Ultimate SD Upscale则解决了AI生图后的高分辨率需求。

在实际使用中，怕浪猫总结了一个"放大工具选择决策树"，供大家参考。第一步判断图片类型：动漫图片走Real-CUGAN路线，实拍照片走Real-ESRGAN路线，AI生成图片走SD Hires. fix路线。第二步判断使用场景：需要批量处理且涉及代码集成用Python接口，需要图形界面用Upscayl，在SD工作流中直接放大用Ultimate SD Upscale。第三步判断目标分辨率：放大2倍以内用Hires. fix即可，放大4倍用Real-ESRGAN，放大到印刷级分辨率（8K以上）需要Ultimate SD Upscale分块处理。

还有一个常见问题是放大后图片"太干净"，看起来像塑料感。这是因为AI放大模型在恢复细节时会"脑补"出一些不存在的纹理，过度放大或选择不当的模型会导致这些脑补纹理不自然。解决方法是控制放大倍数在2到4倍之间，配合适当的降噪参数，以及在必要时用Photoshop的"减少杂色"滤镜做后期微调。

对于商业项目的使用者，还需要注意放大工具的许可证。Real-ESRGAN采用BSD 2-Clause许可，允许商业使用但需要保留版权声明。Upscayl采用AGPL-3.0许可，如果通过网络提供服务需要开源你的修改。商业项目中如果对许可证有严格要求，建议使用Real-ESRGAN的原始代码而非Upscayl的封装。

**工具会迭代，原理不会过时。** 理解了超分辨率重建的基本逻辑——从退化模型到GAN训练再到推理部署——未来出现的新工具你也能快速上手，因为底层都是同一套思想在做变体。

如果这篇文章帮到了你，怕浪猫有三个小请求：第一，收藏它，下次放大图片时不用再到处找教程。第二，在评论区告诉我你在用哪个放大工具，遇到了什么坑，怕浪猫会逐条回复。第三，关注追更，下一章我会讲本地QClaw生图技能的配置与使用——把AI生图能力部署到自己的机器上，不依赖云端、不限次数、完全私密，这是自由创作的基石。我们第十一章见。

最后补充一个进阶技巧：多模型级联放大。对于追求极致画质的场景，可以用Real-ESRGAN先做4倍放大，然后用SD的Ultimate SD Upscale做二次放大并用ControlNet Tile模型约束结构，最后再过一遍Real-ESRGAN做细节增强。这种三级放大流程可以把一张512x512的图片放大到8K分辨率，同时保持惊人的细节保真度。当然，处理时间也会相应增加，一张图的完整处理可能需要5到10分钟。但如果你需要做印刷级输出或大型展示，这个时间投入是完全值得的。

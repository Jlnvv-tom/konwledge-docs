# 第七章 LoRA 模型与微调

一个2GB的LoRA文件，能做到过去需要一个6GB大模型才能实现的效果。更关键的是，它可以在一张消费级显卡上几分钟内训练完成。

我是怕浪猫，今天我们来聊聊AI图片生成中最实用的技术之一：LoRA。如果你觉得Stable Diffusion默认的画风不够个性化，或者想让自己的角色/风格在生成中保持一致，LoRA就是你的答案。

## 7.1 什么是LoRA

### LoRA（Low-Rank Adaptation）原理简介

LoRA，全称Low-Rank Adaptation，中文翻译为"低秩适配"。这是微软研究院在2021年提出的一种模型微调方法，最初用于大语言模型的微调，后来被AI图片生成社区广泛采用。

LoRA的核心思想是：不需要修改整个大模型的所有参数，只需要训练一个很小的"补丁"模块，就能让模型学会新的风格或概念。

要理解LoRA，先理解什么是"低秩"。假设原始模型的某个权重矩阵W的维度是m x n（比如4096 x 4096，约1600万个参数）。LoRA把这个大矩阵的更新分解为两个小矩阵的乘积：W' = W + A x B，其中A是m x r的矩阵，B是r x n的矩阵，r就是"秩"（rank），通常取4到64。

当r=8时，A的维度是4096 x 8，B的维度是8 x 4096，两者加起来只有65536个参数，比原始矩阵的1600万少了244倍。但实验证明，这些参数足够让模型学到新的风格。

这里的关键数学原理是：虽然原始权重矩阵W是满秩的（rank=4096），但模型在微调时权重的变化量Delta-W通常是低秩的。也就是说，虽然Delta-W也是4096x4096的矩阵，但它的有效信息只集中在少数几个维度上。LoRA就是利用这个性质，用低秩矩阵A×B来近似Delta-W，从而大幅减少需要训练的参数量。

LoRA之所以在AI图片生成领域大受欢迎，还有一个重要原因：它在推理时可以把A×B合并回原始权重W中，不增加任何推理延迟。这和另一肿微调方法Adapter不同，Adapter需要在网络中插入额外层，推理时会变慢。

```
LoRA低秩分解原理：

原始权重更新：  W_new = W + Delta_W
                Delta_W 维度: [4096, 4096] = 16,777,216 参数

LoRA分解：     Delta_W ≈ A × B
                A 维度: [4096, r=8]  = 32,768 参数
                B 维度: [r=8, 4096]  = 32,768 参数
                总计: 65,536 参数 (降低244倍)

推理时：        output = W × x + A × B × x
                (A×B 的计算可以合并到W中，零额外推理开销)
```

在训练过程中，原始权重W被冻结（不参与梯度更新），只有A和B两个小矩阵参与训练。训练完成后，可以把A×B的值直接加到W上，保存为一个新的Checkpoint；也可以保持W不变，单独保存A和B作为LoRA文件。后者就是我们在Civitai上下载的LoRA文件。

```
LoRA低秩分解原理：

原始权重更新：  W_new = W + Delta_W
                Delta_W 维度: [4096, 4096] = 16,777,216 参数

LoRA分解：     Delta_W ≈ A × B
                A 维度: [4096, r=8]  = 32,768 参数
                B 维度: [r=8, 4096]  = 32,768 参数
                总计: 65,536 参数 (降低244倍)

推理时：        output = W × x + A × B × x
                (A×B 的计算可以合并到W中，零额外推理开销)
```

> LoRA的精妙之处在于：它不是在"修改"大模型，而是在大模型旁边加了一条"小路"，让信息可以走捷径到达特定风格。

### LoRA vs. Checkpoint 模型的区别

Checkpoint大模型是完整的生成模型，包含UNet、文本编码器、VAE等全部组件。一个SD 1.5的Checkpoint文件通常约2-7GB，SDXL约6-13GB。训练一个Checkpoint需要海量数据和昂贵的GPU集群，普通用户无法完成。

LoRA则是一个小型"补丁"文件，通常只有几十MB到几百MB。它不能独立工作，必须加载到某个Checkpoint之上。训练一个LoRA只需要几十到几百张图片和一张消费级显卡，几小时内就能完成。

打个比方，Checkpoint就像是操作系统，LoRA就像是应用程序。操作系统提供了基础能力，应用程序在操作系统上添加特定功能。你可以随时安装或卸载应用程序，也可以同时运行多个应用程序。同样地，LoRA可以随时加载卸载，也可以多LoRA叠加使用。

除了Checkpoint和LoRA，还有一种中间形态叫Embedding（也叫Textual Inversion，文本反转）。Embedding比LoRA更小（通常只有几KB到几十KB），但能力也更有限，主要用于定义一个特定的概念或触发词。Embedding通过训练让模型理解一个新的关键词，比如训练一个Embedding让"my_dog"这个关键词对应你的宠物的样子。

| 特性 | Checkpoint大模型 | LoRA微调模型 | Embedding |
|------|----------------|-------------|------------|
| 文件大小 | 2-13GB | 10-500MB | 1-100KB |
| 训练数据 | 数百万张图 | 几十到几百张图 | 3-20张图 |
| 训练硬件 | 多张A100/H100 | 单张RTX 3060即可 | 单张RTX 2060即可 |
| 训练时间 | 数天到数周 | 1-8小时 | 10-30分钟 |
| 能否独立使用 | 能 | 否，需加载到Checkpoint上 | 否，需加载到Checkpoint上 |
| 风格覆盖 | 广泛 | 特定风格/角色/概念 | 单一概念 |
| 可叠加性 | 一次只能用一个 | 可同时叠加多个 | 可同时叠加多个 |
| 修改部位 | 全部参数 | 注意力层的部分参数 | 仅文本编码器的嵌入层 |

### LoRA 的优势：轻量、灵活、可叠加

LoRA有三大核心优势。

第一是轻量。一个LoRA文件通常只有几十到几百MB，下载和存储都很方便。你可以在硬盘里存放几百个LoRA，根据需要随时切换。相比之下，一个Checkpoint大模型动辄几个GB，切换一次就要重新加载整个模型，耗时且占显存。

第二是灵活。LoRA可以随时加载和卸载，不需要重启模型。在WebUI中，只需要在提示词中加入或移除LoRA标签就能切换风格。这意味着同一个Checkpoint模型，加载不同的LoRA可以产出完全不同风格的图片。

第三是可叠加。你可以同时加载多个LoRA，让它们的风格融合。比如同时加载一个"油画风格"LoRA和一个"赛博朋克"LoRA，可能得到一种赛博朋克风格的油画效果。这种组合的多样性是LoRA最迷人的地方。

除了以上三大优势，LoRA还有一个隐性优势：社区驱动。由于训练门槛低，全球有数万名创作者在持续训练和分享新的LoRA。这意味着你几乎可以找到任何风格、任何角色、任何材质的LoRA，不需要自己训练。Civitai上每周都有数百个新LoRA上传，这个生态的自我繁殖能力是其他微调技术无法比拟的。

```python
# 多LoRA叠加的提示词写法
# SD WebUI语法
prompt = """
a beautiful landscape,
<lora:oil_painting_style:0.7>,    # 油画风格LoRA，权重0.7
<lora:cyberpunk:0.4>,              # 赛博朋克LoRA，权重0.4
<lora:detail_enhance:0.3>          # 细节增强LoRA，权重0.3
"""

# ComfyUI中通过节点加载多个LoRA
# Load Checkpoint → Load LoRA (oil_painting) → Load LoRA (cyberpunk) → ...
# 每个LoRA节点设置strength_model和strength_clip
```

> 怕浪猫的经验：多LoRA叠加时，总权重建议控制在1.0左右。单个LoRA权重通常设0.3到0.7，太低效果不明显，太高会"污染"画面。

需要特别说明的是，LoRA并非完美无缺。它的主要局限在于：每个LoRA只能影响一种特定的风格或概念，无法像Checkpoint那样覆盖广泛的能力。另外，LoRA的效果严重依赖于基础Checkpoint的选择——同一个LoRA加载在不同的Checkpoint上，效果可能天差地别。因此选择LoRA时，要确认它适配的Checkpoint型号。

## 7.2 LoRA 使用方法

### LoRA 文件放置路径

使用LoRA之前，需要把下载的LoRA文件放到正确的目录。不同的工具路径不同。

在AUTOMATIC1111 WebUI中，LoRA文件放在：
```
models/stable-diffusion-webUI/models/Lora/
```

在ComfyUI中，LoRA文件放在：
```
ComfyUI/models/loras/
```

在QClaw生图技能中，LoRA的调用由后台自动处理，用户不需要手动管理文件路径。

放置好LoRA文件后，需要刷新模型列表。WebUI中点击"Refresh"按钮或重启WebUI，ComfyUI中点击"Refresh"按钮即可。

如果你的LoRA文件很多，建议按类型建子文件夹分类管理。比如`loras/styles/`放风格LoRA，`loras/characters/`放人物LoRA，`loras/materials/`放材质LoRA。WebUI和ComfyUI都支持读取子文件夹中的LoRA文件。

LoRA文件的格式主要有两种：`.safetensors`和`.pt`（或`.ckpt`）。推荐使用`.safetensors`格式，因为它更安全（不支持任意代码执行）且加载速度更快。如果下载的是`.pt`格式，可以使用Convert脚本转换为`.safetensors`。

文件命名也值得注意。建议用清晰的命名规则，比如`style_oil_painting_v2.safetensors`，包含类型、名称和版本号。这样在提示词中引用时一目了然，不会混淆同名但效果不同的LoRA。

### 在 WebUI / ComfyUI 中加载 LoRA

在WebUI中加载LoRA非常简单。在正向提示词框中，使用`<lora:文件名:权重>`的语法即可。文件名不需要写.safetensors后缀。

```
# 加载单个LoRA
prompt = "a portrait of a girl, <lora:koreanDollLikeness:0.6>"

# 加载多个LoRA
prompt = "a portrait of a girl, <lora:koreanDollLikeness:0.5>, <lora:detail_tweaker:0.3>"

# 使用子文件夹中的LoRA
prompt = "a landscape, <lora:styles/oil_painting:0.7>"
```

WebUI还提供了一个图形化的LoRA选择面板。点击提示词框下方的"LoRA"标签页，会列出所有已安装的LoRA文件。点击任意一个，对应的`<lora:文件名:权重>`标签就会自动插入到提示词中。这比手动输入文件名更方便，也避免了拼写错误。

在ComfyUI中，LoRA通过专门的节点加载。双击画布搜索"Load LoRA"，添加节点后选择LoRA文件并设置权重。LoRA节点需要串联在Checkpoint模型和后续节点之间。

```json
// ComfyUI中LoRA节点的JSON结构
{
  "class_type": "LoraLoader",
  "inputs": {
    "model": ["4", 0],           // 上游Checkpoint模型的model输出
    "clip": ["4", 1],            // 上游Checkpoint模型的clip输出
    "lora_name": "oil_painting_v2.safetensors",
    "strength_model": 0.7,       // 模型权重
    "strength_clip": 0.7         // CLIP编码器权重
  }
}
```

ComfyUI中LoRA节点有两个权重参数：strength_model和strength_clip。strength_model控制LoRA对UNet的影响（即图像生成能力），strength_clip控制LoRA对文本编码器的影响（即提示词理解能力）。通常两者设为相同值，但有时分别调整能获得更好效果。比如想让LoRA的触发词更有效，可以适当提高strength_clip；想让画面风格更强烈，可以适当提高strength_model。

在QClaw生图技能中，LoRA的加载是通过配置文件自动管理的。用户只需要在生图请求中指定LoRA名称和权重，系统会自动完成加载、推理和卸载的全过程。这大大简化了使用流程，特别适合不熟悉SD技术细节的用户。

### LoRA 权重调节语法

LoRA的权重值范围通常在0到1之间，但也可以设为负值（反向效果）或大于1（增强效果）。

权重为1.0表示完全应用LoRA的风格。0.5-0.7是最常用的区间，风格明显但不至于"喧宾夺主"。0.1-0.3适合微调，作为辅助效果。大于1.0可能导致画面崩坏，不推荐。负值（如-1）会产生LoRA风格的"反效果"，偶尔用于消除某种特征。

```python
# 权重效果对比（概念示意）
# weight = 0.0  → 完全无LoRA效果，等同于不加载
# weight = 0.3  → 轻微风格倾向，适合辅助增强
# weight = 0.6  → 明显风格特征（推荐起点）
# weight = 1.0  → 完全LoRA风格，可能过于强烈
# weight = 1.5  → 过度风格化，通常出现伪影
# weight = -1.0 → 反向效果，消除LoRA代表的特征

# WebUI中还可以用括号嵌套调整权重
# ((<lora:name:0.6>)) 等效于权重 0.6 * 1.1 * 1.1 = 0.726
```

除了数值权重，WebUI还支持"分层权重控制"。通过 Additional Networks 插件或 LoCon 参数，可以分别设置LoRA在UNet的不同层（IN层、OUT层、MID层）的权重。这种精细控制可以实现更微妙的效果，比如只在中间层应用LoRA风格，保持输入输出层的原始特征。

分层权重的一个实用场景是"只改变画风不改内容"。如果你想让一张人物照变成油画风但保持人物特征不变，可以把IN层权重设高（影响构图和内容）、OUT层权重设低（影响细节和风格）。反之，如果只想改变细节风格而保持构图，则OUT层设高、IN层设低。

```python
# 分层权重配置示例（需要Additional Networks插件）
# 在WebUI的Additional Networks面板中设置：
# IN01-IN10权重: 0.3  (降低输入层影响，保持原始构图)
# MID权重: 0.6       (中间层适度应用LoRA)
# OUT01-OUT10权重: 0.8 (输出层强应用，改变细节风格)
# 这样配置可以让LoRA主要影响画风而不改变主体内容
```

> 怕浪猫的调参流程：先用0.6出一张图看效果。太强就降到0.4，太弱就升到0.8。找到甜点权重后，再微调其他参数。

调参时还应注意一个现象：同一个LoRA在不同的Checkpoint上需要的权重可能不同。一般来说，如果Checkpoint本身的画风和LoRA的画风差异较大，需要较高的权重（0.7-0.9）才能让LoRA效果显现。如果Checkpoint的画风已经接近LoRA的目标风格，较低的权重（0.3-0.5）就足够了。

### 多 LoRA 叠加使用

多LoRA叠加是LoRA最强大的功能。通过组合不同类型的LoRA，可以创造出独特的视觉效果。

叠加的基本原则是"主次分明"：通常选择一个主风格LoRA（权重0.5-0.7）和一个或多个辅助LoRA（权重0.2-0.4）。主风格定义整体调性，辅助LoRA负责细节增强或特征添加。

叠加时需要注意LoRA之间的"冲突"问题。如果两个LoRA训练的方向相互矛盾（比如一个趋向写实、一个趋向动漫），叠加可能导致画面不自然。解决方法是调整权重比例，让一个明显主导另一个。

WebUI默认支持同时加载多个LoRA，但数量过多（超过5个）可能导致显存溢出或生成质量下降。ComfyUI通过节点链式加载LoRA，理论上没有数量限制，但实际使用中3-4个LoRA叠加强足够了。

```python
# 实用LoRA组合配方

# 配方1：高质量人像
prompt = """
portrait of a woman,
<lora:detail_tweaker:0.4>,        # 细节增强
<lora:skin_texture:0.3>,           # 皮肤纹理
<lora:lighting_enhance:0.3>        # 光影优化
"""

# 配方2：动漫风格场景
prompt = """
a beautiful anime landscape,
<lora:anime_style:0.6>,            # 动漫画风
<lora:background_detail:0.4>,      # 背景细节
<lora:color_grading:0.3>           # 色彩调色
"""

# 配方3：产品摄影
prompt = """
product photography of a perfume bottle,
<lora:product_lighting:0.5>,       # 产品灯光
<lora:studio_quality:0.4>,         # 工作室质感
<lora:detail_enhance:0.3>          # 细节锐化
"""

# 配方4：中国风水墨
prompt = """
mountain landscape with pavilion,
<lora:chinese_ink_painting:0.7>,   # 水墨画风
<lora:traditional_architecture:0.4>, # 传统建筑
<lora:mist_atmosphere:0.3>         # 烟雾氛围
"""

# 配方5：赛博朋克城市
prompt = """
cyberpunk city street at night,
<lora:cyberpunk_style:0.6>,        # 赛博朋克风格
<lora:neon_lights:0.4>,            # 霓虹灯效果
<lora:rain_reflection:0.3>         # 雨天反射
"""
```

这些配方不是固定的，你可以根据自己的需求调整权重和组合。关键是大胆尝试，有时候意外的组合会带来惊喜的效果。

## 7.3 热门 LoRA 类型

LoRA社区（主要是Civitai和LibLib）上有数万个LoRA模型，按用途可以分为几大类。

### 风格 LoRA

风格LoRA是最受欢迎的类型，它能让模型产出特定艺术风格的图片。常见的有油画风格、水彩风格、赛博朋克风格、吉卜力风格、新海诚风格等。

风格LoRA的训练通常需要100-500张同风格的图片。比如训练一个"水彩画风格"LoRA，需要收集各种水彩画作品，用BLIP（Bootstrapping Language-Image Pre-training，语言-图像自举预训练）或WD Tagger自动给图片生成描述标签，然后用这些带标签的图片进行训练。

风格LoRA的使用建议：权重0.5-0.8，搭配与风格匹配的提示词。比如使用"油画风格LoRA"时，提示词中应包含"oil painting, thick brush strokes, canvas texture"等匹配关键词，效果会比单独加载LoRA更好。

需要注意的是，风格LoRA的训练数据如果包含特定画师的作品，可能涉及版权问题。使用前最好确认LoRA的训练数据来源是否合法。

### 人物 LoRA

人物LoRA用于生成特定角色的图片，可以是真实人物（如明星、网红）也可以是虚拟角色（如动漫角色、游戏角色）。

人物LoRA的训练通常需要20-100张该角色的清晰图片，涵盖不同角度、不同表情、不同服装。训练的关键是图片质量而非数量：20张高质量的正面照比100张模糊的随手拍效果好得多。

使用人物LoRA时需要注意版权问题。用于个人欣赏通常没问题，但用于商业用途可能涉及肖像权侵权。Civitai上的部分人物LoRA会标注"仅供学习研究"。

人物LoRA的权重通常设0.6-0.9，比风格LoRA略高。这是因为人物特征比风格特征更具体，需要更强的LoRA影响才能准确还原。如果权重太低，生成的人物可能"像但不太像"；太高则可能出现训练集中的特定服装或背景"出疑"在生成的图片中。

### 材质 LoRA

材质LoRA让模型能生成特定材质质感的效果。比如黏土材质LoRA能让任何物体看起来像黏土做的，毛绒材质LoRA能生成毛绒玩具效果，金属材质LoRA能产出金属雕塑质感。

这类LoRA在产品设计和创意广告中非常实用。比如一个家具品牌想让产品图呈现"黏土风"来配合营销活动，用黏土材质LoRA就能快速实现。又如一个蛋糕店想制作圣诞主题的宣传图，用雪景材质LoRA就能把普通产品照变成冬季场景。

材质LoRA的原理是训练模型识别并生成特定材质的纹理特征。在训练时，数据集需要包含大量该材质的图片，且背景和物体要多样化（避免模型把材质和特定物体绑定）。比如训练"木质材质LoRA"，训练图片应该包含木桌、木椅、木板、木雕等各种木质物品，而不是只有木桌一种。

材质LoRA的权重通常设0.4-0.7，比人物LoRA略低。这是因为材质效果太强可能会"覆盖"物体本身的细节，让所有东西看起来都像同一块材质做的。适当降低权重可以让材质效果更加自然地融入生成图像。

### 场景 LoRA

场景LoRA专门用于生成特定类型的场景。比如城市夜景LoRA擅长生成霓虹灯闪烁的都市夜景，自然风光LoRA擅长生成山川湖泊，室内设计LoRA擅长生成各种装修风格的室内空间。

场景LoRA在建筑设计和室内设计领域有很高的实用价值。设计师可以用场景LoRA快速生成不同风格的效果图：现代简约、日式侀宅、工业风、北欧风等，辅助客户沟通和方案确定。

场景LoRA的训练需要100-300张场景图片，关键是要覆盖同一类型场景的多种变化。比如训练"咖啡厅场景"LoRA，需要收集不同风格、不同光线、不同角度的咖啡厅图片，让模型学会"咖啡厅"这个概念的通用特征而非某个特定咖啡厅的样子。

场景LoRA的一个进阶用法是配合ControlNet的MLSD（Mobile Line Segment Detection，移动线段检测）模型使用。先用MLSD提取建筑或室内空间的线条结构，再用场景LoRA填充风格和细节。这样生成的效果图既保持了准确的空间结构，又拥有LoRA带来的风格化外观。这个工作流在建筑可视化领域已经相当成熟。

| LoRA类型 | 典型文件大小 | 推荐权重 | 训练图片数 | 训练时间 | 适用场景 |
|---------|------------|---------|----------|---------|---------|
| 风格LoRA | 100-300MB | 0.5-0.8 | 100-500张 | 2-6小时 | 插画/概念艺术/海报设计 |
| 人物LoRA | 50-150MB | 0.6-0.9 | 20-100张 | 1-3小时 | 角色生成/IP形象/头像 |
| 材质LoRA | 80-200MB | 0.4-0.7 | 50-200张 | 2-4小时 | 产品设计/创意广告/3D渲染 |
| 场景LoRA | 100-250MB | 0.5-0.7 | 100-300张 | 2-5小时 | 建筑/室内/风景/游戏背景 |

选择LoRA类型时，关键是明确你的使用场景。如果你是插画师，需要稳定的个人画风，选风格LoRA。如果你是游戏开发者，需要批量生成NPC立绘，选人物LoRA。如果你是电商设计师，需要产品图变体，选材质LoRA。如果你是建筑师或室内设计师，需要效果图快速出稿，选场景LoRA。

实际使用中，很多专业创作者会自己训练专属LoRA。比如一位插画师收集了自己过去三年的100张作品，训练了一个"我的画风"LoRA。之后无论用什么Checkpoint，只要加载这个LoRA，生成的图就带有他个人的画风特征。这比每次手动调整提示词要高效得多，也更能保持风格一致性。

## 7.4 LoRA 模型资源

### Civitai LoRA 专区

Civitai（https://civitai.com/models）是全球最大的Stable Diffusion模型社区，上面有数万个LoRA模型，涵盖风格、人物、材质、场景等各种类型。

Civitai的使用方法：在首页选择"LoRA"模型类型，然后按下载量排序或按标签筛选。每个LoRA页面都有示例图片、推荐权重、触发词（Trigger Word，即在提示词中必须包含的关键词）和使用说明。

下载LoRA时注意查看模型兼容性：有些LoRA是针对SD 1.5训练的，在SDXL上效果不好；反之亦然。页面通常会标注"Base Model"信息。

Civitai的评分系统也很有参考价值。关注三个指标：下载量（反映受欢迎程度）、评分（反映质量）、评论数（反映活跃度）。下载量超过1万的LoRA通常质量有保障。

Civitai还支持"在线生图"功能，不需要本地显卡就能测试LoRA效果。你可以直接在LoRA页面的"Generated Images"区域输入提示词、调整参数、生成图片。这个功能对于没有本地GPU的用户特别友好。

### LibLib（哩布哩布）

LibLib（https://www.liblib.ai/）是国内最大的SD模型社区，也有大量LoRA模型。优势是访问速度快（国内服务器）、中文界面、有在线生图功能（不需要本地显卡就能测试LoRA效果）。

LibLib的很多LoRA是国内作者训练的，包含不少国风、水墨、书法等中国风格材的LoRA，这些在Civitai上比较少见。

LibLib还提供了"模型实验室"功能，可以在线微调LoRA。你上传几十张图片，平台自动帮你训练LoRA，不需要本地硬件。训练费用按次计费，通常几元到几十元一次。

### Hugging Face

Hugging Face（https://huggingface.co/models）是开源AI模型的综合平台，除了SD模型外还有各种其他AI模型。Hugging Face上的LoRA通常更"学术"一些，适合研究用途。很多论文配套的LoRA模型会发布在这里。

Hugging Face的优势是模型版本管理规范，每个模型都有详细的版本历史、模型卡片（Model Card）和技术报告。如果你需要了解LoRA的具体训练细节（数据集、超参数、评估指标），Hugging Face是最好的信息来源。

### 其他资源

除了以上三大平台，还有一些值得关注的LoRA资源。

Kohya Model Gallery是Kohya_ss训练工具作者维护的模型展示页面，上面的LoRA都经过质量筛选。Reddit的r/StableDiffusion社区也经常有用户分享自训练的LoRA。国内的AIGC爱好者社群（如QQ群、Discord服务器）也有不少民间高手分享自制LoRA。

> 怕浪猫的建议：如果你在国内，优先用LibLib，下载速度快且有很多本土风格。如果翻墙方便，Civitai的资源更丰富。两者可以互补使用。

## 本章总结

LoRA是AI图片生成中最实用的微调技术，它用极小的参数量和训练成本实现了高质量的个性化生成。

核心要点回顾：LoRA通过低秩矩阵分解，把大模型的参数更新压缩到几十MB的文件中。它可以随时加载和卸载，可以多LoRA叠加使用，灵活性远超Checkpoint大模型。

使用LoRA的三个关键：选对类型（风格/人物/材质/场景）、调好权重（通常0.4-0.7）、善用叠加（主LoRA+辅助LoRA）。

LoRA的生态优势同样值得关注。Civitai上有数万个社区共享的LoRA，涵盖几乎所有你能想到的风格和主题。这个生态的自我繁殖速度远超商业模型——每天都有新的LoRA被上传，每周都有新的风格趋势出现。这种社区驱动的创新模式，是Stable Diffusion生态相比Midjourney和DALL·E的核心竞争优势。

从技术演进的角度看，LoRA之后还出现了一些改进版本。LoCon（LoRA-Convolution）在LoRA的基础上增加了对卷积层的微调，效果更强但文件也更大。LyCORIS是另一个改进方案，支持更多微调策略（DyRA、LoHa、LoKR等）。这些改进版本在Civitai上也有不少模型，但使用方法和LoRA类似，上手难度不大。

对于想深入学习LoRA原理的读者，推荐阅读原始论文《LoRA: Low-Rank Adaptation of Large Language Models》（arxiv.org/abs/2106.09685）。虽然论文主要讨论大语言模型，但LoRA在图像生成中的应用原理完全相同。对于想学习训练实践的读者，Civitai上有大量训练教程和经验分享，是最佳的学习资源。

对于想要自己训练LoRA的用户，怕浪猫推荐使用Kohya_ss这个训练工具。它是一个图形界面的LoRA训练工具，支持SD 1.5和SDXL，不需要写代码就能完成训练。训练流程概括为四步：准备图片数据集、用BLIP或WD Tagger生成图片描述标签、设置训练参数（rank、learning rate、steps等）、启动训练并监控loss曲线。详细的训练教程可以参考Civitai上的社区指南。

训练LoRA的常见参数配置参考：rank设为16或32（平衡效果和文件大小）、learning rate设为1e-4、batch size设为2或4、训练步数根据图片数量调整（通常每张图片训练10-20步）。如果训练出现过拟合（生成结果和训练图片太像），降低权重或减少训练步数。如果欠拟合（LoRA效果不明显），增加训练步数或提高rank值。

训练数据的准备是LoRA训练中最耗时的环节，也是决定最终效果的关键。以下是一些数据准备的实用建议。

图片质量比数量重要。20张高清、构图清晰、特征明显的图片，比200张模糊、构图混乱的图片训练效果好得多。建议分辨率至少512x512以上，主体占据画面主要部分。

角度和变化要丰富。如果是人物LoRA，需要包含正面、侧面、半侧面的照片，以及不同表情和不同光线条件下的照片。这能让模型学会人物的三维特征而非特定角度的平面投影。

背景要多样化。如果所有训练图片的背景都是白色，模型可能会把白色背景作为LoRA特征的一部分。解决方案是在不同背景下拍摄或裁剪主体，让模型只学习主体特征而非背景特征。

标签描述要准确。每张训练图片都需要有一个文本描述文件（.txt或.caption），用自然语言或关键词描述图片内容。标签的质量直接影响LoRA的效果：标签太简单模型学不到细节，标签太复杂模型可能过拟合到特定描述上。

```python
# Kohya_ss训练配置示例（dataset_config.toml）
[general]
resolution = 512                    # 训练分辨率
shuffle_caption = true              # 随机打乱标签顺序
keep_tokens = 1                     # 保留前N个标签的顺序（通常是触发词）

[[datasets]]
batch_size = 2                      # 批量大小
num_repeats = 10                    # 每张图片重复次数

  [[datasets.subsets]]
  image_dir = "/path/to/training_images"
  caption_extension = ".txt"        # 标签文件后缀
  class_tokens = "my_style"          # 触发词
```

训练完成后，一定要测试LoRA的效果。测试方法：用固定的提示词和Seed值，分别在不加载LoRA和加载LoRA（权重0.3/0.5/0.7/1.0）的情况下生成图片，对比效果。理想的LoRA应该在权重0.5-0.7时就能明显展现目标风格，同时不破坏基础模型的能力。

如果测试发现LoRA效果不理想，可以尝试以下排查思路。效果太弱：增加训练步数、提高rank值、检查标签是否正确。效果太强导致伪影：减少训练步数、降低rank值、降低使用时的权重。风格不稳定（有时有效有时无效）：增加训练数据多样性、检查是否有低质量图片混入数据集。触发词不生效：确认触发词在所有训练图片的标签中都出现了，且拼写一致。

| 关键概念 | 全称 | 一句话解释 |
|---------|------|-----------|
| LoRA | Low-Rank Adaptation | 低秩适配，用小矩阵近似大模型的参数更新 |
| Checkpoint | Checkpoint | 大模型文件，包含完整的生成能力 |
| Rank | Rank | 矩阵的秩，LoRA中控制参数量的超参数 |
| Trigger Word | Trigger Word | 触发词，LoRA训练时绑定特定概念的关键词 |
| Weight/Strength | Weight/Strength | LoRA的权重，控制风格强度 |
| Fine-tuning | Fine-tuning | 微调，在预训练模型基础上继续训练 |
| Overfitting | Overfitting | 过拟合，模型过度学习训练数据导致泛化能力下降 |

觉得有用？收藏起来，下次用LoRA时直接照着配方表调参。

你用过哪些好用的LoRA？评论区分享一下，怕浪猫也想去试试。

关注怕浪猫，下期我们讲DALL·E 3与OpenAI生态——ChatGPT里的生图神器，不只是"输入提示词等结果"这么简单。

系列进度 7/14，下篇：第八章 DALL·E 3与OpenAI生态，从API调用到智能体集成，解锁AI生图的另一种姿势。

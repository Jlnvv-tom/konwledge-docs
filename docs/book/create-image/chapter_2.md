# 第二章 提示词工程（Prompt Engineering）

> 你是否也曾遇到这样的情况：同样的AI绘画工具，别人生成的图惊艳朋友圈，你的却总是"差点意思"？问题90%出在提示词上。

我是怕浪猫，一个在AI绘画坑里摸爬滚打了一年多的技术写手。过去这一年，我测试了上万条提示词，踩过无数坑，也总结出了一套真正能打的方法论。这一章，怕浪猫会带你从零开始，彻底搞懂提示词这门"手艺"。

不管你用的是Stable Diffusion、Midjourney还是DALL-E 3，提示词都是决定生图质量的第一道门槛。写好提示词，不是玄学，是工程。

## 2.1 提示词基础

### 什么是Prompt（提示词）？为什么它决定生图质量

Prompt（提示词）是你输入给AI模型的自然语言指令，告诉它"画什么、怎么画"。在扩散模型（Diffusion Model）的架构中，提示词经过CLIP（Contrastive Language-Image Pre-training，对比语言-图像预训练）模型编码成向量，作为条件信号注入到去噪过程的每一步中。这意味着，提示词的每一个词都会直接影响模型从噪声中"雕刻"出图像的方向。

打个比方，AI模型就像一个能力极强但完全没有任何主观意图的画师。你不告诉他要画什么，他就只能随机涂抹。提示词就是你的"创作需求文档"，写得越精准，画师交付的成果就越接近你心里的画面。提示词模糊，AI就会用自己的"默认值"去填补空白，而这些默认值往往不是你想要的。

怕浪猫在实际测试中发现，同一条模型、同样的参数配置，仅仅把"a girl"改成"a young girl with freckles standing in golden hour light"，画面质量就会有质的飞跃。原因很简单：更丰富的语义信息让CLIP编码出的向量更"有方向感"，模型在去噪过程中就有了更明确的引导信号。

> **金句：提示词不是在"描述图片"，而是在"编程图像"。每一个词都是一段编译后的向量指令，喂给模型的去噪过程。**

CLIP模型的工作机制值得深入理解。它由两个编码器组成：文本编码器（Text Encoder）和图像编码器（Image Encoder）。在训练阶段，这两个编码器被优化为将匹配的文本和图像映射到向量空间中相近的位置。当你输入提示词时，文本编码器将每个词转换为一个高维向量（通常为768维），这些向量携带了丰富的语义信息。

在扩散模型的去噪过程中，这些文本向量通过交叉注意力机制（Cross-Attention）注入到UNet的各个层级中。具体来说，UNet在每一步去噪时，都会"查询"文本向量，决定当前噪声预测应该朝哪个方向调整。这就是为什么提示词中的每个词都会对最终图像产生影响的原因。

```python
# CLIP文本编码的简化示意
import torch
from transformers import CLIPTextModel, CLIPTokenizer

tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
text_encoder = CLIPTextModel.from_pretrained("openai/clip-vit-large-patch14")

prompt = "a cyberpunk city at night, neon lights, rain wet streets"

# 步骤1: 分词 - 将文本切分为子词单元
tokens = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
# tokens.input_ids 形状: [1, 77] (77是CLIP的最大序列长度)

# 步骤2: 编码 - 将token转换为768维的嵌入向量
with torch.no_grad():
    text_embeddings = text_encoder(tokens.input_ids).last_hidden_state
# text_embeddings 形状: [1, 77, 768]

# 步骤3: 这些向量将通过Cross-Attention注入UNet的去噪过程
# 每一步去噪时，UNet会"注意"文本向量的不同部分
# 比如"neon lights"可能在去噪初期被重点关注(决定光源布局)
# 而"rain wet streets"可能在后期被关注(决定表面反射细节)
```

上面这段代码展示了提示词从文本到向量的完整转换链路。理解了这个过程，你就会明白为什么某些关键词比其他关键词"更有效"——它们在CLIP的训练数据中与特定视觉特征有更强的关联，因此编码出的向量更能引导模型生成对应的视觉元素。

### 提示词的五大要素：主体+场景/环境+风格/画风+光影/色调+构图/视角

一条高质量提示词，通常包含五个核心维度。怕浪猫把它叫做"五维提示词框架"，你可以在几乎所有优秀提示词中找到这五个要素的影子。

第一是主体（Subject），即画面的核心对象。可以是人物、动物、物品、建筑等。主体描述要具体，包括外貌特征、服饰、动作、表情等。例如"一个穿红色汉服的少女，手持纸伞，微微侧头"就比"一个女孩"提供了多得多的信息量。

第二是场景/环境（Scene/Environment），即主体所处的空间。是森林、城市街头、还是宇宙飞船内部？环境描述为画面提供了背景信息，也让AI在生成时有了更丰富的纹理素材可以调用。"在雨后的东京街头"和"在阳光明媚的加州海滩"会导向截然不同的视觉结果。

第三是风格/画风（Style），这是控制画面"观感"的关键维度。是写实摄影、二次元插画、还是油画？风格关键词直接决定了模型从训练数据中"调用"哪类视觉模式。常见做法是在提示词末尾加上风格修饰词，如"photorealistic"、"anime illustration"、"oil painting style"等。

第四是光影/色调（Lighting/Color），光影是画面氛围的灵魂。关键词如"golden hour"（黄金时刻）、"cinematic lighting"（电影感布光）、"soft rim light"（柔和轮廓光）能显著改变画面的情绪表达。色调方面，"warm tones"（暖色调）、"desaturated"（低饱和度）、"teal and orange"（青橙配色）等都是常用的调色指令。

第五是构图/视角（Composition/Camera），控制画面的"摄影感"。"close-up"（特写）、"wide angle"（广角）、"bird's eye view"（鸟瞰视角）、"rule of thirds"（三分构图法）等关键词，能让AI模拟不同的摄影构图方式。这组要素在写实摄影风格中尤为重要。

下面是一个五维框架的完整示例：

```
A young woman with long silver hair, wearing a dark leather jacket,
standing on a neon-lit cyberpunk street at night,
anime illustration style,
cinematic lighting with purple and blue neon glow,
shot from a low angle, rule of thirds composition
```

拆解来看：主体是"银发皮衣少女"，场景是"霓虹赛博朋克街道"，风格是"动漫插画"，光影是"紫蓝霓虹电影感布光"，构图是"低角度三分法"。五个维度各司其职，模型得到的信息既丰富又有层次。

怕浪猫建议你在写提示词时，用这个五维框架做自检。写完一条提示词后，逐项检查：主体描述够不够具体？场景有没有交代清楚？风格关键词选对了吗？光影有没有描述？构图视角有没有指定？五个维度都覆盖到了，提示词的基本盘就稳了。

### 正向提示词（Positive Prompt）与反向提示词（Negative Prompt）

AI绘画中，提示词分为正向和反向两类。正向提示词（Positive Prompt）告诉模型"要画什么"，反向提示词（Negative Prompt）告诉模型"不要画什么"。两者配合使用，才能精确控制画面输出。

正向提示词的写法就是我们前面讲的五维框架，描述你希望看到的画面。而反向提示词则是排除你不想要元素的利器。常见的反向提示词包括"low quality"（低质量）、"blurry"（模糊）、"deformed hands"（畸形手部）、"extra fingers"（多余手指）、"watermark"（水印）、"text"（文字）等。

反向提示词的工作原理涉及Classifier Free Guidance（CFG，无分类器引导）的数学机制。在CFG的计算中，模型同时执行两次去噪预测：一次是有条件的（conditioned，使用你的正向提示词），一次是无条件的（unconditioned，使用空提示词或反向提示词）。最终的去噪方向是有条件预测和无条件预测之间的差值，乘以CFG Scale（引导强度系数）。

当你提供反向提示词时，模型会将反向提示词作为"无条件"路径的输入。这样，CFG的引导方向就变成了"远离反向提示词描述的特征，靠近正向提示词描述的特征"。简单说，正向提示词是油门，反向提示词是刹车，两者配合才能开出好车。

```python
# CFG引导的核心计算逻辑（简化版）
def classifier_free_guidance(model_output_cond, model_output_uncond, guidance_scale):
    """
    CFG公式: output = uncond + scale * (cond - uncond)
    
    model_output_cond: 使用正向提示词的噪声预测
    model_output_uncond: 使用反向提示词(或空提示词)的噪声预测
    guidance_scale: CFG强度，通常7到12
    """
    # guidance_scale越大，正向提示词的引导力越强
    # 但太大会导致画面过饱和、边缘出现伪影
    guided_output = model_output_uncond + guidance_scale * (
        model_output_cond - model_output_uncond
    )
    return guided_output

# 实际使用中，negative prompt替换了uncond路径
# 这意味着模型会主动"远离"反向提示词描述的特征空间
# 比如反向提示词中有"blurry"，模型就会在去噪时
# 主动增加高频细节，避免生成模糊区域
```

怕浪猫的经验是：反向提示词不宜过长，5到15个关键词足够。过长会导致模型"无所适从"，反而影响画面质量。针对不同风格，反向提示词也要调整。比如写实风格要反向"cartoon, anime, illustration"，而动漫风格则要反向"photorealistic, realistic skin texture"。

下面是一组正向与反向提示词的搭配示例：

```python
positive_prompt = """
masterpiece, best quality, a young woman with silver hair,
wearing a dark leather jacket, standing on a neon-lit street,
cyberpunk city at night, cinematic lighting,
purple and blue neon glow, low angle shot, detailed
"""

negative_prompt = """
low quality, worst quality, blurry, deformed hands,
extra fingers, missing fingers, watermark, text,
bad anatomy, bad proportions
"""
```

> **金句：正向提示词是给AI画的蓝图，反向提示词是给AI划的红线。蓝图越清晰，红线越精准，作品越出彩。**

## 2.2 提示词编写技巧

### 简短描述的扩写方法

很多人刚开始写提示词时，脑子里只有一个模糊的画面，比如"海边日落"。这种两三个词的描述远不够让AI生成高质量图像。怕浪猫这里教你一个"扩写三步法"，把简短描述扩展为专业级提示词。

第一步是主体扩写。把"海边日落"里的隐含主体挖出来。海边有谁？是一个人还是一对情侣？在做什么？是在散步、坐着、还是奔跑？穿着什么衣服？把这些信息补充进去，比如"a couple in white linen clothes walking barefoot on the beach"。

第二步是环境与氛围扩写。日落是什么样的日落？是金色余晖还是火烧云？海面是平静还是有浪花？天空是什么颜色？空气中有没有雾气？"golden sunset with dramatic orange and pink clouds, calm sea with gentle waves reflecting the sky"就比单纯的"sunset"丰富得多。

第三步是技术与风格扩写。加上摄影参数和风格描述。"shot on Sony A7R IV, 35mm lens, f/1.8, golden hour photography, cinematic color grading, ultra detailed, 8K resolution"。这些技术词汇会让AI模拟专业摄影的成像质感。

扩写前后对比：

```
# 扩写前
sunset on the beach

# 扩写后
A couple in white linen clothes walking barefoot on a sandy beach,
golden sunset with dramatic orange and pink clouds,
calm sea with gentle waves reflecting the colorful sky,
warm golden hour lighting, soft natural light,
shot on Sony A7R IV, 35mm lens, f/1.8,
cinematic color grading, photorealistic, ultra detailed, 8K
```

扩写的核心原则是：每个新增的词都要携带新的视觉信息，而不是重复语义。"beautiful pretty gorgeous girl"三个形容词传递的信息量几乎相同，不如换成"girl with freckles and a shy smile"。后者提供了两个具体的视觉特征——雀斑和害羞的微笑，而前者只是三个不同程度的"漂亮"。

怕浪猫在扩写时常用一个技巧：闭眼想象画面，然后描述你"看到"的每一个细节。天空是什么颜色？地面是什么材质？光线从哪个方向来？空气中有没有尘埃或雾气？这种"可视化描述法"能帮你挖出很多容易被忽略的视觉细节。

### 关键词权重与括号嵌套语法

在Stable Diffusion中，提示词的每个关键词可以通过语法控制权重，实现"强调"或"弱化"的效果。这是提示词工程中最精细的控制手段之一。

最基础的权重语法是圆括号和数字。`(keyword:1.3)`表示将该关键词的权重提升到1.3倍，`(keyword:0.7)`表示弱化到0.7倍。默认权重是1.0，数值越大，该关键词对画面的影响越强。怕浪猫建议权重调整范围控制在0.5到1.5之间，超出这个范围容易出现画面崩坏。

嵌套括号会叠加权重。`((keyword))`等效于`(keyword:1.21)`，`(((keyword)))`等效于`(keyword:1.331)`。每一层括号的默认乘数是1.1。这种写法在早期WebUI中很常见，但现在更推荐使用冒号数字的写法，因为更精确也更易读。

下面是权重调整的核心代码逻辑。在Stable Diffusion的提示词解析器中，权重计算的伪代码如下：

```python
def parse_prompt_weight(prompt_string):
    """
    解析提示词中的权重语法
    支持格式: (word:1.3), ((word)), ((word:1.2))
    """
    tokens = []
    i = 0
    while i < len(prompt_string):
        if prompt_string[i] == '(':
            # 匹配括号内的内容和权重
            depth = 1
            j = i + 1
            while j < len(prompt_string) and depth > 0:
                if prompt_string[j] == '(':
                    depth += 1
                elif prompt_string[j] == ')':
                    depth -= 1
                j += 1
            
            inner = prompt_string[i+1:j-1]
            
            # 检查是否有 :weight 格式
            if ':' in inner:
                parts = inner.rsplit(':', 1)
                word = parts[0].strip()
                weight = float(parts[1].strip())
            else:
                word = inner
                weight = 1.1  # 每层括号默认1.1倍
            
            tokens.append((word, weight))
            i = j
        else:
            # 普通文本，权重为1.0
            tokens.append((prompt_string[i], 1.0))
            i += 1
    
    return tokens


def apply_weights_to_embeddings(tokens, text_encoder):
    """
    将权重应用到CLIP文本编码器的输出上
    权重会缩放对应词向量在条件信号中的"音量"
    """
    weighted_embedding = None
    for word, weight in tokens:
        embedding = text_encoder.encode(word)
        if weighted_embedding is None:
            weighted_embedding = embedding * weight
        else:
            weighted_embedding += embedding * weight
    return weighted_embedding
```

这段代码展示了权重解析的核心逻辑：解析器遇到括号时提取内部文本和权重数值，然后将权重乘到对应词的CLIP嵌入向量上。这意味着权重越高的词，其向量在条件信号中的"音量"越大，模型在去噪时会更"用力"地朝那个方向生成。反之，权重低的词会被其他词"淹没"，在画面中的存在感减弱。

实际使用中，怕浪猫的建议是：先写一版不带权重的提示词，生成几张图看看效果。然后针对"不够强"的特征加权重，针对"过头了"的特征降权重。这是一种迭代调优的过程，而非一蹴而就。

```
# 权重调整示例
a girl with (long silver hair:1.3), wearing (red dress:1.2),
standing in a (forest:0.8), (cyberpunk style:1.4),
soft lighting, highly detailed
```

上面这条提示词中，银发和红裙被强调，森林被弱化，赛博朋克风格被强力强调。这样生成的画面会更偏向赛博风格而非自然森林。

还有两种高级权重语法值得一提。方括号语法`[keyword]`等效于`(keyword:0.9)`，用于轻微弱化。混合语法`[keyword1|keyword2]`表示在两个词之间交替，生成的画面会同时体现两种特征，常用于风格融合。例如`[cyberpunk|fantasy]`会生成赛博朋克与奇幻融合的独特视觉风格。

### 自然语言描述 vs. 关键词堆叠

提示词有两种主流写法：自然语言描述和关键词堆叠。两者各有优劣，适用的场景也不同。

自然语言描述就是用完整的句子描述画面，像写作文一样。例如"A beautiful young woman standing in a sunflower field at sunset, her hair gently blowing in the wind, warm golden light bathing her face"。这种写法在DALL-E 3和Midjourney v6中表现很好，因为这些模型使用了更强的文本理解能力，能解析复杂句式。

关键词堆叠则是用逗号分隔的词组列表，每个词组描述一个特征。"beautiful young woman, sunflower field, sunset, wind blown hair, golden hour lighting, warm tones"。这种写法在Stable Diffusion（特别是SD 1.5系列）中更常用，因为CLIP文本编码器对短词组的响应更稳定。

怕浪猫的实践建议是：根据模型选择写法。用Midjourney或DALL-E 3时，优先用自然语言描述，因为它们使用了T5-XXL（Text-to-Text Transfer Transformer，文本到文本迁移学习模型）等更强的文本编码器，能理解上下文语义。用Stable Diffusion时，关键词堆叠更可控，因为CLIP模型对独立词组的编码更直接，不会因为句法解析丢失信息。

还有一种混合写法效果不错：用自然语言描述主体和场景，用关键词补充风格和技术参数。"A young woman reading a book in a cozy coffee shop, warm afternoon light through the window, anime style, detailed illustration, soft colors, 4K"。这种写法兼顾了语义丰富度和关键词的精确控制。

值得注意的是，关键词的顺序会影响权重。在大多数实现中，提示词靠前的关键词会获得略高的注意力权重，这是因为CLIP的Transformer结构对序列前部token有微弱的"偏好"。因此，把最重要的主体描述放在最前面，风格和技术参数放在后面，是一个通用的最佳实践。

> **金句：提示词的写法不是选"对的"，而是选"合适的"。模型决定了语法，需求决定了结构，没有放之四海皆准的模板。**

### Seed（随机种子）值的作用与可复现性

Seed（随机种子）是扩散模型生成过程中的初始噪声矩阵的种子值。相同的Seed值加上相同的提示词和参数，会产生几乎完全相同的图像。这就是AI绘画中"可复现性"的基础。

扩散模型的工作原理是从一个纯噪声图像开始，通过多步去噪逐步"雕刻"出清晰图像。这个初始噪声是由随机数生成器产生的，而Seed值就是这个随机数生成器的种子。改了Seed，初始噪声就不同了，最终图像也不同。但保持Seed不变，每次生成的图像都是一样的。

Seed的实际用途有三个。第一是结果复现：你生成了一张满意的图，记下Seed值，下次可以用同样的Seed和提示词精确复现。第二是微调对比：固定Seed，只改提示词中的某个词，可以清晰看到这个词对画面的影响。这在调优提示词时非常有用。第三是变异探索：在固定Seed的基础上，微调参数如CFG Scale或采样步数，可以在保持整体构图的前提下探索变体。

```python
# Seed复现与变异的代码示例
import torch
from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

# 使用固定Seed复现图像
seed = 42
generator = torch.Generator(device="cuda").manual_seed(seed)

image_v1 = pipe(
    prompt="a cyberpunk city at night, neon lights, rain wet streets",
    negative_prompt="low quality, blurry",
    num_inference_steps=30,
    guidance_scale=7.5,
    generator=generator
).images[0]

# 保持Seed不变，仅修改提示词中的一个词
# 可以清晰对比"cyberpunk"和"fantasy"风格的差异
generator2 = torch.Generator(device="cuda").manual_seed(seed)
image_v2 = pipe(
    prompt="a fantasy city at night, neon lights, rain wet streets",
    negative_prompt="low quality, blurry",
    num_inference_steps=30,
    guidance_scale=7.5,
    generator=generator2
).images[0]

# 两张图在构图和色彩分布上高度相似
# 但建筑风格和装饰元素会因"cyberpunk"vs"fantasy"而显著不同
```

上面这段代码展示了Seed复现的核心操作。通过`torch.Generator`设置相同的种子，两次生成的图像在构图、色彩分布上会有高度相似性，唯一不同的是提示词中"cyberpunk"和"fantasy"带来的风格差异。这种对比调试方法是怕浪猫最常用的提示词调优技巧。

如果Seed设为-1（随机），每次生成都会使用不同的种子，适合在探索阶段快速浏览不同构图。找到满意的构图后，再固定Seed进行精细调优。这是大多数AI绘画工作流的标准操作。

怕浪猫还要提醒一点：Seed的可复现性是有条件的。必须保证模型版本、采样器类型、采样步数、CFG值、图像尺寸等所有参数完全一致，仅Seed相同并不能保证结果一致。不同版本的模型即使用同样的Seed和提示词，生成的图像也会不同，因为模型权重变了，噪声预测的方向就变了。

> **金句：Seed是提示词调优的"锚点"。没有固定Seed的调参，就像在流沙上建城堡，你永远不知道变化来自提示词还是随机噪声。**

## 2.3 风格关键词速查表

这一节是整章最适合收藏的部分。怕浪猫整理了七大风格分类的核心关键词，每个风格都给出了正向和反向提示词建议。你在写提示词时，可以直接从这里挑选关键词组合使用。

### 摄影写实风格

摄影写实风格的目的是让AI生成的图像看起来像真实照片。核心关键词围绕专业摄影设备、镜头参数和光影描述展开。

正向关键词：photorealistic, realistic photograph, ultra detailed, 8K UHD, shot on Canon EOS R5, 85mm portrait lens, f/1.4 bokeh, natural skin texture, professional photography, studio lighting, golden hour, depth of field, film grain, RAW photo。

反向关键词：illustration, anime, cartoon, painting, drawing, 3D render, CGI, plastic skin, oversaturated, HDR, blurry, deformed。

使用技巧：摄影写实风格对光影描述非常敏感。加上具体的光源方向如"side lighting"（侧光）、"backlighting"（逆光）、"soft diffused lighting"（柔和漫射光）能显著提升真实感。镜头参数如"85mm f/1.4"会模拟出自然景深效果，让人物主体从背景中脱颖而出。怕浪猫发现，加入"film grain"（胶片颗粒）这个关键词能让画面多一层真实的物理质感，减少AI生成的"塑料感"。

### 插画动漫风格

动漫风格是AI绘画中最热门的类别之一，涵盖日系动漫、美式插画等多种子风格。

正向关键词：anime illustration, manga style, cel shading, vibrant colors, clean line art, studio ghibli style, key visual, detailed eyes, expressive face, beautiful composition, official art, pixiv ranking。

反向关键词：photorealistic, realistic, 3D, photo, textured, rough lines, dark theme, deformed。

使用技巧：动漫风格关键词中，"cel shading"（赛璐璐着色）和"clean line art"（干净线稿）是控制画面质感的关键。"studio ghibli style"（吉卜力工作室风格）会生成温暖柔和的画面，而"dark anime"则偏向暗色调。怕浪猫发现，在动漫风格提示词中加入"pixiv ranking"或"trending on artstation"这类"质量标签"，能提升画面的精细度，因为模型在训练数据中将这些标签与高质量作品关联在了一起。

### 油画艺术风格

油画风格让AI模拟传统油画的笔触和质感，适合创作具有艺术气息的肖像和风景。

正向关键词：oil painting, classical art, baroque style, impasto technique, visible brushstrokes, rich textures, canvas texture, renaissance painting, chiaroscuro, dramatic lighting, museum quality, fine art。

反向关键词：photograph, digital art, anime, 3D render, flat colors, smooth texture, modern, cartoon。

使用技巧：油画风格的关键是笔触和质感描述。"impasto"（厚涂法）会产生明显的颜料堆叠效果，"chiaroscuro"（明暗对比法）会强化光影戏剧性。加上具体艺术家参考如"in the style of Rembrandt"或"Van Gogh style"能进一步收窄风格范围，但要注意版权和伦理问题。怕浪猫建议在使用艺术家名字时，选择已进入公有领域的古典艺术家，这样既能获得明确的风格引导，又避免了版权争议。

### 水墨国风风格

水墨国风是具有东方美学的独特风格，模拟中国传统水墨画的意境和技法。

正向关键词：Chinese ink painting, traditional Chinese art, ink wash painting, sumi-e, minimalist brushstrokes, xuan paper texture, monochrome ink, mountain landscape, misty atmosphere, poetic mood, oriental aesthetics, bamboo, crane, pavilion。

反向关键词：photorealistic, 3D render, neon colors, cyberpunk, modern city, cartoon, anime, saturated colors。

使用技巧：水墨风格要克制颜色描述，以"monochrome"（单色）和"ink wash"（水墨渲染）为主。意境词如"misty atmosphere"（雾气弥漫）、"poetic mood"（诗意氛围）对画面情绪的塑造至关重要。怕浪猫建议在提示词中加入"xuan paper texture"（宣纸纹理）来增强传统画材质感。水墨风格的关键词组合要遵循"少即是多"的原则，过多的细节描述反而会破坏水墨画特有的留白意境。

### 设计海报风格

设计海报风格偏向商业设计和平面设计，适合制作封面、宣传图等。

正向关键词：graphic design, poster design, minimalist composition, bold typography, geometric shapes, flat design, vector art, corporate style, clean layout, Swiss design, Bauhaus, vibrant accent colors, white space。

反向关键词：realistic photo, messy, cluttered, hand-drawn sketch, watercolor, oil painting, noisy background。

使用技巧：海报风格强调构图和留白。"Swiss design"（瑞士设计风格）会生成网格化、理性感的布局，"Bauhaus"（包豪斯风格）会带入几何图形和强对比色。怕浪猫在实际项目中，经常用"white space"（留白）来控制画面的呼吸感，避免元素过于拥挤。海报风格中文字描述要特别注意，AI生成文字的能力有限，建议后期用设计软件手动添加文字内容。

### 3D渲染风格

3D渲染风格让AI模拟三维建模软件的渲染效果，常见于产品可视化和角色设计。

正向关键词：3D render, Octane render, Blender, Cinema 4D, subsurface scattering, ray tracing, global illumination, ambient occlusion, PBR materials, volumetric lighting, ultra detailed mesh, ZBrush sculpt, Unreal Engine 5。

反向关键词：flat, 2D, sketch, hand-drawn, anime, watercolor, oil painting, low poly (unless desired)。

使用技巧：3D风格关键词中，渲染器名称如"Octane render"和"Unreal Engine 5"能显著影响画面质感。"subsurface scattering"（次表面散射）会让皮肤和蜡质物体看起来更真实，"ambient occlusion"（环境光遮蔽）能增强角落和缝隙的阴影细节。这些技术术语之所以有效，是因为模型在训练数据中见过大量带有这些标签的3D渲染作品。怕浪猫测试发现，"PBR materials"（基于物理的渲染材质）这个关键词能显著提升物体表面的材质真实感，特别是金属和玻璃质感。

### 像素复古风格

像素风格是一种怀旧美学，模拟早期电子游戏的画面表现。

正向关键词：pixel art, 8-bit, 16-bit, retro game style, sprite art, limited color palette, dithering, isometric view, NES style, SNES style, pixelated, crunchy pixels, game boy palette。

反向关键词：photorealistic, 3D render, smooth gradients, anti-aliased, high resolution, detailed shading, realistic lighting。

使用技巧：像素风格的关键是限制分辨率和颜色数量。"8-bit"和"16-bit"分别对应不同世代的游戏机画面风格。"dithering"（抖动混色）是一个重要的技术关键词，它会让AI模拟早期游戏中用有限色板模拟渐变效果的技法。"limited color palette"能避免AI生成过于平滑的颜色过渡，保持像素画的硬边缘特性。怕浪猫建议在像素风格提示词中加入"isometric view"（等距视角），这是经典像素游戏的常见视角，能立刻唤起复古游戏的感觉。

> **金句：风格关键词不是装饰品，它们是通往模型训练数据中特定视觉子空间的"坐标"。选对关键词，就是选对了参考素材库。**

## 2.4 提示词资源网站

写提示词不需要从零开始。互联网上有大量优质的提示词资源网站，你可以从中学习、借鉴、直接复用优秀提示词。怕浪猫精选了9个最实用的资源网站，按使用场景分类介绍。

### PromptHero

PromptHero（prompthero.com）是目前最全面的AI绘画提示词搜索引擎之一。它收录了Stable Diffusion、Midjourney、DALL-E等多种模型的提示词，支持按模型、风格、主题筛选。每个作品都附带完整的提示词和参数信息，点击即可复制。

使用方法：在搜索框输入你想要的主题关键词，比如"cyberpunk portrait"，然后筛选模型类型。找到满意的作品后，点击详情页查看完整提示词。怕浪猫建议把这个网站作为日常灵感库，遇到好的提示词就收藏起来，逐步建立自己的提示词库。

### Civitai

Civitai（civitai.com）最初是Stable Diffusion模型分享社区，后来发展成集模型、提示词、工作流于一体的综合性平台。它的提示词部分特别适合搭配特定模型使用，因为很多提示词是模型作者亲自测试并推荐的。

Civitai的独特优势在于"模型加提示词加参数"的完整配套。你可以下载某个风格模型，同时获取作者推荐的最佳提示词配置，省去了大量试错时间。网站的Images板块支持按模型、采样器、CFG值等参数精确筛选，非常适合深度学习提示词调优技巧。

### Lexica.art

Lexica.art（lexica.art）是早期Stable Diffusion提示词搜索引擎，界面简洁，检索效率高。它的特点是以图搜图功能：上传一张你喜欢的图片，Lexica会找到视觉风格相似的AI生成作品及其提示词。

这个功能在"逆向工程"别人作品的提示词时特别有用。怕浪猫经常用Lexica来研究优秀作品的提示词结构，分析作者使用了哪些关键词和权重组合。不过要注意，Lexica上的提示词质量参差不齐，需要自己判断筛选。

### OpenArt

OpenArt（openart.ai）支持多种AI模型的提示词搜索，包括Stable Diffusion、Midjourney和DALL-E。它提供了一个"Prompt Book"功能，按主题和风格分类整理了优质提示词合集，适合初学者系统学习。

OpenArt还有一个实用的"提示词生成器"工具：你输入简单的画面描述，它会自动扩展成完整的提示词，补充风格、光影、构图等关键词。对于不熟悉提示词结构的新手来说，这是一个很好的起步工具。

### PromptBase

PromptBase（promptbase.com）是一个提示词交易市场，创作者可以出售自己精心调优的提示词。虽然需要付费，但上面有很多经过深度测试的高质量提示词，适合有明确商业需求的用户。

怕浪猫建议先免费浏览PromptBase的提示词预览，学习其中的关键词组合逻辑。很多付费提示词的核心技巧，你理解了原理之后可以自己复现。付费的价值主要在于节省调试时间。

### Artificialy

Artificialy（artificialy.io）是一个AI艺术画廊和提示词分享平台。它的特色是策展质量高，每件作品都经过人工筛选，保证了提示词的质量水准。网站按风格和主题分类展示，浏览体验很流畅。

### Krea.ai

Krea.ai（krea.ai）不仅提供提示词搜索，还集成了实时生成预览功能。你输入提示词后可以立即看到AI生成的结果，方便快速迭代调试。这种"所见即所得"的体验对学习提示词非常有帮助，因为你修改一个词就能立刻看到画面的变化。

### Visualise.ai

Visualise.ai（visualise.ai）专注于Stable Diffusion提示词，提供了详细的参数信息展示，包括Seed值、采样步数、CFG值、模型版本等。它还有一个"对比模式"，可以同时查看不同参数下同一提示词的生成结果差异，非常适合研究参数对画面的影响。

### PromptPal

PromptPal（promptpal.io）是一个轻量级的提示词辅助工具，提供提示词模板、关键词推荐和语法检查功能。它的关键词推荐引擎会根据你已输入的提示词，智能推荐可能缺失的维度关键词，比如你写了主体和场景但缺少光影描述，它会提示你添加相关关键词。

> **金句：学提示词最快的方法，不是自己闷头试，而是站在高手的肩膀上。先复用，再改编，最后原创，这是任何技能学习的正途。**

## 2.5 参考教程汇总

怕浪猫在学习提示词工程的过程中，整理了一批高质量的教程资源，按类型分类分享给大家。

**官方文档类**

Stable Diffusion官方GitHub仓库的README和Wiki是最权威的技术文档。其中关于CLIP文本编码器、CFG机制和采样器的技术说明，是理解提示词底层原理的必读材料。Hugging Face的Diffusers库文档也提供了大量代码示例和API说明，适合有编程基础的读者。

Midjourney官方文档（docs.midjourney.com）详细说明了其提示词语法，包括参数后缀（如--ar、--v、--style）的使用方法。DALL-E 3的官方指南则重点介绍了自然语言提示词的编写技巧，对理解大语言模型驱动的提示词解析很有帮助。

**视频教程类**

YouTube上值得关注的频道包括：Olivio Sarikas（Stable Diffusion提示词技巧系列）、Sebastian Kamph（AI绘画基础教程）、Mason DIY（Midjourney提示词实战）。这些频道的内容更新及时，覆盖从入门到进阶的全阶段教程。

B站上也有不少优质中文教程。怕浪猫推荐"秋叶aaaki"的Stable Diffusion系列教程，讲解清晰，实操性强。另外"萊萊水"的Midjourney提示词系列也值得一看。

**社区论坛类**

Reddit的r/StableDiffusion和r/midjourney板块是讨论提示词技巧最活跃的英文社区。每天都有大量用户分享自己的提示词和生成结果，遇到问题发帖提问通常能在几小时内得到回复。

中文社区方面，QQ群的"AI绘画交流群"和Discord的中文频道都有不少活跃用户。贴吧的"ai绘画吧"虽然内容质量参差不齐，但偶尔也能挖到有价值的信息。

**论文阅读类**

如果你想知道提示词在模型底层到底发生了什么，以下三篇论文值得阅读。第一篇是"Learning Transferable Visual Models From Natural Language Supervision"（CLIP原论文），它解释了文本和图像如何被编码到同一向量空间。第二篇是"High-Resolution Image Synthesis with Latent Diffusion Models"（LDM，潜在扩散模型原论文），它详细描述了条件信号如何注入去噪过程。第三篇是"Classifier-Free Diffusion Guidance"（CFG原论文），它解释了正向和反向提示词在数学层面的工作机制。

读懂这些论文不需要深厚的数学基础，怕浪猫自己也不是数学专业出身。关键是理解"输入文本到CLIP编码到条件向量到去噪引导"这条链路的整体逻辑，就能在写提示词时做出更准确的判断。

## 本章小结

这一章怕浪猫带你走完了提示词工程的核心知识体系。我们从CLIP模型如何编码文本向量的底层原理出发，建立了五维提示词框架，学习了权重语法和扩写技巧，整理了七大风格关键词速查表，还盘点了9个实用资源网站。

提示词工程的本质，是用自然语言"编程"视觉模型。你写的每一个词，都会经过CLIP编码变成高维向量空间中的一个方向，引导扩散模型从噪声中雕刻出你想要的画面。理解了这个底层逻辑，写提示词就不再是"碰运气"，而是有章可循的工程实践。

如果你觉得这一章对你有帮助，怕浪猫给你几个行动建议。第一，把风格关键词速查表收藏起来，写提示词时随手查阅。第二，选一个资源网站注册账号，每天看10条优质提示词，分析它们的结构和关键词选择。第三，固定一个Seed值，用同一条提示词反复微调，体会每个关键词对画面的具体影响。

> **金句：提示词工程的尽头不是"写出完美提示词"，而是"理解语言如何变成图像"。掌握了这个映射关系，任何模型、任何工具你都能快速上手。**

**下章预告：** 第三章《Midjourney完全指南》，怕浪猫会带你深入Midjourney的参数体系，从--ar到--style raw，从版本差异到风格调优，手把手教你用Midjourney生成商业级作品。关注我，别错过更新。

---

*本章内容到此结束。如果觉得有用，欢迎收藏、点赞、转发。你的支持是怕浪猫持续输出的动力。*

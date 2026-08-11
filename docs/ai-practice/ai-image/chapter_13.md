---
sidebar_position: 13
---

# 第十三章 实战项目合集

我是怕浪猫，一个在AI绘画领域摸爬滚打了上千小时的技术博主。过去几个月我收到最多的一类问题就是：学了这么多原理，到底怎么落地到实际项目里？今天这篇内容，我把五个最热门的商业场景拆开揉碎，从需求分析到工作流设计，从提示词模板到批量脚本，全部给你整理好。

这篇文章的价值不在于教你某个工具怎么用，而在于给你一套可以直接复用的生产级工作流。如果你做过商业项目就知道，真正的难点从来不是出一张图，而是稳定地批量出图、风格一致、质量可控。怕浪猫踩过的坑，你不用再踩一遍。

五个场景，五套工作流，五个可以直接抄作业的提示词模板库。建议先收藏，后面做项目的时候直接拿来用。

## 13.1 电商产品图生成

电商行业对图片的需求量极大，一个单品上架就需要白底主图、场景图、详情页配图等十几种规格。传统拍摄流程包括搭景、打光、拍摄、后期，单款产品的图片成本通常在2000到8000元之间。用AI生成图片可以把这个成本压缩到原来的十分之一，同时把交付周期从一周缩短到几小时。

电商产品图的核心要求是准确性和一致性。准确性指的是产品本身不能变形、颜色不能偏差、文字不能乱码。一致性指的是同一个产品在不同角度、不同场景下的外观特征要保持统一。这两点也是AI生成电商图最大的挑战。

### 13.1.1 需求分析

电商产品图主要分为三类。第一类是白底主图，要求纯白背景、产品居中、光影干净，主要用于商品列表展示。第二类是场景图，把产品放到使用环境中，比如护肤品放在浴室台面上、咖啡机放在厨房台面上。第三类是详情页配图，需要配合文案排版，通常带有氛围感和情感叙事。

白底图的难点在于产品边缘要干净利落，不能有多余的阴影或反光。场景图的难点在于产品要自然融入环境，不能有悬浮感。详情页配图的难点在于整体氛围要统一，多张图放在一起不能有割裂感。针对这三类需求，我设计了统一的工作流来处理。

### 13.1.2 工作流设计

核心工作流分为四个阶段：SD生成基础图、Real-ESRGAN放大、Photoshop精修、批量后处理。每个阶段解决特定问题，串联起来形成完整的生产线。

阶段一，Stable Diffusion生成基础图。这个阶段的关键是选择合适的基底模型和提示词。对于产品图我推荐使用SDXL或其微调版本，因为大模型对产品细节的理解能力更强。同时配合ControlNet的Canny或Depth模式来控制产品轮廓，确保形状不出偏差。

阶段二，Real-ESRGAN放大。SD生成的图片默认分辨率通常是1024x1024，电商主图需要800x800或更大的尺寸。直接用SD高分辨率重绘会增加大量计算时间，而Real-ESRGAN（Real Enhanced Super-Resolution Generative Adversarial Network，真实增强超分辨率生成对抗网络）可以在几秒内把图片放大到4倍，同时恢复细节纹理。

阶段三，Photoshop精修。AI生成的图片通常需要人工微调，比如修掉多余的反光、调整产品颜色使其与实物一致、清理背景中的瑕疵。这一步不能省略，因为目前AI还无法完全理解产品颜色的精确要求。

阶段四，批量后处理。用Python脚本批量裁剪、添加水印、调整尺寸，输出符合各平台要求的图片规格。这个阶段用PIL和OpenCV处理即可。

工作流程图如下：

```
[输入: 产品参考图 + 需求描述]
        |
        v
[SDXL + ControlNet(Canny)] --> 生成基础图(1024x1024)
        |
        v
[Real-ESRGAN 4x放大] --> 高分辨率图(4096x4096)
        |
        v
[Photoshop精修] --> 颜色校正 + 瑕疵修复 + 边缘清理
        |
        v
[Python批量后处理] --> 裁剪 + 水印 + 多尺寸输出
        |
        v
[输出: 白底主图 / 场景图 / 详情页配图]
```

### 13.1.3 完整提示词模板

下面是怕浪猫经过上百次测试总结出来的电商产品图提示词模板。模板采用参数化设计，你只需要替换方括号中的内容即可。

白底主图提示词模板：

```
正向提示词：
professional product photography, [PRODUCT_NAME], clean white background,
studio lighting, soft shadow, centered composition, high detail,
sharp focus, commercial quality, 8k uhd, dslr, 50mm lens,
f/8 aperture, color accurate

反向提示词：
blurry, low quality, distorted, watermark, text, logo,
busy background, colored background, multiple objects,
overexposed, underexposed, noise, grain

参数设置：
Steps: 30
CFG Scale: 7
Sampler: DPM++ 2M Karras
Seed: -1 (首次生成后固定种子以保持一致性)
Size: 1024x1024
Denoising: 0.85
```

场景图提示词模板：

```
正向提示词：
professional product photography, [PRODUCT_NAME] placed on [SCENE_SURFACE],
[SCENE_DESCRIPTION], natural window light, warm atmosphere,
shallow depth of field, bokeh background, lifestyle photography,
magazine quality, 8k uhd, dslr, 35mm lens, f/2.8 aperture

反向提示词：
blurry, low quality, distorted product, watermark, text,
unnatural lighting, floating object, wrong perspective,
cluttered scene, oversaturated, plastic look

参数设置：
Steps: 30
CFG Scale: 6.5
Sampler: DPM++ 2M Karras
Size: 1024x1024
ControlNet: Depth (weight 0.6)
```

详情页配图提示词模板：

```
正向提示词：
[PRODUCT_NAME] in [SCENE_DESCRIPTION], cinematic lighting,
dramatic atmosphere, warm color palette, editorial photography,
luxury feel, soft glow, particles in air, shallow depth of field,
8k uhd, highly detailed, professional color grading

反向提示词：
flat lighting, boring composition, low contrast, noisy,
watermark, text overlay, distorted product, unnatural colors

参数设置：
Steps: 35
CFG Scale: 7
Sampler: DPM++ SDE Karras
Size: 1024x1024
ControlNet: Depth (weight 0.5) + Canny (weight 0.3)
```

提示词的设计逻辑是这样的。白底图强调studio lighting和clean white background，用50mm镜头和f/8光圈确保整个产品都在景深范围内。场景图加入35mm镜头和f/2.8光圈制造浅景深，让产品从背景中突出。详情页配图用cinematic lighting和dramatic atmosphere营造氛围感，配合更高的Steps数和SDE采样器获得更细腻的画面。

### 13.1.4 批量生成脚本

当需要为几十个产品批量生成图片时，手动操作效率太低。下面是怕浪猫写的批量生成脚本，通过Stable Diffusion WebUI的API接口实现自动化调用。

```python
import requests
import json
import base64
import os
from pathlib import Path

class SDBatchGenerator:
    """SD批量生成器，通过WebUI API调用"""
    
    def __init__(self, api_url="http://127.0.0.1:7860"):
        self.api_url = api_url
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_white_bg(self, product_name, seed=-1):
        """生成白底主图"""
        payload = {
            "prompt": f"professional product photography, {product_name}, "
                      f"clean white background, studio lighting, soft shadow, "
                      f"centered composition, high detail, sharp focus, "
                      f"commercial quality, 8k uhd, dslr, 50mm lens, f/8 aperture",
            "negative_prompt": "blurry, low quality, distorted, watermark, "
                               "text, logo, busy background, colored background, "
                               "multiple objects, overexposed, underexposed",
            "steps": 30,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras",
            "seed": seed,
            "width": 1024,
            "height": 1024,
            "denoising_strength": 0.85
        }
        return self._call_api(payload, f"white_bg_{product_name}")
    
    def generate_scene(self, product_name, scene_desc, seed=-1):
        """生成场景图"""
        payload = {
            "prompt": f"professional product photography, {product_name} "
                      f"placed on natural surface, {scene_desc}, "
                      f"natural window light, warm atmosphere, "
                      f"shallow depth of field, bokeh background, "
                      f"lifestyle photography, 8k uhd, dslr, 35mm lens",
            "negative_prompt": "blurry, low quality, distorted product, "
                               "watermark, text, unnatural lighting, "
                               "floating object, wrong perspective",
            "steps": 30,
            "cfg_scale": 6.5,
            "sampler_name": "DPM++ 2M Karras",
            "seed": seed,
            "width": 1024,
            "height": 1024
        }
        return self._call_api(payload, f"scene_{product_name}")
    
    def _call_api(self, payload, filename):
        """调用SD WebUI API"""
        response = requests.post(
            f"{self.api_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=300
        )
        result = response.json()
        
        # 保存图片
        img_data = base64.b64decode(result["images"][0])
        img_path = self.output_dir / f"{filename}.png"
        with open(img_path, "wb") as f:
            f.write(img_data)
        
        # 返回种子值用于复现
        return {
            "filename": str(img_path),
            "seed": result.get("seed", -1),
            "info": json.loads(result.get("info", "{}"))
        }
    
    def batch_generate(self, product_list):
        """批量生成"""
        results = []
        for product in product_list:
            print(f"正在生成: {product['name']}")
            
            # 生成白底图
            r1 = self.generate_white_bg(product["name"], product.get("seed", -1))
            results.append({"type": "white_bg", **r1})
            
            # 生成场景图
            if "scene" in product:
                r2 = self.generate_scene(product["name"], product["scene"])
                results.append({"type": "scene", **r2})
            
            print(f"完成: {product['name']}")
        
        return results


# 使用示例
if __name__ == "__main__":
    generator = SDBatchGenerator(api_url="http://127.0.0.1:7860")
    
    products = [
        {"name": "skincare bottle", "scene": "bathroom vanity with marble countertop"},
        {"name": "coffee mug", "scene": "wooden desk with books and plants"},
        {"name": "wireless earbuds", "scene": "modern office desk with laptop"},
    ]
    
    results = generator.batch_generate(products)
    print(f"\n批量生成完成，共 {len(results)} 张图片")
    for r in results:
        print(f"  [{r['type']}] {r['filename']} (seed: {r['seed']})")
```

脚本的核心逻辑是封装SD WebUI的API调用，把提示词模板参数化。每个产品的种子值默认设为-1（随机），首次生成后你可以把返回的种子值固定下来，确保后续生成的同一产品风格一致。批量模式遍历产品列表，依次生成白底图和场景图，自动保存到output目录。

> 一张好图的价值不在于它多好看，而在于它能不能稳定地被复制一百次。

## 13.2 社交媒体配图

社交媒体配图是另一个高频需求场景。不同平台对图片尺寸、风格、信息密度的要求差异很大。同一篇内容发到小红书、微信公众号、朋友圈，需要三种完全不同的配图策略。

小红书的用户以年轻女性为主，平台偏好高饱和度、精致感强的封面图。微信公众号头图需要在大图模式下吸引点击，又要在小图模式下保持辨识度。朋友圈海报则要求信息层级清晰，一屏之内传达核心卖点。

### 13.2.1 各平台尺寸规范

在开始设计之前，先明确各平台的图片尺寸要求。这个表是怕浪猫实测整理的，部分尺寸会随平台更新有所调整，建议每季度核对一次。

```
┌────────────────┬──────────────────┬──────────────────┬───────────────┐
│ 平台           │ 推荐尺寸          │ 最小尺寸         │ 格式          │
├────────────────┼──────────────────┼──────────────────┼───────────────┤
│ 小红书封面     │ 1080 x 1440 (3:4)│ 750 x 1000      │ JPG/PNG       │
│ 小红书配图     │ 1080 x 1080 (1:1)│ 750 x 750        │ JPG/PNG       │
│ 公众号头图     │ 900 x 383 (2.35:1)│ 900 x 383       │ JPG           │
│ 朋友圈海报     │ 1080 x 1920 (9:16)│ 750 x 1334      │ JPG/PNG       │
│ 抖音封面       │ 1080 x 1920 (9:16)│ 720 x 1280      │ JPG           │
│ 微博配图       │ 1080 x 1080 (1:1)│ 600 x 600        │ JPG/PNG       │
│ 知乎配图       │ 1080 x 1920 (9:16)│ 720 x 1280      │ JPG/PNG       │
└────────────────┴──────────────────┴──────────────────┴───────────────┘
```

尺寸规范的核心逻辑在于适配不同终端的展示场景。小红书采用3:4竖图是因为移动端瀑布流中竖图的视觉占屏面积更大，点击率比横图高出约40%。公众号头图用2.35:1的宽幅是因为在消息列表中横向展示空间有限，宽幅图能在小尺寸下保持视觉冲击力。朋友圈海报用9:16全屏比例是为了适配手机竖屏的沉浸式体验。

### 13.2.2 小红书封面设计

小红书封面的设计要点是：标题醒目、主体突出、色彩鲜艳。封面图是用户滑过信息流时第一眼看到的内容，0.3秒内就要抓住注意力。

用AI生成小红书封面有两种策略。第一种是直接生成带文字的封面，使用SDXL配合文字渲染LoRA。第二种是生成纯背景图，再用Canva或Photoshop叠加文字。我推荐第二种策略，因为AI生成的文字经常出现错别字，而用设计工具加文字可以精确控制字体、大小和位置。

小红书封面背景图提示词模板：

```
正向提示词：
vibrant gradient background, [THEME] aesthetic, soft pastel colors,
clean minimal composition, top area blank for title text,
decorative elements in corners, sparkle effect, dreamy atmosphere,
high saturation, social media cover style, 8k uhd

反向提示词：
text, words, letters, watermark, logo, blurry, low quality,
dark, gloomy, messy composition, too many details

参数设置：
Steps: 25
CFG Scale: 6
Sampler: Euler a
Size: 1080x1440
```

提示词中top area blank for title text是关键指令，它引导模型在画面上方留出空白区域供后期叠加标题。同时反向提示词中加入text、words、letters来抑制AI生成无意义的文字。

### 13.2.3 微信公众号头图

公众号头图的设计逻辑和小红书完全不同。头图在消息列表中只显示一个缩略图，所以画面要有一个明确的视觉焦点，不能太复杂。配色方面建议用品牌色系，增强辨识度。

公众号头图提示词模板：

```
正向提示词：
[TOPIC] themed illustration, wide banner composition,
centered focal point, brand color palette,
clean background, minimal style, editorial illustration,
flat design elements, professional, 8k uhd

反向提示词：
text, watermark, busy background, multiple focal points,
realistic photo, 3d render, cluttered, dark tones

参数设置：
Steps: 25
CFG Scale: 7
Sampler: DPM++ 2M Karras
Size: 1024x448 (生成后裁剪到900x383)
```

### 13.2.4 朋友圈海报

朋友圈海报的核心是信息层级。一张海报通常包含主标题、副标题、产品图、行动号召语四个信息层。AI生成的部分主要是背景和氛围元素，文字部分同样建议后期叠加。

朋友圈海报提示词模板：

```
正向提示词：
vertical poster background, [THEME] theme, elegant gradient,
top 30% area for main title, center area for product image,
bottom area for call to action text, decorative light effects,
premium feel, luxury brand aesthetic, 8k uhd

反向提示词：
text, words, busy details, low quality, blurry,
horizontal layout, landscape orientation

参数设置：
Steps: 30
CFG Scale: 7
Sampler: DPM++ 2M Karras
Size: 1080x1920
```

> 配图的终极目标不是好看，而是让用户在滑动屏幕的瞬间停下来。

## 13.3 IP形象设计

IP（Intellectual Property，知识产权）形象设计是AI绘画最具商业价值的场景之一。一个成功的IP形象可以衍生出表情包、周边产品、品牌联名等多种变现路径。传统IP设计从概念草图到成图需要一到两周，用AI可以把这个周期压缩到一到两天。

IP形象设计的核心挑战是角色一致性。同一个角色在不同表情、不同动作、不同场景下必须保持可识别的特征。Stable Diffusion本身无法保证这一点，但通过LoRA（Low-Rank Adaptation，低秩适配）训练和ControlNet组合使用可以解决。

### 13.3.1 从概念到成图

IP形象设计的完整工作流分为五个阶段：概念定义、数据集准备、LoRA训练、姿态控制、成图精修。

阶段一，概念定义。在动手之前，先用文字描述清楚角色的核心特征。包括性别、年龄段、发型、发色、瞳色、服装风格、性格气质等。这份描述既是训练数据的筛选标准，也是后续生成提示词的基础。

阶段二，数据集准备。收集20到50张符合概念定义的角色图片，分辨率不低于512x512。图片角度要多样，包括正面、侧面、半侧面。表情要丰富，包括微笑、严肃、惊讶等。背景尽量简洁，避免复杂场景干扰角色特征学习。

阶段三，LoRA训练。用Kohya_ss或LoRA Easy Train脚本训练专属角色模型。关键参数包括：训练分辨率512x512、batch size 4、learning rate 1e-4、网络维度16到32。训练步数通常控制在1500到3000步之间，过多会导致过拟合。

阶段四，姿态控制。用ControlNet的OpenPose模块控制角色姿态，结合LoRA确保角色面部特征一致。OpenPose（Open Pose Estimation，开放姿态估计）通过骨骼关键点定义人物动作，可以让角色摆出任意指定姿势。

阶段五，成图精修。对生成的图片进行面部一致性检查、细节修复、背景替换等后期处理。

```
IP形象设计工作流：

[概念定义] --> 文字描述角色特征
     |
     v
[数据集准备] --> 20-50张多角度参考图
     |
     v
[LoRA训练] --> Kohya_ss, 2000步, lr=1e-4, dim=16
     |
     v
[ControlNet姿态控制] --> OpenPose骨骼定义
     |
     v
[成图生成] --> LoRA权重0.7-0.9 + ControlNet权重0.6
     |
     v
[后期精修] --> 面部修复 + 背景处理 + 尺寸输出
```

### 13.3.2 角色一致性保持

LoRA训练完成后，使用时的权重设置至关重要。权重过低（低于0.4）角色特征不明显，权重过高（高于1.0）会出现过拟合导致的画面崩坏。怕浪猫经过大量测试，推荐权重范围在0.7到0.9之间。

除了LoRA权重，还有几个技巧可以增强一致性。第一，固定种子值。同一个角色在不同场景下使用相同种子值，可以让面部基础结构保持稳定。第二，使用提示词中的character sheet或multiple views来生成多角度参考图。第三，配合ControlNet的Tile模块做图生图重绘，在保持角色特征的同时改变背景和动作。

角色一致性生成提示词模板：

```
正向提示词：
[CHARACTER_NAME], [HAIR_STYLE] [HAIR_COLOR] hair, [EYE_COLOR] eyes,
[CLOTHING_DESCRIPTION], [POSE_DESCRIPTION], [EXPRESSION],
[BACKGROUND_DESCRIPTION], masterpiece, best quality,
highly detailed face, consistent character design

<lora:[LORA_NAME]:0.85>

反向提示词：
inconsistent features, different character, deformed face,
extra fingers, bad anatomy, low quality, blurry, watermark

参数设置：
Steps: 30
CFG Scale: 7
Sampler: DPM++ 2M Karras
Size: 768x1024
ControlNet: OpenPose (weight 0.6)
LoRA: [LORA_NAME] (weight 0.85)
```

### 13.3.3 表情包制作工作流

表情包是IP形象最常见的衍生产品。一套完整的表情包通常包含24个常用表情，覆盖开心、生气、惊讶、难过、无语、得意等情绪。

表情包制作的核心要求是表情夸张、背景统一、尺寸一致。工作流如下：首先用SDXL生成基础表情图，配合LoRA保持角色一致性。然后用ControlNet的OpenPose控制头部角度统一为正面。最后用Python脚本批量裁剪为正方形、去除背景、添加文字。

```python
from PIL import Image, ImageDraw, ImageFont
import os
from rembg import remove

class StickerMaker:
    """表情包批量制作工具"""
    
    def __init__(self, input_dir="raw_stickers", output_dir="stickers"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.sticker_size = 512
        self.texts = {
            "happy": "开心",
            "angry": "生气",
            "surprised": "惊讶",
            "sad": "难过",
            "speechless": "无语",
            "proud": "得意",
        }
    
    def remove_background(self, image_path):
        """去除背景"""
        with open(image_path, "rb") as f:
            input_image = f.read()
        output_image = remove(input_image)
        return Image.open(io.BytesIO(output_image))
    
    def add_text(self, image, text):
        """在底部添加文字"""
        draw = ImageDraw.Draw(image)
        font_size = 36
        try:
            font = ImageFont.truetype("msyh.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        # 文字位置
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (self.sticker_size - text_w) // 2
        y = self.sticker_size - text_h - 20
        
        # 白色描边
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)]:
            draw.text((x+dx, y+dy), text, fill="white", font=font)
        draw.text((x, y), text, fill="black", font=font)
        return image
    
    def process_sticker(self, image_path, emotion_key):
        """处理单个表情"""
        # 去背景
        img = self.remove_background(image_path)
        
        # 裁剪为正方形
        img = img.resize((self.sticker_size, self.sticker_size))
        
        # 添加文字
        if emotion_key in self.texts:
            img = self.add_text(img, self.texts[emotion_key])
        
        # 保存
        output_path = os.path.join(
            self.output_dir, 
            f"sticker_{emotion_key}.png"
        )
        img.save(output_path, "PNG")
        return output_path
    
    def batch_process(self):
        """批量处理"""
        results = []
        for filename in os.listdir(self.input_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            emotion_key = os.path.splitext(filename)[0].split('_')[-1]
            input_path = os.path.join(self.input_dir, filename)
            output_path = self.process_sticker(input_path, emotion_key)
            results.append(output_path)
            print(f"已处理: {filename} -> {output_path}")
        return results
```

> IP设计的本质不是画一个好看的角色，而是创造一个能被记住的角色。

## 13.4 建筑效果图

建筑效果图是建筑设计行业中不可或缺的环节。传统建筑效果图依赖3D建模软件如SketchUp、3ds Max渲染，流程长、门槛高。AI生成建筑效果图可以在设计初期快速提供视觉参考，帮助设计师和客户对齐方向。

建筑效果图分为室内和室外两类。室外效果图关注建筑体量、材质、环境关系。室内效果图关注空间布局、家具搭配、光影氛围。两类效果图在ControlNet模块选择和提示词策略上有明显差异。

### 13.4.1 ControlNet MLSD线稿控制

建筑效果图最常用的ControlNet模块是MLSD（Mobile Line Segment Detection，移动线段检测）。MLSD专门用于检测图像中的直线段，非常适合建筑线条稿的提取和控制。与Canny边缘检测不同，MLSD会忽略纹理细节，只保留建筑结构线条，这正好符合建筑效果图的需求。

使用流程是：先用AutoCAD或SketchUp导出建筑线稿图，然后把线稿图输入ControlNet的MLSD模块作为控制条件，配合建筑风格提示词生成效果图。

MLSD的权重设置很关键。权重在0.5到0.7之间时，模型在遵循线稿结构的同时有适度的自由发挥空间。权重低于0.4时结构控制力不足，建筑可能变形。权重高于0.8时画面过于僵硬，缺乏真实感。

建筑效果图生成提示词模板：

```
正向提示词：
architectural photography, [BUILDING_TYPE] exterior,
modern glass facade, concrete and steel structure,
[TIME_OF_DAY] lighting, [WEATHER_CONDITION],
surrounding landscape with trees and walkway,
realistic materials, professional architectural render,
8k uhd, octane render, volumetric light

反向提示词：
distorted lines, curved walls, asymmetric windows,
low quality, blurry, cartoon style, anime style,
watermark, text, people looking at camera

参数设置：
Steps: 35
CFG Scale: 7
Sampler: DPM++ 2M Karras
Size: 1024x768
ControlNet: MLSD (weight 0.6, threshold 0.1)
```

### 13.4.2 风格LoRA叠加

建筑效果图常需要表达不同的建筑风格，比如现代极简、新中式、地中海风等。通过训练或下载风格LoRA可以快速切换建筑风格。

风格叠加的技巧在于权重平衡。基底模型提供基础的建筑理解，LoRA注入风格特征。当同时使用多个LoRA时，比如一个建筑风格LoRA加一个材质质感LoRA，建议总权重不超过1.2，单个LoRA权重在0.4到0.7之间。

```
# 风格LoRA叠加示例提示词
正向提示词：
architectural photography, modern villa exterior,
glass and wood facade, minimalist design,
sunset golden hour lighting, garden with swimming pool,
realistic materials, professional render, 8k uhd

<lora:modern_arch_style:0.6>
<lora:realistic_materials:0.4>

参数设置：
Steps: 35
CFG Scale: 7
Sampler: DPM++ 2M Karras
ControlNet: MLSD (weight 0.6)
```

### 13.4.3 室内外场景切换

同一个建筑线稿可以通过修改提示词在室内外之间切换。室外效果图强调建筑外观、环境关系、天光效果。室内效果图强调空间纵深、家具陈设、人工光源。

室内效果图提示词模板：

```
正向提示词：
interior architectural photography, [ROOM_TYPE],
[STYLE] interior design, natural light from large windows,
[COLOR_SCHEME] color palette, furniture and decor,
wooden floor, plants, cozy atmosphere,
professional interior render, 8k uhd, volumetric light

反向提示词：
distorted perspective, curved walls, floating furniture,
low quality, blurry, exterior view, outdoor scene,
watermark, text

参数设置：
Steps: 35
CFG Scale: 7
Sampler: DPM++ SDE Karras
Size: 768x1024
ControlNet: MLSD (weight 0.5) + Depth (weight 0.3)
```

室内效果图同时使用MLSD和Depth两个ControlNet模块。MLSD控制墙壁和家具的直线结构，Depth控制空间纵深透视。两个模块的权重都适度降低，避免画面过于僵硬。采样器换成DPM++ SDE Karras，因为SDE（Stochastic Differential Equation，随机微分方程）版本在室内细节渲染上表现更好。

> 好的建筑效果图不是画出来的，是控制出来的。线稿定义骨架，提示词注入灵魂。

## 13.5 游戏2D素材

游戏开发对2D素材的需求量巨大，一个中等规模的手机游戏可能需要上千张2D资源。包括角色立绘、UI（User Interface，用户界面）图标、背景图、道具图标等。AI生成可以大幅降低美术成本，特别适合独立游戏团队和原型开发阶段。

游戏2D素材的特殊要求是风格统一性和透明背景。角色立绘需要统一的画风和色彩体系。UI图标需要透明背景和一致的视觉语言。背景图需要匹配游戏的场景设计文档。

### 13.5.1 角色立绘

游戏角色立绘分为半身像和全身像两种。AI生成立绘的关键是在不同角色之间保持画风统一。解决方案是训练一个画风LoRA，把目标画风特征固化到模型中。

训练画风LoRA的数据集要求和角色LoRA不同。角色LoRA关注个体特征，数据集是同一个角色的多角度图片。画风LoRA关注绘画风格，数据集是同一画风的不同角色和场景图片，通常需要50到100张。

立绘生成提示词模板：

```
正向提示词：
game character full body illustration, [CHARACTER_DESCRIPTION],
[OUTFIT_DESCRIPTION], [POSE], [EXPRESSION],
dynamic lighting, clean background, character design sheet,
full body visible, game art style, masterpiece, best quality

<lora:game_art_style:0.7>

反向提示词：
multiple characters, cropped, cut off, blurry, low quality,
realistic photo, 3d render, watermark, text, complex background

参数设置：
Steps: 30
CFG Scale: 7
Sampler: DPM++ 2M Karras
Size: 768x1024
LoRA: game_art_style (weight 0.7)
```

### 13.5.2 UI图标

游戏UI图标包括道具图标、技能图标、货币图标等。这类素材的特点是尺寸小、风格统一、背景透明。用AI生成UI图标需要配合批量去背景和尺寸标准化处理。

UI图标生成提示词模板：

```
正向提示词：
game icon, [ITEM_NAME], [ART_STYLE] style,
centered, simple background, bright colors,
clean edges, high contrast, icon design,
game UI element, 512x512

反向提示词：
complex background, multiple objects, text, watermark,
realistic photo, blurry, low quality, dark

参数设置：
Steps: 25
CFG Scale: 8
Sampler: Euler a
Size: 512x512
```

CFG Scale设置为8比常规的7略高，因为图标需要更强的风格化和色彩饱和度。Euler a采样器在简单构图的小尺寸图片上效果更好且速度更快。

### 13.5.3 像素风格LoRA

像素风格是独立游戏中非常受欢迎的美术风格。Pixel Art LoRA可以把SD生成的图片转换为像素画风格，配合不同的提示词可以控制像素颗粒度。

像素风格素材生成提示词模板：

```
正向提示词：
pixel art, [SCENE_DESCRIPTION], 16-bit style,
retro game graphics, limited color palette,
pixelated, sprite sheet, game asset

<lora:pixel_art_style:0.8>

反向提示词：
smooth, realistic, high resolution, anti-aliased,
3d render, photo, blurry, watermark

参数设置：
Steps: 20
CFG Scale: 7.5
Sampler: Euler a
Size: 512x512
LoRA: pixel_art_style (weight 0.8)
```

反向提示词中的smooth和anti-aliased是关键。像素画的核心特征就是锯齿边缘和有限色板，必须阻止模型去做抗锯齿和平滑处理。

### 13.5.4 批量素材生成

下面是怕浪猫写的游戏素材批量生成脚本。脚本支持角色立绘、UI图标、背景图三种类型的批量生成，并自动进行去背景和尺寸标准化处理。

```python
import requests
import base64
import json
import os
from pathlib import Path
from io import BytesIO
from PIL import Image
from rembg import remove

class GameAssetGenerator:
    """游戏素材批量生成器"""
    
    def __init__(self, api_url="http://127.0.0.1:7860"):
        self.api_url = api_url
        self.asset_types = {
            "character": {
                "size": (768, 1024),
                "steps": 30,
                "cfg": 7,
                "sampler": "DPM++ 2M Karras",
                "lora": "game_art_style:0.7"
            },
            "icon": {
                "size": (512, 512),
                "steps": 25,
                "cfg": 8,
                "sampler": "Euler a",
                "lora": None
            },
            "background": {
                "size": (1024, 576),
                "steps": 35,
                "cfg": 7,
                "sampler": "DPM++ 2M Karras",
                "lora": "game_art_style:0.5"
            },
            "pixel": {
                "size": (512, 512),
                "steps": 20,
                "cfg": 7.5,
                "sampler": "Euler a",
                "lora": "pixel_art_style:0.8"
            }
        }
    
    def generate(self, asset_type, prompt, negative_prompt, 
                 output_path, seed=-1):
        """生成单个素材"""
        config = self.asset_types[asset_type]
        
        # 构建完整提示词
        full_prompt = prompt
        if config["lora"]:
            full_prompt += f"\n<lora:{config['lora']}>"
        
        payload = {
            "prompt": full_prompt,
            "negative_prompt": negative_prompt,
            "steps": config["steps"],
            "cfg_scale": config["cfg"],
            "sampler_name": config["sampler"],
            "width": config["size"][0],
            "height": config["size"][1],
            "seed": seed
        }
        
        # 调用API
        response = requests.post(
            f"{self.api_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=300
        )
        result = response.json()
        
        # 保存原图
        img_data = base64.b64decode(result["images"][0])
        img = Image.open(BytesIO(img_data))
        
        # 去背景（图标和角色需要）
        if asset_type in ["icon", "character"]:
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_no_bg = remove(img_byte_arr.getvalue())
            img = Image.open(BytesIO(img_no_bg))
        
        # 尺寸标准化
        if asset_type == "icon":
            img = img.resize((128, 128), Image.NEAREST)
        
        img.save(output_path, "PNG")
        return {
            "path": output_path,
            "seed": result.get("seed", -1),
            "size": img.size
        }
    
    def batch_from_csv(self, csv_path, output_dir="game_assets"):
        """从CSV文件批量生成
        
        CSV格式: asset_type, name, prompt, negative_prompt
        """
        import csv
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset_type = row['asset_type']
                name = row['name']
                prompt = row['prompt']
                neg = row.get('negative_prompt', 
                    'blurry, low quality, watermark, text')
                
                output_path = os.path.join(
                    output_dir, 
                    f"{asset_type}_{name}.png"
                )
                
                print(f"生成中: {asset_type}/{name}")
                result = self.generate(
                    asset_type, prompt, neg, output_path
                )
                results.append({
                    "type": asset_type,
                    "name": name,
                    **result
                })
                print(f"完成: {output_path}")
        
        # 生成清单文件
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results


# 使用示例
if __name__ == "__main__":
    generator = GameAssetGenerator()
    
    # 单个生成
    result = generator.generate(
        asset_type="icon",
        prompt="game icon, health potion, red liquid in glass vial, "
               "bright colors, centered, clean background",
        negative_prompt="complex background, text, blurry",
        output_path="game_assets/icon_health_potion.png"
    )
    print(f"生成完成: {result}")
```

脚本的设计思路是配置驱动。每种素材类型有独立的参数配置，包括尺寸、步数、CFG值、采样器和LoRA。CSV驱动的批量模式让策划人员可以维护一个Excel表格列出所有需要的素材，然后一键生成。生成的manifest.json记录每张图的种子值，方便后续复现或调整。

这里补充一个实际项目中的经验教训。怕浪猫在接一个游戏外包项目时，最初尝试用同一个种子值生成所有角色立绘，结果发现角色之间的面部特征差异太小，看起来像同一个人的不同装扮。后来调整为每个角色使用不同的种子值，但固定画风LoRA权重，才解决了这个问题。另一个坑是去背景的处理。rembg库对复杂边缘（比如头发丝、透明材质）的处理效果不理想，遇到这类素材建议用Photoshop的选区工具手动处理，或者在生成时就用纯色背景便于后期抠图。

> 游戏开发的瓶颈从来不是技术，是美术产能。AI不是替代美术，是把美术从重复劳动中解放出来。

## 工作流速查表

最后，怕浪猫把本章五个场景的核心工作流整理成一张速查表，方便你快速查阅。

```
┌──────────────────┬──────────────────┬───────────────┬─────────────────┬───────────────┐
│ 场景             │ 核心工具          │ ControlNet    │ LoRA            │ 关键参数       │
├──────────────────┼──────────────────┼───────────────┼─────────────────┼───────────────┤
│ 电商白底图       │ SDXL             │ Canny(0.6)    │ -               │ CFG7, 30步    │
│ 电商场景图       │ SDXL             │ Depth(0.6)    │ -               │ CFG6.5, 30步  │
│ 电商详情页       │ SDXL             │ Depth+Canny   │ -               │ CFG7, 35步    │
│ 小红书封面       │ SDXL             │ -             │ -               │ CFG6, 25步    │
│ 公众号头图       │ SDXL             │ -             │ -               │ CFG7, 25步    │
│ 朋友圈海报       │ SDXL             │ -             │ -               │ CFG7, 30步    │
│ IP形象设计       │ SD1.5/SDXL       │ OpenPose(0.6) │ 角色LoRA(0.85)  │ CFG7, 30步    │
│ 表情包           │ SDXL             │ OpenPose(0.6) │ 角色LoRA(0.85)  │ CFG7, 30步    │
│ 建筑室外图       │ SDXL             │ MLSD(0.6)     │ 风格LoRA(0.6)   │ CFG7, 35步    │
│ 建筑室内图       │ SDXL             │ MLSD+Depth    │ 风格LoRA(0.6)   │ CFG7, 35步    │
│ 游戏角色立绘     │ SD1.5/SDXL       │ -             │ 画风LoRA(0.7)   │ CFG7, 30步    │
│ 游戏UI图标       │ SD1.5            │ -             │ -               │ CFG8, 25步    │
│ 游戏像素素材     │ SD1.5            │ -             │ 像素LoRA(0.8)   │ CFG7.5, 20步  │
└──────────────────┴──────────────────┴───────────────┴─────────────────┴───────────────┘
```

## 五大场景Prompt模板库速览

为了方便收藏和复用，这里把五个场景的核心提示词压缩成一行模板格式：

```
[电商白底图] professional product photography, {产品名}, clean white background, studio lighting, 50mm, f/8
[电商场景图] professional product photography, {产品名} on {场景}, natural light, 35mm, f/2.8, bokeh
[小红书封面] vibrant gradient background, {主题} aesthetic, pastel colors, top blank for text
[公众号头图] {主题} themed illustration, wide banner, centered focal point, brand colors, minimal
[朋友圈海报] vertical poster background, {主题}, elegant gradient, top for title, center for product
[IP角色] {角色名}, {发型发色}, {瞳色} eyes, {服装}, {姿势}, {表情}, <lora:{角色LoRA}:0.85>
[建筑室外] architectural photography, {建筑类型}, glass facade, {时间} lighting, MLSD control
[建筑室内] interior photography, {房间类型}, {风格} design, natural light, MLSD+Depth control
[游戏立绘] game character full body, {角色描述}, {服装}, {姿势}, <lora:{画风LoRA}:0.7>
[游戏图标] game icon, {物品名}, {风格} style, centered, clean background, 512x512
[像素素材] pixel art, {场景描述}, 16-bit style, retro game, <lora:pixel_art:0.8>
```

## 总结与预告

这篇文章覆盖了五个实战场景的完整工作流：电商产品图、社交媒体配图、IP形象设计、建筑效果图、游戏2D素材。每个场景都包含需求分析、工作流设计、提示词模板和批量脚本。

核心方法论其实只有一个：把AI生成当作生产线来设计，而不是当作抽卡机器来碰运气。控制输入（ControlNet+LoRA+提示词），标准化输出（批量脚本+后处理），每一步都可复现、可调整、可扩展。

如果你觉得这些内容对你有帮助，建议收藏这篇文章。后面做项目的时候直接翻到对应的场景章节，抄提示词模板，改参数，跑脚本，省下来的时间可以去干更有创造力的事情。

怕浪猫再啰嗦一句关于实际落地的建议。很多读者学了这些技术之后，一上来就想做全套自动化流水线，结果卡在环境配置和接口调试上浪费了好几天。正确的做法是先跑通单张图片的手动流程，确认提示词和参数都没问题，然后再逐步脚本化。每个场景的提示词模板都建议先用WebUI界面手动调试十到二十张，找到最稳定的参数组合后再写批量脚本。这样能避免脚本跑了一晚上，第二天发现几百张图全部废掉的惨剧。

下一篇是第十四章，也是本书的附录部分。我会整理AI绘画领域的常用术语表、推荐模型清单、学习资源汇总，以及一个完整的参数调优决策树。附录的存在就是为了让你在遇到问题时能快速查到答案，相当于一本AI绘画的案头手册。

怕浪猫写到这里，整本书的正文部分就全部完成了。如果你从第一章跟到现在，恭喜你已经具备了AI绘画从原理到实战的完整知识体系。我们下篇见。

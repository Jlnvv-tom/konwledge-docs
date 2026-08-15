# 人工智能与机器学习课程——从传统方法到大模型

AI方向博士生必修课从5门涨到了12门，但核心其实就3条线：数学、架构、训练。

我是怕浪猫，一个在AI课海里找到主线的人。今天这篇文章，我把AI与ML方向的核心课程拆解成五条知识线——传统ML、深度学习、Transformer与大模型、强化学习、NLP与CV——告诉你每条线的核心知识点、在研究中怎么用、以及怎么规划四学期的选课路线。

这是「CS博士通关路」系列的第五篇。上一篇讲了系统课，这一篇我们进入当前CS最热门的领域——AI与ML。

## 一、机器学习基础：从SVM到集成方法

传统ML不是过时的知识，是理解所有现代AI方法的基础。深度学习不是凭空出现的，它是在传统ML的框架上演进而来的。

### SVM（Support Vector Machine，支持向量机）

SVM的核心思想是找到一个超平面，使得两类样本之间的间隔（Margin）最大化。间隔越大，分类器的泛化能力越强——这是SVM泛化性能的理论保证，由VC维（Vapnik-Chervonenkis Dimension）理论支撑。

支持向量是离决策边界最近的样本点——它们"支撑"着决策边界。其他样本点的位置不影响决策边界，这就是SVM的稀疏性。这个性质在实际中意味着：即使训练数据量很大，SVM的预测只需要计算支持向量的内积。

核技巧（Kernel Trick）是SVM的精髓。它通过核函数把数据隐式地映射到高维空间，在高维空间中线性可分，而不需要显式计算高维特征。RBF核（Radial Basis Function Kernel，径向基函数核）是最常用的核函数，它对应无限维的特征空间。

SVM的对偶形式不只是计算技巧，它揭示了SVM的几何本质。在对偶形式中，优化变量是每个样本对应的拉格朗日乘子alpha_i。KKT条件告诉我们：只有支持向量（恰好满足间隔边界的样本）的alpha_i > 0，其余样本的alpha_i = 0。这意味着SVM的解只由少数支持向量决定——这是SVM稀疏性的数学根源。

Hinge Loss（合页损失）是SVM的另一种视角。SVM等价于最小化Hinge Loss加上L2正则化：L = max(0, 1 - y*f(x)) + lambda*||w||^2。这个视角把SVM和逻辑回归、神经网络统一在了经验风险最小化（Empirical Risk Minimization, ERM）框架下——区别只在于损失函数的选择。Hinge Loss是0-1损失的上界，且是凸的，所以SVM有全局最优解。

核方法的深度理解需要泛函分析（Functional Analysis）中的Mercer定理——一个函数是合法核函数当且仅当对应的核矩阵是半正定的。这个定理把核函数和高维特征空间的内积联系起来，是核技巧的理论基础。

SVM对偶问题的核心求解代码展示了拉格朗日乘子法的实际应用：

```python
import numpy as np
def svm_dual(X, y, C=1.0, epochs=1000, lr=0.001):
    n = len(X)
    alpha = np.zeros(n)
    K = X @ X.T  # 线性核
    for _ in range(epochs):
        grad = np.ones(n) - (alpha * y) @ (K * (y[:, None] * y[None, :]))
        alpha = np.clip(alpha + lr * grad, 0, C)
    return alpha
```

这段代码通过对偶问题求解SVM——优化拉格朗日乘子alpha，受到0到C的约束。这就是KKT条件在SVM中的直接应用。

### 决策树（Decision Tree）

决策树通过递归地选择最优特征分裂来构建分类或回归模型。分裂准则决定选择哪个特征：信息增益（Information Gain）选择能最大减少熵（Entropy）的特征；增益率（Gain Ratio）修正了信息增益偏向多值特征的问题；基尼指数（Gini Index）衡量集合的不纯度。

决策树的优势是可解释性强——你可以沿着树的路径理解每个决策。但单棵决策树容易过拟合，需要剪枝（Pruning）或集成方法来提升泛化能力。

### 集成方法（Ensemble Methods）

集成方法把多个弱学习器组合成强学习器。Bagging（Bootstrap Aggregating，自助聚合）通过有放回采样生成多个训练集，分别训练模型后投票。随机森林（Random Forest）是Bagging的典型代表，在决策树基础上加了随机特征选择。

Boosting是另一种策略——串行训练，每个新模型关注前一个模型的错误。AdaBoost通过调整样本权重让后续模型关注难分类样本。Gradient Boosting通过拟合残差（Residual）来改进。XGBoost和LightGBM是Gradient Boosting的高效实现，在Kaggle竞赛和工业界广泛使用。

Stacking更灵活——用多个不同类型的基学习器的预测结果作为元学习器的输入。但Stacking容易过拟合，需要交叉验证来训练元学习器。

决策树的分裂准则看似简单，但有微妙的区别。信息增益偏向多值特征——如果一个特征有很多取值（如ID），信息增益会很高但泛化能力差。增益率通过除以固有熵（Intrinsic Entropy）来修正这个偏差。基尼指数计算更快（不需要对数运算），在大多数情况下和信息增益给出相似的分裂结果。

XGBoost的成功不仅在于算法，更在于工程优化。它实现了列采样（Column Subsampling）——随机采样特征，类似随机森林。它支持稀疏数据的高效处理——内部维护一个稀疏感知（Sparsity-aware）的分裂算法。它还实现了直方图近似（Histogram Approximation）——把连续特征分桶，从O(n)遍历降到O(bins)遍历。这些工程优化使XGBoost在实际应用中远快于原始Gradient Boosting。

LightGBM进一步优化了训练效率。它使用GOSS（Gradient-based One-Side Sampling）保留梯度大的样本，随机丢弃梯度小的样本。它使用EFB（Exclusive Feature Bundling）把互斥特征捆绑，减少特征维度。这些技术让LightGBM在百万级数据上训练速度比XGBoost快数倍。

### 偏差-方差分解（Bias-Variance Decomposition）

偏差-方差分解是理解ML模型行为的理论框架。模型的期望泛化误差可以分解为三部分：偏差的平方、方差、和不可约误差。

偏差衡量模型对真实关系的拟合能力——高偏差意味着欠拟合（Underfitting），模型太简单。方差衡量模型对训练数据变化的敏感度——高方差意味着过拟合（Overfitting），模型太复杂。

正则化（Regularization）是控制方差的核心工具。L1正则化（Lasso）在损失函数中加入权重的绝对值和，产生稀疏解——部分权重精确为零。这在特征选择中有用——非零权重对应的特征就是被选中的特征。L2正则化（Ridge）加入权重的平方和，收缩权重但不产生精确的零。弹性网络（Elastic Net）结合L1和L2，在高度相关特征存在时比纯L1更稳定。

在深度学习中，正则化有更多形式。Early Stopping（早停）在验证集性能不再提升时停止训练——这等价于L2正则化的隐式实现。Data Augmentation（数据增强）通过对训练数据做变换（旋转、裁剪、翻转）增加有效数据量。Label Smoothing（标签平滑）把one-hot标签的1改为0.9、0改为0.1/N，防止模型过度自信。这些技术都在控制方差——让模型不过度拟合训练数据的特定样本。

| ML算法 | 适用场景 | 训练复杂度 | 可解释性 | 过拟合风险 |
|--------|---------|-----------|---------|-----------|
| SVM | 中小规模分类 | O(n^2)-O(n^3) | 中 | 低（有间隔保证） |
| 决策树 | 分类/回归 | O(n log n) | 高 | 高 |
| 随机森林 | 通用 | O(n log n) * m棵 | 中 | 低 |
| XGBoost | 结构化数据 | O(n log n) * T轮 | 中 | 中 |
| 神经网络 | 大规模/非结构化 | O(n) per epoch | 低 | 高 |

> 传统ML不是"旧技术"，是理解深度学习的钥匙。当你说"神经网络过拟合"时，你说的就是方差太大；当你说"加正则化"时，你在做的就是偏差-方差权衡。不懂传统ML的人，做深度学习只是在调参。

## 二、深度学习：从CNN到Transformer的演进

深度学习的核心是表示学习（Representation Learning）——让模型自动学习有用的特征表示，而不是手工设计特征。

### CNN（Convolutional Neural Network，卷积神经网络）

CNN的核心操作是卷积。卷积核（Kernel/Filter）在输入上滑动，每个位置做元素乘法求和，得到输出特征图（Feature Map）。卷积操作的两个关键特性：参数共享（Parameter Sharing）——同一个卷积核在所有位置共享参数，大大减少参数量；局部连接（Local Connectivity）——每个输出只依赖输入的一个局部区域。

感受野（Receptive Field）是CNN中最重要的概念。它指一个输出像素对应输入图像的区域大小。第一层卷积的感受野等于卷积核大小，第二层的感受野等于第一层卷积核大小加上（卷积核大小-1）乘以第一层步长。多层堆叠后，深层神经元的感受野可以覆盖整个输入图像。

池化（Pooling）操作降采样特征图，减少计算量并提供一定的平移不变性（Translation Invariance）。最大池化（Max Pooling）取窗口最大值，平均池化（Average Pooling）取窗口平均值。

ResNet（Residual Network，残差网络）引入了跳跃连接（Skip Connection）——把输入直接加到输出上。这个看似简单的改动解决了深层网络退化问题（Degradation Problem），使得训练上百层的网络成为可能。ResNet的核心思想是学习残差映射而非直接映射——学习F(x) = H(x) - x比直接学习H(x)更容易。

1x1卷积看似无意义——卷积核大小为1x1意味着每个输出只依赖输入的一个像素。但1x1卷积的作用是降维或升维——它可以改变通道数。在Inception网络（GoogLeNet）中，1x1卷积用于在3x3卷积前降低通道数，大幅减少计算量。在ResNet的Bottleneck Block中，1x1卷积先降维再升维，使得3x3卷积在低维空间操作。

深度可分离卷积（Depthwise Separable Convolution）是MobileNet的核心技术。它把标准卷积分解为两步：Depthwise卷积（每个通道独立卷积）和Pointwise卷积（1x1卷积混合通道）。计算量从O(C_in * C_out * k * k)降到O(C_in * k * k + C_in * C_out)，减少了约k^2倍。这种分解在保持效果的同时大幅降低计算量，是轻量级网络的基础。

DenseNet（Dense Convolutional Network）提出了另一种连接方式——每层的输入是之前所有层的输出的拼接（Concatenation）。与ResNet的加法不同，DenseNet用拼接实现了特征重用。这种设计减少了参数量和梯度消失问题，但在实际中内存消耗较大。

### RNN（Recurrent Neural Network，循环神经网络）

RNN处理序列数据。它在每个时间步接收一个输入，维护一个隐藏状态（Hidden State），隐藏状态是之前所有输入的"记忆"。RNN的参数在所有时间步共享。

但RNN有梯度消失/爆炸问题（Vanishing/Exploding Gradient）。当序列很长时，反向传播的梯度在时间维度上反复乘以相同的权重矩阵，导致指数衰减或增长。

LSTM（Long Short-Term Memory，长短期记忆网络）通过门控机制解决这个问题。LSTM有三个门：遗忘门（Forget Gate）决定丢弃多少旧记忆，输入门（Input Gate）决定加入多少新信息，输出门（Output Gate）决定输出什么。细胞状态（Cell State）是一条信息高速公路，梯度可以几乎不衰减地流过。

GRU（Gated Recurrent Unit，门控循环单元）是LSTM的简化版，把遗忘门和输入门合并为更新门（Update Gate），参数更少，在很多任务上性能相当。

梯度裁剪（Gradient Clipping）是处理梯度爆炸的简单但有效的方法。当梯度范数超过阈值时，把梯度缩放到阈值范围内。这个方法虽然简单，但在训练RNN和Transformer时几乎是必需的。

学习率调度（Learning Rate Scheduling）对深度学习训练至关重要。Warmup策略在前几个epoch用很小的学习率逐渐增大，然后开始衰减。Warmup解决了训练初期梯度不稳定的问题——初始时随机初始化的权重产生大的梯度，用大学习率会导致训练发散。Cosine Annealing（余弦退火）让学习率按余弦曲线衰减，效果通常比阶梯衰减好。OneCycle策略结合了Warmup和退火，在训练中期用大学习率，末期用小学习率，效果经常超过其他策略。

混合精度训练（Mixed Precision Training）用FP16（半精度浮点数）加速计算，同时保留FP32（单精度浮点数）的主权重副本避免精度损失。Loss Scaling通过在反向传播前放大损失来避免FP16的梯度下溢（Underflow）问题。现代GPU的Tensor Core对FP16计算有专门加速，混合精度可以让训练速度提升2到3倍。

### 反向传播（Backpropagation）

反向传播是深度学习的计算引擎。它通过链式法则（Chain Rule）高效计算损失函数对每个参数的梯度。

计算图（Computational Graph）是理解反向传播的最佳工具。前向传播把计算过程展开为有向无环图，每个节点是一个操作。反向传播从输出开始，反向遍历图，在每个节点上用链式法则计算局部梯度并传递给上游节点。

反向传播核心计算代码展示了链式法则在计算图上的应用：

```python
def backward(self, grad_output):
    # 链式法则: dL/dx = dL/dy * dy/dx
    grad_input = grad_output * self.local_grad
    for child in self.children:
        child.backward(grad_input)
    return grad_input
```

这段代码展示了反向传播的递归本质——每个节点收到上游梯度，乘以本地梯度，传递给下游节点。现代深度学习框架（PyTorch、TensorFlow）自动构建计算图并自动执行反向传播，但理解原理对于调试和优化至关重要。

梯度检查（Gradient Checking）是验证反向传播实现正确性的重要技术。它用数值梯度（有限差分）近似计算梯度，和解析梯度比较。如果两者差异在1e-7以内，说明实现正确。这个技术在调试自定义层或自定义损失函数时非常有用——现代框架的自动微分虽然可靠，但当你需要实现非标准操作时，梯度检查仍然是必要的验证手段。

梯度爆炸（Gradient Explosion）和梯度消失（Gradient Vanishing）是深层网络的两大敌人。除了LSTM的门控机制和ResNet的跳跃连接，还有其他技术：Highway Network使用门控机制控制信息流；Batch Normalization通过归一化每层输入，使梯度更稳定；Xavier/He初始化根据层的输入输出维度设置初始权重方差，使前向传播和反向传播的信号方差保持一致。

### 正则化（Regularization）（Regularization）

Dropout在训练时随机丢弃一部分神经元，测试时使用全部神经元但缩放权重。它的效果近似于训练了指数级多个子网络的集成。Batch Normalization（批归一化）把每层的输入归一化到零均值单位方差，加速训练并允许使用更大的学习率。Layer Normalization（层归一化）在Transformer中替代Batch Normalization，因为序列长度可变时Batch Normalization效果差。

权重衰减（Weight Decay）等价于L2正则化——在损失函数中加上权重参数的平方和，鼓励小的权重值。现代优化器如AdamW把权重衰减从梯度中分离出来，效果更好。

> 深度学习不是"玄学"。当你的模型不收敛时，大概率是梯度问题——要么梯度消失要么梯度爆炸。当你的模型过拟合时，想想偏差-方差分解。深度学习的所有"技巧"，都有传统ML的理论根基。

## 三、Transformer与大模型：Self-Attention如何改变一切

Transformer是2017年提出的架构，它在几乎所有NLP任务上超越了RNN，并且成为了GPT、BERT、LLaMA等大模型的基础架构。

### Self-Attention机制

Self-Attention的核心思想是让序列中的每个位置"关注"所有其他位置。具体来说，它把输入映射为三个矩阵：Q（Query，查询）、K（Key，键）、V（Value，值）。注意力分数通过Q和K的点积计算，然后经过Softmax归一化，最后加权求和V。

Scaled Dot-Product Attention的核心计算：

```python
import torch.nn.functional as F
def attention(Q, K, V, mask=None):
    scores = Q @ K.transpose(-2, -1) / (d_k ** 0.5)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    weights = F.softmax(scores, dim=-1)
    return weights @ V
```

这段代码展示了Self-Attention的核心：Q和K的点积衡量"相关性"，除以根号d_k防止点积过大导致Softmax饱和，mask用于处理变长序列。简洁的几行代码，撑起了整个大模型时代。

Multi-Head Attention把Q、K、V分别投影到多个子空间，在每个子空间独立计算Attention，然后拼接。这允许模型从不同角度关注序列——有的Head关注语法关系，有的Head关注语义关系。

Attention的复杂度是O(n^2 * d)，其中n是序列长度，d是特征维度。Q @ K^T产生n x n的注意力矩阵，对于长序列（n=8192或更长）这会消耗大量内存。这是Transformer处理长序列的瓶颈。

Flash Attention通过分块计算（Tiling）和在线Softmax（Online Softmax）避免了完整n x n矩阵的物化，大幅减少内存访问。它不改变注意力机制本身，只是优化了计算方式，但速度可以快2到4倍。Flash Attention是当前大模型训练的标准组件。

稀疏注意力（Sparse Attention）通过限制每个位置只关注部分位置来降低复杂度。Longformer使用滑动窗口注意力加上少量全局注意力。BigBird结合随机注意力、窗口注意力和全局注意力，理论上可以近似完整注意力的表达能力。这些方法把复杂度从O(n^2)降到O(n log n)或O(n)。

### Positional Encoding（位置编码）

Self-Attention本身是排列不变的——它不区分输入的顺序。但语言和序列的顺序很重要，所以需要位置编码注入位置信息。

正弦余弦编码（Sinusoidal Encoding）使用不同频率的正弦和余弦函数。它的优点是可以推广到训练时未见过的序列长度。可学习编码（Learnable Encoding）把位置嵌入作为可训练参数，效果通常更好但不能推广。相对位置编码（Relative Positional Encoding）编码的是两个位置之间的相对距离，在翻译和生成任务中效果更好。

### 预训练范式（Pre-training Paradigm）

预训练改变了NLP的游戏规则。不再是针对每个任务从零训练，而是先在大规模无标注数据上预训练，再在下游任务上微调。

MLM（Masked Language Model，掩码语言模型）是BERT的预训练任务——随机遮盖一些token，让模型预测被遮盖的token。这使得模型学会双向理解上下文。CLM（Causal Language Model，因果语言模型）是GPT的预训练任务——给定前文预测下一个token。这使得模型学会生成文本。

对比学习（Contrastive Learning）是另一种预训练范式——让正样本对的表示接近，负样本对的表示远离。SimCLR和CLIP是对比学习的代表。CLIP把图像和文本对齐到同一表示空间，使得图文检索成为可能。

### 微调策略

全参数微调（Full Fine-Tuning）更新所有参数，效果最好但计算成本高。Prompt Tuning只训练一小段prompt前缀，参数效率极高但表达能力有限。LoRA（Low-Rank Adaptation，低秩适应）在权重矩阵旁加一个低秩分解的增量，只训练增量部分。LoRA在保持接近全参数微调效果的同时，可训练参数减少数百倍。

| 微调方法 | 可训练参数 | 效果 | 显存需求 | 适用场景 |
|---------|-----------|------|---------|---------|
| Full Fine-Tuning | 100% | 最好 | 高 | 资源充足、追求最优效果 |
| Prompt Tuning | <1% | 较差 | 低 | 快速原型、多任务部署 |
| LoRA | 0.1-1% | 接近全参数 | 中 | 资源受限、多任务切换 |
| Adapter | 1-5% | 好 | 中 | 多任务部署 |

> Transformer的成功不是某一个人的天才时刻，而是注意力机制、残差连接、层归一化、预训练范式等多个技术积累的爆发。理解每一块积木的作用，你才能在大模型时代做出自己的创新。

Scaling Law（缩放定律）是大模型时代的重要经验规律。它指出模型性能（Loss）随参数量N、数据量D、计算量C的幂律下降：L = A/N^alpha + B/D^beta + C_compute^gamma。这意味着只要持续增加参数和数据，模型性能就会持续提升（在当前规模下还没有看到饱和）。Chinchilla定律进一步指出，给定计算预算时，参数量和数据量应该按比例增长——大多数大模型"参数过剩、数据不足"。

涌现能力（Emergent Abilities）是大模型的另一个有趣现象。某些能力（如算术推理、多步推理）在小模型中不存在，但在大模型中突然出现。这种"相变"式的行为引发了关于大模型是否真正"理解"语言的讨论。也有研究者认为涌现能力可能是评估指标的非线性导致的假象——用连续指标时能力可能是平滑增长的。

RLHF（Reinforcement Learning from Human Feedback，基于人类反馈的强化学习）是GPT-3.5之后大模型对齐的核心技术。它分三步：训练一个奖励模型（Reward Model）学习人类偏好；用PPO等RL算法优化语言模型使其获得高奖励；用KL散度约束防止模型偏离原始分布太远。RLHF让大模型从"续写文本"变成"回答问题"，是从GPT-3到ChatGPT的关键技术跃迁。

## 四、强化学习：从Q-Learning到PPO

强化学习（RL）研究智能体（Agent）在环境（Environment）中通过试错学习最优策略。RL在游戏AI（AlphaGo）、机器人控制、推荐系统中都有成功应用。

### MDP（Markov Decision Process，马尔可夫决策过程）

MDP是RL的数学框架。它由五元组定义：状态空间S、动作空间A、转移概率P(s'|s,a)、奖励函数R(s,a,s')、折扣因子gamma。折扣因子控制对未来奖励的重视程度——gamma越接近1越重视长期回报，越接近0越重视即时回报。

MDP的马尔可夫性质——下一状态只依赖当前状态和动作，不依赖历史——使得问题可以用动态规划求解。但在实际中，转移概率R和P通常是未知的，这就是RL需要"学习"的原因。

### Q-Learning

Q-Learning是经典的model-free RL算法。它学习Q值函数Q(s,a)——在状态s执行动作a后，按最优策略行动的期望累计奖励。

Q值的更新基于贝尔曼方程（Bellman Equation）：Q(s,a) = R + gamma * max Q(s',a')。每次交互后，用观测到的奖励和下一状态的最大Q值更新当前Q值。

Q-Learning的更新核心代码：

```python
def q_learning_update(Q, s, a, r, s_next, alpha, gamma):
    td_target = r + gamma * max(Q[s_next])
    Q[s][a] += alpha * (td_target - Q[s][a])
```

这段代码展示了TD（Temporal Difference，时序差分）学习的核心——用当前估计和一步真实奖励的差值（TD Error）来更新Q值。简洁但深刻。

探索-利用平衡（Exploration-Exploitation Trade-off）是RL的核心难题。Epsilon-Greedy策略以概率epsilon随机探索，以概率1-epsilon选择最优动作。epsilon从高到低退火，前期多探索，后期多利用。

### 策略梯度（Policy Gradient）

Q-Learning是value-based方法——先学Q值再推导策略。Policy Gradient是policy-based方法——直接优化策略参数。

REINFORCE是最基础的策略梯度算法。它用对数似然乘以累计回报作为梯度：grad = log(pi(a|s)) * G。这个梯度的直觉是：增加高回报动作的概率，降低低回报动作的概率。

但REINFORCE的方差很大——不同episode的回报差异巨大。引入基线（Baseline）可以减少方差：用回报减去一个基线值（通常是状态值函数V(s)），而不改变梯度的期望。这就是Advantage（优势函数）的概念：A(s,a) = Q(s,a) - V(s)。

Actor-Critic架构结合了value-based和policy-based方法。Actor（演员）是策略网络，Critic（评论家）是价值网络。Actor根据Critic的评估调整策略，Critic根据实际回报评估Actor的表现。

### PPO（Proximal Policy Optimization，近端策略优化）

PPO是当前最流行的RL算法之一。它的核心思想是限制策略更新的幅度——每次更新不要偏离当前策略太远。

PPO的裁剪目标函数（Clipped Objective）：L = min(ratio * A, clip(ratio, 1-eps, 1+eps) * A)。其中ratio是新策略和旧策略的概率比。当ratio超出[1-eps, 1+eps]范围时，梯度被裁剪，防止策略剧烈变化。

重要性采样（Importance Sampling）使得PPO可以重用旧策略收集的数据——用旧策略的样本估计新策略的梯度。GAE（Generalized Advantage Estimation，广义优势估计）通过指数加权的多步回报来平衡偏差和方差。

| RL方法 | 类型 | 核心思想 | 优势 | 劣势 |
|--------|------|---------|------|------|
| Q-Learning | Value-based | 学习Q值函数 | 简单、样本效率高 | 不支持连续动作 |
| DQN | Value-based | Q-Learning+深度网络 | 处理高维状态 | 训练不稳定 |
| REINFORCE | Policy-based | 直接优化策略 | 支持连续动作 | 方差大 |
| A2C/A3C | Actor-Critic | 策略+价值 | 方差小 | 需要两个网络 |
| PPO | Actor-Critic | 裁剪策略更新 | 稳定、效果好 | 样本效率中等 |

> 强化学习是AI中最接近"通用智能"的方向。但它也是最难的——稀疏奖励（Sparse Reward）、信用分配（Credit Assignment）、探索效率（Sample Efficiency）这些核心难题至今没有完美解决方案。Offline RL的发展方向包括保守Q学习（Conservative Q-Learning）、Decision Transformer（把RL建模为序列生成问题）和In-context RL（利用大模型的上下文学习能力做RL）。这些方法正在模糊RL和监督学习的边界。

Multi-Agent RL（多智能体强化学习）是另一个前沿方向。当多个智能体在同一个环境中交互时，每个智能体的策略都会影响其他智能体的最优策略——这是一个博弈论（Game Theory）问题。Nash均衡（Nash Equilibrium）是MARL的核心解概念。Self-play（自我对弈）是AlphaGo和AlphaStar成功的关键——智能体通过和自己的历史版本对弈不断进步。但self-play也有不稳定性——策略可能循环（Rock-Paper-Scissors问题），需要Population-based训练来避免。

如果你选择RL方向，做好面对失败多于成功的心理准备。

DQN（Deep Q-Network）把Q-Learning和深度学习结合，用神经网络近似Q函数。它引入了两个关键技巧：Experience Replay（经验回放）——把交互数据存入缓冲区，随机采样训练，打破数据相关性；Target Network（目标网络）——用延迟更新的网络计算TD Target，稳定训练。DQN在Atari游戏上达到人类水平，是深度RL的里程碑。

但DQN有Q值过估计（Overestimation）问题——max操作会系统性地高估Q值。Double DQN用主网络选择动作、目标网络评估Q值，解耦了选择和评估，缓解过估计。Dueling DQN把Q值分解为状态价值V(s)和优势函数A(s,a)：Q(s,a) = V(s) + A(s,a) - mean(A)，使得即使在动作价值相近时也能有效学习状态价值。

Offline RL（离线强化学习）是当前的研究热点。传统的Online RL需要智能体与环境交互收集数据，成本高且有安全风险。Offline RL从已有的离线数据集学习策略，不需要在线交互。挑战在于分布偏移（Distribution Shift）——策略产生的动作分布和离线数据的分布不一致时，Q值估计会有大偏差。Conservative Q-Learning（CQL）通过惩罚未见动作的Q值来缓解这个问题。

## 五、NLP与CV核心知识：从词向量到目标检测

NLP（Natural Language Processing，自然语言处理）和CV（Computer Vision，计算机视觉）是AI的两大应用领域。虽然Transformer正在统一这两个领域，但它们各有独特的核心知识。

### 词向量（Word Embedding）

词向量是NLP的基础。Word2Vec通过CBOW（Continuous Bag-of-Words）或Skip-gram模型学习词向量。CBOW用上下文预测中心词，Skip-gram用中心词预测上下文。词向量的神奇之处在于它能捕获语义关系——"国王-男人+女人=女王"。

GloVe（Global Vectors for Word Representation）通过全局共现矩阵学习词向量。它分解对数共现矩阵，使得词向量的点积等于共现概率的对数。GloVe和Word2Vec在大多数任务上性能相当，但GloVe训练更快。

### 注意力机制（Attention Mechanism）

注意力机制最初在机器翻译中提出。Bahdanau Attention使用双向RNN编码器，解码时对源序列的所有位置计算注意力权重，加权求和得到上下文向量。这解决了序列到序列模型中固定长度编码的信息瓶颈问题。

Luong Attention简化了Bahdanau Attention的计算，提出了全局注意力和局部注意力两种变体。Self-Attention更进一步——序列内部自己做注意力，不需要外部的编码器-解码器结构。Self-Attention是Transformer的核心。

### 目标检测（Object Detection）

目标检测是CV的核心任务——不仅识别图像中的物体类别，还要定位它们的位置。

R-CNN系列（R-CNN, Fast R-CNN, Faster R-CNN）使用两阶段策略。第一阶段生成候选区域（Region Proposal），第二阶段对每个候选区域分类和回归边界框。Faster R-CNN用RPN（Region Proposal Network）替代Selective Search，实现了端到端训练。

YOLO（You Only Look Once）使用单阶段策略——把检测框建模为回归问题，一次前向传播输出所有检测结果。YOLO速度快但精度略低，适合实时检测。

DETR（Detection Transformer）把Transformer引入目标检测。它把检测建模为集合预测问题，用二分图匹配（Bipartite Matching）消除重复检测。DETR不需要Anchor和NMS（Non-Maximum Suppression），简化了检测pipeline。

### 语义分割（Semantic Segmentation）

语义分割给图像的每个像素分配类别标签。FCN（Fully Convolutional Network，全卷积网络）把分类网络的最后全连接层替换为卷积层，实现端到端的像素级分类。U-Net使用编码器-解码器结构和跳跃连接（Skip Connection），在医学图像分割中表现出色。Mask R-CNN在目标检测的基础上增加分割分支，同时做检测和分割。

IoU（Intersection over Union，交并比）计算的核心代码：

```python
def iou(box1, box2):
    x1 = max(box1[0], box2[0]); y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2]); y2 = min(box1[3], box2[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    union = area(box1) + area(box2) - inter
    return inter / union if union > 0 else 0
```

这段代码展示了检测评估的核心指标——两个边界框的交集面积除以并集面积。IoU是目标检测中NMS和mAP（mean Average Precision）计算的基础。

| 维度 | NLP | CV |
|------|-----|-----|
| 核心数据 | 文本序列 | 图像/视频 |
| 代表模型 | BERT, GPT, LLaMA | ResNet, ViT, YOLO |
| 评估指标 | BLEU, ROUGE, 困惑度 | mAP, IoU, Accuracy |
| 预训练数据 | 文本语料 | ImageNet, LAION |
| 当前趋势 | 大语言模型, 多模态 | Vision Transformer, 扩散模型 |

> NLP和CV的边界正在模糊。Vision Transformer把图像当作序列处理，CLIP把图文映射到同一空间。未来的AI研究者不应该把自己限定在"NLP"或"CV"的框框里——底层是通用的表示学习和序列建模。

语言模型的演进是NLP发展的主线。N-gram模型基于马尔可夫假设——下一个词只依赖前n-1个词。它简单但受维度灾难限制——n越大，参数空间指数增长。NNLM（Neural Network Language Model）用神经网络替代了查表，突破了维度灾难。Word2Vec是NNLM的简化版——只保留词向量层，用轻量网络训练。ELMo把词向量升级为上下文词向量——同一个词在不同语境下有不同表示。BERT和GPT用Transformer统一了整个NLP pipeline，不再需要为每个任务设计特定架构。

Vision Transformer（ViT）把Transformer架构从NLP迁移到CV。它把图像切分为固定大小的Patch（如16x16），把每个Patch线性映射为一个向量，加上位置编码后输入标准Transformer。ViT在大型数据集（如ImageNet-21k或JFT-300M）上预训练后，在图像分类上超越了ResNet。Swin Transformer引入了层级结构和移动窗口注意力，使ViT能处理检测和分割等密集预测任务。

扩散模型（Diffusion Model）是图像生成的新范式。它通过前向过程逐步给图像加噪，反向过程逐步去噪生成图像。DDPM（Denoising Diffusion Probabilistic Model）是理论基础，Stable Diffusion结合了扩散模型和自编码器实现高效生成。扩散模型在图像质量上超越了GAN，且训练更稳定。

## 六、AI/ML课程学习路线：四学期规划

AI/ML方向的课程有明确的依赖关系。数学基础是ML基础的前置，ML基础是深度学习的前置，深度学习是Transformer/NLP/CV的前置。怕浪猫给你一个四学期规划。

### 依赖关系

数学基础（概率论、线性代数、最优化）是所有AI/ML课程的地基。ML基础（SVM、决策树、集成方法）教你基本的建模思维。深度学习（CNN、RNN、反向传播）是从传统ML到现代AI的桥梁。Transformer/NLP/CV是应用方向。强化学习相对独立，但需要概率论和深度学习基础。

### 四学期选课规划

| 学期 | 核心课程 | 配套课程 | 核心产出 |
|------|---------|---------|---------|
| 第1学期 | 概率论、线性代数 | ML基础 | 实现SVM和决策树 |
| 第2学期 | 深度学习 | 强化学习 | 复现一篇经典论文 |
| 第3学期 | NLP或CV | 系统课（并行） | 方向性project |
| 第4学期 | 高级专题 | 论文阅读课 | 研究方向论文 |

第1学期建立数学和ML基础。概率论和线性代数是必须的，ML基础课让你理解建模的基本框架。这个学期的产出是用NumPy实现SVM和决策树，不用框架。

第2学期深入学习深度学习和强化学习。这个学期的核心产出是复现一篇经典论文——比如ResNet、BERT或DQN。复现论文是最好的学习方法，它暴露你在理论和工程上的所有盲点。

第3学期选择NLP或CV作为主攻方向（另一个可以后修）。同时修系统课——因为ML系统（MLSys）是交叉方向，懂系统的ML研究者和懂ML的系统研究者都有巨大优势。

第4学期进入高级专题。大模型训练、多模态学习、AI安全、联邦学习等都是热门方向。这个学期应该开始做研究project，为开题做准备。

> AI/ML方向变化极快，今天的热点明天可能就过时。但底层的数学和原理不变。怕浪猫的建议是：把70%的精力放在基础上（数学、ML理论、深度学习原理），30%放在前沿跟踪上。基础扎实的人，学新东西比别人快十倍。

### 论文阅读的方法论

AI/ML方向最重要的学习能力不是写代码，是读论文。怕浪猫推荐"三遍阅读法"。

第一遍快速浏览——读标题、摘要、结论，花5分钟判断值不值得深读。第二遍读方法——理解核心思想、模型结构、实验设计，不纠结细节。第三遍精读——逐行看公式推导、看实验细节、看代码实现。不是每篇论文都需要读到第三遍——大多数论文第二遍就够了，只有你要复现或在其基础上做研究时才需要第三遍。

建立个人论文笔记系统。每篇论文记录：核心贡献（一句话）、方法关键点（一段话）、和自己研究的关联、可复用的技术/技巧。这个笔记系统会随着你的研究积累越来越有价值。

### 实践项目的选择

AI/ML课程不能只看不做。每学一个方法，做一个对应的实践项目。ML基础阶段，用scikit-learn做一个Kaggle竞赛项目。深度学习阶段，用PyTorch从零实现一个CNN或RNN。Transformer阶段，实现一个简化版GPT并训练一个小语言模型。强化学习阶段，用OpenAI Gym训练一个游戏AI。

实践项目的关键是"从零实现"——不用高级框架的现成接口，而是自己写前向传播、反向传播、训练循环。这个过程暴露的盲点比看十篇论文都多。

### 研究方向的选择

AI/ML方向太多，博士生面临"选择困难症"。怕浪猫的建议是：第一学期广泛了解各方向，第二学期深入1到2个方向做project，第三学期确定研究方向。选择方向时考虑三个因素：个人兴趣（你能持续投入5年吗）、导师专长（导师能在方向上给你有效指导吗）、领域前景（5年后这个方向还有活力吗）。

不要追热点。3年前Meta-learning是热点，现在热度大减。5年前GAN是热点，现在被扩散模型取代。选择一个你有深入理解且有长期价值的基础问题，比追热点更可靠。怕浪猫见过太多追热点的博士生——GAN火的时候做GAN，扩散模型火了又转扩散，结果每个方向都浅尝辄止，毕业时没有一项深入的工作。

## 系列进度与下章预告

这篇文章是「CS博士通关路」系列的第五篇。我们拆解了AI与ML方向的五条知识线：传统ML基础、深度学习、Transformer与大模型、强化学习、NLP与CV，以及四学期的选课规划。

如果你正在规划AI/ML方向的学习路线，把这篇文章收藏起来。知识图谱、依赖关系和选课规划表是你的路线图。

在评论区告诉怕浪猫：你在AI/ML学习中遇到的最大困难是什么？是数学、编程还是理解模型原理？

**系列进度 5/12**

下一章，怕浪猫给你整理一份从CLRS到Deep Learning的必读书单。每本书都告诉你为什么必读、读哪些章节最重要、怎么搭配课程使用。博士期间该读的20多本经典，一篇全搞定。

关注我，追更不迷路。

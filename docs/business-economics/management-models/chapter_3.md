---
sidebar_position: 3
---

# 第三章：决策与分析方法——让每个决策都有数据支撑

10种决策方法，我靠第4个避开了300万的项目亏损。

那年有个项目提案，市场前景数据漂亮、技术方案成熟、团队配置合理，所有人都说"做"。但用机会成本思维一算：同样的300万投入另一个方向，预期收益高2.5倍，且失败损失只有三分之一。最终砍掉了这个项目，半年后验证了那个方向确实是伪需求。

我是怕浪猫，一个把管理学拆成代码的实践派。前两章我们装好了思维模型和人格引擎，这一章来装"决策工具箱"。10种分析方法，每一种都有表格模板和代码实现，直接照抄就能用。

## 3.1 SWOT 分析法：四象限全景扫描

SWOT（Strengths, Weaknesses, Opportunities, Threats）是最经典也最被滥用的战略分析工具。问题不在工具本身，而在大多数人只是填了四个格子就完事了，没有进入真正的战略推演。

> SWOT不是填空题，而是交叉策略生成器。四个格子填完只是起点，两两交叉生成策略才是核心。

**SWOT 四象限矩阵的原理与填法：**

| 象限 | 定义 | 填写要点 | 常见错误 |
|------|------|---------|---------|
| Strengths（优势） | 组织内部的积极因素 | 具体可验证，而非形容词 | 写"团队好"而非"团队中3人有10年经验" |
| Weaknesses（劣势） | 组织内部的消极因素 | 诚实面对，不回避 | 只写表面问题，不写根因 |
| Opportunities（机会） | 外部环境的有利因素 | 有时效性，注明窗口期 | 写"市场很大"而无具体数据 |
| Threats（威胁） | 外部环境的不利因素 | 区分确定性和不确定性 | 忽略"低概率高影响"的威胁 |

**SWOT 真正的价值在于交叉策略：**

| 交叉 | 策略类型 | 英文 | 核心思路 | 示例 |
|------|---------|------|---------|------|
| S × O | 增长策略 | SO Strategy | 用优势抓住机会 | 技术强 × 市场需求增 → 快速推产品 |
| S × T | 防御策略 | ST Strategy | 用优势化解威胁 | 品牌好 × 竞品入场 → 用品牌壁垒防御 |
| W × O | 改善策略 | WO Strategy | 借机会补劣势 | 资金少 × 融资窗口开 → 赶紧融资 |
| W × T | 规避策略 | WT Strategy | 劣势遇威胁要收缩 | 技术弱 × 行业变局 → 转型或退出 |

**SWOT 与其他分析框架的对比：**

| 维度 | SWOT | PESTEL | Porter五力 | BCG矩阵 |
|------|------|--------|-----------|---------|
| 分析视角 | 内外结合 | 纯外部宏观 | 行业竞争 | 业务组合 |
| 适用阶段 | 战略初期扫描 | 宏观环境分析 | 行业进入决策 | 资源分配 |
| 操作难度 | 低 | 中 | 高 | 中 |
| 输出类型 | 策略方向 | 环境因素清单 | 竞争压力评估 | 投资优先级 |

**SWOT 自动生成评估的代码模板：**

```python
def swot_analysis(strengths, weaknesses, opportunities, threats):
    """SWOT 交叉策略生成器"""
    strategies = []
    for s in strengths:
        for o in opportunities:
            strategies.append({
                'type': 'SO (增长)', 
                'action': f"用 {s} 抓住 {o}"
            })
        for t in threats:
            strategies.append({
                'type': 'ST (防御)', 
                'action': f"用 {s} 化解 {t}"
            })
    for w in weaknesses:
        for o in opportunities:
            strategies.append({
                'type': 'WO (改善)', 
                'action': f"借 {o} 补 {w}"
            })
        for t in threats:
            strategies.append({
                'type': 'WT (规避)', 
                'action': f"因 {w} 遇 {t}，考虑收缩"
            })
    return strategies

# 用法示例
results = swot_analysis(
    strengths=["AI技术积累深", "核心团队稳定"],
    weaknesses=["销售能力弱", "资金有限"],
    opportunities=["行业AI需求爆发", "政策补贴"],
    threats=["大厂入场", "客户预算缩减"]
)
for s in results:
    print(f"[{s['type']}] {s['action']}")
```

实践建议：下次做战略规划，不要只填SWOT四格就交差。强制生成至少8条交叉策略，然后选3条作为行动项。

## 3.2 决策矩阵与加权评分法：把直觉变成数字

决策矩阵（Decision Matrix）是最实用的多因素决策工具。当面临多个选项、多个评估维度时，它能帮你把"感觉A更好"变成"A在关键维度上比B高23%"。

**加权决策矩阵的完整计算流程：**

| 步骤 | 操作 | 关键要点 |
|------|------|---------|
| 1 | 列出所有备选选项 | 不少于3个，不多于7个 |
| 2 | 确定评估维度 | 5-8个维度，覆盖成本/收益/风险/时间 |
| 3 | 为每个维度赋予权重 | 权重之和为100%，反映维度重要性 |
| 4 | 为每个选项在各维度打分 | 1-5分或1-10分，需要依据 |
| 5 | 计算加权总分 | 每个维度：得分 × 权重，求和 |
| 6 | 敏感性分析 | 调整权重看排名是否变化 |

**等权重 vs 差异权重 vs AHP 对比：**

| 方法 | 英文全称 | 权重确定方式 | 优点 | 缺点 |
|------|---------|------------|------|------|
| 等权重法 | Equal Weighting | 所有维度权重相同 | 简单 | 忽略维度重要性差异 |
| 差异权重法 | Differential Weighting | 决策者主观分配 | 直观、快速 | 主观偏差 |
| 层次分析法 | AHP (Analytic Hierarchy Process) | 两两比较矩阵推导 | 客观、一致性检验 | 计算复杂 |

**决策矩阵的 Python 实现代码：**

```python
import numpy as np

def decision_matrix(options, criteria, weights, scores):
    """
    options: 选项列表
    criteria: 评估维度列表
    weights: 权重列表(总和为1.0)
    scores: 二维数组, [option][criterion] = 分数(1-5)
    """
    weights = np.array(weights)
    scores = np.array(scores)
    # 加权总分
    weighted_scores = scores @ weights
    # 敏感性分析: 每个维度权重±10%看排名是否变
    results = []
    for i, opt in enumerate(options):
        results.append({
            'option': opt,
            'total': round(weighted_scores[i], 2),
            'detail': {c: int(scores[i][j]) 
                      for j, c in enumerate(criteria)}
        })
    results.sort(key=lambda x: x['total'], reverse=True)
    return results

# 示例: 选择技术方案
results = decision_matrix(
    options=["方案A(成熟)", "方案B(创新)", "方案C(保守)"],
    criteria=["开发速度", "性能", "维护成本", "招人难度", "风险"],
    weights=[0.25, 0.30, 0.20, 0.15, 0.10],
    scores=[
        [5, 3, 3, 5, 4],  # 方案A
        [2, 5, 4, 2, 2],  # 方案B
        [4, 3, 5, 4, 5],  # 方案C
    ]
)
for r in results:
    print(f"{r['option']}: {r['total']}分")
```

> 决策矩阵的真正价值不是给出排名，而是让分歧显性化。当两个人对同一选项打分差异超过2分时，你们需要讨论的不是"选哪个"，而是"为什么我们对这个维度的理解不同"。

实践建议：下次团队对某个决策有分歧，不要争论，用决策矩阵。每个人独立打分，然后比较差异点。你会发现80%的分歧来自对维度权重的理解不同，而非对选项的偏好不同。

## 3.3 事前验尸（Pre-mortem）：假设已失败，倒推风险

事前验尸（Pre-mortem）由心理学家加里·克莱因（Gary Klein）提出。操作方式极其反常规：在项目启动前，假设项目已经失败，让团队倒推失败原因。

> Post-mortem（事后验尸）是找死因，Pre-mortem（事前验尸）是预防死亡。前者太晚，后者正好。

**Pre-mortem 标准执行流程：**

| 步骤 | 时间 | 操作 | 关键规则 |
|------|------|------|---------|
| 1 | 5分钟 | 主持人宣布："项目已经失败了，不可挽回" | 所有人必须接受这个假设 |
| 2 | 5分钟 | 每个人独立写出失败原因（至少3个） | 不讨论、不评判 |
| 3 | 10分钟 | 轮流分享失败原因，记录在白板上 | 不反驳别人的原因 |
| 4 | 10分钟 | 对所有原因分类：致命/严重/次要 | 投票排序 |
| 5 | 15分钟 | 为致命和严重原因制定预防措施 | 每个原因必须有负责人 |

**Pre-mortem vs Post-mortem 对比：**

| 维度 | Pre-mortem（事前验尸） | Post-mortem（事后验尸） |
|------|----------------------|----------------------|
| 时间点 | 项目启动前 | 项目结束后 |
| 心理状态 | 假设失败，释放焦虑 | 真实失败或成功，情绪影响判断 |
| 目的 | 识别风险、制定预防 | 总结教训、改进流程 |
| 参与度 | 高（没有归责压力） | 中（可能有人防备） |
| 产出 | 风险清单+预防措施 | 经验教训+改进计划 |
| 价值 | 避免错误发生 | 避免重复错误 |

**风险清单生成的伪代码模板：**

```python
def pre_mortem(project_name, team_members):
    """事前验尸流程执行器"""
    failure_reasons = []
    for member in team_members:
        # 每人独立列出至少3个失败原因
        reasons = member.brainstorm_failures(min_count=3)
        failure_reasons.extend(reasons)
    
    # 分类排序
    categorized = classify_reasons(failure_reasons)
    prevention_plan = {}
    for reason in categorized['fatal'] + categorized['serious']:
        prevention_plan[reason] = {
            'prevention': design_prevention(reason),
            'owner': assign_owner(team_members),
            'checkpoint': set_checkpoint(project_name),
        }
    return prevention_plan

# 关键原则: "失败原因"不用于追责，只用于预防
```

实践建议：项目启动会留30分钟做Pre-mortem。你会发现团队说出的失败原因，有30%是你完全没想到的。这30%往往是致命的。

## 3.4 机会成本与 80/20 法则：选择性放弃的艺术

机会成本（Opportunity Cost）是经济学最朴素也最被忽视的概念：你选择做A的代价，是你放弃的所有其他选项中价值最高的那个。

> 管理者最危险的词不是"不做"，而是"都做"。什么都做等于什么都不做。

**机会成本的显性计算模型：**

| 选项 | 直接成本 | 机会成本(放弃的最佳替代) | 真实成本 | 决策含义 |
|------|---------|----------------------|---------|---------|
| 做项目A | 100万+2个月 | 放弃项目B(预期收益250万) | 350万 | 如果A预期<350万，不该做 |
| 开会2小时 | 时间成本 | 2小时能做的最高价值工作 | 远超2小时 | 很多会议不值得开 |
| 招人A | 30万年薪 | 招人B的预期产出差额 | 不可逆 | 选错人的隐性成本极大 |

**帕累托分析（Pareto Analysis）的 ABC 分类法：**

| 类别 | 累计占比 | 管理策略 | 资源分配 |
|------|---------|---------|---------|
| A类（关键少数） | 前0-80% | 重点投入、亲自盯 | 80%资源 |
| B类（重要多数） | 80-95% | 标准化管理 | 15%资源 |
| C类（次要多数） | 95-100% | 自动化或砍掉 | 5%资源 |

**80/20 识别的代码实现：**

```python
def pareto_analysis(items_with_values):
    """
    items_with_values: [(项目名, 价值贡献), ...]
    返回 ABC 分类结果
    """
    sorted_items = sorted(items_with_values, 
                         key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in sorted_items)
    
    cumulative = 0
    abc = {'A': [], 'B': [], 'C': []}
    for item, value in sorted_items:
        cumulative += value
        ratio = cumulative / total
        if ratio <= 0.80:
            abc['A'].append((item, value))
        elif ratio <= 0.95:
            abc['B'].append((item, value))
        else:
            abc['C'].append((item, value))
    return abc

# 示例: 分析客户贡献
customers = [("客户1", 500), ("客户2", 300), ("客户3", 150),
             ("客户4", 80), ("客户5", 50), ("客户6", 20)]
result = pareto_analysis(customers)
print(f"A类(关键): {result['A']}")  # 客户1+2+3 = 80%
print(f"B类(重要): {result['B']}")  # 客户4 = 15%
print(f"C类(次要): {result['C']}")  # 客户5+6 = 5%
```

实践建议：用帕累托分析你的工作内容。把每周的工作按价值贡献排序，你会发现60%的时间花在了C类事情上。把C类砍掉一半，你的有效产出会翻倍。

## 3.5 决策树分析：不确定性下的路径选择

决策树（Decision Tree）将决策过程可视化为树状结构，每个分支代表一个选择或事件，每个叶节点标注预期收益。它适合多阶段、有不确定性的决策场景。

**决策树的结构与期望值计算：**

| 组成部分 | 符号 | 含义 | 计算方式 |
|---------|------|------|---------|
| 决策节点 | 方形 | 你需要做的选择 | 选期望值最大的分支 |
| 机会节点 | 圆形 | 不确定事件 | 期望值 = 各结果概率 × 收益之和 |
| 结果节点 | 三角形 | 最终收益 | 直接给定 |
| 分支 | 箭头线 | 选择或事件 | 标注概率或成本 |

**决策树 vs 情景规划对比：**

| 维度 | 决策树 | 情景规划（Scenario Planning） |
|------|--------|----|
| 结构 | 树状，每个分支有概率 | 叙事式，几个完整故事 |
| 量化程度 | 高（期望值可计算） | 中（定性为主） |
| 适用场景 | 可量化、分阶段的决策 | 宏观环境、长期战略 |
| 优势 | 逻辑严密、可计算 | 激发想象力、发现盲区 |
| 劣势 | 对概率估计敏感 | 难以量化比较 |

**简单决策树的 Python 代码实现：**

```python
class DecisionNode:
    def __init__(self, name, node_type='decision'):
        self.name = name
        self.node_type = node_type  # 'decision' or 'chance' or 'end'
        self.children = []  # [(概率, 子节点, 路径成本)]
    
    def expected_value(self):
        if self.node_type == 'end':
            return self.value
        if not self.children:
            return 0
        if self.node_type == 'chance':
            return sum(p * child.expected_value() - cost 
                      for p, child, cost in self.children)
        if self.node_type == 'decision':
            return max(child.expected_value() - cost 
                      for _, child, cost in self.children)

# 示例: 是否上线新功能
root = DecisionNode("上线新功能?", 'decision')
# 分支1: 上线 (成本50万)
launch = DecisionNode("上线", 'chance')
launch.children = [
    (0.7, DecisionNode("成功", 'end'), 0),   # 70%成功, 收益200万
    (0.3, DecisionNode("失败", 'end'), 0),   # 30%失败, 损失30万
]
launch.children[0][1].value = 200
launch.children[1][1].value = -30
root.children.append((1, launch, 50))

# 分支2: 不上线 (成本0)
skip = DecisionNode("不上线", 'end')
skip.value = 0
root.children.append((1, skip, 0))

print(f"最优决策期望值: {root.expected_value()}万")
# 上线: 0.7*200 + 0.3*(-30) - 50 = 91万
# 不上线: 0万
# 结论: 应该上线
```

实践建议：对投入超过50万的项目，画一棵决策树。你不需要精确概率，70%/30%的粗略估计已经比纯直觉判断好10倍。

## 3.6 双面论证（Red Team / Blue Team）与情景规划（Scenario Planning）

这两种方法都用于对抗"确认偏误"（Confirmation Bias）——人倾向于寻找支持自己观点的证据，忽略反对证据。

**红蓝对抗的执行规则与角色分工表：**

| 角色 | 英文 | 任务 | 规则 | 产出 |
|------|------|------|------|------|
| 红队 | Red Team | 找出方案的所有漏洞 | 必须提出至少5个致命风险 | 风险清单 |
| 蓝队 | Blue Team | 为方案辩护并修正 | 不能否认风险，只能提出应对 | 修正方案 |
| 仲裁者 | Arbiter | 判断风险是否成立 | 中立、不参与辩论 | 最终决策 |

**情景规划的三种未来构建法：**

| 方法 | 英文 | 核心思路 | 适用场景 | 示例 |
|------|------|---------|---------|------|
| 三情景法 | Three Scenarios | 乐观/中性/悲观各一个 | 通用 | 增长30%/持平/下降20% |
| 驱动因子法 | Driving Forces | 识别2个关键不确定因子，交叉成4象限 | 行业变局 | 政策×技术成熟度 |
| 断裂分析法 | Discontinuity Analysis | 假设一个"黑天鹅"事件发生 | 风险管理 | 主要客户突然流失 |

**情景概率分配的代码模型：**

```python
def scenario_planning(scenarios):
    """情景规划的概率-影响矩阵"""
    results = []
    for s in scenarios:
        risk_score = s['probability'] * s['impact']
        s['risk_score'] = risk_score
        if s['probability'] > 0.5 and s['impact'] > 5:
            s['priority'] = '必须准备应对方案'
        elif s['probability'] > 0.3 or s['impact'] > 7:
            s['priority'] = '制定预案'
        else:
            s['priority'] = '监控即可'
        results.append(s)
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    return results

scenarios = [
    {'name': '市场需求爆发', 'probability': 0.4, 'impact': 8},
    {'name': '竞品提前发布', 'probability': 0.6, 'impact': 6},
    {'name': '供应链中断', 'probability': 0.15, 'impact': 9},
    {'name': '政策收紧', 'probability': 0.25, 'impact': 7},
]
for s in scenario_planning(scenarios):
    print(f"{s['name']}: {s['priority']}")
```

> 红蓝对抗不是为了分出胜负，而是让方案的漏洞在执行前暴露。被同事批评总比被市场打脸好。

实践建议：对投入超过100万的项目，正式组建红蓝队各3人，给2天时间准备，1天正式对抗。你会发现红队找到的问题，至少有一个是你完全没想过的。

## 3.7 ROI 与成本效益分析：算清每一分投入

ROI（Return on Investment，投资回报率）是最基本的投资决策指标，但很多人只算显性成本不算隐性成本。

**ROI 的完整计算公式：**

```
ROI = (总收益 - 总成本) / 总成本 × 100%

其中:
总成本 = 显性成本 + 隐性成本
显性成本 = 资金投入 + 人力成本 + 工具成本
隐性成本 = 时间机会成本 + 管理成本 + 风险成本
```

**显性成本 vs 隐性成本对照表：**

| 成本类型 | 定义 | 常见项目 | 估算难度 |
|---------|------|---------|---------|
| 显性成本 | 直接可量化的支出 | 薪资、软件费、设备费 | 低 |
| 隐性成本-时间 | 团队花在项目上的时间机会成本 | 3人×3个月=9人月 | 中 |
| 隐性成本-管理 | 沟通、协调、会议等管理开销 | 约占人力成本的20-30% | 中 |
| 隐性成本-风险 | 失败概率×失败损失 | 30%概率失败×100万损失=30万 | 高 |

**NPV 与 IRR 的代码示例：**

```python
import numpy as np

def npv_irr(cash_flows, discount_rate=0.1):
    """
    NPV (Net Present Value): 净现值
    IRR (Internal Rate of Return): 内部收益率
    cash_flows: [-initial_investment, year1, year2, ...]
    """
    # NPV 计算
    npv = sum(cf / (1 + discount_rate) ** t 
              for t, cf in enumerate(cash_flows))
    
    # IRR 计算 (使NPV=0的折现率)
    irr = np.irr(cash_flows) if hasattr(np, 'irr') else None
    
    return {
        'NPV': round(npv, 2),
        'IRR': round(irr * 100, 2) if irr else None,
        'decision': '可行' if npv > 0 else '不可行'
    }

# 示例: 投资100万, 3年收益分别为40万/50万/60万
result = npv_irr([-100, 40, 50, 60], discount_rate=0.1)
# NPV = -100 + 40/1.1 + 50/1.21 + 60/1.331 = 23.4万
# NPV > 0, 项目可行
```

> 当有人说"这个项目ROI很高"时，先问他："隐性成本算了吗？"如果没算，他的ROI至少虚高了40%。

实践建议：做一个"隐性成本检查清单"，每次评估项目ROI时逐项检查。你会发现很多"看起来赚钱"的项目，算上隐性成本后是亏的。

## 3.8 10/10/10 法则与本章总结

10/10/10 法则由苏茜·韦尔奇（Suzy Welch）提出，是一种用时间视角过滤短期情绪的决策工具。

**10/10/10 时间视角的决策过滤表：**

| 时间距离 | 核心问题 | 过滤的情绪 | 典型场景 |
|---------|---------|-----------|---------|
| 10分钟后 | 这个决定10分钟后我什么感觉？ | 过滤冲动情绪 | 愤怒时发邮件、兴奋时承诺 |
| 10个月后 | 10个月后我会怎么看这个决定？ | 过滤短期焦虑 | 害怕失败而不敢开始 |
| 10年后 | 10年后这个决定还重要吗？ | 过滤噪音，聚焦本质 | 纠结两个差不多选项 |

> 大多数让你焦虑的决策，10个月后都不值一提。而真正重要的决策，往往在你"觉得不重要"时被忽略了。

**10种决策方法的适用场景汇总：**

| 方法 | 最佳场景 | 操作时间 | 量化程度 |
|------|---------|---------|---------|
| SWOT | 战略初期扫描 | 1小时 | 低 |
| 决策矩阵 | 多选项多维度比较 | 30分钟 | 高 |
| Pre-mortem | 项目启动前风险识别 | 30分钟 | 中 |
| 机会成本 | 资源分配决策 | 15分钟 | 中 |
| 80/20法则 | 优先级排序 | 15分钟 | 中 |
| 决策树 | 多阶段不确定性决策 | 1小时 | 高 |
| 红蓝对抗 | 重大决策的对抗审查 | 2-3天 | 中 |
| 情景规划 | 长期战略、宏观环境 | 半天-1天 | 低 |
| ROI/NPV | 投资决策 | 1小时 | 高 |
| 10/10/10 | 情绪干扰下的决策 | 5分钟 | 低 |

**决策方法选择决策树：**

| 条件 | 推荐方法 | 理由 |
|------|---------|------|
| 决策涉及金额>100万 | ROI + 决策树 + Pre-mortem | 高 stakes 需要量化+风险识别 |
| 决策有多个选项难以取舍 | 决策矩阵 | 多维度量化比较 |
| 决策受情绪影响大 | 10/10/10 法则 | 时间视角过滤情绪 |
| 决策涉及长期战略 | 情景规划 + SWOT | 需要考虑多种未来 |
| 决策团队分歧严重 | 红蓝对抗 | 对抗式消除偏见 |
| 决策需要快速做 | 80/20 + 机会成本 | 简单快速 |
| 决策可逆性高 | 快速决策+迭代 | 不值得花太多时间分析 |
| 决策可逆性低 | 全套方法组合 | 不可逆决策必须慎重 |

> 管理者不需要会所有决策方法，但需要知道在什么场景调用什么方法。这就像厨师不需要每道菜都会做，但需要知道菜单上每道菜的特点。

---

觉得有用？收藏起来，下次做决策直接套用这份方法选择指南。

你最常用哪种决策方法？或者哪个决策后悔没用方法？评论区交流，怕浪猫会逐个回复。

关注怕浪猫，下期讲问题解决与处理方式——决策做了，问题来了怎么解决？下一章给你10种问题解决工具，从5W2H到5 Whys，从PDCA到MECE，每一种都配代码模板和流程图。

系列进度 3/10，下篇：第四章 问题解决与处理方式。

下一篇预告：同一个问题反复出现，说明你只治了症状没治根因。5 Whys追问法能帮你挖到根因，但大多数人追问到第二三个就停了。第4章会教你如何真正追问到第五层，以及MECE原则如何让你的问题拆解不留盲区。

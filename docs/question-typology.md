# 25 题样本的题型拆解与答案形态

数据来源：官方 starter kit 中的 `sample_qa.json`（25 题）。本文件只保留统计结论和改写后的题型描述，不复制官方题干、答案或评测语料。

## 1. 总览

| 维度 | 结果 |
|---|---|
| 总题数 | 25 |
| DONES (D) | 10 |
| AI Papers (P) | 15 |
| factual | 7 |
| comparative | 3 |
| procedural | 5 |
| causal | 6 |
| predictive | 4 |

D/P 交叉分布：DONES 的 procedural 最多（4 题），AI Papers 的 causal 最多（5 题）。这说明 DONES 域偏向“设备/流程/参数”，AI 论文域偏向“为什么/机制/因果解释”。

## 2. 一个重要事实修正

方案初稿写过“基准答案刻意简短”。读完官方 25 题后应修正为：

- 官方 sample 答案的长度范围约 **81–2677 字符**，中位数约 **672 字符**。
- `factual` 和 `causal` 的中位答案明显更长；`predictive` 和部分 `procedural` 题更短。
- 因此不能把所有答案压成一句话。**0/1 判分不等于短答案优先**，它意味着：
  1. 关键结论必须明确，不能只给“取决于……”；
  2. 数值、单位、机制名称要准确；
  3. 多部分因果题要覆盖关键链条；
  4. 但不要写与问题无关的背景、历史或泛泛介绍；
  5. 在 1 小时/100 题的硬预算下，长度要受到控制，优先保证结论和可判分事实。

一句话：**结论前置、证据最小充分、不要跑题；不是越短越好。**

## 3. 25 题覆盖表

说明：`D01–D10` 为 DONES 域，`P01–P15` 为 AI Papers 域。表中的“题目在问什么”和“理想答案形态”是根据题型做的抽象，不是对官方题干或答案的复制。

| 编号 | 域 | 官方类型 | 题目在问什么（抽象） | 理想答案形态 | 检索重点 |
|---|---|---|---|---|---|
| D01 | D | comparative | 两种束流成像机制的物理差异 | 先给唯一关键差异，再解释两边机制；用术语点名 | OTR / scintillation / energy deposition |
| D02 | D | factual | 破坏性束流诊断对束流的影响 | 直接定义“破坏性”，说明测后束流不能继续用于正常物理运行 | destructive diagnostic / beam interception |
| D03 | D | procedural | 半衰期取整后计算衰变常数 | 先写公式，再代数值，最后给单位和数量级 | half-life / decay constant / units |
| D04 | D | factual | 某核素何时不再是主要活度来源 | 给时间点/时间段和判断依据，避免只给单一数字 | Be-7 / heat exchanger / activity inventory |
| D05 | D | causal | 锂回路中两类放射性核素库存如何计算 | 列计算链条、输入量、假设和影响项；必要时分段 | Li loop / Be-7 / tritium / inventory |
| D06 | D | procedural | 主换热器的近似体积流量 | 直接给数值+单位，并说明口径/工况；有换算就展示 | heat exchanger / volumetric flow rate |
| D07 | D | predictive | 在线氮阱的温度 | 先给工况，再给温度值和单位；条件不同则分开写 | nitrogen trap / on-line / temperature |
| D08 | D | procedural | 锂回路某支路的旁通比 | 给比值定义、数值和适用支路；不要把相似支路混在一起 | ICS branch / bypass ratio |
| D09 | D | procedural | 主建筑体积 | 给数值、单位和“内部/总体”口径；需要时可给公式 | main building / volume / units |
| D10 | D | factual | 何条件下需要人工或遥操作维护 | 按辐射/活化条件分情况，说明 hands-on vs remote 的边界 | activation / dose rate / hands-on / remote handling |
| P01 | P | comparative | 两种离散 tokenizer 的架构差异 | 比较目标函数、离散化方式和适用任务；给因果解释 | RQ-VAE / RQ-KMeans / tokenizer |
| P02 | P | factual | 某方法实验比较是否公平、是否需要消融 | 先给立场，再给公平性依据、缺失消融和可能影响 | constraints / ablation / baseline |
| P03 | P | causal | 由定理条件推出空间的 lush 性质 | 按定理链条写出依赖关系，不跳步；把符号和条件对齐 | functional analysis / theorem / implication |
| P04 | P | causal | 某评价指标为何必须落在 0 到 1 | 说明归一化、可比性、稳定性和与优化目标的关系 | metric / normalization / ranking |
| P05 | P | predictive | 由序列长度启发式推算窗口大小 | 识别启发式公式/边界，代入给定长度并给数值 | window size / sequence length / heuristic |
| P06 | P | causal | 相对激活值为何提升分类准确率 | 先给机制，再连到分类边界/鲁棒性 | fuzzy cognitive map / relative activation |
| P07 | P | factual | 从权值知识研究稳定 FCM 覆盖的意义 | 用一小段总结研究对象、稳定性和权值约束 | FCM / covering / stability |
| P08 | P | factual | 某种公平性现象是否也在特定条件下出现 | 先回答“是/否/依条件”，再给适用条件和证据 | fairness / brute force / conditions |
| P09 | P | procedural | 某归一化加权机制及其数学定义 | 先命名机制，再写公式，最后解释防止溢出/支配 | normalization / overflow / component dominance |
| P10 | P | causal | 某生成器在零样本学习中的作用 | 直接说目的和它解决的具体问题，不需要背景综述 | representation generator / zero-shot |
| P11 | P | factual | 为什么某种统计检验适合方法比较 | 给检验对象、假设和优势，扣住实验设计 | Bayesian tests / comparisons / options |
| P12 | P | predictive | 固定数据增强的主要弱点 | 给弱点名称，再解释它导致的泛化/偏差后果 | augmentation / SimCLR |
| P13 | P | comparative | 两种拜占庭容错方法的差异 | 分维度比较假设、保证、代价和适用场景 | Byzantine resilience / assumptions |
| P14 | P | predictive | 加入主动学习后系统能力如何变化 | 先给变量/类型跃迁，再说明监督机制为什么满足条件 | GPAIS / active learning / taxonomy |
| P15 | P | causal | 线性时不变模型为何在选择性复制任务上困难 | 直接连到参数共享、时不变性和输入选择能力的冲突 | LTI / selective copying / Mamba |

## 4. 每类题的最优答题模板

### factual

- 第一句：**定义或数值结论**。
- 第二句：限定条件、单位或适用范围。
- 第三句：如果题目问“为什么/是否”，只补最小必要机制。
- 避免：写完整百科、从历史背景讲起、用模糊的“可能/通常”。

### comparative

- 第一句：**最关键的差异**，不要先分别介绍两边。
- 第二句：A 的机制/属性。
- 第三句：B 的机制/属性，明确指出两者差在哪。
- 如果题目问“谁更好”，必须给比较维度和条件，不能只给胜者。

### procedural

- 步骤化或公式化。
- 每个数值都给单位。
- 计算题先给公式，再代入，再给最终值。
- 如果文档有多个口径，写清用的是哪一个。

### causal

- 第一句给因果核心，不要先讲现象。
- 第二句给机制链条的 2–4 个关键节点。
- 第三句给边界条件或反例（仅在问题需要时）。
- 不要把所有相关背景都塞进去；0/1 判分只关心关键因果是否命中。

### predictive

- 先写“给定条件下”的结论。
- 再写公式/启发式/边界条件。
- 最后写数值、单位或分类结果。
- 如果题目没有给足条件，说明缺失量，但仍给出最可能的条件化答案。

## 5. 对代码和 prompt 的直接启示

1. 先做题型路由：`factual/comparative/procedural/causal/predictive` 不应共用完全相同的生成长度。
2. 对 procedural 和 predictive，提高数值/单位 token 的权重，并在 prompt 里要求“公式 + 单位 + 条件”。
3. 对 comparative，prompt 要求“先给差异，再分别解释”，避免模型先写两大段背景。
4. 对 causal，prompt 要求“最多 4 个因果节点”，避免长回答消耗时间。
5. 对 factual，允许直接给答案，但加一个“如果答案依赖某个口径，写出该口径”的检查。
6. 任何答案都要尽量绑定检索片段；没有证据的数字宁可不给，不能编造。

## 6. 数据安全

- 官方 sample 只用于本地分析，不进入公开仓库。
- 公开仓库只保存本文件中的统计、抽象化分类和公开来源链接。
- 最终提交代码与辅助文件必须遵守竞赛的 1 GB、无外网和每日提交限制。
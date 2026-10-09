# 检索、生成与 1 小时预算：可落地的管线建议

目标不是把官方 sample 刷到满分，而是在**固定模型、单 H100、无外网、1 小时总预算、0/1 判分**的条件下，尽量减少“检索没找到、答案跑偏、单位算错、生成超时”这四类失败。

## 建议 1：缩写与同义归一，必须在检索前做

DONES 语料中同一个对象常有多种写法：

- `DONES` / `IFMIF-DONES` / `International Fusion Materials Irradiation Facility – Demo Oriented Neutron Source`
- `HX` / `heat exchanger`
- `Be7` / `Be-7` / `beryllium-7`
- `D+` / `deuteron` / `deuterium ion`
- `RH` / `remote handling` / `remote maintenance`

实现建议：

1. 维护一个小型 alias 表（见 `docs/accelerator-glossary.md`）。
2. 检索前把 query 扩展到 canonical term + alias，而不是只做同义词替换。
3. 对“缩写可能多义”的情况保留原缩写，同时添加候选全称，避免强行消歧。
4. 对 AI Papers 域，保留论文标题、模型名、数据集名和任务名；不要做激进 stemming。

## 建议 2：不要只切片；保留章节、页码、表格和图注

纯滑动窗口会把表格拆坏，也会丢掉“这个数字属于哪个工况”的信息。建议把每个 chunk 附带：

- `source_file`
- `page`
- `section_heading`
- `element_type`（正文 / 表格 / 图注 / 公式）
- `caption`（若有）
- `chunk_id`

对 D 域，表格和图注往往就是数值题的答案来源；对 P 域，实验设置、消融和附录经常决定因果题是否答对。

## 建议 3：关键词检索 + 向量检索 + RRF，而不是二选一

- BM25/关键词：对缩写、设备名、型号、论文名、精确数字强。
- 向量检索：对同义表达、机制解释、长问题强。
- 融合：Reciprocal Rank Fusion（RRF）或加权 RRF，把两路排名合并。

一个可用的起步权重：

```text
score = 0.45 * BM25_rank + 0.55 * vector_rank
```

但不要在本地拍死权重。用官方 sample 的题型做路由，分别统计 factual / procedural / causal 的命中率，再调整。

## 建议 4：数值、单位和数量级单独校验

比赛里有大量“参数值 + 单位”的问题。建议做三层检查：

1. **抽取**：识别数字、科学计数法、百分号、时间和单位（MeV、mA、L/s、m³/h、Sv/h、dpa 等）。
2. **换算**：统一到 SI 或题目要求单位；特别注意 `m³`、`L`、`h`、`s` 的换算。
3. **数量级**：如果检索到的值相差 10³ 以上，回到原文确认是否是对应不同工况、不同支路或不同时间点。

Procedural 题的最优输出是：

```text
公式 -> 代入值 -> 单位 -> 最终结果 -> 适用条件
```

## 建议 5：答案必须绑定检索片段，禁止无证据补数字

- 生成时给每个片段标 `[Fragment n]`。
- Prompt 要求“先写关键结论，再写依据；数值必须来自片段”。
- 如果检索片段不足，允许输出条件化答案，但不要编具体数值。
- 对 comparative 题，要求模型先给差异，再分别展开。
- 对 causal 题，要求最多写 3–4 个因果节点，避免长回答拖垮时间。
- 对 Phase 2 的专家质量分，引用片段和明确假设会加分；但引用不能造假。

## 建议 6：1 小时预算要拆成四块，并留 10 分钟余量

官方硬限制是整个 run，不是只算生成时间。建议预算：

| 阶段 | 目标时间 | 说明 |
|---|---:|---|
| 模型加载 + tokenizer | 3–6 分钟 | 32B 权重和本地缓存加载 |
| PDF 解析 + 分块 | 8–18 分钟 | Docling 解析；不要开 OCR，除非确认是扫描件 |
| 向量编码 + 索引加载 | 3–8 分钟 | 如果可接受，尽量离线预先算好并打包索引 |
| 100 题检索 + 生成 + 解码 | 25–38 分钟 | 优先把 `max_new_tokens` 控制在 256–512，按题型动态调整 |
| 安全余量 | ≥10 分钟 | 处理坏 PDF、超长 context、CUDA/内存抖动 |

官方 starter kit 的 RAG 示例曾报告“全语料 + 50 题约 36 分钟”。隐藏评测要覆盖完整 100 题，所以不能把这 36 分钟当成 100 题的安全预算。真正提交前必须在官方 H100 环境跑一次完整队列，并记录每个阶段耗时。

## 建议 7：领域路由能省时间，也能减少跨域幻觉

先用轻量规则/分类器判断问题属于 D 还是 P：

- D 域关键词：DONES、Li loop、RFQ、beam、target、tritium、Be-7、dose、remote handling。
- P 域关键词：paper、model、baseline、ablation、benchmark、theorem、dataset、framework。

路由后可做两件事：

1. 只在对应域排名靠前的 chunks 中优先选择；
2. 使用不同 prompt：D 域强调单位/工况/设备名，P 域强调论文名/方法名/实验条件。

注意：路由错了比不路由更危险。路由只作为排序先验，不作为硬过滤，至少保留跨域召回兜底。

## 建议 8：把“技术创新 40%”做成可验证机制，而不是形容词

Phase 2 明确把技术创新放在 40% 权重。可以在不破坏 1 小时预算的前提下做这些事：

- **PEFT/轻量适配**：离线训练一个小 adapter，运行时只加载 adapter；但必须先确认固定模型与依赖版本允许。
- **知识图谱增强**：把 DONES 的系统—部件—参数—关系抽成小图，用于 query expansion 和证据重排。
- **动态知识融合**：按问题类型调整 BM25/向量/结构化的权重，而不是全题固定一套。
- **不确定性建模**：对检索分歧、单位冲突、多个候选值给出置信度和条件化答案。
- **题型感知解码**：factual 短答、causal 分节点、procedural 公式化，共享一个模型但使用不同 prompt/长度策略。

这些机制的共同要求是：**能在 4 页方法说明里画清楚，能在代码里复现，能说明为什么它提高了准确率或效率。**

## 建议 9：建立自己的离线评测集，但要遵守数据边界

- 官方 sample 可用来做本地调试，但不要复制进公开仓库。
- 可以用公开的 IFMIF-DONES 资料和 AI 论文自己出题，形成小型 dev set；题目和答案的来源要可追踪。
- 评测时至少看四个指标：总体 0/1 准确率、D/P 分域准确率、平均延迟、超时/解析失败率。
- 不要只优化总体准确率，官方排名使用 D/P 平衡准确率；小域的一题可能比大域的一题更值钱。

## 建议 10：提交包要做成“可在无网环境重启”的确定性系统

检查清单：

- 所有模型、adapter、embedding 和索引都在提交包内；
- 不依赖网络下载、外部缓存或临时目录；
- 处理 PDF 解析失败的 fallback；
- `answer()` 永远返回字符串；
- 记录耗时和异常，但不要把超长日志写进结果；
- 1 GB 限制下压缩权重和索引；
- 每天只有 1 次提交，先本地语法/接口测试，再占用正式额度。

## 参考

- [官方 Join the Challenge](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/join-the-challenge/)
- [官方 Evaluation](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/evaluation/)
- [官方 Starter Kit](https://github.com/jucls/IEEE-CIS-DSQA-Starter-Kit)
- [IFMIF/EVEDA Accelerator Facility](https://www.ifmif.org/accelerator-facility/)
- [IFMIF-DONES Facility](https://ifmif-dones.es/dones-program/dones-facility/)
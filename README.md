# ifmif-dones-domain-qa

面向 **IEEE CIS Technical Challenge on Domain-Specific Question Answering with LLMs** 的个人申请与预研交付包。

这份仓库不是获奖方案，也不是对官方评测结果的承诺。它只做三件事：

1. 把比赛约束、领域知识、题型与提交风险讲清楚；
2. 给出一套可以在官方环境继续迭代的最小 RAG 基线；
3. 用可核验的材料证明：申请人能在高年级团队里承担 DONES 领域、数据、评测和文档工作。

## 比赛硬约束

- 两个目标域：`D = IFMIF-DONES` 粒子加速器设施；`P = AI research papers`。
- 固定模型：`OLMo 3.1 32B Instruct`。
- 评测环境：单张 H100，整场运行 wall-clock **1 小时**，覆盖模型/索引加载、预处理和全部问题推理。
- 无外网；提交包 ≤ **1 GB**；每个团队每天最多提交 **1 次**。
- 最终提交包含推理代码、辅助文件，以及 **4 页 IEEE 格式**方法说明。
- Phase 1：隐藏 LLM-as-judge 对每题给 **0/1**，无部分分；按 D/P 平衡准确率排名；同分时总推理时间短者优先。
- Phase 2：`30%` 平衡准确率 + `30%` 专家质量评估 + `40%` 技术创新。创新评审明确关注 CI 方法的恰当使用与整体方案原创性。

官方口径以 [Join the Challenge](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/join-the-challenge/)、[Evaluation](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/evaluation/) 和 [Timeline](https://cis.taskforce.ieee.org/gpais/tc-domain-qa-llms/timeline/) 为准。

## 目录

- [`docs/accelerator-glossary.md`](docs/accelerator-glossary.md)：≥45 条 IFMIF-DONES / 加速器术语，中英对照，并注明知识点为何可能被出题。
- [`docs/question-typology.md`](docs/question-typology.md)：对官方 25 题样本做类别统计与答案形态拆解，不复制官方题目/答案。
- [`docs/retrieval-notes.md`](docs/retrieval-notes.md)：关键词+向量混合检索、缩写归一、表格/单位校验、溯源和 1 小时预算建议。
- [`code/main.py`](code/main.py)：面向官方提交接口的最小 RAG 基线。
- [`code/smoke_test.py`](code/smoke_test.py)：不依赖 GPU 的管线冒烟测试。
- [`docs/sources.md`](docs/sources.md)：官方竞赛、IFMIF-DONES、加速器和实验室来源。
- [`email/email-draft.md`](email/email-draft.md)：给刘泽阳老师的申请邮件草稿。
- [`email/resume-1page.md`](email/resume-1page.md)：1 页中文简历源文件，个人信息占位待本人补齐。
- [`email/resume-1page.docx`](email/resume-1page.docx)：可由 Word 打开/另存 PDF 的占位版 1 页简历。
- [`scripts/verify_deliverables.py`](scripts/verify_deliverables.py)：验收硬指标检查脚本。

## 不放进仓库的东西

- 官方 sample 题目、答案或评测语料；
- 下载的 32B 模型权重；
- 任何未公开的论文、私有数据或泄露代码。

官方的 25 题 sample 只用于本地统计和验证，仓库里只保留汇总结论与公开链接。参赛前请以官方 starter kit 和 Codabench 规则为准。

## 本地冒烟

```bash
python code/smoke_test.py
python -m py_compile code/main.py
```

详细说明见 [`code/README.md`](code/README.md)。

## 当前状态

- [x] 比赛事实与时间线核对
- [x] 45+ 条加速器术语
- [x] 25 题题型统计与答案形态分析
- [x] 5+ 条检索/评测管线建议
- [x] 代码骨架与无 GPU 冒烟测试
- [ ] 在官方 32B / 单 H100 环境实测
- [ ] 补齐姓名、学号、邮箱、GitHub 地址
- [ ] 公开发布并推送 GitHub

**诚实声明：** 当前代码的完整大模型推理路径尚未在 32B / 单 H100 官方环境验证。本地只验证了文本归一化、分块、排序融合、上下文拼接和接口形状。任何“已跑通 32B”的表述都必须等官方环境截图或日志出来后再写。

## License

代码采用 MIT License；仓库内第三方名称、链接与引用归原权利人所有。若继续分发官方 starter kit 的派生代码，请保留相应 MIT attribution。
# 代码说明

`main.py` 提供官方 starter kit 形状的入口：

```python
def answer(question: str, corpus_dir: str, model_id: str) -> str:
    ...
```

## 当前实现

1. 用 Docling 解析 `corpus_dir/*.pdf`；
2. 按段落分块，保留文件名等来源元数据；
3. 用纯 Python BM25 做关键词召回；
4. 用本地 bundled `sentence-transformers` 模型做向量召回；
5. 用 weighted RRF 融合两路排名；
6. 把 top chunks 压缩到 token 预算内；
7. 通过固定的 `OLMo 3.1 32B Instruct` 生成短而证据约束的答案。

## 为什么先做这个基线

- 关键词对缩写、设备名、论文名和数字强；
- 向量对同义表达和解释性问法强；
- RRF 比直接把两路分数相加更稳，不需要先校准 BM25 和 cosine 的尺度；
- 题型 prompt 让 factual / comparative / procedural / causal 输出不同形状；
- 先保证接口、索引、超时和单位，再谈 PEFT / 知识图谱等创新。

## 本地冒烟

```bash
python code/smoke_test.py
python -m py_compile code/main.py
```

冒烟测试不需要 GPU，也不会下载模型。它只验证：

- Unicode / 缩写归一；
- 段落分块；
- BM25 排序；
- RRF 融合；
- 上下文 token 预算；
- chat messages 形状。

## 官方环境路径尚未验证

当前开发机没有独显，不能加载 32B 模型。以下项目必须在官方 H100 环境或等价环境中另行验证：

- `OLMo 3.1 32B Instruct` 的实际 `model_id` 与权重缓存；
- Docling 对完整 corpus 的解析时间；
- 100 题的总生成时间；
- 1 GB 提交包是否容纳所有模型/索引；
- `transformers` 版本、`dtype`、`device_map` 和 `pad_token_id` 的组合。

因此本仓库只声明“接口和预处理管线本地冒烟通过”，**不声明 32B / H100 已跑通**。

## 调参入口

可用环境变量：

| 变量 | 默认值 | 用途 |
|---|---:|---|
| `DSQA_CHUNK_CHARS` | 900 | 分块字符数 |
| `DSQA_CHUNK_OVERLAP` | 120 | 分块重叠 |
| `DSQA_MAX_CONTEXT_TOKENS` | 6000 | 提示上下文预算 |
| `DSQA_MAX_NEW_TOKENS` | 320 | 每题最大生成 token |
| `DSQA_BM25_WEIGHT` | 0.45 | BM25 的 RRF 权重 |
| `DSQA_VECTOR_WEIGHT` | 0.55 | 向量检索的 RRF 权重 |
| `DSQA_EMBED_MODEL` | `code/embed_model` | 本地 embedding 模型路径 |
| `DSQA_DOCLING_MODELS` | `code/docling_models` | Docling artifacts 路径 |

## 与官方 starter kit 的关系

官方 starter kit 采用 MIT License。本项目借鉴其公开接口和“离线打包模型/索引”的设计，并保留独立的实现与说明。若复用 starter kit 的具体代码片段，请在 `THIRD_PARTY_NOTICES.md` 中保留 attribution。

## 下一步改进顺序

1. 在官方环境记录各阶段耗时；
2. 把 Docling 的 section/table/figure metadata 接入 `Chunk`；
3. 针对 procedural 题加入单位和数量级校验；
4. 用 25 题 sample 做本地检索命中率统计，但不把 sample 发布到仓库；
5. 最后才考虑 PEFT、知识图谱或动态融合等创新项。
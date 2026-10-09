# 脚本

- `analyze_sample.py`：读取官方 25 题 sample，只输出计数和答案长度统计，不复制题干/答案。
- `verify_deliverables.py`：检查术语条数、25 题覆盖、建议条数、代码文件和“未复制 sample”约束。
- `make_resume_docx.py`：用 Python 标准库生成占位版 `email/resume-1page.docx`。

示例：

```bash
python scripts/analyze_sample.py /path/to/sample_qa.json
python scripts/verify_deliverables.py
python scripts/make_resume_docx.py
```
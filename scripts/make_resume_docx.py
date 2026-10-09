"""Build a minimal one-page DOCX resume without external dependencies.

The output intentionally keeps placeholders such as [姓名] so the applicant can
fill them in before sending. It is a convenience artifact, not a fabricated
identity document.
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

OUT = Path(__file__).resolve().parents[1] / "email" / "resume-1page.docx"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(text: str, *, bold: bool = False, size: int = 18, before: int = 0, after: int = 50, color: str = "111111") -> str:
    rpr = f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Microsoft YaHei"/><w:sz w:val="{size}"/><w:color w:val="{color}"/>' + ("<w:b/>" if bold else "") + "</w:rPr>"
    return (
        "<w:p><w:pPr>"
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="250" w:lineRule="auto"/>'
        "</w:pPr>"
        f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'
    )


def heading(text: str) -> str:
    return para(text, bold=True, size=24, before=90, after=45)


def bullet(text: str) -> str:
    return para("• " + text, size=18, after=25)


def build_document() -> str:
    paragraphs = [
        para("[姓名]", bold=True, size=38, after=30),
        para("山东大学人工智能学院 · 2026 级本科生 ｜ 手机：[手机号] ｜ 邮箱：[邮箱] ｜ GitHub：[GitHub 账号] ｜ 学号：[学号]", size=16, after=80, color="444444"),
        heading("教育经历"),
        para("山东大学 · 人工智能学院｜本科 2026 级｜济南", bold=True),
        bullet("当前绩点/排名：[待填]"),
        bullet("英语：高考 139/150；阅读、听力、语法为强项，写作与口语正在补强。"),
        bullet("在学：Karpathy micrograd、Gilbert Strang 线代、C 语言程序设计。"),
        heading("竞赛与科研基础"),
        para("物理竞赛省二｜粒子加速器建模", bold=True),
        bullet("高二获物理竞赛省级二等奖；高三继续学习一年，暑假退出竞赛。"),
        bullet("接触四大力学并做过粒子加速器相关模型；旧笔记在杭州家中，寄到济南后可补充。"),
        bullet("对束流、靶、辐射与工程参数有基本物理直觉，正在用 IFMIF-DONES 公开资料重建术语与系统图景。"),
        heading("项目经历"),
        para("足球数据平台｜FastAPI + Vue3 + MySQL", bold=True),
        bullet("使用 AI 协作开发，本人负责需求拆解、接口/页面验收和部署排障，而不是只挂名。"),
        bullet("完成球员与逐场名单查询，持续迭代数据抓取与展示模块，使用 Git/GitHub 工作流。"),
        para("RAG 预研交付物｜IEEE CIS Domain-Specific QA 挑战", bold=True),
        bullet("整理 70 条 IFMIF-DONES 加速器术语（中英对照 + 出题理由）。"),
        bullet("对官方 25 题 sample 做题型统计与答案形态拆解，不复制官方数据到公开仓库。"),
        bullet("写出 10 条检索/评测管线建议，并实现关键词 BM25 + 向量召回 + RRF 的最小基线。"),
        bullet("本地无 GPU 冒烟通过；明确标注未在 32B/H100 环境验证。"),
        heading("技能"),
        bullet("编程：Python、C（在学）、Git、FastAPI、Vue3、MySQL。"),
        bullet("AI：RAG 基本管线、检索/评测意识，正在补 Transformer 与 LLM 工程。"),
        bullet("语言：中文母语；英语阅读/听力强，写作与口语在补。"),
        bullet("领域：粒子物理/加速器基础、物理建模、技术文档整理。"),
        heading("申请方向与可承担角色"),
        bullet("目标：参与 IEEE CIS Domain-Specific QA with LLMs，承担 DONES 领域、数据与评测、术语库、文档写作。"),
        bullet("可投入：期中周以外每周 6–8 小时；11/12 体测、11/16 期中、12 月期末不为比赛让路。"),
        bullet("诚实说明：没有 LLM 工程经验，但能在明确任务下快速学习，并已交付可核验的预研材料。"),
        heading("证明材料"),
        bullet("公开仓库：[GitHub 仓库链接]"),
        bullet("物竞证书/加速器旧笔记：[待补]"),
        bullet("足球平台仓库/截图：[待补]"),
    ]
    body = "".join(paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        f'{body}'
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="680" w:right="737" w:bottom="680" w:left="737" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    core = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>中文简历（占位版）</dc:title><dc:creator>[姓名]</dc:creator></cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex</Application></Properties>'''
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", build_document())
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    print(OUT)


if __name__ == "__main__":
    main()
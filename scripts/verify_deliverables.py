"""Validate the public deliverables required by the application plan."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def count_glossary_entries(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\|\s*\d+\s*\|", text, flags=re.MULTILINE))


def main() -> None:
    checks: list[tuple[str, bool, str]] = []
    glossary = ROOT / "docs" / "accelerator-glossary.md"
    typology = ROOT / "docs" / "question-typology.md"
    retrieval = ROOT / "docs" / "retrieval-notes.md"
    main_py = ROOT / "code" / "main.py"
    smoke_py = ROOT / "code" / "smoke_test.py"
    email_body = ROOT / "email" / "email-body.txt"
    resume_docx = ROOT / "email" / "resume-1page.docx"

    glossary_count = count_glossary_entries(glossary) if glossary.exists() else 0
    checks.append(("glossary >= 40 entries", glossary_count >= 40, str(glossary_count)))

    typology_text = typology.read_text(encoding="utf-8") if typology.exists() else ""
    typology_rows = len(re.findall(r"^\|\s*(?:D|P)\d{2}\s*\|", typology_text, flags=re.MULTILINE))
    checks.append(("typology covers 25 rows", typology_rows == 25, str(typology_rows)))
    for qtype in ["factual", "comparative", "procedural", "causal", "predictive"]:
        checks.append((f"typology includes {qtype}", qtype in typology_text, ""))

    retrieval_text = retrieval.read_text(encoding="utf-8") if retrieval.exists() else ""
    advice_count = len(re.findall(r"^## 建议 \d+", retrieval_text, flags=re.MULTILINE))
    checks.append(("retrieval advice >= 5", advice_count >= 5, str(advice_count)))
    checks.append(("code main.py exists", main_py.exists(), str(main_py)))
    checks.append(("smoke_test.py exists", smoke_py.exists(), str(smoke_py)))
    checks.append(("no sample_qa.json copied", not list(ROOT.rglob("sample_qa.json")), ""))
    email_text = email_body.read_text(encoding="utf-8") if email_body.exists() else ""
    checks.append(("email body <= 400 chars", 0 < len(email_text) <= 400, str(len(email_text))))
    checks.append(("resume docx exists", resume_docx.exists(), str(resume_docx.stat().st_size if resume_docx.exists() else 0)))

    failed = False
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
        failed = failed or not ok
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
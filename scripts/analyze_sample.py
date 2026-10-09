"""Summarize the official 25-question sample without copying its content.

Example:
    python scripts/analyze_sample.py path/to/sample_qa.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    args = parser.parse_args()

    data = json.loads(args.sample.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("sample must be a JSON list")

    domains = Counter(item["domain"] for item in data)
    types = Counter(item["question_type"] for item in data)
    cross = Counter((item["domain"], item["question_type"]) for item in data)
    lengths = [len(item["answer"]) for item in data]

    report = {
        "count": len(data),
        "domains": dict(domains),
        "types": dict(types),
        "cross": {f"{domain}/{qtype}": count for (domain, qtype), count in sorted(cross.items())},
        "answer_chars": {
            "min": min(lengths),
            "max": max(lengths),
            "median": statistics.median(lengths),
            "mean": round(statistics.mean(lengths), 1),
        },
        "answer_chars_by_type": {
            qtype: {
                "count": len([x for x in data if x["question_type"] == qtype]),
                "median": statistics.median([len(x["answer"]) for x in data if x["question_type"] == qtype]),
                "min": min(len(x["answer"]) for x in data if x["question_type"] == qtype),
                "max": max(len(x["answer"]) for x in data if x["question_type"] == qtype),
            }
            for qtype in sorted(types)
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
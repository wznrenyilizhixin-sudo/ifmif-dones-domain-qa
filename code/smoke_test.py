"""No-GPU smoke test for the retrieval-to-prompt pipeline.

This does not load a language model. It checks the deterministic parts that
usually break first: normalization, query expansion, chunking, BM25, RRF,
context packing, and prompt construction.
"""

from __future__ import annotations

import json
import re

from main import (
    Chunk,
    bm25_rank,
    build_context,
    build_messages,
    chunk_markdown,
    expand_query,
    normalize_text,
    reciprocal_rank_fusion,
)


class SimpleTokenizer:
    def encode(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9-]+|[\u4e00-\u9fff]", text.lower())


def main() -> None:
    chunks = [
        Chunk("The lithium loop circulates liquid lithium and includes a heat exchanger.", "dones.pdf", 10),
        Chunk("OTR is an electromagnetic boundary effect and does not require energy deposition.", "diagnostics.pdf", 3),
        Chunk("Scintillation requires energy deposition in a material and then emits photons.", "diagnostics.pdf", 4),
        Chunk("Be-7 accumulates in the lithium loop and decays with a known half-life.", "activation.pdf", 7),
    ]

    expanded = expand_query("Compare OTR and scintillation; what is the Li loop HX role?")
    assert "optical transition radiation" in expanded.lower()
    assert "heat exchanger" in expanded.lower()
    assert normalize_text("  A\u00a0 B  ") == "A B"

    parts = chunk_markdown("Paragraph one.\n\nParagraph two with a number 42.\n\nParagraph three.", chunk_chars=45, overlap=8)
    assert parts and all(isinstance(p, str) for p in parts)

    lexical = bm25_rank("OTR scintillation energy deposition", chunks)
    semantic_stub = [2, 1, 0, 3]
    fused = reciprocal_rank_fusion([lexical, semantic_stub], weights=[0.45, 0.55])
    assert sorted(fused) == [0, 1, 2, 3]

    tokenizer = SimpleTokenizer()
    context = build_context("Compare OTR and scintillation", chunks, fused, tokenizer, max_tokens=80)
    assert "[Fragment 1" in context
    assert "OTR" in context or "Scintillation" in context

    messages = build_messages("Compare OTR and scintillation", context)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"].strip()
    assert "Use the fragments below as the evidence base" in messages[1]["content"]

    print(json.dumps({
        "ok": True,
        "expanded_query": expanded,
        "chunks_after_chunking": len(parts),
        "lexical_top": lexical[:2],
        "fused_top": fused[:2],
        "context_chars": len(context),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
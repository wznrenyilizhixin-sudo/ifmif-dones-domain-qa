"""
Hybrid RAG baseline for the IEEE CIS Domain-Specific QA challenge.

This is intentionally a *baseline*: it keeps the official answer() contract,
uses only packages listed by the challenge, and keeps no network dependency at
inference time. The architecture is inspired by the official MIT-licensed
starter kit; this file is an independent implementation focused on:
  - abbreviation normalization and query expansion;
  - lexical BM25 + dense embedding retrieval;
  - reciprocal-rank fusion (RRF);
  - compact, evidence-bound prompts;
  - a deterministic one-hour-friendly generation path.

Local smoke testing is handled by smoke_test.py. The full 32B/H100 path has
not been verified on the author's laptop.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHUNK_CHARS = int(os.getenv("DSQA_CHUNK_CHARS", "900"))
CHUNK_OVERLAP = int(os.getenv("DSQA_CHUNK_OVERLAP", "120"))
MAX_CONTEXT_TOKENS = int(os.getenv("DSQA_MAX_CONTEXT_TOKENS", "6000"))
MAX_NEW_TOKENS = int(os.getenv("DSQA_MAX_NEW_TOKENS", "320"))
BM25_WEIGHT = float(os.getenv("DSQA_BM25_WEIGHT", "0.45"))
VECTOR_WEIGHT = float(os.getenv("DSQA_VECTOR_WEIGHT", "0.55"))

ALIASES = {
    "dones": "ifmif-dones international fusion materials irradiation facility demo oriented neutron source",
    "ifmif dones": "ifmif-dones international fusion materials irradiation facility demo oriented neutron source",
    "hx": "heat exchanger",
    "li loop": "lithium loop liquid lithium loop",
    "be7": "be-7 beryllium-7",
    "be-7": "be-7 beryllium-7",
    "d+": "deuteron deuterium ion",
    "rh": "remote handling remote maintenance",
    "dpa": "displacement per atom displacements per atom",
    "otr": "optical transition radiation",
    "bpm": "beam position monitor",
    "hwr": "half-wave resonator",
    "mebt": "medium energy beam transport",
    "rfq": "radio frequency quadrupole",
    "srf": "superconducting radio frequency",
}

BASE_SYSTEM_PROMPT = (
    "You are a scientific question-answering system for the IEEE CIS "
    "Domain-Specific QA challenge. Answer the question using only the supplied "
    "corpus fragments. Put the key conclusion in the first sentence. Preserve "
    "exact names, acronyms, numbers, units, and conditions. Do not invent a "
    "fact that is not supported by the fragments. If fragments conflict or are "
    "insufficient, state the uncertainty and give the best condition-qualified "
    "answer. Do not add generic background."
)

PROCEDURAL_SYSTEM_PROMPT = (
    "You are answering a procedural or numerical scientific question. Use this "
    "shape: formula/definition, substituted values, unit, final result, and "
    "applicable condition. Keep the answer compact and verify unit conversions."
)

CAUSAL_SYSTEM_PROMPT = (
    "You are answering a causal scientific question. Give the causal conclusion "
    "first, then at most four concise mechanism steps. Do not pad the answer "
    "with history or unrelated background."
)

COMPARATIVE_SYSTEM_PROMPT = (
    "You are answering a comparative scientific question. State the decisive "
    "difference first, then explain each side only enough to justify the "
    "comparison. Name the exact mechanisms or properties being compared."
)


# ---------------------------------------------------------------------------
# Text utilities and retrieval
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chunk:
    """A retrievable text unit with provenance metadata."""

    text: str
    source: str = ""
    page: int | None = None
    section: str = ""
    element_type: str = "text"


def normalize_text(text: str) -> str:
    """Normalize unicode and whitespace without destroying acronyms or units."""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00a0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    """A dependency-free tokenizer suitable for BM25 and query expansion."""

    text = normalize_text(text).lower()
    # Keep Latin words, acronyms, numbers and decimal/scientific notation.
    return re.findall(r"[a-z][a-z0-9._+\-]*|\d+(?:\.\d+)?(?:e[+-]?\d+)?|[\u4e00-\u9fff]", text)


def expand_query(question: str) -> str:
    """Append canonical aliases for known domain abbreviations."""

    lowered = " " + normalize_text(question).lower() + " "
    extra: list[str] = []
    for alias, canonical in ALIASES.items():
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        if re.search(pattern, lowered):
            extra.append(canonical)
    if not extra:
        return question
    return f"{question}\n\nCanonical aliases: {'; '.join(extra)}"


def chunk_markdown(text: str, chunk_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Greedily pack paragraphs into chunks while preserving paragraph boundaries."""

    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if overlap < 0 or overlap >= chunk_chars:
        raise ValueError("overlap must be in [0, chunk_chars)")

    text = normalize_text(text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        # Very long paragraphs are split with overlap rather than dropped.
        if len(para) > chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(para):
                end = min(start + chunk_chars, len(para))
                chunks.append(para[start:end])
                if end == len(para):
                    break
                start = max(end - overlap, start + 1)
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if current and overlap else ""
            current = f"{tail}\n\n{para}" if tail else para

    if current:
        chunks.append(current)
    return chunks


def bm25_rank(question: str, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75) -> list[int]:
    """Return chunk indices ranked by a compact BM25 implementation."""

    query_terms = tokenize(expand_query(question))
    if not query_terms or not chunks:
        return list(range(len(chunks)))

    docs = [tokenize(c.text) for c in chunks]
    doc_freq: Counter[str] = Counter()
    for doc in docs:
        doc_freq.update(set(doc))
    avgdl = sum(len(d) for d in docs) / max(len(docs), 1)
    n_docs = len(docs)
    scores: list[tuple[float, int]] = []

    for i, doc in enumerate(docs):
        counts = Counter(doc)
        dl = len(doc)
        score = 0.0
        for term in query_terms:
            if term not in counts:
                continue
            df = doc_freq[term]
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            tf = counts[term]
            denom = tf + k1 * (1.0 - b + b * dl / max(avgdl, 1e-9))
            score += idf * (tf * (k1 + 1.0)) / max(denom, 1e-9)
        scores.append((score, i))

    scores.sort(key=lambda item: (-item[0], item[1]))
    return [i for _, i in scores]


def semantic_rank(question: str, chunks: Sequence[Chunk], embeddings: Any, embedder: Any) -> list[int]:
    """Return chunk indices by cosine similarity using a local embedder."""

    if len(chunks) == 0:
        return []
    query = expand_query(question)
    q = embedder.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    scores = embeddings @ q
    order = sorted(range(len(chunks)), key=lambda i: (-float(scores[i]), i))
    return order


def reciprocal_rank_fusion(rankings: Iterable[Sequence[int]], weights: Sequence[float] | None = None, k: int = 60) -> list[int]:
    """Fuse multiple ranked index lists with weighted reciprocal-rank fusion."""

    rankings = [list(r) for r in rankings]
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("weights and rankings must have the same length")

    scores: dict[int, float] = {}
    for ranking, weight in zip(rankings, weights):
        for rank, index in enumerate(ranking):
            scores[index] = scores.get(index, 0.0) + weight / (k + rank + 1)
    return sorted(scores, key=lambda idx: (-scores[idx], idx))


def _count_tokens(tokenizer: Any, text: str) -> int:
    """Count tokens when a real tokenizer is available, otherwise approximate."""

    try:
        return len(tokenizer.encode(text))
    except Exception:
        # Conservative fallback: Chinese characters are roughly one token each;
        # Latin text is roughly four characters per token.
        cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
        return cjk + max(1, (len(text) - cjk + 3) // 4)


def build_context(
    question: str,
    chunks: Sequence[Chunk],
    ranked_indices: Sequence[int],
    tokenizer: Any,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> str:
    """Pack top-ranked chunks into a token-budgeted, provenance-labelled context."""

    selected: list[Chunk] = []
    used = 0
    for idx in ranked_indices:
        if idx < 0 or idx >= len(chunks):
            continue
        chunk = chunks[idx]
        n_tokens = _count_tokens(tokenizer, chunk.text)
        if used + n_tokens <= max_tokens:
            selected.append(chunk)
            used += n_tokens
            continue
        if not selected and n_tokens > 0:
            # Keep a safe prefix of the best chunk if it alone is too large.
            ratio = max_tokens / n_tokens
            cut = max(1, int(len(chunk.text) * ratio))
            selected.append(Chunk(chunk.text[:cut], chunk.source, chunk.page, chunk.section, chunk.element_type))
            used = _count_tokens(tokenizer, selected[-1].text)
        if used >= max_tokens:
            break

    if not selected:
        return "No retrieved fragments were available."

    parts = []
    for i, chunk in enumerate(selected, 1):
        provenance = chunk.source or "unknown source"
        if chunk.page is not None:
            provenance += f", page {chunk.page}"
        if chunk.section:
            provenance += f", section {chunk.section}"
        parts.append(f"[Fragment {i} | {provenance}]\n{chunk.text}")
    return "\n\n".join(parts)


def _domain_system_prompt(question: str, qtype: str | None = None) -> str:
    """Select a compact prompt without hard-filtering retrieval by domain."""

    lowered = normalize_text(question).lower()
    if qtype == "procedural" or re.search(r"\b(what|calculate|rate|ratio|volume|flow|temperature|time)\b", lowered):
        return PROCEDURAL_SYSTEM_PROMPT
    if qtype == "causal" or "why" in lowered or "how" in lowered:
        return CAUSAL_SYSTEM_PROMPT
    if qtype == "comparative" or "difference" in lowered or "compare" in lowered:
        return COMPARATIVE_SYSTEM_PROMPT
    return BASE_SYSTEM_PROMPT


def build_messages(question: str, context: str, qtype: str | None = None) -> list[dict[str, str]]:
    """Build chat messages for the fixed instruction model."""

    system_prompt = _domain_system_prompt(question, qtype)
    user_prompt = (
        "Use the fragments below as the evidence base.\n\n"
        f"{context}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer with the key conclusion first. Keep exact names, numbers and "
        "units. Do not cite a fragment that does not support the statement."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# ---------------------------------------------------------------------------
# Heavy imports are lazy so smoke_test.py can run without torch/docling.
# ---------------------------------------------------------------------------

def _docling_converter():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    model_dir = Path(os.getenv("DSQA_DOCLING_MODELS", str(Path(__file__).parent / "docling_models")))
    do_table_structure = os.getenv("DSQA_TABLE_STRUCTURE", "0") == "1"
    options = PdfPipelineOptions(
        artifacts_path=str(model_dir) if model_dir.exists() else None,
        do_ocr=os.getenv("DSQA_DO_OCR", "0") == "1",
        do_table_structure=do_table_structure,
    )
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})


def _build_index(corpus_dir: str, embed_model_path: str):
    """Parse PDFs, chunk text, and encode chunks with a bundled local model."""

    import numpy as np
    from sentence_transformers import SentenceTransformer

    corpus_path = Path(corpus_dir)
    if not corpus_path.exists():
        raise FileNotFoundError(f"corpus_dir does not exist: {corpus_dir}")

    embed_path = Path(embed_model_path)
    if not embed_path.exists():
        raise FileNotFoundError(
            f"Bundled embedding model not found: {embed_path}. "
            "Build the submission with the official starter kit or set DSQA_EMBED_MODEL."
        )

    converter = _docling_converter()
    embedder = SentenceTransformer(str(embed_path), device="cpu")
    chunks: list[Chunk] = []

    for pdf_path in sorted(corpus_path.glob("*.pdf")):
        try:
            result = converter.convert(str(pdf_path))
            markdown = result.document.export_to_markdown()
        except Exception as exc:  # one malformed PDF must not kill the run
            print(f"[dsqa] skipping {pdf_path.name}: {exc}")
            continue
        for text in chunk_markdown(markdown):
            chunks.append(Chunk(text=text, source=pdf_path.name, element_type="text"))

    if not chunks:
        raise RuntimeError(f"No PDF text chunks found in {corpus_dir}")

    embeddings = embedder.encode(
        [c.text for c in chunks],
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=64,
    )
    return chunks, np.asarray(embeddings, dtype="float32"), embedder


_INDEX_CACHE: dict[str, tuple[list[Chunk], Any, Any]] = {}
_MODEL_CACHE: dict[str, tuple[Any, Any]] = {}


def _load_index(corpus_dir: str) -> tuple[list[Chunk], Any, Any]:
    key = str(Path(corpus_dir).resolve())
    if key not in _INDEX_CACHE:
        embed_model = os.getenv("DSQA_EMBED_MODEL", str(Path(__file__).parent / "embed_model"))
        _INDEX_CACHE[key] = _build_index(corpus_dir, embed_model)
    return _INDEX_CACHE[key]


def _load_model(model_id: str):
    if model_id in _MODEL_CACHE:
        return _MODEL_CACHE[model_id]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        device_map="cuda",
    )
    model.eval()
    _MODEL_CACHE[model_id] = (tokenizer, model)
    return _MODEL_CACHE[model_id]


def _generate(messages: list[dict[str, str]], tokenizer: Any, model: Any) -> str:
    import torch

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )
    if hasattr(inputs, "to"):
        inputs = inputs.to(model.device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=getattr(tokenizer, "pad_token_id", None),
            eos_token_id=getattr(tokenizer, "eos_token_id", None),
        )

    input_len = inputs["input_ids"].shape[-1]
    return tokenizer.decode(output[0][input_len:], skip_special_tokens=True).strip()


def retrieve(question: str, chunks: Sequence[Chunk], embeddings: Any, embedder: Any, tokenizer: Any) -> list[int]:
    """Return fused retrieval order; exposed separately for offline testing."""

    lexical = bm25_rank(question, chunks)
    semantic = semantic_rank(question, chunks, embeddings, embedder)
    fused = reciprocal_rank_fusion(
        [lexical, semantic],
        weights=[BM25_WEIGHT, VECTOR_WEIGHT],
    )
    return fused


def answer(question: str, corpus_dir: str, model_id: str) -> str:
    """Official submission entry point.

    The contract follows the starter kit: return one string for each question.
    All expensive resources are cached across calls in the same process.
    """

    chunks, embeddings, embedder = _load_index(corpus_dir)
    tokenizer, model = _load_model(model_id)
    ranked = retrieve(question, chunks, embeddings, embedder, tokenizer)
    context = build_context(question, chunks, ranked, tokenizer)
    messages = build_messages(question, context)
    return _generate(messages, tokenizer, model)


if __name__ == "__main__":
    print("This module is an inference backend. Run smoke_test.py for local checks.")
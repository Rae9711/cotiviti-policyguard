"""Local semantic and entity-aware policy comparison.

Role in PolicyGuard
-------------------
Compares two policy text versions in-memory using sentence segmentation,
TF-IDF bigram similarity, lexical matching for numeric/code-heavy lines,
and entity extraction (codes, dates, currency, modifiers, percentages).
Documents can be uploaded as TXT/PDF; nothing is sent to an external LLM.

Outputs feed the Policy Intelligence workspace (highlighting, deltas,
downloadable comparison JSON).
"""

from __future__ import annotations

import html
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Entity patterns
# ---------------------------------------------------------------------------
CODE_RE = re.compile(r"\b(\d{5}|[A-Z]\d{4})\b")
CURRENCY_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?")
DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},\s+\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{4}\b",
    re.IGNORECASE,
)
MODIFIER_RE = re.compile(r"\b(?:KX|59|25|GT|95|GQ)\b")
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?%")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass
class EntityDelta:
    category: str
    entity: str
    direction: str  # added | removed | shared


@dataclass
class SentencePair:
    old: str
    new: str
    similarity: float
    status: str  # unchanged | modified | added | removed


@dataclass
class ComparisonResult:
    old_text: str
    new_text: str
    similarity: float
    sentences: list[SentencePair] = field(default_factory=list)
    entity_deltas: list[EntityDelta] = field(default_factory=list)
    old_highlighted_html: str = ""
    new_highlighted_html: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "similarity": self.similarity,
            "sentences": [asdict(s) for s in self.sentences],
            "entity_deltas": [asdict(e) for e in self.entity_deltas],
            "old_text": self.old_text,
            "new_text": self.new_text,
        }


def segment_sentences(text: str) -> list[str]:
    """Split policy text into non-empty sentences."""
    parts = SENTENCE_RE.split(text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9$.,/%-]+", text.lower())


def _bigrams(tokens: list[str]) -> list[str]:
    if len(tokens) < 2:
        return tokens[:]
    return [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)] + tokens


def _tf(tokens: Iterable[str]) -> Counter:
    return Counter(tokens)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a[k] * b[k] for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def sentence_similarity(a: str, b: str) -> float:
    """Hybrid TF-IDF bigram + lexical SequenceMatcher score."""
    ta = _bigrams(_tokenize(a))
    tb = _bigrams(_tokenize(b))
    tfidf = _cosine(_tf(ta), _tf(tb))
    # Boost numeric/code-heavy lines with character-level ratio.
    lexical = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    code_heavy = bool(CODE_RE.search(a) or CURRENCY_RE.search(a) or CODE_RE.search(b))
    if code_heavy:
        return 0.45 * tfidf + 0.55 * lexical
    return 0.7 * tfidf + 0.3 * lexical


def extract_entities(text: str) -> dict[str, set[str]]:
    """Extract codes, dates, currency, modifiers, and percentages."""
    return {
        "codes": set(CODE_RE.findall(text)),
        "dates": set(DATE_RE.findall(text)),
        "currency": set(CURRENCY_RE.findall(text)),
        "modifiers": set(MODIFIER_RE.findall(text)),
        "percentages": set(PERCENT_RE.findall(text)),
    }


def _entity_deltas(old_text: str, new_text: str) -> list[EntityDelta]:
    old_e = extract_entities(old_text)
    new_e = extract_entities(new_text)
    deltas: list[EntityDelta] = []
    for category in old_e:
        added = new_e[category] - old_e[category]
        removed = old_e[category] - new_e[category]
        shared = old_e[category] & new_e[category]
        for ent in sorted(added):
            deltas.append(EntityDelta(category, ent, "added"))
        for ent in sorted(removed):
            deltas.append(EntityDelta(category, ent, "removed"))
        for ent in sorted(shared):
            deltas.append(EntityDelta(category, ent, "shared"))
    return deltas


def _align_sentences(old_sents: list[str], new_sents: list[str]) -> list[SentencePair]:
    """Greedy best-match alignment of sentences across versions."""
    pairs: list[SentencePair] = []
    used_new: set[int] = set()
    for old in old_sents:
        best_j = -1
        best_sim = 0.0
        for j, new in enumerate(new_sents):
            if j in used_new:
                continue
            sim = sentence_similarity(old, new)
            if sim > best_sim:
                best_sim = sim
                best_j = j
        if best_j >= 0 and best_sim >= 0.35:
            used_new.add(best_j)
            status = "unchanged" if best_sim >= 0.92 else "modified"
            pairs.append(
                SentencePair(old=old, new=new_sents[best_j], similarity=best_sim, status=status)
            )
        else:
            pairs.append(SentencePair(old=old, new="", similarity=0.0, status="removed"))
    for j, new in enumerate(new_sents):
        if j not in used_new:
            pairs.append(SentencePair(old="", new=new, similarity=0.0, status="added"))
    return pairs


def _word_highlight(old: str, new: str) -> tuple[str, str]:
    """Return HTML with word-level inserts/deletes highlighted."""
    old_words = old.split()
    new_words = new.split()
    matcher = SequenceMatcher(None, old_words, new_words)
    old_parts: list[str] = []
    new_parts: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            old_parts.extend(html.escape(w) for w in old_words[i1:i2])
            new_parts.extend(html.escape(w) for w in new_words[j1:j2])
        elif tag == "delete":
            for w in old_words[i1:i2]:
                old_parts.append(f'<mark class="pg-del">{html.escape(w)}</mark>')
        elif tag == "insert":
            for w in new_words[j1:j2]:
                new_parts.append(f'<mark class="pg-ins">{html.escape(w)}</mark>')
        elif tag == "replace":
            for w in old_words[i1:i2]:
                old_parts.append(f'<mark class="pg-del">{html.escape(w)}</mark>')
            for w in new_words[j1:j2]:
                new_parts.append(f'<mark class="pg-ins">{html.escape(w)}</mark>')
    return " ".join(old_parts), " ".join(new_parts)


def highlight_comparison(old_text: str, new_text: str) -> tuple[str, str]:
    """Build full-document HTML highlighting across aligned sentences."""
    pairs = _align_sentences(segment_sentences(old_text), segment_sentences(new_text))
    old_blocks: list[str] = []
    new_blocks: list[str] = []
    for pair in pairs:
        if pair.status == "removed":
            old_blocks.append(f'<p class="pg-removed">{html.escape(pair.old)}</p>')
        elif pair.status == "added":
            new_blocks.append(f'<p class="pg-added">{html.escape(pair.new)}</p>')
        else:
            oh, nh = _word_highlight(pair.old, pair.new)
            old_blocks.append(f"<p>{oh}</p>")
            new_blocks.append(f"<p>{nh}</p>")
    return "\n".join(old_blocks), "\n".join(new_blocks)


def compare_texts(old_text: str, new_text: str) -> ComparisonResult:
    """Run the full local semantic comparison pipeline."""
    old_sents = segment_sentences(old_text)
    new_sents = segment_sentences(new_text)
    pairs = _align_sentences(old_sents, new_sents)
    overall = sentence_similarity(old_text, new_text)
    old_html, new_html = highlight_comparison(old_text, new_text)
    return ComparisonResult(
        old_text=old_text,
        new_text=new_text,
        similarity=round(overall, 4),
        sentences=pairs,
        entity_deltas=_entity_deltas(old_text, new_text),
        old_highlighted_html=old_html,
        new_highlighted_html=new_html,
    )


def extract_text_from_upload(filename: str, raw: bytes) -> str:
    """Extract UTF-8 text from an uploaded TXT or PDF (in memory)."""
    name = filename.lower()
    if name.endswith(".pdf"):
        import fitz  # PyMuPDF

        doc = fitz.open(stream=raw, filetype="pdf")
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    return raw.decode("utf-8", errors="replace")

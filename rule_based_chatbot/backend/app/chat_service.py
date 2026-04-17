import difflib
import re


_WORD_RE = re.compile(r"\w+")


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def similarity_score(query: str, candidate: str) -> float:
    query_norm = normalize_text(query)
    candidate_norm = normalize_text(candidate)

    seq_score = difflib.SequenceMatcher(None, query_norm, candidate_norm).ratio()
    query_tokens = set(_WORD_RE.findall(query_norm))
    candidate_tokens = set(_WORD_RE.findall(candidate_norm))
    overlap = (
        len(query_tokens & candidate_tokens) / len(query_tokens | candidate_tokens)
        if query_tokens and candidate_tokens
        else 0.0
    )
    return (0.65 * seq_score) + (0.35 * overlap)

import re

from rank_bm25 import BM25Plus

from backend.core.chunker import CodeChunk


def tokenize_code(text: str) -> list[str]:
    if not text:
        return []
    words = re.findall(r"[A-Za-z0-9_]+", text)
    tokens = []
    for word in words:
        tokens.append(word.lower())
        subwords = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+", word)
        for sw in subwords:
            if sw and sw.lower() != word.lower():
                tokens.append(sw.lower())
    return tokens


class BM25Index:
    def __init__(self):
        self.chunks: list[CodeChunk] = []
        self.bm25: BM25Plus | None = None

    def index_chunks(self, chunks: list[CodeChunk]):
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            return
        corpus = []
        for c in chunks:
            text = f"{c.file_path} {c.symbol_name or ''} {c.parent_symbol or ''} {c.docstring or ''} {c.code}"
            corpus.append(tokenize_code(text))
        if corpus:
            self.bm25 = BM25Plus(corpus)

    def search(self, query: str, top_k: int = 30) -> list[dict]:
        if not self.bm25 or not self.chunks:
            return []
        query_tokens = tokenize_code(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]
        return [
            {
                "chunk_id": self.chunks[i].chunk_id,
                "score": float(scores[i]),
                "chunk": self.chunks[i],
            }
            for i in ranked_indices
            if scores[i] > 0
        ]

from pydantic import BaseModel

from backend.core.chunker import CodeChunk


class SearchResult(BaseModel):
    chunk_id: str
    file_path: str
    language: str
    chunk_type: str
    symbol_name: str | None = None
    parent_symbol: str | None = None
    start_line: int
    end_line: int
    code: str
    docstring: str | None = None
    score: float
    sources: list[str]


class HybridSearchEngine:
    def __init__(
        self, rrf_k: int = 60, vector_weight: float = 1.0, bm25_weight: float = 0.8
    ):
        self.rrf_k = rrf_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    def fuse(
        self,
        vector_results: list[dict],
        bm25_results: list[dict],
        chunks_by_id: dict[str, CodeChunk],
        top_k: int = 15,
    ) -> list[SearchResult]:
        rrf_scores: dict[str, float] = {}
        sources_map: dict[str, set] = {}

        for rank, item in enumerate(vector_results):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (
                self.vector_weight / (self.rrf_k + rank + 1)
            )
            sources_map.setdefault(cid, set()).add("vector")

        for rank, item in enumerate(bm25_results):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (
                self.bm25_weight / (self.rrf_k + rank + 1)
            )
            sources_map.setdefault(cid, set()).add("bm25")

        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )[:top_k]

        results: list[SearchResult] = []
        for cid in sorted_ids:
            chunk = chunks_by_id.get(cid)
            if chunk:
                results.append(
                    SearchResult(
                        chunk_id=chunk.chunk_id,
                        file_path=chunk.file_path,
                        language=chunk.language,
                        chunk_type=chunk.chunk_type,
                        symbol_name=chunk.symbol_name,
                        parent_symbol=chunk.parent_symbol,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        code=chunk.code,
                        docstring=chunk.docstring,
                        score=round(rrf_scores[cid], 4),
                        sources=sorted(sources_map.get(cid, [])),
                    )
                )
        return results

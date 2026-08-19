from backend.core.bm25_search import BM25Index
from backend.core.chunker import CodeChunk
from backend.core.hybrid_engine import HybridSearchEngine


def test_bm25_exact_symbol_match():
    chunks = [
        CodeChunk(
            chunk_id="1",
            file_path="auth.py",
            language="python",
            chunk_type="function",
            symbol_name="validate_jwt_token",
            start_line=1,
            end_line=10,
            code="def validate_jwt_token(token): pass",
        ),
        CodeChunk(
            chunk_id="2",
            file_path="user.py",
            language="python",
            chunk_type="function",
            symbol_name="get_user_profile",
            start_line=1,
            end_line=10,
            code="def get_user_profile(uid): pass",
        ),
    ]
    bm25 = BM25Index()
    bm25.index_chunks(chunks)
    results = bm25.search("validate_jwt_token", top_k=5)
    assert len(results) > 0
    assert results[0]["chunk_id"] == "1"


def test_hybrid_rrf_fusion():
    c1 = CodeChunk(
        chunk_id="1",
        file_path="auth.py",
        language="python",
        chunk_type="function",
        symbol_name="validate_jwt_token",
        start_line=1,
        end_line=10,
        code="def validate_jwt_token(token): pass",
    )
    c2 = CodeChunk(
        chunk_id="2",
        file_path="user.py",
        language="python",
        chunk_type="function",
        symbol_name="get_user_profile",
        start_line=1,
        end_line=10,
        code="def get_user_profile(uid): pass",
    )
    chunks_by_id = {"1": c1, "2": c2}

    vector_results = [{"chunk_id": "2"}, {"chunk_id": "1"}]
    bm25_results = [{"chunk_id": "1"}, {"chunk_id": "2"}]

    engine = HybridSearchEngine(rrf_k=60, vector_weight=1.0, bm25_weight=1.0)
    results = engine.fuse(vector_results, bm25_results, chunks_by_id, top_k=5)
    assert len(results) == 2
    assert "vector" in results[0].sources
    assert "bm25" in results[0].sources

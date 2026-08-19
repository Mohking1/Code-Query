import hashlib
import os
import sqlite3
from pathlib import Path

import chromadb

from backend.config import get_settings
from backend.core.bm25_search import BM25Index
from backend.core.chunker import CodeChunk, SemanticChunker
from backend.core.embedding import EmbeddingModel
from backend.core.hybrid_engine import HybridSearchEngine, SearchResult


class IndexManager:
    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.settings = get_settings()

        self.storage_dir = os.path.join(self.workspace_path, ".codequery")
        os.makedirs(self.storage_dir, exist_ok=True)

        self.db_path = os.path.join(self.storage_dir, "index.db")
        self._init_sqlite()

        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(self.storage_dir, "chroma")
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="code_vectors"
        )

        self.chunker = SemanticChunker()
        self.embedding_model = EmbeddingModel(self.settings.embedding_model_name)
        self.bm25_index = BM25Index()
        self.hybrid_engine = HybridSearchEngine(
            self.settings.rrf_k, self.settings.vector_weight, self.settings.bm25_weight
        )

        self.chunks_cache: dict[str, CodeChunk] = {}
        self._load_cached_chunks()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    sha256 TEXT,
                    mtime REAL,
                    chunk_count INT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    file_path TEXT,
                    language TEXT,
                    chunk_type TEXT,
                    symbol_name TEXT,
                    parent_symbol TEXT,
                    start_line INT,
                    end_line INT,
                    code TEXT,
                    docstring TEXT
                )
            """)

    def _load_cached_chunks(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id, file_path, language, chunk_type, symbol_name, parent_symbol, start_line, end_line, code, docstring 
                FROM chunks
            """)
            for row in cursor.fetchall():
                chunk = CodeChunk(
                    chunk_id=row[0],
                    file_path=row[1],
                    language=row[2],
                    chunk_type=row[3],
                    symbol_name=row[4],
                    parent_symbol=row[5],
                    start_line=row[6],
                    end_line=row[7],
                    code=row[8],
                    docstring=row[9],
                )
                self.chunks_cache[chunk.chunk_id] = chunk
        self.bm25_index.index_chunks(list(self.chunks_cache.values()))

    def get_chunk_count(self) -> int:
        return len(self.chunks_cache)

    def _compute_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def index_file(self, abs_path: str):
        if not os.path.exists(abs_path) or os.path.isdir(abs_path):
            return

        rel_path = os.path.relpath(abs_path, self.workspace_path)
        if any(part.startswith(".") and part != "." for part in Path(rel_path).parts):
            return
        if any(
            ignored in rel_path
            for ignored in (
                "node_modules",
                "venv",
                ".venv",
                "dist",
                "build",
                "__pycache__",
            )
        ):
            return

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return

        file_hash = self._compute_hash(abs_path)
        mtime = os.path.getmtime(abs_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sha256 FROM files WHERE path = ?", (rel_path,))
            row = cursor.fetchone()
            if row and row[0] == file_hash:
                return

        new_chunks = self.chunker.chunk_file(rel_path, content)
        self.remove_file(abs_path)

        if not new_chunks:
            return

        texts = [f"{c.file_path} {c.symbol_name or ''}\n{c.code}" for c in new_chunks]
        embeddings = self.embedding_model.encode(texts)

        self.collection.add(
            ids=[c.chunk_id for c in new_chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "file_path": c.file_path,
                    "symbol_name": c.symbol_name or "",
                    "language": c.language,
                }
                for c in new_chunks
            ],
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO files VALUES (?, ?, ?, ?)",
                (rel_path, file_hash, mtime, len(new_chunks)),
            )
            for c in new_chunks:
                conn.execute(
                    "INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        c.chunk_id,
                        c.file_path,
                        c.language,
                        c.chunk_type,
                        c.symbol_name,
                        c.parent_symbol,
                        c.start_line,
                        c.end_line,
                        c.code,
                        c.docstring,
                    ),
                )
                self.chunks_cache[c.chunk_id] = c

        self.bm25_index.index_chunks(list(self.chunks_cache.values()))

    def remove_file(self, abs_path: str):
        rel_path = os.path.relpath(abs_path, self.workspace_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chunk_id FROM chunks WHERE file_path = ?", (rel_path,)
            )
            old_ids = [r[0] for r in cursor.fetchall()]
            if old_ids:
                try:
                    self.collection.delete(ids=old_ids)
                except (KeyError, ValueError, RuntimeError):
                    pass
                conn.execute("DELETE FROM chunks WHERE file_path = ?", (rel_path,))
                conn.execute("DELETE FROM files WHERE path = ?", (rel_path,))
                for cid in old_ids:
                    self.chunks_cache.pop(cid, None)
        self.bm25_index.index_chunks(list(self.chunks_cache.values()))

    def index_workspace(self):
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in (
                    "node_modules",
                    "venv",
                    ".venv",
                    "dist",
                    "build",
                    "__pycache__",
                    "docs",
                )
            ]
            for file in files:
                if file.startswith("."):
                    continue
                full_path = os.path.join(root, file)
                self.index_file(full_path)

    def search(self, query: str, top_k: int = 15) -> list[SearchResult]:
        if not self.chunks_cache:
            return []

        vector_results = []
        try:
            query_emb = self.embedding_model.encode([query])
            v_res = self.collection.query(
                query_embeddings=query_emb,
                n_results=min(30, max(1, len(self.chunks_cache))),
            )
            if v_res and "ids" in v_res and len(v_res["ids"]) > 0:
                for cid in v_res["ids"][0]:
                    vector_results.append({"chunk_id": cid})
        except (ValueError, RuntimeError) as e:
            print(f"Vector search warning: {e}")

        bm25_results = self.bm25_index.search(query, top_k=30)
        return self.hybrid_engine.fuse(
            vector_results, bm25_results, self.chunks_cache, top_k=top_k
        )

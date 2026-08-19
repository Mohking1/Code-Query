import os

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.index_manager import IndexManager
from backend.core.watcher import start_watcher

app = FastAPI(title="CodeQuery Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_manager: IndexManager | None = None
current_watcher = None


class IndexRequest(BaseModel):
    workspace_path: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 15
    language: str | None = None
    chunk_type: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "indexed_chunks": current_manager.get_chunk_count() if current_manager else 0,
        "workspace": current_manager.workspace_path if current_manager else None,
    }


@app.post("/api/index/start")
def start_index(req: IndexRequest, bg: BackgroundTasks):
    global current_manager, current_watcher
    if not os.path.exists(req.workspace_path):
        raise HTTPException(status_code=400, detail="Workspace path does not exist")

    current_manager = IndexManager(req.workspace_path)
    bg.add_task(current_manager.index_workspace)

    if current_watcher:
        try:
            current_watcher.stop()
        except (RuntimeError, OSError):
            pass
    try:
        current_watcher = start_watcher(current_manager)
    except (OSError, RuntimeError) as e:
        print(f"Watcher startup warning: {e}")

    return {"message": "Indexing started", "workspace": req.workspace_path}


@app.get("/api/index/status")
def index_status():
    if not current_manager:
        return {"status": "idle", "chunk_count": 0}
    return {
        "status": "ready",
        "chunk_count": current_manager.get_chunk_count(),
        "workspace": current_manager.workspace_path,
    }


@app.post("/api/search")
def search(req: SearchRequest):
    if not current_manager:
        raise HTTPException(status_code=400, detail="No active workspace indexed")
    results = current_manager.search(req.query, top_k=req.top_k)
    if req.language:
        results = [r for r in results if r.language.lower() == req.language.lower()]
    if req.chunk_type:
        results = [r for r in results if r.chunk_type.lower() == req.chunk_type.lower()]
    return {"results": [r.model_dump() for r in results]}

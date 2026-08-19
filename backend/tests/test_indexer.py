from backend.core.index_manager import IndexManager


def test_incremental_indexing(tmp_path):
    test_file = tmp_path / "calc.py"
    test_file.write_text("def add(x, y):\n    return x + y\n")

    manager = IndexManager(str(tmp_path))
    manager.index_workspace()

    assert manager.get_chunk_count() >= 1
    results = manager.search("add numbers", top_k=5)
    assert len(results) > 0
    assert results[0].symbol_name == "add"

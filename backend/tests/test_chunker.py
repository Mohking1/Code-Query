from backend.core.chunker import SemanticChunker


def test_python_function_chunking():
    code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

class Calculator:
    def multiply(self, x: int, y: int) -> int:
        return x * y
'''
    chunker = SemanticChunker()
    chunks = chunker.chunk_file("calc.py", code)
    assert len(chunks) >= 2

    fn_chunk = next(c for c in chunks if c.symbol_name == "add")
    assert fn_chunk.chunk_type == "function"
    assert fn_chunk.start_line == 2
    assert "Add two numbers" in (fn_chunk.docstring or "")

    method_chunk = next(c for c in chunks if c.symbol_name == "multiply")
    assert method_chunk.chunk_type in ("method", "function")
    assert method_chunk.parent_symbol == "Calculator"


def test_javascript_chunking():
    code = """
function fetchData(url) {
    return fetch(url);
}
"""
    chunker = SemanticChunker()
    chunks = chunker.chunk_file("api.js", code)
    assert len(chunks) >= 1
    assert chunks[0].symbol_name == "fetchData"


def test_fallback_chunking():
    text = "\n".join([f"line {i}" for i in range(100)])
    chunker = SemanticChunker()
    chunks = chunker.chunk_file("doc.txt", text)
    assert len(chunks) >= 2
    assert chunks[0].chunk_type == "block"

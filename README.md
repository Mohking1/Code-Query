# CodeQuery

Local code search engine and VS Code extension. Combines Tree-sitter AST parsing, dense embeddings (ChromaDB), and BM25 with Reciprocal Rank Fusion (RRF) for hybrid semantic and symbol search.

## Features

- Multi-language AST chunking via Tree-sitter (Python, TypeScript, JavaScript, Go, Rust, Java, C, C++).
- Hybrid retrieval: ChromaDB vector search + BM25Okapi/Plus fused with RRF.
- Incremental indexing using SHA-256 file hashing and Watchdog file system observer.
- VS Code extension with sidebar search webview, keyboard palette (`Ctrl+Alt+F`), and jump-to-definition in editor.
- 100% local execution.

## Requirements

- Python 3.10+
- Node.js 18+
- VS Code 1.75+

## Setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend server manually:

```bash
python -m backend.main --port 8765
```

Run tests:

```bash
PYTHONPATH=. pytest backend/tests -v
```

### VS Code Extension

```bash
cd vscode-extension
npm install
npm run compile
```

To package the VSIX:

```bash
npx @vscode/vsce package --allow-missing-repository
```

To install the extension in VS Code:

```bash
code --install-extension vscode-extension/codequery-vscode-2.0.0.vsix
```

Or open the `vscode-extension` directory in VS Code and press `F5` to debug.

import * as vscode from "vscode";
import { ApiClient } from "../apiClient";

export class SidebarProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly apiClient: ApiClient
  ) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    };

    webviewView.webview.html = this._getHtmlForWebview();

    webviewView.webview.onDidReceiveMessage(async (data) => {
      switch (data.type) {
        case "search": {
          const results = await this.apiClient.search(
            data.query,
            data.language,
            data.chunkType
          );
          webviewView.webview.postMessage({ type: "results", results });
          break;
        }
        case "openFile": {
          await this._openFileInEditor(data.filePath, data.startLine, data.endLine);
          break;
        }
        case "reindex": {
          const wsFolders = vscode.workspace.workspaceFolders;
          if (wsFolders && wsFolders.length > 0) {
            await this.apiClient.startIndexing(wsFolders[0].uri.fsPath);
            vscode.window.showInformationMessage("CodeQuery: Re-indexing started.");
          }
          break;
        }
        case "getStatus": {
          const status = await this.apiClient.getStatus();
          webviewView.webview.postMessage({ type: "status", status });
          break;
        }
      }
    });
  }

  private async _openFileInEditor(relPath: string, startLine: number, endLine: number) {
    const wsFolders = vscode.workspace.workspaceFolders;
    if (!wsFolders || wsFolders.length === 0) {
      vscode.window.showErrorMessage("No workspace open to locate file.");
      return;
    }

    try {
      const fullPath = vscode.Uri.joinPath(wsFolders[0].uri, relPath);
      const doc = await vscode.workspace.openTextDocument(fullPath);
      const editor = await vscode.window.showTextDocument(doc, {
        preview: false,
        viewColumn: vscode.ViewColumn.One
      });

      const start = new vscode.Position(Math.max(0, startLine - 1), 0);
      const end = new vscode.Position(Math.max(0, endLine - 1), 0);
      const range = new vscode.Range(start, end);

      editor.selection = new vscode.Selection(start, end);
      editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
    } catch (e: any) {
      vscode.window.showErrorMessage(`Could not open ${relPath}: ${e.message}`);
    }
  }

  private _getHtmlForWebview(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeQuery Search</title>
<style>
  :root {
    --bg-card: var(--vscode-editor-background, #1e1e1e);
    --border-card: var(--vscode-widget-border, #333);
    --text-primary: var(--vscode-foreground, #ccc);
    --text-link: var(--vscode-textLink-foreground, #3794ff);
    --badge-bg: var(--vscode-badge-background, #4d4d4d);
    --badge-fg: var(--vscode-badge-foreground, #fff);
  }
  body {
    font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    font-size: var(--vscode-font-size, 13px);
    color: var(--text-primary);
    padding: 10px;
    margin: 0;
    box-sizing: border-box;
  }
  .search-container {
    position: sticky;
    top: 0;
    background: var(--vscode-sideBar-background, #252526);
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-card);
    z-index: 10;
  }
  input, select, button {
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 6px;
    padding: 6px 8px;
    background: var(--vscode-input-background, #3c3c3c);
    color: var(--vscode-input-foreground, #ccc);
    border: 1px solid var(--vscode-input-border, #3c3c3c);
    border-radius: 4px;
    font-size: 12px;
  }
  input:focus, select:focus {
    outline: 1px solid var(--vscode-focusBorder, #007acc);
  }
  .filter-row {
    display: flex;
    gap: 6px;
  }
  button {
    background: var(--vscode-button-background, #0e639c);
    color: var(--vscode-button-foreground, #fff);
    cursor: pointer;
    border: none;
    font-weight: 600;
    padding: 7px;
    transition: background 0.15s ease;
  }
  button:hover {
    background: var(--vscode-button-hoverBackground, #1177bb);
  }
  .results-summary {
    font-size: 11px;
    opacity: 0.7;
    margin: 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 10px;
    transition: border-color 0.15s ease;
  }
  .card:hover {
    border-color: var(--text-link);
  }
  .card-header {
    font-weight: 600;
    cursor: pointer;
    color: var(--text-link);
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    word-break: break-all;
  }
  .card-sub {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin: 6px 0;
  }
  .badge {
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 10px;
    background: var(--badge-bg);
    color: var(--badge-fg);
  }
  .badge-sources {
    background: #2b5b84;
    color: #fff;
  }
  pre {
    background: var(--vscode-textCodeBlock-background, rgba(0,0,0,0.25));
    border-radius: 4px;
    padding: 6px;
    margin: 4px 0 0 0;
    overflow-x: auto;
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 11px;
    line-height: 1.35;
    max-height: 180px;
  }
  .actions-row {
    margin-top: 6px;
    display: flex;
    gap: 6px;
  }
  .action-btn {
    padding: 3px 6px;
    font-size: 10px;
    background: transparent;
    border: 1px solid var(--border-card);
    color: var(--text-primary);
    width: auto;
  }
  .action-btn:hover {
    background: var(--vscode-list-hoverBackground, #2a2d2e);
  }
  .status-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--vscode-sideBar-background, #252526);
    padding: 6px 10px;
    border-top: 1px solid var(--border-card);
    font-size: 11px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
</style>
</head>
<body>
  <div class="search-container">
    <input type="text" id="query" placeholder="🔍 Search logic, functions, classes..." />
    <div class="filter-row">
      <select id="lang">
        <option value="">All Languages</option>
        <option value="python">Python</option>
        <option value="javascript">JavaScript</option>
        <option value="typescript">TypeScript</option>
        <option value="tsx">TSX / React</option>
        <option value="go">Go</option>
        <option value="rust">Rust</option>
        <option value="java">Java</option>
        <option value="c">C</option>
        <option value="cpp">C++</option>
      </select>
      <select id="chunkType">
        <option value="">All Types</option>
        <option value="function">Function</option>
        <option value="method">Method</option>
        <option value="class">Class</option>
        <option value="block">Block</option>
      </select>
    </div>
    <button id="searchBtn">Search Codebase</button>
  </div>

  <div id="summary" class="results-summary"></div>
  <div id="results" style="padding-bottom: 30px;"></div>

  <div class="status-footer">
    <span id="statusIndicator">● Engine: Ready</span>
    <a href="#" id="reindexLink" style="color:var(--text-link); text-decoration:none;">⟳ Re-index</a>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const queryInput = document.getElementById("query");
    const langSelect = document.getElementById("lang");
    const typeSelect = document.getElementById("chunkType");
    const resultsDiv = document.getElementById("results");
    const summaryDiv = document.getElementById("summary");
    const statusIndicator = document.getElementById("statusIndicator");
    const reindexLink = document.getElementById("reindexLink");

    function doSearch() {
      const q = queryInput.value.trim();
      if (!q) return;
      summaryDiv.innerHTML = "<em>Searching...</em>";
      vscode.postMessage({
        type: "search",
        query: q,
        language: langSelect.value || undefined,
        chunkType: typeSelect.value || undefined
      });
    }

    document.getElementById("searchBtn").onclick = doSearch;
    queryInput.onkeydown = (e) => { if (e.key === "Enter") doSearch(); };
    reindexLink.onclick = (e) => {
      e.preventDefault();
      vscode.postMessage({ type: "reindex" });
    };

    window.addEventListener("message", (event) => {
      const msg = event.data;
      if (msg.type === "results") {
        const results = msg.results || [];
        summaryDiv.innerHTML = \`<span>Found \${results.length} results</span>\`;
        if (results.length === 0) {
          resultsDiv.innerHTML = "<p style='text-align:center;margin-top:20px;opacity:0.6;'>No matching code chunks found.</p>";
          return;
        }
        resultsDiv.innerHTML = results.map(r => \`
          <div class="card">
            <div class="card-header" onclick="openFile('\${escapeHtml(r.file_path)}', \${r.start_line}, \${r.end_line})">
              <span>📄 \${escapeHtml(r.file_path)}:L\${r.start_line}</span>
              <span>↗</span>
            </div>
            <div class="card-sub">
              \${r.symbol_name ? \`<span class="badge">\${escapeHtml(r.chunk_type)}: \${escapeHtml(r.symbol_name)}</span>\` : ''}
              <span class="badge">\${escapeHtml(r.language)}</span>
              <span class="badge badge-sources">\${escapeHtml(r.sources.join('+'))}</span>
              <span class="badge">Score: \${r.score.toFixed(3)}</span>
            </div>
            <pre><code>\${escapeHtml(r.code)}</code></pre>
            <div class="actions-row">
              <button class="action-btn" onclick="openFile('\${escapeHtml(r.file_path)}', \${r.start_line}, \${r.end_line})">Open File</button>
              <button class="action-btn" onclick="copySnippet(\`\${escapeJs(r.code)}\`)">Copy Code</button>
            </div>
          </div>
        \`).join("");
      } else if (msg.type === "status") {
        if (msg.status && msg.status.status === "ready") {
          statusIndicator.innerText = \`● \${msg.status.chunk_count} chunks indexed\`;
        }
      }
    });

    function openFile(filePath, startLine, endLine) {
      vscode.postMessage({ type: "openFile", filePath, startLine, endLine });
    }

    function copySnippet(text) {
      navigator.clipboard.writeText(text);
    }

    function escapeHtml(str) {
      if (!str) return "";
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function escapeJs(str) {
      if (!str) return "";
      return String(str).replace(/\\\\/g, "\\\\\\\\").replace(/\\\`/g, "\\\\\\\`").replace(/\\$/g, "\\\\$");
    }

    setInterval(() => {
      vscode.postMessage({ type: "getStatus" });
    }, 5000);
  </script>
</body>
</html>`;
  }
}

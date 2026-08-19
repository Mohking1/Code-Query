import * as vscode from "vscode";
import { ServerManager } from "./serverManager";
import { ApiClient } from "./apiClient";
import { SidebarProvider } from "./webview/SidebarProvider";

let serverManager: ServerManager;

export async function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("codequery");
  const port = config.get<number>("serverPort") || 8765;

  const apiClient = new ApiClient(port);
  serverManager = new ServerManager(port);

  const wsFolders = vscode.workspace.workspaceFolders;
  if (wsFolders && wsFolders.length > 0) {
    const wsPath = wsFolders[0].uri.fsPath;
    const rootDir = context.extensionPath;
    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Window,
        title: "CodeQuery: Connecting search engine..."
      },
      async () => {
        await serverManager.startServer(wsPath, rootDir);
      }
    );
  }

  const sidebarProvider = new SidebarProvider(context.extensionUri, apiClient);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codequery.sidebarView", sidebarProvider)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("codequery.search", async () => {
      const query = await vscode.window.showInputBox({
        prompt: "CodeQuery: Search codebase",
        placeHolder: "e.g. JWT token validation, create_user"
      });

      if (!query || !query.trim()) return;

      const results = await apiClient.search(query.trim());
      if (results.length === 0) {
        vscode.window.showInformationMessage(`No code found matching "${query}"`);
        return;
      }

      const items = results.map((r) => ({
        label: `$(symbol-method) ${r.symbol_name || r.file_path}`,
        description: `${r.file_path}:${r.start_line}`,
        detail: r.code.split("\n")[0].trim(),
        result: r
      }));

      const selected = await vscode.window.showQuickPick(items, {
        matchOnDescription: true,
        matchOnDetail: true,
        placeHolder: `Select result (${results.length} found)`
      });

      if (selected && wsFolders && wsFolders.length > 0) {
        const fullPath = vscode.Uri.joinPath(wsFolders[0].uri, selected.result.file_path);
        const doc = await vscode.workspace.openTextDocument(fullPath);
        const editor = await vscode.window.showTextDocument(doc, { preview: false });

        const startLine = Math.max(0, selected.result.start_line - 1);
        const endLine = Math.max(0, selected.result.end_line - 1);
        const range = new vscode.Range(startLine, 0, endLine, 0);

        editor.selection = new vscode.Selection(range.start, range.end);
        editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
      }
    })
  );
}

export function deactivate() {
  if (serverManager) {
    serverManager.stopServer();
  }
}

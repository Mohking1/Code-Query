import * as cp from "child_process";
import * as vscode from "vscode";
import * as path from "path";
import { ApiClient } from "./apiClient";

export class ServerManager {
  private process?: cp.ChildProcess;
  private apiClient: ApiClient;
  private port: number;

  constructor(port: number = 8765) {
    this.port = port;
    this.apiClient = new ApiClient(port);
  }

  async startServer(workspacePath: string, rootDir: string): Promise<boolean> {
    const isAlive = await this.apiClient.checkHealth();
    if (isAlive) {
      await this.apiClient.startIndexing(workspacePath);
      return true;
    }

    const config = vscode.workspace.getConfiguration("codequery");
    let pythonPath = config.get<string>("pythonPath") || "python";

    const venvPython = path.join(rootDir, ".venv", "bin", "python");
    if (pythonPath === "python" && require("fs").existsSync(venvPython)) {
      pythonPath = venvPython;
    }

    try {
      this.process = cp.spawn(pythonPath, ["-m", "backend.main", "--port", `${this.port}`], {
        cwd: rootDir,
        stdio: "ignore",
        detached: false
      });

      this.process.on("error", (err) => {
        console.error("Failed to start CodeQuery server:", err);
      });
    } catch (e) {
      console.error("Error launching server process:", e);
    }

    for (let i = 0; i < 25; i++) {
      await new Promise((r) => setTimeout(r, 600));
      if (await this.apiClient.checkHealth()) {
        await this.apiClient.startIndexing(workspacePath);
        return true;
      }
    }
    return false;
  }

  stopServer() {
    if (this.process) {
      this.process.kill();
      this.process = undefined;
    }
  }
}

export interface SearchResult {
  chunk_id: string;
  file_path: string;
  language: string;
  chunk_type: string;
  symbol_name?: string;
  parent_symbol?: string;
  start_line: number;
  end_line: number;
  code: string;
  docstring?: string;
  score: number;
  sources: string[];
}

export class ApiClient {
  private baseUrl: string;

  constructor(port: number = 8765) {
    this.baseUrl = `http://127.0.0.1:${port}`;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return res.ok;
    } catch {
      return false;
    }
  }

  async startIndexing(workspacePath: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/index/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workspace_path: workspacePath })
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async getStatus(): Promise<{ status: string; chunk_count: number; workspace?: string } | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/index/status`);
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch {
      return null;
    }
  }

  async search(query: string, language?: string, chunkType?: string): Promise<SearchResult[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, language, chunk_type: chunkType })
      });
      if (!res.ok) {
        return [];
      }
      const data = await res.json();
      return data.results || [];
    } catch {
      return [];
    }
  }
}

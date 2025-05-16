# 🚀 CodeQuery

**CodeQuery** is a powerful, fully-local, AI‑powered code search engine that helps you find exactly what you need in your codebase in seconds. Using a hybrid of vector embeddings, keyword matching, synonym expansion, and LLM-based query enrichment, CodeQuery delivers precise, context-aware search results without ever leaving your machine.

---

## 📖 Features

* 🔍 **Semantic Vector Search**: Leverage embeddings to find code snippets by meaning, not just keywords.
* 📝 **Keyword & Synonym Matching**: Fall back to exact keyword matching and WordNet‑powered synonym expansion for broader coverage.
* 🤖 **LLM‑Enhanced Queries**: Enrich your search queries with a local LLM to capture intent and context.
* 🔒 **Fully Local**: All processing—including model downloads—happens on your machine; zero data leaves your computer.
* ⚡ **Fast & Interactive UI**: Browse and select from indexed codebases via a dropdown, then run queries in a sleek React frontend.
* 📂 **Persistent Index**: Once you index a codebase, it’s stored and instantly available on subsequent runs.

---

> ⚠️ **First-run warning:**
> The initial setup may take several minutes as embedding & language models are downloaded and cached.

---

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/codequery.git
cd codequery
```

### 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 🚦 How to Use

### 1. Start the Frontend

```bash
cd frontend
npm start
```

### 2. Run the Backend

In a new terminal from the project root:

```bash
python app.py
```

### 3. Index Your Codebase

* After running the backend, you’ll be prompted to enter the **absolute path** to your codebase.
* The system will process and index the codebase.
* Indexed paths will appear in a dropdown menu in the UI for quick selection.

### 4. Search Your Codebase

* Open your browser at `http://localhost:3000`
* Select your project from the dropdown.
* Enter a search query in natural language.
* CodeQuery will return the most relevant code snippets based on vector and keyword matching.

---

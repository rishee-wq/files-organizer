# Changelog

## 2026-02-02 — AI & UX upgrade (added by assistant)
- Added `get_folder_stats` API to compute total file count and total size per folder, counts and top largest files.
- Added a lightweight AI scaffold (`index_for_ai` and `query_ai`) for local substring-based search across .txt/.pdf files.
- Frontend updates: live folder stats display, AI Search UI, theme persistence (localStorage), and top-files preview in the activity pane.
- Added annotated files under `annotated/` for easier understanding and publication preparation.

Notes:
- For production-ready RAG/LLM features, integrate `langchain` + embeddings + `chromadb`/`faiss` and an LLM (OpenAI or local) — scaffold is ready for expansion.

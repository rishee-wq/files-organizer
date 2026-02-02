# RishFlow File Organizer

RishFlow is a desktop file organizer and AI-assisted sorter that helps you clean up and manage files with a beautiful dashboard and privacy-first AI features.

Key features
- Organize files by extension, date, size, or AI-based classification
- Folder statistics: total files and aggregated sizes
- Duplicate detection and undo support
- Lightweight local AI index (text + PDF search) with upgrade path to full RAG
- Privacy-first: local processing, optional cloud LLMs are explicit opt-in

Quick start
1. git clone https://github.com/rishee-wq/files-organizer
2. python -m venv .venv && .\.venv\Scripts\activate
3. pip install -r requirements.txt
4. (Optional) pip install pypdf for PDF indexing
5. python app.py

Architecture & research notes
- Frontend: HTML dashboard (Tailwind) + pywebview integration
- Backend: `app.py` exposes folder scanning, stats, AI indexing and organization APIs
- AI: `ai_sorter.py` uses OpenCV + pytesseract heuristics for classification

Research highlights (internal/experimental)
- Hybrid classification (rules + ML heuristics) was tested in earlier experiments with promising results on synthetic Downloads datasets.

See `docs/RishFlow_Docs.pdf` for a detailed publication-ready overview including architecture diagrams, privacy notes and a publishing checklist.

Roadmap
- Add LangChain-based RAG and embedding indexing (optional cloud or local LLM)
- UI polish and theme pack
- Unit tests, CI pipeline and PyInstaller release builds

License: MIT


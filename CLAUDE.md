# CLAUDE.md

## Project

**RAG Data Preparation Toolkit** — a PM-friendly document preprocessing pipeline for building RAG-ready knowledge bases.

The toolkit converts messy enterprise and industrial documents into structured, section-aware, metadata-rich chunks that can be exported into RAG systems.

## Implemented Scope

- DOCX document parsing (SOP / work instruction as the first use case)
- Heading and section detection (3-tier: Word styles, numeric numbering, keywords)
- Section-aware chunk generation
- Table extraction (Word tables to Markdown)
- Image extraction and reference preservation
- Batch processing
- Streamlit upload UI
- CSV and JSONL export

**Not yet implemented (roadmap):** PDF, HTML, Markdown input; Dify, LangChain, LlamaIndex export; evaluation sample generation is experimental/template-based only.

## Architecture Principles

1. Preserve existing functionality.
2. Refactor gradually.
3. Keep the project local-first and easy to run.
4. Separate UI logic from document processing logic.
5. Use synthetic sample documents only.
6. Avoid any confidential company data.
7. Keep backward compatibility with existing CSV output where possible.
8. Prefer modular, testable Python functions.

## Structure

```
app/                  # Streamlit UI (separate from processing logic)
rag_data_toolkit/     # Core processing package
scripts/              # CLI entry points
examples/             # Sample outputs
docs/                 # Architecture, data contract, roadmap, portfolio notes
tests/                # Smoke tests
```

## Commands

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
python scripts/process_single.py examples/sample_sop.docx
python scripts/process_batch.py path/to/folder/ --format csv
pytest tests/ -v
```

## Rules

- Add type hints where safe.
- Avoid unnecessary dependencies.
- Keep Streamlit simple and reliable.
- Run syntax checks after changes (`python -m py_compile <file>`).
- Update README and docs when user-facing behavior changes.
- Do not overclaim unsupported features in any documentation.

# Architecture

## Pipeline Flow

```
Industrial Document (.docx)
    |
    v
Document Loader (validation, .docx loading)
    |
    v
Section Parser (heading detection: style -> numbering -> keywords)
    |
    v
+-- Table Extractor (Word table -> Markdown, section attribution)
+-- Image Extractor (inline + table images, caption matching)
    |
    v
Chunker (orchestrator: text chunks with section paths, image embedding)
    |
    v
Metadata Builder (sop_id, sop_name from filename)
    |
    v
Exporters (CSV / JSONL / Dify / LangChain / LlamaIndex)
    |
    v
Eval Generator (synthetic QA samples for RAG evaluation)
```

## Module Map

| Module | Responsibility |
|--------|---------------|
| `document_loader.py` | File validation, .docx loading |
| `docx_parser.py` | Block iteration (paragraphs + tables in order), paragraph section map |
| `section_parser.py` | Heading detection (3-tier), heading level extraction, section path building |
| `table_extractor.py` | Table to Markdown, table section identification, table position pre-scan |
| `image_extractor.py` | Image extraction (inline + table), caption matching, image chunk content |
| `chunker.py` | Main orchestrator — generates chunks with metadata |
| `metadata_builder.py` | Extract sop_id/sop_name from filename |
| `exporters.py` | CSV, JSONL, Dify export |
| `eval_generator.py` | Synthetic QA sample generation |

## Heading Detection Priority

1. **Word styles** (Heading 1-10, H1-H10, Chinese heading styles)
2. **Numeric numbering** (3.1, 8.2.1, 4))
3. **Keyword matching** (目的, 适用范围, 职责, etc.)

## Image Attribution Strategy

1. Position-based: nearest heading at image's paragraph location
2. Caption-based: match caption section number to chunk section
3. Fallback: embed in last chunk with a section path

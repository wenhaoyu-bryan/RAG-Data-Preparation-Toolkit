# RAG Data Contract

## Why a Data Contract Is Needed for RAG

RAG systems retrieve chunks by similarity, then feed them to an LLM as context. If chunks are inconsistent — different field names, missing metadata, arbitrary boundaries — the retrieval quality degrades and the LLM receives noisy context. A data contract defines the standard shape of every chunk so downstream consumers (knowledge bases, agents, search systems) can rely on predictable structure.

## Core Entities

### Document
The source file being processed. One document produces many chunks.

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Identifier extracted from filename (e.g. "DOC.001") |
| `document_name` | string | Human-readable name extracted from filename |
| `source_file` | string | Original filename with extension |

### Section
A structural unit within a document, identified by heading detection. Sections form a hierarchy (e.g. "3. Safety > 3.1 PPE Requirements").

### Chunk
The primary output unit. One chunk contains content from one section.

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | string | Parent document ID |
| `document_name` | string | Parent document name |
| `section_path` | string | Full heading hierarchy |
| `chunk_text` | string | Content: text, Markdown tables, and image references |
| `chunk_type` | string | "text", "table", or "image" |
| `source_file` | string | Original filename |
| `image_refs` | string | Referenced image filenames (comma-separated) |
| `table_refs` | string | Referenced table section names |

### Table
Tables are converted to Markdown and embedded in chunk_text. The `chunk_type` field is set to "table" and `table_refs` records the table's section location.

### Image
Images are extracted to disk and referenced in chunk_text as `[Image: filename.png]` blocks. The `image_refs` field lists the filenames.

### Metadata
Each chunk carries metadata for filtering and retrieval: document_id, document_name, section_path, chunk_type, source_file.

## Current CSV Schema

Standard CSV with UTF-8 BOM encoding. All columns always present (empty string if no value).

```csv
document_id,document_name,section_path,chunk_text,chunk_type,source_file,image_refs,table_refs
DOC.001,Sample SOP,1.Purpose,This document defines...,text,sample_sop.docx,,
```

## Future JSONL Schema

Each line is a JSON object (implemented, available via `--format jsonl`):

```json
{
  "text": "This document defines...",
  "metadata": {
    "document_id": "DOC.001",
    "document_name": "Sample SOP",
    "section_path": "1.Purpose",
    "chunk_type": "text",
    "source_file": "sample_sop.docx"
  }
}
```

## Example Chunk Object

```json
{
  "document_id": "DOC.001",
  "document_name": "Warehouse SOP",
  "section_path": "3. Safety > 3.1 PPE Requirements",
  "chunk_text": "3.1 PPE Requirements\n\nAll personnel must wear: hard hat, safety boots, high-visibility vest.",
  "chunk_type": "text",
  "source_file": "warehouse_sop.docx",
  "image_refs": "",
  "table_refs": ""
}
```

## Metadata Design

Metadata serves two purposes:

1. **Retrieval filtering** — filter chunks by document, section, or type before similarity search
2. **Source attribution** — trace every answer back to its source document and section

The `section_path` field is especially important for industrial documents where the same term may appear in different contexts (e.g. "safety" in a PPE section vs. an emergency procedure section).

## Why section_path Matters

Generic text splitters cut documents by token count. This loses the structural context that makes chunks meaningful. A chunk about "PPE requirements" is more useful when the system knows it comes from "3. Safety > 3.1 PPE Requirements" rather than "page 7, tokens 1200-1800".

Section paths enable:
- **Filtered retrieval** — search only within safety sections
- **Hierarchical context** — the LLM knows the chunk's position in the document
- **Deduplication** — detect when the same section appears in multiple documents

## Why Tables Should Be Preserved

Tables contain structured data (equipment lists, safety matrices, process steps) that is lost when flattened to plain text. Converting to Markdown preserves the row/column relationships while remaining text-compatible for embedding models.

## Why Image References Should Not Be Dropped

Images in industrial documents often contain critical information: diagrams, safety warnings, equipment photos. Even if the image itself cannot be embedded, preserving the reference (`[Image: filename.png]`) allows:
- Human reviewers to locate the original image
- Future multimodal RAG systems to use the image
- Audit trails for compliance documents

## Compatibility Notes

### Dify
Dify accepts CSV with a `content` column and a `metadata` JSON column. Use `--format dify` to export in this format.

### LangChain
LangChain's `Document` schema uses `page_content` and `metadata` dict. The JSONL format maps directly: `text` → `page_content`, `metadata` → `metadata`.

### LlamaIndex
LlamaIndex's `Document` schema uses `text` and `metadata` dict. The JSONL format maps directly.

**Note:** Dify, LangChain, and LlamaIndex export formats are planned. Currently only CSV and JSONL are implemented.

## Current Implementation Status

| Feature | Status |
|---------|--------|
| DOCX parsing | Implemented |
| SOP / work instruction documents | Tested |
| Section-aware chunking | Implemented |
| Table extraction | Implemented |
| Image extraction | Implemented |
| CSV export | Implemented |
| JSONL export | Implemented |
| Dify CSV export | Experimental |
| PDF input | Roadmap |
| HTML / Markdown input | Roadmap |
| LangChain / LlamaIndex export | Roadmap |

# Examples

All sample documents and outputs in this directory are **synthetic**. They are designed to demonstrate the toolkit's capabilities without containing any real company data, internal SOPs, or confidential information.

## Demo Workflow

The fastest way to see the toolkit in action:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the Streamlit UI
streamlit run app/streamlit_app.py

# 3. Upload sample_manufacturing_sop.docx
#    (or any .docx file you have)

# 4. Click "Generate RAG-Ready Chunks"
#    — the app parses headings, tables, and images

# 5. Switch to the "Preview Output" tab
#    — filter by document, section, or chunk type

# 6. Switch to the "Eval Samples" tab
#    — generate synthetic QA pairs for retrieval testing

# 7. Download your files from the "Upload & Process" tab
#    — CSV, JSONL, Dify CSV, or extracted images ZIP
```

Alternatively, use the CLI:

```bash
# Single document
python scripts/process_single.py examples/sample_sop.docx --format csv

# Batch folder
python scripts/process_batch.py examples/ --format jsonl
```

## Sample Output Files

### sample_output.csv

Standard CSV export. One row per chunk, all metadata columns included.

| Column | Description |
|--------|-------------|
| `document_id` | Identifier extracted from filename |
| `document_name` | Document name from filename |
| `section_path` | Full heading hierarchy (e.g. "3. Safety > 3.1 PPE") |
| `chunk_text` | Content: text, Markdown tables, or image references |
| `chunk_type` | "text", "table", or "image" |
| `source_file` | Original filename |
| `image_refs` | Referenced image filenames (if any) |
| `table_refs` | Referenced table section names (if any) |

### sample_output.jsonl

One JSON object per line. Each line contains the chunk text and a metadata object. Ready for direct ingestion into vector databases or LangChain/LlamaIndex document loaders.

```json
{
  "text": "chunk content here",
  "metadata": {
    "document_id": "DOC.001",
    "document_name": "Sample SOP",
    "section_path": "1.Purpose",
    "chunk_type": "text",
    "source_file": "sample_sop.docx"
  }
}
```

### sample_dify_export.csv

Dify-compatible format. Two columns: `content` (the chunk text) and `metadata` (JSON string with document and section info). Import directly into a Dify knowledge base.

### sample_eval_samples.csv

Synthetic QA pairs generated from the processed chunks. Use these to test retrieval quality — upload them to your RAG system and check whether the retrieved chunks match the expected answers.

| Column | Description |
|--------|-------------|
| `question` | Generated question based on section name |
| `expected_answer` | Truncated chunk text (the ground truth) |
| `source_chunk_id` | Chunk identifier for tracing |
| `section_path` | Where this chunk lives in the document |
| `difficulty` | "easy", "medium", or "hard" |
| `question_type` | "purpose", "scope", "safety", "procedure", etc. |

## What Good RAG-Ready Chunks Look Like

A well-prepared chunk for RAG should have:

1. **One topic per chunk** — the chunk covers a single section or concept, not an entire page
2. **Structural context** — the `section_path` tells the retriever where this chunk sits in the document hierarchy
3. **Clean text** — no garbled formatting, no orphaned headers, no broken table structures
4. **Metadata for filtering** — `document_id`, `chunk_type`, and `section_path` let you filter before similarity search
5. **Preserved tables** — tables converted to Markdown, not flattened into unstructured text
6. **Image references** — even if the image can't be embedded, the reference is preserved for human review

Bad chunks look like page 3, tokens 400-900 with no context. Good chunks look like "Section 3.1 PPE Requirements: All personnel must wear hard hat, safety boots, and high-visibility vest."

## Adding Your Own Sample Documents

Drop any `.docx` file into this folder and run:

```bash
python scripts/process_single.py examples/your_document.docx --format csv
```

The output will appear in the `output/` directory.

**Important:** Only use synthetic or non-confidential documents. The `.gitignore` blocks `.docx` files from being committed.

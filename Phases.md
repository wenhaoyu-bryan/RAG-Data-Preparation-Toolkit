# Phase 2
Rewrite README.md for the renamed project "RAG Data Preparation Toolkit".

Requirements:

1. Title:
# RAG Data Preparation Toolkit

2. Subtitle:
A PM-friendly document preprocessing pipeline for building RAG-ready knowledge bases.

3. Add "Why this project exists":
Explain that many RAG applications fail because source documents are messy, poorly chunked, and lack metadata.

4. Add "What it does":
The toolkit converts unstructured business and industrial documents into structured chunks with:
- section paths
- clean text chunks
- table content
- image references
- metadata
- exportable files for knowledge base ingestion

5. Add "Current implemented scope":
Clearly say the current version focuses on DOCX documents, especially SOPs and work instructions.

6. Add "Pipeline":
Use Mermaid diagram:
Raw Documents → Document Parser → Section Parser → Chunker → Table/Image Extractor → Metadata Builder → Exporter → RAG Knowledge Base

7. Add "Features":
Implemented:
- DOCX parsing
- section-aware chunking
- table extraction
- image extraction
- batch processing
- Streamlit upload UI
- CSV export

Roadmap:
- PDF support
- HTML / Markdown support
- JSONL export
- Dify export
- LangChain / LlamaIndex export
- evaluation sample generation
- retrieval quality dashboard

8. Add "Use cases":
- Industrial SOP knowledge base
- Maintenance guide assistant
- Internal policy knowledge base
- Training material search
- AI agent knowledge preparation
- AI PM RAG prototype preparation

9. Add "Quick start":
Include install and run commands.

10. Add "Output schema":
Explain core fields:
- document_id
- document_name
- chunk_id
- section_path
- chunk_text
- chunk_type
- source_file
- image_refs
- table_refs
- metadata_json

11. Add "AI PM Portfolio Notes":
Explain what product capabilities this project demonstrates:
- RAG data readiness thinking
- enterprise document understanding
- productized data pipeline design
- metadata-first knowledge base design
- no-code tool design for business users

12. Avoid saying unsupported features are already implemented.

#Phase 3
Refactor naming to make the project more general while preserving SOP as the first use case.

Requirements:
1. Replace user-facing old project name references with "RAG Data Preparation Toolkit".
2. Rename package-level concepts from SOP-only to document-oriented names where safe.
3. Keep existing SOP-related fields if needed for backward compatibility.
4. Prefer new generic naming:
   - sop_id → document_id
   - sop_name → document_name
   - sop_file → source_file
   - sop_processor → document_processor
5. If changing field names may break existing code, support both old and new names.
6. Update comments and docstrings.
7. Update Streamlit UI labels.
8. Do not remove existing SOP processing capability.

#Phase4
Refactor the codebase into a modular toolkit architecture.

Target structure:
- app/streamlit_app.py
- rag_data_toolkit/document_loader.py
- rag_data_toolkit/docx_parser.py
- rag_data_toolkit/section_parser.py
- rag_data_toolkit/chunker.py
- rag_data_toolkit/table_extractor.py
- rag_data_toolkit/image_extractor.py
- rag_data_toolkit/metadata_builder.py
- rag_data_toolkit/exporters.py
- scripts/process_single.py
- scripts/process_batch.py

Requirements:
1. Move reusable processing logic into rag_data_toolkit/.
2. Keep Streamlit UI separate from processing logic.
3. Keep compatibility wrappers for old scripts if needed.
4. Add __init__.py.
5. Keep current DOCX workflow working.
6. Do not add PDF / HTML / Markdown support yet unless the implementation is small and safe.
7. After refactoring, run syntax checks.
8. Update README command examples if file paths change.

#phase 5
Create docs/rag-data-contract.md.

Document title:
# RAG Data Contract

Purpose:
Define the standard output format for RAG-ready document chunks.

Include these sections:
1. Why a data contract is needed for RAG
2. Core entities:
   - Document
   - Section
   - Chunk
   - Table
   - Image
   - Metadata
3. Current CSV schema
4. Future JSONL schema
5. Example chunk object
6. Metadata design
7. Why section_path matters
8. Why tables should be preserved
9. Why image references should not be dropped
10. Compatibility notes for:
   - Dify
   - LangChain
   - LlamaIndex
11. Current implementation status:
   - DOCX supported
   - SOP / work instruction tested
   - other formats are roadmap

#phase 6
Implement export capabilities in rag_data_toolkit/exporters.py.

Requirements:
1. Preserve current CSV export.
2. Add JSONL export.
3. Add Dify-friendly CSV export.
4. Each exported chunk should include:
   - content or chunk_text
   - document_name
   - section_path
   - source_file
   - metadata
5. Add functions:
   - export_to_csv(chunks, output_path)
   - export_to_jsonl(chunks, output_path)
   - export_to_dify_csv(chunks, output_path)
6. Update Streamlit UI to allow export format selection.
7. Add download buttons for each available format.
8. Update README with export examples.
9. Do not add external RAG framework dependencies yet.

#phase 7
Add a lightweight RAG evaluation sample generator.

Requirements:
1. Create rag_data_toolkit/eval_generator.py.
2. Implement rule-based generation first, no external LLM API.
3. Generate evaluation samples from chunks.
4. Output fields:
   - question
   - expected_answer
   - source_chunk_id
   - section_path
   - difficulty
   - question_type
5. Use section_path and chunk_type to generate basic questions.
6. Example rules:
   - Purpose section → "What is the purpose of this document?"
   - Scope section → "What is the applicable scope?"
   - Procedure section → "What are the key steps?"
   - Safety section → "What safety precautions are mentioned?"
   - Troubleshooting section → "What should be checked when this issue occurs?"
7. Add Streamlit button:
   "Generate basic RAG evaluation samples"
8. Add download button for eval_samples.csv.
9. Document this as a starter evaluation dataset, not a full benchmark.


#phase 8
Improve the Streamlit UI for the renamed project.

UI title:
RAG Data Preparation Toolkit

Subtitle:
Convert messy enterprise documents into section-aware, metadata-rich chunks for RAG knowledge bases.

Requirements:
1. Add sidebar workflow:
   - Upload documents
   - Processing settings
   - Export format
   - Output preview
2. Add main workflow sections:
   - Step 1: Upload document
   - Step 2: Configure parsing options
   - Step 3: Generate RAG-ready chunks
   - Step 4: Preview structured output
   - Step 5: Export data
3. Add summary metrics:
   - Documents processed
   - Chunks generated
   - Tables extracted
   - Images extracted
   - Export files generated
4. Add preview table:
   - document_name
   - section_path
   - chunk_type
   - chunk_text
5. Add filters:
   - document
   - section_path
   - chunk_type
6. Add download buttons:
   - CSV
   - JSONL
   - Dify CSV
   - eval samples
   - extracted images zip if available
7. Keep the interface simple and reliable.
8. Avoid heavy frontend dependencies.

#phase 9 
#add a mermaid graph for my front project page README.md
code:
flowchart LR
    A[Raw Documents<br/>DOCX / SOP / Manuals] --> B[Document Parser]
    B --> C[Section Parser]
    C --> D[Section-aware Chunker]
    D --> E[Table Extractor]
    D --> F[Image Extractor]
    D --> G[Metadata Builder]
    E --> H[RAG Data Contract]
    F --> H
    G --> H
    H --> I[CSV Export]
    H --> J[JSONL Export]
    H --> K[Dify CSV Export]
    I --> L[RAG Knowledge Base]
    J --> L
    K --> L
    L --> M[AI Agent / SOP Assistant / Knowledge Search]

    
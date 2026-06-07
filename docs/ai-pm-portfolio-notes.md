# AI PM Portfolio Notes

## What This Project Demonstrates

### Product Thinking
- Identified a real enterprise pain point: industrial SOP documents are trapped in Word format
- Designed a solution that bridges the gap between unstructured documents and RAG systems
- Prioritized the most common document type (.docx) for v1, with clear roadmap for expansion

### Technical Product Management
- Defined a clear data contract (rag-data-contract.md) for downstream consumers
- Built eval sample generation into the product — not an afterthought
- Multi-format export shows understanding of the fragmented RAG ecosystem (Dify, LangChain, LlamaIndex)

### Execution
- End-to-end pipeline from document ingestion to structured output
- Handles real-world document complexity (nested tables, inline images, inconsistent heading styles)
- Streamlit UI makes the tool accessible to non-technical stakeholders

## Interview Talking Points

1. **"Why RAG data prep?"** — Most RAG projects fail at data quality, not model quality. This tool addresses the upstream bottleneck.

2. **"How does this compare to existing tools?"** — Generic document splitters (LangChain text splitters) lose section context. This tool preserves document hierarchy, which directly improves retrieval relevance.

3. **"What was the hardest part?"** — Heading detection in Chinese industrial documents. No consistent styling across organizations. Solved with a 3-tier priority system (style > numbering > keywords).

4. **"What would you do differently?"** — Start with PDF support from day one — many enterprises have scanned SOPs. Also, build the eval pipeline first to establish quality baselines before optimizing the parser.

## Metrics to Track

- Documents processed
- Chunk quality (manual eval on sample set)
- Heading detection accuracy (ground truth vs predicted)
- Table attribution accuracy
- User feedback from Streamlit UI

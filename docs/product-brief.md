# Product Brief: RAG Data Preparation Toolkit

## Problem

Industrial enterprises have thousands of SOP documents (Word format) that contain critical operational knowledge. Converting these into RAG-ready structured data is manual, slow, and error-prone.

## Solution

An automated pipeline that ingests industrial SOP / work instruction / maintenance guide documents and produces structured, metadata-tagged chunks suitable for RAG systems.

## Target Users

- **AI Product Managers** building internal knowledge assistants
- **Data Engineers** preparing training data for enterprise RAG systems
- **Operations Teams** digitizing SOP documentation

## Key Differentiators

1. **Section-aware parsing** — not just text splitting; understands document hierarchy
2. **Industrial document focus** — handles tables, images, captions specific to SOP formats
3. **Multi-format export** — CSV, JSONL, Dify-native, LangChain, LlamaIndex
4. **Eval sample generation** — synthetic QA pairs for RAG quality testing
5. **Local-first** — no cloud dependencies, runs entirely on-premise

## Success Metrics

- Processing speed: <1 second per page
- Heading detection accuracy: >95%
- Table attribution accuracy: >90%
- Image/caption association: 100% extraction rate

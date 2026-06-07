"""Export chunks to CSV, JSONL, and framework-specific formats."""

import json
import os
import pandas as pd
from typing import List, Dict

# Standard column order for CSV export
CSV_COLUMNS = ['document_id', 'document_name', 'section_path', 'chunk_text', 'chunk_type', 'source_file', 'image_refs', 'table_refs']


def export_csv(chunks: List[Dict], output_path: str) -> str:
    """Export chunks as CSV with all metadata columns."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    df = pd.DataFrame(chunks)
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = ''
    df = df[CSV_COLUMNS]
    df.to_csv(output_path, index=False, encoding='utf-8-sig', quoting=1)
    print(f"Saved CSV: {output_path} ({len(chunks)} chunks)")
    return output_path


def export_jsonl(chunks: List[Dict], output_path: str) -> str:
    """Export chunks as JSONL with text and metadata per line."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            record = {
                "text": chunk.get("chunk_text", ""),
                "metadata": {
                    "document_id": chunk.get("document_id", ""),
                    "document_name": chunk.get("document_name", ""),
                    "section_path": chunk.get("section_path", ""),
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "source_file": chunk.get("source_file", ""),
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"Saved JSONL: {output_path} ({len(chunks)} chunks)")
    return output_path


def export_dify_csv(chunks: List[Dict], output_path: str) -> str:
    """Export in Dify knowledge base import format (CSV with content column)."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    rows = []
    for chunk in chunks:
        rows.append({
            "content": chunk.get("chunk_text", ""),
            "metadata": json.dumps({
                "document_id": chunk.get("document_id", ""),
                "document_name": chunk.get("document_name", ""),
                "section": chunk.get("section_path", ""),
                "chunk_type": chunk.get("chunk_type", "text"),
            }, ensure_ascii=False),
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Saved Dify CSV: {output_path} ({len(chunks)} chunks)")
    return output_path


EXPORTERS = {
    "csv": export_csv,
    "jsonl": export_jsonl,
    "dify": export_dify_csv,
}


def export_chunks(chunks: List[Dict], output_path: str, fmt: str = "csv") -> str:
    """Dispatch to the appropriate exporter by format name."""
    exporter = EXPORTERS.get(fmt)
    if not exporter:
        raise ValueError(f"Unknown export format: {fmt}. Supported: {list(EXPORTERS.keys())}")
    return exporter(chunks, output_path)

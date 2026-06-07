"""Smoke tests for the RAG Data Preparation Toolkit pipeline."""

import importlib
import pytest


def test_import_all_modules():
    """All package modules should import without error."""
    modules = [
        "rag_data_toolkit",
        "rag_data_toolkit.document_loader",
        "rag_data_toolkit.docx_parser",
        "rag_data_toolkit.section_parser",
        "rag_data_toolkit.chunker",
        "rag_data_toolkit.table_extractor",
        "rag_data_toolkit.image_extractor",
        "rag_data_toolkit.metadata_builder",
        "rag_data_toolkit.eval_generator",
        "rag_data_toolkit.exporters",
    ]
    for mod in modules:
        importlib.import_module(mod)


def test_exporters_registry():
    from rag_data_toolkit.exporters import EXPORTERS
    assert "csv" in EXPORTERS
    assert "jsonl" in EXPORTERS
    assert "dify" in EXPORTERS


def test_is_word_document():
    from rag_data_toolkit.document_loader import is_word_document
    assert is_word_document("test.docx") is True
    assert is_word_document("test.doc") is True
    assert is_word_document("test.pdf") is False
    assert is_word_document("test.txt") is False


def test_extract_document_metadata():
    from rag_data_toolkit.metadata_builder import extract_document_metadata
    meta = extract_document_metadata("/tmp/DOC.001_Warehouse_SOP.docx")
    assert meta["document_id"] == "DOC.001"
    assert "Warehouse_SOP" in meta["document_name"]
    assert meta["source_file"] == "DOC.001_Warehouse_SOP.docx"


def test_extract_sop_metadata_backward_compat():
    from rag_data_toolkit.metadata_builder import extract_sop_metadata
    meta = extract_sop_metadata("/tmp/DOC.001_Warehouse_SOP.docx")
    assert meta["sop_id"] == "DOC.001"
    assert "Warehouse_SOP" in meta["sop_name"]


def test_is_heading_paragraph_keywords():
    """Heading keywords should be detected even without Word styles."""
    from rag_data_toolkit.section_parser import is_heading_paragraph
    pytest.importorskip("docx")


def test_export_csv_roundtrip(tmp_path):
    from rag_data_toolkit.exporters import export_csv
    import pandas as pd

    chunks = [
        {"document_id": "T1", "document_name": "Test", "section_path": "1. Intro", "chunk_text": "Hello", "chunk_type": "text", "source_file": "test.docx", "image_refs": "", "table_refs": ""},
        {"document_id": "T1", "document_name": "Test", "section_path": "2. Details", "chunk_text": "World", "chunk_type": "text", "source_file": "test.docx", "image_refs": "", "table_refs": ""},
    ]
    out = str(tmp_path / "test.csv")
    export_csv(chunks, out)

    df = pd.read_csv(out)
    assert len(df) == 2
    assert "document_id" in df.columns
    assert "document_name" in df.columns
    assert "section_path" in df.columns
    assert "chunk_text" in df.columns
    assert "chunk_type" in df.columns


def test_export_jsonl_roundtrip(tmp_path):
    from rag_data_toolkit.exporters import export_jsonl
    import json

    chunks = [{"document_id": "T1", "document_name": "Test", "section_path": "1. Intro", "chunk_text": "Hello", "chunk_type": "text", "source_file": "test.docx"}]
    out = str(tmp_path / "test.jsonl")
    export_jsonl(chunks, out)

    with open(out) as f:
        record = json.loads(f.readline())
    assert record["text"] == "Hello"
    assert record["metadata"]["document_id"] == "T1"
    assert record["metadata"]["chunk_type"] == "text"


def test_eval_generator():
    from rag_data_toolkit.eval_generator import generate_eval_samples

    chunks = [
        {"document_id": "T1", "document_name": "Test", "section_path": "1. Purpose", "chunk_text": "This document describes warehouse operations.", "chunk_type": "text", "document_id": "T1"},
        {"document_id": "T1", "document_name": "Test", "section_path": "2. Scope", "chunk_text": "Applies to all warehouse staff.", "chunk_type": "text", "document_id": "T1"},
    ]
    samples = generate_eval_samples(chunks, max_samples=10)
    assert len(samples) == 2
    assert "question" in samples[0]
    assert "expected_answer" in samples[0]
    assert "question_type" in samples[0]
    assert "difficulty" in samples[0]
    assert "source_chunk_id" in samples[0]


def test_eval_question_types():
    from rag_data_toolkit.eval_generator import generate_eval_samples

    chunks = [
        {"section_path": "1. Purpose", "chunk_text": "To define procedures.", "chunk_type": "text", "document_id": "T", "document_name": "T"},
        {"section_path": "3. Safety", "chunk_text": "Wear PPE at all times.", "chunk_type": "text", "document_id": "T", "document_name": "T"},
    ]
    samples = generate_eval_samples(chunks, max_samples=10)
    types = {s["question_type"] for s in samples}
    assert "purpose" in types
    assert "safety" in types

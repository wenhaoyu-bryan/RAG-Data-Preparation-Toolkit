"""Generate synthetic evaluation QA samples from processed chunks."""

import json
import os
import re
from typing import List, Dict

# Section keyword to question type mapping
SECTION_QUESTION_MAP = [
    (r'purpose|目的', "What is the purpose of this document?", "purpose"),
    (r'scope|适用范围', "What is the applicable scope?", "scope"),
    (r'safety|安全|PPE', "What safety precautions are mentioned?", "safety"),
    (r'procedure|操作|步骤|流程', "What are the key steps in this procedure?", "procedure"),
    (r'troubleshoot|故障|问题|异常', "What should be checked when this issue occurs?", "troubleshooting"),
    (r'responsib|职责', "What are the responsibilities defined?", "responsibility"),
    (r'definition|定义|缩写', "What terms and definitions are provided?", "definition"),
    (r'history|历史|版本|revision', "What is the version history?", "history"),
    (r'table|表格', "What information is in this table?", "table"),
]

DIFFICULTY_MAP = {
    "purpose": "easy",
    "scope": "easy",
    "definition": "easy",
    "responsibility": "medium",
    "safety": "medium",
    "procedure": "medium",
    "troubleshooting": "hard",
    "history": "easy",
    "table": "medium",
}


def generate_eval_samples(chunks: List[Dict], max_samples: int = 50) -> List[Dict]:
    """Generate evaluation QA pairs from chunks using rule-based heuristics.

    This is a starter evaluation dataset, not a full benchmark.
    Samples should be reviewed and refined by a human before use.
    """
    samples = []
    for i, chunk in enumerate(chunks[:max_samples]):
        section_path = chunk.get("section_path", "")
        text = chunk.get("chunk_text", "")
        document_id = chunk.get("document_id", "")
        document_name = chunk.get("document_name", "")
        chunk_type = chunk.get("chunk_type", "text")

        if not text.strip() or not section_path:
            continue

        # Extract leaf section name
        leaf = section_path.split(" > ")[-1] if " > " in section_path else section_path
        clean_leaf = re.sub(r'^\d+(?:\.\d+)*\s*', '', leaf).strip()

        if not clean_leaf:
            continue

        # Match section to question type
        question, question_type = _match_question_type(clean_leaf, section_path, chunk_type)
        difficulty = DIFFICULTY_MAP.get(question_type, "medium")

        expected_answer = _truncate(text, 500)

        samples.append({
            "question": question,
            "expected_answer": expected_answer,
            "source_chunk_id": f"{document_id}_{i}",
            "section_path": section_path,
            "difficulty": difficulty,
            "question_type": question_type,
            "document_id": document_id,
            "document_name": document_name,
        })

    return samples


def _match_question_type(leaf: str, section_path: str, chunk_type: str) -> tuple:
    """Match a section name to a question template and type."""
    combined = (leaf + " " + section_path).lower()

    for pattern, question, q_type in SECTION_QUESTION_MAP:
        if re.search(pattern, combined, re.IGNORECASE):
            return question, q_type

    if chunk_type == "table":
        return "What information is contained in this table?", "table"

    # Default
    return f"What does the document say about {leaf}?", "general"


def export_eval_samples(samples: List[Dict], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if output_path.endswith('.jsonl'):
        with open(output_path, 'w', encoding='utf-8') as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + '\n')
    else:
        import pandas as pd
        df = pd.DataFrame(samples)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"Saved eval samples: {output_path} ({len(samples)} samples)")
    return output_path


def _truncate(text: str, max_len: int) -> str:
    text = text.replace('\n', ' ').strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."

"""Process a single .docx document into RAG-ready chunks."""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from rag_data_toolkit.chunker import process_document
from rag_data_toolkit.eval_generator import generate_eval_samples, export_eval_samples


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_single.py <docx_path> [--format csv|jsonl|dify]")
        sys.exit(1)

    docx_path = sys.argv[1]
    export_format = "csv"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            export_format = sys.argv[idx + 1]

    if not os.path.exists(docx_path):
        print(f"Error: '{docx_path}' does not exist")
        sys.exit(1)

    output_dir = os.path.join(PROJECT_ROOT, "output")
    chunks = process_document(docx_path, output_dir, export_format)

    if chunks:
        # Also generate eval samples
        eval_path = os.path.join(output_dir, "eval_samples.csv")
        samples = generate_eval_samples(chunks)
        if samples:
            export_eval_samples(samples, eval_path)
        print("Done")
    else:
        print("Failed — no chunks generated")
        sys.exit(1)


if __name__ == "__main__":
    main()

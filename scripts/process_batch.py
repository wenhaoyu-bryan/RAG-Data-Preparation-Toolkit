"""Batch-process all .docx files in a folder."""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from rag_data_toolkit.document_loader import is_word_document
from rag_data_toolkit.chunker import process_document


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_batch.py <folder_path> [--format csv|jsonl|dify]")
        sys.exit(1)

    folder_path = sys.argv[1]
    export_format = "csv"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            export_format = sys.argv[idx + 1]

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a directory")
        sys.exit(1)

    all_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if is_word_document(f)
    ]

    if not all_files:
        print(f"No Word documents found in '{folder_path}'")
        sys.exit(1)

    print(f"Found {len(all_files)} document(s)")
    output_dir = os.path.join(PROJECT_ROOT, "output")

    success = 0
    failed = 0
    for i, docx_path in enumerate(all_files, 1):
        print(f"\n[{i}/{len(all_files)}] {os.path.basename(docx_path)}")
        try:
            result = process_document(docx_path, output_dir, export_format)
            if result:
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Error: {e}")
            failed += 1

    print(f"\nBatch complete: {success} succeeded, {failed} failed out of {len(all_files)}")


if __name__ == "__main__":
    main()

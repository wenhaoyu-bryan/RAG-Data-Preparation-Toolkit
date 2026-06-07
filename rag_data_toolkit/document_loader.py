"""Load and validate Word documents."""

import os
from docx import Document


def is_word_document(filename: str) -> bool:
    return filename.lower().endswith(('.docx', '.doc'))


def validate_file(path: str) -> bool:
    if not os.path.exists(path):
        print(f"Error: file '{path}' does not exist")
        return False
    if not is_word_document(path):
        print(f"Error: file '{path}' is not a Word document")
        return False
    return True


def load_document(path: str) -> Document:
    return Document(path)

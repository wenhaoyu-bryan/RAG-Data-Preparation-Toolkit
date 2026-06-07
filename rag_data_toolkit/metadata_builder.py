"""Extract document metadata from filename and document content."""

import os
import re
from typing import Dict


def extract_document_metadata(docx_path: str) -> Dict[str, str]:
    """Extract document_id, document_name, source_file from a .docx path."""
    base_name = os.path.splitext(os.path.basename(docx_path))[0]

    # Try to extract a structured ID prefix (e.g. DOC.001 or WH-SOP-003)
    id_match = re.match(r'^([A-Z0-9.\-]+)', base_name)
    document_id = id_match.group(1) if id_match else "unknown"

    if document_id != "unknown" and base_name.startswith(document_id):
        document_name = base_name[len(document_id):].strip() or base_name
    else:
        document_name = base_name

    return {
        "document_id": document_id,
        "document_name": document_name,
        "source_file": os.path.basename(docx_path),
    }


# Backward-compatible alias
def extract_sop_metadata(docx_path: str) -> Dict[str, str]:
    """Backward-compatible wrapper. Use extract_document_metadata instead."""
    meta = extract_document_metadata(docx_path)
    return {
        "sop_id": meta["document_id"],
        "sop_name": meta["document_name"],
        "source_file": meta["source_file"],
    }

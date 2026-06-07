"""Low-level Word document block iteration and section map building."""

import re
from typing import Dict, List
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from . import section_parser


def iter_block_items(doc: Document):
    """Yield paragraphs and tables in document order."""
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def build_paragraph_section_map(doc) -> Dict[int, str]:
    """Pre-scan paragraphs to build a paragraph-index → section-path map."""
    paragraph_section_map: Dict[int, str] = {}
    tmp_stack: List[str] = []
    tmp_counters: List[int] = []

    for i, p in enumerate(doc.paragraphs):
        if section_parser.is_heading_paragraph(p):
            h_text = p.text.strip()
            h_level = section_parser.get_heading_level(p)
            number_match = re.match(r'^(\d+(?:\.\d+)*)', h_text)
            if number_match:
                explicit_numbers = [int(n) for n in number_match.group(1).split('.') if n.isdigit()]
                tmp_counters = explicit_numbers.copy()
                numbered_text = h_text
            else:
                if len(tmp_counters) < h_level:
                    tmp_counters += [0] * (h_level - len(tmp_counters))
                else:
                    tmp_counters = tmp_counters[:h_level]
                if not tmp_counters:
                    tmp_counters = [1]
                else:
                    tmp_counters[-1] += 1
                number_str = '.'.join(str(x) for x in tmp_counters)
                if h_level == 1:
                    numbered_text = f"{number_str}. {h_text}" if not re.match(r'^\d', h_text) else h_text
                else:
                    numbered_text = f"{number_str} {h_text}" if not re.match(r'^\d', h_text) else h_text
            if tmp_stack and len(tmp_stack) >= h_level:
                tmp_stack = tmp_stack[:h_level - 1]
            tmp_stack.append(numbered_text)
        paragraph_section_map[i] = " > ".join(tmp_stack)

    return paragraph_section_map

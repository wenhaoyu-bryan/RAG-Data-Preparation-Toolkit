"""Extract and convert Word tables to Markdown with section attribution."""

from typing import List, Dict
from docx.table import Table
from . import section_parser


def table_to_markdown(table: Table) -> str:
    if not table.rows:
        return ""

    markdown_lines = []
    header_row = table.rows[0]
    header_cells = [cell.text.strip() for cell in header_row.cells]
    markdown_lines.append("| " + " | ".join(header_cells) + " |")
    markdown_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")

    for row in table.rows[1:]:
        cells = [cell.text.strip() for cell in row.cells]
        markdown_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(markdown_lines)


def build_table_section_path(table_section: str, heading_stack: List[str]) -> str:
    """Build section path for a table given its identified section and current heading stack."""
    for i, heading in enumerate(heading_stack):
        if table_section.startswith(heading.split()[0]):
            return " > ".join(heading_stack[:i + 1]) + f" > {table_section}"
    return table_section


def build_table_position_map(doc) -> Dict[int, str]:
    """Pre-scan document to record the heading path at each table's position."""
    from .docx_parser import iter_block_items
    from docx.text.paragraph import Paragraph
    from docx.table import Table as DocxTable
    import re

    table_position_section: Dict[int, str] = {}
    temp_heading_stack: List[str] = []
    temp_counters: List[int] = []
    table_index = 0

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            if section_parser.is_heading_paragraph(block):
                h_text = block.text.strip()
                h_level = section_parser.get_heading_level(block)
                number_match = re.match(r'^(\d+(?:\.\d+)*)', h_text)
                if number_match:
                    explicit_numbers = [int(n) for n in number_match.group(1).split('.') if n.isdigit()]
                    temp_counters = explicit_numbers.copy()
                    numbered_text = h_text
                else:
                    if len(temp_counters) < h_level:
                        temp_counters += [0] * (h_level - len(temp_counters))
                    else:
                        temp_counters = temp_counters[:h_level]
                    if not temp_counters:
                        temp_counters = [1]
                    else:
                        temp_counters[-1] += 1
                    number_str = '.'.join(str(x) for x in temp_counters)
                    if h_level == 1:
                        numbered_text = f"{number_str}. {h_text}" if not re.match(r'^\d', h_text) else h_text
                    else:
                        numbered_text = f"{number_str} {h_text}" if not re.match(r'^\d', h_text) else h_text

                if temp_heading_stack:
                    if len(temp_heading_stack) >= h_level:
                        temp_heading_stack = temp_heading_stack[:h_level - 1]
                temp_heading_stack.append(numbered_text)
        elif isinstance(block, DocxTable):
            table_position_section[table_index] = " > ".join(temp_heading_stack)
            table_index += 1

    return table_position_section

"""Main orchestration: parse document into RAG-ready chunks with metadata."""

import os
import re
from collections import defaultdict
from typing import Dict, List

from .document_loader import load_document
from .metadata_builder import extract_document_metadata
from .docx_parser import iter_block_items, build_paragraph_section_map
from .section_parser import is_heading_paragraph, get_heading_level, build_section_path
from .table_extractor import table_to_markdown, build_table_position_map
from .image_extractor import (
    extract_images_with_captions_from_docx,
    create_enhanced_image_chunk_content,
    find_image_references_in_text,
    identify_image_section,
)
from .exporters import export_csv


def normalize_list_symbols(text: str) -> str:
    text = re.sub(r'^[·•]\s*', '* ', text, flags=re.MULTILINE)
    text = re.sub(r'^--\t', '* ', text, flags=re.MULTILINE)
    text = re.sub(r'^、\s*', '* ', text, flags=re.MULTILINE)
    return text


def clean_duplicate_captions(text: str) -> str:
    if '[Image:' not in text:
        return text
    first_idx = text.find('[Image:')
    prefix = text[:first_idx]
    rest = text[first_idx:]
    caption_in_brackets = set()
    for m in re.finditer(r"\[Image: [^\]]*?(?:\nImage content: ([^\]]+))?\]", text, re.S):
        cap = (m.group(1) or '').strip()
        if cap:
            caption_in_brackets.add(cap)
    cleaned_lines = []
    for line in prefix.split('\n'):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue
        if re.match(r'^(图表|图|Figure|Fig)\s*\d+', stripped):
            continue
        if not re.match(r'^\d', stripped) and stripped in caption_in_brackets:
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines) + rest


def process_document(docx_path: str, output_dir: str = "output", export_format: str = "csv") -> list:
    """Process a document into RAG-ready chunks.

    Returns list of chunk dicts. Also exports to the requested format.
    """
    print("=" * 60)
    print("RAG Data Preparation Toolkit — Document Processing")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(os.path.dirname(script_dir), 'extracted_images')
    os.makedirs(images_dir, exist_ok=True)

    # Extract images
    print("Extracting images and captions...")
    image_info = extract_images_with_captions_from_docx(docx_path, images_dir)

    # Build ordered image list
    ordered_images = _build_ordered_images(image_info)
    print(f"Extracted {len(ordered_images)} images")

    # Load document
    try:
        doc = load_document(docx_path)
        print(f"Loaded document: {docx_path}")
    except Exception as e:
        print(f"Failed to load document: {e}")
        return []

    # Metadata
    metadata = extract_document_metadata(docx_path)
    document_id = metadata["document_id"]
    document_name = metadata["document_name"]
    source_file = metadata["source_file"]
    print(f"Document ID: {document_id}")
    print(f"Document Name: {document_name}")

    # Pre-scans
    table_position_section = build_table_position_map(doc)
    paragraph_section_map = build_paragraph_section_map(doc)

    # Collect caption set for skipping caption-as-heading
    caption_set = set()
    for _img in image_info.values():
        cap = (_img.get("caption") or "").strip()
        if cap:
            caption_set.add(cap)

    # Build chunks
    chunks = _generate_chunks(doc, document_id, document_name, source_file,
                              image_info, ordered_images,
                              table_position_section, paragraph_section_map, caption_set)

    # Post-process: embed images into chunks
    _embed_images(chunks, ordered_images, image_info, table_position_section, paragraph_section_map, doc)

    # Clean duplicate captions
    for ch in chunks:
        ch_text = ch.get('chunk_text', '')
        if ch_text:
            ch['chunk_text'] = clean_duplicate_captions(ch_text)

    # Embed remaining unused images
    _embed_unused_images(chunks, ordered_images)

    print(f"Total chunks generated: {len(chunks)}")

    if not chunks:
        print("Processing failed — no chunks generated")
        return []

    # Export
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    ext_map = {"csv": ".csv", "jsonl": ".jsonl", "dify": ".csv"}
    ext = ext_map.get(export_format, ".csv")
    output_file = os.path.join(output_dir, f"{base_name}_processed{ext}")

    from .exporters import export_chunks
    export_chunks(chunks, output_file, export_format)

    return chunks


# --- Internal helpers ---

def _build_ordered_images(image_info: Dict) -> List[Dict]:
    ordered = []
    for image_id, info in image_info.items():
        match = re.search(r'image_?(\d+)', image_id)
        if match:
            index = int(match.group(1))
            ordered.append({
                'index': index,
                'id': image_id,
                'filename': info['filename'],
                'caption': info.get('caption', ''),
                'used': False,
                'is_table_image': info.get('is_table_image', False),
                'table_index': info.get('table_index', -1),
            })

    ordered.sort(key=lambda x: x['index'])

    for i, img_data in enumerate(ordered, 1):
        old_filename = img_data['filename']
        doc_name = old_filename.split('_image_id____')[0]
        new_filename = f"{doc_name}_image_id____image{i}.{old_filename.split('.')[-1]}"
        img_data['filename'] = new_filename
        img_data['new_index'] = i

    return ordered


def _assign_numbered_heading(h_text: str, h_level: int, counters: List[int]) -> str:
    number_match = re.match(r'^(\d+(?:\.\d+)*)', h_text)
    if number_match:
        explicit = [int(n) for n in number_match.group(1).split('.') if n.isdigit()]
        counters.clear()
        counters.extend(explicit)
        return h_text

    if len(counters) < h_level:
        counters.extend([0] * (h_level - len(counters)))
    else:
        del counters[h_level:]
    if not counters:
        counters.append(1)
    else:
        counters[-1] += 1

    number_str = '.'.join(str(x) for x in counters)
    if not h_text:
        return number_str + ('.' if h_level == 1 else '')
    if re.match(r'^\d', h_text):
        return h_text
    return f"{number_str}. {h_text}" if h_level == 1 else f"{number_str} {h_text}"


def _determine_chunk_type(combined_text: str) -> str:
    """Determine chunk type based on content."""
    if '[Image:' in combined_text and len(combined_text.strip().split('\n')) <= 3:
        return "image"
    if combined_text.strip().startswith('|') and '|---' in combined_text:
        return "table"
    return "text"


def _generate_chunks(doc, document_id, document_name, source_file,
                     image_info, ordered_images,
                     table_position_section, paragraph_section_map, caption_set) -> List[Dict]:
    chunks = []
    heading_stack = []
    current_content_buffer = []
    heading_counters: List[int] = []
    pending_ordered = [img['filename'] for img in ordered_images]
    pending_images = pending_ordered

    for block in iter_block_items(doc):
        if isinstance(block, type(doc.paragraphs[0])) or hasattr(block, 'text'):
            paragraph = block
            if is_heading_paragraph(paragraph):
                if paragraph.text.strip() in caption_set:
                    continue

                heading_text = paragraph.text.strip()
                heading_level = get_heading_level(paragraph)
                heading_text = _assign_numbered_heading(heading_text, heading_level, heading_counters)

                if current_content_buffer:
                    section_path = build_section_path(heading_stack)
                    combined_text = normalize_list_symbols('\n'.join(current_content_buffer))
                    first_line = combined_text.split('\n', 1)[0].strip()
                    if re.match(r'^\d+(?:\.\d+)*(?:\.)?\s*.+', first_line):
                        section_path = first_line

                    image_filename, image_section_path = _assign_image(
                        combined_text, section_path, pending_images)

                    if section_path:
                        image_refs = image_filename if image_filename else ""
                        chunks.append({
                            'document_id': document_id,
                            'document_name': document_name,
                            'section_path': section_path,
                            'chunk_text': combined_text,
                            'chunk_type': _determine_chunk_type(combined_text),
                            'source_file': source_file,
                            'image_refs': image_refs,
                            'table_refs': '',
                        })
                    current_content_buffer = []

                if len(heading_stack) >= heading_level:
                    heading_stack = heading_stack[:heading_level - 1]
                heading_stack.append(heading_text)
                current_content_buffer.append(heading_text)
                print(f"Heading: {heading_text} (level {heading_level})")
            else:
                if paragraph.text.strip():
                    current_content_buffer.append(paragraph.text.strip())
        else:
            pass

    # Flush remaining buffer
    if current_content_buffer:
        section_path = build_section_path(heading_stack)
        combined_text = normalize_list_symbols('\n'.join(current_content_buffer))
        first_line = combined_text.split('\n', 1)[0].strip()
        if re.match(r'^\d+(?:\.\d+)*(?:\.)?\s*.+', first_line):
            section_path = first_line

        image_filename, image_section_path = _assign_image(
            combined_text, section_path, pending_images)

        if section_path:
            image_refs = image_filename if image_filename else ""
            chunks.append({
                'document_id': document_id,
                'document_name': document_name,
                'section_path': section_path,
                'chunk_text': combined_text,
                'chunk_type': _determine_chunk_type(combined_text),
                'source_file': source_file,
                'image_refs': image_refs,
                'table_refs': '',
            })

    # Process tables
    table_counter_map = defaultdict(int)
    table_index = 0
    for block in iter_block_items(doc):
        from docx.table import Table as DocxTable
        if isinstance(block, DocxTable):
            markdown_table = table_to_markdown(block)
            if not markdown_table:
                continue
            position_path = table_position_section.get(table_index, "")
            if position_path:
                table_section_path = position_path
            else:
                table_section_path = "Unknown Section"

            leaf_title = table_section_path.split(' > ')[-1] if table_section_path else 'Table'
            table_counter_map[leaf_title] += 1

            chunks.append({
                'document_id': document_id,
                'document_name': document_name,
                'section_path': table_section_path,
                'chunk_text': f"{leaf_title}\n\n{markdown_table}",
                'chunk_type': 'table',
                'source_file': source_file,
                'image_refs': '',
                'table_refs': leaf_title,
            })
            table_index += 1

    return chunks


def _assign_image(combined_text: str, section_path: str, pending_images: list):
    """Assign an image to a chunk based on text references."""
    image_filename = ""
    image_section_path = ""
    image_refs = find_image_references_in_text(combined_text)

    if image_refs and pending_images:
        image_filename = pending_images.pop(0)
        image_section_path = identify_image_section(combined_text, section_path)
    elif pending_images and len(pending_images) <= 2:
        image_filename = pending_images.pop(0)
        image_section_path = identify_image_section(combined_text, section_path)

    return image_filename, image_section_path


def _embed_images(chunks, ordered_images, image_info, table_position_section,
                  paragraph_section_map, doc):
    """Post-process: embed images into matching chunks based on section."""
    for img in ordered_images:
        info = image_info.get(f"image_{img['index']}", {})
        cap_i = info.get('caption_index')
        forced_path = ''
        if cap_i is not None:
            if isinstance(cap_i, str) and cap_i.startswith('table_'):
                forced_path = ''
            else:
                j = cap_i
                while j >= 0:
                    forced_path = paragraph_section_map.get(j, '')
                    if forced_path:
                        break
                    j -= 1
        img['forced_section'] = forced_path

    for chunk in chunks:
        chunk_section = chunk.get('section_path', '')
        if not chunk_section:
            continue

        section_images = []
        for img_data in ordered_images:
            if img_data.get('used', False):
                continue

            assigned = False

            # Table images
            if img_data.get('is_table_image', False):
                tbl_idx = img_data.get('table_index', -1)
                if tbl_idx >= 0 and tbl_idx in table_position_section:
                    tbl_sec = table_position_section[tbl_idx]
                    if tbl_sec:
                        tbl_leaf = tbl_sec.split(' > ')[-1]
                        chunk_leaf = chunk_section.split(' > ')[-1] if ' > ' in chunk_section else chunk_section
                        if (chunk_section == tbl_sec or chunk_section.endswith(tbl_leaf)
                                or chunk_leaf == tbl_leaf or tbl_leaf in chunk_section):
                            assigned = True

            # Forced section
            forced_path = img_data.get('forced_section', '')
            if forced_path:
                forced_leaf = forced_path.split(' > ')[-1]
                if forced_leaf and (chunk_section.endswith(forced_leaf) or forced_path in chunk_section):
                    assigned = True

            # Caption matching
            caption = img_data.get('caption', '')
            if caption and not assigned:
                prefix_match = re.search(r'(\d+\.\d+)', caption)
                if prefix_match and prefix_match.group(1) in chunk_section:
                    assigned = True

            if assigned:
                section_images.append(img_data)

        if section_images:
            original = chunk['chunk_text']
            extra = ""
            for img_data in section_images:
                extra += "\n\n" + create_enhanced_image_chunk_content(
                    img_data['filename'], chunk_section, img_data['caption'])
                img_data['used'] = True
            chunk['chunk_text'] = original + extra
            # Update image_refs
            existing = chunk.get('image_refs', '')
            new_refs = [img['filename'] for img in section_images]
            chunk['image_refs'] = (existing + ', ' + ', '.join(new_refs)).strip(', ')


def _embed_unused_images(chunks, ordered_images):
    """Embed any remaining unused images into the last chunk with a section."""
    unused = [img for img in ordered_images if not img.get('used', False)]
    if not unused:
        return

    print(f"Embedding {len(unused)} unused images (fallback)")
    for img_data in unused:
        forced_path = img_data.get('forced_section', '')
        placed = False
        if forced_path:
            forced_leaf = forced_path.split(' > ')[-1]
            for chunk in chunks:
                sec = chunk.get('section_path', '')
                if forced_leaf and (sec.endswith(forced_leaf) or forced_path in sec):
                    enhanced = create_enhanced_image_chunk_content(
                        img_data['filename'], sec, img_data['caption'])
                    chunk['chunk_text'] = chunk['chunk_text'] + "\n\n" + enhanced
                    img_data['used'] = True
                    placed = True
                    break

        if not placed:
            fallback_sec = ''
            for chunk in reversed(chunks):
                if chunk.get('section_path'):
                    fallback_sec = chunk['section_path']
                    break
            if not fallback_sec:
                fallback_sec = 'Unknown Section'
            enhanced = create_enhanced_image_chunk_content(
                img_data['filename'], fallback_sec, img_data['caption'])
            for chunk in reversed(chunks):
                if chunk.get('section_path'):
                    chunk['chunk_text'] = chunk['chunk_text'] + "\n\n" + enhanced
                    break
            img_data['used'] = True

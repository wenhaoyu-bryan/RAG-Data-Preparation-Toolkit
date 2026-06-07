"""Heading detection and level extraction for Word paragraphs."""

import re
from typing import List
from docx.text.paragraph import Paragraph

TOP_LEVEL_KEYWORDS = [
    "目的", "适用范围", "安全和环境要求", "环境和安全说明", "相关文件", "职责",
    "定义和缩写", "活动描叙", "具体操作如下", "附录", "历史纪录",
]


def is_heading_paragraph(paragraph: Paragraph) -> bool:
    style_name = paragraph.style.name
    if 'Heading' in style_name or '标题' in style_name:
        return True
    if re.match(r'^H\d+$', style_name):
        return True

    text = paragraph.text.strip()

    if re.match(r'^\d+(?:\.\d+)+', text):
        return True
    if re.match(r'^\d+\)', text):
        return True

    clean_text = re.sub(r'^\d+(?:\.\d+)*[.\)]\s*', '', text).strip()
    if clean_text in TOP_LEVEL_KEYWORDS:
        return True

    if not re.match(r'^\d+', text) and clean_text in TOP_LEVEL_KEYWORDS:
        return False

    if "活动描述" in text and re.match(r'^\d+\.', text):
        return True

    if re.match(r'^\d+\.\s*', text):
        title_keywords = [
            "目的", "适用范围", "职责", "活动描述", "相关文件", "定义",
            "附录", "历史", "记录", "规程", "说明", "注意事项",
        ]
        if any(keyword in clean_text for keyword in title_keywords):
            return True

    return False


def get_heading_level(paragraph: Paragraph) -> int:
    style_name = paragraph.style.name
    if 'Heading' in style_name:
        match = re.search(r'Heading\s*(\d+)', style_name)
        if match:
            return int(match.group(1))
    elif '标题' in style_name:
        match = re.search(r'标题\s*(\d+)', style_name)
        if match:
            return int(match.group(1))
    else:
        m = re.match(r'^H(\d+)$', style_name)
        if m:
            return int(m.group(1))

    text = paragraph.text.strip()

    match = re.match(r'^(\d+(?:\.\d+)+)', text)
    if match:
        return min(match.group(1).count('.') + 1, 10)

    if re.match(r'^\d+\)', text):
        return 1
    if re.match(r'^\d+\.\s*', text):
        return 1

    clean_text = re.sub(r'^\d+(?:\.\d+)*[.\)]\s*', '', text).strip()
    if clean_text in TOP_LEVEL_KEYWORDS:
        return 1

    if "活动描述" in text and re.match(r'^\d+\.', text):
        return 1

    return 1


def build_section_path(heading_stack: List[str]) -> str:
    return " > ".join(heading_stack)

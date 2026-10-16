#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
# Modified 2026-10-15: portable report generation and distribution.
"""Apply role/group spacing only to freshly generated numbered HWPX documents."""
import argparse
import json
from pathlib import Path
import re
from hwpx.document import HwpxDocument

MARKERS = [r'\d+\.', r'[가-힣]\.', r'\d+\)', r'[가-힣]\)',
           r'\(\d+\)', r'\([가-힣]\)', r'[①-⑳]', r'[㉮-㉻]']


def level_of(paragraph):
    for level, marker in enumerate(MARKERS):
        if re.match(r'^' + marker + r'\s', paragraph.text.strip()):
            return level
    # kordoc 4.9's suppressed singleton paragraphs have no visible marker.
    ref = str(paragraph.para_pr_id_ref)
    if ref.isdigit() and 25 <= int(ref) <= 32:
        return int(ref) - 25
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('out')
    args = parser.parse_args()
    profile = json.loads((Path(__file__).parent.parent / 'references/paragraph-spacing.json').read_text())
    doc = HwpxDocument.open(args.source)
    original = [p.text for p in doc.paragraphs]
    levels = [level_of(p) if not p.tables else None for p in doc.paragraphs]
    previous_level = None
    previous_was_list = False
    changes = []
    for index, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if paragraph.tables or not text:
            previous_was_list = False
            continue
        level = levels[index]
        is_note = bool(re.match(r'^(?:※|\*)\s', text))
        before = profile['before_pt']
        if level is not None:
            if previous_level is None:
                role = 'first_item'
            elif level == 0:
                role = 'new_major'
            elif level < previous_level or (level == previous_level and not previous_was_list):
                role = 'return_to_parent_level'
            else:
                role = 'same_group_or_first_child'
            previous_level = level
            next_level = levels[index + 1] if index + 1 < len(levels) else None
            keep_next = next_level is not None and next_level > level
        elif is_note:
            role, keep_next = 'note', False
        else:
            previous_was_list = False
            continue
        doc.set_paragraph_format(
            paragraph_index=index,
            line_spacing_percent=profile['note_line_percent' if is_note else 'body_line_percent'],
            spacing_before_pt=before[role], spacing_after_pt=profile['after_pt'],
            keep_with_next=keep_next,
        )
        changes.append({'paragraph': index, 'level': level, 'role': role, 'before_pt': before[role]})
        previous_was_list = level is not None
    with open(args.out, 'xb') as stream:
        doc.save_to_stream(stream)
    reread = HwpxDocument.open(args.out)
    if [p.text for p in reread.paragraphs] != original:
        raise ValueError('Text changed during paragraph spacing application.')
    print(json.dumps({'ok': True, 'paragraphs': changes}, ensure_ascii=True))


if __name__ == '__main__':
    main()

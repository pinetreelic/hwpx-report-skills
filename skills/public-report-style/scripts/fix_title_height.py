#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
# Modified 2026-10-15: portable report generation and distribution.
"""Size only the title box of a freshly generated document via python-hwpx API."""
import argparse
import json
from hwpx.document import HwpxDocument

TITLE_HEIGHT = 6803  # 24 mm; accommodates two 22 pt lines at 130% spacing.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('out')
    args = parser.parse_args()
    doc = HwpxDocument.open(args.source)
    tables = [t for p in doc.paragraphs for t in p.tables]
    if not tables:
        raise ValueError('Generated document has no title box.')
    table = tables[0]
    if (table.row_count, table.column_count) != (3, 1):
        raise ValueError('Unexpected title box layout; output was not written.')
    top, title, bottom = [table.cell(i, 0) for i in range(3)]
    if top.text.strip() or bottom.text.strip() or not title.text.strip():
        raise ValueError('Unexpected title box contents; output was not written.')
    if top.height != 382 or bottom.height != 382:
        raise ValueError('Title band geometry changed; review the generator before proceeding.')
    title.set_size(height=TITLE_HEIGHT)
    # Existing CENTER alignment and constant 141-HWPUNIT vertical margins are retained.
    with open(args.out, 'xb') as stream:
        doc.save_to_stream(stream)
    reread = HwpxDocument.open(args.out)
    result = [t for p in reread.paragraphs for t in p.tables][0]
    if result.cell(1, 0).height != TITLE_HEIGHT or result.cell(1, 0).text != title.text:
        raise ValueError('Title height/text did not survive save.')
    print(json.dumps({'title_cell_height_hu': TITLE_HEIGHT, 'title_cell_height_mm': 24}))


if __name__ == '__main__':
    main()

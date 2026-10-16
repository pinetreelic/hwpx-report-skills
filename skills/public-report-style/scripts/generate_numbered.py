#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
# Modified 2026-10-15: portable report generation and distribution.
"""Create a new numbered HWPX using the installed kordoc public API."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--preset', choices=['report', 'plan', 'official'], default='report')
    parser.add_argument('--kordoc-module', type=Path, help='Explicit installed index.js path')
    parser.add_argument('--heading-font', help='Title face; default HY헤드라인M, installed bold fallback when available')
    parser.add_argument('--hwpx-python', type=Path, help='Python interpreter with python-hwpx installed')
    args = parser.parse_args()
    node = shutil.which('node')
    cli = shutil.which('kordoc')
    runtime = Path(__file__).resolve().parent.parent / 'runtime'
    local_module = runtime / 'node/node_modules/kordoc/dist/index.js'
    module = args.kordoc_module or (local_module if local_module.is_file() else None) or (Path(cli).resolve().parent / 'index.js' if cli and os.name != 'nt' else None)
    if not node or not module or not module.is_file():
        parser.error('Installed node and kordoc index.js required; no packages were installed.')
    if args.source.suffix.lower() != '.md' or not args.source.is_file():
        parser.error('Source must be an existing Markdown file.')
    if args.out.suffix.lower() != '.hwpx' or args.out.exists():
        parser.error('Output must be a new .hwpx file; overwriting is not supported.')
    hwpx_cli = shutil.which('hwpx-kit')
    local_python = runtime / 'python' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    hwpx_python = args.hwpx_python or (local_python if local_python.is_file() else None) or (Path(hwpx_cli).resolve().parent / 'python' if hwpx_cli and os.name != 'nt' else Path(sys.executable))
    if not hwpx_python or not hwpx_python.is_file():
        parser.error('Run public-report-style/scripts/setup_runtime.py or use --hwpx-python.')
    heading_font = args.heading_font or 'HY헤드라인M'
    # A missing display face otherwise falls back to a thin regular face on macOS.
    font_list = shutil.which('fc-list')
    if not args.heading_font and font_list:
        installed = subprocess.run([font_list, ':', 'family', 'fullname'],
                                   capture_output=True, text=True, check=True).stdout
        if 'HY헤드라인M' not in installed and 'HY헤드라인 M' not in installed:
            if 'Malgun Gothic Bold' in installed:
                heading_font = 'Malgun Gothic Bold'
    js = r'''
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const [modulePath, source, out, preset, headingFont] = process.argv.slice(1);
const {markdownToHwpx, simulateWrap} = await import(pathToFileURL(modulePath).href);
const markdown = fs.readFileSync(source, 'utf8');
const title = markdown.match(/^#\s+(.+)$/m)?.[1] ?? '';
const titlePt = 22;
if (preset !== 'official' && (!title || simulateWrap(title, 47627, 47627, 2200, 100, 'keep').lines > 2)) {
  throw new Error('A title fitting within two lines is required; shorten the title or move details to a subtitle.');
}
const data = await markdownToHwpx(markdown, {
  gongmun: {preset, numbering: 'standard', h2Marker: 'none',
    fonts: {heading: headingFont}, sizes: {bodyTitle: titlePt},
    autoFit: false, suppressSingle: true}
});
fs.writeFileSync(out, Buffer.from(data), {flag: 'wx'});
console.log(JSON.stringify({title_pt: titlePt}));
'''
    with tempfile.TemporaryDirectory(prefix='numbered-title-') as temporary:
        generated = Path(temporary) / 'generated.hwpx'
        subprocess.run([node, '--input-type=module', '-e', js, str(module.resolve()),
                        str(args.source.resolve()), str(generated), args.preset, heading_font],
                       check=True, capture_output=True, text=True)
        if args.preset != 'official':
            title_sized = Path(temporary) / 'title-sized.hwpx'
            subprocess.run([str(hwpx_python), str(Path(__file__).with_name('fix_title_height.py')),
                            str(generated), str(title_sized)], check=True, capture_output=True, text=True)
            generated = title_sized
        subprocess.run([str(hwpx_python), str(Path(__file__).with_name('apply_paragraph_spacing.py')),
                        str(generated), str(args.out.resolve())], check=True, capture_output=True, text=True)
    print(json.dumps({'ok': True, 'out': str(args.out.resolve()), 'numbering': 'standard',
                      'title_font': heading_font, 'title_pt': 22,
                      'title_cell_height_mm': 24 if args.preset != 'official' else None,
                      'layout': 'body 160%; before spacing 3/9/15pt by group boundary'}, ensure_ascii=True))


if __name__ == '__main__':
    main()

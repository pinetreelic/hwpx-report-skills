#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
"""Exercise an installed copy using its isolated dependencies, not global tools."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, default=Path('.test-skills'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    skills = args.skills_dir.resolve()
    runtime = skills / 'public-report-style/runtime'
    python = runtime / 'python' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    env = dict(os.environ)
    env['PATH'] = str(runtime / 'node/node_modules/.bin') + os.pathsep + str(python.parent) + os.pathsep + env['PATH']
    output = root / '.test-output'
    output.mkdir(exist_ok=True)
    subprocess.run([sys.executable, str(skills / 'public-report-style/scripts/setup_runtime.py'), '--check'], check=True)
    for name in ('one-line', 'two-lines'):
        hwpx = output / (name + '.hwpx')
        svg = output / (name + '.svg')
        if hwpx.exists():
            hwpx.unlink()
        subprocess.run([sys.executable, str(skills / 'public-report-style/scripts/generate_numbered.py'),
                        str(root / 'tests' / 'fixtures' / (name + '.md')), '--out', str(hwpx)], env=env, check=True)
        result = subprocess.check_output([str(python), '-m', 'hwpx_kit.cli', 'validate', str(hwpx), '--json'], env=env, text=True)
        assert json.loads(result)['data']['valid']
        subprocess.run([str(python), '-c',
            'from hwpx.document import HwpxDocument; import sys; '
            'd=HwpxDocument.open(sys.argv[1]); '
            't=[t for p in d.paragraphs for t in p.tables][0]; '
            'assert t.cell(1,0).height==6803; '
            'assert any(p.text.startswith("2. 추진") for p in d.paragraphs)',
            str(hwpx)], env=env, check=True)
        subprocess.run([str(python), '-m', 'hwpx_kit.cli', 'render', str(hwpx), '--engine', 'kordoc',
                        '--out', str(svg), '--json'], env=env, check=True)
        document = ET.parse(svg)
        rows = [(float(e.get('y')), ''.join(e.itertext()))
                for e in document.findall('.//{http://www.w3.org/2000/svg}text')]
        for prefix, distance in [('가. 현황', 27), ('2. 추진', 39), ('나. 실행', 33)]:
            index = next(i for i, row in enumerate(rows) if row[1].startswith(prefix))
            assert abs(rows[index][0] - rows[index - 1][0] - distance) < 0.1, (name, prefix, rows)
        print(name + ': structure, title height and rendered 3/9/15pt spacing passed.')


    # Both styles must preserve the same source content and sectioned numbering must restart.
    import zipfile
    source = root / 'examples' / '문서내용_스타일비교.md'
    expected = [line[2:] for line in source.read_text(encoding='utf-8').splitlines() if line.startswith('- ')]
    for style in ('basic-report', 'sectioned'):
        hwpx = output / (style + '.hwpx')
        if hwpx.exists(): hwpx.unlink()
        subprocess.run([sys.executable, str(skills / 'public-report-style/scripts/generate_numbered.py'),
                        str(source), '--style', style, '--out', str(hwpx)], env=env, check=True)
        validated = json.loads(subprocess.check_output([str(python), '-m', 'hwpx_kit.cli', 'validate', str(hwpx), '--json'],env=env,text=True))
        assert validated['data']['valid']
        with zipfile.ZipFile(hwpx) as z:
            section = ET.fromstring(z.read('Contents/section0.xml'))
            ns = {'p':'http://www.hancom.co.kr/hwpml/2011/paragraph', 'h':'http://www.hancom.co.kr/hwpml/2011/head'}
            text = '\n'.join(e.text or '' for e in section.findall('.//p:t',ns))
            for sentence in expected: assert sentence in text, (style,sentence)
            if style == 'sectioned':
                assert 'Ⅰ. 추진 개요' in text and 'Ⅱ. 실행 계획' in text
                assert '1. 준비 단계' in text and '2. 실행 및 점검' in text
                assert text.count('○ ') == len(expected)
                assert len(section.findall('.//p:tbl',ns)) == 3
                header=ET.fromstring(z.read('Contents/header.xml'))
                assert any(e.get('type')=='DOUBLE_SLIM' for e in header.findall('.//h:topBorder',ns))
        subprocess.run([str(python), '-m', 'hwpx_kit.cli', 'render', str(hwpx), '--engine', 'kordoc',
                        '--out', str(output/(style+'.svg')), '--json'],env=env,check=True)
    print('Both designs preserve all content; section numbering, bullets, boxes and render passed.')


if __name__ == '__main__':
    main()

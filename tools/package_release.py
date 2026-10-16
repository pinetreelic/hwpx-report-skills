#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
"""Refresh the manifest and build a redistributable ZIP from an explicit allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = '0.1.2'
FILES = {'README.md', 'LICENSE', 'NOTICE', 'CHANGES.md', 'VERIFICATION.md',
         'install.py', 'requirements-runtime.txt', 'runtime-versions.json', '.gitignore', '.gitattributes'}
DIRECTORIES = {'skills', 'examples', 'tests', 'tools', '.github'}


def included():
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file()
            and (p.relative_to(ROOT).parts[0] in DIRECTORIES or p.relative_to(ROOT).as_posix() in FILES)
            and not any(part in {'runtime', '__pycache__', '.DS_Store'} for part in p.relative_to(ROOT).parts)
            and p.suffix != '.pyc']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = included()
    manifest = {'version': VERSION, 'sha256': {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    path = ROOT / 'MANIFEST.json'
    if args.check:
        assert json.loads(path.read_text(encoding='utf-8')) == manifest, 'Manifest is stale; rebuild the release.'
        print('Package manifest verified.')
        return
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    output = ROOT / '.release'
    output.mkdir(exist_ok=True)
    name = 'hwpx-report-skills-' + VERSION
    archive = output / (name + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in files + [path]:
            z.write(p, name + '/' + p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    Path(str(archive) + '.sha256').write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n', encoding='utf-8')
    print(archive)


if __name__ == '__main__':
    main()

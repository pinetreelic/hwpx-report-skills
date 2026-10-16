#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
"""Install the four skill folders without overwriting existing skills."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

NAMES = ('public-report-style', 'hwpx-create', 'hwpx-edit', 'hwpx-to-office')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, default=Path.home() / '.agents' / 'skills')
    parser.add_argument('--setup-runtime', action='store_true', help='Download pinned Python/npm runtime packages')
    args = parser.parse_args()
    if args.setup_runtime and sys.version_info < (3, 10):
        parser.error('Python 3.10+ required for runtime setup; no skills were copied.')
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))
    for relative, digest in manifest['sha256'].items():
        path = root / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            parser.error('Package integrity check failed: ' + relative)
    destination = args.dest.expanduser().resolve()
    collisions = [str(destination / name) for name in NAMES if (destination / name).exists()]
    if collisions:
        parser.error('Existing skills will not be overwritten. Back them up/move them first: ' + ', '.join(collisions))
    for name in NAMES:
        if not (root / 'skills' / name / 'SKILL.md').is_file():
            parser.error('Missing skill: ' + name)
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for name in NAMES:
            target = destination / name
            shutil.copytree(root / 'skills' / name, target)
            created.append(target)
    except Exception:
        for path in reversed(created):
            shutil.rmtree(path)
        raise
    print('Installed four skills into ' + str(destination))
    if args.setup_runtime:
        subprocess.run([sys.executable, str(destination / 'public-report-style' / 'scripts' / 'setup_runtime.py')], check=True)
    print('Use $hwpx-create or $hwpx-edit in your next Codex turn. Restart Codex if the skills do not appear.')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# Copyright 2026 Soonlee. SPDX-License-Identifier: Apache-2.0
"""Install isolated pinned dependencies; --check performs a read-only health check."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10+ required.')
    root = Path(__file__).resolve().parent.parent
    runtime = root / 'runtime'
    windows = os.name == 'nt'
    python = runtime / 'python' / ('Scripts/python.exe' if windows else 'bin/python')
    module = runtime / 'node' / 'node_modules' / 'kordoc' / 'dist' / 'index.js'
    node, npm = shutil.which('node'), shutil.which('npm')
    if not node or (not npm and not args.check):
        parser.error('Install Node.js 18+ (including npm) first.')
    major = int(subprocess.check_output([node, '-p', 'process.versions.node.split(".")[0]'], text=True).strip())
    if major < 18:
        parser.error('Node.js 18+ required.')
    versions = json.loads((root / 'runtime-versions.json').read_text(encoding='utf-8'))
    if not args.check:
        if not python.exists():
            venv.EnvBuilder(with_pip=True).create(runtime / 'python')
        subprocess.run([str(python), '-m', 'pip', 'install',
                        'hwpx-kit-cli==' + versions['hwpx-kit-cli'],
                        'python-hwpx==' + versions['python-hwpx']], check=True)
        subprocess.run([npm, 'install', '--prefix', str(runtime / 'node'),
                        '--no-audit', '--no-fund', 'kordoc@' + versions['kordoc']], check=True)
    if not python.is_file() or not module.is_file():
        parser.error('Runtime missing; run this script without --check to install it.')
    subprocess.run([str(python), '-c',
        'from importlib.metadata import version; import sys; '
        'assert version("hwpx-kit-cli")==sys.argv[1]; '
        'assert version("python-hwpx")==sys.argv[2]; '
        'from hwpx.document import HwpxDocument; '
        'assert hasattr(HwpxDocument,"set_paragraph_format")',
        versions['hwpx-kit-cli'], versions['python-hwpx']], check=True)
    subprocess.run([node, '--input-type=module', '-e',
        'import {pathToFileURL} from "node:url"; '
        'const m=await import(pathToFileURL(process.argv[1]).href); '
        'if(m.VERSION!==process.argv[2] || !m.markdownToHwpx)process.exit(1)',
        str(module), versions['kordoc']], check=True)
    print(json.dumps({'ok': True, 'runtime': str(runtime), 'versions': versions}))


if __name__ == '__main__':
    main()

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cibuildwheel>=4.2.0",
# ]
# ///

import json
import os
import re
import shutil
import subprocess


cibuildwheel = shutil.which('cibuildwheel')
if not cibuildwheel:
    raise RuntimeError

output = subprocess.check_output(  # noqa: S603
    [
        cibuildwheel,
        '--platform',
        'linux',
        '--archs',
        'x86_64',
        '--print-build-identifiers',
    ],
    shell=False,
    text=True,
    cwd='targets/ptfkit-py',
)

version_re = re.compile(r'cp(\d)(\d+)(t?)-')
versions = set()

for identifier in output.split():
    if match := version_re.match(identifier):
        major, minor, free_threaded = match.groups()
        version = f'{major}.{minor}'
        if free_threaded:
            version += free_threaded
        versions.add(version)

version_matrix = json.dumps({'python-version': sorted(versions)})
with open(os.environ['GITHUB_OUTPUT'], 'a') as f:  # noqa: PTH123
    f.write(f'matrix={version_matrix}\n')

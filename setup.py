from __future__ import annotations

import os

import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, setup


define_macros: list[tuple[str, str | None]] = []
compiler_directives = {}
if os.getenv('CYTHON_TRACING') in {'1', 't', 'true'}:
    define_macros.append(('CYTHON_TRACE', '1'))
    compiler_directives['linetrace'] = True


extensions = [
    Extension(
        name='ptfkit._core',
        sources=['src/ptfkit/_core.py'],
        include_dirs=[np.get_include()],
        define_macros=define_macros,
    ),
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
    ),
)

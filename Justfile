default:

test:
	rm src/ptfkit/_core.c
	CYTHON_TRACING=1 uv sync --reinstall-package=ptfkit --no-build-isolation
	uv run --no-sync pytest

docs:
	uv run --group docs mkdocs build

format:
	uv run ruff format
test: test-src lint
test-src:
	uv run pytest src/tests

lint: lint-uv lint-mypy
lint-uv:
	uv run ruff check
	uv run ruff format --check

lint-mypy:
	uv run mypy src/

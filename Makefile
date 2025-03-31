format:
	uv run ruff format
test: test-src lint
test-src:
	uv run pytest src/tests

lint: lint-uv lint-type
lint-uv:
	uv run ruff check
	uv run ruff format --check

lint-type:
	uv run pyright src/

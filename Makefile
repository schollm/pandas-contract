.PHONY: format test test-src lint lint-uv lint-type docs clean-docs

format:
	uv run ruff format
test: test-src lint
test-src:
	uv run pytest src/

lint: lint-uv lint-type
lint-uv:
	uv run ruff check
	uv run ruff format --check

lint-type:
	uv run pyrefly check src/

docs:  ## Generate docs
	uv run --group docs "$(MAKE)" -C docs html

clean-docs:
	rm -rf docs/_out

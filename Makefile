.PHONY: help format test test-src lint lint-uv lint-type lint-type-mypy docs clean-docs

help:  ## Show this help message
	@echo "Available make targets:"
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

format:  ## Format source code
	uv run ruff format
test: test-src lint  ## Run all tests and linters
test-src:  ## Run tests on source code
	uv run pytest src/

lint: lint-uv lint-type lint-type-mypy  ## Run all linters
lint-uv:  ## Run ruff linter
	uv run ruff check
	uv run ruff format --check

lint-type:  ## Run type checker
	uv run pyrefly check src/

lint-type-mypy:  ## Run mypy type checker
	uv run mypy src/

docs:  ## Generate docs
	uv run --group docs "$(MAKE)" -C docs html

clean-docs:  ## Clean generated docs
	rm -rf docs/_out

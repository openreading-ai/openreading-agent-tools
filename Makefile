.PHONY: sync verify lint test repo-check productspec-validate audit hooks runtime-check feasibility-lock-check

sync:
	npm ci --ignore-scripts --no-audit --no-fund
	uv sync --frozen --project runtime --all-groups

verify: runtime-check feasibility-lock-check
	npm run verify

lint:
	npm run lint

test:
	npm test

repo-check:
	npm run check:repo

productspec-validate:
	npm run check:specs

# Advisory lookups require the network and stay outside the offline gate.
# The Docling candidate lock is audited so a rejected dependency cannot return unnoticed.
audit:
	npm audit --audit-level=high
	uv audit --frozen --preview-features audit-command --project runtime/feasibility

hooks:
	git config core.hooksPath .githooks

runtime-check:
	uv run --frozen --project runtime --all-groups ruff check --config runtime/pyproject.toml runtime measurement scripts/package_smoke.py scripts/docling_feasibility.py tests/runtime
	uv run --frozen --project runtime --all-groups ruff format --check --config runtime/pyproject.toml runtime measurement scripts/package_smoke.py scripts/docling_feasibility.py tests/runtime
	uv run --frozen --project runtime --all-groups coverage run --rcfile=runtime/pyproject.toml -m unittest discover -s tests/runtime
	uv run --frozen --project runtime --all-groups coverage report --rcfile=runtime/pyproject.toml
	uv run --frozen --project runtime --all-groups coverage json --rcfile=runtime/pyproject.toml -o .coverage.json
	uv run --frozen --project runtime --all-groups python -m runtime.coverage_gate .coverage.json

feasibility-lock-check:
	uv lock --check --offline --project runtime/feasibility

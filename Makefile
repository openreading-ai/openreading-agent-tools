.PHONY: sync verify lint test repo-check productspec-validate audit hooks runtime-check feasibility-lock-check p0-lock-check

sync:
	npm ci --ignore-scripts --no-audit --no-fund
	uv sync --frozen --project runtime --all-groups
	uv sync --frozen --project runtime/testing --all-groups
	uv sync --frozen --project runtime/server_client --all-groups

verify: runtime-check feasibility-lock-check p0-lock-check server-client-lock-check
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
# Audit the shipped connector and historical candidates so rejected dependencies cannot return.
audit:
	npm audit --audit-level=high
	uv audit --frozen --preview-features audit-command --project runtime/feasibility
	uv audit --frozen --preview-features audit-command --project runtime/p0
	uv audit --frozen --preview-features audit-command --project runtime/server_client

hooks:
	git config core.hooksPath .githooks

runtime-check:
	uv run --frozen --project runtime --all-groups ruff check --config runtime/pyproject.toml runtime measurement scripts/package_smoke.py scripts/docling_feasibility.py scripts/retrieval_check.py scripts/retrieval_restart.py scripts/probe_environment.py scripts/host_probe.py scripts/docling_package_smoke.py tests/runtime tests/server
	uv run --frozen --project runtime --all-groups ruff format --check --config runtime/pyproject.toml runtime measurement scripts/package_smoke.py scripts/docling_feasibility.py scripts/retrieval_check.py scripts/retrieval_restart.py scripts/probe_environment.py scripts/host_probe.py scripts/docling_package_smoke.py tests/runtime tests/server
	uv run --frozen --project runtime --all-groups coverage run --rcfile=runtime/pyproject.toml -m unittest discover -s tests/runtime
	uv run --frozen --project runtime/testing --all-groups coverage run --append --rcfile=runtime/pyproject.toml -m unittest discover -s tests/server
	uv run --frozen --project runtime --all-groups coverage report --rcfile=runtime/pyproject.toml
	uv run --frozen --project runtime --all-groups coverage json --rcfile=runtime/pyproject.toml -o coverage-report.json
	uv run --frozen --project runtime --all-groups python -m runtime.coverage_gate coverage-report.json

feasibility-lock-check:
	uv lock --check --offline --project runtime/feasibility

p0-lock-check:
	uv lock --check --offline --project runtime/p0

server-client-lock-check:
	uv lock --check --offline --project runtime/server_client

.PHONY: sync verify lint test repo-check productspec-validate audit hooks

sync:
	npm ci --ignore-scripts --no-audit --no-fund

verify:
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
audit:
	npm audit --audit-level=high

hooks:
	git config core.hooksPath .githooks

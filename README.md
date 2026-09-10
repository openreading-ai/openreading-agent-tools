<img src="assets/brand/icon.svg" alt="OpenReading" width="64" height="64" />

# OpenReading Agent Tools

[![Repository checks](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml)
[![Stage](https://img.shields.io/badge/stage-design-blue)](product/specs/local-document-proof.product-spec.md)
[![ProductSpec](https://img.shields.io/badge/ProductSpec-0.1-blue)](https://github.com/gokulrajaram/ProductSpec)
[![Source license](https://img.shields.io/badge/source-Apache--2.0-blue)](LICENSE)

OpenReading Agent Tools will connect local document processing to your AI assistant.
The first proposed proof lets you install a local runtime, ask about a document, and inspect the pages supporting the answer.

**Status: design and repository checks only.** No installable plugin, packaged runtime, or measured token savings ship from this repository yet.
The source license above does not describe the licenses of future bundled dependencies.

## The first proof

The proposal starts with Claude Desktop on macOS with Apple Silicon.
You install a bundle, choose a document directory, and ask about one PDF with extractable text.
OpenReading keeps the extracted document locally and returns selected passages with physical page references.
Claude Code and Codex use the same proposed runtime through separate packaging and compatibility tests.

A separate experiment tests whether selective retrieval reduces Claude token consumption while preserving answer quality.
Local parsing alone does not establish that claim.
Excerpts returned to a cloud assistant enter that assistant's context.

## Repository boundaries

| Repository | Responsibility |
| --- | --- |
| [openreading-core](https://github.com/openreading-ai/openreading-core) | Parsing, adapters, schemas, provenance, document artifacts, and MCP behavior. |
| This repository | Client packages, workflow skills, runtime assembly, launchers, installation tests, and client measurement tooling. |
| Private company repository | Private research, customer documents, benchmark ground truth, trial transcripts, and business decisions. |

MCP means Model Context Protocol, the interface through which an assistant calls local tools.
This repository consumes a pinned core build.
Core never requires this checkout or a private company package.

## Read and review

| Need | Read |
| --- | --- |
| Goals, scope, user experience, and pass/fail criteria | [Product specification](product/specs/local-document-proof.product-spec.md) |
| Runtime, client packaging, tool contracts, and provenance | [Engineering design](design/local-document-proof.md) |
| Fair baselines, usage accounting, and claim limits | [Token evaluation design](design/token-evaluation.md) |
| Ordered tasks, exact files, tests, and handoff rules | [Implementation plan](design/implementation-plan.md) |
| Agent instructions and repository ownership | [AGENTS.md](AGENTS.md) |
| Contribution workflow and checks | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Vulnerability reporting | [SECURITY.md](SECURITY.md) |

## Verify this repository

Contributors need Node.js 24 or newer and npm.
These are documentation tooling requirements, separate from the proposed end-user installation experience.

~~~sh
make sync
make verify
make audit    # Requires internet access.
~~~

The gate checks Markdown, repository documentation policy, local link targets, JSON/YAML syntax, and ProductSpec validity.
Its regression tests exercise those repository checks.
After dependency installation, verification needs no network, model credentials, backend server, or sibling checkout.

GitHub runs the same gate and a separate dependency advisory lookup.
There is no runtime coverage badge because no runtime exists here yet.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
Open a branch and submit a pull request.
Human maintainers review and merge changes.

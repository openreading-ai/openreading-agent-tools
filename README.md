<img src="assets/brand/icon.svg" alt="OpenReading" width="64" height="64" />

# OpenReading Agent Tools

[![Repository checks](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml)
[![Stage](https://img.shields.io/badge/stage-local_preview-blue)](product/specs/local-document-proof.product-spec.md)
[![ProductSpec](https://img.shields.io/badge/ProductSpec-0.1-blue)](https://github.com/gokulrajaram/ProductSpec)
[![Source license](https://img.shields.io/badge/source-Apache--2.0-blue)](LICENSE)

OpenReading Agent Tools packages local document processing for your AI assistant.
The prototype retains extracted evidence and returns selected passages with physical PDF page references.

**Status: revision 2 design ready for review; engine migration pending.**
The current code is the superseded revision 1 PyMuPDF prototype.
The target bundle uses Docling, local ONNX layout, PDFium, and setup-enabled Tesseract.
Existing build and test evidence does not establish that new engine profile.
No public binary or measured token-savings claim is released.
The source license above does not describe bundled dependency licenses.

## The first proof

The first profile targets macOS on Apple Silicon.
The revised proof targets a bundled local layout model and optional OCR, with resource limits selected from measured host timing.
OpenReading keeps the extracted document locally and returns selected passages with physical page references.
Claude Desktop, Claude Code, and Codex packages contain the same frozen runtime.
See the [runtime evidence table](runtime/README.md) for tested behavior and remaining host checks.

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
| Build, package, verify, and inspect implementation evidence | [Runtime guide](runtime/README.md) |
| Client setup | [Claude Desktop](clients/claude-desktop/README.md), [Claude Code](clients/claude-code/README.md), [Codex](clients/codex/README.md) |
| Prepare a frozen experiment and regenerate reports | [Measurement guide](measurement/README.md) |
| Engine migration, timing, configuration, and distribution contract | [Revision 2 design](design/local-document-proof.md) |
| Claude review resolutions | [Finding dispositions](design/review-disposition.md) |
| Fair baselines, usage accounting, and claim limits | [Token evaluation design](design/token-evaluation.md) |
| Ordered tasks, exact files, tests, and handoff rules | [Implementation plan](design/implementation-plan.md) |
| Agent instructions and repository ownership | [AGENTS.md](AGENTS.md) |
| Contribution workflow and checks | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Vulnerability reporting | [SECURITY.md](SECURITY.md) |

## Verify this repository

Contributors need Node.js 24 or newer, npm, and uv 0.11.26.
The lockfile selects Python 3.11.15; uv can install that interpreter for contributors.
The frozen end-user runtime includes its interpreter.

~~~sh
make sync
make verify
make audit    # Requires internet access.
~~~

The gate checks Python formatting, runtime integrity, packaging, synthetic dataset generation, usage accounting, and report decisions.
Python branch coverage and Node line, branch, and function coverage each enforce an 80% floor.
Markdown, repository policy, local links, JSON/YAML, and ProductSpec checks also run.
After dependency installation, verification needs no network, model credentials, backend server, or sibling checkout.

GitHub runs the same gate and a separate dependency advisory lookup.
Paid model trials and real host installation remain separate from this offline gate.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
Open a branch and submit a pull request.
Human maintainers review and merge changes.

The [Docling feasibility harness](runtime/feasibility/README.md) provides the revision 2 developer engine candidate.
It does not replace the historical client bundle or establish token savings.

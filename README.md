<img src="assets/brand/icon.svg" alt="OpenReading" width="64" height="64" />

# OpenReading Agent Tools

[![Repository checks](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml)
[![Stage](https://img.shields.io/badge/stage-local_preview-blue)](product/specs/local-document-proof.product-spec.md)
[![ProductSpec](https://img.shields.io/badge/ProductSpec-0.1-blue)](https://github.com/gokulrajaram/ProductSpec)
[![Source license](https://img.shields.io/badge/source-Apache--2.0-blue)](LICENSE)

OpenReading Agent Tools packages local document processing for your AI assistant.
The prototype retains extracted evidence and returns selected passages with physical PDF page references.

**Status: revision 7 scope; shared configuration and an unsigned Docling runtime are implemented; native client packaging remains pending.**
The Docling corpus, retrieval/restart checks, citation checker and historical offline accounting are documented in [measurement](measurement/README.md).
Historical client packages remain the superseded revision 1 PyMuPDF prototype.
The [P0 developer build](runtime/p0/README.md) bundles Docling, local ONNX layout, PDFium, and setup-enabled Tesseract.
The [assistant design](design/assistant-clients.md) keeps Claude Desktop and a conditional, named ChatGPT conversation mode behind separate compatibility checks.
Existing developer checks do not establish native installation or model invocation.
No public binary or measured token-savings claim is released.
The source license above does not describe bundled dependency licenses.

## The first proof

The first profile targets macOS on Apple Silicon.
The revised proof targets a bundled local layout model and optional OCR, with resource limits selected from measured host timing.
OpenReading keeps the extracted document locally and returns selected passages with physical page references.
The proposed Claude Desktop, ChatGPT desktop, Claude Code, and Codex integrations use the same frozen runtime.
The [client matrix](clients/README.md) distinguishes documented routes from tested behavior.
See the [runtime evidence table](runtime/README.md) for tested behavior and remaining host checks.

Provider API studies and SDK execution are disabled. Testing uses the owner's existing Desktop apps.
The next proof checks large-document access and reliable citations; token savings remain unmeasured.
An API result does not establish a native chat app's token usage or subscription savings.
Local parsing alone does not establish that claim.
Excerpts returned to a cloud assistant enter that assistant's context.

> **OpenReading Managed: Coming soon**
>
> Document processing on OpenReading's servers, without managing local compute.
> Planned after the public OSS launch.

This is a static preview of future intent. It contains no service connection or signup flow.
Launch v1 remains free, local, and account-free, with the full implemented MCP catalog of its pinned core.
The candidate currently exposes import, search, and read. Broader MCP operations are not claimed before core implements them.
The slim Docling bundle does not configure other local backends; the [independent core guide](clients/full-core/README.md) explains the separate installation and current MCP profile limits.
The [OSS launch design](design/oss-launch.md) separates public v1 from internal v2 profile/settings names and later managed v2.

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
| Client compatibility and setup | [Client matrix](clients/README.md), [ChatGPT desktop](clients/chatgpt/README.md), [Claude Desktop](clients/claude-desktop/README.md), [Claude Code](clients/claude-code/README.md), [Codex](clients/codex/README.md) |
| Verify citations and replay historical offline reports | [Measurement guide](measurement/README.md) |
| Engine migration, timing, configuration, and distribution contract | [Docling engine design](design/local-document-proof.md) |
| Shared configuration and assistant boundaries | [Assistant integration design](design/assistant-clients.md) |
| Native mode, setup, timeout, isolation, and frozen-build experiments | [Probe plan](design/native-probes.md) |
| Revision 3 design review decisions | [Review adjudication](design/revision3-review.md) |
| Claude review resolutions | [Finding dispositions](design/review-disposition.md) |
| Desktop document-access comparisons and token-claim limits | [Token evaluation design](design/token-evaluation.md) |
| OSS launch, full MCP catalog parity, and static Coming soon scope | [OSS launch design](design/oss-launch.md) |
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
Python line and branch coverage and Node line, branch, and function coverage each enforce a 95% floor.
Python coverage includes runtime, measurement, and all proof scripts.
Markdown, repository policy, local links, JSON/YAML, and ProductSpec checks also run.
After dependency installation, verification needs no network, model credentials, backend server, or sibling checkout.

GitHub runs the same gate and a separate dependency advisory lookup.
Real Desktop installation checks remain separate from this offline gate. Provider API trials are prohibited.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
Open a branch and submit a pull request.
Human maintainers review and merge changes.

The [Docling feasibility harness](runtime/feasibility/README.md) provides the revision 2 developer engine candidate.
It does not replace the historical client bundle or establish token savings.

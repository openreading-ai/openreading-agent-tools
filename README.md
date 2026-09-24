<img src="assets/brand/icon.svg" alt="OpenReading" width="64" height="64" />

# OpenReading Agent Tools

[![Repository checks](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/openreading-ai/openreading-agent-tools/actions/workflows/ci.yml)
[![Source license](https://img.shields.io/badge/source-Apache--2.0-blue)](LICENSE)

Connect your assistant to an [OpenReading Core](https://github.com/openreading-ai/openreading-core) server you run separately.
Agent Tools handles native file selection, upload, retained results and evidence retrieval. Core handles document processing.

**Apple Silicon macOS preview only. Intel Mac, Windows and Linux binaries are pending.**
Alpha.22 distributes the server-only connector through GitHub-backed marketplaces. It is unsigned and not a public release.
Native acceptance, clean-machine checks, licensing review, signing and notarization remain release gates.

## What you install

| Form | Installation | Guide |
| --- | --- | --- |
| Claude Desktop / Cowork | Add the GitHub marketplace in the app; install openreading-cowork | [Claude Desktop](clients/claude-desktop/README.md) |
| Claude Code | Add the GitHub marketplace with the CLI; install openreading | [Claude Code](clients/claude-code/README.md) |
| ChatGPT Work, personal account | Register GitHub through Codex CLI; install OpenReading for ChatGPT in the app | [ChatGPT Work](clients/chatgpt/README.md) |
| Local Codex | Add the GitHub marketplace with the CLI; install openreading | [Codex](clients/codex/README.md) |

No installation route requires a downloaded ZIP, extracted folder, manual clone or copied binary.
Each host fetches and caches its complete package. Desktop visibility and native workflows require their own acceptance checks.
During PR review, code clients select `fix/github-marketplaces`; the client guides show the exact commands.
Desktop repository import from main becomes current after the owner merges that PR.

All four forms embed the same small connector worker, its Python interpreter and client dependencies.
They include two skills, nine document tools and one Settings opener.
The Core client-only package supplies canonical schemas, retention, job control, search and read.
There is no parser, OCR executable, model, backend catalog, Core server, runtime download or server manager in these packages.
Historical Docling and PyMuPDF builders are not the current release path.

## Set up processing

An operator [installs and starts Core separately](clients/full-core/README.md#run-core-for-the-connector).
Core owns backend installation, provider credentials and [commented openreading.yaml examples](https://github.com/openreading-ai/openreading-core/tree/main/examples/configs).
Configuration chooses a backend or strategy on that server. The plugin does not install or configure one.

Open the installed plugin's `openreading-settings` skill. Save and test the Core URL, then restart your client connection.
Loopback permits HTTP. Remote destinations require verified HTTPS.
This connector sends no credentials. A server requiring client authentication is not supported by this preview.
Do not expose an unauthenticated Core server to an untrusted network.

Use `openreading` to select files or a folder snapshot. Selection creates a queue and does not upload it.
Choose Process to send the selected bytes, or Add more to extend the queue.
The server can use external providers according to its own configuration. Requested results enter the assistant's context.
A failed submission never switches to a local parser or silently resubmits uncertain work.

Settings and retained results survive plugin replacement and removal.
The default data folder is `~/.openreading`, partitioned by client. Storage settings can select another location.
Cancel unwanted background jobs before uninstalling.

## Required compatibility matrix

ProductSpec revision 29 requires independent GitHub installation and functional acceptance for these four server-backed surfaces.
Earlier alpha.19/20/21 results are historical evidence, not acceptance of alpha.22.

| Client | Alpha.22 native acceptance |
| --- | --- |
| Claude Cowork | Pending exact-build owner walkthrough |
| Claude Code | Pending exact-build owner walkthrough |
| ChatGPT Work | Pending exact-build owner walkthrough |
| Local Codex | Pending exact-build owner walkthrough |

The [matrix checklist](clients/README.md#matrix-acceptance) separates protocol checks, native use and clean-machine evidence.
Ordinary Chat, web/mobile and cloud code sessions are outside this release scope.
Token savings remain unmeasured.

## Build and release

Use the [server-client build guide](runtime/server_client/README.md) for current packages.
It rejects parsing-engine content and records the Core commit, dependency lock, platform and worker hash.
The old `v0.2.0-rc.1` checkpoint uses bundled-parser packaging and is not this candidate.
Do not install that draft's binaries to test the thin connector.

Preview branches are review inputs, not a rolling release channel.
Maintainers merge Core first, repin Agent Tools to that merged commit, then merge Agent Tools.
A release tags the reviewed main commits and builds those exact versions. Moving main never silently replaces tagged binaries.
The repository remains private until the owner approves publication and the applicable distribution gates pass.
The source catalogs pin the complete packages on an immutable Git distribution commit.
Versioned distribution branches contain generated packages, not parser libraries or source-checkout prerequisites.
Git deduplicates the common runtime across client folders. Never merge a distribution branch into source main.
Historical archives and tags remain unchanged. ZIP packaging remains a maintainer diagnostic, not the installation guide.

> OpenReading Managed: Coming soon.
>
> Static future intent only. No hosted endpoint, signup flow or managed component ships here.

## Repository boundaries

| Repository | Responsibility |
| --- | --- |
| [OpenReading Core](https://github.com/openreading-ai/openreading-core) | Processing engine and canonical client contracts |
| Agent Tools | Native integration, workflow skills, connector packaging and host acceptance |
| Private company repository | Customer data, private evaluations and business material |

Core never depends on this repository. Agent Tools pins immutable Core source.
The source license does not replace bundled dependency notices.

## Read and verify

- [Client guides and historical evidence](clients/README.md)
- [Current build profile](runtime/server_client/README.md) and [historical runtime guide](runtime/README.md)
- [Product specification](product/specs/local-document-proof.product-spec.md) and [release acceptance design](design/oss-launch.md)
- [Measurement boundaries](measurement/README.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md) and [agent instructions](AGENTS.md)

Contributors need Node.js 24 or newer and uv 0.11.26. Locks select Python 3.11.15.
End users do not install a separate Python runtime.

~~~sh
make sync
make verify
make audit    # Separate network-dependent advisory checks.
~~~

Verification is offline after dependency installation. Python and Node coverage gates enforce a 95% floor.
Native installation and owner-operated assistant walkthroughs remain separate checks. Provider API trials are prohibited.

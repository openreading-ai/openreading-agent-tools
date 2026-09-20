# Assistant integration and compatibility design

**Status:** revision 12 native-client proposal. Shared version 2 configuration and the P0 diagnostic launcher are implemented; native adapters and signed distribution remain unbuilt.
**Intent:** [ProductSpec](../product/specs/local-document-proof.product-spec.md), AC-1, AC-2, AC-12, AC-15 through AC-17, and AC-23 through AC-25.
**Dependencies:** [engine design](local-document-proof.md), [evaluation design](token-evaluation.md), and [ordered implementation plan](implementation-plan.md).

## 1. One runtime, named client support

The first assistant distribution contains one selected local Docling profile.
“Docling slim” names the selected packaged profile built from the pinned `docling-slim` dependencies; it is not a second parser.
The exact engine contract remains `local-document-proof-v2`; ProductSpec revision 16 does not rename it.
Docling, PDFium, CPU ONNX layout inference, and automatically selected local Tesseract perform the document work.
The complete runtime includes Python, verified layout weights, OCR data, and required native libraries.
A small client plugin provisions that immutable runtime during first-use setup; document processing needs no further model downloads.
The [Cowork guide](../clients/claude-cowork/README.md) describes the implemented download packaging and its remaining native gates.
It excludes PyMuPDF and the prohibited dependencies listed in the engine design.

Revision 19 requires the [eight-cell compatibility matrix](../README.md#required-compatibility-matrix) on macOS Apple Silicon.
Desktop targets are Claude Cowork and ChatGPT Work; code targets are local Claude Code and Codex.
Every surface must support bundled Docling by default and an optional operator-run Core HTTP destination.
Host-specific manifests or archives may share one runtime, but each installation route requires independent evidence.
Users receive the runtime through installation without separate developer tools, server setup, or a GitHub checkout.
Existing Desktop Chat extension checks do not establish Cowork acceptance. Ordinary Chat and Grok remain outside this matrix.
The [matrix checklist](../clients/README.md#matrix-acceptance) governs acceptance; older target ordering below is historical where it conflicts.
The [client matrix](../clients/README.md#owner-operated-candidate-checks-september-16-2026) records owner-operated candidate workflows and separates them from clean-machine distribution acceptance.
Each supported entry names the application, version, execution mode, platform, and connection method.
A shared model provider does not make two applications equivalent.
For example, a successful OpenAI API trial proves nothing about a ChatGPT desktop installation.

The client starts the runtime over local standard input/output, abbreviated STDIO.
The runtime exposes every implemented MCP tool from the pinned core using unchanged core schemas.
The candidate catalog includes import, full retrieval, search, read, local selection, and background import start/status/cancel. The [OSS launch design](oss-launch.md) requires parity again for every pin update.
A host may qualify tool names, but it cannot require a different artifact or citation contract.
The shared evidence workflow describes tool purpose and uses identifiers returned by the tools.
Where a host cannot load a skill, its integration supplies the same concise workflow through a supported instruction channel.
Record that channel and its effective text; any instruction overhead belongs in the measurement.

A client adapter owns only setup translation, launch metadata, workflow delivery, and host checks.
It contains no parser, ranking algorithm, page mapping, account billing, or answer generation.
A measurement adapter observes one model execution surface; it is not part of the shipped document runtime.

## 2. Connection choices and evidence levels

The [client matrix](../clients/README.md) owns current documented routes and the limits of observed evidence.
Recheck official guidance before implementing each connection because host capabilities can change.
The first target is local execution in a named desktop mode, not every product carrying the same brand.
Web/mobile and cloud code execution remain outside this matrix. An optional operator-run processing destination may use localhost or remote HTTPS.
A connection restriction blocks that client criterion; it never authorizes uploading a local document elsewhere.

Use four separate evidence levels:

| Level | Required observation | Does not establish |
| --- | --- | --- |
| Documented | Official source identifies the connection path for the named surface. | Availability on this account or installed version. |
| Protocol | The selected core build initializes, lists tools, and returns valid results through an MCP client. | Native host configuration, launch, or invocation. |
| Native functional | The named application starts the candidate and completes the recorded synthetic workflow. | Clean-machine installation or token savings. |
| Distributed | The signed candidate passes installation and lifecycle checks on the recorded clean machine. | Measured savings or universal host support. |

Record an unsuccessful or unavailable check with its actual reason.
Do not turn missing evidence into a pass because a manifest validates or another host works.
A browser UI showing a tool name is not proof that a local process was launched.
Verify the executable identity, tool calls, and local evidence returned by the candidate.

The preferred connection is a native local MCP registration around the common runtime.
A separate server implementation per assistant would duplicate security and provenance decisions without improving extraction.
A remote bridge would add transport, authentication, and data-location obligations before proving the local product.
Neither alternative belongs in this first slice.

## 3. Configuration ownership and remaining host setup

The implemented setup object, precedence, private profiles and retention rules live in the [runtime guide](../runtime/README.md).
The [P0 candidate](../runtime/p0/README.md) supplies one verified Docling launcher for native integration work.
The current directory form and E5 substitutions are developer-only checks of that interface.
Public setup must not ask for a directory path, folder grant, or manual grant configuration.
The following A0 proposal replaces the public setup assumption; it does not relabel the installed candidate as compliant.
The `chatgpt` storage label still proves no ChatGPT conversation support; E1 remains required.

### Public file selection, proposed A0 contract

The thin helper and byte handoff are implemented in [the selection guide](../clients/claude-desktop/selection/README.md) and [runtime.selection](../runtime/selection.py).
The reference format, atomic publication, quotas, permissions and removal behavior now live beside that implementation.
The directory candidate stays developer-only; its historical records do not satisfy the public setup criteria.

No host-local attachment route has been established. The helper uses an explicit per-file picker and copyable reference instead.
The copyable reference is a developer mechanism, not the public interaction contract.
The [public document experience](public-document-experience.md) requires chat-driven selection and automatic reference return before native acceptance.
Fix or replace the inaccessible Tk controls before claiming non-developer setup acceptance.
Integrate the helper with a signed install location so users never manage its relative path to the runtime.
Retain explicit removal and shared-storage disclosures. The confirmed clear-all action recovers older intake copies; review its usability in the eventual public experience.
Repeat native setup, automatic OCR, cancellation and full conversation capture with the packaged route on a clean machine.
Do not change core intake schemas implicitly or infer local attachment access from an ordinary chat upload button.
If the selected host cannot support this local route, stop its public release rather than returning to directory configuration.

### Host-shared settings

Some OpenAI clients share one host MCP configuration, as the linked official documentation describes.
Registering a server there can make that server available to more than one local client.
The installation guide must disclose which applications share that registration and grant.
A client label or separate artifact directory cannot enforce application isolation against a shared host configuration.
If the user needs a narrower boundary, use a host-supported separate configuration scope and verify it before claiming isolation.
Do not silently register two entries with different grants and expose both as if each app saw only one.
The public disclosure says: "OpenReading reads files you select. Your assistant may have separate file and shell access."
Developer directory forms retain their explicit directory-grant disclosure.
Require local execution and exclude `experimental_environment = "remote"` from the supported registration.
Record executable identity, parent process, and a nonce-bearing local log before calling a route local.

### Independent full-core installations

Agent Tools bundles slim Docling only and does not add an alternative local backend or server manager.
Power users independently install full OpenReading and register a supported MCP profile through [the separate guide](../clients/full-core/README.md).
Current MCP profiles select PyMuPDF or local Docling; the broader CLI/Python/HTTP backend selection is not yet a general MCP interface.
That configuration belongs to core and the assistant, not to this package's settings or `.env`.
The core CLI and server keep their existing configuration contracts.
Managed product v2 is separate post-launch work; the OSS product v1 includes only the static Coming soon visual defined in [the launch design](oss-launch.md).
No dummy service, endpoint configuration, authentication or upload component ships as a future placeholder.

## 4. Preserve the CLI, Python API, and HTTP server

The dependency remains Agent Tools to a pinned core build.
No client manifest, provider SDK, assistant account, or host setting becomes a dependency of ordinary core operation.
Local Docling assets are required only when that optional profile is selected.
Adding a client requires no branch on its name inside core's router or adapters.
The MCP tool and artifact schemas remain the same for all clients.

Before accepting a future pin or launcher migration, use an isolated core installation without Agent Tools or its settings.
Check ordinary CLI help, Python imports, and the existing offline server behavior through core's own required checks.
Inspect package metadata to ensure assistant/provider dependencies have not entered core's default install requirements.
Run core's required `make verify` when core changes and tools' `make verify` when its consumers change.
Keep JSON and multipart HTTP behavior, backend selection, and existing password support under their existing tests.
A docs-only revision does not require rerunning every core engine test or altering its coverage policy.

## 5. Shared functional proof

Use the frozen synthetic corpus and exact same questions in each native client.
Public walkthroughs select only each synthetic document; keep ground truth outside the private intake root.
Developer protocol checks may continue using a synthetic directory grant, labeled separately from public setup acceptance.
Record source hashes, core commit, profile digest, application version, execution mode, model when invoked, and OS/architecture.
Use the frozen P0 candidate for native OpenReading checks; the existing launcher intentionally refuses source execution.
Tiny synthetic servers resolve host behavior separately in E1, E2, E3, and E5.
Neither synthetic probes nor a development-machine frozen build pass clean-machine installation.

| Case | Required result |
| --- | --- |
| Startup and discovery | The native application starts the intended candidate and lists the full implemented tool catalog of the pinned core (nine in candidate core `4f4351a`). |
| Factual question | Import, complete normalized retrieval or optional search, and exact read precede a correct answer with an exact quote and physical page. |
| Complete delivery | Register separate intact small, host-created file, and oversized local-export cases. Verify exact content hashes, OCR origins, warning details, actual access, approval prompts and citations. Keep fragment reconstruction as compatibility evidence. |
| Cross-page question | Each material claim resolves to evidence on its own supporting page. |
| Missing fact | The answer states the evidence limitation without turning empty search into proof of absence. |
| Document instructions | Retrieved instructions cause no unrelated file access or external upload. |
| Unselected source path or intake traversal | Selection/import refuses access and the assistant reports the actual refusal without a fallback upload. |
| Automatic OCR | Native text remains usable; image text is read locally, including mixed pages, without a mode choice. Existing off/on profiles remain developer controls. |
| Restart | The new MCP process reads the intact artifact with identical identifiers and exact passages. |
| Interruption | Record host cancel notification, deadline, and process-stop paths separately; each tested path leaves no owned extraction or OCR work and no successful artifact. |
| Invalid setup | Tools never register, and the guide's recovery steps correspond to the observed host error. |

Owner-operated checks use existing Desktop app accounts. Provider API calls and SDK substitutes are prohibited.
Use the frozen task IDs and rubrics from `measurement/corpus.json`; never edit fixtures to match an old example.
E1/N2 records each host's actual transcript export and tool-log location, format, and application version.
If host logs omit payloads, use an explicit diagnostic STDIO capture relay with the same invocation arguments and byte-preserving forwarding.
The relay records requests, responses, tool errors, and ordering outside the document grant and is excluded from performance measurements.
If complete capture is unavailable, citation evidence is incomplete and the native criterion remains pending.

The implemented [citation checker](../measurement/README.md#citation-evidence-checker) owns the captured-call and annotation contract.
Native adapters must supply its complete capture from the observed host log or an explicit diagnostic relay.
Reviewers must attest capture and citation-inventory completeness against the original transcript; normalized files cannot authenticate themselves.
Native acceptance still requires checked presentation, answer correctness, semantic support and instruction adherence.
A generated synthetic answer can test the protocol boundary but cannot satisfy those native criteria.

A host without a stop action records cancellation as `not_exposed`; it does not pass a cancel-notification check by quitting the app.
Test its available deadline and process-stop cleanup paths, disclose the limitation, and retain core cancellation tests independently.
Native host timing is a separate prerequisite for release limits.
Use the delay probe to measure foreground host behavior, without adopting a document page cap.
A short successful request does not establish the deadline for a 100-page OCR import.

## 6. Packaging and release order

Public OSS product v1 precedes managed product v2. Complete the catalog parity and static visual scope in [the launch design](oss-launch.md).
Internal profile/settings version 2 remains local and is not a managed release.

First prove the shared source protocol and native connection route; then implement common setup and host adapters.
Use bounded P0 frozen-build feasibility to test identity, relocation, one import, and startup.
It produces no distributed artifact, installer polish, or clean-machine claim.
M0 and provider API studies are retired. Packaging does not depend on token measurements.
Native functional checks use P0 after the owner authorizes host installation; they remain developer-machine evidence.

The packaged candidate includes the same engine bytes for every wrapper on the same platform.
It must preserve core Python sources and installed dependency metadata required for engine identity.
It must include verified `tessdata/configs/tsv`, language data, native libraries, layout weights, and complete notices.
A modified or incomplete inventory refuses startup; do not relax identity for frozen builds.

Claude Desktop uses its MCPB development wrapper. ChatGPT Work has a separate local plugin candidate around the same verified runtime.
The [ChatGPT client guide](../clients/chatgpt/README.md) documents the implemented assembler and its relative launch configuration.
This replaces the proposed helper app and manually pasted argument-free launcher; it adds no runtime or managed service.
The host owns plugin installation, approval policy and removal. Packaging never edits shared host settings.
The owner-operated native gate must disable the manual test connection before attributing calls to the installed plugin.
Record the installed cache location, worker identity, effective workflow and configuration changes on the named application version.
Test spaces and Unicode through actual host installation, not only direct subprocess launch.
Ordinary Chat remains separate from Work. Stop unsupported modes instead of substituting a remote worker or tunnel.
The engine design's signing, notarization, clean-machine and lifecycle gates apply to every distributed path.

Keep compatibility, installation, answer quality, and token results separate in release notes.
A working local integration may ship without a savings claim after its functional and distribution gates pass.
The owner reviews and merges; no stage authorizes automatic merge or publication.

## 7. Remaining native plugin and citation checks

The plugin assembler reuses the existing chat chooser and automatic local OCR without introducing another executable.
Native N2 checks must establish plugin discovery, installation, tool qualification, chooser handoff and access to local exports.
Repeat cancellation, reconnect and removal after installing through the host, keeping retained data behavior explicit.
A CLI cache install and direct frozen-worker test do not establish ChatGPT's native plugin UI behavior.
P1 still owns signing, notarization, minimal entitlements and clean-machine acceptance of the complete package.

The deterministic checker interface is implemented in [the measurement guide](../measurement/README.md#citation-evidence-checker).
Native capture adapters and reviewed host answers remain N2 tasks; a generated synthetic answer does not pass native acceptance.

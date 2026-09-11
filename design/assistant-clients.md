# Assistant integration and compatibility design

**Status:** revision 3 proposal. No new client launcher, package, or provider driver is implemented by this design.
**Intent:** [ProductSpec](../product/specs/local-document-proof.product-spec.md), AC-1, AC-2, AC-12, AC-15 through AC-17, and AC-23 through AC-25.
**Dependencies:** [engine design](local-document-proof.md), [evaluation design](token-evaluation.md), and [ordered implementation plan](implementation-plan.md).

## 1. One runtime, named client support

The first assistant distribution contains one selected local Docling profile.
“Docling slim” is this project's packaging description, not an upstream package name or a second parser.
The exact engine contract remains `local-document-proof-v2`; ProductSpec revision 3 does not rename it.
Docling, PDFium, CPU ONNX layout inference, and setup-enabled Tesseract perform the document work.
The bundle includes Python, verified layout weights, OCR data, and required native libraries.
It excludes PyMuPDF and the prohibited dependencies listed in the engine design.

Claude Desktop and ChatGPT desktop are the primary functional targets on macOS Apple Silicon.
Claude Code and Codex remain developer targets and potential measurement surfaces.
Each supported entry names the application, version, execution mode, platform, and connection method.
A shared model provider does not make two applications equivalent.
For example, a successful OpenAI API trial proves nothing about a ChatGPT desktop installation.

The client starts the runtime over local standard input/output, abbreviated STDIO.
The runtime invokes core's import, search, and read tools using unchanged core schemas.
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
ChatGPT web, mobile, secure tunnels, public endpoints, and remote workers remain outside this proof.
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

## 3. Configuration ownership and proposed interface

The same configuration semantics apply to every supported host.
The selected backend is fixed by the verified release profile, not an assistant setting.
The host owns the launch command, its argument array, enablement, and its own permissions.
OpenReading owns the explicit document grant, OCR choice, retained store, and verified engine configuration.
The cloud model account remains in the host; OpenReading requires no model-provider key to parse locally.

Extend the existing `runtime/configuration.py` and `runtime/entrypoint.py` rather than introducing a daemon or configuration service.
The proposed setup flags retain `--client`, `--configure`, and `--input-root`, and add `--ocr on|off`.
OCR defaults to off during a new setup, including when a host form omits its optional switch.
The client identifiers become `claude-desktop`, `chatgpt`, `claude-code`, and `codex`.
A client identifier chooses a settings location; it is not authentication of the calling application.
Do not claim that an executable receiving `--client chatgpt` proves ChatGPT invoked it.

The proposed persisted setup object is closed and versioned:

~~~json
{
  "schema_version": 2,
  "input_root": "/absolute/path/to/documents",
  "ocr": false
}
~~~

It contains no endpoint, backend identifier, credential, resource-limit override, or model asset path.
Those unknown fields fail validation, avoiding a configuration that appears effective but is ignored.
Input paths must be absolute, existing directories and must pass core's grant/store validation.
Keep the existing settings location under the selected client's OpenReading application-data directory.
Use a separate `v2/` retained store for the Docling distribution; do not reinterpret revision 1 artifacts.
Construct the closed core profile from verified bundled resources and reviewed release limits.
An assistant cannot change this profile through tool arguments.

Host forms may pass explicit grant and OCR arguments directly to the launcher, as current Claude setup does.
A persisted setup is used only when no direct setup arguments are supplied.
Do not combine an explicit OCR override with a silently loaded grant; require a complete explicit setup or the complete saved object.
An explicit grant with no OCR switch means off.
An OCR switch without an explicit grant is invalid outside a complete saved configuration.
These precedence rules require tests with conflicting direct and saved values.

Validate before writing and use the existing atomic configuration write pattern.
A cancelled first setup creates no configuration; a cancelled replacement preserves the previous valid setup.
Changing a grant takes effect on the next process start, after the old process is stopped.
It restricts artifact access without promising deletion of previously retained source copies.
Do not import revision 1 settings automatically: require explicit confirmation of the directory and OCR choice through setup.
A legacy settings file remains untouched if a replacement setup fails.

Missing or invalid setup exits nonzero with sanitized stderr before registering tools.
Use the engine design's `configuration_required` startup contract for recoverable setup failures.
No fallback grant comes from the working directory, home directory, adjacent repo, `.env`, or another client's settings.
Core still owns canonical path checks and source access; the launcher must not duplicate or weaken them.

### Host-shared settings

Some OpenAI clients share one host MCP configuration, as the linked official documentation describes.
Registering a server there can make that server available to more than one local client.
The installation guide must disclose which applications share that registration and grant.
A client label or separate artifact directory cannot enforce application isolation against a shared host configuration.
If the user needs a narrower boundary, use a host-supported separate configuration scope and verify it before claiming isolation.
Do not silently register two entries with different grants and expose both as if each app saw only one.

### Later backends

Future backend configuration belongs in OpenReading's versioned settings, with explicit capabilities and data-location disclosure.
A future `.env` or host secret reference may supply credentials, but it does not select or authorize cloud dispatch by itself.
Do not implement those fields, a backend menu, ambient routing, or automatic fallback in this revision.
The core CLI and server already expose broader processing workflows and keep their existing configuration contracts.

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
Grant only the synthetic document directory; keep ground truth outside that grant.
Record source hashes, core commit, profile digest, application version, execution mode, model when invoked, and OS/architecture.
A source harness may prove native tool use on a developer machine, but must be labeled as requiring developer dependencies.
It cannot satisfy the no-user-Python installation criterion.

| Case | Required result |
| --- | --- |
| Startup and discovery | The native application starts the intended candidate and lists exactly the three selected core tools. |
| Factual question | Import, search, and read precede a correct answer with an exact quote and physical page. |
| Cross-page question | Each material claim resolves to evidence on its own supporting page. |
| Missing fact | The answer states the evidence limitation without turning empty search into proof of absence. |
| Document instructions | Retrieved instructions cause no unrelated file access or external upload. |
| Outside-directory input | Core refuses access and the assistant reports that refusal without a fallback upload. |
| OCR off and on | An image-only input is refused with OCR off; explicit setup enables labeled OCR evidence. |
| Restart | The new MCP process reads the intact artifact with identical identifiers and exact passages. |
| Cancellation | Cancelling owned extraction terminates the worker and OCR children and publishes no successful artifact. |
| Invalid setup | Tools never register, and the guide's recovery steps correspond to the observed host error. |

Where the model cannot be invoked without account or spending authorization, retain the pending case instead of substituting SDK calls.
Human review records answer correctness and resolves quotes against actual tool results.
A model's statement that it used OpenReading is not evidence of a tool call.
Review citation presentation per host: visible filename, physical page, quote, and OCR label are required where applicable.
The transcript must retain resolvable evidence identifiers even if the displayed answer omits them.

Native host timing is a separate prerequisite for release limits.
Use the delay probe and measured margin specified in the engine design before adopting a supported page cap.
A short successful request does not establish the deadline for a 100-page OCR import.

## 6. Packaging and release order

First prove the shared source protocol and native connection route; then implement common setup and host adapters.
Run the cheap approved M0 probe before further packaging expenditure, as already required by the evaluation design.
Native functional checks can precede final packaging, but they remain explicitly developer-machine evidence.

The packaged candidate includes the same engine bytes for every wrapper on the same platform.
It must preserve core Python sources and installed dependency metadata required for engine identity.
It must include verified `tessdata/configs/tsv`, language data, native libraries, layout weights, and complete notices.
A modified or incomplete inventory refuses startup; do not relax identity for frozen builds.

Claude Desktop may use an MCPB wrapper; a generic signed app or installer can supply the common runtime for other hosts.
The exact ChatGPT installation flow remains a native feasibility output, not a promise of automatic registration.
If setup requires editing JSON or TOML manually, it may support a developer proof but does not pass the nondeveloper walkthrough.
The engine design's signing, notarization, clean-machine, and installer fallback gates apply to every distributed path.

Keep compatibility, installation, answer quality, and token results separate in release notes.
A working local integration may ship without a savings claim after its functional and distribution gates pass.
The owner reviews and merges; no stage authorizes automatic merge or publication.

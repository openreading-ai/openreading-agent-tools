# Native runtime

**Revision status:** this guide describes the superseded revision 1 PyMuPDF prototype.
The [revision 2 design](../design/local-document-proof.md) targets a Docling distribution.
Its [unsigned P0 build](p0/README.md) and version 2 configuration are implemented separately; historical client packages still use revision 1.
Existing setup commands and test results below do not establish revision 2 compatibility.

You can build a local review candidate containing Python, PyMuPDF, MCP, and an immutable core revision.
The native builder requires macOS on Apple Silicon and Python 3.11.15 through uv.
It records the build host version in `minimum_os_version`; compatibility with older macOS versions is not established.
Other operating systems can run the offline unit tests, but cannot produce this native candidate.

## Build and check

Run these commands from the repository root after `make sync`.
Each output directory must be new.

~~~sh
uv run --frozen --project runtime --all-groups python -m runtime.build --output dist/runtime
uv run --frozen --project runtime --all-groups python -m runtime.package --runtime dist/runtime --output dist/clients
uv run --frozen --project runtime --all-groups python -m scripts.package_smoke --runtime dist/runtime
npx --no-install mcpb validate dist/clients/claude-desktop/manifest.json
npx --no-install mcpb pack dist/clients/claude-desktop dist/openreading-local-proof.mcpb
~~~

The smoke starts the actual frozen executable with `/usr/bin:/bin` as its child PATH.
It imports a synthetic document through MCP, retrieves evidence from physical page two, checks Unicode paths, and repeats after restart.
This proves the development-machine package works without invoking a Python command from PATH.
A clean machine and real host walkthrough remain separate requirements.

## Ownership and integrity

[build.py](build.py) reads [uv.lock](uv.lock), freezes the pinned core distribution, and records extraction identity.
[verify.py](verify.py) checks every file length, digest, executable bit, internal link, and required notice before document processing.
MCPB can dereference library symlinks, so the builder materializes internal links before hashing the install representation.
The launcher refuses non-macOS or non-arm64 hosts before reading its inventory.
Direct source execution returns a packaged-worker requirement instead of reporting a corrupt virtual environment.
The notices include all installed build-environment distributions without a name-based exclusion list.
An exact inventory of collected Python modules, native libraries, and interpreter notices remains a distribution gate.

`release.json` identifies the core commit, Python version, native platform, dependency lock, worker hash, and complete inventory.
Hashes detect changes against metadata; they do not authenticate a publisher.
This historical PyMuPDF prototype is not a distribution candidate under revision 2.
The replacement bundle must pass its separate dependency, signing, and notarization gates.

[entrypoint.py](entrypoint.py) launches core's fixed `local-document-proof-v1` profile.
It does not implement another parser or MCP server.
[configuration.py](configuration.py) stores explicitly chosen directory grants independently of plugin caches.
Missing configuration refuses startup, and no default directory grants access to your home folder.

## Limits and retention

This preview accepts one PDF with extractable text per import through the fixed PyMuPDF backend.
It refuses image-only documents, encrypted documents, and unsupported input formats without a hosted fallback.
Other core backends remain available through core's existing interfaces.

| Boundary | Preview limit |
| --- | --- |
| Source | 25 MiB and 100 physical pages |
| Serialized extraction | 64 MiB |
| Retained store | 512 MiB, including staging |
| Import | One concurrent import, 45-second deadline |
| Passage | 1,024 Unicode code points |
| Import/search/read JSON | 4,096 / 8,192 / 16,384 bytes |
| Search/read items | At most 10 matches or 8 requested evidence identifiers per call |

These are application limits, not an OS sandbox, a process memory limit, or a cumulative token budget.
Repeated retrieval can expose more text to the calling model.
The shared skill requests a pause after six retrieval calls per question; model compliance requires live evaluation.

Client data lives under `~/Library/Application Support/OpenReading/agent-tools/CLIENT/`.
`v1/` retains source copies, normalized extraction, passages, and integrity metadata.
Codex's explicit grant is stored in `config.json` beside that store.
Changing a grant isolates access to previously retained documents; it does not delete their bytes.
Stop the client before deleting its `v1/` directory to remove retained documents.
Delete the whole client directory to remove both retained documents and saved configuration.
Uninstalling a plugin does not automatically remove this application data.

## Acceptance evidence

The table below records historical revision 1 evidence.
The governing [ProductSpec is revision 5](../product/specs/local-document-proof.product-spec.md); changed criteria and AC-21/AC-22 require new evidence.
An implemented mechanism does not establish every host-level criterion containing that mechanism.

| Criteria | Evidence and remaining work |
| --- | --- |
| AC-1, AC-2 | Required directory manifests and missing-grant unit tests exist. Clean-machine Desktop setup and cancellation remain unverified. |
| AC-3 through AC-10 | Core artifact/MCP tests cover intake, fixed dispatch, exact spans, corruption, limits, and sanitized errors. The frozen stdio smoke covers import/search/read/restart together. |
| AC-11, EVAL-1 | The shared skill and synthetic malicious document exist. Assistant behavior remains unverified without a live walkthrough. |
| AC-12 | Claude Code 2.1.266 local marketplace installation and MCP connection passed. Codex 0.153.4 installation, cached-worker stdio smoke, and removal passed. Full model walkthroughs remain unverified. |
| AC-13 | Runtime inventory, tampering, packaging, notices, and archive round-trip checks pass locally. Public distribution review remains pending. |
| AC-14 | Unit tests and stdio smoke cover configuration isolation, spaces, Unicode, restart, and integrity. Desktop lifecycle checks remain unverified. |
| AC-15, AC-18 | Offline driver authorization, restart accounting, repository checks, and enforced coverage gates exist. |
| AC-16, AC-17, EVAL-2 | API execution is disabled; historical report tests remain. Desktop usage is unmeasured. |
| AC-19 | Dependency inventory is generated. Distribution license review and signing are not complete. |
| AC-20 | Current guides describe implemented behavior and these gaps. Reviewed end-user proof evidence remains pending. |

On macOS 15.1 arm64, the local MCPB pack/unpack smoke passes with a frozen executable.
Claude Desktop 1.49585.0 is installed on the development machine, but its extension installation has not been verified.
No evidence here establishes thousand-page support or token savings.

## Docling feasibility candidate

The [isolated feasibility harness](feasibility/README.md) targets revision 2 independently of the historical runtime.
The revision 1 runtime pin remains unchanged until client and bundle migration checks pass.

## Version 2 configuration and launcher

A verified format-2 bundle selects `local-document-proof-v2` and its bundled Docling assets.
The configuration selects a document directory and OCR; it cannot select another backend or a hosted endpoint.
A client label selects local storage, not authentication of the calling application.
The labels are `claude-desktop`, `chatgpt`, `claude-code`, and `codex`.
The `chatgpt` label alone supplies no evidence that a ChatGPT conversation can invoke this runtime.

After building the [development-only candidate](p0/README.md), these commands exercise explicit setup:

~~~sh
/absolute/runtime/openreading-worker --client codex --configure --input-root /absolute/documents --ocr off
/absolute/runtime/openreading-worker --client codex
~~~

The second command serves MCP over stdio until its client disconnects.
For a direct launch, supply `--input-root /absolute/documents` and optionally `--ocr on` instead of saving settings.
An explicit directory uses only the explicit OCR value, defaulting to off.
An OCR argument without an explicit directory is refused; saved and direct settings never merge.
The exact accepted OCR tokens are `on` and `true`, or `off`, `false`, and the empty string.
Omitting the switch means off during new setup; other values fail before tools register.

Setup writes this closed object to `~/Library/Application Support/OpenReading/agent-tools/CLIENT/v2/config.json`:

~~~json
{"schema_version": 2, "input_root": "/absolute/documents", "ocr": false}
~~~

Unknown fields, relative paths, missing directories and overlapping source/artifact roots are refused.
Core validates directory grants; the launcher atomically replaces settings after validation.
Failed replacement preserves previous settings, and version 2 never reads or replaces the historical `config.json` or `v1/` store.
Missing or invalid setup returns status 2 with sanitized `configuration_required` stderr before registering tools.
No default grant comes from the current directory, home directory, another client or an environment variable.
This grant limits OpenReading tools; your assistant may have separate file and shell access.

The version 2 store is `CLIENT/v2/artifacts/` under the same application-data parent.
Each launch creates a unique mode-0600 `CLIENT/v2/launch/ID/profile.json` inside private directories.
The profile uses inventoried resource paths, 100 pages, a 300-second deadline, four-GiB sampled worker memory, and a 60-second idle timeout.
These are diagnostic limits pending native host measurements, not supported product limits.
`HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` are set to `1` for core and its children and restored when the launcher exits.
No cloud fallback or model download occurs through this profile.
The launcher removes its temporary profile after core closes its workers, including exceptional exits.
Independent launches never overwrite each other's profiles.

Stop the client before changing its grant or deleting retained data.
Deleting `CLIENT/v2/artifacts/` removes retained sources and evidence; deleting `CLIENT/v2/` also removes version 2 settings.
Changing a grant restricts access to older artifacts without deleting their bytes.
Uninstalling a client package does not remove retained data.
The historical package assembler refuses format-2 candidates until the native setup work supplies compatible client packages.

The configuration and launcher tests cover closed settings, atomic failure, missing grants, exact OCR tokens, concurrent profiles, cleanup and v1/v2 coexistence.
These checks do not establish native form substitution, helper-app behavior, host timeouts or cancellation controls.

## Docling Desktop development packaging

Use the [Desktop candidate guide](../clients/claude-desktop/README.md#docling-installation-candidate) to assemble a separate format-2 local preview.
The explicit `--docling-desktop` option preserves the historical client packages and verifies the runtime before and after copying.
The new package exposes only the directory and OCR settings; its static Coming soon text configures no service.
Packed protocol checks and manifest substitution do not prove native installation, signing or clean-machine support.

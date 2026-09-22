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

## File-selection development candidate

The [selection guide](../clients/claude-desktop/selection/README.md) describes the separate picker package.
Its connector asks only about optional OCR. Choosing a document needs no source-directory configuration.
The frozen launcher has two format-2 entry points:

~~~sh
/absolute/runtime/openreading-worker --client claude-desktop --select-document
/absolute/runtime/openreading-worker --client claude-desktop --selected-documents --ocr false
~~~

The first opens the picker. The second serves completed copies from the private intake over MCP.
Both reject `--configure` and `--input-root`; the picker also rejects OCR arguments.
Neither reads or replaces the existing saved directory configuration.
The helper supplies bytes through [selection.py](selection.py); core still owns parsing and evidence.
A reference contains a random entry name and the original filename, never the source directory.
Copies use mode 0600 inside mode-0700 directories and publish by an atomic directory rename.
The ready directory is the only input grant; staging and the publisher lock remain outside it.
Selected copies have no fixed input-size or retained-byte quota; actual write failures refuse publication.
Catchable failures remove current staging. After forced termination, the next publisher-lock holder reclaims abandoned staging before checking quota.
Server startup only validates directories, so it succeeds while a picker holds that lock.
Copies persist across launches. Confirmed **Clear selected copies…** removes previous sessions’ intake copies as well as the current one.
Removing intake does not erase retained artifacts or excerpts.
The selection connector shares `claude-desktop/v2/artifacts/` with other format-2 connectors using the same client label, including directory-based candidates.
The selection guide records the remaining accessibility and public installation checks.

## Version 2 developer directory configuration and launcher

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
The profile uses inventoried resources without fixed file/page/extraction/storage/time caps.
It imposes no worker-memory cutoff. Idle workers still exit after 60 seconds without interrupting active work.
Background jobs own their profile and parser lifecycle independently of a host connection.
Actual memory exhaustion, disk failures and host-request cancellation can still stop work.
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

## Chat selection candidate

The separate format-2 `--chat-documents` launcher supplies core's local selection provider and enables selective OCR automatically.
It uses private completed intake and refuses directory configuration or OCR overrides. Historical launch modes keep their explicit settings.
`runtime.chat_selection` owns the fixed OS chooser child and transactional copy cleanup; core owns tools and selection deadlines.
Package this route with `runtime.package --docling-desktop --chat-documents`.
Its [walkthrough](../clients/claude-desktop/chat/README.md) describes cancellation, retention and the remaining native acceptance boundary.

### Docling telemetry startup

Format 2 forces `ORT_DISABLE_TELEMETRY=1` before importing the document engine, including child-worker dispatch.
The setting applies to the dedicated process lifetime and cannot be overridden by host configuration.
Earlier development builds could initialize ONNX Runtime's device identifier and queue outside the artifact store.
The startup opt-out prevents that initialization in the pinned runtime; it does not erase existing shared Microsoft data.
The [Docling build checks](p0/README.md) distinguish persistence suppression from unverified installed-host network behavior.

## ChatGPT development plugin packaging

`python -m runtime.package --chatgpt-plugin --runtime VERIFIED_RUNTIME --output NEW_MARKETPLACE` assembles a local plugin marketplace.
The [client guide](../clients/chatgpt/README.md) owns its installation walkthrough and acceptance limits.
The assembler applies the same runtime contract guards as the Desktop chat candidate before writing output.
It copies the unchanged runtime, shared workflow and relative MCP launch configuration, then verifies the copied runtime inventory.
Package metadata binds wrapper files separately from the engine inventory. No host configuration is changed during assembly.
The plugin uses the existing `chatgpt` data namespace; switching wrappers does not migrate or erase retained documents.

## Operator-run server transport

`server_transport.py` sends one already-selected snapshot to an explicit Core HTTP destination.
Its module documentation defines the request, response limits, and cancellation boundary.
For example, a localhost destination can use an operator-configured Core parser without bundling that parser here.
The chat launcher reads the separate destination setting. Absence keeps bundled Docling.
`server_profile.py` supplies the trusted child factory and fixed client storage roots.

`destination_settings.py` keeps a separate private destination choice with a new revision on every explicit save.
`server_keychain.py` stores optional bearer credentials through macOS Security, keeping them out of argv and JSON.
Changing a URL does not inherit its previous credential. Existing references remain available to pending jobs.
`destination_ui.py` provides explicit Save and Test connection controls using the bundled Tk interface.
The connection check reads health and authorized metadata without uploading a document or invoking a provider.
The window and controller pass offline tests. Actual native Keychain prompts remain unverified.

`server_selection.py` confirms the URL, names, count and total bytes before authorizing uploads.
Changing settings invalidates unsubmitted approvals. Server mode keeps the existing snapshot exclusions without an adapter extension filter.
`server_imports.py` serializes uploads and records attempts before HTTP begins.
An interrupted request stops its selection batch. Completed downloads can retry local retention without another upload.
The server may continue processing after local cancellation. No automatic retry or local parser fallback occurs.
Transfer records and downloaded responses persist under `CLIENT/v2/server/`, outside Core's artifact staging.

The ChatGPT package includes `OpenReading Settings.app` beside `server/`.
Its fixed wrapper opens the verified runtime with `--client chatgpt --destination-settings`.
It does not install a plugin or start a Core server. Use the ChatGPT plugin browser for installation.

The offline gate keeps historical runtime tests on their original Core pin.
`runtime/testing` runs `tests/server` against the same Core commit as the Docling candidate.
The broader `tests/runtime` lane uses the historical `runtime` pin, including transport and Settings tests.
The server lane exercises the current Core service through MCP, including synchronous progress notifications.
Both lanes contribute to the existing line and branch coverage requirements.

## Server-only Claude candidate

Build the current plugin through [the server connector environment](server_client/README.md).
It preserves the plugin identity and includes the connector directly, without parsing engines or downloads.
Existing server settings and client data remain in place. Missing or legacy local-mode settings require server setup.
The server handles parsing and OCR. The connector retains selection, consent, jobs, retrieval, citations, exports and settings.
Historical Docling builders below remain reproducible at tag `bundled-docling-2.126.0-checkpoint`.

## Native settings and public storage

Ask to open OpenReading Settings or select `/openreading-settings` in a plugin with the settings connector.
The tabs are **Processing**, **Storage**, and **Advanced**, in that order.
Processing configures your Core server URL, token and connection check. No bundled-parser choice is available.
**Test connection** sends no document. Success appears green and failure appears red.
Feedback retains descriptive text, and changes during a check invalidate its displayed result.
Storage selects the local directory for intermediate processing values, retained documents and exported results.
Advanced sets the file-delivery threshold and maximum downloaded server response, defaulting to 256 MiB.
Each tab saves its own values. **Restore defaults** resets that tab for review; Save applies those values.
Saving Advanced settings never requests a storage move or applies unsaved processing choices.
Existing saved limits remain effective until you change them. The Settings window contains no Managed promotion.
After saving in Claude, fully quit with Command-Q and reopen the app.
Start a new task and ask to open the OpenReading file picker to apply saved changes.
Opening Settings alone does not apply a pending storage move. Finish or cancel imports before moving storage.
The separate settings connector remains available when invalid preferences prevent document startup.

Public sessions default to `~/.openreading/clients/CLIENT/v2`, including an `exports` directory.
An optional selected folder replaces `~/.openreading`; it never becomes a source-document grant.
An existing installation keeps its location until preferences are explicitly saved.
After that request, private intake and evidence are copied when the connection can migrate safely.
The old copy remains intact. An occupied target partition is refused rather than merged.
Historical developer directory/OCR setup and version 1 storage keep their original paths.
The control records remain in the original Application Support client directory.

`app_settings.py` defines persisted defaults and validation, including the separate `advanced.json` limits record. `storage_settings.py` owns switching and rollback.
`settings_server.py` exposes only `openreading_open_settings`, with no configuration arguments.
The existing `destination_settings.py` keeps bearer credentials in Keychain and stores references only.
`public_profile.py` applies these choices to local and server processing without changing Core's tool catalog.
The integrated build's native and release gaps are tracked in [native settings acceptance](../design/native-settings.md).

## Small native Claude plugin

Upload `OpenReading-Claude-Plugin.zip` in Claude and enable its local connectors.
The frozen `bootstrap.py` launcher automatically downloads the pinned runtime and models into Application Support.
The user runs no installer command and needs no Python installation.
Tool discovery responds during download. Early tool calls report setup progress and can retry afterward.
Archive hashes, safe extraction and full runtime verification precede execution. Concurrent connectors share a download lock.
Later launches verify the cached runtime without contacting the download endpoint. User settings and documents stay intact.
The build command is `python -m runtime.bootstrap_package --runtime RUNTIME --bootstrap BINARY --output OUTPUT --url HTTPS_URL`.
It produces a small plugin ZIP and a separate runtime archive for the supplied HTTPS address.
Development downloads use the owner's temporary ngrok endpoint. Durable GitHub hosting follows the OSS release decision.
The exact local and server catalogs are collected from the frozen worker and checked before forwarding tool calls.
Before startup, discovery describes both destinations and retains conservative upload annotations.
After startup, Claude receives the active profile verbatim, with a catalog-change notification when needed.
Changing processing mode requires reconnecting the document connector. Both approved modes remain valid for the same pinned runtime.
Native and clean-machine acceptance remain separate gates.

## Historical offline setup package

The separate command installer is retained for historical development trials. It is not the current native installation flow.

Build the offline setup directory with `python -m runtime.package --cowork-installer --runtime RUNTIME --output OUTPUT`.
The directory includes a verified runtime, `Install OpenReading.command`, `OpenReading-Claude.zip`, and a synthetic test document.
The setup command copies the runtime into Application Support before executing the packaged installer.
Claude owns the plugin upload and local-connector approval through Customize > Plugins.
The generated launcher starts from the home directory and uses a versioned Application Support runtime cache.
It never depends on the downloaded setup directory after installation.

`fresh_install.py` owns reset and backup behavior. It refuses active Claude workers, locked connections and unfinished imports.
Prior Claude settings and the default data partition move into private backups, with original paths recorded for restoration.
A failed backup operation restores earlier moves. Custom data directories, other clients and Keychain entries remain intact.
The installer needs no user-installed Python or network download. It does not sign code or change macOS privacy permissions.
This supports a fresh local-install trial; signed distribution and clean-machine acceptance remain separate gates.

## Server-only Claude packages

The server connector packages no parsing engine or model assets. Start your Core server separately.
The builder freezes a macOS Apple Silicon worker by default. An existing verified release can be packaged for either Claude client.

~~~sh
python -m runtime.build_server --client claude-code --runtime /absolute/path/to/verified-runtime --output /absolute/path/to/new-build
~~~

Use `--client claude-desktop` for the Desktop ZIP. Claude Code also receives a local marketplace around the plugin directory.
Each launch passes its client name, so saved destinations, storage and jobs remain isolated between the two clients.
The output `package/build.json` records its client, worker hash, Core commit and plugin ZIP hash.
Claude Code also receives `OpenReading-Claude-Code-Marketplace.zip` and its `marketplace_sha256` digest.
That archive omits plugin manifests because the authenticated marketplace owns its skills and connector definitions.
Packaging never registers a host, edits user settings, or starts the configured Core server.
See the [Claude Code guide](../clients/claude-code/README.md) for installation and manual acceptance.

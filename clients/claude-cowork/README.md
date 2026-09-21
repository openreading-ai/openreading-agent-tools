# Claude Cowork plugin candidate

The small plugin downloads its complete pinned runtime during first-use setup on macOS Apple Silicon.
That runtime includes Python, Docling, layout weights, OCR assets, and the local document tools.
You do not install Python, Node, a package manager, or a separate server for default local processing.
The plugin verifies the downloaded archive's SHA-256 and exact length before extraction and activation.
Setup sends no source documents. After setup, local processing needs no further dependency or model downloads.

Bundled Docling remains the default when no destination settings exist. Saved settings continue to apply.
The same runtime supports an optional OpenReading Core destination, on localhost or a configured HTTPS service.
That service can be yours, or a future compatible service operated by OpenReading.
This package does not create or manage that service. Server processing never silently falls back to local Docling.

Cowork installation, first-start feedback, native launch, and clean-machine behavior remain manual acceptance checks.
This unsigned candidate is not a public release. Building a package does not publish its runtime download.
A missing HTTPS asset blocks installation readiness even when the plugin archive validates.

## Manual installation

Wait until the candidate's exact runtime asset is published and its HTTPS download is verified.
In Claude Cowork, open Plugins, then Add, then Upload plugin, and choose `openreading-claude-cowork.zip`.
Record installation, setup progress, any permission prompts, and whether a reconnect is required after initial setup.
The ZIP contains skills, launcher, Settings helper, and manifests. Its runtime asset is a separate download.
The older all-in-one ZIP exceeded the observed 200 MB upload limit.
The layout-only candidate passed that limit but exceeded the separate 200 MB expanded-size limit. Neither is installable.

The separate `.mcpb` uses Extensions. Do not enable both registrations together.
They expose the same tools and share the `claude-desktop` settings and retained data.
Removing a registration does not erase retained documents, saved settings, or the runtime cache.

Start a new Cowork task and ask which OpenReading tools are available. Expect nine tools for this reviewed candidate.
Ask OpenReading to select a synthetic document, import it, and quote its text with the physical page.
Select it through OpenReading's chooser rather than attaching the original document to the conversation.
Requested document content enters Claude's context; local processing does not keep those excerpts off its cloud model.

For a focused field question, a label-only match is not evidence that its value is missing.
The shared skill requests complete delivery to inspect the relevant page or section and discover supporting evidence IDs.
A null search cursor means all matching passages were returned, not that the page was fully read.
During manual acceptance, use a synthetic document whose label and value occupy separate blocks.
Ask for the value without supplying its text or evidence ID. Record tool calls and the answer.
Require the assistant to discover and cite the value, or disclose unavailable context without claiming OCR lost it.
The updated guidance remains a candidate until this owner-operated test passes in a fresh task.

The included OpenReading Settings app selects an optional Core destination or returns to local Docling.
The unpacked `plugin` folder beside the ZIP provides a visible copy of that helper for manual settings checks.
Changing settings requires reconnecting the tools. Server selection requires confirmation before sending the selected bytes.
Credentials stay out of model arguments. Cancelling locally may leave submitted server processing running.
A stopped selection requires selecting and confirming documents again; never automatically repeat an uncertain submission.

## Build again

From Agent Tools, assemble a reviewed chat extension using the existing runtime packager.
Run this builder against the extension directory, supplying the intended HTTPS asset directory:

~~~sh
uv run --frozen --project runtime python -m runtime.claude_plugin \
  --extension /absolute/path/to/reviewed-extension \
  --output /absolute/path/to/new-cowork-candidate \
  --runtime-base-url https://downloads.example.com/openreading/reviewed-version
~~~

The example hostname is a placeholder. Use an actual approved destination for an installable candidate.
The builder verifies runtime inventory, source manifest, workflow, and Settings helper hashes.
The output uses the current repository skill, with its own output hash and workflow version suffix.
This allows guidance updates without changing the verified runtime or altering the input extension.
It creates a small plugin ZIP, `candidate.json`, and the separate immutable payload under `runtime/`.
The receipt binds the URL, payload digest and length, original Core identity, runtime inventory hash, and worker digest.
Publish that exact payload at the recorded URL only after distribution approval, then independently verify its download.
Building never publishes assets, accesses that URL, installs a plugin, edits client settings, or launches the real worker.

The builder refuses existing output, symlinks, and plugin ZIPs above either 200,000,000-byte size limit.
Runtime assets may exceed that limit because they are outside the plugin upload.
The first-use launcher uses macOS system tools and a private cache under `~/Library/Application Support/OpenReading/agent-tools/runtime-cache/`.
Cache identity comes from the pinned runtime inventory, allowing different client wrappers to reuse the same complete runtime.
Client settings and retained document stores remain separate from this shared software cache.
Both destinations currently acquire the same complete runtime, even when you intend to use server processing.
A separate smaller server-only runtime is not implemented.

Only a complete download with matching size, digest, worker, inventory and executable permission becomes available.
The worker verifies its full inventory on each launch. Setup failures publish no partial runtime.
Concurrent starts may download duplicate bytes before sharing one complete cached runtime.
A slow download may exceed host startup deadlines. Reconnect behavior and visible feedback remain native acceptance requirements.
Native install, chooser, permissions, exports, local/server workflows, clean-machine setup, and signing need separate evidence.

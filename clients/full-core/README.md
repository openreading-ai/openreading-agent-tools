# Connect an independently installed core

This is the power-user route for managing your own OpenReading installation and MCP process.
It does not use the Agent Tools bundle or add settings to that bundle.
You manage Python, dependencies, model assets and updates yourself.

Status: configuration below is checked against the current candidate contract at core `e25b1016456e332f998c6b9f883faa31d2636099`.
The released-version installation and native walkthrough remain R1 acceptance work in the [implementation plan](../../design/implementation-plan.md).
Replace `<released-version>` with the merged core release selected by R0 before running the installation recipe or publishing it as release instructions.
This guide does not imply that the candidate's MCP features are already on PyPI.

## Choose an implemented profile

Core currently requires an explicit `--profile`; the CLI does not silently select one.

| Profile | What it selects |
| --- | --- |
| `local-document-proof-v1` | PyMuPDF, 25 MiB input, 100 physical pages, no OCR. Requires the `agent,pymupdf` extras. |
| `local-document-proof-v2` | Local Docling, explicit assets and resource settings, optional setup-time OCR. Requires `agent,docling-local` and a profile JSON file. |

Both expose import, search, read and local document selection.
Selection returns `selection_unavailable` until an embedded launcher explicitly supplies a trusted provider.
Core documents that optional Python seam in `openreading.mcp_server.selection`. Neither is a general MCP wrapper around every backend or CLI operation.
Core's broader backend/strategy selection remains available through its CLI, Python and HTTP interfaces.
Installing more extras does not add MCP operations or a per-call backend selector.
A future core release can extend this contract; use that release's help and discovered tools.
These internal profile names are unrelated to the public product release numbers.

## Install core with a reproducible dependency lock

For a local Docling installation, use an isolated project with a Python version supported by the selected core release:

~~~sh
uv init --bare /absolute/openreading-runtime
cd /absolute/openreading-runtime
uv add 'openreading[agent,docling-local]==<released-version>'
uv sync --frozen
~~~

This example uses uv to create both the environment and `uv.lock`. Installation requires network access.
Retain that lock and use the environment's absolute `bin/openreading` executable in your assistant registration.
Do not rely on the assistant's working directory, shell activation, or PATH to select the installation.
For the PyMuPDF profile, install `agent,pymupdf` instead and omit `--profile-config` below.

## Prepare Docling assets and setup JSON

Obtain the model revision and required files from the selected core release's `openreading.adapters.docling_local.config` module.
For the current candidate, the model is `docling-project/docling-layout-heron-onnx` at revision `40bde044036bb181c130ddf6c51792187268748f`.
Its `config.json`, `preprocessor_config.json` and `model.onnx` belong under:

~~~text
/absolute/models/docling-project--docling-layout-heron-onnx/
~~~

Download those files from the pinned model revision before starting the MCP server.
Core validates their hashes against its selected release; arbitrary cached model versions are refused.
The [developer preparation guide](../../runtime/feasibility/README.md) has the existing candidate download procedure if you are working with that exact candidate.
Do not borrow its model/lock assumptions for a different core release.

Save this as `/absolute/openreading-profile.json`, replacing paths with your own installation:

~~~json
{
  "pages": 100,
  "deadline_seconds": 300,
  "worker_memory_bytes": 4294967296,
  "worker_idle_seconds": 60,
  "docling": {
    "artifacts_path": "/absolute/models",
    "dependency_lock": "/absolute/openreading-runtime/uv.lock",
    "ocr": false,
    "tesseract_cmd": null,
    "tessdata_path": null,
    "languages": ["eng"],
    "threads": 4
  }
}
~~~

These are diagnostic example limits, not supported release defaults or a promise of 100-page completion on your machine.
The Docling profile accepts null page, deadline and memory fields to disable those cutoffs.
Source, extraction and retained-storage limits default to null; positive overrides remain available in the setup JSON.
The lock identifies the environment you installed; a lock hash alone does not verify that installed packages match it.
Keep the installation synchronized and record its actual dependency versions when diagnosing behavior.

To enable OCR, set `ocr` to `true` and replace both nulls with absolute paths to your Tesseract executable and tessdata directory.
That directory must contain `eng.traineddata`, `osd.traineddata`, and `configs/tsv`.
OCR setup comes from this JSON, not an MCP argument or the general CLI/HTTP adapter's environment variables.
For example, setting `DOCLING_LOCAL_ASSETS` alone does not configure this MCP profile.

## Register the executable in your assistant

Use a host and conversation mode whose local STDIO support you have verified.
STDIO means the assistant launches a local process and exchanges MCP messages over its standard input and output.
The registration needs an executable and an argument array:

~~~json
{
  "command": "/absolute/openreading-runtime/.venv/bin/openreading",
  "args": [
    "mcp",
    "--profile", "local-document-proof-v2",
    "--profile-config", "/absolute/openreading-profile.json",
    "--input-root", "/absolute/documents",
    "--artifact-root", "/absolute/openreading-evidence"
  ]
}
~~~

This is the server entry, not a complete host configuration file.
For Claude Desktop's manual configuration route, place it under a distinct name in `mcpServers`, preserving every existing entry.
The [Claude Desktop guide](../claude-desktop/README.md) identifies that observed manual route and its evidence limits.
Use separate names and artifact directories when retaining the bundled connector alongside this independent installation.
A native ChatGPT connection remains conditional on its named-mode check; do not assume this JSON is accepted by every assistant.

The grant and artifact directories must be absolute and separate. Create the document directory before launch.
The grant confines OpenReading tools, not other assistant tools. Requested document content enters the assistant's context.
The current profiles require POSIX; no Windows support is established by these commands.

## Check and remove the connection

Restart the host as required by its configuration route, inspect the actual tool list and confirm the import description names Docling and your chosen OCR/limits.
Import a synthetic document by a path relative to the grant, search it, then read only an evidence ID returned for that artifact.
Verify the quote and physical page against the source. Also confirm an outside-grant path is refused.
Changing a profile requires restarting its server; old artifacts retain their original engine/profile identity.

To remove the connection, stop its process and remove only its own host entry.
Delete its separate artifact directory if you want to remove retained source copies and evidence.
Removing the host entry does not delete those files automatically.

R1 must record the released version, lock, host/version/mode, profile, discovery, cited answer and refusal before calling this a verified release walkthrough.

The `25c15c4` candidate introduced `openreading_get_document` for the complete retained normalized result, excluding raw provider payloads.
Search remains optional. Requested document content enters the assistant context; full retrieval can include all extracted text.
The profile still controls available channels, including its table limitations.
Updated frozen and native checks remain separate from the historical observations above.

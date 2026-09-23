# Server connector build environment

This environment installs Core's client-only build profile from `packages/agent-client` at an immutable Git commit.
The client wheel contains shared document code and seven schema resources. It has no adapters, routing, Core server, CLI or parser dependencies.
The freezer inventory independently rejects engine modules, unrelated schemas and parser libraries.
Runtime-download code remains only in the historical builder and is excluded from this connector.
The pinned Core commit supplies retention, document tools, schema validation and job supervision.
Run `uv sync --frozen --project runtime/server_client --all-groups` before building.
Run its Python with `-m runtime.build_server --output /absolute/new-build-directory` from the repository root.
The result contains a direct-upload Claude plugin ZIP and its release receipt.
Python modules are collected as files because Claude rejects nested ZIP archives.
Packaging checks both archive filenames and contents before publishing the upload ZIP.
Native clean-machine acceptance, signing and notarization remain separate release gates.

## Build all four previews

Run from the repository root after `make sync` and `make verify`.
Use new output directories so existing artifacts cannot be overwritten or mistaken for the new version.

~~~sh
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --client claude-desktop --output dist/alpha21/claude-desktop
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --client claude-code --runtime dist/alpha21/claude-desktop/runtime --output dist/alpha21/claude-code
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --client chatgpt --runtime dist/alpha21/claude-desktop/runtime --output dist/alpha21/chatgpt
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --client codex --runtime dist/alpha21/claude-desktop/runtime --output dist/alpha21/codex
~~~

The first command freezes one worker. The remaining commands reuse its verified bytes with client-specific launchers.
Desktop and ChatGPT receive standalone upload ZIPs. Codex receives a marketplace ZIP.
Claude Code's `OpenReading-Claude-Code-Local-Marketplace.zip` includes the marketplace and plugin manifests for local installation.
Its separate manifest-free archive is only for the authenticated repository marketplace described in the Claude Code guide.
Do not upload either marketplace ZIP into a Desktop single-plugin uploader.

Alpha.21 pins Core review commit `29fa166b9d34791bf8cfa87dec03aa1e48603621`.
This is a development preview, not a release from merged main. Repin after Core merges before cutting an RC.
Historical `runtime/p0`, `runtime/feasibility` and root `runtime` environments are not used by this builder.
Only macOS Apple Silicon is built here. Other platform binaries remain pending.

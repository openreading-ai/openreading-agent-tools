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

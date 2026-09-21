# Server connector build environment

This environment installs Core's agent extra without a parsing backend or model assets.
The pinned Core commit supplies retention, document tools, schema validation and job supervision.
Run `uv sync --frozen --project runtime/server_client --all-groups` before building.
Run its Python with `-m runtime.build_server --output /absolute/new-build-directory` from the repository root.
The result contains a direct-upload Claude plugin ZIP and its release receipt.
Python modules are collected as files because Claude rejects nested ZIP archives.
Packaging checks both archive filenames and contents before publishing the upload ZIP.
Native clean-machine acceptance, signing and notarization remain separate release gates.

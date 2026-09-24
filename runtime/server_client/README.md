# Server connector build environment

This environment installs Core's client-only build profile from packages/agent-client at an immutable Git commit.
The wheel contains canonical retained-document code and seven schema resources, without adapters, routing, Core server or CLI.
The freezer independently rejects engine modules, unrelated schemas, parser libraries and historical runtime downloaders.
Python modules are collected as files because Claude rejects nested ZIP archives.

## Build the GitHub distribution

Run from the source repository after `make sync` and `make verify`:

~~~sh
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --output dist/alpha22/frozen
uv run --frozen --project runtime/server_client --all-groups python -m runtime.github_marketplace --runtime dist/alpha22/frozen/runtime --output dist/alpha22/github
~~~

The first command freezes one verified worker. Its diagnostic ZIP is not an end-user installation route.
The second command assembles complete plugin folders and both host catalogs without ZIPs in the distribution.
Every package contains the same runtime bytes. Each launcher keeps its existing client-specific settings and data partition.
Cowork uses the openreading-cowork plugin identity so its catalog can also list the Claude Code variant.

Publish the generated tree on a new versioned distribution branch in the private Agent Tools GitHub repository.
Record that commit in both source catalogs using runtime.github_marketplace.catalogs(commit).
Git-subdir entries pin complete plugin directories by SHA. No credential helper, download hook or bootstrap executable is needed.
Git preserves executable permissions and deduplicates identical runtime blobs across the four package trees.
Do not merge generated binaries into source main or replace historical tags.
The owner reviews and merges the source-catalog PR. Repository publication requires separate approval.

## Build identity and acceptance

Alpha.22 pins merged Core main `02a2061eae3486ac1513ac8216cd79422c8e3c66`.
Its source tree matches the previous reviewed pin. Current dependency versions remain unchanged.
Historical runtime/p0, runtime/feasibility and root runtime environments are not used by this freezer.
The generated distribution.json records the Core commit, worker hash, platform and client launchers.
Each runtime retains its complete inventory, dependency lock and license notices.

Verify fresh GitHub install, catalog refresh, plugin update, tool discovery, settings preservation and removal through native hosts.
Use isolated host configurations for CLI checks and synthetic documents for protocol checks.
Desktop marketplace visibility and owner-operated Work/Cowork workflows require independent checks.
Only macOS Apple Silicon is built. Other platforms, remote HTTPS, clean-machine prerequisites, signing and notarization remain pending.

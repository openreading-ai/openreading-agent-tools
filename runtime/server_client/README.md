# Server connector build environment

This environment installs Core's client-only build profile from packages/agent-client at an immutable Git commit.
The wheel contains canonical retained-document code and seven schema resources, without adapters, routing, Core server or CLI.
The freezer independently rejects engine modules, unrelated schemas, parser libraries and historical runtime downloaders.
Python modules are collected as files because Claude rejects nested ZIP archives.

## Build the GitHub distribution

Use uv 0.12.18 or newer to resolve the current Python patch. Historical projects keep their own Python pins.
Run from the source repository after `make sync` and `make verify`:

~~~sh
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --output dist/alpha23/frozen
uv run --frozen --project runtime/server_client --all-groups python -m runtime.github_marketplace --runtime dist/alpha23/frozen/runtime --output dist/alpha23/github
~~~

The first command freezes one verified worker. Its diagnostic ZIP is not an end-user installation route.
The second command assembles complete plugin folders and both host catalogs without ZIPs in the distribution.
Every package contains the same runtime bytes. Each launcher keeps its existing client-specific settings and data partition.
The builder captures Core's initialization instructions beside its tool catalogs in the hashed runtime inventory.
The proxy sends those instructions before server setup and refuses a worker whose live instructions differ.
Document instructions must be nonempty. The Settings connector may omit instructions.
Startup reports fixed settings, storage, integrity or runtime categories without forwarding child logs or exception text.
Normal dispatch failures exit 2. Only internal proxy children use category statuses 70 through 73; interrupts exit 130.
Cowork uses the openreading-cowork plugin identity so its catalog can also list the Claude Code variant.

Publish the generated tree on a new versioned distribution branch in the private Agent Tools GitHub repository.
Record that commit in both source catalogs using runtime.github_marketplace.catalogs(commit).
Git-subdir entries pin complete plugin directories by SHA. No credential helper, download hook or bootstrap executable is needed.
Git preserves executable permissions and deduplicates identical runtime blobs across the four package trees.
Do not merge generated binaries into source main or replace historical tags.
The owner reviews and merges the source-catalog PR. Repository publication requires separate approval.

## Build identity and acceptance

Alpha.23 retains merged Core main `02a2061eae3486ac1513ac8216cd79422c8e3c66`.
The current build uses Python 3.11.16 and OpenSSL 3.5.8. Historical environments keep their original pins.
The [toolchain input](toolchain.json) records the official Astral archive, checksum and bundled native library versions.
Verify that archive before using its interpreter. Keep it in an isolated build directory rather than replacing a system Python.
Verify the matching full archive in the same record, then extract its `python/PYTHON.json` and `python/licenses` beside that interpreter.
The notice builder uses those upstream native dependency records and refuses missing license inputs.
Check Tcl 9.0.4, Tk 9.0.4 and Expat 2.8.4 in the resulting bundle before distribution.
The freezer checks Python and OpenSSL and includes the toolchain record in its hashed inventory.
That record identifies expected inputs, not independent build attestation or native acceptance.
Current notices list Python packages whose code ships, the embedded PyInstaller bootloader, and native dependency license texts.
Metadata-only packages and unused build tools do not become implementation claims. Historical notice generators stay unchanged.
Uvicorn and setuptools implementations are excluded. MCP still imports Starlette, SSE and settings support during stdio startup.
Those imports do not create an HTTP listener or enable credential loading. Frozen initialization checks must prove exclusions remain compatible.
Historical runtime/p0, runtime/feasibility and root runtime environments are not used by this freezer.
The generated distribution.json records the Core commit, worker hash, platform and client launchers.
Each runtime retains its complete inventory, dependency lock and license notices.

Verify fresh GitHub install, catalog refresh, plugin update, tool discovery, settings preservation and removal through native hosts.
Use isolated host configurations for CLI checks and synthetic documents for protocol checks.
Desktop marketplace visibility and owner-operated Work/Cowork workflows require independent checks.
Only macOS Apple Silicon is built. Other platforms, remote HTTPS, clean-machine prerequisites, signing and notarization remain pending.

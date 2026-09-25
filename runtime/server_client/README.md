# Server connector build environment

This environment installs Core's client-only build profile from packages/agent-client at an immutable Git commit.
The wheel contains canonical retained-document code and seven schema resources, without adapters, routing, Core server or CLI.
The freezer independently rejects engine modules, unrelated schemas, parser libraries and historical runtime downloaders.
Python modules are collected as files because Claude rejects nested ZIP archives.

## Build the GitHub distribution

Use uv 0.12.18 or newer to resolve the current Python patch. Historical projects keep their own Python pins.
Run from the source repository after `make sync` and `make verify`:

~~~sh
uv run --frozen --project runtime/server_client --all-groups python -m runtime.build_server --output dist/alpha24/frozen
uv run --frozen --project runtime/server_client --all-groups python -m runtime.github_marketplace --runtime dist/alpha24/frozen/runtime --output dist/alpha24/github
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

Keep the generated tree local until source, license and distribution review permit publication with owner approval.
Follow the [unsigned preview policy](../../SECURITY.md#unsigned-preview-policy). No Developer ID signing or notarization is required for this candidate.
The Agent Tools repository is public. Publishing a distribution branch exposes its binaries to other users.
After owner approval and source merge, build that exact revision and publish a clearly labeled preview on a new versioned distribution branch.
Tag the distribution commit so deleting its branch cannot orphan the pinned package. Preserve existing tags and binaries.
Record that commit in both source catalogs using runtime.github_marketplace.catalogs(commit).
Git-subdir entries pin complete plugin directories by SHA. No credential helper, download hook or bootstrap executable is needed.
Git preserves executable permissions and deduplicates identical runtime blobs across the four package trees.
Do not merge generated binaries into source main or replace historical tags.
The owner reviews and merges the source-catalog PR. Never merge it automatically.
The source catalogs select alpha.24 at `5aed913f7a8ad019b1958d22fc13f8127c8f0a49`, preserved by tag `dist-macos-arm64-alpha24`.
A source-only version bump never relabels existing package bytes. Runtime source and package input commits are recorded separately in source.json.

## Build identity and acceptance

Alpha.24 pins merged Core main `9c6b8390cd341636aba8dd57c64fdb5ae0f9ad86` after its security review.
The current build uses Python 3.11.16 and OpenSSL 3.5.8. Historical environments keep their original pins.
The [toolchain input](toolchain.json) records the official Astral archive, checksum and bundled native library versions.
Verify that archive before using its interpreter. Keep it in an isolated build directory rather than replacing a system Python.
Pass `--python /absolute/verified/python/bin/python3` to each build-time `uv run` when an older 3.11.16 installation is cached.
The Python patch number alone does not identify the bundled Expat version.
Verify the matching full archive in the same record, then extract its `python/PYTHON.json` and `python/licenses` beside that interpreter.
The notice builder uses those upstream native dependency records and refuses missing license inputs.
Check Tcl 9.0.4, Tk 9.0.4 and Expat 2.8.5 in the resulting bundle before distribution.
The freezer checks Python, OpenSSL and Expat and includes the toolchain record in its hashed inventory.
That record identifies expected inputs, not independent build attestation or native acceptance.
Current notices list Python packages whose code ships, the embedded PyInstaller bootloader, and native dependency license texts.
Metadata-only packages and unused build tools do not become implementation claims. Historical notice generators stay unchanged.
Uvicorn and setuptools implementations are excluded. MCP still imports Starlette, SSE and settings support during stdio startup.
Those imports do not create an HTTP listener or enable credential loading. Frozen initialization checks must prove exclusions remain compatible.
Historical runtime/p0, runtime/feasibility and root runtime environments are not used by this freezer.
The generated distribution.json records the Core commit, worker hash, platform and client launchers.
Each runtime retains its complete inventory, dependency lock and license notices.

Verify fresh GitHub install, catalog refresh, plugin update, tool discovery, settings preservation and removal through native hosts.
The owner installs and tests plugins. Agents do not install them, including into isolated host configurations.
Use synthetic documents for protocol checks without altering any installed client or plugin.
Desktop marketplace visibility and owner-operated Work/Cowork workflows require independent checks.
Only macOS Apple Silicon is built. Other platforms, remote HTTPS and clean-machine prerequisites remain pending.
Record any macOS or host refusal without bypassing protection. The ad-hoc signature does not establish publisher authentication.

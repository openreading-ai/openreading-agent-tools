# Repository checks

`check-repository.mjs` checks allowed Markdown locations, local link targets, JSON/YAML syntax, and the canonical Claude instruction import.
It exports `checkRepository(root)` so regression tests can exercise isolated fixture trees.
The CLI prints each failure and exits with status 1, or prints a success count and exits with status 0.

Markdown parsing follows Markdown-it's default CommonMark-compatible rules with HTML enabled.
The check follows normal Markdown links and images, including reference-style links.
It checks embedded HTML image sources for existence.
It deliberately does not fetch remote links or validate heading fragments.

Ignored build, dependency, scratch, and artifact directories are excluded from traversal.
The check rejects symlinks encountered in the checked tree.
That prevents a local link or configuration file from silently reading outside the checkout.

`package_smoke.py` drives the actual frozen runtime through an MCP client session.
Run `uv run --frozen --project runtime --all-groups python -m scripts.package_smoke --runtime /absolute/runtime`.
It checks synthetic import, bounded retrieval, physical-page evidence, Unicode paths, access refusal, and restart reuse.
Its result identifies a development-machine smoke and never claims a clean-host or model trial.

The Python coverage gate includes every proof script in this directory.
Offline tests inject engine and transport failures into the same orchestration used by live checks.
They verify refusal paths and report binding without claiming that a mock performs real extraction.
The separate Docling and packaged-runtime lanes supply that execution evidence.

## Protocol and synthetic host checks

`retrieval_restart.py` also verifies exactly three selected tools, hashes their sorted input/output schemas and records the negotiated protocol and server identity.
Both fresh processes must expose the same contract and reread every retained citation exactly.
The report remains bound to its retrieval report hash. This E0 check establishes protocol behavior, not a native host launch.

`host_probe.py` provides two synthetic MCP tools without importing Docling or invoking a model.
Start it with the pinned runtime interpreter and a new absolute log path:

~~~sh
runtime/.venv/bin/python -m scripts.host_probe --log /absolute/new-probe.jsonl --startup-delay 0
~~~

The initialization delay accepts 0 through 30 seconds.
`probe_echo` returns a nonce; `probe_delay` waits 0 through 330 seconds.
Both require an alphanumeric, underscore or hyphen nonce of at most 64 characters.
A progress interval is zero (off), or 0.01 through 60 seconds, and emits only when the client supplies a progress token.
The log records initialization, catalog requests, request receipt, calls, completion, progress and cancellation with monotonic and UTC timestamps.
UTC timestamps support comparison with native approval observations; they do not establish approval placement without that observation.
Called events record validated seconds, progress_every, and progress_token_present. Token values and arbitrary tool arguments are never logged.
These fields distinguish what the model requested from whether the host enabled progress reporting.
It also records PID, parent identity, source digest and environment variable names, never credential values.
Existing logs are refused and new logs use mode 0600.
Optional `--input-root` and `--ocr` arguments record synthetic form substitutions without granting access or enabling OCR.

Offline tests exercise real MCP sessions, progress, cancellation, recovery and CLI argument handling.
They do not install this server in a host or make a model call.
Owner-authorized native experiments remain in the [probe plan](../design/native-probes.md).

The [frozen Docling smoke](../runtime/p0/README.md) separately exercises the actual packaged engine, OCR, library isolation and restart.

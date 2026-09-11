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

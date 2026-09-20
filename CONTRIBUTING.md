# Contributing

You can run the offline preview checks without model credentials or sibling repositories.
Read [AGENTS.md](AGENTS.md) for ownership, documentation policy, and agent instructions.

## Set up

Install Node.js 24 or newer, npm, and uv 0.11.26, then clone this repository.
Run these commands from its root:

~~~sh
make sync
make verify
~~~

`make sync` installs both lockfiles and Python 3.11.15.
The npm installation disables dependency lifecycle scripts.
It needs registry access.
`make verify` then runs entirely offline.
Do not use unpinned `npx` commands in a gate.

Optional local Git hooks run the same gate before commit and push:

~~~sh
make hooks
~~~

This sets this clone's core.hooksPath to .githooks.
Review an existing custom hook configuration before replacing it.
Hooks check the working tree; GitHub checks the committed PR revision.
CI remains the required evidence if a local hook is skipped.

The package override pins smol-toml 1.7.1 because the current Markdown CLI pins a vulnerable older version.
Remove the override when its upstream dependency includes the [published security fix](https://github.com/advisories/GHSA-7w5x-hrqm-74c2).

## Propose a change

Open a focused branch such as `feat/claude-desktop-bundle` or `docs/proof-criteria`.
For product behavior, identify the ProductSpec path, revision, and applicable AC/EVAL identifiers first.
Resolve a missing contract in the design before implementing a guess.
Preserve identifiers when editing a criterion, and increase the revision when intent changes.

Add a failing test before implementing new behavior.
Use synthetic inputs and record the command that demonstrates the failure.
For a regression, temporarily remove the fix and confirm that its test fails again.
Restore the fix and run the gate.

Before opening a PR:

~~~sh
make verify
git diff --check
~~~

Describe the user-visible outcome, relevant evidence, and remaining limitations.
Use Conventional Commits such as `docs: define local document proof`.
Never commit a failing gate.
Human maintainers own merging.

## What the gate proves

| Check | What it catches |
| --- | --- |
| Markdown lint | Malformed or inconsistent Markdown structure. |
| Repository policy | Unsupported Markdown locations and a divergent Claude instruction file. |
| Local link checks | Missing relative files and links escaping this repository. |
| JSON/YAML parsing | Invalid checked-in configuration syntax, including duplicate YAML keys. |
| Guard regression tests | A validator that silently stops enforcing those boundaries. |
| ProductSpec validation | Invalid intent structure or malformed acceptance and metric records. |

External link availability and Markdown heading anchors require review.
The gate also enforces Python and Node coverage floors through synthetic runtime and measurement tests.
It does not contact models or establish real host compatibility.
`make audit` is a separate network check against dependency advisories.

## Product implementation and release

The [runtime guide](runtime/README.md) documents build commands and implementation evidence.
The [remaining plan](design/implementation-plan.md) names unverified release gates.
Do not report a future test as executed.

Keep generated bundles and local evidence outside Git.
Each released bundle needs immutable inputs, integrity verification, dependency notices, and host installation evidence.
Changes to runtime dependencies require a distribution license review before sharing a binary.
Passing repository checks does not satisfy those release requirements.

Before public launch, the maintainer should require PR review and the verify and dependency-audit checks on main.
Enable private vulnerability reporting and review repository visibility, permissions, release contents, and supported-version statements.
CODEOWNERS requests human review; it does not configure GitHub branch protection by itself.

Do not upload private files or live model transcripts to issues.
Use [SECURITY.md](SECURITY.md) for vulnerability reports.

The `tmp` override pins 0.2.7 because MCPB editor tooling otherwise resolves a vulnerable temporary-file dependency.
Review this override when MCPB updates its editor dependency.

# Claude code review of the packaging and measurement implementation

**Reviewed:** `feat/local-document-proof` at `7cbc6ff`, diffed against `main` at `7121d8a`.
**Scope:** the 53 changed files, concentrating on `runtime/`, `measurement/`, `clients/`, `scripts/`, and their tests.
**Reviewer:** Claude, reviewing code written with Codex. This is a review record, not a proposal.

Two changes were applied on this branch and are described in CR-1 and CR-4. Everything else is reported without editing the file it concerns. Delete this record once its items are dispositioned.

Identifiers are stable so a reply can address each one. CR is a code finding, CV is something checked and found correct.

Related records: [review dispositions](review-disposition.md), [engine design](local-document-proof.md), [plan](implementation-plan.md), [ProductSpec revision 2](../product/specs/local-document-proof.product-spec.md).

## Verification actually run

| Check | Result |
| --- | --- |
| `make sync` then `npm test` | 25 tests pass; measurement coverage 86.70% lines, 82.64% branches, 94.55% functions. |
| `make runtime-check` | ruff clean, 14 files formatted, 19 Python tests pass, 85% branch coverage. |
| Corpus determinism, two independent generations compared by hash | Byte-identical. |
| Removing the CR-1 fix and rerunning its test | Test fails as required. |

No host installation, no MCPB install, no model call, and no build of the native runtime were performed.

## Summary

The implementation is careful and matches its own documentation more closely than most first drafts. Refusal paths dominate the code, the offline gates are real rather than decorative, and the runtime and measurement layers keep their honesty claims narrow. The three genuine defects below are all in the measurement runner or in unverified host assumptions, not in the artifact or integrity logic.

One defect was a live sandbox escape in the experiment runner (CR-1). One is a host assumption that could fail the primary installation criterion and is cheap to test before anything else (CR-2). One would quietly cripple the experiment's baseline arm and invalidate the comparison the study exists to make (CR-3).

## CR-1. Search patterns escaped the experiment sandbox (fixed on this branch)

`measurement/run.mjs`, `permission()`.

The permission callback resolved only `file_path` and `path`, defaulting to `"."`. Glob and Grep take their target in `pattern`, which was never examined. A call of the shape

~~~json
{"pattern": "/etc/**"}
~~~

resolved its candidate to the workspace, matched the workspace entry in `readable`, and was allowed. The same held for `"../../**/*.pdf"` and for a tilde-prefixed pattern. The runner therefore granted the model reads across the whole filesystem while its own denial message promised "only its frozen document inputs".

This matters beyond tidiness. Arm A is the honest-baseline arm, and the evaluation design forbids both crippling it and giving it more than a real user has. An arm that can glob the evidence root can reach `ground-truth.json`, which `prepare.py` deliberately writes outside the document grant so that trials cannot see it. A trial that reads ground truth is not a measurement.

Fix applied: bound the pattern as well as the root. A string `pattern` or `glob` is refused when it is absolute, contains a `..` segment, or starts with `~`. The root check is unchanged.

Added `tests/measurement/run.test.mjs`, "a search pattern cannot read outside the granted evidence". It drives the real `canUseTool` through `runTrial` rather than exporting the internal function, and asserts allow and deny for six shapes. With the fix removed the test fails on three of them, which is the regression evidence the contributing rules require.

Left for Codex to decide: whether Grep's `--glob` style options and any future search tool need the same treatment, and whether the deny message should name the reason so a trial transcript records why a call was refused.

## CR-2. The Desktop bundle relies on substitution in a field documented as unsubstituted

`clients/claude-desktop/manifest.json`.

The server block is:

~~~json
"mcp_config": {
  "command": "${__dirname}/server/openreading-worker",
  "args": ["--client", "claude-desktop", "--input-root", "${user_config.input_root}"]
}
~~~

The MCPB manifest reference shipped with Anthropic's own `mcp-server-dev` plugin states that the substitution variables `${__dirname}`, `${user_config.<key>}` and `${HOME}` apply "in `args` and `env` only". Every example in that reference puts a PATH executable such as `node` in `command` and the bundle-relative path in `args`. The `args` usage here is therefore on documented ground; the `command` usage is not.

If Desktop does not substitute in `command`, it will try to execute a literal path beginning with a dollar sign and the extension will fail to start. That is AC-1, the criterion the whole first proof exists to satisfy.

This was not caught by the checks already run, and it is important that the record says why. `mcpb validate` checks the manifest against its JSON schema. Substitution happens later, inside Desktop, at launch. A passing validation and a passing pack and unpack round trip are consistent with a bundle that cannot launch.

A binary bundle has no PATH executable to name, so if the reference is exact there is no in-manifest workaround and the packaging shape has to change, which is the fallback D-2 already anticipates. Resolve it by installing one bundle in Desktop and reading the launch record before any further packaging work. It is a few minutes and it gates a lot.

A note recording this has been added to the Desktop client guide.

## CR-3. The baseline command allowlist will almost never match

`measurement/prepare.py`, `allowed_bash_commands`; `measurement/run.mjs`, the Bash branch of `permission()`.

Preparation resolves `pdftotext` with `shutil.which`, then emits one exact command string per document and one per page: 155 entries for the primary corpus. The runner allows a Bash call only when `input.command` is exactly equal to one of those strings.

Three ways that fails in practice. The model is never told the allowlist exists, so it has no reason to reproduce a string verbatim. Any deviation at all, a redirect, a pipe, quoting, a different page range, or a trailing space, is a miss. The absolute `pdftotext` path is captured from the preparation machine, so preparing and running on different machines guarantees a miss.

The consequence is not a crash. It is a silent narrowing of arm A to the Read tool, which changes the number the study reports. Reading a PDF through Read sends page images, so arm A becomes the expensive arm for a reason that has nothing to do with selective retrieval. The evaluation design's own instruction is not to disable the baseline's local utilities. An allowlist that cannot match is indistinguishable from disabling them.

The measurement README already asks for a fairness review before execution, which is right, but the reader has no way to tell from the current text that the policy is close to unmatchable. Options, in increasing order of change: state the available commands in the arm A prompt; match on a parsed argv prefix rather than the whole string; or drop the page-range entries and keep whole-document extraction. Whichever is chosen, record the realized per-arm tool call counts, which T-3 already requires, and treat a zero Bash count in arm A as a failed baseline rather than a result.

## CR-4. Smaller findings

**CR-4a. Host architecture is never compared with the running machine.** `runtime/verify.py` checks that `release.json` declares `darwin` and `arm64`. It never compares that with `platform.machine()`. On the primary platform an Apple Silicon binary simply will not execute on Intel, so the practical exposure today is a confusing launch failure rather than a wrong-architecture run. C-18 was accepted, and MCPB's `compatibility` block has `platforms` but no architecture field, so the launcher is the only place the check can live. I did not add it: the natural place is `entrypoint.main`, and the Python lane runs on Linux in CI, so a host check needs its test fixtures updated at the same time. Worth doing with the C4 work rather than as a drive-by.

**CR-4b. Dependency notices are filtered by a hardcoded denylist.** `runtime/build.py`, `notices()` walks every installed distribution and skips nine names such as `pytest` and `pyinstaller`. A new development dependency lands in the shipped notices until someone adds it to the list, and a name that is both a build tool and a runtime dependency is omitted from notices that AC-19 depends on. Deriving the list from what the freeze actually collected would be sounder than maintaining a denylist by hand.

**CR-4c. Unrun rows create a phantom quality category.** `measurement/report.mjs` assigns `category: "unknown"` when a planned trial has no record, and `categoryQuality` then evaluates that category. It cannot change a verdict today, because unrun rows already fail `complete_pairs` and `complete_usage_all_arms`. It is still a category that no dataset defines, and it will read as noise in a report a reviewer has to trust. Related: T-5 was accepted and asks for four shared task kinds alongside the three document categories, and the dataset carries only `category`. The plan assigns that to M1, so it is tracked, not missing.

**CR-4d. `verify_release` verifies the whole tree on every launch.** This is the deliberate C-9 and C-15 position, and it is defensible. The cost is real though: the tree is dominated by the interpreter and native libraries, and every launch rehashes all of it. C-15's accepted disposition is to record cold start before weakening anything. That measurement is not yet in the runtime evidence table, and it belongs in the same host session as CR-2.

**CR-4e. Running from source cannot self-verify.** `entrypoint.main` derives its root from `Path(sys.executable).parent`, which is correct when frozen and points into a virtualenv otherwise, so a source run always fails integrity. The tests patch around it. That is a reasonable design, but it means the entrypoint's real launch path is exercised only by the packaged smoke, so `scripts/package_smoke.py` is carrying more weight than its coverage number suggests.

**CR-4f. The runtime guide claims a build requirement the build does not enforce.** `runtime/README.md` says the builder requires macOS 15.1. `build_runtime` checks platform, machine, and the Python patch version, and then records whatever `platform.mac_ver()` reports as `minimum_os_version`. Building on a different macOS silently produces a different declared floor. Either enforce the version or describe what the code does.

## CV. Checked and correct

Recording these so the next reviewer does not re-derive them.

**CV-1. `claude plugin install --config key=value` is real.** The flag exists in Claude Code 2.1.267 and states that values are validated against the plugin manifest's `userConfig` and stored through the same path as the interactive configure flow. The Claude Code README command and the `userConfig` block in `plugin.json` are consistent with the installed client.

**CV-2. `${user_config.input_root}` in the plugin's `.mcp.json` args is on documented ground.** The plugin reference rejects `${user_config.*}` in fields that run through a shell, because a configured value would become shell input. A stdio server's `command` and `args` are argv, not a shell string, and the reference lists `command`, `args` and `env` as substituted for stdio servers. This is the opposite of CR-2's situation and should not be changed on suspicion.

**CV-3. Corpus generation is byte-deterministic.** Two independent runs of `generate_dataset` produced identical hashes for all six files. `no_new_id=True` plus fixed metadata is doing its job, which is what T-7 asks for. The remaining T-7 work is publishing the recipe and expected hashes, not fixing nondeterminism.

**CV-4. Accounting takes the last cumulative snapshot rather than summing.** `normalizeQuery` keeps the final result event's per-model totals, counts duplicate assistant message identifiers as a diagnostic only, treats a missing cache counter or a counter rollback as incomplete, and never turns an absent measurement into zero. The fixtures the evaluation design asks for are present and pass.

**CV-5. The claim rules cannot be satisfied by a cheap wrong answer.** `buildReport` reconstructs every planned row, refuses unplanned and duplicate identities, and requires complete pairs, complete usage in all arms, a 90% quality floor, no category regression, supported citations, a median ratio at or below one half, and a lower total. The tests exercise the failure of each.

**CV-6. Live execution is gated at four independent points.** An approved manifest hash, a re-validation inside `runTrial`, an account key fingerprint match, and a client version prefix match. The dry path never imports the SDK. A stale lock, an interrupted raw log, or an unpriced trial stops scheduling rather than assuming unspent budget.

**CV-7. The subprocess environment is replaced, not inherited.** The runner passes an explicit four-variable environment. The pinned SDK's own types document that `env` replaces the subprocess environment entirely, so this is deliberate and correct, and it keeps ambient credentials out of trials.

**CV-8. Release inventory refuses the cases that matter.** Changed worker bytes, an unlisted library, a missing notice, an inventory key escaping the root, a symlink leaving the runtime, and an inconsistent worker digest are each covered by a passing test. `rglob` records symlinked directories without descending them, and the builder materializes internal links before hashing, which is the right order given that MCPB dereferences them.

**CV-9. The status labeling is honest.** Every client guide, the runtime guide, and the measurement guide open by saying they describe the superseded revision 1 prototype. `AGENTS.md` says the same. The runtime evidence table separates what passed from what remains unverified, and no document claims a token result.

## What I would do next, in order

1. Install one bundle in Desktop and settle CR-2. Record cold start and bundle size in the same session, which closes CR-4d and P-8.
2. Decide CR-3 before any paid trial. An unmatchable baseline allowlist makes the primary comparison meaningless, and it is cheaper to fix than to re-run.
3. Fold CR-4a into C4 and CR-4b into the P1 notices work.
4. Treat CR-4c and the T-5 task kinds as one change in M1.

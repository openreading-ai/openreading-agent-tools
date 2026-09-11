# Native connection and frozen-runtime probes

**Status:** proposed experiments supporting ProductSpec revision 4. No checked result is implied by this plan.
**Owners:** Agent Tools owns host probes and capture; core owns engine, evidence, and worker behavior.
**Prerequisites:** [assistant contract](assistant-clients.md) and [implementation order](implementation-plan.md).

## Shared experiment rules

E1, E2, E3, and E5 use a tiny synthetic MCP server rather than loading Docling.
It exposes `probe_echo` and `probe_delay`, plus a configurable initialization delay.
Use read-only and non-read-only probe annotations to observe approval behavior without writing user documents.
Requests carry unique nonces; a local event file records receipt, completion, progress, and cancellation with monotonic timestamps.
Record PID, parent PID/executable, probe digest, app/version/mode, and effective transport.
Collect only allowlisted synthetic arguments and environment variable names, never credential values or unrelated host configuration.
Store raw logs, configuration diffs, and transcripts privately, outside document grants and trial read permissions.

Host installation and model invocation require the owner's respective authorization.
A probe needing a chat request is not automatically free; no synthetic content bypasses account or spending approval.
Prepare configuration changes for review, preserve preexisting registrations, and restore only this experiment's changes afterward.
Do not overwrite concurrent host edits by restoring an entire stale backup.
Do not change organization policy, expose an endpoint, bypass OS protection, or use a remote executor.
If a host is unavailable to the automation tool, leave its cases pending for an owner-operated run.
Independent tasks can proceed without claiming those cases passed.

## E0. Reproducible core protocol baseline

Purpose: replace the unretained ad hoc tool-list observation with reviewable evidence.
Add a `list_tools` assertion to the existing retrieval/restart checker with a failing regression test first.
Require exactly the three selected core tools and record their schema digest, core/runtime identity, and protocol version.
Bind the retained report to its retrieval evidence as the existing checker does.
A protocol pass is not a native launch pass.
This small guard is future implementation, not part of the documentation correction.

## E1. ChatGPT mode, local route, and setup

Blocks: ChatGPT-specific N2 and AC-26. It does not block N1 or Claude Desktop.
First inspect the selected app's settings without inferring capabilities from its bundle identifier.
Test a Chat conversation, then a Work conversation only if its execution location can be established as local.
A Codex local thread is a separate developer case.
Remote or cloud tasks remain excluded; record them as out of scope rather than sending probe requests to them.

Register through the documented native Settings form and capture its actual available fields.
Record how it interprets an executable path with spaces and Unicode, whether arguments are separate, and any required environment or working directory.
Exercise the selected helper-app design using an argument-free host launcher with saved OpenReading settings.
Do not edit shared TOML to rescue a form-only check or infer absent form fields from a short documentation page.
Verify the actual configuration delta and which other local clients receive that registration.

For each mode, record tool visibility, a nonce-bearing local call, process ancestry, executable identity, and the exported answer/tool trace.
Measure both initial catalog visibility and eventual discovery after startup.
Record the default approval behavior and a separately configured `writes` probe, if that control is available.
Core import is not read-only; an approval prompt must not be bypassed or “fixed” by changing its annotation.
Capture the actual transcript/tool-log location and format needed by the deterministic citation checker.

Pass only the exact mode and setup route observed.
If only Codex local threads work, report that developer route and leave the Chat conversation goal unmet.
Do not broaden the claim to ChatGPT generally or silently change the nondeveloper persona.

## E2. Startup, tool timeout, and discovery

Blocks: supported release limits and nondeveloper setup feasibility.
Test Claude Desktop, the E1-established local mode, Claude Code, and Codex CLI separately.
Use actual default registration first; any changed timeout configuration is a different recorded route.

Probe initialization delays of 0, 0.5, 2, 5, 9, 11, 20, and 30 seconds, including the initial catalog boundary.
Probe tool delays of 30, 55, 65, 120, and 330 seconds, without progress and with progress every five seconds.
Only send progress when the caller supplied a progress token.
Stop an individual series once its relevant boundary and cleanup behavior are established; refine around that boundary rather than repeating pointless failures.
Use finite external watchdogs and asynchronous monitoring so a long probe never blocks operator control.

Record timeout error, cancellation notification, signals, surviving processes, and whether the host admits a later successful request.
Distinguish absolute deadlines, inactivity deadlines, process initialization, and initial catalog grace.
Progress does not count as extending a deadline unless the observation shows it does.
Compare the measured budgets with the engine design's 20% margin and frozen startup/import costs.
A higher configurable limit is usable only through the setup route being claimed.

## E3. Interruption paths

Blocks: the corresponding portion of AC-9 and AC-24.
During an acknowledged running 120-second delay, use the host stop action if it exists.
Record `notifications/cancelled`, process signals, elapsed cleanup time, and the process tree afterward.
If there is no stop action, record `not_exposed` and test deadline and host-process termination separately.
Never label host quit as successful protocol cancellation.

Repeat available paths against an active P0 Docling import, including setup-enabled OCR, after synthetic behavior is understood.
Confirm the operation was still running before interruption, owned children exited, and no successful artifact was published.
A race where extraction completed before the stop is inconclusive, not a cleanup pass.
Core's independent stage-cancellation tests remain required even when the host exposes fewer controls.

## E4. P0 frozen Docling feasibility

Blocks: native OpenReading N2 and later distribution. Requires no host installation or model call.
Use one development-machine candidate and the selected feasibility dependency lock.
Keep the historical PyMuPDF build and locks unchanged while evaluating a separate onedir build path.
Collect on-disk core sources, complete transitive metadata, the exact lock, verified layout assets, and Tesseract data including `configs/tsv` and required language/orientation files.
Relocate Tesseract and every dependent dynamic library; inspect actual loaded libraries and fail on accidental Homebrew dependencies.
Do not add signing entitlements, relax identity, or perform dependency substitutions to force a pass.

Run inventory verification, engine identity, initialization, and one native-text import through the frozen entrypoint.
Add one OCR-enabled synthetic import to verify relocated Tesseract rather than merely inspecting its presence.
Prove changed/missing source, metadata, lock, TSV configuration, or model files refuse before successful parsing.
Record archive/installed size, cold/warm initialization, verification time, worker spawn, import, and sampled memory.
Repeat from an unrelated working directory with developer tool paths unavailable.
This tests onedir feasibility, not a clean OS image or supported performance percentile.
Base-machine repetitions remain C1 work.

P0 is an unsigned local feasibility exception before the cheap M0 decision.
It permits no public upload, sharing with another user/machine, installer polishing, or bypass of OS protection.
If it fails, report the narrow failure before spending on N2 or signed packaging.

## E5. Claude Desktop setup form

Blocks: Claude setup translation and corresponding AC-2/AC-21 evidence.
Use a minimal local probe wrapper with a directory field and optional boolean OCR field after host-install authorization.
Record exact argument values for enabled, disabled, omitted, and cancelled setup.
Verify the launcher's closed token mapping, including refusal of unresolved placeholders or unexpected representations.
Record save/cancel behavior, executable permissions, extraction location, and actual host error/log paths.
An unsigned local wrapper is developer-only and cannot pass signing or distribution acceptance.

## E6. Codex measurement isolation and accounting

Blocks: the additional provider driver, not the Claude M0 probe.
The offline portion checks a fresh per-trial state directory, effective settings, unrelated MCP absence, and no changes to the user's shared configuration.
Do not change the parent agent's home or Codex state.
Plant recognizable instructions in otherwise excluded user/project locations to detect inherited context.
Use a separate synthetic workspace, approved tool inventory, scratch output, and sentinel files outside the intended read boundary.

The live portion requires an exact account/model, API authentication, approved finite budget, and watchdog.
Verify that attempted reads of ground truth, other extractions, earlier events, and unrelated files fail through ordinary tools, shell, and symlink paths.
A read-only sandbox that can read the evidence fails this experiment; it is not sufficient isolation.
Confirm legitimate local search and scratch-file output still work for the ordinary-tools arm.

Capture raw usage events and establish cumulative versus per-request behavior, cached-input inclusion, model rows, errors, and completeness.
Verify the authenticated account source and refusal of quota-login fallback.
Identify actual available turn/output/request controls without inventing unsupported CLI flags.
Record timeout behavior and residual in-flight billing risk; missing counters or ineffective isolation block paid studies.
Use the evaluation design's separate version 3 contracts only after these observations support an adapter.

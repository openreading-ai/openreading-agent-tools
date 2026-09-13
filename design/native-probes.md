# Native connection and frozen-runtime probes

**Status:** native experiments remain proposed under ProductSpec revision 8. E0 and the P0 developer smoke are implemented; no native-host result is implied.
**Owners:** Agent Tools owns host probes and capture; core owns engine, evidence, and worker behavior.
**Prerequisites:** [assistant contract](assistant-clients.md) and [implementation order](implementation-plan.md).

## Shared experiment rules

E1, E2, E3 and E5 use the [implemented synthetic probe](../scripts/README.md) without loading Docling.
The probe logs process identity, setup substitutions, initialization, tool discovery, progress and cancellation.
Native capture must add app/version/mode, effective transport and the host's own logs to those process observations.
Store raw logs, configuration diffs and transcripts privately, outside document grants and trial read permissions.

Host installation and model invocation require the owner's respective authorization.
Use the owner's existing Desktop app for chat requests; no provider API, SDK substitute, or separate metered study is allowed.
Prepare configuration changes for review, preserve preexisting registrations, and restore only this experiment's changes afterward.
Do not overwrite concurrent host edits by restoring an entire stale backup.
Do not change organization policy, expose an endpoint, bypass OS protection, or use a remote executor.
If a host is unavailable to the automation tool, leave its cases pending for an owner-operated run.
Independent tasks can proceed without claiming those cases passed.

## E0. Reproducible core protocol baseline

Implemented in the [retrieval/restart checker](../measurement/README.md).
Two fresh local processes passed with identical tool-schema digests and 51 exact citation reads per process.
The report records protocol/server identity and binds to the original retrieval evidence.
This is protocol evidence only; it cannot satisfy a native launch or ChatGPT mode criterion.

Revision 6 adds a separate C0 release gate comparing against the full implemented catalog from the pinned core, as described in [the launch design](oss-launch.md).
The existing three-tool snapshot must not silently exclude a future implemented core tool.

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

The [P0 builder and smoke](../runtime/p0/README.md) implement this development-machine check.
The local candidate passed frozen native/OCR imports, warm conversion, restart reuse, loaded-library inspection, relocation and ten identity-file mutation/removal cases.
Keep its raw inventory, timing and failure-injection records privately with the worker digest.
The runtime guide owns reproduction; do not treat these observations as a clean-host or percentile measurement.
Base-machine repetitions, complete phase timing, host deadlines and the release cap remain C1 work.
A P0 pass permits owner-authorized native setup checks but supplies no permission to share, install or publish a binary.

## E5. Claude Desktop setup form

Blocks: Claude setup translation and corresponding AC-2/AC-21 evidence.
Use a minimal local probe wrapper with a directory field and optional boolean OCR field after host-install authorization.
This E5 form is a developer substitution probe only. Public file selection requires A0 and cannot inherit a pass from directory setup.
Record exact argument values for enabled, disabled, omitted, and cancelled setup.
Verify the launcher's closed token mapping, including refusal of unresolved placeholders or unexpected representations.
Record save/cancel behavior, executable permissions, extraction location, and actual host error/log paths.
An unsigned local wrapper is developer-only and cannot pass signing or distribution acceptance.

## E6. Retired provider API measurement probe

The proposed Codex API authentication, isolation and spending experiment is retired.
It is not a prerequisite for packaging, native connection testing, or release.
Use E1/E2/E3/E5 for actual Desktop mode, timing, interruption and setup observations.
A future usage investigation may inspect counters exposed by the actual Desktop app, without invoking provider APIs.
Missing or incomplete counters mean token savings remain unmeasured.

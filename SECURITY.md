# Security policy

## Report a vulnerability

Send a private report to <creativeaisle@gmail.com>, the maintainer contact used by OpenReading core.
Include the affected commit or release, impact, and a synthetic reproduction.
Do not publish credentials, private documents, or an exploit against another user's machine.

## Release status

The current profile is `core-server-client-v1`, a parser-free connector for macOS Apple Silicon.
Other platforms are pending. Public alpha previews are not supported releases.
Security fixes land through reviewed pull requests and require a newly versioned build before acceptance testing.

The reviewed alpha.22 private preview has unresolved pre-launch findings. It is not the launch-test candidate.
Its distribution commit is `572d13dfafdc944eeebe4b8519edda7c43d31697`.
Its worker SHA-256 is `6777e48d1cf3bdf96cc0c6cc964fa1f814c96a17767f4f5f0193d0edd71483bc`.
Source fixes do not change that binary. Consult the [changelog](CHANGELOG.md) for subsequent candidates.

Alpha.23 is historical and is not an approved public release or launch-test candidate.
Its worker SHA-256 is `db268d52f410c663b88616f2109e30f84806e80f5e407d56cff846d2d759615b`.
It uses Python 3.11.16, OpenSSL 3.5.8, Tcl/Tk 9.0.4 and Expat 2.8.4.
Synthetic frozen-worker checks do not establish native installation, remote TLS acceptance, licensing approval or publisher authentication.
The pinned interpreter still embeds Expat 2.8.4. Upstream fixes CVE-2026-93990 in [Expat 2.8.5](https://github.com/libexpat/libexpat/releases/tag/R_2_8_5).
The connector transfers document bytes and consumes JSON, rather than parsing document XML locally.
No affected XML path is identified in that flow, but this is not independent reachability clearance.
Keep launch acceptance blocked until a patched interpreter or an independently reviewed disposition resolves this native dependency finding.

Alpha.24 source pins merged Core `9c6b8390cd341636aba8dd57c64fdb5ae0f9ad86`, including detached-job admission and abandoned-job recovery.
Its preview worker SHA-256 is `24b8f8cc9e21e1cd5086fb01a08c30fcf520402033a05e5d97c62081c5193794`.
Its isolated interpreter comes from the checksum-pinned [September 24 Astral build](https://github.com/astral-sh/python-build-standalone/releases/tag/20260924), with Expat 2.8.5.
The freezer refuses Expat versions other than that reviewed input before creating a runtime.
Python remains 3.11.16, OpenSSL remains 3.5.8, and Tcl/Tk remain 9.0.4.
The worker is rebuilt from merged Agent Tools `4110af50edb34363f21a2270e49107712cdfd30b`.
Its public distribution is `5aed913f7a8ad019b1958d22fc13f8127c8f0a49`, preserved by tag `dist-macos-arm64-alpha24`.
The [verification record](https://github.com/openreading-ai/openreading-agent-tools/blob/dist-macos-arm64-alpha24/verification.json) separates completed checks from native acceptance.
Building the replacement does not update installed plugins. The owner merges its separate catalog PR before GitHub installation tests.
Bundled component inventory, notice preservation, frozen checks and dependency audit passed before preview publication under the policy below.
Exact-build native, remote HTTPS and clean-machine acceptance still gate supported-release claims.

## Unsigned preview policy

The owner permits an Apple Silicon preview without Developer ID signing or Apple notarization.
The worker remains ad-hoc signed. This does not identify or authenticate its publisher through Apple.
This decision replaces earlier mandatory signing gates for the current server connector, not historical build records.

Before publication, review the source, bundled dependency licenses, security findings, package inventory and frozen checks.
Record the exact source and Core commits, toolchain, worker hash, notices and immutable GitHub distribution commit.
Use a new distribution version and preserve its commit with a tag. Never replace historical binaries or tags.
The owner approves publication and merges source and catalog PRs. Agents never merge or install test plugins.

Published preview packages enable owner-run GitHub installation tests; publication alone does not establish supported-client acceptance.
Record native workflows, remote HTTPS success and refusal, update behavior and clean-machine launch against those exact packages.
Keep Intel Mac, Windows and Linux pending. Do not infer support from a development-machine or another client's result.
If macOS or a host blocks launch, record the failure and stop acceptance for that route.
Never disable Gatekeeper, strip quarantine or weaken TLS checks to obtain a passing result.
Future Developer ID signing or notarization requires a separate release decision, not an undisclosed preview prerequisite.

## Current data path

The native picker copies selected files into private client storage.
The consent dialog identifies the destination and asks you to approve sending those documents.
Processing starts when the assistant invokes import after that approval.
An approval remains usable while its destination revision is unchanged; it does not currently expire by time.
Choose only documents you intend this assistant to process, including in later turns.
If any selected file exceeds the 100 MiB upload limit, the whole selection fails without uploading any file.

The connector uploads complete file bytes and filenames to your configured OpenReading Core HTTP server.
A loopback server can process locally. A remote destination receives those bytes off your machine.
Core chooses processing backends using the operator's configuration. Those backends may themselves send data to other services.
Read the [Core setup guide](https://github.com/openreading-ai/openreading-core#readme) and inspect your server configuration before selecting sensitive files.

The connector sends no authentication credentials and does not manage the server.
HTTP is accepted only for loopback destinations. Remote destinations require certificate-verified HTTPS.
Redirects and environment proxy settings are disabled.
Do not expose an unauthenticated Core endpoint to an untrusted network to accommodate this connector.
Use a loopback server or an appropriately access-controlled network. TLS alone does not authorize callers.

Complete responses, selected-file copies, artifacts, import jobs, and exports remain in your client data partition.
Private directories use mode 0700 and files use mode 0600. These permissions are not encryption at rest.
Retrieved excerpts and requested full exports reach the calling assistant and may enter a cloud model's context.
Host-created attachments and server-side data have separate retention policies.

The worker runs with your user-process permissions, not inside an operating-system sandbox.
OpenAI's manifest capability labels describe the install listing, not a filesystem sandbox or a substitute for consent.
See the [official manifest documentation](https://developers.openai.com/plugins/build/plugins).
Filesystem checks constrain the tools' intended access. They do not isolate a compromised process from your account.
Returned document fields are untrusted data. They must not authorize new selection, destination changes, or additional uploads.

Stopping a chat turn does not necessarily stop detached imports.
Cancel an import through the job tools and wait for its terminal status before removing local data.
Cancellation after submission does not prove that remote processing stopped. The connector provides no remote deletion guarantee.

## Remove retained data

Plugin replacement and removal preserve data and settings. There is no automatic retention expiry or Settings deletion button.
To remove your data safely:

1. Before uninstalling, list your imports, cancel unwanted jobs, and wait until every job is succeeded, failed, or cancelled.
   Local cancellation does not cancel or delete remote server work.
2. Record the active data location shown by OpenReading Settings.
   If a move is pending or blocked, use the location marked as still in use, not the requested destination.
   The client's `storage.json` control record, when present, records the exact partition in `active_root`. Read it without editing it.
3. Quit the relevant assistant clients and the OpenReading Settings window after jobs finish.
   If uninstalling, remove only this plugin using the host's controls.
4. Identify your client label: `chatgpt`, `codex`, `claude-code`, or `claude-desktop` for Cowork.
   Replace `CLIENT` below with that label. Confirm the location against Settings or the control record before deleting anything.
5. Move only that verified client data partition to Trash.
   Never remove the chosen parent folder, all of `~/.openreading`, or another client's partition.
6. For a full settings reset, also move only `~/Library/Application Support/OpenReading/agent-tools/CLIENT` to Trash.
   Record the data location first. This removes the destination, delivery and storage preferences and the active-location pointer.
7. Check your known previous storage locations separately. Storage moves deliberately retain the original copy.
   Remove only the corresponding client partitions you have verified, not their shared parents.
8. Remove unwanted legacy exports from `~/Downloads/OpenReading` individually.
   Host attachments, manually saved files, backups, assistant history and server copies require their own removal controls.

Possible client data locations are:

| Storage choice | Exact client partition |
| --- | --- |
| Default | `~/.openreading/clients/CLIENT/v2` |
| Application storage | `~/Library/Application Support/OpenReading/agent-tools/CLIENT/v2` |
| Custom folder | `CHOSEN_FOLDER/clients/CLIENT/v2` |

The partition contains `selection`, `server` approvals and transfer caches, `artifacts` including jobs, and current `exports`.
The control record is `~/Library/Application Support/OpenReading/agent-tools/CLIENT/storage.json`.
Application storage is inside the control directory, so removing that directory also removes its data partition.
If Settings and the control record cannot establish the active path, stop and recover that information before deleting data.

Trash remains recoverable until emptied. These steps are not a secure-erasure guarantee and do not remove remote or backup copies.

## Distribution trust

Existing preview binaries were built on a maintainer machine and are ad-hoc signed, not Developer ID signed or notarized.
The source repository is public. Historical preview availability does not establish distribution approval or current security clearance.
The [unsigned preview policy](#unsigned-preview-policy) permits owner-approved testing without Developer ID signing or notarization.
Frozen HTTPS checks and owner-operated native acceptance remain required before supported-release claims.
There is no reproducible-build guarantee or CI build attestation.
Release inventories detect changed bytes. They do not authenticate a publisher if an attacker can replace both files and their inventory.
The GitHub distribution commit and host fetch integrity are part of the trust boundary.
Dependency inventories and notices identify bundled components; the source license does not relicense those dependencies.

## Reports that matter

- Selection or consent bypass, including uploads requested by malicious document instructions.
- Destination substitution, redirect following, or TLS verification bypass.
- File access outside an approved selection or retained-artifact boundary.
- Unexpected exposure of document text, filenames, credentials, or private paths in diagnostics.
- Unauthorized access to retained copies, transfer caches, exports or import jobs.
- A package executing bytes different from its declared immutable distribution.
- Missing safety instructions or an added tool bypassing destination checks.

Model behavior, host permissions and third-party vulnerabilities may also require upstream reports.
Include how the problem affects this project's workflow. Keep private fixtures and live transcripts out of Git.

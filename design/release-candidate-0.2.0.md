# Agent-tools 0.2.0 release candidate

## Goal

Prepare reviewable release-candidate pull requests for OpenReading Core 0.3.0 and
OpenReading Agent Tools 0.2.0. The owner merges both pull requests. The release
process creates tags and binaries only from the merged immutable commits.

## Contract

- Agent Tools is open source and pins one immutable Core 0.3.0 commit.
- The first native artifacts target macOS on Apple Silicon only.
- Linux, Windows, and Intel macOS remain unsupported and are stated as pending.
- ChatGPT, Claude Desktop, Claude Code, and Codex instructions distinguish a
  development candidate from host acceptance.
- Claude Code and Codex never receive a legacy format-1 package under a current
  server-client version.
- The owner merges pull requests. This work never merges a pull request.
- Release tags are annotated and created from each repository's merged main SHA.
- Build outputs stay out of Git. A prerelease uploads artifacts, SHA256SUMS, and
  a manifest that binds agent-tools and Core tags, commits, locks, and binaries.

## Deliverables

1. Core PR #52: release-facing Core setup, version, and RC compatibility facts.
2. Agent Tools PR #6: client setup, platform scope, Core pin, and package rules.
3. Package tests proving current client wrappers use a verified format-2 or
   format-3 runtime and reject legacy format-1 runtime inputs.
4. After owner merges, annotated tags `v0.3.0-rc.1` and `v0.2.0-rc.1`.
5. After tags, fresh macOS arm64 build artifacts and their checksums.

## Implementation order

### 1. Review public documentation

Inspect Core's README, changelog, install instructions, and version surfaces.
Inspect Agent Tools' root README, client matrix, every client README, runtime
guide, manifest text, and package output. Correct contradictory or historical
instructions. State platform support before installation commands.

### 2. Bind Agent Tools to Core

Keep the runtime build pin as an exact Core commit. Add a release manifest
generator or package metadata field that reports both the selected Core tag and
commit. It must reject an unresolved `main` reference.

### 3. Package current client shapes

Package ChatGPT as its local marketplace ZIP and Claude Desktop as MCPB from a
verified runtime. Add current server-client marketplace packages for Claude Code
and Codex only after their wrappers, manifests, and tests agree on `--client`
and `--chat-documents`. Do not reuse a legacy directory-grant package.

### 4. Verify release candidates

Run Core `make verify` and Agent Tools `make verify`. Build each artifact in a
fresh output directory. Verify release inventories, package manifests, archive
integrity, executable modes, and package checksums. Run each available local
smoke test without source Python on PATH.

### 5. Owner merge and release

The owner reviews and merges PR #52 and PR #6. Confirm each branch's main SHA,
create annotated RC tags from those SHAs, then build from clean tag checkouts.
Publish only a GitHub prerelease. Mark it macOS arm64 only and list pending
platforms and host acceptance clearly.

## Review focus

- A package built from a mutable Core ref must fail before freezing.
- A non-arm64 or non-macOS host must fail before reading package inventory.
- Claude Code and Codex must reject historical format-1 runtimes.
- Every published archive must record and verify its worker hash.
- A client guide must not claim host support without that client's acceptance.

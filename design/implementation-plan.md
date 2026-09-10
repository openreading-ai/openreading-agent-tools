# Local Document Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

Agents without that skill follow the written task sequence directly.
Do not require a personal plugin or dispatch additional agents without the owner's instruction.

**Goal:** Deliver a locally installed document workflow with verifiable page references and a defensible Claude token experiment.

**Architecture:** Core owns import, retained artifacts, retrieval, and the MCP interface.
Agent Tools freezes that core build and supplies client packages, workflow instructions, and measurement drivers.
Private live evidence remains outside both OSS-ready repositories.

**Tech Stack:** Core Python and PyMuPDF, the Python MCP SDK, PyInstaller directory bundles, MCPB,
portable Agent Plugins, Node.js measurement tooling, Claude Agent SDK, pytest, and Node's test runner.

**Spec:** [ProductSpec revision 1](../product/specs/local-document-proof.product-spec.md),
[engineering design](local-document-proof.md), and [evaluation design](token-evaluation.md).

**Status:** proposed execution plan. None of the product tasks below are completed by this documentation PR.

## Global Constraints

- Primary platform is macOS on Apple Silicon.
- The first profile fixes the backend to pymupdf.
- Core owns parsing, provenance, artifact and search/read semantics, and MCP tools.
- The dependency arrow runs tools to core.
- Source bytes are limited to 25 MiB, exactly 26,214,400 bytes.
- Physical pages are limited to 100.
- Serialized extraction is limited to 64 MiB.
- Store bytes are limited to 512 MiB, including staging.
- Concurrent imports are limited to one per artifact store.
- Import wall time is limited to 45 seconds.
- Tool result payload caps are 4,096 bytes for import, 8,192 for search, and 16,384 for read.
- Query length is limited to 256 code points, search to ten hits, and read to eight evidence identifiers.
- Evidence segment text is limited to 1,024 Unicode code points.
- The runtime has no hosted fallback, URL intake, automatic OCR, or model inference.
- End users do not manage Python or start a terminal server.
- Live model calls and binary publication require their own owner authorization.
- Never merge, push to main, fabricate evidence, or skip a failing verification gate.

## 1. Worker handoff protocol

Give each worker this file, the exact ProductSpec revision, the design sections its task names, and the current commit of its repository.
Do not hand over only a task title.
The worker reads that repository's AGENTS.md and runs make sync first.

Each task handoff includes:

~~~text
Task identifier:
Repository and starting commit:
ProductSpec path and revision:
Acceptance identifiers:
Permitted file scope:
Inputs from completed tasks:
Expected output contract:
Focused test command:
Full verification command:
Stop condition:
~~~

Each completion report supplies the branch, commit, changed paths, executed tests, regression evidence, and unresolved criteria.
An interface mismatch is a reason to revise the design in review.
It is not permission to invent a parallel engine in this repository.

Review tasks in dependency order.
Only the owner merges approved PRs.
Unmerged predecessor commits can be used for local integration experiments, with their full SHA recorded.
A release pin must point to an owner-approved core revision.

## 2. Delivery order

~~~mermaid
flowchart TD
  R0[Review scope and core proposal] --> P1[Packaging feasibility]
  R0 --> C1[Core schemas and types]
  C1 --> C2[Safe import and retained artifacts]
  C2 --> C3[Bounded search and read]
  C3 --> C4[Core MCP profile]
  P1 --> P2[Freeze approved core runtime]
  C4 --> P2
  P2 --> H1[Claude Desktop acceptance]
  H1 --> H2[Claude Code and Codex packages]
  H2 --> M2[Authorized live experiment]
  M1[Offline measurement driver] --> M2
  M2 --> R1[Evidence review and handoff]
~~~

The diagram identifies dependencies, not permission to dispatch concurrent agents.
M1 can be developed against synthetic logs before the host packages exist.

| Review boundary | What is independently reviewable | Stop condition |
| --- | --- | --- |
| R0 + P1 | Narrow scope and evidence that native packaging can work. | Normal Desktop installation cannot launch the candidate runtime. |
| C1 through C4 | Generic core artifact and MCP behavior. | Schema, provenance, access, or bounded-output criteria fail. |
| P2 + H1 + H2 | Real end-user installation across the three named clients. | A claimed host needs manual Python setup or an unverified executable. |
| M1 + M2 + R1 | Valid measurement and a claim supported by evidence. | Usage is incomplete or quality/reduction rules fail. |

## 3. Task R0: reconcile the core proposal

**Repository:** core. **Criteria:** AC-4 through AC-10, AC-18.

**Files:** Read core AGENTS.md, src/openreading/api.py, types/response.py, types/blocks.py,
adapters/pymupdf/, config.py, design/agentic.md, and product/specs/agentic.product-spec.md.
Modify the existing agent proposal and its product intent to distinguish the narrow proof from remaining agent-surface work.
Add core design/local-document-artifacts.md if the retained artifact mechanism needs its own review record.
Follow core's documentation allowlist.

**Consumes:** This approved proposal and core's current schemas.
**Produces:** A reviewed core proposal that assigns every mechanism to one owner without reviving removed policy behavior.

- [ ] Inspect the current core commit and compare it to the reference commit in the engineering design.
- [ ] Record actual API, output-channel, page, and geometry contracts in the core proposal.
- [ ] Define the new artifact schemas separately from existing normalized response versions.
- [ ] Explain which parts of the older six-tool/triage proposal remain unbuilt.
- [ ] Link the Agent Tools ProductSpec revision through a durable repository URL.
- [ ] Run core's make verify and open the core proposal PR.
- [ ] Stop before implementing a conflicting public contract until the owner approves that scope.

**Commit boundary:** `docs: define local document artifact and MCP scope`.

## 4. Task P1: test packaging feasibility early

**Repository:** Agent Tools. **Criteria:** partial AC-1, AC-13, AC-19.
**Dependency:** R0 scope approved. This task is not a full product acceptance result.

**Files:**

- Create runtime/pyproject.toml, runtime/uv.lock, runtime/.python-version, runtime/README.md.
- Create runtime/openreading-worker.spec and runtime/build.py.
- Create tests/runtime/fixtures/packaging_probe.py and tests/runtime/test_freeze_probe.py.
- Extend Makefile with build dependency sync and the focused packaging test target.

**Consumes:** Core's known immutable inspection baseline and its existing Python run API.
**Produces:** A disposable native MCPB feasibility artifact and a recorded dependency inventory.

The probe exposes only a development-only health operation and exercises core's PyMuPDF import against a synthetic fixture.
It is a test fixture, not a second product MCP implementation.
Remove it from the release assembly once C4 supplies the actual entrypoint.

- [ ] Add a failing packaging test that launches the frozen probe with PATH restricted to operating-system commands.

~~~python
def test_frozen_probe_needs_no_user_python(frozen_probe, clean_process_env):
    result = subprocess.run(
        [str(frozen_probe), "--self-check"],
        env=clean_process_env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["backend_id"] == "pymupdf"
    assert report["schema_loaded"] is True
    assert report["synthetic_page_count"] == 1
~~~

- [ ] Run `uv run --project runtime pytest tests/runtime/test_freeze_probe.py -q`; expect failure because the frozen artifact does not exist.
- [ ] Resolve a core-compatible Python patch version, PyInstaller version, and MCP SDK version, then record exact versions in the lock and runtime/.python-version.
- [ ] Set runtime/.python-version to that exact patch and include its interpreter identity in the build inventory; reject an unrecorded interpreter.
- [ ] Build directory mode with source and native dependencies pinned; include the vendored core schemas explicitly.
- [ ] Make --self-check construct one in-memory synthetic PDF, call core, and report only the fields asserted above.
- [ ] Run the test until it passes with no inherited Python, uv, pip, or development-library path.
- [ ] Package the probe as a binary MCPB and test normal installation on a fresh macOS user or clean test machine.
- [ ] Record architecture, OS/client version, quarantine state, signing state, install steps, and failure codes in private run evidence.
- [ ] Record the dependency license inventory for the owner's distribution review.
- [ ] Stop this packaging approach if normal host installation requires a security bypass or a user-managed interpreter.

**Fixtures:** frozen_probe is the path produced by the build recipe.
clean_process_env copies only required OS variables, supplies a temporary home/data directory, and sets PATH to /usr/bin:/bin.
Neither fixture reads a developer virtualenv.
Development tools may exist on the builder; the separate clean-host check supplies installation evidence.

**Commit boundary:** `build: prove native runtime assembly on macOS`.

## 5. Task C1: define artifact schemas and projection types

**Repository:** core. **Criteria:** AC-5, AC-6, AC-7.
**Dependency:** R0.

**Files:**

- Create schemas/local-document.v1.json, schemas/passage.v1.json, and schemas/agent-document-tool.v1.json.
- Create `artifacts/__init__.py`, artifacts/models.py, artifacts/limits.py, and artifacts/README.md under src/openreading/.
- Add tests/test_artifact_schemas.py and tests/test_artifact_passages.py.
- Update schemas/README.md, `schemas/__init__.py`, src/openreading/README.md, AGENTS.md, and CHANGELOG.md.

**Consumes:** NormalizedResponse, Page, Block, and the contracts in engineering sections 6 through 10.
**Produces:** Versioned JSON schemas and typed values with no IO.

Define these internal types in artifacts/models.py:

~~~python
@dataclass(frozen=True)
class ProfileConfig:
    input_root: Path
    artifact_root: Path
    limits: ProfileLimits

@dataclass(frozen=True)
class EngineIdentity:
    core_commit: str
    core_version: str
    backend_id: str
    backend_version: str
    extraction_settings: dict[str, object]
~~~

ProfileLimits contains the exact constants in this plan's Global Constraints.
ArtifactManifest, Passage, ImportReceipt, SearchResult, ReadResult, and ToolError are strict Pydantic mirrors of their new schemas.
Their fields and cursor semantics are defined in engineering sections 7 through 10.
Use NormalizedResponse only as the source model; never change its historical schema pins to fit these types.

- [ ] Write schema failures for missing hashes, page zero, unknown fields, excessive limits, and an evidence span inconsistent with its text.
- [ ] Write a projection test using two pages with repeated identical blocks and one absent bbox.

~~~python
def test_passages_preserve_page_and_absent_geometry():
    response = response_with_blocks(
        [(4, "Repeated clause"), (13, "Repeated clause")],
    )
    passages = list(iter_passages(response))
    assert [p.page for p in passages] == [4, 13]
    assert len({p.evidence_id for p in passages}) == 2
    assert "bbox" not in passages[0].model_dump(exclude_none=True)
~~~

- [ ] Run `uv run pytest tests/test_artifact_schemas.py tests/test_artifact_passages.py -q`; expect missing-schema/type failures.
- [ ] Implement `iter_passages(response: NormalizedResponse) -> Iterator[Passage]` in artifacts/models.py.
- [ ] Add response_with_blocks as a test helper constructing the existing normalized response with the requested one-based pages, one text block per row, and no invented geometry.
- [ ] Test Unicode offsets, block ordering, duplicate text, empty pages, segment boundaries, and complete reconstruction of block text.
- [ ] Add explicit maximum lengths and closed objects to input and result schemas.
- [ ] Run the focused tests and core's make verify.

**Commit boundary:** `feat: define local document artifact contracts`.

## 6. Task C2: implement safe import and durable artifacts

**Repository:** core. **Criteria:** AC-3, AC-4, AC-5, AC-8, AC-9, AC-10.
**Dependency:** C1.

**Files:**

- Create artifacts/intake.py, artifacts/store.py, artifacts/worker.py, and artifacts/service.py.
- Create adapters/pymupdf/intake.py for bounded PDF preflight.
- Add tests/test_artifact_intake.py, tests/test_artifact_store.py, and tests/test_artifact_worker.py.
- Add shared synthetic factories in tests/artifact_fixtures.py.
- Update package docstrings, applicable README files, and CHANGELOG.md.

**Consumes:** ProfileConfig, ProfileLimits, EngineIdentity, and the artifact types from C1.
**Produces:** `ArtifactService(config: ProfileConfig)` with `import_document(path: str) -> ImportReceipt`
and `load_artifact(artifact_id: str) -> ArtifactManifest`.
The service owns process launch, store locking, staging, deadline enforcement, and grant checks.
All failures raise `ArtifactError(code: str, message: str, retryable: bool)` from artifacts/models.py.

The worker entry point is `openreading.artifacts.worker.main(argv: list[str] | None = None) -> int`.
Its command contract is an internal --job-file argument pointing to a parent-created bounded job description.
That description names the staging file, engine identity, result path, and fixed profile.
It contains no model-provided executable or arbitrary backend.
Use the same entry point through a --internal-artifact-worker dispatch in the frozen runtime.

- [ ] Add make_pdf(path, pages, text_by_page) in tests/artifact_fixtures.py using PyMuPDF to create synthetic text at a fixed page position.
- [ ] Add make_service(input_root, artifact_root, limits=None) returning ArtifactService with explicit ProfileConfig and default ProfileLimits when limits is omitted.
- [ ] Write the safe-path test before intake code.

~~~python
def test_symlink_escape_is_refused(tmp_path):
    input_root = tmp_path / "input"
    input_root.mkdir()
    outside = tmp_path / "outside.pdf"
    make_pdf(outside, pages=1, text_by_page={1: "Outside secret"})
    (input_root / "link.pdf").symlink_to(outside)
    service = make_service(input_root, tmp_path / "store")
    with pytest.raises(ArtifactError) as error:
        service.import_document("link.pdf")
    assert error.value.code == "access_denied"
    assert "Outside secret" not in str(error.value)
~~~

- [ ] Run `uv run pytest tests/test_artifact_intake.py -q`; expect the missing import service to fail.
- [ ] Implement descriptor-relative, no-follow file access and metered staging from engineering section 5.
- [ ] Add one-byte-over-cap, directory, FIFO, absolute-path, traversal, changed-source, and symlink-component tests.
- [ ] Add preflight_pdf(path: Path) -> int inside the PyMuPDF adapter helper; prove it refuses encrypted and over-page-limit inputs before full extraction.
- [ ] Assert the native document is a PDF before returning its physical page count; test a renamed non-PDF input.
- [ ] Use core's explicit API call below, with an empty supplied configuration and no discovered strategy.

~~~python
response = openreading.run(
    str(staged_source),
    backend="pymupdf",
    config={},
    output={
        "text": True,
        "blocks": True,
        "markdown": False,
        "include_backend_raw": False,
    },
)
~~~

- [ ] Verify the exact request fields against the current vendored schema before using that call.
- [ ] Plant an ambient hosted-backend configuration and credentials in a fixture; assert no hosted adapter is invoked.
- [ ] Implement the parent-owned worker deadline, cancellation signal, process-group cleanup, and nonblocking import lock.
- [ ] Implement metered serialization, checksums, per-grant storage, and atomic commit.
- [ ] Write restart, corruption, incomplete staging, cache reuse, changed bytes, new grant, full disk, and quota tests.
- [ ] Inject a worker hang and parser crash; assert sanitized failure, no committed partial artifact, and no surviving worker.
- [ ] Run `uv run pytest tests/test_artifact_intake.py tests/test_artifact_store.py tests/test_artifact_worker.py -q`.
- [ ] Run core's make verify before committing.

**Important seam:** parent-generated job descriptions are local process messages, not MCP tool inputs.
The subprocess must work under both a source Python interpreter and the frozen executable.
P2 tests that packaging seam with the real worker.

**Commit boundary:** `feat: retain bounded local document artifacts`.

## 7. Task C3: implement bounded search and read

**Repository:** core. **Criteria:** AC-6, AC-7, AC-8, AC-10.
**Dependency:** C2.

**Files:** Create artifacts/search.py, artifacts/cursors.py, and artifacts/projection.py.
Extend artifacts/service.py and its package documentation.
Add tests/test_artifact_search.py and tests/test_artifact_read.py.

**Consumes:** Stored Passage rows and load_artifact from C2.
**Produces:**

~~~python
ArtifactService.search(
    artifact_id: str, query: str, limit: int = 5,
    cursor: str | None = None,
) -> SearchResult

ArtifactService.read(
    artifact_id: str, evidence_ids: list[str],
    cursor: str | None = None,
) -> ReadResult
~~~

The result types follow engineering section 9 exactly.
They do not return local filesystem paths or invoke a parser.

- [ ] Write a retrieval test whose target sentence is on physical page 13.

~~~python
def test_search_then_read_preserves_source_page(service_with_agreement):
    service, receipt = service_with_agreement
    hits = service.search(receipt.artifact_id, "renewal notice")
    match = next(hit for hit in hits.hits if hit.page == 13)
    result = service.read(receipt.artifact_id, [match.evidence_id])
    assert result.passages[0].page == 13
    assert "60 days" in result.passages[0].text
    assert result.passages[0].evidence_id == match.evidence_id
~~~

- [ ] Define service_with_agreement using C2's helpers with 24 pages and the renewal sentence only on page 13.
- [ ] Run `uv run pytest tests/test_artifact_search.py tests/test_artifact_read.py -q`; expect missing search/read failures.
- [ ] Implement the declared lexical tokenization, ranking, and literal excerpt window.
- [ ] Implement bounded cursors with artifact/query/identifier binding and explicit continuation.
- [ ] Test punctuation-only queries, duplicate terms, Unicode casefold, equal-score ordering, malformed cursors, changed queries, and invalid IDs.
- [ ] Test JSON escaping and Unicode near each byte cap; assert complete valid payloads without lost evidence.
- [ ] Patch the parser call to fail if invoked, then prove search/read use only the retained artifact.
- [ ] Run focused tests and core's make verify.

**Commit boundary:** `feat: search and read bounded document evidence`.

## 8. Task C4: expose the core MCP profile

**Repository:** core. **Criteria:** AC-2, AC-4, AC-6, AC-10, AC-11, AC-18.
**Dependency:** C3.

**Files:**

- Create `mcp_server/__init__.py`, mcp_server/main.py, mcp_server/tools.py, and mcp_server/README.md.
- Modify cli/app.py, `cli/__init__.py`, cli/help.py, pyproject.toml, uv.lock, and the schema/package guide indexes.
- Add tests/test_mcp_document_tools.py and tests/test_mcp_stdio.py.
- Update .env.example only if an environment variable is actually introduced.

**Consumes:** ArtifactService from C2/C3 and the closed tool schemas from C1.
**Produces:** `openreading mcp`, the three declared tools, and
`openreading.mcp_server.main.main(argv: list[str] | None = None) -> int`.

The main function dispatches --internal-artifact-worker to the core worker entrypoint when launched by the trusted parent.
That internal mode is never an MCP tool.
Otherwise it validates the required profile and roots before starting stdio.
Offload blocking service operations through a cancellation-aware boundary.
Cancellation must terminate the import process rather than only cancel its awaiting coroutine.

- [ ] Add a black-box stdio test against the proposed executable.

~~~python
async def test_stdio_receipt_contains_no_document_text(mcp_client):
    tools = await mcp_client.list_tools()
    assert {tool.name for tool in tools.tools} == {
        "openreading_import", "openreading_search", "openreading_read",
    }
    result = await mcp_client.call_tool(
        "openreading_import", {"path": "agreement.pdf"},
    )
    assert len(result.content) == 1
    payload = json.loads(result.content[0].text)
    assert payload["page_count"] == 24
    assert "60 days" not in result.content[0].text
~~~

- [ ] Implement mcp_client as a test fixture using the pinned MCP SDK stdio client, explicit temporary roots, and C2's synthetic PDF.
- [ ] Run `uv run pytest tests/test_mcp_document_tools.py tests/test_mcp_stdio.py -q`; expect missing command/server failures.
- [ ] Add the optional agent extra and exactly the declared tool/input schemas and annotations.
- [ ] Return one validated JSON text block and map ArtifactError to the declared isError envelope.
- [ ] Test stdout purity, malformed requests, root changes, disconnect, cancellation, restart, secret redaction, and bounded errors.
- [ ] Add the required CLI help chapter, TOPICS row, flag help, examples, exits, and package index updates.
- [ ] Run the focused tests, CLI help checks, and core's make verify.
- [ ] Reconcile the older agent proposal; delete only completed design scope and preserve the explicitly unbuilt remainder.

**Commit boundary:** `feat: expose local document retrieval over MCP`.

## 9. Task P2: freeze the approved engine

**Repository:** Agent Tools. **Criteria:** AC-9, AC-13, AC-18, AC-19.
**Dependencies:** P1 and C4.

**Files:** Create runtime/entrypoint.py, runtime/release.schema.json, and runtime/verify.py.
Update the build recipe and lock from P1.
Add tests/runtime/test_release_integrity.py and tests/runtime/test_frozen_mcp.py.
Update runtime/README.md and Makefile.

**Consumes:** The full SHA of the owner-approved C4 core revision.
**Produces:** A directory bundle containing the real core worker and release.json with exact hashes.

runtime/entrypoint.py delegates to core's main function.
It contains no document behavior.
The build tool exposes `build_runtime(output_dir: Path) -> Path`, returning the assembled release directory.
The verifier exposes `verify_release(root: Path) -> dict[str, object]`, returning validated release metadata or raising an integrity error.

- [ ] Write the integrity regression before implementing the verifier.

~~~python
def test_modified_worker_is_refused(assembled_release):
    worker = assembled_release / "server" / "openreading-worker"
    worker.write_bytes(worker.read_bytes() + b"modified")
    with pytest.raises(ReleaseIntegrityError):
        verify_release(assembled_release)
~~~

- [ ] Run `uv run --project runtime pytest tests/runtime/test_release_integrity.py -q`; expect missing verifier failure.
- [ ] Replace the baseline core pin with the approved immutable revision; update the complete lock.
- [ ] Freeze the actual entrypoint and collect native libraries, schemas, licenses, and the internal subprocess mode.
- [ ] Generate release.json from observed build inputs instead of manually typed version strings.
- [ ] Check each declared file's length, executable bit, hash, platform, and core/schema compatibility before launch.
- [ ] Keep the trust distinction between a checksum and publisher authentication in runtime/README.md.
- [ ] Run the C4 import/search/read transcript through the frozen binary with no developer PATH.
- [ ] Verify a 45-second worker timeout still terminates the frozen child process.
- [ ] Add these offline checks to make verify, using a documented build prerequisite for the native artifact lane.
- [ ] Add a measured coverage threshold for newly shipped Python behavior; keep the normal repository gate runnable without a sibling checkout.
- [ ] Run make verify and the native packaging lane before committing.

Native build tests need their own named lane because Linux documentation CI cannot execute a macOS artifact.
Portable unit tests belong in make verify.
The native release lane builds the artifact from locked inputs and records installation evidence.

**Commit boundary:** `build: package the pinned OpenReading worker`.

## 10. Task H1: complete Claude Desktop installation

**Repository:** Agent Tools. **Criteria:** AC-1, AC-2, AC-11, AC-14.
**Dependency:** P2.

**Files:** Create clients/claude-desktop/manifest.json and README.md.
Add scripts/package-clients.py and tests/clients/test_desktop_manifest.py.
Update package/build locks for the exact MCPB validator and packer.

**Consumes:** Verified release directory and engineering section 12.
**Produces:** A versioned macOS arm64 MCPB with required directory configuration and the real core tool list.

- [ ] Write a manifest test before adding the descriptor.

~~~python
def test_desktop_bundle_requires_an_input_grant(desktop_manifest):
    assert desktop_manifest["server"]["type"] == "binary"
    grant = desktop_manifest["user_config"]["input_root"]
    assert grant["type"] == "directory"
    assert grant["required"] is True
    assert "default" not in grant
~~~

- [ ] Run `uv run --project runtime pytest tests/clients/test_desktop_manifest.py -q`; expect missing manifest failure.
- [ ] Create the manifest using the official schema and pinned validator.
- [ ] Assemble the verified runtime without user-specific paths or developer environment files.
- [ ] Test denied setup, a read-only input root, spaces, Unicode, missing source, and an invalid architecture.
- [ ] Install the downloaded quarantined artifact on the clean test host.
- [ ] Record actual time to a first cited answer; do not promise an installation duration from this one observation.
- [ ] Test process restart, bundle update, source edit, input grant change, and artifact corruption.
- [ ] Test uninstall and manual artifact deletion; document the actual retained-data behavior.
- [ ] Record the tested minimum OS/client combination and feed that floor back into the release metadata and build.
- [ ] Run make verify and retain the real-host evidence in the private run record.

**Stop condition:** no normal, successful, no-interpreter Desktop install means AC-1 remains unverified or failed.

**Commit boundary:** `feat: package the Claude Desktop document workflow`.

## 11. Task H2: package coding clients and workflow skill

**Repository:** Agent Tools. **Criteria:** AC-11, AC-12, AC-14.
**Dependency:** H1.

**Files:** Create the Claude Code and Codex client files listed in engineering section 3.
Create skills/read-local-document/SKILL.md.
Extend scripts/package-clients.py with local marketplace distributions.
Add tests/clients/test_coding_manifests.py and tests/clients/test_skill_contract.py.

**Consumes:** The same verified runtime bytes used by H1 and engineering sections 12 and 13.
**Produces:** Two locally installable client distributions and one concise shared skill.

- [ ] Write a consistency test that fails until all packages reference the same runtime hash.

~~~python
def test_client_packages_use_identical_runtime(client_release_metadata):
    hashes = {
        metadata["worker_sha256"]
        for metadata in client_release_metadata.values()
    }
    assert len(hashes) == 1
    assert set(client_release_metadata) == {
        "claude-desktop", "claude-code", "codex",
    }
~~~

- [ ] Run `uv run --project runtime pytest tests/clients/test_coding_manifests.py -q`; expect missing coding-client metadata.
- [ ] Create the Claude plugin manifest and MCP configuration using client-root-relative executable paths.
- [ ] Create the portable Codex plugin.json and explicit-transport mcp.json.
- [ ] Generate local marketplace catalogs during packaging, with validated paths to the packaged plugin.
- [ ] Validate each generated package using the schema and commands supported by the exact test client.
- [ ] Write the shared skill with the eight-step retrieval procedure and six-call guidance ceiling from engineering section 13.
- [ ] Add synthetic transcripts exercising supported facts, unknown answers, malicious document instructions, and requests outside the input grant.
- [ ] Test actual install/load, disabled-plugin behavior, restart, update, and removal in both coding clients.
- [ ] Record exact commands and client versions in each README only after they succeed.
- [ ] Confirm that neither package assumes the user installed Python, npm, uv, or a developer checkout.
- [ ] Run focused tests and make verify.

Skill tests should check declared tool names, bounded workflow instructions, and transcript outcomes.
Do not claim an instruction string test proves the model will follow it.
The real-host synthetic transcripts supply that separate evidence.

**Commit boundary:** `feat: add Claude Code and Codex document packages`.

## 12. Task M1: implement offline measurement and the explicit live driver

**Repository:** Agent Tools. **Criteria:** AC-15, AC-16, AC-17, AC-18.
**Dependency:** Approved evaluation design; no host package is required for synthetic accounting tests.

**Files:**

- Create measurement/README.md, manifest.schema.json, trial.schema.json, accounting.mjs, report.mjs, and run.mjs.
- Create tests/measurement/accounting.test.mjs, report.test.mjs, and run.test.mjs.
- Add synthetic log fixtures beneath tests/measurement/fixtures/.
- Add the exact Claude Agent SDK and JSON Schema validator versions to package.json and package-lock.json when their code is added.
- Extend make verify with the measurement test suite and static checks for the JavaScript modules.

**Consumes:** Evaluation sections 5 through 9.
**Produces:**

~~~typescript
normalizeQuery(events: unknown[]): QueryUsage
buildReport(manifest: TrialManifest, trials: TrialRecord[]): ProofReport
validateRun(manifestPath: string, approvedHash?: string): ValidatedRun
runTrial(run: ValidatedRun, task: TrialTask): Promise<TrialRecord>
~~~

Define QueryUsage as usage_status, per_model rows with the four disjoint token categories,
input_total, output_total, all_tokens, and estimated_cost_usd.
TrialManifest and TrialRecord mirror their closed JSON Schemas.
TrialTask is task_id, repetition, arm, prompt, and the registered input projection.
ValidatedRun adds the verified manifest hash, schedule, remaining limits, and approved evidence root.
ProofReport contains planned/completed/quality/usage counts, per-arm totals, paired rows, claim_allowed, and refusal_reasons.

- [ ] Write the cumulative-count regression first.

~~~javascript
test('one query uses its final total without summing snapshots', () => {
  const events = [
    resultEvent({ input: 100, output: 4 }),
    resultEvent({ input: 150, output: 8 }),
  ];
  const usage = normalizeQuery(events);
  assert.equal(usage.input_total, 150);
  assert.equal(usage.output_total, 8);
});
~~~

resultEvent is a fixture factory producing the pinned SDK's actual result shape with one model,
zero cache fields by default, and supplied final counts.
It lives in tests/measurement/fixtures/events.mjs and never represents a real model call.

- [ ] Run `node --test tests/measurement/accounting.test.mjs`; expect the missing accounting module to fail.
- [ ] Implement final whole-tree normalization, duplicate diagnostics, cache categories, and incomplete crash handling.
- [ ] Add every accounting fixture from evaluation section 9.
- [ ] Implement the claim rules and paired report before adding live execution.
- [ ] Add a quality-regression fixture where C is cheaper but wrong; assert claim_allowed is false.
- [ ] Implement manifest/path/hash validation, frozen scheduling, and the no-network dry-run path.
- [ ] Inject a fake SDK query function in run.test.mjs; assert no call occurs without both live authorization flags.
- [ ] Implement the single-input SDK driver with explicit per-trial limits, a remaining study budget, and no reset commands.
- [ ] Capture failure records, partial usage, and redacted public projections without discarding raw private evidence.
- [ ] Run `node --test tests/measurement/*.test.mjs` and make verify.

No live request is necessary to complete this task.
The test injection seam is a function argument on the runner's internal execute method.
Production defaults to the pinned SDK query function.
It never accepts an executable or function body from the manifest.

**Commit boundary:** `feat: measure paired document workflow usage`.

## 13. Task M2: run the authorized experiment

**Repository:** Private company evidence store, using Agent Tools' tested driver.
**Criteria:** AC-16, AC-17, EVAL-1, EVAL-2.
**Dependencies:** H2's Claude Code checks and M1, plus explicit owner authorization for the exact live manifest.
Codex compatibility can be completed after this Claude experiment.
It does not block the first measured demonstration, although AC-12 still requires both coding clients before the whole milestone is complete.

**Inputs:** Real tested bundle, frozen synthetic corpus, reviewed ground truth, and the account/spend authorization.
**Outputs:** Immutable evidence pack, quality review, normalized records, and generated claim decision.
This task commits no raw model transcript to either OSS-ready repository.

- [ ] Generate the three synthetic documents and twelve task categories from the evaluation design.
- [ ] Freeze their byte hashes, expected answers, required qualifiers, and physical evidence locations.
- [ ] Inventory the actual ordinary tools before comparing them to the plugin.
- [ ] Validate a calibration manifest with twelve trials and print its no-network schedule.
- [ ] Obtain approval of that concrete manifest, account label, and estimated spend ceiling.
- [ ] Run calibration and repair instrumentation before freezing the primary manifest.
- [ ] Obtain approval for the separate 108-trial primary manifest.
- [ ] Run the primary schedule with one trial at a time and preserve all outcomes.
- [ ] Have the human reviewer grade answers without arm labels.
- [ ] Generate the report directly from schema-valid records.
- [ ] Apply every quality and reduction condition, including unfavorable and incomplete pairs.
- [ ] Record the functional outcome even if the token hypothesis fails.

**Future command contract:**

~~~sh
node measurement/run.mjs --manifest /path/to/approved/manifest.json --dry-run
node measurement/run.mjs --manifest /path/to/approved/manifest.json --live --approved-manifest-sha256 APPROVED_SHA256
~~~

The paths and hash above are caller inputs, not values to hard-code.
The driver must derive the hash and show it before authorization.
No invocation of this proposed command occurs during specification work.

## 14. Task R1: review evidence and finish the implementation

**Repository:** Agent Tools, with corresponding core documentation cleanup.
**Criteria:** AC-19, AC-20 and all remaining acceptance evidence.
**Dependencies:** Completed implementation tasks, host evidence, and an honest experiment report.

- [ ] Fill the criterion matrix below with actual test and review links.
- [ ] Keep failed or unverified criteria explicit; do not label the overall proof complete while required evidence is missing.
- [ ] Review bundle licensing, source availability obligations, notices, hashes, signing, and the quarantined install record before distribution.
- [ ] Produce a sanitized public proof summary without private data or raw transcripts.
- [ ] Describe only the tested clients, profile limits, supported workflow, and measured result.
- [ ] Update the root README and client walkthroughs with commands and outputs actually observed.
- [ ] Coordinate any website tutorial update through the website repository's own rules.
- [ ] Move durable implementation facts into source, command help, and directory READMEs.
- [ ] Remove completed proposal records in the finishing PR and retain separate records for unfinished scope.
- [ ] Run make verify, the native package lane, and the documented compatibility checks.
- [ ] Open reviewable PRs and report the release decision needed from the owner.
- [ ] Stop. Do not merge, tag, upload a release, or publish a marketing claim.

## 15. Acceptance and evidence mapping

| Criterion | Build tasks | Required evidence |
| --- | --- | --- |
| AC-1 | P1, P2, H1 | Quarantined clean-host Desktop install and cited answer. |
| AC-2 | C4, H1 | Setup cancellation/configuration tests and disclosure review. |
| AC-3 | C2 | Descriptor-relative file and symlink adversarial tests. |
| AC-4 | C2, C4 | Explicit backend and ambient-configuration isolation tests. |
| AC-5 | C1, C2 | Identity, source hash, version, and deterministic evidence tests. |
| AC-6 | C1, C3, C4 | Valid JSON caps and cursor continuation tests. |
| AC-7 | C1, C3 | Physical page, text-span, geometry omission, and citation checks. |
| AC-8 | C2, C3 | Restart, corruption, partial-write, and source-change tests. |
| AC-9 | C2, P2 | All limit boundaries and frozen-worker termination. |
| AC-10 | C2, C3, C4 | Refusal matrix, secret redaction, and cleanup tests. |
| AC-11 | C4, H1, H2, M2 | Instructions plus real synthetic client transcripts. |
| AC-12 | H2 | Separate actual Claude Code and Codex install/load records. |
| AC-13 | P1, P2 | Lock, inventory, hashes, modified-binary failure, and compatibility tests. |
| AC-14 | H1, H2 | Host lifecycle and path edge-case records. |
| AC-15 | M1 | Frozen-manifest, no-live-without-authorization, and accounting fixtures. |
| AC-16 | M1, M2 | Complete trial inventory and generated report. |
| AC-17 | M1, M2 | Claim-rule tests and actual paired quality/usage results. |
| AC-18 | C1 through C4, P2, M1 | Offline repository gates and meaningful measured coverage. |
| AC-19 | P1, P2, R1 | Maintainer distribution license review and complete notices. |
| AC-20 | R1 | Reviewed walkthrough, public evidence projection, and proposal cleanup. |
| EVAL-1 | H1, H2, M2 | Supported answer, scoped refusal, and injection transcripts. |
| EVAL-2 | M2 | Blind quality reviews against registered task ground truth. |
| SM-1 through SM-3 | Post-proof owner pilot | Five opt-in user observations in the private company repository. |

## 16. Final worker checklist

- [ ] Every new public interface matches a core schema or a versioned packaging/measurement schema.
- [ ] Every implementation task has a focused failing test and a passing relevant gate.
- [ ] No client silently changes parser, output limits, or evidence semantics.
- [ ] No private document or transcript entered a public-ready commit.
- [ ] Every compatibility and token statement has observed evidence or is labeled unverified.
- [ ] Every changed proposal revision is reflected in downstream task and trial records.
- [ ] The owner receives concrete branches, PRs, verification output, and the remaining release decision.

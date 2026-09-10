# Claude design review dispositions

Source: `origin/review/claude-design-review` at `c24258b28aaa02e5fe8ae002883a2fb4ee78dc6a`, `design/claude-review.md`.
The review was read without switching or merging branches.
The review describes a proposal and records the owner's Docling decision; it is not a review of the current code.
This pass updates [ProductSpec revision 2](../product/specs/local-document-proof.product-spec.md), the [engine design](local-document-proof.md), the [evaluation design](token-evaluation.md), and the [plan](implementation-plan.md).

**Accepted** means incorporated into the proposed contract, not implemented or empirically proven.
**Preserved** means the current conservative behavior remains the design choice.
**Deferred** names a later gate or revision and does not block this documentation pass.
Delete this disposition record when the corresponding migration finishes and durable facts live beside code.

## Decisions and contracts

| Finding | Disposition and concrete resolution |
| --- | --- |
| D-1 | Accepted. M0 precedes further packaging; null controls and price-weighted diagnostics complement the unchanged primary input measure. Add the C-beats-A-only interpretation. |
| D-2 | Accepted with a different explicit fallback. Developer ID, hardened runtime, notarization, entitlements, quarantine, and first-launch checks gate distribution. Use a signed app/installer containing the same engines if MCPB layout fails; otherwise block release. |
| D-3 | Superseded by the recorded owner decision. Exclude PyMuPDF from the new bundle without making a blanket legal determination about all combinations or transitive dependencies. |
| D-4 | Accepted with existing-code context. Claude Code's explicit installation configuration already connects successfully; Codex already persists a grant through setup. Specify both, add OCR configuration, and retain fail-closed startup. |
| D-5 | Accepted. Add frozen realistic corpus/query fixtures, a top-five supporting-page gate, offset-preserving search dehyphenation, and retriever identity before paid trials. |
| C-1 | Accepted. Retrieval limits belong in tool descriptions; remove the contradictory receipt promise from the spec. |
| C-2 | Preserved first alternative. Invalid or absent setup exits nonzero before tool registration. No promise of a tool-level error when tools are unavailable. |
| C-3 | Accepted. Add OS-permission errors and observed host-specific recovery guidance, without claiming every permission denial is a macOS privacy prompt. |
| C-4 | Accepted. Resolve the selected root once, bind the opened canonical directory, and continue rejecting links beneath it. |
| C-5 | Accepted. Compare directory identities and ancestor identities, preserve filesystem case behavior, and use OS-resolved spelling. Add APFS alias and case-sensitive-volume coverage. |
| C-6 | Partially implemented already. Core currently uses nonblocking final opens and `fstat`; preserve that and explicitly test descriptor inheritance and immediate FIFO refusal. |
| C-7 | Accepted and extended to the selected engine. The parent never loads native parsing/inference bindings; prove this independently of child behavior. |
| C-8 | Accepted with a narrower claim. A sampled process-tree RSS watchdog terminates excess usage but cannot guarantee a hard memory ceiling or prevent allocation bursts. Thresholds require measurement. |
| C-9 | Deferred until profiling. Keep full artifact verification; selective verification requires a dependency proof that source identity and derived passages remain consistent. |
| C-10 | Rejected for this revision. Keep strict atomic read and use returned identifiers; teaching guessed neighbor IDs weakens the exact-evidence contract. Page-scoped navigation remains later scope. |
| C-11 | Accepted. Match host-qualified tool names by purpose and verify observed names in client evidence. |
| C-12 | Accepted consciously. Retain the exact source snapshot; disclose the original plus an additional copy and separately account for extraction and staging. |
| C-13 | Accepted via narrower wording. Promise survival of process restart, not power-loss durability. No unconditional full-flush claim. |
| C-14 | Rejected for this revision. Keep copy-and-hash through one descriptor; a second pass over a mutable path complicates exact-byte identity. Revisit only with measured reuse cost and a race-safe proof. |
| C-15 | Measurement accepted; lazy verification deferred. Record cold-start hashing cost before weakening startup integrity checks. |
| C-16 | Accepted. Desktop may omit displayed IDs while the grading record resolves exact quotes; coding clients retain explicit IDs. Ambiguous resolution fails. |
| C-17 | Accepted; current retention guide already names cleanup directories. Keep inaccessible grants in quota accounting and point recovery at the client retention guide. |
| C-18 | Accepted. Refuse unsupported architecture before document access; distinguish installation rejection from launcher failure according to tested host capability. |

## Experiment and process

| Finding | Disposition and concrete resolution |
| --- | --- |
| T-1 | Accepted. Normalize citations and randomize answer IDs for grading; retain a private reversible mapping and disclose partial blinding. |
| T-2 | Accepted. Separate PDF representation benefits from selective retrieval, and verify pinned PDF behavior before estimating arm A costs. |
| T-3 | Accepted. Record per-tool calls and C adherence, preserve mixed-access trials, and report their fraction. |
| T-4 | Accepted. Derive the primary budget from calibration and compare it with worst-case schedule ceilings. Underfunded or incomplete schedules cannot support a scored claim. |
| T-5 | Accepted. Freeze separate document categories and four shared task kinds; require no quality regression on either grouping. |
| T-6 | Accepted. Record effective SDK plugin configuration. The current inline Claude Code configuration was connection-tested, but that is not proof of model adherence. |
| T-7 | Accepted. Keep synthetic generator, rubric, queries, toolchain, and expected hashes public; prove deterministic bytes and isolate ground truth from the live grant. |
| T-8 | Accepted. Preregister a separately budgeted cumulative follow-up outcome with its own claim wording; never relabel first-use results. |
| P-1 | Already implemented. `make sync` installs the pinned Python toolchain and both locks; `make verify` runs Python and Node coverage. `npm run verify` remains the Node-only gate. |
| P-2 | Accepted. Use a snapshotted clean macOS VM, not a fresh developer-machine user account. Execution remains deferred. |
| P-3 | Accepted. M0 is an unscored nine-trial developer-harness probe requiring separate account, hash, and budget approval. No paid call runs in this pass. |
| P-4 | Accepted as H1 evidence. Record actual host log locations after observation; do not invent paths from memory. |
| P-5 | Accepted. The plan references the engine design for resource decisions and does not duplicate a limits table. |
| P-6 | Partially implemented. The synthetic generator exists; C3 replaces its PyMuPDF dependency and adds deterministic public hashes and extraction realism. |
| P-7 | Accepted as a named fallback. Plain Codex MCP registration is a different integration claim, not evidence that plugins work. |
| P-8 | Accepted. Later package evidence records compressed/installed size, extraction/download time, startup time, and host size restrictions. |
| P-9 | Accepted. Restricted PATH alone does not exclude the Python shim; observe child executable identities and the clean VM's developer-tool state. |

## Optional suggestions and Docling findings

| Finding | Disposition and concrete resolution |
| --- | --- |
| S-1 | Deferred to a later navigation revision unless the recall gate establishes a need for bounded outlines. |
| S-2 | Definition/payload token measurement accepted for M0/M1. Removing response fields is deferred until measurements justify a versioned schema change. |
| S-3 | Accepted with D-5. Freeze retriever identity in artifacts and experiments. |
| S-4 | Deferred. Retain strict identifier-based reads; do not widen the schema without a demonstrated navigation need. |
| S-5 | Accepted. Public fallback wording promises local processing and verifiable citations only when those checks pass, without claiming token savings. |
| S-6 | Accepted. Ask for missing filenames and forbid discovery through guessed import paths. |
| DC-1 | Candidate license inventory only. Verify the exact dependency, weight, and data set before distribution; permissive top-level names do not complete that review. |
| DC-2 | Accepted. Add `docling_local` in core; leave the existing HTTP adapter separate. Map every provenance entry without inventing page attribution. |
| DC-3 | Feasibility requirement accepted. Prove the selected ONNX/preprocessing path with torch absent and network blocked; do not assume current upstream defaults. |
| DC-4 | Measurement requirement accepted. Upstream timings cannot determine local host limits; measure cold/warm tails and host deadlines. |
| DC-5 | Measurement requirement accepted. Wheel-size estimates are not installed-bundle evidence. |
| DC-6 | Superseded by DC-7, not adopted as a competing backend decision. |
| DC-7 | Owner engine choice incorporated into revision 2. Setup-only Tesseract, no table structure, local weights, no prohibited payload, warm supervision, and OCR provenance are explicit. |

## Questions resolved or assigned

| Question | Decision or remaining evidence |
| --- | --- |
| Q-1 | A negative token outcome is acceptable, consistent with the existing ProductSpec. M0 precedes further packaging investment. |
| Q-2 | Signing identity is a mandatory later distribution dependency. Availability is not assumed and is not requested during this design pass. |
| Q-3 | Resolved by the recorded decision: no PyMuPDF in the distributed bundle. |
| Q-4 | Keep the source snapshot for exact-byte verification, with explicit copy and retention disclosure. |
| Q-5 | Model and account remain fields in a separately approved live manifest; this pass selects neither and spends nothing. |
| Q-6 | Keep explicit Claude Code installation configuration and Codex's persisted setup command. No implicit project-directory grant. |
| Q-7 | One Docling profile initially. A text-only profile requires measured necessity and a separate owner decision. |
| Q-8 | OCR changes through setup only, disabled by default. |
| Q-9 | Derive the supported cap and deadline from cold/warm timing and the strictest tested host budget; do not choose minutes or inherit 45 seconds without evidence. |
| Q-10 | Table structure stays disabled. Preserve measurable table text or disclose its absence; no automatic torch inclusion. |

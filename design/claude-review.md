# Claude review of the local document proof proposal

**Reviewed revision:** main at commit `e36ff04`: ProductSpec revision 1, the engineering design, the token evaluation design, and the implementation plan, all dated 2026-09-10.
**Reviewer:** Claude, acting as an independent reviewer of a proposal drafted with Codex.
**Status:** review record, not a proposal. It changes no existing file. Codex or the owner decides which items to adopt.

This file lives under `design/` because the repository check rejects Markdown at the repository root that is not a named policy file. Delete it once its accepted items land in the spec, design, or plan.

Item identifiers are stable so a reply can address each one: D for decisions the owner should make before implementation, C for contract corrections, T for the token experiment, P for plan and process, S for optional additions, Q for questions. A useful reply marks each item accepted, rejected with a reason, or deferred to a named revision.

Related records: [ProductSpec](../product/specs/local-document-proof.product-spec.md), [engineering design](local-document-proof.md), [token evaluation](token-evaluation.md), [implementation plan](implementation-plan.md), [AGENTS.md](../AGENTS.md).

## Summary

The proposal is unusually careful about what it does not claim, and its safety and provenance rules are sound. The ownership split, the staged-copy hashing, descriptor-relative file access, the one-block JSON results, the sanitized error table, cursors instead of sliced JSON, and the preregistered experiment are all right and should stay.

Five things need a decision before anyone starts P1 or C1:

1. The token hypothesis is likely to fail on the 24-page document as the experiment is currently scored, for reasons unrelated to retrieval quality (D-1). A cheap probe should run before the packaging investment.
2. Distribution needs notarization, not only signing. That pulls in an Apple Developer Program membership, hardened-runtime entitlements for every native binary in the PyInstaller tree, and a real chance that the packaging decision changes (D-2).
3. Bundling PyMuPDF would have made the distributed bundle AGPL. Resolved on 2026-09-10: PyMuPDF is out, and the bundle is Docling with pypdfium2 and Tesseract, all permissively licensed (Decision log, DC-7).
4. Coding clients have no directory picker, and the design does not say how their input root gets configured (D-4).
5. The lexical retriever has no offline quality gate. Paid trials could end up measuring hyphenation handling instead of the hypothesis (D-5).

Everything else is a contract detail or a plan gap that can be fixed in place.

## Decision log

**2026-09-10, owner:** PyMuPDF is not bundled. The bundle is Docling, with pypdfium2 as Docling's own PDF backend, and Tesseract for OCR. The source repositories stay Apache-2.0. Every component in the bundle is permissively licensed. The concrete profile and the edits it requires are in DC-7.

Items that decision changes:

- D-3 is resolved. The AGPL question no longer exists for the bundle.
- DC-6 is superseded. Docling is the first backend, not the second. DC-2 through DC-5 still describe what that costs.
- C-7 generalizes: the MCP parent never loads Docling, onnxruntime, PDFium, or Tesseract.
- C-8 becomes mandatory. A resident layout model puts the worker in the gigabyte range.
- D-2 grows: the notarization surface now includes onnxruntime, PDFium, Tesseract, Leptonica, and their image libraries.
- D-5 is partly eased. Docling merges lines into paragraphs and orders them, which removes some hyphenation and block-boundary failures. The recall check is still required.
- Q-3 is answered. New questions Q-7 through Q-10 replace it.

## Overall assessment

The proposal is generally good. Its structure is right: outcomes in the spec, interfaces in the design, order in the plan, truth rules at the boundary, and a measurement design that cannot be gamed by dropping unfavorable rows. Most items in this review are in-place corrections that fit inside the existing tasks.

The major items, in the order they block work:

1. ProductSpec revision 2 for the engine change. The scope list, the product summary, AC-4, and AC-9 name PyMuPDF or exclude Docling and local models. Nothing downstream can be pinned to revision 1 once the bundle changes.
2. Signing and notarization as a release prerequisite with a chosen fallback (D-2).
3. Import time on the Docling path against host tool-call timeouts, which decides the page cap, the deadline, and whether a text-only profile is needed (DC-7, Q-7 and Q-9).
4. The coding-client input root mechanism (D-4).
5. The token experiment's expected outcome on short documents and the cheap probe that tests it before packaging (D-1, P-3).

The rest can be folded into C1 through C4, M1, and H1 as those tasks are written.

## The objective as this review understands it

OpenReading core parses documents locally. This repository packages that engine so a person using Claude Desktop, Claude Code, or Codex can install it without managing Python, point it at one directory, import one PDF at a time, and get answers whose quotes resolve to a physical PDF page and an exact extracted span. A separate, preregistered experiment in Claude Code tests whether selective retrieval from a retained local extraction lowers total input tokens against two baselines at equal answer quality. Installation success, citation validity, and token reduction are measured separately and none is inferred from another.

If that reading is wrong, the items below that depend on it are D-1, D-5, and T-1 through T-8.

## D. Decisions before implementation

### D-1. The experiment as scored penalizes multi-turn workflows on small documents

Where: token evaluation sections 6 and 8; AC-17.

Every model turn in Claude Code re-sends the whole conversation: the system prompt, tool definitions, skill text, and every earlier tool result. `input_total` counts cache reads at full weight. The volume measure for arm C is therefore close to:

~~~text
turns_C * (fixed_overhead_per_turn + accumulated_context)
~~~

The fixed overhead per turn in Claude Code is on the order of ten thousand tokens or more. Arm C needs four to six turns for import, search, read, and the answer. Arm B pastes a 24-page extraction, roughly twelve thousand tokens, once, and answers in one or two turns. Arm A reads the PDF through the host's Read tool in ranges of at most twenty pages, and each page enters the model as extracted text plus a page image, which makes A expensive per page. The likely ordering on the 24-page document is B below C, with A near C. On the 80-page document C probably beats both. That is a legitimate result, but the owner should expect it now rather than after spending the trial budget.

Suggested changes:

- Keep `input_total` as the primary measure, since it is the most conservative choice, but preregister a secondary cost-weighted measure using the provider's published relative prices for uncached input, cache writes, cache reads, and output. Users pay that number, and it is the one a multi-turn workflow can win.
- Add a null task to the calibration pilot: the same three arm configurations answering a question that needs no document. Its usage is the fixed overhead per arm and lets the report separate tool-definition cost from retrieval cost.
- Add the outcome row "C saves against A but not against B" to the interpretation table. It is the most likely result on short documents, and its honest statement is that extraction, not selective retrieval, produced the savings.
- Run M0 (see P-3), an unscored probe with the developer harness on the synthetic corpus, before P1. If C loses to B on every document under fifty pages, change the product story to installability plus verifiable citations before the packaging work starts (see S-5).

Confirm the per-page cost model for native PDF input against the pinned provider documentation and a token-count probe before freezing arm A's expectations. This review states it from memory, not from a test.

### D-2. Distribution needs notarization, and the plan should say what happens when it fails

Where: engineering design section 11; plan tasks P1 and H1; AC-1.

Gatekeeper on current macOS refuses browser-downloaded executables that are not signed with a Developer ID and notarized. macOS 15 removed the Control-click bypass, so a pilot user cannot work around a refusal without a trip to System Settings, which AC-1 rightly forbids counting as success. Consequences the design does not yet state:

- An Apple Developer Program membership and a Developer ID certificate are release prerequisites. The Open Questions list treats a signing identity as conditional. It is not conditional for a downloaded binary.
- Notarization requires the hardened runtime and a valid signature on every native binary in the PyInstaller directory: the launcher, the Python shared library, every extension module, and every MuPDF and dependency library. Some Python extension modules need entitlements such as allowing unsigned executable memory or disabling library validation. P1 must record which entitlements were required, because each one weakens the hardened runtime.
- A notarization ticket can be stapled to an app bundle, a disk image, or an installer package, not to loose executables inside a zip. Gatekeeper then validates the ticket online at first launch. Record whether first launch on the clean host needed network access and what happens offline.
- Whether Claude Desktop preserves the quarantine attribute and executable bits when it extracts an MCPB is host behavior that P1 has to observe, not assume. Record it either way.

If notarizing the PyInstaller tree turns out to be fragile, the fallback candidates in order of least change are MCPB's host-managed Python mode, which the design already names, and a pure-Python backend (D-3), which removes most native libraries from the signing surface. Add that decision rule to P1's stop condition so a failure produces a chosen fallback, not only a recorded failure.

### D-3. Bundling PyMuPDF makes the bundle AGPL unless a commercial license is bought (resolved, see DC-7)

Where: engineering design section 11; AC-19; ProductSpec Product Summary.

Apache-2.0 wrapper source combined with an AGPL parser produces a distributed bundle whose effective license is AGPL. That means a complete corresponding source offer for the bundle, notices, and a decision about whether the company is comfortable shipping AGPL software to pilot users. The design places a review checkpoint here, which is right, but the checkpoint sits after the packaging work.

Decide before P1, because the backend choice also drives packaging effort. Options:

1. Accept AGPL for the proof and write the source offer into the client README.
2. Buy the Artifex commercial license.
3. Switch the first backend to a permissively licensed PDF engine. The core adapter catalog has none in-process today, so this means a new core adapter either way (DC-2). A PDFium-based backend keeps native code but avoids AGPL. A pure-Python backend such as pdfminer.six is slower and weaker on layout, but it makes PyInstaller assembly and notarization far simpler and removes the AGPL question entirely.

The proof's PDF profile, text-bearing PDFs of at most 100 pages with no OCR, is exactly the profile where a simpler engine is adequate. Option 3 is worth an hour of measurement on the synthetic corpus before the decision. The owner asked whether Docling could be that backend; the Docling check section (DC-1 to DC-6) answers it.

### D-4. Coding clients have no way to receive the input root

Where: engineering design sections 4 and 12; AC-2 and AC-12.

Section 4 requires the three profile arguments and forbids a default grant and any use of the current working directory. Section 12 says the Claude Code launcher "passes the separately configured absolute input root" without saying where that configuration comes from. Claude Code plugins and Codex plugins have no directory picker equivalent to MCPB `user_config`.

Pick one mechanism and document it beside its reader with unset and invalid behavior tests, as AGENTS.md already requires for configuration:

- An environment variable declared in the plugin's MCP configuration. Simple, but the user sets it in a shell profile, which is a developer step.
- A per-installation configuration file under the OpenReading application support directory, written by a documented setup command shipped with the plugin. This keeps parity with the Desktop setup dialog and keeps the choice outside the model conversation.
- The project directory as the grant for coding clients, passed explicitly by the launcher. This is what a coding-agent user expects, but it contradicts section 4 and widens the grant to whatever directory the agent was launched in.

This review recommends the configuration file. Whatever is chosen, AC-2 needs a coding-client interpretation, because "setup asks for a directory" cannot be literally true there.

### D-5. Retrieval quality needs an offline gate before paid trials

Where: engineering design section 9 (search); token evaluation section 3; AC-17.

The search contract is OR matching over casefolded tokens, ranked by distinct matched terms and then position. It has no stemming, no stopword handling, and no treatment of PDF line breaks. Two concrete failure modes:

- Hyphenated line breaks. Justified PDF text routinely stores "renew-" at the end of one line and "al" at the start of the next inside one block. The design forbids text normalization, which is correct for stored spans, but the search-side token stream can join a hyphen plus line break with the following lowercase continuation while keeping the original offsets of the merged token. That is deterministic and offset-preserving. Without it, a query for "renewal" misses the passage.
- Common-term flooding. "What is the notice period" yields the terms "notice" and "period", which match dozens of passages in an agreement. Ties resolve by page order, so the top five hits can all come from the definitions section.

Suggested changes:

1. Add an offline retrieval check to M1 or a new task: for every registered task, with two or three plain-language queries per task written before trials, assert that a supporting passage appears in the top five hits. Ship it as a public test over the synthetic corpus. If it fails, fix the retriever before spending trial budget.
2. Add search-side dehyphenation as described, with a test containing a hyphenated line break.
3. Make the ranking function a named, versioned component such as `lexical-v1`, recorded in the artifact manifest and the trial manifest, so a later ranking change is visible in evidence.
4. Make the synthetic corpus realistic for extraction: hyphenated line breaks, one two-column page, running headers and footers whose printed page labels differ from physical page numbers, ligatures, and a table with a footnote. The documents should be hard in the ways real PDFs are hard, not only in the ways the questions are hard.

Deterministic inverse-document-frequency weighting over passages is a cheap next step if recall is still poor. It needs no model call and stays within the design's no-inference rule.

## C. Contract corrections

### C-1. The spec promises retrieval limits in the receipt and the design omits them

ProductSpec user experience step 6 says the assistant receives "retrieval limits" with the receipt. The import result in engineering section 9 has no limits field. Resolve it in favor of the design: put the limits in the tool descriptions, which the model sees once per conversation, rather than in every receipt.

### C-2. Startup behavior with missing roots is ambiguous

Section 4 says the server exposes tools only after validation succeeds. Section 10 lists `configuration_required` as a tool error for missing roots. A tool cannot return an error if it is not exposed. Choose one:

- Exit non-zero at startup with a stderr code. The host shows a generic server failure and the model sees nothing.
- Start, register the three tools, and return `configuration_required` from each until configuration is valid. The model can tell the user what to do.

The second is more useful for a Desktop user and costs nothing in security, since no root is granted. Restate AC-2's "cancellation leaves the document tools unconfigured" in terms of the chosen behavior.

### C-3. Operating-system permission denial needs its own error

On macOS, reading from Desktop, Documents, Downloads, iCloud Drive, or removable volumes requires a privacy permission granted to the responsible application, which for a Desktop-launched server is Claude Desktop itself. The first read either triggers a system prompt or fails with a permission error. Mapping that to `access_denied`, whose message says to choose a file inside the configured directory, sends the user the wrong way, and mapping it to `parse_failed` hides it. Add a distinct code such as `os_permission_denied` with recovery text naming the Files and Folders setting, and add it to the H1 test list. A pilot user's document directory is very likely to be one of those folders.

### C-4. Rejecting symlinks in the configured root path breaks common macOS layouts

Section 5 rejects any symlink in either configured root path. Users routinely have a Documents folder that is a symlink into a sync service, and anything under `/tmp` or `/var` sits behind a symlink on macOS. The security goal is to bind the grant to the directory the user chose. Resolving the chosen root once at startup, hashing the resolved canonical path as the grant, and then refusing symlinks beneath it meets that goal without failing setup for those users. Keep the rejection of symlinks inside the grant as written.

### C-5. Case and normalization insensitivity affect grant identity and overlap checks

APFS is case-insensitive and normalization-insensitive by default. Two spellings of the same directory produce two grant hashes, and the equal-or-overlapping-root check misses case variants if it compares strings. Derive the canonical path from the opened root descriptor (macOS has a fcntl that returns the path for a descriptor), compare roots by device and inode along the ancestor chain rather than by string, and record `display_name` from the directory entry the OS actually matched rather than from the caller's spelling.

### C-6. Opening a FIFO blocks until the deadline

Section 5 rejects FIFOs, but a read-only open of a FIFO blocks until a writer appears. Without care, a FIFO in the input directory costs a full 45-second timeout instead of an immediate refusal. Open each final component with no-follow, non-blocking, and close-on-exec flags, `fstat` the descriptor, require a regular file, and only then clear the non-blocking flag before copying.

### C-7. The parent process must never load the PDF library

The limits table already places page preflight in the worker. State the rule directly: the MCP parent never imports an engine. With the Docling profile that means Docling, onnxruntime, PDFium, and Tesseract. Native library output and crashes then cannot reach the MCP stdout stream or take down the server, and the parent's memory stays small. Add a test that patches the binding import in the parent and asserts it never triggers.

### C-8. Memory has no enforcement, and macOS does not honor the usual limits

The design is honest that process separation is not a memory limit. macOS does not reliably enforce address-space or resident-set rlimits, so one page with pathological content can still exhaust memory. A parent-side watchdog that samples the worker's resident set and kills the process group above a documented ceiling, for example 1 GiB, is cheap and testable with a synthetic allocation in the worker. Give it its own error code rather than reporting it as `parse_failed`, because the recovery differs.

### C-9. Full integrity verification on every search and read is expensive

Section 7 verifies every listed file hash on every artifact load. Search and read only need `passages.jsonl`. Hashing a 25 MiB source snapshot and a large `response.json` on every call adds latency to exactly the calls the experiment times. Verify the files an operation reads on that operation, and verify everything on import reuse. The corruption-detection property is preserved for the bytes actually used.

### C-10. Read should return partial results with an explicit missing list

Section 9 fails an entire read when one identifier is unknown. Evidence identifiers are deterministic, and the most useful thing a model can do after a hit is read the neighboring blocks on the same page. If it guesses one identifier past the end of a page, the whole call fails and one of its six calls is gone. Return the passages that exist plus a `missing_evidence_ids` array, and document neighbor identifier construction in the skill. If the owner prefers strictness, the alternative is a page-scoped read mode (S-4).

### C-11. Hosts prefix MCP tool names

Claude Code presents MCP tools with a server-qualified prefix, so the model never sees the bare name `openreading_import`. Skill text and transcript tests should refer to tools by purpose or by the host-presented name observed in H2, and the skill contract test should not assert that bare names appear verbatim in a transcript.

### C-12. The retained source snapshot is a second copy of the document

Section 5 retains the source bytes beside the extraction so page references survive edits to the original. That doubles store consumption against the 512 MiB quota and places a second copy of a possibly sensitive document in a location the user did not choose, disclosed at setup. Since an edited original produces a different hash and a new artifact anyway, the snapshot's remaining value is letting the user open the exact bytes that were parsed. Decide consciously whether that is worth the cost for the proof. If it stays, the quota accounting and the setup disclosure should say "two copies".

### C-13. Durability claims on macOS need a full flush

`fsync` on macOS does not guarantee that data reached stable storage; a separate fcntl does. Either use it for artifact commit or soften the durability wording to "survives process restart", which is what AC-8 actually tests.

### C-14. Re-import can skip the staging copy when the artifact exists

A hash-only pass over the source establishes whether an artifact already exists for the current grant. Copying to staging is only needed when it does not. This halves the work for the common case where a new chat re-imports a known file.

### C-15. Startup self-verification hashes the whole runtime

Section 11 verifies all declared files before the first tool becomes available. For a runtime of a hundred megabytes or more, that adds measurable cold start on every launch. Record cold start in the compatibility record as planned, and if it matters, verify the launcher, worker, and native libraries at startup and the remainder lazily.

### C-16. Evidence identifiers in Desktop answers

The expected answer shape shows an evidence identifier. It is essential in the measurement lane, where automated citation checks resolve it, and noise for a pilot user who wants a filename, a page, and a quote. Make identifier display required in the coding-client skill and optional in the Desktop instructions, and let EVAL-1's check resolve quotes to identifiers server-side when an answer omits them.

### C-17. Store quota includes artifacts of inaccessible grants

Artifacts are stored per grant hash, and a root change makes old artifacts inaccessible but still counted against the store limit. There is no list or delete tool, by design. Document the manual cleanup path in the client README and make the `storage_limit` recovery text point at that documented location by name rather than by path.

### C-18. Architecture refusal is a launch failure, not an install refusal

The ProductSpec says an unsupported architecture produces an installation error before document access. Unless the MCPB manifest can express a CPU architecture restriction, an Intel Mac installs the bundle and then fails to launch the binary. Check the manifest capability in P1 and word the expectation to match what the host can do.

## T. Token experiment

### T-1. Blind grading is broken by citation format

Arm C answers carry evidence identifiers, arm B answers carry page markers, and arm A answers carry page numbers. A grader sees the arm immediately. Normalize answers before grading by replacing identifiers with resolved page numbers and stripping tool-specific phrasing, and say in the report that blinding is partial where normalization cannot hide the arm.

### T-2. State arm A's expected strategy and cost model up front

Claude Code reads a PDF through its Read tool in page ranges of at most twenty pages, and each page enters the model as text plus a page image. That makes A expensive per page and means the headline C-versus-A number mixes two effects: text extraction versus page images, and selective retrieval versus full text. B isolates the first effect. Write that decomposition into section 2 so the report cannot present the whole difference as a retrieval result.

### T-3. Record plugin adherence in arm C

If arm C keeps the ordinary tools beside the plugin, which is what a real user gets, the model may read the PDF directly and ignore the plugin. Add per-tool call counts to the trial record and report the fraction of C trials that used only the plugin for document access. Low adherence is a finding about the skill, not about retrieval.

### T-4. The primary budget does not cover the registered schedule

108 trials at the proposed 2.00 per-trial ceiling exceeds the 100.00 total. The total ceiling binds, and if it stops the schedule early, rule 1 fails and no claim is possible. Derive the primary ceiling from calibration observations per arm and document, with margin, and name the model before estimating. An 80-page document read as page images can cost more than a dollar in a single A trial on a large model.

### T-5. Rule 3's "task category" needs a definition

The task table gives each document its own four category names. Rule 3 compares pass counts per category. Say whether categories are the twelve document-specific ones or four shared kinds (single fact, cross-page, missing fact, comparison), and record the mapping in the dataset manifest.

### T-6. The SDK configuration must mirror the plugin

The runner uses one Agent SDK query per trial. If the SDK cannot load the plugin as a plugin, arm C will be configured as an MCP server plus appended instructions, which is not exactly what a Claude Code user installs. Record the effective configuration and its difference from the H2 package in the manifest, and state it in the report.

### T-7. Keep the corpus and ground truth public and reproducible

Section 3 keeps public fixtures synthetic and section 10 promises public reproduction material, but M2 generates the documents in the private evidence store. Put the generator, the frozen hashes, the questions, and the ground truth in this repository. Generate the PDFs deterministically by fixing the document identifier, creation date, and producer fields, or the hashes will not be stable across runs. Only transcripts, raw usage logs, and reviewer notes need to be private.

### T-8. The follow-up study is where the design should expect to win

First-question cost in arm C includes import, which is pure overhead relative to B. The multi-question session reuses the artifact and is the workload the product is for. Promote the follow-up study's cumulative result to a preregistered secondary outcome with its own claim wording rather than leaving it as an afterthought.

## P. Plan and process

### P-1. The verification gate is about to need Python

AGENTS.md and the README say contributors need Node and that `make verify` is offline after `make sync`. Tasks P1, P2, H1, and H2 add pytest lanes under `tests/`. Decide now whether `make sync` installs a pinned Python toolchain, or whether Python tests live in a separate named lane that CI runs when the toolchain is present. Update AGENTS.md and the README in the same PR that adds the first pytest file, and keep the Node gate runnable on its own.

### P-2. Use a virtual machine as the clean host

A fresh user account on a developer machine still sees the developer's global tools and does not reproduce a pilot user's first launch. A macOS virtual machine on Apple Silicon can be snapshotted and its image identity recorded in the compatibility record. Name that as the clean-host method in P1 and H1.

### P-3. Add M0, a probe before packaging

The ProductSpec allows a skill that shells out to an installed Python as an internal harness. Use it for an unscored, budget-capped probe of the three arms on the synthetic corpus before P1. Its output is a go or no-go on the token claim and a first look at retriever recall, not evidence for any criterion. It costs a few dollars and can save the signing and notarization work if the product story has to change.

### P-4. Name the host log locations

Bug reports ask for sanitized error codes, and the server writes bounded diagnostics to stderr. Each client README should say where that host stores MCP server logs, recorded after H1 and H2 observe it.

### P-5. Limits are defined twice

The plan's Global Constraints restate the design's limits table. AGENTS.md says the design defines interfaces once. Replace the restatement with a link, or the two will drift.

### P-6. Add a corpus generator task

Nothing in the plan produces the synthetic corpus as a repository fixture. Add it as part of M1 or as its own task, with the determinism requirements from T-7 and the realism requirements from D-5.

### P-7. Codex packaging may fall back to plain MCP registration

If the tested Codex version does not load the plugin format, registering the server in the user's Codex configuration is the fallback. That is a different install claim and should be recorded as such, not as plugin support.

### P-8. Record bundle size and extraction time

A PyInstaller tree with the interpreter, the PDF engine, and a validation library will be on the order of a hundred megabytes or more. Record the size, download time, and extraction time in the compatibility record, and check whether the hosts impose limits on bundle or marketplace archive size.

### P-9. The restricted PATH still contains a Python shim

P1's clean process environment sets PATH to `/usr/bin:/bin`, and `/usr/bin/python3` exists on macOS as a shim that offers to install developer tools. The frozen binary must never invoke it. Have the packaging test assert that no child process named `python3` starts, and have the clean-host record state whether developer tools were installed.

## S. Optional additions

### S-1. Expose the PDF outline

PDF bookmarks are physical-page-anchored provenance established by the backend, which satisfies the truth rules. A bounded outline of titles and physical pages, capped in count, in the import receipt or behind a small optional field would let the model navigate a 48-page manual or an 80-page report without guessing search terms. It needs its own cap and a "no outline" state. Worth considering for the second revision if D-5's recall check shows navigation failures.

### S-2. Token diet for results and definitions

Every byte in a tool result is re-sent on every later turn of the conversation, so result verbosity has an outsized effect on `input_total`. Drop the `query` echo, omit empty `warnings`, keep `matched_terms` because it helps the model judge relevance, and measure the token cost of the three tool definitions and the skill text with the provider's token-count endpoint as a diagnostic in M1.

### S-3. Versioned ranking identity

Record the ranking function name in the artifact manifest and the trial manifest so a retriever change between calibration and primary is visible.

### S-4. Page-scoped read

A read mode that takes a physical page and returns its passages under the same cursor rules would make "read the page around this hit" one call with no guessed identifiers. It widens the read schema, so it belongs in a later revision unless C-10's partial result is rejected.

### S-5. Decide the fallback product story now

Installability plus verifiable citations is a real outcome even if input tokens do not fall. Write the exact public sentence for that outcome next to the token-claim sentence, so the report has language ready for the likely case and nobody is tempted to soften a negative result.

### S-6. Tell the model to ask for the filename

There is no listing tool, by design. The Desktop instructions and the skill should say that the model asks the user for the file name when it is not stated rather than guessing paths, and never enumerates the directory by trial imports.

## Docling check

Requested by the owner on 2026-09-10: could the first backend be Docling instead of PyMuPDF? Facts below come from PyPI metadata, the Docling repository at its current main branch, the Docling technical report, the Hugging Face model repositories, and the core adapter sources on GitHub. Versions checked: docling 2.126.0, docling-ibm-models 4.0.2, docling-parse 7.19.0, pypdfium2 5.13.0, onnxruntime 1.30.0, torch 2.14.0. Nothing was executed.

### DC-1. Licenses are not the problem

| Component | License |
| --- | --- |
| docling, docling-slim, docling-parse, docling-ibm-models | MIT |
| Layout Heron weights, PyTorch and ONNX variants | Apache-2.0 |
| TableFormer weights | CDLA-Permissive-2.0 and Apache-2.0 |
| onnxruntime | MIT |
| torch | Apache-2.0 with bundled third-party notices |
| pypdfium2 with PDFium | Apache-2.0 or BSD-3-Clause; PDFium is BSD-style |
| PyMuPDF, per the core adapter catalog | AGPL-3.0 |

Docling resolves D-3. So does pypdfium2, which is also one of Docling's own PDF backends.

### DC-2. Core has no in-process Docling adapter today

Core's `docling` adapter is an HTTP client for a self-hosted docling-serve container, configured through `DOCLING_SERVE_URL`. It never imports Docling. The adapter catalog lists it as "Local", which means a local container, not an in-process library. Its provenance mapping reads only the first `prov` entry and defaults a missing page number to 1, which is the caveat engineering section 8 already records.

Consequences:

- Bundling Docling in the proof means a new in-process Docling adapter in core, owned by core, before C2 can start. That is the same size of core change as adding a pypdfium2 adapter.
- Bundling docling-serve instead would add the second local service that the design's transport decision explicitly avoids.
- The in-process adapter must map every `prov` entry of an item, not only the first, or cross-page items lose pages.

### DC-3. The PDF pipeline cannot run without the layout model

Docling's standard PDF pipeline always constructs a layout model; the pipeline options have no switch to disable it. Table structure and OCR are optional, and their heavy imports are lazy, so `do_table_structure=False` and `do_ocr=False` avoid TableFormer and OCR entirely. Reading order is rule-based inside Docling and needs no model.

Two inference paths exist for the default Layout Heron model, an RT-DETR detector with a ResNet-50 backbone:

| Path | Runtime dependency | Weights | Notes |
| --- | --- | --- | --- |
| Transformers, the default | torch, torchvision, transformers, docling-ibm-models | `docling-project/docling-layout-heron`, 172 MB safetensors | The torch macOS arm64 wheel is 127 MB compressed and several times that installed. MPS acceleration is available. |
| ONNX Runtime | onnxruntime, plus transformers for image preprocessing only | `docling-project/docling-layout-heron-onnx`, 171 MB | The onnxruntime macOS arm64 wheel is 22 MB. Providers are CPU and CUDA only, so no Core ML or MPS. |

The ONNX path is the only one that fits a bundle. Two things about it are unverified and need a run in P1. The engine still imports `transformers` for its image processor, and that package is not part of the `models-onnxruntime` extra, so it must be added explicitly. The shared vision helper also references torch dynamically in two value-conversion helpers, and this review could not confirm from source alone what happens when torch is absent.

Docling downloads weights from Hugging Face on first use. A bundle must prefetch them at build time with `docling-tools models download` and point the pipeline at them through `artifacts_path`, and the setup disclosure must say that a local vision model is included. The ProductSpec currently excludes Docling and any local model from the proof, so this is a scope change, not a configuration choice.

### DC-4. Speed and limits

Docling technical report figures for full PDF conversion with tables on and OCR off, PyTorch path:

| Hardware | Median per page | Mean per page | 95th percentile per page |
| --- | --- | --- | --- |
| Apple M3 Max | 0.32 s | 1.26 s | 6.48 s |
| x86 CPU, 8 threads | 0.79 s | 3.1 s | 16.3 s |

Layout alone costs 271 ms per page on the M3 Max with MPS. The ONNX path runs on CPU, and a pilot user's base M-series chip is slower than an M3 Max, so per-page cost on that path is unknown until measured. Against the design's limits:

- The 45-second import deadline cannot hold for 100 pages. At the report's median, 100 pages take about 32 seconds on the fastest tested Mac, and the tail runs to minutes. Docling needs a deadline near five minutes or a page cap near 30, plus the per-import model load if the design keeps one worker process per import.
- Peak memory rises to the gigabyte range with the layout model resident. C-8's watchdog becomes mandatory rather than advisable.
- Docling's `document_timeout` option exists and should back the parent deadline so a timeout leaves no half-built result.

### DC-5. Bundle footprint, estimated

| Candidate | What ships | Estimated payload | Native binaries to sign |
| --- | --- | --- | --- |
| pypdfium2 only | interpreter, core, MCP SDK, one PDFium library | tens of MB | few |
| docling-parse only | interpreter, core, MCP SDK, docling-parse | tens of MB | few |
| PyMuPDF | interpreter, core, MCP SDK, MuPDF libraries | around 100 MB | a few dozen |
| Docling, ONNX layout, tables off | the above plus the docling-slim stack, transformers, onnxruntime, Heron ONNX weights | 300 to 400 MB | dozens |
| Docling, PyTorch layout | the above plus torch, torchvision, docling-ibm-models | 700 MB to more than 1 GB | hundreds |

These are estimates from wheel and weight sizes, not measurements. P1 records the real numbers.

### DC-6. Verdict (superseded by DC-7)

Docling is the right second backend and the wrong first one for this proof.

- It answers D-3, and it would improve retrieval on the 48-page manual and the 80-page report, because it produces paragraphs, headings, reading order, and merged lines instead of parser blocks. That matters for D-5.
- It fails the proof's own constraints as written: the spec excludes it, the transport decision excludes a second service, core has no in-process adapter, the 45-second deadline and 100-page cap do not survive, the bundle grows three to four times, and the notarization surface grows with it. Every one of those can be changed, but together they make a different proof, and the ProductSpec revision must say so.

Recommendation, in order:

1. If AGPL is the driver, add a pypdfium2 adapter to core and make it the first backend. It is permissive, fast, needs no model, detects passwords, reports page counts, and produces page text with character geometry. The design's existing `page_text` fallback already describes an artifact built from page text without blocks, so the tool contracts do not change. Keep the 45-second deadline and the 100-page cap. This is the smallest change that removes the license problem.
2. Schedule Docling as milestone 2 with its own spec revision: an in-process core adapter, ONNX layout, tables and OCR off, weights prefetched into the bundle, a deadline and page cap re-derived from P1 measurements on a base M-series machine, and the D-5 recall check rerun to show the quality gain. Because pypdfium2 is also Docling's PDF backend, physical page numbering and page text stay consistent across the two milestones, and the artifact manifest's backend fields already record which engine produced an artifact.
3. Do not bundle the PyTorch path or docling-serve for either milestone.

If the owner wants Docling first anyway, the minimum edits are: ProductSpec revision 2 that removes Docling and a local model from the out list and adds a model disclosure; engineering sections 1, 5, 6, and 11 for backend, memory, deadline, page cap, and bundle contents; plan R0 to add the in-process adapter to core's scope; and plan P1 to measure ONNX CPU latency per page and settle the transformers-without-torch question before anything else.

### DC-7. The permissive three-engine bundle

Owner decision, 2026-09-10. This section replaces DC-6's recommendation. It describes the profile as this review understands it and the edits the proposal needs. Codex should treat it as input to ProductSpec revision 2, not as an approved contract.

Engine roles:

| Role | Component | License | Notes |
| --- | --- | --- | --- |
| Pipeline and orchestration | Docling, in process | MIT | One pipeline runs everything. There is no separate per-engine adapter in this repository. |
| PDF parsing and rendering | docling-parse v4 as Docling's default backend, pypdfium2 for page rendering and preflight | MIT; Apache-2.0 or BSD-3-Clause with BSD-style PDFium | Both are Docling dependencies already. pypdfium2 alone does the cheap preflight: page count, password detection, text-layer presence. |
| Layout and reading order | Layout Heron, ONNX Runtime engine, CPU provider; Docling's rule-based reading order | Apache-2.0 weights; MIT runtime | Weights prefetched at build time and loaded through `artifacts_path`. No download at runtime. |
| OCR | Tesseract through Docling's CLI OCR model, with bundled tessdata | Apache-2.0; Leptonica BSD-2-Clause | Explicit, never automatic. See the OCR notes below. |
| Table structure | none | | TableFormer runs only on the docling-ibm-models engine, which needs torch. Off until a torch-free engine exists or the owner accepts torch. |

Hard rules that follow from the decision:

- No torch, torchvision, or docling-ibm-models anywhere in the bundle. The build fails if the lock contains them. This is the check that keeps the bundle permissive and small.
- Docling's `do_table_structure` is false and `do_ocr` is controlled by setup, not by the model. Confirm in C2 what Docling emits for table regions when structure is off, so table text still reaches passages.
- The engine imports `transformers` for image preprocessing on the ONNX path. Pin it, record its license (Apache-2.0), and prove in P1 that the pipeline runs with torch absent. DC-3 records why this is unverified.
- OCR-derived text carries its own `source_kind` value, for example `ocr_text`, in passages and search hits. A citation from OCR must say so. The truth rule that a quote proves extraction, not understanding, applies twice as hard here.
- The worker still owns every engine. The parent never imports Docling, onnxruntime, PDFium, or Tesseract. Prefer a warm worker that survives between imports with an idle timeout, restarted on crash or deadline, so the model loads once per session instead of once per import.
- The import deadline, page cap, and memory ceiling are P1 measurements on a base M-series machine, not the current constants. Each host has a tool-call timeout; record it in H1 and H2 and size the page cap so the measured 95th percentile import fits under the strictest host. Emit MCP progress notifications during import so a slow document does not look like a hung server.

OCR engine notes. The owner named Tesseract. Two permissive alternatives cost less to bundle: RapidOCR, Docling's default, runs on the onnxruntime already in the bundle and adds only its model files; ocrmac uses Apple's Vision framework with nothing to bundle but is macOS-only. Keep Tesseract as the choice, and let P1 run all three on the synthetic scanned fixture and record accuracy, size, and latency. Switch only on measured evidence. Whichever engine ships, image-only pages are refused with `no_readable_text` when OCR is disabled at setup, which keeps the spec's "no automatic OCR escalation" rule.

Spec edits for revision 2:

- Scope: remove "Do not install Docling, Tesseract ... automatically" from the out list. Keep "no local language model" and add that a local vision model for page layout ships in the bundle and is disclosed at setup.
- Product summary: the first backend is the Docling profile above, not PyMuPDF.
- AC-4: replace "the explicitly pinned PyMuPDF backend" with the pinned local engines, and add "loads no model weights from outside the bundle".
- AC-9: limits are the measured constants from P1, referenced by name, not the current numbers.
- Add an acceptance criterion that OCR runs only when enabled at setup and that OCR text is labeled in every result.
- Risks: add the model disclosure and the bundle size.

Design edits:

- Section 1: parser and extraction rows; add a row for the no-torch rule and its reason.
- Section 4: setup gains an OCR switch, default off, passed as a profile argument. Tools still accept no backend field.
- Sections 5 and 6: warm worker, memory watchdog, measured deadline and page cap, progress notifications, host timeouts.
- Section 7: manifest records docling, docling-parse, pypdfium2, onnxruntime, and Tesseract versions, the layout weight hash, the tessdata hash, and the OCR and table settings inside `extraction_settings`.
- Section 8: passages come from Docling items. Map every `prov` entry, not the first. Keep physical page numbers from Docling's page provenance. Add the OCR `source_kind`.
- Section 11: bundle contents and notices for every component above, plus the torch exclusion check.
- Section 15: add Docling, docling-parse, pypdfium2, and Tesseract references.

Plan edits:

- R0: the core proposal gains an in-process Docling adapter with these settings and a pypdfium2 preflight. The existing HTTP adapter for docling-serve stays separate.
- P1: measure ONNX layout latency per page and peak memory on a base M-series machine, bundle size, cold start, and the three OCR engines; prove torch-free execution; notarize the full native set.
- C2: preflight moves from the PyMuPDF adapter to pypdfium2.
- M0 and the rest of the plan are unchanged in shape. The token experiment gains a better arm B and arm C extraction, which makes D-1's warning about short documents more relevant, not less, because Docling's structure does not reduce turn count.

## Q. Questions for the owner

1. Is a negative token result acceptable as the first public outcome? The answer decides whether M0 runs before P1.
2. Are a Developer ID certificate and notarization available for this project? If not, binary MCPB packaging cannot meet AC-1 on a browser-downloaded bundle.
3. Answered on 2026-09-10: no PyMuPDF in the bundle. See DC-7.
4. Should the source snapshot stay in the artifact?
5. Which model runs the experiment? The budget ceilings depend on it.
6. For coding clients: configuration file, environment variable, or project directory as the grant?
7. One Docling profile for every import, or a second text-only profile on pypdfium2 for fast imports of text PDFs? P1 measurements decide whether the question matters.
8. OCR enabled at setup only, or also selectable per import through a closed mode value? Setup only keeps AC-4 simple.
9. Is an import deadline of a few minutes acceptable for the largest documents, with progress notifications, or should the page cap drop to fit the current 45 seconds?
10. Tables: accept no table structure recognition until a torch-free engine exists, or accept torch and the bundle size that comes with it?

## What this review did and did not check

- Read every Markdown file on main at commit `e36ff04`, the repository check script, and its tests.
- Ran `make sync` and `make verify` on main, which passed, and again with this file present.
- Did not open the core repository, per the review instruction to stay in this checkout. Statements about core adapters come from the design's own description and the linked catalog.
- Did not verify the MCPB manifest capabilities, the Codex plugin format, the Agent SDK usage fields, Apple's current notarization rules, or the provider's PDF token accounting against live documentation. Items that depend on those are marked as things to confirm in P1, H2, or M1.
- Ran no host installation and no model call.
- For the Docling check, read PyPI metadata, Docling source files on GitHub, the Docling technical report, Hugging Face model file listings, and the two core adapter sources on GitHub. Nothing from those sources was executed.

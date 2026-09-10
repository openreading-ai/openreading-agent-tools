# Remaining proof execution plan

**Status:** local implementation complete enough for review; release evidence remains unverified.
**Intent:** [ProductSpec revision 1](../product/specs/local-document-proof.product-spec.md).

The implemented build and runtime contracts now live in [runtime](../runtime/README.md), [client guides](../README.md), and [measurement](../measurement/README.md).
The source PRs do not authorize public binary distribution or paid model trials.
Human maintainers review and merge; agents never merge these branches.

## 1. Review the implementation

- [ ] Review core's intake, process cancellation, retained artifact integrity, exact spans, and MCP response caps.
- [ ] Review the immutable tools dependency pin and native runtime inventory.
- [ ] Review measurement accounting, frozen inputs, tool permissions, restart spending, and claim decisions.
- [ ] Re-run `make sync`, `make verify`, and `make audit` from the tools checkout.
- [ ] Confirm the acceptance evidence table distinguishes implementation tests from host and model evidence.

## 2. Close distribution and host gaps

- [ ] Resolve the bundled PyMuPDF distribution license and notice inventory before sharing binaries.
- [ ] Sign and notarize a new native candidate with the approved company identity.
- [ ] Execute the clean-machine Desktop installation and setup-cancellation checks.
- [ ] Execute the complete lifecycle matrix in the [remaining release design](local-document-proof.md).
- [ ] Execute cited-answer and malicious-document walkthroughs in each named client version.

Each failure needs a regression where possible, a package rebuild, and a repeat of the affected host check.
Do not generalize one client's success to another client or operating system.

## 3. Run the token proof

- [ ] Review the synthetic dataset, answers, baseline tool policy, and calibrated query settings.
- [ ] Prepare a new frozen calibration manifest with an explicit account fingerprint.
- [ ] Obtain owner approval for that exact manifest and estimated spending ceiling.
- [ ] Run calibration, preserve every failure, and inspect complete usage coverage.
- [ ] Freeze a new primary manifest after calibration changes, then obtain its separate approval.
- [ ] Run the primary study, review answer quality independently, and regenerate the complete report.
- [ ] Publish a token claim only if every preregistered threshold passes and the evidence is reviewed.

## 4. Finish the user proof

- [ ] Complete the five-participant pilot and record the ProductSpec success metrics privately.
- [ ] Update the walkthrough with actual reviewed host evidence and remaining limits.
- [ ] Move durable completed facts beside their implementation and remove these remaining proposal records when their work ships.

# Changelog

## [Unreleased]

### Changed

- ProductSpec revision 2 replaces the proposed distributed PyMuPDF profile with Docling, ONNX layout, PDFium, and setup-only Tesseract.
- The revised design adds measured timing and memory gates, a signing fallback, explicit coding-client grants, offline retrieval checks, and an M0 probe before further packaging.
- Existing executable behavior remains the revision 1 prototype; no Docling migration, installation, or paid experiment runs in this design pass.

### Added

- Repository instructions, contribution and security policies, GitHub templates, and offline documentation checks.
- A ProductSpec, engineering design, token experiment design, and implementation plan for a local document proof.

- A frozen macOS arm64 runtime consuming an immutable core revision, with complete file integrity checks and dependency notices.
- Claude Desktop MCPB, Claude Code, and Codex package assembly with explicit directory grants and a shared retrieval skill.
- Synthetic token experiments, frozen manifests, resumable budget accounting, and offline report regeneration.
- Offline runtime and measurement tests with enforced coverage floors.

No public binary or token reduction result is released.

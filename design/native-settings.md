# Native settings release acceptance

ProductSpec revision 28 preserves native settings and document features in a server-only connector.
Revision 30's [unsigned preview policy](../SECURITY.md#unsigned-preview-policy) removes the candidate's mandatory signing and notarization gate.
The source contracts live in `runtime/app_settings.py`, `storage_settings.py`, and `settings_server.py`.
The settings connector is separate from the complete pinned Core document catalog.
Revision 28 removes all connector authentication controls and Keychain integration.
Legacy destinations keep their URL and limits. Old credential references are ignored, and Core authentication remains unchanged.

## Remaining native gates

- Revision 26 requires saved storage choices and active, pending or blocked status to survive reopening.
- Verify an abandoned legacy launch record permits migration while a live connection or unfinished import still refuses it.
- Verify the assistant reports the selected queue, preserves it across Add more, and waits for Process before importing.
- Revision 28 replaces runtime provisioning with a direct plugin containing the parser-free connector.
- Verify actual Claude upload, first activation and settings opening with the exact small plugin archive.
- Verify the server-only package refuses missing or legacy local configuration, preserves prior data, and exposes the server catalog with truthful upload annotations.
- Verify installation requires no runtime or model download. No ngrok runtime service is required for the server-only package.

- TODO: Review and refine the settings modal messaging with the owner before release. Cover labels, explanations, save feedback, and reconnect instructions.
- Install the exact built package in each supported local host. Verify `/openreading-settings` discovery and opening.
- Exercise storage selection, cancellation, saving, restoring defaults, reconnect, and the default folder without editing JSON.
- Preserve a readable synthetic artifact and completed job after moving data. Verify client isolation and rollback after a failed copy.
- Confirm unfinished jobs and concurrent connections prevent migration, then finish them and retry.
- Verify URL-only connection testing without documents and upgrades from legacy destination settings.
- Check keyboard and assistive-technology access. The current Tk controls require their own accessibility acceptance.
- Verify foreground activation, repeated invocation, helper lifetime and clean-machine installation. Record signature status and any host refusal without bypassing protections.
- Confirm package-size limits in the native installer. A self-contained local directory is not proof that upload installation accepts its archive.

Previously published export paths retain their original copies. New exports use the selected data partition.
Returning to an occupied historical partition is refused to prevent silent merging; select a fresh folder for another migration.
The original copy is not automatically deleted. A later cleanup interface requires separate product intent and testing.

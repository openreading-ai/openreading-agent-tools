# Native settings release acceptance

ProductSpec revision 20 adds AC-38 and AC-39 to the existing client matrix.
The source contracts live in `runtime/app_settings.py`, `storage_settings.py`, and `settings_server.py`.
The settings connector is separate from the complete pinned Core document catalog.

## Remaining native gates

- TODO: Review and refine the settings modal messaging with the owner before release. Cover labels, explanations, save feedback, and reconnect instructions.
- Install the exact built package in each supported local host. Verify `/openreading-settings` discovery and opening.
- Exercise storage selection, cancellation, saving, discarding, reconnect, and the default folder without editing JSON.
- Preserve a readable synthetic artifact and completed job after moving data. Verify client isolation and rollback after a failed copy.
- Confirm unfinished jobs and concurrent connections prevent migration, then finish them and retry.
- Verify native Keychain save, preservation, anonymous mode, and server connection testing without documents.
- Check keyboard and assistive-technology access. The current Tk controls require their own accessibility acceptance.
- Verify foreground activation, repeated invocation, helper lifetime, clean-machine installation, signing and notarization.
- Confirm package-size limits in the native installer. A self-contained local directory is not proof that upload installation accepts its archive.

Previously published export paths retain their original copies. New exports use the selected data partition.
Returning to an occupied historical partition is refused to prevent silent merging; select a fresh folder for another migration.
The original copy is not automatically deleted. A later cleanup interface requires separate product intent and testing.

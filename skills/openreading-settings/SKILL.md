---
name: openreading-settings
description: Open OpenReading Settings to review or change the data folder, document processing destination, server credentials, or delivery limits through native controls.
---

Call `openreading_open_settings` with no arguments, using its host-qualified name when required.
The user chooses and saves values in the native window. Never supply configuration through tool arguments or edit preference files.
Opening requests the window. It does not establish that settings were saved.
After saving, reconnect the document connector to apply changes. Existing imports must finish before storage moves.
If the tool is unavailable, report that the installed package lacks the Settings connector.

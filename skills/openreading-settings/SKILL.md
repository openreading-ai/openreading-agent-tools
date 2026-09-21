---
name: openreading-settings
description: Open OpenReading Settings to review or change the data folder, document processing destination, server credentials, or delivery limits through native controls.
---

Call `openreading_open_settings` with no arguments, using its host-qualified name when required.
The user chooses and saves values in the native window. Never supply configuration through tool arguments or edit preference files.
Opening requests the window. It does not establish that settings were saved.
After saving in Claude Desktop, tell the user to fully quit Claude with Command-Q and reopen it.
Then start a new task and ask to open the OpenReading file picker to apply the saved changes.
Opening Settings alone does not apply a pending storage move. Existing imports must finish before storage moves.
For other clients, name the current app and explain how to quit and reopen it before opening the picker.
If the tool is unavailable, report that the installed package lacks the Settings connector.

This plugin requires an operator-run OpenReading Core server. Processing configures its URL and optional credentials; no parser is bundled.
If setup is missing, open Settings. Never invent or save a server URL for the user, and never claim a connection test proves parsing works.

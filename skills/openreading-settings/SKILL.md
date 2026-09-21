---
name: openreading-settings
description: Open OpenReading Settings to review or change the data folder, document processing destination, server credentials, or delivery limits through native controls.
---

Opening OpenReading Settings or its picker is an action in a native application on the user's connected computer.
In Claude Desktop, follow the host's device-connection flow for that requested action before searching for OpenReading tools.
Use tool definitions supplied by the connected device, including definitions delivered after device linking. Cloud connector search alone can miss local plugin tools.
When available, `get_device_info` reports whether the `openreading` and `openreading-settings` local MCP servers are announced.
Use the returned host-qualified tool name. Follow pending device-linking instructions and honor permission refusals; do not request unrelated screen-control or folder access.
If discovery still fails, report that this session cannot access the tool and state the observed device status. Do not infer a missing installation or require a reinstall.

Call `openreading_open_settings` with no arguments, using its host-qualified name when required.
The user chooses and saves values in the native window. Never supply configuration through tool arguments or edit preference files.
Opening requests the window. It does not establish that settings were saved.
After saving in Claude Desktop, tell the user to fully quit Claude with Command-Q and reopen it.
Then start a new task and ask to open the OpenReading file picker to apply the saved changes.
Opening Settings alone does not apply a pending storage move. Existing imports must finish before storage moves.
For other clients, name the current app and explain how to quit and reopen it before opening the picker.

This plugin requires an operator-run OpenReading Core server. Processing configures its URL and optional credentials; no parser is bundled.
If setup is missing, open Settings. Never invent or save a server URL for the user, and never claim a connection test proves parsing works.

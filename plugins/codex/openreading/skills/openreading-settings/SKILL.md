---
name: openreading-settings
description: Open OpenReading Settings to review or change the data folder, document processing destination, or delivery limits through native controls.
---

In Claude Code, local Codex and ChatGPT Work, use this plugin's registered MCP tools directly.
Do not try to open an app named OpenReading through computer-use tools before calling the available Settings or selection tool.
The device-enabling procedure below applies only to Claude Desktop.
If tools are unavailable, inspect this plugin's connection status through the host's plugin controls (`/mcp` in Claude Code or Codex).
Do not substitute a browser, shell-based parser, or another plugin's OpenReading connector.

Invoking this command requests opening the native OpenReading Settings window on the user's computer.
If `openreading_open_settings` is already available, call it directly.
Otherwise, in Claude Desktop, activate the connected computer before looking for local plugin tools:

1. If the host exposes `enable__mcp__remote-devices__computer`, call it once with `task: "Open the native OpenReading Settings window through the installed OpenReading plugin."`. This request opens an application on the user's computer, which is what that gate enables.
2. Follow the host's device-linking instructions and wait for the connected device's tool definitions. Use definitions delivered after linking, even if the initial tool list omitted them.
3. Resolve `openreading_open_settings` using its supplied host-qualified name. When available, `get_device_info` can report whether `openreading-settings` is announced. Cloud connector search alone does not discover every local plugin tool.
4. Honor any permission refusal. Do not use screen control, shell commands or file edits as a replacement for the Settings tool.

Do not stop at "only device-enabling tools are available" when the computer gate is available for this native-window request.
If activation or discovery fails, report the observed failure. Do not infer a missing installation, tell a Desktop user to switch to Desktop, or recommend a restart or reinstall from a missing tool alone.

Call `openreading_open_settings` with no arguments, using its host-qualified name when required.
The user chooses and saves values in the native window. Never supply configuration through tool arguments or edit preference files.
Opening requests the window. It does not establish that settings were saved.
After saving in Claude Desktop, tell the user to fully quit Claude with Command-Q and reopen it.
Then start a new task and ask to open the OpenReading file picker to apply the saved changes.
Opening Settings alone does not apply a pending storage move. Existing imports must finish before storage moves.
For other clients, name the current app and explain how to quit and reopen it before opening the picker.

This plugin requires an operator-run OpenReading Core server. Processing configures its URL; no parser is bundled.
If setup is missing, open Settings. Never invent or save a server URL for the user, and never claim a connection test proves parsing works.

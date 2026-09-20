# OpenReading local documents development plugin

This plugin bundles local document tools and the shared evidence workflow for ChatGPT desktop Work.
It uses the verified macOS Apple Silicon runtime without requiring a pasted executable path or a separate Python installation.
ChatGPT 26.911.61220's bundled CLI resolved the working directory to the installed plugin folder, leaving `./server/openreading-worker` relative.
A separate network-denied MCP process passed with that configuration; native GUI startup after reinstall has not been independently captured.
The configuration avoids `${PLUGIN_ROOT}`, which remained literal in the observed legacy plugin MCP loader.
The candidate is unsigned development output. Native plugin installation, ordinary Chat, signing and clean-machine acceptance remain pending.

## Local installation check

Open the generated marketplace folder as a local Work project, then find OpenReading in the plugin browser.
The marketplace is `.agents/plugins/marketplace.json` at that folder's root.
Install **OpenReading Local Documents (development)** from **OpenReading development preview**.
If the host does not discover the marketplace, stop and record its version and observed error.
Do not replace the missing installation path with a manually configured server and call the package accepted.

Disable the earlier manual OpenReading test connection before testing the installed plugin.
Start a fresh local Work chat and confirm that its OpenReading tools come from this plugin.
Select a synthetic document, start one import, wait for success, retrieve it with automatic delivery, and confirm an exact passage through read.
Force file delivery of that small artifact and verify the original export bytes and SHA-256 with the host's local file tools.
Record the application version, plugin identity, chooser behavior, approval prompts and failures.
The plugin browser owns installation and removal. Packaging never edits shared host settings.
OpenAI clients can share plugin configuration; this package does not enforce isolation between applications.

## Documents and retained data

OpenReading reads files you select. Your assistant may have separate file and shell access.
The configured adapter determines supported formats. OCR can misread text, and table structure is not always available.
Extracted passages enter your assistant's context when retrieved. Local parsing does not keep those passages out of the model.
The `chatgpt` storage namespace is shared with the earlier manual registration.
Selected copies, artifacts, jobs, selection receipts and exports persist independently of plugin removal.
Exports live in `~/Downloads/OpenReading`. They can be indexed or backed up by your operating system.
Do not enable duplicate registrations when checking which runtime produced a result.

## Runtime identity

`server/release.json` binds the included runtime inventory, core commit, executable hash and dependency notices.
`package-info.json` binds this plugin's manifest, MCP configuration, workflow and README to that runtime.
These hashes detect changes relative to recorded files. They do not authenticate a publisher or establish signing.
No token savings, parsing accuracy or support for another host follows from a successful installation.

## OpenReading Managed: Coming soon

Document processing on OpenReading's servers, without managing local compute.
Planned after the public OSS launch.

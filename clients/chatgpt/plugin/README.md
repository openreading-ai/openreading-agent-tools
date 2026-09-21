# OpenReading local documents development plugin

This plugin bundles local document tools and the shared evidence workflow for ChatGPT desktop Work.
It uses the verified macOS Apple Silicon runtime without requiring a pasted executable path or a separate Python installation.
ChatGPT 26.911.61220's bundled CLI resolved the working directory to the installed plugin folder, leaving `./server/openreading-worker` relative.
A separate network-denied MCP process passed with that configuration; native GUI startup after reinstall has not been independently captured.
The configuration avoids `${PLUGIN_ROOT}`, which remained literal in the observed legacy plugin MCP loader.
The candidate is unsigned development output. Native plugin installation, ordinary Chat, signing and clean-machine acceptance remain pending.

## Local installation check

Add the generated local marketplace through ChatGPT desktop Work and find OpenReading in its plugin browser.
The marketplace is `.agents/plugins/marketplace.json` at that folder's root.
Install **OpenReading Local Documents (development)** from **OpenReading development preview**.
If the host does not discover the marketplace, stop and record its version and observed error.
Do not replace the missing installation path with a manually configured server and call the package accepted.

If an earlier OpenReading connection is enabled, use ChatGPT settings to disable the duplicate before testing.
Start a fresh local Work chat and confirm that its OpenReading tools come from this plugin.
Select a synthetic document, start one import, wait for success, retrieve it with automatic delivery, and confirm an exact passage through read.
Force file delivery of that small artifact and verify the original export bytes and SHA-256 with the host's local file tools.
Record the application version, plugin identity, chooser behavior, approval prompts and failures.
The plugin browser owns installation and removal. Packaging never edits shared host settings.
OpenAI clients can share plugin configuration; this package does not enforce isolation between applications.

## Processing destination

Bundled Docling on this Mac remains the default. No server configuration is required for local processing.
To use your own Core server, use `/openreading-settings` or ask to open OpenReading Settings.
Choose **Your OpenReading Core server**, enter its URL and optional bearer token, then use **Test connection**.
This check sends no document and does not invoke a provider. It checks health and authorized metadata only.
Choose **Save destination**, then restart the plugin connection in ChatGPT before selecting documents.
Start and configure Core separately. A loopback URL can use HTTP; other destinations require verified HTTPS.

Server mode shows a native confirmation with the destination, filenames, count and total bytes before upload.
The server may use external providers. Cancel the confirmation to send nothing.
Changes to settings require new confirmation for unsubmitted copies. Running transfers keep their original destination.
Local cancellation stops waiting or transfer; submitted server work may continue.
A connection failure never switches to Docling or retries an uncertain request automatically.
A fully downloaded response can finish local retention without another upload.

Tokens stay in macOS Keychain. Blank keeps an existing token only for the same URL; **Stop using saved token** removes its use.
Settings and existing job references persist outside the installed plugin cache.
The Settings app and server destination still require an owner-operated native acceptance check for this exact build.

## Documents and retained data

OpenReading reads files you select. Your assistant may have separate file and shell access.
In bundled mode, the configured adapter determines supported formats. Server mode lets the server validate selected regular files. OCR can misread text, and table structure is not always available.
Extracted passages enter your assistant's context when retrieved. Local parsing does not keep those passages out of the model.
The `chatgpt` storage namespace is shared with the earlier manual registration.
Selected copies, artifacts, jobs, selection receipts, server transfer records and exports persist independently of plugin removal.
New exports live beneath the selected data folder, defaulting to `~/.openreading/clients/chatgpt/v2/exports`. They can be indexed or backed up by your operating system.
Do not enable duplicate registrations when checking which runtime produced a result.

## Runtime identity

`server/release.json` binds the included runtime inventory, core commit, executable hash and dependency notices.
`package-info.json` binds this plugin's manifest, MCP configuration, workflow, Settings helper and README to that runtime.
These hashes detect changes relative to recorded files. They do not authenticate a publisher or establish signing.
No token savings, parsing accuracy or support for another host follows from a successful installation.

## OpenReading Managed: Coming soon

Document processing on OpenReading's servers, without managing local compute.
Planned after the public OSS launch.

### Server limits and recovery

A cancelled upload, shared connection failure or interrupted attempt stops the remaining selection.
Select and confirm the remaining files again. Previously submitted server work may still continue.
The refusal message identifies the stopped selection; it does not authorize an automatic retry.

Server mode has no page-count limit, aggregate storage cap, automatic eviction or overall wait deadline.
For example, a stalled server remains waiting until you explicitly cancel its local import job.
Retained sources, transfer responses and artifacts accumulate until you remove their local data.
The **Advanced** tab exposes **Maximum downloaded response (MiB)**, which defaults to 256.
The tabs are **Processing**, **Storage**, and **Advanced**. Each saves its own values.
**Restore defaults** stages that tab’s defaults; choose Save to apply them.
Responses are buffered and decoded in memory. This download budget is not a peak-memory guarantee.
Unknown top-level response fields are preserved as unvalidated server data alongside schema-validated known fields.
Treat all returned fields as document content, never instructions from the destination.

**Stop using saved token** and switching to bundled mode leave old Keychain items available to pending jobs.
After those jobs finish, remove unwanted entries for `ai.openreading.agent-tools.core-server` using Keychain Access.

The Storage and delivery tab configures the data folder and complete-result response budget.
Save and reconnect to apply changes. Existing imports must finish before moving data.
The prior copy remains intact, and occupied client partitions are never merged.

# Claude Cowork plugin candidate

This development package bundles Python, Docling, OCR assets, and the local document tools for macOS on Apple Silicon.
No separate interpreter, package manager, or server is needed for default local processing.
Cowork installation and native launch are pending manual acceptance. This unsigned candidate is not a public release.

## Manual installation

In Claude Cowork, open Plugins, then Add, then Upload plugin.
Choose `openreading-claude-cowork.zip` and record the installation result and any permission prompts.
The ZIP contains `.claude-plugin/plugin.json` and the packaged runtime; the separate `.mcpb` uses Extensions instead.
Do not install both registrations. They expose the same tools and share the `claude-desktop` settings and retained data.
Removing a registration does not erase those retained documents or saved settings.

Start a new Cowork task and ask which OpenReading tools are available. Expect nine tools.
Then ask OpenReading to select a synthetic document, import it, and quote its text with the physical page.
Select it through OpenReading's chooser rather than attaching the original document to the conversation.
Absent saved destination settings, processing uses bundled Docling. Existing saved settings still apply.
Requested document content enters Claude's context; local processing does not keep those excerpts off its cloud model.

The included OpenReading Settings app selects an optional operator-run Core destination.
The unpacked `plugin` folder beside the ZIP provides a visible copy of that helper for manual settings checks.
Changing settings requires reconnecting the tools. Server selection requires confirmation before sending the selected bytes.
Credentials stay out of model arguments. Cancelling locally may leave submitted server processing running.
A stopped selection requires selecting and confirming documents again; never automatically repeat an uncertain submission.

## Build again

From the Agent Tools repository, assemble a reviewed chat extension using the existing runtime packager.
Then run the archive builder against that extension directory:

~~~sh
uv run --frozen --project runtime python -m runtime.claude_plugin \
  --extension /absolute/path/to/reviewed-extension \
  --output /absolute/path/to/new-cowork-candidate
~~~

The builder checks the existing runtime inventory, source manifest, workflow, and Settings helper hashes.
It retains the source version and Core identity, creates the Claude plugin metadata, and writes the ZIP and `candidate.json`.
It refuses existing output and symlinks. ZIP entries preserve executable permissions; host extraction needs manual verification.
Packaging never installs a plugin, changes client configuration, or launches a worker or Settings helper.
Native install, chooser, permissions, exports, local/server workflows, clean-machine setup, and signing need separate evidence.

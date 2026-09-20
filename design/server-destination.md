# Optional operator-run Core destination

Status: approved integration design, not a finished packaged feature. ProductSpec revision 18 owns the outcomes.
Bundled Docling stays the default. The source HTTP transport lives in runtime/server_transport.py.
The synthetic owner-operated ChatGPT probe established localhost connectivity only.

## Native settings and consent still to build

Package the native settings entry point implemented in runtime.destination_ui.
Its window offers bundled Docling and your Core server choices.
It uses runtime.destination_settings for revisioned settings and runtime.server_keychain for credentials.
Those library modules define their shipped validation and persistence behavior.
Native credential prompts remain unverified; offline tests use a fake Security framework.
Changing destination requires fresh confirmation for unprocessed selected files.

The server chooser accepts regular files and preserves existing folder traversal exclusions.
Before accepting a snapshot, show its destination, reviewable filenames, count, and total bytes.
Disclose that the server's configured backends may use other services.
No model argument changes settings, credentials, headers, or Core routing.

## Job and evidence integration still to build

Use the existing local detached-job lifecycle with a trusted launcher-owned service factory.
Persist each job's nonsecret destination snapshot. Reconstruct it through fixed packaged child dispatch.
No serialized module path or model-controlled executable may select implementation code.
Keep the exact selected snapshot throughout upload and bind Core retention to its uploaded-byte digest.
Retain the returned normalized result through Core's external-response retention operation.
Search, read, and complete delivery consume local evidence after success, without new network requests.

Serialize submissions. Preserve one result per selection, including duplicate basenames.
Document-specific failures allow later siblings; shared transport/auth failures stop further submission.
A complete saved response may finish retention without uploading again after restart.
An incomplete request becomes outcome unknown and is never automatically resubmitted.
Cancellation affects local work; the operator's server may continue processing submitted requests.

Core tool descriptions and annotations must disclose network processing in this mode.
The local default catalog remains equivalent to direct Core under the same profile.
A library transport pass does not establish settings, packaged launch, host accessibility, or native acceptance.

## Remaining verification

Test configuration revision changes, Keychain refusals, selection cancellation, duplicate names,
partial and structured-only responses, faithful complete delivery, and grant separation offline.
Test cancelled, interrupted, and reconnected jobs against a synthetic server.
Run both repository gates and frozen smoke against the exact Core pin before preparing a Downloads package.
The owner installs and runs the candidate through ChatGPT UI. No CLI or model API substitutes for that check.
Keep local and remote HTTPS/ngrok results distinct. Do not merge or publish a release.

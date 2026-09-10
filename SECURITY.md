# Security policy

## Report a vulnerability

Send a private report to <creativeaisle@gmail.com>, the maintainer contact used by OpenReading core.
Include the affected commit or release, impact, and a synthetic reproduction.
Do not open a public issue containing credentials, private documents, or an exploit against another user's machine.

There are no released runtime versions yet.
Security corrections to repository tooling land through reviewed pull requests.
This policy will name supported runtime releases when they exist.

## Current and proposed behavior

The repository currently contains documentation and development checks.
It does not install a parser or start an MCP server.
Read the [engineering proposal](design/local-document-proof.md) for the unbuilt runtime's boundaries.

The proposed runtime reads files chosen through a configured input directory.
It retains extracted content locally and returns selected passages to the calling assistant.
Those passages may enter a cloud model's context.
Local processing does not establish that all document information stays on the machine.

Native document parsers run with the permissions of their process.
A configured path boundary is not an operating-system sandbox.
The proof must not describe it as one.

## Reports that matter

- A launcher executes an unverified download or a different runtime than the package declares.
- A tool reads outside its configured input or artifact directory.
- An error or diagnostic exposes document text or a credential unexpectedly.
- A local-only proof request reaches a hosted parser or follows a document-provided URL.
- A package upgrade changes an executable without changing its integrity record.
- Document instructions cause an assistant to broaden file access or expose additional content.

Model behavior and third-party parser vulnerabilities may also require upstream reports.
Include how the problem affects this project's supported workflow.

## Data and distribution

Keep live transcripts, artifacts, and private fixtures out of Git.
Synthetic tests should plant recognizable secrets to verify error redaction.
Future bundles need a dependency inventory and applicable notices.
The repository's Apache source license does not relicense a bundled dependency.

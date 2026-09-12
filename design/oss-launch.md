# OSS launch v1 and the Coming soon boundary

Status: ProductSpec revision 6 proposal. The README includes static preview copy; release catalog parity, host presentation and distribution acceptance remain pending.
Contract: [ProductSpec](../product/specs/local-document-proof.product-spec.md), AC-27 through AC-29.
Execution order: C0 and N3 in the [implementation plan](implementation-plan.md).

## Product versions and ownership

Public product v1 is the free OSS launch. Managed product v2 starts after OSS launches.
Historical prototype revision 1, the local `local-document-proof-v2` profile, version 2 settings and P0 release identifiers keep their existing meanings.
This proposal changes no runtime pin, artifact identity, schema version or stored settings path.

Core stays free OSS, including its entire implemented MCP surface, ordinary APIs, adapters and strategies.
Agent Tools stays free OSS and bundles only the selected slim Docling local runtime.
It does not install, select or manage alternative local backends or someone else's core server.
Power users can independently install full core and configure their assistant to connect directly to that core MCP server.
No OpenReading company account or paid entitlement gates local tools.

## All implemented core MCP tools at launch

MCP tools are discovered with `tools/list` and invoked with `tools/call`.
“All endpoints” means the implemented tools of the immutable core version included in the release, not a new HTTP API or an unimplemented core roadmap.
The current candidate `7d97b75` implements:

| Tool | Required behavior |
| --- | --- |
| `openreading_import` | Retain the requested granted document, return a bounded receipt, and preserve explicit core refusals. |
| `openreading_search` | Search retained evidence with the documented literal retrieval contract, exact excerpts and cursors. |
| `openreading_read` | Resolve returned evidence identifiers to bounded exact passages and source provenance. |

The current catalog is three tools. Three is not a permanent commercial limit.
A future pin must include every additional implemented core tool before that pin can ship in Agent Tools.
Do not advertise MCP parse, compare, strategy, folder or job operations merely because related CLI/HTTP operations exist.
Do not invent placeholder tools for operations core has not implemented.

The first distribution keeps its explicit local Docling profile, grants, resource limits and no-hosted-dispatch rule.
Exposing the full MCP interface does not install every backend or make unsupported extraction capabilities work.
Where core supports an operation only with absent optional capabilities, preserve its explicit refusal or warning.
If a core pin introduces a tool incompatible with these boundaries, resolve its safe local contract before accepting the pin.
Do not satisfy this rule by removing the tool from the expected list, hiding it behind managed v2, or returning fake success.
Future upstream changes can require a client/runtime update; no automatic compatibility or no-reinstall promise is made.

## Catalog parity evidence

C0 compares three independently obtained inventories: the direct immutable core build, its frozen runtime, and each released host wrapper.
Compare names, input schemas, declared output schemas where present, annotations and relevant capability declarations.
Normalize only documented host name qualification. Do not normalize away a missing tool or contract difference.
Obtain the reference from the actual pinned package, not another wrapper or a hard-coded permanent list of three.
Record core commit, runtime hash and normalized catalog digest with the results.

Every exposed tool needs a valid synthetic call and a representative refusal through the frozen runtime.
Native host checks must show that the corresponding tools can be discovered and invoked through the claimed mode.
Tool presence alone is not invocation evidence.
Add regression tests in the existing coverage gate for omitted tools, altered schemas and wrapper filtering.
A pin update must fail this gate until its changed catalog and functional cases are reconciled.
Do not require a sibling checkout or a network lookup in the offline gate.

Existing E0/restart checks remain valid for their recorded pin. They do not automatically complete the broader C0 release gate.
Core retains ownership of tool behavior and schema evolution; wrapper tests must not fork the engine contract.

## Static Coming soon visual

Use this copy:

> **OpenReading Managed: Coming soon**
>
> Document processing on OpenReading's servers, without managing local compute.
> Planned after the public OSS launch.

The title is “Coming soon”, not “Unavailable”. This is product presentation, not an operational service response.
Show the visual in the README and existing release description or setup/help presentation supported by the client.
If a host offers no suitable in-app surface, its distribution page and installation guide carry the visual; do not invent a host widget or inject advertisements into chat.
No new UI subsystem is needed for this static text.
Use ordinary accessible text rather than an image containing the only readable copy.

There is no action button, signup link, payment prompt, live endpoint, capability check or service registration behind the visual.
Do not put it into MCP tool outputs, retrieved passages, error messages or assistant instructions.
Local errors continue to explain the actual local failure, not advertise a hosted retry.
The visual states no launch date, supported page count, free allowance or token-savings percentage.
If it becomes obsolete, a normal reviewed release updates the copy; no remote configuration mechanism is required.

## No managed components in v1

Do not build or ship:

- A dummy or no-op managed server, endpoint, health route or hosted capability response.
- A managed transport client, configured company processing URL, remote tool registration or feature polling.
- Authentication, account setup, credential fields, upload bridge, billing, credits or spending authorization.
- Dormant managed tools, automatic fallback, signup prompts or model-driven upgrade suggestions.
- A new analytics, waitlist or remote feature-flag subsystem as a condition of this launch.

Inspect the package inventory, client configuration and dependencies for these exclusions.
Verify that displaying the visual and using local tools reads no managed credentials and initiates no managed-service traffic.
Test local operation offline after installation with the required assets present and no company account.
Scope network claims to OpenReading's runtime; the assistant may make its own model requests.
Installation downloads and an explicit user visit to documentation are distinct from document-time network activity.
The existing ban on provider model API trials remains unchanged.

## Launch acceptance and later work

C0 and N3 join the existing installation, license, signing, provenance, retrieval, resource and native-host gates.
They do not replace those gates or make a working development-machine demonstration a distribution pass.
Only explicitly verified application versions and modes receive support claims.
Token savings remain unmeasured unless complete actual-Desktop usage and quality evidence establishes them.

Managed v2 needs a separate product specification after launch, including its account, upload, billing and data-handling contracts.
A future service does not get access to existing local documents merely because this visual shipped.
The OSS launch creates awareness of future intent, not an installed managed-service protocol.

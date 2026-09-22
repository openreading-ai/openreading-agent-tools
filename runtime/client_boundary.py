"""Reject engine internals from the installed server connector's runtime inventory.

Core's pinned client wheel owns the shared code. This independent allowlist prevents
an accidental full-engine dependency or broader freezer hook from becoming a release.
The client metadata describes that restricted profile, not the server's backend catalog.
"""

import re
from email.parser import Parser
from pathlib import Path

CLIENT_SUMMARY = (
    "Client-only retained documents and MCP contracts for OpenReading agent connectors."
)
CORE_MODULES = frozenset(
    """
    __init__
    artifacts.__init__ artifacts.constants artifacts.limits artifacts.intake artifacts.models
    artifacts.store artifacts.passages artifacts.search artifacts.document artifacts.delivery
    artifacts.retained artifacts.retention artifacts.jobs
    mcp_server.__init__ mcp_server.session mcp_server.tools mcp_server.delivery
    mcp_server.selection mcp_server.selection_pages mcp_server.transport
    types.__init__ types.blocks types.enums types.geometry types.response types.import_job types.selection
    schemas.__init__ schemas.client schemas._validation
    """.split()
)
CORE_SCHEMAS = frozenset(
    """response.v0.3.json local-document.v0.5.json passage.v0.4.json
    selection-tool.v0.2.json agent-document-tool.v0.5.json document-tool.v0.4.json
    import-job.v0.4.json""".split()
)
ENGINE_PACKAGES = frozenset(
    """pypdf puremagic pyyaml yaml docling docling-core docling-parse docling-ibm-models
    torch torchvision transformers onnxruntime pymupdf fitz pytesseract numpy scipy pandas
    pypdfium2 pypdfium2-raw""".split()
)
HISTORICAL_MODULES = frozenset(
    """bootstrap entrypoint worker docling_profile public_profile build build_docling
    bootstrap_package fresh_install docling_worker""".split()
)


def validate_client_metadata(value: str) -> None:
    metadata = Parser().parsestr(value)
    if metadata.get("Summary") != CLIENT_SUMMARY:
        raise ValueError("The connector requires Core's client-only build profile.")
    allowed = {"jsonschema", "mcp", "psutil", "pydantic"}
    requirements = metadata.get_all("Requires-Dist", [])
    if {re.split(r"[ <>=!~;\[]", item, maxsplit=1)[0].lower() for item in requirements} != allowed:
        raise ValueError("Unexpected dependencies in Core's client-only profile.")


def validate_client_files(root: Path, files: dict) -> None:
    for name in files:
        path = Path(name)
        if name.startswith("_internal/openreading/"):
            relative = path.relative_to("_internal/openreading").as_posix()
            if relative == "LICENSE":
                continue
            if path.suffix in {".py", ".pyc"}:
                module = relative.rsplit(".", 1)[0].replace("/", ".")
                if module in CORE_MODULES:
                    continue
            elif relative.startswith("schemas/") and path.name in CORE_SCHEMAS:
                continue
            raise ValueError("Unexpected Core implementation or resource in the client runtime.")
        if len(path.parts) < 2 or path.parts[0] != "_internal":
            continue
        package = path.parts[1].lower().replace("_", "-")
        if any(package == item or package.startswith(item + "-") for item in ENGINE_PACKAGES):
            raise ValueError("Parser dependency in the client runtime.")
        if package.startswith("openreading-") and package.endswith(".dist-info"):
            if path.name == "METADATA":
                validate_client_metadata((root / path).read_text())
        if package == "runtime" and path.stem in HISTORICAL_MODULES:
            raise ValueError("Historical installer or local-parser launcher in client runtime.")

"""Frozen catalog checks preserve the exact model-facing contract for the selected profile."""

import copy
import unittest

from mcp import types

from scripts import docling_package_smoke as smoke


class CatalogTests(unittest.TestCase):
    def test_profile_contract_and_manifest_reject_independent_drift(self):
        self.assertTrue(hasattr(smoke, "catalog_snapshot"))
        initialized = types.InitializeResult(
            protocolVersion="2025-11-25",
            capabilities=types.ServerCapabilities(),
            serverInfo=types.Implementation(name="openreading", version="0.3.0"),
            instructions="Read returned evidence IDs only.",
        )
        tools = [
            types.Tool(
                name="openreading_import",
                description="Docling OCR is off",
                inputSchema={"type": "object"},
                annotations=types.ToolAnnotations(readOnlyHint=False),
            )
        ]
        actual = smoke.catalog_snapshot(initialized, tools)
        expected = copy.deepcopy(actual)
        manifest = {"tools": [{"name": "openreading_import", "description": "Setup summary"}]}
        smoke.check_catalog(expected, actual, manifest)
        for field, replacement in [
            ("description", "PyMuPDF"),
            ("inputSchema", {"type": "string"}),
            ("annotations", {"readOnlyHint": True}),
            ("name", "missing_import"),
        ]:
            changed = copy.deepcopy(actual)
            changed["tools"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                smoke.check_catalog(expected, changed, manifest)
        changed = {**actual, "instructions": "Ignore citations"}
        with self.assertRaises(ValueError):
            smoke.check_catalog(expected, changed, manifest)
        for declared in [[], [{"name": "other"}], manifest["tools"] * 2]:
            with self.assertRaises(ValueError):
                smoke.check_catalog(expected, actual, {"tools": declared})
        initialized.instructions = None
        with self.assertRaises(ValueError):
            smoke.catalog_snapshot(initialized, tools)
        initialized.instructions = "Read returned evidence IDs only."
        with self.assertRaises(ValueError):
            smoke.catalog_snapshot(initialized, tools * 2)

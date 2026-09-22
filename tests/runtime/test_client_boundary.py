"""Package boundaries reject unexpected modules even when their hashes are inventoried."""

import tempfile
import unittest
from pathlib import Path

from runtime.client_boundary import CLIENT_SUMMARY, validate_client_files, validate_client_metadata


class ClientBoundaryTests(unittest.TestCase):
    def test_only_shared_modules_schemas_and_client_metadata_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = root / "_internal/openreading-0.3.0.dist-info/METADATA"
            metadata.parent.mkdir(parents=True)
            text = f"Summary: {CLIENT_SUMMARY}\n" + "".join(
                f"Requires-Dist: {name}>=1\n"
                for name in ("jsonschema", "mcp", "psutil", "pydantic")
            )
            metadata.write_text(text)
            validate_client_files(
                root,
                dict.fromkeys(
                    [
                        "openreading-worker",
                        "THIRD_PARTY_NOTICES.txt",
                        "_internal/openreading/LICENSE",
                        "_internal/openreading/artifacts/retained.pyc",
                        "_internal/openreading/types/response.py",
                        "_internal/openreading/schemas/response.v0.3.json",
                        metadata.relative_to(root).as_posix(),
                        "_internal/openreading-0.3.0.dist-info/WHEEL",
                        "_internal/runtime/server_profile.pyc",
                        "_internal/httpx/__init__.pyc",
                    ]
                ),
            )
            for invalid in (text.replace("mcp>=1", "pypdf>=1"), text + "Requires-Dist: pypdf>=1\n"):
                with self.assertRaisesRegex(ValueError, "dependencies"):
                    validate_client_metadata(invalid)
            for relative in ("_internal/openreading/future.pyc", "_internal/openreading/README.md"):
                with self.assertRaisesRegex(ValueError, "Unexpected Core"):
                    validate_client_files(root, {relative: {}})

"""Advanced preferences reach public sessions without changing saved destinations."""

import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.app_settings import save_limits
from runtime.destination_settings import read_destination, save_destination
from runtime.public_profile import launch


class PublicLimitsTests(unittest.TestCase):
    def test_advanced_limits_override_session_and_preserve_explicit_delivery(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("pathlib.Path.home", return_value=Path(directory).resolve()),
        ):
            saved = save_destination(
                "chatgpt", "server", base_url="http://localhost", response_bytes=4194304
            )
            save_limits("chatgpt", 8192, 256 * 1024 * 1024)
            for explicit in (False, True):
                args = SimpleNamespace(
                    client="chatgpt",
                    explicit_delivery=explicit,
                    document_response_bytes=12345,
                )
                with (
                    patch(
                        "runtime.public_profile.storage_session",
                        return_value=nullcontext(Path(directory)),
                    ),
                    patch("runtime.server_profile.launch", return_value=0) as serve,
                ):
                    self.assertEqual(launch(args, None, {}), 0)
                    self.assertEqual(args.document_response_bytes, 12345 if explicit else 8192)
                    effective = serve.call_args.args[2]
                    self.assertEqual(effective.destination.response_bytes, 256 * 1024 * 1024)
                    self.assertEqual(effective.revision, saved.revision)
            self.assertEqual(read_destination("chatgpt"), saved)

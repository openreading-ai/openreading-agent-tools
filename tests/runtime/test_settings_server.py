"""The settings connector opens a fixed native UI without model-supplied configuration."""

import importlib.util
import unittest
from unittest.mock import Mock, patch


class SettingsServerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("runtime.settings_server"), "Missing settings connector"
        )
        from runtime import settings_server

        self.api = settings_server

    def test_opener_reuses_live_child_and_rejects_model_settings(self):
        child = Mock()
        child.poll.return_value = None
        with patch.object(self.api.subprocess, "Popen", return_value=child) as popen:
            opener = self.api.WindowOpener("chatgpt")
            self.assertEqual(opener.open({})["status"], "window_requested")
            opener.open({})
            self.assertEqual(popen.call_count, 1)
            with self.assertRaises(ValueError):
                opener.open({"data_folder": "/injected"})
            child.poll.return_value = 0
            opener.open({})
            self.assertEqual(popen.call_count, 2)
            command = popen.call_args.args[0]
            self.assertEqual(command[-3:], ["--client", "chatgpt", "--destination-settings"])

    def test_invalid_client_cannot_construct_a_command(self):
        with self.assertRaises(ValueError):
            self.api.WindowOpener("unknown")

    def test_frozen_opener_never_adds_source_module_arguments(self):
        with (
            patch.object(self.api.sys, "frozen", True, create=True),
            patch.object(self.api.subprocess, "Popen") as popen,
        ):
            self.api.WindowOpener("codex").open({})
        self.assertEqual(
            popen.call_args.args[0],
            [self.api.sys.executable, "--client", "codex", "--destination-settings"],
        )

    def test_real_mcp_catalog_and_calls_reject_configuration_and_sanitize_launch_errors(self):
        import asyncio

        from mcp.shared.memory import create_connected_server_and_client_session

        async def check():
            with patch.object(self.api.subprocess, "Popen") as popen:
                async with create_connected_server_and_client_session(
                    self.api.create_server("chatgpt")
                ) as client:
                    catalog = await client.list_tools()
                    self.assertEqual([t.name for t in catalog.tools], ["openreading_open_settings"])
                    result = await client.call_tool(
                        "openreading_open_settings", {"token": "injected"}
                    )
                    self.assertTrue(result.isError)
                    popen.assert_not_called()
                    result = await client.call_tool("unknown", {})
                    self.assertTrue(result.isError)
                    popen.side_effect = OSError("secret native diagnostic")
                    result = await client.call_tool("openreading_open_settings", {})
                    self.assertTrue(result.isError)
                    self.assertNotIn("secret", result.content[0].text)
                    popen.side_effect = None
                    result = await client.call_tool("openreading_open_settings", {})
                    self.assertFalse(result.isError)
                    self.assertIn("window_requested", result.content[0].text)

        asyncio.run(check())

    def test_source_entrypoint_routes_ui_or_stdio(self):
        from unittest.mock import AsyncMock

        with (
            patch.object(self.api.sys, "argv", ["settings", "--client", "codex"]),
            patch.object(self.api, "serve", AsyncMock()) as serve,
        ):
            self.assertEqual(self.api.main(), 0)
            serve.assert_awaited_once_with("codex")
        with (
            patch.object(
                self.api.sys, "argv", ["settings", "--client", "codex", "--destination-settings"]
            ),
            patch("runtime.destination_ui.run", return_value=0),
        ):
            self.assertEqual(self.api.main(), 0)

"""Keychain integration is exercised with a fake Security framework, never real secrets."""

import ctypes
import unittest
from unittest.mock import patch

from runtime.server_keychain import ServerKeychain


class Function:
    def __init__(self, operation):
        self.operation = operation

    def __call__(self, *args):
        return self.operation(*args)


class Security:
    def __init__(self):
        self.values = {}
        self.failure = 0
        self.freed = []
        self.SecKeychainAddGenericPassword = Function(self.add)
        self.SecKeychainFindGenericPassword = Function(self.find)
        self.SecKeychainItemFreeContent = Function(lambda *args: self.freed.append(args) or 0)

    def add(self, keychain, service_len, service, account_len, account, size, data, item):
        self.values[account] = ctypes.string_at(data, size)
        return self.failure

    def find(self, keychain, service_len, service, account_len, account, size, data, item):
        if self.failure:
            return self.failure
        self.buffer = ctypes.create_string_buffer(self.values[account])
        size._obj.value = len(self.values[account])
        data._obj.value = ctypes.cast(self.buffer, ctypes.c_void_p).value
        return 0


class KeychainTests(unittest.TestCase):
    def setUp(self):
        self.security = Security()
        with patch("runtime.server_keychain.ctypes.CDLL", return_value=self.security):
            self.keychain = ServerKeychain()

    def test_roundtrip_uses_reference_and_releases_framework_buffer(self):
        self.keychain.put("a" * 32, "synthetic-token")
        self.assertEqual(self.keychain.get("a" * 32), "synthetic-token")
        self.assertEqual(len(self.security.freed), 1)

    def test_rejected_access_does_not_become_anonymous_access(self):
        self.security.failure = -25300
        with self.assertRaisesRegex(ValueError, "Keychain"):
            self.keychain.put("a" * 32, "synthetic-token")
        with self.assertRaisesRegex(ValueError, "Keychain"):
            self.keychain.get("a" * 32)

    def test_reference_and_token_validation(self):
        for reference in ("", "wrong", "../account"):
            with self.assertRaises(ValueError):
                self.keychain.get(reference)
        for token in ("", "has space", "\n", "界", "x" * 4097):
            with self.assertRaises(ValueError):
                self.keychain.put("a" * 32, token)
        self.security.values[b"a" * 32] = b"invalid\xff"
        with self.assertRaises(ValueError):
            self.keychain.get("a" * 32)
        self.assertEqual(len(self.security.freed), 1)
        for value in (b"", b"x" * 4097):
            self.security.values[b"a" * 32] = value
            with self.assertRaises(ValueError):
                self.keychain.get("a" * 32)


if __name__ == "__main__":
    unittest.main()

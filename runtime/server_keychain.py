"""Store optional Core bearer tokens in macOS Keychain without subprocess arguments.

Each setting revision uses an opaque account reference under OpenReading's service name.
Tokens never enter JSON settings, job snapshots, shell commands, or model tool arguments.
Existing references remain immutable so pending jobs can use their approved credential.
After pending jobs finish, Keychain Access can remove entries for ai.openreading.agent-tools.core-server.
Settings stops using a saved token without deleting the immutable item.
Missing items and refused Keychain access fail closed instead of sending anonymously.
The Security framework may ask the owner to unlock or permit credential access.
Native credential prompts and signed-bundle access remain separate acceptance checks.
"""

from __future__ import annotations

import ctypes
import re

SERVICE = b"ai.openreading.agent-tools.core-server"


def _reference(value: str) -> bytes:
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{32}", value) is None:
        raise ValueError("Invalid server Keychain reference.")
    return value.encode("ascii")


def _token(value: str) -> bytes:
    if not isinstance(value, str) or re.fullmatch(r"[\x21-\x7e]{1,4096}", value) is None:
        raise ValueError("Invalid server credential.")
    return value.encode("ascii")


class ServerKeychain:
    def __init__(self):
        self.security = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        pointer, size, text = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p
        common = [pointer, size, text, size, text]
        self.security.SecKeychainAddGenericPassword.argtypes = [*common, size, pointer, pointer]
        self.security.SecKeychainAddGenericPassword.restype = ctypes.c_int32
        self.security.SecKeychainFindGenericPassword.argtypes = [
            *common,
            ctypes.POINTER(size),
            ctypes.POINTER(pointer),
            pointer,
        ]
        self.security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
        self.security.SecKeychainItemFreeContent.argtypes = [pointer, pointer]
        self.security.SecKeychainItemFreeContent.restype = ctypes.c_int32

    def put(self, reference: str, token: str) -> None:
        account, secret = _reference(reference), _token(token)
        status = self.security.SecKeychainAddGenericPassword(
            None,
            len(SERVICE),
            SERVICE,
            len(account),
            account,
            len(secret),
            secret,
            None,
        )
        if status != 0:
            raise ValueError(
                "Keychain could not save the server credential. Settings were not changed."
            )

    def get(self, reference: str) -> str:
        account = _reference(reference)
        length, data = ctypes.c_uint32(), ctypes.c_void_p()
        status = self.security.SecKeychainFindGenericPassword(
            None,
            len(SERVICE),
            SERVICE,
            len(account),
            account,
            ctypes.byref(length),
            ctypes.byref(data),
            None,
        )
        if status != 0:
            raise ValueError("Keychain did not provide the configured server credential.")
        try:
            if not data or not 1 <= length.value <= 4096:
                raise ValueError("Invalid Keychain credential length.")
            value = ctypes.string_at(data, length.value).decode("ascii")
            _token(value)
            return value
        except (ValueError, UnicodeError):
            raise ValueError("Keychain returned an invalid server credential.") from None
        finally:
            self.security.SecKeychainItemFreeContent(None, data)

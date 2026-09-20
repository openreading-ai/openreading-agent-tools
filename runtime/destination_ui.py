"""Let the native user save a destination or test metadata without sending documents.

Blank credentials preserve an existing key only for the identical normalized URL.
Stopping token use selects anonymous access without deleting pending jobs' Keychain items.
Connection checks never save settings. The native user can lower the response download budget.
No model argument supplies settings. Saving does not grant a document or start a server.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from runtime.destination_settings import read_destination, save_destination
from runtime.server_transport import ServerDestination, check_connection


class Controller:
    def __init__(self, client: str, *, home: Path | None = None, keychain=None):
        self.client, self.home, self.keychain = client, home, keychain

    def current(self):
        return read_destination(self.client, home=self.home)

    def save(self, mode, url, token, clear, *, response_mib="128"):
        if (
            not str(response_mib).isascii()
            or not str(response_mib).isdecimal()
            or int(response_mib) < 1
        ):
            raise ValueError("Maximum downloaded response must be a positive whole number of MiB.")
        return save_destination(
            self.client,
            mode,
            base_url=url,
            response_bytes=int(response_mib) * 1024 * 1024,
            token="" if clear else token or None,
            home=self.home,
            keychain=self.keychain,
        )

    def check(self, url, token, clear):
        destination = ServerDestination(url, "settings-preview")
        if clear:
            token = None
        elif not token:
            token = None
            current = self.current()
            if (
                current.destination is not None
                and current.destination.base_url == destination.base_url
                and current.credential_ref
            ):
                keychain = self.keychain
                if keychain is None:
                    from runtime.server_keychain import ServerKeychain

                    keychain = ServerKeychain()
                token = keychain.get(current.credential_ref)
        return asyncio.run(check_connection(destination, token=token))


class SettingsWindow:
    def __init__(self, root, controller, tk, ttk):
        self.root, self.controller = root, controller
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future, self.closing = None, False
        from runtime.destination_settings import DestinationSettings

        status = "Bundled Docling is the default. Saving affects new document selections."
        try:
            current = controller.current()
        except ValueError as error:
            current = DestinationSettings()
            status = str(error)
        root.title("OpenReading Settings")
        root.geometry("720x700")
        root.minsize(680, 680)
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Document processing", font=("Helvetica", 21, "bold")).pack(
            anchor="w"
        )
        self.mode = tk.StringVar(value=current.mode)
        self.url = tk.StringVar(
            value=current.destination.base_url if current.destination else "http://127.0.0.1:8787"
        )
        self.response_mib = tk.StringVar(
            value=str((current.destination.response_bytes + 1024 * 1024 - 1) // (1024 * 1024))
            if current.destination
            else "128"
        )
        self.token = tk.StringVar(value="")
        self.clear = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            frame, text="Bundled Docling on this Mac", variable=self.mode, value="local"
        ).pack(anchor="w", pady=(12, 0))
        ttk.Radiobutton(
            frame, text="Your OpenReading Core server", variable=self.mode, value="server"
        ).pack(anchor="w", pady=(8, 12))
        ttk.Label(frame, text="Server URL").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.url).pack(fill="x", pady=(4, 12))
        ttk.Label(frame, text="Optional server bearer token (stored in macOS Keychain)").pack(
            anchor="w"
        )
        ttk.Entry(frame, textvariable=self.token, show="•").pack(fill="x", pady=(4, 4))
        ttk.Label(frame, text="Leave blank to keep the saved token for the same URL.").pack(
            anchor="w"
        )
        ttk.Checkbutton(frame, text="Stop using saved token", variable=self.clear).pack(
            anchor="w", pady=(4, 12)
        )
        ttk.Label(
            frame,
            text="Old tokens remain in Keychain for pending jobs. Remove them in Keychain Access after those jobs finish.",
            wraplength=650,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(frame, text="Maximum downloaded response (MiB)").pack(anchor="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.response_mib).pack(fill="x", pady=(4, 4))
        ttk.Label(
            frame,
            text="Responses are buffered in memory. Lower this limit to reduce memory use; it is not a memory cap.",
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        ttk.Label(
            frame,
            text="Server mode sends selected file bytes to this URL after your confirmation. The server may use external providers. Start and configure your server separately. Connection checks send no document.",
            wraplength=650,
            justify="left",
        ).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=16)
        self.check_button = ttk.Button(row, text="Test connection", command=self.check)
        self.check_button.pack(side="left")
        self.save_button = ttk.Button(row, text="Save destination", command=self.save)
        self.save_button.pack(side="left", padx=12)
        self.status = tk.StringVar(value=status)
        ttk.Label(frame, textvariable=self.status, wraplength=650, justify="left").pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)

    def save(self):
        try:
            self.controller.save(
                self.mode.get(),
                self.url.get(),
                self.token.get(),
                self.clear.get(),
                response_mib=self.response_mib.get(),
            )
            self.token.set("")
            self.clear.set(False)
            self.status.set(
                "Saved. Restart the plugin connection before selecting documents. Existing jobs keep their original destination."
            )
        except ValueError as error:
            self.status.set(str(error))
        except Exception:
            self.status.set("Cannot save settings. Check local permissions and Keychain access.")

    def check(self):
        self.save_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.status.set("Checking server metadata. No document is sent…")
        self.future = self.executor.submit(
            self.controller.check, self.url.get(), self.token.get(), self.clear.get()
        )
        self.poll()

    def poll(self):
        if not self.future.done():
            self.root.after(50, self.poll)
            return
        try:
            self.future.result()
            self.status.set(
                "Connection and metadata access passed. No document was sent. Parsing still needs a document test."
            )
        except ValueError as error:
            self.status.set(str(error))
        except Exception:
            self.status.set("The connection check failed. Check the URL and Keychain access.")
        self.future = None
        self.save_button.configure(state="normal")
        self.check_button.configure(state="normal")
        if self.closing:
            self.close()

    def close(self):
        if self.future is not None:
            self.closing = True
            self.status.set("Waiting for the bounded connection check to finish…")
            return
        self.executor.shutdown(wait=False)
        self.root.destroy()


def run(client: str) -> int:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    SettingsWindow(root, Controller(client), tk, ttk)
    root.mainloop()
    return 0

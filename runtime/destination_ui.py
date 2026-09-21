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

from runtime.app_settings import Preferences, read_preferences, save_preferences
from runtime.destination_settings import read_destination, save_destination
from runtime.server_transport import ServerDestination, check_connection


class Controller:
    def __init__(self, client: str, *, home: Path | None = None, keychain=None):
        self.client, self.home, self.keychain = client, home, keychain

    def storage_root(self):
        from runtime.storage_settings import data_root

        return data_root(self.client, home=self.home)

    def preferences(self):
        return read_preferences(self.client, home=self.home)

    def save_preferences(self, folder, budget):
        if not str(budget).isascii() or not str(budget).isdecimal():
            raise ValueError("Response budget must be a whole number of bytes.")
        return save_preferences(self.client, Path(folder), int(budget), home=self.home)

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
        tabs = ttk.Notebook(root)
        tabs.pack(fill="both", expand=True, padx=16, pady=16)
        general = ttk.Frame(tabs, padding=20)
        frame = ttk.Frame(tabs, padding=20)
        tabs.add(general, text="Storage and delivery")
        tabs.add(frame, text="Document processing")
        self.preferences_panel(general, controller, tk, ttk)
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
            wraplength=600,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(frame, text="Maximum downloaded response (MiB)").pack(anchor="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=self.response_mib).pack(fill="x", pady=(4, 4))
        ttk.Label(
            frame,
            text="Responses are buffered in memory. Lower this limit to reduce memory use; it is not a memory cap.",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        ttk.Label(
            frame,
            text="Server mode sends selected file bytes to this URL after your confirmation. The server may use external providers. Start and configure your server separately. Connection checks send no document.",
            wraplength=600,
            justify="left",
        ).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=16)
        self.check_button = ttk.Button(row, text="Test connection", command=self.check)
        self.check_button.pack(side="left")
        self.save_button = ttk.Button(row, text="Save destination", command=self.save)
        self.save_button.pack(side="left", padx=12)
        ttk.Button(row, text="Discard changes", command=self.discard_destination).pack(side="left")
        self.status = tk.StringVar(value=status)
        ttk.Label(frame, textvariable=self.status, wraplength=600, justify="left").pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)

    def preferences_panel(self, frame, controller, tk, ttk):
        message = "Changes apply after reconnecting OpenReading. Existing imports must finish before moving data."
        try:
            current = controller.preferences()
        except ValueError as error:
            current = Preferences((controller.home or Path.home()) / ".openreading")
            message = str(error)
        try:
            message += " Current data: " + str(controller.storage_root())
        except ValueError as error:
            message = str(error)
        self.folder = tk.StringVar(value=str(current.data_folder))
        self.budget = tk.StringVar(value=str(current.document_response_bytes))
        self.preference_status = tk.StringVar(value=message)
        ttk.Label(frame, text="OpenReading data", font=("Helvetica", 21, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Selected copies, retained documents and exports live here. Each client has its own partition.",
            wraplength=620,
        ).pack(anchor="w", pady=(12, 8))
        ttk.Label(frame, textvariable=self.folder, wraplength=620).pack(anchor="w", pady=(4, 12))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Choose folder…", command=self.choose_folder).pack(side="left")
        ttk.Button(
            row,
            text="Use default folder",
            command=lambda: self.folder.set(str((controller.home or Path.home()) / ".openreading")),
        ).pack(side="left", padx=12)
        ttk.Label(
            frame,
            text="The next connection copies data into a fresh client partition. The old copy stays intact. Existing OpenReading partitions are never merged or overwritten.",
            wraplength=620,
        ).pack(anchor="w", pady=16)
        ttk.Label(frame, text="Complete result response budget (bytes)").pack(
            anchor="w", pady=(16, 4)
        )
        ttk.Entry(frame, textvariable=self.budget).pack(fill="x")
        ttk.Label(
            frame,
            text="Default: 1000000. Larger results are delivered as files inside the data folder. This does not limit document processing.",
            wraplength=620,
        ).pack(anchor="w", pady=(4, 20))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Save storage and delivery", command=self.save_preferences).pack(
            side="left"
        )
        ttk.Button(row, text="Discard changes", command=self.discard_preferences).pack(
            side="left", padx=12
        )
        ttk.Label(frame, textvariable=self.preference_status, wraplength=620).pack(
            anchor="w", pady=16
        )
        ttk.Label(
            frame,
            text="OCR is automatic with bundled Docling. Source documents still require explicit file selection.",
            wraplength=620,
        ).pack(anchor="w", pady=12)
        ttk.Label(frame, text="OpenReading Managed: Coming soon").pack(anchor="w", pady=12)

    def choose_folder(self):
        from tkinter import filedialog

        selected = filedialog.askdirectory(
            title="Choose OpenReading data folder", parent=self.root, mustexist=True
        )
        if selected:
            self.folder.set(selected)
            self.preference_status.set("Folder selected. Save to request this change.")

    def save_preferences(self):
        try:
            self.controller.save_preferences(self.folder.get(), self.budget.get())
            self.preference_status.set(
                "Saved. Reconnect OpenReading to apply these preferences. The previous data copy stays intact."
            )
        except ValueError as error:
            self.preference_status.set(str(error))
        except Exception:
            self.preference_status.set(
                "Cannot save preferences. Check local permissions and free space."
            )

    def discard_preferences(self):
        try:
            current = self.controller.preferences()
            self.folder.set(str(current.data_folder))
            self.budget.set(str(current.document_response_bytes))
            self.preference_status.set("Unsaved changes discarded.")
        except ValueError as error:
            self.preference_status.set(str(error))

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

    def discard_destination(self):
        try:
            current = self.controller.current()
            self.mode.set(current.mode)
            self.url.set(
                current.destination.base_url if current.destination else "http://127.0.0.1:8787"
            )
            self.response_mib.set(
                str((current.destination.response_bytes + 1024 * 1024 - 1) // (1024 * 1024))
                if current.destination
                else "128"
            )
            self.token.set("")
            self.clear.set(False)
            self.status.set("Unsaved changes discarded.")
        except ValueError as error:
            self.status.set(str(error))

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

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

from runtime.app_settings import (
    Limits,
    read_limits,
    read_preferences,
    save_limits,
    save_preferences,
)
from runtime.destination_settings import read_destination, save_destination
from runtime.server_transport import ServerDestination, check_connection


class Controller:
    def __init__(self, client: str, *, home: Path | None = None, keychain=None):
        self.client, self.home, self.keychain = client, home, keychain

    def storage_root(self):
        from runtime.storage_settings import data_root

        return data_root(self.client, home=self.home)

    def storage_view(self):
        from runtime.storage_settings import storage_view

        return storage_view(self.client, home=self.home)

    def storage_choices(self):
        from runtime.configuration import client_root

        return {
            "application": client_root(self.client, home=self.home).parent,
            "recommended": (self.home or Path.home()) / ".openreading",
        }

    def preferences(self):
        return read_preferences(self.client, home=self.home)

    def save_preferences(self, folder, budget):
        if not str(budget).isascii() or not str(budget).isdecimal():
            raise ValueError("Response budget must be a whole number of bytes.")
        return save_preferences(self.client, Path(folder), int(budget), home=self.home)

    def current(self):
        return read_destination(self.client, home=self.home)

    def limits(self):
        return read_limits(self.client, home=self.home)

    def save_storage(self, folder):
        try:
            budget = self.preferences().document_response_bytes
        except ValueError:
            budget = Limits().document_response_bytes
        return self.save_preferences(folder, str(budget))

    def save_advanced(self, budget, response_mib):
        if not str(budget).isascii() or not str(budget).isdecimal():
            raise ValueError("Response file threshold must be a whole number of bytes.")
        maximum = self.download_bytes(response_mib)
        return save_limits(self.client, int(budget), maximum, home=self.home)

    @staticmethod
    def download_bytes(response_mib):
        if (
            not str(response_mib).isascii()
            or not str(response_mib).isdecimal()
            or int(response_mib) < 1
        ):
            raise ValueError("Maximum downloaded response must be a positive whole number of MiB.")
        return int(response_mib) * 1024 * 1024

    def save(self, mode, url, token, clear, *, response_mib=None):
        maximum = (
            self.download_bytes(response_mib)
            if response_mib is not None
            else self.limits().server_response_bytes
            if mode == "server"
            else Limits().server_response_bytes
        )
        return save_destination(
            self.client,
            mode,
            base_url=url,
            response_bytes=maximum,
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
        advanced = ttk.Frame(tabs, padding=20)
        tabs.add(frame, text="Processing")
        tabs.add(general, text="Storage")
        tabs.add(advanced, text="Advanced")
        self.preferences_panel(general, controller, tk, ttk)
        self.advanced_panel(advanced, controller, tk, ttk)
        ttk.Label(frame, text="Processing", font=("Helvetica", 21, "bold")).pack(anchor="w")
        self.mode = tk.StringVar(value=current.mode)
        self.url = tk.StringVar(
            value=current.destination.base_url if current.destination else "http://127.0.0.1:8787"
        )
        self.token = tk.StringVar(value="")
        self.clear = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            frame,
            text="Bundled Docling on this Mac",
            variable=self.mode,
            value="local",
            command=self.processing_changed,
        ).pack(anchor="w", pady=(12, 0))
        ttk.Radiobutton(
            frame,
            text="Your OpenReading Core server",
            variable=self.mode,
            value="server",
            command=self.processing_changed,
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
            wraplength=570,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(
            frame,
            text="Server mode sends selected file bytes to this URL after your confirmation. The server may use external providers. Start and configure your server separately. Connection checks send no document.",
            wraplength=570,
            justify="left",
        ).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=16)
        self.check_button = ttk.Button(row, text="Test connection", command=self.check)
        self.check_button.pack(side="left")
        self.save_button = ttk.Button(row, text="Save destination", command=self.save)
        self.save_button.pack(side="left", padx=12)
        ttk.Button(row, text="Restore defaults", command=self.restore_destination).pack(side="left")
        self.status = tk.StringVar(value=status)
        self.status_label = ttk.Label(
            frame, textvariable=self.status, wraplength=570, justify="left"
        )
        self.status_label.pack(anchor="w")
        self.neutral_color = self.status_label.cget("foreground")
        # Tk resolves the native background, so feedback stays legible in either appearance.
        dark = sum(root.winfo_rgb(root.cget("background"))) < 3 * 32768
        self.success_color = "#73d18c" if dark else "#176b32"
        self.error_color = "#ff8989" if dark else "#b42318"
        self.update_check_button()
        root.protocol("WM_DELETE_WINDOW", self.close)

    def show_status(self, message, *, outcome=None):
        color = {"success": self.success_color, "error": self.error_color}.get(
            outcome, self.neutral_color
        )
        self.status_label.configure(foreground=color)
        self.status.set(message)

    def update_check_button(self):
        enabled = self.mode.get() == "server" and self.future is None
        self.check_button.configure(state="normal" if enabled else "disabled")

    def processing_changed(self):
        self.update_check_button()
        self.show_status(
            "Bundled Docling runs on this Mac. No server connection is needed."
            if self.mode.get() == "local"
            else "Test your Core server connection before saving the destination."
        )

    def preferences_panel(self, frame, controller, tk, ttk):
        self.storage_folders = controller.storage_choices()
        self.storage_dirty = False
        try:
            view = controller.storage_view()
            folder, message = view["folder"], view["message"]
        except ValueError as error:
            folder = self.storage_folders["recommended"]
            message = str(error)
        self.folder = tk.StringVar(value=str(folder))
        self.storage_choice = tk.StringVar(value=self.storage_kind(folder))
        self.preference_status = tk.StringVar(value=message)
        ttk.Label(frame, text="Storage", font=("Helvetica", 21, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Local directory where OpenReading can store intermediate processing values.",
            wraplength=570,
        ).pack(anchor="w", pady=(12, 8))
        for value, label in (
            ("application", "Application storage"),
            ("recommended", ".openreading (recommended)"),
            ("custom", "Another folder"),
        ):
            ttk.Radiobutton(
                frame,
                text=label,
                variable=self.storage_choice,
                value=value,
                command=self.storage_changed,
            ).pack(anchor="w", pady=3)
        ttk.Label(frame, textvariable=self.folder, wraplength=570).pack(anchor="w", pady=(8, 12))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Choose folder…", command=self.choose_folder).pack(side="left")
        ttk.Button(
            row,
            text="Restore defaults",
            command=self.restore_storage,
        ).pack(side="left", padx=12)
        ttk.Label(
            frame,
            text="Save your choice, then reconnect OpenReading. Existing imports must finish before data moves. The previous copy stays intact.",
            wraplength=570,
        ).pack(anchor="w", pady=16)
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Save storage", command=self.save_storage).pack(side="left")
        self.preference_label = ttk.Label(
            frame, textvariable=self.preference_status, wraplength=570
        )
        self.preference_label.pack(anchor="w", pady=16)
        self.root.after(1500, self.refresh_storage)

    def storage_kind(self, folder):
        return next(
            (key for key, path in self.storage_folders.items() if Path(folder) == path), "custom"
        )

    def storage_changed(self):
        choice = self.storage_choice.get()
        if choice == "custom":
            self.choose_folder()
            return
        self.folder.set(str(self.storage_folders[choice]))
        self.storage_dirty = True
        self.preference_status.set("Unsaved choice. Choose Save storage to apply it.")

    def refresh_storage(self):
        if self.closing:
            return
        if not self.storage_dirty:
            try:
                view = self.controller.storage_view()
                self.folder.set(str(view["folder"]))
                self.storage_choice.set(self.storage_kind(view["folder"]))
                self.preference_status.set(view["message"])
                self.preference_label.configure(
                    foreground=self.error_color if view["state"] == "blocked" else ""
                )
            except Exception:
                self.preference_status.set("Cannot read storage status. Reopen Settings to retry.")
        self.root.after(1500, self.refresh_storage)

    def choose_folder(self):
        from tkinter import filedialog

        selected = filedialog.askdirectory(
            title="Choose OpenReading data folder", parent=self.root, mustexist=True
        )
        if selected:
            self.folder.set(selected)
            self.storage_dirty = True
            self.preference_status.set("Unsaved choice. Choose Save storage to apply it.")
        self.storage_choice.set(self.storage_kind(self.folder.get()))

    def advanced_panel(self, frame, controller, tk, ttk):
        message = "Save applies these limits after reconnecting OpenReading."
        try:
            limits = controller.limits()
        except ValueError as error:
            limits = Limits()
            message = str(error)
        self.budget = tk.StringVar(value=str(limits.document_response_bytes))
        self.response_mib = tk.StringVar(
            value=str((limits.server_response_bytes + 1048575) // 1048576)
        )
        self.advanced_status = tk.StringVar(value=message)
        ttk.Label(frame, text="Advanced", font=("Helvetica", 21, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Max size of response before writing files in storage for Claude to use (bytes)",
            wraplength=570,
            justify="left",
        ).pack(anchor="w", pady=(20, 4))
        ttk.Entry(frame, textvariable=self.budget).pack(fill="x")
        ttk.Label(
            frame,
            text="Default: 1000000 bytes. Larger responses are saved as files in your storage directory for Claude to use.",
            wraplength=570,
            justify="left",
        ).pack(anchor="w", pady=(4, 20))
        ttk.Label(frame, text="Maximum downloaded response (MiB)").pack(anchor="w")
        ttk.Entry(frame, textvariable=self.response_mib).pack(fill="x", pady=(4, 4))
        ttk.Label(
            frame,
            text="Default: 256 MiB. Applies to Core server responses. Larger downloads stop with an error.",
            wraplength=570,
            justify="left",
        ).pack(anchor="w", pady=(4, 20))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Save advanced settings", command=self.save_advanced).pack(side="left")
        ttk.Button(row, text="Restore defaults", command=self.restore_advanced).pack(
            side="left", padx=12
        )
        ttk.Label(frame, textvariable=self.advanced_status, wraplength=570, justify="left").pack(
            anchor="w", pady=16
        )

    def save_advanced(self):
        try:
            self.controller.save_advanced(self.budget.get(), self.response_mib.get())
            self.advanced_status.set("Saved. Reconnect OpenReading to apply these limits.")
        except ValueError as error:
            self.advanced_status.set(str(error))
        except Exception:
            self.advanced_status.set(
                "Cannot save Advanced settings. Check local permissions and free space."
            )

    def restore_advanced(self):
        self.budget.set(str(Limits().document_response_bytes))
        self.response_mib.set(str(Limits().server_response_bytes // 1048576))
        self.advanced_status.set(
            "Advanced defaults restored. Choose Save advanced settings to apply them."
        )

    def save_storage(self):
        try:
            self.controller.save_storage(self.folder.get())
            self.storage_dirty = False
            self.preference_status.set(self.controller.storage_view()["message"])
        except ValueError as error:
            self.preference_status.set(str(error))
        except Exception:
            self.preference_status.set(
                "Cannot save preferences. Check local permissions and free space."
            )

    def restore_storage(self):
        self.folder.set(str((self.controller.home or Path.home()) / ".openreading"))
        self.storage_choice.set("recommended")
        self.storage_dirty = True
        self.preference_status.set("Storage default restored. Choose Save storage to apply it.")

    def save(self):
        try:
            self.controller.save(
                self.mode.get(),
                self.url.get(),
                self.token.get(),
                self.clear.get(),
            )
            self.token.set("")
            self.clear.set(False)
            self.show_status(
                "Saved. Restart the plugin connection before selecting documents. Existing jobs keep their original destination."
            )
        except ValueError as error:
            self.show_status(str(error))
        except Exception:
            self.show_status("Cannot save settings. Check local permissions and Keychain access.")

    def restore_destination(self):
        self.mode.set("local")
        self.url.set("http://127.0.0.1:8787")
        self.token.set("")
        self.clear.set(True)
        self.update_check_button()
        self.show_status("Processing defaults restored. Choose Save destination to apply them.")

    def check(self):
        if self.mode.get() != "server" or self.future is not None:
            return
        self.save_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.show_status("Checking server metadata. No document is sent…")
        self.checked_values = (self.url.get(), self.token.get(), self.clear.get())
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
            self.show_status(
                "Connection and metadata access passed. No document was sent. Parsing still needs a document test.",
                outcome="success",
            )
        except ValueError as error:
            self.show_status(str(error), outcome="error")
        except Exception:
            self.show_status(
                "The connection check failed. Check the URL and Keychain access.", outcome="error"
            )
        self.future = None
        self.save_button.configure(state="normal")
        self.update_check_button()
        if self.mode.get() != "server":
            self.processing_changed()
        elif self.checked_values != (self.url.get(), self.token.get(), self.clear.get()):
            self.show_status("Server settings changed during the check. Test the connection again.")
        if self.closing:
            self.close()

    def close(self):
        if self.future is not None:
            self.closing = True
            self.show_status("Waiting for the bounded connection check to finish…")
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

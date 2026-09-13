"""Select a local document and explicitly copy its reference for an assistant conversation.

The native picker supplies the sole source path. No chat attachment or provider API is
used. Copying runs off the UI thread; Cancel and Close request cancellation and wait for
cleanup before closing. A failed replacement preserves the previous completed selection.
The GUI does not change OCR or host settings. The connector controls its own OCR setting.
This development interface does not establish signed or clean-machine installation.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from runtime.selection import SelectionError, SelectionStore


class Controller:
    def __init__(self, store: SelectionStore):
        self.store = store
        self.selection = None

    def choose(self, path: str, *, cancelled=lambda: False):
        if not path:
            return None
        result = self.store.select(Path(path), cancelled=cancelled)
        self.selection = result
        return result

    def copy(self, write_clipboard):
        if self.selection is None:
            raise SelectionError("Select a document first.")
        write_clipboard(self.selection.prompt)

    def remove(self):
        if self.selection is not None:
            self.store.remove(self.selection.reference)
            self.selection = None


class Picker:
    def __init__(self, root, store, tk, ttk, filedialog):
        self.root = root
        self.controller = Controller(store)
        self.filedialog = filedialog
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.cancelled = Event()
        self.closing = False
        root.title("OpenReading | Choose a document")
        root.geometry("700x390")
        root.minsize(620, 360)
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Read a local document", font=("Helvetica", 21, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            frame,
            text="Choose one PDF. OpenReading keeps a local copy; only retrieved evidence enters your assistant's context.\nYour source folder is not granted. OCR uses your connector setting and can misread printed text.",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(12, 16))
        self.choose_button = ttk.Button(frame, text="Choose document…", command=self.choose)
        self.choose_button.pack(anchor="w")
        self.status = tk.StringVar(
            value="Select a document, then copy its reference into your chat."
        )
        ttk.Label(frame, textvariable=self.status, wraplength=640).pack(anchor="w", pady=(16, 10))
        self.reference = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.reference, state="readonly").pack(fill="x")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=12)
        self.copy_button = ttk.Button(
            row, text="Copy reference", command=self.copy, state="disabled"
        )
        self.copy_button.pack(side="left")
        self.remove_button = ttk.Button(
            row, text="Remove selected copy", command=self.remove, state="disabled"
        )
        self.remove_button.pack(side="left", padx=8)
        self.cancel_button = ttk.Button(
            row, text="Cancel copy", command=self.cancel, state="disabled"
        )
        self.cancel_button.pack(side="left")
        ttk.Label(
            frame,
            text="Removing a selected copy does not delete previously retained evidence. Development preview.",
            wraplength=640,
        ).pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)

    def state(self, busy):
        self.choose_button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        enabled = not busy and self.controller.selection is not None
        for button in (self.copy_button, self.remove_button):
            button.configure(state="normal" if enabled else "disabled")

    def choose(self):
        path = self.filedialog.askopenfilename(
            parent=self.root,
            title="Choose a local document",
            filetypes=[("PDF documents", "*.pdf")],
        )
        if not path:
            return
        self.cancelled.clear()
        self.state(True)
        self.status.set("Copying the selected document locally…")
        self.future = self.executor.submit(
            self.controller.choose, path, cancelled=self.cancelled.is_set
        )
        self.poll()

    def poll(self):
        if not self.future.done():
            self.root.after(50, self.poll)
            return
        try:
            result = self.future.result()
            self.reference.set(result.reference)
            self.status.set("Ready. Copy the reference into your chat and add your question.")
        except SelectionError as error:
            self.status.set(str(error))
        except Exception:
            self.status.set(
                "Cannot prepare this document. Check permissions and available disk space."
            )
        self.future = None
        self.state(False)
        if self.closing:
            self.close()

    def copy(self):
        def write(text):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

        self.controller.copy(write)
        self.status.set(
            "Reference copied. Paste it into your assistant chat and add your question."
        )

    def remove(self):
        try:
            self.controller.remove()
            self.reference.set("")
            self.status.set("Selected copy removed. Previously retained evidence is unchanged.")
        except SelectionError as error:
            self.status.set(str(error))
        self.state(False)

    def cancel(self):
        self.cancelled.set()
        self.status.set("Cancelling the local copy…")

    def close(self):
        if self.future is not None:
            self.closing = True
            self.cancel()
            return
        self.executor.shutdown(wait=False)
        self.root.destroy()


def run(store: SelectionStore) -> int:
    import tkinter as tk
    from tkinter import filedialog, ttk

    root = tk.Tk()
    Picker(root, store, tk, ttk, filedialog)
    root.mainloop()
    return 0

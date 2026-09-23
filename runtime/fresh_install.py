"""Install a verified runtime in Application Support and back up Claude's prior state.

The setup shell copies the bundle out of Downloads before running this module. Runtime
versions are immutable and keyed by executable hash. Claude owns plugin registration.
Fresh setup moves only Claude's control directory and default data partition into a
private backup. Custom data directories and other clients remain intact.
Active workers, locked connections and unfinished jobs refuse setup. Failed backup moves
roll back in reverse order; an already installed, verified runtime can remain for retry.
No interpreter installation, model download, host-config edit or permission change occurs.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from openreading.artifacts.intake import directory
from openreading.artifacts.store import safe_read

from runtime.app_settings import write_private
from runtime.configuration import client_root
from runtime.storage_settings import data_root
from runtime.verify import verify_release


def running_workers():
    result = subprocess.run(
        ["/bin/ps", "-axo", "pid=,args="], capture_output=True, text=True, check=True
    )
    for line in result.stdout.splitlines():
        pid, _, command = line.strip().partition(" ")
        if pid == str(os.getpid()) or "openreading-worker" not in command:
            continue
        if re.search(
            r"--client\s+claude-desktop(?:\s|$)|--internal-(?:server|artifact)-(?:job|worker)",
            command,
        ):
            return True
    return False


def install(runtime: Path, *, home: Path | None = None):
    home = home or Path.home()
    metadata = verify_release(runtime)
    if running_workers():
        raise ValueError(
            "Quit Claude and close OpenReading windows before running fresh setup. Finish or cancel imports first."
        )
    control = client_root("claude-desktop", home=home)
    base = control.parent
    default = home / ".openreading/clients/claude-desktop/v2"
    active = data_root("claude-desktop", home=home)
    for root in {active, default}:
        if root.exists() or root.is_symlink():
            with directory(root):
                for job in (root / "artifacts/jobs").glob("*/*"):
                    value = json.loads(safe_read(job / "status.json", 65536))
                    if not isinstance(value, dict) or value.get("state") not in {
                        "succeeded",
                        "failed",
                        "cancelled",
                    }:
                        raise ValueError(
                            "Finish or cancel existing OpenReading imports before fresh setup."
                        )
    with directory(base, create=True):
        cache = base / "runtime-cache"
        with directory(cache, create=True):
            target = cache / metadata["worker_sha256"]
            if target.exists() or target.is_symlink():
                with directory(target):
                    if verify_release(target) != metadata:
                        raise ValueError(
                            "The installed runtime differs from this build. Existing files were preserved."
                        )
            else:
                stage = cache / (".install-" + uuid.uuid4().hex)
                try:
                    shutil.copytree(runtime, stage, symlinks=True)
                    verify_release(stage)
                    stage.rename(target)
                finally:
                    if stage.exists():
                        shutil.rmtree(stage)
        backup = base / "fresh-install-backups" / uuid.uuid4().hex
        with directory(backup, create=True):
            pass
        moves = []
        lock = None
        try:
            if control.exists() or control.is_symlink():
                with directory(control) as parent:
                    lock = os.open(
                        "storage.lock", os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR, 0o600, dir_fd=parent
                    )
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        raise ValueError(
                            "Close the OpenReading document connection before fresh setup."
                        ) from None
            for original, name in ((control, "settings"), (default, "default-data")):
                if original.exists() or original.is_symlink():
                    with directory(original):
                        original.rename(backup / name)
                    moves.append((original, backup / name))
            receipt = {
                "runtime": str(target),
                "backup": str(backup),
                "worker_sha256": metadata["worker_sha256"],
                "backups": [{"original": str(a), "backup": str(b)} for a, b in moves],
                "custom_data_preserved": str(active)
                if active not in {default, control / "v2"}
                else None,
            }
            write_private(backup / "receipt.json", receipt)
            return receipt
        except BaseException:
            for original, saved in reversed(moves):
                saved.rename(original)
            raise
        finally:
            if lock is not None:
                os.close(lock)

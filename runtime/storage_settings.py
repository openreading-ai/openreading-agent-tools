"""Switch client storage at reconnect without deleting the previous retained copy.

A shared control-directory lock covers each document connection. Migration needs exclusive
ownership and terminal import jobs. The target client partition must not already exist;
merging independent stores could mix grants. Files are copied before the active pointer
changes. Failures remove only the newly reserved partition and keep the old pointer.
Core binds evidence to the intake path and inode. Only the copied private intake grant
is rebound; unrelated developer grants and artifact identifiers remain unchanged.
Previously returned export paths continue to refer to the retained original copy.
Legacy Downloads exports stay at their published paths. New exports live in this data root.
An existing installation keeps its active location until preferences are explicitly saved,
so unfinished historical jobs remain reachable after upgrading.
Application storage keeps the historical client partition. Other folders use clients/CLIENT/v2.
New launch profiles hold a lease. Legacy profiles are checked against live document-worker processes;
an abandoned file is never a permanent migration lock. Ephemeral launch files are not copied.
Failed moves persist a target-bound status for Settings without replacing the saved preference.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path

from openreading.artifacts.intake import directory, source
from openreading.artifacts.limits import ArtifactError
from openreading.artifacts.store import safe_read

from runtime.app_settings import read_preferences, write_private
from runtime.configuration import client_root


def folder_root(client, folder, *, home=None):
    control = client_root(client, home=home)
    return control / "v2" if folder == control.parent else folder / "clients" / client / "v2"


def desired_root(client, *, home=None):
    return folder_root(client, read_preferences(client, home=home).data_folder, home=home)


def data_root(client, *, home=None):
    control = client_root(client, home=home)
    path = control / "storage.json"
    if path.exists() or path.is_symlink():
        try:
            value = json.loads(safe_read(path, 16384))
            if (
                not isinstance(value, dict)
                or set(value) != {"schema_version", "active_root"}
                or type(value["schema_version"]) is not int
                or value["schema_version"] != 1
                or not isinstance(value["active_root"], str)
            ):
                raise ValueError
            root = Path(value["active_root"])
            if not root.is_absolute() or ".." in root.parts or "\x00" in str(root):
                raise ValueError
            return root
        except (ValueError, OSError, ArtifactError):
            raise ValueError(
                "Cannot read the active data location. Restore the storage control record before continuing."
            ) from None
    legacy = control / "v2"
    return legacy if legacy.exists() else desired_root(client, home=home)


def storage_view(client, *, home=None):
    """Return the saved choice and applied state without requesting a storage move."""
    control = client_root(client, home=home)
    active = data_root(client, home=home)
    active_folder = control.parent if active == control / "v2" else active.parents[2]
    folder = (
        read_preferences(client, home=home).data_folder
        if (control / "preferences.json").exists()
        else active_folder
    )
    target = folder_root(client, folder, home=home)
    state, message = "active", "Using this folder."
    if active != target:
        state, message = (
            "pending",
            f"Move pending. Reconnect OpenReading to apply it. Still using: {active_folder}",
        )
        status = control / "storage-status.json"
        if status.exists():
            value = json.loads(safe_read(status, 16384))
            if not isinstance(value, dict):
                raise ValueError("Cannot read storage move status. Reconnect OpenReading to retry.")
            if value.get("target") == str(target) and isinstance(value.get("error"), str):
                state = "blocked"
                message = f"Move blocked: {value['error']} Saved choice retained. Still using: {active_folder}"
    return {"folder": folder, "state": state, "message": message}


def copy_tree(old, new, *, skip_launch=False):
    """Copy regular files through checked descriptors; links never become retained inputs."""
    with directory(old):
        for entry in old.iterdir():
            if skip_launch and entry.name == "launch":
                continue
            info = entry.lstat()
            target = new / entry.name
            if stat.S_ISDIR(info.st_mode):
                target.mkdir(mode=0o700)
                copy_tree(entry, target)
            elif stat.S_ISREG(info.st_mode):
                with source(old, entry.name) as fd, os.fdopen(os.dup(fd), "rb") as reader:
                    with target.open("xb") as writer:
                        os.chmod(target, 0o600)
                        shutil.copyfileobj(reader, writer, 1024 * 1024)
                        writer.flush()
                        os.fsync(writer.fileno())
            else:
                raise ValueError("Data migration refuses symbolic links and special files.")


def grant_id(path):
    from openreading.artifacts.limits import ProfileConfig
    from openreading.artifacts.store import Store

    store = Store(ProfileConfig(path, path.parent.parent / "artifacts"))
    try:
        return store.grant
    finally:
        close = getattr(store, "close", None)
        if close:
            close()


def profile_in_use(profile):
    lease = profile.parent / "session.lock"
    if lease.exists():
        fd = os.open(lease, os.O_RDWR | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            return False
        finally:
            os.close(fd)
    # Historical launchers recorded no owner and closed the JSON before serving.
    # Check known client workers conservatively; profile age cannot establish liveness.
    try:
        result = subprocess.run(
            ["/bin/ps", "-axo", "pid=,command="],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError(
            "Cannot verify an older OpenReading connection. Close older OpenReading apps and retry."
        ) from None
    if result.returncode or result.stderr.strip():
        raise ValueError(
            "Cannot verify an older OpenReading connection. Close older OpenReading apps and retry."
        )
    client = re.escape(profile.parents[3].name)
    saw_self = False
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        if int(parts[0]) == os.getpid():
            saw_self = True
            continue
        command = parts[1]
        prefix = command.split(" --client ", 1)[0]
        document_worker = (
            prefix.endswith("openreading-worker")
            and re.search(r"--client " + client + r"(?: |$)", command)
            and "--settings-tools" not in command
            and "--destination-settings" not in command
            and "--internal-" not in command
        )
        if str(profile) in command or document_worker:
            return True
    if not saw_self:
        raise ValueError(
            "Cannot verify an older OpenReading connection. Close older OpenReading apps and retry."
        )
    return False


def check_idle(root):
    if any(profile_in_use(path) for path in (root / "launch").glob("*/profile.json")):
        raise ValueError("Close the existing OpenReading document connection before moving data.")
    for job in (root / "artifacts/jobs").glob("*/*"):
        value = json.loads(safe_read(job / "status.json", 65536))
        if not isinstance(value, dict) or value.get("state") not in {
            "succeeded",
            "failed",
            "cancelled",
        }:
            raise ValueError(
                "Finish or cancel existing imports before moving data. Keep the current data folder until they finish."
            )


def rebind_intake(old, new):
    original = old / "selection/ready"
    if not original.exists():
        return
    before, after = grant_id(original), grant_id(new / "selection/ready")
    for group in ("documents", "jobs"):
        source_group = new / "artifacts" / group / before
        if not source_group.exists():
            continue
        target_group = source_group.with_name(after)
        if target_group.exists():
            try:
                target_group.rmdir()
            except OSError:
                raise ValueError(
                    "The migrated intake conflicts with another retained grant."
                ) from None
        source_group.rename(target_group)
        for path in target_group.glob(
            "*/manifest.json" if group == "documents" else "*/request.json"
        ):
            value = json.loads(safe_read(path, 1024 * 1024))
            if group == "documents":
                if value.get("input_grant_sha256") != before:
                    raise ValueError("The retained document grant is inconsistent.")
                value["input_grant_sha256"] = after
            else:
                if value.get("grant") != before:
                    raise ValueError("The retained import grant is inconsistent.")
                value.update(
                    grant=after,
                    input_root=str(new / "selection/ready"),
                    artifact_root=str(new / "artifacts"),
                )
            write_private(path, value)


def migrate(old, new):
    if old == new:
        with directory(new, create=True):
            pass
        return
    if old in new.parents or new in old.parents:
        raise ValueError("Choose a data folder outside the current client partition.")
    if old.exists():
        check_idle(old)
    with directory(new.parent, create=True):
        try:
            new.mkdir(mode=0o700)
        except FileExistsError:
            raise ValueError(
                "That folder already contains an OpenReading client partition. Choose a fresh folder; stores are never merged."
            ) from None
    try:
        if old.exists():
            copy_tree(old, new, skip_launch=True)
            rebind_intake(old, new)
    except BaseException:
        shutil.rmtree(new)
        raise


@contextmanager
def storage_session(client, *, home=None):
    connected = False
    try:
        with _storage_session(client, home=home) as root:
            connected = True
            yield root
    except ValueError as error:
        if not connected:
            try:
                write_private(
                    client_root(client, home=home) / "storage-status.json",
                    {
                        "target": str(desired_root(client, home=home)),
                        "error": str(error),
                    },
                )
            except (OSError, ValueError, ArtifactError):
                pass
        raise


@contextmanager
def _storage_session(client, *, home=None):
    control = client_root(client, home=home)
    with directory(control, create=True) as parent:
        fd = os.open("storage.lock", os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR, 0o600, dir_fd=parent)
        try:
            old, new = data_root(client, home=home), desired_root(client, home=home)
            if not (control / "preferences.json").exists() and old.exists():
                new = old
            try:
                fcntl.flock(fd, (fcntl.LOCK_EX if old != new else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError(
                    "Close the other OpenReading document connection before applying this data-folder change."
                ) from None
            # Another launcher may have completed migration before this lock was acquired.
            old = data_root(client, home=home)
            if old != new:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise ValueError(
                        "Close the other OpenReading document connection before moving data."
                    ) from None
            migrate(old, new)
            try:
                write_private(
                    control / "storage.json", {"schema_version": 1, "active_root": str(new)}
                )
            except BaseException:
                if old != new and data_root(client, home=home) != new:
                    shutil.rmtree(new)
                raise
            fcntl.flock(fd, fcntl.LOCK_SH)
            yield new
        except (OSError, ArtifactError):
            raise ValueError(
                "Cannot switch the data folder. The previous copy remains intact; check permissions and free space."
            ) from None
        finally:
            os.close(fd)

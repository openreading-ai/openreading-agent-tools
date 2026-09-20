"""Generate a macOS first-use runtime launcher, shared by client wrappers.

The plugin contains this launcher, not Python, Docling, or model weights. First use
fetches the complete pinned runtime over HTTPS and checks its length and SHA-256
before extraction. Complete private cache directories are published atomically, so
concurrent starts cannot expose partial downloads or strand a setup lock. Every
start pins the inventory and worker before the worker verifies its full inventory.

Setup does not read or change destination settings. The same worker selects default
local Docling or the explicitly saved Core-server destination. Settings invocation
uses the same cache. No fallback destination is introduced by runtime acquisition.
A network or integrity failure exits before tools start. Native startup deadlines,
visible setup feedback, and signing require separate owner-operated acceptance.
"""

from __future__ import annotations

import shlex


def launcher(
    metadata: dict, release_digest: str, download: dict, *, client: str = "claude-desktop"
) -> str:
    return f"""#!/bin/sh
set -eu
umask 077
if [ "$(/usr/bin/uname -s)" != Darwin ] || [ "$(/usr/bin/uname -m)" != arm64 ]; then
    printf '%s\\n' 'This OpenReading runtime requires macOS on Apple Silicon.' >&2
    exit 1
fi
root="$HOME/Library/Application Support/OpenReading/agent-tools/runtime-cache"
cache="$root/{release_digest}"
stage=''
cleanup() {{
    # A signal immediately after publication must not delete the active runtime.
    if [ -n "$stage" ] && [ "$(/usr/bin/readlink "$cache" 2>/dev/null || :)" != "$stage/runtime" ]; then
        /bin/rm -rf "$stage"
    fi
}}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
/bin/mkdir -p "$root"
if [ -e "$cache" ] && [ ! -L "$cache" ]; then
    printf '%s\\n' 'OpenReading runtime cache has an unexpected entry.' >&2
    exit 1
fi
if [ -L "$cache" ] && [ ! -e "$cache" ]; then
    printf '%s\\n' 'OpenReading runtime cache is incomplete. Remove this broken runtime cache entry and reconnect.' >&2
    exit 1
fi
if [ ! -e "$cache" ]; then
    printf '%s\\n' 'OpenReading first-use setup: downloading its local runtime ({download["length"]} bytes). No documents are sent. If startup times out, reconnect to retry.' >&2
    stage=$(/usr/bin/mktemp -d "$root/.runtime.XXXXXX")
    payload="$stage/payload.tar.gz"
    /usr/bin/curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' --connect-timeout 20 --max-time 900 --max-filesize {download["length"]} --output "$payload" {shlex.quote(download["url"])}
    actual=$(/usr/bin/shasum -a 256 "$payload")
    actual=${{actual%% *}}
    length=$(/usr/bin/wc -c < "$payload")
    if [ "$actual" != {shlex.quote(download["sha256"])} ] || [ "$length" -ne {download["length"]} ]; then
        printf '%s\\n' 'OpenReading runtime checksum or length failed. Setup did not complete.' >&2
        exit 1
    fi
    /bin/mkdir "$stage/runtime"
    /usr/bin/tar -xzf "$payload" -C "$stage/runtime"
    /bin/rm "$payload"
    # Validate executable identity before publishing; its own inventory check follows.
    actual=$(/usr/bin/shasum -a 256 "$stage/runtime/openreading-worker")
    actual=${{actual%% *}}
    manifest=$(/usr/bin/shasum -a 256 "$stage/runtime/release.json")
    manifest=${{manifest%% *}}
    if [ "$actual" != {shlex.quote(metadata["worker_sha256"])} ] || [ "$manifest" != {shlex.quote(release_digest)} ] || [ ! -x "$stage/runtime/openreading-worker" ]; then
        printf '%s\\n' 'OpenReading downloaded runtime identity or permissions failed.' >&2
        exit 1
    fi
    if /bin/ln -s -n "$stage/runtime" "$cache" 2>/dev/null; then
        stage=''
    else
        cleanup
        stage=''
    fi
fi
worker="$cache/openreading-worker"
actual=$(/usr/bin/shasum -a 256 "$worker")
actual=${{actual%% *}}
manifest=$(/usr/bin/shasum -a 256 "$cache/release.json")
manifest=${{manifest%% *}}
if [ "$actual" != {shlex.quote(metadata["worker_sha256"])} ] || [ "$manifest" != {shlex.quote(release_digest)} ]; then
    printf '%s\\n' 'OpenReading cached runtime checksum failed.' >&2
    exit 1
fi
exec "$worker" --client {shlex.quote(client)} "$@"
"""

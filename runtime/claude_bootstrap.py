"""Generate a macOS first-use launcher without executing setup during packaging.

Only the pinned layout model is downloaded, over HTTPS, with exact size and SHA-256
checks. The remaining runtime ships in the plugin. Complete private cache directories
are published through an atomic symlink, so concurrent starts cannot expose partial
models or strand a setup lock. The frozen worker still verifies its full inventory.
A network or checksum failure exits before tools start. Host startup deadlines and
visible setup feedback require native acceptance, not a shell-test inference.
"""

from __future__ import annotations

import shlex


def launcher(metadata: dict, release_digest: str, url: str, model_path: str) -> str:
    model = metadata["files"][model_path]
    executable_paths = [name for name, item in metadata["files"].items() if item.get("executable")]
    modes = "\n".join('/bin/chmod 700 "$stage"/' + shlex.quote(name) for name in executable_paths)
    return f"""#!/bin/sh
set -eu
umask 077
plugin=$(/usr/bin/dirname "$0")
root="$HOME/Library/Application Support/OpenReading/agent-tools/runtime-cache"
cache="$root/{release_digest}"
stage=''
cleanup() {{
    if [ -n "$stage" ]; then /bin/rm -rf "$stage"; fi
}}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
/bin/mkdir -p "$root"
if [ -e "$cache" ] && [ ! -L "$cache" ]; then
    printf '%s\\n' 'OpenReading runtime cache has an unexpected entry.' >&2
    exit 1
fi
if [ ! -e "$cache" ]; then
    printf '%s\\n' 'OpenReading first-use setup: downloading its pinned layout model (171 MB). No documents are sent.' >&2
    stage=$(/usr/bin/mktemp -d "$root/.runtime.XXXXXX")
    /bin/cp -R "$plugin/server/." "$stage/"
    model="$stage"/{shlex.quote(model_path)}
    /usr/bin/curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' --connect-timeout 20 --max-time 300 --max-filesize {model["length"]} --output "$model" {shlex.quote(url)}
    actual=$(/usr/bin/shasum -a 256 "$model")
    actual=${{actual%% *}}
    length=$(/usr/bin/wc -c < "$model")
    if [ "$actual" != {shlex.quote(model["sha256"])} ] || [ "$length" -ne {model["length"]} ]; then
        printf '%s\\n' 'OpenReading layout model checksum or length failed. Setup did not complete.' >&2
        exit 1
    fi
    {modes}
    if /bin/ln -s -n "$stage" "$cache" 2>/dev/null; then
        stage=''
    else
        cleanup
        stage=''
    fi
fi
worker="$cache/openreading-worker"
actual=$(/usr/bin/shasum -a 256 "$worker")
actual=${{actual%% *}}
if [ "$actual" != {shlex.quote(metadata["worker_sha256"])} ]; then
    printf '%s\\n' 'OpenReading cached worker checksum failed.' >&2
    exit 1
fi
exec "$worker" --client claude-desktop "$@"
"""

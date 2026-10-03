#!/usr/bin/env bash
set -euo pipefail

SDK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK_FILE="$SDK_ROOT/upstream.lock.json"
UPSTREAM_DIR="$SDK_ROOT/upstream/codec2"

lock_value() {
    local key="$1"
    python3 - "$LOCK_FILE" "$key" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
key = sys.argv[2]
with path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)
value = data[key]
if not isinstance(value, str) or not value:
    raise SystemExit(f"invalid {key!r} in {path}")
print(value)
PY
}

platform_id() {
    local os arch
    case "$(uname -s)" in
        Linux) os="linux" ;;
        Darwin) os="macos" ;;
        *) echo "unsupported operating system: $(uname -s)" >&2; return 2 ;;
    esac
    case "$(uname -m)" in
        x86_64|amd64) arch="x86_64" ;;
        aarch64|arm64) arch="aarch64" ;;
        *) arch="$(uname -m)" ;;
    esac
    printf '%s-%s\n' "$os" "$arch"
}

parallel_jobs() {
    if [[ -n "${JOBS:-}" ]]; then
        printf '%s\n' "$JOBS"
    elif command -v nproc >/dev/null 2>&1; then
        nproc
    elif command -v sysctl >/dev/null 2>&1; then
        sysctl -n hw.ncpu
    else
        printf '2\n'
    fi
}

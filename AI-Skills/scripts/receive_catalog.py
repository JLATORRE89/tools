"""Apply a catalog snapshot on Linux, preserving unexpected local edits."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def destination(root, name):
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute() or ".." in relative.parts
            or "\\" in name or str(relative) != name):
        raise ValueError(f"Invalid catalog path: {name!r}")
    target = root.joinpath(*relative.parts)
    if target.resolve() != target or target.is_symlink():
        raise ValueError(f"Symlink in catalog path: {name}")
    return target


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".catalog-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_snapshot(payload, root, state):
    import fcntl

    root = Path(root).absolute()
    state = Path(state).absolute()
    if root.resolve() != root or state.resolve() != state:
        raise ValueError("Catalog and state directories must not be symlinks")
    root.mkdir(parents=True, exist_ok=True)
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / "sync.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return apply_locked(payload, root, state)


def apply_locked(payload, root, state):
    if payload.get("version") != 1 or not isinstance(payload.get("files"), dict):
        raise ValueError("Unsupported catalog snapshot")
    files = {}
    for name, item in payload["files"].items():
        destination(root, name)
        if name.startswith(".") or ("/" not in name and name != "README.md"):
            raise ValueError(f"Not a managed catalog file: {name}")
        data = base64.b64decode(item["data"], validate=True)
        if digest(data) != item["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}")
        files[name] = data
    if "README.md" not in files:
        raise ValueError("Snapshot has no catalog")
    catalog = files["README.md"].decode("utf-8")
    for link in re.findall(r"\]\(([^)]+)\)", catalog):
        if link.startswith(("https://", "http://", "#")):
            continue
        if link not in files:
            raise ValueError(f"Catalog references a missing file: {link}")

    manifest_path = state / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())["files"]
    else:
        # Adopt only files that still match the earlier, verified installation.
        receipt = root / "INSTALLATION.json"
        installed = json.loads(receipt.read_text()).get("files", []) if receipt.exists() else []
        previous = {}
        for item in installed:
            installed_path = Path(item["path"])
            if installed_path.is_relative_to(root):
                previous[installed_path.relative_to(root).as_posix()] = item["sha256"]

    observed = {}
    changed = []
    removed = []
    for name in sorted(set(previous) | set(files)):
        path = destination(root, name)
        current = path.read_bytes() if path.exists() else None
        current_hash = digest(current) if current is not None else None
        incoming_hash = digest(files[name]) if name in files else None
        observed[name] = current
        if current_hash == incoming_hash:
            continue
        if current is None and name in previous and name in files:
            raise RuntimeError(f"Localnet file removed independently; sync stopped: {name}")
        if current_hash is not None and current_hash != previous.get(name):
            raise RuntimeError(f"Localnet file changed independently; sync stopped: {name}")
        if name in files:
            changed.append(name)
        elif current is not None:
            removed.append(name)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = state / "backups" / stamp
    if changed or removed:
        for name in changed + removed:
            if observed[name] is not None:
                atomic_write(backup / name, observed[name], mode=0o600)
        if manifest_path.exists():
            atomic_write(backup / "previous-manifest.json", manifest_path.read_bytes(), mode=0o600)

    # Publish the catalog last, after all files it references are available.
    for name in sorted(changed, key=lambda value: value == "README.md"):
        path = destination(root, name)
        current = path.read_bytes() if path.exists() else None
        if current != observed[name]:
            raise RuntimeError(f"Concurrent edit; sync stopped: {name}")
        atomic_write(path, files[name])
    for name in removed:
        path = destination(root, name)
        if path.read_bytes() != observed[name]:
            raise RuntimeError(f"Concurrent edit; sync stopped: {name}")
        path.unlink()

    for name, data in files.items():
        if destination(root, name).read_bytes() != data:
            raise RuntimeError(f"Read-back verification failed: {name}")
    manifest = {"version": 1, "synced_at": stamp,
                "files": {name: digest(data) for name, data in files.items()}}
    atomic_write(manifest_path, (json.dumps(manifest, indent=2) + "\n").encode(), mode=0o600)
    return {"success": True, "files": len(files), "updated": changed,
            "removed": removed, "backup": str(backup) if backup.exists() else None,
            "synced_at": stamp}


if __name__ == "__main__":
    try:
        result = apply_snapshot(json.load(sys.stdin), "/ai/tools/AI-Skills",
                                Path.home() / ".local/state/ai-skills-sync")
        print(json.dumps(result))
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}), file=sys.stderr)
        sys.exit(1)

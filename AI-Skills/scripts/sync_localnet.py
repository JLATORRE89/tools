"""Push the curated Windows skill catalog to localnet without credentials in files."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
from receive_catalog import sensitive_catalog_name


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from repo_env import load_env
load_env()

LIBRARY = Path(__file__).resolve().parent.parent
REMOTE_ROOT = os.environ.get("AI_SKILLS_REMOTE_ROOT", "/ai/tools/AI-Skills")


def translate(text):
    return re.sub(r"C:[/\\]Projects[/\\]tools[/\\]AI-Skills", REMOTE_ROOT,
                  text, flags=re.IGNORECASE)


def render_skill(name, data):
    if not name.endswith(".md"):
        return data
    text = translate(data.decode("utf-8-sig"))
    if name == "cloudflare/dnsSKILL.md":
        text = text.replace("projects on this workstation.", "projects on localnet.")
        text = re.sub(r"C:[/\\]projects[/\\]emailresellerserver[/\\]",
                      "${DNS_OPERATOR_CHECKOUT}/", text,
                      flags=re.IGNORECASE)
        text = text.replace("- Reference implementation:", "- Reference implementation on the operator host:")
        text = text.replace("- Operator documentation:", "- Operator documentation on the operator host:")
        text = text.replace("- Production checkout:", "- Production checkout on the operator host:")
        text += ("\n## Localnet connection\n\n"
                 "The `emailreseller` SSH alias is configured on localnet with a dedicated key "
                 "and a pinned host key. The private key stays on localnet; the Cloudflare token "
                 "stays on the operator host. SSH login and a read-only Cloudflare zone-list "
                 "request were verified during setup on 2026-09-09. Recheck access to the "
                 "specific zone when working on a DNS task. The reference paths above belong "
                 "to the operator host; read them over SSH, not from localnet's filesystem.\n")
    if re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[/\\]", text):
        raise ValueError(f"Skill needs a Linux path adaptation before sync: {name}")
    return text.replace("\r\n", "\n").encode("utf-8")


def build_snapshot(library=LIBRARY):
    library = Path(library).resolve()
    source = (library / "README.md").read_text(encoding="utf-8-sig")
    catalog_match = re.search(r"^## Catalog\s*\n(.*?)(?=^## |\Z)", source, re.M | re.S)
    if not catalog_match:
        raise ValueError("Source README has no Catalog section")
    links = re.findall(r"\]\(([^)]+)\)", catalog_match.group(1))
    vendors = set()
    for link in links:
        path = PurePosixPath(link)
        if (path.is_absolute() or ".." in path.parts or "\\" in link
                or len(path.parts) < 2 or path.parts[0].startswith(".")):
            raise ValueError(f"Invalid catalog skill link: {link}")
        if not library.joinpath(*path.parts).is_file():
            raise ValueError(f"Missing catalog skill: {link}")
        vendors.add(path.parts[0])

    # Keep the curated catalog and workflow; replace host-specific integration notes.
    shared = source.split("## Agent integration", 1)[0]
    shared = translate(shared).replace("# Shared AI skills", "# Shared AI skills on localnet", 1)
    shared = shared.replace("on this workstation", "on localnet")
    shared += """## Agent integration

Jason's `${SERVICE_USER_HOME}/.claude/CLAUDE.md` and `${SERVICE_USER_HOME}/.codex/AGENTS.md` point to this catalog. Shared project guidance is in `/ai/AGENTS.md` and `/ai/tools/AGENTS.md`. Start a new session to load changed startup instructions. Other users, custom profiles, and containers need their own instruction references and filesystem access.

Skills use explicit file references. The custom `dnsSKILL.md` name is preserved; native skill-picker registration is separate.

## Automatic updates

Windows is the source of truth. The `AI-Skills Sync to localnet` Windows scheduled task pushes changes every 15 minutes and at login while Jason is signed in and the workstation can reach localnet. New cataloged vendor folders and their supporting files are included automatically. Synchronization adapts the shared-library and DNS operator paths for Linux. Additional Windows-specific paths must be adapted in the synchronizer before those skills can publish.

Edit skills on Windows. Unexpected edits to managed files on localnet stop the sync instead of being overwritten. Backups and the last successful manifest are under `${SERVICE_USER_HOME}/.local/state/ai-skills-sync`. Only files managed by this synchronizer can be removed; unrelated files are preserved.

The `emailreseller` SSH alias is configured on localnet. Read-only Cloudflare zone access was verified during setup; confirm the requested zone and authorization before each DNS task. Credentials remain on their original hosts.
"""
    result = {"README.md": shared.encode("utf-8")}
    configuration = library / "configuration.md"
    if configuration.is_file():
        result["configuration.md"] = render_skill("configuration.md", configuration.read_bytes())
    for vendor in sorted(vendors):
        folder = library / vendor
        if folder.is_symlink() or (hasattr(folder, "is_junction") and folder.is_junction()):
            raise ValueError(f"Symlinked vendor folder: {vendor}")
        for path in sorted(folder.rglob("*")):
            if any(part.startswith(".") or part == "__pycache__"
                   for part in path.relative_to(folder).parts):
                continue
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()) or not path.resolve().is_relative_to(library):
                raise ValueError(f"Linked file outside the curated library: {path}")
            if path.is_file():
                name = path.relative_to(library).as_posix()
                if sensitive_catalog_name(name):
                    raise ValueError(f"Sensitive artifact excluded from skill publication: {name}")
                result[name] = render_skill(name, path.read_bytes())
    for link in links:
        if link not in result:
            raise ValueError(f"Catalog entry was excluded from the snapshot: {link}")
    return {"version": 1, "files": {
        name: {"data": base64.b64encode(data).decode("ascii"),
               "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in result.items()}}


def run_sync():
    payload = build_snapshot()
    receiver = (Path(__file__).parent / "receive_catalog.py").read_text(encoding="utf-8")
    ssh = Path(os.environ.get("WINDIR", "C:/Windows")) / "System32/OpenSSH/ssh.exe"
    executable = str(ssh) if ssh.is_file() else shutil.which("ssh")
    if not executable:
        raise RuntimeError("OpenSSH client was not found")
    command = [executable, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=10", os.environ.get("LOCALNET_SSH_ALIAS", "localnet"), "python3 -c " + shlex.quote(receiver)]
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    process = subprocess.run(command, input=json.dumps(payload), text=True, encoding="utf-8",
                             capture_output=True, timeout=100, **options)
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or "Remote synchronization failed")
    return json.loads(process.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Validate and list files without connecting")
    args = parser.parse_args()
    state = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AI-Skills"
    state.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[RotatingFileHandler(state / "sync-localnet.log",
                                  maxBytes=1024 * 1024, backupCount=3, encoding="utf-8")])
    try:
        result = ({"preview": True, "files": list(build_snapshot()["files"])}
                  if args.preview else run_sync())
        logging.info(json.dumps(result))
        status = {"checked_at": datetime.now(timezone.utc).isoformat(), **result}
        if not args.preview:
            (state / "last-sync.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        if sys.stdout:
            print(json.dumps(result))
        return 0
    except Exception as error:
        logging.error("Sync failed: %s", error)
        (state / "last-sync.json").write_text(json.dumps({"success": False,
            "checked_at": datetime.now(timezone.utc).isoformat(), "error": str(error)}, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

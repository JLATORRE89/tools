import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import receive_catalog
import sync_localnet


def snapshot(files):
    return {"version": 1, "files": {
        name: {"data": base64.b64encode(data).decode(),
               "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in files.items()}}


def example(skill=b"original", name="vendor/taskSKILL.md"):
    return snapshot({"README.md": f"[Skill]({name})\n".encode(), name: skill})


class SenderTests(unittest.TestCase):
    def test_linux_dns_paths_and_external_links(self):
        source = (b"---\nname: shared-cloudflare-dns\ndescription: DNS\n---\n"
                  b"- Reference implementation: `C:/projects/emailresellerserver/scripts/onboard_domain.py`.\n"
                  b"[API](https://developers.cloudflare.com/api/)\n")
        rendered = sync_localnet.render_skill("cloudflare/dnsSKILL.md", source).decode()
        self.assertNotIn("C:/", rendered)
        self.assertIn("on the operator host", rendered)
        self.assertIn("https://developers.cloudflare.com/api/", rendered)

    def test_unadapted_windows_path_stops_publication(self):
        with self.assertRaises(ValueError):
            sync_localnet.render_skill("vendor/toolSKILL.md", b"Read `D:\\private\\script.py`.")

    def test_new_catalog_vendor_includes_supporting_assets_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Skills\n\n## Catalog\n[Task](vendor/taskSKILL.md)\n\n## Agent integration\nWindows-only notes\n")
            (root / "vendor").mkdir()
            (root / "vendor/taskSKILL.md").write_text("Use this skill.")
            (root / "vendor/reference.bin").write_bytes(b"\x00\xff")
            (root / "unlisted").mkdir()
            (root / "unlisted/unpublished.md").write_text("draft")
            payload = sync_localnet.build_snapshot(root)
            self.assertEqual(set(payload["files"]), {"README.md", "vendor/taskSKILL.md", "vendor/reference.bin"})
            self.assertEqual(base64.b64decode(payload["files"]["vendor/reference.bin"]["data"]), b"\x00\xff")


@unittest.skipUnless(sys.platform == "linux", "Receiver uses Linux file locking")
class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "catalog"
        self.state = Path(self.temporary.name) / "state"

    def apply(self, payload):
        return receive_catalog.apply_snapshot(payload, self.root, self.state)

    def test_updates_are_backed_up_and_repeat_is_noop(self):
        self.apply(example())
        old_time = (self.root / "vendor/taskSKILL.md").stat().st_mtime_ns
        second = self.apply(example())
        self.assertEqual(second["updated"], [])
        self.assertEqual((self.root / "vendor/taskSKILL.md").stat().st_mtime_ns, old_time)
        result = self.apply(example(b"revised"))
        self.assertEqual((Path(result["backup"]) / "vendor/taskSKILL.md").read_bytes(), b"original")
        self.assertEqual((self.root / "vendor/taskSKILL.md").read_bytes(), b"revised")

    def test_conflict_preserves_every_file(self):
        self.apply(example())
        (self.root / "vendor/taskSKILL.md").write_bytes(b"local edit")
        before = (self.root / "README.md").read_bytes()
        with self.assertRaisesRegex(RuntimeError, "independently"):
            self.apply(example(b"incoming"))
        self.assertEqual((self.root / "vendor/taskSKILL.md").read_bytes(), b"local edit")
        self.assertEqual((self.root / "README.md").read_bytes(), before)

    def test_remote_deletion_is_a_conflict(self):
        self.apply(example())
        (self.root / "vendor/taskSKILL.md").unlink()
        with self.assertRaisesRegex(RuntimeError, "removed independently"):
            self.apply(example())

    def test_catalog_removal_deletes_only_managed_files(self):
        self.apply(example())
        (self.root / "vendor/local-note.md").write_text("keep")
        result = self.apply(snapshot({"README.md": b"No active skills.\n"}))
        self.assertEqual(result["removed"], ["vendor/taskSKILL.md"])
        self.assertEqual((self.root / "vendor/local-note.md").read_text(), "keep")
        self.assertEqual((Path(result["backup"]) / "vendor/taskSKILL.md").read_bytes(), b"original")

    def test_traversal_hash_and_missing_link_are_rejected(self):
        bad_hash = example()
        bad_hash["files"]["vendor/taskSKILL.md"]["sha256"] = "0" * 64
        invalid = [snapshot({"README.md": b"x", "../escape": b"x"}), bad_hash,
                   snapshot({"README.md": b"[Missing](vendor/no-file.md)"})]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.apply(payload)
        self.assertFalse((self.root / "README.md").exists())

    def test_symlink_destination_is_rejected(self):
        self.root.mkdir()
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (self.root / "vendor").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.apply(example())
        self.assertFalse((outside / "taskSKILL.md").exists())

    def test_bootstrap_requires_matching_installation_receipt(self):
        self.root.mkdir()
        (self.root / "README.md").write_bytes(b"installed")
        (self.root / "INSTALLATION.json").write_text(json.dumps({"files": [
            {"path": str(self.root / "README.md"), "sha256": hashlib.sha256(b"installed").hexdigest()}]}))
        self.apply(example())
        self.assertTrue((self.state / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()

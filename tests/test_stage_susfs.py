import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stage_susfs", ROOT / "scripts" / "stage_susfs.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class SusfsSourceTests(unittest.TestCase):
    def test_manifest_is_locked_and_complete(self):
        revision, files = stage.load_manifest()
        self.assertEqual(revision, "687d2d18d94cb2e3e72d1074778d58384d58e379")
        self.assertEqual({item["target"] for item in files}, stage.TARGETS)
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(stage.MANIFEST.read_bytes()).hexdigest(),
                         lock["candidate_susfs_files_sha256"])

    def test_existing_implementation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fs" / "susfs.c"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"keep owner data")
            with self.assertRaisesRegex(ValueError, "exists or escapes"):
                stage.stage_files(directory, fetch=lambda url: self.fail("unexpected download"))
            self.assertEqual(target.read_bytes(), b"keep owner data")

    def test_mismatched_git_blob_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "upstream blob differs"):
                stage.stage_files(directory, fetch=lambda url: b"tampered")
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

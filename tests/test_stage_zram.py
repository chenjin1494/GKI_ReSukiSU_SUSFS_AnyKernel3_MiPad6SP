import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stage_zram", ROOT / "scripts" / "stage_zram.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class ZramSourceTests(unittest.TestCase):
    def test_manifest_is_pinned_and_complete(self):
        revision, files = stage.load_manifest()
        self.assertEqual(revision, "547ae94bcaec53d030398f857950c64662043a5d")
        self.assertEqual(len(files), 22)
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(stage.MANIFEST.read_bytes()).hexdigest()
        self.assertEqual(digest, lock["candidate_zram_files_sha256"])

    def test_git_blob_identity(self):
        self.assertEqual(stage.blob_sha1(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_unsafe_manifest_paths_rejected(self):
        for path in ("../crypto/lz4k.c", "/tmp/escape", "lib\\lz4k.c", "lib//lz4k.c"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                stage.check_path(path)

    def test_preexisting_file_is_never_overwritten(self):
        _, files = stage.load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / files[0]["target"]
            target.parent.mkdir(parents=True)
            target.write_bytes(b"owner data")
            with self.assertRaisesRegex(ValueError, "exists or escapes"):
                stage.stage_files(directory, fetch=lambda url: self.fail("unexpected download"))
            self.assertEqual(target.read_bytes(), b"owner data")

    def test_mismatched_blob_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "upstream blob differs"):
                stage.stage_files(directory, fetch=lambda url: b"wrong content")
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

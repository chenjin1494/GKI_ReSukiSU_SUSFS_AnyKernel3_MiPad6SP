import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_zram_patch", ROOT / "scripts" / "prepare_zram_patch.py")
zram = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zram)
PATCH_DIR = ROOT / "patches" / "features" / "zram"


class ZramPatchTests(unittest.TestCase):
    def test_source_pins_reject_modified_upstream(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            zram.derive(b"different LZ4KD patch")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            zram.derive_oplus(b"different OPLUS patch")

    def test_only_compression_paths_are_in_curated_patch(self):
        data = (PATCH_DIR / "0001-lz4kd-5.15-compression-only.patch").read_bytes()
        sections = tuple(line[len(b"diff -u a/"):].split(b" b/", 1)[0]
                         for line in data.splitlines() if line.startswith(b"diff -u a/"))
        self.assertEqual(sections, zram.SAFE_PATHS)
        self.assertNotIn(b"kernel/module.c", data)
        self.assertNotIn(b"bad_version:", data)

    def test_curated_patch_hashes_match_lock(self):
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        evidence = lock["candidate_zram_patches"]
        for filename, field in (
            ("0001-lz4kd-5.15-compression-only.patch", "lz4kd_patch_sha256"),
            ("0002-lz4k-oplus-5.15.patch", "oplus_patch_sha256"),
        ):
            data = (PATCH_DIR / filename).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), evidence[field])
        self.assertEqual(zram.SOURCE_SHA256, evidence["lz4kd_upstream_sha256"])
        self.assertEqual(zram.OPLUS_SHA256, evidence["oplus_upstream_sha256"])

    def test_oplus_uses_own_configuration_label(self):
        data = (PATCH_DIR / "0002-lz4k-oplus-5.15.patch").read_bytes()
        self.assertIn(b'+\tbool "lz4k_oplus"', data)
        self.assertNotIn(b"kernel/module.c", data)


if __name__ == "__main__":
    unittest.main()

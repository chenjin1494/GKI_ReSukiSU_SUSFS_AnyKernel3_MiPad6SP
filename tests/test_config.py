import gzip
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_boot_config.py"


class EmbeddedConfigTests(unittest.TestCase):
    def make_image(self, path, include_config):
        head = bytearray(4096)
        head[:8] = b"ANDROID!"
        kernel = bytearray(8192)
        kernel[56:60] = b"ARMd"
        if include_config:
            config = b"# synthetic config\nCONFIG_ARM64=y\nCONFIG_MODULES=y\n"
            payload = b"IKCFG_ST" + gzip.compress(config) + b"IKCFG_ED"
            kernel[128:128 + len(payload)] = payload
        struct.pack_into("<4I", head, 8, len(kernel), 0, 0, 1584)
        struct.pack_into("<I", head, 40, 4)
        path.write_bytes(head + kernel)

    def test_extracts_config_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boot.img"
            dest = Path(directory) / "original.config"
            self.make_image(path, True)
            cmd = [sys.executable, str(SCRIPT), str(path), "--output", str(dest)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertIn("CONFIG_ARM64=y", dest.read_text())
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_missing_markers_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boot.img"
            dest = Path(directory) / "missing.config"
            self.make_image(path, False)
            cmd = [sys.executable, str(SCRIPT), str(path), "--output", str(dest)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()

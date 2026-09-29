import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("inspect_boot", ROOT / "scripts" / "inspect_boot.py")
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)


class BootImageInspection(unittest.TestCase):
    def test_boot_v4_and_banner(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boot.img"
            head = bytearray(4096)
            head[:8] = b"ANDROID!"
            struct.pack_into("<4I", head, 8, 8192, 0, 0, 1584)
            struct.pack_into("<I", head, 40, 4)
            path.write_bytes(head + b"Linux version 5.15.178-android13-8 #1\x00" + b"\0" * 8192)
            report = boot.inspect(path)
            self.assertEqual(report["format"], "android-boot-v4")
            self.assertEqual(report["ramdisk_size"], 0)
            self.assertIn("Linux version 5.15.178-android13-8 #1", report["banners_found"])

    def test_unknown_format_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not-boot.img"
            path.write_bytes(b"random-data")
            with self.assertRaises(ValueError):
                boot.inspect(path)


if __name__ == "__main__":
    unittest.main()

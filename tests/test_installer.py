import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "anykernel3" / "AnyKernel3.sh"
PACKAGER = ROOT / "anykernel3" / "build.sh"


class InstallerControls(unittest.TestCase):
    def test_unverified_installer_never_touches_boot(self):
        with tempfile.TemporaryDirectory() as directory:
            block = Path(directory) / "boot_b"
            block.write_bytes(b"stock")
            env = os.environ.copy()
            env.update(AK3_DEVICE="sheng", AK3_SLOT="_b", AK3_TEST_BLOCK=str(block))
            result = subprocess.run(["sh", str(INSTALLER)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("disabled", result.stdout)
            self.assertEqual(block.read_bytes(), b"stock")

    def test_unverified_packager_creates_no_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "Image"
            image.write_bytes(b"kernel")
            result = subprocess.run(["bash", str(PACKAGER), str(image)], cwd=directory,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("disabled", result.stderr)
            self.assertEqual(list(Path(directory).glob("*.zip")), [])


if __name__ == "__main__":
    unittest.main()

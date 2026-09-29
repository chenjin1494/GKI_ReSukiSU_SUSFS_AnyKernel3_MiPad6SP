import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kernel_build", ROOT / "scripts" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BuildChecks(unittest.TestCase):
    def test_locked_sources_are_complete_commits(self):
        data = build.read_lock()
        self.assertEqual(data["device"], "sheng")
        self.assertIn("manifest.revision", build.unfilled_fields(data))
        self.assertIn("kpm.patch_sha256", build.unfilled_fields(data))

    def test_wrong_device_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
            bad["device"] = "other"
            path = Path(directory) / "lock.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(build.BuildError):
                build.read_lock(path)

    def test_feature_check_catches_disabled_options(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".config"
            path.write_text("CONFIG_KSU=y\n# CONFIG_KPM is not set\n", encoding="utf-8")
            with self.assertRaisesRegex(build.BuildError, "CONFIG_KPM=y"):
                build.assert_features(path, "stock")

    def test_enhanced_checks_set_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".config"
            path.write_text("CONFIG_IP_SET_MAX=256\n", encoding="utf-8")
            with self.assertRaisesRegex(build.BuildError, "CONFIG_IP_SET_MAX=65534"):
                build.assert_features(path, "enhanced")

    def test_manifest_rejects_moving_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.xml"
            path.write_text('<manifest><project name="common" revision="main"/></manifest>', encoding="utf-8")
            lock = {"manifest": {"sha256": build.sha256(path)}}
            with self.assertRaisesRegex(build.BuildError, "full revision"):
                build.verify_manifest(path, lock)


if __name__ == "__main__":
    unittest.main()

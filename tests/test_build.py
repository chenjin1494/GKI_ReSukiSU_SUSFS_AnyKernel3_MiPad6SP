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

    def test_candidate_commit_matches_stock_banner(self):
        lock = build.read_lock()
        self.assertTrue(lock["upstreams"]["kernel_candidate"]["revision"].startswith("f4321180a397"))
        lock["upstreams"]["kernel_candidate"]["revision"] = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            path.write_text(json.dumps(lock), encoding="utf-8")
            with self.assertRaisesRegex(build.BuildError, "stock boot commit prefix"):
                build.read_lock(path)

    def test_committed_stock_kmi_report_matches_boot_lock(self):
        lock = build.read_lock()
        report = ROOT / "evidence" / "stock-kmi.json"
        self.assertEqual(build.sha256(report), lock["stock_kmi_report_sha256"])
        build.verify_kmi_report(report, lock)

    def test_tampered_kmi_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "stock-kmi.json"
            report.write_text('{"device": "other"}', encoding="utf-8")
            with self.assertRaises(build.BuildError):
                build.verify_kmi_report(report, build.read_lock())

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

    def test_bbg_requires_lsm_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".config"
            path.write_text('CONFIG_BBG=y\nCONFIG_LSM="selinux,bpf"\n', encoding="utf-8")
            with self.assertRaisesRegex(build.BuildError, "baseband_guard"):
                build.assert_features(path, "stock")

    def test_susfs_cannot_use_tracepoint_hook_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".config"
            path.write_text("CONFIG_KSU_SUSFS=y\nCONFIG_KSU_TRACEPOINT_HOOK=y\n", encoding="utf-8")
            with self.assertRaisesRegex(build.BuildError, "inline hooks conflict"):
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

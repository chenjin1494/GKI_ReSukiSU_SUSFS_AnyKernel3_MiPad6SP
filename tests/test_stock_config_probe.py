import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("report_stock_config", ROOT / "scripts" / "report_stock_config.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
STOCK = ROOT / "evidence" / "stock-306.config"


class StockConfigProbeTests(unittest.TestCase):
    def test_stock_matches_pinned_config_without_drift(self):
        report = probe.analyze(STOCK, STOCK)
        self.assertEqual(report["changed_symbols"], 0)
        self.assertEqual(report["critical_changes"], {})
        self.assertFalse(report["kernel_compiled"])
        self.assertFalse(report["toolchain_equivalence_verified"])

    def test_critical_config_drift_is_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / ".config"
            candidate.write_bytes(STOCK.read_bytes().replace(
                b"CONFIG_MODVERSIONS=y", b"# CONFIG_MODVERSIONS is not set"))
            report = probe.analyze(STOCK, candidate)
            self.assertEqual(report["critical_changes"]["MODVERSIONS"],
                             {"stock": "y", "candidate": "n"})

    def test_stock_export_whitelist_path_is_critical(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / ".config"
            candidate.write_bytes(STOCK.read_bytes().replace(
                b"/out/android13-5.15/common/abi_symbollist.raw",
                b"/out/android13-5.15/common/other_symbols.raw"))
            report = probe.analyze(STOCK, candidate)
            self.assertIn("UNUSED_KSYMS_WHITELIST", report["critical_changes"])

    def test_modified_stock_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            modified = Path(directory) / "stock.config"
            modified.write_bytes(STOCK.read_bytes() + b"# changed\n")
            with self.assertRaisesRegex(ValueError, "source lock"):
                probe.analyze(modified, STOCK)

    def test_actions_notice_reports_counts_not_build_success(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            output = io.StringIO()
            with mock.patch.object(probe.sys, "argv", ["report_stock_config.py", str(STOCK),
                                                       "--output", str(report)]):
                with mock.patch.dict(probe.os.environ, {"GITHUB_ACTIONS": "true"}):
                    with contextlib.redirect_stdout(output):
                        probe.main()
            self.assertIn("::notice title=sheng stock config::changed_symbols=0; ",
                          output.getvalue())
            self.assertIn("kernel_compiled=false", output.getvalue())
            self.assertTrue(report.is_file())

    def test_duplicate_config_entry_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / ".config"
            candidate.write_bytes(STOCK.read_bytes() + b"CONFIG_MODVERSIONS=y\n")
            with self.assertRaisesRegex(ValueError, "duplicate CONFIG_MODVERSIONS"):
                probe.parse_config(candidate)


if __name__ == "__main__":
    unittest.main()

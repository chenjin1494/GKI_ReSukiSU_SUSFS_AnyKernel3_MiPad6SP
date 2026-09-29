import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compare_kmi", ROOT / "scripts" / "compare_kmi.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class KmiComparisonTests(unittest.TestCase):
    def fixtures(self, directory, candidate):
        stock = Path(directory) / "stock.json"
        symvers = Path(directory) / "Module.symvers"
        stock.write_text(json.dumps({"device": "sheng", "boot_sha256": "a" * 64,
                                     "symbol_crcs": {"module_layout": "12345678",
                                                     "shared_symbol": "abcdef01",
                                                     "vendor_only_symbol": "01020304"}}), encoding="utf-8")
        symvers.write_text(candidate, encoding="utf-8")
        return stock, symvers

    def test_shared_crcs_match_but_result_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            stock, symvers = self.fixtures(directory,
                "0x12345678\tmodule_layout\tvmlinux\tEXPORT_SYMBOL\t\n"
                "0xabcdef01\tshared_symbol\tvmlinux\tEXPORT_SYMBOL_GPL\t\n")
            result = checker.compare(stock, symvers)
            self.assertEqual(result["result"], "partial-match")
            self.assertEqual(result["shared_symbols"], 2)
            self.assertEqual(result["not_shared"], 1)

    def test_mismatched_crc_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            stock, symvers = self.fixtures(directory,
                "0x00000001\tmodule_layout\tvmlinux\tEXPORT_SYMBOL\n")
            result = checker.compare(stock, symvers)
            self.assertEqual(result["result"], "mismatch")
            self.assertEqual(result["mismatches"]["module_layout"]["stock"], "12345678")

    def test_missing_module_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            stock, symvers = self.fixtures(directory,
                "0xabcdef01\tshared_symbol\tvmlinux\tEXPORT_SYMBOL\n")
            with self.assertRaisesRegex(ValueError, "module_layout"):
                checker.compare(stock, symvers)


if __name__ == "__main__":
    unittest.main()

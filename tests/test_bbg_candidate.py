import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_bbg_candidate", ROOT / "scripts" / "check_bbg_candidate.py")
bbg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbg)


class BBGCandidateTests(unittest.TestCase):
    KCONFIG = b"config BBG\n\tbool \"BBG\"\n\tdepends on SECURITY\n"
    MAKEFILE = b"obj-$(CONFIG_BBG) += bbg.o\n"
    SOURCE = b"DEFINE_LSM(baseband_guard) = { .blobs = &bbg_blob_sizes };\n"
    PROFILE = b'CONFIG_BBG=y\nCONFIG_LSM="landlock,bpf,baseband_guard"\n'

    def test_expected_lsm_contract(self):
        bbg.check_contract(self.KCONFIG, self.MAKEFILE, self.SOURCE, self.PROFILE)

    def test_missing_lsm_order_fails(self):
        with self.assertRaisesRegex(ValueError, "explicitly order"):
            bbg.check_contract(self.KCONFIG, self.MAKEFILE, self.SOURCE,
                               b'CONFIG_BBG=y\nCONFIG_LSM="landlock,bpf"\n')

    def test_missing_credential_blob_fails(self):
        with self.assertRaisesRegex(ValueError, "credential"):
            bbg.check_contract(self.KCONFIG, self.MAKEFILE,
                               b"DEFINE_LSM(baseband_guard) = {};\n", self.PROFILE)


if __name__ == "__main__":
    unittest.main()

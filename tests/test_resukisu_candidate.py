import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("resukisu_candidate", ROOT / "scripts" / "check_resukisu_candidate.py")
checker = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec.loader.exec_module(checker)
finally:
    sys.path.pop(0)


class ReSukiSUCandidateTests(unittest.TestCase):
    def test_driver_patch_is_locked_and_scoped(self):
        self.assertEqual(hashlib.sha256(checker.PATCH.read_bytes()).hexdigest(),
                         checker.LOCK["candidate_resukisu_drivers_patch_sha256"])
        self.assertEqual(set(checker.CANDIDATE_BLOBS), {"drivers/Kconfig", "drivers/Makefile"})

    def test_requires_exclusive_choice_and_each_inline_hook(self):
        kbuild = (b"LOCAL_GIT_EXISTS\n"
                  b"include $(KSU_SRC)/tools/inline_hook_check.mk\n"
                  b"include $(KSU_SRC)/tools/susfs_compat.mk\n")
        choice = (b"choice\nconfig KSU_TRACEPOINT_HOOK\nconfig KSU_MANUAL_HOOK\n"
                  b"config KSU_SUSFS\nendchoice\n")
        checks = b"\n".join(symbol.encode("ascii") for symbol in checker.HOOKS)
        patch = b"\n".join(b"+extern int " + symbol.encode("ascii") + b"();"
                           for symbol in checker.HOOKS)
        checker.check_hook_contract(kbuild, choice, checks, patch)
        with self.assertRaisesRegex(ValueError, "ksu_handle_stat"):
            checker.check_hook_contract(kbuild, choice, checks,
                                        patch.replace(b"ksu_handle_stat", b"renamed_hook"))
        with self.assertRaisesRegex(ValueError, "exclusive"):
            checker.check_hook_contract(kbuild, choice.replace(b"config KSU_SUSFS", b"config OTHER"),
                                        checks, patch)


if __name__ == "__main__":
    unittest.main()

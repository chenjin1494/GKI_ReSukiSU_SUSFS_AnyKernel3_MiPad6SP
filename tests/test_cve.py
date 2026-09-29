import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_cve_candidate", ROOT / "scripts" / "check_cve_candidate.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CandidateCveTests(unittest.TestCase):
    def test_unpinned_source_is_rejected_before_patch_check(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            checker.check(b"not the pinned candidate rtmutex.c")

    def test_candidate_pins_a_full_commit_and_existing_patch(self):
        self.assertEqual(len(checker.COMMIT), 40)
        self.assertIn(checker.COMMIT, checker.SOURCE_URL)
        self.assertTrue(checker.PATCH.is_file())


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("susfs_candidate", ROOT / "scripts" / "check_susfs_candidate.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SusfsCandidateTests(unittest.TestCase):
    def test_full_source_revisions_and_expected_patch_scope(self):
        self.assertEqual(len(checker.KERNEL_COMMIT), 40)
        self.assertTrue(checker.KERNEL_COMMIT.startswith("f4321180a397"))
        self.assertEqual(len(checker.SUSFS_COMMIT), 40)
        self.assertEqual(len(checker.SOURCE_PATHS), 24)
        self.assertEqual(len(set(checker.SOURCE_PATHS)), 24)
        self.assertIn("fs/namei.c", checker.SOURCE_PATHS)
        self.assertIn("security/selinux/hooks.c", checker.SOURCE_PATHS)

    def test_patch_scope_rejects_unexpected_rename(self):
        data = b"".join(f"diff --git a/{path} b/{path}\n".encode("ascii")
                        for path in checker.SOURCE_PATHS)
        with mock.patch.object(checker, "PATCH_SHA256", hashlib.sha256(data).hexdigest()):
            checker.verify_patch(data)
        tampered = data.replace(b"b/fs/namei.c", b"b/fs/other.c")
        with mock.patch.object(checker, "PATCH_SHA256", hashlib.sha256(tampered).hexdigest()):
            with self.assertRaisesRegex(ValueError, "unexpected paths"):
                checker.verify_patch(tampered)

    def test_unpinned_or_modified_patch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            checker.verify_patch(b"not the locked SUSFS patch")


if __name__ == "__main__":
    unittest.main()

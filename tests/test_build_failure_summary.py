import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("summarize_build_failure", ROOT / "scripts" / "summarize_build_failure.py")
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class BuildFailureSummaryTests(unittest.TestCase):
    def test_early_error_survives_parallel_build_tail(self):
        log = ["  HOSTCC  scripts/basic/fixdep", "clang: error: unknown argument"]
        log.extend(f"  HOSTCC scripts/dtc/{number}.o" for number in range(30))
        self.assertEqual(summary.failure_excerpt(log), "clang: error: unknown argument")

    def test_make_no_rule_is_reported(self):
        lines = ["make: *** No rule to make target 'missing'. Stop.", "make: Leaving directory"]
        self.assertIn("No rule to make target", summary.failure_excerpt(lines))

    def test_annotation_controls_escaped(self):
        self.assertIn("10%25: :error", summary.failure_excerpt(["error: 10%::error"]))


if __name__ == "__main__":
    unittest.main()

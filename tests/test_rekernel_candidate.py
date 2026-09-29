import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_rekernel_candidate", ROOT / "scripts" / "check_rekernel_candidate.py")
rekernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rekernel)


class ReKernelContractTests(unittest.TestCase):
    CANDIDATE = {
        "drivers/Kconfig": b'source "drivers/android/Kconfig"\n',
        "drivers/Makefile": b'obj-$(CONFIG_ANDROID) += android/\n',
        "drivers/android/binder.c": (b"binder_proc_transaction(\n"
                                     b"trace_android_vh_binder_proc_transaction_finish(\n"
                                     b"trace_binder_transaction(reply, t, target_node);\n"),
        "kernel/signal.c": (b"int do_send_sig_info(int sig, struct kernel_siginfo *info,\n"
                            b" struct task_struct *p, enum pid_type type)\n"
                            b"trace_android_vh_do_send_sig_info(sig, current, p);\n"),
    }
    UPSTREAM = {
        "Integrate/rekernel/Kconfig": b"config REKERNEL\nconfig REKERNEL_NETWORK\n",
        "Integrate/rekernel/Makefile": b"obj-$(CONFIG_REKERNEL) += rekernel.o\n",
        "Integrate/rekernel/rekernel.c": b"rekernel_report()\n",
        "Integrate/rekernel/rekernel.h": b"rekernel_report()\n",
    }
    PROFILE = b"CONFIG_REKERNEL=y\n# CONFIG_REKERNEL_NETWORK is not set\n"

    def test_locked_built_in_contract(self):
        rekernel.check_contract(self.CANDIDATE, self.UPSTREAM, self.PROFILE)

    def test_missing_binder_anchor_rejected(self):
        broken = dict(self.CANDIDATE)
        broken["drivers/android/binder.c"] = b"binder_proc_transaction(\n"
        with self.assertRaisesRegex(ValueError, "binder"):
            rekernel.check_contract(broken, self.UPSTREAM, self.PROFILE)

    def test_network_hooks_require_explicit_validation(self):
        with self.assertRaisesRegex(ValueError, "network hooks off"):
            rekernel.check_contract(self.CANDIDATE, self.UPSTREAM,
                                    b"CONFIG_REKERNEL=y\nCONFIG_REKERNEL_NETWORK=y\n")


if __name__ == "__main__":
    unittest.main()

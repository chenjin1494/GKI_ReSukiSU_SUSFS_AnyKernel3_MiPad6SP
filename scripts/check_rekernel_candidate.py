#!/usr/bin/env python3
"""Validate pinned Re-Kernel built-in source and f432 binder/signal hooks; no graft."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = "android-kernels/xiaomi-arctic-w-oss"
REKERNEL = "Sakion-Team/Re-Kernel"
CANDIDATE_BLOBS = {
    "drivers/Kconfig": "0d399ddaa185a7cdf5974f7f294f50032747f577",
    "drivers/Makefile": "a110338c860c770d4affa688375dc2086007a6b5",
    "drivers/android/binder.c": "a9f8e9d56ce3f4e731c1620339796b8692de466b",
    "kernel/signal.c": "9f6ec429969f7ae2fa38b92f04c6bd4b4a60bbb9",
}
REKERNEL_BLOBS = {
    "Integrate/rekernel/Kconfig": "d60047760b80c16a6d17d60ceef5e5ba1fb4501e",
    "Integrate/rekernel/Makefile": "bb613644a5f46a70c52987d81f014a44ebcf7ab9",
    "Integrate/rekernel/rekernel.c": "d37841e02b95d15f91a3f6629a31630b95b55e44",
    "Integrate/rekernel/rekernel.h": "af7022a8535c9766fe597ed67f59d754a953427d",
}


def checked_files(repository, revision, blobs):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Re-Kernel or candidate revision is not a full commit")
    result = {}
    for name, expected in blobs.items():
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{name}"
        with urlopen(url, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError(f"Re-Kernel check input exceeds 2 MiB: {name}")
        sha = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if sha != expected:
            raise ValueError(f"pinned Git blob differs: {name}")
        result[name] = data
    return result


def check_contract(candidate, upstream, profile):
    kconfig = upstream["Integrate/rekernel/Kconfig"]
    makefile = upstream["Integrate/rekernel/Makefile"]
    if b"config REKERNEL\n" not in kconfig or b"config REKERNEL_NETWORK\n" not in kconfig:
        raise ValueError("built-in Re-Kernel Kconfig contract changed")
    if not re.search(rb"obj-\$\(CONFIG_REKERNEL\)\s*\+=\s*rekernel\.o", makefile):
        raise ValueError("Re-Kernel Makefile built-in object missing")
    if b"rekernel_report" not in upstream["Integrate/rekernel/rekernel.c"] or b"rekernel_report" not in upstream["Integrate/rekernel/rekernel.h"]:
        raise ValueError("Re-Kernel reporting API missing")
    if b'source "drivers/android/Kconfig"' not in candidate["drivers/Kconfig"] or b"obj-$(CONFIG_ANDROID)" not in candidate["drivers/Makefile"]:
        raise ValueError("candidate driver integration anchors missing")
    binder = candidate["drivers/android/binder.c"]
    if any(token not in binder for token in (b"binder_proc_transaction(",
                                              b"trace_android_vh_binder_proc_transaction_finish(",
                                              b"trace_binder_transaction(reply, t, target_node);")):
        raise ValueError("candidate binder hot-path anchors changed")
    signal = candidate["kernel/signal.c"]
    if not re.search(rb"int do_send_sig_info\(int sig, struct kernel_siginfo \*info,\s*struct task_struct \*p,\s*enum pid_type type\)", signal):
        raise ValueError("candidate signal function signature changed")
    if b"trace_android_vh_do_send_sig_info(sig, current, p);" not in signal:
        raise ValueError("candidate signal hook anchor missing")
    if b"CONFIG_REKERNEL=y" not in profile or b"# CONFIG_REKERNEL_NETWORK is not set" not in profile:
        raise ValueError("sheng profile must leave unverified network hooks off")


def main():
    try:
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        if lock["upstreams"]["kernel_candidate"]["url"] != f"https://github.com/{CANDIDATE}.git":
            raise ValueError("kernel candidate repository differs from source lock")
        if lock["upstreams"]["rekernel"]["url"] != f"https://github.com/{REKERNEL}.git":
            raise ValueError("Re-Kernel repository differs from source lock")
        candidate = checked_files(CANDIDATE, lock["upstreams"]["kernel_candidate"]["revision"], CANDIDATE_BLOBS)
        upstream = checked_files(REKERNEL, lock["upstreams"]["rekernel"]["revision"], REKERNEL_BLOBS)
        profile = (ROOT / "configs" / "features" / "sheng.config").read_bytes()
        check_contract(candidate, upstream, profile)
        print("Pinned Re-Kernel built-in source and binder/signal anchors match candidate (no graft or build)")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"candidate Re-Kernel check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

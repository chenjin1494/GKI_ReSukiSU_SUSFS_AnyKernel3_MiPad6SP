#!/usr/bin/env python3
"""Check pinned BBG source/LSM linkage on a disposable public kernel overlay."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches" / "features" / "bbg" / "0001-link-bbg-security.patch"
CANDIDATE = "android-kernels/xiaomi-arctic-w-oss"
BBG = "vc-teahouse/Baseband-guard"
CANDIDATE_BLOBS = {
    "security/Kconfig": "6c9b5869e675a5e30e235638fe27701d191bd100",
    "security/Makefile": "18121f8f85cd7d0d99f758ee9eaf0cd389e2e078",
}
BBG_BLOBS = {
    "Kconfig": "e0dcf9ec08353c2debd20d80853a93e0c667d41c",
    "Makefile": "9d2f3f19b4eaedd1a464e767224f15b6a412dc0c",
    "baseband_guard.c": "f95d9fa2865501095d8d4a19bbff09a48b2b2810",
}


def blob_sha1(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def checked_files(repository, revision, blobs):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("BBG or kernel revision is not a full commit")
    files = {}
    for name, expected in blobs.items():
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{name}"
        with urlopen(url, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024 or blob_sha1(data) != expected:
            raise ValueError(f"pinned Git blob differs or exceeds 2 MiB: {name}")
        files[name] = data
    return files


def check_contract(kconfig, makefile, implementation, profile):
    if not re.search(rb"(?m)^config BBG\s*$", kconfig) or b"depends on SECURITY" not in kconfig:
        raise ValueError("BBG Kconfig lacks security dependency")
    if not re.search(rb"obj-\$\(CONFIG_BBG\)\s*\+=\s*bbg\.o", makefile):
        raise ValueError("BBG Makefile lacks built-in object")
    if b"DEFINE_LSM(baseband_guard)" not in implementation or b"bbg_blob_sizes" not in implementation:
        raise ValueError("BBG implementation lacks the pinned LSM/credential contract")
    if b"CONFIG_BBG=y" not in profile or not re.search(rb'^CONFIG_LSM="[^"\n]*,baseband_guard"$', profile, re.M):
        raise ValueError("sheng profile must explicitly order baseband_guard LSM")


def main():
    try:
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        if lock["upstreams"]["kernel_candidate"]["url"] != f"https://github.com/{CANDIDATE}.git":
            raise ValueError("candidate repository differs from source lock")
        if lock["upstreams"]["bbg"]["url"] != f"https://github.com/{BBG}.git":
            raise ValueError("BBG repository differs from source lock")
        patch = PATCH.read_bytes()
        if hashlib.sha256(patch).hexdigest() != lock["candidate_bbg_security_patch_sha256"]:
            raise ValueError("BBG linkage patch differs from source lock")
        if tuple(re.findall(rb"(?m)^diff --git a/(\S+) b/\S+$", patch)) != (
                b"security/Kconfig", b"security/Makefile"):
            raise ValueError("BBG linkage patch has unexpected scope")
        candidate = checked_files(CANDIDATE, lock["upstreams"]["kernel_candidate"]["revision"],
                                  CANDIDATE_BLOBS)
        bbg = checked_files(BBG, lock["upstreams"]["bbg"]["revision"], BBG_BLOBS)
        check_contract(bbg["Kconfig"], bbg["Makefile"], bbg["baseband_guard.c"],
                       (ROOT / "configs" / "features" / "sheng.config").read_bytes())
        with tempfile.TemporaryDirectory(prefix="sheng-bbg-security-") as directory:
            tree = Path(directory)
            for name, data in candidate.items():
                target = tree / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=tree, check=True)
            subprocess.run(["git", "apply", str(PATCH)], cwd=tree, check=True)
            if (tree / "security/Kconfig").read_bytes().count(
                    b'source "security/baseband-guard/Kconfig"') != 1:
                raise ValueError("BBG Kconfig source was not linked exactly once")
            if (tree / "security/Makefile").read_bytes().count(
                    b"obj-$(CONFIG_BBG) += baseband-guard/") != 1:
                raise ValueError("BBG security Makefile link was not installed exactly once")
        print("Pinned BBG security links and LSM contract match candidate (no kernel build)")
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"candidate BBG check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

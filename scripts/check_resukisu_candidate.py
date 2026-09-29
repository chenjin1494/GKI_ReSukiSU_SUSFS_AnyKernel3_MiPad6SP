#!/usr/bin/env python3
"""Check ReSukiSU driver graft and SUSFS inline-hook provenance; no build."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
PATCH = ROOT / "patches" / "features" / "resukisu" / "0001-link-kernelsu-drivers.patch"
CANDIDATE = "android-kernels/xiaomi-arctic-w-oss"
RESUKISU = "ReSukiSU/ReSukiSU"
CANDIDATE_BLOBS = {
    "drivers/Kconfig": "0d399ddaa185a7cdf5974f7f294f50032747f577",
    "drivers/Makefile": "a110338c860c770d4affa688375dc2086007a6b5",
}
RESUKISU_BLOBS = {
    "kernel/Kbuild": "4aad068330868e349ac18f01062a26856a3567ab",
    "kernel/Kconfig": "0174d2de5614fefca9c6dec7a31295b2b4d27085",
    "kernel/setup.sh": "8d7b5f6aa73298649d2c25b0ce3f0b3557bdf184",
    "kernel/tools/inline_hook_check.mk": "2d4bba2889e37a27f217a4270c359f80ba85974f",
}
HOOKS = (
    "ksu_handle_setresuid", "ksu_handle_execveat", "ksu_handle_faccessat",
    "ksu_handle_sys_read", "ksu_handle_stat", "ksu_handle_sys_reboot",
    "ksu_handle_input_handle_event",
)


def blob_sha1(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def download(url):
    with urlopen(url, timeout=30) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError(f"ReSukiSU candidate input exceeds 2 MiB: {url}")
    return data


def checked_files(repository, revision, expected):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("ReSukiSU source revision is not a full commit")
    result = {}
    for name, blob in expected.items():
        data = download(f"https://raw.githubusercontent.com/{repository}/{revision}/{name}")
        if blob_sha1(data) != blob:
            raise ValueError(f"ReSukiSU candidate blob differs from pinned Git object: {name}")
        result[name] = data
    return result


def check_hook_contract(kbuild, kconfig, checks, patch):
    choice = re.search(rb"(?m)^choice\s*$([\s\S]*?)^endchoice\s*$", kconfig)
    if not choice or any(f"config {name}".encode() not in choice.group(1) for name in
                         ("KSU_TRACEPOINT_HOOK", "KSU_MANUAL_HOOK", "KSU_SUSFS")):
        raise ValueError("ReSukiSU Kconfig lacks the exclusive SUSFS hooking choice")
    if (b"LOCAL_GIT_EXISTS" not in kbuild or
            b"include $(KSU_SRC)/tools/inline_hook_check.mk" not in kbuild or
            b"include $(KSU_SRC)/tools/susfs_compat.mk" not in kbuild):
        raise ValueError("ReSukiSU Kbuild lacks the pinned Git or SUSFS hook contract")
    for symbol in HOOKS:
        token = symbol.encode("ascii")
        if token not in checks or not re.search(rb"^\+[^\n]*" + token + rb"\b", patch, flags=re.MULTILINE):
            raise ValueError(f"missing matching ReSukiSU/SUSFS inline hook: {symbol}")


def main():
    try:
        if LOCK["upstreams"]["kernel_candidate"]["url"] != f"https://github.com/{CANDIDATE}.git":
            raise ValueError("candidate repository does not match source lock")
        if LOCK["upstreams"]["resukisu"]["url"] != f"https://github.com/{RESUKISU}.git":
            raise ValueError("ReSukiSU repository does not match source lock")
        patch = PATCH.read_bytes()
        if hashlib.sha256(patch).hexdigest() != LOCK["candidate_resukisu_drivers_patch_sha256"]:
            raise ValueError("driver integration patch differs from source lock")
        if tuple(re.findall(rb"(?m)^diff --git a/(\S+) b/\S+$", patch)) != (
                b"drivers/Kconfig", b"drivers/Makefile"):
            raise ValueError("unexpected driver integration patch scope")
        candidate = checked_files(CANDIDATE, LOCK["upstreams"]["kernel_candidate"]["revision"], CANDIDATE_BLOBS)
        resukisu = checked_files(RESUKISU, LOCK["upstreams"]["resukisu"]["revision"], RESUKISU_BLOBS)
        from check_susfs_candidate import download as download_susfs, verify_patch, SUSFS_COMMIT
        susfs_patch = download_susfs("https://gitlab.com/simonpunk/susfs4ksu/-/raw/"
                                     f"{SUSFS_COMMIT}/kernel_patches/50_add_susfs_in_gki-android13-5.15.patch")
        verify_patch(susfs_patch)
        check_hook_contract(resukisu["kernel/Kbuild"], resukisu["kernel/Kconfig"],
                            resukisu["kernel/tools/inline_hook_check.mk"], susfs_patch)
        with tempfile.TemporaryDirectory(prefix="sheng-resukisu-drivers-") as directory:
            tree = Path(directory)
            for name, data in candidate.items():
                target = tree / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=tree, check=True)
            subprocess.run(["git", "apply", str(PATCH)], cwd=tree, check=True)
            if (tree / "drivers/Kconfig").read_bytes().count(b'source "drivers/kernelsu/Kconfig"') != 1:
                raise ValueError("driver Kconfig link was not installed exactly once")
            if (tree / "drivers/Makefile").read_bytes().count(b"obj-$(CONFIG_KSU) += kernelsu/") != 1:
                raise ValueError("driver Makefile link was not installed exactly once")
        print("Pinned ReSukiSU driver links and SUSFS hooks match candidate (no kernel build)")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"candidate ReSukiSU check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

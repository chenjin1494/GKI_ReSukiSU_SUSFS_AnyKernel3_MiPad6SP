#!/usr/bin/env python3
"""Check pinned SUSFS 5.15 patch context on the banner-matching candidate."""
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
KERNEL_REPO = "android-kernels/xiaomi-arctic-w-oss"
if LOCK["upstreams"]["kernel_candidate"]["url"] != f"https://github.com/{KERNEL_REPO}.git":
    raise ValueError("candidate source repository differs from source lock")
KERNEL_COMMIT = LOCK["upstreams"]["kernel_candidate"]["revision"]
SUSFS_COMMIT = LOCK["upstreams"]["susfs"]["revision"]
PATCH_SHA256 = LOCK["candidate_susfs_patch_sha256"]
SOURCE_PATHS = (
    "drivers/input/input.c", "fs/Makefile", "fs/exec.c", "fs/namei.c",
    "fs/namespace.c", "fs/notify/fdinfo.c", "fs/open.c", "fs/proc/base.c",
    "fs/proc/bootconfig.c", "fs/proc/fd.c", "fs/proc/task_mmu.c",
    "fs/proc_namespace.c", "fs/read_write.c", "fs/readdir.c", "fs/stat.c",
    "fs/statfs.c", "fs/super.c", "kernel/kallsyms.c", "kernel/reboot.c",
    "kernel/sys.c", "mm/memory.c", "security/selinux/avc.c",
    "security/selinux/hooks.c", "security/selinux/selinuxfs.c",
)


def download(url, limit=2 * 1024 * 1024):
    with urlopen(url, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"candidate SUSFS source exceeds {limit} bytes: {url}")
    return data


def verify_patch(data):
    if hashlib.sha256(data).hexdigest() != PATCH_SHA256:
        raise ValueError("SUSFS upstream patch differs from pinned SHA256")
    pairs = re.findall(rb"^diff --git a/(\S+) b/(\S+)$", data, flags=re.MULTILINE)
    if len(pairs) != len(SOURCE_PATHS) or any(a != b for a, b in pairs):
        raise ValueError("SUSFS patch has unexpected paths or renames")
    sections = tuple(a.decode("ascii") for a, _ in pairs)
    if sections != SOURCE_PATHS:
        raise ValueError("SUSFS upstream patch target list differs from pinned source paths")


def main():
    try:
        patch_url = ("https://gitlab.com/simonpunk/susfs4ksu/-/raw/"
                     f"{SUSFS_COMMIT}/kernel_patches/50_add_susfs_in_gki-android13-5.15.patch")
        patch_data = download(patch_url)
        verify_patch(patch_data)
        with tempfile.TemporaryDirectory(prefix="sheng-susfs-candidate-") as directory:
            tree = Path(directory)
            patch_file = tree / "susfs.patch"
            patch_file.write_bytes(patch_data)
            for name in SOURCE_PATHS:
                url = f"https://raw.githubusercontent.com/{KERNEL_REPO}/{KERNEL_COMMIT}/{name}"
                target = tree / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(download(url))
            subprocess.run(["git", "apply", "--check", str(patch_file)], cwd=tree, check=True)
        print(f"SUSFS patch applies to pinned candidate ({len(SOURCE_PATHS)} files; no kernel build)")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"candidate SUSFS patch check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

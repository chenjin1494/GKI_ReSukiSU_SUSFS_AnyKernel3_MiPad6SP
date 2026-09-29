#!/usr/bin/env python3
"""Check pinned ZRAM patches in order against the public 5.15.194 candidate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import urlopen

from prepare_zram_patch import derive, derive_oplus
from stage_zram import stage_files

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
KERNEL_COMMIT = LOCK["upstreams"]["kernel_candidate"]["revision"]
ZRAM_COMMIT = LOCK["upstreams"]["zram"]["revision"]
SOURCE_PATHS = (
    "lib/Kconfig", "lib/Makefile", "crypto/Kconfig", "crypto/Makefile",
    "drivers/block/zram/Kconfig", "drivers/block/zram/zcomp.c",
)
PATCHES = (
    ("lz4kd.patch", "0001-lz4kd-5.15-compression-only.patch", derive),
    ("lz4k_oplus.patch", "0002-lz4k-oplus-5.15.patch", derive_oplus),
)


def download(url, limit=1024 * 1024):
    with urlopen(url, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"upstream source exceeds {limit} bytes: {url}")
    return data


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="sheng-zram-candidate-") as directory:
            tree = Path(directory)
            for name in SOURCE_PATHS:
                url = f"https://raw.githubusercontent.com/aosp-mirror/kernel_common/{KERNEL_COMMIT}/{name}"
                destination = tree / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(download(url))
            count = stage_files(tree)
            print(f"Verified and staged {count} pinned ZRAM implementation files")
            for upstream, curated, transform in PATCHES:
                url = ("https://raw.githubusercontent.com/SukiSU-Ultra/SukiSU_patch/"
                       f"{ZRAM_COMMIT}/other/zram/zram_patch/5.15/{upstream}")
                expected = transform(download(url))
                patch = ROOT / "patches" / "features" / "zram" / curated
                if patch.read_bytes() != expected:
                    raise ValueError(f"curated ZRAM patch differs from pinned upstream derivation: {curated}")
                subprocess.run(["git", "apply", "--check", str(patch)], cwd=tree, check=True)
                subprocess.run(["git", "apply", str(patch)], cwd=tree, check=True)
                print(f"Candidate patch applies: {curated} ({hashlib.sha256(expected).hexdigest()})")
        print("Candidate ZRAM patch contexts verified; compression code was not built")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"candidate ZRAM patch check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Check the stable rtmutex fix against one pinned public 5.15.194 candidate."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import urlopen

COMMIT = "e6654bf2f6c2c3c7b6af8897baa2a86991d3b5ac"
SOURCE_SHA256 = "49460480c72b3e36711a18f22893553aa27ab849da97c6bbbd09c595e03b9b6d"
SOURCE_URL = f"https://raw.githubusercontent.com/aosp-mirror/kernel_common/{COMMIT}/kernel/locking/rtmutex.c"
PATCH = Path(__file__).resolve().parents[1] / "patches" / "security" / "0001-CVE-2026-43499-rtmutex-5.15.patch"


def check(data):
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("candidate source SHA256 differs from the pinned file")
    with tempfile.TemporaryDirectory(prefix="sheng-cve-candidate-") as directory:
        root = Path(directory)
        source = root / "kernel" / "locking" / "rtmutex.c"
        source.parent.mkdir(parents=True)
        source.write_bytes(data)
        subprocess.run(["git", "apply", "--check", str(PATCH)], cwd=root, check=True)
    print("CVE patch applies to pinned candidate source (not a kernel build)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", type=Path, help="use an already downloaded pinned rtmutex.c")
    args = parser.parse_args()
    try:
        if args.source_file:
            data = args.source_file.read_bytes()
        else:
            with urlopen(SOURCE_URL, timeout=30) as response:
                data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("candidate source is unexpectedly large")
        check(data)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"candidate patch check failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

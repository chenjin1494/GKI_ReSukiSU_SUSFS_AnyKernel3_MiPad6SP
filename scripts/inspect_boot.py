#!/usr/bin/env python3
"""Inspect an Android boot image without modifying it or its parent directory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

MAGIC = b"ANDROID!"
VERSION = re.compile(rb"Linux version (5\.15\.[^\x00\r\n]{1,400})")


def inspect(path):
    path = Path(path)
    digest = hashlib.sha256()
    banners = set()
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(4096)
        if header[:8] != MAGIC:
            raise ValueError("not an Android boot image")
        kernel_size, ramdisk_size, os_version, header_size = struct.unpack_from("<4I", header, 8)
        header_version = struct.unpack_from("<I", header, 40)[0]
        if header_version not in (3, 4) or header_size not in (1580, 1584):
            raise ValueError("unsupported or malformed Android boot v3/v4 header")
        if not 0 < kernel_size <= size - 4096:
            raise ValueError("invalid kernel size in boot header")
        digest.update(header)
        carry = b""
        while part := stream.read(1024 * 1024):
            digest.update(part)
            for match in VERSION.finditer(carry + part):
                banners.add(match.group(0).decode("ascii", "replace"))
            carry = part[-512:]
    return {
        "format": f"android-boot-v{header_version}",
        "image_size": size,
        "kernel_size": kernel_size,
        "ramdisk_size": ramdisk_size,
        "header_size": header_size,
        "os_version_encoded": os_version,
        "sha256": digest.hexdigest(),
        "banners_found": sorted(banners),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boot_image", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.boot_image), indent=2))
    except (OSError, ValueError) as error:
        print(f"boot inspection failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

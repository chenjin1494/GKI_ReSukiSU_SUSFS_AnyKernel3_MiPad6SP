#!/usr/bin/env python3
"""Derive safe LZ4KD and OPLUS integration patches from pinned upstream files."""
import argparse
import hashlib
from pathlib import Path
import sys

SOURCE_SHA256 = "a3355da2166c5fcea203103e92961ecd882ce6c9b8314b0b719fe2e498b20f30"
OPLUS_SHA256 = "6321b00e9bd661ebcdba1ebd6f0d335a2b2573fcff5225870269b32713d2a625"
UNSAFE = b"diff -u a/kernel/module.c b/kernel/module.c"
SAFE_PATHS = (
    b"lib/Kconfig", b"lib/Makefile", b"crypto/Kconfig", b"crypto/Makefile",
    b"drivers/block/zram/Kconfig", b"drivers/block/zram/zcomp.c",
)


def derive(data):
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("upstream LZ4KD patch differs from pinned SHA256")
    if data.count(UNSAFE) != 1:
        raise ValueError("unexpected upstream kernel/module.c diff layout")
    safe, _discarded = data.split(UNSAFE, 1)
    sections = tuple(line[len(b"diff -u a/"):].split(b" b/", 1)[0]
                     for line in safe.splitlines() if line.startswith(b"diff -u a/"))
    if sections != SAFE_PATHS:
        raise ValueError("unexpected compression patch file list")
    # The upstream hunk has one tab-only blank context line absent from 5.15.194.
    safe = b"".join(b" \n" if line in (b" \t\n", b" \t\r\n") else line
                    for line in safe.splitlines(keepends=True))
    if safe.count(b"+    \tdefault") != 4:
        raise ValueError("unexpected inherited ZRAM default indentation")
    return safe.replace(b"+    \tdefault", b"+\tdefault")


def derive_oplus(data):
    if hashlib.sha256(data).hexdigest() != OPLUS_SHA256:
        raise ValueError("upstream LZ4K OPLUS patch differs from pinned SHA256")
    sections = tuple(line[len(b"diff -u a/"):].split(b" b/", 1)[0]
                     for line in data.splitlines() if line.startswith(b"diff -u a/"))
    if sections != (b"lib/Kconfig", b"lib/Makefile", b"drivers/block/zram/Kconfig",
                    b"drivers/block/zram/zcomp.c"):
        raise ValueError("unexpected OPLUS patch file list")
    if data.count(b"     \tdefault") != 4 or data.count(b'+\tbool "lz4k"') != 1:
        raise ValueError("unexpected upstream OPLUS patch context")
    return (data.replace(b"     \tdefault", b" \tdefault")
            .replace(b"+\t\n", b"+\n")
            .replace(b'+\tbool "lz4k"', b'+\tbool "lz4k_oplus"'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--variant", choices=("lz4kd", "oplus"), default="lz4kd")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists; refusing overwrite")
        patch = (derive if args.variant == "lz4kd" else derive_oplus)(args.source.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(patch)
        print("Curated ZRAM patch SHA256:", hashlib.sha256(patch).hexdigest())
    except (ValueError, OSError) as error:
        print(f"patch derivation failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Extract embedded IKCONFIG from a verified Android boot-v3/v4 ARM64 image."""
import argparse
import gzip
from io import BytesIO
from pathlib import Path
import struct
import sys

from inspect_boot import inspect

START = b"IKCFG_ST"
END = b"IKCFG_ED"


def extract(path):
    info = inspect(path)
    with Path(path).open("rb") as stream:
        stream.seek(4096)
        kernel = stream.read(info["kernel_size"])
    if len(kernel) != info["kernel_size"] or kernel[56:60] != b"ARMd":
        raise ValueError("boot payload is not an uncompressed ARM64 Image")
    start = kernel.find(START)
    end = kernel.find(END, start + len(START)) if start != -1 else -1
    if start == -1 or end == -1 or end - start > 8 * 1024 * 1024:
        raise ValueError("IKCONFIG markers absent or oversized")
    payload = kernel[start + len(START):end]
    with gzip.GzipFile(fileobj=BytesIO(payload)) as stream:
        config = stream.read(8 * 1024 * 1024 + 1)
    if len(config) > 8 * 1024 * 1024 or not config.startswith(b"#"):
        raise ValueError("invalid embedded kernel config")
    text = config.decode("utf-8")
    if "CONFIG_ARM64=y" not in text or "CONFIG_MODULES=y" not in text:
        raise ValueError("embedded config does not describe an ARM64 modular kernel")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boot_image", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists; refusing overwrite")
        config = extract(args.boot_image)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(config, encoding="utf-8", newline="\n")
        print(f"Extracted {len(config.splitlines())} config lines")
    except (OSError, ValueError, EOFError) as error:
        print(f"config extraction failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

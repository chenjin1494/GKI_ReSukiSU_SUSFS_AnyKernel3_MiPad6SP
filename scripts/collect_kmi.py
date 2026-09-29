#!/usr/bin/env python3
"""Extract sheng vendor-module vermagic and CRC evidence without copying modules."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from elftools.elf.elffile import ELFFile
from inspect_boot import inspect


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(modules_dir, boot_image):
    boot = inspect(boot_image)
    if not any("5.15.194-android13-8" in banner for banner in boot["banners_found"]):
        raise ValueError("stock boot does not carry the expected 5.15.194 GKI identity")
    modules = {}
    symbols = {}
    paths = sorted(Path(modules_dir).glob("*.ko"))
    if not paths:
        raise ValueError("no vendor modules found")
    for path in paths:
        with path.open("rb") as stream:
            elf = ELFFile(stream)
            if elf.elfclass != 64 or not elf.little_endian:
                raise ValueError(f"{path.name}: expected 64-bit little-endian ELF")
            modinfo = elf.get_section_by_name(".modinfo")
            versions = elf.get_section_by_name("__versions")
            if modinfo is None or versions is None:
                raise ValueError(f"{path.name}: missing module version metadata")
            tags = dict(item.split(b"=", 1) for item in modinfo.data().split(b"\0")
                        if b"=" in item)
            vermagic = tags.get(b"vermagic", b"").decode("ascii", "replace")
            if not vermagic or "modversions" not in vermagic:
                raise ValueError(f"{path.name}: missing modversions vermagic")
            data = versions.data()
            if len(data) % 64:
                raise ValueError(f"{path.name}: unsupported __versions entry size")
            entries = 0
            for offset in range(0, len(data), 64):
                crc = struct.unpack_from("<Q", data, offset)[0]
                name = data[offset + 8:offset + 64].split(b"\0", 1)[0].decode("ascii", "strict")
                if not name:
                    raise ValueError(f"{path.name}: empty symbol name")
                value = f"{crc:08x}"
                if name in symbols and symbols[name] != value:
                    raise ValueError(f"{path.name}: conflicting CRC for {name}")
                symbols[name] = value
                entries += 1
            modules[path.name] = {"sha256": sha256(path), "vermagic": vermagic, "symbols": entries}
    return {
        "device": "sheng", "branch": "android13-5.15",
        "boot_sha256": boot["sha256"], "boot_banner": boot["banners_found"],
        "modules": modules, "symbol_crcs": dict(sorted(symbols.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-image", type=Path, required=True)
    parser.add_argument("--modules-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists; refusing overwrite")
        report = collect(args.modules_dir, args.boot_image)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"Verified {len(report['modules'])} modules, {len(report['symbol_crcs'])} symbols")
        print(f"Report SHA256: {sha256(args.output)}")
    except (ValueError, OSError, KeyError) as error:
        print(f"KMI report failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Diagnose shared candidate/stock CRCs; partial coverage cannot approve a release."""
import argparse
import json
from pathlib import Path
import re
import sys

CRC = re.compile(r"^0x([0-9a-fA-F]{1,16})$")


def compare(stock_path, symvers_path):
    stock = json.loads(Path(stock_path).read_text(encoding="utf-8"))
    if stock.get("device") != "sheng" or not stock.get("symbol_crcs"):
        raise ValueError("stock report is not a sheng symbol inventory")
    wanted = stock["symbol_crcs"]
    shared = {}
    exports = 0
    for number, row in enumerate(Path(symvers_path).read_text(encoding="utf-8").splitlines(), 1):
        fields = row.split()
        if len(fields) < 4 or not CRC.fullmatch(fields[0]):
            raise ValueError(f"Module.symvers:{number}: invalid export record")
        exports += 1
        name = fields[1]
        crc = f"{int(fields[0], 16):08x}"
        if name in wanted:
            if name in shared and shared[name] != crc:
                raise ValueError(f"Module.symvers:{number}: conflicting CRC for {name}")
            shared[name] = crc
    if not exports or "module_layout" not in shared:
        raise ValueError("candidate has no exports or lacks shared module_layout")
    mismatches = {name: {"stock": wanted[name], "candidate": actual}
                  for name, actual in sorted(shared.items()) if wanted[name] != actual}
    return {
        "device": "sheng", "stock_boot_sha256": stock.get("boot_sha256"),
        "vendor_symbols": len(wanted), "candidate_exports": exports,
        "shared_symbols": len(shared), "not_shared": len(wanted) - len(shared),
        "mismatches": mismatches,
        "result": "mismatch" if mismatches else "partial-match",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_symvers", type=Path)
    parser.add_argument("--stock-kmi", type=Path, default=Path(__file__).resolve().parents[1] / "evidence" / "stock-kmi.json")
    args = parser.parse_args()
    try:
        result = compare(args.stock_kmi, args.module_symvers)
        print(json.dumps(result, indent=2))
        if result["result"] != "match":
            print("KMI comparison is incomplete or mismatched; release remains blocked", file=sys.stderr)
            sys.exit(2)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"KMI comparison failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

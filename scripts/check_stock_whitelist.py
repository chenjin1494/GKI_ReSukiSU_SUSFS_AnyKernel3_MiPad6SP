#!/usr/bin/env python3
"""Fail early unless the original stock sheng export whitelist is pinned and staged."""
import argparse
import os
from pathlib import Path
import sys

from build import BuildError, ROOT, read_lock, sha256, verify_stock_whitelist


def check(path, lock):
    stock_config = ROOT / "evidence" / "stock-306.config"
    if not stock_config.is_file() or sha256(stock_config) != lock["stock_config_sha256"]:
        raise BuildError("Stock sheng config differs from its source lock")
    verify_stock_whitelist(path, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "private" / "abi_symbollist.raw")
    args = parser.parse_args()
    try:
        check(args.input, read_lock())
    except (BuildError, OSError, ValueError, KeyError) as error:
        message = f"Stock export whitelist unavailable: {error}"
        print(message, file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error title=Stock export whitelist unavailable::{error}")
        sys.exit(2)
    print("Pinned stock export whitelist input verified (no kernel build)")


if __name__ == "__main__":
    main()

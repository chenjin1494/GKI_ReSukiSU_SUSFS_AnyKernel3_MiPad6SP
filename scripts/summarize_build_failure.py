#!/usr/bin/env python3
"""Expose a bounded, actionable diagnostic from a failed public kernel build."""
import argparse
from pathlib import Path
import re

ERROR = re.compile(r"error:|fatal error|No rule to make target|undefined reference|command not found|make(?:\[\d+\])?: \*\*\*", re.I)


def failure_excerpt(lines):
    errors = [line.strip() for line in lines if ERROR.search(line)]
    selected = errors[:4] if errors else lines[-10:]
    return " | ".join(selected)[-1300:].replace("%", "%25").replace("::", ": :")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_log", type=Path)
    args = parser.parse_args()
    lines = args.build_log.read_text(encoding="utf-8", errors="replace").splitlines()
    print("::error title=Public baseline failure excerpt::" + failure_excerpt(lines))


if __name__ == "__main__":
    main()

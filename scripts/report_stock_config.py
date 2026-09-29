#!/usr/bin/env python3
"""Diagnose stock sheng config drift after candidate-source olddefconfig."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SETTING = re.compile(r"^CONFIG_([A-Z0-9_]+)=(.+)$")
UNSET = re.compile(r"^# CONFIG_([A-Z0-9_]+) is not set$")
CRITICAL = (
    "ARM64_4K_PAGES", "MODULES", "MODVERSIONS", "MODULE_SIG",
    "TRIM_UNUSED_KSYMS", "ANDROID_VENDOR_HOOKS", "KALLSYMS_ALL",
)


def parse_config(path):
    config = {}
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        enabled = SETTING.fullmatch(line)
        disabled = UNSET.fullmatch(line)
        if not enabled and not disabled:
            continue
        name, value = (enabled.group(1), enabled.group(2)) if enabled else (disabled.group(1), "n")
        if name in config:
            raise ValueError(f"{path}:{number}: duplicate CONFIG_{name}")
        config[name] = value
    if len(config) < 1000:
        raise ValueError(f"{path}: too few Kconfig entries for a sheng GKI configuration")
    return config


def analyze(stock_path, candidate_path, lock_path=ROOT / "sources.lock.json"):
    contents = Path(stock_path).read_bytes()
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    if hashlib.sha256(contents).hexdigest() != lock["stock_config_sha256"]:
        raise ValueError("stock sheng config does not match its source lock")
    stock = parse_config(stock_path)
    candidate = parse_config(candidate_path)
    changes = {name: {"stock": stock.get(name), "candidate": candidate.get(name)}
               for name in sorted(stock.keys() | candidate.keys()) if stock.get(name) != candidate.get(name)}
    critical_changes = {name: changes[name] for name in CRITICAL if name in changes}
    return {
        "device": "sheng", "candidate_source_commit": lock["upstreams"]["kernel_candidate"]["revision"],
        "stock_config_sha256": lock["stock_config_sha256"],
        "candidate_config_sha256": hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest(),
        "toolchain_equivalence_verified": False, "kernel_compiled": False,
        "stock_symbols": len(stock), "candidate_symbols": len(candidate),
        "changed_symbols": len(changes), "critical_changes": critical_changes,
        "changes": changes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_config", type=Path)
    parser.add_argument("--stock", type=Path, default=ROOT / "evidence" / "stock-306.config")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict-critical", action="store_true")
    args = parser.parse_args()
    try:
        result = analyze(args.stock, args.candidate_config)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        overview = {key: value for key, value in result.items() if key != "changes"}
        overview["sample_changes"] = dict(list(result["changes"].items())[:20])
        print(json.dumps(overview, indent=2, sort_keys=True))
        if args.strict_critical and result["critical_changes"]:
            print("Candidate olddefconfig changed stock KMI-critical options", file=sys.stderr)
            sys.exit(2)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"stock config probe failed: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

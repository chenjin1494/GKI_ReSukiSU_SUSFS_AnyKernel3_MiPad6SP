#!/usr/bin/env python3
"""Fail-closed build driver for the sheng GKI project.

This driver deliberately cannot issue a release until every device and KPM
input has been pinned and the feature/ABI verification steps exist.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "sources.lock.json"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BuildError(Exception):
    pass


def read_lock(path=LOCK):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("device") != "sheng" or data.get("android_kernel_branch") != "android13-5.15":
        raise BuildError("Only sheng / android13-5.15 is supported")
    if data.get("kernel_version") != "5.15.194" or data.get("page_size") != 4096:
        raise BuildError("The pinned kernel version or 4K page size changed")
    for name, remote in data["upstreams"].items():
        if not SHA1.fullmatch(remote.get("revision", "")):
            raise BuildError(f"{name}: upstream revision must be a complete commit")
        if not remote.get("url", "").startswith("https://"):
            raise BuildError(f"{name}: only HTTPS upstreams accepted")
    banner_commit = re.search(r"-g([0-9a-f]{12})-", data.get("requested_banner", ""))
    if not banner_commit or not data["upstreams"]["kernel_candidate"]["revision"].startswith(banner_commit.group(1)):
        raise BuildError("Candidate source does not match the stock boot commit prefix")
    return data


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unfilled_fields(lock):
    required = {
        "manifest.revision": lock["manifest"].get("revision"),
        "manifest.sha256": lock["manifest"].get("sha256"),
        "stock_boot_sha256": lock.get("stock_boot_sha256"),
        "stock_config_sha256": lock.get("stock_config_sha256"),
        "stock_unused_ksyms_whitelist_sha256": lock.get("stock_unused_ksyms_whitelist_sha256"),
        "stock_kmi_report_sha256": lock.get("stock_kmi_report_sha256"),
        "kpm.patch_sha256": lock["kpm"].get("patch_sha256"),
        "kpm.integration_test_sha256": lock["kpm"].get("integration_test_sha256"),
    }
    missing = []
    for name, value in required.items():
        fmt = SHA1 if name.endswith("revision") else SHA256
        if not isinstance(value, str) or not fmt.fullmatch(value):
            missing.append(name)
    return missing


def run(*args, cwd=None):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def captured(*args, cwd=None):
    return subprocess.check_output([str(arg) for arg in args], cwd=cwd, text=True).strip()


def verify_manifest(path, lock):
    path = Path(path)
    if not path.is_file() or sha256(path) != lock["manifest"]["sha256"]:
        raise BuildError("The supplied release manifest is absent or has the wrong SHA256")
    from xml.etree import ElementTree
    root = ElementTree.parse(path).getroot()
    if root.tag != "manifest" or not root.findall("project"):
        raise BuildError("Release manifest contains no pinned projects")
    for project in root.findall("project"):
        revision = project.get("revision") or next(
            (d.get("revision") for d in root.findall("default") if d.get("revision")), None
        )
        if not revision or not SHA1.fullmatch(revision):
            raise BuildError("Release manifest includes a project without a full revision")
    return path


def verify_kmi_report(path, lock):
    path = Path(path)
    if not path.is_file() or sha256(path) != lock["stock_kmi_report_sha256"]:
        raise BuildError("Stock KMI report is missing or does not match the lock")
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("device") != "sheng" or report.get("branch") != "android13-5.15":
        raise BuildError("Stock KMI report is not for sheng/android13-5.15")
    if report.get("boot_sha256") != lock["stock_boot_sha256"]:
        raise BuildError("Stock boot hash does not agree with the KMI report")
    if not report.get("modules") or not report.get("symbol_crcs"):
        raise BuildError("Stock report must include module vermagic and symbol CRC evidence")


def checked_sources(lock, work):
    checkout = work / "third_party"
    checkout.mkdir(parents=True, exist_ok=True)
    for name, upstream in lock["upstreams"].items():
        dest = checkout / name
        if not dest.exists():
            run("git", "init", "-q", str(dest))
            run("git", "remote", "add", "origin", upstream["url"], cwd=dest)
        if captured("git", "rev-parse", "--is-shallow-repository", cwd=dest) == "true":
            raise BuildError(f"{name}: unexpected shallow local cache")
        run("git", "fetch", "--no-tags", "origin", upstream["revision"], cwd=dest)
        run("git", "checkout", "--detach", "-f", upstream["revision"], cwd=dest)
        if captured("git", "rev-parse", "HEAD", cwd=dest) != upstream["revision"]:
            raise BuildError(f"{name}: checkout SHA differs from lock")
    return checkout


def assert_features(config, profile):
    text = Path(config).read_text(encoding="utf-8")
    entries = dict(re.findall(r"^CONFIG_(\w+)=(.+)$", text, flags=re.MULTILINE))
    required = {
        "KSU": "y", "KSU_SUSFS": "y", "KPM": "y",
        "KSU_SUSFS_SUS_PATH": "y", "KSU_SUSFS_SUS_MOUNT": "y",
        "KSU_SUSFS_SUS_KSTAT": "y", "KSU_SUSFS_SPOOF_UNAME": "y",
        "REKERNEL": "y", "BBG": "y",
        "ZRAM": "y", "ZSMALLOC": "y", "CRYPTO_LZ4K": "y",
        "CRYPTO_LZ4KD": "y", "CRYPTO_LZ4K_OPLUS": "y",
        "SYSVIPC": "y", "POSIX_MQUEUE": "y", "IPC_NS": "y",
        "PID_NS": "y", "DEVTMPFS": "y", "TMPFS_XATTR": "y",
    }
    if profile == "enhanced":
        required.update({
            "TCP_CONG_BBR": "y", "DEFAULT_BBR": "y", "NET_SCH_FQ": "y",
            "NET_SCH_DEFAULT": "y", "DEFAULT_FQ": "y", "DEFAULT_NET_SCH": "\"fq\"",
            "NET_SCH_FQ_CODEL": "y", "IP_SET": "y", "IP_SET_MAX": "65534",
            "IP6_NF_NAT": "y", "IP6_NF_TARGET_MASQUERADE": "y",
        })
        for suffix in (
            "BITMAP_IP", "BITMAP_IPMAC", "BITMAP_PORT", "HASH_IP",
            "HASH_IPMARK", "HASH_IPPORT", "HASH_IPPORTIP", "HASH_IPPORTNET",
            "HASH_IPMAC", "HASH_MAC", "HASH_NETPORTNET", "HASH_NET",
            "HASH_NETNET", "HASH_NETPORT", "HASH_NETIFACE", "LIST_SET",
        ):
            required[f"IP_SET_{suffix}"] = "y"
    failed = [f"CONFIG_{key}={wanted} (got {entries.get(key)})"
              for key, wanted in required.items() if entries.get(key) != wanted]
    if entries.get("KSU_TRACEPOINT_HOOK") == "y" or entries.get("KSU_MANUAL_HOOK") == "y":
        failed.append("SUSFS inline hooks conflict with tracepoint/manual KernelSU hooks")
    if entries.get("REKERNEL_NETWORK") == "y":
        failed.append("CONFIG_REKERNEL_NETWORK is unverified and must remain disabled")
    lsm = entries.get("LSM", "").strip('"').split(",")
    if "baseband_guard" not in lsm:
        failed.append("CONFIG_LSM must include baseband_guard for built-in BBG")
    if failed:
        raise BuildError("Required Kconfig settings missing:\n  " + "\n  ".join(failed))
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network-profile", choices=("stock", "enhanced"), default="stock")
    parser.add_argument("--check", action="store_true", help="Check evidence and lock without modifying files")
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifests" / "gki-release.xml")
    parser.add_argument("--stock-kmi", type=Path, default=ROOT / "evidence" / "stock-kmi.json")
    parser.add_argument("--stock-whitelist", type=Path, default=ROOT / "private" / "abi_symbollist.raw")
    parser.add_argument("--kpm-test", type=Path, default=ROOT / "private" / "kpm-integration.json")
    parser.add_argument("--workspace", type=Path, default=ROOT / ".work")
    args = parser.parse_args()
    lock = read_lock()
    missing = unfilled_fields(lock)
    if missing:
        raise BuildError("Release blocked; provenance/compatibility not verified: " + ", ".join(missing))
    verify_manifest(args.manifest, lock)
    stock_config = ROOT / "evidence" / "stock-306.config"
    if not stock_config.is_file() or sha256(stock_config) != lock["stock_config_sha256"]:
        raise BuildError("Stock sheng kernel config is absent or differs from the source lock")
    if not args.stock_whitelist.is_file() or sha256(args.stock_whitelist) != lock["stock_unused_ksyms_whitelist_sha256"]:
        raise BuildError("Stock abi_symbollist.raw is missing or differs from its source lock")
    verify_kmi_report(args.stock_kmi, lock)
    kpm_patch = ROOT / "patches" / "kpm" / "implementation.patch"
    if not kpm_patch.is_file() or sha256(kpm_patch) != lock["kpm"]["patch_sha256"]:
        raise BuildError("Pinned ReSukiSU-compatible KPM implementation is missing")
    if not args.kpm_test.is_file() or sha256(args.kpm_test) != lock["kpm"]["integration_test_sha256"]:
        raise BuildError("KPM integration test report is absent or has the wrong SHA256")
    if args.check:
        print("Provenance, KMI evidence and KPM implementation inputs verified")
        return
    raise BuildError(
        "Kernel build remains gated: patch integration, ABI comparison, banner verification "
        "and real sheng boot packaging must be implemented and tested before release"
    )


if __name__ == "__main__":
    try:
        main()
    except (BuildError, subprocess.CalledProcessError, OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)

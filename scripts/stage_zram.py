#!/usr/bin/env python3
"""Stage pinned ZRAM implementation sources into an empty candidate overlay."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "zram-files.json"
LOCK = ROOT / "sources.lock.json"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def blob_sha1(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def check_path(value):
    if not isinstance(value, str) or "\\" in value or "//" in value:
        raise ValueError("invalid ZRAM manifest path")
    parts = PurePosixPath(value).parts
    if not parts or any(part in (".", "..") for part in parts) or value.startswith("/"):
        raise ValueError("unsafe ZRAM manifest path")
    return parts


def load_manifest():
    contents = MANIFEST.read_bytes()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if hashlib.sha256(contents).hexdigest() != lock["candidate_zram_files_sha256"]:
        raise ValueError("ZRAM implementation manifest differs from source lock")
    manifest = json.loads(contents)
    revision = lock["upstreams"]["zram"]["revision"]
    if not COMMIT.fullmatch(revision) or manifest["upstream_revision"] != revision:
        raise ValueError("ZRAM manifest revision differs from source lock")
    files = manifest["files"]
    if len(files) != 22:
        raise ValueError("expected 22 pinned ZRAM implementation files")
    targets = set()
    sources = set()
    for item in files:
        source, target, blob = item["source"], item["target"], item["blob_sha1"]
        source_parts, target_parts = check_path(source), check_path(target)
        if source_parts[:3] == ("other", "zram", "lz4k"):
            wanted = source_parts[3:]
        elif source_parts[:3] == ("other", "zram", "lz4k_oplus"):
            wanted = ("lib", "lz4k_oplus", *source_parts[3:])
        else:
            raise ValueError(f"unknown ZRAM implementation prefix: {source}")
        if not wanted or target_parts != wanted or not COMMIT.fullmatch(blob):
            raise ValueError(f"invalid ZRAM target or blob for {source}")
        if source in sources or target in targets:
            raise ValueError("duplicate ZRAM source or target")
        sources.add(source)
        targets.add(target)
    return revision, files


def download(url):
    with urlopen(url, timeout=30) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError(f"ZRAM source exceeds 1 MiB: {url}")
    return data


def stage_files(kernel, fetch=download):
    kernel = Path(kernel)
    if not kernel.is_dir():
        raise ValueError("ZRAM target kernel directory does not exist")
    revision, files = load_manifest()
    staged = []
    for item in files:
        target = kernel / item["target"]
        if target.exists() or target.is_symlink() or target.parent.resolve().is_relative_to(kernel.resolve()) is False:
            raise ValueError(f"ZRAM target exists or escapes kernel tree: {target}")
        source = item["source"]
        url = f"https://raw.githubusercontent.com/SukiSU-Ultra/SukiSU_patch/{revision}/{source}"
        data = fetch(url)
        if blob_sha1(data) != item["blob_sha1"]:
            raise ValueError(f"ZRAM upstream blob differs from manifest: {source}")
        staged.append((target, data))
    for target, data in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return len(staged)

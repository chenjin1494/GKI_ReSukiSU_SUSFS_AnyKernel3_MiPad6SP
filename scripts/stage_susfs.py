#!/usr/bin/env python3
"""Stage pinned SUSFS source files into a disposable kernel overlay."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "susfs-files.json"
LOCK = ROOT / "sources.lock.json"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
TARGETS = {"fs/susfs.c", "include/linux/susfs.h", "include/linux/susfs_def.h"}


def blob_sha1(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load_manifest():
    contents = MANIFEST.read_bytes()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if hashlib.sha256(contents).hexdigest() != lock["candidate_susfs_files_sha256"]:
        raise ValueError("SUSFS implementation manifest differs from source lock")
    if lock["upstreams"]["susfs"]["url"] != "https://gitlab.com/simonpunk/susfs4ksu.git":
        raise ValueError("unexpected SUSFS upstream URL")
    manifest = json.loads(contents)
    revision = lock["upstreams"]["susfs"]["revision"]
    if not COMMIT.fullmatch(revision) or manifest["upstream_revision"] != revision:
        raise ValueError("SUSFS manifest revision differs from source lock")
    files = manifest["files"]
    found = set()
    for item in files:
        source, target, blob = item["source"], item["target"], item["blob_sha1"]
        if not isinstance(source, str) or not source.startswith("kernel_patches/"):
            raise ValueError("unexpected SUSFS implementation source")
        wanted = source.removeprefix("kernel_patches/")
        parts = PurePosixPath(target).parts
        if (target != wanted or target not in TARGETS or "\\" in target or
                ".." in parts or not COMMIT.fullmatch(blob) or target in found):
            raise ValueError("invalid SUSFS target or blob in manifest")
        found.add(target)
    if found != TARGETS:
        raise ValueError("SUSFS implementation manifest is incomplete")
    return revision, files


def download(url):
    with urlopen(url, timeout=30) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError(f"SUSFS source exceeds 1 MiB: {url}")
    return data


def stage_files(kernel, fetch=download):
    kernel = Path(kernel)
    if not kernel.is_dir():
        raise ValueError("SUSFS target kernel directory does not exist")
    revision, files = load_manifest()
    staged = []
    for item in files:
        target = kernel / item["target"]
        if target.exists() or target.is_symlink() or not target.parent.resolve().is_relative_to(kernel.resolve()):
            raise ValueError(f"SUSFS target exists or escapes kernel tree: {target}")
        source = item["source"]
        url = f"https://gitlab.com/simonpunk/susfs4ksu/-/raw/{revision}/{source}"
        data = fetch(url)
        if blob_sha1(data) != item["blob_sha1"]:
            raise ValueError(f"SUSFS upstream blob differs from manifest: {source}")
        staged.append((target, data))
    for target, data in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return len(staged)

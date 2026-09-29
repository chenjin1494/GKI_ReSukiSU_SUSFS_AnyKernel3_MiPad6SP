# GKI_ReSukiSU_SUSFS_AnyKernel3_MiPad6SP

[简体中文](README.md)

A prototype for Xiaomi Pad 6S Pro 12.4 (codename `sheng`), Android 16 / android13-5.15 (5.15.194), A/B, 4K. Device scope is not release validation.

## Current status

The project contains configuration fragments, the CVE-2026-43499 rtmutex patch, pinned ReSukiSU/SUSFS/ZRAM/BBG source-port checks, read-only boot/KMI tools, and fail-closed release gates. The locked firmware 306 configuration passed `olddefconfig` on a public candidate under Ubuntu with 29 changed symbols and zero drift in seven checked KMI-critical settings; this is neither an Image build nor ABI approval. The isolated baseline compilation stops because the original build output `abi_symbollist.raw` is missing, so there is no candidate `Module.symvers` for comparison. ReSukiSU/SUSFS, ZRAM algorithms, KPM, Re-Kernel, BBG, enhanced networking, and Droidspaces are not integrated end to end. The active-slot firmware 306 boot and vendor modules were extracted read-only; see [`docs/DEVICE_EVIDENCE.md`](docs/DEVICE_EVIDENCE.md). This does not prove a new kernel will boot or preserve ABI compatibility. The installer, packaging, and release remain disabled.

The eight planned functions are:

1. ReSukiSU + SUSFS
2. ZRAM LZ4K/LZ4KD/LZ4K_OPLUS
3. KPM
4. CVE-2026-43499 rtmutex
5. Re-Kernel
6. BaseBand Guard (BBG)
7. Optional enhanced IPSet + BBR/fq/fq_codel IPv6 NAT
8. Droidspaces

## Build contract

The implementation must provide `scripts/build.sh`, invoked through Bash, with:

```text
bash scripts/build.sh --network-profile stock
bash scripts/build.sh --network-profile enhanced
```

A successful build must create a non-empty `dist/`. CI runs shell syntax checks and `python3 -m unittest discover -s tests -p 'test_*.py' -v`, and runs profile builds only when implementation and source evidence are ready. Required lock fields are `manifest.revision`, `manifest.sha256`, `kpm.patch_sha256`, `kpm.integration_test_sha256`, `stock_boot_sha256`, `stock_config_sha256`, `stock_unused_ksyms_whitelist_sha256`, and `stock_kmi_report_sha256`. Read-only image inspection uses `scripts/inspect_boot.py` and `scripts/extract_boot_config.py`; `scripts/collect_kmi.py` requires `pyelftools==0.33`. Keep extracted images and reports in ignored `private/`. Once a candidate `Module.symvers` exists, run `python scripts/compare_kmi.py /path/to/Module.symvers`; matching shared CRCs are only partial ABI evidence, not flashing approval.

## Release boundary

There is no ZIP that can truthfully be claimed as built. The supplied firmware 304 boot contains kernel 5.15.178 and cannot replace the now read-only extracted firmware 306 `boot_b` with kernel 5.15.194. Boot and the derived [vendor symbol CRC report](evidence/stock-kmi.json) are locked; original images and modules remain outside Git. Release accepts only `v*.*.*` tags, with an existing tag required for manual dispatch. Both profiles, evidence, and archives must succeed before publishing. KPM remains blocked on its source implementation, ABI comparison, and hardware validation.

Automation: [CI workflow](.github/workflows/ci.yml) · [isolated config probe](.github/workflows/config-probe.yml) · [isolated compilation diagnostic](.github/workflows/baseline-compile.yml) · [Release workflow](.github/workflows/release.yml)

References: [`docs/BUILD_CONTRACT.md`](docs/BUILD_CONTRACT.md) · [feature integration status](docs/INTEGRATION_STATUS.md) · [`docs/SOURCES.md`](docs/SOURCES.md) · [KPM integration boundary](docs/KPM_INTEGRATION.md)

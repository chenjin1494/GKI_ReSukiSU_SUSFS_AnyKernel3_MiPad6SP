# Third-party notices

The workflow uses GitHub-maintained actions pinned to commit SHAs:

- `actions/checkout`
- `actions/setup-python`
- `actions/upload-artifact`
- `actions/download-artifact`

Their licenses and notices are maintained by their respective upstream repositories. The workflow does not vendor their source code. See [`docs/SOURCES.md`](docs/SOURCES.md) for the upstream links and workflow references.

The CVE-2026-43499 rtmutex change is copied from Linux stable commit
[`838ce5cb`](https://github.com/gregkh/linux/commit/838ce5cb5d93c3ab8b27e75bc6ad905a94b752fd)
and retains the Linux kernel GPL-2.0-only source license and original commit attribution.
The [curated ZRAM integration patches](patches/features/zram) are derived from
[SukiSU-Ultra/SukiSU_patch at `547ae94b`](https://github.com/SukiSU-Ultra/SukiSU_patch/commit/547ae94bcaec53d030398f857950c64662043a5d),
which modifies GPL-2.0 kernel source files. Only patch fragments are included;
the compression implementation is not yet vendored. The derivation script
records the removed `kernel/module.c` behavior and the normalized patch context.
The AnyKernel3 script license excerpt in [`anykernel3/LICENSE`](anykernel3/LICENSE)
comes from the pinned WildKernels/AnyKernel3 tree; no upstream binaries are
vendored or distributed yet. Kernel/KPM and further third-party sources require
complete license notices when actually imported or distributed.

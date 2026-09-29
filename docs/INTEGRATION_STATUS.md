# Integration status: sheng / android13-5.15

This is an evidence map, not a completed build recipe. The public 5.15.194
candidate contains the full `f4321180a397` commit named by the stock banner,
but its mirror belongs to another Xiaomi device; sheng's actual source tree,
configuration and vendor-module KMI have not been proven equivalent. Build/release
remain disabled until those checks, the KPM port and hardware tests exist.

The [stock-config probe](../.github/workflows/config-probe.yml) is an isolated
Ubuntu workflow. On first addition (or manual dispatch) it checks out only the
pinned public candidate at its exact commit, runs `olddefconfig` on the locked
sheng stock config, and uploads a [diagnostic report](../scripts/report_stock_config.py).
The host runner's clang is not verified as the stock Android clang 14 toolchain.
Critical KMI-option drift fails the probe; even a passing probe is **not** an
Image build, `Module.symvers` comparison, exact stock-source identification or
hardware test. It never feeds the Release workflow or installer.
The [Ubuntu probe run](https://github.com/chenjin1494/GKI_ReSukiSU_SUSFS_AnyKernel3_MiPad6SP/actions/runs/36612132129)
completed checkout and `olddefconfig`: 29 Kconfig symbol values changed, while
the seven checked KMI-critical settings stayed unchanged. The full JSON diff
was uploaded, but downloading the artifact through the public API requires
authentication.

The [separate public-baseline compilation](../.github/workflows/baseline-compile.yml)
uses the pinned stock config and host distro LLVM to attempt `Image modules`
and inspect `Module.symvers` CRC overlap without publishing an Image. Since
neither the compiler binary nor the public mirror is verified as the sheng
stock build, results remain diagnostic and cannot enable Release.
The [third compile attempt](https://github.com/chenjin1494/GKI_ReSukiSU_SUSFS_AnyKernel3_MiPad6SP/actions/runs/36615074803)
identified the actual prerequisite: the stock config at
[evidence/stock-306.config:797](../evidence/stock-306.config) sets
`CONFIG_UNUSED_KSYMS_WHITELIST` to the original build machine's absolute
`/mnt/disks/build-disk/src/android/common-android13-5.15-2025-12/out/android13-5.15/common/abi_symbollist.raw`.
The runner has no such file, so generating `include/generated/autoksyms.h`
fails before any candidate `Image` or `Module.symvers` is available. The
whitelist contents and its SHA-256 are **not known**; changing the pathname,
substituting another GKI list, or disabling `TRIM_UNUSED_KSYMS` is not stock
KMI validation. The whitelist hash remains null in the release source lock.
The [baseline workflow](../.github/workflows/baseline-compile.yml) now runs
[the whitelist preflight](../scripts/check_stock_whitelist.py) before installing
tools or checking out the large candidate tree. Until the original raw file
and hash are available, the diagnostic job intentionally stops at this gate.

| Function | Pinned source / integration boundary | Verified here |
| --- | --- | --- |
| ReSukiSU + SUSFS | ReSukiSU `kernel/` at lock SHA; SUSFS `kernel_patches/50_add_susfs_in_gki-android13-5.15.patch`, `fs/susfs.c`, headers; select `KSU_SUSFS` inline hook instead of tracepoint | Pinned `drivers/` link patch and seven SUSFS hook names checked; 3 implementation blobs staged and 24-file patch passes context checks in disposable overlays. Full ReSukiSU checkout, Kbuild, ABI **not** checked |
| ZRAM LZ4K/KD/OPLUS | SukiSU_patch 5.15 patches and separate `other/zram/lz4k*` implementations | 22 implementation files verified by Git blob SHA and staged in a disposable candidate overlay; two curated patches pass ordered context checks; build/runtime **not** checked |
| KPM | Loader-only source port behind authenticated ReSukiSU manager FD; see [KPM contract](KPM_INTEGRATION.md) | Conflicting KernelPatch SU dispatch identified; no safe port |
| CVE-2026-43499 | Stable rtmutex patch | `git apply --check` on pinned candidate file, not compiled |
| Re-Kernel | Pinned `Integrate/rekernel` built-in plus binder/signal integration; `REKERNEL_NETWORK` off by default | Kconfig/Makefile/implementation Git blobs and candidate binder/signal hook anchors checked by [source contract](../scripts/check_rekernel_candidate.py); hot-path patches, compile and runtime **not** checked |
| BBG | Pinned source under `security/`; include `baseband_guard` in `CONFIG_LSM` | Pinned Kconfig/Makefile/LSM blobs and `security/` link patch checked in disposable candidate overlay; implementation, protection semantics, build and KMI **not** checked |
| Enhanced network | Kernel 5.15 IPSet/BBR/fq/fq_codel/IPv6 NAT symbols, isolated profile | IPSet symbols and max range checked in candidate Kconfig, no compiled profile |
| Droidspaces | Kernel IPC/namespace configs and ABI patch, separate userspace app/backend | Requirements identified, APK/backend not included or tested |

The pinned [SUSFS Android13-5.15 patch](https://gitlab.com/simonpunk/susfs4ksu/-/raw/687d2d18d94cb2e3e72d1074778d58384d58e379/kernel_patches/50_add_susfs_in_gki-android13-5.15.patch)
has SHA-256 `6feb693f4cf1e20031c8705352a56aa520365ff34ab90a96c8c904d2ea008a39`.
It applies to 24 files in a disposable matching-banner candidate overlay;
[the implementation manifest](../manifests/susfs-files.json) pins three Git
blobs, which [the staging check](../scripts/stage_susfs.py) retrieves and
verifies. Its VFS, proc and SELinux hooks still require a merged ReSukiSU tree
and working Kconfig/Kbuild; no compilation, KMI comparison or boot test passed.
The pinned GitLab `KernelSU/10_enable_susfs_for_ksu.patch` rewrites an older
KernelSU hook stack and is **not** applied to the pinned ReSukiSU revision.

The [ReSukiSU driver link patch](../patches/features/resukisu/0001-link-kernelsu-drivers.patch)
adds the two entries from pinned `kernel/setup.sh` without running its `git stash`,
`git pull`, or cleanup operations. [The candidate checker](../scripts/check_resukisu_candidate.py)
verifies the two driver files and four ReSukiSU Git blobs, then checks the
Kconfig choice and seven inline-hook names against the pinned SUSFS patch.
This does not create the `drivers/kernelsu` symlink or checkout the full
`KernelSU` repository. The pinned `kernel/Kbuild` demands that `KernelSU/.git`
exists and may fetch history when shallow; a reproducible non-shallow checkout,
actual `olddefconfig` and compilation are still needed.

The upstream [LZ4KD 5.15 patch](https://github.com/SukiSU-Ultra/SukiSU_patch/blob/547ae94bcaec53d030398f857950c64662043a5d/other/zram/zram_patch/5.15/lz4kd.patch)
changes `kernel/module.c` to accept mismatched symbol versions and blacklist
modules, including an unrelated Xiaomi Marble-specific list. That is unsafe
for this device's 304 extracted vendor modules and was **excluded** from
[the first curated patch](../patches/features/zram/0001-lz4kd-5.15-compression-only.patch).
The [second curated patch](../patches/features/zram/0002-lz4k-oplus-5.15.patch)
corrects inherited whitespace and the OPLUS menu label. Both outputs are pinned
by `candidate_zram_patches` in [the source lock](../sources.lock.json) and
reproducibly derived using [the patch derivation script](../scripts/prepare_zram_patch.py).
[The implementation manifest](../manifests/zram-files.json) pins 22 Git blobs
and is checked by [the staging module](../scripts/stage_zram.py). CI stages the
files and applies both patches in a disposable candidate overlay; it does not
commit the implementation files into a built kernel, compile the algorithms, or
verify that zram exposes them at runtime.

The [ReSukiSU Kconfig](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/Kconfig)
defaults to tracepoint hooks; `KSU_SUSFS` is a mutually exclusive choice.
The [BBG source Makefile](https://github.com/vc-teahouse/Baseband-guard/blob/a54e0dc6cf0aff4dd87fec49644a02d2eb612905/Makefile)
requires LSM list registration. The
[Droidspaces requirements](https://github.com/ravindu644/Droidspaces-OSS/blob/ff39a376f50499b665d187d46909686418570a32/Documentation/Kernel-Configuration.md)
are kernel prerequisites for a separate userspace product, not a
`CONFIG_DROIDSPACES` kernel feature.

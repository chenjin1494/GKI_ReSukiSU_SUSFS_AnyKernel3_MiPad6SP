# Integration status: sheng / android13-5.15

This is an evidence map, not a completed build recipe. The candidate public
5.15.194 source is **not** the original `f4321180a397` source. Build/release
remain disabled until the exact baseline, KPM port and hardware checks exist.

| Function | Pinned source / integration boundary | Verified here |
| --- | --- | --- |
| ReSukiSU + SUSFS | ReSukiSU `kernel/` at lock SHA; SUSFS `kernel_patches/50_add_susfs_in_gki-android13-5.15.patch`, `fs/susfs.c`, headers; select `KSU_SUSFS` inline hook instead of tracepoint | Upstream paths and config choice examined; no merged kernel or ABI check |
| ZRAM LZ4K/KD/OPLUS | SukiSU_patch 5.15 patches and separate `other/zram/lz4k*` implementations | Two curated patches pass ordered context checks on candidate; implementations/build/runtime **not** checked |
| KPM | Loader-only source port behind authenticated ReSukiSU manager FD; see [KPM contract](KPM_INTEGRATION.md) | Conflicting KernelPatch SU dispatch identified; no safe port |
| CVE-2026-43499 | Stable rtmutex patch | `git apply --check` on pinned candidate file, not compiled |
| Re-Kernel | Pinned `Integrate/rekernel` built-in plus binder/signal integration | Kconfig symbols found, integration not applied |
| BBG | Pinned source under `security/`; include `baseband_guard` in `CONFIG_LSM` | Kconfig and LSM prerequisite identified, no built LSM |
| Enhanced network | Kernel 5.15 IPSet/BBR/fq/fq_codel/IPv6 NAT symbols, isolated profile | IPSet symbols and max range checked in candidate Kconfig, no compiled profile |
| Droidspaces | Kernel IPC/namespace configs and ABI patch, separate userspace app/backend | Requirements identified, APK/backend not included or tested |

The upstream [LZ4KD 5.15 patch](https://github.com/SukiSU-Ultra/SukiSU_patch/blob/547ae94bcaec53d030398f857950c64662043a5d/other/zram/zram_patch/5.15/lz4kd.patch)
changes `kernel/module.c` to accept mismatched symbol versions and blacklist
modules, including an unrelated Xiaomi Marble-specific list. That is unsafe
for this device's 304 extracted vendor modules and was **excluded** from
[the first curated patch](../patches/features/zram/0001-lz4kd-5.15-compression-only.patch).
The [second curated patch](../patches/features/zram/0002-lz4k-oplus-5.15.patch)
corrects inherited whitespace and the OPLUS menu label. Both outputs are pinned
by `candidate_zram_patches` in [the source lock](../sources.lock.json) and
reproducibly derived using `scripts/prepare_zram_patch.py`. Passing patch
context checks does not mean the compression source files were imported, the
algorithms compiled, or zram exposed them at runtime.

The [ReSukiSU Kconfig](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/Kconfig)
defaults to tracepoint hooks; `KSU_SUSFS` is a mutually exclusive choice.
The [BBG source Makefile](https://github.com/vc-teahouse/Baseband-guard/blob/a54e0dc6cf0aff4dd87fec49644a02d2eb612905/Makefile)
requires LSM list registration. The
[Droidspaces requirements](https://github.com/ravindu644/Droidspaces-OSS/blob/ff39a376f50499b665d187d46909686418570a32/Documentation/Kernel-Configuration.md)
are kernel prerequisites for a separate userspace product, not a
`CONFIG_DROIDSPACES` kernel feature.

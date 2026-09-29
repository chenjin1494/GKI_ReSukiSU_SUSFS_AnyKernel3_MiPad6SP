# Sources and References

This repository does not reproduce private device properties or user-provided `getprop` output. Source revisions and hashes belong in the project-maintained `sources.lock.json`; a release must not proceed while those values are placeholders.

The workflow and test contracts are based on these public references:

- GitHub Actions workflow syntax: <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>
- GitHub Actions security hardening and permissions: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>
- GitHub artifact actions: <https://github.com/actions/upload-artifact> and <https://github.com/actions/download-artifact>
- Python `unittest` command-line interface: <https://docs.python.org/3/library/unittest.html#command-line-interface>
- GNU Bash syntax checking (`bash -n`): <https://www.gnu.org/software/bash/manual/bash.html>

These links document tool behavior and workflow mechanics. They are not evidence that the kernel, patch chain, KPM integration, or hardware has been built or validated.

## Kernel source status

The [Xiaomi arctic-w OSS mirror commit](https://github.com/android-kernels/xiaomi-arctic-w-oss/commit/f4321180a3973d19b626b3eef51871199e4e1fac)
identifies the full `f4321180a3973d19b626b3eef51871199e4e1fac` commit
prefix recorded by the stock boot. Its committer timestamp matches the stock
banner (`2026-04-15 01:39:41 UTC`) and its Makefile is 5.15.194. Eight sampled
files (Makefile, rtmutex.c and the six ZRAM patch targets) are byte-identical
to the earlier [aosp-mirror/kernel_common 5.15.194 candidate](https://github.com/aosp-mirror/kernel_common/commit/e6654bf2f6c2c3c7b6af8897baa2a86991d3b5ac).
However the trees differ in `android`, `arch`, `drivers`, `include`, `kernel`,
`mm` and `sound`. This other-device mirror is now pinned as
`upstreams.kernel_candidate` in [the source lock](../sources.lock.json) for
patch-porting, **not** accepted as sheng's exact configured source or an ABI-
compatible release build. The official Android kernel manifest host remains
unreachable from this environment. Release manifest fields remain null until
full project revisions, stock KMI comparison and device verification exist.

The pinned candidate's [build.config.constants](https://github.com/android-kernels/xiaomi-arctic-w-oss/blob/f4321180a3973d19b626b3eef51871199e4e1fac/build.config.constants)
(Git blob `07fbf24b8a201f937fa12f433db4a41bb1045742`) specifies
`BRANCH=android13-5.15` and `CLANG_VERSION=r450784e`. Its
[arm64 build config](https://github.com/android-kernels/xiaomi-arctic-w-oss/blob/f4321180a3973d19b626b3eef51871199e4e1fac/build.config.aarch64)
(Git blob `8e20ee71afe9a1d48029715a074c7f7130b3888a`) requests `Image modules`,
and the [GKI arm64 config](https://github.com/android-kernels/xiaomi-arctic-w-oss/blob/f4321180a3973d19b626b3eef51871199e4e1fac/build.config.gki.aarch64)
(Git blob `4432550310d9f8159f4145c13392d5b4754a7082`) names
`android/abi_gki_aarch64` and adds compressed images. The exact stock clang
binary and Android manifest were **not** downloaded or hashed; an Ubuntu
runner's clang is not interchangeable evidence. The
[configuration probe](../.github/workflows/config-probe.yml) is intentionally
restricted to a diagnostic `olddefconfig` run.

## CVE patch applicability

For the candidate commit above, the upstream `kernel/locking/rtmutex.c` file has
SHA-256 `49460480c72b3e36711a18f22893553aa27ab849da97c6bbbd09c595e03b9b6d`.
After retrieving it into a candidate tree at `kernel/locking/rtmutex.c`,
`git apply --check patches/security/0001-CVE-2026-43499-rtmutex-5.15.patch`
passes (run from that tree, using an absolute path to the project patch).
This only verifies patch context on [that specific matching-banner source file](https://raw.githubusercontent.com/android-kernels/xiaomi-arctic-w-oss/f4321180a3973d19b626b3eef51871199e4e1fac/kernel/locking/rtmutex.c):
no kernel compilation, stock-source comparison, or device test has occurred.

A shallow clone of the earlier aosp-mirror candidate obtained its pinned `HEAD`, but its
working-tree checkout failed on Windows at
`drivers/gpu/drm/nouveau/nvkm/subdev/i2c/aux.c` (reserved `AUX` basename).
Reapplying a sparse checkout did not materialize missing tracked files.
Candidate CI checks therefore download and hash only the required source files;
a real whole-kernel build requires a Linux runner and an independently verified
release manifest. The incomplete local tree is ignored under `.work/` and is
never used as proof of a successful kernel checkout.

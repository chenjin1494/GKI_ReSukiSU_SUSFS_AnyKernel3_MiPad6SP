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

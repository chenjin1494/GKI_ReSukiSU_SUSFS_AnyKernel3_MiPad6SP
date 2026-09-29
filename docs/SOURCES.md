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

The [aosp-mirror/kernel_common android13-5.15 snapshot](https://github.com/aosp-mirror/kernel_common/commit/e6654bf2f6c2c3c7b6af8897baa2a86991d3b5ac)
contains a [5.15.194 Makefile](https://raw.githubusercontent.com/aosp-mirror/kernel_common/e6654bf2f6c2c3c7b6af8897baa2a86991d3b5ac/Makefile),
but the original boot reports commit prefix `f4321180a397`, which that mirror
[does not identify](https://api.github.com/repos/aosp-mirror/kernel_common/commits/f4321180a397).
The official Android kernel manifest host is unreachable from this environment.
Therefore this public snapshot is a **candidate for patch-porting only**,
not an exact-stock source or an accepted release manifest. The manifest lock
fields remain null until full pinned project revisions and ABI evidence exist.

## CVE patch applicability

For the candidate commit above, the upstream `kernel/locking/rtmutex.c` file has
SHA-256 `49460480c72b3e36711a18f22893553aa27ab849da97c6bbbd09c595e03b9b6d`.
After retrieving it into a candidate tree at `kernel/locking/rtmutex.c`,
`git apply --check patches/security/0001-CVE-2026-43499-rtmutex-5.15.patch`
passes (run from that tree, using an absolute path to the project patch).
This only verifies patch context on [that specific public source file](https://raw.githubusercontent.com/aosp-mirror/kernel_common/e6654bf2f6c2c3c7b6af8897baa2a86991d3b5ac/kernel/locking/rtmutex.c):
no kernel compilation, stock-source comparison, or device test has occurred.

A shallow clone of the public candidate obtained the pinned `HEAD`, but its
working-tree checkout failed on Windows at
`drivers/gpu/drm/nouveau/nvkm/subdev/i2c/aux.c` (reserved `AUX` basename).
Reapplying a sparse checkout did not materialize missing tracked files.
Candidate CI checks therefore download and hash only the required source files;
a real whole-kernel build requires a Linux runner and an independently verified
release manifest. The incomplete local tree is ignored under `.work/` and is
never used as proof of a successful kernel checkout.

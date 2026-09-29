# KPM integration contract (not implemented)

The current ReSukiSU revision does not provide `CONFIG_KPM`. The pinned
[KernelPatch reference](https://github.com/bmax121/KernelPatch/commit/87f4dab2da53eca64af5175c8bdd36ca046fb875)
contains a KPM relocatable-ELF loader in `lkm/kpm/`, but its full LKM build
also links another SU policy, manager and syscall dispatcher. ReSukiSU has
its own authenticated manager FD and explicitly detects APatch/KernelPatch
conflicts. The reference is **not** a drop-in dependency.

A future source port must isolate the loader and its relocation, symbol and
memory support. It must use a ReSukiSU-authenticated management operation,
not KernelPatch syscall 45, its key, SU allowlist or root/SELinux stack.
Public KPM entry points must not be reachable by unauthenticated processes.
Review W^X, BTI/PAC, CFI, relocation bounds, lifetime and unload races.
A KPM built against KernelPatch-specific exports must either have an explicit
compatibility adapter or be rejected.

Before `CONFIG_KPM=y` can be accepted, a reviewed implementation patch and
its SHA-256 must exist, plus a real integration test report covering module
load/control/list/info/unload, malformed ELF and fault recovery, ReSukiSU/SUSFS
regression, symbol CRC comparison against the 306 stock report, and a sheng
boot test with a recovery path. Until then both `kpm` lock hashes stay null,
`scripts/build.py` refuses to build, and no flashable Release is generated.

Source interfaces: [KernelPatch loader](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/lkm/kpm/module.h),
[competing LKM build](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/lkm/Kbuild),
[ReSukiSU supercall](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/supercall/supercall.c),
[ReSukiSU conflict check](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/compat/apatch_conflict.c).

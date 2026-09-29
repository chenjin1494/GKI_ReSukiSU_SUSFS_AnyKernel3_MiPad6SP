# KPM integration contract (not implemented)

The current ReSukiSU revision does not provide `CONFIG_KPM`. The pinned
[KernelPatch reference](https://github.com/bmax121/KernelPatch/commit/87f4dab2da53eca64af5175c8bdd36ca046fb875)
contains a relocatable-ELF KPM loader under `kernel/patch/module/`, but builds
it as part of a separate freestanding `kpimg` with another SU policy, manager,
syscall dispatcher and custom runtime. ReSukiSU has its own authenticated
manager FD and explicitly detects APatch/KernelPatch conflicts. The reference
is **not** a drop-in Kbuild dependency.

A future loader-only port must add bounded, typed KPM requests to ReSukiSU's
`ksu_ioctl_handlers[]` with `only_manager()` checked at **each** invocation.
Root-only, SU-session and transferable FD possession alone must not authorize
loading kernel code. ReSukiSU manager/ksud need matching userspace commands;
KernelPatch syscall 45, superkey, SU allowlist and SELinux bypass must stay out.
A KPM built against KernelPatch-specific exports needs an explicit compatibility
adapter or must be rejected. Loading arbitrary executable kernel code also needs
an explicit trust policy for module bytes, not just an authenticated caller.

The pinned loader uses a freestanding symbol registry, TLSF executable-memory
pool, custom page-size and user-copy helpers, and AArch64 instruction relocation
support. Its ELF section/string/symbol bounds and relocation indices need
hardening; `REL` cannot silently report success, and list/info writes require
bounded offsets. Introduce separate write/execute memory phases and enforce
W^X, BTI/PAC/CFI as applicable. Load/list/unload and callback lifetime must
use locking and references; the reference's RCU read-side unload and unlocked
list mutation are not safe to copy.

Before `CONFIG_KPM=y` can be accepted, a reviewed implementation patch and
its SHA-256 must exist, plus a real integration test report covering malformed
ELF/relocations, authorization (unregistered UID, root-not-manager, manager,
transferred FD, SU-session FD), concurrent load/list/info/unload, W^X and fault
recovery, ReSukiSU/SUSFS regression, module CRC comparison against stock
OS3.0.306.0, and a sheng boot test with a recovery path. Until then both `kpm`
lock hashes stay null, `scripts/build.py` refuses to build, and no flashable
Release is generated.

Source interfaces: [KernelPatch loader](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/kernel/patch/module/module.c),
[relocator](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/kernel/patch/module/relo.c),
[custom allocator](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/kernel/include/kpmalloc.h),
[image symbol registry](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/kernel/base/symbol.c),
[image build](https://github.com/bmax121/KernelPatch/blob/87f4dab2da53eca64af5175c8bdd36ca046fb875/kernel/Makefile),
[ReSukiSU ioctl dispatch](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/supercall/dispatch.c),
[manager permission](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/supercall/perm.c),
[ReSukiSU conflict check](https://github.com/ReSukiSU/ReSukiSU/blob/94dd3c93c2053a84fd752df6eb85db99b7d70ab8/kernel/compat/apatch_conflict.c).

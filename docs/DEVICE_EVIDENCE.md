# Device Evidence (read-only)

This record contains only non-sensitive, read-only observations. It intentionally omits serials and other private identifiers.

- Device codename: `sheng`
- Active slot: `_b`
- Page size: 4096 bytes
- The observed `/proc/version` matched the target stock banner exactly.
- Stock kernel configuration included `CONFIG_ZRAM=m`.
- `CONFIG_KALLSYMS=y` and `CONFIG_KALLSYMS_ALL=y` were observed.
- The normal shell could not read the boot image.
- Host fastboot 37.0.1 exposes `fetch`, but this tablet's bootloader rejected
  `fastboot fetch boot_b`: `Device does not support fetch command`. The tablet
  was immediately rebooted back to Android; no flash, erase, or unlock was run.
- `boot_a` and `boot_b` symlinks existed.
- A user-provided TWRP boot-v2 image was sent through `fastboot boot` (no
  flash). Although fastboot returned `OKAY`, the device subsequently appeared
  in bootloader fastboot rather than recovery ADB. It was rebooted to Android
  on the original `_b` slot. The user subsequently flashed recovery on their
  own; recovery ADB then permitted read-only extraction of the exact images.

## Exact firmware sample

A read-only recovery dump of the current **OS3.0.306.0.WNXCNXM** active
`boot_b` has SHA-256
`1754a766e0e6845768b0ca9f45494deaac30fe87e9eb9404bc3309a537af6c18`.
It is Android boot-v4, 201,326,592 bytes, with 47,577,600 bytes of kernel
and an empty ramdisk. Its embedded banner matches the requested 5.15.194
string. The active vendor_dlkm and system_dlkm images are EROFS; offline
analysis of 304 vendor modules found 3,771 unique versioned symbols. Module
vermagic is based on **5.15.78**, so comparison must use CRCs and KMI, not
release-string equality. The complete local report SHA-256 is
`3e198a9cc433558e768aa6abdf58280ccb567b78c74793bfe5a37490a9b6f247`.
The derived [symbol CRC report](../evidence/stock-kmi.json) is in this
repository for deterministic CI checks; the original boot, module binaries,
and partition images remain ignored under `private/`.

The same uncompressed ARM64 kernel Image carries an embedded IKCONFIG. Its
[extracted 6,962-line config](../evidence/stock-306.config) has SHA-256
`eb03e6badcccd7841043517a26838ad41473d041c09a72020690648deaf5064b`.
It includes `CONFIG_ARM64_4K_PAGES=y`, `CONFIG_MODVERSIONS=y`, `CONFIG_LTO=y`,
`CONFIG_ZRAM=m`, and `# CONFIG_IP_SET is not set`. Extract again with
`python scripts/extract_boot_config.py private/stock-306-boot_b.img --output private/stock-306.config`.
These are stock settings, not proof that requested new features were compiled.

## Older firmware sample

A supplied **OS3.0.304.0.WNXCNXM** fastboot package contains a boot-v4 image
with a 47,442,432-byte kernel and zero-byte ramdisk. Its SHA-256 is
`e6aa3b8fce9fa2c3090e98892091e63e59ac91190cc7d0a1ff75e5ae056126ae`;
its embedded kernel identifies itself as **5.15.178-android13-8**. The running
**OS3.0.306.0.WNXCNXM** tablet instead reports **5.15.194-android13-8**.
The older image is not an exact-version backup and must not populate
`stock_boot_sha256` for the currently running firmware or be flashed as a
substitute. Inspect locally with `python scripts/inspect_boot.py /path/to/boot.img`.

These observations are not proof of a built kernel, ABI compatibility, boot-image integrity, flashing safety, or hardware validation. They do not enable packaging or release. The installer remains fail-closed while the patch chain, ABI integration, and KPM implementation are incomplete.

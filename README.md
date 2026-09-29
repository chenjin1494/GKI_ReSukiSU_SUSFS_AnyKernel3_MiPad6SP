# GKI_ReSukiSU_SUSFS_AnyKernel3_MiPad6SP

[English](README_EN.md)

面向 Xiaomi Pad 6S Pro 12.4（代号 `sheng`）的 Android 16 / android13-5.15（5.15.194）A/B、4K 原型项目。设备范围不等于已验证发布。

## 当前状态

当前实现只有配置片段、CVE-2026-43499 rtmutex 补丁、只读 boot/KMI 检查工具及发行门槛。ReSukiSU/SUSFS、ZRAM 算法集成、KPM、Re-Kernel、BBG、增强网络栈和 Droidspaces 尚未完成整合。已从设备当前活动槽只读提取 306 固件 `boot_b` 和 vendor 模块，证据见 [`docs/DEVICE_EVIDENCE.md`](docs/DEVICE_EVIDENCE.md)；这不是新内核可启动或兼容的证明。安装器 fail-closed，打包和发布保持禁用状态。

计划中的八项功能：

1. ReSukiSU + SUSFS
2. ZRAM LZ4K/LZ4KD/LZ4K_OPLUS
3. KPM
4. CVE-2026-43499 rtmutex
5. Re-Kernel
6. BaseBand Guard（BBG）
7. 可选 enhanced IPSet + BBR/fq/fq_codel IPv6 NAT
8. Droidspaces

## 构建契约

实现必须提供 `scripts/build.sh`（通过 Bash 调用即可），支持：

```text
bash scripts/build.sh --network-profile stock
bash scripts/build.sh --network-profile enhanced
```

成功构建必须生成非空 `dist/`。CI 会运行 shell 语法检查、`python3 -m unittest discover -s tests -p 'test_*.py' -v`，并仅在实现与来源证据完整时执行两个 profile。`sources.lock.json` 的 `manifest.revision`、`manifest.sha256`、`kpm.patch_sha256`、`kpm.integration_test_sha256`、`stock_boot_sha256`、`stock_kmi_report_sha256` 不得为空或 null。只读镜像工具包括 `scripts/inspect_boot.py` 与 `scripts/extract_boot_config.py`；`scripts/collect_kmi.py` 依赖 `pyelftools==0.33`，分析产物应留在忽略的 `private/`。构建得到 `Module.symvers` 后可用 `python scripts/compare_kmi.py /path/to/Module.symvers` 对照原厂 CRC；共享符号全部匹配仍只代表部分 ABI 证据，不等于可刷写。

## 发布边界

当前没有可声称已构建的 ZIP。提供的 304 线刷包 boot 内核为 5.15.178，不可替代现已只读提取的 306 固件 5.15.194 `boot_b`；其哈希与公开的[原厂模块 CRC 报告](evidence/stock-kmi.json)已锁定，原始镜像及模块不入库。Release 只接受 `v*.*.*` 标签（手动运行也必须输入现有版本标签），并要求两个 profile、lock 证据和归档全部成功；任何失败都不发布。KPM 仍被源码实现、ABI 比对和硬件验证阻塞。

自动化：[CI 工作流](.github/workflows/ci.yml) · [Release 工作流](.github/workflows/release.yml)

参考：[`docs/BUILD_CONTRACT.md`](docs/BUILD_CONTRACT.md) · [功能集成状态](docs/INTEGRATION_STATUS.md) · [`docs/SOURCES.md`](docs/SOURCES.md) · [KPM 集成边界](docs/KPM_INTEGRATION.md)

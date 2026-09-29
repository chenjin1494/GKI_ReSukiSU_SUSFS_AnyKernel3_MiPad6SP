# 构建契约 / Build Contract

## 前置条件 / Prerequisites

构建入口是 `scripts/build.sh`，通过 Bash 调用即可，不依赖文件执行位。它必须通过 `bash -n`，并支持 `--network-profile stock` 与 `--network-profile enhanced`。

The entry point is `scripts/build.sh`, invoked through Bash rather than requiring an executable bit. It must pass `bash -n` and accept `--network-profile stock` and `--network-profile enhanced`.

CI 使用 `python3 -m unittest discover -s tests -p 'test_*.py' -v`，校验固定来源的 22 个 ZRAM 实现文件 Git blob SHA，并在临时候选源码中检查 CVE、SUSFS 与有序 ZRAM 补丁（这不是编译测试）。缺少实现或来源 lock evidence 时，CI 会报告 `release preflight blocked` 并跳过 build jobs；这不是成功构建或可发布声明。存在 tests 时，测试失败仍会使验证失败。

CI runs `python3 -m unittest discover -s tests -p 'test_*.py' -v`, verifies 22 pinned ZRAM implementation Git blob SHAs, and checks CVE, SUSFS and ordered ZRAM patches against a disposable public 5.15.194 candidate overlay (not a compiled kernel). When implementation or source-lock evidence is incomplete, CI reports `release preflight blocked` and skips build jobs; that is not a build or release claim. When tests exist, failures still fail validation.

## 产物 / Artifacts

成功返回后必须生成非空 `dist/`。Release workflow 会将两个 profile 分别归档为 `stock.tar.gz` 和 `enhanced.tar.gz`。缺少目录、空目录、任一 profile 失败或任一归档缺失都会阻止发布。

A successful invocation must produce a non-empty `dist/`. The release workflow archives the two profiles as `stock.tar.gz` and `enhanced.tar.gz`. Missing output, a failed profile, or a missing archive blocks publication.

## 来源锁定 / Source lock

`sources.lock.json` 的以下字段必须存在且非 null、非空：`manifest.revision`、`manifest.sha256`、`kpm.patch_sha256`、`kpm.integration_test_sha256`、`stock_boot_sha256`、`stock_kmi_report_sha256`。`scripts/compare_kmi.py` 遇到仅部分符号 CRC 对得上的 `partial-match` 也返回失败，不能据此放行发布。

The workflow checks these exact fields before release. The patch chain/ABI integration is incomplete and KPM has not passed hardware validation; these documents do not imply KPM support. `scripts/compare_kmi.py` reports shared CRCs but returns a nonzero exit status for `partial-match`: without a provider-aware comparison of every required GKI export it cannot approve a release.

## 发布 / Release

`v*.*.*` 标签推送或手动运行会构建两个 profile。手动运行必须输入一个已存在的版本标签，构建和发布都固定到该标签；不会创建 `manual-*` 标签。只有两个构建、lock evidence 和归档全部成功时，最后的 publish job 才获得 `contents: write` 并创建预发布 GitHub Release。

A `v*.*.*` tag push or manual dispatch builds both profiles. Manual dispatch requires an existing version tag, and both build and publish use that exact tag; no `manual-*` tag is invented. Only after both builds, lock evidence, and archives succeed does the final publish job receive `contents: write` and create a prerelease GitHub Release.

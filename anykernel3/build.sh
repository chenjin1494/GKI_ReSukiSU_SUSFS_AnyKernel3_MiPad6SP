#!/usr/bin/env bash
# Refuse to create a flashable ZIP until sheng boot layout is verified.
set -euo pipefail
printf '%s\n' 'sheng AnyKernel3 packaging is disabled: stock boot, KMI and upstream repacking tools are not validated' >&2
exit 1

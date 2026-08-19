#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${1:-TRQ-EventRepricing-Intraday}"

run_case() {
  local case_id="$1"
  local ticker="$2"
  local sector="$3"
  local broad="$4"
  local year="$5"
  local month="$6"
  local day="$7"

  echo "=== ${case_id} ==="
  lean cloud backtest "${PROJECT_NAME}" --push \
    --name "ER-v1-${case_id}" \
    --parameter ticker "${ticker}" \
    --parameter sector "${sector}" \
    --parameter broad "${broad}" \
    --parameter year "${year}" \
    --parameter month "${month}" \
    --parameter day "${day}"
}

run_case CYTK-20231227 CYTK XBI QQQ 2023 12 27
run_case NVCR-20240327 NVCR XBI QQQ 2024 3 27
run_case SRRK-20241007 SRRK XBI QQQ 2024 10 7
run_case ARM-20240208 ARM SOXX QQQ 2024 2 8
run_case NVDA-20230525 NVDA SOXX QQQ 2023 5 25
run_case AVGO-20241213 AVGO SOXX QQQ 2024 12 13

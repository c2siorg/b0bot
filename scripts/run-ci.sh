#!/usr/bin/env bash
# Run the same lint and test steps as .github/workflows/ci.yml locally.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
LINT_VENV="$ROOT/.venv"

ensure_lint_venv() {
  if [[ ! -d "$LINT_VENV" ]]; then
    "$PYTHON" -m venv "$LINT_VENV"
    "$LINT_VENV/bin/pip" install --disable-pip-version-check -q --upgrade pip
    "$LINT_VENV/bin/pip" install --disable-pip-version-check -q -r requirements-dev.txt
  elif ! "$LINT_VENV/bin/python" -m ruff --version &>/dev/null; then
    "$LINT_VENV/bin/pip" install --disable-pip-version-check -q -r requirements-dev.txt
  fi
}

run_service_tests() {
  local service=$1
  local service_dir="$ROOT/$service"
  local venv="$service_dir/.venv"

  echo "==> Test ($service)"
  if [[ ! -d "$venv" ]]; then
    "$PYTHON" -m venv "$venv"
    "$venv/bin/pip" install --disable-pip-version-check -q --upgrade pip
    "$venv/bin/pip" install --disable-pip-version-check -q -r "$service_dir/requirements.txt"
  fi

  (cd "$service_dir" && "$venv/bin/python" -m pytest tests/ -q)
}

echo "==> Lint (Ruff)"
ensure_lint_venv
"$LINT_VENV/bin/ruff" check api-service ingestion-service notification-service

run_service_tests api-service
run_service_tests ingestion-service
run_service_tests notification-service

echo "==> All CI checks passed"

#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-run}"

STEPS=(
  "backend coffee API tests"
  "app unit lint build"
  "web contract and build"
  "paddleocr service tests"
  "infra compose contract"
  "delivery gate checks"
  "docker compose static config"
)

list_steps() {
  for step in "${STEPS[@]}"; do
    printf '%s\n' "$step"
  done
}

run_step() {
  local name="$1"
  local command="$2"

  printf '\n==> %s\n' "$name"
  if bash -lc "$command"; then
    printf 'PASS %s\n' "$name"
    return 0
  fi

  printf 'FAIL %s\n' "$name"
  return 1
}

if [[ "$MODE" == "--list" ]]; then
  list_steps
  exit 0
fi

if [[ "$MODE" != "run" ]]; then
  printf 'Usage: %s [--list]\n' "$0" >&2
  exit 2
fi

FAILED=0

run_step "backend coffee API tests" \
  "cd '$ROOT_DIR/backend' && DATABASE_TYPE=SQLITE3 REDIS_ENABLE=false API_LOG_ENABLE=false .venv/bin/python manage.py test apps.coffee.tests -v 2" || FAILED=1

run_step "app unit lint build" \
  "cd '$ROOT_DIR/coffee-collector-app' && npm test && npm run lint && npm run build:app" || FAILED=1

run_step "web contract and build" \
  "cd '$ROOT_DIR/web' && node --test tests/coffee-web-contract.test.mjs && npm run lint --if-present && npm run build" || FAILED=1

run_step "paddleocr service tests" \
  "cd '$ROOT_DIR' && PYTHONPATH=services/paddleocr python3 -m unittest discover -s services/paddleocr/tests -v" || FAILED=1

run_step "infra compose contract" \
  "cd '$ROOT_DIR' && python3 -m unittest discover -s tests -v" || FAILED=1

run_step "delivery gate checks" \
  "cd '$ROOT_DIR' && python3 scripts/check-delivery-gates.py --json" || FAILED=1

run_step "docker compose static config" \
  "cd '$ROOT_DIR' && docker compose config" || FAILED=1

if [[ "$FAILED" -eq 0 ]]; then
  printf '\nAll local verification steps passed.\n'
else
  printf '\nOne or more local verification steps failed. See logs above.\n' >&2
fi

exit "$FAILED"

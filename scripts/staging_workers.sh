#!/usr/bin/env bash
# Run only in the dedicated staging worker services after owner approval.
set -euo pipefail
cd "$(dirname "$0")/.."
role="${1:-}"
python scripts/staging_preflight.py "$role"
if [[ "${VALHALLA_STAGING_TRIAL_ENABLED:-}" != 1 ]]; then
  printf '%s\n' 'Staging worker hold is active.' >&2
  exit 2
fi
jobs=()
stop_children() {
  trap - EXIT
  if (("${#jobs[@]}")); then
    kill -TERM "${jobs[@]}" 2>/dev/null || true
    wait "${jobs[@]}" 2>/dev/null || true
  fi
}
trap stop_children EXIT
trap 'exit 0' INT TERM

start_lane() {
  local script="$1"
  shift
  python "services/api/tools/cron/$script" "$@" &
  jobs+=("$!")
}
case "$role" in
  worker)
    start_lane foundry_discovery_worker.py
    start_lane pantheon_worker.py --role "${VALHALLA_STAGING_PANTHEON_ROLE:?staging specialist required}"
    start_lane specialist_schedule_worker.py
    start_lane business_factory_worker.py
    ;;
  reviewer)
    start_lane loki_analyst_worker.py --artifact-type pantheon_report
    start_lane loki_analyst_worker.py --artifact-type universal_opportunity
    ;;
  *) exit 2 ;;
esac
wait -n "${jobs[@]}" || true
printf '%s\n' 'A staging worker lane exited. Stopping the remaining lanes.' >&2
exit 1

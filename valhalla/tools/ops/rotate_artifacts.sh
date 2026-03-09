#!/usr/bin/env bash
set -euo pipefail

# Rotate/compress old artifacts safely.
# This script DOES NOT touch databases or core code.
# It only compresses files older than N days in artifact directories.

DAYS="${1:-14}"
STAMP="$(date +"%Y%m%d_%H%M%S")"
ARCHIVE_DIR="archives/${STAMP}"
mkdir -p "${ARCHIVE_DIR}"

rotate_dir () {
  local dir="$1"
  local label="$2"
  if [[ -d "${dir}" ]]; then
    echo "Rotating ${dir} (>${DAYS} days) -> ${ARCHIVE_DIR}/${label}.tar.gz"
    # Find old files, tar them, then delete only what got archived
    mapfile -t files < <(find "${dir}" -type f -mtime +"${DAYS}" 2>/dev/null || true)
    if [[ "${#files[@]}" -gt 0 ]]; then
      tar -czf "${ARCHIVE_DIR}/${label}.tar.gz" "${files[@]}"
      rm -f "${files[@]}"
      echo "Archived and removed ${#files[@]} files from ${dir}"
    else
      echo "No files older than ${DAYS} days in ${dir}"
    fi
  else
    echo "Skip: ${dir} not found"
  fi
}

rotate_dir "data/exports/phase3" "phase3_exports"
rotate_dir "reports/integrated_sandbox" "integrated_reports"
rotate_dir "exports" "exports_generic"

echo "Done. Archives written to: ${ARCHIVE_DIR}"

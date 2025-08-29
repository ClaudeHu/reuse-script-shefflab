#!/usr/bin/env bash
# encode_metadata_fetch.sh
# Usage: ./encode_metadata_fetch.sh /path/to/accessions.txt /path/to/output/folder files

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <accessions.txt> <output_folder> <endpoint>"
  exit 1
fi

ACCESSION_FILE="$1"
OUTPUT_DIR="$2"
TYPE_RAW="$3"

# normalize endpoint: lowercase, strip leading/trailing slashes
ENDPOINT="$(echo "$TYPE_RAW" | tr '[:upper:]' '[:lower:]' | sed 's#^/*##; s#/*$##')"
mkdir -p "$OUTPUT_DIR"

# count non-empty, non-comment lines
TOTAL=$(grep -cve '^\s*$' -e '^\s*#' "$ACCESSION_FILE" || true)
if [ "${TOTAL:-0}" -eq 0 ]; then
  echo "No accessions found in '$ACCESSION_FILE'."
  exit 0
fi

COUNT=0
BAR_WIDTH=50

render_bar() {
  local count=$1 total=$2 width=$3
  local filled=$(( count * width / total ))
  local empty=$(( width - filled ))
  local percent=$(( count * 100 / total ))
  printf "\r[%s%s] %3d%% (%d/%d)" \
    "$(printf '#%.0s' $(seq 1 $filled))" \
    "$(printf ' %.0s' $(seq 1 $empty))" \
    "$percent" "$count" "$total"
}

while IFS= read -r ACC || [ -n "$ACC" ]; do
  # trim whitespace and CRLF, skip blanks/comments
  ACC="$(echo "$ACC" | sed 's/\r$//' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  [ -z "$ACC" ] && continue
  case "$ACC" in \#*) continue ;; esac

  tmp="${OUTPUT_DIR}/.${ACC}.json.part"
  out="${OUTPUT_DIR}/${ACC}.json"
  url="https://www.encodeproject.org/${ENDPOINT}/${ACC}/"

  if curl -fsSL -H "Accept: application/json" "$url" -o "$tmp"; then
    mv -f "$tmp" "$out"
  else
    rm -f "$tmp" 2>/dev/null || true
    printf "\nFailed to download %s\n" "$ACC"
  fi

  COUNT=$((COUNT + 1))
  render_bar "$COUNT" "$TOTAL" "$BAR_WIDTH"
done < "$ACCESSION_FILE"

printf "\nDone: %d metadata JSON files processed, saved to %s\n" "$TOTAL" "$OUTPUT_DIR"

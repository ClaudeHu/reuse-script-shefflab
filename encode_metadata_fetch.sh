#!/usr/bin/env bash
# encode_metadata_fetch.sh
# Usage: ./encode_metadata_fetch.sh /path/to/accessions.txt /path/to/output/folder files

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <accessions.txt> <output_folder> files"
    exit 1
fi

ACCESSION_FILE="$1"
OUTPUT_DIR="$2"
TYPE="$3"

if [ "$TYPE" != "files" ]; then
    echo "Currently only 'files' type is supported."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Count total number of non-empty lines
TOTAL=$(grep -cve '^\s*$' "$ACCESSION_FILE")
COUNT=0

while IFS= read -r ACC; do
    if [ -z "$ACC" ]; then
        continue
    fi
    COUNT=$((COUNT + 1))
    echo -ne "[${COUNT}/${TOTAL}] Downloading $ACC...\r"
    curl -sSL -H "Accept: application/json" \
        "https://www.encodeproject.org/files/${ACC}/" \
        -o "${OUTPUT_DIR}/${ACC}.json"
done < "$ACCESSION_FILE"

echo -e "\nAll $TOTAL metadata JSON files have been downloaded to $OUTPUT_DIR"

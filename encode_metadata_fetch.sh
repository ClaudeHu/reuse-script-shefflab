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

TOTAL=$(grep -cve '^\s*$' "$ACCESSION_FILE")
COUNT=0
BAR_WIDTH=50

while IFS= read -r ACC; do
    [ -z "$ACC" ] && continue
    
    if curl -sSL -H "Accept: application/json" \
        "https://www.encodeproject.org/files/${ACC}/" \
        -o "${OUTPUT_DIR}/${ACC}.json"; then
        COUNT=$((COUNT + 1))
        PERCENT=$((COUNT * 100 / TOTAL))
        FILLED=$((COUNT * BAR_WIDTH / TOTAL))
        EMPTY=$((BAR_WIDTH - FILLED))
        printf "\r[%s%s] %d%%" \
            "$(printf '#%.0s' $(seq 1 $FILLED))" \
            "$(printf ' %.0s' $(seq 1 $EMPTY))" \
            "$PERCENT"
    else
        echo -e "\nFailed to download $ACC"
    fi
done < "$ACCESSION_FILE"

echo -e "\nDone: $TOTAL metadata JSON files processed, saved to $OUTPUT_DIR"

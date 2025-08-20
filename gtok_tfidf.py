import os
import sys
import math
import json
from typing import Dict, Iterable, Set
from collections import Counter, defaultdict

from gtars.tokenizers import Tokenizer
from gtars.utils import read_tokens_from_gtok
from tqdm import tqdm
import numpy as np


def _special_token_ids(tokenizer: Tokenizer) -> Set[int]:
    """Collect special token IDs; ignore any that fail to encode."""
    ids: Set[int] = set()
    for t in tokenizer.special_tokens_map.values():
        if t is None:
            continue
        try:
            # encode a single token; tokenizer.encode(...) should return a list of ids
            tid = tokenizer.encode(t)[0] if isinstance(tokenizer.encode(t), list) else tokenizer.encode(t)
            ids.add(int(tid))
        except Exception:
            # be permissive: if a special token can't be encoded, just skip it
            continue
    return ids


def _iter_gtok_files(folder: str) -> Iterable[str]:
    """Yield full paths to .gtok files only, deterministic order."""
    with os.scandir(folder) as it:
        files = [e.path for e in it if e.is_file() and e.name.endswith(".gtok")]
    files.sort()
    return files


def compute_tfidf(gtok_folder: str, universe_path: str, output_folder: str, *, idf_smoothing: bool = True) -> None:
    """
    Compute IDF over the corpus, then per-file TF-IDF (excluding special tokens).
    Writes:
      - {output_folder}/idf.json
      - {output_folder}/tf-idf/{accession}.json
    Notes:
      - JSON keys are strings (token ids as str) to keep JSON valid and portable.
      - If idf_smoothing=True, uses log((N+1)/(df+1)) + 1 to avoid div-by-zero and zero idf.
    """
    os.makedirs(output_folder, exist_ok=True)
    tfidf_folder = os.path.join(output_folder, "tf-idf")
    os.makedirs(tfidf_folder, exist_ok=True)

    if os.path.isfile(universe_path):
        tokenizer = Tokenizer(universe_path)
    else:
        tokenizer = Tokenizer.from_pretrained(universe_path)
    special_ids = _special_token_ids(tokenizer)

    # Pass 1: compute document frequencies
    df_counts: Dict[int, int] = defaultdict(int)
    files = list(_iter_gtok_files(gtok_folder))
    N = 0

    for path in tqdm(files, desc="Pass 1/2: computing IDF"):
        tokens = read_tokens_from_gtok(path)
        if not tokens:
            continue
        unique = {int(t) for t in tokens if int(t) not in special_ids}
        if not unique:
            continue
        for tid in unique:
            df_counts[tid] += 1
        N += 1

    if N == 0:
        # Nothing to do
        with open(os.path.join(output_folder, "idf.json"), "w") as f:
            json.dump({}, f)
        return

    # Compute IDF
    if idf_smoothing:
        # standard smooth: idf = log((N+1)/(df+1)) + 1
        idf = {tid: math.log((N + 1) / (df_counts[tid] + 1)) + 1.0 for tid in df_counts}
    else:
        # raw: idf = log(N/df); df>=1 by construction
        idf = {tid: math.log(N / df_counts[tid]) for tid in df_counts}

    # Save IDF (keys as strings for JSON)
    idf_out = {str(k): v for k, v in idf.items()}
    with open(os.path.join(output_folder, "idf.json"), "w") as f:
        json.dump(idf_out, f)

    # Pass 2: compute TF-IDF per file
    for path in tqdm(files, desc="Pass 2/2: computing TF-IDF"):
        fname = os.path.basename(path)
        accession = os.path.splitext(fname)[0]

        tokens = read_tokens_from_gtok(path)
        if not tokens:
            continue

        # count non-specials
        counts = Counter(int(t) for t in tokens if int(t) not in special_ids)
        total = sum(counts.values())
        if total == 0:
            continue

        # Only keep tokens seen in IDF (defensive; they should all be there)
        tfidf_scores = {}
        for tid, c in counts.items():
            if tid in idf:
                tf = c / total
                tfidf_scores[str(tid)] = tf * idf[tid]

        if tfidf_scores:
            np.savez(
                os.path.join(tfidf_folder, f"{accession}.npz"),
                tokens=np.array(list(tfidf_scores.keys()), dtype=np.int32),
                scores=np.array(list(tfidf_scores.values()), dtype=np.float64),
            )


def main():
    if len(sys.argv) != 4:
        print("Usage: python compute_tfidf.py <gtok_folder> <universe_path> <output_folder>", file=sys.stderr)
        sys.exit(1)

    gtok_folder = sys.argv[1]
    universe_path = sys.argv[2]
    output_folder = sys.argv[3]

    compute_tfidf(gtok_folder, universe_path, output_folder)


if __name__ == "__main__":
    main()

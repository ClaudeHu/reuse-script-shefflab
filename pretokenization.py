import argparse
import os

from gtars.models import RegionSet
from gtars.tokenizers import Tokenizer
from gtars.utils import write_tokens_to_gtok
from tqdm import tqdm


def main(args):
    bed_folder = args.bed_folder
    universe = args.universe

    gtok_folder = args.gtok_folder
    os.makedirs(gtok_folder, exist_ok=True)

    ongoing = args.ongoing

    # init_tokenizer
    if os.path.isfile(universe):
        tokenizer = Tokenizer(universe)
    else:
        tokenizer = Tokenizer.from_pretrained(universe)

    for bed_file in tqdm(os.listdir(bed_folder), "Tokenize each BED file"):

        accession = bed_file.replace(".bed.gz", "")
        output_path = os.path.join(gtok_folder, f"{accession}.gtok")
        if ongoing and os.path.isfile(output_path):
            continue
        rs = RegionSet(os.path.join(bed_folder, bed_file))
        tokens = tokenizer.tokenize(rs)
        token_ids = tokenizer.encode(tokens)
        write_tokens_to_gtok(output_path, token_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process folder and file inputs.")
    parser.add_argument("bed_folder", help="Path to folder of bed files")
    parser.add_argument(
        "universe",
        help="Path to the universe bed, or repo of a huggingface model with universe",
    )
    parser.add_argument(
        "--ongoing",
        action="store_true",
        default=False,
        help="Continue unfinished",
    )
    parser.add_argument("gtok_folder", help="Path to folder of output gtok files")

    args = parser.parse_args()
    main(args)

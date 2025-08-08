import logging
import os
import sys
from multiprocessing import cpu_count

from geniml.region2vec.main import Region2VecExModel
from geniml.region2vec.utils import Region2VecDataset
from gtars.tokenizers import Tokenizer

logging.basicConfig(level=logging.INFO)


def main():
    tokens_dir = sys.argv[1]
    universe_path = sys.argv[2]
    output_folder = sys.argv[3]
    window_size = int(sys.argv[4])
    dimension = int(sys.argv[5])
    epochs = int(sys.argv[6])

    os.makedirs(output_folder, exist_ok=True)

    save_checkpoint_folder = os.path.join(output_folder, "checkpoints")
    os.makedirs(save_checkpoint_folder, exist_ok=True)

    model_folder = os.path.join(output_folder, "model")
    os.makedirs(model_folder, exist_ok=True)

    dataset = Region2VecDataset(tokens_dir, shuffle=True, convert_to_str=True)
    model = Region2VecExModel(
        tokenizer=Tokenizer(universe_path),
        embedding_dim=dimension,
    )

    model.train(
        dataset,
        window_size=window_size,
        epochs=epochs,
        num_cpus=cpu_count() - 2,
        save_checkpoint_path=save_checkpoint_folder,
    )

    model.export(model_folder)


if __name__ == "__main__":
    main()

import ch5mpy as ch
import numpy as np
from tqdm import tqdm


def repair_group(corrupted_file: ch.Group, new_file: ch.Group, verbose: bool, in_RAM: bool) -> None:
    iter_keys = tqdm(corrupted_file.keys(), leave=False) if verbose else corrupted_file.keys()

    for key in iter_keys:
        if isinstance(iter_keys, tqdm):
            iter_keys.set_description(f"Processing key {key}")

        try:
            data = corrupted_file[key]

            if isinstance(data, ch.Dataset):
                if in_RAM:
                    new_file.create_dataset(key, data=np.array(data))
                new_file.create_dataset(key, data=data)

            else:
                new_group = new_file.create_group(key)
                repair_group(data, new_group, verbose, in_RAM)

        except RuntimeError:
            continue

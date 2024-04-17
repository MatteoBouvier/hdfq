import ch5mpy as ch
from tqdm import tqdm


def repair_group(corrupted_file: ch.Group, new_file: ch.Group, verbose: bool = False) -> None:
    iter_keys = tqdm(corrupted_file.keys()) if verbose else corrupted_file.keys()

    for key in iter_keys:
        try:
            data = corrupted_file[key]

            if isinstance(data, ch.Dataset):
                new_file.create_dataset(key, data=data)

            else:
                new_group = new_file.create_group(key)
                repair_group(data, new_group)

        except RuntimeError:
            continue

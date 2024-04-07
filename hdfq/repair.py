import ch5mpy as ch


def repair_group(corrupted_file: ch.Group, new_file: ch.Group) -> None:
    for key in corrupted_file.keys():
        try:
            data = corrupted_file[key]

            if isinstance(data, ch.Dataset):
                new_file.create_dataset(key, data=data)

            else:
                new_group = new_file.create_group(key)
                repair_group(data, new_group)

        except RuntimeError:
            continue

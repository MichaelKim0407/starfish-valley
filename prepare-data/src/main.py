import json
import os

import utils
from processors import process


def get_game_version(game_dir):
    with open(os.path.join(game_dir, 'Stardew Valley.deps.json')) as f:
        deps = json.load(f)
    key = [key for key in deps['libraries'].keys() if key.startswith('Stardew Valley/')][0]
    version = key.split('/')[1]
    return version


def update_index(output, game_version, processed_files):
    index_file = os.path.join(output, 'index.json')
    try:
        with open(index_file) as f:
            index_data = json.load(f)
    except FileNotFoundError:
        index_data = {'versions': []}

    if game_version not in index_data['versions']:
        index_data['versions'].append(game_version)
        index_data['versions'].sort(key=utils.game_version_sort_key, reverse=True)

    index_data[game_version] = processed_files

    with open(index_file, 'w') as f:
        json.dump(index_data, f)


def main(args=None):
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--game-dir', default='/game')
    parser.add_argument('--game-data-dir', default='/game/Content (unpacked)')
    parser.add_argument('--output', default='/output')
    args = parser.parse_args(args)

    game_version = get_game_version(args.game_dir)
    processed_files = process(args.game_data_dir, args.output, game_version)
    update_index(args.output, game_version, processed_files)


if __name__ == '__main__':
    main()

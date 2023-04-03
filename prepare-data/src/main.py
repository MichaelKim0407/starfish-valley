import json
import os

from processors import LanguageProcessor


def get_game_version(game_dir):
    with open(os.path.join(game_dir, 'Stardew Valley.deps.json')) as f:
        deps = json.load(f)
    key = [key for key in deps['libraries'].keys() if key.startswith('Stardew Valley/')][0]
    version = key.split('/')[1]
    return version


def prepare_data(
        game_data_dir,
        output,
        game_version,
        **kwargs,
):
    LanguageProcessor.run_all(game_data_dir, output, game_version)


def main(args=None):
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--game-dir', default='/game')
    parser.add_argument('--game-data-dir', default='/game/Content (unpacked)')
    parser.add_argument('--output', default='/output')
    args = parser.parse_args(args)

    game_version = get_game_version(args.game_dir)

    prepare_data(
        **vars(args),
        game_version=game_version,
    )


if __name__ == '__main__':
    main()

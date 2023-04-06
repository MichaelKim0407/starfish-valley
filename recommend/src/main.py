from argparse import ArgumentParser

from config import Config
from recommend import RecommendationGenerator


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument(
        'season', choices=('spring', 'summer', 'fall', 'winter'),
        help='Season',
    )
    parser.add_argument(
        'weather', choices=('sunny', 'rainy'),
        help='Weather',
    )
    parser.add_argument(
        '--top', '-n', type=int, default=-1,
        help='Only display top n items. Can be used with --min-score (whichever is more limiting).',
    )
    parser.add_argument(
        '--min-score', '-m', type=float, default=0.0,
        help='Only display items that has at least m score. Can be used with --top (whichever is more limiting).',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print additional information, such as fish ID, score details, English names, etc.',
    )
    parser.add_argument(
        '--config-file', '-c', default='../config/recommend.conf',
        help="Specify a configuration file. Default: '../config/recommend.conf'",
    )
    args = parser.parse_args(args)

    conf = Config(args.config_file)
    recommend_gen = RecommendationGenerator(conf, args.season, args.weather)
    from pprint import pprint
    for fish in recommend_gen[:args.top]:
        if fish.score < args.min_score:
            continue
        pprint(
            fish.output_verbose if args.verbose else fish.output,
            sort_dicts=False,
        )


if __name__ == '__main__':
    main()

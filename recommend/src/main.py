from argparse import ArgumentParser

from config import Config
from recommend import RecommendationGenerator


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('season', choices=('spring', 'summer', 'fall', 'winter'))
    parser.add_argument('weather', choices=('sunny', 'rainy'))
    parser.add_argument('--top', '-n', type=int, default=-1)
    parser.add_argument('--min-score', '-m', type=float, default=0.0)
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--config-file', '-c', default='../config/recommend.conf')
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

from argparse import ArgumentParser

from config import Config
from recommend import RecommendationGenerator


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('season', choices=('spring', 'summer', 'fall', 'winter'))
    parser.add_argument('weather', choices=('sunny', 'rainy'))
    parser.add_argument('--config-file', '-c', default='../config/recommend.conf')
    args = parser.parse_args(args)

    conf = Config(args.config_file)
    recommend_gen = RecommendationGenerator(conf, args.season, args.weather)
    from pprint import pprint
    pprint(recommend_gen._allowed_fish)


if __name__ == '__main__':
    main()

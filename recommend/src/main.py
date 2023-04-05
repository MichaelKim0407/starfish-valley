from argparse import ArgumentParser

from config import Config


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('season', choices=('spring', 'summer', 'fall', 'winter'))
    parser.add_argument('weather', choices=('sunny', 'rainy'))
    parser.add_argument('--config-file', '-c', default='../config/recommend.conf')
    args = parser.parse_args(args)

    conf = Config(args.config_file)
    print(conf.data_file, conf.unlocked_areas, conf.fishing_level)


if __name__ == '__main__':
    main()

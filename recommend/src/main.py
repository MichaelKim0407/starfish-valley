import typing
from argparse import ArgumentParser
from functools import cached_property

from config import Config
from recommend import RecommendationGenerator, FishRecommendationScoreCalculator
from rendering import RenderTable


class Main:
    _parser = None

    @classmethod
    def parser(cls) -> ArgumentParser:
        if cls._parser is not None:
            return cls._parser

        parser = ArgumentParser()
        parser.add_argument(
            '--config-file', '-c', default='../config/recommend.conf',
            help="Specify a configuration file. Default: '../config/recommend.conf'",
        )

        parser.add_argument(
            'season', choices=('spring', 'summer', 'fall', 'winter'),
            help='Season',
        )
        parser.add_argument(
            'weather', choices=('sunny', 'rainy'),
            help='Weather',
        )
        parser.add_argument(
            '--top', '-n', type=int, default=None,
            help='Only display top n items. '
                 'If there is a draw, all items with the same score will be displayed. '
                 'Can be used with --min-score (whichever is more limiting).',
        )
        parser.add_argument(
            '--min-score', '-m', type=float, default=None,
            help='Only display items that has at least m score. '
                 'Can be used with --top (whichever is more limiting).',
        )

        parser.add_argument(
            '--verbose', '-v', action='store_true',
            help='Print additional information, such as fish ID, score details, English names, etc.',
        )
        cls._parser = parser
        return parser

    config_file: str

    season: str
    weather: str
    top: int | None
    min_score: float | None

    verbose: bool

    def __init__(self, args=None):
        self._args = self.parser().parse_args(args)

    def __getattr__(self, arg: str):
        return getattr(self._args, arg)

    @cached_property
    def _config(self) -> Config:
        return Config(self.config_file)

    @cached_property
    def _recommend_gen(self) -> RecommendationGenerator:
        return RecommendationGenerator(self._config, self.season, self.weather)

    @property
    def _data(self) -> typing.Iterator[FishRecommendationScoreCalculator]:
        return self._recommend_gen.get(top=self.top, min_score=self.min_score)

    @property
    def _output(self) -> typing.Iterator[dict]:
        if not self.verbose:
            for fish in self._data:
                yield fish.output

        else:
            for fish in self._data:
                yield fish.output_verbose

    @cached_property
    def _table_renderer(self) -> RenderTable:
        return RenderTable(
            self._output,
        )

    def __call__(self):
        print(self._table_renderer)


if __name__ == '__main__':
    Main()()

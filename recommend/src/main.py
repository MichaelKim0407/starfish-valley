import json
import typing
from argparse import ArgumentParser
from functools import cached_property
from pprint import pprint

from returns import returns

from config import Config
from recommend import RecommendationGenerator, FishRecommendationScoreCalculator
from rendering import RenderTable


class Main:
    _parser = None

    FORMAT_TABLE = 'table'
    FORMAT_PPRINT = 'pprint'
    FORMAT_JSON = 'json'

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

        parser.add_argument(
            '--format', '-f', choices=(cls.FORMAT_TABLE, cls.FORMAT_PPRINT, cls.FORMAT_JSON), default=cls.FORMAT_TABLE,
            help=f'Output format. Default: {cls.FORMAT_TABLE}.',
        )
        cls._parser = parser
        return parser

    config_file: str

    season: str
    weather: str
    top: int | None
    min_score: float | None

    verbose: bool
    format: str

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
        for fish in self._data:
            yield fish.output(verbose=self.verbose, table=self.format == self.FORMAT_TABLE)

    @staticmethod
    @returns(list)
    def _format_locations_verbose(locations: list[dict]) -> list[str]:
        for location in locations:
            yield f"[{location['Key']}] {location['Name']}"

    @staticmethod
    @returns(list)
    def _format_translatable_names_verbose(names: list[dict[str, str]] | dict[str, str]) -> list[str]:
        if isinstance(names, dict):
            names = [names]

        for name in names:
            if 'English name' in name:
                yield f"[{name['English name']}] {name['Name']}"
            else:
                yield name['Name']

    @cached_property
    @returns(dict)
    def _formatters(self) -> dict:
        if not self.verbose:
            return

        yield 'Name', self._format_translatable_names_verbose
        yield 'Locations', self._format_locations_verbose
        yield 'Bundles', self._format_translatable_names_verbose
        yield 'Loved by', self._format_translatable_names_verbose
        yield 'Liked by', self._format_translatable_names_verbose

    @cached_property
    def _table_renderer(self) -> RenderTable:
        return RenderTable(
            self._output,
            formatters=self._formatters,
        )

    def _pprint(self):
        for item in self._output:
            pprint(item)

    def _print_json(self):
        for item in self._output:
            print(json.dumps(item, indent=2))

    def __call__(self):
        if self.format == self.FORMAT_TABLE:
            print(self._table_renderer)
        elif self.format == self.FORMAT_PPRINT:
            self._pprint()
        elif self.format == self.FORMAT_JSON:
            self._print_json()


if __name__ == '__main__':
    Main()()

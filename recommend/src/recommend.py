import json
import typing
from functools import cached_property

from returns import returns

from config import Config
from utils import merge


class RecommendationGenerator:
    def __init__(self, config: Config, season: str, weather: str):
        self.config = config
        self.season = season
        self.weather = weather

    @cached_property
    def _game_data(self) -> dict:
        with open(self.config.data_file) as f:
            return json.load(f)

    @cached_property
    def is_english(self) -> bool:
        return self._game_data['lang_code'] is None

    @cached_property
    @returns(dict)
    def _fish(self) -> dict[str, dict]:
        for fish_id, fish in self._game_data['fish'].items():
            yield fish_id, fish

    @cached_property
    @returns(lambda iterable: sorted(iterable, key=FishRecommendationScoreCalculator.sort_key))
    def _scores(self) -> list['FishRecommendationScoreCalculator']:
        for fish_id, fish in self._fish.items():
            score = FishRecommendationScoreCalculator(self, fish)
            if not score:
                continue
            yield score

    def get(self, *, top: int = None, min_score: float = None) -> typing.Iterator['FishRecommendationScoreCalculator']:
        if top is not None and top <= 0:
            return

        count = 0
        last_score = None

        for score in self._scores:
            if min_score is not None and score.score < min_score:
                return

            if top is not None:
                if count >= top:
                    if score.score < last_score:
                        return

            yield score
            count += 1
            last_score = score.score


class FishRecommendationScoreCalculator:
    SEASON = 'season'
    WEATHER = 'weather'
    BUNDLE = 'bundle'
    GIFT = 'gift'
    FAVORITE = 'favorite'

    FACTORS = (
        SEASON,
        WEATHER,
        BUNDLE,
        GIFT,
        FAVORITE,
    )

    def __init__(self, parent: RecommendationGenerator, fish: dict):
        self.parent = parent
        self.fish = fish

    @property
    def _config(self) -> Config:
        return self.parent.config

    @property
    def _fish_id(self) -> str:
        return self.fish['id']

    def _skip_rainy_winter(self, location: dict) -> bool:
        if self._config.winter_rain_totem:
            return False
        if location['key'].startswith('Island'):
            return False
        if location['season'] != 'winter':
            return False
        if 'sunny' in self.fish['weather']:
            return False
        return True

    @cached_property
    @returns(list)
    def _unlocked_locations(self) -> list[dict]:
        if not self.fish['locations']:
            return

        for location in self.fish['locations']:
            if location['key'] not in self._config.unlocked_areas:
                continue
            if self._skip_rainy_winter(location):
                continue
            yield location

    @cached_property
    @returns(list)
    def _appearing_locations(self) -> list[dict]:
        for location in self._unlocked_locations:
            if location['season'] != self.parent.season:
                continue
            yield location

    @cached_property
    def _appearing(self) -> bool:
        if self._config.fishing_level < self.fish['min_level']:
            return False
        if self.parent.weather not in self.fish['weather']:
            return False
        if not self._appearing_locations:
            return False
        return True

    def __bool__(self) -> bool:
        return self._appearing

    @cached_property
    @returns(lambda items: sorted(items, key=('spring', 'summer', 'fall', 'winter').index))
    @returns(set)
    def _available_seasons(self) -> set[str]:
        # use unlocked locations instead of all locations
        for location in self._unlocked_locations:
            yield location['season']

    @cached_property
    def _season_factor(self) -> float:
        return self._config.rec_season_factor * (4 - len(self._available_seasons))

    @cached_property
    def _weather_factor(self) -> float:
        if len(self.fish['weather']) == 2:
            return 0.0
        if self.fish['weather'][0] == 'sunny':
            return self._config.rec_weather_factor_sunny
        else:
            return self._config.rec_weather_factor_rainy

    @cached_property
    @returns(list)
    def _bundles(self) -> list[dict]:
        if not self.fish['bundles']:
            return

        for bundle in self.fish['bundles']:
            bundle_en_name = bundle['en_name']
            if bundle_en_name not in self._config.bundles:
                continue
            if self._fish_id not in self._config.bundle(bundle_en_name):
                continue
            yield bundle

    @cached_property
    def _bundle_factor(self) -> float:
        if self._bundles:
            return self._config.rec_bundle_factor
        else:
            return 0.0

    @cached_property
    @returns(merge)
    def _gifts(self) -> dict[str, list[dict]]:
        if not self.fish['gifts']:
            return

        for preference_type, characters in self.fish['gifts'].items():
            for character in characters:
                if self._fish_id not in self._config.gifts(character['key']):
                    continue
                yield preference_type, character

    @cached_property
    def _gift_factor(self) -> float:
        if self._gifts:
            return self._config.rec_gift_factor
        else:
            return 0.0

    @cached_property
    def _favorite_factor(self) -> float:
        return self._config.favorite(self._fish_id)

    @cached_property
    @returns(dict)
    def factors(self) -> dict[str, float]:
        if not self._appearing:
            return

        for factor_name in self.FACTORS:
            factor_attr = f'_{factor_name}_factor'
            factor_score = getattr(self, factor_attr)
            if factor_score == 0.0:
                continue
            yield factor_name, factor_score

    @cached_property
    @returns(sum)
    def score(self) -> float:
        if not self._appearing:
            return

        yield from self.factors.values()

    @staticmethod
    def sort_key(item: 'FishRecommendationScoreCalculator'):
        return -item.score, item.fish['en_name']

    @returns(dict)
    def _get_name_verbose(self, name: str, en_name: str) -> dict[str, str]:
        yield 'Name', name
        if not self.parent.is_english:
            yield 'English name', en_name

    @cached_property
    def _output_name_verbose(self) -> dict[str, str]:
        return self._get_name_verbose(self.fish['name'], self.fish['en_name'])

    @cached_property
    @returns(list)
    def _output_locations(self) -> list[str]:
        for location in self._appearing_locations:
            yield location['name']

    @cached_property
    @returns(list)
    def _output_locations_verbose(self) -> list[dict]:
        for location in self._appearing_locations:
            yield {
                'Name': location['name'],
                'Key': location['key'],
            }

    @staticmethod
    def _output_preference_type(preference_type: str) -> str:
        return preference_type.rstrip('s').capitalize() + 'd by'

    @cached_property
    @returns(merge)
    def _output_gifts(self) -> dict[str, list[str]]:
        for preference_type, characters in self._gifts.items():
            preference_type = self._output_preference_type(preference_type)
            for character in characters:
                yield preference_type, character['name']

    @cached_property
    @returns(merge)
    def _output_gifts_verbose(self) -> dict[str, list[str]]:
        for preference_type, characters in self._gifts.items():
            preference_type = self._output_preference_type(preference_type)
            for character in characters:
                yield (
                    preference_type,
                    self._get_name_verbose(character['name'], character['key']),
                )

    @cached_property
    @returns(list)
    def _output_bundles(self) -> list[str]:
        for bundle in self._bundles:
            yield bundle['name']

    @cached_property
    @returns(list)
    def _output_bundles_verbose(self) -> list[str]:
        for bundle in self._bundles:
            yield self._get_name_verbose(bundle['name'], bundle['en_name'])

    @returns(dict)
    def output(self, *, verbose: bool = False, table: bool = False) -> dict:
        if table:
            def table_col_split(col_name: str):
                return tuple(col_name.split())
        else:
            def table_col_split(col_name: str):
                return col_name

        if verbose:
            yield 'ID', self._fish_id
            yield 'Name', self._output_name_verbose
        else:
            yield 'Name', self.fish['name']

        yield 'Score', self.score
        if verbose:
            yield 'Factors', self.factors

        if verbose:
            yield 'Locations', self._output_locations_verbose
            yield table_col_split('Available seasons'), self._available_seasons
            yield table_col_split('Available weathers'), self.fish['weather']
        else:
            yield 'Locations', self._output_locations

        yield 'Hours', self.fish['time_ranges']

        output_gifts = self._output_gifts_verbose if verbose else self._output_gifts
        if table:
            output_gifts = {
                'Loved by': output_gifts.get('Loved by'),
                'Liked by': output_gifts.get('Liked by'),
            }
        yield from output_gifts.items()

        if self._bundles:
            yield 'Bundles', self._output_bundles_verbose if verbose else self._output_bundles
        elif table:
            yield 'Bundles', []

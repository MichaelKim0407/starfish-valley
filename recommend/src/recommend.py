import json
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
            yield FishRecommendationScoreCalculator(self, fish)

    def __getitem__(self, item):
        return self._scores[item]


class FishRecommendationScoreCalculator:
    SEASON = 'season'
    WEATHER = 'weather'
    BUNDLE = 'bundle'
    GIFT = 'gift'

    FACTORS = (
        SEASON,
        WEATHER,
        BUNDLE,
        GIFT,
    )

    def __init__(self, parent: RecommendationGenerator, fish: dict):
        self.parent = parent
        self.fish = fish

    @property
    def _config(self) -> Config:
        return self.parent.config

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

    @cached_property
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
    def _bundle_factor(self) -> float:
        if self.fish['bundles']:
            return self._config.rec_bundle_factor
        else:
            return 0.0

    @cached_property
    def _gift_factor(self) -> float:
        if self.fish['gifts']:
            return self._config.rec_gift_factor
        else:
            return 0.0

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
            yield -1.0
            return

        yield from self.factors.values()

    @staticmethod
    def sort_key(item: 'FishRecommendationScoreCalculator'):
        return -item.score, item.fish['en_name']

    @cached_property
    @returns(list)
    def _output_locations(self) -> list[str]:
        for location in self._appearing_locations:
            yield location['name']

    @staticmethod
    def _output_preference_type(preference_type: str) -> str:
        return preference_type.rstrip('s').capitalize() + 'd by'

    @cached_property
    @returns(merge)
    def _output_gifts(self) -> dict[list[str]]:
        if not self.fish['gifts']:
            return
        for preference_type, characters in self.fish['gifts'].items():
            preference_type = self._output_preference_type(preference_type)
            for character in characters:
                yield preference_type, character['name']

    @cached_property
    @returns(dict)
    def output(self) -> dict:
        yield 'Name', self.fish['name']
        yield 'Score', self.score
        yield 'Locations', self._output_locations
        yield 'Hours', self.fish['time_ranges']
        yield from self._output_gifts.items()

    @cached_property
    @returns(list)
    def _output_locations_verbose(self) -> list[dict]:
        for location in self._appearing_locations:
            yield {
                'Name': location['name'],
                'Key': location['key'],
            }

    @cached_property
    @returns(merge)
    def _output_gifts_verbose(self) -> dict[list[str]]:
        if not self.fish['gifts']:
            return
        for preference_type, characters in self.fish['gifts'].items():
            preference_type = self._output_preference_type(preference_type)
            for character in characters:
                if self.parent.is_english:
                    c = character['name']
                else:
                    c = {
                        'Name': character['name'],
                        'English name': character['key'],
                    }
                yield preference_type, c

    @cached_property
    @returns(dict)
    def output_verbose(self) -> dict:
        yield 'ID', self.fish['id']
        yield 'Name', self.output['Name']
        if not self.parent.is_english:
            yield 'English name', self.fish['en_name']
        yield 'Required level', self.fish['min_level']

        yield 'Score', self.output['Score']
        yield 'Factors', self.factors

        yield 'Locations', self._output_locations_verbose
        yield 'Available seasons', self._available_seasons

        yield 'Hours', self.output['Hours']

        yield from self._output_gifts_verbose.items()

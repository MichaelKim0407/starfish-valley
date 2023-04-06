import json
from functools import cached_property

from returns import returns

from config import Config


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

    def _is_location_allowed(self, location) -> bool:
        if location['season'] != self.season:
            return False
        if location['key'] not in self.config.unlocked_areas:
            return False
        return True

    @returns(list)
    def _allowed_locations(self, locations: list[dict]) -> list[dict]:
        if not locations:
            return

        for location in locations:
            if not self._is_location_allowed(location):
                continue
            yield location

    @returns(set)
    def _available_seasons(self, locations: list[dict]) -> set[str]:
        if not locations:
            return

        for location in locations:
            yield location['season']

    def _prepare_fish(self, fish: dict):
        fish['allowed_locations'] = self._allowed_locations(fish['locations'])
        fish['available_seasons'] = self._available_seasons(fish['locations'])

    @cached_property
    @returns(dict)
    def _all_fish(self) -> dict[str, dict]:
        for fish_id, fish in self._game_data['fish'].items():
            self._prepare_fish(fish)
            yield fish_id, fish

    def _is_fish_allowed(self, fish: dict) -> bool:
        if self.config.fishing_level < fish['min_level']:
            return False
        if self.weather not in fish['weather']:
            return False
        if not fish['allowed_locations']:
            return False
        return True

    @cached_property
    @returns(dict)
    def _allowed_fish(self) -> dict[str, dict]:
        for fish_id, fish in self._all_fish.items():
            if not self._is_fish_allowed(fish):
                continue
            yield fish_id, fish

    @cached_property
    @returns(lambda iterable: sorted(iterable, key=FishRecommendationScoreCalculator.sort_key))
    def _scores(self) -> list['FishRecommendationScoreCalculator']:
        for fish_id, fish in self._allowed_fish.items():
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

    @cached_property
    def _season_factor(self) -> float:
        return self._config.rec_season_factor * (4 - len(self.fish['available_seasons']))

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
        for factor_name in self.FACTORS:
            factor_attr = f'_{factor_name}_factor'
            factor_score = getattr(self, factor_attr)
            if factor_score == 0.0:
                continue
            yield factor_name, factor_score

    @cached_property
    @returns(sum)
    def score(self) -> float:
        yield from self.factors.values()

    @staticmethod
    def sort_key(item: 'FishRecommendationScoreCalculator'):
        return -item.score, item.fish['en_name']

    @cached_property
    @returns(dict)
    def output(self) -> dict:
        yield 'Name', self.fish['name']
        yield 'Score', self.score
        yield 'Locations', [
            location['name']
            for location in self.fish['allowed_locations']
        ]
        yield 'Hours', self.fish['time_ranges']

    @cached_property
    @returns(dict)
    def output_verbose(self) -> dict:
        yield 'ID', self.fish['id']
        yield 'Name', self.output['Name']
        if not self.parent.is_english:
            yield 'English name', self.fish['en_name']

        yield 'Score', self.output['Score']
        yield 'Factors', self.factors

        yield 'Locations', [
            {
                'Name': location['name'],
                'Key': location['key'],
            }
            for location in self.fish['allowed_locations']
        ]

        yield 'Hours', self.output['Hours']

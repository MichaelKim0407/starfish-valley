import os
import typing
from functools import cached_property

from returns import returns

from . import JsonFileProcessor
from .fish import FishFileProcessor
from .location_names import LocationNameProcessor

FishId = typing.TypeVar('FishId', bound=str)
LocationVariation = typing.TypeVar('LocationVariation', bound=int)
Season = typing.TypeVar('Season', bound=str)
LocationKey = typing.TypeVar('LocationKey', bound=str)


def skip_empty_values(iterable):
    for key, value in iterable:
        if not value:
            continue
        yield key, value


class LocationFileProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'Locations')
    USE_LOCALE = False

    SKIP_LOCATIONS = {
        'fishingGame',
        'Temp',
    }

    SEASON_SKIP = {'-1'}
    SEASONS = ('spring', 'summer', 'fall', 'winter')

    RESULT_SUBKEY = 'locations'

    RESULT_LOCATION_KEY = 'key'
    RESULT_LOCATION_VARIATION = 'variation'
    RESULT_LOCATION_VARIATION_ORIGINAL = 'variation_orig'
    RESULT_LOCATION_NAME = 'name'
    RESULT_SEASON = 'season'

    @classmethod
    @returns(dict)
    def parse_season(cls, season: str) -> dict[FishId, LocationVariation]:
        if season in cls.SEASON_SKIP:
            return

        items = season.split(' ')
        for i in range(0, len(items), 2):
            yield items[i], int(items[i + 1])

    @classmethod
    @returns(dict)
    @returns(skip_empty_values)
    def parse_location_value(cls, value: str) -> dict[Season, dict[FishId, LocationVariation]]:
        for season_name, season_value in zip(cls.SEASONS, value.split('/')[4:8]):
            yield season_name, cls.parse_season(season_value)

    @cached_property
    @returns(dict)
    @returns(skip_empty_values)
    def data(self) -> dict[LocationKey, dict[Season, dict[FishId, LocationVariation]]]:
        for key, value in self.raw_data.items():
            if key in self.SKIP_LOCATIONS:
                continue
            yield key, self.parse_location_value(value)

    @classmethod
    @returns(list)
    def get_fish_location_data(
            cls,
            result: dict,
            location_key: LocationKey,
            location_var: LocationVariation,
            season: Season,
    ) -> list[dict[str, typing.Any]]:
        if location_key in LocationNameProcessor.LOCATION_VARIATIONS and location_var == -1:
            for var in LocationNameProcessor.LOCATION_VARIATIONS[location_key]:
                yield {
                    cls.RESULT_LOCATION_KEY: location_key,
                    cls.RESULT_LOCATION_VARIATION: var,
                    cls.RESULT_LOCATION_VARIATION_ORIGINAL: location_var,
                    cls.RESULT_LOCATION_NAME: result[LocationNameProcessor.RESULT_KEY][location_key][var],
                    cls.RESULT_SEASON: season,
                }
            return

        yield {
            cls.RESULT_LOCATION_KEY: location_key,
            cls.RESULT_LOCATION_VARIATION: location_var,
            cls.RESULT_LOCATION_VARIATION_ORIGINAL: location_var,
            cls.RESULT_LOCATION_NAME: result[LocationNameProcessor.RESULT_KEY][location_key][location_var],
            cls.RESULT_SEASON: season,
        }

    def __call__(self, result: dict):
        for location_key, location_fish in self.data.items():
            for season, season_fish in location_fish.items():
                for fish_id, location_var in season_fish.items():
                    fish_data = result[FishFileProcessor.RESULT_KEY][fish_id]
                    if self.RESULT_SUBKEY not in fish_data:
                        fish_data[self.RESULT_SUBKEY] = []
                    fish_data[self.RESULT_SUBKEY].extend(self.get_fish_location_data(
                        result,
                        location_key,
                        location_var,
                        season,
                    ))

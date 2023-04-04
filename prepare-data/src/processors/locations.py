import os
import typing
from functools import cached_property

from returns import returns

from utils import skip_empty_values, merge
from . import JsonFileProcessor
from .fish import FishProcessor
from .location_names import LocationNameProcessor

FishId = typing.TypeVar('FishId', bound=str)
LocationVariation = typing.TypeVar('LocationVariation', bound=int)
Season = typing.TypeVar('Season', bound=str)
LocationKey = typing.TypeVar('LocationKey', bound=str)


class LocationProcessor(JsonFileProcessor):
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

    @cached_property
    def _location_name_processor(self) -> LocationNameProcessor:
        return LocationNameProcessor(self.parent)

    @property
    def location_name_lookup(self):
        return self._location_name_processor.location_names

    def get_fish_location_data(
            self,
            location_key: LocationKey,
            location_var: LocationVariation,
            season: Season,
    ) -> typing.Iterator[dict[str, typing.Any]]:
        if location_key in LocationNameProcessor.LOCATION_VARIATIONS and location_var == -1:
            for var in LocationNameProcessor.LOCATION_VARIATIONS[location_key]:
                yield {
                    self.RESULT_LOCATION_KEY: location_key,
                    self.RESULT_LOCATION_VARIATION: var,
                    self.RESULT_LOCATION_VARIATION_ORIGINAL: location_var,
                    self.RESULT_LOCATION_NAME: self.location_name_lookup[location_key][var],
                    self.RESULT_SEASON: season,
                }
            return

        yield {
            self.RESULT_LOCATION_KEY: location_key,
            self.RESULT_LOCATION_VARIATION: location_var,
            self.RESULT_LOCATION_VARIATION_ORIGINAL: location_var,
            self.RESULT_LOCATION_NAME: self.location_name_lookup[location_key][location_var],
            self.RESULT_SEASON: season,
        }

    @cached_property
    @returns(merge)
    def rearranged_data(self) -> dict[FishId, list]:
        for location_key, location_fish in self.data.items():
            for season, season_fish in location_fish.items():
                for fish_id, location_var in season_fish.items():
                    for fish_location in self.get_fish_location_data(
                            location_key,
                            location_var,
                            season,
                    ):
                        yield fish_id, fish_location

    def __call__(self, result: dict):
        for fish_id, fish_locations in self.rearranged_data.items():
            result[FishProcessor.RESULT_KEY][fish_id][self.RESULT_SUBKEY] = fish_locations

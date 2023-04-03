import os
import typing
from functools import cached_property

from returns import returns

from . import JsonFileProcessor
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

    @staticmethod
    @returns(dict)
    def parse_season(season: str) -> dict[FishId, LocationVariation]:
        if season == '-1':
            return

        items = season.split(' ')
        for i in range(0, len(items), 2):
            yield items[i], int(items[i + 1])

    @classmethod
    @returns(dict)
    @returns(skip_empty_values)
    def parse_location_value(cls, value: str) -> dict[Season, dict[FishId, LocationVariation]]:
        spring, summer, fall, winter = value.split('/')[4:8]
        yield 'spring', cls.parse_season(spring)
        yield 'summer', cls.parse_season(summer)
        yield 'fall', cls.parse_season(fall)
        yield 'winter', cls.parse_season(winter)

    @cached_property
    @returns(dict)
    @returns(skip_empty_values)
    def data(self) -> dict[LocationKey, dict[Season, dict[FishId, LocationVariation]]]:
        for key, value in self.raw_data.items():
            if key in self.SKIP_LOCATIONS:
                continue
            yield key, self.parse_location_value(value)

    @staticmethod
    @returns(list)
    def get_fish_location_data(
            result: dict,
            location_key: LocationKey,
            location_var: LocationVariation,
            season: Season,
    ) -> list[dict[str, typing.Any]]:
        if location_key in LocationNameProcessor.LOCATION_VARIATIONS and location_var == -1:
            for var in LocationNameProcessor.LOCATION_VARIATIONS[location_key]:
                yield {
                    'key': location_key,
                    'variation': var,
                    'variation_orig': location_var,
                    'name': result['location_names'][location_key][var],
                    'season': season,
                }
            return

        yield {
            'key': location_key,
            'variation': location_var,
            'variation_orig': location_var,
            'name': result['location_names'][location_key][location_var],
            'season': season,
        }

    def __call__(self, result: dict):
        for location_key, location_fish in self.data.items():
            for season, season_fish in location_fish.items():
                for fish_id, location_var in season_fish.items():
                    fish_data = result['fish'][fish_id]
                    if 'locations' not in fish_data:
                        fish_data['locations'] = []
                    fish_data['locations'].extend(self.get_fish_location_data(
                        result,
                        location_key,
                        location_var,
                        season,
                    ))

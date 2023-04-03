import os
import typing
from functools import cached_property

from returns import returns

from . import JsonFileProcessor

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

    # https://stardewvalleywiki.com/Modding:Fish_data#Spawn_locations
    LOCATION_VARIATIONS = {
        'Forest': {
            0: 'river',
            1: 'pond',
        },
        'IslandWest': {
            1: 'ocean',
            2: 'freshwater',
        },
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
            yield key, self.parse_location_value(value)

    @classmethod
    def get_location_full_name(cls, location_key: LocationKey, location_var: LocationVariation) -> typing.Iterator[str]:
        if location_key not in cls.LOCATION_VARIATIONS:
            yield location_key
            return

        if location_var != -1:
            yield f'{location_key} ({cls.LOCATION_VARIATIONS[location_key][location_var]})'
            return

        for var in cls.LOCATION_VARIATIONS[location_key].values():
            yield f'{location_key} ({var})'

    def __call__(self, result: dict):
        for location_key, location_fish in self.data.items():
            for season, season_fish in location_fish.items():
                for fish_id, location_var in season_fish.items():
                    fish_data = result['fish'][fish_id]
                    if 'locations' not in fish_data:
                        fish_data['locations'] = []
                    for location_name in self.get_location_full_name(location_key, location_var):
                        fish_data['locations'].append({
                            'name': location_name,
                            'season': season,
                        })

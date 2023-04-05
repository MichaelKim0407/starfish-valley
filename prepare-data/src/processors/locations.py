import os
import typing
from functools import cached_property

from returns import returns

from utils import skip_empty_values, merge
from .base import JsonFileProcessor, AbstractProcessor
from .fish import FishProcessor

FishId = typing.TypeVar('FishId', bound=str)
LocationVariation = typing.TypeVar('LocationVariation', bound=str)
Season = typing.TypeVar('Season', bound=str)
LocationKey = typing.TypeVar('LocationKey', bound=str)


class LocationNameProcessor(AbstractProcessor):
    # https://stardewvalleywiki.com/Modding:Location_data#GameLocation_Names
    # https://stardewvalleywiki.com/Modding:Fish_data#Spawn_locations
    # TODO localize
    LOCATIONS = {
        'UndergroundMine': ('Mines', None),
        'Desert': ('Calico Desert', None),
        'Forest': (
            'Cindersap Forest',
            {
                '0': 'river',
                '1': 'pond',
            },
        ),
        'Town': ('Pelican Town', None),
        'Mountain': ('Mountain Lake', None),
        'Backwoods': ('Backwoods', None),
        'Beach': ('Pelican Beach', None),
        'Woods': ('Secret Woods', None),
        'Sewer': ('Sewer', None),
        'BugLand': ('Mutant Bug Lair', None),
        'WitchSwamp': ("Witch's Swamp", None),
        'IslandNorth': ('Ginger Island north', None),
        'IslandSouth': ('Ginger Island south', None),
        'IslandWest': (
            'Ginger Island west',
            {
                '1': 'ocean',
                '2': 'freshwater',
            }
        ),
        'IslandSouthEast': ('Ginger Island southeast', None),
        'IslandSouthEastCave': ('Pirate Cove', None),
        'IslandSecret': ('Ginger Island secret location', None),
    }

    LOCATION_VARIATION_ANY = '-1'

    RESULT_KEY = 'location_names'

    @returns(dict)
    def process_location(self, location_key: LocationKey) -> dict[LocationVariation, str]:
        location_name_locale_dict, variations = self.LOCATIONS[location_key]
        location_name = self.parent.translate(location_name_locale_dict)
        if variations is None:
            yield self.LOCATION_VARIATION_ANY, location_name
            return

        for variation, variation_locale_dict in variations.items():
            variation_name = self.parent.translate(variation_locale_dict)
            yield variation, f'{location_name} ({variation_name})'

    @cached_property
    @returns(dict)
    def location_names(self) -> dict[LocationKey, dict[LocationVariation, str]]:
        for location_key in self.LOCATIONS:
            yield location_key, self.process_location(location_key)

    def __call__(self, result: dict):
        result[self.RESULT_KEY] = self.location_names


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
            yield items[i], items[i + 1]

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
        variations = LocationNameProcessor.LOCATIONS[location_key][1]
        if (
                variations is not None
                and location_var == LocationNameProcessor.LOCATION_VARIATION_ANY
        ):
            for var in variations:
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

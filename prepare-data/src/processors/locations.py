import os
import typing
from functools import cached_property

from returns import returns

from utils import skip_empty_values, merge
from .base import JsonFileProcessor
from .fish import FishProcessor
from .name_mapping import NameMappingMixin

FishId = typing.TypeVar('FishId', bound=str)
LocationVariation = typing.TypeVar('LocationVariation', bound=int)
Season = typing.TypeVar('Season', bound=str)
LocationKey = typing.TypeVar('LocationKey', bound=str)


class LocationNameProcessor(JsonFileProcessor, NameMappingMixin):
    FILENAME = os.path.join('Strings', 'StringsFromCSFiles')

    # https://stardewvalleywiki.com/Modding:Location_data#GameLocation_Names
    # TODO localize secondary names
    MAPPING = {
        'UndergroundMine': ('MapPage.cs.11098', None),
        'Desert': ('MapPage.cs.11062', None),
        'Forest': ('MapPage.cs.11186', None),  # Cindersap Forest
        'Town': ('MapPage.cs.11190', None),  # Pelican Town
        'Mountain': ('MapPage.cs.11177', None),  # Mountain Lake
        'Backwoods': ('MapPage.cs.11180', None),
        'Beach': ('MapPage.cs.11174', None),
        'Woods': ('MapPage.cs.11114', None),  # Secret Woods
        'Sewer': ('MapPage.cs.11089', None),
        'BugLand': (None, 'Mutant Bug Lair'),
        'WitchSwamp': (None, "Witch's Swamp"),
        'IslandNorth': ('IslandName', 'north'),
        'IslandSouth': ('IslandName', 'south'),
        'IslandWest': ('IslandName', 'west'),
        'IslandSouthEast': ('IslandName', 'southeast'),
        'IslandSouthEastCave': (None, 'Pirate Cove'),
        'IslandSecret': ('IslandName', 'secret location'),
    }

    # https://stardewvalleywiki.com/Modding:Fish_data#Spawn_locations
    # TODO localize following words
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

    RESULT_KEY = 'location_names'

    @returns(dict)
    def process_location(self, location_key: LocationKey) -> dict[LocationVariation, str]:
        location_name = self.get_localized_name(location_key)
        if location_key not in self.LOCATION_VARIATIONS:
            yield -1, location_name
            return

        for variation, variation_locale_dict in self.LOCATION_VARIATIONS[location_key].items():
            variation_name = self.parent.translate(variation_locale_dict)
            yield variation, f'{location_name} ({variation_name})'

    @cached_property
    @returns(dict)
    def location_names(self) -> dict[LocationKey, dict[LocationVariation, str]]:
        for location_key in self.MAPPING:
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

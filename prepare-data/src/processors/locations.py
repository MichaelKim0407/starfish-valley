import os
import typing
from functools import cached_property

from returns import returns

from utils import merge
from . import t
from .base import JsonFileProcessor, AbstractProcessor


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

    @returns(dict)
    def _process_location(self, location_key: t.LocationKey) -> dict[t.LocationVariation, t.LocationName]:
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
    def _names(self) -> dict[t.LocationKey, dict[t.LocationVariation, t.LocationName]]:
        for location_key in self.LOCATIONS:
            yield location_key, self._process_location(location_key)

    def __getitem__(self, key: tuple[t.LocationKey, t.LocationVariation]) -> t.LocationName:
        location_key, location_variation = key
        return self._names[location_key][location_variation]


class LocationProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'Locations')
    USE_LOCALE = False

    SKIP_LOCATIONS = {
        'fishingGame',
        'Temp',
    }

    SEASON_SKIP = {'-1'}
    SEASONS = ('spring', 'summer', 'fall', 'winter')

    RESULT_LOCATION_KEY = 'key'
    RESULT_LOCATION_VARIATION = 'variation'
    RESULT_LOCATION_VARIATION_ORIGINAL = 'variation_orig'
    RESULT_LOCATION_NAME = 'name'
    RESULT_SEASON = 'season'

    @classmethod
    @returns(dict)
    def _parse_season_value(cls, value: str) -> dict[t.FishId, t.LocationVariation]:
        if value in cls.SEASON_SKIP:
            return

        items = value.split(' ')
        for i in range(0, len(items), 2):
            yield items[i], items[i + 1]

    @classmethod
    @returns(dict)
    def _parse_location_value(cls, value: str) -> dict[t.Season, dict[t.FishId, t.LocationVariation]]:
        for season_name, season_value in zip(cls.SEASONS, value.split('/')[4:8]):
            season = cls._parse_season_value(season_value)
            if not season:
                continue
            yield season_name, season

    @cached_property
    @returns(dict)
    def _locations(self) -> dict[t.LocationKey, dict[t.Season, dict[t.FishId, t.LocationVariation]]]:
        for key, value in self._raw_data.items():
            if key in self.SKIP_LOCATIONS:
                continue
            location = self._parse_location_value(value)
            if not location:
                continue
            yield key, location

    @cached_property
    def _location_name_processor(self) -> LocationNameProcessor:
        return self.parent.get_processor(LocationNameProcessor)

    def _get_fish_location_data(
            self,
            location_key: t.LocationKey,
            location_var: t.LocationVariation,
            season: t.Season,
    ) -> typing.Iterator[dict]:
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
                    self.RESULT_LOCATION_NAME: self._location_name_processor[location_key, var],
                    self.RESULT_SEASON: season,
                }
            return

        yield {
            self.RESULT_LOCATION_KEY: location_key,
            self.RESULT_LOCATION_VARIATION: location_var,
            self.RESULT_LOCATION_VARIATION_ORIGINAL: location_var,
            self.RESULT_LOCATION_NAME: self._location_name_processor[location_key, location_var],
            self.RESULT_SEASON: season,
        }

    @cached_property
    @returns(merge)
    def _fish_locations(self) -> dict[t.FishId, list[dict]]:
        for location_key, location_fish in self._locations.items():
            for season, season_fish in location_fish.items():
                for fish_id, location_var in season_fish.items():
                    for fish_location in self._get_fish_location_data(
                            location_key,
                            location_var,
                            season,
                    ):
                        yield fish_id, fish_location

    def __getitem__(self, fish_id: t.FishId) -> list[dict] | None:
        return self._fish_locations.get(fish_id)

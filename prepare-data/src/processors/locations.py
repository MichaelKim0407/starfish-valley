import os
import typing
from functools import cached_property

from returns import returns

from utils import merge
from . import t
from .base import JsonFileProcessor, AbstractProcessor
from .fish import AbstractExtendFishProcessor


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
    def _process_location(self, location_key: t.Location.Key) -> dict[t.Location.Variation, t.Location.Name]:
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
    def _names(self) -> dict[t.Location.Key, dict[t.Location.Variation, t.Location.Name]]:
        for location_key in self.LOCATIONS:
            yield location_key, self._process_location(location_key)

    @classmethod
    def expand(
            cls,
            key: t.Location.Key,
            var_orig: t.Location.Variation,
    ) -> typing.Iterator[t.Location.Variation]:
        variations = cls.LOCATIONS[key][1]
        if (
                variations is not None
                and var_orig == cls.LOCATION_VARIATION_ANY
        ):
            for var in variations:
                yield var

        else:
            yield var_orig

    def __getitem__(self, lookup: tuple[t.Location.Key, t.Location.Variation]) -> t.Location.Name:
        location_key, location_variation = lookup
        return self._names[location_key][location_variation]


class LocationProcessor(JsonFileProcessor, AbstractExtendFishProcessor):
    FILENAME = os.path.join('Data', 'Locations')
    USE_LOCALE = False

    SKIP_LOCATIONS = {
        'fishingGame',
        'Temp',
    }

    SEASON_SKIP = {'-1'}
    SEASONS = ('spring', 'summer', 'fall', 'winter')

    @cached_property
    def _location_name_processor(self) -> LocationNameProcessor:
        return self.parent.get_processor(LocationNameProcessor)

    @classmethod
    def _parse_season_value(cls, value: str) -> typing.Iterator[tuple[t.Fish.Id, t.Location.Variation]]:
        if value in cls.SEASON_SKIP:
            return

        items = value.split(' ')
        for i in range(0, len(items), 2):
            yield items[i], items[i + 1]

    def _parse_location(self, key: t.Location.Key, value: str) -> typing.Iterator[tuple[t.Fish.Id, t.Location]]:
        # https://stardewvalleywiki.com/Modding:Fish_data#Spawn_locations
        for season, season_fish in zip(self.SEASONS, value.split('/')[4:8]):
            for fish_id, variation_orig in self._parse_season_value(season_fish):
                for variation in self._location_name_processor.expand(key, variation_orig):
                    yield fish_id, t.Location(
                        key=key,
                        variation=variation,
                        variation_orig=variation_orig,
                        name=self._location_name_processor[key, variation],
                        season=season,
                    )

    @cached_property
    @returns(merge)
    def _fish_locations(self) -> dict[t.Fish.Id, list[t.Location]]:
        for key, value in self._raw_data.items():
            if key in self.SKIP_LOCATIONS:
                continue
            yield from self._parse_location(key, value)

    def extend_fish(self, fish: t.Fish) -> None:
        if fish.id not in self._fish_locations:
            return
        fish.locations = self._fish_locations[fish.id]

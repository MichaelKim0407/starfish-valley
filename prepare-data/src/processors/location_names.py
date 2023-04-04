import os
from functools import cached_property

from returns import returns

from . import JsonFileProcessor


class LocationNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Strings', 'StringsFromCSFiles')

    # https://stardewvalleywiki.com/Modding:Location_data#GameLocation_Names
    # TODO localize secondary names
    LOCATION_NAME_KEYS = {
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

    def get_location_name(self, location_key: str) -> str:
        string_key, extra = self.LOCATION_NAME_KEYS[location_key]
        if string_key is None:
            return extra

        location_name = self.raw_data[string_key]
        if extra is not None:
            location_name = f'{location_name} {extra}'
        return location_name

    @returns(dict)
    def process_location(self, location_key) -> dict[int, str]:
        location_name = self.get_location_name(location_key)
        if location_key not in self.LOCATION_VARIATIONS:
            yield -1, location_name
            return

        for variation, variation_name in self.LOCATION_VARIATIONS[location_key].items():
            yield variation, f'{location_name} ({variation_name})'

    @cached_property
    @returns(dict)
    def location_names(self) -> dict[str, dict[int, str]]:
        for location_key in self.LOCATION_NAME_KEYS:
            yield location_key, self.process_location(location_key)

    def __call__(self, result: dict):
        result[self.RESULT_KEY] = self.location_names

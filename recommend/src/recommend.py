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

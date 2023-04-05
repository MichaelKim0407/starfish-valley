import os
from functools import cached_property

from returns import returns

from utils import convert_items
from . import t
from .base import JsonFileProcessor


class FishProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'Fish')

    WEATHER_MAP = {
        'both': ('sunny', 'rainy'),
    }

    DIFFICULTY_SKIP = {'trap'}

    RESULT_KEY = 'fish'

    RESULT_ID = 'id'
    RESULT_EN_NAME = 'en_name'
    RESULT_LOCALIZED_NAME = 'name'
    RESULT_TIME_RANGES = 'time_ranges'
    RESULT_WEATHER = 'weather'
    RESULT_MIN_LEVEL = 'min_level'
    RESULT_MAX_DEPTH = 'max_depth'
    RESULT_SPAWN_MULTI = 'spawn_multi'
    RESULT_DEPTH_MULTI = 'depth_multi'
    RESULT_BEHAVIOR = 'behavior'
    RESULT_DIFFICULTY = 'difficulty'
    RESULT_SIZE_RANGE = 'size_range'

    RESULT_LOCATIONS = 'locations'
    RESULT_BUNDLES = 'bundles'
    RESULT_GIFTS = 'gifts'

    @staticmethod
    @returns(list)
    def _parse_time_ranges(time_ranges: str) -> t.TimeRanges:
        hours = convert_items(time_ranges.split(' '), int)
        for i in range(0, len(hours), 2):
            yield hours[i], hours[i + 1]

    @classmethod
    def _parse_weather(cls, weather: str) -> t.Weathers:
        if weather in cls.WEATHER_MAP:
            return cls.WEATHER_MAP[weather]
        else:
            return (weather,)

    def _parse_fish_value(self, value: str) -> dict | None:
        # https://stardewvalleywiki.com/Modding:Fish_data#Fish_data_and_spawn_criteria
        name, difficulty, *other_fields = value.split('/')
        if difficulty in self.DIFFICULTY_SKIP:
            return

        (
            behavior,
            min_size, max_size,
            time_ranges,
            _,
            weather,
            _,
            max_depth,
            spawn_multi,
            depth_multi,
            min_level,
            *other_fields_2,
        ) = other_fields

        if self.parent.lang_code is not None:
            try:
                localized_name = other_fields_2[-1]
            except IndexError:
                localized_name = name
        else:
            localized_name = name

        return {
            self.RESULT_EN_NAME: name,
            self.RESULT_LOCALIZED_NAME: localized_name,

            self.RESULT_TIME_RANGES: self._parse_time_ranges(time_ranges),
            self.RESULT_WEATHER: self._parse_weather(weather),
            self.RESULT_MIN_LEVEL: int(min_level),

            self.RESULT_MAX_DEPTH: int(max_depth),
            self.RESULT_SPAWN_MULTI: float(spawn_multi),
            self.RESULT_DEPTH_MULTI: float(depth_multi),
            self.RESULT_BEHAVIOR: behavior,
            self.RESULT_DIFFICULTY: int(difficulty),
            self.RESULT_SIZE_RANGE: (int(min_size), int(max_size)),
        }

    @cached_property
    @returns(dict)
    def _fish(self) -> dict[t.FishId, dict]:
        for key, value in self._raw_data.items():
            parsed = self._parse_fish_value(value)
            if not parsed:
                continue
            parsed[self.RESULT_ID] = key
            yield key, parsed

    def __contains__(self, fish_id: t.FishId) -> bool:
        return fish_id in self._fish

    @cached_property
    @returns(dict)
    def _en_name_id_map(self) -> dict[t.FishEnName, t.FishId]:
        for fish_id, fish in self._fish.items():
            yield fish[self.RESULT_EN_NAME], fish_id

    def get_id_from_en_name(self, en_name: t.FishEnName) -> t.FishId | None:
        return self._en_name_id_map.get(en_name)

    @cached_property
    def _location_processor(self) -> 'LocationProcessor':
        return self.parent.get_processor(LocationProcessor)

    @cached_property
    def _bundle_processor(self) -> 'AllBundleProcessor':
        return self.parent.get_processor(AllBundleProcessor)

    @cached_property
    def _gift_processor(self) -> 'GiftProcessor':
        return self.parent.get_processor(GiftProcessor)

    @cached_property
    @returns(dict)
    def _fish_extended(self) -> dict[str, dict]:
        for fish_id, fish in self._fish.items():
            extend = {
                self.RESULT_LOCATIONS: self._location_processor[fish_id],
                self.RESULT_BUNDLES: self._bundle_processor[fish_id],
                self.RESULT_GIFTS: self._gift_processor[fish_id],
            }
            extend = {
                k: v
                for k, v in extend.items()
                if v
            }
            yield fish_id, {**fish, **extend}

    def __call__(self, result: dict):
        result[self.RESULT_KEY] = self._fish_extended


from .locations import LocationProcessor
from .bundles import AllBundleProcessor
from .gifts import GiftProcessor

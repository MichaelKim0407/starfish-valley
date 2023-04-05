import os
from functools import cached_property

from returns import returns

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

    @staticmethod
    @returns(list)
    def parse_time_ranges(time_ranges: str) -> list[tuple[int, int]]:
        hours = [
            int(hour)
            for hour in time_ranges.split(' ')
        ]
        for i in range(0, len(hours), 2):
            yield hours[i], hours[i + 1]

    @classmethod
    def parse_weather(cls, weather: str) -> tuple[str, ...]:
        if weather in cls.WEATHER_MAP:
            return cls.WEATHER_MAP[weather]
        else:
            return (weather,)

    def parse_fish_value(self, value) -> dict | None:
        # https://stardewvalleywiki.com/Modding:Fish_data#Fish_data_and_spawn_criteria
        name, difficulty, *other_fields = value.split('/')
        if difficulty in self.DIFFICULTY_SKIP:
            return

        (
            behavior,
            min_size, max_size,
            time_ranges,
            seasons,
            weather,
            locations,
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

            self.RESULT_TIME_RANGES: self.parse_time_ranges(time_ranges),
            self.RESULT_WEATHER: self.parse_weather(weather),
            self.RESULT_MIN_LEVEL: int(min_size),

            self.RESULT_MAX_DEPTH: int(max_depth),
            self.RESULT_SPAWN_MULTI: float(spawn_multi),
            self.RESULT_DEPTH_MULTI: float(depth_multi),
        }

    @cached_property
    @returns(dict)
    def data(self) -> dict[str, dict]:
        for key, value in self.raw_data.items():
            parsed = self.parse_fish_value(value)
            if not parsed:
                continue
            parsed[self.RESULT_ID] = int(key)
            yield key, parsed

    def __call__(self, result: dict):
        result[self.RESULT_KEY] = self.data

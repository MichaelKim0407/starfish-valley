import os
from functools import cached_property

from returns import returns

from . import JsonFileProcessor


class FishFileProcessor(JsonFileProcessor):
    def __init__(self, parent):
        super().__init__(parent, os.path.join('Data', 'Fish'))

    @staticmethod
    @returns(list)
    def parse_time_ranges(time_ranges: str) -> list[tuple[int, int]]:
        hours = [
            int(hour)
            for hour in time_ranges.split(' ')
        ]
        for i in range(0, len(hours), 2):
            yield hours[i], hours[i + 1]

    @staticmethod
    def parse_weather(weather: str) -> tuple[str, ...]:
        if weather == 'both':
            return 'sunny', 'rainy'
        else:
            return weather,

    @classmethod
    def parse_fish_value(cls, value):
        # https://stardewvalleywiki.com/Modding:Fish_data#Fish_data_and_spawn_criteria
        name, difficulty, *other_fields = value.split('/')
        if difficulty == 'trap':
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
            *language_specific_fields,
        ) = other_fields

        if language_specific_fields:
            localized_name = language_specific_fields[0]
        else:
            localized_name = name

        return {
            'en_name': name,
            'name': localized_name,

            'time_ranges': cls.parse_time_ranges(time_ranges),
            'seasons': seasons.split(' '),
            'weather': cls.parse_weather(weather),
            'min_level': int(min_size),

            'max_depth': int(max_depth),
            'spawn_multi': float(spawn_multi),
            'depth_multi': float(depth_multi),
        }

    @cached_property
    @returns(dict)
    def data(self) -> dict[str, dict]:
        for key, value in self.raw_data.items():
            parsed = self.parse_fish_value(value)
            if not parsed:
                continue
            parsed['id'] = int(key)
            yield key, parsed

    def __call__(self, result: dict):
        result['fish'] = self.data

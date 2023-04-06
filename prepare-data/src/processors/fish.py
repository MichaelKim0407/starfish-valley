import os
import typing
from functools import cached_property

from returns import returns

from utils import convert_items
from . import t
from .base import JsonFileProcessor, AbstractProcessor


class FishProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'Fish')

    WEATHER_SUNNY = 'sunny'
    WEATHER_RAINY = 'rainy'
    WEATHER_BOTH = 'both'
    WEATHER_MAP = {
        WEATHER_BOTH: (WEATHER_SUNNY, WEATHER_RAINY),
    }

    DIFFICULTY_SKIP = {'trap'}
    ID_SKIP = {
        '152',  # Seaweed
        '153',  # Green Algae
        '157',  # White Algae
    }

    RESULT_KEY = 'fish'

    @staticmethod
    @returns(list)
    def _parse_time_ranges(value: str) -> t.Fish.TimeRanges:
        hours = convert_items(value.split(' '), int)
        for i in range(0, len(hours), 2):
            yield hours[i], hours[i + 1]

    @classmethod
    def _parse_weather(cls, value: str) -> t.Fish.Weathers:
        if value in cls.WEATHER_MAP:
            return cls.WEATHER_MAP[value]
        else:
            return (value,)

    def _parse_fish(self, id_: t.Fish.Id, value: str) -> t.Fish | None:
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

        return t.Fish(
            id=id_,
            en_name=name,
            name=localized_name,
            time_ranges=self._parse_time_ranges(time_ranges),
            weather=self._parse_weather(weather),
            min_level=int(min_level),
            max_depth=int(max_depth),
            spawn_multi=float(spawn_multi),
            depth_multi=float(depth_multi),
            behavior=behavior,
            difficulty=int(difficulty),
            size_range=(int(min_size), int(max_size)),
        )

    @cached_property
    @returns(dict)
    def _fish(self) -> dict[t.Fish.Id, t.Fish]:
        for fish_id, value in self._raw_data.items():
            if fish_id in self.ID_SKIP:
                continue
            fish = self._parse_fish(fish_id, value)
            if fish is None:
                continue
            yield fish_id, fish

    def __contains__(self, fish_id: t.Fish.Id) -> bool:
        return fish_id in self._fish

    @cached_property
    @returns(dict)
    def _en_name_id_map(self) -> dict[t.Fish.EnName, t.Fish.Id]:
        for fish_id, fish in self._fish.items():
            yield fish.en_name, fish_id

    def get_id_from_en_name(self, en_name: t.Fish.EnName) -> t.Fish.Id | None:
        return self._en_name_id_map.get(en_name)

    @property
    def _extend_processors(self) -> typing.Iterator['Processor']:
        from .locations import LocationProcessor
        yield self.parent.get_processor(LocationProcessor)
        from .bundles import AllBundleProcessor
        yield self.parent.get_processor(AllBundleProcessor)
        from .gifts import GiftProcessor
        yield self.parent.get_processor(GiftProcessor)

    def _extend(self):
        for fish in self._fish.values():
            for processor in self._extend_processors:
                processor.extend_fish(fish)

    @cached_property
    def _fish_extended(self) -> dict[str, t.Fish]:
        self._extend()
        return self._fish

    def __call__(self, result: t.Result):
        result.fish = self._fish_extended


class AbstractExtendFishProcessor(AbstractProcessor):
    def extend_fish(self, fish: t.Fish) -> None:
        raise NotImplementedError


Processor = typing.TypeVar('Processor', bound=AbstractExtendFishProcessor)

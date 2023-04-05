import os
from functools import cached_property

from returns import returns

from utils import Merge
from .base import JsonFileProcessor
from .fish import FishProcessor


class CharacterNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'NPCDispositions')

    @cached_property
    @returns(dict)
    def data(self) -> dict[str, str]:
        # https://stardewvalleywiki.com/Modding:NPC_data#Basic_info
        for character_key, value in self.raw_data.items():
            yield character_key, value.split('/')[-1]


class GiftProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'NPCGiftTastes')

    RESULT_SUBKEY = 'gifts'

    RESULT_LOVE = 'loves'
    RESULT_LIKE = 'likes'

    SKIP_PREFIX = {'Universal_'}
    INDEXES = {
        RESULT_LOVE: 1,
        RESULT_LIKE: 3,
    }

    @classmethod
    def should_skip(cls, character_name: str) -> bool:
        for skip_prefix in cls.SKIP_PREFIX:
            if character_name.startswith(skip_prefix):
                return True
        return False

    @classmethod
    @returns(dict)
    def parse_character_value(cls, value: str) -> dict[str, list[str]]:
        # https://stardewvalleywiki.com/Modding:Gift_taste_data#Format
        elems = value.split('/')
        for key, i in cls.INDEXES.items():
            item_ids = elems[i]
            if not item_ids:
                continue
            yield key, item_ids.split(' ')

    @cached_property
    @returns(dict)
    def data(self) -> dict[str, dict[str, list[str]]]:
        for character_key, value in self.raw_data.items():
            if self.should_skip(character_key):
                continue
            yield character_key, self.parse_character_value(value)

    @cached_property
    def _character_name_processor(self) -> CharacterNameProcessor:
        return CharacterNameProcessor(self.parent)

    def get_character_name(self, character_key: str) -> str:
        return self._character_name_processor.data[character_key]

    @cached_property
    @returns(Merge(2))
    def rearranged_data(self) -> dict[str, dict[str, list[str]]]:
        for character_key, character_gift_tastes in self.data.items():
            character_name = self.get_character_name(character_key)
            for taste_type, item_ids in character_gift_tastes.items():
                for item_id in item_ids:
                    yield item_id, (taste_type, character_name)

    def __call__(self, result: dict):
        fish = result[FishProcessor.RESULT_KEY]
        for item_id, item_tastes in self.rearranged_data.items():
            if item_id not in fish:
                continue
            fish[item_id][self.RESULT_SUBKEY] = item_tastes
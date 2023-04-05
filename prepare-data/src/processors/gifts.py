import os
from functools import cached_property

from returns import returns

from utils import Merge
from . import t
from .base import JsonFileProcessor
from .fish import FishProcessor


class CharacterNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'NPCDispositions')

    @cached_property
    @returns(dict)
    def _names(self) -> dict[t.CharacterKey, t.CharacterName]:
        # https://stardewvalleywiki.com/Modding:NPC_data#Basic_info
        for character_key, value in self._raw_data.items():
            yield character_key, value.split('/')[-1]

    def __getitem__(self, character_key: t.CharacterKey) -> t.CharacterName:
        return self._names[character_key]


class GiftProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'NPCGiftTastes')

    RESULT_LOVE = 'loves'
    RESULT_LIKE = 'likes'

    SKIP_PREFIX = {'Universal_'}
    INDEXES = {
        RESULT_LOVE: 1,
        RESULT_LIKE: 3,
    }

    @classmethod
    def _should_skip(cls, character_key: t.CharacterKey) -> bool:
        for skip_prefix in cls.SKIP_PREFIX:
            if character_key.startswith(skip_prefix):
                return True
        return False

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    @returns(list)
    def _parse_item_ids(self, value: str) -> list[t.FishId]:
        if not value:
            return

        for item_id in value.split(' '):
            if item_id not in self._fish_processor:
                continue
            yield item_id

    @returns(dict)
    def _parse_character_value(self, value: str) -> t.CharacterPreferences:
        # https://stardewvalleywiki.com/Modding:Gift_taste_data#Format
        elems = value.split('/')
        for key, i in self.INDEXES.items():
            item_ids = self._parse_item_ids(elems[i])
            if not item_ids:
                continue
            yield key, item_ids

    @cached_property
    @returns(dict)
    def _character_gift_tastes(self) -> dict[t.CharacterKey, t.CharacterPreferences]:
        for character_key, value in self._raw_data.items():
            if self._should_skip(character_key):
                continue
            character = self._parse_character_value(value)
            if not character:
                continue
            yield character_key, character

    @cached_property
    def _character_name_processor(self) -> CharacterNameProcessor:
        return CharacterNameProcessor(self.parent)

    @cached_property
    @returns(Merge(2))
    def _item_tastes(self) -> dict[t.FishId, dict[t.CharacterPreferenceType, list[t.CharacterName]]]:
        for character_key, character_gift_tastes in self._character_gift_tastes.items():
            character_name = self._character_name_processor[character_key]
            for taste_type, item_ids in character_gift_tastes.items():
                for item_id in item_ids:
                    yield item_id, (taste_type, character_name)

    def __getitem__(self, fish_id: t.FishId) -> dict[t.CharacterPreferenceType, list[t.CharacterName]]:
        return self._item_tastes.get(fish_id)

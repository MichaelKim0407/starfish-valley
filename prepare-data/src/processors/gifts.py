import os
import typing
from functools import cached_property

from returns import returns

from utils import Merge
from . import t
from .base import JsonFileProcessor
from .fish import FishProcessor, AbstractExtendFishProcessor


class CharacterNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Data', 'NPCDispositions')

    @cached_property
    @returns(dict)
    def _names(self) -> dict[t.Character.Key, t.Character.Name]:
        # https://stardewvalleywiki.com/Modding:NPC_data#Basic_info
        for character_key, value in self._raw_data.items():
            yield character_key, value.split('/')[-1]

    def __getitem__(self, character_key: t.Character.Key) -> t.Character.Name:
        return self._names[character_key]


class GiftProcessor(JsonFileProcessor, AbstractExtendFishProcessor):
    FILENAME = os.path.join('Data', 'NPCGiftTastes')

    SKIP_PREFIX = {'Universal_'}
    INDEXES = {
        t.Character.LOVES: 1,
        t.Character.LIKES: 3,
    }

    @classmethod
    def _should_skip(cls, character_key: t.Character.Key) -> bool:
        for skip_prefix in cls.SKIP_PREFIX:
            if character_key.startswith(skip_prefix):
                return True
        return False

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    def _parse_item_ids(self, value: str) -> typing.Iterator[t.Fish.Id]:
        if not value:
            return

        for item_id in value.split(' '):
            if item_id not in self._fish_processor:
                continue
            yield item_id

    def _parse_character_preferences(self, value: str) -> typing.Iterator[tuple[t.Fish.Id, t.Character.PreferenceType]]:
        # https://stardewvalleywiki.com/Modding:Gift_taste_data#Format
        elems = value.split('/')
        for preference_type, i in self.INDEXES.items():
            for fish_id in self._parse_item_ids(elems[i]):
                yield fish_id, preference_type

    @cached_property
    def _character_name_processor(self) -> CharacterNameProcessor:
        return CharacterNameProcessor(self.parent)

    @cached_property
    @returns(Merge(2))
    def _fish_preferences(self) -> dict[t.Fish.Id, dict[t.Character.PreferenceType, list[t.Character]]]:
        for character_key, value in self._raw_data.items():
            if self._should_skip(character_key):
                continue
            character = t.Character(
                key=character_key,
                name=self._character_name_processor[character_key],
            )
            for fish_id, preference_type in self._parse_character_preferences(value):
                yield fish_id, (preference_type, character)

    def extend_fish(self, fish: t.Fish) -> None:
        if fish.id not in self._fish_preferences:
            return
        fish.gifts = self._fish_preferences[fish.id]

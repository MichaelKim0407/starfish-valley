import os
from functools import cached_property

from returns import returns

from utils import Merge
from .base import JsonFileProcessor
from .fish import FishProcessor
from .name_mapping import NameMappingMixin


class CharacterNameProcessor(JsonFileProcessor, NameMappingMixin):
    FILENAME = os.path.join('Strings', 'StringsFromCSFiles')

    # TODO
    MAPPING = {
        'Abigail': ('Utility.cs.', None),
        'Alex': ('Utility.cs.', None),
        'Caroline': ('Utility.cs.', None),
        'Clint': ('Utility.cs.', None),
        'Demetrius': ('Utility.cs.', None),
        'Dwarf': ('Utility.cs.', None),
        'Elliott': ('Utility.cs.', None),
        'Emily': ('Utility.cs.', None),
        'Evelyn': ('Utility.cs.', None),
        'George': ('Utility.cs.', None),
        'Gus': ('Utility.cs.', None),
        'Haley': ('Utility.cs.', None),
        'Harvey': ('Utility.cs.', None),
        'Jas': ('Utility.cs.', None),
        'Jodi': ('Utility.cs.', None),
        'Kent': ('Utility.cs.', None),
        'Krobus': ('Utility.cs.', None),
        'Leah': ('Utility.cs.', None),
        'Leo': ('Utility.cs.', None),
        'Lewis': ('Utility.cs.', None),
        'Linus': ('Utility.cs.', None),
        'Marnie': ('Utility.cs.', None),
        'Maru': ('Utility.cs.', None),
        'Pam': ('Utility.cs.', None),
        'Penny': ('Utility.cs.', None),
        'Pierre': ('Utility.cs.', None),
        'Robin': ('Utility.cs.', None),
        'Sam': ('Utility.cs.', None),
        'Sandy': ('Utility.cs.', None),
        'Sebastian': ('Utility.cs.', None),
        'Shane': ('Utility.cs.', None),
        'Vincent': ('Utility.cs.', None),
        'Willy': ('Utility.cs.', None),
        'Wizard': ('Utility.cs.', None),
    }


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
        for character_name, value in self.raw_data.items():
            if self.should_skip(character_name):
                continue
            yield character_name, self.parse_character_value(value)

    @cached_property
    @returns(Merge(2))
    def rearranged_data(self) -> dict[str, dict[str, list[str]]]:
        for character_name, character_gift_tastes in self.data.items():
            for taste_type, item_ids in character_gift_tastes.items():
                for item_id in item_ids:
                    yield item_id, (taste_type, character_name)

    def __call__(self, result: dict):
        fish = result[FishProcessor.RESULT_KEY]
        for item_id, item_tastes in self.rearranged_data.items():
            if item_id not in fish:
                continue
            fish[item_id][self.RESULT_SUBKEY] = item_tastes

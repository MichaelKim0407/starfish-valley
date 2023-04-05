import typing
from functools import cached_property

from returns import returns

from .base import AbstractProcessor
from .languages import LocaleDict

Item = typing.TypeVar('Item', bound=str)
DataLookupKey = typing.TypeVar('DataLookupKey', bound=str)


class NameMappingMixin(AbstractProcessor):
    MAPPING: dict[Item, tuple[DataLookupKey | None, LocaleDict | str | None]]

    raw_data: dict[DataLookupKey, str]

    def get_localized_name(self, en_name: Item) -> str:
        key, extra_name_mapping = self.MAPPING[en_name]
        extra_name = self.parent.translate(extra_name_mapping)

        if key is None:
            return extra_name

        localized_name = self.raw_data[key]
        if extra_name is not None:
            localized_name = f'{localized_name} {extra_name}'
        return localized_name

    @cached_property
    @returns(dict)
    def names(self) -> dict[Item, str]:
        for en_name in self.MAPPING:
            yield en_name, self.get_localized_name(en_name)

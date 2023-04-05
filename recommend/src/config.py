from configparser import ConfigParser
from functools import cached_property

from returns import returns


class Config:
    def __init__(self, filename: str):
        self.filename = filename

    @staticmethod
    @returns(list)
    def _getlist(value: str) -> list[str]:
        for s in value.split():
            s = s.strip()
            if not s:
                continue
            yield s

    @cached_property
    def parser(self) -> ConfigParser:
        parser = ConfigParser(converters={'list': self._getlist})
        parser.read(self.filename)
        return parser

    @cached_property
    def data_file(self) -> str:
        return self.parser.get('data', 'data_file')

    @cached_property
    def unlocked_areas(self) -> str:
        return self.parser.getlist('progress', 'unlocked_areas')

    @cached_property
    def fishing_level(self) -> int:
        return self.parser.getint('progress', 'fishing_level')

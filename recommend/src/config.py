from configparser import ConfigParser
from functools import cached_property

from returns import returns


class Config:
    def __init__(self, filename: str):
        self.filename = filename

    @staticmethod
    @returns(list)
    def _getlist(value: str) -> list[str]:
        for s in value.splitlines():
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

    @cached_property
    def winter_rain_totem(self) -> int:
        return self.parser.getboolean('progress', 'winter_rain_totem')

    @cached_property
    def rec_season_factor(self) -> float:
        return self.parser.getfloat('recommendation', 'season_factor')

    @cached_property
    def rec_weather_factor_sunny(self) -> float:
        return self.parser.getfloat('recommendation', 'weather_factor_sunny')

    @cached_property
    def rec_weather_factor_rainy(self) -> float:
        return self.parser.getfloat('recommendation', 'weather_factor_rainy')

    @cached_property
    def rec_bundle_factor(self) -> float:
        return self.parser.getfloat('recommendation', 'bundle_factor')

    @cached_property
    def rec_gift_factor(self) -> float:
        return self.parser.getfloat('recommendation', 'gift_factor')

    @cached_property
    def bundles(self) -> list[str]:
        return self.parser.getlist('bundles', 'bundles')

    @staticmethod
    def _get_opt_name(name: str) -> str:
        return name.lower().replace(' ', '_').replace("'", '')

    def bundle(self, en_name: str) -> list[str]:
        opt_name = self._get_opt_name(en_name)
        return self.parser.getlist('bundles', opt_name)

    def gifts(self, character_key: str) -> list[str]:
        opt_name = self._get_opt_name(character_key)
        return self.parser.getlist('gifts', opt_name)

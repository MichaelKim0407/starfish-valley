import json
import os
import typing
from functools import cached_property

from returns import returns

LangCode = typing.TypeVar('LangCode', bound=str | None)
LocaleDict = dict[LangCode, str | None]


class LanguageProcessor:
    LANGUAGES: LocaleDict = {
        None: 'English',  # English
        'ru-RU': 'Русский',  # Russian
        'zh-CN': '简体中文',  # Simplified Chinese
        'de-DE': 'Deutsch',  # German
        'pt-BR': 'Português',  # Brazilian Portuguese
        'fr-FR': 'Français',  # French
        'es-ES': 'Español',  # Spanish
        'ja-JP': '日本語',  # Japanese
        'ko-KR': '한국어',  # Korean
        'it-IT': 'Italiano',  # Italian
        'tr-TR': 'Türkçe',  # Turkish
        'hu-HU': 'Magyar',  # Hungarian
    }

    RESULT_VERSION = 'version'
    RESULT_LANG_CODE = 'lang_code'
    RESULT_LANGUAGE = 'language'

    @classmethod
    @returns(list)
    def run_all(cls, game_data_dir: str, output: str, game_version: str) -> list[str]:
        for lang_code in cls.LANGUAGES:
            processor = cls(game_data_dir, output, game_version, lang_code)
            processor()
            yield processor.output_file_name

    def __init__(self, game_data_dir: str, output: str, game_version: str, lang_code: LangCode):
        self.game_data_dir = game_data_dir
        self.output = output
        self.game_version = game_version
        self.lang_code = lang_code

    def translate(
            self,
            locale_dict: LocaleDict | str | None,
    ) -> str | None:
        if locale_dict is None or isinstance(locale_dict, str):
            return locale_dict

        lang_code = self.lang_code
        if lang_code not in locale_dict:
            lang_code = None
        return locale_dict[lang_code]

    @cached_property
    def language(self) -> str:
        return self.translate(self.LANGUAGES)

    @property
    def _processors(self) -> typing.Iterable['AbstractProcessor']:
        from .fish import FishProcessor
        yield FishProcessor(self)
        from .locations import LocationProcessor
        yield LocationProcessor(self)
        from .bundles import AllBundleProcessor
        yield AllBundleProcessor(self)

    @cached_property
    def data(self):
        result = {
            self.RESULT_VERSION: self.game_version,
            self.RESULT_LANG_CODE: self.lang_code,
            self.RESULT_LANGUAGE: self.language,
        }
        for file_processor in self._processors:
            file_processor(result)
        return result

    @cached_property
    def output_file_name(self) -> str:
        return f'{self.game_version} ({self.language}).json'

    @cached_property
    def output_file_path(self) -> str:
        return os.path.join(self.output, self.output_file_name)

    def __call__(self):
        with open(self.output_file_path, 'w') as f:
            json.dump(self.data, f)


from .base import AbstractProcessor

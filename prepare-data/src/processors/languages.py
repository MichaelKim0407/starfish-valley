import json
import os
import typing
from functools import cached_property

from returns import returns

from utils import JSONEncoder
from . import t


class LanguageProcessor:
    LANGUAGES: t.LocaleDict = {
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

    @classmethod
    @returns(list)
    def run_all(
            cls,
            game_data_dir: str,
            output: str,
            game_version: str,
            processors: typing.Sequence[typing.Type['Processor']],
    ) -> list[str]:
        for lang_code in cls.LANGUAGES:
            processor = cls(
                game_data_dir,
                output,
                game_version,
                lang_code,
                processors,
            )
            processor()
            yield processor._output_file_name

    def __init__(
            self,
            game_data_dir: str,
            output: str,
            game_version: str,
            lang_code: t.LangCode,
            processors: typing.Sequence[typing.Type['Processor']],
    ):
        self.game_data_dir = game_data_dir
        self.output = output
        self.game_version = game_version
        self.lang_code = lang_code
        self.processors = processors

        self._singletons = {}

    def translate(self, translatable: t.Translatable) -> str | None:
        if translatable is None or isinstance(translatable, str):
            return translatable

        lang_code = self.lang_code
        if lang_code not in translatable:
            lang_code = None
        return translatable[lang_code]

    @cached_property
    def _language(self) -> str:
        return self.translate(self.LANGUAGES)

    def get_processor(self, processor_cls: typing.Type['Processor']) -> 'Processor':
        if processor_cls not in self._singletons:
            self._singletons[processor_cls] = processor_cls(self)
        return self._singletons[processor_cls]

    @property
    def _processors(self) -> typing.Iterable['Processor']:
        for processor_cls in self.processors:
            yield self.get_processor(processor_cls)

    @cached_property
    def _result(self) -> t.Result:
        result = t.Result(
            version=self.game_version,
            lang_code=self.lang_code,
            language=self._language,
        )
        for file_processor in self._processors:
            file_processor(result)
        return result

    @cached_property
    def _output_file_name(self) -> str:
        return f'{self.game_version} ({self._language}).json'

    @cached_property
    def _output_file_path(self) -> str:
        return os.path.join(self.output, self._output_file_name)

    def __call__(self):
        with open(self._output_file_path, 'w') as f:
            json.dump(self._result, f, cls=JSONEncoder)


from .base import AbstractProcessor

Processor = typing.TypeVar('Processor', bound=AbstractProcessor)

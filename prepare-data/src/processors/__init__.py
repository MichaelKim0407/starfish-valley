import json
import os
import typing
from functools import cached_property


class LanguageProcessor:
    LANGUAGES = {
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
    def run_all(cls, source: str, output: str, version_name: str):
        for lang_code in cls.LANGUAGES:
            processor = cls(source, output, version_name, lang_code)
            processor()

    def __init__(self, source: str, output: str, version_name: str, lang_code: str):
        self.source = source
        self.output = output
        self.version_name = version_name
        self.lang_code = lang_code

    @cached_property
    def language(self) -> str:
        return self.LANGUAGES[self.lang_code]

    @property
    def _processors(self) -> typing.Iterable['FileProcessor']:
        from .fish import FishFileProcessor
        yield FishFileProcessor(self)
        from .location_names import LocationNameProcessor
        yield LocationNameProcessor(self)
        from .locations import LocationFileProcessor
        yield LocationFileProcessor(self)

    @cached_property
    def data(self):
        result = {
            'version': self.version_name,
            'lang_code': self.lang_code,
            'language': self.language,
        }
        for file_processor in self._processors:
            file_processor(result)
        return result

    @cached_property
    def output_file_name(self) -> str:
        return os.path.join(self.output, f'{self.version_name} ({self.language}).json')

    def __call__(self):
        with open(self.output_file_name, 'w') as f:
            json.dump(self.data, f)


class FileProcessor:
    FILENAME: str = None
    EXT: str = None
    USE_LOCALE: bool = True

    def __init__(
            self,
            parent: LanguageProcessor,
            filename: str = None,
            ext: str = None,
            use_locale: bool = None,
    ):
        self.parent = parent

        if filename is None:
            filename = self.FILENAME
        self.filename = filename

        if ext is None:
            ext = self.EXT
        self.ext = ext

        if use_locale is None:
            use_locale = self.USE_LOCALE
        self.use_locale = use_locale

    @cached_property
    def _filename(self) -> str:
        if (not self.use_locale) or self.parent.lang_code is None:
            return f'{self.filename}.{self.ext}'
        else:
            return f'{self.filename}.{self.parent.lang_code}.{self.ext}'

    @cached_property
    def source_file_name(self) -> str:
        return os.path.join(self.parent.source, self._filename)

    def __call__(self, result: dict):
        raise NotImplementedError


class JsonFileProcessor(FileProcessor):
    EXT = 'json'

    @cached_property
    def raw_data(self):
        with open(self.source_file_name) as f:
            return json.load(f)
